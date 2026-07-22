# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Train an algorithm."""

import argparse
import sys
import time
from pathlib import Path

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
from assignment_initial_condition import validate_initial_condition_training_config

from isaaclab.app import AppLauncher

pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional assignment scenario YAML/JSON config.")
pre_args, _ = pre_parser.parse_known_args()
SCENARIO_CONFIG = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
SCENARIO_DEFAULTS = smoke_defaults_from_config(SCENARIO_CONFIG) if "--assignment_rl" in sys.argv else {}

parser = argparse.ArgumentParser(description="Train an RL agent with HARL.", parents=[pre_parser])
parser.add_argument("--video", action="store_true", help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=500, help="Length of the recorded video (in steps).")
parser.add_argument("--video_interval", type=int, default=20000, help="Interval between video recordings (in steps).")
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument("--seed", type=int, default=1, help="Seed used for the environment")
parser.add_argument("--save_interval", type=int, default=None, help="How often to save the model")
parser.add_argument("--log_interval", type=int, default=None, help="How often to log outputs")
parser.add_argument("--exp_name", type=str, default="test", help="Name of the Experiment")
parser.add_argument("--num_env_steps", type=int, default=None, help="RL Policy training iterations.")
parser.add_argument("--dir", type=str, default=None, help="folder with trained models")
parser.add_argument(
    "--assignment_rl",
    action="store_true",
    help="Use assignment-based Discrete viewpoint actions instead of the scan env's raw 9D action space.",
)
parser.add_argument(
    "--assignment_episode_length",
    type=int,
    default=None,
    help="Override HARL train.episode_length for assignment RL only, e.g. 300 for the N=50 smoke scenario.",
)
parser.add_argument(
    "--acknowledge-weight-continuation-reset",
    action="store_true",
    help=(
        "Required with assignment --dir. Acknowledge that actor/critic optimizers, counters, "
        "best-reward state, RNG, environment/resolver state, and rollout buffers reset."
    ),
)

parser.add_argument(
    "--algorithm",
    type=str,
    default="happo",
    choices=[
        "happo",
        "hatrpo",
        "haa2c",
        "mappo",
        "mappo_unshare",
    ],
    help="Algorithm name. Choose from: happo, hatrpo, haa2c, mappo, and mappo_unshare.",
)

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
parser.set_defaults(**SCENARIO_DEFAULTS)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
if args_cli.scenario_config is not None and not args_cli.assignment_rl:
    raise ValueError("--scenario_config is currently supported only with --assignment_rl in train.py")
if args_cli.assignment_episode_length is not None and not args_cli.assignment_rl:
    raise ValueError("--assignment_episode_length is supported only with --assignment_rl")
if args_cli.acknowledge_weight_continuation_reset and (
    not args_cli.assignment_rl or args_cli.dir is None
):
    raise ValueError(
        "--acknowledge-weight-continuation-reset requires --assignment_rl and --dir"
    )
if args_cli.assignment_rl and args_cli.dir is not None and not args_cli.acknowledge_weight_continuation_reset:
    raise ValueError(
        "Assignment --dir uses validated weight continuation and requires "
        "--acknowledge-weight-continuation-reset."
    )
if args_cli.assignment_rl and args_cli.scenario_config is not None:
    validate_smoke_args(args_cli, repo_root=REPO_ROOT, config=SCENARIO_CONFIG)
# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args


def _warm_start_torch_cuda(args: argparse.Namespace):
    """Initialize PyTorch/cuBLAS before Isaac Kit takes over the CUDA context."""
    device_arg = str(getattr(args, "device", "cuda:0")).lower()
    if device_arg == "cpu" or not device_arg.startswith("cuda"):
        return

    import torch

    if not torch.cuda.is_available():
        return

    device = torch.device(device_arg)
    torch.cuda.set_device(device)
    probe = torch.zeros((1, 1), device=device)
    layer = torch.nn.Linear(1, 1).to(device)
    _ = layer(probe)
    torch.cuda.synchronize(device)


_warm_start_torch_cuda(args_cli)


def _finalize_record_video_wrappers(runner):
    """Stop Gymnasium RecordVideo wrappers hidden inside HARL wrappers."""
    seen = set()
    stack = [getattr(runner, "env", None)]
    while stack:
        env = stack.pop()
        if env is None or id(env) in seen:
            continue
        seen.add(id(env))

        if getattr(env, "recording", False) and hasattr(env, "stop_recording"):
            try:
                env.stop_recording()
            except Exception as exc:
                print(f"[WARN]: Could not finalize video recorder: {exc}")

        for child_attr in ("env", "_env"):
            child = getattr(env, child_attr, None)
            if child is not None:
                stack.append(child)

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import os

from harl.runners import RUNNER_REGISTRY

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_training import (
    apply_assignment_episode_length_override,
    register_assignment_harl_runner,
    validate_assignment_lifecycle_policy_sequence,
)
from isaaclab_tasks.utils.hydra import hydra_task_config

algorithm = args_cli.algorithm.lower()
agent_cfg_entry_point = f"harl_{algorithm}_cfg_entry_point"


@hydra_task_config(args_cli.task, agent_cfg_entry_point)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: dict):

    validate_initial_condition_training_config(env_cfg)

    args = args_cli.__dict__

    args["env"] = "isaaclab"

    args["algo"] = args["algorithm"]

    if args["assignment_rl"]:
        register_assignment_harl_runner(RUNNER_REGISTRY, args["algo"])
        print("[INFO]: --assignment_rl enabled for HARL training.")
        print(
            "[WARN]: Assignment RL uses Discrete/Categorical policies; old 9D continuous checkpoints and "
            "assignment checkpoints trained with a different fixed-N viewpoint count are incompatible."
        )
        if args["dir"] is not None:
            print(
                f"[WARN]: --dir={args['dir']} must point to an assignment-RL checkpoint with the same fixed-N "
                "viewpoint count, not a 9D continuous checkpoint."
            )
        if args["exp_name"] == "test":
            print("[WARN]: Consider using an assignment-specific --exp_name to avoid mixing continuous and assignment runs.")

    algo_args = agent_cfg

    algo_args["eval"]["use_eval"] = False
    algo_args["train"]["n_rollout_threads"] = args["num_envs"]
    algo_args["train"]["num_env_steps"] = args["num_env_steps"]
    algo_args["train"]["eval_interval"] = args["save_interval"]
    algo_args["train"]["log_interval"] = args["log_interval"]
    algo_args["train"]["model_dir"] = args["dir"]
    if args["assignment_rl"]:
        applied_episode_length = apply_assignment_episode_length_override(
            algo_args,
            args.get("assignment_episode_length"),
        )
        if applied_episode_length is not None:
            print(f"[INFO]: Assignment RL train.episode_length override applied: {applied_episode_length}")
    algo_args["seed"]["specify_seed"] = True
    algo_args["seed"]["seed"] = args["seed"]

    env_args = {}
    if args["assignment_rl"] and args.get("scenario_config") is not None:
        apply_scenario_config_to_env_cfg(env_cfg, args)
        print(f"[INFO]: Assignment RL scenario_config applied: {getattr(env_cfg, 'scenario_config_path', None)}")
    env_cfg.scene.num_envs = args["num_envs"]
    env_args["task"] = args["task"]
    env_args["config"] = env_cfg
    env_args["assignment_rl"] = args["assignment_rl"]
    env_args["algorithm"] = args["algo"]
    env_args["acknowledge_weight_continuation_reset"] = bool(
        args.get("acknowledge_weight_continuation_reset", False)
    )
    hms_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    env_args["video_settings"] = {
        "video": args_cli.video,
        "video_length": args["video_length"],
        "video_interval": args["video_interval"],
        "log_dir": os.path.join(
            algo_args["logger"]["log_dir"],
            "isaaclab",
            args["task"],
            args["algorithm"],
            args["exp_name"],
            "-".join(["seed-{:0>5}".format(agent_cfg["seed"]["seed"]), hms_time]),
            "videos",
        ),
    }

    if args["assignment_rl"]:
        sequence_contract = validate_assignment_lifecycle_policy_sequence(
            algo_args=algo_args,
            env_args=env_args,
        )
        if sequence_contract["policy_sequence_mode"] == "feed_forward":
            print(
                "[INFO]: Assignment lifecycle policy sequence contract: "
                f"{sequence_contract['policy_sequence_contract_version']} "
                f"generator={sequence_contract['supported_actor_buffer_generator']}"
            )

    # create runner

    runner = RUNNER_REGISTRY[args["algo"]](args, algo_args, env_args)
    run_dir = getattr(runner, "run_dir", None)
    save_dir = getattr(runner, "save_dir", None)
    if run_dir is not None:
        print(f"[INFO]: HARL run directory: {run_dir}")
    if save_dir is not None:
        print(f"[INFO]: HARL model directory: {save_dir}")
    try:
        runner.run()
        if hasattr(runner, "save") and save_dir is not None:
            if args["assignment_rl"]:
                runner.save(save_dir, checkpoint_kind="final")
            else:
                runner.save(save_dir)
            print(f"[INFO]: Saved final HARL model to: {save_dir}")
    finally:
        _finalize_record_video_wrappers(runner)
        runner.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
