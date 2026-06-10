# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
import torch
from collections.abc import Sequence
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
from .static_feasibility import generate_static_geometric_feasibility
from .viewpoint_csv import VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv


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
    action_spaces = {"robot_0": 9, "robot_1": 9, "robot_2": 9}

    # Observation dimensions must match the concatenation layout in `_get_observations()`. Update both places together
    # if new observation terms are added.
    observation_spaces = {"robot_0": 96, "robot_1": 96, "robot_2": 96}

    # `state_space = -1` asks DirectMARLEnv to build the shared state by concatenating all agent observations.
    state_space = -1
    state_spaces = {f"robot_{i}": 0 for i in range(3)}
    possible_agents = ["robot_0", "robot_1", "robot_2"]

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

    enable_usd_debug_visuals = True
    use_camera_light_in_gui = True

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

    # Heterogeneous robot capability parameters. Tuple index 0/1/2 maps to robot_0/robot_1/robot_2 respectively.
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


def _validate_viewpoint_pose_tuple(value, *, index: int) -> tuple[float, float, float, float, float, float, float]:
    pose = _as_float_tuple(value, name=f"viewpoint_poses[{index}]", length=7)
    quat_norm = math.sqrt(sum(item * item for item in pose[3:7]))
    if quat_norm <= 1.0e-8:
        raise ValueError(f"viewpoint_poses[{index}] quaternion must be non-zero.")
    return pose


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
        _prepare_component_mesh_cfg(cfg)
        _prepare_component_proxy_cfg(cfg)
        _prepare_viewpoint_cfg(cfg)
        super().__init__(cfg, render_mode, **kwargs)

        self.num_agents_cfg = len(self.cfg.possible_agents)
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
        self._reset_diagnostics_printed = False
        self._log_static_configuration()

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

        return {
            "num_envs": self.num_envs,
            "num_agents": self.num_agents_cfg,
            "num_viewpoints": self.num_viewpoints,
            "viewpoint_ids": self.viewpoint_ids,
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
            "static_geometric_feasibility_rows": self.static_geometric_feasibility_rows,
            "manual_feasibility_override_rows": self.manual_feasibility_override_rows,
            "feasibility_diagnostic_rows": self.feasibility_diagnostic_rows,
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

        # Keep the large component translucent and matte so robots behind it remain visible without specular glare.
        make_material("scan_component_blue", (0.2, 0.45, 0.9), opacity=0.35, roughness=1.0, specular_color=(0.0, 0.0, 0.0))
        make_material("scan_component_mesh_gray", (0.62, 0.65, 0.68), opacity=1.0, roughness=0.8, specular_color=(0.02, 0.02, 0.02))
        make_material("scan_robot_red", (0.9, 0.2, 0.2))
        make_material("scan_robot_green", (0.2, 0.8, 0.3))
        make_material("scan_robot_yellow", (0.9, 0.75, 0.2))
        make_material("scan_scanner_white", (0.95, 0.95, 0.95))
        make_material("scan_viewpoint_cyan", (0.0, 0.85, 1.0))

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
        add_component_obj_visual(f"{root_path}/MeasuredComponentObjVisual")

        robot_materials = ("scan_robot_red", "scan_robot_green", "scan_robot_yellow")
        for index, pose in enumerate(self.cfg.base_start_poses):
            add_cube(
                f"{root_path}/Robot_{index}_BaseMarker",
                (pose[0], pose[1], pose[2]),
                (0.65, 0.45, 0.25),
                robot_materials[index],
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

    def _update_usd_debug_visuals(self):
        """Update USD markers from high-level task-space buffers."""
        if not self._should_update_usd_debug_visuals():
            return

        # USD writes are useful in GUI and in camera-enabled headless video. Pure headless training/evaluation skips
        # this path to avoid extra overhead and any dependency on rendering state.
        from pxr import Gf, UsdGeom

        stage = self.scene.stage
        for env_index, env_path in enumerate(self.scene.env_prim_paths):
            for agent_index in range(self.num_agents_cfg):
                base_prim = stage.GetPrimAtPath(f"{env_path}/Robot_{agent_index}_BaseMarker")
                scanner_prim = stage.GetPrimAtPath(f"{env_path}/Robot_{agent_index}_ScannerMarker")
                if base_prim.IsValid():
                    base_pos = self.base_pos[env_index, agent_index].detach().cpu().tolist()
                    base_yaw = float(self.base_yaw[env_index, agent_index].detach().cpu())
                    UsdGeom.XformCommonAPI(base_prim).SetTranslate(Gf.Vec3d(*base_pos))
                    UsdGeom.XformCommonAPI(base_prim).SetRotate(
                        (0.0, 0.0, math.degrees(base_yaw)), UsdGeom.XformCommonAPI.RotationOrderXYZ
                    )
                if scanner_prim.IsValid():
                    scanner_pos = self.scanner_pos[env_index, agent_index].detach().cpu().tolist()
                    UsdGeom.XformCommonAPI(scanner_prim).SetTranslate(Gf.Vec3d(*scanner_pos))

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
        """Build per-agent observations with the fixed 96D layout declared in the config."""
        coverage_ratio = self.viewpoints_covered.float().mean(dim=-1, keepdim=True)
        observations = {}
        for agent, index in self.agent_index.items():
            # 96D layout:
            # base_rel(3), yaw sin/cos(2), scanner_rel(3), scanner_quat(4), coverage(1), capability(4),
            # nearest viewpoint slots(8 * 8), other scanners(2 * 3), previous action(9).
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
            observations[agent] = torch.cat(
                (
                    base_rel,
                    yaw_sincos,
                    scanner_rel,
                    self.scanner_quat[:, index, :],
                    coverage_ratio,
                    capability,
                    viewpoint_obs,
                    torch.cat(other_scanners, dim=-1),
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
