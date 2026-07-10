# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Project-local assignment checkpoint manifest construction and atomic saving."""

import hashlib
import json
import os
import re
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

try:
    from .assignment_checkpoint_contract import (
        ArtifactFileInventoryEntry,
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        ContractValidationError,
        MANIFEST_FORMAT_VERSION,
        StateDictTensorInventoryEntry,
        VALIDATED_WEIGHT_CONTINUATION_CANDIDATE,
        canonical_manifest_bytes,
        compute_manifest_sha256,
        compute_tensor_inventory_sha256,
        verify_manifest_sha256,
    )
    from .assignment_lifecycle_training_contract import (
        FEED_FORWARD_GENERATOR,
        resolve_installed_harl_actor_buffer_generator,
    )
    from .assignment_value_normalizer_checkpoint import (
        build_value_normalizer_contract,
        validate_value_normalizer_checkpoint_state,
    )
except ImportError:  # Allows direct lightweight tests with this directory on sys.path.
    from assignment_checkpoint_contract import (  # type: ignore
        ArtifactFileInventoryEntry,
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        ContractValidationError,
        MANIFEST_FORMAT_VERSION,
        StateDictTensorInventoryEntry,
        VALIDATED_WEIGHT_CONTINUATION_CANDIDATE,
        canonical_manifest_bytes,
        compute_manifest_sha256,
        compute_tensor_inventory_sha256,
        verify_manifest_sha256,
    )
    from assignment_lifecycle_training_contract import (  # type: ignore
        FEED_FORWARD_GENERATOR,
        resolve_installed_harl_actor_buffer_generator,
    )
    from assignment_value_normalizer_checkpoint import (  # type: ignore
        build_value_normalizer_contract,
        validate_value_normalizer_checkpoint_state,
    )


CONTRACT_MANIFEST_FILE = "assignment_contract_manifest.json"
CONTRACT_FINGERPRINT_FILE = "assignment_contract_fingerprint.txt"
TRAINING_STATE_MANIFEST_FILE = "assignment_training_state_manifest.json"

CHECKPOINT_KINDS = frozenset({"regular", "best", "episode_snapshot", "final"})
NATIVE_ASSIGNMENT_PROFILES = frozenset({"legacy", "lifecycle_contract_c"})
NON_TRAINING_ASSIGNMENT_PROFILES = frozenset({"lifecycle_ablation", "diagnostics_hidden_state"})

FAIL_AFTER_MARKER_INVALIDATION = "after_completion_marker_invalidation"
FAIL_AFTER_FIRST_ACTOR = "after_first_actor_save"
FAIL_AFTER_ALL_ACTORS = "after_all_actor_saves"
FAIL_AFTER_CRITIC = "after_critic_save"
FAIL_AFTER_VALUE_NORMALIZER = "after_value_normalizer_save"
FAIL_AFTER_CHILD_CONTRACT = "after_child_contract_metadata_write"

_EPISODE_DIRECTORY = re.compile(r"^episode_(\d+)$")


class AssignmentCheckpointSaveError(RuntimeError):
    """Raised when a native assignment checkpoint cannot be saved safely."""


@dataclass(frozen=True)
class AssignmentCheckpointRuntimeState:
    """Effective runtime values used to construct one immutable contract manifest."""

    wrapper_schema_manifest: Mapping[str, Any]
    wrapper_observation_layout: Mapping[str, Any]
    profile_name: str
    algorithm_name: str
    harl_state_type: str
    ordered_agent_names: tuple[str, ...]
    actor_input_dimensions_by_agent: Mapping[str, int]
    critic_input_dimension: int
    actor_action_dimensions_by_agent: Mapping[str, int]
    actor_class: str
    critic_class: str
    action_distribution_class: str
    actor_hidden_sizes: tuple[int, ...]
    critic_hidden_sizes: tuple[int, ...]
    activation: str
    feature_normalization: bool
    share_param: bool
    number_of_actor_networks: int
    ordered_actor_network_names: tuple[str, ...]
    critic_architecture: str
    recurrent_n: int
    initialization_method: str
    action_gain: float
    use_recurrent_policy: bool
    use_naive_recurrent_policy: bool
    actor_buffer_generator: str
    optimizer_class: str
    actor_learning_rate: float
    critic_learning_rate: float
    optimizer_epsilon: float
    weight_decay: float
    ppo_epochs: int
    actor_minibatches: int
    critic_minibatches: int
    clip_coefficient: float
    value_loss_coefficient: float
    entropy_coefficient: float
    gradient_clipping_enabled: bool
    max_gradient_norm: float
    gamma: float
    gae_lambda: float
    value_norm_enabled: bool
    value_normalizer_contract: Mapping[str, Any]
    proper_time_limits: bool
    episode_length: int
    rollout_thread_count: int
    serialization_mode: str = "state_dict"


@dataclass(frozen=True)
class AssignmentCheckpointSaveResult:
    checkpoint_directory: Path
    checkpoint_generation: int
    checkpoint_kind: str
    training_state_manifest: AssignmentTrainingStateManifest


def _feature_entry(
    name: str,
    shape: Sequence[int],
    *,
    source: str,
    snapshot_timing: str,
) -> dict[str, Any]:
    return {
        "name": str(name),
        "source": str(source),
        "shape": [int(value) for value in shape],
        "dtype": "float32",
        "normalization": "schema_defined",
        "snapshot_timing": snapshot_timing,
        "padding_semantics": "fixed_n_no_padding",
    }


def _require_ordered_mapping(
    value: Mapping[str, Any],
    expected_names: tuple[str, ...],
    *,
    field: str,
) -> tuple[Any, ...]:
    if tuple(value.keys()) != expected_names:
        raise AssignmentCheckpointSaveError(
            f"{field} keys/order must equal ordered agents {expected_names}, got {tuple(value.keys())}"
        )
    return tuple(value[name] for name in expected_names)


def _require_equal(values: Sequence[Any], *, field: str) -> Any:
    if not values:
        raise AssignmentCheckpointSaveError(f"{field} must not be empty")
    first = values[0]
    if any(value != first for value in values[1:]):
        raise AssignmentCheckpointSaveError(f"{field} must be identical across actors, got {tuple(values)!r}")
    return first


def build_assignment_checkpoint_contract_manifest(
    runtime: AssignmentCheckpointRuntimeState,
    *,
    allow_evaluation_only_profile: bool = False,
) -> AssignmentCheckpointContractManifest:
    """Build and validate the native assignment contract from effective runtime values."""

    profile = str(runtime.profile_name).strip().lower()
    evaluation_only_profile = profile == "lifecycle_ablation"
    if profile not in NATIVE_ASSIGNMENT_PROFILES and not (
        allow_evaluation_only_profile and evaluation_only_profile
    ):
        raise AssignmentCheckpointSaveError(
            f"native assignment checkpoint metadata is not supported for profile {profile!r}"
        )
    if runtime.serialization_mode != "state_dict":
        raise AssignmentCheckpointSaveError("native assignment checkpoint metadata requires state_dict serialization")
    if str(runtime.algorithm_name).strip().lower() != "happo":
        raise AssignmentCheckpointSaveError("native assignment checkpoint v1 supports HAPPO only")

    schema = dict(runtime.wrapper_schema_manifest)
    layout = dict(runtime.wrapper_observation_layout)
    names = tuple(str(name) for name in runtime.ordered_agent_names)
    if not names or len(names) != len(set(names)):
        raise AssignmentCheckpointSaveError("ordered assignment agent identities must be unique and non-empty")
    if tuple(runtime.ordered_actor_network_names) != names:
        raise AssignmentCheckpointSaveError("actor network order must equal wrapper agent order")
    if runtime.number_of_actor_networks != len(names):
        raise AssignmentCheckpointSaveError(
            "native assignment checkpoint v1 requires one independent actor network per ordered agent"
        )
    if runtime.share_param:
        raise AssignmentCheckpointSaveError(
            "native assignment checkpoint v1 requires share_param=False and independent actor artifacts"
        )

    if str(schema.get("profile_name")) != profile:
        raise AssignmentCheckpointSaveError("wrapper profile and resolved runtime profile differ")
    m = int(schema.get("M", -1))
    n = int(schema.get("N", -1))
    if m != len(names) or int(schema.get("action_dimension", -1)) != n + 1:
        raise AssignmentCheckpointSaveError("wrapper M/N/action dimensions are internally inconsistent")

    wrapper_actor_dims = schema.get("actor_dimension_by_agent")
    if not isinstance(wrapper_actor_dims, Mapping):
        raise AssignmentCheckpointSaveError("wrapper manifest has no ordered actor_dimension_by_agent mapping")
    wrapper_actor_values = _require_ordered_mapping(
        wrapper_actor_dims,
        names,
        field="wrapper actor dimensions",
    )
    runtime_actor_values = _require_ordered_mapping(
        runtime.actor_input_dimensions_by_agent,
        names,
        field="runtime actor input dimensions",
    )
    if wrapper_actor_values != runtime_actor_values:
        raise AssignmentCheckpointSaveError(
            f"wrapper actor dimensions {wrapper_actor_values} do not match constructed actors {runtime_actor_values}"
        )
    actor_dimension = int(_require_equal(runtime_actor_values, field="actor input dimensions"))
    if int(schema.get("actor_dimension", -1)) != actor_dimension:
        raise AssignmentCheckpointSaveError("wrapper scalar actor dimension differs from constructed actors")
    if int(schema.get("shared_dimension", -1)) != int(runtime.critic_input_dimension):
        raise AssignmentCheckpointSaveError(
            "wrapper shared dimension differs from constructed critic input dimension"
        )
    runtime_action_values = _require_ordered_mapping(
        runtime.actor_action_dimensions_by_agent,
        names,
        field="runtime actor action dimensions",
    )
    action_dimension = int(_require_equal(runtime_action_values, field="actor action dimensions"))
    if action_dimension != int(schema["action_dimension"]):
        raise AssignmentCheckpointSaveError("wrapper action dimension differs from actor action heads")

    selected_generator = resolve_installed_harl_actor_buffer_generator(
        use_recurrent_policy=runtime.use_recurrent_policy,
        use_naive_recurrent_policy=runtime.use_naive_recurrent_policy,
    )
    if selected_generator != runtime.actor_buffer_generator:
        raise AssignmentCheckpointSaveError(
            f"runtime actor-buffer generator mismatch: expected {selected_generator}, "
            f"got {runtime.actor_buffer_generator}"
        )
    if profile in {"lifecycle_contract_c", "lifecycle_ablation"}:
        if runtime.harl_state_type != "EP":
            raise AssignmentCheckpointSaveError("lifecycle contract v1 requires HARL EP state")
        if runtime.use_recurrent_policy or runtime.use_naive_recurrent_policy:
            raise AssignmentCheckpointSaveError(
                "lifecycle contract v1 requires both recurrent flags to be false"
            )
        if selected_generator != FEED_FORWARD_GENERATOR:
            raise AssignmentCheckpointSaveError(
                "lifecycle contract v1 requires feed_forward_generator_actor"
            )

    row_fields = tuple(str(value) for value in schema.get("actor_task_row_order", ()))
    tail_fields = tuple(str(value) for value in schema.get("actor_tail_field_order", ()))
    raw_dim = int(layout.get("raw_observation_dim", -1))
    row_dim = int(layout.get("viewpoint_row_dim", -1))
    noop_dim = int(layout.get("noop_context_dim", -1))
    previous_dim = int(layout.get("previous_assignment_one_hot_dim", -1))
    dynamic_fields = tuple(str(value) for value in layout.get("dynamic_scalar_fields", ()))
    covered_dim = int(layout.get("covered_vector_dim", -1))
    if row_dim != len(row_fields) or covered_dim != n:
        raise AssignmentCheckpointSaveError("wrapper observation row/covered dimensions are inconsistent")
    expected_actor_dimension = raw_dim + n * row_dim + noop_dim + previous_dim + len(dynamic_fields) + covered_dim
    if expected_actor_dimension != actor_dimension:
        raise AssignmentCheckpointSaveError(
            f"wrapper observation layout totals {expected_actor_dimension}, actor input is {actor_dimension}"
        )

    actor_features = [
        _feature_entry(
            "raw_env_observation",
            [raw_dim],
            source="ScanMobileManipulatorEnv._get_observations",
            snapshot_timing="next_policy_decision",
        ),
        _feature_entry(
            "per_task_rows",
            [n, row_dim],
            source="AssignmentHarlWrapper",
            snapshot_timing="next_policy_decision",
        ),
        _feature_entry(
            "noop_context",
            [noop_dim],
            source="AssignmentHarlWrapper",
            snapshot_timing="next_policy_decision",
        ),
        _feature_entry(
            "previous_assignment_one_hot",
            [previous_dim],
            source="AssignmentHarlWrapper",
            snapshot_timing="next_policy_decision",
        ),
        _feature_entry(
            "dynamic_scalars",
            [len(dynamic_fields)],
            source="AssignmentHarlWrapper",
            snapshot_timing="next_policy_decision",
        ),
        _feature_entry(
            "covered_vector",
            [covered_dim],
            source="AssignmentHarlWrapper",
            snapshot_timing="next_policy_decision",
        ),
    ]
    shared_blocks_raw = schema.get("shared_ordered_blocks")
    if not isinstance(shared_blocks_raw, Sequence) or not shared_blocks_raw:
        raise AssignmentCheckpointSaveError("wrapper shared ordered blocks are missing")
    shared_blocks = []
    for block in shared_blocks_raw:
        if not isinstance(block, Mapping) or "name" not in block or "shape" not in block:
            raise AssignmentCheckpointSaveError("wrapper shared ordered block is malformed")
        shared_blocks.append(
            _feature_entry(
                str(block["name"]),
                block["shape"],
                source="AssignmentHarlWrapper.shared_observation",
                snapshot_timing="next_policy_decision",
            )
        )

    if profile in {"lifecycle_contract_c", "lifecycle_ablation"}:
        resolver_contract = (
            "assignment_lifecycle_resolver_contract_c_v1"
            if profile == "lifecycle_contract_c"
            else "disabled"
        )
        snapshot_contract = str(schema["snapshot_contract_version"])
        sequence_version = "lifecycle_feed_forward_v1"
        sequence_mode = "feed_forward"
    else:
        resolver_contract = "disabled"
        snapshot_contract = "legacy_no_snapshot_v1"
        sequence_version = (
            "legacy_resolved_feed_forward_v1"
            if selected_generator == FEED_FORWARD_GENERATOR
            else "legacy_resolved_recurrent_v1"
        )
        sequence_mode = (
            "feed_forward"
            if selected_generator == FEED_FORWARD_GENERATOR
            else "naive_recurrent"
            if runtime.use_naive_recurrent_policy and not runtime.use_recurrent_policy
            else "recurrent"
        )

    mapping = {
        "manifest_format_version": MANIFEST_FORMAT_VERSION,
        "identity": {
            "profile_name": profile,
            "training_time_profile": profile,
            "algorithm_name": str(runtime.algorithm_name).lower(),
            "harl_state_type": runtime.harl_state_type,
            "harl_shared_observation_mode": (
                "environment_provided" if runtime.harl_state_type == "EP" else "feature_pruned"
            ),
            "serialization_mode": runtime.serialization_mode,
        },
        "scale": {
            "M": m,
            "N": n,
            "num_agents": len(names),
            "ordered_agent_names": list(names),
        },
        "actor_schema": {
            "actor_schema_version": schema["actor_schema_version"],
            "actor_dimension": actor_dimension,
            "actor_dimension_by_agent": {
                name: int(runtime.actor_input_dimensions_by_agent[name]) for name in names
            },
            "actor_ordered_feature_manifest": actor_features,
            "actor_task_row_field_order": list(row_fields),
            "actor_tail_field_order": list(tail_fields),
        },
        "shared_schema": {
            "shared_schema_version": schema["shared_schema_version"],
            "shared_dimension": int(runtime.critic_input_dimension),
            "shared_construction_mode": schema["shared_construction_mode"],
            "shared_ordered_blocks": shared_blocks,
            "critic_budget_schema_version": schema["critic_budget_schema_version"],
        },
        "action_contract": {
            "action_space_type": "Discrete",
            "action_dimension": action_dimension,
            "target_action_min": 0,
            "target_action_max": n - 1,
            "noop_raw_id": int(schema["noop_raw_id"]),
            "noop_decoded_value": int(schema["noop_decoded_value"]),
        },
        "lifecycle_behavior_contract": {
            "snapshot_contract_version": snapshot_contract,
            "resolver_contract_version": resolver_contract,
            "mask_contract_version": schema["mask_contract_version"],
            "budget_release_contract_version": schema["budget_release_contract"],
            "legacy_guardrail_profile": schema["legacy_guardrail_profile"],
            "ownership_contract_version": "exclusive_owner_active_equivalence_v1",
            "arbitration_contract_version": "lowest_cost_then_robot_id_v1",
        },
        "policy_sequence_contract": {
            "policy_sequence_contract_version": sequence_version,
            "policy_sequence_mode": sequence_mode,
            "use_recurrent_policy": runtime.use_recurrent_policy,
            "use_naive_recurrent_policy": runtime.use_naive_recurrent_policy,
            "supported_actor_buffer_generator": selected_generator,
        },
        "model_structure": {
            "actor_class": runtime.actor_class,
            "critic_class": runtime.critic_class,
            "action_distribution_class": runtime.action_distribution_class,
            "actor_hidden_sizes": list(runtime.actor_hidden_sizes),
            "critic_hidden_sizes": list(runtime.critic_hidden_sizes),
            "activation": runtime.activation,
            "feature_normalization": runtime.feature_normalization,
            "share_param": runtime.share_param,
            "number_of_actor_networks": runtime.number_of_actor_networks,
            "ordered_actor_network_names": list(runtime.ordered_actor_network_names),
            "critic_architecture": runtime.critic_architecture,
            "harl_state_type": runtime.harl_state_type,
            "recurrent_n": runtime.recurrent_n,
            "initialization_method": runtime.initialization_method,
            "action_gain": runtime.action_gain,
        },
        "training_contract": {
            "optimizer_class": runtime.optimizer_class,
            "actor_learning_rate": runtime.actor_learning_rate,
            "critic_learning_rate": runtime.critic_learning_rate,
            "optimizer_epsilon": runtime.optimizer_epsilon,
            "weight_decay": runtime.weight_decay,
            "ppo_epochs": runtime.ppo_epochs,
            "actor_minibatches": runtime.actor_minibatches,
            "critic_minibatches": runtime.critic_minibatches,
            "clip_coefficient": runtime.clip_coefficient,
            "value_loss_coefficient": runtime.value_loss_coefficient,
            "entropy_coefficient": runtime.entropy_coefficient,
            "gradient_clipping_enabled": runtime.gradient_clipping_enabled,
            "max_gradient_norm": runtime.max_gradient_norm,
            "gamma": runtime.gamma,
            "gae_lambda": runtime.gae_lambda,
            "value_norm_enabled": runtime.value_norm_enabled,
            "value_normalizer_contract": dict(runtime.value_normalizer_contract),
            "proper_time_limits": runtime.proper_time_limits,
            "episode_length": runtime.episode_length,
            "rollout_thread_count": runtime.rollout_thread_count,
        },
    }
    try:
        return AssignmentCheckpointContractManifest.from_mapping(mapping)
    except ContractValidationError as exc:
        raise AssignmentCheckpointSaveError(f"runtime checkpoint manifest is invalid: {exc}") from exc


def build_tensor_inventory_from_state_dict(
    state_dict: Mapping[str, Any],
    *,
    artifact_name: str,
) -> tuple[StateDictTensorInventoryEntry, ...]:
    """Inventory every state-dict entry without loading or silently dropping values."""

    if not isinstance(state_dict, Mapping):
        raise AssignmentCheckpointSaveError(f"{artifact_name} state_dict must be a mapping")
    entries: list[StateDictTensorInventoryEntry] = []
    for key, value in state_dict.items():
        if not isinstance(key, str) or not key:
            raise AssignmentCheckpointSaveError(f"{artifact_name} contains a non-string or empty state key")
        if not isinstance(value, torch.Tensor):
            raise AssignmentCheckpointSaveError(
                f"{artifact_name} state entry {key!r} has unsupported non-tensor type "
                f"{type(value).__name__}; no entry may be silently omitted"
            )
        entries.append(
            StateDictTensorInventoryEntry(
                key=key,
                shape=tuple(int(dim) for dim in value.shape),
                dtype=str(value.dtype),
            )
        )
    if not entries:
        raise AssignmentCheckpointSaveError(f"{artifact_name} state_dict must not be empty")
    return tuple(sorted(entries, key=lambda entry: entry.key))


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.assignment-tmp-{uuid.uuid4().hex}")
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_torch_save(path: Path, state_dict: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.assignment-tmp-{uuid.uuid4().hex}")
    try:
        with temporary.open("wb") as stream:
            torch.save(state_dict, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except (AttributeError, OSError):
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def compute_file_sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> tuple[int, str]:
    """Hash final file bytes in bounded chunks and reject concurrent file changes."""

    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise AssignmentCheckpointSaveError(f"artifact changed while hashing: {path.name}")
    return after.st_size, digest.hexdigest()


def _training_state_bytes(manifest: AssignmentTrainingStateManifest) -> bytes:
    payload = json.dumps(
        manifest.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return payload + b"\n"


def _read_contract_pair(directory: Path) -> tuple[AssignmentCheckpointContractManifest, bytes, bytes] | None:
    manifest_path = directory / CONTRACT_MANIFEST_FILE
    fingerprint_path = directory / CONTRACT_FINGERPRINT_FILE
    manifest_exists = manifest_path.exists()
    fingerprint_exists = fingerprint_path.exists()
    if manifest_exists != fingerprint_exists:
        raise AssignmentCheckpointSaveError(
            f"partial assignment contract metadata in {directory}: manifest/fingerprint must both exist"
        )
    if not manifest_exists:
        return None
    manifest_bytes = manifest_path.read_bytes()
    fingerprint_bytes = fingerprint_path.read_bytes()
    try:
        mapping = json.loads(manifest_bytes.decode("utf-8"))
        manifest = AssignmentCheckpointContractManifest.from_mapping(mapping)
    except (UnicodeDecodeError, json.JSONDecodeError, ContractValidationError) as exc:
        raise AssignmentCheckpointSaveError(f"invalid assignment contract manifest in {directory}: {exc}") from exc
    expected_manifest_bytes = canonical_manifest_bytes(manifest) + b"\n"
    if manifest_bytes != expected_manifest_bytes:
        raise AssignmentCheckpointSaveError(
            f"assignment contract manifest in {directory} is not canonical UTF-8 JSON plus LF"
        )
    expected_fingerprint = compute_manifest_sha256(manifest)
    expected_fingerprint_bytes = expected_fingerprint.encode("ascii") + b"\n"
    if fingerprint_bytes != expected_fingerprint_bytes:
        raise AssignmentCheckpointSaveError(
            f"assignment contract fingerprint file in {directory} is malformed or disagrees"
        )
    if not verify_manifest_sha256(manifest, expected_fingerprint):
        raise AssignmentCheckpointSaveError(f"assignment contract fingerprint verification failed in {directory}")
    return manifest, manifest_bytes, fingerprint_bytes


def ensure_contract_metadata_pair(
    directory: Path,
    manifest: AssignmentCheckpointContractManifest,
) -> tuple[bytes, bytes]:
    """Create or strictly validate one canonical manifest/fingerprint pair."""

    directory = Path(directory)
    expected_manifest = canonical_manifest_bytes(manifest) + b"\n"
    expected_fingerprint = compute_manifest_sha256(manifest).encode("ascii") + b"\n"
    existing = _read_contract_pair(directory)
    if existing is None:
        directory.mkdir(parents=True, exist_ok=True)
        _atomic_write_bytes(directory / CONTRACT_MANIFEST_FILE, expected_manifest)
        _atomic_write_bytes(directory / CONTRACT_FINGERPRINT_FILE, expected_fingerprint)
        return expected_manifest, expected_fingerprint
    existing_manifest, manifest_bytes, fingerprint_bytes = existing
    if canonical_manifest_bytes(existing_manifest) != canonical_manifest_bytes(manifest):
        raise AssignmentCheckpointSaveError(
            f"existing assignment contract in {directory} differs from current runtime contract"
        )
    if manifest_bytes != expected_manifest or fingerprint_bytes != expected_fingerprint:
        raise AssignmentCheckpointSaveError(f"existing assignment contract bytes differ in {directory}")
    return manifest_bytes, fingerprint_bytes


def _recognized_checkpoint_path(
    run_root: Path,
    checkpoint_directory: Path,
    checkpoint_kind: str,
    episode_or_update_index: int | None,
) -> int | None:
    run_root = run_root.resolve()
    checkpoint_directory = checkpoint_directory.resolve()
    models = (run_root / "models").resolve()
    best = (run_root / "best_model").resolve()
    if checkpoint_kind in {"regular", "final"}:
        if checkpoint_directory != models:
            raise AssignmentCheckpointSaveError(
                f"{checkpoint_kind} checkpoint must target run_root/models"
            )
        return episode_or_update_index
    if checkpoint_kind == "best":
        if checkpoint_directory != best:
            raise AssignmentCheckpointSaveError("best checkpoint must target run_root/best_model")
        return episode_or_update_index
    expected_parent = (models / "checkpoints").resolve()
    match = _EPISODE_DIRECTORY.fullmatch(checkpoint_directory.name)
    if checkpoint_directory.parent != expected_parent or match is None:
        raise AssignmentCheckpointSaveError(
            "episode_snapshot must target run_root/models/checkpoints/episode_<n>"
        )
    directory_index = int(match.group(1))
    if episode_or_update_index is not None and episode_or_update_index != directory_index:
        raise AssignmentCheckpointSaveError(
            f"episode snapshot index {episode_or_update_index} differs from directory {directory_index}"
        )
    return directory_index


def infer_assignment_checkpoint_kind(
    run_root: Path,
    checkpoint_directory: Path,
) -> tuple[str, int | None]:
    """Infer inherited HARL save calls from the three recognized child locations."""

    run_root = Path(run_root).resolve()
    checkpoint_directory = Path(checkpoint_directory).resolve()
    if checkpoint_directory == (run_root / "models").resolve():
        return "regular", None
    if checkpoint_directory == (run_root / "best_model").resolve():
        return "best", None
    parent = (run_root / "models" / "checkpoints").resolve()
    match = _EPISODE_DIRECTORY.fullmatch(checkpoint_directory.name)
    if checkpoint_directory.parent == parent and match is not None:
        return "episode_snapshot", int(match.group(1))
    raise AssignmentCheckpointSaveError(
        f"unrecognized assignment checkpoint directory {checkpoint_directory}"
    )


def _validate_child_contract_state(
    checkpoint_directory: Path,
    manifest: AssignmentCheckpointContractManifest,
) -> None:
    existing = _read_contract_pair(checkpoint_directory)
    marker_exists = (checkpoint_directory / TRAINING_STATE_MANIFEST_FILE).exists()
    if existing is None:
        if marker_exists:
            raise AssignmentCheckpointSaveError(
                "checkpoint completion marker exists without child contract metadata"
            )
        return
    existing_manifest, _, _ = existing
    if canonical_manifest_bytes(existing_manifest) != canonical_manifest_bytes(manifest):
        raise AssignmentCheckpointSaveError("checkpoint-local contract disagrees with run-root contract")
    if marker_exists:
        marker_path = checkpoint_directory / TRAINING_STATE_MANIFEST_FILE
        try:
            marker = AssignmentTrainingStateManifest.from_mapping(
                json.loads(marker_path.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ContractValidationError) as exc:
            raise AssignmentCheckpointSaveError(f"invalid existing completion marker: {exc}") from exc
        if marker.contract_fingerprint != compute_manifest_sha256(manifest):
            raise AssignmentCheckpointSaveError(
                "existing completion marker is bound to a different contract fingerprint"
            )


def _validate_existing_artifacts(
    checkpoint_directory: Path,
    expected_actor_files: set[str],
    *,
    value_norm_enabled: bool,
) -> None:
    if not checkpoint_directory.exists():
        return
    full_model_files = sorted(path.name for path in checkpoint_directory.glob("*_full.pt"))
    if full_model_files:
        raise AssignmentCheckpointSaveError(
            f"full-model artifacts conflict with native state_dict checkpoint: {full_model_files}"
        )
    actor_files = {path.name for path in checkpoint_directory.glob("actor_agent_*.pt")}
    unexpected_actor_files = sorted(actor_files - expected_actor_files)
    if unexpected_actor_files:
        raise AssignmentCheckpointSaveError(
            f"unexpected or numeric-fallback actor artifacts require a clean checkpoint directory: "
            f"{unexpected_actor_files}"
        )
    critic_files = {path.name for path in checkpoint_directory.glob("critic_agent*.pt")}
    unexpected_critic_files = sorted(critic_files - {"critic_agent.pt"})
    if unexpected_critic_files:
        raise AssignmentCheckpointSaveError(
            f"unexpected critic artifacts require a clean checkpoint directory: {unexpected_critic_files}"
        )
    value_files = {path.name for path in checkpoint_directory.glob("value_normalizer*.pt")}
    expected_value_files = {"value_normalizer.pt"} if value_norm_enabled else set()
    unexpected_value_files = sorted(value_files - expected_value_files)
    if unexpected_value_files:
        raise AssignmentCheckpointSaveError(
            f"unexpected ValueNorm artifacts require a clean checkpoint directory: {unexpected_value_files}"
        )
    value_path = checkpoint_directory / "value_normalizer.pt"
    if not value_norm_enabled and value_path.exists():
        raise AssignmentCheckpointSaveError(
            "value_normalizer.pt exists but ValueNorm is disabled; use a clean checkpoint directory"
        )


def _artifact_entry(
    *,
    role: str,
    path: Path,
    actor_identity: str | None,
    inventory: tuple[StateDictTensorInventoryEntry, ...],
) -> ArtifactFileInventoryEntry:
    file_size, file_digest = compute_file_sha256(path)
    return ArtifactFileInventoryEntry(
        artifact_role=role,
        relative_file_name=path.name,
        file_size=file_size,
        file_sha256=file_digest,
        serialization_mode="state_dict",
        actor_identity=actor_identity,
        tensor_inventory=inventory,
        tensor_inventory_sha256=compute_tensor_inventory_sha256(inventory),
    )


class AssignmentCheckpointSaveCoordinator:
    """Coordinate one complete native assignment checkpoint save operation."""

    def __init__(
        self,
        run_root: Path,
        *,
        failure_injector: Callable[[str], None] | None = None,
        event_recorder: Callable[[str], None] | None = None,
    ) -> None:
        self.run_root = Path(run_root).resolve()
        self.failure_injector = failure_injector
        self.event_recorder = event_recorder

    def _event(self, name: str) -> None:
        if self.event_recorder is not None:
            self.event_recorder(name)

    def _inject(self, point: str) -> None:
        if self.failure_injector is not None:
            self.failure_injector(point)

    def save_checkpoint(
        self,
        *,
        checkpoint_directory: Path,
        checkpoint_kind: str,
        checkpoint_generation: int,
        manifest: AssignmentCheckpointContractManifest,
        actor_state_dicts: Sequence[tuple[str, Mapping[str, Any]]],
        critic_state_dict: Mapping[str, Any],
        value_normalizer_state_dict: Mapping[str, Any] | None,
        episode_or_update_index: int | None = None,
    ) -> AssignmentCheckpointSaveResult:
        if checkpoint_kind not in CHECKPOINT_KINDS:
            raise AssignmentCheckpointSaveError(f"unsupported assignment checkpoint kind {checkpoint_kind!r}")
        if isinstance(checkpoint_generation, bool) or checkpoint_generation < 0:
            raise AssignmentCheckpointSaveError("checkpoint generation must be a non-negative integer")
        checkpoint_directory = Path(checkpoint_directory).resolve()
        effective_index = _recognized_checkpoint_path(
            self.run_root,
            checkpoint_directory,
            checkpoint_kind,
            episode_or_update_index,
        )

        expected_names = tuple(manifest.scale["ordered_agent_names"])
        supplied_names = tuple(str(name) for name, _ in actor_state_dicts)
        if supplied_names != expected_names:
            raise AssignmentCheckpointSaveError(
                f"actor state_dict identities/order {supplied_names} must equal manifest {expected_names}"
            )
        actor_files = {f"actor_agent_{name}.pt" for name in expected_names}
        actor_inventories = {
            name: build_tensor_inventory_from_state_dict(state, artifact_name=f"actor {name}")
            for name, state in actor_state_dicts
        }
        critic_inventory = build_tensor_inventory_from_state_dict(
            critic_state_dict,
            artifact_name="critic",
        )
        value_norm_enabled = bool(manifest.training_contract["value_norm_enabled"])
        if value_norm_enabled != (value_normalizer_state_dict is not None):
            raise AssignmentCheckpointSaveError(
                "ValueNorm runtime state presence does not match the immutable training contract"
            )
        if value_normalizer_state_dict is not None:
            try:
                validate_value_normalizer_checkpoint_state(
                    value_normalizer_state_dict,
                    value_normalizer_contract=manifest.training_contract["value_normalizer_contract"],
                )
            except Exception as exc:
                raise AssignmentCheckpointSaveError(
                    f"invalid ValueNorm checkpoint tensor mapping: {exc}"
                ) from exc
        value_inventory = (
            None
            if value_normalizer_state_dict is None
            else build_tensor_inventory_from_state_dict(
                value_normalizer_state_dict,
                artifact_name="value normalizer",
            )
        )

        run_manifest_bytes, run_fingerprint_bytes = ensure_contract_metadata_pair(
            self.run_root,
            manifest,
        )
        _recognized_checkpoint_path(
            self.run_root,
            checkpoint_directory,
            checkpoint_kind,
            effective_index,
        )
        _validate_child_contract_state(checkpoint_directory, manifest)
        _validate_existing_artifacts(
            checkpoint_directory,
            actor_files,
            value_norm_enabled=value_norm_enabled,
        )
        checkpoint_directory.mkdir(parents=True, exist_ok=True)
        marker_path = checkpoint_directory / TRAINING_STATE_MANIFEST_FILE
        if marker_path.exists():
            marker_path.unlink()
            _fsync_directory(checkpoint_directory)
        self._event(FAIL_AFTER_MARKER_INVALIDATION)

        try:
            self._inject(FAIL_AFTER_MARKER_INVALIDATION)
            actor_entries: list[ArtifactFileInventoryEntry] = []
            for index, (identity, state_dict) in enumerate(actor_state_dicts):
                path = checkpoint_directory / f"actor_agent_{identity}.pt"
                _atomic_torch_save(path, state_dict)
                self._event(f"actor_saved:{identity}")
                if index == 0:
                    self._inject(FAIL_AFTER_FIRST_ACTOR)
            self._inject(FAIL_AFTER_ALL_ACTORS)

            critic_path = checkpoint_directory / "critic_agent.pt"
            _atomic_torch_save(critic_path, critic_state_dict)
            self._event("critic_saved")
            self._inject(FAIL_AFTER_CRITIC)

            value_path: Path | None = None
            if value_normalizer_state_dict is not None:
                value_path = checkpoint_directory / "value_normalizer.pt"
                _atomic_torch_save(value_path, value_normalizer_state_dict)
                self._event("value_normalizer_saved")
                self._inject(FAIL_AFTER_VALUE_NORMALIZER)

            for identity, _ in actor_state_dicts:
                path = checkpoint_directory / f"actor_agent_{identity}.pt"
                actor_entries.append(
                    _artifact_entry(
                        role="actor",
                        path=path,
                        actor_identity=identity,
                        inventory=actor_inventories[identity],
                    )
                )
            critic_entry = _artifact_entry(
                role="critic",
                path=critic_path,
                actor_identity=None,
                inventory=critic_inventory,
            )
            value_entry = (
                None
                if value_path is None or value_inventory is None
                else _artifact_entry(
                    role="value_normalizer",
                    path=value_path,
                    actor_identity=None,
                    inventory=value_inventory,
                )
            )

            child_manifest_path = checkpoint_directory / CONTRACT_MANIFEST_FILE
            child_fingerprint_path = checkpoint_directory / CONTRACT_FINGERPRINT_FILE
            existing_child = _read_contract_pair(checkpoint_directory)
            if existing_child is None:
                _atomic_write_bytes(child_manifest_path, run_manifest_bytes)
                _atomic_write_bytes(child_fingerprint_path, run_fingerprint_bytes)
            else:
                _, child_manifest_bytes, child_fingerprint_bytes = existing_child
                if child_manifest_bytes != run_manifest_bytes or child_fingerprint_bytes != run_fingerprint_bytes:
                    raise AssignmentCheckpointSaveError("checkpoint-local contract bytes disagree with run root")
            self._event(FAIL_AFTER_CHILD_CONTRACT)
            self._inject(FAIL_AFTER_CHILD_CONTRACT)

            training_state = AssignmentTrainingStateManifest(
                contract_fingerprint=compute_manifest_sha256(manifest),
                checkpoint_kind=checkpoint_kind,
                checkpoint_generation=checkpoint_generation,
                episode_or_update_index=effective_index,
                continuation_classification=VALIDATED_WEIGHT_CONTINUATION_CANDIDATE,
                ordered_actor_identities=expected_names,
                actor_artifacts=tuple(actor_entries),
                critic_artifact=critic_entry,
                value_normalizer_artifact=value_entry,
                actor_optimizer_available=False,
                critic_optimizer_available=False,
                training_counters_available=False,
                rng_state_available=False,
                environment_resolver_state_available=False,
                rollout_buffer_state_available=False,
            )
            _atomic_write_bytes(marker_path, _training_state_bytes(training_state))
            self._event("training_state_manifest_committed")
            return AssignmentCheckpointSaveResult(
                checkpoint_directory=checkpoint_directory,
                checkpoint_generation=checkpoint_generation,
                checkpoint_kind=checkpoint_kind,
                training_state_manifest=training_state,
            )
        except Exception:
            if marker_path.exists():
                marker_path.unlink()
                _fsync_directory(checkpoint_directory)
            raise


def capture_assignment_checkpoint_runtime_state(runner: Any) -> AssignmentCheckpointRuntimeState:
    """Capture effective constructed runner/model/buffer values without running a model."""

    wrapper = runner.env.assignment_env
    schema = wrapper.assignment_observation_schema_manifest
    layout = wrapper.assignment_observation_layout
    profile = str(wrapper.assignment_lifecycle_profile_config["profile_name"])
    names = tuple(str(name) for name in wrapper.agents)
    actors = tuple(runner.actor)
    if len(actors) != len(names):
        raise AssignmentCheckpointSaveError("runner actor count differs from wrapper agent count")
    if len({id(actor.actor) for actor in actors}) != len(names):
        raise AssignmentCheckpointSaveError(
            "native assignment checkpoint requires distinct policy objects for every actor identity"
        )

    actor_policies = tuple(actor.actor for actor in actors)
    actor_input_dimensions = {
        name: int(actor.obs_space_size) for name, actor in zip(names, actors, strict=True)
    }
    actor_action_dimensions = {}
    for name, actor, policy in zip(names, actors, actor_policies, strict=True):
        action_head = policy.act.action_out
        if action_head.__class__.__name__ != "Categorical" or not hasattr(action_head, "linear"):
            raise AssignmentCheckpointSaveError(
                f"actor {name} does not expose the required Categorical action head"
            )
        head_dimension = int(action_head.linear.out_features)
        if int(actor.act_space.n) != head_dimension:
            raise AssignmentCheckpointSaveError(
                f"actor {name} action space and Categorical head dimensions differ"
            )
        actor_action_dimensions[name] = head_dimension

    actor_hidden = tuple(
        _require_equal(
            [tuple(int(value) for value in policy.hidden_sizes) for policy in actor_policies],
            field="constructed actor hidden sizes",
        )
    )
    actor_activation = str(
        _require_equal(
            [policy.base.activation_func for policy in actor_policies],
            field="constructed actor activation",
        )
    )
    actor_feature_norm = bool(
        _require_equal(
            [policy.base.use_feature_normalization for policy in actor_policies],
            field="constructed actor feature normalization",
        )
    )
    actor_initialization = str(
        _require_equal(
            [policy.initialization_method for policy in actor_policies],
            field="constructed actor initialization",
        )
    )
    actor_gain = float(
        _require_equal([policy.gain for policy in actor_policies], field="constructed actor gain")
    )
    use_recurrent = bool(
        _require_equal(
            [policy.use_recurrent_policy for policy in actor_policies],
            field="constructed actor recurrent flag",
        )
    )
    use_naive_recurrent = bool(
        _require_equal(
            [policy.use_naive_recurrent_policy for policy in actor_policies],
            field="constructed actor naive recurrent flag",
        )
    )
    recurrent_n = int(
        _require_equal(
            [policy.recurrent_n for policy in actor_policies],
            field="constructed actor recurrent_n",
        )
    )

    critic_wrapper = runner.critic
    critic_policy = critic_wrapper.critic
    critic_hidden = tuple(int(value) for value in critic_policy.hidden_sizes)
    if critic_policy.base.activation_func != actor_activation:
        raise AssignmentCheckpointSaveError("constructed actor and critic activations differ")
    if bool(critic_policy.base.use_feature_normalization) != actor_feature_norm:
        raise AssignmentCheckpointSaveError("constructed actor and critic feature normalization differs")
    if critic_policy.initialization_method != actor_initialization:
        raise AssignmentCheckpointSaveError("constructed actor and critic initialization differs")
    if bool(critic_policy.use_recurrent_policy) != use_recurrent or bool(
        critic_policy.use_naive_recurrent_policy
    ) != use_naive_recurrent:
        raise AssignmentCheckpointSaveError("constructed actor and critic recurrent flags differ")
    if int(critic_policy.recurrent_n) != recurrent_n:
        raise AssignmentCheckpointSaveError("constructed actor and critic recurrent_n differs")

    optimizer_classes = [actor.actor_optimizer.__class__.__name__ for actor in actors]
    optimizer_classes.append(critic_wrapper.critic_optimizer.__class__.__name__)
    optimizer_class = str(_require_equal(optimizer_classes, field="optimizer classes"))
    actor_lrs = [float(actor.lr) for actor in actors]
    actor_eps = [float(actor.opti_eps) for actor in actors]
    actor_weight_decay = [float(actor.weight_decay) for actor in actors]
    ppo_epochs = [int(actor.ppo_epoch) for actor in actors]
    actor_minibatches = [int(actor.actor_num_mini_batch) for actor in actors]
    clip_values = [float(actor.clip_param) for actor in actors] + [float(critic_wrapper.clip_param)]
    grad_enabled = [bool(actor.use_max_grad_norm) for actor in actors] + [
        bool(critic_wrapper.use_max_grad_norm)
    ]
    grad_norms = [float(actor.max_grad_norm) for actor in actors] + [
        float(critic_wrapper.max_grad_norm)
    ]
    critic_buffer = runner.critic_buffer

    actual_value_norm_enabled = runner.value_normalizer is not None
    configured_value_norm = runner.algo_args["train"]["use_valuenorm"]
    if not isinstance(configured_value_norm, bool) or configured_value_norm != actual_value_norm_enabled:
        raise AssignmentCheckpointSaveError(
            "constructed ValueNorm presence differs from resolved training configuration"
        )
    try:
        value_normalizer_contract = build_value_normalizer_contract(
            runner.value_normalizer,
            enabled=actual_value_norm_enabled,
        )
    except Exception as exc:
        raise AssignmentCheckpointSaveError(
            f"constructed ValueNorm does not satisfy the native adapter contract: {exc}"
        ) from exc

    return AssignmentCheckpointRuntimeState(
        wrapper_schema_manifest=schema,
        wrapper_observation_layout=layout,
        profile_name=profile,
        algorithm_name=str(runner.args["algo"]),
        harl_state_type=str(runner.state_type),
        ordered_agent_names=names,
        actor_input_dimensions_by_agent=actor_input_dimensions,
        critic_input_dimension=int(critic_wrapper.share_obs_space.shape[0]),
        actor_action_dimensions_by_agent=actor_action_dimensions,
        actor_class=(
            f"{actors[0].__class__.__name__}/{actor_policies[0].__class__.__name__}"
        ),
        critic_class=(
            f"{critic_wrapper.__class__.__name__}/{critic_policy.__class__.__name__}"
        ),
        action_distribution_class=actor_policies[0].act.action_out.__class__.__name__,
        actor_hidden_sizes=actor_hidden,
        critic_hidden_sizes=critic_hidden,
        activation=actor_activation,
        feature_normalization=actor_feature_norm,
        share_param=bool(runner.share_param),
        number_of_actor_networks=len({id(policy) for policy in actor_policies}),
        ordered_actor_network_names=names,
        critic_architecture="centralized_v_network",
        recurrent_n=recurrent_n,
        initialization_method=actor_initialization,
        action_gain=actor_gain,
        use_recurrent_policy=use_recurrent,
        use_naive_recurrent_policy=use_naive_recurrent,
        actor_buffer_generator=resolve_installed_harl_actor_buffer_generator(
            use_recurrent_policy=use_recurrent,
            use_naive_recurrent_policy=use_naive_recurrent,
        ),
        optimizer_class=optimizer_class,
        actor_learning_rate=float(_require_equal(actor_lrs, field="actor learning rates")),
        critic_learning_rate=float(critic_wrapper.critic_lr),
        optimizer_epsilon=float(
            _require_equal(
                actor_eps + [float(critic_wrapper.opti_eps)],
                field="optimizer epsilon",
            )
        ),
        weight_decay=float(
            _require_equal(
                actor_weight_decay + [float(critic_wrapper.weight_decay)],
                field="optimizer weight decay",
            )
        ),
        ppo_epochs=int(_require_equal(ppo_epochs, field="actor PPO epochs")),
        actor_minibatches=int(
            _require_equal(actor_minibatches, field="actor minibatches")
        ),
        critic_minibatches=int(critic_wrapper.critic_num_mini_batch),
        clip_coefficient=float(_require_equal(clip_values, field="clip coefficient")),
        value_loss_coefficient=float(critic_wrapper.value_loss_coef),
        entropy_coefficient=float(
            _require_equal(
                [float(actor.entropy_coef) for actor in actors],
                field="actor entropy coefficient",
            )
        ),
        gradient_clipping_enabled=bool(
            _require_equal(grad_enabled, field="gradient clipping enabled")
        ),
        max_gradient_norm=float(
            _require_equal(grad_norms, field="maximum gradient norm")
        ),
        gamma=float(critic_buffer.gamma),
        gae_lambda=float(critic_buffer.gae_lambda),
        value_norm_enabled=actual_value_norm_enabled,
        value_normalizer_contract=value_normalizer_contract,
        proper_time_limits=bool(critic_buffer.use_proper_time_limits),
        episode_length=int(critic_buffer.episode_length),
        rollout_thread_count=int(critic_buffer.n_rollout_threads),
        serialization_mode="state_dict",
    )


__all__ = [
    "AssignmentCheckpointRuntimeState",
    "AssignmentCheckpointSaveCoordinator",
    "AssignmentCheckpointSaveError",
    "AssignmentCheckpointSaveResult",
    "CHECKPOINT_KINDS",
    "CONTRACT_FINGERPRINT_FILE",
    "CONTRACT_MANIFEST_FILE",
    "FAIL_AFTER_ALL_ACTORS",
    "FAIL_AFTER_CHILD_CONTRACT",
    "FAIL_AFTER_CRITIC",
    "FAIL_AFTER_FIRST_ACTOR",
    "FAIL_AFTER_MARKER_INVALIDATION",
    "FAIL_AFTER_VALUE_NORMALIZER",
    "NATIVE_ASSIGNMENT_PROFILES",
    "NON_TRAINING_ASSIGNMENT_PROFILES",
    "TRAINING_STATE_MANIFEST_FILE",
    "build_assignment_checkpoint_contract_manifest",
    "build_tensor_inventory_from_state_dict",
    "capture_assignment_checkpoint_runtime_state",
    "compute_file_sha256",
    "ensure_contract_metadata_pair",
    "infer_assignment_checkpoint_kind",
]
