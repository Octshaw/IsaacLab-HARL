"""B2-V2-D4 checkpointed headless-experience narrow isolation diagnostic.

Test-only.  This script never constructs an MRTA environment and never calls
HARL, I0-I6, an optimizer, backward, training, playback, evaluation, or the
original B2-V2 harness.  Every startup composition runs in a fresh child.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Callable


COMPLETE = (
    "PHASE-B2-V2-D4-HEADLESS-EXPERIENCE-REMAINING-GROUP-NARROW-"
    "ISOLATION-COMPLETE-AWAITING-GPT-REVIEW"
)
BASELINE_STOP = "PHASE-B2-V2-D4-STOP-BASELINE-NONREPRODUCIBLE"
BOUNDARY_STOP = "PHASE-B2-V2-D4-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION"
ORIGINAL_ERROR = "CUBLAS_STATUS_NOT_INITIALIZED"
DEVICE = "cuda:0"
MATRIX_DIM = 8
SEED = 260826
TIMEOUT_SECONDS = 180
PREFIX = "__B2_V2_D4_RESULT__"

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
D4_HARNESS = Path(__file__).resolve()

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
    try:
        return [normalize(item) for item in value]
    except (TypeError, AttributeError):
        return repr(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    encoded = json.dumps(payload, indent=2, sort_keys=True, default=str)
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(encoded)
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


def split_dotted(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for character in value.strip():
        if quote:
            if character == quote:
                quote = None
            else:
                current.append(character)
        elif character in {'"', "'"}:
            quote = character
        elif character == ".":
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if current or value.endswith("."):
        parts.append("".join(current).strip())
    return [part for part in parts if part]


def assignment_end(lines: list[str], start: int) -> int:
    square = 0
    curly = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(lines)):
        for character in lines[index]:
            if escaped:
                escaped = False
                continue
            if quote and character == "\\":
                escaped = True
            elif quote and character == quote:
                quote = None
            elif not quote and character in {'"', "'"}:
                quote = character
            elif not quote and character == "#":
                break
            elif not quote and character == "[":
                square += 1
            elif not quote and character == "]":
                square -= 1
            elif not quote and character == "{":
                curly += 1
            elif not quote and character == "}":
                curly -= 1
        if index == start and square == 0 and curly == 0:
            return index
        if index > start and square <= 0 and curly <= 0 and quote is None:
            return index
    return len(lines) - 1


def split_assignment(line: str) -> tuple[str, str] | None:
    quote: str | None = None
    for index, character in enumerate(line):
        if quote and character == quote:
            quote = None
        elif not quote and character in {'"', "'"}:
            quote = character
        elif not quote and character == "#":
            return None
        elif not quote and character == "=":
            return line[:index].strip(), line[index + 1 :].strip()
    return None


def parse_value(raw_value: str) -> Any:
    try:
        import tomli

        return normalize(tomli.loads("value = " + raw_value)["value"])
    except BaseException:
        return " ".join(part.strip() for part in raw_value.splitlines()).strip()


def parse_kit(path: Path, source_label: str) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    table = ""
    entries: list[dict[str, object]] = []
    dependencies: dict[str, dict[str, object]] = {}
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        header = re.match(r"^\[([^\[].*)\]\s*(?:#.*)?$", stripped)
        if header:
            table = header.group(1).strip()
            index += 1
            continue
        assignment = split_assignment(lines[index])
        if not assignment or not stripped or stripped.startswith("#"):
            index += 1
            continue
        raw_key, first_value = assignment
        end = assignment_end(lines, index)
        block = lines[index : end + 1]
        raw_value = "\n".join([first_value, *block[1:]])
        table_segments = split_dotted(table)
        key_segments = split_dotted(raw_key)
        entry = {
            "source": source_label,
            "table": table,
            "raw_key": raw_key,
            "raw_value": raw_value,
            "value": parse_value(raw_value),
            "block": "\n".join(block),
            "start": index,
            "end": end,
        }
        if table == "dependencies":
            dependency_id = key_segments[0] if key_segments else raw_key.strip('"\'')
            entry["canonical"] = dependency_id
            dependencies[dependency_id] = entry
        elif table_segments and table_segments[0] == "settings":
            setting_segments = table_segments[1:]
            if key_segments != ["++"]:
                setting_segments += key_segments
            canonical = ".".join(setting_segments)
            entry["canonical"] = canonical
            entry["setting_path"] = "/" + "/".join(setting_segments)
            entries.append(entry)
        index = end + 1
    return {
        "path": str(path),
        "sha256": sha256(path),
        "lines": lines,
        "settings": entries,
        "dependencies": dependencies,
    }


def effective_passing_settings(base: dict[str, object], base_python: dict[str, object]) -> dict[str, dict[str, object]]:
    effective: dict[str, dict[str, object]] = {}
    for parsed in (base, base_python):
        for entry in parsed["settings"]:
            key = str(entry["canonical"])
            if entry["raw_key"] in {"++", "'++'", '"++"'} and key in effective:
                combined = dict(entry)
                prior = effective[key].get("value")
                current = entry.get("value")
                if isinstance(prior, list) and isinstance(current, list):
                    combined["value"] = [*prior, *current]
                effective[key] = combined
            else:
                effective[key] = entry
    return effective


def normalized_static_diff() -> dict[str, object]:
    failing = parse_kit(HEADLESS_EXPERIENCE, "failing_headless")
    base = parse_kit(BASE_EXPERIENCE, "passing_base")
    base_python = parse_kit(BASE_PYTHON_EXPERIENCE, "passing_base_python")
    passing_settings = effective_passing_settings(base, base_python)
    failing_settings = {str(entry["canonical"]): entry for entry in failing["settings"]}
    shared_settings: list[dict[str, object]] = []
    different_settings: list[dict[str, object]] = []
    fail_only_settings: list[dict[str, object]] = []
    pass_only_settings: list[dict[str, object]] = []
    for key in sorted(set(failing_settings) | set(passing_settings)):
        left = failing_settings.get(key)
        right = passing_settings.get(key)
        if left is None:
            pass_only_settings.append({"key": key, "value": right["value"], "source": right["source"]})
        elif right is None:
            fail_only_settings.append({"key": key, "value": left["value"], "source": left["source"]})
        elif left["value"] == right["value"]:
            shared_settings.append({"key": key, "value": left["value"]})
        else:
            different_settings.append(
                {"key": key, "failing": left["value"], "passing": right["value"], "passing_source": right["source"]}
            )

    failing_dependencies = set(failing["dependencies"])
    passing_dependencies = set(base["dependencies"]) | set(base_python["dependencies"])
    return {
        "sources": {
            "failing": {"path": failing["path"], "sha256": failing["sha256"]},
            "passing_base_python": {"path": base_python["path"], "sha256": base_python["sha256"]},
            "passing_base": {"path": base["path"], "sha256": base["sha256"]},
        },
        "dependencies": {
            "shared": sorted(failing_dependencies & passing_dependencies),
            "fail_only": sorted(failing_dependencies - passing_dependencies),
            "pass_only": sorted(passing_dependencies - failing_dependencies),
            "failing_direct_count": len(failing_dependencies),
            "passing_inherited_direct_count": len(passing_dependencies),
        },
        "settings": {
            "shared": shared_settings,
            "fail_only": fail_only_settings,
            "pass_only": pass_only_settings,
            "different_value": different_settings,
            "counts": {
                "shared": len(shared_settings),
                "fail_only": len(fail_only_settings),
                "pass_only": len(pass_only_settings),
                "different_value": len(different_settings),
            },
        },
        "parsed": {"failing": failing, "base": base, "base_python": base_python},
    }


def starts_with_any(key: str, prefixes: tuple[str, ...]) -> bool:
    return any(key == prefix or key.startswith(prefix) for prefix in prefixes)


def semantic_groups(diff: dict[str, object]) -> list[dict[str, object]]:
    failing_entries = diff["parsed"]["failing"]["settings"]
    passing = effective_passing_settings(diff["parsed"]["base"], diff["parsed"]["base_python"])

    definitions: list[tuple[str, tuple[str, ...]]] = [
        (
            "R1_FAIL_MINUS_RENDERER_HEADLESS_SETTINGS",
            (
                "app.runLoops.",
                "exts.omni.kit.window.viewport.",
                "renderer.",
                "rtx-transient.",
                "app.asyncRendering",
                "app.hydraEngine.",
                "omni.replicator.asyncRendering",
                "app.audio.",
                "exts.omni.kit.window.extensions.",
                "ngx.",
            ),
        ),
        (
            "R2_FAIL_MINUS_PHYSICS_RUNTIME_SETTINGS",
            (
                "physics.",
                "persistent.simulation.",
                "persistent.omnigraph.",
                "persistent.omnihydra.",
                "app.settings.fabricDefaultStageFrameHistoryCount",
            ),
        ),
        (
            "R3_FAIL_MINUS_STARTUP_PYTHON_SETTINGS",
            (
                "app.versionFile",
                "app.folder",
                "app.name",
                "app.version",
                "app.content.",
                "app.enableStdoutOutput",
                "app.settings.persistent",
                "app.settings.dev_build",
                "app.python.",
                "exts.omni.kit.widget.toolbar.",
                "exts.omni.replicator.core.",
                "app.extensions.",
                "isaac.startup.",
                "crashreporter.",
            ),
        ),
        (
            "R4_FAIL_MINUS_PERSISTENT_STAGE_ASSET_SETTINGS",
            ("persistent.",),
        ),
    ]
    groups: list[dict[str, object]] = []
    for group_id, prefixes in definitions:
        selected = [entry for entry in failing_entries if starts_with_any(str(entry["canonical"]), prefixes)]
        if not selected:
            raise RuntimeError(f"static group {group_id} selected no real settings")
        groups.append(
            {
                "variant_id": group_id,
                "kind": "remove_settings",
                "base": "failing_headless",
                "setting_entries": selected,
                "boundary": group_id.replace("FAIL_MINUS_", "").replace("R1_", "").replace("R2_", "").replace("R3_", "").replace("R4_", "")
                + "_NECESSARY_IN_TESTED_COMPOSITION",
            }
        )

    renderer_add_keys = (
        "renderer.asyncInit",
        "renderer.gpuEnumeration.glInterop.enabled",
        "rtx-transient.dlssg.enabled",
        "rtx.hydra.mdlMaterialWarmup",
        "rtx.post.dlss.execMode",
        "exts.omni.kit.renderer.core.present.enabled",
    )
    renderer_entries = [passing[key] for key in renderer_add_keys if key in passing]
    if not renderer_entries:
        raise RuntimeError("base renderer setting group selected no real settings")
    groups += [
        {
            "variant_id": "R5_FAIL_PLUS_BASE_RENDERER_STARTUP_SETTINGS",
            "kind": "add_settings",
            "base": "failing_headless",
            "setting_entries": renderer_entries,
            "boundary": "BASE_RENDERER_STARTUP_SETTINGS_SUFFICIENT_IN_TESTED_CONTRAST",
        },
        {
            "variant_id": "R6_FAIL_PLUS_OMNI_KIT_LOOP_ISAAC",
            "kind": "add_dependencies",
            "base": "failing_headless",
            "dependencies_present": ["omni.kit.loop-isaac"],
            "boundary": "OMNI_KIT_LOOP_ISAAC_EXTENSION_GROUP_SUFFICIENT_IN_TESTED_CONTRAST",
        },
        {
            "variant_id": "R7_FAIL_PLUS_OMNI_PHYSX_BUNDLE",
            "kind": "add_dependencies",
            "base": "failing_headless",
            "dependencies_present": ["omni.physx.bundle"],
            "boundary": "OMNI_PHYSX_BUNDLE_EXTENSION_GROUP_SUFFICIENT_IN_TESTED_CONTRAST",
        },
    ]
    folder_entries = [entry for entry in failing_entries if str(entry["canonical"]) == "app.exts.folders"]
    if not folder_entries:
        raise RuntimeError("extension-folder group selected no real settings")
    groups.append(
        {
            "variant_id": "R8_FAIL_MINUS_EXTENSION_FOLDER_SETTINGS",
            "kind": "remove_settings",
            "base": "failing_headless",
            "setting_entries": folder_entries,
            "boundary": "EXTENSION_FOLDER_SETTINGS_NECESSARY_IN_TESTED_COMPOSITION",
        }
    )
    if len(groups) != 8:
        raise RuntimeError(f"D4 variant budget must be exactly 8 definitions, got {len(groups)}")
    return groups


def rewrite_app_token(source: str, source_path: Path) -> tuple[str, str]:
    original_app = str(source_path.parent.resolve()).replace("\\", "/")
    return source.replace("${app}", original_app), original_app


def materialize_variant(directory: Path, group: dict[str, object]) -> tuple[Path, dict[str, object]]:
    parsed = parse_kit(HEADLESS_EXPERIENCE, "failing_headless")
    lines = list(parsed["lines"])
    removed_settings: list[dict[str, object]] = []
    added_settings: list[dict[str, object]] = []
    added_dependencies: list[str] = []
    kind = str(group["kind"])
    if kind == "remove_settings":
        selected = group["setting_entries"]
        remove_indexes: set[int] = set()
        for entry in selected:
            remove_indexes.update(range(int(entry["start"]), int(entry["end"]) + 1))
            removed_settings.append(
                {
                    "key": entry["canonical"],
                    "path": entry["setting_path"],
                    "declared_value": entry["value"],
                }
            )
        lines = [line for index, line in enumerate(lines) if index not in remove_indexes]
    elif kind == "add_settings":
        for entry in group["setting_entries"]:
            lines += ["", f"[{entry['table']}]", str(entry["block"])]
            added_settings.append(
                {
                    "key": entry["canonical"],
                    "path": entry["setting_path"],
                    "declared_value": entry["value"],
                    "source": entry["source"],
                }
            )
    elif kind == "add_dependencies":
        added_dependencies = list(group["dependencies_present"])
        lines += ["", "[dependencies]"] + [json.dumps(dependency) + " = {}" for dependency in added_dependencies]
    else:
        raise ValueError(f"unknown variant kind: {kind}")

    source, app_root = rewrite_app_token("\n".join(lines) + "\n", HEADLESS_EXPERIENCE)
    path = directory / f"b2_v2_d4_{str(group['variant_id']).lower()}.kit"
    path.write_text(source, encoding="utf-8")
    manifest = {
        "variant_id": group["variant_id"],
        "kind": kind,
        "base": str(HEADLESS_EXPERIENCE),
        "base_sha256": sha256(HEADLESS_EXPERIENCE),
        "path": str(path),
        "sha256": sha256(path),
        "app_token_rewritten_to": app_root,
        "removed_settings": removed_settings,
        "added_settings": added_settings,
        "added_dependencies": added_dependencies,
        "boundary_if_pass": group["boundary"],
    }
    return path, manifest


class Checkpoints:
    def __init__(self, path: Path, case: str, variant_id: str | None):
        self.path = path
        self.case = case
        self.variant_id = variant_id
        self.events: list[dict[str, object]] = []

    def emit(self, stage: str, label: str, details: dict[str, object] | None = None) -> None:
        event = {
            "sequence": len(self.events),
            "stage": stage,
            "label": label,
            "monotonic_seconds": time.monotonic(),
            "pid": os.getpid(),
            "details": normalize(details or {}),
        }
        self.events.append(event)
        atomic_json(
            self.path,
            {
                "case": self.case,
                "variant_id": self.variant_id,
                "last_completed_checkpoint": stage,
                "events": self.events,
            },
        )


def module_state(label: str) -> dict[str, object]:
    loaded = "torch" in sys.modules
    result: dict[str, object] = {"label": label, "torch_in_sys_modules": loaded}
    if loaded:
        torch = sys.modules["torch"]
        result["torch_cuda_initialized"] = bool(torch.cuda.is_initialized())
    return result


def enabled_extensions() -> tuple[object, dict[str, object]]:
    import omni.kit.app

    manager = omni.kit.app.get_app().get_extension_manager()
    enabled: list[str] = []
    for extension in manager.get_extensions():
        ext_id = str(extension.get("id") or extension.get("name") or "")
        if ext_id and manager.is_extension_enabled(ext_id):
            enabled.append(ext_id)
    enabled = sorted(set(enabled))
    encoded = "\n".join(enabled).encode("utf-8")
    return manager, {"count": len(enabled), "sha256": hashlib.sha256(encoded).hexdigest(), "ids": enabled}


def read_settings(paths: dict[str, str]) -> dict[str, object]:
    import carb

    interface = carb.settings.get_settings()
    return {key: normalize(interface.get(path)) for key, path in sorted(paths.items())}


def worker_main(args: argparse.Namespace) -> int:
    result_path = Path(args.result_file)
    checkpoint_path = Path(args.checkpoint_file)
    recorder = Checkpoints(checkpoint_path, args.case, args.variant_id)
    simulation_app = None
    result: dict[str, object] = {
        "case": args.case,
        "variant_id": args.variant_id,
        "status": "failed",
        "failed_substage": "worker_started",
        "original_error_reproduced": False,
        "safe_shutdown": False,
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "timeline": [],
    }
    substage = "S0_worker_started"
    recorder.emit("S0", "worker_started", module_state("worker_started"))
    try:
        from isaacsim import SimulationApp

        substage = "S1_imports_complete"
        recorder.emit("S1", "imports_complete", module_state("imports_complete"))

        experience = args.experience or ""
        if experience:
            experience_path = Path(experience)
            if not experience_path.is_file():
                raise FileNotFoundError(experience)
            actual_hash = sha256(experience_path)
            if args.experience_sha256 and actual_hash != args.experience_sha256:
                raise RuntimeError("experience hash changed before worker startup")
        else:
            actual_hash = None
        substage = "S2_experience_variant_ready"
        recorder.emit(
            "S2",
            "experience_variant_ready",
            {"experience": experience or "<default>", "sha256": actual_hash},
        )

        result["timeline"].append(module_state("immediately_before_constructor"))
        substage = "S3_before_SimulationApp_constructor"
        recorder.emit("S3", "immediately_before_SimulationApp_constructor", result["timeline"][-1])
        simulation_app = SimulationApp({"headless": True}, experience=experience)
        result["timeline"].append(module_state("constructor_returned"))
        substage = "S4_SimulationApp_constructor_returned"
        recorder.emit("S4", "SimulationApp_constructor_returned", result["timeline"][-1])

        substage = "S5_extension_manager_accessible"
        manager, extension_summary = enabled_extensions()
        recorder.emit("S5", "extension_manager_accessible", {"manager_type": type(manager).__name__})
        result["enabled_extensions"] = extension_summary
        substage = "S6_enabled_extension_summary_captured"
        recorder.emit(
            "S6",
            "enabled_extension_summary_captured",
            {"count": extension_summary["count"], "sha256": extension_summary["sha256"]},
        )

        settings_spec = json.loads(Path(args.settings_spec_file).read_text(encoding="utf-8"))
        result["resolved_settings"] = read_settings(settings_spec)
        result["timeline"].append(module_state("immediately_before_torch_cuda_probe"))
        substage = "S7_before_torch_cuda_probe"
        recorder.emit("S7", "immediately_before_torch_cuda_probe", result["timeline"][-1])

        import torch

        result["torch_version"] = torch.__version__
        result["torch_cuda_version"] = torch.version.cuda
        result["timeline"].append(module_state("before_cuda_allocation"))
        substage = "cuda_allocation"
        x = torch.ones((MATRIX_DIM, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
        torch.cuda.synchronize()
        result["cuda_allocation"] = {"device": str(x.device), "dtype": str(x.dtype), "shape": list(x.shape)}
        recorder.emit("S8", "basic_cuda_allocation_complete", result["cuda_allocation"])

        substage = "basic_cuda_kernel_sync"
        y = x + 1.0
        torch.cuda.synchronize()
        result["basic_cuda"] = {"finite": bool(torch.isfinite(y).all().item()), "sum": float(y.sum().item())}
        recorder.emit("S9", "basic_cuda_kernel_sync_complete", result["basic_cuda"])

        other = torch.arange(MATRIX_DIM * MATRIX_DIM, dtype=torch.float32, device=DEVICE).reshape(
            MATRIX_DIM, MATRIX_DIM
        )
        torch.cuda.synchronize()
        substage = "matmul_call"
        with torch.inference_mode():
            product = torch.matmul(x, other)
        recorder.emit("S10", "matmul_complete", {"shape": list(product.shape)})
        substage = "matmul_sync"
        torch.cuda.synchronize()
        result["matmul"] = {"finite": bool(torch.isfinite(product).all().item()), "sum": float(product.sum().item())}
        recorder.emit("S11", "matmul_sync_complete", result["matmul"])

        torch.manual_seed(SEED)
        substage = "linear_forward_sync"
        linear = torch.nn.Linear(MATRIX_DIM, MATRIX_DIM).to(DEVICE)
        inputs = torch.ones((2, MATRIX_DIM), dtype=torch.float32, device=DEVICE)
        with torch.inference_mode():
            output = linear(inputs)
        torch.cuda.synchronize()
        result["linear"] = {"shape": list(output.shape), "finite": bool(torch.isfinite(output).all().item())}
        recorder.emit("S12", "linear_complete", result["linear"])
        result["status"] = "passed"
        result["failed_substage"] = None
    except BaseException as exc:
        result.update(
            {
                "status": "failed",
                "failed_substage": substage,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "original_error_reproduced": ORIGINAL_ERROR in f"{type(exc).__name__}: {exc}",
            }
        )
    finally:
        result["nvidia_smi_after_probe"] = nvidia_inventory()
        atomic_json(result_path, result)
        recorder.emit("S13", "result_persisted", {"status": result["status"], "failed_substage": result["failed_substage"]})
        if simulation_app is not None:
            recorder.emit("S14", "immediately_before_SimulationApp_close")
            try:
                simulation_app.close()
                result["safe_shutdown"] = True
                recorder.emit("S15", "SimulationApp_close_returned")
            except BaseException as close_exc:
                result["close_exception_type"] = type(close_exc).__name__
                result["close_exception_message"] = str(close_exc)
        result["checkpoint_events"] = recorder.events
        result["last_completed_checkpoint"] = recorder.events[-1]["stage"]
        atomic_json(result_path, result)
    print(
        PREFIX
        + json.dumps(
            {
                "case": args.case,
                "variant_id": args.variant_id,
                "status": result["status"],
                "failed_substage": result["failed_substage"],
                "last_completed_checkpoint": result["last_completed_checkpoint"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if result["status"] == "passed" else 1


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


def timeout_boundary(stages: list[str]) -> str | None:
    if "S4" not in stages:
        return "STARTUP_CONSTRUCTOR_TIMEOUT"
    if "S7" not in stages:
        return "POST_STARTUP_EXTENSION_OR_CHECKPOINT_TIMEOUT"
    return "CUDA_PROBE_TIMEOUT_AFTER_" + (stages[-1] if stages else "UNKNOWN")


def run_fresh(
    case: str,
    repeat: int,
    experience: Path | None,
    settings_spec_file: Path,
    timeout_seconds: int,
    variant_id: str | None = None,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"b2_v2_d4_{case.lower()}_{repeat}_") as temporary:
        temp = Path(temporary)
        result_path = temp / "result.json"
        checkpoint_path = temp / "checkpoint.json"
        command = [
            sys.executable,
            "-u",
            str(D4_HARNESS),
            "--worker",
            "--case",
            case,
            "--result-file",
            str(result_path),
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
        before_gpu = nvidia_inventory()
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
            terminate_process_tree(process)
            stdout, _ = process.communicate(timeout=15)

        checkpoint = (
            json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint_path.is_file()
            else {"events": [], "last_completed_checkpoint": None}
        )
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            result = {
                "case": case,
                "variant_id": variant_id,
                "status": "failed",
                "failed_substage": "timeout" if timed_out else "missing_result",
                "exception_type": "Timeout" if timed_out else "MissingResult",
                "exception_message": "worker exceeded timeout" if timed_out else "worker emitted no result",
                "original_error_reproduced": False,
            }
        stages = [str(event.get("stage")) for event in checkpoint.get("events", [])]
        stdout_bytes = stdout.encode("utf-8", errors="replace")
        result.update(
            {
                "repeat": repeat,
                "worker_pid": process.pid,
                "process_exit_code": process.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "timed_out": timed_out,
                "timeout_boundary": timeout_boundary(stages) if timed_out else None,
                "worker_alive_after_wait": process.poll() is None,
                "worker_terminated": process.poll() is not None,
                "safe_shutdown": "S15" in stages and not timed_out,
                "constructor_returned": "S4" in stages,
                "cuda_probe_reached": "S7" in stages,
                "last_completed_checkpoint": checkpoint.get("last_completed_checkpoint"),
                "checkpoint_events": checkpoint.get("events", []),
                "stdout_stderr_line_count": len(stdout.splitlines()),
                "stdout_stderr_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
                "stdout_stderr_tail": stdout[-12000:],
                "nvidia_smi_supervisor_before": before_gpu,
                "nvidia_smi_supervisor_after": nvidia_inventory(),
            }
        )
        return result


def outcome(result: dict[str, object]) -> str:
    if result.get("timed_out"):
        return "TIMEOUT"
    if result.get("status") == "passed":
        return "PASS"
    if result.get("original_error_reproduced") and result.get("failed_substage") == "matmul_call":
        return "CUBLAS_FAIL"
    return "OTHER_FAIL"


def stable_outcome(results: list[dict[str, object]]) -> str:
    values = {outcome(result) for result in results}
    return next(iter(values)) if len(values) == 1 else "MIXED"


def extension_present(enabled: list[str], target: str) -> bool:
    return any(item == target or item.startswith(target + "-") for item in enabled)


def validate_variant_oracle(
    manifest: dict[str, object], result: dict[str, object], failing_control: dict[str, object]
) -> dict[str, object]:
    if not result.get("constructor_returned") or result.get("timed_out"):
        return {"valid": False, "reason": "startup did not complete for runtime oracle"}
    kind = manifest["kind"]
    if kind == "remove_settings":
        baseline = failing_control.get("resolved_settings", {})
        current = result.get("resolved_settings", {})
        targets = [item["key"] for item in manifest["removed_settings"]]
        changed = [key for key in targets if normalize(current.get(key)) != normalize(baseline.get(key))]
        return {
            "valid": bool(changed),
            "reason": "at least one targeted resolved setting changed" if changed else "target settings unchanged",
            "target_count": len(targets),
            "changed_keys": changed,
        }
    if kind == "add_settings":
        current = result.get("resolved_settings", {})
        mismatched = [
            item["key"]
            for item in manifest["added_settings"]
            if normalize(current.get(item["key"])) != normalize(item["declared_value"])
        ]
        return {
            "valid": not mismatched,
            "reason": "all added settings resolved to intended values" if not mismatched else "added settings mismatch",
            "mismatched_keys": mismatched,
        }
    if kind == "add_dependencies":
        enabled = result.get("enabled_extensions", {}).get("ids", [])
        missing = [item for item in manifest["added_dependencies"] if not extension_present(enabled, item)]
        return {
            "valid": not missing,
            "reason": "all target extensions enabled" if not missing else "target extension missing",
            "missing_extensions": missing,
        }
    return {"valid": False, "reason": f"unknown variant kind {kind}"}


def summarize(case: str, results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "case": case,
        "runs": len(results),
        "stable_outcome": stable_outcome(results),
        "outcomes": [outcome(result) for result in results],
        "timeouts": sum(bool(result.get("timed_out")) for result in results),
        "safe_shutdowns": sum(bool(result.get("safe_shutdown")) for result in results),
        "last_checkpoints": [result.get("last_completed_checkpoint") for result in results],
        "failed_substages": [result.get("failed_substage") for result in results],
    }


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
    }


def settings_spec(groups: list[dict[str, object]], diff: dict[str, object]) -> dict[str, str]:
    spec: dict[str, str] = {}
    for entry in diff["parsed"]["failing"]["settings"]:
        spec[str(entry["canonical"])] = str(entry["setting_path"])
    for group in groups:
        for entry in group.get("setting_entries", []):
            spec[str(entry["canonical"])] = str(entry["setting_path"])
    return spec


def run_supervisor(core_repeats: int, variant_repeats: int, timeout_seconds: int) -> dict[str, object]:
    if core_repeats != 3 or variant_repeats != 2 or timeout_seconds != TIMEOUT_SECONDS:
        raise ValueError("D4 requires core=3, variants=2, timeout=180")
    before = file_hashes()
    diff = normalized_static_diff()
    groups = semantic_groups(diff)
    public_diff = {key: value for key, value in diff.items() if key != "parsed"}
    manifests: dict[str, dict[str, object]] = {}
    results: dict[str, list[dict[str, object]]] = {}
    oracle_results: dict[str, list[dict[str, object]]] = {}
    classification = COMPLETE
    stop_reason: str | None = None
    narrowest_boundary = "APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY"
    temporary_paths: list[str] = []

    with tempfile.TemporaryDirectory(prefix="b2_v2_d4_variants_") as temporary:
        variant_root = Path(temporary)
        spec_path = variant_root / "settings_spec.json"
        atomic_json(spec_path, settings_spec(groups, diff))

        def execute(case: str, repeats: int, experience: Path | None, variant_id: str | None = None) -> list[dict[str, object]]:
            items: list[dict[str, object]] = []
            for repeat in range(1, repeats + 1):
                print(f"[D4] {case} {variant_id or ''} repeat {repeat}/{repeats}", flush=True)
                item = run_fresh(case, repeat, experience, spec_path, timeout_seconds, variant_id)
                items.append(item)
                print(json.dumps(summarize(variant_id or case, items), sort_keys=True), flush=True)
                if item.get("timed_out") or not item.get("worker_terminated") or not item.get("safe_shutdown"):
                    break
            results[variant_id or case] = items
            return items

        b0 = execute("D4_B0_DIRECT_MINIMAL", core_repeats, None)
        if len(b0) != core_repeats or stable_outcome(b0) != "PASS" or not all(item.get("safe_shutdown") for item in b0):
            classification = BASELINE_STOP
            stop_reason = "D4-B0 was not stable PASS 3/3 with complete S0-S15 and safe close"
        else:
            b1 = execute("D4_B1_EXACT_HEADLESS_EXPERIENCE", core_repeats, HEADLESS_EXPERIENCE)
            if (
                len(b1) != core_repeats
                or stable_outcome(b1) != "CUBLAS_FAIL"
                or not all(item.get("safe_shutdown") for item in b1)
            ):
                classification = BOUNDARY_STOP
                stop_reason = "D4-B1 exact failing control was intermittent, incomplete, or did not reproduce exact cuBLAS failure"
            else:
                failing_control = b1[0]
                for group in groups:
                    path, manifest = materialize_variant(variant_root, group)
                    temporary_paths.append(str(path))
                    manifests[str(group["variant_id"])] = manifest
                    items = execute("D4_NARROW_VARIANT", variant_repeats, path, str(group["variant_id"]))
                    checks = [validate_variant_oracle(manifest, item, failing_control) for item in items]
                    oracle_results[str(group["variant_id"])] = checks
                    if any(item.get("timed_out") or not item.get("safe_shutdown") for item in items):
                        classification = BOUNDARY_STOP
                        stop_reason = (
                            f"{group['variant_id']} timed out or did not complete safe SimulationApp shutdown; "
                            f"last checkpoint {items[-1].get('last_completed_checkpoint')}"
                        )
                        break
                    if len(items) != variant_repeats or stable_outcome(items) == "MIXED":
                        classification = BOUNDARY_STOP
                        stop_reason = f"{group['variant_id']} was incomplete or mixed"
                        break
                    if not all(check.get("valid") for check in checks):
                        classification = BOUNDARY_STOP
                        stop_reason = f"{group['variant_id']} runtime settings/extension oracle did not confirm intended variant"
                        break
                    if stable_outcome(items) == "PASS":
                        narrowest_boundary = str(group["boundary"])
                        break
                    if stable_outcome(items) != "CUBLAS_FAIL":
                        classification = BOUNDARY_STOP
                        stop_reason = f"{group['variant_id']} produced a non-cuBLAS failure"
                        break

    temporary_variants_removed = all(not Path(path).exists() for path in temporary_paths)
    after = file_hashes()
    protected_unchanged = before == after
    surviving_workers = any(item.get("worker_alive_after_wait") for items in results.values() for item in items)
    environment_violation = any(
        item.get("environment_constructed")
        or item.get("environment_resets")
        or item.get("environment_steps")
        or item.get("harl_calls")
        or item.get("i0_i6_calls")
        or item.get("optimizer_calls")
        or item.get("backward_calls")
        for items in results.values()
        for item in items
    )
    if not protected_unchanged or not temporary_variants_removed or surviving_workers or environment_violation:
        classification = BOUNDARY_STOP
        reasons = []
        if not protected_unchanged:
            reasons.append("protected hashes changed")
        if not temporary_variants_removed:
            reasons.append("temporary variant cleanup failed")
        if surviving_workers:
            reasons.append("worker remained alive")
        if environment_violation:
            reasons.append("forbidden environment/HARL/I0-I6/optimizer path executed")
        stop_reason = "; ".join(reasons)

    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "narrowest_boundary": narrowest_boundary,
        "inventory": inventory(),
        "static_diff": public_diff,
        "semantic_group_definitions": [
            {
                "variant_id": group["variant_id"],
                "kind": group["kind"],
                "setting_keys": [entry["canonical"] for entry in group.get("setting_entries", [])],
                "dependency_ids": group.get("dependencies_present", []),
                "boundary_if_pass": group["boundary"],
            }
            for group in groups
        ],
        "variant_manifests": manifests,
        "results": results,
        "summaries": {case: summarize(case, items) for case, items in results.items()},
        "runtime_oracles": oracle_results,
        "fresh_process_policy": True,
        "timeout_seconds": timeout_seconds,
        "startup_checkpoint_protocol": {f"S{index}": label for index, label in enumerate((
            "worker_started",
            "imports_complete",
            "experience_variant_ready",
            "immediately_before_SimulationApp_constructor",
            "SimulationApp_constructor_returned",
            "extension_manager_accessible",
            "enabled_extension_summary_captured",
            "immediately_before_torch_cuda_probe",
            "basic_cuda_allocation_complete",
            "basic_cuda_kernel_sync_complete",
            "matmul_complete",
            "matmul_sync_complete",
            "linear_complete",
            "result_persisted",
            "immediately_before_SimulationApp_close",
            "SimulationApp_close_returned",
        ))},
        "protected_hash_count": len(before),
        "protected_hashes_before": before,
        "protected_hashes_after": after,
        "protected_hashes_unchanged": protected_unchanged,
        "temporary_variant_paths": temporary_paths,
        "temporary_variants_removed": temporary_variants_removed,
        "workers_alive_after_supervisor": sum(
            bool(item.get("worker_alive_after_wait")) for items in results.values() for item in items
        ),
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "harl_calls": 0,
        "i0_i6_calls": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
        "original_v2_rerun": False,
    }


def static_only() -> dict[str, object]:
    diff = normalized_static_diff()
    groups = semantic_groups(diff)
    return {
        "static_diff": {key: value for key, value in diff.items() if key != "parsed"},
        "semantic_groups": [
            {
                "variant_id": group["variant_id"],
                "kind": group["kind"],
                "setting_keys": [entry["canonical"] for entry in group.get("setting_entries", [])],
                "dependencies": group.get("dependencies_present", []),
            }
            for group in groups
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--case")
    parser.add_argument("--variant-id")
    parser.add_argument("--experience")
    parser.add_argument("--experience-sha256")
    parser.add_argument("--result-file")
    parser.add_argument("--checkpoint-file")
    parser.add_argument("--settings-spec-file")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--core-repeats", type=int, default=3)
    parser.add_argument("--variant-repeats", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        required = (args.case, args.result_file, args.checkpoint_file, args.settings_spec_file)
        if not all(required):
            raise ValueError("worker requires case/result/checkpoint/settings-spec")
        return worker_main(args)
    result = static_only() if args.static_only else run_supervisor(
        args.core_repeats, args.variant_repeats, args.timeout_seconds
    )
    if args.json_output:
        atomic_json(Path(args.json_output), result)
    print(
        PREFIX
        + json.dumps(
            {
                "classification": result.get("classification", "STATIC_ONLY"),
                "narrowest_boundary": result.get("narrowest_boundary"),
                "stop_reason": result.get("stop_reason"),
                "summaries": result.get("summaries"),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 2 if result.get("classification") in {BASELINE_STOP, BOUNDARY_STOP} else 0


if __name__ == "__main__":
    raise SystemExit(main())
