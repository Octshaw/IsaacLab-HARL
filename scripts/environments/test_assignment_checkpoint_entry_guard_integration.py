"""Pure Phase A4b checkpoint-entry semantic-guard integration evidence.

The suite uses canonical namespace packages, temporary metadata text files,
callback spies, and AST/source inspection.  It never imports either
AppLauncher entry point, constructs an actor/critic, or performs checkpoint
tensor serialization, deserialization, mutation, or state-dict inventory.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable, Mapping
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
A4A_SUPPORT_PATH = (
    REPO_ROOT / "scripts" / "environments" / "test_assignment_checkpoint_semantic_dispatch.py"
)
GUARD_KEY = f"{PACKAGE}.assignment_checkpoint_entry_guard"
SAVE_KEY = f"{PACKAGE}.assignment_checkpoint_save"
LOAD_KEY = f"{PACKAGE}.assignment_checkpoint_load"
AUDIT_KEY = f"{PACKAGE}.assignment_training_run_audit"

PLAYBACK_SOURCES = {
    "playback": REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py",
    "evaluation": REPO_ROOT / "scripts" / "environments" / "evaluate_assignment_rl_playback_diagnostics.py",
}

V3_CANONICAL_BYTE_LENGTH = 67794
V3_INTERFACE_SHA256 = "03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_types: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    *message_fragments: str,
) -> BaseException:
    try:
        function()
    except exception_types as exc:
        lowered = str(exc).lower()
        for fragment in message_fragments:
            _assert(fragment.lower() in lowered, f"missing error context {fragment!r}: {exc}")
        return exc
    except Exception as exc:
        raise AssertionError(f"unexpected {type(exc).__name__}: {exc}") from exc
    raise AssertionError("expected an exception")


def _install_namespace() -> None:
    packages = (
        ("isaaclab_tasks", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"),
        (
            "isaaclab_tasks.direct",
            REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct",
        ),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in packages:
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_exact(key: str, path: Path) -> ModuleType:
    existing = sys.modules.get(key)
    if existing is not None:
        _assert(Path(str(existing.__file__)).resolve() == path.resolve(), key)
        return existing
    spec = importlib.util.spec_from_file_location(key, path)
    _assert(spec is not None and spec.loader is not None, f"missing spec for {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(key, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


def _load_a4a_support() -> ModuleType:
    key = "_phase_a4a_checkpoint_fixture_support"
    return _load_exact(key, A4A_SUPPORT_PATH)


_install_namespace()
A4A = _load_a4a_support()
V2 = A4A.V2
V3 = A4A.V3
DISPATCH = A4A.DISPATCH


def _load_a4b_modules() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
    return (
        _load_exact(GUARD_KEY, SCAN_SOURCE / "assignment_checkpoint_entry_guard.py"),
        _load_exact(SAVE_KEY, SCAN_SOURCE / "assignment_checkpoint_save.py"),
        _load_exact(LOAD_KEY, SCAN_SOURCE / "assignment_checkpoint_load.py"),
        _load_exact(AUDIT_KEY, SCAN_SOURCE / "assignment_training_run_audit.py"),
    )


GUARD, SAVE, LOAD, AUDIT = _load_a4b_modules()


def _deepcopy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(value))


def _v3_mapping() -> dict[str, Any]:
    return _deepcopy_mapping(A4A._v3_mapping())


def _v2_manifest(mapping: Mapping[str, Any]) -> object:
    return V2.AssignmentCheckpointContractManifest.from_mapping(mapping)


def _decision_mapping(value: object) -> dict[str, Any]:
    to_mapping = getattr(value, "to_mapping", None)
    _assert(callable(to_mapping), f"decision lacks to_mapping: {type(value).__name__}")
    result = to_mapping()
    _assert(isinstance(result, Mapping), "decision to_mapping must return a mapping")
    return _deepcopy_mapping(result)


def _write_native_pair(
    directory: Path,
    manifest_mapping: Mapping[str, Any],
    *,
    fingerprint: str | None = None,
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    canonical = DISPATCH.canonical_assignment_checkpoint_manifest_bytes(manifest_mapping)
    digest = (
        DISPATCH.compute_assignment_checkpoint_manifest_sha256(manifest_mapping)
        if fingerprint is None
        else fingerprint
    )
    manifest_path = directory / GUARD.CONTRACT_MANIFEST_FILE
    fingerprint_path = directory / GUARD.CONTRACT_FINGERPRINT_FILE
    manifest_path.write_bytes(canonical + b"\n")
    fingerprint_path.write_bytes(digest.encode("ascii") + b"\n")
    return manifest_path, fingerprint_path


def _write_raw_pair(
    directory: Path,
    manifest_mapping: Mapping[str, Any],
    *,
    fingerprint: str | None = None,
) -> tuple[Path, Path]:
    """Write syntax-valid JSON metadata without pre-validating its schema."""

    directory.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(manifest_mapping, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest() if fingerprint is None else fingerprint
    manifest_path = directory / GUARD.CONTRACT_MANIFEST_FILE
    fingerprint_path = directory / GUARD.CONTRACT_FINGERPRINT_FILE
    manifest_path.write_bytes(raw + b"\n")
    fingerprint_path.write_bytes(digest.encode("ascii") + b"\n")
    return manifest_path, fingerprint_path


def _v2_direct_decision(
    *,
    checkpoint_mapping: Mapping[str, Any],
    current_mapping: Mapping[str, Any],
    purpose: object,
    fingerprint: str,
    explicit_ablation_name: str | None = None,
    training_state_manifest: object | None = None,
    continuation_reset_acknowledged: bool = False,
) -> object:
    return V2.evaluate_compatibility(
        V2.CompatibilityRequest(
            purpose=purpose,
            checkpoint_manifest=_v2_manifest(checkpoint_mapping),
            current_manifest=_v2_manifest(current_mapping),
            checkpoint_fingerprint=fingerprint,
            explicit_ablation_name=explicit_ablation_name,
            training_state_manifest=training_state_manifest,
            continuation_reset_acknowledged=continuation_reset_acknowledged,
        )
    )


def _assert_v2_guard_matches_direct(
    *,
    checkpoint_mapping: Mapping[str, Any],
    current_mapping: Mapping[str, Any],
    entry_purpose: object,
    compatibility_purpose: object,
    fingerprint: str,
    explicit_ablation_name: str | None = None,
    training_state_manifest: object | None = None,
    continuation_reset_acknowledged: bool = False,
) -> object:
    direct = _v2_direct_decision(
        checkpoint_mapping=checkpoint_mapping,
        current_mapping=current_mapping,
        purpose=compatibility_purpose,
        fingerprint=fingerprint,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=training_state_manifest,
        continuation_reset_acknowledged=continuation_reset_acknowledged,
    )
    guarded = GUARD.evaluate_checkpoint_entry_guard(
        manifest_mapping=checkpoint_mapping,
        stored_fingerprint=fingerprint,
        purpose=entry_purpose,
        current_manifest_or_context=current_mapping,
        v2_compatibility_purpose=compatibility_purpose,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=(
            None
            if training_state_manifest is None
            else training_state_manifest.to_mapping()
        ),
        continuation_reset_acknowledged=continuation_reset_acknowledged,
    )
    _assert(guarded.semantic_family == "v2", "guard did not classify V2")
    _assert(guarded.fingerprint_verified, "guard did not verify V2 fingerprint")
    _assert(
        _decision_mapping(guarded.semantic_decision) == _decision_mapping(direct),
        "guard changed the full V2 decision mapping",
    )
    _assert(guarded.semantic_allowed is bool(direct.allowed), "V2 allowed bit changed")
    return guarded


def _called_name(node: ast.Call) -> str:
    target: ast.expr = node.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def test_native_metadata_pair_states_and_strict_corruption() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        empty = root / "empty"
        empty.mkdir()
        state = GUARD.inspect_checkpoint_metadata_pair(empty)
        _assert(
            state.metadata_mode is GUARD.AssignmentCheckpointMetadataMode.BOTH_ABSENT,
            "empty directory pair mode",
        )
        _assert(GUARD.read_checkpoint_native_metadata_pair(empty) is None, "both-absent read")
        absent = GUARD.read_and_evaluate_checkpoint_entry_guard(
            checkpoint_directory=empty,
            purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
        )
        _assert(absent.metadata_mode is GUARD.AssignmentCheckpointMetadataMode.BOTH_ABSENT, "absent result mode")
        _assert(absent.fallback_mode == "legacy_v2_metadata_absence_fallback", "fallback identity")
        _assert(not absent.semantic_allowed and not absent.weight_io_authorized, "absent guard must defer closed")
        _assert(absent.parsed_manifest is None, "absent metadata synthesized a manifest")

        valid_v2 = root / "valid_v2"
        _write_native_pair(valid_v2, A4A.V2_LEGACY_MAPPING)
        state = GUARD.inspect_checkpoint_metadata_pair(valid_v2)
        _assert(state.metadata_mode is GUARD.AssignmentCheckpointMetadataMode.BOTH_PRESENT, "V2 pair mode")
        native = GUARD.read_checkpoint_native_metadata_pair(valid_v2)
        _assert(native is not None, "V2 native pair missing")
        _assert(native.stored_fingerprint == A4A.V2_LEGACY_SHA256, "V2 stored fingerprint")
        _assert(native.computed_fingerprint == A4A.V2_LEGACY_SHA256, "V2 computed fingerprint")
        _assert(native.canonical_bytes == A4A.V2_LEGACY_BYTES, "V2 canonical bytes")
        guarded_v2 = GUARD.read_and_evaluate_checkpoint_entry_guard(
            checkpoint_directory=valid_v2,
            purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            current_manifest_or_context=A4A.V2_LEGACY_MAPPING,
            v2_compatibility_purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
        )
        _assert(guarded_v2.semantic_allowed and guarded_v2.weight_io_authorized, "valid native V2")

        valid_v3 = root / "valid_v3"
        _write_native_pair(valid_v3, _v3_mapping())
        guarded_v3 = GUARD.read_and_evaluate_checkpoint_entry_guard(
            checkpoint_directory=valid_v3,
            purpose=GUARD.AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT,
        )
        _assert(guarded_v3.semantic_allowed and not guarded_v3.weight_io_authorized, "valid V3 audit")

        partial_manifest = root / "partial_manifest"
        partial_manifest.mkdir()
        (partial_manifest / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(A4A.V2_LEGACY_BYTES + b"\n")
        _assert(
            GUARD.inspect_checkpoint_metadata_pair(partial_manifest).metadata_mode
            is GUARD.AssignmentCheckpointMetadataMode.PARTIAL,
            "manifest-only pair state",
        )
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(partial_manifest),
            GUARD.AssignmentCheckpointMetadataPairError,
            "both exist or both be absent",
        )

        partial_fingerprint = root / "partial_fingerprint"
        partial_fingerprint.mkdir()
        (partial_fingerprint / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(
            A4A.V2_LEGACY_SHA256.encode("ascii") + b"\n"
        )
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(partial_fingerprint),
            GUARD.AssignmentCheckpointMetadataPairError,
        )

        malformed_manifest = root / "malformed_manifest"
        malformed_manifest.mkdir()
        (malformed_manifest / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(b"{\n")
        (malformed_manifest / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(b"0" * 64 + b"\n")
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(malformed_manifest),
            GUARD.AssignmentCheckpointMetadataPairError,
            "valid UTF-8 JSON",
        )

        noncanonical = root / "noncanonical_manifest"
        noncanonical.mkdir()
        (noncanonical / GUARD.CONTRACT_MANIFEST_FILE).write_text(
            json.dumps(A4A.V2_LEGACY_MAPPING, indent=2) + "\n",
            encoding="utf-8",
            newline="",
        )
        (noncanonical / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(
            A4A.V2_LEGACY_SHA256.encode("ascii") + b"\n"
        )
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(noncanonical),
            GUARD.AssignmentCheckpointMetadataPairError,
            "version-canonical",
        )

        unknown = root / "unknown_version"
        unknown.mkdir()
        unknown_mapping = _deepcopy_mapping(A4A.V2_LEGACY_MAPPING)
        unknown_mapping["manifest_format_version"] = "assignment_checkpoint_contract_v999"
        unknown_bytes = json.dumps(
            unknown_mapping,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        (unknown / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(unknown_bytes + b"\n")
        (unknown / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(
            hashlib.sha256(unknown_bytes).hexdigest().encode("ascii") + b"\n"
        )
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(unknown),
            GUARD.AssignmentCheckpointMetadataPairError,
            "semantic validation",
        )

        for name, raw in (
            ("empty", b"\n"),
            ("short", b"a" * 63 + b"\n"),
            ("uppercase", A4A.V2_LEGACY_SHA256.upper().encode("ascii") + b"\n"),
            ("nonhex", b"g" * 64 + b"\n"),
            ("missing_lf", A4A.V2_LEGACY_SHA256.encode("ascii")),
            ("extra_lf", A4A.V2_LEGACY_SHA256.encode("ascii") + b"\n\n"),
        ):
            directory = root / f"fingerprint_{name}"
            _write_native_pair(directory, A4A.V2_LEGACY_MAPPING)
            (directory / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(raw)
            _expect_error(
                lambda directory=directory: GUARD.read_checkpoint_native_metadata_pair(directory),
                GUARD.AssignmentCheckpointFingerprintError,
            )

        mismatch = root / "fingerprint_mismatch"
        _write_native_pair(mismatch, A4A.V2_LEGACY_MAPPING, fingerprint="a" * 64)
        _expect_error(
            lambda: GUARD.read_checkpoint_native_metadata_pair(mismatch),
            GUARD.AssignmentCheckpointFingerprintError,
            "does not match",
        )


def test_v2_direct_guard_full_decision_equivalence() -> None:
    normal = V2.CompatibilityPurpose.NORMAL_EVALUATION
    structural = V2.CompatibilityPurpose.STRUCTURAL_INSPECTION
    continuation = V2.CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION
    ablation_purpose = V2.CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION
    evaluation = GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION
    offline = GUARD.AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT
    continuation_entry = GUARD.AssignmentCheckpointEntryPurpose.LOAD_CONTINUATION
    ablation = A4A._v2_ablation_mapping()

    cases = (
        (
            "legacy_native",
            A4A.V2_LEGACY_MAPPING,
            A4A.V2_LEGACY_MAPPING,
            evaluation,
            normal,
            A4A.V2_LEGACY_SHA256,
            None,
            "normal_evaluation",
            True,
        ),
        (
            "contract_c_native",
            A4A.V2_CONTRACT_C_MAPPING,
            A4A.V2_CONTRACT_C_MAPPING,
            evaluation,
            normal,
            A4A.V2_CONTRACT_C_SHA256,
            None,
            "normal_evaluation",
            True,
        ),
        (
            "profile_mismatch",
            A4A.V2_CONTRACT_C_MAPPING,
            ablation,
            evaluation,
            normal,
            A4A.V2_CONTRACT_C_SHA256,
            None,
            "evaluation_semantic_mismatch",
            False,
        ),
        (
            "structural_mismatch",
            A4A.V2_LEGACY_MAPPING,
            A4A.V2_CONTRACT_C_MAPPING,
            offline,
            structural,
            A4A.V2_LEGACY_SHA256,
            None,
            "structural_mismatch",
            False,
        ),
        (
            "continuation_mismatch",
            A4A.V2_CONTRACT_C_MAPPING,
            ablation,
            continuation_entry,
            continuation,
            A4A.V2_CONTRACT_C_SHA256,
            None,
            "continuation_contract_mismatch",
            False,
        ),
        (
            "named_ablation",
            A4A.V2_CONTRACT_C_MAPPING,
            ablation,
            evaluation,
            ablation_purpose,
            A4A.V2_CONTRACT_C_SHA256,
            V2.NAMED_LIFECYCLE_ABLATION,
            "explicit_ablation_evaluation",
            True,
        ),
    )
    for (
        name,
        checkpoint,
        current,
        entry_purpose,
        compatibility_purpose,
        fingerprint,
        ablation_name,
        classification,
        allowed,
    ) in cases:
        guarded = _assert_v2_guard_matches_direct(
            checkpoint_mapping=checkpoint,
            current_mapping=current,
            entry_purpose=entry_purpose,
            compatibility_purpose=compatibility_purpose,
            fingerprint=fingerprint,
            explicit_ablation_name=ablation_name,
        )
        _assert(
            guarded.decision_classification == classification,
            f"{name} classification drift",
        )
        _assert(guarded.semantic_allowed is allowed, f"{name} allowed drift")


def test_v3_interface_golden_audit_only_and_weight_denials() -> None:
    mapping = _v3_mapping()
    canonical = DISPATCH.canonical_assignment_checkpoint_manifest_bytes(mapping)
    digest = DISPATCH.compute_assignment_checkpoint_manifest_sha256(mapping)
    _assert(len(canonical) == V3_CANONICAL_BYTE_LENGTH, "V3 canonical byte length drift")
    _assert(digest == V3_INTERFACE_SHA256, "V3 literal interface SHA-256 drift")
    _assert(hashlib.sha256(canonical).hexdigest() == V3_INTERFACE_SHA256, "V3 byte digest drift")

    audit = GUARD.evaluate_checkpoint_entry_guard(
        manifest_mapping=mapping,
        stored_fingerprint=V3_INTERFACE_SHA256,
        purpose=GUARD.AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT,
    )
    _assert(audit.metadata_mode is GUARD.AssignmentCheckpointMetadataMode.BOTH_PRESENT, "V3 metadata mode")
    _assert(audit.manifest_version == V3.MANIFEST_FORMAT_VERSION, "V3 version")
    _assert(
        audit.manifest_kind
        == V3.AssignmentCheckpointManifestKind.INTERFACE_SEMANTIC_DESCRIPTOR.value,
        "V3 kind",
    )
    _assert(audit.semantic_family == "v3", "V3 family")
    _assert(audit.fingerprint_verified, "V3 fingerprint")
    _assert(audit.semantic_allowed, "V3 interface audit must be semantically allowed")
    _assert(not audit.weight_io_authorized, "V3 interface audit cannot authorize weights")
    semantic = _decision_mapping(audit.semantic_decision)
    _assert(semantic["schema_valid"], "V3 schema validity")
    _assert(semantic["interface_semantics_valid"], "V3 interface semantics")
    _assert(not semantic["runtime_ready"], "V3 runtime readiness")
    _assert(not semantic["weight_use_authorized"], "V3 weight readiness")

    for purpose in (
        GUARD.AssignmentCheckpointEntryPurpose.SAVE,
        GUARD.AssignmentCheckpointEntryPurpose.LOAD_CONTINUATION,
        GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
        GUARD.AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK,
    ):
        denied = GUARD.evaluate_checkpoint_entry_guard(
            manifest_mapping=mapping,
            stored_fingerprint=V3_INTERFACE_SHA256,
            purpose=purpose,
        )
        _assert(not denied.semantic_allowed, f"V3 {purpose.value} semantic allow")
        _assert(not denied.weight_io_authorized, f"V3 {purpose.value} weight allow")
        _assert(denied.fingerprint_verified, f"V3 {purpose.value} fingerprint")
        _assert(
            type(denied.semantic_decision) is V3.AssignmentCheckpointV3SemanticDecision,
            f"V3 {purpose.value} denial lost typed interface-audit evidence",
        )
        denied_semantic = _decision_mapping(denied.semantic_decision)
        _assert(
            denied_semantic["interface_semantics_valid"]
            and not denied_semantic["runtime_ready"]
            and not denied_semantic["weight_use_authorized"],
            f"V3 {purpose.value} denial semantic evidence",
        )
        denial = _expect_error(
            lambda result=denied: GUARD.require_checkpoint_weight_io_authorized(result),
            GUARD.AssignmentCheckpointEntryPurposeDeniedError,
        )
        _assert(denial.result is denied, f"V3 {purpose.value} denial lost guard result")

    ready = _v3_mapping()
    ready["manifest_kind"] = V3.AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST.value
    for purpose in tuple(GUARD.AssignmentCheckpointEntryPurpose):
        _expect_error(
            lambda purpose=purpose: GUARD.evaluate_checkpoint_entry_guard(
                manifest_mapping=ready,
                stored_fingerprint=V3_INTERFACE_SHA256,
                purpose=purpose,
            ),
            (
                V3.CheckpointReadyManifestNotAuthorizedError,
                GUARD.AssignmentCheckpointEntryGuardError,
            ),
        )


def test_v2_entry_and_compatibility_purpose_matrix() -> None:
    mapping = A4A.V2_CONTRACT_C_MAPPING
    fingerprint = A4A.V2_CONTRACT_C_SHA256
    allowed_cases = (
        (
            GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            V2.CompatibilityPurpose.STRUCTURAL_INSPECTION,
            True,
            True,
        ),
        (
            GUARD.AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT,
            V2.CompatibilityPurpose.STRUCTURAL_INSPECTION,
            True,
            False,
        ),
    )
    for entry_purpose, compatibility_purpose, semantic_allowed, weight_allowed in allowed_cases:
        result = GUARD.evaluate_checkpoint_entry_guard(
            manifest_mapping=mapping,
            stored_fingerprint=fingerprint,
            purpose=entry_purpose,
            current_manifest_or_context=mapping,
            v2_compatibility_purpose=compatibility_purpose,
        )
        _assert(
            result.semantic_allowed is semantic_allowed,
            f"semantic result for {entry_purpose.value}/{compatibility_purpose.value}",
        )
        _assert(
            result.weight_io_authorized is weight_allowed,
            f"weight result for {entry_purpose.value}/{compatibility_purpose.value}",
        )
        direct = _v2_direct_decision(
            checkpoint_mapping=mapping,
            current_mapping=mapping,
            purpose=compatibility_purpose,
            fingerprint=fingerprint,
        )
        _assert(
            _decision_mapping(result.semantic_decision) == _decision_mapping(direct),
            "entry-purpose glue changed the underlying V2 semantic decision",
        )
        if not weight_allowed:
            denial = _expect_error(
                lambda result=result: GUARD.require_checkpoint_weight_io_authorized(result),
                GUARD.AssignmentCheckpointEntryPurposeDeniedError,
            )
            _assert(denial.result is result, "offline denial lost guard result")

    for entry_purpose, compatibility_purpose in (
        (
            GUARD.AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK,
            V2.CompatibilityPurpose.STRUCTURAL_INSPECTION,
        ),
        (
            GUARD.AssignmentCheckpointEntryPurpose.LOAD_CONTINUATION,
            V2.CompatibilityPurpose.NORMAL_EVALUATION,
        ),
    ):
        direct = _v2_direct_decision(
            checkpoint_mapping=mapping,
            current_mapping=mapping,
            purpose=compatibility_purpose,
            fingerprint=fingerprint,
        )
        _assert(direct.allowed, "negative pair must isolate entry-purpose rejection")
        denied = GUARD.evaluate_checkpoint_entry_guard(
            manifest_mapping=mapping,
            stored_fingerprint=fingerprint,
            purpose=entry_purpose,
            current_manifest_or_context=mapping,
            v2_compatibility_purpose=compatibility_purpose,
        )
        _assert(not denied.semantic_allowed and not denied.weight_io_authorized, "purpose-pair denial")
        _assert(denied.decision_classification == "entry_v2_purpose_mismatch", "purpose-pair classification")
        _assert(_decision_mapping(denied.semantic_decision) == _decision_mapping(direct), "purpose-pair lost V2 decision")
        denial = _expect_error(
            lambda denied=denied: GUARD.require_checkpoint_weight_io_authorized(denied),
            GUARD.AssignmentCheckpointEntryPurposeDeniedError,
            "cannot request V2 compatibility purpose",
        )
        _assert(denial.result is denied, "purpose-pair denial lost guard result")


def test_playback_and_diagnostics_ast_guard_routing() -> None:
    expected_entry_purposes = {
        "playback": "LOAD_PLAYBACK",
        "evaluation": "LOAD_EVALUATION",
    }
    forbidden_exact_calls = {"torch.load", "torch.save", "torch.jit.load"}
    forbidden_import_suffixes = (
        ".assignment_checkpoint_contract_v3",
        ".assignment_checkpoint_semantic_dispatch",
    )
    for label, path in PLAYBACK_SOURCES.items():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        _assert(
            f"{PACKAGE}.assignment_checkpoint_load" in imported_modules,
            f"{label} does not import the canonical checkpoint loader",
        )
        _assert(
            f"{PACKAGE}.assignment_checkpoint_entry_guard" in imported_modules,
            f"{label} does not import the entry-purpose vocabulary",
        )
        _assert(
            not any(module.endswith(forbidden_import_suffixes) for module in imported_modules),
            f"{label} duplicates V3/dispatcher authority",
        )

        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        names = [_called_name(node) for node in calls]
        forbidden = {
            name
            for name in names
            if name in forbidden_exact_calls or name.endswith(".load_state_dict")
        }
        _assert(not forbidden, f"{label} direct checkpoint tensor bypass: {forbidden}")
        loader_calls = [
            node for node, name in zip(calls, names, strict=True)
            if name == "load_assignment_checkpoint"
        ]
        _assert(len(loader_calls) == 1, f"{label} must have exactly one canonical loader call")
        loader_call = loader_calls[0]
        keywords = {keyword.arg: keyword.value for keyword in loader_call.keywords}
        _assert("entry_purpose" in keywords, f"{label} omitted explicit entry purpose")
        entry_value = keywords["entry_purpose"]
        _assert(
            isinstance(entry_value, ast.Attribute)
            and isinstance(entry_value.value, ast.Name)
            and entry_value.value.id == "AssignmentCheckpointEntryPurpose"
            and entry_value.attr == expected_entry_purposes[label],
            f"{label} entry purpose is not exact",
        )
        _assert("purpose" in keywords, f"{label} dropped the unchanged V2 purpose")

        post_load_suffixes = (".prep_rollout", ".reset", ".act", ".evaluate_actions", ".step")
        post_load_calls = [
            node
            for node, name in zip(calls, names, strict=True)
            if any(name.endswith(suffix) for suffix in post_load_suffixes)
        ]
        _assert(post_load_calls, f"{label} expected playback/evaluation operations")
        _assert(
            all(node.lineno > loader_call.lineno for node in post_load_calls),
            f"{label} invokes playback/evaluation before checkpoint guard/load",
        )
        _assert(
            GUARD.CONTRACT_MANIFEST_FILE not in source
            and GUARD.CONTRACT_FINGERPRINT_FILE not in source,
            f"{label} reads native metadata itself",
        )
        _assert(V3_INTERFACE_SHA256 not in source, f"{label} contains a V3 hash allow shortcut")


def test_blocked_v3_save_precedes_inventory_and_artifacts() -> None:
    v2_save = GUARD.evaluate_checkpoint_save_entry_guard(A4A.V2_CONTRACT_C_MAPPING)
    _assert(v2_save.semantic_allowed and v2_save.weight_io_authorized, "V2 save guard regression")
    _assert(v2_save.decision_classification == "v2_save_contract_valid", "V2 save classification")

    calls = {"inventory": 0, "atomic": 0, "torch_save": 0}

    def inventory_spy(*args: Any, **kwargs: Any) -> Any:
        calls["inventory"] += 1
        raise AssertionError("blocked save reached state-dict inventory")

    def atomic_spy(*args: Any, **kwargs: Any) -> Any:
        calls["atomic"] += 1
        raise AssertionError("blocked save reached checkpoint tensor write")

    def torch_save_spy(*args: Any, **kwargs: Any) -> Any:
        calls["torch_save"] += 1
        raise AssertionError("blocked save reached torch.save")

    with tempfile.TemporaryDirectory() as temp:
        run_root = Path(temp) / "run"
        checkpoint = run_root / "models"
        coordinator = SAVE.AssignmentCheckpointSaveCoordinator(run_root)
        with (
            mock.patch.object(SAVE, "build_tensor_inventory_from_state_dict", side_effect=inventory_spy),
            mock.patch.object(SAVE, "_atomic_torch_save", side_effect=atomic_spy),
            mock.patch.object(SAVE.torch, "save", side_effect=torch_save_spy),
        ):
            _expect_error(
                lambda: coordinator.save_checkpoint(
                    checkpoint_directory=checkpoint,
                    checkpoint_kind="regular",
                    checkpoint_generation=0,
                    manifest=_v3_mapping(),
                    actor_state_dicts=(),
                    critic_state_dict={},
                    value_normalizer_state_dict=None,
                ),
                SAVE.AssignmentCheckpointSaveError,
                "semantic save guard",
            )
        _assert(calls == {"inventory": 0, "atomic": 0, "torch_save": 0}, "V3 save pre-I/O ordering")
        _assert(not run_root.exists(), "blocked V3 save created checkpoint artifacts")

    incoming_fingerprint = DISPATCH.compute_assignment_checkpoint_manifest_sha256(
        A4A.V2_CONTRACT_C_MAPPING
    )
    with tempfile.TemporaryDirectory() as temp:
        matching_root = Path(temp) / "matching_v2"
        _write_native_pair(matching_root, A4A.V2_CONTRACT_C_MAPPING)
        SAVE.AssignmentCheckpointSaveCoordinator._guard_existing_metadata_pair(
            matching_root,
            expected_fingerprint=incoming_fingerprint,
        )

    existing_cases: list[tuple[str, Callable[[Path], None]]] = [
        (
            "different valid V2 fingerprint",
            lambda directory: _write_native_pair(directory, A4A.V2_LEGACY_MAPPING),
        ),
        (
            "partial metadata pair",
            lambda directory: (
                directory.mkdir(parents=True, exist_ok=True),
                (directory / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(
                    A4A.V2_CONTRACT_C_BYTES + b"\n"
                ),
            ),
        ),
        (
            "V3 interface descriptor",
            lambda directory: _write_native_pair(directory, _v3_mapping()),
        ),
        (
            "unknown manifest version",
            lambda directory: _write_raw_pair(
                directory,
                {
                    **_deepcopy_mapping(A4A.V2_CONTRACT_C_MAPPING),
                    "manifest_format_version": "assignment_checkpoint_contract_v999",
                },
            ),
        ),
        (
            "V3 checkpoint-ready claim",
            lambda directory: _write_raw_pair(
                directory,
                {
                    **_v3_mapping(),
                    "manifest_kind": (
                        V3.AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST.value
                    ),
                },
            ),
        ),
    ]
    for label, prepare in existing_cases:
        calls = {"inventory": 0, "atomic": 0, "torch_save": 0}
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp) / "run"
            prepare(run_root)
            before = {
                path.relative_to(run_root): path.read_bytes()
                for path in run_root.rglob("*")
                if path.is_file()
            }
            checkpoint = run_root / "models"
            coordinator = SAVE.AssignmentCheckpointSaveCoordinator(run_root)
            with (
                mock.patch.object(
                    SAVE,
                    "build_tensor_inventory_from_state_dict",
                    side_effect=inventory_spy,
                ),
                mock.patch.object(SAVE, "_atomic_torch_save", side_effect=atomic_spy),
                mock.patch.object(SAVE.torch, "save", side_effect=torch_save_spy),
            ):
                _expect_error(
                    lambda: coordinator.save_checkpoint(
                        checkpoint_directory=checkpoint,
                        checkpoint_kind="regular",
                        checkpoint_generation=0,
                        manifest=_v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                        actor_state_dicts=(),
                        critic_state_dict={},
                        value_normalizer_state_dict=None,
                    ),
                    SAVE.AssignmentCheckpointSaveError,
                    "existing-metadata guard",
                    "before tensor inventory",
                )
            after = {
                path.relative_to(run_root): path.read_bytes()
                for path in run_root.rglob("*")
                if path.is_file()
            }
            _assert(
                calls == {"inventory": 0, "atomic": 0, "torch_save": 0},
                f"{label} save pre-I/O ordering",
            )
            _assert(after == before, f"{label} changed existing metadata or wrote artifacts")
            _assert(not checkpoint.exists(), f"{label} created checkpoint directory")


def _load_with_sentinels(
    *,
    directory: Path,
    current_manifest: object,
    purpose: object,
    entry_purpose: object,
    allow_legacy: bool = False,
) -> tuple[Any, dict[str, int]]:
    calls = {"native_read": 0, "native_load": 0, "legacy_load": 0, "torch_load": 0}
    native_sentinel = object()
    return_sentinel = object()

    def native_read(*args: Any, **kwargs: Any) -> object:
        calls["native_read"] += 1
        return native_sentinel

    def native_load(checkpoint: object, **kwargs: Any) -> object:
        calls["native_load"] += 1
        _assert(checkpoint is native_sentinel, "native sentinel identity")
        return return_sentinel

    def legacy_load(*args: Any, **kwargs: Any) -> object:
        calls["legacy_load"] += 1
        return return_sentinel

    def torch_load(*args: Any, **kwargs: Any) -> Any:
        calls["torch_load"] += 1
        raise AssertionError("pure A4b suite reached torch.load")

    with (
        mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=native_read),
        mock.patch.object(LOAD, "_native_load", side_effect=native_load),
        mock.patch.object(LOAD, "_legacy_load", side_effect=legacy_load),
        mock.patch.object(LOAD.torch, "load", side_effect=torch_load),
    ):
        result = LOAD.load_assignment_checkpoint(
            checkpoint_directory=directory,
            purpose=purpose,
            entry_purpose=entry_purpose,
            current_manifest=current_manifest,
            actor_modules=(),
            allow_unversioned_legacy_fallback=allow_legacy,
        )
    return (result, calls)


def test_load_guard_precedes_native_tensor_path() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid_v2"
        _write_native_pair(valid, A4A.V2_CONTRACT_C_MAPPING)
        result, calls = _load_with_sentinels(
            directory=valid,
            current_manifest=_v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
            purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
            entry_purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
        )
        _assert(calls == {"native_read": 1, "native_load": 1, "legacy_load": 0, "torch_load": 0}, "allowed V2 load seam")
        _assert(result is not None, "allowed V2 callback result")

        blocked_cases: list[tuple[str, Path, object, object, object]] = []
        profile_mismatch = root / "profile_mismatch"
        _write_native_pair(profile_mismatch, A4A.V2_CONTRACT_C_MAPPING)
        blocked_cases.append(
            (
                "profile mismatch",
                profile_mismatch,
                _v2_manifest(A4A._v2_ablation_mapping()),
                V2.CompatibilityPurpose.NORMAL_EVALUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            )
        )
        v3_playback = root / "v3_playback"
        _write_native_pair(v3_playback, _v3_mapping())
        (v3_playback / LOAD.TRAINING_STATE_MANIFEST_FILE).write_text(
            "{malformed-v2-marker",
            encoding="utf-8",
        )
        for label, compatibility_purpose, entry_purpose in (
            (
                "V3 playback",
                V2.CompatibilityPurpose.NORMAL_EVALUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK,
            ),
            (
                "V3 evaluation",
                V2.CompatibilityPurpose.NORMAL_EVALUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            ),
            (
                "V3 continuation",
                V2.CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_CONTINUATION,
            ),
        ):
            blocked_cases.append(
                (
                    label,
                    v3_playback,
                    _v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                    compatibility_purpose,
                    entry_purpose,
                )
            )
        corrupt = root / "corrupt"
        _write_native_pair(corrupt, A4A.V2_CONTRACT_C_MAPPING, fingerprint="a" * 64)
        blocked_cases.append(
            (
                "fingerprint mismatch",
                corrupt,
                _v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                V2.CompatibilityPurpose.NORMAL_EVALUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            )
        )
        partial = root / "partial"
        partial.mkdir()
        (partial / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(A4A.V2_CONTRACT_C_BYTES + b"\n")
        blocked_cases.append(
            (
                "partial native metadata",
                partial,
                _v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                V2.CompatibilityPurpose.NORMAL_EVALUATION,
                GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
            )
        )
        for name, mapping in (
            (
                "unknown version",
                {
                    **_deepcopy_mapping(A4A.V2_CONTRACT_C_MAPPING),
                    "manifest_format_version": "assignment_checkpoint_contract_v999",
                },
            ),
            (
                "V3 ready kind",
                {
                    **_v3_mapping(),
                    "manifest_kind": V3.AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST.value,
                },
            ),
        ):
            directory = root / name.replace(" ", "_")
            directory.mkdir()
            raw = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode("utf-8")
            (directory / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(raw + b"\n")
            (directory / GUARD.CONTRACT_FINGERPRINT_FILE).write_bytes(
                hashlib.sha256(raw).hexdigest().encode("ascii") + b"\n"
            )
            blocked_cases.append(
                (
                    name,
                    directory,
                    _v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                    V2.CompatibilityPurpose.NORMAL_EVALUATION,
                    GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
                )
            )
        for name, directory, current, purpose, entry_purpose in blocked_cases:
            native_calls = {
                "read": 0,
                "load": 0,
                "legacy": 0,
                "torch": 0,
                "load_state_dict": 0,
            }

            def unexpected_read(*args: Any, **kwargs: Any) -> Any:
                native_calls["read"] += 1
                raise AssertionError(f"{name} reached native reader")

            def unexpected_native(*args: Any, **kwargs: Any) -> Any:
                native_calls["load"] += 1
                raise AssertionError(f"{name} reached native tensor loader")

            def unexpected_legacy(*args: Any, **kwargs: Any) -> Any:
                native_calls["legacy"] += 1
                raise AssertionError(f"{name} reached legacy tensor loader")

            def unexpected_torch(*args: Any, **kwargs: Any) -> Any:
                native_calls["torch"] += 1
                raise AssertionError(f"{name} reached torch.load")

            def unexpected_mutation(*args: Any, **kwargs: Any) -> Any:
                native_calls["load_state_dict"] += 1
                raise AssertionError(f"{name} reached load_state_dict-like mutation")

            with (
                mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=unexpected_read),
                mock.patch.object(LOAD, "_native_load", side_effect=unexpected_native),
                mock.patch.object(LOAD, "_legacy_load", side_effect=unexpected_legacy),
                mock.patch.object(LOAD.torch, "load", side_effect=unexpected_torch),
                mock.patch.object(LOAD, "_strict_mutate_all", side_effect=unexpected_mutation),
            ):
                _expect_error(
                    lambda directory=directory, current=current, purpose=purpose, entry_purpose=entry_purpose: LOAD.load_assignment_checkpoint(
                        checkpoint_directory=directory,
                        purpose=purpose,
                        entry_purpose=entry_purpose,
                        current_manifest=current,
                        actor_modules=(),
                    ),
                    LOAD.AssignmentCheckpointError,
                )
            _assert(
                native_calls
                == {"read": 0, "load": 0, "legacy": 0, "torch": 0, "load_state_dict": 0},
                f"{name} pre-I/O callback counts",
            )

        toctou = root / "present_then_missing"
        _write_native_pair(toctou, A4A.V2_CONTRACT_C_MAPPING)
        toctou_calls = {"read": 0, "native": 0, "legacy": 0, "torch": 0}

        def disappearing_native(*args: Any, **kwargs: Any) -> None:
            toctou_calls["read"] += 1
            return None

        def forbidden_native(*args: Any, **kwargs: Any) -> Any:
            toctou_calls["native"] += 1
            raise AssertionError("TOCTOU case reached native tensor load")

        def forbidden_legacy(*args: Any, **kwargs: Any) -> Any:
            toctou_calls["legacy"] += 1
            raise AssertionError("TOCTOU case reached legacy fallback")

        def forbidden_torch(*args: Any, **kwargs: Any) -> Any:
            toctou_calls["torch"] += 1
            raise AssertionError("TOCTOU case reached torch.load")

        with (
            mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=disappearing_native),
            mock.patch.object(LOAD, "_native_load", side_effect=forbidden_native),
            mock.patch.object(LOAD, "_legacy_load", side_effect=forbidden_legacy),
            mock.patch.object(LOAD.torch, "load", side_effect=forbidden_torch),
        ):
            _expect_error(
                lambda: LOAD.load_assignment_checkpoint(
                    checkpoint_directory=toctou,
                    purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
                    entry_purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
                    current_manifest=_v2_manifest(A4A.V2_CONTRACT_C_MAPPING),
                    actor_modules=(),
                    allow_unversioned_legacy_fallback=True,
                ),
                LOAD.AssignmentCheckpointMetadataError,
                "metadata disappeared after semantic authorization",
                "legacy fallback is forbidden",
            )
        _assert(
            toctou_calls == {"read": 1, "native": 0, "legacy": 0, "torch": 0},
            "present-to-missing TOCTOU escaped to tensor or legacy path",
        )


def test_legacy_fallback_non_expansion_and_run_root_authority() -> None:
    direct = V2.decide_missing_metadata(
        purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
        current_profile="legacy",
        resolver_enabled=False,
        explicit_unversioned_legacy_fallback=True,
    )
    _assert(
        _decision_mapping(direct)
        == {
            "allowed": True,
            "classification": "legacy_evaluation_fallback",
            "requested_purpose": "normal_evaluation",
            "mismatches": [],
            "first_mismatch": None,
            "reason": "explicit resolver-disabled unversioned legacy evaluation fallback is permitted",
            "required_acknowledgement": None,
            "next_action": "strict_legacy_state_dict_inventory_validation",
        },
        "frozen V2 metadata-free fallback decision drift",
    )

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        legacy = root / "legacy"
        legacy.mkdir()
        calls = {"legacy": 0, "native": 0, "torch": 0}
        sentinel = object()

        def native_none(*args: Any, **kwargs: Any) -> None:
            calls["native"] += 1
            return None

        def legacy_sentinel(*args: Any, **kwargs: Any) -> object:
            calls["legacy"] += 1
            return sentinel

        def torch_blocked(*args: Any, **kwargs: Any) -> Any:
            calls["torch"] += 1
            raise AssertionError("legacy routing test reached torch.load")

        with (
            mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=native_none),
            mock.patch.object(LOAD, "_legacy_load", side_effect=legacy_sentinel),
            mock.patch.object(LOAD.torch, "load", side_effect=torch_blocked),
        ):
            result = LOAD.load_assignment_checkpoint(
                checkpoint_directory=legacy,
                purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
                entry_purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
                current_manifest=_v2_manifest(A4A.V2_LEGACY_MAPPING),
                actor_modules=(),
                allow_unversioned_legacy_fallback=True,
            )
        _assert(result is sentinel, "supported V2 legacy route result")
        _assert(calls == {"legacy": 1, "native": 1, "torch": 0}, "supported V2 legacy route counts")

        event_expectation = root / "event_expectation"
        event_expectation.mkdir()
        calls = {"legacy": 0, "native": 0, "torch": 0}
        with (
            mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=native_none),
            mock.patch.object(LOAD, "_legacy_load", side_effect=legacy_sentinel),
            mock.patch.object(LOAD.torch, "load", side_effect=torch_blocked),
        ):
            _expect_error(
                lambda: LOAD.load_assignment_checkpoint(
                    checkpoint_directory=event_expectation,
                    purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
                    entry_purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
                    current_manifest=_v3_mapping(),
                    actor_modules=(),
                    allow_unversioned_legacy_fallback=True,
                ),
                LOAD.AssignmentCheckpointError,
            )
        _assert(calls == {"legacy": 0, "native": 0, "torch": 0}, "metadata-free V3 expectation reached fallback")

        run_root = root / "native_run"
        selected_child = run_root / "models"
        selected_child.mkdir(parents=True)
        _write_native_pair(run_root, A4A.V2_LEGACY_MAPPING)
        calls = {"legacy": 0, "native": 0, "torch": 0}
        with (
            mock.patch.object(LOAD, "_read_native_checkpoint", side_effect=native_none),
            mock.patch.object(LOAD, "_legacy_load", side_effect=legacy_sentinel),
            mock.patch.object(LOAD.torch, "load", side_effect=torch_blocked),
        ):
            _expect_error(
                lambda: LOAD.load_assignment_checkpoint(
                    checkpoint_directory=selected_child,
                    purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
                    entry_purpose=GUARD.AssignmentCheckpointEntryPurpose.LOAD_EVALUATION,
                    current_manifest=_v2_manifest(A4A.V2_LEGACY_MAPPING),
                    actor_modules=(),
                    allow_unversioned_legacy_fallback=True,
                ),
                LOAD.AssignmentCheckpointMetadataError,
                "run-root native metadata exists",
                "legacy fallback is forbidden",
            )
        _assert(calls == {"legacy": 0, "native": 0, "torch": 0}, "root authority fallback bypass")


def test_offline_audit_v3_metadata_only_output() -> None:
    tensor_io_calls = {"load": 0, "save": 0}

    def blocked_load(*args: Any, **kwargs: Any) -> Any:
        tensor_io_calls["load"] += 1
        raise AssertionError("offline semantic audit reached torch.load")

    def blocked_save(*args: Any, **kwargs: Any) -> Any:
        tensor_io_calls["save"] += 1
        raise AssertionError("offline semantic audit reached torch.save")

    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "v3_interface"
        _write_native_pair(directory, _v3_mapping())
        with (
            mock.patch.object(LOAD.torch, "load", side_effect=blocked_load),
            mock.patch.object(LOAD.torch, "save", side_effect=blocked_save),
        ):
            report = AUDIT.audit_assignment_checkpoint_semantic_metadata(directory)
        expected = {
            "metadata_mode": "both_present",
            "manifest_version": V3.MANIFEST_FORMAT_VERSION,
            "manifest_kind": V3.AssignmentCheckpointManifestKind.INTERFACE_SEMANTIC_DESCRIPTOR.value,
            "semantic_family": "v3",
            "requested_purpose": "offline_audit",
            "fingerprint_verified": True,
            "stored_fingerprint": V3_INTERFACE_SHA256,
            "semantic_allowed": True,
            "weight_io_authorized": False,
            "fallback_mode": None,
            "interface_valid": True,
            "interface_status": "interface-valid",
            "runtime_ready": False,
            "runtime_status": "runtime-not-ready",
            "checkpoint_ready": False,
            "weight_status": "weight-unauthorized",
        }
        for key, value in expected.items():
            _assert(report.get(key) == value, f"offline V3 audit field {key}")
        _assert(
            report.get("decision_classification") == "interface_audit_valid_not_runtime_ready",
            "offline V3 audit classification",
        )

        expectations = AUDIT.AuditExpectations(
            exp_name="a4b_pure_v3_interface",
            algorithm="happo",
            seed=0,
            num_envs=1,
            num_agents=1,
            num_tasks=1,
            episode_length=1,
            configured_num_env_steps=1,
            final_step=1,
            rollouts=1,
            log_points=1,
            save_interval=1,
            log_interval=1,
            profile="event_gated_local_mrta",
            actor_obs_width=1,
            shared_obs_width=1,
            action_width=1,
            raw_noop_id=0,
        )
        issues = AUDIT._Issues()
        with (
            mock.patch.object(LOAD.torch, "load", side_effect=blocked_load),
            mock.patch.object(LOAD.torch, "save", side_effect=blocked_save),
        ):
            checkpoint_audit = AUDIT._audit_checkpoints(directory, expectations, issues)
        _assert(
            [item["code"] for item in issues.errors]
            == ["v3_interface_not_checkpoint_ready"],
            "V3 checkpoint audit issue classification",
        )
        _assert(not issues.warnings, "V3 checkpoint audit emitted warnings")
        _assert(
            checkpoint_audit["run_root_contract"]["semantic_guard"]["interface_status"]
            == "interface-valid",
            "V3 checkpoint audit lost interface validity",
        )
        for child in ("best_model", "final_models"):
            _assert(
                checkpoint_audit[child]["audit_mode"]
                == "not-applicable-v3-interface-only",
                f"V3 checkpoint audit {child} applicability",
            )
            _assert(
                checkpoint_audit[child]["artifact_hashes"] == [],
                f"V3 checkpoint audit {child} artifact hashes",
            )
        _assert(
            checkpoint_audit["generation_order"]["minimum_result"]
            == "NOT_APPLICABLE_V3_INTERFACE_ONLY",
            "V3 checkpoint audit generation applicability",
        )
        _assert(
            checkpoint_audit["legacy_or_temp_scan"]["result"]
            == "NOT_APPLICABLE_V3_INTERFACE_ONLY",
            "V3 checkpoint audit artifact-scan applicability",
        )

        invalid_audits: list[tuple[str, Path]] = []
        fingerprint_mismatch = Path(temp) / "audit_fingerprint_mismatch"
        _write_native_pair(fingerprint_mismatch, _v3_mapping(), fingerprint="a" * 64)
        invalid_audits.append(("fingerprint mismatch", fingerprint_mismatch))

        unknown = Path(temp) / "audit_unknown_version"
        _write_raw_pair(
            unknown,
            {
                **_v3_mapping(),
                "manifest_format_version": "assignment_checkpoint_contract_v999",
            },
        )
        invalid_audits.append(("unknown version", unknown))

        ready = Path(temp) / "audit_ready_claim"
        _write_raw_pair(
            ready,
            {
                **_v3_mapping(),
                "manifest_kind": V3.AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST.value,
            },
        )
        invalid_audits.append(("V3 ready claim", ready))

        partial = Path(temp) / "audit_partial_pair"
        partial.mkdir()
        (partial / GUARD.CONTRACT_MANIFEST_FILE).write_bytes(
            DISPATCH.canonical_assignment_checkpoint_manifest_bytes(_v3_mapping()) + b"\n"
        )
        invalid_audits.append(("partial metadata pair", partial))

        with (
            mock.patch.object(LOAD.torch, "load", side_effect=blocked_load),
            mock.patch.object(LOAD.torch, "save", side_effect=blocked_save),
        ):
            for label, invalid_directory in invalid_audits:
                _expect_error(
                    lambda invalid_directory=invalid_directory: (
                        AUDIT.audit_assignment_checkpoint_semantic_metadata(
                            invalid_directory
                        )
                    ),
                    Exception,
                )
        _assert(
            tensor_io_calls == {"load": 0, "save": 0},
            "offline audit fail-closed cases reached tensor I/O",
        )

        v2_directory = Path(temp) / "v2_contract_c"
        _write_native_pair(v2_directory, A4A.V2_CONTRACT_C_MAPPING)
        v2_report = AUDIT.audit_assignment_checkpoint_semantic_metadata(v2_directory)
        _assert(v2_report["semantic_family"] == "v2", "offline V2 family")
        _assert(v2_report["semantic_allowed"], "offline V2 structural semantics")
        _assert(not v2_report["weight_io_authorized"], "offline V2 must not authorize weights")
        _assert(v2_report["interface_status"] == "not-applicable", "offline V2 interface wording")


def _logger_state() -> tuple[Any, ...]:
    return tuple(
        sorted(
            (
                name,
                type(value).__name__,
                getattr(value, "level", None),
                getattr(value, "propagate", None),
                getattr(value, "disabled", None),
                tuple(id(handler) for handler in getattr(value, "handlers", ())),
            )
            for name, value in logging.Logger.manager.loggerDict.items()
        )
    )


def test_side_effect_snapshots_and_clean_child_import() -> None:
    cwd = Path.cwd()
    environment = dict(os.environ)
    python_rng = random.getstate()
    torch_rng = LOAD.torch.random.get_rng_state().clone()
    sys_path = tuple(sys.path)
    root_handlers = tuple(logging.getLogger().handlers)
    root_level = logging.getLogger().level
    named_loggers = _logger_state()
    modules_before = set(sys.modules)
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "metadata"
        _write_native_pair(directory, _v3_mapping())

        v3_module = sys.modules[f"{PACKAGE}.assignment_checkpoint_contract_v3"]
        with mock.patch.object(
            v3_module,
            "__file__",
            str(Path(temp) / "stale" / "assignment_checkpoint_contract_v3.py"),
        ):
            _expect_error(
                AUDIT._load_canonical_checkpoint_entry_guard,
                AUDIT.AuditPreflightError,
                "unexpected source",
            )

        def blocked(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("side-effect test reached checkpoint tensor I/O")

        with (
            mock.patch.object(LOAD.torch, "load", side_effect=blocked),
            mock.patch.object(LOAD.torch, "save", side_effect=blocked),
        ):
            result = GUARD.read_and_evaluate_checkpoint_entry_guard(
                checkpoint_directory=directory,
                purpose=GUARD.AssignmentCheckpointEntryPurpose.OFFLINE_AUDIT,
            )
            report = AUDIT.audit_assignment_checkpoint_semantic_metadata(directory)
        _assert(result.semantic_allowed and not result.weight_io_authorized, "side-effect guard result")
        _assert(report["interface_status"] == "interface-valid", "side-effect audit result")

    _assert(Path.cwd() == cwd, "cwd changed")
    _assert(dict(os.environ) == environment, "environment changed")
    _assert(random.getstate() == python_rng, "Python RNG changed")
    _assert(LOAD.torch.equal(LOAD.torch.random.get_rng_state(), torch_rng), "torch RNG changed")
    _assert(tuple(sys.path) == sys_path, "sys.path changed")
    _assert(tuple(logging.getLogger().handlers) == root_handlers, "root logger handlers changed")
    _assert(logging.getLogger().level == root_level, "root logger level changed")
    _assert(_logger_state() == named_loggers, "named logger state changed")
    new_modules = set(sys.modules) - modules_before
    _assert(
        not any(
            name.startswith(("omni", "isaaclab.app", "harl"))
            or "scan_mobile_manipulator_env" in name
            or "assignment_harl" in name
            for name in new_modules
        ),
        f"runtime/model module imported: {sorted(new_modules)!r}",
    )

    child = f'''
import contextlib,importlib.util,io,json,logging,os,pathlib,random,sys
import torch
path=pathlib.Path({str(Path(__file__).resolve())!r})
cwd=os.getcwd(); env=dict(os.environ); syspath=tuple(sys.path)
handlers=tuple(logging.getLogger().handlers); level=logging.getLogger().level
def logger_state():
    return tuple(sorted((name,type(value).__name__,getattr(value,"level",None),
      getattr(value,"propagate",None),getattr(value,"disabled",None),
      tuple(id(handler) for handler in getattr(value,"handlers",())))
      for name,value in logging.Logger.manager.loggerDict.items()))
named=logger_state(); py=random.getstate(); trng=torch.random.get_rng_state().clone()
modules=set(sys.modules); files=tuple(pathlib.Path.cwd().iterdir())
def blocked(*args,**kwargs): raise AssertionError("forbidden model/tensor operation")
out=io.StringIO(); err=io.StringIO(); old=sys.dont_write_bytecode
with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err), \
     contextlib.ExitStack() as stack:
    stack.enter_context(__import__("unittest.mock").mock.patch.object(torch,"load",side_effect=blocked))
    stack.enter_context(__import__("unittest.mock").mock.patch.object(torch,"save",side_effect=blocked))
    stack.enter_context(__import__("unittest.mock").mock.patch.object(torch.nn.Module,"load_state_dict",side_effect=blocked))
    stack.enter_context(__import__("unittest.mock").mock.patch.object(torch.nn.Module,"__init__",side_effect=blocked))
    spec=importlib.util.spec_from_file_location("_a4b_clean_child_suite",path)
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module
    try:
        sys.dont_write_bytecode=True; spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode=old
new=set(sys.modules)-modules
payload={{"stdout":out.getvalue(),"stderr":err.getvalue(),
 "cwd":os.getcwd()==cwd,"env":dict(os.environ)==env,"path":tuple(sys.path)==syspath,
 "handlers":tuple(logging.getLogger().handlers)==handlers,"level":logging.getLogger().level==level,
 "named":logger_state()==named,"python_rng":random.getstate()==py,
 "torch_rng":torch.equal(torch.random.get_rng_state(),trng),
 "files":tuple(pathlib.Path.cwd().iterdir())==files,
 "forbidden":not any(name.startswith(("omni","isaaclab.app","harl")) or
   "scan_mobile_manipulator_env" in name or "assignment_harl" in name for name in new),
 "app_launcher":"isaaclab.app" not in sys.modules}}
print(json.dumps(payload,sort_keys=True))
'''
    with tempfile.TemporaryDirectory() as temp:
        completed = subprocess.run(
            [sys.executable, "-c", child],
            cwd=temp,
            capture_output=True,
            text=True,
            check=False,
        )
    _assert(completed.returncode == 0, completed.stderr)
    payload = json.loads(completed.stdout)
    for key, value in payload.items():
        if key in {"stdout", "stderr"}:
            _assert(value == "", f"clean child {key}")
        else:
            _assert(value is True, f"clean child side effect: {key}")


TESTS = (
    ("native_metadata_pair_states_and_strict_corruption", test_native_metadata_pair_states_and_strict_corruption),
    ("v2_direct_guard_full_decision_equivalence", test_v2_direct_guard_full_decision_equivalence),
    ("v2_entry_and_compatibility_purpose_matrix", test_v2_entry_and_compatibility_purpose_matrix),
    ("v3_interface_golden_audit_only_and_weight_denials", test_v3_interface_golden_audit_only_and_weight_denials),
    ("blocked_v3_save_precedes_inventory_and_artifacts", test_blocked_v3_save_precedes_inventory_and_artifacts),
    ("load_guard_precedes_native_tensor_path", test_load_guard_precedes_native_tensor_path),
    ("legacy_fallback_non_expansion_and_run_root_authority", test_legacy_fallback_non_expansion_and_run_root_authority),
    ("offline_audit_v3_metadata_only_output", test_offline_audit_v3_metadata_only_output),
    ("playback_and_diagnostics_ast_guard_routing", test_playback_and_diagnostics_ast_guard_routing),
    ("side_effect_snapshots_and_clean_child_import", test_side_effect_snapshots_and_clean_child_import),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_checkpoint_entry_guard_integration",
        "passed": passed,
        "total": len(results),
        "v3_canonical_byte_length": V3_CANONICAL_BYTE_LENGTH,
        "v3_interface_sha256": V3_INTERFACE_SHA256,
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        for item in results:
            print(f"{item['status'].upper()}: {item['name']}" + (f" - {item['error']}" if "error" in item else ""))
        print(f"{passed}/{len(results)} tests passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
