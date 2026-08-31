"""Authoritative pre-reset terminal audit and timeout-bootstrap evidence.

This B2-I4 module owns immutable evidence values only.  It captures no
lifecycle authority and performs no critic evaluation, learner insertion,
return computation, acknowledgement, or environment reset.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TERMINAL_CRITIC_SIDECAR_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_terminal_critic_sidecar"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TERMINAL_CRITIC_SIDECAR_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: terminal critic sidecar source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TERMINAL_CRITIC_SIDECAR_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

import torch

from .assignment_event_policy_evidence import (
    EventPolicyNumericalBlockLayoutV2,
    EventPolicyPhysicalProblemEvidenceV2,
    _layout,
    _project_common_blocks,
    capture_event_policy_physical_problem_evidence_v2,
)
from .assignment_event_profile_schema_contract_v2 import (
    ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION,
    EVENT_POLICY_CRITIC_SCHEMA_V2,
    EVENT_POLICY_SCALE_V2_CONTRACT_VERSION,
    build_assignment_event_profile_schema_v2_descriptor,
)
from .assignment_initial_claim_runtime import _EventRuntimeCurrentPublication
from .assignment_lifecycle_transaction_runtime import (
    LifecycleStateSnapshot,
    PublishedLifecycleView,
    _TerminalTransitionKey,
)
from .assignment_lifecycle_transition_contract import (
    LifecycleTransitionResult,
    RobotLifecycleState,
    TaskLifecycleState,
    TerminationReason,
)


PRE_RESET_CRITIC_PHYSICAL_SNAPSHOT_V2 = "pre_reset_critic_physical_snapshot_v2"
EVENT_TERMINAL_CRITIC_SIDECAR_V2 = "event_terminal_critic_sidecar_v2"
TERMINAL_AUDIT_PROJECTION_V2 = "terminal_audit_projection_v2"
TIME_LIMIT_BOOTSTRAP_CRITIC_V2 = "time_limit_bootstrap_critic_v2"


class EventTerminalCriticSidecarError(RuntimeError):
    """Fail-closed B2-I4 capture, binding, or copy error."""

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


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    field_name: str | None = None,
    expected: object = None,
    actual: object = None,
) -> None:
    raise EventTerminalCriticSidecarError(
        message,
        failure_code=failure_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        actual=actual,
    )


def _readonly_tensor(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


def _readonly_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True, init=False, eq=False)
class PreResetCriticPhysicalSnapshotV2:
    """Detached physical feature basis captured at the task-local done seam."""

    schema_version: str
    num_envs: int
    M: int
    N: int
    _physical_evidence: EventPolicyPhysicalProblemEvidenceV2 = field(repr=False)
    _scale_contract: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "pre-reset physical snapshots require the canonical capture factory",
            failure_code="physical_snapshot_factory_required",
            stage="pre_reset_physical_capture",
            expected="capture_pre_reset_critic_physical_snapshot_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        physical_evidence: EventPolicyPhysicalProblemEvidenceV2,
        scale_contract: Mapping[str, object],
    ) -> "PreResetCriticPhysicalSnapshotV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", PRE_RESET_CRITIC_PHYSICAL_SNAPSHOT_V2)
        object.__setattr__(instance, "num_envs", physical_evidence.num_envs)
        object.__setattr__(instance, "M", physical_evidence.M)
        object.__setattr__(instance, "N", physical_evidence.N)
        object.__setattr__(instance, "_physical_evidence", physical_evidence._clone())
        object.__setattr__(instance, "_scale_contract", _readonly_mapping(scale_contract))
        return instance

    def _clone(self) -> "PreResetCriticPhysicalSnapshotV2":
        return self._create(
            physical_evidence=self._physical_evidence,
            scale_contract=self._scale_contract,
        )

    @property
    def device(self) -> torch.device:
        return self._physical_evidence.device

    @property
    def physical_evidence(self) -> EventPolicyPhysicalProblemEvidenceV2:
        return self._physical_evidence._clone()

    @property
    def scale_contract(self) -> Mapping[str, object]:
        return self._scale_contract


def capture_pre_reset_critic_physical_snapshot_v2(
    *,
    assignment_problem: Mapping[str, object],
    episode_progress_steps: torch.Tensor,
    scale_contract: Mapping[str, object],
) -> PreResetCriticPhysicalSnapshotV2:
    """Capture the fixed physical basis once, before task-environment autoreset."""

    physical = capture_event_policy_physical_problem_evidence_v2(
        assignment_problem=assignment_problem,
        episode_progress_steps=episode_progress_steps,
        scale_contract=scale_contract,
    )
    descriptor = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=scale_contract
    )
    return PreResetCriticPhysicalSnapshotV2._create(
        physical_evidence=physical,
        scale_contract=descriptor["scale_contract"],
    )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TerminalAuditProjectionV2:
    """Typed terminal-only audit projection; it is never critic-consumable."""

    schema_version: str
    projection_mode: str
    env_id: int
    episode_generation: int
    transition_generation: int
    termination_reason: int
    critic_schema_version: str
    critic_dimension: int
    _semantic_evidence: torch.Tensor = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        key: _TerminalTransitionKey,
        termination_reason: int,
        critic_schema_version: str,
        semantic_evidence: torch.Tensor,
    ) -> "TerminalAuditProjectionV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", TERMINAL_AUDIT_PROJECTION_V2)
        object.__setattr__(instance, "projection_mode", "TERMINAL_AUDIT")
        object.__setattr__(instance, "env_id", key.env_id)
        object.__setattr__(instance, "episode_generation", key.episode_generation)
        object.__setattr__(instance, "transition_generation", key.transition_generation)
        object.__setattr__(instance, "termination_reason", termination_reason)
        object.__setattr__(instance, "critic_schema_version", critic_schema_version)
        object.__setattr__(instance, "critic_dimension", int(semantic_evidence.numel()))
        object.__setattr__(instance, "_semantic_evidence", _readonly_tensor(semantic_evidence))
        return instance

    def _clone(self) -> "TerminalAuditProjectionV2":
        return self._create(
            key=_TerminalTransitionKey(
                self.env_id,
                self.episode_generation,
                self.transition_generation,
            ),
            termination_reason=self.termination_reason,
            critic_schema_version=self.critic_schema_version,
            semantic_evidence=self._semantic_evidence,
        )

    @property
    def semantic_evidence(self) -> torch.Tensor:
        """Return audit-only numerical evidence, never a critic input API."""

        return _readonly_tensor(self._semantic_evidence)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTerminalCriticSidecarV2:
    """One immutable sidecar bound to one exact authoritative terminal row."""

    schema_version: str
    profile_schema_version: str
    scale_contract_version: str
    critic_schema_version: str
    env_id: int
    episode_generation: int
    transition_generation: int
    termination_reason: int
    terminated: bool
    truncated: bool
    published_store_version: int
    bootstrap_projection_valid: bool
    critic_dimension: int
    critic_dtype: torch.dtype
    critic_device: torch.device
    _source_p2_publication_identity: object = field(repr=False)
    _terminal_audit_projection: TerminalAuditProjectionV2 = field(repr=False)
    _bootstrap_critic_obs: torch.Tensor | None = field(repr=False)
    _critic_block_layout: tuple[EventPolicyNumericalBlockLayoutV2, ...] = field(repr=False)
    _physical_provenance: Mapping[str, object] = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        key: _TerminalTransitionKey,
        reason: int,
        terminated: bool,
        truncated: bool,
        published_store_version: int,
        source_p2_publication_identity: object,
        terminal_audit_projection: TerminalAuditProjectionV2,
        bootstrap_critic_obs: torch.Tensor | None,
        critic_schema_version: str,
        critic_block_layout: tuple[EventPolicyNumericalBlockLayoutV2, ...],
        physical_provenance: Mapping[str, object],
    ) -> "EventTerminalCriticSidecarV2":
        if type(key) is not _TerminalTransitionKey:
            _fail(
                "terminal sidecar requires the canonical exact key",
                failure_code="sidecar_key_type",
                stage="sidecar_create",
                expected=_TerminalTransitionKey,
                actual=type(key),
            )
        if type(terminal_audit_projection) is not TerminalAuditProjectionV2:
            _fail(
                "terminal sidecar requires one typed audit projection",
                failure_code="audit_projection_type",
                stage="sidecar_create",
                expected=TerminalAuditProjectionV2,
                actual=type(terminal_audit_projection),
            )
        bootstrap_valid = reason == int(TerminationReason.TIME_LIMIT)
        if bootstrap_valid != (bootstrap_critic_obs is not None):
            _fail(
                "timeout bootstrap presence differs from the finalized reason",
                failure_code="bootstrap_presence",
                stage="sidecar_create",
                expected=bootstrap_valid,
                actual=bootstrap_critic_obs is not None,
            )
        audit_evidence = terminal_audit_projection._semantic_evidence
        if (
            audit_evidence.ndim != 1
            or audit_evidence.dtype is not torch.float32
            or audit_evidence.requires_grad
            or not bool(torch.isfinite(audit_evidence).all().item())
        ):
            _fail(
                "terminal audit evidence violates the critic-schema tensor contract",
                failure_code="audit_tensor_contract",
                stage="sidecar_create",
                expected="finite no-grad float32[S_critic]",
                actual=(audit_evidence.shape, audit_evidence.dtype, audit_evidence.requires_grad),
            )
        if bootstrap_critic_obs is not None and (
            bootstrap_critic_obs.ndim != 1
            or bootstrap_critic_obs.shape != audit_evidence.shape
            or bootstrap_critic_obs.dtype is not torch.float32
            or bootstrap_critic_obs.device != audit_evidence.device
            or bootstrap_critic_obs.requires_grad
            or not bool(torch.isfinite(bootstrap_critic_obs).all().item())
        ):
            _fail(
                "timeout bootstrap observation violates the ordinary critic contract",
                failure_code="bootstrap_tensor_contract",
                stage="sidecar_create",
                expected=(audit_evidence.shape, torch.float32, audit_evidence.device, False),
                actual=(
                    getattr(bootstrap_critic_obs, "shape", None),
                    getattr(bootstrap_critic_obs, "dtype", None),
                    getattr(bootstrap_critic_obs, "device", None),
                    getattr(bootstrap_critic_obs, "requires_grad", None),
                ),
            )
        if bootstrap_critic_obs is not None and not torch.equal(bootstrap_critic_obs, audit_evidence):
            _fail(
                "timeout audit and bootstrap projections must come from the same evidence",
                failure_code="same_evidence_projection",
                stage="sidecar_create",
                expected="exact numerical equality",
                actual="tensor values differ",
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_TERMINAL_CRITIC_SIDECAR_V2)
        object.__setattr__(instance, "profile_schema_version", ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION)
        object.__setattr__(instance, "scale_contract_version", EVENT_POLICY_SCALE_V2_CONTRACT_VERSION)
        object.__setattr__(instance, "critic_schema_version", critic_schema_version)
        object.__setattr__(instance, "env_id", key.env_id)
        object.__setattr__(instance, "episode_generation", key.episode_generation)
        object.__setattr__(instance, "transition_generation", key.transition_generation)
        object.__setattr__(instance, "termination_reason", reason)
        object.__setattr__(instance, "terminated", terminated)
        object.__setattr__(instance, "truncated", truncated)
        object.__setattr__(instance, "published_store_version", published_store_version)
        object.__setattr__(instance, "bootstrap_projection_valid", bootstrap_valid)
        object.__setattr__(instance, "critic_dimension", int(audit_evidence.numel()))
        object.__setattr__(instance, "critic_dtype", audit_evidence.dtype)
        object.__setattr__(instance, "critic_device", audit_evidence.device)
        object.__setattr__(instance, "_source_p2_publication_identity", source_p2_publication_identity)
        object.__setattr__(instance, "_terminal_audit_projection", terminal_audit_projection._clone())
        object.__setattr__(
            instance,
            "_bootstrap_critic_obs",
            None if bootstrap_critic_obs is None else _readonly_tensor(bootstrap_critic_obs),
        )
        object.__setattr__(instance, "_critic_block_layout", critic_block_layout)
        object.__setattr__(instance, "_physical_provenance", _readonly_mapping(physical_provenance))
        return instance

    @property
    def key(self) -> _TerminalTransitionKey:
        return _TerminalTransitionKey(
            self.env_id,
            self.episode_generation,
            self.transition_generation,
        )

    @property
    def source_p2_publication_identity(self) -> object:
        return self._source_p2_publication_identity

    @property
    def terminal_audit_projection(self) -> TerminalAuditProjectionV2:
        return self._terminal_audit_projection._clone()

    @property
    def bootstrap_critic_obs(self) -> torch.Tensor | None:
        if self._bootstrap_critic_obs is None:
            return None
        return _readonly_tensor(self._bootstrap_critic_obs)

    @property
    def critic_block_layout(self) -> tuple[EventPolicyNumericalBlockLayoutV2, ...]:
        return self._critic_block_layout

    @property
    def physical_provenance(self) -> Mapping[str, object]:
        return self._physical_provenance

    def _clone_for_historical(self) -> "EventTerminalCriticSidecarV2":
        return self._create(
            key=self.key,
            reason=self.termination_reason,
            terminated=self.terminated,
            truncated=self.truncated,
            published_store_version=self.published_store_version,
            source_p2_publication_identity=self._source_p2_publication_identity,
            terminal_audit_projection=self._terminal_audit_projection,
            bootstrap_critic_obs=self._bootstrap_critic_obs,
            critic_schema_version=self.critic_schema_version,
            critic_block_layout=self._critic_block_layout,
            physical_provenance=self._physical_provenance,
        )

    def _validate_artifact_binding(
        self,
        *,
        key: _TerminalTransitionKey,
        termination_reason: int,
        terminated: bool,
        truncated: bool,
        published_store_version: int,
    ) -> None:
        actual = (
            (self.env_id, self.episode_generation, self.transition_generation),
            self.termination_reason,
            self.terminated,
            self.truncated,
            self.published_store_version,
        )
        expected = (
            (key.env_id, key.episode_generation, key.transition_generation),
            termination_reason,
            terminated,
            truncated,
            published_store_version,
        )
        if actual != expected:
            _fail(
                "terminal sidecar differs from its authoritative artifact row",
                failure_code="sidecar_artifact_binding",
                stage="sidecar_binding",
                expected=expected,
                actual=actual,
            )


def _validate_snapshot_domain(
    snapshot: object,
    *,
    E: int,
    M: int,
    N: int,
    device: torch.device,
) -> PreResetCriticPhysicalSnapshotV2:
    if type(snapshot) is not PreResetCriticPhysicalSnapshotV2:
        _fail(
            "terminal projection requires the exact pre-reset physical snapshot type",
            failure_code="physical_snapshot_type",
            stage="terminal_projection_prevalidation",
            expected=PreResetCriticPhysicalSnapshotV2,
            actual=type(snapshot),
        )
    if (snapshot.num_envs, snapshot.M, snapshot.N, snapshot.device) != (E, M, N, device):
        _fail(
            "pre-reset physical snapshot differs from the lifecycle domain",
            failure_code="physical_snapshot_domain",
            stage="terminal_projection_prevalidation",
            expected=(E, M, N, device),
            actual=(snapshot.num_envs, snapshot.M, snapshot.N, snapshot.device),
        )
    return snapshot


def build_event_terminal_critic_sidecars_v2(
    *,
    physical_snapshot: PreResetCriticPhysicalSnapshotV2,
    current_publication: _EventRuntimeCurrentPublication,
) -> tuple[EventTerminalCriticSidecarV2 | None, ...]:
    """Bind one capture to finalized P2 and project only authoritative done rows."""

    if type(current_publication) is not _EventRuntimeCurrentPublication:
        _fail(
            "terminal sidecars require the exact prepared P2 publication",
            failure_code="terminal_publication_type",
            stage="terminal_projection",
            expected=_EventRuntimeCurrentPublication,
            actual=type(current_publication),
        )
    view = current_publication.lifecycle_view
    result = current_publication.result
    state = current_publication.lifecycle_state
    if (
        type(view) is not PublishedLifecycleView
        or type(result) is not LifecycleTransitionResult
        or type(state) is not LifecycleStateSnapshot
        or view.result is not result
    ):
        _fail(
            "terminal sidecars require one finalized lifecycle view/result identity",
            failure_code="terminal_publication_binding",
            stage="terminal_projection",
            expected=(PublishedLifecycleView, LifecycleTransitionResult, LifecycleStateSnapshot),
            actual=(type(view), type(result), type(state)),
        )
    E = state.num_envs
    snapshot = _validate_snapshot_domain(
        physical_snapshot,
        E=E,
        M=physical_snapshot.M,
        N=physical_snapshot.N,
        device=state.device,
    )
    M, N = snapshot.M, snapshot.N
    tensors = {
        "task_state": state.task_state,
        "robot_state": state.robot_state,
        "ownership": state.ownership,
        "failed_pairs": state.cumulative_failed_pairs,
        "completion_count": state.completion_count,
        "termination_reason": state.termination_reason,
    }
    expected_shapes = {
        "task_state": (E, N),
        "robot_state": (E, M),
        "ownership": (E, N),
        "failed_pairs": (E, M, N),
        "completion_count": (E, M),
        "termination_reason": (E,),
    }
    for name, value in tensors.items():
        dtype = torch.bool if name == "failed_pairs" else torch.int64
        if tuple(value.shape) != expected_shapes[name] or value.dtype is not dtype or value.device != state.device:
            _fail(
                "finalized P2 lifecycle tensor violates the terminal projector domain",
                failure_code="terminal_lifecycle_tensor_contract",
                stage="terminal_projection",
                field_name=name,
                expected=(expected_shapes[name], dtype, state.device),
                actual=(value.shape, value.dtype, value.device),
            )
    if (
        bool(((tensors["task_state"] < 0) | (tensors["task_state"] >= len(TaskLifecycleState))).any().item())
        or bool(((tensors["robot_state"] < 0) | (tensors["robot_state"] >= len(RobotLifecycleState))).any().item())
        or bool(((tensors["ownership"] < -1) | (tensors["ownership"] >= M)).any().item())
        or bool(((tensors["completion_count"] < 0) | (tensors["completion_count"] > N)).any().item())
    ):
        _fail(
            "finalized P2 values are outside terminal projector semantic domains",
            failure_code="terminal_lifecycle_value_range",
            stage="terminal_projection",
            expected="canonical enum/owner/completion ranges",
            actual="out-of-range value",
        )
    descriptor = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=snapshot.scale_contract
    )
    common = _project_common_blocks(
        physical=snapshot._physical_evidence,
        task_state=tensors["task_state"],
        robot_state=tensors["robot_state"],
        ownership=tensors["ownership"],
        failed_pairs=tensors["failed_pairs"],
        completion_count=tensors["completion_count"],
        scale=descriptor["scale_contract"],
    )
    critic_blocks = descriptor["critic_schema"]["blocks"]
    critic_layout = _layout(critic_blocks, common)
    semantic = torch.cat(
        [common[block["name"]].reshape(E, -1) for block in critic_blocks],
        dim=-1,
    ).to(torch.float32).contiguous()
    expected_dimension = descriptor["critic_schema"]["dimension"]
    if tuple(semantic.shape) != (E, expected_dimension):
        _fail(
            "terminal projection differs from the manifest-derived critic dimension",
            failure_code="terminal_projection_shape",
            stage="terminal_projection",
            expected=(E, expected_dimension),
            actual=tuple(semantic.shape),
        )

    env_ids = current_publication.env_id
    episodes = current_publication.episode_generation
    transitions = current_publication.transition_generation
    terminated = current_publication.terminated
    truncated = current_publication.truncated
    sidecars: list[EventTerminalCriticSidecarV2 | None] = []
    for row in range(E):
        reason = int(tensors["termination_reason"][row].item())
        done = bool(terminated[row].item()) or bool(truncated[row].item())
        if reason == int(TerminationReason.NONE):
            if done:
                _fail(
                    "done flags cannot exist without an authoritative terminal reason",
                    failure_code="terminal_done_reason_binding",
                    stage="terminal_projection",
                    expected=False,
                    actual=True,
                )
            sidecars.append(None)
            continue
        if not done:
            _fail(
                "authoritative terminal reason lacks its projected done flag",
                failure_code="terminal_done_reason_binding",
                stage="terminal_projection",
                expected=True,
                actual=False,
            )
        key = _TerminalTransitionKey(
            int(env_ids[row].item()),
            int(episodes[row].item()),
            int(transitions[row].item()),
        )
        audit = TerminalAuditProjectionV2._create(
            key=key,
            termination_reason=reason,
            critic_schema_version=EVENT_POLICY_CRITIC_SCHEMA_V2,
            semantic_evidence=semantic[row],
        )
        bootstrap = semantic[row] if reason == int(TerminationReason.TIME_LIMIT) else None
        sidecars.append(
            EventTerminalCriticSidecarV2._create(
                key=key,
                reason=reason,
                terminated=bool(terminated[row].item()),
                truncated=bool(truncated[row].item()),
                published_store_version=current_publication.store_version,
                source_p2_publication_identity=current_publication.publication_identity,
                terminal_audit_projection=audit,
                bootstrap_critic_obs=bootstrap,
                critic_schema_version=EVENT_POLICY_CRITIC_SCHEMA_V2,
                critic_block_layout=critic_layout,
                physical_provenance={
                    "capture_schema_version": snapshot.schema_version,
                    "physical_evidence_schema_version": snapshot._physical_evidence.schema_version,
                    "physical_source": snapshot._physical_evidence.provenance,
                    "capture_timing": "ScanMobileManipulatorEnv._get_dones before DirectMARLEnv autoreset",
                    "post_reset_reconstruction": False,
                    "termination_reason_is_critic_input": False,
                    "critic_evaluation_performed": False,
                },
            )
        )
    return tuple(sidecars)


__all__ = ()
