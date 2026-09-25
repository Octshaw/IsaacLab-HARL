"""RE6-R3 test-side preflight and exactly-one fresh formal-attempt harness.

All formal modes are hard-gated by the read-only normalizer and PPQ-V2
qualification artifacts. Importing this module never imports Isaac or HARL.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Mapping
import uuid

import _assignment_phase_b2_t4_re6_r3_ppq_v2_normalization as NORM
import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as PPQ
import _assignment_phase_b2_t4_w2e_multi_update_completion as W2E
import _assignment_phase_b2_t4_windows_evidence_persistence as PW
import test_assignment_phase_b2_t4_ppq_postprocess as V1TEST
import test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract as V2TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DATE = SCAN / "AgentRead/202609/20260920"
OUT = DATE / "b2_t4_re6_r3_artifacts"
PREFIX = OUT / "b2_t4_re6_r3_normal_horizon_20260920_formal01"
NORMALIZER = HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py"
HELPER = HERE / "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py"
SCHEMA = DATE / "b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json"
MANIFEST = DATE / "b2_t4_ppq_v2_artifacts/ppq_v2_source_identity_manifest.json"
W2I = DATE / "b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json"
PW_HELPER = HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py"
RE5_SOURCE = HERE / "test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py"
RE6_R1_SOURCE = HERE / "test_assignment_phase_b2_t4_re6_r1_normal_horizon_learned_training_integration.py"
PRODUCTION = V2TEST.PRODUCTION
CONFIG = V2TEST.CONFIG
PHASE = "B2-T4-RE6-R3"
EXPECTED = {
    "ppq_helper": (HELPER, "115d681d5e8473aa171e6232b6beca8c985139a58926d6d15850c2940785f903"),
    "ppq_runner": (HERE / "test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract.py",
                   "134a8c290949385854a4bf4e0cea11748f447a94fba503b4c6f2454118ab92dc"),
    "ppq_schema": (SCHEMA, "0742a9a0ed44cb1f3410fae8885e348f7a40b7dbc35ac089ca6cf920d89126d5"),
    "w2e": (HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py", PPQ.W2E_SHA),
    "w2i": (W2I, PPQ.W2I_SHA),
    "pw": (PW_HELPER, PPQ.PW_SHA),
    "re5_harness": (RE5_SOURCE, "4ae8e721e4dfbb42f53dd49bf91c002b502f7f2cf29757e2cf756bbe067ca2d8"),
    "re6_r1_harness": (RE6_R1_SOURCE, "858656975abef50adf6a143fe7f6bc68731756d2ad6378430acc6b9e3f3d049c"),
}


def _replace_once(source: str, old: str, new: str) -> str:
    require(source.count(old) == 1, "RUNTIME-SOURCE-DRIFT", old)
    return source.replace(old, new)


def derived_runtime() -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive the unchanged RE5 transaction gates into the fresh R3 namespace."""
    identities()
    source = RE5_SOURCE.read_text(encoding="utf-8")
    replacements = {
        'ARTIFACTS = DATE_ROOT / "b2_t4_re5_artifacts"':
            'ARTIFACTS = SCAN / "AgentRead" / "202609" / "20260920" / "b2_t4_re6_r3_artifacts"',
        'PREFIX = ARTIFACTS / "b2_t4_re5_normal_horizon_20260916_formal01"':
            'PREFIX = ARTIFACTS / "b2_t4_re6_r3_normal_horizon_20260920_formal01"',
    }
    for old, new in replacements.items():
        source = _replace_once(source, old, new)
    for old in ("re5_static_authority.json", "re5_runner_readiness_replay.json",
                "re5_preflight_summary.json", "re5_progress_persistence_binding.json",
                "re5_process_config_authority.json", "re5_cuda_cublas_readiness.json",
                "re5_worker_raw_result.json"):
        source = source.replace(f'"{old}"', f'"{old.replace("re5_", "re6_r3_", 1)}"')
    source = source.replace('"re5_runner"', '"re6_r3_runner"')
    source = source.replace('"B2-T4-RE5"', '"B2-T4-RE6-R3"')
    source = source.replace('PHASE-B2-T4-RE5-', 'PHASE-B2-T4-RE6-R3-')
    source = source.replace('b2-t4-re5-', 'b2-t4-re6-r3-')
    source = re.sub(r'b2_t4_re5_([a-z_]+_v1)', r'b2_t4_re6_r3_\1', source)
    source = source.replace('"b2_t4_re5_20260916_formal01"',
                            '"b2_t4_re6_r3_20260920_formal01"')
    namespace: dict[str, Any] = {"__name__": "_b2_t4_re6_r3_derived_harness",
                                  "__file__": str(Path(__file__).resolve()),
                                  "__package__": None}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), namespace)
    return namespace, {"source_sha256": sha(RE5_SOURCE),
                       "derived_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                       "artifact_namespace": str(OUT),
                       "transaction_gates": "source-derived unchanged RE5 gates",
                       "old_receipt_route": "not called by R3 formal worker"}


def require(ok: bool, reason: str, detail: object = None) -> None:
    if not ok:
        raise RuntimeError(f"STOP — PHASE-B2-T4-RE6-R3-STOP-{reason}: {detail!r}")


def sha(path: Path) -> str:
    return PPQ.sha_file(path)


def write(name: str, payload: Mapping[str, Any]) -> None:
    PPQ.atomic_persist(OUT / name, payload)


def identities() -> dict[str, Any]:
    sources = {name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                      "bytes": path.stat().st_size, "sha256": sha(path),
                      "expected_sha256": expected}
               for name, (path, expected) in EXPECTED.items()}
    require(all(row["sha256"] == row["expected_sha256"] for row in sources.values()),
            "PPQ-V2-IDENTITY-MISMATCH", sources)
    require(sources["w2e"]["bytes"] == 15089, "W2E-IDENTITY-MISMATCH")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["helper_sha256"] == sources["ppq_helper"]["sha256"] and
            manifest["runner_sha256"] == sources["ppq_runner"]["sha256"] and
            manifest["schema_sha256"] == sources["ppq_schema"]["sha256"],
            "PPQ-V2-MANIFEST-MISMATCH")
    for name, path in PRODUCTION.items():
        require(sha(path) == V2TEST.REVIEWED[name], "PRODUCTION-IDENTITY-MISMATCH", name)
    return {"pass": True, "sources": sources,
            "production": {name: sha(path) for name, path in PRODUCTION.items()},
            "ppq_v2_review": "GPT REVIEW PASS / CLOSED"}


def _generic_pw(value: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    return {"contract_version": PPQ.PW_VERSION, "run_id": run_id,
            "transaction_count": value["transactions"],
            "critic_actual": value["critic_records"],
            "actor_factor_actual": value["actor_factor_records"],
            "missing_count": value["missing"],
            "duplicate_count": value["duplicate"],
            "order_fault_count": value["out_of_order"],
            "digest_fault_count": value["digest_mismatch"],
            "temp_residue_count": value["temp_residue"]}


def historical_raw() -> tuple[dict[str, Any], Any]:
    """Read immutable completed RE6-R1 ledgers, never its poisoned receipt."""
    old = V1TEST.load_evidence()
    run_id = "re6-r3-historical-normalizer-fixture"
    raw = {"source_phase": PHASE, "run_id": run_id, "worker_pid": os.getpid(),
           "transactions": old["transactions"], "bridges": old["bridges"],
           "progress": V1TEST.read_jsonl("lifecycle_task_progress.jsonl"),
           "terminal": V1TEST.read_jsonl("terminal_reconciliation.jsonl"),
           "immutability": old["immutability"],
           "actor_reconciliation": V1TEST.read_jsonl("actor_evidence_reconciliation.jsonl"),
           "training_metrics": V1TEST.read_jsonl("training_metrics.jsonl"),
           "final": old["final"], "witnesses": old["final"]["primary_witnesses"],
           "partial_update": False, "route_poisoned": False,
           "checkpoint_io_count": 0, "public_activation_count": 0,
           "evaluation_playback_count": 0,
           "summary_claims": {"transaction_count": 160, "physical_transitions": 320,
                              "production_s10": 160, "bridge_count": 159,
                              "task_completed_count": 22, "coverage_max": 11,
                              "terminal_autoreset_count": 2,
                              "w2e_candidate_count": 29, "w2e_valid_count": 12}}
    def verified_pw() -> dict[str, Any]:
        result = V1TEST.verify_pw(PW, old)
        return _generic_pw(result, run_id)
    return raw, verified_pw


def synthetic_raw() -> tuple[dict[str, Any], Any]:
    """Production-shaped, current-config synthetic raw ledgers, not summaries."""
    fixture = V2TEST.synthetic_fixture(1)
    tx = copy.deepcopy(fixture["transactions"])
    for index, row in enumerate(tx, 1):
        actor = 5 if index <= 24 else 0
        row.update({"actor_backward_by_actor": [actor, 0, 0],
                    "actor_optimizer_step_by_actor": [actor, 0, 0],
                    "critic_backward": 10, "critic_optimizer_step": 10,
                    "valid_nonzero": 10, "valid_zero_effective": 0,
                    "valuenorm_update": 10, "event_returns": 1,
                    "stock_compute_returns": 0})
    bridges = copy.deepcopy(fixture["bridges"])
    steps = copy.deepcopy([step for step in fixture["w2e_input"]["steps"]
                           if step["global_physical_step"] >= 1])
    decisions = copy.deepcopy(fixture["w2e_input"]["decisions"])
    for step in steps:
        physical = step["global_physical_step"]
        for state in step["state_rows"]:
            state["coverage_count"] = 1 if physical < 4 else 2
            if physical >= 300:
                state["episode_generation"] = 1
                state["completion_count"] = [0]
    progress = []
    for index, row in enumerate(tx, 1):
        segment = [step for step in steps if step["transaction_index"] == index]
        lifecycle = [{k: v for k, v in decision.items() if k != "global_physical_step"}
                     for decision in decisions if decision["transaction_index"] == index]
        progress.append({"transaction_index": index, "update_id": row["update_id"],
                         "steps": segment, "lifecycle_rows": lifecycle})
    terminal = []
    for index, row in enumerate(tx, 1):
        found = index == 150
        terminal.append({"transaction_index": index, "update_id": row["update_id"],
                         "pass": True, "reason_counts": {"NONE": 1 if found else 2,
                             "TIME_LIMIT": int(found), "ALL_TASKS_COMPLETED": 0,
                             "NO_FEASIBLE_TASKS_REMAIN": 0},
                         "observed_keys": [[1, 0, 300]] if found else [],
                         "expected_keys": [[1, 0, 300]] if found else [],
                         "missing": [], "extra": [], "duplicates": []})
    initial_step = copy.deepcopy(fixture["w2e_input"]["steps"][0])
    w2_input = NORM._selector_input(progress, tx, bridges, 2, initial_step)
    selected = W2E.reconcile(w2_input)
    raw_witness = {name: {"pass": True} for name in (
        "W1_CROSS_UPDATE_OWNERSHIP", "W3_ZERO_DVM_ACTOR",
        "W4_NONTERMINAL_BOOTSTRAP", "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6_POST_AUTORESET_TRAINING", "W7_RUNTIME_P2_IMMUTABILITY")}
    raw_witness["W2_MULTI_UPDATE_COMPLETION"] = {"pass": True,
        "selected": selected["selected"], "candidate_count": selected["candidate_count"],
        "valid_count": selected["valid_count"]}
    raw_witness["W7_RUNTIME_P2_IMMUTABILITY"].update({"equal": 160, "required": 160})
    counts = {"successful_full_transactions": 160, "real_rollout_steps": 320,
              "s10_pass": 160, "s10_to_next_s0_bridges": 159,
              "terminal_autoreset_events": 1,
              "actor_backward_total": 120, "actor_optimizer_step_total": 120,
              "critic_backward_total": 1600, "critic_optimizer_step_total": 1600,
              "valuenorm_update_total": 1600, "event_return_computations": 160,
              "stock_compute_returns": 0, "transaction_161_started": 0}
    final = {"exact_execution_counts": counts,
             "transactions": [{"transaction": {"real_audit": {
                 "actor_expected_backward": [[0, 5 if i <= 24 else 0], [1, 0], [2, 0]],
                 "actor_expected_step": [[0, 5 if i <= 24 else 0], [1, 0], [2, 0]],
                 "critic_expected_backward": 10, "critic_expected_step": 10,
                 "valuenorm_expected_update": 10}}} for i in range(1, 161)],
             "persistent_learner_identity": {
                 "object_ids_stable": True, "initial": {"valuenorm_object_id": 1},
                 "final": {"valuenorm_object_id": 1,
                    "actor_parameters_finite": True, "actor_optimizer_states_finite": True,
                    "critic_parameters_finite": True, "critic_optimizer_state_finite": True,
                    "valuenorm_state_finite": True, "gradients_clean": True}}}
    run_id = "re6-r3-synthetic-normalizer-fixture"
    raw = {"source_phase": PHASE, "run_id": run_id, "worker_pid": os.getpid(),
           "transactions": tx, "bridges": bridges, "progress": progress,
           "initial_step": initial_step,
           "terminal": terminal,
           "immutability": [{"transaction_index": i, "equal": True} for i in range(1, 161)],
           "actor_reconciliation": [{"transaction_index": i, "exact_match": True,
                                     "faults": 0} for i in range(1, 161)],
           "training_metrics": [{"transaction_index": i, "finite": True}
                                for i in range(1, 161)],
           "final": final, "witnesses": raw_witness,
           "partial_update": False, "route_poisoned": False,
           "checkpoint_io_count": 0, "public_activation_count": 0,
           "evaluation_playback_count": 0,
           "summary_claims": {"transaction_count": 160, "physical_transitions": 320,
                              "production_s10": 160, "bridge_count": 159,
                              "task_completed_count": 1, "coverage_max": 2,
                              "terminal_autoreset_count": 1,
                              "w2e_candidate_count": selected["candidate_count"],
                              "w2e_valid_count": selected["valid_count"]}}
    pw = {"contract_version": PPQ.PW_VERSION, "run_id": run_id,
          "transaction_count": 160, "critic_actual": 6560,
          "actor_factor_actual": 640, "missing_count": 0,
          "duplicate_count": 0, "order_fault_count": 0,
          "digest_fault_count": 0, "temp_residue_count": 0}
    return raw, lambda: pw


def normalized(raw: dict[str, Any], pw_verify: Any) -> dict[str, Any]:
    return NORM.normalize(raw, expected_phase=PHASE, config=CONFIG,
                          w2_selector=W2E.reconcile, pw_verify=pw_verify)


def _pw_files_verifier(root: Path, run_id: str) -> dict[str, Any]:
    critic = actor = 0
    for tx_id in range(1, CONFIG["expected_transaction_count"] + 1):
        critic += len(PW.verify_transaction(root, run_id=run_id, tx_id=tx_id,
                                            side="critic", planned_count=41))
        actor += len(PW.verify_transaction(root, run_id=run_id, tx_id=tx_id,
                                           side="actor", planned_count=4))
    return {"contract_version": PPQ.PW_VERSION, "run_id": run_id,
            "transaction_count": CONFIG["expected_transaction_count"],
            "critic_actual": critic, "actor_factor_actual": actor,
            "missing_count": 0, "duplicate_count": 0, "order_fault_count": 0,
            "digest_fault_count": 0, "temp_residue_count": 0}


def _synthetic_pw_records(root: Path, run_id: str) -> Any:
    for tx_id in range(1, CONFIG["expected_transaction_count"] + 1):
        for side, planned in (("critic", 41), ("actor", 4)):
            for sequence in range(1, planned + 1):
                stage = "CRITIC_PROGRESS" if side == "critic" else "ACTOR_FACTOR_PROGRESS"
                PW.write_record(root, run_id=run_id, tx_id=tx_id, stage=stage,
                                actor_or_critic=side, progress_sequence=sequence,
                                planned_sequence_count=planned,
                                payload={"run_id": run_id, "tx_id": tx_id,
                                         "stage": stage, "actor_or_critic": side,
                                         "synthetic_preflight": True})
    return lambda: _pw_files_verifier(root, run_id)


CANONICAL_NAMES = {
    "W1": "W1_cross_update_ownership.json",
    "W2E": "W2_multi_update_completion_v2.json",
    "W3": "W3_real_zero_dvm_actor.json",
    "W4": "W4_real_nonterminal_bootstrap.json",
    "W5": "W5_normal_horizon_terminal_autoreset.json",
    "W6": "W6_post_autoreset_training.json",
    "W7": "W7_runtime_p2_immutability.json",
}


def _destination(path: Path) -> Path:
    if path.name == "candidate_success_receipt_v2.json":
        return path.with_name("candidate_success_receipt.json")
    for key, filename in CANONICAL_NAMES.items():
        if path.name == f"{key}_canonical_success.json":
            return path.with_name(filename)
    return path


def _receipt_chain(evidence: dict[str, Any], pw_verify: Any,
                   output_dir: Path) -> dict[str, Any]:
    identity = V2TEST.identity(sha(SCHEMA))
    return PPQ.finalize_campaign(
        evidence, w2e_selector=W2E.reconcile, w2i_manifest=W2I,
        pw_reconcile=lambda _: pw_verify(), expected_phase=PHASE,
        config=CONFIG, identity=identity, production_sources=PRODUCTION,
        pw_helper_path=PW_HELPER,
        writer=lambda path, payload: PPQ.atomic_persist(_destination(path), payload),
        reader=lambda path: PPQ.readback(_destination(path)), output_dir=output_dir)


def full_success_preflight() -> dict[str, Any]:
    identities()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="b2_t4_re6_r3_ppq_v2_", dir=OUT) as temp:
        base = Path(temp)
        raw, _ = synthetic_raw()
        verifier = _synthetic_pw_records(base / "pw_records", raw["run_id"])
        converted = normalized(raw, verifier)
        result = _receipt_chain(converted["normalized"], verifier, base / "receipts")
        receipt_path = base / "receipts/candidate_success_receipt.json"
        require(receipt_path.is_file() and len(result["publication"]) == 7 and
                all((base / "receipts" / name).is_file() for name in CANONICAL_NAMES.values()),
                "FULL-SUCCESS-PREFLIGHT-PUBLICATION")
        return {"pass": True, "source_phase": PHASE,
                "normalizer_sha256": sha(NORMALIZER),
                "reviewed_pw_files_verified": 7200,
                "receipt_sha256": result["receipt_sha256"],
                "receipt_contract_version": result["receipt"]["contract_version"],
                "trace": result["trace"], "canonical_publication_count": 7,
                "w2e_candidate_count": result["w2e"]["candidate_count"],
                "w2e_valid_count": result["w2e"]["valid_count"]}


RAW_LEDGER_NAMES = {
    "transactions": "transaction",
    "bridges": "bridge",
    "progress": "lifecycle_task_progress",
    "terminal": "terminal_reconciliation",
    "immutability": "learner_runtime_immutability",
    "actor_reconciliation": "actor_evidence_reconciliation",
    "training_metrics": "training_metric",
}


def _runtime_rows(stem: str) -> list[dict[str, Any]]:
    path = OUT / f"{PREFIX.name}_{stem}_ledger.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line]


def actual_raw(engine: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    """Read only the fresh worker's retained ledgers and raw engine final file."""
    ledgers = {name: _runtime_rows(stem) for name, stem in RAW_LEDGER_NAMES.items()}
    final = json.loads((OUT / f"{PREFIX.name}_final_result.json").read_text(encoding="utf-8"))
    base = engine["RE3"]._RE3["_find_witnesses"](PREFIX)
    w2_input = NORM._selector_input(ledgers["progress"], ledgers["transactions"],
                                   ledgers["bridges"], CONFIG["expected_T"])
    selected = W2E.reconcile(w2_input)
    base["W2_MULTI_UPDATE_COMPLETION"] = {"pass": selected["pass"],
        "selected": selected["selected"], "candidate_count": selected["candidate_count"],
        "valid_count": selected["valid_count"]}
    return {"source_phase": PHASE, "run_id": run_id, "worker_pid": os.getpid(),
            **ledgers, "final": final, "witnesses": base,
            "partial_update": False, "route_poisoned": False,
            "checkpoint_io_count": 0, "public_activation_count": 0,
            "evaluation_playback_count": 0}


def _copy_qualified_ledgers() -> None:
    mapping = {
        "transaction_ledger.jsonl": "transaction",
        "bridge_ledger.jsonl": "bridge",
        "episode_update_timeline.jsonl": "episode_update_timeline",
        "lifecycle_task_progress.jsonl": "lifecycle_task_progress",
        "terminal_reconciliation.jsonl": "terminal_reconciliation",
        "nonterminal_bootstrap.jsonl": "nonterminal_bootstrap",
        "zero_dvm_actor_ledger.jsonl": "zero_dvm_actor",
        "runtime_p2_immutability.jsonl": "learner_runtime_immutability",
        "actor_evidence_reconciliation.jsonl": "actor_evidence_reconciliation",
        "training_metrics.jsonl": "training_metric",
        "rolling_health.jsonl": "rolling_health",
    }
    for target, stem in mapping.items():
        source = OUT / f"{PREFIX.name}_{stem}_ledger.jsonl"
        require(source.is_file(), "REQUIRED-RUNTIME-LEDGER-MISSING", str(source))
        data = source.read_bytes()
        destination = OUT / target
        require(not destination.exists(), "REQUIRED-RUNTIME-LEDGER-EXISTS", str(destination))
        with destination.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        require(destination.read_bytes() == data, "REQUIRED-RUNTIME-LEDGER-READBACK", target)


def formal_worker(run_id: str, receipt_path: Path) -> int:
    engine, _ = derived_runtime()
    normalizer_sha = json.loads((OUT / "runtime_normalizer_identity.json").read_text(
        encoding="utf-8"))["sha256"]
    payload = dict(engine["_base_payload"](run_id, worker_pid=os.getpid()))
    payload.update({"schema_version": "b2_t4_re6_r3_worker_receipt_v1", "phase": PHASE,
                    "normalizer_sha256": normalizer_sha,
                    "ppq_v2_receipt_sha256": None, "normalization_status": "NOT_STARTED"})
    app = None
    resources: dict[str, Any] = {}
    checkpoints_dir = None
    try:
        payload["failure_stage"] = "pre_AppLauncher_authority"
        require(sha(NORMALIZER) == normalizer_sha, "FROZEN-NORMALIZER-DRIFT")
        for name in ("re6_r3_static_authority.json", "re6_r3_runner_readiness_replay.json",
                     "re6_r3_preflight_summary.json", "filesystem_precondition.json",
                     "re6_r3_progress_persistence_binding.json", "full_success_path_preflight.json"):
            require((OUT / name).is_file(), "FORMAL-PREFLIGHT-ARTIFACT-MISSING", name)
        require(not engine["_module_contamination"](), "PRE-APPLAUNCHER-CONTAMINATION")
        static = json.loads((OUT / "re6_r3_static_authority.json").read_text(encoding="utf-8"))
        readiness = json.loads((OUT / "re6_r3_runner_readiness_replay.json").read_text(encoding="utf-8"))
        require(static["pass"] and readiness["pass"] and
                static["hashes"]["re6_r3_runner"] == sha(Path(__file__)) and
                json.loads((OUT / "full_success_path_preflight.json").read_text(
                    encoding="utf-8"))["pass"], "FORMAL-SOURCE-OR-PREFLIGHT-DRIFT")
        require(json.loads((OUT / "filesystem_precondition.json").read_text(
            encoding="utf-8"))["qualification_pass"], "FORMAL-FILESYSTEM-PRECONDITION")
        payload["source_authority_digest"] = sha(OUT / "re6_r3_static_authority.json")
        payload["filesystem_precondition_digest"] = sha(OUT / "filesystem_precondition.json")
        payload["failure_stage"] = "cuda_cublas_probe"
        cuda = engine["_cuda_probe"]()
        payload.update({"cuda_probe_pass": True, "cuda_probe_count": 1})
        write("cuda_cublas_readiness.json", cuda)
        payload["failure_stage"] = "AppLauncher"
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher
        launcher = AppLauncher(headless=True, device="cuda:0", enable_cameras=False,
                               livestream=0, xr=False, experience="")
        app = launcher.app
        payload["app_launcher_started"] = True
        payload["failure_stage"] = "canonical_registration_and_entry_point"
        import gymnasium as gym
        from gymnasium.envs.registration import load_env_creator
        import isaaclab_tasks  # noqa: F401
        package = importlib.import_module(engine["PACKAGE_NAME"])
        defining = importlib.import_module(engine["DEFINING_MODULE"])
        spec = gym.spec(engine["ENV_ID"])
        resolved = load_env_creator(spec.entry_point)
        require(spec.entry_point == engine["ENTRY_POINT"] and
                resolved is defining.ScanMobileManipulatorEnv and
                resolved is package.ScanMobileManipulatorEnv,
                "ENVIRONMENT-ENTRY-POINT-REGRESSION")
        payload["entry_point_resolution_pass"] = True
        payload["failure_stage"] = "training_engine_setup"
        re3 = engine["RE3"]
        runtime = re3._RE3["_INNER"]
        bound = engine["BINDING"].bind_progress(runtime, re3._RE3["_qualified_re3_source"]())
        require(bound == json.loads((OUT / "re6_r3_progress_persistence_binding.json").read_text(
            encoding="utf-8")), "FORMAL-PROGRESS-BINDING-DRIFT")
        runtime["_re3_canonical_termination_reason"] = re3._load_canonical_termination_reason()
        resources["repository_authority"] = runtime["SINGLE"]._repository_authority()
        resources["qualified_source_identity"] = re3._RE3["_source_identity"]()
        resources["_re5_pw_root"] = str(OUT / "pw_records")
        resources["_re5_run_id"] = run_id
        resources["_re5_after_tx"] = engine["_after_tx_pw_reconciliation"]
        resources["_re5_tx130_comparison"] = engine["_tx130_comparison"]
        checkpoints_dir = tempfile.TemporaryDirectory(prefix="b2_t4_re6_r3_worker_")
        checkpoints = runtime["V2"].Checkpoints(Path(checkpoints_dir.name) /
                                                 "diagnostic_checkpoints.json")
        config = {"environment": engine["ENV_ID"], "profile": "event_gated_local_mrta",
                  "device": "cuda:0", "T": 2, "E": 2, "M": 3, "N": 12,
                  "actor_epochs": 5, "actor_minibatches": 2,
                  "critic_epochs": 5, "critic_minibatches": 2,
                  "ValueNorm": True, "fixed_order": False,
                  "episode_length_s": 30.0, "max_episode_length": 300,
                  "control_step_seconds": 0.1, "run_id": run_id,
                  "worker_pid": os.getpid()}
        payload["config_authority_digest"] = PPQ.digest(config)
        write("process_config_authority.json", {"phase": PHASE, "config": config,
              "config_sha256": payload["config_authority_digest"], "pass": True})
        payload["failure_stage"] = "tx001_tx160"
        evidence = runtime["_run_repeated_smoke"](checkpoints, resources,
                                                    artifact_prefix=PREFIX)
        require(evidence.get("status") == "passed", "TRAINING-ENGINE-RESULT",
                evidence.get("classification"))
        payload["failure_stage"] = "runtime_normalization"
        _copy_qualified_ledgers()
        raw = actual_raw(engine, run_id)
        pw_campaign = engine["_campaign_pw_reconciliation"](run_id)
        verifier = lambda: _generic_pw(engine["_campaign_pw_reconciliation"](run_id), run_id)
        converted = normalized(raw, verifier)
        payload["normalization_status"] = "PASS"
        write("runtime_normalization_result.json", converted)
        write("runtime_normalization_crosscheck.json",
              {"pass": converted["crosscheck_pass"], "derived": converted["derived"],
               "raw_sources": converted["raw_sources"]})
        write("w2e_candidate_inventory.json", converted["w2e"])
        write("w2e_selected_witness.json", converted["w2e"]["selected"])
        payload["failure_stage"] = "ppq_v2_success_receipt"
        success = _receipt_chain(converted["normalized"], verifier, OUT)
        payload["ppq_v2_receipt_sha256"] = success["receipt_sha256"]
        write("success_receipt_readback_validation.json",
              {"pass": True, "receipt_sha256": success["receipt_sha256"],
               "schema_validated_twice": True})
        write("success_publication_order.json",
              {"pass": True, "trace": success["trace"],
               "published": [CANONICAL_NAMES[name] for name in PPQ.WITNESSES]})
        payload.update({"status": "success", "classification":
            "PHASE-B2-T4-RE6-R3-PPQ-V2-BOUND-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW",
            "failure_stage": "success_receipt_pre_env_close", "partial_update": False,
            "route_poisoned": False, "irreversible_mutation_occurred": True,
            "production_s10": converted["derived"]["production_s10"],
            "ledger_qualified_transactions": converted["derived"]["transaction_count"],
            "physical_transitions": converted["derived"]["physical_transitions"],
            "bridges": converted["derived"]["bridge_count"],
            "pw_progress": pw_campaign, "normalization_crosscheck_pass": True,
            "witnesses": {name: {"pass": True} for name in PPQ.WITNESSES}})
    except BaseException as exc:
        mutation = engine["_irreversible_mutation_observed"](resources)
        route = resources.get("route")
        if mutation and route is not None:
            route._poisoned = True
        payload.update({"status": "failure", "classification":
            "PHASE-B2-T4-RE6-R3-STOP-FORMAL-WORKER-FAILURE",
            "exception_type": type(exc).__name__, "exception_message": str(exc),
            "traceback_tail": traceback.format_exc()[-20000:],
            "current_tx": int(resources.get("active_transaction", 1)),
            "runtime_counters": {key: resources.get(key, 0) for key in
                ("environment_constructions", "real_resets", "real_rollout_steps",
                 "terminal_autoreset_events", "completed_transactions")},
            "partial_update": mutation, "route_poisoned": mutation,
            "irreversible_mutation_occurred": mutation})
        try:
            write("failure_receipt.json", {"failure_stage": payload["failure_stage"],
                 "reason": str(exc), "current_tx": payload["current_tx"],
                 "runtime_counters": payload["runtime_counters"],
                 "normalization_status": payload["normalization_status"],
                 "witnesses": payload["witnesses"], "mutation_occurred": mutation,
                 "partial_update": mutation, "route_poisoned": mutation,
                 "source_identities": identities()})
        except BaseException as receipt_exc:
            payload["failure_receipt_error"] = f"{type(receipt_exc).__name__}:{receipt_exc}"
    finally:
        try:
            engine["_persist_receipt"](receipt_path, payload)
        except BaseException as exc:
            payload.update({"status": "failure", "classification":
                "PHASE-B2-T4-RE6-R3-STOP-WORKER-RECEIPT-PERSISTENCE",
                "receipt_error": str(exc)})
        guard = resources.get("guard")
        if guard is not None:
            payload["env_close_attempted"] = True
            try:
                guard.close()
                payload["env_close_pass"] = True
            except BaseException as exc:
                payload.update({"status": "failure", "env_close_pass": False,
                    "classification": "PHASE-B2-T4-RE6-R3-STOP-ENVIRONMENT-CLOSE",
                    "exception_message": str(exc)})
        if app is not None:
            payload["app_close_invoked"] = True
        try:
            engine["_persist_receipt"](receipt_path, payload)
        except BaseException as exc:
            payload.update({"status": "failure", "classification":
                "PHASE-B2-T4-RE6-R3-STOP-WORKER-RECEIPT-PERSISTENCE",
                "receipt_error": str(exc)})
        if checkpoints_dir is not None:
            checkpoints_dir.cleanup()
        if app is not None:
            app.close()
    return 0 if payload["status"] == "success" else 20


def formal_supervisor(timeout_seconds: int) -> dict[str, Any]:
    engine, _ = derived_runtime()
    targets = ("formal_worker_receipt.json", "formal_supervisor_result.json",
               "process_quiescence.json", "final_result.json",
               "candidate_success_receipt.json")
    require(not any((OUT / name).exists() for name in targets) and
            not (OUT / "pw_records").exists(), "STALE-FORMAL-TARGET")
    for name in ("runner_readiness_replay.json", "full_success_path_preflight.json",
                 "runtime_normalizer_identity.json"):
        require((OUT / name).is_file(), "FORMAL-READINESS-MISSING", name)
    ready = json.loads((OUT / "runner_readiness_replay.json").read_text(encoding="utf-8"))
    require(ready["pass"] and ready["harness_sha256"] == sha(Path(__file__)) and
            ready["normalizer_sha256"] == sha(NORMALIZER), "FORMAL-RUNNER-DRIFT")
    run_id = f"b2-t4-re6-r3-20260920-formal01-{uuid.uuid4().hex}"
    receipt_path = OUT / "formal_worker_receipt.json"
    command = (sys.executable, "-u", str(Path(__file__).resolve()), "--mode", "formal-worker",
               "--run-id", run_id, "--receipt", str(receipt_path))
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    pid_active, tasklist_output = engine["_tasklist_pid_active"](process.pid)
    matching = engine["_matching_workers"]()
    envelope, receipt_error = engine["_load_receipt"](receipt_path)
    payload = envelope.get("payload", {}) if isinstance(envelope, dict) else {}
    envelope_valid = (receipt_error is None and isinstance(payload, dict) and
        envelope.get("payload_sha256") == engine["_sha_bytes"](
            engine["_canonical_bytes"](payload)))
    candidate = OUT / "candidate_success_receipt.json"
    candidate_receipt = None
    candidate_error = None
    if candidate.is_file():
        try:
            candidate_receipt, digest = PPQ.readback(candidate)
            PPQ.validate_receipt(candidate_receipt, expected_phase=PHASE,
                                 identity=V2TEST.identity(sha(SCHEMA)), config=CONFIG)
            require(digest == payload.get("ppq_v2_receipt_sha256"),
                    "FORMAL-CANDIDATE-DIGEST-MISMATCH")
        except BaseException as exc:
            candidate_error = f"{type(exc).__name__}:{exc}"
    else:
        candidate_error = "missing candidate success receipt"
    layer_a_checks = {
        "worker_receipt_envelope": envelope_valid,
        "worker_source_phase": payload.get("phase") == PHASE,
        "worker_identity": payload.get("run_id") == run_id and
                           payload.get("worker_pid") == process.pid,
        "worker_status_success": payload.get("status") == "success",
        "normalization_pass": payload.get("normalization_status") == "PASS" and
                              payload.get("normalization_crosscheck_pass") is True,
        "frozen_normalizer": payload.get("normalizer_sha256") == sha(NORMALIZER),
        "ppq_v2_candidate_schema_digest": candidate_receipt is not None and
                                           candidate_error is None,
        "env_close": payload.get("env_close_pass") is True,
        "app_close_invoked": payload.get("app_close_invoked") is True,
        "receipt_before_app_close": payload.get("receipt_written_before_app_close") is True and
                                    payload.get("receipt_fsync_pass") is True and
                                    payload.get("receipt_readback_pass") is True,
        "route_health": payload.get("partial_update") is False and
                        payload.get("route_poisoned") is False,
        "counts": payload.get("physical_transitions") == 320 and
                  payload.get("production_s10") == 160 and
                  payload.get("ledger_qualified_transactions") == 160 and
                  payload.get("bridges") == 159,
        "canonical_witnesses": all((OUT / name).is_file() for name in
                                   CANONICAL_NAMES.values()),
    }
    layer_a = {"pass": all(layer_a_checks.values()), "checks": layer_a_checks,
               "candidate_error": candidate_error,
               "candidate_receipt_sha256": sha(candidate) if candidate.is_file() else None,
               "worker_receipt_error": receipt_error}
    process_evidence = {"worker_wait_completed": process.poll() is not None,
                        "timed_out": timed_out, "worker_return_code": process.returncode,
                        "worker_pid_active": pid_active,
                        "matching_formal_worker_pids": matching}
    predicates = engine["EPQ"]._process_predicates(process_evidence)
    layer_b = {"pass": all(predicates.values()), "hard_predicates": predicates,
               "process_evidence": process_evidence,
               "shutdown_marker_observed": engine["EPQ"].SHUTDOWN_MARKER in
                   (stdout + stderr), "shutdown_marker_authoritative": False,
               "tasklist_output": tasklist_output,
               "nonclaims": ["SimulationApp.close returned normally to Python",
                             "every internal Kit callback executed"]}
    passed = layer_a["pass"] and layer_b["pass"]
    mutation = bool(payload.get("irreversible_mutation_occurred") or
                    payload.get("partial_update") or
                    any(OUT.glob(f"{PREFIX.name}_tx*_pre_mutation.json")))
    classification = ("PHASE-B2-T4-RE6-R3-PPQ-V2-BOUND-NORMAL-HORIZON-LEARNED-TRAINING-"
        "INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW" if passed else
        ("PHASE-B2-T4-RE6-R3-STOP-POISONED-RETAINED" if mutation else
         "PHASE-B2-T4-RE6-R3-STOP-PRE-MUTATION"))
    result = {"phase": PHASE, "status": "passed" if passed else "stopped",
              "classification": classification, "run_id": run_id,
              "formal_supervisors": 1, "formal_workers": 1, "formal_retries": 0,
              "worker_pid": process.pid, "worker_return_code": process.returncode,
              "layer_a": layer_a, "layer_b": layer_b,
              "partial_update": mutation and not passed,
              "route_poisoned": mutation and not passed,
              "worker_stdout_tail": stdout[-24000:],
              "worker_stderr_tail": stderr[-24000:]}
    write("process_quiescence.json", layer_b)
    write("formal_supervisor_result.json", result)
    write("final_result.json", {"classification": classification,
          "layer_a_pass": layer_a["pass"], "layer_b_pass": layer_b["pass"],
          "formal_supervisors": 1, "formal_workers": 1, "formal_retries": 0,
          "partial_update": result["partial_update"],
          "route_poisoned": result["route_poisoned"],
          "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0})
    require(passed, classification, result)
    return result


def preflight() -> dict[str, Any]:
    ids = identities()
    engine, derivation = derived_runtime()
    required_keys = ("RE3", "BINDING", "EPQ", "_run_repeated_smoke",
                     "_after_tx_pw_reconciliation", "_tx130_comparison",
                     "_campaign_pw_reconciliation", "_persist_receipt")
    missing = [key for key in required_keys if key not in engine and
               key not in engine["RE3"]._RE3["_INNER"]]
    require(not missing, "HIDDEN-RUNTIME-DEPENDENCY", missing)
    inherited = engine["run_preflight"]()
    historical, historical_pw = historical_raw()
    replay = normalized(historical, historical_pw)
    selected = replay["w2e"]["selected"]
    expected_selected = {"env_id": 1, "robot_id": 1, "task_id": 10,
        "claim_tx": 12, "claim_physical_step": 23,
        "completion_tx": 15, "completion_physical_step": 30,
        "reopen_tx": 16, "reopen_physical_step": 31}
    require(all(selected[key] == value for key, value in expected_selected.items()) and
            replay["derived"]["w2e_candidate_count"] == 29 and
            replay["derived"]["w2e_valid_count"] == 12 and
            replay["derived"]["task_completed_count"] == 22 and
            replay["derived"]["coverage_max"] == 11 and
            replay["derived"]["terminal_autoreset_count"] == 2,
            "HISTORICAL-NORMALIZATION-REPLAY", replay["derived"])
    synthetic, synthetic_pw = synthetic_raw()
    fresh = normalized(synthetic, synthetic_pw)
    negatives = negative_matrix(synthetic, synthetic_pw)
    require(fresh["crosscheck_pass"] and negatives["pass"] and
            fresh["derived"]["w2e_candidate_count"] != 29 and
            fresh["derived"]["task_completed_count"] != 22 and
            fresh["derived"]["coverage_max"] != 11 and
            fresh["derived"]["terminal_autoreset_count"] != 2,
            "SYNTHETIC-NORMALIZATION-NOT-DECOUPLED")
    full = full_success_preflight()
    normalizer_identity = {"sha256": sha(NORMALIZER),
                           "bytes": NORMALIZER.stat().st_size,
                           "path": str(NORMALIZER.relative_to(ROOT)),
                           "historical_replay_pass": True,
                           "synthetic_replay_pass": True,
                           "negative_stop": negatives["actual_stop"],
                           "unexpected_pass": negatives["unexpected_pass"],
                           "frozen_before_formal": True}
    source_map = {
        "transaction_count": "transaction_ledger.jsonl row count",
        "physical_transitions": "lifecycle_task_progress.jsonl steps[*]",
        "S10_count": "transaction_ledger.jsonl s7_s8_s9_s10[3]",
        "bridge_count": "bridge_ledger.jsonl row count and update IDs",
        "W2_candidates_valid_selected": "reviewed W2E.reconcile on retained lifecycle and bridge rows",
        "TASK_COMPLETED": "lifecycle_task_progress.jsonl steps[*].events",
        "completion_delta": "lifecycle_task_progress.jsonl steps[*].state_rows completion_count",
        "max_coverage": "lifecycle_task_progress.jsonl steps[*].state_rows coverage_count",
        "terminal_count": "terminal_reconciliation.jsonl reason_counts and observed_keys",
        "post_autoreset_training": "terminal row plus P2 generation and qualified next transaction",
        "PW_actual_counts": "reviewed PW.verify_transaction over immutable pw_records",
        "actor_critic_valuenorm": "transaction ledger plus raw engine final real_audit",
        "event_returns": "transaction_ledger.jsonl event_returns",
        "stock_compute_returns": "transaction_ledger.jsonl stock_compute_returns"}
    dependency = {"pass": True, "missing_required_engine_keys": missing,
        "hidden_required_engine_key_count": len(missing),
        "forbidden_missing_writer_key_authority_references": 0,
        "historical_fixed_value_dependencies": 0,
        "runtime_explicit_source_derivation": derivation,
        "ppq_success_route": "normalizer -> reviewed PPQ-V2 finalize_campaign",
        "old_RE5_receipt_route_called": False}
    status = subprocess.run(("git", "status", "--porcelain=v1", "-uall"),
        cwd=ROOT, capture_output=True, check=True).stdout
    staged = subprocess.run(("git", "diff", "--cached", "--name-status"),
        cwd=ROOT, capture_output=True, check=True).stdout
    repository = {"branch": subprocess.check_output(("git", "branch", "--show-current"),
                    cwd=ROOT, text=True).strip(),
                  "head": subprocess.check_output(("git", "rev-parse", "HEAD"),
                    cwd=ROOT, text=True).strip(),
                  "porcelain_rows": len(status.splitlines()),
                  "porcelain_sha256": hashlib.sha256(status).hexdigest(),
                  "staged_rows": len(staged.splitlines()),
                  "staged_sha256": hashlib.sha256(staged).hexdigest(),
                  "git_add_commit_push_this_phase": [0, 0, 0]}
    write("repository_authority.json", repository)
    write("static_authority.json", {"pass": inherited["static_authority_pass"],
          "source_derivation": derivation, "inherited_preflight":
          "re6_r3_preflight_summary.json"})
    write("reviewed_identity_gate.json", ids)
    write("runtime_normalization_source_map.json", source_map)
    write("runtime_normalizer_historical_replay.json",
          {"pass": True, "derived": replay["derived"], "selected": selected,
           "historical_classification_unchanged": "STOP / POISONED / NOT QUALIFIED"})
    write("runtime_normalizer_synthetic_replay.json",
          {"pass": True, "derived": fresh["derived"],
           "selected": fresh["w2e"]["selected"], "PPQ_V2_preflight_pass": full["pass"]})
    write("runtime_normalizer_negative_matrix.json", negatives)
    write("runtime_normalizer_identity.json", normalizer_identity)
    write("re6_r2_re6_r3_gate_equivalence.json",
          {"pass": True, "RE6_R2_formal_attempts": 0,
           "unchanged_runtime_gates": "source-derived RE5/RE6-R1 transaction/NR/SR/ZD/PW/W1-W7/learner/EP-Q",
           "intentional_changes": ["PPQ-v1 -> reviewed PPQ-V2",
                                   "unqualified normalization -> frozen R3 normalizer"],
           "derived_runtime": derivation})
    write("success_path_dependency_audit.json", dependency)
    write("full_success_path_preflight.json", full)
    return {"pass": True, "historical": replay["derived"],
            "synthetic": fresh["derived"], "negative_stop": negatives["actual_stop"],
            "full_success_preflight": full, "normalizer_sha256": normalizer_identity["sha256"]}


def readiness() -> dict[str, Any]:
    require((OUT / "runtime_normalizer_identity.json").is_file() and
            (OUT / "full_success_path_preflight.json").is_file(),
            "READINESS-PREFLIGHT-MISSING")
    engine, _ = derived_runtime()
    inherited = engine["run_readiness"]()
    frozen = json.loads((OUT / "runtime_normalizer_identity.json").read_text(
        encoding="utf-8"))
    full = json.loads((OUT / "full_success_path_preflight.json").read_text(
        encoding="utf-8"))
    require(inherited["pass"] and full["pass"] and frozen["sha256"] == sha(NORMALIZER),
            "FINAL-RUNNER-READINESS-FAIL")
    result = {"pass": True, "phase": PHASE, "replay_count": 1,
              "harness_sha256": sha(Path(__file__)),
              "normalizer_sha256": sha(NORMALIZER),
              "reviewed_PPQ_V2": True, "reviewed_W2E": True, "reviewed_PW": True,
              "SR_ZD_W1_W7_inherited": inherited["pass"],
              "full_success_receipt_readback_publication": full["pass"],
              "failure_receipt_contract": True,
              "EP_Q_Layer_B": inherited["G_EP_Q_Layer_B_synthetic"]["pass"],
              "AppLauncher": 0, "formal_workers": 0}
    write("runner_readiness_replay.json", result)
    return result


def negative_matrix(base: dict[str, Any], pw: Any) -> dict[str, Any]:
    cases = [
        ("missing transaction", "transactions.pop", 20),
        ("duplicate transaction", "transactions.19.transaction_index", 19),
        ("missing bridge", "bridges.pop", 20),
        ("bridge discontinuity", "bridges.19.to_update_id", "wrong"),
        ("missing lifecycle step", "progress.19.steps.pop", 0),
        ("generation inconsistency", "progress.1.steps.0.state_rows.0.episode_generation", 99),
        ("completed summary mismatch", "summary_claims.task_completed_count", 2),
        ("coverage summary mismatch", "summary_claims.coverage_max", 3),
        ("terminal summary mismatch", "summary_claims.terminal_autoreset_count", 2),
        ("false post-autoreset claim", "progress.150.steps.0.state_rows.0.episode_generation", 0),
        ("PW summary/verifier mismatch", "pw", "wrong"),
        ("learner counts mismatch", "transactions.0.critic_backward", 9),
        ("W2 candidate manual mismatch", "witnesses.W2_MULTI_UPDATE_COMPLETION.candidate_count", 99),
        ("selected W2 override", "witnesses.W2_MULTI_UPDATE_COMPLETION.selected.env_id", 99),
    ]
    rows = []
    for label, path, replacement in cases:
        raw = copy.deepcopy(base)
        verifier = pw
        if path == "pw":
            verifier = lambda: {**pw(), "critic_actual": 6559}
        elif path.endswith(".pop"):
            keys = path.split(".")
            node = raw
            for key in keys[:-1]:
                node = node[int(key)] if isinstance(node, list) else node[key]
            node.pop(replacement)
        else:
            V2TEST.set_path(raw, path, replacement)
        try:
            normalized(raw, verifier)
            rows.append({"case": label, "expected": "STOP", "actual": "UNEXPECTED_PASS"})
        except (NORM.NormalizationStop, KeyError, IndexError, TypeError, ValueError) as exc:
            rows.append({"case": label, "expected": "STOP", "actual": "STOP",
                         "reason": f"{type(exc).__name__}:{exc}"})
    return {"case_count": len(rows), "actual_stop": sum(r["actual"] == "STOP" for r in rows),
            "unexpected_pass": sum(r["actual"] != "STOP" for r in rows),
            "pass": all(r["actual"] == "STOP" for r in rows), "cases": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?")
    parser.add_argument("--mode", dest="flag_mode")
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=10800)
    args = parser.parse_args()
    mode = args.flag_mode or args.mode
    if mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")
        engine, _ = derived_runtime()
        print(json.dumps(engine["_run_sr_current_zd"](args.artifact_dir)))
    elif mode == "preflight":
        print(json.dumps(preflight(), default=str))
    elif mode == "readiness":
        print(json.dumps(readiness(), default=str))
    elif mode == "formal-worker":
        require(bool(args.run_id) and args.receipt is not None,
                "FORMAL-WORKER-ARGS")
        return formal_worker(args.run_id, args.receipt.resolve())
    elif mode == "formal-supervisor":
        print(json.dumps(formal_supervisor(args.timeout_seconds), default=str))
    elif mode == "normalizer-check":
        ids = identities()
        historical, historical_pw = historical_raw()
        h = normalized(historical, historical_pw)
        synthetic, synthetic_pw = synthetic_raw()
        s = normalized(synthetic, synthetic_pw)
        n = negative_matrix(synthetic, synthetic_pw)
        require(h["crosscheck_pass"] and s["crosscheck_pass"] and n["pass"],
                "RUNTIME-NORMALIZATION-NOT-QUALIFIED")
        print(json.dumps({"pass": True, "identity": ids["pass"],
                          "historical": {k: h["derived"][k] for k in
                              ("transaction_count", "physical_transitions", "task_completed_count",
                               "coverage_max", "terminal_autoreset_count",
                               "w2e_candidate_count", "w2e_valid_count")},
                          "synthetic": {k: s["derived"][k] for k in
                              ("transaction_count", "physical_transitions", "task_completed_count",
                               "coverage_max", "terminal_autoreset_count",
                               "w2e_candidate_count", "w2e_valid_count")},
                          "negative_stop": n["actual_stop"],
                          "unexpected_pass": n["unexpected_pass"]}))
    else:
        parser.error(f"unknown mode: {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
