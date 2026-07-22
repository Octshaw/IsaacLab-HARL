"""Pure controlled initial-condition contracts for assignment playback.

This module deliberately has no Isaac Lab, HARL, or torch dependency. Runtime
configuration is resolved elsewhere and copied into immutable values here for
strict validation, fingerprinting, and playback provenance.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence
from uuid import uuid4

try:
    from .capability_config import load_capability_profiles
    from .component_mesh import compute_base_center_alignment_translation, compute_component_mesh_bounds
    from .robot_config import load_robot_config
    from .viewpoint_csv import VIEWPOINT_CSV_CONVENTIONS, VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv
except ImportError:  # Direct project-local import used by lightweight scripts.
    from capability_config import load_capability_profiles
    from component_mesh import compute_base_center_alignment_translation, compute_component_mesh_bounds
    from robot_config import load_robot_config
    from viewpoint_csv import VIEWPOINT_CSV_CONVENTIONS, VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv


CONDITION_CONTRACT_SCHEMA = "assignment_initial_condition_contract_v1"
CONDITION_MANIFEST_SCHEMA = "assignment_initial_condition_manifest_v1"
RESET_POSE_CONVERSION_CONTRACT = "robot_config_wxyz_to_xyzyaw_v1"
INITIAL_CONDITION_MANIFEST_FILENAME = "assignment_initial_condition_manifest.json"
INITIAL_CONDITION_CLI_FIELD = "--assignment_initial_condition_profile"

EXPECTED_TASK_ID = "Isaac-Scan-Mobile-Manipulator-Direct-v0"
EXPECTED_SCENARIO_NAME = "algorithm_proxy_component_mesh"
EXPECTED_SCENARIO_TYPE = "algorithm_visual_debug"
EXPECTED_ORDERED_ROBOT_IDS = ("robot_0", "robot_1", "robot_2")
EXPECTED_SLOT_IDS = ("S0", "S1", "S2")
EXPECTED_NUM_ROBOTS = 3
EXPECTED_NUM_TASKS = 50

EXPECTED_REPOSITORY_FILES = MappingProxyType(
    {
        "scenario": (
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
            "configs/scenarios/algorithm_proxy_component_mesh.yaml",
            "3256398cda4de7caee3b1e1d6de74018623a5d36888a86eeabe0a94392affdfd",
        ),
        "robot_config": (
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
            "configs/robots/robots_real_proxy.yaml",
            "31f6be04615bdab58f06dd51fdc7185a608231b1f0c784aeff37647e4c9f5837",
        ),
        "capability_config": (
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
            "configs/capabilities/mobile_scanner_profiles.yaml",
            "a340f18094c117066e4f5a9e2ee0d5656bc98d54a91c4071d93808abe6e6bf29",
        ),
        "viewpoint_csv": (
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
            "configs/viewpoints/component_mesh_jittered_n50.csv",
            "f18ee898395e872037e93ff80659e6d480dc89b92460aee8da42bcbb7e2351eb",
        ),
        "component_obj": (
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
            "Model/aircraft_skin_with_frame.obj",
            "9e779f2cfddbb2e9a60691217d2abb7bb780ecb2f5661c666397c55bf6119dc7",
        ),
    }
)


class AssignmentInitialConditionError(RuntimeError):
    """Base error for the controlled initial-condition boundary."""


class InitialConditionProfileError(AssignmentInitialConditionError):
    """A profile id or ordered mapping violates the frozen registry."""


class InitialConditionContractError(AssignmentInitialConditionError):
    """Resolved task configuration differs from the frozen v1 contract."""


class InitialConditionUsageError(AssignmentInitialConditionError):
    """A controlled profile is requested from an unsupported entry boundary."""


class InitialConditionManifestError(AssignmentInitialConditionError):
    """Condition-manifest construction or atomic publication failed."""


def _finite_float_tuple(value: Sequence[float], *, length: int, field: str) -> tuple[float, ...]:
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise InitialConditionContractError(f"{field} must contain {length} finite numbers") from exc
    if len(result) != length:
        raise InitialConditionContractError(f"{field} shape must be [{length}], got [{len(result)}]")
    if not all(math.isfinite(item) for item in result):
        raise InitialConditionContractError(f"{field} contains NaN or Inf: {result!r}")
    return result


def quaternion_wxyz_to_yaw(quaternion: Sequence[float], *, field: str = "quaternion_wxyz") -> float:
    """Normalize a scalar-first quaternion and return the existing reset yaw."""

    qw, qx, qy, qz = _finite_float_tuple(quaternion, length=4, field=field)
    norm = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    if norm <= 1.0e-8:
        raise InitialConditionContractError(f"{field} quaternion must be non-zero")
    qw, qx, qy, qz = (qw / norm, qx / norm, qy / norm, qz / norm)
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


def source_pose_wxyz_to_reset_xyzyaw(
    source_pose: Sequence[float], *, field: str = "source_pose_world_wxyz"
) -> tuple[float, float, float, float]:
    pose = _finite_float_tuple(source_pose, length=7, field=field)
    yaw = quaternion_wxyz_to_yaw(pose[3:7], field=f"{field}[3:7]")
    return (pose[0], pose[1], pose[2], yaw)


@dataclass(frozen=True)
class InitialConditionProfile:
    profile_id: str
    description: str
    ordered_robot_ids: tuple[str, ...]
    ordered_slot_ids: tuple[str, ...]
    robot_to_slot_mapping: tuple[tuple[str, str], ...]


INITIAL_CONDITION_PROFILE_REGISTRY = (
    InitialConditionProfile(
        profile_id="baseline_identity",
        description="Existing robot-to-start-pose identity mapping.",
        ordered_robot_ids=EXPECTED_ORDERED_ROBOT_IDS,
        ordered_slot_ids=EXPECTED_SLOT_IDS,
        robot_to_slot_mapping=(("robot_0", "S0"), ("robot_1", "S1"), ("robot_2", "S2")),
    ),
    InitialConditionProfile(
        profile_id="pose_cycle_forward",
        description="Cycle complete start-pose slots forward across fixed robot identities.",
        ordered_robot_ids=EXPECTED_ORDERED_ROBOT_IDS,
        ordered_slot_ids=EXPECTED_SLOT_IDS,
        robot_to_slot_mapping=(("robot_0", "S1"), ("robot_1", "S2"), ("robot_2", "S0")),
    ),
    InitialConditionProfile(
        profile_id="pose_cycle_reverse",
        description="Cycle complete start-pose slots in reverse across fixed robot identities.",
        ordered_robot_ids=EXPECTED_ORDERED_ROBOT_IDS,
        ordered_slot_ids=EXPECTED_SLOT_IDS,
        robot_to_slot_mapping=(("robot_0", "S2"), ("robot_1", "S0"), ("robot_2", "S1")),
    ),
)
INITIAL_CONDITION_PROFILE_CHOICES = tuple(profile.profile_id for profile in INITIAL_CONDITION_PROFILE_REGISTRY)
_PROFILE_BY_ID = MappingProxyType({profile.profile_id: profile for profile in INITIAL_CONDITION_PROFILE_REGISTRY})


def validate_initial_condition_profile(profile: InitialConditionProfile) -> None:
    if not isinstance(profile.profile_id, str) or not profile.profile_id:
        raise InitialConditionProfileError("profile_id must be a non-empty string")
    if profile.ordered_robot_ids != EXPECTED_ORDERED_ROBOT_IDS:
        raise InitialConditionProfileError(
            f"profile {profile.profile_id!r} ordered robots must be {list(EXPECTED_ORDERED_ROBOT_IDS)!r}, "
            f"got {list(profile.ordered_robot_ids)!r}"
        )
    if profile.ordered_slot_ids != EXPECTED_SLOT_IDS:
        raise InitialConditionProfileError(
            f"profile {profile.profile_id!r} ordered slots must be {list(EXPECTED_SLOT_IDS)!r}, "
            f"got {list(profile.ordered_slot_ids)!r}"
        )
    mapping_robots = tuple(robot for robot, _ in profile.robot_to_slot_mapping)
    mapping_slots = tuple(slot for _, slot in profile.robot_to_slot_mapping)
    if mapping_robots != EXPECTED_ORDERED_ROBOT_IDS:
        missing = [robot for robot in EXPECTED_ORDERED_ROBOT_IDS if robot not in mapping_robots]
        extra = [robot for robot in mapping_robots if robot not in EXPECTED_ORDERED_ROBOT_IDS]
        raise InitialConditionProfileError(
            f"profile {profile.profile_id!r} mapping robot order mismatch; missing={missing}, extra={extra}, "
            f"actual={list(mapping_robots)!r}"
        )
    unknown_slots = [slot for slot in mapping_slots if slot not in EXPECTED_SLOT_IDS]
    if unknown_slots:
        raise InitialConditionProfileError(
            f"profile {profile.profile_id!r} mapping contains unknown slot(s): {unknown_slots!r}"
        )
    duplicate_slots = [slot for slot, count in Counter(mapping_slots).items() if count > 1]
    if duplicate_slots or Counter(mapping_slots) != Counter(EXPECTED_SLOT_IDS):
        raise InitialConditionProfileError(
            f"profile {profile.profile_id!r} mapping must be bijective; duplicate_slots={duplicate_slots!r}, "
            f"actual={list(mapping_slots)!r}"
        )


for _profile in INITIAL_CONDITION_PROFILE_REGISTRY:
    validate_initial_condition_profile(_profile)


@dataclass(frozen=True)
class ResolvedFileReference:
    absolute_path: str
    sha256: str


@dataclass(frozen=True)
class PolicyInterfaceContract:
    assignment_lifecycle_profile: str
    resolver_contract_version: str
    actor_schema_version: str
    shared_schema_version: str
    mask_contract_version: str
    budget_release_contract: str
    legacy_guardrail_profile: str
    algorithm: str
    harl_state_type: str
    policy_sequence_mode: str
    use_recurrent_policy: bool
    use_naive_recurrent_policy: bool
    share_param: bool
    deterministic_actor_mode: bool
    cuda_deterministic: bool
    actor_observation_dimension: int
    shared_observation_dimension: int
    action_dimension: int
    noop_raw_id: int
    noop_decoded_value: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "assignment_lifecycle_profile": self.assignment_lifecycle_profile,
            "resolver_contract_version": self.resolver_contract_version,
            "actor_schema_version": self.actor_schema_version,
            "shared_schema_version": self.shared_schema_version,
            "mask_contract_version": self.mask_contract_version,
            "budget_release_contract": self.budget_release_contract,
            "legacy_guardrail_profile": self.legacy_guardrail_profile,
            "algorithm": self.algorithm,
            "harl_state_type": self.harl_state_type,
            "policy_sequence_mode": self.policy_sequence_mode,
            "use_recurrent_policy": self.use_recurrent_policy,
            "use_naive_recurrent_policy": self.use_naive_recurrent_policy,
            "share_param": self.share_param,
            "deterministic_actor_mode": self.deterministic_actor_mode,
            "cuda_deterministic": self.cuda_deterministic,
            "actor_observation_dimension": self.actor_observation_dimension,
            "shared_observation_dimension": self.shared_observation_dimension,
            "action_dimension": self.action_dimension,
            "noop_raw_id": self.noop_raw_id,
            "noop_decoded_value": self.noop_decoded_value,
        }


FROZEN_POLICY_INTERFACE = PolicyInterfaceContract(
    assignment_lifecycle_profile="lifecycle_contract_c",
    resolver_contract_version="assignment_lifecycle_resolver_contract_c_v1",
    actor_schema_version="lifecycle_v1_actor_3n",
    shared_schema_version="lifecycle_v1_shared_option_a_budget2m",
    mask_contract_version="lifecycle_contract_c_mask_v1",
    budget_release_contract="budget_release_v1",
    legacy_guardrail_profile="lifecycle_no_legacy_guardrails_v1",
    algorithm="happo",
    harl_state_type="EP",
    policy_sequence_mode="feed_forward",
    use_recurrent_policy=False,
    use_naive_recurrent_policy=False,
    share_param=False,
    deterministic_actor_mode=True,
    cuda_deterministic=True,
    actor_observation_dimension=1059,
    shared_observation_dimension=3183,
    action_dimension=51,
    noop_raw_id=50,
    noop_decoded_value=-1,
)


@dataclass(frozen=True)
class InitialConditionRequest:
    profile_id: str
    task_id: str
    repository_root: str
    selected_cli_field: str
    policy_interface_contract: PolicyInterfaceContract


@dataclass(frozen=True)
class CapabilityBinding:
    scanner_start_offset: tuple[float, float, float]
    arm_reach: float
    scanner_min_range: float
    scanner_max_range: float
    scanner_fov_deg: float
    scan_pos_tolerance: float
    scan_rot_tolerance: float
    max_base_xy_step: float
    max_base_yaw_step: float
    max_ee_xyz_step: float
    max_ee_rpy_step: float

    def to_mapping(self) -> dict[str, Any]:
        return {
            "scanner_start_offset": list(self.scanner_start_offset),
            "arm_reach": self.arm_reach,
            "scanner_min_range": self.scanner_min_range,
            "scanner_max_range": self.scanner_max_range,
            "scanner_fov_deg": self.scanner_fov_deg,
            "scan_pos_tolerance": self.scan_pos_tolerance,
            "scan_rot_tolerance": self.scan_rot_tolerance,
            "max_base_xy_step": self.max_base_xy_step,
            "max_base_yaw_step": self.max_base_yaw_step,
            "max_ee_xyz_step": self.max_ee_xyz_step,
            "max_ee_rpy_step": self.max_ee_rpy_step,
        }


@dataclass(frozen=True)
class ResolvedRobotIdentity:
    robot_id: str
    agent_index: int
    model_type: str
    source_pose_world_wxyz: tuple[float, float, float, float, float, float, float]
    baseline_reset_pose_world_xyzyaw: tuple[float, float, float, float]
    capability_profile: str
    capability: CapabilityBinding
    speed_weight: float
    cost_weight: float
    visual_usd_path: str | None
    visual_mesh_path: str | None
    visual_mesh_scale: tuple[float, float, float] | None
    visual_mesh_position_offset: tuple[float, float, float] | None
    visual_mesh_yaw_offset: float | None
    visual_mesh_align_bottom_to_proxy_z: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "agent_index": self.agent_index,
            "model_type": self.model_type,
            "source_pose_world_wxyz": list(self.source_pose_world_wxyz),
            "baseline_reset_pose_world_xyzyaw": list(self.baseline_reset_pose_world_xyzyaw),
            "capability_profile": self.capability_profile,
            "capability": self.capability.to_mapping(),
            "speed_weight": self.speed_weight,
            "cost_weight": self.cost_weight,
            "visual_usd_path": self.visual_usd_path,
            "visual_mesh_path": self.visual_mesh_path,
            "visual_mesh_scale": list(self.visual_mesh_scale) if self.visual_mesh_scale is not None else None,
            "visual_mesh_position_offset": (
                list(self.visual_mesh_position_offset) if self.visual_mesh_position_offset is not None else None
            ),
            "visual_mesh_yaw_offset": self.visual_mesh_yaw_offset,
            "visual_mesh_align_bottom_to_proxy_z": self.visual_mesh_align_bottom_to_proxy_z,
        }


@dataclass(frozen=True)
class ResolvedComponentIdentity:
    mesh_format: str
    mesh_unit: str
    mesh_scale: tuple[float, float, float]
    mesh_position: tuple[float, float, float]
    mesh_orientation: tuple[float, float, float, float]
    mesh_orientation_format: str
    align_base_center_to_world_origin: bool
    base_center_before_translation: tuple[float, float, float]
    auto_translation_if_used: tuple[float, float, float]
    raw_bounds_min: tuple[float, float, float]
    raw_bounds_max: tuple[float, float, float]
    world_bounds_min: tuple[float, float, float]
    world_bounds_max: tuple[float, float, float]
    auto_proxy_center: tuple[float, float, float]
    auto_proxy_half_extents: tuple[float, float, float]
    proxy_type: str
    proxy_center: tuple[float, float, float]
    proxy_half_extents: tuple[float, float, float]
    proxy_auto_from_mesh: bool
    proxy_padding: float

    def to_mapping(self) -> dict[str, Any]:
        return {
            "mesh_format": self.mesh_format,
            "mesh_unit": self.mesh_unit,
            "mesh_scale": list(self.mesh_scale),
            "mesh_position": list(self.mesh_position),
            "mesh_orientation": list(self.mesh_orientation),
            "mesh_orientation_format": self.mesh_orientation_format,
            "align_base_center_to_world_origin": self.align_base_center_to_world_origin,
            "base_center_before_translation": list(self.base_center_before_translation),
            "auto_translation_if_used": list(self.auto_translation_if_used),
            "raw_bounds_min": list(self.raw_bounds_min),
            "raw_bounds_max": list(self.raw_bounds_max),
            "world_bounds_min": list(self.world_bounds_min),
            "world_bounds_max": list(self.world_bounds_max),
            "auto_proxy_center": list(self.auto_proxy_center),
            "auto_proxy_half_extents": list(self.auto_proxy_half_extents),
            "proxy_type": self.proxy_type,
            "proxy_center": list(self.proxy_center),
            "proxy_half_extents": list(self.proxy_half_extents),
            "proxy_auto_from_mesh": self.proxy_auto_from_mesh,
            "proxy_padding": self.proxy_padding,
        }


@dataclass(frozen=True)
class ResolvedInitialConditionConfig:
    task_id: str
    scenario_name: str
    scenario_type: str
    scenario_file: ResolvedFileReference
    robot_config_file: ResolvedFileReference
    capability_config_file: ResolvedFileReference
    viewpoint_csv_file: ResolvedFileReference
    component_obj_file: ResolvedFileReference
    ordered_robot_ids: tuple[str, ...]
    robots: tuple[ResolvedRobotIdentity, ...]
    action_space_key_order: tuple[str, ...]
    observation_space_key_order: tuple[str, ...]
    state_space_key_order: tuple[str, ...]
    viewpoint_format: str
    viewpoint_source: str
    viewpoint_ids: tuple[int, ...]
    viewpoint_poses_world_wxyz: tuple[tuple[float, float, float, float, float, float, float], ...]
    component: ResolvedComponentIdentity
    num_robots: int
    num_tasks: int
    policy_interface_contract: PolicyInterfaceContract


@dataclass(frozen=True)
class PoseSlot:
    slot_id: str
    source_robot_id: str
    source_pose_world_wxyz: tuple[float, float, float, float, float, float, float]
    reset_pose_world_xyzyaw: tuple[float, float, float, float]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "source_robot_id": self.source_robot_id,
            "source_pose_world_wxyz": list(self.source_pose_world_wxyz),
            "reset_pose_world_xyzyaw": list(self.reset_pose_world_xyzyaw),
        }


@dataclass(frozen=True)
class ResolvedRobotPose:
    robot_id: str
    slot_id: str
    source_robot_id: str
    source_pose_world_wxyz: tuple[float, float, float, float, float, float, float]
    reset_pose_world_xyzyaw: tuple[float, float, float, float]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "slot_id": self.slot_id,
            "source_robot_id": self.source_robot_id,
            "source_pose_world_wxyz": list(self.source_pose_world_wxyz),
            "reset_pose_world_xyzyaw": list(self.reset_pose_world_xyzyaw),
        }


@dataclass(frozen=True)
class InitialConditionContract:
    schema_version: str
    profile_id: str
    profile_description: str
    task_id: str
    scenario_identity: tuple[str, str, str, str]
    ordered_robot_ids: tuple[str, ...]
    baseline_slots: tuple[PoseSlot, ...]
    robot_to_slot_mapping: tuple[tuple[str, str], ...]
    resolved_robot_poses: tuple[ResolvedRobotPose, ...]
    component_repository_path: str
    component_sha256: str
    component: ResolvedComponentIdentity
    viewpoint_repository_path: str
    viewpoint_sha256: str
    viewpoint_format: str
    viewpoint_conventions: tuple[tuple[str, str], ...]
    viewpoint_ids: tuple[int, ...]
    viewpoint_ordered_pose_sha256: str
    robot_config_repository_path: str
    robot_config_sha256: str
    capability_config_repository_path: str
    capability_config_sha256: str
    robot_bindings: tuple[ResolvedRobotIdentity, ...]
    policy_interface_contract: PolicyInterfaceContract
    num_robots: int
    num_tasks: int
    reset_pose_conversion_contract: str

    def to_mapping(self) -> dict[str, Any]:
        scenario_path, scenario_sha256, scenario_name, scenario_type = self.scenario_identity
        return {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "profile_description": self.profile_description,
            "task_id": self.task_id,
            "scenario_identity": {
                "repository_path": scenario_path,
                "sha256": scenario_sha256,
                "scenario_name": scenario_name,
                "scenario_type": scenario_type,
            },
            "ordered_robot_ids": list(self.ordered_robot_ids),
            "baseline_slot_ids": [slot.slot_id for slot in self.baseline_slots],
            "baseline_slot_full_poses": [slot.to_mapping() for slot in self.baseline_slots],
            "robot_to_slot_mapping": [
                {"robot_id": robot_id, "slot_id": slot_id}
                for robot_id, slot_id in self.robot_to_slot_mapping
            ],
            "resolved_robot_full_poses": [pose.to_mapping() for pose in self.resolved_robot_poses],
            "component_identity": {
                "repository_path": self.component_repository_path,
                "sha256": self.component_sha256,
                **self.component.to_mapping(),
            },
            "viewpoint_identity": {
                "repository_path": self.viewpoint_repository_path,
                "sha256": self.viewpoint_sha256,
                "format": self.viewpoint_format,
                "conventions": {key: value for key, value in self.viewpoint_conventions},
                "num_viewpoints": self.num_tasks,
                "ordered_viewpoint_ids": list(self.viewpoint_ids),
                "ordered_pose_sha256": self.viewpoint_ordered_pose_sha256,
            },
            "robot_configuration_identity": {
                "robot_config_repository_path": self.robot_config_repository_path,
                "robot_config_sha256": self.robot_config_sha256,
                "capability_config_repository_path": self.capability_config_repository_path,
                "capability_config_sha256": self.capability_config_sha256,
                "ordered_robot_bindings": [robot.to_mapping() for robot in self.robot_bindings],
            },
            "policy_interface_contract": self.policy_interface_contract.to_mapping(),
            "M": self.num_robots,
            "N": self.num_tasks,
            "reset_pose_conversion_contract": self.reset_pose_conversion_contract,
        }

    def identity_mapping(self) -> dict[str, Any]:
        mapping = self.to_mapping()
        mapping.pop("profile_description")
        return mapping


@dataclass(frozen=True)
class InitialConditionResolutionResult:
    request: InitialConditionRequest
    condition_contract: InitialConditionContract
    condition_fingerprint: str
    resolved_base_start_poses: tuple[tuple[float, float, float, float], ...]
    resolved_absolute_source_paths: tuple[tuple[str, str], ...]

    def to_diagnostics(self) -> dict[str, Any]:
        return {
            "profile_id": self.condition_contract.profile_id,
            "condition_contract_schema": self.condition_contract.schema_version,
            "condition_fingerprint": self.condition_fingerprint,
            "ordered_robot_to_slot_mapping": [
                {"robot_id": robot_id, "slot_id": slot_id}
                for robot_id, slot_id in self.condition_contract.robot_to_slot_mapping
            ],
            "resolved_base_start_poses": [list(pose) for pose in self.resolved_base_start_poses],
        }


@dataclass(frozen=True)
class InitialConditionRunProvenance:
    repository_commit: str
    selected_cli_field: str
    profile_id: str
    resolved_absolute_source_paths: tuple[tuple[str, str], ...]
    command_seed: int | None
    deterministic_actor_mode: bool
    checkpoint_directory: str
    checkpoint_child: str
    checkpoint_kind: str
    checkpoint_generation: int | None
    assignment_checkpoint_fingerprint: str | None
    load_purpose: str
    legacy_fallback: bool
    attribution_schema: str
    created_timestamp: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_commit": self.repository_commit,
            "selected_cli_field": self.selected_cli_field,
            "profile_id": self.profile_id,
            "resolved_absolute_source_paths": {
                name: path for name, path in self.resolved_absolute_source_paths
            },
            "command_seed": self.command_seed,
            "deterministic_actor_mode": self.deterministic_actor_mode,
            "checkpoint_directory": self.checkpoint_directory,
            "checkpoint_child": self.checkpoint_child,
            "checkpoint_kind": self.checkpoint_kind,
            "checkpoint_generation": self.checkpoint_generation,
            "assignment_checkpoint_fingerprint": self.assignment_checkpoint_fingerprint,
            "load_purpose": self.load_purpose,
            "legacy_fallback": self.legacy_fallback,
            "attribution_schema": self.attribution_schema,
            "created_timestamp": self.created_timestamp,
        }


@dataclass(frozen=True)
class InitialConditionManifest:
    manifest_schema_version: str
    condition_contract: InitialConditionContract
    condition_fingerprint: str
    run_provenance: InitialConditionRunProvenance

    def to_mapping(self) -> dict[str, Any]:
        return {
            "manifest_schema_version": self.manifest_schema_version,
            "condition_contract": self.condition_contract.to_mapping(),
            "condition_fingerprint": self.condition_fingerprint,
            "run_provenance": self.run_provenance.to_mapping(),
        }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_source_path(path: str | Path, *, repository_root: str | Path, field: str) -> Path:
    root = Path(repository_root).expanduser().resolve()
    candidate = Path(path).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not resolved.exists() or not resolved.is_file():
        raise InitialConditionContractError(f"{field} is not an existing file: {resolved}")
    return resolved


def make_resolved_file_reference(
    path: str | Path, *, repository_root: str | Path, field: str
) -> ResolvedFileReference:
    resolved = _resolve_source_path(path, repository_root=repository_root, field=field)
    return ResolvedFileReference(absolute_path=str(resolved), sha256=sha256_file(resolved))


def _repository_relative_posix(path: str | Path, *, repository_root: str | Path, field: str) -> str:
    root = Path(repository_root).expanduser().resolve()
    resolved = Path(path).expanduser().resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise InitialConditionContractError(f"{field} must be inside repository root {root}: {resolved}") from exc
    return relative.as_posix()


def _validate_file_reference(
    reference: ResolvedFileReference,
    *,
    repository_root: str | Path,
    identity_name: str,
) -> tuple[str, str, Path]:
    if identity_name not in EXPECTED_REPOSITORY_FILES:
        raise InitialConditionContractError(f"unknown frozen file identity {identity_name!r}")
    expected_path, expected_sha256 = EXPECTED_REPOSITORY_FILES[identity_name]
    resolved = _resolve_source_path(
        reference.absolute_path,
        repository_root=repository_root,
        field=f"{identity_name}.path",
    )
    relative = _repository_relative_posix(
        resolved,
        repository_root=repository_root,
        field=f"{identity_name}.path",
    )
    if relative != expected_path:
        raise InitialConditionContractError(
            f"{identity_name}.path mismatch: expected {expected_path!r}, got {relative!r}"
        )
    actual_sha256 = sha256_file(resolved)
    if reference.sha256 != actual_sha256:
        raise InitialConditionContractError(
            f"{identity_name}.declared_sha256 mismatch: declared {reference.sha256!r}, actual {actual_sha256!r}"
        )
    if actual_sha256 != expected_sha256:
        raise InitialConditionContractError(
            f"{identity_name}.sha256 mismatch: expected {expected_sha256!r}, got {actual_sha256!r}"
        )
    return relative, actual_sha256, resolved


def canonical_initial_condition_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InitialConditionContractError(f"initial-condition JSON is not finite/canonicalizable: {exc}") from exc
    return text.encode("utf-8")


def compute_condition_fingerprint(contract: InitialConditionContract) -> str:
    return hashlib.sha256(canonical_initial_condition_bytes(contract.identity_mapping())).hexdigest()


def _ordered_pose_digest(poses: Sequence[Sequence[float]]) -> str:
    payload = {"ordered_viewpoint_poses_world_wxyz": [list(pose) for pose in poses]}
    return hashlib.sha256(canonical_initial_condition_bytes(payload)).hexdigest()


def _close_tuple(actual: Sequence[float], expected: Sequence[float], *, field: str, tolerance: float = 1.0e-12) -> None:
    actual_tuple = tuple(float(value) for value in actual)
    expected_tuple = tuple(float(value) for value in expected)
    if len(actual_tuple) != len(expected_tuple) or any(
        not math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)
        for left, right in zip(actual_tuple, expected_tuple, strict=True)
    ):
        raise InitialConditionContractError(f"{field} mismatch: expected {expected_tuple!r}, got {actual_tuple!r}")


def _capability_from_mapping(mapping: Mapping[str, Any], *, field: str) -> CapabilityBinding:
    try:
        return CapabilityBinding(
            scanner_start_offset=_finite_float_tuple(
                mapping["scanner_start_offset"], length=3, field=f"{field}.scanner_start_offset"
            ),
            arm_reach=float(mapping["arm_reach"]),
            scanner_min_range=float(mapping["scanner_min_range"]),
            scanner_max_range=float(mapping["scanner_max_range"]),
            scanner_fov_deg=float(mapping["scanner_fov_deg"]),
            scan_pos_tolerance=float(mapping["scan_pos_tolerance"]),
            scan_rot_tolerance=float(mapping["scan_rot_tolerance"]),
            max_base_xy_step=float(mapping["max_base_xy_step"]),
            max_base_yaw_step=float(mapping["max_base_yaw_step"]),
            max_ee_xyz_step=float(mapping["max_ee_xyz_step"]),
            max_ee_rpy_step=float(mapping["max_ee_rpy_step"]),
        )
    except KeyError as exc:
        raise InitialConditionContractError(f"{field} is missing capability field {exc.args[0]!r}") from exc


def capability_binding_from_mapping(mapping: Mapping[str, Any], *, field: str) -> CapabilityBinding:
    """Build an immutable capability record from resolved config diagnostics."""

    binding = _capability_from_mapping(mapping, field=field)
    for name, value in binding.to_mapping().items():
        values = value if isinstance(value, list) else [value]
        if not all(math.isfinite(float(item)) for item in values):
            raise InitialConditionContractError(f"{field}.{name} contains NaN or Inf")
    return binding


def _validate_policy_interface(actual: PolicyInterfaceContract) -> None:
    actual_mapping = actual.to_mapping()
    expected_mapping = FROZEN_POLICY_INTERFACE.to_mapping()
    for field, expected in expected_mapping.items():
        value = actual_mapping.get(field)
        if value != expected:
            raise InitialConditionContractError(
                f"policy_interface_contract.{field} mismatch: expected {expected!r}, got {value!r}"
            )


def _validate_robots(
    config: ResolvedInitialConditionConfig,
    *,
    robot_path: Path,
    capability_path: Path,
) -> tuple[PoseSlot, ...]:
    loaded_robots = load_robot_config(robot_path).enabled_robots
    loaded_names = tuple(robot.name for robot in loaded_robots)
    if loaded_names != EXPECTED_ORDERED_ROBOT_IDS:
        raise InitialConditionContractError(
            f"robot_config ordered robots mismatch: expected {list(EXPECTED_ORDERED_ROBOT_IDS)!r}, "
            f"got {list(loaded_names)!r}"
        )
    if config.ordered_robot_ids != EXPECTED_ORDERED_ROBOT_IDS:
        raise InitialConditionContractError(
            f"ordered_robot_ids mismatch: expected {list(EXPECTED_ORDERED_ROBOT_IDS)!r}, "
            f"got {list(config.ordered_robot_ids)!r}"
        )
    if len(config.robots) != EXPECTED_NUM_ROBOTS:
        raise InitialConditionContractError(
            f"robots must contain {EXPECTED_NUM_ROBOTS} entries, got {len(config.robots)}"
        )
    for field, order in (
        ("action_space_key_order", config.action_space_key_order),
        ("observation_space_key_order", config.observation_space_key_order),
        ("state_space_key_order", config.state_space_key_order),
    ):
        if order != EXPECTED_ORDERED_ROBOT_IDS:
            raise InitialConditionContractError(
                f"{field} mismatch: expected {list(EXPECTED_ORDERED_ROBOT_IDS)!r}, got {list(order)!r}"
            )

    capability_config = load_capability_profiles(capability_path)
    slots: list[PoseSlot] = []
    for index, (actual, source) in enumerate(zip(config.robots, loaded_robots, strict=True)):
        field = f"robots[{index}]"
        if actual.robot_id != source.name:
            raise InitialConditionContractError(
                f"{field}.robot_id mismatch: expected {source.name!r}, got {actual.robot_id!r}"
            )
        if actual.agent_index != index:
            raise InitialConditionContractError(
                f"{field}.agent_index mismatch: expected {index}, got {actual.agent_index}"
            )
        source_pose = _finite_float_tuple(
            actual.source_pose_world_wxyz,
            length=7,
            field=f"{field}.source_pose_world_wxyz",
        )
        expected_reset = source_pose_wxyz_to_reset_xyzyaw(
            source_pose, field=f"{field}.source_pose_world_wxyz"
        )
        if source_pose != source.initial_pose_world:
            raise InitialConditionContractError(
                f"{field}.source_pose_world_wxyz mismatch: expected {source.initial_pose_world!r}, "
                f"got {source_pose!r}"
            )
        reset_pose = _finite_float_tuple(
            actual.baseline_reset_pose_world_xyzyaw,
            length=4,
            field=f"{field}.baseline_reset_pose_world_xyzyaw",
        )
        _close_tuple(reset_pose, expected_reset, field=f"{field}.baseline_reset_pose_world_xyzyaw")

        scalar_fields = (
            ("model_type", actual.model_type, source.model_type),
            ("capability_profile", actual.capability_profile, source.capability_profile),
            ("speed_weight", actual.speed_weight, source.speed_weight),
            ("cost_weight", actual.cost_weight, source.cost_weight),
            ("visual_usd_path", actual.visual_usd_path, source.visual_usd_path),
            ("visual_mesh_path", actual.visual_mesh_path, source.visual_mesh_path),
            ("visual_mesh_scale", actual.visual_mesh_scale, source.visual_mesh_scale),
            (
                "visual_mesh_position_offset",
                actual.visual_mesh_position_offset,
                source.visual_mesh_position_offset,
            ),
            ("visual_mesh_yaw_offset", actual.visual_mesh_yaw_offset, source.visual_mesh_yaw_offset),
            (
                "visual_mesh_align_bottom_to_proxy_z",
                actual.visual_mesh_align_bottom_to_proxy_z,
                source.visual_mesh_align_bottom_to_proxy_z,
            ),
        )
        for name, value, expected in scalar_fields:
            if value != expected:
                raise InitialConditionContractError(
                    f"{field}.{name} mismatch: expected {expected!r}, got {value!r}"
                )

        profile = capability_config.profiles.get(source.capability_profile)
        if profile is None:
            raise InitialConditionContractError(
                f"{field}.capability_profile {source.capability_profile!r} is absent from capability config"
            )
        expected_capability = capability_binding_from_mapping(
            profile.to_dict(), field=f"capability_config.{source.capability_profile}"
        )
        if actual.capability != expected_capability:
            raise InitialConditionContractError(
                f"{field}.capability binding changed for robot {actual.robot_id!r}: "
                f"expected {expected_capability.to_mapping()!r}, got {actual.capability.to_mapping()!r}"
            )
        slots.append(
            PoseSlot(
                slot_id=EXPECTED_SLOT_IDS[index],
                source_robot_id=actual.robot_id,
                source_pose_world_wxyz=source_pose,
                reset_pose_world_xyzyaw=reset_pose,
            )
        )
    return tuple(slots)


def _validate_viewpoints(config: ResolvedInitialConditionConfig, *, viewpoint_path: Path) -> str:
    loaded = load_fixed_viewpoint_csv(viewpoint_path)
    if config.viewpoint_format != VIEWPOINT_CSV_FORMAT:
        raise InitialConditionContractError(
            f"viewpoint_format mismatch: expected {VIEWPOINT_CSV_FORMAT!r}, got {config.viewpoint_format!r}"
        )
    expected_source = f"csv:{loaded.path}"
    if config.viewpoint_source != expected_source:
        raise InitialConditionContractError(
            f"viewpoint_source mismatch: expected {expected_source!r}, got {config.viewpoint_source!r}"
        )
    if config.viewpoint_ids != tuple(range(EXPECTED_NUM_TASKS)):
        raise InitialConditionContractError(
            "viewpoint_ids must be ordered exactly 0..49; "
            f"got {list(config.viewpoint_ids)!r}"
        )
    if config.viewpoint_ids != loaded.ids:
        raise InitialConditionContractError("resolved viewpoint ordering differs from the frozen CSV ordering")
    if len(config.viewpoint_poses_world_wxyz) != EXPECTED_NUM_TASKS:
        raise InitialConditionContractError(
            f"viewpoint poses must contain {EXPECTED_NUM_TASKS} rows, got {len(config.viewpoint_poses_world_wxyz)}"
        )
    normalized_poses = tuple(
        _finite_float_tuple(pose, length=7, field=f"viewpoint_poses_world_wxyz[{index}]")
        for index, pose in enumerate(config.viewpoint_poses_world_wxyz)
    )
    if normalized_poses != loaded.poses:
        raise InitialConditionContractError(
            "viewpoint_poses_world_wxyz ordering/values differ from the frozen viewpoint CSV"
        )
    return _ordered_pose_digest(normalized_poses)


def _validate_component(config: ResolvedInitialConditionConfig, *, component_path: Path) -> None:
    actual = config.component
    fixed_values = (
        ("mesh_format", actual.mesh_format, "obj"),
        ("mesh_unit", actual.mesh_unit, "mm"),
        ("mesh_orientation_format", actual.mesh_orientation_format, "qwxyz"),
        ("align_base_center_to_world_origin", actual.align_base_center_to_world_origin, True),
        ("proxy_type", actual.proxy_type, "bbox"),
        ("proxy_auto_from_mesh", actual.proxy_auto_from_mesh, False),
        ("proxy_padding", actual.proxy_padding, 0.0),
    )
    for field, value, expected in fixed_values:
        if value != expected:
            raise InitialConditionContractError(
                f"component.{field} mismatch: expected {expected!r}, got {value!r}"
            )
    _close_tuple(actual.mesh_scale, (0.001, 0.001, 0.001), field="component.mesh_scale")
    _close_tuple(actual.mesh_orientation, (1.0, 0.0, 0.0, 0.0), field="component.mesh_orientation")
    _close_tuple(actual.proxy_center, (0.0, 0.0, 1.0), field="component.proxy_center")
    _close_tuple(actual.proxy_half_extents, (3.0, 1.0, 1.0), field="component.proxy_half_extents")

    alignment = compute_base_center_alignment_translation(
        mesh_path=component_path,
        mesh_format=actual.mesh_format,
        mesh_unit=actual.mesh_unit,
        mesh_scale=actual.mesh_scale,
        mesh_orientation=actual.mesh_orientation,
        mesh_orientation_format=actual.mesh_orientation_format,
    )
    expected_bounds = compute_component_mesh_bounds(
        mesh_path=component_path,
        mesh_format=actual.mesh_format,
        mesh_unit=actual.mesh_unit,
        mesh_scale=actual.mesh_scale,
        mesh_position=alignment.auto_translation,
        mesh_orientation=actual.mesh_orientation,
        mesh_orientation_format=actual.mesh_orientation_format,
        component_proxy_padding=actual.proxy_padding,
    )
    comparisons = (
        ("mesh_position", actual.mesh_position, alignment.auto_translation),
        ("base_center_before_translation", actual.base_center_before_translation, alignment.base_center_before_translation),
        ("auto_translation_if_used", actual.auto_translation_if_used, alignment.auto_translation),
        ("raw_bounds_min", actual.raw_bounds_min, expected_bounds.raw_bounds_obj_units_min),
        ("raw_bounds_max", actual.raw_bounds_max, expected_bounds.raw_bounds_obj_units_max),
        ("world_bounds_min", actual.world_bounds_min, expected_bounds.world_bounds_m_min),
        ("world_bounds_max", actual.world_bounds_max, expected_bounds.world_bounds_m_max),
        ("auto_proxy_center", actual.auto_proxy_center, expected_bounds.auto_component_proxy_center),
        ("auto_proxy_half_extents", actual.auto_proxy_half_extents, expected_bounds.auto_component_proxy_half_extents),
    )
    for field, value, expected in comparisons:
        _close_tuple(value, expected, field=f"component.{field}")


def _validate_top_level(config: ResolvedInitialConditionConfig, request: InitialConditionRequest) -> None:
    if request.task_id != EXPECTED_TASK_ID or config.task_id != EXPECTED_TASK_ID:
        raise InitialConditionContractError(
            f"task_id mismatch: expected {EXPECTED_TASK_ID!r}, request={request.task_id!r}, config={config.task_id!r}"
        )
    if config.scenario_name != EXPECTED_SCENARIO_NAME:
        raise InitialConditionContractError(
            f"scenario_name mismatch: expected {EXPECTED_SCENARIO_NAME!r}, got {config.scenario_name!r}"
        )
    if config.scenario_type != EXPECTED_SCENARIO_TYPE:
        raise InitialConditionContractError(
            f"scenario_type mismatch: expected {EXPECTED_SCENARIO_TYPE!r}, got {config.scenario_type!r}"
        )
    if isinstance(config.num_robots, bool) or config.num_robots != EXPECTED_NUM_ROBOTS:
        raise InitialConditionContractError(
            f"M mismatch: expected {EXPECTED_NUM_ROBOTS}, got {config.num_robots!r}"
        )
    if isinstance(config.num_tasks, bool) or config.num_tasks != EXPECTED_NUM_TASKS:
        raise InitialConditionContractError(
            f"N mismatch: expected {EXPECTED_NUM_TASKS}, got {config.num_tasks!r}"
        )
    if request.policy_interface_contract != config.policy_interface_contract:
        raise InitialConditionContractError("request/config policy_interface_contract values differ")
    _validate_policy_interface(config.policy_interface_contract)


def resolve_assignment_initial_condition(
    request: InitialConditionRequest | None,
    config: ResolvedInitialConditionConfig | None,
) -> InitialConditionResolutionResult | None:
    """Validate and resolve one frozen profile, or return immediately when off."""

    if request is None:
        return None
    if config is None:
        raise InitialConditionUsageError("explicit initial-condition request requires resolved project configuration")
    profile = _PROFILE_BY_ID.get(request.profile_id)
    if profile is None:
        raise InitialConditionProfileError(
            f"unknown initial-condition profile {request.profile_id!r}; expected one of {INITIAL_CONDITION_PROFILE_CHOICES!r}"
        )
    validate_initial_condition_profile(profile)
    _validate_top_level(config, request)

    root = Path(request.repository_root).expanduser().resolve()
    scenario_rel, scenario_sha, scenario_path = _validate_file_reference(
        config.scenario_file, repository_root=root, identity_name="scenario"
    )
    robot_rel, robot_sha, robot_path = _validate_file_reference(
        config.robot_config_file, repository_root=root, identity_name="robot_config"
    )
    capability_rel, capability_sha, capability_path = _validate_file_reference(
        config.capability_config_file, repository_root=root, identity_name="capability_config"
    )
    viewpoint_rel, viewpoint_sha, viewpoint_path = _validate_file_reference(
        config.viewpoint_csv_file, repository_root=root, identity_name="viewpoint_csv"
    )
    component_rel, component_sha, component_path = _validate_file_reference(
        config.component_obj_file, repository_root=root, identity_name="component_obj"
    )

    baseline_slots = _validate_robots(config, robot_path=robot_path, capability_path=capability_path)
    viewpoint_pose_sha = _validate_viewpoints(config, viewpoint_path=viewpoint_path)
    _validate_component(config, component_path=component_path)

    slot_by_id = {slot.slot_id: slot for slot in baseline_slots}
    resolved_poses = tuple(
        ResolvedRobotPose(
            robot_id=robot_id,
            slot_id=slot_id,
            source_robot_id=slot_by_id[slot_id].source_robot_id,
            source_pose_world_wxyz=slot_by_id[slot_id].source_pose_world_wxyz,
            reset_pose_world_xyzyaw=slot_by_id[slot_id].reset_pose_world_xyzyaw,
        )
        for robot_id, slot_id in profile.robot_to_slot_mapping
    )
    if Counter(pose.source_pose_world_wxyz for pose in resolved_poses) != Counter(
        slot.source_pose_world_wxyz for slot in baseline_slots
    ):
        raise InitialConditionContractError("resolved source-pose multiset differs from baseline")
    if Counter(pose.reset_pose_world_xyzyaw for pose in resolved_poses) != Counter(
        slot.reset_pose_world_xyzyaw for slot in baseline_slots
    ):
        raise InitialConditionContractError("resolved reset-pose multiset differs from baseline")

    contract = InitialConditionContract(
        schema_version=CONDITION_CONTRACT_SCHEMA,
        profile_id=profile.profile_id,
        profile_description=profile.description,
        task_id=config.task_id,
        scenario_identity=(scenario_rel, scenario_sha, config.scenario_name, config.scenario_type),
        ordered_robot_ids=config.ordered_robot_ids,
        baseline_slots=baseline_slots,
        robot_to_slot_mapping=profile.robot_to_slot_mapping,
        resolved_robot_poses=resolved_poses,
        component_repository_path=component_rel,
        component_sha256=component_sha,
        component=config.component,
        viewpoint_repository_path=viewpoint_rel,
        viewpoint_sha256=viewpoint_sha,
        viewpoint_format=config.viewpoint_format,
        viewpoint_conventions=tuple(VIEWPOINT_CSV_CONVENTIONS.items()),
        viewpoint_ids=config.viewpoint_ids,
        viewpoint_ordered_pose_sha256=viewpoint_pose_sha,
        robot_config_repository_path=robot_rel,
        robot_config_sha256=robot_sha,
        capability_config_repository_path=capability_rel,
        capability_config_sha256=capability_sha,
        robot_bindings=config.robots,
        policy_interface_contract=config.policy_interface_contract,
        num_robots=config.num_robots,
        num_tasks=config.num_tasks,
        reset_pose_conversion_contract=RESET_POSE_CONVERSION_CONTRACT,
    )
    fingerprint = compute_condition_fingerprint(contract)
    absolute_paths = (
        ("scenario", str(scenario_path)),
        ("robot_config", str(robot_path)),
        ("capability_config", str(capability_path)),
        ("viewpoint_csv", str(viewpoint_path)),
        ("component_obj", str(component_path)),
    )
    return InitialConditionResolutionResult(
        request=request,
        condition_contract=contract,
        condition_fingerprint=fingerprint,
        resolved_base_start_poses=tuple(pose.reset_pose_world_xyzyaw for pose in resolved_poses),
        resolved_absolute_source_paths=absolute_paths,
    )


def make_playback_policy_interface_contract(
    *,
    assignment_lifecycle_profile: str,
    algorithm: str,
    use_recurrent_policy: bool,
    use_naive_recurrent_policy: bool,
    share_param: bool,
    cuda_deterministic: bool,
) -> PolicyInterfaceContract:
    mode = (
        "chunked_recurrent"
        if bool(use_recurrent_policy)
        else "naive_recurrent"
        if bool(use_naive_recurrent_policy)
        else "feed_forward"
    )
    return PolicyInterfaceContract(
        assignment_lifecycle_profile=str(assignment_lifecycle_profile),
        resolver_contract_version=FROZEN_POLICY_INTERFACE.resolver_contract_version,
        actor_schema_version=FROZEN_POLICY_INTERFACE.actor_schema_version,
        shared_schema_version=FROZEN_POLICY_INTERFACE.shared_schema_version,
        mask_contract_version=FROZEN_POLICY_INTERFACE.mask_contract_version,
        budget_release_contract=FROZEN_POLICY_INTERFACE.budget_release_contract,
        legacy_guardrail_profile=FROZEN_POLICY_INTERFACE.legacy_guardrail_profile,
        algorithm=str(algorithm).lower(),
        harl_state_type="EP",
        policy_sequence_mode=mode,
        use_recurrent_policy=use_recurrent_policy,
        use_naive_recurrent_policy=use_naive_recurrent_policy,
        share_param=share_param,
        deterministic_actor_mode=True,
        cuda_deterministic=cuda_deterministic,
        actor_observation_dimension=1059,
        shared_observation_dimension=3183,
        action_dimension=51,
        noop_raw_id=50,
        noop_decoded_value=-1,
    )


def make_initial_condition_request(
    *,
    profile_id: str,
    task_id: str,
    repository_root: str | Path,
    policy_interface_contract: PolicyInterfaceContract,
) -> InitialConditionRequest:
    if profile_id not in _PROFILE_BY_ID:
        raise InitialConditionProfileError(
            f"unknown initial-condition profile {profile_id!r}; expected one of {INITIAL_CONDITION_PROFILE_CHOICES!r}"
        )
    request = InitialConditionRequest(
        profile_id=profile_id,
        task_id=task_id,
        repository_root=str(Path(repository_root).expanduser().resolve()),
        selected_cli_field=INITIAL_CONDITION_CLI_FIELD,
        policy_interface_contract=policy_interface_contract,
    )
    _validate_policy_interface(policy_interface_contract)
    return request


def validate_initial_condition_playback_cli(
    *,
    profile_id: str | None,
    attribution_logging_enabled: bool,
    attribution_output_dir: str | Path | None,
) -> None:
    """Reject malformed explicit-profile use before AppLauncher construction."""

    if profile_id is None:
        return
    if profile_id not in _PROFILE_BY_ID:
        raise InitialConditionProfileError(
            f"unknown initial-condition profile {profile_id!r}; expected one of {INITIAL_CONDITION_PROFILE_CHOICES!r}"
        )
    if not attribution_logging_enabled:
        raise InitialConditionUsageError(
            f"{INITIAL_CONDITION_CLI_FIELD} requires --log_assignment_proposal_effective"
        )
    if attribution_output_dir is None:
        raise InitialConditionUsageError(
            f"{INITIAL_CONDITION_CLI_FIELD} requires --assignment_proposal_effective_output_dir"
        )
    output_path = Path(attribution_output_dir).expanduser().resolve()
    if output_path.exists() and not output_path.is_dir():
        raise NotADirectoryError(f"initial-condition attribution output is not a directory: {output_path}")
    if output_path.exists():
        collisions = tuple(path for path in output_path.iterdir() if path.is_file())
        if collisions:
            raise FileExistsError(
                f"explicit initial-condition attribution output must be new/empty: {collisions[0]}"
            )


def validate_initial_condition_training_config(config: Any) -> None:
    """Keep controlled start-pose profiles out of every training runner path."""

    profile = getattr(config, "assignment_initial_condition_profile", None)
    request = getattr(config, "assignment_initial_condition_request", None)
    if profile is not None or request is not None:
        requested = profile if profile is not None else getattr(request, "profile_id", type(request).__name__)
        raise InitialConditionUsageError(
            "controlled assignment initial-condition profiles are playback-attribution only; "
            f"training received profile/request {requested!r} before runner construction"
        )


def validate_initial_condition_runtime_interface(
    result: InitialConditionResolutionResult,
    *,
    ordered_agent_ids: Sequence[str],
    observation_manifest: Mapping[str, Any],
) -> None:
    """Validate wrapper identity and dimensions without coupling this module to HARL."""

    if tuple(str(value) for value in ordered_agent_ids) != EXPECTED_ORDERED_ROBOT_IDS:
        raise InitialConditionContractError(
            f"runtime actor ordering mismatch: expected {list(EXPECTED_ORDERED_ROBOT_IDS)!r}, "
            f"got {list(ordered_agent_ids)!r}"
        )
    expected_fields = {
        "profile_name": FROZEN_POLICY_INTERFACE.assignment_lifecycle_profile,
        "actor_schema_version": FROZEN_POLICY_INTERFACE.actor_schema_version,
        "shared_schema_version": FROZEN_POLICY_INTERFACE.shared_schema_version,
        "mask_contract_version": FROZEN_POLICY_INTERFACE.mask_contract_version,
        "budget_release_contract": FROZEN_POLICY_INTERFACE.budget_release_contract,
        "legacy_guardrail_profile": FROZEN_POLICY_INTERFACE.legacy_guardrail_profile,
        "actor_dimension": FROZEN_POLICY_INTERFACE.actor_observation_dimension,
        "shared_dimension": FROZEN_POLICY_INTERFACE.shared_observation_dimension,
        "M": EXPECTED_NUM_ROBOTS,
        "N": EXPECTED_NUM_TASKS,
        "action_dimension": FROZEN_POLICY_INTERFACE.action_dimension,
        "noop_raw_id": FROZEN_POLICY_INTERFACE.noop_raw_id,
        "noop_decoded_value": FROZEN_POLICY_INTERFACE.noop_decoded_value,
        "policy_sequence_mode": FROZEN_POLICY_INTERFACE.policy_sequence_mode,
        "use_recurrent_policy": False,
        "use_naive_recurrent_policy": False,
    }
    for field, expected in expected_fields.items():
        value = observation_manifest.get(field)
        if value != expected:
            raise InitialConditionContractError(
                f"runtime observation manifest {field} mismatch: expected {expected!r}, got {value!r}"
            )
    if result.condition_contract.policy_interface_contract != FROZEN_POLICY_INTERFACE:
        raise InitialConditionContractError("resolved condition policy interface changed before wrapper validation")


def build_initial_condition_manifest(
    result: InitialConditionResolutionResult,
    provenance: InitialConditionRunProvenance,
) -> InitialConditionManifest:
    if provenance.profile_id != result.condition_contract.profile_id:
        raise InitialConditionManifestError(
            f"run provenance profile {provenance.profile_id!r} does not match resolved profile "
            f"{result.condition_contract.profile_id!r}"
        )
    if provenance.selected_cli_field != INITIAL_CONDITION_CLI_FIELD:
        raise InitialConditionManifestError(
            f"run provenance selected_cli_field must be {INITIAL_CONDITION_CLI_FIELD!r}"
        )
    if provenance.resolved_absolute_source_paths != result.resolved_absolute_source_paths:
        raise InitialConditionManifestError("run provenance absolute source paths differ from resolved paths")
    recomputed = compute_condition_fingerprint(result.condition_contract)
    if recomputed != result.condition_fingerprint:
        raise InitialConditionManifestError("condition fingerprint no longer matches the resolved contract")
    manifest = InitialConditionManifest(
        manifest_schema_version=CONDITION_MANIFEST_SCHEMA,
        condition_contract=result.condition_contract,
        condition_fingerprint=result.condition_fingerprint,
        run_provenance=provenance,
    )
    canonical_initial_condition_bytes(manifest.to_mapping())
    return manifest


def write_initial_condition_manifest_atomic(
    path: str | Path,
    manifest: InitialConditionManifest,
) -> Path:
    """Publish a complete finite JSON manifest without ever replacing a file."""

    destination = Path(path).expanduser().resolve()
    if not destination.parent.exists() or not destination.parent.is_dir():
        raise InitialConditionManifestError(
            f"initial-condition manifest parent directory does not exist: {destination.parent}"
        )
    if destination.exists():
        raise FileExistsError(f"initial-condition manifest already exists: {destination}")
    try:
        text = json.dumps(
            manifest.to_mapping(),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        ) + "\n"
    except (TypeError, ValueError) as exc:
        raise InitialConditionManifestError(f"initial-condition manifest is not finite JSON: {exc}") from exc

    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            raise FileExistsError(f"initial-condition manifest already exists: {destination}") from None
        except OSError as exc:
            raise InitialConditionManifestError(
                f"atomic no-clobber manifest publication failed for {destination}: {exc}"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def validate_initial_condition_output_files(
    output_dir: str | Path,
    *,
    attribution_filenames: Sequence[str],
    manifest_expected: bool,
) -> tuple[str, ...]:
    directory = Path(output_dir).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        raise InitialConditionManifestError(f"attribution output directory does not exist: {directory}")
    expected = tuple(str(name) for name in attribution_filenames)
    if manifest_expected:
        expected = expected + (INITIAL_CONDITION_MANIFEST_FILENAME,)
    entries = tuple(directory.iterdir())
    non_files = tuple(path.name for path in entries if not path.is_file())
    if non_files:
        raise InitialConditionManifestError(
            f"initial-condition output directory contains non-file entries: {non_files!r}"
        )
    actual = tuple(sorted(path.name for path in entries))
    expected_sorted = tuple(sorted(expected))
    if actual != expected_sorted:
        raise InitialConditionManifestError(
            f"initial-condition output contract mismatch: expected {expected_sorted!r}, got {actual!r}"
        )
    return actual


__all__ = [
    "AssignmentInitialConditionError",
    "CapabilityBinding",
    "CONDITION_CONTRACT_SCHEMA",
    "CONDITION_MANIFEST_SCHEMA",
    "EXPECTED_NUM_ROBOTS",
    "EXPECTED_NUM_TASKS",
    "EXPECTED_ORDERED_ROBOT_IDS",
    "EXPECTED_REPOSITORY_FILES",
    "EXPECTED_SLOT_IDS",
    "EXPECTED_TASK_ID",
    "FROZEN_POLICY_INTERFACE",
    "INITIAL_CONDITION_CLI_FIELD",
    "INITIAL_CONDITION_MANIFEST_FILENAME",
    "INITIAL_CONDITION_PROFILE_CHOICES",
    "INITIAL_CONDITION_PROFILE_REGISTRY",
    "InitialConditionContract",
    "InitialConditionContractError",
    "InitialConditionManifest",
    "InitialConditionManifestError",
    "InitialConditionProfile",
    "InitialConditionProfileError",
    "InitialConditionRequest",
    "InitialConditionResolutionResult",
    "InitialConditionRunProvenance",
    "InitialConditionUsageError",
    "PolicyInterfaceContract",
    "PoseSlot",
    "RESET_POSE_CONVERSION_CONTRACT",
    "ResolvedComponentIdentity",
    "ResolvedFileReference",
    "ResolvedInitialConditionConfig",
    "ResolvedRobotIdentity",
    "ResolvedRobotPose",
    "build_initial_condition_manifest",
    "canonical_initial_condition_bytes",
    "capability_binding_from_mapping",
    "compute_condition_fingerprint",
    "make_initial_condition_request",
    "make_playback_policy_interface_contract",
    "make_resolved_file_reference",
    "quaternion_wxyz_to_yaw",
    "resolve_assignment_initial_condition",
    "sha256_file",
    "source_pose_wxyz_to_reset_xyzyaw",
    "validate_initial_condition_output_files",
    "validate_initial_condition_playback_cli",
    "validate_initial_condition_profile",
    "validate_initial_condition_runtime_interface",
    "validate_initial_condition_training_config",
    "write_initial_condition_manifest_atomic",
]
