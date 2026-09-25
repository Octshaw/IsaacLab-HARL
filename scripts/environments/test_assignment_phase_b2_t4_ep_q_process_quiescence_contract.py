"""Pure/static qualification for B2-T4-EP-Q process quiescence v2."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import uuid

from _assignment_phase_b2_t4_ep_q_process_quiescence import (
    CONTRACT_SCHEMA,
    PASS_CLASSIFICATION,
    SHUTDOWN_MARKER,
    make_receipt_envelope,
    reconcile_process_quiescence_v2,
    replay_old_ep_p_contract,
    sha256_file,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260916"
EP_P_ARTIFACTS = DATE_ROOT / "b2_t4_ep_p_artifacts"
ARTIFACTS = DATE_ROOT / "b2_t4_ep_q_artifacts"
EP_P_HARNESS = HERE / "test_assignment_phase_b2_t4_ep_p_formal_evidence_persistence_supervisor.py"
HELPER = HERE / "_assignment_phase_b2_t4_ep_q_process_quiescence.py"

HISTORICAL_CLASSIFICATION = "PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED"
EXPECTED_EP_P_HASHES = {
    "formal_worker_receipt.json": "47b5a5156b95c6a829bb45d6dd844a1e281221d1aef2b15cd301b28c033f4af0",
    "formal_supervisor_result.json": "f8af60a6fe2887e8899b445b5725719f6fc723741d74a4ccc1a2429120b6fea5",
    "process_quiescence.json": "8ae58d1d0efeb74971af756a1a1433821bc5c781ae1c0a59e13db8c208d522fe",
    "reset_structural_evidence.json": "7f695e9eebc9b283cfb87c0d3a71264ba4d2b59a84b744beabf054f6182186aa",
    "final_result.json": "8e0bad06a92defb3715d9ba36b6589958c4c2a2930cb71c0db2b13d4a9b6b583",
}
EXPECTED_SOURCE_HASHES = {
    "protected_full_transaction": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "protected_real_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "scan_environment": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    "frozen_ep_p_harness": "82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6",
}
SOURCE_PATHS = {
    "protected_full_transaction": SCAN / "assignment_event_training_full_transaction.py",
    "protected_real_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "scan_environment": SCAN / "scan_mobile_manipulator_env.py",
    "frozen_ep_p_harness": EP_P_HARNESS,
    "ep_q_reconciler": HELPER,
    "ep_q_qualification": Path(__file__).resolve(),
}


def require(condition: bool, code: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-EP-Q {code}: {detail!r}")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, object]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(parsed, dict), "JSON-OBJECT", path)
    return parsed


def normalized_process(**updates: object) -> dict[str, object]:
    result: dict[str, object] = {
        "worker_wait_completed": True,
        "timed_out": False,
        "worker_return_code": 0,
        "worker_pid_active": False,
        "matching_formal_worker_pids": [],
    }
    result.update(updates)
    return result


def receipt_for(payload: dict[str, object], **updates: object) -> dict[str, object]:
    revised = copy.deepcopy(payload)
    revised.update(updates)
    return make_receipt_envelope(revised)


def run_case(
    *,
    name: str,
    receipt: dict[str, object] | None,
    receipt_error: str | None,
    expected_run_id: str,
    expected_pid: int,
    process: dict[str, object],
    marker: bool,
    expected_pass: bool,
    expected_reason: str | None = None,
    source_contract: str = "EP-Q synthetic",
) -> dict[str, object]:
    stdout = f"prefix\n{SHUTDOWN_MARKER}\nsuffix\n" if marker else ""
    result = reconcile_process_quiescence_v2(
        receipt_envelope=receipt,
        receipt_error=receipt_error,
        expected_run_id=expected_run_id,
        expected_worker_pid=expected_pid,
        process_evidence=process,
        captured_stdout=stdout,
        captured_stderr="",
        source_contract=source_contract,
    )
    require(result["pass"] is expected_pass, "CASE-RESULT", {"name": name, "result": result})
    if expected_reason is not None:
        require(result["stop_reason"] == expected_reason, "CASE-REASON", {"name": name, "result": result})
    observed_marker = result["layers"]["C_supplemental_shutdown_diagnostics"]["shutdown_marker_observed"]
    require(observed_marker is marker, "CASE-MARKER", {"name": name, "result": result})
    return {
        "name": name,
        "expected": "PASS" if expected_pass else "STOP",
        "expected_reason": expected_reason,
        "observed": "PASS" if result["pass"] else "STOP",
        "pass": result["pass"] is expected_pass,
        "result": result,
    }


def source_excerpt() -> dict[str, object]:
    lines = EP_P_HARNESS.read_text(encoding="utf-8").splitlines()
    needles = {
        "shutdown_marker": 'shutdown_observed = "Simulation App Shutting Down" in (stdout + stderr)',
        "quiescence_pass": '"pass": bool(process.poll() is not None and not pid_active and not matching_workers and not timed_out and shutdown_observed),',
        "supervisor_pass": 'supervisor_pass = bool(validation["qualification_pass"] and process_quiescence["pass"])',
    }
    located: dict[str, object] = {}
    for name, needle in needles.items():
        matches = [index for index, line in enumerate(lines, 1) if line.strip() == needle]
        require(len(matches) == 1, "OLD-PREDICATE-SOURCE", {"needle": needle, "matches": matches})
        located[name] = {"line": matches[0], "source": needle}
    return located


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    expected_outputs = (
        "old_quiescence_contract.json",
        "process_quiescence_contract_v2.json",
        "positive_matrix.json",
        "negative_matrix.json",
        "marker_nonauthority_tests.json",
        "ep_p_artifact_identity.json",
        "ep_p_formal_quiescence_replay.json",
        "source_identity_manifest.json",
        "final_result.json",
    )
    require(not any(ARTIFACTS.glob("*.tmp.*")), "STALE-TEMP")

    artifact_hashes = {name: sha256_file(EP_P_ARTIFACTS / name) for name in EXPECTED_EP_P_HASHES}
    artifact_identity_pass = artifact_hashes == EXPECTED_EP_P_HASHES
    require(artifact_identity_pass, "HISTORICAL-ARTIFACT-DRIFT", artifact_hashes)
    ep_p_identity = {
        "schema_version": "b2_t4_ep_q_ep_p_artifact_identity_v1",
        "expected": EXPECTED_EP_P_HASHES,
        "observed": artifact_hashes,
        "pass": artifact_identity_pass,
        "historical_classification_retained": HISTORICAL_CLASSIFICATION,
    }
    write_json(ARTIFACTS / "ep_p_artifact_identity.json", ep_p_identity)

    source_hashes = {name: sha256_file(path) for name, path in SOURCE_PATHS.items()}
    protected_pass = all(source_hashes[name] == digest for name, digest in EXPECTED_SOURCE_HASHES.items())
    require(protected_pass, "PROTECTED-SOURCE-MODIFIED", source_hashes)
    source_identity = {
        "schema_version": "b2_t4_ep_q_source_identity_manifest_v1",
        "expected_protected_hashes": EXPECTED_SOURCE_HASHES,
        "observed_hashes": source_hashes,
        "protected_sources_pass": protected_pass,
        "production_source_modifications": 0,
        "historical_ep_p_harness_modifications": 0,
        "pass": protected_pass,
    }
    write_json(ARTIFACTS / "source_identity_manifest.json", source_identity)

    old_source = source_excerpt()
    old_contract = {
        "schema_version": "b2_t4_ep_q_old_quiescence_contract_audit_v1",
        "source_file": str(EP_P_HARNESS),
        "source_sha256": source_hashes["frozen_ep_p_harness"],
        "source_expressions": old_source,
        "receipt_predicate": "validation['qualification_pass']",
        "receipt_includes_return_code_zero": True,
        "process_predicates": {
            "wait_completed": "process.poll() is not None",
            "timeout": "not timed_out",
            "worker_pid": "not pid_active",
            "matching_worker_process": "not matching_workers",
            "shutdown_marker": "shutdown_observed",
        },
        "exact_composition": "validation['qualification_pass'] AND (wait_completed AND worker_pid_absent AND matching_workers_empty AND NOT timed_out AND shutdown_marker_observed)",
        "pass": True,
    }
    write_json(ARTIFACTS / "old_quiescence_contract.json", old_contract)

    contract = {
        "schema_version": CONTRACT_SCHEMA,
        "precedence": "direct process state > captured log text for worker existence",
        "hard_layers": ["A_worker_pre_shutdown_qualification", "B_external_process_termination"],
        "pass_expression": "Layer A PASS AND Layer B PASS",
        "layer_A_required": [
            "receipt schemas/digest valid",
            "run_id and worker PID binding valid",
            "worker status success",
            "reset and structural assertions pass",
            "receipt pre-App-close, fsync, and readback pass",
            "env.close pass and app_close_invoked true",
            "physical steps, learner constructions, and learner mutations are zero",
        ],
        "layer_B_required": [
            "subprocess wait completed",
            "timed_out false",
            "return code zero",
            "original worker PID absent",
            "matching formal worker PID set empty",
        ],
        "layer_C": {
            "role": "supplemental diagnostic only",
            "fields": ["shutdown_marker_observed", "captured_stdout_digest", "captured_stderr_digest"],
            "hard_gate": False,
        },
        "claim": "formal worker process reached externally observed process-level quiescence",
        "nonclaims": [
            "SimulationApp.close returned normally to Python",
            "every internal Kit shutdown callback executed",
            "captured streams contain the complete Kit shutdown lifecycle",
        ],
        "pass": True,
    }
    write_json(ARTIFACTS / "process_quiescence_contract_v2.json", contract)

    historical_receipt = read_json(EP_P_ARTIFACTS / "formal_worker_receipt.json")
    historical_payload = copy.deepcopy(historical_receipt["payload"])
    run_id = "b2-t4-ep-q-synthetic"
    worker_pid = 4242
    base_receipt = receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid)
    base_process = normalized_process()

    positive_specs = (
        ("marker_present_direct_complete", True),
        ("marker_absent_direct_complete", False),
        ("empty_captured_streams_direct_complete", False),
    )
    positives = [
        run_case(
            name=name,
            receipt=base_receipt,
            receipt_error=None,
            expected_run_id=run_id,
            expected_pid=worker_pid,
            process=base_process,
            marker=marker,
            expected_pass=True,
        )
        for name, marker in positive_specs
    ]
    positive_matrix = {
        "schema_version": "b2_t4_ep_q_positive_matrix_v1",
        "case_count": len(positives),
        "cases": positives,
        "pass": all(case["pass"] for case in positives),
    }
    write_json(ARTIFACTS / "positive_matrix.json", positive_matrix)

    invalid_json_error = "JSONDecodeError: synthetic malformed receipt"
    negative_specs = (
        ("marker_present_worker_pid_active", base_receipt, None, run_id, worker_pid, normalized_process(worker_pid_active=True), "WORKER_PID_STILL_ACTIVE"),
        ("marker_present_matching_worker_remains", base_receipt, None, run_id, worker_pid, normalized_process(matching_formal_worker_pids=[5151]), "MATCHING_WORKER_PROCESS_REMAINS"),
        ("marker_present_wait_incomplete", base_receipt, None, run_id, worker_pid, normalized_process(worker_wait_completed=False), "PROCESS_WAIT_NOT_COMPLETE"),
        ("marker_present_timeout", base_receipt, None, run_id, worker_pid, normalized_process(timed_out=True), "PROCESS_TIMEOUT"),
        ("marker_present_nonzero_return", base_receipt, None, run_id, worker_pid, normalized_process(worker_return_code=17), "PROCESS_RETURN_CODE_NONZERO"),
        ("process_gone_receipt_missing", None, "missing receipt", run_id, worker_pid, base_process, "WORKER_RECEIPT_MISSING"),
        ("process_gone_receipt_malformed", None, invalid_json_error, run_id, worker_pid, base_process, "WORKER_RECEIPT_MALFORMED"),
        ("process_gone_wrong_run_id", receipt_for(historical_payload, run_id="wrong-run", worker_pid=worker_pid), None, run_id, worker_pid, base_process, "RUN_ID_MISMATCH"),
        ("process_gone_wrong_pid_binding", receipt_for(historical_payload, run_id=run_id, worker_pid=9999), None, run_id, worker_pid, base_process, "PID_BINDING_MISMATCH"),
        ("process_gone_env_close_false", receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid, env_close_pass=False), None, run_id, worker_pid, base_process, "ENV_CLOSE_NOT_QUALIFIED"),
        ("process_gone_app_close_not_invoked", receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid, app_close_invoked=False), None, run_id, worker_pid, base_process, "APP_CLOSE_NOT_INVOKED"),
        ("process_gone_reset_false", receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid, reset_pass=False), None, run_id, worker_pid, base_process, "RESET_NOT_QUALIFIED"),
        ("process_gone_structure_false", receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid, structure_assertions_pass=False), None, run_id, worker_pid, base_process, "STRUCTURE_NOT_QUALIFIED"),
        ("process_gone_learner_mutation", receipt_for(historical_payload, run_id=run_id, worker_pid=worker_pid, learner_mutations=1), None, run_id, worker_pid, base_process, "LEARNER_MUTATIONS_NONZERO"),
        ("stale_receipt_another_attempt", receipt_for(historical_payload, run_id="stale-attempt", worker_pid=worker_pid), None, run_id, worker_pid, base_process, "RUN_ID_MISMATCH"),
    )
    negatives = [
        run_case(
            name=name,
            receipt=receipt,
            receipt_error=receipt_error,
            expected_run_id=expected_run,
            expected_pid=expected_pid,
            process=process,
            marker=True,
            expected_pass=False,
            expected_reason=reason,
        )
        for name, receipt, receipt_error, expected_run, expected_pid, process, reason in negative_specs
    ]
    unexpected_negative_passes = sum(1 for case in negatives if case["result"]["pass"])
    require(unexpected_negative_passes == 0, "UNEXPECTED-NEGATIVE-PASS", negatives)
    negative_matrix = {
        "schema_version": "b2_t4_ep_q_negative_matrix_v1",
        "case_count": len(negatives),
        "unexpected_negative_passes": unexpected_negative_passes,
        "cases": negatives,
        "pass": all(case["pass"] for case in negatives) and unexpected_negative_passes == 0,
    }
    write_json(ARTIFACTS / "negative_matrix.json", negative_matrix)

    marker_nonauthority = {
        "schema_version": "b2_t4_ep_q_marker_nonauthority_v1",
        "marker_present_process_alive": negatives[0],
        "marker_absent_process_terminated": positives[1],
        "marker_is_hard_gate": False,
        "pass": negatives[0]["result"]["pass"] is False and positives[1]["result"]["pass"] is True,
    }
    write_json(ARTIFACTS / "marker_nonauthority_tests.json", marker_nonauthority)

    supervisor = read_json(EP_P_ARTIFACTS / "formal_supervisor_result.json")
    old_quiescence = read_json(EP_P_ARTIFACTS / "process_quiescence.json")
    historical_final = read_json(EP_P_ARTIFACTS / "final_result.json")
    require(supervisor["classification"] == HISTORICAL_CLASSIFICATION, "EP-P-SUPERVISOR-CLASSIFICATION", supervisor["classification"])
    require(historical_final["classification"] == HISTORICAL_CLASSIFICATION, "EP-P-FINAL-CLASSIFICATION", historical_final["classification"])
    require(old_quiescence["pass"] is False, "EP-P-OLD-PASS-DRIFT", old_quiescence)
    historical_process = normalized_process(
        worker_wait_completed=old_quiescence["worker_wait_completed"],
        timed_out=old_quiescence["timed_out"],
        worker_return_code=old_quiescence["worker_return_code"],
        worker_pid_active=old_quiescence["worker_pid_active_in_tasklist"],
        matching_formal_worker_pids=old_quiescence["matching_formal_worker_pids"],
    )
    stdout = str(supervisor.get("worker_stdout_tail") or "")
    stderr = str(supervisor.get("worker_stderr_tail") or "")
    old_replay = replay_old_ep_p_contract(
        worker_receipt_qualified=supervisor["worker_receipt_validation"]["qualification_pass"] is True,
        process_evidence=historical_process,
        captured_stdout=stdout,
        captured_stderr=stderr,
    )
    v2_replay = reconcile_process_quiescence_v2(
        receipt_envelope=historical_receipt,
        receipt_error=None,
        expected_run_id=str(supervisor["run_id"]),
        expected_worker_pid=int(supervisor["worker_pid"]),
        process_evidence=historical_process,
        captured_stdout=stdout,
        captured_stderr=stderr,
        source_contract="EP-P historical",
    )
    require(old_replay["supervisor_pass"] is False, "OLD-REPLAY-DID-NOT-STOP", old_replay)
    require(old_replay["classification"] == HISTORICAL_CLASSIFICATION, "OLD-REPLAY-CLASSIFICATION", old_replay)
    require(v2_replay["pass"] is True, "V2-REPLAY-DID-NOT-PASS", v2_replay)
    require(v2_replay["layers"]["C_supplemental_shutdown_diagnostics"]["shutdown_marker_observed"] is False, "V2-REPLAY-MARKER", v2_replay)
    replay = {
        "schema_version": "b2_t4_ep_q_ep_p_formal_quiescence_replay_v1",
        "source_contract": "EP-P historical",
        "evaluation_contract": "EP-Q v2",
        "artifact_identity_pass": artifact_identity_pass,
        "historical_classification_before": HISTORICAL_CLASSIFICATION,
        "historical_classification_after": HISTORICAL_CLASSIFICATION,
        "historical_reclassification": False,
        "old_contract_replay": old_replay,
        "v2_contract_replay": v2_replay,
        "pass": old_replay["supervisor_pass"] is False and v2_replay["pass"] is True,
    }
    write_json(ARTIFACTS / "ep_p_formal_quiescence_replay.json", replay)

    canonical_reconciler_runs = len(positives) + len(negatives) + 1
    all_pass = bool(
        artifact_identity_pass
        and protected_pass
        and positive_matrix["pass"]
        and negative_matrix["pass"]
        and marker_nonauthority["pass"]
        and replay["pass"]
    )
    final = {
        "schema_version": "b2_t4_ep_q_final_result_v1",
        "status": "passed" if all_pass else "stopped",
        "classification": PASS_CLASSIFICATION if all_pass else "PHASE-B2-T4-EP-Q-STOP-QUIESCENCE-CONTRACT-UNRESOLVED",
        "historical_ep_p_classification": HISTORICAL_CLASSIFICATION,
        "historical_ep_p_reclassified": False,
        "old_contract_replay": "STOP reproduced" if old_replay["supervisor_pass"] is False else "unexpected PASS",
        "v2_contract_replay": "PASS" if v2_replay["pass"] else "STOP",
        "pure_static_python_invocations": 3,
        "canonical_reconciler_qualification_runs": canonical_reconciler_runs,
        "synthetic_positive_cases": len(positives),
        "synthetic_negative_cases": len(negatives),
        "unexpected_negative_passes": unexpected_negative_passes,
        "immutable_ep_p_retrospective_replays": 2,
        "AppLauncher_lifetimes": 0,
        "real_environment_constructions": 0,
        "environment_resets": 0,
        "physical_environment_steps": 0,
        "learner_constructions": 0,
        "learner_mutations": 0,
        "actor_backward_steps": [0, 0],
        "critic_backward_steps": [0, 0],
        "ValueNorm_updates": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
        "production_source_modifications": 0,
        "historical_ep_p_harness_modifications": 0,
        "B2-T4-RE4_started": 0,
        "git_add_commit_push": [0, 0, 0],
        "artifact_files": list(expected_outputs),
        "pass": all_pass,
    }
    write_json(ARTIFACTS / "final_result.json", final)
    require(all_pass, "FINAL-QUALIFICATION", final)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
