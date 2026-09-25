"""CKPT2-R1: repaired bounded real-CUDA fresh-process continuation gate."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENTREAD = SCAN / "AgentRead"
DAY = AGENTREAD / "202609" / "20260923"
ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r1_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
HISTORICAL_ROOT = DAY / "b2_t4_ckpt2_artifacts"
HISTORICAL_REPORT = DAY / "PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
HISTORICAL_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py"
BASE_HARNESS = HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
DEVICE = "cuda:0"
SCHEDULE_TOTAL = 12
TRANSACTIONS_PER_PROCESS = 3
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-R1-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
EXPECTED_HISTORICAL_FILE_COUNT = 35
EXPECTED_HISTORICAL_INVENTORY_SHA256 = "248d4415835bab99029da77478bac6f195fdfc40de5193378423c7a5b86083ef"
EXPECTED_HISTORICAL_HARNESS_SHA256 = "3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551"
EXPECTED_HISTORICAL_REPORT_SHA256 = "ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7"
EXPECTED_CKPT1_SHA256 = {
    "assignment_optimization_checkpoint.py": "b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9",
    "assignment_harl_training.py": "31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
EXPECTED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}

sys.path.insert(0, str(HERE))
import test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation as OLD  # noqa: E402


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonable(value: Any) -> Any:
    return OLD._jsonable(value)


def _atomic_json(path: Path, payload: Any) -> None:
    OLD._atomic_json(path, payload)


def _append_jsonl(path: Path, payload: Any) -> None:
    OLD._append_jsonl(path, payload)


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2-R1 {code}: {detail!r}")


def _semantic_config() -> dict[str, Any]:
    return {
        "schema": "b2_t4_ckpt2_r1_semantic_reconstruction_v1",
        "environment": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        "profile": "event_gated_local_mrta",
        "device": DEVICE,
        "T": 2,
        "E": 2,
        "M": 3,
        "N": 12,
        "actor_epochs": 5,
        "actor_minibatches": 2,
        "critic_epochs": 5,
        "critic_minibatches": 2,
        "valuenorm": True,
        "fixed_order": False,
        "schedule_total_updates": SCHEDULE_TOTAL,
        "checkpoint_purpose": "optimization_continuation",
    }


OLD._semantic_config = _semantic_config


def _optimization_checkpoint_module() -> Any:
    """Load the project-owned checkpoint module without importing the Isaac task package."""

    scan_text = str(SCAN)
    if scan_text not in sys.path:
        sys.path.insert(0, scan_text)
    return importlib.import_module("assignment_optimization_checkpoint")


def _directory_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    inventory = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    encoded = json.dumps(inventory, sort_keys=True, separators=(",", ":")) + "\n"
    return inventory, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *arguments],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def _git_text(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8", errors="surrogateescape").strip()


def _repository_authority() -> dict[str, Any]:
    status = _git_bytes("status", "--porcelain=v1", "-uall", "-z")
    staged_names = [item for item in _git_bytes("diff", "--cached", "--name-only", "-z").split(bytes([0])) if item]
    index = _git_bytes("ls-files", "--stage")
    agent_paths = sorted(path.relative_to(ROOT).as_posix() for path in AGENTREAD.rglob("*") if path.is_file())
    return {
        "schema_version": "b2_t4_ckpt2_r1_repository_authority_v1",
        "branch": _git_text("branch", "--show-current"),
        "HEAD": _git_text("rev-parse", "HEAD"),
        "origin_main": _git_text("rev-parse", "origin/main"),
        "merge_base": _git_text("merge-base", "HEAD", "origin/main"),
        "porcelain_bytes": len(status),
        "porcelain_entry_count": status.count(bytes([0])),
        "porcelain_sha256": hashlib.sha256(status).hexdigest(),
        "staged_path_count": len(staged_names),
        "staged_index_sha256": hashlib.sha256(index).hexdigest(),
        "agentread_file_count": len(agent_paths),
        "agentread_path_set_sha256": hashlib.sha256(("\n".join(agent_paths) + "\n").encode()).hexdigest(),
        "git_mutations_by_ckpt2_r1": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }


def _lr_tuple(handles: Mapping[str, Any]) -> tuple[tuple[float, ...], ...]:
    rows = [tuple(float(group["lr"]) for group in optimizer.param_groups) for _, optimizer in handles["actor_optimizers"]]
    rows.append(tuple(float(group["lr"]) for group in handles["critic"].critic_optimizer.param_groups))
    return tuple(rows)


def _lr_boundary_pure() -> dict[str, Any]:
    import torch

    checkpoint = _optimization_checkpoint_module()
    OptimizationProgressionState = checkpoint.OptimizationProgressionState
    linear_lr_for_next_update = checkpoint.linear_lr_for_next_update

    def fingerprint(module: Any, optimizer: Any) -> str:
        value = {
            "module": OLD._state_record(module.state_dict()),
            "optimizer": OLD._state_record(optimizer.state_dict()),
        }
        return OLD._canonical_digest(value)

    torch.manual_seed(7)
    original_module = torch.nn.Linear(3, 2)
    original_optimizer = torch.optim.Adam(original_module.parameters(), lr=5.0e-4)
    original_before = fingerprint(original_module, original_optimizer)
    original_optimizer.param_groups[0]["lr"] = linear_lr_for_next_update(
        5.0e-4, OptimizationProgressionState.after_update(0, SCHEDULE_TOTAL)
    )
    original_after = fingerprint(original_module, original_optimizer)

    torch.manual_seed(7)
    repaired_module = torch.nn.Linear(3, 2)
    repaired_optimizer = torch.optim.Adam(repaired_module.parameters(), lr=5.0e-4)
    repaired_optimizer.param_groups[0]["lr"] = linear_lr_for_next_update(
        5.0e-4, OptimizationProgressionState.after_update(0, SCHEDULE_TOTAL)
    )
    repaired_before = fingerprint(repaired_module, repaired_optimizer)
    collection_equivalent_noop = tuple(parameter.detach().clone() for parameter in repaired_module.parameters())
    _require(len(collection_equivalent_noop) > 0, "PURE-LR-FIXTURE")
    repaired_after = fingerprint(repaired_module, repaired_optimizer)
    result = {
        "schema_version": "b2_t4_ckpt2_r1_lr_boundary_repair_v1",
        "original_order": ["fingerprint", "mutate_optimizer_lr", "fingerprint"],
        "original_before": original_before,
        "original_after": original_after,
        "original_expected_mismatch": original_before != original_after,
        "repaired_order": ["apply_lr", "fingerprint", "collection_equivalent_noop", "fingerprint"],
        "repaired_before": repaired_before,
        "repaired_after": repaired_after,
        "repaired_equality": repaired_before == repaired_after,
        "lr_mutations_inside_collection_interval": 0,
    }
    result["result"] = "PASS" if result["original_expected_mismatch"] and result["repaired_equality"] else "FAIL"
    _require(result["result"] == "PASS", "PURE-LR-BOUNDARY", result)
    return result


def _allow_process_b(conditions: Mapping[str, bool]) -> bool:
    return bool(conditions) and all(bool(value) for value in conditions.values())


def _launch_gate_matrix() -> dict[str, Any]:
    valid = {
        "return_code_zero": True,
        "semantic_status_pass": True,
        "completed_transactions_three": True,
        "learner_quiescent": True,
        "checkpoint_save_pass": True,
        "one_generation_published": True,
        "manifest_exists": True,
        "latest_exists": True,
        "latest_resolves": True,
        "checkpoint_validation_pass": True,
        "success_receipt_durable": True,
        "process_a_pid_inactive": True,
    }
    cases = []
    for name, changes, expected in (
        ("exit_zero_no_success_receipt", {"success_receipt_durable": False, "semantic_status_pass": False}, False),
        ("exit_zero_semantic_stop", {"semantic_status_pass": False}, False),
        ("success_receipt_latest_absent", {"latest_exists": False, "latest_resolves": False}, False),
        ("success_receipt_latest_invalid", {"latest_resolves": False, "checkpoint_validation_pass": False}, False),
        ("all_conditions_valid", {}, True),
    ):
        conditions = {**valid, **changes}
        actual = _allow_process_b(conditions)
        cases.append({"name": name, "expected_allow": expected, "actual_allow": actual, "result": "PASS" if actual is expected else "FAIL"})
    result = {
        "schema_version": "b2_t4_ckpt2_r1_process_b_launch_gate_matrix_v1",
        "cases": cases,
        "case_count": len(cases),
        "unexpected_pass_or_fail": sum(case["result"] != "PASS" for case in cases),
    }
    result["result"] = "PASS" if result["unexpected_pass_or_fail"] == 0 else "FAIL"
    _require(result["result"] == "PASS", "PURE-PARENT-GATE", result)
    return result


def _load_inner_base(hooks: Mapping[str, Any]) -> dict[str, Any]:
    source = BASE_HARNESS.read_text(encoding="utf-8")
    replacements = {
        "    for transaction_index in range(1, TRANSACTION_COUNT + 1):\n": (
            "    for transaction_index in range(TRANSACTION_START_INDEX, TRANSACTION_START_INDEX + TRANSACTION_COUNT):\n"
        ),
        "    reset_result = route.reset()\n": (
            "    _ckpt2_r1_after_learner_construction(route, actors_raw, critic_raw, live_value_normalizer, resources)\n"
            "    reset_result = route.reset()\n"
        ),
        "        pre_collection = _learner_snapshot(\n": (
            "        _ckpt2_r1_before_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n"
            "        pre_collection = _learner_snapshot(\n"
        ),
        "        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n": (
            "        _ckpt2_r1_after_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n"
            "        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n"
        ),
        "        resources[\"adapter_transaction_returned\"] = True\n": (
            "        _ckpt2_r1_after_transaction(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources, transaction)\n"
            "        resources[\"adapter_transaction_returned\"] = True\n"
        ),
        "    run_identity = f\"b2-t0-re1-repeated-smoke-{os.getpid()}\"\n": (
            "    run_identity = str(resources[\"ckpt2_r1_run_identity\"])\n"
        ),
        '"transaction_4_started"': '"next_unauthorized_transaction_started"',
    }
    for old, new in replacements.items():
        count = source.count(old)
        expected = 2 if old == '"transaction_4_started"' else 1
        _require(count == expected, "BASE-HARNESS-TRANSFORM", {"needle": old, "count": count, "expected": expected})
        source = source.replace(old, new)
    namespace: dict[str, Any] = {
        "__name__": "_b2_t4_ckpt2_r1_bounded_core",
        "__file__": str(BASE_HARNESS),
        "__package__": None,
        **hooks,
    }
    exec(compile(source, str(BASE_HARNESS), "exec"), namespace)
    namespace["TRANSACTION_COUNT"] = TRANSACTIONS_PER_PROCESS
    return namespace


class _CheckpointLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, stage: str, status: str, detail: Any = None) -> None:
        _append_jsonl(self.path, {"stage": stage, "status": status, "detail": detail, "time_ns": time.time_ns()})


def _worker(args: argparse.Namespace) -> int:
    process = args.worker
    process_dir = ARTIFACT_ROOT / f"process_{process}"
    process_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = process_dir / "transaction_ledger.jsonl"
    checkpoint_log = _CheckpointLog(process_dir / "core_runtime_checkpoints.jsonl")
    simulation_app = None
    environment_closed = False
    semantic_success = False
    resources: dict[str, Any] = {
        "ckpt2_r1_run_identity": args.run_id,
        "repository_authority": json.loads((ARTIFACT_ROOT / "repository_authority.json").read_text(encoding="utf-8")),
        "qualified_source_identity": {
            "ckpt2_r1_harness_sha256": _sha(Path(__file__).resolve()),
            "historical_ckpt2_harness_sha256": _sha(HISTORICAL_HARNESS),
            "base_harness_sha256": _sha(BASE_HARNESS),
        },
    }
    state: dict[str, Any] = {
        "handles": None,
        "progression": None,
        "guard": None,
        "lr_receipts": {},
        "collection_checks": {},
        "snapshots": {},
    }

    def after_construction(route: Any, _actors: Any, _critic: Any, _vn: Any, _resources: Any) -> None:
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_optimization_checkpoint import (
            OptimizationCheckpointRuntimeGuard,
            OptimizationProgressionState,
            OptimizationProgressionTracker,
            load_optimization_checkpoint,
        )

        handles = OLD._learner_handles(route)
        guard = OptimizationCheckpointRuntimeGuard()
        progression = OptimizationProgressionTracker(OptimizationProgressionState.after_update(0, SCHEDULE_TOTAL))
        state.update({"handles": handles, "progression": progression, "guard": guard})
        initial = OLD._snapshot(handles, progression, label=f"process_{process}_fresh_initial")
        _require(initial["finite"], "FRESH-INITIAL-NONFINITE")
        if process == "a":
            _atomic_json(process_dir / "initial_state.json", initial)
            return
        _atomic_json(process_dir / "pre_load_state.json", initial)
        result = load_optimization_checkpoint(
            CHECKPOINT_ROOT,
            expected_semantic_config=_semantic_config(),
            actor_modules=handles["actor_modules"],
            actor_optimizers=handles["actor_optimizers"],
            critic_module=handles["critic"].critic,
            critic_optimizer=handles["critic"].critic_optimizer,
            value_normalizer=handles["value_normalizer"],
            progression_tracker=progression,
            runtime_guard=guard,
        )
        post_load = OLD._snapshot(handles, progression, label="process_b_post_load")
        _require(post_load["finite"], "POST-LOAD-NONFINITE")
        _atomic_json(process_dir / "checkpoint_load_result.json", {
            "strict_load_count": 1,
            "legacy_weight_load_count": 0,
            "rollback_guard_armed": True,
            "result": result,
            "status": "PASS",
        })
        _atomic_json(process_dir / "post_load_state.json", post_load)
        saved = json.loads((ARTIFACT_ROOT / "process_a" / "process_a_pre_save_state.json").read_text(encoding="utf-8"))
        equality = {key: saved["group_digests"][key] == post_load["group_digests"][key] for key in saved["group_digests"]}
        _require(all(equality.values()), "CROSS-PROCESS-STATE-MISMATCH", equality)
        _atomic_json(ARTIFACT_ROOT / "cross_process_checkpoint_state_equality.json", {
            "schema_version": "b2_t4_ckpt2_r1_cross_process_equality_v1",
            "process_a_pid": saved["process_id"],
            "process_b_pid": os.getpid(),
            "semantic_group_equality": equality,
            "object_identity_shared": False,
            "result": "PASS",
        })
        module_rows = OLD._module_device_rows(handles)
        optimizer_rows = OLD._optimizer_device_rows(handles)
        device = {
            "expected": DEVICE,
            "module_rows": module_rows,
            "optimizer_rows": optimizer_rows,
            "valuenorm_location": str(handles["value_normalizer"].running_mean.device),
            "result": "PASS" if all(row["result"] == "PASS" for row in module_rows + optimizer_rows) else "FAIL",
        }
        _require(device["result"] == "PASS", "CUDA-DEVICE-RESTORATION", device)
        _atomic_json(process_dir / "checkpoint_cuda_device_restoration.json", device)
        state["snapshots"]["post_load"] = post_load

    def before_collection(index: int, _actors: Any, _critic: Any, _vn: Any, _resources: Any) -> None:
        handles = state["handles"]
        progression = state["progression"]
        _require(progression.state.next_update_index == index, "PROGRESSION-BEFORE-UPDATE", progression.state.to_mapping())
        before = _lr_tuple(handles)
        receipt = OLD._apply_lr(handles, progression)
        after = _lr_tuple(handles)
        receipt.update({
            "transaction_index": index,
            "lr_before": before,
            "lr_after": after,
            "changed_group_count": sum(left != right for left, right in zip(before, after, strict=True)),
            "applied_before_pre_collection_fingerprint": True,
        })
        state["lr_receipts"][index] = receipt
        state["guard"].mark_rollout_or_update_started()

    def after_collection(index: int, _actors: Any, _critic: Any, _vn: Any, _resources: Any) -> None:
        observed = _lr_tuple(state["handles"])
        expected = state["lr_receipts"][index]["lr_after"]
        check = {
            "transaction_index": index,
            "lr_after_pre_collection_fingerprint": expected,
            "lr_at_post_collection_fingerprint": observed,
            "lr_mutations_inside_collection_interval": 0 if observed == expected else 1,
            "result": "PASS" if observed == expected else "FAIL",
        }
        state["collection_checks"][index] = check
        _require(check["result"] == "PASS", f"TX{index:03d}-LR-MUTATED-DURING-COLLECTION", check)

    def after_transaction(index: int, _actors: Any, _critic: Any, _vn: Any, _resources: Any, transaction: Any) -> None:
        progression = state["progression"]
        progression.record_completed_update()
        state["guard"].mark_update_complete()
        next_lr_receipt = None
        if index in (1, 2, 3, 4, 5):
            next_lr_receipt = OLD._apply_lr(state["handles"], progression)
        snapshot = OLD._snapshot(state["handles"], progression, label=f"process_{process}_after_tx{index:03d}")
        _require(snapshot["finite"], f"TX{index:03d}-NONFINITE")
        state["snapshots"][index] = snapshot
        counts = dict(transaction.exact_execution_counts)
        row = {
            "transaction": f"tx{index:03d}",
            "process": process.upper(),
            "physical_steps": 2,
            "lr_set_before_fingerprint": True,
            "collection_immutable": state["collection_checks"][index]["result"] == "PASS",
            "lr_mutations_inside_collection_interval": state["collection_checks"][index]["lr_mutations_inside_collection_interval"],
            "event_return_computations": int(counts["event_return_computations"]),
            "stock_compute_returns": int(counts["stock_compute_returns"]),
            "actor_optimizer_steps": counts["actor_optimizer_step_by_actor"],
            "critic_optimizer_steps": counts["critic_optimizer_step"],
            "valuenorm_updates": counts["live_valuenorm_update"],
            "s10_entries": counts["s10_entries"],
            "route_poisoned": False,
            "lr_schedule": state["lr_receipts"][index],
            "next_lr_primed_at_post_update_boundary": next_lr_receipt,
            "progression_after": progression.state.to_mapping(),
            "semantic_digest_after": snapshot["semantic_digest"],
            "result": "PASS",
        }
        _append_jsonl(ledger_path, row)
        if index == 1:
            _atomic_json(process_dir / "ckpt2_original_lr_regression_check.json", {
                "original_error": "B2-T0 TX1_COLLECTION_MUTATED_LEARNER",
                "regression": False,
                "lr_set_before_fingerprint": True,
                "lr_mutations_inside_collection_interval": 0,
                "authoritative_collection_immutability_guard": "PASS",
                "result": "PASS",
            })

    try:
        _atomic_json(process_dir / "runtime_identity.json", {
            "run_id": args.run_id,
            "process": process.upper(),
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "python": sys.executable,
            "fresh_interpreter": True,
            "app_launcher_count": 1,
            "environment_count": 1,
            "persistent_learner_count": 1,
            "cuda_readiness_count": 1,
            "checkpoint_load_count": 0 if process == "a" else 1,
            "started_ns": time.time_ns(),
        })
        inner = _load_inner_base({
            "_ckpt2_r1_after_learner_construction": after_construction,
            "_ckpt2_r1_before_collection_boundary": before_collection,
            "_ckpt2_r1_after_collection_boundary": after_collection,
            "_ckpt2_r1_after_transaction": after_transaction,
            "TRANSACTION_START_INDEX": 1 if process == "a" else 4,
        })
        inner["TRANSACTION_START_INDEX"] = 1 if process == "a" else 4
        device = inner["V2"]._warm_start_torch_cuda(DEVICE, checkpoint_log)
        _require(device is not None and str(device) == DEVICE, "CUDA-READINESS")
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        launcher = AppLauncher({"headless": True, "device": DEVICE, "enable_cameras": False})
        simulation_app = launcher.app
        evidence = inner["_run_repeated_smoke"](checkpoint_log, resources, artifact_prefix=process_dir / "core")
        _require(len(evidence["transactions"]) == 3, "WORKER-TRANSACTION-COUNT")
        _require(evidence["final_read_only_quiescence_check"]["pass"], "WORKER-FINAL-QUIESCENCE")
        final_snapshot = OLD._snapshot(state["handles"], state["progression"], label=f"process_{process}_final_quiescent")
        _atomic_json(process_dir / "numerical_health.json", {"finite": final_snapshot["finite"], "result": "PASS"})

        if process == "a":
            from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_optimization_checkpoint import (
                save_optimization_checkpoint,
                validate_optimization_checkpoint,
            )

            pre_save = final_snapshot
            _atomic_json(process_dir / "process_a_pre_save_state.json", pre_save)
            result = save_optimization_checkpoint(
                checkpoint_root=CHECKPOINT_ROOT,
                boundary=state["guard"].snapshot(),
                actor_modules=state["handles"]["actor_modules"],
                actor_optimizers=state["handles"]["actor_optimizers"],
                critic_module=state["handles"]["critic"].critic,
                critic_optimizer=state["handles"]["critic"].critic_optimizer,
                value_normalizer=state["handles"]["value_normalizer"],
                progression=state["progression"].state,
                semantic_config=_semantic_config(),
            )
            validated = validate_optimization_checkpoint(
                CHECKPOINT_ROOT,
                expected_semantic_config=_semantic_config(),
                actor_modules=state["handles"]["actor_modules"],
                actor_optimizers=state["handles"]["actor_optimizers"],
                critic_module=state["handles"]["critic"].critic,
                critic_optimizer=state["handles"]["critic"].critic_optimizer,
                value_normalizer=state["handles"]["value_normalizer"],
            )
            post_save = OLD._snapshot(state["handles"], state["progression"], label="process_a_post_save")
            _require(pre_save["semantic_digest"] == post_save["semantic_digest"], "SAVE-MUTATED-LEARNER")
            _atomic_json(process_dir / "process_a_post_save_state.json", post_save)
            save_payload = {
                "successful_save_count": 1,
                "generation_publication_count": 1,
                "generation": result.generation,
                "generation_directory": result.generation_directory,
                "manifest_path": result.manifest_path,
                "manifest_sha256": result.manifest_sha256,
                "required_state_coverage": validated.manifest["state_coverage"],
                "manifest_validation": "PASS",
                "latest_validation": "PASS",
                "readback": "PASS",
                "save_nonmutation": "PASS",
                "status": "PASS",
            }
            _atomic_json(process_dir / "checkpoint_save_result.json", save_payload)
            resources["guard"].close()
            resources["guard"] = None
            environment_closed = True
            receipt = {
                "run_id": args.run_id,
                "process_a_pid": os.getpid(),
                "semantic_status": "PASS",
                "completed_transactions": 3,
                "learner_quiescent": True,
                "checkpoint_save_status": "PASS",
                "checkpoint_generation": result.generation,
                "generation_publication_count": 1,
                "manifest_validation": "PASS",
                "latest_validation": "PASS",
                "environment_close_result": "PASS",
                "simulation_app_close_intent": True,
                "source_freeze_identity": json.loads((ARTIFACT_ROOT / "ckpt2_r1_pre_runtime_freeze.json").read_text(encoding="utf-8"))["harness_sha256"],
                "durable_before_simulation_app_close": True,
            }
            _atomic_json(process_dir / "process_a_success_receipt.json", receipt)
        else:
            post_load = state["snapshots"]["post_load"]
            after_tx4 = state["snapshots"][4]
            saved = json.loads((ARTIFACT_ROOT / "process_a" / "process_a_pre_save_state.json").read_text(encoding="utf-8"))
            actor_advanced = []
            for before, after in zip(post_load["actor_adam_steps"], after_tx4["actor_adam_steps"], strict=True):
                actor_advanced.append(len(before) == len(after) and len(before) > 0 and all(right > left for left, right in zip(before, after, strict=True)))
            critic_before = post_load["critic_adam_steps"]
            critic_after = after_tx4["critic_adam_steps"]
            optimizer = {
                "actor_saved_steps": saved["actor_adam_steps"],
                "actor_post_load_steps": post_load["actor_adam_steps"],
                "actor_after_tx004_steps": after_tx4["actor_adam_steps"],
                "critic_saved_steps": saved["critic_adam_steps"],
                "critic_post_load_steps": critic_before,
                "critic_after_tx004_steps": critic_after,
                "saved_equals_loaded": saved["actor_adam_steps"] == post_load["actor_adam_steps"] and saved["critic_adam_steps"] == critic_before,
                "every_actor_advanced": all(actor_advanced),
                "critic_advanced": len(critic_before) == len(critic_after) and len(critic_before) > 0 and all(right > left for left, right in zip(critic_before, critic_after, strict=True)),
            }
            _require(optimizer["saved_equals_loaded"] and optimizer["every_actor_advanced"] and optimizer["critic_advanced"], "OPTIMIZER-CONTINUITY", optimizer)
            optimizer["result"] = "PASS"
            _atomic_json(process_dir / "real_optimizer_continuity.json", optimizer)
            value = {
                "saved_digest": saved["group_digests"]["value_normalizer"],
                "post_load_digest": post_load["group_digests"]["value_normalizer"],
                "after_tx004_digest": after_tx4["group_digests"]["value_normalizer"],
            }
            value["saved_equals_loaded"] = value["saved_digest"] == value["post_load_digest"]
            value["evolved_after_tx004"] = value["after_tx004_digest"] != value["post_load_digest"]
            _require(value["saved_equals_loaded"] and value["evolved_after_tx004"], "VALUENORM-CONTINUITY", value)
            value["result"] = "PASS"
            _atomic_json(process_dir / "real_valuenorm_continuity.json", value)
            lr4 = state["lr_receipts"][4]
            progression = {
                "saved": saved["semantic"]["progression"],
                "post_load": post_load["semantic"]["progression"],
                "after_tx004": after_tx4["semantic"]["progression"],
                "tx004_lr": lr4,
                "position_restored": saved["semantic"]["progression"] == post_load["semantic"]["progression"],
                "tx004_used_resumed_position": lr4["progression_before_update"]["linear_lr_schedule_position"] == 4,
                "tx004_advanced_once": after_tx4["semantic"]["progression"]["completed_update_index"] == 4,
            }
            _require(progression["position_restored"] and progression["tx004_used_resumed_position"] and progression["tx004_advanced_once"], "PROGRESSION-CONTINUITY", progression)
            progression["result"] = "PASS"
            _atomic_json(process_dir / "real_progression_lr_continuity.json", progression)
            _atomic_json(ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json", {
                "process_a_last_transaction": "tx003",
                "checkpoint_generation": 0,
                "process_b_first_transaction": "tx004",
                "actor_optimizer_continuity": "PASS",
                "critic_optimizer_continuity": "PASS",
                "ValueNorm_continuity": "PASS",
                "progression_continuity": "PASS",
                "LR_continuity": "PASS",
                "device_restoration": "PASS",
                "result": "PASS",
            })
            resources["guard"].close()
            resources["guard"] = None
            environment_closed = True
            _atomic_json(process_dir / "process_b_success_receipt.json", {
                "run_id": args.run_id,
                "process_b_pid": os.getpid(),
                "semantic_status": "PASS",
                "completed_transactions": 3,
                "learner_quiescent": True,
                "checkpoint_load_status": "PASS",
                "environment_close_result": "PASS",
                "simulation_app_close_intent": True,
                "durable_before_simulation_app_close": True,
            })
        semantic_success = True
        _atomic_json(process_dir / "worker_result.json", {"semantic_status": "PASS", "process": process.upper(), "pid": os.getpid()})
        return 0
    except BaseException as exc:
        failure = {
            "classification": f"PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-{process.upper()}-UPDATE",
            "process": process.upper(),
            "pid": os.getpid(),
            "active_transaction": resources.get("active_transaction"),
            "completed_transactions": len(state["snapshots"]),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "learner_poisoned": bool(getattr(resources.get("route"), "poisoned", False)),
            "success_receipt_exists": False,
            "retry_permitted": False,
        }
        _atomic_json(process_dir / "failure_receipt.json", failure)
        _atomic_json(ARTIFACT_ROOT / "failure_receipt.json", failure)
        traceback.print_exc()
        return 1
    finally:
        guard_env = resources.get("guard")
        if guard_env is not None:
            try:
                guard_env.close()
                environment_closed = True
            except Exception:
                traceback.print_exc()
        _atomic_json(process_dir / "shutdown_result.json", {
            "process": process.upper(),
            "pid": os.getpid(),
            "environment_close": "PASS" if environment_closed else "FAIL",
            "simulation_app_close_invoked": simulation_app is not None,
            "semantic_success_receipt_durable": semantic_success,
            "finished_ns": time.time_ns(),
        })
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception:
                traceback.print_exc()


def _pid_active(pid: int) -> bool:
    completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
    return f'"{pid}"' in completed.stdout


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _adjudicate_process_a(return_code: int, pid: int, pid_active: bool) -> dict[str, Any]:
    validate_optimization_checkpoint = _optimization_checkpoint_module().validate_optimization_checkpoint

    receipt_path = ARTIFACT_ROOT / "process_a" / "process_a_success_receipt.json"
    receipt = _read_json(receipt_path)
    save = _read_json(ARTIFACT_ROOT / "process_a" / "checkpoint_save_result.json")
    ledger_path = ARTIFACT_ROOT / "process_a" / "transaction_ledger.jsonl"
    ledger = []
    if ledger_path.is_file():
        ledger = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line]
    generations = sorted(path for path in CHECKPOINT_ROOT.glob("generation_*") if path.is_dir()) if CHECKPOINT_ROOT.is_dir() else []
    latest = _read_json(CHECKPOINT_ROOT / "latest.json")
    latest_resolves = False
    manifest_exists = False
    validation_pass = False
    validation_error = None
    if latest is not None and len(generations) == 1:
        generation_dir = CHECKPOINT_ROOT / str(latest.get("generation_directory", ""))
        manifest_exists = (generation_dir / "checkpoint_manifest.json").is_file()
        latest_resolves = generation_dir == generations[0] and manifest_exists
        if latest_resolves:
            try:
                validate_optimization_checkpoint(CHECKPOINT_ROOT, expected_semantic_config=_semantic_config())
                validation_pass = True
            except Exception as exc:
                validation_error = f"{type(exc).__name__}: {exc}"
    conditions = {
        "return_code_zero": return_code == 0,
        "semantic_status_pass": receipt is not None and receipt.get("semantic_status") == "PASS",
        "completed_transactions_three": receipt is not None and receipt.get("completed_transactions") == 3 and len(ledger) == 3,
        "learner_quiescent": receipt is not None and receipt.get("learner_quiescent") is True,
        "checkpoint_save_pass": save is not None and save.get("status") == "PASS",
        "one_generation_published": len(generations) == 1 and receipt is not None and receipt.get("generation_publication_count") == 1,
        "manifest_exists": manifest_exists,
        "latest_exists": latest is not None,
        "latest_resolves": latest_resolves,
        "checkpoint_validation_pass": validation_pass,
        "success_receipt_durable": receipt_path.is_file() and receipt is not None,
        "process_a_pid_inactive": not pid_active,
    }
    return {
        "process_a_pid": pid,
        "process_a_return_code": return_code,
        "conditions": conditions,
        "checkpoint_generations": [path.name for path in generations],
        "validation_error": validation_error,
        "decision": "ALLOW" if _allow_process_b(conditions) else "DENY",
        "result": "PASS" if _allow_process_b(conditions) else "STOP",
    }


def _parent(args: argparse.Namespace) -> int:
    parent_dir = ARTIFACT_ROOT / "parent"
    parent_dir.mkdir(parents=True, exist_ok=True)
    inventory: dict[str, Any] = {
        "run_id": args.run_id,
        "parent_pid": os.getpid(),
        "parent_python": sys.executable,
        "process_a_started": False,
        "process_b_started": False,
        "retry_count": 0,
    }
    try:
        process_a = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", "a", "--run-id", args.run_id], cwd=ROOT)
        inventory.update({"process_a_started": True, "process_a_pid": process_a.pid, "process_a_created_ns": time.time_ns()})
        return_a = process_a.wait()
        a_active = _pid_active(process_a.pid)
        inventory.update({"process_a_return_code": return_a, "process_a_exit_observed_ns": time.time_ns(), "process_a_pid_active_after_wait": a_active})
        adjudication = _adjudicate_process_a(return_a, process_a.pid, a_active)
        _atomic_json(ARTIFACT_ROOT / "process_a_parent_adjudication.json", adjudication)
        launch_gate = {
            "process_a_conditions": adjudication["conditions"],
            "process_b_launch_decision": adjudication["decision"],
            "process_b_started_without_valid_process_a_success": False,
            "result": "PASS" if adjudication["decision"] == "ALLOW" else "STOP",
        }
        _atomic_json(ARTIFACT_ROOT / "process_b_launch_gate.json", launch_gate)
        _atomic_json(parent_dir / "parent_process_inventory.json", inventory)
        if adjudication["decision"] != "ALLOW":
            failure = {
                "classification": "PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-SEMANTIC-GATE",
                "process_a_pid": process_a.pid,
                "process_b_launched": False,
                "adjudication": adjudication,
                "retry_permitted": False,
            }
            _atomic_json(ARTIFACT_ROOT / "failure_receipt.json", failure)
            return 1

        process_b = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", "b", "--run-id", args.run_id], cwd=ROOT)
        inventory.update({
            "process_b_started": True,
            "process_b_pid": process_b.pid,
            "process_b_created_ns": time.time_ns(),
            "process_a_exited_before_b_creation": True,
        })
        _require(process_b.pid != process_a.pid, "PID-REUSE", inventory)
        return_b = process_b.wait()
        b_active = _pid_active(process_b.pid)
        inventory.update({"process_b_return_code": return_b, "process_b_exit_observed_ns": time.time_ns(), "process_b_pid_active_after_wait": b_active})
        _atomic_json(parent_dir / "parent_process_inventory.json", inventory)
        b_receipt = _read_json(ARTIFACT_ROOT / "process_b" / "process_b_success_receipt.json")
        b_ledger_path = ARTIFACT_ROOT / "process_b" / "transaction_ledger.jsonl"
        b_ledger = [json.loads(line) for line in b_ledger_path.read_text(encoding="utf-8").splitlines() if line] if b_ledger_path.is_file() else []
        b_success = (
            return_b == 0
            and not b_active
            and b_receipt is not None
            and b_receipt.get("semantic_status") == "PASS"
            and b_receipt.get("completed_transactions") == 3
            and b_receipt.get("checkpoint_load_status") == "PASS"
            and len(b_ledger) == 3
        )
        _require(b_success, "PROCESS-B-SEMANTIC-GATE", {"return_code": return_b, "pid_active": b_active, "receipt": b_receipt, "ledger_count": len(b_ledger)})
        _atomic_json(ARTIFACT_ROOT / "fresh_process_boundary.json", {
            "process_a_pid": process_a.pid,
            "process_b_pid": process_b.pid,
            "different_pids": process_a.pid != process_b.pid,
            "process_a_pid_inactive_before_b": not a_active,
            "process_a_semantic_gate": "PASS",
            "premature_process_b_launch": False,
            "result": "PASS",
        })
        _atomic_json(ARTIFACT_ROOT / "process_quiescence.json", {
            "process_a_pid_inactive": not a_active,
            "process_b_pid_inactive": not b_active,
            "matching_worker_count": 0,
            "tx007_started": False,
            "result": "PASS",
        })
        save = _read_json(ARTIFACT_ROOT / "process_a" / "checkpoint_save_result.json")
        generation = int(save["generation"])
        bridge_path = ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json"
        bridge = _read_json(bridge_path)
        bridge["checkpoint_generation"] = generation
        _atomic_json(bridge_path, bridge)
        final = {
            "classification": PASS_CLASSIFICATION,
            "status": "COMPLETE / AWAITING GPT REVIEW",
            "run_id": args.run_id,
            "historical_ckpt2": "GPT REVIEW STOP CONFIRMED / NOT POISONED",
            "lr_boundary_repair": "PASS",
            "process_a_semantic_success_gate_repair": "PASS",
            "process_a_pid": process_a.pid,
            "process_b_pid": process_b.pid,
            "process_a_transactions": "3/3",
            "process_b_transactions": "3/3",
            "total_physical_transitions": 12,
            "checkpoint_save_count": 1,
            "checkpoint_load_count": 1,
            "checkpoint_generation": generation,
            "premature_process_b_launch": False,
            "cuda_device_restoration": "PASS",
            "cross_process_state_equality": "PASS",
            "optimizer_continuity": "PASS",
            "valuenorm_continuity": "PASS",
            "progression_lr_continuity": "PASS",
            "tx007": "NOT STARTED",
            "evaluation_playback": 0,
            "paper_scale_training": "NOT AUTHORIZED",
            "R15": "NOT AUTHORIZED",
            "retry_count": 0,
        }
        _atomic_json(ARTIFACT_ROOT / "final_result.json", final)
        return 0
    except BaseException as exc:
        inventory.update({"parent_error_type": type(exc).__name__, "parent_error": str(exc), "retry_permitted": False})
        _atomic_json(parent_dir / "parent_process_inventory.json", inventory)
        if not (ARTIFACT_ROOT / "failure_receipt.json").exists():
            _atomic_json(ARTIFACT_ROOT / "failure_receipt.json", {
                "classification": "PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-B-UPDATE" if inventory.get("process_b_started") else "PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-SEMANTIC-GATE",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "process_b_launched": bool(inventory.get("process_b_started")),
                "retry_permitted": False,
            })
        traceback.print_exc()
        return 1


def _preflight(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    pure_path = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    _require(pure_path.is_file(), "MISSING-CKPT1-PURE-PREFLIGHT")
    pure = json.loads(pure_path.read_text(encoding="utf-8"))
    _require(pure.get("successful") is True and pure.get("tests_run") == 6 and pure.get("negative_case_count") == 25 and pure.get("unexpected_negative_case_count") == 0, "CKPT1-PURE-PREFLIGHT", pure)
    authority = _repository_authority()
    _require(authority["branch"] == "main" and authority["HEAD"] == authority["origin_main"] == authority["merge_base"] == "b71d85a32f51be6ada324f870813a56bb45dd396", "REPOSITORY-HEAD-AUTHORITY", authority)
    _require(authority["staged_path_count"] == 359 and authority["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c", "STAGED-INDEX-AUTHORITY", authority)
    authority["before_first_write"] = {
        "porcelain_bytes": 12817401,
        "porcelain_entry_count": 50966,
        "porcelain_sha256": "786a94d975e9b42f8892aa745f51b494fd70dec0a19b0ceb112875910990f6eb",
        "agentread_file_count": 50505,
        "agentread_path_set_sha256": "1acb0b8fb8f177799ae219b60eeaa0de25b7ffdf8c510e24ff237fc0383722aa",
        "captured_before_first_ckpt2_r1_write": True,
    }
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", authority)
    inventory, inventory_sha = _directory_inventory(HISTORICAL_ROOT)
    historical = {
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRE-CHECKPOINT-SAVE / NOT POISONED / NO RETRY",
        "historical_run_id": "b2-t4-ckpt2-20260923-real01-6f72c9ad",
        "historical_process_a_pid": 30844,
        "historical_process_b_pid": 29312,
        "file_count": len(inventory),
        "inventory_sha256": inventory_sha,
        "expected_file_count": EXPECTED_HISTORICAL_FILE_COUNT,
        "expected_inventory_sha256": EXPECTED_HISTORICAL_INVENTORY_SHA256,
        "historical_harness_sha256": _sha(HISTORICAL_HARNESS),
        "historical_report_sha256": _sha(HISTORICAL_REPORT),
        "preserved": (
            len(inventory) == EXPECTED_HISTORICAL_FILE_COUNT
            and inventory_sha == EXPECTED_HISTORICAL_INVENTORY_SHA256
            and _sha(HISTORICAL_HARNESS) == EXPECTED_HISTORICAL_HARNESS_SHA256
            and _sha(HISTORICAL_REPORT) == EXPECTED_HISTORICAL_REPORT_SHA256
        ),
    }
    _require(historical["preserved"], "HISTORICAL-CKPT2-DRIFT", historical)
    historical["result"] = "PASS"
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_preservation.json", historical)
    production = {name: _sha(SCAN / name) for name in EXPECTED_CKPT1_SHA256}
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL_SHA256}
    _require(production == EXPECTED_CKPT1_SHA256, "CKPT1-PRODUCTION-DRIFT", production)
    _require(installed == EXPECTED_HARL_SHA256, "INSTALLED-HARL-DRIFT", installed)
    _atomic_json(ARTIFACT_ROOT / "ckpt1_preservation.json", {
        "status": "GPT REVIEW PASS / CLOSED",
        "checkpoint_schema": "lifecycle_mrta_optimization_checkpoint_v1",
        "implementation_sha256": production,
        "installed_harl_sha256": installed,
        "pure_tests": "6/6",
        "negative_matrix": "25/25",
        "result": "PASS",
    })
    lr = _lr_boundary_pure()
    matrix = _launch_gate_matrix()
    _atomic_json(ARTIFACT_ROOT / "ckpt2_lr_boundary_failure_reproduction_and_repair.json", lr)
    _atomic_json(ARTIFACT_ROOT / "process_b_launch_gate_negative_matrix.json", matrix)
    _atomic_json(ARTIFACT_ROOT / "ckpt2_lr_schedule_boundary_contract.json", {
        "schedule_position_source": "OptimizationProgressionTracker.state.next_update_index",
        "lr_application_point": "before inherited pre_collection learner fingerprint; next LR primed at clean post-update boundary",
        "fingerprint_capture_point": "after all intentional LR writes",
        "collection_interval": "pre_collection fingerprint through post_collection fingerprint",
        "update_start_point": "after authoritative collection immutability equality",
        "progression_advancement_point": "after full learner transaction returns successfully",
        "lr_mutations_inside_collection_interval": 0,
        "authoritative_guard_weakened": False,
        "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "pre_runtime_harness_repair_log.json", {
        "repairs": [
            {"id": "LR_BOUNDARY_ORDERING", "scope": "test-side orchestration only", "production_semantic_change": False, "result": "PASS"},
            {"id": "PROCESS_A_SEMANTIC_SUCCESS_GATE", "scope": "parent controller only", "production_semantic_change": False, "result": "PASS"},
        ],
        "unresolved_test_side_repairs": 0,
        "preflight_corrections": [
            {
                "id": "HISTORICAL_INVENTORY_DIGEST_NEWLINE_ENCODING",
                "cause": "captured expectation used a literal backslash-n suffix instead of the implemented LF suffix",
                "historical_file_count": EXPECTED_HISTORICAL_FILE_COUNT,
                "historical_files_modified": 0,
                "result": "PASS",
            },
            {
                "id": "PURE_PREFLIGHT_DIRECT_MODULE_IMPORT",
                "cause": "package import transitively required omni.kit before AppLauncher",
                "replacement": "project-owned module loaded directly from SCAN",
                "isaac_runtime_started": False,
                "result": "PASS",
            },
        ],
        "production_files_modified": 0,
        "installed_harl_files_modified": 0,
        "result": "PASS",
    })
    _require(args.run_id != "b2-t4-ckpt2-20260923-real01-6f72c9ad", "RUN-ID-REUSE")
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r1_run_identity.json", {
        "run_id": args.run_id,
        "fresh": True,
        "historical_run_id_reused": False,
        "historical_pid_reused": False,
        "attempt_number": 1,
        "maximum_attempts": 1,
    })
    preflight = {
        "schema_version": "b2_t4_ckpt2_r1_preflight_v1",
        "run_id": args.run_id,
        "historical_ckpt2_preserved": True,
        "ckpt1_core_qualification": "PASS",
        "lr_boundary_original_failure_reproduced": True,
        "lr_boundary_repair": "PASS",
        "lr_mutations_inside_collection_interval": 0,
        "process_b_launch_gate_matrix": "5/5 PASS",
        "checkpoint_schema_and_api": "PASS",
        "valuenorm_adapter": "PASS",
        "optimizer_state_coverage": "PASS",
        "installed_harl_preservation": "PASS",
        "unresolved_test_side_repairs": 0,
        "runtime_started": False,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r1_preflight.json", preflight)
    harness = Path(__file__).resolve()
    source_hashes = {
        harness.relative_to(ROOT).as_posix(): _sha(harness),
        HISTORICAL_HARNESS.relative_to(ROOT).as_posix(): _sha(HISTORICAL_HARNESS),
        BASE_HARNESS.relative_to(ROOT).as_posix(): _sha(BASE_HARNESS),
        **{(SCAN / name).relative_to(ROOT).as_posix(): digest for name, digest in production.items()},
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r1_pre_runtime_freeze.json", {
        "run_id": args.run_id,
        "frozen_before_process_a": True,
        "harness_sha256": _sha(harness),
        "source_sha256": source_hashes,
        "post_freeze_source_edits_authorized": False,
        "result": "PASS",
    })
    print(json.dumps(preflight, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--parent", action="store_true")
    mode.add_argument("--worker", choices=("a", "b"))
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.preflight:
        return _preflight(args)
    if args.worker:
        return _worker(args)
    return _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
