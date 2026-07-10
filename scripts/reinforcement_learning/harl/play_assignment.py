# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

# python -u scripts\reinforcement_learning\harl\play_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --dir "results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_1m_len320_night\seed-00001-2026-06-06-22-31-18\best_model" --max_steps 320 --print_steps 320 --stop_on_done--headless



"""Bounded assignment-mode HARL play/eval smoke."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any

import torch

REPO_ROOT = Path(__file__).resolve().parents[3]
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
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional assignment scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG)

parser = argparse.ArgumentParser(
    description="Play an assignment-based HARL checkpoint with bounded steps.",
    parents=[pre_parser],
)
parser.add_argument("--algorithm", type=str, default="happo", choices=["happo", "hatrpo", "haa2c"], help="HARL algorithm.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
parser.add_argument("--dir", type=str, required=True, help="Assignment-mode model directory.")
parser.add_argument(
    "--assignment_checkpoint_ablation",
    type=str,
    choices=("lifecycle_contract_c_checkpoint_to_lifecycle_ablation_evaluation_v1",),
    default=None,
    help="Explicit validator-owned lifecycle checkpoint ablation policy.",
)
parser.add_argument(
    "--allow_unversioned_legacy_checkpoint",
    action="store_true",
    help="Explicitly allow resolver-disabled legacy actor evaluation without native metadata.",
)
parser.add_argument("--max_steps", type=int, default=32, help="Maximum number of deterministic play steps.")
parser.add_argument(
    "--assignment_rl",
    action="store_true",
    help="Accepted for explicitness; this dedicated script always runs assignment mode.",
)
parser.add_argument("--print_steps", type=int, default=8, help="Number of leading steps to print in detail.")
parser.add_argument(
    "--diagnostic_interval",
    type=int,
    default=1,
    help="Print assignment diagnostics every N steps. Use 1 to print every step.",
)
parser.add_argument(
    "--stop_on_done",
    action="store_true",
    help="Stop play when any environment finishes one episode.",
)


AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli, hydra_args = parser.parse_known_args()
if args_cli.scenario_config is not None:
    validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)
sys.argv = [sys.argv[0]] + hydra_args


def _warm_start_torch_cuda(args: argparse.Namespace) -> None:
    """Initialize PyTorch/cuBLAS before Isaac Kit takes over the CUDA context."""
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

from harl.algorithms.actors import ALGO_REGISTRY
from harl.utils.models_tools import init_device

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_contract import CompatibilityPurpose
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_load import (
    build_assignment_evaluation_contract_manifest,
    load_assignment_checkpoint,
)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.utils.hydra import hydra_task_config


algorithm = args_cli.algorithm.lower()
agent_cfg_entry_point = f"harl_{algorithm}_cfg_entry_point"


def _mean_float(value: Any, fallback: float | None = None) -> float | None:
    if value is None:
        return fallback
    if isinstance(value, torch.Tensor):
        if value.numel() == 0:
            return fallback
        return float(value.detach().to(dtype=torch.float32).mean().cpu().item())
    if isinstance(value, (int, float, bool)):
        return float(value)
    return fallback


def _info_log_scalar(info: Any, key: str, fallback: float | None = None) -> float | None:
    if not isinstance(info, dict):
        return fallback
    log = info.get("log")
    if not isinstance(log, dict):
        return fallback
    return _mean_float(log.get(key), fallback=fallback)


def _format_optional(value: float | None) -> str:
    return "nan" if value is None else f"{value:.6f}"


def _round_nested(value: Any, digits: int = 4) -> Any:
    if isinstance(value, list):
        return [_round_nested(item, digits=digits) for item in value]
    if isinstance(value, float):
        return round(value, digits) if math.isfinite(value) else value
    return value


def _tensor_list(tensor: torch.Tensor | None, digits: int | None = None) -> list:
    if tensor is None:
        return []
    values = tensor.detach().cpu().tolist()
    return _round_nested(values, digits=digits) if digits is not None else values


def _ids_from_mask(mask: torch.Tensor) -> list[list[int]]:
    return [torch.nonzero(mask[env_id], as_tuple=False).flatten().detach().cpu().tolist() for env_id in range(mask.shape[0])]


def _available_ids_per_agent(available_actions: torch.Tensor) -> list[list[list[int]]]:
    available = available_actions.to(dtype=torch.bool)
    return [
        [
            torch.nonzero(available[env_id, agent_id], as_tuple=False).flatten().detach().cpu().tolist()
            for agent_id in range(available.shape[1])
        ]
        for env_id in range(available.shape[0])
    ]


def _collect_pre_step_diagnostics(wrapper, available_actions: torch.Tensor, actions: torch.Tensor) -> dict[str, Any]:
    problem = wrapper.unwrapped.get_assignment_problem()
    covered_mask = problem["viewpoints_covered"].to(dtype=torch.bool).clone()
    uncovered_mask = ~covered_mask
    raw_ids = actions[..., 0].to(dtype=torch.long)

    selected_available = _selected_available_from_mask(available_actions, raw_ids, wrapper.num_viewpoints)
    distance_to_selected = _distance_to_selected_viewpoint(problem, raw_ids, wrapper.num_viewpoints)
    return {
        "covered_ids": _ids_from_mask(covered_mask),
        "uncovered_ids": _ids_from_mask(uncovered_mask),
        "available_ids_per_agent": _available_ids_per_agent(available_actions),
        "selected_available": selected_available,
        "distance_to_selected_viewpoint": distance_to_selected,
        "pre_covered_mask": covered_mask,
    }


def _selected_available_from_mask(
    available_actions: torch.Tensor,
    raw_ids: torch.Tensor,
    num_viewpoints: int,
) -> torch.Tensor:
    safe_ids = raw_ids.clamp(min=0, max=num_viewpoints).unsqueeze(-1)
    selected_available = torch.gather(available_actions.to(dtype=torch.bool), dim=2, index=safe_ids).squeeze(-1)
    in_range = (raw_ids >= 0) & (raw_ids <= num_viewpoints)
    return selected_available & in_range


def _distance_to_selected_viewpoint(problem: dict, raw_ids: torch.Tensor, num_viewpoints: int) -> torch.Tensor:
    cost_matrix = problem["cost_matrix"]
    distance = torch.full(raw_ids.shape, float("nan"), dtype=torch.float32, device=cost_matrix.device)
    if num_viewpoints <= 0:
        return distance
    valid_viewpoint = (raw_ids >= 0) & (raw_ids < num_viewpoints)
    safe_ids = raw_ids.clamp(min=0, max=num_viewpoints - 1).unsqueeze(-1)
    selected_distance = torch.gather(cost_matrix, dim=2, index=safe_ids).squeeze(-1)
    return torch.where(valid_viewpoint, selected_distance, distance)


def _newly_covered_ids(pre_covered_mask: torch.Tensor, wrapper) -> list[list[int]]:
    post_problem = wrapper.unwrapped.get_assignment_problem()
    post_covered_mask = post_problem["viewpoints_covered"].to(dtype=torch.bool)
    newly_covered = (~pre_covered_mask) & post_covered_mask
    return _ids_from_mask(newly_covered)


def _build_and_load_assignment_actors(wrapper, algo_args: dict, model_dir: Path, device: torch.device):
    actor_args = {**algo_args["model"], **algo_args["algo"]}
    actors = []
    for agent_id, agent_name in enumerate(wrapper.agents):
        actor = ALGO_REGISTRY[algorithm](
            actor_args,
            wrapper.observation_space[agent_id],
            wrapper.action_space[agent_id],
            device=device,
        )
        actors.append(actor)

        act_layer = getattr(actor.actor, "act", None)
        action_type = getattr(act_layer, "action_type", None)
        action_head = getattr(act_layer, "action_out", None)
        action_head_name = action_head.__class__.__name__ if action_head is not None else None
        if action_type != "Discrete" or action_head_name != "Categorical":
            raise RuntimeError(
                "assignment play expected HARL Categorical actor for Discrete action space, "
                f"got action_type={action_type}, distribution_head={action_head_name}"
            )
    current_manifest = build_assignment_evaluation_contract_manifest(
        wrapper=wrapper,
        actors=actors,
        algo_args=algo_args,
        algorithm_name=algorithm,
    )
    purpose = (
        CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION
        if args_cli.assignment_checkpoint_ablation is not None
        else CompatibilityPurpose.NORMAL_EVALUATION
    )
    result = load_assignment_checkpoint(
        checkpoint_directory=model_dir,
        purpose=purpose,
        current_manifest=current_manifest,
        actor_modules=tuple(
            (name, actors[index].actor)
            for index, name in enumerate(wrapper.agents)
        ),
        explicit_ablation_name=args_cli.assignment_checkpoint_ablation,
        allow_unversioned_legacy_fallback=bool(
            args_cli.allow_unversioned_legacy_checkpoint
        ),
    )
    for actor in actors:
        actor.prep_rollout()
    print(
        "[INFO]: validated assignment checkpoint "
        f"kind={result.checkpoint_kind} generation={result.checkpoint_generation} "
        f"purpose={result.load_purpose.value} legacy_fallback={result.legacy_fallback_used}"
    )
    return actors, result


def _assert_available_actions(wrapper, available_actions: torch.Tensor | None) -> None:
    if available_actions is None:
        raise RuntimeError("assignment play requires available_actions, got None")
    expected_shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints + 1)
    if tuple(available_actions.shape) != expected_shape:
        raise RuntimeError(f"available_actions shape mismatch: expected {expected_shape}, got {tuple(available_actions.shape)}")


def _print_step_diagnostics(
    step_id: int,
    wrapper,
    rewards: torch.Tensor,
    info: dict,
    *,
    pre_step_diagnostics: dict[str, Any],
    selected_action_prob: torch.Tensor,
    newly_covered_ids: list[list[int]],
) -> None:
    assignment = wrapper.last_assignment
    duplicate_count = wrapper.last_duplicate_count
    noop_count = wrapper.last_noop_count
    valid_action_count = wrapper.last_valid_action_count
    coverage_ratio = _info_log_scalar(info, "coverage_ratio")
    new_viewpoints = _info_log_scalar(info, "new_viewpoints")
    mean_reward = _info_log_scalar(info, "mean_reward", fallback=_mean_float(rewards))
    print(
        f"[STEP {step_id:03d}] "
        f"assignment={_tensor_list(assignment)} "
        f"noop_count={_tensor_list(noop_count, digits=2)} "
        f"duplicate_count={_tensor_list(duplicate_count, digits=2)} "
        f"valid_action_count={_tensor_list(valid_action_count, digits=2)} "
        f"selected_available={_tensor_list(pre_step_diagnostics['selected_available'])} "
        f"selected_action_prob={_tensor_list(selected_action_prob, digits=4)} "
        f"distance_to_selected_viewpoint={_tensor_list(pre_step_diagnostics['distance_to_selected_viewpoint'], digits=4)} "
        f"coverage_ratio={_format_optional(coverage_ratio)} "
        f"new_viewpoints={_format_optional(new_viewpoints)} "
        f"mean_reward={_format_optional(mean_reward)}"
    )
    print(
        "          "
        f"covered_ids={pre_step_diagnostics['covered_ids']} "
        f"uncovered_ids={pre_step_diagnostics['uncovered_ids']} "
        f"available_ids_per_agent={pre_step_diagnostics['available_ids_per_agent']} "
        f"newly_covered_ids={newly_covered_ids}"
    )


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: dict) -> None:
    if args_cli.max_steps <= 0:
        raise ValueError("--max_steps must be positive")
    if args_cli.num_envs <= 0:
        raise ValueError("--num_envs must be positive")
    if args_cli.diagnostic_interval <= 0:
        raise ValueError("--diagnostic_interval must be positive")

    if not args_cli.assignment_rl:
        print("[INFO]: play_assignment.py is assignment-only; proceeding in assignment mode.")
    print(
        "[WARN]: Do not use old 9D continuous checkpoints or assignment checkpoints trained with a different "
        "fixed-N viewpoint count with this assignment play path."
    )

    model_dir = Path(args_cli.dir).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory does not exist: {model_dir}")

    env_cfg.scene.num_envs = args_cli.num_envs
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed
    if args_cli.scenario_config is not None:
        apply_scenario_config_to_env_cfg(env_cfg, args_cli)
        print(f"[INFO]: Assignment play scenario_config applied: {getattr(env_cfg, 'scenario_config_path', None)}")

    wrapper = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        device = init_device(agent_cfg["device"])
        actors, checkpoint_load_result = _build_and_load_assignment_actors(
            wrapper,
            agent_cfg,
            model_dir,
            device,
        )

        print(
            "[INFO]: Assignment play env "
            f"num_envs={wrapper.num_envs} num_agents={wrapper.num_agents} "
            f"num_viewpoints={wrapper.num_viewpoints} noop_id={wrapper.noop_action_id} "
            f"action_spaces={wrapper.action_space}"
        )

        reset_kwargs = {"seed": args_cli.seed} if args_cli.seed is not None else {}
        obs, _, available_actions = wrapper.reset(**reset_kwargs)
        _assert_available_actions(wrapper, available_actions)
        print(f"[INFO]: reset available_actions shape={tuple(available_actions.shape)} device={available_actions.device}")

        actions = make_harl_action_tensor(wrapper.num_envs, wrapper.action_space, device=wrapper.device)
        rnn_hidden_size = agent_cfg["model"]["hidden_sizes"][-1]
        recurrent_n = agent_cfg["model"]["recurrent_n"]
        rnn_states = torch.zeros(
            (wrapper.num_envs, wrapper.num_agents, recurrent_n, rnn_hidden_size),
            dtype=torch.float32,
            device=device,
        )
        masks = torch.ones((wrapper.num_envs, wrapper.num_agents, 1), dtype=torch.float32, device=device)
        completed_step = args_cli.max_steps

        for step_id in range(1, args_cli.max_steps + 1):
            actions.zero_()
            selected_action_prob = torch.full(
                (wrapper.num_envs, wrapper.num_agents),
                float("nan"),
                dtype=torch.float32,
                device=wrapper.device,
            )
            with torch.inference_mode():
                for agent_id, agent_name in enumerate(wrapper.agents):
                    if available_actions is None:
                        raise RuntimeError("available_actions unexpectedly became None")
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
                    action_log_prob, _, _ = actors[agent_id].evaluate_actions(
                        agent_obs,
                        agent_rnn_states,
                        action,
                        agent_masks,
                        agent_available_actions,
                    )
                    action_width = action.shape[-1]
                    actions[:, agent_id, :action_width] = action.to(device=actions.device)
                    rnn_states[:, agent_id] = rnn_state
                    selected_action_prob[:, agent_id] = torch.exp(action_log_prob.squeeze(-1)).to(
                        device=wrapper.device,
                        dtype=torch.float32,
                    )

            pre_step_diagnostics = _collect_pre_step_diagnostics(wrapper, available_actions, actions)
            obs, _, rewards, dones, info, available_actions = wrapper.step(actions)
            _assert_available_actions(wrapper, available_actions)
            newly_covered_ids = _newly_covered_ids(pre_step_diagnostics["pre_covered_mask"], wrapper)

            if (
                step_id <= args_cli.print_steps
                or step_id % args_cli.diagnostic_interval == 0
                or step_id == args_cli.max_steps
            ):
                _print_step_diagnostics(
                    step_id,
                    wrapper,
                    rewards,
                    info,
                    pre_step_diagnostics=pre_step_diagnostics,
                    selected_action_prob=selected_action_prob,
                    newly_covered_ids=newly_covered_ids,
                )

            dones_env = torch.all(dones, dim=1)


            if args_cli.stop_on_done and bool(dones_env.any()):
                completed_step = step_id
                print(
                    f"[OK] episode completed at step={step_id} "
                    f"done_envs={torch.nonzero(dones_env, as_tuple=False).flatten().detach().cpu().tolist()}"
                )
                break


            masks = torch.ones((wrapper.num_envs, wrapper.num_agents, 1), dtype=torch.float32, device=device)
            if bool(dones_env.any()):
                masks[dones_env] = 0.0
                rnn_states[dones_env] = torch.zeros(
                    (int(dones_env.sum().item()), wrapper.num_agents, recurrent_n, rnn_hidden_size),
                    dtype=torch.float32,
                    device=device,
                )

        print(f"[OK] assignment play smoke completed steps={completed_step}, max_steps={args_cli.max_steps}")
    finally:
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
