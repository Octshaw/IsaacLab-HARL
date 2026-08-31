"""B2-V2-D4-R restarted headless-experience narrow isolation diagnostic.

Test-only.  Uses the reviewed D4-O shutdown classifier without modifying it.
No MRTA environment, HARL, I0-I6, optimizer, backward, training, playback,
evaluation, public route, or original B2-V2 path is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from types import ModuleType
from typing import Any


COMPLETE = (
    "PHASE-B2-V2-D4R-RESTARTED-HEADLESS-EXPERIENCE-NARROW-"
    "ISOLATION-COMPLETE-AWAITING-GPT-REVIEW"
)
PARITY_STOP = "PHASE-B2-V2-D4R-STOP-SHUTDOWN-CLASSIFIER-PARITY-FAIL"
BASELINE_STOP = "PHASE-B2-V2-D4R-STOP-BASELINE-NONREPRODUCIBLE"
CONTROL_STOP = "PHASE-B2-V2-D4R-STOP-FAILING-CONTROL-NONREPRODUCIBLE"
SHUTDOWN_STOP = "PHASE-B2-V2-D4R-STOP-SHUTDOWN-LIFECYCLE-VIOLATION"
ORACLE_STOP = "PHASE-B2-V2-D4R-STOP-VARIANT-ORACLE-FAILURE"
BOUNDARY_STOP = "PHASE-B2-V2-D4R-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
INTERMITTENT_STOP = "PHASE-B2-V2-D4R-STOP-INTERMITTENT-EXPERIENCE-VARIANT-BEHAVIOR"

CUDA_PASS = "CUDA_PASS"
CUBLAS_FAIL = "CUBLAS_FAIL"
STARTUP_FAILURE = "STARTUP_FAILURE"
VARIANT_ORACLE_FAIL = "VARIANT_ORACLE_FAIL"
UNEXPECTED_DIAGNOSTIC_FAILURE = "UNEXPECTED_DIAGNOSTIC_FAILURE"
ORIGINAL_ERROR = "CUBLAS_STATUS_NOT_INITIALIZED"
DEVICE = "cuda:0"
MATRIX_DIM = 8
SEED = 260826
TIMEOUT_SECONDS = 180
PREFIX = "__B2_V2_D4R_RESULT__"

ROOT = Path(__file__).resolve().parents[2]
D4_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py"
D4O_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py"
D4R_HARNESS = Path(__file__).resolve()
EXPECTED_D4_SHA256 = "3847a28e91e0576646514f1efc08fd853360f1b4255f00f38aa27db31762a807"
EXPECTED_D4O_SHA256 = "1ccc9163725a40b10bcf10e423aa389c3bb024db23093bbb8b88104d01b03ff5"
EXPECTED_SOURCE_HASHES = {
    "failing": "475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795",
    "passing_base_python": "1806f0bff51b49af8754b5d150fe64f5942f9b49a22bcfd67ed5d40b4cfddea9",
    "passing_base": "ba9b7e23f5a3bc320ed8d7e3391d2080649b606cff15444b9e751ee16331f9b3",
}
EXPECTED_COUNTS = {
    "failing_direct_count": 17,
    "passing_inherited_direct_count": 114,
    "shared_dependencies": 8,
    "fail_only_dependencies": 9,
    "shared_settings": 17,
    "different_value_settings": 5,
    "fail_only_settings": 54,
    "pass_only_settings": 71,
}
EXPECTED_GROUP_CARDINALITIES = {
    "R1_FAIL_MINUS_RENDERER_HEADLESS_SETTINGS": (14, 0),
    "R2_FAIL_MINUS_PHYSICS_RUNTIME_SETTINGS": (19, 0),
    "R3_FAIL_MINUS_STARTUP_PYTHON_SETTINGS": (16, 0),
    "R4_FAIL_MINUS_PERSISTENT_STAGE_ASSET_SETTINGS": (30, 0),
    "R5_FAIL_PLUS_BASE_RENDERER_STARTUP_SETTINGS": (6, 0),
    "R6_FAIL_PLUS_OMNI_KIT_LOOP_ISAAC": (0, 1),
    "R7_FAIL_PLUS_OMNI_PHYSX_BUNDLE": (0, 1),
    "R8_FAIL_MINUS_EXTENSION_FOLDER_SETTINGS": (1, 0),
}
VARIANT_ORDER = (
    "R1_FAIL_MINUS_RENDERER_HEADLESS_SETTINGS",
    "R2_FAIL_MINUS_PHYSICS_RUNTIME_SETTINGS",
    "R3_FAIL_MINUS_STARTUP_PYTHON_SETTINGS",
    "R8_FAIL_MINUS_EXTENSION_FOLDER_SETTINGS",
    "R5_FAIL_PLUS_BASE_RENDERER_STARTUP_SETTINGS",
    "R6_FAIL_PLUS_OMNI_KIT_LOOP_ISAAC",
    "R7_FAIL_PLUS_OMNI_PHYSX_BUNDLE",
    "R4_FAIL_MINUS_PERSISTENT_STAGE_ASSET_SETTINGS",
)


def load_test_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load test-only module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


D4 = load_test_module(D4_HARNESS, "_b2_v2_d4_static")
D4O = load_test_module(D4O_HARNESS, "_b2_v2_d4o_frozen")
PROTECTED = tuple(D4O.PROTECTED) + (D4O_HARNESS,)
HEADLESS_EXPERIENCE = Path(D4.HEADLESS_EXPERIENCE)


def normalize(value: Any) -> Any:
    return D4O.normalize(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    D4O.atomic_json(path, payload)


def file_hashes() -> dict[str, str]:
    missing = [str(path) for path in PROTECTED if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"protected files missing: {missing}")
    return {str(path): sha256(Path(path)) for path in PROTECTED}


def current_static_manifest() -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    diff = D4.normalized_static_diff()
    groups = D4.semantic_groups(diff)
    dependency = diff["dependencies"]
    setting_counts = diff["settings"]["counts"]
    observed_counts = {
        "failing_direct_count": dependency["failing_direct_count"],
        "passing_inherited_direct_count": dependency["passing_inherited_direct_count"],
        "shared_dependencies": len(dependency["shared"]),
        "fail_only_dependencies": len(dependency["fail_only"]),
        "shared_settings": setting_counts["shared"],
        "different_value_settings": setting_counts["different_value"],
        "fail_only_settings": setting_counts["fail_only"],
        "pass_only_settings": setting_counts["pass_only"],
    }
    group_cardinalities = {
        str(group["variant_id"]): (len(group.get("setting_entries", [])), len(group.get("dependencies_present", [])))
        for group in groups
    }
    source_hashes = {key: value["sha256"] for key, value in diff["sources"].items()}
    vulkan_shared = any(
        item.get("key") == "app.vulkan" and item.get("value") is True for item in diff["settings"]["shared"]
    )
    checks = {
        "D4_harness_sha256": sha256(D4_HARNESS),
        "D4_harness_expected_sha256": EXPECTED_D4_SHA256,
        "D4O_harness_sha256": sha256(D4O_HARNESS),
        "D4O_harness_expected_sha256": EXPECTED_D4O_SHA256,
        "source_hashes": source_hashes,
        "expected_source_hashes": EXPECTED_SOURCE_HASHES,
        "counts": observed_counts,
        "expected_counts": EXPECTED_COUNTS,
        "group_cardinalities": {key: list(value) for key, value in group_cardinalities.items()},
        "expected_group_cardinalities": {key: list(value) for key, value in EXPECTED_GROUP_CARDINALITIES.items()},
        "app_vulkan_shared_true": vulkan_shared,
    }
    checks["pass"] = (
        checks["D4_harness_sha256"] == EXPECTED_D4_SHA256
        and checks["D4O_harness_sha256"] == EXPECTED_D4O_SHA256
        and source_hashes == EXPECTED_SOURCE_HASHES
        and observed_counts == EXPECTED_COUNTS
        and group_cardinalities == EXPECTED_GROUP_CARDINALITIES
        and vulkan_shared
    )
    public_diff = {key: value for key, value in diff.items() if key != "parsed"}
    return diff, groups, {"validation": checks, "normalized_diff": public_diff}


def shutdown_classifier_parity() -> dict[str, object]:
    oracle = D4O.synthetic_oracle()
    required = {
        "in_process": D4O.IN_PROCESS,
        "external_clean": D4O.EXTERNAL_CLEAN,
        "timeout": D4O.UNSAFE,
        "surviving_worker": D4O.UNSAFE,
        "surviving_child": D4O.UNSAFE,
        "missing_O4": D4O.UNSAFE,
        "missing_O5": D4O.UNSAFE,
        "corrupt_result": D4O.UNSAFE,
        "cleanup_failure": D4O.UNSAFE,
        "unexpected_nonzero": D4O.UNSAFE,
    }
    parity = {
        key: {
            "expected": expected,
            "actual": oracle["cases"][key]["actual"],
            "pass": oracle["cases"][key]["actual"] == expected,
        }
        for key, expected in required.items()
    }
    return {
        "D4O_script_sha256": sha256(D4O_HARNESS),
        "required_cases": parity,
        "full_D4O_oracle_pass": oracle["pass"],
        "pass": oracle["pass"] and all(item["pass"] for item in parity.values()),
    }


def cuda_probe() -> tuple[str, dict[str, object]]:
    import torch

    stage = "allocation_call"
    evidence: dict[str, object] = {
        "device": DEVICE,
        "dtype": "torch.float32",
        "matrix_dim": MATRIX_DIM,
        "seed": SEED,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
    }
    try:
        x = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
        stage = "basic_kernel"
        y = x + 1.0
        stage = "basic_sync"
        torch.cuda.synchronize()
        evidence["basic"] = {"finite": bool(torch.isfinite(y).all().item()), "sum": float(y.sum().item())}

        other = torch.arange(MATRIX_DIM * MATRIX_DIM, dtype=torch.float32, device=DEVICE).reshape(
            MATRIX_DIM, MATRIX_DIM
        )
        torch.cuda.synchronize()
        stage = "matmul_call"
        with torch.inference_mode():
            product = torch.matmul(x, other)
        stage = "matmul_sync"
        torch.cuda.synchronize()
        evidence["matmul"] = {
            "finite": bool(torch.isfinite(product).all().item()),
            "sum": float(product.sum().item()),
        }

        torch.manual_seed(SEED)
        stage = "linear_construct"
        linear = torch.nn.Linear(MATRIX_DIM, MATRIX_DIM).to(DEVICE)
        inputs = torch.ones((2, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
        stage = "linear_forward"
        with torch.inference_mode():
            output = linear(inputs)
        stage = "linear_sync"
        torch.cuda.synchronize()
        evidence["linear"] = {"shape": list(output.shape), "finite": bool(torch.isfinite(output).all().item())}
        return CUDA_PASS, evidence
    except BaseException as exc:
        evidence.update(
            {
                "failure_stage": stage,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "original_error_reproduced": ORIGINAL_ERROR in f"{type(exc).__name__}: {exc}",
            }
        )
        if stage == "matmul_call" and evidence["original_error_reproduced"]:
            return CUBLAS_FAIL, evidence
        return UNEXPECTED_DIAGNOSTIC_FAILURE, evidence


def worker_main(args: argparse.Namespace) -> int:
    checkpoint_path = Path(args.checkpoint_file)
    primary_path = Path(args.primary_result_file)
    checkpoints = D4O.Checkpoints(checkpoint_path, args.case)
    checkpoints.emit("O0", "worker_started")
    simulation_app = None
    primary: dict[str, object] = {
        "case": args.case,
        "variant_id": args.variant_id,
        "diagnostic_result": STARTUP_FAILURE,
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

        experience = args.experience or ""
        if experience:
            path = Path(experience)
            if not path.is_file() or sha256(path) != args.experience_sha256:
                raise RuntimeError("experience missing or hash changed before constructor")
        checkpoints.emit(
            "O1",
            "immediately_before_SimulationApp_constructor",
            {"experience": experience or "<default/base-python>"},
        )
        simulation_app = SimulationApp({"headless": True}, experience=experience)
        primary["fast_shutdown"] = bool(simulation_app.config.get("fast_shutdown"))
        checkpoints.emit("O2", "SimulationApp_constructor_returned", {"fast_shutdown": primary["fast_shutdown"]})

        _, extension_summary = D4.enabled_extensions()
        settings_spec = json.loads(Path(args.settings_spec_file).read_text(encoding="utf-8"))
        primary["enabled_extensions"] = extension_summary
        primary["resolved_settings"] = D4.read_settings(settings_spec)
        diagnostic_result, diagnostic_details = cuda_probe()
        primary["diagnostic_result"] = diagnostic_result
        primary["diagnostic_details"] = diagnostic_details
        checkpoints.emit(
            "O3",
            "diagnostic_body_complete_or_exact_failure_captured",
            {
                "diagnostic_result": diagnostic_result,
                "failure_stage": diagnostic_details.get("failure_stage"),
            },
        )
    except BaseException as exc:
        primary.update(
            {
                "diagnostic_result": STARTUP_FAILURE if simulation_app is None else UNEXPECTED_DIAGNOSTIC_FAILURE,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        checkpoints.emit(
            "O3",
            "diagnostic_body_complete_or_exact_failure_captured",
            {"diagnostic_result": primary["diagnostic_result"]},
        )

    atomic_json(primary_path, primary)
    checkpoints.emit("O4", "primary_result_persisted", {"diagnostic_result": primary["diagnostic_result"]})
    if simulation_app is None:
        return 1

    known_tree = D4O.known_descendants()
    primary["known_process_tree_before_close"] = known_tree
    primary["close_invoked"] = True
    atomic_json(primary_path, primary)
    checkpoints.emit("O5", "immediately_before_SimulationApp_close", {"known_process_tree": known_tree})
    simulation_app.close()

    primary["close_returned"] = True
    checkpoints.emit("O6", "SimulationApp_close_returned")
    atomic_json(primary_path, primary)
    return 0


def read_json(path: Path) -> tuple[bool, dict[str, object]]:
    if not path.is_file():
        return False, {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(value, dict), value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return False, {}


def run_fresh(
    case: str,
    repeat: int,
    settings_spec_file: Path,
    timeout_seconds: int,
    experience: Path | None = None,
    variant_id: str | None = None,
) -> dict[str, object]:
    temp_root = Path(tempfile.mkdtemp(prefix=f"b2_v2_d4r_{case.lower()}_{repeat}_"))
    primary_path = temp_root / "primary_result.json"
    checkpoint_path = temp_root / "checkpoints.json"
    command = [
        sys.executable,
        "-u",
        str(D4R_HARNESS),
        "--worker",
        "--case",
        case,
        "--primary-result-file",
        str(primary_path),
        "--checkpoint-file",
        str(checkpoint_path),
        "--settings-spec-file",
        str(settings_spec_file),
    ]
    if experience is not None:
        command += ["--experience", str(experience), "--experience-sha256", sha256(experience)]
    if variant_id:
        command += ["--variant-id", variant_id]
    started = time.monotonic()
    before_gpu = D4O.nvidia_inventory()
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
        D4O.terminate_process_tree(process)
        stdout, _ = process.communicate(timeout=15)

    primary_valid, primary = read_json(primary_path)
    checkpoint_valid, checkpoint = read_json(checkpoint_path)
    events = checkpoint.get("events", []) if checkpoint_valid else []
    checkpoints = [str(event.get("stage")) for event in events]
    known_tree: dict[str, object] = {"status": "NOT_CAPTURED", "children": []}
    for event in events:
        if event.get("stage") == "O5":
            known_tree = event.get("details", {}).get("known_process_tree", known_tree)
    children = known_tree.get("children", []) if isinstance(known_tree, dict) else []
    survivors = D4O.child_survivors(children) if known_tree.get("status") == "PASS" else []
    main_alive = process.poll() is None
    stdout_bytes = stdout.encode("utf-8", errors="replace")

    cleanup_error = None
    try:
        shutil.rmtree(temp_root)
    except BaseException as exc:
        cleanup_error = f"{type(exc).__name__}: {exc}"
    cleanup_pass = not temp_root.exists()

    evidence = {
        "checkpoints": checkpoints,
        "diagnostic_result": primary.get("diagnostic_result") if primary_valid else None,
        "expected_diagnostic_failure": False,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "main_worker_alive": main_alive,
        "known_child_survivors": survivors,
        "primary_result_valid": primary_valid,
        "supervisor_cleanup_pass": cleanup_pass,
        "protected_files_unchanged": True,
    }
    shutdown = D4O.classify_shutdown(evidence)
    return {
        "case": case,
        "variant_id": variant_id,
        "repeat": repeat,
        "diagnostic_result": primary.get("diagnostic_result") if primary_valid else None,
        "diagnostic_details": primary.get("diagnostic_details") if primary_valid else None,
        "fast_shutdown": primary.get("fast_shutdown") if primary_valid else None,
        "enabled_extensions": primary.get("enabled_extensions") if primary_valid else None,
        "resolved_settings": primary.get("resolved_settings") if primary_valid else None,
        "checkpoints": checkpoints,
        "checkpoint_events": events,
        "O4_observed": "O4" in checkpoints,
        "O5_observed": "O5" in checkpoints,
        "O6_observed": "O6" in checkpoints,
        "close_returned_in_process": "O6" in checkpoints,
        "constructor_returned": "O2" in checkpoints,
        "shutdown_class": shutdown["shutdown_class"],
        "safe_shutdown": shutdown["safe_shutdown"],
        "shutdown_reasons": shutdown["reasons"],
        "process_exit_code": process.returncode,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "worker_alive_after_wait": main_alive,
        "known_process_tree_observation": known_tree,
        "known_child_survivors": survivors,
        "process_tree_limitation": "pre-close recursive child snapshot; descendants created after O5 are not proven absent",
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
        "nvidia_smi_supervisor_after": D4O.nvidia_inventory(),
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }


def stable_diagnostic(results: list[dict[str, object]]) -> str:
    values = {item.get("diagnostic_result") for item in results}
    return str(next(iter(values))) if len(values) == 1 else "MIXED"


def result_summary(case: str, results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "case": case,
        "runs": len(results),
        "diagnostic_results": [item.get("diagnostic_result") for item in results],
        "stable_diagnostic": stable_diagnostic(results),
        "shutdown_classes": [item.get("shutdown_class") for item in results],
        "safe_shutdowns": sum(bool(item.get("safe_shutdown")) for item in results),
        "O4/O5/O6": [
            [bool(item.get("O4_observed")), bool(item.get("O5_observed")), bool(item.get("O6_observed"))]
            for item in results
        ],
        "timeouts": sum(bool(item.get("timed_out")) for item in results),
        "kills": sum(bool(item.get("supervisor_kill_used")) for item in results),
        "main_survivors": sum(bool(item.get("worker_alive_after_wait")) for item in results),
        "known_child_survivors": sum(bool(item.get("known_child_survivors")) for item in results),
        "cleanup_passes": sum(bool(item.get("supervisor_cleanup_pass")) for item in results),
        "elapsed_seconds": [item.get("elapsed_seconds") for item in results],
    }


def all_shutdown_safe(results: list[dict[str, object]]) -> bool:
    return all(
        item.get("safe_shutdown")
        and item.get("shutdown_class") in {D4O.IN_PROCESS, D4O.EXTERNAL_CLEAN}
        for item in results
    )


def extension_present(enabled: list[str], target: str) -> bool:
    return any(item == target or item.startswith(target + "-") for item in enabled)


def validate_variant_oracle(
    manifest: dict[str, object], results: list[dict[str, object]], failing_control: dict[str, object]
) -> dict[str, object]:
    base_checks = [D4.validate_variant_oracle(manifest, item, failing_control) for item in results]
    reasons: list[str] = []
    if not all(check.get("valid") for check in base_checks):
        reasons.append("D4 target setting/extension confirmation failed")

    extension_hashes = {
        item.get("enabled_extensions", {}).get("sha256")
        for item in results
        if isinstance(item.get("enabled_extensions"), dict)
    }
    if len(extension_hashes) != 1:
        reasons.append("runtime enabled-extension set was not stable across repeats")

    kind = manifest["kind"]
    contrast: dict[str, object] = {}
    if kind == "add_dependencies":
        baseline_enabled = failing_control.get("enabled_extensions", {}).get("ids", [])
        already_present = [
            target for target in manifest["added_dependencies"] if extension_present(baseline_enabled, target)
        ]
        if already_present:
            reasons.append("added dependency was already enabled in failing control")
        contrast["already_present_in_failing_control"] = already_present
    elif kind == "add_settings":
        baseline = failing_control.get("resolved_settings", {})
        changed = [
            item["key"]
            for item in manifest["added_settings"]
            if normalize(results[0].get("resolved_settings", {}).get(item["key"]))
            != normalize(baseline.get(item["key"]))
        ]
        if not changed:
            reasons.append("added settings produced no resolved contrast from failing control")
        contrast["changed_from_failing_control"] = changed

    return {
        "valid": not reasons,
        "reasons": reasons or ["target runtime oracle and repeat stability passed"],
        "per_repeat_base_checks": base_checks,
        "enabled_extension_hashes": sorted(str(value) for value in extension_hashes),
        "contrast": contrast,
    }


def variant_interpretation(manifest: dict[str, object], diagnostic: str) -> tuple[str, str | None]:
    kind = manifest["kind"]
    variant_id = str(manifest["variant_id"])
    if diagnostic == CUDA_PASS and kind == "remove_settings":
        return (
            f"{variant_id}_NECESSARY_IN_TESTED_HEADLESS_EXPERIENCE_COMPOSITION",
            "FAIL_TO_PASS_SUBTRACTION_BOUNDARY",
        )
    if diagnostic == CUDA_PASS and kind in {"add_settings", "add_dependencies"}:
        return (
            f"{variant_id}_SUFFICIENT_TO_RESTORE_PASS_IN_TESTED_FAILING_COMPOSITION",
            "PASS_RESTORATION_INTERACTION_BOUNDARY",
        )
    if diagnostic == CUBLAS_FAIL and kind == "remove_settings":
        return (f"{variant_id}_NOT_NECESSARY_IN_TESTED_COMPOSITION", None)
    if diagnostic == CUBLAS_FAIL and kind in {"add_settings", "add_dependencies"}:
        return (f"{variant_id}_ALONE_INSUFFICIENT_TO_RESTORE_PASS", None)
    return (f"{variant_id}_{diagnostic}", None)


def run_supervisor(timeout_seconds: int) -> dict[str, object]:
    if timeout_seconds != TIMEOUT_SECONDS:
        raise ValueError("D4-R requires the authorized 180-second timeout")
    before = file_hashes()
    diff, groups, static_evidence = current_static_manifest()
    parity = shutdown_classifier_parity()
    classification = COMPLETE
    stop_reason: str | None = None
    narrowest_boundary = "APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY"
    boundary_kind = "NO_SMALLER_GROUP_ISOLATED_WITHIN_AUTHORIZED_BUDGET"
    results: dict[str, list[dict[str, object]]] = {}
    manifests: dict[str, dict[str, object]] = {}
    variant_oracles: dict[str, dict[str, object]] = {}
    interpretations: dict[str, str] = {}
    temporary_variant_paths: list[str] = []

    if not static_evidence["validation"]["pass"]:
        classification = BOUNDARY_STOP
        stop_reason = "normalized static manifest or frozen source/hash validation failed"
    elif not parity["pass"]:
        classification = PARITY_STOP
        stop_reason = "D4-O shutdown classifier parity failed"

    with tempfile.TemporaryDirectory(prefix="b2_v2_d4r_variants_") as temporary:
        variant_root = Path(temporary)
        spec_path = variant_root / "settings_spec.json"
        atomic_json(spec_path, D4.settings_spec(groups, diff))

        def execute(
            case: str,
            repeats: int,
            experience: Path | None = None,
            variant_id: str | None = None,
        ) -> list[dict[str, object]]:
            items: list[dict[str, object]] = []
            for repeat in range(1, repeats + 1):
                print(f"[D4-R] {variant_id or case} repeat {repeat}/{repeats}", flush=True)
                item = run_fresh(case, repeat, spec_path, timeout_seconds, experience, variant_id)
                items.append(item)
                print(json.dumps(result_summary(variant_id or case, items), sort_keys=True), flush=True)
                if not item.get("safe_shutdown"):
                    break
            results[variant_id or case] = items
            return items

        if classification == COMPLETE:
            b0 = execute("B0_DIRECT_MINIMAL", 3)
            if not all_shutdown_safe(b0):
                classification = SHUTDOWN_STOP
                stop_reason = "B0 produced unsafe/inconclusive shutdown"
            elif len(b0) != 3 or stable_diagnostic(b0) != CUDA_PASS:
                classification = BASELINE_STOP
                stop_reason = "fresh B0 baseline was not stable CUDA_PASS 3/3"

        if classification == COMPLETE:
            b1 = execute("B1_EXACT_HEADLESS", 3, HEADLESS_EXPERIENCE)
            if not all_shutdown_safe(b1):
                classification = SHUTDOWN_STOP
                stop_reason = "B1 produced unsafe/inconclusive shutdown"
            elif len(b1) != 3 or stable_diagnostic(b1) != CUBLAS_FAIL:
                classification = CONTROL_STOP
                stop_reason = "fresh B1 control was not exact CUBLAS_FAIL 3/3"

        if classification == COMPLETE:
            failing_control = results["B1_EXACT_HEADLESS"][0]
            group_by_id = {str(group["variant_id"]): group for group in groups}
            for variant_id in VARIANT_ORDER:
                group = group_by_id[variant_id]
                path, manifest = D4.materialize_variant(variant_root, group)
                temporary_variant_paths.append(str(path))
                manifests[variant_id] = manifest
                items = execute("R_VARIANT", 2, path, variant_id)
                if not all_shutdown_safe(items):
                    classification = SHUTDOWN_STOP
                    stop_reason = f"{variant_id} produced unsafe/inconclusive shutdown"
                    break
                if len(items) != 2:
                    classification = BOUNDARY_STOP
                    stop_reason = f"{variant_id} did not complete two fresh repeats"
                    break
                diagnostic = stable_diagnostic(items)
                if diagnostic == "MIXED":
                    classification = INTERMITTENT_STOP
                    stop_reason = f"{variant_id} produced mixed diagnostic results"
                    break
                if diagnostic not in {CUDA_PASS, CUBLAS_FAIL}:
                    classification = BOUNDARY_STOP
                    stop_reason = f"{variant_id} produced {diagnostic}, not CUDA boundary evidence"
                    break
                oracle = validate_variant_oracle(manifest, items, failing_control)
                variant_oracles[variant_id] = oracle
                if not oracle["valid"]:
                    classification = ORACLE_STOP
                    stop_reason = f"{variant_id} runtime variant oracle failed: {oracle['reasons']}"
                    break
                interpretation, success_kind = variant_interpretation(manifest, diagnostic)
                interpretations[variant_id] = interpretation
                if success_kind is not None:
                    narrowest_boundary = interpretation
                    boundary_kind = success_kind
                    break

    temporary_variants_removed = all(not Path(path).exists() for path in temporary_variant_paths)
    after = file_hashes()
    protected_unchanged = before == after
    if not protected_unchanged or not temporary_variants_removed:
        classification = BOUNDARY_STOP
        stop_reason = (
            "protected hashes changed" if not protected_unchanged else "temporary variant cleanup failed"
        )

    for items in results.values():
        for item in items:
            evidence = {
                "checkpoints": item["checkpoints"],
                "diagnostic_result": item["diagnostic_result"],
                "expected_diagnostic_failure": False,
                "exit_code": item["process_exit_code"],
                "timed_out": item["timed_out"],
                "supervisor_kill_used": item["supervisor_kill_used"],
                "main_worker_alive": item["worker_alive_after_wait"],
                "known_child_survivors": item["known_child_survivors"],
                "primary_result_valid": item["primary_result_valid"],
                "supervisor_cleanup_pass": item["supervisor_cleanup_pass"],
                "protected_files_unchanged": protected_unchanged,
            }
            final_shutdown = D4O.classify_shutdown(evidence)
            item["shutdown_class"] = final_shutdown["shutdown_class"]
            item["safe_shutdown"] = final_shutdown["safe_shutdown"]
            item["shutdown_reasons"] = final_shutdown["reasons"]

    summaries = {case: result_summary(case, items) for case, items in results.items()}
    if classification == COMPLETE and any(
        not item.get("safe_shutdown") for items in results.values() for item in items
    ):
        classification = SHUTDOWN_STOP
        stop_reason = "final protected-aware shutdown classification was unsafe"

    public_group_manifest = [
        {
            "variant_id": group["variant_id"],
            "kind": group["kind"],
            "setting_keys": [entry["canonical"] for entry in group.get("setting_entries", [])],
            "dependency_ids": group.get("dependencies_present", []),
        }
        for group in sorted(groups, key=lambda item: VARIANT_ORDER.index(str(item["variant_id"])))
    ]
    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "narrowest_boundary": narrowest_boundary,
        "boundary_kind": boundary_kind,
        "static_revalidation": static_evidence,
        "shutdown_classifier_parity": parity,
        "variant_execution_order": list(VARIANT_ORDER),
        "variant_order_rationale": (
            "subtraction first; renderer, physics, and startup before extension folders; "
            "small restoration additions before the broad persistent removal"
        ),
        "exact_semantic_group_manifest": public_group_manifest,
        "results": results,
        "summaries": summaries,
        "variant_manifests": manifests,
        "variant_oracles": variant_oracles,
        "variant_interpretations": interpretations,
        "executed_variant_count": len(manifests),
        "protected_hash_count": len(before),
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "protected_hashes_unchanged": protected_unchanged,
        "temporary_variant_paths": temporary_variant_paths,
        "temporary_variants_removed": temporary_variants_removed,
        "fresh_process_policy": True,
        "timeout_seconds": timeout_seconds,
        "old_D4_B0_reused": False,
        "D3_G1_G3_repeated": False,
        "D3_G4_repeated_or_reinterpreted": False,
        "pre_App_CUDA_warmup": False,
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "original_v2_rerun": False,
    }


def static_and_parity_only() -> dict[str, object]:
    _, groups, static_evidence = current_static_manifest()
    return {
        "classification": "STATIC_AND_PARITY_ONLY",
        "static_revalidation": static_evidence,
        "shutdown_classifier_parity": shutdown_classifier_parity(),
        "variant_order": list(VARIANT_ORDER),
        "group_cardinalities": {
            str(group["variant_id"]): [len(group.get("setting_entries", [])), len(group.get("dependencies_present", []))]
            for group in groups
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--case")
    parser.add_argument("--variant-id")
    parser.add_argument("--experience")
    parser.add_argument("--experience-sha256")
    parser.add_argument("--primary-result-file")
    parser.add_argument("--checkpoint-file")
    parser.add_argument("--settings-spec-file")
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--json-output")
    parser.add_argument("--static-and-parity-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        required = (args.case, args.primary_result_file, args.checkpoint_file, args.settings_spec_file)
        if not all(required):
            raise ValueError("worker requires case, primary result, checkpoint, and settings spec")
        return worker_main(args)
    result = static_and_parity_only() if args.static_and_parity_only else run_supervisor(args.timeout_seconds)
    if args.json_output:
        atomic_json(Path(args.json_output), result)
    print(
        PREFIX
        + json.dumps(
            {
                "classification": result["classification"],
                "stop_reason": result.get("stop_reason"),
                "narrowest_boundary": result.get("narrowest_boundary"),
                "boundary_kind": result.get("boundary_kind"),
                "summaries": result.get("summaries"),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    stop_classes = {
        PARITY_STOP,
        BASELINE_STOP,
        CONTROL_STOP,
        SHUTDOWN_STOP,
        ORACLE_STOP,
        BOUNDARY_STOP,
        INTERMITTENT_STOP,
    }
    return 2 if result["classification"] in stop_classes else 0


if __name__ == "__main__":
    raise SystemExit(main())
