# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Episode-boundary reset smoke for assignment HARL wrapper history state."""

"""Launch Isaac Sim Simulator first."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

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
    description="Smoke-test assignment HARL wrapper history reset at Isaac Lab episode boundaries.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Task name.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--max_steps", type=int, default=330, help="Maximum number of wrapper.step calls.")
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

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.utils import parse_env_cfg


def _as_list(tensor: torch.Tensor) -> list:
    return tensor.detach().cpu().tolist()


def _finite_scalar(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return True


def _assert_shapes(wrapper, obs: dict[str, torch.Tensor], shared_obs: torch.Tensor, available_actions: torch.Tensor) -> dict:
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
            raise AssertionError(f"{agent} obs shape mismatch: got {tuple(agent_obs.shape)}")
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

    problem = wrapper.unwrapped.get_assignment_problem()
    available_mask = problem["available_mask"]
    if tuple(available_mask.shape) != (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints):
        raise AssertionError(f"available_mask shape mismatch: got {tuple(available_mask.shape)}")

    return {
        "actor_observation_shape": list(next(iter(actor_shapes.values()))),
        "actor_observation_shape_by_agent": actor_shapes,
        "shared_observation_shape": list(shared_obs.shape),
        "available_actions_shape": list(available_actions.shape),
        "available_mask_shape": list(available_mask.shape),
    }


def _first_available_actions(wrapper, available_actions: torch.Tensor) -> torch.Tensor:
    actions = wrapper.make_action_tensor()
    available_bool = available_actions.to(dtype=torch.bool)
    for env_id in range(wrapper.num_envs):
        for agent_id in range(wrapper.num_agents):
            available_ids = torch.nonzero(
                available_bool[env_id, agent_id, : wrapper.num_viewpoints],
                as_tuple=False,
            ).flatten()
            selected_id = int(available_ids[0].item()) if available_ids.numel() > 0 else int(wrapper.noop_action_id)
            actions[env_id, agent_id, 0] = float(selected_id)
    return actions


def _reward_decomposition_summary(info: dict) -> dict[str, Any]:
    decomposition = info.get("assignment_rl_reward")
    if not isinstance(decomposition, dict):
        raise AssertionError("step info must contain assignment_rl_reward")
    summary = {}
    for key, value in decomposition.items():
        if isinstance(value, torch.Tensor):
            if not torch.isfinite(value).all():
                raise AssertionError(f"assignment_rl_reward.{key} contains non-finite values")
            detached = value.detach().to(dtype=torch.float32).cpu()
            summary[key] = {
                "shape": list(value.shape),
                "mean": float(detached.mean().item()),
                "min": float(detached.min().item()),
                "max": float(detached.max().item()),
                "values": detached.tolist(),
            }
        elif isinstance(value, dict):
            summary[key] = dict(value)
        elif _finite_scalar(value):
            summary[key] = value
    return summary


def _state_snapshot(wrapper, *, step: int, label: str, dones: torch.Tensor | None = None) -> dict[str, Any]:
    reset_buf = getattr(wrapper.unwrapped, "reset_buf", None)
    episode_length_buf = getattr(wrapper.unwrapped, "episode_length_buf", None)
    return {
        "label": label,
        "step": int(step),
        "dones": _as_list(dones.to(dtype=torch.bool)) if isinstance(dones, torch.Tensor) else None,
        "episode_length_buf": _as_list(episode_length_buf) if isinstance(episode_length_buf, torch.Tensor) else None,
        "reset_buf": _as_list(reset_buf.to(dtype=torch.bool)) if isinstance(reset_buf, torch.Tensor) else None,
        "assignment_step": _as_list(wrapper._assignment_step),
        "steps_since_global_coverage_gain": _as_list(wrapper._steps_since_global_coverage_gain),
        "attempted_count_sum": _as_list(wrapper._per_viewpoint_attempted_count.sum(dim=1)),
        "attempted_count_max": _as_list(wrapper._per_viewpoint_attempted_count.max(dim=1).values),
        "never_attempted_count": _as_list((wrapper._last_viewpoint_attempt_step < 0).sum(dim=1)),
        "last_attempt_step_min": _as_list(wrapper._last_viewpoint_attempt_step.min(dim=1).values),
        "previous_assignment": _as_list(wrapper._previous_assignment),
        "same_target_streak": _as_list(wrapper._same_target_streak),
        "per_robot_completed_count": _as_list(wrapper._per_robot_completed_count),
        "per_robot_repeated_assignment_count": _as_list(wrapper._per_robot_repeated_assignment_count),
        "per_robot_selected_count": _as_list(wrapper._per_robot_selected_count),
        "last_covered_count": _as_list(wrapper._last_covered_mask.sum(dim=1)),
    }


def _assert_reset_snapshot(wrapper, snapshot: dict[str, Any]) -> None:
    if any(float(value) != 0.0 for value in snapshot["assignment_step"]):
        raise AssertionError(f"assignment_step did not reset: {snapshot['assignment_step']}")
    if any(float(value) != 0.0 for value in snapshot["steps_since_global_coverage_gain"]):
        raise AssertionError(
            "steps_since_global_coverage_gain did not reset: "
            f"{snapshot['steps_since_global_coverage_gain']}"
        )
    if any(float(value) != 0.0 for value in snapshot["attempted_count_sum"]):
        raise AssertionError(f"per-viewpoint attempted counts did not reset: {snapshot['attempted_count_sum']}")
    if any(int(value) != wrapper.num_viewpoints for value in snapshot["never_attempted_count"]):
        raise AssertionError(f"last-attempt age did not reset to never-attempted: {snapshot['never_attempted_count']}")
    previous = torch.as_tensor(snapshot["previous_assignment"])
    if not bool((previous < 0).all().item()):
        raise AssertionError(f"previous assignment did not reset to no previous/noop: {snapshot['previous_assignment']}")
    same_target = torch.as_tensor(snapshot["same_target_streak"], dtype=torch.float32)
    if not bool((same_target == 0.0).all().item()):
        raise AssertionError(f"same-target streak did not reset: {snapshot['same_target_streak']}")
    completed = torch.as_tensor(snapshot["per_robot_completed_count"], dtype=torch.float32)
    repeated = torch.as_tensor(snapshot["per_robot_repeated_assignment_count"], dtype=torch.float32)
    if not bool((completed == 0.0).all().item()):
        raise AssertionError(f"per-robot completed count did not reset: {snapshot['per_robot_completed_count']}")
    if not bool((repeated == 0.0).all().item()):
        raise AssertionError(f"per-robot repeated count did not reset: {snapshot['per_robot_repeated_assignment_count']}")


def main() -> None:
    if args_cli.num_envs != 1:
        raise ValueError("Phase 9D-1A episode-reset smoke currently expects --num_envs 1")
    if args_cli.max_steps <= 1:
        raise ValueError("--max_steps must be greater than 1")

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

    wrapper = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        obs, shared_obs, available_actions = wrapper.reset(seed=args_cli.seed)
        shape_result = _assert_shapes(wrapper, obs, shared_obs, available_actions)

        snapshots: list[dict[str, Any]] = [_state_snapshot(wrapper, step=0, label="after_explicit_reset")]
        reward_steps_since_values: list[float] = []
        reward_steps_since_by_step: list[dict[str, Any]] = []
        first_done_step: int | None = None
        before_done_snapshot: dict[str, Any] | None = None
        done_boundary_snapshot: dict[str, Any] | None = None
        next_episode_snapshots: list[dict[str, Any]] = []
        previous_snapshot = snapshots[-1]

        for step in range(1, args_cli.max_steps + 1):
            actions = _first_available_actions(wrapper, available_actions)
            obs, shared_obs, rewards, dones, info, available_actions = wrapper.step(actions)
            shape_result = _assert_shapes(wrapper, obs, shared_obs, available_actions)
            if tuple(rewards.shape) != (wrapper.num_envs, wrapper.num_agents, 1):
                raise AssertionError(f"reward shape mismatch: got {tuple(rewards.shape)}")
            if not torch.isfinite(rewards).all():
                raise AssertionError("reward tensor contains non-finite values")
            reward_summary = _reward_decomposition_summary(info)
            steps_since = reward_summary["steps_since_global_coverage_gain"]
            reward_steps_since_values.append(float(steps_since["max"]))
            reward_steps_since_by_step.append(
                {
                    "step": step,
                    "mean": steps_since["mean"],
                    "max": steps_since["max"],
                    "global_coverage_gain_mean": reward_summary["global_coverage_gain"]["mean"],
                    "done_any": bool(dones.any().item()),
                }
            )

            label = None
            if step in {1, 299, 300, 301, args_cli.max_steps}:
                label = f"step_{step}"
            if first_done_step is not None and step in {first_done_step + 1, first_done_step + 2}:
                label = f"next_episode_step_{step - first_done_step}"

            current_snapshot = _state_snapshot(wrapper, step=step, label=label or f"step_{step}", dones=dones)
            if label is not None:
                snapshots.append(current_snapshot)

            if bool(dones.all(dim=1).any().item()) and first_done_step is None:
                first_done_step = step
                before_done_snapshot = previous_snapshot
                done_boundary_snapshot = _state_snapshot(
                    wrapper,
                    step=step,
                    label="immediately_after_done_boundary",
                    dones=dones,
                )
                snapshots.append(done_boundary_snapshot)

            if first_done_step is not None and step in {first_done_step + 1, first_done_step + 2}:
                next_episode_snapshots.append(current_snapshot)

            previous_snapshot = current_snapshot

        if first_done_step is None:
            raise AssertionError(f"no episode boundary was observed within {args_cli.max_steps} wrapper steps")
        if before_done_snapshot is None or done_boundary_snapshot is None:
            raise AssertionError("episode-boundary snapshots were not captured")
        if max(float(value) for value in before_done_snapshot["attempted_count_sum"]) <= 0.0:
            raise AssertionError("pre-boundary attempted counts never became positive")

        _assert_reset_snapshot(wrapper, done_boundary_snapshot)
        if not next_episode_snapshots:
            raise AssertionError("no next-episode snapshots were captured after the done boundary")
        max_next_episode_steps_since = max(
            max(float(v) for v in snapshot["steps_since_global_coverage_gain"])
            for snapshot in next_episode_snapshots
        )
        if max_next_episode_steps_since > 2.0:
            raise AssertionError(
                "steps_since_global_coverage_gain carried into next episode: "
                f"max_next_episode_steps_since={max_next_episode_steps_since}"
            )

        max_reward_steps_since = max(reward_steps_since_values)
        horizon = int(getattr(wrapper.unwrapped, "max_episode_length", 300) or 300)
        if max_reward_steps_since > float(horizon):
            raise AssertionError(
                f"reward steps_since_global_coverage_gain exceeded episode horizon: "
                f"max={max_reward_steps_since} horizon={horizon}"
            )

        result = {
            "task": args_cli.task,
            "scenario_config_path": SCENARIO_CONFIG.get("_scenario_config_path"),
            "num_envs": wrapper.num_envs,
            "num_agents": wrapper.num_agents,
            "num_viewpoints": wrapper.num_viewpoints,
            "noop_id": wrapper.noop_action_id,
            "max_steps": args_cli.max_steps,
            "completed_steps": args_cli.max_steps,
            "first_done_step": first_done_step,
            "episode_horizon": horizon,
            "actor_observation_shape": shape_result["actor_observation_shape"],
            "actor_observation_shape_by_agent": shape_result["actor_observation_shape_by_agent"],
            "shared_observation_shape": shape_result["shared_observation_shape"],
            "available_actions_shape": shape_result["available_actions_shape"],
            "available_mask_shape": shape_result["available_mask_shape"],
            "snapshots": snapshots,
            "before_done_snapshot": before_done_snapshot,
            "done_boundary_snapshot": done_boundary_snapshot,
            "next_episode_snapshots": next_episode_snapshots,
            "reward_steps_since_global_coverage_gain_by_step_sample": reward_steps_since_by_step[:5]
            + reward_steps_since_by_step[-5:],
            "max_reward_steps_since_global_coverage_gain": max_reward_steps_since,
            "max_next_episode_state_steps_since_global_coverage_gain": max_next_episode_steps_since,
            "attempted_counts_positive_before_boundary": True,
            "history_reset_after_boundary": True,
            "no_checkpoint_loaded": True,
            "no_training_run": True,
            "runner_run_called": False,
        }
        if args_cli.result_file is not None:
            result_path = Path(args_cli.result_file)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        print(
            "[OK] assignment history episode-reset smoke passed "
            f"first_done_step={first_done_step} "
            f"max_reward_steps_since={max_reward_steps_since} "
            f"max_next_episode_state_steps_since={max_next_episode_steps_since}"
        )
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
