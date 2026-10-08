"""CR12 execution identities and delivery, with no physics or task authority.

The adapter observes the retained production P2 stream.  It never writes task
state, allocates claim/consume tokens, or constructs an authority result.
"""
from __future__ import annotations

if __name__ != "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_cr12_execution_adapter":
    raise ImportError("CanonicalModuleIdentityError: CR12 adapter requires its canonical module key")

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

import numpy as np
import torch

from .assignment_initial_claim_runtime import (
    EffectiveAssignmentCommitArtifact,
    _CurrentPublicationProvenanceKind,
)
from .assignment_lifecycle_transition_contract import RobotLifecycleState, TaskLifecycleState
from .assignment_interstep_claim_window_runtime import _ClaimWindowFencePhase


class Cr12ExecutionAdapterError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.failure_code = code
        super().__init__(f"{code}: {message}")


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Cr12ExecutionAdapterError(code, message)


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(v) for v in value)
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise Cr12ExecutionAdapterError("metadata_type", f"Unsupported metadata value: {type(value)}")


@dataclass(frozen=True, slots=True, eq=False)
class ExecutionBinding:
    run_instance_id: str
    domain_identity: object = field(repr=False)
    env_id: int
    episode_generation: int
    robot_id: int
    task_id: int
    claim_token: int
    birth_artifact: EffectiveAssignmentCommitArtifact = field(repr=False)
    goal_id: str
    capture_id: str
    attempt_id: str

    def summary(self) -> dict:
        return {"run_instance_id": self.run_instance_id, "env_id": self.env_id,
            "episode_generation": self.episode_generation, "robot_id": self.robot_id,
            "task_id": self.task_id, "claim_token": self.claim_token,
            "source_store_version": self.birth_artifact.source_store_version,
            "committed_store_version": self.birth_artifact.committed_store_version,
            "goal_id": self.goal_id, "capture_id": self.capture_id, "attempt_id": self.attempt_id}


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RawCaptureCustody:
    """Independent RGBA on immutable bytes storage, retained past retire/reset."""
    rgba: np.ndarray = field(repr=False)
    metadata: Mapping = field(repr=False)

    def __init__(self, *, rgba: np.ndarray, metadata: Mapping):
        _require(isinstance(rgba, np.ndarray) and rgba.dtype == np.uint8
            and rgba.ndim == 3 and rgba.shape[2] == 4 and rgba.size > 0,
            "custody_rgba", "Actual nonempty uint8 RGBA is required")
        _require(isinstance(metadata, Mapping) and metadata.get("fresh") is True,
            "custody_fresh", "Custody requires the backend's accepted fresh metadata")
        for key in ("goal_id", "capture_id", "attempt_id"):
            _require(type(metadata.get(key)) is str and bool(metadata[key]), "custody_identity", key)
        _require(type(metadata.get("rendering_frame")) is int and type(metadata.get("source_frame")) is int
            and metadata["rendering_frame"] == metadata.get("source_frame"),
            "custody_frame", "Source and RGBA must have the same accepted frame")
        copied = np.frombuffer(rgba.tobytes(order="C"), dtype=np.uint8).reshape(rgba.shape)
        object.__setattr__(self, "rgba", copied)
        object.__setattr__(self, "metadata", _freeze(metadata))


@dataclass(frozen=True, slots=True)
class ExecutionBoundaryEvidence:
    """Host's latest guarded block-end sample; never the cached terminal sample."""
    physics_step: int
    goal_id: str
    capture_id: str
    off_confirmed: bool
    holding: bool
    resource_healthy: bool
    native_valid: bool
    no_pending_data: bool
    continuous_hold: bool

    def __post_init__(self):
        _require(type(self.physics_step) is int and self.physics_step >= 0, "boundary_step", "Invalid physics step")
        for key in ("off_confirmed", "holding", "resource_healthy", "native_valid", "no_pending_data", "continuous_hold"):
            _require(type(getattr(self, key)) is bool, "boundary_bool", key)
        _require(type(self.goal_id) is str and type(self.capture_id) is str, "boundary_identity", "IDs must be strings")


@dataclass(frozen=True, slots=True, eq=False)
class PendingExecutionResult:
    binding: ExecutionBinding
    outcome: str
    acquired: bool
    custody: RawCaptureCustody | None = field(repr=False)
    physics_step: int
    metadata: Mapping = field(repr=False)


@dataclass(frozen=True, slots=True, eq=False)
class ExecutionDeliveryReceipt:
    binding: ExecutionBinding
    pending: PendingExecutionResult = field(repr=False)
    result: object = field(repr=False)
    facts_consume_token: int
    authority_receipt_id: int
    transition_generation: int

    def summary(self):
        return {**self.binding.summary(), "outcome": self.pending.outcome,
            "acquired": self.pending.acquired, "facts_consume_token": self.facts_consume_token,
            "authority_receipt_id": self.authority_receipt_id,
            "transition_generation": self.transition_generation}


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _StagedPreResetExecutionReport:
    """Factory-only report checked against the same retained P2 before producer."""
    _adapter: object = field(repr=False)
    _physical_report: object = field(repr=False)
    _publication: object = field(repr=False)
    _binding: ExecutionBinding | None = field(repr=False)
    _pending: PendingExecutionResult | None = field(repr=False)
    boundary: ExecutionBoundaryEvidence

    def __init__(self, *args, **kwargs):
        raise Cr12ExecutionAdapterError("report_factory", "Use adapter.build_report")

    @classmethod
    def _create(cls, adapter, physical_report, boundary):
        obj = object.__new__(cls)
        for name, value in (("_adapter", adapter), ("_physical_report", physical_report),
                ("_publication", adapter._admitted), ("_binding", adapter._binding),
                ("_pending", adapter._pending), ("boundary", boundary)):
            object.__setattr__(obj, name, value)
        return obj

    def _validate_for_domain(self, domain_identity, publication, snapshot):
        _require(type(self._adapter) is Cr12ExecutionAdapter, "report_adapter", "Exact adapter required")
        return self._adapter._validate_report(self, domain_identity, publication, snapshot)


class Cr12ExecutionAdapter:
    """One bounded E1/M1/N2 execution stream; retained bindings are not owners."""

    def __init__(self, *, current_read_port, run_instance_id: str, env_id: int = 0, robot_id: int = 0):
        from .assignment_event_profile_runtime_domain import _EventProfileLifecycleCurrentReadPort
        _require(type(current_read_port) is _EventProfileLifecycleCurrentReadPort,
            "read_port", "A real retained-domain current read port is required")
        _require(type(run_instance_id) is str and bool(run_instance_id), "run_identity", "Nonempty run identity required")
        identity = current_read_port._domain.identity
        _require((identity.num_envs, identity.num_robots, identity.num_tasks) == (1, 1, 2),
            "integration_scale", "This bounded adapter supports E1/M1/N2 only")
        _require(robot_id == 0 and type(robot_id) is int and type(env_id) is int,
            "robot_identity", "Single CR12 robot index must be zero")
        self._port = current_read_port
        self.run_instance_id, self.env_id, self.robot_id = run_instance_id, env_id, robot_id
        self.domain_identity = current_read_port.domain_identity
        self._observed = self._admitted = self._binding = self._pending = self._report = None
        self._committed = self._last_ack = self._delivery = None
        self._last_boundary_step = -1
        self._history = []
        self.bind_count = self.continuation_count = self.transition_count = 0

    @property
    def binding(self): return self._binding

    @property
    def history(self): return tuple(self._history)

    def pending_result(self): return self._pending

    def _row(self, pub):
        ids = tuple(int(x) for x in pub.env_id.tolist())
        _require(self.env_id in ids, "environment_identity", "P2 does not cover this environment")
        return ids.index(self.env_id)

    def observe_episode_reset(self):
        _require(self._binding is None and self._pending is None and self._report is None,
            "reset_live_request", "Retire acknowledged requests before reset")
        pub = self._port.read_current(); row = self._row(pub)
        _require(pub.result is None and pub.provenance[row].kind is _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
            "reset_publication", "Observe a real canonical episode rebuild")
        if self._observed is not None:
            old = self._observed
            _require(int(pub.episode_generation[row]) == int(old.episode_generation[self._row(old)]) + 1
                and int(pub.transition_generation[row]) == int(old.transition_generation[self._row(old)]),
                "reset_generation", "Reset must increment episode and preserve transition")
        self._observed = pub

    def _active_matches(self, pub, binding):
        row = self._row(pub); state = pub.lifecycle_state
        _require(binding.domain_identity is self.domain_identity
            and int(pub.episode_generation[row]) == binding.episode_generation,
            "binding_episode", "Old or foreign episode binding")
        _require(int(state.ownership[row, binding.task_id]) == binding.robot_id
            and int(state.task_state[row, binding.task_id]) in tuple(int(s) for s in
                (TaskLifecycleState.CLAIMED, TaskLifecycleState.NAVIGATING, TaskLifecycleState.ALIGNING))
            and int(state.robot_state[row, binding.robot_id]) == int(RobotLifecycleState.EXECUTING),
            "binding_owner", "Current P2 no longer authorizes this active execution")

    def bind_effective_assignment(self, assignment):
        _require(self._report is None and self._admitted is None, "unacknowledged_transition", "A prior step must be acknowledged")
        pub = self._port.read_current(); row = self._row(pub)
        self._require_admission(pub)
        _require(type(assignment) is torch.Tensor and assignment.dtype == torch.int64
            and tuple(assignment.shape) == (1, 1) and assignment.device == pub.env_id.device,
            "assignment_shape", "Expected exact E1/M1 integer assignment on the domain device")
        task = int(assignment[row, self.robot_id]); artifact = pub.provenance[row].assignment_artifact
        if self._observed is not None and pub is not self._observed:
            _require(type(artifact) is EffectiveAssignmentCommitArtifact
                and artifact.source_publication is self._observed,
                "publication_gap", "Every prior authority result and claim must be observed")
        if self._binding is not None:
            _require(self._pending is None, "pending_not_retired", "A completed request must be retired before another step")
            binding = self._binding
            _require(task == binding.task_id, "assignment_switch", "Cannot switch a live binding")
            self._active_matches(pub, binding)
            if artifact is not None:
                _require(artifact is binding.birth_artifact, "claim_replaced", "A different claim cannot continue the old request")
            self.continuation_count += 1
            self._admitted = pub
            return binding, False
        _require(0 <= task < 2, "assignment_missing", "Integration steps require a real active claim")
        _require(type(artifact) is EffectiveAssignmentCommitArtifact
            and artifact._domain_identity is self.domain_identity
            and artifact.committed_store_version == pub.store_version,
            "claim_source", "New execution requires this P2's genuine claim artifact")
        selected = tuple(int(x) for x in artifact.selected_env_ids.tolist())
        _require(self.env_id in selected, "claim_row", "Claim artifact does not cover this environment")
        selected_row = selected.index(self.env_id)
        _require(int(artifact.effective_task_by_robot[selected_row, self.robot_id]) == task
            and int(artifact.episode_generation[selected_row]) == int(pub.episode_generation[row]),
            "claim_assignment", "Claim batch does not create this assignment")
        suffix = f"e{int(pub.episode_generation[row])}_r{self.robot_id}_t{task}_claim{artifact.token}"
        binding = ExecutionBinding(self.run_instance_id, self.domain_identity, self.env_id,
            int(pub.episode_generation[row]), self.robot_id, task, artifact.token, artifact,
            f"{self.run_instance_id}_{suffix}_goal", f"{self.run_instance_id}_{suffix}_capture", self.run_instance_id)
        self._active_matches(pub, binding)
        self._binding = binding; self._admitted = pub; self.bind_count += 1
        return binding, True

    def _require_admission(self, publication):
        fence = self._port._domain.interstep_fence_read_port.read()
        _require(fence.phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT
            and fence.active_step is not None
            and fence.active_step.admitted_publication is publication,
            "execution_admission", "Execution binding/report requires this exact active physical-step admission")

    def record_pending(self, binding, *, outcome, acquired, custody, physics_step, metadata):
        _require(binding is self._binding and self._admitted is not None, "result_binding", "Result must belong to the active admitted binding")
        _require(outcome in ("completed", "cancelled", "completed_unavailable"), "result_outcome", "Unsupported execution outcome")
        _require(type(acquired) is bool and type(physics_step) is int and physics_step >= 0,
            "result_shape", "Invalid acquisition or physics step")
        _require(isinstance(metadata, Mapping), "result_metadata", "Result metadata mapping required")
        if self._pending is not None:
            _require(self._pending.binding is binding and self._pending.outcome == outcome
                and self._pending.acquired == acquired and self._pending.custody is custody,
                "result_replacement", "A retained terminal result is immutable")
            return self._pending
        if outcome == "cancelled":
            _require(not acquired and custody is None, "cancel_has_data", "An acquired result cannot become a no-data cancellation")
        else:
            _require(acquired and type(custody) is RawCaptureCustody,
                "result_custody", "Completion requires real independent RGBA custody")
            for key in ("goal_id", "capture_id", "attempt_id"):
                _require(custody.metadata[key] == getattr(binding, key), "result_capture_identity", key)
        self._pending = PendingExecutionResult(binding, outcome, acquired, custody, physics_step, _freeze(metadata))
        return self._pending

    def build_report(self, *, boundary, coverage_before_transition, physical_truncated,
                     time_limit_reached, pre_reset_critic_physical_snapshot):
        from .assignment_event_profile_runtime_domain import _StagedPreResetPhysicalReport
        _require(self._admitted is not None and self._report is None and self._delivery is None,
            "report_sequence", "Build one report per admitted, unacknowledged step")
        _require(type(boundary) is ExecutionBoundaryEvidence, "boundary_type", "Typed current boundary required")
        _require(pre_reset_critic_physical_snapshot is not None, "critic_required", "Integration requires an actual pre-reset physical snapshot")
        pub = self._admitted
        self._require_admission(pub)
        physical = _StagedPreResetPhysicalReport(device=pub.env_id.device,
            coverage_before_transition=coverage_before_transition,
            raw_new_candidate=torch.zeros((1, 1, 2), dtype=torch.bool, device=pub.env_id.device),
            physical_truncated=physical_truncated, time_limit_reached=time_limit_reached,
            pre_reset_critic_physical_snapshot=pre_reset_critic_physical_snapshot)
        report = _StagedPreResetExecutionReport._create(self, physical, boundary)
        self._report = report
        try:
            self._validate_report(report, self.domain_identity, self._port.read_current(), pub.lifecycle_state)
        except BaseException:
            self._report = None
            raise
        return report

    def _validate_report(self, report, domain_identity, publication, snapshot):
        _require(report is self._report and self._committed is None and self._delivery is None,
            "report_once", "A stale, foreign or committed report cannot produce new facts")
        _require(domain_identity is self.domain_identity and publication is self._admitted
            and publication is report._publication and self._port.read_current() is publication,
            "report_publication", "Report must bind the exact current admitted P2")
        _require(report._binding is self._binding and report._pending is self._pending,
            "report_binding", "Report binding/pending identity changed")
        binding = self._binding; self._active_matches(publication, binding)
        _require(snapshot.store_version == publication.store_version
            and torch.equal(snapshot.ownership, publication.lifecycle_state.ownership)
            and torch.equal(snapshot.task_state, publication.lifecycle_state.task_state)
            and torch.equal(snapshot.robot_state, publication.lifecycle_state.robot_state),
            "report_prestate", "Producer prestate must match the admitted authoritative state")
        physical = report._physical_report
        _require(torch.equal(physical._coverage_before_transition,
            publication.lifecycle_state.task_state == int(TaskLifecycleState.COMPLETED)),
            "report_coverage", "Coverage must be projected from authoritative completed tasks")
        boundary = report.boundary
        _require(boundary.physics_step > self._last_boundary_step and boundary.native_valid,
            "boundary_native", "A fresh valid physical boundary is required")
        _require(boundary.goal_id == binding.goal_id and boundary.capture_id == binding.capture_id,
            "boundary_binding", "Block-end evidence must belong to the active request")
        if bool(physical._time_limit_reached.any()):
            _require(boundary.off_confirmed and boundary.holding and boundary.resource_healthy
                and boundary.continuous_hold, "unsafe_time_limit", "A terminal deadline cannot hide unsafe cleanup")
        completion = torch.zeros_like(physical._raw_new_candidate)
        release = torch.zeros_like(completion)
        unavailable = torch.zeros((1, 1), dtype=torch.bool, device=completion.device)
        if self._pending is not None:
            p = self._pending
            _require(boundary.physics_step >= p.physics_step, "boundary_stale", "Block-end evidence predates the terminal sample")
            if p.outcome in ("completed", "cancelled"):
                _require(boundary.off_confirmed and boundary.holding and boundary.resource_healthy
                    and boundary.continuous_hold, "boundary_handoff", "OFF, continued hold and resource health must still hold at block end")
            if p.outcome == "cancelled":
                _require(boundary.no_pending_data and not p.acquired and p.custody is None,
                    "cancel_data_race", "No-data cancellation requires the latest backend no-data check")
                release[0, self.robot_id, binding.task_id] = True
            else:
                _require(type(p.custody) is RawCaptureCustody and p.acquired,
                    "report_custody", "Acquired data must remain held before producer")
                completion[0, self.robot_id, binding.task_id] = True
                if p.outcome == "completed_unavailable":
                    _require(not boundary.resource_healthy or not boundary.off_confirmed,
                        "unavailable_reason", "C+U requires an actual close/resource failure")
                    unavailable[0, self.robot_id] = True
        return completion, release, unavailable

    def _register_committed(self, report, outcome):
        # Called by the retained domain only after its actual transaction returned.
        self._committed = (report, outcome)

    def ack_authority_delivery(self, outcome):
        if self._last_ack is not None and self._last_ack[0] is outcome:
            return self._last_ack[1]
        _require(self._committed is not None and self._committed[1] is outcome,
            "receipt_source", "Only this report's real completed domain transaction can be acknowledged")
        report = self._committed[0]; result = outcome.result; pub = self._port.read_current()
        _require(pub.result is result and pub.lifecycle_view is outcome.published_view,
            "receipt_publication", "Acknowledge before reset or any subsequent publication")
        row = self._row(pub); old = report._publication
        _require(int(result.episode_generation[row]) == int(old.episode_generation[row])
            and int(result.transition_generation[row]) == int(old.transition_generation[row]) + 1,
            "receipt_generation", "Receipt must belong to this current transition")
        receipt = None
        if self._pending is not None:
            p = self._pending; task = p.binding.task_id
            _require(int(result.updated_ownership[row, task]) == -1,
                "receipt_owner", "Delivery requires authority release of the old owner")
            _require(bool(result.completed_tasks[row, task]) == (p.outcome != "cancelled")
                and bool(result.released_tasks[row, task]) == (p.outcome == "cancelled"),
                "receipt_outcome", "Authority outcome differs from the pending result")
            receipt = ExecutionDeliveryReceipt(p.binding, p, result,
                int(result.facts_consume_token[row]), int(result.authority_receipt_id[row]),
                int(result.transition_generation[row]))
            self._delivery = receipt
            self._history.append(receipt)
        self._last_boundary_step = report.boundary.physics_step
        self._observed = pub; self._admitted = self._report = self._committed = None
        self._last_ack = (outcome, receipt); self.transition_count += 1
        return receipt

    def retire_request(self, binding, receipt):
        _require(binding is self._binding and receipt is self._delivery and receipt is not None
            and receipt.pending is self._pending, "retire_before_receipt", "Retire only the exact acknowledged request")
        self._binding = self._pending = self._delivery = None


LifecycleExecutionAdapter = Cr12ExecutionAdapter
