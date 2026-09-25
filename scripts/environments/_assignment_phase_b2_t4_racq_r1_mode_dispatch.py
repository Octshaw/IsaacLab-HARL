"""Pure RACQ-R1 Layer-A validation-context and mode-dispatch contract.

The context selects how an independently existing runtime-authority object is
validated.  It never creates authority, never infers mode from a receipt, and
never permits a caller-supplied boolean override.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

import _assignment_phase_b2_t4_racq_runtime_authority as RACQ


CONTEXT_VERSION = "b2_t4_layer_a_validation_context_v1"
OFFLINE_QUALIFICATION = "OFFLINE_QUALIFICATION"
LIVE_FORMAL_RUNTIME = "LIVE_FORMAL_RUNTIME"

CONTEXT_FIELDS: dict[str, type] = {
    "context_version": str,
    "execution_purpose": str,
    "expected_source_phase": str,
    "expected_runtime_authority_scope": str,
    "expected_live_runtime_grant": bool,
    "expected_run_binding_required": bool,
}


class RACQR1ModeDispatchStop(ValueError):
    """Fail-closed validation-context or dispatch violation."""


class RuntimeAuthorityValidationMode(Enum):
    OFFLINE_QUALIFICATION = OFFLINE_QUALIFICATION
    LIVE_FORMAL_RUNTIME = LIVE_FORMAL_RUNTIME


@dataclass(frozen=True)
class ResolvedValidationMode:
    mode: RuntimeAuthorityValidationMode
    qualification_mode: bool
    authority_scope: str
    instance_purpose: str
    live_runtime_grant: bool
    run_binding_required: bool


MODE_RULES: dict[str, ResolvedValidationMode] = {
    OFFLINE_QUALIFICATION: ResolvedValidationMode(
        mode=RuntimeAuthorityValidationMode.OFFLINE_QUALIFICATION,
        qualification_mode=True,
        authority_scope=RACQ.AUTHORIZATION_SCOPE,
        instance_purpose=RACQ.QUALIFICATION_PURPOSE,
        live_runtime_grant=False,
        run_binding_required=True,
    ),
    LIVE_FORMAL_RUNTIME: ResolvedValidationMode(
        mode=RuntimeAuthorityValidationMode.LIVE_FORMAL_RUNTIME,
        qualification_mode=False,
        authority_scope=RACQ.AUTHORIZATION_SCOPE,
        instance_purpose=RACQ.LIVE_PURPOSE,
        live_runtime_grant=True,
        run_binding_required=True,
    ),
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RACQR1ModeDispatchStop(reason)


def _strict_context(value: object) -> dict[str, Any]:
    require(type(value) is dict, "VALIDATION-CONTEXT-NOT-OBJECT")
    result = value
    require(
        set(result) == set(CONTEXT_FIELDS),
        "VALIDATION-CONTEXT-FIELDS-MISSING-OR-UNKNOWN",
    )
    for field, expected_type in CONTEXT_FIELDS.items():
        require(type(result[field]) is expected_type, f"VALIDATION-CONTEXT-TYPE:{field}")
    return result


def make_validation_context(
    *, execution_purpose: str, expected_source_phase: str,
) -> dict[str, Any]:
    """Construct one strict external context from the canonical mode mapping."""
    require(execution_purpose in MODE_RULES, "VALIDATION-CONTEXT-UNKNOWN-PURPOSE")
    require(RACQ.phase_number(expected_source_phase) is not None, "VALIDATION-CONTEXT-PHASE")
    rule = MODE_RULES[execution_purpose]
    semantic_scope = (
        rule.instance_purpose
        if rule.mode is RuntimeAuthorityValidationMode.OFFLINE_QUALIFICATION
        else rule.authority_scope
    )
    return {
        "context_version": CONTEXT_VERSION,
        "execution_purpose": execution_purpose,
        "expected_source_phase": expected_source_phase,
        "expected_runtime_authority_scope": semantic_scope,
        "expected_live_runtime_grant": rule.live_runtime_grant,
        "expected_run_binding_required": rule.run_binding_required,
    }


def resolve_runtime_authority_validation_mode(
    validation_context: object,
) -> ResolvedValidationMode:
    """Return the sole canonical internal mode mapping, or STOP."""
    context = _strict_context(validation_context)
    require(context["context_version"] == CONTEXT_VERSION, "VALIDATION-CONTEXT-VERSION")
    purpose = context["execution_purpose"]
    require(purpose in MODE_RULES, "VALIDATION-CONTEXT-UNKNOWN-PURPOSE")
    require(
        RACQ.phase_number(context["expected_source_phase"]) is not None,
        "VALIDATION-CONTEXT-PHASE",
    )
    rule = MODE_RULES[purpose]
    expected = make_validation_context(
        execution_purpose=purpose,
        expected_source_phase=context["expected_source_phase"],
    )
    require(context == expected, "VALIDATION-CONTEXT-DERIVATION")
    return rule


def validation_context_schema_document() -> dict[str, Any]:
    return {
        "schema_version": CONTEXT_VERSION,
        "required_fields": {name: kind.__name__ for name, kind in CONTEXT_FIELDS.items()},
        "unknown_fields": "REJECT",
        "missing_fields": "REJECT",
        "wrong_types": "REJECT",
        "execution_purpose_enum": list(MODE_RULES),
        "receipt_field": False,
    }


def validation_context_contract_document() -> dict[str, Any]:
    return {
        "contract_version": CONTEXT_VERSION,
        "owner": "external supervisor/validator input",
        "creates_runtime_authority": False,
        "receipt_selects_mode": False,
        "caller_boolean_override": "REJECT",
        "missing_or_unknown_context": "STOP",
        "canonical_mapping_function": "resolve_runtime_authority_validation_mode",
        "modes": {
            OFFLINE_QUALIFICATION: {
                "authority_instance_purpose": RACQ.QUALIFICATION_PURPOSE,
                "live_runtime_grant": False,
                "run_binding_required": True,
            },
            LIVE_FORMAL_RUNTIME: {
                "authority_scope": RACQ.AUTHORIZATION_SCOPE,
                "authority_instance_purpose": RACQ.LIVE_PURPOSE,
                "authorization_mode": RACQ.AUTHORIZATION_MODE,
                "live_runtime_grant": True,
                "run_binding_required": True,
            },
        },
    }


def mode_dispatch_contract_document() -> dict[str, Any]:
    return {
        "dispatch_authority_count": 1,
        "dispatch_function": "resolve_runtime_authority_validation_mode",
        "implicit_mode_inference": False,
        "receipt_self_selection": False,
        "phase_name_inference": False,
        "filename_inference": False,
        "live_grant_inference": False,
        "context_authorizes_runtime": False,
        "supported_contexts": list(MODE_RULES),
    }
