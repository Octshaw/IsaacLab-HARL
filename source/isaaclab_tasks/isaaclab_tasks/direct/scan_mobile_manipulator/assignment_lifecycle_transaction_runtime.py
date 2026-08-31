"""Pure, default-off B0-2 lifecycle-authority transaction foundation.

This module is deliberately separate from the B0-1A facts producer and the
B0-1B generation clock.  It consumes their canonical artifacts but has no
environment, wrapper, resolver, controller, Isaac, or HARL entrypoint.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transaction_runtime"
)
ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_SOURCE_PURPOSE = (
    "pure default-off lifecycle state and authority transaction foundation"
)

if __name__ != CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment lifecycle transaction "
        "runtime source must execute under its canonical module key; "
        f"expected module key="
        f"{CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_MODULE!r}; "
        f"actual module key={__name__!r}; source purpose="
        f"{ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_SOURCE_PURPOSE!r}"
    )


from dataclasses import dataclass, field
from threading import Event, Lock
from types import MappingProxyType
from typing import Mapping

import torch

from .assignment_initial_claim_runtime import (
    EffectiveAssignmentCommitArtifact,
    InitialClaimDeriver,
    InitialClaimRequest,
    InitialClaimRuntimeError,
    NO_CLAIM,
    _CurrentPublicationIdentity,
    _CurrentPublicationProvenance,
    _CurrentPublicationProvenanceKind,
    _EventRuntimeCurrentPublication,
    _InitialClaimCandidate,
    _InitialClaimRequestContext,
    _InitialClaimSourceBaseline,
    _InitialClaimSourceKind,
    _tensor_digest,
)
from .assignment_event_contract import (
    LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
    LifecycleCausalSource,
    LifecycleEventRecord,
    LifecycleEventType,
    PairFailureEventPayload,
    RobotLifecycleEventPayload,
    TaskLifecycleEventPayload,
    validate_lifecycle_event_records,
)
from .assignment_lifecycle_authority_runtime import (
    LifecycleGenerationClock,
    TransitionGenerationContext,
)
from .assignment_lifecycle_transition_contract import (
    EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
    LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
    ExecutionFactsProducerId,
    ExecutionFactsProducerStamp,
    ExecutionTransitionFacts,
    LifecycleAuthorityId,
    LifecycleAuthorityStamp,
    LifecycleTransitionResult,
    LifecycleTransitionResultFactory,
    RobotLifecycleState,
    TaskLifecycleState,
    TerminationReason,
    TransitionConsumeLedger,
    TransitionGenerationExpectation,
)
from .assignment_profile_contract import (
    AssignmentProfileRouteError,
    ResolvedEventGatedAssignmentProfile,
)


_INT64_MAX = 2**63 - 1
_ACTIVE_TASK_STATES = (
    int(TaskLifecycleState.CLAIMED),
    int(TaskLifecycleState.NAVIGATING),
    int(TaskLifecycleState.ALIGNING),
)
_TERMINAL_TASK_STATES = (
    int(TaskLifecycleState.COMPLETED),
    int(TaskLifecycleState.TEAM_INFEASIBLE),
)
_EVENT_TYPE_RANK = {
    event_type: rank for rank, event_type in enumerate(LifecycleEventType)
}
_EVENT_TYPE_BY_RANK = tuple(LifecycleEventType)


class _B02RuntimeError(RuntimeError):
    """Typed B0-2 failure with stable, reviewable context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str | None = None,
        field_name: str | None = None,
        env_id: int | None = None,
        expected: object = None,
        actual: object = None,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.stage = stage
        self.field_name = field_name
        self.env_id = env_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"field_name={field_name!r}; env_id={env_id!r}; "
            f"expected={expected!r}; actual={actual!r}"
        )


class LifecycleStateRuntimeError(_B02RuntimeError):
    """The versioned lifecycle-state boundary was violated."""


class LifecycleAuthorityRuntimeError(_B02RuntimeError):
    """The pure lifecycle semantic derivation boundary was violated."""


class LifecycleCoordinatorRuntimeError(_B02RuntimeError):
    """The authority transaction/publication protocol was violated."""


class LifecycleEpisodeRebuildRuntimeError(_B02RuntimeError):
    """The pure episode-rebuild transaction protocol was violated."""


def _require_event_profile(
    profile: object,
    *,
    component: str,
) -> ResolvedEventGatedAssignmentProfile:
    if type(profile) is not ResolvedEventGatedAssignmentProfile:
        raise AssignmentProfileRouteError(
            f"{component} accepts only the canonical event-gated "
            "resolved-profile subtype",
            profile=getattr(profile, "profile_name", None),
            expected=ResolvedEventGatedAssignmentProfile,
            actual=type(profile),
            resolution_origin=getattr(profile, "resolution_origin", None),
        )
    return profile


def _first_true(mask: torch.Tensor) -> tuple[int, ...] | None:
    indices = torch.nonzero(mask, as_tuple=False)
    if int(indices.numel()) == 0:
        return None
    return tuple(int(value.item()) for value in indices[0])


def _enum_mask(value: torch.Tensor, members: tuple[int, ...]) -> torch.Tensor:
    valid = torch.zeros_like(value, dtype=torch.bool)
    for member in members:
        valid |= value == member
    return valid


def _capture_tensor(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    error_type: type[_B02RuntimeError],
    stage: str,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise error_type(
            f"{field_name} must be an exact torch.Tensor",
            failure_code="tensor_type",
            stage=stage,
            field_name=field_name,
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.layout is not torch.strided:
        raise error_type(
            f"{field_name} must use a strided tensor layout",
            failure_code="tensor_layout",
            stage=stage,
            field_name=field_name,
            expected=torch.strided,
            actual=value.layout,
        )
    if tuple(value.shape) != shape:
        raise error_type(
            f"{field_name} has the wrong shape",
            failure_code="shape",
            stage=stage,
            field_name=field_name,
            expected=shape,
            actual=tuple(value.shape),
        )
    if value.dtype is not dtype:
        raise error_type(
            f"{field_name} has the wrong dtype",
            failure_code="dtype",
            stage=stage,
            field_name=field_name,
            expected=dtype,
            actual=value.dtype,
        )
    if value.device != device:
        raise error_type(
            f"{field_name} is on the wrong device",
            failure_code="device",
            stage=stage,
            field_name=field_name,
            expected=device,
            actual=value.device,
        )
    if value.requires_grad:
        raise error_type(
            f"{field_name} must not require gradients",
            failure_code="requires_grad",
            stage=stage,
            field_name=field_name,
            expected=False,
            actual=True,
        )
    return value.detach().clone().contiguous()


def _validate_state_invariants(
    *,
    env_id: torch.Tensor,
    task_state: torch.Tensor,
    robot_state: torch.Tensor,
    ownership: torch.Tensor,
    cumulative_failed_pairs: torch.Tensor,
    completion_count: torch.Tensor,
    termination_reason: torch.Tensor,
    error_type: type[_B02RuntimeError],
    stage: str,
) -> None:
    env_count, num_tasks = task_state.shape
    num_robots = robot_state.shape[1]

    if int(torch.unique(env_id).numel()) != env_count:
        raise error_type(
            "lifecycle state env_id rows must be unique",
            failure_code="env_id_unique",
            stage=stage,
            field_name="env_id",
            expected=env_count,
            actual=int(torch.unique(env_id).numel()),
        )

    task_members = tuple(int(member) for member in TaskLifecycleState)
    invalid = ~_enum_mask(task_state, task_members)
    index = _first_true(invalid)
    if index is not None:
        row, task = index
        raise error_type(
            "task_state is outside the canonical enum domain",
            failure_code="task_state_enum",
            stage=stage,
            field_name="task_state",
            env_id=int(env_id[row].item()),
            expected=task_members,
            actual={"task": task, "state": int(task_state[row, task].item())},
        )

    robot_members = tuple(int(member) for member in RobotLifecycleState)
    invalid = ~_enum_mask(robot_state, robot_members)
    index = _first_true(invalid)
    if index is not None:
        row, robot = index
        raise error_type(
            "robot_state is outside the canonical enum domain",
            failure_code="robot_state_enum",
            stage=stage,
            field_name="robot_state",
            env_id=int(env_id[row].item()),
            expected=robot_members,
            actual={"robot": robot, "state": int(robot_state[row, robot].item())},
        )

    reason_members = tuple(int(member) for member in TerminationReason)
    invalid = ~_enum_mask(termination_reason, reason_members)
    index = _first_true(invalid)
    if index is not None:
        row = index[0]
        raise error_type(
            "termination_reason is outside the canonical enum domain",
            failure_code="termination_reason_enum",
            stage=stage,
            field_name="termination_reason",
            env_id=int(env_id[row].item()),
            expected=reason_members,
            actual=int(termination_reason[row].item()),
        )

    invalid_owner = (ownership < -1) | (ownership >= num_robots)
    index = _first_true(invalid_owner)
    if index is not None:
        row, task = index
        raise error_type(
            "ownership is outside -1..M-1",
            failure_code="ownership_range",
            stage=stage,
            field_name="ownership",
            env_id=int(env_id[row].item()),
            expected=(-1, num_robots - 1),
            actual={"task": task, "owner": int(ownership[row, task].item())},
        )

    active = _enum_mask(task_state, _ACTIVE_TASK_STATES)
    non_active_owned = ~active & (ownership != -1)
    index = _first_true(non_active_owned)
    if index is not None:
        row, task = index
        raise error_type(
            "only an active task may have an owner",
            failure_code="non_active_owned",
            stage=stage,
            field_name="ownership",
            env_id=int(env_id[row].item()),
            expected=-1,
            actual={"task": task, "owner": int(ownership[row, task].item())},
        )
    active_unowned = active & (ownership == -1)
    index = _first_true(active_unowned)
    if index is not None:
        row, task = index
        raise error_type(
            "every active task requires exactly one owner",
            failure_code="active_unowned",
            stage=stage,
            field_name="ownership",
            env_id=int(env_id[row].item()),
            expected="0..M-1",
            actual={"task": task, "owner": -1},
        )

    robot_ids = torch.arange(
        num_robots,
        dtype=torch.int64,
        device=task_state.device,
    ).view(1, num_robots, 1)
    owner_match = ownership.unsqueeze(1) == robot_ids
    active_owned = active.unsqueeze(1) & owner_match
    owned_count = active_owned.sum(dim=2)
    index = _first_true(owned_count > 1)
    if index is not None:
        row, robot = index
        raise error_type(
            "one robot may own at most one active task",
            failure_code="robot_multiple_active_tasks",
            stage=stage,
            field_name="ownership",
            env_id=int(env_id[row].item()),
            expected="<= 1",
            actual={"robot": robot, "count": int(owned_count[row, robot].item())},
        )

    executing = robot_state == int(RobotLifecycleState.EXECUTING)
    executing_mismatch = executing != (owned_count == 1)
    index = _first_true(executing_mismatch)
    if index is not None:
        row, robot = index
        raise error_type(
            "robot EXECUTING state and active ownership are not mutual inverses",
            failure_code="robot_ownership_inverse",
            stage=stage,
            field_name="robot_state",
            env_id=int(env_id[row].item()),
            expected={"executing": bool((owned_count[row, robot] == 1).item())},
            actual={
                "robot": robot,
                "state": int(robot_state[row, robot].item()),
                "owned_count": int(owned_count[row, robot].item()),
            },
        )

    failed_active_owner = active_owned & cumulative_failed_pairs
    index = _first_true(failed_active_owner)
    if index is not None:
        row, robot, task = index
        raise error_type(
            "an active task cannot use a cumulative permanently failed pair",
            failure_code="active_owner_failed_pair",
            stage=stage,
            field_name="cumulative_failed_pairs",
            env_id=int(env_id[row].item()),
            expected=False,
            actual={"robot": robot, "task": task, "failed": True},
        )

    team_equation = (
        task_state != int(TaskLifecycleState.COMPLETED)
    ) & cumulative_failed_pairs.all(dim=1)
    team_state = task_state == int(TaskLifecycleState.TEAM_INFEASIBLE)
    index = _first_true(team_equation != team_state)
    if index is not None:
        row, task = index
        raise error_type(
            "task TEAM_INFEASIBLE state differs from cumulative failure equation",
            failure_code="team_equation",
            stage=stage,
            field_name="task_state",
            env_id=int(env_id[row].item()),
            expected=bool(team_equation[row, task].item()),
            actual={
                "task": task,
                "team_state": bool(team_state[row, task].item()),
            },
        )

    index = _first_true(completion_count < 0)
    if index is not None:
        row, robot = index
        raise error_type(
            "completion_count must be non-negative",
            failure_code="completion_count_nonnegative",
            stage=stage,
            field_name="completion_count",
            env_id=int(env_id[row].item()),
            expected=">= 0",
            actual={"robot": robot, "count": int(completion_count[row, robot].item())},
        )

    all_completed = (task_state == int(TaskLifecycleState.COMPLETED)).all(dim=1)
    all_terminal = _enum_mask(task_state, _TERMINAL_TASK_STATES).all(dim=1)
    expected_terminal_reason = torch.full_like(
        termination_reason,
        int(TerminationReason.NONE),
    )
    expected_terminal_reason[all_terminal & ~all_completed] = int(
        TerminationReason.NO_FEASIBLE_TASKS_REMAIN
    )
    expected_terminal_reason[all_completed] = int(
        TerminationReason.ALL_TASKS_COMPLETED
    )
    terminal_rows = all_terminal
    index = _first_true(
        terminal_rows & (termination_reason != expected_terminal_reason)
    )
    if index is not None:
        row = index[0]
        raise error_type(
            "terminal lifecycle state has an inconsistent termination reason",
            failure_code="stored_termination_reason",
            stage=stage,
            field_name="termination_reason",
            env_id=int(env_id[row].item()),
            expected=int(expected_terminal_reason[row].item()),
            actual=int(termination_reason[row].item()),
        )
    invalid_nonterminal_reason = ~terminal_rows & ~(
        (termination_reason == int(TerminationReason.NONE))
        | (termination_reason == int(TerminationReason.TIME_LIMIT))
    )
    index = _first_true(invalid_nonterminal_reason)
    if index is not None:
        row = index[0]
        raise error_type(
            "nonterminal lifecycle state has a task-terminal reason",
            failure_code="stored_termination_reason",
            stage=stage,
            field_name="termination_reason",
            env_id=int(env_id[row].item()),
            expected=(int(TerminationReason.NONE), int(TerminationReason.TIME_LIMIT)),
            actual=int(termination_reason[row].item()),
        )


@dataclass(frozen=True, slots=True)
class _LifecycleStoreState:
    version: int
    task_state: torch.Tensor = field(repr=False)
    robot_state: torch.Tensor = field(repr=False)
    ownership: torch.Tensor = field(repr=False)
    cumulative_failed_pairs: torch.Tensor = field(repr=False)
    completion_count: torch.Tensor = field(repr=False)
    termination_reason: torch.Tensor = field(repr=False)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class LifecycleStateSnapshot:
    """B0-private, immutable/no-alias full-domain lifecycle snapshot."""

    store_version: int
    _store_identity: object = field(repr=False)
    _device: torch.device = field(repr=False)
    _env_id: torch.Tensor = field(repr=False)
    _task_state: torch.Tensor = field(repr=False)
    _robot_state: torch.Tensor = field(repr=False)
    _ownership: torch.Tensor = field(repr=False)
    _cumulative_failed_pairs: torch.Tensor = field(repr=False)
    _completion_count: torch.Tensor = field(repr=False)
    _termination_reason: torch.Tensor = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise LifecycleStateRuntimeError(
            "LifecycleStateSnapshot can only be issued by LifecycleStateStore",
            failure_code="snapshot_factory_required",
            stage="state_snapshot",
            expected="LifecycleStateStore.snapshot",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        store_identity: object,
        device: torch.device,
        env_id: torch.Tensor,
        state: _LifecycleStoreState,
    ) -> "LifecycleStateSnapshot":
        instance = object.__new__(cls)
        object.__setattr__(instance, "store_version", state.version)
        object.__setattr__(instance, "_store_identity", store_identity)
        object.__setattr__(instance, "_device", device)
        for name, value in (
            ("_env_id", env_id),
            ("_task_state", state.task_state),
            ("_robot_state", state.robot_state),
            ("_ownership", state.ownership),
            ("_cumulative_failed_pairs", state.cumulative_failed_pairs),
            ("_completion_count", state.completion_count),
            ("_termination_reason", state.termination_reason),
        ):
            object.__setattr__(
                instance,
                name,
                value.detach().clone().contiguous(),
            )
        return instance

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def num_envs(self) -> int:
        return int(self._env_id.shape[0])

    @property
    def num_robots(self) -> int:
        return int(self._robot_state.shape[1])

    @property
    def num_tasks(self) -> int:
        return int(self._task_state.shape[1])

    @property
    def env_id(self) -> torch.Tensor:
        return self._env_id.detach().clone().contiguous()

    @property
    def task_state(self) -> torch.Tensor:
        return self._task_state.detach().clone().contiguous()

    @property
    def robot_state(self) -> torch.Tensor:
        return self._robot_state.detach().clone().contiguous()

    @property
    def ownership(self) -> torch.Tensor:
        return self._ownership.detach().clone().contiguous()

    @property
    def cumulative_failed_pairs(self) -> torch.Tensor:
        return self._cumulative_failed_pairs.detach().clone().contiguous()

    @property
    def completion_count(self) -> torch.Tensor:
        return self._completion_count.detach().clone().contiguous()

    @property
    def termination_reason(self) -> torch.Tensor:
        return self._termination_reason.detach().clone().contiguous()

    def _tensor_mapping(self) -> Mapping[str, torch.Tensor]:
        return MappingProxyType(
            {
                "env_id": self.env_id,
                "task_state": self.task_state,
                "robot_state": self.robot_state,
                "ownership": self.ownership,
                "cumulative_failed_pairs": self.cumulative_failed_pairs,
                "completion_count": self.completion_count,
                "termination_reason": self.termination_reason,
            }
        )


@dataclass(frozen=True, slots=True, eq=False)
class _PreparedLifecycleSwap:
    _store_identity: object = field(repr=False)
    _writer_capability: object = field(repr=False)
    _expected_state: _LifecycleStoreState = field(repr=False)
    _replacement_state: _LifecycleStoreState = field(repr=False)
    _replacement_snapshot: LifecycleStateSnapshot = field(repr=False)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EpisodeRebuildInputs:
    """Unversioned B0-private, immutable/no-alias episode-reset inputs."""

    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _device: torch.device = field(repr=False)
    _selected_env_ids: torch.Tensor = field(repr=False)
    _initial_task_state: torch.Tensor = field(repr=False)
    _initial_robot_state: torch.Tensor = field(repr=False)
    _initial_ownership: torch.Tensor = field(repr=False)

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
        *,
        device: torch.device,
        selected_env_ids: torch.Tensor,
        initial_task_state: torch.Tensor,
        initial_robot_state: torch.Tensor,
        initial_ownership: torch.Tensor,
    ) -> None:
        canonical_profile = _require_event_profile(
            profile,
            component="_EpisodeRebuildInputs",
        )
        if type(device) is not torch.device:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild inputs require an explicit torch.device",
                failure_code="device_type",
                stage="reset_input",
                field_name="device",
                expected=torch.device,
                actual=type(device),
            )
        if type(selected_env_ids) is not torch.Tensor or selected_env_ids.ndim != 1:
            raise LifecycleEpisodeRebuildRuntimeError(
                "selected_env_ids must have exact nonempty shape [R]",
                failure_code="selected_env_shape",
                stage="reset_input",
                field_name="selected_env_ids",
                expected="nonempty rank-one torch.Tensor",
                actual=(type(selected_env_ids), getattr(selected_env_ids, "shape", None)),
            )
        selected_count = int(selected_env_ids.shape[0])
        if selected_count <= 0:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild selection must not be empty",
                failure_code="selected_env_shape",
                stage="reset_input",
                field_name="selected_env_ids",
                expected="R > 0",
                actual=selected_count,
            )
        if type(initial_task_state) is not torch.Tensor or initial_task_state.ndim != 2:
            raise LifecycleEpisodeRebuildRuntimeError(
                "initial_task_state must have exact shape [R,N]",
                failure_code="shape",
                stage="reset_input",
                field_name="initial_task_state",
                expected="rank-two torch.Tensor",
                actual=(type(initial_task_state), getattr(initial_task_state, "shape", None)),
            )
        if type(initial_robot_state) is not torch.Tensor or initial_robot_state.ndim != 2:
            raise LifecycleEpisodeRebuildRuntimeError(
                "initial_robot_state must have exact shape [R,M]",
                failure_code="shape",
                stage="reset_input",
                field_name="initial_robot_state",
                expected="rank-two torch.Tensor",
                actual=(type(initial_robot_state), getattr(initial_robot_state, "shape", None)),
            )
        num_tasks = int(initial_task_state.shape[1])
        num_robots = int(initial_robot_state.shape[1])
        if num_tasks <= 0 or num_robots <= 0:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild inputs require positive M and N",
                failure_code="dimensions",
                stage="reset_input",
                expected="M > 0 and N > 0",
                actual=(num_robots, num_tasks),
            )
        captured = {
            "selected_env_ids": _capture_tensor(
                selected_env_ids,
                field_name="selected_env_ids",
                shape=(selected_count,),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleEpisodeRebuildRuntimeError,
                stage="reset_input",
            ),
            "initial_task_state": _capture_tensor(
                initial_task_state,
                field_name="initial_task_state",
                shape=(selected_count, num_tasks),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleEpisodeRebuildRuntimeError,
                stage="reset_input",
            ),
            "initial_robot_state": _capture_tensor(
                initial_robot_state,
                field_name="initial_robot_state",
                shape=(selected_count, num_robots),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleEpisodeRebuildRuntimeError,
                stage="reset_input",
            ),
            "initial_ownership": _capture_tensor(
                initial_ownership,
                field_name="initial_ownership",
                shape=(selected_count, num_tasks),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleEpisodeRebuildRuntimeError,
                stage="reset_input",
            ),
        }
        if len(set(int(value) for value in captured["selected_env_ids"].cpu().tolist())) != selected_count:
            raise LifecycleEpisodeRebuildRuntimeError(
                "selected episode-rebuild environment IDs must be unique",
                failure_code="selected_env_unique",
                stage="reset_input",
                field_name="selected_env_ids",
                expected=selected_count,
                actual=len(set(int(value) for value in captured["selected_env_ids"].cpu().tolist())),
            )
        object.__setattr__(self, "_profile", canonical_profile)
        object.__setattr__(self, "_device", device)
        for name, value in captured.items():
            object.__setattr__(self, f"_{name}", value)

    @property
    def selected_env_ids(self) -> torch.Tensor:
        return self._selected_env_ids.detach().clone().contiguous()

    @property
    def initial_task_state(self) -> torch.Tensor:
        return self._initial_task_state.detach().clone().contiguous()

    @property
    def initial_robot_state(self) -> torch.Tensor:
        return self._initial_robot_state.detach().clone().contiguous()

    @property
    def initial_ownership(self) -> torch.Tensor:
        return self._initial_ownership.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, eq=False)
class _EpisodeRebuildCandidate:
    """Fully prepared, transaction-private full-domain reset candidate."""

    _store_identity: object = field(repr=False)
    store_version: int
    selected_env_ids: tuple[int, ...]
    selected_rows: tuple[int, ...]
    task_state: torch.Tensor = field(repr=False)
    robot_state: torch.Tensor = field(repr=False)
    ownership: torch.Tensor = field(repr=False)
    cumulative_failed_pairs: torch.Tensor = field(repr=False)
    completion_count: torch.Tensor = field(repr=False)
    termination_reason: torch.Tensor = field(repr=False)
    expected_episode_generation: torch.Tensor = field(repr=False)
    expected_transition_generation: torch.Tensor = field(repr=False)


class LifecycleStateStore:
    """Sole B0 lifecycle-state writer boundary; it derives no semantics."""

    __slots__ = (
        "_profile",
        "_device",
        "_env_id",
        "_num_envs",
        "_num_robots",
        "_num_tasks",
        "_store_identity",
        "_writer_capability",
        "_writer_claimed",
        "_lock",
        "_state",
    )

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
        *,
        device: torch.device,
        env_id: torch.Tensor,
        task_state: torch.Tensor,
        robot_state: torch.Tensor,
        ownership: torch.Tensor,
        cumulative_failed_pairs: torch.Tensor,
        completion_count: torch.Tensor,
        termination_reason: torch.Tensor,
    ) -> None:
        self._profile = _require_event_profile(
            profile,
            component="LifecycleStateStore",
        )
        if type(device) is not torch.device:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore requires an explicit torch.device",
                failure_code="device_type",
                stage="state_initialization",
                field_name="device",
                expected=torch.device,
                actual=type(device),
            )
        if type(env_id) is not torch.Tensor or env_id.ndim != 1:
            raise LifecycleStateRuntimeError(
                "env_id must have exact rank-one tensor shape [E]",
                failure_code="env_id_shape",
                stage="state_initialization",
                field_name="env_id",
                expected="nonempty [E] torch.Tensor",
                actual=(type(env_id), getattr(env_id, "shape", None)),
            )
        env_count = int(env_id.shape[0])
        if env_count <= 0:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore requires at least one environment row",
                failure_code="env_id_shape",
                stage="state_initialization",
                field_name="env_id",
                expected="E > 0",
                actual=env_count,
            )
        if type(task_state) is not torch.Tensor or task_state.ndim != 2:
            raise LifecycleStateRuntimeError(
                "task_state must have exact rank-two tensor shape [E,N]",
                failure_code="shape",
                stage="state_initialization",
                field_name="task_state",
                expected="[E,N] torch.Tensor",
                actual=(type(task_state), getattr(task_state, "shape", None)),
            )
        if type(robot_state) is not torch.Tensor or robot_state.ndim != 2:
            raise LifecycleStateRuntimeError(
                "robot_state must have exact rank-two tensor shape [E,M]",
                failure_code="shape",
                stage="state_initialization",
                field_name="robot_state",
                expected="[E,M] torch.Tensor",
                actual=(type(robot_state), getattr(robot_state, "shape", None)),
            )
        num_tasks = int(task_state.shape[1])
        num_robots = int(robot_state.shape[1])
        if num_tasks <= 0 or num_robots <= 0:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore requires positive M and N",
                failure_code="dimensions",
                stage="state_initialization",
                expected="M > 0 and N > 0",
                actual=(num_robots, num_tasks),
            )

        captured = {
            "env_id": _capture_tensor(
                env_id,
                field_name="env_id",
                shape=(env_count,),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "task_state": _capture_tensor(
                task_state,
                field_name="task_state",
                shape=(env_count, num_tasks),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "robot_state": _capture_tensor(
                robot_state,
                field_name="robot_state",
                shape=(env_count, num_robots),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "ownership": _capture_tensor(
                ownership,
                field_name="ownership",
                shape=(env_count, num_tasks),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "cumulative_failed_pairs": _capture_tensor(
                cumulative_failed_pairs,
                field_name="cumulative_failed_pairs",
                shape=(env_count, num_robots, num_tasks),
                dtype=torch.bool,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "completion_count": _capture_tensor(
                completion_count,
                field_name="completion_count",
                shape=(env_count, num_robots),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
            "termination_reason": _capture_tensor(
                termination_reason,
                field_name="termination_reason",
                shape=(env_count,),
                dtype=torch.int64,
                device=device,
                error_type=LifecycleStateRuntimeError,
                stage="state_initialization",
            ),
        }
        _validate_state_invariants(
            **captured,
            error_type=LifecycleStateRuntimeError,
            stage="state_initialization",
        )

        self._device = device
        self._env_id = captured["env_id"]
        self._num_envs = env_count
        self._num_robots = num_robots
        self._num_tasks = num_tasks
        self._store_identity = object()
        self._writer_capability = object()
        self._writer_claimed = False
        self._lock = Lock()
        self._state = _LifecycleStoreState(
            version=0,
            task_state=captured["task_state"],
            robot_state=captured["robot_state"],
            ownership=captured["ownership"],
            cumulative_failed_pairs=captured["cumulative_failed_pairs"],
            completion_count=captured["completion_count"],
            termination_reason=captured["termination_reason"],
        )

    def snapshot(self) -> LifecycleStateSnapshot:
        """Return a B0-private snapshot before a coordinator claims the store.

        Once the unique lifecycle writer has been claimed, fresh snapshots are
        available only through that capability.  This prevents a retained raw
        store reference from bypassing the coordinator publication lock.
        """

        with self._lock:
            if self._writer_claimed:
                raise LifecycleStateRuntimeError(
                    "fresh StateStore reads require the coordinator publication port",
                    failure_code="snapshot_capability_confined",
                    stage="state_snapshot",
                    expected="unclaimed B0-private store",
                    actual="lifecycle writer already claimed",
                )
            return LifecycleStateSnapshot._create(
                store_identity=self._store_identity,
                device=self._device,
                env_id=self._env_id,
                state=self._state,
            )

    def _snapshot_for_lifecycle(
        self,
        *,
        writer_capability: object,
    ) -> LifecycleStateSnapshot:
        """Capture a transaction-private snapshot for the unique writer."""

        with self._lock:
            if (
                not self._writer_claimed
                or writer_capability is not self._writer_capability
            ):
                raise LifecycleStateRuntimeError(
                    "transaction-private snapshot lacks the bound writer capability",
                    failure_code="writer_capability",
                    stage="state_snapshot",
                    expected="bound lifecycle writer capability",
                    actual="missing or foreign capability",
                )
            return LifecycleStateSnapshot._create(
                store_identity=self._store_identity,
                device=self._device,
                env_id=self._env_id,
                state=self._state,
            )

    def _claim_lifecycle_writer(self) -> object:
        with self._lock:
            if self._writer_claimed:
                raise LifecycleStateRuntimeError(
                    "LifecycleStateStore already has a lifecycle writer",
                    failure_code="writer_already_claimed",
                    stage="state_writer_binding",
                    expected=False,
                    actual=True,
                )
            self._writer_claimed = True
            return self._writer_capability

    def _validate_expected_snapshot(
        self,
        snapshot: object,
    ) -> _LifecycleStoreState:
        if type(snapshot) is not LifecycleStateSnapshot:
            raise LifecycleStateRuntimeError(
                "state operation requires an exact LifecycleStateSnapshot",
                failure_code="snapshot_type",
                stage="state_version_validation",
                expected=LifecycleStateSnapshot,
                actual=type(snapshot),
            )
        with self._lock:
            state = self._state
            if snapshot._store_identity is not self._store_identity:
                raise LifecycleStateRuntimeError(
                    "state snapshot belongs to another LifecycleStateStore",
                    failure_code="wrong_store",
                    stage="state_version_validation",
                    expected="bound store identity",
                    actual="different store identity",
                )
            if type(snapshot.store_version) is not int or snapshot.store_version != state.version:
                raise LifecycleStateRuntimeError(
                    "state snapshot version is stale or invalid",
                    failure_code="stale_store_version",
                    stage="state_version_validation",
                    expected=state.version,
                    actual=snapshot.store_version,
                )
            comparisons = (
                (snapshot._env_id, self._env_id, "env_id"),
                (snapshot._task_state, state.task_state, "task_state"),
                (snapshot._robot_state, state.robot_state, "robot_state"),
                (snapshot._ownership, state.ownership, "ownership"),
                (
                    snapshot._cumulative_failed_pairs,
                    state.cumulative_failed_pairs,
                    "cumulative_failed_pairs",
                ),
                (snapshot._completion_count, state.completion_count, "completion_count"),
                (
                    snapshot._termination_reason,
                    state.termination_reason,
                    "termination_reason",
                ),
            )
            for observed, expected, field_name in comparisons:
                if not torch.equal(observed, expected):
                    raise LifecycleStateRuntimeError(
                        "state snapshot contents differ from its bound live version",
                        failure_code="snapshot_content",
                        stage="state_version_validation",
                        field_name=field_name,
                        expected="exact bound store tensor",
                        actual="tensor values differ",
                    )
            return state

    def _prepare_lifecycle_swap(
        self,
        *,
        snapshot: LifecycleStateSnapshot,
        candidate: "_LifecycleTransitionCandidate",
        writer_capability: object,
    ) -> _PreparedLifecycleSwap:
        if writer_capability is not self._writer_capability or not self._writer_claimed:
            raise LifecycleStateRuntimeError(
                "lifecycle swap lacks the bound store-writer capability",
                failure_code="writer_capability",
                stage="state_prepare_swap",
                expected="bound writer capability",
                actual="missing or foreign capability",
            )
        if type(candidate) is not _LifecycleTransitionCandidate:
            raise LifecycleStateRuntimeError(
                "lifecycle swap requires an exact prepared authority candidate",
                failure_code="candidate_type",
                stage="state_prepare_swap",
                expected=_LifecycleTransitionCandidate,
                actual=type(candidate),
            )
        expected_state = self._validate_expected_snapshot(snapshot)
        if (
            candidate._store_identity is not self._store_identity
            or candidate.store_version != expected_state.version
        ):
            raise LifecycleStateRuntimeError(
                "authority candidate is bound to another store/version",
                failure_code="candidate_store_binding",
                stage="state_prepare_swap",
                expected=(id(self._store_identity), expected_state.version),
                actual=(id(candidate._store_identity), candidate.store_version),
            )
        if expected_state.version == _INT64_MAX:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore version space is exhausted",
                failure_code="store_version_overflow",
                stage="state_prepare_swap",
                expected=f"< {_INT64_MAX}",
                actual=expected_state.version,
            )

        prepared_tensors = {
            "env_id": self._env_id.detach().clone().contiguous(),
            "task_state": candidate.updated_task_state.detach().clone().contiguous(),
            "robot_state": candidate.updated_robot_state.detach().clone().contiguous(),
            "ownership": candidate.updated_ownership.detach().clone().contiguous(),
            "cumulative_failed_pairs": (
                candidate.updated_failed_pairs.detach().clone().contiguous()
            ),
            "completion_count": candidate.updated_completion_count.detach().clone().contiguous(),
            "termination_reason": candidate.termination_reason.detach().clone().contiguous(),
        }
        _validate_state_invariants(
            **prepared_tensors,
            error_type=LifecycleStateRuntimeError,
            stage="state_prepare_swap",
        )
        replacement = _LifecycleStoreState(
            version=expected_state.version + 1,
            task_state=prepared_tensors["task_state"],
            robot_state=prepared_tensors["robot_state"],
            ownership=prepared_tensors["ownership"],
            cumulative_failed_pairs=prepared_tensors["cumulative_failed_pairs"],
            completion_count=prepared_tensors["completion_count"],
            termination_reason=prepared_tensors["termination_reason"],
        )
        replacement_snapshot = LifecycleStateSnapshot._create(
            store_identity=self._store_identity,
            device=self._device,
            env_id=self._env_id,
            state=replacement,
        )
        return _PreparedLifecycleSwap(
            _store_identity=self._store_identity,
            _writer_capability=self._writer_capability,
            _expected_state=expected_state,
            _replacement_state=replacement,
            _replacement_snapshot=replacement_snapshot,
        )

    def _commit_prepared_lifecycle_swap(
        self,
        prepared: _PreparedLifecycleSwap,
        *,
        writer_capability: object,
    ) -> LifecycleStateSnapshot:
        if type(prepared) is not _PreparedLifecycleSwap:
            raise LifecycleStateRuntimeError(
                "state commit requires an exact prepared lifecycle swap",
                failure_code="prepared_swap_type",
                stage="state_commit_swap",
                expected=_PreparedLifecycleSwap,
                actual=type(prepared),
            )
        with self._lock:
            if (
                writer_capability is not self._writer_capability
                or prepared._writer_capability is not self._writer_capability
                or prepared._store_identity is not self._store_identity
            ):
                raise LifecycleStateRuntimeError(
                    "prepared swap lacks the bound writer/store capability",
                    failure_code="writer_capability",
                    stage="state_commit_swap",
                    expected="bound store and writer",
                    actual="foreign capability",
                )
            if self._state is not prepared._expected_state:
                raise LifecycleStateRuntimeError(
                    "prepared lifecycle swap is stale or already used",
                    failure_code="stale_prepared_swap",
                    stage="state_commit_swap",
                    expected=prepared._expected_state.version,
                    actual=self._state.version,
                )
            self._state = prepared._replacement_state
            return prepared._replacement_snapshot

    def _prepare_episode_rebuild_swap(
        self,
        *,
        snapshot: LifecycleStateSnapshot,
        candidate: _EpisodeRebuildCandidate,
        writer_capability: object,
    ) -> _PreparedLifecycleSwap:
        """Allocate and validate one no-fail-tail episode-reset replacement."""

        if writer_capability is not self._writer_capability or not self._writer_claimed:
            raise LifecycleStateRuntimeError(
                "episode rebuild lacks the bound store-writer capability",
                failure_code="writer_capability",
                stage="reset_state_prepare_swap",
                expected="bound writer capability",
                actual="missing or foreign capability",
            )
        if type(candidate) is not _EpisodeRebuildCandidate:
            raise LifecycleStateRuntimeError(
                "episode rebuild requires an exact prepared reset candidate",
                failure_code="candidate_type",
                stage="reset_state_prepare_swap",
                expected=_EpisodeRebuildCandidate,
                actual=type(candidate),
            )
        expected_state = self._validate_expected_snapshot(snapshot)
        if (
            candidate._store_identity is not self._store_identity
            or candidate.store_version != expected_state.version
        ):
            raise LifecycleStateRuntimeError(
                "episode rebuild candidate belongs to another store/version",
                failure_code="candidate_store_binding",
                stage="reset_state_prepare_swap",
                expected=(id(self._store_identity), expected_state.version),
                actual=(id(candidate._store_identity), candidate.store_version),
            )
        if expected_state.version == _INT64_MAX:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore version space is exhausted",
                failure_code="store_version_overflow",
                stage="reset_state_prepare_swap",
                expected=f"< {_INT64_MAX}",
                actual=expected_state.version,
            )
        prepared_tensors = {
            "env_id": self._env_id.detach().clone().contiguous(),
            "task_state": candidate.task_state.detach().clone().contiguous(),
            "robot_state": candidate.robot_state.detach().clone().contiguous(),
            "ownership": candidate.ownership.detach().clone().contiguous(),
            "cumulative_failed_pairs": (
                candidate.cumulative_failed_pairs.detach().clone().contiguous()
            ),
            "completion_count": candidate.completion_count.detach().clone().contiguous(),
            "termination_reason": candidate.termination_reason.detach().clone().contiguous(),
        }
        _validate_state_invariants(
            **prepared_tensors,
            error_type=LifecycleStateRuntimeError,
            stage="reset_state_prepare_swap",
        )
        replacement = _LifecycleStoreState(
            version=expected_state.version + 1,
            task_state=prepared_tensors["task_state"],
            robot_state=prepared_tensors["robot_state"],
            ownership=prepared_tensors["ownership"],
            cumulative_failed_pairs=prepared_tensors["cumulative_failed_pairs"],
            completion_count=prepared_tensors["completion_count"],
            termination_reason=prepared_tensors["termination_reason"],
        )
        replacement_snapshot = LifecycleStateSnapshot._create(
            store_identity=self._store_identity,
            device=self._device,
            env_id=self._env_id,
            state=replacement,
        )
        return _PreparedLifecycleSwap(
            _store_identity=self._store_identity,
            _writer_capability=self._writer_capability,
            _expected_state=expected_state,
            _replacement_state=replacement,
            _replacement_snapshot=replacement_snapshot,
        )

    def _prepare_initial_claim_swap(
        self,
        *,
        snapshot: LifecycleStateSnapshot,
        candidate: _InitialClaimCandidate,
        writer_capability: object,
    ) -> _PreparedLifecycleSwap:
        """Prepare one assignment-owned-only replacement for the sole writer."""

        if writer_capability is not self._writer_capability or not self._writer_claimed:
            raise LifecycleStateRuntimeError(
                "initial claim lacks the bound Store writer capability",
                failure_code="writer_capability",
                stage="claim_state_prepare",
                expected="bound writer capability",
                actual="missing or foreign capability",
            )
        if type(candidate) is not _InitialClaimCandidate:
            raise LifecycleStateRuntimeError(
                "initial claim requires the exact pure deriver candidate",
                failure_code="candidate_type",
                stage="claim_state_prepare",
                expected=_InitialClaimCandidate,
                actual=type(candidate),
            )
        expected_state = self._validate_expected_snapshot(snapshot)
        if (
            candidate._store_identity is not self._store_identity
            or candidate.store_version != expected_state.version
        ):
            raise LifecycleStateRuntimeError(
                "initial-claim candidate belongs to another Store/version",
                failure_code="candidate_store_binding",
                stage="claim_state_prepare",
                expected=(id(self._store_identity), expected_state.version),
                actual=(id(candidate._store_identity), candidate.store_version),
            )
        if expected_state.version == _INT64_MAX:
            raise LifecycleStateRuntimeError(
                "LifecycleStateStore version space is exhausted",
                failure_code="store_version_overflow",
                stage="claim_state_prepare",
                expected=f"< {_INT64_MAX}",
                actual=expected_state.version,
            )

        expected_task = expected_state.task_state.detach().clone().contiguous()
        expected_robot = expected_state.robot_state.detach().clone().contiguous()
        expected_owner = expected_state.ownership.detach().clone().contiguous()
        selected = set(candidate.selected_rows)
        for input_row, domain_row in enumerate(candidate.selected_rows):
            if not 0 <= domain_row < self._num_envs:
                raise LifecycleStateRuntimeError(
                    "initial-claim selected row is outside the Store domain",
                    failure_code="selected_row",
                    stage="claim_state_prepare",
                    expected=f"0 <= row < {self._num_envs}",
                    actual=domain_row,
                )
            for robot_id, task_value in enumerate(
                candidate.effective_task_by_robot[input_row].tolist()
            ):
                task_id = int(task_value)
                if task_id == NO_CLAIM:
                    continue
                expected_task[domain_row, task_id] = int(TaskLifecycleState.CLAIMED)
                expected_owner[domain_row, task_id] = robot_id

            available = expected_task[domain_row] == int(TaskLifecycleState.AVAILABLE)
            unowned = expected_owner[domain_row] == -1
            active = _enum_mask(expected_task[domain_row], _ACTIVE_TASK_STATES)
            for robot_id in range(self._num_robots):
                if int(expected_state.robot_state[domain_row, robot_id].item()) == int(
                    RobotLifecycleState.UNAVAILABLE
                ):
                    expected_robot[domain_row, robot_id] = int(
                        RobotLifecycleState.UNAVAILABLE
                    )
                elif bool(
                    (active & (expected_owner[domain_row] == robot_id)).any().item()
                ):
                    expected_robot[domain_row, robot_id] = int(
                        RobotLifecycleState.EXECUTING
                    )
                elif bool(
                    (
                        available
                        & unowned
                        & ~expected_state.cumulative_failed_pairs[
                            domain_row, robot_id
                        ]
                    )
                    .any()
                    .item()
                ):
                    expected_robot[domain_row, robot_id] = int(
                        RobotLifecycleState.NEEDS_ASSIGNMENT
                    )
                else:
                    expected_robot[domain_row, robot_id] = int(
                        RobotLifecycleState.WAITING_FOR_TASK
                    )

        for row in range(self._num_envs):
            if row not in selected and not (
                torch.equal(candidate.task_state[row], expected_state.task_state[row])
                and torch.equal(candidate.robot_state[row], expected_state.robot_state[row])
                and torch.equal(candidate.ownership[row], expected_state.ownership[row])
            ):
                raise LifecycleStateRuntimeError(
                    "initial claim changed an unselected environment row",
                    failure_code="unselected_row_changed",
                    stage="claim_state_prepare",
                    env_id=int(self._env_id[row].item()),
                    expected="bit-exact unselected row",
                    actual="assignment-owned tensor differs",
                )
        for observed, expected, field_name in (
            (candidate.task_state, expected_task, "task_state"),
            (candidate.robot_state, expected_robot, "robot_state"),
            (candidate.ownership, expected_owner, "ownership"),
            (
                candidate.cumulative_failed_pairs,
                expected_state.cumulative_failed_pairs,
                "cumulative_failed_pairs",
            ),
            (candidate.completion_count, expected_state.completion_count, "completion_count"),
            (candidate.termination_reason, expected_state.termination_reason, "termination_reason"),
        ):
            if not torch.equal(observed, expected):
                raise LifecycleStateRuntimeError(
                    "initial claim candidate exceeds its assignment-owned delta",
                    failure_code="claim_delta",
                    stage="claim_state_prepare",
                    field_name=field_name,
                    expected="exact typed initial-claim projection",
                    actual="tensor values differ",
                )

        prepared_tensors = {
            "env_id": self._env_id.detach().clone().contiguous(),
            "task_state": candidate.task_state.detach().clone().contiguous(),
            "robot_state": candidate.robot_state.detach().clone().contiguous(),
            "ownership": candidate.ownership.detach().clone().contiguous(),
            "cumulative_failed_pairs": candidate.cumulative_failed_pairs.detach().clone().contiguous(),
            "completion_count": candidate.completion_count.detach().clone().contiguous(),
            "termination_reason": candidate.termination_reason.detach().clone().contiguous(),
        }
        _validate_state_invariants(
            **prepared_tensors,
            error_type=LifecycleStateRuntimeError,
            stage="claim_state_prepare",
        )
        replacement = _LifecycleStoreState(
            version=expected_state.version + 1,
            task_state=prepared_tensors["task_state"],
            robot_state=prepared_tensors["robot_state"],
            ownership=prepared_tensors["ownership"],
            cumulative_failed_pairs=prepared_tensors["cumulative_failed_pairs"],
            completion_count=prepared_tensors["completion_count"],
            termination_reason=prepared_tensors["termination_reason"],
        )
        replacement_snapshot = LifecycleStateSnapshot._create(
            store_identity=self._store_identity,
            device=self._device,
            env_id=self._env_id,
            state=replacement,
        )
        return _PreparedLifecycleSwap(
            _store_identity=self._store_identity,
            _writer_capability=self._writer_capability,
            _expected_state=expected_state,
            _replacement_state=replacement,
            _replacement_snapshot=replacement_snapshot,
        )


@dataclass(frozen=True, slots=True)
class _LogicalEventSpec:
    env_row: int
    env_id: int
    event_type: LifecycleEventType
    causal_source: LifecycleCausalSource
    robot_id: int
    task_id: int
    payload: (
        TaskLifecycleEventPayload
        | RobotLifecycleEventPayload
        | PairFailureEventPayload
    )


@dataclass(frozen=True, slots=True, eq=False)
class _LifecycleTransitionCandidate:
    """Unversioned transaction-private output of the sole semantic authority."""

    facts: ExecutionTransitionFacts = field(repr=False)
    _store_identity: object = field(repr=False)
    store_version: int
    context_rows: tuple[tuple[int, int, int], ...]
    completed_tasks: torch.Tensor = field(repr=False)
    released_tasks: torch.Tensor = field(repr=False)
    new_failed_pairs: torch.Tensor = field(repr=False)
    prior_failed_pairs: torch.Tensor = field(repr=False)
    updated_failed_pairs: torch.Tensor = field(repr=False)
    new_team_infeasible_tasks: torch.Tensor = field(repr=False)
    updated_task_state: torch.Tensor = field(repr=False)
    updated_robot_state: torch.Tensor = field(repr=False)
    updated_ownership: torch.Tensor = field(repr=False)
    termination_reason: torch.Tensor = field(repr=False)
    updated_completion_count: torch.Tensor = field(repr=False)
    lifecycle_events: tuple[LifecycleEventRecord, ...]


class LifecycleAuthorityRuntime:
    """Sole pure B0 semantic derivation authority for canonical facts."""

    __slots__ = (
        "_profile",
        "_authority_stamp",
        "_producer_stamp",
    )

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
    ) -> None:
        self._profile = _require_event_profile(
            profile,
            component="LifecycleAuthorityRuntime",
        )
        self._authority_stamp = LifecycleAuthorityStamp(
            authority_id=LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
            authority_contract_version=LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
        )
        self._producer_stamp = ExecutionFactsProducerStamp(
            producer_id=ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1,
            producer_contract_version=EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
        )

    def derive_candidate(
        self,
        *,
        facts: ExecutionTransitionFacts,
        state_snapshot: LifecycleStateSnapshot,
        transition_contexts: tuple[TransitionGenerationContext, ...],
    ) -> _LifecycleTransitionCandidate:
        """Derive and fully prevalidate one candidate without mutation."""

        facts_values, state_values, context_rows = self._validate_inputs(
            facts=facts,
            state_snapshot=state_snapshot,
            transition_contexts=transition_contexts,
        )
        env_id = facts_values["env_id"]
        task0 = state_values["task_state"]
        robot0 = state_values["robot_state"]
        owner0 = state_values["ownership"]
        failed0 = state_values["cumulative_failed_pairs"]
        count0 = state_values["completion_count"]

        completion = facts_values["completion_signals"]
        failure = facts_values["terminal_pair_failure_signals"]
        release = facts_values["forced_release_signals"]
        unavailable = facts_values["robot_unavailable_signals"]
        recovered = facts_values["robot_recovered_signals"]

        active0 = _enum_mask(task0, _ACTIVE_TASK_STATES)
        robot_ids = torch.arange(
            state_snapshot.num_robots,
            dtype=torch.int64,
            device=state_snapshot.device,
        ).view(1, state_snapshot.num_robots, 1)
        owner_match = owner0.unsqueeze(1) == robot_ids
        active_owned = active0.unsqueeze(1) & owner_match

        pair_signals = completion | failure | release
        index = _first_true(pair_signals & ~active_owned)
        if index is not None:
            row, robot, task = index
            raise LifecycleAuthorityRuntimeError(
                "C/F/R signals require the exact active pre-transition owner",
                failure_code="pair_signal_active_owner",
                stage="authority_prevalidation",
                field_name="completion/failure/release signals",
                env_id=int(env_id[row].item()),
                expected={"robot": robot, "task": task, "active_owner": True},
                actual=False,
            )
        index = _first_true(completion & failure)
        if index is not None:
            row, robot, task = index
            raise LifecycleAuthorityRuntimeError(
                "one owned pair cannot complete and terminal-fail together",
                failure_code="completion_failure_conflict",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected="C & F == false",
                actual={"robot": robot, "task": task},
            )
        index = _first_true(completion.sum(dim=1) > 1)
        if index is not None:
            row, task = index
            raise LifecycleAuthorityRuntimeError(
                "one task cannot have multiple completing robots",
                failure_code="completion_cardinality",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected="<= 1",
                actual={"task": task},
            )
        index = _first_true(
            unavailable
            & (robot0 == int(RobotLifecycleState.UNAVAILABLE))
        )
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "robot unavailable input must be a falling health edge",
                failure_code="repeated_unavailable_edge",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected="prior robot != UNAVAILABLE",
                actual={"robot": robot, "state": int(robot0[row, robot].item())},
            )
        index = _first_true(
            recovered
            & (robot0 != int(RobotLifecycleState.UNAVAILABLE))
        )
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "robot recovery input requires a prior UNAVAILABLE state",
                failure_code="invalid_recovery_edge",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected=int(RobotLifecycleState.UNAVAILABLE),
                actual={"robot": robot, "state": int(robot0[row, robot].item())},
            )
        owned_count0 = active_owned.sum(dim=2)
        index = _first_true(recovered & (owned_count0 != 0))
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "a recovering robot cannot retain active ownership",
                failure_code="recovery_ownership",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected=0,
                actual={"robot": robot, "count": int(owned_count0[row, robot].item())},
            )
        index = _first_true(unavailable & recovered)
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "one robot cannot become unavailable and recover together",
                failure_code="availability_edge_conflict",
                stage="authority_prevalidation",
                env_id=int(env_id[row].item()),
                expected="U & Rc == false",
                actual={"robot": robot},
            )

        completed = completion.any(dim=1)
        new_failed = failure & ~failed0
        updated_failed = failed0 | new_failed
        unavailable_release = (
            unavailable.unsqueeze(2) & owner_match & active0.unsqueeze(1)
        )
        release_request = release | failure | unavailable_release
        released = release_request.any(dim=1) & ~completed

        task_candidate = task0.detach().clone().contiguous()
        owner_candidate = owner0.detach().clone().contiguous()
        task_candidate[completed] = int(TaskLifecycleState.COMPLETED)
        owner_candidate[completed] = -1
        release_only = released & ~completed
        task_candidate[release_only] = int(TaskLifecycleState.AVAILABLE)
        owner_candidate[release_only] = -1

        completion_delta = completion.to(dtype=torch.int64).sum(dim=2)
        index = _first_true(count0 > (_INT64_MAX - completion_delta))
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "completion_count would overflow signed int64",
                failure_code="completion_count_overflow",
                stage="authority_derivation",
                field_name="completion_count",
                env_id=int(env_id[row].item()),
                expected=f"<= {_INT64_MAX}",
                actual={
                    "robot": robot,
                    "prior": int(count0[row, robot].item()),
                    "delta": int(completion_delta[row, robot].item()),
                },
            )
        count1 = count0 + completion_delta

        team_condition = (
            task_candidate != int(TaskLifecycleState.COMPLETED)
        ) & updated_failed.all(dim=1)
        new_team = team_condition & (
            task0 != int(TaskLifecycleState.TEAM_INFEASIBLE)
        )
        task1 = task_candidate.detach().clone().contiguous()
        owner1 = owner_candidate.detach().clone().contiguous()
        task1[team_condition] = int(TaskLifecycleState.TEAM_INFEASIBLE)
        owner1[team_condition] = -1

        active1 = _enum_mask(task1, _ACTIVE_TASK_STATES)
        owner_match1 = owner1.unsqueeze(1) == robot_ids
        owns_active1 = (active1.unsqueeze(1) & owner_match1).sum(dim=2)
        index = _first_true(owns_active1 > 1)
        if index is not None:
            row, robot = index
            raise LifecycleAuthorityRuntimeError(
                "candidate gives one robot multiple active tasks",
                failure_code="candidate_robot_multiple_tasks",
                stage="authority_derivation",
                env_id=int(env_id[row].item()),
                expected="<= 1",
                actual={"robot": robot, "count": int(owns_active1[row, robot].item())},
            )
        eligible_work = (
            (task1 == int(TaskLifecycleState.AVAILABLE)).unsqueeze(1)
            & (owner1 == -1).unsqueeze(1)
            & ~updated_failed
        ).any(dim=2)
        unavailable_after = unavailable | (
            (robot0 == int(RobotLifecycleState.UNAVAILABLE)) & ~recovered
        )
        robot1 = torch.full_like(
            robot0,
            int(RobotLifecycleState.WAITING_FOR_TASK),
        )
        robot1[eligible_work] = int(RobotLifecycleState.NEEDS_ASSIGNMENT)
        robot1[owns_active1 == 1] = int(RobotLifecycleState.EXECUTING)
        robot1[unavailable_after] = int(RobotLifecycleState.UNAVAILABLE)

        all_completed = (
            task1 == int(TaskLifecycleState.COMPLETED)
        ).all(dim=1)
        all_terminal = _enum_mask(task1, _TERMINAL_TASK_STATES).all(dim=1)
        reason = torch.full(
            (state_snapshot.num_envs,),
            int(TerminationReason.NONE),
            dtype=torch.int64,
            device=state_snapshot.device,
        )
        reason[facts_values["time_limit_reached"]] = int(
            TerminationReason.TIME_LIMIT
        )
        reason[all_terminal & ~all_completed] = int(
            TerminationReason.NO_FEASIBLE_TASKS_REMAIN
        )
        reason[all_completed] = int(TerminationReason.ALL_TASKS_COMPLETED)

        events = self._build_events(
            facts_values=facts_values,
            task0=task0,
            robot0=robot0,
            owner0=owner0,
            task1=task1,
            robot1=robot1,
            completed=completed,
            released=released,
            new_failed=new_failed,
            new_team=new_team,
        )
        candidate = _LifecycleTransitionCandidate(
            facts=facts,
            _store_identity=state_snapshot._store_identity,
            store_version=state_snapshot.store_version,
            context_rows=context_rows,
            completed_tasks=completed.detach().clone().contiguous(),
            released_tasks=released.detach().clone().contiguous(),
            new_failed_pairs=new_failed.detach().clone().contiguous(),
            prior_failed_pairs=failed0.detach().clone().contiguous(),
            updated_failed_pairs=updated_failed.detach().clone().contiguous(),
            new_team_infeasible_tasks=new_team.detach().clone().contiguous(),
            updated_task_state=task1.detach().clone().contiguous(),
            updated_robot_state=robot1.detach().clone().contiguous(),
            updated_ownership=owner1.detach().clone().contiguous(),
            termination_reason=reason.detach().clone().contiguous(),
            updated_completion_count=count1.detach().clone().contiguous(),
            lifecycle_events=events,
        )
        self._prevalidate_candidate(
            candidate=candidate,
            facts_values=facts_values,
            state_values=state_values,
        )
        return candidate

    def _validate_inputs(
        self,
        *,
        facts: object,
        state_snapshot: object,
        transition_contexts: object,
    ) -> tuple[
        Mapping[str, object],
        Mapping[str, torch.Tensor],
        tuple[tuple[int, int, int], ...],
    ]:
        if type(facts) is not ExecutionTransitionFacts:
            raise LifecycleAuthorityRuntimeError(
                "authority requires canonical ExecutionTransitionFacts",
                failure_code="facts_type",
                stage="authority_input",
                expected=ExecutionTransitionFacts,
                actual=type(facts),
            )
        facts.validate_integrity()
        facts_values = facts.to_mapping()
        if (
            facts.producer_id is not self._producer_stamp.producer_id
            or facts.producer_contract_version
            != self._producer_stamp.producer_contract_version
        ):
            raise LifecycleAuthorityRuntimeError(
                "facts producer identity differs from the canonical producer",
                failure_code="facts_producer",
                stage="authority_input",
                expected=(
                    self._producer_stamp.producer_id,
                    self._producer_stamp.producer_contract_version,
                ),
                actual=(facts.producer_id, facts.producer_contract_version),
            )
        if type(state_snapshot) is not LifecycleStateSnapshot:
            raise LifecycleAuthorityRuntimeError(
                "authority requires an exact LifecycleStateSnapshot",
                failure_code="snapshot_type",
                stage="authority_input",
                expected=LifecycleStateSnapshot,
                actual=type(state_snapshot),
            )
        if facts.device != state_snapshot.device:
            raise LifecycleAuthorityRuntimeError(
                "facts and state snapshot devices differ",
                failure_code="device",
                stage="authority_input",
                expected=state_snapshot.device,
                actual=facts.device,
            )
        if (
            facts.num_envs != state_snapshot.num_envs
            or facts.num_robots != state_snapshot.num_robots
            or facts.num_tasks != state_snapshot.num_tasks
        ):
            raise LifecycleAuthorityRuntimeError(
                "facts and state snapshot dimensions differ",
                failure_code="dimensions",
                stage="authority_input",
                expected=(
                    state_snapshot.num_envs,
                    state_snapshot.num_robots,
                    state_snapshot.num_tasks,
                ),
                actual=(facts.num_envs, facts.num_robots, facts.num_tasks),
            )
        state_values = state_snapshot._tensor_mapping()
        comparisons = (
            (facts_values["env_id"], state_values["env_id"], "env_id"),
            (
                facts_values["task_state_before_transition"],
                state_values["task_state"],
                "task_state_before_transition",
            ),
            (
                facts_values["robot_state_before_transition"],
                state_values["robot_state"],
                "robot_state_before_transition",
            ),
            (
                facts_values["ownership_before_transition"],
                state_values["ownership"],
                "ownership_before_transition",
            ),
        )
        for observed, expected, field_name in comparisons:
            if not torch.equal(observed, expected):
                raise LifecycleAuthorityRuntimeError(
                    "facts prestate differs from the exact store snapshot",
                    failure_code="facts_state_mismatch",
                    stage="authority_input",
                    field_name=field_name,
                    expected="exact snapshot tensor",
                    actual="tensor values differ",
                )

        _validate_state_invariants(
            env_id=state_values["env_id"],
            task_state=state_values["task_state"],
            robot_state=state_values["robot_state"],
            ownership=state_values["ownership"],
            cumulative_failed_pairs=state_values["cumulative_failed_pairs"],
            completion_count=state_values["completion_count"],
            termination_reason=state_values["termination_reason"],
            error_type=LifecycleAuthorityRuntimeError,
            stage="authority_prevalidation",
        )
        non_none_reason = state_values["termination_reason"] != int(
            TerminationReason.NONE
        )
        index = _first_true(non_none_reason)
        if index is not None:
            row = index[0]
            raise LifecycleAuthorityRuntimeError(
                "a physical transition requires a live nonterminal prestate",
                failure_code="terminal_prestate",
                stage="authority_prevalidation",
                env_id=int(state_values["env_id"][row].item()),
                expected=int(TerminationReason.NONE),
                actual=int(state_values["termination_reason"][row].item()),
            )

        if type(transition_contexts) is not tuple:
            raise LifecycleAuthorityRuntimeError(
                "transition contexts must be an exact tuple",
                failure_code="context_container_type",
                stage="authority_input",
                expected=tuple,
                actual=type(transition_contexts),
            )
        if len(transition_contexts) != facts.num_envs:
            raise LifecycleAuthorityRuntimeError(
                "transition context count differs from facts rows",
                failure_code="context_count",
                stage="authority_input",
                expected=facts.num_envs,
                actual=len(transition_contexts),
            )
        context_rows: list[tuple[int, int, int]] = []
        for row, context in enumerate(transition_contexts):
            if type(context) is not TransitionGenerationContext:
                raise LifecycleAuthorityRuntimeError(
                    "transition context has the wrong runtime type",
                    failure_code="context_type",
                    stage="authority_input",
                    expected=TransitionGenerationContext,
                    actual=type(context),
                )
            values = (
                context.env_id,
                context.episode_generation,
                context.transition_generation,
            )
            if any(type(value) is not int for value in values):
                raise LifecycleAuthorityRuntimeError(
                    "transition context scalars must be exact Python ints",
                    failure_code="context_scalar_type",
                    stage="authority_input",
                    expected=(int, int, int),
                    actual=tuple(type(value) for value in values),
                )
            expected_values = (
                int(facts_values["env_id"][row].item()),
                int(facts_values["episode_generation"][row].item()),
                int(facts_values["transition_generation"][row].item()),
            )
            if values != expected_values:
                raise LifecycleAuthorityRuntimeError(
                    "transition context differs from its facts row",
                    failure_code="context_facts_binding",
                    stage="authority_input",
                    env_id=expected_values[0],
                    expected=expected_values,
                    actual=values,
                )
            context_rows.append(values)
        return facts_values, state_values, tuple(context_rows)

    def _build_events(
        self,
        *,
        facts_values: Mapping[str, object],
        task0: torch.Tensor,
        robot0: torch.Tensor,
        owner0: torch.Tensor,
        task1: torch.Tensor,
        robot1: torch.Tensor,
        completed: torch.Tensor,
        released: torch.Tensor,
        new_failed: torch.Tensor,
        new_team: torch.Tensor,
    ) -> tuple[LifecycleEventRecord, ...]:
        env_ids = facts_values["env_id"]
        episodes = facts_values["episode_generation"]
        transitions = facts_values["transition_generation"]
        tokens = facts_values["consume_once_token"]
        completion = facts_values["completion_signals"]
        unavailable = facts_values["robot_unavailable_signals"]
        recovered = facts_values["robot_recovered_signals"]

        logical: list[_LogicalEventSpec] = []
        for row in range(int(env_ids.shape[0])):
            env_value = int(env_ids[row].item())
            for task in range(int(task0.shape[1])):
                if bool(completed[row, task].item()):
                    completers = torch.nonzero(
                        completion[row, :, task],
                        as_tuple=False,
                    ).flatten()
                    cause_robot = int(completers[0].item())
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=LifecycleEventType.TASK_COMPLETED,
                            causal_source=LifecycleCausalSource.EXECUTION_FACTS,
                            robot_id=cause_robot,
                            task_id=task,
                            payload=TaskLifecycleEventPayload(
                                task_id=task,
                                previous_task_state=int(task0[row, task].item()),
                                updated_task_state=int(TaskLifecycleState.COMPLETED),
                                cause_robot_id=cause_robot,
                            ),
                        )
                    )
                if bool(released[row, task].item()):
                    cause_robot = int(owner0[row, task].item())
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=LifecycleEventType.TASK_RELEASED,
                            causal_source=LifecycleCausalSource.EXECUTION_FACTS,
                            robot_id=cause_robot,
                            task_id=task,
                            payload=TaskLifecycleEventPayload(
                                task_id=task,
                                previous_task_state=int(task0[row, task].item()),
                                updated_task_state=int(TaskLifecycleState.AVAILABLE),
                                cause_robot_id=cause_robot,
                            ),
                        )
                    )
                if bool(new_team[row, task].item()):
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=(
                                LifecycleEventType.TASK_BECAME_TEAM_INFEASIBLE
                            ),
                            causal_source=(
                                LifecycleCausalSource.LIFECYCLE_DERIVATION
                            ),
                            robot_id=-1,
                            task_id=task,
                            payload=TaskLifecycleEventPayload(
                                task_id=task,
                                previous_task_state=int(TaskLifecycleState.AVAILABLE),
                                updated_task_state=int(
                                    TaskLifecycleState.TEAM_INFEASIBLE
                                ),
                                cause_robot_id=-1,
                            ),
                        )
                    )
            for robot in range(int(robot0.shape[1])):
                for task in range(int(task0.shape[1])):
                    if bool(new_failed[row, robot, task].item()):
                        logical.append(
                            _LogicalEventSpec(
                                env_row=row,
                                env_id=env_value,
                                event_type=(
                                    LifecycleEventType
                                    .TERMINAL_PAIR_FAILURE_RECORDED
                                ),
                                causal_source=(
                                    LifecycleCausalSource.EXECUTION_FACTS
                                ),
                                robot_id=robot,
                                task_id=task,
                                payload=PairFailureEventPayload(
                                    robot_id=robot,
                                    task_id=task,
                                    newly_recorded=True,
                                ),
                            )
                        )
                if bool(unavailable[row, robot].item()):
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=(
                                LifecycleEventType.ROBOT_BECAME_UNAVAILABLE
                            ),
                            causal_source=LifecycleCausalSource.EXECUTION_FACTS,
                            robot_id=robot,
                            task_id=-1,
                            payload=RobotLifecycleEventPayload(
                                robot_id=robot,
                                previous_robot_state=int(robot0[row, robot].item()),
                                updated_robot_state=int(
                                    RobotLifecycleState.UNAVAILABLE
                                ),
                            ),
                        )
                    )
                if bool(recovered[row, robot].item()):
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=LifecycleEventType.ROBOT_RECOVERED,
                            causal_source=LifecycleCausalSource.EXECUTION_FACTS,
                            robot_id=robot,
                            task_id=-1,
                            payload=RobotLifecycleEventPayload(
                                robot_id=robot,
                                previous_robot_state=int(
                                    RobotLifecycleState.UNAVAILABLE
                                ),
                                updated_robot_state=int(robot1[row, robot].item()),
                            ),
                        )
                    )
                if (
                    int(robot0[row, robot].item())
                    != int(RobotLifecycleState.NEEDS_ASSIGNMENT)
                    and int(robot1[row, robot].item())
                    == int(RobotLifecycleState.NEEDS_ASSIGNMENT)
                ):
                    logical.append(
                        _LogicalEventSpec(
                            env_row=row,
                            env_id=env_value,
                            event_type=(
                                LifecycleEventType.ROBOT_NEEDS_ASSIGNMENT
                            ),
                            causal_source=(
                                LifecycleCausalSource.LIFECYCLE_DERIVATION
                            ),
                            robot_id=robot,
                            task_id=-1,
                            payload=RobotLifecycleEventPayload(
                                robot_id=robot,
                                previous_robot_state=int(robot0[row, robot].item()),
                                updated_robot_state=int(
                                    RobotLifecycleState.NEEDS_ASSIGNMENT
                                ),
                            ),
                        )
                    )

        def sort_key(spec: _LogicalEventSpec) -> tuple[int, int, int, int]:
            rank = _EVENT_TYPE_RANK[spec.event_type]
            if spec.event_type in (
                LifecycleEventType.TASK_COMPLETED,
                LifecycleEventType.TASK_RELEASED,
                LifecycleEventType.TASK_BECAME_TEAM_INFEASIBLE,
            ):
                tie = (spec.task_id, spec.robot_id)
            elif spec.event_type is LifecycleEventType.TERMINAL_PAIR_FAILURE_RECORDED:
                tie = (spec.robot_id, spec.task_id)
            else:
                tie = (spec.robot_id, -1)
            return spec.env_id, rank, tie[0], tie[1]

        logical.sort(key=sort_key)
        ordinals: dict[int, int] = {}
        records: list[LifecycleEventRecord] = []
        for spec in logical:
            ordinal = ordinals.get(spec.env_id, 0)
            ordinals[spec.env_id] = ordinal + 1
            episode = int(episodes[spec.env_row].item())
            transition = int(transitions[spec.env_row].item())
            record = LifecycleEventRecord(
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                event_id=(spec.env_id, episode, transition, ordinal),
                causal_source=spec.causal_source,
                event_type=spec.event_type,
                env_id=spec.env_id,
                episode_generation=episode,
                transition_generation=transition,
                ordinal=ordinal,
                robot_id=spec.robot_id,
                task_id=spec.task_id,
                trigger_eligible=True,
                facts_consume_token=int(tokens[spec.env_row].item()),
                authority_id=self._authority_stamp.authority_id,
                payload=spec.payload,
            )
            records.append(record)
        return validate_lifecycle_event_records(tuple(records))

    def _prevalidate_candidate(
        self,
        *,
        candidate: _LifecycleTransitionCandidate,
        facts_values: Mapping[str, object],
        state_values: Mapping[str, torch.Tensor],
    ) -> None:
        env_id = state_values["env_id"]
        _validate_state_invariants(
            env_id=env_id,
            task_state=candidate.updated_task_state,
            robot_state=candidate.updated_robot_state,
            ownership=candidate.updated_ownership,
            cumulative_failed_pairs=candidate.updated_failed_pairs,
            completion_count=candidate.updated_completion_count,
            termination_reason=candidate.termination_reason,
            error_type=LifecycleAuthorityRuntimeError,
            stage="authority_candidate_prevalidation",
        )
        completion = facts_values["completion_signals"]
        failure = facts_values["terminal_pair_failure_signals"]
        release = facts_values["forced_release_signals"]
        unavailable = facts_values["robot_unavailable_signals"]
        recovered = facts_values["robot_recovered_signals"]
        task0 = state_values["task_state"]
        robot0 = state_values["robot_state"]
        owner0 = state_values["ownership"]
        failed0 = state_values["cumulative_failed_pairs"]
        count0 = state_values["completion_count"]
        active0 = _enum_mask(task0, _ACTIVE_TASK_STATES)
        robot_ids = torch.arange(
            candidate.updated_robot_state.shape[1],
            dtype=torch.int64,
            device=env_id.device,
        ).view(1, candidate.updated_robot_state.shape[1], 1)
        owner_match = owner0.unsqueeze(1) == robot_ids
        expected_completed = completion.any(dim=1)
        expected_new_failed = failure & ~failed0
        expected_updated_failed = failed0 | expected_new_failed
        expected_release = (
            release
            | failure
            | (unavailable.unsqueeze(2) & owner_match & active0.unsqueeze(1))
        ).any(dim=1) & ~expected_completed

        expected_task_candidate = task0.detach().clone().contiguous()
        expected_owner_candidate = owner0.detach().clone().contiguous()
        expected_task_candidate[expected_completed] = int(
            TaskLifecycleState.COMPLETED
        )
        expected_owner_candidate[expected_completed] = -1
        expected_task_candidate[expected_release] = int(
            TaskLifecycleState.AVAILABLE
        )
        expected_owner_candidate[expected_release] = -1
        expected_team = (
            expected_task_candidate != int(TaskLifecycleState.COMPLETED)
        ) & expected_updated_failed.all(dim=1)
        expected_task1 = expected_task_candidate.detach().clone().contiguous()
        expected_owner1 = expected_owner_candidate.detach().clone().contiguous()
        expected_task1[expected_team] = int(TaskLifecycleState.TEAM_INFEASIBLE)
        expected_owner1[expected_team] = -1

        expected_active1 = _enum_mask(expected_task1, _ACTIVE_TASK_STATES)
        expected_owner_match1 = expected_owner1.unsqueeze(1) == robot_ids
        expected_owned_count1 = (
            expected_active1.unsqueeze(1) & expected_owner_match1
        ).sum(dim=2)
        expected_eligible_work = (
            (expected_task1 == int(TaskLifecycleState.AVAILABLE)).unsqueeze(1)
            & (expected_owner1 == -1).unsqueeze(1)
            & ~expected_updated_failed
        ).any(dim=2)
        expected_unavailable_after = unavailable | (
            (robot0 == int(RobotLifecycleState.UNAVAILABLE)) & ~recovered
        )
        expected_robot1 = torch.full_like(
            robot0,
            int(RobotLifecycleState.WAITING_FOR_TASK),
        )
        expected_robot1[expected_eligible_work] = int(
            RobotLifecycleState.NEEDS_ASSIGNMENT
        )
        expected_robot1[expected_owned_count1 == 1] = int(
            RobotLifecycleState.EXECUTING
        )
        expected_robot1[expected_unavailable_after] = int(
            RobotLifecycleState.UNAVAILABLE
        )
        equations = (
            (candidate.completed_tasks, expected_completed, "completed_tasks"),
            (candidate.released_tasks, expected_release, "released_tasks"),
            (candidate.new_failed_pairs, expected_new_failed, "new_failed_pairs"),
            (candidate.prior_failed_pairs, failed0, "prior_failed_pairs"),
            (
                candidate.updated_failed_pairs,
                expected_updated_failed,
                "updated_failed_pairs",
            ),
            (
                candidate.updated_task_state,
                expected_task1,
                "updated_task_state",
            ),
            (
                candidate.updated_ownership,
                expected_owner1,
                "updated_ownership",
            ),
            (
                candidate.updated_robot_state,
                expected_robot1,
                "updated_robot_state",
            ),
            (
                candidate.updated_completion_count,
                count0 + completion.to(dtype=torch.int64).sum(dim=2),
                "updated_completion_count",
            ),
        )
        for observed, expected, field_name in equations:
            if not torch.equal(observed, expected):
                raise LifecycleAuthorityRuntimeError(
                    "candidate differs from the frozen B0 derivation equation",
                    failure_code="candidate_equation",
                    stage="authority_candidate_prevalidation",
                    field_name=field_name,
                    expected="exact derived tensor",
                    actual="tensor values differ",
                )
        if bool((candidate.completed_tasks & candidate.released_tasks).any().item()):
            raise LifecycleAuthorityRuntimeError(
                "completion and release result bits must be disjoint",
                failure_code="completion_release_disjoint",
                stage="authority_candidate_prevalidation",
                expected=False,
                actual=True,
            )
        team_equation = (
            candidate.updated_task_state != int(TaskLifecycleState.COMPLETED)
        ) & candidate.updated_failed_pairs.all(dim=1)
        if not torch.equal(
            candidate.updated_task_state == int(TaskLifecycleState.TEAM_INFEASIBLE),
            team_equation,
        ):
            raise LifecycleAuthorityRuntimeError(
                "candidate task state violates the TEAM_INFEASIBLE equation",
                failure_code="candidate_team_equation",
                stage="authority_candidate_prevalidation",
                expected="task != COMPLETED and all updated failed pairs",
                actual="tensor values differ",
            )
        expected_new_team = expected_team & (
            task0 != int(TaskLifecycleState.TEAM_INFEASIBLE)
        )
        if not torch.equal(candidate.new_team_infeasible_tasks, expected_new_team):
            raise LifecycleAuthorityRuntimeError(
                "candidate new TEAM edge differs from the exact state edge",
                failure_code="candidate_new_team",
                stage="authority_candidate_prevalidation",
                expected="exact TEAM state edge",
                actual="tensor values differ",
            )

        all_completed = (
            candidate.updated_task_state == int(TaskLifecycleState.COMPLETED)
        ).all(dim=1)
        all_terminal = _enum_mask(
            candidate.updated_task_state,
            _TERMINAL_TASK_STATES,
        ).all(dim=1)
        expected_reason = torch.full_like(
            candidate.termination_reason,
            int(TerminationReason.NONE),
        )
        expected_reason[facts_values["time_limit_reached"]] = int(
            TerminationReason.TIME_LIMIT
        )
        expected_reason[all_terminal & ~all_completed] = int(
            TerminationReason.NO_FEASIBLE_TASKS_REMAIN
        )
        expected_reason[all_completed] = int(
            TerminationReason.ALL_TASKS_COMPLETED
        )
        if not torch.equal(candidate.termination_reason, expected_reason):
            raise LifecycleAuthorityRuntimeError(
                "candidate termination reason violates the exact priority",
                failure_code="termination_priority",
                stage="authority_candidate_prevalidation",
                expected="ALL_COMPLETED > NO_FEASIBLE > TIME_LIMIT > NONE",
                actual="tensor values differ",
            )
        invalid_truncation = facts_values["physical_truncated"] & ~facts_values[
            "time_limit_reached"
        ]
        index = _first_true(invalid_truncation)
        if index is not None:
            row = index[0]
            raise LifecycleAuthorityRuntimeError(
                "non-time-limit physical truncation is unsupported",
                failure_code="unmappable_physical_truncation",
                stage="authority_candidate_prevalidation",
                env_id=int(env_id[row].item()),
                expected=True,
                actual=False,
            )
        task_terminal_reason = (
            (candidate.termination_reason == int(TerminationReason.ALL_TASKS_COMPLETED))
            | (
                candidate.termination_reason
                == int(TerminationReason.NO_FEASIBLE_TASKS_REMAIN)
            )
        )
        invalid_termination = facts_values["physical_terminated"] & ~task_terminal_reason
        index = _first_true(invalid_termination)
        if index is not None:
            row = index[0]
            raise LifecycleAuthorityRuntimeError(
                "physical termination is not mapped by final task state",
                failure_code="unmappable_physical_termination",
                stage="authority_candidate_prevalidation",
                env_id=int(env_id[row].item()),
                expected=(
                    int(TerminationReason.ALL_TASKS_COMPLETED),
                    int(TerminationReason.NO_FEASIBLE_TASKS_REMAIN),
                ),
                actual=int(candidate.termination_reason[row].item()),
            )

        events = validate_lifecycle_event_records(candidate.lifecycle_events)
        expected_events: dict[
            tuple[int, LifecycleEventType, int, int],
            tuple[
                LifecycleCausalSource,
                TaskLifecycleEventPayload
                | RobotLifecycleEventPayload
                | PairFailureEventPayload,
                int,
                int,
                int,
            ],
        ] = {}
        completion = facts_values["completion_signals"]
        unavailable = facts_values["robot_unavailable_signals"]
        for row in range(int(env_id.shape[0])):
            env_value = int(env_id[row].item())
            episode = int(facts_values["episode_generation"][row].item())
            transition = int(facts_values["transition_generation"][row].item())
            token = int(facts_values["consume_once_token"][row].item())
            for task in range(int(task0.shape[1])):
                if bool(candidate.completed_tasks[row, task].item()):
                    cause = int(
                        torch.nonzero(
                            completion[row, :, task],
                            as_tuple=False,
                        )[0].item()
                    )
                    expected_events[(
                        env_value,
                        LifecycleEventType.TASK_COMPLETED,
                        cause,
                        task,
                    )] = (
                        LifecycleCausalSource.EXECUTION_FACTS,
                        TaskLifecycleEventPayload(
                            task_id=task,
                            previous_task_state=int(task0[row, task].item()),
                            updated_task_state=int(TaskLifecycleState.COMPLETED),
                            cause_robot_id=cause,
                        ),
                        episode,
                        transition,
                        token,
                    )
                if bool(candidate.released_tasks[row, task].item()):
                    cause = int(owner0[row, task].item())
                    expected_events[(
                        env_value,
                        LifecycleEventType.TASK_RELEASED,
                        cause,
                        task,
                    )] = (
                        LifecycleCausalSource.EXECUTION_FACTS,
                        TaskLifecycleEventPayload(
                            task_id=task,
                            previous_task_state=int(task0[row, task].item()),
                            updated_task_state=int(TaskLifecycleState.AVAILABLE),
                            cause_robot_id=cause,
                        ),
                        episode,
                        transition,
                        token,
                    )
                if bool(candidate.new_team_infeasible_tasks[row, task].item()):
                    expected_events[(
                        env_value,
                        LifecycleEventType.TASK_BECAME_TEAM_INFEASIBLE,
                        -1,
                        task,
                    )] = (
                        LifecycleCausalSource.LIFECYCLE_DERIVATION,
                        TaskLifecycleEventPayload(
                            task_id=task,
                            previous_task_state=int(TaskLifecycleState.AVAILABLE),
                            updated_task_state=int(
                                TaskLifecycleState.TEAM_INFEASIBLE
                            ),
                            cause_robot_id=-1,
                        ),
                        episode,
                        transition,
                        token,
                    )
            for robot in range(int(robot0.shape[1])):
                for task in range(int(task0.shape[1])):
                    if bool(candidate.new_failed_pairs[row, robot, task].item()):
                        expected_events[(
                            env_value,
                            LifecycleEventType.TERMINAL_PAIR_FAILURE_RECORDED,
                            robot,
                            task,
                        )] = (
                            LifecycleCausalSource.EXECUTION_FACTS,
                            PairFailureEventPayload(
                                robot_id=robot,
                                task_id=task,
                                newly_recorded=True,
                            ),
                            episode,
                            transition,
                            token,
                        )
                if bool(unavailable[row, robot].item()):
                    expected_events[(
                        env_value,
                        LifecycleEventType.ROBOT_BECAME_UNAVAILABLE,
                        robot,
                        -1,
                    )] = (
                        LifecycleCausalSource.EXECUTION_FACTS,
                        RobotLifecycleEventPayload(
                            robot_id=robot,
                            previous_robot_state=int(robot0[row, robot].item()),
                            updated_robot_state=int(RobotLifecycleState.UNAVAILABLE),
                        ),
                        episode,
                        transition,
                        token,
                    )
                if bool(recovered[row, robot].item()):
                    expected_events[(
                        env_value,
                        LifecycleEventType.ROBOT_RECOVERED,
                        robot,
                        -1,
                    )] = (
                        LifecycleCausalSource.EXECUTION_FACTS,
                        RobotLifecycleEventPayload(
                            robot_id=robot,
                            previous_robot_state=int(RobotLifecycleState.UNAVAILABLE),
                            updated_robot_state=int(
                                candidate.updated_robot_state[row, robot].item()
                            ),
                        ),
                        episode,
                        transition,
                        token,
                    )
                if (
                    int(robot0[row, robot].item())
                    != int(RobotLifecycleState.NEEDS_ASSIGNMENT)
                    and int(candidate.updated_robot_state[row, robot].item())
                    == int(RobotLifecycleState.NEEDS_ASSIGNMENT)
                ):
                    expected_events[(
                        env_value,
                        LifecycleEventType.ROBOT_NEEDS_ASSIGNMENT,
                        robot,
                        -1,
                    )] = (
                        LifecycleCausalSource.LIFECYCLE_DERIVATION,
                        RobotLifecycleEventPayload(
                            robot_id=robot,
                            previous_robot_state=int(robot0[row, robot].item()),
                            updated_robot_state=int(
                                RobotLifecycleState.NEEDS_ASSIGNMENT
                            ),
                        ),
                        episode,
                        transition,
                        token,
                    )

        def event_key(
            event: LifecycleEventRecord,
        ) -> tuple[int, LifecycleEventType, int, int]:
            return (
                event.env_id,
                event.event_type,
                event.robot_id,
                event.task_id,
            )

        def total_key(
            key: tuple[int, LifecycleEventType, int, int],
        ) -> tuple[int, int, int, int]:
            event_env, event_type, robot, task = key
            rank = _EVENT_TYPE_RANK[event_type]
            if event_type in (
                LifecycleEventType.TASK_COMPLETED,
                LifecycleEventType.TASK_RELEASED,
                LifecycleEventType.TASK_BECAME_TEAM_INFEASIBLE,
            ):
                tie = (task, robot)
            elif event_type is LifecycleEventType.TERMINAL_PAIR_FAILURE_RECORDED:
                tie = (robot, task)
            else:
                tie = (robot, -1)
            return event_env, rank, tie[0], tie[1]

        actual_keys = tuple(event_key(event) for event in events)
        expected_keys = tuple(sorted(expected_events, key=total_key))
        if actual_keys != expected_keys:
            raise LifecycleAuthorityRuntimeError(
                "lifecycle event set/order differs from exact semantic edges",
                failure_code="event_semantic_equivalence",
                stage="authority_candidate_prevalidation",
                expected=expected_keys,
                actual=actual_keys,
            )
        by_env: dict[int, list[LifecycleEventRecord]] = {}
        for event in events:
            by_env.setdefault(event.env_id, []).append(event)
            expected_source, expected_payload, episode, transition, token = (
                expected_events[event_key(event)]
            )
            actual_binding = (
                event.causal_source,
                event.payload,
                event.episode_generation,
                event.transition_generation,
                event.facts_consume_token,
                event.authority_id,
            )
            expected_binding = (
                expected_source,
                expected_payload,
                episode,
                transition,
                token,
                self._authority_stamp.authority_id,
            )
            if actual_binding != expected_binding:
                raise LifecycleAuthorityRuntimeError(
                    "lifecycle event payload/source/generation binding is invalid",
                    failure_code="event_semantic_equivalence",
                    stage="authority_candidate_prevalidation",
                    env_id=event.env_id,
                    expected=expected_binding,
                    actual=actual_binding,
                )
        for event_env_id, rows in by_env.items():
            ordinals = tuple(event.ordinal for event in rows)
            if ordinals != tuple(range(len(rows))):
                raise LifecycleAuthorityRuntimeError(
                    "lifecycle event ordinals are not contiguous per environment",
                    failure_code="event_ordinal",
                    stage="authority_candidate_prevalidation",
                    env_id=event_env_id,
                    expected=tuple(range(len(rows))),
                    actual=ordinals,
                )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class PublishedLifecycleView:
    """B0-private immutable state/generation publication boundary."""

    store_version: int
    _state_snapshot: LifecycleStateSnapshot = field(repr=False)
    _episode_generation: torch.Tensor = field(repr=False)
    _transition_generation: torch.Tensor = field(repr=False)
    _terminated: torch.Tensor = field(repr=False)
    _truncated: torch.Tensor = field(repr=False)
    _result: LifecycleTransitionResult | None = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise LifecycleCoordinatorRuntimeError(
            "PublishedLifecycleView can only be installed by the coordinator",
            failure_code="published_view_factory_required",
            stage="publication",
            expected="LifecycleAuthorityTransactionCoordinator",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        state_snapshot: LifecycleStateSnapshot,
        episode_generation: torch.Tensor,
        transition_generation: torch.Tensor,
        result: LifecycleTransitionResult | None,
    ) -> "PublishedLifecycleView":
        if type(state_snapshot) is not LifecycleStateSnapshot:
            raise LifecycleCoordinatorRuntimeError(
                "published view requires an exact lifecycle snapshot",
                failure_code="published_snapshot_type",
                stage="publication_preparation",
                expected=LifecycleStateSnapshot,
                actual=type(state_snapshot),
            )
        env_count = state_snapshot.num_envs
        episode = _capture_tensor(
            episode_generation,
            field_name="episode_generation",
            shape=(env_count,),
            dtype=torch.int64,
            device=state_snapshot.device,
            error_type=LifecycleCoordinatorRuntimeError,
            stage="publication_preparation",
        )
        transition = _capture_tensor(
            transition_generation,
            field_name="transition_generation",
            shape=(env_count,),
            dtype=torch.int64,
            device=state_snapshot.device,
            error_type=LifecycleCoordinatorRuntimeError,
            stage="publication_preparation",
        )
        if bool((episode < -1).any().item()) or bool((transition < -1).any().item()):
            raise LifecycleCoordinatorRuntimeError(
                "published generations are below their internal initial sentinel",
                failure_code="published_generation_range",
                stage="publication_preparation",
                expected=">= -1",
                actual=(episode.tolist(), transition.tolist()),
            )
        reason = state_snapshot.termination_reason
        terminated = (
            (reason == int(TerminationReason.ALL_TASKS_COMPLETED))
            | (reason == int(TerminationReason.NO_FEASIBLE_TASKS_REMAIN))
        )
        truncated = reason == int(TerminationReason.TIME_LIMIT)

        if result is not None:
            if type(result) is not LifecycleTransitionResult:
                raise LifecycleCoordinatorRuntimeError(
                    "published result has the wrong canonical type",
                    failure_code="published_result_type",
                    stage="publication_preparation",
                    expected=LifecycleTransitionResult,
                    actual=type(result),
                )
            result.validate_finalized()
            comparisons = (
                (result.env_id, state_snapshot.env_id, "env_id"),
                (result.episode_generation, episode, "episode_generation"),
                (
                    result.transition_generation,
                    transition,
                    "transition_generation",
                ),
                (result.updated_task_state, state_snapshot.task_state, "task_state"),
                (
                    result.updated_robot_state,
                    state_snapshot.robot_state,
                    "robot_state",
                ),
                (result.updated_ownership, state_snapshot.ownership, "ownership"),
                (
                    result.updated_failed_pairs,
                    state_snapshot.cumulative_failed_pairs,
                    "cumulative_failed_pairs",
                ),
                (
                    result.termination_reason,
                    state_snapshot.termination_reason,
                    "termination_reason",
                ),
            )
            for observed, expected, field_name in comparisons:
                if not torch.equal(observed, expected):
                    raise LifecycleCoordinatorRuntimeError(
                        "published result differs from its state/generation view",
                        failure_code="published_result_binding",
                        stage="publication_preparation",
                        field_name=field_name,
                        expected="exact matching tensor",
                        actual="tensor values differ",
                    )

        instance = object.__new__(cls)
        object.__setattr__(instance, "store_version", state_snapshot.store_version)
        object.__setattr__(instance, "_state_snapshot", state_snapshot)
        object.__setattr__(instance, "_episode_generation", episode)
        object.__setattr__(instance, "_transition_generation", transition)
        object.__setattr__(
            instance,
            "_terminated",
            terminated.detach().clone().contiguous(),
        )
        object.__setattr__(
            instance,
            "_truncated",
            truncated.detach().clone().contiguous(),
        )
        object.__setattr__(instance, "_result", result)
        return instance

    @property
    def lifecycle_state(self) -> LifecycleStateSnapshot:
        return self._state_snapshot

    @property
    def env_id(self) -> torch.Tensor:
        return self._state_snapshot.env_id

    @property
    def episode_generation(self) -> torch.Tensor:
        return self._episode_generation.detach().clone().contiguous()

    @property
    def transition_generation(self) -> torch.Tensor:
        return self._transition_generation.detach().clone().contiguous()

    @property
    def terminated(self) -> torch.Tensor:
        return self._terminated.detach().clone().contiguous()

    @property
    def truncated(self) -> torch.Tensor:
        return self._truncated.detach().clone().contiguous()

    @property
    def result(self) -> LifecycleTransitionResult | None:
        return self._result


@dataclass(frozen=True, slots=True, eq=False)
class _TerminalTransitionKey:
    """Exact B0-private identity of one terminal transition row."""

    env_id: int
    episode_generation: int
    transition_generation: int

    def __post_init__(self) -> None:
        values = (self.env_id, self.episode_generation, self.transition_generation)
        if any(type(value) is not int or value < 0 for value in values):
            raise LifecycleCoordinatorRuntimeError(
                "terminal transition keys require nonnegative exact integers",
                failure_code="terminal_key",
                stage="terminal_key_validation",
                expected="three exact ints >= 0",
                actual=values,
            )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _TerminalHandoffArtifact:
    """Immutable/no-alias terminal evidence retained across episode rebuild."""

    _key: _TerminalTransitionKey = field(repr=False)
    _result: LifecycleTransitionResult = field(repr=False)
    _published_view: PublishedLifecycleView = field(repr=False)
    _coverage_after_transition: torch.Tensor = field(repr=False)
    _termination_reason: int
    _terminated: bool
    _truncated: bool
    _facts_consume_token: int
    _authority_receipt_id: int
    _lifecycle_events: tuple[object, ...] = field(repr=False)
    _optional_sidecar: object | None = field(default=None, repr=False)

    @classmethod
    def _create(
        cls,
        *,
        key: _TerminalTransitionKey,
        result: LifecycleTransitionResult,
        published_view: PublishedLifecycleView,
        domain_row: int,
        coverage_after_transition: torch.Tensor,
        optional_sidecar: object | None = None,
    ) -> "_TerminalHandoffArtifact":
        if type(key) is not _TerminalTransitionKey:
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff requires an exact transition key",
                failure_code="terminal_key_type",
                stage="terminal_handoff_prepare",
                expected=_TerminalTransitionKey,
                actual=type(key),
            )
        if type(result) is not LifecycleTransitionResult or type(published_view) is not PublishedLifecycleView:
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff requires canonical result and published view identities",
                failure_code="terminal_artifact_binding",
                stage="terminal_handoff_prepare",
                expected=(LifecycleTransitionResult, PublishedLifecycleView),
                actual=(type(result), type(published_view)),
            )
        if published_view.result is not result:
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff view does not retain the finalized result identity",
                failure_code="terminal_artifact_binding",
                stage="terminal_handoff_prepare",
                expected=id(result),
                actual=id(published_view.result),
            )
        if type(domain_row) is not int or not 0 <= domain_row < int(result.env_id.numel()):
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff row is outside the result domain",
                failure_code="terminal_row",
                stage="terminal_handoff_prepare",
                expected=f"0 <= row < {int(result.env_id.numel())}",
                actual=domain_row,
            )
        if (
            type(coverage_after_transition) is not torch.Tensor
            or coverage_after_transition.dtype is not torch.bool
            or coverage_after_transition.ndim != 1
            or coverage_after_transition.device != result.env_id.device
        ):
            raise LifecycleCoordinatorRuntimeError(
                "terminal coverage row must be a canonical bool tensor [N]",
                failure_code="terminal_coverage",
                stage="terminal_handoff_prepare",
                expected=(torch.bool, "[N]", result.env_id.device),
                actual=(
                    getattr(coverage_after_transition, "dtype", None),
                    getattr(coverage_after_transition, "shape", None),
                    getattr(coverage_after_transition, "device", None),
                ),
            )
        observed_key = (
            int(result.env_id[domain_row].item()),
            int(result.episode_generation[domain_row].item()),
            int(result.transition_generation[domain_row].item()),
        )
        if observed_key != (key.env_id, key.episode_generation, key.transition_generation):
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff key differs from the finalized result row",
                failure_code="terminal_artifact_binding",
                stage="terminal_handoff_prepare",
                expected=(key.env_id, key.episode_generation, key.transition_generation),
                actual=observed_key,
            )
        reason = int(result.termination_reason[domain_row].item())
        terminated = bool(published_view.terminated[domain_row].item())
        truncated = bool(published_view.truncated[domain_row].item())
        if reason == int(TerminationReason.NONE) or not (terminated or truncated):
            raise LifecycleCoordinatorRuntimeError(
                "terminal handoff may be created only for an authoritative done row",
                failure_code="terminal_done_binding",
                stage="terminal_handoff_prepare",
                expected="reason != NONE and terminated|truncated",
                actual=(reason, terminated, truncated),
            )
        if optional_sidecar is not None:
            from .assignment_event_terminal_critic_sidecar import (
                EventTerminalCriticSidecarV2,
            )

            if type(optional_sidecar) is not EventTerminalCriticSidecarV2:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal handoff sidecar has a noncanonical type",
                    failure_code="terminal_sidecar_type",
                    stage="terminal_handoff_prepare",
                    expected=EventTerminalCriticSidecarV2,
                    actual=type(optional_sidecar),
                )
            optional_sidecar._validate_artifact_binding(
                key=key,
                termination_reason=reason,
                terminated=terminated,
                truncated=truncated,
                published_store_version=published_view.store_version,
            )
        row_events = tuple(
            event for event in result.lifecycle_events if event.env_id == key.env_id
        )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_key", key)
        object.__setattr__(instance, "_result", result)
        object.__setattr__(instance, "_published_view", published_view)
        object.__setattr__(
            instance,
            "_coverage_after_transition",
            coverage_after_transition.detach().clone().contiguous(),
        )
        object.__setattr__(instance, "_termination_reason", reason)
        object.__setattr__(instance, "_terminated", terminated)
        object.__setattr__(instance, "_truncated", truncated)
        object.__setattr__(instance, "_facts_consume_token", int(result.facts_consume_token[domain_row].item()))
        object.__setattr__(instance, "_authority_receipt_id", int(result.authority_receipt_id[domain_row].item()))
        object.__setattr__(instance, "_lifecycle_events", row_events)
        object.__setattr__(instance, "_optional_sidecar", optional_sidecar)
        return instance

    @property
    def key(self) -> _TerminalTransitionKey:
        return self._key

    @property
    def result(self) -> LifecycleTransitionResult:
        return self._result

    @property
    def published_view(self) -> PublishedLifecycleView:
        return self._published_view

    @property
    def coverage_after_transition(self) -> torch.Tensor:
        return self._coverage_after_transition.detach().clone().contiguous()

    @property
    def termination_reason(self) -> int:
        return self._termination_reason

    @property
    def terminated(self) -> bool:
        return self._terminated

    @property
    def truncated(self) -> bool:
        return self._truncated

    @property
    def facts_consume_token(self) -> int:
        return self._facts_consume_token

    @property
    def authority_receipt_id(self) -> int:
        return self._authority_receipt_id

    @property
    def lifecycle_events(self) -> tuple[object, ...]:
        return self._lifecycle_events

    @property
    def optional_sidecar(self) -> object | None:
        return self._optional_sidecar


@dataclass(frozen=True, slots=True, eq=False)
class _TerminalObserverCapability:
    _store_identity: object = field(repr=False)


@dataclass(frozen=True, slots=True, eq=False)
class _TerminalConsumerCapability:
    _store_identity: object = field(repr=False)


@dataclass(frozen=True, slots=True, eq=False)
class _PreparedTerminalHandoffs:
    _store_identity: object = field(repr=False)
    _expected_slots_identity: object = field(repr=False)
    _replacement_slots: dict[int, _TerminalHandoffArtifact] = field(repr=False)
    keys: tuple[_TerminalTransitionKey, ...]


@dataclass(frozen=True, slots=True)
class _CoordinatorTestControl:
    """Private synchronization-only control; never receives runtime artifacts."""

    after_ledger_consume_reached: Event | None = field(default=None, repr=False)
    after_ledger_consume_release: Event | None = field(default=None, repr=False)
    after_state_swap_reached: Event | None = field(default=None, repr=False)
    after_state_swap_release: Event | None = field(default=None, repr=False)
    after_publication_reached: Event | None = field(default=None, repr=False)
    after_publication_release: Event | None = field(default=None, repr=False)
    read_before_lock: Event | None = field(default=None, repr=False)
    fail_terminal_install: bool = False

    def __post_init__(self) -> None:
        for reached_name, release_name in (
            ("after_ledger_consume_reached", "after_ledger_consume_release"),
            ("after_state_swap_reached", "after_state_swap_release"),
            ("after_publication_reached", "after_publication_release"),
        ):
            reached = getattr(self, reached_name)
            release = getattr(self, release_name)
            if (reached is None) != (release is None):
                raise LifecycleCoordinatorRuntimeError(
                    "test synchronization pause requires both Event endpoints",
                    failure_code="test_control_pair",
                    stage="coordinator_initialization",
                    field_name=f"{reached_name}/{release_name}",
                    expected="both None or both Event",
                    actual=(type(reached), type(release)),
                )
        for field_name in (
            "after_ledger_consume_reached",
            "after_ledger_consume_release",
            "after_state_swap_reached",
            "after_state_swap_release",
            "after_publication_reached",
            "after_publication_release",
            "read_before_lock",
        ):
            value = getattr(self, field_name)
            if value is not None and type(value) is not Event:
                raise LifecycleCoordinatorRuntimeError(
                    "test synchronization controls require exact threading.Event",
                    failure_code="test_control_type",
                    stage="coordinator_initialization",
                    field_name=field_name,
                    expected=Event,
                    actual=type(value),
                )
        if type(self.fail_terminal_install) is not bool:
            raise LifecycleCoordinatorRuntimeError(
                "terminal install failure control requires an exact bool",
                failure_code="test_control_type",
                stage="coordinator_initialization",
                field_name="fail_terminal_install",
                expected=bool,
                actual=type(self.fail_terminal_install),
            )


@dataclass(frozen=True, slots=True)
class _EpisodeRebuildTestControl:
    """Private reset synchronization/failure control; carries no artifact."""

    after_state_swap_reached: Event | None = field(default=None, repr=False)
    after_state_swap_release: Event | None = field(default=None, repr=False)
    after_clock_advance_reached: Event | None = field(default=None, repr=False)
    after_clock_advance_release: Event | None = field(default=None, repr=False)
    fail_clock_advance: bool = False
    fail_publication: bool = False
    stage_log: list[str] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for reached_name, release_name in (
            ("after_state_swap_reached", "after_state_swap_release"),
            ("after_clock_advance_reached", "after_clock_advance_release"),
        ):
            reached = getattr(self, reached_name)
            release = getattr(self, release_name)
            if (reached is None) != (release is None):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset test pause requires both Event endpoints",
                    failure_code="test_control_pair",
                    stage="reset_test_control",
                    field_name=f"{reached_name}/{release_name}",
                    expected="both None or both Event",
                    actual=(type(reached), type(release)),
                )
            if reached is not None and (
                type(reached) is not Event or type(release) is not Event
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset test pauses require exact threading.Event values",
                    failure_code="test_control_type",
                    stage="reset_test_control",
                    field_name=f"{reached_name}/{release_name}",
                    expected=Event,
                    actual=(type(reached), type(release)),
                )
        if type(self.fail_clock_advance) is not bool or type(self.fail_publication) is not bool:
            raise LifecycleEpisodeRebuildRuntimeError(
                "reset test failure controls require exact bool values",
                failure_code="test_control_type",
                stage="reset_test_control",
                expected=bool,
                actual=(type(self.fail_clock_advance), type(self.fail_publication)),
            )
        if self.stage_log is not None and type(self.stage_log) is not list:
            raise LifecycleEpisodeRebuildRuntimeError(
                "reset test stage_log must be an exact list",
                failure_code="test_control_type",
                stage="reset_test_control",
                field_name="stage_log",
                expected=list,
                actual=type(self.stage_log),
            )


@dataclass(frozen=True, slots=True)
class _InitialClaimTestControl:
    """Deterministic B1-only synchronization/failure injection."""

    before_state_swap_reached: Event | None = field(default=None, repr=False)
    before_state_swap_release: Event | None = field(default=None, repr=False)
    after_state_swap_reached: Event | None = field(default=None, repr=False)
    after_state_swap_release: Event | None = field(default=None, repr=False)
    fail_after_state_swap: bool = False

    def __post_init__(self) -> None:
        for reached_name, release_name in (
            ("before_state_swap_reached", "before_state_swap_release"),
            ("after_state_swap_reached", "after_state_swap_release"),
        ):
            reached = getattr(self, reached_name)
            release = getattr(self, release_name)
            if (reached is None) != (release is None) or (
                reached is not None
                and (type(reached) is not Event or type(release) is not Event)
            ):
                raise LifecycleCoordinatorRuntimeError(
                    "claim test pause requires two exact Event endpoints",
                    failure_code="test_control_pair",
                    stage="claim_test_control",
                    field_name=f"{reached_name}/{release_name}",
                    expected="both None or both exact Event",
                    actual=(type(reached), type(release)),
                )
        if type(self.fail_after_state_swap) is not bool:
            raise LifecycleCoordinatorRuntimeError(
                "claim failure injection flag must be an exact bool",
                failure_code="test_control_type",
                stage="claim_test_control",
                field_name="fail_after_state_swap",
                expected=bool,
                actual=type(self.fail_after_state_swap),
            )


class _EpisodeRebuildContext:
    """Narrow capability expressing only physical-reset completion."""

    __slots__ = (
        "_coordinator",
        "_inputs",
        "_test_control",
        "_entered",
        "_closed",
        "_signaled",
        "_prepared_swap",
        "_prepared_view",
        "_candidate",
        "_captured_clock_rows",
    )

    def __init__(
        self,
        coordinator: "LifecycleAuthorityTransactionCoordinator",
        inputs: _EpisodeRebuildInputs,
        test_control: _EpisodeRebuildTestControl | None,
    ) -> None:
        self._coordinator = coordinator
        self._inputs = inputs
        self._test_control = test_control
        self._entered = False
        self._closed = False
        self._signaled = False
        self._prepared_swap: _PreparedLifecycleSwap | None = None
        self._prepared_view: _EventRuntimeCurrentPublication | None = None
        self._candidate: _EpisodeRebuildCandidate | None = None
        self._captured_clock_rows: tuple[tuple[int, int, int, int | None], ...] = ()

    def __enter__(self) -> "_EpisodeRebuildContext":
        if self._entered or self._closed:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild context is single-entry",
                failure_code="rebuild_context_reuse",
                stage="reset_prepare",
                expected="fresh context",
                actual=(self._entered, self._closed),
            )
        self._coordinator._enter_episode_rebuild(self)
        self._entered = True
        return self

    def commit_physical_reset_complete(self) -> _EventRuntimeCurrentPublication:
        if not self._entered or self._closed or self._signaled:
            raise LifecycleEpisodeRebuildRuntimeError(
                "physical reset completion requires one active unsignaled context",
                failure_code="physical_reset_signal_state",
                stage="reset_success_tail",
                expected=(True, False, False),
                actual=(self._entered, self._closed, self._signaled),
            )
        self._signaled = True
        return self._coordinator._commit_episode_rebuild(self)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> bool:
        if self._entered and not self._closed:
            self._closed = True
            self._coordinator._exit_episode_rebuild(self)
        return False


class LifecycleAuthorityTransactionCoordinator:
    """Capability-limited ordering, commit, poison, and publication owner."""

    __slots__ = (
        "_profile",
        "_domain_identity",
        "_state_store",
        "_generation_clock",
        "_authority",
        "_claim_deriver",
        "_ledger",
        "_result_factory",
        "_writer_capability",
        "_publication_lock",
        "_published_view",
        "_publication_factory_capability",
        "_next_publication_serial",
        "_claim_factory_capability",
        "_next_request_token",
        "_active_claim_contexts",
        "_consumed_claim_token_intervals",
        "_poisoned",
        "_poison_cause",
        "_test_control",
        "_initial_claim_test_control",
        "_terminal_store_identity",
        "_terminal_slots",
        "_terminal_consumer_capability",
        "_terminal_consumer_issued",
    )

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
        *,
        state_store: LifecycleStateStore,
        generation_clock: LifecycleGenerationClock,
        _test_control: _CoordinatorTestControl | None = None,
        _initial_claim_test_control: _InitialClaimTestControl | None = None,
    ) -> None:
        canonical_profile = _require_event_profile(
            profile,
            component="LifecycleAuthorityTransactionCoordinator",
        )
        if type(state_store) is not LifecycleStateStore:
            raise LifecycleCoordinatorRuntimeError(
                "coordinator requires an exact LifecycleStateStore",
                failure_code="state_store_type",
                stage="coordinator_initialization",
                expected=LifecycleStateStore,
                actual=type(state_store),
            )
        if type(generation_clock) is not LifecycleGenerationClock:
            raise LifecycleCoordinatorRuntimeError(
                "coordinator requires an exact retained LifecycleGenerationClock",
                failure_code="generation_clock_type",
                stage="coordinator_initialization",
                expected=LifecycleGenerationClock,
                actual=type(generation_clock),
            )
        if state_store._profile is not canonical_profile:
            raise LifecycleCoordinatorRuntimeError(
                "state store did not retain the coordinator profile object",
                failure_code="profile_identity",
                stage="coordinator_initialization",
                expected=id(canonical_profile),
                actual=id(state_store._profile),
            )
        if generation_clock._profile is not canonical_profile:
            raise LifecycleCoordinatorRuntimeError(
                "generation clock did not retain the coordinator profile object",
                failure_code="profile_identity",
                stage="coordinator_initialization",
                expected=id(canonical_profile),
                actual=id(generation_clock._profile),
            )
        store_env_ids = tuple(
            int(value) for value in state_store._env_id.detach().cpu().tolist()
        )
        if (
            state_store._device != generation_clock._device
            or store_env_ids != generation_clock._env_ids
        ):
            raise LifecycleCoordinatorRuntimeError(
                "state store and generation clock domains differ",
                failure_code="domain_identity",
                stage="coordinator_initialization",
                expected=(state_store._device, store_env_ids),
                actual=(generation_clock._device, generation_clock._env_ids),
            )
        if _test_control is not None and type(_test_control) is not _CoordinatorTestControl:
            raise LifecycleCoordinatorRuntimeError(
                "private coordinator test control has the wrong exact type",
                failure_code="test_control_type",
                stage="coordinator_initialization",
                expected=_CoordinatorTestControl,
                actual=type(_test_control),
            )
        if (
            _initial_claim_test_control is not None
            and type(_initial_claim_test_control) is not _InitialClaimTestControl
        ):
            raise LifecycleCoordinatorRuntimeError(
                "private initial-claim test control has the wrong exact type",
                failure_code="test_control_type",
                stage="coordinator_initialization",
                expected=_InitialClaimTestControl,
                actual=type(_initial_claim_test_control),
            )

        authority = LifecycleAuthorityRuntime(canonical_profile)
        claim_deriver = InitialClaimDeriver(canonical_profile)
        ledger = TransitionConsumeLedger(
            authority_stamp=authority._authority_stamp,
        )
        result_factory = LifecycleTransitionResultFactory(
            ledger=ledger,
            authority_stamp=ledger.authority_stamp,
        )
        initial_snapshot = state_store.snapshot()
        clock_rows = generation_clock.snapshot(state_store._env_id)
        initial_episode = torch.tensor(
            tuple(row.episode_generation for row in clock_rows),
            dtype=torch.int64,
            device=state_store._device,
        )
        initial_transition = torch.tensor(
            tuple(row.transition_generation for row in clock_rows),
            dtype=torch.int64,
            device=state_store._device,
        )
        initial_view = PublishedLifecycleView._create(
            state_snapshot=initial_snapshot,
            episode_generation=initial_episode,
            transition_generation=initial_transition,
            result=None,
        )
        domain_identity = object()
        publication_factory_capability = object()
        initial_identity = _CurrentPublicationIdentity._create(
            serial=0,
            domain_identity=domain_identity,
            factory_capability=publication_factory_capability,
        )
        initial_provenance = tuple(
            _CurrentPublicationProvenance._create(
                kind=_CurrentPublicationProvenanceKind.PREBOOTSTRAP,
                lifecycle_result=None,
                assignment_artifact=None,
                immediate_predecessor_identity=None,
                root_kind=_CurrentPublicationProvenanceKind.PREBOOTSTRAP,
                root_publication_identity=initial_identity,
                root_lifecycle_result=None,
                factory_capability=publication_factory_capability,
            )
            for _ in range(initial_snapshot.num_envs)
        )
        initial_publication = _EventRuntimeCurrentPublication._create(
            lifecycle_view=initial_view,
            publication_identity=initial_identity,
            provenance=initial_provenance,
            factory_capability=publication_factory_capability,
        )
        writer_capability = state_store._claim_lifecycle_writer()

        self._profile = canonical_profile
        self._domain_identity = domain_identity
        self._state_store = state_store
        self._generation_clock = generation_clock
        self._authority = authority
        self._claim_deriver = claim_deriver
        self._ledger = ledger
        self._result_factory = result_factory
        self._writer_capability = writer_capability
        self._publication_lock = Lock()
        self._published_view = initial_publication
        self._publication_factory_capability = publication_factory_capability
        self._next_publication_serial = 1
        self._claim_factory_capability = object()
        self._next_request_token = 0
        self._active_claim_contexts: dict[int, _InitialClaimRequestContext] = {}
        self._consumed_claim_token_intervals: tuple[tuple[int, int], ...] = ()
        self._poisoned = False
        self._poison_cause: str | None = None
        self._test_control = _test_control
        self._initial_claim_test_control = _initial_claim_test_control
        self._terminal_store_identity = object()
        self._terminal_slots: dict[int, _TerminalHandoffArtifact] = {}
        self._terminal_consumer_capability = _TerminalConsumerCapability(
            self._terminal_store_identity
        )
        self._terminal_consumer_issued = False

    @property
    def poisoned(self) -> bool:
        with self._publication_lock:
            return self._poisoned

    def read_published_view(self) -> _EventRuntimeCurrentPublication:
        """Return only the sole coherent old/old or new/new P2 publication."""

        control = self._test_control
        if control is not None and control.read_before_lock is not None:
            control.read_before_lock.set()
        with self._publication_lock:
            self._require_not_poisoned(stage="published_read")
            return self._published_view

    def _allocate_publication_identity(self) -> _CurrentPublicationIdentity:
        serial = self._next_publication_serial
        if serial > _INT64_MAX:
            raise LifecycleCoordinatorRuntimeError(
                "current-publication identity space is exhausted",
                failure_code="publication_identity_overflow",
                stage="publication_preparation",
                expected=f"<= {_INT64_MAX}",
                actual=serial,
            )
        self._next_publication_serial = serial + 1
        return _CurrentPublicationIdentity._create(
            serial=serial,
            domain_identity=self._domain_identity,
            factory_capability=self._publication_factory_capability,
        )

    def _prepare_reset_publication(
        self,
        *,
        lifecycle_view: PublishedLifecycleView,
        selected_rows: tuple[int, ...],
    ) -> _EventRuntimeCurrentPublication:
        identity = self._allocate_publication_identity()
        selected = set(selected_rows)
        provenance = tuple(
            (
                _CurrentPublicationProvenance._create(
                    kind=_CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
                    lifecycle_result=None,
                    assignment_artifact=None,
                    immediate_predecessor_identity=None,
                    root_kind=_CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
                    root_publication_identity=identity,
                    root_lifecycle_result=None,
                    factory_capability=self._publication_factory_capability,
                )
                if row in selected
                else self._published_view.provenance[row]
            )
            for row in range(self._state_store._num_envs)
        )
        return _EventRuntimeCurrentPublication._create(
            lifecycle_view=lifecycle_view,
            publication_identity=identity,
            provenance=provenance,
            factory_capability=self._publication_factory_capability,
        )

    def _prepare_lifecycle_publication(
        self,
        *,
        lifecycle_view: PublishedLifecycleView,
        result: LifecycleTransitionResult,
    ) -> _EventRuntimeCurrentPublication:
        identity = self._allocate_publication_identity()
        provenance = tuple(
            _CurrentPublicationProvenance._create(
                kind=_CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION,
                lifecycle_result=result,
                assignment_artifact=None,
                immediate_predecessor_identity=None,
                root_kind=_CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION,
                root_publication_identity=identity,
                root_lifecycle_result=result,
                factory_capability=self._publication_factory_capability,
            )
            for _ in range(self._state_store._num_envs)
        )
        return _EventRuntimeCurrentPublication._create(
            lifecycle_view=lifecycle_view,
            publication_identity=identity,
            provenance=provenance,
            factory_capability=self._publication_factory_capability,
        )

    def _prepare_assignment_publication(
        self,
        *,
        lifecycle_view: PublishedLifecycleView,
        artifact: EffectiveAssignmentCommitArtifact,
        selected_rows: tuple[int, ...],
    ) -> _EventRuntimeCurrentPublication:
        identity = self._allocate_publication_identity()
        selected = set(selected_rows)
        source = self._published_view
        provenance = tuple(
            (
                _CurrentPublicationProvenance._create(
                    kind=_CurrentPublicationProvenanceKind.ASSIGNMENT_COMMIT,
                    lifecycle_result=None,
                    assignment_artifact=artifact,
                    immediate_predecessor_identity=source.publication_identity,
                    root_kind=source.provenance[row].root_kind,
                    root_publication_identity=(
                        source.provenance[row].root_publication_identity
                    ),
                    root_lifecycle_result=source.provenance[row].root_lifecycle_result,
                    factory_capability=self._publication_factory_capability,
                )
                if row in selected
                else source.provenance[row]
            )
            for row in range(self._state_store._num_envs)
        )
        return _EventRuntimeCurrentPublication._create(
            lifecycle_view=lifecycle_view,
            publication_identity=identity,
            provenance=provenance,
            factory_capability=self._publication_factory_capability,
        )

    def _capture_execution_prestate(
        self,
        *,
        env_ids: torch.Tensor,
        transition_contexts: tuple[TransitionGenerationContext, ...],
    ) -> LifecycleStateSnapshot:
        """Capture the exact transaction prestate for the private I3 adapter.

        The retained all-row transition reservations prevent a supported reset
        or competing transition from changing this state before ``transact``.
        The public coordinator surface remains unchanged, and the environment
        never receives this snapshot capability.
        """

        with self._publication_lock:
            self._require_not_poisoned(stage="execution_prestate_capture")
            snapshot = self._state_store._snapshot_for_lifecycle(
                writer_capability=self._writer_capability,
            )
            self._state_store._validate_expected_snapshot(snapshot)
            if not torch.equal(env_ids, snapshot._env_id):
                raise LifecycleCoordinatorRuntimeError(
                    "execution prestate capture requires the exact full domain",
                    failure_code="execution_prestate_domain",
                    stage="execution_prestate_capture",
                    expected=tuple(int(value) for value in snapshot._env_id.cpu().tolist()),
                    actual=(
                        tuple(int(value) for value in env_ids.detach().cpu().tolist())
                        if type(env_ids) is torch.Tensor
                        and env_ids.layout is torch.strided
                        and env_ids.ndim == 1
                        else type(env_ids)
                    ),
                )
            self._validate_clock_contexts(env_ids, transition_contexts)
            return snapshot

    def _episode_rebuild(
        self,
        inputs: _EpisodeRebuildInputs,
        *,
        _test_control: _EpisodeRebuildTestControl | None = None,
    ) -> _EpisodeRebuildContext:
        """Issue the B0-private physical-reset-completion capability."""

        if type(inputs) is not _EpisodeRebuildInputs:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild requires exact B0-private reset inputs",
                failure_code="reset_input_type",
                stage="reset_prepare",
                expected=_EpisodeRebuildInputs,
                actual=type(inputs),
            )
        if _test_control is not None and type(_test_control) is not _EpisodeRebuildTestControl:
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild test control has the wrong exact type",
                failure_code="test_control_type",
                stage="reset_prepare",
                expected=_EpisodeRebuildTestControl,
                actual=type(_test_control),
            )
        return _EpisodeRebuildContext(self, inputs, _test_control)

    def _enter_episode_rebuild(self, context: _EpisodeRebuildContext) -> None:
        self._publication_lock.acquire()
        try:
            self._require_not_poisoned(stage="reset_prepare")
            inputs = context._inputs
            if inputs._profile is not self._profile:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "episode rebuild inputs did not retain the coordinator profile",
                    failure_code="profile_identity",
                    stage="reset_prepare",
                    expected=id(self._profile),
                    actual=id(inputs._profile),
                )
            if inputs._device != self._state_store._device:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "episode rebuild input device differs from the coordinator domain",
                    failure_code="device",
                    stage="reset_prepare",
                    expected=self._state_store._device,
                    actual=inputs._device,
                )

            snapshot = self._state_store._snapshot_for_lifecycle(
                writer_capability=self._writer_capability,
            )
            self._state_store._validate_expected_snapshot(snapshot)
            clock_rows = self._capture_clock_rows()
            self._validate_current_publication(snapshot, clock_rows)

            selected_values, selected_rows = (
                self._generation_clock._normalize_selected_env_ids(
                    inputs._selected_env_ids
                )
            )
            if inputs._initial_task_state.shape != (
                len(selected_rows),
                snapshot.num_tasks,
            ) or inputs._initial_robot_state.shape != (
                len(selected_rows),
                snapshot.num_robots,
            ) or inputs._initial_ownership.shape != (
                len(selected_rows),
                snapshot.num_tasks,
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "episode rebuild input dimensions differ from the state domain",
                    failure_code="domain_shape",
                    stage="reset_prepare",
                    expected=(len(selected_rows), snapshot.num_robots, snapshot.num_tasks),
                    actual=(
                        tuple(inputs._initial_task_state.shape),
                        tuple(inputs._initial_robot_state.shape),
                        tuple(inputs._initial_ownership.shape),
                    ),
                )
            if not bool(
                (inputs._initial_task_state == int(TaskLifecycleState.AVAILABLE))
                .all()
                .item()
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset task rows must be canonical AVAILABLE initialization",
                    failure_code="reset_task_state",
                    stage="reset_prepare",
                    expected=int(TaskLifecycleState.AVAILABLE),
                    actual="non-AVAILABLE reset row",
                )
            if not bool(
                (inputs._initial_robot_state == int(RobotLifecycleState.NEEDS_ASSIGNMENT))
                .all()
                .item()
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset robot rows must be canonical healthy NEEDS_ASSIGNMENT initialization",
                    failure_code="reset_robot_state",
                    stage="reset_prepare",
                    expected=int(RobotLifecycleState.NEEDS_ASSIGNMENT),
                    actual="non-NEEDS_ASSIGNMENT reset row",
                )
            if not bool((inputs._initial_ownership == -1).all().item()):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset ownership rows must be canonical unowned initialization",
                    failure_code="reset_ownership",
                    stage="reset_prepare",
                    expected=-1,
                    actual="owned reset row",
                )

            for selected_value, selected_row in zip(
                selected_values,
                selected_rows,
                strict=True,
            ):
                outstanding = clock_rows[selected_row][3]
                if outstanding is not None:
                    raise LifecycleEpisodeRebuildRuntimeError(
                        "selected reset row has an outstanding transition candidate",
                        failure_code="outstanding_transition",
                        stage="reset_prepare",
                        env_id=selected_value,
                        expected=None,
                        actual=outstanding,
                    )

            task_state = snapshot._task_state.detach().clone().contiguous()
            robot_state = snapshot._robot_state.detach().clone().contiguous()
            ownership = snapshot._ownership.detach().clone().contiguous()
            failed_pairs = (
                snapshot._cumulative_failed_pairs.detach().clone().contiguous()
            )
            completion_count = snapshot._completion_count.detach().clone().contiguous()
            reason = snapshot._termination_reason.detach().clone().contiguous()
            current_lifecycle_view = self._published_view.lifecycle_view
            episode = current_lifecycle_view._episode_generation.detach().clone().contiguous()
            transition = (
                current_lifecycle_view._transition_generation.detach().clone().contiguous()
            )
            for input_row, domain_row in enumerate(selected_rows):
                task_state[domain_row] = inputs._initial_task_state[input_row]
                robot_state[domain_row] = inputs._initial_robot_state[input_row]
                ownership[domain_row] = inputs._initial_ownership[input_row]
                failed_pairs[domain_row].zero_()
                completion_count[domain_row].zero_()
                reason[domain_row] = int(TerminationReason.NONE)
                current_episode = int(episode[domain_row].item())
                if current_episode == _INT64_MAX:
                    raise LifecycleEpisodeRebuildRuntimeError(
                        "episode generation space is exhausted",
                        failure_code="episode_overflow",
                        stage="reset_prepare",
                        env_id=selected_values[input_row],
                        expected=f"< {_INT64_MAX}",
                        actual=current_episode,
                    )
                episode[domain_row] = current_episode + 1

            full_env_id = snapshot._env_id.detach().clone().contiguous()
            _validate_state_invariants(
                env_id=full_env_id,
                task_state=task_state,
                robot_state=robot_state,
                ownership=ownership,
                cumulative_failed_pairs=failed_pairs,
                completion_count=completion_count,
                termination_reason=reason,
                error_type=LifecycleEpisodeRebuildRuntimeError,
                stage="reset_candidate_validation",
            )
            candidate = _EpisodeRebuildCandidate(
                _store_identity=snapshot._store_identity,
                store_version=snapshot.store_version,
                selected_env_ids=selected_values,
                selected_rows=selected_rows,
                task_state=task_state,
                robot_state=robot_state,
                ownership=ownership,
                cumulative_failed_pairs=failed_pairs,
                completion_count=completion_count,
                termination_reason=reason,
                expected_episode_generation=episode,
                expected_transition_generation=transition,
            )
            prepared_swap = self._state_store._prepare_episode_rebuild_swap(
                snapshot=snapshot,
                candidate=candidate,
                writer_capability=self._writer_capability,
            )
            prepared_lifecycle_view = PublishedLifecycleView._create(
                state_snapshot=prepared_swap._replacement_snapshot,
                episode_generation=episode,
                transition_generation=transition,
                result=None,
            )
            prepared_view = self._prepare_reset_publication(
                lifecycle_view=prepared_lifecycle_view,
                selected_rows=candidate.selected_rows,
            )
            if bool(prepared_view.terminated.any().item()) or bool(
                prepared_view.truncated.any().item()
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "reset publication must be nonterminal and nontruncated",
                    failure_code="reset_done_projection",
                    stage="reset_prepare",
                    expected=(False, False),
                    actual=(prepared_view.terminated.tolist(), prepared_view.truncated.tolist()),
                )

            self._state_store._validate_expected_snapshot(snapshot)
            revalidated_clock_rows = self._capture_clock_rows()
            if revalidated_clock_rows != clock_rows:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "generation clock changed during reset preparation",
                    failure_code="clock_revalidation",
                    stage="reset_prepare",
                    expected=clock_rows,
                    actual=revalidated_clock_rows,
                )
            self._validate_current_publication(snapshot, revalidated_clock_rows)
            context._candidate = candidate
            context._prepared_swap = prepared_swap
            context._prepared_view = prepared_view
            context._captured_clock_rows = clock_rows
        except Exception:
            self._publication_lock.release()
            raise

    def _commit_episode_rebuild(
        self,
        context: _EpisodeRebuildContext,
    ) -> _EventRuntimeCurrentPublication:
        candidate = context._candidate
        prepared_swap = context._prepared_swap
        prepared_view = context._prepared_view
        if (
            type(candidate) is not _EpisodeRebuildCandidate
            or type(prepared_swap) is not _PreparedLifecycleSwap
            or type(prepared_view) is not _EventRuntimeCurrentPublication
        ):
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild success tail lacks a complete prepared candidate",
                failure_code="reset_preparation_missing",
                stage="reset_success_tail",
                expected="candidate/swap/view",
                actual=(type(candidate), type(prepared_swap), type(prepared_view)),
            )
        stage = "reset_state_swap"
        try:
            current_snapshot = self._state_store._snapshot_for_lifecycle(
                writer_capability=self._writer_capability,
            )
            self._state_store._validate_expected_snapshot(current_snapshot)
            if (
                current_snapshot.store_version != candidate.store_version
                or self._capture_clock_rows() != context._captured_clock_rows
            ):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "state or generation identity changed before reset success tail",
                    failure_code="reset_revalidation",
                    stage=stage,
                    expected=(candidate.store_version, context._captured_clock_rows),
                    actual=(current_snapshot.store_version, self._capture_clock_rows()),
                )
            committed = self._state_store._commit_prepared_lifecycle_swap(
                prepared_swap,
                writer_capability=self._writer_capability,
            )
            if committed is not prepared_swap._replacement_snapshot:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "StateStore returned an unexpected reset snapshot",
                    failure_code="reset_state_swap_identity",
                    stage=stage,
                    expected=id(prepared_swap._replacement_snapshot),
                    actual=id(committed),
                )
            self._record_reset_stage(context._test_control, "state_swap")
            self._pause_for_test(
                reached=(None if context._test_control is None else context._test_control.after_state_swap_reached),
                release=(None if context._test_control is None else context._test_control.after_state_swap_release),
                stage="reset_after_state_swap",
            )

            stage = "reset_clock_advance"
            if context._test_control is not None and context._test_control.fail_clock_advance:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "injected episode clock advance failure",
                    failure_code="injected_clock_advance_failure",
                    stage=stage,
                )
            selected_tensor = torch.tensor(
                candidate.selected_env_ids,
                dtype=torch.int64,
                device=self._state_store._device,
            )
            advanced_rows = self._generation_clock.advance_episode(selected_tensor)
            expected_selected = tuple(
                (
                    candidate.selected_env_ids[input_row],
                    int(candidate.expected_episode_generation[domain_row].item()),
                    int(candidate.expected_transition_generation[domain_row].item()),
                    None,
                )
                for input_row, domain_row in enumerate(candidate.selected_rows)
            )
            actual_selected = tuple(
                (
                    row.env_id,
                    row.episode_generation,
                    row.transition_generation,
                    row.outstanding_transition_generation,
                )
                for row in advanced_rows
            )
            if actual_selected != expected_selected:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "episode clock advance differs from the prepared reset vector",
                    failure_code="reset_clock_binding",
                    stage=stage,
                    expected=expected_selected,
                    actual=actual_selected,
                )
            full_clock_rows = self._capture_clock_rows()
            selected_row_set = set(candidate.selected_rows)
            expected_full = tuple(
                (
                    int(self._state_store._env_id[row].item()),
                    int(candidate.expected_episode_generation[row].item()),
                    int(candidate.expected_transition_generation[row].item()),
                    (
                        None
                        if row in selected_row_set
                        else context._captured_clock_rows[row][3]
                    ),
                )
                for row in range(self._state_store._num_envs)
            )
            if full_clock_rows != expected_full:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "full generation clock differs from the prepared reset publication",
                    failure_code="reset_clock_binding",
                    stage=stage,
                    expected=expected_full,
                    actual=full_clock_rows,
                )
            self._record_reset_stage(context._test_control, "advance_episode")
            self._pause_for_test(
                reached=(None if context._test_control is None else context._test_control.after_clock_advance_reached),
                release=(None if context._test_control is None else context._test_control.after_clock_advance_release),
                stage="reset_after_clock_advance",
            )

            stage = "reset_publication"
            if context._test_control is not None and context._test_control.fail_publication:
                raise LifecycleEpisodeRebuildRuntimeError(
                    "injected reset publication failure",
                    failure_code="injected_publication_failure",
                    stage=stage,
                )
            self._published_view = prepared_view
            self._record_reset_stage(context._test_control, "publication")
            return prepared_view
        except Exception as exc:
            self._poisoned = True
            self._poison_cause = f"{stage}:{type(exc).__name__}:{exc}"
            raise LifecycleEpisodeRebuildRuntimeError(
                "episode rebuild failed after physical-reset completion; "
                "the coordinator is poisoned and requires teardown",
                failure_code="fatal_post_physical_reset_failure",
                stage=stage,
                expected="no-fail reset success tail",
                actual=type(exc).__name__,
            ) from exc

    def _exit_episode_rebuild(self, context: _EpisodeRebuildContext) -> None:
        self._publication_lock.release()

    def _capture_clock_rows(self) -> tuple[tuple[int, int, int, int | None], ...]:
        rows = self._generation_clock.snapshot(self._state_store._env_id)
        return tuple(
            (
                row.env_id,
                row.episode_generation,
                row.transition_generation,
                row.outstanding_transition_generation,
            )
            for row in rows
        )

    def _validate_current_publication(
        self,
        snapshot: LifecycleStateSnapshot,
        clock_rows: tuple[tuple[int, int, int, int | None], ...],
    ) -> None:
        view = self._published_view
        if (
            type(view) is not _EventRuntimeCurrentPublication
            or view.publication_identity._domain_identity is not self._domain_identity
            or view.publication_identity._factory_capability
            is not self._publication_factory_capability
            or len(view.provenance) != self._state_store._num_envs
        ):
            raise LifecycleEpisodeRebuildRuntimeError(
                "current P2 publication lacks the retained authority identity",
                failure_code="published_authority_binding",
                stage="reset_consistency_capture",
                expected="one coordinator-issued full-domain P2 publication",
                actual=type(view),
            )
        published_state = view.lifecycle_state
        if (
            published_state._store_identity is not snapshot._store_identity
            or view.store_version != snapshot.store_version
        ):
            raise LifecycleEpisodeRebuildRuntimeError(
                "published lifecycle state differs from the current StateStore identity/version",
                failure_code="published_store_binding",
                stage="reset_consistency_capture",
                expected=(id(snapshot._store_identity), snapshot.store_version),
                actual=(id(published_state._store_identity), view.store_version),
            )
        for observed, expected, field_name in (
            (published_state._task_state, snapshot._task_state, "task_state"),
            (published_state._robot_state, snapshot._robot_state, "robot_state"),
            (published_state._ownership, snapshot._ownership, "ownership"),
            (
                published_state._cumulative_failed_pairs,
                snapshot._cumulative_failed_pairs,
                "cumulative_failed_pairs",
            ),
            (published_state._completion_count, snapshot._completion_count, "completion_count"),
            (
                published_state._termination_reason,
                snapshot._termination_reason,
                "termination_reason",
            ),
        ):
            if not torch.equal(observed, expected):
                raise LifecycleEpisodeRebuildRuntimeError(
                    "published lifecycle state differs from the current StateStore",
                    failure_code="published_state_binding",
                    stage="reset_consistency_capture",
                    field_name=field_name,
                    expected="exact current state tensor",
                    actual="tensor values differ",
                )
        expected_episode = tuple(row[1] for row in clock_rows)
        expected_transition = tuple(row[2] for row in clock_rows)
        actual_episode = tuple(int(value) for value in view.episode_generation.cpu().tolist())
        actual_transition = tuple(
            int(value) for value in view.transition_generation.cpu().tolist()
        )
        if actual_episode != expected_episode or actual_transition != expected_transition:
            raise LifecycleEpisodeRebuildRuntimeError(
                "published generations differ from the retained generation clock",
                failure_code="published_generation_binding",
                stage="reset_consistency_capture",
                expected=(expected_episode, expected_transition),
                actual=(actual_episode, actual_transition),
            )

    @staticmethod
    def _record_reset_stage(
        control: _EpisodeRebuildTestControl | None,
        stage: str,
    ) -> None:
        if control is not None and control.stage_log is not None:
            control.stage_log.append(stage)

    def transact(
        self,
        *,
        facts: ExecutionTransitionFacts,
        transition_contexts: tuple[TransitionGenerationContext, ...],
    ) -> _EventRuntimeCurrentPublication:
        """Run the unchanged B0-2 transaction without an I4 terminal handoff."""

        return self._run_transaction(
            facts=facts,
            transition_contexts=transition_contexts,
            coverage_before_transition=None,
            pre_reset_critic_physical_snapshot=None,
        )

    def _transact_with_terminal_handoff(
        self,
        *,
        facts: ExecutionTransitionFacts,
        transition_contexts: tuple[TransitionGenerationContext, ...],
        coverage_before_transition: torch.Tensor,
        pre_reset_critic_physical_snapshot: object | None = None,
    ) -> _EventRuntimeCurrentPublication:
        """Private I4 extension installing terminal rows before lock release."""

        return self._run_transaction(
            facts=facts,
            transition_contexts=transition_contexts,
            coverage_before_transition=coverage_before_transition,
            pre_reset_critic_physical_snapshot=pre_reset_critic_physical_snapshot,
        )

    def _run_transaction(
        self,
        *,
        facts: ExecutionTransitionFacts,
        transition_contexts: tuple[TransitionGenerationContext, ...],
        coverage_before_transition: torch.Tensor | None,
        pre_reset_critic_physical_snapshot: object | None,
    ) -> _EventRuntimeCurrentPublication:
        """Run one full-batch consume/finalize/swap/commit/publication."""

        with self._publication_lock:
            self._require_not_poisoned(stage="transaction_start")
            receipt_issued = False
            stage = "prevalidation"
            try:
                state_snapshot = self._state_store._snapshot_for_lifecycle(
                    writer_capability=self._writer_capability,
                )
                self._state_store._validate_expected_snapshot(state_snapshot)
                validated_clock_rows = self._validate_clock_contexts(
                    facts.env_id,
                    transition_contexts,
                )
                candidate = self._authority.derive_candidate(
                    facts=facts,
                    state_snapshot=state_snapshot,
                    transition_contexts=transition_contexts,
                )
                if validated_clock_rows != candidate.context_rows:
                    raise LifecycleCoordinatorRuntimeError(
                        "clock reservations differ from the authority candidate",
                        failure_code="clock_candidate_binding",
                        stage="prevalidation",
                        expected=validated_clock_rows,
                        actual=candidate.context_rows,
                    )
                prepared_swap = self._state_store._prepare_lifecycle_swap(
                    snapshot=state_snapshot,
                    candidate=candidate,
                    writer_capability=self._writer_capability,
                )
                terminal_coverage_after = self._prevalidate_terminal_capacity(
                    candidate=candidate,
                    coverage_before_transition=coverage_before_transition,
                )
                self._prevalidate_terminal_critic_snapshot(
                    candidate=candidate,
                    physical_snapshot=pre_reset_critic_physical_snapshot,
                )

                # Final receipt-free revalidation under the outer publication
                # lock.  Every normal stale/semantic failure still occurs here.
                self._state_store._validate_expected_snapshot(state_snapshot)
                revalidated_clock_rows = self._validate_clock_contexts(
                    facts.env_id,
                    transition_contexts,
                )
                if revalidated_clock_rows != candidate.context_rows:
                    raise LifecycleCoordinatorRuntimeError(
                        "generation context changed during candidate preparation",
                        failure_code="clock_candidate_binding",
                        stage="prevalidation",
                        expected=candidate.context_rows,
                        actual=revalidated_clock_rows,
                    )

                expectations = tuple(
                    TransitionGenerationExpectation(
                        env_id=env_value,
                        episode_generation=episode,
                        transition_generation=transition,
                    )
                    for env_value, episode, transition in candidate.context_rows
                )
                stage = "ledger_consume"
                receipt = self._ledger.consume(
                    facts,
                    producer_stamp=self._authority._producer_stamp,
                    expected_generations=expectations,
                )
                receipt_issued = True
                self._pause_for_test(
                    reached=(
                        None
                        if self._test_control is None
                        else self._test_control.after_ledger_consume_reached
                    ),
                    release=(
                        None
                        if self._test_control is None
                        else self._test_control.after_ledger_consume_release
                    ),
                    stage="after_ledger_consume",
                )

                stage = "result_finalize"
                result = self._result_factory.finalize(
                    facts=facts,
                    receipt=receipt,
                    completed_tasks=candidate.completed_tasks,
                    released_tasks=candidate.released_tasks,
                    new_failed_pairs=candidate.new_failed_pairs,
                    prior_failed_pairs=candidate.prior_failed_pairs,
                    updated_failed_pairs=candidate.updated_failed_pairs,
                    new_team_infeasible_tasks=(
                        candidate.new_team_infeasible_tasks
                    ),
                    updated_task_state=candidate.updated_task_state,
                    updated_robot_state=candidate.updated_robot_state,
                    updated_ownership=candidate.updated_ownership,
                    termination_reason=candidate.termination_reason,
                    task_completed_state_encoding=int(
                        TaskLifecycleState.COMPLETED
                    ),
                    lifecycle_events=candidate.lifecycle_events,
                )
                self._validate_finalized_result(result, candidate)
                prepared_lifecycle_view = PublishedLifecycleView._create(
                    state_snapshot=prepared_swap._replacement_snapshot,
                    episode_generation=facts.episode_generation,
                    transition_generation=facts.transition_generation,
                    result=result,
                )
                prepared_view = self._prepare_lifecycle_publication(
                    lifecycle_view=prepared_lifecycle_view,
                    result=result,
                )
                prepared_terminal = self._prepare_terminal_handoffs(
                    candidate=candidate,
                    result=result,
                    prepared_lifecycle_view=prepared_lifecycle_view,
                    prepared_current_publication=prepared_view,
                    coverage_after_transition=terminal_coverage_after,
                    pre_reset_critic_physical_snapshot=(
                        pre_reset_critic_physical_snapshot
                    ),
                )

                stage = "state_swap"
                committed_snapshot = (
                    self._state_store._commit_prepared_lifecycle_swap(
                        prepared_swap,
                        writer_capability=self._writer_capability,
                    )
                )
                if committed_snapshot is not prepared_swap._replacement_snapshot:
                    raise LifecycleCoordinatorRuntimeError(
                        "StateStore returned an unexpected committed snapshot",
                        failure_code="state_swap_identity",
                        stage="state_swap",
                        expected=id(prepared_swap._replacement_snapshot),
                        actual=id(committed_snapshot),
                    )
                self._pause_for_test(
                    reached=(
                        None
                        if self._test_control is None
                        else self._test_control.after_state_swap_reached
                    ),
                    release=(
                        None
                        if self._test_control is None
                        else self._test_control.after_state_swap_release
                    ),
                    stage="after_state_swap",
                )

                stage = "generation_commit"
                committed_rows = self._generation_clock.commit_transition(
                    facts.env_id,
                    transition_contexts,
                )
                committed_values = tuple(
                    (
                        row.env_id,
                        row.episode_generation,
                        row.transition_generation,
                    )
                    for row in committed_rows
                )
                if committed_values != candidate.context_rows or any(
                    row.outstanding_transition_generation is not None
                    for row in committed_rows
                ):
                    raise LifecycleCoordinatorRuntimeError(
                        "generation commit differs from the prepared candidate",
                        failure_code="generation_commit_binding",
                        stage="generation_commit",
                        expected=candidate.context_rows,
                        actual=committed_values,
                    )

                stage = "publication"
                self._published_view = prepared_view
                self._pause_for_test(
                    reached=(
                        None
                        if self._test_control is None
                        else self._test_control.after_publication_reached
                    ),
                    release=(
                        None
                        if self._test_control is None
                        else self._test_control.after_publication_release
                    ),
                    stage="after_publication_before_terminal_install",
                )
                stage = "terminal_install"
                if self._test_control is not None and self._test_control.fail_terminal_install:
                    raise LifecycleCoordinatorRuntimeError(
                        "injected terminal handoff installation failure",
                        failure_code="injected_terminal_install_failure",
                        stage=stage,
                    )
                self._commit_prepared_terminal_handoffs(prepared_terminal)
                return prepared_view
            except Exception as exc:
                if receipt_issued:
                    self._poisoned = True
                    self._poison_cause = f"{stage}:{type(exc).__name__}:{exc}"
                    raise LifecycleCoordinatorRuntimeError(
                        "authority transaction failed after receipt issuance; "
                        "the coordinator is poisoned and requires teardown",
                        failure_code="fatal_post_receipt_failure",
                        stage=stage,
                        expected="no-fail success tail",
                        actual=type(exc).__name__,
                    ) from exc
                raise

    def _prepare_initial_claim_request(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> InitialClaimRequest:
        """Capture a factory-only exact current baseline and issue one request."""

        with self._publication_lock:
            self._require_not_poisoned(stage="claim_request_issue")
            if type(selected_env_ids) is not torch.Tensor or selected_env_ids.ndim != 1:
                raise InitialClaimRuntimeError(
                    "selected_env_ids must have exact nonempty shape [K]",
                    failure_code="selected_env_shape",
                    stage="claim_request_issue",
                    field_name="selected_env_ids",
                    expected="nonempty rank-one torch.Tensor",
                    actual=(type(selected_env_ids), getattr(selected_env_ids, "shape", None)),
                )
            selected_count = int(selected_env_ids.shape[0])
            if selected_count <= 0:
                raise InitialClaimRuntimeError(
                    "initial claim selection must not be empty",
                    failure_code="empty_request",
                    stage="claim_request_issue",
                    field_name="selected_env_ids",
                    expected="K >= 1",
                    actual=selected_count,
                )
            selected = _capture_tensor(
                selected_env_ids,
                field_name="selected_env_ids",
                shape=(selected_count,),
                dtype=torch.int64,
                device=self._state_store._device,
                error_type=LifecycleCoordinatorRuntimeError,
                stage="claim_request_issue",
            )
            requested = _capture_tensor(
                requested_task_by_robot,
                field_name="requested_task_by_robot",
                shape=(selected_count, self._state_store._num_robots),
                dtype=torch.int64,
                device=self._state_store._device,
                error_type=LifecycleCoordinatorRuntimeError,
                stage="claim_request_issue",
            )
            selected_values, selected_rows = (
                self._generation_clock._normalize_selected_env_ids(selected)
            )
            invalid = (requested < NO_CLAIM) | (requested >= self._state_store._num_tasks)
            index = _first_true(invalid)
            if index is not None:
                input_row, robot_id = index
                raise InitialClaimRuntimeError(
                    "requested task ID is outside NO_CLAIM or 0..N-1",
                    failure_code="task_id_range",
                    stage="claim_request_issue",
                    field_name="requested_task_by_robot",
                    env_id=selected_values[input_row],
                    expected=(NO_CLAIM, self._state_store._num_tasks - 1),
                    actual={"robot": robot_id, "task": int(requested[input_row, robot_id].item())},
                )
            empty_rows = (requested == NO_CLAIM).all(dim=1)
            index = _first_true(empty_rows)
            if index is not None:
                raise InitialClaimRuntimeError(
                    "every selected environment must contain at least one claim",
                    failure_code="empty_selected_row",
                    stage="claim_request_issue",
                    env_id=selected_values[index[0]],
                    expected="one or more non-NO_CLAIM values",
                    actual="all NO_CLAIM",
                )
            for input_row, env_value in enumerate(selected_values):
                claims = tuple(
                    int(value)
                    for value in requested[input_row].tolist()
                    if int(value) != NO_CLAIM
                )
                if len(set(claims)) != len(claims):
                    raise InitialClaimRuntimeError(
                        "duplicate task IDs within a selected row are forbidden",
                        failure_code="duplicate_task",
                        stage="claim_request_issue",
                        env_id=env_value,
                        expected="unique nonnegative task IDs",
                        actual=claims,
                    )

            snapshot = self._state_store._snapshot_for_lifecycle(
                writer_capability=self._writer_capability,
            )
            self._state_store._validate_expected_snapshot(snapshot)
            clock_rows = self._capture_clock_rows()
            self._validate_current_publication(snapshot, clock_rows)
            source_kinds: list[_InitialClaimSourceKind] = []
            for env_value, row in zip(selected_values, selected_rows, strict=True):
                provenance = self._published_view.provenance[row]
                if provenance.kind is _CurrentPublicationProvenanceKind.PREBOOTSTRAP:
                    raise InitialClaimRuntimeError(
                        "PREBOOTSTRAP publication rows are not claim eligible",
                        failure_code="prebootstrap_source",
                        stage="claim_request_issue",
                        env_id=env_value,
                        expected="reset, lifecycle transition, or post-assignment",
                        actual=provenance.kind,
                    )
                if provenance.kind is _CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION:
                    result = provenance.lifecycle_result
                    if type(result) is not LifecycleTransitionResult:
                        raise InitialClaimRuntimeError(
                            "transition provenance lacks its exact lifecycle result",
                            failure_code="source_provenance",
                            stage="claim_request_issue",
                            env_id=env_value,
                            expected=LifecycleTransitionResult,
                            actual=type(result),
                        )
                    result.validate_finalized()
                    for observed, expected, field_name in (
                        (result.updated_task_state[row], snapshot._task_state[row], "task_state"),
                        (result.updated_robot_state[row], snapshot._robot_state[row], "robot_state"),
                        (result.updated_ownership[row], snapshot._ownership[row], "ownership"),
                        (result.updated_failed_pairs[row], snapshot._cumulative_failed_pairs[row], "failed_pairs"),
                    ):
                        if not torch.equal(observed, expected):
                            raise InitialClaimRuntimeError(
                                "transition provenance row differs from current state",
                                failure_code="source_provenance",
                                stage="claim_request_issue",
                                field_name=field_name,
                                env_id=env_value,
                                expected="exact current row",
                                actual="tensor values differ",
                            )
                    source_kinds.append(
                        _InitialClaimSourceKind.FINALIZED_LIFECYCLE_TRANSITION
                    )
                elif provenance.kind is _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET:
                    if not (
                        bool((snapshot._task_state[row] == int(TaskLifecycleState.AVAILABLE)).all().item())
                        and bool((snapshot._robot_state[row] == int(RobotLifecycleState.NEEDS_ASSIGNMENT)).all().item())
                        and bool((snapshot._ownership[row] == -1).all().item())
                        and not bool(snapshot._cumulative_failed_pairs[row].any().item())
                        and not bool(snapshot._completion_count[row].any().item())
                        and int(snapshot._termination_reason[row].item()) == int(TerminationReason.NONE)
                    ):
                        raise InitialClaimRuntimeError(
                            "reset provenance row differs from canonical reset semantics",
                            failure_code="reset_source_semantics",
                            stage="claim_request_issue",
                            env_id=env_value,
                            expected="canonical reset row",
                            actual="state differs",
                        )
                    source_kinds.append(_InitialClaimSourceKind.CANONICAL_EPISODE_RESET)
                else:
                    if type(provenance.assignment_artifact) is not EffectiveAssignmentCommitArtifact:
                        raise InitialClaimRuntimeError(
                            "post-assignment provenance lacks its exact artifact",
                            failure_code="source_provenance",
                            stage="claim_request_issue",
                            env_id=env_value,
                            expected=EffectiveAssignmentCommitArtifact,
                            actual=type(provenance.assignment_artifact),
                        )
                    source_kinds.append(_InitialClaimSourceKind.POST_ASSIGNMENT)

            token = self._next_request_token
            if token > _INT64_MAX:
                raise InitialClaimRuntimeError(
                    "initial-claim request token space is exhausted",
                    failure_code="request_token_overflow",
                    stage="claim_request_issue",
                    expected=f"<= {_INT64_MAX}",
                    actual=token,
                )
            self._next_request_token = token + 1
            baseline = _InitialClaimSourceBaseline._create(
                profile=self._profile,
                domain_identity=self._domain_identity,
                source_publication=self._published_view,
                store_identity=snapshot._store_identity,
                selected_env_ids=selected,
                selected_rows=selected_rows,
                source_kinds=tuple(source_kinds),
                factory_capability=self._claim_factory_capability,
            )
            request_identity = object()
            context = _InitialClaimRequestContext._create(
                token=token,
                domain_identity=self._domain_identity,
                profile=self._profile,
                baseline=baseline,
                request_identity=request_identity,
                selected_env_ids=selected,
                requested_task_by_robot=requested,
                factory_capability=self._claim_factory_capability,
            )
            request = InitialClaimRequest._create(
                context=context,
                baseline=baseline,
                selected_env_ids=selected,
                requested_task_by_robot=requested,
                request_identity=request_identity,
                factory_capability=self._claim_factory_capability,
            )
            replacement = dict(self._active_claim_contexts)
            replacement[token] = context
            self._active_claim_contexts = replacement
            return request

    def _commit_initial_claim(
        self,
        request: InitialClaimRequest,
    ) -> EffectiveAssignmentCommitArtifact:
        """Commit one full selected C2 batch under the existing publication lock."""

        with self._publication_lock:
            self._require_not_poisoned(stage="claim_commit")
            state_swapped = False
            stage = "claim_prevalidation"
            try:
                context = self._validate_claim_request_context(request)
                baseline = request._baseline
                snapshot = self._state_store._snapshot_for_lifecycle(
                    writer_capability=self._writer_capability,
                )
                self._state_store._validate_expected_snapshot(snapshot)
                clock_rows = self._capture_clock_rows()
                self._validate_current_publication(snapshot, clock_rows)
                self._validate_claim_source_current(request, snapshot)
                self._validate_claim_terminal_fence(request)
                candidate = self._claim_deriver.derive_candidate(request)
                _validate_state_invariants(
                    env_id=snapshot._env_id,
                    task_state=candidate.task_state,
                    robot_state=candidate.robot_state,
                    ownership=candidate.ownership,
                    cumulative_failed_pairs=candidate.cumulative_failed_pairs,
                    completion_count=candidate.completion_count,
                    termination_reason=candidate.termination_reason,
                    error_type=LifecycleStateRuntimeError,
                    stage="claim_candidate_validation",
                )
                prepared_swap = self._state_store._prepare_initial_claim_swap(
                    snapshot=snapshot,
                    candidate=candidate,
                    writer_capability=self._writer_capability,
                )
                prepared_lifecycle_view = PublishedLifecycleView._create(
                    state_snapshot=prepared_swap._replacement_snapshot,
                    episode_generation=self._published_view.episode_generation,
                    transition_generation=self._published_view.transition_generation,
                    result=None,
                )
                artifact = EffectiveAssignmentCommitArtifact._create(
                    profile=self._profile,
                    domain_identity=self._domain_identity,
                    request=request,
                    committed_store_version=prepared_swap._replacement_snapshot.store_version,
                    candidate=candidate,
                    factory_capability=self._claim_factory_capability,
                )
                prepared_publication = self._prepare_assignment_publication(
                    lifecycle_view=prepared_lifecycle_view,
                    artifact=artifact,
                    selected_rows=baseline.selected_rows,
                )
                active_replacement = dict(self._active_claim_contexts)
                del active_replacement[request.token]
                consumed_replacement = self._prepare_consumed_token_intervals(
                    request.token
                )

                self._state_store._validate_expected_snapshot(snapshot)
                if self._published_view is not baseline.source_publication:
                    raise InitialClaimRuntimeError(
                        "claim source publication changed during preparation",
                        failure_code="stale_source",
                        stage="claim_revalidation",
                        expected=id(baseline.source_publication),
                        actual=id(self._published_view),
                    )
                self._validate_claim_request_context(request)
                self._validate_claim_terminal_fence(request)
                control = self._initial_claim_test_control
                self._pause_for_test(
                    reached=(None if control is None else control.before_state_swap_reached),
                    release=(None if control is None else control.before_state_swap_release),
                    stage="claim_before_state_swap",
                )

                stage = "claim_state_swap"
                committed = self._state_store._commit_prepared_lifecycle_swap(
                    prepared_swap,
                    writer_capability=self._writer_capability,
                )
                state_swapped = True
                if committed is not prepared_swap._replacement_snapshot:
                    raise LifecycleCoordinatorRuntimeError(
                        "StateStore returned an unexpected initial-claim snapshot",
                        failure_code="claim_state_swap_identity",
                        stage=stage,
                        expected=id(prepared_swap._replacement_snapshot),
                        actual=id(committed),
                    )
                self._pause_for_test(
                    reached=(None if control is None else control.after_state_swap_reached),
                    release=(None if control is None else control.after_state_swap_release),
                    stage="claim_after_state_swap",
                )
                if control is not None and control.fail_after_state_swap:
                    raise LifecycleCoordinatorRuntimeError(
                        "injected failure after initial-claim StateStore swap",
                        failure_code="injected_claim_post_swap_failure",
                        stage=stage,
                    )
                stage = "claim_consume"
                self._active_claim_contexts = active_replacement
                self._consumed_claim_token_intervals = consumed_replacement
                stage = "claim_publication"
                self._published_view = prepared_publication
                return artifact
            except Exception as exc:
                if state_swapped:
                    self._poisoned = True
                    self._poison_cause = f"{stage}:{type(exc).__name__}:{exc}"
                    raise LifecycleCoordinatorRuntimeError(
                        "initial claim failed after StateStore swap; coordinator requires teardown",
                        failure_code="fatal_post_claim_swap_failure",
                        stage=stage,
                        expected="no-fail initial-claim success tail",
                        actual=type(exc).__name__,
                    ) from exc
                raise

    def _validate_claim_request_context(
        self,
        request: object,
    ) -> _InitialClaimRequestContext:
        if type(request) is not InitialClaimRequest:
            raise InitialClaimRuntimeError(
                "claim commit requires an exact issued request",
                failure_code="request_type",
                stage="claim_prevalidation",
                expected=InitialClaimRequest,
                actual=type(request),
            )
        if self._is_consumed_claim_token(request.token):
            raise InitialClaimRuntimeError(
                "initial-claim request token was already consumed",
                failure_code="request_consumed",
                stage="claim_prevalidation",
                expected="unconsumed token",
                actual=request.token,
            )
        context = request._context
        active = self._active_claim_contexts.get(request.token)
        if (
            type(context) is not _InitialClaimRequestContext
            or active is not context
            or context._factory_capability is not self._claim_factory_capability
            or context._domain_identity is not self._domain_identity
            or context._profile is not self._profile
            or context._baseline_identity is not request._baseline
            or context._request_identity is not request._request_identity
            or context.selected_env_ids
            != tuple(int(value) for value in request._selected_env_ids.cpu().tolist())
            or context._request_digest
            != _tensor_digest(request._selected_env_ids, request._requested_task_by_robot)
        ):
            raise InitialClaimRuntimeError(
                "request/context is foreign, altered, or no longer active",
                failure_code="request_context",
                stage="claim_prevalidation",
                expected="exact active retained-domain context",
                actual=(request.token, type(active)),
            )
        return context

    def _validate_claim_source_current(
        self,
        request: InitialClaimRequest,
        snapshot: LifecycleStateSnapshot,
    ) -> None:
        baseline = request._baseline
        if (
            baseline._profile is not self._profile
            or baseline._domain_identity is not self._domain_identity
            or baseline._factory_capability is not self._claim_factory_capability
            or baseline._source_publication is not self._published_view
            or baseline._source_publication_identity
            is not self._published_view.publication_identity
            or baseline._store_identity is not snapshot._store_identity
            or baseline.source_store_version != snapshot.store_version
        ):
            raise InitialClaimRuntimeError(
                "initial-claim source identity/version is stale or foreign",
                failure_code="stale_source",
                stage="claim_prevalidation",
                expected=(id(self._published_view), snapshot.store_version),
                actual=(id(baseline._source_publication), baseline.source_store_version),
            )
        view = self._published_view
        state = view.lifecycle_state
        for observed, expected, field_name in (
            (baseline._episode_generation, view.episode_generation, "episode_generation"),
            (baseline._transition_generation, view.transition_generation, "transition_generation"),
            (baseline._task_state, state._task_state, "task_state"),
            (baseline._robot_state, state._robot_state, "robot_state"),
            (baseline._ownership, state._ownership, "ownership"),
            (baseline._cumulative_failed_pairs, state._cumulative_failed_pairs, "cumulative_failed_pairs"),
            (baseline._completion_count, state._completion_count, "completion_count"),
            (baseline._termination_reason, state._termination_reason, "termination_reason"),
        ):
            if not torch.equal(observed, expected):
                raise InitialClaimRuntimeError(
                    "initial-claim source tensors are stale",
                    failure_code="stale_source",
                    stage="claim_prevalidation",
                    field_name=field_name,
                    expected="exact current publication tensor",
                    actual="tensor values differ",
                )
        for input_row, domain_row in enumerate(baseline.selected_rows):
            if baseline.source_provenance[input_row] is not view.provenance[domain_row]:
                raise InitialClaimRuntimeError(
                    "initial-claim source provenance changed",
                    failure_code="stale_source",
                    stage="claim_prevalidation",
                    env_id=int(baseline._selected_env_ids[input_row].item()),
                    expected=id(baseline.source_provenance[input_row]),
                    actual=id(view.provenance[domain_row]),
                )

    def _validate_claim_terminal_fence(self, request: InitialClaimRequest) -> None:
        for env_value in request._context.selected_env_ids:
            artifact = self._terminal_slots.get(env_value)
            if artifact is not None:
                raise InitialClaimRuntimeError(
                    "selected environment has an unacknowledged terminal handoff",
                    failure_code="terminal_slot_occupied",
                    stage="claim_terminal_fence",
                    env_id=env_value,
                    expected=None,
                    actual=artifact.key,
                )

    def _is_consumed_claim_token(self, token: int) -> bool:
        return any(start <= token <= end for start, end in self._consumed_claim_token_intervals)

    def _prepare_consumed_token_intervals(
        self,
        token: int,
    ) -> tuple[tuple[int, int], ...]:
        intervals = list(self._consumed_claim_token_intervals)
        intervals.append((token, token))
        intervals.sort()
        merged: list[tuple[int, int]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1] + 1:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        return tuple(merged)

    def _prevalidate_terminal_capacity(
        self,
        *,
        candidate: _LifecycleTransitionCandidate,
        coverage_before_transition: torch.Tensor | None,
    ) -> torch.Tensor | None:
        if coverage_before_transition is None:
            return None
        facts = candidate.facts
        if (
            type(coverage_before_transition) is not torch.Tensor
            or coverage_before_transition.dtype is not torch.bool
            or coverage_before_transition.layout is not torch.strided
            or coverage_before_transition.device != facts.device
            or tuple(coverage_before_transition.shape) != (facts.num_envs, facts.num_tasks)
            or coverage_before_transition.requires_grad
        ):
            raise LifecycleCoordinatorRuntimeError(
                "terminal-aware transaction requires canonical coverage evidence [E,N]",
                failure_code="terminal_coverage",
                stage="prevalidation",
                expected=(torch.bool, (facts.num_envs, facts.num_tasks), facts.device),
                actual=(
                    getattr(coverage_before_transition, "dtype", None),
                    getattr(coverage_before_transition, "shape", None),
                    getattr(coverage_before_transition, "device", None),
                ),
            )
        terminal_rows = candidate.termination_reason != int(TerminationReason.NONE)
        for row, is_terminal in enumerate(terminal_rows.detach().cpu().tolist()):
            if not bool(is_terminal):
                continue
            env_value = candidate.context_rows[row][0]
            occupied = self._terminal_slots.get(env_value)
            if occupied is not None:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal handoff capacity is occupied before ledger consumption",
                    failure_code="terminal_slot_occupied",
                    stage="prevalidation",
                    env_id=env_value,
                    expected=None,
                    actual=occupied.key,
                )
        return (
            coverage_before_transition.detach().clone().contiguous()
            | candidate.completed_tasks.detach().clone().contiguous()
        )

    @staticmethod
    def _prevalidate_terminal_critic_snapshot(
        *,
        candidate: _LifecycleTransitionCandidate,
        physical_snapshot: object | None,
    ) -> None:
        """Reject malformed B2-I4 evidence before ledger receipt issuance."""

        if physical_snapshot is None:
            return
        from .assignment_event_terminal_critic_sidecar import (
            PreResetCriticPhysicalSnapshotV2,
        )

        facts = candidate.facts
        if type(physical_snapshot) is not PreResetCriticPhysicalSnapshotV2:
            raise LifecycleCoordinatorRuntimeError(
                "terminal-aware transaction received a noncanonical pre-reset critic snapshot",
                failure_code="terminal_critic_snapshot_type",
                stage="prevalidation",
                expected=PreResetCriticPhysicalSnapshotV2,
                actual=type(physical_snapshot),
            )
        actual = (
            physical_snapshot.num_envs,
            physical_snapshot.M,
            physical_snapshot.N,
            physical_snapshot.device,
        )
        expected = (facts.num_envs, facts.num_robots, facts.num_tasks, facts.device)
        if actual != expected:
            raise LifecycleCoordinatorRuntimeError(
                "pre-reset critic snapshot differs from the authority transaction domain",
                failure_code="terminal_critic_snapshot_domain",
                stage="prevalidation",
                expected=expected,
                actual=actual,
            )

    def _prepare_terminal_handoffs(
        self,
        *,
        candidate: _LifecycleTransitionCandidate,
        result: LifecycleTransitionResult,
        prepared_lifecycle_view: PublishedLifecycleView,
        prepared_current_publication: _EventRuntimeCurrentPublication,
        coverage_after_transition: torch.Tensor | None,
        pre_reset_critic_physical_snapshot: object | None,
    ) -> _PreparedTerminalHandoffs | None:
        if coverage_after_transition is None:
            return None
        sidecars: tuple[object | None, ...]
        if pre_reset_critic_physical_snapshot is None:
            # Compatibility for pre-B2 pure transaction fixtures.  The task-local
            # production seam always supplies B2-I4 physical evidence.
            sidecars = (None,) * int(result.env_id.numel())
        else:
            from .assignment_event_terminal_critic_sidecar import (
                build_event_terminal_critic_sidecars_v2,
            )

            sidecars = build_event_terminal_critic_sidecars_v2(
                physical_snapshot=pre_reset_critic_physical_snapshot,
                current_publication=prepared_current_publication,
            )
            if len(sidecars) != int(result.env_id.numel()):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal sidecar batch differs from the finalized result domain",
                    failure_code="terminal_sidecar_batch_cardinality",
                    stage="terminal_handoff_prepare",
                    expected=int(result.env_id.numel()),
                    actual=len(sidecars),
                )
        replacement = dict(self._terminal_slots)
        keys: list[_TerminalTransitionKey] = []
        for row, reason in enumerate(candidate.termination_reason.detach().cpu().tolist()):
            if int(reason) == int(TerminationReason.NONE):
                continue
            env_value, episode, transition = candidate.context_rows[row]
            key = _TerminalTransitionKey(env_value, episode, transition)
            if env_value in replacement:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal slot changed after receipt-free capacity validation",
                    failure_code="terminal_slot_identity",
                    stage="terminal_handoff_prepare",
                    env_id=env_value,
                    expected=None,
                    actual=replacement[env_value].key,
                )
            replacement[env_value] = _TerminalHandoffArtifact._create(
                key=key,
                result=result,
                published_view=prepared_lifecycle_view,
                domain_row=row,
                coverage_after_transition=coverage_after_transition[row],
                optional_sidecar=sidecars[row],
            )
            keys.append(key)
        return _PreparedTerminalHandoffs(
            self._terminal_store_identity,
            self._terminal_slots,
            replacement,
            tuple(keys),
        )

    def _commit_prepared_terminal_handoffs(
        self,
        prepared: _PreparedTerminalHandoffs | None,
    ) -> None:
        if prepared is None:
            return
        if (
            type(prepared) is not _PreparedTerminalHandoffs
            or prepared._store_identity is not self._terminal_store_identity
            or prepared._expected_slots_identity is not self._terminal_slots
        ):
            raise LifecycleCoordinatorRuntimeError(
                "prepared terminal handoff belongs to another slot version",
                failure_code="terminal_slot_identity",
                stage="terminal_install",
                expected=(id(self._terminal_store_identity), id(self._terminal_slots)),
                actual=(
                    id(getattr(prepared, "_store_identity", None)),
                    id(getattr(prepared, "_expected_slots_identity", None)),
                ),
            )
        self._terminal_slots = prepared._replacement_slots

    def _issue_terminal_observer_capability(self) -> _TerminalObserverCapability:
        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_observer_issue")
            return _TerminalObserverCapability(self._terminal_store_identity)

    def _issue_terminal_consumer_capability(self) -> _TerminalConsumerCapability:
        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_consumer_issue")
            if self._terminal_consumer_issued:
                raise LifecycleCoordinatorRuntimeError(
                    "the designated terminal consumer capability was already issued",
                    failure_code="terminal_consumer_already_issued",
                    stage="terminal_consumer_issue",
                    expected=False,
                    actual=True,
                )
            self._terminal_consumer_issued = True
            return self._terminal_consumer_capability

    def _read_terminal(
        self,
        key: _TerminalTransitionKey,
        *,
        capability: _TerminalObserverCapability | _TerminalConsumerCapability,
    ) -> _TerminalHandoffArtifact:
        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_read")
            if type(key) is not _TerminalTransitionKey:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal read requires an exact transition key",
                    failure_code="terminal_key_type",
                    stage="terminal_read",
                    expected=_TerminalTransitionKey,
                    actual=type(key),
                )
            if (
                type(capability) not in (_TerminalObserverCapability, _TerminalConsumerCapability)
                or capability._store_identity is not self._terminal_store_identity
            ):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal read lacks a bound observer or consumer capability",
                    failure_code="terminal_read_capability",
                    stage="terminal_read",
                    expected="bound read capability",
                    actual=type(capability),
                )
            artifact = self._terminal_slots.get(key.env_id)
            if artifact is None:
                raise LifecycleCoordinatorRuntimeError(
                    "no terminal handoff occupies the requested environment slot",
                    failure_code="terminal_slot_empty",
                    stage="terminal_read",
                    env_id=key.env_id,
                    expected=key,
                    actual=None,
                )
            stored = artifact.key
            if (
                stored.env_id,
                stored.episode_generation,
                stored.transition_generation,
            ) != (key.env_id, key.episode_generation, key.transition_generation):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal handoff key is stale or does not match the occupied slot",
                    failure_code="terminal_key_mismatch",
                    stage="terminal_read",
                    env_id=key.env_id,
                    expected=stored,
                    actual=key,
                )
            return artifact

    def _capture_pending_terminal_artifacts(
        self,
        *,
        capability: _TerminalConsumerCapability,
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        """Capture the exact stored terminal artifacts without consuming them."""

        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_capture")
            if (
                type(capability) is not _TerminalConsumerCapability
                or capability is not self._terminal_consumer_capability
                or capability._store_identity is not self._terminal_store_identity
                or not self._terminal_consumer_issued
            ):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal capture lacks the unique designated consumer capability",
                    failure_code="terminal_capture_capability",
                    stage="terminal_capture",
                    expected="designated consumer capability",
                    actual=type(capability),
                )
            return tuple(
                artifact
                for _, artifact in sorted(self._terminal_slots.items())
            )

    def _acknowledge_terminal(
        self,
        key: _TerminalTransitionKey,
        *,
        capability: _TerminalConsumerCapability,
    ) -> _TerminalHandoffArtifact:
        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_acknowledge")
            if (
                type(capability) is not _TerminalConsumerCapability
                or capability is not self._terminal_consumer_capability
                or capability._store_identity is not self._terminal_store_identity
                or not self._terminal_consumer_issued
            ):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal acknowledgement lacks the unique designated consumer capability",
                    failure_code="terminal_ack_capability",
                    stage="terminal_acknowledge",
                    expected="designated consumer capability",
                    actual=type(capability),
                )
            if type(key) is not _TerminalTransitionKey:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal acknowledgement requires an exact transition key",
                    failure_code="terminal_key_type",
                    stage="terminal_acknowledge",
                    expected=_TerminalTransitionKey,
                    actual=type(key),
                )
            artifact = self._terminal_slots.get(key.env_id)
            if artifact is None:
                raise LifecycleCoordinatorRuntimeError(
                    "no terminal handoff occupies the requested environment slot",
                    failure_code="terminal_slot_empty",
                    stage="terminal_acknowledge",
                    env_id=key.env_id,
                    expected=key,
                    actual=None,
                )
            stored = artifact.key
            if (
                stored.env_id,
                stored.episode_generation,
                stored.transition_generation,
            ) != (key.env_id, key.episode_generation, key.transition_generation):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal acknowledgement key is stale or mismatched",
                    failure_code="terminal_key_mismatch",
                    stage="terminal_acknowledge",
                    env_id=key.env_id,
                    expected=stored,
                    actual=key,
                )
            replacement = dict(self._terminal_slots)
            del replacement[key.env_id]
            self._terminal_slots = replacement
            return artifact

    def _acknowledge_terminal_batch(
        self,
        keys: tuple[_TerminalTransitionKey, ...],
        *,
        capability: _TerminalConsumerCapability,
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        """Atomically acknowledge one fully validated exact-key batch."""

        with self._publication_lock:
            self._require_not_poisoned(stage="terminal_batch_acknowledge")
            if (
                type(capability) is not _TerminalConsumerCapability
                or capability is not self._terminal_consumer_capability
                or capability._store_identity is not self._terminal_store_identity
                or not self._terminal_consumer_issued
            ):
                raise LifecycleCoordinatorRuntimeError(
                    "terminal batch acknowledgement lacks the unique designated consumer capability",
                    failure_code="terminal_batch_ack_capability",
                    stage="terminal_batch_acknowledge",
                    expected="designated consumer capability",
                    actual=type(capability),
                )
            if type(keys) is not tuple:
                raise LifecycleCoordinatorRuntimeError(
                    "terminal batch acknowledgement requires an exact tuple",
                    failure_code="terminal_batch_type",
                    stage="terminal_batch_acknowledge",
                    expected="tuple[_TerminalTransitionKey, ...]",
                    actual=type(keys),
                )

            validated: list[tuple[int, _TerminalTransitionKey, _TerminalHandoffArtifact]] = []
            seen_keys: set[tuple[int, int, int]] = set()
            seen_env_ids: set[int] = set()
            for position, key in enumerate(keys):
                if type(key) is not _TerminalTransitionKey:
                    raise LifecycleCoordinatorRuntimeError(
                        "terminal batch contains a noncanonical transition key",
                        failure_code="terminal_key_type",
                        stage="terminal_batch_acknowledge",
                        expected=_TerminalTransitionKey,
                        actual={"position": position, "type": type(key)},
                    )
                scalar_key = (
                    key.env_id,
                    key.episode_generation,
                    key.transition_generation,
                )
                if scalar_key in seen_keys or key.env_id in seen_env_ids:
                    raise LifecycleCoordinatorRuntimeError(
                        "terminal batch contains a duplicate key or environment row",
                        failure_code="terminal_batch_duplicate",
                        stage="terminal_batch_acknowledge",
                        env_id=key.env_id,
                        expected="unique exact keys and unique env rows",
                        actual=scalar_key,
                    )
                seen_keys.add(scalar_key)
                seen_env_ids.add(key.env_id)
                artifact = self._terminal_slots.get(key.env_id)
                if artifact is None:
                    raise LifecycleCoordinatorRuntimeError(
                        "no terminal handoff occupies one requested batch row",
                        failure_code="terminal_slot_empty",
                        stage="terminal_batch_acknowledge",
                        env_id=key.env_id,
                        expected=key,
                        actual=None,
                    )
                stored = artifact.key
                stored_key = (
                    stored.env_id,
                    stored.episode_generation,
                    stored.transition_generation,
                )
                if stored_key != scalar_key:
                    raise LifecycleCoordinatorRuntimeError(
                        "one terminal batch key is stale or mismatched",
                        failure_code="terminal_key_mismatch",
                        stage="terminal_batch_acknowledge",
                        env_id=key.env_id,
                        expected=stored,
                        actual=key,
                    )
                validated.append((key.env_id, key, artifact))

            canonical = tuple(sorted(validated, key=lambda item: item[0]))
            acknowledged = tuple(item[2] for item in canonical)
            replacement = {
                env_id: artifact
                for env_id, artifact in self._terminal_slots.items()
                if env_id not in seen_env_ids
            }

            # The sole authoritative mutation point. Every validation, return
            # identity, and replacement entry is prepared before publication.
            self._terminal_slots = replacement
            return acknowledged

    def _assert_physical_step_allowed(self) -> None:
        self._capture_physical_step_admission_baseline()

    def _assert_runtime_admission_healthy(self) -> None:
        """Private B1W health gate using the one coordinator poison truth."""

        with self._publication_lock:
            self._require_not_poisoned(stage="runtime_admission")

    def _capture_physical_step_admission_baseline(
        self,
    ) -> _EventRuntimeCurrentPublication:
        """Atomically apply R3 and return the exact P2 admitted for a step."""

        with self._publication_lock:
            self._require_not_poisoned(stage="physical_step_permission")
            if self._terminal_slots:
                occupied = tuple(
                    artifact.key
                    for _, artifact in sorted(self._terminal_slots.items())
                )
                raise LifecycleCoordinatorRuntimeError(
                    "a synchronous terminal acknowledgement is required before the next physical step",
                    failure_code="terminal_ack_required",
                    stage="physical_step_permission",
                    expected=(),
                    actual=occupied,
                )
            return self._published_view

    def _poison_after_runtime_admission_failure(
        self,
        *,
        stage: str,
        cause: BaseException,
    ) -> None:
        """Enter the existing fail-stop authority after an admitted call fails."""

        if type(stage) is not str or not stage:
            raise TypeError("runtime admission failure stage must be a non-empty exact string")
        if not isinstance(cause, BaseException):
            raise TypeError("runtime admission failure cause must be a BaseException")
        with self._publication_lock:
            if not self._poisoned:
                self._poisoned = True
                self._poison_cause = (
                    f"runtime_admission:{stage}:{type(cause).__name__}:{cause}"
                )

    def _poison_after_environment_bookkeeping_failure(
        self,
        *,
        published_view: PublishedLifecycleView,
        cause: BaseException,
    ) -> None:
        with self._publication_lock:
            if self._published_view.lifecycle_view is not published_view:
                raise LifecycleCoordinatorRuntimeError(
                    "post-authority bookkeeping failure does not bind the current publication",
                    failure_code="bookkeeping_view_identity",
                    stage="environment_bookkeeping_failure",
                    expected=id(self._published_view.lifecycle_view),
                    actual=id(published_view),
                )
            self._poisoned = True
            self._poison_cause = (
                f"environment_bookkeeping:{type(cause).__name__}:{cause}"
            )

    def _validate_clock_contexts(
        self,
        env_ids: torch.Tensor,
        contexts: object,
    ) -> tuple[tuple[int, int, int], ...]:
        if type(contexts) is not tuple:
            raise LifecycleCoordinatorRuntimeError(
                "clock validation requires an exact context tuple",
                failure_code="context_container_type",
                stage="clock_prevalidation",
                expected=tuple,
                actual=type(contexts),
            )
        selected_env_ids, rows = self._generation_clock._normalize_selected_env_ids(
            env_ids
        )
        if len(contexts) != len(rows):
            raise LifecycleCoordinatorRuntimeError(
                "clock context count differs from selected rows",
                failure_code="context_count",
                stage="clock_prevalidation",
                expected=len(rows),
                actual=len(contexts),
            )
        with self._generation_clock._lock:
            state = self._generation_clock._state
            validated: list[tuple[int, int, int]] = []
            for env_value, row, context in zip(
                selected_env_ids,
                rows,
                contexts,
                strict=True,
            ):
                if type(context) is not TransitionGenerationContext:
                    raise LifecycleCoordinatorRuntimeError(
                        "clock context has the wrong exact runtime type",
                        failure_code="context_type",
                        stage="clock_prevalidation",
                        env_id=env_value,
                        expected=TransitionGenerationContext,
                        actual=type(context),
                    )
                context_values = (
                    context.env_id,
                    context.episode_generation,
                    context.transition_generation,
                )
                if any(type(value) is not int for value in context_values):
                    raise LifecycleCoordinatorRuntimeError(
                        "clock context scalar fields must be exact integers",
                        failure_code="context_scalar_type",
                        stage="clock_prevalidation",
                        env_id=env_value,
                        expected=(int, int, int),
                        actual=tuple(type(value) for value in context_values),
                    )
                active = state.outstanding[row]
                expected_values = (
                    env_value,
                    state.episode_generation[row],
                    state.transition_generation[row] + 1,
                )
                if (
                    context._clock_identity
                    is not self._generation_clock._clock_identity
                    or active is None
                    or active.context is not context
                    or context_values != expected_values
                    or active.env_id != context_values[0]
                    or active.episode_generation != context_values[1]
                    or active.transition_generation != context_values[2]
                ):
                    raise LifecycleCoordinatorRuntimeError(
                        "context is not the exact outstanding next clock candidate",
                        failure_code="context_not_outstanding",
                        stage="clock_prevalidation",
                        env_id=env_value,
                        expected=expected_values,
                        actual=context_values,
                    )
                validated.append(context_values)
            return tuple(validated)

    @staticmethod
    def _validate_finalized_result(
        result: object,
        candidate: _LifecycleTransitionCandidate,
    ) -> None:
        if type(result) is not LifecycleTransitionResult:
            raise LifecycleCoordinatorRuntimeError(
                "result factory returned a noncanonical result",
                failure_code="result_type",
                stage="result_finalize",
                expected=LifecycleTransitionResult,
                actual=type(result),
            )
        result.validate_finalized()
        comparisons = (
            (result.completed_tasks, candidate.completed_tasks, "completed_tasks"),
            (result.released_tasks, candidate.released_tasks, "released_tasks"),
            (result.new_failed_pairs, candidate.new_failed_pairs, "new_failed_pairs"),
            (
                result.updated_failed_pairs,
                candidate.updated_failed_pairs,
                "updated_failed_pairs",
            ),
            (
                result.new_team_infeasible_tasks,
                candidate.new_team_infeasible_tasks,
                "new_team_infeasible_tasks",
            ),
            (
                result.updated_task_state,
                candidate.updated_task_state,
                "updated_task_state",
            ),
            (
                result.updated_robot_state,
                candidate.updated_robot_state,
                "updated_robot_state",
            ),
            (
                result.updated_ownership,
                candidate.updated_ownership,
                "updated_ownership",
            ),
            (
                result.termination_reason,
                candidate.termination_reason,
                "termination_reason",
            ),
        )
        for observed, expected, field_name in comparisons:
            if not torch.equal(observed, expected):
                raise LifecycleCoordinatorRuntimeError(
                    "factory result differs from the prevalidated candidate",
                    failure_code="result_candidate_binding",
                    stage="result_finalize",
                    field_name=field_name,
                    expected="exact candidate tensor",
                    actual="tensor values differ",
                )
        if result.lifecycle_events != candidate.lifecycle_events:
            raise LifecycleCoordinatorRuntimeError(
                "factory result events differ from the prevalidated candidate",
                failure_code="result_candidate_binding",
                stage="result_finalize",
                field_name="lifecycle_events",
                expected=candidate.lifecycle_events,
                actual=result.lifecycle_events,
            )

    @staticmethod
    def _pause_for_test(
        *,
        reached: Event | None,
        release: Event | None,
        stage: str,
    ) -> None:
        if reached is None and release is None:
            return
        if reached is None or release is None:
            raise LifecycleCoordinatorRuntimeError(
                "private test pause is missing one synchronization endpoint",
                failure_code="test_control_pair",
                stage=stage,
                expected="two Event values",
                actual=(type(reached), type(release)),
            )
        reached.set()
        if not release.wait(timeout=15.0):
            raise LifecycleCoordinatorRuntimeError(
                "private test pause timed out",
                failure_code="test_control_timeout",
                stage=stage,
                expected="release Event within watchdog interval",
                actual=False,
            )

    def _require_not_poisoned(self, *, stage: str) -> None:
        if self._poisoned:
            raise LifecycleCoordinatorRuntimeError(
                "lifecycle authority coordinator is poisoned",
                failure_code="coordinator_poisoned",
                stage=stage,
                expected=False,
                actual=self._poison_cause,
            )


__all__ = [
    "ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_SOURCE_PURPOSE",
    "CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_MODULE",
    "LifecycleAuthorityRuntime",
    "LifecycleAuthorityRuntimeError",
    "LifecycleAuthorityTransactionCoordinator",
    "LifecycleCoordinatorRuntimeError",
    "LifecycleStateRuntimeError",
    "LifecycleStateSnapshot",
    "LifecycleStateStore",
    "PublishedLifecycleView",
]
