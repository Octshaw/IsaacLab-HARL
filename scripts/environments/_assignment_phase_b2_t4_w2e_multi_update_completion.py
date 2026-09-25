"""Pure, fail-closed W2E evidence reconciler; no Isaac or learner imports.

Input is normalized copies of retained lifecycle, transaction and bridge ledgers.
This is a new versioned retrospective contract, not the historical RE5 W2 gate.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


CONTRACT_VERSION = "b2_t4_w2e_multi_update_completion_v2"
ACTIVE_TASK_STATES = (1, 2, 3)  # CLAIMED, NAVIGATING, ALIGNING
AVAILABLE = 0
COMPLETED = 4
EXECUTING = 0
NEEDS_ASSIGNMENT = 1
NO_OWNER = -1


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _state(step: Mapping[str, Any] | None, env: int) -> Mapping[str, Any] | None:
    if step is None:
        return None
    return next((row for row in step["state_rows"] if int(row["env_id"]) == env), None)


def _qualified(tx: int, transactions: Mapping[int, Mapping[str, Any]]) -> bool:
    row = transactions.get(tx)
    return bool(row and list(row["s7_s8_s9_s10"]) == [True] * 4 and row["finite"])


def _evaluate_pair(
    claim: Mapping[str, Any],
    completion: Mapping[str, Any],
    steps: Mapping[int, Mapping[str, Any]],
    decisions: Mapping[tuple[int, int, int], Mapping[str, Any]],
    decision_multiplicity: Counter[tuple[int, int, int]],
    transactions: Mapping[int, Mapping[str, Any]],
    bridges: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    env, robot, task = (int(claim[key]) for key in ("env_index", "robot_index", "ownership_after"))
    claim_step = int(claim["global_physical_step"])
    claim_tx = int(claim["transaction_index"])
    complete_step = int(completion["global_physical_step"])
    complete_tx = int(completion["transaction_index"])
    gen = int(claim["episode_generation"])
    errors: list[str] = []
    layers: dict[str, bool] = {}
    claim_step_row = steps.get(claim_step)
    pre = _state(steps.get(claim_step - 1), env)
    post = _state(claim_step_row, env)

    def require(ok: bool, reason: str) -> None:
        if not ok:
            errors.append(reason)

    # A: proposal is insufficient; exact before/after P2 and admitted effective
    # assignment must concur. The first/reset step is intentionally not inferred.
    a_start = len(errors)
    require(decision_multiplicity[(claim_step, env, robot)] == 1, "duplicate_or_ambiguous_claim_decision")
    require(int(claim.get("collection_index", -1)) == claim_step, "claim_observer_step_identity_stale")
    require(claim.get("decision_reason") == "POLICY_DECISION_ROW", "claim_not_policy_decision")
    require(claim.get("decision_required") is True and int(claim.get("actor_policy_call_count", -1)) == 1, "claim_policy_call_invalid")
    require(claim.get("proposal_produced") is True, "claim_proposal_missing")
    require(claim.get("ownership_before") is None, "claim_is_continuation")
    require(claim_step_row is not None and int(claim_step_row["effective_assignment"][env][robot]) == task, "claim_not_effective_assignment")
    require(pre is not None, "claim_pre_p2_missing")
    if pre is not None:
        require(int(pre["episode_generation"]) == gen, "claim_episode_generation_mismatch")
        require(int(pre["task_state"][task]) == AVAILABLE and int(pre["ownership"][task]) == NO_OWNER, "claim_pre_task_not_available_unowned")
        require(robot not in [int(value) for value in pre["ownership"]], "claim_robot_previously_owned_task")
    require(post is not None, "claim_post_p2_missing")
    if post is not None:
        require(int(post["episode_generation"]) == gen, "claim_post_generation_mismatch")
        require(int(post["ownership"][task]) == robot and int(post["task_state"][task]) in ACTIVE_TASK_STATES, "claim_post_p2_not_owned_active")
        require(int(post["robot_state"][robot]) == EXECUTING and int(post["next_owned_task"][robot]) == task, "claim_post_robot_not_executing_task")
    require(_qualified(claim_tx, transactions), "claim_transaction_not_qualified")
    layers["A_claim_authority"] = len(errors) == a_start

    # B: every intervening post-transition P2 row must preserve the exact owner;
    # an intact, qualified bridge with forced continuation must exist strictly
    # before completion. This rejects release/reassign and reset joins.
    b_start = len(errors)
    require(claim_tx < complete_tx, "claim_completion_same_or_reverse_transaction")
    require(complete_step > claim_step, "completion_not_after_claim")
    for physical_step in range(claim_step, complete_step):
        step = steps.get(physical_step)
        row = _state(step, env)
        if row is None:
            require(False, "continuity_state_missing")
            break
        if any(
            event["event"] in ("task_released", "terminal_pair_failure_recorded", "task_completed")
            and int(event["env_id"]) == env
            and int(event["task_id"]) == task
            and int(event.get("robot_id", robot)) in (robot, -1)
            for event in step["events"]
        ):
            require(False, "release_failure_or_early_completion_event")
        if not (
            int(row["episode_generation"]) == gen
            and int(row["ownership"][task]) == robot
            and int(row["task_state"][task]) in ACTIVE_TASK_STATES
            and int(row["robot_state"][robot]) == EXECUTING
            and int(row["next_owned_task"][robot]) == task
        ):
            require(False, "release_reassign_or_generation_break")
            break
    qualifying_boundaries: list[int] = []
    for boundary_tx in range(claim_tx, complete_tx):
        next_step = 2 * boundary_tx + 1
        if next_step >= complete_step:
            continue
        bridge = bridges.get(boundary_tx)
        left, right = transactions.get(boundary_tx), transactions.get(boundary_tx + 1)
        decision = decisions.get((next_step, env, robot))
        if not (
            bridge and left and right and bool(bridge["pass"])
            and steps.get(next_step) is not None
            and steps.get(next_step - 1) is not None
            and int(steps[next_step]["transaction_index"]) == boundary_tx + 1
            and int(steps[next_step - 1]["transaction_index"]) == boundary_tx
            and bool(bridge["persistent_object_identity"])
            and bool(bridge["learner_post_to_pre_exact"])
            and bool(bridge["collection_preserved_learner"])
            and bool(bridge["next_s0_established"])
            and bridge["from_update_id"] == left["update_id"]
            and bridge["to_update_id"] == right["update_id"]
            and _qualified(boundary_tx, transactions)
            and _qualified(boundary_tx + 1, transactions)
            and decision
            and int(decision.get("collection_index", -1)) == next_step
            and decision["decision_reason"] == "FORCED_CONTINUATION_ROW"
            and decision["decision_required"] is False
            and int(decision["actor_policy_call_count"]) == 0
            and decision["continuation_used"] is True
            and decision["ownership_before"] == task
            and decision["ownership_after"] == task
            and decision_multiplicity[(next_step, env, robot)] == 1
        ):
            require(False, "qualified_bridge_or_continuation_mismatch")
            continue
        qualifying_boundaries.append(boundary_tx)
    require(bool(qualifying_boundaries), "no_qualified_precompletion_update_boundary")
    layers["B_ownership_continuity"] = len(errors) == b_start

    # C: an independent exact completion event and monotone per-robot count.
    c_start = len(errors)
    before_completion = _state(steps.get(complete_step - 1), env)
    completed = _state(steps.get(complete_step), env)
    require(completed is not None, "completion_post_p2_missing")
    require(before_completion is not None, "completion_pre_p2_missing")
    if completed is not None:
        require(int(completed["episode_generation"]) == gen, "completion_episode_generation_mismatch")
        require(int(completed["task_state"][task]) == COMPLETED, "completion_task_state_not_completed")
    if before_completion is not None and completed is not None:
        require(int(before_completion["completion_count"][robot]) + 1 == int(completed["completion_count"][robot]), "completion_count_not_incremented")
    require(_qualified(complete_tx, transactions), "completion_transaction_not_qualified")
    layers["C_completion_authority"] = len(errors) == c_start

    # D: completion must clear both the P2 owner and inverse current-task view.
    d_start = len(errors)
    if completed is not None:
        require(int(completed["ownership"][task]) == NO_OWNER, "completed_owner_not_cleared")
        require(int(completed["next_owned_task"][robot]) != task, "robot_still_points_to_completed_task")
    layers["D_ownership_clear"] = len(errors) == d_start

    # E: the same robot's post-completion DVM must reopen and the immediately
    # following decision row must actually be policy-eligible/called once.
    e_start = len(errors)
    reopen_step = complete_step + 1
    reopen = decisions.get((reopen_step, env, robot))
    if completed is not None:
        require(int(completed["robot_state"][robot]) == NEEDS_ASSIGNMENT, "robot_not_needs_assignment_after_completion")
        require(completed["next_decision_required"][robot] is True, "decision_not_reopened_after_completion")
    require(reopen is not None, "reopen_decision_row_missing")
    if reopen is not None:
        require(int(reopen.get("collection_index", -1)) == reopen_step, "reopen_observer_step_identity_stale")
        require(int(reopen["episode_generation"]) == gen, "reopen_episode_generation_mismatch")
        require(reopen["decision_reason"] == "POLICY_DECISION_ROW" and reopen["decision_required"] is True and int(reopen["actor_policy_call_count"]) == 1, "reopen_policy_evidence_missing")
        require(reopen["ownership_before"] is None, "reopen_robot_still_owned")
        require(decision_multiplicity[(reopen_step, env, robot)] == 1, "reopen_decision_ambiguous")
    layers["E_decision_reopen"] = len(errors) == e_start

    pointers = {
        "claim": {"ledger": "lifecycle_task_progress", "transaction_index": claim_tx, "physical_step": claim_step},
        "completion": {"ledger": "lifecycle_task_progress", "transaction_index": complete_tx, "physical_step": complete_step},
        "first_bridge": None if not qualifying_boundaries else {"ledger": "bridge", "bridge_index": qualifying_boundaries[0]},
        "reopen": {"ledger": "lifecycle_task_progress", "physical_step": reopen_step},
    }
    return {
        "env_id": env, "robot_id": robot, "task_id": task, "episode_generation": gen,
        "claim_tx": claim_tx, "claim_physical_step": claim_step,
        "completion_tx": complete_tx, "completion_physical_step": complete_step,
        "first_bridge": None if not qualifying_boundaries else qualifying_boundaries[0],
        "continuation_bridge_txs": qualifying_boundaries,
        "reopen_tx": None if reopen is None else int(reopen["transaction_index"]),
        "reopen_physical_step": reopen_step,
        "ownership_clear": None if completed is None else int(completed["ownership"][task]) == NO_OWNER,
        "state_digests": {
            "pre_claim": None if pre is None else _digest(pre),
            "post_claim": None if post is None else _digest(post),
            "pre_completion": None if before_completion is None else _digest(before_completion),
            "post_completion": None if completed is None else _digest(completed),
        },
        "artifact_pointers": pointers,
        "layers": layers,
        "fail_reasons": list(dict.fromkeys(errors)),
        "pass": not errors,
    }


def reconcile(evidence: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """Return every candidate and the deterministic first valid witness.

    The caller supplies normalized ledger dictionaries and retains read/identity
    responsibility. No module import or call touches runtime state or the FS.
    """
    steps = {int(row["global_physical_step"]): row for row in evidence["steps"]}
    transactions = {int(row["transaction_index"]): row for row in evidence["transactions"]}
    bridges = {int(row["bridge_index"]): row for row in evidence["bridges"]}
    decisions: dict[tuple[int, int, int], Mapping[str, Any]] = {}
    multiplicity: Counter[tuple[int, int, int]] = Counter()
    for row in evidence["decisions"]:
        key = (int(row["global_physical_step"]), int(row["env_index"]), int(row["robot_index"]))
        multiplicity[key] += 1
        decisions.setdefault(key, row)
    completions = []
    for step in evidence["steps"]:
        for event in step["events"]:
            if event["event"] == "task_completed":
                completions.append({**event, "global_physical_step": step["global_physical_step"], "transaction_index": step["transaction_index"]})
    claim_edges = [
        row for row in evidence["decisions"]
        if row.get("ownership_before") is None and type(row.get("ownership_after")) is int
    ]
    inventory = []
    for claim in claim_edges:
        matches = [
            event for event in completions
            if int(event["env_id"]) == int(claim["env_index"])
            and int(event["robot_id"]) == int(claim["robot_index"])
            and int(event["task_id"]) == int(claim["ownership_after"])
            and int(event["global_physical_step"]) > int(claim["global_physical_step"])
        ]
        if not matches:
            inventory.append({
                "env_id": claim["env_index"], "robot_id": claim["robot_index"],
                "task_id": claim["ownership_after"], "claim_tx": claim["transaction_index"],
                "claim_physical_step": claim["global_physical_step"], "pass": False,
                "layers": {"A_claim_authority": False, "B_ownership_continuity": False, "C_completion_authority": False, "D_ownership_clear": False, "E_decision_reopen": False},
                "fail_reasons": ["same_identity_completion_missing"],
            })
        for event in matches:
            inventory.append(_evaluate_pair(claim, event, steps, decisions, multiplicity, transactions, bridges))
    inventory.sort(key=lambda row: (int(row["claim_tx"]), int(row["claim_physical_step"]), int(row.get("completion_tx", 10**9)), int(row["env_id"]), int(row["robot_id"]), int(row["task_id"])))
    valid = [row for row in inventory if row["pass"]]
    return {
        "schema_version": CONTRACT_VERSION,
        "selection_order": "claim_tx,claim_physical_step,completion_tx,env_id,robot_id,task_id ascending",
        "claim_edge_count": len(claim_edges),
        "completion_event_count": len(completions),
        "candidate_count": len(inventory),
        "valid_count": len(valid),
        "inventory": inventory,
        "selected": valid[0] if valid else None,
        "pass": bool(valid),
    }


__all__ = ("CONTRACT_VERSION", "reconcile")
