# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate high-level viewpoint assignment solvers on the scan mobile manipulator task."""

"""Launch Isaac Sim Simulator first."""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Evaluate scan viewpoint assignment solvers.")
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
parser.add_argument("--solver", type=str, default="greedy", choices=("random", "nearest", "greedy"), help="Solver name.")
parser.add_argument("--num_envs", type=int, default=2, help="Number of environments to simulate.")
parser.add_argument(
    "--num_episodes_per_env",
    type=int,
    default=None,
    help="Number of complete episode records to collect per vectorized environment.",
)
parser.add_argument(
    "--num_episodes",
    type=int,
    default=None,
    help="Deprecated: total number of vector-env episode records to collect.",
)
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--max_steps_per_episode", type=int, default=None, help="Optional script-level episode step cap.")
parser.add_argument("--save_csv", type=str, default=None, help="Optional path to write per-episode CSV results.")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import csv
import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions
from isaaclab_tasks.direct.scan_mobile_manipulator.solvers import make_solver
from isaaclab_tasks.utils import parse_env_cfg


def _as_bool_tensor(value, num_envs: int, device: torch.device) -> torch.Tensor:
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


def _set_global_seeds(seed: int | None):
    if seed is None:
        return
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _aggregate_done(done, agents: list[str], num_envs: int, device: torch.device) -> torch.Tensor:
    if isinstance(done, torch.Tensor):
        return _as_bool_tensor(done, num_envs, device)
    if "__all__" in done:
        return _as_bool_tensor(done["__all__"], num_envs, device)

    values = [_as_bool_tensor(done[agent], num_envs, device) for agent in agents if agent in done]
    if not values:
        return torch.zeros(num_envs, dtype=torch.bool, device=device)
    return torch.stack(values, dim=0).all(dim=0)


def _sum_rewards(rewards: dict[str, torch.Tensor], agents: list[str], num_envs: int, device: torch.device) -> torch.Tensor:
    values = [rewards[agent].to(device=device).reshape(num_envs) for agent in agents if agent in rewards]
    if not values:
        return torch.zeros(num_envs, dtype=torch.float32, device=device)
    return torch.stack(values, dim=0).sum(dim=0)


def _action_stack(actions: dict[str, torch.Tensor], agents: list[str], num_envs: int, device: torch.device) -> torch.Tensor:
    values = [actions[agent].to(device=device).reshape(num_envs, -1) for agent in agents]
    return torch.stack(values, dim=1)


def _assignment_duplicate_count(assignment: torch.Tensor) -> torch.Tensor:
    duplicates = torch.zeros(assignment.shape[0], dtype=torch.float32, device=assignment.device)
    for env_id in range(assignment.shape[0]):
        selected = assignment[env_id][assignment[env_id] >= 0]
        if selected.numel() == 0:
            continue
        duplicates[env_id] = float(selected.numel() - torch.unique(selected).numel())
    return duplicates


def _validate_assignment(problem: dict, assignment: torch.Tensor):
    expected_shape = (problem["num_envs"], problem["num_agents"])
    if tuple(assignment.shape) != expected_shape:
        raise RuntimeError(f"assignment shape mismatch: expected {expected_shape}, got {tuple(assignment.shape)}")
    if assignment.dtype != torch.long:
        raise RuntimeError(f"assignment dtype mismatch: expected torch.long, got {assignment.dtype}")
    if assignment.device != problem["available_mask"].device:
        raise RuntimeError(
            f"assignment device mismatch: expected {problem['available_mask'].device}, got {assignment.device}"
        )
    if torch.any(assignment < -1) or torch.any(assignment >= problem["num_viewpoints"]):
        raise RuntimeError("assignment contains values outside [-1, num_viewpoints)")

    for env_id in range(problem["num_envs"]):
        for agent_id in range(problem["num_agents"]):
            viewpoint_id = int(assignment[env_id, agent_id].item())
            if viewpoint_id >= 0 and not bool(problem["available_mask"][env_id, agent_id, viewpoint_id].item()):
                raise RuntimeError(
                    f"solver selected unavailable viewpoint {viewpoint_id} for env {env_id}, agent {agent_id}"
                )


def _validate_actions(env, actions: dict[str, torch.Tensor]):
    expected_device = torch.device(env.device)
    expected_agents = set(env.possible_agents)
    if set(actions.keys()) != expected_agents:
        raise RuntimeError(f"action keys mismatch: expected {sorted(expected_agents)}, got {sorted(actions.keys())}")

    for agent in env.possible_agents:
        expected_shape = (env.num_envs, *env.action_spaces[agent].shape)
        action = actions[agent]
        if tuple(action.shape) != expected_shape:
            raise RuntimeError(f"{agent} action shape mismatch: expected {expected_shape}, got {tuple(action.shape)}")
        if action.device != expected_device:
            raise RuntimeError(f"{agent} action device mismatch: expected {expected_device}, got {action.device}")
        if not torch.isfinite(action).all():
            raise RuntimeError(f"{agent} action contains non-finite values")
        if torch.any(action < -1.0) or torch.any(action > 1.0):
            raise RuntimeError(f"{agent} action contains values outside [-1, 1]")


def _make_record(
    episode_id: int,
    solver_name: str,
    env_id: int,
    success: torch.Tensor,
    coverage: torch.Tensor,
    episode_lengths: torch.Tensor,
    total_reward: torch.Tensor,
    assignment_duplicate_count: torch.Tensor,
    scan_duplicate_count: torch.Tensor,
    reach_violation_count: torch.Tensor,
    steps_to_50: torch.Tensor,
    steps_to_80: torch.Tensor,
    coverage_auc: torch.Tensor,
    robot_coverage_gain: torch.Tensor,
    action_norm_sum: torch.Tensor,
    action_delta_sum: torch.Tensor,
    action_delta_count: torch.Tensor,
) -> dict:
    episode_length = int(episode_lengths[env_id].item())
    coverage_auc_value = 0.0
    mean_action_norm = 0.0
    mean_action_delta = 0.0
    if episode_length > 0:
        coverage_auc_value = float((coverage_auc[env_id] / episode_lengths[env_id]).item())
        mean_action_norm = float((action_norm_sum[env_id] / episode_lengths[env_id]).item())
    if int(action_delta_count[env_id].item()) > 0:
        mean_action_delta = float((action_delta_sum[env_id] / action_delta_count[env_id]).item())

    record = {
        "episode_id": episode_id,
        "solver": solver_name,
        "env_id": env_id,
        "coverage_ratio": float(coverage[env_id].item()),
        "success": int(success[env_id].item()),
        "episode_length": episode_length,
        "total_reward": float(total_reward[env_id].item()),
        "assignment_duplicate_count": float(assignment_duplicate_count[env_id].item()),
        "scan_duplicate_count": float(scan_duplicate_count[env_id].item()),
        "reach_violation_count": float(reach_violation_count[env_id].item()),
        "steps_to_50_coverage": int(steps_to_50[env_id].item()),
        "steps_to_80_coverage": int(steps_to_80[env_id].item()),
        "coverage_auc": coverage_auc_value,
        "mean_action_norm": mean_action_norm,
        "mean_action_delta": mean_action_delta,
    }
    for agent_id in range(robot_coverage_gain.shape[1]):
        record[f"robot_{agent_id}_coverage_gain"] = float(robot_coverage_gain[env_id, agent_id].item())
    return record


def _summarize(records: list[dict], num_agents: int) -> dict:
    if not records:
        return {}

    count = float(len(records))
    steps_to_50_reached = [record["steps_to_50_coverage"] for record in records if record["steps_to_50_coverage"] >= 0]
    steps_to_80_reached = [record["steps_to_80_coverage"] for record in records if record["steps_to_80_coverage"] >= 0]
    mean_steps_to_50 = sum(steps_to_50_reached) / len(steps_to_50_reached) if steps_to_50_reached else None
    mean_steps_to_80 = sum(steps_to_80_reached) / len(steps_to_80_reached) if steps_to_80_reached else None

    summary = {
        "episodes": len(records),
        "mean_coverage_ratio": sum(record["coverage_ratio"] for record in records) / count,
        "success_rate": sum(record["success"] for record in records) / count,
        "mean_episode_length": sum(record["episode_length"] for record in records) / count,
        "mean_total_reward": sum(record["total_reward"] for record in records) / count,
        "mean_assignment_duplicate_count": sum(record["assignment_duplicate_count"] for record in records) / count,
        "mean_scan_duplicate_count": sum(record["scan_duplicate_count"] for record in records) / count,
        "mean_reach_violation": sum(record["reach_violation_count"] for record in records) / count,
        "mean_steps_to_50_coverage": mean_steps_to_50,
        "mean_steps_to_50_coverage_reached_only": mean_steps_to_50,
        "steps_to_50_coverage_reach_rate": len(steps_to_50_reached) / count,
        "mean_steps_to_80_coverage": mean_steps_to_80,
        "mean_steps_to_80_coverage_reached_only": mean_steps_to_80,
        "steps_to_80_coverage_reach_rate": len(steps_to_80_reached) / count,
        "mean_coverage_auc": sum(record["coverage_auc"] for record in records) / count,
        "mean_action_norm": sum(record["mean_action_norm"] for record in records) / count,
        "mean_action_delta": sum(record["mean_action_delta"] for record in records) / count,
    }
    summary["mean_per_robot_coverage_gain"] = [
        sum(record[f"robot_{agent_id}_coverage_gain"] for record in records) / count for agent_id in range(num_agents)
    ]
    return summary


def _write_csv(path: str, records: list[dict], num_agents: int):
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "episode_id",
        "solver",
        "env_id",
        "coverage_ratio",
        "success",
        "episode_length",
        "total_reward",
        "assignment_duplicate_count",
        "scan_duplicate_count",
        "reach_violation_count",
        "steps_to_50_coverage",
        "steps_to_80_coverage",
        "coverage_auc",
        "mean_action_norm",
        "mean_action_delta",
        *[f"robot_{agent_id}_coverage_gain" for agent_id in range(num_agents)],
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"[INFO]: Wrote CSV results to: {csv_path}")


def main():
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.num_episodes_per_env is not None and args_cli.num_episodes_per_env <= 0:
        raise ValueError("--num_episodes_per_env must be positive when provided")
    if args_cli.num_episodes is not None and args_cli.num_episodes <= 0:
        raise ValueError("--num_episodes must be positive when provided")

    if args_cli.num_episodes_per_env is None:
        if args_cli.num_episodes is None:
            target_records = args_cli.num_envs
            num_episodes_per_env_text = "1"
        else:
            target_records = args_cli.num_episodes
            num_episodes_per_env_text = "deprecated-total-records"
            print(
                "[WARN]: --num_episodes is deprecated and means total vector-env episode records. "
                "Use --num_episodes_per_env for per-environment collection."
            )
    else:
        target_records = args_cli.num_envs * args_cli.num_episodes_per_env
        num_episodes_per_env_text = str(args_cli.num_episodes_per_env)

    _set_global_seeds(args_cli.seed)
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed

    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    solver = make_solver(args_cli.solver)
    env.reset(seed=args_cli.seed)

    device = torch.device(unwrapped.device)
    agents = list(unwrapped.possible_agents)
    num_envs = unwrapped.num_envs
    num_agents = len(agents)
    max_steps = args_cli.max_steps_per_episode
    if max_steps is None:
        max_steps = int(unwrapped.max_episode_length)
    if max_steps <= 0:
        raise ValueError("--max_steps_per_episode must be positive when provided")

    episode_lengths = torch.zeros(num_envs, dtype=torch.long, device=device)
    total_reward = torch.zeros(num_envs, dtype=torch.float32, device=device)
    assignment_duplicate_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
    scan_duplicate_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
    reach_violation_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
    steps_to_50 = torch.full((num_envs,), -1, dtype=torch.long, device=device)
    steps_to_80 = torch.full((num_envs,), -1, dtype=torch.long, device=device)
    coverage_auc = torch.zeros(num_envs, dtype=torch.float32, device=device)
    max_coverage = torch.zeros(num_envs, dtype=torch.float32, device=device)
    robot_coverage_gain = torch.zeros(num_envs, num_agents, dtype=torch.float32, device=device)
    action_norm_sum = torch.zeros(num_envs, dtype=torch.float32, device=device)
    action_delta_sum = torch.zeros(num_envs, dtype=torch.float32, device=device)
    action_delta_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
    previous_actions = torch.zeros(num_envs, num_agents, 0, dtype=torch.float32, device=device)
    has_previous_action = torch.zeros(num_envs, dtype=torch.bool, device=device)

    records = []
    print(
        f"[INFO]: Evaluating solver={args_cli.solver} task={args_cli.task} "
        f"num_envs={num_envs} num_episodes_per_env={num_episodes_per_env_text} "
        f"target_episode_records={target_records} max_steps_per_episode={max_steps}"
    )

    with torch.inference_mode():
        while simulation_app.is_running() and len(records) < target_records:
            problem = unwrapped.get_assignment_problem()
            pre_coverage = problem["viewpoints_covered"].float().mean(dim=-1)

            assignment = solver.solve(problem)
            _validate_assignment(problem, assignment)

            actions = viewpoint_assignment_to_actions(unwrapped, assignment)
            _validate_actions(unwrapped, actions)
            stacked_actions = _action_stack(actions, agents, num_envs, device)

            _, rewards, terminated, truncated, _ = env.step(actions)

            episode_lengths += 1
            total_reward += _sum_rewards(rewards, agents, num_envs, device)
            assignment_duplicate_count += _assignment_duplicate_count(assignment)
            action_norm_sum += torch.linalg.norm(stacked_actions, dim=-1).mean(dim=1)
            if previous_actions.shape[-1] == 0:
                previous_actions = torch.zeros_like(stacked_actions)
            action_delta = torch.linalg.norm(stacked_actions - previous_actions, dim=-1).mean(dim=1)
            action_delta_sum += torch.where(has_previous_action, action_delta, torch.zeros_like(action_delta))
            action_delta_count += has_previous_action.float()
            previous_actions = stacked_actions.clone()
            has_previous_action[:] = True

            if hasattr(unwrapped, "last_duplicate_scans"):
                scan_duplicate_count += unwrapped.last_duplicate_scans.sum(dim=1)
            if hasattr(unwrapped, "last_reach_violation"):
                reach_violation_count += unwrapped.last_reach_violation.sum(dim=1)
            if hasattr(unwrapped, "last_own_coverage_gain"):
                robot_coverage_gain += unwrapped.last_own_coverage_gain

            terminated_tensor = _aggregate_done(terminated, agents, num_envs, device)
            truncated_tensor = _aggregate_done(truncated, agents, num_envs, device)
            env_done = terminated_tensor | truncated_tensor
            script_done = episode_lengths >= max_steps
            done = env_done | script_done

            post_coverage = unwrapped.viewpoints_covered.float().mean(dim=-1)
            # DirectMARLEnv can reset completed envs before control returns here. For env-level timeout/truncation,
            # pre-step coverage is the last stable value; true termination means the task reached full coverage.
            step_coverage = torch.where(env_done & (~terminated_tensor), pre_coverage, post_coverage)
            step_coverage = torch.where(terminated_tensor, torch.ones_like(step_coverage), step_coverage)
            max_coverage = torch.maximum(max_coverage, step_coverage)
            coverage_auc += step_coverage

            hit_50 = (steps_to_50 < 0) & (step_coverage >= 0.5)
            steps_to_50[hit_50] = episode_lengths[hit_50]
            hit_80 = (steps_to_80 < 0) & (step_coverage >= 0.8)
            steps_to_80[hit_80] = episode_lengths[hit_80]

            done_ids = torch.nonzero(done, as_tuple=False).flatten()
            if done_ids.numel() == 0:
                continue

            remaining = target_records - len(records)
            for env_id_tensor in done_ids[:remaining]:
                env_id = int(env_id_tensor.item())
                records.append(
                    _make_record(
                        len(records),
                        args_cli.solver,
                        env_id,
                        terminated_tensor,
                        max_coverage,
                        episode_lengths,
                        total_reward,
                        assignment_duplicate_count,
                        scan_duplicate_count,
                        reach_violation_count,
                        steps_to_50,
                        steps_to_80,
                        coverage_auc,
                        robot_coverage_gain,
                        action_norm_sum,
                        action_delta_sum,
                        action_delta_count,
                    )
                )

            manual_reset = script_done & (~env_done)
            manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
            if manual_reset_ids.numel() > 0:
                unwrapped._reset_idx(manual_reset_ids)

            episode_lengths[done_ids] = 0
            total_reward[done_ids] = 0.0
            assignment_duplicate_count[done_ids] = 0.0
            scan_duplicate_count[done_ids] = 0.0
            reach_violation_count[done_ids] = 0.0
            steps_to_50[done_ids] = -1
            steps_to_80[done_ids] = -1
            coverage_auc[done_ids] = 0.0
            max_coverage[done_ids] = 0.0
            robot_coverage_gain[done_ids] = 0.0
            action_norm_sum[done_ids] = 0.0
            action_delta_sum[done_ids] = 0.0
            action_delta_count[done_ids] = 0.0
            has_previous_action[done_ids] = False
            previous_actions[done_ids] = 0.0
            # Current assignment baselines are stateless; keep a full reset for compatibility.
            solver.reset()

    summary = _summarize(records, num_agents)
    if not summary:
        print("[WARN]: No completed episodes were collected.")
    else:
        print("[RESULT]: Scan assignment evaluation summary")
        for key, value in summary.items():
            print(f"{key}: {value}")

    if args_cli.save_csv is not None:
        _write_csv(args_cli.save_csv, records, num_agents)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
