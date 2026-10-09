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
    goal_id: str | None
    capture_id: str | None
    off_confirmed: bool
    holding: bool
    resource_healthy: bool
    native_valid: bool
    no_pending_data: bool
    continuous_hold: bool
    hold_basis: str = 'scanner_task'
    control_segment_id: str | None = None
    physical_clear: bool = False
    clear_stable_samples: int = 0
    clear_stable_span_s: float = 0.0
    clear_window_start_step: int | None = None
    clear_window_end_step: int | None = None
    peer_park_verified: bool = False
    peer_physics_step: int | None = None

    def __post_init__(self):
        _require(type(self.physics_step) is int and self.physics_step >= 0, "boundary_step", "Invalid physics step")
        for key in ("off_confirmed", "holding", "resource_healthy", "native_valid", "no_pending_data", "continuous_hold"):
            _require(type(getattr(self, key)) is bool, "boundary_bool", key)
        _require((type(self.goal_id) is str and type(self.capture_id) is str)
            or (self.goal_id is None and self.capture_id is None),
            "boundary_identity", "Request IDs must both be strings, or both None for an idle slot")
        _require(self.hold_basis in ('scanner_task', 'clear', 'park'), 'boundary_hold_basis', 'Unknown physical hold basis')
        _require(type(self.physical_clear) is bool and type(self.peer_park_verified) is bool,
            'boundary_clear', 'Clear and peer evidence must be explicit booleans')


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
    """Factory-only full-domain report checked before the single producer."""
    _adapter: object = field(repr=False)
    _physical_report: object = field(repr=False)
    _publication: object = field(repr=False)
    _bindings: tuple = field(repr=False)
    _pendings: tuple = field(repr=False)
    boundaries_by_robot: Mapping

    def __init__(self, *args, **kwargs):
        raise Cr12ExecutionAdapterError("report_factory", "Use adapter.build_report")

    @classmethod
    def _create(cls, adapter, physical_report, boundaries):
        obj = object.__new__(cls)
        for name, value in (("_adapter", adapter), ("_physical_report", physical_report),
                ("_publication", adapter._admitted), ("_bindings", tuple(adapter._bindings)),
                ("_pendings", tuple(adapter._pendings)),
                ("boundaries_by_robot", MappingProxyType(dict(boundaries)))):
            object.__setattr__(obj, name, value)
        return obj

    @property
    def boundary(self):
        self._adapter._require_single()
        return self.boundaries_by_robot[0]

    def _validate_for_domain(self, domain_identity, publication, snapshot):
        _require(type(self._adapter) is Cr12ExecutionAdapter, "report_adapter", "Exact adapter required")
        return self._adapter._validate_report(self, domain_identity, publication, snapshot)


class Cr12ExecutionAdapter:
    """Fixed E1/M1/N2 or E1/M2/N4 stream; execution slots never own tasks."""

    def __init__(self, *, current_read_port, run_instance_id: str, env_id: int = 0,
                 robot_id: int = 0, execution_profile: str = "single_m1n2"):
        from .assignment_event_profile_runtime_domain import _EventProfileLifecycleCurrentReadPort
        _require(type(current_read_port) is _EventProfileLifecycleCurrentReadPort,
            "read_port", "A real retained-domain current read port is required")
        _require(type(run_instance_id) is str and bool(run_instance_id), "run_identity", "Nonempty run identity required")
        profiles = {"single_m1n2": (1, 1, 2), "dual_m2n4": (1, 2, 4), "shared_m2n1": (1, 2, 1)}
        _require(type(execution_profile) is str and execution_profile in profiles,
            "integration_scale", "Only the fixed CR12 execution profiles are supported")
        identity = current_read_port._domain.identity
        dimensions = (identity.num_envs, identity.num_robots, identity.num_tasks)
        _require(dimensions == profiles[execution_profile], "integration_scale", "Profile and retained domain dimensions differ")
        _require(type(robot_id) is int and robot_id == 0 and type(env_id) is int,
            "robot_identity", "The adapter covers all robot slots; legacy robot index must be zero")
        self._port = current_read_port
        self.run_instance_id, self.env_id, self.robot_id = run_instance_id, env_id, robot_id
        self.execution_profile = execution_profile
        self.num_robots, self.num_tasks = dimensions[1:]
        self.robot_ids = tuple(range(self.num_robots))
        self.domain_identity = current_read_port.domain_identity
        self._observed = self._admitted = self._report = self._committed = self._last_ack = None
        self._bindings = [None] * self.num_robots
        self._pendings = [None] * self.num_robots
        self._deliveries = [None] * self.num_robots
        self._last_boundary_step = -1
        self._history = []
        self.bind_count = self.continuation_count = self.transition_count = 0

    def _require_single(self):
        _require(self.num_robots == 1, "singular_api", "Use the plural API for the dual profile")

    def _robot_index(self, robot_id):
        _require(type(robot_id) is int and robot_id in self.robot_ids, "robot_identity", "Unknown robot slot")
        return robot_id

    @property
    def binding(self):
        self._require_single()
        return self._bindings[0]

    def binding_for(self, robot_id):
        return self._bindings[self._robot_index(robot_id)]

    @property
    def history(self): return tuple(self._history)

    def pending_result(self, robot_id=0):
        return self._pendings[self._robot_index(robot_id)]

    def _row(self, pub):
        ids = tuple(int(x) for x in pub.env_id.tolist())
        _require(self.env_id in ids, "environment_identity", "P2 does not cover this environment")
        return ids.index(self.env_id)

    def observe_episode_reset(self):
        _require(not any(self._bindings) and not any(self._pendings) and not any(self._deliveries)
            and self._report is None and self._admitted is None and self._committed is None,
            "reset_live_request", "Retire all acknowledged requests before reset")
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
        _require(type(binding) is ExecutionBinding and binding.domain_identity is self.domain_identity
            and binding.run_instance_id == self.run_instance_id and binding.env_id == self.env_id
            and int(pub.episode_generation[row]) == binding.episode_generation,
            "binding_episode", "Old or foreign episode binding")
        _require(binding.robot_id in self.robot_ids and 0 <= binding.task_id < self.num_tasks
            and int(state.ownership[row, binding.task_id]) == binding.robot_id
            and int(state.task_state[row, binding.task_id]) in tuple(int(s) for s in
                (TaskLifecycleState.CLAIMED, TaskLifecycleState.NAVIGATING, TaskLifecycleState.ALIGNING))
            and int(state.robot_state[row, binding.robot_id]) == int(RobotLifecycleState.EXECUTING),
            "binding_owner", "Current P2 no longer authorizes this active execution")
        artifact = binding.birth_artifact
        _require(type(artifact) is EffectiveAssignmentCommitArtifact
            and artifact._domain_identity is self.domain_identity and artifact.token == binding.claim_token,
            "binding_birth", "Retained binding must preserve its genuine birth artifact")
        selected = tuple(int(x) for x in artifact.selected_env_ids.tolist())
        _require(self.env_id in selected, "binding_birth", "Birth artifact does not cover this environment")
        ar = selected.index(self.env_id)
        _require(int(artifact.effective_task_by_robot[ar, binding.robot_id]) == binding.task_id
            and int(artifact.episode_generation[ar]) == binding.episode_generation,
            "binding_birth", "Birth artifact does not create this robot/task/episode")

    def _idle_matches(self, pub, robot_id):
        state = pub.lifecycle_state; row = self._row(pub)
        _require(self.num_robots == 2 and not bool((state.ownership[row] == robot_id).any())
            and int(state.robot_state[row, robot_id]) in
                (int(RobotLifecycleState.NEEDS_ASSIGNMENT), int(RobotLifecycleState.WAITING_FOR_TASK)),
            "idle_owner", "Idle hold requires a healthy robot without an authoritative assignment")

    def bind_effective_assignment(self, assignment):
        self._require_single()
        return self.bind_effective_assignments(assignment)[0]

    def bind_effective_assignments(self, assignment):
        _require(self._report is None and self._admitted is None and self._committed is None
            and not any(self._deliveries), "unacknowledged_transition", "A prior step and all deliveries must be retired")
        pub = self._port.read_current(); row = self._row(pub)
        self._require_admission(pub)
        _require(type(assignment) is torch.Tensor and assignment.dtype == torch.int64
            and tuple(assignment.shape) == (1, self.num_robots) and assignment.device == pub.env_id.device,
            "assignment_shape", "Expected exact integer assignment for this fixed domain on its device")
        artifact = pub.provenance[row].assignment_artifact
        if self._observed is not None and pub is not self._observed:
            _require(type(artifact) is EffectiveAssignmentCommitArtifact
                and artifact.source_publication is self._observed,
                "publication_gap", "Every prior authority result and claim must be observed")
        ar = None
        if artifact is not None:
            _require(type(artifact) is EffectiveAssignmentCommitArtifact
                and artifact._domain_identity is self.domain_identity
                and artifact.committed_store_version == pub.store_version,
                "claim_source", "Claim provenance must be this current retained publication")
            selected = tuple(int(x) for x in artifact.selected_env_ids.tolist())
            _require(self.env_id in selected, "claim_row", "Claim artifact does not cover this environment")
            ar = selected.index(self.env_id)
            _require(int(artifact.episode_generation[ar]) == int(pub.episode_generation[row]),
                "claim_assignment", "Claim artifact belongs to another episode")
        choices = []
        # Validate the complete admitted batch before installing any new slot.
        for robot in self.robot_ids:
            task = int(assignment[row, robot]); binding = self._bindings[robot]
            _require(self._pendings[robot] is None, "pending_not_retired", "Retire terminal results before another step")
            claimed = None if artifact is None else int(artifact.effective_task_by_robot[ar, robot])
            if binding is not None:
                _require(task == binding.task_id, "assignment_switch", "Cannot switch a live binding")
                self._active_matches(pub, binding)
                if artifact is not None:
                    _require(artifact is binding.birth_artifact or claimed == -1,
                        "claim_replaced", "This batch cannot replace a live robot's birth claim")
                choices.append((binding, False))
            elif task == -1 and self.num_robots == 2:
                self._idle_matches(pub, robot)
                _require(claimed in (None, -1), "idle_claim", "Idle slot cannot hide a new claim")
                choices.append((None, False))
            else:
                _require(0 <= task < self.num_tasks, "assignment_missing", "Execution requires a real active claim")
                _require(type(artifact) is EffectiveAssignmentCommitArtifact, "claim_source", "New execution requires a genuine birth artifact")
                _require(claimed == task, "claim_assignment", "Claim batch does not create this robot's assignment")
                suffix = f"e{int(pub.episode_generation[row])}_r{robot}_t{task}_claim{artifact.token}"
                binding = ExecutionBinding(self.run_instance_id, self.domain_identity, self.env_id,
                    int(pub.episode_generation[row]), robot, task, artifact.token, artifact,
                    f"{self.run_instance_id}_{suffix}_goal", f"{self.run_instance_id}_{suffix}_capture", self.run_instance_id)
                self._active_matches(pub, binding)
                choices.append((binding, True))
        for robot, (binding, new) in enumerate(choices):
            self._bindings[robot] = binding
            self.bind_count += int(new)
            self.continuation_count += int(binding is not None and not new)
        self._admitted = pub
        return tuple(choices)

    def _require_admission(self, publication):
        fence = self._port._domain.interstep_fence_read_port.read()
        _require(fence.phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT
            and fence.active_step is not None
            and fence.active_step.admitted_publication is publication,
            "execution_admission", "Execution binding/report requires this exact active physical-step admission")

    def record_pending(self, binding, *, outcome, acquired, custody, physics_step, metadata):
        _require(type(binding) is ExecutionBinding and binding.robot_id in self.robot_ids
            and binding is self._bindings[binding.robot_id] and self._admitted is not None,
            "result_binding", "Result must belong to the active admitted binding")
        robot = binding.robot_id
        _require(outcome in ("completed", "cancelled", "completed_unavailable"), "result_outcome", "Unsupported execution outcome")
        _require(type(acquired) is bool and type(physics_step) is int and physics_step >= 0,
            "result_shape", "Invalid acquisition or physics step")
        _require(isinstance(metadata, Mapping), "result_metadata", "Result metadata mapping required")
        pending = self._pendings[robot]
        if pending is not None:
            _require(pending.binding is binding and pending.outcome == outcome
                and pending.acquired == acquired and pending.custody is custody
                and pending.physics_step == physics_step and pending.metadata == _freeze(metadata),
                "result_replacement", "A retained terminal result is immutable")
            return pending
        if outcome == "cancelled":
            _require(not acquired and custody is None, "cancel_has_data", "An acquired result cannot become a no-data cancellation")
        else:
            _require(acquired and type(custody) is RawCaptureCustody,
                "result_custody", "Completion requires real independent RGBA custody")
            for key in ("goal_id", "capture_id", "attempt_id"):
                _require(custody.metadata[key] == getattr(binding, key), "result_capture_identity", key)
            for key in ("robot_id", "task_id", "claim_token"):
                if key in custody.metadata:
                    _require(type(custody.metadata[key]) is int and custody.metadata[key] == getattr(binding, key),
                        "result_capture_identity", key)
        pending = PendingExecutionResult(binding, outcome, acquired, custody, physics_step, _freeze(metadata))
        self._pendings[robot] = pending
        return pending

    def build_report(self, *, boundary=None, boundaries_by_robot=None, coverage_before_transition,
                     physical_truncated, time_limit_reached, pre_reset_critic_physical_snapshot):
        from .assignment_event_profile_runtime_domain import _StagedPreResetPhysicalReport
        _require(self._admitted is not None and self._report is None and not any(self._deliveries),
            "report_sequence", "Build one report per admitted, unacknowledged step")
        if boundary is not None:
            self._require_single()
            _require(boundaries_by_robot is None, "boundary_shape", "Use one boundary interface")
            boundaries_by_robot = {0: boundary}
        _require(isinstance(boundaries_by_robot, Mapping)
            and all(type(k) is int for k in boundaries_by_robot)
            and set(boundaries_by_robot) == set(self.robot_ids),
            "boundary_shape", "Provide exactly one current boundary for every robot")
        _require(all(type(b) is ExecutionBoundaryEvidence for b in boundaries_by_robot.values()),
            "boundary_type", "Typed current boundaries required")
        _require(pre_reset_critic_physical_snapshot is not None, "critic_required", "Integration requires an actual pre-reset physical snapshot")
        pub = self._admitted
        self._require_admission(pub)
        physical = _StagedPreResetPhysicalReport(device=pub.env_id.device,
            coverage_before_transition=coverage_before_transition,
            raw_new_candidate=torch.zeros((1, self.num_robots, self.num_tasks), dtype=torch.bool, device=pub.env_id.device),
            physical_truncated=physical_truncated, time_limit_reached=time_limit_reached,
            pre_reset_critic_physical_snapshot=pre_reset_critic_physical_snapshot)
        report = _StagedPreResetExecutionReport._create(self, physical, boundaries_by_robot)
        self._report = report
        try:
            self._validate_report(report, self.domain_identity, self._port.read_current(), pub.lifecycle_state)
        except BaseException:
            self._report = None
            raise
        return report

    def _validate_report(self, report, domain_identity, publication, snapshot):
        # The retained domain calls here under its operation lock: do not read the fence here.
        _require(report is self._report and self._committed is None and not any(self._deliveries),
            "report_once", "A stale, foreign or committed report cannot produce new facts")
        _require(domain_identity is self.domain_identity and publication is self._admitted
            and publication is report._publication and self._port.read_current() is publication,
            "report_publication", "Report must bind the exact current admitted P2")
        _require(all(a is b for a, b in zip(report._bindings, self._bindings))
            and all(a is b for a, b in zip(report._pendings, self._pendings)),
            "report_binding", "Report binding/pending identities changed")
        _require(snapshot.store_version == publication.store_version
            and torch.equal(snapshot.ownership, publication.lifecycle_state.ownership)
            and torch.equal(snapshot.task_state, publication.lifecycle_state.task_state)
            and torch.equal(snapshot.robot_state, publication.lifecycle_state.robot_state),
            "report_prestate", "Producer prestate must match the admitted authoritative state")
        physical = report._physical_report
        _require(torch.equal(physical._coverage_before_transition,
            publication.lifecycle_state.task_state == int(TaskLifecycleState.COMPLETED)),
            "report_coverage", "Coverage must be projected from authoritative completed tasks")
        boundaries = report.boundaries_by_robot
        steps = {b.physics_step for b in boundaries.values()}
        _require(len(steps) == 1, "boundary_clock", "All robot samples must use the same global physics boundary")
        completion = torch.zeros_like(physical._raw_new_candidate)
        release = torch.zeros_like(completion)
        unavailable = torch.zeros((1, self.num_robots), dtype=torch.bool, device=completion.device)
        for robot in self.robot_ids:
            boundary = boundaries[robot]; binding = self._bindings[robot]
            _require(boundary.physics_step > self._last_boundary_step and boundary.native_valid,
                "boundary_native", "A fresh valid physical boundary is required")
            healthy = boundary.off_confirmed and boundary.holding and boundary.resource_healthy and boundary.continuous_hold
            if bool(physical._time_limit_reached.any()):
                _require(healthy, "unsafe_time_limit", "A terminal deadline cannot hide unsafe cleanup")
            if binding is None:
                self._idle_matches(publication, robot)
                _require(boundary.goal_id is None and boundary.capture_id is None
                    and healthy and boundary.no_pending_data and self._pendings[robot] is None,
                    "idle_boundary", "Unbound hold requires current OFF/hold/health and no request/data")
                continue
            self._active_matches(publication, binding)
            _require(boundary.goal_id == binding.goal_id and boundary.capture_id == binding.capture_id,
                "boundary_binding", "Block-end evidence must belong to this robot's active request")
            p = self._pendings[robot]
            if p is None:
                continue
            _require(boundary.physics_step >= p.physics_step, "boundary_stale", "Block-end evidence predates the terminal sample")
            if p.outcome in ("completed", "cancelled"):
                _require(healthy, "boundary_handoff", "OFF, continued hold and resource health must still hold at block end")
            if p.outcome == "cancelled":
                _require(boundary.no_pending_data and not p.acquired and p.custody is None,
                    "cancel_data_race", "No-data cancellation requires the latest backend no-data check")
                if self.execution_profile == 'shared_m2n1':
                    _require(robot == 0 and binding.task_id == 0 and boundary.hold_basis == 'clear'
                        and boundary.physical_clear and boundary.peer_park_verified
                        and boundary.peer_physics_step == boundary.physics_step
                        and type(boundary.control_segment_id) is str and bool(boundary.control_segment_id)
                        and type(boundary.clear_stable_samples) is int and boundary.clear_stable_samples >= 121
                        and type(boundary.clear_stable_span_s) in (int, float)
                        and 1.0-1e-6 <= boundary.clear_stable_span_s < float('inf')
                        and type(boundary.clear_window_start_step) is int
                        and type(boundary.clear_window_end_step) is int
                        and boundary.clear_window_start_step >= 0
                        and boundary.clear_window_end_step == boundary.physics_step
                        and boundary.clear_window_end_step-boundary.clear_window_start_step >= 120,
                        'shared_clear_release', 'Shared cancellation requires current fixed-clear and peer-park evidence')
                    _require(p.metadata.get('cancellation_source') == 'stable_waiting_data'
                        and p.metadata.get('camera_failure_category') == 'CANCELLED'
                        and p.metadata.get('control_segment_id') == boundary.control_segment_id,
                        'shared_cancel_source', 'Shared R must retain the stable no-data cancellation and retreat identity')
                release[0, robot, binding.task_id] = True
            else:
                if self.execution_profile == 'shared_m2n1':
                    _require(robot == 1 and binding.task_id == 0 and boundary.hold_basis == 'scanner_task',
                        'shared_completion_source', 'Only B completes the one shared scanner task')
                _require(type(p.custody) is RawCaptureCustody and p.acquired,
                    "report_custody", "Acquired data must remain held before producer")
                completion[0, robot, binding.task_id] = True
                if p.outcome == "completed_unavailable":
                    _require(not boundary.resource_healthy or not boundary.off_confirmed,
                        "unavailable_reason", "C+U requires an actual close/resource failure")
                    unavailable[0, robot] = True
        return completion, release, unavailable

    def _register_committed(self, report, outcome):
        # Called by the retained domain only after its actual transaction returned.
        self._committed = (report, outcome)

    def ack_authority_delivery(self, outcome):
        self._require_single()
        deliveries = self.ack_authority_deliveries(outcome)
        return deliveries[0] if deliveries else None

    def ack_authority_deliveries(self, outcome):
        if self._last_ack is not None and self._last_ack[0] is outcome:
            return self._last_ack[1]
        _require(self._committed is not None and self._committed[1] is outcome,
            "receipt_source", "Only this report's real completed domain transaction can be acknowledged")
        report = self._committed[0]; result = outcome.result; pub = self._port.read_current()
        _require(pub.result is result and pub.lifecycle_view is outcome.published_view,
            "receipt_publication", "Acknowledge before reset or any subsequent publication")
        row = self._row(pub); old = report._publication
        _require(int(result.episode_generation[row]) == int(old.episode_generation[self._row(old)])
            and int(result.transition_generation[row]) == int(old.transition_generation[self._row(old)]) + 1,
            "receipt_generation", "Receipt must belong to this current transition")
        deliveries = []
        # No local slot/history mutation until every pending effect has been checked.
        for robot, pending in enumerate(report._pendings):
            _require(self._pendings[robot] is pending and self._bindings[robot] is report._bindings[robot],
                "receipt_binding", "Committed bindings and retained data must remain intact")
            if pending is None:
                continue
            task = pending.binding.task_id
            _require(int(result.updated_ownership[row, task]) == -1,
                "receipt_owner", "Delivery requires authority release of the old owner")
            _require(bool(result.completed_tasks[row, task]) == (pending.outcome != "cancelled")
                and bool(result.released_tasks[row, task]) == (pending.outcome == "cancelled"),
                "receipt_outcome", "Authority outcome differs from the pending result")
            deliveries.append(ExecutionDeliveryReceipt(pending.binding, pending, result,
                int(result.facts_consume_token[row]), int(result.authority_receipt_id[row]),
                int(result.transition_generation[row])))
        deliveries = tuple(deliveries)
        for receipt in deliveries:
            self._deliveries[receipt.binding.robot_id] = receipt
        self._history.extend(deliveries)
        self._last_boundary_step = report.boundaries_by_robot[0].physics_step
        self._observed = pub; self._admitted = self._report = self._committed = None
        self._last_ack = (outcome, deliveries); self.transition_count += 1
        return deliveries

    def retire_request(self, binding, receipt):
        _require(type(binding) is ExecutionBinding and binding.robot_id in self.robot_ids
            and binding is self._bindings[binding.robot_id] and receipt is not None
            and receipt is self._deliveries[binding.robot_id] and receipt.pending is self._pendings[binding.robot_id],
            "retire_before_receipt", "Retire only the exact acknowledged request")
        robot = binding.robot_id
        self._bindings[robot] = self._pendings[robot] = self._deliveries[robot] = None


LifecycleExecutionAdapter = Cr12ExecutionAdapter
