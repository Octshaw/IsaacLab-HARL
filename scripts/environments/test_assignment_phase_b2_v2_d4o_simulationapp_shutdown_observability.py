"""B2-V2-D4-O standalone SimulationApp shutdown observability diagnostic.

Test-only.  This script distinguishes diagnostic results from shutdown evidence.
It never constructs an MRTA environment and never executes HARL, I0-I6, an
optimizer, backward, training, playback, evaluation, or the original B2-V2.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any


COMPLETE = (
    "PHASE-B2-V2-D4O-SIMULATIONAPP-SHUTDOWN-OBSERVABILITY-"
    "CONTRACT-COMPLETE-AWAITING-GPT-REVIEW"
)
CONTRACT_STOP = "PHASE-B2-V2-D4O-STOP-SHUTDOWN-CONTRACT-NONREPRODUCIBLE"
BOUNDARY_STOP = "PHASE-B2-V2-D4O-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
IN_PROCESS = "IN_PROCESS_CLOSE_RETURN"
EXTERNAL_CLEAN = "EXTERNAL_CLEAN_TERMINATION"
UNSAFE = "UNSAFE_OR_INCONCLUSIVE_TERMINATION"
EXPECTED_FAILURE = "EXPECTED_TEST_FAILURE"
CUDA_PASS = "CUDA_PASS"
NOOP_PASS = "NOOP_PASS"
TIMEOUT_SECONDS = 180
EXPECTED_FAILURE_EXIT_CODE = 10
DEVICE = "cuda:0"
MATRIX_DIM = 8
SEED = 260826
PREFIX = "__B2_V2_D4O_RESULT__"

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
ISAAC_SITE = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim")
APP_LAUNCHER = ROOT / "source" / "isaaclab" / "isaaclab" / "app" / "app_launcher.py"
HEADLESS_EXPERIENCE = ROOT / "apps" / "isaaclab.python.headless.kit"
BASE_PYTHON_EXPERIENCE = ISAAC_SITE / "apps" / "isaacsim.exp.base.python.kit"
BASE_EXPERIENCE = ISAAC_SITE / "apps" / "isaacsim.exp.base.kit"
SIMULATION_APP_SOURCE = (
    ISAAC_SITE / "exts" / "isaacsim.simulation_app" / "isaacsim" / "simulation_app" / "simulation_app.py"
)
V2_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py"
D1_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py"
D2_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py"
D3_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py"
D4_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py"
D4O_HARNESS = Path(__file__).resolve()

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
    D3_HARNESS,
    D4_HARNESS,
)


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


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, default=str)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


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


class Checkpoints:
    def __init__(self, path: Path, control: str):
        self.path = path
        self.control = control
        self.events: list[dict[str, object]] = []

    def emit(self, stage: str, label: str, details: dict[str, object] | None = None) -> None:
        event = {
            "sequence": len(self.events),
            "stage": stage,
            "label": label,
            "pid": os.getpid(),
            "monotonic_seconds": time.monotonic(),
            "details": normalize(details or {}),
        }
        self.events.append(event)
        atomic_json(
            self.path,
            {
                "control": self.control,
                "last_completed_checkpoint": stage,
                "events": self.events,
            },
        )


def known_descendants() -> dict[str, object]:
    try:
        import psutil

        children: list[dict[str, object]] = []
        for child in psutil.Process(os.getpid()).children(recursive=True):
            try:
                children.append(
                    {
                        "pid": child.pid,
                        "create_time": child.create_time(),
                        "name": child.name(),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"status": "PASS", "method": "psutil recursive pre-close snapshot", "children": children}
    except BaseException as exc:
        return {
            "status": "UNAVAILABLE",
            "method": "psutil recursive pre-close snapshot",
            "children": [],
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }


def cuda_body() -> dict[str, object]:
    import torch

    x = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    torch.cuda.synchronize()
    y = x + 1.0
    torch.cuda.synchronize()
    other = torch.arange(MATRIX_DIM * MATRIX_DIM, dtype=torch.float32, device=DEVICE).reshape(
        MATRIX_DIM, MATRIX_DIM
    )
    with torch.inference_mode():
        product = torch.matmul(x, other)
    torch.cuda.synchronize()
    torch.manual_seed(SEED)
    linear = torch.nn.Linear(MATRIX_DIM, MATRIX_DIM).to(DEVICE)
    inputs = torch.ones((2, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
    with torch.inference_mode():
        output = linear(inputs)
    torch.cuda.synchronize()
    return {
        "device": str(x.device),
        "dtype": str(x.dtype),
        "matrix_shape": list(x.shape),
        "basic_finite": bool(torch.isfinite(y).all().item()),
        "basic_sum": float(y.sum().item()),
        "matmul_finite": bool(torch.isfinite(product).all().item()),
        "matmul_sum": float(product.sum().item()),
        "linear_shape": list(output.shape),
        "linear_finite": bool(torch.isfinite(output).all().item()),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
    }


def worker_main(args: argparse.Namespace) -> int:
    checkpoint_path = Path(args.checkpoint_file)
    primary_path = Path(args.primary_result_file)
    checkpoints = Checkpoints(checkpoint_path, args.control)
    checkpoints.emit("O0", "worker_started")
    simulation_app = None
    primary: dict[str, object] = {
        "control": args.control,
        "diagnostic_result": "UNEXPECTED_FAILURE",
        "diagnostic_details": {},
        "expected_diagnostic_failure": False,
        "close_invoked": False,
        "close_returned": False,
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }
    try:
        from isaacsim import SimulationApp

        checkpoints.emit("O1", "immediately_before_SimulationApp_constructor")
        simulation_app = SimulationApp({"headless": True})
        primary["fast_shutdown"] = bool(simulation_app.config.get("fast_shutdown"))
        checkpoints.emit(
            "O2",
            "SimulationApp_constructor_returned",
            {"fast_shutdown": primary["fast_shutdown"]},
        )

        if args.control == "T0_NOOP":
            primary["diagnostic_result"] = NOOP_PASS
            primary["diagnostic_details"] = {"operation": "no-op"}
        elif args.control == "T1_CUDA":
            primary["diagnostic_result"] = CUDA_PASS
            primary["diagnostic_details"] = cuda_body()
        elif args.control == "T2_EXPECTED_FAILURE":
            primary["diagnostic_result"] = EXPECTED_FAILURE
            primary["expected_diagnostic_failure"] = True
            primary["diagnostic_details"] = {
                "operation": "authorized synthetic Python diagnostic failure artifact",
                "cuda_failure": False,
            }
        else:
            raise ValueError(f"unknown control {args.control}")
        checkpoints.emit(
            "O3",
            "diagnostic_body_complete",
            {"diagnostic_result": primary["diagnostic_result"]},
        )
    except BaseException as exc:
        primary.update(
            {
                "diagnostic_result": "UNEXPECTED_FAILURE",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )

    atomic_json(primary_path, primary)
    checkpoints.emit(
        "O4",
        "primary_result_persisted",
        {"diagnostic_result": primary["diagnostic_result"]},
    )
    if simulation_app is None:
        return 1

    process_tree = known_descendants()
    primary["known_process_tree_before_close"] = process_tree
    primary["close_invoked"] = True
    atomic_json(primary_path, primary)
    checkpoints.emit(
        "O5",
        "immediately_before_SimulationApp_close",
        {"known_process_tree": process_tree},
    )
    simulation_app.close()

    primary["close_returned"] = True
    checkpoints.emit("O6", "SimulationApp_close_returned")
    atomic_json(primary_path, primary)
    return EXPECTED_FAILURE_EXIT_CODE if primary["expected_diagnostic_failure"] else 0


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
    else:
        process.kill()


def child_survivors(children: list[dict[str, object]], wait_seconds: float = 5.0) -> list[dict[str, object]]:
    import psutil

    deadline = time.monotonic() + wait_seconds
    survivors: list[dict[str, object]] = []
    while True:
        survivors = []
        for recorded in children:
            try:
                process = psutil.Process(int(recorded["pid"]))
                same_process = abs(process.create_time() - float(recorded["create_time"])) < 0.01
                if same_process and process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    survivors.append(recorded)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not survivors or time.monotonic() >= deadline:
            return survivors
        time.sleep(0.1)


def classify_shutdown(evidence: dict[str, object]) -> dict[str, object]:
    checkpoints = set(evidence.get("checkpoints", []))
    diagnostic_result = evidence.get("diagnostic_result")
    expected_failure = diagnostic_result == EXPECTED_FAILURE and bool(evidence.get("expected_diagnostic_failure"))
    expected_exit = evidence.get("exit_code") == EXPECTED_FAILURE_EXIT_CODE and expected_failure
    normal_or_expected_exit = evidence.get("exit_code") == 0 or expected_exit
    unsafe_reasons: list[str] = []
    if evidence.get("timed_out"):
        unsafe_reasons.append("supervisor timeout")
    if evidence.get("supervisor_kill_used"):
        unsafe_reasons.append("supervisor process-tree kill used")
    if evidence.get("main_worker_alive"):
        unsafe_reasons.append("main worker remains alive")
    if evidence.get("known_child_survivors"):
        unsafe_reasons.append("known child process remains alive")
    if not evidence.get("primary_result_valid"):
        unsafe_reasons.append("primary result missing or corrupt")
    if "O4" not in checkpoints:
        unsafe_reasons.append("O4 primary result checkpoint missing")
    if "O5" not in checkpoints:
        unsafe_reasons.append("O5 pre-close checkpoint missing")
    if not evidence.get("supervisor_cleanup_pass"):
        unsafe_reasons.append("supervisor cleanup failed")
    if not evidence.get("protected_files_unchanged", True):
        unsafe_reasons.append("protected files changed")
    if not normal_or_expected_exit:
        unsafe_reasons.append("unexpected non-zero process exit")
    if unsafe_reasons:
        return {"shutdown_class": UNSAFE, "safe_shutdown": False, "reasons": unsafe_reasons}
    if "O6" in checkpoints:
        return {
            "shutdown_class": IN_PROCESS,
            "safe_shutdown": True,
            "reasons": ["O4/O5/O6 persisted and process terminated without supervisor intervention"],
        }
    return {
        "shutdown_class": EXTERNAL_CLEAN,
        "safe_shutdown": True,
        "reasons": [
            "O4/O5 persisted, no O6 claim, process terminated without supervisor intervention, no known survivor"
        ],
    }


def synthetic_oracle() -> dict[str, object]:
    base = {
        "checkpoints": ["O0", "O1", "O2", "O3", "O4", "O5"],
        "diagnostic_result": NOOP_PASS,
        "expected_diagnostic_failure": False,
        "exit_code": 0,
        "timed_out": False,
        "supervisor_kill_used": False,
        "main_worker_alive": False,
        "known_child_survivors": [],
        "primary_result_valid": True,
        "supervisor_cleanup_pass": True,
        "protected_files_unchanged": True,
    }
    definitions: list[tuple[str, dict[str, object], str]] = [
        ("in_process", {**base, "checkpoints": [*base["checkpoints"], "O6"]}, IN_PROCESS),
        ("external_clean", dict(base), EXTERNAL_CLEAN),
        ("timeout", {**base, "timed_out": True, "supervisor_kill_used": True}, UNSAFE),
        ("surviving_worker", {**base, "main_worker_alive": True}, UNSAFE),
        ("surviving_child", {**base, "known_child_survivors": [{"pid": 42}]}, UNSAFE),
        ("missing_O4", {**base, "checkpoints": ["O0", "O1", "O2", "O3", "O5"]}, UNSAFE),
        ("missing_O5", {**base, "checkpoints": ["O0", "O1", "O2", "O3", "O4"]}, UNSAFE),
        ("corrupt_result", {**base, "primary_result_valid": False}, UNSAFE),
        ("cleanup_failure", {**base, "supervisor_cleanup_pass": False}, UNSAFE),
        ("protected_change", {**base, "protected_files_unchanged": False}, UNSAFE),
        ("unexpected_nonzero", {**base, "exit_code": 7}, UNSAFE),
        (
            "expected_failure_nonzero",
            {
                **base,
                "diagnostic_result": EXPECTED_FAILURE,
                "expected_diagnostic_failure": True,
                "exit_code": EXPECTED_FAILURE_EXIT_CODE,
            },
            EXTERNAL_CLEAN,
        ),
    ]
    results: dict[str, dict[str, object]] = {}
    for name, evidence, expected in definitions:
        classification = classify_shutdown(evidence)
        results[name] = {
            "expected": expected,
            "actual": classification["shutdown_class"],
            "pass": classification["shutdown_class"] == expected,
            "classification": classification,
        }
    return {"pass": all(item["pass"] for item in results.values()), "cases": results}


def read_json(path: Path) -> tuple[bool, dict[str, object]]:
    if not path.is_file():
        return False, {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(value, dict), value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return False, {}


def run_fresh(control: str, repeat: int, timeout_seconds: int) -> dict[str, object]:
    temp_root = Path(tempfile.mkdtemp(prefix=f"b2_v2_d4o_{control.lower()}_{repeat}_"))
    primary_path = temp_root / "primary_result.json"
    checkpoint_path = temp_root / "checkpoints.json"
    command = [
        sys.executable,
        "-u",
        str(D4O_HARNESS),
        "--worker",
        "--control",
        control,
        "--primary-result-file",
        str(primary_path),
        "--checkpoint-file",
        str(checkpoint_path),
    ]
    started = time.monotonic()
    before_gpu = nvidia_inventory()
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    timed_out = False
    kill_used = False
    try:
        stdout, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_used = True
        terminate_process_tree(process)
        stdout, _ = process.communicate(timeout=15)

    primary_valid, primary = read_json(primary_path)
    checkpoint_valid, checkpoint = read_json(checkpoint_path)
    events = checkpoint.get("events", []) if checkpoint_valid else []
    checkpoints = [str(event.get("stage")) for event in events]
    known_tree: dict[str, object] = {"status": "NOT_CAPTURED", "children": []}
    for event in events:
        if event.get("stage") == "O5":
            known_tree = event.get("details", {}).get("known_process_tree", known_tree)
    known_children = known_tree.get("children", []) if isinstance(known_tree, dict) else []
    survivors = child_survivors(known_children) if known_tree.get("status") == "PASS" else []
    main_alive = process.poll() is None
    exit_code = process.returncode
    diagnostic_result = primary.get("diagnostic_result") if primary_valid else None
    expected_failure = bool(primary.get("expected_diagnostic_failure")) if primary_valid else False
    stdout_bytes = stdout.encode("utf-8", errors="replace")

    cleanup_error = None
    try:
        shutil.rmtree(temp_root)
    except BaseException as exc:
        cleanup_error = f"{type(exc).__name__}: {exc}"
    cleanup_pass = not temp_root.exists()

    evidence = {
        "checkpoints": checkpoints,
        "diagnostic_result": diagnostic_result,
        "expected_diagnostic_failure": expected_failure,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "main_worker_alive": main_alive,
        "known_child_survivors": survivors,
        "primary_result_valid": primary_valid,
        "supervisor_cleanup_pass": cleanup_pass,
        "protected_files_unchanged": True,
    }
    shutdown = classify_shutdown(evidence)
    return {
        "control": control,
        "repeat": repeat,
        "diagnostic_result": diagnostic_result,
        "diagnostic_details": primary.get("diagnostic_details") if primary_valid else None,
        "fast_shutdown": primary.get("fast_shutdown") if primary_valid else None,
        "expected_diagnostic_failure": expected_failure,
        "checkpoints": checkpoints,
        "checkpoint_events": events,
        "O6_observed": "O6" in checkpoints,
        "close_returned_in_process": "O6" in checkpoints,
        "shutdown_class": shutdown["shutdown_class"],
        "safe_shutdown": shutdown["safe_shutdown"],
        "shutdown_reasons": shutdown["reasons"],
        "process_exit_code": exit_code,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "worker_alive_after_wait": main_alive,
        "known_process_tree_observation": known_tree,
        "known_child_survivors": survivors,
        "process_tree_limitation": "pre-close recursive child snapshot; cannot prove absence of descendants created after O5",
        "primary_result_valid": primary_valid,
        "checkpoint_file_valid": checkpoint_valid,
        "supporting_shutdown_marker_observed": "Simulation App Shutting Down" in stdout,
        "supervisor_cleanup_pass": cleanup_pass,
        "supervisor_cleanup_error": cleanup_error,
        "temporary_directory_remaining": temp_root.exists(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_stderr_line_count": len(stdout.splitlines()),
        "stdout_stderr_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
        "stdout_stderr_tail": stdout[-12000:],
        "nvidia_smi_supervisor_before": before_gpu,
        "nvidia_smi_supervisor_after": nvidia_inventory(),
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }


def control_summary(control: str, results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "control": control,
        "runs": len(results),
        "diagnostic_results": [item.get("diagnostic_result") for item in results],
        "shutdown_classes": [item.get("shutdown_class") for item in results],
        "O6_frequency": sum(bool(item.get("O6_observed")) for item in results),
        "external_clean_frequency": sum(item.get("shutdown_class") == EXTERNAL_CLEAN for item in results),
        "in_process_frequency": sum(item.get("shutdown_class") == IN_PROCESS for item in results),
        "unsafe_frequency": sum(item.get("shutdown_class") == UNSAFE for item in results),
        "exit_codes": [item.get("process_exit_code") for item in results],
        "timeouts": sum(bool(item.get("timed_out")) for item in results),
        "surviving_workers": sum(bool(item.get("worker_alive_after_wait")) for item in results),
        "surviving_known_children": sum(bool(item.get("known_child_survivors")) for item in results),
        "shutdown_markers": sum(bool(item.get("supporting_shutdown_marker_observed")) for item in results),
        "cleanup_passes": sum(bool(item.get("supervisor_cleanup_pass")) for item in results),
        "elapsed_seconds": [item.get("elapsed_seconds") for item in results],
    }


def stable_clean(results: list[dict[str, object]], expected_diagnostic: str) -> bool:
    classes = {item.get("shutdown_class") for item in results}
    return (
        len(classes) == 1
        and classes.issubset({IN_PROCESS, EXTERNAL_CLEAN})
        and all(item.get("diagnostic_result") == expected_diagnostic for item in results)
        and all(item.get("safe_shutdown") for item in results)
    )


def inventory() -> dict[str, object]:
    versions: dict[str, str | None] = {}
    for distribution in ("torch", "isaacsim", "isaaclab", "isaaclab-tasks", "harl", "psutil"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
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
        "simulation_app_source": str(SIMULATION_APP_SOURCE),
        "simulation_app_source_sha256": sha256(SIMULATION_APP_SOURCE),
    }


def run_supervisor(timeout_seconds: int) -> dict[str, object]:
    if timeout_seconds != TIMEOUT_SECONDS:
        raise ValueError("D4-O requires the authorized 180-second timeout")
    before = file_hashes()
    oracle = synthetic_oracle()
    results: dict[str, list[dict[str, object]]] = {}
    classification = COMPLETE
    stop_reason: str | None = None

    if not oracle["pass"]:
        classification = BOUNDARY_STOP
        stop_reason = "pure shutdown classifier oracle failed"
    else:
        for control, repeats, expected in (
            ("T0_NOOP", 3, NOOP_PASS),
            ("T1_CUDA", 3, CUDA_PASS),
            ("T2_EXPECTED_FAILURE", 2, EXPECTED_FAILURE),
        ):
            items: list[dict[str, object]] = []
            for repeat in range(1, repeats + 1):
                print(f"[D4-O] {control} repeat {repeat}/{repeats}", flush=True)
                item = run_fresh(control, repeat, timeout_seconds)
                items.append(item)
                print(json.dumps(control_summary(control, items), sort_keys=True), flush=True)
                if item.get("shutdown_class") == UNSAFE:
                    break
            results[control] = items
            if len(items) != repeats or not stable_clean(items, expected):
                classification = CONTRACT_STOP
                stop_reason = f"{control} did not produce one stable clean shutdown classification in all authorized repeats"
                break

    after = file_hashes()
    protected_unchanged = before == after
    if not protected_unchanged:
        classification = BOUNDARY_STOP
        stop_reason = "protected hashes changed"
    for items in results.values():
        for item in items:
            evidence = {
                "checkpoints": item["checkpoints"],
                "diagnostic_result": item["diagnostic_result"],
                "expected_diagnostic_failure": item["expected_diagnostic_failure"],
                "exit_code": item["process_exit_code"],
                "timed_out": item["timed_out"],
                "supervisor_kill_used": item["supervisor_kill_used"],
                "main_worker_alive": item["worker_alive_after_wait"],
                "known_child_survivors": item["known_child_survivors"],
                "primary_result_valid": item["primary_result_valid"],
                "supervisor_cleanup_pass": item["supervisor_cleanup_pass"],
                "protected_files_unchanged": protected_unchanged,
            }
            final_shutdown = classify_shutdown(evidence)
            item["shutdown_class"] = final_shutdown["shutdown_class"]
            item["safe_shutdown"] = final_shutdown["safe_shutdown"]
            item["shutdown_reasons"] = final_shutdown["reasons"]
    summaries = {control: control_summary(control, items) for control, items in results.items()}
    if classification == COMPLETE and not all(
        item.get("shutdown_class") in {IN_PROCESS, EXTERNAL_CLEAN}
        for items in results.values()
        for item in items
    ):
        classification = CONTRACT_STOP
        stop_reason = "final protected-state-aware shutdown classification was not clean"

    contract_decision = {
        "shutdown_result_domain": [IN_PROCESS, EXTERNAL_CLEAN, UNSAFE],
        "safe_shutdown_definition": f"shutdown_result in {{{IN_PROCESS}, {EXTERNAL_CLEAN}}}",
        "O6_universal_requirement": False,
        "diagnostic_result_is_orthogonal": True,
        "stdout_marker_authority": "supporting only",
        "external_clean_requires": [
            "valid persisted primary result and O4",
            "persisted O5 before close invocation",
            "no O6 claim",
            "normal exit or exact authorized expected-failure exit",
            "no timeout or supervisor kill",
            "main worker dead and no known pre-close descendant survivor",
            "supervisor cleanup pass",
            "protected files unchanged",
        ],
    }
    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "inventory": inventory(),
        "source_audit": {
            "default_fast_shutdown": True,
            "default_documentation": "True to exit process immediately; false to shutdown each extension",
            "close_calls": ["self._app.shutdown()", "self._framework.unload_all_plugins()"],
            "fast_shutdown_modified": False,
            "monkeypatch_used": False,
            "atexit_or_signal_workaround_used": False,
        },
        "synthetic_classifier_oracle": oracle,
        "results": results,
        "summaries": summaries,
        "contract_decision": contract_decision,
        "protected_hash_count": len(before),
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "protected_hashes_unchanged": protected_unchanged,
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
        "old_d4_retroactively_passed": False,
        "d3_g4_reinterpreted": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--control", choices=("T0_NOOP", "T1_CUDA", "T2_EXPECTED_FAILURE"))
    parser.add_argument("--primary-result-file")
    parser.add_argument("--checkpoint-file")
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--json-output")
    parser.add_argument("--synthetic-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        if not args.control or not args.primary_result_file or not args.checkpoint_file:
            raise ValueError("worker requires control, primary-result-file, and checkpoint-file")
        return worker_main(args)
    result = {"classification": "SYNTHETIC_ONLY", "synthetic_classifier_oracle": synthetic_oracle()} if args.synthetic_only else run_supervisor(args.timeout_seconds)
    if args.json_output:
        atomic_json(Path(args.json_output), result)
    print(
        PREFIX
        + json.dumps(
            {
                "classification": result["classification"],
                "stop_reason": result.get("stop_reason"),
                "summaries": result.get("summaries"),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 2 if result["classification"] in {CONTRACT_STOP, BOUNDARY_STOP} else 0


if __name__ == "__main__":
    raise SystemExit(main())
