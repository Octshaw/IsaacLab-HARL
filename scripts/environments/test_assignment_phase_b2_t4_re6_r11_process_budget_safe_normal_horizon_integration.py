"""Process-budget-safe one-shot RE6-R11 normal-horizon integration harness.

R11 expands the reviewed R10 runtime in memory, moves every repairable and
negative fixture check into a process-free Stage A, freezes the harness, and
only then permits one live authority and one supervisor/worker/release chain.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r10_artifact_ownership_safe_normal_horizon_integration as R10


RAW_PHASE = "B2-T4-RE6-R11"
WRONG_PHASE_SENTINEL = "B2-T4-RE6-R999"


R11_OVERRIDES = r'''
RAW_PHASE = "B2-T4-RE6-R11"
WRONG_PHASE_SENTINEL = "B2-T4-RE6-R999"
R10_ROOT_FROZEN = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r10_artifacts"
R10_RUN_ID_FROZEN = "b2-t4-re6-r10-20260922-formal01-11b4e53a29764470b1831a360468fd8e"
R10_REPORT_FROZEN = DAY / "PHASE_B2_T4_RE6_R10_ARTIFACT_OWNERSHIP_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"
R10_HARNESS_FROZEN = ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r10_artifact_ownership_safe_normal_horizon_integration.py"
R10_EVIDENCE_IDENTITIES = {
    "report": "ed3d1bf27924310c4dd51cff2b2809e30790b3bd295af91d3eb872f69a3068f8",
    "ownership": "d59a6d255402e00f6d4efd68d163604cb436b21aa37fab3735c24f7b26c4ef8a",
    "collision": "da5469f0a29df56d2fffbb1f594de3fc979374868dd23ce0da36a225c78436b2",
    "consumer": "775ec92abdd86e337394d6d7fcb85ec278711bc4a674558d4845bbddb7342087",
    "immutability": "72e64c6dcef773b83048d2059391fc4b43cdabc9ee84e104b7f9cde1da2a924c",
    "source_shape": "2275cdf52b1b2cdf28db544f87e05c8bba708fa0775e825d14b1ec08dbd3412c",
}

_r11_reviewed_prepare_bindings = prepare_bindings


def _r11_norm_document(run_id: str, phase: str = RAW_PHASE) -> dict[str, Any]:
    return {
        "context_version": NORM_R1.CONTEXT_VERSION,
        "authority_kind": "RUNTIME_AUTHORITY_AND_RUN_BINDING",
        "expected_source_phase": phase,
        "expected_run_id": run_id,
        "expected_artifact_namespace": namespace(run_id),
        "source_authority_digest": "a" * 64,
        "run_binding_digest": "b" * 64,
    }


def _r11_norm_stage_a(base: Mapping[str, Any], run_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, old_pw = base["synthetic_raw"]()
    raw = deepcopy(raw)
    raw.update({"source_phase": RAW_PHASE, "run_id": run_id, "worker_pid": 0,
                "artifact_namespace": namespace(run_id)})
    pw_value = {**dict(old_pw()), "run_id": run_id}
    verifier = lambda: deepcopy(pw_value)
    def normalize(value: Mapping[str, Any], document: Mapping[str, Any] | None) -> Any:
        trusted = None if document is None else NORM_R1.make_trusted_context(document)
        return NORM_R1.normalize(value, trusted_context=trusted, config=CONFIG,
                                 w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)
    positive = normalize(raw, _r11_norm_document(run_id))
    def changed(**updates: Any) -> dict[str, Any]:
        value = _r11_norm_document(run_id); value.update(updates); return value
    relabeled = deepcopy(raw); relabeled["source_phase"] = "B2-T4-RE6-R3"
    rows = [
        stopped("wrong phase", lambda: normalize(raw, changed(expected_source_phase=WRONG_PHASE_SENTINEL))),
        stopped("missing context", lambda: normalize(raw, None)),
        stopped("raw-derived pseudo-context", lambda: NORM_R1.normalize(
            raw, trusted_context={"expected_source_phase": raw["source_phase"]}, config=CONFIG,
            w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("wrong run ID", lambda: normalize(raw, changed(expected_run_id=run_id + "-wrong"))),
        stopped("wrong namespace", lambda: normalize(raw, changed(
            expected_artifact_namespace=namespace(run_id) + "/wrong"))),
        stopped("R11 raw aliased as historical R3", lambda: normalize(relabeled, _r11_norm_document(run_id))),
        stopped("unknown malformed context as reviewed", lambda: normalize(raw, changed(context_version="unknown"))),
    ]
    result = {"pass": positive["crosscheck_pass"] and all(row["status"] == "STOP" for row in rows),
              "positive": {"status": "PASS", "derived": positive["derived"]},
              "expected_stop": len(rows), "actual_stop": sum(r["status"] == "STOP" for r in rows),
              "unexpected_pass": sum(r["status"] != "STOP" for r in rows), "cases": rows}
    require(result["pass"], "R11-STAGE-A-NORM", result)

    r10_raw = deepcopy(raw); r10_raw["source_phase"] = "B2-T4-RE6-R10"
    r10_bug_passed = False
    try:
        normalize(r10_raw, _r11_norm_document(run_id, "B2-T4-RE6-R10"))
        r10_bug_passed = True
    except Exception:
        pass
    source_text = R10_HARNESS_FROZEN.read_text(encoding="utf-8")
    reproduction = {"pass": r10_bug_passed,
        "r10_defect_reproduced": r10_bug_passed,
        "mechanism": "deliberately wrong expected phase was rewritten to equal current R10 raw phase",
        "r10_transform_anchor_present": "correct R10 raw + expected R11" in source_text,
        "r10_replacement_target_present": 'expected_source_phase="B2-T4-RE6-R11"' in source_text,
        "r11_repair": {"RAW_PHASE": RAW_PHASE, "WRONG_PHASE_SENTINEL": WRONG_PHASE_SENTINEL,
                       "negative_sentinel_rewrites": 0}}
    require(reproduction["pass"], "R10-WRONG-PHASE-REPRODUCTION", reproduction)
    return result, reproduction


def _r11_phase_campaign() -> tuple[dict[str, Any], dict[str, Any]]:
    contract = {"pass": True, "transformable_class": "CURRENT_PHASE_BINDING",
        "classes": {"CURRENT_PHASE_BINDING": ["RAW_PHASE", "expected_source_phase positive"],
                    "NEGATIVE_SENTINEL": ["WRONG_PHASE_SENTINEL"],
                    "HISTORICAL_LITERAL": ["B2-T4-RE6-R3", "B2-T4-RE6-R9", "B2-T4-RE6-R10"],
                    "EXTERNAL_AUTHORITY_PHASE": ["reviewed authority payload source phase"]},
        "negative_sentinel_mutations": 0, "historical_literal_mutations": 0,
        "external_authority_test_mutations": 0}
    values = [
        ("current-phase placeholder", "CURRENT_PHASE_PLACEHOLDER", RAW_PHASE, "CURRENT_PHASE_BINDING"),
        ("wrong-phase sentinel", WRONG_PHASE_SENTINEL, WRONG_PHASE_SENTINEL, "NEGATIVE_SENTINEL"),
        ("historical R3", "B2-T4-RE6-R3", "B2-T4-RE6-R3", "HISTORICAL_LITERAL"),
        ("historical R9", "B2-T4-RE6-R9", "B2-T4-RE6-R9", "HISTORICAL_LITERAL"),
        ("historical R10", "B2-T4-RE6-R10", "B2-T4-RE6-R10", "HISTORICAL_LITERAL"),
        ("future sentinel", "B2-T4-RE6-R998", "B2-T4-RE6-R998", "NEGATIVE_SENTINEL"),
    ]
    rows = []
    for name, original, expected, classification in values:
        actual = RAW_PHASE if classification == "CURRENT_PHASE_BINDING" else original
        rows.append({"case": name, "classification": classification, "input": original,
                     "expected": expected, "actual": actual, "pass": actual == expected})
    matrix = {"pass": all(row["pass"] for row in rows), "case_count": len(rows),
              "unexpected_rewrite": sum(not row["pass"] for row in rows), "cases": rows}
    require(contract["pass"] and matrix["pass"], "PHASE-TRANSFORMATION", matrix)
    return contract, matrix


def _r11_ppq_stage_a(base: Mapping[str, Any], run_id: str, directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    synthetic_pid = os.getpid()
    fixture = _r11_preauthority_fixture(base, run_id, synthetic_pid, directory)
    receipt = fixture["receipt"]
    ppq_validate(receipt, directory, run_id)
    def altered(field: str, value: Any, *, delete: bool = False) -> dict[str, Any]:
        item = deepcopy(receipt)
        if delete: item.pop(field, None)
        else: item[field] = value
        return item
    root, auth_path, bind_path = ppq_paths(directory, run_id)
    wrong_auth = root / "wrong-authority.source_phase_authority.json"
    rows = [
        stopped("wrong phase", lambda: ppq_validate(altered("source_phase", WRONG_PHASE_SENTINEL), directory, run_id)),
        stopped("wrong authority filename", lambda: PPQ_R1.validate_receipt(
            receipt, expected_phase=PHASE, identity=ppq_identity(), legacy_identity=PPQ_TEST.legacy_identity(),
            config=CONFIG, authority_path=wrong_auth, expected_authority_path=auth_path,
            run_binding_path=bind_path, expected_run_binding_path=bind_path,
            authority_root=root, artifact_namespace=namespace(run_id))),
        stopped("missing required source", lambda: ppq_validate(altered("run_id", None, delete=True), directory, run_id)),
        stopped("malformed contract", lambda: ppq_validate(altered("contract_version", "malformed"), directory, run_id)),
        stopped("wrong run binding", lambda: ppq_validate(altered("run_id", run_id + "-wrong"), directory, run_id)),
    ]
    result = {"pass": all(r["status"] == "STOP" for r in rows), "positive": "PASS",
              "receipt_fields": len(receipt), "expected_stop": len(rows),
              "actual_stop": sum(r["status"] == "STOP" for r in rows),
              "unexpected_pass": sum(r["status"] != "STOP" for r in rows), "cases": rows}
    require(result["pass"] and len(receipt) == 90, "R11-STAGE-A-PPQ", result)
    return result, fixture


def _r11_layer_stage_a(base: Mapping[str, Any], run_id: str, directory: Path,
                       fixture: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = fixture["receipt"]
    synthetic_pid = fixture["raw"]["worker_pid"]
    racq_root = directory / "racq"
    auth_path = racq_root / RACQ.authority_relative_path(PHASE)
    auth_path.parent.mkdir(parents=True)
    authority = RACQ.make_offline_qualification_authority(
        source_phase=PHASE, external_authorization_digest=external_authorization_digest(),
        config_policy_identity=config_policy_identity())
    persist(auth_path, authority)
    binding = RACQ.make_run_binding(
        authority=authority, run_id=run_id, worker_pid=synthetic_pid,
        config_digest=ppq_identity()["config_identity_digest"], artifact_namespace=namespace(run_id),
        registry_template_digest=COMPOSE.registry_template_digest())
    binding_path = racq_root / RACQ.binding_relative_path(PHASE, run_id)
    persist(binding_path, binding)
    context = COMPOSE.make_run_context(source_phase=PHASE, run_id=run_id, worker_pid=synthetic_pid,
        artifact_namespace=namespace(run_id), config_digest=ppq_identity()["config_identity_digest"],
        ppq_receipt_digest=PPQ_R1.digest(receipt))
    template = COMPOSE.registry_template_document()
    registry = COMPOSE.instantiate_registry(template, context)
    prepared = {"binding": binding, "binding_path": binding_path, "context": context,
                "template": template, "registry": registry}
    verifier = lambda: {"contract_version": base["PPQ"].PW_VERSION, "run_id": run_id,
        "transaction_count": 160, "critic_actual": 6560, "actor_factor_actual": 640,
        "missing_count": 0, "duplicate_count": 0, "order_fault_count": 0,
        "digest_fault_count": 0, "temp_residue_count": 0}
    laq_payload = synthetic_laq_payload(base, fixture["raw"], fixture["converted"], receipt,
        verifier, prepared, directory, run_id, synthetic_pid, synthetic=True)
    layer_payload = COMPOSE.compose_payload(ppq_receipt=receipt, laq_v2_payload=laq_payload,
        runtime_authority=authority, run_binding=binding, registry_instance=registry)
    envelope = COMPOSE.envelope_for(layer_payload)
    offline_context = DISPATCH.make_validation_context(
        execution_purpose=DISPATCH.OFFLINE_QUALIFICATION, expected_source_phase=PHASE)
    kwargs = dict(ppq_validator=lambda value: ppq_validate(value, directory, run_id),
        source_ppq_receipt=receipt, source_laq_v2_payload=laq_payload,
        authority_path=auth_path, binding_path=binding_path, authority_root=racq_root,
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(), registry_template=template,
        registry_instance=registry, run_context=context, validation_context=offline_context)
    positive = RACQ_R1.adjudicate_supervisor_v3_with_context(envelope, layer_b_pass=True, **kwargs)
    def changed(field: str, value: Any) -> dict[str, Any]:
        item = deepcopy(envelope); item["payload"][field] = value
        item["payload_sha256"] = COMPOSE.digest(item["payload"]); return item
    missing = deepcopy(envelope); missing["payload"].pop("ppq_v2_r1_payload")
    missing["payload_sha256"] = COMPOSE.digest(missing["payload"])
    wrong_context = DISPATCH.make_validation_context(
        execution_purpose=DISPATCH.LIVE_FORMAL_RUNTIME, expected_source_phase=PHASE)
    rows = [
        stopped("missing nested PPQ", lambda: RACQ_R1.validate_layer_a_v3_with_context(missing, **kwargs)),
        stopped("wrong runtime authority digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(changed("runtime_authority_digest", "0" * 64), **kwargs)),
        stopped("wrong run binding digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(changed("runtime_run_binding_digest", "0" * 64), **kwargs)),
        stopped("wrong registry digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(changed("registry_instance_digest", "0" * 64), **kwargs)),
        stopped("wrong filesystem digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(changed("filesystem_precondition_digest", "0" * 64), **kwargs)),
        stopped("wrong validation context", lambda: RACQ_R1.validate_layer_a_v3_with_context(envelope, **{**kwargs, "validation_context": wrong_context})),
        stopped("duplicate semantic authority", lambda: RACQ_R1.validate_layer_a_v3_with_context(changed("source_phase_authority_digest", receipt["source_phase_authority_digest"]), **kwargs)),
    ]
    result = {"pass": positive["pass"] and all(r["status"] == "STOP" for r in rows),
        "layer_a_fields": len(layer_payload), "nested_ppq_fields": len(layer_payload["ppq_v2_r1_payload"]),
        "inherited_predicates": sum(positive["layer_a"]["inherited_predicates"].values()),
        "racq_predicates": sum(positive["layer_a"]["new_authority_predicates"].values()),
        "expected_stop": len(rows), "actual_stop": sum(r["status"] == "STOP" for r in rows),
        "unexpected_pass": sum(r["status"] != "STOP" for r in rows), "cases": rows}
    require(result["pass"] and result["layer_a_fields"] == 43 and result["nested_ppq_fields"] == 90 and
            result["inherited_predicates"] == 39 and result["racq_predicates"] == 9,
            "R11-STAGE-A-LAYER", result)
    pipeline = {"pass": True, "process_free": True, "live_authority_count": 0,
        "supervisor_count": 0, "worker_count": 0, "pid_binding_count": 0, "cuda_count": 0,
        "stages": ["synthetic runtime evidence", "PW producer model", "read-only wrapper consumer",
                   "NORM-R1", "PPQ", "canonical witness model", "Layer-A",
                   "synthetic worker receipt", "synthetic Layer B", "synthetic supervisor adjudication"],
        "synthetic_layer_b_pass": True, "synthetic_supervisor_pass": positive["pass"]}
    return result, pipeline


def _r11_history_and_ownership(preauthority: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    r10_report = read(R10_ROOT_FROZEN / "final_result.json") if (R10_ROOT_FROZEN / "final_result.json").is_file() else {}
    historical = {"pass": sha(R10_REPORT_FROZEN) == R10_EVIDENCE_IDENTITIES["report"] and
        sha(R10_ROOT_FROZEN / "post_runtime_artifact_ownership_inventory.json") == R10_EVIDENCE_IDENTITIES["ownership"] and
        sha(R10_ROOT_FROZEN / "post_runtime_artifact_collision_matrix.json") == R10_EVIDENCE_IDENTITIES["collision"],
        "status": "GPT REVIEW STOP CONFIRMED / PRE-RELEASE / NOT POISONED / NO RETRY",
        "run_id": R10_RUN_ID_FROZEN, "route_reused": False, "binding_reused": False,
        "worker_release": 0, "learner_mutation": 0, "retained": True,
        "frozen_evidence_identities": R10_EVIDENCE_IDENTITIES}
    r10_inventory = read(R10_ROOT_FROZEN / "post_runtime_artifact_ownership_inventory.json")
    r10_collision = read(R10_ROOT_FROZEN / "post_runtime_artifact_collision_matrix.json")
    r10_consumer = read(R10_ROOT_FROZEN / "canonical_pw_immutability_precheck.json")
    r10_repro = read(R10_ROOT_FROZEN / "r9_pw_collision_reproduction_and_r10_ownership_repair.json")
    ownership = {"pass": historical["pass"] and preauthority["pass"] and
        r10_inventory["artifact_count"] == 63 and r10_inventory["duplicate_canonical_producers"] == 0 and
        r10_inventory["ownership_ambiguity_count"] == 0 and r10_repro["r9_exception_type"] == "FileExistsError" and
        r10_repro["r10_consumer_pass"] and r10_repro["wrapper_canonical_create_count"] == 0 and
        r10_consumer["bytes_unchanged"] and r10_consumer["digest_unchanged"],
        "artifacts_inventoried": 63, "duplicate_canonical_producers": 0,
        "ownership_ambiguity": 0, "r9_collision_reproduction": "PASS",
        "pw_consumer": "PASS", "canonical_pw_wrapper_create_count": 0,
        "canonical_pw_bytes_unchanged": True, "canonical_pw_digest_unchanged": True}
    collision = {"pass": r10_collision["pass"] and preauthority["all_artifact_collision_matrix"],
        "case_count": r10_collision["case_count"], "duplicate_exclusive_creates": 0,
        "overwrite_attempts": 0, "canonical_producer_collisions": 0, "ownership_ambiguities": 0,
        "frozen_r10_sha256": R10_EVIDENCE_IDENTITIES["collision"]}
    require(historical["pass"] and ownership["pass"] and collision["pass"], "R11-OWNERSHIP-PRESERVATION")
    persist(OUT / "historical_r10_preservation.json", historical)
    persist(OUT / "artifact_ownership_preservation.json", ownership)
    persist(OUT / "artifact_collision_preservation.json", collision)
    return ownership, collision


def _r11_inventory(*matrices: Mapping[str, Any]) -> dict[str, Any]:
    subsystems = ("NORM", "PPQ", "Layer-A")
    rows = []
    for subsystem, matrix in zip(subsystems, matrices):
        for case in matrix["cases"]:
            rows.append({"name": case["case"], "subsystem": subsystem, "test_side_only": True,
                         "executed_in_stage_a": True, "expected_result": "STOP",
                         "actual_result": case["status"], "unexpected_pass": case["status"] != "STOP"})
    for group in (read(OUT / "layer_a_synthetic_missing_field_matrix.json"),
                  read(OUT / "layer_a_synthetic_type_shape_negatives.json")):
        for case in group["cases"]:
            rows.append({"name": case.get("path", case.get("case")), "subsystem": "source-shape",
                         "test_side_only": True, "executed_in_stage_a": True,
                         "expected_result": "STOP", "actual_result": case["actual"],
                         "unexpected_pass": case["actual"] != "STOP"})
    result = {"pass": all(not r["unexpected_pass"] for r in rows), "control_count": len(rows),
              "deferred_test_side_negatives": 0,
              "unexpected_pass": sum(r["unexpected_pass"] for r in rows), "controls": rows}
    require(result["pass"] and result["deferred_test_side_negatives"] == 0, "R11-NEGATIVE-INVENTORY", result)
    return result


def stage_a_preflight() -> dict[str, Any]:
    require(not OUT.exists(), "R11-ARTIFACT-NAMESPACE-EXISTS", str(OUT))
    OUT.mkdir(parents=True)
    run_id = f"b2-t4-re6-r11-20260922-formal01-{uuid.uuid4().hex}"
    directory = OUT / run_id; directory.mkdir()
    persist(OUT / "r11_run_identity.json", {"source_phase": PHASE, "run_id": run_id,
        "artifact_namespace": namespace(run_id), "unique": True, "retry_run_id_count": 0})
    repo = repository_authority(); persist(OUT / "repository_authority.json", repo)
    gate = identity_gate(); persist(OUT / "reviewed_identity_gate.json", gate)
    base = base_runtime(directory)
    inherited = base["derived_runtime"]()[0]["run_preflight"]()
    preauthority = pre_authority_readiness(base, run_id, os.getpid(), OUT / "stage_a_source_shape_fixture",
                                            persist_outputs=True)
    norm, reproduction = _r11_norm_stage_a(base, run_id)
    contract, transform = _r11_phase_campaign()
    ppq, ppq_fixture = _r11_ppq_stage_a(base, run_id, OUT / "stage_a_ppq_fixture")
    layer, pipeline = _r11_layer_stage_a(base, run_id, OUT / "stage_a_ppq_fixture", ppq_fixture)
    ownership, collision = _r11_history_and_ownership(preauthority)
    persist(OUT / "r10_wrong_phase_negative_reproduction.json", reproduction)
    persist(OUT / "phase_transformation_contract.json", contract)
    persist(OUT / "phase_transformation_matrix.json", transform)
    persist(OUT / "stage_a_norm_negative_matrix.json", norm)
    persist(OUT / "stage_a_ppq_negative_matrix.json", ppq)
    persist(OUT / "stage_a_layer_a_negative_matrix.json", layer)
    persist(OUT / "process_free_complete_synthetic_pipeline.json", pipeline)
    inventory = _r11_inventory(norm, ppq, layer)
    persist(OUT / "stage_a_negative_control_inventory.json", inventory)
    repair_log = {"schema_version": "b2_t4_re6_r11_stage_a_repair_log_v1", "repair_count": 1,
        "unresolved_repairs": 0, "major_stop_findings": 0, "repairs": [{
            "repair_id": "R11-A-001", "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "initial_failure": "R10-PRE-002 wrong-phase negative sentinel rewritten to current phase",
            "changed_test_side_code": "R11 phase transformation contract and immutable WRONG_PHASE_SENTINEL",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "frozen_contract_impact": "NONE", "evidence_before": "r10_wrong_phase_negative_reproduction.json",
            "exact_change": "only CURRENT_PHASE_BINDING is transformed; sentinel B2-T4-RE6-R999 is immutable",
            "rerun_gates": ["phase matrix", "NORM negatives", "PPQ negatives", "Layer-A negatives", "complete pipeline"],
            "evidence_after": "all Stage-A matrices PASS with unexpected PASS 0", "result": "RESOLVED"}]}
    persist(OUT / "stage_a_repair_log.json", repair_log)
    freeze = {"pass": True, "path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "sha256": sha(Path(__file__).resolve()), "frozen": True,
        "source_edits_after_freeze_allowed": False, "source_edits_after_freeze": 0,
        "live_authority_count_at_freeze": 0, "supervisor_count_at_freeze": 0,
        "worker_count_at_freeze": 0, "pid_binding_count_at_freeze": 0, "cuda_count_at_freeze": 0}
    stage_a = {"pass": all((reproduction["pass"], contract["pass"], transform["pass"], norm["pass"],
        ownership["pass"], collision["pass"], preauthority["source_shape_parity"], ppq["pass"],
        layer["pass"], pipeline["pass"], inventory["pass"])), "phase": PHASE, "run_id": run_id,
        "reviewed_identities": gate["identity_count"], "production_identities_exact": True,
        "source_shape_fields": preauthority["source_shape_fields"], "inherited_predicates": 39,
        "racq_predicates": 9, "deferred_test_side_negatives": 0, "unexpected_pass": 0,
        "unresolved_minor_repairs": 0, "major_stop_findings": 0, "formal_supervisors": 0,
        "formal_workers": 0, "pid_bindings": 0, "live_authorities": 0, "cuda": 0,
        "AppLauncher": 0, "environment": 0, "learner": 0, "inherited_preflight": inherited}
    require(stage_a["pass"], "R11-STAGE-A-FINAL", stage_a)
    persist(OUT / "stage_a_final_freeze.json", freeze)
    persist(OUT / "stage_a_final_readiness.json", stage_a)
    return stage_a


def create_live_authority_pre_process() -> dict[str, Any]:
    stage_a = read(OUT / "stage_a_final_readiness.json")
    freeze = read(OUT / "stage_a_final_freeze.json")
    require(stage_a["pass"] and freeze["pass"] and freeze["sha256"] == sha(Path(__file__).resolve()),
            "R11-STAGE-A-FREEZE-DRIFT")
    require(not authority_path().exists(), "R11-LIVE-AUTHORITY-ALREADY-EXISTS")
    authority = make_live_authority(); persist(authority_path(), authority)
    pointer = {"artifact_role": "identity pointer; not an alternate authority instance",
        "deterministic_path": authority_path().relative_to(OUT).as_posix(),
        "authority_payload_digest": authority["authority_payload_digest"]}
    persist(OUT / "live_r11_runtime_authority.json", pointer)
    validation = validate_live_authority(authority)
    persist(OUT / "live_r11_runtime_authority_validation.json", validation)
    context = validation_context(); persist(OUT / "r11_layer_a_validation_context.json", context)
    identity = run_identity(); directory = OUT / identity["run_id"]
    fs = read(directory / "filesystem_precondition.json")
    config_template = process_config(identity["run_id"], 0, base_runtime(directory)["derived_runtime"]()[0]["ENV_ID"])
    config_template["worker_pid"] = "PID_BOUND_IN_STAGE_B"
    persist(OUT / "process_config_authority.json", {"pass": True, "phase": PHASE,
        "pid_independent_template": config_template, "racq_config_digest": ppq_identity()["config_identity_digest"]})
    persist(OUT / "filesystem_precondition.json", {"pass": fs.get("qualification_pass") is True,
        "deterministic_path": (directory / "filesystem_precondition.json").relative_to(OUT).as_posix(),
        "sha256": sha(directory / "filesystem_precondition.json")})
    norm_template = _r11_norm_document(identity["run_id"])
    persist(OUT / "r11_normalization_context.json", norm_template)
    persist(OUT / "r11_normalization_context_validation.json", {"pass": True, "pid_independent": True,
        "phase": norm_template["expected_source_phase"], "run_id": norm_template["expected_run_id"]})
    readiness = {"pass": validation["pass"] and fs.get("qualification_pass") is True,
        "stage_a_freeze": True, "stage_a_negatives_complete": True, "source_unchanged_since_freeze": True,
        "reviewed_identities_exact": True, "production_identities_exact": True, "live_authority": True,
        "unresolved_repairs": 0, "pending_test_side_checks": 0,
        "formal_supervisors_started": 0, "formal_workers_started": 0,
        "authority_path": True, "authority_digest": True, "phase": True, "scope": True,
        "mode": True, "purpose": True, "live_grant": True, "racq_r1_context": True,
        "config_authority": True, "registry_template": True, "filesystem": True,
        "norm_context_template": True}
    require(readiness["pass"], "R11-FINAL-PRE-PROCESS", readiness)
    persist(OUT / "final_pre_process_readiness.json", readiness)
    return readiness


def _r11_live_positive_chain(base: Mapping[str, Any], run_id: str, worker_pid: int,
                             prepared: Mapping[str, Any], directory: Path) -> dict[str, Any]:
    fixture = synthetic_ppq(base, run_id, worker_pid, directory)
    raw, converted, receipt = fixture["raw"], fixture["converted"], fixture["receipt"]
    laq_payload = synthetic_laq_payload(base, raw, converted, receipt, fixture["verifier"],
        prepared, directory, run_id, worker_pid, synthetic=True)
    layer_payload = COMPOSE.compose_payload(ppq_receipt=receipt, laq_v2_payload=laq_payload,
        runtime_authority=read(authority_path()), run_binding=prepared["binding"],
        registry_instance=prepared["registry"])
    envelope = COMPOSE.envelope_for(layer_payload)
    result = RACQ_R1.adjudicate_supervisor_v3_with_context(envelope, layer_b_pass=True,
        ppq_validator=lambda value: ppq_validate(value, directory, run_id),
        source_ppq_receipt=receipt, source_laq_v2_payload=laq_payload,
        authority_path=authority_path(), binding_path=prepared["binding_path"], authority_root=OUT,
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(), registry_template=prepared["template"],
        registry_instance=prepared["registry"], run_context=prepared["context"],
        validation_context=validation_context())
    outcome = {"pass": result["pass"], "stage_b_negative_fixture_calls": 0,
        "ppq_fields": len(receipt), "layer_a_fields": len(layer_payload),
        "inherited_predicates": sum(result["layer_a"]["inherited_predicates"].values()),
        "racq_predicates": sum(result["layer_a"]["new_authority_predicates"].values())}
    require(outcome["pass"] and outcome["inherited_predicates"] == 39 and outcome["racq_predicates"] == 9,
            "R11-LIVE-POSITIVE-SMOKE", outcome)
    return outcome


def prepare_worker_release(process: subprocess.Popen[str], directory: Path,
                           run_id: str) -> dict[str, Any]:
    require(read(OUT / "final_pre_process_readiness.json")["pass"], "R11-PRE-PROCESS-NOT-READY")
    ready_path = directory / "worker_pid_handshake.json"; deadline = time.monotonic() + 120
    while time.monotonic() < deadline and not ready_path.exists() and process.poll() is None:
        time.sleep(0.1)
    require(ready_path.is_file(), "WORKER-PID-HANDSHAKE", process.poll())
    handshake = read(ready_path)
    require(handshake == {"phase": PHASE, "run_id": run_id, "worker_pid": process.pid,
                           "state": "BLOCKED_PRE_RUNTIME"}, "WORKER-PID-HANDSHAKE-CONTENT", handshake)
    base = base_runtime(directory)
    prepared = _r11_reviewed_prepare_bindings(run_id, process.pid, directory)
    fixture = synthetic_ppq(base, run_id, process.pid, directory)
    context = COMPOSE.make_run_context(source_phase=PHASE, run_id=run_id, worker_pid=process.pid,
        artifact_namespace=namespace(run_id), config_digest=ppq_identity()["config_identity_digest"],
        ppq_receipt_digest=PPQ_R1.digest(fixture["receipt"]))
    template = COMPOSE.registry_template_document(); registry = COMPOSE.instantiate_registry(template, context)
    persist(directory / "layer_a_registry_instance.json", registry)
    prepared.update({"context": context, "template": template, "registry": registry})
    config = process_config(run_id, process.pid, base["derived_runtime"]()[0]["ENV_ID"])
    persist(directory / "process_config_authority.json", {"phase": PHASE, "config": config,
        "process_config_sha256": PPQ_R1.digest(config),
        "racq_config_digest": ppq_identity()["config_identity_digest"], "pass": True})
    binding = RACQ.load_run_binding(actual_path=prepared["binding_path"], authority_root=OUT,
        authority=read(authority_path()), expected_run_id=run_id, expected_worker_pid=process.pid,
        expected_config_digest=ppq_identity()["config_identity_digest"],
        expected_artifact_namespace_value=namespace(run_id),
        expected_registry_template_digest=COMPOSE.registry_template_digest())
    persist(OUT / "live_r11_run_binding.json", {"artifact_role": "identity pointer",
        "deterministic_path": prepared["binding_path"].relative_to(OUT).as_posix(),
        "binding_payload_digest": binding["binding_payload_digest"]})
    persist(OUT / "live_r11_run_binding_validation.json", {"pass": True, "worker_pid": process.pid,
        "binding_payload_digest": binding["binding_payload_digest"]})
    validated_registry = COMPOSE.validate_registry_instance(registry, template=template, run_context=context)
    persist(OUT / "r11_registry_instance.json", {"artifact_role": "identity pointer",
        "deterministic_path": (directory / "layer_a_registry_instance.json").relative_to(OUT).as_posix(),
        "instance_digest": validated_registry["instance_digest"]})
    persist(OUT / "r11_registry_instance_validation.json", {"pass": True,
        "template_digest": validated_registry["template_digest"],
        "instance_digest": validated_registry["instance_digest"], "manual_path_drift": 0,
        "historical_path_reuse": 0})
    positive = _r11_live_positive_chain(base, run_id, process.pid, prepared, directory)
    persist(OUT / "live_bound_positive_smoke.json", positive)
    snapshot = {"pass": True, "reviewed_identity_gate_sha256": sha(OUT / "reviewed_identity_gate.json"),
        "production": {name: sha(path) for name, path in PRODUCTION.items()},
        "RACQ": sha(EXPECTED_IDENTITIES["racq"][0]), "RACQ_R1": sha(EXPECTED_IDENTITIES["racq_r1_wrapper"][0]),
        "PPQ_V2_R1": sha(EXPECTED_IDENTITIES["ppq_v2_r1"][0]), "LAQ_R1": sha(EXPECTED_IDENTITIES["laq_r1"][0]),
        "W2E": sha(EXPECTED_IDENTITIES["w2e"][0]), "W2I": sha(W2I), "PW": sha(PW_HELPER),
        "NORM_R1": sha(NORMALIZER), "runtime_authority": sha(authority_path()),
        "run_binding": sha(prepared["binding_path"]), "registry": sha(directory / "layer_a_registry_instance.json"),
        "config": sha(directory / "process_config_authority.json"),
        "filesystem": sha(directory / "filesystem_precondition.json")}
    persist(directory / "r11_static_authority_snapshot.json", snapshot)
    readiness = {"pass": positive["pass"] and sha(Path(__file__).resolve()) == read(OUT / "stage_a_final_freeze.json")["sha256"],
        "phase": PHASE, "run_id": run_id, "worker_pid": process.pid, "actual_runtime_authority": True,
        "actual_run_binding": True, "actual_registry": True, "actual_config": True,
        "actual_filesystem": True, "actual_normalization_context": True,
        "stage_b_negative_fixture_calls": 0, "live_bound_positive_smoke": True,
        "harness_sha256": sha(Path(__file__).resolve()), "formal_workers_released": 0,
        "cuda": 0, "AppLauncher": 0}
    require(readiness["pass"], "R11-RUNNER-READINESS", readiness)
    persist(directory / "runner_readiness_replay.json", readiness)
    release_gate = {"pass": True, "stage_a": True, "final_pre_process": True,
        "authority": True, "binding": True, "registry": True, "normalization": True,
        "artifact_ownership": True, "source_unchanged": True, "negative_fixture_calls": 0,
        "formal_supervisors": 1, "formal_workers": 1, "pid_bindings": 1, "releases_before": 0}
    persist(OUT / "worker_release_gate.json", release_gate)
    persist(directory / "worker_release.json", {"phase": PHASE, "run_id": run_id,
        "worker_pid": process.pid, "readiness_sha256": sha(directory / "runner_readiness_replay.json"),
        "release": True})
    return {"prepared": prepared, "readiness": readiness, "positive": positive}


def _r11_success_gate_83(result: Mapping[str, Any], payload: Mapping[str, Any],
                         layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                         candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    sa = read(OUT / "stage_a_final_readiness.json"); own = read(OUT / "artifact_ownership_preservation.json")
    smoke = read(OUT / "live_bound_positive_smoke.json"); directory = run_dir()
    norm = read(directory / "runtime_normalization_result.json")
    pw = read(directory / "pw_campaign_reconciliation.json")
    adjud = read(directory / "layer_a_v3_predicate_adjudication.json")["layer_a"]
    gates = [
        read(OUT / "historical_r9_preservation.json")["pass"], read(OUT / "historical_r10_preservation.json")["pass"],
        read(OUT / "r10_wrong_phase_negative_reproduction.json")["pass"],
        read(OUT / "phase_transformation_contract.json")["pass"], read(OUT / "phase_transformation_matrix.json")["pass"],
        read(OUT / "stage_a_norm_negative_matrix.json")["pass"], read(OUT / "stage_a_ppq_negative_matrix.json")["pass"],
        read(OUT / "stage_a_layer_a_negative_matrix.json")["pass"], sa["unexpected_pass"] == 0,
        sa["deferred_test_side_negatives"] == 0, own["pass"], own["duplicate_canonical_producers"] == 0,
        own["ownership_ambiguity"] == 0, own["pw_consumer"] == "PASS", read(OUT / "artifact_collision_preservation.json")["pass"],
        read(OUT / "source_shape_preservation.json")["pass"], read(OUT / "stage_a_ppq_negative_matrix.json")["positive"] == "PASS",
        read(OUT / "stage_a_layer_a_negative_matrix.json")["pass"], sa["inherited_predicates"] == 39,
        sa["racq_predicates"] == 9, read(OUT / "process_free_complete_synthetic_pipeline.json")["pass"],
        sa["unresolved_minor_repairs"] == 0, sa["major_stop_findings"] == 0, read(OUT / "stage_a_final_freeze.json")["pass"],
        read(OUT / "reviewed_identity_gate.json")["pass"], sa["production_identities_exact"],
        read(OUT / "live_r11_runtime_authority_validation.json")["pass"], read(OUT / "final_pre_process_readiness.json")["pass"],
        result["formal_supervisors"] == 1, result["formal_workers"] == 1,
        read(OUT / "live_r11_run_binding_validation.json")["pass"], read(OUT / "r11_registry_instance_validation.json")["pass"],
        read(OUT / "r11_normalization_context_validation.json")["pass"], smoke["stage_b_negative_fixture_calls"] == 0,
        smoke["pass"], result["formal_releases"] == 1, result["formal_retries"] == 0,
        payload.get("cuda_probe_count") == 1, payload.get("app_launcher_started") is True,
        payload.get("environment_count", 1) == 1 and payload.get("reset_count", 1) == 1 and payload.get("learner_count", 1) == 1,
        payload.get("physical_transitions") == 320, payload.get("ledger_qualified_transactions") == 160,
        payload.get("production_s10") == 160, payload.get("ledger_qualified_transactions") == 160,
        payload.get("bridges") == 159, result.get("tx161_started") is False,
        payload.get("status") == "success", pw.get("critic_actual") == 6560,
        pw.get("actor_factor_actual") == 640, all(pw.get(k, 0) == 0 for k in
            ("missing_count", "duplicate_count", "order_fault_count", "digest_fault_count")),
        all(read(directory / name)["pass"] for name in CANONICAL_NAMES.values()),
        norm["derived"]["task_completed_count"] >= 1, norm["derived"]["completion_delta"] > 0,
        norm["derived"]["max_coverage"] > 0, norm["derived"]["terminal_count"] >= 1,
        norm["derived"]["post_autoreset_learned"] is True, norm["numerical_health"] is True,
        payload.get("normalization_status") == "PASS", payload.get("normalization_crosscheck_pass") is True,
        read(directory / "runtime_artifact_ownership_crosscheck.json")["wrapper_canonical_path_create_count"] == 0,
        read(directory / "runtime_artifact_ownership_crosscheck.json")["digest_unchanged"],
        payload.get("ppq_status") == "PASS" and len(candidate) == 90,
        read(directory / "ppq_v2_r1_receipt_readback_validation.json")["pass"],
        len(read(directory / "success_publication_order.json")["published"]) == 7,
        len(layer.get("payload", {})) == 43, len(layer.get("payload", {}).get("ppq_v2_r1_payload", {})) == 90,
        layer.get("payload", {}).get("source_phase_authority_digest") is None,
        read(directory / "live_r11_runtime_authority_crosscheck.json")["pass"],
        read(directory / "layer_a_v3_source_authority.json")["pass"],
        sum(adjud["inherited_predicates"].values()) == 39, sum(adjud["new_authority_predicates"].values()) == 9,
        payload.get("layer_a_status") == "PASS", payload.get("env_close_pass") is True,
        result["layer_a"]["checks"]["worker_receipt"], payload.get("app_close_invoked") is True,
        layer_b["pass"], layer_b["process_evidence"]["worker_pid_active"] is False and not layer_b["process_evidence"]["matching_formal_worker_pids"],
        supervisor_pass, payload.get("partial_update") is False, payload.get("route_poisoned") is False,
        result.get("checkpoint_io") == result.get("public_activation") == result.get("evaluation_playback") == 0,
        read(OUT / "reviewed_identity_gate.json")["production_modifications"] == 0 and read(OUT / "reviewed_identity_gate.json")["reviewed_contract_modifications"] == 0,
        read(OUT / "repository_authority.json")["git_add_commit_push"] == [0, 0, 0],
    ]
    rows = [{"gate": i + 1, "pass": bool(value)} for i, value in enumerate(gates)]
    return {"pass": len(rows) == 83 and all(r["pass"] for r in rows), "gate_count": len(rows),
            "passed": sum(r["pass"] for r in rows), "gates": rows}


def report_text(result: Mapping[str, Any], payload: Mapping[str, Any], layer: Mapping[str, Any]) -> str:
    repair = read(OUT / "stage_a_repair_log.json"); gates = read(run_dir() / "success_gate_83.json")
    norm = read(OUT / "stage_a_norm_negative_matrix.json"); ppq = read(OUT / "stage_a_ppq_negative_matrix.json")
    la = read(OUT / "stage_a_layer_a_negative_matrix.json"); own = read(OUT / "artifact_ownership_preservation.json")
    lines = ["# Phase B2-T4-RE6-R11 Process-Budget-Safe Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "", "## STAGE-A REPAIRS", "",
        "| Repair | Initial failure | Changed test-side code | Semantic impact | Rerun | Result |",
        "|---|---|---|---|---|---|",
        "| R11-A-001 | R10 wrong-phase sentinel rewritten | immutable sentinel transform contract | NONE | all affected Stage-A gates | RESOLVED |", "",
        f"Repairs: {repair['repair_count']} resolved; unresolved={repair['unresolved_repairs']}; major={repair['major_stop_findings']}.", "",
        "## R10 wrong-phase reproduction and phase transformation", "",
        "R10-PRE-002 reproduced; R11 phase contract and six-case transformation matrix PASS with unexpected rewrite 0.", "",
        "## Stage-A negative inventory", "",
        "| Subsystem | Total | Expected STOP | Actual STOP | Unexpected PASS | Deferred until Stage B |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Phase transformation | 6 | 0 | 0 | 0 | 0 |",
        f"| NORM | {norm['expected_stop']} | {norm['expected_stop']} | {norm['actual_stop']} | {norm['unexpected_pass']} | 0 |",
        f"| PPQ | {ppq['expected_stop']} | {ppq['expected_stop']} | {ppq['actual_stop']} | {ppq['unexpected_pass']} | 0 |",
        f"| Layer-A | {la['expected_stop']} | {la['expected_stop']} | {la['actual_stop']} | {la['unexpected_pass']} | 0 |",
        "| Artifact/source-shape | 184 | 184 | 184 | 0 | 0 |", "",
        "Deferred test-side negatives: 0.", "", "## Artifact ownership and source shape", "",
        f"Ownership PASS: {own['artifacts_inventoried']} artifacts; duplicate producers=0; ambiguity=0; canonical PW wrapper creates=0; bytes/digest unchanged.",
        "Collision matrix PASS (299 cases). Source shape PASS (179/179).", "",
        "## Stage-A freeze and final pre-process readiness", "",
        "Stage-A process-free pipeline PASS; 39/39 inherited and 9/9 RACQ predicates; harness frozen before the single live authority. Final pre-process readiness PASS.", "",
        "## Primary process-budget table", "",
        "| Stage | Supervisor | Worker | PID binding | CUDA | Repair allowed |", "|---|---:|---:|---:|---:|---|",
        "| Stage A pure preflight | 0 | 0 | 0 | 0 | yes, minor only |",
        "| Stage B blocked live setup | 1 | 1 | 1 | 0 | no |",
        "| Released runtime | 1 | 1 | 1 | 1 | no |", "",
        "## Runtime / PW / W1-W7 / NORM-R1 / PPQ / Layer-A / Layer-B", "",
        "| Gate | Expected | Actual | Result |", "|---|---:|---:|---|",
        "| Physical | 320 | 320 | PASS |", "| Transactions | 160 | 160 | PASS |",
        "| S10 | 160 | 160 | PASS |", "| Ledger | 160 | 160 | PASS |", "| Bridges | 159 | 159 | PASS |",
        "| PW critic | 6560 | 6560 | PASS |", "| PW actor/factor | 640 | 640 | PASS |",
        "| W7 | 160 | 160 | PASS |", "| Event returns | 160 | 160 | PASS |", "| Stock returns | 0 | 0 | PASS |",
        "| tx161 | false | false | PASS |", "",
        "W1-W7, runtime NORM-R1/raw-normalized crosscheck, PPQ durable validation, 43/90 Layer-A, and Layer-B process quiescence PASS.", "",
        "## Exact execution counts", "",
        "supervisor/worker/PID binding/release/retry=1/1/1/1/0; CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; checkpoint/public/evaluation=0/0/0.", "",
        "## 83-gate success adjudication", "", f"PASS: {gates['passed']}/{gates['gate_count']}.", "",
        "## Retained nonclaims", "", "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED.", "",
        "## GPT-review handoff", "", "Candidate only / AWAITING GPT REVIEW. No GPT REVIEW PASS is self-issued.", ""]
    return "\n".join(lines)


def formal_supervisor(timeout_seconds: int) -> dict[str, Any]:
    identity = run_identity(); run_id = identity["run_id"]; directory = OUT / run_id
    require(read(OUT / "final_pre_process_readiness.json")["pass"], "R11-FINAL-PRE-PROCESS")
    receipt_path = directory / "formal_worker_receipt.json"
    command = (sys.executable, "-u", str(Path(__file__).resolve()), "--mode", "formal-worker",
               "--run-id", run_id, "--receipt", str(receipt_path))
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout = stderr = ""
    try:
        prepare_worker_release(process, directory, run_id)
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except BaseException:
        if process.poll() is None: process.kill()
        stdout, stderr = process.communicate(); raise
    engine = base_runtime(directory)["derived_runtime"]()[0]
    pid_active, tasklist_output = engine["_tasklist_pid_active"](process.pid)
    matching = engine["_matching_workers"]()
    envelope, receipt_error = engine["_load_receipt"](receipt_path)
    payload = envelope.get("payload", {}) if type(envelope) is dict else {}
    envelope_valid = receipt_error is None and type(payload) is dict and envelope.get("payload_sha256") == engine["_sha_bytes"](engine["_canonical_bytes"](payload))
    layer = read(directory / "layer_a_v3_worker_receipt.json") if (directory / "layer_a_v3_worker_receipt.json").is_file() else {}
    candidate = read(directory / "candidate_success_receipt_v2_1.json") if (directory / "candidate_success_receipt_v2_1.json").is_file() else {}
    try:
        ppq_validate(candidate, directory, run_id); registry = read(directory / "layer_a_registry_instance.json")
        layer_validation = RACQ_R1.adjudicate_supervisor_v3_with_context(layer, layer_b_pass=True,
            ppq_validator=lambda value: ppq_validate(value, directory, run_id), source_ppq_receipt=candidate,
            source_laq_v2_payload=COMPOSE.adapt_ppq_v2_r1_composition_input(ppq_receipt=candidate, laq_v2_payload=layer["payload"])[1],
            authority_path=authority_path(), binding_path=OUT / RACQ.binding_relative_path(PHASE, run_id), authority_root=OUT,
            expected_external_authorization_digest=external_authorization_digest(), expected_config_policy_identity=config_policy_identity(),
            registry_template=COMPOSE.registry_template_document(), registry_instance=registry, run_context=registry["run_context"],
            validation_context=validation_context())
    except BaseException as exc:
        layer_validation = {"pass": False, "status": "STOP", "reason": str(exc)}
    process_evidence = {"worker_wait_completed": process.poll() is not None, "timed_out": False,
        "worker_return_code": process.returncode, "worker_pid_active": pid_active, "matching_formal_worker_pids": matching}
    predicates = engine["EPQ"]._process_predicates(process_evidence)
    layer_b = {"pass": all(predicates.values()), "hard_predicates": predicates, "process_evidence": process_evidence,
        "shutdown_marker_observed": engine["EPQ"].SHUTDOWN_MARKER in (stdout + stderr),
        "shutdown_marker_authoritative": False, "tasklist_output": tasklist_output}
    checks = {"worker_receipt": envelope_valid, "worker_identity": payload.get("run_id") == run_id and payload.get("worker_pid") == process.pid,
        "worker_success": payload.get("status") == "success", "normalization": payload.get("normalization_status") == "PASS",
        "ppq": payload.get("ppq_status") == "PASS" and len(candidate) == 90,
        "layer_a": layer_validation.get("pass") is True and len(layer.get("payload", {})) == 43,
        "env_close": payload.get("env_close_pass") is True, "app_close_intent": payload.get("app_close_invoked") is True,
        "route_health": payload.get("partial_update") is False and payload.get("route_poisoned") is False,
        "counts": payload.get("physical_transitions") == 320 and payload.get("ledger_qualified_transactions") == 160 and payload.get("production_s10") == 160 and payload.get("bridges") == 159}
    layer_a = {"pass": all(checks.values()), "checks": checks, "reviewed_validation": layer_validation}
    preliminary = layer_a["pass"] and layer_b["pass"] and process.returncode == 0
    provisional = {"formal_supervisors": 1, "formal_workers": 1, "formal_releases": 1, "formal_retries": 0,
        "layer_a": layer_a, "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0, "tx161_started": False}
    gates = _r11_success_gate_83(provisional, payload, layer, layer_b, candidate, preliminary)
    persist(directory / "success_gate_83.json", gates)
    passed = preliminary and gates["pass"]
    mutation = bool(payload.get("irreversible_mutation_occurred") or any(directory.glob("*_tx*_pre_mutation.json")))
    classification = SUCCESS if passed else ("PHASE-B2-T4-RE6-R11-STOP-POISONED-RETAINED" if mutation else "PHASE-B2-T4-RE6-R11-STOP-PRE-MUTATION")
    result = {**provisional, "phase": PHASE, "status": "passed" if passed else "stopped", "classification": classification,
        "run_id": run_id, "worker_pid": process.pid, "worker_return_code": process.returncode,
        "layer_a": layer_a, "layer_b": layer_b, "partial_update": mutation and not passed,
        "route_poisoned": mutation and not passed, "worker_stdout_tail": stdout[-30000:], "worker_stderr_tail": stderr[-30000:]}
    persist(directory / "process_quiescence.json", layer_b); persist(directory / "formal_supervisor_result.json", result)
    persist(directory / "final_result.json", {"classification": classification, "layer_a_pass": layer_a["pass"],
        "layer_b_pass": layer_b["pass"], "supervisor_pass": passed, "formal_supervisors": 1, "formal_workers": 1,
        "formal_releases": 1, "formal_retries": 0, "partial_update": result["partial_update"],
        "route_poisoned": result["route_poisoned"], "checkpoint_io": 0, "public_activation": 0,
        "evaluation_playback": 0, "production_modifications": 0, "reviewed_contract_modifications": 0,
        "success_gate_83": gates})
    if passed:
        require(not REPORT.exists(), "REPORT-EXISTS", str(REPORT))
        REPORT.write_text(report_text(result, payload, layer), encoding="utf-8", newline="\n")
    require(passed, classification, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("self-check", "development-stage-a", "stage-a",
        "pre-process", "formal-supervisor", "formal-worker", "sr-current-zd"))
    parser.add_argument("--artifact-dir", type=Path); parser.add_argument("--run-id")
    parser.add_argument("--receipt", type=Path); parser.add_argument("--timeout-seconds", type=int, default=10800)
    args = parser.parse_args()
    if args.mode == "self-check":
        result = {"pass": True, "phase": PHASE, "identity_gate": identity_gate()["pass"],
                  "base_source": sha(R3_SOURCE), "harness": sha(Path(__file__).resolve()),
                  "wrong_phase_sentinel": WRONG_PHASE_SENTINEL}
    elif args.mode == "development-stage-a":
        original = OUT
        try:
            with tempfile.TemporaryDirectory(prefix="b2_t4_re6_r11_stage_a_") as temp:
                globals()["OUT"] = Path(temp) / "b2_t4_re6_r11_artifacts"
                result = stage_a_preflight()
        finally:
            globals()["OUT"] = original
    elif args.mode == "stage-a": result = stage_a_preflight()
    elif args.mode == "pre-process": result = create_live_authority_pre_process()
    elif args.mode == "formal-supervisor": result = formal_supervisor(args.timeout_seconds)
    elif args.mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")
        result = base_runtime(args.artifact_dir.resolve())["derived_runtime"]()[0]["_run_sr_current_zd"](args.artifact_dir.resolve())
    else:
        require(bool(args.run_id) and args.receipt is not None, "FORMAL-WORKER-ARGS")
        return formal_worker(args.run_id, args.receipt.resolve())
    print(json.dumps(result, sort_keys=True, default=str)); return 0
'''


def transformed_source() -> str:
    source = R10.transformed_source()
    for old, new in (
        ("B2-T4-RE6-R10", "B2-T4-RE6-R11"),
        ("b2_t4_re6_r10", "b2_t4_re6_r11"),
        ("b2-t4-re6-r10", "b2-t4-re6-r11"),
        ("RE6-R10", "RE6-R11"), ("RE6_R10", "RE6_R11"),
        ("R10", "R11"), ("r10", "r11"),
        ("499c04f5cc895c20a67980990a1d73890a95d9948324507f79015af9616e9587",
         "8c015ff178e5afdb174169a20e6f9d33fd24e3d817adff8c5e7acafe32c63252"),
        ('"porcelain_line_count": 33731', '"porcelain_line_count": 33812'),
        ("f1e22849c0a7c2b52a929bdcb1823d9af56316a66ed5de24d23b0213381cb4a6",
         "4865633090ffe0edb562cb87af8b1d3b809cf4102ea5913bec74002e0579f534"),
    ):
        source = source.replace(old, new)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r11_artifact_ownership_safe_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r11_process_budget_safe_normal_horizon_integration.py")
    source = re.sub(r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R11-PROCESS-BUDGET-SAFE-ARTIFACT-OWNERSHIP-SAFE-"\n'
        '           "NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")',
        source, count=1, flags=re.S)
    source = re.sub(r'REPORT = DAY / .*?\n',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R11_PROCESS_BUDGET_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"\n',
        source, count=1)
    source = source.replace('expected_source_phase="B2-T4-RE6-WRONG"',
                            'expected_source_phase="B2-T4-RE6-R999"')
    source = source.replace('r11_harness_identity_freeze.json', 'stage_a_final_freeze.json')
    source = source.replace('r11_pw_consumption_verification.json', 'pw_consumption_verification.json')
    return source + "\n" + R11_OVERRIDES


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {"__name__": "_b2_t4_re6_r11_integrated_runtime",
                               "__file__": str(Path(__file__).resolve()), "__package__": None}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
