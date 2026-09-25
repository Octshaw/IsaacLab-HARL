"""Pure actor/critic plan, exact coverage, and full-index factor tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as H  # noqa: E402


def _actor_plan(*, policy: str = "match_backward"):
    authority = H.authority()
    partitions = H.P.build_exact_partitions_v1(
        B=authority.B,
        epoch_count=authority.resolved_config.actor_epoch_count,
        minibatch_count=authority.resolved_config.actor_minibatch_count,
        partition_policy="reviewed_exact_coverage",
    )
    return H.P.build_actor_update_plan_v1(
        authority=authority,
        authority_config_digest=authority.config_digest,
        actor_permutation=(2, 0, 1),
        approved_partitions_by_epoch=partitions,
        dvm_indices_by_actor={0: (), 1: (0, 4, 5, 11), 2: (1, 2, 8, 9)},
        active_indices_by_actor={0: (0, 1), 1: (0, 8, 11), 2: (1, 8)},
        factor_input_digest=H.digest("factor-input"),
        optimizer_step_policy=policy,
    )


def test_actor_plan() -> dict[str, object]:
    P, E = H.P, H.E
    authority = H.authority()
    plan = _actor_plan()
    H.assert_true(plan.plan_digest == _actor_plan().plan_digest, "actor plan digest")
    backward = dict(plan.expected_backward_count_by_actor)
    steps = dict(plan.expected_optimizer_step_count_by_actor)
    H.assert_true(backward[0] == 0 and steps[0] == 0, "forced actor counts")
    H.assert_true(any(item.dvm_evaluation_indices and not item.active_and_dvm_loss_indices for item in plan.minibatches), "inactive DVM fixture")
    no_step = _actor_plan(policy="disabled")
    H.assert_true(any(count > 0 for _, count in no_step.expected_backward_count_by_actor) and all(count == 0 for _, count in no_step.expected_optimizer_step_count_by_actor), "R2 no-step representability")
    partitions = P.build_exact_partitions_v1(B=authority.B, epoch_count=2, minibatch_count=3, partition_policy="reviewed_exact_coverage")
    common = dict(authority=authority, authority_config_digest=authority.config_digest, approved_partitions_by_epoch=partitions,
                  dvm_indices_by_actor={0: (), 1: (0,), 2: (1,)}, active_indices_by_actor={0: (), 1: (0,), 2: (1,)},
                  factor_input_digest=H.digest("factor-input"))
    for permutation in ((0, 0, 2), (0, 1), (0, 1, 3)):
        H.expect_stop(P.STOP_AGENT_ORDER, lambda permutation=permutation: P.build_actor_update_plan_v1(actor_permutation=permutation, **common))
    bad_dvm = {0: (), 1: (authority.B,), 2: (1,)}
    H.expect_stop(P.STOP_FORCED_ROW_POLICY_LEAK, lambda: P.build_actor_update_plan_v1(actor_permutation=(0, 1, 2), **{**common, "dvm_indices_by_actor": bad_dvm}))
    H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda: P.build_actor_update_plan_v1(actor_permutation=(0, 1, 2), **{**common, "authority_config_digest": H.digest("wrong")}))
    H.expect_stop(P.STOP_FORCED_ROW_POLICY_LEAK, lambda: P.B2RActorMinibatchPlanV1(0, 0, 0, (0, 1), (0,), (1,), False))
    H.expect_stop(P.STOP_FORCED_ROW_POLICY_LEAK, lambda: P.B2RActorMinibatchPlanV1(0, 0, 0, (0, 1), (0, 1), (0, 0), False))
    H.expect_stop(P.STOP_UNEXPECTED_STEP_COUNT, lambda: replace(plan, expected_backward_count_by_actor=((0, 99), (1, 0), (2, 0))))
    return {"mixed_multi_t_env": 1, "deterministic": 1, "r2_disabled_steps_schema": 1, "actor_faults": 8}


def test_factor() -> dict[str, object]:
    P = H.P
    shape = (3, 4, 1)
    factor0 = torch.ones(shape, dtype=torch.float64)
    mask0 = torch.zeros(shape, dtype=torch.bool)
    mask0[0, 0, 0] = True
    mask0[1, 2, 0] = True
    pre = torch.zeros(shape, dtype=torch.float64)
    post = torch.zeros(shape, dtype=torch.float64)
    post[mask0] = torch.tensor([0.2, -0.1], dtype=torch.float64)
    first = P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor0, decision_valid_mask=mask0, factor_pre_logprob=pre, factor_post_logprob=post)
    H.assert_true(tuple(first.factor_after.shape) == shape, "full factor shape")
    mask1 = torch.zeros(shape, dtype=torch.bool)
    mask1[2, 3, 0] = True
    skipped = P.compute_full_index_factor_transition_v1(actor_id=1, factor_before=first.factor_after, decision_valid_mask=mask1, factor_pre_logprob=pre, factor_post_logprob=post, skipped_actor=True)
    H.assert_true(torch.equal(skipped.factor_after, first.factor_after), "skipped actor changed factor")
    H.assert_true(skipped.factor_after[0, 0, 0] != 1, "prior factor was reset")
    H.assert_true(first.evidence.off_dvm_exact_one and first.evidence.recurrence_exact, "factor evidence")
    H.expect_stop(P.STOP_FACTOR, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor0, decision_valid_mask=mask0, factor_pre_logprob=pre, factor_post_logprob=post, scatter_indices=(0, 0)))
    bad = pre.clone(); bad[0, 0, 0] = float("nan")
    H.expect_stop(P.STOP_FACTOR, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor0, decision_valid_mask=mask0, factor_pre_logprob=bad, factor_post_logprob=post))
    huge = post.clone(); huge[mask0] = 1000.0
    H.expect_stop(P.STOP_FACTOR, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor0, decision_valid_mask=mask0, factor_pre_logprob=pre, factor_post_logprob=huge))
    under = post.clone(); under[mask0] = -1000.0
    H.expect_stop(P.STOP_FACTOR, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=factor0, decision_valid_mask=mask0, factor_pre_logprob=pre, factor_post_logprob=under))
    zero = factor0.clone(); zero[0, 0, 0] = 0.0
    H.expect_stop(P.STOP_FACTOR, lambda: P.compute_full_index_factor_transition_v1(actor_id=0, factor_before=zero, decision_valid_mask=mask0, factor_pre_logprob=pre, factor_post_logprob=post))
    H.expect_stop(P.STOP_FACTOR, lambda: replace(first.evidence, off_dvm_exact_one=False))
    H.expect_stop(P.STOP_FACTOR, lambda: replace(first.evidence, strictly_positive=False))
    H.expect_stop(P.STOP_FACTOR, lambda: replace(first.evidence, recurrence_exact=False))
    H.expect_stop(P.STOP_FACTOR, lambda: replace(skipped.evidence, recurrence_exact=False))
    return {"full_index_transitions": 2, "off_dvm_exact_one": True, "factor_faults": 9, "executed_mutations": 0}


def test_critic_plan() -> dict[str, object]:
    P = H.P
    authority = H.authority()
    config = authority.resolved_config
    partitions = P.build_exact_partitions_v1(B=authority.B, epoch_count=config.critic_epoch_count, minibatch_count=config.critic_minibatch_count, partition_policy="reviewed_exact_coverage")
    plan = P.build_critic_update_plan_v1(authority=authority, authority_config_digest=authority.config_digest, approved_partitions_by_epoch=partitions, raw_target_digest=H.digest("returns-minus-final"))
    H.assert_true(plan.expected_backward_count == 10 and plan.expected_optimizer_step_count == 10 and plan.expected_valuenorm_update_count == 10, "derived counts")
    disabled = P.build_critic_update_plan_v1(authority=authority, authority_config_digest=authority.config_digest, approved_partitions_by_epoch=partitions, raw_target_digest=H.digest("returns-minus-final"), optimizer_step_policy="disabled")
    H.assert_true(disabled.expected_backward_count == 10 and disabled.expected_optimizer_step_count == 0 and disabled.expected_valuenorm_update_count == 0, "disabled step counts")
    no_vn_auth = H.authority(cfg=H.config(valuenorm_enabled=False))
    no_vn_parts = P.build_exact_partitions_v1(B=no_vn_auth.B, epoch_count=2, minibatch_count=5, partition_policy="reviewed_exact_coverage")
    no_vn = P.build_critic_update_plan_v1(authority=no_vn_auth, authority_config_digest=no_vn_auth.config_digest, approved_partitions_by_epoch=no_vn_parts, raw_target_digest=H.digest("target"))
    H.assert_true(no_vn.expected_valuenorm_update_count == 0, "ValueNorm disabled count")
    epoch0 = list(partitions[0])
    fault_partitions = [
        (tuple(epoch0[:-1]), partitions[1]),
        ((epoch0[0][:-1],) + tuple(epoch0[1:]), partitions[1]),
        (((epoch0[0] + (epoch0[1][0],)),) + tuple(epoch0[1:]), partitions[1]),
        ((((authority.B,),) + tuple(epoch0[1:])), partitions[1]),
        ((((),) + tuple(epoch0[1:])), partitions[1]),
        (partitions[0],),
    ]
    for bad in fault_partitions:
        H.expect_stop(P.STOP_CRITIC_ROW_COVERAGE, lambda bad=bad: P.build_critic_update_plan_v1(authority=authority, authority_config_digest=authority.config_digest, approved_partitions_by_epoch=bad, raw_target_digest=H.digest("target")))
    H.expect_stop(P.STOP_CRITIC_ROW_COVERAGE, lambda: P.build_exact_partitions_v1(B=12, epoch_count=1, minibatch_count=5, partition_policy="exact_divisible"))
    H.expect_stop(H.E.STOP_AUTHORITY_DRIFT, lambda: P.build_critic_update_plan_v1(authority=authority, authority_config_digest=H.digest("wrong"), approved_partitions_by_epoch=partitions, raw_target_digest=H.digest("target")))
    H.expect_stop(P.STOP_UNEXPECTED_STEP_COUNT, lambda: replace(plan, expected_optimizer_step_count=9))
    H.expect_stop(P.STOP_UNEXPECTED_STEP_COUNT, lambda: replace(plan, expected_valuenorm_update_count=9))
    return {"exact_rows_per_epoch": authority.B, "derived_counts": 3, "critic_faults": 10}


if __name__ == "__main__":
    H.run([("actor_plan", test_actor_plan), ("factor", test_factor), ("critic_plan", test_critic_plan)])
