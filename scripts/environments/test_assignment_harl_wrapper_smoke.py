# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Short headless smoke for the repo-local assignment HARL wrapper."""

"""Launch Isaac Sim Simulator first."""

import argparse
import json
import sys
from pathlib import Path

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

pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="Smoke-test assignment-aware HARL wrapper for the scan task.",
    parents=[pre_parser],
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of vectorized environments.")
parser.add_argument("--max_steps", type=int, default=2, help="Maximum number of wrapper.step calls.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--viewpoint_csv_path", type=str, default=None, help="Optional fixed-N viewpoint CSV path.")
parser.add_argument("--expect_num_viewpoints", type=int, default=None, help="Assert the loaded viewpoint count.")
parser.add_argument("--result_file", type=str, default=None, help="Optional JSON file for smoke diagnostics.")
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


def _reset_diagnostics(wrapper, available_actions: torch.Tensor, completed_steps: int) -> dict:
    problem = wrapper.unwrapped.get_assignment_problem()
    feasible = problem["feasible_mask"].to(dtype=torch.bool)
    static_feasible = problem.get("static_geometric_feasible_mask", feasible).to(dtype=torch.bool)
    viewpoint_ids = list(problem.get("viewpoint_ids", range(wrapper.num_viewpoints)))

    def _agents_per_viewpoint(mask: torch.Tensor) -> dict:
        first_env_mask = mask[0]
        result = {}
        for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
            result[str(viewpoint_id)] = [
                agent
                for agent_id, agent in enumerate(wrapper.agents)
                if bool(first_env_mask[agent_id, viewpoint_index].item())
            ]
        return result

    static_feasible_agents_per_viewpoint = _agents_per_viewpoint(static_feasible)
    feasible_agents_per_viewpoint = _agents_per_viewpoint(feasible)
    final_rows = list(problem.get("feasibility_diagnostic_rows", []))
    static_rows = list(problem.get("static_geometric_feasibility_rows", []))
    manual_override_rows = list(problem.get("manual_feasibility_override_rows", []))
    mesh_diagnostics = None
    if hasattr(wrapper.unwrapped, "get_component_mesh_diagnostics"):
        mesh_diagnostics = wrapper.unwrapped.get_component_mesh_diagnostics()
    infeasible_rows = [row for row in final_rows if not row.get("feasible", False)]
    infeasible_rows_missing_reason = [row for row in infeasible_rows if not row.get("reason_if_false")]
    if infeasible_rows_missing_reason:
        raise AssertionError(f"infeasible feasibility rows must include reason_if_false: {infeasible_rows_missing_reason}")

    for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
        if not feasible_agents_per_viewpoint[str(viewpoint_id)]:
            raise AssertionError(f"viewpoint {viewpoint_id} has zero feasible agents")

    env_has_feasible_agent = feasible.any(dim=1)
    unavailable_indices = torch.nonzero(~env_has_feasible_agent.any(dim=0), as_tuple=False).flatten()
    permanently_unavailable = [viewpoint_ids[int(index.item())] for index in unavailable_indices.detach().cpu()]
    result = {
        "num_envs": wrapper.num_envs,
        "num_agents": wrapper.num_agents,
        "num_viewpoints": wrapper.num_viewpoints,
        "noop_id": wrapper.noop_action_id,
        "available_actions_shape": list(available_actions.shape),
        "viewpoint_csv_path": getattr(wrapper.unwrapped.cfg, "viewpoint_csv_path", None),
        "viewpoint_ids": viewpoint_ids,
        "static_geometric_feasible_agents_per_viewpoint": static_feasible_agents_per_viewpoint,
        "feasible_agents_per_viewpoint": feasible_agents_per_viewpoint,
        "permanently_unavailable_viewpoints": permanently_unavailable,
        "static_geometric_feasibility_rows": static_rows,
        "manual_feasibility_override_rows": manual_override_rows,
        "feasibility_diagnostic_rows": final_rows,
        "infeasible_rows": infeasible_rows,
        "completed_steps": completed_steps,
    }
    if mesh_diagnostics is not None:
        result.update(mesh_diagnostics)
    return result


def main() -> None:
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if args_cli.align_base_center_to_world_origin and args_cli.component_mesh_position is not None:
        raise ValueError(
            "--align_base_center_to_world_origin cannot be combined with --component_mesh_position. "
            "Use one world-origin convention at a time."
        )

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    if args_cli.viewpoint_csv_path is not None:
        env_cfg.viewpoint_csv_path = args_cli.viewpoint_csv_path
    if args_cli.component_mesh_path is not None:
        env_cfg.component_mesh_path = args_cli.component_mesh_path
    if args_cli.component_mesh_format is not None:
        env_cfg.component_mesh_format = args_cli.component_mesh_format
    if args_cli.component_mesh_unit is not None:
        env_cfg.component_mesh_unit = args_cli.component_mesh_unit
    if args_cli.component_mesh_scale is not None:
        env_cfg.component_mesh_scale = tuple(args_cli.component_mesh_scale)
    if args_cli.component_mesh_position is not None:
        env_cfg.component_mesh_position = tuple(args_cli.component_mesh_position)
    if args_cli.component_mesh_orientation is not None:
        env_cfg.component_mesh_orientation = tuple(args_cli.component_mesh_orientation)
    if args_cli.component_mesh_orientation_format is not None:
        env_cfg.component_mesh_orientation_format = args_cli.component_mesh_orientation_format
    if args_cli.component_mesh_visible is not None:
        env_cfg.component_mesh_visible = bool(args_cli.component_mesh_visible)
    if args_cli.align_base_center_to_world_origin:
        env_cfg.component_mesh_align_base_center_to_world_origin = True
    if args_cli.component_proxy_type is not None:
        env_cfg.component_proxy_type = args_cli.component_proxy_type
    if args_cli.component_proxy_auto_from_mesh is not None:
        env_cfg.component_proxy_auto_from_mesh = bool(args_cli.component_proxy_auto_from_mesh)
    if args_cli.component_proxy_padding is not None:
        env_cfg.component_proxy_padding = float(args_cli.component_proxy_padding)
    if args_cli.component_proxy_visual_visible is not None:
        env_cfg.component_proxy_visual_visible = bool(args_cli.component_proxy_visual_visible)

    wrapper = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        if args_cli.expect_num_viewpoints is not None and wrapper.num_viewpoints != args_cli.expect_num_viewpoints:
            raise AssertionError(
                f"num_viewpoints mismatch: expected {args_cli.expect_num_viewpoints}, got {wrapper.num_viewpoints}"
            )
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

        completed_steps = 0
        for step_id in range(args_cli.max_steps):
            obs, shared_obs, rewards, dones, info, available_actions = wrapper.step(discrete_actions)
            completed_steps = step_id + 1
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

        if args_cli.result_file is not None:
            result = _reset_diagnostics(wrapper, available_actions, completed_steps)
            result_path = Path(args_cli.result_file)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        print("[OK] assignment HARL wrapper smoke passed")
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
