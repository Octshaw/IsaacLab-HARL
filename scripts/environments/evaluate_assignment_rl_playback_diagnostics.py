# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Playback diagnostics for fixed-N assignment RL checkpoints.

This script is diagnostic-only. It mirrors the assignment baseline reporting
fields for an RL checkpoint without changing rewards, masks, controller logic,
or environment dynamics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
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

from scenario_config import (  # noqa: E402
    apply_scenario_config_to_env_cfg,
    load_scenario_config,
    smoke_defaults_from_config,
    validate_smoke_args,
)

from isaaclab.app import AppLauncher  # noqa: E402


pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional assignment scenario YAML/JSON.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="Run proxy playback diagnostics for a fixed-N assignment RL checkpoint.",
    parents=[pre_parser],
)
parser.add_argument("--algorithm", type=str, default="happo", choices=["happo", "hatrpo", "haa2c"], help="HARL algorithm.")
parser.add_argument("--assignment_rl", action="store_true", help="Accepted for explicitness; this script is assignment-only.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--task", type=str, default=None, help="Isaac Lab task name.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--dir", type=str, required=True, help="Assignment RL checkpoint model directory.")
parser.add_argument("--num_episodes", type=int, default=1, help="Number of playback episodes.")
parser.add_argument("--max_steps", type=int, default=300, help="Maximum wrapper steps per episode.")
parser.add_argument("--output_dir", type=str, required=True, help="Directory for diagnostics.json/CSV outputs.")
parser.add_argument("--stop_on_done", action="store_true", help="End each episode when any env reports done.")
AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli, hydra_args = parser.parse_known_args()
if args_cli.scenario_config is not None:
    validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)
sys.argv = [sys.argv[0]] + hydra_args


def _warm_start_torch_cuda(args: argparse.Namespace) -> None:
    """Initialize PyTorch/cuBLAS before Isaac Kit owns the CUDA context."""

    device_arg = str(getattr(args, "device", "cuda:0")).lower()
    if device_arg == "cpu" or not device_arg.startswith("cuda"):
        return
    if not torch.cuda.is_available():
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

from harl.algorithms.actors import ALGO_REGISTRY  # noqa: E402
from harl.utils.models_tools import init_device  # noqa: E402

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor  # noqa: E402
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env  # noqa: E402
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import (  # noqa: E402
    compute_assignment_duplicate_count,
)
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402


ALGORITHM = args_cli.algorithm.lower()
agent_cfg_entry_point = f"harl_{ALGORITHM}_cfg_entry_point"


PER_EPISODE_FIELDS = [
    "method",
    "episode",
    "checkpoint_dir",
    "checkpoint_kind",
    "num_envs",
    "num_agents",
    "num_viewpoints",
    "noop_id",
    "episode_length",
    "steps",
    "done",
    "total_return",
    "final_coverage",
    "coverage_auc",
    "new_viewpoints_total",
    "final_uncovered_viewpoint_ids",
    "steps_since_last_global_coverage_gain",
    "no_progress_steps_after_last_gain",
    "late_repeated_assignment_pattern",
    "late_repeated_assignment_count",
    "per_viewpoint_attempted_count",
    "per_robot_selected_count",
    "per_robot_completed_count",
    "per_robot_repeated_assignment_count",
    "duplicate_selected_target_count",
    "duplicate_selected_target_rate",
    "noop_when_available_count",
    "noop_when_available_rate",
    "valid_action_count_mean",
    "selected_available_mask_mean",
    "selected_target_conflict_count",
    "selected_target_conflict_rate",
    "selected_target_conflict_min_clearance",
    "inter_robot_overlap_count",
    "inter_robot_overlap_rate",
    "inter_robot_min_clearance",
    "actual_base_motion_intersection_count",
    "actual_base_motion_intersection_rate",
    "actual_base_motion_min_distance",
    "selected_path_cost_sum",
    "selected_path_cost_mean",
    "selected_path_cost_max",
    "cooldown_enabled",
    "cooldown_trigger_count",
    "cooldown_active_count",
    "cooldown_suppressed_count",
    "max_cooldown_remaining",
]

SUMMARY_FIELDS = [
    "method",
    "checkpoint_dir",
    "checkpoint_kind",
    "episodes",
    "num_envs",
    "num_agents",
    "num_viewpoints",
    "noop_id",
    "max_steps",
    "final_coverage_mean",
    "final_coverage_std",
    "coverage_auc_mean",
    "coverage_auc_std",
    "new_viewpoints_total_mean",
    "duplicate_selected_target_rate_mean",
    "noop_when_available_rate_mean",
    "selected_available_mask_mean",
    "selected_target_conflict_rate_mean",
    "inter_robot_overlap_rate_mean",
    "actual_base_motion_intersection_rate_mean",
    "selected_path_cost_mean",
    "selected_path_cost_max",
    "late_repeated_assignment_count_mean",
    "cooldown_enabled",
    "cooldown_trigger_count_mean",
    "cooldown_active_count_mean",
    "cooldown_suppressed_count_mean",
    "max_cooldown_remaining",
    "episode_steps_mean",
]

ASSIGNMENT_HISTORY_FIELDS = [
    "method",
    "episode",
    "step",
    "env_id",
    "robot_id",
    "robot_name",
    "selected_action",
    "selected_viewpoint_id",
    "assigned_viewpoint_id",
    "is_noop",
    "selected_available",
    "selected_covered_before",
    "selected_feasible",
    "new_coverage_gain_after_step",
    "coverage_ratio_after_step",
    "robot_base_x",
    "robot_base_y",
    "target_x",
    "target_y",
    "selected_path_cost",
    "duplicate_selected_target_on_step",
    "noop_when_available",
    "same_target_streak",
    "steps_since_global_coverage_gain",
    "available_viewpoint_count",
    "covered_before_count",
    "covered_after_count",
    "newly_covered_viewpoint_ids",
    "actual_base_motion_intersects_component",
    "actual_base_motion_distance",
    "cooldown_active_for_selected_pair",
    "cooldown_remaining_for_selected_pair",
    "cooldown_triggered_after_step",
    "cooldown_suppressed_available_count_for_robot",
    "failed_attempt_count_for_selected_pair",
]


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=_json_default), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=_json_default, sort_keys=True)
    if isinstance(value, torch.Tensor):
        return json.dumps(value.detach().cpu().tolist())
    if isinstance(value, np.ndarray):
        return json.dumps(value.tolist())
    if isinstance(value, float) and math.isnan(value):
        return "nan"
    return value


def _scalar_float(value: Any, default: float = float("nan")) -> float:
    if isinstance(value, torch.Tensor):
        if value.numel() == 0:
            return default
        return float(value.detach().to(dtype=torch.float32).mean().cpu().item())
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return default
        return float(np.asarray(value, dtype=np.float32).mean())
    if isinstance(value, (np.integer, np.floating)):
        return float(value.item())
    if isinstance(value, (int, float, bool)):
        return float(value)
    return default


def _sum_reward_tensor(rewards: torch.Tensor) -> torch.Tensor:
    if rewards.ndim < 2:
        raise ValueError(f"Expected reward tensor with env and agent dims, got shape {tuple(rewards.shape)}")
    reduce_dims = tuple(range(1, rewards.ndim))
    return rewards.to(dtype=torch.float32).sum(dim=reduce_dims)


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _population_std(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    mean = sum(finite) / len(finite)
    return float(math.sqrt(sum((value - mean) ** 2 for value in finite) / len(finite)))


def _ids_from_mask(mask: torch.Tensor) -> list[list[int]]:
    return [
        torch.nonzero(mask[env_id], as_tuple=False).flatten().detach().cpu().tolist()
        for env_id in range(mask.shape[0])
    ]


def _tensor_row_json(tensor: torch.Tensor, env_id: int, *, precision: int | None = None) -> str:
    values = tensor[env_id].detach().cpu().tolist()
    if precision is not None:
        values = _round_nested(values, precision)
    return json.dumps(values)


def _round_nested(value: Any, digits: int) -> Any:
    if isinstance(value, list):
        return [_round_nested(item, digits) for item in value]
    if isinstance(value, float):
        return round(value, digits) if math.isfinite(value) else value
    return value


def _decode_actions(raw_ids: torch.Tensor, noop_id: int) -> torch.Tensor:
    return torch.where(raw_ids == int(noop_id), torch.full_like(raw_ids, -1), raw_ids)


def _valid_assignment_decisions(problem: dict[str, Any], assignment: torch.Tensor) -> torch.Tensor:
    available = problem["available_mask"].to(dtype=torch.bool)
    num_viewpoints = int(problem["num_viewpoints"])
    valid = assignment < 0
    non_noop = assignment >= 0
    in_range = (assignment >= 0) & (assignment < num_viewpoints)
    if bool(in_range.any()):
        safe_ids = assignment.clamp(min=0, max=max(0, num_viewpoints - 1)).unsqueeze(-1)
        selected_available = torch.gather(available, dim=2, index=safe_ids).squeeze(-1)
        valid = valid | (non_noop & in_range & selected_available)
    return valid


def _selected_path_cost(problem: dict[str, Any], assignment: torch.Tensor) -> torch.Tensor:
    cost_matrix = problem["cost_matrix"].to(dtype=torch.float32)
    selected_path_cost = torch.full(assignment.shape, float("nan"), dtype=torch.float32, device=assignment.device)
    num_viewpoints = int(problem["num_viewpoints"])
    if num_viewpoints <= 0:
        return selected_path_cost
    valid = (assignment >= 0) & (assignment < num_viewpoints)
    safe_ids = assignment.clamp(min=0, max=num_viewpoints - 1).unsqueeze(-1)
    selected = torch.gather(cost_matrix, dim=2, index=safe_ids).squeeze(-1)
    return torch.where(valid, selected, selected_path_cost)


def _assignment_reporting_step(
    buffers: dict[str, torch.Tensor],
    problem: dict[str, Any],
    assignment: torch.Tensor,
) -> dict[str, torch.Tensor]:
    available = problem["available_mask"].to(dtype=torch.bool)
    feasible = problem.get("feasible_mask", available).to(dtype=torch.bool)
    covered_before = problem["viewpoints_covered"].to(dtype=torch.bool)
    num_viewpoints = int(problem["num_viewpoints"])
    non_noop = assignment >= 0
    valid_viewpoint = non_noop & (assignment < num_viewpoints)
    safe_ids = assignment.clamp(min=0, max=max(0, num_viewpoints - 1)).unsqueeze(-1)
    selected_available = torch.zeros_like(assignment, dtype=torch.bool)
    selected_feasible = torch.zeros_like(assignment, dtype=torch.bool)
    selected_covered_before = torch.zeros_like(assignment, dtype=torch.bool)
    if num_viewpoints > 0:
        selected_available = torch.gather(available, dim=2, index=safe_ids).squeeze(-1) & valid_viewpoint
        selected_feasible = torch.gather(feasible, dim=2, index=safe_ids).squeeze(-1) & valid_viewpoint
        selected_covered_before = torch.gather(covered_before.unsqueeze(1).expand_as(available), dim=2, index=safe_ids).squeeze(-1)
        selected_covered_before = selected_covered_before & valid_viewpoint
    noop_when_available = (assignment < 0) & available.any(dim=-1)
    repeated = valid_viewpoint & (assignment == buffers["previous_assignment"])
    same_target_streak_next = torch.where(
        valid_viewpoint,
        torch.where(repeated, buffers["same_target_streak"] + 1.0, torch.ones_like(buffers["same_target_streak"])),
        torch.zeros_like(buffers["same_target_streak"]),
    )
    selected_cost = _selected_path_cost(problem, assignment)
    return {
        "selected_available": selected_available,
        "selected_feasible": selected_feasible,
        "selected_covered_before": selected_covered_before,
        "noop_when_available": noop_when_available,
        "valid_viewpoint": valid_viewpoint,
        "repeated": repeated,
        "same_target_streak_next": same_target_streak_next,
        "selected_path_cost": selected_cost,
    }


def _selected_target_conflict_diagnostics(
    problem: dict[str, Any],
    assignment: torch.Tensor,
    viewpoint_ids: torch.Tensor,
) -> dict[str, Any]:
    device = assignment.device
    num_envs, num_agents = assignment.shape
    pair_count = torch.zeros(num_envs, dtype=torch.long, device=device)
    min_distance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    min_clearance = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
    pairs_sample: list[dict[str, Any]] = []

    enabled = bool(problem.get("inter_robot_conflict_diagnostics_enabled", False)) and bool(
        problem.get("inter_robot_target_conflict_enabled", True)
    )
    radius = float(problem.get("inter_robot_target_conflict_radius", problem.get("inter_robot_conflict_robot_footprint_radius", 0.35)))
    margin = float(problem.get("inter_robot_target_conflict_safety_margin", problem.get("inter_robot_conflict_safety_margin", 0.15)))
    threshold = (2.0 * radius) + margin
    if not enabled:
        return {
            "selected_target_conflict_pair_count": pair_count,
            "selected_target_conflict_min_distance": min_distance,
            "selected_target_conflict_min_clearance": min_clearance,
            "selected_target_conflict_pairs_sample": pairs_sample,
            "selected_target_conflict_skipped_reason": "disabled",
            "selected_target_conflict_threshold": threshold,
        }
    if num_agents < 2:
        return {
            "selected_target_conflict_pair_count": pair_count,
            "selected_target_conflict_min_distance": min_distance,
            "selected_target_conflict_min_clearance": min_clearance,
            "selected_target_conflict_pairs_sample": pairs_sample,
            "selected_target_conflict_skipped_reason": "fewer_than_two_robots",
            "selected_target_conflict_threshold": threshold,
        }

    viewpoint_pos = problem["viewpoint_pos"].to(dtype=torch.float32)
    min_distance.fill_(float("inf"))
    min_clearance.fill_(float("inf"))
    max_sample = 10
    for robot_i in range(num_agents):
        for robot_j in range(robot_i + 1, num_agents):
            view_i = assignment[:, robot_i]
            view_j = assignment[:, robot_j]
            valid = (view_i >= 0) & (view_j >= 0) & (view_i < viewpoint_ids.numel()) & (view_j < viewpoint_ids.numel())
            if not bool(valid.any()):
                continue
            safe_i = view_i.clamp(min=0, max=viewpoint_ids.numel() - 1)
            safe_j = view_j.clamp(min=0, max=viewpoint_ids.numel() - 1)
            pos_i = viewpoint_pos[torch.arange(num_envs, device=device), safe_i, :2]
            pos_j = viewpoint_pos[torch.arange(num_envs, device=device), safe_j, :2]
            distance = torch.linalg.norm(pos_i - pos_j, dim=-1)
            distance = torch.where(valid, distance, torch.full_like(distance, float("inf")))
            clearance = distance - threshold
            conflict = valid & (clearance < 0.0)
            pair_count += conflict.to(dtype=torch.long)
            min_distance = torch.minimum(min_distance, distance)
            min_clearance = torch.minimum(min_clearance, clearance)
            if len(pairs_sample) < max_sample and bool(conflict.any()):
                for env_id in torch.nonzero(conflict, as_tuple=False).flatten().detach().cpu().tolist():
                    if len(pairs_sample) >= max_sample:
                        break
                    pairs_sample.append(
                        {
                            "env_id": int(env_id),
                            "robot_i": int(robot_i),
                            "robot_j": int(robot_j),
                            "viewpoint_i": int(view_i[env_id].item()),
                            "viewpoint_j": int(view_j[env_id].item()),
                            "distance": float(distance[env_id].item()),
                            "clearance": float(clearance[env_id].item()),
                            "threshold": threshold,
                        }
                    )
    min_distance = torch.where(torch.isinf(min_distance), torch.full_like(min_distance, float("nan")), min_distance)
    min_clearance = torch.where(torch.isinf(min_clearance), torch.full_like(min_clearance, float("nan")), min_clearance)
    return {
        "selected_target_conflict_pair_count": pair_count,
        "selected_target_conflict_min_distance": min_distance,
        "selected_target_conflict_min_clearance": min_clearance,
        "selected_target_conflict_pairs_sample": pairs_sample,
        "selected_target_conflict_skipped_reason": None,
        "selected_target_conflict_threshold": threshold,
    }


def _linearly_spaced_points(start_xy: torch.Tensor, end_xy: torch.Tensor, sample_step: float) -> list[tuple[float, float]]:
    start = start_xy.detach().cpu().tolist()
    end = end_xy.detach().cpu().tolist()
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    length = math.hypot(dx, dy)
    sample_count = max(1, int(math.ceil(length / max(sample_step, 1.0e-6))))
    return [
        (float(start[0]) + (sample / sample_count) * dx, float(start[1]) + (sample / sample_count) * dy)
        for sample in range(sample_count + 1)
    ]


def _segment_min_distance_to_footprint(start_xy: torch.Tensor, end_xy: torch.Tensor, footprint: Any, sample_step: float) -> float:
    occupied_cells = getattr(footprint, "inflated_occupied_cells", None) or getattr(footprint, "occupied_cells", None)
    if not occupied_cells:
        return float("nan")
    min_distance = float("inf")
    points = _linearly_spaced_points(start_xy, end_xy, sample_step)
    for point in points:
        for row, col in occupied_cells:
            center = footprint.cell_center(int(row), int(col))
            distance = math.hypot(point[0] - float(center[0]), point[1] - float(center[1]))
            min_distance = min(min_distance, distance)
    return min_distance if math.isfinite(min_distance) else float("nan")


def _actual_base_motion_step_diagnostics(
    env: Any,
    *,
    previous_base_pos: torch.Tensor,
    current_base_pos: torch.Tensor,
    assignment: torch.Tensor,
) -> dict[str, Any]:
    cfg = getattr(env, "cfg", None)
    device = assignment.device
    num_envs, num_agents = assignment.shape
    intersects = torch.zeros((num_envs, num_agents), dtype=torch.bool, device=device)
    distance = torch.full((num_envs, num_agents), float("nan"), dtype=torch.float32, device=device)
    sample_rows: list[dict[str, Any]] = []

    enabled = bool(getattr(cfg, "actual_base_motion_obstacle_diagnostics_enabled", False))
    footprint = getattr(cfg, "component_obstacle_footprint", None)
    if not enabled or footprint is None:
        return {
            "actual_base_motion_intersects_component": intersects,
            "actual_base_motion_distance": distance,
            "actual_base_motion_pairs_sample": sample_rows,
            "actual_base_motion_skipped_reason": "disabled" if not enabled else "missing_footprint",
        }

    sample_step = float(getattr(cfg, "actual_base_motion_line_sample_step", getattr(footprint, "line_sample_step", 0.10)))
    min_motion_distance = float(getattr(cfg, "actual_base_motion_min_motion_distance", 1.0e-6))
    max_sample = int(getattr(cfg, "actual_base_motion_max_pairs_sample", 10))
    for env_id in range(num_envs):
        for robot_id in range(num_agents):
            start_xy = previous_base_pos[env_id, robot_id, :2]
            end_xy = current_base_pos[env_id, robot_id, :2]
            motion_distance = float(torch.linalg.norm(end_xy - start_xy).detach().cpu().item())
            if motion_distance < min_motion_distance:
                distance[env_id, robot_id] = float("nan")
                continue
            hit = bool(footprint.intersects_segment(start_xy.detach().cpu().tolist(), end_xy.detach().cpu().tolist()))
            min_distance = _segment_min_distance_to_footprint(start_xy, end_xy, footprint, sample_step)
            intersects[env_id, robot_id] = hit
            distance[env_id, robot_id] = float(min_distance)
            if hit and len(sample_rows) < max_sample:
                sample_rows.append(
                    {
                        "env_id": int(env_id),
                        "robot_id": int(robot_id),
                        "assigned_viewpoint_id": int(assignment[env_id, robot_id].item()),
                        "start_xy": [float(start_xy[0].item()), float(start_xy[1].item())],
                        "end_xy": [float(end_xy[0].item()), float(end_xy[1].item())],
                        "motion_distance": motion_distance,
                        "min_distance": float(min_distance),
                    }
                )

    return {
        "actual_base_motion_intersects_component": intersects,
        "actual_base_motion_distance": distance,
        "actual_base_motion_pairs_sample": sample_rows,
        "actual_base_motion_skipped_reason": None,
    }


def _install_prereset_coverage_capture(unwrapped: Any) -> dict[str, Any]:
    state: dict[str, Any] = {"snapshots": {}, "installed": False}
    original_reset_idx = getattr(unwrapped, "_reset_idx", None)
    if original_reset_idx is None or not callable(original_reset_idx):
        return state

    def wrapped_reset_idx(env_ids, *args, **kwargs):
        try:
            if isinstance(env_ids, torch.Tensor):
                env_id_list = env_ids.detach().cpu().flatten().tolist()
            elif env_ids is None:
                env_id_list = list(range(int(getattr(unwrapped, "num_envs", 1))))
            else:
                env_id_list = list(env_ids)
            covered = getattr(unwrapped, "viewpoints_covered", None)
            if isinstance(covered, torch.Tensor):
                for env_id in env_id_list:
                    state["snapshots"][int(env_id)] = covered[int(env_id)].detach().clone()
        except Exception as exc:  # pragma: no cover - diagnostic best effort
            state["last_error"] = repr(exc)
        return original_reset_idx(env_ids, *args, **kwargs)

    setattr(unwrapped, "_reset_idx", wrapped_reset_idx)
    state["installed"] = True
    state["original_reset_idx"] = original_reset_idx
    return state


def _restore_prereset_coverage_capture(unwrapped: Any, state: dict[str, Any]) -> None:
    original = state.get("original_reset_idx")
    if original is not None:
        setattr(unwrapped, "_reset_idx", original)


def _coverage_from_env(unwrapped: Any, done_envs: torch.Tensor, capture: dict[str, Any]) -> torch.Tensor:
    covered = unwrapped.viewpoints_covered.detach().clone().to(dtype=torch.bool)
    snapshots = capture.get("snapshots", {})
    if isinstance(snapshots, dict) and bool(done_envs.any()):
        for env_id in torch.nonzero(done_envs, as_tuple=False).flatten().detach().cpu().tolist():
            snapshot = snapshots.pop(int(env_id), None)
            if isinstance(snapshot, torch.Tensor):
                covered[int(env_id)] = snapshot.to(device=covered.device, dtype=torch.bool)
    return covered


def _actor_checkpoint_path(model_dir: Path, agent_name: str, agent_id: int) -> Path:
    candidates = (
        model_dir / f"actor_agent_{agent_name}.pt",
        model_dir / f"actor_agent_{agent_id}.pt",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    joined = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not find assignment actor checkpoint for {agent_name}; checked: {joined}")


def _load_assignment_actors(wrapper: Any, algo_args: dict[str, Any], model_dir: Path, device: torch.device):
    actor_args = {**algo_args["model"], **algo_args["algo"]}
    actors = []
    for agent_id, agent_name in enumerate(wrapper.agents):
        actor = ALGO_REGISTRY[ALGORITHM](
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
                f"Failed to load {checkpoint_path}. Expected assignment-mode Discrete/Categorical actor "
                "weights for this fixed-N viewpoint count, not old N=12 assignment or 9D continuous scan weights."
            ) from exc
        actor.prep_rollout()
        actors.append(actor)

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
                "assignment diagnostics expected HARL Categorical actor for Discrete action space, "
                f"got action_type={action_type}, distribution_head={action_head_name}"
            )
    return actors


def _assert_available_actions(wrapper: Any, available_actions: torch.Tensor | None) -> None:
    if available_actions is None:
        raise RuntimeError("assignment playback diagnostics requires available_actions, got None")
    expected_shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1)
    if tuple(available_actions.shape) != expected_shape:
        raise RuntimeError(f"available_actions shape mismatch: expected {expected_shape}, got {tuple(available_actions.shape)}")


def _checkpoint_kind(model_dir: Path) -> str:
    name = model_dir.name.lower()
    if name == "models":
        return "models"
    if name == "best_model":
        return "best_model"
    return "unknown"


def _exp_name_from_checkpoint(model_dir: Path) -> str:
    parts = model_dir.parts
    if len(parts) >= 3 and parts[-1].lower() in {"models", "best_model"}:
        return parts[-3]
    return model_dir.parent.name


def _init_buffers(num_envs: int, num_agents: int, num_viewpoints: int, device: torch.device) -> dict[str, torch.Tensor]:
    return {
        "length": torch.zeros(num_envs, dtype=torch.long, device=device),
        "return": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "coverage_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "new_viewpoints_total": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "previous_assignment": torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device),
        "same_target_streak": torch.zeros((num_envs, num_agents), dtype=torch.float32, device=device),
        "per_viewpoint_attempted": torch.zeros((num_envs, num_viewpoints), dtype=torch.long, device=device),
        "per_robot_selected": torch.zeros((num_envs, num_agents), dtype=torch.float32, device=device),
        "per_robot_completed": torch.zeros((num_envs, num_agents), dtype=torch.float32, device=device),
        "per_robot_repeated": torch.zeros((num_envs, num_agents), dtype=torch.float32, device=device),
        "steps_since_gain": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "no_progress_after_last_gain": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "late_repeated": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "duplicate_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "noop_when_available_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "valid_action_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_available_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "decision_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_path_cost_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_path_cost_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_path_cost_max": torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device),
        "selected_target_conflict_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_conflict_decisions": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "selected_target_conflict_min_clearance": torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device),
        "inter_robot_overlap_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_overlap_decisions": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "inter_robot_min_clearance": torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device),
        "actual_base_motion_intersection_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_decisions": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "actual_base_motion_min_distance": torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device),
        "cooldown_trigger_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "cooldown_active_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "cooldown_suppressed_count_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "cooldown_max_remaining": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "cooldown_step_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
    }


def _update_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    rewards: torch.Tensor,
    assignment: torch.Tensor,
    pre_problem: dict[str, Any],
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    reporting: dict[str, torch.Tensor],
    selected_target_conflict: dict[str, Any],
    inter_robot_conflict: dict[str, Any],
    actual_base_motion: dict[str, Any],
) -> None:
    num_envs, num_agents = assignment.shape
    num_viewpoints = int(pre_problem["num_viewpoints"])
    reward_sum = _sum_reward_tensor(rewards)
    buffers["return"] += reward_sum
    buffers["length"] += 1

    coverage_ratio = covered_after.to(dtype=torch.float32).mean(dim=-1)
    buffers["coverage_sum"] += coverage_ratio
    newly_covered = covered_after & (~covered_before)
    newly_covered_count = newly_covered.to(dtype=torch.float32).sum(dim=-1)
    buffers["new_viewpoints_total"] += newly_covered_count
    has_gain = newly_covered_count > 0
    buffers["steps_since_gain"] = torch.where(has_gain, torch.zeros_like(buffers["steps_since_gain"]), buffers["steps_since_gain"] + 1.0)
    buffers["no_progress_after_last_gain"] = buffers["steps_since_gain"]

    duplicate_count = compute_assignment_duplicate_count(assignment).to(dtype=torch.float32)
    buffers["duplicate_count"] += duplicate_count
    buffers["noop_when_available_count"] += reporting["noop_when_available"].to(dtype=torch.float32).sum(dim=1)
    valid_decisions = _valid_assignment_decisions(pre_problem, assignment)
    buffers["valid_action_count_sum"] += valid_decisions.to(dtype=torch.float32).sum(dim=1)
    buffers["selected_available_sum"] += reporting["selected_available"].to(dtype=torch.float32).sum(dim=1)
    buffers["decision_count"] += float(num_agents)

    non_noop = (assignment >= 0) & (assignment < num_viewpoints)
    buffers["per_robot_selected"] += non_noop.to(dtype=torch.float32)
    buffers["per_robot_repeated"] += reporting["repeated"].to(dtype=torch.float32)
    buffers["same_target_streak"] = reporting["same_target_streak_next"]
    buffers["late_repeated"] += (reporting["repeated"] & (buffers["steps_since_gain"].unsqueeze(1) > 0.0)).to(dtype=torch.float32).sum(dim=1)
    buffers["previous_assignment"] = assignment.clone()

    for robot_id in range(num_agents):
        selected = assignment[:, robot_id]
        valid_envs = torch.nonzero((selected >= 0) & (selected < num_viewpoints), as_tuple=False).flatten()
        if valid_envs.numel() == 0:
            continue
        buffers["per_viewpoint_attempted"][valid_envs, selected[valid_envs]] += 1

    selected_matrix = torch.zeros(num_envs, num_agents, num_viewpoints, dtype=torch.bool, device=assignment.device)
    env_indices, agent_indices = torch.nonzero(non_noop, as_tuple=True)
    if env_indices.numel() > 0:
        selected_matrix[env_indices, agent_indices, assignment[env_indices, agent_indices]] = True
    newly_selected = selected_matrix & newly_covered.unsqueeze(1)
    duplicate_completion_count = newly_selected.to(dtype=torch.float32).sum(dim=1, keepdim=True).clamp(min=1.0)
    buffers["per_robot_completed"] += (newly_selected.to(dtype=torch.float32) / duplicate_completion_count).sum(dim=-1)

    selected_cost = reporting["selected_path_cost"]
    finite_cost = torch.isfinite(selected_cost)
    buffers["selected_path_cost_sum"] += torch.where(finite_cost, selected_cost, torch.zeros_like(selected_cost)).sum(dim=1)
    buffers["selected_path_cost_count"] += finite_cost.to(dtype=torch.float32).sum(dim=1)
    row_max = torch.where(finite_cost, selected_cost, torch.full_like(selected_cost, float("-inf"))).max(dim=1).values
    current_max = torch.nan_to_num(buffers["selected_path_cost_max"], nan=float("-inf"))
    buffers["selected_path_cost_max"] = torch.maximum(current_max, row_max)
    buffers["selected_path_cost_max"] = torch.where(
        torch.isinf(buffers["selected_path_cost_max"]),
        torch.full_like(buffers["selected_path_cost_max"], float("nan")),
        buffers["selected_path_cost_max"],
    )

    selected_pair_count = selected_target_conflict["selected_target_conflict_pair_count"].to(dtype=torch.float32)
    buffers["selected_target_conflict_count"] += selected_pair_count
    buffers["selected_target_conflict_decisions"] += 1.0
    selected_clearance = selected_target_conflict["selected_target_conflict_min_clearance"].to(dtype=torch.float32)
    buffers["selected_target_conflict_min_clearance"] = _nanmin(buffers["selected_target_conflict_min_clearance"], selected_clearance)

    overlap_count = inter_robot_conflict.get("inter_robot_overlap_pair_count")
    if isinstance(overlap_count, torch.Tensor):
        buffers["inter_robot_overlap_count"] += overlap_count.to(dtype=torch.float32)
        buffers["inter_robot_overlap_decisions"] += 1.0
    overlap_clearance = inter_robot_conflict.get("inter_robot_min_clearance")
    if isinstance(overlap_clearance, torch.Tensor):
        buffers["inter_robot_min_clearance"] = _nanmin(buffers["inter_robot_min_clearance"], overlap_clearance.to(dtype=torch.float32))

    actual_intersections = actual_base_motion["actual_base_motion_intersects_component"].to(dtype=torch.float32).sum(dim=1)
    buffers["actual_base_motion_intersection_count"] += actual_intersections
    buffers["actual_base_motion_decisions"] += float(num_agents)
    actual_distance = actual_base_motion["actual_base_motion_distance"].to(dtype=torch.float32)
    row_min = torch.where(torch.isfinite(actual_distance), actual_distance, torch.full_like(actual_distance, float("inf"))).min(dim=1).values
    row_min = torch.where(torch.isinf(row_min), torch.full_like(row_min, float("nan")), row_min)
    buffers["actual_base_motion_min_distance"] = _nanmin(buffers["actual_base_motion_min_distance"], row_min)


def _info_tensor(
    cooldown_info: dict[str, Any],
    key: str,
    *,
    num_envs: int,
    device: torch.device,
) -> torch.Tensor:
    value = cooldown_info.get(key)
    if isinstance(value, torch.Tensor):
        tensor = value.detach().to(device=device, dtype=torch.float32)
    elif value is None:
        tensor = torch.zeros(num_envs, dtype=torch.float32, device=device)
    else:
        tensor = torch.as_tensor(value, dtype=torch.float32, device=device)
    if tensor.numel() == 1:
        return tensor.reshape(1).expand(num_envs)
    if tensor.shape[0] != num_envs:
        return tensor.reshape(num_envs, -1).mean(dim=1)
    if tensor.ndim > 1:
        return tensor.reshape(num_envs, -1).mean(dim=1)
    return tensor


def _update_cooldown_buffers(buffers: dict[str, torch.Tensor], info: Any, *, num_envs: int, device: torch.device) -> None:
    if not isinstance(info, dict):
        return
    cooldown_info = info.get("assignment_cooldown")
    if not isinstance(cooldown_info, dict):
        return
    buffers["cooldown_trigger_count"] += _info_tensor(
        cooldown_info,
        "triggered_pair_count",
        num_envs=num_envs,
        device=device,
    )
    buffers["cooldown_active_count_sum"] += _info_tensor(
        cooldown_info,
        "active_count",
        num_envs=num_envs,
        device=device,
    )
    buffers["cooldown_suppressed_count_sum"] += _info_tensor(
        cooldown_info,
        "suppressed_action_count",
        num_envs=num_envs,
        device=device,
    )
    max_remaining = _info_tensor(cooldown_info, "max_cooldown_remaining", num_envs=num_envs, device=device)
    buffers["cooldown_max_remaining"] = torch.maximum(buffers["cooldown_max_remaining"], max_remaining)
    buffers["cooldown_step_count"] += 1.0


def _nanmin(current: torch.Tensor, candidate: torch.Tensor) -> torch.Tensor:
    current_filled = torch.nan_to_num(current, nan=float("inf"))
    candidate_filled = torch.nan_to_num(candidate, nan=float("inf"))
    result = torch.minimum(current_filled, candidate_filled)
    return torch.where(torch.isinf(result), torch.full_like(result, float("nan")), result)


def _append_assignment_history(
    rows: list[dict[str, Any]],
    *,
    method: str,
    episode: int,
    step: int,
    wrapper: Any,
    raw_ids: torch.Tensor,
    assignment: torch.Tensor,
    problem: dict[str, Any],
    covered_before: torch.Tensor,
    covered_after: torch.Tensor,
    reporting: dict[str, torch.Tensor],
    actual_base_motion: dict[str, Any],
    buffers: dict[str, torch.Tensor],
    previous_base_pos: torch.Tensor,
) -> None:
    viewpoint_pos = problem["viewpoint_pos"].to(dtype=torch.float32)
    available = problem["available_mask"].to(dtype=torch.bool)
    newly_covered = covered_after & (~covered_before)
    newly_covered_ids = _ids_from_mask(newly_covered)
    covered_before_count = covered_before.to(dtype=torch.float32).sum(dim=-1)
    covered_after_count = covered_after.to(dtype=torch.float32).sum(dim=-1)
    coverage_ratio = covered_after.to(dtype=torch.float32).mean(dim=-1)
    cooldown_active = getattr(wrapper, "_last_cooldown_active_for_selected_pair", None)
    cooldown_remaining = getattr(wrapper, "_last_cooldown_remaining_for_selected_pair", None)
    cooldown_triggered = getattr(wrapper, "_last_cooldown_triggered_after_step", None)
    cooldown_suppressed = getattr(wrapper, "_last_cooldown_suppressed_available_count_for_robot", None)
    failed_attempt_count = getattr(wrapper, "_last_failed_attempt_count_for_selected_pair", None)
    for env_id in range(wrapper.num_envs):
        for robot_id, robot_name in enumerate(wrapper.agents):
            raw_action = int(raw_ids[env_id, robot_id].item())
            selected_id = int(assignment[env_id, robot_id].item())
            is_noop = selected_id < 0
            target_x = float("nan")
            target_y = float("nan")
            if not is_noop and selected_id < wrapper.num_viewpoints:
                target_x = float(viewpoint_pos[env_id, selected_id, 0].item())
                target_y = float(viewpoint_pos[env_id, selected_id, 1].item())
            rows.append(
                {
                    "method": method,
                    "episode": int(episode),
                    "step": int(step),
                    "env_id": int(env_id),
                    "robot_id": int(robot_id),
                    "robot_name": str(robot_name),
                    "selected_action": raw_action,
                    "selected_viewpoint_id": selected_id,
                    "assigned_viewpoint_id": selected_id,
                    "is_noop": bool(is_noop),
                    "selected_available": bool(reporting["selected_available"][env_id, robot_id].item()),
                    "selected_covered_before": bool(reporting["selected_covered_before"][env_id, robot_id].item()),
                    "selected_feasible": bool(reporting["selected_feasible"][env_id, robot_id].item()),
                    "new_coverage_gain_after_step": bool(
                        (not is_noop) and selected_id < wrapper.num_viewpoints and newly_covered[env_id, selected_id].item()
                    ),
                    "coverage_ratio_after_step": float(coverage_ratio[env_id].item()),
                    "robot_base_x": float(previous_base_pos[env_id, robot_id, 0].item()),
                    "robot_base_y": float(previous_base_pos[env_id, robot_id, 1].item()),
                    "target_x": target_x,
                    "target_y": target_y,
                    "selected_path_cost": float(reporting["selected_path_cost"][env_id, robot_id].item()),
                    "duplicate_selected_target_on_step": int(compute_assignment_duplicate_count(assignment)[env_id].item()),
                    "noop_when_available": bool(reporting["noop_when_available"][env_id, robot_id].item()),
                    "same_target_streak": float(reporting["same_target_streak_next"][env_id, robot_id].item()),
                    "steps_since_global_coverage_gain": float(buffers["steps_since_gain"][env_id].item()),
                    "available_viewpoint_count": int(available[env_id, robot_id].sum().item()),
                    "covered_before_count": int(covered_before_count[env_id].item()),
                    "covered_after_count": int(covered_after_count[env_id].item()),
                    "newly_covered_viewpoint_ids": newly_covered_ids[env_id],
                    "actual_base_motion_intersects_component": bool(
                        actual_base_motion["actual_base_motion_intersects_component"][env_id, robot_id].item()
                    ),
                    "actual_base_motion_distance": float(
                        actual_base_motion["actual_base_motion_distance"][env_id, robot_id].item()
                    ),
                    "cooldown_active_for_selected_pair": bool(
                        cooldown_active is not None and cooldown_active[env_id, robot_id].item()
                    ),
                    "cooldown_remaining_for_selected_pair": int(
                        cooldown_remaining[env_id, robot_id].item() if cooldown_remaining is not None else 0
                    ),
                    "cooldown_triggered_after_step": bool(
                        cooldown_triggered is not None and cooldown_triggered[env_id, robot_id].item()
                    ),
                    "cooldown_suppressed_available_count_for_robot": int(
                        cooldown_suppressed[env_id, robot_id].item() if cooldown_suppressed is not None else 0
                    ),
                    "failed_attempt_count_for_selected_pair": int(
                        failed_attempt_count[env_id, robot_id].item() if failed_attempt_count is not None else 0
                    ),
                }
            )


def _make_episode_record(
    *,
    method: str,
    episode: int,
    env_id: int,
    checkpoint_dir: str,
    checkpoint_kind: str,
    wrapper: Any,
    buffers: dict[str, torch.Tensor],
    covered_final: torch.Tensor,
    done: bool,
) -> dict[str, Any]:
    steps = int(buffers["length"][env_id].item())
    final_coverage = float(covered_final[env_id].to(dtype=torch.float32).mean().item())
    coverage_auc = float(buffers["coverage_sum"][env_id].item() / max(1, steps))
    decision_count = max(1.0, float(buffers["decision_count"][env_id].item()))
    selected_target_decisions = max(1.0, float(buffers["selected_target_conflict_decisions"][env_id].item()))
    overlap_decisions = max(1.0, float(buffers["inter_robot_overlap_decisions"][env_id].item()))
    actual_motion_decisions = max(1.0, float(buffers["actual_base_motion_decisions"][env_id].item()))
    selected_path_cost_count = float(buffers["selected_path_cost_count"][env_id].item())
    selected_path_cost_mean = (
        float(buffers["selected_path_cost_sum"][env_id].item() / selected_path_cost_count)
        if selected_path_cost_count > 0
        else float("nan")
    )
    cooldown_steps = max(1.0, float(buffers["cooldown_step_count"][env_id].item()))
    cooldown_config = getattr(wrapper, "assignment_cooldown_config", {})
    cooldown_enabled = bool(cooldown_config.get("enabled", False)) if isinstance(cooldown_config, dict) else False
    return {
        "method": method,
        "episode": int(episode),
        "checkpoint_dir": checkpoint_dir,
        "checkpoint_kind": checkpoint_kind,
        "num_envs": wrapper.num_envs,
        "num_agents": wrapper.num_agents,
        "num_viewpoints": wrapper.num_viewpoints,
        "noop_id": wrapper.noop_action_id,
        "episode_length": int(getattr(wrapper.unwrapped, "max_episode_length", args_cli.max_steps)),
        "steps": steps,
        "done": bool(done),
        "total_return": float(buffers["return"][env_id].item()),
        "final_coverage": final_coverage,
        "coverage_auc": coverage_auc,
        "new_viewpoints_total": float(buffers["new_viewpoints_total"][env_id].item()),
        "final_uncovered_viewpoint_ids": torch.nonzero(~covered_final[env_id], as_tuple=False).flatten().detach().cpu().tolist(),
        "steps_since_last_global_coverage_gain": float(buffers["steps_since_gain"][env_id].item()),
        "no_progress_steps_after_last_gain": float(buffers["no_progress_after_last_gain"][env_id].item()),
        "late_repeated_assignment_pattern": bool(buffers["late_repeated"][env_id].item() > 0.0),
        "late_repeated_assignment_count": float(buffers["late_repeated"][env_id].item()),
        "per_viewpoint_attempted_count": _tensor_row_json(buffers["per_viewpoint_attempted"], env_id),
        "per_robot_selected_count": _tensor_row_json(buffers["per_robot_selected"], env_id, precision=4),
        "per_robot_completed_count": _tensor_row_json(buffers["per_robot_completed"], env_id, precision=4),
        "per_robot_repeated_assignment_count": _tensor_row_json(buffers["per_robot_repeated"], env_id, precision=4),
        "duplicate_selected_target_count": float(buffers["duplicate_count"][env_id].item()),
        "duplicate_selected_target_rate": float(buffers["duplicate_count"][env_id].item() / max(1, steps)),
        "noop_when_available_count": float(buffers["noop_when_available_count"][env_id].item()),
        "noop_when_available_rate": float(buffers["noop_when_available_count"][env_id].item() / decision_count),
        "valid_action_count_mean": float(buffers["valid_action_count_sum"][env_id].item() / max(1, steps)),
        "selected_available_mask_mean": float(buffers["selected_available_sum"][env_id].item() / decision_count),
        "selected_target_conflict_count": float(buffers["selected_target_conflict_count"][env_id].item()),
        "selected_target_conflict_rate": float(buffers["selected_target_conflict_count"][env_id].item() / selected_target_decisions),
        "selected_target_conflict_min_clearance": float(buffers["selected_target_conflict_min_clearance"][env_id].item()),
        "inter_robot_overlap_count": float(buffers["inter_robot_overlap_count"][env_id].item()),
        "inter_robot_overlap_rate": float(buffers["inter_robot_overlap_count"][env_id].item() / overlap_decisions),
        "inter_robot_min_clearance": float(buffers["inter_robot_min_clearance"][env_id].item()),
        "actual_base_motion_intersection_count": float(buffers["actual_base_motion_intersection_count"][env_id].item()),
        "actual_base_motion_intersection_rate": float(
            buffers["actual_base_motion_intersection_count"][env_id].item() / actual_motion_decisions
        ),
        "actual_base_motion_min_distance": float(buffers["actual_base_motion_min_distance"][env_id].item()),
        "selected_path_cost_sum": float(buffers["selected_path_cost_sum"][env_id].item()),
        "selected_path_cost_mean": selected_path_cost_mean,
        "selected_path_cost_max": float(buffers["selected_path_cost_max"][env_id].item()),
        "cooldown_enabled": bool(cooldown_enabled),
        "cooldown_trigger_count": float(buffers["cooldown_trigger_count"][env_id].item()),
        "cooldown_active_count": float(buffers["cooldown_active_count_sum"][env_id].item() / cooldown_steps),
        "cooldown_suppressed_count": float(buffers["cooldown_suppressed_count_sum"][env_id].item() / cooldown_steps),
        "max_cooldown_remaining": float(buffers["cooldown_max_remaining"][env_id].item()),
    }


def _summarize(records: list[dict[str, Any]], *, checkpoint_dir: str, checkpoint_kind: str, wrapper: Any) -> list[dict[str, Any]]:
    if not records:
        return []
    def col(name: str) -> list[float]:
        return [float(record[name]) for record in records if name in record]

    return [
        {
            "method": "rl_checkpoint",
            "checkpoint_dir": checkpoint_dir,
            "checkpoint_kind": checkpoint_kind,
            "episodes": len(records),
            "num_envs": wrapper.num_envs,
            "num_agents": wrapper.num_agents,
            "num_viewpoints": wrapper.num_viewpoints,
            "noop_id": wrapper.noop_action_id,
            "max_steps": args_cli.max_steps,
            "final_coverage_mean": _mean(col("final_coverage")),
            "final_coverage_std": _population_std(col("final_coverage")),
            "coverage_auc_mean": _mean(col("coverage_auc")),
            "coverage_auc_std": _population_std(col("coverage_auc")),
            "new_viewpoints_total_mean": _mean(col("new_viewpoints_total")),
            "duplicate_selected_target_rate_mean": _mean(col("duplicate_selected_target_rate")),
            "noop_when_available_rate_mean": _mean(col("noop_when_available_rate")),
            "selected_available_mask_mean": _mean(col("selected_available_mask_mean")),
            "selected_target_conflict_rate_mean": _mean(col("selected_target_conflict_rate")),
            "inter_robot_overlap_rate_mean": _mean(col("inter_robot_overlap_rate")),
            "actual_base_motion_intersection_rate_mean": _mean(col("actual_base_motion_intersection_rate")),
            "selected_path_cost_mean": _mean(col("selected_path_cost_mean")),
            "selected_path_cost_max": max(col("selected_path_cost_max")) if col("selected_path_cost_max") else float("nan"),
            "late_repeated_assignment_count_mean": _mean(col("late_repeated_assignment_count")),
            "cooldown_enabled": bool(any(record.get("cooldown_enabled", False) for record in records)),
            "cooldown_trigger_count_mean": _mean(col("cooldown_trigger_count")),
            "cooldown_active_count_mean": _mean(col("cooldown_active_count")),
            "cooldown_suppressed_count_mean": _mean(col("cooldown_suppressed_count")),
            "max_cooldown_remaining": max(col("max_cooldown_remaining")) if col("max_cooldown_remaining") else 0.0,
            "episode_steps_mean": _mean(col("steps")),
        }
    ]


def _extract_static_diagnostics(unwrapped: Any, problem: dict[str, Any]) -> dict[str, Any]:
    cfg = getattr(unwrapped, "cfg", None)
    component = None
    if hasattr(unwrapped, "get_component_obstacle_footprint_diagnostics"):
        component = unwrapped.get_component_obstacle_footprint_diagnostics()
    return {
        "inter_robot_conflict_diagnostics_enabled": bool(problem.get("inter_robot_conflict_diagnostics_enabled", False)),
        "inter_robot_conflict_diagnostics_mode": problem.get("inter_robot_conflict_diagnostics_mode", "disabled"),
        "inter_robot_conflict_robot_footprint_radius": _scalar_float(
            problem.get("inter_robot_conflict_robot_footprint_radius", 0.35)
        ),
        "inter_robot_conflict_safety_margin": _scalar_float(problem.get("inter_robot_conflict_safety_margin", 0.15)),
        "inter_robot_target_conflict_enabled": bool(problem.get("inter_robot_target_conflict_enabled", True)),
        "inter_robot_target_conflict_radius": _scalar_float(problem.get("inter_robot_target_conflict_radius", 0.35)),
        "inter_robot_target_conflict_safety_margin": _scalar_float(
            problem.get("inter_robot_target_conflict_safety_margin", 0.15)
        ),
        "actual_base_motion_obstacle_diagnostics_enabled": bool(
            getattr(cfg, "actual_base_motion_obstacle_diagnostics_enabled", False)
        ),
        "actual_base_motion_obstacle_diagnostics_mode": getattr(
            cfg,
            "actual_base_motion_obstacle_diagnostics_mode",
            "disabled",
        ),
        "component_obstacle_footprint_diagnostics": component,
        "proxy_diagnostics_note": (
            "Conflict, overlap, and component crossing are diagnostic proxies only. They do not alter rewards, "
            "masks, controller behavior, collision geometry, local avoidance, or path planning."
        ),
    }


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: dict[str, Any]) -> None:
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.num_episodes <= 0:
        raise ValueError("--num_episodes must be positive")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if not args_cli.assignment_rl:
        print("[INFO]: evaluate_assignment_rl_playback_diagnostics.py is assignment-only; proceeding in assignment mode.")

    model_dir = Path(args_cli.dir).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory does not exist: {model_dir}")
    output_dir = Path(args_cli.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_kind = _checkpoint_kind(model_dir)
    if checkpoint_kind == "best_model":
        print("[WARN]: best_model from pre-9D-2A runs may have polluted Total_Reward accounting. Use as a debug artifact only.")

    env_cfg.scene.num_envs = args_cli.num_envs
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    if args_cli.scenario_config is not None:
        apply_scenario_config_to_env_cfg(env_cfg, args_cli)
        print(f"[INFO]: Assignment RL playback scenario_config applied: {getattr(env_cfg, 'scenario_config_path', None)}")

    wrapper = None
    capture_state: dict[str, Any] | None = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        capture_state = _install_prereset_coverage_capture(wrapper.unwrapped)
        device = init_device(agent_cfg["device"])
        actors = _load_assignment_actors(wrapper, agent_cfg, model_dir, device)
        print(
            "[INFO]: Assignment RL playback diagnostics env "
            f"num_envs={wrapper.num_envs} num_agents={wrapper.num_agents} "
            f"num_viewpoints={wrapper.num_viewpoints} noop_id={wrapper.noop_action_id} "
            f"action_spaces={wrapper.action_space}"
        )

        if wrapper.num_viewpoints != 50 or wrapper.num_agents != 3 or wrapper.noop_action_id != 50:
            raise RuntimeError(
                "Phase 9D-2B smoke expected fixed N=50/M=3 assignment path with noop id 50, "
                f"got N={wrapper.num_viewpoints}, M={wrapper.num_agents}, noop={wrapper.noop_action_id}"
            )

        rnn_hidden_size = int(agent_cfg["model"]["hidden_sizes"][-1])
        recurrent_n = int(agent_cfg["model"]["recurrent_n"])
        all_episode_records: list[dict[str, Any]] = []
        assignment_history_rows: list[dict[str, Any]] = []
        static_diagnostics: dict[str, Any] | None = None
        last_covered_final: torch.Tensor | None = None

        for episode in range(args_cli.num_episodes):
            reset_kwargs = {"seed": int(args_cli.seed) + episode} if args_cli.seed is not None else {}
            obs, _, available_actions = wrapper.reset(**reset_kwargs)
            _assert_available_actions(wrapper, available_actions)
            problem = wrapper.unwrapped.get_assignment_problem()
            if static_diagnostics is None:
                static_diagnostics = _extract_static_diagnostics(wrapper.unwrapped, problem)

            actions = make_harl_action_tensor(wrapper.num_envs, wrapper.action_space, device=wrapper.device)
            rnn_states = torch.zeros(
                (wrapper.num_envs, wrapper.num_agents, recurrent_n, rnn_hidden_size),
                dtype=torch.float32,
                device=device,
            )
            masks = torch.ones((wrapper.num_envs, wrapper.num_agents, 1), dtype=torch.float32, device=device)
            buffers = _init_buffers(wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints, wrapper.device)
            episode_records_written: set[int] = set()
            done_any = False
            covered_final = wrapper.unwrapped.viewpoints_covered.detach().clone().to(dtype=torch.bool)

            for step_id in range(1, args_cli.max_steps + 1):
                _assert_available_actions(wrapper, available_actions)
                pre_problem = wrapper.unwrapped.get_assignment_problem()
                covered_before = wrapper.unwrapped.viewpoints_covered.detach().clone().to(dtype=torch.bool)
                previous_base_pos = wrapper.unwrapped.base_pos.detach().clone()
                actions.zero_()

                with torch.inference_mode():
                    for agent_id, agent_name in enumerate(wrapper.agents):
                        agent_obs = obs[agent_name].to(device=device)
                        agent_available_actions = available_actions[:, agent_id, :].to(device=device)
                        agent_rnn_states = rnn_states[:, agent_id].clone()
                        agent_masks = masks[:, agent_id]
                        action, rnn_state = actors[agent_id].act(
                            agent_obs,
                            agent_rnn_states,
                            agent_masks,
                            agent_available_actions,
                            deterministic=True,
                        )
                        action_width = action.shape[-1]
                        actions[:, agent_id, :action_width] = action.to(device=actions.device)
                        rnn_states[:, agent_id] = rnn_state

                raw_ids = actions[..., 0].to(dtype=torch.long)
                assignment = _decode_actions(raw_ids, wrapper.noop_action_id)
                reporting = _assignment_reporting_step(buffers, pre_problem, assignment)
                selected_target_conflict = _selected_target_conflict_diagnostics(
                    pre_problem,
                    assignment,
                    torch.arange(wrapper.num_viewpoints, device=wrapper.device, dtype=torch.long),
                )

                obs, _, rewards, dones, info, available_actions = wrapper.step(actions)
                _assert_available_actions(wrapper, available_actions)
                done_envs = torch.all(dones, dim=1)
                current_base_pos = wrapper.unwrapped.base_pos.detach().clone()
                covered_after = _coverage_from_env(wrapper.unwrapped, done_envs, capture_state)
                inter_robot_conflict = wrapper.unwrapped.get_inter_robot_conflict_diagnostics()
                actual_base_motion = _actual_base_motion_step_diagnostics(
                    wrapper.unwrapped,
                    previous_base_pos=previous_base_pos,
                    current_base_pos=current_base_pos,
                    assignment=assignment,
                )

                _update_buffers(
                    buffers,
                    rewards=rewards,
                    assignment=assignment,
                    pre_problem=pre_problem,
                    covered_before=covered_before,
                    covered_after=covered_after,
                    reporting=reporting,
                    selected_target_conflict=selected_target_conflict,
                    inter_robot_conflict=inter_robot_conflict,
                    actual_base_motion=actual_base_motion,
                )
                _update_cooldown_buffers(
                    buffers,
                    info,
                    num_envs=wrapper.num_envs,
                    device=wrapper.device,
                )
                _append_assignment_history(
                    assignment_history_rows,
                    method="rl_checkpoint",
                    episode=episode,
                    step=step_id,
                    wrapper=wrapper,
                    raw_ids=raw_ids,
                    assignment=assignment,
                    problem=pre_problem,
                    covered_before=covered_before,
                    covered_after=covered_after,
                    reporting=reporting,
                    actual_base_motion=actual_base_motion,
                    buffers=buffers,
                    previous_base_pos=previous_base_pos,
                )
                covered_final = covered_after
                last_covered_final = covered_final.detach().clone()

                if bool(done_envs.any()):
                    done_any = True
                    for env_id in torch.nonzero(done_envs, as_tuple=False).flatten().detach().cpu().tolist():
                        if int(env_id) in episode_records_written:
                            continue
                        all_episode_records.append(
                            _make_episode_record(
                                method="rl_checkpoint",
                                episode=episode,
                                env_id=int(env_id),
                                checkpoint_dir=str(model_dir),
                                checkpoint_kind=checkpoint_kind,
                                wrapper=wrapper,
                                buffers=buffers,
                                covered_final=covered_final,
                                done=True,
                            )
                        )
                        episode_records_written.add(int(env_id))
                    if args_cli.stop_on_done:
                        print(f"[OK]: episode {episode} completed at step {step_id}; stop_on_done set")
                        break

                masks.fill_(1.0)
                if bool(done_envs.any()):
                    masks[done_envs] = 0.0
                    rnn_states[done_envs] = 0.0

            if len(episode_records_written) < wrapper.num_envs:
                for env_id in range(wrapper.num_envs):
                    if env_id in episode_records_written:
                        continue
                    all_episode_records.append(
                        _make_episode_record(
                            method="rl_checkpoint",
                            episode=episode,
                            env_id=env_id,
                            checkpoint_dir=str(model_dir),
                            checkpoint_kind=checkpoint_kind,
                            wrapper=wrapper,
                            buffers=buffers,
                            covered_final=covered_final,
                            done=done_any,
                        )
                    )
                    episode_records_written.add(env_id)

        summary_rows = _summarize(all_episode_records, checkpoint_dir=str(model_dir), checkpoint_kind=checkpoint_kind, wrapper=wrapper)
        diagnostics = {
            "metadata": {
                "method": "rl_checkpoint",
                "checkpoint_dir": str(model_dir),
                "checkpoint_kind": checkpoint_kind,
                "exp_name": _exp_name_from_checkpoint(model_dir),
                "task": args_cli.task,
                "algorithm": ALGORITHM,
                "assignment_rl": True,
                "scenario_config": str(getattr(env_cfg, "scenario_config_path", args_cli.scenario_config)),
                "num_episodes": args_cli.num_episodes,
                "max_steps": args_cli.max_steps,
                "num_envs": wrapper.num_envs,
                "num_agents": wrapper.num_agents,
                "num_viewpoints": wrapper.num_viewpoints,
                "noop_id": wrapper.noop_action_id,
                "episode_length": int(getattr(wrapper.unwrapped, "max_episode_length", args_cli.max_steps)),
                "device": str(getattr(args_cli, "device", agent_cfg.get("device", "unknown"))),
                "available_actions_shape": [wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1],
                "action_space": {str(agent_id): str(space) for agent_id, space in wrapper.action_space.items()},
                "observation_layout": wrapper.assignment_observation_layout,
                "assignment_cooldown_config": wrapper.assignment_cooldown_config,
            },
            "static_diagnostics": static_diagnostics or {},
            "summary": summary_rows,
            "episodes": all_episode_records,
            "history_row_count": len(assignment_history_rows),
            "outputs": {
                "diagnostics_json": str(output_dir / "diagnostics.json"),
                "summary_csv": str(output_dir / "summary.csv"),
                "per_episode_csv": str(output_dir / "per_episode.csv"),
                "assignment_history_csv": str(output_dir / "assignment_history.csv"),
            },
            "capture_state": {
                "prereset_coverage_capture_installed": bool((capture_state or {}).get("installed", False)),
                "last_error": (capture_state or {}).get("last_error"),
            },
        }
        if last_covered_final is not None:
            diagnostics["final_uncovered_viewpoint_ids_by_env"] = _ids_from_mask(~last_covered_final)

        _write_json(output_dir / "diagnostics.json", diagnostics)
        _write_csv(output_dir / "summary.csv", summary_rows, SUMMARY_FIELDS)
        _write_csv(output_dir / "per_episode.csv", all_episode_records, PER_EPISODE_FIELDS)
        _write_csv(output_dir / "assignment_history.csv", assignment_history_rows, ASSIGNMENT_HISTORY_FIELDS)
        print(f"[OK]: wrote diagnostics to {output_dir}")
    finally:
        if wrapper is not None:
            if capture_state is not None:
                _restore_prereset_coverage_capture(wrapper.unwrapped, capture_state)
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
