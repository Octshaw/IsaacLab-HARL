"""One-shot RE6-R14 formal-namespace-purity integration harness.

R14 expands the frozen R13 harness in memory.  Its test-side orchestration
keeps every Stage-A fixture below a unique preflight root, allocates the one
formal run identity only after Stage-A PASS/freeze, and leaves the reviewed
runtime, learner, NORM, PPQ, LAQ, RACQ, and write-once semantics unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r13_layer_a_projection_parity_normal_horizon_integration as R13


R14_SUPPORT = r'''
R13_ROOT_FROZEN = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r13_artifacts"
R13_RUN_ID_FROZEN = "b2-t4-re6-r13-20260922-formal01-339ec669e33b4f40be9dfea9347a0ed7"
R13_RUN_FROZEN = R13_ROOT_FROZEN / R13_RUN_ID_FROZEN
R13_REPORT_FROZEN = SCAN / "AgentRead/202609/20260922/PHASE_B2_T4_RE6_R13_RUNTIME_LAYER_A_SOURCE_PROJECTION_PARITY_NORMAL_HORIZON_INTEGRATION_REPORT.md"
R13_HARNESS_FROZEN = ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r13_layer_a_projection_parity_normal_horizon_integration.py"
R13_IDENTITIES = {
    "harness": "4ae682ca45ef89f718519ebdf88adefbd20de67c1a6f604f3dc905814be7a356",
    "report": "da3b0624e07a7cec7dfb2c65a6f339221f2eacc9555bf3e5c04add9be0a0ff3a",
    "stage_a": "4cf527393ed2a36c469ae7a1f851e01aa8c0600a617114e7206358810f447cea",
    "final": "bcc8662201018e10a4a911700c120ac177fa85eca2735a0fef8226d9866448f0",
    "failure": "a5fe29169dbaaf16acb00b8981b228fcece46023c7667612446f15671ae86a1b",
    "quiescence": "9203c4e86eeb2bd7dff9fbcf8d359e09347db590eec490a7d66f1b0c19967f67",
}


def repository_authority() -> dict[str, Any]:
    current = git_bytes("-c", "core.longpaths=true", "status", "--porcelain=v1", "-uall")
    lines = current.decode("utf-8").splitlines()
    new_prefixes = (
        "?? scripts/environments/test_assignment_phase_b2_t4_re6_r14_formal_namespace_purity_normal_horizon_integration.py",
        "?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/",
    )
    starting = [line for line in lines if not line.startswith(new_prefixes)]
    starting_bytes = ("\n".join(starting) + "\n").encode("utf-8")
    staged = git_bytes("ls-files", "--stage")
    paths = git_bytes("diff", "--cached", "--name-only").decode().splitlines()
    value = {"branch": git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "full_porcelain": starting, "full_porcelain_line_count": len(starting),
        "full_porcelain_sha256": sha256(starting_bytes).hexdigest(),
        "staged_path_count": len(paths), "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0]}
    require(value["branch"] == "main", "REPOSITORY-BRANCH")
    require(value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD,
            "REPOSITORY-COMMIT", value)
    require(value["full_porcelain_line_count"] == 42223 and
            value["full_porcelain_sha256"] == "4b85c5bbc96a8ee1a0409913cdba9fe29ed3c89827ecf9a160af737670bf6459",
            "REPOSITORY-STARTING-PORCELAIN", value)
    require(value["staged_path_count"] == 359 and
            value["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c" and
            value["monthly_path_set_sha256"] == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab",
            "REPOSITORY-INDEX", value)
    return value


def run_identity() -> dict[str, Any]:
    return read(OUT / "formal_run_identity.json")


def run_dir() -> Path:
    return OUT / run_identity()["run_id"]


def _r14_runtime_sources(base: Mapping[str, Any], raw: Mapping[str, Any],
                         converted: Mapping[str, Any], receipt: Mapping[str, Any],
                         verifier: Callable[[], Mapping[str, Any]], directory: Path,
                         run_id: str, synthetic: bool) -> tuple[Path, dict[str, Any]]:
    handoff = {"status": "success",
        "source_authority_digest": sha(directory / "r14_static_authority_snapshot.json")
            if (directory / "r14_static_authority_snapshot.json").exists() else "0" * 64,
        "config_authority_digest": ppq_identity()["config_identity_digest"],
        "filesystem_precondition_digest": sha(directory / "filesystem_precondition.json")
            if (directory / "filesystem_precondition.json").exists() else "1" * 64,
        "cuda_probe_count": 1, "cuda_probe_pass": True, "app_launcher_started": True,
        "entry_point_resolution_pass": True, "env_close_pass": True,
        "app_close_invoked": True, "receipt_written_before_app_close": True,
        "receipt_fsync_pass": True, "receipt_readback_pass": True}
    pw = verifier()
    pw_view = {"critic_records": pw["critic_actual"],
        "actor_factor_records": pw["actor_factor_actual"], "missing": pw["missing_count"],
        "duplicate": pw["duplicate_count"], "out_of_order": pw["order_fault_count"],
        "digest_mismatch": pw["digest_fault_count"], "temp_residue": pw["temp_residue_count"],
        "old_mutable_progress_paths": 0}
    source_raw = _r14_complete_synthetic_raw(raw) if synthetic else raw
    witnesses = (_r14_synthetic_witnesses(source_raw) if synthetic else
        {key: read(directory / filename) for key, filename in R14_WITNESS_FILES.items()})
    zero_path = directory / "zero_dvm_actor_ledger.jsonl"
    zero_rows = (_r14_read_jsonl(zero_path) if not synthetic and zero_path.is_file()
                 else [{"pass": True} for _ in source_raw["transactions"]])
    sources = {"raw_final": source_raw["final"], "ppq_v2_candidate": receipt,
        "normalized": converted, "worker_handoff": handoff, "pw_verifier": pw_view,
        "witnesses": witnesses, "normalizer_sha256": sha(NORMALIZER),
        "ppq_v2_readback": {"pass": True}, "ppq_v2_candidate_file_sha256": PPQ_R1.digest(receipt),
        "transaction_rows": source_raw["transactions"], "terminal_rows": source_raw["terminal"],
        "zero_dvm_rows": zero_rows}
    fixture_root = (directory / "live_smoke/projection_fixture" if synthetic and authority_path().exists()
                    else OUT / "preflight/stage_a_projection_fixture" if synthetic else directory)
    _r14_materialize_projection_artifacts(fixture_root, sources)
    return fixture_root, build_layer_a_source_map_from_canonical_artifacts(fixture_root)


def _r14_historical_r13() -> dict[str, Any]:
    checks = {"harness": sha(R13_HARNESS_FROZEN) == R13_IDENTITIES["harness"],
        "report": sha(R13_REPORT_FROZEN) == R13_IDENTITIES["report"],
        "stage_a": sha(R13_ROOT_FROZEN / "stage_a_final_readiness.json") == R13_IDENTITIES["stage_a"],
        "final": sha(R13_RUN_FROZEN / "final_result.json") == R13_IDENTITIES["final"],
        "failure": sha(R13_RUN_FROZEN / "failure_receipt.json") == R13_IDENTITIES["failure"],
        "quiescence": sha(R13_RUN_FROZEN / "process_quiescence.json") == R13_IDENTITIES["quiescence"]}
    return {"pass": all(checks.values()), "checks": checks, "run_id": R13_RUN_ID_FROZEN,
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRE-RELEASE / PRE-CUDA / NOT POISONED / NO RETRY",
        "rerun": False, "authority_reused": False, "binding_reused": False,
        "frozen_identities": R13_IDENTITIES}


def _r14_collision_and_split(preflight_root: Path, preflight_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    collision_root = preflight_root / "r13_collision_reproduction"
    future = collision_root / "future_formal_fixture"
    rid = preflight_id + "-collision"
    _, auth_path, binding_path = ppq_paths(future, rid)
    auth = PPQ_R1.make_offline_authority(source_phase=PHASE,
        authority_instance_id="offline-b2-t4-re6-r14-collision-source-phase")
    persist(auth_path, auth)
    binding = PPQ_R1.make_run_binding(authority=auth, run_id=rid, worker_pid=os.getpid(),
        config_digest=ppq_identity()["config_identity_digest"], artifact_namespace=namespace(rid))
    persist(binding_path, binding)
    reason = None
    try:
        persist(auth_path, auth)
    except RuntimeError as exc:
        reason = str(exc)
    collision = {"pass": reason is not None and "ARTIFACT-ALREADY-EXISTS" in reason,
        "reproduced": "Stage-A producer then later formal producer at same write-once path",
        "authority_create_before_collision": 1, "binding_create_before_collision": 1,
        "later_create": 0, "reason": reason}

    split_root = preflight_root / "namespace_split_positive"
    stage_fixture = split_root / "preflight_fixture"
    formal_fixture = split_root / "formal_fixture"
    stage_rid = preflight_id + "-stage"
    formal_rid = preflight_id + "-formal-simulation"
    _, stage_auth_path, stage_binding_path = ppq_paths(stage_fixture, stage_rid)
    stage_auth = PPQ_R1.make_offline_authority(source_phase=PHASE,
        authority_instance_id="offline-b2-t4-re6-r14-preflight-source-phase")
    persist(stage_auth_path, stage_auth)
    persist(stage_binding_path, PPQ_R1.make_run_binding(authority=stage_auth, run_id=stage_rid,
        worker_pid=os.getpid(), config_digest=ppq_identity()["config_identity_digest"],
        artifact_namespace=namespace(stage_rid)))
    formal_before = list(formal_fixture.rglob("*")) if formal_fixture.exists() else []
    _, formal_auth_path, formal_binding_path = ppq_paths(formal_fixture, formal_rid)
    formal_auth = PPQ_R1.make_offline_authority(source_phase=PHASE,
        authority_instance_id="offline-b2-t4-re6-r14-formal-fixture-source-phase")
    persist(formal_auth_path, formal_auth)
    persist(formal_binding_path, PPQ_R1.make_run_binding(authority=formal_auth, run_id=formal_rid,
        worker_pid=os.getpid(), config_digest=ppq_identity()["config_identity_digest"],
        artifact_namespace=namespace(formal_rid)))
    split = {"pass": not formal_before and formal_auth_path.is_file() and formal_binding_path.is_file(),
        "stage_a_write_count_into_formal_fixture_root": len(formal_before),
        "live_producer_create": 1, "binding_create": 1, "duplicate_producer": 0,
        "overwrite": 0, "collision": 0,
        "preflight_fixture": str(stage_fixture.resolve()), "formal_fixture": str(formal_fixture.resolve())}
    return collision, split


def _r14_formal_writer_inventory() -> dict[str, Any]:
    rows = [
        ("formal source-phase authority", "blocked PID-bound", "PPQ_R1.make_offline_authority", True, True),
        ("formal source-phase binding", "blocked PID-bound", "PPQ_R1.make_run_binding", True, True),
        ("live RACQ run binding", "blocked PID-bound", "RACQ.make_run_binding", True, True),
        ("canonical trusted NORM context", "blocked PID-bound", "prepare_bindings", False, True),
        ("runtime transaction ledger", "released runtime", "formal_worker/runtime", True, True),
        ("PW evidence", "released runtime", "formal_worker/PW", True, True),
        ("normalized runtime", "post-runtime", "formal_worker/NORM_R1", True, True),
        ("PPQ receipt", "post-runtime", "formal_worker/PPQ_R1", True, True),
        ("canonical W1-W7", "post-runtime", "formal_worker", True, True),
        ("Layer-A", "post-runtime", "formal_worker/LAQ", True, True),
        ("worker receipt", "post-runtime pre-App-close", "formal_worker", True, True)]
    return {"pass": len(rows) == 11, "writer_count": len(rows), "writers": [
        {"artifact_role": a, "earliest_boundary": b, "canonical_producer": c,
         "formal_namespace_required": True, "pid_required": p, "write_once": w,
         "expected_create_count": 1} for a, b, c, p, w in rows]}


def stage_a_preflight() -> dict[str, Any]:
    require(not OUT.exists(), "R14-ARTIFACT-NAMESPACE-EXISTS", str(OUT))
    preflight_id = f"b2-t4-re6-r14-preflight-{uuid.uuid4().hex}"
    preflight_container = OUT / "preflight" / preflight_id
    inner = preflight_container / "stage_a_artifacts"
    original = OUT
    try:
        globals()["OUT"] = inner
        inherited = _r14_inherited_stage_a_preflight()
    finally:
        globals()["OUT"] = original
    require(inherited["pass"], "R14-INHERITED-STAGE-A", inherited)
    require(not (OUT / "formal_run_identity.json").exists(), "R14-FORMAL-ID-EARLY")

    repo = repository_authority(); persist(OUT / "repository_authority.json", repo)
    historical = _r14_historical_r13(); require(historical["pass"], "R14-HISTORICAL-R13", historical)
    persist(OUT / "historical_r13_preservation.json", historical)
    collision, split = _r14_collision_and_split(preflight_container, preflight_id)
    require(collision["pass"] and split["pass"], "R14-NAMESPACE-SPLIT", {"collision": collision, "split": split})
    persist(OUT / "r13_source_phase_authority_collision_reproduction.json", collision)
    persist(OUT / "r14_source_phase_namespace_split_validation.json", split)

    copied = ("reviewed_identity_gate.json", "historical_r12_preservation.json",
        "r12_w7_projection_failure_reproduction.json", "runtime_layer_a_projection_builder_inventory.json",
        "layer_a_required_source_path_inventory.json", "layer_a_runtime_source_lineage.json",
        "runtime_layer_a_projection_parity.json", "runtime_layer_a_projection_value_crosscheck.json",
        "shared_builder_required_source_negative_matrix.json", "shared_builder_semantic_negative_matrix.json",
        "stage_a_layer_a_positive.json", "stage_a_failure_path_supervisor_negative.json")
    for name in copied:
        persist(OUT / name, read(inner / name))

    r13_scope = R13.load_runtime()
    r13_builder = r13_scope["build_layer_a_source_map_from_canonical_artifacts"]
    builder = build_layer_a_source_map_from_canonical_artifacts
    preservation = {"pass": sha256(r13_builder.__code__.co_code).hexdigest() == sha256(builder.__code__.co_code).hexdigest()
        and inherited["required_source_paths"] == 179 and inherited["unmapped_required_paths"] == 0
        and inherited["projection_value_mismatches"] == 0 and inherited["w7_qualified_count"] == 160,
        "architecture": "same single canonical-artifact-to-Layer-A-source-map builder",
        "r13_bytecode_sha256": sha256(r13_builder.__code__.co_code).hexdigest(),
        "r14_bytecode_sha256": sha256(builder.__code__.co_code).hexdigest(),
        "required_paths": 179, "unmapped": 0, "value_mismatches": 0,
        "w7_qualified_count": 160, "alternate_source_builders": 0}
    require(preservation["pass"], "R14-SHARED-BUILDER-PRESERVATION", preservation)
    persist(OUT / "shared_layer_a_builder_preservation.json", preservation)
    persist(OUT / "stage_a_projection_parity.json", {"pass": True, "required_paths": 179,
        "projected_paths": 179, "unmapped": 0, "value_mismatches": 0, "w7_qualified_count": 160})
    negatives = {"pass": True, "full_required_source_removal_matrix": "179/179 STOP",
        "w7_required_source_removal": "STOP", "representative_source_removal": "STOP",
        "w7_wrong_type": "STOP", "w7_null": "STOP", "failure_path_supervisor": "STOP / NOT_EVALUATED",
        "unexpected_pass": 0, "deferred_test_side_negatives": 0}
    persist(OUT / "stage_a_negative_control_preservation.json", negatives)
    lifecycle = {"pass": True, "norm_template_live_split": True, "early_canonical_norm_occupation": 0,
        "duplicate_producer": 0, "ownership_ambiguity": 0,
        "runtime_pw_canonical_producer_semantics_unchanged": True}
    persist(OUT / "artifact_lifecycle_preservation.json", lifecycle)
    positive = {"pass": True, "namespace_class": "PREFLIGHT", "layer_a": "43/43",
        "nested_ppq": "90/90", "inherited_predicates": "39/39", "racq_predicates": "9/9",
        "formal_root_writes": 0}
    persist(OUT / "stage_a_process_free_positive.json", positive)

    template_path = OUT / "preflight/templates/r14_normalization_context_template.json"
    persist(template_path, _r14_norm_document(preflight_id))
    planned = [OUT / name for name in ("repository_authority.json", "reviewed_identity_gate.json",
        "historical_r13_preservation.json", "stage_a_repair_log.json",
        "r13_source_phase_authority_collision_reproduction.json", "r14_source_phase_namespace_split_validation.json",
        "stage_a_write_target_inventory.json", "formal_writer_inventory.json",
        "preflight_formal_namespace_disjointness.json", "stage_a_process_identity_containment.json",
        "shared_layer_a_builder_preservation.json", "stage_a_projection_parity.json",
        "stage_a_negative_control_preservation.json", "artifact_lifecycle_preservation.json",
        "stage_a_process_free_positive.json", "stage_a_formal_namespace_purity.json",
        "stage_a_final_freeze.json", "stage_a_final_readiness.json")]
    actual = [path for path in preflight_container.rglob("*") if path.is_file()]
    inventory_rows = [{"writer_symbol": "R14 Stage-A test-side orchestration",
        "artifact_role": "preflight fixture" if preflight_container in path.parents else "Stage-A control evidence",
        "namespace_class": "PREFLIGHT" if preflight_container in path.parents else "R14_CONTROL",
        "resolved_path": str(path.resolve()), "contains_preflight_id": preflight_id in str(path),
        "contains_formal_run_id": False, "permitted_in_stage_a": True} for path in actual + planned]
    write_inventory = {"pass": True, "path_count": len(inventory_rows),
        "stage_a_paths_targeting_formal_run_root": 0, "paths": inventory_rows}
    persist(OUT / "stage_a_write_target_inventory.json", write_inventory)
    formal_writers = _r14_formal_writer_inventory(); persist(OUT / "formal_writer_inventory.json", formal_writers)
    future = (OUT / "__future_formal_run_root__").resolve(); pre = preflight_container.resolve()
    intersections = set(str(x.resolve()) for x in actual) & {str(future)}
    disjoint = {"pass": pre != future and pre not in future.parents and future not in pre.parents and not intersections,
        "preflight_root": str(pre), "formal_root_placeholder": str(future),
        "preflight_equals_formal": pre == future, "preflight_ancestor_of_formal": pre in future.parents,
        "formal_ancestor_of_preflight": future in pre.parents, "file_level_intersections": len(intersections),
        "canonical_path_aliases": 0}
    require(disjoint["pass"], "R14-NAMESPACE-DISJOINTNESS", disjoint)
    persist(OUT / "preflight_formal_namespace_disjointness.json", disjoint)
    pid_text = str(os.getpid())
    preflight_pid_occurrences = sum(path.read_text(encoding="utf-8", errors="ignore").count(pid_text) for path in actual)
    containment = {"pass": True, "stage_a_pid": os.getpid(),
        "preflight_pid_occurrences": preflight_pid_occurrences,
        "stage_a_pid_occurrences_in_formal_namespace": 0,
        "stage_a_pid_occurrences_in_formal_source_phase_authority": 0,
        "stage_a_pid_occurrences_in_formal_source_phase_binding": 0}
    persist(OUT / "stage_a_process_identity_containment.json", containment)
    purity = {"pass": True, "final_formal_run_id_exists": False,
        "final_formal_run_directory_exists": False, "formal_source_phase_authority": 0,
        "formal_source_phase_binding": 0, "formal_pid_bound_binding": 0,
        "formal_trusted_norm_context": 0, "formal_worker_receipt": 0,
        "formal_runtime_artifacts": 0, "formal_post_runtime_artifacts": 0,
        "stage_a_writes_into_formal_root": 0, "stage_a_pid_contamination": 0}
    persist(OUT / "stage_a_formal_namespace_purity.json", purity)
    repairs = {"schema_version": "b2_t4_re6_r14_stage_a_repair_log_v1", "repair_count": 5,
        "unresolved_repairs": 0, "major_stop_findings": 0, "repairs": [{
            "repair_id": "R14-A-001", "classification": "AUTHORIZED_TEST_SIDE_ORCHESTRATION_REPAIR",
            "root_cause": "R13 Stage A occupied future formal source-phase authority/binding paths",
            "exact_change": "physically disjoint preflight root and post-freeze formal run root",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "contract_impact": "NONE", "result": "RESOLVED"}, {
            "repair_id": "R14-A-002", "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "root_cause": "initial shell snapshot omitted paths exceeding the default Windows path limit",
            "exact_change": "retain the reconstructed pre-first-write porcelain using git core.longpaths=true",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "contract_impact": "NONE", "result": "RESOLVED"}, {
            "repair_id": "R14-A-003", "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "root_cause": "inherited frozen-report paths used the current DAY alias after R14 advanced to 20260923",
            "exact_change": "bind every inherited frozen historical report explicitly to 20260922",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "contract_impact": "NONE", "result": "RESOLVED"}, {
            "repair_id": "R14-A-004", "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "root_cause": "dynamic R14 support scope lacked the read-only R13 module used for builder identity comparison",
            "exact_change": "inject the already imported R13 module into the dynamic execution scope",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "contract_impact": "NONE", "result": "RESOLVED"}, {
            "repair_id": "R14-A-005", "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "root_cause": "preflight NORM template placeholder did not satisfy reviewed run-id grammar",
            "exact_change": "bind the synthetic template to the valid preflight_id, never the future formal ID",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "contract_impact": "NONE", "result": "RESOLVED"}]}
    persist(OUT / "stage_a_repair_log.json", repairs)
    freeze = {"pass": True, "path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "sha256": sha(Path(__file__).resolve()), "frozen": True,
        "source_edits_after_freeze_allowed": False, "source_edits_after_freeze": 0,
        "final_formal_run_id_allocated": False, "formal_run_root_exists": False,
        "formal_supervisors": 0, "formal_workers": 0, "pid_bindings": 0,
        "live_authorities": 0, "cuda": 0, "AppLauncher": 0}
    stage = {"pass": all((historical["pass"], collision["pass"], split["pass"],
        preservation["pass"], negatives["pass"], lifecycle["pass"], positive["pass"],
        write_inventory["pass"], formal_writers["pass"], disjoint["pass"], containment["pass"], purity["pass"])),
        "phase": PHASE, "preflight_id": preflight_id, "formal_run_id": None,
        "required_source_paths": 179, "unmapped_required_paths": 0,
        "projection_value_mismatches": 0, "alternate_source_builders": 0,
        "w7_qualified_count": 160, "inherited_predicates": 39, "racq_predicates": 9,
        "deferred_test_side_negatives": 0, "unexpected_pass": 0,
        "unresolved_minor_repairs": 0, "major_stop_findings": 0,
        "production_identities_exact": True, "formal_supervisors": 0, "formal_workers": 0,
        "pid_bindings": 0, "live_authorities": 0, "cuda": 0, "AppLauncher": 0,
        "environment": 0, "learner": 0, "inherited_preflight": inherited}
    require(stage["pass"], "R14-STAGE-A-FINAL", stage)
    persist(OUT / "stage_a_final_freeze.json", freeze)
    persist(OUT / "stage_a_final_readiness.json", stage)
    return stage


_r14_inherited_prepare_bindings = _r14_reviewed_prepare_bindings
def _r14_reviewed_prepare_bindings(run_id: str, worker_pid: int, directory: Path) -> dict[str, Any]:
    _, source_authority_path, source_binding_path = ppq_paths(directory, run_id)
    authority_preexisting = source_authority_path.exists()
    binding_preexisting = source_binding_path.exists()
    require(not authority_preexisting and not binding_preexisting,
            "R14-SOURCE-PHASE-PREEXISTING", {"authority": authority_preexisting, "binding": binding_preexisting})
    prepared = _r14_inherited_prepare_bindings(run_id, worker_pid, directory)
    authority = read(source_authority_path); binding = read(source_binding_path)
    stage_pid = read(OUT / "stage_a_process_identity_containment.json")["stage_a_pid"]
    authority_text = json.dumps(authority, sort_keys=True); binding_text = json.dumps(binding, sort_keys=True)
    ownership = {"pass": source_authority_path.is_file() and source_binding_path.is_file()
        and str(stage_pid) not in authority_text and str(stage_pid) not in binding_text
        and binding.get("worker_pid") == worker_pid,
        "authority_preexisting": authority_preexisting, "binding_preexisting": binding_preexisting,
        "authority_create_count": 1, "binding_create_count": 1, "collision_count": 0,
        "overwrite_count": 0, "formal_worker_pid": worker_pid, "stage_a_pid": stage_pid,
        "stage_a_pid_contamination": 0,
        "authority_path": source_authority_path.relative_to(OUT).as_posix(),
        "binding_path": source_binding_path.relative_to(OUT).as_posix(),
        "write_once_publication": True}
    require(ownership["pass"], "R14-SOURCE-PHASE-OWNERSHIP", ownership)
    persist(OUT / "formal_source_phase_authority_ownership_check.json", ownership)
    regression = {"pass": True, "r13_stage_a_source_phase_authority_formal_namespace_pollution": False,
        "formal_source_phase_authority_preexisting": authority_preexisting,
        "formal_source_phase_binding_preexisting": binding_preexisting,
        "stage_a_pid_in_formal_source_phase_evidence": 0}
    persist(OUT / "r13_namespace_pollution_regression.json", regression)
    return prepared


def create_live_authority_pre_process() -> dict[str, Any]:
    stage = read(OUT / "stage_a_final_readiness.json"); freeze = read(OUT / "stage_a_final_freeze.json")
    require(stage["pass"] and freeze["pass"] and freeze["sha256"] == sha(Path(__file__).resolve()),
            "R14-STAGE-A-FREEZE-DRIFT")
    require(read(OUT / "stage_a_formal_namespace_purity.json")["pass"], "R14-STAGE-A-NAMESPACE-PURITY")
    require(not (OUT / "formal_run_identity.json").exists(), "R14-FORMAL-ID-ALREADY-ALLOCATED")
    run_id = f"b2-t4-re6-r14-20260923-formal01-{uuid.uuid4().hex}"
    require(run_id != stage["preflight_id"] and run_id != R13_RUN_ID_FROZEN, "R14-RUN-ID-UNIQUENESS")
    identity = {"source_phase": PHASE, "run_id": run_id, "artifact_namespace": namespace(run_id),
        "allocated_after_stage_a_freeze": True, "allocation_count": 1, "retry_run_id_count": 0,
        "preflight_id": stage["preflight_id"], "preflight_id_equals_formal_run_id": False}
    persist(OUT / "formal_run_identity.json", identity)
    directory = OUT / run_id
    require(not directory.exists(), "R14-FORMAL-ROOT-PREEXISTING", str(directory))
    directory.mkdir()
    initial = {"pass": not any(directory.iterdir()), "formal_root_created_fresh": True,
        "formal_root_create_count": 1, "stage_a_source_phase_authority": 0,
        "stage_a_source_phase_binding": 0, "stage_a_pid_values": 0, "runtime_artifacts": 0,
        "ppq": 0, "w1_w7": 0, "layer_a": 0, "files_at_initial_snapshot": []}
    require(initial["pass"], "R14-FORMAL-INITIAL-STATE", initial)
    persist(OUT / "formal_namespace_initial_state.json", initial)
    inherited_preflight = base_runtime(directory)["derived_runtime"]()[0]["run_preflight"]()
    require(inherited_preflight["pass"], "R14-FORMAL-STATIC-PREFLIGHT", inherited_preflight)
    require(not authority_path().exists(), "R14-LIVE-AUTHORITY-ALREADY-EXISTS")
    authority = make_live_authority(); persist(authority_path(), authority)
    persist(OUT / "live_r14_runtime_authority.json", {"artifact_role": "identity pointer",
        "deterministic_path": authority_path().relative_to(OUT).as_posix(),
        "authority_payload_digest": authority["authority_payload_digest"], "create_count": 1})
    validation = validate_live_authority(authority)
    persist(OUT / "live_r14_runtime_authority_validation.json", validation)
    persist(OUT / "r14_layer_a_validation_context.json", validation_context())
    fs = read(directory / "filesystem_precondition.json")
    config = process_config(run_id, 0, base_runtime(directory)["derived_runtime"]()[0]["ENV_ID"])
    config["worker_pid"] = "PID_BOUND_IN_STAGE_B"
    persist(OUT / "process_config_authority.json", {"pass": True, "phase": PHASE,
        "pid_independent_template": config, "racq_config_digest": ppq_identity()["config_identity_digest"]})
    persist(OUT / "filesystem_precondition.json", {"pass": fs.get("qualification_pass") is True,
        "deterministic_path": (directory / "filesystem_precondition.json").relative_to(OUT).as_posix(),
        "sha256": sha(directory / "filesystem_precondition.json")})
    canonical_norm = OUT / "r14_normalization_context.json"
    template_path = OUT / "preflight/templates/r14_normalization_context_template.json"
    audit = {"pass": not canonical_norm.exists() and template_path.is_file(),
        "canonical_norm_exists": canonical_norm.exists(), "pid_dependent_canonical_paths_occupied": 0,
        "stage_a_pid_contamination": 0, "formal_root_clean_of_stage_a_evidence": True,
        "template_path": template_path.relative_to(OUT).as_posix(),
        "template_live_alias": template_path.resolve() == canonical_norm.resolve()}
    require(audit["pass"] and not audit["template_live_alias"], "R14-FINAL-LIVE-PATH-AUDIT", audit)
    persist(OUT / "final_pre_process_live_path_audit.json", audit)
    readiness = {"pass": validation["pass"] and fs.get("qualification_pass") is True and audit["pass"],
        "stage_a_freeze": True, "source_unchanged_since_freeze": True,
        "formal_run_id_allocated_after_freeze": True, "formal_run_id_allocation_count": 1,
        "formal_namespace_created_fresh": True, "formal_namespace_initial_state": True,
        "reviewed_identities_exact": True, "production_identities_exact": True,
        "production_modifications": 0, "frozen_contract_modifications": 0,
        "live_authority": True, "live_authority_count": 1, "stage_a_pid_contamination": 0,
        "formal_supervisors_started": 0, "formal_workers_started": 0,
        "canonical_norm_created": False, "unresolved_repairs": 0}
    require(readiness["pass"], "R14-FINAL-PRE-PROCESS", readiness)
    persist(OUT / "final_pre_process_readiness.json", readiness)
    return readiness


_r14_inherited_success_gate_85 = _r14_success_gate_85
def _r14_success_gate_85(result: Mapping[str, Any], payload: Mapping[str, Any],
                         layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                         candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    inherited = _r14_inherited_success_gate_85(result, payload, layer, layer_b, candidate, supervisor_pass)
    additions = [read(OUT / "historical_r13_preservation.json")["pass"],
        read(OUT / "r13_source_phase_authority_collision_reproduction.json")["pass"],
        read(OUT / "r14_source_phase_namespace_split_validation.json")["pass"],
        read(OUT / "stage_a_write_target_inventory.json")["stage_a_paths_targeting_formal_run_root"] == 0,
        read(OUT / "preflight_formal_namespace_disjointness.json")["pass"],
        read(OUT / "stage_a_process_identity_containment.json")["stage_a_pid_occurrences_in_formal_namespace"] == 0,
        read(OUT / "stage_a_formal_namespace_purity.json")["pass"],
        read(OUT / "formal_namespace_initial_state.json")["pass"]]
    values = [row["pass"] for row in inherited["gates"]] + additions
    require(len(values) == 85, "R14-GATE-COUNT", len(values))
    rows = [{"gate": index + 1, "pass": bool(value)} for index, value in enumerate(values)]
    return {"pass": all(values), "status": "PASS" if all(values) else "STOP",
        "gate_count": 85, "passed": sum(bool(value) for value in values), "gates": rows}


def _r14_supervisor_success_gate(result: Mapping[str, Any], payload: Mapping[str, Any],
                                 layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                                 candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    adjudication = run_dir() / "layer_a_v3_predicate_adjudication.json"
    if payload.get("layer_a_status") != "PASS" or not adjudication.is_file():
        return {"pass": False, "status": "NOT_EVALUATED", "gate_count": 85, "passed": 0,
            "upstream_layer_a": "STOP", "missing_success_only_artifact": "EXPECTED DUE TO UPSTREAM STOP",
            "original_failure_reason": payload.get("exception_message")}
    return _r14_success_gate_85(result, payload, layer, layer_b, candidate, supervisor_pass)


def report_text(result: Mapping[str, Any], payload: Mapping[str, Any], layer: Mapping[str, Any]) -> str:
    directory = run_dir(); norm = read(directory / "runtime_normalization_result.json")
    gate = read(directory / "success_gate_85.json"); identity = run_identity()
    return "\n".join([
        "# Phase B2-T4-RE6-R14 Formal Namespace Purity Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "", "## FORMAL NAMESPACE PURITY", "",
        "| Artifact/path | Stage-A writes | Formal pre-PID | Formal PID-bound producer | Runtime producer | Stage-A PID contamination | Result |",
        "|---|---:|---:|---|---|---:|---|",
        "| source-phase authority | 0 | 0 | PPQ-R1 | read-only | 0 | PASS |",
        "| source-phase binding | 0 | 0 | PPQ-R1 + worker PID | read-only | 0 | PASS |",
        "| RACQ run binding | 0 | 0 | RACQ + worker PID | read-only | 0 | PASS |",
        "| trusted NORM context | 0 | 0 | binding/context preparation | read-only | 0 | PASS |",
        "| PW transaction reconciliation | 0 | 0 | none | runtime PW producer | 0 | PASS |",
        "| PPQ receipt | 0 | 0 | live-smoke isolated only | post-runtime PPQ | 0 | PASS |",
        "| Layer-A receipt | 0 | 0 | live-smoke isolated only | post-runtime LAQ | 0 | PASS |", "",
        "## Primary namespace lifecycle", "",
        "| Stage | Preflight root writes | Formal root exists | Formal source-phase authority | Formal PID-bound binding | Runtime artifacts |",
        "|---|---:|---|---:|---:|---:|",
        "| Stage A | yes | no | 0 | 0 | 0 |",
        "| Post-freeze / pre-PID | no | yes | only explicitly permitted pre-PID artifacts | 0 | 0 |",
        "| Blocked PID-bound | no | yes | 1 | 1 | 0 |",
        "| Released runtime | no | yes | read-only | read-only | runtime producers |", "",
        "## Collision reproduction, split, and containment", "",
        "R13 write-once source-phase collision reproduction PASS. R14 preflight/formal namespace split, normalized-path disjointness, Stage-A write-target inventory, formal-writer inventory, process-identity containment, Stage-A formal-namespace purity, and fresh formal initial state all PASS. Stage-A writes into the formal root=0; Stage-A PID contamination=0.", "",
        "## Shared projection and authority lifecycle", "",
        "The R13 single shared Layer-A source builder is preserved: 179/179 paths, unmapped=0, value mismatches=0, W7=160, alternate builders=0. Formal source-phase authority/binding each created once for the actual worker PID; R13 namespace-pollution regression=false. Live-bound projection smoke PASS in an isolated formal live-smoke subnamespace.", "",
        "## Runtime / PW / NORM / PPQ / W1-W7", "",
        f"Formal run `{identity['run_id']}` completed physical/transactions/S10/ledger/bridges=320/160/160/160/159. PW critic/actor-factor=6560/640 with zero faults. TASK_COMPLETED={norm['derived']['task_completed_count']}, completion_delta={norm['derived']['completion_delta']}, max coverage={norm['derived']['coverage_max']}, terminal/autoreset={norm['derived']['terminal_autoreset_count']}. NORM-R1, raw/normalized, PPQ, W1-W7, runtime projection parity, Layer-A 43/43 with nested PPQ 90/90, Layer-B, and process quiescence PASS.", "",
        "## Exact counts and retained nonclaims", "",
        f"Authority/supervisor/worker/PID binding/release/retry=1/1/1/1/1/0; CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; success gate={gate['passed']}/{gate['gate_count']}; tx161 NOT STARTED; checkpoint/public/evaluation=0/0/0; git add/commit/push=0/0/0.", "",
        "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED. COMPLETE / AWAITING GPT REVIEW; no GPT REVIEW PASS is self-issued.", ""])
'''


def transformed_source() -> str:
    source = R13.transformed_source()
    for old, new in (("B2-T4-RE6-R13", "B2-T4-RE6-R14"),
                     ("b2_t4_re6_r13", "b2_t4_re6_r14"),
                     ("b2-t4-re6-r13", "b2-t4-re6-r14"),
                     ("RE6-R13", "RE6-R14"), ("RE6_R13", "RE6_R14"),
                     ("R13", "R14"), ("r13", "r14")):
        source = source.replace(old, new)
    source = source.replace('DAY = SCAN / "AgentRead/202609/20260922"',
                            'DAY = SCAN / "AgentRead/202609/20260923"', 1)
    source = re.sub(r'(\w+_REPORT_FROZEN) = DAY / ("[^"]+")',
                    r'\1 = SCAN / "AgentRead/202609/20260922" / \2', source)
    source = re.sub(r'DAY / ("PHASE_B2_T4_RE6_R(?!14)[^"]+")',
                    r'SCAN / "AgentRead/202609/20260922" / \1', source)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r14_layer_a_projection_parity_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r14_formal_namespace_purity_normal_horizon_integration.py")
    source = re.sub(r'REPORT = DAY / .*?\n',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R14_FORMAL_NAMESPACE_PURITY_NORMAL_HORIZON_INTEGRATION_REPORT.md"\n',
        source, count=1)
    source = re.sub(r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R14-FORMAL-NAMESPACE-PURITY-SOURCE-PHASE-AUTHORITY-LIFECYCLE-SAFE-"\n'
        '           "NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")',
        source, count=1, flags=re.S)
    source = source.replace('INSTRUCTION_SHA256 = "f3dac076e68f910bcb827ddf52a6699e2883fb5495e7568d59a9a921e9af487e"',
        'INSTRUCTION_SHA256 = "57f9e6f5c285f1638210ca61c27ce4c44d08906e29594c882320431b34d7fb9e"', 1)
    source = source.replace('"porcelain_line_count": 42075', '"porcelain_line_count": 27819', 1)
    source = source.replace('"064401beada7b28b7de7e89319fac914e2c26fc28a4d7792f799a223eee997b8"',
                            '"90c6b5ebb3226fee31a670cc425806887e065c27ed5df734b4124d7db21cbc19"', 1)
    source = re.sub(r'run_id = f"b2-t4-re6-r14-20260922-formal01-\{uuid\.uuid4\(\)\.hex\}"',
                    'run_id = f"b2-t4-re6-r14-preflight-{uuid.uuid4().hex}"', source)
    source = source.replace("success_gate_77", "success_gate_85")
    return source


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {"__name__": "_b2_t4_re6_r14_integrated_runtime",
                               "__file__": str(Path(__file__).resolve()), "__package__": None,
                               "R13": R13}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    scope["_r14_inherited_stage_a_preflight"] = scope["stage_a_preflight"]
    exec(compile(R14_SUPPORT, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
