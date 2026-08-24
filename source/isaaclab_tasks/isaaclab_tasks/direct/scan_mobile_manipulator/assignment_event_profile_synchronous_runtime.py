"""B-private synchronous orchestration for the exact event-profile runtime.

This module owns no lifecycle, Store, publication, fence, poison, resolver,
scheduler, policy, terminal-consumer, wrapper, or HARL authority.  It sequences
only narrow retained-domain ports around one synchronous environment call.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_SYNCHRONOUS_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_synchronous_runtime"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_SYNCHRONOUS_RUNTIME_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event synchronous runtime source must "
        "execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_SYNCHRONOUS_RUNTIME_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import torch

from .assignment_event_profile_runtime_domain import (
    _EventProfileInterStepFenceReadPort,
    _EventProfileLifecycleCurrentReadPort,
    _EventProfilePhysicalStepAdmissionPort,
    _EventProfileProductionInitialClaimPort,
    _EventProfileStandaloneResetAdmissionPort,
    _EventProfileTerminalConsumerPort,
)
from .assignment_initial_claim_runtime import (
    EffectiveAssignmentCommitArtifact,
    _EventRuntimeCurrentPublication,
)
from .assignment_interstep_claim_window_runtime import (
    _ClaimWindowFenceView,
    _PhysicalStepAdmission,
)
from .assignment_lifecycle_transaction_runtime import (
    _TerminalHandoffArtifact,
    _TerminalTransitionKey,
)
from .assignment_lifecycle_transition_contract import TaskLifecycleState


_ACTIVE_TASK_STATES = (
    int(TaskLifecycleState.CLAIMED),
    int(TaskLifecycleState.NAVIGATING),
    int(TaskLifecycleState.ALIGNING),
)
_NO_CLAIM_STEP_RECEIPT_FACTORY_CAPABILITY = object()


class EventProfileSynchronousRuntimeError(RuntimeError):
    """Typed B-private orchestration/projection failure."""

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


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EventProfileNoClaimStepReceipt:
    """Exact O1 receipt for one admitted no-new-claim physical step."""

    environment_result: object = field(repr=False)
    admitted_publication: _EventRuntimeCurrentPublication = field(repr=False)
    admitted_control_assignment: torch.Tensor = field(repr=False)
    completed_window: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        environment_result: object,
        admitted_publication: _EventRuntimeCurrentPublication,
        admitted_control_assignment: torch.Tensor,
        completed_window: object,
        factory_capability: object,
    ) -> "_EventProfileNoClaimStepReceipt":
        if factory_capability is not _NO_CLAIM_STEP_RECEIPT_FACTORY_CAPABILITY:
            raise EventProfileSynchronousRuntimeError(
                "no-claim step receipt requires the exact O1 factory",
                failure_code="step_receipt_factory",
                stage="step_receipt_create",
                expected="O1 factory capability",
                actual=type(factory_capability),
            )
        if type(admitted_publication) is not _EventRuntimeCurrentPublication:
            raise EventProfileSynchronousRuntimeError(
                "no-claim step receipt requires the exact admitted P2",
                failure_code="step_receipt_publication",
                stage="step_receipt_create",
                expected=_EventRuntimeCurrentPublication,
                actual=type(admitted_publication),
            )
        if type(admitted_control_assignment) is not torch.Tensor:
            raise EventProfileSynchronousRuntimeError(
                "no-claim step receipt requires an exact controller assignment tensor",
                failure_code="step_receipt_assignment",
                stage="step_receipt_create",
                expected=torch.Tensor,
                actual=type(admitted_control_assignment),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "environment_result", environment_result)
        object.__setattr__(instance, "admitted_publication", admitted_publication)
        object.__setattr__(
            instance,
            "admitted_control_assignment",
            admitted_control_assignment.detach().clone().contiguous(),
        )
        object.__setattr__(instance, "completed_window", completed_window)
        return instance


def _derive_control_assignment_from_admitted_publication(
    admission: _PhysicalStepAdmission,
) -> torch.Tensor:
    """Invert exact Ak-bound P2 ownership into controller ``[E,M]`` form."""

    if type(admission) is not _PhysicalStepAdmission:
        raise EventProfileSynchronousRuntimeError(
            "control assignment requires an exact physical-step admission",
            failure_code="control_admission_type",
            stage="control_assignment_projection",
            expected=_PhysicalStepAdmission,
            actual=type(admission),
        )
    publication = admission.admitted_publication
    if type(publication) is not _EventRuntimeCurrentPublication:
        raise EventProfileSynchronousRuntimeError(
            "physical-step admission lost its exact P2 publication",
            failure_code="control_publication_type",
            stage="control_assignment_projection",
            expected=_EventRuntimeCurrentPublication,
            actual=type(publication),
        )
    state = publication.lifecycle_state
    task_state = state.task_state
    robot_state = state.robot_state
    ownership = state.ownership
    if (
        type(task_state) is not torch.Tensor
        or type(robot_state) is not torch.Tensor
        or type(ownership) is not torch.Tensor
        or task_state.dtype != torch.int64
        or robot_state.dtype != torch.int64
        or ownership.dtype != torch.int64
        or task_state.ndim != 2
        or robot_state.ndim != 2
        or ownership.shape != task_state.shape
        or task_state.shape[0] != robot_state.shape[0]
        or task_state.device != robot_state.device
        or ownership.device != task_state.device
    ):
        raise EventProfileSynchronousRuntimeError(
            "Ak-bound lifecycle state has an invalid fixed-domain tensor layout",
            failure_code="control_state_layout",
            stage="control_assignment_projection",
            expected="int64 task[E,N], robot[E,M], ownership[E,N] on one device",
            actual=(
                getattr(task_state, "shape", None),
                getattr(robot_state, "shape", None),
                getattr(ownership, "shape", None),
            ),
        )

    num_envs, num_tasks = task_state.shape
    num_robots = int(robot_state.shape[1])
    assignment = torch.full(
        (num_envs, num_robots),
        -1,
        dtype=torch.int64,
        device=task_state.device,
    )
    active = torch.zeros_like(task_state, dtype=torch.bool)
    for state_value in _ACTIVE_TASK_STATES:
        active |= task_state == state_value
    owned = ownership >= 0
    if bool((owned & ~active).any().item()) or bool((active & ~owned).any().item()):
        raise EventProfileSynchronousRuntimeError(
            "ownership and active task state are inconsistent",
            failure_code="control_ownership_state",
            stage="control_assignment_projection",
            expected="ownership exists exactly for active tasks",
            actual="inactive-owned or active-unowned task",
        )
    if bool(((ownership < -1) | (ownership >= num_robots)).any().item()):
        raise EventProfileSynchronousRuntimeError(
            "ownership contains a robot id outside the fixed domain",
            failure_code="control_owner_range",
            stage="control_assignment_projection",
            expected=f"-1 or 0..{num_robots - 1}",
            actual=(int(ownership.min().item()), int(ownership.max().item())),
        )

    for env_row in range(num_envs):
        for task_id in range(num_tasks):
            if not bool(active[env_row, task_id].item()):
                continue
            robot_id = int(ownership[env_row, task_id].item())
            if int(assignment[env_row, robot_id].item()) != -1:
                raise EventProfileSynchronousRuntimeError(
                    "one robot owns more than one active task",
                    failure_code="control_robot_multi_owner",
                    stage="control_assignment_projection",
                    expected="at most one active task per robot",
                    actual=(env_row, robot_id),
                )
            assignment[env_row, robot_id] = task_id
    return assignment.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventProfileSynchronousRuntimeCoordinator:
    """HARL-independent O1 sequencing over narrow runtime capabilities."""

    _environment: object = field(repr=False)
    _current_read_port: _EventProfileLifecycleCurrentReadPort = field(repr=False)
    _production_claim_port: _EventProfileProductionInitialClaimPort = field(repr=False)
    _physical_step_admission_port: _EventProfilePhysicalStepAdmissionPort = field(repr=False)
    _standalone_reset_admission_port: _EventProfileStandaloneResetAdmissionPort = field(repr=False)
    _terminal_consumer_port: _EventProfileTerminalConsumerPort = field(repr=False)
    _fence_read_port: _EventProfileInterStepFenceReadPort | None = field(repr=False)
    _stage_observer: Callable[[str, object | None], None] | None = field(repr=False)

    def __init__(
        self,
        *,
        environment: object,
        current_read_port: _EventProfileLifecycleCurrentReadPort,
        production_claim_port: _EventProfileProductionInitialClaimPort,
        physical_step_admission_port: _EventProfilePhysicalStepAdmissionPort,
        standalone_reset_admission_port: _EventProfileStandaloneResetAdmissionPort,
        terminal_consumer_port: _EventProfileTerminalConsumerPort,
        fence_read_port: _EventProfileInterStepFenceReadPort | None = None,
        stage_observer: Callable[[str, object | None], None] | None = None,
    ) -> None:
        ports = (
            current_read_port,
            production_claim_port,
            physical_step_admission_port,
            standalone_reset_admission_port,
            terminal_consumer_port,
        )
        expected_types = (
            _EventProfileLifecycleCurrentReadPort,
            _EventProfileProductionInitialClaimPort,
            _EventProfilePhysicalStepAdmissionPort,
            _EventProfileStandaloneResetAdmissionPort,
            _EventProfileTerminalConsumerPort,
        )
        if any(type(port) is not expected for port, expected in zip(ports, expected_types, strict=True)):
            raise EventProfileSynchronousRuntimeError(
                "O1 requires the exact narrow runtime port types",
                failure_code="coordinator_port_type",
                stage="coordinator_construct",
                expected=expected_types,
                actual=tuple(type(port) for port in ports),
            )
        domain_identity = current_read_port.domain_identity
        if any(port.domain_identity is not domain_identity for port in ports[1:]):
            raise EventProfileSynchronousRuntimeError(
                "O1 ports must originate from one exact retained domain",
                failure_code="coordinator_domain_identity",
                stage="coordinator_construct",
                expected=id(domain_identity),
                actual=tuple(id(port.domain_identity) for port in ports),
            )
        if fence_read_port is not None and type(fence_read_port) is not _EventProfileInterStepFenceReadPort:
            raise EventProfileSynchronousRuntimeError(
                "fence inspection must use the exact read-only capability",
                failure_code="coordinator_fence_port_type",
                stage="coordinator_construct",
                expected=_EventProfileInterStepFenceReadPort,
                actual=type(fence_read_port),
            )
        if fence_read_port is not None and fence_read_port.domain_identity is not domain_identity:
            raise EventProfileSynchronousRuntimeError(
                "fence read capability must originate from the same retained domain",
                failure_code="coordinator_domain_identity",
                stage="coordinator_construct",
                expected=id(domain_identity),
                actual=id(fence_read_port.domain_identity),
            )
        if not callable(getattr(environment, "reset", None)) or not callable(
            getattr(environment, "step", None)
        ):
            raise EventProfileSynchronousRuntimeError(
                "O1 environment capability requires synchronous reset and step callables",
                failure_code="coordinator_environment_capability",
                stage="coordinator_construct",
                expected="reset()/step(actions)",
                actual=type(environment),
            )
        if stage_observer is not None and not callable(stage_observer):
            raise TypeError("stage_observer must be callable or None")
        object.__setattr__(self, "_environment", environment)
        object.__setattr__(self, "_current_read_port", current_read_port)
        object.__setattr__(self, "_production_claim_port", production_claim_port)
        object.__setattr__(self, "_physical_step_admission_port", physical_step_admission_port)
        object.__setattr__(self, "_standalone_reset_admission_port", standalone_reset_admission_port)
        object.__setattr__(self, "_terminal_consumer_port", terminal_consumer_port)
        object.__setattr__(self, "_fence_read_port", fence_read_port)
        object.__setattr__(self, "_stage_observer", stage_observer)
        self._emit("S0_COORDINATOR_READY")

    def read_current(self) -> _EventRuntimeCurrentPublication:
        return self._current_read_port.read_current()

    @property
    def domain_identity(self) -> object:
        """Return only the opaque same-domain identity retained by O1's ports."""

        return self._current_read_port.domain_identity

    def read_interstep_fence(self) -> _ClaimWindowFenceView:
        """Read the existing fence projection without acquiring writer authority."""

        port = self._fence_read_port
        if port is None:
            raise EventProfileSynchronousRuntimeError(
                "O1 was composed without the read-only fence capability",
                failure_code="coordinator_fence_read_unavailable",
                stage="coordinator_fence_read",
                expected="same-domain read-only fence port",
                actual=None,
            )
        return port.read()

    def capture_pending_terminal_artifacts(
        self,
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        """Return the exact pending slot artifacts without acknowledging them."""

        return self._terminal_consumer_port.capture_pending_terminal_artifacts()

    def acknowledge_terminal_artifact(
        self,
        key: _TerminalTransitionKey,
    ) -> _TerminalHandoffArtifact:
        """Acknowledge exactly one previously captured terminal key."""

        return self._terminal_consumer_port.acknowledge_terminal(key)

    def acknowledge_terminal_artifacts(
        self,
        keys: tuple[_TerminalTransitionKey, ...],
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        """Atomically acknowledge one exact same-domain terminal batch."""

        return self._terminal_consumer_port.acknowledge_terminal_batch(keys)

    def commit_deterministic_initial_claim(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> EffectiveAssignmentCommitArtifact:
        """Backward-compatible deterministic fixture entrypoint."""

        artifact = self._commit_initial_claim_batch(
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested_task_by_robot,
        )
        self._emit("S5_DETERMINISTIC_CLAIM_COMMITTED", artifact)
        self._emit("S6_FINAL_P2_SEEN", self._current_read_port.read_current())
        return artifact

    def commit_initial_claim_batch(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> EffectiveAssignmentCommitArtifact:
        """Submit exactly one already-resolved task-disjoint M1 B1 batch."""

        artifact = self._commit_initial_claim_batch(
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested_task_by_robot,
        )
        self._emit("S5_PROPOSAL_M1_CLAIM_COMMITTED", artifact)
        self._emit("S6_FINAL_P2_SEEN", self._current_read_port.read_current())
        return artifact

    def _commit_initial_claim_batch(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> EffectiveAssignmentCommitArtifact:
        envelope = self._production_claim_port.prepare_production_initial_claim(
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested_task_by_robot,
        )
        return self._production_claim_port.commit_production_initial_claim(envelope)

    def reset_environment(self, *args: object, **kwargs: object) -> Any:
        admission = self._standalone_reset_admission_port.begin_full_reset_admission()
        self._emit("S1_RESET_ADMISSION_BEGUN", admission)
        try:
            result = self._environment.reset(*args, **kwargs)
            self._emit("S3_ENV_RESET_RETURNED", result)
            window = self._standalone_reset_admission_port.commit_successful_return(admission)
        except BaseException as exc:
            self._emit("F_RESET_ADMISSION_FAILURE", exc)
            self._standalone_reset_admission_port.report_abnormal_failure(admission, exc)
            raise
        self._emit("S4_WINDOW_OPEN", window)
        return result

    def step_environment(
        self,
        *,
        action_builder: Callable[[object, torch.Tensor], object] | None = None,
    ) -> Any:
        """Preserve the existing raw environment-result surface."""

        return self.step_environment_without_new_claim(
            action_builder=action_builder,
        ).environment_result

    def step_environment_without_new_claim(
        self,
        *,
        action_builder: Callable[[object, torch.Tensor], object] | None = None,
    ) -> _EventProfileNoClaimStepReceipt:
        """Run one zero-claim step and return its exact Ak-bound diagnostic receipt."""

        self._emit("S5_ZERO_CLAIM_CONTINUATION")
        self._emit("S7_STEP_ADMISSION_REQUESTED")
        admission = self._physical_step_admission_port.begin_physical_step_admission()
        self._emit("S8_AK_ACTIVE", admission)
        try:
            self._emit("S6_FINAL_P2_SEEN", admission.admitted_publication)
            assignment = _derive_control_assignment_from_admitted_publication(admission)
            if action_builder is None:
                from .assignment_rl_interface import assignment_to_env_actions

                actions = assignment_to_env_actions(self._environment, assignment)
            else:
                actions = action_builder(self._environment, assignment)
            self._emit("S9_CONTROL_ACTION_BUILT", assignment)
            result = self._environment.step(actions)
            self._emit("S12_ENV_STEP_RETURNED", result)
            window = self._physical_step_admission_port.commit_successful_return(admission)
        except BaseException as exc:
            self._emit("F_PHYSICAL_STEP_FAILURE", exc)
            self._physical_step_admission_port.report_abnormal_failure(admission, exc)
            raise
        self._emit("S13_AK_COMPLETED", admission)
        self._emit("S14_WINDOW_OPEN", window)
        return _EventProfileNoClaimStepReceipt._create(
            environment_result=result,
            admitted_publication=admission.admitted_publication,
            admitted_control_assignment=assignment,
            completed_window=window,
            factory_capability=_NO_CLAIM_STEP_RECEIPT_FACTORY_CAPABILITY,
        )

    def _emit(self, stage: str, detail: object | None = None) -> None:
        observer = self._stage_observer
        if observer is None:
            return
        try:
            observer(stage, detail)
        except BaseException:
            # Diagnostics are observational and cannot alter admission semantics.
            return


__all__: tuple[str, ...] = ()
