"""Pure B-private exact-event proposal interpretation and M1 construction.

This module owns no runtime, domain, Store, O1, wrapper, resolver, terminal
slot, ownership cache, synchronization primitive, or poison authority.  Cost
is ranking evidence only; explicit physical feasibility is an independent
eligibility input.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_PROPOSAL_ADAPTER_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_proposal_adapter"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_PROPOSAL_ADAPTER_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event proposal adapter source must "
        "execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_PROPOSAL_ADAPTER_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, field
from enum import Enum

import torch

from .assignment_initial_claim_runtime import (
    NO_CLAIM,
    _CurrentPublicationIdentity,
    _EventRuntimeCurrentPublication,
)
from .assignment_lifecycle_transition_contract import (
    RobotLifecycleState,
    TaskLifecycleState,
    TerminationReason,
)
from .assignment_profile_contract import ResolvedEventGatedAssignmentProfile


_DECISION_FACTORY_CAPABILITY = object()
_RESOLUTION_FACTORY_CAPABILITY = object()
_ACTIVE_TASK_STATES = frozenset(
    (
        int(TaskLifecycleState.CLAIMED),
        int(TaskLifecycleState.NAVIGATING),
        int(TaskLifecycleState.ALIGNING),
    )
)


class EventProposalAdapterError(RuntimeError):
    """Typed pure proposal/snapshot validation failure."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.stage = stage
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"field_name={field_name!r}; expected={expected!r}; actual={actual!r}"
        )


class _EventProposalInterpretation(Enum):
    CONTINUE_EXISTING = "continue_existing"
    NEW_CLAIM_CANDIDATE = "new_claim_candidate"
    NEW_CLAIM_SELECTED = "new_claim_selected"
    NEW_CLAIM_COMMITTED = "new_claim_committed"
    PROPOSAL_NO_CLAIM = "proposal_no_claim"
    INVALID_SWITCH_WHILE_EXECUTING = "invalid_switch_while_executing"
    ILLEGAL_EXECUTING_NOOP = "illegal_executing_noop"
    INVALID_ROBOT_STATE = "invalid_robot_state"
    TASK_NOT_AVAILABLE = "task_not_available"
    TASK_OWNED = "task_owned"
    FAILED_PAIR = "failed_pair"
    PHYSICALLY_INFEASIBLE = "physically_infeasible"
    CONFLICT_LOSER = "conflict_loser"


def _capture_exact_tensor(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    stage: str,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise EventProposalAdapterError(
            f"{field_name} must be an exact torch.Tensor",
            failure_code="tensor_type",
            stage=stage,
            field_name=field_name,
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.layout is not torch.strided or tuple(value.shape) != shape:
        raise EventProposalAdapterError(
            f"{field_name} has an invalid layout or shape",
            failure_code="tensor_shape",
            stage=stage,
            field_name=field_name,
            expected=(torch.strided, shape),
            actual=(value.layout, tuple(value.shape)),
        )
    if value.dtype is not dtype or value.device != device or value.requires_grad:
        raise EventProposalAdapterError(
            f"{field_name} has an invalid dtype, device, or grad contract",
            failure_code="tensor_contract",
            stage=stage,
            field_name=field_name,
            expected=(dtype, device, False),
            actual=(value.dtype, value.device, value.requires_grad),
        )
    return value.detach().clone().contiguous()


def _capture_cost_tensor(
    value: object,
    *,
    shape: tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise EventProposalAdapterError(
            "cost_matrix must be an exact torch.Tensor",
            failure_code="tensor_type",
            stage="decision_capture",
            field_name="cost_matrix",
            expected=torch.Tensor,
            actual=type(value),
        )
    if (
        value.layout is not torch.strided
        or tuple(value.shape) != shape
        or value.dtype not in (torch.float32, torch.float64)
        or value.device != device
        or value.requires_grad
    ):
        raise EventProposalAdapterError(
            "cost_matrix has an invalid tensor contract",
            failure_code="tensor_contract",
            stage="decision_capture",
            field_name="cost_matrix",
            expected=(shape, "float32|float64", device, False),
            actual=(tuple(value.shape), value.dtype, value.device, value.requires_grad),
        )
    return value.detach().clone().contiguous()


def _generation_tuple(value: object, *, field_name: str) -> tuple[int, ...]:
    if type(value) is not torch.Tensor or value.dtype is not torch.int64 or value.ndim != 1:
        raise EventProposalAdapterError(
            "proposal source generation has an invalid tensor contract",
            failure_code="source_generation_contract",
            stage="decision_capture",
            field_name=field_name,
            expected="int64[E]",
            actual=(type(value), getattr(value, "dtype", None), getattr(value, "shape", None)),
        )
    return tuple(int(item) for item in value.detach().cpu().tolist())


def _require_current_publication(value: object) -> _EventRuntimeCurrentPublication:
    if type(value) is not _EventRuntimeCurrentPublication:
        raise EventProposalAdapterError(
            "proposal adapter requires the exact current P2 publication",
            failure_code="source_publication_type",
            stage="proposal_source_validate",
            expected=_EventRuntimeCurrentPublication,
            actual=type(value),
        )
    return value


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventProposalDecisionSnapshot:
    """One-call P2/window-bound feasibility and cost decision evidence."""

    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _source_publication_identity: _CurrentPublicationIdentity = field(repr=False)
    _source_window_identity: object = field(repr=False)
    episode_generations: tuple[int, ...]
    transition_generations: tuple[int, ...]
    _feasible_mask: torch.Tensor = field(repr=False)
    _cost_matrix: torch.Tensor = field(repr=False)
    _available_mask: torch.Tensor | None = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise EventProposalAdapterError(
            "decision snapshot requires the proposal-adapter factory",
            failure_code="decision_factory_required",
            stage="decision_capture",
            expected="EventProposalAdapter.capture_decision",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        profile: ResolvedEventGatedAssignmentProfile,
        publication: _EventRuntimeCurrentPublication,
        window_identity: object,
        feasible_mask: torch.Tensor,
        cost_matrix: torch.Tensor,
        available_mask: torch.Tensor | None,
        factory_capability: object,
    ) -> "EventProposalDecisionSnapshot":
        if factory_capability is not _DECISION_FACTORY_CAPABILITY:
            raise EventProposalAdapterError(
                "decision snapshot requires the proposal-adapter factory",
                failure_code="decision_factory",
                stage="decision_capture",
                expected="proposal adapter factory capability",
                actual=type(factory_capability),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_profile", profile)
        object.__setattr__(instance, "_source_publication_identity", publication.publication_identity)
        object.__setattr__(instance, "_source_window_identity", window_identity)
        object.__setattr__(
            instance,
            "episode_generations",
            _generation_tuple(publication.episode_generation, field_name="episode_generation"),
        )
        object.__setattr__(
            instance,
            "transition_generations",
            _generation_tuple(publication.transition_generation, field_name="transition_generation"),
        )
        object.__setattr__(instance, "_feasible_mask", feasible_mask.detach().clone().contiguous())
        object.__setattr__(instance, "_cost_matrix", cost_matrix.detach().clone().contiguous())
        object.__setattr__(
            instance,
            "_available_mask",
            None if available_mask is None else available_mask.detach().clone().contiguous(),
        )
        return instance

    @property
    def proposal_source_publication_identity(self) -> _CurrentPublicationIdentity:
        return self._source_publication_identity

    @property
    def proposal_source_window_identity(self) -> object:
        return self._source_window_identity

    @property
    def feasible_mask(self) -> torch.Tensor:
        return self._feasible_mask.detach().clone().contiguous()

    @property
    def cost_matrix(self) -> torch.Tensor:
        return self._cost_matrix.detach().clone().contiguous()

    @property
    def available_mask(self) -> torch.Tensor | None:
        value = self._available_mask
        return None if value is None else value.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventProposalResolution:
    """Immutable pure proposal diagnostics and task-disjoint M1 request."""

    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _source_publication_identity: _CurrentPublicationIdentity = field(repr=False)
    _source_window_identity: object = field(repr=False)
    episode_generations: tuple[int, ...]
    transition_generations: tuple[int, ...]
    interpretations: tuple[tuple[_EventProposalInterpretation, ...], ...]
    _raw_action_ids: torch.Tensor = field(repr=False)
    _decoded_proposal: torch.Tensor = field(repr=False)
    _feasible_mask: torch.Tensor = field(repr=False)
    _cost_matrix: torch.Tensor = field(repr=False)
    _structural_rejection_mask: torch.Tensor = field(repr=False)
    _feasibility_rejection_mask: torch.Tensor = field(repr=False)
    _conflict_winner_mask: torch.Tensor = field(repr=False)
    _conflict_loser_mask: torch.Tensor = field(repr=False)
    _selected_env_ids: torch.Tensor = field(repr=False)
    _requested_task_by_robot: torch.Tensor = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise EventProposalAdapterError(
            "proposal resolution requires the proposal-adapter factory",
            failure_code="resolution_factory_required",
            stage="proposal_resolve",
            expected="EventProposalAdapter.resolve",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        profile: ResolvedEventGatedAssignmentProfile,
        decision: EventProposalDecisionSnapshot,
        interpretations: tuple[tuple[_EventProposalInterpretation, ...], ...],
        raw_action_ids: torch.Tensor,
        decoded_proposal: torch.Tensor,
        structural_rejection_mask: torch.Tensor,
        feasibility_rejection_mask: torch.Tensor,
        conflict_winner_mask: torch.Tensor,
        conflict_loser_mask: torch.Tensor,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
        factory_capability: object,
    ) -> "EventProposalResolution":
        if factory_capability is not _RESOLUTION_FACTORY_CAPABILITY:
            raise EventProposalAdapterError(
                "proposal resolution requires the adapter factory",
                failure_code="resolution_factory",
                stage="proposal_resolve",
                expected="proposal adapter resolution capability",
                actual=type(factory_capability),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_profile", profile)
        object.__setattr__(instance, "_source_publication_identity", decision._source_publication_identity)
        object.__setattr__(instance, "_source_window_identity", decision._source_window_identity)
        object.__setattr__(instance, "episode_generations", decision.episode_generations)
        object.__setattr__(instance, "transition_generations", decision.transition_generations)
        object.__setattr__(instance, "interpretations", interpretations)
        for name, value in (
            ("_raw_action_ids", raw_action_ids),
            ("_decoded_proposal", decoded_proposal),
            ("_feasible_mask", decision._feasible_mask),
            ("_cost_matrix", decision._cost_matrix),
            ("_structural_rejection_mask", structural_rejection_mask),
            ("_feasibility_rejection_mask", feasibility_rejection_mask),
            ("_conflict_winner_mask", conflict_winner_mask),
            ("_conflict_loser_mask", conflict_loser_mask),
            ("_selected_env_ids", selected_env_ids),
            ("_requested_task_by_robot", requested_task_by_robot),
        ):
            object.__setattr__(instance, name, value.detach().clone().contiguous())
        return instance

    @property
    def proposal_source_publication_identity(self) -> _CurrentPublicationIdentity:
        return self._source_publication_identity

    @property
    def proposal_source_window_identity(self) -> object:
        return self._source_window_identity

    @property
    def raw_action_ids(self) -> torch.Tensor:
        return self._raw_action_ids.detach().clone().contiguous()

    @property
    def decoded_proposal(self) -> torch.Tensor:
        return self._decoded_proposal.detach().clone().contiguous()

    @property
    def feasible_mask(self) -> torch.Tensor:
        return self._feasible_mask.detach().clone().contiguous()

    @property
    def cost_matrix(self) -> torch.Tensor:
        return self._cost_matrix.detach().clone().contiguous()

    @property
    def structural_rejection_mask(self) -> torch.Tensor:
        return self._structural_rejection_mask.detach().clone().contiguous()

    @property
    def feasibility_rejection_mask(self) -> torch.Tensor:
        return self._feasibility_rejection_mask.detach().clone().contiguous()

    @property
    def conflict_winner_mask(self) -> torch.Tensor:
        return self._conflict_winner_mask.detach().clone().contiguous()

    @property
    def conflict_loser_mask(self) -> torch.Tensor:
        return self._conflict_loser_mask.detach().clone().contiguous()

    @property
    def selected_env_ids(self) -> torch.Tensor:
        return self._selected_env_ids.detach().clone().contiguous()

    @property
    def requested_task_by_robot(self) -> torch.Tensor:
        return self._requested_task_by_robot.detach().clone().contiguous()

    @property
    def claim_count(self) -> int:
        return int((self._requested_task_by_robot >= 0).sum().item())


class EventProposalAdapter:
    """Stateless except for exact profile identity; pure proposal semantics."""

    __slots__ = ("_profile",)

    def __init__(self, profile: ResolvedEventGatedAssignmentProfile) -> None:
        if type(profile) is not ResolvedEventGatedAssignmentProfile:
            raise EventProposalAdapterError(
                "proposal adapter requires the exact event profile",
                failure_code="profile_type",
                stage="adapter_construct",
                expected=ResolvedEventGatedAssignmentProfile,
                actual=type(profile),
            )
        self._profile = profile

    def capture_decision(
        self,
        *,
        current_publication: _EventRuntimeCurrentPublication,
        current_window_identity: object,
        feasible_mask: torch.Tensor,
        cost_matrix: torch.Tensor,
        available_mask: torch.Tensor | None = None,
    ) -> EventProposalDecisionSnapshot:
        publication = _require_current_publication(current_publication)
        if current_window_identity is None:
            raise EventProposalAdapterError(
                "proposal decision requires the exact OPEN window identity",
                failure_code="decision_window",
                stage="decision_capture",
                expected="opaque OPEN window identity",
                actual=None,
            )
        state = publication.lifecycle_state
        device = state.device
        shape = (state.num_envs, state.num_robots, state.num_tasks)
        feasible = _capture_exact_tensor(
            feasible_mask,
            field_name="feasible_mask",
            shape=shape,
            dtype=torch.bool,
            device=device,
            stage="decision_capture",
        )
        cost = _capture_cost_tensor(cost_matrix, shape=shape, device=device)
        available = None
        if available_mask is not None:
            available = _capture_exact_tensor(
                available_mask,
                field_name="available_mask",
                shape=shape,
                dtype=torch.bool,
                device=device,
                stage="decision_capture",
            )
            if bool((available & ~feasible).any().item()):
                raise EventProposalAdapterError(
                    "available_mask cannot make a physically infeasible pair available",
                    failure_code="available_feasibility_inconsistent",
                    stage="decision_capture",
                    field_name="available_mask",
                    expected="available_mask implies feasible_mask",
                    actual=True,
                )
        return EventProposalDecisionSnapshot._create(
            profile=self._profile,
            publication=publication,
            window_identity=current_window_identity,
            feasible_mask=feasible,
            cost_matrix=cost,
            available_mask=available,
            factory_capability=_DECISION_FACTORY_CAPABILITY,
        )

    def resolve(
        self,
        *,
        current_publication: _EventRuntimeCurrentPublication,
        current_window_identity: object,
        decision: EventProposalDecisionSnapshot,
        raw_action_ids: torch.Tensor,
        decoded_proposal: torch.Tensor,
    ) -> EventProposalResolution:
        publication = _require_current_publication(current_publication)
        self.validate_decision_current(
            current_publication=publication,
            current_window_identity=current_window_identity,
            decision=decision,
        )
        state = publication.lifecycle_state
        shape = (state.num_envs, state.num_robots)
        raw = _capture_exact_tensor(
            raw_action_ids,
            field_name="raw_action_ids",
            shape=shape,
            dtype=torch.int64,
            device=state.device,
            stage="proposal_resolve",
        )
        proposal = _capture_exact_tensor(
            decoded_proposal,
            field_name="decoded_proposal",
            shape=shape,
            dtype=torch.int64,
            device=state.device,
            stage="proposal_resolve",
        )
        num_tasks = state.num_tasks
        if bool(((raw < 0) | (raw > num_tasks)).any().item()):
            raise EventProposalAdapterError(
                "raw action IDs are outside the frozen action domain",
                failure_code="raw_action_id",
                stage="proposal_resolve",
                expected=f"0..{num_tasks}",
                actual=raw,
            )
        expected_proposal = torch.where(raw == num_tasks, torch.full_like(raw, NO_CLAIM), raw)
        if not torch.equal(expected_proposal, proposal):
            raise EventProposalAdapterError(
                "decoded proposal does not preserve the raw actor action IDs",
                failure_code="proposal_decode_mismatch",
                stage="proposal_resolve",
                expected=expected_proposal,
                actual=proposal,
            )

        task_state = state.task_state
        robot_state = state.robot_state
        ownership = state.ownership
        failed_pairs = state.cumulative_failed_pairs
        terminated = publication.terminated
        truncated = publication.truncated
        reason = state.termination_reason
        statuses = [
            [_EventProposalInterpretation.PROPOSAL_NO_CLAIM for _ in range(state.num_robots)]
            for _ in range(state.num_envs)
        ]
        structural_rejection = torch.zeros(shape, dtype=torch.bool, device=state.device)
        feasibility_rejection = torch.zeros_like(structural_rejection)
        winner_mask = torch.zeros_like(structural_rejection)
        loser_mask = torch.zeros_like(structural_rejection)
        candidates: dict[tuple[int, int], list[int]] = {}

        for env_row in range(state.num_envs):
            row_terminal = bool(terminated[env_row].item()) or bool(truncated[env_row].item())
            row_terminal = row_terminal or int(reason[env_row].item()) not in (
                int(TerminationReason.NONE),
                int(TerminationReason.TIME_LIMIT),
            )
            for robot_id in range(state.num_robots):
                action = int(proposal[env_row, robot_id].item())
                robot = int(robot_state[env_row, robot_id].item())
                owned_active = [
                    task_id
                    for task_id in range(num_tasks)
                    if int(ownership[env_row, task_id].item()) == robot_id
                    and int(task_state[env_row, task_id].item()) in _ACTIVE_TASK_STATES
                ]
                if robot == int(RobotLifecycleState.EXECUTING):
                    if len(owned_active) != 1:
                        status = _EventProposalInterpretation.INVALID_ROBOT_STATE
                    elif action == owned_active[0]:
                        status = _EventProposalInterpretation.CONTINUE_EXISTING
                    elif action == NO_CLAIM:
                        status = _EventProposalInterpretation.ILLEGAL_EXECUTING_NOOP
                    else:
                        status = _EventProposalInterpretation.INVALID_SWITCH_WHILE_EXECUTING
                elif robot == int(RobotLifecycleState.NEEDS_ASSIGNMENT):
                    if action == NO_CLAIM:
                        status = _EventProposalInterpretation.PROPOSAL_NO_CLAIM
                    elif row_terminal or owned_active:
                        status = _EventProposalInterpretation.INVALID_ROBOT_STATE
                    elif int(ownership[env_row, action].item()) != NO_CLAIM:
                        status = _EventProposalInterpretation.TASK_OWNED
                    elif int(task_state[env_row, action].item()) != int(TaskLifecycleState.AVAILABLE):
                        status = _EventProposalInterpretation.TASK_NOT_AVAILABLE
                    elif bool(failed_pairs[env_row, robot_id, action].item()):
                        status = _EventProposalInterpretation.FAILED_PAIR
                    elif not bool(decision._feasible_mask[env_row, robot_id, action].item()):
                        status = _EventProposalInterpretation.PHYSICALLY_INFEASIBLE
                    else:
                        status = _EventProposalInterpretation.NEW_CLAIM_CANDIDATE
                        candidates.setdefault((env_row, action), []).append(robot_id)
                else:
                    status = (
                        _EventProposalInterpretation.PROPOSAL_NO_CLAIM
                        if action == NO_CLAIM
                        else _EventProposalInterpretation.INVALID_ROBOT_STATE
                    )
                statuses[env_row][robot_id] = status
                if status in (
                    _EventProposalInterpretation.INVALID_SWITCH_WHILE_EXECUTING,
                    _EventProposalInterpretation.ILLEGAL_EXECUTING_NOOP,
                    _EventProposalInterpretation.INVALID_ROBOT_STATE,
                    _EventProposalInterpretation.TASK_NOT_AVAILABLE,
                    _EventProposalInterpretation.TASK_OWNED,
                    _EventProposalInterpretation.FAILED_PAIR,
                ):
                    structural_rejection[env_row, robot_id] = True
                elif status is _EventProposalInterpretation.PHYSICALLY_INFEASIBLE:
                    feasibility_rejection[env_row, robot_id] = True

        for (env_row, task_id), robot_ids in candidates.items():
            finite = [
                robot_id
                for robot_id in robot_ids
                if bool(torch.isfinite(decision._cost_matrix[env_row, robot_id, task_id]).item())
            ]
            if finite:
                winner = min(
                    finite,
                    key=lambda robot_id: (
                        float(decision._cost_matrix[env_row, robot_id, task_id].item()),
                        robot_id,
                    ),
                )
            else:
                winner = min(robot_ids)
            for robot_id in robot_ids:
                if robot_id == winner:
                    statuses[env_row][robot_id] = _EventProposalInterpretation.NEW_CLAIM_SELECTED
                    winner_mask[env_row, robot_id] = True
                else:
                    statuses[env_row][robot_id] = _EventProposalInterpretation.CONFLICT_LOSER
                    loser_mask[env_row, robot_id] = True

        env_id_values = [int(value) for value in state.env_id.detach().cpu().tolist()]
        selected_pairs = sorted(
            (
                (env_id_values[env_row], env_row)
                for env_row in range(state.num_envs)
                if bool(winner_mask[env_row].any().item())
            ),
            key=lambda item: item[0],
        )
        selected_env_ids = torch.tensor(
            [env_id for env_id, _ in selected_pairs],
            dtype=torch.int64,
            device=state.device,
        )
        requested = torch.full(
            (len(selected_pairs), state.num_robots),
            NO_CLAIM,
            dtype=torch.int64,
            device=state.device,
        )
        for selected_row, (_, env_row) in enumerate(selected_pairs):
            for robot_id in range(state.num_robots):
                if bool(winner_mask[env_row, robot_id].item()):
                    requested[selected_row, robot_id] = proposal[env_row, robot_id]
            nonnegative = requested[selected_row][requested[selected_row] >= 0]
            if nonnegative.numel() == 0 or int(torch.unique(nonnegative).numel()) != int(nonnegative.numel()):
                raise EventProposalAdapterError(
                    "proposal adapter produced an invalid conflicting M1 row",
                    failure_code="m1_invariant",
                    stage="m1_construct",
                    expected="at least one task-disjoint claim per selected env",
                    actual=requested[selected_row],
                )

        return EventProposalResolution._create(
            profile=self._profile,
            decision=decision,
            interpretations=tuple(tuple(row) for row in statuses),
            raw_action_ids=raw,
            decoded_proposal=proposal,
            structural_rejection_mask=structural_rejection,
            feasibility_rejection_mask=feasibility_rejection,
            conflict_winner_mask=winner_mask,
            conflict_loser_mask=loser_mask,
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested,
            factory_capability=_RESOLUTION_FACTORY_CAPABILITY,
        )

    def validate_decision_current(
        self,
        *,
        current_publication: _EventRuntimeCurrentPublication,
        current_window_identity: object,
        decision: EventProposalDecisionSnapshot,
    ) -> None:
        publication = _require_current_publication(current_publication)
        if type(decision) is not EventProposalDecisionSnapshot or decision._profile is not self._profile:
            raise EventProposalAdapterError(
                "proposal decision belongs to another adapter/profile",
                failure_code="decision_identity",
                stage="proposal_source_validate",
                expected=id(self._profile),
                actual=(type(decision), id(getattr(decision, "_profile", None))),
            )
        current_episode = _generation_tuple(publication.episode_generation, field_name="episode_generation")
        current_transition = _generation_tuple(
            publication.transition_generation,
            field_name="transition_generation",
        )
        if (
            publication.publication_identity is not decision._source_publication_identity
            or current_episode != decision.episode_generations
            or current_transition != decision.transition_generations
        ):
            raise EventProposalAdapterError(
                "proposal source P2 is stale and cannot be rebound",
                failure_code="stale_proposal_source",
                stage="proposal_source_validate",
                expected=(
                    id(decision._source_publication_identity),
                    decision.episode_generations,
                    decision.transition_generations,
                ),
                actual=(id(publication.publication_identity), current_episode, current_transition),
            )
        if current_window_identity is not decision._source_window_identity:
            raise EventProposalAdapterError(
                "proposal source window is stale and cannot be rebound",
                failure_code="stale_proposal_window",
                stage="proposal_source_validate",
                expected=id(decision._source_window_identity),
                actual=id(current_window_identity),
            )

    def validate_resolution_current(
        self,
        *,
        current_publication: _EventRuntimeCurrentPublication,
        current_window_identity: object,
        resolution: EventProposalResolution,
    ) -> None:
        publication = _require_current_publication(current_publication)
        if type(resolution) is not EventProposalResolution or resolution._profile is not self._profile:
            raise EventProposalAdapterError(
                "proposal resolution belongs to another adapter/profile",
                failure_code="resolution_identity",
                stage="proposal_source_validate",
                expected=id(self._profile),
                actual=(type(resolution), id(getattr(resolution, "_profile", None))),
            )
        current_episode = _generation_tuple(publication.episode_generation, field_name="episode_generation")
        current_transition = _generation_tuple(
            publication.transition_generation,
            field_name="transition_generation",
        )
        if (
            publication.publication_identity is not resolution._source_publication_identity
            or current_episode != resolution.episode_generations
            or current_transition != resolution.transition_generations
        ):
            raise EventProposalAdapterError(
                "resolved proposal source P2 is stale and cannot be rebound",
                failure_code="stale_proposal_source",
                stage="proposal_source_validate",
                expected=(
                    id(resolution._source_publication_identity),
                    resolution.episode_generations,
                    resolution.transition_generations,
                ),
                actual=(id(publication.publication_identity), current_episode, current_transition),
            )
        if current_window_identity is not resolution._source_window_identity:
            raise EventProposalAdapterError(
                "resolved proposal window is stale and cannot be rebound",
                failure_code="stale_proposal_window",
                stage="proposal_source_validate",
                expected=id(resolution._source_window_identity),
                actual=id(current_window_identity),
            )


def _committed_interpretations(
    resolution: EventProposalResolution,
    *,
    committed: bool,
) -> tuple[tuple[_EventProposalInterpretation, ...], ...]:
    if type(resolution) is not EventProposalResolution:
        raise EventProposalAdapterError(
            "committed diagnostics require an exact proposal resolution",
            failure_code="resolution_type",
            stage="proposal_commit_diagnostic",
            expected=EventProposalResolution,
            actual=type(resolution),
        )
    replacement = (
        _EventProposalInterpretation.NEW_CLAIM_COMMITTED
        if committed
        else _EventProposalInterpretation.NEW_CLAIM_SELECTED
    )
    return tuple(
        tuple(
            replacement if item is _EventProposalInterpretation.NEW_CLAIM_SELECTED else item
            for item in row
        )
        for row in resolution.interpretations
    )


__all__: tuple[str, ...] = ()
