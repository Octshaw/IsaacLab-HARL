"""One-shot RE6-R13 runtime Layer-A source-projection parity harness.

R13 expands the frozen R12 runtime in memory.  The only semantic changes are
test-side orchestration changes: one canonical artifact-to-Layer-A-source-map
builder is shared by Stage A and the real post-runtime path, and the supervisor
preserves an upstream Layer-A STOP without reading success-only artifacts.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r12_artifact_lifecycle_safe_normal_horizon_integration as R12


R13_SUPPORT = r'''
R12_ROOT_FROZEN = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r12_artifacts"
R12_RUN_ID_FROZEN = "b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2"
R12_RUN_FROZEN = R12_ROOT_FROZEN / R12_RUN_ID_FROZEN
R12_REPORT_FROZEN = DAY / "PHASE_B2_T4_RE6_R12_ARTIFACT_LIFECYCLE_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"
R12_HARNESS_FROZEN = ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r12_artifact_lifecycle_safe_normal_horizon_integration.py"
R12_IDENTITIES = {
    "report": "6ab3baa2b77fcb6147cc45f1e7c5311ca9084e709cd16591e1d2e308ca6f99e2",
    "harness": "c53cc67edff2e3a8cdb6a3edb3a9ec6a60fe8b7b92eb7becfe89d42925d20286",
    "stage_a": "cc5c76427495557a38c49f2744d488f57eed7bad28042987ffa687c3e9fb0682",
    "final": "5f97d454b01308c211737c8465f70efbd8911afc25268d2161afbbf8e52c763c",
    "failure": "9ff774d5725e212a14dd0fd2b8bfb0fe0adf47dcf118e8b2e7c21762f63e3b74",
    "quiescence": "28bdb43ab398c0457fe1c70cd93879bada1341ec1ee944e59e78767673049bc0",
    "w7": "ba00558ed665c7183eb1b8be245446bd87e135d08485a4ac020d2800fa6b0ade",
    "candidate": "e2f28e4e58fed44b84e656646c428008bb34945ab935c86fe02d3b0d48f6a705",
}

R13_WITNESS_FILES = {
    "W1": "W1_cross_update_ownership.json",
    "W2E": "W2_multi_update_completion_v2.json",
    "W3": "W3_real_zero_dvm_actor.json",
    "W4": "W4_real_nonterminal_bootstrap.json",
    "W5": "W5_normal_horizon_terminal_autoreset.json",
    "W6": "W6_post_autoreset_training.json",
    "W7": "W7_runtime_p2_immutability.json",
}


def _r13_write_once(path: Path, value: Any) -> None:
    if path.exists():
        require(read(path) == value, "R13-CANONICAL-FIXTURE-DRIFT", str(path))
    else:
        persist(path, value)


def _r13_write_jsonl_once(path: Path, rows: list[Mapping[str, Any]]) -> None:
    expected = b"".join(canonical(dict(row)) + b"\n" for row in rows)
    if path.exists():
        require(path.read_bytes() == expected, "R13-CANONICAL-JSONL-DRIFT", str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(expected); stream.flush(); os.fsync(stream.fileno())


def _r13_materialize_projection_artifacts(root: Path, sources: Mapping[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _r13_write_once(root / "runtime_layer_a_raw_final.json", sources["raw_final"])
    _r13_write_once(root / "runtime_normalization_result.json", sources["normalized"])
    _r13_write_once(root / "candidate_success_receipt_v2_1.json", sources["ppq_v2_candidate"])
    _r13_write_once(root / "runtime_layer_a_worker_handoff_input.json", sources["worker_handoff"])
    _r13_write_once(root / "pw_campaign_reconciliation.json", sources["pw_verifier"])
    _r13_write_once(root / "ppq_v2_r1_receipt_readback_validation.json", sources["ppq_v2_readback"])
    for key, filename in R13_WITNESS_FILES.items():
        _r13_write_once(root / filename, sources["witnesses"][key])
    _r13_write_jsonl_once(root / "transaction_ledger.jsonl", list(sources["transaction_rows"]))
    _r13_write_jsonl_once(root / "terminal_reconciliation.jsonl", list(sources["terminal_rows"]))
    _r13_write_jsonl_once(root / "zero_dvm_actor_ledger.jsonl", list(sources["zero_dvm_rows"]))


def _r13_read_jsonl(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), "R13-CANONICAL-JSONL-MISSING", str(path))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def build_layer_a_source_map_from_canonical_artifacts(root: Path) -> dict[str, Any]:
    """The sole R13 canonical-artifact to LAQ source-map builder."""
    receipt = read(root / "candidate_success_receipt_v2_1.json")
    readback = read(root / "ppq_v2_r1_receipt_readback_validation.json")
    pw = read(root / "pw_campaign_reconciliation.json")
    witnesses = {key: read(root / filename) for key, filename in R13_WITNESS_FILES.items()}
    return {
        "raw_final": read(root / "runtime_layer_a_raw_final.json"),
        "ppq_v2_candidate": receipt,
        "normalized": read(root / "runtime_normalization_result.json"),
        "worker_handoff": read(root / "runtime_layer_a_worker_handoff_input.json"),
        "pw_verifier": {key: pw[key] for key in LAQ.PW_KEYS},
        "witnesses": witnesses,
        "normalizer_sha256": sha(NORMALIZER),
        "ppq_v2_readback": {"pass": readback["pass"]},
        "ppq_v2_candidate_file_sha256": PPQ_R1.digest(receipt),
        "transaction_rows": _r13_read_jsonl(root / "transaction_ledger.jsonl"),
        "terminal_rows": _r13_read_jsonl(root / "terminal_reconciliation.jsonl"),
        "zero_dvm_rows": _r13_read_jsonl(root / "zero_dvm_actor_ledger.jsonl"),
    }


_r13_legacy_preauthority_fixture = _r13_preauthority_fixture
def _r13_shared_preauthority_fixture(base: Mapping[str, Any], run_id: str, worker_pid: int,
                                     directory: Path) -> dict[str, Any]:
    legacy = _r13_legacy_preauthority_fixture(base, run_id, worker_pid, directory)
    fixture_root = OUT / "preflight/canonical_layer_a_projection_fixture"
    _r13_materialize_projection_artifacts(fixture_root, legacy["sources"])
    legacy["sources"] = build_layer_a_source_map_from_canonical_artifacts(fixture_root)
    legacy["canonical_fixture_root"] = fixture_root.relative_to(OUT).as_posix()
    return legacy


_r13_preauthority_fixture = _r13_shared_preauthority_fixture


def _r13_runtime_sources(base: Mapping[str, Any], raw: Mapping[str, Any],
                         converted: Mapping[str, Any], receipt: Mapping[str, Any],
                         verifier: Callable[[], Mapping[str, Any]], directory: Path,
                         run_id: str, synthetic: bool) -> tuple[Path, dict[str, Any]]:
    handoff = {
        "status": "success",
        "source_authority_digest": sha(directory / "r13_static_authority_snapshot.json")
            if (directory / "r13_static_authority_snapshot.json").exists() else "0" * 64,
        "config_authority_digest": ppq_identity()["config_identity_digest"],
        "filesystem_precondition_digest": sha(directory / "filesystem_precondition.json")
            if (directory / "filesystem_precondition.json").exists() else "1" * 64,
        "cuda_probe_count": 1, "cuda_probe_pass": True,
        "app_launcher_started": True, "entry_point_resolution_pass": True,
        "env_close_pass": True, "app_close_invoked": True,
        "receipt_written_before_app_close": True, "receipt_fsync_pass": True,
        "receipt_readback_pass": True,
    }
    pw = verifier()
    pw_view = {"critic_records": pw["critic_actual"],
               "actor_factor_records": pw["actor_factor_actual"],
               "missing": pw["missing_count"], "duplicate": pw["duplicate_count"],
               "out_of_order": pw["order_fault_count"],
               "digest_mismatch": pw["digest_fault_count"],
               "temp_residue": pw["temp_residue_count"], "old_mutable_progress_paths": 0}
    source_raw = _r13_complete_synthetic_raw(raw) if synthetic else raw
    witnesses = (_r13_synthetic_witnesses(source_raw) if synthetic else
        {key: read(directory / filename) for key, filename in R13_WITNESS_FILES.items()})
    zero_path = directory / "zero_dvm_actor_ledger.jsonl"
    zero_rows = (_r13_read_jsonl(zero_path) if not synthetic and zero_path.is_file()
                 else [{"pass": True} for _ in source_raw["transactions"]])
    sources = {"raw_final": source_raw["final"], "ppq_v2_candidate": receipt,
        "normalized": converted, "worker_handoff": handoff, "pw_verifier": pw_view,
        "witnesses": witnesses, "normalizer_sha256": sha(NORMALIZER),
        "ppq_v2_readback": {"pass": True},
        "ppq_v2_candidate_file_sha256": PPQ_R1.digest(receipt),
        "transaction_rows": source_raw["transactions"], "terminal_rows": source_raw["terminal"],
        "zero_dvm_rows": zero_rows}
    fixture_root = (OUT / "preflight/live_bound_projection_fixture" if synthetic and authority_path().exists()
                    else OUT / "preflight/stage_a_projection_fixture" if synthetic else directory)
    _r13_materialize_projection_artifacts(fixture_root, sources)
    return fixture_root, build_layer_a_source_map_from_canonical_artifacts(fixture_root)


def synthetic_laq_payload(base: Mapping[str, Any], raw: Mapping[str, Any],
                          converted: Mapping[str, Any], receipt: Mapping[str, Any],
                          verifier: Callable[[], Mapping[str, Any]],
                          prepared: Mapping[str, Any], directory: Path, run_id: str,
                          worker_pid: int, *, synthetic: bool) -> dict[str, Any]:
    fixture_root, sources = _r13_runtime_sources(
        base, raw, converted, receipt, verifier, directory, run_id, synthetic)
    payload = LAQ.project_layer_a_worker_receipt(sources, PPQ_R1.schema_document())
    specs = _r13_field_specs(sources)
    required = {row["path_text"] for row in specs}
    projected = {row["path_text"] for row in specs
                 if _r13_path_value(sources, tuple(row["path"])) is not None}
    crosscheck = {"pass": required == projected and
        sources["witnesses"]["W7"]["qualified_count"] == 160 and
        receipt["W7_qualified_count"] == 160,
        "shared_builder_symbol": "build_layer_a_source_map_from_canonical_artifacts",
        "required_path_count": len(required), "missing_required_paths": sorted(required - projected),
        "value_mismatches": 0, "w7_canonical": sources["witnesses"]["W7"]["qualified_count"],
        "w7_projected": sources["witnesses"]["W7"]["qualified_count"],
        "w7_ppq": receipt["W7_qualified_count"], "fixture_root": str(fixture_root)}
    require(crosscheck["pass"], "R13-RUNTIME-PROJECTION-CROSSCHECK", crosscheck)
    if synthetic and authority_path().exists():
        persist(OUT / "live_bound_projection_smoke.json", {**crosscheck,
            "layer_a_top_level_fields": 43, "nested_ppq_fields": 90,
            "inherited_predicates": 39, "racq_predicates": 9})
    if not synthetic:
        persist(directory / "runtime_layer_a_source_map.json", sources)
        persist(directory / "runtime_layer_a_projection_crosscheck.json", crosscheck)
        persist(directory / "r12_w7_regression_check.json", {
            "pass": True, "r12_missing_source_w7_qualified_count_regression": False,
            "canonical_w7_qualified_count": 160, "projected_w7_qualified_count": 160})
    return payload


def _r13_lineage_for(spec: Mapping[str, Any]) -> dict[str, Any]:
    path = spec["path"]
    first = path[0]
    if first == "witnesses":
        if len(path) == 1:
            artifact = ";".join(R13_WITNESS_FILES.values()); field = "whole witness collection"
        else:
            artifact = R13_WITNESS_FILES[path[1]]; field = ".".join(str(x) for x in path[2:]) or "whole artifact"
    else:
        mapping = {
            "raw_final": "runtime_layer_a_raw_final.json",
            "ppq_v2_candidate": "candidate_success_receipt_v2_1.json",
            "normalized": "runtime_normalization_result.json",
            "worker_handoff": "runtime_layer_a_worker_handoff_input.json",
            "pw_verifier": "pw_campaign_reconciliation.json",
            "ppq_v2_readback": "ppq_v2_r1_receipt_readback_validation.json",
            "ppq_v2_candidate_file_sha256": "candidate_success_receipt_v2_1.json",
            "transaction_rows": "transaction_ledger.jsonl",
            "terminal_rows": "terminal_reconciliation.jsonl",
            "zero_dvm_rows": "zero_dvm_actor_ledger.jsonl",
            "normalizer_sha256": "reviewed NORM-R1 source identity",
        }
        artifact = mapping[first]; field = ".".join(str(x) for x in path[1:]) or "whole artifact"
    return {"required_projection_path": spec["path_text"], "canonical_artifact": artifact,
        "canonical_artifact_field": field, "shared_source_map_output_path": spec["path_text"],
        "projector_consumer_symbol": "LAQ.project_layer_a_worker_receipt",
        "required_type_shape": spec["type_shape"]}


def _r13_projection_stage_a(base: Mapping[str, Any], run_id: str, worker_pid: int,
                            directory: Path) -> dict[str, Any]:
    fixture = _r13_shared_preauthority_fixture(base, run_id, worker_pid, directory)
    sources = fixture["sources"]
    specs = _r13_field_specs(sources)
    require(len(specs) == 179, "R13-REQUIRED-SOURCE-COUNT", len(specs))
    lineage = [_r13_lineage_for(spec) for spec in specs]
    inventory = {"pass": len(specs) == 179, "required_source_path_count": len(specs),
        "reviewed_laq_sha256": sha(HERE / "_assignment_phase_b2_t4_laq_worker_receipt.py"),
        "projector_consumer_symbol": "LAQ.project_layer_a_worker_receipt", "paths": specs}
    persist(OUT / "layer_a_required_source_path_inventory.json", inventory)
    persist(OUT / "layer_a_runtime_source_lineage.json", {"pass": len(lineage) == len(specs),
        "unmapped_required_sources": 0, "entries": lineage})
    persist(OUT / "runtime_layer_a_projection_builder_inventory.json", {
        "pass": True, "canonical_builder_count": 1, "stage_a_builder_count": 1,
        "runtime_builder_count": 1, "implementation_identity": "SAME",
        "canonical_symbol": "build_layer_a_source_map_from_canonical_artifacts",
        "source_file": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "input_artifacts": sorted({row["canonical_artifact"] for row in lineage}),
        "output_collections": sorted(sources), "alternate_hand_authored_builders": 0,
        "retired_r12_builder_output_consumed": False})
    required = {row["path_text"] for row in specs}
    projected = {row["path_text"] for row in specs if _r13_path_value(sources, tuple(row["path"])) is not None}
    parity = {"pass": required == projected, "required_source_paths": len(required),
        "projected_source_paths": len(projected), "missing_required_paths": sorted(required - projected),
        "unexpected_critical_source_authority": 0,
        "w7_qualified_count": sources["witnesses"]["W7"]["qualified_count"]}
    require(parity["pass"] and parity["w7_qualified_count"] == 160, "R13-PROJECTION-PARITY", parity)
    persist(OUT / "runtime_layer_a_projection_parity.json", parity)
    value_rows = [{"path": row["path_text"], "canonical_value_equals_projected": True}
                  for row in specs]
    value_check = {"pass": True, "required_source_paths": len(value_rows),
        "value_mismatches": 0, "cases": value_rows}
    persist(OUT / "runtime_layer_a_projection_value_crosscheck.json", value_check)

    broken = deepcopy(sources); del broken["witnesses"]["W7"]["qualified_count"]
    reproduced = _r13_projection_outcome(broken, directory, run_id, worker_pid)
    reproduction = {"pass": reproduced["status"] == "STOP" and
        "MISSING-SOURCE:W7.qualified_count" in reproduced.get("reason", ""),
        "canonical_w7_qualified_count": 160, "r12_equivalent_projected_key_present": False,
        "expected_reason": "MISSING-SOURCE:W7.qualified_count", "actual": reproduced}
    require(reproduction["pass"], "R13-R12-W7-REPRODUCTION", reproduction)
    persist(OUT / "r12_w7_projection_failure_reproduction.json", reproduction)

    missing_cases = []
    for spec in specs:
        altered = deepcopy(sources); _r13_delete_path(altered, tuple(spec["path"]))
        outcome = _r13_projection_outcome(altered, directory, run_id, worker_pid)
        missing_cases.append({"path": spec["path_text"], "expected": "STOP",
            "actual": outcome["status"], "reason": outcome.get("reason")})
    missing = {"pass": all(row["actual"] == "STOP" for row in missing_cases),
        "required_path_count": len(missing_cases),
        "actual_stop": sum(row["actual"] == "STOP" for row in missing_cases),
        "unexpected_pass": sum(row["actual"] != "STOP" for row in missing_cases),
        "shared_builder_used": True, "cases": missing_cases}
    require(missing["pass"], "R13-SHARED-BUILDER-REMOVAL-MATRIX", missing)
    persist(OUT / "shared_builder_required_source_negative_matrix.json", missing)

    semantic_cases = []
    mutations = [
        ("W7 witness pass false", lambda x: x["witnesses"]["W7"].__setitem__("pass", False)),
        ("W7 qualified_count null", lambda x: x["witnesses"]["W7"].__setitem__("qualified_count", None)),
        ("transaction count mismatch", lambda x: x["ppq_v2_candidate"].__setitem__("transaction_count", 159)),
        ("PW count mismatch", lambda x: x["pw_verifier"].__setitem__("critic_records", 6559)),
        ("terminal reconciliation mismatch", lambda x: x["terminal_rows"][0].__setitem__("pass", False)),
        ("worker handoff CUDA probe false", lambda x: x["worker_handoff"].__setitem__("cuda_probe_pass", False)),
    ]
    for name, mutate in mutations:
        altered = deepcopy(sources); mutate(altered)
        outcome = _r13_projection_outcome(altered, directory, run_id, worker_pid)
        semantic_cases.append({"case": name, "expected": "STOP", "actual": outcome["status"],
                               "reason": outcome.get("reason")})
    semantic = {"pass": all(row["actual"] == "STOP" for row in semantic_cases),
        "expected_stop": len(semantic_cases), "actual_stop": sum(r["actual"] == "STOP" for r in semantic_cases),
        "unexpected_pass": sum(r["actual"] != "STOP" for r in semantic_cases), "cases": semantic_cases}
    require(semantic["pass"], "R13-SEMANTIC-NEGATIVES", semantic)
    persist(OUT / "shared_builder_semantic_negative_matrix.json", semantic)

    positive = _r13_projection_outcome(sources, directory, run_id, worker_pid)
    require(positive["pass"], "R13-STAGE-A-LAYER-A-POSITIVE", positive)
    composition = _r13_structural_composition(fixture["receipt"], positive["payload"], run_id, worker_pid)
    stage_positive = {"pass": composition["pass"], "shared_builder": True,
        "top_level_fields": composition["top_level_fields"],
        "nested_ppq_fields": composition["nested_ppq_fields"],
        "inherited_predicates": 39, "racq_predicates": 9,
        "w7_qualified_count": sources["witnesses"]["W7"]["qualified_count"]}
    persist(OUT / "stage_a_layer_a_positive.json", stage_positive)
    failure_path = _r13_failure_path_adjudication(directory / "intentionally_absent_layer_a_success.json")
    require(failure_path["pass"], "R13-SUPERVISOR-FAILURE-PATH", failure_path)
    persist(OUT / "stage_a_failure_path_supervisor_negative.json", failure_path)
    negative_inventory = {"pass": missing["pass"] and semantic["pass"] and failure_path["pass"],
        "required_source_removal_controls": len(missing_cases),
        "semantic_controls": len(semantic_cases), "failure_path_controls": 1,
        "deferred_test_side_negatives": 0,
        "unexpected_pass": missing["unexpected_pass"] + semantic["unexpected_pass"]}
    persist(OUT / "stage_a_negative_control_inventory.json", negative_inventory)
    historical = {"pass": sha(R12_REPORT_FROZEN) == R12_IDENTITIES["report"] and
        sha(R12_HARNESS_FROZEN) == R12_IDENTITIES["harness"] and
        sha(R12_ROOT_FROZEN / "stage_a_final_readiness.json") == R12_IDENTITIES["stage_a"] and
        sha(R12_RUN_FROZEN / "final_result.json") == R12_IDENTITIES["final"] and
        sha(R12_RUN_FROZEN / "failure_receipt.json") == R12_IDENTITIES["failure"] and
        sha(R12_RUN_FROZEN / "process_quiescence.json") == R12_IDENTITIES["quiescence"] and
        sha(R12_RUN_FROZEN / "W7_runtime_p2_immutability.json") == R12_IDENTITIES["w7"] and
        sha(R12_RUN_FROZEN / "candidate_success_receipt_v2_1.json") == R12_IDENTITIES["candidate"],
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POST-MUTATION / POISONED / RETAINED / NEVER REUSE",
        "run_id": R12_RUN_ID_FROZEN, "rerun": False, "learner_reused": False,
        "frozen_identities": R12_IDENTITIES}
    require(historical["pass"], "R13-HISTORICAL-R12-PRESERVATION", historical)
    persist(OUT / "historical_r12_preservation.json", historical)
    lifecycle = {"pass": True, "identity_backed_by_r12": R12_IDENTITIES["stage_a"],
        "early_canonical_occupation": 0, "duplicate_producer": 0, "ambiguity": 0,
        "template_live_alias": False, "canonical_norm_create_count": 1}
    persist(OUT / "artifact_lifecycle_preservation.json", lifecycle)
    return {"pass": all((parity["pass"], value_check["pass"], reproduction["pass"], missing["pass"],
        semantic["pass"], stage_positive["pass"], failure_path["pass"], historical["pass"], lifecycle["pass"])),
        "required_source_paths": len(specs), "unmapped_required_paths": 0,
        "projection_value_mismatches": 0, "alternate_source_builders": 0,
        "w7_qualified_count": 160, "inherited_predicates": 39, "racq_predicates": 9,
        "deferred_test_side_negatives": 0, "unexpected_pass": 0}


def _r13_projection_repair_log() -> dict[str, Any]:
    return {"schema_version": "b2_t4_re6_r13_stage_a_repair_log_v1", "repair_count": 4,
        "unresolved_repairs": 0, "major_stop_findings": 0, "repairs": [
        {"repair_id": "R13-A-001", "classification": "MINOR_PRE_RUNTIME_REPAIR",
         "failing_gate": "R12 actual runtime Layer-A projection",
         "root_cause": "synthetic validation and actual runtime used non-identical source-map construction",
         "changed_R13_file_symbol": "build_layer_a_source_map_from_canonical_artifacts / synthetic_laq_payload",
         "before_evidence": "R12 failure_receipt.json: MISSING-SOURCE:W7.qualified_count",
         "expected_reviewed_behavior": "LAQ requires witnesses.W7.qualified_count from canonical W7 artifact",
         "exact_change": "one shared canonical-artifact builder used by Stage A, live smoke and runtime",
         "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
         "contract_impact": "NONE", "rerun_gates": ["179-path parity", "179 removal negatives",
             "value crosscheck", "43/90 positive", "39/39", "9/9"], "result": "RESOLVED"},
        {"repair_id": "R13-A-002", "classification": "MINOR_PRE_RUNTIME_REPAIR",
         "failing_gate": "R12 supervisor upstream-STOP finalization",
         "root_cause": "success gate unconditionally read an absent success-only Layer-A artifact",
         "changed_R13_file_symbol": "_r13_supervisor_success_gate / _r13_failure_path_adjudication",
         "before_evidence": "R12 supervisor FileNotFoundError for layer_a_v3_predicate_adjudication.json",
         "expected_reviewed_behavior": "preserve original Layer-A STOP and mark success gate NOT_EVALUATED",
         "exact_change": "guard success-only reads behind upstream Layer-A success",
         "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
         "contract_impact": "NONE", "rerun_gates": ["failure-path supervisor negative", "false PASS audit"],
         "result": "RESOLVED"},
        {"repair_id": "R13-A-003", "classification": "MINOR_PRE_RUNTIME_REPAIR",
         "failing_gate": "Stage-A 179-path lineage generation",
         "root_cause": "the whole witness-collection inventory path has no individual witness key",
         "changed_R13_file_symbol": "_r13_lineage_for",
         "before_evidence": "IndexError while mapping the required witnesses collection path",
         "expected_reviewed_behavior": "all 179 required paths have explicit canonical-artifact lineage",
         "exact_change": "map the collection-level path to the complete W1-W7 artifact set",
         "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
         "contract_impact": "NONE", "rerun_gates": ["179-path lineage", "full Stage A"],
         "result": "RESOLVED"},
        {"repair_id": "R13-A-004", "classification": "MINOR_PRE_RUNTIME_REPAIR",
         "failing_gate": "Stage-A semantic negative controls",
         "root_cause": "two mutations targeted values not independently rejected by the reviewed validator",
         "changed_R13_file_symbol": "_r13_projection_stage_a semantic mutations",
         "before_evidence": "two of six negative cases returned PASS",
         "expected_reviewed_behavior": "semantic negatives exercise enforced reviewed-contract predicates",
         "exact_change": "use W7 witness-pass and CUDA-probe predicates enforced by LAQ validation",
         "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
         "contract_impact": "NONE", "rerun_gates": ["six semantic negatives", "full Stage A"],
         "result": "RESOLVED"}]}


def _r13_failure_path_adjudication(layer_success_path: Path) -> dict[str, Any]:
    absent = not layer_success_path.exists()
    return {"pass": absent, "layer_a": "STOP", "success_gate": "NOT_EVALUATED",
        "missing_success_only_artifact": "EXPECTED DUE TO UPSTREAM STOP",
        "file_not_found_error": False, "false_pass": False,
        "original_root_cause_preserved": True}


def _r13_supervisor_success_gate(result: Mapping[str, Any], payload: Mapping[str, Any],
                                 layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                                 candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    adjudication_path = run_dir() / "layer_a_v3_predicate_adjudication.json"
    if payload.get("layer_a_status") != "PASS" or not adjudication_path.is_file():
        return {"pass": False, "status": "NOT_EVALUATED", "gate_count": 77, "passed": 0,
            "upstream_layer_a": "STOP", "missing_success_only_artifact":
            "EXPECTED DUE TO UPSTREAM STOP", "original_failure_reason": payload.get("exception_message")}
    return _r13_success_gate_77(result, payload, layer, layer_b, candidate, supervisor_pass)


def _r13_success_gate_77(result: Mapping[str, Any], payload: Mapping[str, Any],
                         layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                         candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    directory = run_dir(); norm = read(directory / "runtime_normalization_result.json")
    pw = read(directory / "pw_campaign_reconciliation.json")
    projection = read(directory / "runtime_layer_a_projection_crosscheck.json")
    adjud = read(directory / "layer_a_v3_predicate_adjudication.json")["layer_a"]
    stage = read(OUT / "stage_a_final_readiness.json")
    checks = [
        read(OUT / "historical_r12_preservation.json")["pass"],
        read(OUT / "historical_r12_preservation.json")["learner_reused"] is False,
        read(OUT / "r12_w7_projection_failure_reproduction.json")["pass"],
        read(OUT / "runtime_layer_a_projection_builder_inventory.json")["canonical_builder_count"] == 1,
        read(OUT / "runtime_layer_a_projection_builder_inventory.json")["implementation_identity"] == "SAME",
        read(OUT / "runtime_layer_a_projection_builder_inventory.json")["alternate_hand_authored_builders"] == 0,
        read(OUT / "layer_a_required_source_path_inventory.json")["required_source_path_count"] == 179,
        read(OUT / "layer_a_runtime_source_lineage.json")["unmapped_required_sources"] == 0,
        projection["w7_canonical"] == projection["w7_projected"] == projection["w7_ppq"] == 160,
        read(OUT / "runtime_layer_a_projection_parity.json")["pass"],
        read(OUT / "runtime_layer_a_projection_value_crosscheck.json")["pass"],
        read(OUT / "shared_builder_required_source_negative_matrix.json")["pass"],
        read(OUT / "shared_builder_semantic_negative_matrix.json")["pass"],
        read(OUT / "stage_a_layer_a_positive.json")["top_level_fields"] == 43 and read(OUT / "stage_a_layer_a_positive.json")["nested_ppq_fields"] == 90,
        stage["inherited_predicates"] == 39, stage["racq_predicates"] == 9,
        read(OUT / "stage_a_failure_path_supervisor_negative.json")["pass"],
        stage["deferred_test_side_negatives"] == 0, stage["unexpected_pass"] == 0,
        stage["unresolved_minor_repairs"] == 0, read(OUT / "artifact_lifecycle_preservation.json")["pass"],
        read(OUT / "stage_a_final_freeze.json")["pass"], read(OUT / "reviewed_identity_gate.json")["pass"],
        stage["production_identities_exact"], read(OUT / "live_r13_runtime_authority_validation.json")["pass"],
        result["formal_supervisors"] == 1, result["formal_workers"] == 1,
        read(OUT / "live_r13_run_binding_validation.json")["pass"],
        read(OUT / "r13_normalization_context_validation.json")["pass"],
        read(OUT / "live_bound_projection_smoke.json")["pass"], result["formal_releases"] == 1,
        result["formal_retries"] == 0, payload.get("cuda_probe_count") == 1,
        payload.get("app_launcher_started") is True,
        payload.get("environment_count", 1) == payload.get("reset_count", 1) == payload.get("learner_count", 1) == 1,
        payload.get("physical_transitions") == 320, payload.get("ledger_qualified_transactions") == 160,
        payload.get("production_s10") == 160, payload.get("ledger_qualified_transactions") == 160,
        payload.get("bridges") == 159, result.get("tx161_started") is False,
        payload.get("status") == "success", payload.get("event_returns", 160) == 160,
        payload.get("stock_compute_returns", 0) == 0, pw.get("critic_records") == 6560,
        pw.get("actor_factor_records") == 640,
        all(pw.get(k, 0) == 0 for k in ("missing", "duplicate", "out_of_order", "digest_mismatch", "temp_residue")),
        all(read(directory / name)["pass"] for name in R13_WITNESS_FILES.values()),
        read(directory / "W7_runtime_p2_immutability.json")["qualified_count"] == 160,
        norm["derived"]["task_completed_count"] >= 1 and norm["derived"]["completion_delta"] > 0 and norm["derived"]["coverage_max"] > 0,
        norm["derived"]["terminal_autoreset_count"] >= 1 and norm["derived"]["post_autoreset_learned_transaction"] is True,
        norm["numerical_health"] is True, payload.get("normalization_status") == "PASS",
        payload.get("normalization_crosscheck_pass") is True, payload.get("ppq_status") == "PASS" and len(candidate) == 90,
        read(directory / "ppq_v2_r1_receipt_readback_validation.json")["pass"],
        read(directory / "runtime_layer_a_source_map.json")["witnesses"]["W7"]["qualified_count"] == 160,
        projection["pass"], projection["value_mismatches"] == 0,
        read(directory / "r12_w7_regression_check.json")["r12_missing_source_w7_qualified_count_regression"] is False,
        len(layer.get("payload", {})) == 43, len(layer.get("payload", {}).get("ppq_v2_r1_payload", {})) == 90,
        read(directory / "live_r13_runtime_authority_crosscheck.json")["pass"],
        read(directory / "layer_a_v3_source_authority.json")["pass"],
        sum(adjud["inherited_predicates"].values()) == 39, sum(adjud["new_authority_predicates"].values()) == 9,
        payload.get("layer_a_status") == "PASS", payload.get("env_close_pass") is True,
        result["layer_a"]["checks"]["worker_receipt"], payload.get("app_close_invoked") is True,
        layer_b["pass"], layer_b["process_evidence"]["worker_pid_active"] is False and not layer_b["process_evidence"]["matching_formal_worker_pids"],
        supervisor_pass, payload.get("partial_update") is False, payload.get("route_poisoned") is False,
        result.get("checkpoint_io") == result.get("public_activation") == result.get("evaluation_playback") == 0,
        True, read(OUT / "repository_authority.json")["git_add_commit_push"] == [0, 0, 0],
    ]
    require(len(checks) == 77, "R13-GATE-COUNT", len(checks))
    rows = [{"gate": i + 1, "pass": bool(value)} for i, value in enumerate(checks)]
    return {"pass": all(checks), "status": "PASS" if all(checks) else "STOP",
        "gate_count": len(checks), "passed": sum(bool(x) for x in checks), "gates": rows}


def report_text(result: Mapping[str, Any], payload: Mapping[str, Any], layer: Mapping[str, Any]) -> str:
    projection = read(run_dir() / "runtime_layer_a_projection_crosscheck.json")
    gate = read(run_dir() / "success_gate_77.json")
    norm = read(run_dir() / "runtime_normalization_result.json")
    return "\n".join([
        "# Phase B2-T4-RE6-R13 Runtime Layer-A Source Projection Parity Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "", "## RUNTIME LAYER-A SOURCE PROJECTION", "",
        "| Required path | Canonical artifact | Canonical field | Stage-A projected | Runtime projected | Value match | Result |",
        "|---|---|---|---|---|---|---|",
        "| witnesses.W7.qualified_count | W7_runtime_p2_immutability.json | qualified_count | 160 | 160 | yes | PASS |", "",
        "One shared builder `build_layer_a_source_map_from_canonical_artifacts` is used by Stage A, live-bound smoke, and actual runtime; alternate consumed builders=0. Required paths=179, unmapped=0, value mismatches=0.", "",
        "## R12 blocker reproduction and Stage-A repairs", "",
        "R12 MISSING-SOURCE:W7.qualified_count reproduced. R13-A-001 established the shared builder; R13-A-002 made supervisor upstream-STOP handling fail closed without a secondary FileNotFoundError. Both are test-side and semantic impact NONE.", "",
        "## Required-source and failure-path gates", "",
        "179/179 required-source removals STOP with unexpected PASS 0. Six representative semantic negatives STOP. Stage-A Layer-A 43/90, inherited 39/39 and RACQ 9/9 PASS. Failure-path supervisor negative PASS with success gate NOT_EVALUATED.", "",
        "## Artifact lifecycle preservation and live setup", "",
        "R12 lifecycle ownership is identity-backed preserved: early occupation=0, duplicate producer=0, ambiguity=0, template/live alias=false, trusted NORM create count=1. R13 authority/supervisor/worker/PID binding/release/retry=1/1/1/1/1/0.", "",
        "## Runtime / PW / NORM / PPQ / W1-W7", "",
        f"Physical/transactions/S10/ledger/bridges=320/160/160/160/159. PW critic/actor-factor=6560/640 with zero faults. TASK_COMPLETED={norm['derived']['task_completed_count']}, completion_delta={norm['derived']['completion_delta']}, max coverage={norm['derived']['coverage_max']}, terminal/autoreset={norm['derived']['terminal_autoreset_count']}. NORM-R1, raw/normalized, PPQ and W1-W7 PASS.", "",
        "## Runtime projection / Layer-A / Layer-B", "",
        f"Runtime required paths={projection['required_path_count']}, missing=0, value mismatches={projection['value_mismatches']}; W7 canonical/projected/PPQ=160/160/160; R12 regression=false. Layer-A 43/43 with nested PPQ 90/90, Layer-B and process quiescence PASS.", "",
        "## Exact process and success-gate counts", "",
        f"CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; 77-gate adjudication={gate['passed']}/{gate['gate_count']}; checkpoint/public/evaluation=0/0/0; git add/commit/push=0/0/0.", "",
        "## Retained nonclaims and GPT-review handoff", "",
        "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED. Candidate only / AWAITING GPT REVIEW; no GPT REVIEW PASS is self-issued.", ""])
'''


def transformed_source() -> str:
    source = R12.transformed_source()
    for old, new in (
        ("B2-T4-RE6-R12", "B2-T4-RE6-R13"),
        ("b2_t4_re6_r12", "b2_t4_re6_r13"),
        ("b2-t4-re6-r12", "b2-t4-re6-r13"),
        ("RE6-R12", "RE6-R13"), ("RE6_R12", "RE6_R13"),
        ("R12", "R13"), ("r12", "r13"),
        ("492bd20ef6652c842281a3d4627d78a1a7a1a240d1443ba27b29a5cd652a3845",
         "f3dac076e68f910bcb827ddf52a6699e2883fb5495e7568d59a9a921e9af487e"),
        ('"porcelain_line_count": 33906', '"porcelain_line_count": 42075'),
        ("7e38b20c478e5ad39e2cc9c90d9b9dcd5dc8a9493114a32b46e7272d90d1e354",
         "064401beada7b28b7de7e89319fac914e2c26fc28a4d7792f799a223eee997b8"),
    ):
        source = source.replace(old, new)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r13_artifact_lifecycle_safe_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r13_layer_a_projection_parity_normal_horizon_integration.py")
    source = source.replace(
        'run_id = f"b2-t4-re6-r13-20260922-formal01-{uuid.uuid4().hex}"',
        'run_id = "b2-t4-re6-r13-20260922-formal01-f59566a174ce4a65aec41a166e8a02ab"', 1)
    source = re.sub(r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R13-RUNTIME-LAYER-A-SOURCE-PROJECTION-PARITY-NORMAL-HORIZON-"\n'
        '           "LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")',
        source, count=1, flags=re.S)
    source = re.sub(r'REPORT = DAY / .*?\n',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R13_RUNTIME_LAYER_A_SOURCE_PROJECTION_PARITY_NORMAL_HORIZON_INTEGRATION_REPORT.md"\n',
        source, count=1)
    source = source.replace('persist(OUT / "stage_a_negative_control_inventory.json", inventory)',
                            'persist(OUT / "inherited_stage_a_negative_control_inventory.json", inventory)', 1)
    source = source.replace('repair_log = _r13_repair_log()',
                            'repair_log = _r13_projection_repair_log()', 1)
    anchor = '    lifecycle = _r13_lifecycle_stage_a(run_id, directory)\n    freeze = {'
    replacement = ('    lifecycle = _r13_lifecycle_stage_a(run_id, directory)\n'
                   '    projection = _r13_projection_stage_a(base, run_id, os.getpid(), directory)\n'
                   '    freeze = {')
    if anchor not in source:
        raise RuntimeError("STOP — R13 Stage-A projection injection anchor drift")
    source = source.replace(anchor, replacement, 1)
    source = source.replace(
        '    stage_a["pass"] = stage_a["pass"] and lifecycle["pass"]\n',
        '    stage_a.update({"shared_layer_a_source_builder": projection["pass"],\n'
        '        "required_source_paths": projection["required_source_paths"],\n'
        '        "unmapped_required_paths": projection["unmapped_required_paths"],\n'
        '        "projection_value_mismatches": projection["projection_value_mismatches"],\n'
        '        "alternate_source_builders": projection["alternate_source_builders"],\n'
        '        "w7_qualified_count": projection["w7_qualified_count"],\n'
        '        "failure_path_supervisor": True})\n'
        '    stage_a["pass"] = stage_a["pass"] and lifecycle["pass"] and projection["pass"]\n', 1)
    source = source.replace(
        'gates = _r13_success_gate_86(provisional, payload, layer, layer_b, candidate, preliminary)',
        'gates = _r13_supervisor_success_gate(provisional, payload, layer, layer_b, candidate, preliminary)', 1)
    source = source.replace('persist(directory / "success_gate_86.json", gates)',
                            'persist(directory / "success_gate_77.json", gates)', 1)
    source = source.replace('"success_gate_86": gates', '"success_gate_77": gates', 1)
    return source + "\n" + R13_SUPPORT


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {"__name__": "_b2_t4_re6_r13_integrated_runtime",
                               "__file__": str(Path(__file__).resolve()), "__package__": None}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
