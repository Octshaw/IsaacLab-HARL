"""Phase 9G-8F-3 shared assignment checkpoint loader integration tests."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

import assignment_checkpoint_load as load_module  # noqa: E402
import assignment_harl_training as training_module  # noqa: E402
from assignment_checkpoint_contract import (  # noqa: E402
    NAMED_LIFECYCLE_ABLATION,
    AssignmentCheckpointContractManifest,
    CompatibilityPurpose,
    canonical_manifest_bytes,
    compute_manifest_sha256,
)
from assignment_checkpoint_load import (  # noqa: E402
    AssignmentCheckpointCompatibilityError,
    AssignmentCheckpointIntegrityError,
    AssignmentCheckpointInventoryError,
    AssignmentCheckpointMetadataError,
    build_assignment_evaluation_contract_manifest,
    load_assignment_checkpoint,
)
from assignment_checkpoint_save import (  # noqa: E402
    CONTRACT_FINGERPRINT_FILE,
    CONTRACT_MANIFEST_FILE,
    TRAINING_STATE_MANIFEST_FILE,
    AssignmentCheckpointSaveCoordinator,
)
from assignment_harl_training import AssignmentOnPolicyHARunner  # noqa: E402
from harl.runners.on_policy_ha_runner import OnPolicyHARunner  # noqa: E402
from test_assignment_checkpoint_contract_core import _changed  # noqa: E402
from test_assignment_checkpoint_save_metadata_integration import (  # noqa: E402
    HAPPO,
    _manifest,
    _wrapper_contract,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], *expected: str) -> Exception:
    try:
        func()
    except Exception as exc:
        message = str(exc)
        for text in expected:
            if text not in message:
                raise AssertionError(f"expected {text!r} in {message!r}") from exc
        return exc
    raise AssertionError(f"expected an exception containing {expected!r}")


class TrackingModule(torch.nn.Module):
    def __init__(self, seed: int) -> None:
        super().__init__()
        self.base = torch.nn.Linear(3, 2)
        self.register_buffer("counter", torch.tensor(seed, dtype=torch.int64))
        self.load_calls: list[bool] = []
        with torch.no_grad():
            self.base.weight.fill_(float(seed))
            self.base.bias.fill_(float(seed) + 0.5)

    def load_state_dict(self, state_dict, strict=True):
        self.load_calls.append(strict)
        return super().load_state_dict(state_dict, strict=strict)


def _modules(seed_offset: int = 0):
    actors = tuple(
        (f"robot_{index}", TrackingModule(seed_offset + index + 1))
        for index in range(3)
    )
    critic = TrackingModule(seed_offset + 20)
    value = TrackingModule(seed_offset + 30)
    return actors, critic, value


def _snapshot(modules) -> dict[int, dict[str, torch.Tensor]]:
    values = [module for _, module in modules[0]] + [modules[1], modules[2]]
    return {
        id(module): {
            key: value.detach().clone()
            for key, value in module.state_dict().items()
        }
        for module in values
    }


def _assert_snapshot(modules, snapshot, message: str) -> None:
    values = [module for _, module in modules[0]] + [modules[1], modules[2]]
    for module in values:
        for key, value in module.state_dict().items():
            _assert(torch.equal(value, snapshot[id(module)][key]), f"{message}: {key}")


def _save_native(
    root: Path,
    *,
    manifest: AssignmentCheckpointContractManifest | None = None,
    kind: str = "regular",
    directory: Path | None = None,
) -> tuple[Path, AssignmentCheckpointContractManifest, tuple, TrackingModule, TrackingModule]:
    manifest = manifest or _manifest()
    source_actors, source_critic, source_value = _modules()
    directory = directory or root / "models"
    AssignmentCheckpointSaveCoordinator(root).save_checkpoint(
        checkpoint_directory=directory,
        checkpoint_kind=kind,
        checkpoint_generation=4,
        manifest=manifest,
        actor_state_dicts=tuple(
            (name, module.state_dict()) for name, module in source_actors
        ),
        critic_state_dict=source_critic.state_dict(),
        value_normalizer_state_dict=(
            source_value.state_dict()
            if bool(manifest.training_contract["value_norm_enabled"])
            else None
        ),
    )
    return directory, manifest, source_actors, source_critic, source_value


def _load(
    directory: Path,
    manifest: AssignmentCheckpointContractManifest,
    targets,
    *,
    purpose: CompatibilityPurpose = CompatibilityPurpose.NORMAL_EVALUATION,
    acknowledgement: bool = False,
    ablation_name: str | None = None,
    fallback: bool = False,
):
    return load_assignment_checkpoint(
        checkpoint_directory=directory,
        purpose=purpose,
        current_manifest=manifest,
        actor_modules=targets[0],
        critic_module=targets[1],
        value_normalizer_module=targets[2],
        explicit_ablation_name=ablation_name,
        continuation_reset_acknowledged=acknowledgement,
        allow_unversioned_legacy_fallback=fallback,
    )


def _marker_mapping(directory: Path) -> dict[str, Any]:
    return json.loads((directory / TRAINING_STATE_MANIFEST_FILE).read_text(encoding="utf-8"))


def _write_marker(directory: Path, mapping: dict[str, Any]) -> None:
    (directory / TRAINING_STATE_MANIFEST_FILE).write_text(
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _replace_artifact_and_rebind_file(
    directory: Path,
    role: str,
    state_dict: dict[str, Any],
    *,
    actor_identity: str | None = None,
) -> None:
    marker = _marker_mapping(directory)
    if role == "actor":
        artifact = next(
            entry
            for entry in marker["actor_artifacts"]
            if entry["actor_identity"] == actor_identity
        )
    elif role == "critic":
        artifact = marker["critic_artifact"]
    else:
        artifact = marker["value_normalizer_artifact"]
    path = directory / artifact["relative_file_name"]
    torch.save(state_dict, path)
    artifact["file_size"] = path.stat().st_size
    artifact["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_marker(directory, marker)


def test_valid_native_evaluation_actor_only_and_weights_only_cpu() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, source_actors, _, _ = _save_native(Path(temp) / "run")
        targets = _modules(100)
        original_load = load_module.torch.load
        calls: list[dict[str, Any]] = []

        def spy_load(*args, **kwargs):
            calls.append(dict(kwargs))
            return original_load(*args, **kwargs)

        load_module.torch.load = spy_load
        try:
            result = _load(directory, manifest, targets)
        finally:
            load_module.torch.load = original_load
        _assert(result.compatibility_decision.classification == "normal_evaluation", "normal evaluation")
        _assert(result.loaded_actor_identities == ("robot_0", "robot_1", "robot_2"), "actors loaded")
        _assert(not result.critic_loaded and not result.value_normalizer_loaded, "actor-only")
        _assert(len(calls) == 3, "only actors deserialized")
        _assert(all(call == {"map_location": "cpu", "weights_only": True} for call in calls), "safe load kwargs")
        for (_, target), (_, source) in zip(targets[0], source_actors, strict=True):
            for key, value in source.state_dict().items():
                _assert(torch.equal(target.state_dict()[key], value), f"actor value {key}")
            _assert(target.load_calls == [True], "strict actor load")
        _assert(targets[1].load_calls == [] and targets[2].load_calls == [], "critic/ValueNorm untouched")


def test_actor_only_evaluation_contract_builder() -> None:
    schema, layout = _wrapper_contract("lifecycle_contract_c")
    names = ("robot_0", "robot_1", "robot_2")
    wrapper = SimpleNamespace(
        agents=names,
        assignment_observation_schema_manifest=schema,
        assignment_observation_layout=layout,
        assignment_lifecycle_profile_config={"profile_name": "lifecycle_contract_c"},
        share_observation_space={0: SimpleNamespace(shape=(3183,))},
    )
    actors = [HAPPO(), HAPPO(), HAPPO()]
    algo_args = {
        "model": {
            "hidden_sizes": [256, 256],
            "critic_lr": 0.0005,
        },
        "algo": {
            "share_param": False,
            "critic_num_mini_batch": 2,
            "value_loss_coef": 1.0,
            "gamma": 0.99,
            "gae_lambda": 0.95,
        },
        "train": {
            "use_valuenorm": True,
            "use_proper_time_limits": True,
            "episode_length": 1000,
            "n_rollout_threads": 20,
        },
    }
    lifecycle = build_assignment_evaluation_contract_manifest(
        wrapper=wrapper,
        actors=actors,
        algo_args=algo_args,
        algorithm_name="happo",
    )
    _assert(lifecycle.actor_schema["actor_dimension"] == 1059, "evaluation actor dimension")
    _assert(lifecycle.shared_schema["shared_dimension"] == 3183, "evaluation shared dimension")

    ablation_schema = copy.deepcopy(schema)
    ablation_schema["profile_name"] = "lifecycle_ablation"
    ablation_schema["mask_contract_version"] = "lifecycle_ablation_physical_mask_v1"
    ablation_schema["budget_release_contract"] = "disabled"
    wrapper.assignment_observation_schema_manifest = ablation_schema
    wrapper.assignment_lifecycle_profile_config = {"profile_name": "lifecycle_ablation"}
    ablation = build_assignment_evaluation_contract_manifest(
        wrapper=wrapper,
        actors=actors,
        algo_args=algo_args,
        algorithm_name="happo",
    )
    _assert(ablation.identity["profile_name"] == "lifecycle_ablation", "ablation profile")
    _assert(ablation.actor_schema["actor_dimension"] == 1059, "ablation actor dimension")


def test_valid_continuation_and_acknowledgement() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, source_actors, source_critic, source_value = _save_native(Path(temp) / "run")
        targets = _modules(100)
        result = _load(
            directory,
            manifest,
            targets,
            purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            acknowledgement=True,
        )
        _assert(result.critic_loaded and result.value_normalizer_loaded, "continuation global state")
        _assert(result.continuation_acknowledgement is not None, "ack recorded")
        _assert("best-reward" in result.continuation_acknowledgement, "complete reset acknowledgement")
        for (_, target), (_, source) in zip(targets[0], source_actors, strict=True):
            _assert(target.load_calls == [True], "actor strict continuation")
            _assert(all(torch.equal(target.state_dict()[k], v) for k, v in source.state_dict().items()), "actor")
        _assert(targets[1].load_calls == [True] and targets[2].load_calls == [True], "global strict")
        _assert(
            all(torch.equal(targets[1].state_dict()[k], v) for k, v in source_critic.state_dict().items()),
            "critic loaded",
        )
        _assert(
            all(torch.equal(targets[2].state_dict()[k], v) for k, v in source_value.state_dict().items()),
            "ValueNorm loaded",
        )


def test_missing_acknowledgement_prevents_mutation() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        targets = _modules(100)
        before = _snapshot(targets)
        _expect_raises(
            lambda: _load(
                directory,
                manifest,
                targets,
                purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            ),
            "acknowledgement_required",
        )
        _assert_snapshot(targets, before, "missing acknowledgement")
        _assert(all(module.load_calls == [] for _, module in targets[0]), "no actor mutation")


def test_completion_marker_missing_before_deserialization() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / TRAINING_STATE_MANIFEST_FILE).unlink()
        targets = _modules(100)
        original_load = load_module.torch.load
        calls = 0

        def forbidden_load(*args, **kwargs):
            nonlocal calls
            calls += 1
            raise AssertionError("deserialization must not occur")

        load_module.torch.load = forbidden_load
        try:
            _expect_raises(lambda: _load(directory, manifest, targets), "incomplete")
        finally:
            load_module.torch.load = original_load
        _assert(calls == 0, "no deserialization")


def test_contract_pair_and_fingerprint_failures() -> None:
    for missing in (CONTRACT_MANIFEST_FILE, CONTRACT_FINGERPRINT_FILE):
        with tempfile.TemporaryDirectory() as temp:
            directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
            (directory / missing).unlink()
            _expect_raises(lambda: _load(directory, manifest, _modules(100)), "both exist or both be absent")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / CONTRACT_FINGERPRINT_FILE).write_bytes(b"0" * 64 + b"\n")
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "does not match")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        directory, manifest, _, _, _ = _save_native(root)
        legacy = _manifest("legacy")
        (root / CONTRACT_MANIFEST_FILE).write_bytes(canonical_manifest_bytes(legacy) + b"\n")
        (root / CONTRACT_FINGERPRINT_FILE).write_bytes(
            compute_manifest_sha256(legacy).encode("ascii") + b"\n"
        )
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "run-root contracts disagree")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        marker = _marker_mapping(directory)
        marker["contract_fingerprint"] = "a" * 64
        _write_marker(directory, marker)
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "does not match")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        marker = _marker_mapping(directory)
        marker["actor_artifacts"] = marker["actor_artifacts"][:-1]
        _write_marker(directory, marker)
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "complete")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        marker = _marker_mapping(directory)
        marker["critic_artifact"] = None
        _write_marker(directory, marker)
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "must declare critic_agent.pt")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        mapping = manifest.to_mapping()
        mapping["manifest_format_version"] = "unsupported"
        (directory / CONTRACT_MANIFEST_FILE).write_text(
            json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "unsupported")


def test_declared_file_integrity_and_full_model_conflicts() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / "actor_agent_robot_0.pt").write_bytes(b"modified")
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "size")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        actor_path = directory / "actor_agent_robot_0.pt"
        payload = bytearray(actor_path.read_bytes())
        payload[-1] ^= 1
        actor_path.write_bytes(payload)
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "SHA-256")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / "actor_agent_robot_1.pt").unlink()
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "missing/non-regular")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / "actor_agent_0.pt").write_bytes(b"numeric")
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "unexpected/numeric")

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        (directory / "critic_agent_full.pt").write_bytes(b"pickle")
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "full-model pickle")


def test_tensor_inventory_mismatches() -> None:
    invalid_states = (
        {"base.weight": torch.ones(2, 3), "counter": torch.tensor(1)},
        {
            "base.weight": torch.ones(2, 3),
            "base.bias": torch.ones(2),
            "counter": torch.tensor(1),
            "unexpected": torch.ones(1),
        },
        {
            "base.weight": torch.ones(3, 3),
            "base.bias": torch.ones(2),
            "counter": torch.tensor(1),
        },
        {
            "base.weight": torch.ones(2, 3, dtype=torch.float64),
            "base.bias": torch.ones(2),
            "counter": torch.tensor(1),
        },
        {
            "base.weight": torch.ones(2, 3),
            "base.bias": torch.ones(2),
            "counter": "non-tensor",
        },
    )
    for invalid in invalid_states:
        with tempfile.TemporaryDirectory() as temp:
            directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
            _replace_artifact_and_rebind_file(
                directory,
                "actor",
                invalid,
                actor_identity="robot_2",
            )
            _expect_raises(
                lambda: _load(directory, manifest, _modules(100)),
                "inventory",
            )

    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        marker = _marker_mapping(directory)
        marker["actor_artifacts"][0]["tensor_inventory_sha256"] = "b" * 64
        _write_marker(directory, marker)
        _expect_raises(lambda: _load(directory, manifest, _modules(100)), "tensor_inventory_sha256")


def test_no_partial_mutation_on_third_actor_or_global_failure() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        invalid = {
            "base.weight": torch.ones(4, 3),
            "base.bias": torch.ones(2),
            "counter": torch.tensor(1),
        }
        _replace_artifact_and_rebind_file(
            directory,
            "actor",
            invalid,
            actor_identity="robot_2",
        )
        targets = _modules(100)
        before = _snapshot(targets)
        _expect_raises(lambda: _load(directory, manifest, targets), "inventory")
        _assert_snapshot(targets, before, "third actor inspection failure")
        _assert(all(module.load_calls == [] for _, module in targets[0]), "no actor load calls")

    for role in ("critic", "value_normalizer"):
        with tempfile.TemporaryDirectory() as temp:
            directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
            invalid = {
                "base.weight": torch.ones(4, 3),
                "base.bias": torch.ones(2),
                "counter": torch.tensor(1),
            }
            _replace_artifact_and_rebind_file(directory, role, invalid)
            targets = _modules(100)
            before = _snapshot(targets)
            _expect_raises(
                lambda: _load(
                    directory,
                    manifest,
                    targets,
                    purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                    acknowledgement=True,
                ),
                "inventory",
            )
            _assert_snapshot(targets, before, f"{role} inspection failure")
            _assert(all(module.load_calls == [] for _, module in targets[0]), "actors remain untouched")


def test_structural_inspection_is_read_only() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        targets = _modules(100)
        before = _snapshot(targets)
        result = _load(
            directory,
            manifest,
            targets,
            purpose=CompatibilityPurpose.STRUCTURAL_INSPECTION,
        )
        _assert(result.compatibility_decision.classification == "structurally_compatible", "structural")
        _assert(result.loaded_actor_identities == (), "no loaded actors")
        _assert_snapshot(targets, before, "structural read only")
        _assert(all(module.load_calls == [] for _, module in targets[0]), "no strict load")


def test_named_lifecycle_ablation_exact_and_evaluation_only() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, checkpoint_manifest, _, _, _ = _save_native(Path(temp) / "run")
        ablation_mapping = checkpoint_manifest.to_mapping()
        ablation_mapping["identity"]["profile_name"] = "lifecycle_ablation"
        ablation_mapping["identity"]["training_time_profile"] = "lifecycle_ablation"
        behavior = ablation_mapping["lifecycle_behavior_contract"]
        behavior["resolver_contract_version"] = "disabled"
        behavior["mask_contract_version"] = "lifecycle_ablation_physical_mask_v1"
        behavior["budget_release_contract_version"] = "disabled"
        ablation = AssignmentCheckpointContractManifest.from_mapping(ablation_mapping)
        result = _load(
            directory,
            ablation,
            _modules(100),
            purpose=CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            ablation_name=NAMED_LIFECYCLE_ABLATION,
        )
        _assert(result.named_ablation_used == NAMED_LIFECYCLE_ABLATION, "named ablation")

        _expect_raises(
            lambda: _load(
                directory,
                ablation,
                _modules(100),
                purpose=CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            ),
            "unknown_or_missing_ablation",
        )
        _expect_raises(
            lambda: _load(
                directory,
                ablation,
                _modules(100),
                purpose=CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
                ablation_name="wrong",
            ),
            "unknown_or_missing_ablation",
        )
        unauthorized = _changed(
            ablation,
            "lifecycle_behavior_contract.legacy_guardrail_profile",
            "unauthorized",
        )
        _expect_raises(
            lambda: _load(
                directory,
                unauthorized,
                _modules(100),
                purpose=CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
                ablation_name=NAMED_LIFECYCLE_ABLATION,
            ),
            "ablation_mismatch",
        )
        _expect_raises(
            lambda: _load(
                directory,
                ablation,
                _modules(100),
                purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                acknowledgement=True,
                ablation_name=NAMED_LIFECYCLE_ABLATION,
            ),
            "continuation_contract_mismatch",
        )


def _write_unversioned_legacy(directory: Path, modules, *, numeric: bool) -> None:
    directory.mkdir(parents=True)
    for index, (identity, module) in enumerate(modules[0]):
        name = f"actor_agent_{index}.pt" if numeric else f"actor_agent_{identity}.pt"
        torch.save(module.state_dict(), directory / name)


def test_explicit_unversioned_legacy_fallback() -> None:
    legacy = _manifest("legacy")
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "legacy"
        source = _modules()
        _write_unversioned_legacy(directory, source, numeric=True)
        targets = _modules(100)
        result = _load(directory, legacy, targets, fallback=True)
        _assert(result.legacy_fallback_used, "legacy fallback")
        _assert(result.checkpoint_kind == "unversioned_legacy", "legacy kind")
        _assert(all(module.load_calls == [True] for _, module in targets[0]), "legacy strict")

    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "legacy"
        _write_unversioned_legacy(directory, _modules(), numeric=True)
        _expect_raises(lambda: _load(directory, legacy, _modules(100)), "explicit")
        _expect_raises(
            lambda: _load(directory, _manifest(), _modules(100), fallback=True),
            "metadata-free checkpoint is not permitted",
        )
        _expect_raises(
            lambda: _load(
                directory,
                legacy,
                _modules(100),
                purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                acknowledgement=True,
                fallback=True,
            ),
            "evaluation/inspection only",
        )
        torch.save(_modules()[0][0][1].state_dict(), directory / "actor_agent_robot_0.pt")
        _expect_raises(lambda: _load(directory, legacy, _modules(100), fallback=True), "exactly one")

    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "legacy"
        _write_unversioned_legacy(directory, _modules(), numeric=False)
        (directory / "actor_agent_robot_0_full.pt").write_bytes(b"pickle")
        _expect_raises(lambda: _load(directory, legacy, _modules(100), fallback=True), "full-model")


def test_unsupported_fine_tuning_and_exact_resume_before_load() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory, manifest, _, _, _ = _save_native(Path(temp) / "run")
        original_load = load_module.torch.load
        load_module.torch.load = lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("must not deserialize")
        )
        try:
            _expect_raises(
                lambda: _load(
                    directory,
                    manifest,
                    _modules(100),
                    purpose=CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING,
                ),
                "not supported",
            )
            _expect_raises(
                lambda: _load(
                    directory,
                    manifest,
                    _modules(100),
                    purpose=CompatibilityPurpose.EXACT_TRAINING_RESUME,
                ),
                "exact resume is unsupported",
            )
        finally:
            load_module.torch.load = original_load


def test_assignment_runner_restore_uses_shared_loader_only() -> None:
    runner = AssignmentOnPolicyHARunner.__new__(AssignmentOnPolicyHARunner)
    runner.assignment_rl = True
    runner.algo_args = {"train": {"model_dir": "checkpoint"}}
    runner.env_args = {"acknowledge_weight_continuation_reset": True}
    runner.actor = [
        SimpleNamespace(actor=TrackingModule(1)),
        SimpleNamespace(actor=TrackingModule(2)),
        SimpleNamespace(actor=TrackingModule(3)),
    ]
    runner.critic = SimpleNamespace(critic=TrackingModule(20))
    runner.value_normalizer = TrackingModule(30)
    runtime = SimpleNamespace(ordered_agent_names=("robot_0", "robot_1", "robot_2"))
    manifest = _manifest()
    calls: list[dict[str, Any]] = []
    original_capture = training_module.capture_assignment_checkpoint_runtime_state
    original_build = training_module.build_assignment_checkpoint_contract_manifest
    original_loader = training_module.load_assignment_checkpoint
    original_restore = OnPolicyHARunner.restore
    training_module.capture_assignment_checkpoint_runtime_state = lambda current: runtime
    training_module.build_assignment_checkpoint_contract_manifest = lambda state: manifest
    training_module.load_assignment_checkpoint = lambda **kwargs: calls.append(kwargs) or "loaded"
    OnPolicyHARunner.restore = lambda self: (_ for _ in ()).throw(
        AssertionError("inherited restore must not run")
    )
    try:
        result = runner.restore()
    finally:
        training_module.capture_assignment_checkpoint_runtime_state = original_capture
        training_module.build_assignment_checkpoint_contract_manifest = original_build
        training_module.load_assignment_checkpoint = original_loader
        OnPolicyHARunner.restore = original_restore
    _assert(result == "loaded" and len(calls) == 1, "shared loader once")
    _assert(calls[0]["purpose"] == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION, "purpose")
    _assert(calls[0]["continuation_reset_acknowledged"] is True, "ack")

    runner.env_args["acknowledge_weight_continuation_reset"] = False
    _expect_raises(lambda: runner.restore(), "explicit")


def test_all_five_entry_point_boundaries_and_direct_load_scan() -> None:
    paths = {
        "train": REPO_ROOT / "scripts/reinforcement_learning/harl/train.py",
        "generic_play": REPO_ROOT / "scripts/reinforcement_learning/harl/play.py",
        "assignment_play": REPO_ROOT / "scripts/reinforcement_learning/harl/play_assignment.py",
        "diagnostics": REPO_ROOT / "scripts/environments/evaluate_assignment_rl_playback_diagnostics.py",
        "comparison": REPO_ROOT / "scripts/environments/evaluate_assignment_methods.py",
    }
    texts = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    training_source = (
        SCAN_TASK_SOURCE / "assignment_harl_training.py"
    ).read_text(encoding="utf-8")
    _assert("load_assignment_checkpoint(" in training_source, "train continuation shared loader")
    _assert("--acknowledge-weight-continuation-reset" in texts["train"], "training ack CLI")
    _assert("Use play_assignment.py" in texts["generic_play"], "generic assignment hard guard")
    _assert(
        texts["generic_play"].index("Use play_assignment.py")
        < texts["generic_play"].index("RUNNER_REGISTRY"),
        "generic guard before runner import/construction",
    )
    for name in ("assignment_play", "diagnostics"):
        _assert("load_assignment_checkpoint(" in texts[name], f"{name} shared loader")
        _assert("torch.load(" not in texts[name], f"{name} no direct torch.load")
        _assert("def _load_assignment_actors" not in texts[name], f"{name} duplicate removed")
    _assert("torch.load(" not in texts["comparison"], "comparison no direct load")
    _assert("hard-rejects before any checkpoint load" in texts["comparison"], "comparison hard guard")


TESTS = (
    test_valid_native_evaluation_actor_only_and_weights_only_cpu,
    test_actor_only_evaluation_contract_builder,
    test_valid_continuation_and_acknowledgement,
    test_missing_acknowledgement_prevents_mutation,
    test_completion_marker_missing_before_deserialization,
    test_contract_pair_and_fingerprint_failures,
    test_declared_file_integrity_and_full_model_conflicts,
    test_tensor_inventory_mismatches,
    test_no_partial_mutation_on_third_actor_or_global_failure,
    test_structural_inspection_is_read_only,
    test_named_lifecycle_ablation_exact_and_evaluation_only,
    test_explicit_unversioned_legacy_fallback,
    test_unsupported_fine_tuning_and_exact_resume_before_load,
    test_assignment_runner_restore_uses_shared_loader_only,
    test_all_five_entry_point_boundaries_and_direct_load_scan,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    failures: list[str] = []
    for test in TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failures.append(test.__name__)
            print(f"FAIL {test.__name__}: {exc!r}")
    passed = len(TESTS) - len(failures)
    if failures:
        print(f"FAIL {passed}/{len(TESTS)} tests; failures={failures}")
        return 1
    print(f"PASS {passed}/{len(TESTS)} tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
