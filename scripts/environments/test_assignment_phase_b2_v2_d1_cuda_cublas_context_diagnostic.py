"""Fresh-process B2-V2-D1 CUDA/cuBLAS boundary isolation diagnostic.

Test-only: no environment step, actor sampling, optimizer, backward, training,
playback, evaluation, checkpoint, public activation, or production mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any


STARTED = time.monotonic()
PREFIX = "__B2_V2_D1_STAGE_RESULT__"
ACTIVE_RESULT_PATH: str | None = None
COMPLETE = "PHASE-B2-V2-D1-CUDA-CUBLAS-CONTEXT-DIAGNOSTIC-COMPLETE-AWAITING-GPT-REVIEW"
ALL_PASS = "PHASE-B2-V2-D1-DIAGNOSTIC-ALL-PASS-ORIGINAL-CUBLAS-FAILURE-NOT-REPRODUCED-AWAITING-GPT-REVIEW"
BOUNDARY_STOP = "PHASE-B2-V2-D1-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
ORIGINAL_ERROR = "CUBLAS_STATUS_NOT_INITIALIZED"
DEVICE = "cuda:0"
E, M, N = 2, 3, 12
CRITIC_DIM = 418
HIDDEN = 32
SEED = 260826

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
PROTECTED = tuple(
    SCAN / name
    for name in (
        "assignment_event_profile_schema_contract_v2.py",
        "assignment_event_policy_evidence.py",
        "assignment_event_policy_decision.py",
        "assignment_event_actor_collection.py",
        "assignment_event_happo_policy_math.py",
        "assignment_event_terminal_critic_sidecar.py",
        "assignment_event_terminal_learner_transport.py",
        "assignment_event_critic_buffer.py",
        "assignment_event_gae_returns.py",
        "assignment_event_learned_route.py",
        "assignment_event_runtime_facade.py",
        "assignment_event_proposal_adapter.py",
        "assignment_lifecycle_transaction_runtime.py",
        "assignment_lifecycle_authority_runtime.py",
        "assignment_harl_wrapper.py",
        "assignment_harl_training.py",
        "scan_mobile_manipulator_env.py",
    )
) + (
    ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py",
) + tuple(
    HARL / name
    for name in (
        "algorithms/actors/happo.py",
        "algorithms/actors/on_policy_base.py",
        "algorithms/critics/v_critic.py",
        "common/valuenorm.py",
        "common/buffers/on_policy_actor_buffer.py",
        "common/buffers/on_policy_critic_buffer_ep.py",
        "runners/on_policy_base_runner.py",
        "runners/on_policy_ha_runner.py",
    )
)


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class WrapperView:
    def __init__(self, env: object) -> None:
        self._env = env
        self.unwrapped = env.unwrapped  # type: ignore[attr-defined]

    def __getattr__(self, name: str) -> object:
        return getattr(self._env, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("diagnostic wrapper used its public raw reset seam")

    def step(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("diagnostic must never step the environment")

    def close(self) -> None:
        self._env.close()  # type: ignore[attr-defined]


def emit(stage: str, message: str, **evidence: object) -> None:
    print(
        json.dumps(
            {
                "elapsed_seconds": round(time.monotonic() - STARTED, 3),
                "stage": stage,
                "message": message,
                **evidence,
            },
            sort_keys=True,
            default=str,
        ),
        flush=True,
    )


def file_hashes() -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in PROTECTED}


def nvidia_inventory() -> dict[str, object]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=15)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def cuda_memory(torch: Any) -> dict[str, int]:
    return {
        "allocated": int(torch.cuda.memory_allocated(0)),
        "reserved": int(torch.cuda.memory_reserved(0)),
    }


def versions_without_cuda_ops() -> dict[str, object]:
    import torch

    versions: dict[str, object] = {}
    for distribution in ("isaacsim", "isaaclab", "isaaclab-tasks", "harl"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    vc_spec = importlib.util.find_spec("harl.algorithms.critics.v_critic")
    harl_spec = importlib.util.find_spec("harl")
    cuda_env = {
        key: value
        for key, value in os.environ.items()
        if key.upper().startswith("CUDA") or key.upper().startswith("PYTORCH_CUDA")
    }
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_current_device": torch.cuda.current_device() if torch.cuda.is_available() else None,
        "cuda_device_name_0": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "package_versions": versions,
        "harl_source": None if harl_spec is None else harl_spec.origin,
        "vcritic_source": None if vc_spec is None else vc_spec.origin,
        "cuda_environment": cuda_env,
        "nvidia_smi": nvidia_inventory(),
    }


def basic_cuda() -> dict[str, object]:
    import torch

    x = torch.ones((8, 8), dtype=torch.float32, device=DEVICE)
    y = x + 1.0
    torch.cuda.synchronize()
    return {
        "allocation": "PASS",
        "basic_kernel": "PASS",
        "device": str(y.device),
        "dtype": str(y.dtype),
        "finite": bool(torch.isfinite(y).all().item()),
        "sum": float(y.sum().item()),
        "memory": cuda_memory(torch),
        "synchronized_after": "x+1",
    }


def tiny_cublas(torch: Any) -> dict[str, object]:
    torch.manual_seed(SEED)
    a = torch.ones((8, 8), dtype=torch.float32, device=DEVICE)
    b = torch.arange(64, dtype=torch.float32, device=DEVICE).reshape(8, 8)
    with torch.inference_mode():
        product = torch.matmul(a, b)
    torch.cuda.synchronize()
    matmul = {
        "status": "PASS",
        "device": str(product.device),
        "finite": bool(torch.isfinite(product).all().item()),
        "sum": float(product.sum().item()),
        "synchronized": True,
    }
    linear = torch.nn.Linear(8, 8).to(DEVICE)
    input_tensor = torch.ones((2, 8), dtype=torch.float32, device=DEVICE)
    with torch.inference_mode():
        output = linear(input_tensor)
    torch.cuda.synchronize()
    return {
        "matmul": matmul,
        "linear": {
            "status": "PASS",
            "shape": list(output.shape),
            "device": str(output.device),
            "finite": bool(torch.isfinite(output).all().item()),
            "synchronized": True,
        },
        "memory": cuda_memory(torch),
    }


def critic_args() -> dict[str, object]:
    return {
        "hidden_sizes": [HIDDEN, HIDDEN],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "clip_param": 0.2,
        "critic_epoch": 1,
        "critic_num_mini_batch": 1,
        "data_chunk_length": 2,
        "value_loss_coef": 1.0,
        "max_grad_norm": 10.0,
        "huber_delta": 10.0,
        "use_max_grad_norm": True,
        "use_clipped_value_loss": True,
        "use_huber_loss": True,
        "use_policy_active_masks": True,
        "critic_lr": 0.0005,
        "opti_eps": 0.00001,
        "weight_decay": 0,
    }


def happo_args() -> dict[str, object]:
    return {
        "hidden_sizes": [HIDDEN, HIDDEN],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "gain": 0.01,
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "data_chunk_length": 2,
        "lr": 0.0005,
        "opti_eps": 0.00001,
        "weight_decay": 0,
        "std_x_coef": 1,
        "std_y_coef": 0.5,
        "ppo_epoch": 1,
        "clip_param": 0.2,
        "actor_num_mini_batch": 1,
        "entropy_coef": 0.01,
        "use_max_grad_norm": True,
        "max_grad_norm": 10.0,
        "use_policy_active_masks": True,
        "action_aggregation": "prod",
    }


def construct_environment() -> tuple[object, object, object, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import _EventProfileLifecycleDomainSpec, _EventProfileLifecycleRuntimeDomain
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import AssignmentProfileName, AssignmentProfileResolutionOrigin, resolve_assignment_profile
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

    profile = resolve_assignment_profile(AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = E
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    cfg.episode_length_s = float(cfg.sim.dt) * int(cfg.decimation) * 3
    if (len(cfg.possible_agents), len(cfg.viewpoint_poses), str(cfg.sim.device)) != (M, N, DEVICE):
        raise RuntimeError("canonical E/M/N/device configuration changed")
    device = torch.device(DEVICE)
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(E, dtype=torch.int64, device=device),
            num_robots=M,
            num_tasks=N,
        )
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    view = WrapperView(env)
    wrapper = _compose_event_assignment_harl_wrapper(
        env=view,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        assignment_profile_entrypoint="B2-V2-D1.cuda_context_diagnostic",
    )
    reset_result = wrapper.reset()
    if type(reset_result) is not tuple or len(reset_result) != 3:
        raise RuntimeError("canonical admitted reset arity changed")
    return view, wrapper, domain, cfg


def capture_real_i1(raw: object, domain: object) -> object:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import seal_current_event_policy_decision_bundle_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import capture_current_event_policy_evidence_snapshot_v2, capture_event_policy_physical_problem_evidence_v2

    scale = raw._event_terminal_critic_scale_contract_v2
    physical = capture_event_policy_physical_problem_evidence_v2(
        assignment_problem=raw.get_assignment_problem(),
        episode_progress_steps=raw.episode_length_buf,
        scale_contract=scale,
    )
    snapshot = capture_current_event_policy_evidence_snapshot_v2(
        current_publication=domain.current_read_port.read_current(),
        current_open_window_view=domain.interstep_fence_read_port.read(),
        physical_evidence=physical,
        scale_contract=scale,
    )
    return seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)


def vcritic_forward(torch: Any, obs: Any) -> dict[str, object]:
    from harl.algorithms.critics.v_critic import VCritic

    torch.manual_seed(SEED + 20)
    critic = VCritic(critic_args(), Box((CRITIC_DIM,)), device=torch.device(DEVICE))
    critic.prep_rollout()
    rnn = torch.zeros((E, 1, HIDDEN), dtype=torch.float32, device=DEVICE)
    masks = torch.ones((E, 1), dtype=torch.float32, device=DEVICE)
    with torch.inference_mode():
        values, next_rnn = critic.get_values(obs, rnn, masks)
    torch.cuda.synchronize()
    if critic.critic_optimizer.state or any(parameter.grad is not None for parameter in critic.critic.parameters()):
        raise RuntimeError("diagnostic VCritic created optimizer state or gradients")
    return {
        "values_shape": list(values.shape),
        "values_device": str(values.device),
        "values_finite": bool(torch.isfinite(values).all().item()),
        "next_rnn_shape": list(next_rnn.shape),
        "optimizer_state_entries": len(critic.critic_optimizer.state),
        "grad_tensors": sum(parameter.grad is not None for parameter in critic.critic.parameters()),
        "memory": cuda_memory(torch),
        "synchronized": True,
    }


def run_app_stage(stage: str, *, warmup_before_app: bool = False) -> dict[str, object]:
    simulation_app = None
    view = None
    try:
        prewarm = None
        if warmup_before_app:
            import torch

            prewarm = tiny_cublas(torch)
        from isaaclab.app import AppLauncher

        simulation_app = AppLauncher(headless=True).app
        import torch

        after_app_memory = cuda_memory(torch)
        if stage == "D3":
            result = {"app_launcher": "PASS", "cublas": tiny_cublas(torch)}
        else:
            view, wrapper, domain, cfg = construct_environment()
            raw = view.unwrapped
            environment = {
                "id": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
                "type": type(raw).__name__,
                "E": int(raw.num_envs),
                "M": len(cfg.possible_agents),
                "N": len(cfg.viewpoint_poses),
                "device": str(raw.device),
                "reset": "PASS",
                "common_step_counter": int(raw.common_step_counter),
            }
            if int(raw.common_step_counter) != 0:
                raise RuntimeError("diagnostic unexpectedly performed a physical step")
            if stage == "D4":
                result = {"environment": environment, "cublas": tiny_cublas(torch)}
            elif stage == "D5":
                obs = torch.zeros((E, CRITIC_DIM), dtype=torch.float32, device=DEVICE)
                result = {
                    "environment": environment,
                    "input": {"source": "synthetic", "shape": list(obs.shape), "stride": list(obs.stride()), "contiguous": obs.is_contiguous(), "dtype": str(obs.dtype), "device": str(obs.device)},
                    "vcritic": vcritic_forward(torch, obs),
                }
            elif stage in ("D6", "D7A", "D7B", "D8R1", "D8R2"):
                bundle = capture_real_i1(raw, domain)
                runner_share = bundle.evidence_snapshot.runner_share_obs
                obs = runner_share[:, 0]
                result = {
                    "environment": environment,
                    "input": {
                        "source": "real_I1_runner_share_obs_agent0_I6_projection",
                        "runner_shape": list(runner_share.shape),
                        "shape": list(obs.shape),
                        "stride": list(obs.stride()),
                        "storage_offset": int(obs.storage_offset()),
                        "contiguous": obs.is_contiguous(),
                        "dtype": str(obs.dtype),
                        "device": str(obs.device),
                        "requires_grad": obs.requires_grad,
                        "finite": bool(torch.isfinite(obs).all().item()),
                    },
                    "vcritic": vcritic_forward(torch, obs),
                }
            elif stage == "D7C":
                import gymnasium as gym
                from harl.algorithms.actors.happo import HAPPO

                bundle = capture_real_i1(raw, domain)
                actor_dim = int(bundle.evidence_snapshot.actor_obs.shape[-1])
                actors = []
                for agent_id in range(M):
                    torch.manual_seed(SEED + 10 + agent_id)
                    actor = HAPPO(happo_args(), Box((actor_dim,)), gym.spaces.Discrete(N + 1), device=torch.device(DEVICE))
                    actor.prep_rollout()
                    actors.append(actor)
                obs = bundle.evidence_snapshot.runner_share_obs[:, 0]
                result = {
                    "environment": environment,
                    "contrast": "original component construction order; HAPPO constructed but not forwarded",
                    "actor_count": len(actors),
                    "actor_optimizer_state_entries": [len(actor.actor_optimizer.state) for actor in actors],
                    "vcritic": vcritic_forward(torch, obs),
                }
            else:
                raise ValueError(f"unsupported AppLauncher stage: {stage}")
        result["memory_after_app_before_stage"] = after_app_memory
        if prewarm is not None:
            result["pre_app_cublas_warmup"] = prewarm
        result["physical_steps"] = 0
        result["optimizer_calls"] = 0
        result["backward_calls"] = 0
        checkpoint = {
            "stage": stage,
            "status": "passed",
            "evidence": result,
            "nvidia_smi_after": nvidia_inventory(),
            "original_error_reproduced": False,
        }
        write_result(ACTIVE_RESULT_PATH, checkpoint)
        print(PREFIX + json.dumps(checkpoint, sort_keys=True, default=str), flush=True)
        return result
    except BaseException as exc:
        trace = traceback.format_exc()
        checkpoint = {
            "stage": stage,
            "status": "failed",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": trace,
            "nvidia_smi_after": nvidia_inventory(),
            "original_error_reproduced": ORIGINAL_ERROR in f"{type(exc).__name__}: {exc}",
        }
        write_result(ACTIVE_RESULT_PATH, checkpoint)
        print(PREFIX + json.dumps(checkpoint, sort_keys=True, default=str), flush=True)
        raise
    finally:
        if view is not None:
            view.close()
        if simulation_app is not None:
            simulation_app.close()


def run_stage(stage: str) -> dict[str, object]:
    if stage == "D0":
        return versions_without_cuda_ops()
    if stage == "D1":
        return basic_cuda()
    if stage == "D2":
        import torch

        return tiny_cublas(torch)
    if stage in ("D3", "D4", "D5", "D6", "D7A", "D7C", "D8R1", "D8R2"):
        return run_app_stage(stage)
    if stage == "D7B":
        return run_app_stage(stage, warmup_before_app=True)
    raise ValueError(f"unknown diagnostic stage: {stage}")


def write_result(path: str | None, result: dict[str, object]) -> None:
    if path:
        Path(path).write_text(json.dumps(result, sort_keys=True, default=str), encoding="utf-8")


def worker(args: argparse.Namespace) -> int:
    global ACTIVE_RESULT_PATH
    ACTIVE_RESULT_PATH = args.result_file
    result: dict[str, object]
    try:
        emit(args.stage, "fresh worker started", python=sys.executable, nvidia_smi_before=nvidia_inventory())
        evidence = run_stage(args.stage)
        result = {
            "stage": args.stage,
            "status": "passed",
            "evidence": evidence,
            "nvidia_smi_after": nvidia_inventory(),
            "original_error_reproduced": False,
        }
        code = 0
    except BaseException as exc:
        trace = traceback.format_exc()
        message = f"{type(exc).__name__}: {exc}"
        print(trace, file=sys.stderr, flush=True)
        result = {
            "stage": args.stage,
            "status": "failed",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": trace,
            "nvidia_smi_after": nvidia_inventory(),
            "original_error_reproduced": ORIGINAL_ERROR in message,
        }
        code = 1
    write_result(args.result_file, result)
    print(PREFIX + json.dumps(result, sort_keys=True, default=str), flush=True)
    return code


def reader(pipe: Any, lines: queue.Queue[str | None]) -> None:
    try:
        for line in pipe:
            lines.put(line)
    finally:
        lines.put(None)


def terminate_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True, text=True)
    elif process.poll() is None:
        process.kill()


def run_fresh_stage(stage: str, timeout_seconds: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"b2_v2_d1_{stage.lower()}_") as temp:
        result_path = os.path.join(temp, "result.json")
        command = [sys.executable, "-u", os.path.abspath(__file__), "--worker", "--stage", stage, "--result-file", result_path]
        before_gpu = nvidia_inventory()
        emit(stage, "supervisor launching fresh stage", timeout_seconds=timeout_seconds)
        process = subprocess.Popen(command, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        lines: queue.Queue[str | None] = queue.Queue()
        thread = threading.Thread(target=reader, args=(process.stdout, lines), daemon=True)
        thread.start()
        deadline = time.monotonic() + timeout_seconds
        done = False
        streamed: dict[str, object] | None = None
        timed_out = False
        while not done or process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0 and process.poll() is None:
                timed_out = True
                terminate_tree(process)
                break
            try:
                line = lines.get(timeout=min(0.25, max(0.01, remaining)))
            except queue.Empty:
                continue
            if line is None:
                done = True
            elif line.startswith(PREFIX):
                streamed = json.loads(line[len(PREFIX):])
            else:
                print(line, end="", flush=True)
        try:
            exit_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_tree(process)
            exit_code = process.wait(timeout=15)
        thread.join(timeout=5)
        if os.path.isfile(result_path):
            streamed = json.loads(Path(result_path).read_text(encoding="utf-8"))
        if timed_out:
            result = {"stage": stage, "status": "failed", "exception_type": "Timeout", "exception_message": "fresh worker exceeded timeout", "original_error_reproduced": False}
        elif streamed is None:
            result = {"stage": stage, "status": "failed", "exception_type": "MissingResult", "exception_message": "fresh worker emitted no result", "original_error_reproduced": False}
        else:
            result = dict(streamed)
        result.update(
            {
                "process_exit_code": exit_code,
                "timed_out": timed_out,
                "worker_alive_after_wait": process.poll() is None,
                "safe_shutdown": not timed_out and process.poll() is not None,
                "nvidia_smi_supervisor_before": before_gpu,
                "nvidia_smi_supervisor_after": nvidia_inventory(),
            }
        )
        return result


BOUNDARIES = {
    "D1": "CUDA_BASE_CONTEXT_GAP",
    "D2": "PLAIN_TORCH_CUBLAS_GAP",
    "D3": "APP_LAUNCHER_CUDA_CONTEXT_INTERACTION",
    "D4": "ISAAC_ENVIRONMENT_CUDA_CONTEXT_INTERACTION",
    "D5": "INSTALLED_VCRITIC_COMPONENT_GAP",
    "D6": "REAL_I1_CRITIC_INPUT_INTERFACE_GAP",
    "D7A": "STARTUP_ORDER_SENSITIVE_CUDA_CONTEXT",
    "D7B": "STARTUP_ORDER_SENSITIVE_CUDA_CONTEXT",
    "D7C": "HARL_COMPONENT_CONSTRUCTION_ORDER_CUDA_CONTEXT_INTERACTION",
    "D8R1": "INTERMITTENT_CUDA_CONTEXT_GAP",
    "D8R2": "INTERMITTENT_CUDA_CONTEXT_GAP",
}


def supervisor(args: argparse.Namespace) -> int:
    before = file_hashes()
    results: list[dict[str, object]] = []
    first_failure: dict[str, object] | None = None
    sequence = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]
    for stage in sequence:
        result = run_fresh_stage(stage, args.timeout_seconds)
        results.append(result)
        if result["status"] != "passed":
            first_failure = result
            break
    if first_failure is None:
        for stage in ("D7A", "D7B", "D7C"):
            result = run_fresh_stage(stage, args.timeout_seconds)
            results.append(result)
            if result["status"] != "passed":
                first_failure = result
                break
    if first_failure is None:
        for stage in ("D8R1", "D8R2"):
            result = run_fresh_stage(stage, args.timeout_seconds)
            results.append(result)
            if result["status"] != "passed":
                first_failure = result
                break
    after = file_hashes()
    unchanged = before == after
    safe = all(bool(item["safe_shutdown"]) and not bool(item["worker_alive_after_wait"]) for item in results)
    if not unchanged or not safe:
        classification = BOUNDARY_STOP
        boundary = "DIAGNOSTIC_BOUNDARY_VIOLATION"
        status = "failed"
    elif first_failure is not None:
        classification = COMPLETE
        boundary = BOUNDARIES.get(str(first_failure["stage"]), "UNCLASSIFIED_DIAGNOSTIC_BOUNDARY")
        status = "diagnostic_complete"
    else:
        classification = ALL_PASS
        boundary = "DIAGNOSTIC_ALL_PASS_ORIGINAL_FAILURE_NOT_REPRODUCED"
        status = "diagnostic_complete"
    summary = {
        "classification": classification,
        "status": status,
        "first_failing_boundary": boundary,
        "first_failing_stage": None if first_failure is None else first_failure["stage"],
        "original_error_reproduced": any(bool(item.get("original_error_reproduced")) for item in results),
        "stage_matrix": [{"stage": item["stage"], "status": item["status"], "original_error_reproduced": item.get("original_error_reproduced", False)} for item in results],
        "stages": results,
        "fresh_process_count": len(results),
        "protected_hash_count": len(before),
        "protected_hashes_unchanged": unchanged,
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "all_workers_stopped_without_timeout": safe,
        "production_changes": "NONE",
        "installed_harl_changes": "NONE",
        "environment_steps": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "training": "NOT RUN",
        "original_v2_rerun": False,
        "B2_V2": "STOPPED / INCOMPLETE",
        "B2_R": "NOT AUTHORIZED",
    }
    print(json.dumps(summary, sort_keys=True) if args.json else json.dumps(summary, indent=2, sort_keys=True), flush=True)
    if args.output:
        Path(args.output).write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if status == "diagnostic_complete" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7A", "D7B", "D7C", "D8R1", "D8R2"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", help=argparse.SUPPRESS)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("timeout must be positive")
    if args.worker and (args.stage is None or args.result_file is None):
        parser.error("worker requires --stage and --result-file")
    if not args.worker and args.stage is not None:
        parser.error("--stage is worker-only; supervisor chooses the decision tree")
    return args


def main() -> int:
    args = parse_args()
    return worker(args) if args.worker else supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
