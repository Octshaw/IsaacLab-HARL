# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Pure assignment checkpoint contracts, fingerprints, and compatibility decisions."""

import hashlib
import hmac
import json
import math
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import PurePosixPath
from typing import Any


MANIFEST_FORMAT_VERSION = "assignment_checkpoint_contract_v1"
TRAINING_STATE_FORMAT_VERSION = "assignment_training_state_v1"
NAMED_LIFECYCLE_ABLATION = "lifecycle_contract_c_checkpoint_to_lifecycle_ablation_evaluation_v1"
VALIDATED_WEIGHT_CONTINUATION_CANDIDATE = "validated_weight_continuation_candidate"
CONTINUATION_ACKNOWLEDGEMENT = (
    "actor and critic optimizers, training counters, best-reward state, RNG, environment, "
    "resolver, and rollout buffers reset"
)

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NUMERIC_STRING = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_TIMESTAMP_LIKE = re.compile(r"(?:19|20)\d{2}-\d{2}-\d{2}(?:[T _-]\d{2})?")
_FORBIDDEN_CONTRACT_KEYS = {
    "absolute_path",
    "device_name",
    "directory",
    "dir",
    "git_working_tree",
    "host",
    "hostname",
    "machine",
    "path",
    "run_directory",
    "temporary_directory",
    "timestamp",
    "user",
    "username",
}
_STABLE_DTYPES = {
    "bfloat16",
    "bool",
    "float16",
    "float32",
    "float64",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
}

_SECTION_KEYS = {
    "identity": {
        "profile_name",
        "training_time_profile",
        "algorithm_name",
        "harl_state_type",
        "harl_shared_observation_mode",
        "serialization_mode",
    },
    "scale": {"M", "N", "num_agents", "ordered_agent_names"},
    "actor_schema": {
        "actor_schema_version",
        "actor_dimension",
        "actor_dimension_by_agent",
        "actor_ordered_feature_manifest",
        "actor_task_row_field_order",
        "actor_tail_field_order",
    },
    "shared_schema": {
        "shared_schema_version",
        "shared_dimension",
        "shared_construction_mode",
        "shared_ordered_blocks",
        "critic_budget_schema_version",
    },
    "action_contract": {
        "action_space_type",
        "action_dimension",
        "target_action_min",
        "target_action_max",
        "noop_raw_id",
        "noop_decoded_value",
    },
    "lifecycle_behavior_contract": {
        "snapshot_contract_version",
        "resolver_contract_version",
        "mask_contract_version",
        "budget_release_contract_version",
        "legacy_guardrail_profile",
        "ownership_contract_version",
        "arbitration_contract_version",
    },
    "policy_sequence_contract": {
        "policy_sequence_contract_version",
        "policy_sequence_mode",
        "use_recurrent_policy",
        "use_naive_recurrent_policy",
        "supported_actor_buffer_generator",
    },
    "model_structure": {
        "actor_class",
        "critic_class",
        "action_distribution_class",
        "actor_hidden_sizes",
        "critic_hidden_sizes",
        "activation",
        "feature_normalization",
        "share_param",
        "number_of_actor_networks",
        "ordered_actor_network_names",
        "critic_architecture",
        "harl_state_type",
        "recurrent_n",
        "initialization_method",
        "action_gain",
    },
    "training_contract": {
        "optimizer_class",
        "actor_learning_rate",
        "critic_learning_rate",
        "optimizer_epsilon",
        "weight_decay",
        "ppo_epochs",
        "actor_minibatches",
        "critic_minibatches",
        "clip_coefficient",
        "value_loss_coefficient",
        "entropy_coefficient",
        "gradient_clipping_enabled",
        "max_gradient_norm",
        "gamma",
        "gae_lambda",
        "value_norm_enabled",
        "proper_time_limits",
        "episode_length",
        "rollout_thread_count",
    },
}

_FEATURE_ENTRY_KEYS = {
    "name",
    "source",
    "shape",
    "dtype",
    "normalization",
    "snapshot_timing",
    "padding_semantics",
}

_DECIMAL_PATHS = {
    "model_structure.action_gain",
    "training_contract.actor_learning_rate",
    "training_contract.critic_learning_rate",
    "training_contract.optimizer_epsilon",
    "training_contract.weight_decay",
    "training_contract.clip_coefficient",
    "training_contract.value_loss_coefficient",
    "training_contract.entropy_coefficient",
    "training_contract.max_gradient_norm",
    "training_contract.gamma",
    "training_contract.gae_lambda",
}

_STRUCTURAL_PATHS = (
    "identity.algorithm_name",
    "identity.harl_state_type",
    "identity.serialization_mode",
    "scale.num_agents",
    "scale.ordered_agent_names",
    "actor_schema.actor_dimension",
    "actor_schema.actor_dimension_by_agent",
    "shared_schema.shared_dimension",
    "action_contract.action_space_type",
    "action_contract.action_dimension",
    "policy_sequence_contract.use_recurrent_policy",
    "policy_sequence_contract.use_naive_recurrent_policy",
    "model_structure.actor_class",
    "model_structure.critic_class",
    "model_structure.action_distribution_class",
    "model_structure.actor_hidden_sizes",
    "model_structure.critic_hidden_sizes",
    "model_structure.activation",
    "model_structure.feature_normalization",
    "model_structure.share_param",
    "model_structure.number_of_actor_networks",
    "model_structure.ordered_actor_network_names",
    "model_structure.critic_architecture",
    "model_structure.harl_state_type",
    "model_structure.recurrent_n",
)

_EVALUATION_PATHS = (
    "identity.profile_name",
    "identity.training_time_profile",
    "identity.algorithm_name",
    "identity.harl_state_type",
    "identity.harl_shared_observation_mode",
    "identity.serialization_mode",
    "scale",
    "actor_schema",
    "shared_schema",
    "action_contract",
    "lifecycle_behavior_contract",
    "policy_sequence_contract",
    "model_structure.actor_class",
    "model_structure.critic_class",
    "model_structure.action_distribution_class",
    "model_structure.actor_hidden_sizes",
    "model_structure.critic_hidden_sizes",
    "model_structure.activation",
    "model_structure.feature_normalization",
    "model_structure.share_param",
    "model_structure.number_of_actor_networks",
    "model_structure.ordered_actor_network_names",
    "model_structure.critic_architecture",
    "model_structure.harl_state_type",
    "model_structure.recurrent_n",
)

_ABLATION_DIFFERENCES = {
    "identity.profile_name": ("lifecycle_contract_c", "lifecycle_ablation"),
    "identity.training_time_profile": ("lifecycle_contract_c", "lifecycle_ablation"),
    "lifecycle_behavior_contract.resolver_contract_version": (
        "assignment_lifecycle_resolver_contract_c_v1",
        "disabled",
    ),
    "lifecycle_behavior_contract.mask_contract_version": (
        "lifecycle_contract_c_mask_v1",
        "lifecycle_ablation_physical_mask_v1",
    ),
    "lifecycle_behavior_contract.budget_release_contract_version": ("budget_release_v1", "disabled"),
}


class ContractValidationError(ValueError):
    """Raised when pure checkpoint metadata violates its schema."""


class FrozenDict(Mapping[str, Any]):
    """Small insertion-order-preserving immutable mapping."""

    __slots__ = ("_items",)

    def __init__(self, items: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> None:
        raw_items = items.items() if isinstance(items, Mapping) else items
        normalized: list[tuple[str, Any]] = []
        seen: set[str] = set()
        for key, value in raw_items:
            key = str(key)
            if key in seen:
                raise ContractValidationError(f"duplicate mapping key: {key!r}")
            seen.add(key)
            normalized.append((key, _deep_freeze(value)))
        object.__setattr__(self, "_items", tuple(normalized))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __getitem__(self, key: str) -> Any:
        for item_key, value in self._items:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"FrozenDict({dict(self._items)!r})"


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, FrozenDict):
        return value
    if isinstance(value, Mapping):
        return FrozenDict(value)
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _deep_thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _deep_thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_deep_thaw(item) for item in value]
    return value


def canonical_decimal(value: int | float | Decimal | str) -> str:
    """Normalize one finite numeric contract value to a plain decimal string."""

    if isinstance(value, bool):
        raise ContractValidationError("boolean is not a numeric contract value")
    if isinstance(value, str):
        if _NUMERIC_STRING.fullmatch(value) is None:
            raise ContractValidationError(f"invalid numeric string: {value!r}")
        source: int | float | Decimal | str = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(f"numeric contract value must be finite, got {value!r}")
        source = str(value)
    elif isinstance(value, (int, Decimal)):
        source = value
    else:
        raise ContractValidationError(f"unsupported numeric contract type: {type(value).__name__}")
    try:
        decimal_value = Decimal(source)
    except (InvalidOperation, ValueError) as exc:
        raise ContractValidationError(f"invalid numeric contract value: {value!r}") from exc
    if not decimal_value.is_finite():
        raise ContractValidationError(f"numeric contract value must be finite, got {value!r}")
    if decimal_value == 0:
        return "0"
    output = format(decimal_value, "f")
    if "." in output:
        output = output.rstrip("0").rstrip(".")
    return output


def _normalize_dtype(dtype: str) -> str:
    value = str(dtype).strip().lower()
    if value.startswith("torch."):
        value = value[6:]
    if value not in _STABLE_DTYPES:
        raise ContractValidationError(f"unsupported tensor dtype: {dtype!r}")
    return value


def _normalize_relative_path(path: str) -> str:
    raw = str(path).strip()
    if not raw:
        raise ContractValidationError("artifact path must not be empty")
    if _WINDOWS_ABSOLUTE.match(raw) or raw.startswith(("/", "\\")):
        raise ContractValidationError(f"artifact path must be relative: {path!r}")
    normalized = raw.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ContractValidationError(f"artifact path traversal is forbidden: {path!r}")
    return "/".join(parts)


def _validate_sha256(value: str, *, field: str) -> str:
    normalized = str(value)
    if _HEX_SHA256.fullmatch(normalized) is None:
        raise ContractValidationError(f"{field} must be 64 lowercase hexadecimal characters")
    return normalized


def _require_exact_keys(section_name: str, value: Mapping[str, Any], required: set[str]) -> None:
    keys = set(value.keys())
    if keys != required:
        missing = sorted(required - keys)
        unexpected = sorted(keys - required)
        raise ContractValidationError(
            f"{section_name} keys mismatch: missing={missing}, unexpected={unexpected}"
        )


def _validate_shape(shape: Any, *, field: str, allow_empty: bool = False) -> tuple[int, ...]:
    if not isinstance(shape, (list, tuple)):
        raise ContractValidationError(f"{field} must be a list/tuple of dimensions")
    output = tuple(shape)
    if (not output and not allow_empty) or any(
        isinstance(dim, bool) or not isinstance(dim, int) or dim < 0 for dim in output
    ):
        raise ContractValidationError(f"{field} must contain non-negative integer dimensions")
    return output


def _validate_feature_entries(entries: Any, *, field: str) -> None:
    if not isinstance(entries, (list, tuple)) or len(entries) == 0:
        raise ContractValidationError(f"{field} must be a non-empty ordered list")
    names: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ContractValidationError(f"{field}[{index}] must be an object")
        _require_exact_keys(f"{field}[{index}]", entry, _FEATURE_ENTRY_KEYS)
        name = str(entry["name"])
        if not name or name in names:
            raise ContractValidationError(f"{field} contains an empty or duplicate name: {name!r}")
        names.add(name)
        _validate_shape(entry["shape"], field=f"{field}[{index}].shape")
        _normalize_dtype(str(entry["dtype"]))


def _validate_contract_strings(value: Any, *, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_lower = str(key).lower()
            if key_lower in _FORBIDDEN_CONTRACT_KEYS:
                raise ContractValidationError(f"machine-specific contract field is forbidden: {path}{key}")
            _validate_contract_strings(item, path=f"{path}{key}.")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_contract_strings(item, path=f"{path}{index}.")
        return
    if isinstance(value, str):
        if _WINDOWS_ABSOLUTE.match(value) or value.startswith(("/", "\\")) or "\\" in value:
            raise ContractValidationError(f"machine-specific path value is forbidden at {path[:-1]}: {value!r}")
        if _TIMESTAMP_LIKE.search(value):
            raise ContractValidationError(f"timestamp-like contract value is forbidden at {path[:-1]}: {value!r}")


def _normalize_manifest_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    output = _deep_thaw(_deep_freeze(mapping))
    for path in _DECIMAL_PATHS:
        section, field = path.split(".", 1)
        output[section][field] = canonical_decimal(output[section][field])
    return output


@dataclass(frozen=True)
class AssignmentCheckpointContractManifest:
    identity: Mapping[str, Any]
    scale: Mapping[str, Any]
    actor_schema: Mapping[str, Any]
    shared_schema: Mapping[str, Any]
    action_contract: Mapping[str, Any]
    lifecycle_behavior_contract: Mapping[str, Any]
    policy_sequence_contract: Mapping[str, Any]
    model_structure: Mapping[str, Any]
    training_contract: Mapping[str, Any]
    manifest_format_version: str = MANIFEST_FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.manifest_format_version != MANIFEST_FORMAT_VERSION:
            raise ContractValidationError(
                f"unsupported manifest_format_version: {self.manifest_format_version!r}"
            )
        raw = {
            section: _deep_thaw(getattr(self, section))
            for section in _SECTION_KEYS
        }
        raw = _normalize_manifest_mapping(raw)
        for section, required in _SECTION_KEYS.items():
            value = raw[section]
            if not isinstance(value, Mapping):
                raise ContractValidationError(f"{section} must be an object")
            _require_exact_keys(section, value, required)
            object.__setattr__(self, section, FrozenDict(value))
        self._validate_semantics()

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> AssignmentCheckpointContractManifest:
        required = {"manifest_format_version", *_SECTION_KEYS.keys()}
        _require_exact_keys("manifest", mapping, required)
        return cls(
            manifest_format_version=str(mapping["manifest_format_version"]),
            **{section: mapping[section] for section in _SECTION_KEYS},
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "manifest_format_version": self.manifest_format_version,
            **{section: _deep_thaw(getattr(self, section)) for section in _SECTION_KEYS},
        }

    def _validate_semantics(self) -> None:
        mapping = self.to_mapping()
        _validate_contract_strings(mapping)
        identity = mapping["identity"]
        scale = mapping["scale"]
        actor = mapping["actor_schema"]
        shared = mapping["shared_schema"]
        action = mapping["action_contract"]
        sequence = mapping["policy_sequence_contract"]
        model = mapping["model_structure"]
        training = mapping["training_contract"]

        if identity["serialization_mode"] != "state_dict":
            raise ContractValidationError("checkpoint contract v1 supports serialization_mode='state_dict' only")
        if str(identity["algorithm_name"]).lower() != "happo":
            raise ContractValidationError("checkpoint contract v1 official algorithm is HAPPO")
        if identity["harl_state_type"] not in {"EP", "FP"}:
            raise ContractValidationError("harl_state_type must be 'EP' or 'FP'")

        for key in ("M", "N", "num_agents"):
            if isinstance(scale[key], bool) or not isinstance(scale[key], int) or scale[key] <= 0:
                raise ContractValidationError(f"scale.{key} must be a positive integer")
        agent_names = tuple(scale["ordered_agent_names"])
        if scale["M"] != scale["num_agents"] or len(agent_names) != scale["num_agents"]:
            raise ContractValidationError("M, num_agents, and ordered_agent_names length must agree")
        if len(set(agent_names)) != len(agent_names) or any(not str(name) for name in agent_names):
            raise ContractValidationError("ordered_agent_names must be unique non-empty strings")

        dimension_by_agent = actor["actor_dimension_by_agent"]
        if not isinstance(dimension_by_agent, Mapping) or tuple(dimension_by_agent.keys()) != agent_names:
            raise ContractValidationError("actor_dimension_by_agent keys must match ordered_agent_names")
        if any(value != actor["actor_dimension"] for value in dimension_by_agent.values()):
            raise ContractValidationError("all actor dimensions must match actor_dimension for contract v1")
        _validate_feature_entries(actor["actor_ordered_feature_manifest"], field="actor_ordered_feature_manifest")
        if not actor["actor_task_row_field_order"] or not actor["actor_tail_field_order"]:
            raise ContractValidationError("actor ordered field lists must not be empty")

        profile = identity["profile_name"]
        expected_actor = (
            100 + 3 * scale["M"] + 16 * scale["N"]
            if profile == "legacy"
            else 100 + 3 * scale["M"] + 19 * scale["N"]
        )
        expected_shared = (
            scale["M"] * expected_actor
            if profile == "legacy"
            else scale["M"] * expected_actor + 2 * scale["M"]
        )
        if actor["actor_dimension"] != expected_actor:
            raise ContractValidationError(
                f"actor dimension mismatch for profile {profile!r}: expected {expected_actor}"
            )
        if shared["shared_dimension"] != expected_shared:
            raise ContractValidationError(
                f"shared dimension mismatch for profile {profile!r}: expected {expected_shared}"
            )
        _validate_feature_entries(shared["shared_ordered_blocks"], field="shared_ordered_blocks")

        if action != {
            "action_space_type": "Discrete",
            "action_dimension": scale["N"] + 1,
            "target_action_min": 0,
            "target_action_max": scale["N"] - 1,
            "noop_raw_id": scale["N"],
            "noop_decoded_value": -1,
        }:
            raise ContractValidationError("action contract must use targets 0..N-1 and raw noop N decoded to -1")

        if profile == "lifecycle_contract_c":
            if sequence != {
                "policy_sequence_contract_version": "lifecycle_feed_forward_v1",
                "policy_sequence_mode": "feed_forward",
                "use_recurrent_policy": False,
                "use_naive_recurrent_policy": False,
                "supported_actor_buffer_generator": "feed_forward_generator_actor",
            }:
                raise ContractValidationError("lifecycle_contract_c requires lifecycle_feed_forward_v1")
        if not isinstance(model["share_param"], bool):
            raise ContractValidationError("model_structure.share_param must be a boolean")
        if (
            isinstance(model["number_of_actor_networks"], bool)
            or not isinstance(model["number_of_actor_networks"], int)
            or model["number_of_actor_networks"] <= 0
        ):
            raise ContractValidationError("number_of_actor_networks must be a positive integer")
        if tuple(model["ordered_actor_network_names"]) != agent_names:
            raise ContractValidationError("ordered_actor_network_names must match ordered_agent_names")
        if model["harl_state_type"] != identity["harl_state_type"]:
            raise ContractValidationError("model and identity HARL state types must match")
        for field in ("actor_hidden_sizes", "critic_hidden_sizes"):
            values = tuple(model[field])
            if not values or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in values):
                raise ContractValidationError(f"model_structure.{field} must contain positive integers")
        if isinstance(model["recurrent_n"], bool) or not isinstance(model["recurrent_n"], int) or model["recurrent_n"] <= 0:
            raise ContractValidationError("model_structure.recurrent_n must be positive")

        bool_fields = (
            "gradient_clipping_enabled",
            "value_norm_enabled",
            "proper_time_limits",
        )
        if any(not isinstance(training[field], bool) for field in bool_fields):
            raise ContractValidationError("training boolean fields must remain JSON booleans")
        int_fields = (
            "ppo_epochs",
            "actor_minibatches",
            "critic_minibatches",
            "episode_length",
            "rollout_thread_count",
        )
        if any(
            isinstance(training[field], bool) or not isinstance(training[field], int) or training[field] <= 0
            for field in int_fields
        ):
            raise ContractValidationError("training count fields must be positive JSON integers")


def canonical_manifest_bytes(manifest: AssignmentCheckpointContractManifest | Mapping[str, Any]) -> bytes:
    validated = (
        manifest
        if isinstance(manifest, AssignmentCheckpointContractManifest)
        else AssignmentCheckpointContractManifest.from_mapping(manifest)
    )
    text = json.dumps(
        validated.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return text.encode("utf-8")


def compute_manifest_sha256(manifest: AssignmentCheckpointContractManifest | Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def verify_manifest_sha256(
    manifest: AssignmentCheckpointContractManifest | Mapping[str, Any],
    expected_fingerprint: str,
) -> bool:
    expected = _validate_sha256(expected_fingerprint, field="expected_fingerprint")
    return hmac.compare_digest(compute_manifest_sha256(manifest), expected)


@dataclass(frozen=True)
class StateDictTensorInventoryEntry:
    key: str
    shape: tuple[int, ...]
    dtype: str

    def __post_init__(self) -> None:
        key = str(self.key)
        if not key:
            raise ContractValidationError("tensor inventory key must not be empty")
        object.__setattr__(self, "key", key)
        object.__setattr__(
            self,
            "shape",
            _validate_shape(self.shape, field=f"tensor[{key}].shape", allow_empty=True),
        )
        object.__setattr__(self, "dtype", _normalize_dtype(self.dtype))

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> StateDictTensorInventoryEntry:
        _require_exact_keys("tensor inventory entry", mapping, {"key", "shape", "dtype"})
        return cls(key=mapping["key"], shape=tuple(mapping["shape"]), dtype=mapping["dtype"])

    def to_mapping(self) -> dict[str, Any]:
        return {"key": self.key, "shape": list(self.shape), "dtype": self.dtype}


def normalize_tensor_inventory(
    entries: Iterable[StateDictTensorInventoryEntry | Mapping[str, Any]],
) -> tuple[StateDictTensorInventoryEntry, ...]:
    normalized = tuple(
        entry if isinstance(entry, StateDictTensorInventoryEntry) else StateDictTensorInventoryEntry.from_mapping(entry)
        for entry in entries
    )
    keys = [entry.key for entry in normalized]
    if len(keys) != len(set(keys)):
        raise ContractValidationError("state-dict tensor inventory contains duplicate keys")
    return tuple(sorted(normalized, key=lambda entry: entry.key))


def compute_tensor_inventory_sha256(
    entries: Iterable[StateDictTensorInventoryEntry | Mapping[str, Any]],
) -> str:
    normalized = [entry.to_mapping() for entry in normalize_tensor_inventory(entries)]
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ArtifactFileInventoryEntry:
    artifact_role: str
    relative_file_name: str
    file_size: int
    file_sha256: str
    serialization_mode: str
    actor_identity: str | None = None
    tensor_inventory: tuple[StateDictTensorInventoryEntry, ...] = ()
    tensor_inventory_sha256: str | None = None

    def __post_init__(self) -> None:
        role = str(self.artifact_role)
        if role not in {"actor", "critic", "value_normalizer"}:
            raise ContractValidationError(f"unsupported artifact role: {role!r}")
        object.__setattr__(self, "artifact_role", role)
        object.__setattr__(self, "relative_file_name", _normalize_relative_path(self.relative_file_name))
        if isinstance(self.file_size, bool) or not isinstance(self.file_size, int) or self.file_size < 0:
            raise ContractValidationError("artifact file_size must be a non-negative integer")
        object.__setattr__(self, "file_sha256", _validate_sha256(self.file_sha256, field="file_sha256"))
        if self.serialization_mode != "state_dict":
            raise ContractValidationError("checkpoint v1 artifact serialization must be state_dict")
        if role == "actor" and not self.actor_identity:
            raise ContractValidationError("actor artifact requires actor_identity")
        if role != "actor" and self.actor_identity is not None:
            raise ContractValidationError(f"{role} artifact must not define actor_identity")
        inventory = normalize_tensor_inventory(self.tensor_inventory)
        object.__setattr__(self, "tensor_inventory", inventory)
        digest = self.tensor_inventory_sha256 or compute_tensor_inventory_sha256(inventory)
        digest = _validate_sha256(digest, field="tensor_inventory_sha256")
        if not hmac.compare_digest(digest, compute_tensor_inventory_sha256(inventory)):
            raise ContractValidationError("tensor_inventory_sha256 does not match tensor inventory")
        object.__setattr__(self, "tensor_inventory_sha256", digest)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> ArtifactFileInventoryEntry:
        required = {
            "artifact_role",
            "relative_file_name",
            "file_size",
            "file_sha256",
            "serialization_mode",
            "actor_identity",
            "tensor_inventory",
            "tensor_inventory_sha256",
        }
        _require_exact_keys("artifact inventory entry", mapping, required)
        return cls(
            artifact_role=mapping["artifact_role"],
            relative_file_name=mapping["relative_file_name"],
            file_size=mapping["file_size"],
            file_sha256=mapping["file_sha256"],
            serialization_mode=mapping["serialization_mode"],
            actor_identity=mapping["actor_identity"],
            tensor_inventory=tuple(
                StateDictTensorInventoryEntry.from_mapping(entry) for entry in mapping["tensor_inventory"]
            ),
            tensor_inventory_sha256=mapping["tensor_inventory_sha256"],
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "artifact_role": self.artifact_role,
            "relative_file_name": self.relative_file_name,
            "file_size": self.file_size,
            "file_sha256": self.file_sha256,
            "serialization_mode": self.serialization_mode,
            "actor_identity": self.actor_identity,
            "tensor_inventory": [entry.to_mapping() for entry in self.tensor_inventory],
            "tensor_inventory_sha256": self.tensor_inventory_sha256,
        }


@dataclass(frozen=True)
class AssignmentTrainingStateManifest:
    contract_fingerprint: str
    checkpoint_kind: str
    checkpoint_generation: int
    continuation_classification: str
    ordered_actor_identities: tuple[str, ...]
    actor_artifacts: tuple[ArtifactFileInventoryEntry, ...]
    critic_artifact: ArtifactFileInventoryEntry | None
    value_normalizer_artifact: ArtifactFileInventoryEntry | None
    actor_optimizer_available: bool
    critic_optimizer_available: bool
    training_counters_available: bool
    rng_state_available: bool
    environment_resolver_state_available: bool
    rollout_buffer_state_available: bool
    episode_or_update_index: int | None = None
    training_state_format_version: str = TRAINING_STATE_FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.training_state_format_version != TRAINING_STATE_FORMAT_VERSION:
            raise ContractValidationError(
                f"unsupported training_state_format_version: {self.training_state_format_version!r}"
            )
        object.__setattr__(
            self,
            "contract_fingerprint",
            _validate_sha256(self.contract_fingerprint, field="contract_fingerprint"),
        )
        if self.checkpoint_kind not in {
            "regular",
            "best",
            "episode_snapshot",
            "final",
            "temporary_test",
        }:
            raise ContractValidationError(f"unsupported checkpoint_kind: {self.checkpoint_kind!r}")
        if not isinstance(self.continuation_classification, str) or not self.continuation_classification:
            raise ContractValidationError("continuation_classification must be a non-empty string")
        if (
            isinstance(self.checkpoint_generation, bool)
            or not isinstance(self.checkpoint_generation, int)
            or self.checkpoint_generation < 0
        ):
            raise ContractValidationError("checkpoint_generation must be a non-negative integer")
        if self.episode_or_update_index is not None and (
            isinstance(self.episode_or_update_index, bool)
            or not isinstance(self.episode_or_update_index, int)
            or self.episode_or_update_index < 0
        ):
            raise ContractValidationError("episode_or_update_index must be null or non-negative")
        identities = tuple(str(value) for value in self.ordered_actor_identities)
        if not identities or len(identities) != len(set(identities)):
            raise ContractValidationError("ordered_actor_identities must be unique and non-empty")
        object.__setattr__(self, "ordered_actor_identities", identities)
        artifacts = tuple(self.actor_artifacts)
        artifact_identities = tuple(artifact.actor_identity for artifact in artifacts)
        if artifact_identities != identities:
            raise ContractValidationError(
                "actor artifact identities must be complete and match ordered_actor_identities"
            )
        if any(artifact.artifact_role != "actor" for artifact in artifacts):
            raise ContractValidationError("actor_artifacts may contain only actor artifacts")
        object.__setattr__(self, "actor_artifacts", artifacts)
        if self.critic_artifact is not None and self.critic_artifact.artifact_role != "critic":
            raise ContractValidationError("critic_artifact has the wrong role")
        if (
            self.value_normalizer_artifact is not None
            and self.value_normalizer_artifact.artifact_role != "value_normalizer"
        ):
            raise ContractValidationError("value_normalizer_artifact has the wrong role")
        availability_fields = (
            "actor_optimizer_available",
            "critic_optimizer_available",
            "training_counters_available",
            "rng_state_available",
            "environment_resolver_state_available",
            "rollout_buffer_state_available",
        )
        if any(not isinstance(getattr(self, field), bool) for field in availability_fields):
            raise ContractValidationError("training-state availability fields must be booleans")
        paths = [
            artifact.relative_file_name
            for artifact in (
                *self.actor_artifacts,
                self.critic_artifact,
                self.value_normalizer_artifact,
            )
            if artifact is not None
        ]
        if len(paths) != len(set(paths)):
            raise ContractValidationError("artifact inventory contains duplicate relative file names")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "training_state_format_version": self.training_state_format_version,
            "contract_fingerprint": self.contract_fingerprint,
            "checkpoint_kind": self.checkpoint_kind,
            "checkpoint_generation": self.checkpoint_generation,
            "episode_or_update_index": self.episode_or_update_index,
            "continuation_classification": self.continuation_classification,
            "ordered_actor_identities": list(self.ordered_actor_identities),
            "actor_artifacts": [artifact.to_mapping() for artifact in self.actor_artifacts],
            "critic_artifact": None if self.critic_artifact is None else self.critic_artifact.to_mapping(),
            "value_normalizer_artifact": (
                None if self.value_normalizer_artifact is None else self.value_normalizer_artifact.to_mapping()
            ),
            "actor_optimizer_available": self.actor_optimizer_available,
            "critic_optimizer_available": self.critic_optimizer_available,
            "training_counters_available": self.training_counters_available,
            "rng_state_available": self.rng_state_available,
            "environment_resolver_state_available": self.environment_resolver_state_available,
            "rollout_buffer_state_available": self.rollout_buffer_state_available,
        }

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> AssignmentTrainingStateManifest:
        required = {
            "training_state_format_version",
            "contract_fingerprint",
            "checkpoint_kind",
            "checkpoint_generation",
            "episode_or_update_index",
            "continuation_classification",
            "ordered_actor_identities",
            "actor_artifacts",
            "critic_artifact",
            "value_normalizer_artifact",
            "actor_optimizer_available",
            "critic_optimizer_available",
            "training_counters_available",
            "rng_state_available",
            "environment_resolver_state_available",
            "rollout_buffer_state_available",
        }
        _require_exact_keys("training-state manifest", mapping, required)
        critic = mapping["critic_artifact"]
        value_normalizer = mapping["value_normalizer_artifact"]
        return cls(
            training_state_format_version=mapping["training_state_format_version"],
            contract_fingerprint=mapping["contract_fingerprint"],
            checkpoint_kind=mapping["checkpoint_kind"],
            checkpoint_generation=mapping["checkpoint_generation"],
            episode_or_update_index=mapping["episode_or_update_index"],
            continuation_classification=mapping["continuation_classification"],
            ordered_actor_identities=tuple(mapping["ordered_actor_identities"]),
            actor_artifacts=tuple(
                ArtifactFileInventoryEntry.from_mapping(entry) for entry in mapping["actor_artifacts"]
            ),
            critic_artifact=None if critic is None else ArtifactFileInventoryEntry.from_mapping(critic),
            value_normalizer_artifact=(
                None
                if value_normalizer is None
                else ArtifactFileInventoryEntry.from_mapping(value_normalizer)
            ),
            actor_optimizer_available=mapping["actor_optimizer_available"],
            critic_optimizer_available=mapping["critic_optimizer_available"],
            training_counters_available=mapping["training_counters_available"],
            rng_state_available=mapping["rng_state_available"],
            environment_resolver_state_available=mapping["environment_resolver_state_available"],
            rollout_buffer_state_available=mapping["rollout_buffer_state_available"],
        )


class CompatibilityPurpose(str, Enum):
    STRUCTURAL_INSPECTION = "structural_inspection"
    NORMAL_EVALUATION = "normal_evaluation"
    EXPLICIT_ABLATION_EVALUATION = "explicit_ablation_evaluation"
    VALIDATED_WEIGHT_CONTINUATION = "validated_weight_continuation"
    TRAINING_INITIALIZATION_OR_FINE_TUNING = "training_initialization_or_fine_tuning"
    EXACT_TRAINING_RESUME = "exact_training_resume"


@dataclass(frozen=True)
class CompatibilityMismatch:
    field_path: str
    category: str
    expected_value: Any
    actual_value: Any
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_value", _deep_freeze(self.expected_value))
        object.__setattr__(self, "actual_value", _deep_freeze(self.actual_value))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "field_path": self.field_path,
            "category": self.category,
            "expected_value": _deep_thaw(self.expected_value),
            "actual_value": _deep_thaw(self.actual_value),
            "message": self.message,
        }


@dataclass(frozen=True)
class CompatibilityRequest:
    purpose: CompatibilityPurpose
    current_manifest: AssignmentCheckpointContractManifest
    checkpoint_manifest: AssignmentCheckpointContractManifest | None
    checkpoint_fingerprint: str | None = None
    explicit_ablation_name: str | None = None
    training_state_manifest: AssignmentTrainingStateManifest | None = None
    continuation_reset_acknowledged: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, CompatibilityPurpose):
            raise ContractValidationError("compatibility purpose must be a CompatibilityPurpose")
        if not isinstance(self.current_manifest, AssignmentCheckpointContractManifest):
            raise ContractValidationError("current_manifest must be a validated checkpoint contract")
        if self.checkpoint_manifest is not None and not isinstance(
            self.checkpoint_manifest, AssignmentCheckpointContractManifest
        ):
            raise ContractValidationError("checkpoint_manifest must be a validated checkpoint contract")
        if self.training_state_manifest is not None and not isinstance(
            self.training_state_manifest, AssignmentTrainingStateManifest
        ):
            raise ContractValidationError("training_state_manifest must be validated")
        if not isinstance(self.continuation_reset_acknowledged, bool):
            raise ContractValidationError("continuation_reset_acknowledged must be a boolean")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose.value,
            "current_manifest": self.current_manifest.to_mapping(),
            "checkpoint_manifest": (
                None if self.checkpoint_manifest is None else self.checkpoint_manifest.to_mapping()
            ),
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "explicit_ablation_name": self.explicit_ablation_name,
            "training_state_manifest": (
                None if self.training_state_manifest is None else self.training_state_manifest.to_mapping()
            ),
            "continuation_reset_acknowledged": self.continuation_reset_acknowledged,
        }


@dataclass(frozen=True)
class CompatibilityDecision:
    allowed: bool
    classification: str
    requested_purpose: CompatibilityPurpose
    mismatches: tuple[CompatibilityMismatch, ...]
    reason: str
    required_acknowledgement: str | None = None
    next_action: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.requested_purpose, CompatibilityPurpose):
            raise ContractValidationError("requested_purpose must be a CompatibilityPurpose")
        mismatches = tuple(self.mismatches)
        if any(not isinstance(mismatch, CompatibilityMismatch) for mismatch in mismatches):
            raise ContractValidationError("decision mismatches must be CompatibilityMismatch values")
        object.__setattr__(self, "mismatches", mismatches)

    @property
    def first_mismatch(self) -> CompatibilityMismatch | None:
        return self.mismatches[0] if self.mismatches else None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "classification": self.classification,
            "requested_purpose": self.requested_purpose.value,
            "mismatches": [mismatch.to_mapping() for mismatch in self.mismatches],
            "first_mismatch": (
                None if self.first_mismatch is None else self.first_mismatch.to_mapping()
            ),
            "reason": self.reason,
            "required_acknowledgement": self.required_acknowledgement,
            "next_action": self.next_action,
        }


def _value_at_path(mapping: Mapping[str, Any], path: str) -> Any:
    value: Any = mapping
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _compare_paths(
    checkpoint: Mapping[str, Any],
    current: Mapping[str, Any],
    paths: Iterable[str],
    *,
    category: str,
) -> list[CompatibilityMismatch]:
    mismatches: list[CompatibilityMismatch] = []
    for path in paths:
        expected = _value_at_path(checkpoint, path)
        actual = _value_at_path(current, path)
        if expected != actual:
            mismatches.append(
                CompatibilityMismatch(
                    field_path=path,
                    category=category,
                    expected_value=expected,
                    actual_value=actual,
                    message=f"{path} differs for {category}",
                )
            )
    return mismatches


def _expand_leaf_comparison_paths(
    checkpoint: Mapping[str, Any],
    current: Mapping[str, Any],
    paths: Iterable[str],
) -> tuple[str, ...]:
    expanded: set[str] = set()
    for path in paths:
        checkpoint_value = _value_at_path(checkpoint, path)
        current_value = _value_at_path(current, path)
        if isinstance(checkpoint_value, Mapping) or isinstance(current_value, Mapping):
            if isinstance(checkpoint_value, Mapping):
                expanded.update(_flatten_leaf_paths(checkpoint_value, prefix=path))
            if isinstance(current_value, Mapping):
                expanded.update(_flatten_leaf_paths(current_value, prefix=path))
        else:
            expanded.add(path)
    return tuple(sorted(expanded))


def _flatten_leaf_paths(value: Any, *, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            output.update(_flatten_leaf_paths(item, prefix=path))
        return output
    return {prefix: _deep_thaw(value)}


def _compare_complete_contract(
    checkpoint: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    category: str,
) -> list[CompatibilityMismatch]:
    expected = _flatten_leaf_paths(checkpoint)
    actual = _flatten_leaf_paths(current)
    mismatches: list[CompatibilityMismatch] = []
    for path in sorted(set(expected) | set(actual)):
        if expected.get(path) != actual.get(path):
            mismatches.append(
                CompatibilityMismatch(
                    field_path=path,
                    category=category,
                    expected_value=expected.get(path),
                    actual_value=actual.get(path),
                    message=f"{path} differs for {category}",
                )
            )
    return mismatches


def _decision(
    request: CompatibilityRequest,
    *,
    allowed: bool,
    classification: str,
    reason: str,
    mismatches: Iterable[CompatibilityMismatch] = (),
    required_acknowledgement: str | None = None,
    next_action: str | None = None,
) -> CompatibilityDecision:
    return CompatibilityDecision(
        allowed=allowed,
        classification=classification,
        requested_purpose=request.purpose,
        mismatches=tuple(mismatches),
        reason=reason,
        required_acknowledgement=required_acknowledgement,
        next_action=next_action,
    )


def evaluate_compatibility(request: CompatibilityRequest) -> CompatibilityDecision:
    """Evaluate a native checkpoint contract for one explicit load purpose."""

    if request.purpose == CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING:
        return _decision(
            request,
            allowed=False,
            classification="unsupported_deferred",
            reason=(
                "training initialization/fine-tuning is not supported by assignment checkpoint contract v1"
            ),
        )
    if request.purpose == CompatibilityPurpose.EXACT_TRAINING_RESUME:
        return _decision(
            request,
            allowed=False,
            classification="unsupported_exact_resume",
            reason=(
                "exact resume is unsupported: actor/critic optimizer state, training counters, best-reward state, "
                "RNG state, environment/resolver/budget state, and rollout-buffer state are unavailable"
            ),
        )
    checkpoint_manifest = request.checkpoint_manifest
    if checkpoint_manifest is None:
        return _decision(
            request,
            allowed=False,
            classification="missing_native_metadata",
            reason="native manifest metadata is required for this compatibility path",
        )
    if request.checkpoint_fingerprint is None:
        if request.purpose != CompatibilityPurpose.STRUCTURAL_INSPECTION:
            return _decision(
                request,
                allowed=False,
                classification="missing_fingerprint",
                reason="checkpoint manifest integrity fingerprint is required",
            )
    else:
        try:
            fingerprint_valid = verify_manifest_sha256(
                checkpoint_manifest,
                request.checkpoint_fingerprint,
            )
        except ContractValidationError as exc:
            return _decision(
                request,
                allowed=False,
                classification="invalid_fingerprint",
                reason=str(exc),
            )
        if not fingerprint_valid:
            return _decision(
                request,
                allowed=False,
                classification="fingerprint_mismatch",
                reason="checkpoint manifest SHA-256 verification failed",
            )

    checkpoint = checkpoint_manifest.to_mapping()
    current = request.current_manifest.to_mapping()
    structural = _compare_paths(checkpoint, current, _STRUCTURAL_PATHS, category="structural")
    if request.purpose == CompatibilityPurpose.STRUCTURAL_INSPECTION:
        return _decision(
            request,
            allowed=not structural,
            classification="structurally_compatible" if not structural else "structural_mismatch",
            reason=(
                "model/state-dict structures correspond"
                if not structural
                else "one or more structural fields differ"
            ),
            mismatches=structural,
            next_action="weights_only_state_dict_inventory_inspection",
        )
    if structural:
        return _decision(
            request,
            allowed=False,
            classification="structural_mismatch",
            reason="structural compatibility is required before this load purpose",
            mismatches=structural,
        )

    if request.purpose == CompatibilityPurpose.NORMAL_EVALUATION:
        paths = _expand_leaf_comparison_paths(checkpoint, current, _EVALUATION_PATHS)
        mismatches = _compare_paths(checkpoint, current, paths, category="evaluation_semantics")
        return _decision(
            request,
            allowed=not mismatches,
            classification="normal_evaluation" if not mismatches else "evaluation_semantic_mismatch",
            reason=(
                "checkpoint is compatible for normal evaluation"
                if not mismatches
                else "evaluation-semantic fields differ"
            ),
            mismatches=mismatches,
        )

    if request.purpose == CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION:
        return _evaluate_named_ablation(request, checkpoint, current)

    if request.purpose == CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION:
        mismatches = _compare_complete_contract(
            checkpoint,
            current,
            category="validated_weight_continuation",
        )
        if mismatches:
            return _decision(
                request,
                allowed=False,
                classification="continuation_contract_mismatch",
                reason="validated weight continuation requires exact immutable contract equality",
                mismatches=mismatches,
            )
        return _evaluate_continuation_inventory(request)

    return _decision(
        request,
        allowed=False,
        classification="unsupported_purpose",
        reason=f"unsupported compatibility purpose: {request.purpose.value}",
    )


def _evaluate_named_ablation(
    request: CompatibilityRequest,
    checkpoint: Mapping[str, Any],
    current: Mapping[str, Any],
) -> CompatibilityDecision:
    if request.explicit_ablation_name != NAMED_LIFECYCLE_ABLATION:
        return _decision(
            request,
            allowed=False,
            classification="unknown_or_missing_ablation",
            reason=f"explicit validator-owned ablation name {NAMED_LIFECYCLE_ABLATION!r} is required",
        )
    paths = _expand_leaf_comparison_paths(checkpoint, current, _EVALUATION_PATHS)
    semantic_mismatches = _compare_paths(
        checkpoint,
        current,
        paths,
        category="ablation_evaluation",
    )
    unauthorized: list[CompatibilityMismatch] = []
    observed_paths = {mismatch.field_path for mismatch in semantic_mismatches}
    for mismatch in semantic_mismatches:
        permitted = _ABLATION_DIFFERENCES.get(mismatch.field_path)
        if permitted != (_deep_thaw(mismatch.expected_value), _deep_thaw(mismatch.actual_value)):
            unauthorized.append(mismatch)
    missing_declared = set(_ABLATION_DIFFERENCES) - observed_paths
    for path in sorted(missing_declared):
        expected, actual = _ABLATION_DIFFERENCES[path]
        unauthorized.append(
            CompatibilityMismatch(
                field_path=path,
                category="ablation_evaluation",
                expected_value=expected,
                actual_value=actual,
                message="named ablation did not contain its required declared difference",
            )
        )
    return _decision(
        request,
        allowed=not unauthorized,
        classification="explicit_ablation_evaluation" if not unauthorized else "ablation_mismatch",
        reason=(
            "validator-owned lifecycle Contract C to lifecycle ablation evaluation is authorized"
            if not unauthorized
            else "named ablation contains missing or unauthorized differences"
        ),
        mismatches=unauthorized,
    )


def _evaluate_continuation_inventory(request: CompatibilityRequest) -> CompatibilityDecision:
    manifest = request.checkpoint_manifest
    training_state = request.training_state_manifest
    assert manifest is not None
    if manifest.identity["serialization_mode"] != "state_dict":
        return _decision(
            request,
            allowed=False,
            classification="unsupported_serialization",
            reason="validated weight continuation requires state_dict serialization",
        )
    if training_state is None:
        return _decision(
            request,
            allowed=False,
            classification="missing_training_state_manifest",
            reason="validated weight continuation requires checkpoint-local training-state inventory",
        )
    expected_fingerprint = request.checkpoint_fingerprint
    assert expected_fingerprint is not None
    if training_state.contract_fingerprint != expected_fingerprint:
        return _decision(
            request,
            allowed=False,
            classification="training_state_binding_mismatch",
            reason="training-state manifest is not bound to the checkpoint contract fingerprint",
        )
    expected_actor_identities = tuple(manifest.scale["ordered_agent_names"])
    if training_state.ordered_actor_identities != expected_actor_identities:
        return _decision(
            request,
            allowed=False,
            classification="actor_inventory_identity_mismatch",
            reason="training-state actor inventory does not match the contract's ordered actors",
        )
    if training_state.critic_artifact is None:
        return _decision(
            request,
            allowed=False,
            classification="missing_critic_inventory",
            reason="validated weight continuation requires critic inventory",
        )
    if bool(manifest.training_contract["value_norm_enabled"]) and training_state.value_normalizer_artifact is None:
        return _decision(
            request,
            allowed=False,
            classification="missing_value_normalizer_inventory",
            reason="validated weight continuation requires ValueNorm inventory when enabled",
        )
    if any(artifact.serialization_mode != "state_dict" for artifact in training_state.actor_artifacts):
        return _decision(
            request,
            allowed=False,
            classification="unsupported_serialization",
            reason="all actor artifacts must use state_dict serialization",
        )
    if not request.continuation_reset_acknowledged:
        return _decision(
            request,
            allowed=False,
            classification="acknowledgement_required",
            reason="contract and artifact inventory pass; continuation reset acknowledgement is required",
            required_acknowledgement=CONTINUATION_ACKNOWLEDGEMENT,
        )
    return _decision(
        request,
        allowed=True,
        classification="validated_weight_continuation",
        reason="exact contract and required weight inventory pass with reset acknowledgement",
        required_acknowledgement=CONTINUATION_ACKNOWLEDGEMENT,
    )


def decide_missing_metadata(
    *,
    purpose: CompatibilityPurpose,
    current_profile: str,
    resolver_enabled: bool,
    explicit_unversioned_legacy_fallback: bool,
) -> CompatibilityDecision:
    """Classify a metadata-free checkpoint without reading weight files."""

    if purpose == CompatibilityPurpose.STRUCTURAL_INSPECTION:
        return CompatibilityDecision(
            allowed=True,
            classification="structural_inspection_only",
            requested_purpose=purpose,
            mismatches=(),
            reason="metadata-free checkpoint may proceed only to weights-only CPU inventory inspection",
            next_action="weights_only_state_dict_inventory_inspection",
        )
    if (
        purpose == CompatibilityPurpose.NORMAL_EVALUATION
        and current_profile == "legacy"
        and resolver_enabled is False
        and explicit_unversioned_legacy_fallback
    ):
        return CompatibilityDecision(
            allowed=True,
            classification="legacy_evaluation_fallback",
            requested_purpose=purpose,
            mismatches=(),
            reason="explicit resolver-disabled unversioned legacy evaluation fallback is permitted",
            next_action="strict_legacy_state_dict_inventory_validation",
        )
    return CompatibilityDecision(
        allowed=False,
        classification="missing_metadata_hard_error",
        requested_purpose=purpose,
        mismatches=(),
        reason="metadata-free checkpoint is not permitted for the requested purpose/profile",
    )


def compare_state_dict_inventories(
    expected_entries: Iterable[StateDictTensorInventoryEntry | Mapping[str, Any]],
    actual_entries: Iterable[StateDictTensorInventoryEntry | Mapping[str, Any]],
) -> CompatibilityDecision:
    """Compare synthetic expected/actual state-dict inventories exactly."""

    purpose = CompatibilityPurpose.STRUCTURAL_INSPECTION
    try:
        expected = normalize_tensor_inventory(expected_entries)
        actual = normalize_tensor_inventory(actual_entries)
    except ContractValidationError as exc:
        return CompatibilityDecision(
            allowed=False,
            classification="invalid_tensor_inventory",
            requested_purpose=purpose,
            mismatches=(),
            reason=str(exc),
        )
    expected_by_key = {entry.key: entry for entry in expected}
    actual_by_key = {entry.key: entry for entry in actual}
    mismatches: list[CompatibilityMismatch] = []
    for key in sorted(expected_by_key.keys() - actual_by_key.keys()):
        mismatches.append(
            CompatibilityMismatch(key, "missing_tensor_key", expected_by_key[key].to_mapping(), None, "missing key")
        )
    for key in sorted(actual_by_key.keys() - expected_by_key.keys()):
        mismatches.append(
            CompatibilityMismatch(key, "unexpected_tensor_key", None, actual_by_key[key].to_mapping(), "unexpected key")
        )
    for key in sorted(expected_by_key.keys() & actual_by_key.keys()):
        expected_entry = expected_by_key[key]
        actual_entry = actual_by_key[key]
        if expected_entry.shape != actual_entry.shape:
            mismatches.append(
                CompatibilityMismatch(
                    f"{key}.shape",
                    "tensor_shape",
                    expected_entry.shape,
                    actual_entry.shape,
                    "tensor shape mismatch",
                )
            )
        if expected_entry.dtype != actual_entry.dtype:
            mismatches.append(
                CompatibilityMismatch(
                    f"{key}.dtype",
                    "tensor_dtype",
                    expected_entry.dtype,
                    actual_entry.dtype,
                    "tensor dtype mismatch",
                )
            )
    return CompatibilityDecision(
        allowed=not mismatches,
        classification="tensor_inventory_match" if not mismatches else "tensor_inventory_mismatch",
        requested_purpose=purpose,
        mismatches=tuple(mismatches),
        reason="tensor inventories match exactly" if not mismatches else "tensor inventories differ",
    )


__all__ = [
    "ArtifactFileInventoryEntry",
    "AssignmentCheckpointContractManifest",
    "AssignmentTrainingStateManifest",
    "CompatibilityDecision",
    "CompatibilityMismatch",
    "CompatibilityPurpose",
    "CompatibilityRequest",
    "ContractValidationError",
    "CONTINUATION_ACKNOWLEDGEMENT",
    "MANIFEST_FORMAT_VERSION",
    "NAMED_LIFECYCLE_ABLATION",
    "StateDictTensorInventoryEntry",
    "TRAINING_STATE_FORMAT_VERSION",
    "VALIDATED_WEIGHT_CONTINUATION_CANDIDATE",
    "canonical_decimal",
    "canonical_manifest_bytes",
    "compare_state_dict_inventories",
    "compute_manifest_sha256",
    "compute_tensor_inventory_sha256",
    "decide_missing_metadata",
    "evaluate_compatibility",
    "normalize_tensor_inventory",
    "verify_manifest_sha256",
]
