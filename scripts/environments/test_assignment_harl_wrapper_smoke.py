# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Short headless smoke for the repo-local assignment HARL wrapper."""

"""Launch Isaac Sim Simulator first."""

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ISAACLAB_TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks"
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
for source_path in (ISAACLAB_TASKS_SOURCE, SCAN_TASK_SOURCE):
    if str(source_path) not in sys.path:
        sys.path.insert(0, str(source_path))

from scenario_config import load_scenario_config, smoke_defaults_from_config, validate_smoke_args

from isaaclab.app import AppLauncher

pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="Smoke-test assignment-aware HARL wrapper for the scan task.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--max_steps", type=int, default=2, help="Maximum number of wrapper.step calls.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--viewpoint_csv_path", type=str, default=None, help="Optional fixed-N viewpoint CSV path.")
parser.add_argument("--expect_num_viewpoints", type=int, default=None, help="Assert the loaded viewpoint count.")
parser.add_argument("--robot_config_path", type=str, default=None, help="Optional Robot Config MVP YAML path.")
parser.add_argument("--capability_config_path", type=str, default=None, help="Optional capability profile YAML path.")
parser.add_argument(
    "--robot_visual_mode",
    type=str,
    choices=("mesh", "debug_marker", "none"),
    default=None,
    help="Robot visual mode: mesh, debug_marker, or none.",
)
parser.add_argument(
    "--component_visual_mode",
    type=str,
    choices=("mesh", "bbox", "none"),
    default=None,
    help="Component visual mode: mesh, bbox, or none.",
)
parser.add_argument(
    "--gui_camera_enabled",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Set a default GUI viewport camera when not headless.",
)
parser.add_argument("--gui_camera_eye", nargs=3, type=float, default=None, help="GUI camera eye position.")
parser.add_argument("--gui_camera_target", nargs=3, type=float, default=None, help="GUI camera look-at target.")
parser.add_argument(
    "--ground_grid_enabled",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Draw a visual-only USD ground grid for GUI inspection.",
)
parser.add_argument("--ground_grid_half_extent", type=float, default=None, help="Ground grid half extent in meters.")
parser.add_argument("--ground_grid_spacing", type=float, default=None, help="Ground grid line spacing in meters.")
parser.add_argument("--ground_grid_z", type=float, default=None, help="Ground grid z height in meters.")
parser.add_argument("--ground_grid_line_width", type=float, default=None, help="Ground grid USD curve width.")
parser.add_argument("--result_file", type=str, default=None, help="Optional JSON file for smoke diagnostics.")
parser.add_argument(
    "--pause_after_setup",
    "--gui_pause",
    action="store_true",
    default=False,
    help="Run a GUI-safe timed pause after reset and initial diagnostics.",
)
parser.add_argument(
    "--pause_after_setup_seconds",
    type=float,
    default=0.0,
    help="GUI-safe setup inspection pause duration. If <= 0 with --pause_after_setup, defaults to 300 seconds.",
)
parser.add_argument("--component_mesh_path", type=str, default=None, help="Optional visual-only component OBJ path.")
parser.add_argument("--component_mesh_format", type=str, default=None, help="Component mesh format; currently obj.")
parser.add_argument("--component_mesh_unit", type=str, default=None, help="Explicit component mesh unit; currently mm.")
parser.add_argument("--component_mesh_scale", nargs=3, type=float, default=None, help="Component mesh xyz scale.")
parser.add_argument("--component_mesh_position", nargs=3, type=float, default=None, help="Component mesh xyz position.")
parser.add_argument(
    "--component_mesh_orientation",
    nargs=4,
    type=float,
    default=None,
    help="Component mesh quaternion in qw qx qy qz order.",
)
parser.add_argument(
    "--component_mesh_orientation_format",
    type=str,
    default=None,
    help="Component mesh quaternion format; currently qwxyz.",
)
parser.add_argument(
    "--component_mesh_visible",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Whether to create the visual-only mesh prim.",
)
parser.add_argument(
    "--align_base_center_to_world_origin",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Set mesh translation so the scaled/rotated mesh base center is at world origin.",
)
parser.add_argument(
    "--component_proxy_auto_from_mesh",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Compute bbox proxy center/half_extents from transformed mesh bounds.",
)
parser.add_argument("--component_proxy_type", type=str, default=None, help="Component proxy type; currently bbox.")
parser.add_argument("--component_proxy_padding", type=float, default=None, help="Auto bbox proxy padding in meters.")
parser.add_argument(
    "--component_proxy_visual_visible",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Whether to show the translucent bbox proxy debug visual.",
)
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli = parser.parse_args()
validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_state import status_counts
from isaaclab_tasks.utils import parse_env_cfg


def _assert_available_actions(wrapper, available_actions: torch.Tensor) -> None:
    if available_actions is None:
        raise AssertionError("available_actions must not be None")
    expected_shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1)
    if tuple(available_actions.shape) != expected_shape:
        raise AssertionError(f"available_actions shape mismatch: expected {expected_shape}, got {tuple(available_actions.shape)}")
    if available_actions.dtype != torch.float32:
        raise AssertionError(f"available_actions dtype mismatch: expected torch.float32, got {available_actions.dtype}")
    if not torch.all(available_actions[..., -1] == 1.0):
        raise AssertionError("no-op available_actions column must be all ones")


def _assert_action_spaces(wrapper) -> None:
    expected_n = wrapper.num_viewpoints + 1
    for agent_id, space in wrapper.action_space.items():
        if space.__class__.__name__ != "Discrete":
            raise AssertionError(f"agent {agent_id} action space must be Discrete, got {space}")
        if space.n != expected_n:
            raise AssertionError(f"agent {agent_id} Discrete n mismatch: expected {expected_n}, got {space.n}")


def _make_manual_discrete_actions(wrapper) -> torch.Tensor:
    actions = wrapper.make_action_tensor()
    actions.fill_(float(wrapper.noop_action_id))
    actions[:, 0, 0] = 0.0
    if wrapper.num_agents > 1:
        actions[:, 1, 0] = 1.0 if wrapper.num_viewpoints > 1 else float(wrapper.noop_action_id)
    if wrapper.num_agents > 2:
        actions[:, 2, 0] = float(wrapper.noop_action_id)
    return actions


def _assert_decoded_assignment(wrapper, actions: torch.Tensor) -> torch.Tensor:
    assignment = wrapper.decode_actions(actions)
    expected_shape = (wrapper.num_envs, wrapper.num_agents)
    if tuple(assignment.shape) != expected_shape:
        raise AssertionError(f"assignment shape mismatch: expected {expected_shape}, got {tuple(assignment.shape)}")
    if assignment.dtype != torch.long:
        raise AssertionError(f"assignment dtype mismatch: expected torch.long, got {assignment.dtype}")
    if wrapper.num_agents > 2 and not torch.all(assignment[:, 2] == -1):
        raise AssertionError("agent 2 no-op action id did not decode to -1")
    return assignment


def _assert_env_actions(wrapper, env_actions: dict[str, torch.Tensor]) -> None:
    expected_agents = set(wrapper.agents)
    if set(env_actions.keys()) != expected_agents:
        raise AssertionError(f"env action agents mismatch: expected {expected_agents}, got {set(env_actions.keys())}")
    for agent, action in env_actions.items():
        expected_shape = (wrapper.num_envs, 9)
        if tuple(action.shape) != expected_shape:
            raise AssertionError(f"{agent} env action shape mismatch: expected {expected_shape}, got {tuple(action.shape)}")
        if not torch.isfinite(action).all():
            raise AssertionError(f"{agent} env action contains non-finite values")
        if torch.any(action < -1.0) or torch.any(action > 1.0):
            raise AssertionError(f"{agent} env action contains values outside [-1, 1]")


def _selected_valid_count(wrapper) -> float:
    selected_available = wrapper.last_selected_available_mask
    if selected_available is None:
        return 0.0
    return float(selected_available.to(dtype=torch.float32).sum().item())


def _resolve_pause_after_setup() -> tuple[bool, bool, float, str]:
    requested_seconds = max(0.0, float(getattr(args_cli, "pause_after_setup_seconds", 0.0)))
    requested = bool(args_cli.pause_after_setup or requested_seconds > 0.0)
    if not requested:
        return False, False, 0.0, "disabled"
    if bool(getattr(args_cli, "headless", False)):
        return True, False, requested_seconds, "headless_skip"
    pause_seconds = requested_seconds if requested_seconds > 0.0 else 300.0
    return True, True, pause_seconds, "timed_app_update"


def _run_gui_safe_setup_pause(pause_seconds: float) -> None:
    print(f"[PAUSE] GUI inspection pause for {pause_seconds:.1f} seconds.")
    print("The GUI should remain responsive.")
    print("Inspect:")
    print("  /World/envs/env_0/ObstacleDebugLines")
    print("  /World/envs/env_0/ObstacleDebugLines/BlockedPath_000")
    print("Use Frame Selected in the Stage panel.")
    print("The smoke run will continue automatically when the timer expires.")

    deadline = time.monotonic() + pause_seconds
    next_status_time = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        simulation_app.update()
        now = time.monotonic()
        if now >= next_status_time:
            remaining = max(0.0, deadline - now)
            print(f"[PAUSE] GUI inspection pause remaining: {remaining:.0f} seconds.")
            next_status_time += 30.0

    print("[PAUSE-END] GUI inspection pause finished; continuing smoke run.")


def _obstacle_diagnostics_summary(problem: dict, *, agents: list[str], viewpoint_ids: list[int]) -> dict:
    summary = {
        "obstacle_diagnostics_enabled": bool(problem.get("obstacle_diagnostics_enabled", False)),
        "obstacle_source": problem.get("obstacle_source"),
        "obstacle_diagnostics_mode": problem.get("obstacle_diagnostics_mode"),
    }
    footprint = problem.get("component_obstacle_footprint_diagnostics")
    if footprint:
        summary["component_obstacle_footprint_diagnostics"] = footprint
        for key in (
            "footprint_resolution",
            "footprint_inflation_radius",
            "line_sample_step",
            "footprint_bounds_xy",
            "footprint_grid_shape",
            "occupied_cell_count",
            "inflated_occupied_cell_count",
        ):
            if key in footprint:
                summary[key] = footprint[key]

    intersection_mask = problem.get("mesh_footprint_intersection_mask")
    aware_cost = problem.get("mesh_footprint_aware_cost_matrix")
    penalty_matrix = problem.get("mesh_footprint_penalty_matrix")
    straight_line_cost = problem.get("straight_line_cost_matrix")
    if isinstance(intersection_mask, torch.Tensor):
        mask = intersection_mask.to(dtype=torch.bool)
        summary["mesh_footprint_intersection_shape"] = list(mask.shape)
        summary["mesh_footprint_intersection_count"] = int(mask.sum().item())
        blocked_pairs = []
        for index in torch.nonzero(mask, as_tuple=False)[:10].detach().cpu().tolist():
            env_id, agent_id, viewpoint_index = [int(value) for value in index]
            pair = {
                "env_id": env_id,
                "robot_name": agents[agent_id] if agent_id < len(agents) else str(agent_id),
                "viewpoint_id": viewpoint_ids[viewpoint_index]
                if viewpoint_index < len(viewpoint_ids)
                else viewpoint_index,
            }
            if isinstance(straight_line_cost, torch.Tensor):
                pair["straight_line_cost"] = float(straight_line_cost[env_id, agent_id, viewpoint_index].item())
            if isinstance(aware_cost, torch.Tensor):
                pair["obstacle_aware_cost"] = float(aware_cost[env_id, agent_id, viewpoint_index].item())
            blocked_pairs.append(pair)
        summary["blocked_pairs_sample"] = blocked_pairs
    if isinstance(straight_line_cost, torch.Tensor):
        summary["straight_line_cost_matrix_shape"] = list(straight_line_cost.shape)
    if isinstance(penalty_matrix, torch.Tensor):
        summary["mesh_footprint_penalty_matrix_shape"] = list(penalty_matrix.shape)
    if isinstance(aware_cost, torch.Tensor):
        summary["mesh_footprint_aware_cost_shape"] = list(aware_cost.shape)
    for key in (
        "obstacle_debug_visualization_enabled",
        "obstacle_debug_visualization_draw_in_headless",
        "obstacle_debug_visualization_line_source",
        "obstacle_debug_visualization_max_lines_per_robot",
        "obstacle_debug_visualization_max_total_lines",
        "obstacle_debug_visualization_prefer_shortest_blocked_pairs",
        "obstacle_debug_visualization_line_z_mode",
        "obstacle_debug_visualization_line_z_value",
        "obstacle_debug_visualization_line_z_offset",
        "obstacle_debug_visualization_line_width",
        "obstacle_debug_visualization_drawn_line_count",
        "obstacle_debug_visualization_skipped_reason",
        "obstacle_debug_visualization_pairs_sample",
        "obstacle_debug_visualization_line_prim_paths_sample",
        "selected_assignment_debug_visualization_enabled",
        "selected_assignment_debug_visualization_line_count",
        "selected_assignment_debug_visualization_pairs_sample",
        "selected_assignment_debug_visualization_intersection_count",
        "selected_assignment_debug_visualization_skipped_reason",
    ):
        if key in problem:
            summary[key] = problem[key]
    return summary


def _inter_robot_conflict_diagnostics_summary(problem: dict) -> dict:
    summary = {}
    for key in (
        "inter_robot_conflict_diagnostics_enabled",
        "inter_robot_conflict_diagnostics_mode",
        "inter_robot_conflict_robot_footprint_radius",
        "inter_robot_conflict_safety_margin",
        "inter_robot_target_conflict_enabled",
        "inter_robot_target_conflict_radius",
        "inter_robot_target_conflict_safety_margin",
        "inter_robot_conflict_debug_visualization_enabled",
        "inter_robot_conflict_debug_visualization_draw_in_headless",
        "inter_robot_conflict_debug_visualization_max_lines",
        "inter_robot_conflict_debug_visualization_line_width",
        "inter_robot_conflict_skipped_reason",
        "inter_robot_overlap_pairs_sample",
    ):
        if key in problem:
            summary[key] = problem[key]
    for key in (
        "inter_robot_overlap_pair_count",
        "inter_robot_min_distance",
        "inter_robot_min_clearance",
        "inter_robot_overlap_any",
    ):
        value = problem.get(key)
        if isinstance(value, torch.Tensor):
            summary[f"{key}_shape"] = list(value.shape)
            summary[f"{key}_sample"] = value.detach().cpu().flatten()[:10].tolist()
    return summary


def _reset_diagnostics(
    wrapper,
    available_actions: torch.Tensor,
    completed_steps: int,
    *,
    pause_after_setup_requested: bool = False,
    pause_after_setup_applied: bool = False,
    pause_after_setup_seconds: float = 0.0,
    pause_after_setup_mode: str = "disabled",
) -> dict:
    problem = wrapper.unwrapped.get_assignment_problem()
    feasible = problem["feasible_mask"].to(dtype=torch.bool)
    available_mask = problem["available_mask"].to(dtype=torch.bool)
    cost_matrix = problem["cost_matrix"]
    static_feasible = problem.get("static_geometric_feasible_mask", feasible).to(dtype=torch.bool)
    task_status = problem["task_status"].to(dtype=torch.long)
    robot_status = problem["robot_status"].to(dtype=torch.long)
    expected_assignment_shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints)
    expected_task_status_shape = (wrapper.num_envs, wrapper.num_viewpoints)
    expected_robot_status_shape = (wrapper.num_envs, wrapper.num_agents)
    if tuple(available_mask.shape) != expected_assignment_shape:
        raise AssertionError(
            f"available_mask shape mismatch: expected {expected_assignment_shape}, got {tuple(available_mask.shape)}"
        )
    if tuple(cost_matrix.shape) != expected_assignment_shape:
        raise AssertionError(
            f"cost_matrix shape mismatch: expected {expected_assignment_shape}, got {tuple(cost_matrix.shape)}"
        )
    if tuple(task_status.shape) != expected_task_status_shape:
        raise AssertionError(
            f"task_status shape mismatch: expected {expected_task_status_shape}, got {tuple(task_status.shape)}"
        )
    if tuple(robot_status.shape) != expected_robot_status_shape:
        raise AssertionError(
            f"robot_status shape mismatch: expected {expected_robot_status_shape}, got {tuple(robot_status.shape)}"
        )
    task_status_names = problem.get("task_status_names", {})
    robot_status_names = problem.get("robot_status_names", {})
    viewpoint_ids = list(problem.get("viewpoint_ids", range(wrapper.num_viewpoints)))

    def _agents_per_viewpoint(mask: torch.Tensor) -> dict:
        first_env_mask = mask[0]
        result = {}
        for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
            result[str(viewpoint_id)] = [
                agent
                for agent_id, agent in enumerate(wrapper.agents)
                if bool(first_env_mask[agent_id, viewpoint_index].item())
            ]
        return result

    static_feasible_agents_per_viewpoint = _agents_per_viewpoint(static_feasible)
    feasible_agents_per_viewpoint = _agents_per_viewpoint(feasible)
    final_rows = list(problem.get("feasibility_diagnostic_rows", []))
    static_rows = list(problem.get("static_geometric_feasibility_rows", []))
    manual_override_rows = list(problem.get("manual_feasibility_override_rows", []))
    mesh_diagnostics = None
    if hasattr(wrapper.unwrapped, "get_component_mesh_diagnostics"):
        mesh_diagnostics = wrapper.unwrapped.get_component_mesh_diagnostics()
    scenario_diagnostics = problem.get("scenario_diagnostics", {})
    if not scenario_diagnostics and hasattr(wrapper.unwrapped, "get_scenario_diagnostics"):
        scenario_diagnostics = wrapper.unwrapped.get_scenario_diagnostics()
    robot_config_diagnostics = None
    if hasattr(wrapper.unwrapped, "get_robot_config_diagnostics"):
        robot_config_diagnostics = wrapper.unwrapped.get_robot_config_diagnostics()
    robot_visual_diagnostics = problem.get("robot_visual_diagnostics", {})
    capability_diagnostics = problem.get("capability_diagnostics", {})
    if not capability_diagnostics and hasattr(wrapper.unwrapped, "get_capability_diagnostics"):
        capability_diagnostics = wrapper.unwrapped.get_capability_diagnostics()
    infeasible_rows = [row for row in final_rows if not row.get("feasible", False)]
    infeasible_rows_missing_reason = [row for row in infeasible_rows if not row.get("reason_if_false")]
    if infeasible_rows_missing_reason:
        raise AssertionError(f"infeasible feasibility rows must include reason_if_false: {infeasible_rows_missing_reason}")

    for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
        if not feasible_agents_per_viewpoint[str(viewpoint_id)]:
            raise AssertionError(f"viewpoint {viewpoint_id} has zero feasible agents")

    env_has_feasible_agent = feasible.any(dim=1)
    unavailable_indices = torch.nonzero(~env_has_feasible_agent.any(dim=0), as_tuple=False).flatten()
    permanently_unavailable = [viewpoint_ids[int(index.item())] for index in unavailable_indices.detach().cpu()]
    result = {
        "num_envs": wrapper.num_envs,
        "num_agents": wrapper.num_agents,
        "num_viewpoints": wrapper.num_viewpoints,
        "noop_id": wrapper.noop_action_id,
        "scenario_config_path": scenario_diagnostics.get("scenario_config_path"),
        "scenario_name": scenario_diagnostics.get("scenario_name"),
        "scenario_type": scenario_diagnostics.get("scenario_type"),
        "robot_visual_mode": scenario_diagnostics.get("robot_visual_mode"),
        "component_visual_mode": scenario_diagnostics.get("component_visual_mode"),
        "robot_visual_mesh_enabled": scenario_diagnostics.get("robot_visual_mesh_enabled"),
        "component_mesh_enabled": scenario_diagnostics.get("component_mesh_enabled"),
        "component_proxy_type": scenario_diagnostics.get("component_proxy_type"),
        "component_proxy_center": scenario_diagnostics.get("component_proxy_center"),
        "component_proxy_half_extents": scenario_diagnostics.get("component_proxy_half_extents"),
        "available_actions_shape": list(available_actions.shape),
        "available_mask_shape": list(available_mask.shape),
        "cost_matrix_shape": list(cost_matrix.shape),
        "task_status_shape": list(task_status.shape),
        "robot_status_shape": list(robot_status.shape),
        "task_status_counts": status_counts(task_status, task_status_names),
        "robot_status_counts": status_counts(robot_status, robot_status_names),
        "task_status_names": task_status_names,
        "robot_status_names": robot_status_names,
        "viewpoint_csv_path": getattr(wrapper.unwrapped.cfg, "viewpoint_csv_path", None),
        "viewpoint_ids": viewpoint_ids,
        "static_geometric_feasible_agents_per_viewpoint": static_feasible_agents_per_viewpoint,
        "feasible_agents_per_viewpoint": feasible_agents_per_viewpoint,
        "permanently_unavailable_viewpoints": permanently_unavailable,
        "static_geometric_feasibility_rows": static_rows,
        "manual_feasibility_override_rows": manual_override_rows,
        "feasibility_diagnostic_rows": final_rows,
        "infeasible_rows": infeasible_rows,
        "completed_steps": completed_steps,
        "pause_after_setup_requested": bool(pause_after_setup_requested),
        "pause_after_setup_applied": bool(pause_after_setup_applied),
        "pause_after_setup_seconds": float(pause_after_setup_seconds),
        "pause_after_setup_mode": pause_after_setup_mode,
    }
    if scenario_diagnostics:
        result["scenario_diagnostics"] = scenario_diagnostics
    if mesh_diagnostics is not None:
        result.update(mesh_diagnostics)
    if robot_config_diagnostics:
        result["robot_config_diagnostics"] = robot_config_diagnostics
    if robot_visual_diagnostics:
        result["robot_visual_diagnostics"] = robot_visual_diagnostics
    if capability_diagnostics:
        result["capability_diagnostics"] = capability_diagnostics
    result.update(_obstacle_diagnostics_summary(problem, agents=list(wrapper.agents), viewpoint_ids=viewpoint_ids))
    result.update(_inter_robot_conflict_diagnostics_summary(problem))
    return result


def main() -> None:
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if args_cli.align_base_center_to_world_origin and args_cli.component_mesh_position is not None:
        raise ValueError(
            "--align_base_center_to_world_origin cannot be combined with --component_mesh_position. "
            "Use one world-origin convention at a time."
        )

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    for attr in ("scenario_config_path", "scenario_name", "scenario_type"):
        value = getattr(args_cli, attr, None)
        if value is not None:
            setattr(env_cfg, attr, value)
    if args_cli.viewpoint_csv_path is not None:
        env_cfg.viewpoint_csv_path = args_cli.viewpoint_csv_path
    if args_cli.robot_config_path is not None:
        env_cfg.robot_config_path = args_cli.robot_config_path
    if args_cli.capability_config_path is not None:
        env_cfg.capability_config_path = args_cli.capability_config_path
    if args_cli.robot_visual_mode is not None:
        env_cfg.robot_visual_mode = args_cli.robot_visual_mode
    if args_cli.component_visual_mode is not None:
        env_cfg.component_visual_mode = args_cli.component_visual_mode
    if args_cli.gui_camera_enabled is not None:
        env_cfg.gui_camera_enabled = bool(args_cli.gui_camera_enabled)
    if args_cli.gui_camera_eye is not None:
        env_cfg.gui_camera_eye = tuple(args_cli.gui_camera_eye)
    if args_cli.gui_camera_target is not None:
        env_cfg.gui_camera_target = tuple(args_cli.gui_camera_target)
    for attr in (
        "ground_grid_enabled",
        "ground_grid_half_extent",
        "ground_grid_spacing",
        "ground_grid_z",
        "ground_grid_line_width",
    ):
        value = getattr(args_cli, attr, None)
        if value is not None:
            setattr(env_cfg, attr, value)
    if args_cli.component_mesh_path is not None:
        env_cfg.component_mesh_path = args_cli.component_mesh_path
    if args_cli.component_mesh_format is not None:
        env_cfg.component_mesh_format = args_cli.component_mesh_format
    if args_cli.component_mesh_unit is not None:
        env_cfg.component_mesh_unit = args_cli.component_mesh_unit
    if args_cli.component_mesh_scale is not None:
        env_cfg.component_mesh_scale = tuple(args_cli.component_mesh_scale)
    if args_cli.component_mesh_position is not None:
        env_cfg.component_mesh_position = tuple(args_cli.component_mesh_position)
    if args_cli.component_mesh_orientation is not None:
        env_cfg.component_mesh_orientation = tuple(args_cli.component_mesh_orientation)
    if args_cli.component_mesh_orientation_format is not None:
        env_cfg.component_mesh_orientation_format = args_cli.component_mesh_orientation_format
    if args_cli.component_mesh_visible is not None:
        env_cfg.component_mesh_visible = bool(args_cli.component_mesh_visible)
    if args_cli.align_base_center_to_world_origin:
        env_cfg.component_mesh_align_base_center_to_world_origin = True
    if args_cli.component_proxy_type is not None:
        env_cfg.component_proxy_type = args_cli.component_proxy_type
    if args_cli.component_proxy_auto_from_mesh is not None:
        env_cfg.component_proxy_auto_from_mesh = bool(args_cli.component_proxy_auto_from_mesh)
    if args_cli.component_proxy_padding is not None:
        env_cfg.component_proxy_padding = float(args_cli.component_proxy_padding)
    if args_cli.component_proxy_visual_visible is not None:
        env_cfg.component_proxy_visual_visible = bool(args_cli.component_proxy_visual_visible)
    for attr in (
        "obstacle_diagnostics_enabled",
        "obstacle_diagnostics_mode",
        "obstacle_source",
        "obstacle_footprint_resolution",
        "obstacle_footprint_inflation_radius",
        "obstacle_line_sample_step",
        "obstacle_blocked_path_penalty",
        "obstacle_debug_visualization_enabled",
        "obstacle_debug_visualization_draw_in_headless",
        "obstacle_debug_visualization_line_source",
        "obstacle_debug_visualization_max_lines_per_robot",
        "obstacle_debug_visualization_max_total_lines",
        "obstacle_debug_visualization_prefer_shortest_blocked_pairs",
        "obstacle_debug_visualization_line_z_mode",
        "obstacle_debug_visualization_line_z_value",
        "obstacle_debug_visualization_line_z_offset",
        "obstacle_debug_visualization_line_width",
        "inter_robot_conflict_diagnostics_enabled",
        "inter_robot_conflict_diagnostics_mode",
        "inter_robot_conflict_robot_footprint_radius",
        "inter_robot_conflict_safety_margin",
        "inter_robot_target_conflict_enabled",
        "inter_robot_target_conflict_radius",
        "inter_robot_target_conflict_safety_margin",
        "inter_robot_conflict_debug_visualization_enabled",
        "inter_robot_conflict_debug_visualization_draw_in_headless",
        "inter_robot_conflict_debug_visualization_max_lines",
        "inter_robot_conflict_debug_visualization_line_width",
    ):
        value = getattr(args_cli, attr, None)
        if value is not None:
            setattr(env_cfg, attr, value)

    wrapper = None
    (
        pause_after_setup_requested,
        pause_after_setup_applied,
        pause_after_setup_seconds,
        pause_after_setup_mode,
    ) = _resolve_pause_after_setup()
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        if args_cli.expect_num_viewpoints is not None and wrapper.num_viewpoints != args_cli.expect_num_viewpoints:
            raise AssertionError(
                f"num_viewpoints mismatch: expected {args_cli.expect_num_viewpoints}, got {wrapper.num_viewpoints}"
            )
        obs, shared_obs, available_actions = wrapper.reset(seed=args_cli.seed)
        if not isinstance(obs, dict) or set(obs.keys()) != set(wrapper.agents):
            raise AssertionError(f"reset obs must be an agent dict with keys {wrapper.agents}, got {list(obs.keys())}")
        if shared_obs.shape[0] != wrapper.num_envs or shared_obs.shape[1] != wrapper.num_agents:
            raise AssertionError(f"shared_obs leading shape mismatch: got {tuple(shared_obs.shape)}")
        _assert_action_spaces(wrapper)
        _assert_available_actions(wrapper, available_actions)

        discrete_actions = _make_manual_discrete_actions(wrapper)
        assignment = _assert_decoded_assignment(wrapper, discrete_actions)
        env_actions = wrapper.assignment_to_env_actions(assignment)
        _assert_env_actions(wrapper, env_actions)

        duplicate_count = wrapper.last_duplicate_count
        duplicate_count = duplicate_count if duplicate_count is not None else torch.zeros(wrapper.num_envs, device=wrapper.device)
        noop_count = (assignment < 0).sum(dim=1).to(dtype=torch.float32)
        available_viewpoint_count = available_actions[..., :-1].sum(dim=-1)
        print(
            "[INFO]: reset ok "
            f"num_envs={wrapper.num_envs} num_agents={wrapper.num_agents} "
            f"num_viewpoints={wrapper.num_viewpoints} noop_id={wrapper.noop_action_id} "
            f"available_shape={tuple(available_actions.shape)} "
            f"available_viewpoints_per_agent={available_viewpoint_count.detach().cpu().tolist()}"
        )
        print(
            "[INFO]: manual decode ok "
            f"assignment={assignment.detach().cpu().tolist()} "
            f"duplicate_count={duplicate_count.detach().cpu().tolist()} "
            f"noop_count={noop_count.detach().cpu().tolist()}"
        )

        if pause_after_setup_requested:
            if not pause_after_setup_applied:
                print("[PAUSE-SKIP] --pause_after_setup requested but the run is headless.")
            else:
                _reset_diagnostics(
                    wrapper,
                    available_actions,
                    completed_steps=0,
                    pause_after_setup_requested=pause_after_setup_requested,
                    pause_after_setup_applied=pause_after_setup_applied,
                    pause_after_setup_seconds=pause_after_setup_seconds,
                    pause_after_setup_mode=pause_after_setup_mode,
                )
                _run_gui_safe_setup_pause(pause_after_setup_seconds)

        completed_steps = 0
        for step_id in range(args_cli.max_steps):
            obs, shared_obs, rewards, dones, info, available_actions = wrapper.step(discrete_actions)
            completed_steps = step_id + 1
            _assert_available_actions(wrapper, available_actions)
            if tuple(rewards.shape) != (wrapper.num_envs, wrapper.num_agents, 1):
                raise AssertionError(f"reward shape mismatch: got {tuple(rewards.shape)}")
            if tuple(dones.shape) != (wrapper.num_envs, wrapper.num_agents):
                raise AssertionError(f"done shape mismatch: got {tuple(dones.shape)}")
            if "assignment_rl" not in info:
                raise AssertionError("step info must contain assignment_rl diagnostics")

            duplicate_count = wrapper.last_duplicate_count
            noop_count = wrapper.last_noop_count
            valid_action_count = wrapper.last_valid_action_count
            if duplicate_count is None or noop_count is None or valid_action_count is None:
                raise AssertionError("wrapper did not populate assignment diagnostics")

            print(
                f"[STEP {step_id + 1}]: "
                f"reward_mean={float(rewards.mean().item()):.6f} "
                f"done_any={bool(dones.any().item())} "
                f"duplicate_count={duplicate_count.detach().cpu().tolist()} "
                f"noop_count={noop_count.detach().cpu().tolist()} "
                f"valid_action_count={valid_action_count.detach().cpu().tolist()} "
                f"selected_valid_count={_selected_valid_count(wrapper):.1f} "
                f"available_shape={tuple(available_actions.shape)}"
            )

        if args_cli.result_file is not None:
            result = _reset_diagnostics(
                wrapper,
                available_actions,
                completed_steps,
                pause_after_setup_requested=pause_after_setup_requested,
                pause_after_setup_applied=pause_after_setup_applied,
                pause_after_setup_seconds=pause_after_setup_seconds,
                pause_after_setup_mode=pause_after_setup_mode,
            )
            result_path = Path(args_cli.result_file)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        print("[OK] assignment HARL wrapper smoke passed")
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
