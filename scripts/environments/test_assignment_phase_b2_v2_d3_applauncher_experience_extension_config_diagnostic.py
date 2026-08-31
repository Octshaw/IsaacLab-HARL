"""B2-V2-D3 fresh-process AppLauncher experience/config boundary diagnostic.

Test-only.  The core B0-B4 matrix never constructs an Isaac environment and
never runs HARL, I0-I6, an optimizer, backward, training, playback, evaluation,
or the original B2-V2 harness.  It diagnoses startup composition only.
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


COMPLETE = (
    "PHASE-B2-V2-D3-APPLAUNCHER-EXPERIENCE-EXTENSION-CONFIG-"
    "BOUNDARY-DIAGNOSTIC-COMPLETE-AWAITING-GPT-REVIEW"
)
BASELINE_STOP = "PHASE-B2-V2-D3-STOP-BASELINE-NONREPRODUCIBLE"
BOUNDARY_STOP = "PHASE-B2-V2-D3-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
CONTROL_STOP = "PHASE-B2-V2-D3-STOP-APPLAUNCHER-CONTROL-NONREPRODUCIBLE"
INTERMITTENT_STOP = "PHASE-B2-V2-D3-STOP-INTERMITTENT-APPLAUNCHER-CONFIG-BOUNDARY"
ORIGINAL_ERROR = "CUBLAS_STATUS_NOT_INITIALIZED"
DEVICE = "cuda:0"
MATRIX_DIM = 8
SEED = 260826
PREFIX = "__B2_V2_D3_RESULT__"
ACTIVE_RESULT_PATH: str | None = None
CURRENT_SUBSTAGE = "worker_start"

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
ISAAC_SITE = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim")
APP_LAUNCHER = ROOT / "source" / "isaaclab" / "isaaclab" / "app" / "app_launcher.py"
HEADLESS_EXPERIENCE = ROOT / "apps" / "isaaclab.python.headless.kit"
BASE_PYTHON_EXPERIENCE = ISAAC_SITE / "apps" / "isaacsim.exp.base.python.kit"
BASE_EXPERIENCE = ISAAC_SITE / "apps" / "isaacsim.exp.base.kit"
SIMULATION_APP_SOURCE = (
    ISAAC_SITE
    / "exts"
    / "isaacsim.simulation_app"
    / "isaacsim"
    / "simulation_app"
    / "simulation_app.py"
)
V2_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py"
D1_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py"
D2_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py"

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
) + (
    V2_HARNESS,
    D1_HARNESS,
    D2_HARNESS,
    APP_LAUNCHER,
    HEADLESS_EXPERIENCE,
    BASE_PYTHON_EXPERIENCE,
    BASE_EXPERIENCE,
    SIMULATION_APP_SOURCE,
)


def set_substage(name: str) -> None:
    global CURRENT_SUBSTAGE
    CURRENT_SUBSTAGE = name


def normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [normalize(item) for item in value]
    return repr(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes() -> dict[str, str]:
    missing = [str(path) for path in PROTECTED if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"protected files missing: {missing}")
    return {str(path): sha256(path) for path in PROTECTED}


def nvidia_inventory() -> dict[str, object]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def module_snapshot(label: str) -> dict[str, object]:
    torch_loaded = "torch" in sys.modules
    result: dict[str, object] = {
        "label": label,
        "torch_in_sys_modules": torch_loaded,
        "isaacsim_in_sys_modules": "isaacsim" in sys.modules,
        "isaaclab_app_in_sys_modules": "isaaclab.app" in sys.modules,
    }
    if torch_loaded:
        torch = sys.modules["torch"]
        initialized = bool(torch.cuda.is_initialized())
        result["torch_cuda_initialized"] = initialized
        if initialized:
            result["memory_allocated"] = int(torch.cuda.memory_allocated(0))
            result["memory_reserved"] = int(torch.cuda.memory_reserved(0))
    return result


def snapshot(timeline: list[dict[str, object]], label: str) -> None:
    timeline.append(module_snapshot(label))


def torch_cuda_state(torch: Any, label: str) -> dict[str, object]:
    initialized = bool(torch.cuda.is_initialized())
    result: dict[str, object] = {"label": label, "initialized": initialized}
    if initialized:
        result.update(
            {
                "device": int(torch.cuda.current_device()),
                "memory_allocated": int(torch.cuda.memory_allocated(0)),
                "memory_reserved": int(torch.cuda.memory_reserved(0)),
            }
        )
    return result


def cuda_probe(torch: Any, timeline: list[dict[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    snapshot(timeline, "before_cuda_allocation")
    set_substage("cuda_alloc_call")
    x = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    set_substage("cuda_alloc_sync")
    torch.cuda.synchronize()
    set_substage("cuda_basic_kernel")
    y = x + 1.0
    set_substage("cuda_basic_sync")
    torch.cuda.synchronize()
    result["basic"] = {
        "status": "PASS",
        "device": str(y.device),
        "dtype": str(y.dtype),
        "shape": list(y.shape),
        "finite": bool(torch.isfinite(y).all().item()),
        "sum": float(y.sum().item()),
        "state": torch_cuda_state(torch, "post_basic"),
    }

    set_substage("matmul_input_call")
    other = torch.arange(MATRIX_DIM * MATRIX_DIM, dtype=torch.float32, device=DEVICE).reshape(
        MATRIX_DIM, MATRIX_DIM
    )
    set_substage("matmul_input_sync")
    torch.cuda.synchronize()
    snapshot(timeline, "before_matmul")
    set_substage("matmul_call")
    with torch.inference_mode():
        product = torch.matmul(x, other)
    set_substage("matmul_sync")
    torch.cuda.synchronize()
    result["matmul"] = {
        "status": "PASS",
        "shape": list(product.shape),
        "finite": bool(torch.isfinite(product).all().item()),
        "sum": float(product.sum().item()),
        "state": torch_cuda_state(torch, "post_matmul"),
    }

    torch.manual_seed(SEED + 1)
    set_substage("linear_construct")
    linear = torch.nn.Linear(MATRIX_DIM, MATRIX_DIM)
    set_substage("linear_to_cuda")
    linear = linear.to(DEVICE)
    set_substage("linear_to_sync")
    torch.cuda.synchronize()
    set_substage("linear_input_call")
    inputs = torch.ones((2, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    set_substage("linear_input_sync")
    torch.cuda.synchronize()
    set_substage("linear_forward")
    with torch.inference_mode():
        output = linear(inputs)
    set_substage("linear_sync")
    torch.cuda.synchronize()
    result["linear"] = {
        "status": "PASS",
        "shape": list(output.shape),
        "finite": bool(torch.isfinite(output).all().item()),
        "state": torch_cuda_state(torch, "post_linear"),
    }
    return result


def enabled_extensions() -> dict[str, object]:
    try:
        import omni.kit.app

        manager = omni.kit.app.get_app().get_extension_manager()
        enabled: list[str] = []
        for extension in manager.get_extensions():
            ext_id = str(extension.get("id") or extension.get("name") or "")
            if ext_id and manager.is_extension_enabled(ext_id):
                enabled.append(ext_id)
        enabled = sorted(set(enabled))
        encoded = "\n".join(enabled).encode("utf-8")
        return {"status": "PASS", "count": len(enabled), "sha256": hashlib.sha256(encoded).hexdigest(), "ids": enabled}
    except BaseException as exc:
        return {"status": "UNAVAILABLE", "exception_type": type(exc).__name__, "exception_message": str(exc)}


def resolved_launcher_state(launcher: object) -> dict[str, object]:
    return {
        "call": "AppLauncher(headless=True)",
        "experience": os.path.abspath(str(getattr(launcher, "_sim_experience_file"))),
        "sim_app_config": normalize(getattr(launcher, "_sim_app_config")),
        "headless": normalize(getattr(launcher, "_headless", None)),
        "device_id": normalize(getattr(launcher, "device_id", None)),
        "livestream": normalize(getattr(launcher, "_livestream", None)),
        "enable_cameras": normalize(getattr(launcher, "_enable_cameras", None)),
        "offscreen_render": normalize(getattr(launcher, "_offscreen_render", None)),
        "render_viewport": normalize(getattr(launcher, "_render_viewport", None)),
        "xr": normalize(getattr(launcher, "_xr", None)),
    }


def run_case(
    case: str,
    resolved_config_json: str | None,
    resolved_experience: str | None,
    variant_id: str | None,
) -> dict[str, object]:
    global ACTIVE_RESULT_PATH
    simulation_app = None
    launcher = None
    timeline: list[dict[str, object]] = []
    evidence: dict[str, object] = {
        "case": case,
        "pid": os.getpid(),
        "timeline": timeline,
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "device": DEVICE,
        "dtype": "torch.float32",
        "matrix_dim": MATRIX_DIM,
        "seed": SEED,
    }
    snapshot(timeline, "process_start")
    try:
        if case == "B1_applauncher":
            snapshot(timeline, "before_applauncher_import")
            set_substage("applauncher_import")
            from isaaclab.app import AppLauncher

            snapshot(timeline, "before_applauncher_constructor")
            set_substage("applauncher_constructor")
            launcher = AppLauncher(headless=True)
            simulation_app = launcher.app
            snapshot(timeline, "immediately_after_startup")
            evidence["startup_path"] = "AppLauncher(headless=True)"
            evidence["resolved_launcher"] = resolved_launcher_state(launcher)
            evidence["simulation_app_config"] = normalize(getattr(simulation_app, "config", None))
        else:
            snapshot(timeline, "before_isaacsim_import")
            set_substage("simulationapp_import")
            from isaacsim import SimulationApp

            snapshot(timeline, "before_simulationapp_constructor")
            if case == "B0_direct_minimal":
                launch_config = {"headless": True}
                experience = ""
                evidence["startup_path"] = "SimulationApp({'headless': True})"
            elif case == "B2_direct_experience_only":
                if not resolved_experience:
                    raise ValueError("B2 requires resolved AppLauncher experience")
                launch_config = {"headless": True}
                experience = resolved_experience
                evidence["startup_path"] = "direct SimulationApp + AppLauncher experience + minimal config"
            elif case == "B3_direct_config_only":
                if not resolved_config_json:
                    raise ValueError("B3 requires resolved AppLauncher config")
                launch_config = json.loads(resolved_config_json)
                experience = ""
                evidence["startup_path"] = "direct SimulationApp + AppLauncher config + default experience"
            elif case == "B4_direct_experience_config":
                if not resolved_config_json or not resolved_experience:
                    raise ValueError("B4 requires resolved AppLauncher experience and config")
                launch_config = json.loads(resolved_config_json)
                experience = resolved_experience
                evidence["startup_path"] = "direct SimulationApp + AppLauncher experience + config"
            elif case == "G_direct_variant":
                if not resolved_experience or not variant_id:
                    raise ValueError("G_direct_variant requires an experience path and variant id")
                launch_config = {"headless": True}
                experience = resolved_experience
                evidence["startup_path"] = "direct SimulationApp + test-only D3 experience variant"
                evidence["variant_id"] = variant_id
                evidence["variant_experience_sha256"] = sha256(Path(experience))
            else:
                raise ValueError(f"unknown D3 core case: {case}")
            evidence["requested_config"] = normalize(launch_config)
            evidence["requested_experience"] = experience or "<SimulationApp default resolution>"
            set_substage("simulationapp_constructor")
            simulation_app = SimulationApp(launch_config, experience=experience)
            snapshot(timeline, "immediately_after_startup")
            evidence["simulation_app_config"] = normalize(getattr(simulation_app, "config", None))

        evidence["enabled_extensions"] = enabled_extensions()
        snapshot(timeline, "before_explicit_torch_access")
        set_substage("torch_import_or_access")
        import torch

        snapshot(timeline, "after_explicit_torch_access")
        evidence["torch_version"] = torch.__version__
        evidence["torch_cuda_version"] = torch.version.cuda
        evidence["pre_probe_cuda_state"] = torch_cuda_state(torch, "pre_probe")
        evidence["cuda_probe"] = cuda_probe(torch, timeline)

        result = {
            "case": case,
            "status": "passed",
            "evidence": evidence,
            "failed_substage": None,
            "original_error_reproduced": False,
            "shutdown_requested": simulation_app is not None,
            "nvidia_smi_after_operations": nvidia_inventory(),
        }
        write_result(ACTIVE_RESULT_PATH, result)
        print(PREFIX + json.dumps({"case": case, "status": "passed"}), flush=True)
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
            "original_error_reproduced": ORIGINAL_ERROR in f"{type(exc).__name__}: {exc}",
            "shutdown_requested": simulation_app is not None,
            "nvidia_smi_after_operations": nvidia_inventory(),
        }
        write_result(ACTIVE_RESULT_PATH, result)
        print(PREFIX + json.dumps({"case": case, "status": "failed", "substage": CURRENT_SUBSTAGE, "error": str(exc)}), flush=True)
        raise
    finally:
        if simulation_app is not None:
            set_substage("simulationapp_close")
            simulation_app.close()


def write_result(path: str | None, result: dict[str, object]) -> None:
    if path:
        Path(path).write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")


def worker(args: argparse.Namespace) -> int:
    global ACTIVE_RESULT_PATH
    ACTIVE_RESULT_PATH = args.result_file
    try:
        run_case(args.case, args.resolved_config_json, args.resolved_experience, args.variant_id)
        return 0
    except BaseException as exc:
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        if not Path(args.result_file).is_file():
            write_result(
                args.result_file,
                {
                    "case": args.case,
                    "status": "failed",
                    "failed_substage": CURRENT_SUBSTAGE,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "traceback": traceback.format_exc(),
                    "original_error_reproduced": ORIGINAL_ERROR in str(exc),
                },
            )
        return 1


def run_fresh(
    case: str,
    repeat: int,
    timeout_seconds: int,
    resolved_config: dict[str, object] | None = None,
    resolved_experience: str | None = None,
    variant_id: str | None = None,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"b2_v2_d3_{case.lower()}_{repeat}_") as temp:
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
        if resolved_config is not None:
            command += ["--resolved-config-json", json.dumps(resolved_config, separators=(",", ":"))]
        if resolved_experience is not None:
            command += ["--resolved-experience", resolved_experience]
        if variant_id is not None:
            command += ["--variant-id", variant_id]
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
        stdout_bytes = stdout.encode("utf-8", errors="replace")
        result.update(
            {
                "repeat": repeat,
                "worker_pid": process.pid,
                "process_exit_code": process.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "timed_out": timed_out,
                "worker_alive_after_wait": process.poll() is None,
                "safe_shutdown": not timed_out and process.poll() is not None,
                "stdout_stderr_line_count": len(stdout.splitlines()),
                "stdout_stderr_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
                "stdout_stderr_tail": stdout[-12000:],
                "nvidia_smi_supervisor_before": before_gpu,
                "nvidia_smi_supervisor_after": nvidia_inventory(),
            }
        )
        return result


def summary(case: str, results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "case": case,
        "runs": len(results),
        "pass": sum(result.get("status") == "passed" for result in results),
        "fail": sum(result.get("status") != "passed" for result in results),
        "original_error": sum(bool(result.get("original_error_reproduced")) for result in results),
        "timeouts": sum(bool(result.get("timed_out")) for result in results),
        "surviving_workers": sum(bool(result.get("worker_alive_after_wait")) for result in results),
        "failed_substages": [result.get("failed_substage") for result in results if result.get("status") != "passed"],
        "exception_messages": [result.get("exception_message") for result in results if result.get("status") != "passed"],
    }


def stable_status(results: list[dict[str, object]]) -> str:
    passed = sum(result.get("status") == "passed" for result in results)
    if passed == len(results):
        return "PASS"
    if passed == 0:
        return "FAIL"
    return "MIXED"


def consensus_launcher(results: list[dict[str, object]]) -> tuple[dict[str, object], str]:
    states = [result["evidence"]["resolved_launcher"] for result in results]
    config_encodings = {json.dumps(state["sim_app_config"], sort_keys=True) for state in states}
    experiences = {os.path.abspath(state["experience"]) for state in states}
    if len(config_encodings) != 1 or len(experiences) != 1:
        raise RuntimeError("B1 AppLauncher resolved inputs were not identical across repeats")
    return json.loads(next(iter(config_encodings))), next(iter(experiences))


def inventory() -> dict[str, object]:
    versions: dict[str, str | None] = {}
    for distribution in ("torch", "isaacsim", "isaaclab", "isaaclab-tasks", "harl"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "windows": platform.platform(),
        "versions": versions,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "git_describe": subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip(),
        "nvidia_smi": nvidia_inventory(),
        "cuda_environment": {
            key: value
            for key, value in os.environ.items()
            if key.upper().startswith("CUDA") or key.upper().startswith("PYTORCH_CUDA")
        },
        "static_paths": {
            "app_launcher": str(APP_LAUNCHER),
            "app_launcher_sha256": sha256(APP_LAUNCHER),
            "headless_experience": str(HEADLESS_EXPERIENCE),
            "headless_experience_sha256": sha256(HEADLESS_EXPERIENCE),
            "base_python_experience": str(BASE_PYTHON_EXPERIENCE),
            "base_python_experience_sha256": sha256(BASE_PYTHON_EXPERIENCE),
            "base_experience": str(BASE_EXPERIENCE),
            "base_experience_sha256": sha256(BASE_EXPERIENCE),
            "simulation_app_source": str(SIMULATION_APP_SOURCE),
            "simulation_app_source_sha256": sha256(SIMULATION_APP_SOURCE),
        },
    }


def run_core(repeats: int, timeout_seconds: int) -> dict[str, object]:
    before = file_hashes()
    results: dict[str, list[dict[str, object]]] = {}
    classification = COMPLETE
    stop_reason = None

    def execute(case: str, config: dict[str, object] | None = None, experience: str | None = None) -> list[dict[str, object]]:
        case_results: list[dict[str, object]] = []
        for repeat in range(1, repeats + 1):
            print(f"[D3] {case} repeat {repeat}/{repeats}", flush=True)
            item = run_fresh(case, repeat, timeout_seconds, config, experience)
            case_results.append(item)
            if item.get("timed_out") or item.get("worker_alive_after_wait"):
                break
        results[case] = case_results
        print(json.dumps(summary(case, case_results), sort_keys=True), flush=True)
        return case_results

    b0 = execute("B0_direct_minimal")
    if len(b0) != repeats or stable_status(b0) != "PASS":
        classification = BASELINE_STOP
        stop_reason = "direct minimal SimulationApp baseline was not PASS in every formal repeat"
    else:
        b1 = execute("B1_applauncher")
        b1_status = stable_status(b1)
        if len(b1) != repeats or b1_status == "MIXED":
            classification = INTERMITTENT_STOP
            stop_reason = "AppLauncher control was mixed or incomplete"
        elif b1_status != "FAIL" or not all(item.get("original_error_reproduced") for item in b1):
            classification = CONTROL_STOP
            stop_reason = "AppLauncher control did not reproduce the exact failure in every repeat"
        else:
            resolved_config, resolved_experience = consensus_launcher(b1)
            execute("B2_direct_experience_only", {"headless": True}, resolved_experience)
            execute("B3_direct_config_only", resolved_config, None)
            execute("B4_direct_experience_config", resolved_config, resolved_experience)

    after = file_hashes()
    changed = before != after
    unsafe = any(
        item.get("timed_out") or item.get("worker_alive_after_wait")
        for case_results in results.values()
        for item in case_results
    )
    if changed or unsafe:
        classification = BOUNDARY_STOP
        stop_reason = (
            "protected hash change"
            if changed
            else "extension variant worker timed out and did not demonstrate safe SimulationApp shutdown"
        )

    launcher_config = None
    launcher_experience = None
    if "B1_applauncher" in results and stable_status(results["B1_applauncher"]) == "FAIL":
        launcher_config, launcher_experience = consensus_launcher(results["B1_applauncher"])
    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "inventory": inventory(),
        "core_results": results,
        "summaries": {case: summary(case, items) for case, items in results.items()},
        "stable_status": {case: stable_status(items) for case, items in results.items()},
        "resolved_app_launcher_config": launcher_config,
        "resolved_app_launcher_experience": launcher_experience,
        "protected_hash_count": len(before),
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "protected_hashes_unchanged": not changed,
        "fresh_process_policy": True,
        "timeout_seconds": timeout_seconds,
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "original_v2_rerun": False,
    }


ISAACLAB_DEPENDENCIES = (
    '"isaaclab" = {order = 1000}',
    '"isaaclab_assets" = {order = 1000}',
    '"isaaclab_tasks" = {order = 1000}',
    '"isaaclab_mimic" = {order = 1000}',
    '"isaaclab_rl" = {order = 1000}',
)
PHYSX_FABRIC_DEPENDENCY = '"omni.physx.fabric" = {}'


def write_variant(
    directory: Path,
    variant_id: str,
    *,
    remove_isaaclab: bool = False,
    remove_fabric: bool = False,
    add_base_python: bool = False,
) -> tuple[Path, dict[str, object]]:
    source = HEADLESS_EXPERIENCE.read_text(encoding="utf-8")
    original_app_root = str((ROOT / "apps").resolve()).replace("\\", "/")
    source = source.replace("${app}", original_app_root)
    removed: list[str] = []
    lines: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        should_remove = (remove_isaaclab and stripped in ISAACLAB_DEPENDENCIES) or (
            remove_fabric and stripped == PHYSX_FABRIC_DEPENDENCY
        )
        if should_remove:
            removed.append(stripped)
        else:
            lines.append(line)
    added: list[str] = []
    if add_base_python:
        added.append('"isaacsim.exp.base.python" = {}')
        lines += ["", "# D3 test-only added dependency", "[dependencies]", *added]
    path = directory / f"b2_v2_d3_{variant_id.lower()}.kit"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, {
        "variant_id": variant_id,
        "base": str(HEADLESS_EXPERIENCE),
        "base_sha256": sha256(HEADLESS_EXPERIENCE),
        "path": str(path),
        "sha256": sha256(path),
        "removed_dependencies": removed,
        "added_dependencies": added,
        "app_token_rewritten_to": original_app_root,
    }


def run_extension_isolation(core_result_path: Path, repeats: int, timeout_seconds: int) -> dict[str, object]:
    core = json.loads(core_result_path.read_text(encoding="utf-8"))
    expected = {
        "B0_direct_minimal": "PASS",
        "B1_applauncher": "FAIL",
        "B2_direct_experience_only": "FAIL",
        "B3_direct_config_only": "PASS",
        "B4_direct_experience_config": "FAIL",
    }
    if core.get("stable_status") != expected:
        raise RuntimeError(f"extension isolation requires exact stable core scenario A, got {core.get('stable_status')}")

    before = file_hashes()
    results: dict[str, list[dict[str, object]]] = {}
    manifests: dict[str, dict[str, object]] = {}
    classification = COMPLETE
    stop_reason = None

    def execute(variant_id: str, path: Path) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for repeat in range(1, repeats + 1):
            print(f"[D3] {variant_id} repeat {repeat}/{repeats}", flush=True)
            item = run_fresh(
                "G_direct_variant",
                repeat,
                timeout_seconds,
                resolved_experience=str(path),
                variant_id=variant_id,
            )
            items.append(item)
            if item.get("timed_out") or item.get("worker_alive_after_wait"):
                break
        results[variant_id] = items
        print(json.dumps(summary(variant_id, items), sort_keys=True), flush=True)
        return items

    with tempfile.TemporaryDirectory(prefix="b2_v2_d3_variants_") as temp:
        variant_root = Path(temp)
        definitions = (
            ("G1_NO_ISAACLAB", {"remove_isaaclab": True}),
            ("G2_NO_PHYSX_FABRIC", {"remove_fabric": True}),
            ("G3_NO_ISAACLAB_OR_FABRIC", {"remove_isaaclab": True, "remove_fabric": True}),
        )
        for variant_id, options in definitions:
            path, manifest = write_variant(variant_root, variant_id, **options)
            manifests[variant_id] = manifest
            items = execute(variant_id, path)
            if len(items) != repeats or stable_status(items) == "MIXED":
                classification = INTERMITTENT_STOP
                stop_reason = f"{variant_id} was mixed or incomplete"
                break

        if classification == COMPLETE and all(stable_status(items) == "FAIL" for items in results.values()):
            variant_id = "G4_ADD_BASE_PYTHON_GROUP"
            path, manifest = write_variant(variant_root, variant_id, add_base_python=True)
            manifests[variant_id] = manifest
            items = execute(variant_id, path)
            if len(items) != repeats or stable_status(items) == "MIXED":
                classification = INTERMITTENT_STOP
                stop_reason = f"{variant_id} was mixed or incomplete"

    after = file_hashes()
    changed = before != after
    unsafe = any(
        item.get("timed_out") or item.get("worker_alive_after_wait")
        for case_results in results.values()
        for item in case_results
    )
    if changed or unsafe:
        classification = BOUNDARY_STOP
        stop_reason = "protected hash change or unsafe worker lifecycle"

    statuses = {variant_id: stable_status(items) for variant_id, items in results.items()}
    if classification == COMPLETE:
        no_lab = statuses.get("G1_NO_ISAACLAB")
        no_fabric = statuses.get("G2_NO_PHYSX_FABRIC")
        no_both = statuses.get("G3_NO_ISAACLAB_OR_FABRIC")
        if no_lab == "FAIL" and no_fabric == "PASS":
            boundary = "OMNI_PHYSX_FABRIC_EXTENSION_INCLUSION_BOUNDARY"
        elif no_lab == "PASS" and no_fabric == "FAIL":
            boundary = "ISAACLAB_EXTENSION_GROUP_INCLUSION_BOUNDARY"
        elif no_lab == "FAIL" and no_fabric == "FAIL" and no_both == "PASS":
            boundary = "ISAACLAB_PHYSX_FABRIC_EXTENSION_GROUP_INTERACTION_BOUNDARY"
        elif no_lab == "PASS" and no_fabric == "PASS":
            boundary = "ISAACLAB_PHYSX_FABRIC_JOINT_NECESSITY_BOUNDARY"
        elif statuses.get("G4_ADD_BASE_PYTHON_GROUP") == "PASS":
            boundary = "ISAAC_SIM_BASE_PYTHON_EXTENSION_GROUP_RESTORES_PASS_BOUNDARY"
        else:
            boundary = "HEADLESS_EXPERIENCE_NONUNIQUE_EXTENSION_OR_SETTINGS_BOUNDARY_REMAINS"
    else:
        boundary = None

    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "core_result_path": str(core_result_path),
        "variant_results": results,
        "summaries": {variant_id: summary(variant_id, items) for variant_id, items in results.items()},
        "stable_status": statuses,
        "variant_manifests": manifests,
        "narrowest_observed_boundary": boundary,
        "protected_hash_count": len(before),
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "protected_hashes_unchanged": not changed,
        "temporary_variants_removed": True,
        "environment_constructed": False,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "original_v2_rerun": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument(
        "--case",
        choices=(
            "B0_direct_minimal",
            "B1_applauncher",
            "B2_direct_experience_only",
            "B3_direct_config_only",
            "B4_direct_experience_config",
            "G_direct_variant",
        ),
    )
    parser.add_argument("--result-file")
    parser.add_argument("--resolved-config-json")
    parser.add_argument("--resolved-experience")
    parser.add_argument("--variant-id")
    parser.add_argument("--extension-isolation-core-result")
    parser.add_argument("--repeat", type=int, default=3)
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
    if args.extension_isolation_core_result:
        result = run_extension_isolation(
            Path(args.extension_isolation_core_result), args.repeat, args.timeout_seconds
        )
    else:
        result = run_core(args.repeat, args.timeout_seconds)
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(
        PREFIX
        + json.dumps(
            {
                "classification": result["classification"],
                "summaries": result["summaries"],
                "narrowest_observed_boundary": result.get("narrowest_observed_boundary"),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 2 if result["classification"] in {BASELINE_STOP, BOUNDARY_STOP, CONTROL_STOP, INTERMITTENT_STOP} else 0


if __name__ == "__main__":
    raise SystemExit(main())
