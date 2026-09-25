"""Pure RACQ run-portable registry and canonical Layer-A v3 composition.

The canonical v3 receipt nests one complete PPQ-V2-R1 payload.  It does not
flatten 90 PPQ fields beside the 34 frozen LAQ extension fields, so the rejected
124-field union is never a valid receipt shape.  Frozen LAQ semantics are
preserved as compare-only predicates over the nested PPQ payload and the 34
explicit extension fields.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_laq_r1_worker_receipt as LAQ_R1
import _assignment_phase_b2_t4_laq_worker_receipt as LAQ
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1
import _assignment_phase_b2_t4_racq_runtime_authority as RACQ


VERSION = "b2_t4_layer_a_worker_receipt_v3"
ENVELOPE_VERSION = "b2_t4_layer_a_worker_receipt_envelope_v3"
REGISTRY_TEMPLATE_VERSION = "b2_t4_layer_a_authority_registry_template_v1"
REGISTRY_INSTANCE_VERSION = "b2_t4_layer_a_authority_registry_instance_v1"

RUNTIME_FIELDS: dict[str, type] = {
    "runtime_authority_version": str,
    "runtime_authorization_scope": str,
    "runtime_authority_digest": str,
    "runtime_run_binding_version": str,
    "runtime_run_binding_digest": str,
    "registry_template_digest": str,
    "registry_instance_digest": str,
    "composition_contract_digest": str,
}

V3_FIELDS: dict[str, type] = {
    **LAQ.EXTRA_TYPES,
    "ppq_v2_r1_payload": dict,
    **RUNTIME_FIELDS,
}

RUN_CONTEXT_FIELDS: dict[str, type] = {
    "source_phase": str,
    "run_id": str,
    "worker_pid": int,
    "artifact_namespace": str,
    "config_digest": str,
    "runtime_authority_path": str,
    "run_binding_path": str,
    "ppq_receipt_digest": str,
}

PATH_ROLE_RULES = {
    "PRODUCTION_SOURCE": "fixed reviewed repository source set",
    "REVIEWED_HELPER": "fixed reviewed repository helper/schema set",
    "PRE_RUNTIME_AUTHORITY": "runtime_authority/<phase-slug>.json",
    "RUN_BINDING": "run_binding/<phase-slug>/<run-id>.json",
    "CONFIG_AUTHORITY": "<artifact-namespace>/process_config_authority.json",
    "FILESYSTEM_AUTHORITY": "<artifact-namespace>/filesystem_precondition.json",
    "RUNTIME_LEDGER": "<artifact-namespace>/runtime evidence ledgers",
    "RUNTIME_WITNESS": "<artifact-namespace>/canonical witness artifacts",
    "PPQ_RECEIPT": "<artifact-namespace>/candidate_success_receipt_v2_1.json",
    "CLOSE_HANDOFF": "<artifact-namespace>/formal_worker_receipt.json",
    "REGISTRY_INSTANCE": "<artifact-namespace>/layer_a_registry_instance.json",
    "COMPOSITION_CONTRACT": "fixed RACQ composition helper/schema",
    "RUN_CONTEXT": "trusted exact phase/run/PID/config/namespace context",
}

HEX = frozenset("0123456789abcdef")


class RACQCompositionStop(ValueError):
    """Fail-closed registry, composition, or Layer-A v3 violation."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RACQCompositionStop(reason)


def canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RACQCompositionStop("CANONICAL-JSON") from exc


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def sha256_value(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= HEX


def _strict(value: object, fields: Mapping[str, type], label: str) -> dict[str, Any]:
    require(type(value) is dict, f"{label}-NOT-OBJECT")
    result = value
    require(set(result) == set(fields), f"{label}-FIELDS-MISSING-OR-UNKNOWN")
    for key, expected_type in fields.items():
        require(type(result[key]) is expected_type, f"{label}-TYPE:{key}")
        require(result[key] is not None, f"{label}-NULL:{key}")
    return result


def _old_role(field: str, category: str) -> list[str]:
    if field == "config_authority_digest":
        return ["CONFIG_AUTHORITY"]
    if field == "filesystem_precondition_digest":
        return ["FILESYSTEM_AUTHORITY"]
    if field in {"source_authority_digest"}:
        return ["PRE_RUNTIME_AUTHORITY", "PRODUCTION_SOURCE", "REVIEWED_HELPER"]
    if field in {"ppq_v2_candidate_sha256", "ppq_v2_readback_pass"}:
        return ["PPQ_RECEIPT"]
    if field in {
        "final_in_worker_quiescence_pass", "env_close_pass", "app_close_invoked",
        "receipt_written_before_app_close", "receipt_fsync_pass", "receipt_readback_pass",
    }:
        return ["CLOSE_HANDOFF"]
    if field == "witnesses":
        return ["RUNTIME_WITNESS"]
    if field in {"layer_a_contract_version", "contracts"} or category in {
        "REVIEWED_SOURCE_IDENTITY", "CONTRACT_VERSION_IDENTITY",
    }:
        return ["REVIEWED_HELPER"]
    if category == "CALLER_BOUND_IDENTITY":
        return ["RUN_CONTEXT"]
    if category == "MULTI_SOURCE_COMPOSITE_DIGEST":
        return ["PRODUCTION_SOURCE", "CONFIG_AUTHORITY"]
    return ["RUNTIME_LEDGER"]


def registry_template_document() -> dict[str, Any]:
    frozen = LAQ_R1.registry_document()["fields"]
    fields: dict[str, dict[str, Any]] = {}
    for name in LAQ.EXTRA_TYPES:
        old = frozen[name]
        fields[name] = {
            "field_name": name,
            "semantic_role": old["semantic_purpose"],
            "authority_category": old["category"],
            "computation_rule": old["computation"],
            "path_roles": _old_role(name, old["category"]),
            "production_stage": "RUNTIME_PRODUCED" if "RUNTIME" in old["category"] else "PRE_RUNTIME_OR_REVIEWED",
            "content_binding": "exact value and canonical source/identity digest",
        }
    fields["ppq_v2_r1_payload"] = {
        "field_name": "ppq_v2_r1_payload",
        "semantic_role": "one complete reviewed PPQ-V2-R1 payload",
        "authority_category": "NESTED_REVIEWED_RECEIPT",
        "computation_rule": "exact PPQ-V2-R1 validation plus canonical payload digest",
        "path_roles": ["PPQ_RECEIPT"],
        "production_stage": "RUNTIME_PRODUCED",
        "content_binding": "exact 90-field payload; no flattening",
    }
    for name in RUNTIME_FIELDS:
        role = (
            "PRE_RUNTIME_AUTHORITY" if name.startswith("runtime_author")
            else "RUN_BINDING" if name.startswith("runtime_run_binding")
            else "REGISTRY_INSTANCE" if name.startswith("registry_")
            else "COMPOSITION_CONTRACT"
        )
        fields[name] = {
            "field_name": name,
            "semantic_role": f"qualify exact RACQ {name}",
            "authority_category": "RACQ_RUNTIME_AUTHORITY",
            "computation_rule": "exact version or SHA-256 canonical contract digest",
            "path_roles": [role],
            "production_stage": "PRE_RUNTIME_OR_COMPOSITION",
            "content_binding": "exact independently recomputed value",
        }
    document = {
        "template_version": REGISTRY_TEMPLATE_VERSION,
        "layer_a_contract": VERSION,
        "field_count": len(fields),
        "fields": fields,
        "path_role_rules": PATH_ROLE_RULES,
        "historical_attempt_paths": "FORBIDDEN",
        "manual_path_rebinding": "REJECT",
        "instance_generation": "deterministic from exact run context",
    }
    require(len(fields) == len(V3_FIELDS), "REGISTRY-TEMPLATE-FIELD-COUNT")
    encoded = canonical(document).decode("utf-8")
    require("20260920" not in encoded and "b2_t4_re6_r3" not in encoded, "REGISTRY-TEMPLATE-HISTORICAL-PATH")
    return document


def registry_template_digest() -> str:
    return digest(registry_template_document())


def make_run_context(
    *, source_phase: str, run_id: str, worker_pid: int, artifact_namespace: str,
    config_digest: str, ppq_receipt_digest: str,
) -> dict[str, Any]:
    require(RACQ.phase_number(source_phase) is not None, "REGISTRY-CONTEXT-PHASE")
    require(RACQ.valid_run_id(run_id), "REGISTRY-CONTEXT-RUN-ID")
    require(type(worker_pid) is int and worker_pid > 0, "REGISTRY-CONTEXT-PID")
    require(
        artifact_namespace == RACQ.expected_artifact_namespace(source_phase, run_id),
        "REGISTRY-CONTEXT-NAMESPACE",
    )
    require(sha256_value(config_digest) and sha256_value(ppq_receipt_digest), "REGISTRY-CONTEXT-DIGEST")
    return {
        "source_phase": source_phase,
        "run_id": run_id,
        "worker_pid": worker_pid,
        "artifact_namespace": artifact_namespace,
        "config_digest": config_digest,
        "runtime_authority_path": RACQ.authority_relative_path(source_phase).as_posix(),
        "run_binding_path": RACQ.binding_relative_path(source_phase, run_id).as_posix(),
        "ppq_receipt_digest": ppq_receipt_digest,
    }


def _resolved_sources(role: str, context: Mapping[str, Any]) -> list[str]:
    namespace = context["artifact_namespace"]
    fixed = {
        "PRODUCTION_SOURCE": [
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_full_transaction.py",
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_real_isaac_adapter.py",
            "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py",
        ],
        "REVIEWED_HELPER": [
            "scripts/environments/_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
            "scripts/environments/_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
        ],
        "PRE_RUNTIME_AUTHORITY": [context["runtime_authority_path"]],
        "RUN_BINDING": [context["run_binding_path"]],
        "CONFIG_AUTHORITY": [f"{namespace}/process_config_authority.json"],
        "FILESYSTEM_AUTHORITY": [f"{namespace}/filesystem_precondition.json"],
        "RUNTIME_LEDGER": [
            f"{namespace}/transaction_ledger.jsonl",
            f"{namespace}/bridge_ledger.jsonl",
            f"{namespace}/lifecycle_task_progress.jsonl",
        ],
        "RUNTIME_WITNESS": [f"{namespace}/canonical_witnesses"],
        "PPQ_RECEIPT": [f"{namespace}/candidate_success_receipt_v2_1.json"],
        "CLOSE_HANDOFF": [f"{namespace}/formal_worker_receipt.json"],
        "REGISTRY_INSTANCE": [f"{namespace}/layer_a_registry_instance.json"],
        "COMPOSITION_CONTRACT": [
            "scripts/environments/_assignment_phase_b2_t4_racq_layer_a_composition.py"
        ],
        "RUN_CONTEXT": ["@trusted-run-context"],
    }
    require(role in fixed, f"UNKNOWN-PATH-ROLE:{role}")
    return fixed[role]


def instantiate_registry(template: Mapping[str, Any], run_context: Mapping[str, Any]) -> dict[str, Any]:
    require(type(template) is dict and template == registry_template_document(), "REGISTRY-TEMPLATE-IDENTITY")
    context = _strict(deepcopy(run_context), RUN_CONTEXT_FIELDS, "REGISTRY-RUN-CONTEXT")
    require(
        context == make_run_context(
            source_phase=context["source_phase"], run_id=context["run_id"],
            worker_pid=context["worker_pid"], artifact_namespace=context["artifact_namespace"],
            config_digest=context["config_digest"], ppq_receipt_digest=context["ppq_receipt_digest"],
        ),
        "REGISTRY-RUN-CONTEXT-DERIVATION",
    )
    fields: dict[str, Any] = {}
    for name, definition in template["fields"].items():
        paths: list[str] = []
        for role in definition["path_roles"]:
            paths.extend(_resolved_sources(role, context))
        fields[name] = {
            "field_name": name,
            "template_semantic_digest": digest(definition),
            "resolved_sources": paths,
            "content_binding": definition["content_binding"],
        }
    payload: dict[str, Any] = {
        "instance_version": REGISTRY_INSTANCE_VERSION,
        "template_digest": digest(template),
        "run_context": context,
        "fields": fields,
    }
    payload["instance_digest"] = digest(payload)
    return payload


def validate_registry_instance(
    instance: object, *, template: Mapping[str, Any], run_context: Mapping[str, Any],
) -> dict[str, Any]:
    require(type(instance) is dict, "REGISTRY-INSTANCE-NOT-OBJECT")
    expected = instantiate_registry(template, run_context)
    require(instance == expected, "REGISTRY-INSTANCE-PATH-OR-DEFINITION-DRIFT")
    require(
        instance.get("instance_digest")
        == digest({key: value for key, value in instance.items() if key != "instance_digest"}),
        "REGISTRY-INSTANCE-DIGEST",
    )
    return instance


def composition_contract_document() -> dict[str, Any]:
    return {
        "contract_version": VERSION,
        "envelope_version": ENVELOPE_VERSION,
        "canonical_top_level_field_count": len(V3_FIELDS),
        "nested_ppq_v2_r1_field_count": len(PPQ_R1.FIELDS),
        "retained_laq_extension_field_count": len(LAQ.EXTRA_TYPES),
        "new_runtime_composition_field_count": len(RUNTIME_FIELDS),
        "formula": "34 retained LAQ extensions + 1 nested exact PPQ-V2-R1 payload + 8 RACQ fields",
        "naive_flat_124_field_union": "REJECT",
        "unknown_fields": "REJECT",
        "supervisor_repairs_fields": False,
    }


def composition_contract_digest() -> str:
    return digest(composition_contract_document())


def schema_document() -> dict[str, Any]:
    return {
        "schema_version": VERSION,
        "envelope_version": ENVELOPE_VERSION,
        "required_fields": {name: value.__name__ for name, value in V3_FIELDS.items()},
        "nested_ppq_v2_r1_required_fields": {
            name: value.__name__ for name, value in PPQ_R1.FIELDS.items()
        },
        "unknown_fields": "REJECT",
        "missing_or_null": "REJECT",
        "payload_digest": "SHA-256 sorted compact UTF-8 JSON",
    }


def composition_field_map() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    old_ppq_fields = set(LAQ_R1.PPQ.FIELDS)
    new_ppq_fields = set(PPQ_R1.FIELDS)
    for name in sorted(old_ppq_fields):
        rows.append({
            "field_name": name,
            "origin": "PPQ-V2 / frozen LAQ-R1 flattened payload",
            "semantic_purpose": f"preserve exact PPQ semantic fact {name}",
            "authority": "nested reviewed PPQ-V2-R1 payload",
            "old_status": "top-level field",
            "new_status": f"ppq_v2_r1_payload.{name}",
            "action": "MERGED_WITH_PPQ_V2_R1_FIELD",
        })
    for name in sorted(LAQ.EXTRA_TYPES):
        rows.append({
            "field_name": name,
            "origin": "LAQ-R1 extension",
            "semantic_purpose": registry_template_document()["fields"][name]["semantic_role"],
            "authority": "RACQ registry instance",
            "old_status": "top-level field",
            "new_status": "top-level field",
            "action": "RETAINED_UNCHANGED",
        })
    for name in sorted(new_ppq_fields - old_ppq_fields):
        rows.append({
            "field_name": name,
            "origin": "PPQ-V2-R1 four-field authority delta",
            "semantic_purpose": f"preserve exact PPQ-V2-R1 {name}",
            "authority": "nested reviewed PPQ-V2-R1 payload",
            "old_status": "absent",
            "new_status": f"ppq_v2_r1_payload.{name}",
            "action": "NEW_REQUIRED_FIELD",
        })
    rows.append({
        "field_name": "ppq_v2_r1_payload",
        "origin": "RACQ structural composition",
        "semantic_purpose": "single non-duplicating container for all 90 PPQ-V2-R1 fields",
        "authority": "reviewed PPQ-V2-R1 validator",
        "old_status": "absent as container",
        "new_status": "required exact nested object",
        "action": "NEW_REQUIRED_FIELD",
    })
    for name in sorted(RUNTIME_FIELDS):
        rows.append({
            "field_name": name,
            "origin": "RACQ runtime authority/composition",
            "semantic_purpose": registry_template_document()["fields"][name]["semantic_role"],
            "authority": "RACQ runtime authority, binding, registry, or composition contract",
            "old_status": "absent",
            "new_status": "required top-level field",
            "action": "NEW_REQUIRED_FIELD",
        })
    return rows


def envelope_for(payload: Mapping[str, Any]) -> dict[str, Any]:
    require(type(payload) is dict, "ENVELOPE-PAYLOAD-NOT-OBJECT")
    return {
        "schema_version": ENVELOPE_VERSION,
        "payload": deepcopy(payload),
        "payload_sha256": digest(payload),
    }


def adapt_ppq_v2_r1_composition_input(
    *, ppq_receipt: Mapping[str, Any], laq_v2_payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project the two reviewed inputs into one non-duplicating v3 input.

    PPQ-V2-R1 is the primary authority for semantic facts already present in
    PPQ.  The returned nested PPQ object is byte-for-byte value-equivalent to
    the caller's 90-field input.  LAQ-only process, close, witness-source, and
    runtime fields remain sourced from the LAQ input; overlapping LAQ views are
    deterministic projections of PPQ rather than second authorities.
    """
    ppq = _strict(deepcopy(ppq_receipt), PPQ_R1.FIELDS, "PPQ-V2-R1-PAYLOAD")
    require(type(laq_v2_payload) is dict, "LAQ-V2-SOURCE-NOT-OBJECT")
    extras: dict[str, Any] = {}
    for name, expected_type in LAQ.EXTRA_TYPES.items():
        require(
            name in laq_v2_payload and type(laq_v2_payload[name]) is expected_type,
            f"LAQ-V2-EXTRA:{name}",
        )
        extras[name] = deepcopy(laq_v2_payload[name])

    extras.update({
        "S10_count": ppq["transaction_count"],
        "ledger_count": ppq["transaction_count"],
        "event_returns_count": ppq["event_returns"],
        "stock_compute_returns_count": ppq["stock_compute_returns"],
        "TASK_COMPLETED_count": ppq["task_completed_count"],
        "max_coverage": ppq["coverage_max"],
        "invalid_critic_class_count": (
            ppq["critic_step"] - ppq["valid_nonzero_update"]
            - ppq["valid_zero_effective_update"]
        ),
        "learner": {name: deepcopy(ppq[name]) for name in LAQ.LEARNER_KEYS},
        "witnesses": {
            name: {"pass": ppq[f"{name}_status"] == "PASS"}
            for name in LAQ.WITNESS_KEYS
        },
        "pw_progress": {
            "critic_records": ppq["pw_critic_actual"],
            "actor_factor_records": ppq["pw_actor_factor_actual"],
            "missing": 0,
            "duplicate": 0,
            "out_of_order": 0,
            "digest_mismatch": 0,
            "temp_residue": 0,
            "old_mutable_progress_paths": 0,
        },
    })
    extras["witnesses"]["W7"]["count"] = ppq["W7_qualified_count"]
    return ppq, extras


def compose_payload(
    *, ppq_receipt: Mapping[str, Any], laq_v2_payload: Mapping[str, Any],
    runtime_authority: Mapping[str, Any], run_binding: Mapping[str, Any],
    registry_instance: Mapping[str, Any],
) -> dict[str, Any]:
    ppq, extras = adapt_ppq_v2_r1_composition_input(
        ppq_receipt=ppq_receipt, laq_v2_payload=laq_v2_payload,
    )
    extras["layer_a_contract_version"] = VERSION
    extras["ppq_v2_candidate_sha256"] = digest(ppq)
    extras["ppq_v2_readback_pass"] = True
    extras["source_authority_digest"] = digest({
        "runtime_authority_digest": runtime_authority["authority_payload_digest"],
        "registry_template_digest": registry_instance["template_digest"],
        "production_identity_digest": ppq["production_identity_digest"],
    })
    extras["config_authority_digest"] = ppq["config_identity_digest"]
    extras["filesystem_precondition_digest"] = digest({
        "artifact_namespace": run_binding["artifact_namespace"],
        "filesystem_authority_path": f"{run_binding['artifact_namespace']}/filesystem_precondition.json",
        "path_policy": "exact deterministic run namespace; no alias or traversal",
    })
    contracts = deepcopy(extras["contracts"])
    require(type(contracts) is dict, "CONTRACT-MAP")
    contracts.update({
        "layer_a_contract_version": VERSION,
        "contract_version": PPQ_R1.VERSION,
        "ppq_v2_helper_sha256": ppq["ppq_v2_helper_sha256"],
        "ppq_v2_schema_sha256": ppq["ppq_v2_schema_sha256"],
        "runtime_authority_version": RACQ.AUTHORITY_VERSION,
        "runtime_run_binding_version": RACQ.BINDING_VERSION,
        "registry_template_digest": registry_instance["template_digest"],
        "composition_contract_digest": composition_contract_digest(),
    })
    extras["contracts"] = contracts
    payload = {
        **extras,
        "ppq_v2_r1_payload": ppq,
        "runtime_authority_version": runtime_authority["authority_version"],
        "runtime_authorization_scope": runtime_authority["authorization_scope"],
        "runtime_authority_digest": runtime_authority["authority_payload_digest"],
        "runtime_run_binding_version": run_binding["binding_version"],
        "runtime_run_binding_digest": run_binding["binding_payload_digest"],
        "registry_template_digest": registry_instance["template_digest"],
        "registry_instance_digest": registry_instance["instance_digest"],
        "composition_contract_digest": composition_contract_digest(),
    }
    return _strict(payload, V3_FIELDS, "LAYER-A-V3-PAYLOAD")


def _inherited_checks(payload: Mapping[str, Any], *, expected_source_phase: str,
                      expected_run_id: str, expected_pid: int) -> dict[str, bool]:
    ppq = payload["ppq_v2_r1_payload"]
    learner = payload["learner"]
    contracts = payload["contracts"]
    witnesses = payload["witnesses"]
    pw = payload["pw_progress"]
    checks = {
        "receipt_present": True,
        "receipt_parse_valid": True,
        "envelope_schema": True,
        "payload_schema": payload["layer_a_contract_version"] == VERSION,
        "payload_digest": True,
        "phase": ppq["source_phase"] == expected_source_phase,
        "run_id": bool(ppq["run_id"]) and ppq["run_id"] == expected_run_id,
        "worker_pid": ppq["worker_pid"] == expected_pid > 0,
        "source_authority": sha256_value(payload["source_authority_digest"]),
        "config_authority": sha256_value(payload["config_authority_digest"]),
        "pw_helper_identity": sha256_value(ppq["pw_helper_sha256"]),
        "filesystem_authority": sha256_value(payload["filesystem_precondition_digest"]),
        "status_success": payload["status"] == "success",
        "cuda_probe": payload["cuda_probe_count"] == 1 and payload["cuda_probe_pass"] is True,
        "app_launcher": payload["app_launcher_count"] == 1 and payload["app_launcher_started"] is True,
        "entry_point": payload["entry_point_resolution_pass"] is True,
        "environment": payload["environment_count"] == 1,
        "reset": payload["initial_reset_count"] == 1,
        "learner_once": payload["persistent_learner_count"] == 1,
        "targets": ppq["expected_T"] == 2 and ppq["expected_transaction_count"] == 160,
        "completion": payload["S10_count"] == payload["ledger_count"] == ppq["transaction_count"],
        "pw_progress": (
            type(pw) is dict and pw.get("critic_records") == ppq["pw_critic_actual"]
            and pw.get("actor_factor_records") == ppq["pw_actor_factor_actual"]
            and all(pw.get(key) == 0 for key in ("missing", "duplicate", "out_of_order", "digest_mismatch", "temp_residue", "old_mutable_progress_paths"))
        ),
        "w1_w6": type(witnesses) is dict and all(witnesses.get(key, {}).get("pass") is True for key in ("W1", "W2E", "W3", "W4", "W5", "W6")),
        "w7": type(witnesses) is dict and witnesses.get("W7", {}).get("pass") is True and ppq["W7_qualified_count"] == ppq["transaction_count"],
        "task_progress": payload["TASK_COMPLETED_count"] == ppq["task_completed_count"] >= 1 and payload["max_coverage"] == ppq["coverage_max"] > 0,
        "persistent_learner": payload["persistent_continuity_pass"] is True,
        "actor_plans": type(learner) is dict and learner.get("actor_backward") == ppq["actor_backward"] and learner.get("actor_step") == ppq["actor_step"],
        "factor": payload["factor_audits_pass"] is True,
        "critic": type(learner) is dict and learner.get("critic_backward") == ppq["critic_backward"] and learner.get("critic_step") == ppq["critic_step"],
        "valuenorm": type(learner) is dict and learner.get("valuenorm_update") == ppq["valuenorm_update"] and learner.get("valuenorm_continuity") == ppq["valuenorm_continuity"],
        "adam": type(learner) is dict and learner.get("actor_adam_continuity") == ppq["actor_adam_continuity"] and learner.get("critic_adam_continuity") == ppq["critic_adam_continuity"],
        "numerical": type(learner) is dict and learner.get("numerical_health") == ppq["numerical_health"] is True,
        "contracts": type(contracts) is dict and contracts.get("layer_a_contract_version") == VERSION and contracts.get("contract_version") == PPQ_R1.VERSION,
        "returns": payload["event_returns_count"] == ppq["event_returns"] == ppq["transaction_count"] and payload["stock_compute_returns_count"] == ppq["stock_compute_returns"] == 0,
        "route": ppq["campaign_status"] == "SUCCESS" and ppq["partial_update"] is False and ppq["route_poisoned"] is False and payload["final_in_worker_quiescence_pass"] is True,
        "forbidden": ppq["checkpoint_io_count"] == ppq["public_activation_count"] == ppq["evaluation_playback_count"] == 0,
        "receipt_order": payload["receipt_written_before_app_close"] is True and payload["receipt_fsync_pass"] is True and payload["receipt_readback_pass"] is True,
        "env_close": payload["env_close_pass"] is True,
        "app_close_invoked": payload["app_close_invoked"] is True,
    }
    require(len(checks) == 39, "INHERITED-PREDICATE-COUNT")
    return checks


def validate_layer_a_v3(
    receipt: object, *, ppq_validator: Callable[[Mapping[str, Any]], None],
    source_ppq_receipt: Mapping[str, Any], source_laq_v2_payload: Mapping[str, Any],
    authority_path: Path, binding_path: Path, authority_root: Path,
    expected_external_authorization_digest: str,
    expected_config_policy_identity: str, registry_template: Mapping[str, Any],
    registry_instance: Mapping[str, Any], run_context: Mapping[str, Any],
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    require(type(receipt) is dict, "LAYER-A-V3-ENVELOPE-NOT-OBJECT")
    before = deepcopy(receipt)
    require(set(receipt) == {"schema_version", "payload", "payload_sha256"}, "LAYER-A-V3-ENVELOPE-FIELDS")
    require(receipt["schema_version"] == ENVELOPE_VERSION, "LAYER-A-V3-ENVELOPE-VERSION")
    payload = _strict(receipt["payload"], V3_FIELDS, "LAYER-A-V3-PAYLOAD")
    require(receipt["payload_sha256"] == digest(payload), "LAYER-A-V3-PAYLOAD-DIGEST")
    ppq = _strict(payload["ppq_v2_r1_payload"], PPQ_R1.FIELDS, "PPQ-V2-R1-PAYLOAD")
    try:
        ppq_validator(ppq)
    except Exception as exc:
        raise RACQCompositionStop(f"PPQ-V2-R1:{exc}") from exc
    authority = RACQ.load_runtime_authority(
        actual_path=authority_path, authority_root=authority_root,
        expected_source_phase=run_context["source_phase"],
        expected_external_authorization_digest=expected_external_authorization_digest,
        expected_config_policy_identity=expected_config_policy_identity,
        qualification_mode=True,
    )
    binding = RACQ.load_run_binding(
        actual_path=binding_path, authority_root=authority_root, authority=authority,
        expected_run_id=run_context["run_id"], expected_worker_pid=run_context["worker_pid"],
        expected_config_digest=run_context["config_digest"],
        expected_artifact_namespace_value=run_context["artifact_namespace"],
        expected_registry_template_digest=registry_template_digest(),
    )
    validated_registry = validate_registry_instance(
        registry_instance, template=registry_template, run_context=run_context
    )
    require(ppq["source_phase"] == authority["authorized_source_phase"] == run_context["source_phase"], "V3-PHASE-CROSSCHECK")
    require(ppq["run_id"] == binding["run_id"] == run_context["run_id"], "V3-RUN-CROSSCHECK")
    require(ppq["worker_pid"] == binding["worker_pid"] == run_context["worker_pid"], "V3-PID-CROSSCHECK")
    require(ppq["config_identity_digest"] == binding["config_digest"] == run_context["config_digest"], "V3-CONFIG-CROSSCHECK")
    require(binding["artifact_namespace"] == run_context["artifact_namespace"], "V3-NAMESPACE-CROSSCHECK")
    expected = compose_payload(
        ppq_receipt=source_ppq_receipt, laq_v2_payload=source_laq_v2_payload,
        runtime_authority=authority, run_binding=binding, registry_instance=validated_registry,
    )
    require(payload == expected, "V3-SOURCE-BINDING")
    inherited = _inherited_checks(
        payload, expected_source_phase=run_context["source_phase"],
        expected_run_id=run_context["run_id"], expected_pid=run_context["worker_pid"],
    )
    failed_inherited = [name for name, passed in inherited.items() if not passed]
    require(
        not failed_inherited,
        "V3-INHERITED-PREDICATE:" + ",".join(failed_inherited),
    )
    new_authority = {
        "runtime_scope": payload["runtime_authorization_scope"] == RACQ.AUTHORIZATION_SCOPE,
        "runtime_authority_digest": payload["runtime_authority_digest"] == authority["authority_payload_digest"],
        "deterministic_authority_path": authority_path == authority_root / RACQ.authority_relative_path(run_context["source_phase"]),
        "run_binding": payload["runtime_run_binding_digest"] == binding["binding_payload_digest"],
        "deterministic_binding_path": binding_path == authority_root / RACQ.binding_relative_path(run_context["source_phase"], run_context["run_id"]),
        "phase_run_config_namespace": all((
            ppq["source_phase"] == run_context["source_phase"],
            ppq["run_id"] == run_context["run_id"],
            ppq["config_identity_digest"] == run_context["config_digest"],
            binding["artifact_namespace"] == run_context["artifact_namespace"],
        )),
        "registry_template_identity": payload["registry_template_digest"] == registry_template_digest(),
        "registry_instance_identity": payload["registry_instance_digest"] == registry_instance["instance_digest"],
        "composition_identity": payload["composition_contract_digest"] == composition_contract_digest(),
    }
    require(all(new_authority.values()), "V3-NEW-AUTHORITY-PREDICATE")
    require(receipt == before, "SUPERVISOR-MUTATED-RECEIPT")
    checks.update({"schema": True, "ppq_v2_r1": True, "source_binding": True,
                   "inherited_predicates": True, "new_authority_predicates": True,
                   "supervisor_repair": False})
    return {
        "pass": True,
        "checks": checks,
        "inherited_predicates": inherited,
        "new_authority_predicates": new_authority,
        "canonical_field_count": len(payload),
        "ppq_nested_field_count": len(ppq),
        "supervisor_mutations": 0,
    }


def adjudicate_supervisor_v3(receipt: object, *, layer_b_pass: bool, **kwargs: Any) -> dict[str, Any]:
    before = deepcopy(receipt)
    try:
        layer_a = validate_layer_a_v3(receipt, **kwargs)
        status = "PASS" if layer_b_pass else "STOP"
        passed = bool(layer_b_pass)
    except (RACQCompositionStop, RACQ.RACQAuthorityStop, PPQ_R1.PPQV2R1Stop, KeyError, TypeError, ValueError, OSError) as exc:
        layer_a = {"pass": False, "reason": str(exc)}
        status = "STOP"
        passed = False
    require(receipt == before, "SUPERVISOR-MUTATED-RECEIPT")
    return {
        "layer_a": layer_a,
        "layer_b_pass": layer_b_pass,
        "pass": passed and layer_a.get("pass") is True,
        "status": status if passed and layer_a.get("pass") is True else "STOP",
        "supervisor_mutations": 0,
    }


def pre_mutation_failure_semantics() -> dict[str, Any]:
    return {"partial_update": False, "route_poisoned": False, "retry": False}


def post_mutation_failure_semantics() -> dict[str, Any]:
    return {"partial_update": True, "route_poisoned": True, "retry": False}
