"""Pure, default-off execution-facts and generation-clock foundations.

This B0-1A/B0-1B module accepts only an already-resolved event-gated profile.
It keeps explicit facts construction separate from an instance-owned,
per-environment generation clock.  Neither component is wired into the task
environment or any outer runtime route.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_authority_runtime"
)
ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_SOURCE_PURPOSE = (
    "pure default-off execution facts and generation clock foundations"
)

if __name__ != CANONICAL_ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment lifecycle authority runtime "
        "source must execute under its canonical module key; "
        f"expected module key="
        f"{CANONICAL_ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose="
        f"{ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_SOURCE_PURPOSE!r}"
    )


from dataclasses import dataclass, field
from threading import Lock

import torch

from .assignment_lifecycle_transition_contract import (
    EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
    EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
    ExecutionFactsProducerId,
    ExecutionFactsProducerStamp,
    ExecutionTransitionFacts,
)
from .assignment_profile_contract import (
    AssignmentProfileRouteError,
    ResolvedEventGatedAssignmentProfile,
)


_INT64_MAX = 2**63 - 1
_PROCESS_TOKEN_LOCK = Lock()
_NEXT_TOKEN_BY_ENV: dict[int, int] = {}


class ExecutionFactsProducerRuntimeError(RuntimeError):
    """A private producer input or token-allocation boundary was violated."""


class GenerationClockRuntimeError(RuntimeError):
    """A pure generation-clock protocol boundary was violated."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        env_id: int | None = None,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.env_id = env_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; env_id={env_id!r}; "
            f"expected={expected!r}; actual={actual!r}"
        )


@dataclass(frozen=True, slots=True, eq=False)
class TransitionGenerationContext:
    """Immutable identity-bearing candidate for one environment row."""

    env_id: int
    episode_generation: int
    transition_generation: int
    _clock_identity: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class GenerationClockSnapshotRow:
    """Detached scalar view of one row in a generation clock."""

    env_id: int
    episode_generation: int
    transition_generation: int
    outstanding_transition_generation: int | None


@dataclass(frozen=True, slots=True)
class _OutstandingTransition:
    context: TransitionGenerationContext
    env_id: int
    episode_generation: int
    transition_generation: int


@dataclass(frozen=True, slots=True)
class _GenerationClockState:
    episode_generation: tuple[int, ...]
    transition_generation: tuple[int, ...]
    outstanding: tuple[_OutstandingTransition | None, ...]


class LifecycleGenerationClock:
    """Own per-row episode and committed-transition generations.

    One clock instance belongs to one declared vector-environment domain and
    must be retained for that domain's process lifetime.  It exposes no state
    reinitialization or candidate-discard capability.
    """

    __slots__ = (
        "_profile",
        "_device",
        "_env_ids",
        "_row_by_env",
        "_clock_identity",
        "_lock",
        "_state",
    )

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
        *,
        env_ids: torch.Tensor,
    ) -> None:
        if type(profile) is not ResolvedEventGatedAssignmentProfile:
            raise AssignmentProfileRouteError(
                "generation clock accepts only the canonical event-gated "
                "resolved-profile subtype",
                profile=getattr(profile, "profile_name", None),
                expected=ResolvedEventGatedAssignmentProfile,
                actual=type(profile),
                resolution_origin=getattr(profile, "resolution_origin", None),
            )
        device, domain_env_ids = self._validate_declared_env_ids(env_ids)
        self._profile = profile
        self._device = device
        self._env_ids = domain_env_ids
        self._row_by_env = {
            env_id: row for row, env_id in enumerate(domain_env_ids)
        }
        self._clock_identity = object()
        self._lock = Lock()
        row_count = len(domain_env_ids)
        self._state = _GenerationClockState(
            episode_generation=(-1,) * row_count,
            transition_generation=(-1,) * row_count,
            outstanding=(None,) * row_count,
        )

    def snapshot(
        self,
        env_ids: torch.Tensor,
    ) -> tuple[GenerationClockSnapshotRow, ...]:
        """Return detached scalar snapshots for selected rows."""

        selected_env_ids, rows = self._normalize_selected_env_ids(env_ids)
        with self._lock:
            return self._snapshot_rows(self._state, selected_env_ids, rows)

    def advance_episode(
        self,
        env_ids: torch.Tensor,
    ) -> tuple[GenerationClockSnapshotRow, ...]:
        """Atomically advance selected episode generations by exactly one."""

        selected_env_ids, rows = self._normalize_selected_env_ids(env_ids)
        with self._lock:
            state = self._state
            for env_id, row in zip(selected_env_ids, rows, strict=True):
                active = state.outstanding[row]
                if active is not None:
                    raise GenerationClockRuntimeError(
                        "episode advance is blocked by an outstanding candidate",
                        failure_code="outstanding_transition",
                        env_id=env_id,
                        expected=None,
                        actual=active.transition_generation,
                    )
                current = state.episode_generation[row]
                if current == _INT64_MAX:
                    raise GenerationClockRuntimeError(
                        "episode generation space is exhausted",
                        failure_code="episode_overflow",
                        env_id=env_id,
                        expected=f"< {_INT64_MAX}",
                        actual=current,
                    )

            next_episode = list(state.episode_generation)
            for row in rows:
                next_episode[row] += 1
            replacement = _GenerationClockState(
                episode_generation=tuple(next_episode),
                transition_generation=state.transition_generation,
                outstanding=state.outstanding,
            )
            self._state = replacement
            return self._snapshot_rows(
                replacement,
                selected_env_ids,
                rows,
            )

    def request_transition_candidate(
        self,
        env_ids: torch.Tensor,
    ) -> tuple[TransitionGenerationContext, ...]:
        """Atomically reserve the exact next candidate for selected rows."""

        selected_env_ids, rows = self._normalize_selected_env_ids(env_ids)
        with self._lock:
            state = self._state
            for env_id, row in zip(selected_env_ids, rows, strict=True):
                episode = state.episode_generation[row]
                if episode < 0:
                    raise GenerationClockRuntimeError(
                        "a transition candidate requires a started episode",
                        failure_code="episode_not_started",
                        env_id=env_id,
                        expected=">= 0",
                        actual=episode,
                    )
                active = state.outstanding[row]
                if active is not None:
                    raise GenerationClockRuntimeError(
                        "an active transition candidate already exists",
                        failure_code="candidate_already_outstanding",
                        env_id=env_id,
                        expected=None,
                        actual=active.transition_generation,
                    )
                committed = state.transition_generation[row]
                if committed == _INT64_MAX:
                    raise GenerationClockRuntimeError(
                        "transition generation space is exhausted",
                        failure_code="transition_overflow",
                        env_id=env_id,
                        expected=f"< {_INT64_MAX}",
                        actual=committed,
                    )

            contexts = tuple(
                TransitionGenerationContext(
                    env_id=env_id,
                    episode_generation=state.episode_generation[row],
                    transition_generation=state.transition_generation[row] + 1,
                    _clock_identity=self._clock_identity,
                )
                for env_id, row in zip(selected_env_ids, rows, strict=True)
            )
            next_outstanding = list(state.outstanding)
            for context, row in zip(contexts, rows, strict=True):
                next_outstanding[row] = _OutstandingTransition(
                    context=context,
                    env_id=context.env_id,
                    episode_generation=context.episode_generation,
                    transition_generation=context.transition_generation,
                )
            self._state = _GenerationClockState(
                episode_generation=state.episode_generation,
                transition_generation=state.transition_generation,
                outstanding=tuple(next_outstanding),
            )
            return contexts

    def commit_transition(
        self,
        env_ids: torch.Tensor,
        contexts: tuple[TransitionGenerationContext, ...],
    ) -> tuple[GenerationClockSnapshotRow, ...]:
        """Atomically commit exact active candidates for selected rows."""

        selected_env_ids, rows = self._normalize_selected_env_ids(env_ids)
        if type(contexts) is not tuple:
            raise GenerationClockRuntimeError(
                "transition contexts must be an exact tuple",
                failure_code="context_container_type",
                expected=tuple,
                actual=type(contexts),
            )
        if len(contexts) != len(rows):
            raise GenerationClockRuntimeError(
                "transition context count must match selected rows",
                failure_code="context_count",
                expected=len(rows),
                actual=len(contexts),
            )
        for context in contexts:
            if type(context) is not TransitionGenerationContext:
                raise GenerationClockRuntimeError(
                    "each transition context must use the exact runtime type",
                    failure_code="context_type",
                    expected=TransitionGenerationContext,
                    actual=type(context),
                )

        with self._lock:
            state = self._state
            validated_transitions: list[int] = []
            for env_id, row, context in zip(
                selected_env_ids,
                rows,
                contexts,
                strict=True,
            ):
                context_env_id = context.env_id
                context_episode = context.episode_generation
                context_transition = context.transition_generation
                context_clock_identity = context._clock_identity
                if any(
                    type(value) is not int
                    for value in (
                        context_env_id,
                        context_episode,
                        context_transition,
                    )
                ):
                    raise GenerationClockRuntimeError(
                        "transition context scalar fields must be exact integers",
                        failure_code="context_scalar_type",
                        expected=int,
                        actual=(
                            type(context_env_id),
                            type(context_episode),
                            type(context_transition),
                        ),
                    )
                if context_env_id != env_id:
                    raise GenerationClockRuntimeError(
                        "transition context belongs to another environment row",
                        failure_code="wrong_env",
                        env_id=env_id,
                        expected=env_id,
                        actual=context_env_id,
                    )
                if context_clock_identity is not self._clock_identity:
                    raise GenerationClockRuntimeError(
                        "transition context belongs to another clock",
                        failure_code="wrong_clock",
                        env_id=env_id,
                        expected="selected clock identity",
                        actual="different clock identity",
                    )
                current_episode = state.episode_generation[row]
                if context_episode != current_episode:
                    raise GenerationClockRuntimeError(
                        "transition context belongs to another episode",
                        failure_code="wrong_episode",
                        env_id=env_id,
                        expected=current_episode,
                        actual=context_episode,
                    )
                committed = state.transition_generation[row]
                candidate = context_transition
                expected_candidate = committed + 1
                if candidate < committed:
                    raise GenerationClockRuntimeError(
                        "transition context is stale",
                        failure_code="stale_candidate",
                        env_id=env_id,
                        expected=expected_candidate,
                        actual=candidate,
                    )
                if candidate == committed:
                    raise GenerationClockRuntimeError(
                        "transition context was already committed",
                        failure_code="duplicate_commit",
                        env_id=env_id,
                        expected=expected_candidate,
                        actual=candidate,
                    )
                if candidate > expected_candidate:
                    raise GenerationClockRuntimeError(
                        "transition context is from the future",
                        failure_code="future_candidate",
                        env_id=env_id,
                        expected=expected_candidate,
                        actual=candidate,
                    )
                active = state.outstanding[row]
                if active is None:
                    raise GenerationClockRuntimeError(
                        "transition context is not outstanding",
                        failure_code="candidate_not_outstanding",
                        env_id=env_id,
                        expected=expected_candidate,
                        actual=None,
                    )
                if active.context is not context:
                    raise GenerationClockRuntimeError(
                        "transition candidate identity does not match",
                        failure_code="candidate_identity",
                        env_id=env_id,
                        expected=id(active.context),
                        actual=id(context),
                    )
                if (
                    active.env_id != context_env_id
                    or active.episode_generation != context_episode
                    or active.transition_generation != candidate
                ):
                    raise GenerationClockRuntimeError(
                        "active transition context was altered",
                        failure_code="candidate_content",
                        env_id=env_id,
                        expected=(
                            active.env_id,
                            active.episode_generation,
                            active.transition_generation,
                        ),
                        actual=(
                            context_env_id,
                            context_episode,
                            candidate,
                        ),
                    )
                validated_transitions.append(active.transition_generation)

            next_transition = list(state.transition_generation)
            next_outstanding = list(state.outstanding)
            for row, transition in zip(rows, validated_transitions, strict=True):
                next_transition[row] = transition
                next_outstanding[row] = None
            replacement = _GenerationClockState(
                episode_generation=state.episode_generation,
                transition_generation=tuple(next_transition),
                outstanding=tuple(next_outstanding),
            )
            self._state = replacement
            return self._snapshot_rows(
                replacement,
                selected_env_ids,
                rows,
            )

    @staticmethod
    def _validate_declared_env_ids(
        env_ids: torch.Tensor,
    ) -> tuple[torch.device, tuple[int, ...]]:
        if type(env_ids) is not torch.Tensor:
            raise GenerationClockRuntimeError(
                "declared env IDs must be an exact torch.Tensor",
                failure_code="env_id_type",
                expected=torch.Tensor,
                actual=type(env_ids),
            )
        if env_ids.dtype is not torch.int64:
            raise GenerationClockRuntimeError(
                "declared env IDs must use torch.int64",
                failure_code="env_id_dtype",
                expected=torch.int64,
                actual=env_ids.dtype,
            )
        if env_ids.ndim != 1 or int(env_ids.numel()) <= 0:
            raise GenerationClockRuntimeError(
                "declared env IDs must have nonempty shape [E]",
                failure_code="env_id_shape",
                expected="nonempty [E]",
                actual=tuple(env_ids.shape),
            )
        if env_ids.layout is not torch.strided:
            raise GenerationClockRuntimeError(
                "declared env IDs must use a strided tensor layout",
                failure_code="env_id_layout",
                expected=torch.strided,
                actual=env_ids.layout,
            )
        try:
            values = tuple(
                int(value) for value in env_ids.detach().cpu().tolist()
            )
        except (NotImplementedError, RuntimeError, TypeError) as exc:
            raise GenerationClockRuntimeError(
                "declared env IDs must be materializable as scalar integers",
                failure_code="env_id_materialization",
                expected="materializable strided int64 tensor",
                actual=env_ids.device,
            ) from exc
        if len(set(values)) != len(values):
            raise GenerationClockRuntimeError(
                "declared env IDs must be unique",
                failure_code="env_id_unique",
                expected=len(values),
                actual=len(set(values)),
            )
        return env_ids.device, values

    def _normalize_selected_env_ids(
        self,
        env_ids: torch.Tensor,
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        device, values = self._validate_declared_env_ids(env_ids)
        if device != self._device:
            raise GenerationClockRuntimeError(
                "selected env IDs must use the declared device",
                failure_code="env_id_device",
                expected=self._device,
                actual=device,
            )
        unknown = tuple(value for value in values if value not in self._row_by_env)
        if unknown:
            raise GenerationClockRuntimeError(
                "selected env ID is outside the declared domain",
                failure_code="unknown_env",
                env_id=unknown[0],
                expected=self._env_ids,
                actual=unknown,
            )
        return values, tuple(self._row_by_env[value] for value in values)

    @staticmethod
    def _snapshot_rows(
        state: _GenerationClockState,
        env_ids: tuple[int, ...],
        rows: tuple[int, ...],
    ) -> tuple[GenerationClockSnapshotRow, ...]:
        return tuple(
            GenerationClockSnapshotRow(
                env_id=env_id,
                episode_generation=state.episode_generation[row],
                transition_generation=state.transition_generation[row],
                outstanding_transition_generation=(
                    None
                    if state.outstanding[row] is None
                    else state.outstanding[row].transition_generation
                ),
            )
            for env_id, row in zip(env_ids, rows, strict=True)
        )


@dataclass(frozen=True, slots=True)
class ExecutionTransitionInput:
    """Explicit raw tensors for one vectorized physical transition.

    ``coverage_before_transition`` is the raw physical coverage baseline.  The
    producer combines it only with the explicit pair-attributed completion
    input to form the prospective pre-reset coverage snapshot.
    """

    device: torch.device
    env_id: torch.Tensor
    episode_generation: torch.Tensor
    transition_generation: torch.Tensor
    physical_terminated: torch.Tensor
    physical_truncated: torch.Tensor
    time_limit_reached: torch.Tensor
    bad_transition: torch.Tensor
    completion_signals: torch.Tensor
    terminal_pair_failure_signals: torch.Tensor
    forced_release_signals: torch.Tensor
    robot_unavailable_signals: torch.Tensor
    robot_recovered_signals: torch.Tensor
    coverage_before_transition: torch.Tensor
    task_state_before_transition: torch.Tensor
    robot_state_before_transition: torch.Tensor
    ownership_before_transition: torch.Tensor


class EnvironmentExecutionFactsProducer:
    """Build canonical immutable execution facts for the event profile only."""

    __slots__ = (
        "_profile",
        "_producer_stamp",
    )

    def __init__(self, profile: ResolvedEventGatedAssignmentProfile) -> None:
        if type(profile) is not ResolvedEventGatedAssignmentProfile:
            raise AssignmentProfileRouteError(
                "execution facts producer accepts only the canonical "
                "event-gated resolved-profile subtype",
                profile=getattr(profile, "profile_name", None),
                expected=ResolvedEventGatedAssignmentProfile,
                actual=type(profile),
                resolution_origin=getattr(profile, "resolution_origin", None),
            )
        self._profile = profile
        self._producer_stamp = ExecutionFactsProducerStamp(
            producer_id=(
                ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
            ),
            producer_contract_version=(
                EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
            ),
        )

    def build_facts(
        self,
        transition_input: ExecutionTransitionInput,
    ) -> ExecutionTransitionFacts:
        """Validate explicit inputs and construct one canonical facts batch.

        Tokens are allocated before final tensor/schema validation.  A token
        allocated for a batch that later fails is deliberately burned.
        """

        if type(transition_input) is not ExecutionTransitionInput:
            raise ExecutionFactsProducerRuntimeError(
                "build_facts requires an exact ExecutionTransitionInput"
            )

        consume_once_token = self._allocate_consume_tokens(transition_input)
        coverage_before_reset = self._prospective_coverage(transition_input)

        values: dict[str, object] = {
            "schema_version": EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            "producer_contract_version": (
                EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
            ),
            "producer_id": (
                ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
            ),
            "env_id": transition_input.env_id,
            "episode_generation": transition_input.episode_generation,
            "transition_generation": transition_input.transition_generation,
            "physical_terminated": transition_input.physical_terminated,
            "physical_truncated": transition_input.physical_truncated,
            "time_limit_reached": transition_input.time_limit_reached,
            "bad_transition": transition_input.bad_transition,
            "completion_signals": transition_input.completion_signals,
            "terminal_pair_failure_signals": (
                transition_input.terminal_pair_failure_signals
            ),
            "forced_release_signals": transition_input.forced_release_signals,
            "robot_unavailable_signals": (
                transition_input.robot_unavailable_signals
            ),
            "robot_recovered_signals": (
                transition_input.robot_recovered_signals
            ),
            "coverage_before_reset": coverage_before_reset,
            "task_state_before_transition": (
                transition_input.task_state_before_transition
            ),
            "robot_state_before_transition": (
                transition_input.robot_state_before_transition
            ),
            "ownership_before_transition": (
                transition_input.ownership_before_transition
            ),
            "consume_once_token": consume_once_token,
        }
        return ExecutionTransitionFacts.from_mapping(
            values,
            producer_stamp=self._producer_stamp,
            device=transition_input.device,
        )

    def _allocate_consume_tokens(
        self,
        transition_input: ExecutionTransitionInput,
    ) -> torch.Tensor:
        device = transition_input.device
        env_id = transition_input.env_id
        if type(device) is not torch.device:
            raise ExecutionFactsProducerRuntimeError(
                "transition input device must be an exact torch.device"
            )
        if type(env_id) is not torch.Tensor:
            raise ExecutionFactsProducerRuntimeError(
                "transition input env_id must be an exact torch.Tensor"
            )
        if env_id.dtype is not torch.int64:
            raise ExecutionFactsProducerRuntimeError(
                "transition input env_id must use torch.int64"
            )
        if env_id.device != device:
            raise ExecutionFactsProducerRuntimeError(
                "transition input env_id must be on the explicit device"
            )
        if env_id.ndim != 1 or int(env_id.numel()) <= 0:
            raise ExecutionFactsProducerRuntimeError(
                "transition input env_id must have nonempty shape [E]"
            )

        env_ids = tuple(int(value) for value in env_id.detach().cpu().tolist())
        if len(set(env_ids)) != len(env_ids):
            raise ExecutionFactsProducerRuntimeError(
                "transition input env_id rows must be unique"
            )

        with _PROCESS_TOKEN_LOCK:
            tokens = tuple(
                _NEXT_TOKEN_BY_ENV.get(env_value, 0)
                for env_value in env_ids
            )
            exhausted = tuple(
                env_value
                for env_value, token in zip(env_ids, tokens, strict=True)
                if token > _INT64_MAX
            )
            if exhausted:
                raise ExecutionFactsProducerRuntimeError(
                    "consume-once token space exhausted for env IDs "
                    f"{exhausted!r}"
                )
            for env_value, token in zip(env_ids, tokens, strict=True):
                _NEXT_TOKEN_BY_ENV[env_value] = token + 1

        return torch.tensor(tokens, dtype=torch.int64, device=device)

    @staticmethod
    def _prospective_coverage(
        transition_input: ExecutionTransitionInput,
    ) -> torch.Tensor:
        completion = transition_input.completion_signals
        coverage = transition_input.coverage_before_transition
        device = transition_input.device
        env_count = int(transition_input.env_id.numel())

        if type(completion) is not torch.Tensor or type(coverage) is not torch.Tensor:
            raise ExecutionFactsProducerRuntimeError(
                "completion and coverage inputs must be exact torch.Tensor values"
            )
        if completion.dtype is not torch.bool or coverage.dtype is not torch.bool:
            raise ExecutionFactsProducerRuntimeError(
                "completion and coverage inputs must use torch.bool"
            )
        if completion.device != device or coverage.device != device:
            raise ExecutionFactsProducerRuntimeError(
                "completion and coverage inputs must be on the explicit device"
            )
        if completion.ndim != 3 or int(completion.shape[0]) != env_count:
            raise ExecutionFactsProducerRuntimeError(
                "completion_signals must have shape [E,M,N]"
            )
        expected_coverage_shape = (env_count, int(completion.shape[2]))
        if coverage.ndim != 2 or tuple(coverage.shape) != expected_coverage_shape:
            raise ExecutionFactsProducerRuntimeError(
                "coverage_before_transition must have shape [E,N]"
            )
        return coverage | completion.any(dim=1)


__all__ = [
    "CANONICAL_ASSIGNMENT_LIFECYCLE_AUTHORITY_RUNTIME_MODULE",
    "EnvironmentExecutionFactsProducer",
    "ExecutionFactsProducerRuntimeError",
    "ExecutionTransitionInput",
    "GenerationClockRuntimeError",
    "GenerationClockSnapshotRow",
    "LifecycleGenerationClock",
    "TransitionGenerationContext",
]
