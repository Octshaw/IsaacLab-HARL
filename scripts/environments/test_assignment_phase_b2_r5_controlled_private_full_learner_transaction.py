"""B2-R5 controlled private full learner-transaction verification."""

from __future__ import annotations

from dataclasses import replace
import ast
import json
from pathlib import Path

import torch

import _assignment_phase_b2_r5_full_transaction_helpers as H


R5, R3, R4, E, P, C = H.R5, H.R3, H.R4, H.E, H.P, H.C
GLOBAL_COUNTER = R5.B2R5ExecutionCounterV1(H.ACTORS)


EXPECTED_DEPENDENCY_EDGES = (
    ("assignment_event_training_actor_mutation", "assignment_event_training_control"),
    ("assignment_event_training_actor_mutation", "assignment_event_training_evidence"),
    ("assignment_event_training_actor_mutation", "assignment_event_training_gradient_probe"),
    ("assignment_event_training_actor_mutation", "assignment_event_training_plans"),
    ("assignment_event_training_critic_mutation", "assignment_event_training_actor_mutation"),
    ("assignment_event_training_critic_mutation", "assignment_event_training_control"),
    ("assignment_event_training_critic_mutation", "assignment_event_training_evidence"),
    ("assignment_event_training_critic_mutation", "assignment_event_training_gradient_probe"),
    ("assignment_event_training_critic_mutation", "assignment_event_training_plans"),
    ("assignment_event_training_full_transaction", "assignment_event_training_actor_mutation"),
    ("assignment_event_training_full_transaction", "assignment_event_training_control"),
    ("assignment_event_training_full_transaction", "assignment_event_training_critic_mutation"),
    ("assignment_event_training_full_transaction", "assignment_event_training_evidence"),
    ("assignment_event_training_full_transaction", "assignment_event_training_gradient_probe"),
    ("assignment_event_training_full_transaction", "assignment_event_training_plans"),
    ("assignment_event_training_gradient_probe", "assignment_event_training_control"),
    ("assignment_event_training_gradient_probe", "assignment_event_training_evidence"),
    ("assignment_event_training_gradient_probe", "assignment_event_training_plans"),
)


def _counts() -> dict[str, object]:
    return {
        "actor_backward": GLOBAL_COUNTER.actor_backward_executed,
        "actor_step": GLOBAL_COUNTER.actor_step_executed,
        "per_actor_backward": list(GLOBAL_COUNTER.actor_backward_by_actor),
        "per_actor_step": list(GLOBAL_COUNTER.actor_step_by_actor),
        "critic_backward": GLOBAL_COUNTER.critic_backward_executed,
        "critic_step": GLOBAL_COUNTER.critic_step_executed,
        "live_valuenorm_update": GLOBAL_COUNTER.live_valuenorm_executed,
        "training_mode_entries": GLOBAL_COUNTER.training_mode_entries,
        "rollout_mode_restorations": GLOBAL_COUNTER.rollout_mode_restorations,
        "critic_rollovers": GLOBAL_COUNTER.critic_rollovers,
        "terminal_ledger_resets": GLOBAL_COUNTER.terminal_ledger_resets,
        "actor_storage_rollovers": GLOBAL_COUNTER.actor_storage_rollovers,
        "s10_entries": GLOBAL_COUNTER.s10_entries,
        "successful_transactions": GLOBAL_COUNTER.successful_transactions,
    }


def _delta(before: dict[str, object]) -> dict[str, int]:
    after = _counts()
    return {
        key: int(after[key]) - int(before[key])
        for key in (
            "actor_backward", "actor_step", "critic_backward", "critic_step",
            "live_valuenorm_update", "training_mode_entries",
            "rollout_mode_restorations", "critic_rollovers",
            "terminal_ledger_resets", "actor_storage_rollovers", "s10_entries",
            "successful_transactions",
        )
    }


def test_static_private_public_guards() -> dict[str, object]:
    source = H.R1.SCAN_SOURCE
    executor_files = tuple(source / name for name in (
        "assignment_event_training_gradient_probe.py",
        "assignment_event_training_actor_mutation.py",
        "assignment_event_training_critic_mutation.py",
        "assignment_event_training_full_transaction.py",
    ))
    evidence = H.SG.validate_r5_dependency_graph_v1(executor_files, expected_edges=EXPECTED_DEPENDENCY_EDGES)
    private = set(source.glob("assignment_event_training_*.py"))
    production = tuple(sorted(path for path in source.glob("*.py") if path not in private))
    tokens = ("assignment_event_training_full_transaction", "assignment_event_training_full_transaction_guards")
    public = H.SG.validate_r5_public_isolation_v1(production, private_tokens=tokens)
    faults = (
        (H.SG.STOP_UNAUTHORIZED_BACKWARD, "loss.backward()"),
        (H.SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "optimizer.step()"),
        (H.SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "actor.actor_optimizer.step()"),
        (H.SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "critic.critic_optimizer.step()"),
        (H.SG.STOP_VALUENORM, "value_normalizer.update(raw)"),
        (H.SG.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.update(batch)"),
        (H.SG.STOP_CRITIC_TRAINING_SLICE, "VCritic.train()"),
        (H.SG.STOP_STOCK_RETURNS_BYPASS, "critic_buffer.compute_returns(value)"),
    )
    for index, (stop, source_text) in enumerate(faults):
        H.expect_stop(stop, lambda index=index, source_text=source_text: H.SG.validate_r5_source_text_fault_v1(source_text, identity=f"r5-source-fault-{index}"))
    H.expect_stop(H.SG.STOP_PUBLIC_ROUTE_OPEN, lambda: H.SG.validate_r5_public_source_text_v1("import assignment_event_training_full_transaction", identity="public.py", private_tokens=tokens))
    H.assert_true(public.violation_count == 0 and len(production) == 57, "R5 public isolation")
    return {
        "dependency_edges": len(evidence.dependency_edges),
        "backward_executor": evidence.backward_executor_count,
        "actor_step_executor": evidence.actor_step_executor_count,
        "critic_step_executor": evidence.critic_step_executor_count,
        "live_valuenorm_executor": evidence.live_valuenorm_executor_count,
        "r5_actor_sequence_calls": evidence.r5_actor_sequence_call_count,
        "r5_critic_sequence_calls": evidence.r5_critic_sequence_call_count,
        "scheduler_steps": evidence.scheduler_step_count,
        "production_files": len(production), "static_public_faults": 9,
    }


def _plan_validation(context, plan) -> None:
    R5.validate_immutable_plan_v1(
        authority=context.authority, plan=plan, actor_plan=context.actor_plan,
        critic_plan=context.critic_plan, initial_factor=context.initial_factor,
        current_component_digest=R5._component_state_digest(
            context.components.actors, context.components.critic,
            context.components.live_value_normalizer,
        ),
    )


def _advance(machine, stages) -> None:
    for stage in stages:
        machine.transition(stage)


def _r3_permit_context(context):
    minibatch = next(item for item in context.actor_plan.minibatches if item.actor_id == 0 and not item.empty_loss)
    actor = context.components.actors[0]
    fp = R3.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=actor.actor, optimizer=actor.actor_optimizer)
    permit = R3._make_permit_v1(
        authority=context.authority.actor_authority, actor_id=0,
        actor_order_position=0, minibatch=minibatch,
        operation=C.B2RPermitOperationV1.BACKWARD,
        module_fingerprint=R3._parameter_digest(fp),
        optimizer_fingerprint=R3._optimizer_digest(fp),
    )
    kwargs = dict(
        operation=C.B2RPermitOperationV1.BACKWARD, actor_id=0,
        actor_order_position=0, epoch=minibatch.epoch,
        minibatch=minibatch.minibatch,
        canonical_indices=minibatch.active_and_dvm_loss_indices,
        module_fingerprint=R3._parameter_digest(fp),
        optimizer_fingerprint=R3._optimizer_digest(fp),
    )
    return permit, kwargs


def _r4_permit_context(context):
    partition = context.critic_plan.partitions_by_epoch[0][0]
    raw = context.critic_inputs.returns_storage[:-1].reshape(H.B, 1)[torch.tensor(partition)]
    critic_fp = R4.fingerprint_component_v1(component_kind="critic", owner_identity="critic", module=context.components.critic.critic, optimizer=context.components.critic.critic_optimizer)
    vn_fp = R4.fingerprint_component_v1(component_kind="live_valuenorm", owner_identity="live_valuenorm", value_normalizer=context.components.live_value_normalizer)
    raw_digest = E.fingerprint_tensor_v1(raw).content_digest
    permit = R4._make_permit_v1(
        authority=context.authority.critic_authority, component_kind="live_valuenorm",
        epoch=0, minibatch=0, indices=partition, raw_digest=raw_digest,
        operation=C.B2RPermitOperationV1.VALUENORM_UPDATE,
        critic_parameter_digest=R4._parameter_digest(critic_fp),
        critic_optimizer_digest=R4._optimizer_digest(critic_fp),
        valuenorm_digest=vn_fp.fingerprint_digest,
    )
    kwargs = dict(
        component_kind="live_valuenorm", epoch=0, minibatch=0,
        canonical_indices=partition, raw_target_digest=raw_digest,
        operation=C.B2RPermitOperationV1.VALUENORM_UPDATE,
        critic_parameter_fingerprint=R4._parameter_digest(critic_fp),
        critic_optimizer_fingerprint=R4._optimizer_digest(critic_fp),
        valuenorm_fingerprint=vn_fp.fingerprint_digest,
    )
    return permit, kwargs


def test_pure_integrated_fault_matrix(success_receipt) -> dict[str, object]:
    context = H.make_context(update_id="b2-r5-pure-faults")
    bad_digest = H.R1.digest("r5-bad")
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, update_id="stale")))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, authority_config_digest=bad_digest)))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: replace(context.authority, slice_identity="B2-R4"))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, actor_plan_digest=bad_digest)))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, critic_plan_digest=bad_digest)))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, actor_expected_step=((0, 3), (1, 4), (2, 0)))))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: _plan_validation(context, replace(context.immutable_plan, critic_expected_step=2)))

    H.expect_stop(C.STOP_MODE_ORDER, lambda: C.B2RUpdateStateMachineV1().transition(C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE))
    machine = C.B2RUpdateStateMachineV1(); _advance(machine, tuple(C.B2RUpdateStageV1)[1:5])
    H.expect_stop(C.STOP_MODE_ORDER, lambda: machine.transition(C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE))
    for next_stage in (C.B2RUpdateStageV1.S8_ROLLOUT_MODE_RESTORED, C.B2RUpdateStageV1.S8_ROLLOUT_MODE_RESTORED):
        machine = C.B2RUpdateStateMachineV1(); _advance(machine, tuple(C.B2RUpdateStageV1)[1:7])
        H.expect_stop(C.STOP_MODE_ORDER, lambda machine=machine, next_stage=next_stage: machine.transition(next_stage))
    machine = C.B2RUpdateStateMachineV1(); _advance(machine, tuple(C.B2RUpdateStageV1)[1:8])
    H.expect_stop(C.STOP_ROLLOVER_ORDER, lambda: machine.transition(C.B2RUpdateStageV1.S9_ROLLOVER_COMPLETE))
    order = R5.B2R5RolloverOrderV1()
    H.expect_stop(C.STOP_ROLLOVER_ORDER, order.record_terminal_reset)
    order = R5.B2R5RolloverOrderV1(); order.record_critic_rollover()
    H.expect_stop(C.STOP_ROLLOVER_ORDER, order.record_actor_rollover)
    machine = C.B2RUpdateStateMachineV1(); _advance(machine, tuple(C.B2RUpdateStageV1)[1:9])
    H.expect_stop(C.STOP_MODE_ORDER, lambda: machine.transition(C.B2RUpdateStageV1.S10_QUIESCENT))

    expected = {"actor1": H.R1.digest("same"), "critic": H.R1.digest("critic")}
    for key in ("actor1", "critic"):
        changed = dict(expected); changed[key] = bad_digest
        H.expect_stop(C.STOP_MUTATION_ATTRIBUTION, lambda changed=changed: R3.validate_foreign_state_claim_v1(expected=expected, observed=changed))
    H.expect_stop(C.STOP_MUTATION_ATTRIBUTION, lambda: R4.validate_actor_freeze_claim_v1(expected={"actor0": H.R1.digest("a")}, observed={"actor0": bad_digest}))
    H.expect_stop(C.STOP_MUTATION_ATTRIBUTION, lambda: R3.validate_foreign_state_claim_v1(expected={"live_valuenorm": H.R1.digest("v")}, observed={"live_valuenorm": bad_digest}))

    pending = replace(success_receipt.quiescence_evidence, pending_optimizer_permits=1, checkpoint_boundary_eligible_by_state_machine=False)
    H.expect_stop(C.STOP_CHECKPOINT_BOUNDARY, lambda: R5.validate_quiescence_claim_v1(pending))
    permit, kwargs = _r3_permit_context(context)
    ledger = R3.B2R3PermitLedgerV1(); state = R3.B2R3RouteStateV1()
    ledger.consume(permit, authority=context.authority.actor_authority, route_state=state, **kwargs)
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: ledger.consume(permit, authority=context.authority.actor_authority, route_state=state, **kwargs))
    new_context = H.make_context(update_id="b2-r5-new-transaction")
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: R3.B2R3PermitLedgerV1().consume(permit, authority=new_context.authority.actor_authority, route_state=R3.B2R3RouteStateV1(), **kwargs))
    permit4, kwargs4 = _r4_permit_context(context)
    ledger4 = R4.B2R4PermitLedgerV1(); state4 = R4.B2R4RouteStateV1()
    ledger4.consume(permit4, authority=context.authority.critic_authority, route_state=state4, **kwargs4)
    H.expect_stop(E.STOP_VALUENORM, lambda: ledger4.consume(permit4, authority=context.authority.critic_authority, route_state=state4, **kwargs4))
    H.expect_stop(E.STOP_VALUENORM, lambda: R4.B2R4PermitLedgerV1().consume(permit4, authority=new_context.authority.critic_authority, route_state=R4.B2R4RouteStateV1(), **kwargs4))

    segment = success_receipt.actor_sequence_receipt.actor_segments[1]
    H.expect_stop(P.STOP_FACTOR, lambda: R3.validate_factor_segment_contract_v1(replace(segment, factor_before_digest=bad_digest), expected_dvm_indices=segment.dvm_indices))
    H.expect_stop(P.STOP_FACTOR, lambda: replace(segment.factor_transition, recurrence_exact=False))

    missing = replace(context.rollout_evidence, terminal_consumption_keys=())
    H.expect_stop(R5.STOP_ROLLOUT_INCOMPLETE, lambda: R5.validate_rollout_complete_v1(authority=context.authority, rollout=missing, rollover_resources=context.rollover_resources))
    early = R5.B2R5RolloverOrderV1()
    H.expect_stop(C.STOP_ROLLOVER_ORDER, early.record_terminal_reset)
    stale = replace(success_receipt.quiescence_evidence, unconsumed_terminal_keys=1, checkpoint_boundary_eligible_by_state_machine=False)
    H.expect_stop(C.STOP_CHECKPOINT_BOUNDARY, lambda: R5.validate_quiescence_claim_v1(stale))

    for operation in ("actor_continuation", "critic_start", "rollover", "checkpoint"):
        poisoned = C.B2RUpdateStateMachineV1(); poisoned.poison()
        H.expect_stop(C.STOP_MODE_ORDER, lambda poisoned=poisoned: poisoned.transition(C.B2RUpdateStageV1.S1_FINAL_VALUE_EVALUATED))
    return {
        "authority_plan_faults": 7, "ordering_faults": 8,
        "mutation_isolation_faults": 4, "permit_faults": 5,
        "factor_faults": 2, "terminal_faults": 3,
        "poison_continuation_faults": 4, "total": 33,
    }


def test_pre_mutation_failure() -> dict[str, object]:
    context = H.make_context(update_id="b2-r5-pre-mutation-failure")
    state = R5.B2R5TransactionRouteStateV1(); before = _counts()
    H.expect_stop(R5.STOP_ROLLOUT_INCOMPLETE, lambda: H.execute(context, counter=GLOBAL_COUNTER, route_state=state, synthetic_fault="pre_mutation"))
    delta = _delta(before); failure = state.last_failure
    H.assert_true(all(delta[key] == 0 for key in ("actor_step", "critic_step", "live_valuenorm_update", "critic_rollovers", "terminal_ledger_resets", "s10_entries")), "pre-mutation delta")
    H.assert_true(failure is not None and not failure.partial_update and not failure.route_poisoned and failure.failed_stage is C.B2RUpdateStageV1.S0_ROLLOUT_COMPLETE, "pre-mutation evidence")
    return {"delta": delta, "partial_update": False, "route_poisoned": False}


def test_successful_full_transaction():
    context = H.make_context(update_id="b2-r5-success-0001")
    H.assert_true(
        all(tuple(inputs.decision_valid_mask.shape) == (H.B, 1) for inputs in context.actor_inputs.values()),
        "R5 actor factor path did not use [B,1] masks",
    )
    final_critic_slot = context.rollover_resources.critic_buffer.share_obs[-1].detach().clone()
    final_actor_slots = tuple(storage.final_current_slot_digest for storage in context.rollover_resources.actor_storages)
    before = _counts()
    receipt = H.execute(context, counter=GLOBAL_COUNTER)
    delta = _delta(before)
    H.assert_true(delta == {
        "actor_backward": 8, "actor_step": 8, "critic_backward": 1,
        "critic_step": 1, "live_valuenorm_update": 1,
        "training_mode_entries": 1, "rollout_mode_restorations": 1,
        "critic_rollovers": 1, "terminal_ledger_resets": 1,
        "actor_storage_rollovers": 3, "s10_entries": 1,
        "successful_transactions": 1,
    }, "successful transaction counts")
    H.assert_true(receipt.ordering_evidence.history == tuple(C.B2RUpdateStageV1), "S0-S10 history")
    H.assert_true(receipt.actor_parameter_mutation_by_actor == ((0, True), (1, True), (2, False)), "actor mutation summary")
    H.assert_true(receipt.critic_parameter_mutated and receipt.live_valuenorm_mutated, "critic/VN mutation summary")
    H.assert_true(torch.equal(context.rollover_resources.critic_buffer.share_obs[0], final_critic_slot), "critic final slot rollover")
    H.assert_true(tuple(storage.slot_zero_digest for storage in context.rollover_resources.actor_storages) == final_actor_slots, "actor final current slots")
    H.assert_true(context.rollover_resources.terminal_collector.consumed_terminal_keys == (), "terminal ledger not cleared")
    return {
        "update_id": context.authority.update_id,
        "evidence_digest": receipt.evidence_digest,
        "plan_digest": receipt.immutable_plan_digest,
        "S0_S10": [stage.value for stage in receipt.ordering_evidence.history],
        "actor_order": list(receipt.actor_sequence_receipt.actor_order),
        "actor_counts": [[segment.actor_id, segment.observed_backward_count, segment.observed_step_count] for segment in receipt.actor_sequence_receipt.actor_segments],
        "actor_mask_shapes": [list(context.actor_inputs[actor_id].decision_valid_mask.shape) for actor_id in range(H.ACTORS)],
        "actor_dvm_rows": {
            str(actor_id): list(R3._canonical_true_row_indices_v1(context.actor_inputs[actor_id].decision_valid_mask))
            for actor_id in range(H.ACTORS)
        },
        "actor_off_dvm_rows": {
            str(actor_id): list(R3._canonical_true_row_indices_v1(~context.actor_inputs[actor_id].decision_valid_mask))
            for actor_id in range(H.ACTORS)
        },
        "factor_post_audit_passes": 2,
        "factor_initial_final": [receipt.actor_sequence_receipt.initial_factor_digest, receipt.actor_sequence_receipt.final_factor_digest],
        "critic_counts": [receipt.critic_sequence_receipt.observed_backward_count, receipt.critic_sequence_receipt.observed_step_count, receipt.critic_sequence_receipt.observed_valuenorm_count],
        "critic_rows": receipt.critic_sequence_receipt.partitions_by_epoch,
        "rollover_order": receipt.rollover_evidence.operation_order,
        "terminal_keys_before_after": [receipt.rollover_evidence.terminal_keys_before, receipt.rollover_evidence.terminal_keys_after],
        "quiescence_digest": receipt.quiescence_evidence.evidence_digest,
        "checkpoint_boundary_eligible_by_state_machine": receipt.quiescence_evidence.checkpoint_boundary_eligible_by_state_machine,
    }, receipt


def _poisoned_transaction(*, name: str, fault: str, expected_stop: str, expected_delta: tuple[int, int, int], expected_stage: C.B2RUpdateStageV1) -> dict[str, object]:
    context = H.make_context(update_id=f"b2-r5-{name}")
    state = R5.B2R5TransactionRouteStateV1(); before = _counts()
    H.expect_stop(expected_stop, lambda: H.execute(context, counter=GLOBAL_COUNTER, route_state=state, synthetic_fault=fault))
    delta = _delta(before); failure = state.last_failure
    H.assert_true((delta["actor_step"], delta["critic_step"], delta["live_valuenorm_update"]) == expected_delta, f"{name} mutation delta")
    H.assert_true(delta["critic_rollovers"] == delta["terminal_ledger_resets"] == delta["actor_storage_rollovers"] == delta["s10_entries"] == 0, f"{name} rollover")
    H.assert_true(failure is not None and failure.partial_update and failure.route_poisoned and failure.failed_stage is expected_stage and not failure.rollover_allowed and not failure.ledger_reset_allowed and not failure.checkpoint_allowed and not failure.public_use_allowed, f"{name} poison")
    H.expect_stop(C.STOP_MODE_ORDER, lambda: state.machine.transition(C.B2RUpdateStageV1.S8_ROLLOUT_MODE_RESTORED))
    return {"delta": delta, "failed_stage": failure.failed_stage.value, "partial_update": True, "route_poisoned": True, "later_rollover": 0, "s10": 0}


def main() -> None:
    results: dict[str, object] = {}
    try:
        results["static_private_public"] = test_static_private_public_guards()
        results["pre_mutation"] = test_pre_mutation_failure()
        success, receipt = test_successful_full_transaction(); results["success"] = success
        results["pure_fault_matrix"] = test_pure_integrated_fault_matrix(receipt)
        results["actor_post_step_poison"] = _poisoned_transaction(name="actor-post-step", fault="actor_post_step", expected_stop=P.STOP_FACTOR, expected_delta=(1, 0, 0), expected_stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE)
        results["post_valuenorm_poison"] = _poisoned_transaction(name="post-valuenorm", fault="post_valuenorm", expected_stop=E.STOP_VALUENORM, expected_delta=(8, 0, 1), expected_stage=C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE)
        results["post_critic_step_poison"] = _poisoned_transaction(name="post-critic-step", fault="post_step", expected_stop=C.STOP_MUTATION_ATTRIBUTION, expected_delta=(8, 1, 1), expected_stage=C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE)
        results["post_update_audit_poison"] = _poisoned_transaction(name="post-update-audit", fault="post_update_audit", expected_stop=C.STOP_MUTATION_ATTRIBUTION, expected_delta=(8, 1, 1), expected_stage=C.B2RUpdateStageV1.S7_POST_UPDATE_AUDIT)
        counts = _counts()
        H.assert_true(counts == {
            "actor_backward": 33, "actor_step": 33,
            "per_actor_backward": [17, 16, 0], "per_actor_step": [17, 16, 0],
            "critic_backward": 3, "critic_step": 3,
            "live_valuenorm_update": 4, "training_mode_entries": 5,
            "rollout_mode_restorations": 1, "critic_rollovers": 1,
            "terminal_ledger_resets": 1, "actor_storage_rollovers": 3,
            "s10_entries": 1, "successful_transactions": 1,
        }, "authoritative R5 aggregate counts")
    except BaseException:
        print(json.dumps({"status": "FAIL", "tests": results, "execution_counts": _counts()}, sort_keys=True))
        raise
    print(json.dumps({
        "status": "PASS", "tests": results, "execution_counts": counts,
        "successful_full_transactions": 1, "pre_mutation_failed_transactions": 1,
        "actor_post_step_poisoned_transactions": 1,
        "post_valuenorm_poisoned_transactions": 1,
        "post_critic_step_poisoned_transactions": 1,
        "post_update_audit_poisoned_transactions": 1,
        "pure_fault_assertions": 33, "static_public_faults": 9,
        "isaac_runtime_rollouts": 0, "training_campaigns": 0,
        "evaluation_playback": 0, "checkpoint_weight_io": 0,
        "public_route_activations": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
