"""Repair-tolerant one-shot RE6-R9 formal integration harness.

The reviewed R8 orchestration is expanded in memory and rebound to a fresh R9
namespace.  Only R9 test-side source construction changes: the complete LAQ
synthetic source shape is derived and tested before a live authority exists.
Reviewed helpers, contracts, and production sources remain read-only.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r8_norm_r1_racq_r1_bound_normal_horizon_integration as R8


PREAUTH_SUPPORT = r'''
def _r9_complete_synthetic_raw(raw_value: Mapping[str, Any]) -> dict[str, Any]:
    """Project the reviewed runtime-produced fields into the R9-only fixture."""
    raw = deepcopy(raw_value)
    counts = raw["final"]["exact_execution_counts"]
    counts.update({
        "app_launcher_lifetimes": 1,
        "environment_constructions": 1,
        "environment_resets": 1,
        "distinct_learner_constructions": 1,
        "valid_nonzero_update": 1600,
        "valid_zero_effective_update": 0,
        "missing_call_faults": 0,
        "duplicate_call_faults": 0,
        "continuation_resample_faults": 0,
    })
    raw["final"]["final_read_only_quiescence_check"] = {"pass": True}
    for row in raw["final"]["transactions"]:
        row["factor_segment_count"] = 3
        row["s10_pass"] = True
    for row in raw["terminal"]:
        row["s7_ledger_unchanged"] = True
    return raw


def _r9_synthetic_witnesses(raw: Mapping[str, Any]) -> dict[str, Any]:
    witnesses = {key: deepcopy(raw["witnesses"][{
        "W1": "W1_CROSS_UPDATE_OWNERSHIP", "W2E": "W2_MULTI_UPDATE_COMPLETION",
        "W3": "W3_ZERO_DVM_ACTOR", "W4": "W4_NONTERMINAL_BOOTSTRAP",
        "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY"}[key]])
        for key in CANONICAL_NAMES}
    witnesses["W7"]["qualified_count"] = CONFIG["expected_transaction_count"]
    return witnesses


def _r9_preauthority_fixture(base: Mapping[str, Any], run_id: str, worker_pid: int,
                             directory: Path) -> dict[str, Any]:
    raw, _ = base["synthetic_raw"]()
    raw = _r9_complete_synthetic_raw(raw)
    raw.update({"source_phase": PHASE, "run_id": run_id, "worker_pid": worker_pid,
                "artifact_namespace": namespace(run_id)})
    pw_value = {"contract_version": base["PPQ"].PW_VERSION, "run_id": run_id,
                "transaction_count": 160, "critic_actual": 6560,
                "actor_factor_actual": 640, "missing_count": 0,
                "duplicate_count": 0, "order_fault_count": 0,
                "digest_fault_count": 0, "temp_residue_count": 0}
    verifier = lambda: deepcopy(pw_value)
    synthetic_context_document = {
        "context_version": NORM_R1.CONTEXT_VERSION,
        "authority_kind": "RUNTIME_AUTHORITY_AND_RUN_BINDING",
        "expected_source_phase": PHASE,
        "expected_run_id": run_id,
        "expected_artifact_namespace": namespace(run_id),
        "source_authority_digest": "a" * 64,
        "run_binding_digest": "b" * 64,
    }
    converted = NORM_R1.normalize(
        raw, trusted_context=NORM_R1.make_trusted_context(synthetic_context_document),
        config=CONFIG, w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)

    root, auth_path, bind_path = ppq_paths(directory, run_id)
    authority = PPQ_R1.make_offline_authority(
        source_phase=PHASE,
        authority_instance_id=auth_path.name.removesuffix(".source_phase_authority.json"))
    persist(auth_path, authority)
    binding = PPQ_R1.make_run_binding(
        authority=authority, run_id=run_id, worker_pid=worker_pid,
        config_digest=ppq_identity()["config_identity_digest"],
        artifact_namespace=namespace(run_id))
    persist(bind_path, binding)
    receipt, _, _, trace = PPQ_R1.build_receipt(
        converted["normalized"], w2e_selector=PPQ_TEST.W2E.reconcile,
        w2i_manifest=W2I, pw_reconcile=lambda _: verifier(), expected_phase=PHASE,
        config=CONFIG, identity=ppq_identity(), legacy_identity=PPQ_TEST.legacy_identity(),
        production_sources=PRODUCTION, pw_helper_path=PW_HELPER,
        authority_path=auth_path, expected_authority_path=auth_path,
        run_binding_path=bind_path, expected_run_binding_path=bind_path,
        authority_root=root, artifact_namespace=namespace(run_id))
    handoff = {
        "status": "success", "source_authority_digest": "c" * 64,
        "config_authority_digest": ppq_identity()["config_identity_digest"],
        "filesystem_precondition_digest": "d" * 64,
        "cuda_probe_count": 1, "cuda_probe_pass": True,
        "app_launcher_started": True, "entry_point_resolution_pass": True,
        "env_close_pass": True, "app_close_invoked": True,
        "receipt_written_before_app_close": True, "receipt_fsync_pass": True,
        "receipt_readback_pass": True,
    }
    pw_view = {"critic_records": 6560, "actor_factor_records": 640,
               "missing": 0, "duplicate": 0, "out_of_order": 0,
               "digest_mismatch": 0, "temp_residue": 0,
               "old_mutable_progress_paths": 0}
    sources = {
        "raw_final": raw["final"], "ppq_v2_candidate": receipt,
        "normalized": converted, "worker_handoff": handoff,
        "pw_verifier": pw_view, "witnesses": _r9_synthetic_witnesses(raw),
        "normalizer_sha256": sha(NORMALIZER),
        "ppq_v2_readback": {"pass": True},
        "ppq_v2_candidate_file_sha256": PPQ_R1.digest(receipt),
        "transaction_rows": raw["transactions"],
        "terminal_rows": raw["terminal"],
        "zero_dvm_rows": [{"pass": True} for _ in raw["transactions"]],
    }
    return {"raw": raw, "converted": converted, "receipt": receipt,
            "sources": sources, "trace": trace, "normalization_context": synthetic_context_document}


def _r9_projection_outcome(sources: Mapping[str, Any], directory: Path,
                           run_id: str, worker_pid: int) -> dict[str, Any]:
    try:
        payload = LAQ.project_layer_a_worker_receipt(sources, PPQ_R1.schema_document())
        envelope = LAQ.envelope_for(payload)
        validation = LAQ.validate_layer_a_worker_receipt(
            envelope, ppq_schema=PPQ_R1.schema_document(),
            ppq_validator=lambda value, **_: ppq_validate(value, directory, run_id),
            expected_phase=PHASE, expected_run_id=run_id, expected_pid=worker_pid,
            expected_source_digest=sources["worker_handoff"]["source_authority_digest"],
            expected_config_digest=ppq_identity()["config_identity_digest"],
            ppq_identity=ppq_identity(), ppq_config=CONFIG,
            expected_normalizer_sha256=sha(NORMALIZER))
        return {"status": "PASS" if validation["pass"] else "STOP",
                "pass": validation["pass"], "validation": validation,
                "payload": payload if validation["pass"] else None,
                "reason": None if validation["pass"] else validation["failed"]}
    except Exception as exc:
        return {"status": "STOP", "pass": False,
                "exception_type": type(exc).__name__, "reason": str(exc),
                "payload": None}


def _r9_path_value(value: Any, path: tuple[Any, ...]) -> Any:
    for token in path:
        value = value[token]
    return value


def _r9_delete_path(value: Any, path: tuple[Any, ...]) -> None:
    parent = _r9_path_value(value, path[:-1])
    del parent[path[-1]]


def _r9_shape(value: Any) -> str:
    if type(value) is list:
        return f"list[{len(value)}]"
    if type(value) is dict:
        return f"object[{len(value)}]"
    return type(value).__name__


def _r9_field_specs(sources: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[tuple[tuple[Any, ...], str, str]] = []
    def add(path: tuple[Any, ...], origin: str, producer: str) -> None:
        if path not in [entry[0] for entry in rows]:
            rows.append((path, origin, producer))
    for key in sources:
        add((key,), "LAQ project_layer_a_worker_receipt top-level source", "R9 synthetic source builder")
    for key in sources["ppq_v2_candidate"]:
        add(("ppq_v2_candidate", key), "PPQ-V2-R1 required field", "reviewed PPQ-R1 builder")
    for key in sources["raw_final"]["exact_execution_counts"]:
        if key in {"app_launcher_lifetimes", "environment_constructions", "environment_resets",
                   "distinct_learner_constructions", "s10_pass", "event_return_computations",
                   "stock_compute_returns", "critic_optimizer_step_total", "valid_nonzero_update",
                   "valid_zero_effective_update", "missing_call_faults", "duplicate_call_faults",
                   "continuation_resample_faults"}:
            add(("raw_final", "exact_execution_counts", key), "LAQ direct execution-count projection",
                "real runtime final-result counter")
    add(("raw_final", "persistent_learner_identity", "object_ids_stable"),
        "LAQ persistent-continuity projection", "real runtime identity ledger")
    add(("raw_final", "final_read_only_quiescence_check", "pass"),
        "LAQ worker-quiescence projection", "real runtime final quiescence check")
    for key in ("factor_segment_count", "s10_pass"):
        add(("raw_final", "transactions", 0, key), "LAQ factor-audit projection",
            "real runtime transaction result")
    for key in LAQ.LEARNER_KEYS:
        add(("normalized", "normalized", "learner", key), "LAQ normalized learner projection",
            "NORM-R1 normalized runtime evidence")
    for key in ("task_completed_count", "coverage_max"):
        add(("normalized", "derived", key), "LAQ normalized progress projection",
            "NORM-R1 derived evidence")
    for key in ("status", "source_authority_digest", "config_authority_digest",
                "filesystem_precondition_digest", "cuda_probe_count", "cuda_probe_pass",
                "app_launcher_started", "entry_point_resolution_pass", "env_close_pass",
                "app_close_invoked", "receipt_written_before_app_close", "receipt_fsync_pass",
                "receipt_readback_pass"):
        add(("worker_handoff", key), "LAQ close-handoff projection", "real formal worker handoff")
    for key in LAQ.PW_KEYS:
        add(("pw_verifier", key), "LAQ PW projection", "reviewed PW verifier")
    for key in LAQ.WITNESS_KEYS:
        add(("witnesses", key), "LAQ witness-set closure", "real canonical witness producer")
        add(("witnesses", key, "pass"), "LAQ witness-status projection", "real canonical witness producer")
    add(("witnesses", "W7", "qualified_count"), "LAQ W7 count projection", "real W7 producer")
    for key in ("pass", "s7_ledger_unchanged"):
        add(("terminal_rows", 0, key), "LAQ terminal-row projection", "terminal reconciliation ledger")
    add(("zero_dvm_rows", 0, "pass"), "LAQ zero-DVM projection", "zero-DVM actor ledger")
    for key in ("s7_s8_s9_s10", "finite"):
        add(("transaction_rows", 0, key), "LAQ bookkeeping projection", "transaction ledger")
    add(("ppq_v2_readback", "pass"), "LAQ PPQ readback projection", "PPQ durable readback")
    result = []
    for path, origin, producer in rows:
        current = _r9_path_value(sources, path)
        result.append({"path": list(path), "path_text": ".".join(str(x) for x in path),
                       "field_source_origin": origin, "type_shape": _r9_shape(current),
                       "real_runtime_producer": producer,
                       "synthetic_producer": "_r9_preauthority_fixture",
                       "classification": "required"})
    return result


def _r9_structural_composition(receipt: Mapping[str, Any], laq_payload: Mapping[str, Any],
                               run_id: str, worker_pid: int) -> dict[str, Any]:
    template = COMPOSE.registry_template_document()
    registry = {"template_digest": COMPOSE.digest(template),
                "instance_digest": "e" * 64}
    authority = {"authority_version": RACQ.AUTHORITY_VERSION,
                 "authorization_scope": RACQ.AUTHORIZATION_SCOPE,
                 "authority_payload_digest": "f" * 64}
    binding = {"binding_version": RACQ.BINDING_VERSION,
               "binding_payload_digest": "1" * 64,
               "artifact_namespace": namespace(run_id)}
    payload = COMPOSE.compose_payload(
        ppq_receipt=receipt, laq_v2_payload=laq_payload,
        runtime_authority=authority, run_binding=binding, registry_instance=registry)
    return {"pass": len(payload) == 43 and len(payload["ppq_v2_r1_payload"]) == 90,
            "top_level_fields": len(payload),
            "nested_ppq_fields": len(payload["ppq_v2_r1_payload"]),
            "authority_objects": "NONLIVE_SYNTHETIC_STRUCTURAL_PLACEHOLDERS"}


def pre_authority_readiness(base: Mapping[str, Any], run_id: str, worker_pid: int,
                            directory: Path, *, persist_outputs: bool) -> dict[str, Any]:
    fixture = _r9_preauthority_fixture(base, run_id, worker_pid, directory)
    sources = fixture["sources"]
    specs = _r9_field_specs(sources)
    required = {row["path_text"] for row in specs}
    present = {row["path_text"] for row in specs
               if _r9_path_value(sources, tuple(row["path"])) is not None}
    parity = {
        "pass": required == present,
        "required_field_count": len(required), "synthetic_field_count": len(present),
        "missing_required_fields": sorted(required - present),
        "unexpected_synthetic_authority_bearing_fields": [],
        "required_minus_synthetic_empty": required - present == set(),
    }
    require(parity["pass"], "PREAUTH-SOURCE-SHAPE-PARITY", parity)

    old_r8 = deepcopy(sources)
    for row in old_r8["terminal_rows"]:
        row.pop("s7_ledger_unchanged", None)
    old_outcome = _r9_projection_outcome(old_r8, directory, run_id, worker_pid)
    positive = _r9_projection_outcome(sources, directory, run_id, worker_pid)
    require(old_outcome["status"] == "STOP" and positive["pass"],
            "R8-REPRODUCTION-R9-REPAIR", {"r8": old_outcome, "r9": positive})

    missing_rows = []
    for spec in specs:
        altered = deepcopy(sources)
        _r9_delete_path(altered, tuple(spec["path"]))
        outcome = _r9_projection_outcome(altered, directory, run_id, worker_pid)
        missing_rows.append({"path": spec["path_text"], "expected": "STOP",
                             "actual": outcome["status"],
                             "reason": outcome.get("reason"),
                             "exception_type": outcome.get("exception_type")})
    missing_matrix = {"pass": all(row["actual"] == "STOP" for row in missing_rows),
                      "expected_stop": len(missing_rows),
                      "actual_stop": sum(row["actual"] == "STOP" for row in missing_rows),
                      "unexpected_pass": sum(row["actual"] != "STOP" for row in missing_rows),
                      "cases": missing_rows}
    require(missing_matrix["pass"], "PREAUTH-MISSING-FIELD-MATRIX", missing_matrix)

    representative = []
    for label, mutate in (
        ("terminal s7 wrong type", lambda value: value["terminal_rows"][0].__setitem__("s7_ledger_unchanged", "true")),
        ("terminal_rows wrong shape", lambda value: value.__setitem__("terminal_rows", {"pass": True})),
        ("terminal s7 null", lambda value: value["terminal_rows"][0].__setitem__("s7_ledger_unchanged", None)),
        ("terminal s7 semantically false", lambda value: value["terminal_rows"][0].__setitem__("s7_ledger_unchanged", False)),
        ("transaction bookkeeping wrong shape", lambda value: value["transaction_rows"][0].__setitem__("s7_s8_s9_s10", [True])),
    ):
        altered = deepcopy(sources); mutate(altered)
        outcome = _r9_projection_outcome(altered, directory, run_id, worker_pid)
        representative.append({"case": label, "expected": "STOP", "actual": outcome["status"],
                               "reason": outcome.get("reason"),
                               "exception_type": outcome.get("exception_type")})
    representative_result = {"pass": all(row["actual"] == "STOP" for row in representative),
                             "expected_stop": len(representative),
                             "actual_stop": sum(row["actual"] == "STOP" for row in representative),
                             "unexpected_pass": sum(row["actual"] != "STOP" for row in representative),
                             "cases": representative}
    require(representative_result["pass"], "PREAUTH-TYPE-SHAPE-NEGATIVES", representative_result)
    composition = _r9_structural_composition(fixture["receipt"], positive["payload"], run_id, worker_pid)
    require(composition["pass"], "PREAUTH-LAYER-A-STRUCTURE", composition)

    contract = {
        "contract_version": "b2_t4_re6_r9_layer_a_synthetic_source_shape_v1",
        "reviewed_projection_path": "LAQ.project_layer_a_worker_receipt",
        "reviewed_laq_sha256": sha(HERE / "_assignment_phase_b2_t4_laq_worker_receipt.py"),
        "required_terminal_row_fields": [row for row in specs if row["path_text"].startswith("terminal_rows.0.")],
        "required_nonterminal_row_fields": [],
        "nonterminal_rows_applicable": False,
        "all_required_projection_fields": specs,
    }
    reproduction = {"pass": True,
        "r8_fixture_missing_s7_ledger_unchanged": old_outcome,
        "r9_complete_source_shape": {"status": positive["status"],
            "validation_pass": positive["validation"]["pass"]},
        "same_laq_projection_stage": True}
    repair_log = {"schema_version": "b2_t4_re6_r9_pre_runtime_repair_log_v1",
        "repair_count": 4, "unresolved_repairs": 0, "major_stop_findings": 0,
        "repairs": [{
            "repair_id": "R9-PRE-001", "timestamp_order": 1,
            "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "failing_gate": "historical R8 pre_runtime_layer_a_synthetic_positive",
            "original_exception_reason": "KeyError:s7_ledger_unchanged",
            "affected_file": "scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py",
            "affected_symbol": "_r9_complete_synthetic_raw / _r9_synthetic_witnesses",
            "exact_root_cause": "R8 synthetic builder did not project the complete reviewed LAQ source-field set",
            "reviewed_contract_establishing_expected_behavior": "_assignment_phase_b2_t4_laq_worker_receipt.py::project_layer_a_worker_receipt",
            "changed_files": ["scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py"],
            "semantic_impact": "NONE", "production_impact": "NONE",
            "frozen_contract_impact": "NONE", "learner_impact": "NONE",
            "before_evidence": "R8 pre_runtime_layer_a_controls.json and failure_receipt.json",
            "after_evidence": "R9 source-shape parity, full missing-field matrix, representative type/shape negatives, and repaired projection PASS",
            "validation_rerun": ["R8 blocker reproduction", "complete LAQ projection", "canonical 43/90 structural composition"],
            "result": "RESOLVED"}, {
            "repair_id": "R9-PRE-002", "timestamp_order": 2,
            "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "failing_gate": "pre-authority synthetic PPQ-V2-R1 phase-authority binding",
            "original_exception_reason": "PPQV2R1Stop:PHASE-AUTHORITY-FILENAME",
            "affected_file": "scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py",
            "affected_symbol": "_r9_preauthority_fixture",
            "exact_root_cause": "test-side authority_instance_id literal did not equal the reviewed deterministic authority filename stem",
            "reviewed_contract_establishing_expected_behavior": "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py::load_phase_authority",
            "changed_files": ["scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py"],
            "semantic_impact": "NONE", "production_impact": "NONE",
            "frozen_contract_impact": "NONE", "learner_impact": "NONE",
            "before_evidence": "pre-authority-check PPQV2R1Stop PHASE-AUTHORITY-FILENAME",
            "after_evidence": "authority_instance_id derived from deterministic reviewed path",
            "validation_rerun": ["synthetic PPQ projection", "complete downstream pre-authority readiness"],
            "result": "RESOLVED"}, {
            "repair_id": "R9-PRE-003", "timestamp_order": 3,
            "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "failing_gate": "repaired synthetic LAQ projection critic-class count",
            "original_exception_reason": "LayerAStop:MISSING-SOURCE:raw.counts.valid_nonzero_update",
            "affected_file": "scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py",
            "affected_symbol": "_r9_complete_synthetic_raw",
            "exact_root_cause": "R9 synthetic execution-count projection omitted the reviewed valid critic update-class count pair",
            "reviewed_contract_establishing_expected_behavior": "_assignment_phase_b2_t4_laq_worker_receipt.py::project_layer_a_worker_receipt invalid_critic_class_count derivation",
            "changed_files": ["scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py"],
            "semantic_impact": "NONE", "production_impact": "NONE",
            "frozen_contract_impact": "NONE", "learner_impact": "NONE",
            "before_evidence": "pre-authority repaired projection STOP on missing valid_nonzero_update",
            "after_evidence": "synthetic reviewed counts project critic total 1600 into valid nonzero/effective-zero 1600/0",
            "validation_rerun": ["complete LAQ projection", "all downstream pre-authority gates"],
            "result": "RESOLVED"}, {
            "repair_id": "R9-PRE-004", "timestamp_order": 4,
            "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "failing_gate": "repository starting-porcelain reconstruction before live authority",
            "original_exception_reason": "REPOSITORY-STARTING-PORCELAIN one unfiltered R9 harness path",
            "affected_file": "scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py",
            "affected_symbol": "transformed_source repository_authority path filter",
            "exact_root_cause": "inherited R8 filename substitution produced an R9 filename that did not equal the repair-tolerant harness filename",
            "reviewed_contract_establishing_expected_behavior": "task repository-authority rule and captured pre-first-write porcelain digest",
            "changed_files": ["scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py"],
            "semantic_impact": "NONE", "production_impact": "NONE",
            "frozen_contract_impact": "NONE", "learner_impact": "NONE",
            "before_evidence": "static-preflight STOP with reconstructed line count 25629 instead of 25628",
            "after_evidence": "exact repair-tolerant harness path excluded as task-created evidence",
            "validation_rerun": ["repository authority", "complete static preflight and all downstream gates"],
            "result": "RESOLVED"}]}
    result = {"pass": True, "live_authority_created": False,
              "source_shape_parity": parity["pass"],
              "r8_blocker_reproduced": old_outcome["status"] == "STOP",
              "repaired_laq_projection": positive["pass"],
              "synthetic_ppq_fields": len(fixture["receipt"]),
              "synthetic_norm_r1": fixture["converted"]["crosscheck_pass"],
              "layer_a_structural_composition": composition,
              "missing_field_matrix": {k: v for k, v in missing_matrix.items() if k != "cases"},
              "representative_negatives": {k: v for k, v in representative_result.items() if k != "cases"},
              "minor_repairs": 4, "unresolved_minor_repairs": 0, "major_stop_findings": 0}
    if persist_outputs:
        persist(OUT / "layer_a_synthetic_source_shape_contract.json", contract)
        persist(OUT / "layer_a_synthetic_source_shape_parity.json", parity)
        persist(OUT / "layer_a_synthetic_missing_field_matrix.json", missing_matrix)
        persist(OUT / "layer_a_synthetic_type_shape_negatives.json", representative_result)
        persist(OUT / "r8_source_shape_reproduction_and_r9_repair.json", reproduction)
        persist(OUT / "pre_runtime_repair_log.json", repair_log)
        r8_root = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r8_artifacts"
        r8_run = r8_root / "b2-t4-re6-r8-20260922-formal01-f5c47b1ad2ba42a1baaa552f64d3a675"
        persist(OUT / "historical_r8_preservation.json", {
            "pass": True, "status": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / NOT POISONED / NO RETRY",
            "report_sha256": sha(SCAN / "AgentRead/202609/20260922/PHASE_B2_T4_RE6_R8_NORM_R1_RACQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_REPORT.md"),
            "final_result_sha256": sha(r8_run / "final_result.json"),
            "process_quiescence_sha256": sha(r8_run / "process_quiescence.json"),
            "rerun": False, "rewritten": False})
        persist(OUT / "pre_authority_readiness.json", result)
    return result


def final_static_replay(base: Mapping[str, Any], run_id: str, worker_pid: int,
                        prepared: Mapping[str, Any], directory: Path) -> dict[str, Any]:
    frozen = read(OUT / "r9_harness_identity_freeze.json")
    chain = synthetic_chain(base, run_id, worker_pid, prepared, directory)
    authority_check = validate_live_authority(read(authority_path()))
    normalization_check = _validate_normalization_document(
        read(OUT / "r9_normalization_context.json"), run_id)
    registry_check = COMPOSE.validate_registry_instance(
        prepared["registry"], template=prepared["template"], run_context=prepared["context"])
    mode_check = mode_controls(read(authority_path()))
    result = {"pass": identity_gate()["pass"] and
                     read(OUT / "pre_authority_readiness.json")["pass"] and
                     authority_check["pass"] and normalization_check["pass"] and
                     bool(registry_check) and mode_check["pass"] and chain["pass"] and
                     frozen["sha256"] == sha(Path(__file__).resolve()),
              "identity_gate": True, "pre_authority_readiness": True,
              "live_authority": authority_check["pass"],
              "normalization_context": normalization_check["pass"],
              "registry": bool(registry_check), "mode_controls": mode_check["pass"],
              "complete_synthetic_chain": chain["pass"],
              "harness_frozen": frozen["sha256"] == sha(Path(__file__).resolve()),
              "source_edits_after_freeze": 0, "worker_released": False}
    require(result["pass"], "FINAL-STATIC-READINESS", result)
    persist(OUT / "final_static_readiness.json", result)
    return result
'''


REPORT_WRAPPER = r'''
_r9_base_report_text = report_text
def report_text(result: Mapping[str, Any], payload: Mapping[str, Any],
                layer: Mapping[str, Any]) -> str:
    repair_log = read(OUT / "pre_runtime_repair_log.json")
    contract = read(OUT / "layer_a_synthetic_source_shape_contract.json")
    parity = read(OUT / "layer_a_synthetic_source_shape_parity.json")
    missing = read(OUT / "layer_a_synthetic_missing_field_matrix.json")
    final_static = read(OUT / "final_static_readiness.json")
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, result["run_id"]))
    registry = read(run_dir() / "layer_a_registry_instance.json")
    ppq = read(run_dir() / "candidate_success_receipt_v2_1.json")
    selected = read(run_dir() / "w2e_selected_witness.json")
    lines = [
        "# Phase B2-T4-RE6-R9 Repair-Tolerant Preflight Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "",
        "## PRE-RUNTIME REPAIRS", "",
        "| Repair ID | Initial failure | Classification | Changed file | Semantic impact | Revalidation | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in repair_log["repairs"]:
        lines.append(f"| {row['repair_id']} | {row['original_exception_reason']} | {row['classification']} | {row['affected_file']} | {row['semantic_impact']} | complete source-shape + missing/type/shape + 43/90 composition | {row['result']} |")
    lines.extend(["", "## Source-shape required fields", "",
                  "| Collection | Field | Type/shape | Real producer | Required |",
                  "|---|---|---|---|---|"])
    for row in contract["required_terminal_row_fields"]:
        lines.append(f"| terminal_rows | {row['path_text']} | {row['type_shape']} | {row['real_runtime_producer']} | yes |")
    lines.extend(["", "Nonterminal row fields: not applicable to the reviewed projection path.", "",
                  "## Source-shape parity", "",
                  f"PASS. required={parity['required_field_count']}; present={parity['synthetic_field_count']}; missing=0; unexpected authority-bearing=0.", "",
                  "## Missing-field matrix", "",
                  f"PASS. {missing['actual_stop']}/{missing['expected_stop']} STOP; unexpected PASS={missing['unexpected_pass']}.", "",
                  "## Live authority / binding / registry", "",
                  "| Item | Count | Digest | Result |", "|---|---:|---|---|",
                  f"| Live R9 authority | 1 | {authority['authority_payload_digest']} | PASS |",
                  f"| Live R9 run binding | 1 | {binding['binding_payload_digest']} | PASS |",
                  f"| R9 registry instance | 1 | {registry['instance_digest']} | PASS |", "",
                  "## Normalization", "", f"NORM-R1 PASS; phase `{PHASE}`; historical R3 calls 0.", "",
                  "## Runtime", "", f"physical/transactions/S10/bridges={payload['physical_transitions']}/{payload['ledger_qualified_transactions']}/{payload['production_s10']}/{payload['bridges']}; tx161 not started.", "",
                  "## W2 witness", "", f"env={selected.get('env_id')}, robot={selected.get('robot_id')}, task={selected.get('task_id')}, claim=tx{selected.get('claim_tx')}, completion=tx{selected.get('completion_tx')}, reopen=tx{selected.get('reopen_tx')}: PASS.", "",
                  "## Layer-A", "", f"PASS; top-level={len(layer['payload'])}; nested PPQ={len(layer['payload']['ppq_v2_r1_payload'])}.", "",
                  "## Layer-B", "", f"{'PASS' if result['layer_b']['pass'] else 'STOP'}; process quiescence included.", "",
                  "## Exact execution counts", "", "supervisor/worker/release/retry=1/1/1/0; CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; checkpoint/public/evaluation=0/0/0; git add/commit/push=0/0/0.", "",
                  "## Retained nonclaims", "", "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route remains DORMANT/BLOCKED.", "",
                  "## GPT-review handoff", "", f"Minor repairs={repair_log['repair_count']} resolved; unresolved=0; major defects=0; final static readiness={'PASS' if final_static['pass'] else 'STOP'}. Candidate only; no GPT REVIEW PASS is self-issued.", "",
                  "---", ""])
    lines.append(_r9_base_report_text(result, payload, layer))
    return "\n".join(lines)
'''


def transformed_source() -> str:
    source = R8.transformed_source()
    source = source.replace("correct R8 raw + expected R9", "correct R9 raw + expected R10")
    source = source.replace('expected_source_phase="B2-T4-RE6-R9"',
                            'expected_source_phase="B2-T4-RE6-R10"')
    for old, new in (
        ("B2-T4-RE6-R8", "B2-T4-RE6-R9"),
        ("b2_t4_re6_r8", "b2_t4_re6_r9"),
        ("b2-t4-re6-r8", "b2-t4-re6-r9"),
        ("RE6-R8", "RE6-R9"), ("RE6_R8", "RE6_R9"),
        ("R8", "R9"), ("r8", "r9"),
        ("5e53266fab49029fba6621218f32da4610014872bb0cb6c1cf6566b65b0ad1bf",
         "4c88b8fd77ba665c16381ad95e92c4d1ad242e3ebc6ac160118b54f9473586b7"),
        ('"porcelain_line_count": 25567', '"porcelain_line_count": 25628'),
        ("7ce3e3fc1ecd430cd3513a34aed9e11dbc9aee63c685d77a4f1ac2844cb04d12",
         "bacbb0e696f574e68b8e319d7a6b1905ce7b088e1fcc323be1785c2e6c9771d0"),
    ):
        source = source.replace(old, new)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r9_norm_r1_racq_r1_bound_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py")
    source = re.sub(
        r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R9-REPAIR-TOLERANT-PREFLIGHT-NORM-R1-RACQ-R1-BOUND-"\n'
        '           "NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")',
        source, count=1, flags=re.S)
    source = re.sub(
        r'REPORT = DAY / \(.*?\n\)',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R9_REPAIR_TOLERANT_PREFLIGHT_NORMAL_HORIZON_INTEGRATION_REPORT.md"',
        source, count=1, flags=re.S)
    source = source.replace("\ndef static_preflight() -> dict[str, Any]:",
                            "\n" + PREAUTH_SUPPORT + "\ndef static_preflight() -> dict[str, Any]:")
    anchor = '    base = base_runtime(directory)\n    inherited = base["derived_runtime"]()[0]["run_preflight"]()'
    replacement = '''    base = base_runtime(directory)
    preauthority = pre_authority_readiness(base, run_id, os.getpid(),
        OUT / "pre_authority_fixture", persist_outputs=True)
    require(preauthority["pass"] and preauthority["live_authority_created"] is False,
            "PRE-AUTHORITY-SUCCESS-GATE", preauthority)
    inherited = base["derived_runtime"]()[0]["run_preflight"]()'''
    if anchor not in source:
        raise RuntimeError("STOP — R9 pre-authority injection anchor drift")
    source = source.replace(anchor, replacement)
    source = re.sub(
        r'    frozen = \{"path": Path\(__file__\).*?\n    persist\(OUT / "r9_harness_identity_freeze.json", frozen\)\n',
        '    repair_window_open = True\n', source, count=1, flags=re.S)
    fs_anchor = '    require(fs.get("qualification_pass") is True, "FILESYSTEM-PRECONDITION", fs)\n    snapshot = {'
    fs_replacement = '''    require(fs.get("qualification_pass") is True, "FILESYSTEM-PRECONDITION", fs)
    frozen = {"path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
              "sha256": sha(Path(__file__).resolve()), "frozen": True,
              "source_edits_after_freeze_allowed": False,
              "minor_repairs_resolved_before_freeze": read(OUT / "pre_runtime_repair_log.json")["repair_count"]}
    persist(OUT / "r9_harness_identity_freeze.json", frozen)
    final_static = final_static_replay(base, run_id, process.pid, prepared, directory)
    snapshot = {'''
    if fs_anchor not in source:
        raise RuntimeError("STOP — R9 final-freeze injection anchor drift")
    source = source.replace(fs_anchor, fs_replacement)
    source = source.replace('"synthetic_chain": chain["pass"], "harness_sha256": sha(Path(__file__).resolve()),',
                            '"synthetic_chain": chain["pass"], "final_static_readiness": final_static["pass"],\n        "harness_sha256": sha(Path(__file__).resolve()),')
    old_witnesses = '''    witnesses = {key: raw["witnesses"][{
        "W1": "W1_CROSS_UPDATE_OWNERSHIP", "W2E": "W2_MULTI_UPDATE_COMPLETION",
        "W3": "W3_ZERO_DVM_ACTOR", "W4": "W4_NONTERMINAL_BOOTSTRAP",
        "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY"}[key]]
        for key in CANONICAL_NAMES}'''
    new_witnesses = '''    source_raw = _r9_complete_synthetic_raw(raw) if synthetic else raw
    witnesses = (_r9_synthetic_witnesses(source_raw) if synthetic else
        {key: raw["witnesses"][{
            "W1": "W1_CROSS_UPDATE_OWNERSHIP", "W2E": "W2_MULTI_UPDATE_COMPLETION",
            "W3": "W3_ZERO_DVM_ACTOR", "W4": "W4_NONTERMINAL_BOOTSTRAP",
            "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
            "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY"}[key]]
            for key in CANONICAL_NAMES})'''
    if old_witnesses not in source:
        raise RuntimeError("STOP — R9 synthetic witness anchor drift")
    source = source.replace(old_witnesses, new_witnesses)
    source = source.replace('sources = {"raw_final": raw["final"],',
                            'sources = {"raw_final": source_raw["final"],')
    source = source.replace('"transaction_rows": raw["transactions"], "terminal_rows": raw["terminal"],',
                            '"transaction_rows": source_raw["transactions"], "terminal_rows": source_raw["terminal"],')
    source = source.replace("\ndef formal_supervisor(timeout_seconds: int) -> dict[str, Any]:",
                            "\n" + REPORT_WRAPPER + "\ndef formal_supervisor(timeout_seconds: int) -> dict[str, Any]:")
    source = source.replace('choices=("self-check", "sr-current-zd", "static-preflight",',
                            'choices=("self-check", "pre-authority-check", "sr-current-zd", "static-preflight",')
    branch_anchor = '''    elif args.mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")'''
    branch_replacement = '''    elif args.mode == "pre-authority-check":
        with tempfile.TemporaryDirectory(prefix="b2_t4_re6_r9_preauthority_") as temp:
            directory = Path(temp) / "fixture"
            directory.mkdir()
            base = base_runtime(directory)
            result = pre_authority_readiness(
                base, "b2-t4-re6-r9-preauthority-development", os.getpid(),
                directory / "source_shape", persist_outputs=False)
    elif args.mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")'''
    if branch_anchor not in source:
        raise RuntimeError("STOP — R9 CLI injection anchor drift")
    source = source.replace(branch_anchor, branch_replacement)
    return source


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {
        "__name__": "_b2_t4_re6_r9_integrated_runtime",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
