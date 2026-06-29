# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""No-training readiness smoke for assignment HARL train-entry plumbing."""

"""Launch Isaac Sim Simulator first."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

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

from scenario_config import (
    apply_scenario_config_to_env_cfg,
    load_scenario_config,
    smoke_defaults_from_config,
    validate_smoke_args,
)

from isaaclab.app import AppLauncher

pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="No-training assignment HARL training-entry readiness smoke.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Task name.")
parser.add_argument("--algorithm", type=str, default="happo", choices=("happo", "hatrpo", "haa2c"))
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--assignment_episode_length", type=int, default=None, help="Assignment train.episode_length override.")
parser.add_argument("--result_file", type=str, default=None, help="Optional JSON result file.")
parser.add_argument("--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O.")
AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli = parser.parse_args()
validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_training import (
    ASSIGNMENT_REWARD_LOG_FIELDS,
    AssignmentIsaacLabEnv,
    apply_assignment_episode_length_override,
)
from isaaclab_tasks.utils import parse_env_cfg


def _load_agent_cfg(algorithm: str) -> dict[str, Any]:
    cfg_path = SCAN_TASK_SOURCE / "agents" / f"harl_{algorithm}_cfg.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No task-local HARL config found for algorithm={algorithm!r}: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict) or "train" not in data:
        raise ValueError(f"Invalid HARL config: {cfg_path}")
    return data


def _first_available_action_tensor(wrapper, available_actions: torch.Tensor) -> torch.Tensor:
    actions = wrapper.make_action_tensor()
    available_bool = available_actions.to(dtype=torch.bool)
    for env_id in range(wrapper.num_envs):
        for agent_id in range(wrapper.num_agents):
            viewpoint_ids = torch.nonzero(
                available_bool[env_id, agent_id, : wrapper.num_viewpoints],
                as_tuple=False,
            ).flatten()
            if viewpoint_ids.numel() > 0:
                selected_id = int(viewpoint_ids[0].item())
            else:
                selected_id = int(wrapper.noop_action_id)
            actions[env_id, agent_id, 0] = float(selected_id)
    return actions


def _assert_shapes(env: AssignmentIsaacLabEnv, obs: dict[str, torch.Tensor], shared_obs: torch.Tensor, available_actions: torch.Tensor) -> dict[str, Any]:
    wrapper = env.assignment_env
    if env.num_agents != 3:
        raise AssertionError(f"expected 3 agents, got {env.num_agents}")
    if env.num_viewpoints != 50:
        raise AssertionError(f"expected 50 viewpoints, got {env.num_viewpoints}")
    if env.noop_action_id != 50:
        raise AssertionError(f"expected noop id 50, got {env.noop_action_id}")

    actor_shapes = {}
    for agent_name in wrapper.agents:
        agent_obs = obs[agent_name]
        if tuple(agent_obs.shape) != (env.n_envs, 909):
            raise AssertionError(f"{agent_name} obs shape mismatch: got {tuple(agent_obs.shape)}")
        if not torch.isfinite(agent_obs).all():
            raise AssertionError(f"{agent_name} obs contains non-finite values")
        actor_shapes[agent_name] = list(agent_obs.shape)
    if tuple(shared_obs.shape) != (env.n_envs, env.num_agents, 2727):
        raise AssertionError(f"shared obs shape mismatch: got {tuple(shared_obs.shape)}")
    if tuple(available_actions.shape) != (env.n_envs, env.num_agents, env.num_viewpoints + 1):
        raise AssertionError(f"available_actions shape mismatch: got {tuple(available_actions.shape)}")
    problem = env.unwrapped.get_assignment_problem()
    available_mask = problem["available_mask"]
    if tuple(available_mask.shape) != (env.n_envs, env.num_agents, env.num_viewpoints):
        raise AssertionError(f"available_mask shape mismatch: got {tuple(available_mask.shape)}")
    return {
        "actor_observation_shape": list(next(iter(actor_shapes.values()))),
        "actor_observation_shape_by_agent": actor_shapes,
        "shared_observation_shape": list(shared_obs.shape),
        "available_actions_shape": list(available_actions.shape),
        "available_mask_shape": list(available_mask.shape),
    }


def main() -> None:
    if args_cli.num_envs != 1:
        raise ValueError("Phase 9C-2 readiness smoke currently expects --num_envs 1")
    if args_cli.assignment_episode_length is None:
        raise ValueError("--assignment_episode_length is required for this readiness smoke")

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    apply_scenario_config_to_env_cfg(env_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs

    agent_cfg = _load_agent_cfg(args_cli.algorithm)
    episode_length_default = int(agent_cfg["train"]["episode_length"])
    applied_episode_length = apply_assignment_episode_length_override(agent_cfg, args_cli.assignment_episode_length)
    if applied_episode_length != int(args_cli.assignment_episode_length):
        raise AssertionError("assignment episode length override was not applied")

    env = None
    try:
        env = AssignmentIsaacLabEnv(
            {
                "n_threads": args_cli.num_envs,
                "task": args_cli.task,
                "config": env_cfg,
                "assignment_rl": True,
                "video_settings": {"video": False},
            }
        )
        obs, shared_obs, available_actions = env.reset()
        shape_result = _assert_shapes(env, obs, shared_obs, available_actions)
        actions = _first_available_action_tensor(env.assignment_env, available_actions)
        obs, shared_obs, rewards, dones, infos, available_actions = env.step(actions)
        shape_result = _assert_shapes(env, obs, shared_obs, available_actions)
        if not torch.isfinite(rewards).all():
            raise AssertionError("reward tensor contains non-finite values")

        expected_reward_log_keys = [
            f"assignment_rl_reward/{key}_mean"
            for key in ASSIGNMENT_REWARD_LOG_FIELDS
        ]
        present_reward_log_keys = [
            key for key in expected_reward_log_keys
            if key in env.log_info
        ]
        if len(present_reward_log_keys) != len(expected_reward_log_keys):
            missing = sorted(set(expected_reward_log_keys) - set(present_reward_log_keys))
            raise AssertionError(f"missing assignment_rl_reward log keys: {missing}")

        scenario_path = getattr(env.unwrapped.cfg, "scenario_config_path", None)
        result = {
            "task": args_cli.task,
            "algorithm": args_cli.algorithm,
            "scenario_config_applied": bool(scenario_path),
            "scenario_config_path": scenario_path,
            "num_envs": env.n_envs,
            "num_agents": env.num_agents,
            "num_viewpoints": env.num_viewpoints,
            "noop_id": env.noop_action_id,
            "actor_observation_shape": shape_result["actor_observation_shape"],
            "actor_observation_shape_by_agent": shape_result["actor_observation_shape_by_agent"],
            "shared_observation_shape": shape_result["shared_observation_shape"],
            "available_actions_shape": shape_result["available_actions_shape"],
            "available_mask_shape": shape_result["available_mask_shape"],
            "episode_length_default_value": episode_length_default,
            "episode_length_override_supported": True,
            "episode_length_override_value": applied_episode_length,
            "assignment_rl_reward_log_keys_present": True,
            "assignment_rl_reward_log_keys": present_reward_log_keys,
            "assignment_rl_log_info_values": {
                key: float(env.log_info[key])
                for key in present_reward_log_keys
            },
            "reward_shape": list(rewards.shape),
            "reward_finite": bool(torch.isfinite(rewards).all().item()),
            "selected_action_ids": actions[..., 0].to(dtype=torch.long).detach().cpu().tolist(),
            "wrapper_step_success": True,
            "no_checkpoint_loaded": True,
            "no_checkpoint_saved": True,
            "no_training_run": True,
            "runner_run_called": False,
        }
        if args_cli.result_file is not None:
            result_path = Path(args_cli.result_file)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(
            "[OK] assignment training-entry readiness smoke passed "
            f"scenario_config_applied={result['scenario_config_applied']} "
            f"episode_length={applied_episode_length} "
            f"reward_log_keys={len(present_reward_log_keys)}"
        )
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
