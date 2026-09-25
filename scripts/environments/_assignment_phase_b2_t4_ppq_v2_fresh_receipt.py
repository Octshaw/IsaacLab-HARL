"""Pure, test-side fresh-campaign receipt contract; no Isaac/HARL imports.

The caller owns evidence capture and supplies every identity and I/O authority.
This candidate is not a reviewed formal-route implementation.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
from pathlib import Path
from typing import Any, Callable, Mapping


VERSION = "b2_t4_ppq_fresh_run_success_receipt_v2"
PW_VERSION = "b2_t4_ppq_fresh_campaign_pw_result_v2"
W2E_VERSION = "b2_t4_w2e_multi_update_completion_v2"
W2E_SHA = "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0"
W2I_SHA = "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b"
PW_SHA = "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b"
WITNESSES = ("W1", "W2E", "W3", "W4", "W5", "W6", "W7")
FRESH_PHASES = ("B2-T4-RE6-R3", "B2-T4-RE6-R3-SYNTHETIC", "B2-T4-PPQ-V2-HISTORICAL-FIXTURE")
HEX = set("0123456789abcdef")


class PPQV2Stop(RuntimeError):
    """Fail-closed contract violation."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise PPQV2Stop(reason)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_persist(path: Path, payload: Mapping[str, Any]) -> str:
    """Candidate-only durable JSON writer; refuses overwrite."""
    encoded = canonical(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".ppq-v2-tmp")
    need(not path.exists() and not tmp.exists(), "DESTINATION-EXISTS")
    with tmp.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    need(path.read_bytes() == encoded, "DURABLE-READBACK")
    return hashlib.sha256(encoded).hexdigest()


def readback(path: Path) -> tuple[dict[str, Any], str]:
    encoded = path.read_bytes()
    return json.loads(encoded), hashlib.sha256(encoded).hexdigest()


FIELDS: dict[str, type] = {
    "contract_version": str, "campaign_status": str, "source_phase": str,
    "run_id": str, "worker_pid": int,
    "w2e_contract_version": str, "w2e_selector_sha256": str,
    "w2i_binding_manifest_sha256": str, "ppq_v2_helper_sha256": str,
    "ppq_v2_schema_sha256": str, "pw_helper_sha256": str,
    "production_identity_digest": str, "config_identity_digest": str,
    "expected_transaction_count": int, "expected_T": int,
    "transaction_count": int, "physical_transitions": int,
    "production_s10": int, "transaction_ledger_count": int,
    "bridge_count": int, "tx161_started": bool,
    "w2e_candidate_count": int, "w2e_valid_count": int,
    "w2_env": int, "w2_robot": int, "w2_task": int, "w2_generation": int,
    "w2_claim_tx": int, "w2_claim_step": int,
    "w2_completion_tx": int, "w2_completion_step": int,
    "w2_reopen_tx": int, "w2_reopen_step": int,
    "w2_claim_authority": bool, "w2_continuity": bool,
    "w2_completion": bool, "w2_clear": bool, "w2_reopen": bool,
    "task_completed_count": int, "completion_delta": int, "coverage_max": int,
    "terminal_autoreset_count": int, "terminal_reason_priority_pass": bool,
    "post_autoreset_learned_transaction": bool,
    "pw_contract_version": str, "pw_transaction_count": int,
    "pw_critic_expected": int, "pw_critic_actual": int,
    "pw_actor_factor_expected": int, "pw_actor_factor_actual": int,
    "pw_missing_count": int, "pw_duplicate_count": int,
    "pw_order_fault_count": int, "pw_digest_fault_count": int,
    "pw_temp_residue_count": int,
    "W1_status": str, "W2E_status": str, "W3_status": str,
    "W4_status": str, "W5_status": str, "W6_status": str, "W7_status": str,
    "W7_qualified_count": int,
    "actor_backward_planned": int, "actor_backward": int,
    "actor_step_planned": int, "actor_step": int,
    "critic_backward_planned": int, "critic_backward": int,
    "critic_step_planned": int, "critic_step": int,
    "valid_nonzero_update": int, "valid_zero_effective_update": int,
    "valuenorm_expected": int, "valuenorm_update": int,
    "actor_adam_continuity": bool, "critic_adam_continuity": bool,
    "valuenorm_continuity": bool, "numerical_health": bool,
    "event_returns": int, "stock_compute_returns": int,
    "partial_update": bool, "route_poisoned": bool,
    "checkpoint_io_count": int, "public_activation_count": int,
    "evaluation_playback_count": int,
}


def schema_document() -> dict[str, Any]:
    return {
        "contract_version": VERSION,
        "required_fields": {name: typ.__name__ for name, typ in FIELDS.items()},
        "unknown_fields": "REJECT",
        "source_phase": list(FRESH_PHASES),
        "fixed_reviewed_identity": {"w2e_contract_version": W2E_VERSION,
                                    "w2e_selector_sha256": W2E_SHA,
                                    "w2i_binding_manifest_sha256": W2I_SHA,
                                    "pw_helper_sha256": PW_SHA},
        "derivation": {"physical_transitions": "expected_T * transaction_count",
                       "bridge_count": "transaction_count - 1",
                       "pw_critic_expected": "transaction_count * critic_records_per_tx",
                       "pw_actor_factor_expected": "transaction_count * actor_factor_records_per_tx"},
        "success_route": {"campaign_status": "SUCCESS", "partial_update": False,
                          "route_poisoned": False, "forbidden_action_counters": 0},
    }


def _finite(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(v) for v in value)
    return True


def _sha(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= HEX


def validate_receipt(receipt: Mapping[str, Any], *, expected_phase: str,
                     identity: Mapping[str, str], config: Mapping[str, int]) -> None:
    need(type(receipt) is dict, "SCHEMA-NOT-OBJECT")
    need(set(receipt) == set(FIELDS), "SCHEMA-FIELDS-MISSING-OR-UNKNOWN")
    for key, typ in FIELDS.items():
        need(type(receipt[key]) is typ, f"SCHEMA-TYPE-{key}")
    need(_finite(receipt), "SCHEMA-NONFINITE")
    need(receipt["contract_version"] == VERSION and receipt["campaign_status"] == "SUCCESS",
         "SCHEMA-VERSION-OR-STATUS")
    need(expected_phase in FRESH_PHASES and receipt["source_phase"] == expected_phase,
         "SOURCE-PHASE")
    need(bool(receipt["run_id"]) and receipt["worker_pid"] > 0, "PROCESS-IDENTITY")
    for field, value in schema_document()["fixed_reviewed_identity"].items():
        need(receipt[field] == value, f"IDENTITY-{field}")
    for field in ("ppq_v2_helper_sha256", "ppq_v2_schema_sha256",
                  "production_identity_digest", "config_identity_digest"):
        need(_sha(receipt[field]) and receipt[field] == identity.get(field), f"IDENTITY-{field}")
    n = config["expected_transaction_count"]
    t = config["expected_T"]
    need(n == 160 and t == 2, "FORMAL-CONFIG-NOT-QUALIFIED")
    need(receipt["expected_transaction_count"] == n and receipt["expected_T"] == t and
         receipt["transaction_count"] == n and receipt["physical_transitions"] == n * t and
         receipt["production_s10"] == n and receipt["transaction_ledger_count"] == n and
         receipt["bridge_count"] == n - 1 and receipt["tx161_started"] is False,
         "CAMPAIGN-COUNTS")
    need(receipt["w2e_candidate_count"] >= 1 and 1 <= receipt["w2e_valid_count"] <= receipt["w2e_candidate_count"],
         "W2E-COUNTS")
    need(1 <= receipt["w2_claim_tx"] < receipt["w2_completion_tx"] <= receipt["w2_reopen_tx"] <= n and
         receipt["w2_claim_step"] < receipt["w2_completion_step"] < receipt["w2_reopen_step"] <= n * t,
         "W2-ORDER")
    need(all(receipt[k] is True for k in ("w2_claim_authority", "w2_continuity", "w2_completion",
                                                   "w2_clear", "w2_reopen")), "W2-LAYERS")
    need(receipt["task_completed_count"] >= 1 and receipt["completion_delta"] > 0 and
         receipt["coverage_max"] > 0, "TASK-PROGRESS")
    need(receipt["terminal_autoreset_count"] >= 1 and
         receipt["terminal_reason_priority_pass"] is True and
         receipt["post_autoreset_learned_transaction"] is True, "TERMINAL-AUTORESET")
    need(receipt["pw_contract_version"] == PW_VERSION and receipt["pw_transaction_count"] == n,
         "PW-SCHEMA-OR-TRANSACTIONS")
    need(receipt["pw_critic_expected"] == n * config["critic_records_per_tx"] and
         receipt["pw_actor_factor_expected"] == n * config["actor_factor_records_per_tx"] and
         receipt["pw_critic_actual"] == receipt["pw_critic_expected"] and
         receipt["pw_actor_factor_actual"] == receipt["pw_actor_factor_expected"], "PW-COUNTS")
    need(all(receipt[k] == 0 for k in ("pw_missing_count", "pw_duplicate_count", "pw_order_fault_count",
                                                "pw_digest_fault_count", "pw_temp_residue_count")), "PW-FAULT")
    need(all(receipt[f"{w}_status"] == "PASS" for w in WITNESSES) and
         receipt["W7_qualified_count"] == n, "WITNESSES")
    need(all(receipt[k] == receipt[k + "_planned"] for k in
             ("actor_backward", "actor_step", "critic_backward", "critic_step")), "LEARNER-PLAN")
    need(receipt["valid_nonzero_update"] + receipt["valid_zero_effective_update"] ==
         receipt["critic_step_planned"] and receipt["valuenorm_expected"] ==
         receipt["critic_step_planned"] == receipt["valuenorm_update"], "CRITIC-CLASS-VALUENORM")
    need(all(receipt[k] is True for k in ("actor_adam_continuity", "critic_adam_continuity",
                                                   "valuenorm_continuity", "numerical_health")), "LEARNER-HEALTH")
    need(receipt["event_returns"] == n and receipt["stock_compute_returns"] == 0,
         "RETURNS")
    need(receipt["partial_update"] is False and receipt["route_poisoned"] is False,
         "ROUTE-HEALTH")
    need(all(receipt[k] == 0 for k in ("checkpoint_io_count", "public_activation_count",
                                                "evaluation_playback_count")), "FORBIDDEN-ACTION")


def _selected(w2: Mapping[str, Any]) -> tuple[int, ...]:
    return tuple(w2[k] for k in ("env_id", "robot_id", "task_id", "episode_generation",
                                "claim_tx", "claim_physical_step", "completion_tx",
                                "completion_physical_step", "reopen_tx", "reopen_physical_step"))


def _selector_authority(selector: Callable[..., Any]) -> None:
    need(callable(selector) and selector.__name__ == "reconcile", "W2E-SELECTOR-CALLABLE")
    source = inspect.getsourcefile(selector)
    need(source is not None and sha_file(Path(source)) == W2E_SHA, "W2E-SELECTOR-SOURCE")


def build_receipt(evidence: Mapping[str, Any], *, w2e_selector: Callable[..., dict[str, Any]],
                  w2i_manifest: Path, pw_reconcile: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                  expected_phase: str, config: Mapping[str, int],
                  identity: Mapping[str, str], production_sources: Mapping[str, Path],
                  pw_helper_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    """Reconcile current evidence, then build a candidate from observed values."""
    need(type(evidence) is dict and callable(pw_reconcile), "EXPLICIT-DEPENDENCIES")
    need(not any(k in evidence for k in ("engine", "_base_atomic_json", "hidden_engine_dependency")),
         "HIDDEN-ENGINE-DEPENDENCY")
    _selector_authority(w2e_selector)
    need(sha_file(w2i_manifest) == W2I_SHA, "W2I-MANIFEST-IDENTITY")
    need(sha_file(pw_helper_path) == PW_SHA, "PW-HELPER-IDENTITY")
    need(sha_file(Path(__file__)) == identity.get("ppq_v2_helper_sha256"), "PPQ-V2-HELPER-IDENTITY")
    need(hashlib.sha256(canonical(schema_document())).hexdigest() ==
         identity.get("ppq_v2_schema_sha256"), "PPQ-V2-SCHEMA-IDENTITY")
    need(bool(production_sources) and
         digest({name: sha_file(path) for name, path in sorted(production_sources.items())}) ==
         identity.get("production_identity_digest"), "PRODUCTION-IDENTITY")
    need(digest(dict(config)) == identity.get("config_identity_digest"), "CONFIG-IDENTITY")
    need(evidence.get("source_phase") == expected_phase and expected_phase in FRESH_PHASES,
         "SOURCE-PHASE")
    need(evidence.get("run_id") and type(evidence.get("worker_pid")) is int,
         "PROCESS-IDENTITY")
    n, t = config["expected_transaction_count"], config["expected_T"]
    need((n, t) == (160, 2) and config["critic_records_per_tx"] == 41 and
         config["actor_factor_records_per_tx"] == 4, "FORMAL-CONFIG-NOT-QUALIFIED")
    tx, bridges = evidence["transactions"], evidence["bridges"]
    need(len(tx) == n and all(row["transaction_index"] == i and
                             row["s7_s8_s9_s10"] == [True] * 4 and row["finite"] is True
                             for i, row in enumerate(tx, 1)), "TRANSACTION-LEDGER")
    need(len(bridges) == n - 1 and all(row["bridge_index"] == i and row["pass"] is True and
                                       row["from_update_id"] == tx[i - 1]["update_id"] and
                                       row["to_update_id"] == tx[i]["update_id"]
                                       for i, row in enumerate(bridges, 1)), "BRIDGE-LEDGER")
    need(evidence["physical_transitions"] == n * t and evidence["production_s10"] == n and
         evidence["transaction_ledger_count"] == n and evidence["bridge_count"] == n - 1 and
         evidence["tx161_started"] is False, "CAMPAIGN-COUNTS")
    need(evidence["w2e_input"]["transactions"] == tx and evidence["w2e_input"]["bridges"] == bridges,
         "W2E-INPUT-LEDGER-DRIFT")
    pw = dict(pw_reconcile(evidence))
    need(pw.get("contract_version") == PW_VERSION and pw.get("transaction_count") == n and
         pw.get("run_id") == evidence["run_id"], "PW-FRESH-IDENTITY")
    trace = ["01_reconcile_transactions_bridges_pw"]
    w2 = w2e_selector(evidence["w2e_input"])
    need(w2.get("schema_version") == W2E_VERSION and w2.get("pass") is True and
         w2.get("candidate_count", 0) >= 1 and
         1 <= w2.get("valid_count", 0) <= w2["candidate_count"] and
         type(w2.get("selected")) is dict, "W2E-SELECTOR")
    valid = [item for item in w2["inventory"] if item["pass"]]
    need(w2["selected"] == valid[0] and len(valid) == w2["valid_count"], "W2E-DETERMINISM")
    if "retained_w2e_inventory" in evidence:
        need(w2 == evidence["retained_w2e_inventory"], "W2E-RETAINED-DRIFT")
    selected = w2["selected"]
    need(all(selected["layers"].values()) and selected["ownership_clear"] is True and
         selected["first_bridge"] is not None, "W2E-LAYERS")
    need(_selected(selected) == _selected(evidence["witnesses"]["W2E"]["selected"]),
         "W2E-WITNESS-IDENTITY")
    need(selected["claim_tx"] < selected["completion_tx"] <= selected["reopen_tx"] and
         selected["claim_physical_step"] < selected["completion_physical_step"] <
         selected["reopen_physical_step"],
         "W2E-TX-ORDER")
    need(all(evidence["witnesses"][w]["pass"] is True for w in WITNESSES),
         "WITNESS-ADJUDICATION")
    need(evidence["witnesses"]["W7"]["qualified_count"] == n,
         "W7-QUALIFIED-COUNT")
    trace.append("02_adjudicate_w2e_w1_w7_and_route")
    learner = evidence["learner"]
    receipt = {
        "contract_version": VERSION, "campaign_status": "SUCCESS",
        "source_phase": evidence["source_phase"], "run_id": evidence["run_id"],
        "worker_pid": evidence["worker_pid"], "w2e_contract_version": W2E_VERSION,
        "w2e_selector_sha256": W2E_SHA, "w2i_binding_manifest_sha256": W2I_SHA,
        "ppq_v2_helper_sha256": identity["ppq_v2_helper_sha256"],
        "ppq_v2_schema_sha256": identity["ppq_v2_schema_sha256"],
        "pw_helper_sha256": PW_SHA,
        "production_identity_digest": identity["production_identity_digest"],
        "config_identity_digest": identity["config_identity_digest"],
        "expected_transaction_count": n, "expected_T": t,
        "transaction_count": len(tx), "physical_transitions": evidence["physical_transitions"],
        "production_s10": evidence["production_s10"],
        "transaction_ledger_count": evidence["transaction_ledger_count"],
        "bridge_count": evidence["bridge_count"], "tx161_started": evidence["tx161_started"],
        "w2e_candidate_count": w2["candidate_count"], "w2e_valid_count": w2["valid_count"],
        "w2_env": selected["env_id"], "w2_robot": selected["robot_id"],
        "w2_task": selected["task_id"], "w2_generation": selected["episode_generation"],
        "w2_claim_tx": selected["claim_tx"], "w2_claim_step": selected["claim_physical_step"],
        "w2_completion_tx": selected["completion_tx"],
        "w2_completion_step": selected["completion_physical_step"],
        "w2_reopen_tx": selected["reopen_tx"], "w2_reopen_step": selected["reopen_physical_step"],
        "w2_claim_authority": selected["layers"]["A_claim_authority"],
        "w2_continuity": selected["layers"]["B_ownership_continuity"],
        "w2_completion": selected["layers"]["C_completion_authority"],
        "w2_clear": selected["layers"]["D_ownership_clear"],
        "w2_reopen": selected["layers"]["E_decision_reopen"],
        "task_completed_count": evidence["task_completed_count"],
        "completion_delta": evidence["completion_delta"], "coverage_max": evidence["coverage_max"],
        "terminal_autoreset_count": evidence["terminal_autoreset_count"],
        "terminal_reason_priority_pass": evidence["terminal_reason_priority_pass"],
        "post_autoreset_learned_transaction": evidence["post_autoreset_learned_transaction"],
        "pw_contract_version": pw["contract_version"],
        "pw_transaction_count": pw["transaction_count"],
        "pw_critic_expected": n * config["critic_records_per_tx"],
        "pw_critic_actual": pw["critic_actual"],
        "pw_actor_factor_expected": n * config["actor_factor_records_per_tx"],
        "pw_actor_factor_actual": pw["actor_factor_actual"],
        **{f"pw_{k}": pw[k] for k in ("missing_count", "duplicate_count", "order_fault_count",
                                        "digest_fault_count", "temp_residue_count")},
        **{f"{w}_status": "PASS" for w in WITNESSES},
        "W7_qualified_count": evidence["witnesses"]["W7"]["qualified_count"],
        **{k: learner[k] for k in ("actor_backward_planned", "actor_backward",
                                     "actor_step_planned", "actor_step",
                                     "critic_backward_planned", "critic_backward",
                                     "critic_step_planned", "critic_step",
                                     "valid_nonzero_update", "valid_zero_effective_update",
                                     "valuenorm_expected", "valuenorm_update",
                                     "actor_adam_continuity", "critic_adam_continuity",
                                     "valuenorm_continuity", "numerical_health")},
        "event_returns": evidence["event_returns"],
        "stock_compute_returns": evidence["stock_compute_returns"],
        "partial_update": evidence["partial_update"], "route_poisoned": evidence["route_poisoned"],
        "checkpoint_io_count": evidence["checkpoint_io_count"],
        "public_activation_count": evidence["public_activation_count"],
        "evaluation_playback_count": evidence["evaluation_playback_count"],
    }
    trace.append("03_build_receipt")
    validate_receipt(receipt, expected_phase=expected_phase, identity=identity, config=config)
    trace.append("04_schema_validate")
    return receipt, w2, pw, trace


def publish_witnesses(*, validated: bool, receipt_sha256: str,
                      witnesses: Mapping[str, Any], provisional_digests: Mapping[str, str],
                      writer: Callable[[Path, Mapping[str, Any]], str], output_dir: Path) -> list[str]:
    need(validated and _sha(receipt_sha256), "PREMATURE-PUBLICATION")
    need(set(witnesses) == set(WITNESSES) == set(provisional_digests), "WITNESS-SET")
    need(all(digest(witnesses[w]) == provisional_digests[w] for w in WITNESSES),
         "STALE-PROVISIONAL-WITNESS")
    names = []
    for witness in WITNESSES:
        filename = f"{witness}_canonical_success.json"
        writer(output_dir / filename, witnesses[witness])
        names.append(filename)
    return names


def finalize_campaign(evidence: Mapping[str, Any], *, w2e_selector: Callable[..., dict[str, Any]],
                      w2i_manifest: Path, pw_reconcile: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                      expected_phase: str, config: Mapping[str, int], identity: Mapping[str, str],
                      production_sources: Mapping[str, Path], pw_helper_path: Path,
                      writer: Callable[[Path, Mapping[str, Any]], str],
                      reader: Callable[[Path], tuple[dict[str, Any], str]], output_dir: Path,
                      payload_mutator: Callable[[dict[str, Any]], None] | None = None,
                      readback_guard: Callable[[dict[str, Any], str], None] | None = None,
                      before_publication: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    need(callable(writer) and callable(reader) and isinstance(output_dir, Path),
         "EXPLICIT-PERSISTENCE-DEPENDENCIES")
    receipt, w2, pw, trace = build_receipt(
        evidence, w2e_selector=w2e_selector, w2i_manifest=w2i_manifest,
        pw_reconcile=pw_reconcile, expected_phase=expected_phase, config=config, identity=identity,
        production_sources=production_sources, pw_helper_path=pw_helper_path)
    if payload_mutator:
        payload_mutator(receipt)
        validate_receipt(receipt, expected_phase=expected_phase, identity=identity, config=config)
    provisional = {w: (w2 if w == "W2E" else evidence["witnesses"][w]) for w in WITNESSES}
    provisional_digests = {w: digest(provisional[w]) for w in WITNESSES}
    if before_publication:
        before_publication(provisional)
    path = output_dir / "candidate_success_receipt_v2.json"
    expected_sha = writer(path, receipt)
    trace.append("05_durable_write")
    observed, observed_sha = reader(path)
    trace.append("06_readback")
    need(observed == receipt and observed_sha == expected_sha == digest(receipt),
         "RECEIPT-DIGEST-OR-READBACK")
    trace.append("07_digest_validate")
    if readback_guard:
        readback_guard(observed, observed_sha)
    validate_receipt(observed, expected_phase=expected_phase, identity=identity, config=config)
    trace.append("08_schema_revalidate")
    publication = publish_witnesses(validated=True, receipt_sha256=observed_sha,
                                    witnesses=provisional, provisional_digests=provisional_digests,
                                    writer=writer, output_dir=output_dir)
    trace.append("09_canonical_witness_publication")
    return {"pass": True, "receipt": receipt, "receipt_sha256": observed_sha,
            "publication": publication, "trace": trace,
            "w2e": {"candidate_count": w2["candidate_count"],
                    "valid_count": w2["valid_count"], "selected": w2["selected"]},
            "pw": pw}


def failure_record(*, stage: str, exception: BaseException, mutation_occurred: bool,
                   writer: Callable[[Path, Mapping[str, Any]], str], output_dir: Path) -> dict[str, Any]:
    need(bool(stage) and callable(writer), "FAILURE-DEPENDENCY")
    payload = {"contract_version": "b2_t4_ppq_fresh_failure_record_v2", "status": "FAILURE",
               "stage": stage, "exception_type": type(exception).__name__,
               "exception_message": str(exception), "partial_update": mutation_occurred,
               "route_poisoned": mutation_occurred, "success_receipt": None,
               "canonical_success_witnesses": []}
    writer(output_dir / "failure_record_v2.json", payload)
    return payload
