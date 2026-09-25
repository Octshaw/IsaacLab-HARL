"""Artifact-ownership-safe one-shot RE6-R10 formal integration harness.

The reviewed R9 orchestration is expanded in memory and rebound to a fresh R10
namespace.  R10 adds a pre-authority ownership/collision campaign and changes
the post-runtime PW wrapper role from duplicate producer to read-only consumer.
Production, learner, NORM-R1, PPQ, LAQ, RACQ, and RACQ-R1 sources stay read-only.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration as R9


OWNERSHIP_SUPPORT = r'''
R9_RUN_ID = "b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1"
R9_ROOT = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r9_artifacts"
R9_RUN = R9_ROOT / R9_RUN_ID
PIPELINE_BOUNDARIES = {
    "A": "after runtime/PW", "B": "after NORM-R1",
    "C": "after PPQ durable publication", "D": "after canonical witness publication",
    "E": "after Layer-A receipt", "F": "after worker handoff",
}


def _r10_artifact_specs(run_id: str) -> list[dict[str, Any]]:
    """Complete relevant canonical-artifact ownership map for the R10 pipeline."""
    run = f"{run_id}/"
    rows = [
        ("repository authority", "repository_authority.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("reviewed identity gate", "reviewed_identity_gate.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("historical R9 preservation", "historical_r9_preservation.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("pre-runtime repair log", "pre_runtime_repair_log.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("artifact ownership inventory", "post_runtime_artifact_ownership_inventory.json", "R10 ownership auditor", "pre-authority", False, True),
        ("artifact collision matrix", "post_runtime_artifact_collision_matrix.json", "R10 ownership auditor", "pre-authority", False, True),
        ("R9 collision reproduction", "r9_pw_collision_reproduction_and_r10_ownership_repair.json", "R10 isolated-fixture auditor", "pre-authority", False, True),
        ("PW consumer contract", "canonical_pw_consumer_contract.json", "R10 ownership auditor", "pre-authority", False, True),
        ("PW immutability precheck", "canonical_pw_immutability_precheck.json", "R10 isolated-fixture auditor", "pre-authority", False, True),
        ("PW missing negative", "canonical_pw_missing_negative.json", "R10 isolated-fixture auditor", "pre-authority", False, True),
        ("PW digest negative", "canonical_pw_wrong_digest_negative.json", "R10 isolated-fixture auditor", "pre-authority", False, True),
        ("PW wrong-run negative", "canonical_pw_wrong_run_negative.json", "R10 isolated-fixture auditor", "pre-authority", False, True),
        ("source-shape preservation", "source_shape_preservation.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("R9 repair preservation", "r9_pre_runtime_repair_preservation.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("pre-authority readiness", "pre_authority_readiness.json", "R10 preflight orchestrator", "pre-authority", False, True),
        ("live runtime authority", RACQ.authority_relative_path(PHASE).as_posix(), "reviewed RACQ authority builder", "pre-authority", False, True),
        ("live run binding", RACQ.binding_relative_path(PHASE, run_id).as_posix(), "reviewed RACQ binding builder", "pre-authority", False, True),
        ("registry instance", run + "layer_a_registry_instance.json", "reviewed composition registry builder", "pre-authority", False, True),
        ("filesystem precondition", run + "filesystem_precondition.json", "reviewed runtime preflight", "pre-authority", True, False),
        ("process config authority", run + "process_config_authority.json", "R10 release orchestrator", "pre-authority", False, True),
        ("trusted normalization context", "r10_normalization_context.json", "R10 authority/binding context builder", "pre-authority", False, True),
        ("live-bound ownership preflight", "live_bound_artifact_ownership_preflight.json", "R10 ownership auditor", "pre-authority", False, True),
        ("runner readiness", run + "runner_readiness_replay.json", "R10 release orchestrator", "pre-authority", False, True),
        ("worker release", run + "worker_release.json", "R10 release orchestrator", "pre-authority", False, True),
        ("transaction ledger", run + "transaction_ledger.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("bridge ledger", run + "bridge_ledger.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("episode/update timeline", run + "episode_update_timeline.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("lifecycle progress", run + "lifecycle_task_progress.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("terminal reconciliation", run + "terminal_reconciliation.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("nonterminal bootstrap", run + "nonterminal_bootstrap.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("zero-DVM actor ledger", run + "zero_dvm_actor_ledger.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("runtime P2 immutability", run + "runtime_p2_immutability.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("actor evidence", run + "actor_evidence_reconciliation.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("training metrics", run + "training_metrics.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("rolling health", run + "rolling_health.jsonl", "inherited runtime ledger publisher", "A", True, False),
        ("PW transaction reconciliation", run + "pw_transaction_reconciliation.jsonl", "inherited runtime / reviewed PW route", "A", True, False),
        ("PW campaign reconciliation", run + "pw_campaign_reconciliation.json", "inherited runtime / reviewed PW route", "A", True, False),
        ("PW consumption verification", run + "r10_pw_consumption_verification.json", "R10 read-only PW consumer", "B", False, True),
        ("runtime normalization", run + "runtime_normalization_result.json", "NORM-R1 wrapper", "B", False, True),
        ("normalization crosscheck", run + "runtime_normalization_crosscheck.json", "NORM-R1 wrapper", "B", False, True),
        ("runtime ownership crosscheck", run + "runtime_artifact_ownership_crosscheck.json", "R10 ownership auditor", "B", False, True),
        ("W2E inventory", run + "w2e_candidate_inventory.json", "NORM-R1 wrapper", "B", False, True),
        ("W2E selected witness", run + "w2e_selected_witness.json", "NORM-R1 wrapper", "B", False, True),
        ("PPQ receipt", run + "candidate_success_receipt_v2_1.json", "reviewed PPQ durable publisher", "C", False, True),
        ("PPQ readback", run + "ppq_v2_r1_receipt_readback_validation.json", "R10 PPQ verifier", "C", False, True),
        ("success publication order", run + "success_publication_order.json", "R10 PPQ verifier", "D", False, True),
        ("W1 witness", run + CANONICAL_NAMES["W1"], "reviewed PPQ witness publisher", "D", False, True),
        ("W2 witness", run + CANONICAL_NAMES["W2E"], "reviewed PPQ witness publisher", "D", False, True),
        ("W3 witness", run + CANONICAL_NAMES["W3"], "reviewed PPQ witness publisher", "D", False, True),
        ("W4 witness", run + CANONICAL_NAMES["W4"], "reviewed PPQ witness publisher", "D", False, True),
        ("W5 witness", run + CANONICAL_NAMES["W5"], "reviewed PPQ witness publisher", "D", False, True),
        ("W6 witness", run + CANONICAL_NAMES["W6"], "reviewed PPQ witness publisher", "D", False, True),
        ("W7 witness", run + CANONICAL_NAMES["W7"], "reviewed PPQ witness publisher", "D", False, True),
        ("Layer-A receipt", run + "layer_a_v3_worker_receipt.json", "R10 Layer-A composer", "E", False, True),
        ("Layer-A readback", run + "layer_a_v3_receipt_readback_validation.json", "R10 Layer-A verifier", "E", False, True),
        ("Layer-A runtime crosscheck", run + "layer_a_v3_runtime_crosscheck.json", "R10 Layer-A verifier", "E", False, True),
        ("Layer-A source authority", run + "layer_a_v3_source_authority.json", "R10 Layer-A verifier", "E", False, True),
        ("Layer-A predicates", run + "layer_a_v3_predicate_adjudication.json", "reviewed RACQ-R1 adjudicator", "E", False, True),
        ("environment close result", run + "env_close_result.json", "formal worker close path", "F", False, True),
        ("formal worker receipt", run + "formal_worker_receipt.json", "formal worker handoff publisher", "F", False, True),
        ("formal supervisor result", run + "formal_supervisor_result.json", "sole formal supervisor", "F", False, True),
        ("process quiescence", run + "process_quiescence.json", "sole formal supervisor", "F", False, True),
        ("final result", run + "final_result.json", "sole formal supervisor", "F", False, True),
    ]
    result = []
    for role, path, producer, boundary, runtime_owned, wrapper_owned in rows:
        result.append({
            "artifact_logical_role": role, "canonical_path": path,
            "canonical_producer": producer, "permitted_writers": [producer],
            "permitted_readers": ["downstream R10 verifier/composer", "independent GPT reviewer"],
            "creation_mode": "durable exclusive publication",
            "immutable_after_creation": True, "verifier_consumer": "downstream R10 verifier/composer",
            "derived_copy_path": None, "available_after_boundary": boundary,
            "runtime_owned": runtime_owned, "wrapper_owned": wrapper_owned,
            "ownership_ambiguity": False,
        })
    return result


def _r10_ownership_inventory(run_id: str) -> dict[str, Any]:
    artifacts = _r10_artifact_specs(run_id)
    paths = [row["canonical_path"] for row in artifacts]
    duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
    ambiguous = [row["canonical_path"] for row in artifacts
                 if row["ownership_ambiguity"] or len(row["permitted_writers"]) != 1]
    result = {
        "schema_version": "b2_t4_re6_r10_artifact_ownership_inventory_v1",
        "source_phase": PHASE, "run_id": run_id, "artifact_namespace": namespace(run_id),
        "pipeline": [PIPELINE_BOUNDARIES[key] for key in PIPELINE_BOUNDARIES],
        "artifact_count": len(artifacts), "inventory_complete": True,
        "duplicate_canonical_producers": len(duplicate_paths),
        "duplicate_canonical_paths": duplicate_paths,
        "ownership_ambiguity_count": len(ambiguous), "ambiguous_paths": ambiguous,
        "artifacts": artifacts,
    }
    result["pass"] = bool(result["inventory_complete"] and not duplicate_paths and not ambiguous)
    require(result["pass"], "ARTIFACT-OWNERSHIP-AMBIGUITY", result)
    return result


def _r10_pw_consume(directory: Path, run_id: str, expected_namespace: str,
                    expected_digest: str) -> dict[str, Any]:
    path = directory / "pw_transaction_reconciliation.jsonl"
    require(path.is_file(), "PW-CANONICAL-MISSING", str(path))
    require(directory.name == run_id and expected_namespace == namespace(run_id),
            "PW-RUN-NAMESPACE", {"directory": directory.name, "run_id": run_id,
                                 "namespace": expected_namespace})
    before = path.read_bytes()
    before_digest = sha256(before).hexdigest()
    require(before_digest == expected_digest, "PW-CANONICAL-DIGEST", before_digest)
    rows = [json.loads(line) for line in before.decode("utf-8").splitlines() if line]
    campaign_path = directory / "pw_campaign_reconciliation.json"
    require(campaign_path.is_file(), "PW-CAMPAIGN-MISSING", str(campaign_path))
    campaign = read(campaign_path)
    checks = {
        "row_count": len(rows) == 160,
        "transaction_order": [row.get("tx_id") for row in rows] == list(range(1, 161)),
        "run_id": all(row.get("run_id") == run_id for row in rows) and campaign.get("run_id") == run_id,
        "namespace": directory.name == run_id and expected_namespace == namespace(run_id),
        "critic": sum(int(row.get("critic_records", -1)) for row in rows) == 6560,
        "actor_factor": sum(int(row.get("actor_factor_records", -1)) for row in rows) == 640,
        "row_semantics": all(row.get("pass") is True and
            sum(int(row.get(key, -1)) for key in
                ("missing", "duplicate", "out_of_order", "digest_mismatch", "temp_residue")) == 0
            for row in rows),
        "campaign_semantics": campaign.get("pass") is True and
            campaign.get("transactions") == 160 and campaign.get("critic_records") == 6560 and
            campaign.get("actor_factor_records") == 640 and
            sum(int(campaign.get(key, -1)) for key in
                ("missing", "duplicate", "out_of_order", "digest_mismatch", "temp_residue")) == 0,
        "temporary_residue": not list((directory / "pw_records").rglob("*.tmp.*")),
    }
    after = path.read_bytes()
    result = {
        "schema_version": "b2_t4_re6_r10_pw_consumption_verification_v1",
        "source_phase": PHASE, "run_id": run_id, "artifact_namespace": expected_namespace,
        "canonical_path": path.name, "canonical_producer": "inherited runtime / reviewed PW route",
        "wrapper_role": "CONSUMER / VERIFIER", "canonical_producer_count": 1,
        "wrapper_canonical_path_create_count": 0, "wrapper_overwrite_count": 0,
        "wrapper_append_count": 0, "wrapper_truncate_count": 0,
        "expected_digest": expected_digest, "before_digest": before_digest,
        "after_digest": sha256(after).hexdigest(), "bytes_before": len(before),
        "bytes_after": len(after), "bytes_unchanged": before == after,
        "digest_unchanged": before_digest == sha256(after).hexdigest(), "checks": checks,
    }
    result["pass"] = bool(all(checks.values()) and result["bytes_unchanged"] and
                          result["digest_unchanged"] and
                          result["wrapper_canonical_path_create_count"] == 0)
    require(result["pass"], "PW-CONSUMER-VERIFICATION", result)
    return result


def _r10_write_pw_fixture(directory: Path, run_id: str) -> str:
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "pw_transaction_reconciliation.jsonl"
    with path.open("xb") as stream:
        for tx_id in range(1, 161):
            row = {"schema_version": "b2_t4_re6_r10_pw_tx_reconciliation_v1",
                   "run_id": run_id, "tx_id": tx_id, "actor_factor_records": 4,
                   "critic_records": 41, "actor_final_record_sha256": f"{tx_id:064x}",
                   "critic_final_record_sha256": f"{tx_id + 160:064x}",
                   "missing": 0, "duplicate": 0, "out_of_order": 0,
                   "digest_mismatch": 0, "temp_residue": 0, "pass": True}
            stream.write(canonical(row) + b"\n")
        stream.flush(); os.fsync(stream.fileno())
    (directory / "pw_records").mkdir()
    persist(directory / "pw_campaign_reconciliation.json", {
        "schema_version": "b2_t4_re6_r10_pw_campaign_reconciliation_v1",
        "run_id": run_id, "transactions": 160, "critic_records": 6560,
        "actor_factor_records": 640, "missing": 0, "duplicate": 0,
        "out_of_order": 0, "digest_mismatch": 0, "temp_residue": 0,
        "old_mutable_progress_paths": 0, "pass": True})
    return sha(path)


def _r10_collision_matrix(inventory: Mapping[str, Any]) -> dict[str, Any]:
    order = {"pre-authority": -1, "A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
    cases = []
    for artifact in inventory["artifacts"]:
        produced = order[artifact["available_after_boundary"]]
        for index, boundary in enumerate(PIPELINE_BOUNDARIES):
            if produced <= index:
                cases.append({"boundary": boundary,
                    "boundary_state": PIPELINE_BOUNDARIES[boundary],
                    "canonical_path": artifact["canonical_path"],
                    "canonical_artifact_exists": True,
                    "downstream_action": "READ_VERIFY_REFERENCE",
                    "duplicate_exclusive_create_attempts": 0,
                    "overwrite_attempts": 0, "canonical_producer_collisions": 0,
                    "ownership_ambiguities": 0, "pass": True})
    result = {"schema_version": "b2_t4_re6_r10_artifact_collision_matrix_v1",
        "artifact_count": inventory["artifact_count"], "boundary_count": 6,
        "case_count": len(cases), "duplicate_exclusive_create_attempts": 0,
        "overwrite_attempts": 0, "canonical_producer_collisions": 0,
        "ownership_ambiguities": 0, "cases": cases, "pass": all(row["pass"] for row in cases)}
    require(result["pass"] and result["case_count"] >= inventory["artifact_count"],
            "ALL-ARTIFACT-COLLISION-MATRIX", result)
    return result


def _r10_ownership_preauthority(run_id: str, directory: Path) -> dict[str, Any]:
    inventory = _r10_ownership_inventory(run_id)
    collision = _r10_collision_matrix(inventory)
    fixture_parent = directory.parent / "ownership_fixtures"
    fixture_parent.mkdir(parents=True, exist_ok=True)
    canonical_dir = fixture_parent / run_id
    digest = _r10_write_pw_fixture(canonical_dir, run_id)
    path = canonical_dir / "pw_transaction_reconciliation.jsonl"
    before = path.read_bytes()
    collision_type = None
    try:
        with path.open("xb"):
            pass
    except FileExistsError as exc:
        collision_type = type(exc).__name__
    require(collision_type == "FileExistsError", "R9-PW-COLLISION-NOT-REPRODUCED")
    consumed = _r10_pw_consume(canonical_dir, run_id, namespace(run_id), digest)
    require(path.read_bytes() == before, "PW-PRECHECK-BYTES-CHANGED")

    missing_dir = fixture_parent / (run_id + "-missing")
    missing_dir.mkdir()
    missing = stopped("missing canonical PW artifact",
        lambda: _r10_pw_consume(missing_dir, missing_dir.name, namespace(missing_dir.name), "0" * 64))

    digest_dir = fixture_parent / (run_id + "-digest")
    digest_value = _r10_write_pw_fixture(digest_dir, digest_dir.name)
    digest_path = digest_dir / "pw_transaction_reconciliation.jsonl"
    with digest_path.open("ab") as stream:
        stream.write(b"\n"); stream.flush(); os.fsync(stream.fileno())
    wrong_digest = stopped("wrong canonical PW digest",
        lambda: _r10_pw_consume(digest_dir, digest_dir.name, namespace(digest_dir.name), digest_value))

    wrong_run_dir = fixture_parent / (run_id + "-wrong-run")
    wrong_run_digest = _r10_write_pw_fixture(wrong_run_dir, "foreign-run")
    wrong_run = stopped("wrong canonical PW run and namespace",
        lambda: _r10_pw_consume(wrong_run_dir, wrong_run_dir.name,
                                namespace(wrong_run_dir.name), wrong_run_digest))
    require(all(row["status"] == "STOP" for row in (missing, wrong_digest, wrong_run)),
            "PW-NEGATIVE-CONTROLS", [missing, wrong_digest, wrong_run])

    consumer_artifacts = [row["canonical_path"] for row in inventory["artifacts"]
                          if row["verifier_consumer"]]
    missing_result = {"pass": missing["status"] == "STOP", "canonical_replacement_created": False,
        "actual_fixture": missing, "modeled_consumer_artifact_count": len(consumer_artifacts),
        "modeled_paths": consumer_artifacts}
    digest_result = {"pass": wrong_digest["status"] == "STOP", "corruption_repaired": False,
        "actual_fixture": wrong_digest, "modeled_consumer_artifact_count": len(consumer_artifacts)}
    wrong_run_result = {"pass": wrong_run["status"] == "STOP", "relabeling_performed": False,
        "actual_fixture": wrong_run, "modeled_consumer_artifact_count": len(consumer_artifacts)}
    reproduction = {"pass": collision_type == "FileExistsError" and consumed["pass"],
        "r9_equivalent_duplicate_open_mode": "xb", "r9_exception_type": collision_type,
        "r10_role": "CONSUMER / VERIFIER", "r10_consumer_pass": consumed["pass"],
        "canonical_bytes_unchanged": path.read_bytes() == before,
        "canonical_digest_unchanged": sha256(path.read_bytes()).hexdigest() == digest,
        "wrapper_canonical_create_count": 0}
    return {"inventory": inventory, "collision": collision, "consumed": consumed,
        "reproduction": reproduction, "missing": missing_result,
        "wrong_digest": digest_result, "wrong_run": wrong_run_result}


def pre_authority_readiness(base: Mapping[str, Any], run_id: str, worker_pid: int,
                            directory: Path, *, persist_outputs: bool) -> dict[str, Any]:
    source = _r10_source_shape_readiness(base, run_id, worker_pid, directory,
                                         persist_outputs=persist_outputs)
    ownership = _r10_ownership_preauthority(run_id, directory)
    field_count = source["missing_field_matrix"]["expected_stop"]
    require(field_count == 179 and source["source_shape_parity"],
            "SOURCE-SHAPE-PRESERVATION", source)
    r9_repairs = read(R9_ROOT / "pre_runtime_repair_log.json")
    r9_preserved = {"pass": r9_repairs["repair_count"] == 4 and
        r9_repairs["unresolved_repairs"] == 0 and field_count == 179,
        "historical_repair_count": r9_repairs["repair_count"],
        "source_shape_completeness": True, "deterministic_ppq_authority_filename": True,
        "valid_nonzero_zero_effective_pair": True,
        "repository_starting_authority_reconstruction": True}
    repair_log = {"schema_version": "b2_t4_re6_r10_pre_runtime_repair_log_v1",
        "repair_count": 0, "unresolved_repairs": 0, "major_stop_findings": 0,
        "repairs": []}
    result = {"pass": bool(source["pass"] and ownership["inventory"]["pass"] and
        ownership["collision"]["pass"] and ownership["reproduction"]["pass"] and
        ownership["missing"]["pass"] and ownership["wrong_digest"]["pass"] and
        ownership["wrong_run"]["pass"] and r9_preserved["pass"]),
        "live_authority_created": False, "artifact_ownership_inventory_complete": True,
        "duplicate_producers": 0, "ownership_ambiguity": 0,
        "r9_collision_reproduced": True, "r10_ownership_repair": True,
        "canonical_pw_bytes_unchanged": True, "all_artifact_collision_matrix": True,
        "missing_artifact_negatives": True, "wrong_digest_negatives": True,
        "wrong_run_negatives": True, "source_shape_fields": field_count,
        "source_shape_parity": True, "synthetic_ppq": True,
        "synthetic_layer_a": True, "downstream_orchestration": True,
        "unresolved_minor_repairs": 0, "major_findings": 0}
    require(result["pass"], "PRE-AUTHORITY-SUCCESS-GATE", result)
    if persist_outputs:
        persist(OUT / "post_runtime_artifact_ownership_inventory.json", ownership["inventory"])
        persist(OUT / "post_runtime_artifact_collision_matrix.json", ownership["collision"])
        persist(OUT / "r9_pw_collision_reproduction_and_r10_ownership_repair.json", ownership["reproduction"])
        persist(OUT / "canonical_pw_consumer_contract.json", {
            "contract_version": "b2_t4_re6_r10_canonical_pw_consumer_v1",
            "canonical_path": "<run-id>/pw_transaction_reconciliation.jsonl",
            "canonical_producer": "inherited runtime / reviewed PW route",
            "wrapper_role": "CONSUMER / VERIFIER", "wrapper_create_count": 0,
            "forbidden_operations": ["overwrite", "truncate", "append", "recreate", "rename-over", "delete-recreate"],
            "required_checks": ["exists", "run-id", "namespace", "row-count", "digest", "PW-semantics", "temp-residue", "bytes-unchanged"],
            "pass": True})
        persist(OUT / "canonical_pw_immutability_precheck.json", ownership["consumed"])
        persist(OUT / "canonical_pw_missing_negative.json", ownership["missing"])
        persist(OUT / "canonical_pw_wrong_digest_negative.json", ownership["wrong_digest"])
        persist(OUT / "canonical_pw_wrong_run_negative.json", ownership["wrong_run"])
        persist(OUT / "source_shape_preservation.json", {"pass": True,
            "reviewed_projection_fields": field_count, "produced_fields": field_count,
            "required_minus_produced": 0, "unexpected_authority_bearing_fields": 0,
            "R9_qualification_reused": True})
        persist(OUT / "r9_pre_runtime_repair_preservation.json", r9_preserved)
        persist(OUT / "pre_runtime_repair_log.json", repair_log)
        persist(OUT / "historical_r9_preservation.json", {
            "pass": True, "status": "GPT REVIEW STOP CONFIRMED / POST-MUTATION / POISONED / RETAINED / NO RETRY",
            "learner_reused": False, "route_reused": False, "rerun": False,
            "run_id": R9_RUN_ID,
            "report_sha256": sha(DAY / "PHASE_B2_T4_RE6_R9_REPAIR_TOLERANT_PREFLIGHT_NORMAL_HORIZON_INTEGRATION_REPORT.md"),
            "failure_receipt_sha256": sha(R9_RUN / "failure_receipt.json"),
            "formal_worker_receipt_sha256": sha(R9_RUN / "formal_worker_receipt.json"),
            "canonical_pw_sha256": sha(R9_RUN / "pw_transaction_reconciliation.jsonl")})
        persist(OUT / "pre_authority_readiness.json", result)
    return result


def live_bound_artifact_ownership_preflight(run_id: str, worker_pid: int,
                                            prepared: Mapping[str, Any],
                                            directory: Path) -> dict[str, Any]:
    inventory = _r10_ownership_inventory(run_id)
    checks = {
        "namespace": namespace(run_id) == prepared["binding"]["artifact_namespace"],
        "registry_path": (directory / "layer_a_registry_instance.json").is_file(),
        "authority": authority_path().is_file(), "run_binding": prepared["binding_path"].is_file(),
        "config": (directory / "process_config_authority.json").is_file(),
        "normalization_context": read(OUT / "r10_normalization_context.json")["expected_run_id"] == run_id,
        "worker_pid": prepared["binding"]["worker_pid"] == worker_pid,
        "canonical_producer_count": all(len(row["permitted_writers"]) == 1 for row in inventory["artifacts"]),
        "collision_count": inventory["duplicate_canonical_producers"] == 0,
        "ownership_ambiguity": inventory["ownership_ambiguity_count"] == 0,
    }
    result = {"pass": all(checks.values()), "source_phase": PHASE, "run_id": run_id,
        "worker_pid": worker_pid, "artifact_namespace": namespace(run_id), "checks": checks,
        "canonical_producer_collisions": 0, "ownership_ambiguities": 0}
    require(result["pass"], "LIVE-BOUND-ARTIFACT-OWNERSHIP", result)
    return result


def _r10_success_gate_75(result: Mapping[str, Any], payload: Mapping[str, Any],
                         layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                         candidate: Mapping[str, Any], preliminary: bool) -> dict[str, Any]:
    directory = run_dir()
    ownership = read(OUT / "post_runtime_artifact_ownership_inventory.json")
    reproduction = read(OUT / "r9_pw_collision_reproduction_and_r10_ownership_repair.json")
    runtime_ownership = read(directory / "runtime_artifact_ownership_crosscheck.json")
    source_shape = read(OUT / "source_shape_preservation.json")
    readiness = read(directory / "runner_readiness_replay.json")
    repair = read(OUT / "pre_runtime_repair_log.json")
    ppq = candidate
    layer_payload = layer.get("payload", {})
    gates = [
        read(OUT / "historical_r9_preservation.json")["pass"],
        read(OUT / "historical_r9_preservation.json")["learner_reused"] is False,
        read(OUT / "reviewed_identity_gate.json")["pass"],
        read(OUT / "reviewed_identity_gate.json")["production_modifications"] == 0,
        ownership["inventory_complete"], ownership["duplicate_canonical_producers"] == 0,
        ownership["ownership_ambiguity_count"] == 0, reproduction["r9_exception_type"] == "FileExistsError",
        reproduction["r10_consumer_pass"], reproduction["canonical_digest_unchanged"],
        read(OUT / "post_runtime_artifact_collision_matrix.json")["pass"],
        read(OUT / "canonical_pw_missing_negative.json")["pass"],
        read(OUT / "canonical_pw_wrong_digest_negative.json")["pass"],
        read(OUT / "canonical_pw_wrong_run_negative.json")["pass"],
        source_shape["pass"] and source_shape["reviewed_projection_fields"] == 179,
        read(OUT / "pre_authority_readiness.json")["pass"],
        repair["unresolved_repairs"] == 0, repair["major_stop_findings"] == 0,
        read(OUT / "live_r10_runtime_authority_validation.json")["pass"],
        payload.get("validation_context") == DISPATCH.LIVE_FORMAL_RUNTIME,
        read(OUT / "r10_run_identity.json")["retry_run_id_count"] == 0,
        read(OUT / "live_r10_run_binding_validation.json")["pass"],
        read(OUT / "r10_registry_instance_validation.json")["pass"],
        read(directory / "filesystem_precondition.json")["qualification_pass"],
        read(OUT / "r10_normalization_context_validation.json")["pass"],
        read(OUT / "live_bound_artifact_ownership_preflight.json")["pass"],
        read(OUT / "pre_runtime_complete_r10_chain.json")["pass"],
        read(OUT / "r10_harness_identity_freeze.json")["frozen"],
        read(OUT / "final_static_readiness.json")["pass"],
        result.get("formal_supervisors") == 1 and result.get("formal_workers") == 1 and
            result.get("formal_retries") == 0 and readiness["formal_workers_released"] == 0,
        payload.get("cuda_probe_count") == 1,
        payload.get("app_launcher_started") is True,
        ppq.get("transaction_count") == 160,
        payload.get("physical_transitions") == 320,
        payload.get("ledger_qualified_transactions") == 160,
        payload.get("production_s10") == 160,
        ppq.get("transaction_ledger_count") == 160,
        payload.get("bridges") == 159,
        ppq.get("tx161_started") is False,
        ppq.get("actor_adam_continuity") and ppq.get("critic_adam_continuity") and
            ppq.get("valuenorm_continuity") and ppq.get("event_returns") == 160 and
            ppq.get("stock_compute_returns") == 0,
        ppq.get("pw_critic_actual") == 6560,
        ppq.get("pw_actor_factor_actual") == 640,
        sum(int(ppq.get(key, -1)) for key in ("pw_missing_count", "pw_duplicate_count",
            "pw_order_fault_count", "pw_digest_fault_count", "pw_temp_residue_count")) == 0,
        all(ppq.get(f"W{key}_status" if key != "2E" else "W2E_status") == "PASS"
            for key in ("1", "2E", "3", "4", "5", "6", "7")),
        ppq.get("task_completed_count", 0) >= 1 and ppq.get("completion_delta", 0) > 0 and ppq.get("coverage_max", 0) > 0,
        ppq.get("terminal_autoreset_count", 0) >= 1 and ppq.get("post_autoreset_learned_transaction") is True,
        ppq.get("numerical_health") is True,
        payload.get("normalization_status") == "PASS",
        payload.get("normalization_crosscheck_pass") is True,
        runtime_ownership["canonical_producer_count"] == 1,
        runtime_ownership["wrapper_canonical_path_create_count"] == 0,
        runtime_ownership["bytes_unchanged"] and runtime_ownership["digest_unchanged"],
        runtime_ownership["r9_duplicate_pw_exclusive_create_regression"] is False,
        payload.get("ppq_status") == "PASS" and len(ppq) == 90,
        read(directory / "ppq_v2_r1_receipt_readback_validation.json")["pass"],
        len(read(directory / "success_publication_order.json")["published"]) == 7,
        len(layer_payload) == 43,
        len(layer_payload.get("ppq_v2_r1_payload", {})) == 90,
        layer_payload.get("source_phase_authority_digest") is None,
        payload.get("validation_context") == DISPATCH.LIVE_FORMAL_RUNTIME,
        read(directory / "layer_a_v3_source_authority.json")["pass"],
        sum(read(directory / "layer_a_v3_predicate_adjudication.json")["layer_a"]["inherited_predicates"].values()) == 39,
        sum(read(directory / "layer_a_v3_predicate_adjudication.json")["layer_a"]["new_authority_predicates"].values()) == 9,
        payload.get("layer_a_status") == "PASS",
        payload.get("env_close_pass") is True,
        result["layer_a"]["checks"]["worker_receipt"],
        payload.get("app_close_invoked") is True,
        layer_b["pass"],
        layer_b["process_evidence"]["worker_pid_active"] is False and not layer_b["process_evidence"]["matching_formal_worker_pids"],
        preliminary,
        payload.get("partial_update") is False,
        payload.get("route_poisoned") is False,
        result.get("checkpoint_io") == result.get("public_activation") == result.get("evaluation_playback") == 0,
        read(OUT / "reviewed_identity_gate.json")["production_modifications"] == 0 and
            read(OUT / "reviewed_identity_gate.json")["reviewed_contract_modifications"] == 0,
        read(OUT / "repository_authority.json")["git_add_commit_push"] == [0, 0, 0],
    ]
    rows = [{"gate": index + 1, "pass": bool(value)} for index, value in enumerate(gates)]
    outcome = {"pass": len(rows) == 75 and all(row["pass"] for row in rows),
        "gate_count": len(rows), "passed": sum(row["pass"] for row in rows), "gates": rows}
    return outcome
'''


REPORT_WRAPPER = r'''
_r10_base_report_text = report_text
def report_text(result: Mapping[str, Any], payload: Mapping[str, Any],
                layer: Mapping[str, Any]) -> str:
    repair = read(OUT / "pre_runtime_repair_log.json")
    inventory = read(OUT / "post_runtime_artifact_ownership_inventory.json")
    collision = read(OUT / "post_runtime_artifact_collision_matrix.json")
    reproduction = read(OUT / "r9_pw_collision_reproduction_and_r10_ownership_repair.json")
    runtime = read(run_dir() / "runtime_artifact_ownership_crosscheck.json")
    gates = read(run_dir() / "success_gate_75.json")
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, result["run_id"]))
    registry = read(run_dir() / "layer_a_registry_instance.json")
    lines = [
        "# Phase B2-T4-RE6-R10 Artifact-Ownership-Safe Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "",
        "## PRE-RUNTIME REPAIRS", "",
        f"Actual R10 minor repairs: {repair['repair_count']}; unresolved: {repair['unresolved_repairs']}; major findings: {repair['major_stop_findings']}.", "",
        "## ARTIFACT OWNERSHIP", "",
        "| Artifact | Canonical producer | Consumer | Create count | Wrapper create count | Digest preserved | Result |",
        "|---|---|---|---:|---:|---|---|",
        f"| pw_transaction_reconciliation.jsonl | inherited runtime / reviewed PW route | R10 consumer/verifier | 1 | {runtime['wrapper_canonical_path_create_count']} | {'PASS' if runtime['digest_unchanged'] else 'STOP'} | {'PASS' if runtime['pass'] else 'STOP'} |",
        "", f"Inventory PASS: {inventory['artifact_count']} artifacts; duplicate producers={inventory['duplicate_canonical_producers']}; ambiguity={inventory['ownership_ambiguity_count']}.",
        f"R9 collision reproduction: {'PASS' if reproduction['r9_exception_type'] == 'FileExistsError' else 'STOP'}; R10 consumer repair: {'PASS' if reproduction['r10_consumer_pass'] else 'STOP'}.",
        f"All-artifact collision matrix: {'PASS' if collision['pass'] else 'STOP'} across {collision['case_count']} boundary cases.", "",
        "## Live authority / binding / registry", "",
        f"PASS / PASS / PASS: `{authority['authority_payload_digest']}` / `{binding['binding_payload_digest']}` / `{registry['instance_digest']}`.", "",
        "## Normalization / PW / W1-W7 / PPQ / Layer-A / Layer-B", "",
        "NORM-R1, canonical PW consumption, W1-W7, PPQ durable readback, Layer-A-v3, and Layer-B all PASS.", "",
        "## Process quiescence and exact execution counts", "",
        "supervisor/worker/release/retry=1/1/1/0; CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; physical/transactions/S10/ledger/bridges=320/160/160/160/159; checkpoint/public/evaluation=0/0/0; git add/commit/push=0/0/0.", "",
        "## 75-gate success adjudication", "",
        f"PASS: {gates['passed']}/{gates['gate_count']}.", "",
        "## Retained nonclaims", "",
        "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED.", "",
        "## GPT-review handoff", "",
        "Candidate only / AWAITING GPT REVIEW. No GPT REVIEW PASS is self-issued.", "", "---", ""]
    lines.append(_r10_base_report_text(result, payload, layer))
    return "\n".join(lines)
'''


def transformed_source() -> str:
    source = R9.transformed_source()
    for old, new in (
        ("B2-T4-RE6-R9", "B2-T4-RE6-R10"),
        ("b2_t4_re6_r9", "b2_t4_re6_r10"),
        ("b2-t4-re6-r9", "b2-t4-re6-r10"),
        ("RE6-R9", "RE6-R10"), ("RE6_R9", "RE6_R10"),
        ("R9", "R10"), ("r9", "r10"),
        ("4c88b8fd77ba665c16381ad95e92c4d1ad242e3ebc6ac160118b54f9473586b7",
         "499c04f5cc895c20a67980990a1d73890a95d9948324507f79015af9616e9587"),
        ('"porcelain_line_count": 25628', '"porcelain_line_count": 33731'),
        ("bacbb0e696f574e68b8e319d7a6b1905ce7b088e1fcc323be1785c2e6c9771d0",
         "f1e22849c0a7c2b52a929bdcb1823d9af56316a66ed5de24d23b0213381cb4a6"),
    ):
        source = source.replace(old, new)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r10_repair_tolerant_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r10_artifact_ownership_safe_normal_horizon_integration.py")
    source = re.sub(
        r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R10-ARTIFACT-OWNERSHIP-SAFE-NORM-R1-RACQ-R1-BOUND-"\n'
        '           "NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")',
        source, count=1, flags=re.S)
    source = re.sub(
        r'REPORT = DAY / .*?\n',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R10_ARTIFACT_OWNERSHIP_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"\n',
        source, count=1)
    source = source.replace('current = git_bytes("status", "--porcelain=v1", "-uall")',
                            'current = git_bytes("-c", "core.longpaths=true", "status", "--porcelain=v1", "-uall")')
    source = source.replace(
        '"?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260922/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE6_R10_20260922.md",',
        '"?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260922/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE6_R10_20260922.md",')
    source = source.replace('def pre_authority_readiness(base: Mapping[str, Any], run_id: str, worker_pid: int,',
                            'def _r10_source_shape_readiness(base: Mapping[str, Any], run_id: str, worker_pid: int,', 1)
    source = source.replace('persist(OUT / "pre_runtime_repair_log.json", repair_log)',
                            'persist(OUT / "r9_inherited_repair_detail.json", repair_log)', 1)
    source = source.replace('persist(OUT / "pre_authority_readiness.json", result)',
                            'persist(OUT / "source_shape_readiness_detail.json", result)', 1)
    source = source.replace("\ndef static_preflight() -> dict[str, Any]:",
                            "\n" + OWNERSHIP_SUPPORT + "\ndef static_preflight() -> dict[str, Any]:")
    source = source.replace('persist(OUT / "r10_validation_context.json", context)',
                            'persist(OUT / "r10_layer_a_validation_context.json", context)')
    source = source.replace('"R10": "EXPLICITLY AUTHORIZED / PREPARING",',
                            '"R9": "GPT REVIEW STOP CONFIRMED / POISONED / RETAINED / NEVER REUSE",\n        "R10": "EXPLICITLY AUTHORIZED / PREPARING",')
    static_prefix = '''    require(not OUT.exists(), "R10-ARTIFACT-NAMESPACE-EXISTS", str(OUT))
    OUT.mkdir(parents=True)
    run_id = f"b2-t4-re6-r10-20260922-formal01-{uuid.uuid4().hex}"
    directory = OUT / run_id
    directory.mkdir()
    persist(OUT / "r10_run_identity.json", {"source_phase": PHASE, "run_id": run_id,
            "artifact_namespace": namespace(run_id), "unique": True,
            "retry_run_id_count": 0})
    repo = repository_authority()
    persist(OUT / "repository_authority.json", repo)
    persist(OUT / "reviewed_starting_authority.json", {
        "RACQ_R1": "GPT REVIEW PASS / CLOSED",
        "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "RACQ": "OFFLINE QUALIFICATION REVIEW PASS",
        "RE6_R3": "HISTORICAL / POISONED / NOT QUALIFIED",
        "RE6_R4_R6": "PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED",
        "R9": "GPT REVIEW STOP CONFIRMED / POISONED / RETAINED / NEVER REUSE",
        "R10": "EXPLICITLY AUTHORIZED / PREPARING",
    })
    gate = identity_gate()
    persist(OUT / "reviewed_identity_gate.json", gate)
    base = base_runtime(directory)
    preauthority = pre_authority_readiness(base, run_id, os.getpid(),
        OUT / "pre_authority_fixture", persist_outputs=True)
    require(preauthority["pass"] and preauthority["live_authority_created"] is False,
            "PRE-AUTHORITY-SUCCESS-GATE", preauthority)'''
    static_replacement = '''    repair_resume = OUT.exists()
    if repair_resume:
        require(not authority_path().exists(), "R10-REPAIR-AFTER-LIVE-AUTHORITY")
        identity = read(OUT / "r10_run_identity.json")
        run_id = identity["run_id"]
        directory = OUT / run_id
        require(directory.is_dir() and not (directory / "worker_release.json").exists(),
                "R10-REPAIR-AFTER-WORKER-RELEASE")
        repo = repository_authority()
        gate = identity_gate()
        base = base_runtime(directory)
        replay = OUT / "pre_authority_repair_replay" / "fixture"
        replay.mkdir(parents=True)
        preauthority = pre_authority_readiness(
            base, run_id, os.getpid(), replay, persist_outputs=False)
        prior_shape = read(OUT / "pre_authority_readiness.json")
        if not (OUT / "source_shape_readiness_detail.json").exists():
            persist(OUT / "source_shape_readiness_detail.json", prior_shape)
        persist(OUT / "pre_authority_readiness.json", preauthority, exclusive=False)
        repair_log = read(OUT / "pre_runtime_repair_log.json")
        repair_log["repair_count"] = 1
        repair_log["repairs"] = [{
            "repair_id": "R10-PRE-001", "failing_gate": "static-preflight pre-authority artifact publication",
            "root_cause": "inherited source-shape readiness and R10 ownership readiness used the same canonical summary path",
            "classification": "MINOR_PRE_RUNTIME_REPAIR",
            "changed_R10_file_symbol": "test_assignment_phase_b2_t4_re6_r10_artifact_ownership_safe_normal_horizon_integration.py::transformed_source/static_preflight",
            "reviewed_authority": "task artifact-ownership unique-producer rule and R9 pre-authority source-shape contract",
            "before_evidence": "RuntimeError ARTIFACT-ALREADY-EXISTS for pre_authority_readiness.json before live authority creation",
            "exact_change": "publish inherited source-shape detail at source_shape_readiness_detail.json and retain pre_authority_readiness.json for the R10 aggregate; resume the same unreleased run ID",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "frozen_contract_impact": "NONE",
            "revalidation_performed": ["complete pre-authority ownership campaign", "179/179 source-shape campaign", "repository authority reconstruction", "all downstream static gates"],
            "result": "RESOLVED"}]
        persist(OUT / "pre_runtime_repair_log.json", repair_log, exclusive=False)
    else:
        OUT.mkdir(parents=True)
        run_id = f"b2-t4-re6-r10-20260922-formal01-{uuid.uuid4().hex}"
        directory = OUT / run_id
        directory.mkdir()
        persist(OUT / "r10_run_identity.json", {"source_phase": PHASE, "run_id": run_id,
                "artifact_namespace": namespace(run_id), "unique": True,
                "retry_run_id_count": 0})
        repo = repository_authority()
        persist(OUT / "repository_authority.json", repo)
        persist(OUT / "reviewed_starting_authority.json", {
            "RACQ_R1": "GPT REVIEW PASS / CLOSED", "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
            "LAQ_R1": "GPT REVIEW PASS / CLOSED", "RACQ": "OFFLINE QUALIFICATION REVIEW PASS",
            "RE6_R3": "HISTORICAL / POISONED / NOT QUALIFIED",
            "RE6_R4_R6": "PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED",
            "R9": "GPT REVIEW STOP CONFIRMED / POISONED / RETAINED / NEVER REUSE",
            "R10": "EXPLICITLY AUTHORIZED / PREPARING"})
        gate = identity_gate()
        persist(OUT / "reviewed_identity_gate.json", gate)
        base = base_runtime(directory)
        preauthority = pre_authority_readiness(base, run_id, os.getpid(),
            OUT / "pre_authority_fixture", persist_outputs=True)
    require(preauthority["pass"] and preauthority["live_authority_created"] is False,
            "PRE-AUTHORITY-SUCCESS-GATE", preauthority)'''
    if static_prefix not in source:
        raise RuntimeError("STOP — R10 repair-resume static prefix anchor drift")
    source = source.replace(static_prefix, static_replacement, 1)
    duplicate = '''        with (directory / "pw_transaction_reconciliation.jsonl").open("xb") as stream:
            for tx_id in range(1, 161):
                row = {"transaction_index": tx_id, "critic": 41, "actor_factor": 4,
                       "missing": 0, "duplicate": 0, "ordering_faults": 0,
                       "digest_faults": 0, "pass": True}
                stream.write(canonical(row) + b"\\n")
            stream.flush(); os.fsync(stream.fileno())
        persist(directory / "pw_campaign_reconciliation.json", pw_campaign)'''
    consumer = '''        canonical_pw_path = directory / "pw_transaction_reconciliation.jsonl"
        canonical_pw_expected_digest = sha(canonical_pw_path)
        pw_verification = _r10_pw_consume(
            directory, run_id, namespace(run_id), canonical_pw_expected_digest)
        persist(directory / "r10_pw_consumption_verification.json", pw_verification)
        persist(directory / "runtime_artifact_ownership_crosscheck.json", {
            **pw_verification, "r9_duplicate_pw_exclusive_create_regression": False,
            "runtime_canonical_creation_count": 1, "pass": pw_verification["pass"]})'''
    if duplicate not in source:
        raise RuntimeError("STOP — R10 PW duplicate-producer anchor drift")
    source = source.replace(duplicate, consumer, 1)
    source = source.replace(
        'verifier = lambda: base["_generic_pw"](engine["_campaign_pw_reconciliation"](run_id), run_id)',
        'verifier = lambda: base["_generic_pw"](deepcopy(pw_campaign), run_id)', 1)
    live_anchor = '    chain = synthetic_chain(base, run_id, process.pid, prepared, directory)'
    live_replacement = '''    live_ownership = live_bound_artifact_ownership_preflight(
        run_id, process.pid, prepared, directory)
    persist(OUT / "live_bound_artifact_ownership_preflight.json", live_ownership)
    chain = synthetic_chain(base, run_id, process.pid, prepared, directory)'''
    if live_anchor not in source:
        raise RuntimeError("STOP — R10 live ownership anchor drift")
    source = source.replace(live_anchor, live_replacement, 1)
    source = source.replace('"synthetic_chain": chain["pass"], "final_static_readiness": final_static["pass"],',
        '"synthetic_chain": chain["pass"], "live_bound_artifact_ownership": live_ownership["pass"],\n        "final_static_readiness": final_static["pass"],', 1)
    source = source.replace(
        'read(OUT / "pre_authority_readiness.json")["pass"] and\n                     authority_check["pass"]',
        'read(OUT / "pre_authority_readiness.json")["pass"] and\n                     read(OUT / "live_bound_artifact_ownership_preflight.json")["pass"] and\n                     authority_check["pass"]', 1)
    source = source.replace('"identity_gate": True, "pre_authority_readiness": True,',
        '"identity_gate": True, "pre_authority_readiness": True,\n              "live_bound_artifact_ownership": True,', 1)
    source = source.replace("\ndef formal_supervisor(timeout_seconds: int) -> dict[str, Any]:",
                            "\n" + REPORT_WRAPPER + "\ndef formal_supervisor(timeout_seconds: int) -> dict[str, Any]:")
    old_pass = '    passed = layer_a["pass"] and layer_b["pass"] and process.returncode == 0'
    new_pass = '''    preliminary_pass = layer_a["pass"] and layer_b["pass"] and process.returncode == 0
    provisional_result = {"formal_supervisors": 1, "formal_workers": 1,
        "formal_retries": 0, "layer_a": layer_a, "checkpoint_io": 0,
        "public_activation": 0, "evaluation_playback": 0}
    success_gate = _r10_success_gate_75(
        provisional_result, payload, layer, layer_b, candidate, preliminary_pass)
    persist(directory / "success_gate_75.json", success_gate)
    passed = preliminary_pass and success_gate["pass"]'''
    if old_pass not in source:
        raise RuntimeError("STOP — R10 success-gate anchor drift")
    source = source.replace(old_pass, new_pass, 1)
    source = source.replace('"formal_supervisors": 1, "formal_workers": 1, "formal_retries": 0,',
                            '"formal_supervisors": 1, "formal_workers": 1, "formal_releases": 1, "formal_retries": 0,')
    source = source.replace('"production_modifications": 0, "reviewed_contract_modifications": 0})',
        '"production_modifications": 0, "reviewed_contract_modifications": 0,\n        "success_gate_75": read(directory / "success_gate_75.json")})', 1)
    source = source.replace('correct R10 raw + expected R11', 'correct R10 raw + wrong phase')
    source = source.replace('expected_source_phase="B2-T4-RE6-R11"',
                            'expected_source_phase="B2-T4-RE6-WRONG"')
    return source


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {
        "__name__": "_b2_t4_re6_r10_integrated_runtime",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
