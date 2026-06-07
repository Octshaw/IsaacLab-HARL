# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""View a DirectMARLEnv task with random or zero actions.

This is a lightweight viewer/debug helper. It is meant for inspecting custom multi-agent
direct environments without starting a full RL training run.
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import time

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Viewer for Isaac Lab DirectMARLEnv tasks.")
parser.add_argument("--task", type=str, required=True, help="Name of the task.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--duration", type=float, default=None, help="Optional viewer duration in seconds.")
parser.add_argument("--step_rate", type=float, default=20.0, help="Environment steps per second.")
parser.add_argument("--zero_actions", action="store_true", help="Use zero actions instead of random actions.")
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
from isaaclab.envs import DirectMARLEnv
from isaaclab_tasks.utils import parse_env_cfg


def _sample_actions(env: DirectMARLEnv, zero_actions: bool) -> dict[str, torch.Tensor]:
    """Build a MARL action dictionary with one tensor per agent."""
    actions = {}
    for agent in env.possible_agents:
        action_shape = env.action_spaces[agent].shape
        if zero_actions:
            actions[agent] = torch.zeros((env.num_envs, *action_shape), device=env.device)
        else:
            actions[agent] = 2.0 * torch.rand((env.num_envs, *action_shape), device=env.device) - 1.0
    return actions


def main():
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    if not isinstance(unwrapped, DirectMARLEnv):
        raise TypeError(f"Task '{args_cli.task}' is not a DirectMARLEnv. Received: {type(unwrapped)}")

    print(f"[INFO]: Agents: {unwrapped.possible_agents}")
    print(f"[INFO]: Observation spaces: {unwrapped.observation_spaces}")
    print(f"[INFO]: Action spaces: {unwrapped.action_spaces}")
    print("[INFO]: Viewer is running. Close Isaac Sim to stop.")

    env.reset()
    start_time = time.time()

    # Limit the stepping speed so GUI inspection does not finish in a flash.
    min_step_dt = 0.0 if args_cli.step_rate <= 0 else 1.0 / args_cli.step_rate

    while simulation_app.is_running():
        if args_cli.duration is not None and time.time() - start_time >= args_cli.duration:
            break
        step_start = time.time()
        with torch.inference_mode():
            env.step(_sample_actions(unwrapped, args_cli.zero_actions))
        elapsed = time.time() - step_start
        if elapsed < min_step_dt:
            time.sleep(min_step_dt - elapsed)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
