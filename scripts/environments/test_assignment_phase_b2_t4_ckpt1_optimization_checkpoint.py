"""CPU-only qualification for B2-T4-CKPT1 optimization continuation."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
sys.path.insert(0, str(SOURCE_DIR))

from assignment_optimization_checkpoint import (  # noqa: E402
    OPTIMIZATION_CHECKPOINT_SCHEMA,
    OptimizationCheckpointBoundaryError,
    OptimizationCheckpointBoundaryState,
    OptimizationCheckpointLoadError,
    OptimizationCheckpointRuntimeGuard,
    OptimizationCheckpointValidationError,
    OptimizationProgressionState,
    OptimizationProgressionTracker,
    linear_lr_for_next_update,
    load_optimization_checkpoint,
    save_optimization_checkpoint,
    validate_optimization_checkpoint,
)
from assignment_value_normalizer_checkpoint import export_value_normalizer_checkpoint_state  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


SEMANTIC_CONFIG = {
    "assignment_profile": "lifecycle_contract_c",
    "algorithm": "happo",
    "actor_order": ["robot_0", "robot_1"],
    "optimizer": "torch.optim.Adam",
    "value_normalizer": {"enabled": True, "adapter": "project_owned"},
    "schedule": {"kind": "linear", "total_update_count": 12},
}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left.cpu(), right.cpu())
    if isinstance(left, dict) and isinstance(right, dict):
        return tuple(left) == tuple(right) and all(nested_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, type(left)):
        return len(left) == len(right) and all(nested_equal(a, b) for a, b in zip(left, right, strict=True))
    return left == right


class Fixture:
    def __init__(self, seed: int, *, value_shape: int = 1) -> None:
        torch.manual_seed(seed)
        self.value_shape = value_shape
        self.actors = [
            ("robot_0", torch.nn.Sequential(torch.nn.Linear(3, 5), torch.nn.Tanh(), torch.nn.Linear(5, 2))),
            ("robot_1", torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.ReLU(), torch.nn.Linear(4, 2))),
        ]
        self.actor_optimizers = [
            (name, torch.optim.Adam(module.parameters(), lr=0.011 + index * 0.003, eps=1e-5))
            for index, (name, module) in enumerate(self.actors)
        ]
        self.critic = torch.nn.Sequential(torch.nn.Linear(4, 6), torch.nn.Tanh(), torch.nn.Linear(6, 1))
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=0.017, eps=1e-5)
        self.value_normalizer = ValueNorm(value_shape, device=torch.device("cpu"))
        self.progression = OptimizationProgressionTracker(OptimizationProgressionState.after_update(1, 12))
        self.populate()

    def populate(self) -> None:
        actor_input = torch.tensor(
            [[0.25, -0.5, 0.75], [1.0, 0.1, -0.2], [-0.4, 0.8, 0.3]], dtype=torch.float32
        )
        for index, ((_, actor), (_, optimizer)) in enumerate(zip(self.actors, self.actor_optimizers, strict=True)):
            optimizer.zero_grad(set_to_none=True)
            target = torch.full((3, 2), 0.15 * (index + 1), dtype=torch.float32)
            torch.nn.functional.mse_loss(actor(actor_input), target).backward()
            optimizer.step()
        self.critic_optimizer.zero_grad(set_to_none=True)
        critic_input = torch.tensor(
            [[0.2, 0.4, -0.1, 0.9], [0.7, -0.3, 0.5, 0.1], [-0.6, 0.2, 0.8, -0.4]], dtype=torch.float32
        )
        torch.nn.functional.mse_loss(self.critic(critic_input), torch.tensor([[0.4], [-0.2], [0.6]])).backward()
        self.critic_optimizer.step()
        values = torch.tensor([[1.0], [2.5], [-0.25], [4.0]], dtype=torch.float32)
        if self.value_shape != 1:
            values = values.repeat(1, self.value_shape)
        self.value_normalizer.update(values)

    def controlled_update(self) -> None:
        actor_input = torch.tensor(
            [[-0.3, 0.2, 0.7], [0.5, -0.6, 0.1], [0.9, 0.4, -0.8]], dtype=torch.float32
        )
        for index, ((_, actor), (_, optimizer)) in enumerate(zip(self.actors, self.actor_optimizers, strict=True)):
            optimizer.zero_grad(set_to_none=True)
            target = torch.full((3, 2), -0.11 * (index + 1), dtype=torch.float32)
            torch.nn.functional.mse_loss(actor(actor_input), target).backward()
            optimizer.step()
        self.critic_optimizer.zero_grad(set_to_none=True)
        critic_input = torch.tensor(
            [[0.1, -0.2, 0.3, -0.4], [0.4, 0.3, -0.2, -0.1], [0.6, -0.5, 0.2, 0.7]], dtype=torch.float32
        )
        torch.nn.functional.mse_loss(self.critic(critic_input), torch.tensor([[0.1], [0.3], [-0.4]])).backward()
        self.critic_optimizer.step()
        values = torch.tensor([[0.5], [3.0], [-1.0]], dtype=torch.float32)
        if self.value_shape != 1:
            values = values.repeat(1, self.value_shape)
        self.value_normalizer.update(values)
        current = self.progression.state
        self.progression.replace(
            OptimizationProgressionState.after_update(current.next_update_index, current.total_update_count)
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "actors": [(name, copy.deepcopy(module.state_dict())) for name, module in self.actors],
            "actor_optimizers": [(name, copy.deepcopy(optimizer.state_dict())) for name, optimizer in self.actor_optimizers],
            "critic": copy.deepcopy(self.critic.state_dict()),
            "critic_optimizer": copy.deepcopy(self.critic_optimizer.state_dict()),
            "value_normalizer": export_value_normalizer_checkpoint_state(self.value_normalizer),
            "progression": self.progression.state.to_mapping(),
        }


def save_fixture(root: Path, fixture: Fixture, *, injector=None):
    return save_optimization_checkpoint(
        checkpoint_root=root,
        boundary=OptimizationCheckpointBoundaryState.clean(),
        actor_modules=fixture.actors,
        actor_optimizers=fixture.actor_optimizers,
        critic_module=fixture.critic,
        critic_optimizer=fixture.critic_optimizer,
        value_normalizer=fixture.value_normalizer,
        progression=fixture.progression.state,
        semantic_config=SEMANTIC_CONFIG,
        failure_injector=injector,
    )


def load_fixture(root: Path, fixture: Fixture, *, injector=None):
    return load_optimization_checkpoint(
        root,
        expected_semantic_config=SEMANTIC_CONFIG,
        actor_modules=fixture.actors,
        actor_optimizers=fixture.actor_optimizers,
        critic_module=fixture.critic,
        critic_optimizer=fixture.critic_optimizer,
        value_normalizer=fixture.value_normalizer,
        progression_tracker=fixture.progression,
        runtime_guard=OptimizationCheckpointRuntimeGuard(),
        apply_failure_injector=injector,
    )


def generation_dir(root: Path) -> Path:
    pointer = json.loads((root / "latest.json").read_text(encoding="utf-8"))
    return root / pointer["generation_directory"]


def refresh_pointer(root: Path) -> None:
    pointer_path = root / "latest.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["manifest_sha256"] = sha256_path(generation_dir(root) / "checkpoint_manifest.json")
    pointer_path.write_bytes(canonical_bytes(pointer))


def rewrite_manifest(root: Path, transform) -> None:
    manifest_path = generation_dir(root) / "checkpoint_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    transform(manifest)
    manifest_path.write_bytes(canonical_bytes(manifest))
    refresh_pointer(root)


def rewrite_artifact(root: Path, component: str, transform) -> None:
    directory = generation_dir(root)
    manifest_path = directory / "checkpoint_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(item for item in manifest["artifacts"] if item["component"] == component)
    path = directory / record["path"]
    value = torch.load(path, map_location="cpu", weights_only=True)
    transform(value)
    torch.save(value, path)
    record["sha256"] = sha256_path(path)
    manifest_path.write_bytes(canonical_bytes(manifest))
    refresh_pointer(root)


QUALIFICATION: dict[str, Any] = {"negative_cases": [], "checks": {}}


class OptimizationCheckpointQualification(unittest.TestCase):
    def test_01_roundtrip_all_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = Fixture(7)
            target = Fixture(91)
            save_result = save_fixture(root, source)
            load_result = load_fixture(root, target)
            self.assertTrue(nested_equal(source.snapshot(), target.snapshot()))
            self.assertEqual(save_result.generation, 0)
            self.assertEqual(load_result.generation, 0)
            QUALIFICATION["checks"]["roundtrip"] = "PASS"

    def test_02_post_load_controlled_update_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = Fixture(13)
            save_fixture(root, source)
            target = Fixture(101)
            load_fixture(root, target)
            for fixture in (source, target):
                schedule = fixture.progression.state
                for index, (_, optimizer) in enumerate(fixture.actor_optimizers):
                    scheduled_lr = linear_lr_for_next_update(0.011 + index * 0.003, schedule)
                    for group in optimizer.param_groups:
                        group["lr"] = scheduled_lr
                scheduled_critic_lr = linear_lr_for_next_update(0.017, schedule)
                for group in fixture.critic_optimizer.param_groups:
                    group["lr"] = scheduled_critic_lr
            self.assertAlmostEqual(
                target.actor_optimizers[0][1].param_groups[0]["lr"],
                0.011 * (1.0 - 2.0 / 12.0),
                places=15,
            )
            source.controlled_update()
            target.controlled_update()
            self.assertTrue(nested_equal(source.snapshot(), target.snapshot()))
            self.assertEqual(source.progression.state.completed_update_index, 2)
            QUALIFICATION["checks"]["post_load_controlled_update"] = "PASS"
            QUALIFICATION["checks"]["progression_schedule"] = "PASS"

    def test_03_generations_and_failed_save_preserve_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = Fixture(19)
            first = save_fixture(root, fixture)
            first_pointer = (root / "latest.json").read_bytes()
            fixture.controlled_update()
            second = save_fixture(root, fixture)
            self.assertEqual((first.generation, second.generation), (0, 1))
            self.assertTrue(first.generation_directory.is_dir())
            second_pointer = (root / "latest.json").read_bytes()
            self.assertNotEqual(first_pointer, second_pointer)

            def fail(phase: str) -> None:
                if phase == "after_readback_validation":
                    raise RuntimeError("injected save failure")

            fixture.controlled_update()
            with self.assertRaisesRegex(RuntimeError, "injected save failure"):
                save_fixture(root, fixture, injector=fail)
            self.assertEqual((root / "latest.json").read_bytes(), second_pointer)
            self.assertTrue(first.generation_directory.is_dir())
            self.assertTrue(second.generation_directory.is_dir())
            self.assertEqual(validate_optimization_checkpoint(root).generation, 1)
            QUALIFICATION["checks"]["atomic_generation_publish"] = "PASS"
            QUALIFICATION["checks"]["failed_save_old_generation_preserved"] = "PASS"

    def test_04_failed_apply_rolls_back_every_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save_fixture(root, Fixture(23))
            target = Fixture(109)
            before = target.snapshot()

            def fail(phase: str) -> None:
                if phase == "after_actor_optimizers":
                    raise RuntimeError("injected apply failure")

            with self.assertRaisesRegex(OptimizationCheckpointLoadError, "TARGET_ROLLED_BACK"):
                load_fixture(root, target, injector=fail)
            self.assertTrue(nested_equal(before, target.snapshot()))
            QUALIFICATION["checks"]["failed_load_target_rollback"] = "PASS"

    def test_05_negative_matrix(self) -> None:
        boundary_cases = {
            "boundary_transaction_incomplete": {"transaction_complete": False},
            "boundary_partial_update": {"partial_update": True},
            "boundary_optimizer_mutation_incomplete": {"optimizer_mutation_complete": False},
            "boundary_valuenorm_mutation_incomplete": {"value_normalizer_mutation_complete": False},
            "boundary_active_backward": {"active_backward": True},
            "boundary_active_optimizer_step": {"active_optimizer_step": True},
            "boundary_active_load": {"active_load": True},
            "boundary_poisoned": {"poisoned": True},
        }
        clean = OptimizationCheckpointBoundaryState.clean().__dict__
        for name, changes in boundary_cases.items():
            with self.subTest(name=name):
                state = OptimizationCheckpointBoundaryState(**{**clean, **changes})
                with tempfile.TemporaryDirectory() as temp:
                    fixture = Fixture(31)
                    with self.assertRaises(OptimizationCheckpointBoundaryError):
                        save_optimization_checkpoint(
                            checkpoint_root=temp,
                            boundary=state,
                            actor_modules=fixture.actors,
                            actor_optimizers=fixture.actor_optimizers,
                            critic_module=fixture.critic,
                            critic_optimizer=fixture.critic_optimizer,
                            value_normalizer=fixture.value_normalizer,
                            progression=fixture.progression.state,
                            semantic_config=SEMANTIC_CONFIG,
                        )
                QUALIFICATION["negative_cases"].append({"name": name, "expected_rejection": True, "result": "PASS"})

        mutation_cases = [
            ("missing_artifact", self._case_missing_artifact),
            ("artifact_digest_mismatch", self._case_digest_mismatch),
            ("unexpected_artifact", self._case_unexpected_artifact),
            ("manifest_schema_mismatch", lambda root: rewrite_manifest(root, lambda m: m.__setitem__("schema", "bad"))),
            ("manifest_incomplete_status", lambda root: rewrite_manifest(root, lambda m: m.__setitem__("status", "incomplete"))),
            ("optimizer_coverage_false", lambda root: rewrite_manifest(root, lambda m: m["state_coverage"].__setitem__("actor_optimizers", False))),
            ("actor_order_identity_mismatch", lambda root: rewrite_manifest(root, lambda m: m.__setitem__("actor_order", ["robot_1", "robot_0"]))),
            ("progression_next_index_invalid", self._case_bad_progression),
            ("actor_tensor_shape_mismatch", self._case_actor_shape),
            ("actor_optimizer_empty_state", self._case_optimizer_empty),
            ("actor_optimizer_moment_shape_mismatch", self._case_optimizer_moment_shape),
            ("critic_optimizer_group_mismatch", self._case_critic_group),
            ("latest_pointer_digest_mismatch", self._case_pointer_digest),
        ]
        for index, (name, mutate) in enumerate(mutation_cases):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                save_fixture(root, Fixture(41 + index))
                target = Fixture(151 + index)
                before = target.snapshot()
                mutate(root)
                with self.assertRaises(OptimizationCheckpointValidationError):
                    load_fixture(root, target)
                self.assertTrue(nested_equal(before, target.snapshot()))
                QUALIFICATION["negative_cases"].append({"name": name, "expected_rejection": True, "result": "PASS"})

        with self.subTest(name="semantic_config_mismatch"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save_fixture(root, Fixture(71))
            with self.assertRaisesRegex(OptimizationCheckpointValidationError, "semantic reconstruction"):
                validate_optimization_checkpoint(root, expected_semantic_config={**SEMANTIC_CONFIG, "algorithm": "haa2c"})
            QUALIFICATION["negative_cases"].append({"name": "semantic_config_mismatch", "expected_rejection": True, "result": "PASS"})

        with self.subTest(name="valuenorm_target_shape_mismatch"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save_fixture(root, Fixture(73))
            target = Fixture(173, value_shape=2)
            before = target.snapshot()
            with self.assertRaises(Exception):
                load_fixture(root, target)
            self.assertTrue(nested_equal(before, target.snapshot()))
            QUALIFICATION["negative_cases"].append({"name": "valuenorm_target_shape_mismatch", "expected_rejection": True, "result": "PASS"})

        with self.subTest(name="legacy_weights_only_optimization_reject"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            torch.save(Fixture(79).actors[0][1].state_dict(), root / "actor_agent0.pt")
            with self.assertRaisesRegex(
                OptimizationCheckpointValidationError,
                "OPTIMIZER_STATE_REQUIRED_FOR_OPTIMIZATION_CONTINUATION",
            ):
                validate_optimization_checkpoint(root)
            QUALIFICATION["negative_cases"].append({"name": "legacy_weights_only_optimization_reject", "expected_rejection": True, "result": "PASS"})

        with self.subTest(name="missing_latest_pointer"), tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(OptimizationCheckpointValidationError, "latest.json is missing"):
                validate_optimization_checkpoint(temp)
            QUALIFICATION["negative_cases"].append({"name": "missing_latest_pointer", "expected_rejection": True, "result": "PASS"})

        self.assertGreaterEqual(len(QUALIFICATION["negative_cases"]), 18)
        QUALIFICATION["checks"]["negative_matrix"] = "PASS"
        QUALIFICATION["checks"]["strict_pre_mutation_validation"] = "PASS"
        QUALIFICATION["checks"]["legacy_optimization_rejection"] = "PASS"

    def test_06_static_source_guards(self) -> None:
        implementation_path = SOURCE_DIR / "assignment_optimization_checkpoint.py"
        runner_path = SOURCE_DIR / "assignment_harl_training.py"
        implementation_source = implementation_path.read_text(encoding="utf-8")
        runner_source = runner_path.read_text(encoding="utf-8")
        implementation_tree = ast.parse(implementation_source)
        runner_tree = ast.parse(runner_source)
        public_functions = {
            node.name for node in implementation_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        self.assertTrue(
            {"save_optimization_checkpoint", "validate_optimization_checkpoint", "load_optimization_checkpoint"}
            <= public_functions
        )
        runner_class = next(
            node for node in runner_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "AssignmentOnPolicyHARunner"
        )
        runner_methods = {node.name for node in runner_class.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue(
            {
                "save_optimization_continuation_checkpoint",
                "validate_optimization_continuation_checkpoint",
                "restore_optimization_continuation_checkpoint",
                "apply_optimization_continuation_lr_schedule",
            }
            <= runner_methods
        )
        for forbidden in ("torch.cuda", "AppLauncher", "gym.make", "PPQ", "Layer-A", "RACQ"):
            self.assertNotIn(forbidden, implementation_source)
        QUALIFICATION["checks"]["static_source_guards"] = "PASS"

    @staticmethod
    def _case_missing_artifact(root: Path) -> None:
        directory = generation_dir(root)
        manifest = json.loads((directory / "checkpoint_manifest.json").read_text(encoding="utf-8"))
        path = directory / manifest["artifacts"][0]["path"]
        path.unlink()

    @staticmethod
    def _case_digest_mismatch(root: Path) -> None:
        directory = generation_dir(root)
        manifest = json.loads((directory / "checkpoint_manifest.json").read_text(encoding="utf-8"))
        path = directory / manifest["artifacts"][0]["path"]
        path.write_bytes(path.read_bytes() + b"corrupt")

    @staticmethod
    def _case_unexpected_artifact(root: Path) -> None:
        (generation_dir(root) / "unexpected.bin").write_bytes(b"unexpected")

    @staticmethod
    def _case_bad_progression(root: Path) -> None:
        directory = generation_dir(root)
        manifest_path = directory / "checkpoint_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = next(item for item in manifest["artifacts"] if item["component"] == "progression")
        path = directory / record["path"]
        progression = json.loads(path.read_text(encoding="utf-8"))
        progression["next_update_index"] += 2
        path.write_bytes(canonical_bytes(progression))
        record["sha256"] = sha256_path(path)
        manifest_path.write_bytes(canonical_bytes(manifest))
        refresh_pointer(root)

    @staticmethod
    def _case_actor_shape(root: Path) -> None:
        def change(state):
            first = next(iter(state))
            state[first] = state[first][:-1]
        rewrite_artifact(root, "actor_weights", change)

    @staticmethod
    def _case_optimizer_empty(root: Path) -> None:
        rewrite_artifact(root, "actor_optimizer", lambda state: state.__setitem__("state", {}))

    @staticmethod
    def _case_optimizer_moment_shape(root: Path) -> None:
        def change(state):
            first_entry = next(iter(state["state"].values()))
            first_entry["exp_avg"] = first_entry["exp_avg"].reshape(-1)[:-1]
        rewrite_artifact(root, "actor_optimizer", change)

    @staticmethod
    def _case_critic_group(root: Path) -> None:
        rewrite_artifact(root, "critic_optimizer", lambda state: state["param_groups"].append(copy.deepcopy(state["param_groups"][0])))

    @staticmethod
    def _case_pointer_digest(root: Path) -> None:
        path = root / "latest.json"
        pointer = json.loads(path.read_text(encoding="utf-8"))
        pointer["manifest_sha256"] = "0" * 64
        path.write_bytes(canonical_bytes(pointer))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OptimizationCheckpointQualification)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    output = {
        "schema": "phase_b2_t4_ckpt1_cpu_qualification_v1",
        "checkpoint_schema": OPTIMIZATION_CHECKPOINT_SCHEMA,
        "runtime_executed": False,
        "cuda_call_count": 0,
        "app_launcher_call_count": 0,
        "isaac_environment_instantiation_count": 0,
        "formal_supervisor_call_count": 0,
        "formal_worker_call_count": 0,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
        "checks": QUALIFICATION["checks"],
        "negative_cases": QUALIFICATION["negative_cases"],
        "negative_case_count": len(QUALIFICATION["negative_cases"]),
        "unexpected_negative_case_count": sum(case["result"] != "PASS" for case in QUALIFICATION["negative_cases"]),
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_bytes(canonical_bytes(output))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
