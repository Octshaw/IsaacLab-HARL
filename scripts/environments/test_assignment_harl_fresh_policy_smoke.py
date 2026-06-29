# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Fresh-policy tensor-flow smoke for fixed-N assignment HARL."""

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
    description="No-training fresh-policy tensor-flow smoke for fixed-N assignment HARL.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Task name.")
parser.add_argument("--algorithm", type=str, default="happo", choices=("happo", "hatrpo", "haa2c"))
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--max_steps", type=int, default=1, help="Number of wrapper steps to smoke.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
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

from harl.algorithms.actors import ALGO_REGISTRY

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.utils import parse_env_cfg


EXPECTED_REWARD_KEYS = (
    "config",
    "base_env_reward",
    "repeated_same_target_no_progress",
    "global_no_progress",
    "selected_path_cost",
    "selected_path_cost_raw",
    "selected_path_cost_norm",
    "total_assignment_reward_adjustment",
    "final_reward",
    "same_target_streak",
    "steps_since_global_coverage_gain",
    "global_coverage_gain",
)


def _load_agent_config(algorithm: str) -> dict[str, Any]:
    cfg_path = SCAN_TASK_SOURCE / "agents" / f"harl_{algorithm}_cfg.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No task-local HARL config found for algorithm={algorithm!r}: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict) or "model" not in data or "algo" not in data:
        raise ValueError(f"Invalid HARL actor config: {cfg_path}")
    return data


def _actor_args(agent_cfg: dict[str, Any]) -> dict[str, Any]:
    return {**agent_cfg["model"], **agent_cfg["algo"]}


def _head_width(action_head: Any) -> int | None:
    for attr_name in ("linear", "fc", "fc_mean"):
        layer = getattr(action_head, attr_name, None)
        weight = getattr(layer, "weight", None)
        if weight is not None and getattr(weight, "ndim", 0) >= 2:
            return int(weight.shape[0])
    for attr_name in ("weight",):
        weight = getattr(action_head, attr_name, None)
        if weight is not None and getattr(weight, "ndim", 0) >= 2:
            return int(weight.shape[0])
    state = action_head.state_dict() if hasattr(action_head, "state_dict") else {}
    for key, value in state.items():
        if key.endswith("weight") and getattr(value, "ndim", 0) >= 2:
            return int(value.shape[0])
    return None


def _make_fresh_actors(
    wrapper, *, algorithm: str, agent_cfg: dict[str, Any], device: torch.device
) -> tuple[list[Any], dict[str, int]]:
    actor_args = _actor_args(agent_cfg)
    actors = []
    head_widths: dict[str, int] = {}
    for agent_id, agent_name in enumerate(wrapper.agents):
        actor = ALGO_REGISTRY[algorithm](
            actor_args,
            wrapper.observation_space[agent_id],
            wrapper.action_space[agent_id],
            device=device,
        )
        actor.prep_rollout()
        policy = getattr(actor, "actor", None)
        act_layer = getattr(policy, "act", None)
        action_type = getattr(act_layer, "action_type", None)
        action_head = getattr(act_layer, "action_out", None)
        action_head_name = action_head.__class__.__name__ if action_head is not None else None
        if action_type != "Discrete" or action_head_name != "Categorical":
            raise AssertionError(
                f"{agent_name} expected Discrete/Categorical actor, got {action_type}/{action_head_name}"
            )
        width = _head_width(action_head)
        if width != wrapper.num_viewpoints + 1:
            raise AssertionError(
                f"{agent_name} action head width mismatch: expected {wrapper.num_viewpoints + 1}, got {width}"
            )
        actors.append(actor)
        head_widths[agent_name] = int(width)
    return actors, head_widths


def _assert_wrapper_shapes(wrapper, obs: dict[str, torch.Tensor], shared_obs: torch.Tensor, available_actions: torch.Tensor) -> dict:
    if wrapper.num_agents != 3:
        raise AssertionError(f"expected 3 agents, got {wrapper.num_agents}")
    if wrapper.num_viewpoints != 50:
        raise AssertionError(f"expected 50 viewpoints, got {wrapper.num_viewpoints}")
    if wrapper.noop_action_id != 50:
        raise AssertionError(f"expected noop id 50, got {wrapper.noop_action_id}")

    actor_shapes = {}
    for agent in wrapper.agents:
        agent_obs = obs[agent]
        if tuple(agent_obs.shape) != (wrapper.num_envs, 909):
            raise AssertionError(f"{agent} obs shape mismatch: expected {(wrapper.num_envs, 909)}, got {tuple(agent_obs.shape)}")
        if not torch.isfinite(agent_obs).all():
            raise AssertionError(f"{agent} obs contains non-finite values")
        actor_shapes[agent] = list(agent_obs.shape)

    if tuple(shared_obs.shape) != (wrapper.num_envs, wrapper.num_agents, 2727):
        raise AssertionError(f"shared obs shape mismatch: got {tuple(shared_obs.shape)}")
    if not torch.isfinite(shared_obs).all():
        raise AssertionError("shared obs contains non-finite values")

    expected_available = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1)
    if tuple(available_actions.shape) != expected_available:
        raise AssertionError(f"available_actions shape mismatch: expected {expected_available}, got {tuple(available_actions.shape)}")
    if not torch.isfinite(available_actions).all():
        raise AssertionError("available_actions contains non-finite values")

    problem = wrapper.unwrapped.get_assignment_problem()
    available_mask = problem["available_mask"]
    expected_mask = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints)
    if tuple(available_mask.shape) != expected_mask:
        raise AssertionError(f"available_mask shape mismatch: expected {expected_mask}, got {tuple(available_mask.shape)}")

    return {
        "actor_observation_shape": list(next(iter(actor_shapes.values()))),
        "actor_observation_shape_by_agent": actor_shapes,
        "shared_observation_shape": list(shared_obs.shape),
        "available_actions_shape": list(available_actions.shape),
        "available_mask_shape": list(available_mask.shape),
    }


def _action_space_summary(wrapper) -> dict[str, dict[str, Any]]:
    summary = {}
    for agent_id, space in wrapper.action_space.items():
        summary[wrapper.agents[agent_id]] = {
            "class": space.__class__.__name__,
            "n": int(getattr(space, "n", -1)),
        }
    return summary


def _tensor_values(tensor: torch.Tensor) -> list:
    return tensor.detach().cpu().tolist()


def _reward_tensor_summary(tensor: torch.Tensor) -> dict[str, Any]:
    detached = tensor.detach().to(dtype=torch.float32).cpu()
    return {
        "shape": list(tensor.shape),
        "finite": bool(torch.isfinite(tensor).all().item()),
        "min": float(detached.min().item()),
        "max": float(detached.max().item()),
        "mean": float(detached.mean().item()),
        "values": detached.tolist(),
    }


def _collect_actor_actions(
    wrapper,
    actors: list[Any],
    obs: dict[str, torch.Tensor],
    available_actions: torch.Tensor,
    agent_cfg: dict[str, Any],
    device: torch.device,
) -> tuple[torch.Tensor, dict[str, Any]]:
    actions = make_harl_action_tensor(wrapper.num_envs, wrapper.action_space, device=wrapper.device)
    rnn_hidden_size = int(agent_cfg["model"]["hidden_sizes"][-1])
    recurrent_n = int(agent_cfg["model"]["recurrent_n"])
    rnn_states = torch.zeros(
        (wrapper.num_envs, wrapper.num_agents, recurrent_n, rnn_hidden_size),
        dtype=torch.float32,
        device=device,
    )
    masks = torch.ones((wrapper.num_envs, wrapper.num_agents, 1), dtype=torch.float32, device=device)

    sampled_ids = []
    valid = []
    available = []
    action_shapes = []
    with torch.inference_mode():
        for agent_id, agent_name in enumerate(wrapper.agents):
            agent_obs = obs[agent_name].to(device=device)
            agent_available_actions = available_actions[:, agent_id, :].to(device=device)
            action, rnn_state = actors[agent_id].act(
                agent_obs,
                rnn_states[:, agent_id].clone(),
                masks[:, agent_id],
                agent_available_actions,
                deterministic=False,
            )
            rnn_states[:, agent_id] = rnn_state
            action = action.to(device=wrapper.device)
            action_shapes.append(list(action.shape))
            if tuple(action.shape) != (wrapper.num_envs, 1):
                raise AssertionError(f"{agent_name} action shape mismatch: expected {(wrapper.num_envs, 1)}, got {tuple(action.shape)}")
            action_ids = action[..., 0].to(dtype=torch.long)
            in_range = (action_ids >= 0) & (action_ids <= wrapper.noop_action_id)
            selected_available = torch.gather(
                available_actions[:, agent_id, :].to(dtype=torch.bool),
                dim=1,
                index=action_ids.clamp(min=0, max=wrapper.noop_action_id).unsqueeze(-1),
            ).squeeze(-1)
            if not bool(in_range.all().item()):
                raise AssertionError(f"{agent_name} produced out-of-range action ids: {_tensor_values(action_ids)}")
            if not bool(selected_available.all().item()):
                raise AssertionError(f"{agent_name} produced unavailable action ids: {_tensor_values(action_ids)}")
            actions[:, agent_id, : action.shape[-1]] = action
            sampled_ids.append(_tensor_values(action_ids))
            valid.append(_tensor_values(in_range))
            available.append(_tensor_values(selected_available))

    return actions, {
        "action_tensor_shape": list(actions.shape),
        "per_agent_action_shape": action_shapes,
        "sampled_action_per_agent": sampled_ids,
        "sampled_action_valid_per_agent": valid,
        "sampled_action_available_per_agent": available,
    }


def _verify_reward_decomposition(info: dict, rewards: torch.Tensor) -> dict[str, Any]:
    if "assignment_rl_reward" not in info:
        raise AssertionError("info must contain assignment_rl_reward")
    decomposition = info["assignment_rl_reward"]
    missing = [key for key in EXPECTED_REWARD_KEYS if key not in decomposition]
    if missing:
        raise AssertionError(f"assignment_rl_reward missing keys: {missing}")
    if not torch.isfinite(rewards).all():
        raise AssertionError("reward tensor contains non-finite values")
    if not torch.allclose(decomposition["final_reward"], rewards):
        raise AssertionError("returned rewards do not match assignment_rl_reward.final_reward")
    for key, value in decomposition.items():
        if isinstance(value, torch.Tensor) and not torch.isfinite(value).all():
            raise AssertionError(f"assignment_rl_reward.{key} contains non-finite values")
    return {
        "reward_shape": list(rewards.shape),
        "reward_finite": bool(torch.isfinite(rewards).all().item()),
        "reward_decomposition_present": True,
        "reward_decomposition_keys": sorted(decomposition.keys()),
        "reward_summary": _reward_tensor_summary(rewards),
    }


def main() -> None:
    if args_cli.num_envs != 1:
        raise ValueError("Phase 9C-1 smoke currently expects --num_envs 1")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if bool(getattr(args_cli, "align_base_center_to_world_origin", False)) and getattr(args_cli, "component_mesh_position", None) is not None:
        raise ValueError("--align_base_center_to_world_origin cannot be combined with --component_mesh_position")

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    apply_scenario_config_to_env_cfg(env_cfg, args_cli)

    wrapper = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        obs, shared_obs, available_actions = wrapper.reset(seed=args_cli.seed)
        shape_result = _assert_wrapper_shapes(wrapper, obs, shared_obs, available_actions)
        device = torch.device(str(args_cli.device))
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(f"Requested CUDA device {device}, but torch.cuda.is_available() is false")
        agent_cfg = _load_agent_config(args_cli.algorithm)
        actors, head_widths = _make_fresh_actors(
            wrapper, algorithm=args_cli.algorithm, agent_cfg=agent_cfg, device=device
        )
        action_result: dict[str, Any] | None = None
        reward_result: dict[str, Any] | None = None
        completed_steps = 0
        for step_id in range(1, args_cli.max_steps + 1):
            actions, action_result = _collect_actor_actions(
                wrapper, actors, obs, available_actions, agent_cfg, device
            )
            obs, shared_obs, rewards, dones, info, available_actions = wrapper.step(actions)
            reward_result = _verify_reward_decomposition(info, rewards)
            _assert_wrapper_shapes(wrapper, obs, shared_obs, available_actions)
            completed_steps = step_id

        if action_result is None or reward_result is None:
            raise AssertionError("smoke did not execute any wrapper steps")

        result = {
            "task": args_cli.task,
            "algorithm": args_cli.algorithm,
            "num_envs": wrapper.num_envs,
            "num_agents": wrapper.num_agents,
            "num_viewpoints": wrapper.num_viewpoints,
            "noop_id": wrapper.noop_action_id,
            "scenario_config_path": SCENARIO_CONFIG.get("_scenario_config_path"),
            "completed_steps": completed_steps,
            "actor_observation_shape": shape_result["actor_observation_shape"],
            "actor_observation_shape_by_agent": shape_result["actor_observation_shape_by_agent"],
            "shared_observation_shape": shape_result["shared_observation_shape"],
            "available_actions_shape": shape_result["available_actions_shape"],
            "available_mask_shape": shape_result["available_mask_shape"],
            "action_space_summary": _action_space_summary(wrapper),
            "actor_head_width_per_agent": head_widths,
            "sampled_action_per_agent": action_result["sampled_action_per_agent"],
            "sampled_action_valid_per_agent": action_result["sampled_action_valid_per_agent"],
            "sampled_action_available_per_agent": action_result["sampled_action_available_per_agent"],
            "action_tensor_shape": action_result["action_tensor_shape"],
            "per_agent_action_shape": action_result["per_agent_action_shape"],
            "reward_shape": reward_result["reward_shape"],
            "reward_finite": reward_result["reward_finite"],
            "reward_decomposition_present": reward_result["reward_decomposition_present"],
            "reward_decomposition_keys": reward_result["reward_decomposition_keys"],
            "reward_summary": reward_result["reward_summary"],
            "wrapper_step_success": True,
            "no_checkpoint_loaded": True,
            "no_training_run": True,
            "checkpoint_saved": False,
            "runner_run_called": False,
        }
        if args_cli.result_file is not None:
            result_path = Path(args_cli.result_file)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        print(
            "[OK] fresh assignment policy tensor-flow smoke passed "
            f"obs={shape_result['actor_observation_shape']} "
            f"shared={shape_result['shared_observation_shape']} "
            f"available={shape_result['available_actions_shape']} "
            f"head_widths={head_widths}"
        )
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
