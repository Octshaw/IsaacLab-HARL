# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unified fixed-12 assignment method evaluation.

This Phase 5 script compares assignment baselines and assignment-RL checkpoints on
the same scan environment, fixed viewpoint set, feasible mask, and episode
accounting. It does not train and does not modify HARL internals.
"""

from __future__ import annotations

import argparse
import copy
import csv
import random
import sys
from pathlib import Path
from typing import Any

import torch

from isaaclab.app import AppLauncher


METHODS = ("random", "nearest", "greedy", "assignment_rl")

parser = argparse.ArgumentParser(description="Evaluate fixed-12 scan assignment methods.")
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Task name.")
parser.add_argument("--methods", nargs="+", default=["random", "nearest", "greedy"], choices=METHODS)
parser.add_argument("--algorithm", type=str, default="happo", choices=("happo", "hatrpo", "haa2c"))
parser.add_argument("--assignment_checkpoint_dir", type=str, default=None, help="Assignment-mode models directory.")
parser.add_argument("--assignment_rl", action="store_true", help="Accepted for explicit assignment-RL eval commands.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--num_episodes", type=int, default=1, help="Total episode records to collect per method.")
parser.add_argument("--max_steps", type=int, default=320, help="Script-level episode step cap.")
parser.add_argument("--seed", type=int, default=None, help="Optional seed.")
parser.add_argument("--output_dir", type=str, default="results/assignment_eval/fixed12_phase5")
parser.add_argument(
    "--append_csv",
    action="store_true",
    help="Append new per-episode rows to an existing output_dir/per_episode.csv and recompute summary.csv.",
)
parser.add_argument("--print_diagnostics_steps", type=int, default=5, help="Leading assignment-RL steps to print.")
parser.add_argument(
    "--diagnostic_interval",
    type=int,
    default=0,
    help="Print assignment-RL diagnostics every N steps after the leading window. 0 disables interval printing.",
)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args
print(f"[INFO]: evaluate_assignment_methods methods={args_cli.methods}", flush=True)


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

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import compute_assignment_duplicate_count
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
    "success",
    "steps_to_full_coverage",
    "coverage_auc",
    "duplicate_count_mean",
    "noop_rate",
    "valid_action_rate",
    "new_viewpoints_total",
    "episode_length",
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
    if args_cli.seed is not None:
        cfg.seed = args_cli.seed
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
    if bool(feasible[:, 2, 5].any()):
        raise RuntimeError("fixed-12 MVP expected agent_2 -> viewpoint_5 to be infeasible")

    print(
        f"[INFO]: {method} fixed-12 MVP mask ok: "
        f"viewpoint_11_available={available[0, :, 11].detach().cpu().tolist()} "
        f"agent2_viewpoint5_available={bool(available[0, 2, 5].item())}"
    )


def _init_buffers(num_envs: int, device: torch.device) -> dict[str, torch.Tensor]:
    return {
        "length": torch.zeros(num_envs, dtype=torch.long, device=device),
        "return": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "coverage_auc": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "max_coverage": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "max_covered_count": torch.zeros(num_envs, dtype=torch.long, device=device),
        "steps_to_full": torch.full((num_envs,), -1, dtype=torch.long, device=device),
        "duplicate_sum": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "noop_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "valid_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "decision_count": torch.zeros(num_envs, dtype=torch.float32, device=device),
        "new_viewpoints_total": torch.zeros(num_envs, dtype=torch.float32, device=device),
    }


def _update_buffers(
    buffers: dict[str, torch.Tensor],
    *,
    reward_sum: torch.Tensor,
    assignment: torch.Tensor,
    valid_decisions: torch.Tensor,
    coverage: torch.Tensor,
    covered_count: torch.Tensor,
    new_viewpoints: torch.Tensor,
) -> None:
    num_agents = assignment.shape[1]
    buffers["length"] += 1
    buffers["return"] += reward_sum
    buffers["coverage_auc"] += coverage
    buffers["max_coverage"] = torch.maximum(buffers["max_coverage"], coverage)
    buffers["max_covered_count"] = torch.maximum(buffers["max_covered_count"], covered_count.to(dtype=torch.long))
    buffers["duplicate_sum"] += compute_assignment_duplicate_count(assignment)
    buffers["noop_count"] += (assignment < 0).sum(dim=1).to(dtype=torch.float32)
    buffers["valid_count"] += valid_decisions.sum(dim=1).to(dtype=torch.float32)
    buffers["decision_count"] += float(num_agents)
    buffers["new_viewpoints_total"] += new_viewpoints.to(dtype=torch.float32)

    hit_full = (buffers["steps_to_full"] < 0) & (coverage >= 1.0)
    buffers["steps_to_full"][hit_full] = buffers["length"][hit_full]


def _make_records(
    method: str,
    episode_start: int,
    env_ids: torch.Tensor,
    buffers: dict[str, torch.Tensor],
    max_steps: int,
) -> list[dict[str, float | int | str]]:
    records = []
    for offset, env_id_tensor in enumerate(env_ids):
        env_id = int(env_id_tensor.item())
        length = max(1, int(buffers["length"][env_id].item()))
        final_coverage = float(buffers["max_coverage"][env_id].item())
        steps_to_full = int(buffers["steps_to_full"][env_id].item())
        if steps_to_full < 0:
            steps_to_full = max_steps
        records.append(
            {
                "method": method,
                "episode": episode_start + offset,
                "episode_return": float(buffers["return"][env_id].item()),
                "final_coverage": final_coverage,
                "final_covered_count": int(buffers["max_covered_count"][env_id].item()),
                "success": int(final_coverage >= 1.0),
                "steps_to_full_coverage": steps_to_full,
                "coverage_auc": float((buffers["coverage_auc"][env_id] / length).item()),
                "duplicate_count_mean": float((buffers["duplicate_sum"][env_id] / length).item()),
                "noop_rate": float((buffers["noop_count"][env_id] / buffers["decision_count"][env_id].clamp(min=1.0)).item()),
                "valid_action_rate": float((buffers["valid_count"][env_id] / buffers["decision_count"][env_id].clamp(min=1.0)).item()),
                "new_viewpoints_total": float(buffers["new_viewpoints_total"][env_id].item()),
                "episode_length": length,
            }
        )
    return records


def _reset_buffers(buffers: dict[str, torch.Tensor], env_ids: torch.Tensor) -> None:
    for value in buffers.values():
        value[env_ids] = 0
    buffers["steps_to_full"][env_ids] = -1


def _coverage_from_env(unwrapped, env_done: torch.Tensor, pre_coverage: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    post_covered = unwrapped.viewpoints_covered.to(dtype=torch.bool)
    post_coverage = post_covered.float().mean(dim=-1)
    post_count = post_covered.sum(dim=-1)

    coverage = torch.where(env_done, torch.ones_like(pre_coverage), post_coverage)
    covered_count = torch.where(
        env_done,
        torch.full_like(post_count, int(unwrapped.num_viewpoints)),
        post_count,
    )
    return coverage, covered_count


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


def _evaluate_baseline(method: str, env_cfg) -> list[dict]:
    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    solver = make_solver(method)
    env.reset(seed=args_cli.seed)

    device = torch.device(unwrapped.device)
    agents = list(unwrapped.possible_agents)
    num_envs = int(unwrapped.num_envs)
    buffers = _init_buffers(num_envs, device)
    records: list[dict] = []
    _validate_fixed12_scenario(unwrapped.get_assignment_problem(), method)

    print(f"[INFO]: evaluating method={method} num_envs={num_envs} episodes={args_cli.num_episodes} max_steps={args_cli.max_steps}")
    try:
        with torch.no_grad():
            while simulation_app.is_running() and len(records) < args_cli.num_episodes:
                problem = unwrapped.get_assignment_problem()
                pre_coverage = problem["viewpoints_covered"].float().mean(dim=-1)
                assignment = solver.solve(problem)
                _validate_assignment(problem, assignment)
                valid_decisions = _valid_assignment_decisions(problem, assignment)

                actions = viewpoint_assignment_to_actions(unwrapped, assignment)
                _, rewards, terminated, truncated, _ = env.step(actions)

                terminated_tensor = _aggregate_done(terminated, agents, num_envs, device)
                truncated_tensor = _aggregate_done(truncated, agents, num_envs, device)
                env_done = terminated_tensor | truncated_tensor
                coverage, covered_count = _coverage_from_env(unwrapped, env_done, pre_coverage)
                new_viewpoints = _new_viewpoints_from_env(unwrapped)
                reward_sum = _sum_reward_dict(rewards, agents, num_envs, device)

                _update_buffers(
                    buffers,
                    reward_sum=reward_sum,
                    assignment=assignment,
                    valid_decisions=valid_decisions,
                    coverage=coverage,
                    covered_count=covered_count,
                    new_viewpoints=new_viewpoints,
                )

                script_done = buffers["length"] >= args_cli.max_steps
                done = env_done | script_done
                done_ids = torch.nonzero(done, as_tuple=False).flatten()
                if done_ids.numel() == 0:
                    continue

                remaining = args_cli.num_episodes - len(records)
                record_ids = done_ids[:remaining]
                records.extend(_make_records(method, len(records), record_ids, buffers, args_cli.max_steps))

                manual_reset = script_done & (~env_done)
                manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
                if manual_reset_ids.numel() > 0:
                    unwrapped._reset_idx(manual_reset_ids)

                _reset_buffers(buffers, done_ids)
                solver.reset()
    finally:
        env.close()
    return records


def _evaluate_baseline_methods(methods: list[str], env_cfg) -> list[dict]:
    env = gym.make(args_cli.task, cfg=env_cfg)
    unwrapped = env.unwrapped
    device = torch.device(unwrapped.device)
    agents = list(unwrapped.possible_agents)
    num_envs = int(unwrapped.num_envs)
    all_records: list[dict] = []

    try:
        for method in methods:
            solver = make_solver(method)
            env.reset(seed=args_cli.seed)
            buffers = _init_buffers(num_envs, device)
            records: list[dict] = []
            _validate_fixed12_scenario(unwrapped.get_assignment_problem(), method)

            print(
                f"[INFO]: evaluating method={method} num_envs={num_envs} "
                f"episodes={args_cli.num_episodes} max_steps={args_cli.max_steps}"
            )
            with torch.no_grad():
                while simulation_app.is_running() and len(records) < args_cli.num_episodes:
                    problem = unwrapped.get_assignment_problem()
                    pre_coverage = problem["viewpoints_covered"].float().mean(dim=-1)
                    assignment = solver.solve(problem)
                    _validate_assignment(problem, assignment)
                    valid_decisions = _valid_assignment_decisions(problem, assignment)

                    actions = viewpoint_assignment_to_actions(unwrapped, assignment)
                    _, rewards, terminated, truncated, _ = env.step(actions)

                    terminated_tensor = _aggregate_done(terminated, agents, num_envs, device)
                    truncated_tensor = _aggregate_done(truncated, agents, num_envs, device)
                    env_done = terminated_tensor | truncated_tensor
                    coverage, covered_count = _coverage_from_env(unwrapped, env_done, pre_coverage)
                    new_viewpoints = _new_viewpoints_from_env(unwrapped)
                    reward_sum = _sum_reward_dict(rewards, agents, num_envs, device)

                    _update_buffers(
                        buffers,
                        reward_sum=reward_sum,
                        assignment=assignment,
                        valid_decisions=valid_decisions,
                        coverage=coverage,
                        covered_count=covered_count,
                        new_viewpoints=new_viewpoints,
                    )

                    script_done = buffers["length"] >= args_cli.max_steps
                    done = env_done | script_done
                    done_ids = torch.nonzero(done, as_tuple=False).flatten()
                    if done_ids.numel() == 0:
                        continue

                    remaining = args_cli.num_episodes - len(records)
                    record_ids = done_ids[:remaining]
                    records.extend(_make_records(method, len(records), record_ids, buffers, args_cli.max_steps))

                    manual_reset = script_done & (~env_done)
                    manual_reset_ids = torch.nonzero(manual_reset, as_tuple=False).flatten()
                    if manual_reset_ids.numel() > 0:
                        unwrapped._reset_idx(manual_reset_ids)

                    _reset_buffers(buffers, done_ids)
                    solver.reset()
            all_records.extend(records)
    finally:
        env.close()
    return all_records


def _evaluate_assignment_rl(env_cfg, agent_cfg: dict) -> list[dict]:
    if args_cli.assignment_checkpoint_dir is None:
        raise ValueError("--assignment_checkpoint_dir is required when methods include assignment_rl")
    model_dir = Path(args_cli.assignment_checkpoint_dir).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Assignment checkpoint directory does not exist: {model_dir}")

    wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
    device = init_device(agent_cfg["device"])
    actors = _load_assignment_actors(wrapper, agent_cfg, model_dir, device)
    reset_kwargs = {"seed": args_cli.seed} if args_cli.seed is not None else {}
    obs, _, available_actions = wrapper.reset(**reset_kwargs)
    _assert_available_actions(wrapper, available_actions)
    _validate_fixed12_scenario(wrapper.unwrapped.get_assignment_problem(), "assignment_rl")

    num_envs = int(wrapper.num_envs)
    num_agents = int(wrapper.num_agents)
    buffers = _init_buffers(num_envs, wrapper.device)
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
                pre_coverage = problem["viewpoints_covered"].float().mean(dim=-1)

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

                obs, _, rewards, dones, info, available_actions = wrapper.step(actions)
                _assert_available_actions(wrapper, available_actions)

                dones_env = torch.all(dones.to(dtype=torch.bool), dim=1)
                coverage, covered_count = _coverage_from_env(wrapper.unwrapped, dones_env, pre_coverage)
                new_viewpoints = _new_viewpoints_from_env(wrapper.unwrapped)
                reward_sum = _sum_reward_tensor(rewards).to(device=wrapper.device)

                _update_buffers(
                    buffers,
                    reward_sum=reward_sum,
                    assignment=assignment,
                    valid_decisions=valid_decisions,
                    coverage=coverage,
                    covered_count=covered_count,
                    new_viewpoints=new_viewpoints,
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
                records.extend(_make_records("assignment_rl", len(records), record_ids, buffers, args_cli.max_steps))

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
        wrapper.close()
    return records


def _summarize(records: list[dict]) -> list[dict]:
    rows = []
    for method in METHODS:
        method_records = [record for record in records if record["method"] == method]
        if not method_records:
            continue
        count = float(len(method_records))
        rows.append(
            {
                "method": method,
                "episodes": len(method_records),
                "success_rate": sum(record["success"] for record in method_records) / count,
                "mean_return": sum(record["episode_return"] for record in method_records) / count,
                "mean_final_coverage": sum(record["final_coverage"] for record in method_records) / count,
                "mean_steps_to_full_coverage": sum(record["steps_to_full_coverage"] for record in method_records) / count,
                "mean_coverage_auc": sum(record["coverage_auc"] for record in method_records) / count,
                "mean_duplicate_count": sum(record["duplicate_count_mean"] for record in method_records) / count,
                "mean_noop_rate": sum(record["noop_rate"] for record in method_records) / count,
                "mean_valid_action_rate": sum(record["valid_action_rate"] for record in method_records) / count,
            }
        )
    return rows


def _read_per_episode_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    int_fields = {"episode", "final_covered_count", "success", "steps_to_full_coverage", "episode_length"}
    float_fields = {
        "episode_return",
        "final_coverage",
        "coverage_auc",
        "duplicate_count_mean",
        "noop_rate",
        "valid_action_rate",
        "new_viewpoints_total",
    }
    records = []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            record = dict(row)
            for field in int_fields:
                record[field] = int(float(record[field]))
            for field in float_fields:
                record[field] = float(record[field])
            records.append(record)
    return records


def _offset_episode_ids(new_records: list[dict], existing_records: list[dict]) -> None:
    next_episode_by_method = {}
    for record in existing_records:
        method = record["method"]
        next_episode_by_method[method] = max(next_episode_by_method.get(method, 0), int(record["episode"]) + 1)
    for record in new_records:
        method = record["method"]
        offset = next_episode_by_method.get(method, 0)
        record["episode"] = int(record["episode"]) + offset


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[INFO]: wrote {path}")


def _print_summary(rows: list[dict]) -> None:
    if not rows:
        print("[WARN]: no summary rows")
        return
    print("[RESULT]: Phase 5 assignment method summary")
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

    _set_global_seeds(args_cli.seed)
    all_records: list[dict] = []
    baseline_methods = [method for method in args_cli.methods if method != "assignment_rl"]
    if "assignment_rl" in args_cli.methods:
        all_records.extend(_evaluate_assignment_rl(_clone_env_cfg(env_cfg), agent_cfg))
    if baseline_methods:
        all_records.extend(_evaluate_baseline_methods(baseline_methods, _clone_env_cfg(env_cfg)))

    output_dir = Path(args_cli.output_dir)
    per_episode_path = output_dir / "per_episode.csv"
    summary_path = output_dir / "summary.csv"
    existing_records = _read_per_episode_csv(per_episode_path) if args_cli.append_csv else []
    if existing_records:
        _offset_episode_ids(all_records, existing_records)
        all_records = existing_records + all_records
    summary_rows = _summarize(all_records)
    _write_csv(per_episode_path, all_records, PER_EPISODE_FIELDS)
    _write_csv(summary_path, summary_rows, SUMMARY_FIELDS)
    _print_summary(summary_rows)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
