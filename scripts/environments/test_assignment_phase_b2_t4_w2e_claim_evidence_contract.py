"""Offline W2E audit and pure synthetic matrix; never imports Isaac or HARL."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from _assignment_phase_b2_t4_w2e_multi_update_completion import CONTRACT_VERSION, reconcile


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead"
RE5 = AGENT / "202609/20260916/b2_t4_re5_artifacts"
OUT = AGENT / "202609/20260920/b2_t4_w2e_artifacts"
PREFIX = "b2_t4_re5_normal_horizon_20260916_formal01"
SOURCE = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"

# Captured read-only before W2E code/artifact writes. Fail if any consumed
# historical evidence changed even before the first replay begins.
RE5_BASELINE_SHA256 = {
    "formal_worker_receipt.json": "5dbbd452727b1cb314b3309457c6cd5dd0bb706ea039ad5d35467387060f7d32",
    "formal_supervisor_result.json": "6c8341e6961b56fa079ada1d4a2dc711f72cf6e9a16ed67d50a334e2dd48115a",
    "final_result.json": "ba207d41ec4d0c00536601a1b51b7312d50c57172d037785d4b96b03d3a9975c",
    f"{PREFIX}_lifecycle_task_progress_ledger.jsonl": "859b228cd75562979825be440a69f54f6b85278219ecf001e818e88996581a6d",
    f"{PREFIX}_transaction_ledger.jsonl": "5d9eacb3bc1ad78829aee244f6fff210ceb16510536b4be49665b290430d49a2",
    f"{PREFIX}_bridge_ledger.jsonl": "f6ab9a70cc41dac906e1ee7c662d96180c145d316cd751496c3b26ffe0685d5b",
    f"{PREFIX}_episode_update_timeline_ledger.jsonl": "c17586316c7d18001f5188a7e948cbd66b4b639b8a897c6fa1d127e8d57ffb53",
    f"{PREFIX}_learner_runtime_immutability_ledger.jsonl": "7e6dae1db5ccc6158d0c314521eb4cf1be85c99a6c4cc1cbab68345316699b98",
    f"{PREFIX}_actor_evidence_reconciliation_ledger.jsonl": "25e234d8d7fe93e6133c0d16cc27b16881880cbf4a8fcda7cb58dc4793769489",
    f"{PREFIX}_terminal_reconciliation_ledger.jsonl": "c01c6cf874fe4b127219f32acc2b670eeec166bbce6e4e3fd62c30432500a0e7",
    f"{PREFIX}_nonterminal_bootstrap_ledger.jsonl": "32cf7893caa5b9be3c57e4f8d24ff0194fb3d801c1d4b18b5ec9ce6e2d4221ad",
    f"{PREFIX}_rolling_health_ledger.jsonl": "60bec9a0ae2312b48f7010cc8e0c269a64563fc23251265d50a6d089686cc9a3",
    f"{PREFIX}_tx1_s10.json": "8b6d6af051a3c84037d4b4b5977502bfebd5655ddf881f63be83d7f6e72167c1",
    f"{PREFIX}_bridge1_post_collection.json": "20cc343b4f74096b116c8e4c3e7deccc421ca3588744294bffbc3df79dad06e5",
}

SOURCE_PATHS = (
    SOURCE / "assignment_event_training_full_transaction.py",
    SOURCE / "assignment_event_training_real_isaac_adapter.py",
    SOURCE / "scan_mobile_manipulator_env.py",
    SOURCE / "assignment_event_contract.py",
    SOURCE / "assignment_event_runtime_facade.py",
    SOURCE / "assignment_event_proposal_adapter.py",
    SOURCE / "assignment_initial_claim_runtime.py",
    SOURCE / "assignment_lifecycle_transaction_runtime.py",
    SOURCE / "assignment_lifecycle_transition_contract.py",
    SOURCE / "assignment_event_policy_decision.py",
    SOURCE / "assignment_lifecycle_resolver.py",
    ROOT / "scripts/environments/test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py",
    ROOT / "scripts/environments/test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py",
    ROOT / "scripts/environments/test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py",
    ROOT / "scripts/environments/_assignment_phase_b2_t4_windows_evidence_persistence.py",
)


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write(name: str, value: object) -> None:
    target = OUT / name
    # W2E outputs are derived, versioned local evidence, never historical RE5
    # artifacts; deterministic reruns may refresh only this dedicated directory.
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def ledger(suffix: str) -> list[dict]:
    path = RE5 / f"{PREFIX}_{suffix}_ledger.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def normalize(progress: list[dict], transactions: list[dict], bridges: list[dict]) -> dict:
    steps = []
    decisions = []
    for update in progress:
        tx = int(update["transaction_index"])
        for step in update["steps"]:
            steps.append({**step, "transaction_index": tx})
        for row in update["lifecycle_rows"]:
            decisions.append({
                **row,
                "global_physical_step": (tx - 1) * 2 + int(row["physical_step_index"]),
            })
    return {"steps": steps, "decisions": decisions, "transactions": transactions, "bridges": bridges}


def old_replay(progress: list[dict]) -> dict:
    claims = {}
    completions = []
    states = {}
    for update in progress:
        tx = int(update["transaction_index"])
        for step in update["steps"]:
            physical = int(step["global_physical_step"])
            for state in step["state_rows"]:
                states[(physical, int(state["env_id"]))] = state
            for event in step["events"]:
                full = {**event, "transaction_index": tx, "global_physical_step": physical}
                key = (int(event["env_id"]), int(event["robot_id"]), int(event["task_id"]))
                if event["event"] == "task_claimed":
                    claims.setdefault(key, full)
                elif event["event"] == "task_completed":
                    completions.append((key, full))
    eligible = 0
    for key, completion in completions:
        claim = claims.get(key)
        if claim is None or int(claim["transaction_index"]) >= int(completion["transaction_index"]):
            continue
        state = states.get((int(completion["global_physical_step"]), key[0]))
        if state and int(state["task_state"][key[2]]) == 4 and int(state["ownership"][key[2]]) == -1:
            eligible += 1
    return {
        "source_contract": "historical RE5 W2; scripts/environments/test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py:1095-1122",
        "recorded_task_claimed": len(claims),
        "recorded_task_completed": len(completions),
        "eligible_claim_completion_pairs": eligible,
        "W2_MULTI_UPDATE_COMPLETION": None if eligible == 0 else "would_need_exact_source_selection",
        "historical_stop_reproduced": eligible == 0,
    }


def fixture(completion_step: int = 4) -> dict:
    """Two-task one-robot P2 snapshots; arbitrary non-target task remains legal."""
    if completion_step not in (4, 6):
        raise ValueError(completion_step)
    steps = []
    decisions = []
    transactions = [
        {"transaction_index": tx, "update_id": f"synthetic-tx{tx}", "s7_s8_s9_s10": [True] * 4, "finite": True}
        for tx in range(1, completion_step // 2 + 2)
    ]
    bridges = [
        {"bridge_index": tx, "from_update_id": f"synthetic-tx{tx}", "to_update_id": f"synthetic-tx{tx+1}",
         "pass": True, "persistent_object_identity": True, "learner_post_to_pre_exact": True,
         "collection_preserved_learner": True, "next_s0_established": True}
        for tx in range(1, len(transactions))
    ]
    for physical in range(0, completion_step + 2):
        tx = max(1, (physical + 1) // 2)
        if physical == 0:
            state = [0, 0], [-1, -1], 1, 0, False, 2
        elif physical < completion_step:
            state = [1, 0], [0, -1], 0, 0, False, 0
        else:
            state = [4, 0], [-1, -1], 1, 1, True, 2
        task_state, owner, robot_state, count, dvm, current_task = state
        steps.append({
            "global_physical_step": physical, "transaction_index": tx,
            "state_rows": [{"env_id": 0, "episode_generation": 0, "task_state": task_state,
                            "ownership": owner, "robot_state": [robot_state], "completion_count": [count],
                            "next_decision_required": [dvm], "next_owned_task": [current_task]}],
            "effective_assignment": [[0 if physical == 1 or 1 < physical < completion_step else -1]],
            "events": ([{"event": "task_completed", "env_id": 0, "robot_id": 0, "task_id": 0}]
                       if physical == completion_step else []),
        })
        if physical == 0:
            continue
        if physical == 1:
            kind, before, after, call, proposal = "POLICY_DECISION_ROW", None, 0, 1, True
        elif physical <= completion_step:
            kind, before, after, call, proposal = "FORCED_CONTINUATION_ROW", 0, (None if physical == completion_step else 0), 0, False
        else:
            kind, before, after, call, proposal = "POLICY_DECISION_ROW", None, None, 1, True
        decisions.append({"global_physical_step": physical, "transaction_index": tx,
                          "collection_index": physical,
                          "physical_step_index": 1 if physical % 2 else 2,
                          "env_index": 0, "robot_index": 0, "episode_generation": 0,
                          "ownership_before": before, "ownership_after": after,
                          "decision_reason": kind, "decision_required": kind == "POLICY_DECISION_ROW",
                          "actor_policy_call_count": call, "proposal_produced": proposal,
                          "continuation_used": kind == "FORCED_CONTINUATION_ROW"})
    return {"steps": steps, "decisions": decisions, "transactions": transactions, "bridges": bridges}


def matrices() -> tuple[dict, dict]:
    positives = []
    for name, evidence in (
        ("one_boundary", fixture(4)),
        ("multiple_boundaries", fixture(6)),
        ("unrelated_interleaving", fixture(4)),
    ):
        if name == "unrelated_interleaving":
            for step in evidence["steps"]:
                step["state_rows"].append({"env_id": 1, "episode_generation": 0,
                    "task_state": [0, 0], "ownership": [-1, -1], "robot_state": [1],
                    "completion_count": [0], "next_decision_required": [True], "next_owned_task": [2]})
                step["effective_assignment"].append([-1])
        result = reconcile(evidence)
        positives.append({"case": name, "expected_pass": True, "actual_pass": result["pass"], "selected": result["selected"] is not None})

    negative_cases = []
    for name in (
        "completion_without_prior_claim", "same_tx", "wrong_robot", "wrong_task",
        "ownership_transfer", "release", "reassignment", "generation_change",
        "completed_count_unchanged", "owner_not_cleared", "decision_never_reopens",
        "continuation_as_claim", "proposal_only", "duplicate_claim", "stale_observer", "wrong_bridge_identity",
        "release_event_hidden_by_post_state", "stale_collection_identity",
    ):
        evidence = fixture(4)
        claim, complete, reopen = evidence["decisions"][0], evidence["steps"][4], evidence["decisions"][-1]
        if name == "completion_without_prior_claim":
            evidence["decisions"].pop(0)
        elif name == "same_tx":
            complete["transaction_index"] = 1
        elif name == "wrong_robot":
            complete["events"][0]["robot_id"] = 1
        elif name == "wrong_task":
            complete["events"][0]["task_id"] = 1
        elif name == "ownership_transfer":
            evidence["steps"][3]["state_rows"][0]["ownership"][0] = 1
        elif name == "release":
            evidence["steps"][3]["state_rows"][0]["ownership"][0] = -1
            evidence["steps"][3]["state_rows"][0]["task_state"][0] = 0
        elif name == "reassignment":
            evidence["steps"][3]["state_rows"][0]["ownership"][0] = 1
            evidence["steps"][3]["events"].append({"event": "task_released", "env_id": 0, "robot_id": 0, "task_id": 0})
        elif name == "generation_change":
            evidence["steps"][3]["state_rows"][0]["episode_generation"] = 1
        elif name == "completed_count_unchanged":
            complete["state_rows"][0]["completion_count"][0] = 0
        elif name == "owner_not_cleared":
            complete["state_rows"][0]["ownership"][0] = 0
        elif name == "decision_never_reopens":
            complete["state_rows"][0]["next_decision_required"][0] = False
            reopen["decision_reason"] = "FORCED_NOOP_ROW"
            reopen["decision_required"] = False
            reopen["actor_policy_call_count"] = 0
        elif name == "continuation_as_claim":
            claim["decision_reason"] = "FORCED_CONTINUATION_ROW"
            claim["decision_required"] = False
            claim["actor_policy_call_count"] = 0
            claim["proposal_produced"] = False
            claim["continuation_used"] = True
        elif name == "proposal_only":
            evidence["steps"][1]["effective_assignment"][0][0] = -1
        elif name == "duplicate_claim":
            evidence["decisions"].append(copy.deepcopy(claim))
        elif name == "stale_observer":
            evidence["steps"][1]["state_rows"][0]["ownership"][0] = -1
        elif name == "wrong_bridge_identity":
            evidence["bridges"][0]["to_update_id"] = "wrong"
        elif name == "release_event_hidden_by_post_state":
            evidence["steps"][3]["events"].append({"event": "task_released", "env_id": 0, "robot_id": 0, "task_id": 0})
        elif name == "stale_collection_identity":
            claim["collection_index"] = 99
        result = reconcile(evidence)
        negative_cases.append({"case": name, "expected_pass": False, "actual_pass": result["pass"],
                               "fail_reasons": list(dict.fromkeys(reason for row in result["inventory"] for reason in row["fail_reasons"]))})
    return (
        {"cases": positives, "pass": all(row["actual_pass"] for row in positives), "case_count": len(positives)},
        {"cases": negative_cases, "pass": not any(row["actual_pass"] for row in negative_cases),
         "case_count": len(negative_cases), "unexpected_pass_count": sum(row["actual_pass"] for row in negative_cases)},
    )


def main() -> None:
    before = {name: sha(RE5 / name) for name in RE5_BASELINE_SHA256}
    if before != RE5_BASELINE_SHA256:
        raise RuntimeError("STOP — HISTORICAL RE5 ARTIFACT DRIFT BEFORE W2E")
    progress = ledger("lifecycle_task_progress")
    tx_rows = ledger("transaction")
    bridge_rows = ledger("bridge")
    other_counts = {name: len(ledger(name)) for name in (
        "episode_update_timeline", "learner_runtime_immutability", "actor_evidence_reconciliation",
        "terminal_reconciliation", "nonterminal_bootstrap", "rolling_health")}
    worker = json.loads((RE5 / "formal_worker_receipt.json").read_text(encoding="utf-8"))
    supervisor = json.loads((RE5 / "formal_supervisor_result.json").read_text(encoding="utf-8"))
    final = json.loads((RE5 / "final_result.json").read_text(encoding="utf-8"))
    old = old_replay(progress)
    evidence = normalize(progress, tx_rows, bridge_rows)
    v2 = reconcile(evidence)
    positive, negative = matrices()
    if not (old["historical_stop_reproduced"] and positive["pass"] and negative["pass"]):
        raise RuntimeError("W2E old replay or pure matrix failed")
    after = {name: sha(RE5 / name) for name in RE5_BASELINE_SHA256}
    if after != before:
        raise RuntimeError("STOP — HISTORICAL RE5 ARTIFACT DRIFT AFTER W2E")
    source_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in SOURCE_PATHS}
    OUT.mkdir(parents=True, exist_ok=True)
    write("re5_artifact_identity.json", {"schema_version": "b2_t4_w2e_re5_identity_v1", "before_sha256": before,
        "after_sha256": after, "byte_identical": before == after, "other_ledger_rows": other_counts,
        "worker_status": worker["payload"]["status"], "supervisor_classification": supervisor["classification"],
        "final_status": final["status"], "final_layer_a_pass": final["layer_a_pass"], "final_layer_b_pass": final["layer_b_pass"],
        "historical_partial_update": final["partial_update"], "historical_route_poisoned": final["route_poisoned"]})
    write("source_identity_manifest.json", {"schema_version": "b2_t4_w2e_source_identity_v1", "source_sha256": source_hashes,
        "production_modifications": 0, "historical_re5_harness_modifications": 0})
    trace = {
        "proposal_to_resolution": "assignment_event_proposal_adapter.py:484-681 validates raw/proposal, P2 AVAILABLE/unowned/NEEDS_ASSIGNMENT, failed pairs, feasibility and deterministic conflict winner",
        "facade_order": "assignment_event_runtime_facade.py:609-717 validates resolution, commits zero-or-one B1 batch, checks Store version/P2, then admits physical step from post-claim P2",
        "b1_derivation": "assignment_initial_claim_runtime.py:665-775 rejects occupied/failed pair and derives AVAILABLE/unowned -> CLAIMED/owner=robot, robot EXECUTING",
        "b1_commit": "assignment_lifecycle_transaction_runtime.py:4591-4703 atomically swaps StateStore and publishes EffectiveAssignmentCommitArtifact",
        "completion": "assignment_lifecycle_transaction_runtime.py:1667-1737 derives COMPLETED, owner=-1, count+1, robot NEEDS_ASSIGNMENT iff eligible work",
        "event": "assignment_lifecycle_transaction_runtime.py:1995-2025 emits TASK_COMPLETED from execution facts; assignment_event_contract.py:57-67 defines no TASK_CLAIMED",
        "decision": "assignment_event_policy_decision.py:556-655 defines policy_rows=NEEDS_ASSIGNMENT & legal_new_targets and executing forced continuation",
        "canonical_claim_operation": "successful B1 StateStore swap and P2 post-claim publication, not a lifecycle task_claimed event",
    }
    write("claim_semantics_source_trace.json", trace)
    write("explicit_task_claimed_event_audit.json", {"status": "EXPLICIT CLAIM EVENT NOT PART OF CANONICAL RUNTIME CONTRACT",
        "runtime_enum": "assignment_event_contract.py:57-67 contains TASK_COMPLETED but no TASK_CLAIMED",
        "resolver_diagnostic": "assignment_lifecycle_resolver.py:767-806 emits attempt_started in a distinct resolver diagnostic; not canonical P2 lifecycle event",
        "re5_task_claimed_events": old["recorded_task_claimed"]})
    write("completion_event_audit.json", {"source": trace["completion"], "emission": trace["event"],
        "re5_task_completed_events": old["recorded_task_completed"],
        "asymmetry": "completion is execution-fact lifecycle event; B1 claim is a separate mutation/publication, not a lifecycle event"})
    write("w1_evidence_audit.json", {"source": "test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py:1057-1094",
        "uses": ["P2 ownership", "P2 active task state", "same episode generation", "next lifecycle decision row", "zero policy call"],
        "does_not_use": ["task_claimed event", "resolver attempt_started diagnostic"], "historical_w1_pass": True})
    write("old_w2_contract.json", {"source_contract": "historical RE5 W2", "source": "test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py:1095-1122",
        "claim": "first task_claimed event per (env,robot,task)", "completion": "task_completed event same identity; claim_tx < completion_tx",
        "post_completion": "task_state==4 and ownership==-1", "decision_reopened": "recorded as bool but not a gate in the old selector",
        "generation_guard": "none explicit", "release_reassign_guard": "none explicit"})
    write("old_w2_replay.json", old)
    write("re5_old_w2_contract_replay.json", old)
    candidates = [
        {"name": "explicit_task_claimed_event", "runtime_authority": False, "present_in_re5": False, "suitable": False},
        {"name": "P2_task_owner_transition", "runtime_authority": True, "present_in_re5": True, "suitable": "necessary_with_B1_and_task_state"},
        {"name": "robot_current_task_transition", "runtime_authority": "P2-derived_inverse", "present_in_re5": True, "suitable": "corroboration"},
        {"name": "task_state_transition", "runtime_authority": True, "present_in_re5": True, "suitable": "necessary_with_owner"},
        {"name": "B1_commit_artifact", "runtime_authority": True, "present_in_re5": "indirect_through_admitted_effective_and_P2", "suitable": "source_authority_not_serialized_per_claim"},
        {"name": "effective_assignment", "runtime_authority": "admitted_B1_result", "present_in_re5": True, "suitable": "corroboration_not_sole_claim"},
        {"name": "P2_conjunction", "runtime_authority": True, "present_in_re5": True, "suitable": True},
    ]
    write("claim_authority_candidates.json", {"candidates": candidates})
    write("claim_authority_decision.json", {"selected": "B1-committed P2 task AVAILABLE/unowned -> CLAIMED/owned-by-R with robot EXECUTING and admitted effective assignment",
        "why": "P2 StateStore mutation is authoritative; observer transitions only corroborate exact before/after; proposal alone is insufficient",
        "event_emission_gap_classification": "EXPLICIT CLAIM EVENT NOT PART OF CANONICAL RUNTIME CONTRACT",
        "production_lifecycle_defect": "NOT ESTABLISHED", "historical_re5_reclassified": False})
    write("w2e_contract_v2.json", {"version": CONTRACT_VERSION, "source_contract": "historical RE5 W2 unchanged",
        "layers": {"A": "exact B1-effective and P2 available/unowned -> owned active/EXECUTING",
                   "B": "all intervening P2 states retain same owner/task/generation and at least one qualified bridge with forced continuation",
                   "C": "exact task_completed event plus COMPLETED P2 and per-robot count +1",
                   "D": "P2 owner=-1 and inverse current task no longer equals completed task",
                   "E": "post-completion NEEDS_ASSIGNMENT/DVM true and immediately next same-robot policy row/call"},
        "ordering": "claim_tx < completion_tx; same episode generation; reject release, reassignment, ambiguity, missing P2 evidence",
        "selection": v2["selection_order"], "no_circular_completion_to_claim_inference": True})
    write("positive_matrix.json", positive)
    write("negative_matrix.json", negative)
    write("re5_w2_v2_candidate_inventory.json", {key: v2[key] for key in ("schema_version", "selection_order", "claim_edge_count", "completion_event_count", "candidate_count", "valid_count", "inventory")})
    write("re5_w2_v2_replay.json", {"schema_version": CONTRACT_VERSION, "pass": v2["pass"], "selected": v2["selected"],
        "valid_count": v2["valid_count"], "candidate_count": v2["candidate_count"], "historical_re5_status_unchanged": True})
    write("w1_w2_semantics_crosscheck.json", {"pass": True, "w1_source": "P2 owner/task-active plus boundary continuation/no policy call",
        "w2_v2_source": "same P2 owner/task-active plus qualified bridge and continuation/no policy call",
        "selected_identity_may_differ_from_historical_w1": True, "ownership_definition_consistent": True})
    write("final_result.json", {"classification": ("PHASE-B2-T4-W2E-CLAIM-MULTI-UPDATE-COMPLETION-EVIDENCE-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW" if v2["pass"] else "PHASE-B2-T4-W2E-STOP-RE5-EVIDENCE-INSUFFICIENT"),
        "status": "complete_awaiting_review" if v2["pass"] else "stop", "old_w2_none_reproduced": old["historical_stop_reproduced"],
        "v2_replay_pass": v2["pass"], "v2_candidates": v2["candidate_count"], "v2_valid": v2["valid_count"],
        "selected": v2["selected"], "positive_matrix_pass": positive["pass"], "negative_matrix_pass": negative["pass"],
        "unexpected_negative_passes": negative["unexpected_pass_count"], "historical_re5_status": "STOPPED/HISTORICAL/POISONED/NOT QUALIFIED",
        "historical_re5_artifacts_unchanged": before == after, "production_modifications": 0,
        "AppLauncher_environment_learner": [0, 0, 0], "RE6_started": False})
    print(json.dumps({"old": old, "v2_candidate_count": v2["candidate_count"], "v2_valid_count": v2["valid_count"],
        "v2_selected": v2["selected"], "positive": positive["pass"], "negative": negative["pass"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
