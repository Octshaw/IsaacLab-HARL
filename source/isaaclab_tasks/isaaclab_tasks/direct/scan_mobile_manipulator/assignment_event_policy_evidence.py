"""Immutable current-policy evidence capture and v2 numerical projectors.

This B2-I1 module is read-only.  It consumes one current P2 publication, one
already-read OPEN fence view, and one physical/problem capture.  It owns no
lifecycle state, window, environment, action mask, proposal, or learner path.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_POLICY_EVIDENCE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_policy_evidence"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_POLICY_EVIDENCE_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event policy evidence source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_POLICY_EVIDENCE_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from types import MappingProxyType

import torch
import torch.nn.functional as torch_functional

from .assignment_event_profile_schema_contract_v2 import (
    ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION,
    EVENT_POLICY_ACTOR_SCHEMA_V2,
    EVENT_POLICY_CRITIC_SCHEMA_V2,
    EVENT_POLICY_SCALE_V2_CONTRACT_VERSION,
    EventPolicyEvidenceIdentityV2,
    build_assignment_event_profile_schema_v2_descriptor,
    capture_event_policy_evidence_identity_v2,
)
from .assignment_initial_claim_runtime import _EventRuntimeCurrentPublication
from .assignment_interstep_claim_window_runtime import (
    _ClaimWindowFencePhase,
    _ClaimWindowFenceView,
    _ClaimWindowIdentity,
)
from .assignment_lifecycle_transaction_runtime import LifecycleStateSnapshot
from .assignment_lifecycle_transition_contract import (
    RobotLifecycleState,
    TaskLifecycleState,
    TerminationReason,
)
from .assignment_profile_contract import AssignmentProfileName


EVENT_POLICY_PHYSICAL_EVIDENCE_V2 = "event_policy_physical_problem_evidence_v2"
EVENT_POLICY_EVIDENCE_SNAPSHOT_V2 = "event_policy_evidence_snapshot_v2"
EVENT_POLICY_PROJECTOR_V2 = "event_policy_current_projector_v2"
CURRENT_POLICY_CRITIC_PROJECTION_V2 = "current_policy_critic_projection_v2"

_PHYSICAL_PROBLEM_KEYS = (
    "num_envs",
    "num_agents",
    "agent_names",
    "num_viewpoints",
    "viewpoint_ids",
    "base_pos",
    "base_yaw",
    "scanner_pos",
    "scanner_quat",
    "viewpoint_pos",
    "viewpoint_quat",
    "arm_reach",
    "scanner_min_range",
    "scanner_max_range",
    "scanner_fov_deg",
    "feasible_mask",
    "cost_matrix",
)
_EXCLUDED_LEGACY_STATUS_KEYS = ("robot_status", "task_status")


class EventPolicyEvidenceError(RuntimeError):
    """Fail-closed current evidence capture or projection error."""

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
            f"field_name={field_name!r}; expected={expected!r}; "
            f"actual={actual!r}; schema={EVENT_POLICY_EVIDENCE_SNAPSHOT_V2!r}"
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
    raise EventPolicyEvidenceError(
        message,
        failure_code=failure_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        actual=actual,
    )


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if type(value) in (tuple, list):
        return tuple(_deep_readonly(item) for item in value)
    return value


def _tensor_contract(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    finite: bool = False,
) -> torch.Tensor:
    if (
        type(value) is not torch.Tensor
        or tuple(value.shape) != shape
        or value.dtype is not dtype
        or value.device != device
    ):
        _fail(
            "tensor violates the exact physical evidence contract",
            failure_code="physical_tensor_contract",
            stage="physical_capture",
            field_name=field_name,
            expected=(shape, dtype, device),
            actual=(
                type(value),
                getattr(value, "shape", None),
                getattr(value, "dtype", None),
                getattr(value, "device", None),
            ),
        )
    if finite and not bool(torch.isfinite(value).all().item()):
        _fail(
            "physical numerical evidence must be finite",
            failure_code="nonfinite_physical_evidence",
            stage="physical_capture",
            field_name=field_name,
            expected="all finite",
            actual="contains NaN or infinity",
        )
    return value.detach().clone().contiguous()


def _readonly_tensor(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


def _canonicalize_quaternion(value: torch.Tensor, *, field_name: str) -> torch.Tensor:
    norms = torch.linalg.vector_norm(value, dim=-1, keepdim=True)
    if bool((norms <= 1.0e-12).any().item()):
        _fail(
            "quaternion norm is zero",
            failure_code="invalid_quaternion_norm",
            stage="projection",
            field_name=field_name,
            expected="norm > 1e-12",
            actual="zero-norm row",
        )
    unit = value / norms
    w = unit[..., 0]
    xyz = unit[..., 1:]
    first_nonzero_sign = torch.ones_like(w)
    unresolved = w == 0
    for column in range(3):
        coordinate = xyz[..., column]
        selected = unresolved & (coordinate != 0)
        first_nonzero_sign = torch.where(
            selected,
            torch.where(coordinate < 0, -torch.ones_like(w), torch.ones_like(w)),
            first_nonzero_sign,
        )
        unresolved = unresolved & (coordinate == 0)
    sign = torch.where(w < 0, -torch.ones_like(w), first_nonzero_sign)
    return (unit * sign.unsqueeze(-1)).contiguous()


@dataclass(frozen=True, slots=True)
class EventPolicyNumericalBlockLayoutV2:
    order: int
    name: str
    start: int
    stop: int
    semantic_shape: tuple[object, ...]

    @property
    def width(self) -> int:
        return self.stop - self.start


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyPhysicalProblemEvidenceV2:
    """Detached current physical/problem capture; no lifecycle truth."""

    schema_version: str
    num_envs: int
    M: int
    N: int
    ordered_agent_names: tuple[str, ...]
    ordered_task_ids: tuple[int, ...]
    _base_pos: torch.Tensor = field(repr=False)
    _base_yaw: torch.Tensor = field(repr=False)
    _scanner_pos: torch.Tensor = field(repr=False)
    _scanner_quat: torch.Tensor = field(repr=False)
    _task_pos: torch.Tensor = field(repr=False)
    _task_quat: torch.Tensor = field(repr=False)
    _arm_reach: torch.Tensor = field(repr=False)
    _scanner_min_range: torch.Tensor = field(repr=False)
    _scanner_max_range: torch.Tensor = field(repr=False)
    _scanner_fov_deg: torch.Tensor = field(repr=False)
    _explicit_physical_feasibility: torch.Tensor = field(repr=False)
    _geometric_pair_ranking_cost: torch.Tensor = field(repr=False)
    _episode_progress_steps: torch.Tensor = field(repr=False)
    _provenance: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "physical evidence requires the canonical capture factory",
            failure_code="physical_factory_required",
            stage="physical_capture",
            expected="capture_event_policy_physical_problem_evidence_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(cls, **values: object) -> "EventPolicyPhysicalProblemEvidenceV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_POLICY_PHYSICAL_EVIDENCE_V2)
        for name in ("num_envs", "M", "N", "ordered_agent_names", "ordered_task_ids"):
            object.__setattr__(instance, name, values[name])
        for name in (
            "base_pos", "base_yaw", "scanner_pos", "scanner_quat", "task_pos",
            "task_quat", "arm_reach", "scanner_min_range", "scanner_max_range",
            "scanner_fov_deg", "explicit_physical_feasibility",
            "geometric_pair_ranking_cost", "episode_progress_steps",
        ):
            object.__setattr__(instance, f"_{name}", _readonly_tensor(values[name]))
        object.__setattr__(instance, "_provenance", _deep_readonly(values["provenance"]))
        return instance

    def _clone(self) -> "EventPolicyPhysicalProblemEvidenceV2":
        return self._create(
            num_envs=self.num_envs,
            M=self.M,
            N=self.N,
            ordered_agent_names=self.ordered_agent_names,
            ordered_task_ids=self.ordered_task_ids,
            base_pos=self._base_pos,
            base_yaw=self._base_yaw,
            scanner_pos=self._scanner_pos,
            scanner_quat=self._scanner_quat,
            task_pos=self._task_pos,
            task_quat=self._task_quat,
            arm_reach=self._arm_reach,
            scanner_min_range=self._scanner_min_range,
            scanner_max_range=self._scanner_max_range,
            scanner_fov_deg=self._scanner_fov_deg,
            explicit_physical_feasibility=self._explicit_physical_feasibility,
            geometric_pair_ranking_cost=self._geometric_pair_ranking_cost,
            episode_progress_steps=self._episode_progress_steps,
            provenance=self._provenance,
        )

    @property
    def device(self) -> torch.device:
        return self._base_pos.device

    @property
    def base_pos(self) -> torch.Tensor:
        return _readonly_tensor(self._base_pos)

    @property
    def base_yaw(self) -> torch.Tensor:
        return _readonly_tensor(self._base_yaw)

    @property
    def scanner_pos(self) -> torch.Tensor:
        return _readonly_tensor(self._scanner_pos)

    @property
    def scanner_quat(self) -> torch.Tensor:
        return _readonly_tensor(self._scanner_quat)

    @property
    def task_pos(self) -> torch.Tensor:
        return _readonly_tensor(self._task_pos)

    @property
    def task_quat(self) -> torch.Tensor:
        return _readonly_tensor(self._task_quat)

    @property
    def arm_reach(self) -> torch.Tensor:
        return _readonly_tensor(self._arm_reach)

    @property
    def scanner_min_range(self) -> torch.Tensor:
        return _readonly_tensor(self._scanner_min_range)

    @property
    def scanner_max_range(self) -> torch.Tensor:
        return _readonly_tensor(self._scanner_max_range)

    @property
    def scanner_fov_deg(self) -> torch.Tensor:
        return _readonly_tensor(self._scanner_fov_deg)

    @property
    def explicit_physical_feasibility(self) -> torch.Tensor:
        return _readonly_tensor(self._explicit_physical_feasibility)

    @property
    def geometric_pair_ranking_cost(self) -> torch.Tensor:
        return _readonly_tensor(self._geometric_pair_ranking_cost)

    @property
    def episode_progress_steps(self) -> torch.Tensor:
        return _readonly_tensor(self._episode_progress_steps)

    @property
    def provenance(self) -> Mapping[str, object]:
        return self._provenance


def capture_event_policy_physical_problem_evidence_v2(
    *,
    assignment_problem: Mapping[str, object],
    episode_progress_steps: torch.Tensor,
    scale_contract: Mapping[str, object],
) -> EventPolicyPhysicalProblemEvidenceV2:
    """Read every required current problem field once, validate, and detach."""

    if not isinstance(assignment_problem, Mapping):
        _fail(
            "assignment problem must be a mapping",
            failure_code="physical_problem_type",
            stage="physical_capture",
            expected="Mapping",
            actual=type(assignment_problem),
        )
    descriptor = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=scale_contract
    )
    scale = descriptor["scale_contract"]
    M = scale["M"]
    N = scale["N"]
    missing = tuple(key for key in _PHYSICAL_PROBLEM_KEYS if key not in assignment_problem)
    if missing:
        _fail(
            "assignment problem is missing required physical fields",
            failure_code="physical_problem_missing_fields",
            stage="physical_capture",
            expected=_PHYSICAL_PROBLEM_KEYS,
            actual=missing,
        )
    captured = {key: assignment_problem[key] for key in _PHYSICAL_PROBLEM_KEYS}
    E = captured["num_envs"]
    if type(E) is not int or E <= 0:
        _fail(
            "num_envs must be an exact positive int",
            failure_code="physical_cardinality",
            stage="physical_capture",
            field_name="num_envs",
            expected="positive int",
            actual=E,
        )
    cardinality = (
        captured["num_agents"],
        captured["num_viewpoints"],
        captured["agent_names"],
        captured["viewpoint_ids"],
    )
    expected_cardinality = (
        M,
        N,
        scale["ordered_agent_names"],
        scale["ordered_task_ids"],
    )
    if cardinality != expected_cardinality:
        _fail(
            "physical problem ordering/cardinality differs from the scale contract",
            failure_code="physical_cardinality",
            stage="physical_capture",
            expected=expected_cardinality,
            actual=cardinality,
        )
    base_pos = captured["base_pos"]
    if type(base_pos) is not torch.Tensor:
        _fail(
            "base_pos must establish the physical evidence device",
            failure_code="physical_tensor_contract",
            stage="physical_capture",
            field_name="base_pos",
            expected="torch.Tensor",
            actual=type(base_pos),
        )
    device = base_pos.device
    values = {
        "base_pos": _tensor_contract(base_pos, field_name="base_pos", shape=(E, M, 3), dtype=torch.float32, device=device, finite=True),
        "base_yaw": _tensor_contract(captured["base_yaw"], field_name="base_yaw", shape=(E, M), dtype=torch.float32, device=device, finite=True),
        "scanner_pos": _tensor_contract(captured["scanner_pos"], field_name="scanner_pos", shape=(E, M, 3), dtype=torch.float32, device=device, finite=True),
        "scanner_quat": _tensor_contract(captured["scanner_quat"], field_name="scanner_quat", shape=(E, M, 4), dtype=torch.float32, device=device, finite=True),
        "task_pos": _tensor_contract(captured["viewpoint_pos"], field_name="viewpoint_pos", shape=(E, N, 3), dtype=torch.float32, device=device, finite=True),
        "task_quat": _tensor_contract(captured["viewpoint_quat"], field_name="viewpoint_quat", shape=(E, N, 4), dtype=torch.float32, device=device, finite=True),
        "arm_reach": _tensor_contract(captured["arm_reach"], field_name="arm_reach", shape=(M,), dtype=torch.float32, device=device, finite=True),
        "scanner_min_range": _tensor_contract(captured["scanner_min_range"], field_name="scanner_min_range", shape=(M,), dtype=torch.float32, device=device, finite=True),
        "scanner_max_range": _tensor_contract(captured["scanner_max_range"], field_name="scanner_max_range", shape=(M,), dtype=torch.float32, device=device, finite=True),
        "scanner_fov_deg": _tensor_contract(captured["scanner_fov_deg"], field_name="scanner_fov_deg", shape=(M,), dtype=torch.float32, device=device, finite=True),
        "explicit_physical_feasibility": _tensor_contract(captured["feasible_mask"], field_name="feasible_mask", shape=(E, M, N), dtype=torch.bool, device=device),
        "geometric_pair_ranking_cost": _tensor_contract(captured["cost_matrix"], field_name="cost_matrix", shape=(E, M, N), dtype=torch.float32, device=device, finite=True),
        "episode_progress_steps": _tensor_contract(episode_progress_steps, field_name="episode_progress_steps", shape=(E,), dtype=torch.int64, device=device),
    }
    if (
        bool((values["arm_reach"] <= 0).any().item())
        or bool((values["scanner_min_range"] < 0).any().item())
        or bool((values["scanner_max_range"] <= values["scanner_min_range"]).any().item())
        or bool(((values["scanner_fov_deg"] <= 0) | (values["scanner_fov_deg"] > 180)).any().item())
        or bool((values["geometric_pair_ranking_cost"] < 0).any().item())
        or bool((values["episode_progress_steps"] < 0).any().item())
    ):
        _fail(
            "physical ranges violate their semantic contract",
            failure_code="physical_value_range",
            stage="physical_capture",
            expected="positive capabilities, nonnegative distance/progress",
            actual="out-of-range value",
        )
    provenance = {
        "schema_version": EVENT_POLICY_PHYSICAL_EVIDENCE_V2,
        "physical_problem_source": "ScanMobileManipulatorEnv.get_assignment_problem current mapping",
        "physical_problem_required_keys": _PHYSICAL_PROBLEM_KEYS,
        "legacy_status_keys_excluded_from_lifecycle_truth": _EXCLUDED_LEGACY_STATUS_KEYS,
        "explicit_feasibility_source": "assignment_problem.feasible_mask",
        "geometric_cost_source": "scanner-to-viewpoint Euclidean ranking distance",
        "geometric_cost_is_feasibility": False,
        "episode_progress_source": "current episode progress steps supplied with same capture",
        "external_producers": descriptor["external_evidence_seams"],
    }
    return EventPolicyPhysicalProblemEvidenceV2._create(
        num_envs=E,
        M=M,
        N=N,
        ordered_agent_names=scale["ordered_agent_names"],
        ordered_task_ids=scale["ordered_task_ids"],
        provenance=provenance,
        **values,
    )


def _validate_lifecycle_tensor(
    value: torch.Tensor,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
) -> torch.Tensor:
    if tuple(value.shape) != shape or value.dtype is not dtype or value.device != device:
        _fail(
            "current P2 tensor violates the projector contract",
            failure_code="p2_tensor_contract",
            stage="current_capture",
            field_name=field_name,
            expected=(shape, dtype, device),
            actual=(tuple(value.shape), value.dtype, value.device),
        )
    return _readonly_tensor(value)


def _layout(
    blocks: Sequence[Mapping[str, object]],
    values: Mapping[str, torch.Tensor],
) -> tuple[EventPolicyNumericalBlockLayoutV2, ...]:
    offset = 0
    result = []
    for order, block in enumerate(blocks, start=1):
        name = block["name"]
        if block["order"] != order or name not in values:
            _fail(
                "projector block mapping differs from the B2-I0 manifest",
                failure_code="projector_manifest_mismatch",
                stage="projection",
                expected=(order, name),
                actual=(block.get("order"), tuple(values)),
            )
        width = (
            int(values[name].shape[-1])
            if name == "actor_robot_identity_one_hot"
            else int(math.prod(values[name].shape[1:]))
        )
        result.append(
            EventPolicyNumericalBlockLayoutV2(
                order=order,
                name=name,
                start=offset,
                stop=offset + width,
                semantic_shape=block["shape"],
            )
        )
        offset += width
    if set(values) != {block["name"] for block in blocks}:
        _fail(
            "projector has extra numerical blocks outside the manifest",
            failure_code="projector_manifest_mismatch",
            stage="projection",
            expected=tuple(block["name"] for block in blocks),
            actual=tuple(values),
        )
    return tuple(result)


def _project_common_blocks(
    *,
    physical: EventPolicyPhysicalProblemEvidenceV2,
    task_state: torch.Tensor,
    robot_state: torch.Tensor,
    ownership: torch.Tensor,
    failed_pairs: torch.Tensor,
    completion_count: torch.Tensor,
    scale: Mapping[str, object],
) -> Mapping[str, torch.Tensor]:
    E, M, N = physical.num_envs, physical.M, physical.N
    spacing = float(scale["scene_env_spacing"])
    horizon = int(scale["episode_horizon_steps"])
    robot_quat = _canonicalize_quaternion(physical.scanner_quat, field_name="scanner_quat")
    task_quat = _canonicalize_quaternion(physical.task_quat, field_name="viewpoint_quat")
    capabilities = torch.stack(
        (
            physical.arm_reach / spacing,
            physical.scanner_min_range / spacing,
            physical.scanner_max_range / spacing,
            torch.cos(0.5 * torch.deg2rad(physical.scanner_fov_deg)),
        ),
        dim=-1,
    ).view(1, M, 4).expand(E, M, 4)
    robot_physical = torch.cat(
        (
            physical.base_pos / spacing,
            torch.sin(physical.base_yaw).unsqueeze(-1),
            torch.cos(physical.base_yaw).unsqueeze(-1),
            physical.scanner_pos / spacing,
            robot_quat,
            capabilities,
        ),
        dim=-1,
    ).contiguous()
    robot_one_hot = torch_functional.one_hot(robot_state, num_classes=4).to(torch.float32)
    robot_available = (robot_state != int(RobotLifecycleState.UNAVAILABLE)).to(torch.float32).unsqueeze(-1)
    robot_lifecycle = torch.cat((robot_one_hot, robot_available), dim=-1)
    task_pose = torch.cat((physical.task_pos / spacing, task_quat), dim=-1)
    task_lifecycle = torch_functional.one_hot(task_state, num_classes=6).to(torch.float32)
    owner_index = torch.where(ownership >= 0, ownership, torch.full_like(ownership, M))
    task_ownership = torch_functional.one_hot(owner_index, num_classes=M + 1).to(torch.float32)
    robot_ids = torch.arange(M, device=ownership.device, dtype=torch.int64).view(1, M, 1)
    owner_match = ownership.unsqueeze(1) == robot_ids
    owned_count = owner_match.sum(dim=2)
    if bool((owned_count > 1).any().item()):
        _fail(
            "current P2 assigns multiple active tasks to one robot",
            failure_code="multiple_owned_tasks",
            stage="projection",
            field_name="ownership",
            expected="zero or one task per robot",
            actual=int(owned_count.max().item()),
        )
    first_owned = owner_match.to(torch.int64).argmax(dim=2)
    owned_task_index = torch.where(
        owned_count == 1,
        first_owned,
        torch.full_like(first_owned, N),
    )
    current_owned = torch_functional.one_hot(owned_task_index, num_classes=N + 1).to(torch.float32)
    progress = (
        physical.episode_progress_steps.to(torch.float32) / float(horizon)
    ).clamp(0.0, 1.0).unsqueeze(-1)
    values = {
        "global_robot_physical_state": robot_physical,
        "global_robot_lifecycle_state": robot_lifecycle,
        "task_pose": task_pose,
        "task_lifecycle_state": task_lifecycle,
        "task_ownership": task_ownership,
        "current_robot_owned_task": current_owned,
        "failed_pair_state": failed_pairs.to(torch.float32),
        "explicit_physical_feasibility": physical.explicit_physical_feasibility.to(torch.float32),
        "geometric_pair_ranking_cost": physical.geometric_pair_ranking_cost / spacing,
        "robot_workload": completion_count.to(torch.float32).unsqueeze(-1) / float(N),
        "episode_physical_progress_fraction": progress,
    }
    if any(value.dtype is not torch.float32 or not value.is_contiguous() for value in values.values()):
        values = {name: value.to(torch.float32).contiguous() for name, value in values.items()}
    return MappingProxyType(values)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyEvidenceSnapshot:
    """One sealed current P2/OPEN/physical evidence and projection boundary."""

    schema_version: str
    profile_name: str
    identity: EventPolicyEvidenceIdentityV2
    projector_version: str
    critic_projection_mode: str
    _source_publication: _EventRuntimeCurrentPublication = field(repr=False)
    _source_window_identity: _ClaimWindowIdentity = field(repr=False)
    _physical_evidence: EventPolicyPhysicalProblemEvidenceV2 = field(repr=False)
    _task_state: torch.Tensor = field(repr=False)
    _robot_state: torch.Tensor = field(repr=False)
    _ownership: torch.Tensor = field(repr=False)
    _current_owned_task_id: torch.Tensor = field(repr=False)
    _cumulative_failed_pairs: torch.Tensor = field(repr=False)
    _completion_count: torch.Tensor = field(repr=False)
    _actor_obs: torch.Tensor = field(repr=False)
    _semantic_share_obs: torch.Tensor = field(repr=False)
    _runner_share_obs: torch.Tensor = field(repr=False)
    _actor_block_layout: tuple[EventPolicyNumericalBlockLayoutV2, ...]
    _critic_block_layout: tuple[EventPolicyNumericalBlockLayoutV2, ...]
    _scale_contract: Mapping[str, object] = field(repr=False)
    _provenance: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "policy evidence snapshot requires the canonical capture factory",
            failure_code="snapshot_factory_required",
            stage="current_capture",
            expected="capture_current_event_policy_evidence_snapshot_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(cls, **values: object) -> "EventPolicyEvidenceSnapshot":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_POLICY_EVIDENCE_SNAPSHOT_V2)
        object.__setattr__(instance, "profile_name", AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value)
        object.__setattr__(instance, "projector_version", EVENT_POLICY_PROJECTOR_V2)
        object.__setattr__(instance, "critic_projection_mode", CURRENT_POLICY_CRITIC_PROJECTION_V2)
        for name in ("identity", "source_publication", "source_window_identity"):
            object.__setattr__(instance, name if name == "identity" else f"_{name}", values[name])
        object.__setattr__(instance, "_physical_evidence", values["physical_evidence"]._clone())
        for name in (
            "task_state", "robot_state", "ownership", "current_owned_task_id",
            "cumulative_failed_pairs", "completion_count", "actor_obs",
            "semantic_share_obs", "runner_share_obs",
        ):
            object.__setattr__(instance, f"_{name}", _readonly_tensor(values[name]))
        object.__setattr__(instance, "_actor_block_layout", values["actor_block_layout"])
        object.__setattr__(instance, "_critic_block_layout", values["critic_block_layout"])
        object.__setattr__(instance, "_scale_contract", _deep_readonly(values["scale_contract"]))
        object.__setattr__(instance, "_provenance", _deep_readonly(values["provenance"]))
        return instance

    @property
    def source_publication(self) -> _EventRuntimeCurrentPublication:
        return self._source_publication

    @property
    def source_window_identity(self) -> _ClaimWindowIdentity:
        return self._source_window_identity

    @property
    def physical_evidence(self) -> EventPolicyPhysicalProblemEvidenceV2:
        return self._physical_evidence

    @property
    def task_state(self) -> torch.Tensor:
        return _readonly_tensor(self._task_state)

    @property
    def robot_state(self) -> torch.Tensor:
        return _readonly_tensor(self._robot_state)

    @property
    def ownership(self) -> torch.Tensor:
        return _readonly_tensor(self._ownership)

    @property
    def current_owned_task_id(self) -> torch.Tensor:
        return _readonly_tensor(self._current_owned_task_id)

    @property
    def cumulative_failed_pairs(self) -> torch.Tensor:
        return _readonly_tensor(self._cumulative_failed_pairs)

    @property
    def completion_count(self) -> torch.Tensor:
        return _readonly_tensor(self._completion_count)

    @property
    def actor_obs(self) -> torch.Tensor:
        return _readonly_tensor(self._actor_obs)

    @property
    def semantic_share_obs(self) -> torch.Tensor:
        return _readonly_tensor(self._semantic_share_obs)

    @property
    def runner_share_obs(self) -> torch.Tensor:
        return _readonly_tensor(self._runner_share_obs)

    @property
    def actor_block_layout(self) -> tuple[EventPolicyNumericalBlockLayoutV2, ...]:
        return self._actor_block_layout

    @property
    def critic_block_layout(self) -> tuple[EventPolicyNumericalBlockLayoutV2, ...]:
        return self._critic_block_layout

    @property
    def scale_contract(self) -> Mapping[str, object]:
        return self._scale_contract

    @property
    def provenance(self) -> Mapping[str, object]:
        return self._provenance

    def validate_current(
        self,
        *,
        current_publication: _EventRuntimeCurrentPublication,
        current_open_window_view: _ClaimWindowFenceView,
    ) -> None:
        if type(current_publication) is not _EventRuntimeCurrentPublication:
            _fail(
                "stale validation requires the exact P2 publication type",
                failure_code="current_publication_type",
                stage="stale_validation",
                expected=_EventRuntimeCurrentPublication,
                actual=type(current_publication),
            )
        window = _require_open_window(current_open_window_view, stage="stale_validation")
        if current_publication is not self._source_publication:
            _fail(
                "snapshot belongs to a different current P2 publication object",
                failure_code="source_publication_mismatch",
                stage="stale_validation",
                expected="same publication object",
                actual="different publication object",
            )
        self.identity.validate_current(
            p2_publication_identity=current_publication.publication_identity,
            episode_generations=_generation_tuple(current_publication.episode_generation, field_name="episode_generation"),
            transition_generations=_generation_tuple(current_publication.transition_generation, field_name="transition_generation"),
            open_window_identity=window,
            M=self.identity.M,
            N=self.identity.N,
        )


def _generation_tuple(value: torch.Tensor, *, field_name: str) -> tuple[int, ...]:
    if type(value) is not torch.Tensor or value.dtype is not torch.int64 or value.ndim != 1:
        _fail(
            "P2 generation has an invalid tensor contract",
            failure_code="generation_contract",
            stage="current_capture",
            field_name=field_name,
            expected="int64[E]",
            actual=(type(value), getattr(value, "dtype", None), getattr(value, "shape", None)),
        )
    return tuple(int(item) for item in value.detach().cpu().tolist())


def _require_open_window(view: object, *, stage: str) -> _ClaimWindowIdentity:
    window = view.window if type(view) is _ClaimWindowFenceView else None
    if (
        type(view) is not _ClaimWindowFenceView
        or view.phase is not _ClaimWindowFencePhase.OPEN
        or type(window) is not _ClaimWindowIdentity
        or view.active_step is not None
        or view.active_reset is not None
    ):
        _fail(
            "current evidence requires one exact idle OPEN window view",
            failure_code="open_window_contract",
            stage=stage,
            expected="OPEN view with exact opaque window and no active admission",
            actual=(
                type(view),
                getattr(view, "phase", None),
                type(getattr(view, "window", None)),
                getattr(view, "active_step", None),
                getattr(view, "active_reset", None),
            ),
        )
    return window


def capture_current_event_policy_evidence_snapshot_v2(
    *,
    current_publication: _EventRuntimeCurrentPublication,
    current_open_window_view: _ClaimWindowFenceView,
    physical_evidence: EventPolicyPhysicalProblemEvidenceV2,
    scale_contract: Mapping[str, object],
) -> EventPolicyEvidenceSnapshot:
    """Seal actor and current-critic projections from one exact input bundle."""

    if type(current_publication) is not _EventRuntimeCurrentPublication:
        _fail(
            "current evidence requires the exact P2 publication type",
            failure_code="current_publication_type",
            stage="current_capture",
            expected=_EventRuntimeCurrentPublication,
            actual=type(current_publication),
        )
    if type(physical_evidence) is not EventPolicyPhysicalProblemEvidenceV2:
        _fail(
            "current evidence requires a canonical detached physical capture",
            failure_code="physical_evidence_type",
            stage="current_capture",
            expected=EventPolicyPhysicalProblemEvidenceV2,
            actual=type(physical_evidence),
        )
    window = _require_open_window(current_open_window_view, stage="current_capture")
    publication_identity = current_publication.publication_identity
    if publication_identity._domain_identity is not window._domain_identity:
        _fail(
            "current P2 and OPEN window belong to different runtime domains",
            failure_code="runtime_domain_mismatch",
            stage="current_capture",
            expected="same opaque domain identity",
            actual="different domain identities",
        )
    descriptor = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale_contract)
    scale = descriptor["scale_contract"]
    M, N, E = scale["M"], scale["N"], physical_evidence.num_envs
    if (physical_evidence.M, physical_evidence.N) != (M, N):
        _fail(
            "physical evidence and v2 schema use different fixed cardinality",
            failure_code="fixed_cardinality_mismatch",
            stage="current_capture",
            expected=(M, N),
            actual=(physical_evidence.M, physical_evidence.N),
        )
    lifecycle_state = current_publication.lifecycle_state
    if type(lifecycle_state) is not LifecycleStateSnapshot:
        _fail(
            "P2 publication does not contain the canonical lifecycle snapshot",
            failure_code="lifecycle_snapshot_type",
            stage="current_capture",
            expected=LifecycleStateSnapshot,
            actual=type(lifecycle_state),
        )
    device = physical_evidence.device
    if lifecycle_state.device != device or lifecycle_state.num_envs != E:
        _fail(
            "P2 and physical evidence have different device/environment domains",
            failure_code="evidence_domain_mismatch",
            stage="current_capture",
            expected=(device, E),
            actual=(lifecycle_state.device, lifecycle_state.num_envs),
        )
    env_id = _validate_lifecycle_tensor(lifecycle_state.env_id, field_name="env_id", shape=(E,), dtype=torch.int64, device=device)
    if not torch.equal(env_id, torch.arange(E, dtype=torch.int64, device=device)):
        _fail(
            "P2 env rows are not in canonical physical row order",
            failure_code="environment_order_mismatch",
            stage="current_capture",
            field_name="env_id",
            expected=tuple(range(E)),
            actual=tuple(int(item) for item in env_id.cpu().tolist()),
        )
    task_state = _validate_lifecycle_tensor(lifecycle_state.task_state, field_name="task_state", shape=(E, N), dtype=torch.int64, device=device)
    robot_state = _validate_lifecycle_tensor(lifecycle_state.robot_state, field_name="robot_state", shape=(E, M), dtype=torch.int64, device=device)
    ownership = _validate_lifecycle_tensor(lifecycle_state.ownership, field_name="ownership", shape=(E, N), dtype=torch.int64, device=device)
    failed_pairs = _validate_lifecycle_tensor(lifecycle_state.cumulative_failed_pairs, field_name="cumulative_failed_pairs", shape=(E, M, N), dtype=torch.bool, device=device)
    completion_count = _validate_lifecycle_tensor(lifecycle_state.completion_count, field_name="completion_count", shape=(E, M), dtype=torch.int64, device=device)
    termination_reason = _validate_lifecycle_tensor(lifecycle_state.termination_reason, field_name="termination_reason", shape=(E,), dtype=torch.int64, device=device)
    invalid_state = (
        bool(((task_state < 0) | (task_state >= len(TaskLifecycleState))).any().item())
        or bool(((robot_state < 0) | (robot_state >= len(RobotLifecycleState))).any().item())
        or bool(((ownership < -1) | (ownership >= M)).any().item())
        or bool(((completion_count < 0) | (completion_count > N)).any().item())
    )
    if invalid_state:
        _fail(
            "current P2 values are outside projector semantic domains",
            failure_code="p2_value_range",
            stage="current_capture",
            expected="canonical enum/owner/completion ranges",
            actual="out-of-range value",
        )
    terminated = current_publication.terminated
    truncated = current_publication.truncated
    if (
        bool(terminated.any().item())
        or bool(truncated.any().item())
        or bool((termination_reason != int(TerminationReason.NONE)).any().item())
    ):
        _fail(
            "B2-I1 accepts only current nonterminal policy evidence",
            failure_code="terminal_evidence_unsupported",
            stage="current_capture",
            expected="terminated=false, truncated=false, reason=NONE",
            actual=(terminated, truncated, termination_reason),
        )
    episode_generations = _generation_tuple(current_publication.episode_generation, field_name="episode_generation")
    transition_generations = _generation_tuple(current_publication.transition_generation, field_name="transition_generation")
    identity = capture_event_policy_evidence_identity_v2(
        p2_publication_identity=publication_identity,
        episode_generations=episode_generations,
        transition_generations=transition_generations,
        open_window_identity=window,
        M=M,
        N=N,
    )
    common = _project_common_blocks(
        physical=physical_evidence,
        task_state=task_state,
        robot_state=robot_state,
        ownership=ownership,
        failed_pairs=failed_pairs,
        completion_count=completion_count,
        scale=scale,
    )
    actor_identity = torch.eye(M, dtype=torch.float32, device=device).view(1, M, M).expand(E, M, M).contiguous()
    actor_values = {"actor_robot_identity_one_hot": actor_identity, **dict(common)}
    actor_blocks = descriptor["actor_schema"]["blocks"]
    critic_blocks = descriptor["critic_schema"]["blocks"]
    actor_layout = _layout(actor_blocks, actor_values)
    critic_layout = _layout(critic_blocks, common)
    actor_parts = []
    for block in actor_blocks:
        value = actor_values[block["name"]]
        if block["name"] == "actor_robot_identity_one_hot":
            actor_parts.append(value)
        else:
            actor_parts.append(value.reshape(E, -1).unsqueeze(1).expand(E, M, -1))
    actor_obs = torch.cat(actor_parts, dim=-1).to(torch.float32).contiguous()
    semantic_share_obs = torch.cat(
        [common[block["name"]].reshape(E, -1) for block in critic_blocks],
        dim=-1,
    ).to(torch.float32).contiguous()
    runner_share_obs = semantic_share_obs.unsqueeze(1).expand(E, M, -1).clone().contiguous()
    expected_actor = descriptor["actor_schema"]["dimension"]
    expected_critic = descriptor["critic_schema"]["dimension"]
    if tuple(actor_obs.shape) != (E, M, expected_actor) or tuple(semantic_share_obs.shape) != (E, expected_critic) or tuple(runner_share_obs.shape) != (E, M, expected_critic):
        _fail(
            "projected tensors differ from manifest-derived dimensions",
            failure_code="projection_shape_mismatch",
            stage="projection",
            expected=((E, M, expected_actor), (E, expected_critic), (E, M, expected_critic)),
            actual=(tuple(actor_obs.shape), tuple(semantic_share_obs.shape), tuple(runner_share_obs.shape)),
        )
    current_owned_task_id = common["current_robot_owned_task"].argmax(dim=-1).to(torch.int64)
    provenance = {
        "snapshot_schema_version": EVENT_POLICY_EVIDENCE_SNAPSHOT_V2,
        "schema_contract_version": ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION,
        "scale_contract_version": EVENT_POLICY_SCALE_V2_CONTRACT_VERSION,
        "actor_schema_version": EVENT_POLICY_ACTOR_SCHEMA_V2,
        "critic_schema_version": EVENT_POLICY_CRITIC_SCHEMA_V2,
        "critic_projection_mode": CURRENT_POLICY_CRITIC_PROJECTION_V2,
        "lifecycle_source": "exact current P2 LifecycleStateSnapshot",
        "physical_source": physical_evidence.provenance,
        "capture_rule": "one supplied P2 publication + one supplied OPEN view + one detached physical capture",
        "actor_and_critic_share_exact_capture": True,
        "identity_metadata_is_model_input": False,
        "terminal_or_historical_supported": False,
        "action_mask_or_row_semantics_present": False,
        "normalization_contract": {
            "position_and_capability_lengths": "divide by scale_contract.scene_env_spacing",
            "base_yaw": "sin then cos",
            "quaternion": "unit wxyz with deterministic nonnegative leading sign",
            "geometric_ranking_cost": "divide by scale_contract.scene_env_spacing",
            "robot_workload": "P2 completion count divide by fixed N",
            "episode_progress": "current progress steps divide by horizon then clamp [0,1]",
            "data_dependent_statistics": False,
        },
    }
    return EventPolicyEvidenceSnapshot._create(
        identity=identity,
        source_publication=current_publication,
        source_window_identity=window,
        physical_evidence=physical_evidence,
        task_state=task_state,
        robot_state=robot_state,
        ownership=ownership,
        current_owned_task_id=current_owned_task_id,
        cumulative_failed_pairs=failed_pairs,
        completion_count=completion_count,
        actor_obs=actor_obs,
        semantic_share_obs=semantic_share_obs,
        runner_share_obs=runner_share_obs,
        actor_block_layout=actor_layout,
        critic_block_layout=critic_layout,
        scale_contract=scale,
        provenance=provenance,
    )


def get_event_policy_current_projector_descriptor_v2(
    *, scale_contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Describe the implemented I1 projector without mutating frozen I0."""

    schema = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=scale_contract
    )
    return _deep_readonly(
        {
            "snapshot_schema_version": EVENT_POLICY_EVIDENCE_SNAPSHOT_V2,
            "projector_version": EVENT_POLICY_PROJECTOR_V2,
            "schema_contract_version": schema["contract_version"],
            "profile_name": schema["profile_binding"]["profile_name"],
            "scale_contract": schema["scale_contract"],
            "actor_projection": {
                "schema_version": schema["actor_schema"]["schema_version"],
                "dimension": schema["actor_schema"]["dimension"],
                "implemented": True,
            },
            "critic_projection": {
                "schema_version": schema["critic_schema"]["schema_version"],
                "mode": CURRENT_POLICY_CRITIC_PROJECTION_V2,
                "dimension": schema["critic_schema"]["dimension"],
                "implemented": True,
            },
            "single_capture_required": True,
            "identity_metadata_numerical_encoding": False,
            "terminal_or_historical_projection": False,
            "lifecycle_legality_or_routing": False,
            "public_runtime_integration": False,
            "readiness_change_authorized": False,
        }
    )


__all__ = (
    "CANONICAL_ASSIGNMENT_EVENT_POLICY_EVIDENCE_MODULE",
    "CURRENT_POLICY_CRITIC_PROJECTION_V2",
    "EVENT_POLICY_EVIDENCE_SNAPSHOT_V2",
    "EVENT_POLICY_PHYSICAL_EVIDENCE_V2",
    "EVENT_POLICY_PROJECTOR_V2",
    "EventPolicyEvidenceError",
    "EventPolicyEvidenceSnapshot",
    "EventPolicyNumericalBlockLayoutV2",
    "EventPolicyPhysicalProblemEvidenceV2",
    "capture_current_event_policy_evidence_snapshot_v2",
    "capture_event_policy_physical_problem_evidence_v2",
    "get_event_policy_current_projector_descriptor_v2",
)
