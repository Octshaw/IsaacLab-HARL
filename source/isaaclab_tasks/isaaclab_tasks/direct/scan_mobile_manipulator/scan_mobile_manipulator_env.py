# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
import torch
from collections.abc import Mapping, Sequence
from pathlib import Path

from isaaclab.envs import DirectMARLEnv, DirectMARLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import (
    normalize,
    quat_apply,
    quat_error_magnitude,
    quat_from_euler_xyz,
    quat_mul,
    wrap_to_pi,
)

from .component_mesh import (
    compute_base_center_alignment_translation,
    compute_component_mesh_bounds,
    load_obj_mesh,
    transform_vertices,
    validate_mesh_format,
    validate_mesh_unit,
    validate_orientation_format,
)
from .component_obstacle_footprint import ComponentObstacleFootprint, build_component_obstacle_footprint
from .assignment_state import (
    ROBOT_IDLE,
    ROBOT_STATUS_NAMES,
    TASK_COMPLETED,
    TASK_STATUS_NAMES,
    TASK_UNASSIGNED,
)
from .static_feasibility import generate_static_geometric_feasibility
from .viewpoint_csv import VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv
from .robot_config import RobotConfig, RobotSpec, load_robot_config
from .capability_config import CapabilityConfig, CapabilityProfile, load_capability_profiles


ROBOT_ACTION_DIM = 9
BASE_OBSERVATION_DIM_WITHOUT_OTHER_SCANNERS = 90
LEGACY_ROBOT_CONFIG_PATH = Path("<builtin_legacy_three_proxy>")
ROBOT_VISUAL_MESH_SCALE = (0.001, 0.001, 0.001)
ROBOT_VISUAL_MESH_POSITION_OFFSET = (0.0, 0.0, 0.0)
ROBOT_VISUAL_MESH_YAW_OFFSET = 0.0
ROBOT_VISUAL_MODES = ("mesh", "debug_marker", "none")
COMPONENT_VISUAL_MODES = ("mesh", "bbox", "none")
LEGACY_CAPABILITY_PROFILES = ("mobile_scanner_a", "mobile_scanner_b", "mobile_scanner_c")


@configclass
class ScanMobileManipulatorEnvCfg(DirectMARLEnvCfg):
    """Configuration for the high-level heterogeneous scanning task.

    This environment is intentionally a task-space skeleton. It keeps robot state in tensors and uses lightweight USD
    debug markers for visualization, so assignment/controller logic can be validated before real robot assets, IK,
    collision checks, or raycast scanning are connected.

    Each agent action controls a kinematic task-space proxy:
    [base_dx, base_dy, base_dyaw, ee_dx, ee_dy, ee_dz, ee_droll, ee_dpitch, ee_dyaw].
    Quaternions are stored in Isaac Lab's scalar-first convention: (w, x, y, z).
    """

    # Basic episode timing. With dt=1/60 and decimation=6, the policy/control step is about 0.1 second.
    seed = 1
    ui_window_class_type = None
    episode_length_s = 30.0
    decimation = 6

    # Every robot is exposed as one HARL agent. The 9D action is shared structurally, while per-robot step sizes below
    # make the agents heterogeneous in practice.
    action_spaces = {"robot_0": ROBOT_ACTION_DIM, "robot_1": ROBOT_ACTION_DIM, "robot_2": ROBOT_ACTION_DIM}

    # Observation dimensions must match `_get_observations()`. Three legacy robots produce the original 96D layout;
    # Robot Config MVP paths update this to account for the enabled robot count before DirectMARLEnv initializes.
    observation_spaces = {"robot_0": 96, "robot_1": 96, "robot_2": 96}

    # `state_space = -1` asks DirectMARLEnv to build the shared state by concatenating all agent observations.
    state_space = -1
    state_spaces = {f"robot_{i}": 0 for i in range(3)}
    possible_agents = ["robot_0", "robot_1", "robot_2"]

    # Optional Robot Config MVP YAML. When omitted, the legacy three task-space proxy setup is preserved.
    scenario_config_path = None
    scenario_name = None
    scenario_type = None
    robot_config_path = None
    robot_config_diagnostics = None
    # Optional capability profile YAML. When omitted, configs/capabilities/mobile_scanner_profiles.yaml is used.
    capability_config_path = None
    capability_config_diagnostics = None
    # Visual mode controls let algorithm scenarios avoid loading large visual-only assets while preserving GUI demos.
    robot_visual_mode = "mesh"
    component_visual_mode = "mesh"

    # Simulation config is still needed by Isaac Lab even though this skeleton does not spawn real robot articulations.
    sim: SimulationCfg = SimulationCfg(dt=1 / 60, render_interval=decimation)

    # The scene only holds cloned env roots and optional USD debug markers. Real Articulation/RigidObject assets should
    # be registered here later when the high-level task is replaced by a physical robot model.
    scene: InteractiveSceneCfg = InteractiveSceneCfg(num_envs=64, env_spacing=12.0, replicate_physics=True)

    # Minimal Stage 1 component proxy support. Only bbox is supported for now; scanner range is measured from the
    # scanner/viewpoint to this axis-aligned box surface until mesh/raycast coverage is introduced later.
    component_proxy_type = "bbox"
    component_proxy_center = (0.0, 0.0, 1.0)
    component_proxy_half_extents = (3.0, 1.0, 1.0)
    component_proxy_auto_from_mesh = False
    component_proxy_padding = 0.0
    component_proxy_visual_visible = True
    # Legacy aliases kept so existing fixed-12 config readers do not break while the new proxy fields become canonical.
    component_center = component_proxy_center
    component_half_extents = component_proxy_half_extents

    # Optional visual-only measured component mesh. OBJ units are explicit; the default millimeter scale converts raw
    # OBJ coordinates to meters. The mesh does not participate in collision, raycast, IK, or coverage.
    component_mesh_path = None
    component_mesh_format = "obj"
    component_mesh_unit = "mm"
    component_mesh_scale = (0.001, 0.001, 0.001)
    component_mesh_position = (0.0, 0.0, 0.0)
    component_mesh_orientation = (1.0, 0.0, 0.0, 0.0)
    component_mesh_orientation_format = "qwxyz"
    component_mesh_visible = True
    component_mesh_align_base_center_to_world_origin = False
    component_mesh_base_center_before_translation = None
    component_mesh_auto_translation_if_used = None
    component_mesh_resolved_path = None
    component_mesh_raw_bounds_obj_units_min = None
    component_mesh_raw_bounds_obj_units_max = None
    component_mesh_scaled_local_bounds_m_min = None
    component_mesh_scaled_local_bounds_m_max = None
    component_mesh_world_bounds_m_min = None
    component_mesh_world_bounds_m_max = None
    component_mesh_auto_proxy_center = None
    component_mesh_auto_proxy_half_extents = None

    # Optional diagnostic-only obstacle footprint. These fields report straight-line path crossings against an inflated
    # component OBJ footprint and do not alter cost_matrix, masks, reward, controller logic, or solver behavior.
    obstacle_diagnostics_enabled = False
    obstacle_diagnostics_mode = "disabled"
    obstacle_source = None
    obstacle_footprint_resolution = 0.10
    obstacle_footprint_inflation_radius = 0.30
    obstacle_line_sample_step = 0.10
    obstacle_blocked_path_penalty = 100.0
    component_obstacle_footprint = None
    component_obstacle_footprint_diagnostics = None

    # Optional visual-only debug lines for obstacle diagnostics. These draw a small sample of robot-to-viewpoint
    # segments that already intersect the diagnostic mesh footprint. They do not alter assignment costs or masks.
    obstacle_debug_visualization_enabled = False
    obstacle_debug_visualization_draw_in_headless = False
    obstacle_debug_visualization_line_source = "mesh_footprint_intersections"
    obstacle_debug_visualization_max_lines_per_robot = 5
    obstacle_debug_visualization_max_total_lines = 20
    obstacle_debug_visualization_prefer_shortest_blocked_pairs = True
    obstacle_debug_visualization_line_z_mode = "max_endpoint"
    obstacle_debug_visualization_line_z_value = 0.20
    obstacle_debug_visualization_line_z_offset = 0.05
    obstacle_debug_visualization_line_width = 0.03

    enable_usd_debug_visuals = True
    use_camera_light_in_gui = True
    gui_camera_enabled = True
    gui_camera_eye = (0.0, -7.5, 3.2)
    gui_camera_target = (0.0, 0.0, 1.1)
    ground_grid_enabled = False
    ground_grid_half_extent = 6.0
    ground_grid_spacing = 0.5
    ground_grid_z = 0.01
    ground_grid_line_width = 0.008

    # Fixed 12-viewpoint MVP scan set. Pose layout is [x, y, z, qw, qx, qy, qz]; keep the WXYZ quaternion order used by
    # Isaac Lab math utilities. Viewpoint 11 is intentionally outside the component proxy's min-range shell so it remains
    # an available coverage target for this scenario.
    viewpoint_poses = (
        (-3.0, -1.35, 1.0, 0.7071, 0.0, 0.0, 0.7071),
        (-1.5, -1.35, 1.3, 0.7071, 0.0, 0.0, 0.7071),
        (0.0, -1.35, 1.6, 0.7071, 0.0, 0.0, 0.7071),
        (1.5, -1.35, 1.3, 0.7071, 0.0, 0.0, 0.7071),
        (3.0, -1.35, 1.0, 0.7071, 0.0, 0.0, 0.7071),
        (-3.0, 1.35, 1.0, 0.7071, 0.0, 0.0, -0.7071),
        (-1.5, 1.35, 1.3, 0.7071, 0.0, 0.0, -0.7071),
        (0.0, 1.35, 1.6, 0.7071, 0.0, 0.0, -0.7071),
        (1.5, 1.35, 1.3, 0.7071, 0.0, 0.0, -0.7071),
        (3.0, 1.35, 1.0, 0.7071, 0.0, 0.0, -0.7071),
        # (-3.2, 0.0, 1.4, 1.0, 0.0, 0.0, 0.0),
        # (3.2, 0.0, 1.4, 0.0, 0.0, 0.0, 1.0),
        (1.9, 1.55, 1.4, 0.7071, 0.0, 0.0, -0.7071),
        (2.8, 1.45, 1.2, 0.7071, 0.0, 0.0, -0.7071),
    )
    viewpoint_csv_path = None
    viewpoint_csv_format = VIEWPOINT_CSV_FORMAT
    viewpoint_source = "builtin_fixed_12"
    viewpoint_ids = ()
    enable_reset_diagnostics = True
    reset_diagnostics_once = True
    feasibility_generator_type = "static_geometric_v1"
    require_each_viewpoint_feasible = True
    num_viewpoints_in_observation = 8
    # Fixed 12-viewpoint MVP scenario-level capability override. Bounded diagnostics showed robot_2 does not stably
    # satisfy the coverage gates for viewpoint 5 within the current high-level controller/tolerance setup. This is not a
    # generic arbitrary-viewpoint feasibility rule; remove or replace it when moving beyond the fixed MVP scenario.
    fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
    fixed_12_mvp_level2_diagnostic_reasons = (
        ("robot_2", 5, "level2_controller_diagnostic_position_rotation_gates_never_simultaneously_satisfied"),
    )

    # Legacy heterogeneous robot capability parameters. Tuple index 0/1/2 maps to robot_0/robot_1/robot_2 respectively.
    # These values affect action scaling, assignment feasibility, scan completion checks, and observation features.
    base_start_poses = (
        (-4.0, -3.0, 0.15, 0.0),
        (0.0, 3.2, 0.15, -math.pi / 2),
        (4.0, -3.0, 0.15, math.pi),
    )
    scanner_start_offsets = (
        (0.7, 0.0, 0.85),
        (0.9, 0.0, 1.05),
        (0.6, 0.0, 0.75),
    )
    arm_reach = (2.0, 3.0, 1.6)
    scanner_min_range = (0.25, 0.35, 0.20)
    scanner_max_range = (1.4, 2.0, 1.1)
    scanner_fov_deg = (65.0, 90.0, 50.0)
    scan_pos_tolerance = (0.18, 0.25, 0.15)
    scan_rot_tolerance = (0.45, 0.60, 0.40)
    max_base_xy_step = (0.08, 0.10, 0.06)
    max_base_yaw_step = (0.08, 0.10, 0.06)
    max_ee_xyz_step = (0.07, 0.09, 0.05)
    max_ee_rpy_step = (0.08, 0.10, 0.06)
    dwell_steps = 1

    # Reward scales for coverage, duplicate scans, reach violations, action smoothness, and elapsed time.
    global_coverage_reward_scale = 5.0
    own_coverage_reward_scale = 2.0
    duplicate_scan_penalty_scale = 0.25
    reach_violation_penalty_scale = 0.05
    action_rate_penalty_scale = 0.01
    time_penalty = 0.002


def _as_float_tuple(value, *, name: str, length: int) -> tuple[float, ...]:
    try:
        values = tuple(float(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of {length} finite floats, got {value!r}.") from exc
    if len(values) != length:
        raise ValueError(f"{name} must contain {length} values, got {len(values)}: {value!r}.")
    if not all(math.isfinite(item) for item in values):
        raise ValueError(f"{name} must contain only finite values, got {value!r}.")
    return values


def _positive_finite(value, *, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be positive and finite, got {value!r}.")
    return numeric


def _non_negative_finite(value, *, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be finite and non-negative, got {value!r}.")
    return numeric


def _validate_viewpoint_pose_tuple(value, *, index: int) -> tuple[float, float, float, float, float, float, float]:
    pose = _as_float_tuple(value, name=f"viewpoint_poses[{index}]", length=7)
    quat_norm = math.sqrt(sum(item * item for item in pose[3:7]))
    if quat_norm <= 1.0e-8:
        raise ValueError(f"viewpoint_poses[{index}] quaternion must be non-zero.")
    return pose


def _observation_dim_for_num_agents(num_agents: int) -> int:
    return BASE_OBSERVATION_DIM_WITHOUT_OTHER_SCANNERS + 3 * max(num_agents - 1, 0)


def _yaw_to_quat_wxyz(yaw: float) -> tuple[float, float, float, float]:
    half_yaw = 0.5 * float(yaw)
    return (math.cos(half_yaw), 0.0, 0.0, math.sin(half_yaw))


def _robot_visual_pose_from_proxy(
    base_pos: Sequence[float],
    base_yaw: float,
    position_offset: Sequence[float],
    yaw_offset: float,
) -> tuple[tuple[float, float, float], float]:
    base_x, base_y, base_z = _as_float_tuple(base_pos, name="robot_visual_base_pos", length=3)
    offset_x, offset_y, offset_z = _as_float_tuple(
        position_offset,
        name="robot_visual_position_offset",
        length=3,
    )
    yaw = float(base_yaw)
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    visual_pos = (
        base_x + cos_yaw * offset_x - sin_yaw * offset_y,
        base_y + sin_yaw * offset_x + cos_yaw * offset_y,
        base_z + offset_z,
    )
    return visual_pos, yaw + float(yaw_offset)


def _quat_wxyz_to_yaw(quat: Sequence[float], *, name: str) -> float:
    qw, qx, qy, qz = _as_float_tuple(quat, name=name, length=4)
    quat_norm = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    if quat_norm <= 1.0e-8:
        raise ValueError(f"{name} quaternion must be non-zero.")
    qw, qx, qy, qz = (qw / quat_norm, qx / quat_norm, qy / quat_norm, qz / quat_norm)
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


def _safe_usd_prim_name(value: str) -> str:
    safe = "".join(char if char.isalnum() or char == "_" else "_" for char in str(value).strip())
    return safe or "robot"


def _asset_search_roots() -> tuple[Path, ...]:
    module_dir = Path(__file__).resolve().parent
    return (module_dir, *module_dir.parents)


def _resolve_optional_existing_asset_path(path_value: str | Path | None) -> str | None:
    if not path_value:
        return None
    raw_path = Path(path_value).expanduser()
    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [Path.cwd() / raw_path]
        candidates.extend(root / raw_path for root in _asset_search_roots())

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_file():
            return str(resolved)
    return None


def _augment_visual_asset_diagnostics(diagnostics: dict[str, object]) -> dict[str, object]:
    enabled_names = list(diagnostics.get("enabled_robot_names", []))
    visual_usd_paths = dict(diagnostics.get("visual_usd_path_by_robot", {}) or {})
    visual_mesh_paths = dict(diagnostics.get("visual_mesh_path_by_robot", {}) or {})
    visual_mesh_scales = dict(diagnostics.get("visual_mesh_scale_by_robot", {}) or {})
    visual_mesh_position_offsets = dict(diagnostics.get("visual_mesh_position_offset_by_robot", {}) or {})
    visual_mesh_yaw_offsets = dict(diagnostics.get("visual_mesh_yaw_offset_by_robot", {}) or {})
    visual_mesh_align_bottom = dict(
        diagnostics.get("visual_mesh_align_bottom_to_proxy_z_by_robot", {}) or {}
    )

    visual_usd_resolved = {}
    visual_usd_exists = {}
    visual_usd_spawned = {}
    visual_mesh_resolved = {}
    visual_mesh_exists = {}
    visual_mesh_spawned = {}
    visual_mesh_prim_paths = {}
    visual_follow_enabled = {}
    visual_mesh_error = {}
    visual_mesh_local_min_z = {}
    visual_mesh_auto_bottom_offset_z = {}
    visual_mesh_effective_position_offsets = {}

    for name in enabled_names:
        usd_path = visual_usd_paths.get(name)
        usd_resolved = _resolve_optional_existing_asset_path(usd_path)
        visual_usd_resolved[name] = usd_resolved
        visual_usd_exists[name] = usd_resolved is not None
        visual_usd_spawned[name] = False

        mesh_path = visual_mesh_paths.get(name)
        mesh_resolved = _resolve_optional_existing_asset_path(mesh_path)
        mesh_scale_value = visual_mesh_scales.get(name)
        mesh_position_offset_value = visual_mesh_position_offsets.get(name)
        mesh_yaw_offset_value = visual_mesh_yaw_offsets.get(name)
        mesh_scale = _as_float_tuple(
            mesh_scale_value if mesh_scale_value is not None else ROBOT_VISUAL_MESH_SCALE,
            name=f"visual_mesh_scale_by_robot[{name}]",
            length=3,
        )
        mesh_position_offset = _as_float_tuple(
            mesh_position_offset_value
            if mesh_position_offset_value is not None
            else ROBOT_VISUAL_MESH_POSITION_OFFSET,
            name=f"visual_mesh_position_offset_by_robot[{name}]",
            length=3,
        )
        mesh_yaw_offset = (
            float(mesh_yaw_offset_value)
            if mesh_yaw_offset_value is not None
            else ROBOT_VISUAL_MESH_YAW_OFFSET
        )
        if not math.isfinite(mesh_yaw_offset):
            raise ValueError(f"visual_mesh_yaw_offset_by_robot[{name}] must be finite.")
        visual_mesh_scales[name] = list(mesh_scale)
        visual_mesh_position_offsets[name] = list(mesh_position_offset)
        visual_mesh_yaw_offsets[name] = mesh_yaw_offset
        visual_mesh_align_bottom[name] = bool(visual_mesh_align_bottom.get(name, False))
        visual_mesh_local_min_z[name] = None
        visual_mesh_auto_bottom_offset_z[name] = None
        visual_mesh_effective_position_offsets[name] = list(mesh_position_offset)
        visual_mesh_resolved[name] = mesh_resolved
        visual_mesh_exists[name] = mesh_resolved is not None
        visual_mesh_spawned[name] = False
        visual_mesh_prim_paths[name] = None
        visual_follow_enabled[name] = False
        visual_mesh_error[name] = None

    diagnostics["visual_usd_resolved_path_by_robot"] = visual_usd_resolved
    diagnostics["visual_usd_exists_by_robot"] = visual_usd_exists
    diagnostics["visual_usd_spawned_by_robot"] = visual_usd_spawned
    diagnostics["visual_mesh_scale_by_robot"] = visual_mesh_scales
    diagnostics["visual_mesh_position_offset_by_robot"] = visual_mesh_position_offsets
    diagnostics["visual_mesh_yaw_offset_by_robot"] = visual_mesh_yaw_offsets
    diagnostics["visual_mesh_align_bottom_to_proxy_z_by_robot"] = visual_mesh_align_bottom
    diagnostics["visual_mesh_local_min_z_by_robot"] = visual_mesh_local_min_z
    diagnostics["visual_mesh_auto_bottom_offset_z_by_robot"] = visual_mesh_auto_bottom_offset_z
    diagnostics["visual_mesh_effective_position_offset_by_robot"] = visual_mesh_effective_position_offsets
    diagnostics["visual_mesh_resolved_path_by_robot"] = visual_mesh_resolved
    diagnostics["visual_mesh_exists_by_robot"] = visual_mesh_exists
    diagnostics["visual_mesh_spawned_by_robot"] = visual_mesh_spawned
    diagnostics["visual_mesh_prim_path_by_robot"] = visual_mesh_prim_paths
    diagnostics["visual_follow_enabled_by_robot"] = visual_follow_enabled
    diagnostics["visual_mesh_error_by_robot"] = visual_mesh_error
    return diagnostics


def _apply_robot_visual_mode_diagnostics(
    cfg: ScanMobileManipulatorEnvCfg,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    enabled_names = list(diagnostics.get("enabled_robot_names", []))
    robot_visual_mode = str(getattr(cfg, "robot_visual_mode", "mesh")).strip().lower()
    mesh_enabled = robot_visual_mode == "mesh"
    diagnostics["robot_visual_mode"] = robot_visual_mode
    diagnostics["robot_visual_mesh_enabled"] = mesh_enabled
    diagnostics["visual_mesh_enabled_by_robot"] = {name: mesh_enabled for name in enabled_names}
    return diagnostics


def _validate_visual_mode(value: object, *, field_name: str, allowed_modes: Sequence[str]) -> str:
    mode = str(value if value is not None else "").strip().lower()
    if mode not in allowed_modes:
        allowed = ", ".join(allowed_modes)
        raise ValueError(f"{field_name} must be one of {{{allowed}}}, got {value!r}.")
    return mode


def _prepare_visualization_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    cfg.robot_visual_mode = _validate_visual_mode(
        getattr(cfg, "robot_visual_mode", "mesh"),
        field_name="robot_visual_mode",
        allowed_modes=ROBOT_VISUAL_MODES,
    )
    cfg.component_visual_mode = _validate_visual_mode(
        getattr(cfg, "component_visual_mode", "mesh"),
        field_name="component_visual_mode",
        allowed_modes=COMPONENT_VISUAL_MODES,
    )
    if cfg.component_visual_mode != "mesh":
        cfg.component_mesh_visible = False
        if not bool(getattr(cfg, "component_proxy_auto_from_mesh", False)):
            cfg.component_mesh_path = None
    if cfg.component_visual_mode == "none":
        cfg.component_proxy_visual_visible = False
    cfg.gui_camera_enabled = bool(getattr(cfg, "gui_camera_enabled", True))
    cfg.gui_camera_eye = _as_float_tuple(
        getattr(cfg, "gui_camera_eye", (0.0, -7.5, 3.2)),
        name="gui_camera_eye",
        length=3,
    )
    cfg.gui_camera_target = _as_float_tuple(
        getattr(cfg, "gui_camera_target", (0.0, 0.0, 1.1)),
        name="gui_camera_target",
        length=3,
    )
    if cfg.gui_camera_enabled:
        cfg.viewer.eye = cfg.gui_camera_eye
        cfg.viewer.lookat = cfg.gui_camera_target
    cfg.ground_grid_enabled = bool(getattr(cfg, "ground_grid_enabled", False))
    cfg.ground_grid_half_extent = _positive_finite(
        getattr(cfg, "ground_grid_half_extent", 6.0),
        name="ground_grid_half_extent",
    )
    cfg.ground_grid_spacing = _positive_finite(
        getattr(cfg, "ground_grid_spacing", 0.5),
        name="ground_grid_spacing",
    )
    cfg.ground_grid_z = float(getattr(cfg, "ground_grid_z", 0.01))
    if not math.isfinite(cfg.ground_grid_z):
        raise ValueError(f"ground_grid_z must be finite, got {cfg.ground_grid_z!r}.")
    cfg.ground_grid_line_width = _positive_finite(
        getattr(cfg, "ground_grid_line_width", 0.008),
        name="ground_grid_line_width",
    )


def _legacy_robot_config_from_cfg(cfg: ScanMobileManipulatorEnvCfg) -> RobotConfig:
    robots = []
    for index, agent_name in enumerate(cfg.possible_agents):
        pose = _as_float_tuple(cfg.base_start_poses[index], name=f"base_start_poses[{index}]", length=4)
        quat = _yaw_to_quat_wxyz(pose[3])
        profile = LEGACY_CAPABILITY_PROFILES[index] if index < len(LEGACY_CAPABILITY_PROFILES) else "mobile_scanner_a"
        robots.append(
            RobotSpec(
                name=str(agent_name),
                enabled=True,
                model_type="task_space_proxy",
                initial_pose_world=(pose[0], pose[1], pose[2], *quat),
                capability_profile=profile,
                speed_weight=1.0,
                cost_weight=1.0,
                source_index=index,
            )
        )
    robots_tuple = tuple(robots)
    return RobotConfig(
        config_path=LEGACY_ROBOT_CONFIG_PATH,
        robots=robots_tuple,
        enabled_robots=robots_tuple,
        agent_id_by_name={robot.name: index for index, robot in enumerate(robots_tuple)},
    )


def _profile_values(robot: RobotSpec, profiles: Mapping[str, CapabilityProfile]) -> dict[str, object]:
    profile = profiles.get(robot.capability_profile)
    if profile is None:
        known = ", ".join(profiles.keys())
        raise ValueError(
            f"Unsupported capability_profile={robot.capability_profile!r} for robot {robot.name!r}. "
            f"Known YAML capability profiles: {known}."
        )
    return profile.to_dict()


def _apply_capability_profiles_to_cfg(
    cfg: ScanMobileManipulatorEnvCfg,
    enabled_robots: Sequence[RobotSpec],
    profile_values: Sequence[Mapping[str, object]],
) -> None:
    cfg.scanner_start_offsets = tuple(profile["scanner_start_offset"] for profile in profile_values)
    cfg.arm_reach = tuple(profile["arm_reach"] for profile in profile_values)
    cfg.scanner_min_range = tuple(profile["scanner_min_range"] for profile in profile_values)
    cfg.scanner_max_range = tuple(profile["scanner_max_range"] for profile in profile_values)
    cfg.scanner_fov_deg = tuple(profile["scanner_fov_deg"] for profile in profile_values)
    cfg.scan_pos_tolerance = tuple(profile["scan_pos_tolerance"] for profile in profile_values)
    cfg.scan_rot_tolerance = tuple(profile["scan_rot_tolerance"] for profile in profile_values)
    cfg.max_base_xy_step = tuple(profile["max_base_xy_step"] for profile in profile_values)
    cfg.max_base_yaw_step = tuple(profile["max_base_yaw_step"] for profile in profile_values)
    cfg.max_ee_xyz_step = tuple(profile["max_ee_xyz_step"] for profile in profile_values)
    cfg.max_ee_rpy_step = tuple(profile["max_ee_rpy_step"] for profile in profile_values)


def _capability_diagnostics(
    capability_config: CapabilityConfig,
    enabled_robots: Sequence[RobotSpec],
    profile_values: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    diagnostics = capability_config.to_diagnostics()
    diagnostics["capability_profile_by_robot"] = {
        robot.name: robot.capability_profile for robot in enabled_robots
    }
    diagnostics["capability_profiles_by_robot"] = {
        robot.name: dict(profile) for robot, profile in zip(enabled_robots, profile_values, strict=True)
    }
    return diagnostics


def _validate_agent_config_shapes(cfg: ScanMobileManipulatorEnvCfg) -> None:
    agents = tuple(str(agent) for agent in cfg.possible_agents)
    if not agents:
        raise ValueError("possible_agents must contain at least one enabled robot.")
    expected_agent_keys = set(agents)
    for field_name in ("action_spaces", "observation_spaces", "state_spaces"):
        mapping = getattr(cfg, field_name)
        if set(mapping.keys()) != expected_agent_keys:
            raise ValueError(
                f"{field_name} keys must match possible_agents={list(agents)}, got {list(mapping.keys())}."
            )

    per_agent_fields = (
        ("base_start_poses", 4),
        ("scanner_start_offsets", 3),
    )
    for field_name, tuple_length in per_agent_fields:
        values = tuple(getattr(cfg, field_name))
        if len(values) != len(agents):
            raise ValueError(f"{field_name} must have {len(agents)} entries, got {len(values)}.")
        for index, value in enumerate(values):
            _as_float_tuple(value, name=f"{field_name}[{index}]", length=tuple_length)

    scalar_fields = (
        "arm_reach",
        "scanner_min_range",
        "scanner_max_range",
        "scanner_fov_deg",
        "scan_pos_tolerance",
        "scan_rot_tolerance",
        "max_base_xy_step",
        "max_base_yaw_step",
        "max_ee_xyz_step",
        "max_ee_rpy_step",
    )
    for field_name in scalar_fields:
        values = _as_float_tuple(getattr(cfg, field_name), name=field_name, length=len(agents))
        if field_name != "scan_rot_tolerance" and any(value <= 0.0 for value in values):
            raise ValueError(f"{field_name} values must be positive, got {values!r}.")


def _prepare_robot_config_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    module_dir = Path(__file__).resolve().parent
    capability_config_path = getattr(cfg, "capability_config_path", None)
    capability_config = load_capability_profiles(capability_config_path, base_dir=module_dir)

    robot_config_path = getattr(cfg, "robot_config_path", None)
    if robot_config_path:
        robot_config = load_robot_config(robot_config_path, base_dir=module_dir)
        enabled_robots = robot_config.enabled_robots
        if not enabled_robots:
            raise ValueError(f"robot config has no enabled robots: {robot_config.config_path}")

        agents = [robot.name for robot in enabled_robots]
        cfg.possible_agents = agents
        cfg.action_spaces = {agent: ROBOT_ACTION_DIM for agent in agents}
        observation_dim = _observation_dim_for_num_agents(len(agents))
        cfg.observation_spaces = {agent: observation_dim for agent in agents}
        cfg.state_spaces = {agent: 0 for agent in agents}
        cfg.base_start_poses = tuple(
            (
                robot.initial_pose_world[0],
                robot.initial_pose_world[1],
                robot.initial_pose_world[2],
                _quat_wxyz_to_yaw(robot.initial_pose_world[3:7], name=f"{robot.name}.initial_pose_world[3:7]"),
            )
            for robot in enabled_robots
        )
        cfg.robot_config_path = str(robot_config.config_path)
    else:
        robot_config = _legacy_robot_config_from_cfg(cfg)
        enabled_robots = robot_config.enabled_robots

    profile_values = [_profile_values(robot, capability_config.profiles) for robot in enabled_robots]
    _apply_capability_profiles_to_cfg(cfg, enabled_robots, profile_values)

    cfg.capability_config_path = str(capability_config.config_path)
    cfg.capability_config_diagnostics = _capability_diagnostics(
        capability_config,
        enabled_robots,
        profile_values,
    )
    cfg.robot_config_diagnostics = _apply_robot_visual_mode_diagnostics(
        cfg,
        _augment_visual_asset_diagnostics(robot_config.to_diagnostics()),
    )
    _validate_agent_config_shapes(cfg)


def _prepare_component_mesh_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    mesh_path = getattr(cfg, "component_mesh_path", None)
    cfg.component_mesh_format = validate_mesh_format(getattr(cfg, "component_mesh_format", "obj"))
    cfg.component_mesh_unit = validate_mesh_unit(getattr(cfg, "component_mesh_unit", "mm"))
    cfg.component_mesh_scale = _as_float_tuple(
        getattr(cfg, "component_mesh_scale", (0.001, 0.001, 0.001)),
        name="component_mesh_scale",
        length=3,
    )
    if any(value <= 0.0 for value in cfg.component_mesh_scale):
        raise ValueError(f"component_mesh_scale must contain positive values, got {cfg.component_mesh_scale!r}.")
    cfg.component_mesh_position = _as_float_tuple(
        getattr(cfg, "component_mesh_position", (0.0, 0.0, 0.0)),
        name="component_mesh_position",
        length=3,
    )
    cfg.component_mesh_orientation = _as_float_tuple(
        getattr(cfg, "component_mesh_orientation", (1.0, 0.0, 0.0, 0.0)),
        name="component_mesh_orientation",
        length=4,
    )
    cfg.component_mesh_orientation_format = validate_orientation_format(
        getattr(cfg, "component_mesh_orientation_format", "qwxyz")
    )
    cfg.component_mesh_visible = bool(getattr(cfg, "component_mesh_visible", True))
    cfg.component_mesh_align_base_center_to_world_origin = bool(
        getattr(cfg, "component_mesh_align_base_center_to_world_origin", False)
    )
    cfg.component_proxy_auto_from_mesh = bool(getattr(cfg, "component_proxy_auto_from_mesh", False))
    cfg.component_proxy_padding = float(getattr(cfg, "component_proxy_padding", 0.0))
    cfg.component_proxy_visual_visible = bool(getattr(cfg, "component_proxy_visual_visible", True))
    if not math.isfinite(cfg.component_proxy_padding) or cfg.component_proxy_padding < 0.0:
        raise ValueError(f"component_proxy_padding must be finite and non-negative, got {cfg.component_proxy_padding!r}.")

    cfg.component_mesh_resolved_path = None
    cfg.component_mesh_base_center_before_translation = None
    cfg.component_mesh_auto_translation_if_used = None
    cfg.component_mesh_raw_bounds_obj_units_min = None
    cfg.component_mesh_raw_bounds_obj_units_max = None
    cfg.component_mesh_scaled_local_bounds_m_min = None
    cfg.component_mesh_scaled_local_bounds_m_max = None
    cfg.component_mesh_world_bounds_m_min = None
    cfg.component_mesh_world_bounds_m_max = None
    cfg.component_mesh_auto_proxy_center = None
    cfg.component_mesh_auto_proxy_half_extents = None

    if not mesh_path:
        if cfg.component_proxy_auto_from_mesh:
            raise ValueError("component_proxy_auto_from_mesh=True requires component_mesh_path.")
        if cfg.component_mesh_align_base_center_to_world_origin:
            raise ValueError(
                "component_mesh_align_base_center_to_world_origin=True requires component_mesh_path."
            )
        return

    module_dir = Path(__file__).resolve().parent
    if cfg.component_mesh_align_base_center_to_world_origin:
        default_position = (0.0, 0.0, 0.0)
        if any(abs(cfg.component_mesh_position[index] - default_position[index]) > 1.0e-12 for index in range(3)):
            raise ValueError(
                "component_mesh_align_base_center_to_world_origin=True cannot be combined with a non-zero "
                "component_mesh_position. Use one world-origin convention at a time."
            )
        alignment = compute_base_center_alignment_translation(
            mesh_path=mesh_path,
            mesh_format=cfg.component_mesh_format,
            mesh_unit=cfg.component_mesh_unit,
            mesh_scale=cfg.component_mesh_scale,
            mesh_orientation=cfg.component_mesh_orientation,
            mesh_orientation_format=cfg.component_mesh_orientation_format,
            search_roots=(module_dir,),
        )
        cfg.component_mesh_position = alignment.auto_translation
        cfg.component_mesh_base_center_before_translation = alignment.base_center_before_translation
        cfg.component_mesh_auto_translation_if_used = alignment.auto_translation

    bounds = compute_component_mesh_bounds(
        mesh_path=mesh_path,
        mesh_format=cfg.component_mesh_format,
        mesh_unit=cfg.component_mesh_unit,
        mesh_scale=cfg.component_mesh_scale,
        mesh_position=cfg.component_mesh_position,
        mesh_orientation=cfg.component_mesh_orientation,
        mesh_orientation_format=cfg.component_mesh_orientation_format,
        component_proxy_padding=cfg.component_proxy_padding,
        search_roots=(module_dir,),
    )
    cfg.component_mesh_path = bounds.mesh_path
    cfg.component_mesh_resolved_path = bounds.mesh_path
    cfg.component_mesh_scale = bounds.mesh_scale
    cfg.component_mesh_position = bounds.mesh_position
    cfg.component_mesh_orientation = bounds.mesh_orientation
    cfg.component_mesh_raw_bounds_obj_units_min = bounds.raw_bounds_obj_units_min
    cfg.component_mesh_raw_bounds_obj_units_max = bounds.raw_bounds_obj_units_max
    cfg.component_mesh_scaled_local_bounds_m_min = bounds.scaled_local_bounds_m_min
    cfg.component_mesh_scaled_local_bounds_m_max = bounds.scaled_local_bounds_m_max
    cfg.component_mesh_world_bounds_m_min = bounds.world_bounds_m_min
    cfg.component_mesh_world_bounds_m_max = bounds.world_bounds_m_max
    cfg.component_mesh_auto_proxy_center = bounds.auto_component_proxy_center
    cfg.component_mesh_auto_proxy_half_extents = bounds.auto_component_proxy_half_extents

    if cfg.component_proxy_auto_from_mesh:
        cfg.component_proxy_center = bounds.auto_component_proxy_center
        cfg.component_proxy_half_extents = bounds.auto_component_proxy_half_extents


def _prepare_component_proxy_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    proxy_type = str(getattr(cfg, "component_proxy_type", "bbox")).strip().lower()
    if proxy_type != "bbox":
        raise ValueError(f"Unsupported component_proxy_type={proxy_type!r}; only 'bbox' is supported in Stage 1.")

    center = _as_float_tuple(cfg.component_proxy_center, name="component_proxy_center", length=3)
    half_extents = _as_float_tuple(cfg.component_proxy_half_extents, name="component_proxy_half_extents", length=3)
    if any(value <= 0.0 for value in half_extents):
        raise ValueError(f"component_proxy_half_extents must all be positive, got {half_extents!r}.")

    cfg.component_proxy_type = proxy_type
    cfg.component_proxy_center = center
    cfg.component_proxy_half_extents = half_extents
    cfg.component_center = center
    cfg.component_half_extents = half_extents


def _prepare_obstacle_diagnostics_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    enabled = bool(getattr(cfg, "obstacle_diagnostics_enabled", False))
    cfg.obstacle_diagnostics_enabled = enabled
    cfg.component_obstacle_footprint = None
    cfg.component_obstacle_footprint_diagnostics = None

    if not enabled:
        cfg.obstacle_diagnostics_mode = "disabled"
        cfg.obstacle_source = None
        return

    mode = str(getattr(cfg, "obstacle_diagnostics_mode", "diagnostics_only")).strip().lower()
    if mode != "diagnostics_only":
        raise ValueError(
            f"Unsupported obstacle_diagnostics_mode={mode!r}; only 'diagnostics_only' is supported."
        )
    source = str(getattr(cfg, "obstacle_source", "component_mesh_footprint")).strip().lower()
    if source != "component_mesh_footprint":
        raise ValueError(
            f"Unsupported obstacle_source={source!r}; only 'component_mesh_footprint' is supported."
        )

    cfg.obstacle_diagnostics_mode = mode
    cfg.obstacle_source = source
    cfg.obstacle_footprint_resolution = _positive_finite(
        getattr(cfg, "obstacle_footprint_resolution", 0.10),
        name="obstacle_footprint_resolution",
    )
    cfg.obstacle_footprint_inflation_radius = _non_negative_finite(
        getattr(cfg, "obstacle_footprint_inflation_radius", 0.30),
        name="obstacle_footprint_inflation_radius",
    )
    cfg.obstacle_line_sample_step = _positive_finite(
        getattr(cfg, "obstacle_line_sample_step", 0.10),
        name="obstacle_line_sample_step",
    )
    cfg.obstacle_blocked_path_penalty = _non_negative_finite(
        getattr(cfg, "obstacle_blocked_path_penalty", 100.0),
        name="obstacle_blocked_path_penalty",
    )
    if not getattr(cfg, "component_mesh_path", None):
        raise ValueError(
            "obstacle_source=component_mesh_footprint requires component_mesh_path; "
            "bbox proxies are intentionally not used as hard obstacle blockers."
        )

    module_dir = Path(__file__).resolve().parent
    footprint = build_component_obstacle_footprint(
        mesh_path=cfg.component_mesh_path,
        mesh_scale=cfg.component_mesh_scale,
        mesh_position=cfg.component_mesh_position,
        mesh_orientation=cfg.component_mesh_orientation,
        mesh_orientation_format=cfg.component_mesh_orientation_format,
        footprint_resolution=cfg.obstacle_footprint_resolution,
        footprint_inflation_radius=cfg.obstacle_footprint_inflation_radius,
        line_sample_step=cfg.obstacle_line_sample_step,
        search_roots=(module_dir,),
    )
    cfg.component_obstacle_footprint = footprint
    cfg.component_obstacle_footprint_diagnostics = footprint.to_diagnostics()


def _prepare_obstacle_debug_visualization_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    enabled = bool(getattr(cfg, "obstacle_debug_visualization_enabled", False))
    cfg.obstacle_debug_visualization_enabled = enabled
    cfg.obstacle_debug_visualization_draw_in_headless = bool(
        getattr(cfg, "obstacle_debug_visualization_draw_in_headless", False)
    )
    line_source = str(
        getattr(cfg, "obstacle_debug_visualization_line_source", "mesh_footprint_intersections")
    ).strip().lower()
    if line_source != "mesh_footprint_intersections":
        raise ValueError(
            f"Unsupported obstacle_debug_visualization_line_source={line_source!r}; "
            "only 'mesh_footprint_intersections' is supported."
        )
    cfg.obstacle_debug_visualization_line_source = line_source

    for attr in (
        "obstacle_debug_visualization_max_lines_per_robot",
        "obstacle_debug_visualization_max_total_lines",
    ):
        value = int(getattr(cfg, attr, 0))
        if value < 0:
            raise ValueError(f"{attr} must be non-negative, got {value!r}.")
        setattr(cfg, attr, value)
    cfg.obstacle_debug_visualization_prefer_shortest_blocked_pairs = bool(
        getattr(cfg, "obstacle_debug_visualization_prefer_shortest_blocked_pairs", True)
    )
    line_z_mode = str(getattr(cfg, "obstacle_debug_visualization_line_z_mode", "max_endpoint")).strip().lower()
    if line_z_mode not in ("fixed", "max_endpoint"):
        raise ValueError(
            f"Unsupported obstacle_debug_visualization_line_z_mode={line_z_mode!r}; "
            "expected 'fixed' or 'max_endpoint'."
        )
    cfg.obstacle_debug_visualization_line_z_mode = line_z_mode
    cfg.obstacle_debug_visualization_line_z_value = float(
        getattr(cfg, "obstacle_debug_visualization_line_z_value", 0.20)
    )
    if not math.isfinite(cfg.obstacle_debug_visualization_line_z_value):
        raise ValueError("obstacle_debug_visualization_line_z_value must be finite.")
    cfg.obstacle_debug_visualization_line_z_offset = _non_negative_finite(
        getattr(cfg, "obstacle_debug_visualization_line_z_offset", 0.05),
        name="obstacle_debug_visualization_line_z_offset",
    )
    cfg.obstacle_debug_visualization_line_width = _positive_finite(
        getattr(cfg, "obstacle_debug_visualization_line_width", 0.03),
        name="obstacle_debug_visualization_line_width",
    )


def _prepare_viewpoint_cfg(cfg: ScanMobileManipulatorEnvCfg) -> None:
    csv_path = getattr(cfg, "viewpoint_csv_path", None)
    if csv_path:
        csv_format = str(getattr(cfg, "viewpoint_csv_format", VIEWPOINT_CSV_FORMAT)).strip()
        if csv_format != VIEWPOINT_CSV_FORMAT:
            raise ValueError(
                f"Unsupported viewpoint_csv_format={csv_format!r}; only {VIEWPOINT_CSV_FORMAT!r} is supported."
            )
        module_dir = Path(__file__).resolve().parent
        load_result = load_fixed_viewpoint_csv(csv_path, search_roots=(module_dir,))
        cfg.viewpoint_poses = load_result.poses
        cfg.viewpoint_ids = load_result.ids
        cfg.viewpoint_source = f"csv:{load_result.path}"
        return

    poses = tuple(
        _validate_viewpoint_pose_tuple(pose, index=index) for index, pose in enumerate(cfg.viewpoint_poses)
    )
    if not poses:
        raise ValueError("viewpoint_poses must contain at least one viewpoint.")
    cfg.viewpoint_poses = poses
    cfg.viewpoint_ids = tuple(range(len(poses)))
    cfg.viewpoint_source = "builtin_fixed_12"


class ScanMobileManipulatorEnv(DirectMARLEnv):
    """DirectMARLEnv implementation for the high-level scan assignment skeleton."""

    cfg: ScanMobileManipulatorEnvCfg

    def __init__(self, cfg: ScanMobileManipulatorEnvCfg, render_mode: str | None = None, **kwargs):
        _prepare_visualization_cfg(cfg)
        _prepare_robot_config_cfg(cfg)
        _prepare_component_mesh_cfg(cfg)
        _prepare_component_proxy_cfg(cfg)
        _prepare_obstacle_diagnostics_cfg(cfg)
        _prepare_obstacle_debug_visualization_cfg(cfg)
        _prepare_viewpoint_cfg(cfg)
        super().__init__(cfg, render_mode, **kwargs)

        self.num_agents_cfg = len(self.cfg.possible_agents)
        self.robot_config_diagnostics = self.get_robot_config_diagnostics()
        self.capability_diagnostics = self.get_capability_diagnostics()
        self.num_viewpoints = len(self.cfg.viewpoint_poses)
        self.viewpoint_ids = tuple(int(value) for value in self.cfg.viewpoint_ids)
        self.viewpoint_source = str(self.cfg.viewpoint_source)
        self.noop_action_id = self.num_viewpoints
        self._apply_fixed_12_mvp_override = self.viewpoint_source == "builtin_fixed_12" and self.num_viewpoints == 12
        self.agent_index = {agent: index for index, agent in enumerate(self.cfg.possible_agents)}

        # Static task data is copied to `self.device` once. Later steps stay in torch tensors and avoid CPU/numpy
        # round-trips, which keeps the assignment path compatible with vectorized GPU environments.
        self.viewpoint_poses = torch.tensor(self.cfg.viewpoint_poses, dtype=torch.float32, device=self.device)
        self.viewpoint_pos_local = self.viewpoint_poses[:, :3]
        self.viewpoint_quat = normalize(self.viewpoint_poses[:, 3:7])
        self.component_center = torch.tensor(self.cfg.component_proxy_center, dtype=torch.float32, device=self.device)
        self.component_half_extents = torch.tensor(
            self.cfg.component_proxy_half_extents, dtype=torch.float32, device=self.device
        )

        self.base_start_poses = torch.tensor(self.cfg.base_start_poses, dtype=torch.float32, device=self.device)
        self.scanner_start_offsets = torch.tensor(
            self.cfg.scanner_start_offsets, dtype=torch.float32, device=self.device
        )
        self.arm_reach = torch.tensor(self.cfg.arm_reach, dtype=torch.float32, device=self.device)
        self.scanner_min_range = torch.tensor(self.cfg.scanner_min_range, dtype=torch.float32, device=self.device)
        self.scanner_max_range = torch.tensor(self.cfg.scanner_max_range, dtype=torch.float32, device=self.device)
        self.scanner_fov_deg = torch.tensor(self.cfg.scanner_fov_deg, dtype=torch.float32, device=self.device)
        self.scanner_fov_cos = torch.cos(0.5 * torch.deg2rad(self.scanner_fov_deg))
        self.scan_pos_tolerance = torch.tensor(self.cfg.scan_pos_tolerance, dtype=torch.float32, device=self.device)
        self.scan_rot_tolerance = torch.tensor(self.cfg.scan_rot_tolerance, dtype=torch.float32, device=self.device)
        self.max_base_xy_step = torch.tensor(self.cfg.max_base_xy_step, dtype=torch.float32, device=self.device)
        self.max_base_yaw_step = torch.tensor(self.cfg.max_base_yaw_step, dtype=torch.float32, device=self.device)
        self.max_ee_xyz_step = torch.tensor(self.cfg.max_ee_xyz_step, dtype=torch.float32, device=self.device)
        self.max_ee_rpy_step = torch.tensor(self.cfg.max_ee_rpy_step, dtype=torch.float32, device=self.device)

        self._build_static_feasibility()

        # High-level task-space state. These buffers are the current source of truth for robot and scanner pose until
        # real robot articulation state is wired in.
        self.base_pos = torch.zeros(self.num_envs, self.num_agents_cfg, 3, device=self.device)
        self.base_yaw = torch.zeros(self.num_envs, self.num_agents_cfg, device=self.device)
        self.scanner_pos = torch.zeros(self.num_envs, self.num_agents_cfg, 3, device=self.device)
        self.scanner_quat = torch.zeros(self.num_envs, self.num_agents_cfg, 4, device=self.device)
        self.viewpoints_covered = torch.zeros(self.num_envs, self.num_viewpoints, dtype=torch.bool, device=self.device)
        self.dwell_counter = torch.zeros(
            self.num_envs, self.num_agents_cfg, self.num_viewpoints, dtype=torch.long, device=self.device
        )
        self.actions = {
            agent: torch.zeros(self.num_envs, self.cfg.action_spaces[agent], device=self.device)
            for agent in self.cfg.possible_agents
        }
        self.previous_actions = {agent: tensor.clone() for agent, tensor in self.actions.items()}

        # Reward bookkeeping is updated in `_update_scan_progress()` before `_get_rewards()` distributes per-agent
        # rewards. Keeping these as buffers avoids recalculating scan events multiple times in one step.
        self.last_global_coverage_gain = torch.zeros(self.num_envs, device=self.device)
        self.last_own_coverage_gain = torch.zeros(self.num_envs, self.num_agents_cfg, device=self.device)
        self.last_duplicate_scans = torch.zeros(self.num_envs, self.num_agents_cfg, device=self.device)
        self.last_reach_violation = torch.zeros(self.num_envs, self.num_agents_cfg, device=self.device)
        self._usd_debug_dirty = True
        self._obstacle_debug_line_prim_paths = set()
        self._obstacle_debug_visualization_last_diagnostics = self._obstacle_debug_visualization_base_diagnostics(
            drawn_line_count=0,
            skipped_reason="not_drawn_yet",
            pairs_sample=[],
            line_prim_paths_sample=[],
        )
        self._reset_diagnostics_printed = False
        self._log_static_configuration()

    def _mesh_footprint_obstacle_fields(self, cost_matrix: torch.Tensor, viewpoint_pos: torch.Tensor) -> dict:
        enabled = bool(getattr(self.cfg, "obstacle_diagnostics_enabled", False))
        fields: dict[str, object] = {
            "obstacle_diagnostics_enabled": enabled,
            "obstacle_diagnostics_mode": getattr(self.cfg, "obstacle_diagnostics_mode", "disabled"),
            "obstacle_source": getattr(self.cfg, "obstacle_source", None),
            "component_obstacle_footprint_diagnostics": self.get_component_obstacle_footprint_diagnostics(),
        }
        if not enabled:
            return fields

        footprint: ComponentObstacleFootprint | None = getattr(self.cfg, "component_obstacle_footprint", None)
        if footprint is None:
            raise RuntimeError("obstacle diagnostics are enabled but no component obstacle footprint was built.")

        intersection_mask = torch.zeros_like(cost_matrix, dtype=torch.bool)
        base_xy = self.base_pos[:, :, :2].detach().cpu().tolist()
        viewpoint_xy = viewpoint_pos[:, :, :2].detach().cpu().tolist()
        for env_id in range(self.num_envs):
            for agent_id in range(self.num_agents_cfg):
                start_xy = base_xy[env_id][agent_id]
                for viewpoint_index in range(self.num_viewpoints):
                    end_xy = viewpoint_xy[env_id][viewpoint_index]
                    if footprint.intersects_segment(start_xy, end_xy):
                        intersection_mask[env_id, agent_id, viewpoint_index] = True

        straight_line_cost_matrix = cost_matrix.clone()
        penalty_value = float(getattr(self.cfg, "obstacle_blocked_path_penalty", 100.0))
        mesh_footprint_penalty_matrix = torch.where(
            intersection_mask,
            torch.full_like(cost_matrix, penalty_value),
            torch.zeros_like(cost_matrix),
        )
        mesh_footprint_aware_cost_matrix = straight_line_cost_matrix + mesh_footprint_penalty_matrix
        fields.update(
            {
                "straight_line_cost_matrix": straight_line_cost_matrix,
                "mesh_footprint_intersection_mask": intersection_mask,
                "mesh_footprint_penalty_matrix": mesh_footprint_penalty_matrix,
                "mesh_footprint_aware_cost_matrix": mesh_footprint_aware_cost_matrix,
            }
        )
        return fields

    def get_assignment_problem(self) -> dict:
        """Return the high-level viewpoint assignment problem for the current state.

        The returned tensors are intentionally not detached or moved to CPU. Solvers can use them directly on the
        environment device and return a `torch.long` assignment tensor with shape [num_envs, num_agents].
        """
        viewpoint_pos = self.viewpoint_pos_local.unsqueeze(0).expand(self.num_envs, -1, -1)
        viewpoint_quat = self.viewpoint_quat.unsqueeze(0).expand(self.num_envs, -1, -1)

        # Cost is a simple scanner-to-viewpoint distance. It is only used by baseline solvers and does not affect the
        # environment dynamics by itself.
        cost_matrix = torch.norm(self.scanner_pos[:, :, None, :] - viewpoint_pos[:, None, :, :], dim=-1)

        static_geometric_feasible_mask = self.static_geometric_feasible_mask.unsqueeze(0).expand(
            self.num_envs, -1, -1
        )
        feasible_mask = self.assignment_feasible_mask_base.unsqueeze(0).expand(self.num_envs, -1, -1)
        available_mask = feasible_mask & (~self.viewpoints_covered[:, None, :])
        task_status = torch.full(
            (self.num_envs, self.num_viewpoints),
            TASK_UNASSIGNED,
            dtype=torch.long,
            device=self.device,
        )
        task_status = torch.where(
            self.viewpoints_covered,
            torch.full_like(task_status, TASK_COMPLETED),
            task_status,
        )
        robot_status = torch.full(
            (self.num_envs, self.num_agents_cfg),
            ROBOT_IDLE,
            dtype=torch.long,
            device=self.device,
        )

        problem = {
            "num_envs": self.num_envs,
            "num_agents": self.num_agents_cfg,
            "agent_names": tuple(self.cfg.possible_agents),
            "num_viewpoints": self.num_viewpoints,
            "viewpoint_ids": self.viewpoint_ids,
            "scenario_diagnostics": self.get_scenario_diagnostics(),
            "robot_config_diagnostics": self.robot_config_diagnostics,
            "robot_visual_diagnostics": self.get_robot_visual_diagnostics(),
            "capability_diagnostics": self.capability_diagnostics,
            "base_pos": self.base_pos,
            "base_yaw": self.base_yaw,
            "scanner_pos": self.scanner_pos,
            "scanner_quat": self.scanner_quat,
            "viewpoint_pos": viewpoint_pos,
            "viewpoint_quat": viewpoint_quat,
            "viewpoints_covered": self.viewpoints_covered,
            "arm_reach": self.arm_reach,
            "scanner_min_range": self.scanner_min_range,
            "scanner_max_range": self.scanner_max_range,
            "scanner_fov_deg": self.scanner_fov_deg,
            "cost_matrix": cost_matrix,
            "static_geometric_feasible_mask": static_geometric_feasible_mask,
            "feasible_mask": feasible_mask,
            "available_mask": available_mask,
            "task_status": task_status,
            "robot_status": robot_status,
            "task_status_names": dict(TASK_STATUS_NAMES),
            "robot_status_names": dict(ROBOT_STATUS_NAMES),
            "static_geometric_feasibility_rows": self.static_geometric_feasibility_rows,
            "manual_feasibility_override_rows": self.manual_feasibility_override_rows,
            "feasibility_diagnostic_rows": self.feasibility_diagnostic_rows,
        }
        problem.update(self._mesh_footprint_obstacle_fields(cost_matrix, viewpoint_pos))
        problem.update(self.get_obstacle_debug_visualization_diagnostics())
        return problem

    def get_robot_config_diagnostics(self) -> dict:
        return dict(getattr(self.cfg, "robot_config_diagnostics", {}) or {})

    def get_capability_diagnostics(self) -> dict:
        return dict(getattr(self.cfg, "capability_config_diagnostics", {}) or {})

    def get_component_obstacle_footprint_diagnostics(self) -> dict | None:
        diagnostics = getattr(self.cfg, "component_obstacle_footprint_diagnostics", None)
        return dict(diagnostics) if diagnostics else None

    def _obstacle_debug_visualization_base_diagnostics(
        self,
        *,
        drawn_line_count: int,
        skipped_reason: str | None,
        pairs_sample: list[dict],
        line_prim_paths_sample: list[str],
    ) -> dict:
        return {
            "obstacle_debug_visualization_enabled": bool(
                getattr(self.cfg, "obstacle_debug_visualization_enabled", False)
            ),
            "obstacle_debug_visualization_draw_in_headless": bool(
                getattr(self.cfg, "obstacle_debug_visualization_draw_in_headless", False)
            ),
            "obstacle_debug_visualization_line_source": getattr(
                self.cfg,
                "obstacle_debug_visualization_line_source",
                "mesh_footprint_intersections",
            ),
            "obstacle_debug_visualization_max_lines_per_robot": int(
                getattr(self.cfg, "obstacle_debug_visualization_max_lines_per_robot", 0)
            ),
            "obstacle_debug_visualization_max_total_lines": int(
                getattr(self.cfg, "obstacle_debug_visualization_max_total_lines", 0)
            ),
            "obstacle_debug_visualization_prefer_shortest_blocked_pairs": bool(
                getattr(self.cfg, "obstacle_debug_visualization_prefer_shortest_blocked_pairs", True)
            ),
            "obstacle_debug_visualization_line_z_mode": getattr(
                self.cfg,
                "obstacle_debug_visualization_line_z_mode",
                "max_endpoint",
            ),
            "obstacle_debug_visualization_line_z_value": float(
                getattr(self.cfg, "obstacle_debug_visualization_line_z_value", 0.20)
            ),
            "obstacle_debug_visualization_line_z_offset": float(
                getattr(self.cfg, "obstacle_debug_visualization_line_z_offset", 0.05)
            ),
            "obstacle_debug_visualization_line_width": float(
                getattr(self.cfg, "obstacle_debug_visualization_line_width", 0.03)
            ),
            "obstacle_debug_visualization_drawn_line_count": int(drawn_line_count),
            "obstacle_debug_visualization_skipped_reason": skipped_reason,
            "obstacle_debug_visualization_pairs_sample": pairs_sample,
            "obstacle_debug_visualization_line_prim_paths_sample": line_prim_paths_sample[:10],
        }

    def get_obstacle_debug_visualization_diagnostics(self) -> dict:
        diagnostics = getattr(self, "_obstacle_debug_visualization_last_diagnostics", None)
        if diagnostics is None:
            diagnostics = self._obstacle_debug_visualization_base_diagnostics(
                drawn_line_count=0,
                skipped_reason="not_drawn_yet",
                pairs_sample=[],
                line_prim_paths_sample=[],
            )
        return dict(diagnostics)

    def get_scenario_diagnostics(self) -> dict:
        component_mesh_enabled = bool(
            getattr(self.cfg, "component_visual_mode", "mesh") == "mesh"
            and getattr(self.cfg, "component_mesh_path", None)
            and getattr(self.cfg, "component_mesh_visible", False)
        )
        robot_visual_mesh_enabled = bool(getattr(self.cfg, "robot_visual_mode", "mesh") == "mesh")
        return {
            "scenario_config_path": getattr(self.cfg, "scenario_config_path", None),
            "scenario_name": getattr(self.cfg, "scenario_name", None),
            "scenario_type": getattr(self.cfg, "scenario_type", None),
            "robot_visual_mode": getattr(self.cfg, "robot_visual_mode", "mesh"),
            "component_visual_mode": getattr(self.cfg, "component_visual_mode", "mesh"),
            "gui_camera_enabled": bool(getattr(self.cfg, "gui_camera_enabled", True)),
            "gui_camera_eye": list(getattr(self.cfg, "gui_camera_eye", (0.0, -7.5, 3.2))),
            "gui_camera_target": list(getattr(self.cfg, "gui_camera_target", (0.0, 0.0, 1.1))),
            "viewer_eye": list(getattr(self.cfg.viewer, "eye", (7.5, 7.5, 7.5))),
            "viewer_lookat": list(getattr(self.cfg.viewer, "lookat", (0.0, 0.0, 0.0))),
            "ground_grid_enabled": bool(getattr(self.cfg, "ground_grid_enabled", False)),
            "ground_grid_half_extent": float(getattr(self.cfg, "ground_grid_half_extent", 6.0)),
            "ground_grid_spacing": float(getattr(self.cfg, "ground_grid_spacing", 0.5)),
            "ground_grid_z": float(getattr(self.cfg, "ground_grid_z", 0.01)),
            "ground_grid_line_width": float(getattr(self.cfg, "ground_grid_line_width", 0.008)),
            "robot_visual_mesh_enabled": robot_visual_mesh_enabled,
            "component_mesh_enabled": component_mesh_enabled,
            "component_proxy_type": self.cfg.component_proxy_type,
            "component_proxy_center": list(self.cfg.component_proxy_center),
            "component_proxy_half_extents": list(self.cfg.component_proxy_half_extents),
            "component_proxy_visual_visible": bool(self.cfg.component_proxy_visual_visible),
            "robot_config_path": getattr(self.cfg, "robot_config_path", None),
            "capability_config_path": getattr(self.cfg, "capability_config_path", None),
            "viewpoint_source": getattr(self, "viewpoint_source", getattr(self.cfg, "viewpoint_source", None)),
            "viewpoint_csv_path": getattr(self.cfg, "viewpoint_csv_path", None),
            "obstacle_diagnostics_enabled": bool(getattr(self.cfg, "obstacle_diagnostics_enabled", False)),
            "obstacle_diagnostics_mode": getattr(self.cfg, "obstacle_diagnostics_mode", "disabled"),
            "obstacle_source": getattr(self.cfg, "obstacle_source", None),
            "obstacle_footprint_resolution": float(getattr(self.cfg, "obstacle_footprint_resolution", 0.10)),
            "obstacle_footprint_inflation_radius": float(
                getattr(self.cfg, "obstacle_footprint_inflation_radius", 0.30)
            ),
            "obstacle_line_sample_step": float(getattr(self.cfg, "obstacle_line_sample_step", 0.10)),
            "obstacle_blocked_path_penalty": float(getattr(self.cfg, "obstacle_blocked_path_penalty", 100.0)),
            **self.get_obstacle_debug_visualization_diagnostics(),
        }

    def get_robot_visual_diagnostics(self) -> dict:
        diagnostics = self.get_robot_config_diagnostics()
        return {
            key: value
            for key, value in diagnostics.items()
            if key.startswith("visual_") or key in ("robot_visual_mode", "robot_visual_mesh_enabled")
        }

    def get_component_mesh_diagnostics(self) -> dict | None:
        if not self.cfg.component_mesh_path:
            return None
        return {
            "component_mesh_path": self.cfg.component_mesh_path,
            "component_mesh_format": self.cfg.component_mesh_format,
            "component_mesh_unit": self.cfg.component_mesh_unit,
            "component_mesh_scale": list(self.cfg.component_mesh_scale),
            "component_mesh_position": list(self.cfg.component_mesh_position),
            "component_mesh_orientation": list(self.cfg.component_mesh_orientation),
            "component_mesh_orientation_format": self.cfg.component_mesh_orientation_format,
            "component_mesh_visible": bool(self.cfg.component_mesh_visible),
            "component_mesh_align_base_center_to_world_origin": bool(
                self.cfg.component_mesh_align_base_center_to_world_origin
            ),
            "component_mesh_base_center_before_translation": (
                list(self.cfg.component_mesh_base_center_before_translation)
                if self.cfg.component_mesh_base_center_before_translation is not None
                else None
            ),
            "component_mesh_auto_translation_if_used": (
                list(self.cfg.component_mesh_auto_translation_if_used)
                if self.cfg.component_mesh_auto_translation_if_used is not None
                else None
            ),
            "component_proxy_auto_from_mesh": bool(self.cfg.component_proxy_auto_from_mesh),
            "component_proxy_padding": float(self.cfg.component_proxy_padding),
            "component_proxy_visual_visible": bool(self.cfg.component_proxy_visual_visible),
            "raw_mesh_bounds_obj_units_min": list(self.cfg.component_mesh_raw_bounds_obj_units_min),
            "raw_mesh_bounds_obj_units_max": list(self.cfg.component_mesh_raw_bounds_obj_units_max),
            "scaled_local_mesh_bounds_m_min": list(self.cfg.component_mesh_scaled_local_bounds_m_min),
            "scaled_local_mesh_bounds_m_max": list(self.cfg.component_mesh_scaled_local_bounds_m_max),
            "transformed_world_mesh_bounds_m_min": list(self.cfg.component_mesh_world_bounds_m_min),
            "transformed_world_mesh_bounds_m_max": list(self.cfg.component_mesh_world_bounds_m_max),
            "auto_component_proxy_center": list(self.cfg.component_mesh_auto_proxy_center),
            "auto_component_proxy_half_extents": list(self.cfg.component_mesh_auto_proxy_half_extents),
            "component_proxy_center": list(self.cfg.component_proxy_center),
            "component_proxy_half_extents": list(self.cfg.component_proxy_half_extents),
        }

    def _setup_scene(self):
        # Register only debug visuals in this skeleton. When real robots are added, ArticulationCfg/RigidObjectCfg
        # assets should be created here before cloning environments.
        if self.cfg.enable_usd_debug_visuals:
            self._create_static_usd_debug_scene()
        self.scene.clone_environments(copy_from_source=False)
        self._configure_gui_lighting()
        self._configure_gui_camera()

    def _configure_gui_lighting(self):
        """Prefer viewport camera lighting for GUI debugging while leaving headless runs unchanged."""
        if not self.cfg.use_camera_light_in_gui or not self.sim.has_gui():
            return

        try:
            import carb
            import omni.usd
            from omni.kit.viewport.menubar.lighting.actions import _set_lighting_mode

            succeeded, lighting_mode, _ = _set_lighting_mode("camera", usd_context=omni.usd.get_context())
            if not succeeded or lighting_mode != "camera":
                carb.settings.get_settings().set("/rtx/useViewLightingMode", True)
                carb.log_warn("Fell back to /rtx/useViewLightingMode for scan debug camera lighting.")
        except Exception as exc:
            try:
                import carb

                carb.settings.get_settings().set("/rtx/useViewLightingMode", True)
                carb.log_warn(f"Could not enable scan debug camera lighting: {exc}")
            except Exception:
                pass

    def _configure_gui_camera(self):
        """Set a useful default GUI viewport angle for scan debugging."""
        if not self.cfg.gui_camera_enabled or not self.sim.has_gui():
            return

        try:
            self.sim.set_camera_view(
                eye=list(self.cfg.gui_camera_eye),
                target=list(self.cfg.gui_camera_target),
            )
        except Exception as exc:
            try:
                import carb

                carb.log_warn(f"Could not set scan debug GUI camera view: {exc}")
            except Exception:
                pass

    def _create_static_usd_debug_scene(self):
        """Create non-physics USD visuals for GUI inspection.

        These prims are intentionally not RigidObject/Articulation assets. They do not enter PhysX tensor views, so
        training remains a high-level tensor task while the viewport still shows the task layout.
        """
        from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade

        stage = self.scene.stage
        root_path = self.scene.env_prim_paths[0]
        material_cache = {}

        def make_material(
            name: str,
            color: tuple[float, float, float],
            opacity: float = 1.0,
            roughness: float = 0.55,
            specular_color: tuple[float, float, float] | None = None,
        ):
            if name in material_cache:
                return material_cache[name]
            material_path = f"/World/Materials/{name}"
            material = UsdShade.Material.Define(stage, material_path)
            shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
            shader.CreateIdAttr("UsdPreviewSurface")
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
            if specular_color is not None:
                shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*specular_color))
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
            material_cache[name] = material
            return material

        def set_transform(
            prim,
            pos: tuple[float, float, float],
            scale: tuple[float, float, float],
            yaw_rad: float = 0.0,
        ):
            UsdGeom.XformCommonAPI(prim).SetTranslate(Gf.Vec3d(*pos))
            UsdGeom.XformCommonAPI(prim).SetRotate(
                (0.0, 0.0, math.degrees(yaw_rad)), UsdGeom.XformCommonAPI.RotationOrderXYZ
            )
            UsdGeom.XformCommonAPI(prim).SetScale(Gf.Vec3f(*scale))

        def add_cube(
            path: str,
            pos: tuple[float, float, float],
            scale: tuple[float, float, float],
            mat_name: str,
            yaw_rad: float = 0.0,
        ):
            cube = UsdGeom.Cube.Define(stage, path)
            cube.CreateSizeAttr(1.0)
            set_transform(cube.GetPrim(), pos, scale, yaw_rad)
            UsdShade.MaterialBindingAPI(cube.GetPrim()).Bind(material_cache[mat_name])

        def add_sphere(path: str, pos: tuple[float, float, float], radius: float, mat_name: str):
            sphere = UsdGeom.Sphere.Define(stage, path)
            sphere.CreateRadiusAttr(radius)
            set_transform(sphere.GetPrim(), pos, (1.0, 1.0, 1.0))
            UsdShade.MaterialBindingAPI(sphere.GetPrim()).Bind(material_cache[mat_name])

        def add_component_obj_visual(path: str):
            if not self.cfg.component_mesh_path or not self.cfg.component_mesh_visible:
                return
            mesh_data = load_obj_mesh(self.cfg.component_mesh_path)
            if not mesh_data.faces:
                print(
                    "[WARN]: Component OBJ visual mesh has no faces; bbox proxy remains active but no mesh surface "
                    f"visual was created for {self.cfg.component_mesh_path}."
                )
                return
            # The transform is baked into the USD points to avoid depending on a GUI/USD conversion step. This prim is
            # visual-only and intentionally has no collision or physics API applied.
            world_vertices = transform_vertices(
                mesh_data.vertices,
                mesh_scale=self.cfg.component_mesh_scale,
                mesh_position=self.cfg.component_mesh_position,
                mesh_orientation=self.cfg.component_mesh_orientation,
            )
            mesh = UsdGeom.Mesh.Define(stage, path)
            mesh.CreatePointsAttr([Gf.Vec3f(*vertex) for vertex in world_vertices])
            mesh.CreateFaceVertexCountsAttr([len(face) for face in mesh_data.faces])
            mesh.CreateFaceVertexIndicesAttr([index for face in mesh_data.faces for index in face])
            mesh.CreateSubdivisionSchemeAttr("none")
            UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material_cache["scan_component_mesh_gray"])

        def add_ground_grid_visual(path: str):
            if not self.cfg.ground_grid_enabled:
                return
            half_extent = float(self.cfg.ground_grid_half_extent)
            spacing = float(self.cfg.ground_grid_spacing)
            z_value = float(self.cfg.ground_grid_z)
            line_width = float(self.cfg.ground_grid_line_width)
            steps = max(1, int(math.floor(half_extent / spacing)))
            coordinates = [round(index * spacing, 6) for index in range(-steps, steps + 1)]
            points = []
            curve_vertex_counts = []
            for coordinate in coordinates:
                points.extend(
                    [
                        Gf.Vec3f(-half_extent, coordinate, z_value),
                        Gf.Vec3f(half_extent, coordinate, z_value),
                    ]
                )
                curve_vertex_counts.append(2)
                points.extend(
                    [
                        Gf.Vec3f(coordinate, -half_extent, z_value),
                        Gf.Vec3f(coordinate, half_extent, z_value),
                    ]
                )
                curve_vertex_counts.append(2)

            grid = UsdGeom.BasisCurves.Define(stage, path)
            grid.CreateTypeAttr("linear")
            grid.CreateCurveVertexCountsAttr(curve_vertex_counts)
            grid.CreatePointsAttr(points)
            grid.CreateWidthsAttr([line_width] * len(points))
            try:
                grid.SetWidthsInterpolation(UsdGeom.Tokens.vertex)
            except AttributeError:
                pass
            grid.CreateWrapAttr("nonperiodic")
            UsdShade.MaterialBindingAPI(grid.GetPrim()).Bind(material_cache["scan_ground_grid"])

        robot_visual_mesh_cache = {}

        def _robot_visual_mesh_payload(
            resolved_path: str,
            mesh_scale: tuple[float, float, float],
        ):
            cache_key = (resolved_path, mesh_scale)
            if cache_key in robot_visual_mesh_cache:
                return robot_visual_mesh_cache[cache_key]
            mesh_data = load_obj_mesh(resolved_path)
            if not mesh_data.faces:
                raise ValueError(f"robot visual OBJ has no faces: {resolved_path}")
            local_vertices = transform_vertices(
                mesh_data.vertices,
                mesh_scale=mesh_scale,
                mesh_position=(0.0, 0.0, 0.0),
                mesh_orientation=(1.0, 0.0, 0.0, 0.0),
            )
            local_min_z = min(vertex[2] for vertex in local_vertices)
            payload = (
                [Gf.Vec3f(*vertex) for vertex in local_vertices],
                [len(face) for face in mesh_data.faces],
                [index for face in mesh_data.faces for index in face],
                local_min_z,
            )
            robot_visual_mesh_cache[cache_key] = payload
            return payload

        def add_robot_obj_visual(robot_name: str, agent_index: int):
            diagnostics = self.cfg.robot_config_diagnostics or {}
            mesh_resolved_by_robot = diagnostics.get("visual_mesh_resolved_path_by_robot", {}) or {}
            mesh_scale_by_robot = diagnostics.get("visual_mesh_scale_by_robot", {}) or {}
            mesh_position_offset_by_robot = diagnostics.get("visual_mesh_position_offset_by_robot", {}) or {}
            mesh_yaw_offset_by_robot = diagnostics.get("visual_mesh_yaw_offset_by_robot", {}) or {}
            mesh_align_bottom_by_robot = (
                diagnostics.get("visual_mesh_align_bottom_to_proxy_z_by_robot", {}) or {}
            )
            mesh_local_min_z_by_robot = diagnostics.get("visual_mesh_local_min_z_by_robot", {}) or {}
            mesh_auto_bottom_offset_z_by_robot = (
                diagnostics.get("visual_mesh_auto_bottom_offset_z_by_robot", {}) or {}
            )
            mesh_effective_position_offset_by_robot = (
                diagnostics.get("visual_mesh_effective_position_offset_by_robot", {}) or {}
            )
            mesh_spawned_by_robot = diagnostics.get("visual_mesh_spawned_by_robot", {}) or {}
            mesh_prim_path_by_robot = diagnostics.get("visual_mesh_prim_path_by_robot", {}) or {}
            follow_enabled_by_robot = diagnostics.get("visual_follow_enabled_by_robot", {}) or {}
            mesh_error_by_robot = diagnostics.get("visual_mesh_error_by_robot", {}) or {}
            mesh_enabled_by_robot = diagnostics.get("visual_mesh_enabled_by_robot", {}) or {}

            visual_root_path = f"{root_path}/RobotVisuals"
            UsdGeom.Xform.Define(stage, visual_root_path)
            mesh_path = mesh_resolved_by_robot.get(robot_name)
            prim_path = f"{visual_root_path}/{_safe_usd_prim_name(robot_name)}_visual"
            mesh_prim_path_by_robot[robot_name] = prim_path
            if not bool(mesh_enabled_by_robot.get(robot_name, True)):
                mesh_spawned_by_robot[robot_name] = False
                follow_enabled_by_robot[robot_name] = False
                mesh_error_by_robot[robot_name] = None
                return
            if not mesh_path:
                mesh_spawned_by_robot[robot_name] = False
                follow_enabled_by_robot[robot_name] = False
                mesh_error_by_robot[robot_name] = None
                return

            try:
                mesh_scale = _as_float_tuple(
                    mesh_scale_by_robot.get(robot_name, ROBOT_VISUAL_MESH_SCALE),
                    name=f"visual_mesh_scale_by_robot[{robot_name}]",
                    length=3,
                )
                position_offset = _as_float_tuple(
                    mesh_position_offset_by_robot.get(robot_name, ROBOT_VISUAL_MESH_POSITION_OFFSET),
                    name=f"visual_mesh_position_offset_by_robot[{robot_name}]",
                    length=3,
                )
                yaw_offset = float(mesh_yaw_offset_by_robot.get(robot_name, ROBOT_VISUAL_MESH_YAW_OFFSET))
                if not math.isfinite(yaw_offset):
                    raise ValueError(f"visual_mesh_yaw_offset_by_robot[{robot_name}] must be finite.")
                points, face_counts, face_indices, local_min_z = _robot_visual_mesh_payload(
                    str(mesh_path), mesh_scale
                )
                align_bottom = bool(mesh_align_bottom_by_robot.get(robot_name, False))
                auto_bottom_offset_z = -local_min_z if align_bottom else 0.0
                effective_position_offset = (
                    position_offset[0],
                    position_offset[1],
                    position_offset[2] + auto_bottom_offset_z,
                )
                mesh_local_min_z_by_robot[robot_name] = local_min_z
                mesh_auto_bottom_offset_z_by_robot[robot_name] = auto_bottom_offset_z
                mesh_effective_position_offset_by_robot[robot_name] = list(effective_position_offset)
                mesh = UsdGeom.Mesh.Define(stage, prim_path)
                mesh.CreatePointsAttr(points)
                mesh.CreateFaceVertexCountsAttr(face_counts)
                mesh.CreateFaceVertexIndicesAttr(face_indices)
                mesh.CreateSubdivisionSchemeAttr("none")
                UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material_cache["scan_robot_visual_mesh"])
                pose = self.cfg.base_start_poses[agent_index]
                visual_pos, visual_yaw = _robot_visual_pose_from_proxy(
                    (pose[0], pose[1], pose[2]),
                    pose[3],
                    effective_position_offset,
                    yaw_offset,
                )
                set_transform(mesh.GetPrim(), visual_pos, (1.0, 1.0, 1.0), visual_yaw)
                mesh_spawned_by_robot[robot_name] = True
                follow_enabled_by_robot[robot_name] = True
                mesh_error_by_robot[robot_name] = None
            except Exception as exc:
                print(
                    "[WARN]: Robot OBJ visual mesh was not spawned; task-space proxy remains active. "
                    f"robot={robot_name} path={mesh_path} error={exc}"
                )
                mesh_spawned_by_robot[robot_name] = False
                follow_enabled_by_robot[robot_name] = False
                mesh_error_by_robot[robot_name] = str(exc)

            diagnostics["visual_mesh_spawned_by_robot"] = mesh_spawned_by_robot
            diagnostics["visual_mesh_prim_path_by_robot"] = mesh_prim_path_by_robot
            diagnostics["visual_follow_enabled_by_robot"] = follow_enabled_by_robot
            diagnostics["visual_mesh_error_by_robot"] = mesh_error_by_robot
            diagnostics["visual_mesh_local_min_z_by_robot"] = mesh_local_min_z_by_robot
            diagnostics["visual_mesh_auto_bottom_offset_z_by_robot"] = mesh_auto_bottom_offset_z_by_robot
            diagnostics["visual_mesh_effective_position_offset_by_robot"] = (
                mesh_effective_position_offset_by_robot
            )

        # Keep the large component translucent and matte so robots behind it remain visible without specular glare.
        make_material("scan_component_blue", (0.2, 0.45, 0.9), opacity=0.35, roughness=1.0, specular_color=(0.0, 0.0, 0.0))
        make_material("scan_component_mesh_gray", (0.62, 0.65, 0.68), opacity=1.0, roughness=0.8, specular_color=(0.02, 0.02, 0.02))
        make_material("scan_robot_red", (0.9, 0.2, 0.2))
        make_material("scan_robot_green", (0.2, 0.8, 0.3))
        make_material("scan_robot_yellow", (0.9, 0.75, 0.2))
        make_material("scan_robot_visual_mesh", (0.55, 0.58, 0.62), opacity=1.0, roughness=0.75, specular_color=(0.02, 0.02, 0.02))
        make_material("scan_scanner_white", (0.95, 0.95, 0.95))
        make_material("scan_viewpoint_cyan", (0.0, 0.85, 1.0))
        make_material("scan_ground_grid", (0.34, 0.36, 0.38), opacity=1.0, roughness=1.0, specular_color=(0.0, 0.0, 0.0))

        # Use a non-dome stage light to keep Isaac Sim's default viewport background. In GUI runs, camera light is
        # enabled separately by `_configure_gui_lighting()` for a brighter debug view.
        light = UsdLux.DistantLight.Define(stage, "/World/ScanDebugLight")
        light.CreateIntensityAttr(2500.0)

        if self.cfg.component_proxy_visual_visible:
            component_scale = tuple(2.0 * value for value in self.cfg.component_proxy_half_extents)
            add_cube(
                f"{root_path}/LargeComponentVisual",
                self.cfg.component_proxy_center,
                component_scale,
                "scan_component_blue",
            )
        add_ground_grid_visual(f"{root_path}/GroundGrid")
        add_component_obj_visual(f"{root_path}/MeasuredComponentObjVisual")

        robot_materials = ("scan_robot_red", "scan_robot_green", "scan_robot_yellow")
        for index, pose in enumerate(self.cfg.base_start_poses):
            robot_name = str(self.cfg.possible_agents[index])
            if self.cfg.robot_visual_mode == "mesh":
                add_robot_obj_visual(robot_name, index)
            if self.cfg.robot_visual_mode != "none":
                add_cube(
                    f"{root_path}/Robot_{index}_BaseMarker",
                    (pose[0], pose[1], pose[2]),
                    (0.65, 0.45, 0.25),
                    robot_materials[index % len(robot_materials)],
                    pose[3],
                )
                scanner_pos = (
                    pose[0] + self.cfg.scanner_start_offsets[index][0],
                    pose[1] + self.cfg.scanner_start_offsets[index][1],
                    pose[2] + self.cfg.scanner_start_offsets[index][2],
                )
                add_sphere(
                    f"{root_path}/Robot_{index}_ScannerMarker",
                    scanner_pos,
                    0.12,
                    "scan_scanner_white",
                )

        for index, viewpoint in enumerate(self.cfg.viewpoint_poses):
            add_sphere(
                f"{root_path}/Viewpoint_{index:02d}",
                (viewpoint[0], viewpoint[1], viewpoint[2]),
                0.08,
                "scan_viewpoint_cyan",
            )

    def _should_update_usd_debug_visuals(self) -> bool:
        """Return whether USD debug markers can be visible in the current run."""
        if not self.cfg.enable_usd_debug_visuals:
            return False
        if self.sim.has_gui():
            return True
        return self.sim.render_mode >= self.sim.RenderMode.PARTIAL_RENDERING

    def _record_obstacle_debug_visualization_skip(self, reason: str) -> None:
        self._obstacle_debug_visualization_last_diagnostics = self._obstacle_debug_visualization_base_diagnostics(
            drawn_line_count=0,
            skipped_reason=reason,
            pairs_sample=[],
            line_prim_paths_sample=[],
        )

    def _should_update_obstacle_debug_visuals(self) -> bool:
        if not bool(getattr(self.cfg, "obstacle_debug_visualization_enabled", False)):
            self._record_obstacle_debug_visualization_skip("disabled")
            return False
        if not self.cfg.enable_usd_debug_visuals:
            self._record_obstacle_debug_visualization_skip("usd_debug_visuals_disabled")
            return False
        if not bool(getattr(self.cfg, "obstacle_diagnostics_enabled", False)):
            self._record_obstacle_debug_visualization_skip("obstacle_diagnostics_disabled")
            return False
        if getattr(self.cfg, "obstacle_debug_visualization_line_source", None) != "mesh_footprint_intersections":
            self._record_obstacle_debug_visualization_skip("unsupported_line_source")
            return False
        draw_in_headless = bool(getattr(self.cfg, "obstacle_debug_visualization_draw_in_headless", False))
        if not self.sim.has_gui() and not draw_in_headless:
            self._record_obstacle_debug_visualization_skip("headless_without_draw_in_headless")
            return False
        if not self.sim.has_gui() and not draw_in_headless and not self._should_update_usd_debug_visuals():
            self._record_obstacle_debug_visualization_skip("debug_visuals_unavailable")
            return False
        return True

    def _ensure_obstacle_debug_line_material(self, stage):
        from pxr import Gf, Sdf, UsdShade

        material_path = "/World/Materials/scan_obstacle_blocked_line"
        material = UsdShade.Material.Get(stage, material_path)
        if material and material.GetPrim().IsValid():
            return material
        material = UsdShade.Material.Define(stage, material_path)
        shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1.0, 0.05, 0.02))
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.35, 0.0, 0.0))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.35)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        return material

    def _hide_inactive_obstacle_debug_lines(self, stage, UsdGeom, active_paths: set[str]) -> None:
        previous_paths = getattr(self, "_obstacle_debug_line_prim_paths", set())
        for prim_path in previous_paths - active_paths:
            prim = stage.GetPrimAtPath(prim_path)
            if prim.IsValid():
                UsdGeom.Imageable(prim).MakeInvisible()
        self._obstacle_debug_line_prim_paths = set(previous_paths | active_paths)

    def _select_obstacle_debug_line_pairs(self, problem: dict) -> tuple[list[dict], str | None]:
        mask = problem.get("mesh_footprint_intersection_mask")
        if not isinstance(mask, torch.Tensor):
            return [], "missing_mesh_footprint_intersection_mask"
        mask = mask.to(dtype=torch.bool)
        if mask.ndim != 3:
            return [], "invalid_mesh_footprint_intersection_mask_shape"
        if not bool(mask.any().item()):
            return [], "no_blocked_pairs"

        max_lines_per_robot = int(getattr(self.cfg, "obstacle_debug_visualization_max_lines_per_robot", 0))
        max_total_lines = int(getattr(self.cfg, "obstacle_debug_visualization_max_total_lines", 0))
        if max_lines_per_robot <= 0 or max_total_lines <= 0:
            return [], "line_limit_zero"

        straight_line_cost = problem.get("straight_line_cost_matrix")
        aware_cost = problem.get("mesh_footprint_aware_cost_matrix")
        prefer_shortest = bool(
            getattr(self.cfg, "obstacle_debug_visualization_prefer_shortest_blocked_pairs", True)
        )
        viewpoint_pos = problem["viewpoint_pos"]
        viewpoint_ids = list(problem.get("viewpoint_ids", range(self.num_viewpoints)))
        z_mode = str(getattr(self.cfg, "obstacle_debug_visualization_line_z_mode", "max_endpoint"))
        z_value = float(getattr(self.cfg, "obstacle_debug_visualization_line_z_value", 0.20))
        z_offset = float(getattr(self.cfg, "obstacle_debug_visualization_line_z_offset", 0.05))

        pairs: list[dict] = []
        for env_id in range(min(mask.shape[0], self.num_envs)):
            for agent_id in range(min(mask.shape[1], self.num_agents_cfg)):
                candidate_indices = torch.nonzero(mask[env_id, agent_id], as_tuple=False).flatten().tolist()
                if prefer_shortest and isinstance(straight_line_cost, torch.Tensor):
                    candidate_indices.sort(
                        key=lambda viewpoint_index: float(
                            straight_line_cost[env_id, agent_id, int(viewpoint_index)].detach().cpu().item()
                        )
                    )
                for viewpoint_index in candidate_indices[:max_lines_per_robot]:
                    if len(pairs) >= max_total_lines:
                        return pairs, None
                    viewpoint_index = int(viewpoint_index)
                    base_pos = self.base_pos[env_id, agent_id].detach().cpu().tolist()
                    end_pos = viewpoint_pos[env_id, viewpoint_index].detach().cpu().tolist()
                    if z_mode == "fixed":
                        line_z = z_value + z_offset
                    else:
                        line_z = max(float(base_pos[2]), float(end_pos[2]), 0.0) + z_offset
                    pair = {
                        "env_id": env_id,
                        "robot_id": agent_id,
                        "robot_name": str(self.cfg.possible_agents[agent_id]),
                        "viewpoint_id": viewpoint_ids[viewpoint_index]
                        if viewpoint_index < len(viewpoint_ids)
                        else viewpoint_index,
                        "viewpoint_index": viewpoint_index,
                        "straight_line_cost": None,
                        "obstacle_aware_cost": None,
                        "intersects_mesh_footprint": True,
                        "_line_start": (float(base_pos[0]), float(base_pos[1]), line_z),
                        "_line_end": (float(end_pos[0]), float(end_pos[1]), line_z),
                    }
                    if isinstance(straight_line_cost, torch.Tensor):
                        pair["straight_line_cost"] = float(
                            straight_line_cost[env_id, agent_id, viewpoint_index].detach().cpu().item()
                        )
                    if isinstance(aware_cost, torch.Tensor):
                        pair["obstacle_aware_cost"] = float(
                            aware_cost[env_id, agent_id, viewpoint_index].detach().cpu().item()
                        )
                    pairs.append(pair)
        return pairs, None

    def _update_obstacle_debug_visual_lines(self, stage, Gf, UsdGeom) -> None:
        problem = self.get_assignment_problem()
        selected_pairs, skipped_reason = self._select_obstacle_debug_line_pairs(problem)
        active_paths: set[str] = set()
        if not selected_pairs:
            self._hide_inactive_obstacle_debug_lines(stage, UsdGeom, active_paths)
            self._obstacle_debug_visualization_last_diagnostics = (
                self._obstacle_debug_visualization_base_diagnostics(
                    drawn_line_count=0,
                    skipped_reason=skipped_reason or "no_selected_pairs",
                    pairs_sample=[],
                    line_prim_paths_sample=[],
                )
            )
            return

        from pxr import UsdShade

        material = self._ensure_obstacle_debug_line_material(stage)
        line_width = float(getattr(self.cfg, "obstacle_debug_visualization_line_width", 0.03))
        for line_index, pair in enumerate(selected_pairs):
            env_id = int(pair["env_id"])
            if env_id >= len(self.scene.env_prim_paths):
                continue
            root_path = f"{self.scene.env_prim_paths[env_id]}/ObstacleDebugLines"
            UsdGeom.Xform.Define(stage, root_path)
            prim_path = f"{root_path}/BlockedPath_{line_index:03d}"
            curve = UsdGeom.BasisCurves.Define(stage, prim_path)
            curve.CreateTypeAttr("linear")
            curve.CreateCurveVertexCountsAttr([2])
            curve.CreatePointsAttr([Gf.Vec3f(*pair["_line_start"]), Gf.Vec3f(*pair["_line_end"])])
            curve.CreateWidthsAttr([line_width, line_width])
            try:
                curve.SetWidthsInterpolation(UsdGeom.Tokens.vertex)
            except AttributeError:
                pass
            curve.CreateWrapAttr("nonperiodic")
            UsdShade.MaterialBindingAPI(curve.GetPrim()).Bind(material)
            UsdGeom.Imageable(curve.GetPrim()).MakeVisible()
            active_paths.add(prim_path)

        self._hide_inactive_obstacle_debug_lines(stage, UsdGeom, active_paths)
        sample_pairs = [
            {key: value for key, value in pair.items() if not key.startswith("_")}
            for pair in selected_pairs[:10]
        ]
        self._obstacle_debug_visualization_last_diagnostics = self._obstacle_debug_visualization_base_diagnostics(
            drawn_line_count=len(active_paths),
            skipped_reason=None,
            pairs_sample=sample_pairs,
            line_prim_paths_sample=sorted(active_paths)[:10],
        )

    def _update_usd_debug_visuals(self):
        """Update USD markers from high-level task-space buffers."""
        update_debug_markers = self._should_update_usd_debug_visuals()
        update_obstacle_debug_lines = self._should_update_obstacle_debug_visuals()
        visual_follow_enabled = (
            (self.cfg.robot_config_diagnostics or {}).get("visual_follow_enabled_by_robot", {}) or {}
        )
        visual_position_offsets = (
            (self.cfg.robot_config_diagnostics or {}).get(
                "visual_mesh_effective_position_offset_by_robot", {}
            )
            or (self.cfg.robot_config_diagnostics or {}).get("visual_mesh_position_offset_by_robot", {})
            or {}
        )
        visual_yaw_offsets = (
            (self.cfg.robot_config_diagnostics or {}).get("visual_mesh_yaw_offset_by_robot", {}) or {}
        )
        update_robot_visuals = any(bool(value) for value in visual_follow_enabled.values())
        if not update_debug_markers and not update_robot_visuals and not update_obstacle_debug_lines:
            return

        # Marker USD writes are useful in GUI and in camera-enabled headless video. Robot visual mesh follow is also
        # allowed in pure headless smokes when a configured display-only mesh was actually spawned.
        from pxr import Gf, UsdGeom

        stage = self.scene.stage
        for env_index, env_path in enumerate(self.scene.env_prim_paths):
            for agent_index in range(self.num_agents_cfg):
                base_pos = self.base_pos[env_index, agent_index].detach().cpu().tolist()
                base_yaw = float(self.base_yaw[env_index, agent_index].detach().cpu())
                if update_debug_markers:
                    base_prim = stage.GetPrimAtPath(f"{env_path}/Robot_{agent_index}_BaseMarker")
                    scanner_prim = stage.GetPrimAtPath(f"{env_path}/Robot_{agent_index}_ScannerMarker")
                    if base_prim.IsValid():
                        UsdGeom.XformCommonAPI(base_prim).SetTranslate(Gf.Vec3d(*base_pos))
                        UsdGeom.XformCommonAPI(base_prim).SetRotate(
                            (0.0, 0.0, math.degrees(base_yaw)), UsdGeom.XformCommonAPI.RotationOrderXYZ
                        )
                    if scanner_prim.IsValid():
                        scanner_pos = self.scanner_pos[env_index, agent_index].detach().cpu().tolist()
                        UsdGeom.XformCommonAPI(scanner_prim).SetTranslate(Gf.Vec3d(*scanner_pos))

                if update_robot_visuals:
                    robot_name = str(self.cfg.possible_agents[agent_index])
                    if not bool(visual_follow_enabled.get(robot_name, False)):
                        continue
                    visual_prim = stage.GetPrimAtPath(
                        f"{env_path}/RobotVisuals/{_safe_usd_prim_name(robot_name)}_visual"
                    )
                    if not visual_prim.IsValid():
                        continue
                    position_offset = visual_position_offsets.get(robot_name, ROBOT_VISUAL_MESH_POSITION_OFFSET)
                    yaw_offset = visual_yaw_offsets.get(robot_name, ROBOT_VISUAL_MESH_YAW_OFFSET)
                    visual_pos, visual_yaw = _robot_visual_pose_from_proxy(
                        base_pos,
                        base_yaw,
                        position_offset,
                        float(yaw_offset),
                    )
                    UsdGeom.XformCommonAPI(visual_prim).SetTranslate(Gf.Vec3d(*visual_pos))
                    UsdGeom.XformCommonAPI(visual_prim).SetRotate(
                        (0.0, 0.0, math.degrees(visual_yaw)), UsdGeom.XformCommonAPI.RotationOrderXYZ
                    )

        if update_obstacle_debug_lines:
            self._update_obstacle_debug_visual_lines(stage, Gf, UsdGeom)

    def _pre_physics_step(self, actions: dict[str, torch.Tensor]):
        # Preserve the previous action for the action-rate penalty, then clamp policy/controller outputs before they
        # affect the task-space state.
        for agent, action in actions.items():
            self.previous_actions[agent] = self.actions[agent].clone()
            self.actions[agent] = action.clamp(-1.0, 1.0)
        self._integrate_high_level_actions()
        self._usd_debug_dirty = True

    def _integrate_high_level_actions(self):
        """Integrate 9D task-space actions into high-level robot/scanner buffers."""
        for agent, index in self.agent_index.items():
            action = self.actions[agent]

            # Actions are normalized increments, not torques or joint targets. Per-agent scale tensors make the same
            # action value produce different motion magnitudes for heterogeneous robots.
            base_delta = action[:, 0:2] * self.max_base_xy_step[index]
            yaw_delta = action[:, 2] * self.max_base_yaw_step[index]
            ee_delta = action[:, 3:6] * self.max_ee_xyz_step[index]
            rpy_delta = action[:, 6:9] * self.max_ee_rpy_step[index]

            self.base_pos[:, index, :2] += base_delta
            self.base_yaw[:, index] = wrap_to_pi(self.base_yaw[:, index] + yaw_delta)
            self.scanner_pos[:, index, :] += ee_delta

            delta_quat = quat_from_euler_xyz(rpy_delta[:, 0], rpy_delta[:, 1], rpy_delta[:, 2])
            self.scanner_quat[:, index, :] = normalize(quat_mul(delta_quat, self.scanner_quat[:, index, :]))

            # Enforce a simple spherical arm workspace around each base. This is the only current workspace constraint
            # before real IK/collision constraints are introduced.
            arm_vector = self.scanner_pos[:, index, :] - self.base_pos[:, index, :]
            arm_distance = torch.norm(arm_vector, dim=-1).clamp(min=1e-6)
            max_distance = self.arm_reach[index]
            clipped_vector = arm_vector / arm_distance.unsqueeze(-1) * max_distance
            too_far = arm_distance > max_distance
            self.scanner_pos[:, index, :] = torch.where(
                too_far.unsqueeze(-1), self.base_pos[:, index, :] + clipped_vector, self.scanner_pos[:, index, :]
            )
            self.last_reach_violation[:, index] = too_far.float()

    def _apply_action(self):
        # No simulator-side robot actuation in the high-level skeleton. `_integrate_high_level_actions()` already
        # updates task-space buffers; this hook mirrors those buffers into visible/video markers when needed.
        if self._usd_debug_dirty:
            self._update_usd_debug_visuals()
            self._usd_debug_dirty = False

    def _get_observations(self) -> dict[str, torch.Tensor]:
        """Build per-agent observations with the configured per-agent layout."""
        coverage_ratio = self.viewpoints_covered.float().mean(dim=-1, keepdim=True)
        observations = {}
        for agent, index in self.agent_index.items():
            # 96D layout:
            # base_rel(3), yaw sin/cos(2), scanner_rel(3), scanner_quat(4), coverage(1), capability(4),
            # nearest viewpoint slots(8 * 8), other scanners((M - 1) * 3), previous action(9).
            base_rel = self.base_pos[:, index, :] / self.cfg.scene.env_spacing
            yaw = self.base_yaw[:, index]
            yaw_sincos = torch.stack((torch.sin(yaw), torch.cos(yaw)), dim=-1)
            scanner_rel = self.scanner_pos[:, index, :] / self.cfg.scene.env_spacing
            capability = torch.stack(
                (
                    self.arm_reach[index].repeat(self.num_envs) / 4.0,
                    self.scanner_min_range[index].repeat(self.num_envs) / 4.0,
                    self.scanner_max_range[index].repeat(self.num_envs) / 4.0,
                    self.scanner_fov_cos[index].repeat(self.num_envs),
                ),
                dim=-1,
            )
            viewpoint_obs = self._get_nearest_viewpoint_observation(index)
            other_scanners = []
            for other_index in range(self.num_agents_cfg):
                if other_index != index:
                    other_scanners.append(
                        (self.scanner_pos[:, other_index, :] - self.scanner_pos[:, index, :])
                        / self.cfg.scene.env_spacing
                    )
            if other_scanners:
                other_scanner_obs = torch.cat(other_scanners, dim=-1)
            else:
                other_scanner_obs = torch.zeros(self.num_envs, 0, dtype=torch.float32, device=self.device)
            observations[agent] = torch.cat(
                (
                    base_rel,
                    yaw_sincos,
                    scanner_rel,
                    self.scanner_quat[:, index, :],
                    coverage_ratio,
                    capability,
                    viewpoint_obs,
                    other_scanner_obs,
                    self.previous_actions[agent],
                ),
                dim=-1,
            )
        return observations

    def _get_nearest_viewpoint_observation(self, agent_index: int) -> torch.Tensor:
        """Return fixed-size nearest-viewpoint slots for one agent.

        Each slot is [rel_x, rel_y, rel_z, qw, qx, qy, qz, valid]. Covered viewpoints are masked out by assigning them
        a large temporary distance. If there are fewer viewpoints than slots, the remaining rows stay zero.
        """
        k = self.cfg.num_viewpoints_in_observation
        world_viewpoints = self.viewpoint_pos_local.unsqueeze(0) + self.scene.env_origins.unsqueeze(1)
        scanner_pos = self.scanner_pos[:, agent_index, :].unsqueeze(1) + self.scene.env_origins.unsqueeze(1)
        distances = torch.norm(world_viewpoints - scanner_pos, dim=-1)

        masked_distances = distances.masked_fill(self.viewpoints_covered, 1.0e6)
        selected_count = min(k, self.num_viewpoints)
        selected_ids = torch.topk(masked_distances, k=selected_count, dim=-1, largest=False).indices

        pad = torch.zeros(self.num_envs, k, 8, device=self.device)
        batch_ids = torch.arange(self.num_envs, device=self.device).unsqueeze(-1)
        selected_pos = self.viewpoint_pos_local[selected_ids]
        selected_quat = self.viewpoint_quat[selected_ids]
        selected_valid = (~self.viewpoints_covered[batch_ids, selected_ids]).float().unsqueeze(-1)
        rel_pos = (selected_pos - self.scanner_pos[:, agent_index, :].unsqueeze(1)) / self.cfg.scene.env_spacing
        pad[:, :selected_count, :] = torch.cat((rel_pos, selected_quat, selected_valid), dim=-1)
        return pad.reshape(self.num_envs, k * 8)

    def _get_states(self) -> torch.Tensor:
        # Centralized critic state is the concatenation of agent observations in the configured agent order.
        observations = self._get_observations()
        return torch.cat([observations[agent].reshape(self.num_envs, -1) for agent in self.cfg.possible_agents], dim=-1)

    def _update_scan_progress(self):
        """Update coverage buffers and per-agent scan-event reward terms."""
        world_viewpoints = self.viewpoint_pos_local.unsqueeze(0) + self.scene.env_origins.unsqueeze(1)
        scanner_world_pos = self.scanner_pos + self.scene.env_origins.unsqueeze(1)
        pos_error = torch.norm(scanner_world_pos.unsqueeze(2) - world_viewpoints.unsqueeze(1), dim=-1)

        # Scan success requires position, orientation, workspace, sensor-range, and FOV checks. Keeping all conditions
        # explicit here makes it easy to replace each rule with a real sensor or robot constraint later.
        scanner_quat = self.scanner_quat.unsqueeze(2).expand(-1, -1, self.num_viewpoints, -1)
        viewpoint_quat = self.viewpoint_quat.view(1, 1, self.num_viewpoints, 4).expand_as(scanner_quat)
        rot_error = quat_error_magnitude(scanner_quat.reshape(-1, 4), viewpoint_quat.reshape(-1, 4)).reshape(
            self.num_envs, self.num_agents_cfg, self.num_viewpoints
        )

        arm_distance = torch.norm(
            world_viewpoints.unsqueeze(1) - (self.base_pos + self.scene.env_origins.unsqueeze(1)).unsqueeze(2), dim=-1
        )
        scanner_to_box = torch.abs(self.scanner_pos - self.component_center.view(1, 1, 3))
        scanner_to_box = torch.clamp(scanner_to_box - self.component_half_extents.view(1, 1, 3), min=0.0)
        sensor_distance = torch.norm(scanner_to_box, dim=-1).unsqueeze(-1)

        forward_axis = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float32, device=self.device)
        repeated_forward = forward_axis.repeat(self.num_envs * self.num_agents_cfg * self.num_viewpoints, 1)
        scanner_forward = quat_apply(scanner_quat.reshape(-1, 4), repeated_forward).reshape(
            self.num_envs, self.num_agents_cfg, self.num_viewpoints, 3
        )
        desired_forward = quat_apply(viewpoint_quat.reshape(-1, 4), repeated_forward).reshape(
            self.num_envs, self.num_agents_cfg, self.num_viewpoints, 3
        )
        fov_ok = torch.sum(scanner_forward * desired_forward, dim=-1) > self.scanner_fov_cos.view(1, -1, 1)

        candidate = (
            (pos_error < self.scan_pos_tolerance.view(1, -1, 1))
            & (rot_error < self.scan_rot_tolerance.view(1, -1, 1))
            & (arm_distance <= self.arm_reach.view(1, -1, 1) + 1.0e-6)
            & (sensor_distance >= self.scanner_min_range.view(1, -1, 1) - 1.0e-6)
            & (sensor_distance <= self.scanner_max_range.view(1, -1, 1) + 1.0e-6)
            & fov_ok
        )
        self.dwell_counter = torch.where(candidate, self.dwell_counter + 1, torch.zeros_like(self.dwell_counter))
        dwell_met = self.dwell_counter >= self.cfg.dwell_steps

        # If multiple robots newly scan the same viewpoint in the same frame, the global coverage event is counted once
        # and own coverage credit is split among the participating robots.
        uncovered = ~self.viewpoints_covered.unsqueeze(1)
        new_candidate = dwell_met & uncovered
        candidate_count = new_candidate.float().sum(dim=1, keepdim=True).clamp(min=1.0)
        own_new_fraction = (new_candidate.float() / candidate_count).sum(dim=-1)
        newly_covered = torch.any(new_candidate, dim=1)

        self.last_global_coverage_gain = newly_covered.float().sum(dim=-1)
        self.last_own_coverage_gain = own_new_fraction
        self.last_duplicate_scans = (candidate & self.viewpoints_covered.unsqueeze(1)).float().sum(dim=-1)
        self.viewpoints_covered |= newly_covered

    def _get_rewards(self) -> dict[str, torch.Tensor]:
        rewards = {}
        for agent, index in self.agent_index.items():
            action_rate = torch.mean(torch.square(self.actions[agent] - self.previous_actions[agent]), dim=-1)
            rewards[agent] = (
                self.cfg.global_coverage_reward_scale * self.last_global_coverage_gain
                + self.cfg.own_coverage_reward_scale * self.last_own_coverage_gain[:, index]
                - self.cfg.duplicate_scan_penalty_scale * self.last_duplicate_scans[:, index]
                - self.cfg.reach_violation_penalty_scale * self.last_reach_violation[:, index]
                - self.cfg.action_rate_penalty_scale * action_rate
                - self.cfg.time_penalty
            )
            self.extras[agent]["coverage_ratio"] = self.viewpoints_covered.float().mean()
            self.extras[agent]["new_viewpoints"] = self.last_global_coverage_gain.mean()

        # HARL's Isaac Lab adapter expects episode/logging scalars at the top-level `info["log"]` entry. DirectMARLEnv
        # returns `self.extras` as `info`, so keep this compatibility block here near the reward metrics.
        stacked_rewards = torch.stack([reward.mean() for reward in rewards.values()])
        self.extras["log"] = {
            "coverage_ratio": self.viewpoints_covered.float().mean(),
            "new_viewpoints": self.last_global_coverage_gain.mean(),
            "duplicate_scans": self.last_duplicate_scans.mean(),
            "reach_violation": self.last_reach_violation.mean(),
            "mean_reward": stacked_rewards.mean(),
        }
        return rewards

    def _get_dones(self) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        # DirectMARLEnv calls this before reward collection, so scan progress is updated here to make reward terms reflect
        # the latest post-action state.
        self._update_scan_progress()
        all_covered = torch.all(self.viewpoints_covered, dim=-1)
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        terminated = {agent: all_covered for agent in self.cfg.possible_agents}
        time_outs = {agent: time_out for agent in self.cfg.possible_agents}
        return terminated, time_outs

    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = torch.arange(self.num_envs, dtype=torch.int64, device=self.device)
        super()._reset_idx(env_ids)

        # Reset only the selected vectorized environments. The start pose tensors have shape [num_agents, ...] and are
        # broadcast across env_ids.
        self.base_pos[env_ids] = self.base_start_poses[:, :3].unsqueeze(0)
        self.base_yaw[env_ids] = self.base_start_poses[:, 3].unsqueeze(0)
        self.scanner_pos[env_ids] = self.base_pos[env_ids] + self.scanner_start_offsets.unsqueeze(0)
        self.scanner_quat[env_ids, :, :] = torch.tensor(
            (1.0, 0.0, 0.0, 0.0), dtype=torch.float32, device=self.device
        )
        self.viewpoints_covered[env_ids] = False
        self.dwell_counter[env_ids] = 0
        self.last_global_coverage_gain[env_ids] = 0.0
        self.last_own_coverage_gain[env_ids] = 0.0
        self.last_duplicate_scans[env_ids] = 0.0
        self.last_reach_violation[env_ids] = 0.0
        for agent in self.cfg.possible_agents:
            self.actions[agent][env_ids] = 0.0
            self.previous_actions[agent][env_ids] = 0.0
        self._usd_debug_dirty = True
        self._update_usd_debug_visuals()
        self._run_reset_diagnostics()

    def _log_static_configuration(self) -> None:
        print(
            "[INFO]: Scan component proxy "
            f"type={self.cfg.component_proxy_type} center={self.cfg.component_proxy_center} "
            f"half_extents={self.cfg.component_proxy_half_extents} "
            f"visual_visible={self.cfg.component_proxy_visual_visible}"
        )
        print(f"[INFO]: Scan scenario diagnostics {self.get_scenario_diagnostics()}")
        print(f"[INFO]: Scan robot config diagnostics {self.get_robot_config_diagnostics()}")
        print(f"[INFO]: Scan capability diagnostics {self.get_capability_diagnostics()}")
        if self.cfg.component_mesh_path:
            print(
                "[INFO]: Scan component visual mesh "
                f"path={self.cfg.component_mesh_path} format={self.cfg.component_mesh_format} "
                f"unit={self.cfg.component_mesh_unit} scale={self.cfg.component_mesh_scale} "
                f"position={self.cfg.component_mesh_position} orientation={self.cfg.component_mesh_orientation} "
                f"align_base_center_to_world_origin={self.cfg.component_mesh_align_base_center_to_world_origin}"
            )
            if self.cfg.component_mesh_align_base_center_to_world_origin:
                print(
                    "[INFO]: Scan component mesh base-center alignment "
                    f"base_center_before_translation={self.cfg.component_mesh_base_center_before_translation} "
                    f"auto_translation={self.cfg.component_mesh_auto_translation_if_used}"
                )
            print(
                "[INFO]: Scan component mesh bounds "
                f"raw_min={self.cfg.component_mesh_raw_bounds_obj_units_min} "
                f"raw_max={self.cfg.component_mesh_raw_bounds_obj_units_max} "
                f"world_min={self.cfg.component_mesh_world_bounds_m_min} "
                f"world_max={self.cfg.component_mesh_world_bounds_m_max} "
                f"auto_proxy_center={self.cfg.component_mesh_auto_proxy_center} "
                f"auto_proxy_half_extents={self.cfg.component_mesh_auto_proxy_half_extents}"
            )
        if self.cfg.obstacle_diagnostics_enabled:
            print(
                "[INFO]: Scan obstacle diagnostics "
                f"mode={self.cfg.obstacle_diagnostics_mode} source={self.cfg.obstacle_source} "
                f"footprint={self.get_component_obstacle_footprint_diagnostics()}"
            )
        print(
            "[INFO]: Scan viewpoints loaded "
            f"source={self.viewpoint_source} num_viewpoints={self.num_viewpoints} "
            f"no-op id={self.noop_action_id} viewpoint_ids={list(self.viewpoint_ids)}"
        )
        print(
            "[INFO]: Scan feasibility generator "
            f"type={self.cfg.feasibility_generator_type} "
            f"static_mask_shape={tuple(self.static_geometric_feasible_mask.shape)}"
        )
        if self.manual_feasibility_override_rows:
            print(
                "[WARN]: Fixed-12 manual feasibility overrides remain active; "
                "these rows carry cached or required Level 2 controller diagnostics: "
                f"{self.manual_feasibility_override_rows}"
            )
        if self.num_viewpoints != 12:
            print(
                "[WARN]: Fixed-N assignment checkpoints are only compatible with the same num_viewpoints "
                f"and action-space width. Old fixed-12 checkpoints are incompatible with N={self.num_viewpoints}."
            )

    def _run_reset_diagnostics(self) -> None:
        if not self.cfg.enable_reset_diagnostics:
            return
        if self.cfg.reset_diagnostics_once and self._reset_diagnostics_printed:
            return

        problem = self.get_assignment_problem()
        feasible_mask = problem["feasible_mask"].to(dtype=torch.bool)
        static_feasible_mask = problem["static_geometric_feasible_mask"].to(dtype=torch.bool)
        env_has_feasible_agent = feasible_mask.any(dim=1)
        missing_env_viewpoints = ~env_has_feasible_agent
        permanently_unavailable = torch.nonzero(missing_env_viewpoints.any(dim=0), as_tuple=False).flatten()
        permanently_unavailable_ids = [
            self.viewpoint_ids[int(index.item())] for index in permanently_unavailable.detach().cpu()
        ]

        static_feasible_agents_per_viewpoint = {}
        first_env_static_feasible = static_feasible_mask[0]
        for viewpoint_index, viewpoint_id in enumerate(self.viewpoint_ids):
            static_feasible_agents_per_viewpoint[int(viewpoint_id)] = [
                agent
                for agent, agent_index in self.agent_index.items()
                if bool(first_env_static_feasible[agent_index, viewpoint_index].item())
            ]

        feasible_agents_per_viewpoint = {}
        first_env_feasible = feasible_mask[0]
        for viewpoint_index, viewpoint_id in enumerate(self.viewpoint_ids):
            feasible_agents_per_viewpoint[int(viewpoint_id)] = [
                agent
                for agent, agent_index in self.agent_index.items()
                if bool(first_env_feasible[agent_index, viewpoint_index].item())
            ]

        available_actions_shape = (self.num_envs, self.num_agents_cfg, self.num_viewpoints + 1)
        print(
            "[INFO]: Scan reset diagnostics "
            f"num_envs={self.num_envs} num_agents={self.num_agents_cfg} "
            f"num_viewpoints={self.num_viewpoints} no-op id={self.noop_action_id} "
            f"available_actions shape={available_actions_shape}"
        )
        print(f"[INFO]: Scan reset diagnostics viewpoint ids={list(self.viewpoint_ids)}")
        print(
            "[INFO]: Scan reset diagnostics static geometric feasible agents per viewpoint="
            f"{static_feasible_agents_per_viewpoint}"
        )
        print(f"[INFO]: Scan reset diagnostics final feasible agents per viewpoint={feasible_agents_per_viewpoint}")
        mesh_diagnostics = self.get_component_mesh_diagnostics()
        if mesh_diagnostics is not None:
            print(f"[INFO]: Scan reset diagnostics component mesh={mesh_diagnostics}")
        print(f"[INFO]: Scan reset diagnostics scenario={self.get_scenario_diagnostics()}")
        print(f"[INFO]: Scan reset diagnostics robot config={self.get_robot_config_diagnostics()}")
        print(f"[INFO]: Scan reset diagnostics capability config={self.get_capability_diagnostics()}")
        print(
            "[INFO]: Scan reset diagnostics infeasible rows="
            f"{[row for row in self.feasibility_diagnostic_rows if not row['feasible']]}"
        )
        print(f"[INFO]: Scan reset diagnostics permanently unavailable viewpoints={permanently_unavailable_ids}")

        self._reset_diagnostics_printed = True
        if permanently_unavailable_ids and self.cfg.require_each_viewpoint_feasible:
            detail_rows = []
            poses = self.viewpoint_poses.detach().cpu().tolist()
            for viewpoint_index in permanently_unavailable.detach().cpu().tolist():
                failed_envs = torch.nonzero(missing_env_viewpoints[:, viewpoint_index], as_tuple=False).flatten()
                pair_rows = [
                    row
                    for row in self.feasibility_diagnostic_rows
                    if row["viewpoint_index"] == int(viewpoint_index)
                ]
                detail_rows.append(
                    {
                        "viewpoint_id": self.viewpoint_ids[int(viewpoint_index)],
                        "pose": poses[int(viewpoint_index)],
                        "failed_envs": failed_envs.detach().cpu().tolist(),
                        "agent_viewpoint_diagnostics": pair_rows,
                    }
                )
            raise RuntimeError(
                "Scan assignment feasibility failure: viewpoints have no feasible agent. "
                f"permanently_unavailable_viewpoints={permanently_unavailable_ids} details={detail_rows}"
            )

    def _build_static_feasibility(self) -> None:
        if self.cfg.feasibility_generator_type != "static_geometric_v1":
            raise ValueError(
                f"Unsupported feasibility_generator_type={self.cfg.feasibility_generator_type!r}; "
                "only 'static_geometric_v1' is supported in Stage 3A."
            )

        result = generate_static_geometric_feasibility(
            viewpoint_ids=self.viewpoint_ids,
            viewpoint_pos=self.viewpoint_pos_local,
            viewpoint_quat=self.viewpoint_quat,
            component_center=self.component_center,
            component_half_extents=self.component_half_extents,
            agent_names=tuple(self.cfg.possible_agents),
            base_start_poses=self.base_start_poses,
            arm_reach=self.arm_reach,
            scanner_min_range=self.scanner_min_range,
            scanner_max_range=self.scanner_max_range,
            scanner_fov_cos=self.scanner_fov_cos,
            scanner_fov_deg=self.scanner_fov_deg,
            scan_pos_tolerance=self.scan_pos_tolerance,
            scan_rot_tolerance=self.scan_rot_tolerance,
        )
        self.static_geometric_feasible_mask = result.feasible_mask
        self.static_geometric_feasibility_rows = result.diagnostic_rows
        self.assignment_feasible_mask_base = self.static_geometric_feasible_mask.clone()
        self.manual_feasibility_override_rows = []
        if self._apply_fixed_12_mvp_override:
            self._apply_fixed_12_manual_feasibility_override()
        self.feasibility_diagnostic_rows = self._build_final_feasibility_rows()

    def _apply_fixed_12_manual_feasibility_override(self) -> None:
        for agent_name, viewpoint_indices in self.cfg.fixed_12_mvp_infeasible_agent_viewpoints.items():
            agent_index = self.agent_index.get(agent_name)
            if agent_index is None:
                continue
            for viewpoint_index in viewpoint_indices:
                if viewpoint_index >= self.num_viewpoints:
                    continue
                static_feasible = bool(self.static_geometric_feasible_mask[agent_index, viewpoint_index].item())
                level2_reason = None
                for reason_agent, reason_viewpoint_index, reason_text in getattr(
                    self.cfg, "fixed_12_mvp_level2_diagnostic_reasons", ()
                ):
                    if str(reason_agent) == str(agent_name) and int(reason_viewpoint_index) == int(viewpoint_index):
                        level2_reason = str(reason_text)
                        break
                self.assignment_feasible_mask_base[agent_index, viewpoint_index] = False
                self.manual_feasibility_override_rows.append(
                    {
                        "viewpoint_id": int(self.viewpoint_ids[viewpoint_index]),
                        "viewpoint_index": int(viewpoint_index),
                        "agent": str(agent_name),
                        "agent_index": int(agent_index),
                        "static_geometric_feasible": static_feasible,
                        "manual_override": True,
                        "level2_controller_diagnostic_required": static_feasible and level2_reason is None,
                        "level2_controller_diagnostic_available": level2_reason is not None,
                        "reason": (
                            level2_reason
                            if level2_reason is not None
                            else "fixed_12_mvp_manual_override_requires_level2_controller_feasibility_diagnostic"
                            if static_feasible
                            else "fixed_12_mvp_manual_override_confirms_static_geometric_infeasible_pair"
                        ),
                    }
                )

    def _build_final_feasibility_rows(self) -> list[dict]:
        rows = []
        override_by_pair = {
            (row["agent_index"], row["viewpoint_index"]): row for row in self.manual_feasibility_override_rows
        }
        final_mask_cpu = self.assignment_feasible_mask_base.detach().cpu()
        for static_row in self.static_geometric_feasibility_rows:
            row = dict(static_row)
            key = (row["agent_index"], row["viewpoint_index"])
            row["static_geometric_feasible"] = bool(static_row["feasible"])
            row["manual_override"] = key in override_by_pair
            row["level2_controller_diagnostic_required"] = False
            row["level2_controller_diagnostic_available"] = False
            row["feasible"] = bool(final_mask_cpu[key[0], key[1]].item())
            if row["manual_override"]:
                override_row = override_by_pair[key]
                row["level2_controller_diagnostic_required"] = bool(
                    override_row["level2_controller_diagnostic_required"]
                )
                row["level2_controller_diagnostic_available"] = bool(
                    override_row.get("level2_controller_diagnostic_available", False)
                )
                override_reason = override_row["reason"]
                if row["reason_if_false"]:
                    row["reason_if_false"] = f"{row['reason_if_false']};{override_reason}"
                else:
                    row["reason_if_false"] = override_reason
            elif not row["feasible"] and not row["reason_if_false"]:
                row["reason_if_false"] = "static_geometric_feasibility_failed_without_specific_reason"
            rows.append(row)
        return rows
