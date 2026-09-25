"""Pure, run-portable normalization of retained assignment evidence.

This module validates and transforms evidence.  It neither grants a phase nor
creates runtime authority.  The expected identity enters through an opaque
context minted from an independently supplied authority document.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any


CONTEXT_VERSION = "b2_t4_normalization_context_v1"
CONTEXT_AUTHORITY_FIELDS = frozenset({
    "context_version", "authority_kind", "expected_source_phase",
    "expected_run_id", "expected_artifact_namespace",
    "source_authority_digest", "run_binding_digest",
})
AUTHORITY_KINDS = frozenset({"OFFLINE_QUALIFICATION", "RUNTIME_AUTHORITY_AND_RUN_BINDING"})
_CONTEXT_SEAL = object()


class NormalizationStop(RuntimeError):
    """A raw/normalized evidence authority did not reconcile."""


class TrustedNormalizationContext:
    """Opaque validated identity context; construct via ``make_trusted_context``."""

    __slots__ = (
        "context_version", "authority_kind", "expected_source_phase",
        "expected_run_id", "expected_artifact_namespace",
        "source_authority_digest", "run_binding_digest", "authority_document_digest",
        "_seal",
    )

    def __init__(self, authority: Mapping[str, str], seal: object) -> None:
        if seal is not _CONTEXT_SEAL:
            raise NormalizationStop("CONTEXT-NOT-TRUSTED")
        for name in CONTEXT_AUTHORITY_FIELDS:
            setattr(self, name, authority[name])
        self.authority_document_digest = hashlib.sha256(
            json.dumps(dict(authority), sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self._seal = seal

    def as_dict(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in sorted(CONTEXT_AUTHORITY_FIELDS)} | {
            "authority_document_digest": self.authority_document_digest,
        }


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise NormalizationStop(reason)


def _sha256(value: object) -> bool:
    return (type(value) is str and len(value) == 64 and
            all(character in "0123456789abcdef" for character in value))


def make_trusted_context(authority: Mapping[str, Any]) -> TrustedNormalizationContext:
    """Validate an external authority/run-binding projection and mint a context."""
    require(type(authority) is dict, "CONTEXT-AUTHORITY-NOT-OBJECT")
    require(set(authority) == CONTEXT_AUTHORITY_FIELDS, "CONTEXT-AUTHORITY-SCHEMA")
    require(authority["context_version"] == CONTEXT_VERSION, "CONTEXT-VERSION")
    require(authority["authority_kind"] in AUTHORITY_KINDS, "CONTEXT-AUTHORITY-KIND")
    for field in ("expected_source_phase", "expected_run_id", "expected_artifact_namespace"):
        require(type(authority[field]) is str and bool(authority[field]), f"CONTEXT-{field.upper()}-TYPE")
    require(_sha256(authority["source_authority_digest"]), "CONTEXT-SOURCE-AUTHORITY-DIGEST")
    require(_sha256(authority["run_binding_digest"]), "CONTEXT-RUN-BINDING-DIGEST")
    return TrustedNormalizationContext(authority, _CONTEXT_SEAL)


def _checked_context(context: object) -> TrustedNormalizationContext:
    require(type(context) is TrustedNormalizationContext and
            context._seal is _CONTEXT_SEAL, "TRUSTED-CONTEXT-REQUIRED")
    return context


def _finite(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return all(_finite(v) for v in value)
    return True


def _state(step: Mapping[str, Any], env: int) -> Mapping[str, Any]:
    matches = [row for row in step["state_rows"] if row["env_id"] == env]
    require(len(matches) == 1, "P2-STATE-ROW-MISSING-OR-DUPLICATE")
    return matches[0]


def _selector_input(progress: Sequence[Mapping[str, Any]],
                    transactions: Sequence[Mapping[str, Any]],
                    bridges: Sequence[Mapping[str, Any]], expected_T: int,
                    initial_step: Mapping[str, Any] | None = None) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for update in progress:
        tx = update["transaction_index"]
        require(len(update["steps"]) == expected_T, "PHYSICAL-STEP-COUNT")
        for step in update["steps"]:
            require(step["transaction_index"] == tx, "PHYSICAL-STEP-TX-IDENTITY")
            steps.append(dict(step))
        for row in update["lifecycle_rows"]:
            physical = (tx - 1) * expected_T + row["physical_step_index"]
            decisions.append({**row, "global_physical_step": physical})
    require([step["global_physical_step"] for step in steps] == list(range(1, len(steps) + 1)),
            "PHYSICAL-STEP-ORDER-OR-MISSING")
    if initial_step is not None:
        require(initial_step["global_physical_step"] == 0 and
                initial_step["transaction_index"] == 1,
                "INITIAL-P2-SNAPSHOT-IDENTITY")
        steps.insert(0, dict(initial_step))
    return {"steps": steps, "decisions": decisions,
            "transactions": list(transactions), "bridges": list(bridges)}


def _completion_count(progress: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    events = 0
    p2_delta = 0
    previous: dict[tuple[int, int, int], int] = {}
    for update in progress:
        for step in update["steps"]:
            events += sum(event["event"] == "task_completed" for event in step["events"])
            for state in step["state_rows"]:
                for robot, value in enumerate(state["completion_count"]):
                    key = (state["env_id"], state["episode_generation"], robot)
                    old = previous.get(key)
                    if old is not None:
                        require(value >= old, "P2-COMPLETION-COUNTER-REGRESSION")
                        p2_delta += value - old
                    previous[key] = value
    require(events == p2_delta, "TASK-COMPLETED-EVENT-P2-DELTA-MISMATCH")
    return events, p2_delta


def _terminal(progress: Sequence[Mapping[str, Any]],
              terminal_rows: Sequence[Mapping[str, Any]],
              transactions: Sequence[Mapping[str, Any]]) -> tuple[int, bool, bool]:
    require(len(terminal_rows) == len(transactions), "TERMINAL-LEDGER-COUNT")
    observed_total = 0
    reason_pass = True
    post_reset = False
    for index, row in enumerate(terminal_rows):
        require(row["transaction_index"] == index + 1 and row["pass"] is True,
                "TERMINAL-LEDGER-ORDER-OR-FAIL")
        counts = row["reason_counts"]
        require(set(counts) == {"NONE", "TIME_LIMIT", "ALL_TASKS_COMPLETED",
                                "NO_FEASIBLE_TASKS_REMAIN"}, "TERMINAL-REASON-VOCABULARY")
        count = sum(value for reason, value in counts.items() if reason != "NONE")
        require(count == len(row["observed_keys"]) == len(row["expected_keys"]) and
                not row["missing"] and not row["extra"] and not row["duplicates"],
                "TERMINAL-RAW-RECONCILIATION")
        observed_total += count
        if count and index + 1 < len(transactions):
            current = progress[index]["steps"]
            following = progress[index + 1]["steps"]
            before = {s["env_id"]: s["episode_generation"] for s in current[0]["state_rows"]}
            after = {s["env_id"]: s["episode_generation"] for s in current[-1]["state_rows"]}
            next_generation = {s["env_id"]: s["episode_generation"] for s in following[0]["state_rows"]}
            if any(after[env] > before[env] and next_generation[env] == after[env]
                   for env in before if env in after and env in next_generation):
                post_reset = bool(transactions[index + 1]["s7_s8_s9_s10"] == [True] * 4 and
                                  transactions[index + 1]["finite"] is True)
    return observed_total, reason_pass, post_reset


def _plans(final: Mapping[str, Any], transactions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    raw_txs = final["transactions"]
    require(len(raw_txs) == len(transactions), "LEARNER-RAW-TRANSACTION-COUNT")
    result = {name: 0 for name in ("actor_backward_planned", "actor_backward",
                                  "actor_step_planned", "actor_step",
                                  "critic_backward_planned", "critic_backward",
                                  "critic_step_planned", "critic_step",
                                  "valid_nonzero_update", "valid_zero_effective_update",
                                  "valuenorm_expected", "valuenorm_update")}
    for index, (raw, row) in enumerate(zip(raw_txs, transactions, strict=True), 1):
        audit = raw["transaction"]["real_audit"]
        require(row["transaction_index"] == index, "LEARNER-TX-IDENTITY")
        result["actor_backward_planned"] += sum(count for _, count in audit["actor_expected_backward"])
        result["actor_step_planned"] += sum(count for _, count in audit["actor_expected_step"])
        result["critic_backward_planned"] += audit["critic_expected_backward"]
        result["critic_step_planned"] += audit["critic_expected_step"]
        result["valuenorm_expected"] += audit["valuenorm_expected_update"]
        result["actor_backward"] += sum(row["actor_backward_by_actor"])
        result["actor_step"] += sum(row["actor_optimizer_step_by_actor"])
        result["critic_backward"] += row["critic_backward"]
        result["critic_step"] += row["critic_optimizer_step"]
        result["valid_nonzero_update"] += row["valid_nonzero"]
        result["valid_zero_effective_update"] += row["valid_zero_effective"]
        result["valuenorm_update"] += row["valuenorm_update"]
    require(all(result[name] == result[name + "_planned"] for name in
                ("actor_backward", "actor_step", "critic_backward", "critic_step")),
            "LEARNER-PLAN-OBSERVED-MISMATCH")
    require(result["valid_nonzero_update"] + result["valid_zero_effective_update"] ==
            result["critic_step"] == result["valuenorm_expected"] == result["valuenorm_update"],
            "LEARNER-CRITIC-CLASS-VALUENORM-MISMATCH")
    persistent = final["persistent_learner_identity"]
    final_state = persistent["final"]
    result["actor_adam_continuity"] = persistent["object_ids_stable"] is True
    result["critic_adam_continuity"] = persistent["object_ids_stable"] is True
    result["valuenorm_continuity"] = (persistent["object_ids_stable"] is True and
                                    final_state["valuenorm_object_id"] ==
                                    persistent["initial"]["valuenorm_object_id"] and
                                    final_state["valuenorm_state_finite"] is True)
    result["numerical_health"] = all(final_state[name] is True for name in
                                     ("actor_parameters_finite", "actor_optimizer_states_finite",
                                      "critic_parameters_finite", "critic_optimizer_state_finite",
                                      "valuenorm_state_finite", "gradients_clean"))
    require(all(result[name] is True for name in ("actor_adam_continuity",
                                                  "critic_adam_continuity",
                                                  "valuenorm_continuity", "numerical_health")),
            "LEARNER-CONTINUITY-OR-NUMERICS")
    return result


def normalize(raw: Mapping[str, Any], *, trusted_context: TrustedNormalizationContext,
              config: Mapping[str, int],
              w2_selector: Callable[[Mapping[str, Any]], dict[str, Any]],
              pw_verify: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    """Return source-bound normalized evidence after exact raw reconciliation."""
    require(type(raw) is dict and callable(w2_selector) and callable(pw_verify),
            "EXPLICIT-NORMALIZATION-DEPENDENCIES")
    context = _checked_context(trusted_context)
    require(raw["source_phase"] == context.expected_source_phase, "FRESH-SOURCE-PHASE")
    require(raw["run_id"] == context.expected_run_id, "FRESH-RUN-ID")
    if "artifact_namespace" in raw:
        require(raw["artifact_namespace"] == context.expected_artifact_namespace,
                "FRESH-ARTIFACT-NAMESPACE")
    n, t = config["expected_transaction_count"], config["expected_T"]
    tx, bridges, progress = raw["transactions"], raw["bridges"], raw["progress"]
    require(len(tx) == len(progress) == n and len(bridges) == n - 1, "RAW-LEDGER-COUNTS")
    require(all(row["transaction_index"] == i and row["s7_s8_s9_s10"] == [True] * 4 and
                row["finite"] is True for i, row in enumerate(tx, 1)), "TX-ORDER-OR-QUALIFICATION")
    require(all(row["bridge_index"] == i and row["pass"] is True and
                row["from_update_id"] == tx[i - 1]["update_id"] and
                row["to_update_id"] == tx[i]["update_id"] for i, row in enumerate(bridges, 1)),
            "BRIDGE-DISCONTINUITY")
    require(all(row["transaction_index"] == i and row["update_id"] == tx[i - 1]["update_id"]
                for i, row in enumerate(progress, 1)), "PROGRESS-LEDGER-IDENTITY")
    w2_input = _selector_input(progress, tx, bridges, t, raw.get("initial_step"))
    physical = len(w2_input["steps"]) - int("initial_step" in raw)
    require(physical == n * t, "PHYSICAL-COUNT")
    w2 = w2_selector(w2_input)
    require(w2["pass"] is True and w2["selected"] is not None and
            w2["candidate_count"] >= 1 and 1 <= w2["valid_count"] <= w2["candidate_count"],
            "W2E-RAW-SELECTOR")
    candidates = raw["witnesses"]
    retained_w2 = candidates["W2_MULTI_UPDATE_COMPLETION"]
    require(retained_w2["pass"] is True and retained_w2["selected"] == w2["selected"] and
            retained_w2["candidate_count"] == w2["candidate_count"] and
            retained_w2["valid_count"] == w2["valid_count"], "W2-MANUAL-OVERRIDE-OR-DRIFT")
    task_completed, completion_delta = _completion_count(progress)
    coverage = max(state["coverage_count"] for update in progress
                   for step in update["steps"] for state in step["state_rows"])
    terminals, priority, post_reset = _terminal(progress, raw["terminal"], tx)
    require(task_completed >= 1 and completion_delta > 0 and coverage > 0 and
            terminals >= 1 and post_reset, "TASK-TERMINAL-PROGRESS")
    require(len(raw["immutability"]) == n and all(row["transaction_index"] == i and
            row["equal"] is True for i, row in enumerate(raw["immutability"], 1)),
            "W7-RAW-IMMUTABILITY")
    require(len(raw["actor_reconciliation"]) == n and all(row["transaction_index"] == i and
            row["exact_match"] is True and row["faults"] == 0
            for i, row in enumerate(raw["actor_reconciliation"], 1)), "ACTOR-EVIDENCE")
    learner = _plans(raw["final"], tx)
    require(all(row["finite"] is True for row in tx) and _finite(raw["training_metrics"]),
            "NUMERICAL-LEDGER-HEALTH")
    pw = dict(pw_verify())
    require(pw["contract_version"] == "b2_t4_ppq_fresh_campaign_pw_result_v2" and
            pw["run_id"] == raw["run_id"] and pw["transaction_count"] == n and
            pw["critic_actual"] == n * config["critic_records_per_tx"] and
            pw["actor_factor_actual"] == n * config["actor_factor_records_per_tx"] and
            all(pw[k] == 0 for k in ("missing_count", "duplicate_count", "order_fault_count",
                                    "digest_fault_count", "temp_residue_count")), "PW-VERIFIER-MISMATCH")
    source_keys = {"W1": "W1_CROSS_UPDATE_OWNERSHIP", "W3": "W3_ZERO_DVM_ACTOR",
                   "W4": "W4_NONTERMINAL_BOOTSTRAP", "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
                   "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY"}
    witnesses = {name: dict(candidates[source]) for name, source in source_keys.items()}
    witnesses["W2E"] = {"pass": True, "selected": w2["selected"]}
    witnesses["W7"]["qualified_count"] = sum(row["equal"] is True for row in raw["immutability"])
    require(all(witnesses[name]["pass"] is True for name in witnesses) and
            witnesses["W7"]["qualified_count"] == n, "W1-W7-RAW-WITNESSES")
    event_returns = sum(row["event_returns"] for row in tx)
    stock_returns = sum(row["stock_compute_returns"] for row in tx)
    derived = {"transaction_count": len(tx), "physical_transitions": physical,
               "production_s10": sum(row["s7_s8_s9_s10"][3] is True for row in tx),
               "transaction_ledger_count": len(tx), "bridge_count": len(bridges),
               "task_completed_count": task_completed, "completion_delta": completion_delta,
               "coverage_max": coverage, "terminal_autoreset_count": terminals,
               "post_autoreset_learned_transaction": post_reset,
               "pw_critic_actual": pw["critic_actual"],
               "pw_actor_factor_actual": pw["actor_factor_actual"],
               "w2e_candidate_count": w2["candidate_count"],
               "w2e_valid_count": w2["valid_count"], "w2e_selected": w2["selected"],
               "actor_backward": learner["actor_backward"], "actor_step": learner["actor_step"],
               "critic_backward": learner["critic_backward"], "critic_step": learner["critic_step"],
               "valuenorm_update": learner["valuenorm_update"],
               "event_returns": event_returns, "stock_compute_returns": stock_returns}
    for field, asserted in raw.get("summary_claims", {}).items():
        require(field in derived and derived[field] == asserted, f"RAW-SUMMARY-MISMATCH-{field}")
    counts = raw["final"]["exact_execution_counts"]
    for field, raw_field in (("transaction_count", "successful_full_transactions"),
                             ("physical_transitions", "real_rollout_steps"),
                             ("production_s10", "s10_pass"),
                             ("bridge_count", "s10_to_next_s0_bridges"),
                             ("terminal_autoreset_count", "terminal_autoreset_events"),
                             ("actor_backward", "actor_backward_total"),
                             ("actor_step", "actor_optimizer_step_total"),
                             ("critic_backward", "critic_backward_total"),
                             ("critic_step", "critic_optimizer_step_total"),
                             ("valuenorm_update", "valuenorm_update_total"),
                             ("event_returns", "event_return_computations"),
                             ("stock_compute_returns", "stock_compute_returns")):
        require(derived[field] == counts[raw_field], f"FINAL-RAW-COUNT-MISMATCH-{field}")
    require(counts["transaction_161_started"] == 0 and len(tx) == n, "TX161-STARTED")
    normalized = {"source_phase": context.expected_source_phase, "run_id": raw["run_id"],
                  "worker_pid": raw["worker_pid"], "transactions": list(tx),
                  "bridges": list(bridges), "physical_transitions": physical,
                  "production_s10": derived["production_s10"],
                  "transaction_ledger_count": len(tx), "bridge_count": len(bridges),
                  "tx161_started": False, "w2e_input": w2_input,
                  "retained_w2e_inventory": w2, "witnesses": witnesses,
                  "task_completed_count": task_completed,
                  "completion_delta": completion_delta, "coverage_max": coverage,
                  "terminal_autoreset_count": terminals,
                  "terminal_reason_priority_pass": priority,
                  "post_autoreset_learned_transaction": post_reset,
                  "pw_result": pw, "learner": learner,
                  "event_returns": event_returns, "stock_compute_returns": stock_returns,
                  "partial_update": raw["partial_update"],
                  "route_poisoned": raw["route_poisoned"],
                  "checkpoint_io_count": raw["checkpoint_io_count"],
                  "public_activation_count": raw["public_activation_count"],
                  "evaluation_playback_count": raw["evaluation_playback_count"]}
    return {"normalized": normalized, "derived": derived,
            "crosscheck_pass": True, "w2e": w2,
            "raw_sources": {"transactions": len(tx), "bridges": len(bridges),
                            "physical_steps": physical, "lifecycle_updates": len(progress),
                            "terminal_rows": len(raw["terminal"]),
                            "actor_reconciliation_rows": len(raw["actor_reconciliation"]),
                            "immutability_rows": len(raw["immutability"])}}
