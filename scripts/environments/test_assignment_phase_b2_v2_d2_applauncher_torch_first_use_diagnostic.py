"""Fresh-process B2-V2-D2 AppLauncher/Torch first-use diagnostic.

Test-only.  This file never constructs an Isaac environment and never runs
HARL, an optimizer, backward, training, playback, evaluation, or a checkpoint.
The ordering contrasts are diagnostic evidence, not production workarounds.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any


CLASSIFICATION = (
    "PHASE-B2-V2-D2-APPLAUNCHER-TORCH-FIRST-USE-CHARACTERIZATION-"
    "COMPLETE-AWAITING-GPT-REVIEW"
)
BOUNDARY_STOP = "PHASE-B2-V2-D2-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
OFFICIAL_ORACLE = "OFFICIAL_ORDER_NOT_CLEANLY_REPRODUCED"
ORIGINAL_ERROR = "CUBLAS_STATUS_NOT_INITIALIZED"
DEVICE = "cuda:0"
DTYPE_NAME = "float32"
MATRIX_DIM = 8
SEED = 260826
DEFAULT_REPEATS = 3
PREFIX = "__B2_V2_D2_RESULT__"
ACTIVE_RESULT_PATH: str | None = None
CURRENT_SUBSTAGE = "worker_start"

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
V2_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py"
D1_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py"
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
) + (V2_HARNESS, D1_HARNESS)


class OfficialOrderOracleError(RuntimeError):
    """The official-order case was already contaminated by an implicit Torch import."""


def set_substage(name: str) -> None:
    global CURRENT_SUBSTAGE
    CURRENT_SUBSTAGE = name


def file_hashes() -> dict[str, str]:
    missing = [str(path) for path in PROTECTED if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"protected files missing: {missing}")
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in PROTECTED}


def nvidia_inventory() -> dict[str, object]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=15)
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def module_snapshot(label: str) -> dict[str, object]:
    torch_loaded = "torch" in sys.modules
    snapshot: dict[str, object] = {
        "label": label,
        "torch_in_sys_modules": torch_loaded,
        "isaaclab_app_in_sys_modules": "isaaclab.app" in sys.modules,
        "isaacsim_in_sys_modules": "isaacsim" in sys.modules,
    }
    if torch_loaded:
        torch = sys.modules["torch"]
        snapshot["torch_cuda_initialized"] = bool(torch.cuda.is_initialized())
        if snapshot["torch_cuda_initialized"]:
            snapshot["cuda_memory_allocated"] = int(torch.cuda.memory_allocated(0))
            snapshot["cuda_memory_reserved"] = int(torch.cuda.memory_reserved(0))
    return snapshot


def append_snapshot(timeline: list[dict[str, object]], label: str) -> None:
    timeline.append(module_snapshot(label))


def cuda_state(torch: Any, label: str) -> dict[str, object]:
    result: dict[str, object] = {
        "label": label,
        "available": bool(torch.cuda.is_available()),
        "initialized": bool(torch.cuda.is_initialized()),
    }
    if result["available"]:
        result.update(
            {
                "current_device": int(torch.cuda.current_device()),
                "device_name": torch.cuda.get_device_name(0),
                "memory_allocated": int(torch.cuda.memory_allocated(0)),
                "memory_reserved": int(torch.cuda.memory_reserved(0)),
            }
        )
    return result


def basic_cuda(torch: Any, timeline: list[dict[str, object]], prefix: str) -> dict[str, object]:
    append_snapshot(timeline, f"{prefix}_before_first_cuda_op")
    set_substage(f"{prefix}.allocation_call")
    x = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    set_substage(f"{prefix}.allocation_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.basic_kernel_call")
    y = x + 1.0
    set_substage(f"{prefix}.basic_kernel_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.finite_check")
    finite = bool(torch.isfinite(y).all().item())
    return {
        "allocation": "PASS",
        "basic_kernel": "PASS",
        "device": str(y.device),
        "dtype": str(y.dtype),
        "shape": list(y.shape),
        "finite": finite,
        "sum": float(y.sum().item()),
        "synchronized": True,
        "cuda_state": cuda_state(torch, f"{prefix}_after_basic"),
    }


def matmul(torch: Any, timeline: list[dict[str, object]], prefix: str) -> dict[str, object]:
    torch.manual_seed(SEED)
    set_substage(f"{prefix}.input_a_allocation")
    a = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    set_substage(f"{prefix}.input_a_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.input_b_allocation")
    b = torch.arange(MATRIX_DIM * MATRIX_DIM, dtype=torch.float32, device=DEVICE).reshape(
        MATRIX_DIM, MATRIX_DIM
    )
    set_substage(f"{prefix}.input_b_synchronize")
    torch.cuda.synchronize()
    append_snapshot(timeline, f"{prefix}_before_first_cublas_op")
    set_substage(f"{prefix}.matmul_call")
    with torch.inference_mode():
        product = torch.matmul(a, b)
    set_substage(f"{prefix}.matmul_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.finite_check")
    finite = bool(torch.isfinite(product).all().item())
    return {
        "matmul": "PASS",
        "device": str(product.device),
        "dtype": str(product.dtype),
        "shape": list(product.shape),
        "finite": finite,
        "sum": float(product.sum().item()),
        "synchronized": True,
        "cuda_state": cuda_state(torch, f"{prefix}_after_matmul"),
    }


def linear(torch: Any, prefix: str) -> dict[str, object]:
    torch.manual_seed(SEED + 1)
    set_substage(f"{prefix}.linear_construct")
    layer = torch.nn.Linear(MATRIX_DIM, MATRIX_DIM)
    set_substage(f"{prefix}.linear_to_cuda")
    layer = layer.to(DEVICE)
    set_substage(f"{prefix}.linear_to_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.input_allocation")
    inputs = torch.ones((2, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    set_substage(f"{prefix}.input_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.linear_call")
    with torch.inference_mode():
        output = layer(inputs)
    set_substage(f"{prefix}.linear_synchronize")
    torch.cuda.synchronize()
    set_substage(f"{prefix}.finite_check")
    finite = bool(torch.isfinite(output).all().item())
    return {
        "linear": "PASS",
        "device": str(output.device),
        "dtype": str(output.dtype),
        "shape": list(output.shape),
        "finite": finite,
        "synchronized": True,
        "cuda_state": cuda_state(torch, f"{prefix}_after_linear"),
    }


def app_config(launcher: object) -> dict[str, object]:
    config = getattr(launcher, "_sim_app_config", {})
    if not isinstance(config, dict):
        config = {}
    return {
        "headless": config.get("headless", getattr(launcher, "_headless", None)),
        "active_gpu": config.get("active_gpu"),
        "physics_gpu": config.get("physics_gpu"),
        "multi_gpu": config.get("multi_gpu"),
        "device_id": getattr(launcher, "device_id", None),
    }


def import_torch(timeline: list[dict[str, object]], label: str) -> Any:
    append_snapshot(timeline, f"{label}_before_torch_import")
    set_substage(f"{label}.torch_import")
    import torch

    append_snapshot(timeline, f"{label}_after_torch_import")
    return torch


def launch_app(timeline: list[dict[str, object]], *, clean_oracle: bool) -> tuple[object, object]:
    append_snapshot(timeline, "immediately_before_applauncher_import")
    set_substage("applauncher_import")
    from isaaclab.app import AppLauncher

    append_snapshot(timeline, "immediately_before_applauncher_construction")
    if clean_oracle and "torch" in sys.modules:
        raise OfficialOrderOracleError(
            f"{OFFICIAL_ORACLE}: torch was already in sys.modules before AppLauncher construction"
        )
    set_substage("applauncher_construction")
    launcher = AppLauncher(headless=True)
    simulation_app = launcher.app
    append_snapshot(timeline, "immediately_after_simulationapp_startup")
    return launcher, simulation_app


def run_case(case: str) -> dict[str, object]:
    global ACTIVE_RESULT_PATH
    timeline: list[dict[str, object]] = []
    simulation_app = None
    launcher = None
    evidence: dict[str, object] = {
        "case": case,
        "timeline": timeline,
        "device": DEVICE,
        "dtype": DTYPE_NAME,
        "matrix_dim": MATRIX_DIM,
        "seed": SEED,
        "environment_constructed": False,
        "environment_steps": 0,
        "harl_executed": False,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }
    append_snapshot(timeline, "process_startup")
    try:
        if case == "C0_plain_torch":
            torch = import_torch(timeline, case)
            evidence["post_matmul"] = matmul(torch, timeline, "plain")
            evidence["post_linear"] = linear(torch, "plain")
        elif case == "C1_d1_exact":
            launcher, simulation_app = launch_app(timeline, clean_oracle=False)
            evidence["app_config"] = app_config(launcher)
            torch = import_torch(timeline, case)
            evidence["post_app_pre_first_cuda"] = cuda_state(torch, "post_app_pre_first_cuda")
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        elif case == "C2_official_order":
            launcher, simulation_app = launch_app(timeline, clean_oracle=True)
            evidence["app_config"] = app_config(launcher)
            if "torch" in sys.modules:
                raise OfficialOrderOracleError(
                    f"{OFFICIAL_ORACLE}: AppLauncher/SimulationApp startup implicitly loaded torch "
                    "before the script's post-startup import"
                )
            torch = import_torch(timeline, case)
            evidence["post_app_pre_first_cuda"] = cuda_state(torch, "post_app_pre_first_cuda")
            evidence["post_basic"] = basic_cuda(torch, timeline, "post_app")
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        elif case == "C3_torch_preimport_no_cuda":
            torch = import_torch(timeline, case)
            evidence["pre_app_torch_cuda_initialized"] = bool(torch.cuda.is_initialized())
            launcher, simulation_app = launch_app(timeline, clean_oracle=False)
            evidence["app_config"] = app_config(launcher)
            evidence["post_basic"] = basic_cuda(torch, timeline, "post_app")
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        elif case == "C4_pre_cuda_basic":
            torch = import_torch(timeline, case)
            evidence["pre_app_basic"] = basic_cuda(torch, timeline, "pre_app")
            launcher, simulation_app = launch_app(timeline, clean_oracle=False)
            evidence["app_config"] = app_config(launcher)
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        elif case == "C5_pre_cublas":
            torch = import_torch(timeline, case)
            evidence["pre_app_matmul"] = matmul(torch, timeline, "pre_app")
            launcher, simulation_app = launch_app(timeline, clean_oracle=False)
            evidence["app_config"] = app_config(launcher)
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        elif case == "C6_direct_simulationapp":
            append_snapshot(timeline, "immediately_before_isaacsim_import")
            set_substage("isaacsim_simulationapp_import")
            from isaacsim import SimulationApp

            append_snapshot(timeline, "immediately_before_simulationapp_construction")
            set_substage("direct_simulationapp_construction")
            simulation_app = SimulationApp({"headless": True})
            append_snapshot(timeline, "immediately_after_simulationapp_startup")
            torch = import_torch(timeline, case)
            evidence["direct_config"] = {"headless": True}
            evidence["post_basic"] = basic_cuda(torch, timeline, "post_app")
            evidence["post_matmul"] = matmul(torch, timeline, "post_app")
            evidence["post_linear"] = linear(torch, "post_app")
        else:
            raise ValueError(f"unknown case: {case}")

        set_substage("result_persist_before_shutdown")
        result = {
            "case": case,
            "status": "passed",
            "evidence": evidence,
            "original_error_reproduced": False,
            "shutdown_requested": simulation_app is not None,
            "nvidia_smi_after_operations": nvidia_inventory(),
        }
        write_result(ACTIVE_RESULT_PATH, result)
        print(PREFIX + json.dumps(result, sort_keys=True, default=str), flush=True)
        return result
    except BaseException as exc:
        result = {
            "case": case,
            "status": "failed",
            "failed_substage": CURRENT_SUBSTAGE,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            "evidence": evidence,
            "official_order_oracle_failed": isinstance(exc, OfficialOrderOracleError),
            "original_error_reproduced": ORIGINAL_ERROR in f"{type(exc).__name__}: {exc}",
            "shutdown_requested": simulation_app is not None,
            "nvidia_smi_after_operations": nvidia_inventory(),
        }
        write_result(ACTIVE_RESULT_PATH, result)
        print(PREFIX + json.dumps(result, sort_keys=True, default=str), flush=True)
        raise
    finally:
        if simulation_app is not None:
            set_substage("simulationapp_close")
            simulation_app.close()


def write_result(path: str | None, result: dict[str, object]) -> None:
    if path is not None:
        Path(path).write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")


def worker(args: argparse.Namespace) -> int:
    global ACTIVE_RESULT_PATH
    ACTIVE_RESULT_PATH = args.result_file
    try:
        run_case(args.case)
        return 0
    except BaseException as exc:
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        if not Path(args.result_file).is_file():
            result = {
                "case": args.case,
                "status": "failed",
                "failed_substage": CURRENT_SUBSTAGE,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "original_error_reproduced": ORIGINAL_ERROR in str(exc),
            }
            write_result(args.result_file, result)
        return 1


def run_fresh(case: str, repeat: int, timeout_seconds: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"b2_v2_d2_{case.lower()}_{repeat}_") as temp:
        result_path = Path(temp) / "result.json"
        command = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--worker",
            "--case",
            case,
            "--result-file",
            str(result_path),
        ]
        before_gpu = nvidia_inventory()
        started = time.monotonic()
        process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        timed_out = False
        try:
            stdout, _ = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            else:
                process.kill()
            stdout, _ = process.communicate(timeout=15)
        elapsed = round(time.monotonic() - started, 3)
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            result = {
                "case": case,
                "status": "failed",
                "exception_type": "Timeout" if timed_out else "MissingResult",
                "exception_message": "worker exceeded timeout" if timed_out else "worker emitted no result",
                "original_error_reproduced": False,
            }
        result.update(
            {
                "repeat": repeat,
                "process_exit_code": process.returncode,
                "elapsed_seconds": elapsed,
                "timed_out": timed_out,
                "worker_alive_after_wait": process.poll() is None,
                "safe_shutdown": not timed_out and process.poll() is not None,
                "stdout_stderr": stdout,
                "nvidia_smi_supervisor_before": before_gpu,
                "nvidia_smi_supervisor_after": nvidia_inventory(),
            }
        )
        return result


def inventory() -> dict[str, object]:
    versions: dict[str, str | None] = {}
    for distribution in ("torch", "isaacsim", "isaaclab", "isaaclab-tasks", "harl"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=False, capture_output=True, text=True
    ).stdout.strip()
    git_describe = subprocess.run(
        ["git", "describe", "--tags", "--always", "--dirty"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "windows_version": platform.platform(),
        "distributions": versions,
        "git_head": git_head,
        "git_describe": git_describe,
        "nvidia_smi": nvidia_inventory(),
        "cuda_environment": {
            key: value
            for key, value in os.environ.items()
            if key.upper().startswith("CUDA") or key.upper().startswith("PYTORCH_CUDA")
        },
    }


def summarize(case: str, results: list[dict[str, object]]) -> dict[str, object]:
    passed = sum(result.get("status") == "passed" for result in results)
    failed = len(results) - passed
    original = sum(bool(result.get("original_error_reproduced")) for result in results)
    oracle = sum(bool(result.get("official_order_oracle_failed")) for result in results)
    return {
        "case": case,
        "runs": len(results),
        "pass": passed,
        "fail": failed,
        "original_cublas_error": original,
        "official_order_oracle_fail": oracle,
        "timeouts": sum(bool(result.get("timed_out")) for result in results),
        "surviving_workers": sum(bool(result.get("worker_alive_after_wait")) for result in results),
        "failed_substages": [
            result.get("failed_substage") for result in results if result.get("status") != "passed"
        ],
        "exception_messages": [
            result.get("exception_message") for result in results if result.get("status") != "passed"
        ],
    }


def formal_matrix(repeats: int, timeout_seconds: int) -> dict[str, object]:
    before = file_hashes()
    cases: list[tuple[str, int]] = [
        ("C0_plain_torch", 1),
        ("C1_d1_exact", repeats),
        ("C2_official_order", repeats),
        ("C3_torch_preimport_no_cuda", repeats),
        ("C4_pre_cuda_basic", repeats),
        ("C5_pre_cublas", repeats),
    ]
    all_results: dict[str, list[dict[str, object]]] = {}
    boundary_violation = False
    for case, count in cases:
        case_results = []
        for repeat in range(1, count + 1):
            print(f"[D2] {case} repeat {repeat}/{count}", flush=True)
            result = run_fresh(case, repeat, timeout_seconds)
            case_results.append(result)
            if result.get("timed_out") or result.get("worker_alive_after_wait"):
                boundary_violation = True
                break
        all_results[case] = case_results
        print(json.dumps(summarize(case, case_results), sort_keys=True), flush=True)
        if boundary_violation:
            break

    c2_results = all_results.get("C2_official_order", [])
    c2_requires_direct_contrast = any(result.get("status") == "failed" for result in c2_results)
    direct_tested = False
    if not boundary_violation and c2_requires_direct_contrast:
        direct_tested = True
        direct_results = []
        for repeat in range(1, repeats + 1):
            print(f"[D2] C6_direct_simulationapp repeat {repeat}/{repeats}", flush=True)
            result = run_fresh("C6_direct_simulationapp", repeat, timeout_seconds)
            direct_results.append(result)
            if result.get("timed_out") or result.get("worker_alive_after_wait"):
                boundary_violation = True
                break
        all_results["C6_direct_simulationapp"] = direct_results
        print(json.dumps(summarize("C6_direct_simulationapp", direct_results), sort_keys=True), flush=True)

    after = file_hashes()
    unchanged = before == after
    if not unchanged:
        boundary_violation = True
    summaries = {case: summarize(case, results) for case, results in all_results.items()}
    output = {
        "classification": BOUNDARY_STOP if boundary_violation else CLASSIFICATION,
        "inventory": inventory(),
        "fresh_process_policy": True,
        "repeat_default": repeats,
        "case_results": all_results,
        "summaries": summaries,
        "direct_simulationapp_tested": direct_tested,
        "protected_hash_count": len(before),
        "protected_hashes_unchanged": unchanged,
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "environment_constructed": False,
        "environment_steps": 0,
        "harl_executed": False,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "original_v2_rerun": False,
    }
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument(
        "--case",
        choices=(
            "C0_plain_torch",
            "C1_d1_exact",
            "C2_official_order",
            "C3_torch_preimport_no_cuda",
            "C4_pre_cuda_basic",
            "C5_pre_cublas",
            "C6_direct_simulationapp",
        ),
    )
    parser.add_argument("--result-file")
    parser.add_argument("--repeat", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        if not args.case or not args.result_file:
            raise ValueError("worker requires --case and --result-file")
        return worker(args)
    if not 1 <= args.repeat <= 5:
        raise ValueError("--repeat must be between 1 and 5")
    output = formal_matrix(args.repeat, args.timeout_seconds)
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(output, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
    print(PREFIX + json.dumps(output, sort_keys=True, default=str), flush=True)
    return 2 if output["classification"] == BOUNDARY_STOP else 0


if __name__ == "__main__":
    raise SystemExit(main())
