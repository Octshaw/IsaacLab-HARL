"""B2-R3 real actor Adam mutation and sequential full-index factor tests."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import torch

import _assignment_phase_b2_r3_actor_mutation_helpers as H


R3, E, P, C, SG = H.R3, H.E, H.P, H.C, H.SG
GLOBAL_COUNTER = R3.B2R3ExecutionCounterV1(H.ACTORS)


def test_authority_and_order() -> dict[str, object]:
    context = H.make_context()
    freezer = R3.B2R3ActorOrderFreezerV1(context.base_authority)
    evidence = freezer.freeze(rng_seed=H.ORDER_SEED)
    H.expect_stop(P.STOP_AGENT_ORDER, lambda: freezer.freeze(rng_seed=H.ORDER_SEED))
    H.expect_stop(P.STOP_AGENT_ORDER, lambda: replace(evidence, actor_order=(0, 0, 1)))
    H.expect_stop(P.STOP_AGENT_ORDER, lambda: replace(evidence, actor_order=(0, 1)))
    state = R3.B2R3RouteStateV1()
    before = GLOBAL_COUNTER.actor_step_executed
    H.expect_stop(
        P.STOP_AGENT_ORDER,
        lambda: R3.execute_actor_sequence_v1(
            authority=context.authority,
            frozen_inputs=context.frozen_inputs,
            actor_plan=context.plan,
            actors=context.components.actors,
            critic=context.components.critic,
            live_value_normalizer=context.components.live_value_normalizer,
            actor_inputs=context.actor_inputs,
            initial_factor=context.factor,
            route_state=state,
            counter=GLOBAL_COUNTER,
            claimed_actor_order=(1, 0, 2),
        ),
    )
    H.assert_true(GLOBAL_COUNTER.actor_step_executed == before, "order fault stepped")
    H.assert_true(state.last_failure is not None and not state.last_failure.partial_update, "order pre-step failure classification")
    return {"actor_order": evidence.actor_order, "rng_seed": evidence.rng_seed, "order_faults": 4}


def _permit_fixture(context, **changes):
    values = {
        "permit_id": "step-permit",
        "update_id": context.authority.update_id,
        "authority_config_digest": context.authority.config_digest,
        "actor_id": 0,
        "actor_order_position": 0,
        "epoch": 0,
        "minibatch": 0,
        "canonical_index_digest": E.canonical_digest_v1((0,)),
        "operation": C.B2RPermitOperationV1.OPTIMIZER_STEP,
        "expected_module_fingerprint": H.R1.digest("module"),
        "expected_optimizer_fingerprint": H.R1.digest("optimizer"),
        "empty_minibatch": False,
    }
    values.update(changes)
    return R3.B2R3MutationPermitV1(**values)


def _consume_step(context, permit, *, ledger=None, state=None):
    R3.consume_actor_step_permit_v1(
        ledger=R3.B2R3PermitLedgerV1() if ledger is None else ledger,
        permit=permit,
        authority=context.authority,
        route_state=R3.B2R3RouteStateV1() if state is None else state,
        actor_id=0,
        actor_order_position=0,
        epoch=0,
        minibatch=0,
        canonical_indices=(0,),
        module_fingerprint=H.R1.digest("module"),
        optimizer_fingerprint=H.R1.digest("optimizer"),
        counter=GLOBAL_COUNTER,
    )


def test_step_permit_faults() -> dict[str, object]:
    context = H.make_context()
    stop = R3.STOP_UNAUTHORIZED_OPTIMIZER_STEP
    H.expect_stop(stop, lambda: _consume_step(context, None))
    ledger = R3.B2R3PermitLedgerV1()
    valid = _permit_fixture(context)
    _consume_step(context, valid, ledger=ledger)
    H.expect_stop(stop, lambda: _consume_step(context, valid, ledger=ledger))
    faults = (
        {"update_id": "stale-update"},
        {"authority_config_digest": H.R1.digest("stale-config")},
        {"actor_id": 1},
        {"actor_order_position": 2},
        {"epoch": 1},
        {"minibatch": 1},
        {"canonical_index_digest": E.canonical_digest_v1((1,))},
        {"expected_module_fingerprint": H.R1.digest("stale-module")},
        {"expected_optimizer_fingerprint": H.R1.digest("stale-optimizer")},
        {"empty_minibatch": True},
        {"operation": C.B2RPermitOperationV1.BACKWARD},
    )
    for changes in faults:
        H.expect_stop(stop, lambda changes=changes: _consume_step(context, _permit_fixture(context, **changes)))
    poisoned = R3.B2R3RouteStateV1()
    poisoned.record_failure(stop_code=P.STOP_FACTOR, executed_steps=1)
    H.expect_stop(stop, lambda: _consume_step(context, valid, state=poisoned))
    H.assert_true(GLOBAL_COUNTER.unauthorized_actor_step_attempted == 14, "unauthorized step trap count")
    H.assert_true(GLOBAL_COUNTER.actor_step_executed == 0, "permit faults executed a step")
    return {"step_permit_faults": 14, "unauthorized_actor_step_attempts_trapped": 14}


def test_pre_step_faults() -> dict[str, object]:
    context = H.make_context()
    parameter = next(context.components.actors[0].actor.parameters())
    parameter.grad = torch.zeros_like(parameter)
    H.expect_stop(
        R3.STOP_MUTATION_ATTRIBUTION,
        lambda: R3._capture_components_v1(
            actors=context.components.actors,
            critic=context.components.critic,
            live_value_normalizer=context.components.live_value_normalizer,
        ),
    )
    parameter.grad = None
    gates = (
        (R3.STOP_NONFINITE_LOSS, dict(loss_finite=False, owned_gradients_finite=True, aggregate_gradient_norm=1.0, clip_result=1.0, foreign_gradient_names=())),
        (R3.STOP_NONFINITE_GRADIENT, dict(loss_finite=True, owned_gradients_finite=False, aggregate_gradient_norm=1.0, clip_result=1.0, foreign_gradient_names=())),
        (R3.STOP_NONFINITE_GRADIENT, dict(loss_finite=True, owned_gradients_finite=True, aggregate_gradient_norm=1.0, clip_result=float("inf"), foreign_gradient_names=())),
        (R3.STOP_MUTATION_ATTRIBUTION, dict(loss_finite=True, owned_gradients_finite=True, aggregate_gradient_norm=1.0, clip_result=1.0, foreign_gradient_names=("critic.x",))),
    )
    for stop, kwargs in gates:
        H.expect_stop(stop, lambda kwargs=kwargs: R3.validate_pre_step_gate_v1(**kwargs))
    return {"pre_step_state_faults": 5}


def test_successful_sequence() -> tuple[dict[str, object], object]:
    context = H.make_context()
    state = R3.B2R3RouteStateV1()
    receipt = R3.execute_actor_sequence_v1(
        authority=context.authority,
        frozen_inputs=context.frozen_inputs,
        actor_plan=context.plan,
        actors=context.components.actors,
        critic=context.components.critic,
        live_value_normalizer=context.components.live_value_normalizer,
        actor_inputs=context.actor_inputs,
        initial_factor=context.factor,
        route_state=state,
        counter=GLOBAL_COUNTER,
    )
    segments = {item.actor_id: item for item in receipt.actor_segments}
    dvm_rows = {
        actor_id: R3._canonical_true_row_indices_v1(context.actor_inputs[actor_id].decision_valid_mask)
        for actor_id in range(H.ACTORS)
    }
    off_dvm_rows = {
        actor_id: R3._canonical_true_row_indices_v1(~context.actor_inputs[actor_id].decision_valid_mask)
        for actor_id in range(H.ACTORS)
    }
    H.assert_true(
        all(tuple(inputs.decision_valid_mask.shape) == (H.B, 1) for inputs in context.actor_inputs.values()),
        "controlled factor path did not use [B,1] DVM masks",
    )
    H.assert_true(
        dvm_rows == {0: (0, 1, 3, 4), 1: (0, 1, 4, 5), 2: ()},
        "canonical DVM rows",
    )
    H.assert_true(
        off_dvm_rows == {0: (2, 5), 1: (2, 3), 2: (0, 1, 2, 3, 4, 5)},
        "canonical off-DVM rows",
    )
    H.assert_true(receipt.actor_order == (0, 1, 2), "sequence order")
    H.assert_true((segments[0].observed_step_count, segments[1].observed_step_count, segments[2].observed_step_count) == (4, 4, 0), "per-actor step counts")
    H.assert_true((segments[0].observed_backward_count, segments[1].observed_backward_count, segments[2].observed_backward_count) == (4, 4, 0), "per-actor backward counts")
    H.assert_true(all(step.target_parameter_mutated and step.target_optimizer_mutated for actor in (0, 1) for step in segments[actor].step_receipts), "owned mutation evidence")
    H.assert_true(segments[1].factor_before_digest == segments[0].factor_transition.factor_after_digest, "factor handoff")
    H.assert_true(segments[1].prior_accumulation_witness_indices == (3,) and segments[1].prior_accumulation_preserved, "prior actor factor accumulation witness")
    H.assert_true(0 not in off_dvm_rows[1], "false row-0 injection")
    H.assert_true(segments[2].skipped and segments[2].factor_before_digest == segments[2].factor_transition.factor_after_digest, "forced-only actor factor")
    H.assert_true(receipt.critic_unchanged and receipt.live_valuenorm_unchanged and receipt.gradients_clean_after, "frozen foreign state")
    H.assert_true(not state.partial_update and not state.route_poisoned and state.last_failure is None, "successful route poisoned")
    return ({
        "actor_order": receipt.actor_order,
        "per_actor_backward": [4, 4, 0],
        "per_actor_step": [4, 4, 0],
        "distinct_actor_parameter_mutations": 2,
        "distinct_actor_optimizer_state_mutations": 2,
        "factor_pre_evaluations": [1, 1, 0],
        "factor_post_evaluations": [1, 1, 0],
        "factor_updates": [1, 1, 1],
        "mask_shapes": [list(context.actor_inputs[actor_id].decision_valid_mask.shape) for actor_id in range(H.ACTORS)],
        "canonical_dvm_rows": {str(actor_id): list(dvm_rows[actor_id]) for actor_id in range(H.ACTORS)},
        "canonical_off_dvm_rows": {str(actor_id): list(off_dvm_rows[actor_id]) for actor_id in range(H.ACTORS)},
        "prior_accumulation_witness": 3,
        "false_row_zero_injections": 0,
        "factor_post_audit_passes": 2,
        "factor_pre_post_digests": {
            str(actor_id): [segments[actor_id].factor_pre_logprob_digest, segments[actor_id].factor_post_logprob_digest]
            for actor_id in (0, 1)
        },
        "foreign_state_isolation": {
            "critic_unchanged": receipt.critic_unchanged,
            "live_valuenorm_unchanged": receipt.live_valuenorm_unchanged,
            "gradients_clean_after": receipt.gradients_clean_after,
        },
        "parameter_fingerprint_pairs": {
            str(actor_id): [[step.parameter_digest_before, step.parameter_digest_after] for step in segments[actor_id].step_receipts]
            for actor_id in (0, 1)
        },
        "optimizer_fingerprint_pairs": {
            str(actor_id): [[step.optimizer_digest_before, step.optimizer_digest_after] for step in segments[actor_id].step_receipts]
            for actor_id in (0, 1)
        },
        "backward_clip_receipts": {
            str(actor_id): [[step.aggregate_gradient_norm, step.clip_result] for step in segments[actor_id].step_receipts]
            for actor_id in (0, 1)
        },
        "factor_transition_digests": {
            str(actor_id): {
                "before": segments[actor_id].factor_transition.factor_before_digest,
                "ratio_full": segments[actor_id].factor_transition.ratio_full_digest,
                "after": segments[actor_id].factor_transition.factor_after_digest,
            }
            for actor_id in (0, 1, 2)
        },
    }, receipt)


def test_mutation_attribution_faults(context) -> dict[str, object]:
    expected = {"actor1": H.R1.digest("a1"), "critic": H.R1.digest("critic"), "foreign_optimizer": H.R1.digest("opt"), "live_valuenorm": H.R1.digest("vn")}
    for key in expected:
        observed = dict(expected)
        observed[key] = H.R1.digest(f"changed-{key}")
        H.expect_stop(R3.STOP_MUTATION_ATTRIBUTION, lambda observed=observed: R3.validate_foreign_state_claim_v1(expected=expected, observed=observed))
    H.expect_stop(
        P.STOP_UNEXPECTED_STEP_COUNT,
        lambda: replace(context.plan, expected_optimizer_step_count_by_actor=((0, 3), (1, 4), (2, 0))),
    )
    return {"mutation_attribution_faults": 5}


def test_factor_faults(receipt) -> dict[str, object]:
    segments = {item.actor_id: item for item in receipt.actor_segments}
    first, skipped = segments[0], segments[2]
    stop = P.STOP_FACTOR
    cases = (
        replace(first, factor_pre_logprob_field="original_rollout_behavior_logprob"),
        replace(first, factor_pre_evaluation_count=2),
        replace(first, factor_update_count=2),
        replace(first, loss_factor_digests=(H.R1.digest("self-ratio-factor"),) * len(first.loss_factor_digests)),
    )
    for case in cases:
        H.expect_stop(stop, lambda case=case: R3.validate_factor_segment_contract_v1(case, expected_dvm_indices=first.dvm_indices))
    H.expect_stop(stop, lambda: R3.validate_factor_segment_contract_v1(first, expected_dvm_indices=tuple(reversed(first.dvm_indices))))
    H.expect_stop(stop, lambda: replace(first.factor_transition, off_dvm_exact_one=False))
    H.expect_stop(stop, lambda: replace(first.factor_transition, recurrence_exact=False))
    H.expect_stop(stop, lambda: R3.validate_factor_segment_contract_v1(replace(skipped, prior_accumulation_preserved=False), expected_dvm_indices=()))
    factor = torch.ones((H.T, H.ENVIRONMENTS, 1), dtype=torch.float32)
    mask = torch.tensor([True, False, False, False, False, False]).reshape(factor.shape)
    pre = torch.zeros_like(factor)
    nonfinite = torch.zeros_like(factor); nonfinite.reshape(-1)[0] = float("inf")
    underflow = torch.zeros_like(factor); underflow.reshape(-1)[0] = -1000.0
    H.expect_stop(stop, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor, decision_valid_mask=mask, factor_pre_logprob=pre, factor_post_logprob=nonfinite))
    H.expect_stop(stop, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor, decision_valid_mask=mask, factor_pre_logprob=pre, factor_post_logprob=underflow))
    return {"factor_faults": 10, "off_dvm_exact_one": True, "recurrence_exact": True}


def test_post_step_poisoning() -> dict[str, object]:
    context = H.make_context()
    snapshot = H.snapshot_actor_mutable_state(context)
    snapshot_digest = E.canonical_digest_v1(snapshot)
    state = R3.B2R3RouteStateV1()
    before_steps = tuple(GLOBAL_COUNTER.actor_step_by_actor)
    H.expect_stop(
        P.STOP_FACTOR,
        lambda: R3.execute_actor_sequence_v1(
            authority=context.authority,
            frozen_inputs=context.frozen_inputs,
            actor_plan=context.plan,
            actors=context.components.actors,
            critic=context.components.critic,
            live_value_normalizer=context.components.live_value_normalizer,
            actor_inputs=context.actor_inputs,
            initial_factor=context.factor,
            route_state=state,
            counter=GLOBAL_COUNTER,
            synthetic_post_step_fault_actor=0,
        ),
    )
    deltas = tuple(after - before for after, before in zip(GLOBAL_COUNTER.actor_step_by_actor, before_steps))
    failure = state.last_failure
    H.assert_true(deltas == (1, 0, 0), "later actor stepped after poison")
    H.assert_true(failure is not None and failure.partial_update and failure.route_poisoned, "post-step poison classification")
    H.assert_true(not failure.rollover_allowed and not failure.checkpoint_allowed and not failure.next_rollout_allowed and not failure.public_use_allowed, "poison continuation gates")
    H.restore_actor_mutable_state(context, snapshot)
    restored_digest = E.canonical_digest_v1(H.snapshot_actor_mutable_state(context))
    H.assert_true(restored_digest == snapshot_digest, "test isolation restore")
    H.assert_true(state.route_poisoned and state.partial_update, "restoration cleared logical poison")
    return {"post_step_poisoned_failures": 1, "step_delta": deltas, "restoration_exact": True, "logical_poison_retained": True}


def test_critic_valuenorm_traps() -> dict[str, object]:
    critic_trap = R3.B2R3CriticStepTrapV1(GLOBAL_COUNTER)
    vn_trap = R3.B2R3LiveValueNormTrapV1(GLOBAL_COUNTER)
    H.expect_stop(R3.STOP_CRITIC_TRAINING_SLICE, lambda: critic_trap.step())
    H.expect_stop(E.STOP_VALUENORM, lambda: vn_trap.update(torch.ones(1)))
    H.assert_true(GLOBAL_COUNTER.critic_step_executed == 0 and GLOBAL_COUNTER.live_valuenorm_executed == 0, "forbidden trap delegated")
    return {"critic_step_attempts_trapped": 1, "live_valuenorm_attempts_trapped": 1}


def test_static_public_guards() -> dict[str, object]:
    source_dir = H.R1.SCAN_SOURCE
    test_dir = Path(__file__).resolve().parent
    guarded = (
        source_dir / "assignment_event_training_actor_mutation.py",
        source_dir / "assignment_event_training_actor_mutation_guards.py",
        test_dir / "_assignment_phase_b2_r3_actor_mutation_helpers.py",
        Path(__file__).resolve(),
    )
    evidence = SG.validate_r3_mutation_source_guards_v1(guarded)
    private_extensions = tuple(sorted(source_dir.glob("assignment_event_training_*.py")))
    public_files = tuple(sorted(path for path in source_dir.glob("*.py") if path not in private_extensions))
    tokens = ("assignment_event_training_actor_mutation", "assignment_event_training_actor_mutation_guards")
    public = SG.validate_r3_public_isolation_v1(public_files, private_tokens=tokens)
    faults = (
        (SG.STOP_UNAUTHORIZED_BACKWARD, "loss.backward()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "optimizer.step()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "scheduler.step()"),
        (SG.STOP_VALUENORM, "valuenorm.update(values)"),
        (SG.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.update(sample)"),
        (SG.STOP_CRITIC_TRAINING_SLICE, "VCritic.update(sample)"),
        (SG.STOP_STOCK_RETURNS_BYPASS, "buffer.compute_returns()"),
    )
    for index, (stop, source) in enumerate(faults):
        H.expect_stop(stop, lambda index=index, source=source: SG.validate_r3_source_text_fault_v1(source, identity=f"r3-static-{index}"))
    H.expect_stop(SG.STOP_PUBLIC_ROUTE_OPEN, lambda: SG.validate_r3_public_source_text_v1("import assignment_event_training_actor_mutation", identity="r3-public", private_tokens=tokens))
    H.assert_true(evidence.actor_step_call_count == 1 and evidence.backward_call_count == 0, "central R3 source seam")
    H.assert_true(public.violation_count == 0 and len(public_files) == 57, "R3 public isolation")
    H.assert_true(R3.__all__ == () and SG.__all__ == (), "R3 export fence")
    return {"reviewed_actor_step_call_sites": 1, "r3_backward_call_sites": 0, "guarded_r3_files": len(guarded), "guarded_production_files": len(public_files), "static_public_faults": 8}


def execution_counts() -> dict[str, object]:
    return {
        "actor_backward_executed": GLOBAL_COUNTER.actor_backward_executed,
        "actor_optimizer_step_executed": GLOBAL_COUNTER.actor_step_executed,
        "per_actor_backward": GLOBAL_COUNTER.actor_backward_by_actor,
        "per_actor_optimizer_step": GLOBAL_COUNTER.actor_step_by_actor,
        "unauthorized_actor_step_attempts_trapped": GLOBAL_COUNTER.unauthorized_actor_step_attempted,
        "critic_backward_executed": GLOBAL_COUNTER.critic_backward_executed,
        "critic_optimizer_step_attempted": GLOBAL_COUNTER.critic_step_attempted,
        "critic_optimizer_step_executed": GLOBAL_COUNTER.critic_step_executed,
        "live_valuenorm_attempted": GLOBAL_COUNTER.live_valuenorm_attempted,
        "live_valuenorm_updates": GLOBAL_COUNTER.live_valuenorm_executed,
        "scheduler_step_executed": GLOBAL_COUNTER.scheduler_step_executed,
    }


def main() -> None:
    results: dict[str, object] = {}
    try:
        results["authority_order"] = test_authority_and_order()
        results["step_permits"] = test_step_permit_faults()
        results["pre_step"] = test_pre_step_faults()
        success, receipt = test_successful_sequence()
        results["success"] = success
        context = H.make_context()
        results["mutation_attribution"] = test_mutation_attribution_faults(context)
        results["factor_faults"] = test_factor_faults(receipt)
        results["post_step_poison"] = test_post_step_poisoning()
        results["critic_valuenorm_traps"] = test_critic_valuenorm_traps()
        results["static_public"] = test_static_public_guards()
    except BaseException:
        print(json.dumps({"status": "FAIL", "tests": results, "execution_counts": execution_counts()}, sort_keys=True))
        raise
    counts = execution_counts()
    H.assert_true(counts["actor_backward_executed"] == 9 and counts["actor_optimizer_step_executed"] == 9, "exact real execution counts")
    H.assert_true(counts["per_actor_backward"] == [5, 4, 0] and counts["per_actor_optimizer_step"] == [5, 4, 0], "cumulative per-actor counts")
    print(json.dumps({"status": "PASS", "tests": results, "execution_counts": counts, "pre_step_failure_assertions": 48, "post_step_poisoned_failures": 1}, sort_keys=True))


if __name__ == "__main__":
    main()
