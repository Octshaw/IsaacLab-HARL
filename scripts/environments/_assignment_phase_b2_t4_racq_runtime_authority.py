"""Pure RACQ formal-runtime authority and run-binding contract.

The frozen PPQ-V2-R1 authority remains offline-only.  This separate candidate
contract represents a future runtime grant, but this module deliberately has no
live-authority issuer.  Qualification fixtures are runtime-shaped and remain
explicitly non-live; a future live instance requires a separately trusted
external-authorization digest supplied by a reviewed supervisor.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping


AUTHORITY_VERSION = "b2_t4_formal_runtime_authority_v1"
BINDING_VERSION = "b2_t4_formal_runtime_run_binding_v1"
AUTHORIZATION_SCOPE = "FORMAL-RUNTIME-AUTHORIZED"
AUTHORIZATION_MODE = "FORMAL_FRESH_ATTEMPT"
QUALIFICATION_PURPOSE = "OFFLINE-RUNTIME-CONTRACT-QUALIFICATION"
LIVE_PURPOSE = "LIVE-FORMAL-RUNTIME"
PHASE_PATTERN = r"^B2-T4-RE6-R([1-9][0-9]*)$"
PHASE_FAMILY = "B2-T4-RE6-R<positive-integer>"
PPQ_PARENT_VERSION = "b2_t4_ppq_fresh_run_success_receipt_v2_1"
PPQ_PARENT_HELPER_SHA256 = "bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0"
PPQ_PARENT_SCHEMA_SHA256 = "d9e28e050616bc1e2f38abfdc32d21ba884b282311d6f141a1c240632582adef"
NAMESPACE_POLICY = "phase-slug_artifacts/run-id"

AUTHORITY_FIELDS: dict[str, type] = {
    "authority_version": str,
    "authorization_scope": str,
    "authorization_mode": str,
    "authorized_source_phase": str,
    "phase_family": str,
    "qualification_parent_version": str,
    "qualification_parent_helper_sha256": str,
    "qualification_parent_schema_sha256": str,
    "expected_ppq_contract": str,
    "allowed_run_binding_contract": str,
    "namespace_policy": str,
    "config_policy_identity": str,
    "external_authorization_digest": str,
    "instance_purpose": str,
    "live_runtime_grant": bool,
    "authority_payload_digest": str,
}

BINDING_FIELDS: dict[str, type] = {
    "binding_version": str,
    "runtime_authority_digest": str,
    "authorized_source_phase": str,
    "run_id": str,
    "worker_pid": int,
    "config_digest": str,
    "artifact_namespace": str,
    "registry_template_digest": str,
    "binding_payload_digest": str,
}

HEX = frozenset("0123456789abcdef")


class RACQAuthorityStop(ValueError):
    """Fail-closed RACQ authority or binding violation."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RACQAuthorityStop(reason)


def canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RACQAuthorityStop("CANONICAL-JSON") from exc


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def sha256_value(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= HEX


def phase_number(source_phase: object) -> int | None:
    if type(source_phase) is not str:
        return None
    match = re.fullmatch(PHASE_PATTERN, source_phase)
    return int(match.group(1)) if match else None


def phase_slug(source_phase: str) -> str:
    require(phase_number(source_phase) is not None, "FORMAL-PHASE-GRAMMAR")
    return source_phase.lower().replace("-", "_")


def valid_run_id(run_id: object) -> bool:
    return type(run_id) is str and bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,127}", run_id))


def expected_artifact_namespace(source_phase: str, run_id: str) -> str:
    require(valid_run_id(run_id), "RUN-ID-GRAMMAR")
    return f"{phase_slug(source_phase)}_artifacts/{run_id}"


def authority_relative_path(source_phase: str) -> Path:
    return Path("runtime_authority") / f"{phase_slug(source_phase)}.json"


def binding_relative_path(source_phase: str, run_id: str) -> Path:
    require(valid_run_id(run_id), "RUN-ID-GRAMMAR")
    return Path("run_binding") / phase_slug(source_phase) / f"{run_id}.json"


def _without_digest(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: value[key] for key in value if key != field}


def _strict(value: object, fields: Mapping[str, type], label: str) -> dict[str, Any]:
    require(type(value) is dict, f"{label}-NOT-OBJECT")
    result = value
    require(set(result) == set(fields), f"{label}-FIELDS-MISSING-OR-UNKNOWN")
    for key, expected_type in fields.items():
        require(type(result[key]) is expected_type, f"{label}-TYPE:{key}")
    return result


def make_offline_qualification_authority(
    *, source_phase: str, external_authorization_digest: str,
    config_policy_identity: str,
) -> dict[str, Any]:
    """Create a non-live fixture for qualification of the runtime contract."""
    require(phase_number(source_phase) is not None, "FORMAL-PHASE-GRAMMAR")
    require(sha256_value(external_authorization_digest), "EXTERNAL-AUTHORIZATION-DIGEST")
    require(sha256_value(config_policy_identity), "CONFIG-POLICY-IDENTITY")
    payload: dict[str, Any] = {
        "authority_version": AUTHORITY_VERSION,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_mode": AUTHORIZATION_MODE,
        "authorized_source_phase": source_phase,
        "phase_family": PHASE_FAMILY,
        "qualification_parent_version": PPQ_PARENT_VERSION,
        "qualification_parent_helper_sha256": PPQ_PARENT_HELPER_SHA256,
        "qualification_parent_schema_sha256": PPQ_PARENT_SCHEMA_SHA256,
        "expected_ppq_contract": PPQ_PARENT_VERSION,
        "allowed_run_binding_contract": BINDING_VERSION,
        "namespace_policy": NAMESPACE_POLICY,
        "config_policy_identity": config_policy_identity,
        "external_authorization_digest": external_authorization_digest,
        "instance_purpose": QUALIFICATION_PURPOSE,
        "live_runtime_grant": False,
    }
    payload["authority_payload_digest"] = digest(payload)
    return payload


def validate_authority_object(
    authority: object, *, expected_source_phase: str,
    expected_external_authorization_digest: str | None,
    expected_config_policy_identity: str,
    qualification_mode: bool,
) -> dict[str, Any]:
    result = _strict(authority, AUTHORITY_FIELDS, "RUNTIME-AUTHORITY")
    require(result["authority_version"] == AUTHORITY_VERSION, "RUNTIME-AUTHORITY-VERSION")
    require(result["authorization_scope"] == AUTHORIZATION_SCOPE, "RUNTIME-AUTHORITY-SCOPE")
    require(result["authorization_mode"] == AUTHORIZATION_MODE, "RUNTIME-AUTHORITY-MODE")
    require(phase_number(expected_source_phase) is not None, "EXPECTED-PHASE-GRAMMAR")
    require(
        result["authorized_source_phase"] == expected_source_phase,
        "RUNTIME-AUTHORITY-PHASE",
    )
    require(result["phase_family"] == PHASE_FAMILY, "RUNTIME-AUTHORITY-FAMILY")
    require(
        result["qualification_parent_version"] == PPQ_PARENT_VERSION
        and result["qualification_parent_helper_sha256"] == PPQ_PARENT_HELPER_SHA256
        and result["qualification_parent_schema_sha256"] == PPQ_PARENT_SCHEMA_SHA256,
        "RUNTIME-AUTHORITY-QUALIFICATION-PARENT",
    )
    require(
        result["expected_ppq_contract"] == PPQ_PARENT_VERSION,
        "RUNTIME-AUTHORITY-PPQ-CONTRACT",
    )
    require(
        result["allowed_run_binding_contract"] == BINDING_VERSION,
        "RUNTIME-AUTHORITY-BINDING-CONTRACT",
    )
    require(result["namespace_policy"] == NAMESPACE_POLICY, "RUNTIME-AUTHORITY-NAMESPACE-POLICY")
    require(
        result["config_policy_identity"] == expected_config_policy_identity,
        "RUNTIME-AUTHORITY-CONFIG-POLICY",
    )
    require(
        expected_external_authorization_digest is not None
        and sha256_value(expected_external_authorization_digest)
        and result["external_authorization_digest"] == expected_external_authorization_digest,
        "RUNTIME-AUTHORITY-EXTERNAL-AUTHORIZATION",
    )
    if qualification_mode:
        require(
            result["instance_purpose"] == QUALIFICATION_PURPOSE
            and result["live_runtime_grant"] is False,
            "RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE",
        )
    else:
        require(
            result["instance_purpose"] == LIVE_PURPOSE
            and result["live_runtime_grant"] is True,
            "RUNTIME-AUTHORITY-LIVE-GRANT",
        )
    require(
        result["authority_payload_digest"]
        == digest(_without_digest(result, "authority_payload_digest")),
        "RUNTIME-AUTHORITY-DIGEST",
    )
    return result


def _read_exact_canonical(path: Path, expected: Path, root: Path, label: str) -> dict[str, Any]:
    require(all(isinstance(item, Path) for item in (path, expected, root)), f"{label}-PATH-TYPE")
    require(".." not in path.parts and ".." not in expected.parts, f"{label}-PATH-TRAVERSAL")
    require(path == expected, f"{label}-UNEXPECTED-PATH")
    require(path.exists() and path.is_file(), f"{label}-MISSING")
    require(not path.is_symlink(), f"{label}-SYMLINK")
    root_resolved = root.resolve(strict=True)
    path_resolved = path.resolve(strict=True)
    require(path_resolved.is_relative_to(root_resolved), f"{label}-OUTSIDE-ROOT")
    cursor = path_resolved.parent
    while cursor != root_resolved:
        require(not cursor.is_symlink(), f"{label}-PARENT-SYMLINK")
        cursor = cursor.parent
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RACQAuthorityStop(f"{label}-JSON") from exc
    require(raw == canonical(value), f"{label}-NONCANONICAL-CONTENT")
    return value


def load_runtime_authority(
    *, actual_path: Path, authority_root: Path, expected_source_phase: str,
    expected_external_authorization_digest: str | None,
    expected_config_policy_identity: str, qualification_mode: bool,
) -> dict[str, Any]:
    expected_path = authority_root / authority_relative_path(expected_source_phase)
    value = _read_exact_canonical(actual_path, expected_path, authority_root, "RUNTIME-AUTHORITY")
    return validate_authority_object(
        value, expected_source_phase=expected_source_phase,
        expected_external_authorization_digest=expected_external_authorization_digest,
        expected_config_policy_identity=expected_config_policy_identity,
        qualification_mode=qualification_mode,
    )


def make_run_binding(
    *, authority: Mapping[str, Any], run_id: str, worker_pid: int,
    config_digest: str, artifact_namespace: str, registry_template_digest: str,
) -> dict[str, Any]:
    require(valid_run_id(run_id), "RUN-ID-GRAMMAR")
    require(type(worker_pid) is int and worker_pid > 0, "WORKER-PID")
    require(sha256_value(config_digest), "CONFIG-DIGEST")
    require(sha256_value(registry_template_digest), "REGISTRY-TEMPLATE-DIGEST")
    source_phase = authority.get("authorized_source_phase")
    require(type(source_phase) is str, "BINDING-AUTHORITY-PHASE")
    require(
        artifact_namespace == expected_artifact_namespace(source_phase, run_id),
        "BINDING-NAMESPACE",
    )
    payload: dict[str, Any] = {
        "binding_version": BINDING_VERSION,
        "runtime_authority_digest": authority.get("authority_payload_digest"),
        "authorized_source_phase": source_phase,
        "run_id": run_id,
        "worker_pid": worker_pid,
        "config_digest": config_digest,
        "artifact_namespace": artifact_namespace,
        "registry_template_digest": registry_template_digest,
    }
    payload["binding_payload_digest"] = digest(payload)
    return payload


def validate_binding_object(
    binding: object, *, authority: Mapping[str, Any], expected_run_id: str,
    expected_worker_pid: int, expected_config_digest: str,
    expected_artifact_namespace: str, expected_registry_template_digest: str,
) -> dict[str, Any]:
    result = _strict(binding, BINDING_FIELDS, "RUN-BINDING")
    require(result["binding_version"] == BINDING_VERSION, "RUN-BINDING-VERSION")
    require(result["runtime_authority_digest"] == authority.get("authority_payload_digest"), "RUN-BINDING-AUTHORITY")
    require(result["authorized_source_phase"] == authority.get("authorized_source_phase"), "RUN-BINDING-PHASE")
    require(result["run_id"] == expected_run_id and valid_run_id(expected_run_id), "RUN-BINDING-RUN-ID")
    require(result["worker_pid"] == expected_worker_pid and expected_worker_pid > 0, "RUN-BINDING-PID")
    require(result["config_digest"] == expected_config_digest, "RUN-BINDING-CONFIG")
    require(result["artifact_namespace"] == expected_artifact_namespace, "RUN-BINDING-NAMESPACE")
    require(
        result["artifact_namespace"]
        == globals()["expected_artifact_namespace"](result["authorized_source_phase"], result["run_id"]),
        "RUN-BINDING-NAMESPACE-POLICY",
    )
    require(result["registry_template_digest"] == expected_registry_template_digest, "RUN-BINDING-REGISTRY-TEMPLATE")
    require(
        result["binding_payload_digest"] == digest(_without_digest(result, "binding_payload_digest")),
        "RUN-BINDING-DIGEST",
    )
    return result


def load_run_binding(
    *, actual_path: Path, authority_root: Path, authority: Mapping[str, Any],
    expected_run_id: str, expected_worker_pid: int, expected_config_digest: str,
    expected_artifact_namespace_value: str, expected_registry_template_digest: str,
) -> dict[str, Any]:
    source_phase = authority.get("authorized_source_phase")
    require(type(source_phase) is str, "RUN-BINDING-AUTHORITY-PHASE")
    expected_path = authority_root / binding_relative_path(source_phase, expected_run_id)
    value = _read_exact_canonical(actual_path, expected_path, authority_root, "RUN-BINDING")
    return validate_binding_object(
        value, authority=authority, expected_run_id=expected_run_id,
        expected_worker_pid=expected_worker_pid,
        expected_config_digest=expected_config_digest,
        expected_artifact_namespace=expected_artifact_namespace_value,
        expected_registry_template_digest=expected_registry_template_digest,
    )


def authority_schema_document() -> dict[str, Any]:
    return {
        "schema_version": AUTHORITY_VERSION,
        "required_fields": {name: value.__name__ for name, value in AUTHORITY_FIELDS.items()},
        "unknown_fields": "REJECT",
        "formal_phase_pattern": PHASE_PATTERN,
        "authorized_phase_cardinality": 1,
        "runtime_scope": AUTHORIZATION_SCOPE,
        "offline_fixture_is_live_grant": False,
        "external_authorization_is_trusted_supervisor_input": True,
        "digest": "SHA-256(sorted compact UTF-8 JSON excluding authority_payload_digest)",
    }


def binding_schema_document() -> dict[str, Any]:
    return {
        "schema_version": BINDING_VERSION,
        "required_fields": {name: value.__name__ for name, value in BINDING_FIELDS.items()},
        "unknown_fields": "REJECT",
        "two_stage": True,
        "binds": ["authority digest", "phase", "run_id", "worker PID", "config digest", "namespace", "registry template"],
        "digest": "SHA-256(sorted compact UTF-8 JSON excluding binding_payload_digest)",
    }


def authority_contract_document() -> dict[str, Any]:
    return {
        "version": AUTHORITY_VERSION,
        "scope": AUTHORIZATION_SCOPE,
        "mode": AUTHORIZATION_MODE,
        "qualification_parent": PPQ_PARENT_VERSION,
        "caller_string_is_authority": False,
        "grammar_is_authority": False,
        "live_issuer_implemented": False,
        "future_live_transition": "reviewed RACQ + later explicit user authorization -> one external instance",
        "offline_qualification_instances": "runtime-shaped but live_runtime_grant=false",
    }


def authority_path_policy_document() -> dict[str, Any]:
    return {
        "formula": "runtime_authority/<canonical-phase-slug>.json",
        "phase_slug": "lowercase source phase with hyphens replaced by underscores",
        "caller_basename_allowed": False,
        "path_traversal": "REJECT",
        "alias_or_symlink": "REJECT",
        "content": "canonical JSON and recomputed digest required",
    }


def binding_path_policy_document() -> dict[str, Any]:
    return {
        "formula": "run_binding/<canonical-phase-slug>/<run-id>.json",
        "caller_basename_allowed": False,
        "path_traversal": "REJECT",
        "alias_or_symlink": "REJECT",
        "content": "canonical JSON and recomputed digest required",
    }
