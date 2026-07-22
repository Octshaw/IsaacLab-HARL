# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

# python -u scripts\reinforcement_learning\harl\play_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --dir "results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_1m_len320_night\seed-00001-2026-06-06-22-31-18\best_model" --max_steps 320 --print_steps 320 --stop_on_done--headless



"""Bounded assignment-mode HARL play/eval smoke."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import math
from pathlib import Path
import subprocess
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
from assignment_playback_attribution_diagnostics import (
    OUTPUT_FILENAMES as ASSIGNMENT_ATTRIBUTION_OUTPUT_FILENAMES,
    SCHEMA_VERSION as ASSIGNMENT_ATTRIBUTION_SCHEMA_VERSION,
    capture_assignment_playback_physical_snapshot,
    format_assignment_playback_attribution_row,
    make_assignment_playback_attribution_collector_if_enabled,
    stack_assignment_controller_actions,
    validate_assignment_playback_attribution_cli,
)

from isaaclab.app import AppLauncher


PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES = (
    "baseline_identity",
    "pose_cycle_forward",
    "pose_cycle_reverse",
)


def _validate_initial_condition_prelaunch_cli(
    *,
    profile_id: str | None,
    attribution_logging_enabled: bool,
    attribution_output_dir: str | Path | None,
) -> None:
    """Preserve early CLI failures without importing the task package."""

    if profile_id is None:
        return
    if profile_id not in PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES:
        raise ValueError(
            f"unknown initial-condition profile {profile_id!r}; "
            f"expected one of {PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES!r}"
        )
    if not attribution_logging_enabled:
        raise ValueError(
            "--assignment_initial_condition_profile requires "
            "--log_assignment_proposal_effective"
        )
    if attribution_output_dir is None:
        raise ValueError(
            "--assignment_initial_condition_profile requires "
            "--assignment_proposal_effective_output_dir"
        )
    output_path = Path(attribution_output_dir).expanduser().resolve()
    if output_path.exists() and not output_path.is_dir():
        raise NotADirectoryError(
            f"initial-condition attribution output is not a directory: {output_path}"
        )
    if output_path.exists():
        collisions = tuple(output_path.iterdir())
        if collisions:
            raise FileExistsError(
                f"explicit initial-condition attribution output must be new/empty: {collisions[0]}"
            )


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
parser.add_argument(
    "--log_assignment_proposal_effective",
    action="store_true",
    help="Write playback-only proposal/effective attribution diagnostics.",
)
parser.add_argument(
    "--assignment_proposal_effective_output_dir",
    type=str,
    default=None,
    help="New output directory for proposal/effective attribution files.",
)
parser.add_argument(
    "--print_assignment_proposal_effective",
    action="store_true",
    help="Print compact per-robot proposal/effective attribution rows.",
)
parser.add_argument(
    "--assignment_initial_condition_profile",
    type=str,
    choices=PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES,
    default=None,
    help="Optional controlled playback-only robot start-pose profile.",
)


AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
args_cli, hydra_args = parser.parse_known_args()
if args_cli.scenario_config is not None:
    validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)
ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR = validate_assignment_playback_attribution_cli(
    log_enabled=bool(args_cli.log_assignment_proposal_effective),
    print_enabled=bool(args_cli.print_assignment_proposal_effective),
    output_dir=args_cli.assignment_proposal_effective_output_dir,
)
_validate_initial_condition_prelaunch_cli(
    profile_id=args_cli.assignment_initial_condition_profile,
    attribution_logging_enabled=bool(args_cli.log_assignment_proposal_effective),
    attribution_output_dir=args_cli.assignment_proposal_effective_output_dir,
)
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
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition import (
    INITIAL_CONDITION_MANIFEST_FILENAME,
    INITIAL_CONDITION_PROFILE_CHOICES,
    InitialConditionRunProvenance,
    build_initial_condition_manifest,
    make_initial_condition_request,
    make_playback_policy_interface_contract,
    validate_initial_condition_output_files,
    validate_initial_condition_playback_cli,
    validate_initial_condition_runtime_interface,
    write_initial_condition_manifest_atomic,
)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_adapter import make_harl_action_tensor
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_contract import CompatibilityPurpose
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_load import (
    build_assignment_evaluation_contract_manifest,
    load_assignment_checkpoint,
)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import make_assignment_harl_env
from isaaclab_tasks.utils.hydra import hydra_task_config


if PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES != INITIAL_CONDITION_PROFILE_CHOICES:
    raise RuntimeError(
        "pre-AppLauncher initial-condition profile vocabulary differs from the canonical registry: "
        f"prelaunch={PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES!r}, "
        f"canonical={INITIAL_CONDITION_PROFILE_CHOICES!r}"
    )
validate_initial_condition_playback_cli(
    profile_id=args_cli.assignment_initial_condition_profile,
    attribution_logging_enabled=bool(args_cli.log_assignment_proposal_effective),
    attribution_output_dir=args_cli.assignment_proposal_effective_output_dir,
)


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


def _resolved_bool(mapping: dict, key: str, *, field: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must resolve to a boolean, got {value!r}")
    return value


def _attach_initial_condition_request(env_cfg, agent_cfg: dict) -> None:
    profile_id = args_cli.assignment_initial_condition_profile
    if profile_id is None:
        return
    existing_profile = getattr(env_cfg, "assignment_initial_condition_profile", None)
    existing_request = getattr(env_cfg, "assignment_initial_condition_request", None)
    if existing_profile is not None or existing_request is not None:
        raise ValueError(
            "controlled initial conditions must be selected only through "
            "--assignment_initial_condition_profile; low-level profile/request values are not accepted"
        )
    model_cfg = agent_cfg.get("model")
    algo_cfg = agent_cfg.get("algo")
    device_cfg = agent_cfg.get("device")
    if not isinstance(model_cfg, dict) or not isinstance(algo_cfg, dict) or not isinstance(device_cfg, dict):
        raise ValueError("controlled initial-condition playback requires resolved HARL model/algo/device mappings")
    policy_interface = make_playback_policy_interface_contract(
        assignment_lifecycle_profile=str(getattr(env_cfg, "assignment_lifecycle_profile", "legacy")),
        algorithm=algorithm,
        use_recurrent_policy=_resolved_bool(
            model_cfg, "use_recurrent_policy", field="agent.model.use_recurrent_policy"
        ),
        use_naive_recurrent_policy=_resolved_bool(
            model_cfg, "use_naive_recurrent_policy", field="agent.model.use_naive_recurrent_policy"
        ),
        share_param=_resolved_bool(algo_cfg, "share_param", field="agent.algo.share_param"),
        cuda_deterministic=_resolved_bool(
            device_cfg, "cuda_deterministic", field="agent.device.cuda_deterministic"
        ),
    )
    request = make_initial_condition_request(
        profile_id=profile_id,
        task_id=str(args_cli.task),
        repository_root=REPO_ROOT,
        policy_interface_contract=policy_interface,
    )
    env_cfg.assignment_initial_condition_profile = profile_id
    env_cfg.assignment_initial_condition_request = request


def _validated_initial_condition_result(wrapper):
    profile_id = args_cli.assignment_initial_condition_profile
    if profile_id is None:
        return None
    accessor = getattr(wrapper.unwrapped, "get_assignment_initial_condition_result", None)
    if not callable(accessor):
        raise RuntimeError("assignment environment does not expose the validated initial-condition result")
    result = accessor()
    if result is None:
        raise RuntimeError(f"explicit initial-condition profile {profile_id!r} produced no validated result")
    validate_initial_condition_runtime_interface(
        result,
        ordered_agent_ids=wrapper.agents,
        observation_manifest=wrapper.assignment_observation_schema_manifest,
    )
    return result


def _repository_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = completed.stdout.strip()
    if len(commit) != 40:
        raise RuntimeError(f"unexpected repository commit identity: {commit!r}")
    return commit


def _write_initial_condition_manifest(
    *,
    result,
    checkpoint_load_result,
    model_dir: Path,
) -> Path:
    if ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR is None:
        raise RuntimeError("explicit initial-condition profile has no attribution output directory")
    validate_initial_condition_output_files(
        ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR,
        attribution_filenames=ASSIGNMENT_ATTRIBUTION_OUTPUT_FILENAMES,
        manifest_expected=False,
    )
    provenance = InitialConditionRunProvenance(
        repository_commit=_repository_commit(),
        selected_cli_field="--assignment_initial_condition_profile",
        profile_id=result.condition_contract.profile_id,
        resolved_absolute_source_paths=result.resolved_absolute_source_paths,
        command_seed=args_cli.seed,
        deterministic_actor_mode=True,
        checkpoint_directory=str(model_dir),
        checkpoint_child=model_dir.name,
        checkpoint_kind=checkpoint_load_result.checkpoint_kind,
        checkpoint_generation=checkpoint_load_result.checkpoint_generation,
        assignment_checkpoint_fingerprint=checkpoint_load_result.contract_fingerprint,
        load_purpose=checkpoint_load_result.load_purpose.value,
        legacy_fallback=bool(checkpoint_load_result.legacy_fallback_used),
        attribution_schema=ASSIGNMENT_ATTRIBUTION_SCHEMA_VERSION,
        created_timestamp=datetime.now(timezone.utc).isoformat(),
    )
    manifest = build_initial_condition_manifest(result, provenance)
    manifest_path = ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR / INITIAL_CONDITION_MANIFEST_FILENAME
    write_initial_condition_manifest_atomic(manifest_path, manifest)
    validate_initial_condition_output_files(
        ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR,
        attribution_filenames=ASSIGNMENT_ATTRIBUTION_OUTPUT_FILENAMES,
        manifest_expected=True,
    )
    return manifest_path


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
    _attach_initial_condition_request(env_cfg, agent_cfg)

    wrapper = None
    attribution_collector = None
    try:
        wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
        initial_condition_result = _validated_initial_condition_result(wrapper)
        device = init_device(agent_cfg["device"])
        actors, checkpoint_load_result = _build_and_load_assignment_actors(
            wrapper,
            agent_cfg,
            model_dir,
            device,
        )
        if initial_condition_result is not None:
            mapping_text = ",".join(
                f"{robot_id}->{slot_id}"
                for robot_id, slot_id in initial_condition_result.condition_contract.robot_to_slot_mapping
            )
            print(
                "[INFO]: assignment initial condition "
                f"profile={initial_condition_result.condition_contract.profile_id} "
                f"fingerprint={initial_condition_result.condition_fingerprint} "
                f"mapping={mapping_text}"
            )

        print(
            "[INFO]: Assignment play env "
            f"num_envs={wrapper.num_envs} num_agents={wrapper.num_agents} "
            f"num_viewpoints={wrapper.num_viewpoints} noop_id={wrapper.noop_action_id} "
            f"action_spaces={wrapper.action_space}"
        )

        attribution_collector = make_assignment_playback_attribution_collector_if_enabled(
            log_enabled=bool(args_cli.log_assignment_proposal_effective),
            print_enabled=bool(args_cli.print_assignment_proposal_effective),
            output_dir=ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR,
            method_name=algorithm,
            num_envs=wrapper.num_envs,
            num_robots=wrapper.num_agents,
            num_tasks=wrapper.num_viewpoints,
            robot_names=wrapper.agents,
            noop_raw_id=wrapper.noop_action_id,
            distance_dwell_thresholds=getattr(wrapper.unwrapped, "scan_pos_tolerance", None),
        )

        reset_kwargs = {"seed": args_cli.seed} if args_cli.seed is not None else {}
        obs, _, available_actions = wrapper.reset(**reset_kwargs)
        _assert_available_actions(wrapper, available_actions)
        if attribution_collector is not None:
            attribution_collector.reset_envs(episode_ids=torch.zeros(wrapper.num_envs, dtype=torch.long))
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
            attribution_pre_state = None
            if attribution_collector is not None:
                attribution_pre_state = capture_assignment_playback_physical_snapshot(
                    wrapper.unwrapped.get_assignment_problem()
                )
            obs, _, rewards, dones, info, available_actions = wrapper.step(actions)
            _assert_available_actions(wrapper, available_actions)
            newly_covered_ids = _newly_covered_ids(pre_step_diagnostics["pre_covered_mask"], wrapper)
            dones_env = torch.all(dones, dim=1)

            attribution_rows: list[dict[str, Any]] = []
            if attribution_collector is not None:
                lifecycle_resolution = wrapper.get_last_assignment_lifecycle_resolution()
                if lifecycle_resolution is None:
                    raise RuntimeError("assignment attribution requires a lifecycle-resolution payload after wrapper.step")
                if attribution_pre_state is None:
                    raise RuntimeError("assignment attribution pre-state was not captured")
                if wrapper.last_assignment is None or wrapper.last_env_actions is None:
                    raise RuntimeError("assignment attribution requires wrapper controller assignments and actions")
                attribution_post_state = capture_assignment_playback_physical_snapshot(
                    wrapper.unwrapped.get_assignment_problem()
                )
                controller_actions = stack_assignment_controller_actions(
                    wrapper.last_env_actions,
                    wrapper.agents,
                )
                attribution_rows = attribution_collector.record_decision(
                    raw_actions=actions,
                    selected_action_probabilities=selected_action_prob,
                    pre_state=attribution_pre_state,
                    lifecycle_resolution=lifecycle_resolution,
                    controller_assignment=wrapper.last_assignment,
                    controller_actions=controller_actions,
                    post_state=attribution_post_state,
                    post_state_pre_reset_available=~dones_env,
                    dones=dones_env,
                )

            print_this_step = (
                step_id <= args_cli.print_steps
                or step_id % args_cli.diagnostic_interval == 0
                or step_id == args_cli.max_steps
            )
            if print_this_step:
                _print_step_diagnostics(
                    step_id,
                    wrapper,
                    rewards,
                    info,
                    pre_step_diagnostics=pre_step_diagnostics,
                    selected_action_prob=selected_action_prob,
                    newly_covered_ids=newly_covered_ids,
                )
                if args_cli.print_assignment_proposal_effective:
                    for row in attribution_rows:
                        print(format_assignment_playback_attribution_row(row))

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

        if attribution_collector is not None:
            attribution_collector.finalize()
        if initial_condition_result is not None:
            manifest_path = _write_initial_condition_manifest(
                result=initial_condition_result,
                checkpoint_load_result=checkpoint_load_result,
                model_dir=model_dir,
            )
            print(f"[INFO]: assignment initial-condition manifest written: {manifest_path}")
        print(f"[OK] assignment play smoke completed steps={completed_step}, max_steps={args_cli.max_steps}")
    finally:
        if attribution_collector is not None:
            attribution_collector.finalize()
        if wrapper is not None:
            wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
