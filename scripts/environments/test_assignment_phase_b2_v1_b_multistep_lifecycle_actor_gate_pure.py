"""B2-V1-B multi-step lifecycle, DVM, actor-population, and slot gate."""

from __future__ import annotations

from pathlib import Path
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_v1_event_route_helpers as H  # noqa: E402


POLICY = int(H.DECISION.EventPolicyRowKind.POLICY_DECISION_ROW)
CONTINUE = int(H.DECISION.EventPolicyRowKind.FORCED_CONTINUATION_ROW)
FORCED_NOOP = int(H.DECISION.EventPolicyRowKind.FORCED_NOOP_ROW)


def collect_lifecycle():
    harness = H.lifecycle_harness()
    harness.route.reset()
    receipts = tuple(harness.route.collect_step() for _ in range(3))
    return harness, receipts


def test_v1_b1_needs_claim_execute_continue_complete_release_reassign() -> dict[str, object]:
    harness, receipts = collect_lifecycle()
    kinds = [int(receipt.decision_bundle.row_kind[3, 0].item()) for receipt in receipts]
    H.assert_true(kinds == [POLICY, CONTINUE, POLICY], f"env3 lifecycle row sequence: {kinds}")
    first_current = receipts[0].facade_result.current_publication.lifecycle_state
    second_current = receipts[1].facade_result.current_publication.lifecycle_state
    H.assert_true(int(first_current.robot_state[3, 0]) == int(H.RobotState.EXECUTING), "claim did not enter EXECUTING")
    H.assert_true(int(first_current.ownership[3, 2]) == 0, "P2 ownership missing after claim")
    H.assert_true(int(second_current.task_state[3, 2]) == int(H.TaskState.COMPLETED), "completion missing")
    H.assert_true(int(second_current.ownership[3, 2]) == -1, "completion did not release ownership")
    H.assert_true(int(second_current.robot_state[3, 0]) == int(H.RobotState.NEEDS_ASSIGNMENT), "robot did not return to NEEDS_ASSIGNMENT")
    H.assert_true(receipts[1].facade_result.resolution.interpretations[3][0].name == "CONTINUE_EXISTING", "continuation re-claimed")
    H.assert_true(receipts[2].facade_result.resolution.interpretations[3][0].name in {"NEW_CLAIM_COMMITTED", "NEW_CLAIM_SELECTED"}, "released row did not reassign")
    return {"row_sequence": ["POLICY", "CONTINUATION", "POLICY"], "release": True, "reassign": 3}


def test_v1_b2_conflict_winner_loser_and_original_proposals_across_transition() -> dict[str, object]:
    harness, receipts = collect_lifecycle()
    first = receipts[0]
    envelope = first.proposal_envelope
    H.assert_true(tuple(int(v) for v in envelope.original_policy_proposal_ids[0, :2, 0]) == (0, 0), "conflict proposals lost")
    H.assert_true(torch.allclose(envelope.action_logprobs[0, :2, 0], torch.tensor([-0.10, -0.20])), "original proposal logprobs lost")
    statuses = tuple(item.name for item in first.facade_result.resolution.interpretations[0][:2])
    H.assert_true("CONFLICT_LOSER" in statuses and any("COMMITTED" in item or "SELECTED" in item for item in statuses), f"conflict statuses: {statuses}")
    H.assert_true(int(first.facade_result.current_publication.lifecycle_state.ownership[0, 0]) == 1, "cost winner not P2 owner")
    second = receipts[1]
    H.assert_true(second.facade_result.resolution.interpretations[0][1].name == "CONTINUE_EXISTING", "winner did not continue")
    H.assert_true(not bool(second.proposal_envelope.policy_proposal_present_mask[0, 1, 0]), "continuation gained proposal evidence")
    return {"winner": 1, "loser": 0, "winner_next": "CONTINUE_EXISTING", "original_logprobs": True}


def test_v1_b3_policy_noop_and_forced_noop_future_decisions() -> dict[str, object]:
    harness, receipts = collect_lifecycle()
    first, second = receipts[:2]
    N = harness.N
    H.assert_true(int(first.proposal_envelope.action_ids[1, 0, 0]) == N, "policy noop action")
    H.assert_true(bool(first.proposal_envelope.policy_proposal_present_mask[1, 0, 0]), "policy noop proposal absent")
    H.assert_true(int(second.decision_bundle.row_kind[1, 0]) == POLICY, "policy noop row not sampled later")
    H.assert_true(bool(second.proposal_envelope.policy_proposal_present_mask[1, 0, 0]), "later policy evidence absent")
    H.assert_true(int(first.decision_bundle.row_kind[2, 1]) == FORCED_NOOP, "t0 forced noop setup")
    H.assert_true(not bool(first.proposal_envelope.policy_proposal_present_mask[2, 1, 0]), "forced noop gained proposal")
    H.assert_true(int(second.decision_bundle.row_kind[2, 1]) == POLICY, "forced noop did not become policy at t1")
    H.assert_true(bool(second.proposal_envelope.policy_proposal_present_mask[2, 1, 0]), "future proposal polluted/absent")
    return {"policy_noop_resampled": True, "forced_noop_to_policy": True, "future_evidence_clean": True}


def test_v1_b4_actor_storage_slots_and_same_transition_correlation() -> dict[str, object]:
    harness, receipts = collect_lifecycle()
    for agent_id, storage in enumerate(harness.route.actor_storages):
        H.assert_true(tuple(storage.obs.shape[:2]) == (4, 4), "obs [T+1,E]")
        H.assert_true(tuple(storage.available_actions.shape) == (4, 4, 5), "available [T+1,E,N+1]")
        H.assert_true(tuple(storage.decision_valid_masks.shape) == (4, 4, 1), "DVM [T+1,E,1]")
        H.assert_true(tuple(storage.action_ids.shape) == (3, 4, 1), "actions [T,E,1]")
        H.assert_true(tuple(storage.action_logprobs.shape) == (3, 4, 1), "logprobs [T,E,1]")
        for t, receipt in enumerate(receipts):
            H.assert_true(storage.decision_bundle_refs[t] is receipt.decision_bundle, "actor slot decision identity")
            H.assert_true(torch.equal(storage.action_ids[t], receipt.proposal_envelope.action_ids[:, agent_id]), "actor action transition alignment")
    H.assert_true(tuple(harness.buffer.share_obs.shape[:2]) == (4, 4), "critic share [T+1,E]")
    H.assert_true(tuple(harness.buffer.rewards.shape) == (3, 4, 1), "critic rewards [T,E,1]")
    H.assert_true(tuple(harness.buffer.termination_reason.shape) == (3, 4, 1), "reason [T,E,1]")
    H.assert_true(tuple(harness.buffer.timeout_bootstrap_value_preds.shape) == (3, 4, 1), "timeout value [T,E,1]")
    for t, receipt in enumerate(receipts):
        H.assert_true(torch.equal(harness.buffer.rewards[t, :, 0], receipt.harl_step_result[2][:, 0, 0]), "actor/critic physical transition mismatch")
    return {"actor_state_slots": 4, "actor_action_slots": 3, "critic_transition_slots": 3, "same_transition": True}


def test_v1_b5_active_false_dvm_true_and_full_canonical_factor() -> dict[str, object]:
    harness = H.lifecycle_harness()
    harness.route.reset()
    storage0 = harness.route.actor_storages[0]
    H.assert_true(bool(storage0._decision_valid_masks[0, 0, 0]), "edge row is not DVM true")
    storage0._active_masks[0, 0, 0] = 0.0
    receipts = tuple(harness.route.collect_step() for _ in range(3))
    H.assert_true(bool(receipts[0].proposal_envelope.policy_proposal_present_mask[0, 0, 0]), "active=false suppressed proposal collection")
    H.assert_true(bool(harness.buffer._event_slot_written.all().item()), "critic dropped a physical transition")
    rollout = harness.route.finish_rollout(agent_order=(0, 1, 2))
    completed = rollout.completed_actor_storages[0]
    loss_mask = completed.decision_valid_masks[:-1] & completed.active_masks[:-1].to(torch.bool)
    normalized = H.HAPPO.normalize_event_policy_advantages_v2(
        advantages=rollout.advantages,
        policy_loss_mask=loss_mask,
    )
    H.assert_true(not bool(loss_mask[0, 0, 0]), "active=false row entered actor loss")
    H.assert_true(float(normalized.normalized_advantages[0, 0, 0]) == 0.0, "excluded actor loss received advantage")
    trainer = harness.actor_train_calls[0]
    factor = trainer["initial_factor"]
    H.assert_true(tuple(factor.shape) == (3, 4, 1), "factor compacted")
    for storage in trainer["actor_storages"]:
        canonical = torch.nonzero(storage.decision_valid_masks[:-1].reshape(-1), as_tuple=False).flatten()
        expected = tuple(t * 4 + e for t in range(3) for e in range(4) if bool(storage.decision_valid_masks[t, e, 0]))
        H.assert_true(tuple(int(v) for v in canonical.tolist()) == expected, "canonical k=t*E+e changed")
    return {"proposal_present": True, "actor_loss_excluded": True, "critic_transition_preserved": True, "factor": [3, 4, 1]}


TESTS = (
    ("B2-V1-B1", test_v1_b1_needs_claim_execute_continue_complete_release_reassign),
    ("B2-V1-B2", test_v1_b2_conflict_winner_loser_and_original_proposals_across_transition),
    ("B2-V1-B3", test_v1_b3_policy_noop_and_forced_noop_future_decisions),
    ("B2-V1-B4", test_v1_b4_actor_storage_slots_and_same_transition_correlation),
    ("B2-V1-B5", test_v1_b5_active_false_dvm_true_and_full_canonical_factor),
)


if __name__ == "__main__":
    raise SystemExit(H.run_tests(suite="assignment_phase_b2_v1_b_multistep_lifecycle_actor_gate_pure", tests=TESTS))
