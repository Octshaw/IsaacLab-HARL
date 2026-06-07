# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Short headless smoke for the repo-local assignment HARL wrapper."""

"""Launch Isaac Sim Simulator first."""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Smoke-test assignment-aware HARL wrapper for the scan task.")
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--max_steps", type=int, default=2, help="Maximum number of wrapper.step calls.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
ISAACLAB_TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks"
if str(ISAACLAB_TASKS_SOURCE) not in sys.path:
    sys.path.insert(0, str(ISAACLAB_TASKS_SOURCE))

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
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


def main() -> None:
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed

    wrapper = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
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

        for step_id in range(args_cli.max_steps):
            obs, shared_obs, rewards, dones, info, available_actions = wrapper.step(discrete_actions)
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

        print("[OK] assignment HARL wrapper smoke passed")
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
