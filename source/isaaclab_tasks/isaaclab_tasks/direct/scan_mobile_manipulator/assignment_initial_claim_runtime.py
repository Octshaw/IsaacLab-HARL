"""Pure, dormant B1 initial-claim semantics and immutable artifacts.

This module owns no StateStore, generation clock, publication lock, lifecycle
authority, environment port, resolver, or policy.  The retained lifecycle
transaction coordinator is the only factory/order owner for these private
objects.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_INITIAL_CLAIM_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_initial_claim_runtime"
)
ASSIGNMENT_INITIAL_CLAIM_RUNTIME_SOURCE_PURPOSE = (
    "pure dormant default-off initial-claim semantic foundation"
)

if __name__ != CANONICAL_ASSIGNMENT_INITIAL_CLAIM_RUNTIME_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: initial-claim runtime source must "
        "execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_INITIAL_CLAIM_RUNTIME_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

import torch

from .assignment_lifecycle_transition_contract import (
    LifecycleTransitionResult,
    RobotLifecycleState,
    TaskLifecycleState,
    TerminationReason,
)
from .assignment_profile_contract import (
    AssignmentProfileRouteError,
    ResolvedEventGatedAssignmentProfile,
)


_INT64_MAX = 2**63 - 1
NO_CLAIM = -1
_ACTIVE_TASK_STATES = (
    int(TaskLifecycleState.CLAIMED),
    int(TaskLifecycleState.NAVIGATING),
    int(TaskLifecycleState.ALIGNING),
)


class InitialClaimRuntimeError(RuntimeError):
    """Typed B1-private semantic/capability failure."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
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


def _require_event_profile(
    profile: object,
    *,
    component: str,
) -> ResolvedEventGatedAssignmentProfile:
    if type(profile) is not ResolvedEventGatedAssignmentProfile:
        raise AssignmentProfileRouteError(
            f"{component} accepts only the canonical event-gated profile",
            profile=getattr(profile, "profile_name", None),
            expected=ResolvedEventGatedAssignmentProfile,
            actual=type(profile),
            resolution_origin=getattr(profile, "resolution_origin", None),
        )
    return profile


def _capture_tensor(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    stage: str,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise InitialClaimRuntimeError(
            f"{field_name} must be an exact torch.Tensor",
            failure_code="tensor_type",
            stage=stage,
            field_name=field_name,
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.layout is not torch.strided:
        raise InitialClaimRuntimeError(
            f"{field_name} must have strided layout",
            failure_code="tensor_layout",
            stage=stage,
            field_name=field_name,
            expected=torch.strided,
            actual=value.layout,
        )
    if tuple(value.shape) != shape:
        raise InitialClaimRuntimeError(
            f"{field_name} has the wrong shape",
            failure_code="shape",
            stage=stage,
            field_name=field_name,
            expected=shape,
            actual=tuple(value.shape),
        )
    if value.dtype is not dtype:
        raise InitialClaimRuntimeError(
            f"{field_name} has the wrong dtype",
            failure_code="dtype",
            stage=stage,
            field_name=field_name,
            expected=dtype,
            actual=value.dtype,
        )
    if value.device != device:
        raise InitialClaimRuntimeError(
            f"{field_name} is on the wrong device",
            failure_code="device",
            stage=stage,
            field_name=field_name,
            expected=device,
            actual=value.device,
        )
    if value.requires_grad:
        raise InitialClaimRuntimeError(
            f"{field_name} must not require gradients",
            failure_code="requires_grad",
            stage=stage,
            field_name=field_name,
            expected=False,
            actual=True,
        )
    return value.detach().clone().contiguous()


def _tensor_digest(*values: torch.Tensor) -> bytes:
    digest = sha256()
    for value in values:
        captured = value.detach().cpu().contiguous()
        digest.update(str(captured.dtype).encode("ascii"))
        digest.update(repr(tuple(captured.shape)).encode("ascii"))
        digest.update(captured.numpy().tobytes())
    return digest.digest()


class _CurrentPublicationProvenanceKind(Enum):
    PREBOOTSTRAP = "prebootstrap"
    FINALIZED_LIFECYCLE_TRANSITION = "finalized_lifecycle_transition"
    CANONICAL_EPISODE_RESET = "canonical_episode_reset"
    ASSIGNMENT_COMMIT = "assignment_commit"


class _InitialClaimSourceKind(Enum):
    FINALIZED_LIFECYCLE_TRANSITION = "finalized_lifecycle_transition"
    CANONICAL_EPISODE_RESET = "canonical_episode_reset"
    POST_ASSIGNMENT = "post_assignment"


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _CurrentPublicationIdentity:
    serial: int
    _domain_identity: object = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        serial: int,
        domain_identity: object,
        factory_capability: object,
    ) -> "_CurrentPublicationIdentity":
        if type(serial) is not int or not 0 <= serial <= _INT64_MAX:
            raise InitialClaimRuntimeError(
                "publication serial must be an exact nonnegative int64",
                failure_code="publication_identity",
                stage="publication_prepare",
                expected=f"0..{_INT64_MAX}",
                actual=serial,
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "serial", serial)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _CurrentPublicationProvenance:
    kind: _CurrentPublicationProvenanceKind
    _lifecycle_result: object | None = field(repr=False)
    _assignment_artifact: object | None = field(repr=False)
    _immediate_predecessor_identity: _CurrentPublicationIdentity | None = field(
        repr=False
    )
    _root_kind: _CurrentPublicationProvenanceKind
    _root_publication_identity: _CurrentPublicationIdentity
    _root_lifecycle_result: object | None = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        kind: _CurrentPublicationProvenanceKind,
        lifecycle_result: object | None,
        assignment_artifact: object | None,
        immediate_predecessor_identity: _CurrentPublicationIdentity | None,
        root_kind: _CurrentPublicationProvenanceKind,
        root_publication_identity: _CurrentPublicationIdentity,
        root_lifecycle_result: object | None,
        factory_capability: object,
    ) -> "_CurrentPublicationProvenance":
        if (
            type(kind) is not _CurrentPublicationProvenanceKind
            or type(root_kind) is not _CurrentPublicationProvenanceKind
            or type(root_publication_identity) is not _CurrentPublicationIdentity
            or root_publication_identity._factory_capability is not factory_capability
        ):
            raise InitialClaimRuntimeError(
                "provenance lacks exact enum/root factory identity",
                failure_code="provenance_factory",
                stage="publication_prepare",
                expected="coordinator-issued provenance",
                actual=(type(kind), type(root_kind), type(root_publication_identity)),
            )
        if kind is _CurrentPublicationProvenanceKind.PREBOOTSTRAP:
            valid = (
                lifecycle_result is None
                and assignment_artifact is None
                and immediate_predecessor_identity is None
                and root_kind is kind
                and root_lifecycle_result is None
            )
        elif kind is _CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION:
            valid = (
                type(lifecycle_result) is LifecycleTransitionResult
                and assignment_artifact is None
                and immediate_predecessor_identity is None
                and root_kind is kind
                and root_lifecycle_result is lifecycle_result
            )
        elif kind is _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET:
            valid = (
                lifecycle_result is None
                and assignment_artifact is None
                and immediate_predecessor_identity is None
                and root_kind is kind
                and root_lifecycle_result is None
            )
        else:
            valid = (
                lifecycle_result is None
                and type(assignment_artifact) is EffectiveAssignmentCommitArtifact
                and type(immediate_predecessor_identity) is _CurrentPublicationIdentity
                and immediate_predecessor_identity._factory_capability
                is factory_capability
                and root_kind
                in (
                    _CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION,
                    _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
                )
                and (
                    root_lifecycle_result is not None
                    if root_kind
                    is _CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION
                    else root_lifecycle_result is None
                )
            )
        if not valid:
            raise InitialClaimRuntimeError(
                "publication provenance variant fields are incoherent",
                failure_code="provenance_variant",
                stage="publication_prepare",
                expected=kind,
                actual="incoherent variant fields",
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "kind", kind)
        object.__setattr__(instance, "_lifecycle_result", lifecycle_result)
        object.__setattr__(instance, "_assignment_artifact", assignment_artifact)
        object.__setattr__(
            instance,
            "_immediate_predecessor_identity",
            immediate_predecessor_identity,
        )
        object.__setattr__(instance, "_root_kind", root_kind)
        object.__setattr__(instance, "_root_publication_identity", root_publication_identity)
        object.__setattr__(instance, "_root_lifecycle_result", root_lifecycle_result)
        return instance

    @property
    def lifecycle_result(self) -> object | None:
        return self._lifecycle_result

    @property
    def assignment_artifact(self) -> object | None:
        return self._assignment_artifact

    @property
    def immediate_predecessor_identity(self) -> _CurrentPublicationIdentity | None:
        return self._immediate_predecessor_identity

    @property
    def root_kind(self) -> _CurrentPublicationProvenanceKind:
        return self._root_kind

    @property
    def root_publication_identity(self) -> _CurrentPublicationIdentity:
        return self._root_publication_identity

    @property
    def root_lifecycle_result(self) -> object | None:
        return self._root_lifecycle_result


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EventRuntimeCurrentPublication:
    """The sole full-domain fresh-current P2 publication."""

    store_version: int
    _lifecycle_view: object = field(repr=False)
    _publication_identity: _CurrentPublicationIdentity = field(repr=False)
    _provenance: tuple[_CurrentPublicationProvenance, ...] = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        lifecycle_view: object,
        publication_identity: _CurrentPublicationIdentity,
        provenance: tuple[_CurrentPublicationProvenance, ...],
        factory_capability: object,
    ) -> "_EventRuntimeCurrentPublication":
        if (
            type(publication_identity) is not _CurrentPublicationIdentity
            or publication_identity._factory_capability is not factory_capability
            or type(provenance) is not tuple
            or not provenance
            or any(type(item) is not _CurrentPublicationProvenance for item in provenance)
        ):
            raise InitialClaimRuntimeError(
                "P2 publication requires exact coordinator-issued identity/provenance",
                failure_code="publication_factory",
                stage="publication_prepare",
                expected="coordinator-issued full-domain publication",
                actual=(type(publication_identity), type(provenance)),
            )
        store_version = getattr(lifecycle_view, "store_version", None)
        env_id = getattr(lifecycle_view, "env_id", None)
        if (
            type(store_version) is not int
            or type(env_id) is not torch.Tensor
            or int(env_id.numel()) != len(provenance)
        ):
            raise InitialClaimRuntimeError(
                "P2 lifecycle view/domain binding is invalid",
                failure_code="publication_view_binding",
                stage="publication_prepare",
                expected="lifecycle view with one provenance per env row",
                actual=(store_version, getattr(env_id, "shape", None), len(provenance)),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "store_version", store_version)
        object.__setattr__(instance, "_lifecycle_view", lifecycle_view)
        object.__setattr__(instance, "_publication_identity", publication_identity)
        object.__setattr__(instance, "_provenance", provenance)
        return instance

    @property
    def lifecycle_view(self) -> object:
        return self._lifecycle_view

    @property
    def publication_identity(self) -> _CurrentPublicationIdentity:
        return self._publication_identity

    @property
    def provenance(self) -> tuple[_CurrentPublicationProvenance, ...]:
        return self._provenance

    # Immutable compatibility projections.  They do not create a second current
    # pointer; every value comes from the one nested lifecycle view.
    @property
    def lifecycle_state(self) -> object:
        return self._lifecycle_view.lifecycle_state

    @property
    def env_id(self) -> torch.Tensor:
        return self._lifecycle_view.env_id

    @property
    def episode_generation(self) -> torch.Tensor:
        return self._lifecycle_view.episode_generation

    @property
    def transition_generation(self) -> torch.Tensor:
        return self._lifecycle_view.transition_generation

    @property
    def terminated(self) -> torch.Tensor:
        return self._lifecycle_view.terminated

    @property
    def truncated(self) -> torch.Tensor:
        return self._lifecycle_view.truncated

    @property
    def result(self) -> object | None:
        return self._lifecycle_view.result


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _InitialClaimSourceBaseline:
    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _domain_identity: object = field(repr=False)
    _source_publication: _EventRuntimeCurrentPublication = field(repr=False)
    _source_publication_identity: _CurrentPublicationIdentity = field(repr=False)
    _store_identity: object = field(repr=False)
    source_store_version: int
    _selected_env_ids: torch.Tensor = field(repr=False)
    selected_rows: tuple[int, ...]
    _episode_generation: torch.Tensor = field(repr=False)
    _transition_generation: torch.Tensor = field(repr=False)
    _task_state: torch.Tensor = field(repr=False)
    _robot_state: torch.Tensor = field(repr=False)
    _ownership: torch.Tensor = field(repr=False)
    _cumulative_failed_pairs: torch.Tensor = field(repr=False)
    _completion_count: torch.Tensor = field(repr=False)
    _termination_reason: torch.Tensor = field(repr=False)
    _terminated: torch.Tensor = field(repr=False)
    _truncated: torch.Tensor = field(repr=False)
    source_kinds: tuple[_InitialClaimSourceKind, ...]
    source_provenance: tuple[_CurrentPublicationProvenance, ...]
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        profile: ResolvedEventGatedAssignmentProfile,
        domain_identity: object,
        source_publication: _EventRuntimeCurrentPublication,
        store_identity: object,
        selected_env_ids: torch.Tensor,
        selected_rows: tuple[int, ...],
        source_kinds: tuple[_InitialClaimSourceKind, ...],
        factory_capability: object,
    ) -> "_InitialClaimSourceBaseline":
        view = source_publication.lifecycle_view
        state = view.lifecycle_state
        selected = selected_env_ids.detach().clone().contiguous()
        instance = object.__new__(cls)
        object.__setattr__(instance, "_profile", profile)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_source_publication", source_publication)
        object.__setattr__(instance, "_source_publication_identity", source_publication.publication_identity)
        object.__setattr__(instance, "_store_identity", store_identity)
        object.__setattr__(instance, "source_store_version", source_publication.store_version)
        object.__setattr__(instance, "_selected_env_ids", selected)
        object.__setattr__(instance, "selected_rows", selected_rows)
        for name, value in (
            ("_episode_generation", view.episode_generation),
            ("_transition_generation", view.transition_generation),
            ("_task_state", state.task_state),
            ("_robot_state", state.robot_state),
            ("_ownership", state.ownership),
            ("_cumulative_failed_pairs", state.cumulative_failed_pairs),
            ("_completion_count", state.completion_count),
            ("_termination_reason", state.termination_reason),
            ("_terminated", view.terminated),
            ("_truncated", view.truncated),
        ):
            object.__setattr__(instance, name, value.detach().clone().contiguous())
        object.__setattr__(instance, "source_kinds", source_kinds)
        object.__setattr__(
            instance,
            "source_provenance",
            tuple(source_publication.provenance[row] for row in selected_rows),
        )
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance

    @property
    def selected_env_ids(self) -> torch.Tensor:
        return self._selected_env_ids.detach().clone().contiguous()

    @property
    def source_publication(self) -> _EventRuntimeCurrentPublication:
        return self._source_publication


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _InitialClaimRequestContext:
    token: int
    _domain_identity: object = field(repr=False)
    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _baseline_identity: _InitialClaimSourceBaseline = field(repr=False)
    _request_identity: object = field(repr=False)
    selected_env_ids: tuple[int, ...]
    _request_digest: bytes = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        token: int,
        domain_identity: object,
        profile: ResolvedEventGatedAssignmentProfile,
        baseline: _InitialClaimSourceBaseline,
        request_identity: object,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
        factory_capability: object,
    ) -> "_InitialClaimRequestContext":
        instance = object.__new__(cls)
        object.__setattr__(instance, "token", token)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_profile", profile)
        object.__setattr__(instance, "_baseline_identity", baseline)
        object.__setattr__(instance, "_request_identity", request_identity)
        object.__setattr__(instance, "selected_env_ids", tuple(int(v) for v in selected_env_ids.cpu().tolist()))
        object.__setattr__(instance, "_request_digest", _tensor_digest(selected_env_ids, requested_task_by_robot))
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class InitialClaimRequest:
    """Opaque immutable request issued only by the retained domain capability."""

    _context: _InitialClaimRequestContext = field(repr=False)
    _baseline: _InitialClaimSourceBaseline = field(repr=False)
    _selected_env_ids: torch.Tensor = field(repr=False)
    _requested_task_by_robot: torch.Tensor = field(repr=False)
    _request_identity: object = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise InitialClaimRuntimeError(
            "InitialClaimRequest requires the retained-domain factory",
            failure_code="request_factory_required",
            stage="request_issue",
            expected="initial_claim_port.prepare_initial_claim",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        context: _InitialClaimRequestContext,
        baseline: _InitialClaimSourceBaseline,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
        request_identity: object,
        factory_capability: object,
    ) -> "InitialClaimRequest":
        if (
            type(context) is not _InitialClaimRequestContext
            or context._factory_capability is not factory_capability
            or context._baseline_identity is not baseline
            or context._request_identity is not request_identity
        ):
            raise InitialClaimRuntimeError(
                "request/context lacks the retained factory binding",
                failure_code="request_factory",
                stage="request_issue",
                expected="coordinator-issued context",
                actual=type(context),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_context", context)
        object.__setattr__(instance, "_baseline", baseline)
        object.__setattr__(instance, "_selected_env_ids", selected_env_ids.detach().clone().contiguous())
        object.__setattr__(instance, "_requested_task_by_robot", requested_task_by_robot.detach().clone().contiguous())
        object.__setattr__(instance, "_request_identity", request_identity)
        return instance

    @property
    def token(self) -> int:
        return self._context.token

    @property
    def selected_env_ids(self) -> torch.Tensor:
        return self._selected_env_ids.detach().clone().contiguous()

    @property
    def requested_task_by_robot(self) -> torch.Tensor:
        return self._requested_task_by_robot.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, eq=False)
class _InitialClaimCandidate:
    _store_identity: object = field(repr=False)
    store_version: int
    selected_rows: tuple[int, ...]
    task_state: torch.Tensor = field(repr=False)
    robot_state: torch.Tensor = field(repr=False)
    ownership: torch.Tensor = field(repr=False)
    cumulative_failed_pairs: torch.Tensor = field(repr=False)
    completion_count: torch.Tensor = field(repr=False)
    termination_reason: torch.Tensor = field(repr=False)
    effective_task_by_robot: torch.Tensor = field(repr=False)


class InitialClaimDeriver:
    """Pure semantic validator/deriver with no mutation capability."""

    __slots__ = ("_profile",)

    def __init__(self, profile: ResolvedEventGatedAssignmentProfile) -> None:
        self._profile = _require_event_profile(profile, component="InitialClaimDeriver")

    def derive_candidate(self, request: InitialClaimRequest) -> _InitialClaimCandidate:
        if type(request) is not InitialClaimRequest:
            raise InitialClaimRuntimeError(
                "claim derivation requires an exact issued request",
                failure_code="request_type",
                stage="claim_derivation",
                expected=InitialClaimRequest,
                actual=type(request),
            )
        baseline = request._baseline
        if baseline._profile is not self._profile:
            raise InitialClaimRuntimeError(
                "claim request belongs to another profile",
                failure_code="profile_identity",
                stage="claim_derivation",
                expected=id(self._profile),
                actual=id(baseline._profile),
            )
        task = baseline._task_state.detach().clone().contiguous()
        robot = baseline._robot_state.detach().clone().contiguous()
        owner = baseline._ownership.detach().clone().contiguous()
        failed = baseline._cumulative_failed_pairs.detach().clone().contiguous()
        requested = request._requested_task_by_robot

        for input_row, domain_row in enumerate(baseline.selected_rows):
            env_value = int(baseline._selected_env_ids[input_row].item())
            if (
                int(baseline._termination_reason[domain_row].item())
                != int(TerminationReason.NONE)
                or bool(baseline._terminated[domain_row].item())
                or bool(baseline._truncated[domain_row].item())
            ):
                raise InitialClaimRuntimeError(
                    "a terminal/truncated source row cannot claim",
                    failure_code="terminal_source",
                    stage="claim_derivation",
                    env_id=env_value,
                    expected=(int(TerminationReason.NONE), False, False),
                    actual=(
                        int(baseline._termination_reason[domain_row].item()),
                        bool(baseline._terminated[domain_row].item()),
                        bool(baseline._truncated[domain_row].item()),
                    ),
                )
            seen_tasks: set[int] = set()
            for robot_id, task_value in enumerate(requested[input_row].tolist()):
                task_id = int(task_value)
                if task_id == NO_CLAIM:
                    continue
                if task_id in seen_tasks:
                    raise InitialClaimRuntimeError(
                        "one task cannot be claimed by two robots in one row",
                        failure_code="duplicate_task",
                        stage="claim_derivation",
                        env_id=env_value,
                        actual=task_id,
                    )
                seen_tasks.add(task_id)
                robot_state = int(robot[domain_row, robot_id].item())
                if robot_state != int(RobotLifecycleState.NEEDS_ASSIGNMENT):
                    raise InitialClaimRuntimeError(
                        "claim robot is not NEEDS_ASSIGNMENT",
                        failure_code="robot_not_assignable",
                        stage="claim_derivation",
                        env_id=env_value,
                        expected=int(RobotLifecycleState.NEEDS_ASSIGNMENT),
                        actual={"robot": robot_id, "state": robot_state},
                    )
                if bool((owner[domain_row] == robot_id).any().item()):
                    raise InitialClaimRuntimeError(
                        "claim robot already owns an active task",
                        failure_code="robot_already_owns",
                        stage="claim_derivation",
                        env_id=env_value,
                        actual=robot_id,
                    )
                task_state = int(task[domain_row, task_id].item())
                if task_state != int(TaskLifecycleState.AVAILABLE) or int(
                    owner[domain_row, task_id].item()
                ) != -1:
                    raise InitialClaimRuntimeError(
                        "claim task is not exact AVAILABLE/unowned",
                        failure_code="task_not_available",
                        stage="claim_derivation",
                        env_id=env_value,
                        expected=(int(TaskLifecycleState.AVAILABLE), -1),
                        actual=(task_id, task_state, int(owner[domain_row, task_id].item())),
                    )
                if bool(failed[domain_row, robot_id, task_id].item()):
                    raise InitialClaimRuntimeError(
                        "claim pair is permanently failed",
                        failure_code="failed_pair",
                        stage="claim_derivation",
                        env_id=env_value,
                        actual=(robot_id, task_id),
                    )
            for robot_id, task_value in enumerate(requested[input_row].tolist()):
                task_id = int(task_value)
                if task_id == NO_CLAIM:
                    continue
                task[domain_row, task_id] = int(TaskLifecycleState.CLAIMED)
                owner[domain_row, task_id] = robot_id

            available = task[domain_row] == int(TaskLifecycleState.AVAILABLE)
            unowned = owner[domain_row] == -1
            active = torch.zeros_like(task[domain_row], dtype=torch.bool)
            for active_state in _ACTIVE_TASK_STATES:
                active |= task[domain_row] == active_state
            for robot_id in range(int(robot.shape[1])):
                if int(baseline._robot_state[domain_row, robot_id].item()) == int(
                    RobotLifecycleState.UNAVAILABLE
                ):
                    robot[domain_row, robot_id] = int(RobotLifecycleState.UNAVAILABLE)
                elif bool((active & (owner[domain_row] == robot_id)).any().item()):
                    robot[domain_row, robot_id] = int(RobotLifecycleState.EXECUTING)
                elif bool((available & unowned & ~failed[domain_row, robot_id]).any().item()):
                    robot[domain_row, robot_id] = int(RobotLifecycleState.NEEDS_ASSIGNMENT)
                else:
                    robot[domain_row, robot_id] = int(RobotLifecycleState.WAITING_FOR_TASK)

        return _InitialClaimCandidate(
            _store_identity=baseline._store_identity,
            store_version=baseline.source_store_version,
            selected_rows=baseline.selected_rows,
            task_state=task,
            robot_state=robot,
            ownership=owner,
            cumulative_failed_pairs=baseline._cumulative_failed_pairs.detach().clone().contiguous(),
            completion_count=baseline._completion_count.detach().clone().contiguous(),
            termination_reason=baseline._termination_reason.detach().clone().contiguous(),
            effective_task_by_robot=request._requested_task_by_robot.detach().clone().contiguous(),
        )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EffectiveAssignmentCommitArtifact:
    """Immutable/no-alias B1 claim history; never a lifecycle event/result."""

    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _domain_identity: object = field(repr=False)
    _request: InitialClaimRequest = field(repr=False)
    _request_context: _InitialClaimRequestContext = field(repr=False)
    token: int
    _source_publication: _EventRuntimeCurrentPublication = field(repr=False)
    _source_publication_identity: _CurrentPublicationIdentity = field(repr=False)
    source_store_version: int
    committed_store_version: int
    source_provenance_kinds: tuple[_InitialClaimSourceKind, ...]
    _selected_env_ids: torch.Tensor = field(repr=False)
    _episode_generation: torch.Tensor = field(repr=False)
    _transition_generation: torch.Tensor = field(repr=False)
    _requested_task_by_robot: torch.Tensor = field(repr=False)
    _effective_task_by_robot: torch.Tensor = field(repr=False)
    _pre_task_state: torch.Tensor = field(repr=False)
    _pre_robot_state: torch.Tensor = field(repr=False)
    _pre_ownership: torch.Tensor = field(repr=False)
    _post_task_state: torch.Tensor = field(repr=False)
    _post_robot_state: torch.Tensor = field(repr=False)
    _post_ownership: torch.Tensor = field(repr=False)
    immediate_predecessor_provenance: tuple[_CurrentPublicationProvenance, ...]
    root_provenance: tuple[_CurrentPublicationProvenance, ...]

    @classmethod
    def _create(
        cls,
        *,
        profile: ResolvedEventGatedAssignmentProfile,
        domain_identity: object,
        request: InitialClaimRequest,
        committed_store_version: int,
        candidate: _InitialClaimCandidate,
        factory_capability: object,
    ) -> "EffectiveAssignmentCommitArtifact":
        baseline = request._baseline
        if baseline._factory_capability is not factory_capability:
            raise InitialClaimRuntimeError(
                "artifact factory lacks request/baseline capability",
                failure_code="artifact_factory",
                stage="claim_prepare",
                expected="coordinator factory",
                actual="foreign capability",
            )
        roots_list: list[_CurrentPublicationProvenance] = []
        for input_row, provenance in enumerate(baseline.source_provenance):
            if provenance.kind in (
                _CurrentPublicationProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION,
                _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
            ):
                roots_list.append(provenance)
                continue
            prior = provenance.assignment_artifact
            if type(prior) is not EffectiveAssignmentCommitArtifact:
                raise InitialClaimRuntimeError(
                    "post-assignment provenance lacks its immediate artifact",
                    failure_code="artifact_provenance",
                    stage="claim_prepare",
                    expected=EffectiveAssignmentCommitArtifact,
                    actual=type(prior),
                )
            env_value = int(baseline._selected_env_ids[input_row].item())
            prior_envs = tuple(int(value) for value in prior._selected_env_ids.cpu().tolist())
            if env_value not in prior_envs:
                raise InitialClaimRuntimeError(
                    "prior assignment artifact does not cover the source row",
                    failure_code="artifact_provenance",
                    stage="claim_prepare",
                    env_id=env_value,
                    expected="env in immediate artifact",
                    actual=prior_envs,
                )
            roots_list.append(prior.root_provenance[prior_envs.index(env_value)])
        roots = tuple(roots_list)
        instance = object.__new__(cls)
        object.__setattr__(instance, "_profile", profile)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_request", request)
        object.__setattr__(instance, "_request_context", request._context)
        object.__setattr__(instance, "token", request.token)
        object.__setattr__(instance, "_source_publication", baseline.source_publication)
        object.__setattr__(
            instance,
            "_source_publication_identity",
            baseline._source_publication_identity,
        )
        object.__setattr__(instance, "source_store_version", baseline.source_store_version)
        object.__setattr__(instance, "committed_store_version", committed_store_version)
        object.__setattr__(instance, "source_provenance_kinds", baseline.source_kinds)
        for name, value in (
            ("_selected_env_ids", request._selected_env_ids),
            ("_episode_generation", baseline._episode_generation),
            ("_transition_generation", baseline._transition_generation),
            ("_requested_task_by_robot", request._requested_task_by_robot),
            ("_effective_task_by_robot", candidate.effective_task_by_robot),
            ("_pre_task_state", baseline._task_state),
            ("_pre_robot_state", baseline._robot_state),
            ("_pre_ownership", baseline._ownership),
            ("_post_task_state", candidate.task_state),
            ("_post_robot_state", candidate.robot_state),
            ("_post_ownership", candidate.ownership),
        ):
            object.__setattr__(instance, name, value.detach().clone().contiguous())
        object.__setattr__(instance, "immediate_predecessor_provenance", baseline.source_provenance)
        object.__setattr__(instance, "root_provenance", roots)
        return instance

    @property
    def request(self) -> InitialClaimRequest:
        return self._request

    @property
    def request_context(self) -> _InitialClaimRequestContext:
        return self._request_context

    @property
    def source_publication(self) -> _EventRuntimeCurrentPublication:
        return self._source_publication

    @property
    def source_publication_identity(self) -> _CurrentPublicationIdentity:
        return self._source_publication_identity

    @property
    def selected_env_ids(self) -> torch.Tensor:
        return self._selected_env_ids.detach().clone().contiguous()

    @property
    def episode_generation(self) -> torch.Tensor:
        return self._episode_generation.detach().clone().contiguous()

    @property
    def transition_generation(self) -> torch.Tensor:
        return self._transition_generation.detach().clone().contiguous()

    @property
    def requested_task_by_robot(self) -> torch.Tensor:
        return self._requested_task_by_robot.detach().clone().contiguous()

    @property
    def effective_task_by_robot(self) -> torch.Tensor:
        return self._effective_task_by_robot.detach().clone().contiguous()

    @property
    def pre_state(self) -> Mapping[str, torch.Tensor]:
        return MappingProxyType(
            {
                "task_state": self._pre_task_state.detach().clone().contiguous(),
                "robot_state": self._pre_robot_state.detach().clone().contiguous(),
                "ownership": self._pre_ownership.detach().clone().contiguous(),
            }
        )

    @property
    def post_state(self) -> Mapping[str, torch.Tensor]:
        return MappingProxyType(
            {
                "task_state": self._post_task_state.detach().clone().contiguous(),
                "robot_state": self._post_robot_state.detach().clone().contiguous(),
                "ownership": self._post_ownership.detach().clone().contiguous(),
            }
        )


__all__: tuple[str, ...] = ()
