"""Project-owned checkpoint state support for installed HARL ValueNorm."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn


VALUE_NORMALIZER_STATE_KEYS = (
    "running_mean",
    "running_mean_sq",
    "debiasing_term",
)
VALUE_NORMALIZER_ADAPTER_CONTRACT_VERSION = "harl_valuenorm_runtime_state_v1"
VALUE_NORMALIZER_ARTIFACT_STATE_FORMAT = "harl_runtime_attribute_tensor_mapping_v1"
VALUE_NORMALIZER_IMPLEMENTATION_ID = "harl.common.valuenorm.ValueNorm"

_DTYPE_NAMES = {
    torch.bfloat16: "bfloat16",
    torch.bool: "bool",
    torch.float16: "float16",
    torch.float32: "float32",
    torch.float64: "float64",
    torch.int8: "int8",
    torch.int16: "int16",
    torch.int32: "int32",
    torch.int64: "int64",
    torch.uint8: "uint8",
}
_DTYPE_ALIASES = {
    "torch.bfloat16": "bfloat16",
    "torch.bool": "bool",
    "torch.float16": "float16",
    "torch.float": "float32",
    "torch.float32": "float32",
    "torch.float64": "float64",
    "torch.int8": "int8",
    "torch.int16": "int16",
    "torch.int32": "int32",
    "torch.int64": "int64",
    "torch.uint8": "uint8",
}
for _name in tuple(_DTYPE_ALIASES.values()):
    _DTYPE_ALIASES[_name] = _name


class ValueNormalizerCheckpointError(RuntimeError):
    """Raised when ValueNorm checkpoint state is invalid or cannot be restored."""


@dataclass(frozen=True)
class ValueNormalizerFieldInventory:
    name: str
    shape: tuple[int, ...]
    dtype: str
    device: str
    object_type: str
    is_parameter: bool


@dataclass(frozen=True)
class ValueNormalizerTargetInventory:
    implementation_id: str
    fields: tuple[ValueNormalizerFieldInventory, ...]
    input_shape: tuple[int, ...]
    norm_axes: int
    beta: float
    epsilon: float
    per_element_update: bool
    tensor_dtype: str

    def to_contract_mapping(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "adapter_contract_version": VALUE_NORMALIZER_ADAPTER_CONTRACT_VERSION,
            "artifact_state_format": VALUE_NORMALIZER_ARTIFACT_STATE_FORMAT,
            "implementation_id": self.implementation_id,
            "input_shape": list(self.input_shape),
            "norm_axes": self.norm_axes,
            "beta": self.beta,
            "epsilon": self.epsilon,
            "per_element_update": self.per_element_update,
            "tensor_dtype": self.tensor_dtype,
            "canonical_state_keys": list(VALUE_NORMALIZER_STATE_KEYS),
        }


def normalize_value_normalizer_dtype(dtype: torch.dtype | str) -> str:
    """Return the canonical checkpoint dtype name without device information."""

    if isinstance(dtype, torch.dtype):
        try:
            return _DTYPE_NAMES[dtype]
        except KeyError as exc:
            raise ValueNormalizerCheckpointError(f"unsupported ValueNorm dtype {dtype!s}") from exc
    value = str(dtype).strip().lower()
    try:
        return _DTYPE_ALIASES[value]
    except KeyError as exc:
        raise ValueNormalizerCheckpointError(f"unsupported ValueNorm dtype {dtype!r}") from exc


def _implementation_id(value_normalizer: Any) -> str:
    return f"{value_normalizer.__class__.__module__}.{value_normalizer.__class__.__qualname__}"


def _require_supported_implementation(value_normalizer: Any, *, operation: str) -> None:
    if value_normalizer is None:
        raise ValueNormalizerCheckpointError(f"{operation}: ValueNorm target must not be None")
    observed = _implementation_id(value_normalizer)
    if observed != VALUE_NORMALIZER_IMPLEMENTATION_ID:
        raise ValueNormalizerCheckpointError(
            f"{operation}: unsupported ValueNorm implementation expected="
            f"{VALUE_NORMALIZER_IMPLEMENTATION_ID!r} observed={observed!r}"
        )


def _normalize_input_shape(value: Any, *, operation: str) -> tuple[int, ...]:
    if isinstance(value, bool):
        raise ValueNormalizerCheckpointError(f"{operation}: input_shape must not be boolean")
    if isinstance(value, int):
        values = (value,)
    elif isinstance(value, (tuple, list, torch.Size)):
        values = tuple(value)
    else:
        raise ValueNormalizerCheckpointError(
            f"{operation}: input_shape must be int or shape sequence observed={type(value).__name__}"
        )
    if not values or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in values):
        raise ValueNormalizerCheckpointError(f"{operation}: invalid input_shape={values!r}")
    return tuple(int(item) for item in values)


def _require_finite(value: torch.Tensor, *, field: str, operation: str) -> None:
    if not torch.isfinite(value).all().item():
        raise ValueNormalizerCheckpointError(f"{operation}: field={field!r} contains nonfinite values")


def inspect_value_normalizer_target(value_normalizer: Any) -> ValueNormalizerTargetInventory:
    """Inspect installed HARL ValueNorm attributes without consulting Module state APIs."""

    operation = "inspect ValueNorm target"
    _require_supported_implementation(value_normalizer, operation=operation)
    input_shape = _normalize_input_shape(getattr(value_normalizer, "input_shape", None), operation=operation)
    norm_axes = getattr(value_normalizer, "norm_axes", None)
    if isinstance(norm_axes, bool) or not isinstance(norm_axes, int) or not 1 <= norm_axes <= len(input_shape):
        raise ValueNormalizerCheckpointError(
            f"{operation}: norm_axes must be in [1, {len(input_shape)}] observed={norm_axes!r}"
        )
    beta = getattr(value_normalizer, "beta", None)
    epsilon = getattr(value_normalizer, "epsilon", None)
    per_element_update = getattr(value_normalizer, "per_element_update", None)
    if isinstance(beta, bool) or not isinstance(beta, (int, float)) or not torch.isfinite(torch.tensor(float(beta))):
        raise ValueNormalizerCheckpointError(f"{operation}: beta must be finite numeric observed={beta!r}")
    if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)) or not torch.isfinite(torch.tensor(float(epsilon))):
        raise ValueNormalizerCheckpointError(f"{operation}: epsilon must be finite numeric observed={epsilon!r}")
    if not isinstance(per_element_update, bool):
        raise ValueNormalizerCheckpointError(
            f"{operation}: per_element_update must be bool observed={per_element_update!r}"
        )

    fields: list[ValueNormalizerFieldInventory] = []
    observed_dtype: str | None = None
    observed_device: str | None = None
    expected_shapes = {
        "running_mean": input_shape,
        "running_mean_sq": input_shape,
        "debiasing_term": (),
    }
    for name in VALUE_NORMALIZER_STATE_KEYS:
        if not hasattr(value_normalizer, name):
            raise ValueNormalizerCheckpointError(f"{operation}: missing required field={name!r}")
        value = getattr(value_normalizer, name)
        if not isinstance(value, torch.Tensor):
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={name!r} must be Tensor or Parameter observed={type(value).__name__}"
            )
        if tuple(value.shape) != expected_shapes[name]:
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={name!r} shape expected={expected_shapes[name]} "
                f"observed={tuple(value.shape)}"
            )
        _require_finite(value, field=name, operation=operation)
        dtype = normalize_value_normalizer_dtype(value.dtype)
        device = str(value.device)
        if observed_dtype is None:
            observed_dtype = dtype
            observed_device = device
        elif observed_dtype != dtype:
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={name!r} dtype expected={observed_dtype!r} observed={dtype!r}"
            )
        elif observed_device != device:
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={name!r} device expected={observed_device!r} observed={device!r}"
            )
        fields.append(
            ValueNormalizerFieldInventory(
                name=name,
                shape=tuple(value.shape),
                dtype=dtype,
                device=device,
                object_type=type(value).__name__,
                is_parameter=isinstance(value, nn.Parameter),
            )
        )
    assert observed_dtype is not None
    return ValueNormalizerTargetInventory(
        implementation_id=_implementation_id(value_normalizer),
        fields=tuple(fields),
        input_shape=input_shape,
        norm_axes=norm_axes,
        beta=float(beta),
        epsilon=float(epsilon),
        per_element_update=per_element_update,
        tensor_dtype=observed_dtype,
    )


def build_value_normalizer_contract(value_normalizer: Any | None, *, enabled: bool) -> dict[str, Any]:
    """Build the immutable enabled/disabled ValueNorm contract from live state."""

    if not isinstance(enabled, bool):
        raise ValueNormalizerCheckpointError(f"build ValueNorm contract: enabled must be bool observed={enabled!r}")
    if not enabled:
        if value_normalizer is not None:
            raise ValueNormalizerCheckpointError(
                "build ValueNorm contract: live ValueNorm exists while contract is disabled"
            )
        return {"enabled": False}
    if value_normalizer is None:
        raise ValueNormalizerCheckpointError(
            "build ValueNorm contract: live ValueNorm is required while contract is enabled"
        )
    return inspect_value_normalizer_target(value_normalizer).to_contract_mapping()


def validate_value_normalizer_target_contract(
    target_inventory: ValueNormalizerTargetInventory,
    value_normalizer_contract: Mapping[str, Any],
) -> None:
    """Require live ValueNorm semantics to match the immutable v2 contract.

    Runtime placement is deliberately absent: a CPU checkpoint may restore into
    a compatible CUDA target, but the installed HARL layout and scalar
    semantics are immutable compatibility inputs.
    """

    operation = "validate ValueNorm target contract"
    if not isinstance(value_normalizer_contract, Mapping):
        raise ValueNormalizerCheckpointError(f"{operation}: contract must be a mapping")
    if value_normalizer_contract.get("enabled") is not True:
        raise ValueNormalizerCheckpointError(
            f"{operation}: enabled ValueNorm contract is required"
        )
    try:
        expected = {
            "implementation_id": str(value_normalizer_contract["implementation_id"]),
            "input_shape": tuple(int(value) for value in value_normalizer_contract["input_shape"]),
            "norm_axes": int(value_normalizer_contract["norm_axes"]),
            "beta": float(value_normalizer_contract["beta"]),
            "epsilon": float(value_normalizer_contract["epsilon"]),
            "per_element_update": value_normalizer_contract["per_element_update"],
            "tensor_dtype": normalize_value_normalizer_dtype(
                value_normalizer_contract["tensor_dtype"]
            ),
            "canonical_state_keys": tuple(value_normalizer_contract["canonical_state_keys"]),
        }
    except Exception as exc:
        raise ValueNormalizerCheckpointError(
            f"{operation}: malformed immutable contract: {exc}"
        ) from exc
    observed = {
        "implementation_id": target_inventory.implementation_id,
        "input_shape": target_inventory.input_shape,
        "norm_axes": target_inventory.norm_axes,
        "beta": target_inventory.beta,
        "epsilon": target_inventory.epsilon,
        "per_element_update": target_inventory.per_element_update,
        "tensor_dtype": target_inventory.tensor_dtype,
        "canonical_state_keys": VALUE_NORMALIZER_STATE_KEYS,
    }
    for field, expected_value in expected.items():
        if observed[field] != expected_value:
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={field!r} expected={expected_value!r} "
                f"observed={observed[field]!r}"
            )


def _validate_checkpoint_mapping(
    checkpoint_state: Mapping[str, Any],
    *,
    inventory: ValueNormalizerTargetInventory | None,
    operation: str,
) -> OrderedDict[str, torch.Tensor]:
    if not isinstance(checkpoint_state, Mapping) or not checkpoint_state:
        raise ValueNormalizerCheckpointError(f"{operation}: checkpoint state must be a nonempty mapping")
    keys = tuple(str(key) for key in checkpoint_state.keys())
    if keys != VALUE_NORMALIZER_STATE_KEYS:
        raise ValueNormalizerCheckpointError(
            f"{operation}: canonical key order expected={VALUE_NORMALIZER_STATE_KEYS} observed={keys}"
        )
    output: OrderedDict[str, torch.Tensor] = OrderedDict()
    expected_fields = {} if inventory is None else {field.name: field for field in inventory.fields}
    for name in VALUE_NORMALIZER_STATE_KEYS:
        value = checkpoint_state[name]
        if not isinstance(value, torch.Tensor):
            raise ValueNormalizerCheckpointError(
                f"{operation}: field={name!r} must be Tensor observed={type(value).__name__}"
            )
        _require_finite(value, field=name, operation=operation)
        if inventory is not None:
            field = expected_fields[name]
            if tuple(value.shape) != field.shape:
                raise ValueNormalizerCheckpointError(
                    f"{operation}: field={name!r} shape expected={field.shape} observed={tuple(value.shape)}"
                )
            dtype = normalize_value_normalizer_dtype(value.dtype)
            if dtype != field.dtype:
                raise ValueNormalizerCheckpointError(
                    f"{operation}: field={name!r} dtype expected={field.dtype!r} observed={dtype!r}"
                )
        output[name] = value
    return output


def validate_value_normalizer_checkpoint_state(
    checkpoint_state: Mapping[str, Any],
    *,
    target_inventory: ValueNormalizerTargetInventory | None = None,
    value_normalizer_contract: Mapping[str, Any] | None = None,
) -> OrderedDict[str, torch.Tensor]:
    """Validate canonical checkpoint mapping, optionally against a live target inventory."""

    if target_inventory is not None and value_normalizer_contract is not None:
        raise ValueNormalizerCheckpointError(
            "validate ValueNorm checkpoint state: specify target inventory or contract, not both"
        )
    state = _validate_checkpoint_mapping(
        checkpoint_state,
        inventory=target_inventory,
        operation="validate ValueNorm checkpoint state",
    )
    if value_normalizer_contract is None:
        return state
    if value_normalizer_contract.get("enabled") is not True:
        raise ValueNormalizerCheckpointError(
            "validate ValueNorm checkpoint state: enabled ValueNorm contract is required"
        )
    try:
        expected_input_shape = tuple(int(value) for value in value_normalizer_contract["input_shape"])
        expected_dtype = normalize_value_normalizer_dtype(value_normalizer_contract["tensor_dtype"])
        expected_keys = tuple(value_normalizer_contract["canonical_state_keys"])
    except Exception as exc:
        raise ValueNormalizerCheckpointError(
            f"validate ValueNorm checkpoint state: malformed immutable contract: {exc}"
        ) from exc
    if expected_keys != VALUE_NORMALIZER_STATE_KEYS:
        raise ValueNormalizerCheckpointError(
            f"validate ValueNorm checkpoint state: contract canonical keys expected="
            f"{VALUE_NORMALIZER_STATE_KEYS} observed={expected_keys}"
        )
    expected_shapes = {
        "running_mean": expected_input_shape,
        "running_mean_sq": expected_input_shape,
        "debiasing_term": (),
    }
    for name, value in state.items():
        if tuple(value.shape) != expected_shapes[name]:
            raise ValueNormalizerCheckpointError(
                f"validate ValueNorm checkpoint state: field={name!r} shape expected="
                f"{expected_shapes[name]} observed={tuple(value.shape)}"
            )
        dtype = normalize_value_normalizer_dtype(value.dtype)
        if dtype != expected_dtype:
            raise ValueNormalizerCheckpointError(
                f"validate ValueNorm checkpoint state: field={name!r} dtype expected="
                f"{expected_dtype!r} observed={dtype!r}"
            )
    return state


def export_value_normalizer_checkpoint_state(value_normalizer: Any) -> OrderedDict[str, torch.Tensor]:
    """Export explicit mutable ValueNorm runtime state without Module state APIs."""

    inventory = inspect_value_normalizer_target(value_normalizer)
    output: OrderedDict[str, torch.Tensor] = OrderedDict()
    for field in inventory.fields:
        value = getattr(value_normalizer, field.name)
        output[field.name] = value.detach().clone().cpu()
    return _validate_checkpoint_mapping(
        output,
        inventory=inventory,
        operation="export ValueNorm checkpoint state",
    )


def _copy_target_field(target: torch.Tensor, source: torch.Tensor) -> None:
    target.copy_(source.to(device=target.device))


def restore_value_normalizer_checkpoint_state(
    value_normalizer: Any,
    checkpoint_state: Mapping[str, Any],
    *,
    strict: bool = True,
) -> None:
    """Strictly copy canonical state into a live ValueNorm with full rollback."""

    if strict is not True:
        raise ValueNormalizerCheckpointError("restore ValueNorm checkpoint state: strict=True is required")
    inventory = inspect_value_normalizer_target(value_normalizer)
    state = _validate_checkpoint_mapping(
        checkpoint_state,
        inventory=inventory,
        operation="restore ValueNorm checkpoint state",
    )
    targets = {name: getattr(value_normalizer, name) for name in VALUE_NORMALIZER_STATE_KEYS}
    target_ids = {name: id(targets[name]) for name in VALUE_NORMALIZER_STATE_KEYS}
    backups = {name: targets[name].detach().clone() for name in VALUE_NORMALIZER_STATE_KEYS}
    try:
        with torch.no_grad():
            for name in VALUE_NORMALIZER_STATE_KEYS:
                _copy_target_field(targets[name], state[name])
            for name in VALUE_NORMALIZER_STATE_KEYS:
                expected = state[name].to(device=targets[name].device)
                if id(getattr(value_normalizer, name)) != target_ids[name]:
                    raise ValueNormalizerCheckpointError(
                        f"restore ValueNorm checkpoint state: field={name!r} object identity changed"
                    )
                if not torch.equal(targets[name], expected):
                    raise ValueNormalizerCheckpointError(
                        f"restore ValueNorm checkpoint state: field={name!r} verification mismatch"
                    )
                _require_finite(targets[name], field=name, operation="restore ValueNorm checkpoint state")
    except Exception as exc:
        rollback_errors: list[str] = []
        with torch.no_grad():
            for name in VALUE_NORMALIZER_STATE_KEYS:
                try:
                    _copy_target_field(targets[name], backups[name])
                except Exception as rollback_exc:  # pragma: no cover - hardware/runtime defensive path.
                    rollback_errors.append(f"{name}: {rollback_exc}")
        raise ValueNormalizerCheckpointError(
            "restore ValueNorm checkpoint state failed; "
            f"original_error={exc}; rollback_errors={rollback_errors}"
        ) from exc


__all__ = [
    "VALUE_NORMALIZER_ADAPTER_CONTRACT_VERSION",
    "VALUE_NORMALIZER_ARTIFACT_STATE_FORMAT",
    "VALUE_NORMALIZER_IMPLEMENTATION_ID",
    "VALUE_NORMALIZER_STATE_KEYS",
    "ValueNormalizerCheckpointError",
    "ValueNormalizerFieldInventory",
    "ValueNormalizerTargetInventory",
    "build_value_normalizer_contract",
    "export_value_normalizer_checkpoint_state",
    "inspect_value_normalizer_target",
    "normalize_value_normalizer_dtype",
    "restore_value_normalizer_checkpoint_state",
    "validate_value_normalizer_target_contract",
    "validate_value_normalizer_checkpoint_state",
]
