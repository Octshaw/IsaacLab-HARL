"""B2-V1-C terminal/history, learner, GAE, and rollover integration gate."""

from __future__ import annotations

from pathlib import Path
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_v1_event_route_helpers as H  # noqa: E402


def collect_rollout():
    harness = H.lifecycle_harness()
    harness.route.reset()
    receipts = tuple(harness.route.collect_step() for _ in range(3))
    return harness, receipts


def _event_batches(harness: H.RouteHarness):
    return tuple(detail for stage, detail in harness.events if stage == "I5a_critic_buffer_insert")


def test_v1_c1_partial_terminal_autoreset_and_multiple_episode_keys() -> dict[str, object]:
    harness, receipts = collect_rollout()
    first, second, third = receipts
    H.assert_true(first.harl_step_result[3][:, 0].tolist() == [False, True, True, False], "partial terminal vector")
    H.assert_true(second.harl_step_result[3][:, 0].tolist() == [False, False, False, False], "continued/autoreset vector")
    H.assert_true(third.harl_step_result[3][:, 0].tolist() == [False, True, False, False], "same env did not terminate again")
    H.assert_true(first.next_decision_bundle.evidence_identity.episode_generations == (0, 1, 1, 0), "per-env autoreset generations")
    H.assert_true(first.next_decision_bundle.evidence_identity.transition_generations == (3, 3, 3, 3), "per-env transition generations")
    H.assert_true(third.next_decision_bundle.evidence_identity.episode_generations[1] == 2, "second env1 autoreset generation")
    keys = harness.route.collector.consumed_terminal_keys
    env1 = tuple(key for key in keys if key[0] == 1)
    H.assert_true(len(env1) == 2 and env1[0] != env1[1], f"same-env terminal keys: {env1}")
    H.assert_true(len(keys) == 3 and len(set(keys)) == 3, "terminal key collision/duplicate")
    for receipt in receipts:
        H.assert_true(len(receipt.harl_step_result) == 6, "HARL six tuple changed")
        for t in receipt.next_decision_bundle.evidence_identity.episode_generations + receipt.next_decision_bundle.evidence_identity.transition_generations:
            H.assert_true(type(t) is int and t >= 0, "generation identity")
    return {"t0_done": [1, 2], "t2_done": [1], "env1_terminal_keys": 2, "six_tuple_steps": 3}


def test_v1_c2_timeout_true_terminal_full_i4_i5a_i5b_and_autoreset_trap() -> dict[str, object]:
    harness, receipts = collect_rollout()
    first = receipts[0]
    info_key = H.LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2
    timeout_dto = first.harl_step_result[4][1][0][info_key]
    true_dto = first.harl_step_result[4][2][0][info_key]
    A = timeout_dto.bootstrap_critic_obs.sum().to(torch.float32)
    B = first.next_decision_bundle.evidence_snapshot.runner_share_obs[1, 0].sum().to(torch.float32)
    H.assert_true(not torch.isclose(A, B), "pre-reset A equals post-reset B trap")
    H.assert_true(torch.isclose(harness.buffer.timeout_bootstrap_value_preds[0, 1, 0], A), "I5a timeout critic did not use A")
    H.assert_true(not torch.isclose(harness.buffer.timeout_bootstrap_value_preds[0, 1, 0], B), "I5a used post-reset B")
    H.assert_true(harness.buffer.timeout_bootstrap_masks[0, :, 0].tolist() == [False, True, False, False], "timeout-only mask")
    H.assert_true(timeout_dto.termination_reason == int(H.Reason.TIME_LIMIT), "timeout DTO reason")
    H.assert_true(true_dto.termination_reason == int(H.Reason.ALL_TASKS_COMPLETED), "true terminal DTO reason")
    true_compact_calls = [call for call in harness.critic.calls if call["obs"].shape[0] == 1]
    H.assert_true(len(true_compact_calls) == 2, "two TIME_LIMIT rows should yield two compact calls")
    rollout = harness.route.finish_rollout(agent_order=(0, 1, 2))
    event = rollout.event_returns_result
    H.assert_true(torch.isclose(event.bootstrap_values[0, 1, 0], A), "I5b timeout bootstrap changed")
    H.assert_true(float(event.bootstrap_values[0, 2, 0]) == 0.0, "true terminal bootstrapped")
    H.assert_true(not bool(event.trace_continue_masks[0, 1, 0]) and not bool(event.trace_continue_masks[0, 2, 0]), "terminal trace continued")
    expected_timeout_return = harness.buffer.rewards[0, 1, 0] + 0.99 * A
    H.assert_true(torch.isclose(event.returns[0, 1, 0], expected_timeout_return), "TIME_LIMIT reward+bootstrap return")
    H.assert_true(torch.isclose(event.returns[0, 2, 0], harness.buffer.rewards[0, 2, 0]), "true terminal reward-only return")
    H.assert_true(torch.equal(harness.buffer.share_obs[0], receipts[-1].next_decision_bundle.evidence_snapshot.runner_share_obs[:, 0]), "after_update did not roll final B/current state")
    return {"TIME_LIMIT": "A bootstrap + trace stop", "true_terminal": "zero bootstrap + trace stop", "post_reset_B_used_for_next": True}


def test_v1_c3_sanitized_infos_and_ack_safe_historical_copy() -> dict[str, object]:
    harness, receipts = collect_rollout()
    key = H.LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2
    batches = _event_batches(harness)
    H.assert_true(len(batches) == 3, "I5a event batch count")
    for batch in batches:
        for row in batch.correlation.sanitized_infos:
            H.assert_true(all(key not in cell for cell in row), "typed DTO leaked to sanitized infos")
    H.assert_true(harness.domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "runtime ACK delayed")
    dto = receipts[0].harl_step_result[4][1][0][key]
    before = dto.bootstrap_critic_obs
    returned = dto.bootstrap_critic_obs
    returned.fill_(777.0)
    H.assert_true(torch.equal(dto.bootstrap_critic_obs, before), "historical DTO getter aliases storage")
    H.assert_true(not torch.equal(dto.bootstrap_critic_obs, torch.full_like(dto.bootstrap_critic_obs, 777.0)), "DTO mutated after ACK")
    return {"sanitized_steps": 3, "pending_runtime_slots": 0, "historical_copy_survives": True}


def test_v1_c4_runtime_reuse_after_ack_before_learner_consumption() -> dict[str, object]:
    harness = H.lifecycle_harness()
    reused = []

    def observer(stage: str, detail: object | None) -> None:
        harness.events.append((stage, detail))
        if stage == "I5a_terminal_infos" and not reused:
            H.assert_true(harness.domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "ACK not complete before learner")
            H.I4._reset(harness.domain, [1, 2])
            reused.append(True)

    harness.route._observer = observer
    harness.route.reset()
    receipt = harness.route.collect_step()
    H.assert_true(reused == [True], "runtime reuse hook did not run")
    H.assert_true(harness.buffer.step == 1 and bool(harness.buffer._event_slot_written[0]), "learner failed after runtime reuse")
    H.assert_true(receipt.harl_step_result[3][:, 0].tolist() == [False, True, True, False], "historical result changed by reuse")
    return {"ACK_before_reuse": True, "learner_after_reuse": True, "storage_insert": 1}


def test_v1_c5_successful_rollover_ledger_lifetime_and_next_rollout_step() -> dict[str, object]:
    harness, receipts = collect_rollout()
    old_keys = harness.route.collector.consumed_terminal_keys
    H.assert_true(len(old_keys) == 3, "terminal keys missing before after_update")
    completed_ids = tuple(id(storage) for storage in harness.route.actor_storages)
    harness.route.finish_rollout(agent_order=(0, 1, 2))
    H.assert_true(harness.route.collector.consumed_terminal_keys == (), "ledger not cleared after successful after_update")
    H.assert_true(harness.buffer.step == 0 and not bool(harness.buffer._event_slot_written.any()), "event buffer fields leaked")
    H.assert_true(all(id(storage) not in completed_ids for storage in harness.route.actor_storages), "actor storage reused")
    H.assert_true(all(not bool(storage._action_ids.any()) and not bool(storage._action_logprobs.any()) for storage in harness.route.actor_storages), "previous actions/logprobs leaked")
    final_bundle = receipts[-1].next_decision_bundle
    H.assert_true(all(storage.decision_bundle_refs[0] is final_bundle for storage in harness.route.actor_storages), "final current slot0 not rolled")
    next_receipt = harness.route.collect_step()
    H.assert_true(next_receipt.transition_slot == 0 and harness.buffer.step == 1, "next rollout first step failed")
    H.assert_true(harness.route.collector.consumed_terminal_keys == (), "old terminal keys reactivated")
    return {"ledger_before": len(old_keys), "ledger_after": 0, "next_rollout_slot": 0, "old_action_leak": False}


def test_v1_c6_ledger_cannot_clear_before_successful_after_update() -> dict[str, object]:
    harness, _ = collect_rollout()
    H.expect_failure(harness.route.collector.reset_consumption_ledger_after_buffer_update, "collector_ledger_lifetime")
    before = harness.route.collector.consumed_terminal_keys
    harness.route._critic_trainer = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic critic trainer failure"))
    H.expect_failure(lambda: harness.route.finish_rollout(agent_order=(0, 1, 2)))
    H.assert_true(harness.route.poisoned, "failed finish did not poison route")
    H.assert_true(harness.route.collector.consumed_terminal_keys == before, "ledger cleared before after_update")
    H.assert_true(harness.buffer.step == 0 and bool(harness.buffer._event_slot_written.all()), "buffer fields cleared after failed trainer")
    return {"early_clear": "rejected", "failed_trainer_ledger_retained": len(before), "route_poisoned": True}


TESTS = (
    ("B2-V1-C1", test_v1_c1_partial_terminal_autoreset_and_multiple_episode_keys),
    ("B2-V1-C2", test_v1_c2_timeout_true_terminal_full_i4_i5a_i5b_and_autoreset_trap),
    ("B2-V1-C3", test_v1_c3_sanitized_infos_and_ack_safe_historical_copy),
    ("B2-V1-C4", test_v1_c4_runtime_reuse_after_ack_before_learner_consumption),
    ("B2-V1-C5", test_v1_c5_successful_rollover_ledger_lifetime_and_next_rollout_step),
    ("B2-V1-C6", test_v1_c6_ledger_cannot_clear_before_successful_after_update),
)


if __name__ == "__main__":
    raise SystemExit(H.run_tests(suite="assignment_phase_b2_v1_c_terminal_learner_rollover_gate_pure", tests=TESTS))
