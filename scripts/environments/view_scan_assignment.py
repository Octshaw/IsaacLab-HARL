# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""View high-level scan viewpoint assignment behavior in Isaac Sim."""

"""Launch Isaac Sim Simulator first."""

import argparse
import time

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Viewer for scan viewpoint assignment solvers.")
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
parser.add_argument("--solver", type=str, default="greedy", choices=("random", "nearest", "greedy"), help="Solver name.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--duration", type=float, default=None, help="Optional viewer duration in seconds.")
parser.add_argument("--max_steps", type=int, default=None, help="Optional maximum number of viewer steps.")
parser.add_argument("--step_rate", type=float, default=5.0, help="Environment steps per second.")
parser.add_argument("--print_interval", type=int, default=1, help="Print every N environment steps.")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions
from isaaclab_tasks.direct.scan_mobile_manipulator.solvers import make_solver
from isaaclab_tasks.utils import parse_env_cfg


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


def main():
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.max_steps is not None and args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive when provided")
    if args_cli.print_interval <= 0:
        raise ValueError("--print_interval must be positive")

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

    print(f"[INFO]: Agents: {unwrapped.possible_agents}")
    print(f"[INFO]: Observation spaces: {unwrapped.observation_spaces}")
    print(f"[INFO]: Action spaces: {unwrapped.action_spaces}")
    print(
        f"[INFO]: Viewing solver={args_cli.solver} task={args_cli.task} "
        f"num_envs={unwrapped.num_envs} step_rate={args_cli.step_rate}"
    )
    print("[INFO]: Close Isaac Sim to stop.")

    env.reset(seed=args_cli.seed)
    start_time = time.time()
    step_count = 0
    min_step_dt = 0.0 if args_cli.step_rate <= 0 else 1.0 / args_cli.step_rate

    with torch.inference_mode():
        while simulation_app.is_running():
            if args_cli.duration is not None and time.time() - start_time >= args_cli.duration:
                break
            if args_cli.max_steps is not None and step_count >= args_cli.max_steps:
                break

            step_start = time.time()
            problem = unwrapped.get_assignment_problem()
            assignment = solver.solve(problem)
            _validate_assignment(problem, assignment)

            actions = viewpoint_assignment_to_actions(unwrapped, assignment)
            _validate_actions(unwrapped, actions)

            env.step(actions)
            step_count += 1

            if step_count % args_cli.print_interval == 0:
                coverage = unwrapped.viewpoints_covered.float().mean(dim=-1).detach().cpu().tolist()
                assignment_list = assignment.detach().cpu().tolist()
                print(f"step={step_count} coverage_ratio={coverage} assignment={assignment_list}", flush=True)

            elapsed = time.time() - step_start
            if elapsed < min_step_dt:
                time.sleep(min_step_dt - elapsed)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
