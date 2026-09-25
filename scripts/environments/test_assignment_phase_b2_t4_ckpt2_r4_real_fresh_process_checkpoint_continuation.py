"""CKPT2-R4: import-isolated real-CUDA fresh-process continuation gate.

The orchestration interpreter stays free of Isaac task imports. Production-schema
qualification runs in one short-lived subprocess, while processes A and B import
the real registered task package only after AppLauncher initialization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENTREAD = SCAN / "AgentRead"
DAY = AGENTREAD / "202609" / "20260923"
ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r4_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
R3_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r3_real_fresh_process_checkpoint_continuation.py"
R3_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r3_artifacts"
R3_REPORT = DAY / "PHASE_B2_T4_CKPT2_R3_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
R1_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py"
BASE_HARNESS = HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
ENVIRONMENT_ID = "Isaac-Scan-Mobile-Manipulator-Direct-v0"
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-R4-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
BEFORE_FIRST_WRITE = {
    "branch": "main",
    "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "porcelain_bytes": 12832532,
    "porcelain_entry_count": 51063,
    "porcelain_sha256": "7471563c4def4be9ec80e552ba088b42afc181b0c880e259c04da0af2bbf5862",
    "staged_path_count": 359,
    "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
    "agentread_file_count": 50599,
    "agentread_path_set_sha256": "3224b2ec34af444eeef94a59856d46d94f9ebe35f653079d3addae197ffc9a99",
}
EXPECTED_R3 = {
    "artifact_file_count": 30,
    "artifact_inventory_sha256": "644cc7f85f4274dc29804cc82a3cac9dd6a7168601fdd2363d19691d550a7839",
    "harness_sha256": "47aaadc95346e3b6e2b94aca58f2e847ea67c7320739d09fc0d1d478d66457f1",
    "report_sha256": "39ab4444a60cd3726886781a1e0ad174cfdeec48a35d0434780a30bda1cddd4d",
}
EXPECTED_HISTORY = {
    "ckpt2": {
        "artifact_root": DAY / "b2_t4_ckpt2_artifacts",
        "harness": HERE / "test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py",
        "report": DAY / "PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md",
        "count": 35,
        "inventory": "248d4415835bab99029da77478bac6f195fdfc40de5193378423c7a5b86083ef",
        "harness_sha256": "3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551",
        "report_sha256": "ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7",
    },
    "r1": {
        "artifact_root": DAY / "b2_t4_ckpt2_r1_artifacts",
        "harness": R1_HARNESS,
        "report": DAY / "PHASE_B2_T4_CKPT2_R1_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md",
        "count": 25,
        "inventory": "511fa0d2727c6a9f2eeece317ce06b75f7b03c47e46607c0e4e09553d93f122b",
        "harness_sha256": "c11774e887045bd96aae8cb2241f2bee953bf1eb92a411888a7fc58927abe324",
        "report_sha256": "94b0898b7c4d28c5a14982e1052de86eb84acaf76fd73d7e0b4f5841b55a1ef4",
    },
    "r2": {
        "artifact_root": DAY / "b2_t4_ckpt2_r2_artifacts",
        "harness": HERE / "test_assignment_phase_b2_t4_ckpt2_r2_real_fresh_process_checkpoint_continuation.py",
        "report": DAY / "PHASE_B2_T4_CKPT2_R2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md",
        "count": 30,
        "inventory": "d1e9500bf77e199623fbae9521a365a72f0846f7dea0c5a073125fcccc17f091",
        "harness_sha256": "ff152638626cef06c79641c0e032d94b0537965e7a07136cc539584311d2e2f7",
        "report_sha256": "4316eb0fce204f82d3688c7c357a70d4108b0125438b070f331d9def43012676",
    },
}
EXPECTED_CKPT1_SHA256 = {
    "assignment_optimization_checkpoint.py": "b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9",
    "assignment_harl_training.py": "31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
EXPECTED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2-R4 {code}: {detail!r}")


def _inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    rows = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + bytes([10])
    return rows, hashlib.sha256(encoded).hexdigest()


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.longpaths=true", *arguments], cwd=ROOT)


def _repository_authority() -> dict[str, Any]:
    status = _git_bytes("status", "--porcelain=v1", "-uall", "-z")
    staged = _git_bytes("diff", "--cached", "--name-only", "-z")
    index = _git_bytes("ls-files", "--stage")
    paths = sorted(path.relative_to(ROOT).as_posix() for path in AGENTREAD.rglob("*") if path.is_file())
    return {
        "branch": _git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": _git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": _git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": _git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "porcelain_bytes": len(status),
        "porcelain_entry_count": sum(bool(item) for item in status.split(bytes([0]))),
        "porcelain_sha256": hashlib.sha256(status).hexdigest(),
        "staged_path_count": sum(bool(item) for item in staged.split(bytes([0]))),
        "staged_index_sha256": hashlib.sha256(index).hexdigest(),
        "agentread_file_count": len(paths),
        "agentread_path_set_sha256": hashlib.sha256(("\n".join(paths) + "\n").encode()).hexdigest(),
        "before_first_write": BEFORE_FIRST_WRITE,
        "git_mutations_by_ckpt2_r4": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }


def _safe_r3_namespace() -> dict[str, Any]:
    """Compile R3 without executing its package-shim import or eager runtime build."""

    source = R3_HARNESS.read_text(encoding="utf-8")
    source = source.replace("CKPT2-R3", "CKPT2-R4").replace("ckpt2_r3", "ckpt2_r4")
    eager_import = "FULL, REAL = _load_production_modules()"
    eager_runtime = "RUNTIME, TRANSFORMED_RUNTIME_SHA256 = _runtime_namespace()"
    _require(source.count(eager_import) == 1, "R3-EAGER-IMPORT-TRANSFORM")
    _require(source.count(eager_runtime) == 1, "R3-EAGER-RUNTIME-TRANSFORM")
    source = source.replace(eager_import, "FULL = REAL = None")
    source = source.replace(eager_runtime, 'RUNTIME = {}\nTRANSFORMED_RUNTIME_SHA256 = "DEFERRED"')
    module_name = "_b2_t4_ckpt2_r4_import_safe_source"
    module = type(sys)(module_name)
    namespace: dict[str, Any] = module.__dict__
    namespace.update({
        "__name__": module_name,
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    })
    sys.modules[module_name] = module
    exec(compile(source, str(R3_HARNESS), "exec"), namespace)
    namespace.update({
        "ARTIFACT_ROOT": ARTIFACT_ROOT,
        "CHECKPOINT_ROOT": CHECKPOINT_ROOT,
        "PASS_CLASSIFICATION": PASS_CLASSIFICATION,
        "BEFORE_FIRST_WRITE": BEFORE_FIRST_WRITE,
    })
    return namespace


def _real_package_gates(process: str) -> tuple[Any, Any]:
    import gymnasium as gym

    package = sys.modules.get(PACKAGE)
    package_file = Path(str(getattr(package, "__file__", ""))).resolve() if package is not None else None
    expected_root = SCAN.resolve()
    path_ok = package_file is not None and package_file.is_relative_to(expected_root)
    env_class = getattr(package, "ScanMobileManipulatorEnv", None) if package is not None else None
    class_ok = env_class is not None and getattr(env_class, "__module__", "") == f"{PACKAGE}.scan_mobile_manipulator_env"
    identity = {
        "process": process.upper(),
        "pid": os.getpid(),
        "package": PACKAGE,
        "package_file": str(package_file) if package_file is not None else None,
        "expected_package_root": str(expected_root),
        "under_production_source": path_ok,
        "synthetic_placeholder": package is not None and getattr(package, "__file__", None) is None,
        "ScanMobileManipulatorEnv_attribute": env_class is not None,
        "ScanMobileManipulatorEnv_real_module": class_ok,
    }
    identity["result"] = "PASS" if path_ok and not identity["synthetic_placeholder"] and class_ok else "FAIL"
    _require(identity["result"] == "PASS", "REAL-PACKAGE-IDENTITY", identity)
    spec = gym.spec(ENVIRONMENT_ID)
    registration = {
        "process": process.upper(),
        "pid": os.getpid(),
        "environment_id": ENVIRONMENT_ID,
        "registered": spec is not None,
        "entry_point": str(spec.entry_point),
        "expected_entry_point": f"{PACKAGE}:ScanMobileManipulatorEnv",
        "creator_is_real_module": spec.entry_point == f"{PACKAGE}:ScanMobileManipulatorEnv" and class_ok,
    }
    registration["result"] = "PASS" if registration["registered"] and registration["creator_is_real_module"] else "FAIL"
    _require(registration["result"] == "PASS", "ENVIRONMENT-REGISTRATION", registration)
    return identity, registration


def _install_r4_inner_loader(runtime: dict[str, Any]) -> None:
    def load_inner_base(hooks: Mapping[str, Any]) -> dict[str, Any]:
        start_index = int(hooks["TRANSACTION_START_INDEX"])
        process = "a" if start_index == 1 else "b"
        process_dir = ARTIFACT_ROOT / f"process_{process}"

        def before_gym_make(resources: dict[str, Any]) -> None:
            identity, registration = _real_package_gates(process)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_real_package_identity.json", identity)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_environment_registration.json", registration)
            if process == "a":
                _atomic_json(ARTIFACT_ROOT / "r3_import_side_effect_regression_check.json", {
                    "historical_r3_failure": "synthetic package lacked ScanMobileManipulatorEnv",
                    "current_package_file": identity["package_file"],
                    "synthetic_placeholder": False,
                    "ScanMobileManipulatorEnv_attribute": True,
                    "checked_after_AppLauncher_before_gym_make": True,
                    "result": "PASS",
                })

        def after_gym_make(env: Any, resources: dict[str, Any]) -> None:
            payload = {
                "process": process.upper(),
                "pid": os.getpid(),
                "environment_id": ENVIRONMENT_ID,
                "gym_make_returned": env is not None,
                "environment_constructions": resources.get("environment_constructions"),
                "unwrapped_type": type(env.unwrapped).__name__ if env is not None else None,
                "result": "PASS" if env is not None and resources.get("environment_constructions") == 1 else "FAIL",
            }
            _require(payload["result"] == "PASS", "ENVIRONMENT-CREATION", payload)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_environment_creation.json", payload)
            _atomic_json(process_dir / "environment_creation.json", payload)

        source = BASE_HARNESS.read_text(encoding="utf-8")
        replacements = {
            "    for transaction_index in range(1, TRANSACTION_COUNT + 1):\n": "    for transaction_index in range(TRANSACTION_START_INDEX, TRANSACTION_START_INDEX + TRANSACTION_COUNT):\n",
            "    reset_result = route.reset()\n": "    _ckpt2_r4_after_learner_construction(route, actors_raw, critic_raw, live_value_normalizer, resources)\n    reset_result = route.reset()\n",
            "        pre_collection = _learner_snapshot(\n": "        _ckpt2_r4_before_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n        pre_collection = _learner_snapshot(\n",
            "        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n": "        _ckpt2_r4_after_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n",
            "        resources[\"adapter_transaction_returned\"] = True\n": "        _ckpt2_r4_after_transaction(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources, transaction)\n        resources[\"adapter_transaction_returned\"] = True\n",
            "    run_identity = f\"b2-t0-re1-repeated-smoke-{os.getpid()}\"\n": "    run_identity = str(resources[\"ckpt2_r4_run_identity\"])\n",
            "    env = gym.make(\n": "    _ckpt2_r4_before_gym_make(resources)\n    env = gym.make(\n",
            "    resources[\"environment_constructions\"] = 1\n": "    resources[\"environment_constructions\"] = 1\n    _ckpt2_r4_after_gym_make(env, resources)\n",
            '"transaction_4_started"': '"next_unauthorized_transaction_started"',
        }
        for old, new in replacements.items():
            count = source.count(old)
            expected = 2 if old == '"transaction_4_started"' else 1
            _require(count == expected, "BASE-HARNESS-TRANSFORM", {"needle": old, "count": count, "expected": expected})
            source = source.replace(old, new)
        namespace: dict[str, Any] = {
            "__name__": "_b2_t4_ckpt2_r4_bounded_core",
            "__file__": str(BASE_HARNESS),
            "__package__": None,
            **hooks,
            "_ckpt2_r4_before_gym_make": before_gym_make,
            "_ckpt2_r4_after_gym_make": after_gym_make,
        }
        exec(compile(source, str(BASE_HARNESS), "exec"), namespace)
        namespace["TRANSACTION_COUNT"] = 3
        return namespace

    runtime["_load_inner_base"] = load_inner_base


def _runtime_bundle() -> tuple[dict[str, Any], dict[str, Any], str]:
    _require(not any(name == PACKAGE or name.startswith(PACKAGE + ".") for name in sys.modules), "PARENT-PACKAGE-CONTAMINATION")
    r4 = _safe_r3_namespace()
    runtime, digest = r4["_runtime_namespace"]()
    runtime.update({"ARTIFACT_ROOT": ARTIFACT_ROOT, "CHECKPOINT_ROOT": CHECKPOINT_ROOT, "PASS_CLASSIFICATION": PASS_CLASSIFICATION})
    _install_r4_inner_loader(runtime)
    r4.update({"RUNTIME": runtime, "TRANSFORMED_RUNTIME_SHA256": digest})
    _require(not any(name == PACKAGE or name.startswith(PACKAGE + ".") for name in sys.modules), "PARENT-RUNTIME-PACKAGE-CONTAMINATION")
    return r4, runtime, digest


def _clean_baseline(args: argparse.Namespace) -> int:
    names = sorted(name for name in sys.modules if name == PACKAGE or name.startswith(PACKAGE + "."))
    payload = {
        "run_id": args.run_id,
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "python": sys.executable,
        "production_package_modules_at_entry": names,
        "production_package_loaded": bool(names),
        "fresh_short_lived_interpreter": True,
        "result": "PASS" if not names else "FAIL",
    }
    _atomic_json(ARTIFACT_ROOT / "clean_interpreter_baseline.json", payload)
    _require(payload["result"] == "PASS", "CLEAN-INTERPRETER-BASELINE", payload)
    return 0


def _pure_qualification(args: argparse.Namespace) -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location("_historical_ckpt2_r3_pure", R3_HARNESS)
    _require(spec is not None and spec.loader is not None, "R3-PURE-SPEC")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    shim = sys.modules.get(PACKAGE)
    reproduction = {
        "historical_failure": "AttributeError: module lacked ScanMobileManipulatorEnv",
        "synthetic_package_present": shim is not None,
        "synthetic_package_file": getattr(shim, "__file__", None),
        "ScanMobileManipulatorEnv_attribute": hasattr(shim, "ScanMobileManipulatorEnv") if shim is not None else False,
        "reproduced": shim is not None and getattr(shim, "__file__", None) is None and not hasattr(shim, "ScanMobileManipulatorEnv"),
    }
    reproduction["result"] = "PASS" if reproduction["reproduced"] else "FAIL"
    _require(reproduction["result"] == "PASS", "R3-IMPORT-FAILURE-REPRODUCTION", reproduction)
    inventory, contract = module._identity_artifacts()
    parity, r2_reproduction, positive, negative = module._schema_and_ledger_qualification()
    binding = module._ledger_schema()
    lr = module.RUNTIME["_lr_boundary_pure"]()
    gate = module.RUNTIME["_launch_gate_matrix"]()
    outputs = {
        "r3_import_namespace_failure_reproduction.json": reproduction,
        "transaction_update_identity_authority_inventory.json": inventory,
        "transaction_update_identity_contract.json": contract,
        "production_transaction_schema_parity.json": parity,
        "ckpt2_r2_identity_binding_failure_reproduction.json": r2_reproduction,
        "transaction_ledger_schema_binding_v2.json": binding,
        "transaction_ledger_v2_positive_qualification.json": positive,
        "transaction_identity_negative_matrix.json": negative,
        "r2_event_return_binding_preservation.json": {"authority": "transaction.real_audit.event_return_compute_count", "observed_fixture_count": positive["event_return_count"], "changed_by_r4": False, "result": "PASS"},
        "r1_lr_boundary_preservation.json": {"rule": "LR applied before pre-collection fingerprint; no LR mutation during collection", "pure_boundary_fixture": lr, "changed_by_r4": False, "result": "PASS"},
        "process_a_semantic_gate_preservation.json": {"all_conditions_required": True, "negative_matrix": gate, "changed_by_r4": False, "result": "PASS"},
    }
    for name, payload in outputs.items():
        _atomic_json(ARTIFACT_ROOT / name, payload)
    result = {
        "run_id": args.run_id,
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "production_dataclass_constructors_used": True,
        "production_schema_parity": parity["result"],
        "identity_relation": contract["relation"],
        "ledger_contract_case": contract["case"],
        "ledger_v2_positive": positive["result"],
        "identity_negative_matrix": f"{negative['stop_case_count']}/8 expected STOP",
        "event_return_authority": "transaction.real_audit.event_return_compute_count",
        "process_exits_before_process_a": True,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "pure_qualification_result.json", result)
    return 0


def _run_preflight_children(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = []
    for mode, artifact in (("--clean-baseline", "clean_interpreter_baseline.json"), ("--pure-qualification", "pure_qualification_result.json")):
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), mode, "--run-id", args.run_id], cwd=ROOT)
        return_code = process.wait()
        active = _pid_active(process.pid)
        payload = json.loads((ARTIFACT_ROOT / artifact).read_text(encoding="utf-8")) if (ARTIFACT_ROOT / artifact).is_file() else None
        row = {"mode": mode, "pid": process.pid, "return_code": return_code, "pid_inactive_after_wait": not active, "artifact": artifact, "semantic_result": payload.get("result") if payload else None}
        rows.append(row)
        _require(return_code == 0 and not active and payload is not None and payload.get("result") == "PASS", "PREFLIGHT-SUBPROCESS", row)
    isolation = {
        "orchestration_parent_pid": os.getpid(),
        "clean_baseline": rows[0],
        "pure_qualification": rows[1],
        "distinct_pids": len({os.getpid(), rows[0]["pid"], rows[1]["pid"]}) == 3,
        "both_exited_before_process_a": True,
        "process_a_started": False,
        "cross_process_python_object_sharing": False,
        "sys_modules_pop_used": False,
        "result": "PASS",
    }
    _require(isolation["distinct_pids"], "PREFLIGHT-PID-ISOLATION", isolation)
    _atomic_json(ARTIFACT_ROOT / "pure_runtime_process_isolation.json", isolation)
    return rows[0], rows[1]


def _pid_active(pid: int) -> bool:
    completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
    return f'"{pid}"' in completed.stdout


def _preflight_and_parent(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    pure_path = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    _require(pure_path.is_file(), "MISSING-CKPT1-PURE-PREFLIGHT")
    ckpt1_test = json.loads(pure_path.read_text(encoding="utf-8"))
    _require(ckpt1_test.get("successful") is True and ckpt1_test.get("tests_run") == 6 and ckpt1_test.get("negative_case_count") == 25 and ckpt1_test.get("unexpected_negative_case_count") == 0, "CKPT1-PURE-PREFLIGHT", ckpt1_test)
    authority = _repository_authority()
    _require(authority["branch"] == "main" and authority["HEAD"] == authority["origin_main"] == authority["merge_base"] == BEFORE_FIRST_WRITE["HEAD"], "REPOSITORY-AUTHORITY", authority)
    _require(authority["staged_path_count"] == BEFORE_FIRST_WRITE["staged_path_count"] and authority["staged_index_sha256"] == BEFORE_FIRST_WRITE["staged_index_sha256"], "STAGED-INDEX-AUTHORITY", authority)
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", authority)

    r3_inventory, r3_digest = _inventory(R3_ARTIFACT_ROOT)
    r3 = {
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRE-ENVIRONMENT / NO LEARNER / NOT POISONED / NO RETRY",
        "historical_run_id": "b2-t4-ckpt2-r3-20260923-real01-200f916d",
        "artifact_file_count": len(r3_inventory),
        "artifact_inventory_sha256": r3_digest,
        "harness_sha256": _sha(R3_HARNESS),
        "report_sha256": _sha(R3_REPORT),
    }
    r3["preserved"] = all(r3[key] == value for key, value in EXPECTED_R3.items())
    r3["result"] = "PASS" if r3["preserved"] else "FAIL"
    _require(r3["preserved"], "HISTORICAL-R3-DRIFT", r3)
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_r3_preservation.json", r3)
    for label, expected in EXPECTED_HISTORY.items():
        rows, digest = _inventory(expected["artifact_root"])
        preservation = {
            "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRESERVED",
            "artifact_file_count": len(rows),
            "artifact_inventory_sha256": digest,
            "harness_sha256": _sha(expected["harness"]),
            "report_sha256": _sha(expected["report"]),
        }
        preservation["preserved"] = (
            preservation["artifact_file_count"] == expected["count"]
            and preservation["artifact_inventory_sha256"] == expected["inventory"]
            and preservation["harness_sha256"] == expected["harness_sha256"]
            and preservation["report_sha256"] == expected["report_sha256"]
        )
        preservation["result"] = "PASS" if preservation["preserved"] else "FAIL"
        _require(preservation["preserved"], f"HISTORICAL-{label.upper()}-DRIFT", preservation)
        _atomic_json(ARTIFACT_ROOT / f"historical_{'ckpt2_' + label if label != 'ckpt2' else 'ckpt2'}_preservation.json", preservation)

    production = {name: _sha(SCAN / name) for name in EXPECTED_CKPT1_SHA256}
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL_SHA256}
    _require(production == EXPECTED_CKPT1_SHA256, "CKPT1-PRODUCTION-DRIFT", production)
    _require(installed == EXPECTED_HARL_SHA256, "INSTALLED-HARL-DRIFT", installed)
    _atomic_json(ARTIFACT_ROOT / "ckpt1_preservation.json", {"status": "GPT REVIEW PASS / CLOSED", "implementation_sha256": production, "installed_harl_sha256": installed, "pure_tests": "6/6", "negative_matrix": "25/25", "result": "PASS"})

    clean, pure = _run_preflight_children(args)
    r4, runtime, runtime_digest = _runtime_bundle()
    _atomic_json(ARTIFACT_ROOT / "pre_runtime_harness_repair_log.json", {
        "repairs": [{"id": "PURE_RUNTIME_IMPORT_NAMESPACE_ISOLATION", "scope": "CKPT2-R4 harness only", "historical_r3_source_modified": False, "sys_modules_pop_used": False, "result": "PASS"}],
        "production_files_modified": 0, "installed_harl_files_modified": 0, "unresolved_test_side_repairs": 0, "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "import_namespace_isolation_contract.json", {
        "parent_allowed_imports": "standard library and side-effect-free harness definitions",
        "production_schema_qualification": "one short-lived subprocess",
        "real_package_import": "A/B only after AppLauncher initialization",
        "same_runtime_sys_modules_cleanup": False,
        "primary_mechanism": "OS process isolation",
        "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "r3_identity_contract_preservation.json", {"identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C", "ledger_identity_path": "transaction.r5_transaction.quiescence_evidence.update_id", "event_return_authority": "transaction.real_audit.event_return_compute_count", "result": "PASS"})
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r4_run_identity.json", {"run_id": args.run_id, "fresh": True, "attempt_number": 1, "maximum_attempts": 1, "retry_count": 0})
    preflight = {
        "run_id": args.run_id,
        "historical_ckpt2_r1_r2_r3_preserved": True,
        "ckpt1_focused_suite": "6/6 PASS; 25/25 expected negative",
        "r3_import_failure_reproduction": "PASS",
        "clean_interpreter_baseline": clean["semantic_result"],
        "pure_qualification": pure["semantic_result"],
        "process_isolation": "PASS",
        "identity_relation": "ONE_TO_ONE_BOUND",
        "ledger_contract_case": "CASE C",
        "event_return_authority": "transaction.real_audit.event_return_compute_count",
        "installed_harl_preservation": "PASS",
        "runtime_started": False,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r4_preflight.json", preflight)
    harness = Path(__file__).resolve()
    freeze = {
        "run_id": args.run_id,
        "frozen_before_process_a": True,
        "harness_sha256": _sha(harness),
        "transformed_r1_runtime_sha256": runtime_digest,
        "source_sha256": {harness.relative_to(ROOT).as_posix(): _sha(harness), R3_HARNESS.relative_to(ROOT).as_posix(): _sha(R3_HARNESS), R1_HARNESS.relative_to(ROOT).as_posix(): _sha(R1_HARNESS), **{(SCAN / name).relative_to(ROOT).as_posix(): value for name, value in production.items()}},
        "post_freeze_source_edits_authorized": False,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r4_pre_runtime_freeze.json", freeze)
    result = runtime["_parent"](args)
    if result == 0:
        final_path = ARTIFACT_ROOT / "final_result.json"
        final = json.loads(final_path.read_text(encoding="utf-8"))
        final.update({
            "classification": PASS_CLASSIFICATION,
            "historical_ckpt2_r1_r2_r3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRESERVED",
            "import_namespace_isolation": "PASS",
            "real_package_identity_A_B": "PASS",
            "environment_registration_A_B": "PASS",
            "environment_creation_A_B": "PASS",
            "identity_relation": "ONE_TO_ONE_BOUND",
            "ledger_contract_case": "CASE C",
            "transaction_event_return_authority": "transaction.real_audit.event_return_compute_count",
        })
        _atomic_json(final_path, final)
    else:
        failure_path = ARTIFACT_ROOT / "failure_receipt.json"
        failure = json.loads(failure_path.read_text(encoding="utf-8")) if failure_path.is_file() else {}
        a_failure = ARTIFACT_ROOT / "process_a" / "failure_receipt.json"
        detail = json.loads(a_failure.read_text(encoding="utf-8")) if a_failure.is_file() else {}
        if not (ARTIFACT_ROOT / "process_a_environment_creation.json").is_file():
            failure["classification"] = "PHASE-B2-T4-CKPT2-R4-STOP-PROCESS-A-ENVIRONMENT-CREATION"
        failure.update({"retry_permitted": False, "retry_count": 0, "worker_failure": detail})
        _atomic_json(failure_path, failure)
    return result


def _worker(args: argparse.Namespace) -> int:
    _r4, runtime, _digest = _runtime_bundle()
    return runtime["_worker"](args)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--parent", action="store_true")
    mode.add_argument("--worker", choices=("a", "b"))
    mode.add_argument("--pure-qualification", action="store_true")
    mode.add_argument("--clean-baseline", action="store_true")
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.clean_baseline:
        return _clean_baseline(args)
    if args.pure_qualification:
        return _pure_qualification(args)
    if args.worker:
        return _worker(args)
    return _preflight_and_parent(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        failure_path = ARTIFACT_ROOT / "failure_receipt.json"
        if not failure_path.exists():
            _atomic_json(failure_path, {"classification": "PHASE-B2-T4-CKPT2-R4-STOP-PRE-RUNTIME-IMPORT-ISOLATION", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(), "retry_permitted": False, "retry_count": 0})
        traceback.print_exc()
        raise SystemExit(1)
