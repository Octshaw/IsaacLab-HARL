"""Repo-local B2-I5a/I5b EP critic-buffer and learner seams."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_CRITIC_BUFFER_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_CRITIC_BUFFER_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event critic buffer must execute under "
        f"its canonical module key; expected={CANONICAL_ASSIGNMENT_EVENT_CRITIC_BUFFER_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, field

import torch
from harl.common.buffers.on_policy_critic_buffer_ep import OnPolicyCriticBufferEP

from .assignment_event_gae_returns import (
    EventGAEReturnComputationV2,
    compute_event_gae_returns_v2,
)
from .assignment_event_terminal_learner_transport import (
    EventLearnerTransitionExpectationV2,
    EventRolloutCriticGuardV2,
    EventTerminalCriticEvaluationBatchV2,
    _make_timeout_critic_input_batch_v2,
    correlate_event_terminal_infos_v2,
    evaluate_event_timeout_bootstrap_values_v2,
)
from .assignment_lifecycle_transition_contract import TerminationReason


EVENT_CRITIC_BUFFER_FIELDS_V2 = "event_critic_buffer_fields_v2"
EVENT_TERMINAL_LEARNER_COLLECTOR_V2 = "event_terminal_learner_collector_v2"


class EventCriticBufferError(RuntimeError):
    """Fail-closed transition-slot or exactly-once collector error."""

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
    raise EventCriticBufferError(
        message,
        failure_code=failure_code,
        stage=stage,
        expected=expected,
        actual=actual,
    )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _PreparedEventFieldsV2:
    slot: int
    reason: torch.Tensor = field(repr=False)
    values: torch.Tensor = field(repr=False)
    masks: torch.Tensor = field(repr=False)


class EventOnPolicyCriticBufferEPV2(OnPolicyCriticBufferEP):
    """Installed EP storage plus explicit I5a fields and I5b event returns."""

    schema_version = EVENT_CRITIC_BUFFER_FIELDS_V2

    def __init__(self, args, share_obs_space, device="cuda:0") -> None:
        super().__init__(args, share_obs_space, device=device)
        shape = (self.episode_length, self.n_rollout_threads, 1)
        self.termination_reason = torch.full(
            shape,
            int(TerminationReason.NONE),
            dtype=torch.int64,
            device=self.device,
        )
        self.timeout_bootstrap_value_preds = torch.zeros(
            shape, dtype=torch.float32, device=self.device
        )
        self.timeout_bootstrap_masks = torch.zeros(
            shape, dtype=torch.bool, device=self.device
        )
        self._event_slot_written = torch.zeros(
            (self.episode_length,), dtype=torch.bool, device=self.device
        )
        self._event_returns_computed = False

    def insert(self, *args, **kwargs) -> None:
        """Reject stock insertion that would silently omit I5a terminal fields."""

        _fail(
            "event EP critic buffer requires insert_event with exact I5a fields",
            failure_code="event_fields_required",
            stage="event_buffer_insert",
            expected="insert_event(..., transition_slot=t, event_batch=...)",
            actual="stock insert",
        )

    def validate_event_slot_available(self, transition_slot: int) -> None:
        if type(transition_slot) is not int or not 0 <= transition_slot < self.episode_length:
            _fail(
                "event critic transition slot is outside the rollout",
                failure_code="event_slot_range",
                stage="event_buffer_prepare",
                expected=f"0 <= slot < {self.episode_length}",
                actual=transition_slot,
            )
        if transition_slot != self.step:
            _fail(
                "terminal fields must be inserted at the current transition slot t",
                failure_code="event_slot_shift",
                stage="event_buffer_prepare",
                expected=self.step,
                actual=transition_slot,
            )
        if bool(self._event_slot_written[transition_slot].item()):
            _fail(
                "event critic transition slot was already written",
                failure_code="event_slot_duplicate",
                stage="event_buffer_prepare",
                expected="unwritten slot",
                actual=transition_slot,
            )

    def _prepare_event_fields(
        self,
        *,
        transition_slot: int,
        event_batch: EventTerminalCriticEvaluationBatchV2,
    ) -> _PreparedEventFieldsV2:
        self.validate_event_slot_available(transition_slot)
        if type(event_batch) is not EventTerminalCriticEvaluationBatchV2:
            _fail(
                "event buffer requires one exact evaluated terminal batch",
                failure_code="event_batch_type",
                stage="event_buffer_prepare",
                expected=EventTerminalCriticEvaluationBatchV2,
                actual=type(event_batch),
            )
        expected_shape = (self.n_rollout_threads, 1)
        reason = event_batch.termination_reason
        values = event_batch.timeout_bootstrap_value_preds
        masks = event_batch.timeout_bootstrap_masks
        if (
            tuple(reason.shape) != expected_shape
            or reason.dtype is not torch.int64
            or reason.device != torch.device(self.device)
            or reason.requires_grad
            or tuple(values.shape) != expected_shape
            or values.dtype is not torch.float32
            or values.device != torch.device(self.device)
            or values.requires_grad
            or tuple(masks.shape) != expected_shape
            or masks.dtype is not torch.bool
            or masks.device != torch.device(self.device)
            or masks.requires_grad
        ):
            _fail(
                "event critic fields violate fixed [E,1] dtype/device contracts",
                failure_code="event_field_contract",
                stage="event_buffer_prepare",
                expected=(expected_shape, torch.device(self.device)),
                actual=((reason.shape, reason.dtype, reason.device), (values.shape, values.dtype, values.device), (masks.shape, masks.dtype, masks.device)),
            )
        valid_reasons = torch.tensor(
            [int(item) for item in TerminationReason], dtype=torch.int64, device=reason.device
        )
        if not bool((reason.unsqueeze(-1) == valid_reasons).any(dim=-1).all().item()):
            _fail(
                "event critic reason contains an unknown enum value",
                failure_code="event_reason_value",
                stage="event_buffer_prepare",
                expected=tuple(int(item) for item in TerminationReason),
                actual=reason,
            )
        expected_masks = reason == int(TerminationReason.TIME_LIMIT)
        if not torch.equal(masks, expected_masks):
            _fail(
                "timeout mask is not the exact TIME_LIMIT reason predicate",
                failure_code="event_timeout_mask",
                stage="event_buffer_prepare",
                expected=expected_masks,
                actual=masks,
            )
        if not bool(torch.isfinite(values).all().item()):
            _fail(
                "event timeout values must be finite",
                failure_code="event_timeout_nonfinite",
                stage="event_buffer_prepare",
                expected="finite",
                actual=values,
            )
        if not torch.equal(values[~masks], torch.zeros_like(values[~masks])):
            _fail(
                "invalid timeout value slots must use the deterministic zero sentinel",
                failure_code="event_timeout_sentinel",
                stage="event_buffer_prepare",
                expected=0.0,
                actual=values[~masks],
            )
        instance = object.__new__(_PreparedEventFieldsV2)
        object.__setattr__(instance, "slot", transition_slot)
        object.__setattr__(instance, "reason", reason.detach().clone().contiguous())
        object.__setattr__(instance, "values", values.detach().clone().contiguous())
        object.__setattr__(instance, "masks", masks.detach().clone().contiguous())
        return instance

    def insert_event(
        self,
        share_obs,
        rnn_states_critic,
        value_preds,
        rewards,
        masks,
        bad_masks,
        *,
        transition_slot: int,
        event_batch: EventTerminalCriticEvaluationBatchV2,
    ) -> None:
        """Insert current state at t+1 and terminal fields at exact slot t."""

        prepared = self._prepare_event_fields(
            transition_slot=transition_slot,
            event_batch=event_batch,
        )
        super().insert(
            share_obs,
            rnn_states_critic,
            value_preds,
            rewards,
            masks,
            bad_masks,
        )
        slot = prepared.slot
        self.termination_reason[slot].copy_(prepared.reason)
        self.timeout_bootstrap_value_preds[slot].copy_(prepared.values)
        self.timeout_bootstrap_masks[slot].copy_(prepared.masks)
        self._event_slot_written[slot] = True

    def compute_event_returns(
        self,
        next_value: torch.Tensor,
        value_normalizer=None,
    ) -> EventGAEReturnComputationV2:
        """Compute B2-I5b returns once from the completed I5a rollout fields."""

        if not self.use_gae:
            _fail(
                "B2-I5b is an event GAE contract and requires use_gae",
                failure_code="event_gae_required",
                stage="event_buffer_returns",
                expected=True,
                actual=self.use_gae,
            )
        if self._event_returns_computed:
            _fail(
                "event returns were already computed for this rollout",
                failure_code="event_returns_duplicate",
                stage="event_buffer_returns",
                expected="one successful computation per rollout",
                actual="already computed",
            )
        if not bool(self._event_slot_written.all().item()):
            _fail(
                "event returns require every transition slot to contain I5a fields",
                failure_code="event_rollout_incomplete",
                stage="event_buffer_returns",
                expected="all event transition slots written",
                actual=self._event_slot_written,
            )
        result = compute_event_gae_returns_v2(
            rewards=self.rewards,
            value_preds=self.value_preds,
            next_value=next_value,
            masks=self.masks,
            termination_reason=self.termination_reason,
            timeout_bootstrap_masks=self.timeout_bootstrap_masks,
            timeout_bootstrap_value_preds=self.timeout_bootstrap_value_preds,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
            value_normalizer=value_normalizer,
        )
        self.value_preds[-1].copy_(next_value.detach())
        self.returns[:-1].copy_(result.returns)
        self._event_returns_computed = True
        return result

    def after_update(self) -> None:
        super().after_update()
        self.termination_reason.fill_(int(TerminationReason.NONE))
        self.timeout_bootstrap_value_preds.zero_()
        self.timeout_bootstrap_masks.zero_()
        self._event_slot_written.zero_()
        self._event_returns_computed = False


class EventTerminalLearnerCollectorV2:
    """Dormant/private exact-info -> critic -> buffer collection seam."""

    schema_version = EVENT_TERMINAL_LEARNER_COLLECTOR_V2

    def __init__(self, *, critic_buffer: EventOnPolicyCriticBufferEPV2) -> None:
        if type(critic_buffer) is not EventOnPolicyCriticBufferEPV2:
            _fail(
                "event collector requires the repo-local EP critic buffer",
                failure_code="collector_buffer_type",
                stage="collector_create",
                expected=EventOnPolicyCriticBufferEPV2,
                actual=type(critic_buffer),
            )
        self.critic_buffer = critic_buffer
        self._consumed_terminal_keys: set[tuple[int, int, int]] = set()
        self._poisoned = False

    @property
    def consumed_terminal_keys(self) -> tuple[tuple[int, int, int], ...]:
        return tuple(sorted(self._consumed_terminal_keys))

    def reset_consumption_ledger_after_buffer_update(self) -> None:
        """Bound the exactly-once ledger to one completed rollout buffer."""

        if self._poisoned:
            _fail(
                "a poisoned terminal collector cannot be reused",
                failure_code="collector_poisoned",
                stage="collector_ledger_reset",
                expected="discard collector",
                actual="poisoned",
            )
        if self.critic_buffer.step != 0 or bool(self.critic_buffer._event_slot_written.any().item()):
            _fail(
                "terminal consumption ledger can clear only after buffer after_update",
                failure_code="collector_ledger_lifetime",
                stage="collector_ledger_reset",
                expected=(0, "all event slots cleared"),
                actual=(self.critic_buffer.step, self.critic_buffer._event_slot_written),
            )
        self._consumed_terminal_keys.clear()

    def consume_before_optimizer_update(
        self,
        *,
        transition_slot: int,
        expectation: EventLearnerTransitionExpectationV2,
        harl_step_result: tuple[object, torch.Tensor, torch.Tensor, torch.Tensor, object, object],
        value_preds: torch.Tensor,
        rnn_states_critic_after_current: torch.Tensor,
        critic: object,
        rollout_critic_guard: EventRolloutCriticGuardV2,
    ) -> EventTerminalCriticEvaluationBatchV2:
        if self._poisoned:
            _fail(
                "event terminal collector is poisoned after a failed consumption",
                failure_code="collector_poisoned",
                stage="collector_consume",
                expected="fresh collector",
                actual="poisoned",
            )
        self.critic_buffer.validate_event_slot_available(transition_slot)
        if type(harl_step_result) is not tuple or len(harl_step_result) != 6:
            _fail(
                "collector requires the preserved six-element HARL step result",
                failure_code="collector_harl_arity",
                stage="collector_consume",
                expected="six-tuple",
                actual=type(harl_step_result),
            )
        share_obs, rewards, dones, infos = (
            harl_step_result[1],
            harl_step_result[2],
            harl_step_result[3],
            harl_step_result[4],
        )
        E = self.critic_buffer.n_rollout_threads
        if (
            type(share_obs) is not torch.Tensor
            or share_obs.ndim != 3
            or share_obs.shape[0] != E
            or share_obs.shape[1] <= 0
            or tuple(share_obs.shape[2:]) != tuple(self.critic_buffer.share_obs.shape[2:])
            or share_obs.dtype is not torch.float32
            or share_obs.device != torch.device(self.critic_buffer.device)
            or share_obs.requires_grad
            or not bool(torch.isfinite(share_obs).all().item())
        ):
            _fail(
                "current post-reset HARL share_obs has an invalid [E,M,S] contract",
                failure_code="collector_share_obs_contract",
                stage="collector_consume",
                expected=(E, "M>0", "S", torch.float32, torch.device(self.critic_buffer.device)),
                actual=(getattr(share_obs, "shape", None), getattr(share_obs, "dtype", None), getattr(share_obs, "device", None)),
            )
        M = int(share_obs.shape[1])
        if (
            type(rewards) is not torch.Tensor
            or tuple(rewards.shape) != (E, M, 1)
            or rewards.dtype is not torch.float32
            or rewards.device != share_obs.device
            or rewards.requires_grad
            or not bool(torch.isfinite(rewards).all().item())
            or type(dones) is not torch.Tensor
            or tuple(dones.shape) != (E, M)
            or dones.dtype is not torch.bool
            or dones.device != share_obs.device
            or dones.requires_grad
        ):
            _fail(
                "collector rewards/dones violate the fixed HARL contract",
                failure_code="collector_step_tensor_contract",
                stage="collector_consume",
                expected=((E, M, 1), (E, M), share_obs.device),
                actual=((getattr(rewards, "shape", None), getattr(rewards, "dtype", None)), (getattr(dones, "shape", None), getattr(dones, "dtype", None))),
            )
        if (
            type(value_preds) is not torch.Tensor
            or tuple(value_preds.shape) != (E, 1)
            or value_preds.dtype is not torch.float32
            or value_preds.device != share_obs.device
            or value_preds.requires_grad
            or not bool(torch.isfinite(value_preds).all().item())
            or type(rnn_states_critic_after_current) is not torch.Tensor
            or tuple(rnn_states_critic_after_current.shape)
            != tuple(self.critic_buffer.rnn_states_critic.shape[1:])
            or rnn_states_critic_after_current.dtype is not torch.float32
            or rnn_states_critic_after_current.device != share_obs.device
            or rnn_states_critic_after_current.requires_grad
            or not bool(torch.isfinite(rnn_states_critic_after_current).all().item())
        ):
            _fail(
                "collector value/RNN evidence violates the rollout critic contract",
                failure_code="collector_critic_state_contract",
                stage="collector_consume",
                expected=((E, 1), tuple(self.critic_buffer.rnn_states_critic.shape[1:]), torch.float32, share_obs.device, False),
                actual=(
                    (getattr(value_preds, "shape", None), getattr(value_preds, "dtype", None), getattr(value_preds, "device", None)),
                    (getattr(rnn_states_critic_after_current, "shape", None), getattr(rnn_states_critic_after_current, "dtype", None), getattr(rnn_states_critic_after_current, "device", None)),
                ),
            )
        try:
            correlation = correlate_event_terminal_infos_v2(
                expectation=expectation,
                dones=dones,
                infos=infos,
            )
            keys = tuple(key.value for key in correlation.terminal_keys)
            duplicates = tuple(key for key in keys if key in self._consumed_terminal_keys)
            if duplicates:
                _fail(
                    "terminal learner DTO was already consumed",
                    failure_code="terminal_dto_already_consumed",
                    stage="collector_consume",
                    expected="new exact terminal keys",
                    actual=duplicates,
                )
            if len(self._consumed_terminal_keys.union(keys)) > (
                self.critic_buffer.episode_length * self.critic_buffer.n_rollout_threads
            ):
                _fail(
                    "terminal exactly-once ledger exceeded one fixed rollout bound",
                    failure_code="collector_ledger_bound",
                    stage="collector_consume",
                    expected=self.critic_buffer.episode_length * self.critic_buffer.n_rollout_threads,
                    actual=len(self._consumed_terminal_keys.union(keys)),
                )
            # Reserve before evaluation.  A failed forward or insertion poisons
            # this collector and can never trigger a second evaluation.
            self._consumed_terminal_keys.update(keys)
            event_batch = evaluate_event_timeout_bootstrap_values_v2(
                timeout_input=_make_timeout_critic_input_batch_v2(correlation),
                correlation=correlation,
                critic=critic,
                rollout_critic_guard=rollout_critic_guard,
                rnn_states_critic_after_current=rnn_states_critic_after_current,
            )
            done_env = dones[:, 0]
            next_masks = (~done_env).to(dtype=torch.float32).unsqueeze(-1)
            next_rnn = rnn_states_critic_after_current.detach().clone().contiguous()
            next_rnn[done_env] = 0.0
            bad_masks = torch.ones((E, 1), dtype=torch.float32, device=share_obs.device)
            bad_masks[event_batch._timeout_bootstrap_masks[:, 0]] = 0.0
            self.critic_buffer.insert_event(
                share_obs[:, 0],
                next_rnn,
                value_preds,
                rewards[:, 0],
                next_masks,
                bad_masks,
                transition_slot=transition_slot,
                event_batch=event_batch,
            )
        except Exception:
            self._poisoned = True
            raise
        return event_batch


__all__: tuple[str, ...] = ()
