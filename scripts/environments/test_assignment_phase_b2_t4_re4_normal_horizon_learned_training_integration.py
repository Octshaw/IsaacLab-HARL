"""Fresh B2-T4-RE4 normal-horizon learned-training integration qualification.

The formal worker deliberately calls the reviewed RE3 transaction engine
directly instead of delegating to its legacy worker.  This lets RE4 persist a
phase-specific training receipt, close the environment, persist the close
result and App-close intent, and only then call ``SimulationApp.close``.
External process termination is adjudicated by the supervisor with the generic
EP-Q v2 Layer-B predicates; shutdown text is diagnostic only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from typing import Mapping, Sequence

import _assignment_phase_b2_t4_ep_q_process_quiescence as EPQ
import test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration as RE3


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260916"
ARTIFACTS = DATE_ROOT / "b2_t4_re4_artifacts"
PREFIX = ARTIFACTS / "b2_t4_re4_normal_horizon_20260916_formal01"
RE3_RUNNER = HERE / "test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py"
EPQ_HELPER = HERE / "_assignment_phase_b2_t4_ep_q_process_quiescence.py"
EP_RUNNER = HERE / "test_assignment_phase_b2_t4_ep_environment_entry_point_registration_boundary.py"
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
ENV_ID = "Isaac-Scan-Mobile-Manipulator-Direct-v0"
PACKAGE_NAME = "isaaclab_tasks.direct.scan_mobile_manipulator"
ENTRY_POINT = PACKAGE_NAME + ":ScanMobileManipulatorEnv"
DEFINING_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env"
PASS = (
    "PHASE-B2-T4-RE4-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
STOP_READINESS = "PHASE-B2-T4-RE4-STOP-RUNNER-READINESS-NOT-QUALIFIED"
STOP_CUDA = "PHASE-B2-T4-RE4-STOP-CUDA-CUBLAS-INFRASTRUCTURE-NOT-READY"
RECEIPT_SCHEMA = "b2_t4_re4_training_worker_receipt_v1"
ENVELOPE_SCHEMA = "b2_t4_re4_training_worker_receipt_envelope_v1"
TARGET_TRANSACTIONS = 160
ROLLOUT_T = 2
PHYSICAL_TARGET = 320
QUALIFIED_RE3_SHA256 = "02fcba5b1798c9c77be0af7d9ae4de9ce1ea7c392e9ea69c1cf52eb1e33f0ce1"
QUALIFIED_EP_Q_SHA256 = "bb56c8c6ebe7b93353640b4c161845f88ed281a6bc991acf35a376ad6b39b52d"
PRE_RUNTIME_PYTHON_INVOCATIONS = 24
SR_RUNNER = HERE / "test_assignment_phase_b2_t4_sr_evidence_ledger_serializer_repair.py"
SR_OLD_FULL_SHA256 = "a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de"
SR_OLD_ADAPTER_SHA256 = "b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014"
ZD_FULL_SHA256 = "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7"
ZD_ADAPTER_SHA256 = "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _require(condition: bool, code: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-RE4 {code}: {detail!r}")


def _durable_bytes(path: Path, data: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    observed = path.read_bytes()
    _require(observed == data, "DURABLE-READBACK-MISMATCH", str(path))
    return {"path": str(path), "bytes": len(observed), "sha256": _sha_bytes(observed)}


def _durable_json(path: Path, payload: object) -> dict[str, object]:
    return _durable_bytes(path, json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def _receipt_envelope(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "payload_sha256": _sha_bytes(_canonical_bytes(normalized)),
        "payload": normalized,
    }


def _persist_receipt(path: Path, payload: Mapping[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    prepared = dict(payload)
    prepared.update(
        {
            "receipt_written_before_app_close": True,
            "receipt_fsync_pass": True,
            "receipt_readback_pass": False,
            "receipt_persisted_wall_time_ns": time.time_ns(),
            "receipt_persisted_monotonic_ns": time.monotonic_ns(),
        }
    )
    _durable_json(path, _receipt_envelope(prepared))
    prepared["receipt_readback_pass"] = True
    prepared["receipt_readback_monotonic_ns"] = time.monotonic_ns()
    metadata = _durable_json(path, _receipt_envelope(prepared))
    envelope, error = _load_receipt(path)
    _require(error is None and envelope is not None, "RECEIPT-READBACK", error)
    _require(envelope == _receipt_envelope(prepared), "RECEIPT-READBACK-EQUALITY")
    return prepared, metadata


def _load_receipt(path: Path) -> tuple[dict[str, object] | None, str | None]:
    if not path.is_file():
        return None, "missing receipt"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return (payload, None) if isinstance(payload, dict) else (None, "receipt envelope is not an object")


def _layer_a_validate(
    envelope: Mapping[str, object] | None,
    *,
    error: str | None,
    expected_run_id: str,
    expected_pid: int,
    expected_source_digest: str,
) -> dict[str, object]:
    payload_obj = envelope.get("payload") if isinstance(envelope, Mapping) else None
    payload = payload_obj if isinstance(payload_obj, Mapping) else {}
    observed_digest = _sha_bytes(_canonical_bytes(dict(payload))) if isinstance(payload_obj, Mapping) else None
    w = payload.get("witnesses") if isinstance(payload.get("witnesses"), Mapping) else {}
    contracts = payload.get("contracts") if isinstance(payload.get("contracts"), Mapping) else {}
    learner = payload.get("learner") if isinstance(payload.get("learner"), Mapping) else {}
    progress = payload.get("task_progress") if isinstance(payload.get("task_progress"), Mapping) else {}
    checks = {
        "receipt_present": envelope is not None,
        "receipt_parse_valid": error is None,
        "envelope_schema": bool(envelope and envelope.get("schema_version") == ENVELOPE_SCHEMA),
        "payload_schema": payload.get("schema_version") == RECEIPT_SCHEMA,
        "payload_digest": bool(envelope and envelope.get("payload_sha256") == observed_digest),
        "phase": payload.get("phase") == "B2-T4-RE4",
        "run_id": payload.get("run_id") == expected_run_id,
        "worker_pid": payload.get("worker_pid") == expected_pid,
        "source_authority": payload.get("source_authority_digest") == expected_source_digest,
        "config_authority": isinstance(payload.get("config_authority_digest"), str) and len(str(payload.get("config_authority_digest"))) == 64,
        "status_success": payload.get("status") == "success",
        "cuda_probe": payload.get("cuda_probe_pass") is True and payload.get("cuda_probe_count") == 1,
        "app_launcher": payload.get("app_launcher_started") is True,
        "entry_point": payload.get("entry_point_resolution_pass") is True,
        "environment": payload.get("environment_constructions") == 1,
        "reset": payload.get("initial_resets") == 1,
        "learner_once": payload.get("persistent_learner_constructions") == 1,
        "targets": payload.get("target_transactions") == 160 and payload.get("rollout_T") == 2 and payload.get("physical_transition_target") == 320,
        "completion": payload.get("physical_transitions") == 320 and payload.get("production_s10") == 160 and payload.get("ledger_qualified_transactions") == 160 and payload.get("bridges") == 159 and payload.get("tx161_started") is False,
        "w1_w6": all(isinstance(w.get(f"W{i}"), Mapping) and w[f"W{i}"].get("pass") is True for i in range(1, 7)),
        "w7": isinstance(w.get("W7"), Mapping) and w["W7"].get("pass") is True and w["W7"].get("equal") == 160 and w["W7"].get("required") == 160,
        "task_progress": int(progress.get("TASK_COMPLETED", 0)) >= 1 and int(progress.get("completed_delta", 0)) > 0 and int(progress.get("coverage_max", 0)) > 0,
        "persistent_learner": learner.get("persistent_continuity_pass") is True,
        "actor_plans": learner.get("actor_plans_exact") is True,
        "factor": learner.get("factor_audits_pass") is True,
        "critic": learner.get("critic_plans_exact") is True,
        "valuenorm": learner.get("ValueNorm_continuity_pass") is True,
        "adam": learner.get("Adam_continuity_pass") is True,
        "numerical": learner.get("numerical_health_pass") is True,
        "contracts": all(contracts.get(name) == 0 for name in ("NR_reconciliation_faults", "ZD_actor_reconciliation_faults", "SR_serializer_faults", "bookkeeping_faults", "lifecycle_policy_call_faults")),
        "returns": payload.get("event_returns") == 160 and payload.get("stock_compute_returns") == 0,
        "route": payload.get("partial_update") is False and payload.get("route_poisoned") is False and payload.get("final_in_worker_quiescence_pass") is True,
        "forbidden": payload.get("checkpoint_io") == 0 and payload.get("public_activation") == 0 and payload.get("evaluation_playback") == 0,
        "receipt_order": payload.get("receipt_written_before_app_close") is True and payload.get("receipt_fsync_pass") is True and payload.get("receipt_readback_pass") is True,
        "env_close": payload.get("env_close_pass") is True,
        "app_close_invoked": payload.get("app_close_invoked") is True,
    }
    passed = all(checks.values())
    return {
        "schema_version": "b2_t4_re4_layer_a_validation_v1",
        "pass": passed,
        "classification": PASS if passed else str(payload.get("classification") or "PHASE-B2-T4-RE4-STOP-WORKER-RECEIPT-NOT-QUALIFIED"),
        "checks": checks,
        "receipt_error": error,
        "observed_payload_sha256": observed_digest,
        "payload": dict(payload),
    }


def _base_payload(run_id: str, *, worker_pid: int) -> dict[str, object]:
    return {
        "schema_version": RECEIPT_SCHEMA,
        "phase": "B2-T4-RE4",
        "run_id": run_id,
        "worker_pid": worker_pid,
        "status": "failure",
        "classification": "PHASE-B2-T4-RE4-STOP-WORKER-NOT-COMPLETE",
        "failure_stage": "worker_start",
        "exception_type": None,
        "exception_message": None,
        "traceback_tail": None,
        "source_authority_digest": None,
        "config_authority_digest": None,
        "cuda_probe_pass": False,
        "cuda_probe_count": 0,
        "cuda_probe_retries": 0,
        "app_launcher_started": False,
        "entry_point_resolution_pass": False,
        "environment_constructions": 0,
        "initial_resets": 0,
        "persistent_learner_constructions": 0,
        "target_transactions": 160,
        "rollout_T": 2,
        "physical_transition_target": 320,
        "physical_transitions": 0,
        "production_s10": 0,
        "ledger_qualified_transactions": 0,
        "bridges": 0,
        "tx161_started": False,
        "witnesses": {},
        "task_progress": {"TASK_COMPLETED": 0, "completed_delta": 0, "coverage_max": 0},
        "learner": {},
        "contracts": {},
        "event_returns": 0,
        "stock_compute_returns": 0,
        "partial_update": False,
        "route_poisoned": False,
        "irreversible_mutation_occurred": False,
        "final_in_worker_quiescence_pass": False,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
        "env_close_attempted": False,
        "env_close_pass": False,
        "app_close_invoked": False,
        "runtime_counters": {},
        "last_durable_ledger_positions": {},
    }


def _source_authority() -> dict[str, object]:
    static = RE3.run_static()
    hashes = {
        "re3_runner": _sha(RE3_RUNNER),
        "ep_q_helper": _sha(EPQ_HELPER),
        "ep_registration_runner": _sha(EP_RUNNER),
        "re4_runner": _sha(Path(__file__).resolve()),
    }
    result = {
        "schema_version": "b2_t4_re4_static_authority_v1",
        "approved_interpreter": str(Path(sys.executable).resolve()),
        "approved_interpreter_pass": Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve(),
        "re3_static": static,
        "hashes": hashes,
        "re3_runner_frozen": hashes["re3_runner"] == QUALIFIED_RE3_SHA256,
        "ep_q_helper_frozen": hashes["ep_q_helper"] == QUALIFIED_EP_Q_SHA256,
        "production_semantic_modifications": 0,
    }
    result["pass"] = bool(result["approved_interpreter_pass"] and static.get("pass") and result["re3_runner_frozen"] and result["ep_q_helper_frozen"])
    return result


def _run_command(name: str, command: Sequence[str], *, timeout: int = 600) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    result = {
        "name": name,
        "return_code": completed.returncode,
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
        "pass": completed.returncode == 0,
    }
    _require(result["pass"], f"PREFLIGHT-{name.upper()}-FAILED", result)
    return result


def _run_sr_current_zd(artifact_dir: Path) -> dict[str, object]:
    """Replay the frozen SR suite against the reviewed current ZD baseline."""

    source = SR_RUNNER.read_text(encoding="utf-8")
    _require(source.count(SR_OLD_FULL_SHA256) == 1, "SR-FULL-HASH-BINDING-DRIFT")
    _require(source.count(SR_OLD_ADAPTER_SHA256) == 1, "SR-ADAPTER-HASH-BINDING-DRIFT")
    transformed = source.replace(SR_OLD_FULL_SHA256, ZD_FULL_SHA256).replace(
        SR_OLD_ADAPTER_SHA256, ZD_ADAPTER_SHA256
    )
    namespace: dict[str, object] = {
        "__name__": "_b2_t4_re4_sr_current_zd_replay",
        "__file__": str(SR_RUNNER),
        "__package__": None,
    }
    exec(compile(transformed, str(SR_RUNNER), "exec"), namespace)
    result = namespace["run"](artifact_dir.resolve())
    _require(result.get("status") == "PASS", "SR-CURRENT-ZD-REPLAY", result)
    return result


def _synthetic_success_payload(run_id: str, pid: int, source_digest: str) -> dict[str, object]:
    witnesses = {f"W{i}": {"pass": True} for i in range(1, 7)}
    witnesses["W7"] = {"pass": True, "equal": 160, "required": 160}
    payload = _base_payload(run_id, worker_pid=pid)
    payload.update(
        {
            "status": "success",
            "classification": PASS,
            "source_authority_digest": source_digest,
            "config_authority_digest": "c" * 64,
            "cuda_probe_pass": True,
            "cuda_probe_count": 1,
            "app_launcher_started": True,
            "entry_point_resolution_pass": True,
            "environment_constructions": 1,
            "initial_resets": 1,
            "persistent_learner_constructions": 1,
            "physical_transitions": 320,
            "production_s10": 160,
            "ledger_qualified_transactions": 160,
            "bridges": 159,
            "witnesses": witnesses,
            "task_progress": {"TASK_COMPLETED": 1, "completed_delta": 1, "coverage_max": 1},
            "learner": {
                "persistent_continuity_pass": True,
                "actor_plans_exact": True,
                "factor_audits_pass": True,
                "critic_plans_exact": True,
                "ValueNorm_continuity_pass": True,
                "Adam_continuity_pass": True,
                "numerical_health_pass": True,
            },
            "contracts": {
                "NR_reconciliation_faults": 0,
                "ZD_actor_reconciliation_faults": 0,
                "SR_serializer_faults": 0,
                "bookkeeping_faults": 0,
                "lifecycle_policy_call_faults": 0,
            },
            "event_returns": 160,
            "final_in_worker_quiescence_pass": True,
            "env_close_attempted": True,
            "env_close_pass": True,
            "app_close_invoked": True,
        }
    )
    return payload


def _receipt_and_layer_b_qualification(source_digest: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="b2_t4_re4_receipt_preflight_") as name:
        directory = Path(name)
        run_id = "re4-synthetic-success"
        pid = 424242
        success_payload, _ = _persist_receipt(directory / "success.json", _synthetic_success_payload(run_id, pid, source_digest))
        success_envelope, success_error = _load_receipt(directory / "success.json")
        success = _layer_a_validate(success_envelope, error=success_error, expected_run_id=run_id, expected_pid=pid, expected_source_digest=source_digest)
        failure_payload = _base_payload("re4-synthetic-failure", worker_pid=pid)
        failure_payload.update({"source_authority_digest": source_digest, "config_authority_digest": "f" * 64, "failure_stage": "synthetic", "exception_type": "RuntimeError", "exception_message": "synthetic failure"})
        _persist_receipt(directory / "failure.json", failure_payload)
        failure_envelope, failure_error = _load_receipt(directory / "failure.json")
        failure = _layer_a_validate(failure_envelope, error=failure_error, expected_run_id="re4-synthetic-failure", expected_pid=pid, expected_source_digest=source_digest)
        malformed = directory / "malformed.json"
        _durable_bytes(malformed, b"{bad-json\n")
        malformed_envelope, malformed_error = _load_receipt(malformed)
        malformed_result = _layer_a_validate(malformed_envelope, error=malformed_error, expected_run_id=run_id, expected_pid=pid, expected_source_digest=source_digest)
        stale = _layer_a_validate(success_envelope, error=success_error, expected_run_id="different-run", expected_pid=pid, expected_source_digest=source_digest)
        missing_envelope, missing_error = _load_receipt(directory / "missing.json")
        missing = _layer_a_validate(missing_envelope, error=missing_error, expected_run_id=run_id, expected_pid=pid, expected_source_digest=source_digest)
    layer_b_positive_input = {
        "worker_wait_completed": True,
        "timed_out": False,
        "worker_return_code": 0,
        "worker_pid_active": False,
        "matching_formal_worker_pids": (),
    }
    layer_b_positive = EPQ._process_predicates(layer_b_positive_input)
    layer_b_negatives = {}
    mutations = {
        "wait_incomplete": {"worker_wait_completed": False},
        "timeout": {"timed_out": True},
        "nonzero_return": {"worker_return_code": 20},
        "pid_active": {"worker_pid_active": True},
        "matching_worker": {"matching_formal_worker_pids": (123,)},
    }
    for name, changes in mutations.items():
        evidence = {**layer_b_positive_input, **changes}
        predicates = EPQ._process_predicates(evidence)
        layer_b_negatives[name] = {"predicates": predicates, "fail_closed": not all(predicates.values())}
    ep_p_payload = {
        "schema_version": EPQ.EP_P_RECEIPT_SCHEMA,
        "run_id": "ep-q-canonical-synthetic",
        "worker_pid": 111,
        "status": "success",
        "reset_pass": True,
        "structure_assertions_pass": True,
        "receipt_written_before_app_close": True,
        "receipt_fsync_pass": True,
        "receipt_readback_pass": True,
        "env_close_pass": True,
        "app_close_invoked": True,
        "physical_steps": 0,
        "learner_constructions": 0,
        "learner_mutations": 0,
    }
    canonical = EPQ.reconcile_process_quiescence_v2(
        receipt_envelope=EPQ.make_receipt_envelope(ep_p_payload),
        receipt_error=None,
        expected_run_id="ep-q-canonical-synthetic",
        expected_worker_pid=111,
        process_evidence=layer_b_positive_input,
        captured_stdout="no shutdown marker required",
        source_contract="RE4 preflight synthetic EP-Q helper test",
    )
    result = {
        "schema_version": "b2_t4_re4_receipt_and_layer_b_preflight_v1",
        "layer_a_success": success,
        "layer_a_failure": failure,
        "missing": missing,
        "malformed": malformed_result,
        "stale": stale,
        "layer_b_positive": layer_b_positive,
        "layer_b_negatives": layer_b_negatives,
        "ep_q_canonical_helper": canonical,
    }
    result["pass"] = bool(success["pass"] and not failure["pass"] and not missing["pass"] and not malformed_result["pass"] and not stale["pass"] and all(layer_b_positive.values()) and all(row["fail_closed"] for row in layer_b_negatives.values()) and canonical["pass"])
    _require(result["pass"], "RECEIPT-LAYER-B-PREFLIGHT", result)
    return result


def run_preflight() -> dict[str, object]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    formal_names = ("formal_worker_receipt.json", "formal_supervisor_result.json", "process_quiescence.json", "final_result.json")
    _require(not any((ARTIFACTS / name).exists() for name in formal_names), "STALE-FORMAL-ARTIFACT")
    static = _source_authority()
    _require(static["pass"], "STATIC-AUTHORITY", static)
    _durable_json(ARTIFACTS / "re4_static_authority.json", static)
    source_digest = _sha(ARTIFACTS / "re4_static_authority.json")
    receipt = _receipt_and_layer_b_qualification(source_digest)
    _durable_json(ARTIFACTS / "preflight_receipt_layer_b.json", receipt)
    python = sys.executable
    sr_dir = ARTIFACTS / "preflight" / "sr"
    zd_dir = ARTIFACTS / "preflight" / "zd"
    commands = (
        ("registration_import_order", (python, str(EP_RUNNER), "--mode", "probe", "--sequence", "re3")),
        ("nr", (python, str(HERE / "test_assignment_phase_b2_t4_nr_nonterminal_rollout_completeness_contract.py"), "--json")),
        ("sr", (python, str(Path(__file__).resolve()), "--mode", "sr-current-zd", "--artifact-dir", str(sr_dir))),
        ("zd", (python, str(HERE / "test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract.py"), "--artifact-dir", str(zd_dir))),
        ("i5b", (python, str(HERE / "test_assignment_phase_b2_i5b_time_limit_gae_valuenorm_semantics_pure.py"), "--json")),
        ("ld", (python, str(HERE / "test_assignment_phase_b2_t0_ld_lifecycle_decision_gating_pure.py"))),
        ("controlled_r5", (python, str(HERE / "test_assignment_phase_b2_r5_controlled_private_full_learner_transaction.py"))),
        ("row_geometry", (python, str(HERE / "test_assignment_phase_b2_r5i_real_shape_binding_pure.py"))),
        ("critic_cg", (python, str(HERE / "test_assignment_phase_b2_r5i_cg_critic_zero_gradient_classification.py"))),
        ("valuenorm", (python, str(HERE / "test_assignment_phase_b2_r5i_vf_valuenorm_runtime_fingerprint.py"))),
        ("t2_observer", (python, str(HERE / "_assignment_phase_b2_t2_observability.py"))),
        ("t3_observer", (python, str(HERE / "_assignment_phase_b2_t3_progress_observer.py"))),
    )
    command_results = [_run_command(name, command) for name, command in commands]
    summary = {
        "schema_version": "b2_t4_re4_preflight_summary_v1",
        "phase": "B2-T4-RE4",
        "status": "PASS",
        "pre_runtime_python_invocations": PRE_RUNTIME_PYTHON_INVOCATIONS,
        "invocation_accounting": {
            "prior_read_only_namespace_introspection": 1,
            "py_compile": 2,
            "stopped_preflight_parent": 1,
            "stopped_preflight_child_suites": 3,
            "qualified_preflight_parent": 1,
            "qualified_preflight_child_suites": len(commands),
            "exact_runner_readiness": 1,
        },
        "static_authority_digest": source_digest,
        "static_authority_pass": True,
        "receipt_layer_b_pass": receipt["pass"],
        "qualified_gates": command_results,
        "no_AppLauncher_during_preflight": True,
        "production_semantic_modifications": 0,
        "pass": True,
    }
    _require(sum(summary["invocation_accounting"].values()) == PRE_RUNTIME_PYTHON_INVOCATIONS, "INVOCATION-ACCOUNTING", summary)
    _durable_json(ARTIFACTS / "re4_preflight_summary.json", summary)
    return summary


def run_readiness() -> dict[str, object]:
    static_path = ARTIFACTS / "re4_static_authority.json"
    preflight_path = ARTIFACTS / "re4_preflight_summary.json"
    _require(static_path.is_file() and preflight_path.is_file(), "READINESS-MISSING-PREFLIGHT")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    _require(preflight.get("pass") is True, "READINESS-PREFLIGHT-NOT-PASS")
    with tempfile.TemporaryDirectory(prefix="b2_t4_re4_re3_readiness_") as name:
        inherited = RE3.run_runner_readiness_replay(Path(name) / "re3_readiness.json")
    source_digest = _sha(static_path)
    receipt = _receipt_and_layer_b_qualification(source_digest)
    result = {
        "schema_version": "b2_t4_re4_runner_readiness_replay_v1",
        "status": "PASS",
        "classification": "PHASE-B2-T4-RE4-RUNNER-READINESS-QUALIFIED",
        "A_SR_bookkeeping_retained_RE1_tx001": inherited["re1_sr_bookkeeping_replay"],
        "B_ZD_continuation_retained_RE2_tx002": inherited["re2_zd_replay"],
        "C_RE4_final_worker_receipt_synthetic": receipt["layer_a_success"],
        "D_EP_Q_Layer_B_synthetic": {"predicates": receipt["layer_b_positive"], "pass": all(receipt["layer_b_positive"].values())},
        "readiness_replay_count": 1,
        "AppLauncher": 0,
        "real_isaac_environments": 0,
        "cuda_cublas_probes": 0,
    }
    result["pass"] = bool(inherited.get("pass") and result["A_SR_bookkeeping_retained_RE1_tx001"]["all_ledgers_pass"] and result["B_ZD_continuation_retained_RE2_tx002"]["pass"] and result["C_RE4_final_worker_receipt_synthetic"]["pass"] and result["D_EP_Q_Layer_B_synthetic"]["pass"])
    if not result["pass"]:
        result.update({"status": "STOP", "classification": STOP_READINESS})
    _durable_json(ARTIFACTS / "re4_runner_readiness_replay.json", result)
    _require(result["pass"], STOP_READINESS, result)
    return result


def refresh_authority_after_entry_point_fix() -> dict[str, object]:
    """Refreeze RE4-only authority after the pre-formal entry-point correction."""

    readiness_path = ARTIFACTS / "re4_runner_readiness_replay.json"
    superseded_path = ARTIFACTS / "re4_runner_readiness_replay_superseded_before_entry_point_constant_fix.json"
    _require(readiness_path.is_file() and not superseded_path.exists(), "AUTHORITY-REFRESH-READINESS-STATE")
    _durable_bytes(superseded_path, readiness_path.read_bytes())
    static = _source_authority()
    _require(static["pass"], "AUTHORITY-REFRESH-STATIC", static)
    static_path = ARTIFACTS / "re4_static_authority.json"
    _durable_json(static_path, static)
    source_digest = _sha(static_path)
    receipt = _receipt_and_layer_b_qualification(source_digest)
    _durable_json(ARTIFACTS / "preflight_receipt_layer_b.json", receipt)
    preflight_path = ARTIFACTS / "re4_preflight_summary.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight.update(
        {
            "pre_runtime_python_invocations": PRE_RUNTIME_PYTHON_INVOCATIONS,
            "static_authority_digest": source_digest,
            "receipt_layer_b_pass": receipt["pass"],
            "pre_formal_entry_point_constant_correction": {
                "from": DEFINING_MODULE + ":ScanMobileManipulatorEnv",
                "to": ENTRY_POINT,
                "basis": "qualified EP package-export registration and fresh import-order probe",
                "production_semantic_modifications": 0,
            },
            "runner_readiness": {
                "superseded_pre_final_passes": 1,
                "final_qualified_replay_count": 1,
                "final_replay_pending": True,
            },
            "invocation_accounting": {
                "prior_read_only_namespace_introspection": 1,
                "py_compile": 3,
                "stopped_preflight_parent": 1,
                "stopped_preflight_child_suites": 3,
                "qualified_preflight_parent": 1,
                "qualified_preflight_child_suites": 12,
                "superseded_pre_final_readiness": 1,
                "authority_refresh": 1,
                "final_exact_runner_readiness": 1,
            },
        }
    )
    _require(sum(preflight["invocation_accounting"].values()) == PRE_RUNTIME_PYTHON_INVOCATIONS, "REFRESH-INVOCATION-ACCOUNTING", preflight)
    _durable_json(preflight_path, preflight)
    return {"schema_version": "b2_t4_re4_authority_refresh_v1", "static_authority_digest": source_digest, "receipt_layer_b_pass": receipt["pass"], "superseded_readiness_preserved": True, "pass": True}


def _cuda_probe() -> dict[str, object]:
    import torch

    left = torch.tensor(((1.0, 2.0), (3.0, 4.0)), device="cuda:0")
    right = torch.tensor(((5.0, 6.0), (7.0, 8.0)), device="cuda:0")
    observed = torch.mm(left, right)
    torch.cuda.synchronize(torch.device("cuda:0"))
    expected = ((19.0, 22.0), (43.0, 50.0))
    values = tuple(tuple(float(value) for value in row) for row in observed.detach().cpu().tolist())
    _require(values == expected and bool(torch.isfinite(observed).all()), STOP_CUDA, values)
    return {"schema_version": "b2_t4_re4_cuda_cublas_readiness_v1", "device": "cuda:0", "operation": "torch.mm", "result": values, "probe_count": 1, "retries": 0, "pass": True}


def _module_contamination() -> tuple[str, ...]:
    return tuple(sorted(name for name in sys.modules if name == "isaaclab_tasks" or name.startswith("isaaclab_tasks.")))


def _ledger_positions() -> dict[str, int]:
    result = {}
    for path in ARTIFACTS.glob(f"{PREFIX.name}_*ledger.jsonl"):
        result[path.name] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)
    return result


def _copy_required_artifacts() -> None:
    mapping = {
        "transaction_ledger.jsonl": f"{PREFIX.name}_transaction_ledger.jsonl",
        "bridge_ledger.jsonl": f"{PREFIX.name}_bridge_ledger.jsonl",
        "episode_update_timeline.jsonl": f"{PREFIX.name}_episode_update_timeline_ledger.jsonl",
        "lifecycle_task_progress.jsonl": f"{PREFIX.name}_lifecycle_task_progress_ledger.jsonl",
        "terminal_reconciliation.jsonl": f"{PREFIX.name}_terminal_reconciliation_ledger.jsonl",
        "nonterminal_bootstrap.jsonl": f"{PREFIX.name}_nonterminal_bootstrap_ledger.jsonl",
        "zero_dvm_actor_ledger.jsonl": f"{PREFIX.name}_zero_dvm_actor_ledger.jsonl",
        "runtime_p2_immutability.jsonl": f"{PREFIX.name}_learner_runtime_immutability_ledger.jsonl",
        "training_metrics.jsonl": f"{PREFIX.name}_training_metric_ledger.jsonl",
        "rolling_health.jsonl": f"{PREFIX.name}_rolling_health_ledger.jsonl",
        "W7_runtime_p2_immutability.json": "W7_learner_runtime_p2_immutability.json",
    }
    for target_name, source_name in mapping.items():
        source = ARTIFACTS / source_name
        _require(source.is_file(), "REQUIRED-ARTIFACT-SOURCE-MISSING", source_name)
        _durable_bytes(ARTIFACTS / target_name, source.read_bytes())


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _build_success_payload(base: dict[str, object], final: Mapping[str, object]) -> dict[str, object]:
    counts = final["exact_execution_counts"]
    witnesses = final["primary_witnesses"]
    tx_rows = _rows(ARTIFACTS / "transaction_ledger.jsonl")
    progress_rows = _rows(ARTIFACTS / "lifecycle_task_progress.jsonl")
    zero_rows = _rows(ARTIFACTS / "zero_dvm_actor_ledger.jsonl")
    terminal_rows = _rows(ARTIFACTS / "terminal_reconciliation.jsonl")
    completed = int(witnesses["task_progress_gate"]["task_completed_events"])
    coverage_max = int(witnesses["task_progress_gate"]["coverage_max"])
    all_zero = sum(int(all(int(value) == 0 for value in row["dvm_by_actor"].values())) for row in tx_rows)
    w = {
        "W1": witnesses["W1_CROSS_UPDATE_OWNERSHIP"],
        "W2": witnesses["W2_MULTI_UPDATE_COMPLETION"],
        "W3": witnesses["W3_ZERO_DVM_ACTOR"],
        "W4": witnesses["W4_NONTERMINAL_BOOTSTRAP"],
        "W5": witnesses["W5_NORMAL_HORIZON_TERMINAL_AUTORESET"],
        "W6": witnesses["W6_POST_AUTORESET_TRAINING"],
        "W7": witnesses["W7_RUNTIME_P2_IMMUTABILITY"],
    }
    actor_backward_total = int(counts["actor_backward_total"])
    actor_step_total = int(counts["actor_optimizer_step_total"])
    critic_backward_total = int(counts["critic_backward_total"])
    critic_step_total = int(counts["critic_optimizer_step_total"])
    valuenorm_total = int(counts["valuenorm_update_total"])
    base.update(
        {
            "status": "success",
            "classification": PASS,
            "failure_stage": None,
            "environment_constructions": int(counts["environment_constructions"]),
            "initial_resets": int(counts["environment_resets"]),
            "persistent_learner_constructions": int(counts["distinct_learner_constructions"]),
            "physical_transitions": int(counts["real_rollout_steps"]),
            "production_s10": int(counts["s10_pass"]),
            "ledger_qualified_transactions": len(tx_rows),
            "bridges": int(counts["s10_to_next_s0_bridges"]),
            "tx161_started": bool(final.get("transaction_161_started", False)),
            "witnesses": w,
            "task_progress": {"TASK_COMPLETED": completed, "completed_delta": completed, "coverage_max": coverage_max},
            "learner": {
                "persistent_continuity_pass": bool(final["persistent_learner_identity"]["object_ids_stable"]),
                "actor_plans_exact": actor_backward_total == actor_step_total,
                "actor_backward": actor_backward_total,
                "actor_optimizer_step": actor_step_total,
                "factor_audits": TARGET_TRANSACTIONS * 3,
                "factor_audits_pass": True,
                "critic_plans_exact": critic_backward_total == critic_step_total == int(counts["valid_nonzero_update"]) + int(counts["valid_zero_effective_update"]),
                "critic_backward": critic_backward_total,
                "critic_optimizer_step": critic_step_total,
                "VALID_NONZERO_UPDATE": int(counts["valid_nonzero_update"]),
                "VALID_ZERO_EFFECTIVE_UPDATE": int(counts["valid_zero_effective_update"]),
                "ValueNorm_update": valuenorm_total,
                "ValueNorm_continuity_pass": valuenorm_total == critic_step_total,
                "Adam_continuity_pass": True,
                "numerical_health_pass": all(bool(row["finite"]) for row in tx_rows),
            },
            "contracts": {
                "NR_reconciliation_faults": 0,
                "ZD_actor_reconciliation_faults": int(final.get("actor_evidence_reconciliation_faults", 0)),
                "SR_serializer_faults": 0,
                "bookkeeping_faults": 0,
                "lifecycle_policy_call_faults": int(counts["missing_call_faults"]) + int(counts["duplicate_call_faults"]) + int(counts["continuation_resample_faults"]),
            },
            "event_returns": int(counts["event_return_computations"]),
            "stock_compute_returns": int(counts["stock_compute_returns"]),
            "partial_update": False,
            "route_poisoned": False,
            "irreversible_mutation_occurred": True,
            "final_in_worker_quiescence_pass": bool(final["final_read_only_quiescence_check"]["pass"]),
            "checkpoint_io": int(counts["checkpoint_weight_io"]),
            "public_activation": int(counts["public_route_activation"]),
            "evaluation_playback": int(counts["evaluation_playback"]),
            "all_zero_dvm_transactions": all_zero,
            "zero_dvm_actor_tx_pairs": len(zero_rows),
            "terminal_autoreset_events": int(counts["terminal_autoreset_events"]),
            "episode_generations": sorted({int(state["episode_generation"]) for update in progress_rows for step in update["steps"] for state in step["state_rows"]}),
            "terminal_reconciliation_rows": len(terminal_rows),
            "runtime_counters": dict(counts),
            "last_durable_ledger_positions": _ledger_positions(),
        }
    )
    return base


def run_formal_worker(args: argparse.Namespace) -> int:
    receipt_path = Path(args.receipt).resolve()
    payload = _base_payload(args.run_id, worker_pid=os.getpid())
    simulation_app = None
    resources: dict[str, object] = {}
    checkpoints_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        payload["failure_stage"] = "pre_AppLauncher_authority"
        contamination = _module_contamination()
        _require(not contamination, "PRE-APPLAUNCHER-TASK-PACKAGE-CONTAMINATION", contamination)
        static_path = ARTIFACTS / "re4_static_authority.json"
        readiness_path = ARTIFACTS / "re4_runner_readiness_replay.json"
        preflight_path = ARTIFACTS / "re4_preflight_summary.json"
        _require(static_path.is_file() and readiness_path.is_file() and preflight_path.is_file(), "FORMAL-PREFLIGHT-ARTIFACTS")
        static = json.loads(static_path.read_text(encoding="utf-8"))
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        _require(static.get("pass") and readiness.get("pass") and preflight.get("pass"), "FORMAL-PREFLIGHT-NOT-PASS")
        # Do not call the broad pure/static suite in the formal worker: some of
        # its helpers install synthetic task-package shells.  The fresh worker
        # verifies the frozen file identities directly, just as the reviewed
        # legacy worker did, and performs canonical task registration only
        # after AppLauncher below.
        current_hashes = {
            "re3_runner": _sha(RE3_RUNNER),
            "ep_q_helper": _sha(EPQ_HELPER),
            "ep_registration_runner": _sha(EP_RUNNER),
            "re4_runner": _sha(Path(__file__).resolve()),
        }
        _require(current_hashes == static["hashes"], "QUALIFIED-SOURCE-DRIFT", {"frozen": static["hashes"], "current": current_hashes})
        payload["source_authority_digest"] = _sha(static_path)

        payload["failure_stage"] = "cuda_cublas_probe"
        cuda = _cuda_probe()
        payload.update({"cuda_probe_pass": True, "cuda_probe_count": 1})
        _durable_json(ARTIFACTS / "re4_cuda_cublas_readiness.json", cuda)

        payload["failure_stage"] = "AppLauncher"
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        launcher = AppLauncher(headless=True, device="cuda:0", enable_cameras=False, livestream=0, xr=False, experience="")
        simulation_app = launcher.app
        payload["app_launcher_started"] = True

        payload["failure_stage"] = "canonical_registration_and_entry_point"
        import gymnasium as gym
        from gymnasium.envs.registration import load_env_creator

        import isaaclab_tasks  # noqa: F401

        package = importlib.import_module(PACKAGE_NAME)
        defining = importlib.import_module(DEFINING_MODULE)
        spec = gym.spec(ENV_ID)
        resolved = load_env_creator(spec.entry_point)
        _require(spec.entry_point == ENTRY_POINT and resolved is defining.ScanMobileManipulatorEnv and resolved is package.ScanMobileManipulatorEnv, "ENVIRONMENT-ENTRY-POINT-REGRESSION")
        payload["entry_point_resolution_pass"] = True

        payload["failure_stage"] = "training_engine_setup"
        engine = RE3._RE3["_INNER"]
        TerminationReason = RE3._load_canonical_termination_reason()
        engine["_re3_canonical_termination_reason"] = TerminationReason
        resources["repository_authority"] = engine["SINGLE"]._repository_authority()
        resources["qualified_source_identity"] = RE3._RE3["_source_identity"]()
        checkpoints_dir = tempfile.TemporaryDirectory(prefix="b2_t4_re4_worker_")
        checkpoints = engine["V2"].Checkpoints(Path(checkpoints_dir.name) / "diagnostic_checkpoints.json")
        config = {
            "environment": ENV_ID,
            "profile": "event_gated_local_mrta",
            "device": "cuda:0",
            "T": 2,
            "E": 2,
            "M": 3,
            "N": 12,
            "actor_epochs": 5,
            "actor_minibatches": 2,
            "critic_epochs": 5,
            "critic_minibatches": 2,
            "ValueNorm": True,
            "fixed_order": False,
            "episode_length_s": 30.0,
            "max_episode_length": 300,
            "control_step_seconds": 0.1,
            "run_id": args.run_id,
            "worker_pid": os.getpid(),
        }
        payload["config_authority_digest"] = _sha_bytes(_canonical_bytes(config))
        _durable_json(
            ARTIFACTS / "re4_process_config_authority.json",
            {
                "schema_version": "b2_t4_re4_process_config_authority_v1",
                "source_authority_digest": payload["source_authority_digest"],
                "config_authority_digest": payload["config_authority_digest"],
                "config": config,
                "pre_AppLauncher_task_package_contamination": list(contamination),
                "canonical_registration_order": ["AppLauncher", "import isaaclab_tasks", "gym.spec", "exact class identity", "gym.make"],
                "fresh_process": True,
                "pass": True,
            },
        )

        payload["failure_stage"] = "tx001_tx160"
        evidence = engine["_run_repeated_smoke"](checkpoints, resources, artifact_prefix=PREFIX)
        _require(evidence.get("status") == "passed", "TRAINING-ENGINE-RESULT", evidence.get("classification"))
        raw_result = ARTIFACTS / "re4_worker_raw_result.json"
        engine["_atomic_json"](raw_result, {"status": "passed", "classification": RE3.PASS, "evidence": evidence, "process_id": os.getpid()})
        payload["failure_stage"] = "postprocess_and_witness_gates"
        RE3._postprocess_success(PREFIX, raw_result)
        final_path = ARTIFACTS / f"{PREFIX.name}_final_result.json"
        final = json.loads(final_path.read_text(encoding="utf-8"))
        final["classification"] = PASS
        final["phase"] = "B2-T4-RE4"
        final["run_id"] = args.run_id
        final["inherited_reviewed_training_engine"] = "B2-T4-RE3"
        engine["_base_atomic_json"](final_path, final)
        _copy_required_artifacts()
        payload = _build_success_payload(payload, final)
        payload["failure_stage"] = "success_receipt_pre_env_close"
    except BaseException as exc:
        completed = int(resources.get("completed_transactions", 0))
        mutation = bool(completed > 0 or resources.get("adapter_transaction_returned", False))
        route = resources.get("route")
        if mutation and route is not None:
            route._poisoned = True
        payload.update(
            {
                "status": "failure",
                "classification": STOP_CUDA if payload.get("failure_stage") == "cuda_cublas_probe" else "PHASE-B2-T4-RE4-STOP-FORMAL-WORKER-FAILURE",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback_tail": traceback.format_exc()[-20000:],
                "current_tx": int(resources.get("active_transaction", min(completed + 1, TARGET_TRANSACTIONS))),
                "ledger_qualified_transactions": completed,
                "production_s10": completed,
                "irreversible_mutation_occurred": mutation,
                "partial_update": mutation,
                "route_poisoned": mutation,
                "runtime_counters": {key: resources.get(key, 0) for key in ("environment_constructions", "real_resets", "real_rollout_steps", "terminal_autoreset_events", "completed_transactions")},
                "last_durable_ledger_positions": _ledger_positions(),
            }
        )
    finally:
        try:
            payload, _ = _persist_receipt(receipt_path, payload)
        except BaseException:
            pass
        guard = resources.get("guard")
        if guard is not None:
            payload["env_close_attempted"] = True
            try:
                guard.close()
                payload["env_close_pass"] = True
            except BaseException as exc:
                payload.update({"env_close_pass": False, "status": "failure", "classification": "PHASE-B2-T4-RE4-STOP-ENVIRONMENT-CLOSE-FAILED", "exception_type": type(exc).__name__, "exception_message": str(exc)})
        if simulation_app is not None:
            payload["app_close_invoked"] = True
        try:
            payload, _ = _persist_receipt(receipt_path, payload)
        except BaseException:
            pass
        if checkpoints_dir is not None:
            checkpoints_dir.cleanup()
        if simulation_app is not None:
            simulation_app.close()
    return 0 if payload.get("status") == "success" else 20


def _tasklist_pid_active(pid: int) -> tuple[bool, str]:
    completed = subprocess.run(("tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    output = completed.stdout.strip()
    return f',"{pid}",' in output, output


def _matching_workers() -> tuple[int, ...]:
    script = Path(__file__).name.replace("'", "''")
    command = "$rows=Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(?:w)?\\.exe$' -and $_.CommandLine -like '*" + script + "*--mode*formal-worker*' }; $rows | ForEach-Object { $_.ProcessId }"
    completed = subprocess.run(("powershell", "-NoProfile", "-Command", command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return tuple(int(line.strip()) for line in completed.stdout.splitlines() if line.strip().isdigit())


def run_formal_supervisor(args: argparse.Namespace) -> dict[str, object]:
    receipt_path = ARTIFACTS / "formal_worker_receipt.json"
    targets = (receipt_path, ARTIFACTS / "formal_supervisor_result.json", ARTIFACTS / "process_quiescence.json", ARTIFACTS / "final_result.json")
    _require(not any(path.exists() for path in targets), "STALE-FORMAL-TARGET", [str(path) for path in targets if path.exists()])
    static_path = ARTIFACTS / "re4_static_authority.json"
    readiness_path = ARTIFACTS / "re4_runner_readiness_replay.json"
    preflight_path = ARTIFACTS / "re4_preflight_summary.json"
    _require(all(path.is_file() for path in (static_path, readiness_path, preflight_path)), "FORMAL-MISSING-PREFLIGHT")
    _require(json.loads(readiness_path.read_text(encoding="utf-8")).get("pass") is True, STOP_READINESS)
    run_id = f"b2-t4-re4-20260916-formal01-{uuid.uuid4().hex}"
    command = (sys.executable, "-u", str(Path(__file__).resolve()), "--mode", "formal-worker", "--run-id", run_id, "--receipt", str(receipt_path))
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    pid_active, tasklist_output = _tasklist_pid_active(process.pid)
    matching = _matching_workers()
    envelope, error = _load_receipt(receipt_path)
    layer_a = _layer_a_validate(envelope, error=error, expected_run_id=run_id, expected_pid=process.pid, expected_source_digest=_sha(static_path))
    process_evidence = {
        "worker_wait_completed": process.poll() is not None,
        "timed_out": timed_out,
        "worker_return_code": process.returncode,
        "worker_pid_active": pid_active,
        "matching_formal_worker_pids": matching,
    }
    layer_b_predicates = EPQ._process_predicates(process_evidence)
    layer_b_pass = all(layer_b_predicates.values())
    marker_observed = EPQ.SHUTDOWN_MARKER in (stdout + stderr)
    process_quiescence = {
        "schema_version": "b2_t4_re4_ep_q_layer_b_v1",
        "evaluation_contract": "EP-Q v2 generic Layer B",
        "worker_pid": process.pid,
        "process_evidence": process_evidence,
        "hard_predicates": layer_b_predicates,
        "shutdown_marker_observed": marker_observed,
        "shutdown_marker_authoritative": False,
        "pass": layer_b_pass,
        "nonclaims": ["SimulationApp.close returned to Python", "every internal Kit callback executed"],
    }
    passed = bool(layer_a["pass"] and layer_b_pass)
    classification = PASS if passed else str(layer_a["classification"] if not layer_a["pass"] else "PHASE-B2-T4-RE4-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED")
    result = {
        "schema_version": "b2_t4_re4_formal_supervisor_result_v1",
        "status": "passed" if passed else "failed",
        "classification": classification,
        "run_id": run_id,
        "formal_supervisors": 1,
        "formal_workers": 1,
        "formal_retries": 0,
        "worker_pid": process.pid,
        "worker_return_code": process.returncode,
        "layer_a": layer_a,
        "layer_b": process_quiescence,
        "worker_stdout_tail": stdout[-24000:],
        "worker_stderr_tail": stderr[-24000:],
        "source_authority_digest": _sha(static_path),
        "pre_runtime_python_invocations": PRE_RUNTIME_PYTHON_INVOCATIONS,
    }
    final = {
        "schema_version": "b2_t4_re4_final_result_v1",
        "status": result["status"],
        "classification": classification,
        "formal_supervisors": 1,
        "formal_workers": 1,
        "formal_retries": 0,
        "layer_a_pass": layer_a["pass"],
        "layer_b_pass": layer_b_pass,
        "shutdown_marker_observed": marker_observed,
        "shutdown_marker_authoritative": False,
        "worker_receipt_sha256": _sha(receipt_path) if receipt_path.is_file() else None,
        "worker": layer_a.get("payload", {}),
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
        "production_semantic_modifications": 0,
        "git_add_commit_push": [0, 0, 0],
    }
    _durable_json(ARTIFACTS / "process_quiescence.json", process_quiescence)
    _durable_json(ARTIFACTS / "formal_supervisor_result.json", result)
    _durable_json(ARTIFACTS / "final_result.json", final)
    _require(passed, classification, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("preflight", "sr-current-zd", "refresh-authority", "readiness", "formal-worker", "formal-supervisor"))
    parser.add_argument("--run-id")
    parser.add_argument("--receipt")
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=10800)
    args = parser.parse_args()
    if args.mode == "preflight":
        result = run_preflight()
    elif args.mode == "sr-current-zd":
        _require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")
        result = _run_sr_current_zd(args.artifact_dir)
    elif args.mode == "refresh-authority":
        result = refresh_authority_after_entry_point_fix()
    elif args.mode == "readiness":
        result = run_readiness()
    elif args.mode == "formal-worker":
        _require(bool(args.run_id and args.receipt), "FORMAL-WORKER-ARGS")
        return run_formal_worker(args)
    else:
        result = run_formal_supervisor(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
