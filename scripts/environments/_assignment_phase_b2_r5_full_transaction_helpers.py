"""Controlled CPU fixtures for the private B2-R5 full transaction."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import sys
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as R1  # noqa: E402
import _assignment_phase_b2_r3_actor_mutation_helpers as R3H  # noqa: E402


E, P, C = R1.E, R1.P, R1.C
R3 = R1.load_canonical("assignment_event_training_actor_mutation.py")
R4 = R1.load_canonical("assignment_event_training_critic_mutation.py")
R5 = R1.load_canonical("assignment_event_training_full_transaction.py")
SG = R1.load_canonical("assignment_event_training_full_transaction_guards.py") if (
    R1.SCAN_SOURCE / "assignment_event_training_full_transaction_guards.py"
).exists() else None
CB = R1.load_canonical("assignment_event_critic_buffer.py")
TRANSITION = R1.load_canonical("assignment_lifecycle_transition_contract.py")


DEVICE = torch.device("cpu")
T, ENVIRONMENTS, ACTORS, TASKS = 2, 3, 3, 4
B = T * ENVIRONMENTS
OBS_DIM, SHARED_DIM, HIDDEN = 8, 12, 32
ORDER_SEED = 7


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_stop(stop_code: str, function) -> Any:
    try:
        function()
    except E.B2RContractError as exc:
        assert_true(exc.stop_code == stop_code, f"wrong STOP {exc.stop_code}; expected {stop_code}")
        return exc
    raise AssertionError(f"expected {stop_code}")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tensor_digest(value: torch.Tensor) -> str:
    return E.fingerprint_tensor_v1(value).content_digest


def _tuple_tensor_digest(*values: torch.Tensor) -> str:
    return E.canonical_digest_v1(tuple(_tensor_digest(value) for value in values))


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class ControlledActorStorageV1:
    """Mutable controlled storage with the frozen actor rollover semantics."""

    def __init__(self, *, actor_id: int, inputs: Any) -> None:
        self.actor_id = actor_id
        self.episode_length = T
        self.next_action_slot = T
        self.obs = torch.zeros((T + 1, ENVIRONMENTS, OBS_DIM), dtype=torch.float32)
        self.available_actions = torch.zeros((T + 1, ENVIRONMENTS, TASKS + 1), dtype=torch.float32)
        self.decision_valid_masks = torch.zeros((T + 1, ENVIRONMENTS, 1), dtype=torch.bool)
        self.active_masks = torch.zeros((T + 1, ENVIRONMENTS, 1), dtype=torch.float32)
        self.action_ids = inputs.actions.reshape(T, ENVIRONMENTS, 1).detach().clone()
        self.action_logprobs = inputs.behavior_old_logprobs.reshape(T, ENVIRONMENTS, 1).detach().clone()
        self.obs[:-1].copy_(inputs.obs.reshape(T, ENVIRONMENTS, OBS_DIM))
        self.available_actions[:-1].copy_(inputs.available_actions.reshape(T, ENVIRONMENTS, TASKS + 1))
        self.decision_valid_masks[:-1].copy_(inputs.decision_valid_mask.reshape(T, ENVIRONMENTS, 1))
        self.active_masks[:-1].copy_(inputs.active_mask.reshape(T, ENVIRONMENTS, 1).to(torch.float32))
        self.obs[-1].copy_(torch.arange(ENVIRONMENTS * OBS_DIM, dtype=torch.float32).reshape(ENVIRONMENTS, OBS_DIM) / 50.0 + actor_id)
        self.available_actions[-1].fill_(1.0)
        final_dvm = torch.tensor([[True], [actor_id != 2], [False]], dtype=torch.bool)
        self.decision_valid_masks[-1].copy_(final_dvm)
        self.active_masks[-1].copy_(torch.tensor([[1.0], [0.0], [1.0]], dtype=torch.float32))

    @property
    def final_current_slot_digest(self) -> str:
        return _tuple_tensor_digest(
            self.obs[-1], self.available_actions[-1],
            self.decision_valid_masks[-1], self.active_masks[-1],
        )

    @property
    def slot_zero_digest(self) -> str:
        return _tuple_tensor_digest(
            self.obs[0], self.available_actions[0],
            self.decision_valid_masks[0], self.active_masks[0],
        )

    @property
    def storage_digest(self) -> str:
        return E.canonical_digest_v1((
            self.actor_id, self.next_action_slot,
            _tensor_digest(self.obs), _tensor_digest(self.available_actions),
            _tensor_digest(self.decision_valid_masks), _tensor_digest(self.active_masks),
            _tensor_digest(self.action_ids), _tensor_digest(self.action_logprobs),
        ))

    def rollover_from_final_current_slot(self) -> None:
        final_obs = self.obs[-1].detach().clone()
        final_available = self.available_actions[-1].detach().clone()
        final_dvm = self.decision_valid_masks[-1].detach().clone()
        final_active = self.active_masks[-1].detach().clone()
        self.obs.zero_(); self.available_actions.zero_()
        self.decision_valid_masks.zero_(); self.active_masks.zero_()
        self.action_ids.zero_(); self.action_logprobs.zero_()
        self.obs[0].copy_(final_obs)
        self.available_actions[0].copy_(final_available)
        self.decision_valid_masks[0].copy_(final_dvm)
        self.active_masks[0].copy_(final_active)
        self.next_action_slot = 0


class RolloverResourcesV1:
    def __init__(self, *, critic_buffer: object, terminal_collector: object, actor_storages: tuple[ControlledActorStorageV1, ...]) -> None:
        self.critic_buffer = critic_buffer
        self.terminal_collector = terminal_collector
        self.actor_storages = actor_storages

    @property
    def critic_rollover_digest(self) -> str:
        buffer = self.critic_buffer
        return E.canonical_digest_v1((
            buffer.step,
            _tensor_digest(buffer.share_obs), _tensor_digest(buffer.rnn_states_critic),
            _tensor_digest(buffer.masks), _tensor_digest(buffer.bad_masks),
            _tensor_digest(buffer.termination_reason),
            _tensor_digest(buffer.timeout_bootstrap_value_preds),
            _tensor_digest(buffer.timeout_bootstrap_masks),
            _tensor_digest(buffer._event_slot_written), bool(buffer._event_returns_computed),
        ))


@dataclass
class Context:
    components: Any
    authority: Any
    rollout_evidence: Any
    frozen_inputs: Any
    immutable_plan: Any
    actor_plan: Any
    critic_plan: Any
    actor_inputs: dict[int, Any]
    initial_factor: torch.Tensor
    critic_inputs: Any
    event_returns_result: torch.Tensor
    rollover_resources: RolloverResourcesV1


def _base_authority(
    *, update_id: str, critic_minibatches: int = 1,
    valuenorm_enabled: bool = True,
) -> Any:
    config = E.B2RResolvedConfigV1(
        resolved_T=T, resolved_E=ENVIRONMENTS, resolved_M=ACTORS, resolved_N=TASKS,
        actor_epoch_count=2, actor_minibatch_count=2,
        actor_partition_policy="reviewed_exact_coverage",
        critic_epoch_count=1, critic_minibatch_count=critic_minibatches,
        critic_partition_policy="reviewed_exact_coverage",
        fixed_order=False, valuenorm_enabled=valuenorm_enabled,
        ppo_happo_settings=(("clip_param", 0.2), ("entropy_coef", 0.01), ("max_grad_norm", 10.0), ("value_loss_coef", 1.0)),
    )
    repo_names = (
        "assignment_event_training_evidence.py", "assignment_event_training_plans.py",
        "assignment_event_training_control.py", "assignment_event_training_gradient_probe.py",
        "assignment_event_training_actor_mutation.py", "assignment_event_training_critic_mutation.py",
        "assignment_event_training_full_transaction.py", "assignment_event_critic_buffer.py",
    )
    repo_files = tuple(sorted((R1.SCAN_SOURCE / name for name in repo_names), key=lambda path: path.as_posix()))
    harl_root = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
    harl_files = tuple(sorted((
        harl_root / "algorithms" / "actors" / "happo.py",
        harl_root / "algorithms" / "critics" / "v_critic.py",
        harl_root / "common" / "valuenorm.py",
        harl_root / "common" / "buffers" / "on_policy_critic_buffer_ep.py",
    ), key=lambda path: path.as_posix()))
    return E.B2RUpdateAuthorityV1(
        update_id=update_id, slice_identity="B2-R1",
        repository_head="b71d85a32f51be6ada324f870813a56bb45dd396",
        dirty_state_classification="reviewed uncommitted B2-R0-R4 plus authorized private B2-R5",
        repo_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(R1.REPO_ROOT).as_posix(), _sha(path)) for path in repo_files),
        installed_harl_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(harl_root).as_posix(), _sha(path)) for path in harl_files),
        resolved_config=config,
        authorization_scope=("r1_contracts", "r2_unique_backward", "r3_actor_sequence", "r4_critic_valuenorm_sequence", "r5_private_full_transaction"),
        forbidden_operations=("isaac", "real_environment_rollout", "training_campaign", "evaluation_playback", "checkpoint_weight_io", "public_route_activation", "r6", "r7"),
    )


def make_context(
    *, update_id: str = "b2-r5-controlled-full-update-0001",
    critic_minibatches: int = 1,
    valuenorm_enabled: bool = True,
) -> Context:
    components = R3H.make_components()
    actor_inputs = R3H.make_actor_inputs(components)
    for actor in components.actors:
        actor.actor.eval()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    components.critic.critic.eval()
    components.critic.critic_optimizer.zero_grad(set_to_none=True)
    base = _base_authority(
        update_id=update_id,
        critic_minibatches=critic_minibatches,
        valuenorm_enabled=valuenorm_enabled,
    )
    order = R3.B2R3ActorOrderFreezerV1(base).freeze(rng_seed=ORDER_SEED)
    behavior_by_actor = tuple(
        (actor_id, _tensor_digest(actor_inputs[actor_id].behavior_old_logprobs))
        for actor_id in range(ACTORS)
    )
    actor_authority = R3.B2R3MutationAuthorityV1(
        base_authority=base, mutation_id=f"{update_id}-actor", slice_identity="B2-R3",
        order_evidence=order, behavior_digest_by_actor=behavior_by_actor,
        allowed_operations=("actor_zero_grad", "actor_backward", "actor_gradient_clip", "actor_optimizer_step", "actor_post_step_evaluation", "factor_attribution"),
        forbidden_operations=("critic_backward", "critic_optimizer_step", "critic_parameter_mutation", "live_valuenorm_update", "scheduler_step", "full_learner_update", "isaac", "training", "evaluation_playback", "checkpoint_weight_io", "public_route_activation"),
    )
    critic_authority = R4.B2R4MutationAuthorityV1(
        base_authority=base, mutation_id=f"{update_id}-critic", slice_identity="B2-R4",
        allowed_operations=("live_valuenorm_update", "critic_backward", "critic_gradient_clip", "critic_optimizer_step"),
        forbidden_operations=("actor_backward", "actor_optimizer_step", "actor_parameter_mutation", "scheduler_step", "full_learner_update", "isaac", "training", "evaluation_playback", "checkpoint_weight_io", "public_route_activation"),
    )
    authority = R5.B2R5FullUpdateAuthorityV1(
        base_authority=base, actor_authority=actor_authority,
        critic_authority=critic_authority, transaction_id=f"transaction-{update_id}",
        slice_identity="B2-R5",
        allowed_operations=("actor_sequence", "critic_sequence", "live_valuenorm_update", "training_mode_entry", "rollout_mode_restore", "critic_rollover", "terminal_ledger_reset", "actor_storage_rollover"),
        forbidden_operations=("isaac", "real_environment_rollout", "training_campaign", "evaluation_playback", "checkpoint_weight_io", "public_route_activation", "r6", "r7", "scheduler_redesign"),
    )

    initial_factor = torch.ones((T, ENVIRONMENTS, 1), dtype=torch.float32)
    partitions = P.build_exact_partitions_v1(B=B, epoch_count=2, minibatch_count=2, partition_policy="reviewed_exact_coverage")
    dvm = {
        actor_id: R3._canonical_true_row_indices_v1(actor_inputs[actor_id].decision_valid_mask)
        for actor_id in range(ACTORS)
    }
    active = {
        actor_id: R3._canonical_true_row_indices_v1(actor_inputs[actor_id].active_mask)
        for actor_id in range(ACTORS)
    }
    actor_plan = P.build_actor_update_plan_v1(
        authority=base, authority_config_digest=base.config_digest,
        actor_permutation=order.actor_order, approved_partitions_by_epoch=partitions,
        dvm_indices_by_actor=dvm, active_indices_by_actor=active,
        factor_input_digest=_tensor_digest(initial_factor), optimizer_step_policy="match_backward",
    )

    args = {
        "episode_length": T, "n_rollout_threads": ENVIRONMENTS,
        "hidden_sizes": [HIDDEN], "recurrent_n": 1, "gamma": 0.99,
        "gae_lambda": 0.95, "use_gae": True, "use_proper_time_limits": True,
    }
    buffer = CB.EventOnPolicyCriticBufferEPV2(args, Box((SHARED_DIM,)), device=DEVICE)
    shared_full = torch.arange((T + 1) * ENVIRONMENTS * SHARED_DIM, dtype=torch.float32).reshape(T + 1, ENVIRONMENTS, SHARED_DIM) / 90.0 - 0.7
    buffer.share_obs.copy_(shared_full)
    buffer.rnn_states_critic.zero_(); buffer.masks.fill_(1.0); buffer.bad_masks.fill_(1.0)
    flat_shared = buffer.share_obs[:-1].reshape(B, SHARED_DIM)
    flat_rnn = buffer.rnn_states_critic[:-1].reshape(B, 1, HIDDEN)
    flat_masks = buffer.masks[:-1].reshape(B, 1)
    with torch.no_grad():
        value_preds, _ = components.critic.get_values(flat_shared, flat_rnn, flat_masks)
    buffer.value_preds[:-1].copy_(value_preds.reshape(T, ENVIRONMENTS, 1))
    buffer.returns[:-1].copy_(torch.linspace(-1.5, 3.0, B, dtype=torch.float32).reshape(T, ENVIRONMENTS, 1))
    buffer.returns[-1].fill_(654.0)
    reason = torch.tensor([[0, 1, 2], [3, 0, 0]], dtype=torch.int64).reshape(T, ENVIRONMENTS, 1)
    buffer.termination_reason.copy_(reason)
    buffer.timeout_bootstrap_masks.copy_(reason == int(TRANSITION.TerminationReason.TIME_LIMIT))
    buffer.timeout_bootstrap_value_preds.zero_()
    buffer.timeout_bootstrap_value_preds[buffer.timeout_bootstrap_masks] = 2.75
    buffer._event_slot_written.fill_(True)
    buffer._event_returns_computed = True
    buffer.step = 0
    collector = CB.EventTerminalLearnerCollectorV2(critic_buffer=buffer)
    collector._consumed_terminal_keys.update({(0, 0, 10), (1, 0, 11), (2, 1, 12)})
    storages = tuple(ControlledActorStorageV1(actor_id=actor_id, inputs=actor_inputs[actor_id]) for actor_id in range(ACTORS))
    resources = RolloverResourcesV1(critic_buffer=buffer, terminal_collector=collector, actor_storages=storages)

    raw_target = buffer.returns[:-1].reshape(B, 1)
    critic_partitions = P.build_exact_partitions_v1(
        B=B,
        epoch_count=1,
        minibatch_count=critic_minibatches,
        partition_policy="reviewed_exact_coverage",
    )
    critic_plan = P.build_critic_update_plan_v1(
        authority=base, authority_config_digest=base.config_digest,
        approved_partitions_by_epoch=critic_partitions,
        raw_target_digest=_tensor_digest(raw_target), optimizer_step_policy="match_backward",
    )
    critic_inputs = R4.B2R4CriticInputsV1(
        flat_shared, flat_rnn, flat_masks, value_preds.detach().clone(), buffer.returns,
    )
    event_returns_result = buffer.returns[:-1].detach().clone().contiguous()
    combined_behavior = E.canonical_digest_v1(behavior_by_actor)
    selected_digest = _tensor_digest(buffer.termination_reason)
    timeout_digest = _tuple_tensor_digest(buffer.timeout_bootstrap_masks, buffer.timeout_bootstrap_value_preds)
    actor_obs_digest = E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].obs) for index in range(ACTORS)))
    availability_digest = E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].available_actions) for index in range(ACTORS)))
    proposal_digest = E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].actions) for index in range(ACTORS)))
    dvm_digest = E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].decision_valid_mask) for index in range(ACTORS)))
    active_digest = E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].active_mask) for index in range(ACTORS)))
    actor_evidence_rows = tuple(
        (
            base.update_id,
            actor_id,
            row // ENVIRONMENTS,
            row % ENVIRONMENTS,
            0,
            row + 1,
        )
        for actor_id in range(ACTORS)
        for row in R3._canonical_true_row_indices_v1(
            actor_inputs[actor_id].decision_valid_mask
            & actor_inputs[actor_id].active_mask
        )
    )
    actor_reconciliation = R5.reconcile_actor_evidence_v1(
        update_id=base.update_id,
        actor_ids=tuple(range(ACTORS)),
        expected_actor_rows=actor_evidence_rows,
        observed_actor_rows=actor_evidence_rows,
    )
    frozen = E.B2RFrozenTrainingInputsV1(
        update_id=base.update_id, authority_config_digest=base.config_digest,
        actor_canonical_identities=tuple((actor, t, env) for actor in range(ACTORS) for t in range(T) for env in range(ENVIRONMENTS)),
        historical_actor_observation_digest=actor_obs_digest,
        historical_available_action_mask_digest=availability_digest,
        original_proposal_action_digest=proposal_digest,
        original_behavior_logprob_digest=combined_behavior,
        dvm_digest=dvm_digest, active_mask_digest=active_digest,
        selected_reason_grid_digest=selected_digest,
        precedence_resolution_evidence_digest=R1.digest(f"{update_id}-precedence"),
        terminal_correlation_evidence_digest=R1.digest(f"{update_id}-terminal-correlation"),
        timeout_critic_evidence_digest=timeout_digest,
        event_return_result_digest=_tensor_digest(event_returns_result),
        critic_training_slice_digest=_tensor_digest(raw_target),
        final_structural_return_slot_digest=_tensor_digest(buffer.returns[-1]),
        baseline_value_digest=_tensor_digest(value_preds),
        advantage_digest=E.canonical_digest_v1(tuple(_tensor_digest(actor_inputs[index].advantages) for index in range(ACTORS))),
        termination_domain_valid=True, exactly_one_selected_category=True,
        return_equality_proof="exact controlled event result equals buffer returns[:-1]",
        return_no_alias_proof="controlled event result is a detached clone",
    )
    rollout = R5.B2R5RolloutCompleteEvidenceV1(
        update_id=base.update_id, authority_config_digest=base.config_digest,
        resolved_T=T, resolved_E=ENVIRONMENTS, resolved_M=ACTORS, resolved_N=TASKS,
        actor_storage_complete=(True, True, True), critic_transition_storage_complete=True,
        terminal_learner_evidence_complete=True,
        termination_reason_digest=selected_digest, timeout_sidecar_digest=timeout_digest,
        proposal_action_logprob_digest=E.canonical_digest_v1((proposal_digest, combined_behavior)),
        dvm_active_availability_digest=E.canonical_digest_v1((dvm_digest, active_digest, availability_digest)),
        actor_evidence_expected_rows=actor_reconciliation.expected_actor_rows,
        actor_evidence_observed_rows=actor_reconciliation.observed_actor_rows,
        actor_evidence_reconciliation_digest=actor_reconciliation.evidence_digest,
        current_final_slot_digest_by_actor=tuple((index, storage.final_current_slot_digest) for index, storage in enumerate(storages)),
        actor_buffer_cursors=(T, T, T), critic_buffer_cursor=buffer.step,
        expected_terminal_keys=collector.consumed_terminal_keys,
        terminal_consumption_keys=collector.consumed_terminal_keys,
        terminal_reconciliation_digest=R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=collector.consumed_terminal_keys,
            observed_terminal_keys=collector.consumed_terminal_keys,
        ).evidence_digest,
        terminal_evidence_is_historical_pre_reset=True,
        runtime_ack_is_separate_from_learner_consumption=True,
        final_value_evaluated=True, selected_termination_domain_valid=True,
        event_returns_compute_count=1,
    )
    immutable_plan = R5.B2R5ImmutableUpdatePlanV1(
        update_id=base.update_id, authority_config_digest=base.config_digest,
        actor_order=order.actor_order, actor_plan_digest=actor_plan.plan_digest,
        critic_plan_digest=critic_plan.plan_digest,
        actor_expected_backward=actor_plan.expected_backward_count_by_actor,
        actor_expected_step=actor_plan.expected_optimizer_step_count_by_actor,
        critic_expected_backward=critic_plan.expected_backward_count,
        critic_expected_step=critic_plan.expected_optimizer_step_count,
        valuenorm_expected_update=critic_plan.expected_valuenorm_update_count,
        lifecycle_evidence_digest=rollout.evidence_digest,
        returns_evidence_digest=E.canonical_digest_v1((_tensor_digest(event_returns_result), _tensor_digest(raw_target), _tensor_digest(buffer.returns[-1]))),
        initial_component_state_digest=R5._component_state_digest(components.actors, components.critic, components.live_value_normalizer),
        initial_factor_digest=_tensor_digest(initial_factor),
        expected_stage_progression=tuple(C.B2RUpdateStageV1),
    )
    return Context(
        components, authority, rollout, frozen, immutable_plan, actor_plan,
        critic_plan, actor_inputs, initial_factor, critic_inputs,
        event_returns_result, resources,
    )


def rebind_critic_targets(
    context: Context,
    *,
    training_returns: torch.Tensor,
    frozen_value_predictions: torch.Tensor,
) -> Context:
    """Rebind one controlled R5 event-return/critic-target identity exactly."""

    expected = (B, 1)
    if tuple(training_returns.shape) != expected or tuple(
        frozen_value_predictions.shape
    ) != expected:
        raise ValueError(
            f"controlled R5 rebind requires {expected}, got "
            f"{tuple(training_returns.shape)} and "
            f"{tuple(frozen_value_predictions.shape)}"
        )
    buffer = context.rollover_resources.critic_buffer
    buffer.returns[:-1].copy_(training_returns.reshape(T, ENVIRONMENTS, 1))
    event_returns_result = buffer.returns[:-1].detach().clone().contiguous()
    raw_target = buffer.returns[:-1].reshape(B, 1)
    target_digest = _tensor_digest(raw_target)
    critic_inputs = replace(
        context.critic_inputs,
        value_preds=frozen_value_predictions.detach().clone(),
        returns_storage=buffer.returns,
    )
    critic_plan = replace(context.critic_plan, raw_target_digest=target_digest)
    frozen_inputs = replace(
        context.frozen_inputs,
        event_return_result_digest=_tensor_digest(event_returns_result),
        critic_training_slice_digest=target_digest,
        baseline_value_digest=_tensor_digest(frozen_value_predictions),
    )
    immutable_plan = replace(
        context.immutable_plan,
        critic_plan_digest=critic_plan.plan_digest,
        returns_evidence_digest=E.canonical_digest_v1(
            (
                _tensor_digest(event_returns_result),
                target_digest,
                _tensor_digest(buffer.returns[-1]),
            )
        ),
    )
    return Context(
        context.components,
        context.authority,
        context.rollout_evidence,
        frozen_inputs,
        immutable_plan,
        context.actor_plan,
        critic_plan,
        context.actor_inputs,
        context.initial_factor,
        critic_inputs,
        event_returns_result,
        context.rollover_resources,
    )


def execute(context: Context, *, counter: Any, route_state: Any | None = None, synthetic_fault: str | None = None):
    state = R5.B2R5TransactionRouteStateV1() if route_state is None else route_state
    return R5.execute_full_learner_transaction_v1(
        authority=context.authority, rollout_evidence=context.rollout_evidence,
        frozen_inputs=context.frozen_inputs, immutable_plan=context.immutable_plan,
        actor_plan=context.actor_plan, critic_plan=context.critic_plan,
        actors=context.components.actors, critic=context.components.critic,
        live_value_normalizer=context.components.live_value_normalizer,
        actor_inputs=context.actor_inputs, initial_factor=context.initial_factor,
        critic_inputs=context.critic_inputs, event_returns_result=context.event_returns_result,
        rollover_resources=context.rollover_resources, route_state=state,
        counter=counter, synthetic_fault=synthetic_fault,
    )
