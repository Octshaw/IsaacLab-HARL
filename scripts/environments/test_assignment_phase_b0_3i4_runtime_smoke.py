"""Focused, stage-marked Isaac runtime smoke for Phase B0-3I4-R.

This runner is intentionally separate from the pure/static B0-3I4 suite.  Each
mode launches one fresh application process so launcher, legacy-environment,
and event-profile failures remain attributable to a single runtime boundary.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from typing import Any


_STARTED_AT = time.monotonic()


def _mark(stage: str, message: str, **evidence: object) -> None:
    payload = {
        "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
        "message": message,
        "pid": os.getpid(),
        "stage": stage,
    }
    payload.update(evidence)
    print(json.dumps(payload, sort_keys=True, default=str), flush=True)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _tensor_values(value: object) -> list[object]:
    return value.detach().cpu().tolist()  # type: ignore[union-attr]


def _assert_initial_view(view: object, *, episode: int) -> None:
    episode_values = _tensor_values(view.episode_generation)  # type: ignore[attr-defined]
    transition_values = _tensor_values(view.transition_generation)  # type: ignore[attr-defined]
    _require(all(value == episode for value in episode_values), "unexpected episode generation")
    _require(all(value == -1 for value in transition_values), "unexpected initial transition generation")
    _require(view.result is None, "initial publication unexpectedly carries a transition result")  # type: ignore[attr-defined]
    _require(not any(_tensor_values(view.terminated)), "initial publication is terminated")  # type: ignore[attr-defined]
    _require(not any(_tensor_values(view.truncated)), "initial publication is truncated")  # type: ignore[attr-defined]


def _zero_actions(raw_env: object, torch: Any) -> dict[str, object]:
    return {
        agent: torch.zeros(
            (raw_env.num_envs, raw_env.cfg.action_spaces[agent]),
            device=raw_env.device,
        )
        for agent in raw_env.cfg.possible_agents
    }


def _run_legacy(*, num_envs: int) -> dict[str, object]:
    _mark("S3", "before legacy environment imports")
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import (
        ScanMobileManipulatorEnvCfg,
    )

    _mark("S4", "before legacy environment configuration")
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = num_envs
    _mark("S6", "before legacy environment construction", num_envs=num_envs)
    env = gym.make("Isaac-Scan-Mobile-Manipulator-Direct-v0", cfg=cfg)
    try:
        _mark("S7", "legacy environment constructed")
        _mark("S8", "before legacy reset")
        observations, extras = env.reset()
        _mark(
            "S9",
            "legacy observations obtained",
            agents=sorted(observations),
            extras_type=type(extras).__name__,
        )
        raw = env.unwrapped
        actions = _zero_actions(raw, torch)
        _mark("S10", "before legacy neutral step")
        returned = env.step(actions)
        _mark("S11", "legacy neutral step returned", tuple_length=len(returned))
        _require(type(returned) is tuple and len(returned) == 5, "legacy step return contract")
        _mark("S12", "legacy smoke complete")
        return {
            "legacy_num_envs": num_envs,
            "legacy_reset": True,
            "legacy_step": True,
            "legacy_tuple_length": len(returned),
        }
    finally:
        env.close()


def _run_event(*, num_envs: int, steps: int) -> dict[str, object]:
    _mark("S3", "before event-profile environment imports")
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
        AssignmentProfileName,
        AssignmentProfileResolutionOrigin,
        resolve_assignment_profile,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import (
        ScanMobileManipulatorEnvCfg,
    )

    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = num_envs
    device = torch.device(cfg.sim.device)
    _mark(
        "S4",
        "before event lifecycle domain construction",
        device=str(device),
        num_envs=num_envs,
    )
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(num_envs, dtype=torch.int64, device=device),
            num_robots=len(cfg.possible_agents),
            num_tasks=len(cfg.viewpoint_poses),
        )
    )
    prebootstrap = domain.current_read_port.read_current()
    _assert_initial_view(prebootstrap, episode=-1)
    _mark(
        "S5",
        "event lifecycle domain constructed",
        episode_generation=_tensor_values(prebootstrap.episode_generation),
        transition_generation=_tensor_values(prebootstrap.transition_generation),
    )
    _mark("S6", "before event environment construction", num_envs=num_envs)
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
    )
    try:
        _mark("S7", "event environment constructed")
        _mark("S8", "before event environment reset")
        observations, extras = env.reset()
        reset_view = domain.current_read_port.read_current()
        _assert_initial_view(reset_view, episode=0)
        _mark(
            "S9",
            "event observations and initial lifecycle publication obtained",
            agents=sorted(observations),
            episode_generation=_tensor_values(reset_view.episode_generation),
            extras_type=type(extras).__name__,
            transition_generation=_tensor_values(reset_view.transition_generation),
        )
        raw = env.unwrapped
        actions = _zero_actions(raw, torch)
        transition_evidence: list[dict[str, object]] = []
        for step_index in range(steps):
            _mark("S10", "before event neutral step", step_index=step_index)
            returned = env.step(actions)
            _mark("S11", "event neutral step returned", step_index=step_index, tuple_length=len(returned))
            _require(type(returned) is tuple and len(returned) == 5, "event step return contract")
            view = domain.current_read_port.read_current()
            result = view.result
            expected_transition = step_index
            episodes = _tensor_values(view.episode_generation)
            transitions = _tensor_values(view.transition_generation)
            terminated = _tensor_values(view.terminated)
            truncated = _tensor_values(view.truncated)
            _require(all(value == 0 for value in episodes), "episode changed during neutral continuity smoke")
            _require(
                all(value == expected_transition for value in transitions),
                "transition generation is not exactly contiguous",
            )
            _require(result is not None, "committed transition has no finalized result")
            _require(not any(terminated), "neutral continuity transition unexpectedly terminated")
            _require(not any(truncated), "neutral continuity transition unexpectedly truncated")
            _require(len(result.lifecycle_events) == 0, "neutral continuity transition emitted lifecycle events")
            transition_evidence.append(
                {
                    "episode_generation": episodes,
                    "event_count": len(result.lifecycle_events),
                    "step_index": step_index,
                    "transition_generation": transitions,
                }
            )
        _mark("S12", "event runtime smoke complete", steps=steps)
        return {
            "event_num_envs": num_envs,
            "event_reset": True,
            "event_steps": steps,
            "prebootstrap_episode": _tensor_values(prebootstrap.episode_generation),
            "reset_episode": _tensor_values(reset_view.episode_generation),
            "transitions": transition_evidence,
        }
    finally:
        env.close()


_WORKER_RESULT_PREFIX = "__B0_3I4R_WORKER_RESULT__"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("app", "legacy", "event"), required=True)
    parser.add_argument("--num-envs", type=int, default=2)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.num_envs <= 0:
        parser.error("--num-envs must be positive")
    if args.steps <= 0:
        parser.error("--steps must be positive")
    return args


def _run_worker(args: argparse.Namespace) -> int:

    _mark("S0", "diagnostic script entered", mode=args.mode, python=sys.executable)
    simulation_app = None
    result: dict[str, object]
    exit_code = 1
    try:
        _mark("S1", "before AppLauncher construction", mode=args.mode)
        from isaaclab.app import AppLauncher

        app_launcher = AppLauncher(headless=True)
        simulation_app = app_launcher.app
        _mark("S2", "AppLauncher construction returned", mode=args.mode)
        evidence: dict[str, object] = {}
        if args.mode == "app":
            _mark("S12", "minimal AppLauncher baseline complete")
        elif args.mode == "legacy":
            evidence = _run_legacy(num_envs=args.num_envs)
        else:
            evidence = _run_event(num_envs=args.num_envs, steps=args.steps)
        result = {
            "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
            "evidence": evidence,
            "mode": args.mode,
            "pid": os.getpid(),
            "status": "passed",
        }
        exit_code = 0
    except BaseException as exc:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        result = {
            "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "failure_code": getattr(exc, "failure_code", None),
            "mode": args.mode,
            "pid": os.getpid(),
            "status": "failed",
        }
    finally:
        print(
            _WORKER_RESULT_PREFIX + json.dumps(result, sort_keys=True, separators=(",", ":")),
            flush=True,
        )
        _mark("S13", "before SimulationApp shutdown", mode=args.mode)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except BaseException as close_exc:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                result = {
                    "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
                    "error": f"shutdown {type(close_exc).__name__}: {close_exc}",
                    "mode": args.mode,
                    "pid": os.getpid(),
                    "status": "failed",
                }
                exit_code = 1
                print(
                    _WORKER_RESULT_PREFIX
                    + json.dumps(result, sort_keys=True, separators=(",", ":")),
                    flush=True,
                )
    return exit_code


def _run_supervisor(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        "-u",
        os.path.abspath(__file__),
        "--mode",
        args.mode,
        "--num-envs",
        str(args.num_envs),
        "--steps",
        str(args.steps),
        "--worker",
    ]
    process = subprocess.Popen(
        command,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    worker_result: dict[str, object] | None = None
    assert process.stdout is not None
    for line in process.stdout:
        if line.startswith(_WORKER_RESULT_PREFIX):
            worker_result = json.loads(line[len(_WORKER_RESULT_PREFIX) :])
        else:
            print(line, end="", flush=True)
    child_exit_code = process.wait()
    _mark(
        "S14",
        "diagnostic worker process exited after SimulationApp shutdown",
        child_exit_code=child_exit_code,
        child_pid=process.pid,
        mode=args.mode,
    )
    if worker_result is None:
        result: dict[str, object] = {
            "child_exit_code": child_exit_code,
            "error": "worker exited without a pre-shutdown result",
            "mode": args.mode,
            "status": "failed",
        }
    else:
        result = dict(worker_result)
        result["child_exit_code"] = child_exit_code
        result["shutdown_observed"] = child_exit_code == 0
        if child_exit_code != 0:
            result["status"] = "failed"
            result["shutdown_error"] = f"worker exit code {child_exit_code}"
    print(
        json.dumps(result, sort_keys=True, separators=(",", ":"))
        if args.json
        else json.dumps(result, indent=2, sort_keys=True),
        flush=True,
    )
    return 0 if result.get("status") == "passed" and child_exit_code == 0 else 1


def main() -> int:
    args = _parse_args()
    return _run_worker(args) if args.worker else _run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
