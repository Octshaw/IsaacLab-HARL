"""Versioned RACQ-R1 Layer-A-v3 validator with explicit external context.

This wrapper composes the reviewed RACQ authority, binding, registry, PPQ, and
Layer-A-v3 primitives without editing or monkeypatching the frozen sources.
The canonical 43-field receipt remains unchanged.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1
import _assignment_phase_b2_t4_racq_layer_a_composition as COMPOSE
import _assignment_phase_b2_t4_racq_runtime_authority as RACQ
import _assignment_phase_b2_t4_racq_r1_mode_dispatch as DISPATCH


WRAPPER_VERSION = "b2_t4_layer_a_v3_validation_wrapper_racq_r1"


class RACQR1LayerAStop(ValueError):
    """Fail-closed RACQ-R1 Layer-A validation violation."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RACQR1LayerAStop(reason)


def validate_layer_a_v3_with_context(
    receipt: object, *, ppq_validator: Callable[[Mapping[str, Any]], None],
    source_ppq_receipt: Mapping[str, Any], source_laq_v2_payload: Mapping[str, Any],
    authority_path: Path, binding_path: Path, authority_root: Path,
    expected_external_authorization_digest: str,
    expected_config_policy_identity: str, registry_template: Mapping[str, Any],
    registry_instance: Mapping[str, Any], run_context: Mapping[str, Any],
    validation_context: object = None,
) -> dict[str, Any]:
    """Validate canonical Layer-A-v3 using exactly one context dispatch."""
    mode = DISPATCH.resolve_runtime_authority_validation_mode(validation_context)
    require(type(run_context) is dict, "RUN-CONTEXT-NOT-OBJECT")
    require(
        validation_context["expected_source_phase"] == run_context.get("source_phase"),
        "VALIDATION-CONTEXT-RUN-PHASE",
    )
    require(mode.run_binding_required, "VALIDATION-CONTEXT-RUN-BINDING-REQUIRED")

    checks: dict[str, bool] = {}
    require(type(receipt) is dict, "LAYER-A-V3-ENVELOPE-NOT-OBJECT")
    before = deepcopy(receipt)
    require(
        set(receipt) == {"schema_version", "payload", "payload_sha256"},
        "LAYER-A-V3-ENVELOPE-FIELDS",
    )
    require(
        receipt["schema_version"] == COMPOSE.ENVELOPE_VERSION,
        "LAYER-A-V3-ENVELOPE-VERSION",
    )
    payload = COMPOSE._strict(receipt["payload"], COMPOSE.V3_FIELDS, "LAYER-A-V3-PAYLOAD")
    require(receipt["payload_sha256"] == COMPOSE.digest(payload), "LAYER-A-V3-PAYLOAD-DIGEST")
    ppq = COMPOSE._strict(payload["ppq_v2_r1_payload"], PPQ_R1.FIELDS, "PPQ-V2-R1-PAYLOAD")
    try:
        ppq_validator(ppq)
    except Exception as exc:
        raise RACQR1LayerAStop(f"PPQ-V2-R1:{exc}") from exc

    authority = RACQ.load_runtime_authority(
        actual_path=authority_path,
        authority_root=authority_root,
        expected_source_phase=run_context["source_phase"],
        expected_external_authorization_digest=expected_external_authorization_digest,
        expected_config_policy_identity=expected_config_policy_identity,
        qualification_mode=mode.qualification_mode,
    )
    require(authority["authorization_scope"] == mode.authority_scope, "RACQ-R1-AUTHORITY-SCOPE")
    require(authority["instance_purpose"] == mode.instance_purpose, "RACQ-R1-AUTHORITY-PURPOSE")
    require(
        authority["live_runtime_grant"] is mode.live_runtime_grant,
        "RACQ-R1-LIVE-RUNTIME-GRANT",
    )

    binding = RACQ.load_run_binding(
        actual_path=binding_path,
        authority_root=authority_root,
        authority=authority,
        expected_run_id=run_context["run_id"],
        expected_worker_pid=run_context["worker_pid"],
        expected_config_digest=run_context["config_digest"],
        expected_artifact_namespace_value=run_context["artifact_namespace"],
        expected_registry_template_digest=COMPOSE.registry_template_digest(),
    )
    validated_registry = COMPOSE.validate_registry_instance(
        registry_instance, template=registry_template, run_context=run_context,
    )

    require(
        ppq["source_phase"] == authority["authorized_source_phase"] == run_context["source_phase"],
        "V3-PHASE-CROSSCHECK",
    )
    require(ppq["run_id"] == binding["run_id"] == run_context["run_id"], "V3-RUN-CROSSCHECK")
    require(
        ppq["worker_pid"] == binding["worker_pid"] == run_context["worker_pid"],
        "V3-PID-CROSSCHECK",
    )
    require(
        ppq["config_identity_digest"] == binding["config_digest"] == run_context["config_digest"],
        "V3-CONFIG-CROSSCHECK",
    )
    require(binding["artifact_namespace"] == run_context["artifact_namespace"], "V3-NAMESPACE-CROSSCHECK")

    expected = COMPOSE.compose_payload(
        ppq_receipt=source_ppq_receipt,
        laq_v2_payload=source_laq_v2_payload,
        runtime_authority=authority,
        run_binding=binding,
        registry_instance=validated_registry,
    )
    require(payload == expected, "V3-SOURCE-BINDING")
    inherited = COMPOSE._inherited_checks(
        payload,
        expected_source_phase=run_context["source_phase"],
        expected_run_id=run_context["run_id"],
        expected_pid=run_context["worker_pid"],
    )
    failed_inherited = [name for name, passed in inherited.items() if not passed]
    require(not failed_inherited, "V3-INHERITED-PREDICATE:" + ",".join(failed_inherited))

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
        "registry_template_identity": payload["registry_template_digest"] == COMPOSE.registry_template_digest(),
        "registry_instance_identity": payload["registry_instance_digest"] == registry_instance["instance_digest"],
        "composition_identity": payload["composition_contract_digest"] == COMPOSE.composition_contract_digest(),
    }
    require(all(new_authority.values()), "V3-NEW-AUTHORITY-PREDICATE")
    require(receipt == before, "SUPERVISOR-MUTATED-RECEIPT")
    checks.update({
        "schema": True,
        "ppq_v2_r1": True,
        "source_binding": True,
        "inherited_predicates": True,
        "new_authority_predicates": True,
        "supervisor_repair": False,
        "validation_context": True,
    })
    return {
        "pass": True,
        "checks": checks,
        "validation_context_version": DISPATCH.CONTEXT_VERSION,
        "validation_mode": mode.mode.value,
        "inherited_predicates": inherited,
        "new_authority_predicates": new_authority,
        "canonical_field_count": len(payload),
        "ppq_nested_field_count": len(ppq),
        "supervisor_mutations": 0,
    }


def adjudicate_supervisor_v3_with_context(
    receipt: object, *, layer_b_pass: bool, **kwargs: Any,
) -> dict[str, Any]:
    before = deepcopy(receipt)
    try:
        layer_a = validate_layer_a_v3_with_context(receipt, **kwargs)
        passed = bool(layer_b_pass)
    except (
        RACQR1LayerAStop,
        DISPATCH.RACQR1ModeDispatchStop,
        COMPOSE.RACQCompositionStop,
        RACQ.RACQAuthorityStop,
        PPQ_R1.PPQV2R1Stop,
        KeyError,
        TypeError,
        ValueError,
        OSError,
    ) as exc:
        layer_a = {"pass": False, "reason": str(exc), "exception_type": type(exc).__name__}
        passed = False
    require(receipt == before, "SUPERVISOR-MUTATED-RECEIPT")
    return {
        "wrapper_version": WRAPPER_VERSION,
        "layer_a": layer_a,
        "layer_b_pass": layer_b_pass,
        "pass": passed and layer_a.get("pass") is True,
        "status": "PASS" if passed and layer_a.get("pass") is True else "STOP",
        "supervisor_mutations": 0,
    }
