# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Shared three-stage assignment checkpoint validation and strict loading."""

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

try:
    from .assignment_checkpoint_contract import (
        NAMED_LIFECYCLE_ABLATION,
        ArtifactFileInventoryEntry,
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        CompatibilityDecision,
        CompatibilityPurpose,
        CompatibilityRequest,
        VALIDATED_WEIGHT_CONTINUATION_CANDIDATE,
        canonical_manifest_bytes,
        compare_state_dict_inventories,
        compute_manifest_sha256,
        compute_tensor_inventory_sha256,
        decide_missing_metadata,
        evaluate_compatibility,
        verify_manifest_sha256,
    )
    from .assignment_checkpoint_save import (
        CONTRACT_FINGERPRINT_FILE,
        CONTRACT_MANIFEST_FILE,
        TRAINING_STATE_MANIFEST_FILE,
        AssignmentCheckpointRuntimeState,
        build_assignment_checkpoint_contract_manifest,
        build_tensor_inventory_from_state_dict,
        compute_file_sha256,
    )
    from .assignment_lifecycle_training_contract import (
        resolve_installed_harl_actor_buffer_generator,
    )
    from .assignment_value_normalizer_checkpoint import (
        build_value_normalizer_contract,
        export_value_normalizer_checkpoint_state,
        inspect_value_normalizer_target,
        restore_value_normalizer_checkpoint_state,
        validate_value_normalizer_checkpoint_state,
        validate_value_normalizer_target_contract,
    )
except ImportError:  # Allows direct lightweight tests with this directory on sys.path.
    from assignment_checkpoint_contract import (  # type: ignore
        NAMED_LIFECYCLE_ABLATION,
        ArtifactFileInventoryEntry,
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        CompatibilityDecision,
        CompatibilityPurpose,
        CompatibilityRequest,
        VALIDATED_WEIGHT_CONTINUATION_CANDIDATE,
        canonical_manifest_bytes,
        compare_state_dict_inventories,
        compute_manifest_sha256,
        compute_tensor_inventory_sha256,
        decide_missing_metadata,
        evaluate_compatibility,
        verify_manifest_sha256,
    )
    from assignment_checkpoint_save import (  # type: ignore
        CONTRACT_FINGERPRINT_FILE,
        CONTRACT_MANIFEST_FILE,
        TRAINING_STATE_MANIFEST_FILE,
        AssignmentCheckpointRuntimeState,
        build_assignment_checkpoint_contract_manifest,
        build_tensor_inventory_from_state_dict,
        compute_file_sha256,
    )
    from assignment_lifecycle_training_contract import (  # type: ignore
        resolve_installed_harl_actor_buffer_generator,
    )
    from assignment_value_normalizer_checkpoint import (  # type: ignore
        build_value_normalizer_contract,
        export_value_normalizer_checkpoint_state,
        inspect_value_normalizer_target,
        restore_value_normalizer_checkpoint_state,
        validate_value_normalizer_checkpoint_state,
        validate_value_normalizer_target_contract,
    )


_EPISODE_DIRECTORY = re.compile(r"^episode_(\d+)$")


class AssignmentCheckpointError(RuntimeError):
    """Base error for project-owned assignment checkpoint loading."""


class AssignmentCheckpointMetadataError(AssignmentCheckpointError):
    """Checkpoint metadata is absent, malformed, partial, or inconsistent."""


class AssignmentCheckpointIntegrityError(AssignmentCheckpointError):
    """A fingerprint, file size, or file digest check failed."""


class AssignmentCheckpointCompatibilityError(AssignmentCheckpointError):
    """The checkpoint contract is incompatible with the requested purpose."""


class AssignmentCheckpointInventoryError(AssignmentCheckpointError):
    """A serialized state-dict inventory does not match its declared/live shape."""


class AssignmentCheckpointLoadError(AssignmentCheckpointError):
    """Strict live-model mutation failed after successful inspection."""


@dataclass(frozen=True)
class AssignmentCheckpointLoadResult:
    checkpoint_directory: Path
    load_purpose: CompatibilityPurpose
    checkpoint_kind: str
    checkpoint_generation: int | None
    contract_fingerprint: str | None
    compatibility_decision: CompatibilityDecision
    loaded_actor_identities: tuple[str, ...]
    critic_loaded: bool
    value_normalizer_loaded: bool
    legacy_fallback_used: bool
    named_ablation_used: str | None
    continuation_acknowledgement: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _NativeCheckpoint:
    directory: Path
    manifest: AssignmentCheckpointContractManifest
    fingerprint: str
    training_state: AssignmentTrainingStateManifest


@dataclass(frozen=True)
class _InspectedArtifact:
    entry: ArtifactFileInventoryEntry
    state_dict: Mapping[str, torch.Tensor]
    target_module: Any | None
    is_value_normalizer: bool


def _context(directory: Path, purpose: CompatibilityPurpose, message: str) -> str:
    return f"checkpoint={directory} purpose={purpose.value}: {message}"


def _read_contract_pair(
    directory: Path,
    *,
    purpose: CompatibilityPurpose,
    required: bool,
) -> tuple[AssignmentCheckpointContractManifest, str] | None:
    manifest_path = directory / CONTRACT_MANIFEST_FILE
    fingerprint_path = directory / CONTRACT_FINGERPRINT_FILE
    manifest_exists = manifest_path.exists()
    fingerprint_exists = fingerprint_path.exists()
    if manifest_exists != fingerprint_exists:
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, "manifest and fingerprint must either both exist or both be absent")
        )
    if not manifest_exists:
        if required:
            raise AssignmentCheckpointMetadataError(
                _context(directory, purpose, "native contract manifest/fingerprint pair is required")
            )
        return None
    try:
        raw_manifest = manifest_path.read_bytes()
        mapping = json.loads(raw_manifest.decode("utf-8"))
        manifest = AssignmentCheckpointContractManifest.from_mapping(mapping)
    except Exception as exc:
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, f"invalid contract manifest: {exc}")
        ) from exc
    expected_manifest = canonical_manifest_bytes(manifest) + b"\n"
    if raw_manifest != expected_manifest:
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, "contract manifest is not canonical UTF-8 JSON plus LF")
        )
    try:
        raw_fingerprint = fingerprint_path.read_bytes()
        fingerprint = raw_fingerprint.decode("ascii").removesuffix("\n")
    except (UnicodeDecodeError, OSError) as exc:
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, f"invalid fingerprint file: {exc}")
        ) from exc
    if raw_fingerprint != fingerprint.encode("ascii") + b"\n":
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, "fingerprint must be lowercase SHA-256 plus one LF")
        )
    try:
        valid = verify_manifest_sha256(manifest, fingerprint)
    except Exception as exc:
        raise AssignmentCheckpointIntegrityError(
            _context(directory, purpose, f"invalid contract fingerprint: {exc}")
        ) from exc
    if not valid:
        raise AssignmentCheckpointIntegrityError(
            _context(directory, purpose, "contract fingerprint does not match canonical manifest")
        )
    return manifest, fingerprint


def _recognized_run_root(checkpoint_directory: Path) -> Path | None:
    directory = checkpoint_directory.resolve()
    if directory.name in {"models", "best_model"}:
        return directory.parent
    if (
        _EPISODE_DIRECTORY.fullmatch(directory.name)
        and directory.parent.name == "checkpoints"
        and directory.parent.parent.name == "models"
    ):
        return directory.parent.parent.parent
    return None


def _read_native_checkpoint(
    checkpoint_directory: Path,
    purpose: CompatibilityPurpose,
) -> _NativeCheckpoint | None:
    directory = checkpoint_directory.resolve()
    local_pair = _read_contract_pair(directory, purpose=purpose, required=False)
    marker_path = directory / TRAINING_STATE_MANIFEST_FILE
    if local_pair is None:
        if marker_path.exists():
            raise AssignmentCheckpointMetadataError(
                _context(directory, purpose, "completion marker exists without a native contract pair")
            )
        return None
    if not marker_path.exists():
        raise AssignmentCheckpointMetadataError(
            _context(
                directory,
                purpose,
                f"native checkpoint is incomplete: missing {TRAINING_STATE_MANIFEST_FILE}",
            )
        )
    manifest, fingerprint = local_pair
    try:
        marker_mapping = json.loads(marker_path.read_text(encoding="utf-8"))
        training_state = AssignmentTrainingStateManifest.from_mapping(marker_mapping)
    except Exception as exc:
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, f"invalid training-state completion marker: {exc}")
        ) from exc
    if training_state.contract_fingerprint != fingerprint:
        raise AssignmentCheckpointIntegrityError(
            _context(
                directory,
                purpose,
                "training-state contract fingerprint does not match checkpoint contract fingerprint",
            )
        )

    run_root = _recognized_run_root(directory)
    if run_root is not None:
        root_pair = _read_contract_pair(run_root, purpose=purpose, required=False)
        if root_pair is not None:
            root_manifest, root_fingerprint = root_pair
            if (
                canonical_manifest_bytes(root_manifest) != canonical_manifest_bytes(manifest)
                or root_fingerprint != fingerprint
            ):
                raise AssignmentCheckpointIntegrityError(
                    _context(directory, purpose, "checkpoint-local and recognized run-root contracts disagree")
                )
    return _NativeCheckpoint(directory, manifest, fingerprint, training_state)


def _validate_native_artifact_layout(checkpoint: _NativeCheckpoint) -> tuple[ArtifactFileInventoryEntry, ...]:
    directory = checkpoint.directory
    manifest = checkpoint.manifest
    state = checkpoint.training_state
    expected_names = tuple(manifest.scale["ordered_agent_names"])
    if state.ordered_actor_identities != expected_names:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: completion actor identities/order {state.ordered_actor_identities} "
            f"do not match contract {expected_names}"
        )
    expected_actor_files = tuple(f"actor_agent_{name}.pt" for name in expected_names)
    actual_actor_files = tuple(entry.relative_file_name for entry in state.actor_artifacts)
    if actual_actor_files != expected_actor_files:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: canonical actor files expected={expected_actor_files} actual={actual_actor_files}"
        )
    if state.critic_artifact is None:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: completed native checkpoint must declare critic_agent.pt"
        )
    if state.critic_artifact.relative_file_name != "critic_agent.pt":
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: critic artifact must be critic_agent.pt"
        )
    value_enabled = bool(manifest.training_contract["value_norm_enabled"])
    if value_enabled != (state.value_normalizer_artifact is not None):
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: ValueNorm completion inventory disagrees with contract"
        )
    if (
        state.value_normalizer_artifact is not None
        and state.value_normalizer_artifact.relative_file_name != "value_normalizer.pt"
    ):
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: ValueNorm artifact must be value_normalizer.pt"
        )

    full_files = sorted(path.name for path in directory.glob("*_full.pt"))
    if full_files:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: full-model pickle artifacts are forbidden: {full_files}"
        )
    declared_actor_files = set(expected_actor_files)
    actual_actor_candidates = {path.name for path in directory.glob("actor_agent_*.pt")}
    unexpected_actor = sorted(actual_actor_candidates - declared_actor_files)
    if unexpected_actor:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: unexpected/numeric actor files: {unexpected_actor}"
        )
    unexpected_critic = sorted(
        path.name for path in directory.glob("critic_agent*.pt") if path.name != "critic_agent.pt"
    )
    unexpected_value = sorted(
        path.name
        for path in directory.glob("value_normalizer*.pt")
        if path.name != "value_normalizer.pt"
    )
    if not value_enabled and (directory / "value_normalizer.pt").exists():
        unexpected_value.append("value_normalizer.pt")
    if unexpected_critic or unexpected_value:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: unexpected critic={unexpected_critic} ValueNorm={unexpected_value}"
        )
    return tuple(
        (
            *state.actor_artifacts,
            state.critic_artifact,
            state.value_normalizer_artifact,
        )
    )


def _artifact_path(directory: Path, entry: ArtifactFileInventoryEntry) -> Path:
    path = (directory / entry.relative_file_name).resolve()
    try:
        path.relative_to(directory)
    except ValueError as exc:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: artifact path escapes checkpoint: {entry.relative_file_name}"
        ) from exc
    return path


def _verify_all_declared_files(checkpoint: _NativeCheckpoint) -> tuple[ArtifactFileInventoryEntry, ...]:
    entries = tuple(entry for entry in _validate_native_artifact_layout(checkpoint) if entry is not None)
    for entry in entries:
        path = _artifact_path(checkpoint.directory, entry)
        if not path.exists() or not path.is_file():
            raise AssignmentCheckpointIntegrityError(
                f"checkpoint={checkpoint.directory}: missing/non-regular {entry.artifact_role} file {path.name}"
            )
        actual_size, actual_digest = compute_file_sha256(path)
        if actual_size != entry.file_size:
            raise AssignmentCheckpointIntegrityError(
                f"checkpoint={checkpoint.directory}: artifact={path.name} size "
                f"expected={entry.file_size} actual={actual_size}"
            )
        if actual_digest != entry.file_sha256:
            raise AssignmentCheckpointIntegrityError(
                f"checkpoint={checkpoint.directory}: artifact={path.name} SHA-256 "
                f"expected={entry.file_sha256} actual={actual_digest}"
            )
    return entries


def _load_and_inspect_artifact(
    checkpoint: _NativeCheckpoint,
    entry: ArtifactFileInventoryEntry,
    target_module: Any | None,
) -> _InspectedArtifact:
    path = _artifact_path(checkpoint.directory, entry)
    try:
        state_dict = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise AssignmentCheckpointInventoryError(
            f"checkpoint={checkpoint.directory}: weights_only CPU deserialization failed for {path.name}: {exc}"
        ) from exc
    if not isinstance(state_dict, Mapping):
        raise AssignmentCheckpointInventoryError(
            f"checkpoint={checkpoint.directory}: {path.name} did not deserialize to a state-dict mapping"
        )
    try:
        actual_inventory = build_tensor_inventory_from_state_dict(
            state_dict,
            artifact_name=path.name,
        )
    except Exception as exc:
        raise AssignmentCheckpointInventoryError(
            f"checkpoint={checkpoint.directory}: invalid tensor inventory for {path.name}: {exc}"
        ) from exc
    declared_decision = compare_state_dict_inventories(entry.tensor_inventory, actual_inventory)
    if not declared_decision.allowed:
        mismatch = declared_decision.first_mismatch
        raise AssignmentCheckpointInventoryError(
            f"checkpoint={checkpoint.directory}: artifact={path.name} declared inventory mismatch "
            f"field={None if mismatch is None else mismatch.field_path} "
            f"expected={None if mismatch is None else mismatch.expected_value} "
            f"actual={None if mismatch is None else mismatch.actual_value}"
        )
    actual_digest = compute_tensor_inventory_sha256(actual_inventory)
    if actual_digest != entry.tensor_inventory_sha256:
        raise AssignmentCheckpointInventoryError(
            f"checkpoint={checkpoint.directory}: artifact={path.name} tensor inventory digest "
            f"expected={entry.tensor_inventory_sha256} actual={actual_digest}"
        )
    is_value_normalizer = entry.artifact_role == "value_normalizer"
    if is_value_normalizer:
        try:
            validate_value_normalizer_checkpoint_state(
                state_dict,
                value_normalizer_contract=checkpoint.manifest.training_contract["value_normalizer_contract"],
            )
        except Exception as exc:
            raise AssignmentCheckpointInventoryError(
                f"checkpoint={checkpoint.directory}: invalid ValueNorm mapping for {path.name}: {exc}"
            ) from exc
        if target_module is not None:
            try:
                target_inventory = inspect_value_normalizer_target(target_module)
                validate_value_normalizer_target_contract(
                    target_inventory,
                    checkpoint.manifest.training_contract["value_normalizer_contract"],
                )
                validate_value_normalizer_checkpoint_state(
                    state_dict,
                    target_inventory=target_inventory,
                )
            except Exception as exc:
                raise AssignmentCheckpointInventoryError(
                    f"checkpoint={checkpoint.directory}: incompatible live ValueNorm target for {path.name}: {exc}"
                ) from exc
    elif target_module is not None:
        try:
            live_inventory = build_tensor_inventory_from_state_dict(
                target_module.state_dict(),
                artifact_name=f"live target for {path.name}",
            )
        except Exception as exc:
            raise AssignmentCheckpointInventoryError(
                f"checkpoint={checkpoint.directory}: cannot inventory live target for {path.name}: {exc}"
            ) from exc
        live_decision = compare_state_dict_inventories(live_inventory, actual_inventory)
        if not live_decision.allowed:
            mismatch = live_decision.first_mismatch
            raise AssignmentCheckpointInventoryError(
                f"checkpoint={checkpoint.directory}: artifact={path.name} live inventory mismatch "
                f"field={None if mismatch is None else mismatch.field_path} "
                f"expected={None if mismatch is None else mismatch.expected_value} "
                f"actual={None if mismatch is None else mismatch.actual_value}"
            )
    return _InspectedArtifact(
        entry=entry,
        state_dict=state_dict,
        target_module=target_module,
        is_value_normalizer=is_value_normalizer,
    )


def _clone_module_state(module: Any) -> dict[str, torch.Tensor]:
    return {key: value.detach().clone() for key, value in module.state_dict().items()}


def _strict_mutate_all(
    inspected: Sequence[_InspectedArtifact],
    *,
    directory: Path,
    purpose: CompatibilityPurpose,
) -> None:
    targets = tuple(item for item in inspected if item.target_module is not None)
    backups: dict[int, Mapping[str, torch.Tensor]] = {}
    try:
        for item in targets:
            if item.is_value_normalizer:
                backups[id(item.target_module)] = export_value_normalizer_checkpoint_state(item.target_module)
            else:
                backups[id(item.target_module)] = _clone_module_state(item.target_module)
    except Exception as exc:
        raise AssignmentCheckpointLoadError(
            _context(directory, purpose, f"cannot snapshot live target before mutation: {exc}")
        ) from exc
    current_item: _InspectedArtifact | None = None
    try:
        for item in targets:
            current_item = item
            if item.is_value_normalizer:
                restore_value_normalizer_checkpoint_state(item.target_module, item.state_dict, strict=True)
            else:
                item.target_module.load_state_dict(item.state_dict, strict=True)
    except Exception as exc:
        rollback_errors: list[str] = []
        for item in targets:
            try:
                if item.is_value_normalizer:
                    restore_value_normalizer_checkpoint_state(
                        item.target_module,
                        backups[id(item.target_module)],
                        strict=True,
                    )
                else:
                    item.target_module.load_state_dict(
                        backups[id(item.target_module)],
                        strict=True,
                    )
            except Exception as rollback_exc:
                rollback_errors.append(
                    f"{item.entry.relative_file_name}: {rollback_exc}"
                )
        raise AssignmentCheckpointLoadError(
            _context(
                directory,
                purpose,
                f"strict live load failed for "
                f"{None if current_item is None else current_item.entry.relative_file_name}: {exc}; "
                f"rollback_errors={rollback_errors}",
            )
        ) from exc


def _module_map(
    actor_modules: Sequence[tuple[str, Any]],
    critic_module: Any | None,
    value_normalizer_module: Any | None,
) -> tuple[dict[str, Any], Any | None, Any | None]:
    actor_map: dict[str, Any] = {}
    for identity, module in actor_modules:
        identity = str(identity)
        if identity in actor_map:
            raise AssignmentCheckpointMetadataError(f"duplicate live actor identity {identity!r}")
        actor_map[identity] = module
    return actor_map, critic_module, value_normalizer_module


def _native_load(
    checkpoint: _NativeCheckpoint,
    *,
    purpose: CompatibilityPurpose,
    current_manifest: AssignmentCheckpointContractManifest,
    actor_modules: Sequence[tuple[str, Any]],
    critic_module: Any | None,
    value_normalizer_module: Any | None,
    explicit_ablation_name: str | None,
    continuation_reset_acknowledged: bool,
) -> AssignmentCheckpointLoadResult:
    request = CompatibilityRequest(
        purpose=purpose,
        current_manifest=current_manifest,
        checkpoint_manifest=checkpoint.manifest,
        checkpoint_fingerprint=checkpoint.fingerprint,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=checkpoint.training_state,
        continuation_reset_acknowledged=continuation_reset_acknowledged,
    )
    decision = evaluate_compatibility(request)
    if not decision.allowed:
        mismatch = decision.first_mismatch
        raise AssignmentCheckpointCompatibilityError(
            _context(
                checkpoint.directory,
                purpose,
                f"classification={decision.classification} reason={decision.reason} "
                f"field={None if mismatch is None else mismatch.field_path} "
                f"expected={None if mismatch is None else mismatch.expected_value} "
                f"actual={None if mismatch is None else mismatch.actual_value}",
            )
        )
    if (
        purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION
        and checkpoint.training_state.continuation_classification
        != VALIDATED_WEIGHT_CONTINUATION_CANDIDATE
    ):
        raise AssignmentCheckpointCompatibilityError(
            _context(
                checkpoint.directory,
                purpose,
                "completion marker is not classified as validated_weight_continuation_candidate",
            )
        )

    entries = _verify_all_declared_files(checkpoint)
    actor_map, critic_target, value_target = _module_map(
        actor_modules,
        critic_module,
        value_normalizer_module,
    )
    expected_names = tuple(checkpoint.manifest.scale["ordered_agent_names"])
    if tuple(actor_map) != expected_names:
        raise AssignmentCheckpointCompatibilityError(
            _context(
                checkpoint.directory,
                purpose,
                f"live actor order expected={expected_names} actual={tuple(actor_map)}",
            )
        )

    entry_by_role: dict[tuple[str, str | None], ArtifactFileInventoryEntry] = {}
    for entry in entries:
        entry_by_role[(entry.artifact_role, entry.actor_identity)] = entry
    required: list[tuple[ArtifactFileInventoryEntry, Any | None]] = []
    for identity in expected_names:
        required.append((entry_by_role[("actor", identity)], actor_map[identity]))
    if purpose in {
        CompatibilityPurpose.STRUCTURAL_INSPECTION,
        CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
    }:
        critic_entry = checkpoint.training_state.critic_artifact
        if critic_entry is None:
            raise AssignmentCheckpointMetadataError(
                _context(checkpoint.directory, purpose, "critic artifact is required")
            )
        if purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION and critic_target is None:
            raise AssignmentCheckpointCompatibilityError(
                _context(checkpoint.directory, purpose, "live critic module is required")
            )
        required.append((critic_entry, critic_target))
        value_entry = checkpoint.training_state.value_normalizer_artifact
        if value_entry is not None:
            if purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION and value_target is None:
                raise AssignmentCheckpointCompatibilityError(
                    _context(checkpoint.directory, purpose, "live ValueNorm module is required")
                )
            required.append((value_entry, value_target))
        elif purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION and value_target is not None:
            raise AssignmentCheckpointCompatibilityError(
                _context(checkpoint.directory, purpose, "live ValueNorm exists but contract disables it")
            )

    inspected = tuple(
        _load_and_inspect_artifact(checkpoint, entry, target)
        for entry, target in required
    )
    if purpose != CompatibilityPurpose.STRUCTURAL_INSPECTION:
        _strict_mutate_all(inspected, directory=checkpoint.directory, purpose=purpose)

    loaded_names = expected_names if purpose != CompatibilityPurpose.STRUCTURAL_INSPECTION else ()
    critic_loaded = (
        purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION and critic_target is not None
    )
    value_loaded = (
        purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION and value_target is not None
    )
    return AssignmentCheckpointLoadResult(
        checkpoint_directory=checkpoint.directory,
        load_purpose=purpose,
        checkpoint_kind=checkpoint.training_state.checkpoint_kind,
        checkpoint_generation=checkpoint.training_state.checkpoint_generation,
        contract_fingerprint=checkpoint.fingerprint,
        compatibility_decision=decision,
        loaded_actor_identities=loaded_names,
        critic_loaded=critic_loaded,
        value_normalizer_loaded=value_loaded,
        legacy_fallback_used=False,
        named_ablation_used=(
            explicit_ablation_name
            if purpose == CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION
            else None
        ),
        continuation_acknowledgement=decision.required_acknowledgement,
        warnings=(),
    )


def _legacy_actor_paths(
    directory: Path,
    identities: tuple[str, ...],
) -> tuple[Path, ...]:
    full_files = sorted(path.name for path in directory.glob("*_full.pt"))
    if full_files:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: full-model legacy pickle files are forbidden: {full_files}"
        )
    selected: list[Path] = []
    for index, identity in enumerate(identities):
        candidates = (
            directory / f"actor_agent_{identity}.pt",
            directory / f"actor_agent_{index}.pt",
        )
        existing = tuple(path for path in candidates if path.exists())
        if len(existing) != 1:
            raise AssignmentCheckpointMetadataError(
                f"checkpoint={directory}: legacy actor {identity} requires exactly one canonical/numeric "
                f"candidate, found={[path.name for path in existing]}"
            )
        selected.append(existing[0])
    expected = {path.name for path in selected}
    unexpected = sorted(path.name for path in directory.glob("actor_agent_*.pt") if path.name not in expected)
    if unexpected:
        raise AssignmentCheckpointMetadataError(
            f"checkpoint={directory}: unexpected legacy actor files {unexpected}"
        )
    return tuple(selected)


def _legacy_load(
    directory: Path,
    *,
    purpose: CompatibilityPurpose,
    current_manifest: AssignmentCheckpointContractManifest,
    actor_modules: Sequence[tuple[str, Any]],
    explicit_fallback: bool,
) -> AssignmentCheckpointLoadResult:
    profile = str(current_manifest.identity["profile_name"])
    resolver_enabled = (
        current_manifest.lifecycle_behavior_contract["resolver_contract_version"] != "disabled"
    )
    if not explicit_fallback:
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, "explicit unversioned legacy fallback was not requested")
        )
    decision = decide_missing_metadata(
        purpose=purpose,
        current_profile=profile,
        resolver_enabled=resolver_enabled,
        explicit_unversioned_legacy_fallback=explicit_fallback,
    )
    if not decision.allowed:
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, decision.reason)
        )
    if profile != "legacy":
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, "unversioned fallback requires current profile=legacy")
        )
    if (
        int(current_manifest.actor_schema["actor_dimension"]) != 909
        or int(current_manifest.action_contract["action_dimension"]) != 51
        or int(current_manifest.action_contract["noop_raw_id"]) != 50
    ):
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, "legacy fallback requires actor_dim=909 action_dim=51 noop=50")
        )
    actor_map, _, _ = _module_map(actor_modules, None, None)
    identities = tuple(current_manifest.scale["ordered_agent_names"])
    if tuple(actor_map) != identities:
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, "legacy live actor order differs from current contract")
        )
    paths = _legacy_actor_paths(directory, identities)
    inspected: list[_InspectedArtifact] = []
    for identity, path in zip(identities, paths, strict=True):
        try:
            state_dict = torch.load(path, map_location="cpu", weights_only=True)
        except Exception as exc:
            raise AssignmentCheckpointInventoryError(
                _context(directory, purpose, f"legacy actor {path.name} weights_only load failed: {exc}")
            ) from exc
        if not isinstance(state_dict, Mapping):
            raise AssignmentCheckpointInventoryError(
                _context(directory, purpose, f"legacy actor {path.name} is not a state-dict mapping")
            )
        actual = build_tensor_inventory_from_state_dict(state_dict, artifact_name=path.name)
        expected = build_tensor_inventory_from_state_dict(
            actor_map[identity].state_dict(),
            artifact_name=f"live {identity}",
        )
        comparison = compare_state_dict_inventories(expected, actual)
        if not comparison.allowed:
            mismatch = comparison.first_mismatch
            raise AssignmentCheckpointInventoryError(
                _context(
                    directory,
                    purpose,
                    f"legacy actor {path.name} inventory mismatch "
                    f"field={None if mismatch is None else mismatch.field_path}",
                )
            )
        file_size, file_digest = compute_file_sha256(path)
        inspected.append(
            _InspectedArtifact(
                entry=ArtifactFileInventoryEntry(
                    artifact_role="actor",
                    relative_file_name=path.name,
                    file_size=file_size,
                    file_sha256=file_digest,
                    serialization_mode="state_dict",
                    actor_identity=identity,
                    tensor_inventory=actual,
                    tensor_inventory_sha256=compute_tensor_inventory_sha256(actual),
                ),
                state_dict=state_dict,
                target_module=actor_map[identity],
                is_value_normalizer=False,
            )
        )
    if purpose != CompatibilityPurpose.STRUCTURAL_INSPECTION:
        _strict_mutate_all(inspected, directory=directory, purpose=purpose)
    return AssignmentCheckpointLoadResult(
        checkpoint_directory=directory,
        load_purpose=purpose,
        checkpoint_kind="unversioned_legacy",
        checkpoint_generation=None,
        contract_fingerprint=None,
        compatibility_decision=decision,
        loaded_actor_identities=identities if purpose != CompatibilityPurpose.STRUCTURAL_INSPECTION else (),
        critic_loaded=False,
        value_normalizer_loaded=False,
        legacy_fallback_used=True,
        named_ablation_used=None,
        continuation_acknowledgement=None,
        warnings=("unversioned legacy fallback has no native file digests or immutable contract",),
    )


def load_assignment_checkpoint(
    *,
    checkpoint_directory: Path,
    purpose: CompatibilityPurpose,
    current_manifest: AssignmentCheckpointContractManifest,
    actor_modules: Sequence[tuple[str, Any]],
    critic_module: Any | None = None,
    value_normalizer_module: Any | None = None,
    explicit_ablation_name: str | None = None,
    continuation_reset_acknowledged: bool = False,
    allow_unversioned_legacy_fallback: bool = False,
) -> AssignmentCheckpointLoadResult:
    """Validate all required state dictionaries before any strict live mutation."""

    directory = Path(checkpoint_directory).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        raise AssignmentCheckpointMetadataError(
            _context(directory, purpose, "selected checkpoint directory does not exist")
        )
    if purpose in {
        CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING,
        CompatibilityPurpose.EXACT_TRAINING_RESUME,
    }:
        decision = evaluate_compatibility(
            CompatibilityRequest(
                purpose=purpose,
                current_manifest=current_manifest,
                checkpoint_manifest=None,
            )
        )
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, decision.reason)
        )
    native = _read_native_checkpoint(directory, purpose)
    if native is not None:
        return _native_load(
            native,
            purpose=purpose,
            current_manifest=current_manifest,
            actor_modules=actor_modules,
            critic_module=critic_module,
            value_normalizer_module=value_normalizer_module,
            explicit_ablation_name=explicit_ablation_name,
            continuation_reset_acknowledged=continuation_reset_acknowledged,
        )
    if purpose not in {
        CompatibilityPurpose.NORMAL_EVALUATION,
        CompatibilityPurpose.STRUCTURAL_INSPECTION,
    }:
        raise AssignmentCheckpointCompatibilityError(
            _context(directory, purpose, "metadata-free checkpoints are evaluation/inspection only")
        )
    return _legacy_load(
        directory,
        purpose=purpose,
        current_manifest=current_manifest,
        actor_modules=actor_modules,
        explicit_fallback=allow_unversioned_legacy_fallback,
    )


def build_assignment_evaluation_contract_manifest(
    *,
    wrapper: Any,
    actors: Sequence[Any],
    algo_args: Mapping[str, Any],
    algorithm_name: str,
    harl_state_type: str = "EP",
) -> AssignmentCheckpointContractManifest:
    """Build the current evaluation contract from wrapper, constructed actors, and resolved config."""

    names = tuple(str(name) for name in wrapper.agents)
    if len(actors) != len(names) or len({id(actor.actor) for actor in actors}) != len(names):
        raise AssignmentCheckpointCompatibilityError(
            "evaluation requires one distinct constructed actor per ordered wrapper identity"
        )
    policies = tuple(actor.actor for actor in actors)

    def uniform(values: Sequence[Any], field: str) -> Any:
        if not values or any(value != values[0] for value in values[1:]):
            raise AssignmentCheckpointCompatibilityError(
                f"constructed evaluation actors disagree on {field}: {tuple(values)!r}"
            )
        return values[0]

    actor_hidden = tuple(
        uniform(
            [tuple(int(value) for value in policy.hidden_sizes) for policy in policies],
            "hidden sizes",
        )
    )
    activation = str(uniform([policy.base.activation_func for policy in policies], "activation"))
    feature_norm = bool(
        uniform(
            [policy.base.use_feature_normalization for policy in policies],
            "feature normalization",
        )
    )
    initialization = str(
        uniform([policy.initialization_method for policy in policies], "initialization")
    )
    gain = float(uniform([policy.gain for policy in policies], "action gain"))
    use_recurrent = bool(
        uniform([policy.use_recurrent_policy for policy in policies], "recurrent flag")
    )
    use_naive = bool(
        uniform([policy.use_naive_recurrent_policy for policy in policies], "naive recurrent flag")
    )
    recurrent_n = int(uniform([policy.recurrent_n for policy in policies], "recurrent_n"))
    action_dimensions: dict[str, int] = {}
    for name, actor, policy in zip(names, actors, policies, strict=True):
        head = policy.act.action_out
        if head.__class__.__name__ != "Categorical" or not hasattr(head, "linear"):
            raise AssignmentCheckpointCompatibilityError(
                f"evaluation actor {name} is not a Discrete/Categorical policy"
            )
        if int(actor.act_space.n) != int(head.linear.out_features):
            raise AssignmentCheckpointCompatibilityError(
                f"evaluation actor {name} action space/head dimensions disagree"
            )
        action_dimensions[name] = int(head.linear.out_features)

    model_args = algo_args["model"]
    policy_args = algo_args["algo"]
    train_args = algo_args["train"]
    value_norm_enabled = bool(train_args["use_valuenorm"])
    if value_norm_enabled:
        from harl.common.valuenorm import ValueNorm

        value_normalizer_contract = build_value_normalizer_contract(
            ValueNorm(1),
            enabled=True,
        )
    else:
        value_normalizer_contract = build_value_normalizer_contract(None, enabled=False)
    optimizer_class = str(
        uniform(
            [actor.actor_optimizer.__class__.__name__ for actor in actors],
            "optimizer class",
        )
    )
    runtime = AssignmentCheckpointRuntimeState(
        wrapper_schema_manifest=wrapper.assignment_observation_schema_manifest,
        wrapper_observation_layout=wrapper.assignment_observation_layout,
        profile_name=str(wrapper.assignment_lifecycle_profile_config["profile_name"]),
        algorithm_name=str(algorithm_name).lower(),
        harl_state_type=harl_state_type,
        ordered_agent_names=names,
        actor_input_dimensions_by_agent={
            name: int(actor.obs_space_size) for name, actor in zip(names, actors, strict=True)
        },
        critic_input_dimension=int(wrapper.share_observation_space[0].shape[0]),
        actor_action_dimensions_by_agent=action_dimensions,
        actor_class=f"{actors[0].__class__.__name__}/{policies[0].__class__.__name__}",
        critic_class="VCritic/VNet",
        action_distribution_class=policies[0].act.action_out.__class__.__name__,
        actor_hidden_sizes=actor_hidden,
        critic_hidden_sizes=tuple(int(value) for value in model_args["hidden_sizes"]),
        activation=activation,
        feature_normalization=feature_norm,
        share_param=bool(policy_args["share_param"]),
        number_of_actor_networks=len({id(policy) for policy in policies}),
        ordered_actor_network_names=names,
        critic_architecture="centralized_v_network",
        recurrent_n=recurrent_n,
        initialization_method=initialization,
        action_gain=gain,
        use_recurrent_policy=use_recurrent,
        use_naive_recurrent_policy=use_naive,
        actor_buffer_generator=resolve_installed_harl_actor_buffer_generator(
            use_recurrent_policy=use_recurrent,
            use_naive_recurrent_policy=use_naive,
        ),
        optimizer_class=optimizer_class,
        actor_learning_rate=float(uniform([actor.lr for actor in actors], "actor learning rate")),
        critic_learning_rate=float(model_args["critic_lr"]),
        optimizer_epsilon=float(uniform([actor.opti_eps for actor in actors], "optimizer epsilon")),
        weight_decay=float(uniform([actor.weight_decay for actor in actors], "weight decay")),
        ppo_epochs=int(uniform([actor.ppo_epoch for actor in actors], "PPO epochs")),
        actor_minibatches=int(
            uniform([actor.actor_num_mini_batch for actor in actors], "actor minibatches")
        ),
        critic_minibatches=int(policy_args["critic_num_mini_batch"]),
        clip_coefficient=float(uniform([actor.clip_param for actor in actors], "clip coefficient")),
        value_loss_coefficient=float(policy_args["value_loss_coef"]),
        entropy_coefficient=float(
            uniform([actor.entropy_coef for actor in actors], "entropy coefficient")
        ),
        gradient_clipping_enabled=bool(
            uniform([actor.use_max_grad_norm for actor in actors], "gradient clipping")
        ),
        max_gradient_norm=float(
            uniform([actor.max_grad_norm for actor in actors], "maximum gradient norm")
        ),
        gamma=float(policy_args["gamma"]),
        gae_lambda=float(policy_args["gae_lambda"]),
        value_norm_enabled=value_norm_enabled,
        value_normalizer_contract=value_normalizer_contract,
        proper_time_limits=bool(train_args["use_proper_time_limits"]),
        episode_length=int(train_args["episode_length"]),
        rollout_thread_count=int(train_args["n_rollout_threads"]),
    )
    return build_assignment_checkpoint_contract_manifest(
        runtime,
        allow_evaluation_only_profile=True,
    )


__all__ = [
    "AssignmentCheckpointCompatibilityError",
    "AssignmentCheckpointError",
    "AssignmentCheckpointIntegrityError",
    "AssignmentCheckpointInventoryError",
    "AssignmentCheckpointLoadError",
    "AssignmentCheckpointLoadResult",
    "AssignmentCheckpointMetadataError",
    "NAMED_LIFECYCLE_ABLATION",
    "build_assignment_evaluation_contract_manifest",
    "load_assignment_checkpoint",
]
