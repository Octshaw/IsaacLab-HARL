# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""View high-level scan viewpoint assignment behavior in Isaac Sim."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from _windows_runtime_startup import prepare_windows_runtime_args


def _emit(stage: str, **facts):
    """Flush compact facts before Kit shutdown can end this process."""
    print("[RUNTIME_CHECK] " + json.dumps({"stage": stage, "pid": os.getpid(), **facts}, ensure_ascii=True), flush=True)


def _parse_args(app_launcher_type):
    parser = argparse.ArgumentParser(description="Viewer for scan viewpoint assignment solvers.")
    parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0", help="Name of the task.")
    parser.add_argument("--solver", type=str, default="greedy", choices=("random", "nearest", "greedy"), help="Solver name.")
    parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
    parser.add_argument("--seed", type=int, default=None, help="Optional environment seed.")
    parser.add_argument("--duration", type=float, default=None, help="Optional viewer duration in seconds.")
    parser.add_argument("--max_steps", type=int, default=None, help="Optional maximum number of viewer steps.")
    parser.add_argument("--step_rate", type=float, default=5.0, help="Environment steps per second.")
    parser.add_argument("--print_interval", type=int, default=1, help="Print every N environment steps.")
    parser.add_argument("--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations.")
    parser.add_argument("--runtime_check", action="store_true", help="Require CUDA verification and the full step budget.")
    app_launcher_type.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.num_envs <= 0:
        parser.error("--num_envs must be positive")
    if args.max_steps is not None and args.max_steps <= 0:
        parser.error("--max_steps must be positive when provided")
    if args.print_interval <= 0:
        parser.error("--print_interval must be positive")
    if args.runtime_check and (args.max_steps is None or not args.device.startswith("cuda")):
        parser.error("--runtime_check requires --max_steps and an explicit CUDA device (for example --device cuda:0)")
    return args


def _prepare_cuda_before_app(device_arg: str):
    """New shared Windows/CUDA startup preparation; no random numbers or learners."""
    if sys.platform != "win32" or not device_arg.startswith("cuda"):
        return {"performed": False, "reason": "not_windows_cuda", "requested_device": device_arg}
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(f"CUDA requested ({device_arg}), but CUDA is unavailable; no CPU fallback")
    device = torch.device(device_arg)
    torch.cuda.set_device(device)
    left = torch.ones((16, 16), dtype=torch.float32, device=device)
    right = torch.ones((16, 16), dtype=torch.float32, device=device)
    product = left @ right
    torch.cuda.synchronize(device)
    return {"performed": True, "requested_device": device_arg, "actual_device": str(product.device),
            "torch_version": torch.__version__, "torch_source": torch.__file__, "synchronized": True}


def _verify_cuda_after_app(device_arg: str):
    device = torch.device(device_arg)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("Runtime CUDA check requires an available CUDA device; no CPU fallback")
    left = torch.ones((16, 16), dtype=torch.float32, device=device)
    product = left @ left
    total = product.sum()
    finite = torch.isfinite(product).all()
    expected_entries = (product == 16.0).all()
    torch.cuda.synchronize(device)
    value = total.item()
    actual = product.device
    expected_index = device.index if device.index is not None else torch.cuda.current_device()
    if (actual.type != "cuda" or actual.index != expected_index or not finite.item()
            or not expected_entries.item() or value != 4096.0):
        raise RuntimeError(f"CUDA numerical/device check failed: device={actual}, sum={value}")
    _emit("cuda_verified", requested_device=device_arg, actual_device=str(actual), shape=[16, 16],
          expected_entry=16.0, expected_sum=4096.0, actual_sum=value, finite=True,
          all_entries_correct=True, synchronized=True, gpu_name=torch.cuda.get_device_name(actual))


def _validate_assignment(problem: dict, assignment: torch.Tensor):
    expected_shape = (problem["num_envs"], problem["num_agents"])
    if tuple(assignment.shape) != expected_shape:
        raise RuntimeError(f"assignment shape mismatch: expected {expected_shape}, got {tuple(assignment.shape)}")
    if assignment.dtype != torch.long:
        raise RuntimeError(f"assignment dtype mismatch: expected torch.long, got {assignment.dtype}")
    if assignment.device != problem["available_mask"].device:
        raise RuntimeError(
            f"assignment device mismatch: expected {problem['available_mask'].device}, got {assignment.device}"
        )
    if torch.any(assignment < -1) or torch.any(assignment >= problem["num_viewpoints"]):
        raise RuntimeError("assignment contains values outside [-1, num_viewpoints)")


def _validate_actions(env, actions: dict[str, torch.Tensor]):
    expected_device = torch.device(env.device)
    expected_agents = set(env.possible_agents)
    if set(actions.keys()) != expected_agents:
        raise RuntimeError(f"action keys mismatch: expected {sorted(expected_agents)}, got {sorted(actions.keys())}")

    for agent in env.possible_agents:
        expected_shape = (env.num_envs, *env.action_spaces[agent].shape)
        action = actions[agent]
        if tuple(action.shape) != expected_shape:
            raise RuntimeError(f"{agent} action shape mismatch: expected {expected_shape}, got {tuple(action.shape)}")
        if action.device != expected_device:
            raise RuntimeError(f"{agent} action device mismatch: expected {expected_device}, got {action.device}")
        if not torch.isfinite(action).all():
            raise RuntimeError(f"{agent} action contains non-finite values")
        if torch.any(action < -1.0) or torch.any(action > 1.0):
            raise RuntimeError(f"{agent} action contains values outside [-1, 1]")


def _run_environment(args_cli, simulation_app, resources):
    import gymnasium as gym
    import isaaclab_tasks
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.solvers import make_solver
    from isaaclab_tasks.utils import parse_env_cfg

    resources["phase"] = "environment_config"
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed

    if args_cli.runtime_check:
        _emit("environment_config", task_source=isaaclab_tasks.__file__, requested_device=args_cli.device,
              cfg_device=str(env_cfg.sim.device), num_envs=env_cfg.scene.num_envs,
              profile=getattr(env_cfg, "assignment_lifecycle_profile", None))
        if getattr(env_cfg, "assignment_lifecycle_profile", None) != "legacy":
            raise RuntimeError("This bounded viewer check requires the existing default legacy profile")
        if torch.device(env_cfg.sim.device) != torch.device(args_cli.device):
            raise RuntimeError("Requested CUDA device and environment config device differ")
    resources["phase"] = "environment_constructing"
    env = gym.make(args_cli.task, cfg=env_cfg)
    resources["env"] = env
    unwrapped = env.unwrapped
    _emit("environment_created", env_class=f"{type(unwrapped).__module__}.{type(unwrapped).__name__}",
          env_source=sys.modules[type(unwrapped).__module__].__file__, actual_device=str(unwrapped.device),
          cfg_device=str(env_cfg.sim.device), num_envs=unwrapped.num_envs,
          agents=list(unwrapped.possible_agents), profile=getattr(env_cfg, "assignment_lifecycle_profile", None))
    if args_cli.runtime_check and torch.device(unwrapped.device) != torch.device(args_cli.device):
        raise RuntimeError("Actual environment device differs from the requested CUDA device")
    solver = make_solver(args_cli.solver)

    print(f"[INFO]: Agents: {unwrapped.possible_agents}")
    print(f"[INFO]: Observation spaces: {unwrapped.observation_spaces}")
    print(f"[INFO]: Action spaces: {unwrapped.action_spaces}")
    print(
        f"[INFO]: Viewing solver={args_cli.solver} task={args_cli.task} "
        f"num_envs={unwrapped.num_envs} step_rate={args_cli.step_rate}"
    )
    print("[INFO]: Close Isaac Sim to stop.")

    resources["phase"] = "environment_reset"
    env.reset(seed=args_cli.seed)
    _emit("reset_completed", reset_calls=1)
    start_time = time.time()
    step_count = 0
    min_step_dt = 0.0 if args_cli.step_rate <= 0 else 1.0 / args_cli.step_rate
    resources["phase"] = "environment_steps"
    stop_reason = "app_closed"

    with torch.inference_mode():
        while simulation_app.is_running():
            if args_cli.duration is not None and time.time() - start_time >= args_cli.duration:
                stop_reason = "duration"
                break
            if args_cli.max_steps is not None and step_count >= args_cli.max_steps:
                stop_reason = "step_budget"
                break

            step_start = time.time()
            problem = unwrapped.get_assignment_problem()
            assignment = solver.solve(problem)
            _validate_assignment(problem, assignment)

            actions = viewpoint_assignment_to_actions(unwrapped, assignment)
            _validate_actions(unwrapped, actions)

            env.step(actions)
            step_count += 1
            resources["step_count"] = step_count

            if step_count % args_cli.print_interval == 0:
                coverage = unwrapped.viewpoints_covered.float().mean(dim=-1).detach().cpu().tolist()
                assignment_list = assignment.detach().cpu().tolist()
                print(f"step={step_count} coverage_ratio={coverage} assignment={assignment_list}", flush=True)

            elapsed = time.time() - step_start
            if elapsed < min_step_dt:
                time.sleep(min_step_dt - elapsed)

    if args_cli.runtime_check and step_count != args_cli.max_steps:
        raise RuntimeError(f"Incomplete runtime check: {step_count}/{args_cli.max_steps} env.step calls ({stop_reason})")
    resources["work_completed"] = args_cli.max_steps is None or step_count == args_cli.max_steps
    _emit("steps_completed", step_count=step_count, expected_steps=args_cli.max_steps,
          stop_reason=stop_reason, work_completed=resources["work_completed"],
          count_unit="successful env.step returns")


def main():
    global torch
    simulation_app = None
    primary_error = None
    close_errors = []
    resources = {"env": None, "phase": "arguments", "step_count": 0, "work_completed": False}
    expected_steps = None
    runtime_check = False
    failures = []
    try:
        from isaaclab.app import AppLauncher

        original_argv = list(sys.argv)
        args_cli = _parse_args(AppLauncher)
        expected_steps = args_cli.max_steps
        runtime_check = args_cli.runtime_check
        resources["phase"] = "windows_startup_arguments"
        startup = prepare_windows_runtime_args(args_cli, original_argv=original_argv)
        _emit("startup_arguments", **startup)
        if runtime_check:
            repo_root = Path(__file__).resolve().parents[2]
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
                                  capture_output=True, text=True, timeout=5).stdout.strip()
            _emit("startup_identity", python=sys.executable, utf8_mode=sys.flags.utf8_mode,
                  cwd=os.getcwd(), entry=str(Path(__file__).resolve()), head=head, pid=os.getpid(),
                  parent_pid=os.getppid(), original_argv=original_argv, runtime_check=True,
                  app_launcher_source=sys.modules[AppLauncher.__module__].__file__,
                  requested_device=args_cli.device,
                  mode_environment={key: os.environ.get(key) for key in ("HEADLESS", "ENABLE_CAMERAS", "LIVESTREAM", "XR")})
        resources["phase"] = "pre_app_cuda"
        # Shared by ordinary and diagnostic mode; diagnostic mode has no startup shortcut.
        _emit("pre_app_cuda_ready", **_prepare_cuda_before_app(args_cli.device))
        resources["phase"] = "app_constructing"
        _emit("app_constructing")
        app_launcher = AppLauncher(args_cli)
        simulation_app = app_launcher.app
        import carb.settings
        import torch

        settings = carb.settings.get_settings()
        _emit("app_created", experience=app_launcher._sim_experience_file,
              headless=app_launcher._headless, enable_cameras=app_launcher._enable_cameras,
              livestream=app_launcher._livestream, vulkan_setting=settings.get("/app/vulkan"),
              user_config_path=settings.get("/app/userConfigPath"), kit_log_path=settings.get("/log/file"),
              actual_graphics_api="UNCONFIRMED_UNTIL_SAME_RUN_KIT_LOG")
        resources["phase"] = "post_app_cuda"
        if runtime_check:
            if startup["requested_backend"] == "D3D12" and settings.get("/app/vulkan") is not False:
                raise RuntimeError("Requested D3D12 but /app/vulkan is not False; inspect this run's Kit log")
            _verify_cuda_after_app(args_cli.device)
        _run_environment(args_cli, simulation_app, resources)
    except BaseException as exc:
        primary_error = exc
        failures.append({"phase": resources["phase"], "type": type(exc).__name__, "message": str(exc)})
        _emit("failure", **failures[-1], step_count=resources["step_count"])
        raise
    finally:
        env_close_ok = None
        if resources["env"] is not None:
            try:
                resources["env"].close()
                env_close_ok = True
                _emit("environment_closed")
            except BaseException as exc:
                env_close_ok = False
                close_errors.append(exc)
                failures.append({"phase": "env_close", "type": type(exc).__name__, "message": str(exc)})
                _emit("close_failure", **failures[-1])
        _emit("pre_close_result", runtime_check=runtime_check, work_completed=resources["work_completed"],
              step_count=resources["step_count"], expected_steps=expected_steps,
              env_close_ok=env_close_ok, app_close_requested=simulation_app is not None,
              last_work_phase=resources["phase"], failures=failures)
        if simulation_app is not None:
            try:
                simulation_app.close()
                _emit("app_close_returned")
            except BaseException as exc:
                close_errors.append(exc)
                _emit("close_failure", phase="app_close", type=type(exc).__name__, message=str(exc))
        if primary_error is None and close_errors:
            raise close_errors[0]


if __name__ == "__main__":
    main()
