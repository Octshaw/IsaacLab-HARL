"""Bounded B2-T4-EP environment entry-point and registration qualification.

Pure modes model the real package export/registration source with lightweight
sentinel classes.  The formal mode is deliberately separate and is the only
mode allowed to launch Isaac Sim or construct the real environment.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASKS_SOURCE = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN = DIRECT_SOURCE / "scan_mobile_manipulator"
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260915"
ARTIFACTS = DATE_ROOT / "b2_t4_ep_artifacts"

ENV_ID = "Isaac-Scan-Mobile-Manipulator-Direct-v0"
PACKAGE_NAME = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEFINING_MODULE = PACKAGE_NAME + ".scan_mobile_manipulator_env"
ENTRY_POINT = PACKAGE_NAME + ":ScanMobileManipulatorEnv"
PASS = (
    "PHASE-B2-T4-EP-ENVIRONMENT-ENTRY-POINT-REGISTRATION-BOUNDARY-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)

PACKAGE_INIT = SCAN / "__init__.py"
ENV_SOURCE = SCAN / "scan_mobile_manipulator_env.py"
ROOT_INIT = TASKS_SOURCE / "__init__.py"
DIRECT_INIT = DIRECT_SOURCE / "__init__.py"
RE2_RUNNER = HERE / "test_assignment_phase_b2_t4_re2_normal_horizon_learned_training_integration.py"
RE3_RUNNER = HERE / "test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py"
ZD_SUITE = HERE / "test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract.py"
R1_HELPER = HERE / "_assignment_phase_b2_r1_contract_helpers.py"
FULL_TRANSACTION = SCAN / "assignment_event_training_full_transaction.py"
REAL_ADAPTER = SCAN / "assignment_event_training_real_isaac_adapter.py"

HISTORICAL_RE3_SHA256 = "b6325c78189ab5b62c7daaf7452745c036eb7acd629f3c705cbded24eda86f6c"
EXPECTED_FULL_SHA256 = "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7"
EXPECTED_ADAPTER_SHA256 = "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _require(condition: bool, code: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-EP {code}: {detail!r}")


def _module_state(name: str) -> dict[str, object]:
    module = sys.modules.get(name)
    if module is None:
        return {"present": False, "name": name}
    keys = tuple(
        key
        for key in (
            "ScanMobileManipulatorEnv",
            "ScanMobileManipulatorEnvCfg",
            "__all__",
        )
        if key in module.__dict__
    )
    return {
        "present": True,
        "name": name,
        "file": getattr(module, "__file__", None),
        "spec": repr(getattr(module, "__spec__", None)),
        "path": tuple(str(value) for value in getattr(module, "__path__", ())),
        "object_id": id(module),
        "has_env_class": hasattr(module, "ScanMobileManipulatorEnv"),
        "relevant_dict_keys": keys,
        "all": getattr(module, "__all__", None),
    }


def _relevant_module_state() -> dict[str, object]:
    return {
        name: _module_state(name)
        for name in (
            "isaaclab_tasks",
            "isaaclab_tasks.direct",
            PACKAGE_NAME,
            DEFINING_MODULE,
        )
    }


def _install_pure_package_model() -> tuple[type, type]:
    """Execute the real registration __init__ against one stub defining module."""

    tasks = types.ModuleType("isaaclab_tasks")
    tasks.__path__ = [str(TASKS_SOURCE)]
    direct = types.ModuleType("isaaclab_tasks.direct")
    direct.__path__ = [str(DIRECT_SOURCE)]
    tasks.direct = direct
    sys.modules["isaaclab_tasks"] = tasks
    sys.modules["isaaclab_tasks.direct"] = direct

    canonical_env = type("ScanMobileManipulatorEnv", (), {"__module__": DEFINING_MODULE})
    canonical_cfg = type("ScanMobileManipulatorEnvCfg", (), {"__module__": DEFINING_MODULE})
    defining = types.ModuleType(DEFINING_MODULE)
    defining.__file__ = str(ENV_SOURCE)
    defining.__spec__ = importlib.util.spec_from_loader(DEFINING_MODULE, loader=None)
    defining.ScanMobileManipulatorEnv = canonical_env
    defining.ScanMobileManipulatorEnvCfg = canonical_cfg
    sys.modules[DEFINING_MODULE] = defining

    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        PACKAGE_INIT,
        submodule_search_locations=[str(SCAN)],
    )
    _require(spec is not None and spec.loader is not None, "PURE-PACKAGE-SPEC")
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    direct.scan_mobile_manipulator = package
    spec.loader.exec_module(package)
    return canonical_env, canonical_cfg


def _pure_probe(sequence: str) -> dict[str, object]:
    import gymnasium as gym
    from gymnasium.envs.registration import load_env_creator

    _require(ENV_ID not in gym.registry, "PURE-PROCESS-NOT-FRESH", ENV_ID)
    imported_runner = None
    if sequence == "re2":
        imported_runner = "test_assignment_phase_b2_t4_re2_normal_horizon_learned_training_integration"
        importlib.import_module(imported_runner)
    elif sequence in ("re3", "re3_repeat"):
        imported_runner = "test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration"
        importlib.import_module(imported_runner)
    elif sequence != "canonical":
        raise ValueError(sequence)

    before = _relevant_module_state()
    if imported_runner is not None:
        _require(
            not any(value["present"] for value in before.values()),
            "RUNNER-PRE-APPLAUNCHER-PACKAGE-POLLUTION",
            before,
        )

    canonical_env, canonical_cfg = _install_pure_package_model()
    package = sys.modules[PACKAGE_NAME]
    defining = sys.modules[DEFINING_MODULE]
    spec = gym.spec(ENV_ID)
    resolved = load_env_creator(spec.entry_point)
    passed = bool(
        spec.id == ENV_ID
        and spec.entry_point == ENTRY_POINT
        and resolved is canonical_env
        and resolved is defining.ScanMobileManipulatorEnv
        and package.ScanMobileManipulatorEnv is canonical_env
        and spec.kwargs["env_cfg_entry_point"] is canonical_cfg
    )
    _require(passed, "PURE-ENTRY-POINT-IDENTITY")
    return {
        "schema_version": "b2_t4_ep_pure_resolution_probe_v1",
        "sequence": sequence,
        "fresh_process": True,
        "process_id": os.getpid(),
        "runner_imported_before_registration": imported_runner,
        "module_state_before_canonical_registration": before,
        "module_state_after_canonical_registration": _relevant_module_state(),
        "spec": {
            "id": spec.id,
            "entry_point": spec.entry_point,
            "disable_env_checker": spec.disable_env_checker,
            "kwargs_keys": tuple(sorted(spec.kwargs)),
        },
        "package_file": package.__file__,
        "package_all_defined": hasattr(package, "__all__"),
        "resolved_class": {
            "module": resolved.__module__,
            "name": resolved.__name__,
            "identity_matches_defining_module": resolved is defining.ScanMobileManipulatorEnv,
            "identity_matches_package_export": resolved is package.ScanMobileManipulatorEnv,
        },
        "model_boundary": (
            "The real registration/package __init__.py executed unchanged; only the heavy "
            "defining module classes were replaced by identity-preserving sentinels."
        ),
        "pass": passed,
    }


def _negative_probe() -> dict[str, object]:
    import gymnasium as gym
    from gymnasium.envs.registration import load_env_creator

    _require(ENV_ID not in gym.registry, "NEGATIVE-PROCESS-NOT-FRESH")
    _install_pure_package_model()
    cases: dict[str, object] = {}
    for name, target, expected in (
        ("wrong_attribute", PACKAGE_NAME + ":NotTheEnvironment", "AttributeError"),
        ("wrong_module", PACKAGE_NAME + ".missing_module:ScanMobileManipulatorEnv", "ModuleNotFoundError"),
    ):
        try:
            load_env_creator(target)
        except BaseException as exc:
            cases[name] = {
                "target": target,
                "expected_exception": expected,
                "actual_exception": type(exc).__name__,
                "diagnostic": str(exc),
                "pass": type(exc).__name__ == expected,
            }
        else:
            cases[name] = {"target": target, "pass": False, "actual_exception": None}
    missing_id = "Isaac-Scan-Mobile-Manipulator-EP-Missing-v0"
    try:
        gym.spec(missing_id)
    except BaseException as exc:
        cases["missing_registration"] = {
            "target": missing_id,
            "actual_exception": type(exc).__name__,
            "diagnostic": str(exc),
            "pass": type(exc).__name__ in {"NameNotFound", "NamespaceNotFound"},
        }
    else:
        cases["missing_registration"] = {"target": missing_id, "pass": False}
    passed = all(bool(value["pass"]) for value in cases.values())
    _require(passed, "NEGATIVE-RESOLUTION-DIAGNOSTICS", cases)
    return {
        "schema_version": "b2_t4_ep_negative_resolution_v1",
        "fresh_process": True,
        "process_id": os.getpid(),
        "cases": cases,
        "duplicate_registration": {
            "executed": False,
            "reason": (
                "Gymnasium overwrites duplicate IDs with a warning rather than providing a "
                "project fail-closed detector; mutating the qualified registry was unnecessary."
            ),
        },
        "pass": passed,
    }


def _source_trace() -> dict[str, object]:
    init_tree = ast.parse(PACKAGE_INIT.read_text(encoding="utf-8"))
    env_tree = ast.parse(ENV_SOURCE.read_text(encoding="utf-8"))
    re3_tree = ast.parse(RE3_RUNNER.read_text(encoding="utf-8"))
    registration = None
    export_import = None
    for node in ast.walk(init_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "register":
            values = {keyword.arg: ast.literal_eval(keyword.value) for keyword in node.keywords if keyword.arg in {"id", "entry_point"}}
            registration = {"line": node.lineno, **values}
        if isinstance(node, ast.ImportFrom) and node.module == "scan_mobile_manipulator_env":
            export_import = {
                "line": node.lineno,
                "level": node.level,
                "names": tuple(alias.name for alias in node.names),
            }
    env_class_line = next(
        node.lineno
        for node in ast.walk(env_tree)
        if isinstance(node, ast.ClassDef) and node.name == "ScanMobileManipulatorEnv"
    )
    zd_imports = [
        {
            "line": node.lineno,
            "scope": "run_runner_readiness_replay" if node.col_offset else "module",
            "module": alias.name,
        }
        for node in ast.walk(re3_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract"
    ]
    _require(
        registration == {"line": 19, "id": ENV_ID, "entry_point": ENTRY_POINT}
        and export_import is not None
        and "ScanMobileManipulatorEnv" in export_import["names"]
        and env_class_line == 1468
        and zd_imports == [
            {
                "line": 331,
                "scope": "run_runner_readiness_replay",
                "module": "test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract",
            }
        ],
        "SOURCE-TRACE-DRIFT",
        {"registration": registration, "export": export_import, "env_line": env_class_line, "zd": zd_imports},
    )
    return {
        "schema_version": "b2_t4_ep_registration_source_trace_v1",
        "registration_file": str(PACKAGE_INIT.relative_to(ROOT)),
        "registration": registration,
        "python_import_module": PACKAGE_NAME,
        "python_attribute": "ScanMobileManipulatorEnv",
        "package_export_import": export_import,
        "defining_file": str(ENV_SOURCE.relative_to(ROOT)),
        "defining_class_line": env_class_line,
        "defining_class_module": DEFINING_MODULE,
        "package_all_defined": False,
        "re3_zd_import_after_repair": zd_imports,
        "pass": True,
    }


def _git(*args: str) -> str:
    completed = subprocess.run(
        ("git", *args), cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return completed.stdout.strip()


def _source_manifest() -> dict[str, object]:
    paths = {
        "isaaclab_tasks/__init__.py": ROOT_INIT,
        "isaaclab_tasks/direct/__init__.py": DIRECT_INIT,
        "scan_mobile_manipulator/__init__.py": PACKAGE_INIT,
        "scan_mobile_manipulator_env.py": ENV_SOURCE,
        "RE2 runner": RE2_RUNNER,
        "RE3 runner EP-qualified": RE3_RUNNER,
        "ZD suite": ZD_SUITE,
        "R1 pure helper": R1_HELPER,
        "assignment_event_training_full_transaction.py": FULL_TRANSACTION,
        "assignment_event_training_real_isaac_adapter.py": REAL_ADAPTER,
    }
    hashes = {name: _sha(path) for name, path in paths.items()}
    protected_pass = bool(
        hashes["assignment_event_training_full_transaction.py"] == EXPECTED_FULL_SHA256
        and hashes["assignment_event_training_real_isaac_adapter.py"] == EXPECTED_ADAPTER_SHA256
    )
    registration_status = {
        name: _git("status", "--short", "--", str(path.relative_to(ROOT)))
        for name, path in paths.items()
        if name in {
            "isaaclab_tasks/__init__.py",
            "isaaclab_tasks/direct/__init__.py",
            "scan_mobile_manipulator/__init__.py",
            "scan_mobile_manipulator_env.py",
        }
    }
    _require(protected_pass, "TRAINING-PRODUCTION-SOURCE-DRIFT", hashes)
    _require(not any(registration_status.values()), "PRODUCTION-REGISTRATION-SOURCE-MODIFIED", registration_status)
    return {
        "schema_version": "b2_t4_ep_source_identity_manifest_v1",
        "hashes": hashes,
        "historical_re3_wrapper_sha256": HISTORICAL_RE3_SHA256,
        "historical_re3_wrapper_preserved_in_report_and_artifacts": True,
        "protected_training_hashes_pass": protected_pass,
        "registration_export_production_git_status": registration_status,
        "previous_re2_re3_manifest_coverage": {
            "isaaclab_tasks/__init__.py": False,
            "isaaclab_tasks/direct/__init__.py": False,
            "scan_mobile_manipulator/__init__.py": False,
            "scan_mobile_manipulator_env.py": False,
        },
        "future_frozen_authority_additions": tuple(
            name
            for name in (
                "isaaclab_tasks/__init__.py",
                "isaaclab_tasks/direct/__init__.py",
                "scan_mobile_manipulator/__init__.py",
                "scan_mobile_manipulator_env.py",
            )
        ),
        "pass": True,
    }


def _run_child(mode: str, sequence: str | None = None) -> dict[str, object]:
    command = [sys.executable, str(Path(__file__).resolve()), "--mode", mode]
    if sequence is not None:
        command.extend(("--sequence", sequence))
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(completed.returncode == 0, "FRESH-PROCESS-PROBE-FAILED", {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    })
    lines = [line for line in completed.stdout.splitlines() if line.startswith("B2_T4_EP_JSON=")]
    _require(len(lines) == 1, "FRESH-PROCESS-PROBE-OUTPUT", completed.stdout)
    return json.loads(lines[0].split("=", 1)[1])


def _run_matrix() -> dict[str, object]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    trace = _source_trace()
    manifest = _source_manifest()
    probes = {
        "A_canonical_import_sequence": _run_child("probe", "canonical"),
        "B_exact_re3_formal_import_sequence": _run_child("probe", "re3"),
        "C_fresh_repeat_of_B": _run_child("probe", "re3_repeat"),
        "historical_re2_pre_AppLauncher_sequence": _run_child("probe", "re2"),
    }
    negatives = _run_child("negative")
    passed = bool(all(value["pass"] for value in probes.values()) and negatives["pass"])
    _require(passed, "FRESH-PROCESS-ENTRY-POINT-UNSTABLE")

    canonical = probes["A_canonical_import_sequence"]
    re2 = probes["historical_re2_pre_AppLauncher_sequence"]
    re3 = probes["B_exact_re3_formal_import_sequence"]
    comparison = {
        "schema_version": "b2_t4_ep_re2_re3_import_comparison_v1",
        "rows": {
            "env_id": {"re2": ENV_ID, "re3_before_ep": ENV_ID, "ep_qualified": ENV_ID},
            "entry_point": {"re2": ENTRY_POINT, "re3_before_ep": ENTRY_POINT, "ep_qualified": ENTRY_POINT},
            "pre_AppLauncher_package_present": {"re2": False, "re3_before_ep": True, "ep_qualified": False},
            "pre_AppLauncher_package_file": {"re2": None, "re3_before_ep": None, "ep_qualified": None},
            "pre_AppLauncher_env_export": {"re2": False, "re3_before_ep": False, "ep_qualified": False},
            "after_canonical_registration_env_export": {"re2": True, "re3_before_ep": "not reached", "ep_qualified": True},
            "gym_spec_resolves": {"re2": True, "re3_before_ep": False, "ep_qualified": True},
            "runner_difference": {
                "re2": "No top-level ZD import; task package absent before AppLauncher.",
                "re3_before_ep": "Top-level ZD -> NR -> R5 helper -> R1 helper installed synthetic package shells.",
                "ep_qualified": "ZD import is local to pure readiness; formal import leaves task package absent.",
            },
        },
        "historical_re3_state_source": "B2-T4-EP diagnostic fresh-process probe before repair",
        "ep_probe_process_ids": {"re2": re2["process_id"], "re3": re3["process_id"]},
        "pass": True,
    }
    module_audit = {
        "schema_version": "b2_t4_ep_module_export_audit_v1",
        "package_file": str(PACKAGE_INIT),
        "export_statement_line": trace["package_export_import"]["line"],
        "exports_env_class": True,
        "all_defined": False,
        "wildcard_or_all_required": False,
        "entry_point_consistent_with_export": True,
        "production_repair_required": False,
        "pass": True,
    }
    repair = {
        "schema_version": "b2_t4_ep_repair_decision_v1",
        "root_cause_classification": "TEST-SIDE IMPORT ORDER / SYS.MODULES CACHE POISONING",
        "before": (
            "RE3 imported ZD at module scope; ZD's helper chain installed file-less synthetic "
            "isaaclab_tasks package shells before AppLauncher. The later canonical import hit "
            "those cached shells, so scan_mobile_manipulator/__init__.py never exported the env class."
        ),
        "after": (
            "RE3 imports ZD only inside its pure readiness function. A formal worker reaches "
            "AppLauncher with isaaclab_tasks absent, then the canonical task import executes the "
            "real package initializer, registers the ID, and exports the exact defining class."
        ),
        "repair_type": "TEST-SIDE",
        "production_registration_export_files_changed": 0,
        "production_training_semantic_files_changed": 0,
        "test_side_runner_files_changed": 1,
        "dedicated_test_files_created": 1,
        "pass": True,
    }
    matrix = {
        "schema_version": "b2_t4_ep_fresh_process_resolution_matrix_v1",
        "probes": probes,
        "negative_resolution": negatives,
        "fresh_child_processes": 5,
        "successful_positive_fresh_process_probes": 4,
        "successful_negative_fresh_process_probe_processes": 1,
        "D_AppLauncher_compatible_sequence": (
            "Deferred to the one formal process, where real resolution must pass after AppLauncher and before gym.make."
        ),
        "pass": passed,
    }
    spec_artifact = {
        "schema_version": "b2_t4_ep_env_entry_point_spec_v1",
        **canonical["spec"],
        "pure_source_model_resolution_pass": True,
        "real_AppLauncher_resolution": "pending formal smoke",
    }
    class_identity = {
        "schema_version": "b2_t4_ep_env_class_definition_identity_v1",
        "defining_file": str(ENV_SOURCE),
        "defining_source_sha256": _sha(ENV_SOURCE),
        "class_line": trace["defining_class_line"],
        "class_module": DEFINING_MODULE,
        "pure_identity_matches_package_and_defining_module": True,
        "real_identity": "pending formal smoke",
    }
    sys_modules = {
        "schema_version": "b2_t4_ep_sys_modules_probe_v1",
        "re2_pre_AppLauncher": re2["module_state_before_canonical_registration"],
        "re3_after_EP_pre_AppLauncher": re3["module_state_before_canonical_registration"],
        "re3_before_EP": {
            "package_present": True,
            "package_file": None,
            "package_spec": None,
            "env_export_present": False,
            "defining_module_present": False,
            "provenance": "fresh diagnostic process before the EP runner repair",
        },
        "pass": True,
    }
    for filename, payload in (
        ("registration_source_trace.json", trace),
        ("env_entry_point_spec.json", spec_artifact),
        ("env_class_definition_identity.json", class_identity),
        ("re2_re3_import_comparison.json", comparison),
        ("module_export_audit.json", module_audit),
        ("sys_modules_probe.json", sys_modules),
        ("fresh_process_resolution_matrix.json", matrix),
        ("negative_resolution_tests.json", negatives),
        ("repair_decision.json", repair),
        ("source_identity_manifest.json", manifest),
    ):
        _atomic_json(ARTIFACTS / filename, payload)
    return matrix


def _shape(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _shape(item) for key, item in value.items()}
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dimension) for dimension in shape)
    if value is None:
        return None
    return type(value).__name__


def _run_formal() -> dict[str, object]:
    """Run the one authorized real AppLauncher/make/reset/close smoke."""

    result: dict[str, Any] = {
        "schema_version": "b2_t4_ep_formal_environment_smoke_v1",
        "status": "failed",
        "classification": "PHASE-B2-T4-EP-STOP-ENVIRONMENT-CONSTRUCTION-FAILED",
        "process_id": os.getpid(),
        "fresh_process": True,
        "formal_attempts": 1,
        "AppLauncher_lifetimes": 0,
        "environment_constructions": 0,
        "initial_resets": 0,
        "physical_environment_steps": 0,
        "persistent_learner_constructions": 0,
        "learner_updates": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
    }
    env = None
    simulation_app = None
    close_errors: list[str] = []
    reset_evidence: dict[str, object] | None = None
    try:
        # This is the exact repaired RE3 module-import position: before AppLauncher.
        importlib.import_module("test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration")
        before_launcher = _relevant_module_state()
        _require(
            not any(value["present"] for value in before_launcher.values()),
            "RUNNER-PRE-APPLAUNCHER-PACKAGE-POLLUTION",
            before_launcher,
        )
        result["exact_re3_pre_AppLauncher_module_state"] = before_launcher

        import torch

        cuda_probe = torch.empty((1,), dtype=torch.float32, device="cuda:0")
        cuda_probe.add_(1.0)
        torch.cuda.synchronize()
        result["minimal_cuda_readiness"] = {
            "device": str(cuda_probe.device),
            "value": float(cuda_probe.item()),
            "pass": True,
        }
        del cuda_probe

        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        launcher = AppLauncher(
            headless=True,
            device="cuda:0",
            enable_cameras=False,
            livestream=0,
            xr=False,
            experience="",
        )
        simulation_app = launcher.app
        result["AppLauncher_lifetimes"] = 1

        import gymnasium as gym
        from gymnasium.envs.registration import load_env_creator

        before_canonical_import = _relevant_module_state()
        import isaaclab_tasks  # noqa: F401
        package = importlib.import_module(PACKAGE_NAME)
        defining = importlib.import_module(DEFINING_MODULE)
        spec = gym.spec(ENV_ID)
        resolved = load_env_creator(spec.entry_point)
        _require(spec.entry_point == ENTRY_POINT, "FORMAL-ENTRY-POINT", spec.entry_point)
        _require(
            resolved is defining.ScanMobileManipulatorEnv
            and resolved is package.ScanMobileManipulatorEnv,
            "FORMAL-CLASS-IDENTITY",
        )
        result["resolution_before_gym_make"] = {
            "module_state_before_canonical_import": before_canonical_import,
            "module_state_after_canonical_import": _relevant_module_state(),
            "spec_id": spec.id,
            "entry_point": spec.entry_point,
            "package_file": package.__file__,
            "resolved_class_module": resolved.__module__,
            "resolved_class_name": resolved.__name__,
            "identity_matches_defining_module": resolved is defining.ScanMobileManipulatorEnv,
            "identity_matches_package_export": resolved is package.ScanMobileManipulatorEnv,
            "pass": True,
        }

        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
            _EventProfileLifecycleDomainSpec,
            _EventProfileLifecycleRuntimeDomain,
        )
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import (
            _compose_event_assignment_harl_wrapper,
        )
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
            AssignmentProfileName,
            AssignmentProfileResolutionOrigin,
            resolve_assignment_profile,
        )

        cfg = defining.ScanMobileManipulatorEnvCfg()
        cfg.scene.num_envs = 2
        cfg.episode_length_s = 30.0
        profile = resolve_assignment_profile(
            AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
        )
        cfg.assignment_lifecycle_profile = profile.profile_name.value
        device = torch.device(cfg.sim.device)
        resolved_m = len(cfg.possible_agents)
        resolved_n = len(cfg.viewpoint_poses)
        domain = _EventProfileLifecycleRuntimeDomain(
            _EventProfileLifecycleDomainSpec(
                profile,
                device=device,
                env_ids=torch.arange(2, dtype=torch.int64, device=device),
                num_robots=resolved_m,
                num_tasks=resolved_n,
            )
        )

        env = gym.make(
            ENV_ID,
            cfg=cfg,
            resolved_assignment_profile=profile,
            event_lifecycle_runtime_domain=domain,
            event_admission_validation_port=domain.environment_admission_validation_port,
        )
        result["environment_constructions"] = 1
        raw = env.unwrapped
        _require(type(raw) is resolved, "FORMAL-CONSTRUCTED-TYPE", type(raw))
        wrapper = _compose_event_assignment_harl_wrapper(
            env=env,
            resolved_assignment_profile=profile,
            runtime_domain=domain,
            assignment_profile_entrypoint="B2-T4-EP.environment_reset_smoke",
        )
        reset_result = wrapper.reset()
        result["initial_resets"] = 1
        _require(type(reset_result) is tuple and len(reset_result) == 3, "FORMAL-RESET-CONTRACT")
        observations, shared_observations, available_actions = reset_result
        generations = wrapper.last_lifecycle_episode_generation
        current_publication = domain.current_read_port.read_current()
        reset_evidence = {
            "schema_version": "b2_t4_ep_reset_structural_evidence_v1",
            "reset_returned_successfully": True,
            "observation_shapes": _shape(observations),
            "shared_observation_shape": _shape(shared_observations),
            "available_actions_shape": _shape(available_actions),
            "available_actions_expected_absent_at_I4_boundary": available_actions is None,
            "device": str(raw.device),
            "num_envs": int(raw.num_envs),
            "M": int(raw.num_agents_cfg),
            "N": int(raw.num_viewpoints),
            "episode_length_s": float(raw.cfg.episode_length_s),
            "max_episode_length": int(raw.max_episode_length),
            "control_step_seconds": float(raw.step_dt),
            "P2_event_runtime_initialized": bool(
                raw._event_lifecycle_environment_port is domain.environment_port
            ),
            "episode_generation_shape": _shape(generations),
            "episode_generation_values": tuple(int(value) for value in generations.detach().cpu().tolist()),
            "current_publication_type": type(current_publication).__name__,
            "physical_environment_steps": int(raw.common_step_counter),
            "pass": True,
        }
        _require(
            reset_evidence["num_envs"] == 2
            and reset_evidence["M"] == 3
            and reset_evidence["N"] == 12
            and reset_evidence["episode_length_s"] == 30.0
            and reset_evidence["max_episode_length"] == 300
            and reset_evidence["control_step_seconds"] == 0.1
            and reset_evidence["P2_event_runtime_initialized"]
            and reset_evidence["physical_environment_steps"] == 0,
            "FORMAL-RESET-STRUCTURE",
            reset_evidence,
        )
        result.update(
            {
                "status": "passed",
                "classification": PASS,
                "environment_type": f"{type(env).__module__}.{type(env).__name__}",
                "unwrapped_type": f"{type(raw).__module__}.{type(raw).__name__}",
                "normal_horizon_config": {
                    "profile": profile.profile_name.value,
                    "device": str(raw.device),
                    "num_envs": int(raw.num_envs),
                    "M": int(raw.num_agents_cfg),
                    "N": int(raw.num_viewpoints),
                    "episode_length_s": float(raw.cfg.episode_length_s),
                    "max_episode_length": int(raw.max_episode_length),
                    "control_step_seconds": float(raw.step_dt),
                },
                "physical_environment_steps": 0,
                "reset_structural_evidence": reset_evidence,
            }
        )
    except BaseException as exc:
        result["exception_type"] = type(exc).__name__
        result["exception"] = str(exc)
        if result["environment_constructions"] == 1 and result["initial_resets"] == 0:
            result["classification"] = "PHASE-B2-T4-EP-STOP-ENVIRONMENT-RESET-FAILED"
    finally:
        if env is not None:
            try:
                env.close()
                result["environment_close_pass"] = True
            except BaseException as exc:
                close_errors.append(f"environment: {type(exc).__name__}: {exc}")
                result["environment_close_pass"] = False
        else:
            result["environment_close_pass"] = True
        if simulation_app is not None:
            try:
                simulation_app.close()
                result["AppLauncher_close_pass"] = True
            except BaseException as exc:
                close_errors.append(f"AppLauncher: {type(exc).__name__}: {exc}")
                result["AppLauncher_close_pass"] = False
        else:
            result["AppLauncher_close_pass"] = True
        result["close_errors"] = close_errors
        result["clean_close_pass"] = not close_errors
        if close_errors and result["status"] == "passed":
            result["status"] = "failed"
            result["classification"] = "PHASE-B2-T4-EP-STOP-RESOURCE-CLOSE-FAILED"
        _atomic_json(ARTIFACTS / "formal_environment_smoke.json", result)
        if reset_evidence is not None:
            _atomic_json(ARTIFACTS / "reset_structural_evidence.json", reset_evidence)
        _atomic_json(
            ARTIFACTS / "final_result.json",
            {
                "schema_version": "b2_t4_ep_final_result_v1",
                "status": result["status"],
                "classification": result["classification"],
                "formal_attempts": 1,
                "AppLauncher_lifetimes": result["AppLauncher_lifetimes"],
                "environment_constructions": result["environment_constructions"],
                "initial_resets": result["initial_resets"],
                "physical_environment_steps": result["physical_environment_steps"],
                "persistent_learner_constructions": 0,
                "learner_updates": 0,
                "actor_backward_steps": [0, 0],
                "critic_backward_steps": [0, 0],
                "ValueNorm_updates": 0,
                "checkpoint_io": 0,
                "public_activation": 0,
                "evaluation_playback": 0,
                "clean_close_pass": result["clean_close_pass"],
            },
        )
    _require(result["status"] == "passed", str(result["classification"]), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("matrix", "probe", "negative", "formal"))
    parser.add_argument("--sequence", choices=("canonical", "re2", "re3", "re3_repeat"))
    args = parser.parse_args()
    if args.mode == "matrix":
        payload = _run_matrix()
    elif args.mode == "probe":
        _require(args.sequence is not None, "MISSING-PROBE-SEQUENCE")
        payload = _pure_probe(args.sequence)
    elif args.mode == "negative":
        payload = _negative_probe()
    else:
        payload = _run_formal()
    print("B2_T4_EP_JSON=" + json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
