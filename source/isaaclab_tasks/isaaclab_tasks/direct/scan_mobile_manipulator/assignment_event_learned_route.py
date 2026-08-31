"""Dormant B2-I6 composition of the reviewed event-policy learner seams.

This module is deliberately private and is not registered with the public
wrapper or HARL runner.  It owns call ordering and fixed rollout transport;
all evidence, legality, proposal, lifecycle, terminal, and return semantics
remain owned by the reviewed I1--I5b components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

import torch

from .assignment_event_actor_collection import (
    EventPolicyActorSlotStorageV2,
    EventPolicyProposalEnvelope,
    collect_event_policy_proposals_v2,
    create_event_policy_actor_slot_storage_v2,
)
from .assignment_event_critic_buffer import (
    EventOnPolicyCriticBufferEPV2,
    EventTerminalLearnerCollectorV2,
)
from .assignment_event_happo_policy_math import train_event_policy_happo_sequence_v2
from .assignment_event_policy_decision import EventPolicyDecisionBundle
from .assignment_event_proposal_adapter import EventProposalDecisionSnapshot
from .assignment_event_runtime_facade import EventFacadeProposalStepResult
from .assignment_event_terminal_learner_transport import (
    EventRolloutCriticGuardV2,
    attach_event_terminal_infos_to_harl_step_v2,
    capture_event_learner_transition_expectation_v2,
    capture_event_rollout_critic_guard_v2,
)


EVENT_DORMANT_LEARNED_POLICY_ROUTE_V2 = "event_dormant_learned_policy_route_v2"
_PRIVATE_ROUTE_FACTORY_CAPABILITY = object()


class EventDormantLearnedPolicyRouteError(RuntimeError):
    """Typed fail-closed B2-I6 composition error."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.stage = stage
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"expected={expected!r}; actual={actual!r}"
        )


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    expected: object = None,
    actual: object = None,
) -> None:
    raise EventDormantLearnedPolicyRouteError(
        message,
        failure_code=failure_code,
        stage=stage,
        expected=expected,
        actual=actual,
    )


def _readonly(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


@dataclass(frozen=True, slots=True)
class EventDormantLearnedStepReceiptV2:
    """Bounded diagnostic receipt for one successfully inserted transition."""

    transition_slot: int
    decision_bundle: EventPolicyDecisionBundle = field(repr=False)
    proposal_envelope: EventPolicyProposalEnvelope = field(repr=False)
    facade_result: EventFacadeProposalStepResult = field(repr=False)
    next_decision_bundle: EventPolicyDecisionBundle = field(repr=False)
    harl_step_result: tuple[object, object, object, torch.Tensor, object, object] = field(
        repr=False
    )


@dataclass(frozen=True, slots=True)
class EventDormantLearnedRolloutResultV2:
    """Bounded result after event returns, injected trainers, and rollover."""

    advantages: torch.Tensor = field(repr=False)
    event_returns_result: object = field(repr=False)
    actor_train_result: object = field(repr=False)
    critic_train_result: object = field(repr=False)
    completed_actor_storages: tuple[EventPolicyActorSlotStorageV2, ...] = field(
        repr=False
    )


def _validate_bundle(bundle: object, *, stage: str) -> EventPolicyDecisionBundle:
    if type(bundle) is not EventPolicyDecisionBundle:
        _fail(
            "event learned route requires the exact reviewed I2 bundle",
            failure_code="decision_bundle_type",
            stage=stage,
            expected=EventPolicyDecisionBundle,
            actual=type(bundle),
        )
    bundle.validate_evidence_snapshot(bundle.evidence_snapshot)
    return bundle


def _validate_adapter_binding(
    *,
    bundle: EventPolicyDecisionBundle,
    decision: object,
) -> EventProposalDecisionSnapshot:
    if type(decision) is not EventProposalDecisionSnapshot:
        _fail(
            "I4-2 capture returned a noncanonical decision snapshot",
            failure_code="i42_decision_type",
            stage="proposal_source_binding",
            expected=EventProposalDecisionSnapshot,
            actual=type(decision),
        )
    binding = bundle.proposal_source_binding
    binding.validate_evidence_snapshot(bundle.evidence_snapshot)
    physical = bundle.evidence_snapshot.physical_evidence
    expected_available = (
        bundle.available_actions_bool[..., : bundle.evidence_identity.N]
        & bundle.policy_row_mask.expand(-1, -1, bundle.evidence_identity.N)
    ).contiguous()
    actual_available = decision.available_mask
    exact = (
        decision.proposal_source_publication_identity is binding.p2_publication_identity
        and decision.proposal_source_window_identity is binding.open_window_identity
        and decision.episode_generations == binding.episode_generations
        and decision.transition_generations == binding.transition_generations
        and torch.equal(decision.feasible_mask, physical.explicit_physical_feasibility)
        and torch.equal(decision.cost_matrix, physical.geometric_pair_ranking_cost)
        and actual_available is not None
        and torch.equal(actual_available, expected_available)
    )
    if not exact:
        _fail(
            "actual I4-2 decision is not the exact I1/I2 proposal source",
            failure_code="i42_proposal_source_mismatch",
            stage="proposal_source_binding",
            expected="same P2/window/generations and sealed physical/I2 masks",
            actual="binding mismatch",
        )
    return decision


def _validate_resolution_routing(
    *,
    bundle: EventPolicyDecisionBundle,
    envelope: EventPolicyProposalEnvelope,
    result: object,
) -> EventFacadeProposalStepResult:
    if type(result) is not EventFacadeProposalStepResult:
        _fail(
            "proposal route returned a noncanonical I4-2 facade result",
            failure_code="i42_step_result_type",
            stage="proposal_execution",
            expected=EventFacadeProposalStepResult,
            actual=type(result),
        )
    resolution = result.resolution
    raw = envelope.action_ids[..., 0]
    decoded = torch.where(
        raw == bundle.evidence_identity.N,
        torch.full_like(raw, -1),
        raw,
    )
    if not torch.equal(resolution.raw_action_ids, raw) or not torch.equal(
        resolution.decoded_proposal, decoded
    ):
        _fail(
            "I4-2 resolution did not preserve the fixed routed action tensor",
            failure_code="i42_action_binding",
            stage="proposal_execution",
            expected=(raw, decoded),
            actual=(resolution.raw_action_ids, resolution.decoded_proposal),
        )
    proposal_mask = envelope.policy_proposal_present_mask[..., 0]
    continuation = bundle.forced_continuation_mask[..., 0]
    forced_noop = bundle.forced_noop_mask[..., 0]
    for env_id, row in enumerate(resolution.interpretations):
        for robot_id, interpretation in enumerate(row):
            name = getattr(interpretation, "name", "")
            if continuation[env_id, robot_id] and name != "CONTINUE_EXISTING":
                _fail(
                    "forced continuation was not interpreted as no-reclaim continuation",
                    failure_code="forced_continuation_reinterpreted",
                    stage="proposal_execution",
                    expected="CONTINUE_EXISTING",
                    actual=name,
                )
            if forced_noop[env_id, robot_id] and name != "PROPOSAL_NO_CLAIM":
                _fail(
                    "forced noop was reinterpreted as a policy claim",
                    failure_code="forced_noop_reinterpreted",
                    stage="proposal_execution",
                    expected="PROPOSAL_NO_CLAIM",
                    actual=name,
                )
            if name in {
                "NEW_CLAIM_CANDIDATE",
                "NEW_CLAIM_SELECTED",
                "NEW_CLAIM_COMMITTED",
                "CONFLICT_LOSER",
            } and not bool(proposal_mask[env_id, robot_id].item()):
                _fail(
                    "a forced row entered proposal arbitration",
                    failure_code="forced_row_became_proposal",
                    stage="proposal_execution",
                    expected="candidate/conflict statuses only on policy-present rows",
                    actual=(env_id, robot_id, name),
                )
    return result


def _build_harl_step_result_v2(
    *,
    facade_result: EventFacadeProposalStepResult,
    next_bundle: EventPolicyDecisionBundle,
) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor, torch.Tensor, list[list[dict]], torch.Tensor]:
    """Adapt the raw DirectMARLEnv five-tuple to the existing HARL six slots."""

    raw = facade_result.environment_result
    if type(raw) is not tuple or len(raw) != 5:
        _fail(
            "event physical step did not return the DirectMARLEnv five-tuple",
            failure_code="environment_step_arity",
            stage="harl_six_tuple",
            expected="(obs,rewards,terminated,truncated,info)",
            actual=(type(raw), getattr(raw, "__len__", lambda: None)()),
        )
    _, reward_map, terminated_map, truncated_map, _ = raw
    names = tuple(next_bundle.evidence_snapshot.scale_contract["ordered_agent_names"])
    E = next_bundle.evidence_identity.num_envs
    M = next_bundle.evidence_identity.M
    if (
        len(names) != M
        or not isinstance(reward_map, Mapping)
        or not isinstance(terminated_map, Mapping)
        or not isinstance(truncated_map, Mapping)
        or any(name not in reward_map or name not in terminated_map or name not in truncated_map for name in names)
    ):
        _fail(
            "raw event result does not preserve fixed ordered agent mappings",
            failure_code="environment_agent_mapping",
            stage="harl_six_tuple",
            expected=names,
            actual=(type(reward_map), tuple(reward_map) if isinstance(reward_map, Mapping) else None),
        )
    rewards = torch.stack([reward_map[name] for name in names], dim=1).unsqueeze(-1)
    dones = torch.stack(
        [terminated_map[name].to(torch.bool) | truncated_map[name].to(torch.bool) for name in names],
        dim=1,
    )
    device = next_bundle.evidence_snapshot.actor_obs.device
    if (
        tuple(rewards.shape) != (E, M, 1)
        or rewards.dtype is not torch.float32
        or rewards.device != device
        or tuple(dones.shape) != (E, M)
        or dones.device != device
        or not torch.equal(dones, dones[:, :1].expand_as(dones))
    ):
        _fail(
            "adapted rewards/dones violate the fixed synchronized HARL contract",
            failure_code="harl_step_tensor_contract",
            stage="harl_six_tuple",
            expected=((E, M, 1), (E, M), device),
            actual=((rewards.shape, rewards.dtype, rewards.device), (dones.shape, dones.device)),
        )
    actor_obs = next_bundle.evidence_snapshot.actor_obs
    obs = {name: _readonly(actor_obs[:, agent_id]) for agent_id, name in enumerate(names)}
    infos = [[{} for _ in range(M)] for _ in range(E)]
    return (
        obs,
        next_bundle.evidence_snapshot.runner_share_obs,
        rewards.detach().clone().contiguous(),
        dones.detach().clone().contiguous(),
        infos,
        next_bundle.runner_available_actions,
    )


class EventDormantLearnedPolicyRouteV2:
    """Private fixed-M/N event rollout and learner composition authority."""

    def __init__(
        self,
        *,
        episode_length: int,
        actors: Sequence[object],
        critic: object,
        critic_buffer: EventOnPolicyCriticBufferEPV2,
        admitted_reset: Callable[[], object],
        current_decision_supplier: Callable[[], EventPolicyDecisionBundle],
        current_decision_validator: Callable[[EventPolicyDecisionBundle], None],
        capture_i42_decision: Callable[..., EventProposalDecisionSnapshot],
        step_i42_proposals: Callable[..., EventFacadeProposalStepResult],
        action_builder: Callable[[object, torch.Tensor], object] | None,
        actor_trainer: Callable[..., object],
        critic_trainer: Callable[[EventOnPolicyCriticBufferEPV2, object | None], object],
        value_normalizer: object | None,
        actor_rnn_shape: tuple[int, int],
        call_observer: Callable[[str, object | None], None] | None,
        factory_capability: object,
    ) -> None:
        if factory_capability is not _PRIVATE_ROUTE_FACTORY_CAPABILITY:
            _fail(
                "dormant event route requires its private composition factory",
                failure_code="private_factory_required",
                stage="route_construct",
                expected="_compose_dormant_event_learned_policy_route_v2",
                actual="direct constructor",
            )
        if type(episode_length) is not int or episode_length <= 0:
            _fail("invalid rollout length", failure_code="rollout_length", stage="route_construct", expected="positive int", actual=episode_length)
        if type(critic_buffer) is not EventOnPolicyCriticBufferEPV2:
            _fail("event route requires the I5a critic buffer", failure_code="critic_buffer_type", stage="route_construct", expected=EventOnPolicyCriticBufferEPV2, actual=type(critic_buffer))
        if critic_buffer.episode_length != episode_length:
            _fail("actor/critic rollout lengths differ", failure_code="rollout_length", stage="route_construct", expected=episode_length, actual=critic_buffer.episode_length)
        if type(actors) not in (tuple, list) or not actors or len({id(item) for item in actors}) != len(actors):
            _fail("event route requires distinct fixed-order actors", failure_code="actor_domain", stage="route_construct", expected="nonempty distinct tuple/list", actual=type(actors))
        if not callable(getattr(critic, "get_values", None)):
            _fail("critic lacks get_values", failure_code="critic_api", stage="route_construct", expected="callable get_values", actual=type(critic))
        if type(actor_rnn_shape) is not tuple or len(actor_rnn_shape) != 2 or any(type(item) is not int or item <= 0 for item in actor_rnn_shape):
            _fail("actor RNN placeholder shape is invalid", failure_code="actor_rnn_shape", stage="route_construct", expected="(R,H) positive ints", actual=actor_rnn_shape)
        callbacks = (admitted_reset, current_decision_supplier, current_decision_validator, capture_i42_decision, step_i42_proposals, actor_trainer, critic_trainer)
        if any(not callable(item) for item in callbacks):
            _fail("route composition callback is missing", failure_code="composition_callback", stage="route_construct", expected="all callbacks callable", actual=tuple(callable(item) for item in callbacks))
        self.schema_version = EVENT_DORMANT_LEARNED_POLICY_ROUTE_V2
        self.episode_length = episode_length
        self.actors = tuple(actors)
        self.critic = critic
        self.critic_buffer = critic_buffer
        self.collector = EventTerminalLearnerCollectorV2(critic_buffer=critic_buffer)
        self._admitted_reset = admitted_reset
        self._current_decision_supplier = current_decision_supplier
        self._current_decision_validator = current_decision_validator
        self._capture_i42_decision = capture_i42_decision
        self._step_i42_proposals = step_i42_proposals
        self._action_builder = action_builder
        self._actor_trainer = actor_trainer
        self._critic_trainer = critic_trainer
        self._value_normalizer = value_normalizer
        self._actor_rnn_shape = actor_rnn_shape
        self._observer = call_observer
        self._initialized = False
        self._poisoned = False
        self._physical_step_started = False
        self._current_bundle: EventPolicyDecisionBundle | None = None
        self._actor_storages: tuple[EventPolicyActorSlotStorageV2, ...] = ()
        self._actor_rnn_states: torch.Tensor | None = None
        self._actor_masks: torch.Tensor | None = None
        self._critic_guard: EventRolloutCriticGuardV2 | None = None

    def _observe(self, stage: str, detail: object | None = None) -> None:
        if self._observer is not None:
            self._observer(stage, detail)

    def _require_live(self, *, stage: str) -> None:
        if self._poisoned:
            _fail("event route is poisoned after an irreversible composition failure", failure_code="route_poisoned", stage=stage, expected="fresh route", actual="poisoned")

    @property
    def current_decision_bundle(self) -> EventPolicyDecisionBundle:
        if self._current_bundle is None:
            _fail("event route has not been reset", failure_code="route_not_initialized", stage="route_read", expected="reset", actual=None)
        return self._current_bundle

    @property
    def actor_storages(self) -> tuple[EventPolicyActorSlotStorageV2, ...]:
        return self._actor_storages

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    def reset(self) -> object:
        """Run admitted reset and initialize actor/critic slot zero only."""

        self._require_live(stage="route_reset")
        if self._initialized:
            _fail("route reset cannot discard an active rollout", failure_code="active_rollout_reset", stage="route_reset", expected="new route", actual=self.critic_buffer.step)
        if self.critic_buffer.step != 0 or bool(self.critic_buffer._event_slot_written.any().item()):
            _fail("critic buffer is not fresh at reset", failure_code="critic_buffer_not_fresh", stage="route_reset", expected=(0, "no event slots"), actual=(self.critic_buffer.step, self.critic_buffer._event_slot_written))
        reset_result = self._admitted_reset()
        self._observe("reset_admitted", None)
        bundle = _validate_bundle(self._current_decision_supplier(), stage="reset_current_bundle")
        self._observe("I1_I2_current", bundle)
        E, M = bundle.evidence_identity.num_envs, bundle.evidence_identity.M
        if M != len(self.actors) or E != self.critic_buffer.n_rollout_threads:
            _fail("reset decision and rollout domains differ", failure_code="rollout_domain", stage="route_reset", expected=(self.critic_buffer.n_rollout_threads, len(self.actors)), actual=(E, M))
        share = bundle.evidence_snapshot.runner_share_obs
        if tuple(share[:, 0].shape) != tuple(self.critic_buffer.share_obs[0].shape):
            _fail("I1 critic projection and buffer spaces differ", failure_code="critic_share_obs_shape", stage="route_reset", expected=tuple(self.critic_buffer.share_obs[0].shape), actual=tuple(share[:, 0].shape))
        active = torch.ones((E, 1), dtype=torch.float32, device=share.device)
        storages = tuple(
            create_event_policy_actor_slot_storage_v2(
                episode_length=self.episode_length,
                agent_id=agent_id,
                current_decision_bundle=bundle,
                initial_active_masks=active,
            )
            for agent_id in range(M)
        )
        R, H = self._actor_rnn_shape
        self._actor_rnn_states = torch.zeros((self.episode_length + 1, E, M, R, H), dtype=torch.float32, device=share.device)
        self._actor_masks = torch.ones((self.episode_length + 1, E, M, 1), dtype=torch.float32, device=share.device)
        self.critic_buffer.share_obs[0].copy_(share[:, 0])
        self.critic_buffer.rnn_states_critic[0].zero_()
        self.critic_buffer.masks[0].fill_(1.0)
        self._actor_storages = storages
        self._current_bundle = bundle
        self._critic_guard = capture_event_rollout_critic_guard_v2(self.critic)
        self._initialized = True
        self._observe("slot0_initialized", None)
        return reset_result

    def _prevalidate_actor_commit(
        self,
        *,
        slot: int,
        envelope: EventPolicyProposalEnvelope,
        next_bundle: EventPolicyDecisionBundle,
        next_active: torch.Tensor,
    ) -> None:
        for storage in self._actor_storages:
            if storage.next_action_slot != slot or storage.decision_bundle_refs[slot] is not self.current_decision_bundle:
                _fail("actor storage slot is not bound to current I2", failure_code="actor_storage_alignment", stage="transition_precommit", expected=(slot, id(self.current_decision_bundle)), actual=(storage.next_action_slot, id(storage.decision_bundle_refs[slot])))
            envelope.validate_decision_bundle(storage.decision_bundle_refs[slot])
            if next_bundle.evidence_identity.num_envs != storage.E or next_bundle.evidence_identity.M != storage.M or next_bundle.evidence_identity.N != storage.N or next_bundle.evidence_snapshot.actor_obs.shape[-1] != storage.obs_dim:
                _fail("next I2 differs from actor storage fixed domain", failure_code="actor_storage_domain", stage="transition_precommit", expected=(storage.E, storage.M, storage.N, storage.obs_dim), actual=(next_bundle.evidence_identity.num_envs, next_bundle.evidence_identity.M, next_bundle.evidence_identity.N, next_bundle.evidence_snapshot.actor_obs.shape[-1]))
        if tuple(next_active.shape) != (self.critic_buffer.n_rollout_threads, 1):
            _fail("next active mask shape mismatch", failure_code="active_mask_shape", stage="transition_precommit", expected=(self.critic_buffer.n_rollout_threads, 1), actual=tuple(next_active.shape))

    def collect_step(self) -> EventDormantLearnedStepReceiptV2:
        """Collect one exact transition and commit its actor/critic slots."""

        self._require_live(stage="collect_step")
        if not self._initialized:
            _fail("collect requires reset", failure_code="route_not_initialized", stage="collect_step", expected="reset", actual=None)
        slot = self.critic_buffer.step
        if slot >= self.episode_length:
            _fail("rollout is already complete", failure_code="rollout_complete", stage="collect_step", expected=f"slot < {self.episode_length}", actual=slot)
        bundle = self.current_decision_bundle
        try:
            self._current_decision_validator(bundle)
            self._observe("current_binding_validated", bundle)
            expectation = capture_event_learner_transition_expectation_v2(bundle)
            self._observe("learner_expectation", expectation)
            assert self._actor_rnn_states is not None and self._actor_masks is not None
            assert self._critic_guard is not None
            with torch.inference_mode():
                critic_result = self.critic.get_values(
                    self.critic_buffer.share_obs[slot],
                    self.critic_buffer.rnn_states_critic[slot],
                    self.critic_buffer.masks[slot],
                )
            if type(critic_result) is not tuple or len(critic_result) != 2:
                _fail("rollout critic returned an invalid tuple", failure_code="critic_output", stage="critic_current", expected="(values,rnn)", actual=type(critic_result))
            values, next_critic_rnn = critic_result
            E = bundle.evidence_identity.num_envs
            if type(values) is not torch.Tensor or tuple(values.shape) != (E, 1) or values.dtype is not torch.float32 or values.device != bundle.evidence_snapshot.actor_obs.device or values.requires_grad or not bool(torch.isfinite(values).all().item()):
                _fail("current critic value contract failed", failure_code="critic_value", stage="critic_current", expected=(E, 1, torch.float32), actual=(getattr(values, "shape", None), getattr(values, "dtype", None)))
            envelope = collect_event_policy_proposals_v2(
                decision_bundle=bundle,
                actors=self.actors,
                rnn_states=self._actor_rnn_states[slot],
                masks=self._actor_masks[slot],
            )
            self._observe("I3a_actor_collection", envelope)
            physical = bundle.evidence_snapshot.physical_evidence
            decision = self._capture_i42_decision(
                feasible_mask=physical.explicit_physical_feasibility,
                cost_matrix=physical.geometric_pair_ranking_cost,
                available_mask=(
                    bundle.available_actions_bool[..., : bundle.evidence_identity.N]
                    & bundle.policy_row_mask.expand(-1, -1, bundle.evidence_identity.N)
                ).contiguous(),
            )
            decision = _validate_adapter_binding(bundle=bundle, decision=decision)
            self._observe("I42_proposal_adapter", decision)
            self._physical_step_started = True
            facade_result = self._step_i42_proposals(
                envelope.runner_actions,
                decision=decision,
                layout="env_agent_action",
                action_builder=self._action_builder,
            )
            facade_result = _validate_resolution_routing(bundle=bundle, envelope=envelope, result=facade_result)
            self._observe("runtime_proposal_effective_step", facade_result)
            next_bundle = _validate_bundle(self._current_decision_supplier(), stage="next_current_bundle")
            current = facade_result.current_publication
            next_identity = next_bundle.evidence_identity
            actual_episode = tuple(int(item) for item in current.episode_generation.detach().cpu().tolist())
            actual_transition = tuple(int(item) for item in current.transition_generation.detach().cpu().tolist())
            if next_identity.p2_publication_identity is not current.publication_identity or next_identity.episode_generations != actual_episode or next_identity.transition_generations != actual_transition:
                _fail("next I1/I2 is not the returned current P2", failure_code="next_current_binding", stage="next_current_bundle", expected=(id(current.publication_identity), actual_episode, actual_transition), actual=(id(next_identity.p2_publication_identity), next_identity.episode_generations, next_identity.transition_generations))
            self._observe("next_I1_I2_current", next_bundle)
            base_step = _build_harl_step_result_v2(facade_result=facade_result, next_bundle=next_bundle)
            harl_step = attach_event_terminal_infos_to_harl_step_v2(harl_step_result=base_step, facade_result=facade_result, expectation=expectation)
            self._observe("I5a_terminal_infos", harl_step[4])
            dones = harl_step[3]
            done_env = dones[:, 0]
            staged_actor_rnn = envelope.next_rnn_states
            staged_actor_rnn[done_env] = 0.0
            staged_actor_masks = (~done_env).to(torch.float32).view(E, 1, 1).expand(E, len(self.actors), 1).contiguous()
            next_active = torch.ones((E, 1), dtype=torch.float32, device=dones.device)
            self._prevalidate_actor_commit(slot=slot, envelope=envelope, next_bundle=next_bundle, next_active=next_active)
            event_batch = self.collector.consume_before_optimizer_update(
                transition_slot=slot,
                expectation=expectation,
                harl_step_result=harl_step,
                value_preds=values.detach().clone().contiguous(),
                rnn_states_critic_after_current=next_critic_rnn.detach().clone().contiguous(),
                critic=self.critic,
                rollout_critic_guard=self._critic_guard,
            )
            self._observe("I5a_critic_buffer_insert", event_batch)
            for storage in self._actor_storages:
                storage.insert_transition(slot=slot, proposal_envelope=envelope, next_decision_bundle=next_bundle, next_active_masks=next_active)
            self._actor_rnn_states[slot + 1].copy_(staged_actor_rnn)
            self._actor_masks[slot + 1].copy_(staged_actor_masks)
            self._current_bundle = next_bundle
            self._physical_step_started = False
            self._observe("actor_slot_insert", slot)
            return EventDormantLearnedStepReceiptV2(slot, bundle, envelope, facade_result, next_bundle, harl_step)
        except Exception:
            if self._physical_step_started:
                self._poisoned = True
            raise

    def finish_rollout(
        self,
        *,
        agent_order: Sequence[int] | None = None,
        minibatch_permutations_by_agent: Mapping[int, Sequence[torch.Tensor]] | None = None,
    ) -> EventDormantLearnedRolloutResultV2:
        """Compute event returns, invoke injected trainers, then roll slot zero."""

        self._require_live(stage="finish_rollout")
        complete = (
            self._initialized
            and bool(self.critic_buffer._event_slot_written.all().item())
            and all(storage.next_action_slot == self.episode_length for storage in self._actor_storages)
        )
        if not complete:
            _fail(
                "event rollout is incomplete",
                failure_code="rollout_incomplete",
                stage="finish_rollout",
                expected=(self.episode_length, "all event slots written"),
                actual=(
                    tuple(storage.next_action_slot for storage in self._actor_storages),
                    self.critic_buffer._event_slot_written,
                ),
            )
        assert self._actor_rnn_states is not None and self._actor_masks is not None
        try:
            with torch.inference_mode():
                final_result = self.critic.get_values(
                    self.critic_buffer.share_obs[-1],
                    self.critic_buffer.rnn_states_critic[-1],
                    self.critic_buffer.masks[-1],
                )
            if type(final_result) is not tuple or len(final_result) != 2:
                _fail("ordinary final critic returned an invalid tuple", failure_code="critic_output", stage="final_next_value", expected="(values,rnn)", actual=type(final_result))
            next_value = final_result[0]
            E = self.critic_buffer.n_rollout_threads
            if type(next_value) is not torch.Tensor or tuple(next_value.shape) != (E, 1) or next_value.dtype is not torch.float32 or next_value.requires_grad or not bool(torch.isfinite(next_value).all().item()):
                _fail("ordinary final next value contract failed", failure_code="critic_value", stage="final_next_value", expected=(E, 1, torch.float32, False), actual=(getattr(next_value, "shape", None), getattr(next_value, "dtype", None), getattr(next_value, "requires_grad", None)))
            self._observe("ordinary_final_next_value", next_value)
            event_returns = self.critic_buffer.compute_event_returns(next_value.detach().clone().contiguous(), self._value_normalizer)
            self._observe("I5b_compute_event_returns", event_returns)
            if self._value_normalizer is None:
                value_baseline = self.critic_buffer.value_preds[:-1]
            else:
                with torch.inference_mode():
                    value_baseline = self._value_normalizer.denormalize(self.critic_buffer.value_preds[:-1])
            advantages = (self.critic_buffer.returns[:-1] - value_baseline).detach().clone().contiguous()
            if tuple(advantages.shape) != (self.episode_length, E, 1) or not bool(torch.isfinite(advantages).all().item()):
                _fail("stock-compatible event advantages are invalid", failure_code="advantage_contract", stage="advantage_derivation", expected=(self.episode_length, E, 1), actual=advantages)
            self._observe("event_advantages", advantages)
            order = tuple(range(len(self.actors))) if agent_order is None else tuple(agent_order)
            initial_factor = torch.ones((self.episode_length, E, 1), dtype=torch.float32, device=advantages.device)
            rnn_by_agent = tuple(self._actor_rnn_states[:, :, agent_id].detach().clone().contiguous() for agent_id in range(len(self.actors)))
            masks_by_agent = tuple(self._actor_masks[:, :, agent_id].detach().clone().contiguous() for agent_id in range(len(self.actors)))
            completed_storages = self._actor_storages
            actor_result = self._actor_trainer(
                actors=self.actors,
                actor_storages=completed_storages,
                rnn_states_by_agent=rnn_by_agent,
                masks_by_agent=masks_by_agent,
                advantages=advantages.clone(),
                initial_factor=initial_factor,
                agent_order=order,
                minibatch_permutations_by_agent=minibatch_permutations_by_agent,
            )
            self._observe("I3b_actor_train", actor_result)
            critic_result = self._critic_trainer(self.critic_buffer, self._value_normalizer)
            self._observe("critic_train", critic_result)
            final_bundle = self.current_decision_bundle
            final_actor_rnn = self._actor_rnn_states[-1].detach().clone().contiguous()
            final_actor_masks = self._actor_masks[-1].detach().clone().contiguous()
            final_active = tuple(storage.active_masks[-1].detach().clone().contiguous() for storage in completed_storages)
            self.critic_buffer.after_update()
            self._observe("critic_after_update", None)
            self.collector.reset_consumption_ledger_after_buffer_update()
            self._observe("terminal_ledger_reset", None)
            new_storages = tuple(
                create_event_policy_actor_slot_storage_v2(
                    episode_length=self.episode_length,
                    agent_id=agent_id,
                    current_decision_bundle=final_bundle,
                    initial_active_masks=final_active[agent_id],
                )
                for agent_id in range(len(self.actors))
            )
            self._actor_rnn_states.zero_()
            self._actor_rnn_states[0].copy_(final_actor_rnn)
            self._actor_masks.fill_(1.0)
            self._actor_masks[0].copy_(final_actor_masks)
            self._actor_storages = new_storages
            self._critic_guard = capture_event_rollout_critic_guard_v2(self.critic)
            self._observe("rollout_slot0_rebuilt", final_bundle)
            return EventDormantLearnedRolloutResultV2(
                advantages=_readonly(advantages),
                event_returns_result=event_returns,
                actor_train_result=actor_result,
                critic_train_result=critic_result,
                completed_actor_storages=completed_storages,
            )
        except Exception:
            self._poisoned = True
            raise


def _compose_dormant_event_learned_policy_route_v2(
    *,
    episode_length: int,
    actors: Sequence[object],
    critic: object,
    critic_buffer: EventOnPolicyCriticBufferEPV2,
    admitted_reset: Callable[[], object],
    current_decision_supplier: Callable[[], EventPolicyDecisionBundle],
    current_decision_validator: Callable[[EventPolicyDecisionBundle], None],
    capture_i42_decision: Callable[..., EventProposalDecisionSnapshot],
    step_i42_proposals: Callable[..., EventFacadeProposalStepResult],
    critic_trainer: Callable[[EventOnPolicyCriticBufferEPV2, object | None], object],
    actor_rnn_shape: tuple[int, int],
    action_builder: Callable[[object, torch.Tensor], object] | None = None,
    actor_trainer: Callable[..., object] = train_event_policy_happo_sequence_v2,
    value_normalizer: object | None = None,
    call_observer: Callable[[str, object | None], None] | None = None,
) -> EventDormantLearnedPolicyRouteV2:
    """Private/test-only B2-I6 factory; no public readiness bypass exists."""

    return EventDormantLearnedPolicyRouteV2(
        episode_length=episode_length,
        actors=actors,
        critic=critic,
        critic_buffer=critic_buffer,
        admitted_reset=admitted_reset,
        current_decision_supplier=current_decision_supplier,
        current_decision_validator=current_decision_validator,
        capture_i42_decision=capture_i42_decision,
        step_i42_proposals=step_i42_proposals,
        action_builder=action_builder,
        actor_trainer=actor_trainer,
        critic_trainer=critic_trainer,
        value_normalizer=value_normalizer,
        actor_rnn_shape=actor_rnn_shape,
        call_observer=call_observer,
        factory_capability=_PRIVATE_ROUTE_FACTORY_CAPABILITY,
    )


def get_dormant_event_learned_policy_route_descriptor_v2() -> Mapping[str, object]:
    """Describe the composition without opening the public event route."""

    return MappingProxyType(
        {
            "schema_version": EVENT_DORMANT_LEARNED_POLICY_ROUTE_V2,
            "profile": "event_gated_local_mrta_only",
            "route": "private_test_only_dormant",
            "public_activation": "blocked_pending_B2_V1_V2_R",
            "stock_full_row_actor_sampling": False,
            "stock_compute_returns": False,
            "stock_happo_train": False,
            "installed_harl_modified": False,
            "fixed_cardinality_only": True,
        }
    )


__all__: tuple[str, ...] = ()
