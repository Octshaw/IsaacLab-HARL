"""Pure B2-T4-EP-Q process-quiescence contract authority.

This module is intentionally independent of AppLauncher, Isaac Lab, the
environment, and learner code.  It separates a durable pre-shutdown worker
receipt from externally observed child-process termination.  Captured shutdown
text is retained as diagnostic evidence and is never a hard gate in v2.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping


CONTRACT_SCHEMA = "b2_t4_ep_q_process_quiescence_v2"
EP_P_ENVELOPE_SCHEMA = "b2_t4_ep_p_worker_receipt_envelope_v1"
EP_P_RECEIPT_SCHEMA = "b2_t4_ep_p_formal_worker_receipt_v1"
SHUTDOWN_MARKER = "Simulation App Shutting Down"
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-EP-Q-PROCESS-QUIESCENCE-CONTRACT-QUALIFIED-"
    "AWAITING-GPT-REVIEW"
)
STOP_CLASSIFICATION = "PHASE-B2-T4-EP-Q-STOP-QUIESCENCE-CONTRACT-UNRESOLVED"


def _canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def make_receipt_envelope(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    return {
        "schema_version": EP_P_ENVELOPE_SCHEMA,
        "payload_sha256": sha256_bytes(_canonical_bytes(normalized)),
        "payload": normalized,
    }


def load_receipt_envelope(path: Path) -> tuple[dict[str, object] | None, str | None]:
    if not path.is_file():
        return None, "missing receipt"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(parsed, dict):
        return None, "receipt envelope is not an object"
    return parsed, None


def _receipt_predicates(
    envelope: Mapping[str, object] | None,
    *,
    receipt_error: str | None,
    expected_run_id: str,
    expected_worker_pid: int,
) -> tuple[dict[str, bool], dict[str, object]]:
    envelope_available = envelope is not None
    present = envelope_available or (
        receipt_error is not None and receipt_error != "missing receipt"
    )
    parse_valid = envelope_available and receipt_error is None
    payload_object = envelope.get("payload") if envelope_available else None
    payload = payload_object if isinstance(payload_object, Mapping) else {}
    payload_is_mapping = isinstance(payload_object, Mapping)
    envelope_schema_valid = bool(
        envelope_available and envelope.get("schema_version") == EP_P_ENVELOPE_SCHEMA
    )
    payload_schema_valid = payload.get("schema_version") == EP_P_RECEIPT_SCHEMA
    try:
        observed_digest = sha256_bytes(_canonical_bytes(dict(payload))) if payload_is_mapping else None
    except (TypeError, ValueError):
        observed_digest = None
    digest_valid = bool(
        envelope_available
        and payload_is_mapping
        and isinstance(envelope.get("payload_sha256"), str)
        and envelope.get("payload_sha256") == observed_digest
    )
    predicates = {
        "receipt_present": present,
        "receipt_parse_valid": parse_valid,
        "receipt_payload_object": payload_is_mapping,
        "receipt_envelope_schema_valid": envelope_schema_valid,
        "receipt_payload_schema_valid": payload_schema_valid,
        "receipt_digest_valid": digest_valid,
        "run_id_valid": payload.get("run_id") == expected_run_id,
        "worker_pid_binding_valid": payload.get("worker_pid") == expected_worker_pid,
        "worker_status_success": payload.get("status") == "success",
        "reset_pass": payload.get("reset_pass") is True,
        "structure_assertions_pass": payload.get("structure_assertions_pass") is True,
        "receipt_written_before_app_close": payload.get("receipt_written_before_app_close") is True,
        "receipt_fsync_pass": payload.get("receipt_fsync_pass") is True,
        "receipt_readback_pass": payload.get("receipt_readback_pass") is True,
        "env_close_pass": payload.get("env_close_pass") is True,
        "app_close_invoked": payload.get("app_close_invoked") is True,
        "physical_steps_zero": payload.get("physical_steps") == 0,
        "learner_constructions_zero": payload.get("learner_constructions") == 0,
        "learner_mutations_zero": payload.get("learner_mutations") == 0,
    }
    identity = {
        "expected_run_id": expected_run_id,
        "observed_run_id": payload.get("run_id"),
        "expected_worker_pid": expected_worker_pid,
        "observed_worker_pid": payload.get("worker_pid"),
        "receipt_error": receipt_error,
        "expected_payload_sha256": envelope.get("payload_sha256") if envelope_available else None,
        "observed_payload_sha256": observed_digest,
    }
    return predicates, identity


def _process_predicates(process_evidence: Mapping[str, object]) -> dict[str, bool]:
    matching = process_evidence.get("matching_formal_worker_pids")
    return {
        "subprocess_wait_completed": process_evidence.get("worker_wait_completed") is True,
        "timed_out_false": process_evidence.get("timed_out") is False,
        "return_code_zero": process_evidence.get("worker_return_code") == 0,
        "worker_pid_absent": process_evidence.get("worker_pid_active") is False,
        "matching_formal_worker_pids_empty": isinstance(matching, (list, tuple)) and len(matching) == 0,
    }


_FAILURE_CODES = (
    ("receipt_present", "WORKER_RECEIPT_MISSING"),
    ("receipt_parse_valid", "WORKER_RECEIPT_MALFORMED"),
    ("receipt_payload_object", "WORKER_RECEIPT_MALFORMED"),
    ("receipt_envelope_schema_valid", "WORKER_RECEIPT_SCHEMA_INVALID"),
    ("receipt_payload_schema_valid", "WORKER_RECEIPT_SCHEMA_INVALID"),
    ("receipt_digest_valid", "WORKER_RECEIPT_DIGEST_MISMATCH"),
    ("run_id_valid", "RUN_ID_MISMATCH"),
    ("worker_pid_binding_valid", "PID_BINDING_MISMATCH"),
    ("worker_status_success", "WORKER_STATUS_NOT_SUCCESS"),
    ("reset_pass", "RESET_NOT_QUALIFIED"),
    ("structure_assertions_pass", "STRUCTURE_NOT_QUALIFIED"),
    ("receipt_written_before_app_close", "RECEIPT_NOT_PRE_APP_CLOSE"),
    ("receipt_fsync_pass", "RECEIPT_FSYNC_NOT_QUALIFIED"),
    ("receipt_readback_pass", "RECEIPT_READBACK_NOT_QUALIFIED"),
    ("env_close_pass", "ENV_CLOSE_NOT_QUALIFIED"),
    ("app_close_invoked", "APP_CLOSE_NOT_INVOKED"),
    ("physical_steps_zero", "PHYSICAL_STEPS_NONZERO"),
    ("learner_constructions_zero", "LEARNER_CONSTRUCTIONS_NONZERO"),
    ("learner_mutations_zero", "LEARNER_MUTATIONS_NONZERO"),
    ("subprocess_wait_completed", "PROCESS_WAIT_NOT_COMPLETE"),
    ("timed_out_false", "PROCESS_TIMEOUT"),
    ("return_code_zero", "PROCESS_RETURN_CODE_NONZERO"),
    ("worker_pid_absent", "WORKER_PID_STILL_ACTIVE"),
    ("matching_formal_worker_pids_empty", "MATCHING_WORKER_PROCESS_REMAINS"),
)


def reconcile_process_quiescence_v2(
    *,
    receipt_envelope: Mapping[str, object] | None,
    receipt_error: str | None,
    expected_run_id: str,
    expected_worker_pid: int,
    process_evidence: Mapping[str, object],
    captured_stdout: str = "",
    captured_stderr: str = "",
    source_contract: str = "EP-Q synthetic",
) -> dict[str, object]:
    """Evaluate the v2 contract without importing or launching runtime code."""

    receipt_predicates, receipt_identity = _receipt_predicates(
        receipt_envelope,
        receipt_error=receipt_error,
        expected_run_id=expected_run_id,
        expected_worker_pid=expected_worker_pid,
    )
    process_predicates = _process_predicates(process_evidence)
    worker_pre_shutdown_qualified = all(receipt_predicates.values())
    external_process_termination_qualified = all(process_predicates.values())
    hard_predicates = {**receipt_predicates, **process_predicates}
    passed = worker_pre_shutdown_qualified and external_process_termination_qualified
    failed_codes = [code for key, code in _FAILURE_CODES if not hard_predicates[key]]
    combined_output = captured_stdout + captured_stderr
    diagnostics = {
        "authoritative_for_process_quiescence": False,
        "shutdown_marker": SHUTDOWN_MARKER,
        "shutdown_marker_observed": SHUTDOWN_MARKER in combined_output,
        "captured_stdout_digest": sha256_bytes(captured_stdout.encode("utf-8")),
        "captured_stderr_digest": sha256_bytes(captured_stderr.encode("utf-8")),
        "captured_stdout_bytes": len(captured_stdout.encode("utf-8")),
        "captured_stderr_bytes": len(captured_stderr.encode("utf-8")),
    }
    return {
        "schema_version": CONTRACT_SCHEMA,
        "source_contract": source_contract,
        "evaluation_contract": "EP-Q v2",
        "status": "passed" if passed else "stopped",
        "classification": PASS_CLASSIFICATION if passed else STOP_CLASSIFICATION,
        "stop_reason": None if passed else failed_codes[0],
        "failure_reasons": failed_codes,
        "pass": passed,
        "hard_predicates": hard_predicates,
        "layers": {
            "A_worker_pre_shutdown_qualification": {
                "pass": worker_pre_shutdown_qualified,
                "predicates": receipt_predicates,
                "identity": receipt_identity,
            },
            "B_external_process_termination": {
                "pass": external_process_termination_qualified,
                "predicates": process_predicates,
                "worker_pid": expected_worker_pid,
                "matching_formal_worker_pids": list(
                    process_evidence.get("matching_formal_worker_pids") or []
                ),
            },
            "C_supplemental_shutdown_diagnostics": diagnostics,
        },
        "claim": (
            "formal worker process reached externally observed process-level quiescence"
            if passed
            else "process-level quiescence not established"
        ),
        "nonclaims": [
            "SimulationApp.close returned normally to Python",
            "every internal Kit shutdown callback executed",
            "captured streams contain the complete Kit shutdown lifecycle",
        ],
    }


def replay_old_ep_p_contract(
    *,
    worker_receipt_qualified: bool,
    process_evidence: Mapping[str, object],
    captured_stdout: str = "",
    captured_stderr: str = "",
) -> dict[str, object]:
    """Reproduce the frozen EP-P conjunction without reclassifying history."""

    shutdown_observed = SHUTDOWN_MARKER in (captured_stdout + captured_stderr)
    direct_process_exit_pass = bool(
        process_evidence.get("worker_wait_completed") is True
        and process_evidence.get("worker_pid_active") is False
        and not process_evidence.get("matching_formal_worker_pids")
        and process_evidence.get("timed_out") is False
    )
    process_quiescence_pass = direct_process_exit_pass and shutdown_observed
    supervisor_pass = worker_receipt_qualified and process_quiescence_pass
    return {
        "schema_version": "b2_t4_ep_p_process_quiescence_v1_replay",
        "source_contract": "EP-P historical",
        "worker_receipt_qualified": worker_receipt_qualified,
        "return_code_zero_in_receipt_qualification": process_evidence.get("worker_return_code") == 0,
        "direct_process_exit_pass": direct_process_exit_pass,
        "shutdown_marker_observed": shutdown_observed,
        "process_quiescence_pass": process_quiescence_pass,
        "supervisor_pass": supervisor_pass,
        "classification": (
            "PHASE-B2-T4-EP-P-FORMAL-EVIDENCE-PERSISTENCE-SUPERVISOR-QUALIFIED-AWAITING-GPT-REVIEW"
            if supervisor_pass
            else "PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED"
        ),
    }
