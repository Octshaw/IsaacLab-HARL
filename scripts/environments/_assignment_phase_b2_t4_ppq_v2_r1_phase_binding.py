"""Pure PPQ-V2-R1 source-phase binding; no Isaac, HARL, or CUDA imports.

The reviewed PPQ-V2 implementation remains immutable.  This module composes
it through an explicit legacy projection: only the receipt version, helper /
schema identities, and source-phase authorization layer differ.  Every other
receipt predicate is adjudicated by the reviewed PPQ-V2 validator itself.

The expected authority path is a trust input owned by a reviewed supervisor;
an authority supplied by the evidence caller cannot select that path.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as LEGACY


VERSION = "b2_t4_ppq_fresh_run_success_receipt_v2_1"
AUTHORITY_VERSION = "b2_t4_formal_source_phase_authority_v1"
RUN_BINDING_VERSION = "source_phase_run_binding_v1"
FORMAL_PHASE_PATTERN = r"^B2-T4-RE6-R([1-9][0-9]*)$"
FORMAL_PHASE_FAMILY = "B2-T4-RE6-R<positive-integer>"
QUALIFICATION_SCOPE = "OFFLINE-QUALIFICATION-ONLY"
ISSUING_PHASE = "B2-T4-PPQ-V2-R1"
FORMAL_MODE = "FORMAL_FRESH_ATTEMPT"
SYNTHETIC_MODE = "OFFLINE_SYNTHETIC_QUALIFICATION"
HISTORICAL_MODE = "HISTORICAL_COMPATIBILITY_REPLAY"
AUTHORITY_MODES = (FORMAL_MODE, SYNTHETIC_MODE, HISTORICAL_MODE)
RUN_BINDING_MODE = "REQUIRED"

AUTHORITY_FIELDS: dict[str, type] = {
    "authority_version": str,
    "authorization_mode": str,
    "authorized_source_phase": str,
    "phase_family": str,
    "attempt_identifier": int,
    "qualification_scope": str,
    "expected_ppq_contract_version": str,
    "run_binding_mode": str,
    "authorized_run_id": type(None),
    "issued_from_reviewed_phase": str,
    "authority_instance_id": str,
    "authority_payload_digest": str,
}

RUN_BINDING_FIELDS: dict[str, type] = {
    "binding_version": str,
    "authority_digest": str,
    "authorized_source_phase": str,
    "run_id": str,
    "worker_pid": int,
    "config_digest": str,
    "artifact_namespace": str,
    "binding_payload_digest": str,
}

AUTHORITY_RECEIPT_FIELDS: dict[str, type] = {
    "source_phase_authority_version": str,
    "source_phase_authority_digest": str,
    "source_phase_authorization_mode": str,
    "source_phase_run_binding_digest": str,
}

FIELDS = {**LEGACY.FIELDS, **AUTHORITY_RECEIPT_FIELDS}


class PPQV2R1Stop(LEGACY.PPQV2Stop):
    """Fail-closed PPQ-V2-R1 contract violation."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise PPQV2R1Stop(reason)


def canonical(value: object) -> bytes:
    return LEGACY.canonical(value)


def digest(value: object) -> str:
    return LEGACY.digest(value)


def sha_file(path: Path) -> str:
    return LEGACY.sha_file(path)


def atomic_persist(path: Path, payload: Mapping[str, Any]) -> str:
    return LEGACY.atomic_persist(path, payload)


def readback(path: Path) -> tuple[dict[str, Any], str]:
    return LEGACY.readback(path)


def formal_attempt_identifier(source_phase: object) -> int | None:
    if type(source_phase) is not str:
        return None
    match = re.fullmatch(FORMAL_PHASE_PATTERN, source_phase)
    return int(match.group(1)) if match else None


def expected_artifact_namespace(source_phase: str, run_id: str) -> str:
    need(formal_attempt_identifier(source_phase) is not None, "FORMAL-PHASE-GRAMMAR")
    need(type(run_id) is str and bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,127}", run_id)),
         "RUN-ID-GRAMMAR")
    return f"{source_phase.lower().replace('-', '_')}_artifacts/{run_id}"


def _payload_without_digest(value: Mapping[str, Any], digest_field: str) -> dict[str, Any]:
    return {key: value[key] for key in value if key != digest_field}


def make_offline_authority(*, source_phase: str, authority_instance_id: str,
                           authorization_mode: str = FORMAL_MODE) -> dict[str, Any]:
    """Construct an offline qualification authority, never a runtime grant."""
    attempt = formal_attempt_identifier(source_phase)
    payload: dict[str, Any] = {
        "authority_version": AUTHORITY_VERSION,
        "authorization_mode": authorization_mode,
        "authorized_source_phase": source_phase,
        "phase_family": FORMAL_PHASE_FAMILY,
        "attempt_identifier": attempt if attempt is not None else 1,
        "qualification_scope": QUALIFICATION_SCOPE,
        "expected_ppq_contract_version": VERSION,
        "run_binding_mode": RUN_BINDING_MODE,
        "authorized_run_id": None,
        "issued_from_reviewed_phase": ISSUING_PHASE,
        "authority_instance_id": authority_instance_id,
    }
    payload["authority_payload_digest"] = digest(payload)
    return payload


def make_run_binding(*, authority: Mapping[str, Any], run_id: str, worker_pid: int,
                     config_digest: str, artifact_namespace: str) -> dict[str, Any]:
    """Derive a run-specific binding from a previously selected phase authority."""
    payload: dict[str, Any] = {
        "binding_version": RUN_BINDING_VERSION,
        "authority_digest": authority.get("authority_payload_digest"),
        "authorized_source_phase": authority.get("authorized_source_phase"),
        "run_id": run_id,
        "worker_pid": worker_pid,
        "config_digest": config_digest,
        "artifact_namespace": artifact_namespace,
    }
    payload["binding_payload_digest"] = digest(payload)
    return payload


def authority_schema_document() -> dict[str, Any]:
    return {
        "authority_version": AUTHORITY_VERSION,
        "required_fields": {name: typ.__name__ for name, typ in AUTHORITY_FIELDS.items()},
        "unknown_fields": "REJECT",
        "canonical_encoding": "UTF-8 JSON; sort_keys=true; separators=(',', ':'); allow_nan=false",
        "digest_construction": "SHA-256(canonical object excluding authority_payload_digest)",
        "formal_phase_pattern": FORMAL_PHASE_PATTERN,
        "formal_phase_family": FORMAL_PHASE_FAMILY,
        "allowed_modes": list(AUTHORITY_MODES),
        "formal_success_mode": FORMAL_MODE,
        "qualification_scope": QUALIFICATION_SCOPE,
        "authorized_phase_cardinality": 1,
        "run_binding": "two-stage / REQUIRED",
        "path_policy": "exact expected regular non-symlink path plus canonical content digest",
    }


def run_binding_schema_document() -> dict[str, Any]:
    return {
        "binding_version": RUN_BINDING_VERSION,
        "required_fields": {name: typ.__name__ for name, typ in RUN_BINDING_FIELDS.items()},
        "unknown_fields": "REJECT",
        "canonical_encoding": "UTF-8 JSON; sort_keys=true; separators=(',', ':'); allow_nan=false",
        "digest_construction": "SHA-256(canonical object excluding binding_payload_digest)",
        "binds": ["authority digest", "exact source phase", "run_id", "worker_pid",
                  "config digest", "artifact namespace"],
    }


def schema_document() -> dict[str, Any]:
    return {
        "contract_version": VERSION,
        "inherits_non_phase_contract": LEGACY.VERSION,
        "required_fields": {name: typ.__name__ for name, typ in FIELDS.items()},
        "unknown_fields": "REJECT",
        "source_phase": {
            "grammar": FORMAL_PHASE_PATTERN,
            "grammar_is_authority": False,
            "exact_equality": "receipt == expected == external authority",
        },
        "new_authority_fields": list(AUTHORITY_RECEIPT_FIELDS),
        "fixed_reviewed_identity": LEGACY.schema_document()["fixed_reviewed_identity"],
        "non_phase_validation": "reviewed PPQ-V2 validator via phase/identity-only projection",
        "success_route": LEGACY.schema_document()["success_route"],
    }


def _strict_types(value: object, fields: Mapping[str, type], label: str) -> dict[str, Any]:
    need(type(value) is dict, f"{label}-NOT-OBJECT")
    result = value
    need(set(result) == set(fields), f"{label}-FIELDS-MISSING-OR-UNKNOWN")
    for key, expected in fields.items():
        need(type(result[key]) is expected, f"{label}-TYPE-{key}")
    return result


def _read_exact_canonical_json(*, actual_path: Path, expected_path: Path,
                               authority_root: Path, label: str) -> dict[str, Any]:
    need(isinstance(actual_path, Path) and isinstance(expected_path, Path) and
         isinstance(authority_root, Path), f"{label}-PATH-TYPE")
    need(".." not in actual_path.parts and ".." not in expected_path.parts,
         f"{label}-PATH-TRAVERSAL")
    need(actual_path == expected_path, f"{label}-UNEXPECTED-PATH")
    need(actual_path.exists() and actual_path.is_file(), f"{label}-MISSING")
    need(not actual_path.is_symlink(), f"{label}-SYMLINK")
    resolved_root = authority_root.resolve(strict=True)
    resolved_actual = actual_path.resolve(strict=True)
    resolved_expected = expected_path.resolve(strict=True)
    need(resolved_actual == resolved_expected and resolved_actual.parent == resolved_root,
         f"{label}-RESOLVED-PATH")
    raw = actual_path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PPQV2R1Stop(f"{label}-JSON") from exc
    need(raw == canonical(value), f"{label}-NONCANONICAL-CONTENT")
    return value


def load_phase_authority(*, actual_path: Path, expected_path: Path,
                         authority_root: Path, required_mode: str = FORMAL_MODE) -> dict[str, Any]:
    authority = _strict_types(
        _read_exact_canonical_json(actual_path=actual_path, expected_path=expected_path,
                                   authority_root=authority_root, label="PHASE-AUTHORITY"),
        AUTHORITY_FIELDS, "PHASE-AUTHORITY")
    need(authority["authority_version"] == AUTHORITY_VERSION, "PHASE-AUTHORITY-VERSION")
    need(required_mode in AUTHORITY_MODES and authority["authorization_mode"] == required_mode,
         "PHASE-AUTHORITY-MODE")
    need(authority["qualification_scope"] == QUALIFICATION_SCOPE,
         "PHASE-AUTHORITY-SCOPE")
    need(authority["expected_ppq_contract_version"] == VERSION,
         "PHASE-AUTHORITY-PPQ-VERSION")
    need(authority["run_binding_mode"] == RUN_BINDING_MODE and
         authority["authorized_run_id"] is None, "PHASE-AUTHORITY-RUN-MODE")
    need(authority["issued_from_reviewed_phase"] == ISSUING_PHASE,
         "PHASE-AUTHORITY-ISSUER")
    need(authority["phase_family"] == FORMAL_PHASE_FAMILY,
         "PHASE-AUTHORITY-FAMILY")
    attempt = formal_attempt_identifier(authority["authorized_source_phase"])
    need(attempt is not None and authority["attempt_identifier"] == attempt,
         "PHASE-AUTHORITY-FORMAL-GRAMMAR")
    need(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,95}", authority["authority_instance_id"])),
         "PHASE-AUTHORITY-INSTANCE-ID")
    need(actual_path.name == f"{authority['authority_instance_id']}.source_phase_authority.json",
         "PHASE-AUTHORITY-FILENAME")
    computed = digest(_payload_without_digest(authority, "authority_payload_digest"))
    need(authority["authority_payload_digest"] == computed,
         "PHASE-AUTHORITY-DIGEST")
    return authority


def load_run_binding(*, actual_path: Path, expected_path: Path,
                     authority_root: Path) -> dict[str, Any]:
    binding = _strict_types(
        _read_exact_canonical_json(actual_path=actual_path, expected_path=expected_path,
                                   authority_root=authority_root, label="RUN-BINDING"),
        RUN_BINDING_FIELDS, "RUN-BINDING")
    need(binding["binding_version"] == RUN_BINDING_VERSION, "RUN-BINDING-VERSION")
    need(LEGACY._sha(binding["authority_digest"]) and
         LEGACY._sha(binding["config_digest"]), "RUN-BINDING-SHA")
    need(binding["worker_pid"] > 0, "RUN-BINDING-PID")
    need(actual_path.name == f"{binding['run_id']}.source_phase_run_binding.json",
         "RUN-BINDING-FILENAME")
    computed = digest(_payload_without_digest(binding, "binding_payload_digest"))
    need(binding["binding_payload_digest"] == computed, "RUN-BINDING-DIGEST")
    return binding


def _legacy_projection(receipt: Mapping[str, Any],
                       legacy_identity: Mapping[str, str]) -> dict[str, Any]:
    projected = {key: copy.deepcopy(receipt[key]) for key in LEGACY.FIELDS}
    projected["contract_version"] = LEGACY.VERSION
    projected["source_phase"] = LEGACY.FRESH_PHASES[0]
    projected["ppq_v2_helper_sha256"] = legacy_identity["ppq_v2_helper_sha256"]
    projected["ppq_v2_schema_sha256"] = legacy_identity["ppq_v2_schema_sha256"]
    return projected


def validate_receipt(receipt: Mapping[str, Any], *, expected_phase: str,
                     identity: Mapping[str, str], legacy_identity: Mapping[str, str],
                     config: Mapping[str, int], authority_path: Path,
                     expected_authority_path: Path, run_binding_path: Path,
                     expected_run_binding_path: Path, authority_root: Path,
                     artifact_namespace: str) -> None:
    candidate = _strict_types(receipt, FIELDS, "RECEIPT")
    need(candidate["contract_version"] == VERSION and
         candidate["campaign_status"] == "SUCCESS", "RECEIPT-VERSION-OR-STATUS")
    need(sha_file(Path(__file__)) == identity.get("ppq_v2_helper_sha256"),
         "PPQ-V2-R1-HELPER-IDENTITY")
    need(digest(schema_document()) == identity.get("ppq_v2_schema_sha256"),
         "PPQ-V2-R1-SCHEMA-IDENTITY")
    authority = load_phase_authority(actual_path=authority_path,
                                     expected_path=expected_authority_path,
                                     authority_root=authority_root,
                                     required_mode=FORMAL_MODE)
    binding = load_run_binding(actual_path=run_binding_path,
                               expected_path=expected_run_binding_path,
                               authority_root=authority_root)
    need(formal_attempt_identifier(expected_phase) is not None,
         "EXPECTED-FORMAL-PHASE-GRAMMAR")
    need(candidate["source_phase"] == expected_phase ==
         authority["authorized_source_phase"], "SOURCE-PHASE-AUTHORITY")
    need(candidate["source_phase_authority_version"] == AUTHORITY_VERSION,
         "RECEIPT-AUTHORITY-VERSION")
    need(candidate["source_phase_authority_digest"] ==
         authority["authority_payload_digest"], "RECEIPT-AUTHORITY-DIGEST")
    need(candidate["source_phase_authorization_mode"] == FORMAL_MODE,
         "RECEIPT-AUTHORITY-MODE")
    need(candidate["source_phase_run_binding_digest"] ==
         binding["binding_payload_digest"], "RECEIPT-RUN-BINDING-DIGEST")
    need(binding["authority_digest"] == authority["authority_payload_digest"] and
         binding["authorized_source_phase"] == expected_phase,
         "RUN-BINDING-AUTHORITY")
    need(binding["run_id"] == candidate["run_id"] and
         binding["worker_pid"] == candidate["worker_pid"], "RUN-BINDING-PROCESS")
    need(binding["config_digest"] == candidate["config_identity_digest"] ==
         identity.get("config_identity_digest"), "RUN-BINDING-CONFIG")
    need(binding["artifact_namespace"] == artifact_namespace ==
         expected_artifact_namespace(expected_phase, candidate["run_id"]),
         "RUN-BINDING-NAMESPACE")
    projected = _legacy_projection(candidate, legacy_identity)
    LEGACY.validate_receipt(projected, expected_phase=LEGACY.FRESH_PHASES[0],
                            identity=legacy_identity, config=config)


def _preflight_binding(*, evidence: Mapping[str, Any], expected_phase: str,
                       identity: Mapping[str, str], authority_path: Path,
                       expected_authority_path: Path, run_binding_path: Path,
                       expected_run_binding_path: Path, authority_root: Path,
                       artifact_namespace: str) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = load_phase_authority(actual_path=authority_path,
                                     expected_path=expected_authority_path,
                                     authority_root=authority_root,
                                     required_mode=FORMAL_MODE)
    binding = load_run_binding(actual_path=run_binding_path,
                               expected_path=expected_run_binding_path,
                               authority_root=authority_root)
    need(type(evidence) is dict and evidence.get("source_phase") == expected_phase ==
         authority["authorized_source_phase"], "PREFLIGHT-SOURCE-PHASE")
    need(binding["authority_digest"] == authority["authority_payload_digest"] and
         binding["authorized_source_phase"] == expected_phase,
         "PREFLIGHT-RUN-AUTHORITY")
    need(binding["run_id"] == evidence.get("run_id") and
         binding["worker_pid"] == evidence.get("worker_pid"), "PREFLIGHT-RUN-PROCESS")
    need(binding["config_digest"] == identity.get("config_identity_digest"),
         "PREFLIGHT-RUN-CONFIG")
    need(binding["artifact_namespace"] == artifact_namespace ==
         expected_artifact_namespace(expected_phase, evidence["run_id"]),
         "PREFLIGHT-RUN-NAMESPACE")
    return authority, binding


def build_receipt(evidence: Mapping[str, Any], *,
                  w2e_selector: Callable[..., dict[str, Any]], w2i_manifest: Path,
                  pw_reconcile: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                  expected_phase: str, config: Mapping[str, int],
                  identity: Mapping[str, str], legacy_identity: Mapping[str, str],
                  production_sources: Mapping[str, Path], pw_helper_path: Path,
                  authority_path: Path, expected_authority_path: Path,
                  run_binding_path: Path, expected_run_binding_path: Path,
                  authority_root: Path, artifact_namespace: str,
                  receipt_mutator: Callable[[dict[str, Any]], None] | None = None,
                  ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    authority, binding = _preflight_binding(
        evidence=evidence, expected_phase=expected_phase, identity=identity,
        authority_path=authority_path, expected_authority_path=expected_authority_path,
        run_binding_path=run_binding_path, expected_run_binding_path=expected_run_binding_path,
        authority_root=authority_root, artifact_namespace=artifact_namespace)
    projected_evidence = copy.deepcopy(dict(evidence))
    projected_evidence["source_phase"] = LEGACY.FRESH_PHASES[0]
    legacy_receipt, w2, pw, old_trace = LEGACY.build_receipt(
        projected_evidence, w2e_selector=w2e_selector, w2i_manifest=w2i_manifest,
        pw_reconcile=pw_reconcile, expected_phase=LEGACY.FRESH_PHASES[0], config=config,
        identity=legacy_identity, production_sources=production_sources,
        pw_helper_path=pw_helper_path)
    receipt = dict(legacy_receipt)
    receipt.update({
        "contract_version": VERSION,
        "source_phase": expected_phase,
        "ppq_v2_helper_sha256": identity["ppq_v2_helper_sha256"],
        "ppq_v2_schema_sha256": identity["ppq_v2_schema_sha256"],
        "source_phase_authority_version": AUTHORITY_VERSION,
        "source_phase_authority_digest": authority["authority_payload_digest"],
        "source_phase_authorization_mode": authority["authorization_mode"],
        "source_phase_run_binding_digest": binding["binding_payload_digest"],
    })
    if receipt_mutator:
        receipt_mutator(receipt)
    validate_receipt(
        receipt, expected_phase=expected_phase, identity=identity,
        legacy_identity=legacy_identity, config=config, authority_path=authority_path,
        expected_authority_path=expected_authority_path, run_binding_path=run_binding_path,
        expected_run_binding_path=expected_run_binding_path, authority_root=authority_root,
        artifact_namespace=artifact_namespace)
    trace = ["00_phase_authority_and_run_binding_preflight"]
    trace.extend("04_legacy_non_phase_schema_validate" if item == "04_schema_validate" else item
                 for item in old_trace)
    trace.append("05_v2_1_phase_authority_schema_validate")
    return receipt, w2, pw, trace


def finalize_campaign(evidence: Mapping[str, Any], *,
                      w2e_selector: Callable[..., dict[str, Any]], w2i_manifest: Path,
                      pw_reconcile: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                      expected_phase: str, config: Mapping[str, int],
                      identity: Mapping[str, str], legacy_identity: Mapping[str, str],
                      production_sources: Mapping[str, Path], pw_helper_path: Path,
                      authority_path: Path, expected_authority_path: Path,
                      run_binding_path: Path, expected_run_binding_path: Path,
                      authority_root: Path, artifact_namespace: str,
                      writer: Callable[[Path, Mapping[str, Any]], str],
                      reader: Callable[[Path], tuple[dict[str, Any], str]], output_dir: Path,
                      receipt_mutator: Callable[[dict[str, Any]], None] | None = None,
                      readback_guard: Callable[[dict[str, Any], str], None] | None = None,
                      before_publication: Callable[[dict[str, Any]], None] | None = None,
                      ) -> dict[str, Any]:
    need(callable(writer) and callable(reader) and isinstance(output_dir, Path),
         "EXPLICIT-PERSISTENCE-DEPENDENCIES")
    receipt, w2, pw, trace = build_receipt(
        evidence, w2e_selector=w2e_selector, w2i_manifest=w2i_manifest,
        pw_reconcile=pw_reconcile, expected_phase=expected_phase, config=config,
        identity=identity, legacy_identity=legacy_identity,
        production_sources=production_sources, pw_helper_path=pw_helper_path,
        authority_path=authority_path, expected_authority_path=expected_authority_path,
        run_binding_path=run_binding_path, expected_run_binding_path=expected_run_binding_path,
        authority_root=authority_root, artifact_namespace=artifact_namespace,
        receipt_mutator=receipt_mutator)
    provisional = {w: (w2 if w == "W2E" else evidence["witnesses"][w])
                   for w in LEGACY.WITNESSES}
    provisional_digests = {w: digest(provisional[w]) for w in LEGACY.WITNESSES}
    if before_publication:
        before_publication(provisional)
    path = output_dir / "candidate_success_receipt_v2_1.json"
    expected_sha = writer(path, receipt)
    trace.append("06_durable_write")
    observed, observed_sha = reader(path)
    trace.append("07_readback")
    need(observed == receipt and observed_sha == expected_sha == digest(receipt),
         "RECEIPT-DIGEST-OR-READBACK")
    trace.append("08_digest_validate")
    if readback_guard:
        readback_guard(observed, observed_sha)
    validate_receipt(
        observed, expected_phase=expected_phase, identity=identity,
        legacy_identity=legacy_identity, config=config, authority_path=authority_path,
        expected_authority_path=expected_authority_path, run_binding_path=run_binding_path,
        expected_run_binding_path=expected_run_binding_path, authority_root=authority_root,
        artifact_namespace=artifact_namespace)
    trace.append("09_schema_revalidate")
    publication = LEGACY.publish_witnesses(
        validated=True, receipt_sha256=observed_sha, witnesses=provisional,
        provisional_digests=provisional_digests, writer=writer, output_dir=output_dir)
    trace.append("10_canonical_witness_publication")
    return {"pass": True, "receipt": receipt, "receipt_sha256": observed_sha,
            "publication": publication, "trace": trace,
            "w2e": {"candidate_count": w2["candidate_count"],
                    "valid_count": w2["valid_count"], "selected": w2["selected"]},
            "pw": pw}


def failure_semantics(*, mutation_occurred: bool) -> dict[str, Any]:
    need(type(mutation_occurred) is bool, "FAILURE-MUTATION-TYPE")
    return {"partial_update": mutation_occurred, "route_poisoned": mutation_occurred,
            "retry": False, "success_receipt": None,
            "canonical_success_witnesses": []}
