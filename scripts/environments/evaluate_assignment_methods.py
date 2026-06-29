# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unified fixed-N assignment method evaluation.

This Stage 4A script evaluates assignment baselines on the same scan
environment, fixed viewpoint set, feasible mask, and episode accounting. It does
not train and does not modify HARL internals.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import torch

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


CONFLICT_AWARE_METHODS = ("greedy_conflict_aware", "nearest_conflict_aware")
METHODS = ("random", "nearest", "greedy", *CONFLICT_AWARE_METHODS)

pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="Evaluate fixed-N scan assignment baseline methods.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Task name.")
parser.add_argument("--methods", nargs="+", default=["random", "nearest", "greedy"], choices=METHODS)
parser.add_argument("--algorithm", type=str, default="happo", choices=("happo", "hatrpo", "haa2c"))
parser.add_argument(
    "--assignment_checkpoint_dir",
    type=str,
    default=None,
    help="Disabled in Stage 4A; assignment-RL evaluation is intentionally not supported.",
)
parser.add_argument(
    "--assignment_rl",
    action="store_true",
    help="Disabled in Stage 4A; assignment-RL evaluation is intentionally not supported.",
)
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--num_episodes", type=int, default=1, help="Total episode records to collect per method.")
parser.add_argument("--max_steps", type=int, default=320, help="Script-level episode step cap.")
parser.add_argument("--seed", type=int, default=None, help="Optional seed.")
parser.add_argument(
    "--output_dir",
    type=str,
    default=None,
    help=(
        "Output directory. If omitted, writes under results/assignment_evaluation/ with a scenario-safe run name."
    ),
)
parser.add_argument("--output_name", type=str, default=None, help="Optional safe run folder name under --output_dir.")
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
parser.add_argument(
    "--viewpoint_candidate_top_k",
    type=int,
    default=-1,
    help="Solver candidate limit per env/agent. <=0 uses all available viewpoints; >0 keeps nearest-k candidates.",
)
parser.add_argument(
    "--level2_pair_filter_json",
    type=str,
    default=None,
    help=(
        "Optional Level 2 diagnostics JSON. When provided, evaluator baselines deny only agent-viewpoint pairs "
        "that appear in the JSON with covered=false. Unchecked pairs remain unchanged."
    ),
)
parser.add_argument(
    "--assignment_retry_fallback",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Evaluator-only cooldown for repeated same agent-viewpoint assignments with no coverage gain.",
)
parser.add_argument(
    "--assignment_stall_window",
    type=int,
    default=30,
    help="Consecutive same-pair steps without coverage gain before retry/fallback cooldown is triggered.",
)
parser.add_argument(
    "--assignment_pair_cooldown",
    type=int,
    default=60,
    help="Episode-local cooldown duration for a stalled agent-viewpoint pair.",
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
parser.add_argument(
    "--append_csv",
    action="store_true",
    help="Append new per-episode rows to an existing output_dir/per_episode.csv and recompute summary.csv.",
)
parser.add_argument(
    "--write_assignment_history",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Write assignment_history.csv with per-step method/env/agent assignment diagnostics.",
)
parser.add_argument(
    "--write_controller_state_trace",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Write controller_state_trace.csv for selected full-episode agent-viewpoint pairs.",
)
parser.add_argument(
    "--controller_trace_pairs",
    nargs="*",
    default=[],
    help="Numeric AGENT_ID:VIEWPOINT_ID pairs to trace, for example 1:1 2:12.",
)
parser.add_argument(
    "--controller_trace_agent_viewpoint_pairs",
    nargs="*",
    default=[],
    help="Named AGENT_NAME:VIEWPOINT_ID pairs to trace, for example robot_1:1 robot_2:12.",
)
parser.add_argument("--print_diagnostics_steps", type=int, default=5, help="Leading assignment-RL steps to print.")
parser.add_argument(
    "--diagnostic_interval",
    type=int,
    default=0,
    help="Print assignment-RL diagnostics every N steps after the leading window. 0 disables interval printing.",
)
parser.add_argument(
    "--compare_obstacle_aware_candidates",
    action="store_true",
    default=False,
    help=(
        "Diagnostic-only: compare nearest/greedy baseline choices against choices from a copied problem whose "
        "cost_matrix is mesh_footprint_aware_cost_matrix. Does not change actual solver inputs."
    ),
)
AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli, hydra_args = parser.parse_known_args()
validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)
sys.argv = [sys.argv[0]] + hydra_args
print(
    f"[INFO]: evaluate_assignment_methods methods={args_cli.methods} "
    f"scenario_config={SCENARIO_CONFIG.get('_scenario_config_path')} "
    f"robot_config_path={getattr(args_cli, 'robot_config_path', None)} "
    f"capability_config_path={getattr(args_cli, 'capability_config_path', None)} "
    f"robot_visual_mode={getattr(args_cli, 'robot_visual_mode', None)} "
    f"component_visual_mode={getattr(args_cli, 'component_visual_mode', None)} "
    f"viewpoint_candidate_top_k={args_cli.viewpoint_candidate_top_k} "
    f"candidate_mode={'all_viewpoints' if int(args_cli.viewpoint_candidate_top_k) <= 0 else 'nearest_top_k'} "
    f"level2_pair_filter_json={args_cli.level2_pair_filter_json} "
    f"assignment_retry_fallback={bool(args_cli.assignment_retry_fallback)} "
    f"assignment_stall_window={args_cli.assignment_stall_window} "
    f"assignment_pair_cooldown={args_cli.assignment_pair_cooldown} "
    f"compare_obstacle_aware_candidates={bool(args_cli.compare_obstacle_aware_candidates)} "
    f"target_conflict_candidate_comparison={bool(getattr(args_cli, 'target_conflict_candidate_comparison_enabled', False))} "
    f"conflict_aware_baseline={bool(getattr(args_cli, 'conflict_aware_baseline_enabled', False))} "
    f"write_controller_state_trace={bool(args_cli.write_controller_state_trace)} "
    f"controller_trace_pairs={args_cli.controller_trace_pairs or args_cli.controller_trace_agent_viewpoint_pairs}",
    flush=True,
)


def _warm_start_torch_cuda(args: argparse.Namespace) -> None:
    """Initialize PyTorch/cuBLAS before Isaac Kit owns the CUDA context."""
    device_arg = str(getattr(args, "device", "cuda:0")).lower()
    if device_arg == "cpu" or not device_arg.startswith("cuda") or not torch.cuda.is_available():
        return

    device = torch.device(device_arg)
    torch.cuda.set_device(device)
    probe = torch.zeros((1, 1), device=device)
    layer = torch.nn.Linear(1, 1).to(device)
    _ = layer(probe)
    torch.cuda.synchronize(device)


_warm_start_torch_cuda(args_cli)

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import numpy as np

from harl.algorithms.actors import ALGO_REGISTRY
from harl.utils.models_tools import init_device

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg
from isaaclab.utils.math import quat_apply, quat_error_magnitude

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import compute_assignment_duplicate_count
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_state import status_counts
from isaaclab_tasks.direct.scan_mobile_manipulator.solvers import make_solver
from isaaclab_tasks.utils.hydra import hydra_task_config


algorithm = args_cli.algorithm.lower()
agent_cfg_entry_point = f"harl_{algorithm}_cfg_entry_point"


PER_EPISODE_FIELDS = [
    "method",
    "episode",
    "episode_return",
    "final_coverage",
    "final_covered_count",
    "final_covered_viewpoint_ids",
    "final_uncovered_viewpoint_ids",
    "success",
    "steps_to_full_coverage",
    "first_full_coverage_step",
    "coverage_auc",
    "duplicate_count_mean",
    "noop_rate",
    "valid_action_rate",
    "new_viewpoints_total",
    "episode_length",
    "per_robot_selected_count",
    "per_robot_completed_count",
    "per_robot_repeated_assignment_count",
    "per_viewpoint_attempted_count",
    "last_global_coverage_gain_step",
    "steps_since_last_global_coverage_gain",
    "no_progress_steps_after_last_gain",
    "duplicate_selected_target_count",
    "duplicate_selected_target_rate",
    "noop_when_available_count",
    "noop_when_available_rate",
    "selected_path_cost_mean",
    "selected_path_cost_max",
    "selected_path_cost_sum",
    "load_balance_selected_std",
    "load_balance_completed_std",
    "late_repeated_assignment_pattern",
    "inter_robot_overlap_step_count",
    "inter_robot_overlap_rate",
    "inter_robot_overlap_pair_count_total",
    "inter_robot_min_distance_min",
    "inter_robot_min_distance_mean",
    "inter_robot_min_clearance_min",
    "inter_robot_min_clearance_mean",
    "selected_target_conflict_step_count",
    "selected_target_conflict_rate",
    "selected_target_conflict_pair_count_total",
    "selected_target_min_distance_min",
    "selected_target_min_distance_mean",
    "selected_target_min_clearance_min",
    "selected_target_min_clearance_mean",
    "selected_target_skipped_robot_count_total",
    "selected_target_valid_robot_count_mean",
    "actual_base_motion_intersection_step_count",
    "actual_base_motion_intersection_rate",
    "actual_base_motion_intersection_pair_count_total",
    "actual_base_motion_intersection_pair_count_mean",
    "actual_base_motion_min_distance_to_footprint_min",
    "actual_base_motion_min_distance_to_footprint_mean",
    "actual_base_motion_valid_robot_count_mean",
    "actual_base_motion_skipped_robot_count_total",
    "baseline_selected_target_conflict_step_count",
    "baseline_selected_target_conflict_rate_mean",
    "baseline_selected_target_conflict_pair_count_total",
    "baseline_selected_target_min_distance_min",
    "baseline_selected_target_min_clearance_min",
    "baseline_selected_target_conflict_penalty_sum_total",
    "candidate_selected_target_conflict_step_count",
    "candidate_selected_target_conflict_rate_mean",
    "candidate_selected_target_conflict_pair_count_total",
    "candidate_selected_target_min_distance_min",
    "candidate_selected_target_min_clearance_min",
    "candidate_selected_target_conflict_penalty_sum_total",
    "candidate_changed_assignment_rate_mean",
    "candidate_changed_assignment_count_total",
    "conflict_aware_solver_enabled",
    "conflict_aware_fallback_step_count",
    "conflict_aware_fallback_rate",
    "conflict_aware_candidate_combination_count_mean",
    "conflict_aware_selected_score_mean",
    "conflict_aware_selected_unary_cost_sum_mean",
    "conflict_aware_selected_target_conflict_pair_count_total",
    "conflict_aware_selected_target_conflict_penalty_sum_total",
    "conflict_aware_selected_duplicate_pair_count_total",
    "conflict_aware_changed_vs_base_count_total",
    "conflict_aware_changed_vs_base_rate_mean",
]

SUMMARY_FIELDS = [
    "method",
    "episodes",
    "success_rate",
    "mean_return",
    "mean_final_coverage",
    "mean_steps_to_full_coverage",
    "mean_coverage_auc",
    "mean_duplicate_count",
    "mean_noop_rate",
    "mean_valid_action_rate",
    "per_robot_selected_count_mean",
    "per_robot_completed_count_mean",
    "per_robot_repeated_assignment_count_mean",
    "per_viewpoint_attempted_count_sum",
    "mean_steps_since_last_global_coverage_gain",
    "mean_no_progress_steps_after_last_gain",
    "duplicate_selected_target_count_total",
    "duplicate_selected_target_rate_mean",
    "noop_when_available_count_total",
    "noop_when_available_rate_mean",
    "selected_path_cost_mean",
    "selected_path_cost_max",
    "selected_path_cost_sum_total",
    "load_balance_selected_std_mean",
    "load_balance_completed_std_mean",
    "late_repeated_assignment_pattern_summary",
    "inter_robot_overlap_step_count_total",
    "inter_robot_overlap_rate_mean",
    "inter_robot_overlap_pair_count_total",
    "inter_robot_min_distance_min",
    "inter_robot_min_distance_mean",
    "inter_robot_min_clearance_min",
    "inter_robot_min_clearance_mean",
    "selected_target_conflict_step_count_total",
    "selected_target_conflict_rate_mean",
    "selected_target_conflict_pair_count_total",
    "selected_target_min_distance_min",
    "selected_target_min_distance_mean",
    "selected_target_min_clearance_min",
    "selected_target_min_clearance_mean",
    "selected_target_skipped_robot_count_total",
    "selected_target_valid_robot_count_mean",
    "actual_base_motion_intersection_step_count_total",
    "actual_base_motion_intersection_rate_mean",
    "actual_base_motion_intersection_pair_count_total",
    "actual_base_motion_intersection_pair_count_mean",
    "actual_base_motion_min_distance_to_footprint_min",
    "actual_base_motion_min_distance_to_footprint_mean",
    "actual_base_motion_valid_robot_count_mean",
    "actual_base_motion_skipped_robot_count_total",
    "baseline_selected_target_conflict_step_count",
    "baseline_selected_target_conflict_rate_mean",
    "baseline_selected_target_conflict_pair_count_total",
    "baseline_selected_target_min_distance_min",
    "baseline_selected_target_min_clearance_min",
    "baseline_selected_target_conflict_penalty_sum_total",
    "candidate_selected_target_conflict_step_count",
    "candidate_selected_target_conflict_rate_mean",
    "candidate_selected_target_conflict_pair_count_total",
    "candidate_selected_target_min_distance_min",
    "candidate_selected_target_min_clearance_min",
    "candidate_selected_target_conflict_penalty_sum_total",
    "candidate_changed_assignment_rate_mean",
    "candidate_changed_assignment_count_total",
    "conflict_aware_solver_enabled",
    "conflict_aware_fallback_step_count_total",
    "conflict_aware_fallback_rate_mean",
    "conflict_aware_candidate_combination_count_mean",
    "conflict_aware_selected_score_mean",
    "conflict_aware_selected_unary_cost_sum_mean",
    "conflict_aware_selected_target_conflict_pair_count_total",
    "conflict_aware_selected_target_conflict_penalty_sum_total",
    "conflict_aware_selected_duplicate_pair_count_total",
    "conflict_aware_changed_vs_base_count_total",
    "conflict_aware_changed_vs_base_rate_mean",
]

ASSIGNMENT_HISTORY_FIELDS = [
    "method",
    "episode",
    "step",
    "env_id",
    "agent_id",
    "assigned_viewpoint_id",
    "is_noop",
    "selected_available",
    "available_viewpoint_count",
    "noop_when_available",
    "is_repeated_assignment",
    "selected_path_cost",
    "duplicate_selected_target_count_step",
    "covered_before_count",
    "covered_after_count",
    "newly_covered_viewpoint_ids",
    "coverage_count",
    "coverage_ratio",
    "assigned_viewpoint_was_covered_before",
    "assigned_viewpoint_covered_after",
    "pair_in_cooldown_before_selection",
    "cooldown_event_triggered",
    "cooldown_remaining_after_step",
    "stall_count_before_step",
    "stall_count_after_step",
    "actual_base_motion_intersects_component",
    "actual_base_motion_distance",
]

_FOOTPRINT_CELL_CENTER_CACHE: dict[int, tuple[tuple[float, float], ...]] = {}

RETRY_FALLBACK_EVENT_FIELDS = [
    "method",
    "episode",
    "step",
    "env_id",
    "agent_id",
    "viewpoint_id",
    "reason",
    "stall_window",
    "cooldown_duration",
    "coverage_count_when_triggered",
]

CONTROLLER_STATE_TRACE_FIELDS = [
    "method",
    "episode",
    "step",
    "env_id",
    "agent_id",
    "agent_name",
    "viewpoint_id",
    "assigned_viewpoint_id",
    "is_pair_selected_this_step",
    "is_noop",
    "coverage_count",
    "coverage_ratio",
    "assigned_viewpoint_was_covered_before",
    "assigned_viewpoint_covered_after",
    "newly_covered_viewpoint_ids",
    "robot_base_x",
    "robot_base_y",
    "robot_base_z",
    "ee_x",
    "ee_y",
    "ee_z",
    "target_x",
    "target_y",
    "target_z",
    "position_error",
    "rotation_error",
    "range_value",
    "range_margin",
    "fov_alignment",
    "position_gate_ok",
    "rotation_gate_ok",
    "range_gate_ok",
    "fov_alignment_gate_ok",
    "position_rotation_gate_ok",
    "all_coverage_gates_ok",
    "controller_target_changed_this_step",
    "consecutive_steps_assigned_to_same_viewpoint",
    "cooldown_active_for_pair",
    "cooldown_remaining",
]

CONTROLLER_STATE_TRACE_SUMMARY_FIELDS = [
    "method",
    "agent_id",
    "agent_name",
    "viewpoint_id",
    "assigned_steps",
    "first_assigned_step",
    "last_assigned_step",
    "num_assignment_segments",
    "max_consecutive_assigned_steps",
    "ever_position_gate_ok",
    "ever_rotation_gate_ok",
    "ever_range_gate_ok",
    "ever_fov_alignment_gate_ok",
    "ever_position_rotation_gate_ok",
    "ever_all_coverage_gates_ok",
    "ever_covered_after_assignment",
    "min_position_error",
    "min_rotation_error",
    "max_range_margin",
    "max_fov_alignment",
    "num_target_switches",
    "num_cooldown_interruptions",
    "likely_failure_mode",
]


def _set_global_seeds(seed: int | None) -> None:
    if seed is None:
        return
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _clone_env_cfg(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg):
    cfg = copy.deepcopy(env_cfg)
    cfg.scene.num_envs = args_cli.num_envs
    if hasattr(cfg, "sim") and hasattr(cfg.sim, "device"):
        cfg.sim.device = args_cli.device
    if hasattr(cfg, "sim") and hasattr(cfg.sim, "use_fabric"):
        cfg.sim.use_fabric = not bool(getattr(args_cli, "disable_fabric", False))
    if args_cli.seed is not None:
        cfg.seed = args_cli.seed
    for attr in ("scenario_config_path", "scenario_name", "scenario_type"):
        value = getattr(args_cli, attr, None)
        if value is not None:
            setattr(cfg, attr, value)
    if args_cli.viewpoint_csv_path is not None:
        cfg.viewpoint_csv_path = args_cli.viewpoint_csv_path
    if args_cli.robot_config_path is not None:
        cfg.robot_config_path = args_cli.robot_config_path
    if args_cli.capability_config_path is not None:
        cfg.capability_config_path = args_cli.capability_config_path
    if args_cli.robot_visual_mode is not None:
        cfg.robot_visual_mode = args_cli.robot_visual_mode
    if args_cli.component_visual_mode is not None:
        cfg.component_visual_mode = args_cli.component_visual_mode
    if args_cli.gui_camera_enabled is not None:
        cfg.gui_camera_enabled = bool(args_cli.gui_camera_enabled)
    if args_cli.gui_camera_eye is not None:
        cfg.gui_camera_eye = tuple(args_cli.gui_camera_eye)
    if args_cli.gui_camera_target is not None:
        cfg.gui_camera_target = tuple(args_cli.gui_camera_target)
    for attr in (
        "ground_grid_enabled",
        "ground_grid_half_extent",
        "ground_grid_spacing",
        "ground_grid_z",
        "ground_grid_line_width",
    ):
        value = getattr(args_cli, attr, None)
        if value is not None:
            setattr(cfg, attr, value)
    if args_cli.component_mesh_path is not None:
        cfg.component_mesh_path = args_cli.component_mesh_path
    if args_cli.component_mesh_format is not None:
        cfg.component_mesh_format = args_cli.component_mesh_format
    if args_cli.component_mesh_unit is not None:
        cfg.component_mesh_unit = args_cli.component_mesh_unit
    if args_cli.component_mesh_scale is not None:
        cfg.component_mesh_scale = tuple(args_cli.component_mesh_scale)
    if args_cli.component_mesh_position is not None:
        cfg.component_mesh_position = tuple(args_cli.component_mesh_position)
    if args_cli.component_mesh_orientation is not None:
        cfg.component_mesh_orientation = tuple(args_cli.component_mesh_orientation)
    if args_cli.component_mesh_orientation_format is not None:
        cfg.component_mesh_orientation_format = args_cli.component_mesh_orientation_format
    if args_cli.component_mesh_visible is not None:
        cfg.component_mesh_visible = bool(args_cli.component_mesh_visible)
    if args_cli.align_base_center_to_world_origin:
        cfg.component_mesh_align_base_center_to_world_origin = True
    if args_cli.component_proxy_type is not None:
        cfg.component_proxy_type = args_cli.component_proxy_type
    if args_cli.component_proxy_auto_from_mesh is not None:
        cfg.component_proxy_auto_from_mesh = bool(args_cli.component_proxy_auto_from_mesh)
    if args_cli.component_proxy_padding is not None:
        cfg.component_proxy_padding = float(args_cli.component_proxy_padding)
    if args_cli.component_proxy_visual_visible is not None:
        cfg.component_proxy_visual_visible = bool(args_cli.component_proxy_visual_visible)
    for attr in (
        "obstacle_diagnostics_enabled",
        "obstacle_diagnostics_mode",
        "obstacle_source",
        "obstacle_footprint_resolution",
        "obstacle_footprint_inflation_radius",
        "obstacle_line_sample_step",
        "obstacle_blocked_path_penalty",
        "actual_base_motion_obstacle_diagnostics_enabled",
        "actual_base_motion_obstacle_diagnostics_mode",
        "actual_base_motion_obstacle_source",
        "actual_base_motion_line_sample_step",
        "actual_base_motion_min_motion_distance",
        "actual_base_motion_max_pairs_sample",
        "actual_base_motion_debug_visualization_enabled",
        "actual_base_motion_debug_visualization_draw_in_headless",
        "actual_base_motion_debug_visualization_max_lines",
        "actual_base_motion_debug_visualization_line_width",
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
            setattr(cfg, attr, value)
    return cfg


def _as_bool_tensor(value: Any, num_envs: int, device: torch.device) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        tensor = value.to(device=device, dtype=torch.bool)
    else:
        tensor = torch.as_tensor(value, dtype=torch.bool, device=device)
    tensor = tensor.flatten()
    if tensor.numel() == 1:
        return tensor.expand(num_envs)
    if tensor.numel() != num_envs:
        raise RuntimeError(f"done tensor size mismatch: expected {num_envs}, got {tensor.numel()}")
    return tensor


def _aggregate_done(done: Any, agents: list[str], num_envs: int, device: torch.device) -> torch.Tensor:
    if isinstance(done, torch.Tensor):
        if done.ndim == 2:
            return torch.all(done.to(device=device, dtype=torch.bool), dim=1)
        return _as_bool_tensor(done, num_envs, device)
    if isinstance(done, dict) and "__all__" in done:
        return _as_bool_tensor(done["__all__"], num_envs, device)
    if isinstance(done, dict):
        values = [_as_bool_tensor(done[agent], num_envs, device) for agent in agents if agent in done]
        if values:
            return torch.stack(values, dim=0).all(dim=0)
    return torch.zeros(num_envs, dtype=torch.bool, device=device)


def _sum_reward_dict(rewards: dict[str, torch.Tensor], agents: list[str], num_envs: int, device: torch.device) -> torch.Tensor:
    values = [rewards[agent].to(device=device).reshape(num_envs) for agent in agents]
    return torch.stack(values, dim=0).sum(dim=0)


def _sum_reward_tensor(rewards: torch.Tensor) -> torch.Tensor:
    reward_tensor = rewards.to(dtype=torch.float32)
    if reward_tensor.ndim == 3:
        return reward_tensor.squeeze(-1).sum(dim=1)
    if reward_tensor.ndim == 2:
        return reward_tensor.sum(dim=1)
    return reward_tensor.reshape(reward_tensor.shape[0], -1).sum(dim=1)


def _validate_assignment(problem: dict, assignment: torch.Tensor) -> None:
    expected_shape = (problem["num_envs"], problem["num_agents"])
    if tuple(assignment.shape) != expected_shape:
        raise RuntimeError(f"assignment shape mismatch: expected {expected_shape}, got {tuple(assignment.shape)}")
    if assignment.dtype != torch.long:
        raise RuntimeError(f"assignment dtype mismatch: expected torch.long, got {assignment.dtype}")
    if assignment.device != problem["available_mask"].device:
        raise RuntimeError(f"assignment device mismatch: expected {problem['available_mask'].device}, got {assignment.device}")
    if torch.any(assignment < -1) or torch.any(assignment >= problem["num_viewpoints"]):
        raise RuntimeError("assignment contains values outside [-1, num_viewpoints)")

    valid = _valid_assignment_decisions(problem, assignment)
    invalid_non_noop = (assignment >= 0) & (~valid)
    if bool(invalid_non_noop.any()):
        bad = torch.nonzero(invalid_non_noop, as_tuple=False)[0]
        env_id, agent_id = int(bad[0].item()), int(bad[1].item())
        viewpoint_id = int(assignment[env_id, agent_id].item())
        raise RuntimeError(f"selected unavailable viewpoint {viewpoint_id} for env {env_id}, agent {agent_id}")


def _set_selected_assignment_debug_visualization(unwrapped, assignment: torch.Tensor, problem: dict) -> None:
    setter = getattr(unwrapped, "set_obstacle_debug_selected_assignments", None)
    if callable(setter):
        setter(assignment, problem)


def _update_selected_assignment_debug_runtime_diagnostics(
    diagnostics: dict | None,
    unwrapped,
    *,
    method: str,
    step: torch.Tensor | None,
) -> None:
    if diagnostics is None:
        return
    getter = getattr(unwrapped, "get_obstacle_debug_visualization_diagnostics", None)
    if not callable(getter):
        return
    debug = getter()
    if "selected_assignment_debug_visualization_enabled" not in debug:
        return
    snapshot = dict(debug)
    snapshot["method"] = method
    if isinstance(step, torch.Tensor):
        snapshot["step_by_env"] = [int(value) for value in step.detach().cpu().flatten().tolist()]
    diagnostics["selected_assignment_debug_visualization_latest"] = snapshot


def _zero_conflict_metrics(
    num_envs: int,
    device: torch.device,
    *,
    pair_prefix: str,
    metric_prefix: str,
    skipped_reason: str,
) -> dict:
    pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    min_values = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    return {
        f"{pair_prefix}_pair_count": pair_count,
        f"{pair_prefix}_pairs_sample": [],
        f"{metric_prefix}_min_distance": min_values.clone(),
        f"{metric_prefix}_min_clearance": min_values.clone(),
        f"{pair_prefix}_any": pair_count > 0,
        f"{pair_prefix}_skipped_reason": skipped_reason,
    }


def _selected_target_conflict_diagnostics(problem: dict, assignment: torch.Tensor, viewpoint_ids: list[int]) -> dict:
    num_envs = int(problem["num_envs"])
    num_agents = int(problem["num_agents"])
    device = assignment.device
    diagnostics_enabled = bool(problem.get("inter_robot_conflict_diagnostics_enabled", False))
    target_enabled = bool(problem.get("inter_robot_target_conflict_enabled", False))
    if not diagnostics_enabled:
        metrics = _zero_conflict_metrics(
            num_envs,
            device,
            pair_prefix="selected_target_conflict",
            metric_prefix="selected_target",
            skipped_reason="inter_robot_conflict_diagnostics_disabled",
        )
        metrics["selected_target_valid_robot_count"] = torch.zeros(num_envs, dtype=torch.long, device=device)
        metrics["selected_target_skipped_robot_count"] = torch.full(
            (num_envs,),
            num_agents,
            dtype=torch.long,
            device=device,
        )
        return metrics
    if not target_enabled:
        metrics = _zero_conflict_metrics(
            num_envs,
            device,
            pair_prefix="selected_target_conflict",
            metric_prefix="selected_target",
            skipped_reason="target_conflict_disabled",
        )
        metrics["selected_target_valid_robot_count"] = torch.zeros(num_envs, dtype=torch.long, device=device)
        metrics["selected_target_skipped_robot_count"] = torch.full(
            (num_envs,),
            num_agents,
            dtype=torch.long,
            device=device,
        )
        return metrics

    viewpoint_pos = problem.get("viewpoint_pos")
    if not isinstance(viewpoint_pos, torch.Tensor):
        metrics = _zero_conflict_metrics(
            num_envs,
            device,
            pair_prefix="selected_target_conflict",
            metric_prefix="selected_target",
            skipped_reason="missing_viewpoint_pos",
        )
        metrics["selected_target_valid_robot_count"] = torch.zeros(num_envs, dtype=torch.long, device=device)
        metrics["selected_target_skipped_robot_count"] = torch.full(
            (num_envs,),
            num_agents,
            dtype=torch.long,
            device=device,
        )
        return metrics

    target_radius = float(problem.get("inter_robot_target_conflict_radius", 0.35))
    target_margin = float(problem.get("inter_robot_target_conflict_safety_margin", 0.15))
    threshold = (2.0 * target_radius) + target_margin
    pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    min_distance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    min_clearance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    valid_robot_count = (assignment >= 0).sum(dim=1).to(dtype=torch.long)
    skipped_robot_count = (assignment < 0).sum(dim=1).to(dtype=torch.long)
    pairs_sample: list[dict] = []
    max_sample = 10

    if num_agents >= 2:
        min_distance.fill_(float("inf"))
        min_clearance.fill_(float("inf"))
        has_candidate_pair = torch.zeros(num_envs, dtype=torch.bool, device=device)
        viewpoint_xy = viewpoint_pos[:, :, :2]
        for robot_i in range(num_agents):
            selected_i = assignment[:, robot_i]
            valid_i = selected_i >= 0
            safe_i = selected_i.clamp(min=0)
            target_i = viewpoint_xy[torch.arange(num_envs, device=device), safe_i]
            for robot_j in range(robot_i + 1, num_agents):
                selected_j = assignment[:, robot_j]
                valid_j = selected_j >= 0
                pair_valid = valid_i & valid_j
                if not bool(pair_valid.any()):
                    continue
                safe_j = selected_j.clamp(min=0)
                target_j = viewpoint_xy[torch.arange(num_envs, device=device), safe_j]
                distance = torch.linalg.norm(target_i - target_j, dim=-1)
                clearance = distance - threshold
                conflict = pair_valid & (clearance < 0.0)
                pair_count += conflict.to(dtype=torch.long)
                has_candidate_pair |= pair_valid
                min_distance = torch.where(pair_valid, torch.minimum(min_distance, distance), min_distance)
                min_clearance = torch.where(pair_valid, torch.minimum(min_clearance, clearance), min_clearance)
                if len(pairs_sample) < max_sample and bool(conflict.any()):
                    for env_id in torch.nonzero(conflict, as_tuple=False).flatten().detach().cpu().tolist():
                        if len(pairs_sample) >= max_sample:
                            break
                        viewpoint_i_index = int(selected_i[env_id].item())
                        viewpoint_j_index = int(selected_j[env_id].item())
                        pairs_sample.append(
                            {
                                "env_id": int(env_id),
                                "robot_i": int(robot_i),
                                "robot_j": int(robot_j),
                                "viewpoint_i": viewpoint_ids[viewpoint_i_index]
                                if viewpoint_i_index < len(viewpoint_ids)
                                else viewpoint_i_index,
                                "viewpoint_j": viewpoint_ids[viewpoint_j_index]
                                if viewpoint_j_index < len(viewpoint_ids)
                                else viewpoint_j_index,
                                "distance": float(distance[env_id].item()),
                                "clearance": float(clearance[env_id].item()),
                                "threshold": threshold,
                                "target_conflict_radius_i": target_radius,
                                "target_conflict_radius_j": target_radius,
                                "target_conflict_safety_margin": target_margin,
                            }
                        )
        min_distance = torch.where(has_candidate_pair, min_distance, torch.full_like(min_distance, float("nan")))
        min_clearance = torch.where(has_candidate_pair, min_clearance, torch.full_like(min_clearance, float("nan")))

    return {
        "selected_target_conflict_pair_count": pair_count,
        "selected_target_conflict_pairs_sample": pairs_sample,
        "selected_target_min_distance": min_distance,
        "selected_target_min_clearance": min_clearance,
        "selected_target_conflict_any": pair_count > 0,
        "selected_target_valid_robot_count": valid_robot_count,
        "selected_target_skipped_robot_count": skipped_robot_count,
        "selected_target_conflict_skipped_reason": None,
    }


def _compact_conflict_snapshot(metrics: dict, *, pair_prefix: str, metric_prefix: str) -> dict:
    snapshot = {}
    for key in (
        f"{pair_prefix}_pair_count",
        f"{pair_prefix}_pairs_sample",
        f"{metric_prefix}_min_distance",
        f"{metric_prefix}_min_clearance",
        f"{pair_prefix}_any",
        f"{pair_prefix}_skipped_reason",
    ):
        if key in metrics:
            snapshot[key] = metrics[key]
    if pair_prefix == "inter_robot_overlap" and "inter_robot_conflict_skipped_reason" in metrics:
        snapshot["inter_robot_conflict_skipped_reason"] = metrics["inter_robot_conflict_skipped_reason"]
    return snapshot


def _update_inter_robot_runtime_diagnostics(
    diagnostics: dict | None,
    *,
    method: str,
    step: torch.Tensor,
    current_overlap: dict,
    selected_target: dict,
) -> None:
    if diagnostics is None:
        return
    diagnostics["inter_robot_conflict_runtime_latest"] = {
        "method": method,
        "step_by_env": [int(value) for value in step.detach().cpu().flatten().tolist()],
        "current_robot_overlap": _compact_conflict_snapshot(
            current_overlap,
            pair_prefix="inter_robot_overlap",
            metric_prefix="inter_robot",
        ),
        "selected_target_conflict": _compact_conflict_snapshot(
            selected_target,
            pair_prefix="selected_target_conflict",
            metric_prefix="selected_target",
        ),
        "selected_target_valid_robot_count": selected_target.get("selected_target_valid_robot_count"),
        "selected_target_skipped_robot_count": selected_target.get("selected_target_skipped_robot_count"),
    }


def _target_conflict_candidate_config() -> dict:
    compare_methods = getattr(args_cli, "target_conflict_candidate_compare_methods", None)
    if compare_methods is None:
        compare_methods = ["nearest", "greedy"]
    if isinstance(compare_methods, str):
        compare_methods = [compare_methods]
    compare_methods = [str(method).strip().lower() for method in compare_methods if str(method).strip()]
    return {
        "enabled": bool(getattr(args_cli, "target_conflict_candidate_comparison_enabled", False)),
        "mode": str(getattr(args_cli, "target_conflict_candidate_comparison_mode", "diagnostic_only")).strip().lower(),
        "candidate_generator": str(
            getattr(args_cli, "target_conflict_candidate_generator", "sequential_robot_order")
        ).strip().lower(),
        "robot_order": str(getattr(args_cli, "target_conflict_candidate_robot_order", "robot_index")).strip().lower(),
        "target_conflict_radius": float(getattr(args_cli, "target_conflict_candidate_radius", 0.35)),
        "target_conflict_safety_margin": float(
            getattr(args_cli, "target_conflict_candidate_safety_margin", 0.15)
        ),
        "selected_target_conflict_penalty": float(getattr(args_cli, "target_conflict_candidate_penalty", 100.0)),
        "compare_methods": compare_methods,
        "include_random_as_baseline_only": bool(
            getattr(args_cli, "target_conflict_candidate_include_random_as_baseline_only", True)
        ),
        "max_pairs_sample": int(getattr(args_cli, "target_conflict_candidate_max_pairs_sample", 20)),
    }


def _conflict_aware_baseline_config(method: str | None = None) -> dict:
    configured_methods = getattr(args_cli, "conflict_aware_baseline_methods", None)
    if configured_methods is None:
        methods = list(CONFLICT_AWARE_METHODS)
    else:
        methods = [str(value).strip().lower() for value in configured_methods]

    configured_enabled = getattr(args_cli, "conflict_aware_baseline_enabled", None)
    if configured_enabled is None:
        enabled = method in CONFLICT_AWARE_METHODS if method is not None else False
    else:
        enabled = bool(configured_enabled)
    if method is not None:
        enabled = bool(enabled and str(method).strip().lower() in methods)

    return {
        "enabled": enabled,
        "methods": methods,
        "mode": str(getattr(args_cli, "conflict_aware_baseline_mode", "gated_solver_variant")).strip().lower(),
        "top_k": int(getattr(args_cli, "conflict_aware_baseline_top_k", 10)),
        "target_conflict_radius": float(getattr(args_cli, "conflict_aware_baseline_target_conflict_radius", 0.35)),
        "target_conflict_safety_margin": float(
            getattr(args_cli, "conflict_aware_baseline_target_conflict_safety_margin", 0.15)
        ),
        "target_conflict_penalty": float(getattr(args_cli, "conflict_aware_baseline_target_conflict_penalty", 100.0)),
        "duplicate_penalty": float(getattr(args_cli, "conflict_aware_baseline_duplicate_penalty", 1_000_000.0)),
        "fallback_to_base_method": bool(
            getattr(args_cli, "conflict_aware_baseline_fallback_to_base_method", True)
        ),
        "max_pairs_sample": int(getattr(args_cli, "conflict_aware_baseline_max_pairs_sample", 20)),
    }


def _attach_conflict_aware_baseline_config(problem: dict, *, method: str | None) -> dict:
    config = _conflict_aware_baseline_config(method)
    updated = dict(problem)
    updated.update(
        {
            "conflict_aware_baseline_enabled": bool(config["enabled"]),
            "conflict_aware_baseline_methods": tuple(config["methods"]),
            "conflict_aware_baseline_mode": config["mode"],
            "conflict_aware_top_k": int(config["top_k"]),
            "conflict_aware_target_conflict_radius": float(config["target_conflict_radius"]),
            "conflict_aware_target_conflict_safety_margin": float(config["target_conflict_safety_margin"]),
            "conflict_aware_target_conflict_penalty": float(config["target_conflict_penalty"]),
            "conflict_aware_duplicate_penalty": float(config["duplicate_penalty"]),
            "conflict_aware_fallback_to_base_method": bool(config["fallback_to_base_method"]),
            "conflict_aware_max_pairs_sample": int(config["max_pairs_sample"]),
        }
    )
    return updated


def _target_conflict_threshold(config: dict) -> float:
    return (2.0 * float(config["target_conflict_radius"])) + float(config["target_conflict_safety_margin"])


def _target_conflict_required_tensors(problem: dict) -> tuple[dict[str, torch.Tensor] | None, str | None]:
    required = {
        "cost_matrix": problem.get("cost_matrix"),
        "available_mask": problem.get("available_mask"),
        "viewpoint_pos": problem.get("viewpoint_pos"),
    }
    missing = [name for name, value in required.items() if not isinstance(value, torch.Tensor)]
    if missing:
        return None, f"missing_required_tensors:{','.join(missing)}"
    cost_shape = tuple(required["cost_matrix"].shape)
    if tuple(required["available_mask"].shape) != cost_shape:
        return None, f"available_mask_shape_mismatch expected={cost_shape} got={tuple(required['available_mask'].shape)}"
    expected_viewpoint_shape = (cost_shape[0], cost_shape[2])
    if tuple(required["viewpoint_pos"].shape[:2]) != expected_viewpoint_shape:
        return None, (
            "viewpoint_pos_shape_mismatch "
            f"expected_prefix={expected_viewpoint_shape} got={tuple(required['viewpoint_pos'].shape)}"
        )
    return required, None


def _target_conflict_assignment_metrics(
    *,
    assignment: torch.Tensor,
    viewpoint_pos: torch.Tensor,
    viewpoint_ids: list[int],
    agents: list[str],
    config: dict,
    max_pairs_sample: int | None = None,
) -> dict:
    num_envs, num_agents = assignment.shape
    device = assignment.device
    threshold = _target_conflict_threshold(config)
    penalty_value = float(config["selected_target_conflict_penalty"])
    max_pairs_sample = int(config["max_pairs_sample"] if max_pairs_sample is None else max_pairs_sample)

    pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    conflict_pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    min_distance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    min_clearance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    penalty_sum = torch.zeros(num_envs, dtype=torch.float32, device=device)
    conflict_pairs_sample: list[dict] = []

    if num_agents < 2:
        return {
            "pair_count": pair_count,
            "conflict_pair_count": conflict_pair_count,
            "conflict_rate": torch.zeros(num_envs, dtype=torch.float32, device=device),
            "min_distance": min_distance,
            "min_clearance": min_clearance,
            "penalty_sum": penalty_sum,
            "conflict_pairs_sample": conflict_pairs_sample,
        }

    min_distance.fill_(float("inf"))
    min_clearance.fill_(float("inf"))
    has_pair = torch.zeros(num_envs, dtype=torch.bool, device=device)
    viewpoint_xy = viewpoint_pos[:, :, :2]
    env_indices = torch.arange(num_envs, device=device)
    for robot_i in range(num_agents):
        selected_i = assignment[:, robot_i]
        valid_i = selected_i >= 0
        safe_i = selected_i.clamp(min=0)
        target_i = viewpoint_xy[env_indices, safe_i]
        for robot_j in range(robot_i + 1, num_agents):
            selected_j = assignment[:, robot_j]
            valid_j = selected_j >= 0
            pair_valid = valid_i & valid_j
            if not bool(pair_valid.any()):
                continue
            safe_j = selected_j.clamp(min=0)
            target_j = viewpoint_xy[env_indices, safe_j]
            distance = torch.linalg.norm(target_i - target_j, dim=-1)
            clearance = distance - threshold
            conflict = pair_valid & (clearance < 0.0)
            pair_count += pair_valid.to(dtype=torch.long)
            conflict_pair_count += conflict.to(dtype=torch.long)
            penalty_sum += conflict.to(dtype=torch.float32) * penalty_value
            has_pair |= pair_valid
            min_distance = torch.where(pair_valid, torch.minimum(min_distance, distance), min_distance)
            min_clearance = torch.where(pair_valid, torch.minimum(min_clearance, clearance), min_clearance)
            if len(conflict_pairs_sample) < max_pairs_sample and bool(conflict.any()):
                for env_id in torch.nonzero(conflict, as_tuple=False).flatten().detach().cpu().tolist():
                    if len(conflict_pairs_sample) >= max_pairs_sample:
                        break
                    viewpoint_i_index = int(selected_i[env_id].item())
                    viewpoint_j_index = int(selected_j[env_id].item())
                    conflict_pairs_sample.append(
                        {
                            "env_id": int(env_id),
                            "robot_i": int(robot_i),
                            "robot_j": int(robot_j),
                            "robot_i_name": agents[robot_i] if robot_i < len(agents) else f"robot_{robot_i}",
                            "robot_j_name": agents[robot_j] if robot_j < len(agents) else f"robot_{robot_j}",
                            "viewpoint_i": _viewpoint_id_from_assignment(viewpoint_ids, viewpoint_i_index),
                            "viewpoint_j": _viewpoint_id_from_assignment(viewpoint_ids, viewpoint_j_index),
                            "distance": float(distance[env_id].item()),
                            "clearance": float(clearance[env_id].item()),
                            "threshold": threshold,
                            "selected_target_conflict_penalty": penalty_value,
                        }
                    )

    min_distance = torch.where(has_pair, min_distance, torch.full_like(min_distance, float("nan")))
    min_clearance = torch.where(has_pair, min_clearance, torch.full_like(min_clearance, float("nan")))
    conflict_rate = conflict_pair_count.to(dtype=torch.float32) / pair_count.clamp(min=1).to(dtype=torch.float32)
    return {
        "pair_count": pair_count,
        "conflict_pair_count": conflict_pair_count,
        "conflict_rate": conflict_rate,
        "min_distance": min_distance,
        "min_clearance": min_clearance,
        "penalty_sum": penalty_sum,
        "conflict_pairs_sample": conflict_pairs_sample,
    }


def _target_conflict_candidate_assignment(problem: dict, *, config: dict) -> tuple[torch.Tensor | None, str | None]:
    tensors, reason = _target_conflict_required_tensors(problem)
    if tensors is None:
        return None, reason
    if config["candidate_generator"] != "sequential_robot_order":
        return None, f"unsupported_candidate_generator:{config['candidate_generator']}"
    if config["robot_order"] != "robot_index":
        return None, f"unsupported_robot_order:{config['robot_order']}"

    cost_matrix = tensors["cost_matrix"]
    available_mask = tensors["available_mask"].to(dtype=torch.bool)
    viewpoint_pos = tensors["viewpoint_pos"]
    num_envs, num_agents, num_viewpoints = cost_matrix.shape
    device = cost_matrix.device
    threshold = _target_conflict_threshold(config)
    penalty_value = float(config["selected_target_conflict_penalty"])
    viewpoint_xy = viewpoint_pos[:, :, :2]
    candidate = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)

    for env_id in range(num_envs):
        selected: list[int] = []
        for robot_id in range(num_agents):
            available_indices = torch.nonzero(available_mask[env_id, robot_id], as_tuple=False).flatten()
            if available_indices.numel() == 0:
                continue
            nonduplicate = [int(index.item()) for index in available_indices if int(index.item()) not in selected]
            candidate_indices = nonduplicate
            if not candidate_indices:
                candidate_indices = [int(index.item()) for index in available_indices]
            best_index = -1
            best_score = float("inf")
            for viewpoint_index in candidate_indices:
                score = float(cost_matrix[env_id, robot_id, viewpoint_index].item())
                for previous_index in selected:
                    distance = torch.linalg.norm(
                        viewpoint_xy[env_id, viewpoint_index] - viewpoint_xy[env_id, previous_index]
                    )
                    if float(distance.item()) < threshold:
                        score += penalty_value
                if score < best_score:
                    best_score = score
                    best_index = viewpoint_index
            if best_index >= 0:
                candidate[env_id, robot_id] = int(best_index)
                selected.append(int(best_index))
    return candidate, "sequential_robot_order_target_conflict_penalty"


def _target_conflict_changed_pairs_sample(
    *,
    baseline_assignment: torch.Tensor,
    candidate_assignment: torch.Tensor,
    cost_matrix: torch.Tensor | None,
    agents: list[str],
    viewpoint_ids: list[int],
    step: torch.Tensor | None,
    episode_index: torch.Tensor | None,
    limit: int,
) -> list[dict]:
    rows = []
    changed = baseline_assignment != candidate_assignment
    for env_id_tensor, agent_id_tensor in torch.nonzero(changed, as_tuple=False):
        if len(rows) >= limit:
            break
        env_id = int(env_id_tensor.item())
        agent_id = int(agent_id_tensor.item())
        baseline_index = int(baseline_assignment[env_id, agent_id].item())
        candidate_index = int(candidate_assignment[env_id, agent_id].item())
        step_value = (
            int(step.flatten()[env_id].item())
            if isinstance(step, torch.Tensor) and step.numel() > env_id
            else None
        )
        episode_value = (
            int(episode_index.flatten()[env_id].item())
            if isinstance(episode_index, torch.Tensor) and episode_index.numel() > env_id
            else None
        )
        rows.append(
            {
                "env_id": env_id,
                "episode_index": episode_value,
                "step": step_value,
                "robot_id": agent_id,
                "robot_name": agents[agent_id] if agent_id < len(agents) else f"robot_{agent_id}",
                "baseline_viewpoint_id": _viewpoint_id_from_assignment(viewpoint_ids, baseline_index),
                "candidate_viewpoint_id": _viewpoint_id_from_assignment(viewpoint_ids, candidate_index),
                "baseline_cost": _assignment_pair_value(cost_matrix, env_id, agent_id, baseline_index),
                "candidate_cost": _assignment_pair_value(cost_matrix, env_id, agent_id, candidate_index),
            }
        )
    return rows


def _target_conflict_metric_total(metrics: dict, key: str, *, as_int: bool = False) -> float | int:
    value = metrics[key]
    total = value.sum().item() if isinstance(value, torch.Tensor) else sum(value)
    return int(total) if as_int else float(total)


def _target_conflict_metric_min(metrics: dict, key: str) -> float:
    value = metrics[key]
    if not isinstance(value, torch.Tensor):
        return float("nan")
    finite = value[torch.isfinite(value)]
    return float(finite.min().item()) if finite.numel() > 0 else float("nan")


def _compare_target_conflict_candidate_step(
    *,
    method: str,
    step: torch.Tensor,
    episode_index: torch.Tensor | None,
    problem: dict,
    baseline_assignment: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
) -> dict:
    config = _target_conflict_candidate_config()
    tensors, tensor_reason = _target_conflict_required_tensors(problem)
    candidate_reason = "disabled"
    candidate_assignment = None
    candidate_available = False
    candidate_metrics = None
    baseline_metrics = None
    decision_count = int(baseline_assignment.numel())
    changed_count = 0
    changed_rate = 0.0

    row = {
        "method": method,
        "steps": 1,
        "target_conflict_candidate_comparison_enabled": bool(config["enabled"]),
        "target_conflict_candidate_available": False,
        "target_conflict_candidate_reason": candidate_reason,
        "candidate_assignment_decision_count": decision_count,
        "candidate_changed_assignment_count": 0,
        "candidate_changed_assignment_rate": 0.0,
        "baseline_selected_target_pair_count": 0,
        "baseline_selected_target_conflict_pair_count": 0,
        "baseline_selected_target_conflict_rate": 0.0,
        "baseline_selected_target_min_distance": float("nan"),
        "baseline_selected_target_min_clearance": float("nan"),
        "baseline_selected_target_conflict_penalty_sum": 0.0,
        "candidate_selected_target_pair_count": 0,
        "candidate_selected_target_conflict_pair_count": 0,
        "candidate_selected_target_conflict_rate": 0.0,
        "candidate_selected_target_min_distance": float("nan"),
        "candidate_selected_target_min_clearance": float("nan"),
        "candidate_selected_target_conflict_penalty_sum": 0.0,
        "candidate_changed_pairs_sample": [],
        "baseline_target_conflict_pairs_sample": [],
        "candidate_target_conflict_pairs_sample": [],
        "step_min": int(step.min().item()) if isinstance(step, torch.Tensor) and step.numel() > 0 else 0,
        "step_max": int(step.max().item()) if isinstance(step, torch.Tensor) and step.numel() > 0 else 0,
        "episode_index_min": (
            int(episode_index.min().item())
            if isinstance(episode_index, torch.Tensor) and episode_index.numel() > 0
            else 0
        ),
        "episode_index_max": (
            int(episode_index.max().item())
            if isinstance(episode_index, torch.Tensor) and episode_index.numel() > 0
            else 0
        ),
    }

    if tensors is None:
        row["target_conflict_candidate_reason"] = tensor_reason
        return row

    baseline_metrics = _target_conflict_assignment_metrics(
        assignment=baseline_assignment,
        viewpoint_pos=tensors["viewpoint_pos"],
        viewpoint_ids=viewpoint_ids,
        agents=agents,
        config=config,
    )
    row.update(
        {
            "baseline_selected_target_pair_count": _target_conflict_metric_total(
                baseline_metrics, "pair_count", as_int=True
            ),
            "baseline_selected_target_conflict_pair_count": _target_conflict_metric_total(
                baseline_metrics, "conflict_pair_count", as_int=True
            ),
            "baseline_selected_target_conflict_rate": float(baseline_metrics["conflict_rate"].mean().item()),
            "baseline_selected_target_min_distance": _target_conflict_metric_min(baseline_metrics, "min_distance"),
            "baseline_selected_target_min_clearance": _target_conflict_metric_min(baseline_metrics, "min_clearance"),
            "baseline_selected_target_conflict_penalty_sum": _target_conflict_metric_total(
                baseline_metrics, "penalty_sum"
            ),
            "baseline_target_conflict_pairs_sample": list(baseline_metrics["conflict_pairs_sample"]),
            "_baseline_pair_count_tensor": baseline_metrics["pair_count"],
            "_baseline_conflict_pair_count_tensor": baseline_metrics["conflict_pair_count"],
            "_baseline_conflict_rate_tensor": baseline_metrics["conflict_rate"],
            "_baseline_min_distance_tensor": baseline_metrics["min_distance"],
            "_baseline_min_clearance_tensor": baseline_metrics["min_clearance"],
            "_baseline_penalty_sum_tensor": baseline_metrics["penalty_sum"],
        }
    )

    if not bool(config["enabled"]):
        row["target_conflict_candidate_reason"] = "disabled"
        return row
    if config["mode"] != "diagnostic_only":
        row["target_conflict_candidate_reason"] = f"unsupported_mode:{config['mode']}"
        return row
    if method not in set(config["compare_methods"]):
        if method == "random" and bool(config["include_random_as_baseline_only"]):
            row["target_conflict_candidate_reason"] = "method_baseline_only:random"
        else:
            row["target_conflict_candidate_reason"] = f"method_not_in_compare_methods:{method}"
        return row

    candidate_assignment, candidate_reason = _target_conflict_candidate_assignment(problem, config=config)
    if candidate_assignment is None:
        row["target_conflict_candidate_reason"] = candidate_reason
        return row
    _validate_assignment(problem, candidate_assignment)
    candidate_available = True
    candidate_metrics = _target_conflict_assignment_metrics(
        assignment=candidate_assignment,
        viewpoint_pos=tensors["viewpoint_pos"],
        viewpoint_ids=viewpoint_ids,
        agents=agents,
        config=config,
    )
    changed_count = int((baseline_assignment != candidate_assignment).sum().item())
    changed_rate = changed_count / float(max(1, decision_count))
    row.update(
        {
            "target_conflict_candidate_available": candidate_available,
            "target_conflict_candidate_reason": candidate_reason,
            "candidate_changed_assignment_count": changed_count,
            "candidate_changed_assignment_rate": changed_rate,
            "candidate_selected_target_pair_count": _target_conflict_metric_total(
                candidate_metrics, "pair_count", as_int=True
            ),
            "candidate_selected_target_conflict_pair_count": _target_conflict_metric_total(
                candidate_metrics, "conflict_pair_count", as_int=True
            ),
            "candidate_selected_target_conflict_rate": float(candidate_metrics["conflict_rate"].mean().item()),
            "candidate_selected_target_min_distance": _target_conflict_metric_min(candidate_metrics, "min_distance"),
            "candidate_selected_target_min_clearance": _target_conflict_metric_min(candidate_metrics, "min_clearance"),
            "candidate_selected_target_conflict_penalty_sum": _target_conflict_metric_total(
                candidate_metrics, "penalty_sum"
            ),
            "candidate_changed_pairs_sample": _target_conflict_changed_pairs_sample(
                baseline_assignment=baseline_assignment,
                candidate_assignment=candidate_assignment,
                cost_matrix=tensors["cost_matrix"],
                agents=agents,
                viewpoint_ids=viewpoint_ids,
                step=step,
                episode_index=episode_index,
                limit=int(config["max_pairs_sample"]),
            ),
            "candidate_target_conflict_pairs_sample": list(candidate_metrics["conflict_pairs_sample"]),
            "_candidate_pair_count_tensor": candidate_metrics["pair_count"],
            "_candidate_conflict_pair_count_tensor": candidate_metrics["conflict_pair_count"],
            "_candidate_conflict_rate_tensor": candidate_metrics["conflict_rate"],
            "_candidate_min_distance_tensor": candidate_metrics["min_distance"],
            "_candidate_min_clearance_tensor": candidate_metrics["min_clearance"],
            "_candidate_penalty_sum_tensor": candidate_metrics["penalty_sum"],
            "_candidate_changed_count_tensor": (baseline_assignment != candidate_assignment).sum(dim=1).to(dtype=torch.long),
            "_candidate_changed_rate_tensor": (
                (baseline_assignment != candidate_assignment).sum(dim=1).to(dtype=torch.float32)
                / float(max(1, baseline_assignment.shape[1]))
            ),
        }
    )
    return row


def _valid_assignment_decisions(problem: dict, assignment: torch.Tensor) -> torch.Tensor:
    valid = assignment < 0
    non_noop = assignment >= 0
    if bool(non_noop.any()):
        safe_assignment = assignment.clamp(min=0).unsqueeze(-1)
        selected_available = torch.gather(problem["available_mask"], dim=2, index=safe_assignment).squeeze(-1)
        valid = valid | (non_noop & selected_available)
    return valid


def _valid_discrete_decisions(available_actions: torch.Tensor, raw_ids: torch.Tensor, noop_id: int) -> torch.Tensor:
    in_range = (raw_ids >= 0) & (raw_ids <= noop_id)
    safe_ids = raw_ids.clamp(min=0, max=noop_id).unsqueeze(-1)
    selected_available = torch.gather(available_actions.to(dtype=torch.bool), dim=2, index=safe_ids).squeeze(-1)
    return in_range & selected_available


def _candidate_mode() -> str:
    return "all_viewpoints" if int(args_cli.viewpoint_candidate_top_k) <= 0 else "nearest_top_k"


_LEVEL2_PAIR_FILTER_CACHE: dict | None = None


def _as_int(value: Any, default: int = -1) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _tensor_value(value: torch.Tensor | float | bool | int) -> float | bool | int:
    if isinstance(value, torch.Tensor):
        if value.dtype == torch.bool:
            return bool(value.item())
        if value.dtype in (torch.int8, torch.int16, torch.int32, torch.int64):
            return int(value.item())
        return float(value.item())
    return value


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _agent_names_from_unwrapped(unwrapped: Any) -> list[str]:
    names = getattr(unwrapped, "agent_names", None)
    if names is None:
        names = getattr(unwrapped, "possible_agents", None)
    if names is None:
        names = unwrapped.cfg.possible_agents
    return list(names)


def _parse_controller_trace_pair_text(pair_text: str, agent_names: list[str], viewpoint_ids: list[int]) -> tuple[int, int]:
    if ":" not in pair_text:
        raise ValueError(f"controller trace pair must use AGENT:VIEWPOINT_ID, got {pair_text!r}")
    agent_text, viewpoint_text = pair_text.split(":", 1)
    agent_text = agent_text.strip()
    viewpoint_text = viewpoint_text.strip()
    if not agent_text or not viewpoint_text:
        raise ValueError(f"controller trace pair must use non-empty AGENT:VIEWPOINT_ID, got {pair_text!r}")

    if agent_text in agent_names:
        agent_id = agent_names.index(agent_text)
    else:
        agent_id = _as_int(agent_text, default=-1)
    if agent_id < 0 or agent_id >= len(agent_names):
        raise ValueError(f"unknown controller trace agent {agent_text!r}; available agents: {agent_names}")

    viewpoint_id = _as_int(viewpoint_text, default=-1)
    if viewpoint_id not in viewpoint_ids:
        raise ValueError(f"unknown controller trace viewpoint id {viewpoint_id}; available ids: {viewpoint_ids}")
    return agent_id, viewpoint_id


def _controller_trace_pairs(agent_names: list[str], viewpoint_ids: list[int]) -> list[tuple[int, int]]:
    pair_texts = list(args_cli.controller_trace_pairs or []) + list(args_cli.controller_trace_agent_viewpoint_pairs or [])
    if not pair_texts:
        return []

    pairs = []
    seen = set()
    for pair_text in pair_texts:
        pair = _parse_controller_trace_pair_text(str(pair_text), agent_names, viewpoint_ids)
        if pair not in seen:
            pairs.append(pair)
            seen.add(pair)
    return pairs


def _init_controller_trace_state(
    *, num_envs: int, num_agents: int, device: torch.device, pairs: list[tuple[int, int]], agent_names: list[str]
) -> dict:
    return {
        "enabled": bool(args_cli.write_controller_state_trace),
        "pairs": pairs,
        "agent_names": agent_names,
        "current_assignment_id": torch.full((num_envs, num_agents), -2, dtype=torch.long, device=device),
        "consecutive_assignment_count": torch.zeros((num_envs, num_agents), dtype=torch.long, device=device),
        "unavailable_fields": set(),
    }


def _reset_controller_trace_state(state: dict | None, env_ids: torch.Tensor) -> None:
    if state is None or not bool(state.get("enabled", False)) or env_ids.numel() == 0:
        return
    state["current_assignment_id"][env_ids] = -2
    state["consecutive_assignment_count"][env_ids] = 0


def _update_controller_trace_assignment_state(
    trace_state: dict | None,
    assignment: torch.Tensor,
    viewpoint_ids: list[int],
) -> dict[tuple[int, int], dict]:
    info: dict[tuple[int, int], dict] = {}
    if trace_state is None or not bool(trace_state.get("enabled", False)):
        return info

    current_assignment_id = trace_state["current_assignment_id"]
    consecutive_count = trace_state["consecutive_assignment_count"]
    num_envs, num_agents = assignment.shape
    for env_id in range(num_envs):
        for agent_id in range(num_agents):
            assigned_index = int(assignment[env_id, agent_id].item())
            assigned_viewpoint_id = -1 if assigned_index < 0 else int(viewpoint_ids[assigned_index])
            previous_viewpoint_id = int(current_assignment_id[env_id, agent_id].item())
            changed = assigned_viewpoint_id != previous_viewpoint_id
            if changed:
                current_assignment_id[env_id, agent_id] = assigned_viewpoint_id
                consecutive_count[env_id, agent_id] = 1
            else:
                consecutive_count[env_id, agent_id] += 1
            info[(env_id, agent_id)] = {
                "controller_target_changed_this_step": bool(changed),
                "consecutive_steps_assigned_to_same_viewpoint": int(consecutive_count[env_id, agent_id].item()),
            }
    return info


def _controller_trace_gate_values(
    unwrapped: Any,
    *,
    env_id: int,
    agent_id: int,
    viewpoint_index: int,
    unavailable_fields: set[str],
) -> dict:
    row = {field: "" for field in CONTROLLER_STATE_TRACE_FIELDS}
    try:
        device = unwrapped.device
        scanner_pos = unwrapped.scanner_pos[env_id, agent_id]
        scanner_quat = unwrapped.scanner_quat[env_id, agent_id]
        base_pos = unwrapped.base_pos[env_id, agent_id]
        target_pos = unwrapped.viewpoint_pos_local[viewpoint_index]
        target_quat = unwrapped.viewpoint_quat[viewpoint_index]

        position_error = torch.linalg.norm(scanner_pos - target_pos)
        rotation_error = quat_error_magnitude(scanner_quat.unsqueeze(0), target_quat.unsqueeze(0))[0]

        proxy_center = unwrapped.component_center.to(device=device)
        proxy_half_extents = unwrapped.component_half_extents.to(device=device)
        scanner_to_box = torch.clamp(torch.abs(scanner_pos - proxy_center) - proxy_half_extents, min=0.0)
        sensor_surface_distance = torch.linalg.norm(scanner_to_box)

        min_range = unwrapped.scanner_min_range[agent_id]
        max_range = unwrapped.scanner_max_range[agent_id]
        min_margin = sensor_surface_distance - min_range
        max_margin = max_range - sensor_surface_distance
        range_margin = torch.minimum(min_margin, max_margin)
        range_ok = (sensor_surface_distance >= min_range) & (sensor_surface_distance <= max_range)

        position_gate_ok = position_error < unwrapped.scan_pos_tolerance[agent_id]
        rotation_gate_ok = rotation_error < unwrapped.scan_rot_tolerance[agent_id]

        forward_axis = torch.tensor([1.0, 0.0, 0.0], device=device)
        scanner_forward = quat_apply(scanner_quat.unsqueeze(0), forward_axis.unsqueeze(0))[0]
        target_forward = quat_apply(target_quat.unsqueeze(0), forward_axis.unsqueeze(0))[0]
        alignment_cos = torch.dot(scanner_forward, target_forward)
        fov_alignment_ok = alignment_cos > unwrapped.scanner_fov_cos[agent_id]

        arm_distance = torch.linalg.norm(target_pos - base_pos)
        arm_margin = unwrapped.arm_reach[agent_id] - arm_distance
        arm_reach_ok = arm_margin >= 0.0

        position_rotation_gate_ok = position_gate_ok & rotation_gate_ok
        all_coverage_gates_ok = position_rotation_gate_ok & range_ok & arm_reach_ok & fov_alignment_ok

        row.update(
            {
                "robot_base_x": _tensor_value(base_pos[0]),
                "robot_base_y": _tensor_value(base_pos[1]),
                "robot_base_z": _tensor_value(base_pos[2]),
                "ee_x": _tensor_value(scanner_pos[0]),
                "ee_y": _tensor_value(scanner_pos[1]),
                "ee_z": _tensor_value(scanner_pos[2]),
                "target_x": _tensor_value(target_pos[0]),
                "target_y": _tensor_value(target_pos[1]),
                "target_z": _tensor_value(target_pos[2]),
                "position_error": _tensor_value(position_error),
                "rotation_error": _tensor_value(rotation_error),
                "range_value": _tensor_value(sensor_surface_distance),
                "range_margin": _tensor_value(range_margin),
                "fov_alignment": _tensor_value(alignment_cos),
                "position_gate_ok": _tensor_value(position_gate_ok),
                "rotation_gate_ok": _tensor_value(rotation_gate_ok),
                "range_gate_ok": _tensor_value(range_ok),
                "fov_alignment_gate_ok": _tensor_value(fov_alignment_ok),
                "position_rotation_gate_ok": _tensor_value(position_rotation_gate_ok),
                "all_coverage_gates_ok": _tensor_value(all_coverage_gates_ok),
            }
        )
    except (AttributeError, IndexError, RuntimeError, KeyError) as exc:
        unavailable_fields.add(f"controller_gate_fields:{type(exc).__name__}:{exc}")
    return {field: row.get(field, "") for field in CONTROLLER_STATE_TRACE_FIELDS}


def _append_controller_state_trace_step(
    pending_trace_by_env: dict[int, list[dict]],
    *,
    unwrapped: Any,
    trace_state: dict,
    method: str,
    step: torch.Tensor,
    assignment: torch.Tensor,
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    viewpoint_ids: list[int],
    retry_state: dict | None,
    assignment_transition_info: dict[tuple[int, int], dict],
) -> None:
    if not bool(trace_state.get("enabled", False)) or not trace_state.get("pairs"):
        return

    num_envs, _ = assignment.shape
    num_viewpoints = len(viewpoint_ids)
    viewpoint_index_by_id = {int(viewpoint_id): index for index, viewpoint_id in enumerate(viewpoint_ids)}
    covered_after_count = covered_after.sum(dim=-1).to(dtype=torch.long)
    newly_covered = covered_after & (~covered_before)
    agent_names = trace_state["agent_names"]

    for env_id in range(num_envs):
        newly_ids = _covered_ids_from_mask(newly_covered[env_id], viewpoint_ids)
        coverage_count = int(covered_after_count[env_id].item())
        coverage_ratio = coverage_count / float(num_viewpoints)
        for agent_id, viewpoint_id in trace_state["pairs"]:
            viewpoint_index = viewpoint_index_by_id[int(viewpoint_id)]
            assigned_index = int(assignment[env_id, agent_id].item())
            is_noop = assigned_index < 0
            assigned_viewpoint_id = -1 if is_noop else int(viewpoint_ids[assigned_index])
            is_pair_selected = assigned_viewpoint_id == int(viewpoint_id)
            cooldown_remaining = 0
            if retry_state is not None and bool(retry_state.get("enabled", False)):
                cooldown_remaining = int(retry_state["cooldown_remaining"][env_id, agent_id, viewpoint_index].item())

            row = _controller_trace_gate_values(
                unwrapped,
                env_id=env_id,
                agent_id=agent_id,
                viewpoint_index=viewpoint_index,
                unavailable_fields=trace_state["unavailable_fields"],
            )
            row.update(
                {
                    "method": method,
                    "episode": -1,
                    "step": int(step[env_id].item()),
                    "env_id": int(env_id),
                    "agent_id": int(agent_id),
                    "agent_name": agent_names[agent_id],
                    "viewpoint_id": int(viewpoint_id),
                    "assigned_viewpoint_id": int(assigned_viewpoint_id),
                    "is_pair_selected_this_step": bool(is_pair_selected),
                    "is_noop": bool(is_noop),
                    "coverage_count": coverage_count,
                    "coverage_ratio": coverage_ratio,
                    "assigned_viewpoint_was_covered_before": bool(covered_before[env_id, viewpoint_index].item()),
                    "assigned_viewpoint_covered_after": bool(covered_after[env_id, viewpoint_index].item()),
                    "newly_covered_viewpoint_ids": json.dumps(newly_ids),
                    "cooldown_active_for_pair": bool(cooldown_remaining > 0),
                    "cooldown_remaining": cooldown_remaining,
                }
            )
            row.update(
                assignment_transition_info.get(
                    (env_id, agent_id),
                    {
                        "controller_target_changed_this_step": False,
                        "consecutive_steps_assigned_to_same_viewpoint": 0,
                    },
                )
            )
            pending_trace_by_env.setdefault(env_id, []).append(
                {field: row.get(field, "") for field in CONTROLLER_STATE_TRACE_FIELDS}
            )


def _count_true_segments(rows: list[dict], field: str) -> int:
    segments = 0
    was_true = False
    previous_step: int | None = None
    for row in rows:
        step = int(row["step"])
        current = _as_bool(row.get(field, False))
        if current and (not was_true or (previous_step is not None and step != previous_step + 1)):
            segments += 1
        was_true = current
        previous_step = step
    return segments


def _max_true_run(rows: list[dict], field: str) -> int:
    max_run = 0
    current_run = 0
    previous_step: int | None = None
    for row in rows:
        step = int(row["step"])
        current = _as_bool(row.get(field, False))
        if current and (previous_step is None or step == previous_step + 1):
            current_run += 1
        elif current:
            current_run = 1
        else:
            current_run = 0
        max_run = max(max_run, current_run)
        previous_step = step
    return max_run


def _controller_trace_likely_failure_mode(summary: dict) -> str:
    if bool(summary["ever_covered_after_assignment"]):
        return "covered"
    if int(summary["assigned_steps"]) <= 0:
        return "assigned_too_briefly_before_switch"
    required_gate_values = [
        summary["ever_position_gate_ok"],
        summary["ever_rotation_gate_ok"],
        summary["ever_range_gate_ok"],
        summary["ever_fov_alignment_gate_ok"],
        summary["ever_position_rotation_gate_ok"],
        summary["ever_all_coverage_gates_ok"],
    ]
    if any(value == "" for value in required_gate_values):
        return "unknown_missing_trace_fields"
    if not bool(summary["ever_position_gate_ok"]):
        return "never_reaches_position_gate"
    if not bool(summary["ever_rotation_gate_ok"]):
        return "never_reaches_rotation_gate"
    if not bool(summary["ever_range_gate_ok"]):
        return "never_reaches_range_gate"
    if not bool(summary["ever_fov_alignment_gate_ok"]):
        return "never_reaches_fov_gate"
    if not bool(summary["ever_position_rotation_gate_ok"]):
        return "position_rotation_never_simultaneous"
    if bool(summary["ever_all_coverage_gates_ok"]):
        return "all_gates_true_but_coverage_not_recorded"
    if int(summary["max_consecutive_assigned_steps"]) < int(args_cli.assignment_stall_window):
        return "assigned_too_briefly_before_switch"
    if int(summary["num_cooldown_interruptions"]) > 0:
        return "cooldown_interrupts_before_convergence"
    return "unknown_missing_trace_fields"


def _summarize_controller_state_trace(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        key = (str(row["method"]), int(row["agent_id"]), int(row["viewpoint_id"]))
        grouped.setdefault(key, []).append(row)

    summaries = []
    for key in sorted(grouped):
        pair_rows = sorted(grouped[key], key=lambda item: (int(item["episode"]), int(item["step"])))
        selected_rows = [row for row in pair_rows if _as_bool(row.get("is_pair_selected_this_step", False))]
        first_step = min((int(row["step"]) for row in selected_rows), default=-1)
        last_step = max((int(row["step"]) for row in selected_rows), default=-1)

        def any_selected_bool(field: str) -> bool | str:
            if not selected_rows:
                return False
            values = [row.get(field, "") for row in selected_rows]
            if all(str(value).strip() == "" for value in values):
                return ""
            return any(_as_bool(value) for value in values if str(value).strip() != "")

        def min_selected_float(field: str) -> float | str:
            values = [_as_optional_float(row.get(field)) for row in selected_rows]
            values = [value for value in values if value is not None]
            return min(values) if values else ""

        def max_selected_float(field: str) -> float | str:
            values = [_as_optional_float(row.get(field)) for row in selected_rows]
            values = [value for value in values if value is not None]
            return max(values) if values else ""

        summary = {
            "method": key[0],
            "agent_id": key[1],
            "agent_name": pair_rows[0].get("agent_name", f"agent_{key[1]}"),
            "viewpoint_id": key[2],
            "assigned_steps": len(selected_rows),
            "first_assigned_step": first_step,
            "last_assigned_step": last_step,
            "num_assignment_segments": _count_true_segments(pair_rows, "is_pair_selected_this_step"),
            "max_consecutive_assigned_steps": _max_true_run(pair_rows, "is_pair_selected_this_step"),
            "ever_position_gate_ok": any_selected_bool("position_gate_ok"),
            "ever_rotation_gate_ok": any_selected_bool("rotation_gate_ok"),
            "ever_range_gate_ok": any_selected_bool("range_gate_ok"),
            "ever_fov_alignment_gate_ok": any_selected_bool("fov_alignment_gate_ok"),
            "ever_position_rotation_gate_ok": any_selected_bool("position_rotation_gate_ok"),
            "ever_all_coverage_gates_ok": any_selected_bool("all_coverage_gates_ok"),
            "ever_covered_after_assignment": any_selected_bool("assigned_viewpoint_covered_after"),
            "min_position_error": min_selected_float("position_error"),
            "min_rotation_error": min_selected_float("rotation_error"),
            "max_range_margin": max_selected_float("range_margin"),
            "max_fov_alignment": max_selected_float("fov_alignment"),
            "num_target_switches": max(0, _count_true_segments(pair_rows, "is_pair_selected_this_step") - 1),
            "num_cooldown_interruptions": _count_true_segments(pair_rows, "cooldown_active_for_pair"),
        }
        summary["likely_failure_mode"] = _controller_trace_likely_failure_mode(summary)
        summaries.append(summary)
    return summaries


def _load_level2_pair_filter() -> dict:
    global _LEVEL2_PAIR_FILTER_CACHE
    if _LEVEL2_PAIR_FILTER_CACHE is not None:
        return _LEVEL2_PAIR_FILTER_CACHE

    json_path = args_cli.level2_pair_filter_json
    if json_path is None:
        _LEVEL2_PAIR_FILTER_CACHE = {
            "enabled": False,
            "json_path": None,
            "pairs": {},
            "allowed_pairs": [],
            "denied_pairs": [],
            "num_loaded": 0,
            "num_allowed": 0,
            "num_denied": 0,
            "unchecked_pairs_policy": "unchanged",
        }
        return _LEVEL2_PAIR_FILTER_CACHE

    path = Path(json_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"--level2_pair_filter_json does not exist: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    pair_lookup: dict[tuple[int, int], dict] = {}
    for row in payload.get("results", []):
        agent_id = _as_int(row.get("agent_id"))
        viewpoint_id = _as_int(row.get("viewpoint_id", row.get("viewpoint_index")))
        if agent_id < 0 or viewpoint_id < 0:
            continue
        covered = bool(row.get("covered", False))
        pair_lookup[(agent_id, viewpoint_id)] = {
            "agent_id": agent_id,
            "agent_name": row.get("agent_name", f"agent_{agent_id}"),
            "viewpoint_id": viewpoint_id,
            "covered": covered,
            "first_covered_step": row.get("first_covered_step"),
            "most_likely_failure_reason": row.get("most_likely_failure_reason", ""),
        }

    pairs = [pair_lookup[key] for key in sorted(pair_lookup)]
    allowed_pairs = [pair for pair in pairs if bool(pair["covered"])]
    denied_pairs = [pair for pair in pairs if not bool(pair["covered"])]
    _LEVEL2_PAIR_FILTER_CACHE = {
        "enabled": True,
        "json_path": str(path),
        "pairs": pair_lookup,
        "allowed_pairs": allowed_pairs,
        "denied_pairs": denied_pairs,
        "num_loaded": len(pairs),
        "num_allowed": len(allowed_pairs),
        "num_denied": len(denied_pairs),
        "unchecked_pairs_policy": "unchanged",
    }
    return _LEVEL2_PAIR_FILTER_CACHE


def _level2_pair_filter_diagnostics() -> dict:
    pair_filter = _load_level2_pair_filter()
    return {
        "level2_pair_filter_enabled": bool(pair_filter["enabled"]),
        "level2_pair_filter_json": pair_filter["json_path"],
        "num_level2_pairs_loaded": int(pair_filter["num_loaded"]),
        "num_level2_pairs_denied": int(pair_filter["num_denied"]),
        "num_level2_pairs_allowed": int(pair_filter["num_allowed"]),
        "denied_pairs": pair_filter["denied_pairs"],
        "allowed_pairs": pair_filter["allowed_pairs"],
        "unchecked_pairs_policy": pair_filter["unchecked_pairs_policy"],
    }


def _apply_level2_pair_filter(problem: dict) -> dict:
    pair_filter = _load_level2_pair_filter()
    if not bool(pair_filter["enabled"]) or not pair_filter["denied_pairs"]:
        return problem

    num_agents = int(problem["num_agents"])
    viewpoint_ids = [int(value) for value in problem.get("viewpoint_ids", range(int(problem["num_viewpoints"])))]
    viewpoint_index_by_id = {viewpoint_id: index for index, viewpoint_id in enumerate(viewpoint_ids)}
    available_mask = problem["available_mask"].to(dtype=torch.bool).clone()
    applied_denied_pairs = []
    skipped_denied_pairs = []

    for pair in pair_filter["denied_pairs"]:
        agent_id = int(pair["agent_id"])
        viewpoint_id = int(pair["viewpoint_id"])
        viewpoint_index = viewpoint_index_by_id.get(viewpoint_id)
        if agent_id < 0 or agent_id >= num_agents or viewpoint_index is None:
            skipped_denied_pairs.append(pair)
            continue
        available_mask[:, agent_id, viewpoint_index] = False
        applied_denied_pairs.append(pair)

    filtered_problem = dict(problem)
    filtered_problem["available_mask"] = available_mask
    filtered_problem["level2_pair_filter_applied_denied_pairs"] = applied_denied_pairs
    filtered_problem["level2_pair_filter_skipped_denied_pairs"] = skipped_denied_pairs
    return filtered_problem


def _retry_fallback_enabled() -> bool:
    return bool(args_cli.assignment_retry_fallback)


def _retry_fallback_static_diagnostics() -> dict:
    return {
        "assignment_retry_fallback_enabled": _retry_fallback_enabled(),
        "assignment_stall_window": int(args_cli.assignment_stall_window),
        "assignment_pair_cooldown": int(args_cli.assignment_pair_cooldown),
        "retry_fallback_policy": "consecutive_same_pair_no_coverage_gain",
    }


def _init_retry_fallback_stats() -> dict:
    return {
        "num_cooldown_events_total": 0,
        "cooldown_events_by_method": {},
        "cooldown_events_by_pair": {},
        "final_active_cooldowns": [],
    }


def _make_retry_fallback_state(
    *,
    method: str,
    num_envs: int,
    num_agents: int,
    num_viewpoints: int,
    viewpoint_ids: list[int],
    device: torch.device,
    stats: dict,
) -> dict:
    return {
        "enabled": _retry_fallback_enabled(),
        "method": method,
        "viewpoint_ids": [int(value) for value in viewpoint_ids],
        "current_viewpoint_id": torch.full((num_envs, num_agents), -2, dtype=torch.long, device=device),
        "stall_count": torch.zeros((num_envs, num_agents), dtype=torch.long, device=device),
        "streak_start_coverage": torch.zeros((num_envs, num_agents), dtype=torch.long, device=device),
        "cooldown_remaining": torch.zeros(
            (num_envs, num_agents, num_viewpoints), dtype=torch.long, device=device
        ),
        "stats": stats,
    }


def _reset_retry_fallback_state(state: dict | None, env_ids: torch.Tensor) -> None:
    if state is None or not bool(state.get("enabled", False)) or env_ids.numel() == 0:
        return
    state["current_viewpoint_id"][env_ids] = -2
    state["stall_count"][env_ids] = 0
    state["streak_start_coverage"][env_ids] = 0
    state["cooldown_remaining"][env_ids] = 0


def _apply_retry_fallback_filter(problem: dict, retry_state: dict | None) -> dict:
    if retry_state is None or not bool(retry_state.get("enabled", False)):
        return problem
    cooldown_mask = retry_state["cooldown_remaining"] > 0
    if not bool(cooldown_mask.any()):
        return problem
    available_mask = problem["available_mask"].to(dtype=torch.bool).clone()
    if tuple(cooldown_mask.shape) != tuple(available_mask.shape):
        raise RuntimeError(
            f"retry/fallback cooldown mask shape mismatch: expected {tuple(available_mask.shape)}, "
            f"got {tuple(cooldown_mask.shape)}"
        )
    filtered_problem = dict(problem)
    filtered_problem["available_mask"] = available_mask & (~cooldown_mask)
    filtered_problem["retry_fallback_cooldown_mask"] = cooldown_mask
    return filtered_problem


def _retry_fallback_default_history_fields() -> dict:
    return {
        "pair_in_cooldown_before_selection": False,
        "cooldown_event_triggered": False,
        "cooldown_remaining_after_step": 0,
        "stall_count_before_step": 0,
        "stall_count_after_step": 0,
    }


def _retry_fallback_selected_pair_info(
    retry_state: dict | None,
    assignment: torch.Tensor,
    viewpoint_ids: list[int],
) -> dict[tuple[int, int], dict]:
    info: dict[tuple[int, int], dict] = {}
    if retry_state is None or not bool(retry_state.get("enabled", False)):
        return info

    cooldown_remaining = retry_state["cooldown_remaining"]
    current_viewpoint_id = retry_state["current_viewpoint_id"]
    stall_count = retry_state["stall_count"]
    num_envs, num_agents = assignment.shape
    for env_id in range(num_envs):
        for agent_id in range(num_agents):
            fields = _retry_fallback_default_history_fields()
            assigned_index = int(assignment[env_id, agent_id].item())
            if assigned_index >= 0:
                viewpoint_id = int(viewpoint_ids[assigned_index])
                fields["pair_in_cooldown_before_selection"] = bool(
                    cooldown_remaining[env_id, agent_id, assigned_index].item() > 0
                )
                if int(current_viewpoint_id[env_id, agent_id].item()) == viewpoint_id:
                    fields["stall_count_before_step"] = int(stall_count[env_id, agent_id].item())
            info[(env_id, agent_id)] = fields
    return info


def _capture_retry_fallback_active_cooldowns(state: dict | None, env_ids: torch.Tensor | None = None) -> list[dict]:
    if state is None or not bool(state.get("enabled", False)):
        return []
    cooldown_remaining = state["cooldown_remaining"]
    active_mask = cooldown_remaining > 0
    if env_ids is not None:
        env_mask = torch.zeros(active_mask.shape[0], dtype=torch.bool, device=active_mask.device)
        env_mask[env_ids] = True
        active_mask = active_mask & env_mask[:, None, None]
    active = []
    viewpoint_ids = state["viewpoint_ids"]
    for env_id, agent_id, viewpoint_index in torch.nonzero(active_mask, as_tuple=False):
        env_int = int(env_id.item())
        agent_int = int(agent_id.item())
        viewpoint_idx_int = int(viewpoint_index.item())
        active.append(
            {
                "method": state["method"],
                "env_id": env_int,
                "agent_id": agent_int,
                "viewpoint_id": int(viewpoint_ids[viewpoint_idx_int]),
                "remaining": int(cooldown_remaining[env_int, agent_int, viewpoint_idx_int].item()),
            }
        )
    return active


def _record_retry_fallback_event(
    retry_state: dict,
    pending_events_by_env: dict[int, list[dict]],
    *,
    env_id: int,
    agent_id: int,
    viewpoint_id: int,
    step: int,
    coverage_count: int,
) -> None:
    method = retry_state["method"]
    stats = retry_state["stats"]
    pair_key = f"agent_{agent_id}_viewpoint_{viewpoint_id}"
    stats["num_cooldown_events_total"] += 1
    stats["cooldown_events_by_method"][method] = int(stats["cooldown_events_by_method"].get(method, 0)) + 1
    stats["cooldown_events_by_pair"][pair_key] = int(stats["cooldown_events_by_pair"].get(pair_key, 0)) + 1
    pending_events_by_env.setdefault(env_id, []).append(
        {
            "method": method,
            "episode": -1,
            "step": int(step),
            "env_id": int(env_id),
            "agent_id": int(agent_id),
            "viewpoint_id": int(viewpoint_id),
            "reason": "consecutive_same_pair_no_coverage_gain",
            "stall_window": int(args_cli.assignment_stall_window),
            "cooldown_duration": int(args_cli.assignment_pair_cooldown),
            "coverage_count_when_triggered": int(coverage_count),
        }
    )


def _update_retry_fallback_after_step(
    retry_state: dict | None,
    *,
    method: str,
    step: torch.Tensor,
    assignment: torch.Tensor,
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    viewpoint_ids: list[int],
    pending_events_by_env: dict[int, list[dict]],
) -> dict[tuple[int, int], dict]:
    info = _retry_fallback_selected_pair_info(retry_state, assignment, viewpoint_ids)
    if retry_state is None or not bool(retry_state.get("enabled", False)):
        return info

    stall_window = int(args_cli.assignment_stall_window)
    cooldown_duration = int(args_cli.assignment_pair_cooldown)
    if stall_window <= 0 or cooldown_duration <= 0:
        return info

    cooldown_remaining = retry_state["cooldown_remaining"]
    cooldown_remaining.copy_(torch.clamp(cooldown_remaining - 1, min=0))

    current_viewpoint_id = retry_state["current_viewpoint_id"]
    stall_count = retry_state["stall_count"]
    streak_start_coverage = retry_state["streak_start_coverage"]
    covered_before_count = covered_before.sum(dim=-1).to(dtype=torch.long)
    covered_after_count = covered_after.sum(dim=-1).to(dtype=torch.long)
    num_envs, num_agents = assignment.shape

    for env_id in range(num_envs):
        coverage_gain = int(covered_after_count[env_id].item()) > int(covered_before_count[env_id].item())
        if coverage_gain:
            current_viewpoint_id[env_id] = -2
            stall_count[env_id] = 0
            streak_start_coverage[env_id] = int(covered_after_count[env_id].item())
        for agent_id in range(num_agents):
            assigned_index = int(assignment[env_id, agent_id].item())
            fields = info.setdefault((env_id, agent_id), _retry_fallback_default_history_fields())
            if assigned_index < 0:
                current_viewpoint_id[env_id, agent_id] = -2
                stall_count[env_id, agent_id] = 0
                streak_start_coverage[env_id, agent_id] = int(covered_after_count[env_id].item())
                continue
            viewpoint_id = int(viewpoint_ids[assigned_index])
            if coverage_gain or bool(covered_before[env_id, assigned_index].item()) or bool(
                covered_after[env_id, assigned_index].item()
            ):
                current_viewpoint_id[env_id, agent_id] = -2
                stall_count[env_id, agent_id] = 0
                streak_start_coverage[env_id, agent_id] = int(covered_after_count[env_id].item())
                fields["cooldown_remaining_after_step"] = int(cooldown_remaining[env_id, agent_id, assigned_index].item())
                fields["stall_count_after_step"] = 0
                continue

            if int(current_viewpoint_id[env_id, agent_id].item()) == viewpoint_id:
                stall_count[env_id, agent_id] += 1
            else:
                current_viewpoint_id[env_id, agent_id] = viewpoint_id
                stall_count[env_id, agent_id] = 1
                streak_start_coverage[env_id, agent_id] = int(covered_before_count[env_id].item())

            if int(stall_count[env_id, agent_id].item()) >= stall_window and int(
                covered_after_count[env_id].item()
            ) <= int(streak_start_coverage[env_id, agent_id].item()):
                cooldown_remaining[env_id, agent_id, assigned_index] = cooldown_duration
                fields["cooldown_event_triggered"] = True
                _record_retry_fallback_event(
                    retry_state,
                    pending_events_by_env,
                    env_id=env_id,
                    agent_id=agent_id,
                    viewpoint_id=viewpoint_id,
                    step=int(step[env_id].item()),
                    coverage_count=int(covered_after_count[env_id].item()),
                )
                current_viewpoint_id[env_id, agent_id] = -2
                stall_count[env_id, agent_id] = 0
                streak_start_coverage[env_id, agent_id] = int(covered_after_count[env_id].item())

            fields["cooldown_remaining_after_step"] = int(cooldown_remaining[env_id, agent_id, assigned_index].item())
            fields["stall_count_after_step"] = int(stall_count[env_id, agent_id].item())
    return info


def _retry_fallback_runtime_diagnostics(stats: dict) -> dict:
    return {
        "num_cooldown_events_total": int(stats.get("num_cooldown_events_total", 0)),
        "cooldown_events_by_method": dict(stats.get("cooldown_events_by_method", {})),
        "cooldown_events_by_pair": dict(stats.get("cooldown_events_by_pair", {})),
        "final_active_cooldowns": list(stats.get("final_active_cooldowns", [])),
    }


def _apply_viewpoint_candidate_filter(problem: dict) -> dict:
    top_k = int(args_cli.viewpoint_candidate_top_k)
    if top_k <= 0:
        return problem

    num_viewpoints = int(problem["num_viewpoints"])
    if num_viewpoints <= 0:
        return problem

    selected_count = min(top_k, num_viewpoints)
    available_mask = problem["available_mask"].to(dtype=torch.bool)
    cost_matrix = problem["cost_matrix"]
    filtered_mask = torch.zeros_like(available_mask, dtype=torch.bool)
    masked_cost = cost_matrix.masked_fill(~available_mask, float("inf"))
    top_values, top_indices = torch.topk(masked_cost, k=selected_count, dim=-1, largest=False)
    finite = torch.isfinite(top_values)
    filtered_mask.scatter_(dim=2, index=top_indices, src=finite)

    filtered_problem = dict(problem)
    filtered_problem["available_mask"] = filtered_mask
    filtered_problem["candidate_unfiltered_available_mask"] = available_mask
    filtered_problem["viewpoint_candidate_top_k"] = top_k
    filtered_problem["candidate_mode"] = _candidate_mode()
    return filtered_problem


def _prepare_baseline_assignment_problem(problem: dict, retry_state: dict | None = None, *, method: str | None = None) -> dict:
    problem = _apply_level2_pair_filter(problem)
    problem = _apply_retry_fallback_filter(problem, retry_state)
    problem = _apply_viewpoint_candidate_filter(problem)
    return _attach_conflict_aware_baseline_config(problem, method=method)


def _json_float(value: Any) -> float | None:
    try:
        numeric = float(value.item() if isinstance(value, torch.Tensor) else value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _viewpoint_id_from_assignment(viewpoint_ids: list[int], viewpoint_index: int) -> int:
    if viewpoint_index < 0:
        return -1
    if viewpoint_index < len(viewpoint_ids):
        return int(viewpoint_ids[viewpoint_index])
    return int(viewpoint_index)


def _selected_matrix_sum(matrix: torch.Tensor | None, assignment: torch.Tensor) -> float:
    if not isinstance(matrix, torch.Tensor):
        return 0.0
    total = 0.0
    for env_id_tensor, agent_id_tensor in torch.nonzero(assignment >= 0, as_tuple=False):
        env_id = int(env_id_tensor.item())
        agent_id = int(agent_id_tensor.item())
        viewpoint_index = int(assignment[env_id, agent_id].item())
        value = _json_float(matrix[env_id, agent_id, viewpoint_index])
        if value is not None:
            total += value
    return total


def _selected_intersection_count(intersection_mask: torch.Tensor | None, assignment: torch.Tensor) -> int:
    if not isinstance(intersection_mask, torch.Tensor):
        return 0
    mask = intersection_mask.to(dtype=torch.bool)
    count = 0
    for env_id_tensor, agent_id_tensor in torch.nonzero(assignment >= 0, as_tuple=False):
        env_id = int(env_id_tensor.item())
        agent_id = int(agent_id_tensor.item())
        viewpoint_index = int(assignment[env_id, agent_id].item())
        count += int(bool(mask[env_id, agent_id, viewpoint_index].item()))
    return count


def _assignment_pair_value(matrix: torch.Tensor | None, env_id: int, agent_id: int, viewpoint_index: int) -> float | None:
    if viewpoint_index < 0 or not isinstance(matrix, torch.Tensor):
        return None
    return _json_float(matrix[env_id, agent_id, viewpoint_index])


def _assignment_pair_intersects(
    intersection_mask: torch.Tensor | None,
    env_id: int,
    agent_id: int,
    viewpoint_index: int,
) -> bool:
    if viewpoint_index < 0 or not isinstance(intersection_mask, torch.Tensor):
        return False
    return bool(intersection_mask.to(dtype=torch.bool)[env_id, agent_id, viewpoint_index].item())


def _selected_pair_sample(
    *,
    assignment: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
    intersection_mask: torch.Tensor | None,
    baseline_cost_matrix: torch.Tensor | None,
    obstacle_aware_cost_matrix: torch.Tensor | None,
    obstacle_penalty_matrix: torch.Tensor | None,
    limit: int = 10,
) -> list[dict]:
    rows = []
    for env_id_tensor, agent_id_tensor in torch.nonzero(assignment >= 0, as_tuple=False):
        if len(rows) >= limit:
            break
        env_id = int(env_id_tensor.item())
        agent_id = int(agent_id_tensor.item())
        viewpoint_index = int(assignment[env_id, agent_id].item())
        rows.append(
            {
                "env_id": env_id,
                "robot_id": agent_id,
                "robot_name": agents[agent_id] if agent_id < len(agents) else f"robot_{agent_id}",
                "viewpoint_id": _viewpoint_id_from_assignment(viewpoint_ids, viewpoint_index),
                "pair_intersects": _assignment_pair_intersects(intersection_mask, env_id, agent_id, viewpoint_index),
                "baseline_cost": _assignment_pair_value(baseline_cost_matrix, env_id, agent_id, viewpoint_index),
                "obstacle_aware_cost": _assignment_pair_value(
                    obstacle_aware_cost_matrix, env_id, agent_id, viewpoint_index
                ),
                "obstacle_penalty": _assignment_pair_value(obstacle_penalty_matrix, env_id, agent_id, viewpoint_index),
            }
        )
    return rows


def _changed_pair_sample(
    *,
    baseline_assignment: torch.Tensor,
    candidate_assignment: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
    intersection_mask: torch.Tensor | None,
    baseline_cost_matrix: torch.Tensor | None,
    obstacle_aware_cost_matrix: torch.Tensor | None,
    limit: int = 10,
) -> list[dict]:
    rows = []
    changed = baseline_assignment != candidate_assignment
    for env_id_tensor, agent_id_tensor in torch.nonzero(changed, as_tuple=False):
        if len(rows) >= limit:
            break
        env_id = int(env_id_tensor.item())
        agent_id = int(agent_id_tensor.item())
        baseline_index = int(baseline_assignment[env_id, agent_id].item())
        candidate_index = int(candidate_assignment[env_id, agent_id].item())
        rows.append(
            {
                "env_id": env_id,
                "robot_id": agent_id,
                "robot_name": agents[agent_id] if agent_id < len(agents) else f"robot_{agent_id}",
                "baseline_viewpoint_id": _viewpoint_id_from_assignment(viewpoint_ids, baseline_index),
                "candidate_viewpoint_id": _viewpoint_id_from_assignment(viewpoint_ids, candidate_index),
                "baseline_pair_intersects": _assignment_pair_intersects(
                    intersection_mask, env_id, agent_id, baseline_index
                ),
                "candidate_pair_intersects": _assignment_pair_intersects(
                    intersection_mask, env_id, agent_id, candidate_index
                ),
                "baseline_cost": _assignment_pair_value(baseline_cost_matrix, env_id, agent_id, baseline_index),
                "candidate_cost": _assignment_pair_value(baseline_cost_matrix, env_id, agent_id, candidate_index),
                "baseline_obstacle_aware_cost": _assignment_pair_value(
                    obstacle_aware_cost_matrix, env_id, agent_id, baseline_index
                ),
                "candidate_obstacle_aware_cost": _assignment_pair_value(
                    obstacle_aware_cost_matrix, env_id, agent_id, candidate_index
                ),
            }
        )
    return rows


def _obstacle_candidate_required_tensors(problem: dict) -> tuple[dict[str, torch.Tensor] | None, str | None]:
    required = {
        "baseline_cost_matrix": problem.get("cost_matrix"),
        "mesh_footprint_intersection_mask": problem.get("mesh_footprint_intersection_mask"),
        "mesh_footprint_penalty_matrix": problem.get("mesh_footprint_penalty_matrix"),
        "mesh_footprint_aware_cost_matrix": problem.get("mesh_footprint_aware_cost_matrix"),
    }
    missing = [name for name, value in required.items() if not isinstance(value, torch.Tensor)]
    if missing:
        return None, f"missing_required_tensors:{','.join(missing)}"

    expected_shape = tuple(required["baseline_cost_matrix"].shape)
    shape_errors = [name for name, value in required.items() if tuple(value.shape) != expected_shape]
    if shape_errors:
        return None, f"shape_mismatch:{','.join(shape_errors)} expected={expected_shape}"
    return required, None


def _obstacle_candidate_baseline_metrics(
    *,
    method: str,
    step: torch.Tensor,
    episode_index: torch.Tensor | None,
    problem: dict,
    assignment: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
) -> dict:
    tensors, reason = _obstacle_candidate_required_tensors(problem)
    selected_pair_count = int((assignment >= 0).sum().item())
    row = {
        "method": method,
        "steps": 1,
        "available": tensors is not None,
        "skipped_reason": reason,
        "candidate_available": False,
        "candidate_reason": "baseline_intersection_stats_only",
        "selected_pair_count": selected_pair_count,
        "selected_intersection_count": 0,
        "selected_baseline_cost_sum": 0.0,
        "selected_obstacle_aware_cost_sum": 0.0,
        "obstacle_penalty_sum_for_baseline_selection": 0.0,
        "candidate_changed_assignment_count": 0,
        "candidate_assignment_decision_count": int(assignment.numel()),
        "candidate_selected_pair_count": 0,
        "candidate_intersection_count": 0,
        "candidate_baseline_cost_sum": 0.0,
        "candidate_obstacle_aware_cost_sum": 0.0,
        "obstacle_penalty_sum_for_candidate_selection": 0.0,
        "mesh_footprint_intersection_count": 0,
        "baseline_selected_pairs_sample": [],
        "candidate_selected_pairs_sample": [],
        "changed_pairs_sample": [],
        "blocked_baseline_pairs_sample": [],
        "step_min": int(step.min().item()) if isinstance(step, torch.Tensor) and step.numel() > 0 else 0,
        "step_max": int(step.max().item()) if isinstance(step, torch.Tensor) and step.numel() > 0 else 0,
        "episode_index_min": (
            int(episode_index.min().item())
            if isinstance(episode_index, torch.Tensor) and episode_index.numel() > 0
            else 0
        ),
        "episode_index_max": (
            int(episode_index.max().item())
            if isinstance(episode_index, torch.Tensor) and episode_index.numel() > 0
            else 0
        ),
    }
    if tensors is None:
        return row

    intersection_mask = tensors["mesh_footprint_intersection_mask"]
    penalty_matrix = tensors["mesh_footprint_penalty_matrix"]
    aware_cost_matrix = tensors["mesh_footprint_aware_cost_matrix"]
    baseline_cost_matrix = tensors["baseline_cost_matrix"]
    row.update(
        {
            "selected_intersection_count": _selected_intersection_count(intersection_mask, assignment),
            "selected_baseline_cost_sum": _selected_matrix_sum(baseline_cost_matrix, assignment),
            "selected_obstacle_aware_cost_sum": _selected_matrix_sum(aware_cost_matrix, assignment),
            "obstacle_penalty_sum_for_baseline_selection": _selected_matrix_sum(penalty_matrix, assignment),
            "mesh_footprint_intersection_count": int(intersection_mask.to(dtype=torch.bool).sum().item()),
            "baseline_selected_pairs_sample": _selected_pair_sample(
                assignment=assignment,
                agents=agents,
                viewpoint_ids=viewpoint_ids,
                intersection_mask=intersection_mask,
                baseline_cost_matrix=baseline_cost_matrix,
                obstacle_aware_cost_matrix=aware_cost_matrix,
                obstacle_penalty_matrix=penalty_matrix,
            ),
            "blocked_baseline_pairs_sample": [
                pair
                for pair in _selected_pair_sample(
                    assignment=assignment,
                    agents=agents,
                    viewpoint_ids=viewpoint_ids,
                    intersection_mask=intersection_mask,
                    baseline_cost_matrix=baseline_cost_matrix,
                    obstacle_aware_cost_matrix=aware_cost_matrix,
                    obstacle_penalty_matrix=penalty_matrix,
                )
                if bool(pair.get("pair_intersects", False))
            ],
        }
    )
    return row


def _compare_obstacle_aware_candidate_step(
    *,
    method: str,
    step: torch.Tensor,
    episode_index: torch.Tensor | None,
    problem: dict,
    baseline_assignment: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
) -> dict:
    row = _obstacle_candidate_baseline_metrics(
        method=method,
        step=step,
        episode_index=episode_index,
        problem=problem,
        assignment=baseline_assignment,
        agents=agents,
        viewpoint_ids=viewpoint_ids,
    )
    if not bool(row["available"]):
        return row
    if method not in {"nearest", "greedy"}:
        return row

    tensors, reason = _obstacle_candidate_required_tensors(problem)
    if tensors is None:
        row["candidate_reason"] = reason
        return row

    candidate_problem = dict(problem)
    candidate_problem["cost_matrix"] = tensors["mesh_footprint_aware_cost_matrix"]
    candidate_assignment = make_solver(method).solve(candidate_problem)
    _validate_assignment(candidate_problem, candidate_assignment)

    intersection_mask = tensors["mesh_footprint_intersection_mask"]
    penalty_matrix = tensors["mesh_footprint_penalty_matrix"]
    baseline_cost_matrix = tensors["baseline_cost_matrix"]
    aware_cost_matrix = tensors["mesh_footprint_aware_cost_matrix"]
    changed_count = int((baseline_assignment != candidate_assignment).sum().item())
    row.update(
        {
            "candidate_available": True,
            "candidate_reason": "mesh_footprint_aware_cost_matrix_on_copied_problem",
            "candidate_changed_assignment_count": changed_count,
            "candidate_selected_pair_count": int((candidate_assignment >= 0).sum().item()),
            "candidate_intersection_count": _selected_intersection_count(intersection_mask, candidate_assignment),
            "candidate_baseline_cost_sum": _selected_matrix_sum(baseline_cost_matrix, candidate_assignment),
            "candidate_obstacle_aware_cost_sum": _selected_matrix_sum(aware_cost_matrix, candidate_assignment),
            "obstacle_penalty_sum_for_candidate_selection": _selected_matrix_sum(penalty_matrix, candidate_assignment),
            "candidate_selected_pairs_sample": _selected_pair_sample(
                assignment=candidate_assignment,
                agents=agents,
                viewpoint_ids=viewpoint_ids,
                intersection_mask=intersection_mask,
                baseline_cost_matrix=baseline_cost_matrix,
                obstacle_aware_cost_matrix=aware_cost_matrix,
                obstacle_penalty_matrix=penalty_matrix,
            ),
            "changed_pairs_sample": _changed_pair_sample(
                baseline_assignment=baseline_assignment,
                candidate_assignment=candidate_assignment,
                agents=agents,
                viewpoint_ids=viewpoint_ids,
                intersection_mask=intersection_mask,
                baseline_cost_matrix=baseline_cost_matrix,
                obstacle_aware_cost_matrix=aware_cost_matrix,
            ),
        }
    )
    return row


def _limited_extend(target: list[dict], source: list[dict], *, limit: int = 10) -> None:
    remaining = max(0, limit - len(target))
    if remaining > 0:
        target.extend(source[:remaining])


def _summarize_obstacle_candidate_rows(rows: list[dict]) -> dict:
    selected_pair_count = sum(int(row.get("selected_pair_count", 0)) for row in rows)
    selected_intersection_count = sum(int(row.get("selected_intersection_count", 0)) for row in rows)
    candidate_decision_count = sum(int(row.get("candidate_assignment_decision_count", 0)) for row in rows)
    candidate_changed_count = sum(int(row.get("candidate_changed_assignment_count", 0)) for row in rows)
    candidate_selected_pair_count = sum(int(row.get("candidate_selected_pair_count", 0)) for row in rows)
    candidate_intersection_count = sum(int(row.get("candidate_intersection_count", 0)) for row in rows)
    candidate_available = any(bool(row.get("candidate_available", False)) for row in rows)
    baseline_cost_sum = sum(float(row.get("selected_baseline_cost_sum", 0.0)) for row in rows)
    baseline_obstacle_aware_cost_sum = sum(
        float(row.get("selected_obstacle_aware_cost_sum", 0.0)) for row in rows
    )
    baseline_obstacle_penalty_sum = sum(
        float(row.get("obstacle_penalty_sum_for_baseline_selection", 0.0)) for row in rows
    )
    candidate_baseline_cost_sum = sum(float(row.get("candidate_baseline_cost_sum", 0.0)) for row in rows)
    candidate_obstacle_aware_cost_sum = sum(
        float(row.get("candidate_obstacle_aware_cost_sum", 0.0)) for row in rows
    )
    candidate_obstacle_penalty_sum = sum(
        float(row.get("obstacle_penalty_sum_for_candidate_selection", 0.0)) for row in rows
    )
    baseline_intersection_rate = (
        selected_intersection_count / float(selected_pair_count) if selected_pair_count > 0 else 0.0
    )
    candidate_changed_rate = (
        candidate_changed_count / float(candidate_decision_count) if candidate_decision_count > 0 else 0.0
    )
    candidate_intersection_rate = (
        candidate_intersection_count / float(candidate_selected_pair_count)
        if candidate_selected_pair_count > 0
        else 0.0
    )
    return {
        "steps": len(rows),
        "candidate_available": candidate_available,
        "candidate_reason": next(
            (str(row.get("candidate_reason")) for row in rows if row.get("candidate_reason")),
            None,
        ),
        "selected_pair_count": selected_pair_count,
        "selected_intersection_count": selected_intersection_count,
        "selected_intersection_rate": baseline_intersection_rate,
        "selected_baseline_cost_sum": baseline_cost_sum,
        "selected_obstacle_aware_cost_sum": baseline_obstacle_aware_cost_sum,
        "obstacle_penalty_sum_for_baseline_selection": baseline_obstacle_penalty_sum,
        "candidate_changed_assignment_count": candidate_changed_count,
        "candidate_changed_assignment_rate": candidate_changed_rate,
        "candidate_selected_pair_count": candidate_selected_pair_count,
        "candidate_intersection_count": candidate_intersection_count,
        "candidate_intersection_rate": candidate_intersection_rate,
        "candidate_baseline_cost_sum": candidate_baseline_cost_sum,
        "candidate_obstacle_aware_cost_sum": candidate_obstacle_aware_cost_sum,
        "obstacle_penalty_sum_for_candidate_selection": candidate_obstacle_penalty_sum,
        "baseline_selected_pair_count": selected_pair_count,
        "baseline_selected_intersection_count": selected_intersection_count,
        "baseline_selected_intersection_rate": baseline_intersection_rate,
        "baseline_cost_sum": baseline_cost_sum,
        "baseline_obstacle_aware_cost_sum": baseline_obstacle_aware_cost_sum,
        "baseline_obstacle_penalty_sum": baseline_obstacle_penalty_sum,
        "candidate_selected_intersection_count": candidate_intersection_count,
        "candidate_selected_intersection_rate": candidate_intersection_rate,
        "candidate_obstacle_penalty_sum": candidate_obstacle_penalty_sum,
    }


def _finalize_obstacle_aware_candidate_comparison(rows: list[dict], methods: list[str]) -> dict:
    diagnostics = {
        "enabled": True,
        "mode": "diagnostic_only_copied_problem_cost_swap",
        "candidate_cost_field": "mesh_footprint_aware_cost_matrix",
        "baseline_cost_field": "cost_matrix",
        "solver_behavior_changed": False,
        "methods_requested": list(methods),
        "methods_compared": [],
        "methods_baseline_only": [],
        "available": any(bool(row.get("available", False)) for row in rows),
        "unavailable_reasons": sorted(
            {
                str(row.get("skipped_reason"))
                for row in rows
                if not bool(row.get("available", False)) and row.get("skipped_reason")
            }
        ),
        "mesh_footprint_intersection_count": max(
            (int(row.get("mesh_footprint_intersection_count", 0)) for row in rows),
            default=0,
        ),
        "per_step_summary": [],
        "per_episode_summary": [],
        "per_method_summary": {},
        "samples": {
            "blocked_baseline_pairs_sample": [],
            "changed_pairs_sample": [],
            "baseline_selected_pairs_sample": [],
            "candidate_selected_pairs_sample": [],
        },
    }
    if not rows:
        diagnostics["available"] = False
        diagnostics["unavailable_reasons"] = ["no_evaluation_steps_recorded"]
        return diagnostics

    for method in methods:
        method_rows = [row for row in rows if row.get("method") == method]
        if not method_rows:
            continue
        candidate_available = any(bool(row.get("candidate_available", False)) for row in method_rows)
        if candidate_available:
            diagnostics["methods_compared"].append(method)
        else:
            diagnostics["methods_baseline_only"].append(method)

        diagnostics["per_method_summary"][method] = _summarize_obstacle_candidate_rows(method_rows)

        for row in method_rows:
            _limited_extend(
                diagnostics["samples"]["blocked_baseline_pairs_sample"],
                list(row.get("blocked_baseline_pairs_sample", [])),
            )
            _limited_extend(
                diagnostics["samples"]["changed_pairs_sample"],
                list(row.get("changed_pairs_sample", [])),
            )
            _limited_extend(
                diagnostics["samples"]["baseline_selected_pairs_sample"],
                list(row.get("baseline_selected_pairs_sample", [])),
            )
            _limited_extend(
                diagnostics["samples"]["candidate_selected_pairs_sample"],
                list(row.get("candidate_selected_pairs_sample", [])),
            )
    step_groups: dict[tuple[str, int, int], list[dict]] = {}
    episode_groups: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        method = str(row.get("method", "unknown"))
        step_key = (method, int(row.get("step_min", 0)), int(row.get("step_max", 0)))
        episode_key = (method, int(row.get("episode_index_min", 0)), int(row.get("episode_index_max", 0)))
        step_groups.setdefault(step_key, []).append(row)
        episode_groups.setdefault(episode_key, []).append(row)
    for (method, step_min, step_max), group_rows in sorted(step_groups.items(), key=lambda item: item[0]):
        summary = _summarize_obstacle_candidate_rows(group_rows)
        summary.update({"method": method, "step_min": step_min, "step_max": step_max})
        diagnostics["per_step_summary"].append(summary)
    for (method, episode_min, episode_max), group_rows in sorted(episode_groups.items(), key=lambda item: item[0]):
        summary = _summarize_obstacle_candidate_rows(group_rows)
        summary.update({"method": method, "episode_index_min": episode_min, "episode_index_max": episode_max})
        diagnostics["per_episode_summary"].append(summary)
    return diagnostics


def _finite_row_values(rows: list[dict], field: str) -> list[float]:
    values = []
    for row in rows:
        try:
            value = float(row.get(field, float("nan")))
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return values


def _mean_row_field(rows: list[dict], field: str, default: float = 0.0) -> float:
    if not rows:
        return default
    values = []
    for row in rows:
        try:
            values.append(float(row.get(field, default)))
        except (TypeError, ValueError):
            values.append(default)
    return sum(values) / float(len(values)) if values else default


def _min_row_field(rows: list[dict], field: str) -> float:
    values = _finite_row_values(rows, field)
    return min(values) if values else float("nan")


def _first_reason(rows: list[dict]) -> str | None:
    return next(
        (str(row.get("target_conflict_candidate_reason")) for row in rows if row.get("target_conflict_candidate_reason")),
        None,
    )


def _summarize_target_conflict_candidate_rows(rows: list[dict]) -> dict:
    step_count = sum(int(row.get("steps", 1)) for row in rows)
    baseline_pair_count = sum(int(row.get("baseline_selected_target_pair_count", 0)) for row in rows)
    baseline_conflict_count = sum(int(row.get("baseline_selected_target_conflict_pair_count", 0)) for row in rows)
    baseline_penalty_sum = sum(float(row.get("baseline_selected_target_conflict_penalty_sum", 0.0)) for row in rows)
    candidate_pair_count = sum(int(row.get("candidate_selected_target_pair_count", 0)) for row in rows)
    candidate_conflict_count = sum(int(row.get("candidate_selected_target_conflict_pair_count", 0)) for row in rows)
    candidate_penalty_sum = sum(float(row.get("candidate_selected_target_conflict_penalty_sum", 0.0)) for row in rows)
    decision_count = sum(int(row.get("candidate_assignment_decision_count", 0)) for row in rows)
    changed_count = sum(int(row.get("candidate_changed_assignment_count", 0)) for row in rows)
    candidate_available = any(bool(row.get("target_conflict_candidate_available", False)) for row in rows)
    baseline_conflict_rate = (
        baseline_conflict_count / float(baseline_pair_count) if baseline_pair_count > 0 else 0.0
    )
    candidate_conflict_rate = (
        candidate_conflict_count / float(candidate_pair_count) if candidate_pair_count > 0 else 0.0
    )
    changed_rate = changed_count / float(decision_count) if decision_count > 0 else 0.0

    return {
        "steps": step_count,
        "target_conflict_candidate_comparison_enabled": any(
            bool(row.get("target_conflict_candidate_comparison_enabled", False)) for row in rows
        ),
        "target_conflict_candidate_available": candidate_available,
        "target_conflict_candidate_reason": _first_reason(rows),
        "baseline_selected_target_pair_count": baseline_pair_count,
        "baseline_selected_target_conflict_pair_count": baseline_conflict_count,
        "baseline_selected_target_conflict_rate": baseline_conflict_rate,
        "baseline_selected_target_conflict_rate_mean": _mean_row_field(
            rows,
            "baseline_selected_target_conflict_rate",
        ),
        "baseline_selected_target_min_distance": _min_row_field(rows, "baseline_selected_target_min_distance"),
        "baseline_selected_target_min_clearance": _min_row_field(rows, "baseline_selected_target_min_clearance"),
        "baseline_selected_target_conflict_penalty_sum": baseline_penalty_sum,
        "candidate_selected_target_pair_count": candidate_pair_count,
        "candidate_selected_target_conflict_pair_count": candidate_conflict_count,
        "candidate_selected_target_conflict_rate": candidate_conflict_rate,
        "candidate_selected_target_conflict_rate_mean": _mean_row_field(
            rows,
            "candidate_selected_target_conflict_rate",
        ),
        "candidate_selected_target_min_distance": _min_row_field(rows, "candidate_selected_target_min_distance"),
        "candidate_selected_target_min_clearance": _min_row_field(rows, "candidate_selected_target_min_clearance"),
        "candidate_selected_target_conflict_penalty_sum": candidate_penalty_sum,
        "candidate_assignment_decision_count": decision_count,
        "candidate_changed_assignment_count": changed_count,
        "candidate_changed_assignment_rate": changed_rate,
        "candidate_changed_assignment_rate_mean": _mean_row_field(rows, "candidate_changed_assignment_rate"),
    }


def _finalize_target_conflict_candidate_comparison(rows: list[dict], methods: list[str]) -> dict:
    config = _target_conflict_candidate_config()
    diagnostics = {
        "enabled": bool(config["enabled"]),
        "mode": str(config["mode"]),
        "candidate_generator": str(config["candidate_generator"]),
        "robot_order": str(config["robot_order"]),
        "target_conflict_radius": float(config["target_conflict_radius"]),
        "target_conflict_safety_margin": float(config["target_conflict_safety_margin"]),
        "selected_target_conflict_threshold": _target_conflict_threshold(config),
        "selected_target_conflict_penalty": float(config["selected_target_conflict_penalty"]),
        "compare_methods": list(config["compare_methods"]),
        "include_random_as_baseline_only": bool(config["include_random_as_baseline_only"]),
        "solver_behavior_changed": False,
        "actual_assignment_changed": False,
        "candidate_assignment_executed": False,
        "live_solver_inputs_changed": False,
        "methods_requested": list(methods),
        "methods_compared": [],
        "methods_baseline_only": [],
        "available": any(bool(row.get("target_conflict_candidate_available", False)) for row in rows),
        "unavailable_reasons": sorted(
            {
                str(row.get("target_conflict_candidate_reason"))
                for row in rows
                if not bool(row.get("target_conflict_candidate_available", False))
                and row.get("target_conflict_candidate_reason")
            }
        ),
        "per_step_summary": [],
        "per_episode_summary": [],
        "per_method_summary": {},
        "samples": {
            "baseline_target_conflict_pairs_sample": [],
            "candidate_target_conflict_pairs_sample": [],
            "candidate_changed_pairs_sample": [],
        },
    }
    if not rows:
        diagnostics["unavailable_reasons"] = ["no_evaluation_steps_recorded"]
        return diagnostics

    for method in methods:
        method_rows = [row for row in rows if row.get("method") == method]
        if not method_rows:
            continue
        if any(bool(row.get("target_conflict_candidate_available", False)) for row in method_rows):
            diagnostics["methods_compared"].append(method)
        else:
            diagnostics["methods_baseline_only"].append(method)
        diagnostics["per_method_summary"][method] = _summarize_target_conflict_candidate_rows(method_rows)
        for row in method_rows:
            _limited_extend(
                diagnostics["samples"]["baseline_target_conflict_pairs_sample"],
                list(row.get("baseline_target_conflict_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )
            _limited_extend(
                diagnostics["samples"]["candidate_target_conflict_pairs_sample"],
                list(row.get("candidate_target_conflict_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )
            _limited_extend(
                diagnostics["samples"]["candidate_changed_pairs_sample"],
                list(row.get("candidate_changed_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )

    step_groups: dict[tuple[str, int, int], list[dict]] = {}
    episode_groups: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        method = str(row.get("method", "unknown"))
        step_key = (method, int(row.get("step_min", 0)), int(row.get("step_max", 0)))
        episode_key = (method, int(row.get("episode_index_min", 0)), int(row.get("episode_index_max", 0)))
        step_groups.setdefault(step_key, []).append(row)
        episode_groups.setdefault(episode_key, []).append(row)
    for (method, step_min, step_max), group_rows in sorted(step_groups.items(), key=lambda item: item[0]):
        summary = _summarize_target_conflict_candidate_rows(group_rows)
        summary.update({"method": method, "step_min": step_min, "step_max": step_max})
        diagnostics["per_step_summary"].append(summary)
    for (method, episode_min, episode_max), group_rows in sorted(episode_groups.items(), key=lambda item: item[0]):
        summary = _summarize_target_conflict_candidate_rows(group_rows)
        summary.update({"method": method, "episode_index_min": episode_min, "episode_index_max": episode_max})
        diagnostics["per_episode_summary"].append(summary)
    return diagnostics


def _mean_finite_tensor(tensor: torch.Tensor) -> float:
    values = tensor.to(dtype=torch.float32).flatten()
    finite = torch.isfinite(values)
    if not bool(finite.any()):
        return float("nan")
    return float(values[finite].mean().item())


def _conflict_aware_solver_step_row(
    *,
    method: str,
    step: torch.Tensor,
    episode_index: torch.Tensor,
    solver_diagnostics: dict | None,
    num_envs: int,
    num_agents: int,
    device: torch.device,
) -> dict | None:
    if not solver_diagnostics:
        return None
    if "conflict_aware_candidate_combination_count" not in solver_diagnostics:
        return None

    combination_count = _as_tensor_metric(
        solver_diagnostics["conflict_aware_candidate_combination_count"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    selected_score = _as_tensor_metric(
        solver_diagnostics["conflict_aware_selected_score"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    selected_unary = _as_tensor_metric(
        solver_diagnostics["conflict_aware_selected_unary_cost_sum"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    selected_conflicts = _as_tensor_metric(
        solver_diagnostics["conflict_aware_selected_target_conflict_pair_count"],
        num_envs,
        device,
        dtype=torch.long,
    )
    selected_penalty = _as_tensor_metric(
        solver_diagnostics["conflict_aware_selected_target_conflict_penalty_sum"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    selected_duplicates = _as_tensor_metric(
        solver_diagnostics["conflict_aware_selected_duplicate_pair_count"],
        num_envs,
        device,
        dtype=torch.long,
    )
    fallback_used = _as_tensor_metric(
        solver_diagnostics["conflict_aware_fallback_used"],
        num_envs,
        device,
        dtype=torch.bool,
    )
    changed_count = _as_tensor_metric(
        solver_diagnostics["conflict_aware_changed_vs_base_count"],
        num_envs,
        device,
        dtype=torch.long,
    )
    changed_rate = _as_tensor_metric(
        solver_diagnostics["conflict_aware_changed_vs_base_rate"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    step_values = [int(value) for value in step.detach().cpu().flatten().tolist()]
    episode_values = [int(value) for value in episode_index.detach().cpu().flatten().tolist()]
    env_step_count = max(1, int(num_envs))
    decision_count = env_step_count * max(1, int(num_agents))

    return {
        "method": method,
        "step_min": min(step_values) if step_values else 0,
        "step_max": max(step_values) if step_values else 0,
        "episode_index_min": min(episode_values) if episode_values else 0,
        "episode_index_max": max(episode_values) if episode_values else 0,
        "env_step_count": env_step_count,
        "decision_count": decision_count,
        "conflict_aware_solver_enabled": bool(solver_diagnostics.get("conflict_aware_solver_enabled", False)),
        "conflict_aware_solver_method": solver_diagnostics.get("conflict_aware_solver_method"),
        "conflict_aware_solver_base_method": solver_diagnostics.get("conflict_aware_solver_base_method"),
        "conflict_aware_top_k": int(solver_diagnostics.get("conflict_aware_top_k", 0)),
        "conflict_aware_target_conflict_threshold": float(
            solver_diagnostics.get("conflict_aware_target_conflict_threshold", float("nan"))
        ),
        "conflict_aware_target_conflict_penalty": float(
            solver_diagnostics.get("conflict_aware_target_conflict_penalty", 0.0)
        ),
        "conflict_aware_duplicate_penalty": float(solver_diagnostics.get("conflict_aware_duplicate_penalty", 0.0)),
        "conflict_aware_candidate_combination_count": int(combination_count.sum().item()),
        "conflict_aware_candidate_combination_count_mean": float(combination_count.mean().item()),
        "conflict_aware_selected_score_mean": _mean_finite_tensor(selected_score),
        "conflict_aware_selected_unary_cost_sum_mean": _mean_finite_tensor(selected_unary),
        "conflict_aware_selected_target_conflict_pair_count": int(selected_conflicts.sum().item()),
        "conflict_aware_selected_target_conflict_penalty_sum": float(selected_penalty.sum().item()),
        "conflict_aware_selected_duplicate_pair_count": int(selected_duplicates.sum().item()),
        "conflict_aware_fallback_used": bool(fallback_used.any().item()),
        "conflict_aware_fallback_count": int(fallback_used.to(dtype=torch.long).sum().item()),
        "conflict_aware_fallback_reasons": list(solver_diagnostics.get("conflict_aware_fallback_reasons", [])),
        "conflict_aware_changed_vs_base_count": int(changed_count.sum().item()),
        "conflict_aware_changed_vs_base_rate": float(changed_rate.mean().item()),
        "conflict_aware_changed_pairs_sample": list(
            solver_diagnostics.get("conflict_aware_changed_pairs_sample", [])
        ),
        "conflict_aware_target_conflict_pairs_sample": list(
            solver_diagnostics.get("conflict_aware_target_conflict_pairs_sample", [])
        ),
        "conflict_aware_duplicate_pairs_sample": list(
            solver_diagnostics.get("conflict_aware_duplicate_pairs_sample", [])
        ),
    }


def _first_conflict_aware_reason(rows: list[dict]) -> str | None:
    for row in rows:
        reasons = row.get("conflict_aware_fallback_reasons")
        if isinstance(reasons, list) and reasons:
            return str(reasons[0])
    return None


def _summarize_conflict_aware_solver_rows(rows: list[dict]) -> dict:
    env_step_count = sum(int(row.get("env_step_count", 1)) for row in rows)
    decision_count = sum(int(row.get("decision_count", 0)) for row in rows)
    conflict_count = sum(int(row.get("conflict_aware_selected_target_conflict_pair_count", 0)) for row in rows)
    duplicate_count = sum(int(row.get("conflict_aware_selected_duplicate_pair_count", 0)) for row in rows)
    penalty_sum = sum(float(row.get("conflict_aware_selected_target_conflict_penalty_sum", 0.0)) for row in rows)
    fallback_count = sum(int(row.get("conflict_aware_fallback_count", 0)) for row in rows)
    changed_count = sum(int(row.get("conflict_aware_changed_vs_base_count", 0)) for row in rows)
    return {
        "steps": len(rows),
        "env_step_count": env_step_count,
        "decision_count": decision_count,
        "conflict_aware_solver_enabled": any(
            bool(row.get("conflict_aware_solver_enabled", False)) for row in rows
        ),
        "conflict_aware_solver_method": next(
            (row.get("conflict_aware_solver_method") for row in rows if row.get("conflict_aware_solver_method")),
            None,
        ),
        "conflict_aware_solver_base_method": next(
            (
                row.get("conflict_aware_solver_base_method")
                for row in rows
                if row.get("conflict_aware_solver_base_method")
            ),
            None,
        ),
        "conflict_aware_candidate_combination_count_mean": _mean_row_field(
            rows,
            "conflict_aware_candidate_combination_count_mean",
        ),
        "conflict_aware_selected_score_mean": _mean_row_field(rows, "conflict_aware_selected_score_mean"),
        "conflict_aware_selected_unary_cost_sum_mean": _mean_row_field(
            rows,
            "conflict_aware_selected_unary_cost_sum_mean",
        ),
        "conflict_aware_selected_target_conflict_pair_count": conflict_count,
        "conflict_aware_selected_target_conflict_penalty_sum": penalty_sum,
        "conflict_aware_selected_duplicate_pair_count": duplicate_count,
        "conflict_aware_fallback_step_count": fallback_count,
        "conflict_aware_fallback_rate": fallback_count / float(env_step_count) if env_step_count > 0 else 0.0,
        "conflict_aware_fallback_reason": _first_conflict_aware_reason(rows),
        "conflict_aware_changed_vs_base_count": changed_count,
        "conflict_aware_changed_vs_base_rate": changed_count / float(decision_count) if decision_count > 0 else 0.0,
        "conflict_aware_changed_vs_base_rate_mean": _mean_row_field(rows, "conflict_aware_changed_vs_base_rate"),
    }


def _finalize_conflict_aware_solver_diagnostics(rows: list[dict], methods: list[str]) -> dict:
    config = _conflict_aware_baseline_config()
    threshold = (2.0 * float(config["target_conflict_radius"])) + float(config["target_conflict_safety_margin"])
    diagnostics = {
        "enabled": bool(config["enabled"]),
        "mode": str(config["mode"]),
        "methods": list(config["methods"]),
        "top_k": int(config["top_k"]),
        "target_conflict_radius": float(config["target_conflict_radius"]),
        "target_conflict_safety_margin": float(config["target_conflict_safety_margin"]),
        "target_conflict_threshold": threshold,
        "target_conflict_penalty": float(config["target_conflict_penalty"]),
        "duplicate_penalty": float(config["duplicate_penalty"]),
        "fallback_to_base_method": bool(config["fallback_to_base_method"]),
        "available": bool(rows),
        "original_baseline_methods_changed": False,
        "live_solver_inputs_changed": False,
        "per_step_summary": [],
        "per_episode_summary": [],
        "per_method_summary": {},
        "samples": {
            "changed_pairs_sample": [],
            "target_conflict_pairs_sample": [],
            "duplicate_pairs_sample": [],
        },
    }
    if not rows:
        diagnostics["unavailable_reasons"] = ["no_conflict_aware_solver_steps_recorded"]
        return diagnostics

    for method in methods:
        method_rows = [row for row in rows if row.get("method") == method]
        if not method_rows:
            continue
        diagnostics["per_method_summary"][method] = _summarize_conflict_aware_solver_rows(method_rows)
        for row in method_rows:
            _limited_extend(
                diagnostics["samples"]["changed_pairs_sample"],
                list(row.get("conflict_aware_changed_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )
            _limited_extend(
                diagnostics["samples"]["target_conflict_pairs_sample"],
                list(row.get("conflict_aware_target_conflict_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )
            _limited_extend(
                diagnostics["samples"]["duplicate_pairs_sample"],
                list(row.get("conflict_aware_duplicate_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )

    step_groups: dict[tuple[str, int, int], list[dict]] = {}
    episode_groups: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        method = str(row.get("method", "unknown"))
        step_key = (method, int(row.get("step_min", 0)), int(row.get("step_max", 0)))
        episode_key = (method, int(row.get("episode_index_min", 0)), int(row.get("episode_index_max", 0)))
        step_groups.setdefault(step_key, []).append(row)
        episode_groups.setdefault(episode_key, []).append(row)
    for (method, step_min, step_max), group_rows in sorted(step_groups.items(), key=lambda item: item[0]):
        summary = _summarize_conflict_aware_solver_rows(group_rows)
        summary.update({"method": method, "step_min": step_min, "step_max": step_max})
        diagnostics["per_step_summary"].append(summary)
    for (method, episode_min, episode_max), group_rows in sorted(episode_groups.items(), key=lambda item: item[0]):
        summary = _summarize_conflict_aware_solver_rows(group_rows)
        summary.update({"method": method, "episode_index_min": episode_min, "episode_index_max": episode_max})
        diagnostics["per_episode_summary"].append(summary)
    return diagnostics


def _summarize_actual_base_motion_rows(rows: list[dict], agents: list[str]) -> dict:
    env_step_count = sum(int(row.get("env_step_count", 1)) for row in rows)
    intersection_step_count = sum(int(row.get("actual_base_motion_intersection_step_count", 0)) for row in rows)
    pair_count_total = sum(int(row.get("actual_base_motion_intersection_pair_count", 0)) for row in rows)
    valid_robot_count_sum = sum(int(row.get("actual_base_motion_valid_robot_count", 0)) for row in rows)
    skipped_robot_count_total = sum(int(row.get("actual_base_motion_skipped_robot_count", 0)) for row in rows)
    min_distance_sum = sum(float(row.get("actual_base_motion_min_distance_to_footprint_sum", 0.0)) for row in rows)
    min_distance_count = sum(float(row.get("actual_base_motion_min_distance_to_footprint_count", 0.0)) for row in rows)
    min_distance_min = _min_row_field(rows, "actual_base_motion_min_distance_to_footprint_min")
    by_robot_intersections = {agent: 0 for agent in agents}
    by_robot_valid = {agent: 0 for agent in agents}
    for row in rows:
        for robot_name, count in dict(row.get("actual_base_motion_intersection_count_by_robot", {})).items():
            by_robot_intersections[str(robot_name)] = by_robot_intersections.get(str(robot_name), 0) + int(count)
        for robot_name, count in dict(row.get("actual_base_motion_valid_count_by_robot", {})).items():
            by_robot_valid[str(robot_name)] = by_robot_valid.get(str(robot_name), 0) + int(count)
    by_robot_rate = {
        robot_name: (
            by_robot_intersections.get(robot_name, 0) / float(valid_count) if int(valid_count) > 0 else 0.0
        )
        for robot_name, valid_count in by_robot_valid.items()
    }
    return {
        "steps": len(rows),
        "env_step_count": env_step_count,
        "actual_base_motion_intersection_step_count": intersection_step_count,
        "actual_base_motion_intersection_rate": (
            intersection_step_count / float(env_step_count) if env_step_count > 0 else 0.0
        ),
        "actual_base_motion_intersection_pair_count_total": pair_count_total,
        "actual_base_motion_intersection_pair_count_mean": (
            pair_count_total / float(env_step_count) if env_step_count > 0 else 0.0
        ),
        "actual_base_motion_min_distance_to_footprint_min": min_distance_min,
        "actual_base_motion_min_distance_to_footprint_mean": (
            min_distance_sum / float(min_distance_count) if min_distance_count > 0.0 else float("nan")
        ),
        "actual_base_motion_valid_robot_count_mean": (
            valid_robot_count_sum / float(env_step_count) if env_step_count > 0 else 0.0
        ),
        "actual_base_motion_skipped_robot_count_total": skipped_robot_count_total,
        "actual_base_motion_intersection_count_by_robot": by_robot_intersections,
        "actual_base_motion_intersection_rate_by_robot": by_robot_rate,
    }


def _finalize_actual_base_motion_diagnostics(rows: list[dict], methods: list[str], agents: list[str]) -> dict:
    config = _actual_base_motion_config()
    diagnostics = {
        "enabled": bool(config["enabled"]),
        "mode": str(config["mode"]),
        "obstacle_source": config["obstacle_source"],
        "line_sample_step": float(config["line_sample_step"]),
        "min_motion_distance": float(config["min_motion_distance"]),
        "path_segment_definition": "previous_proxy_base_xy_to_current_proxy_base_xy",
        "diagnostic_only": True,
        "solver_behavior_changed": False,
        "environment_behavior_changed": False,
        "available": bool(rows),
        "per_step_summary": [],
        "per_episode_summary": [],
        "per_method_summary": {},
        "samples": {
            "actual_base_motion_intersection_pairs_sample": [],
        },
    }
    if not rows:
        diagnostics["unavailable_reasons"] = ["no_evaluation_steps_recorded"]
        return diagnostics

    diagnostics["unavailable_reasons"] = sorted(
        {
            str(row.get("actual_base_motion_skipped_reason"))
            for row in rows
            if row.get("actual_base_motion_skipped_reason")
        }
    )
    for method in methods:
        method_rows = [row for row in rows if row.get("method") == method]
        if not method_rows:
            continue
        diagnostics["per_method_summary"][method] = _summarize_actual_base_motion_rows(method_rows, agents)
        for row in method_rows:
            _limited_extend(
                diagnostics["samples"]["actual_base_motion_intersection_pairs_sample"],
                list(row.get("actual_base_motion_intersection_pairs_sample", [])),
                limit=int(config["max_pairs_sample"]),
            )

    step_groups: dict[tuple[str, int, int], list[dict]] = {}
    episode_groups: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        method = str(row.get("method", "unknown"))
        step_key = (method, int(row.get("step_min", 0)), int(row.get("step_max", 0)))
        episode_key = (method, int(row.get("episode_index_min", 0)), int(row.get("episode_index_max", 0)))
        step_groups.setdefault(step_key, []).append(row)
        episode_groups.setdefault(episode_key, []).append(row)
    for (method, step_min, step_max), group_rows in sorted(step_groups.items(), key=lambda item: item[0]):
        summary = _summarize_actual_base_motion_rows(group_rows, agents)
        summary.update({"method": method, "step_min": step_min, "step_max": step_max})
        diagnostics["per_step_summary"].append(summary)
    for (method, episode_min, episode_max), group_rows in sorted(episode_groups.items(), key=lambda item: item[0]):
        summary = _summarize_actual_base_motion_rows(group_rows, agents)
        summary.update({"method": method, "episode_index_min": episode_min, "episode_index_max": episode_max})
        diagnostics["per_episode_summary"].append(summary)
    return diagnostics


def _decode_raw_ids(raw_ids: torch.Tensor, noop_id: int) -> torch.Tensor:
    return torch.where(raw_ids == noop_id, torch.full_like(raw_ids, -1), raw_ids)


def _validate_fixed12_scenario(problem: dict, method: str) -> None:
    num_viewpoints = int(problem["num_viewpoints"])
    if num_viewpoints != 12:
        raise RuntimeError(f"Phase 5 fixed-12 MVP expected 12 viewpoints, got {num_viewpoints}")

    feasible = problem["feasible_mask"].to(dtype=torch.bool)
    available = problem["available_mask"].to(dtype=torch.bool)
    feasible_by_viewpoint = feasible.any(dim=1).all(dim=0)
    if not bool(feasible_by_viewpoint.all()):
        missing = torch.nonzero(~feasible_by_viewpoint, as_tuple=False).flatten().detach().cpu().tolist()
        raise RuntimeError(f"fixed-12 MVP has viewpoints with no feasible agent: {missing}")
    if not bool(available[:, :, 11].any()):
        raise RuntimeError("fixed-12 MVP expected viewpoint 11 to enter available_mask")
    agent2_viewpoint5_available = None
    if int(problem["num_agents"]) > 2:
        agent2_viewpoint5_available = bool(available[0, 2, 5].item())
    if int(problem["num_agents"]) > 2 and bool(feasible[:, 2, 5].any()):
        raise RuntimeError("fixed-12 MVP expected agent_2 -> viewpoint_5 to be infeasible")

    print(
        f"[INFO]: {method} fixed-12 MVP mask ok: "
        f"viewpoint_11_available={available[0, :, 11].detach().cpu().tolist()} "
        f"agent2_viewpoint5_available={agent2_viewpoint5_available}"
    )


def _fixed_n_invariants(unwrapped, problem: dict) -> dict:
    num_envs = int(problem["num_envs"])
    num_agents = int(problem["num_agents"])
    num_viewpoints = int(problem["num_viewpoints"])
    noop_id = int(getattr(unwrapped, "noop_action_id", num_viewpoints))
    available_mask_shape = tuple(problem["available_mask"].shape)
    feasible_mask_shape = tuple(problem["feasible_mask"].shape)
    cost_matrix_shape = tuple(problem["cost_matrix"].shape)
    task_status_shape = tuple(problem["task_status"].shape)
    robot_status_shape = tuple(problem["robot_status"].shape)
    expected_mask_shape = (num_envs, num_agents, num_viewpoints)
    expected_task_status_shape = (num_envs, num_viewpoints)
    expected_robot_status_shape = (num_envs, num_agents)
    available_actions_shape = (num_envs, num_agents, num_viewpoints + 1)

    if num_viewpoints <= 0:
        raise RuntimeError(f"fixed-N evaluation requires at least one viewpoint, got {num_viewpoints}")
    if noop_id != num_viewpoints:
        raise RuntimeError(f"fixed-N invariant failed: expected noop_id={num_viewpoints}, got {noop_id}")
    if available_mask_shape != expected_mask_shape:
        raise RuntimeError(
            f"available_mask shape mismatch: expected {expected_mask_shape}, got {available_mask_shape}"
        )
    if feasible_mask_shape != expected_mask_shape:
        raise RuntimeError(f"feasible_mask shape mismatch: expected {expected_mask_shape}, got {feasible_mask_shape}")
    if cost_matrix_shape != expected_mask_shape:
        raise RuntimeError(f"cost_matrix shape mismatch: expected {expected_mask_shape}, got {cost_matrix_shape}")
    if task_status_shape != expected_task_status_shape:
        raise RuntimeError(
            f"task_status shape mismatch: expected {expected_task_status_shape}, got {task_status_shape}"
        )
    if robot_status_shape != expected_robot_status_shape:
        raise RuntimeError(
            f"robot_status shape mismatch: expected {expected_robot_status_shape}, got {robot_status_shape}"
        )

    return {
        "num_envs": num_envs,
        "num_agents": num_agents,
        "num_viewpoints": num_viewpoints,
        "noop_id": noop_id,
        "action_width": num_viewpoints + 1,
        "available_mask_shape": list(available_mask_shape),
        "feasible_mask_shape": list(feasible_mask_shape),
        "cost_matrix_shape": list(cost_matrix_shape),
        "task_status_shape": list(task_status_shape),
        "robot_status_shape": list(robot_status_shape),
        "available_actions_shape": list(available_actions_shape),
    }


def _is_external_fixed_n(unwrapped) -> bool:
    if args_cli.scenario_config is not None or args_cli.viewpoint_csv_path is not None:
        return True
    return str(getattr(unwrapped, "viewpoint_source", "")).startswith("csv:")


def _validate_evaluation_scenario(unwrapped, problem: dict, method: str) -> None:
    invariants = _fixed_n_invariants(unwrapped, problem)
    if args_cli.expect_num_viewpoints is not None and invariants["num_viewpoints"] != int(args_cli.expect_num_viewpoints):
        raise RuntimeError(
            f"num_viewpoints mismatch: expected {args_cli.expect_num_viewpoints}, "
            f"got {invariants['num_viewpoints']}"
        )
    if not _is_external_fixed_n(unwrapped):
        _validate_fixed12_scenario(problem, method)
    else:
        print(
            f"[INFO]: {method} fixed-N mask ok: "
            f"N={invariants['num_viewpoints']} noop_id={invariants['noop_id']} "
            f"action_width={invariants['action_width']} "
            f"available_actions_shape={tuple(invariants['available_actions_shape'])}"
        )


def _agents_per_viewpoint(mask: torch.Tensor, *, agents: list[str], viewpoint_ids: list[int]) -> dict[str, list[str]]:
    first_env_mask = mask.to(dtype=torch.bool)[0]
    result = {}
    for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
        result[str(viewpoint_id)] = [
            agent for agent_id, agent in enumerate(agents) if bool(first_env_mask[agent_id, viewpoint_index].item())
        ]
    return result


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


def _tensor_values_sample(value: Any, *, limit: int = 10) -> list:
    if not isinstance(value, torch.Tensor):
        return []
    return value.detach().cpu().flatten()[:limit].tolist()


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
            summary[f"{key}_sample"] = _tensor_values_sample(value)
    return summary


def _actual_base_motion_config() -> dict:
    enabled = bool(getattr(args_cli, "actual_base_motion_obstacle_diagnostics_enabled", False))
    mode = str(
        getattr(
            args_cli,
            "actual_base_motion_obstacle_diagnostics_mode",
            "diagnostics_only" if enabled else "disabled",
        )
    ).strip().lower()
    source = getattr(args_cli, "actual_base_motion_obstacle_source", None)
    if enabled and source is None:
        source = "component_mesh_footprint"
    return {
        "enabled": enabled,
        "mode": mode,
        "obstacle_source": str(source).strip().lower() if source is not None else None,
        "line_sample_step": float(getattr(args_cli, "actual_base_motion_line_sample_step", 0.10)),
        "min_motion_distance": float(getattr(args_cli, "actual_base_motion_min_motion_distance", 1.0e-6)),
        "max_pairs_sample": int(getattr(args_cli, "actual_base_motion_max_pairs_sample", 20)),
        "debug_visualization_enabled": bool(
            getattr(args_cli, "actual_base_motion_debug_visualization_enabled", False)
        ),
        "debug_visualization_draw_in_headless": bool(
            getattr(args_cli, "actual_base_motion_debug_visualization_draw_in_headless", False)
        ),
        "debug_visualization_max_lines": int(
            getattr(args_cli, "actual_base_motion_debug_visualization_max_lines", 20)
        ),
        "debug_visualization_line_width": float(
            getattr(args_cli, "actual_base_motion_debug_visualization_line_width", 0.03)
        ),
    }


def _actual_base_motion_static_diagnostics() -> dict:
    config = _actual_base_motion_config()
    return {
        "actual_base_motion_obstacle_diagnostics_enabled": bool(config["enabled"]),
        "actual_base_motion_obstacle_diagnostics_mode": str(config["mode"]),
        "actual_base_motion_obstacle_source": config["obstacle_source"],
        "actual_base_motion_line_sample_step": float(config["line_sample_step"]),
        "actual_base_motion_min_motion_distance": float(config["min_motion_distance"]),
        "actual_base_motion_max_pairs_sample": int(config["max_pairs_sample"]),
        "actual_base_motion_debug_visualization_enabled": bool(config["debug_visualization_enabled"]),
        "actual_base_motion_debug_visualization_draw_in_headless": bool(
            config["debug_visualization_draw_in_headless"]
        ),
        "actual_base_motion_debug_visualization_max_lines": int(config["debug_visualization_max_lines"]),
        "actual_base_motion_debug_visualization_line_width": float(config["debug_visualization_line_width"]),
        "actual_base_motion_path_segment_definition": "previous_proxy_base_xy_to_current_proxy_base_xy",
        "actual_base_motion_diagnostic_only": True,
        "actual_base_motion_solver_behavior_changed": False,
        "actual_base_motion_environment_behavior_changed": False,
    }


def _conflict_aware_baseline_static_diagnostics() -> dict:
    config = _conflict_aware_baseline_config()
    return {
        "conflict_aware_baseline_enabled": bool(config["enabled"]),
        "conflict_aware_baseline_mode": str(config["mode"]),
        "conflict_aware_baseline_methods": list(config["methods"]),
        "conflict_aware_baseline_top_k": int(config["top_k"]),
        "conflict_aware_baseline_target_conflict_radius": float(config["target_conflict_radius"]),
        "conflict_aware_baseline_target_conflict_safety_margin": float(config["target_conflict_safety_margin"]),
        "conflict_aware_baseline_target_conflict_threshold": (
            2.0 * float(config["target_conflict_radius"]) + float(config["target_conflict_safety_margin"])
        ),
        "conflict_aware_baseline_target_conflict_penalty": float(config["target_conflict_penalty"]),
        "conflict_aware_baseline_duplicate_penalty": float(config["duplicate_penalty"]),
        "conflict_aware_baseline_fallback_to_base_method": bool(config["fallback_to_base_method"]),
        "conflict_aware_baseline_max_pairs_sample": int(config["max_pairs_sample"]),
        "conflict_aware_baseline_original_methods_unchanged": True,
    }


def _collect_evaluation_diagnostics(unwrapped, problem: dict, methods: list[str]) -> dict:
    invariants = _fixed_n_invariants(unwrapped, problem)
    agents = list(unwrapped.possible_agents)
    viewpoint_ids = [int(value) for value in problem.get("viewpoint_ids", range(invariants["num_viewpoints"]))]
    feasible_mask = problem["feasible_mask"].to(dtype=torch.bool)
    static_feasible_mask = problem.get("static_geometric_feasible_mask", feasible_mask).to(dtype=torch.bool)
    task_status = problem["task_status"].to(dtype=torch.long)
    robot_status = problem["robot_status"].to(dtype=torch.long)
    task_status_names = problem.get("task_status_names", {})
    robot_status_names = problem.get("robot_status_names", {})
    env_has_feasible_agent = feasible_mask.any(dim=1)
    unavailable_indices = torch.nonzero(~env_has_feasible_agent.any(dim=0), as_tuple=False).flatten()
    permanently_unavailable = [viewpoint_ids[int(index.item())] for index in unavailable_indices.detach().cpu()]
    final_rows = list(problem.get("feasibility_diagnostic_rows", []))
    mesh_diagnostics = None
    if hasattr(unwrapped, "get_component_mesh_diagnostics"):
        mesh_diagnostics = unwrapped.get_component_mesh_diagnostics()
    scenario_diagnostics = problem.get("scenario_diagnostics", {})
    if not scenario_diagnostics and hasattr(unwrapped, "get_scenario_diagnostics"):
        scenario_diagnostics = unwrapped.get_scenario_diagnostics()
    robot_config_diagnostics = None
    if hasattr(unwrapped, "get_robot_config_diagnostics"):
        robot_config_diagnostics = unwrapped.get_robot_config_diagnostics()
    robot_visual_diagnostics = problem.get("robot_visual_diagnostics", {})
    capability_diagnostics = problem.get("capability_diagnostics", {})
    if not capability_diagnostics and hasattr(unwrapped, "get_capability_diagnostics"):
        capability_diagnostics = unwrapped.get_capability_diagnostics()

    diagnostics = {
        "task": args_cli.task,
        "scenario_config_path": SCENARIO_CONFIG.get("_scenario_config_path"),
        "scenario_name": SCENARIO_CONFIG.get("scenario_name"),
        "scenario_type": SCENARIO_CONFIG.get("scenario_type"),
        "viewpoint_csv_path": getattr(unwrapped.cfg, "viewpoint_csv_path", None),
        "robot_config_path": getattr(unwrapped.cfg, "robot_config_path", None),
        "capability_config_path": getattr(unwrapped.cfg, "capability_config_path", None),
        "robot_visual_mode": scenario_diagnostics.get("robot_visual_mode"),
        "component_visual_mode": scenario_diagnostics.get("component_visual_mode"),
        "robot_visual_mesh_enabled": scenario_diagnostics.get("robot_visual_mesh_enabled"),
        "component_mesh_enabled": scenario_diagnostics.get("component_mesh_enabled"),
        "component_proxy_type": scenario_diagnostics.get("component_proxy_type"),
        "component_proxy_center": scenario_diagnostics.get("component_proxy_center"),
        "component_proxy_half_extents": scenario_diagnostics.get("component_proxy_half_extents"),
        "viewpoint_source": getattr(unwrapped, "viewpoint_source", None),
        "viewpoint_ids": viewpoint_ids,
        "methods_evaluated": list(methods),
        "num_episodes": int(args_cli.num_episodes),
        "max_steps": int(args_cli.max_steps),
        "seed": args_cli.seed,
        "viewpoint_candidate_top_k": int(args_cli.viewpoint_candidate_top_k),
        "candidate_mode": _candidate_mode(),
        "external_fixed_n": _is_external_fixed_n(unwrapped),
        "static_geometric_feasible_agents_per_viewpoint": _agents_per_viewpoint(
            static_feasible_mask, agents=agents, viewpoint_ids=viewpoint_ids
        ),
        "feasible_agents_per_viewpoint": _agents_per_viewpoint(feasible_mask, agents=agents, viewpoint_ids=viewpoint_ids),
        "task_status_counts": status_counts(task_status, task_status_names),
        "robot_status_counts": status_counts(robot_status, robot_status_names),
        "task_status_names": task_status_names,
        "robot_status_names": robot_status_names,
        "permanently_unavailable_viewpoints": permanently_unavailable,
        "manual_feasibility_override_rows": list(problem.get("manual_feasibility_override_rows", [])),
        "infeasible_rows": [row for row in final_rows if not row.get("feasible", False)],
    }
    diagnostics.update(_level2_pair_filter_diagnostics())
    diagnostics.update(_retry_fallback_static_diagnostics())
    diagnostics.update(invariants)
    if mesh_diagnostics is not None:
        diagnostics["component_mesh_diagnostics"] = mesh_diagnostics
    if scenario_diagnostics:
        diagnostics["scenario_diagnostics"] = scenario_diagnostics
    if robot_config_diagnostics:
        diagnostics["robot_config_diagnostics"] = robot_config_diagnostics
    if robot_visual_diagnostics:
        diagnostics["robot_visual_diagnostics"] = robot_visual_diagnostics
    if capability_diagnostics:
        diagnostics["capability_diagnostics"] = capability_diagnostics
    diagnostics.update(_obstacle_diagnostics_summary(problem, agents=agents, viewpoint_ids=viewpoint_ids))
    diagnostics.update(_inter_robot_conflict_diagnostics_summary(problem))
    diagnostics.update(_actual_base_motion_static_diagnostics())
    diagnostics.update(_conflict_aware_baseline_static_diagnostics())
    return diagnostics


def _init_buffers(
    num_envs: int,
    device: torch.device,
    *,
    num_agents: int = 0,
    num_viewpoints: int = 0,
) -> dict[str, torch.Tensor]:
    return {
        "length": torch.zeros(num_envs, dtype=torch.long, device=device),
        "return": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "coverage_auc": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "final_coverage": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "final_covered_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "steps_to_full": torch.full((num_envs,), -1, dtype=torch.long, device=device),
        "duplicate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "noop_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "valid_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "decision_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "new_viewpoints_total": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "per_robot_selected_count": torch.zeros((num_envs, num_agents), dtype=torch.long, device=device),
        "per_robot_completed_count": torch.zeros((num_envs, num_agents), dtype=torch.float32, device=device),
        "per_robot_repeated_assignment_count": torch.zeros(
            (num_envs, num_agents), dtype=torch.long, device=device
        ),
        "per_viewpoint_attempted_count": torch.zeros(
            (num_envs, num_viewpoints), dtype=torch.long, device=device
        ),
        "previous_assignment": torch.full((num_envs, num_agents), -2, dtype=torch.long, device=device),
        "last_global_coverage_gain_step": torch.full((num_envs,), -1, dtype=torch.long, device=device),
        "steps_since_last_global_coverage_gain": torch.zeros(num_envs, dtype=torch.long, device=device),
        "duplicate_selected_target_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "noop_when_available_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "selected_path_cost_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_path_cost_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_path_cost_max": torch.full((num_envs,), -float("inf"), dtype=torch.float32, device=device),
        "post_gain_repeated_pair_count": torch.zeros(
            (num_envs, num_agents, num_viewpoints), dtype=torch.long, device=device
        ),
        "unattributed_completed_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_overlap_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "inter_robot_overlap_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "inter_robot_min_distance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_min_distance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_min_distance_min": torch.full((num_envs,), float("inf"), dtype=torch.float32, device=device),
        "inter_robot_min_clearance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_min_clearance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_min_clearance_min": torch.full((num_envs,), float("inf"), dtype=torch.float32, device=device),
        "selected_target_conflict_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "selected_target_conflict_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "selected_target_min_distance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_min_distance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_min_distance_min": torch.full((num_envs,), float("inf"), dtype=torch.float32, device=device),
        "selected_target_min_clearance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_min_clearance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_min_clearance_min": torch.full((num_envs,), float("inf"), dtype=torch.float32, device=device),
        "selected_target_skipped_robot_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "selected_target_valid_robot_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_intersection_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "actual_base_motion_intersection_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "actual_base_motion_intersection_pair_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_min_distance_to_footprint_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_min_distance_to_footprint_count": torch.zeros(
            num_envs, dtype=torch.float32, device=device
        ),
        "actual_base_motion_min_distance_to_footprint_min": torch.full(
            (num_envs,), float("inf"), dtype=torch.float32, device=device
        ),
        "actual_base_motion_valid_robot_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_skipped_robot_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "baseline_selected_target_conflict_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "baseline_selected_target_conflict_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "baseline_selected_target_conflict_rate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "baseline_selected_target_min_distance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "baseline_selected_target_min_distance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "baseline_selected_target_min_distance_min": torch.full(
            (num_envs,), float("inf"), dtype=torch.float32, device=device
        ),
        "baseline_selected_target_min_clearance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "baseline_selected_target_min_clearance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "baseline_selected_target_min_clearance_min": torch.full(
            (num_envs,), float("inf"), dtype=torch.float32, device=device
        ),
        "baseline_selected_target_conflict_penalty_sum_total": torch.zeros(
            num_envs, dtype=torch.float32, device=device
        ),
        "candidate_selected_target_conflict_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "candidate_selected_target_conflict_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "candidate_selected_target_conflict_rate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "candidate_selected_target_min_distance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "candidate_selected_target_min_distance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "candidate_selected_target_min_distance_min": torch.full(
            (num_envs,), float("inf"), dtype=torch.float32, device=device
        ),
        "candidate_selected_target_min_clearance_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "candidate_selected_target_min_clearance_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "candidate_selected_target_min_clearance_min": torch.full(
            (num_envs,), float("inf"), dtype=torch.float32, device=device
        ),
        "candidate_selected_target_conflict_penalty_sum_total": torch.zeros(
            num_envs, dtype=torch.float32, device=device
        ),
        "candidate_changed_assignment_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "candidate_changed_assignment_rate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_solver_enabled_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "conflict_aware_solver_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "conflict_aware_candidate_combination_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_selected_score_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_selected_score_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_selected_unary_cost_sum_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_selected_unary_cost_sum_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "conflict_aware_selected_target_conflict_pair_count_total": torch.zeros(
            num_envs, dtype=torch.long, device=device
        ),
        "conflict_aware_selected_target_conflict_penalty_sum_total": torch.zeros(
            num_envs, dtype=torch.float32, device=device
        ),
        "conflict_aware_selected_duplicate_pair_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "conflict_aware_fallback_step_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "conflict_aware_changed_vs_base_count_total": torch.zeros(num_envs, dtype=torch.long, device=device),
        "conflict_aware_changed_vs_base_rate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
    }


def _assignment_reporting_step_diagnostics(
    buffers: dict[str, torch.Tensor],
    problem: dict,
    assignment: torch.Tensor,
) -> dict[str, torch.Tensor]:
    num_envs, num_agents = assignment.shape
    device = assignment.device
    previous_assignment = buffers.get("previous_assignment")
    if not isinstance(previous_assignment, torch.Tensor) or tuple(previous_assignment.shape) != tuple(assignment.shape):
        previous_assignment = torch.full_like(assignment, -2)

    is_non_noop = assignment >= 0
    is_repeated_assignment = is_non_noop & (assignment == previous_assignment)
    duplicate_selected_target_count = compute_assignment_duplicate_count(assignment).to(dtype=torch.long)

    available_mask = problem.get("available_mask")
    if isinstance(available_mask, torch.Tensor):
        available_mask_bool = available_mask.to(device=device, dtype=torch.bool)
        available_viewpoint_count = available_mask_bool.sum(dim=-1).to(dtype=torch.long)
        noop_when_available = (assignment < 0) & (available_viewpoint_count > 0)
    else:
        available_viewpoint_count = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)
        noop_when_available = torch.zeros((num_envs, num_agents), dtype=torch.bool, device=device)

    selected_path_cost = torch.full((num_envs, num_agents), float("nan"), dtype=torch.float32, device=device)
    cost_matrix = problem.get("cost_matrix")
    if isinstance(cost_matrix, torch.Tensor):
        cost_matrix = cost_matrix.to(device=device, dtype=torch.float32)
        for env_id_tensor, agent_id_tensor in torch.nonzero(is_non_noop, as_tuple=False):
            env_id = int(env_id_tensor.item())
            agent_id = int(agent_id_tensor.item())
            viewpoint_index = int(assignment[env_id, agent_id].item())
            if 0 <= viewpoint_index < cost_matrix.shape[2]:
                selected_path_cost[env_id, agent_id] = cost_matrix[env_id, agent_id, viewpoint_index]

    return {
        "is_non_noop": is_non_noop,
        "is_repeated_assignment": is_repeated_assignment,
        "duplicate_selected_target_count": duplicate_selected_target_count,
        "available_viewpoint_count": available_viewpoint_count,
        "noop_when_available": noop_when_available,
        "selected_path_cost": selected_path_cost,
    }


def _update_assignment_reporting_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    assignment: torch.Tensor,
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    new_viewpoints: torch.Tensor,
    reporting_step: dict[str, torch.Tensor],
) -> None:
    num_envs, num_agents = assignment.shape
    num_viewpoints = covered_after.shape[1]
    is_non_noop = reporting_step["is_non_noop"].to(dtype=torch.bool)
    is_repeated_assignment = reporting_step["is_repeated_assignment"].to(dtype=torch.bool)
    noop_when_available = reporting_step["noop_when_available"].to(dtype=torch.bool)
    selected_path_cost = reporting_step["selected_path_cost"].to(dtype=torch.float32)

    buffers["per_robot_selected_count"] += is_non_noop.to(dtype=torch.long)
    buffers["per_robot_repeated_assignment_count"] += is_repeated_assignment.to(dtype=torch.long)
    buffers["duplicate_selected_target_count"] += reporting_step["duplicate_selected_target_count"].to(dtype=torch.long)
    buffers["noop_when_available_count"] += noop_when_available.sum(dim=1).to(dtype=torch.long)

    for env_id in range(num_envs):
        for agent_id in range(num_agents):
            viewpoint_index = int(assignment[env_id, agent_id].item())
            if 0 <= viewpoint_index < num_viewpoints:
                buffers["per_viewpoint_attempted_count"][env_id, viewpoint_index] += 1

        newly_covered_indices = torch.nonzero(covered_after[env_id] & (~covered_before[env_id]), as_tuple=False)
        for viewpoint_index_tensor in newly_covered_indices.flatten():
            viewpoint_index = int(viewpoint_index_tensor.item())
            selected_agents = torch.nonzero(assignment[env_id] == viewpoint_index, as_tuple=False).flatten()
            if selected_agents.numel() == 0:
                buffers["unattributed_completed_count"][env_id] += 1.0
                continue
            credit = 1.0 / float(selected_agents.numel())
            for agent_id_tensor in selected_agents:
                buffers["per_robot_completed_count"][env_id, int(agent_id_tensor.item())] += credit

    finite_cost = torch.isfinite(selected_path_cost)
    if bool(finite_cost.any()):
        buffers["selected_path_cost_sum"] += torch.where(
            finite_cost,
            selected_path_cost,
            torch.zeros_like(selected_path_cost),
        ).sum(dim=1)
        buffers["selected_path_cost_count"] += finite_cost.sum(dim=1).to(dtype=torch.float32)
        row_max = torch.where(finite_cost, selected_path_cost, torch.full_like(selected_path_cost, -float("inf"))).max(
            dim=1
        ).values
        buffers["selected_path_cost_max"] = torch.maximum(buffers["selected_path_cost_max"], row_max)

    coverage_gain = new_viewpoints.to(dtype=torch.float32) > 0.0
    buffers["last_global_coverage_gain_step"] = torch.where(
        coverage_gain,
        buffers["length"],
        buffers["last_global_coverage_gain_step"],
    )
    no_previous_gain = buffers["last_global_coverage_gain_step"] < 0
    buffers["steps_since_last_global_coverage_gain"] = torch.where(
        no_previous_gain,
        buffers["length"],
        buffers["length"] - buffers["last_global_coverage_gain_step"],
    )

    if "post_gain_repeated_pair_count" in buffers:
        for env_id in range(num_envs):
            if bool(coverage_gain[env_id].item()):
                buffers["post_gain_repeated_pair_count"][env_id].zero_()
                continue
            for agent_id in range(num_agents):
                if not bool(is_repeated_assignment[env_id, agent_id].item()):
                    continue
                viewpoint_index = int(assignment[env_id, agent_id].item())
                if 0 <= viewpoint_index < num_viewpoints:
                    buffers["post_gain_repeated_pair_count"][env_id, agent_id, viewpoint_index] += 1

    buffers["previous_assignment"] = assignment.to(dtype=torch.long).clone()


def _update_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    reward_sum: torch.Tensor,
    assignment: torch.Tensor,
    valid_decisions: torch.Tensor,
    covered_before: torch.Tensor,
    covered_mask: torch.Tensor,
    new_viewpoints: torch.Tensor,
    reporting_step: dict[str, torch.Tensor] | None = None,
) -> None:
    num_agents = assignment.shape[1]
    num_viewpoints = covered_mask.shape[1]
    covered_count = covered_mask.sum(dim=-1).to(dtype=torch.long)
    coverage = covered_count.to(dtype=torch.float32) / float(num_viewpoints)
    buffers["length"] += 1
    buffers["return"] += reward_sum
    buffers["coverage_auc"] += coverage
    buffers["final_coverage"] = coverage
    buffers["final_covered_count"] = covered_count
    buffers["covered_mask"] = covered_mask.to(dtype=torch.bool).clone()
    buffers["duplicate_sum"] += compute_assignment_duplicate_count(assignment)
    buffers["noop_count"] += (assignment < 0).sum(dim=1).to(dtype=torch.float32)
    buffers["valid_count"] += valid_decisions.sum(dim=1).to(dtype=torch.float32)
    buffers["decision_count"] += float(num_agents)
    buffers["new_viewpoints_total"] += new_viewpoints.to(dtype=torch.float32)

    hit_full = (buffers["steps_to_full"] < 0) & (covered_count == num_viewpoints)
    buffers["steps_to_full"][hit_full] = buffers["length"][hit_full]
    if reporting_step is not None:
        _update_assignment_reporting_buffers(
            buffers,
            assignment=assignment,
            covered_before=covered_before.to(dtype=torch.bool),
            covered_after=covered_mask.to(dtype=torch.bool),
            new_viewpoints=new_viewpoints,
            reporting_step=reporting_step,
        )


def _as_tensor_metric(value: Any, num_envs: int, device: torch.device, *, dtype: torch.dtype) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        tensor = value.to(device=device, dtype=dtype).flatten()
    else:
        tensor = torch.as_tensor(value, dtype=dtype, device=device).flatten()
    if tensor.numel() == 1:
        return tensor.expand(num_envs)
    if tensor.numel() != num_envs:
        raise RuntimeError(f"diagnostic tensor size mismatch: expected {num_envs}, got {tensor.numel()}")
    return tensor


def _accumulate_min_metric(buffers: dict[str, torch.Tensor], prefix: str, name: str, values: torch.Tensor) -> None:
    finite = torch.isfinite(values)
    if not bool(finite.any()):
        return
    sum_key = f"{prefix}_{name}_sum"
    count_key = f"{prefix}_{name}_count"
    min_key = f"{prefix}_{name}_min"
    buffers[sum_key] += torch.where(finite, values, torch.zeros_like(values))
    buffers[count_key] += finite.to(dtype=torch.float32)
    buffers[min_key] = torch.where(finite, torch.minimum(buffers[min_key], values), buffers[min_key])


def _update_inter_robot_conflict_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    current_overlap: dict,
    selected_target: dict,
    num_envs: int,
    device: torch.device,
) -> None:
    overlap_pair_count = _as_tensor_metric(
        current_overlap.get("inter_robot_overlap_pair_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["inter_robot_overlap_step_count"] += (overlap_pair_count > 0).to(dtype=torch.long)
    buffers["inter_robot_overlap_pair_count_total"] += overlap_pair_count
    _accumulate_min_metric(
        buffers,
        "inter_robot",
        "min_distance",
        _as_tensor_metric(
            current_overlap.get("inter_robot_min_distance", torch.full((num_envs,), float("nan"), device=device)),
            num_envs,
            device,
            dtype=torch.float32,
        ),
    )
    _accumulate_min_metric(
        buffers,
        "inter_robot",
        "min_clearance",
        _as_tensor_metric(
            current_overlap.get("inter_robot_min_clearance", torch.full((num_envs,), float("nan"), device=device)),
            num_envs,
            device,
            dtype=torch.float32,
        ),
    )

    target_pair_count = _as_tensor_metric(
        selected_target.get("selected_target_conflict_pair_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["selected_target_conflict_step_count"] += (target_pair_count > 0).to(dtype=torch.long)
    buffers["selected_target_conflict_pair_count_total"] += target_pair_count
    _accumulate_min_metric(
        buffers,
        "selected_target",
        "min_distance",
        _as_tensor_metric(
            selected_target.get("selected_target_min_distance", torch.full((num_envs,), float("nan"), device=device)),
            num_envs,
            device,
            dtype=torch.float32,
        ),
    )
    _accumulate_min_metric(
        buffers,
        "selected_target",
        "min_clearance",
        _as_tensor_metric(
            selected_target.get("selected_target_min_clearance", torch.full((num_envs,), float("nan"), device=device)),
            num_envs,
            device,
            dtype=torch.float32,
        ),
    )
    buffers["selected_target_skipped_robot_count_total"] += _as_tensor_metric(
        selected_target.get("selected_target_skipped_robot_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["selected_target_valid_robot_count_sum"] += _as_tensor_metric(
        selected_target.get("selected_target_valid_robot_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.float32,
    )


def _footprint_cell_centers(footprint: Any) -> tuple[tuple[float, float], ...]:
    cache_key = id(footprint)
    centers = _FOOTPRINT_CELL_CENTER_CACHE.get(cache_key)
    if centers is not None:
        return centers
    cells = getattr(footprint, "inflated_occupied_cells", ()) or ()
    center_values = []
    for row, col in cells:
        x, y = footprint.cell_center(row, col)
        center_values.append((float(x), float(y)))
    centers = tuple(center_values)
    _FOOTPRINT_CELL_CENTER_CACHE[cache_key] = centers
    return centers


def _segment_min_distance_to_footprint(
    footprint: Any,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    *,
    line_sample_step: float,
) -> float:
    centers = _footprint_cell_centers(footprint)
    if not centers:
        return float("nan")
    dx = end_xy[0] - start_xy[0]
    dy = end_xy[1] - start_xy[1]
    length = math.hypot(dx, dy)
    sample_step = max(float(line_sample_step), 1.0e-9)
    sample_count = max(1, int(math.ceil(length / sample_step)))
    min_distance = float("inf")
    for sample_index in range(sample_count + 1):
        alpha = sample_index / sample_count
        point = (start_xy[0] + alpha * dx, start_xy[1] + alpha * dy)
        if footprint.contains_xy(point):
            return 0.0
        for center in centers:
            distance = math.hypot(point[0] - center[0], point[1] - center[1])
            if distance < min_distance:
                min_distance = distance
    return min_distance if math.isfinite(min_distance) else float("nan")


def _actual_base_motion_step_diagnostics(
    *,
    unwrapped: Any,
    method: str,
    step: torch.Tensor,
    episode_index: torch.Tensor,
    assignment: torch.Tensor,
    previous_base_pos: torch.Tensor,
    current_base_pos: torch.Tensor,
    env_done: torch.Tensor,
    agents: list[str],
    viewpoint_ids: list[int],
) -> dict:
    config = _actual_base_motion_config()
    num_envs, num_agents = assignment.shape
    device = assignment.device
    pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    valid_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    skipped_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    min_distance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    robot_intersects = torch.zeros((num_envs, num_agents), dtype=torch.bool, device=device)
    robot_motion_distance = torch.full((num_envs, num_agents), float("nan"), dtype=torch.float32, device=device)
    robot_valid = torch.zeros((num_envs, num_agents), dtype=torch.bool, device=device)
    robot_skipped = torch.zeros((num_envs, num_agents), dtype=torch.bool, device=device)

    step_values = [int(value) for value in step.detach().cpu().flatten().tolist()]
    episode_values = [int(value) for value in episode_index.detach().cpu().flatten().tolist()]
    row = {
        "method": method,
        "step_min": min(step_values) if step_values else 0,
        "step_max": max(step_values) if step_values else 0,
        "episode_index_min": min(episode_values) if episode_values else 0,
        "episode_index_max": max(episode_values) if episode_values else 0,
        "env_step_count": num_envs,
        "decision_count": num_envs * num_agents,
        "actual_base_motion_obstacle_diagnostics_enabled": bool(config["enabled"]),
        "actual_base_motion_obstacle_diagnostics_mode": str(config["mode"]),
        "actual_base_motion_obstacle_source": config["obstacle_source"],
        "actual_base_motion_path_segment_definition": "previous_proxy_base_xy_to_current_proxy_base_xy",
        "actual_base_motion_line_sample_step": float(config["line_sample_step"]),
        "actual_base_motion_min_motion_distance": float(config["min_motion_distance"]),
        "actual_base_motion_intersection_pairs_sample": [],
        "actual_base_motion_skipped_reason": None,
        "_actual_base_motion_intersection_pair_count_tensor": pair_count,
        "_actual_base_motion_valid_robot_count_tensor": valid_count,
        "_actual_base_motion_skipped_robot_count_tensor": skipped_count,
        "_actual_base_motion_min_distance_tensor": min_distance,
        "_actual_base_motion_intersection_by_robot": robot_intersects,
        "_actual_base_motion_distance_by_robot": robot_motion_distance,
        "_actual_base_motion_valid_by_robot": robot_valid,
        "_actual_base_motion_skipped_by_robot": robot_skipped,
    }

    if not bool(config["enabled"]):
        row["actual_base_motion_skipped_reason"] = "disabled"
        return row
    if str(config["mode"]) != "diagnostics_only":
        row["actual_base_motion_skipped_reason"] = "unsupported_mode"
        return row
    if config["obstacle_source"] != "component_mesh_footprint":
        row["actual_base_motion_skipped_reason"] = "unsupported_obstacle_source"
        return row
    footprint = getattr(unwrapped.cfg, "component_obstacle_footprint", None)
    if footprint is None:
        row["actual_base_motion_skipped_reason"] = "component_mesh_footprint_unavailable"
        return row

    max_pairs_sample = int(config["max_pairs_sample"])
    sample: list[dict] = []
    min_motion_distance = float(config["min_motion_distance"])
    line_sample_step = float(config["line_sample_step"])
    env_done_cpu = env_done.detach().cpu().to(dtype=torch.bool)
    previous_cpu = previous_base_pos.detach().cpu()
    current_cpu = current_base_pos.detach().cpu()
    assignment_cpu = assignment.detach().cpu()
    step_cpu = step.detach().cpu()

    by_robot_intersection_count = {agent: 0 for agent in agents[:num_agents]}
    by_robot_valid_count = {agent: 0 for agent in agents[:num_agents]}
    min_distance_sum = torch.zeros(num_envs, dtype=torch.float32, device=device)
    min_distance_count = torch.zeros(num_envs, dtype=torch.float32, device=device)

    for env_id in range(num_envs):
        if bool(env_done_cpu[env_id].item()):
            skipped_count[env_id] += num_agents
            robot_skipped[env_id, :] = True
            continue
        env_min_distance = float("inf")
        for agent_id in range(num_agents):
            start_xy = (
                float(previous_cpu[env_id, agent_id, 0].item()),
                float(previous_cpu[env_id, agent_id, 1].item()),
            )
            end_xy = (
                float(current_cpu[env_id, agent_id, 0].item()),
                float(current_cpu[env_id, agent_id, 1].item()),
            )
            motion_distance = math.hypot(end_xy[0] - start_xy[0], end_xy[1] - start_xy[1])
            robot_motion_distance[env_id, agent_id] = float(motion_distance)
            if motion_distance < min_motion_distance:
                skipped_count[env_id] += 1
                robot_skipped[env_id, agent_id] = True
                continue

            valid_count[env_id] += 1
            robot_valid[env_id, agent_id] = True
            robot_name = agents[agent_id] if agent_id < len(agents) else f"agent_{agent_id}"
            by_robot_valid_count[robot_name] = by_robot_valid_count.get(robot_name, 0) + 1
            intersects = bool(footprint.intersects_segment(start_xy, end_xy))
            if intersects:
                pair_count[env_id] += 1
                robot_intersects[env_id, agent_id] = True
                by_robot_intersection_count[robot_name] = by_robot_intersection_count.get(robot_name, 0) + 1
                segment_min_distance = 0.0
            else:
                segment_min_distance = _segment_min_distance_to_footprint(
                    footprint,
                    start_xy,
                    end_xy,
                    line_sample_step=line_sample_step,
                )
            if math.isfinite(segment_min_distance):
                env_min_distance = min(env_min_distance, segment_min_distance)
                min_distance_sum[env_id] += float(segment_min_distance)
                min_distance_count[env_id] += 1.0

            if intersects and len(sample) < max_pairs_sample:
                assigned_index = int(assignment_cpu[env_id, agent_id].item())
                selected_viewpoint_id = -1
                if assigned_index >= 0 and assigned_index < len(viewpoint_ids):
                    selected_viewpoint_id = int(viewpoint_ids[assigned_index])
                sample.append(
                    {
                        "env_id": env_id,
                        "method": method,
                        "step": int(step_cpu[env_id].item()) if step_cpu.numel() > env_id else row["step_min"],
                        "robot_id": agent_id,
                        "robot_name": robot_name,
                        "prev_base_xy": [start_xy[0], start_xy[1]],
                        "current_base_xy": [end_xy[0], end_xy[1]],
                        "motion_distance": float(motion_distance),
                        "selected_viewpoint_id": selected_viewpoint_id,
                        "intersects_component_mesh_footprint": True,
                    }
                )
        if math.isfinite(env_min_distance):
            min_distance[env_id] = float(env_min_distance)

    row.update(
        {
            "actual_base_motion_intersection_pair_count": int(pair_count.sum().item()),
            "actual_base_motion_intersection_step_count": int((pair_count > 0).to(dtype=torch.long).sum().item()),
            "actual_base_motion_intersection_any": bool((pair_count > 0).any().item()),
            "actual_base_motion_valid_robot_count": int(valid_count.sum().item()),
            "actual_base_motion_skipped_robot_count": int(skipped_count.sum().item()),
            "actual_base_motion_min_distance_to_footprint": _mean_finite_tensor(min_distance),
            "actual_base_motion_min_distance_to_footprint_min": (
                float(min_distance[torch.isfinite(min_distance)].min().item())
                if bool(torch.isfinite(min_distance).any())
                else float("nan")
            ),
            "actual_base_motion_min_distance_to_footprint_sum": float(min_distance_sum.sum().item()),
            "actual_base_motion_min_distance_to_footprint_count": float(min_distance_count.sum().item()),
            "actual_base_motion_intersection_count_by_robot": by_robot_intersection_count,
            "actual_base_motion_valid_count_by_robot": by_robot_valid_count,
            "actual_base_motion_intersection_pairs_sample": sample,
        }
    )
    return row


def _update_actual_base_motion_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    diagnostics: dict,
    num_envs: int,
    device: torch.device,
) -> None:
    if "_actual_base_motion_intersection_pair_count_tensor" not in diagnostics:
        return
    pair_count = _as_tensor_metric(
        diagnostics["_actual_base_motion_intersection_pair_count_tensor"],
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["actual_base_motion_intersection_step_count"] += (pair_count > 0).to(dtype=torch.long)
    buffers["actual_base_motion_intersection_pair_count_total"] += pair_count
    buffers["actual_base_motion_intersection_pair_count_sum"] += pair_count.to(dtype=torch.float32)
    buffers["actual_base_motion_valid_robot_count_sum"] += _as_tensor_metric(
        diagnostics["_actual_base_motion_valid_robot_count_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    buffers["actual_base_motion_skipped_robot_count_total"] += _as_tensor_metric(
        diagnostics["_actual_base_motion_skipped_robot_count_tensor"],
        num_envs,
        device,
        dtype=torch.long,
    )
    _accumulate_min_metric(
        buffers,
        "actual_base_motion",
        "min_distance_to_footprint",
        _as_tensor_metric(
            diagnostics["_actual_base_motion_min_distance_tensor"],
            num_envs,
            device,
            dtype=torch.float32,
        ),
    )


def _update_target_conflict_candidate_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    comparison: dict,
    num_envs: int,
    device: torch.device,
) -> None:
    if "_baseline_conflict_pair_count_tensor" not in comparison:
        return
    baseline_conflict_count = _as_tensor_metric(
        comparison["_baseline_conflict_pair_count_tensor"],
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["baseline_selected_target_conflict_step_count"] += (baseline_conflict_count > 0).to(dtype=torch.long)
    buffers["baseline_selected_target_conflict_pair_count_total"] += baseline_conflict_count
    buffers["baseline_selected_target_conflict_rate_sum"] += _as_tensor_metric(
        comparison["_baseline_conflict_rate_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    buffers["baseline_selected_target_conflict_penalty_sum_total"] += _as_tensor_metric(
        comparison["_baseline_penalty_sum_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    _accumulate_min_metric(
        buffers,
        "baseline_selected_target",
        "min_distance",
        _as_tensor_metric(comparison["_baseline_min_distance_tensor"], num_envs, device, dtype=torch.float32),
    )
    _accumulate_min_metric(
        buffers,
        "baseline_selected_target",
        "min_clearance",
        _as_tensor_metric(comparison["_baseline_min_clearance_tensor"], num_envs, device, dtype=torch.float32),
    )

    if "_candidate_conflict_pair_count_tensor" not in comparison:
        return
    candidate_conflict_count = _as_tensor_metric(
        comparison["_candidate_conflict_pair_count_tensor"],
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["candidate_selected_target_conflict_step_count"] += (candidate_conflict_count > 0).to(dtype=torch.long)
    buffers["candidate_selected_target_conflict_pair_count_total"] += candidate_conflict_count
    buffers["candidate_selected_target_conflict_rate_sum"] += _as_tensor_metric(
        comparison["_candidate_conflict_rate_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    buffers["candidate_selected_target_conflict_penalty_sum_total"] += _as_tensor_metric(
        comparison["_candidate_penalty_sum_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )
    _accumulate_min_metric(
        buffers,
        "candidate_selected_target",
        "min_distance",
        _as_tensor_metric(comparison["_candidate_min_distance_tensor"], num_envs, device, dtype=torch.float32),
    )
    _accumulate_min_metric(
        buffers,
        "candidate_selected_target",
        "min_clearance",
        _as_tensor_metric(comparison["_candidate_min_clearance_tensor"], num_envs, device, dtype=torch.float32),
    )
    buffers["candidate_changed_assignment_count_total"] += _as_tensor_metric(
        comparison["_candidate_changed_count_tensor"],
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["candidate_changed_assignment_rate_sum"] += _as_tensor_metric(
        comparison["_candidate_changed_rate_tensor"],
        num_envs,
        device,
        dtype=torch.float32,
    )


def _update_conflict_aware_solver_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    solver_diagnostics: dict | None,
    num_envs: int,
    device: torch.device,
) -> None:
    if not solver_diagnostics:
        return
    if "conflict_aware_candidate_combination_count" not in solver_diagnostics:
        return

    enabled = bool(solver_diagnostics.get("conflict_aware_solver_enabled", False))
    buffers["conflict_aware_solver_step_count"] += 1
    if enabled:
        buffers["conflict_aware_solver_enabled_count"] += 1

    combination_count = _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_candidate_combination_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.float32,
    )
    buffers["conflict_aware_candidate_combination_count_sum"] += combination_count

    selected_score = _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_selected_score", torch.full((num_envs,), float("nan"), device=device)),
        num_envs,
        device,
        dtype=torch.float32,
    )
    finite_score = torch.isfinite(selected_score)
    buffers["conflict_aware_selected_score_sum"] += torch.where(
        finite_score, selected_score, torch.zeros_like(selected_score)
    )
    buffers["conflict_aware_selected_score_count"] += finite_score.to(dtype=torch.float32)

    selected_unary = _as_tensor_metric(
        solver_diagnostics.get(
            "conflict_aware_selected_unary_cost_sum", torch.full((num_envs,), float("nan"), device=device)
        ),
        num_envs,
        device,
        dtype=torch.float32,
    )
    finite_unary = torch.isfinite(selected_unary)
    buffers["conflict_aware_selected_unary_cost_sum_sum"] += torch.where(
        finite_unary, selected_unary, torch.zeros_like(selected_unary)
    )
    buffers["conflict_aware_selected_unary_cost_sum_count"] += finite_unary.to(dtype=torch.float32)

    buffers["conflict_aware_selected_target_conflict_pair_count_total"] += _as_tensor_metric(
        solver_diagnostics.get(
            "conflict_aware_selected_target_conflict_pair_count", torch.zeros(num_envs, device=device)
        ),
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["conflict_aware_selected_target_conflict_penalty_sum_total"] += _as_tensor_metric(
        solver_diagnostics.get(
            "conflict_aware_selected_target_conflict_penalty_sum", torch.zeros(num_envs, device=device)
        ),
        num_envs,
        device,
        dtype=torch.float32,
    )
    buffers["conflict_aware_selected_duplicate_pair_count_total"] += _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_selected_duplicate_pair_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.long,
    )
    fallback_used = _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_fallback_used", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.bool,
    )
    buffers["conflict_aware_fallback_step_count"] += fallback_used.to(dtype=torch.long)
    buffers["conflict_aware_changed_vs_base_count_total"] += _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_changed_vs_base_count", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.long,
    )
    buffers["conflict_aware_changed_vs_base_rate_sum"] += _as_tensor_metric(
        solver_diagnostics.get("conflict_aware_changed_vs_base_rate", torch.zeros(num_envs, device=device)),
        num_envs,
        device,
        dtype=torch.float32,
    )


def _covered_id_lists(covered_mask: torch.Tensor, viewpoint_ids: list[int]) -> tuple[list[int], list[int]]:
    covered = []
    uncovered = []
    for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
        if bool(covered_mask[viewpoint_index].item()):
            covered.append(int(viewpoint_id))
        else:
            uncovered.append(int(viewpoint_id))
    return covered, uncovered


def _covered_ids_from_mask(covered_mask: torch.Tensor, viewpoint_ids: list[int]) -> list[int]:
    return [
        int(viewpoint_id)
        for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids)
        if bool(covered_mask[viewpoint_index].item())
    ]


def _append_assignment_history_step(
    pending_history_by_env: dict[int, list[dict]],
    *,
    method: str,
    step: torch.Tensor,
    assignment: torch.Tensor,
    valid_decisions: torch.Tensor,
    reporting_step: dict[str, torch.Tensor],
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    viewpoint_ids: list[int],
    retry_fallback_info: dict[tuple[int, int], dict] | None = None,
    actual_base_motion: dict | None = None,
) -> None:
    num_envs, num_agents = assignment.shape
    num_viewpoints = len(viewpoint_ids)
    covered_before_count = covered_before.sum(dim=-1).to(dtype=torch.long)
    covered_after_count = covered_after.sum(dim=-1).to(dtype=torch.long)
    newly_covered = covered_after & (~covered_before)
    available_viewpoint_count = reporting_step["available_viewpoint_count"].to(dtype=torch.long)
    noop_when_available = reporting_step["noop_when_available"].to(dtype=torch.bool)
    is_repeated_assignment = reporting_step["is_repeated_assignment"].to(dtype=torch.bool)
    selected_path_cost = reporting_step["selected_path_cost"].to(dtype=torch.float32)
    duplicate_selected_target_count = reporting_step["duplicate_selected_target_count"].to(dtype=torch.long)

    for env_id in range(num_envs):
        newly_ids = _covered_ids_from_mask(newly_covered[env_id], viewpoint_ids)
        newly_ids_text = json.dumps(newly_ids)
        coverage_count = int(covered_after_count[env_id].item())
        coverage_ratio = coverage_count / float(num_viewpoints)
        for agent_id in range(num_agents):
            assigned_index = int(assignment[env_id, agent_id].item())
            is_noop = assigned_index < 0
            assigned_viewpoint_id = -1 if is_noop else int(viewpoint_ids[assigned_index])
            was_covered_before = False
            covered_after_step = False
            if not is_noop:
                was_covered_before = bool(covered_before[env_id, assigned_index].item())
                covered_after_step = bool(covered_after[env_id, assigned_index].item())
            row = {
                "method": method,
                "episode": -1,
                "step": int(step[env_id].item()),
                "env_id": env_id,
                "agent_id": agent_id,
                "assigned_viewpoint_id": assigned_viewpoint_id,
                "is_noop": bool(is_noop),
                "selected_available": bool(valid_decisions[env_id, agent_id].item()),
                "available_viewpoint_count": int(available_viewpoint_count[env_id, agent_id].item()),
                "noop_when_available": bool(noop_when_available[env_id, agent_id].item()),
                "is_repeated_assignment": bool(is_repeated_assignment[env_id, agent_id].item()),
                "selected_path_cost": (
                    float(selected_path_cost[env_id, agent_id].item())
                    if math.isfinite(float(selected_path_cost[env_id, agent_id].item()))
                    else ""
                ),
                "duplicate_selected_target_count_step": int(duplicate_selected_target_count[env_id].item()),
                "covered_before_count": int(covered_before_count[env_id].item()),
                "covered_after_count": coverage_count,
                "newly_covered_viewpoint_ids": newly_ids_text,
                "coverage_count": coverage_count,
                "coverage_ratio": coverage_ratio,
                "assigned_viewpoint_was_covered_before": was_covered_before,
                "assigned_viewpoint_covered_after": covered_after_step,
                "actual_base_motion_intersects_component": False,
                "actual_base_motion_distance": "",
            }
            if actual_base_motion is not None:
                intersection_by_robot = actual_base_motion.get("_actual_base_motion_intersection_by_robot")
                distance_by_robot = actual_base_motion.get("_actual_base_motion_distance_by_robot")
                if isinstance(intersection_by_robot, torch.Tensor) and intersection_by_robot.ndim == 2:
                    row["actual_base_motion_intersects_component"] = bool(
                        intersection_by_robot[env_id, agent_id].item()
                    )
                if isinstance(distance_by_robot, torch.Tensor) and distance_by_robot.ndim == 2:
                    distance = float(distance_by_robot[env_id, agent_id].item())
                    row["actual_base_motion_distance"] = distance if math.isfinite(distance) else ""
            row.update(_retry_fallback_default_history_fields())
            if retry_fallback_info is not None:
                row.update(retry_fallback_info.get((env_id, agent_id), {}))
            pending_history_by_env.setdefault(env_id, []).append(row)


def _finalize_assignment_history(
    assignment_history: list[dict],
    pending_history_by_env: dict[int, list[dict]],
    *,
    episode_start: int,
    env_ids: torch.Tensor,
) -> None:
    for offset, env_id_tensor in enumerate(env_ids):
        env_id = int(env_id_tensor.item())
        rows = pending_history_by_env.pop(env_id, [])
        episode_id = episode_start + offset
        for row in rows:
            row["episode"] = episode_id
        assignment_history.extend(rows)


def _check_record_consistency(record: dict[str, float | int | str], num_viewpoints: int) -> None:
    final_covered_count = int(record["final_covered_count"])
    final_coverage = float(record["final_coverage"])
    expected_coverage = final_covered_count / float(num_viewpoints)
    if abs(final_coverage - expected_coverage) > 1.0e-6:
        raise RuntimeError(
            f"metric consistency failure for {record['method']} episode {record['episode']}: "
            f"final_coverage={final_coverage} but final_covered_count={final_covered_count}/{num_viewpoints}"
        )
    if int(record["success"]) == 1 and final_covered_count != num_viewpoints:
        raise RuntimeError(
            f"metric consistency failure for {record['method']} episode {record['episode']}: "
            f"success=1 but final_covered_count={final_covered_count}/{num_viewpoints}"
        )
    if abs(final_coverage - 1.0) <= 1.0e-6 and final_covered_count != num_viewpoints:
        raise RuntimeError(
            f"metric consistency failure for {record['method']} episode {record['episode']}: "
            f"final_coverage=1.0 but final_covered_count={final_covered_count}/{num_viewpoints}"
        )


def _buffer_mean_or_nan(buffers: dict[str, torch.Tensor], env_id: int, *, sum_key: str, count_key: str) -> float:
    count = float(buffers[count_key][env_id].item())
    if count <= 0.0:
        return float("nan")
    return float((buffers[sum_key][env_id] / buffers[count_key][env_id]).item())


def _buffer_min_or_nan(buffers: dict[str, torch.Tensor], env_id: int, *, min_key: str, count_key: str) -> float:
    count = float(buffers[count_key][env_id].item())
    if count <= 0.0:
        return float("nan")
    return float(buffers[min_key][env_id].item())


def _tensor_row_json(tensor: torch.Tensor, env_id: int, *, digits: int | None = None) -> str:
    row = tensor[env_id].detach().cpu().flatten().tolist()
    if digits is None:
        values = [int(value) for value in row]
    else:
        values = [round(float(value), digits) for value in row]
    return json.dumps(values)


def _population_std(tensor: torch.Tensor) -> float:
    values = tensor.detach().to(dtype=torch.float32).flatten()
    if values.numel() <= 1:
        return 0.0
    return float(torch.std(values, unbiased=False).item())


def _selected_path_cost_max_or_nan(buffers: dict[str, torch.Tensor], env_id: int) -> float:
    if float(buffers["selected_path_cost_count"][env_id].item()) <= 0.0:
        return float("nan")
    value = float(buffers["selected_path_cost_max"][env_id].item())
    return value if math.isfinite(value) else float("nan")


def _late_repeated_assignment_pattern_json(
    buffers: dict[str, torch.Tensor],
    env_id: int,
    viewpoint_ids: list[int],
    *,
    limit: int = 10,
) -> str:
    pair_counts = buffers.get("post_gain_repeated_pair_count")
    if not isinstance(pair_counts, torch.Tensor) or pair_counts.numel() == 0:
        return "[]"
    rows = []
    for agent_id, viewpoint_index in torch.nonzero(pair_counts[env_id] > 0, as_tuple=False).detach().cpu().tolist():
        viewpoint_id = viewpoint_ids[viewpoint_index] if viewpoint_index < len(viewpoint_ids) else viewpoint_index
        rows.append(
            {
                "agent_id": int(agent_id),
                "viewpoint_id": int(viewpoint_id),
                "count": int(pair_counts[env_id, agent_id, viewpoint_index].item()),
            }
        )
    rows.sort(key=lambda item: (-int(item["count"]), int(item["agent_id"]), int(item["viewpoint_id"])))
    return json.dumps(rows[:limit])


def _make_records(
    method: str,
    episode_start: int,
    env_ids: torch.Tensor,
    buffers: dict[str, torch.Tensor],
    viewpoint_ids: list[int],
) -> list[dict[str, float | int | str]]:
    records = []
    num_viewpoints = len(viewpoint_ids)
    for offset, env_id_tensor in enumerate(env_ids):
        env_id = int(env_id_tensor.item())
        length = max(1, int(buffers["length"][env_id].item()))
        final_covered_count = int(buffers["final_covered_count"][env_id].item())
        final_coverage = final_covered_count / float(num_viewpoints)
        steps_to_full = int(buffers["steps_to_full"][env_id].item())
        covered_ids, uncovered_ids = _covered_id_lists(buffers["covered_mask"][env_id], viewpoint_ids)
        per_robot_selected = buffers["per_robot_selected_count"][env_id]
        per_robot_completed = buffers["per_robot_completed_count"][env_id]
        selected_count_total = float(per_robot_selected.sum().item())
        noop_count = float(buffers["noop_count"][env_id].item())
        selected_path_cost_count = float(buffers["selected_path_cost_count"][env_id].item())
        selected_path_cost_mean = (
            float((buffers["selected_path_cost_sum"][env_id] / buffers["selected_path_cost_count"][env_id]).item())
            if selected_path_cost_count > 0.0
            else float("nan")
        )
        last_gain_step = int(buffers["last_global_coverage_gain_step"][env_id].item())
        steps_since_last_gain = int(buffers["steps_since_last_global_coverage_gain"][env_id].item())
        record = {
            "method": method,
            "episode": episode_start + offset,
            "episode_return": float(buffers["return"][env_id].item()),
            "final_coverage": final_coverage,
            "final_covered_count": final_covered_count,
            "final_covered_viewpoint_ids": json.dumps(covered_ids),
            "final_uncovered_viewpoint_ids": json.dumps(uncovered_ids),
            "success": int(final_covered_count == num_viewpoints),
            "steps_to_full_coverage": steps_to_full,
            "first_full_coverage_step": steps_to_full,
            "coverage_auc": float((buffers["coverage_auc"][env_id] / length).item()),
            "duplicate_count_mean": float((buffers["duplicate_sum"][env_id] / length).item()),
            "noop_rate": float((buffers["noop_count"][env_id] / buffers["decision_count"][env_id].clamp(min=1.0)).item()),
            "valid_action_rate": float((buffers["valid_count"][env_id] / buffers["decision_count"][env_id].clamp(min=1.0)).item()),
            "new_viewpoints_total": float(buffers["new_viewpoints_total"][env_id].item()),
            "episode_length": length,
            "per_robot_selected_count": _tensor_row_json(buffers["per_robot_selected_count"], env_id),
            "per_robot_completed_count": _tensor_row_json(buffers["per_robot_completed_count"], env_id, digits=6),
            "per_robot_repeated_assignment_count": _tensor_row_json(
                buffers["per_robot_repeated_assignment_count"], env_id
            ),
            "per_viewpoint_attempted_count": _tensor_row_json(buffers["per_viewpoint_attempted_count"], env_id),
            "last_global_coverage_gain_step": last_gain_step,
            "steps_since_last_global_coverage_gain": steps_since_last_gain,
            "no_progress_steps_after_last_gain": steps_since_last_gain,
            "duplicate_selected_target_count": int(buffers["duplicate_selected_target_count"][env_id].item()),
            "duplicate_selected_target_rate": float(
                buffers["duplicate_selected_target_count"][env_id].item()
            )
            / max(1.0, selected_count_total),
            "noop_when_available_count": int(buffers["noop_when_available_count"][env_id].item()),
            "noop_when_available_rate": float(buffers["noop_when_available_count"][env_id].item())
            / max(1.0, noop_count),
            "selected_path_cost_mean": selected_path_cost_mean,
            "selected_path_cost_max": _selected_path_cost_max_or_nan(buffers, env_id),
            "selected_path_cost_sum": float(buffers["selected_path_cost_sum"][env_id].item()),
            "load_balance_selected_std": _population_std(per_robot_selected),
            "load_balance_completed_std": _population_std(per_robot_completed),
            "late_repeated_assignment_pattern": _late_repeated_assignment_pattern_json(
                buffers,
                env_id,
                viewpoint_ids,
            ),
            "inter_robot_overlap_step_count": int(buffers["inter_robot_overlap_step_count"][env_id].item()),
            "inter_robot_overlap_rate": float(buffers["inter_robot_overlap_step_count"][env_id].item()) / float(length),
            "inter_robot_overlap_pair_count_total": int(
                buffers["inter_robot_overlap_pair_count_total"][env_id].item()
            ),
            "inter_robot_min_distance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="inter_robot_min_distance_min",
                count_key="inter_robot_min_distance_count",
            ),
            "inter_robot_min_distance_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="inter_robot_min_distance_sum",
                count_key="inter_robot_min_distance_count",
            ),
            "inter_robot_min_clearance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="inter_robot_min_clearance_min",
                count_key="inter_robot_min_clearance_count",
            ),
            "inter_robot_min_clearance_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="inter_robot_min_clearance_sum",
                count_key="inter_robot_min_clearance_count",
            ),
            "selected_target_conflict_step_count": int(
                buffers["selected_target_conflict_step_count"][env_id].item()
            ),
            "selected_target_conflict_rate": float(
                buffers["selected_target_conflict_step_count"][env_id].item()
            )
            / float(length),
            "selected_target_conflict_pair_count_total": int(
                buffers["selected_target_conflict_pair_count_total"][env_id].item()
            ),
            "selected_target_min_distance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="selected_target_min_distance_min",
                count_key="selected_target_min_distance_count",
            ),
            "selected_target_min_distance_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="selected_target_min_distance_sum",
                count_key="selected_target_min_distance_count",
            ),
            "selected_target_min_clearance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="selected_target_min_clearance_min",
                count_key="selected_target_min_clearance_count",
            ),
            "selected_target_min_clearance_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="selected_target_min_clearance_sum",
                count_key="selected_target_min_clearance_count",
            ),
            "selected_target_skipped_robot_count_total": int(
                buffers["selected_target_skipped_robot_count_total"][env_id].item()
            ),
            "selected_target_valid_robot_count_mean": float(
                (buffers["selected_target_valid_robot_count_sum"][env_id] / float(length)).item()
            ),
            "actual_base_motion_intersection_step_count": int(
                buffers["actual_base_motion_intersection_step_count"][env_id].item()
            ),
            "actual_base_motion_intersection_rate": float(
                buffers["actual_base_motion_intersection_step_count"][env_id].item()
            )
            / float(length),
            "actual_base_motion_intersection_pair_count_total": int(
                buffers["actual_base_motion_intersection_pair_count_total"][env_id].item()
            ),
            "actual_base_motion_intersection_pair_count_mean": float(
                (buffers["actual_base_motion_intersection_pair_count_sum"][env_id] / float(length)).item()
            ),
            "actual_base_motion_min_distance_to_footprint_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="actual_base_motion_min_distance_to_footprint_min",
                count_key="actual_base_motion_min_distance_to_footprint_count",
            ),
            "actual_base_motion_min_distance_to_footprint_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="actual_base_motion_min_distance_to_footprint_sum",
                count_key="actual_base_motion_min_distance_to_footprint_count",
            ),
            "actual_base_motion_valid_robot_count_mean": float(
                (buffers["actual_base_motion_valid_robot_count_sum"][env_id] / float(length)).item()
            ),
            "actual_base_motion_skipped_robot_count_total": int(
                buffers["actual_base_motion_skipped_robot_count_total"][env_id].item()
            ),
            "baseline_selected_target_conflict_step_count": int(
                buffers["baseline_selected_target_conflict_step_count"][env_id].item()
            ),
            "baseline_selected_target_conflict_rate_mean": float(
                (buffers["baseline_selected_target_conflict_rate_sum"][env_id] / float(length)).item()
            ),
            "baseline_selected_target_conflict_pair_count_total": int(
                buffers["baseline_selected_target_conflict_pair_count_total"][env_id].item()
            ),
            "baseline_selected_target_min_distance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="baseline_selected_target_min_distance_min",
                count_key="baseline_selected_target_min_distance_count",
            ),
            "baseline_selected_target_min_clearance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="baseline_selected_target_min_clearance_min",
                count_key="baseline_selected_target_min_clearance_count",
            ),
            "baseline_selected_target_conflict_penalty_sum_total": float(
                buffers["baseline_selected_target_conflict_penalty_sum_total"][env_id].item()
            ),
            "candidate_selected_target_conflict_step_count": int(
                buffers["candidate_selected_target_conflict_step_count"][env_id].item()
            ),
            "candidate_selected_target_conflict_rate_mean": float(
                (buffers["candidate_selected_target_conflict_rate_sum"][env_id] / float(length)).item()
            ),
            "candidate_selected_target_conflict_pair_count_total": int(
                buffers["candidate_selected_target_conflict_pair_count_total"][env_id].item()
            ),
            "candidate_selected_target_min_distance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="candidate_selected_target_min_distance_min",
                count_key="candidate_selected_target_min_distance_count",
            ),
            "candidate_selected_target_min_clearance_min": _buffer_min_or_nan(
                buffers,
                env_id,
                min_key="candidate_selected_target_min_clearance_min",
                count_key="candidate_selected_target_min_clearance_count",
            ),
            "candidate_selected_target_conflict_penalty_sum_total": float(
                buffers["candidate_selected_target_conflict_penalty_sum_total"][env_id].item()
            ),
            "candidate_changed_assignment_rate_mean": float(
                (buffers["candidate_changed_assignment_rate_sum"][env_id] / float(length)).item()
            ),
            "candidate_changed_assignment_count_total": int(
                buffers["candidate_changed_assignment_count_total"][env_id].item()
            ),
            "conflict_aware_solver_enabled": int(
                buffers["conflict_aware_solver_enabled_count"][env_id].item() > 0
            ),
            "conflict_aware_fallback_step_count": int(
                buffers["conflict_aware_fallback_step_count"][env_id].item()
            ),
            "conflict_aware_fallback_rate": float(
                buffers["conflict_aware_fallback_step_count"][env_id].item()
            )
            / float(length),
            "conflict_aware_candidate_combination_count_mean": float(
                (
                    buffers["conflict_aware_candidate_combination_count_sum"][env_id]
                    / buffers["conflict_aware_solver_step_count"][env_id].clamp(min=1).to(dtype=torch.float32)
                ).item()
            ),
            "conflict_aware_selected_score_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="conflict_aware_selected_score_sum",
                count_key="conflict_aware_selected_score_count",
            ),
            "conflict_aware_selected_unary_cost_sum_mean": _buffer_mean_or_nan(
                buffers,
                env_id,
                sum_key="conflict_aware_selected_unary_cost_sum_sum",
                count_key="conflict_aware_selected_unary_cost_sum_count",
            ),
            "conflict_aware_selected_target_conflict_pair_count_total": int(
                buffers["conflict_aware_selected_target_conflict_pair_count_total"][env_id].item()
            ),
            "conflict_aware_selected_target_conflict_penalty_sum_total": float(
                buffers["conflict_aware_selected_target_conflict_penalty_sum_total"][env_id].item()
            ),
            "conflict_aware_selected_duplicate_pair_count_total": int(
                buffers["conflict_aware_selected_duplicate_pair_count_total"][env_id].item()
            ),
            "conflict_aware_changed_vs_base_count_total": int(
                buffers["conflict_aware_changed_vs_base_count_total"][env_id].item()
            ),
            "conflict_aware_changed_vs_base_rate_mean": float(
                (buffers["conflict_aware_changed_vs_base_rate_sum"][env_id] / float(length)).item()
            ),
        }
        _check_record_consistency(record, num_viewpoints)
        records.append(record)
    return records


def _reset_buffers(buffers: dict[str, torch.Tensor], env_ids: torch.Tensor) -> None:
    for value in buffers.values():
        value[env_ids] = 0
    buffers["steps_to_full"][env_ids] = -1
    if "previous_assignment" in buffers:
        buffers["previous_assignment"][env_ids] = -2
    if "last_global_coverage_gain_step" in buffers:
        buffers["last_global_coverage_gain_step"][env_ids] = -1
    if "selected_path_cost_max" in buffers:
        buffers["selected_path_cost_max"][env_ids] = -float("inf")
    for key in (
        "inter_robot_min_distance_min",
        "inter_robot_min_clearance_min",
        "selected_target_min_distance_min",
        "selected_target_min_clearance_min",
        "actual_base_motion_min_distance_to_footprint_min",
        "baseline_selected_target_min_distance_min",
        "baseline_selected_target_min_clearance_min",
        "candidate_selected_target_min_distance_min",
        "candidate_selected_target_min_clearance_min",
    ):
        buffers[key][env_ids] = float("inf")


def _env_id_tensor(unwrapped, env_ids: Any) -> torch.Tensor:
    if env_ids is None:
        return torch.arange(unwrapped.num_envs, dtype=torch.long, device=unwrapped.device)
    if isinstance(env_ids, torch.Tensor):
        return env_ids.to(device=unwrapped.device, dtype=torch.long).flatten()
    return torch.as_tensor(list(env_ids), dtype=torch.long, device=unwrapped.device).flatten()


def _install_prereset_coverage_capture(unwrapped) -> tuple[dict[int, torch.Tensor], Any]:
    snapshots: dict[int, torch.Tensor] = {}
    original_reset_idx = unwrapped._reset_idx

    def capture_reset_idx(env_ids=None):
        if hasattr(unwrapped, "viewpoints_covered"):
            ids = _env_id_tensor(unwrapped, env_ids)
            covered = unwrapped.viewpoints_covered.detach().clone()
            for env_id_tensor in ids:
                env_id = int(env_id_tensor.item())
                snapshots[env_id] = covered[env_id].clone()
        return original_reset_idx(env_ids)

    unwrapped._reset_idx = capture_reset_idx
    return snapshots, original_reset_idx


def _coverage_from_env(
    unwrapped,
    env_done: torch.Tensor,
    prereset_coverage_snapshots: dict[int, torch.Tensor] | None = None,
) -> torch.Tensor:
    covered = unwrapped.viewpoints_covered.to(dtype=torch.bool).clone()
    if prereset_coverage_snapshots:
        for env_id_tensor in torch.nonzero(env_done, as_tuple=False).flatten():
            env_id = int(env_id_tensor.item())
            snapshot = prereset_coverage_snapshots.get(env_id)
            if snapshot is not None:
                covered[env_id] = snapshot.to(device=covered.device, dtype=torch.bool)
    return covered


def _new_viewpoints_from_env(unwrapped) -> torch.Tensor:
    if hasattr(unwrapped, "last_global_coverage_gain"):
        return unwrapped.last_global_coverage_gain.reshape(unwrapped.num_envs)
    return torch.zeros(unwrapped.num_envs, dtype=torch.float32, device=unwrapped.device)


def _actor_checkpoint_path(model_dir: Path, agent_name: str, agent_id: int) -> Path:
    candidates = (
        model_dir / f"actor_agent_{agent_name}.pt",
        model_dir / f"actor_agent_{agent_id}.pt",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find actor checkpoint for {agent_name}; checked {candidates}")


def _load_assignment_actors(wrapper, algo_args: dict, model_dir: Path, device: torch.device):
    actor_args = {**algo_args["model"], **algo_args["algo"]}
    actors = []
    for agent_id, agent_name in enumerate(wrapper.agents):
        actor = ALGO_REGISTRY[algorithm](
            actor_args,
            wrapper.observation_space[agent_id],
            wrapper.action_space[agent_id],
            device=device,
        )
        checkpoint_path = _actor_checkpoint_path(model_dir, agent_name, agent_id)
        state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        try:
            actor.actor.load_state_dict(state_dict)
        except RuntimeError as exc:
            raise RuntimeError(
                f"Failed to load {checkpoint_path}. Use an assignment-mode Discrete/Categorical checkpoint, "
                "not an old 9D continuous checkpoint or a checkpoint trained with a different fixed-N viewpoint count."
            ) from exc
        actor.prep_rollout()

        act_layer = getattr(actor.actor, "act", None)
        action_type = getattr(act_layer, "action_type", None)
        action_head = getattr(act_layer, "action_out", None)
        action_head_name = action_head.__class__.__name__ if action_head is not None else None
        print(
            f"[INFO]: restored {agent_name} from {checkpoint_path} "
            f"action_type={action_type} distribution_head={action_head_name}"
        )
        if action_type != "Discrete" or action_head_name != "Categorical":
            raise RuntimeError(
                "assignment_rl expected HARL Categorical actor for Discrete action space, "
                f"got action_type={action_type}, distribution_head={action_head_name}"
            )
        actors.append(actor)
    return actors


def _assert_available_actions(wrapper, available_actions: torch.Tensor | None) -> None:
    if available_actions is None:
        raise RuntimeError("assignment_rl requires available_actions, got None")
    expected_shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1)
    if tuple(available_actions.shape) != expected_shape:
        raise RuntimeError(f"available_actions shape mismatch: expected {expected_shape}, got {tuple(available_actions.shape)}")


def _refresh_assignment_obs(wrapper):
    obs = wrapper.unwrapped._get_observations()
    wrapper._sync_agents(obs)
    return obs, wrapper._build_shared_obs(obs), wrapper.make_available_actions()


def _should_print_assignment_diag(step_id: int) -> bool:
    if step_id <= args_cli.print_diagnostics_steps:
        return True
    return args_cli.diagnostic_interval > 0 and step_id % args_cli.diagnostic_interval == 0


def _evaluate_baseline(method: str, env_cfg) -> tuple[list[dict], dict]:
    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    prereset_coverage_snapshots, original_reset_idx = _install_prereset_coverage_capture(unwrapped)
    solver = make_solver(method)
    env.reset(seed=args_cli.seed)

    device = torch.device(unwrapped.device)
    agents = list(unwrapped.possible_agents)
    num_envs = int(unwrapped.num_envs)
    viewpoint_ids = [int(value) for value in unwrapped.viewpoint_ids]
    records: list[dict] = []
    problem = unwrapped.get_assignment_problem()
    buffers = _init_buffers(
        num_envs,
        device,
        num_agents=int(problem["num_agents"]),
        num_viewpoints=int(problem["num_viewpoints"]),
    )
    _validate_evaluation_scenario(unwrapped, problem, method)
    diagnostics = _collect_evaluation_diagnostics(unwrapped, problem, [method])

    print(f"[INFO]: evaluating method={method} num_envs={num_envs} episodes={args_cli.num_episodes} max_steps={args_cli.max_steps}")
    try:
        with torch.no_grad():
            while simulation_app.is_running() and len(records) < args_cli.num_episodes:
                problem = _prepare_baseline_assignment_problem(unwrapped.get_assignment_problem(), method=method)
                assignment = solver.solve(problem)
                solver_diagnostics = getattr(solver, "latest_diagnostics", None)
                _validate_assignment(problem, assignment)
                valid_decisions = _valid_assignment_decisions(problem, assignment)
                step_before = buffers["length"].clone()
                _update_conflict_aware_solver_buffers(
                    buffers,
                    solver_diagnostics=solver_diagnostics,
                    num_envs=num_envs,
                    device=device,
                )
                selected_target_conflict = _selected_target_conflict_diagnostics(problem, assignment, viewpoint_ids)
                _set_selected_assignment_debug_visualization(unwrapped, assignment, problem)
                _update_selected_assignment_debug_runtime_diagnostics(
                    diagnostics,
                    unwrapped,
                    method=method,
                    step=step_before,
                )
                covered_before = unwrapped.viewpoints_covered.to(dtype=torch.bool).clone()
                reporting_step = _assignment_reporting_step_diagnostics(buffers, problem, assignment)

                actions = viewpoint_assignment_to_actions(unwrapped, assignment)
                _, rewards, terminated, truncated, _ = env.step(actions)

                terminated_tensor = _aggregate_done(terminated, agents, num_envs, device)
                truncated_tensor = _aggregate_done(truncated, agents, num_envs, device)
                env_done = terminated_tensor | truncated_tensor
                covered_mask = _coverage_from_env(unwrapped, env_done, prereset_coverage_snapshots)
                new_viewpoints = _new_viewpoints_from_env(unwrapped)
                reward_sum = _sum_reward_dict(rewards, agents, num_envs, device)
                current_overlap = unwrapped.get_inter_robot_conflict_diagnostics()
                _update_inter_robot_runtime_diagnostics(
                    diagnostics,
                    method=method,
                    step=step_before,
                    current_overlap=current_overlap,
                    selected_target=selected_target_conflict,
                )
                _update_inter_robot_conflict_buffers(
                    buffers,
                    current_overlap=current_overlap,
                    selected_target=selected_target_conflict,
                    num_envs=num_envs,
                    device=device,
                )

                _update_buffers(
                    buffers,
                    reward_sum=reward_sum,
                    assignment=assignment,
                    valid_decisions=valid_decisions,
                    covered_before=covered_before,
                    covered_mask=covered_mask,
                    new_viewpoints=new_viewpoints,
                    reporting_step=reporting_step,
                )

                script_done = buffers["length"] >= args_cli.max_steps
                done = env_done | script_done
                done_ids = torch.nonzero(done, as_tuple=False).flatten()
                if done_ids.numel() == 0:
                    continue

                remaining = args_cli.num_episodes - len(records)
                record_ids = done_ids[:remaining]
                records.extend(_make_records(method, len(records), record_ids, buffers, viewpoint_ids))

                manual_reset = script_done & (~env_done)
                manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
                if manual_reset_ids.numel() > 0:
                    unwrapped._reset_idx(manual_reset_ids)

                _reset_buffers(buffers, done_ids)
                solver.reset()
    finally:
        unwrapped._reset_idx = original_reset_idx
        env.close()
    return records, diagnostics


def _evaluate_baseline_methods(methods: list[str], env_cfg) -> tuple[list[dict], dict, list[dict], list[dict], list[dict]]:
    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    prereset_coverage_snapshots, original_reset_idx = _install_prereset_coverage_capture(unwrapped)
    device = torch.device(unwrapped.device)
    agents = list(unwrapped.possible_agents)
    num_envs = int(unwrapped.num_envs)
    viewpoint_ids = [int(value) for value in unwrapped.viewpoint_ids]
    all_records: list[dict] = []
    assignment_history: list[dict] = []
    retry_fallback_events: list[dict] = []
    controller_state_trace: list[dict] = []
    obstacle_candidate_comparison_rows: list[dict] = []
    target_conflict_candidate_comparison_rows: list[dict] = []
    conflict_aware_solver_rows: list[dict] = []
    actual_base_motion_rows: list[dict] = []
    retry_fallback_stats = _init_retry_fallback_stats()
    diagnostics: dict | None = None
    agent_names = _agent_names_from_unwrapped(unwrapped)
    controller_trace_pairs = _controller_trace_pairs(agent_names, viewpoint_ids)

    try:
        for method in methods:
            solver = make_solver(method)
            env.reset(seed=args_cli.seed)
            pending_history_by_env: dict[int, list[dict]] = {}
            pending_retry_events_by_env: dict[int, list[dict]] = {}
            pending_controller_trace_by_env: dict[int, list[dict]] = {}
            records: list[dict] = []
            episode_index_by_env = torch.zeros(num_envs, dtype=torch.long, device=device)
            problem = unwrapped.get_assignment_problem()
            buffers = _init_buffers(
                num_envs,
                device,
                num_agents=int(problem["num_agents"]),
                num_viewpoints=int(problem["num_viewpoints"]),
            )
            _validate_evaluation_scenario(unwrapped, problem, method)
            if diagnostics is None:
                diagnostics = _collect_evaluation_diagnostics(unwrapped, problem, methods)
                diagnostics["controller_state_trace"] = {
                    "enabled": bool(args_cli.write_controller_state_trace),
                    "requested_pairs": [
                        {
                            "agent_id": int(agent_id),
                            "agent_name": agent_names[agent_id],
                            "viewpoint_id": int(viewpoint_id),
                        }
                        for agent_id, viewpoint_id in controller_trace_pairs
                    ],
                    "fields": CONTROLLER_STATE_TRACE_FIELDS if args_cli.write_controller_state_trace else [],
                    "summary_fields": (
                        CONTROLLER_STATE_TRACE_SUMMARY_FIELDS if args_cli.write_controller_state_trace else []
                    ),
                }
            retry_state = _make_retry_fallback_state(
                method=method,
                num_envs=num_envs,
                num_agents=int(problem["num_agents"]),
                num_viewpoints=int(problem["num_viewpoints"]),
                viewpoint_ids=viewpoint_ids,
                device=device,
                stats=retry_fallback_stats,
            )
            trace_state = _init_controller_trace_state(
                num_envs=num_envs,
                num_agents=int(problem["num_agents"]),
                device=device,
                pairs=controller_trace_pairs,
                agent_names=agent_names,
            )

            pair_filter = _load_level2_pair_filter()
            print(
                f"[INFO]: evaluating method={method} num_envs={num_envs} "
                f"episodes={args_cli.num_episodes} max_steps={args_cli.max_steps} "
                f"candidate_mode={_candidate_mode()} top_k={int(args_cli.viewpoint_candidate_top_k)} "
                f"level2_pair_filter_enabled={bool(pair_filter['enabled'])} "
                f"level2_denied={int(pair_filter['num_denied'])} "
                f"level2_allowed={int(pair_filter['num_allowed'])} "
                f"assignment_retry_fallback_enabled={bool(args_cli.assignment_retry_fallback)}"
            )
            with torch.no_grad():
                while simulation_app.is_running() and len(records) < args_cli.num_episodes:
                    problem = _prepare_baseline_assignment_problem(unwrapped.get_assignment_problem(), retry_state, method=method)
                    assignment = solver.solve(problem)
                    solver_diagnostics = getattr(solver, "latest_diagnostics", None)
                    _validate_assignment(problem, assignment)
                    valid_decisions = _valid_assignment_decisions(problem, assignment)
                    step_before = buffers["length"].clone()
                    conflict_aware_solver_row = _conflict_aware_solver_step_row(
                        method=method,
                        step=step_before,
                        episode_index=episode_index_by_env.clone(),
                        solver_diagnostics=solver_diagnostics,
                        num_envs=num_envs,
                        num_agents=int(problem["num_agents"]),
                        device=device,
                    )
                    if conflict_aware_solver_row is not None:
                        conflict_aware_solver_rows.append(conflict_aware_solver_row)
                    _update_conflict_aware_solver_buffers(
                        buffers,
                        solver_diagnostics=solver_diagnostics,
                        num_envs=num_envs,
                        device=device,
                    )
                    selected_target_conflict = _selected_target_conflict_diagnostics(problem, assignment, viewpoint_ids)
                    _set_selected_assignment_debug_visualization(unwrapped, assignment, problem)
                    _update_selected_assignment_debug_runtime_diagnostics(
                        diagnostics,
                        unwrapped,
                        method=method,
                        step=step_before,
                    )
                    covered_before = unwrapped.viewpoints_covered.to(dtype=torch.bool).clone()
                    reporting_step = _assignment_reporting_step_diagnostics(buffers, problem, assignment)
                    if args_cli.compare_obstacle_aware_candidates:
                        obstacle_candidate_comparison_rows.append(
                            _compare_obstacle_aware_candidate_step(
                                method=method,
                                step=step_before,
                                episode_index=episode_index_by_env.clone(),
                                problem=problem,
                                baseline_assignment=assignment,
                                agents=agent_names,
                                viewpoint_ids=viewpoint_ids,
                            )
                        )
                    target_conflict_candidate_comparison = _compare_target_conflict_candidate_step(
                        method=method,
                        step=step_before,
                        episode_index=episode_index_by_env.clone(),
                        problem=problem,
                        baseline_assignment=assignment,
                        agents=agent_names,
                        viewpoint_ids=viewpoint_ids,
                    )
                    target_conflict_candidate_comparison_rows.append(target_conflict_candidate_comparison)
                    _update_target_conflict_candidate_buffers(
                        buffers,
                        comparison=target_conflict_candidate_comparison,
                        num_envs=num_envs,
                        device=device,
                    )
                    assignment_transition_info = _update_controller_trace_assignment_state(
                        trace_state, assignment, viewpoint_ids
                    )

                    actions = viewpoint_assignment_to_actions(unwrapped, assignment)
                    previous_base_pos = unwrapped.base_pos.detach().clone()
                    _, rewards, terminated, truncated, _ = env.step(actions)
                    current_base_pos = unwrapped.base_pos.detach().clone()

                    terminated_tensor = _aggregate_done(terminated, agents, num_envs, device)
                    truncated_tensor = _aggregate_done(truncated, agents, num_envs, device)
                    env_done = terminated_tensor | truncated_tensor
                    actual_base_motion = _actual_base_motion_step_diagnostics(
                        unwrapped=unwrapped,
                        method=method,
                        step=step_before,
                        episode_index=episode_index_by_env.clone(),
                        assignment=assignment,
                        previous_base_pos=previous_base_pos,
                        current_base_pos=current_base_pos,
                        env_done=env_done,
                        agents=agent_names,
                        viewpoint_ids=viewpoint_ids,
                    )
                    actual_base_motion_rows.append(actual_base_motion)
                    _update_actual_base_motion_buffers(
                        buffers,
                        diagnostics=actual_base_motion,
                        num_envs=num_envs,
                        device=device,
                    )
                    covered_mask = _coverage_from_env(unwrapped, env_done, prereset_coverage_snapshots)
                    new_viewpoints = _new_viewpoints_from_env(unwrapped)
                    reward_sum = _sum_reward_dict(rewards, agents, num_envs, device)
                    current_overlap = unwrapped.get_inter_robot_conflict_diagnostics()
                    _update_inter_robot_runtime_diagnostics(
                        diagnostics,
                        method=method,
                        step=step_before,
                        current_overlap=current_overlap,
                        selected_target=selected_target_conflict,
                    )
                    _update_inter_robot_conflict_buffers(
                        buffers,
                        current_overlap=current_overlap,
                        selected_target=selected_target_conflict,
                        num_envs=num_envs,
                        device=device,
                    )
                    retry_fallback_info = _update_retry_fallback_after_step(
                        retry_state,
                        method=method,
                        step=step_before,
                        assignment=assignment,
                        covered_before=covered_before,
                        covered_after=covered_mask,
                        viewpoint_ids=viewpoint_ids,
                        pending_events_by_env=pending_retry_events_by_env,
                    )
                    if args_cli.write_controller_state_trace:
                        _append_controller_state_trace_step(
                            pending_controller_trace_by_env,
                            unwrapped=unwrapped,
                            trace_state=trace_state,
                            method=method,
                            step=step_before,
                            assignment=assignment,
                            covered_before=covered_before,
                            covered_after=covered_mask,
                            viewpoint_ids=viewpoint_ids,
                            retry_state=retry_state,
                            assignment_transition_info=assignment_transition_info,
                        )
                    if args_cli.write_assignment_history:
                        _append_assignment_history_step(
                            pending_history_by_env,
                            method=method,
                            step=step_before,
                            assignment=assignment,
                            valid_decisions=valid_decisions,
                            reporting_step=reporting_step,
                            covered_before=covered_before,
                            covered_after=covered_mask,
                            viewpoint_ids=viewpoint_ids,
                            retry_fallback_info=retry_fallback_info,
                            actual_base_motion=actual_base_motion,
                        )

                    _update_buffers(
                        buffers,
                        reward_sum=reward_sum,
                        assignment=assignment,
                        valid_decisions=valid_decisions,
                        covered_before=covered_before,
                        covered_mask=covered_mask,
                        new_viewpoints=new_viewpoints,
                        reporting_step=reporting_step,
                    )

                    script_done = buffers["length"] >= args_cli.max_steps
                    done = env_done | script_done
                    done_ids = torch.nonzero(done, as_tuple=False).flatten()
                    if done_ids.numel() == 0:
                        continue

                    remaining = args_cli.num_episodes - len(records)
                    record_ids = done_ids[:remaining]
                    episode_start = len(records)
                    records.extend(_make_records(method, episode_start, record_ids, buffers, viewpoint_ids))
                    if args_cli.assignment_retry_fallback:
                        retry_fallback_stats["final_active_cooldowns"].extend(
                            _capture_retry_fallback_active_cooldowns(retry_state, record_ids)
                        )
                    if args_cli.write_assignment_history:
                        _finalize_assignment_history(
                            assignment_history,
                            pending_history_by_env,
                            episode_start=episode_start,
                            env_ids=record_ids,
                        )
                    if args_cli.assignment_retry_fallback:
                        _finalize_assignment_history(
                            retry_fallback_events,
                            pending_retry_events_by_env,
                            episode_start=episode_start,
                            env_ids=record_ids,
                        )
                    if args_cli.write_controller_state_trace:
                        _finalize_assignment_history(
                            controller_state_trace,
                            pending_controller_trace_by_env,
                            episode_start=episode_start,
                            env_ids=record_ids,
                        )

                    manual_reset = script_done & (~env_done)
                    manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
                    if manual_reset_ids.numel() > 0:
                        unwrapped._reset_idx(manual_reset_ids)

                    episode_index_by_env[done_ids] += 1
                    if args_cli.write_assignment_history:
                        for env_id_tensor in done_ids:
                            pending_history_by_env.pop(int(env_id_tensor.item()), None)
                    if args_cli.assignment_retry_fallback:
                        for env_id_tensor in done_ids:
                            pending_retry_events_by_env.pop(int(env_id_tensor.item()), None)
                        _reset_retry_fallback_state(retry_state, done_ids)
                    if args_cli.write_controller_state_trace:
                        for env_id_tensor in done_ids:
                            pending_controller_trace_by_env.pop(int(env_id_tensor.item()), None)
                        _reset_controller_trace_state(trace_state, done_ids)
                    _reset_buffers(buffers, done_ids)
                    solver.reset()
            all_records.extend(records)
            if diagnostics is not None and args_cli.write_controller_state_trace:
                unavailable = diagnostics.setdefault("controller_state_trace", {}).setdefault("unavailable_fields", [])
                unavailable.extend(str(value) for value in sorted(trace_state["unavailable_fields"]) if str(value) not in unavailable)
    finally:
        unwrapped._reset_idx = original_reset_idx
        env.close()
    if diagnostics is None:
        diagnostics = {}
    diagnostics.update(_retry_fallback_runtime_diagnostics(retry_fallback_stats))
    if args_cli.compare_obstacle_aware_candidates:
        diagnostics["obstacle_aware_candidate_comparison"] = _finalize_obstacle_aware_candidate_comparison(
            obstacle_candidate_comparison_rows,
            methods,
        )
    if bool(_target_conflict_candidate_config()["enabled"]) or target_conflict_candidate_comparison_rows:
        diagnostics["selected_target_conflict_candidate_comparison"] = _finalize_target_conflict_candidate_comparison(
            target_conflict_candidate_comparison_rows,
            methods,
        )
    if bool(_conflict_aware_baseline_config()["enabled"]) or conflict_aware_solver_rows:
        diagnostics["conflict_aware_baseline"] = _finalize_conflict_aware_solver_diagnostics(
            conflict_aware_solver_rows,
            methods,
        )
    if bool(_actual_base_motion_config()["enabled"]) or actual_base_motion_rows:
        diagnostics["actual_base_motion_obstacle_diagnostics"] = _finalize_actual_base_motion_diagnostics(
            actual_base_motion_rows,
            methods,
            agent_names,
        )
    return all_records, diagnostics, assignment_history, retry_fallback_events, controller_state_trace


def _evaluate_assignment_rl(env_cfg, agent_cfg: dict) -> list[dict]:
    if args_cli.assignment_checkpoint_dir is None:
        raise ValueError("--assignment_checkpoint_dir is required when methods include assignment_rl")
    model_dir = Path(args_cli.assignment_checkpoint_dir).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Assignment checkpoint directory does not exist: {model_dir}")

    wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
    prereset_coverage_snapshots, original_reset_idx = _install_prereset_coverage_capture(wrapper.unwrapped)
    device = init_device(agent_cfg["device"])
    actors = _load_assignment_actors(wrapper, agent_cfg, model_dir, device)
    reset_kwargs = {"seed": args_cli.seed} if args_cli.seed is not None else {}
    obs, _, available_actions = wrapper.reset(**reset_kwargs)
    _assert_available_actions(wrapper, available_actions)
    _validate_fixed12_scenario(wrapper.unwrapped.get_assignment_problem(), "assignment_rl")

    num_envs = int(wrapper.num_envs)
    num_agents = int(wrapper.num_agents)
    viewpoint_ids = [int(value) for value in wrapper.unwrapped.viewpoint_ids]
    buffers = _init_buffers(
        num_envs,
        wrapper.device,
        num_agents=num_agents,
        num_viewpoints=int(wrapper.num_viewpoints),
    )
    actions = make_harl_action_tensor(num_envs, wrapper.action_space, device=wrapper.device)
    rnn_hidden_size = agent_cfg["model"]["hidden_sizes"][-1]
    recurrent_n = agent_cfg["model"]["recurrent_n"]
    rnn_states = torch.zeros((num_envs, num_agents, recurrent_n, rnn_hidden_size), dtype=torch.float32, device=device)
    masks = torch.ones((num_envs, num_agents, 1), dtype=torch.float32, device=device)
    records: list[dict] = []

    print(
        f"[INFO]: evaluating method=assignment_rl num_envs={num_envs} episodes={args_cli.num_episodes} "
        f"max_steps={args_cli.max_steps} checkpoint={model_dir}"
    )
    print(f"[INFO]: assignment_rl available_actions shape={tuple(available_actions.shape)}")
    try:
        with torch.no_grad():
            while simulation_app.is_running() and len(records) < args_cli.num_episodes:
                actions.zero_()
                problem = wrapper.unwrapped.get_assignment_problem()

                for agent_id, agent_name in enumerate(wrapper.agents):
                    agent_obs = obs[agent_name].to(device=device)
                    agent_available_actions = available_actions[:, agent_id, :].to(device=device)
                    action, rnn_state = actors[agent_id].act(
                        agent_obs,
                        rnn_states[:, agent_id].clone(),
                        masks[:, agent_id],
                        agent_available_actions,
                        deterministic=True,
                    )
                    actions[:, agent_id, : action.shape[-1]] = action.to(device=wrapper.device)
                    rnn_states[:, agent_id] = rnn_state

                raw_ids = actions[..., 0].to(dtype=torch.long)
                assignment = _decode_raw_ids(raw_ids, wrapper.noop_action_id)
                valid_decisions = _valid_discrete_decisions(available_actions, raw_ids, wrapper.noop_action_id)
                covered_before = wrapper.unwrapped.viewpoints_covered.to(dtype=torch.bool).clone()
                reporting_step = _assignment_reporting_step_diagnostics(buffers, problem, assignment)

                obs, _, rewards, dones, info, available_actions = wrapper.step(actions)
                _assert_available_actions(wrapper, available_actions)

                dones_env = torch.all(dones.to(dtype=torch.bool), dim=1)
                covered_mask = _coverage_from_env(wrapper.unwrapped, dones_env, prereset_coverage_snapshots)
                coverage = covered_mask.float().mean(dim=-1)
                new_viewpoints = _new_viewpoints_from_env(wrapper.unwrapped)
                reward_sum = _sum_reward_tensor(rewards).to(device=wrapper.device)

                _update_buffers(
                    buffers,
                    reward_sum=reward_sum,
                    assignment=assignment,
                    valid_decisions=valid_decisions,
                    covered_before=covered_before,
                    covered_mask=covered_mask,
                    new_viewpoints=new_viewpoints,
                    reporting_step=reporting_step,
                )

                step_id = int(buffers["length"].max().item())
                if _should_print_assignment_diag(step_id):
                    print(
                        f"[ASSIGNMENT_RL step={step_id}] assignment={assignment.detach().cpu().tolist()} "
                        f"coverage={coverage.detach().cpu().tolist()} "
                        f"noop_count={(assignment < 0).sum(dim=1).detach().cpu().tolist()} "
                        f"duplicate_count={compute_assignment_duplicate_count(assignment).detach().cpu().tolist()} "
                        f"valid_action_rate={valid_decisions.float().mean(dim=1).detach().cpu().tolist()} "
                        f"new_viewpoints={new_viewpoints.detach().cpu().tolist()}"
                    )

                script_done = buffers["length"] >= args_cli.max_steps
                done = dones_env | script_done
                done_ids = torch.nonzero(done, as_tuple=False).flatten()
                if done_ids.numel() == 0:
                    masks = torch.ones((num_envs, num_agents, 1), dtype=torch.float32, device=device)
                    continue

                remaining = args_cli.num_episodes - len(records)
                record_ids = done_ids[:remaining]
                records.extend(_make_records("assignment_rl", len(records), record_ids, buffers, viewpoint_ids))

                manual_reset = script_done & (~dones_env)
                manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
                if manual_reset_ids.numel() > 0:
                    wrapper.unwrapped._reset_idx(manual_reset_ids)
                    obs, _, available_actions = _refresh_assignment_obs(wrapper)

                _reset_buffers(buffers, done_ids)
                masks = torch.ones((num_envs, num_agents, 1), dtype=torch.float32, device=device)
                masks[done_ids] = 0.0
                rnn_states[done_ids] = 0.0
    finally:
        wrapper.unwrapped._reset_idx = original_reset_idx
        wrapper.close()
    return records


def _record_float(record: dict, field: str, default: float = 0.0) -> float:
    value = record.get(field, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _record_int(record: dict, field: str, default: int = 0) -> int:
    value = record.get(field, default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _finite_record_values(records: list[dict], field: str) -> list[float]:
    values = []
    for record in records:
        value = _record_float(record, field, float("nan"))
        if math.isfinite(value):
            values.append(value)
    return values


def _mean_record_field(records: list[dict], field: str, default: float = 0.0) -> float:
    if not records:
        return default
    return sum(_record_float(record, field, default) for record in records) / float(len(records))


def _mean_finite_record_field(records: list[dict], field: str) -> float:
    values = _finite_record_values(records, field)
    return sum(values) / float(len(values)) if values else float("nan")


def _min_finite_record_field(records: list[dict], field: str) -> float:
    values = _finite_record_values(records, field)
    return min(values) if values else float("nan")


def _max_finite_record_field(records: list[dict], field: str) -> float:
    values = _finite_record_values(records, field)
    return max(values) if values else float("nan")


def _json_number_list(value: Any) -> list[float]:
    decoded = _decode_json_list(value)
    values = []
    for item in decoded:
        try:
            values.append(float(item))
        except (TypeError, ValueError):
            continue
    return values


def _sum_json_number_lists(records: list[dict], field: str, *, digits: int | None = None) -> str:
    totals: list[float] = []
    for record in records:
        values = _json_number_list(record.get(field))
        if not totals:
            totals = [0.0 for _ in values]
        if len(values) != len(totals):
            continue
        for index, value in enumerate(values):
            totals[index] += value
    if digits is None:
        return json.dumps([int(round(value)) for value in totals])
    return json.dumps([round(float(value), digits) for value in totals])


def _mean_json_number_lists(records: list[dict], field: str, *, digits: int = 6) -> str:
    totals: list[float] = []
    count = 0
    for record in records:
        values = _json_number_list(record.get(field))
        if not totals:
            totals = [0.0 for _ in values]
        if len(values) != len(totals):
            continue
        for index, value in enumerate(values):
            totals[index] += value
        count += 1
    if count <= 0:
        return "[]"
    return json.dumps([round(value / float(count), digits) for value in totals])


def _late_repeated_pattern_summary(records: list[dict], *, limit: int = 10) -> str:
    counts: dict[tuple[int, int], int] = {}
    for record in records:
        for item in _decode_json_list(record.get("late_repeated_assignment_pattern")):
            if not isinstance(item, dict):
                continue
            try:
                key = (int(item["agent_id"]), int(item["viewpoint_id"]))
                counts[key] = counts.get(key, 0) + int(item.get("count", 0))
            except (KeyError, TypeError, ValueError):
                continue
    rows = [
        {"agent_id": agent_id, "viewpoint_id": viewpoint_id, "count": count}
        for (agent_id, viewpoint_id), count in counts.items()
        if count > 0
    ]
    rows.sort(key=lambda item: (-int(item["count"]), int(item["agent_id"]), int(item["viewpoint_id"])))
    return json.dumps(rows[:limit])


def _summarize(records: list[dict]) -> list[dict]:
    rows = []
    for method in METHODS:
        method_records = [record for record in records if record["method"] == method]
        if not method_records:
            continue
        count = float(len(method_records))
        full_coverage_steps = [
            int(record["steps_to_full_coverage"])
            for record in method_records
            if int(record["steps_to_full_coverage"]) >= 0
        ]
        mean_steps_to_full = (
            sum(full_coverage_steps) / float(len(full_coverage_steps)) if full_coverage_steps else -1.0
        )
        rows.append(
            {
                "method": method,
                "episodes": len(method_records),
                "success_rate": sum(record["success"] for record in method_records) / count,
                "mean_return": sum(record["episode_return"] for record in method_records) / count,
                "mean_final_coverage": sum(record["final_coverage"] for record in method_records) / count,
                "mean_steps_to_full_coverage": mean_steps_to_full,
                "mean_coverage_auc": sum(record["coverage_auc"] for record in method_records) / count,
                "mean_duplicate_count": sum(record["duplicate_count_mean"] for record in method_records) / count,
                "mean_noop_rate": sum(record["noop_rate"] for record in method_records) / count,
                "mean_valid_action_rate": sum(record["valid_action_rate"] for record in method_records) / count,
                "per_robot_selected_count_mean": _mean_json_number_lists(
                    method_records,
                    "per_robot_selected_count",
                ),
                "per_robot_completed_count_mean": _mean_json_number_lists(
                    method_records,
                    "per_robot_completed_count",
                ),
                "per_robot_repeated_assignment_count_mean": _mean_json_number_lists(
                    method_records,
                    "per_robot_repeated_assignment_count",
                ),
                "per_viewpoint_attempted_count_sum": _sum_json_number_lists(
                    method_records,
                    "per_viewpoint_attempted_count",
                ),
                "mean_steps_since_last_global_coverage_gain": _mean_record_field(
                    method_records,
                    "steps_since_last_global_coverage_gain",
                ),
                "mean_no_progress_steps_after_last_gain": _mean_record_field(
                    method_records,
                    "no_progress_steps_after_last_gain",
                ),
                "duplicate_selected_target_count_total": sum(
                    _record_int(record, "duplicate_selected_target_count") for record in method_records
                ),
                "duplicate_selected_target_rate_mean": _mean_record_field(
                    method_records,
                    "duplicate_selected_target_rate",
                ),
                "noop_when_available_count_total": sum(
                    _record_int(record, "noop_when_available_count") for record in method_records
                ),
                "noop_when_available_rate_mean": _mean_record_field(
                    method_records,
                    "noop_when_available_rate",
                ),
                "selected_path_cost_mean": _mean_finite_record_field(
                    method_records,
                    "selected_path_cost_mean",
                ),
                "selected_path_cost_max": _max_finite_record_field(
                    method_records,
                    "selected_path_cost_max",
                ),
                "selected_path_cost_sum_total": sum(
                    _record_float(record, "selected_path_cost_sum") for record in method_records
                ),
                "load_balance_selected_std_mean": _mean_record_field(
                    method_records,
                    "load_balance_selected_std",
                ),
                "load_balance_completed_std_mean": _mean_record_field(
                    method_records,
                    "load_balance_completed_std",
                ),
                "late_repeated_assignment_pattern_summary": _late_repeated_pattern_summary(method_records),
                "inter_robot_overlap_step_count_total": sum(
                    _record_int(record, "inter_robot_overlap_step_count") for record in method_records
                ),
                "inter_robot_overlap_rate_mean": _mean_record_field(
                    method_records,
                    "inter_robot_overlap_rate",
                ),
                "inter_robot_overlap_pair_count_total": sum(
                    _record_int(record, "inter_robot_overlap_pair_count_total") for record in method_records
                ),
                "inter_robot_min_distance_min": _min_finite_record_field(
                    method_records,
                    "inter_robot_min_distance_min",
                ),
                "inter_robot_min_distance_mean": _mean_finite_record_field(
                    method_records,
                    "inter_robot_min_distance_mean",
                ),
                "inter_robot_min_clearance_min": _min_finite_record_field(
                    method_records,
                    "inter_robot_min_clearance_min",
                ),
                "inter_robot_min_clearance_mean": _mean_finite_record_field(
                    method_records,
                    "inter_robot_min_clearance_mean",
                ),
                "selected_target_conflict_step_count_total": sum(
                    _record_int(record, "selected_target_conflict_step_count") for record in method_records
                ),
                "selected_target_conflict_rate_mean": _mean_record_field(
                    method_records,
                    "selected_target_conflict_rate",
                ),
                "selected_target_conflict_pair_count_total": sum(
                    _record_int(record, "selected_target_conflict_pair_count_total") for record in method_records
                ),
                "selected_target_min_distance_min": _min_finite_record_field(
                    method_records,
                    "selected_target_min_distance_min",
                ),
                "selected_target_min_distance_mean": _mean_finite_record_field(
                    method_records,
                    "selected_target_min_distance_mean",
                ),
                "selected_target_min_clearance_min": _min_finite_record_field(
                    method_records,
                    "selected_target_min_clearance_min",
                ),
                "selected_target_min_clearance_mean": _mean_finite_record_field(
                    method_records,
                    "selected_target_min_clearance_mean",
                ),
                "selected_target_skipped_robot_count_total": sum(
                    _record_int(record, "selected_target_skipped_robot_count_total") for record in method_records
                ),
                "selected_target_valid_robot_count_mean": _mean_record_field(
                    method_records,
                    "selected_target_valid_robot_count_mean",
                ),
                "actual_base_motion_intersection_step_count_total": sum(
                    _record_int(record, "actual_base_motion_intersection_step_count") for record in method_records
                ),
                "actual_base_motion_intersection_rate_mean": _mean_record_field(
                    method_records,
                    "actual_base_motion_intersection_rate",
                ),
                "actual_base_motion_intersection_pair_count_total": sum(
                    _record_int(record, "actual_base_motion_intersection_pair_count_total")
                    for record in method_records
                ),
                "actual_base_motion_intersection_pair_count_mean": _mean_record_field(
                    method_records,
                    "actual_base_motion_intersection_pair_count_mean",
                ),
                "actual_base_motion_min_distance_to_footprint_min": _min_finite_record_field(
                    method_records,
                    "actual_base_motion_min_distance_to_footprint_min",
                ),
                "actual_base_motion_min_distance_to_footprint_mean": _mean_finite_record_field(
                    method_records,
                    "actual_base_motion_min_distance_to_footprint_mean",
                ),
                "actual_base_motion_valid_robot_count_mean": _mean_record_field(
                    method_records,
                    "actual_base_motion_valid_robot_count_mean",
                ),
                "actual_base_motion_skipped_robot_count_total": sum(
                    _record_int(record, "actual_base_motion_skipped_robot_count_total") for record in method_records
                ),
                "baseline_selected_target_conflict_step_count": sum(
                    _record_int(record, "baseline_selected_target_conflict_step_count") for record in method_records
                ),
                "baseline_selected_target_conflict_rate_mean": _mean_record_field(
                    method_records,
                    "baseline_selected_target_conflict_rate_mean",
                ),
                "baseline_selected_target_conflict_pair_count_total": sum(
                    _record_int(record, "baseline_selected_target_conflict_pair_count_total")
                    for record in method_records
                ),
                "baseline_selected_target_min_distance_min": _min_finite_record_field(
                    method_records,
                    "baseline_selected_target_min_distance_min",
                ),
                "baseline_selected_target_min_clearance_min": _min_finite_record_field(
                    method_records,
                    "baseline_selected_target_min_clearance_min",
                ),
                "baseline_selected_target_conflict_penalty_sum_total": sum(
                    _record_float(record, "baseline_selected_target_conflict_penalty_sum_total")
                    for record in method_records
                ),
                "candidate_selected_target_conflict_step_count": sum(
                    _record_int(record, "candidate_selected_target_conflict_step_count") for record in method_records
                ),
                "candidate_selected_target_conflict_rate_mean": _mean_record_field(
                    method_records,
                    "candidate_selected_target_conflict_rate_mean",
                ),
                "candidate_selected_target_conflict_pair_count_total": sum(
                    _record_int(record, "candidate_selected_target_conflict_pair_count_total")
                    for record in method_records
                ),
                "candidate_selected_target_min_distance_min": _min_finite_record_field(
                    method_records,
                    "candidate_selected_target_min_distance_min",
                ),
                "candidate_selected_target_min_clearance_min": _min_finite_record_field(
                    method_records,
                    "candidate_selected_target_min_clearance_min",
                ),
                "candidate_selected_target_conflict_penalty_sum_total": sum(
                    _record_float(record, "candidate_selected_target_conflict_penalty_sum_total")
                    for record in method_records
                ),
                "candidate_changed_assignment_rate_mean": _mean_record_field(
                    method_records,
                    "candidate_changed_assignment_rate_mean",
                ),
                "candidate_changed_assignment_count_total": sum(
                    _record_int(record, "candidate_changed_assignment_count_total") for record in method_records
                ),
                "conflict_aware_solver_enabled": int(
                    any(bool(_record_int(record, "conflict_aware_solver_enabled")) for record in method_records)
                ),
                "conflict_aware_fallback_step_count_total": sum(
                    _record_int(record, "conflict_aware_fallback_step_count") for record in method_records
                ),
                "conflict_aware_fallback_rate_mean": _mean_record_field(
                    method_records,
                    "conflict_aware_fallback_rate",
                ),
                "conflict_aware_candidate_combination_count_mean": _mean_record_field(
                    method_records,
                    "conflict_aware_candidate_combination_count_mean",
                ),
                "conflict_aware_selected_score_mean": _mean_finite_record_field(
                    method_records,
                    "conflict_aware_selected_score_mean",
                ),
                "conflict_aware_selected_unary_cost_sum_mean": _mean_finite_record_field(
                    method_records,
                    "conflict_aware_selected_unary_cost_sum_mean",
                ),
                "conflict_aware_selected_target_conflict_pair_count_total": sum(
                    _record_int(record, "conflict_aware_selected_target_conflict_pair_count_total")
                    for record in method_records
                ),
                "conflict_aware_selected_target_conflict_penalty_sum_total": sum(
                    _record_float(record, "conflict_aware_selected_target_conflict_penalty_sum_total")
                    for record in method_records
                ),
                "conflict_aware_selected_duplicate_pair_count_total": sum(
                    _record_int(record, "conflict_aware_selected_duplicate_pair_count_total")
                    for record in method_records
                ),
                "conflict_aware_changed_vs_base_count_total": sum(
                    _record_int(record, "conflict_aware_changed_vs_base_count_total") for record in method_records
                ),
                "conflict_aware_changed_vs_base_rate_mean": _mean_record_field(
                    method_records,
                    "conflict_aware_changed_vs_base_rate_mean",
                ),
            }
        )
    return rows


def _read_per_episode_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    int_fields = {
        "episode",
        "final_covered_count",
        "success",
        "steps_to_full_coverage",
        "first_full_coverage_step",
        "episode_length",
        "last_global_coverage_gain_step",
        "steps_since_last_global_coverage_gain",
        "no_progress_steps_after_last_gain",
        "duplicate_selected_target_count",
        "noop_when_available_count",
        "inter_robot_overlap_step_count",
        "inter_robot_overlap_pair_count_total",
        "selected_target_conflict_step_count",
        "selected_target_conflict_pair_count_total",
        "selected_target_skipped_robot_count_total",
        "actual_base_motion_intersection_step_count",
        "actual_base_motion_intersection_pair_count_total",
        "actual_base_motion_skipped_robot_count_total",
        "baseline_selected_target_conflict_step_count",
        "baseline_selected_target_conflict_pair_count_total",
        "candidate_selected_target_conflict_step_count",
        "candidate_selected_target_conflict_pair_count_total",
        "candidate_changed_assignment_count_total",
        "conflict_aware_solver_enabled",
        "conflict_aware_fallback_step_count",
        "conflict_aware_selected_target_conflict_pair_count_total",
        "conflict_aware_selected_duplicate_pair_count_total",
        "conflict_aware_changed_vs_base_count_total",
    }
    float_fields = {
        "episode_return",
        "final_coverage",
        "coverage_auc",
        "duplicate_count_mean",
        "noop_rate",
        "valid_action_rate",
        "new_viewpoints_total",
        "duplicate_selected_target_rate",
        "noop_when_available_rate",
        "selected_path_cost_mean",
        "selected_path_cost_max",
        "selected_path_cost_sum",
        "load_balance_selected_std",
        "load_balance_completed_std",
        "inter_robot_overlap_rate",
        "inter_robot_min_distance_min",
        "inter_robot_min_distance_mean",
        "inter_robot_min_clearance_min",
        "inter_robot_min_clearance_mean",
        "selected_target_conflict_rate",
        "selected_target_min_distance_min",
        "selected_target_min_distance_mean",
        "selected_target_min_clearance_min",
        "selected_target_min_clearance_mean",
        "selected_target_valid_robot_count_mean",
        "actual_base_motion_intersection_rate",
        "actual_base_motion_intersection_pair_count_mean",
        "actual_base_motion_min_distance_to_footprint_min",
        "actual_base_motion_min_distance_to_footprint_mean",
        "actual_base_motion_valid_robot_count_mean",
        "baseline_selected_target_conflict_rate_mean",
        "baseline_selected_target_min_distance_min",
        "baseline_selected_target_min_clearance_min",
        "baseline_selected_target_conflict_penalty_sum_total",
        "candidate_selected_target_conflict_rate_mean",
        "candidate_selected_target_min_distance_min",
        "candidate_selected_target_min_clearance_min",
        "candidate_selected_target_conflict_penalty_sum_total",
        "candidate_changed_assignment_rate_mean",
        "conflict_aware_fallback_rate",
        "conflict_aware_candidate_combination_count_mean",
        "conflict_aware_selected_score_mean",
        "conflict_aware_selected_unary_cost_sum_mean",
        "conflict_aware_selected_target_conflict_penalty_sum_total",
        "conflict_aware_changed_vs_base_rate_mean",
    }
    records = []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            record = dict(row)
            for field in int_fields:
                if field in record and str(record[field]).strip() != "":
                    record[field] = int(float(record[field]))
            for field in float_fields:
                if field in record and str(record[field]).strip() != "":
                    record[field] = float(record[field])
            records.append(record)
    return records


def _read_assignment_history_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return [dict(row) for row in csv.DictReader(csv_file)]


def _offset_episode_ids(new_records: list[dict], existing_records: list[dict]) -> None:
    next_episode_by_method = {}
    for record in existing_records:
        method = record["method"]
        next_episode_by_method[method] = max(next_episode_by_method.get(method, 0), int(record["episode"]) + 1)
    for record in new_records:
        method = record["method"]
        offset = next_episode_by_method.get(method, 0)
        record["episode"] = int(record["episode"]) + offset


def _offset_assignment_history_episode_ids(history_rows: list[dict], existing_records: list[dict]) -> None:
    next_episode_by_method = {}
    for record in existing_records:
        method = record["method"]
        next_episode_by_method[method] = max(next_episode_by_method.get(method, 0), int(record["episode"]) + 1)
    for row in history_rows:
        method = row["method"]
        row["episode"] = int(row["episode"]) + next_episode_by_method.get(method, 0)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[INFO]: wrote {path}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")
    print(f"[INFO]: wrote {path}")


def _decode_json_list(value: Any) -> list:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return decoded if isinstance(decoded, list) else []
    return value if isinstance(value, list) else []


def _episode_metric_diagnostics(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        rows.append(
            {
                "method": record.get("method"),
                "episode": record.get("episode"),
                "final_covered_count": record.get("final_covered_count"),
                "final_coverage": record.get("final_coverage"),
                "success": record.get("success"),
                "first_full_coverage_step": record.get("first_full_coverage_step"),
                "final_covered_viewpoint_ids": _decode_json_list(record.get("final_covered_viewpoint_ids")),
                "final_uncovered_viewpoint_ids": _decode_json_list(record.get("final_uncovered_viewpoint_ids")),
                "per_robot_selected_count": _decode_json_list(record.get("per_robot_selected_count")),
                "per_robot_completed_count": _decode_json_list(record.get("per_robot_completed_count")),
                "per_robot_repeated_assignment_count": _decode_json_list(
                    record.get("per_robot_repeated_assignment_count")
                ),
                "per_viewpoint_attempted_count": _decode_json_list(record.get("per_viewpoint_attempted_count")),
                "last_global_coverage_gain_step": record.get("last_global_coverage_gain_step"),
                "steps_since_last_global_coverage_gain": record.get("steps_since_last_global_coverage_gain"),
                "no_progress_steps_after_last_gain": record.get("no_progress_steps_after_last_gain"),
                "duplicate_selected_target_count": record.get("duplicate_selected_target_count"),
                "duplicate_selected_target_rate": record.get("duplicate_selected_target_rate"),
                "noop_when_available_count": record.get("noop_when_available_count"),
                "noop_when_available_rate": record.get("noop_when_available_rate"),
                "selected_path_cost_mean": record.get("selected_path_cost_mean"),
                "selected_path_cost_max": record.get("selected_path_cost_max"),
                "selected_path_cost_sum": record.get("selected_path_cost_sum"),
                "load_balance_selected_std": record.get("load_balance_selected_std"),
                "load_balance_completed_std": record.get("load_balance_completed_std"),
                "late_repeated_assignment_pattern": _decode_json_list(record.get("late_repeated_assignment_pattern")),
                "inter_robot_overlap_step_count": record.get("inter_robot_overlap_step_count"),
                "inter_robot_overlap_rate": record.get("inter_robot_overlap_rate"),
                "inter_robot_overlap_pair_count_total": record.get("inter_robot_overlap_pair_count_total"),
                "inter_robot_min_distance_min": record.get("inter_robot_min_distance_min"),
                "inter_robot_min_clearance_min": record.get("inter_robot_min_clearance_min"),
                "selected_target_conflict_step_count": record.get("selected_target_conflict_step_count"),
                "selected_target_conflict_rate": record.get("selected_target_conflict_rate"),
                "selected_target_conflict_pair_count_total": record.get("selected_target_conflict_pair_count_total"),
                "selected_target_min_distance_min": record.get("selected_target_min_distance_min"),
                "selected_target_min_clearance_min": record.get("selected_target_min_clearance_min"),
                "baseline_selected_target_conflict_step_count": record.get(
                    "baseline_selected_target_conflict_step_count"
                ),
                "baseline_selected_target_conflict_rate_mean": record.get(
                    "baseline_selected_target_conflict_rate_mean"
                ),
                "baseline_selected_target_conflict_pair_count_total": record.get(
                    "baseline_selected_target_conflict_pair_count_total"
                ),
                "baseline_selected_target_min_distance_min": record.get(
                    "baseline_selected_target_min_distance_min"
                ),
                "baseline_selected_target_min_clearance_min": record.get(
                    "baseline_selected_target_min_clearance_min"
                ),
                "baseline_selected_target_conflict_penalty_sum_total": record.get(
                    "baseline_selected_target_conflict_penalty_sum_total"
                ),
                "candidate_selected_target_conflict_step_count": record.get(
                    "candidate_selected_target_conflict_step_count"
                ),
                "candidate_selected_target_conflict_rate_mean": record.get(
                    "candidate_selected_target_conflict_rate_mean"
                ),
                "candidate_selected_target_conflict_pair_count_total": record.get(
                    "candidate_selected_target_conflict_pair_count_total"
                ),
                "candidate_selected_target_min_distance_min": record.get(
                    "candidate_selected_target_min_distance_min"
                ),
                "candidate_selected_target_min_clearance_min": record.get(
                    "candidate_selected_target_min_clearance_min"
                ),
                "candidate_selected_target_conflict_penalty_sum_total": record.get(
                    "candidate_selected_target_conflict_penalty_sum_total"
                ),
                "candidate_changed_assignment_rate_mean": record.get("candidate_changed_assignment_rate_mean"),
                "candidate_changed_assignment_count_total": record.get("candidate_changed_assignment_count_total"),
                "conflict_aware_solver_enabled": record.get("conflict_aware_solver_enabled"),
                "conflict_aware_fallback_step_count": record.get("conflict_aware_fallback_step_count"),
                "conflict_aware_fallback_rate": record.get("conflict_aware_fallback_rate"),
                "conflict_aware_candidate_combination_count_mean": record.get(
                    "conflict_aware_candidate_combination_count_mean"
                ),
                "conflict_aware_selected_target_conflict_pair_count_total": record.get(
                    "conflict_aware_selected_target_conflict_pair_count_total"
                ),
                "conflict_aware_selected_duplicate_pair_count_total": record.get(
                    "conflict_aware_selected_duplicate_pair_count_total"
                ),
                "conflict_aware_changed_vs_base_count_total": record.get(
                    "conflict_aware_changed_vs_base_count_total"
                ),
                "conflict_aware_changed_vs_base_rate_mean": record.get(
                    "conflict_aware_changed_vs_base_rate_mean"
                ),
                "actual_base_motion_intersection_step_count": record.get(
                    "actual_base_motion_intersection_step_count"
                ),
                "actual_base_motion_intersection_rate": record.get("actual_base_motion_intersection_rate"),
                "actual_base_motion_intersection_pair_count_total": record.get(
                    "actual_base_motion_intersection_pair_count_total"
                ),
                "actual_base_motion_intersection_pair_count_mean": record.get(
                    "actual_base_motion_intersection_pair_count_mean"
                ),
                "actual_base_motion_min_distance_to_footprint_min": record.get(
                    "actual_base_motion_min_distance_to_footprint_min"
                ),
                "actual_base_motion_min_distance_to_footprint_mean": record.get(
                    "actual_base_motion_min_distance_to_footprint_mean"
                ),
                "actual_base_motion_valid_robot_count_mean": record.get(
                    "actual_base_motion_valid_robot_count_mean"
                ),
                "actual_base_motion_skipped_robot_count_total": record.get(
                    "actual_base_motion_skipped_robot_count_total"
                ),
            }
        )
    return rows


def _safe_name(value: str) -> str:
    safe_chars = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_"):
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    safe = "".join(safe_chars).strip("_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe or "run"


def _resolve_output_dir(diagnostics: dict) -> Path:
    if args_cli.output_dir is not None and args_cli.output_name is None:
        return Path(args_cli.output_dir)

    base_dir = Path(args_cli.output_dir) if args_cli.output_dir is not None else Path("results/assignment_evaluation")
    if args_cli.output_name is not None:
        return base_dir / _safe_name(args_cli.output_name)

    scenario_label = diagnostics.get("scenario_name")
    if not scenario_label:
        csv_path = diagnostics.get("viewpoint_csv_path")
        if csv_path:
            scenario_label = Path(str(csv_path)).stem
        else:
            scenario_label = "fixed12_default"
    method_label = "-".join(str(method) for method in args_cli.methods)
    run_name = f"{scenario_label}_n{diagnostics.get('num_viewpoints', 'unknown')}_{method_label}"
    return base_dir / _safe_name(run_name)


def _print_summary(rows: list[dict]) -> None:
    if not rows:
        print("[WARN]: no summary rows")
        return
    print("[RESULT]: Stage 4A assignment method summary")
    header = (
        f"{'method':<14} {'episodes':>8} {'success':>8} {'coverage':>10} "
        f"{'steps_full':>10} {'auc':>10} {'dup':>8} {'noop':>8} {'valid':>8}"
    )
    print(header)
    for row in rows:
        print(
            f"{row['method']:<14} {row['episodes']:>8} {row['success_rate']:>8.3f} "
            f"{row['mean_final_coverage']:>10.3f} {row['mean_steps_to_full_coverage']:>10.1f} "
            f"{row['mean_coverage_auc']:>10.3f} {row['mean_duplicate_count']:>8.3f} "
            f"{row['mean_noop_rate']:>8.3f} {row['mean_valid_action_rate']:>8.3f}"
        )


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: dict) -> None:
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.num_episodes <= 0:
        raise ValueError("--num_episodes must be positive")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if args_cli.print_diagnostics_steps < 0:
        raise ValueError("--print_diagnostics_steps must be non-negative")
    if args_cli.diagnostic_interval < 0:
        raise ValueError("--diagnostic_interval must be non-negative")
    if args_cli.assignment_rl or args_cli.assignment_checkpoint_dir is not None:
        raise ValueError(
            "Stage 4A supports only baseline assignment methods and gated conflict-aware baseline variants; "
            "assignment-RL evaluation is disabled."
        )

    _set_global_seeds(args_cli.seed)
    all_records, diagnostics, assignment_history, retry_fallback_events, controller_state_trace = _evaluate_baseline_methods(
        list(args_cli.methods), _clone_env_cfg(env_cfg)
    )

    output_dir = _resolve_output_dir(diagnostics)
    per_episode_path = output_dir / "per_episode.csv"
    summary_path = output_dir / "summary.csv"
    diagnostics_path = output_dir / "diagnostics.json"
    assignment_history_path = output_dir / "assignment_history.csv"
    retry_fallback_events_path = output_dir / "retry_fallback_events.csv"
    controller_state_trace_path = output_dir / "controller_state_trace.csv"
    controller_state_trace_summary_path = output_dir / "controller_state_trace_summary.csv"
    if "obstacle_aware_candidate_comparison" in diagnostics:
        diagnostics["obstacle_aware_candidate_comparison"]["output_path"] = str(diagnostics_path)
    existing_records = _read_per_episode_csv(per_episode_path) if args_cli.append_csv else []
    if existing_records:
        _offset_episode_ids(all_records, existing_records)
        _offset_assignment_history_episode_ids(assignment_history, existing_records)
        _offset_assignment_history_episode_ids(controller_state_trace, existing_records)
        all_records = existing_records + all_records
    if args_cli.append_csv and args_cli.write_assignment_history:
        existing_history = _read_assignment_history_csv(assignment_history_path)
        if existing_history:
            assignment_history = existing_history + assignment_history
    summary_rows = _summarize(all_records)
    controller_state_trace_summary_rows = _summarize_controller_state_trace(controller_state_trace)
    diagnostics["metric_consistency_checks"] = {
        "final_coverage_equals_final_covered_count_over_num_viewpoints": True,
        "success_requires_final_covered_count_equal_num_viewpoints": True,
        "final_coverage_one_requires_final_covered_count_equal_num_viewpoints": True,
        "timeout_does_not_imply_full_coverage": True,
    }
    diagnostics["assignment_history"] = {
        "enabled": bool(args_cli.write_assignment_history),
        "path": str(assignment_history_path) if args_cli.write_assignment_history else None,
        "rows": len(assignment_history) if args_cli.write_assignment_history else 0,
        "fields": ASSIGNMENT_HISTORY_FIELDS if args_cli.write_assignment_history else [],
    }
    diagnostics["rl_dynamic_assignment_reporting_counters"] = {
        "enabled": True,
        "phase": "Phase 9B-1",
        "behavior_change": False,
        "source": "evaluation_reporting_only",
        "per_episode_fields": [
            "per_robot_selected_count",
            "per_robot_completed_count",
            "per_robot_repeated_assignment_count",
            "per_viewpoint_attempted_count",
            "last_global_coverage_gain_step",
            "steps_since_last_global_coverage_gain",
            "no_progress_steps_after_last_gain",
            "duplicate_selected_target_count",
            "duplicate_selected_target_rate",
            "noop_when_available_count",
            "noop_when_available_rate",
            "selected_path_cost_mean",
            "selected_path_cost_max",
            "selected_path_cost_sum",
            "load_balance_selected_std",
            "load_balance_completed_std",
            "late_repeated_assignment_pattern",
        ],
        "summary_fields": [
            "per_robot_selected_count_mean",
            "per_robot_completed_count_mean",
            "per_robot_repeated_assignment_count_mean",
            "per_viewpoint_attempted_count_sum",
            "mean_steps_since_last_global_coverage_gain",
            "mean_no_progress_steps_after_last_gain",
            "duplicate_selected_target_count_total",
            "duplicate_selected_target_rate_mean",
            "noop_when_available_count_total",
            "noop_when_available_rate_mean",
            "selected_path_cost_mean",
            "selected_path_cost_max",
            "selected_path_cost_sum_total",
            "load_balance_selected_std_mean",
            "load_balance_completed_std_mean",
            "late_repeated_assignment_pattern_summary",
        ],
        "assignment_history_fields": [
            "available_viewpoint_count",
            "noop_when_available",
            "is_repeated_assignment",
            "selected_path_cost",
            "duplicate_selected_target_count_step",
        ],
        "definitions": {
            "per_robot_completed_count": "fractional credit for newly covered viewpoints selected by one or more robots; simultaneous duplicate completion splits one viewpoint across selected robots",
            "duplicate_selected_target_rate": "duplicate_selected_target_count divided by non-noop selected assignments",
            "noop_when_available_rate": "noop_when_available_count divided by noop selections",
            "selected_path_cost": "selected entry from the evaluator problem cost_matrix for non-noop selected assignments",
            "late_repeated_assignment_pattern": "consecutive same robot-viewpoint selections accumulated after the last global coverage gain",
        },
        "unavailable_counters": [],
    }
    diagnostics["retry_fallback_events"] = {
        "enabled": bool(args_cli.assignment_retry_fallback),
        "path": str(retry_fallback_events_path) if args_cli.assignment_retry_fallback else None,
        "rows": len(retry_fallback_events) if args_cli.assignment_retry_fallback else 0,
        "fields": RETRY_FALLBACK_EVENT_FIELDS if args_cli.assignment_retry_fallback else [],
    }
    controller_trace_diagnostics = diagnostics.setdefault("controller_state_trace", {})
    controller_trace_diagnostics.update(
        {
            "enabled": bool(args_cli.write_controller_state_trace),
            "path": str(controller_state_trace_path) if args_cli.write_controller_state_trace else None,
            "summary_path": (
                str(controller_state_trace_summary_path) if args_cli.write_controller_state_trace else None
            ),
            "rows": len(controller_state_trace) if args_cli.write_controller_state_trace else 0,
            "summary_rows": (
                len(controller_state_trace_summary_rows) if args_cli.write_controller_state_trace else 0
            ),
            "fields": CONTROLLER_STATE_TRACE_FIELDS if args_cli.write_controller_state_trace else [],
            "summary_fields": (
                CONTROLLER_STATE_TRACE_SUMMARY_FIELDS if args_cli.write_controller_state_trace else []
            ),
            "unavailable_fields": sorted(set(controller_trace_diagnostics.get("unavailable_fields", []))),
        }
    )
    diagnostics["episode_metric_diagnostics"] = _episode_metric_diagnostics(all_records)
    _write_csv(per_episode_path, all_records, PER_EPISODE_FIELDS)
    _write_csv(summary_path, summary_rows, SUMMARY_FIELDS)
    if args_cli.write_assignment_history:
        _write_csv(assignment_history_path, assignment_history, ASSIGNMENT_HISTORY_FIELDS)
    if args_cli.assignment_retry_fallback:
        _write_csv(retry_fallback_events_path, retry_fallback_events, RETRY_FALLBACK_EVENT_FIELDS)
    if args_cli.write_controller_state_trace:
        _write_csv(controller_state_trace_path, controller_state_trace, CONTROLLER_STATE_TRACE_FIELDS)
        _write_csv(
            controller_state_trace_summary_path,
            controller_state_trace_summary_rows,
            CONTROLLER_STATE_TRACE_SUMMARY_FIELDS,
        )
    _write_json(diagnostics_path, diagnostics)
    _print_summary(summary_rows)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
