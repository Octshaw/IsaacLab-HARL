"""Pure, test-side Layer-A worker receipt projection and supervisor validation.

The PPQ-V2 receipt remains a separate reviewed contract.  This module adds the
inherited worker/process gates which the RE6-R3 supervisor accidentally dropped.
No environment, learner, CUDA, or Isaac modules are imported here.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Callable, Mapping


VERSION = "b2_t4_layer_a_worker_receipt_v2"
ENVELOPE_VERSION = "b2_t4_layer_a_worker_receipt_envelope_v2"

# These are additional direct fields; all PPQ-V2 fields are also mandatory.
EXTRA_TYPES: dict[str, type] = {
    "layer_a_contract_version": str,
    "status": str,
    "source_authority_digest": str,
    "config_authority_digest": str,
    "filesystem_precondition_digest": str,
    "ppq_v2_candidate_sha256": str,
    "ppq_v2_readback_pass": bool,
    "cuda_probe_count": int,
    "cuda_probe_pass": bool,
    "app_launcher_count": int,
    "app_launcher_started": bool,
    "entry_point_resolution_pass": bool,
    "environment_count": int,
    "initial_reset_count": int,
    "persistent_learner_count": int,
    "S10_count": int,
    "ledger_count": int,
    "event_returns_count": int,
    "stock_compute_returns_count": int,
    "TASK_COMPLETED_count": int,
    "max_coverage": int,
    "invalid_critic_class_count": int,
    "persistent_continuity_pass": bool,
    "factor_audits_pass": bool,
    "learner": dict,
    "contracts": dict,
    "witnesses": dict,
    "pw_progress": dict,
    "final_in_worker_quiescence_pass": bool,
    "env_close_pass": bool,
    "app_close_invoked": bool,
    "receipt_written_before_app_close": bool,
    "receipt_fsync_pass": bool,
    "receipt_readback_pass": bool,
}

LEARNER_KEYS = (
    "actor_backward_planned", "actor_backward", "actor_step_planned", "actor_step",
    "critic_backward_planned", "critic_backward", "critic_step_planned", "critic_step",
    "valid_nonzero_update", "valid_zero_effective_update", "valuenorm_expected",
    "valuenorm_update", "actor_adam_continuity", "critic_adam_continuity",
    "valuenorm_continuity", "numerical_health",
)
CONTRACT_ID_KEYS = (
    "w2e_contract_version", "w2e_selector_sha256", "w2i_binding_manifest_sha256",
    "pw_helper_sha256", "pw_contract_version", "ppq_v2_helper_sha256",
    "ppq_v2_schema_sha256", "contract_version", "normalizer_sha256",
    "layer_a_contract_version", "production_identity_digest", "config_identity_digest",
)
PW_KEYS = (
    "critic_records", "actor_factor_records", "missing", "duplicate",
    "out_of_order", "digest_mismatch", "temp_residue", "old_mutable_progress_paths",
)
WITNESS_KEYS = ("W1", "W2E", "W3", "W4", "W5", "W6", "W7")
HEX = frozenset("0123456789abcdef")


class LayerAStop(ValueError):
    """A missing or contradictory mandatory source/receipt predicate."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise LayerAStop(reason)


def item(source: Mapping[str, Any], key: str, label: str) -> Any:
    require(type(source) is dict and key in source and source[key] is not None,
            f"MISSING-SOURCE:{label}.{key}")
    return source[key]


def nested(source: Mapping[str, Any], *path: str) -> Any:
    value: Any = source
    for part in path:
        value = item(value, part, ".".join(path[:-1]))
    return value


def digest64(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= HEX


def canonical_sha(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8") + b"\n").hexdigest()


def envelope_for(payload: Mapping[str, Any]) -> dict[str, Any]:
    require(type(payload) is dict, "ENVELOPE-PAYLOAD-NOT-OBJECT")
    return {"schema_version": ENVELOPE_VERSION, "payload": deepcopy(payload),
            "payload_sha256": canonical_sha(payload)}


def project_layer_a_worker_receipt(sources: Mapping[str, Any],
                                   ppq_schema: Mapping[str, Any]) -> dict[str, Any]:
    """Construct, never default, a future-worker-shaped receipt from explicit evidence.

    The caller must pass current-run raw final, normalized result, a PPQ-V2
    candidate, worker-local pre-close/close facts, PW verifier and witnesses.
    The caller must validate and crosscheck before durable success publication.
    """
    raw = item(sources, "raw_final", "sources")
    candidate = item(sources, "ppq_v2_candidate", "sources")
    normalized = item(sources, "normalized", "sources")
    handoff = item(sources, "worker_handoff", "sources")
    pw = item(sources, "pw_verifier", "sources")
    witnesses = item(sources, "witnesses", "sources")
    normalizer_sha = item(sources, "normalizer_sha256", "sources")
    ppq_readback = item(sources, "ppq_v2_readback", "sources")
    required_ppq = item(ppq_schema, "required_fields", "ppq_schema")
    require(type(candidate) is dict and set(candidate) == set(required_ppq),
            "PPQ-V2-CANDIDATE-FIELDS")
    require(type(witnesses) is dict and set(witnesses) == set(WITNESS_KEYS),
            "WITNESS-SOURCES-INCOMPLETE")

    counts = nested(raw, "exact_execution_counts")
    learner_source = nested(normalized, "normalized", "learner")
    learner = {key: deepcopy(item(learner_source, key, "normalized.learner"))
               for key in LEARNER_KEYS}
    contract_ids = {key: deepcopy(item(candidate, key, "ppq_v2_candidate"))
                    for key in CONTRACT_ID_KEYS if key not in
                    ("normalizer_sha256", "layer_a_contract_version")}
    contract_ids["normalizer_sha256"] = normalizer_sha
    contract_ids["layer_a_contract_version"] = VERSION
    # RE5's five zero-fault gates remain explicit, not silently removed.
    contract_ids["NR_reconciliation_faults"] = sum(
        0 if row["pass"] is True else 1 for row in item(sources, "terminal_rows", "sources"))
    contract_ids["ZD_actor_reconciliation_faults"] = sum(
        0 if row["pass"] is True else 1 for row in item(sources, "zero_dvm_rows", "sources"))
    contract_ids["SR_serializer_faults"] = sum(
        0 if row["s7_ledger_unchanged"] is True else 1
        for row in item(sources, "terminal_rows", "sources"))
    contract_ids["bookkeeping_faults"] = sum(
        0 if row["s7_s8_s9_s10"] == [True, True, True, True] and
        row["finite"] is True else 1 for row in item(sources, "transaction_rows", "sources"))
    contract_ids["lifecycle_policy_call_faults"] = (
        item(counts, "missing_call_faults", "raw.counts") +
        item(counts, "duplicate_call_faults", "raw.counts") +
        item(counts, "continuation_resample_faults", "raw.counts"))
    result = deepcopy(candidate)
    result.update({
        "layer_a_contract_version": VERSION,
        "status": item(handoff, "status", "worker_handoff"),
        "source_authority_digest": item(handoff, "source_authority_digest", "worker_handoff"),
        "config_authority_digest": item(handoff, "config_authority_digest", "worker_handoff"),
        "filesystem_precondition_digest": item(handoff, "filesystem_precondition_digest", "worker_handoff"),
        "ppq_v2_candidate_sha256": item(sources, "ppq_v2_candidate_file_sha256", "sources"),
        "ppq_v2_readback_pass": item(ppq_readback, "pass", "ppq_v2_readback"),
        "cuda_probe_count": item(handoff, "cuda_probe_count", "worker_handoff"),
        "cuda_probe_pass": item(handoff, "cuda_probe_pass", "worker_handoff"),
        "app_launcher_count": item(counts, "app_launcher_lifetimes", "raw.counts"),
        "app_launcher_started": item(handoff, "app_launcher_started", "worker_handoff"),
        "entry_point_resolution_pass": item(handoff, "entry_point_resolution_pass", "worker_handoff"),
        "environment_count": item(counts, "environment_constructions", "raw.counts"),
        "initial_reset_count": item(counts, "environment_resets", "raw.counts"),
        "persistent_learner_count": item(counts, "distinct_learner_constructions", "raw.counts"),
        "S10_count": item(counts, "s10_pass", "raw.counts"),
        "ledger_count": len(item(sources, "transaction_rows", "sources")),
        "event_returns_count": item(counts, "event_return_computations", "raw.counts"),
        "stock_compute_returns_count": item(counts, "stock_compute_returns", "raw.counts"),
        "TASK_COMPLETED_count": nested(normalized, "derived", "task_completed_count"),
        "max_coverage": nested(normalized, "derived", "coverage_max"),
        "invalid_critic_class_count": (item(counts, "critic_optimizer_step_total", "raw.counts") -
                                       item(counts, "valid_nonzero_update", "raw.counts") -
                                       item(counts, "valid_zero_effective_update", "raw.counts")),
        "persistent_continuity_pass": nested(raw, "persistent_learner_identity", "object_ids_stable"),
        "factor_audits_pass": all(tx["factor_segment_count"] == 3 and tx["s10_pass"] is True
                                  for tx in item(raw, "transactions", "raw_final")),
        "learner": learner,
        "contracts": contract_ids,
        "witnesses": {key: {"pass": item(witnesses[key], "pass", key)}
                      for key in WITNESS_KEYS},
        "pw_progress": {key: item(pw, key, "pw_verifier") for key in PW_KEYS},
        "final_in_worker_quiescence_pass": nested(raw, "final_read_only_quiescence_check", "pass"),
        "env_close_pass": item(handoff, "env_close_pass", "worker_handoff"),
        "app_close_invoked": item(handoff, "app_close_invoked", "worker_handoff"),
        "receipt_written_before_app_close": item(handoff, "receipt_written_before_app_close", "worker_handoff"),
        "receipt_fsync_pass": item(handoff, "receipt_fsync_pass", "worker_handoff"),
        "receipt_readback_pass": item(handoff, "receipt_readback_pass", "worker_handoff"),
    })
    result["witnesses"]["W7"]["count"] = item(witnesses["W7"], "qualified_count", "W7")
    require(set(result) == set(required_ppq) | set(EXTRA_TYPES), "PROJECTED-FIELDS-INCOMPLETE")
    return result


def validate_layer_a_worker_receipt(
    receipt: Any, *, ppq_schema: Mapping[str, Any],
    ppq_validator: Callable[..., None], expected_phase: str,
    expected_run_id: str, expected_pid: int, expected_source_digest: str,
    expected_config_digest: str, ppq_identity: Mapping[str, str],
    ppq_config: Mapping[str, int], expected_normalizer_sha256: str,
) -> dict[str, Any]:
    """Supervisor predicate set. It never changes or fills the worker receipt."""
    required_ppq = item(ppq_schema, "required_fields", "ppq_schema")
    checks: dict[str, bool] = {}
    checks["receipt_object"] = type(receipt) is dict
    if not checks["receipt_object"]:
        return {"pass": False, "checks": checks, "failed": ["receipt_object"]}
    checks["envelope_schema"] = receipt.get("schema_version") == ENVELOPE_VERSION
    checks["envelope_fields"] = set(receipt) == {"schema_version", "payload", "payload_sha256"}
    payload = receipt.get("payload")
    checks["payload_object"] = type(payload) is dict
    checks["payload_digest"] = checks["payload_object"] and receipt.get("payload_sha256") == canonical_sha(payload)
    if not checks["payload_object"]:
        return {"pass": False, "checks": checks,
                "failed": [key for key, passed in checks.items() if not passed]}
    receipt = payload
    checks["closed_schema"] = set(receipt) == set(required_ppq) | set(EXTRA_TYPES)
    for field, name in {**required_ppq, **{k: v.__name__ for k, v in EXTRA_TYPES.items()}}.items():
        checks[f"field:{field}"] = field in receipt and receipt[field] is not None and type(receipt[field]).__name__ == name
    if not checks["closed_schema"] or not all(checks.values()):
        return {"pass": False, "checks": checks,
                "failed": [key for key, passed in checks.items() if not passed]}
    try:
        ppq_validator({key: receipt[key] for key in required_ppq},
                      expected_phase=expected_phase, identity=ppq_identity,
                      config=ppq_config)
        checks["complete_ppq_v2_validator"] = True
    except (Exception, KeyError, TypeError, ValueError):
        checks["complete_ppq_v2_validator"] = False
    checks.update({
        "layer_a_contract_version": receipt["layer_a_contract_version"] == VERSION,
        "status_success": receipt["status"] == "success",
        "run_id": bool(receipt["run_id"]) and receipt["run_id"] == expected_run_id,
        "worker_pid": receipt["worker_pid"] > 0 and receipt["worker_pid"] == expected_pid,
        "source_authority": digest64(receipt["source_authority_digest"]) and receipt["source_authority_digest"] == expected_source_digest,
        "config_authority": digest64(receipt["config_authority_digest"]) and receipt["config_authority_digest"] == expected_config_digest,
        "filesystem_authority": digest64(receipt["filesystem_precondition_digest"]),
        "ppq_v2_candidate_digest": digest64(receipt["ppq_v2_candidate_sha256"]) and receipt["ppq_v2_readback_pass"] is True,
        "cuda_probe": receipt["cuda_probe_count"] == 1 and receipt["cuda_probe_pass"] is True,
        "app_launcher": receipt["app_launcher_count"] == 1 and receipt["app_launcher_started"] is True,
        "entry_point": receipt["entry_point_resolution_pass"] is True,
        "environment": receipt["environment_count"] == 1,
        "reset": receipt["initial_reset_count"] == 1,
        "learner_once": receipt["persistent_learner_count"] == 1,
        "s10": receipt["S10_count"] == receipt["transaction_count"],
        "ledger": receipt["ledger_count"] == receipt["transaction_count"],
        "returns_direct": receipt["event_returns_count"] == receipt["event_returns"] == receipt["transaction_count"] and receipt["stock_compute_returns_count"] == receipt["stock_compute_returns"] == 0,
        "task_direct": receipt["TASK_COMPLETED_count"] == receipt["task_completed_count"] >= 1 and receipt["max_coverage"] == receipt["coverage_max"] > 0,
        "invalid_critic_classes": receipt["invalid_critic_class_count"] == 0,
        "persistent_learner": receipt["persistent_continuity_pass"] is True,
        "factor": receipt["factor_audits_pass"] is True,
        "learner_map_nonempty": bool(receipt["learner"]),
        "contract_map_nonempty": bool(receipt["contracts"]),
        "witness_map_nonempty": bool(receipt["witnesses"]),
        "pw_map_nonempty": bool(receipt["pw_progress"]),
        "worker_quiescence": receipt["final_in_worker_quiescence_pass"] is True,
        "env_close": receipt["env_close_pass"] is True,
        "app_close_invoked": receipt["app_close_invoked"] is True,
        "receipt_order": all(receipt[key] is True for key in
                             ("receipt_written_before_app_close", "receipt_fsync_pass",
                              "receipt_readback_pass")),
    })
    learner = receipt["learner"]
    checks["learner_map_fields"] = set(learner) == set(LEARNER_KEYS) and all(
        type(learner[key]) is (bool if key.endswith("continuity") or key == "numerical_health" else int)
        for key in LEARNER_KEYS if key in learner)
    if checks["learner_map_fields"]:
        checks["learner_map_values"] = all(learner[key] == receipt[key] for key in LEARNER_KEYS)
    else:
        checks["learner_map_values"] = False
    contracts = receipt["contracts"]
    checks["contract_map_fields"] = set(CONTRACT_ID_KEYS) <= set(contracts) and all(
        key in contracts for key in ("NR_reconciliation_faults", "ZD_actor_reconciliation_faults",
                                     "SR_serializer_faults", "bookkeeping_faults",
                                     "lifecycle_policy_call_faults"))
    checks["contract_identities"] = checks["contract_map_fields"] and all(
        contracts[key] == (VERSION if key == "layer_a_contract_version" else
                          expected_normalizer_sha256 if key == "normalizer_sha256" else
                          receipt[key]) for key in CONTRACT_ID_KEYS)
    checks["contract_faults"] = checks["contract_map_fields"] and all(
        type(contracts[key]) is int and contracts[key] == 0 for key in
        ("NR_reconciliation_faults", "ZD_actor_reconciliation_faults",
         "SR_serializer_faults", "bookkeeping_faults", "lifecycle_policy_call_faults"))
    witnesses = receipt["witnesses"]
    checks["witness_statuses"] = set(witnesses) == set(WITNESS_KEYS) and all(
        type(witnesses[key]) is dict and witnesses[key].get("pass") is True and
        receipt[f"{key}_status"] == "PASS" for key in WITNESS_KEYS)
    checks["w7_count"] = receipt["W7_qualified_count"] == receipt["transaction_count"]
    pw = receipt["pw_progress"]
    checks["pw_map_fields"] = set(pw) == set(PW_KEYS) and all(type(pw[key]) is int for key in PW_KEYS if key in pw)
    checks["pw_map_values"] = checks["pw_map_fields"] and (
        pw["critic_records"] == receipt["pw_critic_actual"] == receipt["pw_critic_expected"] and
        pw["actor_factor_records"] == receipt["pw_actor_factor_actual"] == receipt["pw_actor_factor_expected"] and
        all(pw[key] == 0 for key in PW_KEYS[2:]) and
        receipt["pw_transaction_count"] == receipt["transaction_count"])
    checks["route_health"] = receipt["campaign_status"] == "SUCCESS" and receipt["partial_update"] is False and receipt["route_poisoned"] is False
    checks["forbidden_actions"] = all(receipt[key] == 0 for key in
                                      ("checkpoint_io_count", "public_activation_count",
                                       "evaluation_playback_count"))
    failed = [key for key, passed in checks.items() if not passed]
    return {"pass": not failed, "checks": checks, "failed": failed}


def crosscheck_raw_vs_receipt(receipt: Any, sources: Mapping[str, Any]) -> dict[str, Any]:
    """Independently compare published values with raw counters and ledgers."""
    if type(receipt) is not dict:
        return {"pass": False, "checks": {"receipt_object": False},
                "failed": ["receipt_object"]}
    raw = item(sources, "raw_final", "sources")
    counts = nested(raw, "exact_execution_counts")
    normalized = item(sources, "normalized", "sources")
    derived = nested(normalized, "derived")
    candidate = item(sources, "ppq_v2_candidate", "sources")
    handoff = item(sources, "worker_handoff", "sources")
    tx_rows = item(sources, "transaction_rows", "sources")
    bridge_rows = item(sources, "bridge_rows", "sources")
    lifecycle_rows = item(sources, "lifecycle_rows", "sources")
    terminal_rows = item(sources, "terminal_rows", "sources")
    pw = item(sources, "pw_verifier", "sources")
    w2e = item(sources, "w2e_result", "sources")
    witnesses = item(sources, "witnesses", "sources")
    completion_events = sum(
        event.get("event") == "task_completed" for row in lifecycle_rows
        for step in row["steps"] for event in step["events"])
    raw_values: dict[str, Any] = {
        "run_id": handoff["run_id"],
        "worker_pid": raw["process_id"],
        "cuda_probe_count": handoff["cuda_probe_count"],
        "app_launcher_count": counts["app_launcher_lifetimes"],
        "environment_count": counts["environment_constructions"],
        "initial_reset_count": counts["environment_resets"],
        "persistent_learner_count": counts["distinct_learner_constructions"],
        "physical_transitions": counts["real_rollout_steps"],
        "transaction_count": counts["successful_full_transactions"],
        "S10_count": counts["s10_pass"],
        "production_s10": counts["s10_pass"],
        "ledger_count": len(tx_rows),
        "transaction_ledger_count": len(tx_rows),
        "bridge_count": len(bridge_rows),
        "event_returns_count": counts["event_return_computations"],
        "event_returns": sum(row["event_returns"] for row in tx_rows),
        "stock_compute_returns_count": counts["stock_compute_returns"],
        "stock_compute_returns": sum(row["stock_compute_returns"] for row in tx_rows),
        "TASK_COMPLETED_count": completion_events,
        "task_completed_count": derived["task_completed_count"],
        "completion_delta": derived["completion_delta"],
        "max_coverage": derived["coverage_max"],
        "coverage_max": derived["coverage_max"],
        "terminal_autoreset_count": counts["terminal_autoreset_events"],
        "post_autoreset_learned_transaction": derived["post_autoreset_learned_transaction"],
        "actor_backward": counts["actor_backward_total"],
        "actor_step": counts["actor_optimizer_step_total"],
        "critic_backward": counts["critic_backward_total"],
        "critic_step": counts["critic_optimizer_step_total"],
        "valid_nonzero_update": counts["valid_nonzero_update"],
        "valid_zero_effective_update": counts["valid_zero_effective_update"],
        "valuenorm_update": counts["valuenorm_update_total"],
        "invalid_critic_class_count": (counts["critic_optimizer_step_total"] -
                                       counts["valid_nonzero_update"] -
                                       counts["valid_zero_effective_update"]),
        "w2e_candidate_count": w2e["candidate_count"],
        "w2e_valid_count": w2e["valid_count"],
        "pw_critic_actual": pw["critic_records"],
        "pw_actor_factor_actual": pw["actor_factor_records"],
        "final_in_worker_quiescence_pass": raw["final_read_only_quiescence_check"]["pass"],
        "persistent_continuity_pass": raw["persistent_learner_identity"]["object_ids_stable"],
        "factor_audits_pass": all(tx["factor_segment_count"] == 3 and tx["s10_pass"] is True
                                  for tx in raw["transactions"]),
        "ppq_v2_candidate_sha256": sources["ppq_v2_candidate_file_sha256"],
        "ppq_v2_readback_pass": sources["ppq_v2_readback"]["pass"],
    }
    raw_values["tx161_started"] = bool(counts["transaction_161_started"])
    for key in ("env_close_pass", "app_close_invoked", "receipt_written_before_app_close",
                "receipt_fsync_pass", "receipt_readback_pass", "partial_update",
                "route_poisoned"):
        raw_values[key] = handoff[key]
    for key in LEARNER_KEYS:
        raw_values[f"learner.{key}"] = normalized["normalized"]["learner"][key]
    for key in WITNESS_KEYS:
        raw_values[f"witnesses.{key}.pass"] = witnesses[key]["pass"]
    raw_values["witnesses.W7.count"] = witnesses["W7"]["qualified_count"]
    for key in PW_KEYS:
        raw_values[f"pw_progress.{key}"] = pw[key]
    for key in ("w2_env", "w2_robot", "w2_task", "w2_generation", "w2_claim_tx",
                "w2_claim_step", "w2_completion_tx", "w2_completion_step",
                "w2_reopen_tx", "w2_reopen_step"):
        selected = w2e["selected"]
        selected_key = {"w2_env": "env_id", "w2_robot": "robot_id", "w2_task": "task_id",
                        "w2_generation": "episode_generation", "w2_claim_step": "claim_physical_step",
                        "w2_completion_step": "completion_physical_step",
                        "w2_reopen_step": "reopen_physical_step"}.get(key, key[3:])
        raw_values[key] = selected[selected_key]
    checks = {}
    for key, value in raw_values.items():
        actual: Any = receipt
        for component in key.split("."):
            actual = actual.get(component) if type(actual) is dict else None
        checks[key] = type(actual) is type(value) and actual == value
    checks["candidate_exact"] = all(receipt.get(key) == value for key, value in candidate.items())
    checks["raw_transaction_rows"] = all(
        row["transaction_index"] == index and row["s7_s8_s9_s10"] == [True] * 4 and
        row["finite"] is True for index, row in enumerate(tx_rows, 1))
    checks["raw_bridge_rows"] = all(
        row["bridge_index"] == index and row["pass"] is True
        for index, row in enumerate(bridge_rows, 1))
    checks["raw_terminal_rows"] = len(terminal_rows) == len(tx_rows) and all(
        row["pass"] is True for row in terminal_rows)
    failed = [key for key, passed in checks.items() if not passed]
    return {"pass": not failed, "checks": checks, "failed": failed}


def adjudicate_supervisor(receipt: Any, layer_b_pass: bool,
                          *, raw_sources: Mapping[str, Any],
                          **validator_kwargs: Any) -> dict[str, Any]:
    """Layer B is independent and cannot rescue invalid Layer A or raw mismatch."""
    layer_a = validate_layer_a_worker_receipt(receipt, **validator_kwargs)
    payload = receipt.get("payload") if type(receipt) is dict else None
    crosscheck = crosscheck_raw_vs_receipt(payload, raw_sources)
    passed = layer_a["pass"] and crosscheck["pass"] and layer_b_pass
    return {"layer_a": layer_a, "raw_crosscheck": crosscheck,
            "layer_b_pass": layer_b_pass, "pass": passed,
            "status": "PASS" if passed else "STOP"}


def failure_flags(*, irreversible_mutation_observed: bool) -> dict[str, Any]:
    """Failure state for a future worker; no historical object is changed."""
    require(type(irreversible_mutation_observed) is bool, "MUTATION-STATE-MISSING")
    return {"status": "STOP", "partial_update": irreversible_mutation_observed,
            "route_poisoned": irreversible_mutation_observed,
            "success_receipt_published": False}
