"""Dormant B0-3I4 event-profile lifecycle integration capabilities.

The module is deliberately absent from normal task-package entrypoints.  It
retains one B0 authority stack and exposes episode-rebuild, staged physical
transition finalization, current-read, and synchronous terminal-handoff ports.
Real failure/release/health reporters remain unimplemented.
"""

from __future__ import annotations


CANONICAL_EVENT_PROFILE_RUNTIME_DOMAIN_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_runtime_domain"
)
EVENT_PROFILE_RUNTIME_DOMAIN_SOURCE_PURPOSE = (
    "pure dormant event-profile runtime domain and staged facts adapter"
)

if __name__ != CANONICAL_EVENT_PROFILE_RUNTIME_DOMAIN_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event-profile runtime domain source "
        "must execute under its canonical module key; "
        f"expected={CANONICAL_EVENT_PROFILE_RUNTIME_DOMAIN_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, field
from threading import Event, Lock

import torch

from .assignment_interstep_claim_window_runtime import (
    InterStepClaimWindowRuntimeError,
    RuntimeClaimAdmissionEnvelope,
    _ClaimWindowFenceView,
    _InterStepClaimWindowFence,
    _PhysicalStepAdmission,
    _StandaloneResetAdmission,
)
from .assignment_initial_claim_runtime import (
    EffectiveAssignmentCommitArtifact,
    InitialClaimRequest,
    _CurrentPublicationProvenanceKind,
    _EventRuntimeCurrentPublication,
)
from .assignment_lifecycle_authority_runtime import (
    EnvironmentExecutionFactsProducer,
    ExecutionTransitionInput,
    LifecycleGenerationClock,
    TransitionGenerationContext,
)
from .assignment_lifecycle_transaction_runtime import (
    LifecycleAuthorityRuntime,
    LifecycleAuthorityTransactionCoordinator,
    LifecycleStateSnapshot,
    LifecycleStateStore,
    PublishedLifecycleView,
    _EpisodeRebuildContext,
    _EpisodeRebuildInputs,
    _InitialClaimTestControl,
    _TerminalConsumerCapability,
    _TerminalHandoffArtifact,
    _TerminalObserverCapability,
    _TerminalTransitionKey,
)
from .assignment_lifecycle_transition_contract import (
    RobotLifecycleState,
    LifecycleTransitionResult,
    TaskLifecycleState,
    TerminationReason,
    TransitionConsumeLedger,
)
from .assignment_event_terminal_critic_sidecar import PreResetCriticPhysicalSnapshotV2
from .assignment_profile_contract import (
    AssignmentProfileRouteError,
    ResolvedEventGatedAssignmentProfile,
)


class _EventProfileLifecycleDomainRuntimeError(RuntimeError):
    """Typed B0-private domain/capability boundary failure."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; "
            f"field_name={field_name!r}; expected={expected!r}; actual={actual!r}"
        )


def _require_event_profile(
    profile: object,
    *,
    component: str,
) -> ResolvedEventGatedAssignmentProfile:
    if type(profile) is not ResolvedEventGatedAssignmentProfile:
        raise AssignmentProfileRouteError(
            f"{component} accepts only the canonical event-gated resolved profile",
            profile=getattr(profile, "profile_name", None),
            expected=ResolvedEventGatedAssignmentProfile,
            actual=type(profile),
            resolution_origin=getattr(profile, "resolution_origin", None),
        )
    return profile


def _capture_env_ids(
    value: object,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, tuple[int, ...]]:
    if type(value) is not torch.Tensor:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must be an exact torch.Tensor",
            failure_code="env_id_type",
            field_name="env_ids",
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.dtype is not torch.int64:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must use torch.int64",
            failure_code="env_id_dtype",
            field_name="env_ids",
            expected=torch.int64,
            actual=value.dtype,
        )
    if value.ndim != 1 or int(value.numel()) <= 0:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must have nonempty shape [E]",
            failure_code="env_id_shape",
            field_name="env_ids",
            expected="nonempty [E]",
            actual=tuple(value.shape),
        )
    if value.layout is not torch.strided:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must use a strided layout",
            failure_code="env_id_layout",
            field_name="env_ids",
            expected=torch.strided,
            actual=value.layout,
        )
    if value.device != device:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must use the explicit domain device",
            failure_code="env_id_device",
            field_name="env_ids",
            expected=device,
            actual=value.device,
        )
    if value.requires_grad:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must not require gradients",
            failure_code="env_id_requires_grad",
            field_name="env_ids",
            expected=False,
            actual=True,
        )
    try:
        values = tuple(int(item) for item in value.detach().cpu().tolist())
    except (NotImplementedError, RuntimeError, TypeError) as exc:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must be materializable scalar integers",
            failure_code="env_id_materialization",
            field_name="env_ids",
            expected="materializable int64 values",
            actual=value.device,
        ) from exc
    if len(set(values)) != len(values):
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must be unique",
            failure_code="env_id_unique",
            field_name="env_ids",
            expected=len(values),
            actual=len(set(values)),
        )
    negative = tuple(item for item in values if item < 0)
    if negative:
        raise _EventProfileLifecycleDomainRuntimeError(
            "domain env_ids must be nonnegative",
            failure_code="env_id_range",
            field_name="env_ids",
            expected=">= 0",
            actual=negative,
        )
    return value.detach().clone().contiguous(), values


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EventProfileLifecycleDomainSpec:
    """Immutable/no-alias B0-private vector-domain construction identity."""

    _profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _device: torch.device = field(repr=False)
    _env_ids: torch.Tensor = field(repr=False)
    _env_values: tuple[int, ...] = field(repr=False)
    num_robots: int
    num_tasks: int

    def __init__(
        self,
        profile: ResolvedEventGatedAssignmentProfile,
        *,
        device: torch.device,
        env_ids: torch.Tensor,
        num_robots: int,
        num_tasks: int,
    ) -> None:
        canonical_profile = _require_event_profile(
            profile,
            component="_EventProfileLifecycleDomainSpec",
        )
        if type(device) is not torch.device:
            raise _EventProfileLifecycleDomainRuntimeError(
                "domain spec requires an explicit torch.device",
                failure_code="device_type",
                field_name="device",
                expected=torch.device,
                actual=type(device),
            )
        for field_name, value in (
            ("num_robots", num_robots),
            ("num_tasks", num_tasks),
        ):
            if type(value) is not int or value <= 0:
                raise _EventProfileLifecycleDomainRuntimeError(
                    "domain dimensions must be positive exact integers",
                    failure_code="dimension",
                    field_name=field_name,
                    expected="exact int > 0",
                    actual=value,
                )
        captured_env_ids, env_values = _capture_env_ids(env_ids, device=device)
        object.__setattr__(self, "_profile", canonical_profile)
        object.__setattr__(self, "_device", device)
        object.__setattr__(self, "_env_ids", captured_env_ids)
        object.__setattr__(self, "_env_values", env_values)
        object.__setattr__(self, "num_robots", num_robots)
        object.__setattr__(self, "num_tasks", num_tasks)

    @property
    def profile(self) -> ResolvedEventGatedAssignmentProfile:
        return self._profile

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def env_ids(self) -> torch.Tensor:
        return self._env_ids.detach().clone().contiguous()

    @property
    def num_envs(self) -> int:
        return len(self._env_values)


def _capture_bool_tensor(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensors must be exact torch.Tensor values",
            failure_code="report_tensor_type",
            field_name=field_name,
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.dtype is not torch.bool:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensors must use torch.bool",
            failure_code="report_tensor_dtype",
            field_name=field_name,
            expected=torch.bool,
            actual=value.dtype,
        )
    if value.device != device:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensors must use the explicit report device",
            failure_code="report_tensor_device",
            field_name=field_name,
            expected=device,
            actual=value.device,
        )
    if value.layout is not torch.strided:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensors must use a strided layout",
            failure_code="report_tensor_layout",
            field_name=field_name,
            expected=torch.strided,
            actual=value.layout,
        )
    if tuple(value.shape) != shape:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensor shape differs from the declared report domain",
            failure_code="report_tensor_shape",
            field_name=field_name,
            expected=shape,
            actual=tuple(value.shape),
        )
    if value.requires_grad:
        raise _EventProfileLifecycleDomainRuntimeError(
            "staged report tensors must not require gradients",
            failure_code="report_tensor_requires_grad",
            field_name=field_name,
            expected=False,
            actual=True,
        )
    return value.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _StagedPreResetPhysicalReport:
    """Immutable raw detector/horizon material staged before mutation/reset."""

    _device: torch.device = field(repr=False)
    _coverage_before_transition: torch.Tensor = field(repr=False)
    _raw_new_candidate: torch.Tensor = field(repr=False)
    _physical_truncated: torch.Tensor = field(repr=False)
    _time_limit_reached: torch.Tensor = field(repr=False)
    _pre_reset_critic_physical_snapshot: PreResetCriticPhysicalSnapshotV2 | None = field(
        repr=False
    )
    num_envs: int
    num_robots: int
    num_tasks: int

    def __init__(
        self,
        *,
        device: torch.device,
        coverage_before_transition: torch.Tensor,
        raw_new_candidate: torch.Tensor,
        physical_truncated: torch.Tensor,
        time_limit_reached: torch.Tensor,
        pre_reset_critic_physical_snapshot: PreResetCriticPhysicalSnapshotV2 | None = None,
    ) -> None:
        if type(device) is not torch.device:
            raise _EventProfileLifecycleDomainRuntimeError(
                "staged report requires an explicit torch.device",
                failure_code="report_device_type",
                field_name="device",
                expected=torch.device,
                actual=type(device),
            )
        if type(raw_new_candidate) is not torch.Tensor or raw_new_candidate.ndim != 3:
            raise _EventProfileLifecycleDomainRuntimeError(
                "raw_new_candidate must have exact rank-three shape [E,M,N]",
                failure_code="report_candidate_shape",
                field_name="raw_new_candidate",
                expected="[E,M,N]",
                actual=(
                    tuple(raw_new_candidate.shape)
                    if type(raw_new_candidate) is torch.Tensor
                    else type(raw_new_candidate)
                ),
            )
        env_count, num_robots, num_tasks = (
            int(raw_new_candidate.shape[0]),
            int(raw_new_candidate.shape[1]),
            int(raw_new_candidate.shape[2]),
        )
        if env_count <= 0 or num_robots <= 0 or num_tasks <= 0:
            raise _EventProfileLifecycleDomainRuntimeError(
                "staged report dimensions must be positive",
                failure_code="report_dimensions",
                expected="E,M,N > 0",
                actual=(env_count, num_robots, num_tasks),
            )
        captured = {
            "coverage": _capture_bool_tensor(
                coverage_before_transition,
                field_name="coverage_before_transition",
                shape=(env_count, num_tasks),
                device=device,
            ),
            "candidate": _capture_bool_tensor(
                raw_new_candidate,
                field_name="raw_new_candidate",
                shape=(env_count, num_robots, num_tasks),
                device=device,
            ),
            "truncated": _capture_bool_tensor(
                physical_truncated,
                field_name="physical_truncated",
                shape=(env_count,),
                device=device,
            ),
            "time_limit": _capture_bool_tensor(
                time_limit_reached,
                field_name="time_limit_reached",
                shape=(env_count,),
                device=device,
            ),
        }
        if not torch.equal(captured["truncated"], captured["time_limit"]):
            raise _EventProfileLifecycleDomainRuntimeError(
                "the current scan adapter supports only horizon truncation",
                failure_code="unsupported_truncation_mapping",
                field_name="physical_truncated",
                expected="physical_truncated == time_limit_reached",
                actual="tensor values differ",
            )
        object.__setattr__(self, "_device", device)
        object.__setattr__(self, "_coverage_before_transition", captured["coverage"])
        object.__setattr__(self, "_raw_new_candidate", captured["candidate"])
        object.__setattr__(self, "_physical_truncated", captured["truncated"])
        object.__setattr__(self, "_time_limit_reached", captured["time_limit"])
        if pre_reset_critic_physical_snapshot is not None:
            if type(pre_reset_critic_physical_snapshot) is not PreResetCriticPhysicalSnapshotV2:
                raise _EventProfileLifecycleDomainRuntimeError(
                    "staged report terminal critic evidence has the wrong immutable type",
                    failure_code="pre_reset_critic_snapshot_type",
                    field_name="pre_reset_critic_physical_snapshot",
                    expected=PreResetCriticPhysicalSnapshotV2,
                    actual=type(pre_reset_critic_physical_snapshot),
                )
            if (
                pre_reset_critic_physical_snapshot.device != device
                or pre_reset_critic_physical_snapshot.num_envs != env_count
                or pre_reset_critic_physical_snapshot.M != num_robots
                or pre_reset_critic_physical_snapshot.N != num_tasks
            ):
                raise _EventProfileLifecycleDomainRuntimeError(
                    "staged terminal critic evidence differs from the report domain",
                    failure_code="pre_reset_critic_snapshot_domain",
                    field_name="pre_reset_critic_physical_snapshot",
                    expected=(device, env_count, num_robots, num_tasks),
                    actual=(
                        pre_reset_critic_physical_snapshot.device,
                        pre_reset_critic_physical_snapshot.num_envs,
                        pre_reset_critic_physical_snapshot.M,
                        pre_reset_critic_physical_snapshot.N,
                    ),
                )
            pre_reset_critic_physical_snapshot = pre_reset_critic_physical_snapshot._clone()
        object.__setattr__(
            self,
            "_pre_reset_critic_physical_snapshot",
            pre_reset_critic_physical_snapshot,
        )
        object.__setattr__(self, "num_envs", env_count)
        object.__setattr__(self, "num_robots", num_robots)
        object.__setattr__(self, "num_tasks", num_tasks)

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def coverage_before_transition(self) -> torch.Tensor:
        return self._coverage_before_transition.detach().clone().contiguous()

    @property
    def raw_new_candidate(self) -> torch.Tensor:
        return self._raw_new_candidate.detach().clone().contiguous()

    @property
    def physical_truncated(self) -> torch.Tensor:
        return self._physical_truncated.detach().clone().contiguous()

    @property
    def time_limit_reached(self) -> torch.Tensor:
        return self._time_limit_reached.detach().clone().contiguous()

    @property
    def pre_reset_critic_physical_snapshot(
        self,
    ) -> PreResetCriticPhysicalSnapshotV2 | None:
        if self._pre_reset_critic_physical_snapshot is None:
            return None
        return self._pre_reset_critic_physical_snapshot._clone()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EnvironmentPhysicalTransitionOutcome:
    """Immutable same-step authority and environment-bookkeeping evidence."""

    _published_view: PublishedLifecycleView = field(repr=False)
    _result: LifecycleTransitionResult = field(repr=False)
    _completion_signals: torch.Tensor = field(repr=False)
    _canonical_task_completion: torch.Tensor = field(repr=False)
    _coverage_before_transition: torch.Tensor = field(repr=False)
    _coverage_after_transition: torch.Tensor = field(repr=False)
    _terminated: torch.Tensor = field(repr=False)
    _truncated: torch.Tensor = field(repr=False)
    _terminal_keys: tuple[_TerminalTransitionKey | None, ...] = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        published_view: PublishedLifecycleView,
        completion_signals: torch.Tensor,
        canonical_task_completion: torch.Tensor,
        coverage_before_transition: torch.Tensor,
    ) -> "_EnvironmentPhysicalTransitionOutcome":
        if type(published_view) is not PublishedLifecycleView:
            raise _EventProfileLifecycleDomainRuntimeError(
                "physical transition outcome requires an exact published view",
                failure_code="outcome_view_type",
                expected=PublishedLifecycleView,
                actual=type(published_view),
            )
        result = published_view.result
        if type(result) is not LifecycleTransitionResult:
            raise _EventProfileLifecycleDomainRuntimeError(
                "physical transition outcome requires a finalized result",
                failure_code="outcome_result_type",
                expected=LifecycleTransitionResult,
                actual=type(result),
            )
        completed = result.completed_tasks
        coverage_after = coverage_before_transition | completed
        instance = object.__new__(cls)
        object.__setattr__(instance, "_published_view", published_view)
        object.__setattr__(instance, "_result", result)
        for name, value in (
            ("_completion_signals", completion_signals),
            ("_canonical_task_completion", canonical_task_completion),
            ("_coverage_before_transition", coverage_before_transition),
            ("_coverage_after_transition", coverage_after),
            ("_terminated", published_view.terminated),
            ("_truncated", published_view.truncated),
        ):
            object.__setattr__(instance, name, value.detach().clone().contiguous())
        terminal_keys = tuple(
            (
                None
                if int(result.termination_reason[row].item()) == int(TerminationReason.NONE)
                else _TerminalTransitionKey(
                    int(result.env_id[row].item()),
                    int(result.episode_generation[row].item()),
                    int(result.transition_generation[row].item()),
                )
            )
            for row in range(int(result.env_id.numel()))
        )
        object.__setattr__(instance, "_terminal_keys", terminal_keys)
        return instance

    @property
    def published_view(self) -> PublishedLifecycleView:
        return self._published_view

    @property
    def result(self) -> LifecycleTransitionResult:
        return self._result

    @property
    def completion_signals(self) -> torch.Tensor:
        return self._completion_signals.detach().clone().contiguous()

    @property
    def canonical_task_completion(self) -> torch.Tensor:
        return self._canonical_task_completion.detach().clone().contiguous()

    @property
    def coverage_before_transition(self) -> torch.Tensor:
        return self._coverage_before_transition.detach().clone().contiguous()

    @property
    def coverage_after_transition(self) -> torch.Tensor:
        return self._coverage_after_transition.detach().clone().contiguous()

    @property
    def terminated(self) -> torch.Tensor:
        return self._terminated.detach().clone().contiguous()

    @property
    def truncated(self) -> torch.Tensor:
        return self._truncated.detach().clone().contiguous()

    @property
    def terminal_keys(self) -> tuple[_TerminalTransitionKey | None, ...]:
        return self._terminal_keys


@dataclass(frozen=True, slots=True, eq=False)
class _PendingPhysicalTransition:
    report: _StagedPreResetPhysicalReport = field(repr=False)
    contexts: tuple[TransitionGenerationContext, ...] = field(repr=False)
    state_snapshot: LifecycleStateSnapshot | None = field(default=None, repr=False)


@dataclass(slots=True, eq=False)
class _PhysicalTransitionAdapterTestControl:
    """Synchronization/failure-only pure-test control with no artifact callback."""

    fail_next_facts_build: bool = False
    after_prestate_reached: Event | None = field(default=None, repr=False)
    after_prestate_release: Event | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True, eq=False)
class _EnvironmentEpisodeRebuildContext:
    """Port wrapper exposing only physical-reset completion."""

    _inner: _EpisodeRebuildContext = field(repr=False)
    _operation_lock: Lock = field(repr=False)
    _entered: bool = field(default=False, repr=False)

    def __enter__(self) -> "_EnvironmentEpisodeRebuildContext":
        self._operation_lock.acquire()
        try:
            self._inner.__enter__()
            object.__setattr__(self, "_entered", True)
            return self
        except BaseException:
            self._operation_lock.release()
            raise

    def commit_physical_reset_complete(self) -> _EventRuntimeCurrentPublication:
        return self._inner.commit_physical_reset_complete()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> bool:
        try:
            return self._inner.__exit__(exc_type, exc, traceback)
        finally:
            if self._entered:
                object.__setattr__(self, "_entered", False)
                self._operation_lock.release()


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileLifecycleEnvironmentPort:
    """Environment-facing episode rebuild and staged-transition capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def episode_rebuild(
        self,
        *,
        selected_env_ids: torch.Tensor,
        initial_task_state: torch.Tensor,
        initial_robot_state: torch.Tensor,
        initial_ownership: torch.Tensor,
    ) -> _EnvironmentEpisodeRebuildContext:
        domain = self._domain
        with domain._operation_lock:
            try:
                domain._interstep_fence._require_reset_entry_validation_if_active()
            except BaseException as exc:
                domain._poison_environment_admission_violation(
                    stage="reset_entry_guard",
                    cause=exc,
                )
                raise
        inputs = _EpisodeRebuildInputs(
            domain._spec._profile,
            device=domain._spec._device,
            selected_env_ids=selected_env_ids,
            initial_task_state=initial_task_state,
            initial_robot_state=initial_robot_state,
            initial_ownership=initial_ownership,
        )
        inner = domain._coordinator._episode_rebuild(inputs)
        return _EnvironmentEpisodeRebuildContext(inner, domain._operation_lock)

    def finalize_physical_transition(
        self,
        staged_report: _StagedPreResetPhysicalReport,
    ) -> _EnvironmentPhysicalTransitionOutcome:
        """Finalize one already-staged full-domain physical transition."""

        return self._domain._finalize_physical_transition(staged_report)

    def assert_physical_step_allowed(self) -> None:
        """Fail synchronously until every prior terminal row is acknowledged."""

        self._domain._coordinator._assert_physical_step_allowed()

    def report_post_authority_bookkeeping_failure(
        self,
        outcome: _EnvironmentPhysicalTransitionOutcome,
        cause: BaseException,
    ) -> None:
        """Poison only an exact already-published environment outcome failure."""

        if type(outcome) is not _EnvironmentPhysicalTransitionOutcome:
            raise _EventProfileLifecycleDomainRuntimeError(
                "bookkeeping failure requires an exact physical transition outcome",
                failure_code="outcome_type",
                expected=_EnvironmentPhysicalTransitionOutcome,
                actual=type(outcome),
            )
        if not isinstance(cause, BaseException):
            raise _EventProfileLifecycleDomainRuntimeError(
                "bookkeeping failure requires the raised BaseException",
                failure_code="bookkeeping_cause_type",
                expected=BaseException,
                actual=type(cause),
            )
        self._domain._coordinator._poison_after_environment_bookkeeping_failure(
            published_view=outcome._published_view,
            cause=cause,
        )


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileLifecycleCurrentReadPort:
    """Current immutable publication capability: read only."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def read_current(self) -> _EventRuntimeCurrentPublication:
        return self._domain._coordinator.read_published_view()


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileInitialClaimPort:
    """Narrow dormant B1 request issuance/explicit-commit capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    def prepare_initial_claim(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> InitialClaimRequest:
        with self._domain._operation_lock:
            return self._domain._coordinator._prepare_initial_claim_request(
                selected_env_ids=selected_env_ids,
                requested_task_by_robot=requested_task_by_robot,
            )

    def commit_initial_claim(
        self,
        request: InitialClaimRequest,
    ) -> EffectiveAssignmentCommitArtifact:
        with self._domain._operation_lock:
            return self._domain._coordinator._commit_initial_claim(request)


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileProductionInitialClaimPort:
    """Dormant W2 production-envelope capability; not wired to a caller."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def prepare_production_initial_claim(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> RuntimeClaimAdmissionEnvelope:
        return self._domain._prepare_production_initial_claim(
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested_task_by_robot,
        )

    def commit_production_initial_claim(
        self,
        envelope: RuntimeClaimAdmissionEnvelope,
    ) -> EffectiveAssignmentCommitArtifact:
        return self._domain._commit_production_initial_claim(envelope)


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfilePhysicalStepAdmissionPort:
    """Caller-side S4 admission and explicit O1 completion capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def begin_physical_step_admission(self) -> _PhysicalStepAdmission:
        return self._domain._begin_physical_step_admission()

    def commit_successful_return(
        self,
        admission: _PhysicalStepAdmission,
    ) -> object:
        return self._domain._complete_physical_step_admission(admission)

    def report_abnormal_failure(
        self,
        admission: _PhysicalStepAdmission,
        cause: BaseException,
    ) -> None:
        self._domain._report_physical_step_admission_failure(admission, cause)


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileStandaloneResetAdmissionPort:
    """Caller-side full-reset admission and explicit O1 completion capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def begin_full_reset_admission(self) -> _StandaloneResetAdmission:
        return self._domain._begin_full_reset_admission()

    def commit_successful_return(
        self,
        admission: _StandaloneResetAdmission,
    ) -> object:
        return self._domain._complete_full_reset_admission(admission)

    def report_abnormal_failure(
        self,
        admission: _StandaloneResetAdmission,
        cause: BaseException,
    ) -> None:
        self._domain._report_full_reset_admission_failure(admission, cause)


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileEnvironmentAdmissionValidationPort:
    """Environment current-call validation handshake; no open/close capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def validate_physical_step_entry_for_active_call(self) -> None:
        self._domain._validate_physical_step_entry_for_active_call()

    def validate_physical_finalization_for_active_call(self) -> None:
        self._domain._validate_physical_finalization_for_active_call()

    def validate_reset_entry_for_active_call(self) -> None:
        self._domain._validate_reset_entry_for_active_call()

    def validate_physical_step_entry(self, admission: _PhysicalStepAdmission) -> None:
        self._domain._validate_physical_step_entry(admission)

    def validate_physical_finalization(self, admission: _PhysicalStepAdmission) -> None:
        self._domain._validate_physical_finalization(admission)

    def validate_reset_entry(self, admission: _StandaloneResetAdmission) -> None:
        self._domain._validate_full_reset_entry(admission)


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileInterStepFenceReadPort:
    """Read-only B1W phase/identity projection for pure verification."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def read(self) -> _ClaimWindowFenceView:
        return self._domain._read_interstep_fence()


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileTerminalObserverPort:
    """Repeatable, non-destructive exact-key terminal observer."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)
    _capability: _TerminalObserverCapability = field(repr=False)

    def read_terminal(self, key: _TerminalTransitionKey) -> _TerminalHandoffArtifact:
        return self._domain._coordinator._read_terminal(
            key,
            capability=self._capability,
        )


@dataclass(frozen=True, slots=True, eq=False)
class _EventProfileTerminalConsumerPort:
    """The one designated exact-key terminal read/ack capability."""

    _domain: "_EventProfileLifecycleRuntimeDomain" = field(repr=False)
    _capability: _TerminalConsumerCapability = field(repr=False)

    @property
    def domain_identity(self) -> object:
        return self._domain._coordinator._domain_identity

    def capture_pending_terminal_artifacts(
        self,
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        return self._domain._coordinator._capture_pending_terminal_artifacts(
            capability=self._capability,
        )

    def read_terminal(self, key: _TerminalTransitionKey) -> _TerminalHandoffArtifact:
        return self._domain._coordinator._read_terminal(
            key,
            capability=self._capability,
        )

    def acknowledge_terminal(self, key: _TerminalTransitionKey) -> _TerminalHandoffArtifact:
        return self._domain._coordinator._acknowledge_terminal(
            key,
            capability=self._capability,
        )

    def acknowledge_terminal_batch(
        self,
        keys: tuple[_TerminalTransitionKey, ...],
    ) -> tuple[_TerminalHandoffArtifact, ...]:
        return self._domain._coordinator._acknowledge_terminal_batch(
            keys,
            capability=self._capability,
        )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _EventProfileLifecycleRuntimeDomain:
    """One retained B0 authority stack for one live vector domain."""

    _spec: _EventProfileLifecycleDomainSpec = field(repr=False)
    _producer: EnvironmentExecutionFactsProducer = field(repr=False)
    _clock: LifecycleGenerationClock = field(repr=False)
    _state_store: LifecycleStateStore = field(repr=False)
    _authority: LifecycleAuthorityRuntime = field(repr=False)
    _ledger: TransitionConsumeLedger = field(repr=False)
    _coordinator: LifecycleAuthorityTransactionCoordinator = field(repr=False)
    _interstep_fence: _InterStepClaimWindowFence = field(repr=False)
    _environment_port: _EventProfileLifecycleEnvironmentPort = field(repr=False)
    _current_read_port: _EventProfileLifecycleCurrentReadPort = field(repr=False)
    _initial_claim_port: _EventProfileInitialClaimPort = field(repr=False)
    _production_claim_port: _EventProfileProductionInitialClaimPort = field(repr=False)
    _physical_step_admission_port: _EventProfilePhysicalStepAdmissionPort = field(repr=False)
    _standalone_reset_admission_port: _EventProfileStandaloneResetAdmissionPort = field(repr=False)
    _environment_admission_validation_port: _EventProfileEnvironmentAdmissionValidationPort = field(repr=False)
    _interstep_fence_read_port: _EventProfileInterStepFenceReadPort = field(repr=False)
    _terminal_consumer_port: _EventProfileTerminalConsumerPort = field(repr=False)
    _operation_lock: Lock = field(repr=False)
    _pending_transition: _PendingPhysicalTransition | None = field(repr=False)
    _test_control: _PhysicalTransitionAdapterTestControl | None = field(repr=False)

    def __init__(
        self,
        spec: _EventProfileLifecycleDomainSpec,
        *,
        _test_control: _PhysicalTransitionAdapterTestControl | None = None,
        _initial_claim_test_control: _InitialClaimTestControl | None = None,
    ) -> None:
        if type(spec) is not _EventProfileLifecycleDomainSpec:
            raise _EventProfileLifecycleDomainRuntimeError(
                "runtime domain requires an exact immutable construction spec",
                failure_code="spec_type",
                field_name="spec",
                expected=_EventProfileLifecycleDomainSpec,
                actual=type(spec),
            )
        if (
            _test_control is not None
            and type(_test_control) is not _PhysicalTransitionAdapterTestControl
        ):
            raise _EventProfileLifecycleDomainRuntimeError(
                "private transition adapter test control has the wrong exact type",
                failure_code="test_control_type",
                field_name="_test_control",
                expected=_PhysicalTransitionAdapterTestControl,
                actual=type(_test_control),
            )

        bound_spec = _EventProfileLifecycleDomainSpec(
            spec._profile,
            device=spec._device,
            env_ids=spec._env_ids,
            num_robots=spec.num_robots,
            num_tasks=spec.num_tasks,
        )
        env_ids = bound_spec._env_ids.detach().clone().contiguous()
        env_count = bound_spec.num_envs
        producer = EnvironmentExecutionFactsProducer(bound_spec._profile)
        clock = LifecycleGenerationClock(bound_spec._profile, env_ids=env_ids)
        state_store = LifecycleStateStore(
            bound_spec._profile,
            device=bound_spec._device,
            env_id=env_ids,
            task_state=torch.full(
                (env_count, bound_spec.num_tasks),
                int(TaskLifecycleState.AVAILABLE),
                dtype=torch.int64,
                device=bound_spec._device,
            ),
            robot_state=torch.full(
                (env_count, bound_spec.num_robots),
                int(RobotLifecycleState.NEEDS_ASSIGNMENT),
                dtype=torch.int64,
                device=bound_spec._device,
            ),
            ownership=torch.full(
                (env_count, bound_spec.num_tasks),
                -1,
                dtype=torch.int64,
                device=bound_spec._device,
            ),
            cumulative_failed_pairs=torch.zeros(
                (env_count, bound_spec.num_robots, bound_spec.num_tasks),
                dtype=torch.bool,
                device=bound_spec._device,
            ),
            completion_count=torch.zeros(
                (env_count, bound_spec.num_robots),
                dtype=torch.int64,
                device=bound_spec._device,
            ),
            termination_reason=torch.full(
                (env_count,),
                int(TerminationReason.NONE),
                dtype=torch.int64,
                device=bound_spec._device,
            ),
        )
        coordinator = LifecycleAuthorityTransactionCoordinator(
            bound_spec._profile,
            state_store=state_store,
            generation_clock=clock,
            _initial_claim_test_control=_initial_claim_test_control,
        )
        view = coordinator.read_published_view()
        if (
            view.store_version != 0
            or view.result is not None
            or not torch.equal(view.env_id, env_ids)
            or not bool((view.episode_generation == -1).all().item())
            or not bool((view.transition_generation == -1).all().item())
            or bool(view.terminated.any().item())
            or bool(view.truncated.any().item())
            or any(
                provenance.kind
                is not _CurrentPublicationProvenanceKind.PREBOOTSTRAP
                for provenance in view.provenance
            )
        ):
            raise _EventProfileLifecycleDomainRuntimeError(
                "constructed authority stack is not canonical pre-bootstrap state",
                failure_code="prebootstrap_state",
                expected="version 0, generations -1, result None, no done",
                actual=(
                    view.store_version,
                    view.episode_generation.tolist(),
                    view.transition_generation.tolist(),
                    type(view.result),
                ),
            )
        authority = coordinator._authority
        ledger = coordinator._ledger
        if (
            type(authority) is not LifecycleAuthorityRuntime
            or type(ledger) is not TransitionConsumeLedger
            or authority._profile is not bound_spec._profile
            or producer._profile is not bound_spec._profile
            or clock._profile is not bound_spec._profile
            or state_store._profile is not bound_spec._profile
        ):
            raise _EventProfileLifecycleDomainRuntimeError(
                "retained authority stack has inconsistent component identity",
                failure_code="component_identity",
                expected="one exact canonical profile-bound stack",
                actual="component identity mismatch",
            )

        object.__setattr__(self, "_spec", bound_spec)
        object.__setattr__(self, "_producer", producer)
        object.__setattr__(self, "_clock", clock)
        object.__setattr__(self, "_state_store", state_store)
        object.__setattr__(self, "_authority", authority)
        object.__setattr__(self, "_ledger", ledger)
        object.__setattr__(self, "_coordinator", coordinator)
        object.__setattr__(self, "_operation_lock", Lock())
        object.__setattr__(
            self,
            "_interstep_fence",
            _InterStepClaimWindowFence(domain_identity=coordinator._domain_identity),
        )
        object.__setattr__(self, "_pending_transition", None)
        object.__setattr__(self, "_test_control", _test_control)
        object.__setattr__(
            self,
            "_environment_port",
            _EventProfileLifecycleEnvironmentPort(self),
        )
        object.__setattr__(
            self,
            "_current_read_port",
            _EventProfileLifecycleCurrentReadPort(self),
        )
        object.__setattr__(
            self,
            "_initial_claim_port",
            _EventProfileInitialClaimPort(self),
        )
        object.__setattr__(
            self,
            "_production_claim_port",
            _EventProfileProductionInitialClaimPort(self),
        )
        object.__setattr__(
            self,
            "_physical_step_admission_port",
            _EventProfilePhysicalStepAdmissionPort(self),
        )
        object.__setattr__(
            self,
            "_standalone_reset_admission_port",
            _EventProfileStandaloneResetAdmissionPort(self),
        )
        object.__setattr__(
            self,
            "_environment_admission_validation_port",
            _EventProfileEnvironmentAdmissionValidationPort(self),
        )
        object.__setattr__(
            self,
            "_interstep_fence_read_port",
            _EventProfileInterStepFenceReadPort(self),
        )
        object.__setattr__(
            self,
            "_terminal_consumer_port",
            _EventProfileTerminalConsumerPort(
                self,
                coordinator._issue_terminal_consumer_capability(),
            ),
        )

    def _read_interstep_fence(self) -> _ClaimWindowFenceView:
        with self._operation_lock:
            return self._interstep_fence._view(poisoned=self._coordinator.poisoned)

    def _prepare_production_initial_claim(
        self,
        *,
        selected_env_ids: torch.Tensor,
        requested_task_by_robot: torch.Tensor,
    ) -> RuntimeClaimAdmissionEnvelope:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            window = self._interstep_fence._require_open_for_claim_prepare()
            request = self._coordinator._prepare_initial_claim_request(
                selected_env_ids=selected_env_ids,
                requested_task_by_robot=requested_task_by_robot,
            )
            return self._interstep_fence._create_claim_envelope(
                request=request,
                window=window,
            )

    def _commit_production_initial_claim(
        self,
        envelope: RuntimeClaimAdmissionEnvelope,
    ) -> EffectiveAssignmentCommitArtifact:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            validated = self._interstep_fence._validate_claim_envelope(envelope)
            return self._coordinator._commit_initial_claim(validated._request)

    def _begin_physical_step_admission(self) -> _PhysicalStepAdmission:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            self._interstep_fence._require_open_for_step_begin()
            publication = self._coordinator._capture_physical_step_admission_baseline()
            return self._interstep_fence._begin_physical_step(
                publication=publication,
            )

    def _validate_physical_step_entry(
        self,
        admission: _PhysicalStepAdmission,
    ) -> None:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            self._interstep_fence._validate_step_entry(admission)

    def _validate_physical_step_entry_for_active_call(self) -> None:
        with self._operation_lock:
            try:
                self._coordinator._assert_runtime_admission_healthy()
                self._interstep_fence._validate_step_entry_for_active_call()
                self._coordinator._assert_physical_step_allowed()
            except BaseException as exc:
                self._poison_environment_admission_violation(
                    stage="physical_step_entry",
                    cause=exc,
                )
                raise

    def _validate_physical_finalization(
        self,
        admission: _PhysicalStepAdmission,
    ) -> None:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            self._interstep_fence._validate_step_finalization(admission)

    def _validate_physical_finalization_for_active_call(self) -> None:
        with self._operation_lock:
            try:
                self._coordinator._assert_runtime_admission_healthy()
                self._interstep_fence._validate_step_finalization_for_active_call()
            except BaseException as exc:
                self._poison_environment_admission_violation(
                    stage="physical_step_finalization",
                    cause=exc,
                )
                raise

    def _complete_physical_step_admission(
        self,
        admission: _PhysicalStepAdmission,
    ) -> object:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            return self._interstep_fence._complete_physical_step(admission)

    def _report_physical_step_admission_failure(
        self,
        admission: _PhysicalStepAdmission,
        cause: BaseException,
    ) -> None:
        if not isinstance(cause, BaseException):
            raise TypeError("physical-step failure cause must be a BaseException")
        with self._operation_lock:
            self._interstep_fence._validate_abnormal_step(admission)
            self._coordinator._poison_after_runtime_admission_failure(
                stage="physical_step",
                cause=cause,
            )

    def _begin_full_reset_admission(self) -> _StandaloneResetAdmission:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            return self._interstep_fence._begin_full_reset()

    def _validate_full_reset_entry(
        self,
        admission: _StandaloneResetAdmission,
    ) -> None:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            self._interstep_fence._validate_reset_entry(admission)

    def _validate_reset_entry_for_active_call(self) -> None:
        with self._operation_lock:
            try:
                self._coordinator._assert_runtime_admission_healthy()
                self._interstep_fence._validate_reset_entry_for_active_call()
            except BaseException as exc:
                self._poison_environment_admission_violation(
                    stage="reset_entry",
                    cause=exc,
                )
                raise

    def _poison_environment_admission_violation(
        self,
        *,
        stage: str,
        cause: BaseException,
    ) -> None:
        self._coordinator._poison_after_runtime_admission_failure(
            stage=f"environment_{stage}",
            cause=cause,
        )

    def _complete_full_reset_admission(
        self,
        admission: _StandaloneResetAdmission,
    ) -> object:
        with self._operation_lock:
            self._coordinator._assert_runtime_admission_healthy()
            return self._interstep_fence._complete_full_reset(admission)

    def _report_full_reset_admission_failure(
        self,
        admission: _StandaloneResetAdmission,
        cause: BaseException,
    ) -> None:
        if not isinstance(cause, BaseException):
            raise TypeError("reset failure cause must be a BaseException")
        with self._operation_lock:
            self._interstep_fence._validate_abnormal_reset(admission)
            self._coordinator._poison_after_runtime_admission_failure(
                stage="standalone_reset",
                cause=cause,
            )

    def _finalize_physical_transition(
        self,
        report: _StagedPreResetPhysicalReport,
    ) -> _EnvironmentPhysicalTransitionOutcome:
        if type(report) is not _StagedPreResetPhysicalReport:
            raise _EventProfileLifecycleDomainRuntimeError(
                "physical transition finalization requires the exact staged report",
                failure_code="staged_report_type",
                field_name="staged_report",
                expected=_StagedPreResetPhysicalReport,
                actual=type(report),
            )
        self._validate_report_domain(report)
        with self._operation_lock:
            try:
                self._interstep_fence._require_step_finalization_validation_if_active()
            except BaseException as exc:
                self._poison_environment_admission_violation(
                    stage="physical_step_finalization_guard",
                    cause=exc,
                )
                raise
            pending = self._pending_transition
            if pending is None:
                contexts = self._clock.request_transition_candidate(
                    self._spec._env_ids,
                )
                pending = _PendingPhysicalTransition(report, contexts)
                object.__setattr__(self, "_pending_transition", pending)
            elif report is not pending.report:
                raise _EventProfileLifecycleDomainRuntimeError(
                    "a different physical report cannot replace the pending transition",
                    failure_code="pending_report_identity",
                    field_name="staged_report",
                    expected=id(pending.report),
                    actual=id(report),
                )

            snapshot = self._coordinator._capture_execution_prestate(
                env_ids=self._spec._env_ids,
                transition_contexts=pending.contexts,
            )
            if pending.state_snapshot is None:
                pending = _PendingPhysicalTransition(
                    pending.report,
                    pending.contexts,
                    snapshot,
                )
                object.__setattr__(self, "_pending_transition", pending)
            else:
                self._require_same_prestate(pending.state_snapshot, snapshot)

            control = self._test_control
            if control is not None and control.after_prestate_reached is not None:
                control.after_prestate_reached.set()
            if control is not None and control.after_prestate_release is not None:
                if not control.after_prestate_release.wait(timeout=10.0):
                    raise _EventProfileLifecycleDomainRuntimeError(
                        "timed out at the private prestate test interlock",
                        failure_code="test_interlock_timeout",
                        expected="release event set",
                        actual=False,
                    )

            revalidated = self._coordinator._capture_execution_prestate(
                env_ids=self._spec._env_ids,
                transition_contexts=pending.contexts,
            )
            self._require_same_prestate(pending.state_snapshot, revalidated)
            transition_input, completion, task_completion = (
                self._build_transition_input(
                    report=report,
                    snapshot=revalidated,
                    contexts=pending.contexts,
                )
            )
            facts = self._producer.build_facts(transition_input)
            current = self._coordinator._transact_with_terminal_handoff(
                facts=facts,
                transition_contexts=pending.contexts,
                coverage_before_transition=report._coverage_before_transition,
                pre_reset_critic_physical_snapshot=(
                    report._pre_reset_critic_physical_snapshot
                ),
            )
            outcome = _EnvironmentPhysicalTransitionOutcome._create(
                published_view=current.lifecycle_view,
                completion_signals=completion,
                canonical_task_completion=task_completion,
                coverage_before_transition=report._coverage_before_transition,
            )
            object.__setattr__(self, "_pending_transition", None)
            return outcome

    def _validate_report_domain(
        self,
        report: _StagedPreResetPhysicalReport,
    ) -> None:
        expected = (
            self._spec._device,
            self._spec.num_envs,
            self._spec.num_robots,
            self._spec.num_tasks,
        )
        actual = (
            report._device,
            report.num_envs,
            report.num_robots,
            report.num_tasks,
        )
        if actual != expected:
            raise _EventProfileLifecycleDomainRuntimeError(
                "staged report differs from its retained runtime domain",
                failure_code="report_domain",
                field_name="device/E/M/N",
                expected=expected,
                actual=actual,
            )
        if not torch.equal(
            report._physical_truncated,
            report._time_limit_reached,
        ):
            raise _EventProfileLifecycleDomainRuntimeError(
                "staged report was altered after horizon validation",
                failure_code="report_integrity",
                field_name="physical_truncated/time_limit_reached",
                expected="exact equality",
                actual="tensor values differ",
            )

    @staticmethod
    def _require_same_prestate(
        expected: LifecycleStateSnapshot,
        actual: LifecycleStateSnapshot,
    ) -> None:
        fields = (
            "_env_id",
            "_task_state",
            "_robot_state",
            "_ownership",
            "_cumulative_failed_pairs",
            "_completion_count",
            "_termination_reason",
        )
        if (
            expected._store_identity is not actual._store_identity
            or expected.store_version != actual.store_version
            or any(
                not torch.equal(getattr(expected, name), getattr(actual, name))
                for name in fields
            )
        ):
            raise _EventProfileLifecycleDomainRuntimeError(
                "pending transition prestate is stale or was reinterpreted",
                failure_code="stale_bound_prestate",
                field_name="LifecycleStateSnapshot",
                expected=(id(expected._store_identity), expected.store_version),
                actual=(id(actual._store_identity), actual.store_version),
            )

    def _build_transition_input(
        self,
        *,
        report: _StagedPreResetPhysicalReport,
        snapshot: LifecycleStateSnapshot,
        contexts: tuple[TransitionGenerationContext, ...],
    ) -> tuple[ExecutionTransitionInput, torch.Tensor, torch.Tensor]:
        task0 = snapshot._task_state
        owner0 = snapshot._ownership
        active0 = (
            (task0 == int(TaskLifecycleState.CLAIMED))
            | (task0 == int(TaskLifecycleState.NAVIGATING))
            | (task0 == int(TaskLifecycleState.ALIGNING))
        )
        robot_ids = torch.arange(
            self._spec.num_robots,
            dtype=torch.int64,
            device=self._spec._device,
        ).view(1, self._spec.num_robots, 1)
        owner_match = owner0.unsqueeze(1) == robot_ids
        completion = (
            report._raw_new_candidate
            & active0.unsqueeze(1)
            & owner_match
        )
        if bool((completion.sum(dim=1) > 1).any().item()):
            raise _EventProfileLifecycleDomainRuntimeError(
                "owner-qualified completion violates unique task ownership",
                failure_code="completion_cardinality",
                field_name="completion_signals",
                expected="sum_i <= 1",
                actual="multiple completing robots",
            )
        task_completion = completion.any(dim=1)
        prospective_coverage = report._coverage_before_transition | task_completion
        physical_terminated = prospective_coverage.all(dim=1)
        episode = torch.tensor(
            tuple(context.episode_generation for context in contexts),
            dtype=torch.int64,
            device=self._spec._device,
        )
        transition = torch.tensor(
            tuple(context.transition_generation for context in contexts),
            dtype=torch.int64,
            device=self._spec._device,
        )
        false_pairs = torch.zeros_like(completion)
        false_robots = torch.zeros(
            (self._spec.num_envs, self._spec.num_robots),
            dtype=torch.bool,
            device=self._spec._device,
        )
        recovered: torch.Tensor = false_robots
        control = self._test_control
        if control is not None and control.fail_next_facts_build:
            control.fail_next_facts_build = False
            recovered = false_robots.to(dtype=torch.int64)
        transition_input = ExecutionTransitionInput(
            device=self._spec._device,
            env_id=self._spec._env_ids,
            episode_generation=episode,
            transition_generation=transition,
            physical_terminated=physical_terminated,
            physical_truncated=report._physical_truncated,
            time_limit_reached=report._time_limit_reached,
            bad_transition=torch.zeros(
                (self._spec.num_envs,),
                dtype=torch.bool,
                device=self._spec._device,
            ),
            completion_signals=completion,
            terminal_pair_failure_signals=false_pairs,
            forced_release_signals=false_pairs,
            robot_unavailable_signals=false_robots,
            robot_recovered_signals=recovered,
            coverage_before_transition=report._coverage_before_transition,
            task_state_before_transition=snapshot._task_state,
            robot_state_before_transition=snapshot._robot_state,
            ownership_before_transition=snapshot._ownership,
        )
        return transition_input, completion, task_completion

    @property
    def identity(self) -> _EventProfileLifecycleDomainSpec:
        return _EventProfileLifecycleDomainSpec(
            self._spec._profile,
            device=self._spec._device,
            env_ids=self._spec._env_ids,
            num_robots=self._spec.num_robots,
            num_tasks=self._spec.num_tasks,
        )

    @property
    def environment_port(self) -> _EventProfileLifecycleEnvironmentPort:
        return self._environment_port

    @property
    def current_read_port(self) -> _EventProfileLifecycleCurrentReadPort:
        return self._current_read_port

    @property
    def initial_claim_port(self) -> _EventProfileInitialClaimPort:
        return self._initial_claim_port

    @property
    def production_claim_port(self) -> _EventProfileProductionInitialClaimPort:
        return self._production_claim_port

    @property
    def physical_step_admission_port(self) -> _EventProfilePhysicalStepAdmissionPort:
        return self._physical_step_admission_port

    @property
    def standalone_reset_admission_port(self) -> _EventProfileStandaloneResetAdmissionPort:
        return self._standalone_reset_admission_port

    @property
    def environment_admission_validation_port(
        self,
    ) -> _EventProfileEnvironmentAdmissionValidationPort:
        return self._environment_admission_validation_port

    @property
    def interstep_fence_read_port(self) -> _EventProfileInterStepFenceReadPort:
        return self._interstep_fence_read_port

    @property
    def terminal_consumer_port(self) -> _EventProfileTerminalConsumerPort:
        return self._terminal_consumer_port

    def terminal_observer_port(self) -> _EventProfileTerminalObserverPort:
        return _EventProfileTerminalObserverPort(
            self,
            self._coordinator._issue_terminal_observer_capability(),
        )


__all__: tuple[str, ...] = ()
