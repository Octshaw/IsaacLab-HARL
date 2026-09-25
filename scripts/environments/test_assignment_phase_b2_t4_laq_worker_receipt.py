"""Offline B2-T4-LAQ qualification; no Isaac, CUDA, environment or learner imports.

Modes are intentionally separated.  ``qualify`` can be rerun while developing;
``final-positive`` and ``final-negative`` are single-use frozen evidence modes.
"""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DATE = SCAN / "AgentRead/202609/20260921"
R3 = SCAN / "AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"
R1 = SCAN / "AgentRead/202609/20260920/b2_t4_re6_r1_artifacts"
R2 = SCAN / "AgentRead/202609/20260920/b2_t4_re6_r2_artifacts"
OUT = DATE / "b2_t4_laq_artifacts"
PPQ_SCHEMA = SCAN / "AgentRead/202609/20260920/b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json"
PPQ_HELPER = HERE / "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py"
NORMALIZER = HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py"
RE5 = HERE / "test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py"
R3_HARNESS = HERE / "test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration.py"
LAQ = HERE / "_assignment_phase_b2_t4_laq_worker_receipt.py"
sys.path.insert(0, str(HERE))
import _assignment_phase_b2_t4_laq_worker_receipt as L  # noqa: E402
import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as PPQ  # noqa: E402

CONFIG = {"expected_transaction_count": 160, "expected_T": 2,
          "critic_records_per_tx": 41, "actor_factor_records_per_tx": 4}
PRODUCTION = {
    "full_transaction": SCAN / "assignment_event_training_full_transaction.py",
    "real_isaac_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "environment": SCAN / "scan_mobile_manipulator_env.py",
}
PROTECTED = {
    **{f"production_{name}": path for name, path in PRODUCTION.items()},
    "w2e": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i": SCAN / "AgentRead/202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw": HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "ppq_v1_helper": HERE / "_assignment_phase_b2_t4_ppq_postprocess.py",
    "ppq_v1_schema": SCAN / "AgentRead/202609/20260920/b2_t4_ppq_artifacts/success_receipt_schema.json",
    "ppq_v2_helper": PPQ_HELPER,
    "ppq_v2_runner": HERE / "test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract.py",
    "ppq_v2_schema": PPQ_SCHEMA,
    "r3_normalizer": NORMALIZER,
    "r3_harness": R3_HARNESS,
}
WITNESS_FILES = {
    "W1": "W1_cross_update_ownership.json",
    "W2E": "W2_multi_update_completion_v2.json",
    "W3": "W3_real_zero_dvm_actor.json",
    "W4": "W4_real_nonterminal_bootstrap.json",
    "W5": "W5_normal_horizon_terminal_autoreset.json",
    "W6": "W6_post_autoreset_training.json",
    "W7": "W7_runtime_p2_immutability.json",
}


def sha(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def read(name: str) -> Any:
    return json.loads((R3 / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict[str, Any]]:
    with (R3 / name).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(name: str, value: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def expected_identity() -> dict[str, str]:
    return {
        "ppq_v2_helper_sha256": sha(PPQ_HELPER),
        "ppq_v2_schema_sha256": sha(PPQ_SCHEMA),
        "production_identity_digest": PPQ.digest(
            {key: sha(path) for key, path in sorted(PRODUCTION.items())}),
        "config_identity_digest": PPQ.digest(CONFIG),
    }


def collect() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = json.loads(PPQ_SCHEMA.read_text(encoding="utf-8"))
    envelope = read("formal_worker_receipt.json")
    L.require(type(envelope) is dict and envelope.get("payload_sha256") ==
              L.canonical_sha(envelope.get("payload")), "ORIGINAL-ENVELOPE-DIGEST")
    candidate = read("candidate_success_receipt.json")
    readback = read("success_receipt_readback_validation.json")
    L.require(readback["pass"] is True and
              readback["receipt_sha256"] == sha(R3 / "candidate_success_receipt.json"),
              "PPQ-V2-READBACK-DIGEST")
    sources = {
        "raw_final": read("b2_t4_re6_r3_normal_horizon_20260920_formal01_final_result.json"),
        "ppq_v2_candidate": candidate,
        "ppq_v2_candidate_file_sha256": sha(R3 / "candidate_success_receipt.json"),
        "ppq_v2_readback": readback,
        "normalized": read("runtime_normalization_result.json"),
        "worker_handoff": envelope["payload"],
        "pw_verifier": read("pw_campaign_reconciliation.json"),
        "witnesses": {key: read(name) for key, name in WITNESS_FILES.items()},
        "w2e_result": read("W2_multi_update_completion_v2.json"),
        "transaction_rows": rows("transaction_ledger.jsonl"),
        "bridge_rows": rows("bridge_ledger.jsonl"),
        "lifecycle_rows": rows("lifecycle_task_progress.jsonl"),
        "terminal_rows": rows("terminal_reconciliation.jsonl"),
        "zero_dvm_rows": rows("zero_dvm_actor_ledger.jsonl"),
        "normalizer_sha256": sha(NORMALIZER),
    }
    context = {
        "ppq_schema": schema,
        "ppq_validator": PPQ.validate_receipt,
        "expected_phase": candidate["source_phase"],
        "expected_run_id": envelope["payload"]["run_id"],
        "expected_pid": sources["raw_final"]["process_id"],
        "expected_source_digest": sha(R3 / "re6_r3_static_authority.json"),
        "expected_config_digest": read("process_config_authority.json")["config_sha256"],
        "ppq_identity": expected_identity(),
        "ppq_config": CONFIG,
        "expected_normalizer_sha256": sha(NORMALIZER),
    }
    return sources, context, envelope


def supervision(receipt: Any, sources: dict[str, Any],
                context: dict[str, Any], layer_b: bool = True) -> dict[str, Any]:
    return L.adjudicate_supervisor(receipt, layer_b, raw_sources=sources, **context)


def source_map(schema: dict[str, Any]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for field in schema["required_fields"]:
        if field.startswith("w2") or field.startswith("W2"):
            authority = "reviewed W2E selector result / retained lifecycle, transaction and bridge ledgers"
        elif field.startswith("W"):
            authority = "canonical W1-W7 source witness artifact, cross-bound to PPQ-V2 candidate"
        elif field.startswith("pw_"):
            authority = "reviewed PW campaign verifier / immutable PW records"
        elif field.startswith(("actor_", "critic_", "valuenorm_", "valid_")):
            authority = "normalized learner evidence crosschecked to raw final and transaction ledger"
        elif field in ("task_completed_count", "completion_delta", "coverage_max"):
            authority = "lifecycle task-progress ledger / normalized derivation"
        elif field in ("terminal_autoreset_count", "post_autoreset_learned_transaction",
                       "terminal_reason_priority_pass"):
            authority = "terminal reconciliation and post-reset transaction ledgers"
        elif field in ("physical_transitions", "transaction_count", "production_s10",
                       "transaction_ledger_count", "bridge_count", "tx161_started"):
            authority = "raw engine exact counters / transaction and bridge ledgers"
        elif field in ("event_returns", "stock_compute_returns"):
            authority = "transaction ledger sums / raw engine exact counters"
        elif field.endswith("sha256") or field.endswith("digest") or field.endswith("version"):
            authority = "reviewed source bytes / PPQ-V2 contract / process config authority"
        elif field in ("partial_update", "route_poisoned", "campaign_status"):
            authority = "worker-local route state and reviewed PPQ-V2 candidate"
        else:
            authority = "reviewed PPQ-V2 normalized candidate, separately crosschecked to raw evidence"
        value[field] = {"authoritative_source": authority,
                        "projection": f"ppq_v2_candidate.{field}",
                        "crosscheck": "PPQ-V2 complete validator and raw-vs-receipt crosscheck"}
    extra = {
        "layer_a_contract_version": "LAQ versioned contract",
        "status": "worker-local success/failure state",
        "source_authority_digest": "raw re6_r3_static_authority.json bytes",
        "config_authority_digest": "process_config_authority.config_sha256",
        "filesystem_precondition_digest": "worker-local filesystem precondition identity",
        "ppq_v2_candidate_sha256": "PPQ-V2 candidate success receipt raw bytes and readback digest",
        "ppq_v2_readback_pass": "PPQ-V2 readback/schema/digest validation result",
        "cuda_probe_count": "worker-local CUDA probe counter",
        "cuda_probe_pass": "worker-local CUDA probe result",
        "app_launcher_count": "raw_final.exact_execution_counts.app_launcher_lifetimes",
        "app_launcher_started": "worker-local AppLauncher start result",
        "entry_point_resolution_pass": "worker-local canonical entry-point result",
        "environment_count": "raw_final.exact_execution_counts.environment_constructions",
        "initial_reset_count": "raw_final.exact_execution_counts.environment_resets",
        "persistent_learner_count": "raw_final.exact_execution_counts.distinct_learner_constructions",
        "S10_count": "raw_final.exact_execution_counts.s10_pass",
        "ledger_count": "transaction_ledger.jsonl row count",
        "event_returns_count": "raw_final.exact_execution_counts.event_return_computations",
        "stock_compute_returns_count": "raw_final.exact_execution_counts.stock_compute_returns",
        "TASK_COMPLETED_count": "lifecycle_task_progress.jsonl task_completed events",
        "max_coverage": "runtime_normalization_result.derived.coverage_max / P2 progress",
        "invalid_critic_class_count": "raw critic-step total minus valid class counts",
        "persistent_continuity_pass": "raw final persistent learner object IDs stable",
        "factor_audits_pass": "raw final per-transaction factor segment count and S10",
        "learner": "runtime_normalization_result.normalized.learner / raw engine counts",
        "contracts": "reviewed identity bytes plus NR/ZD/SR/bookkeeping/policy fault ledgers",
        "witnesses": "seven canonical W1-W7 source artifacts",
        "pw_progress": "reviewed PW campaign verifier result",
        "final_in_worker_quiescence_pass": "raw_final.final_read_only_quiescence_check.pass",
        "env_close_pass": "worker-local env.close handoff",
        "app_close_invoked": "worker-local pre-exit App close invocation",
        "receipt_written_before_app_close": "worker-local receipt publication order",
        "receipt_fsync_pass": "worker-local durable receipt writer",
        "receipt_readback_pass": "worker-local receipt readback",
    }
    for field, authority in extra.items():
        value[field] = {"authoritative_source": authority,
                        "projection": f"explicit source for {field}",
                        "crosscheck": "complete supervisor validator and raw-vs-receipt crosscheck"}
    L.require(set(value) == set(schema["required_fields"]) | set(L.EXTRA_TYPES),
              "SOURCE-MAP-INCOMPLETE")
    return value


# Every key is extracted from RE5 _layer_a_validate's source AST below.  The
# mapping is explicit so a newly discovered inherited check makes LAQ STOP.
LEGACY_TO_V2 = {
    "receipt_present": "receipt_object",
    "receipt_parse_valid": "receipt_object",
    "envelope_schema": "envelope_schema",
    "payload_schema": "layer_a_contract_version",
    "payload_digest": "payload_digest",
    "phase": "complete_ppq_v2_validator",
    "run_id": "run_id",
    "worker_pid": "worker_pid",
    "source_authority": "source_authority",
    "config_authority": "config_authority",
    "pw_helper_identity": "complete_ppq_v2_validator",
    "filesystem_authority": "filesystem_authority",
    "status_success": "status_success",
    "cuda_probe": "cuda_probe",
    "app_launcher": "app_launcher",
    "entry_point": "entry_point",
    "environment": "environment",
    "reset": "reset",
    "learner_once": "learner_once",
    "targets": "complete_ppq_v2_validator",
    "completion": "complete_ppq_v2_validator+s10+ledger",
    "pw_progress": "pw_map_values",
    "w1_w6": "witness_statuses",
    "w7": "w7_count+witness_statuses",
    "task_progress": "complete_ppq_v2_validator+task_direct",
    "persistent_learner": "persistent_learner",
    "actor_plans": "learner_map_values+complete_ppq_v2_validator",
    "factor": "factor",
    "critic": "learner_map_values+complete_ppq_v2_validator",
    "valuenorm": "learner_map_values+complete_ppq_v2_validator",
    "adam": "learner_map_values+complete_ppq_v2_validator",
    "numerical": "learner_map_values+complete_ppq_v2_validator",
    "contracts": "contract_identities+contract_faults",
    "returns": "returns_direct",
    "route": "route_health+worker_quiescence",
    "forbidden": "forbidden_actions",
    "receipt_order": "receipt_order",
    "env_close": "env_close",
    "app_close_invoked": "app_close_invoked",
}


def historical_inventory(sources: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    tree = ast.parse(RE5.read_text(encoding="utf-8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_layer_a_validate")
    assignment = next(n for n in ast.walk(function) if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == "checks" for t in n.targets))
    assert isinstance(assignment.value, ast.Dict)
    legacy = {key.value: key.lineno for key in assignment.value.keys if isinstance(key, ast.Constant)}
    L.require(set(legacy) == set(LEGACY_TO_V2), "HISTORICAL-LAYER-A-INVENTORY-INCOMPLETE")
    original = sources["worker_handoff"]
    r3_checked = read("formal_supervisor_result.json")["layer_a"]["checks"]
    r3_semantic = {
        "receipt_present": "worker_receipt_envelope", "receipt_parse_valid": "worker_receipt_envelope",
        "payload_digest": "worker_receipt_envelope", "phase": "worker_source_phase",
        "run_id": "worker_identity", "worker_pid": "worker_identity",
        "status_success": "worker_status_success", "env_close": "env_close",
        "app_close_invoked": "app_close_invoked", "receipt_order": "receipt_before_app_close",
        "completion": "counts", "route": "route_health", "w1_w6": "canonical_witnesses",
        "w7": "canonical_witnesses", "config_authority": "worker_receipt_envelope",
    }
    defaulted = {"environment", "reset", "learner_once", "task_progress", "persistent_learner",
                 "actor_plans", "factor", "critic", "valuenorm", "adam", "numerical",
                 "contracts", "returns", "route", "w1_w6", "w7"}
    field_map = {
        "environment": ["environment_count"], "reset": ["initial_reset_count"],
        "learner_once": ["persistent_learner_count"], "task_progress": ["TASK_COMPLETED_count", "completion_delta", "max_coverage"],
        "returns": ["event_returns_count", "stock_compute_returns_count"],
        "contracts": ["contracts"], "persistent_learner": ["learner"],
        "actor_plans": ["learner"], "factor": ["factor_audits_pass"],
        "critic": ["learner"], "valuenorm": ["learner"], "adam": ["learner"],
        "numerical": ["learner"], "route": ["partial_update", "route_poisoned", "final_in_worker_quiescence_pass"],
        "w1_w6": ["witnesses"], "w7": ["witnesses", "W7_qualified_count"],
    }
    result = []
    for predicate, line in legacy.items():
        mapped = r3_semantic.get(predicate)
        checked = bool(mapped and r3_checked.get(mapped) is True)
        result.append({
            "predicate_id": predicate,
            "semantic_purpose": f"Inherited RE5 Layer-A {predicate} success gate",
            "worker_receipt_fields": field_map.get(predicate, [predicate]),
            "authoritative_raw_source": "RE5 formal worker receipt plus raw run/ledger/normalization/PPQ-V2 evidence",
            "expected_relation": LEGACY_TO_V2[predicate],
            "historical_source_file_function_line": f"{RE5.relative_to(ROOT).as_posix()}:_layer_a_validate:{line}",
            "r3_receipt_populated": predicate not in defaulted,
            "r3_supervisor_checked": checked,
            "r3_check_name": mapped,
            "classification": "DEFAULTED" if predicate in defaulted and predicate not in ("w1_w6", "w7") else
                              "REDUCED" if predicate in ("w1_w6", "w7") else
                              "OMITTED" if not checked else "PRESERVED",
            "v2_predicate": LEGACY_TO_V2[predicate],
        })
    return result


def mutate_payload(payload: dict[str, Any], path: str, value: Any,
                   *, missing: bool = False) -> dict[str, Any]:
    changed = deepcopy(payload)
    parts = path.split(".")
    target = changed
    for part in parts[:-1]:
        target = target[part]
    if missing:
        target.pop(parts[-1], None)
    else:
        target[parts[-1]] = value
    return changed


def negative_matrix(payload: dict[str, Any], sources: dict[str, Any],
                    context: dict[str, Any]) -> dict[str, Any]:
    specs: list[tuple[str, str, Any]] = [
        ("A_environment_zero", "environment_count", 0),
        ("B_reset_zero", "initial_reset_count", 0),
        ("C_learner_zero", "persistent_learner_count", 0),
        ("D_app_launcher_zero", "app_launcher_count", 0),
        ("E_cuda_zero", "cuda_probe_count", 0),
        ("F_physical_mismatch", "physical_transitions", 319),
        ("G_s10_mismatch", "S10_count", 159),
        ("H_ledger_mismatch", "ledger_count", 159),
        ("I_bridge_mismatch", "bridge_count", 158),
        ("J_tx161_started", "tx161_started", True),
        ("K_actor_backward_mismatch", "actor_backward", 0),
        ("L_actor_step_mismatch", "actor_step", 0),
        ("M_critic_backward_mismatch", "critic_backward", 0),
        ("N_critic_step_mismatch", "critic_step", 0),
        ("O_invalid_class", "invalid_critic_class_count", 1),
        ("P_valuenorm_mismatch", "valuenorm_update", 0),
        ("Q_actor_adam_false", "actor_adam_continuity", False),
        ("R_critic_adam_false", "critic_adam_continuity", False),
        ("S_valuenorm_continuity_false", "valuenorm_continuity", False),
        ("T_numerical_false", "numerical_health", False),
        ("U_event_returns_zero", "event_returns_count", 0),
        ("V_stock_returns_nonzero", "stock_compute_returns_count", 1),
        ("W_task_completed_zero", "TASK_COMPLETED_count", 0),
        ("X_completion_delta_zero", "completion_delta", 0),
        ("Y_max_coverage_zero", "max_coverage", 0),
        ("Z_terminal_zero", "terminal_autoreset_count", 0),
        ("AA_post_reset_false", "post_autoreset_learned_transaction", False),
        ("AB_contracts_empty", "contracts", {}),
        ("AC_w2e_identity_wrong", "w2e_selector_sha256", "0" * 64),
        ("AD_ppq_identity_wrong", "ppq_v2_helper_sha256", "0" * 64),
        ("AE_normalizer_identity_wrong", "contracts.normalizer_sha256", "0" * 64),
        ("AF_w1_fail", "witnesses.W1.pass", False),
        ("AG_w2_fail", "witnesses.W2E.pass", False),
        ("AH_w3_fail", "witnesses.W3.pass", False),
        ("AI_w4_fail", "witnesses.W4.pass", False),
        ("AJ_w5_fail", "witnesses.W5.pass", False),
        ("AK_w6_fail", "witnesses.W6.pass", False),
        ("AL_w7_fail", "witnesses.W7.pass", False),
        ("AM_w7_count_mismatch", "W7_qualified_count", 159),
        ("AN_pw_critic_mismatch", "pw_progress.critic_records", 6559),
        ("AO_pw_actor_mismatch", "pw_progress.actor_factor_records", 639),
        ("AP_pw_fault", "pw_progress.missing", 1),
        ("AQ_campaign_not_success", "campaign_status", "STOP"),
        ("AR_partial_update", "partial_update", True),
        ("AS_route_poisoned", "route_poisoned", True),
        ("AT_worker_quiescence_false", "final_in_worker_quiescence_pass", False),
        ("AU_env_close_false", "env_close_pass", False),
        ("AV_app_close_false", "app_close_invoked", False),
        ("AW_checkpoint", "checkpoint_io_count", 1),
        ("AX_public_activation", "public_activation_count", 1),
        ("AY_evaluation", "evaluation_playback_count", 1),
        ("AZ_field_missing", "environment_count", None),
        ("BA_field_sentinel", "initial_reset_count", None),
        ("BB_learner_empty", "learner", {}),
        ("BC_contracts_empty", "contracts", {}),
        ("BD_individually_valid_raw_mismatch", "w2e_candidate_count", payload["w2e_candidate_count"] + 1),
        ("BE_layer_b_cannot_rescue", "environment_count", 0),
    ]
    L.require(len(specs) == 57, "NEGATIVE-SPEC-COUNT")
    results = []
    for name, path, value in specs:
        changed = mutate_payload(payload, path, value, missing=name.startswith("AZ_"))
        envelope = L.envelope_for(changed)
        outcome = supervision(envelope, sources, context)
        results.append({"case": name, "field": path, "expected": "STOP",
                        "actual": outcome["status"],
                        "layer_a_pass": outcome["layer_a"]["pass"],
                        "raw_crosscheck_pass": outcome["raw_crosscheck"]["pass"],
                        "failed_predicates": outcome["layer_a"]["failed"],
                        "failed_crosschecks": outcome["raw_crosscheck"]["failed"]})
    L.require(all(row["actual"] == "STOP" for row in results), "NEGATIVE-UNEXPECTED-PASS")
    return {"expected_stop": len(results), "actual_stop": len(results),
            "unexpected_pass": 0, "cases": results}


def defaults_and_coverage(payload: dict[str, Any], sources: dict[str, Any],
                          context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    defaults = [("0", 0), ("false", False), ("empty_object", {}),
                ("empty_array", []), ("none", None), ("missing", None)]
    cases = []
    for field in ("run_id", "environment_count", "learner", "contracts",
                  "event_returns_count", "env_close_pass"):
        for label, value in defaults:
            changed = mutate_payload(payload, field, value, missing=label == "missing")
            result = supervision(L.envelope_for(changed), sources, context)
            cases.append({"field": field, "default": label, "status": result["status"],
                          "failed": result["layer_a"]["failed"]})
    # A legitimate zero is acceptable only when the explicit source is present.
    zero_source_cases = []
    for source_section, key in (("raw_final", "stock_compute_returns"),
                                ("ppq_v2_candidate", "checkpoint_io_count")):
        changed_sources = deepcopy(sources)
        target = (changed_sources["raw_final"]["exact_execution_counts"]
                  if source_section == "raw_final" else changed_sources[source_section])
        target.pop(key)
        try:
            L.project_layer_a_worker_receipt(changed_sources, context["ppq_schema"])
            status = "PASS"
        except (L.LayerAStop, KeyError):
            status = "STOP"
        zero_source_cases.append({"source": f"{source_section}.{key}",
                                  "legitimate_zero_with_missing_source": status})
    L.require(all(case["status"] == "STOP" for case in cases) and
              all(case["legitimate_zero_with_missing_source"] == "STOP"
                  for case in zero_source_cases), "TEMPLATE-DEFAULT-NOT-FAIL-CLOSED")
    field_cases = []
    for field in sorted(payload):
        changed = mutate_payload(payload, field, None, missing=True)
        result = supervision(L.envelope_for(changed), sources, context)
        field_cases.append({"field": field, "negative_case": f"missing:{field}",
                            "status": result["status"],
                            "validator_field_check": result["layer_a"]["checks"].get(f"field:{field}")})
    L.require(all(case["status"] == "STOP" and case["validator_field_check"] is False
                  for case in field_cases), "SUPERVISOR-FIELD-COVERAGE")
    matrix = {"default_cases": cases, "legitimate_zero_source_absence": zero_source_cases,
              "expected_stop": len(cases) + len(zero_source_cases),
              "actual_stop": len(cases) + len(zero_source_cases), "unexpected_pass": 0}
    coverage = {"required_field_count": len(payload), "covered_field_count": len(field_cases),
                "coverage_percent": 100, "supervisor_invocation":
                "adjudicate_supervisor -> validate_layer_a_worker_receipt -> field predicate",
                "fields": field_cases}
    return matrix, coverage


def repository_authority() -> dict[str, Any]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)
    porcelain = git("status", "--porcelain=v1", "-uall")
    staged = git("ls-files", "--stage").decode("utf-8").strip() + "\n"
    paths = git("diff", "--cached", "--name-only").decode("utf-8").strip().splitlines()
    result = {
        "branch": git("branch", "--show-current").decode().strip(),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "origin_main": git("rev-parse", "origin/main").decode().strip(),
        "merge_base": git("merge-base", "HEAD", "origin/main").decode().strip(),
        "full_porcelain": porcelain.decode("utf-8"),
        "porcelain_rows": len(porcelain.decode("utf-8").splitlines()),
        "porcelain_sha256": sha256(porcelain).hexdigest(),
        "pre_first_write_porcelain_rows": 25222,
        "pre_first_write_porcelain_sha256": "3ba9d6e4137139287cbb6e9aa1072c89559e85df63428f69280215d033b2601c",
        "staged_path_count": len(paths),
        "staged_index_sha256": sha256(staged.encode()).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
    }
    L.require(result["branch"] == "main" and result["head"] == result["origin_main"] == result["merge_base"] ==
              "b71d85a32f51be6ada324f870813a56bb45dd396" and
              result["staged_path_count"] == 359 and
              result["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c" and
              result["monthly_path_set_sha256"] == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab",
              "REPOSITORY-AUTHORITY-DRIFT")
    return result


def tree_identity(directory: Path) -> dict[str, Any]:
    h = sha256()
    count = 0
    total = 0
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        relative = path.relative_to(directory).as_posix()
        size = path.stat().st_size
        h.update(f"{relative}\0{size}\0{sha(path)}\n".encode("utf-8"))
        count += 1
        total += size
    return {"file_count": count, "total_bytes": total, "path_size_content_sha256": h.hexdigest()}


def protected_identity() -> dict[str, Any]:
    files = {key: {"path": path.relative_to(ROOT).as_posix(),
                   "bytes": path.stat().st_size, "sha256": sha(path)}
             for key, path in PROTECTED.items()}
    trees = {"historical_r3": tree_identity(R3),
             "historical_r1": tree_identity(R1),
             "historical_r2": tree_identity(R2)}
    return {"files": files, "trees": trees}


def qualification() -> None:
    L.require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(),
              "APPROVED-INTERPRETER")
    authority = repository_authority()
    before = protected_identity()
    sources, context, original = collect()
    payload = L.project_layer_a_worker_receipt(sources, context["ppq_schema"])
    envelope = L.envelope_for(payload)
    positive = supervision(envelope, sources, context)
    original_negative = supervision(original, sources, context)
    L.require(positive["pass"] and not original_negative["pass"] and
              original_negative["layer_b_pass"], "PRIMARY-POSITIVE-NEGATIVE-GATE")
    field_matrix = negative_matrix(payload, sources, context)
    default_matrix, coverage = defaults_and_coverage(payload, sources, context)
    inventory = historical_inventory(sources, context)
    source_fields = source_map(context["ppq_schema"])
    gate_equivalence = [{"historical_predicate": row["predicate_id"],
                         "new_predicate": row["v2_predicate"],
                         "classification": ("IDENTICAL" if row["predicate_id"] in
                                            ("run_id", "worker_pid", "env_close", "app_close_invoked")
                                            else "SUPERSEDED_BY_STRONGER_V2"),
                         "negative_test": "missing:" +
                         next((name for name in row["worker_receipt_fields"] if name in payload),
                              "layer_a_contract_version")}
                        for row in inventory]
    L.require(len(gate_equivalence) == len(inventory) and
              all(row["new_predicate"] for row in gate_equivalence), "GATE-EQUIVALENCE-OMISSION")
    truth_table = []
    for a_pass in (True, False):
        for b_pass in (True, False):
            chosen = envelope if a_pass else L.envelope_for(
                mutate_payload(payload, "environment_count", 0))
            outcome = supervision(chosen, sources, context, b_pass)
            truth_table.append({"layer_a_expected": a_pass, "layer_b_expected": b_pass,
                                "overall_expected": a_pass and b_pass,
                                "layer_a_actual": outcome["layer_a"]["pass"] and outcome["raw_crosscheck"]["pass"],
                                "overall_actual": outcome["pass"]})
    L.require(all(row["layer_a_actual"] == row["layer_a_expected"] and
                  row["overall_actual"] == row["overall_expected"] for row in truth_table),
              "LAYER-A-B-TRUTH-TABLE")
    post = L.failure_flags(irreversible_mutation_observed=True)
    pre = L.failure_flags(irreversible_mutation_observed=False)
    L.require(post["partial_update"] and post["route_poisoned"] and
              not pre["partial_update"] and not pre["route_poisoned"], "FAILURE-SEMANTICS")
    after = protected_identity()
    L.require(before == after, "PROTECTED-SOURCE-DRIFT")

    schema = {"schema_version": L.VERSION, "envelope_schema_version": L.ENVELOPE_VERSION,
              "required_fields": {**context["ppq_schema"]["required_fields"],
                                  **{key: typ.__name__ for key, typ in L.EXTRA_TYPES.items()}},
              "unknown_fields": "REJECT", "missing_or_null": "REJECT",
              "ppq_v2_schema_sha256": sha(PPQ_SCHEMA),
              "envelope_digest": "SHA-256 of RE5-compatible canonical JSON payload bytes with final LF"}
    contract = {"version": L.VERSION, "generic_future_fresh_worker": True,
                "historical_r3_outcome_values_hardcoded": False,
                "requires": ["full PPQ-V2 validation", "all inherited RE5 Layer-A gates",
                             "explicit worker-local construction and close facts",
                             "raw-vs-receipt crosscheck", "Layer B independent PASS"],
                "current_formal_config": CONFIG,
                "template_default_policy": "absent/None/unpopulated mandatory source or field STOP; legitimate zero requires explicit source",
                "publication_order": ["collect authoritative sources", "project worker receipt",
                                      "validate complete Layer A", "crosscheck raw evidence",
                                      "durably publish success", "external Layer B", "overall adjudicate"]}
    write("repository_authority.json", authority)
    write("reviewed_starting_authority.json", {
        "ppq_v2": "GPT REVIEW PASS / CLOSED",
        "re6_r3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "re6_r3_reviewed_classification":
        "PHASE-B2-T4-RE6-R3-INCOMPLETE-LAYER-A-WORKER-RECEIPT-AFTER-MUTATION-REVIEW-STOP",
        "laq": "AUTHORIZED / PURE STATIC QUALIFICATION", "re6_r4": "NOT AUTHORIZED"})
    write("protected_source_identity_before.json", before)
    write("protected_source_identity_after.json", after)
    write("complete_layer_a_predicate_inventory.json", {
        "count": len(inventory), "source": f"{RE5.relative_to(ROOT).as_posix()}:_layer_a_validate",
        "predicates": inventory})
    write("layer_a_receipt_contract_v2.json", contract)
    write("layer_a_receipt_schema_v2.json", schema)
    write("layer_a_receipt_source_map.json", source_fields)
    write("layer_a_gate_equivalence.json", {"historical_count": len(inventory),
          "mapped_count": len(gate_equivalence), "unexplained_omissions": 0,
          "predicates": gate_equivalence})
    write("supervisor_predicate_coverage.json", coverage)
    write("historical_r3_original_receipt_negative.json", {
        "original_sha256": sha(R3 / "formal_worker_receipt.json"),
        "status": original_negative["status"], "layer_b_pass": True,
        "failed_validator_predicates": original_negative["layer_a"]["failed"],
        "failed_raw_crosschecks": original_negative["raw_crosscheck"]["failed"],
        "historical_reclassification": False})
    write("corrected_r3_projection_positive.json", {
        "hypothetical_only": True, "historical_reclassification": False,
        "receipt_envelope": envelope, "validation": positive["layer_a"]})
    write("raw_receipt_crosscheck.json", positive["raw_crosscheck"])
    write("supervisor_replay_positive.json", positive)
    write("supervisor_replay_original_r3_negative.json", original_negative)
    write("field_negative_matrix.json", field_matrix)
    write("template_default_fail_closed_matrix.json", default_matrix)
    write("layer_a_layer_b_truth_table.json", {"pass": True, "cases": truth_table})
    write("post_mutation_failure_semantics.json", post)
    write("pre_mutation_failure_semantics.json", pre)
    write("future_re6_r4_integration_plan.json", {
        "design_only": True, "re6_r4_authorized": False,
        "fresh_namespace": True, "one_worker_zero_retry": True,
        "worker_projection": "build from explicit raw authoritative sources before durable publication",
        "worker_validation": "full Layer-A V2 validator and raw crosscheck before success",
        "supervisor": "validate immutable worker envelope; do not repair; Layer A and EP-Q Layer B both required",
        "ppq_v2": "unchanged reviewed formal success receipt contract",
        "w2e_w2i_pw": "unchanged reviewed authorities",
        "r3_normalizer": "reuse only if frozen identity independently bound",
        "canonical_witnesses": "W1-W7 cannot replace Layer A",
        "historical_r3_learner": "NEVER REUSE"})
    write("qualification_pre_final_result.json", {
        "status": "PASS", "historical_predicates": len(inventory),
        "new_receipt_fields": len(payload), "negative_cases": field_matrix["actual_stop"],
        "unexpected_negative_pass": 0, "default_cases": default_matrix["actual_stop"],
        "coverage_percent": coverage["coverage_percent"], "gate_omissions": 0,
        "truth_table": "4/4 PASS", "final_frozen_positive_runs": 0,
        "final_original_negative_controls": 0})
    write("laq_source_identity_pre_final.json", {
        "helper_sha256": sha(LAQ), "runner_sha256": sha(Path(__file__)),
        "schema_sha256": sha(OUT / "layer_a_receipt_schema_v2.json"),
        "status": "FROZEN FOR ONE FINAL OFFLINE DRY RUN"})
    print(json.dumps({"pre_final_status": "PASS", "fields": len(payload),
                      "historical_predicates": len(inventory),
                      "field_negatives": field_matrix["actual_stop"],
                      "defaults": default_matrix["actual_stop"],
                      "coverage": coverage["coverage_percent"]}))


def require_source_freeze() -> dict[str, Any]:
    frozen = json.loads((OUT / "laq_source_identity_pre_final.json").read_text(encoding="utf-8"))
    L.require(frozen["helper_sha256"] == sha(LAQ) and
              frozen["runner_sha256"] == sha(Path(__file__)) and
              frozen["schema_sha256"] == sha(OUT / "layer_a_receipt_schema_v2.json"),
              "LAQ-CANDIDATE-DRIFT-AFTER-FREEZE")
    return frozen


def final_positive() -> None:
    L.require(not (OUT / "final_dry_run_result.json").exists(),
              "FINAL-POSITIVE-ALREADY-EXECUTED")
    frozen = require_source_freeze()
    pre = json.loads((OUT / "qualification_pre_final_result.json").read_text(encoding="utf-8"))
    L.require(pre["status"] == "PASS" and pre["final_frozen_positive_runs"] == 0,
              "PRE-FINAL-GATE-NOT-PASS")
    sources, context, _ = collect()
    payload = L.project_layer_a_worker_receipt(sources, context["ppq_schema"])
    envelope = L.envelope_for(payload)
    outcome = supervision(envelope, sources, context,
                          read("process_quiescence.json")["pass"])
    L.require(outcome["pass"] and outcome["layer_a"]["pass"] and
              outcome["raw_crosscheck"]["pass"] and outcome["layer_b_pass"],
              "FINAL-FROZEN-POSITIVE-DRY-RUN-FAILED")
    write("final_dry_run_result.json", {
        "status": "PASS", "scope": "hypothetical corrected R3 projection only",
        "historical_r3_reclassified": False,
        "pipeline": ["immutable R3 raw evidence", "Layer-A V2 projection",
                     "raw-vs-receipt crosscheck", "complete Layer-A validator",
                     "preserved EP-Q Layer-B PASS", "supervisor hypothetical PASS"],
        "layer_a_pass": True, "layer_b_pass": True,
        "overall_hypothetical_pass": True,
        "frozen_helper_sha256": frozen["helper_sha256"],
        "frozen_runner_sha256": frozen["runner_sha256"],
        "frozen_schema_sha256": frozen["schema_sha256"],
        "projected_receipt_payload_sha256": envelope["payload_sha256"],
        "raw_crosscheck_count": len(outcome["raw_crosscheck"]["checks"]),
        "validator_predicate_count": len(outcome["layer_a"]["checks"]),
        "final_frozen_positive_offline_dry_runs": 1})
    print("FINAL-POSITIVE-PASS")


def final_negative() -> None:
    L.require((OUT / "final_dry_run_result.json").exists(),
              "FINAL-POSITIVE-MISSING")
    L.require(not (OUT / "final_original_r3_negative_control.json").exists(),
              "FINAL-NEGATIVE-ALREADY-EXECUTED")
    frozen = require_source_freeze()
    sources, context, original = collect()
    outcome = supervision(original, sources, context,
                          read("process_quiescence.json")["pass"])
    L.require(outcome["status"] == "STOP" and not outcome["layer_a"]["pass"] and
              not outcome["raw_crosscheck"]["pass"] and outcome["layer_b_pass"],
              "FINAL-ORIGINAL-R3-NEGATIVE-CONTROL-FAILED")
    before = json.loads((OUT / "protected_source_identity_before.json").read_text(encoding="utf-8"))
    after = protected_identity()
    L.require(before == after, "PROTECTED-SOURCE-DRIFT-AFTER-FINAL")
    write("protected_source_identity_after.json", after)
    write("final_original_r3_negative_control.json", {
        "status": "STOP AS EXPECTED", "original_receipt_sha256": sha(R3 / "formal_worker_receipt.json"),
        "layer_a_pass": False, "layer_b_pass": True, "overall_pass": False,
        "failed_validator_predicates": outcome["layer_a"]["failed"],
        "failed_raw_crosschecks": outcome["raw_crosscheck"]["failed"],
        "historical_r3_reclassified": False,
        "final_original_r3_negative_controls": 1})
    write("laq_source_identity_manifest.json", {
        "status": "CANDIDATE / AWAITING GPT REVIEW",
        "helper_sha256": frozen["helper_sha256"],
        "runner_sha256": frozen["runner_sha256"],
        "schema_sha256": frozen["schema_sha256"],
        "final_dry_run_result_sha256": sha(OUT / "final_dry_run_result.json")})
    write("final_result.json", {
        "classification":
        "PHASE-B2-T4-LAQ-LAYER-A-WORKER-RECEIPT-SUPERVISOR-PREDICATE-QUALIFIED-AWAITING-GPT-REVIEW",
        "status": "COMPLETE / AWAITING GPT REVIEW",
        "historical_r3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "layer_a_predicate_inventory": "PASS",
        "r3_defaulted_omitted_analysis": "PASS",
        "source_map": "PASS", "template_defaults": "FAIL CLOSED",
        "raw_projection_crosscheck": "PASS",
        "corrected_hypothetical_r3": "PASS",
        "original_r3_receipt": "STOP AS EXPECTED",
        "field_negatives": 57, "unexpected_negative_pass": 0,
        "supervisor_predicate_coverage_percent": 100,
        "gate_equivalence_unexplained_omissions": 0,
        "layer_a_layer_b_truth_table": "4/4 PASS",
        "final_frozen_positive_offline_dry_runs": 1,
        "final_original_r3_negative_controls": 1,
        "protected_source_changes": 0,
        "formal_supervisors": 0, "formal_workers": 0, "cuda_probes": 0,
        "app_launchers": 0, "environments": 0, "learners": 0,
        "re6_r4_attempts": 0, "checkpoint_io": 0,
        "public_activation": 0, "evaluation_playback": 0,
        "git_add_commit_push": [0, 0, 0],
        "re6_r4": "NOT AUTHORIZED", "public_route": "DORMANT / BLOCKED"})
    print("FINAL-ORIGINAL-R3-STOP-AS-EXPECTED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=("qualify", "final-positive", "final-negative"))
    mode = parser.parse_args().mode
    if mode == "qualify":
        qualification()
    elif mode == "final-positive":
        final_positive()
    else:
        final_negative()


if __name__ == "__main__":
    main()
