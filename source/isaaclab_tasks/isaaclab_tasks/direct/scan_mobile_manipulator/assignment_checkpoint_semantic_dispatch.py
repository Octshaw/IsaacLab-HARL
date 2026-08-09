"""Pure version dispatch for assignment checkpoint semantic manifests.

The facade consumes manifests that are already available as mappings.  It does
not discover metadata, access checkpoint files, inspect tensors, or invoke any
runtime, model, training, playback, or evaluation entry point.
"""

from __future__ import annotations


if __name__ != (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_semantic_dispatch"
):
    raise ImportError(
        "CanonicalModuleIdentityError: assignment checkpoint semantic "
        "dispatcher must fail before declaring identity-bearing types or "
        "importing dependencies; expected module key="
        "'isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_checkpoint_semantic_dispatch'; actual module key="
        f"{__name__!r}"
    )


from collections.abc import Mapping
from typing import Any

from . import assignment_checkpoint_contract as _v2
from . import assignment_checkpoint_contract_v3 as _v3
from .assignment_checkpoint_contract_v3 import (
    CheckpointManifestFamilyMismatchError,
    CheckpointManifestInputError,
    UnsupportedCheckpointManifestVersionError,
)


CANONICAL_ASSIGNMENT_CHECKPOINT_SEMANTIC_DISPATCH_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_semantic_dispatch"
)
V2_MANIFEST_FORMAT_VERSION = _v2.MANIFEST_FORMAT_VERSION
V3_MANIFEST_FORMAT_VERSION = _v3.MANIFEST_FORMAT_VERSION
SUPPORTED_MANIFEST_FORMAT_VERSIONS = (
    V2_MANIFEST_FORMAT_VERSION,
    V3_MANIFEST_FORMAT_VERSION,
)


def _require_manifest_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CheckpointManifestInputError(
            f"{field} must be an already available manifest Mapping; "
            f"received {type(value).__name__}"
        )
    return value


def _manifest_format_version(
    value: Any,
    *,
    field: str,
) -> tuple[Mapping[str, Any], str]:
    mapping = _require_manifest_mapping(value, field=field)
    if "manifest_format_version" not in mapping:
        raise UnsupportedCheckpointManifestVersionError(
            f"{field}.manifest_format_version is required; metadata-free "
            "fallback is outside the semantic dispatcher"
        )
    version = mapping["manifest_format_version"]
    if not isinstance(version, str) or version not in SUPPORTED_MANIFEST_FORMAT_VERSIONS:
        raise UnsupportedCheckpointManifestVersionError(
            f"unsupported {field}.manifest_format_version: {version!r}; "
            f"supported versions are {SUPPORTED_MANIFEST_FORMAT_VERSIONS!r}"
        )
    return mapping, version


def _parse_with_version(
    mapping: Mapping[str, Any],
    version: str,
) -> _v2.AssignmentCheckpointContractManifest | _v3.AssignmentCheckpointContractManifestV3:
    if version == V2_MANIFEST_FORMAT_VERSION:
        return _v2.AssignmentCheckpointContractManifest.from_mapping(mapping)
    return _v3.AssignmentCheckpointContractManifestV3.from_mapping(mapping)


def parse_assignment_checkpoint_manifest(
    manifest: Mapping[str, Any],
) -> _v2.AssignmentCheckpointContractManifest | _v3.AssignmentCheckpointContractManifestV3:
    """Parse one present manifest through its exact canonical version API."""

    mapping, version = _manifest_format_version(manifest, field="manifest")
    return _parse_with_version(mapping, version)


def canonical_assignment_checkpoint_manifest_bytes(
    manifest: Mapping[str, Any],
) -> bytes:
    """Return canonical bytes without normalizing across manifest families."""

    mapping, version = _manifest_format_version(manifest, field="manifest")
    if version == V2_MANIFEST_FORMAT_VERSION:
        return _v2.canonical_manifest_bytes(mapping)
    return _v3.canonical_assignment_checkpoint_manifest_v3_bytes(mapping)


def compute_assignment_checkpoint_manifest_sha256(
    manifest: Mapping[str, Any],
) -> str:
    """Return the version-native semantic fingerprint for one mapping."""

    mapping, version = _manifest_format_version(manifest, field="manifest")
    if version == V2_MANIFEST_FORMAT_VERSION:
        return _v2.compute_manifest_sha256(mapping)
    return _v3.compute_assignment_checkpoint_manifest_v3_sha256(mapping)


def _parse_v2_training_state(
    value: _v2.AssignmentTrainingStateManifest | Mapping[str, Any] | None,
) -> _v2.AssignmentTrainingStateManifest | None:
    if value is None or isinstance(value, _v2.AssignmentTrainingStateManifest):
        return value
    if isinstance(value, Mapping):
        return _v2.AssignmentTrainingStateManifest.from_mapping(value)
    raise CheckpointManifestInputError(
        "training_state_manifest must be a V2 AssignmentTrainingStateManifest, "
        "a mapping accepted by its direct parser, or None"
    )


def evaluate_assignment_checkpoint_semantics(
    checkpoint_manifest: Mapping[str, Any],
    *,
    purpose: _v2.CompatibilityPurpose | _v3.AssignmentCheckpointV3Purpose,
    current_manifest: Mapping[str, Any] | None = None,
    checkpoint_fingerprint: str | None = None,
    explicit_ablation_name: str | None = None,
    training_state_manifest: (
        _v2.AssignmentTrainingStateManifest | Mapping[str, Any] | None
    ) = None,
    continuation_reset_acknowledged: bool = False,
) -> _v2.CompatibilityDecision | _v3.AssignmentCheckpointV3SemanticDecision:
    """Evaluate semantics through the native V2 or V3 contract API.

    V2 evaluation requires a current-manifest mapping and is delegated to the
    unchanged V2 ``evaluate_compatibility`` function.  V3 evaluation is the
    Phase-A interface audit only.  If both checkpoint and current mappings are
    supplied, their manifest families are compared before either family can
    perform any shape or semantic compatibility check.
    """

    checkpoint_mapping, checkpoint_version = _manifest_format_version(
        checkpoint_manifest,
        field="checkpoint_manifest",
    )

    current_mapping: Mapping[str, Any] | None = None
    current_version: str | None = None
    if current_manifest is not None:
        current_mapping, current_version = _manifest_format_version(
            current_manifest,
            field="current_manifest",
        )
        if current_version != checkpoint_version:
            raise CheckpointManifestFamilyMismatchError(
                "checkpoint/current semantic families differ: "
                f"checkpoint={checkpoint_version!r}, current={current_version!r}; "
                "equal tensor or observation shapes cannot bridge manifest families"
            )

    if checkpoint_version == V2_MANIFEST_FORMAT_VERSION:
        if current_mapping is None:
            raise CheckpointManifestInputError(
                "current_manifest Mapping is required for V2 compatibility evaluation"
            )
        checkpoint_v2 = _v2.AssignmentCheckpointContractManifest.from_mapping(
            checkpoint_mapping
        )
        current_v2 = _v2.AssignmentCheckpointContractManifest.from_mapping(
            current_mapping
        )
        request = _v2.CompatibilityRequest(
            purpose=purpose,
            current_manifest=current_v2,
            checkpoint_manifest=checkpoint_v2,
            checkpoint_fingerprint=checkpoint_fingerprint,
            explicit_ablation_name=explicit_ablation_name,
            training_state_manifest=_parse_v2_training_state(training_state_manifest),
            continuation_reset_acknowledged=continuation_reset_acknowledged,
        )
        return _v2.evaluate_compatibility(request)

    if (
        checkpoint_fingerprint is not None
        or explicit_ablation_name is not None
        or training_state_manifest is not None
        or continuation_reset_acknowledged
    ):
        raise CheckpointManifestInputError(
            "V2 fingerprint, ablation, training-state, and continuation "
            "arguments are not valid for a V3 interface audit"
        )

    checkpoint_v3 = _v3.AssignmentCheckpointContractManifestV3.from_mapping(
        checkpoint_mapping
    )
    current_v3 = (
        None
        if current_mapping is None
        else _v3.AssignmentCheckpointContractManifestV3.from_mapping(current_mapping)
    )
    return _v3.evaluate_assignment_checkpoint_manifest_v3_semantics(
        checkpoint_v3,
        current_manifest=current_v3,
        purpose=purpose,
    )


__all__ = [
    "CANONICAL_ASSIGNMENT_CHECKPOINT_SEMANTIC_DISPATCH_MODULE",
    "SUPPORTED_MANIFEST_FORMAT_VERSIONS",
    "V2_MANIFEST_FORMAT_VERSION",
    "V3_MANIFEST_FORMAT_VERSION",
    "canonical_assignment_checkpoint_manifest_bytes",
    "compute_assignment_checkpoint_manifest_sha256",
    "evaluate_assignment_checkpoint_semantics",
    "parse_assignment_checkpoint_manifest",
]
