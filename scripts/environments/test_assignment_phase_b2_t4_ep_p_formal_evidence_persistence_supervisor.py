"""B2-T4-EP-P durable worker receipt and external-supervisor qualification."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260916"
ARTIFACTS = DATE_ROOT / "b2_t4_ep_p_artifacts"
EP_SCRIPT = HERE / "test_assignment_phase_b2_t4_ep_environment_entry_point_registration_boundary.py"
RE3_RUNNER = HERE / "test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py"

ENV_ID = "Isaac-Scan-Mobile-Manipulator-Direct-v0"
PACKAGE_NAME = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEFINING_MODULE = PACKAGE_NAME + ".scan_mobile_manipulator_env"
ENTRY_POINT = PACKAGE_NAME + ":ScanMobileManipulatorEnv"
ENVELOPE_SCHEMA = "b2_t4_ep_p_worker_receipt_envelope_v1"
WORKER_SCHEMA = "b2_t4_ep_p_formal_worker_receipt_v1"
SYNTHETIC_SCHEMA = "b2_t4_ep_p_synthetic_worker_receipt_v1"
PASS = "PHASE-B2-T4-EP-P-FORMAL-EVIDENCE-PERSISTENCE-SUPERVISOR-QUALIFIED-AWAITING-GPT-REVIEW"

EXPECTED_HASHES = {
    "isaaclab_tasks_root_initializer": "e10fe2f377265733b534b38ea85b5e83c8ec3d116a49376a445410d69f8ab0d9",
    "direct_initializer": "29f633f50248f8d7c6827e64b9036c8a88cc58680cffc0bacce8d5e4bfc02907",
    "scan_package_initializer": "c72daa4adfdbc2d98265956207ee5b75e53c3dbf92ad58b64b915b13a0e9ff46",
    "scan_environment": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    "repaired_re3_runner": "02fcba5b1798c9c77be0af7d9ae4de9ce1ea7c392e9ea69c1cf52eb1e33f0ce1",
    "protected_full_transaction": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "protected_real_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
}

SOURCE_PATHS = {
    "isaaclab_tasks_root_initializer": ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "__init__.py",
    "direct_initializer": ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "__init__.py",
    "scan_package_initializer": SCAN / "__init__.py",
    "scan_environment": SCAN / "scan_mobile_manipulator_env.py",
    "repaired_re3_runner": RE3_RUNNER,
    "ep_p_worker_supervisor": Path(__file__).resolve(),
    "protected_full_transaction": SCAN / "assignment_event_training_full_transaction.py",
    "protected_real_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
}

HISTORICAL_EP_PATHS = {
    "ep_report": SCAN / "AgentRead" / "202609" / "20260915" / "PHASE_B2_T4_EP_ENVIRONMENT_ENTRY_POINT_REGISTRATION_BOUNDARY_QUALIFICATION_REPORT.md",
    "ep_formal_smoke": SCAN / "AgentRead" / "202609" / "20260915" / "b2_t4_ep_artifacts" / "formal_environment_smoke.json",
    "ep_reset_evidence": SCAN / "AgentRead" / "202609" / "20260915" / "b2_t4_ep_artifacts" / "reset_structural_evidence.json",
    "ep_final_result": SCAN / "AgentRead" / "202609" / "20260915" / "b2_t4_ep_artifacts" / "final_result.json",
}


def _require(condition: bool, code: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-EP-P {code}: {detail!r}")


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _envelope(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "payload_sha256": _sha_bytes(_canonical_bytes(normalized)),
        "payload": normalized,
    }


def _durable_bytes(path: Path, encoded: bytes, *, replace: bool = True) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        os.replace(temporary, path)
        target = path
    else:
        target = temporary
    return {
        "target": str(target),
        "bytes": len(encoded),
        "sha256": _sha(target),
        "file_fsync_pass": True,
        "atomic_replace_pass": replace,
    }


def _durable_json(path: Path, payload: object) -> dict[str, object]:
    return _durable_bytes(path, json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def _read_envelope(path: Path) -> tuple[bool, dict[str, object], str | None]:
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        if type(parsed) is not dict or type(parsed.get("payload")) is not dict:
            return False, {}, "envelope/payload type"
        if parsed.get("schema_version") != ENVELOPE_SCHEMA:
            return False, parsed, "envelope schema"
        observed = _sha_bytes(_canonical_bytes(parsed["payload"]))
        if parsed.get("payload_sha256") != observed:
            return False, parsed, "payload digest"
        return True, parsed, None
    except BaseException as exc:
        return False, {}, f"{type(exc).__name__}: {exc}"


def _persist_worker_receipt(path: Path, payload: Mapping[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    first = dict(payload)
    first.update(
        {
            "receipt_written_before_app_close": True,
            "receipt_fsync_pass": True,
            "receipt_readback_pass": False,
            "receipt_persisted_wall_time_ns": time.time_ns(),
            "receipt_persisted_monotonic_ns": time.monotonic_ns(),
        }
    )
    _durable_json(path, _envelope(first))
    valid, parsed, error = _read_envelope(path)
    _require(valid and parsed["payload"] == first, "WORKER-RECEIPT-FIRST-READBACK", error)
    final = dict(first)
    final["receipt_readback_pass"] = True
    final["receipt_readback_monotonic_ns"] = time.monotonic_ns()
    write = _durable_json(path, _envelope(final))
    valid, parsed, error = _read_envelope(path)
    _require(valid and parsed["payload"] == final, "WORKER-RECEIPT-FINAL-READBACK", error)
    return final, write


def _shape(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _shape(item) for key, item in value.items()}
    shape = getattr(value, "shape", None)
    if shape is not None:
        return [int(dimension) for dimension in shape]
    if value is None:
        return None
    return type(value).__name__


def _module_state() -> dict[str, object]:
    names = (
        "isaaclab_tasks",
        "isaaclab_tasks.direct",
        PACKAGE_NAME,
        DEFINING_MODULE,
    )
    return {
        name: {
            "present": name in sys.modules,
            "file": getattr(sys.modules.get(name), "__file__", None),
            "spec": repr(getattr(sys.modules.get(name), "__spec__", None)),
            "has_env_class": hasattr(sys.modules.get(name), "ScanMobileManipulatorEnv"),
        }
        for name in names
    }


def _source_hashes() -> dict[str, str]:
    return {name: _sha(path) for name, path in SOURCE_PATHS.items()}


def _source_identity_manifest() -> dict[str, object]:
    hashes = _source_hashes()
    expected_pass = all(hashes[name] == expected for name, expected in EXPECTED_HASHES.items())
    historical = {name: _sha(path) for name, path in HISTORICAL_EP_PATHS.items()}
    registration_status = subprocess.run(
        (
            "git",
            "status",
            "--short",
            "--",
            str(SOURCE_PATHS["isaaclab_tasks_root_initializer"].relative_to(ROOT)),
            str(SOURCE_PATHS["direct_initializer"].relative_to(ROOT)),
            str(SOURCE_PATHS["scan_package_initializer"].relative_to(ROOT)),
            str(SOURCE_PATHS["scan_environment"].relative_to(ROOT)),
        ),
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()
    _require(expected_pass, "PRODUCTION-SOURCE-DRIFT", {"actual": hashes, "expected": EXPECTED_HASHES})
    _require(registration_status == "", "PRODUCTION-REGISTRATION-SOURCE-DRIFT", registration_status)
    return {
        "schema_version": "b2_t4_ep_p_source_identity_manifest_v1",
        "hashes": hashes,
        "expected_protected_and_registration_hashes": EXPECTED_HASHES,
        "expected_hashes_pass": expected_pass,
        "production_registration_git_status": registration_status,
        "historical_ep_immutable_hashes": historical,
        "production_files_changed": 0,
        "pass": True,
    }


def _base_receipt(*, schema: str, run_id: str, worker_pid: int, status: str) -> dict[str, object]:
    success = status == "success"
    return {
        "schema_version": schema,
        "phase": "B2-T4-EP-P",
        "run_id": run_id,
        "worker_pid": worker_pid,
        "status": status,
        "classification": PASS if success else "PHASE-B2-T4-EP-P-STOP-SYNTHETIC-WORKER-FAILURE",
        "failure_stage": None if success else "synthetic_failure",
        "exception_type": None if success else "SyntheticFailure",
        "exception_message": None if success else "intentional pure failure witness",
        "cuda_probe_pass": success,
        "app_launcher_started": success,
        "gym_spec_pass": success,
        "entry_point_resolution_pass": success,
        "environment_constructed": success,
        "reset_attempted": success,
        "reset_pass": success,
        "structure_assertions_pass": success,
        "env_close_attempted": success,
        "env_close_pass": success,
        "app_close_invoked": success,
        "env_id": ENV_ID,
        "spec_entry_point": ENTRY_POINT,
        "resolved_class_module": DEFINING_MODULE,
        "resolved_class_name": "ScanMobileManipulatorEnv",
        "env_type": "synthetic.Env",
        "unwrapped_env_type": "synthetic.Env",
        "profile": "event_gated_local_mrta",
        "device": "cuda:0",
        "num_envs": 2,
        "robot_count": 3,
        "viewpoint_count": 12,
        "episode_length_s": 30.0,
        "max_episode_length": 300,
        "control_step_seconds": 0.1,
        "observation_structure_summary": {"robot_0": [2, 1]},
        "shared_observation_shape": [2, 3],
        "available_actions_shape": None,
        "episode_generation_summary": {"shape": [2], "values": [1, 1]},
        "P2_initialization_summary": {"event_runtime_initialized": success},
        "physical_steps": 0,
        "learner_constructions": 0,
        "learner_mutations": 0,
        "actor_backward": 0,
        "actor_optimizer_steps": 0,
        "critic_backward": 0,
        "critic_optimizer_steps": 0,
        "ValueNorm_updates": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
    }


def _validate_receipt(
    path: Path,
    *,
    expected_run_id: str,
    expected_pid: int,
    worker_return_code: int,
    expected_schema: str,
) -> dict[str, object]:
    valid, envelope, error = _read_envelope(path) if path.is_file() else (False, {}, "missing receipt")
    payload = envelope.get("payload", {}) if valid else {}
    identity_checks = {
        "envelope_valid": valid,
        "payload_schema": payload.get("schema_version") == expected_schema,
        "run_id": payload.get("run_id") == expected_run_id,
        "worker_pid": payload.get("worker_pid") == expected_pid,
    }
    success_checks = {
        "worker_status_success": payload.get("status") == "success",
        "worker_return_code_zero": worker_return_code == 0,
        "cuda_probe_pass": payload.get("cuda_probe_pass") is True,
        "app_launcher_started": payload.get("app_launcher_started") is True,
        "gym_spec_pass": payload.get("gym_spec_pass") is True,
        "entry_point_resolution_pass": payload.get("entry_point_resolution_pass") is True,
        "environment_constructed": payload.get("environment_constructed") is True,
        "reset_attempted": payload.get("reset_attempted") is True,
        "reset_pass": payload.get("reset_pass") is True,
        "structure_assertions_pass": payload.get("structure_assertions_pass") is True,
        "receipt_pre_app_close": payload.get("receipt_written_before_app_close") is True,
        "receipt_fsync": payload.get("receipt_fsync_pass") is True,
        "receipt_readback": payload.get("receipt_readback_pass") is True,
        "env_close_pass": payload.get("env_close_pass") is True,
        "app_close_invoked": payload.get("app_close_invoked") is True,
        "physical_steps_zero": payload.get("physical_steps") == 0,
        "learner_constructions_zero": payload.get("learner_constructions") == 0,
        "learner_mutations_zero": payload.get("learner_mutations") == 0,
        "entry_point_exact": payload.get("spec_entry_point") == ENTRY_POINT,
        "formal_config_exact": (
            payload.get("device") == "cuda:0"
            and payload.get("num_envs") == 2
            and payload.get("robot_count") == 3
            and payload.get("viewpoint_count") == 12
            and payload.get("episode_length_s") == 30.0
            and payload.get("max_episode_length") == 300
            and payload.get("control_step_seconds") == 0.1
        ),
    }
    identity_pass = all(identity_checks.values())
    qualification_pass = bool(identity_pass and all(success_checks.values()))
    if not valid:
        classification = "PHASE-B2-T4-EP-P-STOP-WORKER-RECEIPT-NOT-PERSISTED" if error == "missing receipt" else "PHASE-B2-T4-EP-P-STOP-WORKER-RECEIPT-MALFORMED"
    elif not identity_checks["payload_schema"]:
        classification = "PHASE-B2-T4-EP-P-STOP-WORKER-RECEIPT-WRONG-SCHEMA"
    elif not identity_checks["run_id"]:
        classification = "PHASE-B2-T4-EP-P-STOP-WORKER-RECEIPT-RUN-ID-MISMATCH"
    elif not identity_checks["worker_pid"]:
        classification = "PHASE-B2-T4-EP-P-STOP-WORKER-RECEIPT-PID-MISMATCH"
    elif payload.get("status") != "success":
        classification = str(payload.get("classification") or "PHASE-B2-T4-EP-P-STOP-WORKER-REPORTED-FAILURE")
    elif worker_return_code != 0:
        classification = "PHASE-B2-T4-EP-P-STOP-WORKER-EXIT-RECEIPT-CONFLICT"
    elif not success_checks["reset_pass"]:
        classification = "PHASE-B2-T4-EP-P-STOP-RESET-NOT-QUALIFIED"
    elif not success_checks["structure_assertions_pass"]:
        classification = "PHASE-B2-T4-EP-P-STOP-STRUCTURAL-ASSERTION-FAILED"
    elif not success_checks["learner_mutations_zero"]:
        classification = "PHASE-B2-T4-EP-P-STOP-LEARNER-MUTATION-NONZERO"
    else:
        classification = PASS if qualification_pass else "PHASE-B2-T4-EP-P-STOP-SUPERVISOR-ADJUDICATION-FAILED"
    return {
        "receipt_path": str(path),
        "receipt_file_sha256": _sha(path) if path.is_file() else None,
        "parse_error": error,
        "identity_checks": identity_checks,
        "success_checks": success_checks,
        "identity_pass": identity_pass,
        "qualification_pass": qualification_pass,
        "worker_status": payload.get("status"),
        "classification": classification,
        "payload": payload,
    }


def _run_synthetic_worker(args: argparse.Namespace) -> int:
    receipt = Path(args.receipt).resolve()
    scenario = args.scenario
    payload = _base_receipt(
        schema=SYNTHETIC_SCHEMA,
        run_id=args.run_id,
        worker_pid=os.getpid(),
        status="failure" if scenario == "failure" else "success",
    )
    if scenario in {"success", "failure", "nonzero_success"}:
        _persist_worker_receipt(receipt, payload)
    elif scenario == "malformed":
        _durable_bytes(receipt, b"{not-json\n")
    elif scenario == "temp_only":
        _durable_bytes(receipt, _canonical_bytes(_envelope(payload)), replace=False)
    elif scenario != "missing":
        raise ValueError(scenario)
    os._exit(17 if scenario == "failure" else 9 if scenario == "nonzero_success" else 0)


def _launch_synthetic(directory: Path, scenario: str) -> dict[str, object]:
    run_id = f"synthetic-{scenario}-{uuid.uuid4().hex}"
    receipt = directory / f"{scenario}.json"
    command = [
        sys.executable,
        "-u",
        str(Path(__file__).resolve()),
        "--mode",
        "synthetic-worker",
        "--scenario",
        scenario,
        "--run-id",
        run_id,
        "--receipt",
        str(receipt),
    ]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(timeout=30)
    validation = _validate_receipt(
        receipt,
        expected_run_id=run_id,
        expected_pid=process.pid,
        worker_return_code=int(process.returncode),
        expected_schema=SYNTHETIC_SCHEMA,
    )
    return {
        "scenario": scenario,
        "run_id": run_id,
        "worker_pid": process.pid,
        "worker_return_code": process.returncode,
        "worker_exited": process.poll() is not None,
        "receipt_exists": receipt.is_file(),
        "temp_files": tuple(path.name for path in directory.glob(f"{receipt.name}.tmp.*")),
        "stdout": stdout,
        "stderr": stderr,
        "validation": validation,
    }


def _write_test_envelope(path: Path, payload: Mapping[str, object], *, corrupt_digest: bool = False) -> None:
    envelope = _envelope(payload)
    if corrupt_digest:
        envelope["payload_sha256"] = "0" * 64
    _durable_json(path, envelope)


def _run_negative_matrix(directory: Path) -> dict[str, object]:
    run_id = "negative-current-run"
    pid = 424242
    base = _base_receipt(schema=SYNTHETIC_SCHEMA, run_id=run_id, worker_pid=pid, status="success")
    cases: dict[str, object] = {}

    def validate_case(name: str, payload: Mapping[str, object] | None, *, return_code: int = 0, malformed: bytes | None = None, corrupt_digest: bool = False, expected_run: str = run_id, expected_pid: int = pid, temp_only: bool = False) -> None:
        path = directory / f"negative_{name}.json"
        if malformed is not None:
            _durable_bytes(path, malformed)
        elif payload is not None and temp_only:
            _durable_bytes(path, _canonical_bytes(_envelope(payload)), replace=False)
        elif payload is not None:
            _write_test_envelope(path, payload, corrupt_digest=corrupt_digest)
        result = _validate_receipt(
            path,
            expected_run_id=expected_run,
            expected_pid=expected_pid,
            worker_return_code=return_code,
            expected_schema=SYNTHETIC_SCHEMA,
        )
        cases[name] = {
            "qualification_pass": result["qualification_pass"],
            "classification": result["classification"],
            "fail_closed_pass": not result["qualification_pass"],
            "final_receipt_exists": path.is_file(),
            "temp_files": tuple(candidate.name for candidate in directory.glob(f"{path.name}.tmp.*")),
        }

    validate_case("missing_receipt", None)
    validate_case("malformed_json", None, malformed=b"{bad-json")
    wrong_schema = dict(base, schema_version="wrong_schema")
    validate_case("wrong_schema", wrong_schema)
    wrong_run = dict(base, run_id="wrong-run")
    validate_case("wrong_run_id", wrong_run)
    wrong_pid = dict(base, worker_pid=pid + 1)
    validate_case("wrong_pid", wrong_pid)
    reset_false = dict(base, reset_pass=False)
    validate_case("success_reset_false", reset_false)
    structure_false = dict(base, structure_assertions_pass=False)
    validate_case("success_structure_false", structure_false)
    mutation = dict(base, learner_mutations=1)
    validate_case("success_learner_mutation", mutation)
    stale = dict(base, run_id="previous-formal-attempt")
    validate_case("stale_previous_attempt", stale)
    validate_case("temp_without_final_replace", base, temp_only=True)
    validate_case("digest_mismatch", base, corrupt_digest=True)
    validate_case("nonzero_exit_success_receipt", base, return_code=9)
    passed = all(bool(value["fail_closed_pass"]) for value in cases.values())
    _require(passed, "SUPERVISOR-NEGATIVE-MATRIX", cases)
    return {
        "schema_version": "b2_t4_ep_p_supervisor_negative_matrix_v1",
        "case_count": len(cases),
        "cases": cases,
        "pass": passed,
    }


def _run_entry_point_regression() -> dict[str, object]:
    command = [sys.executable, str(EP_SCRIPT), "--mode", "probe", "--sequence", "re3"]
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    lines = [line for line in completed.stdout.splitlines() if line.startswith("B2_T4_EP_JSON=")]
    payload = json.loads(lines[0].split("=", 1)[1]) if len(lines) == 1 else {}
    before = payload.get("module_state_before_canonical_registration", {})
    unpolluted = bool(before and not any(value.get("present") for value in before.values()))
    passed = bool(
        completed.returncode == 0
        and payload.get("pass") is True
        and payload.get("spec", {}).get("entry_point") == ENTRY_POINT
        and payload.get("resolved_class", {}).get("identity_matches_defining_module") is True
        and unpolluted
    )
    _require(passed, "ENTRY-POINT-REGRESSION", {"returncode": completed.returncode, "payload": payload, "stderr": completed.stderr})
    return {
        "schema_version": "b2_t4_ep_p_entry_point_regression_v1",
        "fresh_process": True,
        "return_code": completed.returncode,
        "repaired_re3_pre_AppLauncher_unpolluted": unpolluted,
        "gym_spec_entry_point": payload["spec"]["entry_point"],
        "class_identity_matches_defining_module": payload["resolved_class"]["identity_matches_defining_module"],
        "class_identity_matches_package_export": payload["resolved_class"]["identity_matches_package_export"],
        "process_id": payload["process_id"],
        "pass": passed,
    }


def _run_preflight() -> dict[str, object]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    forbidden = tuple(
        path.name
        for path in ARTIFACTS.iterdir()
        if path.name.startswith("formal_") or path.name in {"reset_structural_evidence.json", "process_quiescence.json", "final_result.json"}
    )
    _require(not forbidden, "PREEXISTING-FORMAL-ARTIFACT", forbidden)
    with tempfile.TemporaryDirectory(prefix="b2_t4_ep_p_pure_") as name:
        directory = Path(name)
        synthetic = {
            scenario: _launch_synthetic(directory, scenario)
            for scenario in ("success", "failure", "missing", "malformed", "temp_only", "nonzero_success")
        }
        negatives = _run_negative_matrix(directory)
    success = synthetic["success"]
    failure = synthetic["failure"]
    _require(success["validation"]["qualification_pass"], "PURE-SUCCESS-RECEIPT", success)
    _require(
        failure["validation"]["identity_pass"]
        and not failure["validation"]["qualification_pass"]
        and failure["validation"]["worker_status"] == "failure",
        "PURE-FAILURE-RECEIPT",
        failure,
    )
    _require(
        not synthetic["missing"]["validation"]["qualification_pass"]
        and not synthetic["malformed"]["validation"]["qualification_pass"]
        and not synthetic["temp_only"]["validation"]["qualification_pass"]
        and not synthetic["nonzero_success"]["validation"]["qualification_pass"],
        "PURE-SUPERVISOR-FAIL-CLOSED",
        synthetic,
    )
    entry_point = _run_entry_point_regression()
    manifest = _source_identity_manifest()
    persistence_contract = {
        "schema_version": "b2_t4_ep_p_persistence_contract_v1",
        "ordering": [
            "construct receipt payload",
            "write unique temp file",
            "flush",
            "os.fsync",
            "close",
            "os.replace",
            "read final envelope",
            "verify payload digest and equality",
            "env.close",
            "persist env-close update",
            "persist app-close-invoked marker",
            "SimulationApp.close",
        ],
        "mandatory_writes_after_SimulationApp_close": 0,
        "pass": True,
    }
    supervisor_contract = {
        "schema_version": "b2_t4_ep_p_supervisor_contract_v1",
        "outside_AppLauncher_worker": True,
        "requires_valid_receipt": True,
        "requires_matching_run_id": True,
        "requires_matching_worker_pid": True,
        "requires_payload_digest": True,
        "requires_success_flags": True,
        "requires_zero_exit_for_success": True,
        "exit_code_zero_alone_is_pass": False,
        "requires_process_quiescence": True,
        "formal_retry_count": 0,
        "pass": True,
    }
    outputs = {
        "persistence_contract.json": persistence_contract,
        "supervisor_contract.json": supervisor_contract,
        "pure_success_receipt_test.json": success,
        "pure_failure_receipt_test.json": failure,
        "supervisor_negative_matrix.json": negatives,
        "stale_receipt_test.json": {
            "schema_version": "b2_t4_ep_p_stale_receipt_test_v1",
            "wrong_run_id": negatives["cases"]["wrong_run_id"],
            "stale_previous_attempt": negatives["cases"]["stale_previous_attempt"],
            "temp_without_final_replace": negatives["cases"]["temp_without_final_replace"],
            "pass": True,
        },
        "entry_point_regression.json": entry_point,
        "source_identity_manifest.json": manifest,
    }
    for filename, payload in outputs.items():
        _durable_json(ARTIFACTS / filename, payload)
    result = {
        "schema_version": "b2_t4_ep_p_preflight_v1",
        "synthetic_worker_processes": 6,
        "synthetic_success_receipts": 2,
        "supervisor_negative_cases": negatives["case_count"],
        "fresh_process_entry_point_regression_probes": 1,
        "source_identity_pass": manifest["pass"],
        "pass": True,
    }
    _durable_json(ARTIFACTS / "preflight_result.json", result)
    return result


def _formal_payload(run_id: str) -> dict[str, object]:
    return {
        "schema_version": WORKER_SCHEMA,
        "phase": "B2-T4-EP-P",
        "run_id": run_id,
        "worker_pid": os.getpid(),
        "status": "failure",
        "classification": "PHASE-B2-T4-EP-P-STOP-WORKER-NOT-COMPLETE",
        "failure_stage": "worker_start",
        "exception_type": None,
        "exception_message": None,
        "traceback_tail": None,
        "worker_started_wall_time_ns": time.time_ns(),
        "worker_started_monotonic_ns": time.monotonic_ns(),
        "cuda_probe_pass": False,
        "app_launcher_started": False,
        "gym_spec_pass": False,
        "entry_point_resolution_pass": False,
        "environment_constructed": False,
        "reset_attempted": False,
        "reset_pass": False,
        "structure_assertions_pass": False,
        "env_close_attempted": False,
        "env_close_pass": False,
        "app_close_invoked": False,
        "env_id": ENV_ID,
        "spec_entry_point": None,
        "resolved_class_module": None,
        "resolved_class_name": None,
        "env_type": None,
        "unwrapped_env_type": None,
        "profile": "event_gated_local_mrta",
        "device": None,
        "num_envs": None,
        "robot_count": None,
        "viewpoint_count": None,
        "episode_length_s": None,
        "max_episode_length": None,
        "control_step_seconds": None,
        "observation_structure_summary": None,
        "shared_observation_shape": None,
        "available_actions_shape": None,
        "episode_generation_summary": None,
        "P2_initialization_summary": None,
        "physical_steps": 0,
        "learner_constructions": 0,
        "learner_mutations": 0,
        "actor_backward": 0,
        "actor_optimizer_steps": 0,
        "critic_backward": 0,
        "critic_optimizer_steps": 0,
        "ValueNorm_updates": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
    }


def _run_formal_worker(args: argparse.Namespace) -> int:
    receipt_path = Path(args.receipt).resolve()
    payload = _formal_payload(args.run_id)
    env = None
    simulation_app = None
    try:
        payload["failure_stage"] = "repaired_re3_pre_AppLauncher_import"
        importlib.import_module("test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration")
        pre_launcher = _module_state()
        _require(not any(value["present"] for value in pre_launcher.values()), "ENTRY-POINT-REGRESSION", pre_launcher)
        payload["pre_AppLauncher_module_state"] = pre_launcher

        payload["failure_stage"] = "cuda_readiness"
        import torch

        cuda_probe = torch.tensor(((1.0, 2.0), (3.0, 4.0)), device="cuda:0")
        cuda_result = cuda_probe @ cuda_probe
        torch.cuda.synchronize()
        _require(cuda_result.detach().cpu().tolist() == [[7.0, 10.0], [15.0, 22.0]], "CUDA-READINESS")
        payload["cuda_probe_pass"] = True
        payload["cuda_probe_result"] = cuda_result.detach().cpu().tolist()
        del cuda_probe, cuda_result

        payload["failure_stage"] = "AppLauncher"
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        launcher = AppLauncher(headless=True, device="cuda:0", enable_cameras=False, livestream=0, xr=False, experience="")
        simulation_app = launcher.app
        payload["app_launcher_started"] = True

        payload["failure_stage"] = "gym_spec_and_entry_point"
        import gymnasium as gym
        from gymnasium.envs.registration import load_env_creator

        import isaaclab_tasks  # noqa: F401
        package = importlib.import_module(PACKAGE_NAME)
        defining = importlib.import_module(DEFINING_MODULE)
        spec = gym.spec(ENV_ID)
        resolved = load_env_creator(spec.entry_point)
        _require(spec.id == ENV_ID and spec.entry_point == ENTRY_POINT, "FORMAL-GYM-SPEC", spec)
        _require(resolved is defining.ScanMobileManipulatorEnv and resolved is package.ScanMobileManipulatorEnv, "FORMAL-CLASS-IDENTITY")
        payload.update(
            {
                "gym_spec_pass": True,
                "entry_point_resolution_pass": True,
                "spec_entry_point": spec.entry_point,
                "resolved_class_module": resolved.__module__,
                "resolved_class_name": resolved.__name__,
            }
        )

        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
            _EventProfileLifecycleDomainSpec,
            _EventProfileLifecycleRuntimeDomain,
        )
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
            AssignmentProfileName,
            AssignmentProfileResolutionOrigin,
            resolve_assignment_profile,
        )

        cfg = defining.ScanMobileManipulatorEnvCfg()
        cfg.scene.num_envs = 2
        cfg.episode_length_s = 30.0
        profile = resolve_assignment_profile(AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        cfg.assignment_lifecycle_profile = profile.profile_name.value
        device = torch.device(cfg.sim.device)
        resolved_m = len(cfg.possible_agents)
        resolved_n = len(cfg.viewpoint_poses)
        domain = _EventProfileLifecycleRuntimeDomain(
            _EventProfileLifecycleDomainSpec(
                profile,
                device=device,
                env_ids=torch.arange(2, dtype=torch.int64, device=device),
                num_robots=resolved_m,
                num_tasks=resolved_n,
            )
        )

        payload["failure_stage"] = "gym_make"
        env = gym.make(
            ENV_ID,
            cfg=cfg,
            resolved_assignment_profile=profile,
            event_lifecycle_runtime_domain=domain,
            event_admission_validation_port=domain.environment_admission_validation_port,
        )
        payload["environment_constructed"] = True
        raw = env.unwrapped
        _require(type(raw) is resolved, "FORMAL-CONSTRUCTED-TYPE", type(raw))
        wrapper = _compose_event_assignment_harl_wrapper(
            env=env,
            resolved_assignment_profile=profile,
            runtime_domain=domain,
            assignment_profile_entrypoint="B2-T4-EP-P.environment_reset_smoke",
        )

        payload["failure_stage"] = "reset"
        payload["reset_attempted"] = True
        reset_result = wrapper.reset()
        _require(type(reset_result) is tuple and len(reset_result) == 3, "FORMAL-RESET-CONTRACT")
        observations, shared_observations, available_actions = reset_result
        payload["reset_pass"] = True
        generations = wrapper.last_lifecycle_episode_generation
        current_publication = domain.current_read_port.read_current()
        structure = {
            "observation_structure_summary": _shape(observations),
            "shared_observation_shape": _shape(shared_observations),
            "available_actions_shape": _shape(available_actions),
            "available_actions_expected_absent_at_I4_boundary": available_actions is None,
            "device": str(raw.device),
            "num_envs": int(raw.num_envs),
            "robot_count": int(raw.num_agents_cfg),
            "viewpoint_count": int(raw.num_viewpoints),
            "episode_length_s": float(raw.cfg.episode_length_s),
            "max_episode_length": int(raw.max_episode_length),
            "control_step_seconds": float(raw.step_dt),
            "episode_generation_summary": {
                "shape": _shape(generations),
                "values": [int(value) for value in generations.detach().cpu().tolist()],
            },
            "P2_initialization_summary": {
                "event_runtime_initialized": raw._event_lifecycle_environment_port is domain.environment_port,
                "current_publication_type": type(current_publication).__name__,
            },
            "physical_steps": int(raw.common_step_counter),
        }
        payload["failure_stage"] = "structural_assertions"
        _require(
            structure["device"] == "cuda:0"
            and structure["num_envs"] == 2
            and structure["robot_count"] == 3
            and structure["viewpoint_count"] == 12
            and structure["episode_length_s"] == 30.0
            and structure["max_episode_length"] == 300
            and structure["control_step_seconds"] == 0.1
            and structure["P2_initialization_summary"]["event_runtime_initialized"]
            and structure["physical_steps"] == 0,
            "FORMAL-STRUCTURE",
            structure,
        )
        payload.update(structure)
        payload.update(
            {
                "structure_assertions_pass": True,
                "env_type": f"{type(env).__module__}.{type(env).__name__}",
                "unwrapped_env_type": f"{type(raw).__module__}.{type(raw).__name__}",
                "profile": profile.profile_name.value,
                "status": "success",
                "classification": PASS,
                "failure_stage": None,
            }
        )
    except BaseException as exc:
        payload.update(
            {
                "status": "failure",
                "classification": "PHASE-B2-T4-EP-P-STOP-FORMAL-WORKER-FAILURE",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback_tail": traceback.format_exc()[-12000:],
            }
        )
    finally:
        try:
            payload, _ = _persist_worker_receipt(receipt_path, payload)
        except BaseException:
            pass
        if env is not None:
            payload["env_close_attempted"] = True
            try:
                env.close()
                payload["env_close_pass"] = True
            except BaseException as exc:
                payload["env_close_pass"] = False
                payload["status"] = "failure"
                payload["classification"] = "PHASE-B2-T4-EP-P-STOP-ENVIRONMENT-CLOSE-FAILED"
                payload["exception_type"] = type(exc).__name__
                payload["exception_message"] = str(exc)
        if simulation_app is not None:
            payload["app_close_invoked"] = True
        try:
            payload, _ = _persist_worker_receipt(receipt_path, payload)
        except BaseException:
            pass
        if simulation_app is not None:
            simulation_app.close()
    return 0 if payload["status"] == "success" else 20


def _tasklist_pid_active(pid: int) -> tuple[bool, str]:
    completed = subprocess.run(
        ("tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = completed.stdout.strip()
    return f',"{pid}",' in output, output


def _formal_worker_processes() -> tuple[int, ...]:
    script_name = Path(__file__).name.replace("'", "''")
    command = (
        "$rows=Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -match '^python(?:w)?\\.exe$' -and "
        f"$_.CommandLine -like '*{script_name}*--mode*formal-worker*'"
        " }; $rows | ForEach-Object { $_.ProcessId }"
    )
    completed = subprocess.run(
        ("powershell", "-NoProfile", "-Command", command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return tuple(int(line.strip()) for line in completed.stdout.splitlines() if line.strip().isdigit())


def _run_formal_supervisor(args: argparse.Namespace) -> dict[str, object]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    receipt = ARTIFACTS / "formal_worker_receipt.json"
    supervisor_path = ARTIFACTS / "formal_supervisor_result.json"
    reset_path = ARTIFACTS / "reset_structural_evidence.json"
    quiescence_path = ARTIFACTS / "process_quiescence.json"
    final_path = ARTIFACTS / "final_result.json"
    targets = (receipt, supervisor_path, reset_path, quiescence_path, final_path)
    _require(not any(path.exists() for path in targets), "STALE-FORMAL-TARGET", tuple(str(path) for path in targets if path.exists()))
    _require(not tuple(ARTIFACTS.glob(f"{receipt.name}.tmp.*")), "STALE-FORMAL-TEMP")

    frozen = json.loads((ARTIFACTS / "source_identity_manifest.json").read_text(encoding="utf-8"))
    current_hashes = _source_hashes()
    _require(frozen.get("pass") is True and frozen.get("hashes") == current_hashes, "PREFLIGHT-SOURCE-DRIFT", {"frozen": frozen.get("hashes"), "current": current_hashes})
    preflight = json.loads((ARTIFACTS / "preflight_result.json").read_text(encoding="utf-8"))
    _require(preflight.get("pass") is True, "PREFLIGHT-NOT-PASS", preflight)

    run_id = f"b2-t4-ep-p-20260916-formal01-{uuid.uuid4().hex}"
    command = [
        sys.executable,
        "-u",
        str(Path(__file__).resolve()),
        "--mode",
        "formal-worker",
        "--run-id",
        run_id,
        "--receipt",
        str(receipt),
    ]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    pid_active, tasklist_output = _tasklist_pid_active(process.pid)
    matching_workers = _formal_worker_processes()
    validation = _validate_receipt(
        receipt,
        expected_run_id=run_id,
        expected_pid=process.pid,
        worker_return_code=int(process.returncode),
        expected_schema=WORKER_SCHEMA,
    )
    shutdown_observed = "Simulation App Shutting Down" in (stdout + stderr)
    process_quiescence = {
        "schema_version": "b2_t4_ep_p_process_quiescence_v1",
        "worker_pid": process.pid,
        "worker_return_code": process.returncode,
        "worker_wait_completed": process.poll() is not None,
        "worker_pid_active_in_tasklist": pid_active,
        "tasklist_output": tasklist_output,
        "matching_formal_worker_pids": matching_workers,
        "shutdown_observed": shutdown_observed,
        "timed_out": timed_out,
        "pass": bool(process.poll() is not None and not pid_active and not matching_workers and not timed_out and shutdown_observed),
    }
    supervisor_pass = bool(validation["qualification_pass"] and process_quiescence["pass"])
    result = {
        "schema_version": "b2_t4_ep_p_formal_supervisor_result_v1",
        "status": "passed" if supervisor_pass else "failed",
        "classification": PASS if supervisor_pass else validation["classification"] if not validation["qualification_pass"] else "PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED",
        "run_id": run_id,
        "formal_supervisors": 1,
        "formal_workers": 1,
        "formal_retries": 0,
        "worker_pid": process.pid,
        "worker_return_code": process.returncode,
        "worker_receipt_validation": validation,
        "worker_receipt_digest": validation["receipt_file_sha256"],
        "process_quiescence": process_quiescence,
        "worker_stdout_tail": stdout[-16000:],
        "worker_stderr_tail": stderr[-16000:],
        "source_identity_manifest_sha256": _sha(ARTIFACTS / "source_identity_manifest.json"),
    }
    payload = validation.get("payload", {})
    reset_evidence = {
        "schema_version": "b2_t4_ep_p_reset_structural_evidence_v1",
        "run_id": run_id,
        "worker_pid": process.pid,
        "reset_attempted": payload.get("reset_attempted"),
        "reset_pass": payload.get("reset_pass"),
        "structure_assertions_pass": payload.get("structure_assertions_pass"),
        "observation_structure_summary": payload.get("observation_structure_summary"),
        "shared_observation_shape": payload.get("shared_observation_shape"),
        "available_actions_shape": payload.get("available_actions_shape"),
        "device": payload.get("device"),
        "num_envs": payload.get("num_envs"),
        "robot_count": payload.get("robot_count"),
        "viewpoint_count": payload.get("viewpoint_count"),
        "episode_length_s": payload.get("episode_length_s"),
        "max_episode_length": payload.get("max_episode_length"),
        "control_step_seconds": payload.get("control_step_seconds"),
        "episode_generation_summary": payload.get("episode_generation_summary"),
        "P2_initialization_summary": payload.get("P2_initialization_summary"),
        "physical_steps": payload.get("physical_steps"),
        "pass": bool(payload.get("reset_pass") is True and payload.get("structure_assertions_pass") is True),
    }
    final = {
        "schema_version": "b2_t4_ep_p_final_result_v1",
        "status": result["status"],
        "classification": result["classification"],
        "formal_supervisors": 1,
        "formal_workers": 1,
        "formal_retries": 0,
        "CUDA_readiness_probes": 1,
        "AppLauncher_lifetimes": 1 if payload.get("app_launcher_started") else 0,
        "gym_spec_pass": payload.get("gym_spec_pass"),
        "entry_point_resolution_pass": payload.get("entry_point_resolution_pass"),
        "environment_constructions": 1 if payload.get("environment_constructed") else 0,
        "initial_resets": 1 if payload.get("reset_pass") else 0,
        "structural_assertions_pass": payload.get("structure_assertions_pass"),
        "worker_receipts": 1 if validation["identity_pass"] else 0,
        "worker_receipt_pre_app_close": payload.get("receipt_written_before_app_close"),
        "worker_receipt_fsync_readback_pass": bool(payload.get("receipt_fsync_pass") and payload.get("receipt_readback_pass")),
        "environment_close_pass": payload.get("env_close_pass"),
        "SimulationApp_shutdown_observed": shutdown_observed,
        "supervisor_adjudications": 1,
        "supervisor_adjudication_pass": supervisor_pass,
        "process_quiescence_pass": process_quiescence["pass"],
        "physical_environment_steps": payload.get("physical_steps", 0),
        "persistent_learner_constructions": payload.get("learner_constructions", 0),
        "learner_updates": 0,
        "learner_mutations": payload.get("learner_mutations", 0),
        "actor_backward_steps": [payload.get("actor_backward", 0), payload.get("actor_optimizer_steps", 0)],
        "critic_backward_steps": [payload.get("critic_backward", 0), payload.get("critic_optimizer_steps", 0)],
        "ValueNorm_updates": payload.get("ValueNorm_updates", 0),
        "checkpoint_io": payload.get("checkpoint_io", 0),
        "public_activation": payload.get("public_activation", 0),
        "evaluation_playback": payload.get("evaluation_playback", 0),
        "production_files_changed": 0,
        "B2-T4-RE4_started": 0,
    }
    _durable_json(reset_path, reset_evidence)
    _durable_json(quiescence_path, process_quiescence)
    _durable_json(supervisor_path, result)
    _durable_json(final_path, final)
    _require(supervisor_pass, str(result["classification"]), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("preflight", "synthetic-worker", "formal-worker", "formal-supervisor"))
    parser.add_argument("--scenario", choices=("success", "failure", "missing", "malformed", "temp_only", "nonzero_success"))
    parser.add_argument("--run-id")
    parser.add_argument("--receipt")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    if args.mode == "synthetic-worker":
        _require(args.scenario and args.run_id and args.receipt, "SYNTHETIC-WORKER-ARGS")
        return _run_synthetic_worker(args)
    if args.mode == "formal-worker":
        _require(args.run_id and args.receipt, "FORMAL-WORKER-ARGS")
        return _run_formal_worker(args)
    if args.mode == "preflight":
        result = _run_preflight()
    else:
        result = _run_formal_supervisor(args)
    print("B2_T4_EP_P_JSON=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
