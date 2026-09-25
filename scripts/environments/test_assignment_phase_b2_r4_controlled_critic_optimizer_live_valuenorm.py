"""B2-R4 real critic Adam and live ValueNorm controlled mutation tests."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import torch

import _assignment_phase_b2_r4_critic_mutation_helpers as H


R4, E, P, C, SG = H.R4, H.E, H.P, H.C, H.SG
GLOBAL_COUNTER = R4.B2R4ExecutionCounterV1()


def _execute(context, *, state=None, synthetic_fault=None):
    return R4.execute_critic_sequence_v1(
        authority=context.authority,
        frozen_inputs=context.frozen_inputs,
        critic_plan=context.plan,
        actors=context.components.actors,
        critic=context.components.critic,
        live_value_normalizer=context.components.live_value_normalizer,
        inputs=context.inputs,
        route_state=R4.B2R4RouteStateV1() if state is None else state,
        counter=GLOBAL_COUNTER,
        synthetic_fault=synthetic_fault,
    )


def test_enabled_sequence() -> tuple[dict[str, object], object]:
    context = H.make_context()
    state = R4.B2R4RouteStateV1()
    receipt = _execute(context, state=state)
    H.assert_true((receipt.observed_backward_count, receipt.observed_step_count, receipt.observed_valuenorm_count) == (4, 4, 4), "enabled counts")
    H.assert_true(receipt.per_epoch_backward_count == (2, 2) and receipt.per_epoch_step_count == (2, 2) and receipt.per_epoch_valuenorm_count == (2, 2), "per-epoch counts")
    H.assert_true(all(item.valuenorm_receipt is not None and item.valuenorm_receipt.normalize_same_object and item.valuenorm_receipt.normalize_same_digest for item in receipt.step_receipts), "same raw normalization")
    H.assert_true(all(item.critic_parameter_mutated and item.critic_optimizer_mutated and item.valuenorm_mutated for item in receipt.step_receipts), "enabled mutation receipts")
    H.assert_true(receipt.actor_components_unchanged and receipt.actor_optimizers_unchanged and receipt.gradients_clean_after, "actor hard freeze")
    first, last = receipt.step_receipts[0], receipt.step_receipts[-1]
    return ({
        "counts": [4, 4, 4],
        "per_epoch": {"backward": [2, 2], "step": [2, 2], "valuenorm": [2, 2]},
        "partitions": receipt.partitions_by_epoch,
        "target_digest": receipt.target_digest,
        "final_slot_digest": receipt.final_slot_digest,
        "critic_parameter_first_pre_final_post": [first.critic_parameter_digest_before, last.critic_parameter_digest_after],
        "critic_optimizer_first_pre_final_post": [first.critic_optimizer_digest_before, last.critic_optimizer_digest_after],
        "valuenorm_first_pre_final_post": [first.valuenorm_receipt.pre_fingerprint, last.valuenorm_receipt.post_fingerprint],
        "valuenorm_receipts": [{
            "epoch": item.epoch,
            "minibatch": item.minibatch,
            "rows": item.canonical_indices,
            "raw_digest": item.raw_target_digest,
            "pre": item.valuenorm_receipt.pre_fingerprint,
            "post": item.valuenorm_receipt.post_fingerprint,
            "mean": item.valuenorm_receipt.running_mean_values,
            "mean_sq": item.valuenorm_receipt.running_mean_sq_values,
            "debias": item.valuenorm_receipt.debiasing_term_values,
            "normalize_calls": item.valuenorm_receipt.normalize_call_count,
        } for item in receipt.step_receipts],
        "critic_step_receipts": [{
            "epoch": item.epoch,
            "minibatch": item.minibatch,
            "loss": item.loss_value,
            "gradient_norm": item.aggregate_gradient_norm,
            "clip": item.clip_result,
            "parameter_pre": item.critic_parameter_digest_before,
            "parameter_post": item.critic_parameter_digest_after,
            "optimizer_pre": item.critic_optimizer_digest_before,
            "optimizer_post": item.critic_optimizer_digest_after,
        } for item in receipt.step_receipts],
    }, receipt)


def test_disabled_sequence() -> dict[str, object]:
    context = H.make_context(valuenorm_enabled=False, suffix="disabled")
    before_vn = R4._valuenorm_digest(context.components.live_value_normalizer)
    receipt = _execute(context)
    after_vn = R4._valuenorm_digest(context.components.live_value_normalizer)
    H.assert_true((receipt.observed_backward_count, receipt.observed_step_count, receipt.observed_valuenorm_count) == (2, 2, 0), "disabled counts")
    H.assert_true(before_vn == after_vn and all(item.valuenorm_receipt is None and not item.valuenorm_mutated for item in receipt.step_receipts), "disabled ValueNorm changed")
    return {"probe_count": 1, "backward": 2, "step": 2, "valuenorm_updates": 0, "valuenorm_unchanged": True, "raw_target_used_directly": True}


def test_remainder_safe_sequence() -> dict[str, object]:
    context = H.make_context(remainder_safe=True, suffix="remainder")
    receipt = _execute(context)
    sizes = tuple(len(item) for item in receipt.partitions_by_epoch[0])
    covered = tuple(row for batch in receipt.partitions_by_epoch[0] for row in batch)
    H.assert_true(sizes == (3, 2, 2) and covered == tuple(range(7)), "remainder-safe partition")
    H.assert_true(receipt.remainder_safe and (receipt.observed_backward_count, receipt.observed_step_count, receipt.observed_valuenorm_count) == (3, 3, 3), "remainder real mutation")
    return {"B": 7, "minibatches": 3, "partition_sizes": sizes, "covered_rows": covered, "backward": 3, "step": 3, "valuenorm_updates": 3}


def _permit_context():
    context = H.make_context(suffix="permit")
    actors, critic, vn = R4._capture_all_v1(
        actors=context.components.actors,
        critic=context.components.critic,
        live_value_normalizer=context.components.live_value_normalizer,
    )
    partition = context.plan.partitions_by_epoch[0][0]
    raw = context.inputs.returns_storage[:-1].reshape(context.B, 1)[torch.tensor(partition)]
    return context, critic, vn, partition, E.fingerprint_tensor_v1(raw).content_digest


def _permit(context, critic, vn, partition, raw_digest, *, operation, component_kind, **changes):
    values = {
        "permit_id": f"permit-{component_kind}-{operation.value}",
        "update_id": context.authority.update_id,
        "authority_config_digest": context.authority.config_digest,
        "component_kind": component_kind,
        "epoch": 0,
        "minibatch": 0,
        "canonical_index_digest": E.canonical_digest_v1(partition),
        "raw_target_digest": raw_digest,
        "operation": operation,
        "expected_critic_parameter_fingerprint": R4._parameter_digest(critic),
        "expected_critic_optimizer_fingerprint": R4._optimizer_digest(critic),
        "expected_valuenorm_fingerprint": vn.fingerprint_digest,
        "target_classification": "raw_returns_minus_final",
    }
    values.update(changes)
    return R4.B2R4MutationPermitV1(**values)


def _consume(context, critic, vn, partition, raw_digest, permit, *, operation, component_kind, ledger=None, state=None):
    (R4.B2R4PermitLedgerV1() if ledger is None else ledger).consume(
        permit,
        authority=context.authority,
        route_state=R4.B2R4RouteStateV1() if state is None else state,
        component_kind=component_kind,
        epoch=0,
        minibatch=0,
        canonical_indices=partition,
        raw_target_digest=raw_digest,
        operation=operation,
        critic_parameter_fingerprint=R4._parameter_digest(critic),
        critic_optimizer_fingerprint=R4._optimizer_digest(critic),
        valuenorm_fingerprint=vn.fingerprint_digest,
    )


def test_authority_target_faults() -> dict[str, object]:
    context = H.make_context(suffix="authority-fault")
    stale_update = replace(context.plan, update_id="stale-update")
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: R4.execute_critic_sequence_v1(authority=context.authority, frozen_inputs=context.frozen_inputs, critic_plan=stale_update, actors=context.components.actors, critic=context.components.critic, live_value_normalizer=context.components.live_value_normalizer, inputs=context.inputs, route_state=R4.B2R4RouteStateV1(), counter=GLOBAL_COUNTER))
    stale_config = replace(context.plan, authority_config_digest=H.R1.digest("stale-config"))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: R4.execute_critic_sequence_v1(authority=context.authority, frozen_inputs=context.frozen_inputs, critic_plan=stale_config, actors=context.components.actors, critic=context.components.critic, live_value_normalizer=context.components.live_value_normalizer, inputs=context.inputs, route_state=R4.B2R4RouteStateV1(), counter=GLOBAL_COUNTER))
    wrong_target = replace(context.plan, raw_target_digest=H.R1.digest("wrong-target"))
    H.expect_stop(R4.STOP_CRITIC_TRAINING_SLICE, lambda: R4.execute_critic_sequence_v1(authority=context.authority, frozen_inputs=context.frozen_inputs, critic_plan=wrong_target, actors=context.components.actors, critic=context.components.critic, live_value_normalizer=context.components.live_value_normalizer, inputs=context.inputs, route_state=R4.B2R4RouteStateV1(), counter=GLOBAL_COUNTER))
    nonfinite_inputs = replace(context.inputs, returns_storage=context.inputs.returns_storage.clone())
    nonfinite_inputs.returns_storage[0, 0, 0] = float("nan")
    H.expect_stop(R4.STOP_NONFINITE_TARGET, lambda: R4.execute_critic_sequence_v1(authority=context.authority, frozen_inputs=context.frozen_inputs, critic_plan=context.plan, actors=context.components.actors, critic=context.components.critic, live_value_normalizer=context.components.live_value_normalizer, inputs=nonfinite_inputs, route_state=R4.B2R4RouteStateV1(), counter=GLOBAL_COUNTER))
    partitions = context.plan.partitions_by_epoch
    plan_cases = (
        (((0, 1), (3, 4, 5)),),
        (((0, 1, 2), (2, 3, 4, 5)),),
        (((0, 1, 2), (3, 4, 6)),),
        (((0, 1, 2), (3, 4, context.B)),),
    )
    for bad in plan_cases:
        H.expect_stop(P.STOP_CRITIC_ROW_COVERAGE, lambda bad=bad: P.build_critic_update_plan_v1(authority=context.base_authority, authority_config_digest=context.base_authority.config_digest, approved_partitions_by_epoch=bad * context.plan.critic_epoch_count, raw_target_digest=context.plan.raw_target_digest))
    H.expect_stop(P.STOP_CRITIC_ROW_COVERAGE, lambda: P.build_exact_partitions_v1(B=7, epoch_count=1, minibatch_count=3, partition_policy="exact_divisible"))
    return {"authority_target_faults": 9}


def test_valuenorm_permit_faults() -> dict[str, object]:
    context, critic, vn, partition, raw_digest = _permit_context()
    op = C.B2RPermitOperationV1.VALUENORM_UPDATE
    component = "live_valuenorm"
    valid = _permit(context, critic, vn, partition, raw_digest, operation=op, component_kind=component)
    H.expect_stop(E.STOP_VALUENORM, lambda: _consume(context, critic, vn, partition, raw_digest, None, operation=op, component_kind=component))
    ledger = R4.B2R4PermitLedgerV1(); _consume(context, critic, vn, partition, raw_digest, valid, operation=op, component_kind=component, ledger=ledger)
    H.expect_stop(E.STOP_VALUENORM, lambda: _consume(context, critic, vn, partition, raw_digest, valid, operation=op, component_kind=component, ledger=ledger))
    cases = (
        {"update_id": "stale-update"},
        {"authority_config_digest": H.R1.digest("stale-config")},
        {"component_kind": "critic"},
        {"epoch": 1},
        {"minibatch": 1},
        {"canonical_index_digest": H.R1.digest("wrong-rows")},
        {"raw_target_digest": H.R1.digest("wrong-raw")},
        {"expected_valuenorm_fingerprint": H.R1.digest("stale-vn")},
        {"target_classification": "normalized_target"},
    )
    for changes in cases:
        H.expect_stop(E.STOP_VALUENORM, lambda changes=changes: _consume(context, critic, vn, partition, raw_digest, _permit(context, critic, vn, partition, raw_digest, **{"operation": op, "component_kind": component, **changes}), operation=op, component_kind=component))
    H.expect_stop(E.STOP_VALUENORM, lambda: R4.validate_same_raw_normalization_v1(update_digest=raw_digest, normalize_digest=H.R1.digest("different-raw"), same_object=True))
    H.expect_stop(E.STOP_VALUENORM, lambda: R4.validate_same_raw_normalization_v1(update_digest=raw_digest, normalize_digest=raw_digest, same_object=False))
    H.expect_stop(R4.STOP_NONFINITE_VALUENORM_STATE, lambda: R4.validate_valuenorm_state_claim_v1(finite=False, mutated=True))
    H.expect_stop(R4.STOP_MUTATION_ATTRIBUTION, lambda: R4.validate_valuenorm_state_claim_v1(finite=True, mutated=False))
    return {"valuenorm_faults": 15}


def test_critic_permit_state_faults() -> dict[str, object]:
    context, critic, vn, partition, raw_digest = _permit_context()
    backward = C.B2RPermitOperationV1.BACKWARD
    step = C.B2RPermitOperationV1.OPTIMIZER_STEP
    valid_backward = _permit(context, critic, vn, partition, raw_digest, operation=backward, component_kind="critic")
    H.expect_stop(R4.STOP_UNAUTHORIZED_BACKWARD, lambda: _consume(context, critic, vn, partition, raw_digest, None, operation=backward, component_kind="critic"))
    ledger = R4.B2R4PermitLedgerV1(); _consume(context, critic, vn, partition, raw_digest, valid_backward, operation=backward, component_kind="critic", ledger=ledger)
    H.expect_stop(R4.STOP_UNAUTHORIZED_BACKWARD, lambda: _consume(context, critic, vn, partition, raw_digest, valid_backward, operation=backward, component_kind="critic", ledger=ledger))
    valid_step = _permit(context, critic, vn, partition, raw_digest, operation=step, component_kind="critic")
    H.expect_stop(R4.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda: _consume(context, critic, vn, partition, raw_digest, None, operation=step, component_kind="critic"))
    ledger2 = R4.B2R4PermitLedgerV1(); _consume(context, critic, vn, partition, raw_digest, valid_step, operation=step, component_kind="critic", ledger=ledger2)
    H.expect_stop(R4.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda: _consume(context, critic, vn, partition, raw_digest, valid_step, operation=step, component_kind="critic", ledger=ledger2))
    step_cases = (
        {"expected_critic_parameter_fingerprint": H.R1.digest("stale-param")},
        {"expected_critic_optimizer_fingerprint": H.R1.digest("stale-opt")},
        {"expected_valuenorm_fingerprint": H.R1.digest("stale-vn")},
        {"epoch": 1},
        {"minibatch": 1},
        {"canonical_index_digest": H.R1.digest("wrong-rows")},
    )
    for changes in step_cases:
        H.expect_stop(R4.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda changes=changes: _consume(context, critic, vn, partition, raw_digest, _permit(context, critic, vn, partition, raw_digest, operation=step, component_kind="critic", **changes), operation=step, component_kind="critic"))
    H.expect_stop(R4.STOP_NONFINITE_LOSS, lambda: R4.validate_pre_backward_loss_v1(raw_finite=True, normalized_finite=True, prediction_finite=True, loss_finite=False))
    H.expect_stop(R4.STOP_NONFINITE_GRADIENT, lambda: R4.validate_gradient_clip_claim_v1(owned_finite=False, aggregate_norm=1.0, clip_result=1.0, foreign_gradient_names=()))
    H.expect_stop(R4.STOP_NONFINITE_GRADIENT, lambda: R4.validate_gradient_clip_claim_v1(owned_finite=True, aggregate_norm=1.0, clip_result=float("inf"), foreign_gradient_names=()))
    H.expect_stop(R4.STOP_MUTATION_ATTRIBUTION, lambda: R4.validate_gradient_clip_claim_v1(owned_finite=True, aggregate_norm=1.0, clip_result=1.0, foreign_gradient_names=("actor0.x",)))
    H.expect_stop(R4.STOP_NONFINITE_PARAMETER, lambda: R4.validate_post_step_state_claim_v1(parameter_finite=False, optimizer_finite=True, parameter_mutated=True, optimizer_mutated=True))
    H.expect_stop(R4.STOP_NONFINITE_OPTIMIZER_STATE, lambda: R4.validate_post_step_state_claim_v1(parameter_finite=True, optimizer_finite=False, parameter_mutated=True, optimizer_mutated=True))
    H.expect_stop(R4.STOP_MUTATION_ATTRIBUTION, lambda: R4.validate_post_step_state_claim_v1(parameter_finite=True, optimizer_finite=True, parameter_mutated=False, optimizer_mutated=True))
    return {"critic_permit_state_faults": 17}


def test_count_actor_faults() -> dict[str, object]:
    for observed in ((3, 4, 4), (4, 3, 4), (4, 4, 3)):
        H.expect_stop(R4.STOP_UNEXPECTED_STEP_COUNT, lambda observed=observed: R4.validate_count_claim_v1(expected=(4, 4, 4), observed=observed))
    expected = {"actor0": H.R1.digest("actor0"), "actor0.optimizer": H.R1.digest("actor0-opt")}
    changed = dict(expected); changed["actor0"] = H.R1.digest("changed")
    H.expect_stop(R4.STOP_MUTATION_ATTRIBUTION, lambda: R4.validate_actor_freeze_claim_v1(expected=expected, observed=changed))
    trap = R4.B2R4ActorStepTrapV1(GLOBAL_COUNTER)
    H.expect_stop(R4.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda: trap.step())
    return {"count_faults": 3, "actor_freeze_faults": 2, "actor_step_attempts_trapped": 1}


def _poison_attempt(context, state):
    _, critic, vn, partition, raw_digest = _permit_context()
    permit = _permit(context, critic, vn, partition, raw_digest, operation=C.B2RPermitOperationV1.OPTIMIZER_STEP, component_kind="critic")
    R4.B2R4PermitLedgerV1().consume(permit, authority=context.authority, route_state=state, component_kind="critic", epoch=0, minibatch=0, canonical_indices=partition, raw_target_digest=raw_digest, operation=C.B2RPermitOperationV1.OPTIMIZER_STEP, critic_parameter_fingerprint=R4._parameter_digest(critic), critic_optimizer_fingerprint=R4._optimizer_digest(critic), valuenorm_fingerprint=vn.fingerprint_digest)


def test_post_valuenorm_poisoning() -> dict[str, object]:
    context = H.make_context(suffix="post-vn")
    snapshot = H.snapshot_mutable_state(context); before_digest = E.canonical_digest_v1(snapshot)
    state = R4.B2R4RouteStateV1()
    before = (GLOBAL_COUNTER.critic_backward_executed, GLOBAL_COUNTER.critic_step_executed, GLOBAL_COUNTER.live_valuenorm_executed)
    H.expect_stop(E.STOP_VALUENORM, lambda: _execute(context, state=state, synthetic_fault="post_valuenorm"))
    delta = (GLOBAL_COUNTER.critic_backward_executed - before[0], GLOBAL_COUNTER.critic_step_executed - before[1], GLOBAL_COUNTER.live_valuenorm_executed - before[2])
    failure = state.last_failure
    H.assert_true(delta == (0, 0, 1), "post-ValueNorm counts")
    H.assert_true(failure is not None and failure.partial_update and failure.route_poisoned and not failure.rollover_allowed and not failure.checkpoint_allowed and not failure.next_rollout_allowed and not failure.public_use_allowed, "post-ValueNorm poison")
    H.restore_mutable_state(context, snapshot)
    H.assert_true(E.canonical_digest_v1(H.snapshot_mutable_state(context)) == before_digest and state.route_poisoned, "post-ValueNorm restore/poison")
    return {"post_valuenorm_poisoned_failures": 1, "delta": delta, "restoration_exact": True, "logical_poison_retained": True}


def test_post_step_poisoning() -> dict[str, object]:
    context = H.make_context(suffix="post-step")
    snapshot = H.snapshot_mutable_state(context); before_digest = E.canonical_digest_v1(snapshot)
    state = R4.B2R4RouteStateV1()
    before = (GLOBAL_COUNTER.critic_backward_executed, GLOBAL_COUNTER.critic_step_executed, GLOBAL_COUNTER.live_valuenorm_executed)
    H.expect_stop(R4.STOP_MUTATION_ATTRIBUTION, lambda: _execute(context, state=state, synthetic_fault="post_step"))
    delta = (GLOBAL_COUNTER.critic_backward_executed - before[0], GLOBAL_COUNTER.critic_step_executed - before[1], GLOBAL_COUNTER.live_valuenorm_executed - before[2])
    failure = state.last_failure
    H.assert_true(delta == (1, 1, 1), "post-step counts")
    H.assert_true(failure is not None and failure.partial_update and failure.route_poisoned and not failure.rollover_allowed and not failure.checkpoint_allowed and not failure.next_rollout_allowed and not failure.public_use_allowed, "post-step poison")
    H.restore_mutable_state(context, snapshot)
    H.assert_true(E.canonical_digest_v1(H.snapshot_mutable_state(context)) == before_digest and state.route_poisoned, "post-step restore/poison")
    return {"post_critic_step_poisoned_failures": 1, "delta": delta, "later_minibatches": 0, "restoration_exact": True, "logical_poison_retained": True}


def test_static_public_guards() -> dict[str, object]:
    source_dir = H.R1.SCAN_SOURCE
    test_dir = Path(__file__).resolve().parent
    guarded = (
        source_dir / "assignment_event_training_critic_mutation.py",
        source_dir / "assignment_event_training_critic_mutation_guards.py",
        test_dir / "_assignment_phase_b2_r4_critic_mutation_helpers.py",
        Path(__file__).resolve(),
    )
    evidence = SG.validate_r4_source_guards_v1(guarded)
    private_extensions = tuple(sorted(source_dir.glob("assignment_event_training_*.py")))
    public_files = tuple(sorted(path for path in source_dir.glob("*.py") if path not in private_extensions))
    tokens = ("assignment_event_training_critic_mutation", "assignment_event_training_critic_mutation_guards")
    public = SG.validate_r4_public_isolation_v1(public_files, private_tokens=tokens)
    faults = (
        (SG.STOP_UNAUTHORIZED_BACKWARD, "loss.backward()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "optimizer.step()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "actor.actor_optimizer.step()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "scheduler.step()"),
        (SG.STOP_VALUENORM, "valuenorm.update(values)"),
        (SG.STOP_CRITIC_TRAINING_SLICE, "VCritic.update(sample)"),
        (SG.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.update(sample)"),
        (SG.STOP_STOCK_RETURNS_BYPASS, "buffer.compute_returns()"),
    )
    for index, (stop, source) in enumerate(faults):
        H.expect_stop(stop, lambda index=index, source=source: SG.validate_r4_source_text_fault_v1(source, identity=f"r4-static-{index}"))
    H.expect_stop(SG.STOP_PUBLIC_ROUTE_OPEN, lambda: SG.validate_r4_public_source_text_v1("import assignment_event_training_critic_mutation", identity="r4-public", private_tokens=tokens))
    H.assert_true((evidence.critic_step_call_count, evidence.live_valuenorm_update_call_count, evidence.backward_call_count) == (1, 1, 0), "R4 centralized calls")
    H.assert_true(public.violation_count == 0 and len(public_files) == 57, "R4 public isolation")
    H.assert_true(R4.__all__ == () and SG.__all__ == (), "R4 private exports")
    return {"reviewed_critic_step_call_sites": 1, "reviewed_live_valuenorm_update_call_sites": 1, "r4_backward_call_sites": 0, "guarded_r4_files": 4, "guarded_production_files": 57, "static_public_faults": 9}


def execution_counts() -> dict[str, object]:
    return {
        "critic_backward_executed": GLOBAL_COUNTER.critic_backward_executed,
        "critic_optimizer_step_executed": GLOBAL_COUNTER.critic_step_executed,
        "live_valuenorm_update_executed": GLOBAL_COUNTER.live_valuenorm_executed,
        "actor_backward_executed": GLOBAL_COUNTER.actor_backward_executed,
        "actor_optimizer_step_attempted": GLOBAL_COUNTER.actor_step_attempted,
        "actor_optimizer_step_executed": GLOBAL_COUNTER.actor_step_executed,
        "scheduler_step_executed": GLOBAL_COUNTER.scheduler_step_executed,
    }


def main() -> None:
    results: dict[str, object] = {}
    try:
        enabled, _ = test_enabled_sequence(); results["enabled"] = enabled
        results["disabled"] = test_disabled_sequence()
        results["remainder"] = test_remainder_safe_sequence()
        results["authority_target_faults"] = test_authority_target_faults()
        results["valuenorm_faults"] = test_valuenorm_permit_faults()
        results["critic_faults"] = test_critic_permit_state_faults()
        results["count_actor_faults"] = test_count_actor_faults()
        results["post_valuenorm_poison"] = test_post_valuenorm_poisoning()
        results["post_step_poison"] = test_post_step_poisoning()
        results["static_public"] = test_static_public_guards()
    except BaseException:
        print(json.dumps({"status": "FAIL", "tests": results, "execution_counts": execution_counts()}, sort_keys=True))
        raise
    counts = execution_counts()
    H.assert_true(counts == {
        "critic_backward_executed": 10,
        "critic_optimizer_step_executed": 10,
        "live_valuenorm_update_executed": 9,
        "actor_backward_executed": 0,
        "actor_optimizer_step_attempted": 1,
        "actor_optimizer_step_executed": 0,
        "scheduler_step_executed": 0,
    }, "exact R4 execution counts")
    print(json.dumps({"status": "PASS", "tests": results, "execution_counts": counts, "pre_mutation_failure_assertions": 55, "post_valuenorm_poisoned_failures": 1, "post_critic_step_poisoned_failures": 1}, sort_keys=True))


if __name__ == "__main__":
    main()
