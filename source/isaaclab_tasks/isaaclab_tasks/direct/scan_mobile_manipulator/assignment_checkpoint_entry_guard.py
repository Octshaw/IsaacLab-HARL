"""Pure semantic guard for assignment checkpoint entry boundaries.

This module owns only entry intent and native metadata-pair handling.  Manifest
schemas and compatibility decisions remain owned by the V2/V3 contracts and
the semantic dispatcher.  No tensor framework, model, trainer, runner, or
Isaac runtime is imported here.
"""

from __future__ import annotations


if __name__ != (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_entry_guard"
):
    raise ImportError(
        "CanonicalModuleIdentityError: assignment checkpoint entry guard must "
        "be imported by its canonical package key; expected="
        "'isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_checkpoint_entry_guard'; actual="
        f"{__name__!r}"
    )


import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from . import assignment_checkpoint_contract as _v2
from . import assignment_checkpoint_contract_v3 as _v3
from . import assignment_checkpoint_semantic_dispatch as _dispatch


# These are the native filenames already used by the V2 save/load contract.
# They are repeated here only to keep this pure filesystem adapter independent
# of assignment_checkpoint_save.py, which imports torch.
CONTRACT_MANIFEST_FILE = "assignment_contract_manifest.json"
CONTRACT_FINGERPRINT_FILE = "assignment_contract_fingerprint.txt"


class AssignmentCheckpointEntryPurpose(str, Enum):
    """Glue-only entry intent; this is not a manifest semantic authority."""

    SAVE = "save"
    LOAD_CONTINUATION = "load_continuation"
    LOAD_EVALUATION = "load_evaluation"
    LOAD_PLAYBACK = "load_playback"
    OFFLINE_AUDIT = "offline_audit"


class AssignmentCheckpointMetadataMode(str, Enum):
    BOTH_PRESENT = "both_present"
    BOTH_ABSENT = "both_absent"
    PARTIAL = "partial"


class AssignmentCheckpointEntryGuardError(RuntimeError):
    """Base error for entry-glue validation failures."""


class AssignmentCheckpointMetadataPairError(AssignmentCheckpointEntryGuardError):
    """The native metadata pair is partial, malformed, or non-canonical."""


class AssignmentCheckpointFingerprintError(AssignmentCheckpointEntryGuardError):
    """The stored fingerprint is malformed or does not bind the manifest."""


class AssignmentCheckpointEntryPurposeDeniedError(
    AssignmentCheckpointEntryGuardError
):
    """The selected semantic family does not authorize the requested entry."""

    def __init__(self, result: "AssignmentCheckpointEntryGuardResult") -> None:
        self.result = result
        super().__init__(
            f"{result.decision_classification}: {result.reason}"
        )


@dataclass(frozen=True, slots=True)
class AssignmentCheckpointMetadataPairState:
    checkpoint_directory: Path
    manifest_path: Path
    fingerprint_path: Path
    metadata_mode: AssignmentCheckpointMetadataMode


@dataclass(frozen=True, slots=True)
class AssignmentCheckpointNativeMetadata:
    pair_state: AssignmentCheckpointMetadataPairState
    manifest_mapping: Mapping[str, Any]
    parsed_manifest: object
    canonical_bytes: bytes
    stored_fingerprint: str
    computed_fingerprint: str


@dataclass(frozen=True, slots=True)
class AssignmentCheckpointEntryGuardResult:
    metadata_mode: AssignmentCheckpointMetadataMode
    manifest_version: str | None
    manifest_kind: str | None
    semantic_family: str | None
    requested_purpose: AssignmentCheckpointEntryPurpose
    fingerprint_verified: bool
    semantic_allowed: bool
    weight_io_authorized: bool
    fallback_mode: str | None
    decision_classification: str
    reason: str
    semantic_decision: (
        _v2.CompatibilityDecision
        | _v3.AssignmentCheckpointV3SemanticDecision
        | None
    )
    parsed_manifest: (
        _v2.AssignmentCheckpointContractManifest
        | _v3.AssignmentCheckpointContractManifestV3
        | None
    )
    stored_fingerprint: str | None


_LOWERCASE_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_entry_purpose(value: Any) -> AssignmentCheckpointEntryPurpose:
    if type(value) is not AssignmentCheckpointEntryPurpose:
        raise AssignmentCheckpointEntryGuardError(
            "purpose must be an exact AssignmentCheckpointEntryPurpose"
        )
    return value


def _as_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if not callable(to_mapping):
        raise AssignmentCheckpointEntryGuardError(
            f"{field} must be a manifest Mapping or typed manifest with to_mapping()"
        )
    mapping = to_mapping()
    if not isinstance(mapping, Mapping):
        raise AssignmentCheckpointEntryGuardError(
            f"{field}.to_mapping() must return a Mapping"
        )
    return mapping


def inspect_checkpoint_metadata_pair(
    checkpoint_directory: str | Path,
) -> AssignmentCheckpointMetadataPairState:
    """Classify the two exact native metadata filenames without reading them."""

    directory = Path(checkpoint_directory).expanduser().resolve()
    manifest_path = directory / CONTRACT_MANIFEST_FILE
    fingerprint_path = directory / CONTRACT_FINGERPRINT_FILE
    manifest_exists = manifest_path.exists()
    fingerprint_exists = fingerprint_path.exists()
    if manifest_exists and fingerprint_exists:
        mode = AssignmentCheckpointMetadataMode.BOTH_PRESENT
    elif not manifest_exists and not fingerprint_exists:
        mode = AssignmentCheckpointMetadataMode.BOTH_ABSENT
    else:
        mode = AssignmentCheckpointMetadataMode.PARTIAL
    return AssignmentCheckpointMetadataPairState(
        checkpoint_directory=directory,
        manifest_path=manifest_path,
        fingerprint_path=fingerprint_path,
        metadata_mode=mode,
    )


def read_checkpoint_native_metadata_pair(
    checkpoint_directory: str | Path,
) -> AssignmentCheckpointNativeMetadata | None:
    """Read and strictly verify a present native semantic metadata pair."""

    state = inspect_checkpoint_metadata_pair(checkpoint_directory)
    if state.metadata_mode is AssignmentCheckpointMetadataMode.PARTIAL:
        raise AssignmentCheckpointMetadataPairError(
            "native manifest and fingerprint must either both exist or both be "
            f"absent: checkpoint={state.checkpoint_directory}"
        )
    if state.metadata_mode is AssignmentCheckpointMetadataMode.BOTH_ABSENT:
        return None

    try:
        raw_manifest = state.manifest_path.read_bytes()
    except OSError as exc:
        raise AssignmentCheckpointMetadataPairError(
            f"native manifest is unreadable: {state.manifest_path}: {exc}"
        ) from exc
    try:
        decoded = raw_manifest.decode("utf-8")
        mapping = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssignmentCheckpointMetadataPairError(
            f"native manifest is not valid UTF-8 JSON: {state.manifest_path}: {exc}"
        ) from exc
    if not isinstance(mapping, Mapping):
        raise AssignmentCheckpointMetadataPairError(
            f"native manifest root must be a JSON object: {state.manifest_path}"
        )
    try:
        parsed = _dispatch.parse_assignment_checkpoint_manifest(mapping)
        canonical = _dispatch.canonical_assignment_checkpoint_manifest_bytes(mapping)
        computed = _dispatch.compute_assignment_checkpoint_manifest_sha256(mapping)
    except Exception as exc:
        raise AssignmentCheckpointMetadataPairError(
            f"native manifest semantic validation failed: {state.manifest_path}: {exc}"
        ) from exc
    if raw_manifest != canonical + b"\n":
        raise AssignmentCheckpointMetadataPairError(
            "native manifest must be exact version-canonical UTF-8 JSON plus one LF: "
            f"{state.manifest_path}"
        )

    try:
        raw_fingerprint = state.fingerprint_path.read_bytes()
    except OSError as exc:
        raise AssignmentCheckpointFingerprintError(
            f"native fingerprint is unreadable: {state.fingerprint_path}: {exc}"
        ) from exc
    if len(raw_fingerprint) != 65 or not raw_fingerprint.endswith(b"\n"):
        raise AssignmentCheckpointFingerprintError(
            "native fingerprint must be 64 lowercase SHA-256 characters plus one LF"
        )
    try:
        stored = raw_fingerprint[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise AssignmentCheckpointFingerprintError(
            "native fingerprint must contain ASCII lowercase SHA-256"
        ) from exc
    if _LOWERCASE_SHA256.fullmatch(stored) is None:
        raise AssignmentCheckpointFingerprintError(
            "native fingerprint must be exactly 64 lowercase hexadecimal characters"
        )
    if stored != computed:
        raise AssignmentCheckpointFingerprintError(
            "native fingerprint does not match the version-canonical manifest"
        )
    return AssignmentCheckpointNativeMetadata(
        pair_state=state,
        manifest_mapping=mapping,
        parsed_manifest=parsed,
        canonical_bytes=canonical,
        stored_fingerprint=stored,
        computed_fingerprint=computed,
    )


def _manifest_identity(mapping: Mapping[str, Any]) -> tuple[str, str | None, str]:
    version = mapping.get("manifest_format_version")
    if type(version) is not str:
        # Let the dispatcher produce its authoritative typed error.
        _dispatch.parse_assignment_checkpoint_manifest(mapping)
        raise AssertionError("unreachable")
    kind = mapping.get("manifest_kind")
    manifest_kind = kind if type(kind) is str else None
    if version == _dispatch.V2_MANIFEST_FORMAT_VERSION:
        return version, manifest_kind, "v2"
    if version == _dispatch.V3_MANIFEST_FORMAT_VERSION:
        return version, manifest_kind, "v3"
    _dispatch.parse_assignment_checkpoint_manifest(mapping)
    raise AssertionError("unreachable")


def _decision_fields(decision: object) -> tuple[bool, str, str]:
    allowed = getattr(decision, "allowed", None)
    if allowed is None:
        allowed = getattr(decision, "interface_semantics_valid", False)
    classification = getattr(decision, "classification", type(decision).__name__)
    reason = getattr(decision, "reason", repr(decision))
    return bool(allowed), str(classification), str(reason)


def _validate_v2_purpose_pair(
    entry_purpose: AssignmentCheckpointEntryPurpose,
    compatibility_purpose: _v2.CompatibilityPurpose,
) -> bool:
    continuation_purposes = {
        _v2.CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
        _v2.CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING,
        _v2.CompatibilityPurpose.EXACT_TRAINING_RESUME,
    }
    evaluation_purposes = {
        _v2.CompatibilityPurpose.NORMAL_EVALUATION,
        _v2.CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
    }
    valid = (
        entry_purpose is AssignmentCheckpointEntryPurpose.LOAD_CONTINUATION
        and compatibility_purpose in continuation_purposes
    ) or (
        entry_purpose is AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK
        and compatibility_purpose in evaluation_purposes
    ) or (
        entry_purpose is AssignmentCheckpointEntryPurpose.LOAD_EVALUATION
        and compatibility_purpose
        in {*evaluation_purposes, _v2.CompatibilityPurpose.STRUCTURAL_INSPECTION}
    ) or (
        entry_purpose is AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT
        and compatibility_purpose is _v2.CompatibilityPurpose.STRUCTURAL_INSPECTION
    )
    return valid


def evaluate_checkpoint_entry_guard(
    *,
    manifest_mapping: Mapping[str, Any] | object,
    stored_fingerprint: str,
    purpose: AssignmentCheckpointEntryPurpose,
    current_manifest_or_context: Mapping[str, Any] | object | None = None,
    v2_compatibility_purpose: _v2.CompatibilityPurpose | None = None,
    explicit_ablation_name: str | None = None,
    training_state_manifest: _v2.AssignmentTrainingStateManifest | Mapping[str, Any] | None = None,
    continuation_reset_acknowledged: bool = False,
) -> AssignmentCheckpointEntryGuardResult:
    """Evaluate one already-available, fingerprint-bound manifest mapping."""

    entry_purpose = _require_entry_purpose(purpose)
    mapping = _as_mapping(manifest_mapping, field="manifest_mapping")
    if type(stored_fingerprint) is not str or _LOWERCASE_SHA256.fullmatch(
        stored_fingerprint
    ) is None:
        raise AssignmentCheckpointFingerprintError(
            "stored_fingerprint must be exactly 64 lowercase hexadecimal characters"
        )
    parsed = _dispatch.parse_assignment_checkpoint_manifest(mapping)
    computed = _dispatch.compute_assignment_checkpoint_manifest_sha256(mapping)
    if stored_fingerprint != computed:
        raise AssignmentCheckpointFingerprintError(
            "stored fingerprint does not match the version-canonical manifest"
        )
    version, kind, family = _manifest_identity(mapping)

    current_mapping = (
        None
        if current_manifest_or_context is None
        else _as_mapping(current_manifest_or_context, field="current_manifest_or_context")
    )

    if family == "v2" and entry_purpose is AssignmentCheckpointEntryPurpose.SAVE:
        return AssignmentCheckpointEntryGuardResult(
            metadata_mode=AssignmentCheckpointMetadataMode.BOTH_PRESENT,
            manifest_version=version,
            manifest_kind=kind,
            semantic_family=family,
            requested_purpose=entry_purpose,
            fingerprint_verified=True,
            semantic_allowed=True,
            weight_io_authorized=True,
            fallback_mode=None,
            decision_classification="v2_save_contract_valid",
            reason=(
                "the existing V2 save coordinator may proceed after exact manifest "
                "parse and fingerprint validation"
            ),
            semantic_decision=None,
            parsed_manifest=parsed,
            stored_fingerprint=stored_fingerprint,
        )

    if family == "v3" and entry_purpose is not AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT:
        audit_decision = _dispatch.evaluate_assignment_checkpoint_semantics(
            mapping,
            purpose=_v3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        )
        return AssignmentCheckpointEntryGuardResult(
            metadata_mode=AssignmentCheckpointMetadataMode.BOTH_PRESENT,
            manifest_version=version,
            manifest_kind=kind,
            semantic_family=family,
            requested_purpose=entry_purpose,
            fingerprint_verified=True,
            semantic_allowed=False,
            weight_io_authorized=False,
            fallback_mode=None,
            decision_classification="v3_interface_weight_use_denied",
            reason=(
                "V3 interface descriptors authorize only offline interface audit; "
                f"entry purpose {entry_purpose.value!r} cannot use checkpoint weights"
            ),
            semantic_decision=audit_decision,
            parsed_manifest=parsed,
            stored_fingerprint=stored_fingerprint,
        )

    if family == "v3":
        decision = _dispatch.evaluate_assignment_checkpoint_semantics(
            mapping,
            purpose=_v3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
            current_manifest=current_mapping,
        )
        allowed, classification, reason = _decision_fields(decision)
        return AssignmentCheckpointEntryGuardResult(
            metadata_mode=AssignmentCheckpointMetadataMode.BOTH_PRESENT,
            manifest_version=version,
            manifest_kind=kind,
            semantic_family=family,
            requested_purpose=entry_purpose,
            fingerprint_verified=True,
            semantic_allowed=allowed,
            weight_io_authorized=False,
            fallback_mode=None,
            decision_classification=classification,
            reason=reason,
            semantic_decision=decision,
            parsed_manifest=parsed,
            stored_fingerprint=stored_fingerprint,
        )

    compatibility_purpose = v2_compatibility_purpose
    if entry_purpose is AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT:
        compatibility_purpose = (
            _v2.CompatibilityPurpose.STRUCTURAL_INSPECTION
            if compatibility_purpose is None
            else compatibility_purpose
        )
        current_mapping = mapping if current_mapping is None else current_mapping
    if compatibility_purpose is None:
        raise AssignmentCheckpointEntryGuardError(
            "v2_compatibility_purpose is required for V2 load entry evaluation"
        )
    if current_mapping is None:
        raise AssignmentCheckpointEntryGuardError(
            "current_manifest_or_context is required for V2 load entry evaluation"
        )
    decision = _dispatch.evaluate_assignment_checkpoint_semantics(
        mapping,
        purpose=compatibility_purpose,
        current_manifest=current_mapping,
        checkpoint_fingerprint=stored_fingerprint,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=training_state_manifest,
        continuation_reset_acknowledged=continuation_reset_acknowledged,
    )
    allowed, classification, reason = _decision_fields(decision)
    entry_pair_allowed = _validate_v2_purpose_pair(
        entry_purpose, compatibility_purpose
    )
    if not entry_pair_allowed:
        classification = "entry_v2_purpose_mismatch"
        reason = (
            f"entry purpose {entry_purpose.value!r} cannot request V2 "
            f"compatibility purpose {compatibility_purpose.value!r}; underlying "
            f"V2 decision={getattr(decision, 'classification', type(decision).__name__)!r}"
        )
    return AssignmentCheckpointEntryGuardResult(
        metadata_mode=AssignmentCheckpointMetadataMode.BOTH_PRESENT,
        manifest_version=version,
        manifest_kind=kind,
        semantic_family=family,
        requested_purpose=entry_purpose,
        fingerprint_verified=True,
        semantic_allowed=allowed and entry_pair_allowed,
        weight_io_authorized=(
            allowed
            and entry_pair_allowed
            and entry_purpose is not AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT
        ),
        fallback_mode=None,
        decision_classification=classification,
        reason=reason,
        semantic_decision=decision,
        parsed_manifest=parsed,
        stored_fingerprint=stored_fingerprint,
    )


def read_and_evaluate_checkpoint_entry_guard(
    *,
    checkpoint_directory: str | Path,
    purpose: AssignmentCheckpointEntryPurpose,
    current_manifest_or_context: Mapping[str, Any] | object | None = None,
    v2_compatibility_purpose: _v2.CompatibilityPurpose | None = None,
    explicit_ablation_name: str | None = None,
    training_state_manifest: _v2.AssignmentTrainingStateManifest | Mapping[str, Any] | None = None,
    continuation_reset_acknowledged: bool = False,
) -> AssignmentCheckpointEntryGuardResult:
    """Read a native pair, then route its semantics through the dispatcher."""

    entry_purpose = _require_entry_purpose(purpose)
    native = read_checkpoint_native_metadata_pair(checkpoint_directory)
    if native is None:
        return AssignmentCheckpointEntryGuardResult(
            metadata_mode=AssignmentCheckpointMetadataMode.BOTH_ABSENT,
            manifest_version=None,
            manifest_kind=None,
            semantic_family=None,
            requested_purpose=entry_purpose,
            fingerprint_verified=False,
            semantic_allowed=False,
            weight_io_authorized=False,
            fallback_mode="legacy_v2_metadata_absence_fallback",
            decision_classification="native_metadata_absent",
            reason=(
                "native semantic metadata is absent; only the unchanged explicit "
                "V2 legacy fallback boundary may decide whether to continue"
            ),
            semantic_decision=None,
            parsed_manifest=None,
            stored_fingerprint=None,
        )
    return evaluate_checkpoint_entry_guard(
        manifest_mapping=native.manifest_mapping,
        stored_fingerprint=native.stored_fingerprint,
        purpose=entry_purpose,
        current_manifest_or_context=current_manifest_or_context,
        v2_compatibility_purpose=v2_compatibility_purpose,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=training_state_manifest,
        continuation_reset_acknowledged=continuation_reset_acknowledged,
    )


def evaluate_checkpoint_save_entry_guard(
    manifest: Mapping[str, Any] | object,
) -> AssignmentCheckpointEntryGuardResult:
    """Validate an in-memory save manifest before any checkpoint artifact write."""

    mapping = _as_mapping(manifest, field="manifest")
    fingerprint = _dispatch.compute_assignment_checkpoint_manifest_sha256(mapping)
    return evaluate_checkpoint_entry_guard(
        manifest_mapping=mapping,
        stored_fingerprint=fingerprint,
        purpose=AssignmentCheckpointEntryPurpose.SAVE,
    )


def require_checkpoint_weight_io_authorized(
    result: AssignmentCheckpointEntryGuardResult,
) -> AssignmentCheckpointEntryGuardResult:
    """Fail closed unless an existing V2 decision authorizes weight I/O."""

    if type(result) is not AssignmentCheckpointEntryGuardResult:
        raise AssignmentCheckpointEntryGuardError(
            "result must be an exact AssignmentCheckpointEntryGuardResult"
        )
    if not result.semantic_allowed or not result.weight_io_authorized:
        raise AssignmentCheckpointEntryPurposeDeniedError(result)
    return result


__all__ = [
    "CONTRACT_FINGERPRINT_FILE",
    "CONTRACT_MANIFEST_FILE",
    "AssignmentCheckpointEntryGuardError",
    "AssignmentCheckpointEntryGuardResult",
    "AssignmentCheckpointEntryPurpose",
    "AssignmentCheckpointEntryPurposeDeniedError",
    "AssignmentCheckpointFingerprintError",
    "AssignmentCheckpointMetadataMode",
    "AssignmentCheckpointMetadataPairError",
    "AssignmentCheckpointMetadataPairState",
    "AssignmentCheckpointNativeMetadata",
    "evaluate_checkpoint_entry_guard",
    "evaluate_checkpoint_save_entry_guard",
    "inspect_checkpoint_metadata_pair",
    "read_and_evaluate_checkpoint_entry_guard",
    "read_checkpoint_native_metadata_pair",
    "require_checkpoint_weight_io_authorized",
]
