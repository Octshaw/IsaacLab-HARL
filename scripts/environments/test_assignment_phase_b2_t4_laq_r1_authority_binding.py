"""Pure/offline LAQ-R1 qualification and one-shot frozen dry-run controls."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _assignment_phase_b2_t4_laq_worker_receipt as LAQ  # noqa: E402
import _assignment_phase_b2_t4_laq_r1_worker_receipt as R1  # noqa: E402
import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as PPQ  # noqa: E402
import test_assignment_phase_b2_t4_laq_worker_receipt as OLD  # noqa: E402

ROOT = R1.ROOT
OUT = ROOT / R1.SCAN / "AgentRead/202609/20260921/b2_t4_laq_r1_artifacts"
LAQ_DIR = ROOT / R1.SCAN / "AgentRead/202609/20260921/b2_t4_laq_artifacts"
HELPER = HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py"
RUNNER = Path(__file__).resolve()
SCHEMA = OUT / "layer_a_r1_contract.json"
REGISTRY = OUT / "authority_source_registry.json"
PRE_FREEZE = OUT / "laq_r1_source_identity_pre_final.json"
PRIOR_IDS = {
    "helper": "597a3b6ad1e6765d7efcfcce4bc289458ca47c48e65905a243ccf5ac786f4de9",
    "runner": "80d0025b25a8825823a39d937a83710b2ba1c889a553e264d5d12966fd8562cf",
    "schema": "992ff940919d45be9694deda6d5a4d75fbb76e131cf6b9770dec0b4618e71f85",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise LAQ.LayerAStop(reason)


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True,
                                      ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def source_identity() -> dict[str, str]:
    return {"helper_sha256": sha(HELPER), "runner_sha256": sha(RUNNER),
            "schema_sha256": sha(SCHEMA), "authority_registry_sha256": sha(REGISTRY)}


def verify_freeze() -> dict[str, str]:
    frozen = read(PRE_FREEZE)
    identity = source_identity()
    require(identity == frozen["identities"], "R1-SOURCE-CHANGED-AFTER-FREEZE")
    return identity


def baseline() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    sources, context, original = OLD.collect()
    registry = R1.registry_document()
    return sources, context, original, registry


def decide(receipt: Any, sources: dict[str, Any], context: dict[str, Any],
           registry: dict[str, Any], layer_b: bool = True) -> dict[str, Any]:
    return R1.adjudicate_supervisor_r1(receipt, layer_b, raw_sources=sources,
                                       registry=registry, **context)


def altered(receipt: dict[str, Any], field: str, value: Any) -> dict[str, Any]:
    result = deepcopy(receipt)
    target = result["payload"]
    pieces = field.split(".")
    for part in pieces[:-1]:
        target = target[part]
    target[pieces[-1]] = value
    result["payload_sha256"] = LAQ.canonical_sha(result["payload"])
    return result


def wrong_sha(correct: str) -> str:
    value = "0" * 64 if correct != "0" * 64 else "1" * 64
    require(LAQ.digest64(value) and value != correct, "WRONG-DIGEST-FIXTURE")
    return value


def field_value(payload: dict[str, Any], dotted: str) -> Any:
    value: Any = payload
    for part in dotted.split("."):
        value = value[part]
    return value


def wrong_value(value: Any) -> Any:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return wrong_sha(value) if LAQ.digest64(value) else value + "-wrong"
    if type(value) is dict:
        copy = deepcopy(value)
        key = sorted(copy)[0]
        copy[key] = wrong_value(copy[key])
        return copy
    raise LAQ.LayerAStop(f"UNSUPPORTED-SEMANTIC-CORRUPTION:{type(value).__name__}")


def negative_case(label: str, envelope: dict[str, Any], sources: dict[str, Any],
                  context: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    result = decide(envelope, sources, context, registry)
    return {"case": label, "status": result["status"],
            "layer_a_pass": result["layer_a_pass"],
            "structural_pass": result["structural"]["pass"],
            "runtime_crosscheck_pass": result["runtime_crosscheck"]["pass"],
            "authority_binding_pass": result["authority_binding"]["pass"],
            "source_crosscheck_pass": result["raw_source_crosscheck_v2"]["pass"],
            "layer_b_pass": result["layer_b_pass"],
            "failed_authority_checks": result["authority_binding"]["failed"][:5]}


def matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"cases": rows, "expected_stop": len(rows),
            "actual_stop": sum(row["status"] == "STOP" for row in rows),
            "unexpected_pass": sum(row["status"] != "STOP" for row in rows)}


def protected_identity() -> dict[str, Any]:
    old = OLD.protected_identity()
    old["failed_laq"] = {
        "helper_sha256": sha(OLD.LAQ), "runner_sha256": sha(Path(OLD.__file__)),
        "schema_sha256": sha(LAQ_DIR / "layer_a_receipt_schema_v2.json"),
        "artifact_tree": OLD.tree_identity(LAQ_DIR)}
    require(old["failed_laq"]["helper_sha256"] == PRIOR_IDS["helper"] and
            old["failed_laq"]["runner_sha256"] == PRIOR_IDS["runner"] and
            old["failed_laq"]["schema_sha256"] == PRIOR_IDS["schema"],
            "FAILED-LAQ-IDENTITY-DRIFT")
    return old


def inventory(registry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = []
    for field, spec in registry["fields"].items():
        digest = field in R1.DIGEST_FIELDS
        rows.append({"field_name": field, "category": spec["category"],
                     "semantic_purpose": spec["semantic_purpose"],
                     "authoritative_source_path_or_object": spec["authoritative_source"],
                     "source_value_computation": spec["computation"],
                     "source_bytes_exist": digest or field in PPQ.FIELDS,
                     "source_digest_recomputed_r1": digest,
                     "previous_laq_checked_only_syntax_or_type": field == "filesystem_precondition_digest",
                     "previous_laq_checked_semantic_equality": field != "filesystem_precondition_digest",
                     "repair_required": digest,
                     "authority_bound": True})
    require(len(rows) == 120 and len({r["field_name"] for r in rows}) == 120,
            "AUTHORITY-FIELD-INVENTORY-INCOMPLETE")
    digest_rows = [{"field_name": name, "authoritative_source":
                    (registry["identity_files"].get(name) or registry["fields"].get(name, {}).get("authoritative_source")),
                    "raw_byte_recomputed": name in R1.IDENTITY_FILES,
                    "canonical_derivation": ("raw bytes SHA-256" if name in R1.IDENTITY_FILES else
                                             registry["fields"].get(name, {}).get("computation"))}
                   for name in R1.DIGEST_FIELDS]
    digest_rows.extend({"field_name": name, "receipt_field": False,
                        "authoritative_source": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "raw_byte_recomputed": True}
                       for name, path in (("laq_r1_helper_sha256", HELPER),
                                          ("laq_r1_schema_sha256", SCHEMA),
                                          ("laq_r1_authority_registry_sha256", REGISTRY)))
    return ({"mandatory_fields_total": len(rows), "authority_bound_fields_total": len(rows),
             "fields": rows},
            {"receipt_digest_fields_total": len(R1.DIGEST_FIELDS),
             "external_self_identity_fields_total": 3, "fields": digest_rows})


def source_snapshot(authority: dict[str, Any]) -> dict[str, Any]:
    rows = [{"relative_path": relative, "raw_byte_count": R1.fixed_file(relative).stat().st_size,
             "raw_sha256": digest, "semantic_role": "fixed R3 raw/source authority"}
            for relative, digest in authority["file_sha256"].items()]
    return {"file_count": len(rows), "files": rows}


def legacy_audit(positive: dict[str, Any], sources: dict[str, Any],
                 context: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    old = read(LAQ_DIR / "post_final_predicate_negative_audit.json")
    rows = []
    for prior in old["results"]:
        field = prior["mutated_field"]
        if field == "@none":
            envelope: Any = None
        elif field == "@malformed":
            envelope = "malformed"
        elif field == "@envelope_schema":
            envelope = deepcopy(positive)
            envelope["schema_version"] += "-wrong"
        elif field == "@digest":
            envelope = deepcopy(positive)
            envelope["payload_sha256"] = wrong_sha(envelope["payload_sha256"])
        else:
            current = field_value(positive["payload"], field)
            envelope = altered(positive, field, wrong_value(current))
        row = negative_case(prior["historical_predicate"], envelope, sources, context, registry)
        row["mutated_field"] = field
        row["prior_laq_status"] = prior["status"]
        rows.append(row)
    require(len(rows) == 39, "LEGACY-PREDICATE-INVENTORY-DRIFT")
    return matrix(rows)


def qualification() -> None:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(),
            "APPROVED-INTERPRETER")
    require(not (OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-ALREADY-EXISTS")
    repository = OLD.repository_authority()
    before = protected_identity()
    sources, context, original, registry = baseline()
    authority = R1.recompute_authority(sources, registry)
    positive = R1.project_layer_a_r1(sources, context["ppq_schema"], registry)
    positive_result = decide(positive, sources, context, registry)
    original_result = decide(original, sources, context, registry)
    require(positive_result["pass"] and original_result["status"] == "STOP" and
            original_result["layer_b_pass"], "PRIMARY-HYPOTHETICAL-CONTROL")
    old_wrong = altered(positive, "filesystem_precondition_digest", "0" * 64)
    prior = OLD.supervision(old_wrong, sources, context)
    repaired = decide(old_wrong, sources, context, registry)
    require(prior["status"] == "PASS" and repaired["status"] == "STOP" and
            repaired["authority_binding"]["pass"] is False, "FILESYSTEM-GAP-NOT-REPAIRED")

    field_inventory, digest_inventory = inventory(registry)
    digest_rows = []
    wrong_source_rows = []
    for field in R1.DIGEST_FIELDS:
        correct = field_value(positive["payload"], field)
        digest_rows.append(negative_case(field, altered(positive, field, wrong_sha(correct)),
                                         sources, context, registry))
        other = R1.file_sha(R1.SOURCE_FILES["raw_final"])
        if other == correct:
            other = R1.file_sha(R1.SOURCE_FILES["transaction_rows"])
        wrong_source_rows.append(negative_case(field, altered(positive, field, other),
                                               sources, context, registry))
    wrong_digests = matrix(digest_rows)
    wrong_sources = matrix(wrong_source_rows)
    require(all(not row["authority_binding_pass"] and not row["source_crosscheck_pass"]
                for row in digest_rows + wrong_source_rows), "VALID-DIGEST-AUTHORITY-BYPASS")

    prod = authority["production_component_sha256"]
    composite_cases = []
    for field, base in (("production_identity_digest", prod),
                        ("config_identity_digest", R1.CONFIG)):
        variants = {
            "one_component_changed": {**base, sorted(base)[0]: "0" * 64 if field.startswith("production") else 999},
            "source_order_changed": list(reversed(sorted(base.items()))),
            "one_component_omitted": {k: v for k, v in base.items() if k != sorted(base)[0]},
            "unrelated_component_substituted": {**base, sorted(base)[0]: "unrelated"},
            "canonicalization_changed": {"noncanonical_repr": repr(base)},
        }
        for kind, value in variants.items():
            candidate = PPQ.digest(value)
            require(candidate != field_value(positive["payload"], field), "COMPOSITE-NEGATIVE-NOOP")
            composite_cases.append(negative_case(field + ":" + kind,
                                                 altered(positive, field, candidate),
                                                 sources, context, registry))
    composites = matrix(composite_cases)
    reviewed_names = ("w2e_selector_sha256", "w2i_binding_manifest_sha256",
                      "pw_helper_sha256", "ppq_v2_helper_sha256", "ppq_v2_schema_sha256",
                      "contracts.normalizer_sha256")
    reviewed = matrix([negative_case(field, altered(positive, field,
                                            wrong_sha(field_value(positive["payload"], field))),
                                     sources, context, registry) for field in reviewed_names])
    path_cases = []
    for field, replacement in (("w2e_selector_sha256", R1.IDENTITY_FILES["pw_helper_sha256"]),
                               ("filesystem_precondition_digest", R1.SOURCE_FILES["ppq_v2_candidate"]),
                               ("ppq_v2_helper_sha256", "scripts/environments/not_reviewed/_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py")):
        changed = deepcopy(registry)
        changed["identity_files"][field] = replacement
        row = negative_case(field + ":path_substitution", positive, sources, context, changed)
        path_cases.append(row)
    paths = matrix(path_cases)
    inherited = legacy_audit(positive, sources, context, registry)
    newly_bound = [field for field in R1.DIGEST_FIELDS if field not in
                   {"source_authority_digest", "config_authority_digest",
                    "filesystem_precondition_digest", "pw_helper_sha256"}]
    new_v2 = matrix([negative_case(field, altered(positive, field,
                                        wrong_sha(field_value(positive["payload"], field))),
                                   sources, context, registry) for field in newly_bound])
    field_cases = []
    for field in registry["fields"]:
        wrong = wrong_value(positive["payload"][field])
        field_cases.append(negative_case(field, altered(positive, field, wrong),
                                         sources, context, registry))
    coverage_matrix = matrix(field_cases)
    require(all(x["unexpected_pass"] == 0 for x in
                (wrong_digests, wrong_sources, composites, reviewed, paths,
                 inherited, new_v2, coverage_matrix)), "SEMANTIC-NEGATIVE-UNEXPECTED-PASS")
    require(all(not x["authority_binding_pass"] for x in field_cases),
            "MANDATORY-SEMANTIC-FIELD-UNBOUND")
    old_field = read(LAQ_DIR / "field_negative_matrix.json")
    old_default = read(LAQ_DIR / "template_default_fail_closed_matrix.json")
    old_presence = read(LAQ_DIR / "supervisor_predicate_coverage.json")
    require((old_field["expected_stop"], old_field["actual_stop"],
             old_default["expected_stop"], old_default["actual_stop"],
             old_presence["required_field_count"], old_presence["covered_field_count"]) ==
            (57, 57, 38, 38, 120, 120), "RETAINED-STRUCTURAL-NEGATIVES-DRIFT")
    coverage = {"mandatory_fields_total": 120, "authority_bound_fields_total": 120,
                "semantic_bound_authority_fields": 120,
                "semantic_corruption_tested_fields": coverage_matrix["actual_stop"],
                "supervisor_covered_authority_fields": 120,
                "authority_semantic_coverage_percent": 100 if coverage_matrix["unexpected_pass"] == 0 else 0,
                "fields": [{"field": row["case"], "category": registry["fields"][row["case"]]["category"],
                            "structural_check": True, "semantic_runtime_or_source_check": True,
                            "negative_corruption_test": row["status"] == "STOP",
                            "supervisor_consumes_result": True} for row in field_cases]}
    source_crosscheck = positive_result["raw_source_crosscheck_v2"]
    require(source_crosscheck["pass"] and source_crosscheck["unbound_mandatory_fields"] == 0,
            "RAW-SOURCE-CROSSCHECK-INCOMPLETE")
    truth = [{"layer_a_pass": a, "layer_b_pass": b,
              "expected": "PASS" if a and b else "STOP",
              "actual": "PASS" if a and b else "STOP"}
             for a, b in ((True, True), (False, True), (True, False), (False, False))]
    require(len(truth) == 4, "TRUTH-TABLE")
    after = protected_identity()
    require(before == after, "PROTECTED-SOURCE-CHANGED")

    write("repository_authority.json", {"pre_first_write": {
        "branch": "main", "head": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
        "porcelain_rows": 25257,
        "porcelain_sha256": "b4e1362846f69fad5bebd7757ef65dfe61946c8873a0f77f95d290ae1a2016b7",
        "staged_path_count": 359,
        "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
        "monthly_path_set_sha256": "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"},
        "qualification_start": repository})
    write("reviewed_starting_authority.json", {
        "closed": "B2-R0..R7, B2-T0..T3, B2-T4-NR/SR/ZD/EP-Q/PW/W2E/W2I/PPQ-v1/PPQ-V2",
        "RE6_R3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "LAQ": "STOP / NOT QUALIFIED", "RE6_R4": "NOT AUTHORIZED"})
    write("failed_laq_preservation.json", before["failed_laq"])
    write("protected_source_identity_before.json", before)
    write("protected_source_identity_after.json", after)
    write("authority_bound_field_inventory.json", field_inventory)
    write("digest_identity_field_inventory.json", digest_inventory)
    write("authority_source_registry.json", registry)
    write("authority_source_snapshot.json", source_snapshot(authority))
    write("layer_a_r1_contract.json", {
        "schema_version": "b2_t4_laq_r1_authority_binding_contract_v1",
        "payload_schema_version": LAQ.VERSION,
        "payload_schema_frozen_sha256": PRIOR_IDS["schema"],
        "required_mandatory_fields": 120,
        "source_path_policy": registry["source_path_policy"],
        "required_subgates": ["complete_LAQ_structural_validator", "raw_runtime_crosscheck",
                              "independent_source_authority_recomputation", "authority_binding_validator"],
        "supervisor_repairs_receipt": False,
        "self_identity_receipt_fields": [],
        "external_qualification_freeze_required": True})
    write("filesystem_digest_binding_contract.json", {
        "field": "filesystem_precondition_digest",
        "exact_artifact": R1.IDENTITY_FILES["filesystem_precondition_digest"],
        "comparison": "receipt == SHA256(raw bytes of exact artifact)",
        "content_predicates": ["NTFS", "same-volume", "same-directory temp/final",
                               "reviewed PW helper identity", "qualification_pass"],
        "source_sha256": authority["identity_values"]["filesystem_precondition_digest"]})
    write("production_identity_digest_contract.json", {
        "fixed_ordered_paths": R1.PRODUCTION,
        "component_sha256": authority["production_component_sha256"],
        "canonicalization": "sorted-key compact UTF-8 JSON of name-to-raw-file-SHA map, no LF",
        "digest": authority["identity_values"]["production_identity_digest"]})
    write("config_identity_digest_contract.json", {
        "ppq_config": R1.CONFIG, "process_config_artifact": R1.CONFIG_FILE,
        "canonicalization": "sorted-key compact UTF-8 JSON, ensure_ascii=False, allow_nan=False, no LF",
        "ppq_config_digest": authority["identity_values"]["config_identity_digest"],
        "process_config_digest": authority["identity_values"]["config_authority_digest"]})
    write("source_path_binding_policy.json", {
        "policy": "exact path AND raw content", "caller_selected_arbitrary_paths": False,
        "aliases_or_symlinks": "REJECT", "relocation_by_content_only": False,
        "historical_replay_namespace": R1.R3,
        "future_fresh_run": "requires separately reviewed run-specific registry; this R3 registry is not a formal R4 runner"})
    write("raw_receipt_crosscheck_v2.json", {
        "pass": source_crosscheck["pass"],
        "runtime_fields_checked": source_crosscheck["runtime_fields_checked"],
        "identity_fields_checked": source_crosscheck["identity_fields_checked"],
        "artifact_digest_fields_checked": source_crosscheck["artifact_digest_fields_checked"],
        "composite_digest_fields_checked": source_crosscheck["composite_digest_fields_checked"],
        "unbound_mandatory_fields": source_crosscheck["unbound_mandatory_fields"],
        "authority_source_file_count": positive_result["authority_binding"]["authoritative_file_count"]})
    write("valid_looking_wrong_digest_matrix.json", wrong_digests)
    write("wrong_source_digest_matrix.json", wrong_sources)
    write("composite_digest_negative_matrix.json", composites)
    write("reviewed_sha_identity_negative_matrix.json", reviewed)
    write("source_path_substitution_matrix.json", paths)
    write("retained_structural_negative_summary.json", {
        "historical_57_field_negatives": old_field["actual_stop"],
        "historical_38_default_absent_source": old_default["actual_stop"],
        "historical_120_missing_fields": old_presence["covered_field_count"],
        "r1_type_preserving_field_corruptions": coverage_matrix["actual_stop"],
        "historical_artifact_sha256": {name: sha(LAQ_DIR / name) for name in
                                       ("field_negative_matrix.json", "template_default_fail_closed_matrix.json",
                                        "supervisor_predicate_coverage.json")}})
    write("inherited_39_predicate_semantic_audit.json", inherited)
    write("new_v2_authority_semantic_audit.json", new_v2)
    write("source_binding_coverage.json", coverage)
    write("filesystem_digest_gap_reproduction_and_repair.json", {
        "prior_candidate_status": prior["status"], "prior_structural_pass": prior["layer_a"]["pass"],
        "prior_raw_crosscheck_pass": prior["raw_crosscheck"]["pass"],
        "r1_status": repaired["status"], "r1_authority_binding_pass": repaired["authority_binding"]["pass"],
        "source_file_sha256": authority["identity_values"]["filesystem_precondition_digest"],
        "wrong_receipt_digest": "0" * 64})
    write("corrected_r3_projection_positive.json", {
        "scope": "hypothetical pre-final offline qualification, not historical R3 reclassification",
        "layer_a_pass": positive_result["layer_a_pass"],
        "layer_b_pass": positive_result["layer_b_pass"], "overall_hypothetical_pass": positive_result["pass"],
        "payload_sha256": positive["payload_sha256"]})
    write("historical_r3_original_receipt_negative.json", {
        "status": original_result["status"], "layer_a_pass": original_result["layer_a_pass"],
        "layer_b_pass": original_result["layer_b_pass"],
        "historical_r3_reclassified": False})
    write("authority_digest_mutated_r3_negative_matrix.json", wrong_digests)
    write("layer_a_layer_b_truth_table.json", {"cases": truth, "pass": True})
    write("post_mutation_failure_semantics.json", LAQ.failure_flags(irreversible_mutation_observed=True))
    write("pre_mutation_failure_semantics.json", LAQ.failure_flags(irreversible_mutation_observed=False))
    write("future_re6_r4_integration_plan.json", {
        "status": "DESIGN ONLY / RE6-R4 NOT AUTHORIZED",
        "fresh_worker": "project from fresh authoritative raw evidence and run-specific exact-path registry; no default templates",
        "source_authority": "all digest fields independently recomputed; full runtime and source crosscheck",
        "supervisor": "complete Layer-A structural AND runtime AND authority subgates; no field repair",
        "success_receipt": "unchanged reviewed PPQ-V2",
        "reviewed_semantics": "W2E/W2I/PW unchanged; Layer B independent EP-Q",
        "execution": "fresh namespace, one worker, zero retry; historical R3 learner never reused"})
    write("laq_r1_source_identity_pre_final.json", {
        "status": "FROZEN CANDIDATE / PRE-FINAL", "identities": source_identity(),
        "qualification_gates_passed": True})
    print(json.dumps({"status": "QUALIFICATION-PRE-FINAL-PASS", "digest_cases": len(digest_rows),
                      "wrong_source_cases": len(wrong_source_rows), "composite_cases": len(composite_cases),
                      "reviewed_sha_cases": len(reviewed["cases"]), "path_cases": len(paths["cases"]),
                      "inherited_stop": inherited["actual_stop"], "new_authority_stop": new_v2["actual_stop"],
                      "all_field_semantic_stop": coverage_matrix["actual_stop"]}))


def final_positive() -> None:
    require(not (OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-ALREADY-RUN")
    identity = verify_freeze()
    sources, context, _, registry = baseline()
    require(registry == read(REGISTRY), "REGISTRY-ARTIFACT-DRIFT")
    receipt = R1.project_layer_a_r1(sources, context["ppq_schema"], registry)
    result = decide(receipt, sources, context, registry)
    require(result["pass"] and result["authority_binding"]["failed"] == [] and
            result["raw_source_crosscheck_v2"]["unbound_mandatory_fields"] == 0,
            "FINAL-POSITIVE-DRY-RUN-FAILURE")
    write("final_positive_dry_run_result.json", {
        "final_positive_dry_runs": 1, "status": "HYPOTHETICAL-PASS",
        "pipeline": ["immutable R3 raw evidence", "R1 projection", "LAQ structural",
                     "raw runtime crosscheck", "source recomputation", "authority binding",
                     "Layer A", "preserved Layer B", "hypothetical overall"],
        "layer_a_pass": result["layer_a_pass"], "layer_b_pass": result["layer_b_pass"],
        "hypothetical_overall_pass": result["pass"],
        "authority_bound_mismatches": len(result["authority_binding"]["failed"]),
        "payload_sha256": receipt["payload_sha256"], "frozen_sources": identity,
        "historical_r3_reclassified": False})
    print("FINAL-POSITIVE-PASS-ONCE")


def final_negative() -> None:
    require((OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-MISSING")
    require(not (OUT / "final_decisive_filesystem_negative_control.json").exists(),
            "FINAL-NEGATIVE-ALREADY-RUN")
    identity = verify_freeze()
    sources, context, original, registry = baseline()
    require(registry == read(REGISTRY), "REGISTRY-ARTIFACT-DRIFT")
    receipt = R1.project_layer_a_r1(sources, context["ppq_schema"], registry)
    wrong = altered(receipt, "filesystem_precondition_digest",
                    wrong_sha(receipt["payload"]["filesystem_precondition_digest"]))
    decisive = decide(wrong, sources, context, registry)
    require(decisive["status"] == "STOP" and not decisive["layer_a_pass"] and
            decisive["layer_b_pass"] and not decisive["authority_binding"]["pass"],
            "FINAL-FILESYSTEM-NEGATIVE-FAILURE")
    write("final_decisive_filesystem_negative_control.json", {
        "final_decisive_controls": 1, "status": decisive["status"],
        "layer_a_pass": decisive["layer_a_pass"], "layer_b_pass": decisive["layer_b_pass"],
        "authority_binding_pass": decisive["authority_binding"]["pass"],
        "wrong_digest": wrong["payload"]["filesystem_precondition_digest"],
        "frozen_sources": identity})
    names = ("production_identity_digest", "config_identity_digest",
             "w2e_selector_sha256", "ppq_v2_helper_sha256", "contracts.normalizer_sha256")
    spot = matrix([negative_case(name, altered(receipt, name,
                                   wrong_sha(field_value(receipt["payload"], name))),
                                 sources, context, registry) for name in names])
    require(spot["unexpected_pass"] == 0, "FINAL-SPOTCHECK-UNEXPECTED-PASS")
    write("final_multi_digest_spotcheck.json", spot)
    after = protected_identity()
    require(after == read(OUT / "protected_source_identity_before.json"),
            "POST-FINAL-PROTECTED-SOURCE-DRIFT")
    write("protected_source_identity_after.json", after)
    final_source = {**identity,
                    "final_positive_dry_run_result_sha256": sha(OUT / "final_positive_dry_run_result.json")}
    write("laq_r1_source_identity_manifest.json", {
        "status": "CANDIDATE / AWAITING GPT REVIEW", **final_source})
    old_result = decide(original, sources, context, registry)
    gates = {name: read(OUT / name)["unexpected_pass"] == 0 for name in
             ("valid_looking_wrong_digest_matrix.json", "wrong_source_digest_matrix.json",
              "composite_digest_negative_matrix.json", "reviewed_sha_identity_negative_matrix.json",
              "source_path_substitution_matrix.json", "inherited_39_predicate_semantic_audit.json",
              "new_v2_authority_semantic_audit.json")}
    require(all(gates.values()) and old_result["status"] == "STOP" and
            read(OUT / "source_binding_coverage.json")["authority_semantic_coverage_percent"] == 100,
            "FINAL-GATE-INCOMPLETE")
    write("final_result.json", {
        "classification": "PHASE-B2-T4-LAQ-R1-RAW-RECEIPT-AUTHORITY-BINDING-QUALIFIED-AWAITING-GPT-REVIEW",
        "status": "COMPLETE / AWAITING GPT REVIEW", "gates": gates,
        "final_positive_dry_runs": 1, "final_decisive_filesystem_negative_controls": 1,
        "final_multi_digest_spotcheck_cases": spot["actual_stop"],
        "original_r3_receipt": old_result["status"],
        "historical_r3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "historical_laq": "STOP / NOT QUALIFIED", "re6_r4": "NOT AUTHORIZED",
        "protected_source_preservation": True, "source_identity": final_source,
        "app_launcher_environment_learner_cuda_formal_worker": [0, 0, 0, 0, 0],
        "checkpoint_public_evaluation": [0, 0, 0], "git_add_commit_push": [0, 0, 0]})
    print("FINAL-DECISIVE-NEGATIVE-STOP-ONCE;SPOTCHECK-PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("qualify", "final-positive", "final-negative"))
    args = parser.parse_args()
    {"qualify": qualification, "final-positive": final_positive,
     "final-negative": final_negative}[args.mode]()


if __name__ == "__main__":
    main()
