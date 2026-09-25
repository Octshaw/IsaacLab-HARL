"""B2-T4-PPQ offline candidate postprocess; no runtime or learner imports.

All authorities are explicit arguments. This module is a candidate pending GPT
review, and its success receipts describe hypothetical PPQ replay only.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "b2_t4_ppq_formal_success_receipt_v1"
W2E_VERSION = "b2_t4_w2e_multi_update_completion_v2"
W2E_SHA = "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0"
W2I_SHA = "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b"
PW_SHA = "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b"
PW_SCHEMA = "b2_t4_pw_immutable_progress_v1"
SUCCESS_CLASSIFICATION = "PHASE-B2-T4-PPQ-FORMAL-POSTPROCESS-SUCCESS-RECEIPT-PATH-QUALIFIED-AWAITING-GPT-REVIEW"
WITNESS_FILES = {
    "W1": "W1_cross_update_ownership.json",
    "W2E": "W2_multi_update_completion_v2.json",
    "W3": "W3_real_zero_dvm_actor.json",
    "W4": "W4_real_nonterminal_bootstrap.json",
    "W5": "W5_normal_horizon_terminal_autoreset.json",
    "W6": "W6_post_autoreset_training.json",
    "W7": "W7_runtime_p2_immutability.json",
}


class PPQStop(RuntimeError):
    """A missing or inconsistent mandatory postprocess authority."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise PPQStop(reason)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def atomic_persist(path: Path, payload: Mapping[str, Any]) -> str:
    """Explicit PPQ-only durable writer; never targets historical evidence."""
    encoded = canonical(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".ppq-tmp")
    require(not path.exists() and not temporary.exists(), "DESTINATION-ALREADY-EXISTS")
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    require(path.read_bytes() == encoded, "PERSIST-READBACK-MISMATCH")
    return hashlib.sha256(encoded).hexdigest()


def readback(path: Path) -> tuple[dict[str, Any], str]:
    encoded = path.read_bytes()
    return json.loads(encoded), hashlib.sha256(encoded).hexdigest()


def _is_int(value: object) -> bool:
    return type(value) is int


def _finite(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return True


REQUIRED_TYPES: dict[str, type] = {
    "schema_version": str, "status": str, "classification": str,
    "source_phase": str, "historical_source_status": str,
    "w2e_contract_version": str, "w2e_selector_sha256": str,
    "w2i_binding_manifest_sha256": str, "pw_schema_version": str,
    "pw_helper_sha256": str, "run_id": str,
    "physical_transitions": int, "production_s10": int,
    "transaction_ledger_count": int, "bridge_count": int,
    "tx161_started": bool, "terminal_autoreset_count": int,
    "post_autoreset_learned_transaction": bool,
    "task_completed_count": int, "coverage_max": int,
    "pw_critic_expected": int, "pw_critic_actual": int,
    "pw_actor_factor_expected": int, "pw_actor_factor_actual": int,
    "pw_missing": int, "pw_duplicate": int, "pw_order_fault": int,
    "pw_digest_fault": int, "pw_temp_residue": int,
    "W1_status": str, "W2E_status": str,
    "w2e_candidate_count": int, "w2e_valid_count": int,
    "w2_env": int, "w2_robot": int, "w2_task": int,
    "w2_claim_tx": int, "w2_claim_step": int,
    "w2_completion_tx": int, "w2_completion_step": int,
    "w2_reopen_tx": int, "w2_reopen_step": int,
    "W3_status": str, "W4_status": str, "W5_status": str,
    "W6_status": str, "W7_status": str, "W7_equal": int,
    "W7_required": int, "actor_backward": int, "actor_step": int,
    "critic_backward": int, "critic_step": int,
    "valid_nonzero_update": int, "valid_zero_effective_update": int,
    "valuenorm_update": int, "event_returns": int,
    "stock_compute_returns": int, "actor_adam_continuity": bool,
    "critic_adam_continuity": bool, "valuenorm_continuity": bool,
    "numerical_health": bool, "actor_plan_exact": bool,
    "factor_audit_pass": bool, "critic_plan_exact": bool,
    "partial_update": bool, "route_poisoned": bool,
}


def schema_document() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "required_fields": {key: typ.__name__ for key, typ in REQUIRED_TYPES.items()},
        "unknown_fields": "REJECT",
        "exact_counts": {"physical_transitions": 320, "production_s10": 160,
                         "transaction_ledger_count": 160, "bridge_count": 159,
                         "pw_critic_expected": 6560, "pw_actor_factor_expected": 640,
                         "W7_equal": 160, "W7_required": 160},
        "route_health": {"partial_update": False, "route_poisoned": False},
        "identity": {"w2e_contract_version": W2E_VERSION,
                     "w2e_selector_sha256": W2E_SHA,
                     "w2i_binding_manifest_sha256": W2I_SHA,
                     "pw_helper_sha256": PW_SHA, "pw_schema_version": PW_SCHEMA},
    }


def validate_success(payload: Mapping[str, Any]) -> None:
    require(type(payload) is dict, "SCHEMA-NOT-OBJECT")
    require(set(payload) == set(REQUIRED_TYPES), "SCHEMA-FIELDS-MISSING-OR-UNKNOWN")
    for key, typ in REQUIRED_TYPES.items():
        require(type(payload[key]) is typ, f"SCHEMA-TYPE-{key}")
    require(_finite(payload), "SCHEMA-NONFINITE")
    require(payload["schema_version"] == SCHEMA_VERSION, "SCHEMA-VERSION")
    require(payload["status"] == "success" and payload["classification"] == SUCCESS_CLASSIFICATION,
            "SCHEMA-SUCCESS-STATUS")
    require(payload["source_phase"] == "B2-T4-RE6-R1" and payload["historical_source_status"] == "STOP-POISONED",
            "HISTORICAL-STATUS-CONTRADICTION")
    for key, value in schema_document()["identity"].items():
        require(payload[key] == value, f"IDENTITY-{key}")
    require(len(payload["run_id"]) > 0, "RUN-ID")
    for key, value in schema_document()["exact_counts"].items():
        require(payload[key] == value, f"COUNT-{key}")
    require(payload["tx161_started"] is False and payload["terminal_autoreset_count"] == 2,
            "CAMPAIGN-TERMINAL-OR-TX161")
    require(payload["post_autoreset_learned_transaction"] is True,
            "POST-AUTORESET-MISSING")
    require(payload["task_completed_count"] == 22 and payload["coverage_max"] == 11,
            "TASK-PROGRESS")
    require(payload["pw_critic_actual"] == payload["pw_critic_expected"] and
            payload["pw_actor_factor_actual"] == payload["pw_actor_factor_expected"],
            "PW-COUNT")
    require(all(payload[key] == 0 for key in
                ("pw_missing", "pw_duplicate", "pw_order_fault", "pw_digest_fault", "pw_temp_residue")),
            "PW-FAULT")
    require(all(payload[f"{key}_status"] == "PASS" for key in WITNESS_FILES), "WITNESS-STATUS")
    require(payload["w2e_candidate_count"] == 29 and payload["w2e_valid_count"] == 12,
            "W2E-COUNTS")
    require(tuple(payload[key] for key in ("w2_env", "w2_robot", "w2_task", "w2_claim_tx",
                                           "w2_claim_step", "w2_completion_tx", "w2_completion_step",
                                           "w2_reopen_tx", "w2_reopen_step")) ==
            (1, 1, 10, 12, 23, 15, 30, 16, 31), "W2E-SELECTED-IDENTITY")
    require(payload["actor_backward"] == payload["actor_step"] == 165,
            "ACTOR-PLAN")
    require(payload["critic_backward"] == payload["critic_step"] == 1600,
            "CRITIC-PLAN")
    require(payload["valid_nonzero_update"] == 1576 and
            payload["valid_zero_effective_update"] == 24 and
            payload["valid_nonzero_update"] + payload["valid_zero_effective_update"] == payload["critic_step"],
            "CRITIC-CLASSIFICATIONS")
    require(payload["valuenorm_update"] == 1600 and payload["event_returns"] == 160 and
            payload["stock_compute_returns"] == 0, "RETURNS-VALUENORM")
    require(all(payload[key] is True for key in
                ("actor_adam_continuity", "critic_adam_continuity", "valuenorm_continuity",
                 "numerical_health", "actor_plan_exact", "factor_audit_pass", "critic_plan_exact")),
            "LEARNER-CONTINUITY")
    require(payload["partial_update"] is False and payload["route_poisoned"] is False,
            "POISONED-SUCCESS-CONTRADICTION")


def _selected_tuple(selected: Mapping[str, Any]) -> tuple[int, ...]:
    return tuple(int(selected[key]) for key in
                 ("env_id", "robot_id", "task_id", "claim_tx", "claim_physical_step",
                  "completion_tx", "completion_physical_step", "reopen_tx", "reopen_physical_step"))


def build_success_payload(
    evidence: Mapping[str, Any], *, w2e_selector: Callable[[Mapping[str, Any]], dict[str, Any]],
    pw_reconcile: Callable[[], Mapping[str, Any]], identity: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Re-adjudicate real evidence; never use a hidden engine dictionary."""
    require(callable(w2e_selector) and callable(pw_reconcile), "MISSING-DEPENDENCY")
    require("engine" not in evidence and "_base_atomic_json" not in evidence and
            not evidence.get("hidden_engine_dependency", False), "HIDDEN-ENGINE-DEPENDENCY")
    trace: list[str] = []
    for key, expected in (("w2e_selector_sha256", W2E_SHA),
                          ("w2i_binding_manifest_sha256", W2I_SHA),
                          ("pw_helper_sha256", PW_SHA)):
        require(identity.get(key) == expected, f"IDENTITY-{key}")
    trace.append("01_source_identity")
    final = evidence["final"]
    counts = final["exact_execution_counts"]
    tx = evidence["transactions"]
    bridges = evidence["bridges"]
    require(len(tx) == counts["successful_full_transactions"] == 160 and
            all(row["transaction_index"] == index for index, row in enumerate(tx, 1)) and
            all(row["s7_s8_s9_s10"] == [True] * 4 for row in tx), "TRANSACTION-COUNT-OR-ORDER")
    trace.append("02_transaction_reconciliation")
    require(len(bridges) == counts["s10_to_next_s0_bridges"] == 159 and
            all(row["bridge_index"] == index and row["pass"] is True for index, row in enumerate(bridges, 1)),
            "BRIDGE-COUNT-OR-ORDER")
    trace.append("03_bridge_reconciliation")
    require(counts["real_rollout_steps"] == 320 and counts["s10_pass"] == 160 and
            counts["transaction_161_started"] == 0 and counts["terminal_autoreset_events"] == 2,
            "CAMPAIGN-COUNT")
    pw = dict(pw_reconcile())
    require(pw.get("schema_version") == "b2_t4_re6_r1_pw_campaign_reconciliation_v1" and
            pw.get("critic_records") == 6560 and pw.get("actor_factor_records") == 640 and
            pw.get("transactions") == 160 and pw.get("pass") is True and
            all(pw.get(key) == 0 for key in
                ("missing", "duplicate", "out_of_order", "digest_mismatch", "temp_residue")),
            "PW-CAMPAIGN")
    trace.append("04_pw_campaign_reconciliation")
    witnesses = evidence["witnesses"]
    require(witnesses["W1"]["pass"] is True and evidence["actor_reconciliation_pass"] is True,
            "W1-OWNERSHIP-OR-ACTOR-EVIDENCE")
    trace.append("05_W1")
    w2 = w2e_selector(evidence["w2e_input"])
    require(w2.get("schema_version") == W2E_VERSION and w2.get("pass") is True and
            w2.get("candidate_count") == 29 and w2.get("valid_count") == 12 and
            isinstance(w2.get("selected"), dict), "W2E-SELECTOR")
    require(w2 == evidence["retained_w2e_inventory"], "W2E-INVENTORY-DRIFT")
    require(_selected_tuple(w2["selected"]) == _selected_tuple(evidence["retained_selected"]),
            "W2E-SELECTED-DRIFT")
    trace.append("06_W2E_selector")
    require(witnesses["W2E"]["pass"] is True and
            _selected_tuple(witnesses["W2E"]["selected"]) == _selected_tuple(w2["selected"]),
            "W2-WITNESS-INCONSISTENT")
    trace.append("07_W2")
    for name in ("W3", "W4", "W5", "W6", "W7"):
        require(witnesses[name]["pass"] is True, f"{name}-FAIL")
        if name == "W5":
            require(witnesses[name]["reason_counts"]["TIME_LIMIT"] == 2 and
                    witnesses[name]["transaction_index"] == 150, "W5-TERMINAL-AUTORESET")
        if name == "W6":
            require(witnesses[name]["post_autoreset_transaction"] == 151 and
                    witnesses[name]["fresh_rollout_and_update"] is True, "W6-POST-AUTORESET")
        if name == "W7":
            require(witnesses[name]["equal"] == witnesses[name]["required"] == 160 and
                    all(row["equal"] is True for row in evidence["immutability"]), "W7-COUNT")
        trace.append(f"{8 + int(name[1]) - 3:02d}_{name}")
    require(sum(sum(row["actor_backward_by_actor"]) for row in tx) == 165 and
            sum(sum(row["actor_optimizer_step_by_actor"]) for row in tx) == 165 and
            counts["actor_backward_total"] == counts["actor_optimizer_step_total"] == 165 and
            evidence["actor_plan_exact"] is True, "ACTOR-PLAN")
    trace.append("13_actor_plan")
    require(evidence["factor_audit_pass"] is True, "FACTOR-AUDIT")
    trace.append("14_factor")
    require(sum(row["critic_backward"] for row in tx) == 1600 and
            sum(row["critic_optimizer_step"] for row in tx) == 1600 and
            counts["critic_backward_total"] == counts["critic_optimizer_step_total"] == 1600 and
            sum(row["valid_nonzero"] for row in tx) == 1576 and
            sum(row["valid_zero_effective"] for row in tx) == 24 and
            evidence["critic_plan_exact"] is True, "CRITIC-PLAN-OR-CLASSES")
    trace.append("15_critic_plan_classes")
    require(evidence["actor_adam_continuity"] is True and
            evidence["critic_adam_continuity"] is True, "ADAM-CONTINUITY")
    trace.append("16_Adam_continuity")
    require(sum(row["valuenorm_update"] for row in tx) == 1600 and
            counts["valuenorm_update_total"] == 1600 and
            evidence["valuenorm_continuity"] is True, "VALUENORM-CONTINUITY")
    trace.append("17_ValueNorm_continuity")
    require(all(row["finite"] is True for row in tx) and
            evidence["numerical_health"] is True, "NUMERICAL-HEALTH")
    trace.append("18_numerical_health")
    task_progress = final["primary_witnesses"]["task_progress_gate"]
    selected = w2["selected"]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": "success", "classification": SUCCESS_CLASSIFICATION,
        "source_phase": "B2-T4-RE6-R1", "historical_source_status": "STOP-POISONED",
        "w2e_contract_version": W2E_VERSION, "w2e_selector_sha256": identity["w2e_selector_sha256"],
        "w2i_binding_manifest_sha256": identity["w2i_binding_manifest_sha256"],
        "pw_schema_version": PW_SCHEMA, "pw_helper_sha256": identity["pw_helper_sha256"],
        "run_id": evidence["run_id"],
        "physical_transitions": counts["real_rollout_steps"], "production_s10": counts["s10_pass"],
        "transaction_ledger_count": len(tx), "bridge_count": len(bridges),
        "tx161_started": False, "terminal_autoreset_count": counts["terminal_autoreset_events"],
        "post_autoreset_learned_transaction": True,
        "task_completed_count": task_progress["task_completed_events"],
        "coverage_max": task_progress["coverage_max"],
        "pw_critic_expected": 6560, "pw_critic_actual": pw["critic_records"],
        "pw_actor_factor_expected": 640, "pw_actor_factor_actual": pw["actor_factor_records"],
        "pw_missing": pw["missing"], "pw_duplicate": pw["duplicate"],
        "pw_order_fault": pw["out_of_order"], "pw_digest_fault": pw["digest_mismatch"],
        "pw_temp_residue": pw["temp_residue"],
        **{f"{key}_status": "PASS" for key in WITNESS_FILES},
        "w2e_candidate_count": w2["candidate_count"], "w2e_valid_count": w2["valid_count"],
        "w2_env": selected["env_id"], "w2_robot": selected["robot_id"],
        "w2_task": selected["task_id"], "w2_claim_tx": selected["claim_tx"],
        "w2_claim_step": selected["claim_physical_step"],
        "w2_completion_tx": selected["completion_tx"],
        "w2_completion_step": selected["completion_physical_step"],
        "w2_reopen_tx": selected["reopen_tx"], "w2_reopen_step": selected["reopen_physical_step"],
        "W7_equal": 160, "W7_required": 160,
        "actor_backward": counts["actor_backward_total"],
        "actor_step": counts["actor_optimizer_step_total"],
        "critic_backward": counts["critic_backward_total"],
        "critic_step": counts["critic_optimizer_step_total"],
        "valid_nonzero_update": counts["valid_nonzero_update"],
        "valid_zero_effective_update": counts["valid_zero_effective_update"],
        "valuenorm_update": counts["valuenorm_update_total"],
        "event_returns": counts["event_return_computations"],
        "stock_compute_returns": counts["stock_compute_returns"],
        "actor_adam_continuity": True, "critic_adam_continuity": True,
        "valuenorm_continuity": True, "numerical_health": True,
        "actor_plan_exact": True, "factor_audit_pass": True, "critic_plan_exact": True,
        # These flags apply only to the hypothetical PPQ success candidate.
        "partial_update": False, "route_poisoned": False,
    }
    trace.append("19_success_payload_constructed")
    return payload, w2, trace


def publish_witnesses(*, validated: bool, receipt_digest: str, witnesses: Mapping[str, Any],
                      output_dir: Path, persist: Callable[[Path, Mapping[str, Any]], str],
                      provisional_digests: Mapping[str, str]) -> list[str]:
    require(validated and len(receipt_digest) == 64, "PREMATURE-SUCCESS-PUBLICATION")
    require(set(witnesses) == set(WITNESS_FILES) == set(provisional_digests), "WITNESS-SET")
    require(all(digest(witnesses[key]) == provisional_digests[key] for key in WITNESS_FILES),
            "STALE-PROVISIONAL-WITNESS")
    published = []
    for key, filename in WITNESS_FILES.items():
        persist(output_dir / filename, witnesses[key])
        published.append(filename)
    return published


def finalize_campaign(
    evidence: Mapping[str, Any], *, w2e_selector: Callable[[Mapping[str, Any]], dict[str, Any]],
    pw_reconcile: Callable[[], Mapping[str, Any]], identity: Mapping[str, str],
    persistence_writer: Callable[[Path, Mapping[str, Any]], str] | None,
    receipt_reader: Callable[[Path], tuple[dict[str, Any], str]] | None,
    output_dir: Path, payload_mutator: Callable[[dict[str, Any]], None] | None = None,
    readback_validator: Callable[[dict[str, Any], str], None] | None = None,
    before_publication: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    require(callable(persistence_writer) and callable(receipt_reader), "MISSING-PERSISTENCE-DEPENDENCY")
    payload, w2, trace = build_success_payload(evidence, w2e_selector=w2e_selector,
                                               pw_reconcile=pw_reconcile, identity=identity)
    if payload_mutator is not None:
        payload_mutator(payload)
    validate_success(payload)
    trace.append("20_schema_validation")
    provisional = {key: (w2 if key == "W2E" else evidence["witnesses"][key])
                   for key in WITNESS_FILES}
    provisional_digests = {key: digest(value) for key, value in provisional.items()}
    if before_publication is not None:
        before_publication(provisional)
    receipt_path = output_dir / "candidate_success_receipt.json"
    expected_digest = persistence_writer(receipt_path, payload)
    trace.append("21_durable_candidate_receipt")
    observed_payload, observed_digest = receipt_reader(receipt_path)
    trace.append("22_receipt_readback")
    require(observed_payload == payload and observed_digest == expected_digest and
            observed_digest == digest(payload), "RECEIPT-READBACK-OR-DIGEST")
    if readback_validator is not None:
        readback_validator(observed_payload, observed_digest)
    validate_success(observed_payload)
    trace.append("23_receipt_digest_validated")
    published = publish_witnesses(validated=True, receipt_digest=observed_digest,
                                  witnesses=provisional, output_dir=output_dir,
                                  persist=persistence_writer, provisional_digests=provisional_digests)
    trace.append("24_canonical_witness_publication")
    return {"pass": True, "receipt": payload, "receipt_sha256": observed_digest,
            "publication": published, "trace": trace, "w2e": {
                "candidate_count": w2["candidate_count"], "valid_count": w2["valid_count"],
                "selected": w2["selected"]}}


def failure_receipt(*, failure_stage: str, exception: BaseException, completed_transactions: int,
                    ledger_count: int, bridge_count: int, witness_status: Mapping[str, str],
                    w2e_counts: Mapping[str, int] | None, pw_state: Mapping[str, Any] | None,
                    mutation_occurred: bool) -> dict[str, Any]:
    require(bool(failure_stage) and type(completed_transactions) is int and
            type(ledger_count) is int and type(bridge_count) is int,
            "FAILURE-RECEIPT-INPUT")
    require(set(witness_status) == set(WITNESS_FILES), "FAILURE-WITNESS-STATUS")
    return {"schema_version": "b2_t4_ppq_formal_failure_receipt_v1", "status": "failure",
            "failure_stage": failure_stage, "exception_type": type(exception).__name__,
            "exception_message": str(exception), "completed_transactions": completed_transactions,
            "ledger_count": ledger_count, "bridge_count": bridge_count,
            "witness_status": dict(witness_status), "w2e_counts": dict(w2e_counts or {}),
            "pw_state": dict(pw_state or {}), "partial_update": mutation_occurred,
            "route_poisoned": mutation_occurred, "canonical_success_witnesses": []}
