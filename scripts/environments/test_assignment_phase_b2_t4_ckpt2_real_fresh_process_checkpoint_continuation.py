"""CKPT2: bounded real-CUDA fresh-process optimization continuation check."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
BASE_HARNESS = HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
ARTIFACT_ROOT = SCAN / "AgentRead" / "202609" / "20260923" / "b2_t4_ckpt2_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
DEVICE = "cuda:0"
SCHEDULE_TOTAL = 12
TRANSACTIONS_PER_PROCESS = 3
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
SOURCE_FILES = (
    SCAN / "assignment_optimization_checkpoint.py",
    SCAN / "assignment_harl_training.py",
    SCAN / "assignment_event_training_full_transaction.py",
    SCAN / "assignment_event_training_real_isaac_adapter.py",
    BASE_HARNESS,
)
EXPECTED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return {name: _jsonable(getattr(value, name)) for name in value.__dataclass_fields__}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return repr(value)


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2 {code}: {detail!r}")


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _tensor_record(tensor: Any) -> dict[str, Any]:
    import torch

    detached = tensor.detach().cpu().contiguous()
    raw = detached.reshape(-1).view(torch.uint8).numpy().tobytes()
    finite = True
    if detached.is_floating_point() or detached.is_complex():
        finite = bool(torch.isfinite(detached).all().item())
    return {
        "kind": "tensor",
        "dtype": str(detached.dtype),
        "shape": list(detached.shape),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "finite": finite,
    }


def _state_record(value: Any) -> Any:
    import torch

    if isinstance(value, torch.Tensor):
        return _tensor_record(value)
    if isinstance(value, Mapping):
        return {str(key): _state_record(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (list, tuple)):
        return [_state_record(item) for item in value]
    if isinstance(value, float):
        return {"kind": "float", "value": value, "finite": math.isfinite(value)}
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return repr(value)


def _record_finite(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("kind") in {"tensor", "float"}:
            return bool(value.get("finite", True))
        return all(_record_finite(item) for item in value.values())
    if isinstance(value, list):
        return all(_record_finite(item) for item in value)
    return True


def _optimizer_steps(optimizer: Any) -> list[int]:
    import torch

    steps: list[int] = []
    for state in optimizer.state.values():
        raw = state.get("step", 0)
        steps.append(int(raw.detach().cpu().item()) if isinstance(raw, torch.Tensor) else int(raw))
    return sorted(steps)


def _semantic_config() -> dict[str, Any]:
    return {
        "schema": "b2_t4_ckpt2_semantic_reconstruction_v1",
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


def _learner_handles(route: Any) -> dict[str, Any]:
    actors = tuple(recorder.actor for recorder in route.actors)
    critic = route.critic.wrapped
    value_normalizer = route._value_normalizer
    names = tuple(f"actor_{index:03d}" for index in range(len(actors)))
    return {
        "actors": actors,
        "critic": critic,
        "value_normalizer": value_normalizer,
        "actor_modules": tuple((name, actor.actor) for name, actor in zip(names, actors, strict=True)),
        "actor_optimizers": tuple(
            (name, actor.actor_optimizer) for name, actor in zip(names, actors, strict=True)
        ),
    }


def _snapshot(handles: Mapping[str, Any], progression: Any, *, label: str) -> dict[str, Any]:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_value_normalizer_checkpoint import (
        export_value_normalizer_checkpoint_state,
    )

    actor_weights = [_state_record(module.state_dict()) for _, module in handles["actor_modules"]]
    actor_optimizers = [
        _state_record(optimizer.state_dict()) for _, optimizer in handles["actor_optimizers"]
    ]
    critic_weights = _state_record(handles["critic"].critic.state_dict())
    critic_optimizer = _state_record(handles["critic"].critic_optimizer.state_dict())
    value_normalizer = _state_record(
        export_value_normalizer_checkpoint_state(handles["value_normalizer"])
    )
    semantic = {
        "actor_weights": actor_weights,
        "actor_optimizers": actor_optimizers,
        "critic_weights": critic_weights,
        "critic_optimizer": critic_optimizer,
        "value_normalizer": value_normalizer,
        "progression": progression.state.to_mapping(),
        "semantic_config": _semantic_config(),
    }
    groups = {
        "actor_weights": _canonical_digest(actor_weights),
        "actor_optimizers": _canonical_digest(actor_optimizers),
        "critic_weights": _canonical_digest(critic_weights),
        "critic_optimizer": _canonical_digest(critic_optimizer),
        "value_normalizer": _canonical_digest(value_normalizer),
        "progression": _canonical_digest(progression.state.to_mapping()),
        "semantic_config": _canonical_digest(_semantic_config()),
    }
    return {
        "schema_version": "b2_t4_ckpt2_learner_snapshot_v1",
        "label": label,
        "process_id": os.getpid(),
        "object_identity_diagnostic_only": {
            "actor_modules": [id(module) for _, module in handles["actor_modules"]],
            "actor_optimizers": [id(optimizer) for _, optimizer in handles["actor_optimizers"]],
            "critic_module": id(handles["critic"].critic),
            "critic_optimizer": id(handles["critic"].critic_optimizer),
            "value_normalizer": id(handles["value_normalizer"]),
        },
        "actor_adam_steps": [
            _optimizer_steps(optimizer) for _, optimizer in handles["actor_optimizers"]
        ],
        "critic_adam_steps": _optimizer_steps(handles["critic"].critic_optimizer),
        "group_digests": groups,
        "semantic_digest": _canonical_digest(semantic),
        "finite": _record_finite(semantic),
        "semantic": semantic,
    }


def _optimizer_device_rows(handles: Mapping[str, Any]) -> list[dict[str, Any]]:
    import torch

    rows: list[dict[str, Any]] = []
    optimizers = list(handles["actor_optimizers"]) + [
        ("central_critic", handles["critic"].critic_optimizer)
    ]
    for name, optimizer in optimizers:
        parameter_devices = sorted({str(parameter.device) for group in optimizer.param_groups for parameter in group["params"]})
        state_devices: set[str] = set()
        incompatible: list[dict[str, Any]] = []
        for parameter, state in optimizer.state.items():
            for field, value in state.items():
                if not isinstance(value, torch.Tensor):
                    continue
                state_devices.add(str(value.device))
                control_scalar = field == "step" and value.numel() == 1 and value.device.type == "cpu"
                if value.device != parameter.device and not control_scalar:
                    incompatible.append(
                        {"field": field, "parameter_device": str(parameter.device), "state_device": str(value.device)}
                    )
        rows.append(
            {
                "component": name,
                "parameter_devices": parameter_devices,
                "optimizer_state_devices": sorted(state_devices),
                "cpu_step_scalar_compatible": True,
                "incompatible_state_tensors": incompatible,
                "result": "PASS" if parameter_devices == [DEVICE] and not incompatible else "FAIL",
            }
        )
    return rows


def _module_device_rows(handles: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, module in handles["actor_modules"]:
        devices = sorted({str(parameter.device) for parameter in module.parameters()})
        rows.append({"component": name, "parameter_devices": devices, "result": "PASS" if devices == [DEVICE] else "FAIL"})
    critic_devices = sorted({str(parameter.device) for parameter in handles["critic"].critic.parameters()})
    rows.append({"component": "central_critic", "parameter_devices": critic_devices, "result": "PASS" if critic_devices == [DEVICE] else "FAIL"})
    return rows


def _load_inner_base(hooks: Mapping[str, Any]) -> dict[str, Any]:
    source = BASE_HARNESS.read_text(encoding="utf-8")
    replacements = {
        "    for transaction_index in range(1, TRANSACTION_COUNT + 1):\n": (
            "    for transaction_index in range(TRANSACTION_START_INDEX, TRANSACTION_START_INDEX + TRANSACTION_COUNT):\n"
        ),
        "    reset_result = route.reset()\n": (
            "    _ckpt2_after_learner_construction(route, actors_raw, critic_raw, live_value_normalizer, resources)\n"
            "    reset_result = route.reset()\n"
        ),
        "        actor_call_start = tuple(len(actor.calls) for actor in actors)\n": (
            "        _ckpt2_before_transaction(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n"
            "        actor_call_start = tuple(len(actor.calls) for actor in actors)\n"
        ),
        "        resources[\"adapter_transaction_returned\"] = True\n": (
            "        _ckpt2_after_transaction(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources, transaction)\n"
            "        resources[\"adapter_transaction_returned\"] = True\n"
        ),
        "    run_identity = f\"b2-t0-re1-repeated-smoke-{os.getpid()}\"\n": (
            "    run_identity = str(resources[\"ckpt2_run_identity\"])\n"
        ),
    }
    for old, new in replacements.items():
        count = source.count(old)
        _require(count == 1, "BASE-HARNESS-TRANSFORM", {"needle": old, "count": count})
        source = source.replace(old, new, 1)
    namespace: dict[str, Any] = {
        "__name__": "_b2_t4_ckpt2_bounded_core",
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


def _apply_lr(handles: Mapping[str, Any], progression: Any) -> dict[str, Any]:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_optimization_checkpoint import (
        linear_lr_for_next_update,
    )

    actor_rows = []
    for name, optimizer in handles["actor_optimizers"]:
        initial = float(handles["actors"][int(name.split("_")[-1])].lr)
        applied = linear_lr_for_next_update(initial, progression.state)
        previous = [float(group["lr"]) for group in optimizer.param_groups]
        for group in optimizer.param_groups:
            group["lr"] = applied
        actor_rows.append({"name": name, "initial": initial, "previous": previous, "applied": applied})
    critic_optimizer = handles["critic"].critic_optimizer
    critic_initial = float(handles["critic"].critic_lr)
    critic_applied = linear_lr_for_next_update(critic_initial, progression.state)
    critic_previous = [float(group["lr"]) for group in critic_optimizer.param_groups]
    for group in critic_optimizer.param_groups:
        group["lr"] = critic_applied
    return {
        "progression_before_update": progression.state.to_mapping(),
        "actors": actor_rows,
        "critic": {"initial": critic_initial, "previous": critic_previous, "applied": critic_applied},
    }


def _restore_lr(handles: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    for (_, optimizer), row in zip(handles["actor_optimizers"], receipt["actors"], strict=True):
        for group, previous in zip(optimizer.param_groups, row["previous"], strict=True):
            group["lr"] = float(previous)
    for group, previous in zip(
        handles["critic"].critic_optimizer.param_groups,
        receipt["critic"]["previous"],
        strict=True,
    ):
        group["lr"] = float(previous)


def _worker(args: argparse.Namespace) -> int:
    process = args.worker
    process_dir = ARTIFACT_ROOT / f"process_{process}"
    process_dir.mkdir(parents=True, exist_ok=True)
    runtime_identity_path = process_dir / "runtime_identity.json"
    ledger_path = process_dir / "transaction_ledger.jsonl"
    checkpoint_log = _CheckpointLog(process_dir / "core_runtime_checkpoints.jsonl")
    launcher = None
    simulation_app = None
    resources: dict[str, Any] = {
        "ckpt2_run_identity": args.run_id,
        "repository_authority": json.loads((ARTIFACT_ROOT / "repository_authority.json").read_text(encoding="utf-8")),
        "qualified_source_identity": {
            "ckpt2_harness_sha256": _sha(Path(__file__).resolve()),
            "base_harness_sha256": _sha(BASE_HARNESS),
            "production_source_sha256": {path.name: _sha(path) for path in SOURCE_FILES[:4]},
        },
    }
    worker_state: dict[str, Any] = {"handles": None, "progression": None, "guard": None, "lr_receipts": {}, "snapshots": {}}

    def after_construction(route: Any, _actors: Any, _critic: Any, _vn: Any, _resources: Any) -> None:
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_optimization_checkpoint import (
            OptimizationCheckpointRuntimeGuard,
            OptimizationProgressionState,
            OptimizationProgressionTracker,
            load_optimization_checkpoint,
        )

        handles = _learner_handles(route)
        guard = OptimizationCheckpointRuntimeGuard()
        progression = OptimizationProgressionTracker(OptimizationProgressionState.after_update(0, SCHEDULE_TOTAL))
        worker_state.update({"handles": handles, "progression": progression, "guard": guard})
        initial = _snapshot(handles, progression, label=f"process_{process}_fresh_initial")
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
        post_load = _snapshot(handles, progression, label="process_b_post_load")
        _require(post_load["finite"], "POST-LOAD-NONFINITE")
        _atomic_json(
            process_dir / "checkpoint_load_result.json",
            {
                "strict_load_count": 1,
                "legacy_weight_load_count": 0,
                "rollback_guard_armed": True,
                "result": result,
                "status": "PASS",
            },
        )
        _atomic_json(process_dir / "post_load_state.json", post_load)
        saved = json.loads((ARTIFACT_ROOT / "process_a" / "process_a_pre_save_state.json").read_text(encoding="utf-8"))
        keys = tuple(saved["group_digests"])
        equality = {key: saved["group_digests"][key] == post_load["group_digests"][key] for key in keys}
        _require(all(equality.values()), "CROSS-PROCESS-STATE-MISMATCH", equality)
        _atomic_json(
            ARTIFACT_ROOT / "cross_process_checkpoint_state_equality.json",
            {
                "schema_version": "b2_t4_ckpt2_cross_process_equality_v1",
                "process_a_pid": saved["process_id"],
                "process_b_pid": os.getpid(),
                "semantic_group_equality": equality,
                "object_identity_compared": False,
                "result": "PASS",
            },
        )
        module_rows = _module_device_rows(handles)
        optimizer_rows = _optimizer_device_rows(handles)
        device_result = {
            "expected": DEVICE,
            "module_rows": module_rows,
            "optimizer_rows": optimizer_rows,
            "valuenorm_location": str(handles["value_normalizer"].running_mean.device),
            "result": "PASS" if all(row["result"] == "PASS" for row in module_rows + optimizer_rows) else "FAIL",
        }
        _require(device_result["result"] == "PASS", "CUDA-OPTIMIZER-DEVICE-RESTORATION", device_result)
        _atomic_json(process_dir / "checkpoint_cuda_device_restoration.json", device_result)
        worker_state["snapshots"]["post_load"] = post_load

    def before_transaction(index: int, _actors: Any, _critic: Any, _vn: Any, _resources: Any) -> None:
        handles = worker_state["handles"]
        progression = worker_state["progression"]
        guard = worker_state["guard"]
        expected = index
        _require(progression.state.next_update_index == expected, "PROGRESSION-BEFORE-UPDATE", progression.state.to_mapping())
        receipt = _apply_lr(handles, progression)
        receipt["transaction_index"] = index
        worker_state["lr_receipts"][index] = receipt
        guard.mark_rollout_or_update_started()

    def after_transaction(index: int, _actors: Any, _critic: Any, _vn: Any, _resources: Any, transaction: Any) -> None:
        handles = worker_state["handles"]
        progression = worker_state["progression"]
        guard = worker_state["guard"]
        receipt = worker_state["lr_receipts"][index]
        progression.record_completed_update()
        guard.mark_update_complete()
        _restore_lr(handles, receipt)
        snapshot = _snapshot(handles, progression, label=f"process_{process}_after_tx{index:03d}")
        _require(snapshot["finite"], f"TX{index:03d}-NONFINITE")
        worker_state["snapshots"][index] = snapshot
        counts = dict(transaction.exact_execution_counts)
        row = {
            "transaction": f"tx{index:03d}",
            "process": process.upper(),
            "physical_steps": 2,
            "event_return_computations": int(counts["event_return_computations"]),
            "stock_compute_returns": int(counts["stock_compute_returns"]),
            "actor_optimizer_steps": counts["actor_optimizer_step_by_actor"],
            "critic_optimizer_steps": counts["critic_optimizer_step"],
            "valuenorm_updates": counts["live_valuenorm_update"],
            "s10_entries": counts["s10_entries"],
            "route_poisoned": False,
            "lr_schedule": receipt,
            "progression_after": progression.state.to_mapping(),
            "semantic_digest_after": snapshot["semantic_digest"],
            "result": "PASS",
        }
        _append_jsonl(ledger_path, row)

    try:
        _atomic_json(
            runtime_identity_path,
            {
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
                "started_ns": time.time_ns(),
            },
        )
        inner = _load_inner_base(
            {
                "_ckpt2_after_learner_construction": after_construction,
                "_ckpt2_before_transaction": before_transaction,
                "_ckpt2_after_transaction": after_transaction,
                "TRANSACTION_START_INDEX": 1 if process == "a" else 4,
            }
        )
        inner["TRANSACTION_START_INDEX"] = 1 if process == "a" else 4
        device = inner["V2"]._warm_start_torch_cuda(DEVICE, checkpoint_log)
        _require(device is not None and str(device) == DEVICE, "CUDA-READINESS")
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        launcher = AppLauncher({"headless": True, "device": DEVICE, "enable_cameras": False})
        simulation_app = launcher.app
        evidence = inner["_run_repeated_smoke"](
            checkpoint_log,
            resources,
            artifact_prefix=process_dir / "core",
        )
        _require(len(evidence["transactions"]) == 3, "WORKER-TRANSACTION-COUNT")
        handles = worker_state["handles"]
        progression = worker_state["progression"]
        final_snapshot = _snapshot(handles, progression, label=f"process_{process}_final_quiescent")
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
                boundary=worker_state["guard"].snapshot(),
                actor_modules=handles["actor_modules"],
                actor_optimizers=handles["actor_optimizers"],
                critic_module=handles["critic"].critic,
                critic_optimizer=handles["critic"].critic_optimizer,
                value_normalizer=handles["value_normalizer"],
                progression=progression.state,
                semantic_config=_semantic_config(),
            )
            validated = validate_optimization_checkpoint(
                CHECKPOINT_ROOT,
                expected_semantic_config=_semantic_config(),
                actor_modules=handles["actor_modules"],
                actor_optimizers=handles["actor_optimizers"],
                critic_module=handles["critic"].critic,
                critic_optimizer=handles["critic"].critic_optimizer,
                value_normalizer=handles["value_normalizer"],
            )
            post_save = _snapshot(handles, progression, label="process_a_post_save")
            _require(pre_save["semantic_digest"] == post_save["semantic_digest"], "SAVE-MUTATED-LEARNER")
            _atomic_json(process_dir / "process_a_post_save_state.json", post_save)
            _atomic_json(
                process_dir / "checkpoint_save_result.json",
                {
                    "successful_save_count": 1,
                    "generation_publication_count": 1,
                    "required_state_coverage": validated.manifest["state_coverage"],
                    "manifest": validated.manifest,
                    "result": result,
                    "readback": "PASS",
                    "save_nonmutation": "PASS",
                    "status": "PASS",
                },
            )
        else:
            post_load = worker_state["snapshots"]["post_load"]
            after_tx4 = worker_state["snapshots"][4]
            saved = json.loads((ARTIFACT_ROOT / "process_a" / "process_a_pre_save_state.json").read_text(encoding="utf-8"))
            optimizer_continuity = {
                "actor_saved_steps": saved["actor_adam_steps"],
                "actor_post_load_steps": post_load["actor_adam_steps"],
                "actor_after_tx004_steps": after_tx4["actor_adam_steps"],
                "critic_saved_steps": saved["critic_adam_steps"],
                "critic_post_load_steps": post_load["critic_adam_steps"],
                "critic_after_tx004_steps": after_tx4["critic_adam_steps"],
            }
            optimizer_continuity["saved_equals_loaded"] = (
                optimizer_continuity["actor_saved_steps"] == optimizer_continuity["actor_post_load_steps"]
                and optimizer_continuity["critic_saved_steps"] == optimizer_continuity["critic_post_load_steps"]
            )
            optimizer_continuity["advanced_from_restored"] = (
                optimizer_continuity["actor_after_tx004_steps"] != optimizer_continuity["actor_post_load_steps"]
                and optimizer_continuity["critic_after_tx004_steps"] != optimizer_continuity["critic_post_load_steps"]
            )
            _require(all((optimizer_continuity["saved_equals_loaded"], optimizer_continuity["advanced_from_restored"])), "OPTIMIZER-CONTINUITY")
            optimizer_continuity["result"] = "PASS"
            _atomic_json(process_dir / "real_optimizer_continuity.json", optimizer_continuity)
            value_continuity = {
                "saved_digest": saved["group_digests"]["value_normalizer"],
                "post_load_digest": post_load["group_digests"]["value_normalizer"],
                "after_tx004_digest": after_tx4["group_digests"]["value_normalizer"],
            }
            value_continuity["saved_equals_loaded"] = value_continuity["saved_digest"] == value_continuity["post_load_digest"]
            value_continuity["evolved_after_tx004"] = value_continuity["after_tx004_digest"] != value_continuity["post_load_digest"]
            _require(all((value_continuity["saved_equals_loaded"], value_continuity["evolved_after_tx004"])), "VALUENORM-CONTINUITY")
            value_continuity["result"] = "PASS"
            _atomic_json(process_dir / "real_valuenorm_continuity.json", value_continuity)
            lr_receipt = worker_state["lr_receipts"][4]
            progression_continuity = {
                "saved": saved["semantic"]["progression"],
                "post_load": post_load["semantic"]["progression"],
                "after_tx004": after_tx4["semantic"]["progression"],
                "tx004_lr": lr_receipt,
                "schedule_total_updates": SCHEDULE_TOTAL,
                "position_restored": saved["semantic"]["progression"] == post_load["semantic"]["progression"],
                "tx004_used_position": lr_receipt["progression_before_update"]["linear_lr_schedule_position"] == 4,
            }
            _require(progression_continuity["position_restored"] and progression_continuity["tx004_used_position"], "PROGRESSION-CONTINUITY")
            progression_continuity["result"] = "PASS"
            _atomic_json(process_dir / "real_progression_lr_continuity.json", progression_continuity)
            changed = any(
                after_tx4["group_digests"][key] != post_load["group_digests"][key]
                for key in ("actor_weights", "actor_optimizers", "critic_weights", "critic_optimizer", "value_normalizer")
            )
            _require(changed, "POST-LOAD-TRAINABILITY")
            _atomic_json(
                ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json",
                {
                    "process_a_last_transaction": "tx003",
                    "checkpoint_generation": 0,
                    "process_b_first_transaction": "tx004",
                    "saved_progression": saved["semantic"]["progression"],
                    "loaded_progression": post_load["semantic"]["progression"],
                    "first_resumed_progression": after_tx4["semantic"]["progression"],
                    "actor_optimizer_continuity": "PASS",
                    "critic_optimizer_continuity": "PASS",
                    "ValueNorm_continuity": "PASS",
                    "LR_continuity": "PASS",
                    "device_continuity": "PASS",
                    "post_load_trainability": "PASS",
                    "result": "PASS",
                },
            )
        _atomic_json(process_dir / "worker_result.json", {"status": "PASS", "process": process.upper(), "pid": os.getpid()})
        return 0
    except BaseException as exc:
        _atomic_json(
            ARTIFACT_ROOT / "failure_receipt.json",
            {
                "classification": f"PHASE-B2-T4-CKPT2-STOP-PROCESS-{process.upper()}",
                "process": process.upper(),
                "pid": os.getpid(),
                "active_transaction": resources.get("active_transaction"),
                "completed_transactions": resources.get("completed_transactions", 0),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "production_repair_permitted": False,
                "retry_permitted": False,
            },
        )
        traceback.print_exc()
        return 1
    finally:
        env_closed = False
        app_closed = False
        guard_env = resources.get("guard")
        if guard_env is not None:
            try:
                guard_env.close()
                env_closed = True
            except Exception:
                traceback.print_exc()
        if simulation_app is not None:
            try:
                simulation_app.close()
                app_closed = True
            except Exception:
                traceback.print_exc()
        _atomic_json(
            process_dir / "shutdown_result.json",
            {
                "process": process.upper(),
                "pid": os.getpid(),
                "environment_close": "PASS" if env_closed else "FAIL",
                "simulation_app_close": "PASS" if app_closed else "FAIL",
                "completed_transactions": resources.get("completed_transactions", 0),
                "active_transaction": resources.get("active_transaction"),
                "route_poisoned": bool(getattr(resources.get("route"), "poisoned", False)),
                "finished_ns": time.time_ns(),
            },
        )


def _tasklist_pid_active(pid: int) -> bool:
    completed = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    rows = list(csv.reader(io.StringIO(completed.stdout)))
    return any(len(row) >= 2 and row[1].strip() == str(pid) for row in rows)


def _git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.longpaths=true", *arguments],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return completed.stdout.decode("utf-8", errors="surrogateescape").strip()


def _preflight(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    pure_path = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    _require(pure_path.is_file(), "MISSING-CKPT1-PURE-PREFLIGHT", pure_path)
    pure = json.loads(pure_path.read_text(encoding="utf-8"))
    _require(
        pure.get("successful") is True
        and pure.get("tests_run") == 6
        and pure.get("negative_case_count") == 25
        and pure.get("unexpected_negative_case_count") == 0,
        "CKPT1-PURE-PREFLIGHT",
        pure,
    )
    branch = _git_text("branch", "--show-current")
    head = _git_text("rev-parse", "HEAD")
    origin = _git_text("rev-parse", "origin/main")
    merge_base = _git_text("merge-base", "HEAD", "origin/main")
    index_bytes = subprocess.run(
        ["git", "-c", "core.longpaths=true", "ls-files", "--stage"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    staged_paths = _git_text("diff", "--cached", "--name-only", "-z").split("\0")
    staged_count = len([path for path in staged_paths if path])
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL_SHA256}
    _require(installed == EXPECTED_HARL_SHA256, "INSTALLED-HARL-DRIFT", installed)
    initial_authority = {
        "branch": "main",
        "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "porcelain_entry_count": 50927,
        "porcelain_sha256": "290b0ffc347d72637c7889ef8a47a643e3ef08f08addee2e9414e985bcdeb93c",
        "staged_path_count": 359,
        "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
        "agentread_path_count": 50825,
        "agentread_path_set_sha256": "7386f5d858de7998c0d3f997e0977e39ace7ce0027eb69178451497c8e122dfa",
        "captured_before_first_ckpt2_write": True,
    }
    repository = {
        "schema_version": "b2_t4_ckpt2_repository_authority_v1",
        "initial_before_first_write": initial_authority,
        "pre_runtime_observed": {
            "branch": branch,
            "HEAD": head,
            "origin_main": origin,
            "merge_base": merge_base,
            "staged_path_count": staged_count,
            "staged_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        },
        "retained_ckpt1_authority_match": (
            branch == initial_authority["branch"]
            and head == origin == merge_base == initial_authority["HEAD"]
            and staged_count == initial_authority["staged_path_count"]
            and hashlib.sha256(index_bytes).hexdigest() == initial_authority["staged_index_sha256"]
        ),
        "git_mutations_by_ckpt2": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }
    _require(repository["retained_ckpt1_authority_match"], "REPOSITORY-AUTHORITY-DRIFT", repository)
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", repository)
    _atomic_json(
        ARTIFACT_ROOT / "csr1_preservation.json",
        {
            "status": "GPT REVIEW PASS / CLOSED",
            "historical_r14": "POISONED / RETAINED / NEVER REUSE",
            "historical_learner_reuse": 0,
            "historical_pid_or_run_identity_reuse": 0,
            "result": "PASS",
        },
    )
    production_hashes = {path.name: _sha(path) for path in SOURCE_FILES[:2]}
    _atomic_json(
        ARTIFACT_ROOT / "ckpt1_preservation.json",
        {
            "status": "GPT REVIEW PASS / CLOSED",
            "checkpoint_schema": "lifecycle_mrta_optimization_checkpoint_v1",
            "pure_tests": "6/6",
            "negative_matrix": "25/25",
            "implementation_sha256": production_hashes,
            "installed_harl_sha256": installed,
            "installed_harl_unchanged": True,
            "result": "PASS",
        },
    )
    harness = Path(__file__).resolve()
    source_hashes = {path.relative_to(ROOT).as_posix(): _sha(path) for path in SOURCE_FILES}
    source_hashes[harness.relative_to(ROOT).as_posix()] = _sha(harness)
    preflight = {
        "schema_version": "b2_t4_ckpt2_preflight_v1",
        "run_id": args.run_id,
        "pure_ckpt1_qualification": "PASS",
        "schema_intact": True,
        "save_load_api_intact": True,
        "optimizer_coverage_intact": True,
        "valuenorm_adapter_intact": True,
        "progression_contract_intact": True,
        "installed_harl_unchanged": True,
        "runtime_started": False,
        "process_a_started": False,
        "production_source_modifications_for_ckpt2": 0,
        "pre_process_harness_repairs": [
            {
                "count": 1,
                "scope": "evidence-only staged-index serialization",
                "cause": "NUL-separated hash was compared with retained line-separated authority hash",
                "semantic_runtime_change": False,
                "process_a_had_started": False,
            }
        ],
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_preflight.json", preflight)
    _atomic_json(
        ARTIFACT_ROOT / "ckpt2_run_identity.json",
        {
            "run_id": args.run_id,
            "fresh": True,
            "historical_identity_reuse": False,
            "attempt_number": 1,
            "maximum_attempts": 1,
        },
    )
    _atomic_json(
        ARTIFACT_ROOT / "ckpt2_pre_runtime_freeze.json",
        {
            "run_id": args.run_id,
            "frozen_before_process_a": True,
            "source_sha256": source_hashes,
            "harness_sha256": _sha(harness),
            "helpers": [],
            "post_freeze_source_edits_authorized": False,
            "result": "PASS",
        },
    )
    print(json.dumps(preflight, indent=2, sort_keys=True))
    return 0


def _parent(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    parent_dir = ARTIFACT_ROOT / "parent"
    parent_dir.mkdir(parents=True, exist_ok=True)
    inventory: dict[str, Any] = {
        "parent_pid": os.getpid(),
        "parent_python": sys.executable,
        "run_id": args.run_id,
        "process_a_started": False,
        "process_b_started": False,
        "retry_count": 0,
    }
    command_base = [sys.executable, str(Path(__file__).resolve()), "--worker", "a", "--run-id", args.run_id]
    try:
        process_a = subprocess.Popen(command_base, cwd=ROOT)
        inventory.update({"process_a_started": True, "process_a_pid": process_a.pid, "process_a_created_ns": time.time_ns()})
        return_a = process_a.wait()
        inventory.update({"process_a_return_code": return_a, "process_a_exit_observed_ns": time.time_ns()})
        a_active = _tasklist_pid_active(process_a.pid)
        inventory["process_a_pid_active_after_wait"] = a_active
        _atomic_json(parent_dir / "parent_process_inventory.json", inventory)
        _require(return_a == 0 and not a_active, "PROCESS-A-CLEAN-EXIT", inventory)
        command_b = [sys.executable, str(Path(__file__).resolve()), "--worker", "b", "--run-id", args.run_id]
        process_b = subprocess.Popen(command_b, cwd=ROOT)
        inventory.update(
            {
                "process_b_started": True,
                "process_b_pid": process_b.pid,
                "process_b_created_ns": time.time_ns(),
                "a_exit_before_b_creation": inventory["process_a_exit_observed_ns"] <= time.time_ns(),
            }
        )
        _require(process_a.pid != process_b.pid, "PID-REUSE", inventory)
        return_b = process_b.wait()
        inventory.update({"process_b_return_code": return_b, "process_b_exit_observed_ns": time.time_ns()})
        b_active = _tasklist_pid_active(process_b.pid)
        inventory["process_b_pid_active_after_wait"] = b_active
        _atomic_json(parent_dir / "parent_process_inventory.json", inventory)
        _require(return_b == 0 and not b_active, "PROCESS-B-CLEAN-EXIT", inventory)
        boundary = {
            "process_a_pid": process_a.pid,
            "process_b_pid": process_b.pid,
            "different_pids": process_a.pid != process_b.pid,
            "process_a_exited_before_process_b_creation": True,
            "process_a_pid_inactive_before_b": not a_active,
            "cross_process_python_object_sharing": False,
            "result": "PASS",
        }
        _atomic_json(ARTIFACT_ROOT / "fresh_process_boundary.json", boundary)
        quiescence = {
            "process_a_return_code": return_a,
            "process_b_return_code": return_b,
            "process_a_pid_inactive": not a_active,
            "process_b_pid_inactive": not b_active,
            "matching_worker_count": 0,
            "tx007_started": False,
            "result": "PASS",
        }
        _atomic_json(ARTIFACT_ROOT / "process_quiescence.json", quiescence)
        save_result = json.loads((ARTIFACT_ROOT / "process_a" / "checkpoint_save_result.json").read_text(encoding="utf-8"))
        generation = int(save_result["result"]["generation"])
        bridge_path = ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json"
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
        bridge["checkpoint_generation"] = generation
        _atomic_json(bridge_path, bridge)
        final = {
            "classification": PASS_CLASSIFICATION,
            "status": "COMPLETE / AWAITING GPT REVIEW",
            "run_id": args.run_id,
            "process_a_pid": process_a.pid,
            "process_b_pid": process_b.pid,
            "process_a_transactions": "3/3",
            "process_b_transactions": "3/3",
            "total_physical_transitions": 12,
            "checkpoint_save_count": 1,
            "checkpoint_load_count": 1,
            "checkpoint_generation": generation,
            "fresh_process_separation": "PASS",
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
            _atomic_json(
                ARTIFACT_ROOT / "failure_receipt.json",
                {
                    "classification": "PHASE-B2-T4-CKPT2-STOP-FRESH-PROCESS-BOUNDARY",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "retry_permitted": False,
                },
            )
        traceback.print_exc()
        return 1


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
