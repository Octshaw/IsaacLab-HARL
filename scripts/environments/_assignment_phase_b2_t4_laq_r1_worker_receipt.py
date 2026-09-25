"""Pure LAQ-R1 source authority overlay for the frozen LAQ structural receipt.

The old LAQ candidate is deliberately imported without modification.  Its
structure is necessary, but never sufficient: every accepted R1 receipt is
compared to fixed-path raw evidence and independently recomputed identities.
This module imports no Isaac, CUDA, environment, or learner implementation.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import _assignment_phase_b2_t4_laq_worker_receipt as LAQ
import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as PPQ


ROOT = Path(__file__).resolve().parents[2]
SCAN = "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
R3 = f"{SCAN}/AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"
DAY20 = f"{SCAN}/AgentRead/202609/20260920"
SCRIPT = "scripts/environments"
CONFIG = {"expected_transaction_count": 160, "expected_T": 2,
          "critic_records_per_tx": 41, "actor_factor_records_per_tx": 4}
SOURCE_FILES = {
    "raw_final": f"{R3}/b2_t4_re6_r3_normal_horizon_20260920_formal01_final_result.json",
    "ppq_v2_candidate": f"{R3}/candidate_success_receipt.json",
    "ppq_v2_readback": f"{R3}/success_receipt_readback_validation.json",
    "normalized": f"{R3}/runtime_normalization_result.json",
    "worker_handoff": f"{R3}/formal_worker_receipt.json",
    "pw_verifier": f"{R3}/pw_campaign_reconciliation.json",
    "w2e_result": f"{R3}/W2_multi_update_completion_v2.json",
    "transaction_rows": f"{R3}/transaction_ledger.jsonl",
    "bridge_rows": f"{R3}/bridge_ledger.jsonl",
    "lifecycle_rows": f"{R3}/lifecycle_task_progress.jsonl",
    "terminal_rows": f"{R3}/terminal_reconciliation.jsonl",
    "zero_dvm_rows": f"{R3}/zero_dvm_actor_ledger.jsonl",
    **{f"witness:{key}": f"{R3}/{name}" for key, name in {
        "W1": "W1_cross_update_ownership.json",
        "W2E": "W2_multi_update_completion_v2.json",
        "W3": "W3_real_zero_dvm_actor.json",
        "W4": "W4_real_nonterminal_bootstrap.json",
        "W5": "W5_normal_horizon_terminal_autoreset.json",
        "W6": "W6_post_autoreset_training.json",
        "W7": "W7_runtime_p2_immutability.json",
    }.items()},
}
IDENTITY_FILES = {
    "source_authority_digest": f"{R3}/re6_r3_static_authority.json",
    "filesystem_precondition_digest": f"{R3}/filesystem_precondition.json",
    "ppq_v2_candidate_sha256": SOURCE_FILES["ppq_v2_candidate"],
    "w2e_selector_sha256": f"{SCRIPT}/_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i_binding_manifest_sha256": f"{DAY20}/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw_helper_sha256": f"{SCRIPT}/_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "ppq_v2_helper_sha256": f"{SCRIPT}/_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py",
    "ppq_v2_schema_sha256": f"{DAY20}/b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json",
    "contracts.normalizer_sha256": f"{SCRIPT}/_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
}
PRODUCTION = {
    "environment": f"{SCAN}/scan_mobile_manipulator_env.py",
    "full_transaction": f"{SCAN}/assignment_event_training_full_transaction.py",
    "real_isaac_adapter": f"{SCAN}/assignment_event_training_real_isaac_adapter.py",
}
CONFIG_FILE = f"{R3}/process_config_authority.json"
REVIEWED_SHA = {
    "w2e_selector_sha256": "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0",
    "w2i_binding_manifest_sha256": "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b",
    "pw_helper_sha256": "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b",
    "ppq_v2_helper_sha256": "115d681d5e8473aa171e6232b6beca8c985139a58926d6d15850c2940785f903",
    "ppq_v2_schema_sha256": "0742a9a0ed44cb1f3410fae8885e348f7a40b7dbc35ac089ca6cf920d89126d5",
    "contracts.normalizer_sha256": "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3",
}
PRODUCTION_SHA = {
    "environment": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    "full_transaction": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "real_isaac_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
}
DIGEST_FIELDS = (*IDENTITY_FILES, "config_authority_digest",
                 "production_identity_digest", "config_identity_digest")
VERSION_FIELDS = {"contract_version", "w2e_contract_version", "pw_contract_version",
                  "layer_a_contract_version"}
CALLER_FIELDS = {"source_phase", "run_id", "worker_pid"}
RELATIONAL_FIELDS = {"expected_transaction_count", "expected_T", "physical_transitions",
                     "production_s10", "transaction_ledger_count", "bridge_count",
                     "S10_count", "ledger_count", "event_returns_count",
                     "stock_compute_returns_count", "TASK_COMPLETED_count", "max_coverage",
                     "invalid_critic_class_count", "pw_transaction_count",
                     "pw_critic_expected", "pw_actor_factor_expected", "contracts"}


def fixed_file(relative: str) -> Path:
    """No caller-selected path, symlink, directory, or traversal is authority."""
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise LAQ.LayerAStop(f"SOURCE-PATH-UNSAFE:{relative}")
    path = ROOT / relative
    if not path.is_file() or path.is_symlink() or path.resolve() != (ROOT / relative).resolve():
        raise LAQ.LayerAStop(f"SOURCE-PATH-MISSING-OR-ALIAS:{relative}")
    return path


def file_sha(relative: str) -> str:
    return sha256(fixed_file(relative).read_bytes()).hexdigest()


def read_json(relative: str) -> Any:
    return json.loads(fixed_file(relative).read_bytes())


def read_rows(relative: str) -> list[Any]:
    return [json.loads(line) for line in fixed_file(relative).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def registry_document() -> dict[str, Any]:
    """Fixed authority definitions; each of the 120 fields gets exactly one."""
    fields: dict[str, dict[str, Any]] = {}
    for name in (*PPQ.FIELDS, *LAQ.EXTRA_TYPES):
        if name in fields:
            raise LAQ.LayerAStop(f"DUPLICATE-FIELD:{name}")
        if name in IDENTITY_FILES:
            category = ("ARTIFACT_CONTENT_DIGEST" if name in
                        {"source_authority_digest", "filesystem_precondition_digest",
                         "ppq_v2_candidate_sha256", "w2i_binding_manifest_sha256",
                         "ppq_v2_schema_sha256"} else "REVIEWED_SOURCE_IDENTITY")
            source = IDENTITY_FILES[name]
            computation = "SHA256(raw bytes of fixed-path file)"
        elif name == "config_authority_digest":
            category, source = "ARTIFACT_CONTENT_DIGEST", CONFIG_FILE
            computation = "SHA256(canonical UTF-8 JSON of process_config_authority.config)"
        elif name == "production_identity_digest":
            category, source = "MULTI_SOURCE_COMPOSITE_DIGEST", PRODUCTION
            computation = "SHA256(canonical UTF-8 JSON of fixed ordered raw-file SHA map)"
        elif name == "config_identity_digest":
            category, source = "MULTI_SOURCE_COMPOSITE_DIGEST", [CONFIG_FILE, "frozen formal cadence"]
            computation = "SHA256(canonical UTF-8 JSON of four-field qualified PPQ config)"
        elif name == "contracts":
            category, source = "REVIEWED_SOURCE_IDENTITY", [SOURCE_FILES["ppq_v2_candidate"],
                                                              IDENTITY_FILES["contracts.normalizer_sha256"]]
            computation = "exact nested projection plus independently recomputed source identities"
        elif name in VERSION_FIELDS:
            category, source, computation = "CONTRACT_VERSION_IDENTITY", "frozen LAQ/PPQ/W2E/PW contract", "exact version string"
        elif name in CALLER_FIELDS:
            category, source, computation = "CALLER_BOUND_IDENTITY", [CONFIG_FILE, SOURCE_FILES["raw_final"]], "exact run/phase/PID binding"
        elif name in RELATIONAL_FIELDS:
            category, source, computation = "RELATIONAL_RUNTIME_DERIVATION", SOURCE_FILES, "exact projection and raw relation"
        else:
            category = "DIRECT_RUNTIME_OBSERVATION"
            source = SOURCE_FILES["ppq_v2_candidate"] if name in PPQ.FIELDS else SOURCE_FILES
            computation = "exact frozen candidate/raw-evidence projection and runtime crosscheck"
        fields[name] = {"field_name": name, "category": category,
                        "semantic_purpose": f"qualify exact Layer-A {name} value",
                        "source_kind": "fixed_file_or_explicit_raw_object",
                        "authoritative_source": source, "computation": computation,
                        "canonicalization": "raw bytes for file SHA; sorted-key compact UTF-8 JSON without LF for composites"}
    return {"schema_version": "b2_t4_laq_r1_authority_registry_v1",
            "payload_schema": LAQ.VERSION, "fields": fields,
            "source_files": SOURCE_FILES, "identity_files": IDENTITY_FILES,
            "production_files": PRODUCTION, "config_file": CONFIG_FILE,
            "source_path_policy": "exact repository-relative path AND raw content; no alias or relocation"}


def _checked_registry(registry: Mapping[str, Any]) -> None:
    if type(registry) is not dict or registry != registry_document():
        raise LAQ.LayerAStop("AUTHORITY-REGISTRY-PATH-OR-DEFINITION-DRIFT")


def _source_object(name: str, relative: str) -> Any:
    value = read_rows(relative) if relative.endswith(".jsonl") else read_json(relative)
    return value["payload"] if name == "worker_handoff" else value


def recompute_authority(sources: Mapping[str, Any], registry: Mapping[str, Any]) -> dict[str, Any]:
    """Independent raw-file recomputation; receipt values are never inputs."""
    _checked_registry(registry)
    if type(sources) is not dict:
        raise LAQ.LayerAStop("RAW-SOURCES-NOT-OBJECT")
    for name, relative in SOURCE_FILES.items():
        actual = (sources.get("witnesses", {}).get(name.split(":", 1)[1])
                  if name.startswith("witness:") else sources.get(name))
        if actual != _source_object(name, relative):
            raise LAQ.LayerAStop(f"RAW-SOURCE-FILE-MISMATCH:{name}")
    if sources.get("ppq_v2_candidate_file_sha256") != file_sha(IDENTITY_FILES["ppq_v2_candidate_sha256"]):
        raise LAQ.LayerAStop("CANDIDATE-SOURCE-DIGEST-MISMATCH")
    if sources.get("normalizer_sha256") != file_sha(IDENTITY_FILES["contracts.normalizer_sha256"]):
        raise LAQ.LayerAStop("NORMALIZER-SOURCE-DIGEST-MISMATCH")
    identities = {field: file_sha(path) for field, path in IDENTITY_FILES.items()}
    for field, expected in REVIEWED_SHA.items():
        if identities[field] != expected:
            raise LAQ.LayerAStop(f"REVIEWED-SOURCE-DRIFT:{field}")
    prod_sha = {name: file_sha(path) for name, path in sorted(PRODUCTION.items())}
    if prod_sha != PRODUCTION_SHA:
        raise LAQ.LayerAStop("REVIEWED-PRODUCTION-SOURCE-DRIFT")
    manifest = read_json(IDENTITY_FILES["w2i_binding_manifest_sha256"])
    if (manifest.get("selector_path") != IDENTITY_FILES["w2e_selector_sha256"] or
            manifest.get("selector_sha256") != identities["w2e_selector_sha256"] or
            manifest.get("offline_runner_path") != f"{SCRIPT}/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py" or
            file_sha(manifest["offline_runner_path"]) != manifest.get("offline_runner_sha256") or
            manifest.get("w2e_contract_artifact_path") != f"{DAY20}/b2_t4_w2e_artifacts/w2e_contract_v2.json" or
            file_sha(manifest["w2e_contract_artifact_path"]) != manifest.get("w2e_contract_artifact_sha256")):
        raise LAQ.LayerAStop("W2I-MANIFEST-REFERENCED-SOURCE-DRIFT")
    if read_json(IDENTITY_FILES["ppq_v2_schema_sha256"]) != PPQ.schema_document():
        raise LAQ.LayerAStop("PPQ-V2-SCHEMA-CONTENT-DRIFT")
    fs = read_json(IDENTITY_FILES["filesystem_precondition_digest"])
    root = fixed_file(IDENTITY_FILES["filesystem_precondition_digest"]).parent
    final = Path(fs.get("final_example", ""))
    temp = Path(fs.get("temp_example", ""))
    if not (fs.get("schema_version") == "b2_t4_re6_r3_filesystem_precondition_v1" and
            fs.get("filesystem_name") == "NTFS" and fs.get("NTFS_pass") is True and
            fs.get("temp_final_same_volume") is True and
            fs.get("helper_same_directory_temp_contract") is True and
            fs.get("qualification_pass") is True and
            fs.get("artifact_root") == str(root) and
            fs.get("resolved_volume_root") and
            final.parent == temp.parent and temp.name.startswith(final.name + ".tmp") and
            final.is_relative_to(root) and temp.is_relative_to(root)):
        raise LAQ.LayerAStop("FILESYSTEM-PRECONDITION-CONTENT-INVALID")
    static = read_json(IDENTITY_FILES["source_authority_digest"])
    if not (static.get("pass") is True and
            static.get("hashes", {}).get("full_transaction") == prod_sha["full_transaction"] and
            static.get("hashes", {}).get("real_adapter") == prod_sha["real_isaac_adapter"] and
            static.get("hashes", {}).get("environment") == prod_sha["environment"] and
            static.get("hashes", {}).get("pw_helper") == identities["pw_helper_sha256"]):
        raise LAQ.LayerAStop("STATIC-AUTHORITY-CONTENT-INVALID")
    pc = read_json(CONFIG_FILE)
    config = pc.get("config")
    if type(config) is not dict:
        raise LAQ.LayerAStop("PROCESS-CONFIG-NOT-OBJECT")
    config_sha = PPQ.digest(config)
    raw = sources["raw_final"]
    if not (pc.get("pass") is True and pc.get("phase") == "B2-T4-RE6-R3" and
            pc.get("config_sha256") == config_sha and config.get("T") == CONFIG["expected_T"] and
            config.get("run_id") == sources["worker_handoff"].get("run_id") and
            config.get("worker_pid") == raw.get("process_id") and
            raw["exact_execution_counts"]["successful_full_transactions"] == CONFIG["expected_transaction_count"]):
        raise LAQ.LayerAStop("PROCESS-CONFIG-CANONICAL-IDENTITY-INVALID")
    candidate_sha = identities["ppq_v2_candidate_sha256"]
    readback = sources["ppq_v2_readback"]
    if not (readback.get("pass") is True and readback.get("receipt_sha256") == candidate_sha):
        raise LAQ.LayerAStop("PPQ-CANDIDATE-READBACK-INVALID")
    identities.update({"config_authority_digest": config_sha,
                       "production_identity_digest": PPQ.digest(prod_sha),
                       "config_identity_digest": PPQ.digest(CONFIG)})
    return {"identity_values": identities, "file_sha256": {
        path: file_sha(path) for path in sorted(set(SOURCE_FILES.values()) |
                                                   set(IDENTITY_FILES.values()) |
                                                   set(PRODUCTION.values()) | {CONFIG_FILE})},
            "production_component_sha256": prod_sha,
            "process_config_canonical_sha256": config_sha}


def project_layer_a_r1(sources: Mapping[str, Any], ppq_schema: Mapping[str, Any],
                       registry: Mapping[str, Any]) -> dict[str, Any]:
    """Construct a candidate only after source/file agreement; no default repair."""
    authority = recompute_authority(sources, registry)
    payload = LAQ.project_layer_a_worker_receipt(sources, ppq_schema)
    if any(_get(payload, field) != value for field, value in authority["identity_values"].items()):
        raise LAQ.LayerAStop("PROJECTION-SOURCE-IDENTITY-MISMATCH")
    return LAQ.envelope_for(payload)


def _get(payload: Mapping[str, Any], dotted: str) -> Any:
    value: Any = payload
    for component in dotted.split("."):
        value = value.get(component) if type(value) is dict else None
    return value


def validate_receipt_authority_bindings(receipt: Any, raw_sources: Mapping[str, Any],
                                        registry: Mapping[str, Any],
                                        ppq_schema: Mapping[str, Any]) -> dict[str, Any]:
    """Distinct read-only validator; recomputes all 120 fields and every digest."""
    try:
        if type(receipt) is not dict or type(receipt.get("payload")) is not dict:
            raise LAQ.LayerAStop("RECEIPT-PAYLOAD-MISSING")
        authority = recompute_authority(raw_sources, registry)
        expected = LAQ.project_layer_a_worker_receipt(raw_sources, ppq_schema)
        for field, value in authority["identity_values"].items():
            if "." in field:
                expected["contracts"][field.split(".", 1)[1]] = value
            else:
                expected[field] = value
        payload = receipt["payload"]
        checks = {field: (field in payload and type(payload[field]) is type(value) and
                          payload[field] == value) for field, value in expected.items()}
        for field, value in authority["identity_values"].items():
            checks[f"source:{field}"] = LAQ.digest64(_get(payload, field)) and _get(payload, field) == value
        return {"pass": all(checks.values()) and set(payload) == set(expected),
                "checks": checks, "failed": [field for field, passed in checks.items() if not passed],
                "mandatory_fields_checked": len(expected),
                "source_digests_checked": len(authority["identity_values"]),
                "authoritative_file_count": len(authority["file_sha256"])}
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        return {"pass": False, "checks": {}, "failed": [f"AUTHORITY-SOURCE:{exc}"],
                "mandatory_fields_checked": 0, "source_digests_checked": 0,
                "authoritative_file_count": 0}


def crosscheck_raw_source_v2(receipt: Any, raw_sources: Mapping[str, Any],
                             registry: Mapping[str, Any], ppq_schema: Mapping[str, Any]) -> dict[str, Any]:
    payload = receipt.get("payload") if type(receipt) is dict else None
    try:
        runtime = LAQ.crosscheck_raw_vs_receipt(payload, raw_sources)
    except (KeyError, TypeError, ValueError) as exc:
        runtime = {"pass": False, "checks": {}, "failed": [f"RAW-RUNTIME:{exc}"]}
    authority = validate_receipt_authority_bindings(receipt, raw_sources, registry, ppq_schema)
    return {"pass": runtime["pass"] and authority["pass"], "runtime": runtime,
            "authority": authority, "runtime_fields_checked": len(runtime["checks"]),
            "identity_fields_checked": authority["source_digests_checked"],
            "artifact_digest_fields_checked": 4,
            "composite_digest_fields_checked": 2,
            "unbound_mandatory_fields": max(0, len(PPQ.FIELDS) + len(LAQ.EXTRA_TYPES) -
                                           authority["mandatory_fields_checked"])}


def adjudicate_supervisor_r1(receipt: Any, layer_b_pass: bool,
                             *, raw_sources: Mapping[str, Any], registry: Mapping[str, Any],
                             **structural_kwargs: Any) -> dict[str, Any]:
    """Compare-only supervisor. Never edits, fills, or reconstructs the receipt."""
    before = deepcopy(receipt)
    structural = LAQ.validate_layer_a_worker_receipt(receipt, **structural_kwargs)
    crosscheck = crosscheck_raw_source_v2(receipt, raw_sources, registry,
                                          structural_kwargs["ppq_schema"])
    authority = crosscheck["authority"]
    layer_a_pass = structural["pass"] and crosscheck["runtime"]["pass"] and authority["pass"]
    if receipt != before:
        raise LAQ.LayerAStop("SUPERVISOR-MUTATED-RECEIPT")
    return {"structural": structural, "runtime_crosscheck": crosscheck["runtime"],
            "authority_binding": authority, "raw_source_crosscheck_v2": crosscheck,
            "layer_a_pass": layer_a_pass, "layer_b_pass": layer_b_pass,
            "pass": layer_a_pass and layer_b_pass,
            "status": "PASS" if layer_a_pass and layer_b_pass else "STOP"}
