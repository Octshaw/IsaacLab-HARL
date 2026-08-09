"""Pure typed DTO contracts for event-gated local MRTA.

Phase A3 freezes schema, identity, alias-isolation, and algebraic consistency
only.  Nothing in this module schedules an assignment tick, constructs a local
set, selects Top-K candidates, samples a policy, builds a transfer graph,
arbitrates a component, commits ownership, or changes reward/runtime behavior.

Tensor immutability is an observable supported-path contract: construction
isolates source aliases, public accessors return clones, and normal in-place
corruption of private backing tensors is detected before supported reads.
This is not a cryptographic or adversarial-reflection guarantee.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_MRTA_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract"
)
ASSIGNMENT_MRTA_SOURCE_PURPOSE = (
    "pure event-gated local MRTA data-transfer contracts"
)

if __name__ != CANONICAL_ASSIGNMENT_MRTA_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment MRTA contract source must "
        "fail before declaring identity-bearing types or importing torch; "
        f"expected module key={CANONICAL_ASSIGNMENT_MRTA_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose={ASSIGNMENT_MRTA_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, IntEnum
import math
import re
from types import MappingProxyType
from typing import ClassVar

import torch

from .assignment_event_contract import (
    AssignmentOpportunityRecord,
    LifecycleEventRecord,
    ResolverDiagnosticRecord,
    validate_assignment_opportunity_records,
    validate_lifecycle_event_records,
    validate_local_trigger_sources,
)


ASSIGNMENT_MRTA_CONTRACT_VERSION = "assignment_mrta_contract_v2"
OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION = (
    "assignment_tensor_alias_isolation_v1"
)
UNRESOLVED_PARAMETER_SPEC_VERSION = "unresolved_parameter_spec_v1"
NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION = "nominal_pair_cost_result_v1"
LOCAL_SET_REQUEST_SCHEMA_VERSION = "local_set_request_v1"
LOCAL_SET_RESULT_SCHEMA_VERSION = "local_set_result_v1"
TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION = "top_k_candidate_result_v1"
DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION = (
    "decision_valid_mask_snapshot_v1"
)
PROPOSAL_SNAPSHOT_SCHEMA_VERSION = "proposal_snapshot_v1"
TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION = "transfer_component_request_v1"
TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION = "transfer_component_result_v1"
COMPONENT_REJECTION_RECORD_SCHEMA_VERSION = "component_rejection_record_v1"
ACTION_CONTRACT_VERSION = "event_gated_action_contract_v1"
LOCAL_CANDIDATE_SEMANTICS_VERSION = (
    "event_gated_local_candidate_semantics_v1"
)
COST_PATH_SEMANTICS_VERSION = "event_gated_cost_path_semantics_v1"
COMPONENT_SEMANTICS_VERSION = "event_gated_component_semantics_v1"

_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1
_CANONICAL_STRING_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:[.-][a-z0-9_]+)*$")


class AssignmentMrtaContractError(RuntimeError):
    """Base error with stable A3 MRTA schema context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
        env_id: object = None,
        robot_id: object = None,
        task_id: object = None,
        schema_version: str = ASSIGNMENT_MRTA_CONTRACT_VERSION,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        self.env_id = env_id
        self.robot_id = robot_id
        self.task_id = task_id
        self.schema_version = schema_version
        super().__init__(
            f"{message}; failure_code={failure_code!r}; "
            f"field_name={field_name!r}; expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; env_id={env_id!r}; "
            f"robot_id={robot_id!r}; task_id={task_id!r}; "
            f"schema_version={schema_version!r}"
        )


class MrtaSchemaError(AssignmentMrtaContractError):
    """An MRTA DTO violates its exact schema or frozen relation."""


class MrtaGenerationError(AssignmentMrtaContractError):
    """An MRTA DTO has invalid or mismatched generation identity."""


class MrtaSnapshotMutationError(AssignmentMrtaContractError):
    """Supported-path mutation of protected tensor backing was detected."""


class LocalSetOverflowDisposition(IntEnum):
    """Frozen local-set overflow handling."""

    NONE = 0
    FAIL_CLOSED_NO_ASSIGNMENT = 1


class ProposalKind(str, Enum):
    """Semantic policy proposal kind in canonical order."""

    CLAIM = "claim"
    CONTINUE = "continue"
    SWITCH = "switch"
    NOOP_IDLE = "noop_idle"


class StoredActionRowKind(str, Enum):
    """Storage presence is distinct from policy-proposal presence."""

    POLICY_PROPOSAL = "policy_proposal"
    FORCED_NONDECISION = "forced_nondecision"
    NO_ROW = "no_row"


class ComponentRejectionReason(str, Enum):
    """Canonical first-reason precedence for ordinary component rejection."""

    NONE = "none"
    CONTENTION_LOSS = "contention_loss"
    INCOMPLETE_TRANSFER_CHAIN = "incomplete_transfer_chain"
    OWNERSHIP_COORDINATION_INVALID = "ownership_coordination_invalid"
    PREEMPTION_INELIGIBLE = "preemption_ineligible"
    ASSIGNED_UNFINISHED_COUNT_DECREASE = "assigned_unfinished_count_decrease"
    PAIR_IMPROVEMENT_NOT_MET = "pair_improvement_not_met"
    COMPONENT_IMPROVEMENT_NOT_MET = "component_improvement_not_met"
    LOCAL_SET_OVERFLOW_FAIL_CLOSED = "local_set_overflow_fail_closed"
    POST_SNAPSHOT_SYSTEM_INVALIDATION = "post_snapshot_system_invalidation"
    TERMINAL_TRANSITION = "terminal_transition"


_NON_POLICY_REJECTION_REASONS = frozenset(
    {
        ComponentRejectionReason.LOCAL_SET_OVERFLOW_FAIL_CLOSED,
        ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION,
        ComponentRejectionReason.TERMINAL_TRANSITION,
    }
)


def _context_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, torch.dtype):
        return str(value)
    if isinstance(value, torch.device):
        return str(value)
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return value


def _require_mapping_keys(
    values: object,
    *,
    field_order: tuple[str, ...],
    schema_version: str,
) -> Mapping[str, object]:
    if not isinstance(values, Mapping):
        raise MrtaSchemaError(
            "DTO input must be a mapping",
            failure_code="mapping_type",
            expected="Mapping[str, object]",
            actual=type(values),
            schema_version=schema_version,
        )
    non_string = tuple(
        sorted((key for key in values if type(key) is not str), key=repr)
    )
    actual_keys = set(values)
    expected_keys = set(field_order)
    missing = tuple(name for name in field_order if name not in actual_keys)
    unexpected = tuple(sorted(actual_keys - expected_keys, key=repr))
    if non_string or missing or unexpected:
        raise MrtaSchemaError(
            "DTO mapping does not have its exact field set",
            failure_code="mapping_fields",
            expected=field_order,
            actual={
                "non_string": non_string,
                "missing": missing,
                "unexpected": unexpected,
            },
            schema_version=schema_version,
        )
    return values


def _require_schema_version(
    value: object,
    *,
    expected: str,
) -> None:
    if type(value) is not str or value != expected:
        raise MrtaSchemaError(
            "schema_version does not match the exact DTO schema",
            failure_code="schema_version",
            field_name="schema_version",
            expected=expected,
            actual=value,
            schema_version=expected,
        )


def _require_explicit_device(
    device: object,
    *,
    schema_version: str,
) -> torch.device:
    if type(device) is not torch.device:
        raise MrtaSchemaError(
            "tensor DTO construction requires an explicit torch.device",
            failure_code="device",
            field_name="device",
            expected="torch.device",
            actual=type(device),
            schema_version=schema_version,
        )
    return device


def _require_int64_scalar(
    value: object,
    *,
    field_name: str,
    schema_version: str,
    nonnegative: bool,
    allow_minus_one: bool = False,
) -> int:
    if type(value) is not int:
        raise MrtaSchemaError(
            f"{field_name} must be an exact Python int",
            failure_code="scalar_type",
            field_name=field_name,
            expected="signed int64 scalar",
            actual=type(value),
            schema_version=schema_version,
        )
    if value < _INT64_MIN or value > _INT64_MAX:
        raise MrtaSchemaError(
            f"{field_name} is outside signed int64 range",
            failure_code="scalar_range",
            field_name=field_name,
            expected=(_INT64_MIN, _INT64_MAX),
            actual=value,
            schema_version=schema_version,
        )
    if nonnegative and value < 0 and not (allow_minus_one and value == -1):
        raise MrtaGenerationError(
            f"{field_name} must be non-negative",
            failure_code="generation_nonnegative",
            field_name=field_name,
            expected=">= 0",
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_bool_scalar(
    value: object,
    *,
    field_name: str,
    schema_version: str,
) -> bool:
    if type(value) is not bool:
        raise MrtaSchemaError(
            f"{field_name} must be an exact Python bool",
            failure_code="scalar_type",
            field_name=field_name,
            expected="bool",
            actual=type(value),
            schema_version=schema_version,
        )
    return value


def _require_finite_float(
    value: object,
    *,
    field_name: str,
    schema_version: str,
    nonnegative: bool,
) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise MrtaSchemaError(
            f"{field_name} must be a finite exact Python float",
            failure_code="finite_float",
            field_name=field_name,
            expected="finite float",
            actual=value,
            schema_version=schema_version,
        )
    if nonnegative and value < 0.0:
        raise MrtaSchemaError(
            f"{field_name} must be non-negative",
            failure_code="nonnegative",
            field_name=field_name,
            expected=">= 0",
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_canonical_string(
    value: object,
    *,
    field_name: str,
    schema_version: str,
) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or _CANONICAL_STRING_PATTERN.fullmatch(value) is None
    ):
        raise MrtaSchemaError(
            f"{field_name} must be a non-empty canonical string",
            failure_code="canonical_string",
            field_name=field_name,
            expected="[a-z][a-z0-9_]*(.[a-z0-9_]+ or -segment)*",
            actual=value,
            schema_version=schema_version,
        )
    return value


def _first_true_index(mask: torch.Tensor) -> tuple[int, ...] | None:
    indices = torch.nonzero(mask, as_tuple=False)
    if indices.numel() == 0:
        return None
    return tuple(int(item.item()) for item in indices[0])


@dataclass(frozen=True, slots=True)
class UnresolvedParameterSpec:
    """Identity and phase ownership of a deliberately unresolved parameter."""

    name: str
    owner_phase: str
    semantic_purpose: str

    def __post_init__(self) -> None:
        for field_name in ("name", "owner_phase", "semantic_purpose"):
            _require_canonical_string(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=UNRESOLVED_PARAMETER_SPEC_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "name": self.name,
                "owner_phase": self.owner_phase,
                "semantic_purpose": self.semantic_purpose,
            }
        )


@dataclass(frozen=True, slots=True, eq=False)
class _ProtectedTensor:
    """Private tensor clone plus replaceable integrity metadata."""

    _tensor: torch.Tensor = field(repr=False)
    _shape: tuple[int, ...]
    _dtype: torch.dtype
    _device: torch.device
    _requires_grad: bool
    _contiguous: bool
    _mutation_version: int = field(repr=False)

    @classmethod
    def capture(
        cls,
        value: object,
        *,
        field_name: str,
        expected_shape: tuple[int, ...],
        expected_dtype: torch.dtype,
        expected_device: torch.device,
        schema_version: str,
    ) -> "_ProtectedTensor":
        if type(value) is not torch.Tensor:
            raise MrtaSchemaError(
                f"{field_name} must be an exact torch.Tensor",
                failure_code="tensor_type",
                field_name=field_name,
                expected="torch.Tensor",
                actual=type(value),
                schema_version=schema_version,
            )
        if value.dtype is not expected_dtype:
            raise MrtaSchemaError(
                f"{field_name} has the wrong dtype; implicit cast is forbidden",
                failure_code="dtype",
                field_name=field_name,
                expected=expected_dtype,
                actual=value.dtype,
                schema_version=schema_version,
            )
        if value.device != expected_device:
            raise MrtaSchemaError(
                f"{field_name} is on the wrong device; implicit move is forbidden",
                failure_code="device",
                field_name=field_name,
                expected=expected_device,
                actual=value.device,
                schema_version=schema_version,
            )
        if tuple(value.shape) != expected_shape:
            raise MrtaSchemaError(
                f"{field_name} has the wrong shape",
                failure_code="shape",
                field_name=field_name,
                expected=expected_shape,
                actual=tuple(value.shape),
                schema_version=schema_version,
            )
        if value.requires_grad:
            raise MrtaSchemaError(
                f"{field_name} must not require gradients",
                failure_code="requires_grad",
                field_name=field_name,
                expected=False,
                actual=True,
                schema_version=schema_version,
            )
        with torch.inference_mode(False):
            cloned = value.detach().clone().contiguous()
        return cls(
            _tensor=cloned,
            _shape=tuple(cloned.shape),
            _dtype=cloned.dtype,
            _device=cloned.device,
            _requires_grad=bool(cloned.requires_grad),
            _contiguous=bool(cloned.is_contiguous()),
            _mutation_version=int(cloned._version),
        )

    def validate(self, *, field_name: str, schema_version: str) -> None:
        tensor = self._tensor
        actual = (
            tuple(tensor.shape),
            tensor.dtype,
            tensor.device,
            bool(tensor.requires_grad),
            bool(tensor.is_contiguous()),
            int(tensor._version),
        )
        expected = (
            self._shape,
            self._dtype,
            self._device,
            self._requires_grad,
            self._contiguous,
            self._mutation_version,
        )
        if actual != expected:
            raise MrtaSnapshotMutationError(
                "protected MRTA tensor changed after construction",
                failure_code="snapshot_mutation",
                field_name=field_name,
                expected="protected tensor integrity unchanged",
                actual="supported-path mutation detected",
                schema_version=schema_version,
            )

    def clone(self, *, field_name: str, schema_version: str) -> torch.Tensor:
        self.validate(field_name=field_name, schema_version=schema_version)
        return self._tensor.detach().clone().contiguous()

    def internal(self, *, field_name: str, schema_version: str) -> torch.Tensor:
        self.validate(field_name=field_name, schema_version=schema_version)
        return self._tensor


_BATCH_GENERATION_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("assignment_tick_generation", ("E",), torch.int64),
)


def _shape_from_symbols(
    symbols: tuple[str, ...],
    *,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    top_k: int = 1,
) -> tuple[int, ...]:
    sizes = {
        "E": num_envs,
        "M": num_robots,
        "N": num_tasks,
        "K": top_k,
        "A": num_tasks + 1,
        "ONE": 1,
    }
    return tuple(sizes[symbol] for symbol in symbols)


def _infer_ranked_tensor(
    value: object,
    *,
    field_name: str,
    rank: int,
    schema_version: str,
) -> tuple[int, ...]:
    if type(value) is not torch.Tensor:
        raise MrtaSchemaError(
            f"{field_name} must be an exact torch.Tensor",
            failure_code="tensor_type",
            field_name=field_name,
            expected="torch.Tensor",
            actual=type(value),
            schema_version=schema_version,
        )
    if value.ndim != rank:
        raise MrtaSchemaError(
            f"{field_name} has the wrong rank",
            failure_code="shape",
            field_name=field_name,
            expected=f"rank {rank}",
            actual=tuple(value.shape),
            schema_version=schema_version,
        )
    return tuple(int(size) for size in value.shape)


def _capture_tensor_specs(
    values: Mapping[str, object],
    *,
    specs: tuple[tuple[str, tuple[str, ...], torch.dtype], ...],
    device: torch.device,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    schema_version: str,
    top_k: int = 1,
) -> Mapping[str, _ProtectedTensor]:
    protected: dict[str, _ProtectedTensor] = {}
    for name, symbols, dtype in specs:
        protected[name] = _ProtectedTensor.capture(
            values[name],
            field_name=name,
            expected_shape=_shape_from_symbols(
                symbols,
                num_envs=num_envs,
                num_robots=num_robots,
                num_tasks=num_tasks,
                top_k=top_k,
            ),
            expected_dtype=dtype,
            expected_device=device,
            schema_version=schema_version,
        )
    return MappingProxyType(protected)


def _initialize_tensor_dto(
    instance: object,
    *,
    schema_version: str,
    device: torch.device,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    tensor_snapshots: Mapping[str, _ProtectedTensor],
    metadata: Mapping[str, object] | None = None,
) -> None:
    object.__setattr__(instance, "schema_version", schema_version)
    object.__setattr__(instance, "_device", device)
    object.__setattr__(instance, "_num_envs", num_envs)
    object.__setattr__(instance, "_num_robots", num_robots)
    object.__setattr__(instance, "_num_tasks", num_tasks)
    object.__setattr__(instance, "_tensor_snapshots", tensor_snapshots)
    if metadata is not None:
        for name, value in metadata.items():
            object.__setattr__(instance, name, value)


class _TensorDtoMixin:
    """Shared supported-path mechanics; not a public schema type."""

    __slots__ = ()

    _SCHEMA_VERSION: ClassVar[str]
    _TENSOR_SPECS: ClassVar[
        tuple[tuple[str, tuple[str, ...], torch.dtype], ...]
    ]

    def validate_integrity(self) -> None:
        if self.schema_version != self._SCHEMA_VERSION:
            raise MrtaSnapshotMutationError(
                "MRTA DTO schema metadata changed after construction",
                failure_code="snapshot_metadata",
                field_name="schema_version",
                expected=self._SCHEMA_VERSION,
                actual=self.schema_version,
                schema_version=self._SCHEMA_VERSION,
            )
        if type(self._tensor_snapshots) is not MappingProxyType:
            raise MrtaSnapshotMutationError(
                "MRTA DTO tensor index changed after construction",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected="private read-only mapping",
                actual=type(self._tensor_snapshots),
                schema_version=self._SCHEMA_VERSION,
            )
        expected_names = tuple(name for name, _, _ in self._TENSOR_SPECS)
        if tuple(self._tensor_snapshots) != expected_names:
            raise MrtaSnapshotMutationError(
                "MRTA DTO tensor field order changed after construction",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected=expected_names,
                actual=tuple(self._tensor_snapshots),
                schema_version=self._SCHEMA_VERSION,
            )
        for name, snapshot in self._tensor_snapshots.items():
            if type(snapshot) is not _ProtectedTensor:
                raise MrtaSnapshotMutationError(
                    "MRTA DTO private tensor wrapper changed",
                    failure_code="snapshot_metadata",
                    field_name=name,
                    expected=_ProtectedTensor,
                    actual=type(snapshot),
                    schema_version=self._SCHEMA_VERSION,
                )
            snapshot.validate(
                field_name=name,
                schema_version=self._SCHEMA_VERSION,
            )

    @property
    def device(self) -> torch.device:
        self.validate_integrity()
        return self._device

    @property
    def num_envs(self) -> int:
        self.validate_integrity()
        return self._num_envs

    @property
    def num_robots(self) -> int:
        self.validate_integrity()
        return self._num_robots

    @property
    def num_tasks(self) -> int:
        self.validate_integrity()
        return self._num_tasks

    def _validated_internal_tensors(self) -> dict[str, torch.Tensor]:
        self.validate_integrity()
        return {
            name: snapshot.internal(
                field_name=name,
                schema_version=self._SCHEMA_VERSION,
            )
            for name, snapshot in self._tensor_snapshots.items()
        }

    def _clone_tensor(self, name: str) -> torch.Tensor:
        self.validate_integrity()
        return self._tensor_snapshots[name].clone(
            field_name=name,
            schema_version=self._SCHEMA_VERSION,
        )


def _tensor_property(name: str) -> property:
    return property(lambda self: self._clone_tensor(name))


def _validate_batch_generation(
    tensors: Mapping[str, torch.Tensor],
    *,
    num_envs: int,
    schema_version: str,
) -> None:
    env_id = tensors["env_id"]
    if int(torch.unique(env_id).numel()) != num_envs:
        raise MrtaGenerationError(
            "env_id rows must be unique",
            failure_code="env_id_unique",
            field_name="env_id",
            expected=f"{num_envs} unique IDs",
            actual=tuple(int(item.item()) for item in env_id),
            schema_version=schema_version,
        )
    for name in (
        "episode_generation",
        "transition_generation",
        "assignment_tick_generation",
    ):
        index = _first_true_index(tensors[name] < 0)
        if index is not None:
            row = index[0]
            raise MrtaGenerationError(
                f"{name} must be non-negative",
                failure_code="generation_nonnegative",
                field_name=name,
                expected=">= 0",
                actual=int(tensors[name][row].item()),
                env_id=int(env_id[row].item()),
                schema_version=schema_version,
            )


def _mapping_with_cloned_tensors(
    dto: _TensorDtoMixin,
    *,
    field_order: tuple[str, ...],
    scalar_values: Mapping[str, object],
) -> Mapping[str, object]:
    dto.validate_integrity()
    result: dict[str, object] = {}
    for name in field_order:
        if name in dto._tensor_snapshots:
            result[name] = dto._clone_tensor(name)
        else:
            result[name] = scalar_values[name]
    return MappingProxyType(result)


_NOMINAL_COST_TENSOR_SPECS = (
    ("navigation_cost", ("E", "M", "N"), torch.float32),
    ("alignment_cost", ("E", "M", "N"), torch.float32),
    ("nominal_cost", ("E", "M", "N"), torch.float32),
    ("path_valid", ("E", "M", "N"), torch.bool),
    *_BATCH_GENERATION_SPECS,
)
_NOMINAL_COST_FIELD_ORDER = (
    "schema_version",
    "navigation_cost",
    "alignment_cost",
    "nominal_cost",
    "path_valid",
    "cost_unit",
    "estimator_version",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class NominalPairCostResult(_TensorDtoMixin):
    """Caller-produced nominal pair costs; this DTO runs no estimator."""

    schema_version: str
    cost_unit: str
    estimator_version: str
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION
    _TENSOR_SPECS = _NOMINAL_COST_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "NominalPairCostResult must be created by from_mapping()",
            failure_code="factory_required",
            expected="NominalPairCostResult.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
    ) -> "NominalPairCostResult":
        values = _require_mapping_keys(
            values,
            field_order=_NOMINAL_COST_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        shape = _infer_ranked_tensor(
            values["navigation_cost"],
            field_name="navigation_cost",
            rank=3,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_robots, num_tasks = shape
        if min(shape) <= 0:
            raise MrtaSchemaError(
                "nominal cost requires E > 0, M > 0, N > 0",
                failure_code="dimensions",
                expected="E>0,M>0,N>0",
                actual=shape,
                schema_version=cls._SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
            metadata={
                "cost_unit": _require_canonical_string(
                    values["cost_unit"],
                    field_name="cost_unit",
                    schema_version=cls._SCHEMA_VERSION,
                ),
                "estimator_version": _require_canonical_string(
                    values["estimator_version"],
                    field_name="estimator_version",
                    schema_version=cls._SCHEMA_VERSION,
                ),
            },
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        valid = tensors["path_valid"]
        for name in ("navigation_cost", "alignment_cost", "nominal_cost"):
            value = tensors[name]
            invalid_valid_cell = valid & (~torch.isfinite(value) | (value < 0))
            index = _first_true_index(invalid_valid_cell)
            if index is not None:
                env, robot, task = index
                raise MrtaSchemaError(
                    f"{name} must be finite and non-negative on valid paths",
                    failure_code="valid_cost",
                    field_name=name,
                    expected="finite and >= 0",
                    actual=float(value[env, robot, task].item()),
                    env_id=int(tensors["env_id"][env].item()),
                    robot_id=robot,
                    task_id=task,
                    schema_version=self._SCHEMA_VERSION,
                )
            invalid_path_not_nan = ~valid & ~torch.isnan(value)
            index = _first_true_index(invalid_path_not_nan)
            if index is not None:
                env, robot, task = index
                raise MrtaSchemaError(
                    f"{name} must be canonical NaN when path_valid is false",
                    failure_code="invalid_path_nan",
                    field_name=name,
                    expected="NaN",
                    actual=float(value[env, robot, task].item()),
                    env_id=int(tensors["env_id"][env].item()),
                    robot_id=robot,
                    task_id=task,
                    schema_version=self._SCHEMA_VERSION,
                )
        expected_nominal = (
            tensors["navigation_cost"] + tensors["alignment_cost"]
        )
        if not torch.equal(
            tensors["nominal_cost"][valid],
            expected_nominal[valid],
        ):
            raise MrtaSchemaError(
                "nominal_cost must exactly equal navigation + alignment",
                failure_code="nominal_sum",
                field_name="nominal_cost",
                expected="navigation_cost + alignment_cost",
                actual="valid cells differ",
                schema_version=self._SCHEMA_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_NOMINAL_COST_FIELD_ORDER,
            scalar_values={
                "schema_version": self.schema_version,
                "cost_unit": self.cost_unit,
                "estimator_version": self.estimator_version,
            },
        )


for _name, _, _ in _NOMINAL_COST_TENSOR_SPECS:
    setattr(NominalPairCostResult, _name, _tensor_property(_name))


_LOCAL_SET_REQUEST_TENSOR_SPECS = (
    ("seed_robot_mask", ("E", "M"), torch.bool),
    ("needs_assignment_mask", ("E", "M"), torch.bool),
    ("robot_available_mask", ("E", "M"), torch.bool),
    ("task_state", ("E", "N"), torch.int64),
    ("event_updated_ownership", ("E", "N"), torch.int64),
    *_BATCH_GENERATION_SPECS,
)
_LOCAL_SET_REQUEST_FIELD_ORDER = (
    "schema_version",
    "seed_robot_mask",
    "needs_assignment_mask",
    "robot_available_mask",
    "task_state",
    "event_updated_ownership",
    "lifecycle_event_records",
    "assignment_opportunities",
    "top_k_spec",
    "robot_cap_spec",
    "task_cap_spec",
    "owner_expansion_rounds",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


def _validate_per_env_trigger_collections(
    lifecycle_records: object,
    opportunities: object,
    *,
    tensors: Mapping[str, torch.Tensor],
    num_envs: int,
    schema_version: str,
) -> tuple[
    tuple[tuple[LifecycleEventRecord, ...], ...],
    tuple[tuple[AssignmentOpportunityRecord, ...], ...],
]:
    if type(lifecycle_records) is not tuple or type(opportunities) is not tuple:
        raise MrtaSchemaError(
            "local trigger collections must be exact immutable per-env tuples",
            failure_code="trigger_collection_type",
            expected="tuple[tuple[canonical record, ...], ...]",
            actual=(type(lifecycle_records), type(opportunities)),
            schema_version=schema_version,
        )
    if len(lifecycle_records) != num_envs or len(opportunities) != num_envs:
        raise MrtaSchemaError(
            "local trigger collection outer length must equal E",
            failure_code="trigger_collection_shape",
            expected=num_envs,
            actual=(len(lifecycle_records), len(opportunities)),
            schema_version=schema_version,
        )
    checked_events: list[tuple[LifecycleEventRecord, ...]] = []
    checked_opportunities: list[tuple[AssignmentOpportunityRecord, ...]] = []
    for row in range(num_envs):
        event_row = lifecycle_records[row]
        opportunity_row = opportunities[row]
        if type(event_row) is not tuple or type(opportunity_row) is not tuple:
            raise MrtaSchemaError(
                "each per-env trigger collection must be an exact tuple",
                failure_code="trigger_collection_type",
                expected="tuple",
                actual=(type(event_row), type(opportunity_row)),
                env_id=int(tensors["env_id"][row].item()),
                schema_version=schema_version,
            )
        try:
            canonical_events = validate_lifecycle_event_records(event_row)
            canonical_opportunities = validate_assignment_opportunity_records(
                opportunity_row
            )
            validate_local_trigger_sources(
                canonical_events + canonical_opportunities
            )
        except Exception as exc:
            raise MrtaSchemaError(
                "local trigger collection violates canonical event placement",
                failure_code="trigger_placement",
                expected=(
                    "LifecycleEventRecord and AssignmentOpportunityRecord only"
                ),
                actual=f"{type(exc).__module__}.{type(exc).__qualname__}: {exc}",
                env_id=int(tensors["env_id"][row].item()),
                schema_version=schema_version,
            ) from exc
        env_id = int(tensors["env_id"][row].item())
        episode = int(tensors["episode_generation"][row].item())
        transition = int(tensors["transition_generation"][row].item())
        tick = int(tensors["assignment_tick_generation"][row].item())
        for record in canonical_events:
            if (
                type(record) is not LifecycleEventRecord
                or record.env_id != env_id
                or record.episode_generation != episode
                or record.transition_generation != transition
            ):
                raise MrtaGenerationError(
                    "lifecycle event differs from LocalSetRequest generation",
                    failure_code="trigger_generation",
                    expected=(env_id, episode, transition),
                    actual=(
                        getattr(record, "env_id", None),
                        getattr(record, "episode_generation", None),
                        getattr(record, "transition_generation", None),
                    ),
                    env_id=env_id,
                    schema_version=schema_version,
                )
        for record in canonical_opportunities:
            if (
                type(record) is not AssignmentOpportunityRecord
                or record.env_id != env_id
                or record.episode_generation != episode
                or record.transition_generation != transition
                or record.assignment_tick_generation != tick
            ):
                raise MrtaGenerationError(
                    "assignment opportunity differs from LocalSetRequest generation",
                    failure_code="trigger_generation",
                    expected=(env_id, episode, transition, tick),
                    actual=(
                        getattr(record, "env_id", None),
                        getattr(record, "episode_generation", None),
                        getattr(record, "transition_generation", None),
                        getattr(record, "assignment_tick_generation", None),
                    ),
                    env_id=env_id,
                    schema_version=schema_version,
                )
        checked_events.append(canonical_events)
        checked_opportunities.append(canonical_opportunities)
    return tuple(checked_events), tuple(checked_opportunities)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class LocalSetRequest(_TensorDtoMixin):
    """Validated local-set inputs; no local set is constructed here."""

    schema_version: str
    lifecycle_event_records: tuple[tuple[LifecycleEventRecord, ...], ...]
    assignment_opportunities: tuple[
        tuple[AssignmentOpportunityRecord, ...], ...
    ]
    top_k_spec: UnresolvedParameterSpec
    robot_cap_spec: UnresolvedParameterSpec
    task_cap_spec: UnresolvedParameterSpec
    owner_expansion_rounds: int
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = LOCAL_SET_REQUEST_SCHEMA_VERSION
    _TENSOR_SPECS = _LOCAL_SET_REQUEST_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "LocalSetRequest must be created by from_mapping()",
            failure_code="factory_required",
            expected="LocalSetRequest.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
    ) -> "LocalSetRequest":
        values = _require_mapping_keys(
            values,
            field_order=_LOCAL_SET_REQUEST_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        robot_shape = _infer_ranked_tensor(
            values["seed_robot_mask"],
            field_name="seed_robot_mask",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        task_shape = _infer_ranked_tensor(
            values["task_state"],
            field_name="task_state",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_robots = robot_shape
        task_envs, num_tasks = task_shape
        if (
            min(num_envs, num_robots, num_tasks) <= 0
            or task_envs != num_envs
        ):
            raise MrtaSchemaError(
                "local-set request requires consistent positive E, M, N",
                failure_code="dimensions",
                expected="E>0,M>0,N>0 and matching E",
                actual=(robot_shape, task_shape),
                schema_version=cls._SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        internal = {
            name: snapshot.internal(
                field_name=name,
                schema_version=cls._SCHEMA_VERSION,
            )
            for name, snapshot in snapshots.items()
        }
        _validate_batch_generation(
            internal,
            num_envs=num_envs,
            schema_version=cls._SCHEMA_VERSION,
        )
        events, opportunities = _validate_per_env_trigger_collections(
            values["lifecycle_event_records"],
            values["assignment_opportunities"],
            tensors=internal,
            num_envs=num_envs,
            schema_version=cls._SCHEMA_VERSION,
        )
        specs: dict[str, UnresolvedParameterSpec] = {}
        for name in ("top_k_spec", "robot_cap_spec", "task_cap_spec"):
            value = values[name]
            if type(value) is not UnresolvedParameterSpec:
                raise MrtaSchemaError(
                    f"{name} must use the canonical unresolved parameter type",
                    failure_code="parameter_spec_type",
                    field_name=name,
                    expected=UnresolvedParameterSpec,
                    actual=type(value),
                    schema_version=cls._SCHEMA_VERSION,
                )
            specs[name] = value
        rounds = _require_int64_scalar(
            values["owner_expansion_rounds"],
            field_name="owner_expansion_rounds",
            schema_version=cls._SCHEMA_VERSION,
            nonnegative=True,
        )
        if rounds != 1:
            raise MrtaSchemaError(
                "first-version owner expansion rounds must be exactly one",
                failure_code="owner_expansion_rounds",
                field_name="owner_expansion_rounds",
                expected=1,
                actual=rounds,
                schema_version=cls._SCHEMA_VERSION,
            )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
            metadata={
                "lifecycle_event_records": events,
                "assignment_opportunities": opportunities,
                **specs,
                "owner_expansion_rounds": rounds,
            },
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        invalid = (tensors["event_updated_ownership"] < -1) | (
            tensors["event_updated_ownership"] >= self._num_robots
        )
        index = _first_true_index(invalid)
        if index is not None:
            env, task = index
            raise MrtaSchemaError(
                "event_updated_ownership is outside -1..M-1",
                failure_code="ownership_range",
                field_name="event_updated_ownership",
                expected=(-1, self._num_robots - 1),
                actual=int(
                    tensors["event_updated_ownership"][env, task].item()
                ),
                env_id=int(tensors["env_id"][env].item()),
                task_id=task,
                schema_version=self._SCHEMA_VERSION,
            )
        seed = tensors["seed_robot_mask"]
        needs_assignment = tensors["needs_assignment_mask"]
        index = _first_true_index(needs_assignment & ~seed)
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "NEEDS_ASSIGNMENT robot must be a local-set seed",
                failure_code="needs_assignment_seed",
                field_name="seed_robot_mask",
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                expected=True,
                actual=False,
                schema_version=self._SCHEMA_VERSION,
            )
        for env in range(self._num_envs):
            trigger_records = (
                self.lifecycle_event_records[env]
                + self.assignment_opportunities[env]
            )
            for record in trigger_records:
                robot = int(record.robot_id)
                if robot < 0:
                    continue
                if robot >= self._num_robots:
                    raise MrtaSchemaError(
                        "trigger robot ID is outside the request robot domain",
                        failure_code="trigger_robot_range",
                        field_name="robot_id",
                        env_id=int(tensors["env_id"][env].item()),
                        robot_id=robot,
                        expected=(0, self._num_robots - 1),
                        actual=robot,
                        schema_version=self._SCHEMA_VERSION,
                    )
                if not bool(seed[env, robot].item()):
                    raise MrtaSchemaError(
                        "trigger robot must be a local-set seed",
                        failure_code="trigger_robot_seed",
                        field_name="seed_robot_mask",
                        env_id=int(tensors["env_id"][env].item()),
                        robot_id=robot,
                        expected=True,
                        actual=False,
                        schema_version=self._SCHEMA_VERSION,
                    )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_LOCAL_SET_REQUEST_FIELD_ORDER,
            scalar_values={
                "schema_version": self.schema_version,
                "lifecycle_event_records": self.lifecycle_event_records,
                "assignment_opportunities": self.assignment_opportunities,
                "top_k_spec": self.top_k_spec,
                "robot_cap_spec": self.robot_cap_spec,
                "task_cap_spec": self.task_cap_spec,
                "owner_expansion_rounds": self.owner_expansion_rounds,
            },
        )


for _name, _, _ in _LOCAL_SET_REQUEST_TENSOR_SPECS:
    setattr(LocalSetRequest, _name, _tensor_property(_name))


_LOCAL_SET_RESULT_TENSOR_SPECS = (
    ("local_robot_mask", ("E", "M"), torch.bool),
    ("local_task_mask", ("E", "N"), torch.bool),
    ("owner_added_robot_mask", ("E", "M"), torch.bool),
    ("overlap_merged", ("E",), torch.bool),
    ("overflowed", ("E",), torch.bool),
    ("overflow_disposition", ("E",), torch.int64),
    ("owner_expansion_rounds_used", ("E",), torch.int64),
    *_BATCH_GENERATION_SPECS,
)
_LOCAL_SET_RESULT_FIELD_ORDER = (
    "schema_version",
    "local_robot_mask",
    "local_task_mask",
    "owner_added_robot_mask",
    "overlap_merged",
    "overflowed",
    "overflow_disposition",
    "owner_expansion_rounds_used",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class LocalSetResult(_TensorDtoMixin):
    """Caller-produced local-set masks with fail-closed overflow encoding."""

    schema_version: str
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = LOCAL_SET_RESULT_SCHEMA_VERSION
    _TENSOR_SPECS = _LOCAL_SET_RESULT_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "LocalSetResult must be created by from_mapping()",
            failure_code="factory_required",
            expected="LocalSetResult.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
    ) -> "LocalSetResult":
        values = _require_mapping_keys(
            values,
            field_order=_LOCAL_SET_RESULT_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        robot_shape = _infer_ranked_tensor(
            values["local_robot_mask"],
            field_name="local_robot_mask",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        task_shape = _infer_ranked_tensor(
            values["local_task_mask"],
            field_name="local_task_mask",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_robots = robot_shape
        task_envs, num_tasks = task_shape
        if (
            min(num_envs, num_robots, num_tasks) <= 0
            or task_envs != num_envs
        ):
            raise MrtaSchemaError(
                "local-set result requires consistent positive E, M, N",
                failure_code="dimensions",
                expected="E>0,M>0,N>0 and matching E",
                actual=(robot_shape, task_shape),
                schema_version=cls._SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        index = _first_true_index(
            tensors["owner_added_robot_mask"] & ~tensors["local_robot_mask"]
        )
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "owner-added robot must be a local robot",
                failure_code="owner_added_subset",
                field_name="owner_added_robot_mask",
                expected="owner_added_robot_mask <= local_robot_mask",
                actual=(env, robot),
                schema_version=self._SCHEMA_VERSION,
            )
        rounds = tensors["owner_expansion_rounds_used"]
        index = _first_true_index((rounds < 0) | (rounds > 1))
        if index is not None:
            env = index[0]
            raise MrtaSchemaError(
                "owner_expansion_rounds_used must be 0 or 1",
                failure_code="owner_expansion_rounds",
                field_name="owner_expansion_rounds_used",
                expected=(0, 1),
                actual=int(rounds[env].item()),
                env_id=int(tensors["env_id"][env].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        expected_disposition = torch.where(
            tensors["overflowed"],
            torch.full_like(
                tensors["overflow_disposition"],
                int(LocalSetOverflowDisposition.FAIL_CLOSED_NO_ASSIGNMENT),
            ),
            torch.full_like(
                tensors["overflow_disposition"],
                int(LocalSetOverflowDisposition.NONE),
            ),
        )
        if not torch.equal(
            tensors["overflow_disposition"],
            expected_disposition,
        ):
            raise MrtaSchemaError(
                "overflow disposition must exactly encode fail-closed handling",
                failure_code="overflow_disposition",
                field_name="overflow_disposition",
                expected=(
                    "NONE when not overflowed; "
                    "FAIL_CLOSED_NO_ASSIGNMENT when overflowed"
                ),
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_LOCAL_SET_RESULT_FIELD_ORDER,
            scalar_values={"schema_version": self.schema_version},
        )


for _name, _, _ in _LOCAL_SET_RESULT_TENSOR_SPECS:
    setattr(LocalSetResult, _name, _tensor_property(_name))


_TOP_K_TENSOR_SPECS = (
    ("global_task_ids", ("E", "M", "K"), torch.int64),
    ("candidate_valid", ("E", "M", "K"), torch.bool),
    ("candidate_nominal_cost", ("E", "M", "K"), torch.float32),
    ("current_task_id", ("E", "M"), torch.int64),
    ("current_task_retained", ("E", "M"), torch.bool),
    *_BATCH_GENERATION_SPECS,
)
_TOP_K_FIELD_ORDER = (
    "schema_version",
    "global_task_ids",
    "candidate_valid",
    "candidate_nominal_cost",
    "current_task_id",
    "current_task_retained",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TopKCandidateResult(_TensorDtoMixin):
    """Caller-selected global-ID candidates; this DTO performs no selection."""

    schema_version: str
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _top_k: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION
    _TENSOR_SPECS = _TOP_K_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "TopKCandidateResult must be created by from_mapping()",
            failure_code="factory_required",
            expected="TopKCandidateResult.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        num_tasks: int,
        device: torch.device,
    ) -> "TopKCandidateResult":
        values = _require_mapping_keys(
            values,
            field_order=_TOP_K_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        num_tasks = _require_int64_scalar(
            num_tasks,
            field_name="num_tasks",
            schema_version=cls._SCHEMA_VERSION,
            nonnegative=True,
        )
        shape = _infer_ranked_tensor(
            values["global_task_ids"],
            field_name="global_task_ids",
            rank=3,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_robots, top_k = shape
        if min(num_envs, num_robots, num_tasks, top_k) <= 0:
            raise MrtaSchemaError(
                "Top-K result requires E > 0, M > 0, N > 0, K > 0",
                failure_code="dimensions",
                expected="E>0,M>0,N>0,K>0",
                actual=(num_envs, num_robots, num_tasks, top_k),
                schema_version=cls._SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            top_k=top_k,
            schema_version=cls._SCHEMA_VERSION,
        )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
        )
        object.__setattr__(instance, "_top_k", top_k)
        instance._validate_semantics()
        return instance

    @property
    def top_k(self) -> int:
        self.validate_integrity()
        return self._top_k

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        ids = tensors["global_task_ids"]
        valid = tensors["candidate_valid"]
        costs = tensors["candidate_nominal_cost"]
        index = _first_true_index((~valid) & (ids != -1))
        if index is not None:
            raise MrtaSchemaError(
                "invalid Top-K slot must use task ID -1",
                failure_code="candidate_invalid_id",
                field_name="global_task_ids",
                expected=-1,
                actual=int(ids[index].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(valid & ((ids < 0) | (ids >= self._num_tasks)))
        if index is not None:
            raise MrtaSchemaError(
                "valid Top-K slot task ID is outside global 0..N-1",
                failure_code="candidate_id_range",
                field_name="global_task_ids",
                expected=(0, self._num_tasks - 1),
                actual=int(ids[index].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(
            valid & (~torch.isfinite(costs) | (costs < 0))
        )
        if index is not None:
            raise MrtaSchemaError(
                "valid Top-K candidate cost must be finite and non-negative",
                failure_code="candidate_cost",
                field_name="candidate_nominal_cost",
                expected="finite and >= 0",
                actual=float(costs[index].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index((~valid) & ~torch.isnan(costs))
        if index is not None:
            raise MrtaSchemaError(
                "invalid Top-K candidate cost must be canonical NaN",
                failure_code="candidate_invalid_cost",
                field_name="candidate_nominal_cost",
                expected="NaN",
                actual=float(costs[index].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        for env in range(self._num_envs):
            for robot in range(self._num_robots):
                row_ids = ids[env, robot][valid[env, robot]]
                if int(torch.unique(row_ids).numel()) != int(row_ids.numel()):
                    raise MrtaSchemaError(
                        "valid global task IDs must be unique in each Top-K row",
                        failure_code="candidate_duplicate",
                        field_name="global_task_ids",
                        env_id=int(tensors["env_id"][env].item()),
                        robot_id=robot,
                        expected="unique valid IDs",
                        actual=tuple(int(item.item()) for item in row_ids),
                        schema_version=self._SCHEMA_VERSION,
                    )
        current = tensors["current_task_id"]
        index = _first_true_index(
            (current < -1) | (current >= self._num_tasks)
        )
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "current_task_id is outside -1..N-1",
                failure_code="current_task_range",
                field_name="current_task_id",
                expected=(-1, self._num_tasks - 1),
                actual=int(current[env, robot].item()),
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                schema_version=self._SCHEMA_VERSION,
            )
        retained = tensors["current_task_retained"]
        for env in range(self._num_envs):
            for robot in range(self._num_robots):
                current_id = int(current[env, robot].item())
                if current_id >= 0 and not bool(
                    retained[env, robot].item()
                ):
                    raise MrtaSchemaError(
                        "current task must be explicitly retained",
                        failure_code="current_task_retention",
                        field_name="current_task_retained",
                        env_id=int(tensors["env_id"][env].item()),
                        robot_id=robot,
                        expected=True,
                        actual=False,
                        schema_version=self._SCHEMA_VERSION,
                    )
                if bool(retained[env, robot].item()):
                    present = bool(
                        (
                            valid[env, robot]
                            & (ids[env, robot] == current_id)
                        ).any().item()
                    )
                    if current_id < 0 or not present:
                        raise MrtaSchemaError(
                            "retained current task must appear in valid candidates",
                            failure_code="current_task_retention",
                            field_name="current_task_retained",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected="current global ID in valid candidate row",
                            actual=current_id,
                            schema_version=self._SCHEMA_VERSION,
                        )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_TOP_K_FIELD_ORDER,
            scalar_values={"schema_version": self.schema_version},
        )


for _name, _, _ in _TOP_K_TENSOR_SPECS:
    setattr(TopKCandidateResult, _name, _tensor_property(_name))


_DVM_TENSOR_SPECS = (
    ("global_task_valid_mask", ("E", "N"), torch.bool),
    ("failed_pair_legal_mask", ("E", "M", "N"), torch.bool),
    ("nominal_path_valid_mask", ("E", "M", "N"), torch.bool),
    ("local_topk_or_continue_mask", ("E", "M", "N"), torch.bool),
    ("ownership_preemption_legal_mask", ("E", "M", "N"), torch.bool),
    ("robot_available_mask", ("E", "M"), torch.bool),
    ("decision_opportunity_present", ("E", "M", "ONE"), torch.bool),
    ("target_action_mask", ("E", "M", "N"), torch.bool),
    ("noop_action_mask", ("E", "M", "ONE"), torch.bool),
    ("available_actions", ("E", "M", "A"), torch.bool),
    ("semantic_legal_action_count", ("E", "M", "ONE"), torch.int64),
    ("decision_valid_mask", ("E", "M", "ONE"), torch.bool),
    ("forced_policy_action_id", ("E", "M", "ONE"), torch.int64),
    *_BATCH_GENERATION_SPECS,
)
_DVM_FIELD_ORDER = (
    "schema_version",
    "global_task_valid_mask",
    "failed_pair_legal_mask",
    "nominal_path_valid_mask",
    "local_topk_or_continue_mask",
    "ownership_preemption_legal_mask",
    "robot_available_mask",
    "decision_opportunity_present",
    "target_action_mask",
    "noop_action_mask",
    "available_actions",
    "semantic_legal_action_count",
    "decision_valid_mask",
    "forced_policy_action_id",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)
_DVM_CONSTRUCTION_CONTEXT_SPECS = (
    ("current_task_id", ("E", "M"), torch.int64),
    ("executing_mask", ("E", "M"), torch.bool),
    ("idle_or_needs_assignment_mask", ("E", "M"), torch.bool),
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class DecisionValidMaskSnapshot(_TensorDtoMixin):
    """Auditable action-mask provenance and decision-valid snapshot."""

    schema_version: str
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION
    _TENSOR_SPECS = _DVM_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "DecisionValidMaskSnapshot must be created by from_mapping()",
            failure_code="factory_required",
            expected="DecisionValidMaskSnapshot.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
        current_task_id: torch.Tensor,
        executing_mask: torch.Tensor,
        idle_or_needs_assignment_mask: torch.Tensor,
    ) -> "DecisionValidMaskSnapshot":
        values = _require_mapping_keys(
            values,
            field_order=_DVM_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        task_shape = _infer_ranked_tensor(
            values["global_task_valid_mask"],
            field_name="global_task_valid_mask",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        robot_shape = _infer_ranked_tensor(
            values["robot_available_mask"],
            field_name="robot_available_mask",
            rank=2,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_tasks = task_shape
        robot_envs, num_robots = robot_shape
        if (
            min(num_envs, num_robots, num_tasks) <= 0
            or robot_envs != num_envs
        ):
            raise MrtaSchemaError(
                "DVM snapshot requires consistent positive E, M, N",
                failure_code="dimensions",
                expected="E>0,M>0,N>0 and matching E",
                actual=(task_shape, robot_shape),
                schema_version=cls._SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        construction_context_snapshots = _capture_tensor_specs(
            {
                "current_task_id": current_task_id,
                "executing_mask": executing_mask,
                "idle_or_needs_assignment_mask": (
                    idle_or_needs_assignment_mask
                ),
            },
            specs=_DVM_CONSTRUCTION_CONTEXT_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        construction_context = {
            name: snapshot.internal(
                field_name=name,
                schema_version=cls._SCHEMA_VERSION,
            )
            for name, snapshot in construction_context_snapshots.items()
        }
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
        )
        instance._validate_semantics(
            construction_context=construction_context,
        )
        return instance

    def _validate_semantics(
        self,
        *,
        construction_context: Mapping[str, torch.Tensor],
    ) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        expected_target = (
            tensors["global_task_valid_mask"].unsqueeze(1)
            & tensors["failed_pair_legal_mask"]
            & tensors["nominal_path_valid_mask"]
            & tensors["local_topk_or_continue_mask"]
            & tensors["ownership_preemption_legal_mask"]
            & tensors["robot_available_mask"].unsqueeze(-1)
        )
        if not torch.equal(tensors["target_action_mask"], expected_target):
            raise MrtaSchemaError(
                "target_action_mask differs from provenance conjunction",
                failure_code="target_mask_conjunction",
                field_name="target_action_mask",
                expected=(
                    "global & failed-pair & path & local/continue & "
                    "ownership/preemption & robot-available"
                ),
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        expected_available = torch.cat(
            [tensors["target_action_mask"], tensors["noop_action_mask"]],
            dim=-1,
        )
        if not torch.equal(tensors["available_actions"], expected_available):
            raise MrtaSchemaError(
                "available_actions must concatenate target and noop masks",
                failure_code="available_actions_concat",
                field_name="available_actions",
                expected="concat(target_action_mask, noop_action_mask)",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        expected_count = expected_available.sum(
            dim=-1,
            keepdim=True,
            dtype=torch.int64,
        )
        if not torch.equal(
            tensors["semantic_legal_action_count"],
            expected_count,
        ):
            raise MrtaSchemaError(
                "semantic legal action count differs from available actions",
                failure_code="semantic_action_count",
                field_name="semantic_legal_action_count",
                expected="available_actions.sum(-1, keepdim=True)",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        opportunity = tensors["decision_opportunity_present"]
        robot_available = tensors["robot_available_mask"].unsqueeze(-1)
        expected_dvm = opportunity & robot_available & (expected_count >= 2)
        if not torch.equal(tensors["decision_valid_mask"], expected_dvm):
            raise MrtaSchemaError(
                "decision_valid_mask differs from frozen opportunity semantics",
                failure_code="decision_valid_relation",
                field_name="decision_valid_mask",
                expected="opportunity & robot_available & semantic_count>=2",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        no_opportunity = ~opportunity
        if bool((expected_available & no_opportunity.expand_as(expected_available)).any()):
            raise MrtaSchemaError(
                "no-opportunity row must have an all-false semantic mask",
                failure_code="no_opportunity_mask",
                field_name="available_actions",
                expected="all false",
                actual="true action in no-opportunity row",
                schema_version=self._SCHEMA_VERSION,
            )
        unavailable_targets = (
            ~robot_available.expand_as(tensors["target_action_mask"])
            & tensors["target_action_mask"]
        )
        if bool(unavailable_targets.any()):
            raise MrtaSchemaError(
                "unavailable robot cannot have a target action",
                failure_code="unavailable_target",
                field_name="target_action_mask",
                expected="all false for unavailable robot",
                actual="true target",
                schema_version=self._SCHEMA_VERSION,
            )
        current_task_id = construction_context["current_task_id"]
        executing = construction_context["executing_mask"]
        idle_or_needs = construction_context[
            "idle_or_needs_assignment_mask"
        ]
        overlap = executing & idle_or_needs
        index = _first_true_index(overlap)
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "executing and idle/needs-assignment contexts are disjoint",
                failure_code="construction_context_overlap",
                field_name="executing_mask",
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                expected=False,
                actual=True,
                schema_version=self._SCHEMA_VERSION,
            )
        context_required = (
            opportunity.squeeze(-1) & tensors["robot_available_mask"]
        )
        classified = executing | idle_or_needs
        index = _first_true_index(context_required & ~classified)
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "available opportunity row requires one construction context",
                failure_code="construction_context_unclassified",
                field_name="executing_mask",
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                expected="exactly one of executing or idle/needs-assignment",
                actual=False,
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(
            (current_task_id < -1) | (current_task_id >= self._num_tasks)
        )
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "construction current_task_id is outside -1..N-1",
                failure_code="current_task_range",
                field_name="current_task_id",
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                expected=(-1, self._num_tasks - 1),
                actual=int(current_task_id[env, robot].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(
            idle_or_needs & (current_task_id != -1)
        )
        if index is not None:
            env, robot = index
            raise MrtaSchemaError(
                "idle/needs-assignment context has no current task",
                failure_code="idle_current_task",
                field_name="current_task_id",
                env_id=int(tensors["env_id"][env].item()),
                robot_id=robot,
                expected=-1,
                actual=int(current_task_id[env, robot].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        executing_opportunity = context_required & executing
        idle_opportunity = context_required & idle_or_needs
        for env in range(self._num_envs):
            for robot in range(self._num_robots):
                current = int(current_task_id[env, robot].item())
                if bool(executing_opportunity[env, robot].item()):
                    if current < 0:
                        raise MrtaSchemaError(
                            "executing opportunity requires a current task",
                            failure_code="executing_current_task",
                            field_name="current_task_id",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected="global task ID in 0..N-1",
                            actual=current,
                            schema_version=self._SCHEMA_VERSION,
                        )
                    if not bool(
                        tensors["global_task_valid_mask"][env, current].item()
                    ):
                        raise MrtaSchemaError(
                            "executing current task must be globally valid",
                            failure_code="executing_current_global_valid",
                            field_name="global_task_valid_mask",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            task_id=current,
                            expected=True,
                            actual=False,
                            schema_version=self._SCHEMA_VERSION,
                        )
                    if (
                        not bool(
                            tensors["local_topk_or_continue_mask"][
                                env, robot, current
                            ].item()
                        )
                        or not bool(
                            tensors["target_action_mask"][
                                env, robot, current
                            ].item()
                        )
                    ):
                        raise MrtaSchemaError(
                            "executing opportunity must retain its current task",
                            failure_code="executing_continue_retention",
                            field_name="local_topk_or_continue_mask",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            task_id=current,
                            expected=(
                                "local_topk_or_continue=true and "
                                "target_action_mask=true"
                            ),
                            actual=False,
                            schema_version=self._SCHEMA_VERSION,
                        )
                    if bool(
                        tensors["noop_action_mask"][env, robot, 0].item()
                    ):
                        raise MrtaSchemaError(
                            "executing opportunity cannot expose noop",
                            failure_code="executing_noop_forbidden",
                            field_name="noop_action_mask",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=False,
                            actual=True,
                            schema_version=self._SCHEMA_VERSION,
                        )
                elif bool(idle_opportunity[env, robot].item()):
                    if not bool(
                        tensors["noop_action_mask"][env, robot, 0].item()
                    ):
                        raise MrtaSchemaError(
                            "idle/needs-assignment opportunity requires noop",
                            failure_code="idle_noop_required",
                            field_name="noop_action_mask",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=True,
                            actual=False,
                            schema_version=self._SCHEMA_VERSION,
                        )
        forced = tensors["forced_policy_action_id"]
        action_count = self._num_tasks + 1
        for env in range(self._num_envs):
            for robot in range(self._num_robots):
                has_opportunity = bool(opportunity[env, robot, 0].item())
                decision_valid = bool(
                    tensors["decision_valid_mask"][env, robot, 0].item()
                )
                count = int(expected_count[env, robot, 0].item())
                forced_id = int(forced[env, robot, 0].item())
                if not has_opportunity:
                    if count != 0 or forced_id != -1:
                        raise MrtaSchemaError(
                            "no-opportunity row requires count 0 and forced ID -1",
                            failure_code="no_opportunity_no_row",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=(0, -1),
                            actual=(count, forced_id),
                            schema_version=self._SCHEMA_VERSION,
                        )
                elif decision_valid:
                    if forced_id != -1:
                        raise MrtaSchemaError(
                            "decision-valid row has no forced policy action",
                            failure_code="decision_forced_id",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=-1,
                            actual=forced_id,
                            schema_version=self._SCHEMA_VERSION,
                        )
                else:
                    if count < 1:
                        raise MrtaSchemaError(
                            "nonterminal forced row requires a legal forced action",
                            failure_code="forced_action_missing",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected="semantic count >= 1",
                            actual=count,
                            schema_version=self._SCHEMA_VERSION,
                        )
                    if (
                        forced_id < 0
                        or forced_id >= action_count
                        or not bool(
                            expected_available[env, robot, forced_id].item()
                        )
                    ):
                        raise MrtaSchemaError(
                            "forced action ID must be legal in its own snapshot",
                            failure_code="forced_action_legality",
                            field_name="forced_policy_action_id",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected="legal ID in 0..N",
                            actual=forced_id,
                            schema_version=self._SCHEMA_VERSION,
                        )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_DVM_FIELD_ORDER,
            scalar_values={"schema_version": self.schema_version},
        )


for _name, _, _ in _DVM_TENSOR_SPECS:
    setattr(DecisionValidMaskSnapshot, _name, _tensor_property(_name))


_PROPOSAL_TENSOR_SPECS = (
    ("storage_row_present_mask", ("E", "M", "ONE"), torch.bool),
    ("policy_proposal_present_mask", ("E", "M", "ONE"), torch.bool),
    ("forced_nondecision_mask", ("E", "M", "ONE"), torch.bool),
    ("decision_valid_mask", ("E", "M", "ONE"), torch.bool),
    ("nonterminal_mask", ("E", "M", "ONE"), torch.bool),
    ("stored_action_id", ("E", "M", "ONE"), torch.int64),
    ("stored_action_log_prob", ("E", "M", "ONE"), torch.float32),
    ("proposed_task_id", ("E", "M", "ONE"), torch.int64),
    ("historical_available_actions", ("E", "M", "A"), torch.bool),
    *_BATCH_GENERATION_SPECS,
)
_PROPOSAL_FIELD_ORDER = (
    "schema_version",
    "storage_row_present_mask",
    "policy_proposal_present_mask",
    "forced_nondecision_mask",
    "decision_valid_mask",
    "nonterminal_mask",
    "stored_action_id",
    "stored_action_log_prob",
    "stored_action_row_kind",
    "proposal_kind",
    "proposed_task_id",
    "historical_available_actions",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


def _validate_nested_enum_rows(
    value: object,
    *,
    enum_type: type[Enum],
    allow_none: bool,
    num_envs: int,
    num_robots: int,
    field_name: str,
    schema_version: str,
) -> tuple[tuple[Enum | None, ...], ...]:
    if type(value) is not tuple or len(value) != num_envs:
        raise MrtaSchemaError(
            f"{field_name} must be an exact E-length tuple",
            failure_code="typed_row_shape",
            field_name=field_name,
            expected=(num_envs, num_robots),
            actual=type(value) if type(value) is not tuple else len(value),
            schema_version=schema_version,
        )
    checked: list[tuple[Enum | None, ...]] = []
    for env, row in enumerate(value):
        if type(row) is not tuple or len(row) != num_robots:
            raise MrtaSchemaError(
                f"{field_name} row must be an exact M-length tuple",
                failure_code="typed_row_shape",
                field_name=field_name,
                expected=num_robots,
                actual=type(row) if type(row) is not tuple else len(row),
                env_id=env,
                schema_version=schema_version,
            )
        for robot, item in enumerate(row):
            if item is None and allow_none:
                continue
            if type(item) is not enum_type:
                raise MrtaSchemaError(
                    f"{field_name} contains a noncanonical enum value",
                    failure_code="typed_row_value",
                    field_name=field_name,
                    expected=enum_type,
                    actual=type(item),
                    env_id=env,
                    robot_id=robot,
                    schema_version=schema_version,
                )
        checked.append(row)
    return tuple(checked)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class ProposalSnapshot(_TensorDtoMixin):
    """Four-mask fixed-rollout storage snapshot; never stores effective assignment."""

    schema_version: str
    stored_action_row_kind: tuple[tuple[StoredActionRowKind, ...], ...]
    proposal_kind: tuple[tuple[ProposalKind | None, ...], ...]
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = PROPOSAL_SNAPSHOT_SCHEMA_VERSION
    _TENSOR_SPECS = _PROPOSAL_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "ProposalSnapshot must be created by from_mapping()",
            failure_code="factory_required",
            expected="ProposalSnapshot.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
    ) -> "ProposalSnapshot":
        values = _require_mapping_keys(
            values,
            field_order=_PROPOSAL_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        action_shape = _infer_ranked_tensor(
            values["historical_available_actions"],
            field_name="historical_available_actions",
            rank=3,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_envs, num_robots, action_dim = action_shape
        num_tasks = action_dim - 1
        if min(num_envs, num_robots, num_tasks) <= 0:
            raise MrtaSchemaError(
                "proposal snapshot requires E > 0, M > 0, N > 0",
                failure_code="dimensions",
                expected="E>0,M>0,N>0,A=N+1",
                actual=action_shape,
                schema_version=cls._SCHEMA_VERSION,
            )
        row_kind = _validate_nested_enum_rows(
            values["stored_action_row_kind"],
            enum_type=StoredActionRowKind,
            allow_none=False,
            num_envs=num_envs,
            num_robots=num_robots,
            field_name="stored_action_row_kind",
            schema_version=cls._SCHEMA_VERSION,
        )
        proposal_kind = _validate_nested_enum_rows(
            values["proposal_kind"],
            enum_type=ProposalKind,
            allow_none=True,
            num_envs=num_envs,
            num_robots=num_robots,
            field_name="proposal_kind",
            schema_version=cls._SCHEMA_VERSION,
        )
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
            metadata={
                "stored_action_row_kind": row_kind,
                "proposal_kind": proposal_kind,
            },
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=self._num_envs,
            schema_version=self._SCHEMA_VERSION,
        )
        storage = tensors["storage_row_present_mask"]
        policy = tensors["policy_proposal_present_mask"]
        forced = tensors["forced_nondecision_mask"]
        dvm = tensors["decision_valid_mask"]
        nonterminal = tensors["nonterminal_mask"]
        if not torch.equal(policy, dvm):
            raise MrtaSchemaError(
                "policy proposal presence must exactly equal DVM",
                failure_code="four_mask_policy_dvm",
                expected="policy_proposal_present_mask == decision_valid_mask",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        if not torch.equal(storage, nonterminal):
            raise MrtaSchemaError(
                "storage presence must exactly equal historical nonterminal mask",
                failure_code="four_mask_storage_nonterminal",
                expected="storage_row_present_mask == nonterminal_mask",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        expected_forced = storage & nonterminal & ~dvm
        if not torch.equal(forced, expected_forced):
            raise MrtaSchemaError(
                "forced nondecision mask differs from frozen relation",
                failure_code="four_mask_forced",
                expected="storage & nonterminal & ~DVM",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        if not torch.equal(storage, policy | forced) or bool(
            (policy & forced).any()
        ):
            raise MrtaSchemaError(
                "policy and forced rows must be disjoint and cover storage",
                failure_code="four_mask_partition",
                expected="storage == policy | forced; policy & forced == false",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        ids = tensors["stored_action_id"]
        log_prob = tensors["stored_action_log_prob"]
        proposed = tensors["proposed_task_id"]
        historical = tensors["historical_available_actions"]
        for env in range(self._num_envs):
            for robot in range(self._num_robots):
                is_storage = bool(storage[env, robot, 0].item())
                is_policy = bool(policy[env, robot, 0].item())
                is_forced = bool(forced[env, robot, 0].item())
                action_id = int(ids[env, robot, 0].item())
                task_id = int(proposed[env, robot, 0].item())
                action_log_prob = float(log_prob[env, robot, 0].item())
                row_kind = self.stored_action_row_kind[env][robot]
                proposal_kind = self.proposal_kind[env][robot]
                if not is_storage:
                    if (
                        is_policy
                        or is_forced
                        or action_id != -1
                        or task_id != -1
                        or action_log_prob != 0.0
                        or row_kind is not StoredActionRowKind.NO_ROW
                        or proposal_kind is not None
                        or bool(historical[env, robot].any().item())
                    ):
                        raise MrtaSchemaError(
                            "terminal no-row encoding is not canonical",
                            failure_code="proposal_terminal_no_row",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=(
                                "no row, IDs -1, log-prob 0, all-false mask"
                            ),
                            actual=(
                                action_id,
                                task_id,
                                action_log_prob,
                                row_kind,
                                proposal_kind,
                            ),
                            schema_version=self._SCHEMA_VERSION,
                        )
                    continue
                if (
                    action_id < 0
                    or action_id > self._num_tasks
                    or not bool(historical[env, robot, action_id].item())
                ):
                    raise MrtaSchemaError(
                        "stored action must be legal in its historical mask",
                        failure_code="historical_action_legality",
                        field_name="stored_action_id",
                        env_id=int(tensors["env_id"][env].item()),
                        robot_id=robot,
                        expected="legal ID in 0..N",
                        actual=action_id,
                        schema_version=self._SCHEMA_VERSION,
                    )
                if is_forced:
                    if (
                        row_kind is not StoredActionRowKind.FORCED_NONDECISION
                        or proposal_kind is not None
                        or task_id != -1
                        or action_log_prob != 0.0
                    ):
                        raise MrtaSchemaError(
                            "forced storage row must not claim policy evidence",
                            failure_code="forced_not_proposal",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=(
                                StoredActionRowKind.FORCED_NONDECISION,
                                None,
                                -1,
                                0.0,
                            ),
                            actual=(
                                row_kind,
                                proposal_kind,
                                task_id,
                                action_log_prob,
                            ),
                            schema_version=self._SCHEMA_VERSION,
                        )
                elif is_policy:
                    if (
                        row_kind is not StoredActionRowKind.POLICY_PROPOSAL
                        or type(proposal_kind) is not ProposalKind
                        or not math.isfinite(action_log_prob)
                    ):
                        raise MrtaSchemaError(
                            "policy row requires canonical kind and finite log-prob",
                            failure_code="policy_proposal_row",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=(
                                StoredActionRowKind.POLICY_PROPOSAL,
                                ProposalKind,
                                "finite log-prob",
                            ),
                            actual=(
                                row_kind,
                                type(proposal_kind),
                                action_log_prob,
                            ),
                            schema_version=self._SCHEMA_VERSION,
                        )
                    if proposal_kind is ProposalKind.NOOP_IDLE:
                        valid_meaning = (
                            action_id == self._num_tasks and task_id == -1
                        )
                    else:
                        valid_meaning = (
                            action_id < self._num_tasks
                            and task_id == action_id
                        )
                    if not valid_meaning:
                        raise MrtaSchemaError(
                            "proposal kind/action/global-task decoding is inconsistent",
                            failure_code="proposal_action_semantics",
                            env_id=int(tensors["env_id"][env].item()),
                            robot_id=robot,
                            expected=(
                                "task kinds: task_id == action_id < N; "
                                "NOOP_IDLE: action_id == N, task_id == -1"
                            ),
                            actual=(proposal_kind, action_id, task_id),
                            schema_version=self._SCHEMA_VERSION,
                        )

    def resolver_policy_mask(self) -> torch.Tensor:
        """Return only policy rows; forced storage is deliberately excluded."""

        return self._clone_tensor("policy_proposal_present_mask")

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_PROPOSAL_FIELD_ORDER,
            scalar_values={
                "schema_version": self.schema_version,
                "stored_action_row_kind": self.stored_action_row_kind,
                "proposal_kind": self.proposal_kind,
            },
        )


for _name, _, _ in _PROPOSAL_TENSOR_SPECS:
    setattr(ProposalSnapshot, _name, _tensor_property(_name))


_COMPONENT_REQUEST_TENSOR_SPECS = (
    ("member_robot_mask", ("M",), torch.bool),
    ("member_task_mask", ("N",), torch.bool),
    ("baseline_assignment_a0", ("M",), torch.int64),
    ("baseline_ownership_a0", ("N",), torch.int64),
    ("proposed_task_id", ("M",), torch.int64),
    ("policy_proposal_present_mask", ("M",), torch.bool),
    ("task_state", ("N",), torch.int64),
    ("robot_state", ("M",), torch.int64),
    ("pair_legal_mask", ("M", "N"), torch.bool),
    ("nominal_cost", ("M", "N"), torch.float32),
    *_BATCH_GENERATION_SPECS,
)
_COMPONENT_REQUEST_FIELD_ORDER = (
    "schema_version",
    "component_id",
    "member_robot_mask",
    "member_task_mask",
    "baseline_assignment_a0",
    "baseline_ownership_a0",
    "proposed_task_id",
    "proposal_kind",
    "policy_proposal_present_mask",
    "task_state",
    "robot_state",
    "pair_legal_mask",
    "nominal_cost",
    "pair_abs_threshold_spec",
    "pair_rel_threshold_spec",
    "component_abs_threshold_spec",
    "component_rel_threshold_spec",
    "transfer_penalty_spec",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


def _validate_assignment_ownership_consistency(
    assignment: torch.Tensor,
    ownership: torch.Tensor,
    *,
    num_robots: int,
    num_tasks: int,
    field_prefix: str,
    schema_version: str,
) -> None:
    invalid_assignment = (assignment < -1) | (assignment >= num_tasks)
    index = _first_true_index(invalid_assignment)
    if index is not None:
        robot = index[0]
        raise MrtaSchemaError(
            f"{field_prefix} assignment is outside -1..N-1",
            failure_code="assignment_range",
            field_name=f"{field_prefix}_assignment",
            robot_id=robot,
            expected=(-1, num_tasks - 1),
            actual=int(assignment[robot].item()),
            schema_version=schema_version,
        )
    invalid_ownership = (ownership < -1) | (ownership >= num_robots)
    index = _first_true_index(invalid_ownership)
    if index is not None:
        task = index[0]
        raise MrtaSchemaError(
            f"{field_prefix} ownership is outside -1..M-1",
            failure_code="ownership_range",
            field_name=f"{field_prefix}_ownership",
            task_id=task,
            expected=(-1, num_robots - 1),
            actual=int(ownership[task].item()),
            schema_version=schema_version,
        )
    seen_tasks: set[int] = set()
    for robot in range(num_robots):
        task = int(assignment[robot].item())
        if task < 0:
            continue
        if task in seen_tasks or int(ownership[task].item()) != robot:
            raise MrtaSchemaError(
                f"{field_prefix} assignment/ownership is not one-to-one",
                failure_code="assignment_ownership_consistency",
                robot_id=robot,
                task_id=task,
                expected="assignment and ownership mutual inverse",
                actual=int(ownership[task].item()),
                schema_version=schema_version,
            )
        seen_tasks.add(task)
    for task in range(num_tasks):
        robot = int(ownership[task].item())
        if robot >= 0 and int(assignment[robot].item()) != task:
            raise MrtaSchemaError(
                f"{field_prefix} ownership has no matching assignment",
                failure_code="assignment_ownership_consistency",
                robot_id=robot,
                task_id=task,
                expected=task,
                actual=int(assignment[robot].item()),
                schema_version=schema_version,
            )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TransferComponentRequest(_TensorDtoMixin):
    """Single-environment resolver input snapshot; no graph is constructed."""

    schema_version: str
    component_id: str
    proposal_kind: tuple[ProposalKind | None, ...]
    pair_abs_threshold_spec: UnresolvedParameterSpec
    pair_rel_threshold_spec: UnresolvedParameterSpec
    component_abs_threshold_spec: UnresolvedParameterSpec
    component_rel_threshold_spec: UnresolvedParameterSpec
    transfer_penalty_spec: UnresolvedParameterSpec
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION
    _TENSOR_SPECS = _COMPONENT_REQUEST_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "TransferComponentRequest must be created by from_mapping()",
            failure_code="factory_required",
            expected="TransferComponentRequest.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        device: torch.device,
    ) -> "TransferComponentRequest":
        values = _require_mapping_keys(
            values,
            field_order=_COMPONENT_REQUEST_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        robot_shape = _infer_ranked_tensor(
            values["member_robot_mask"],
            field_name="member_robot_mask",
            rank=1,
            schema_version=cls._SCHEMA_VERSION,
        )
        task_shape = _infer_ranked_tensor(
            values["member_task_mask"],
            field_name="member_task_mask",
            rank=1,
            schema_version=cls._SCHEMA_VERSION,
        )
        num_robots = robot_shape[0]
        num_tasks = task_shape[0]
        if min(num_robots, num_tasks) <= 0:
            raise MrtaSchemaError(
                "component request requires M > 0 and N > 0",
                failure_code="dimensions",
                expected="M>0,N>0",
                actual=(num_robots, num_tasks),
                schema_version=cls._SCHEMA_VERSION,
            )
        proposal_kind_value = values["proposal_kind"]
        if (
            type(proposal_kind_value) is not tuple
            or len(proposal_kind_value) != num_robots
        ):
            raise MrtaSchemaError(
                "component proposal_kind must be an exact M-length tuple",
                failure_code="typed_row_shape",
                field_name="proposal_kind",
                expected=num_robots,
                actual=(
                    type(proposal_kind_value)
                    if type(proposal_kind_value) is not tuple
                    else len(proposal_kind_value)
                ),
                schema_version=cls._SCHEMA_VERSION,
            )
        for robot, item in enumerate(proposal_kind_value):
            if item is not None and type(item) is not ProposalKind:
                raise MrtaSchemaError(
                    "component proposal_kind contains a noncanonical value",
                    failure_code="typed_row_value",
                    field_name="proposal_kind",
                    expected="ProposalKind | None",
                    actual=type(item),
                    robot_id=robot,
                    schema_version=cls._SCHEMA_VERSION,
                )
        specs: dict[str, UnresolvedParameterSpec] = {}
        for name in (
            "pair_abs_threshold_spec",
            "pair_rel_threshold_spec",
            "component_abs_threshold_spec",
            "component_rel_threshold_spec",
            "transfer_penalty_spec",
        ):
            value = values[name]
            if type(value) is not UnresolvedParameterSpec:
                raise MrtaSchemaError(
                    "component threshold fields require unresolved specs in A3",
                    failure_code="parameter_spec_type",
                    field_name=name,
                    expected=UnresolvedParameterSpec,
                    actual=type(value),
                    schema_version=cls._SCHEMA_VERSION,
                )
            specs[name] = value
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=1,
            num_robots=num_robots,
            num_tasks=num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=1,
            num_robots=num_robots,
            num_tasks=num_tasks,
            tensor_snapshots=snapshots,
            metadata={
                "component_id": _require_canonical_string(
                    values["component_id"],
                    field_name="component_id",
                    schema_version=cls._SCHEMA_VERSION,
                ),
                "proposal_kind": proposal_kind_value,
                **specs,
            },
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=1,
            schema_version=self._SCHEMA_VERSION,
        )
        members_robot = tensors["member_robot_mask"]
        members_task = tensors["member_task_mask"]
        policy = tensors["policy_proposal_present_mask"]
        if (
            not bool(members_robot.any().item())
            or not bool(members_task.any().item())
            or not bool(policy.any().item())
        ):
            raise MrtaSchemaError(
                "component requires robot, task, and policy-proposal members",
                failure_code="component_empty",
                expected="at least one robot, task, and policy row",
                actual=(
                    int(members_robot.sum().item()),
                    int(members_task.sum().item()),
                    int(policy.sum().item()),
                ),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(policy & ~members_robot)
        if index is not None:
            robot = index[0]
            raise MrtaSchemaError(
                "policy proposal row must be a component robot member",
                failure_code="component_policy_membership",
                robot_id=robot,
                expected=True,
                actual=False,
                schema_version=self._SCHEMA_VERSION,
            )
        _validate_assignment_ownership_consistency(
            tensors["baseline_assignment_a0"],
            tensors["baseline_ownership_a0"],
            num_robots=self._num_robots,
            num_tasks=self._num_tasks,
            field_prefix="baseline",
            schema_version=self._SCHEMA_VERSION,
        )
        proposed = tensors["proposed_task_id"]
        index = _first_true_index(
            (proposed < -1) | (proposed >= self._num_tasks)
        )
        if index is not None:
            robot = index[0]
            raise MrtaSchemaError(
                "proposed_task_id is outside -1..N-1",
                failure_code="proposal_task_range",
                robot_id=robot,
                expected=(-1, self._num_tasks - 1),
                actual=int(proposed[robot].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        baseline_assignment = tensors["baseline_assignment_a0"]
        baseline_ownership = tensors["baseline_ownership_a0"]
        for robot in range(self._num_robots):
            if not bool(members_robot[robot].item()):
                continue
            baseline_task = int(baseline_assignment[robot].item())
            if (
                baseline_task >= 0
                and not bool(members_task[baseline_task].item())
            ):
                raise MrtaSchemaError(
                    "member robot's baseline task must be a member task",
                    failure_code="component_membership_closure",
                    robot_id=robot,
                    task_id=baseline_task,
                    expected=True,
                    actual=False,
                    schema_version=self._SCHEMA_VERSION,
                )
        for task in range(self._num_tasks):
            if not bool(members_task[task].item()):
                continue
            baseline_owner = int(baseline_ownership[task].item())
            if (
                baseline_owner >= 0
                and not bool(members_robot[baseline_owner].item())
            ):
                raise MrtaSchemaError(
                    "member task's baseline owner must be a member robot",
                    failure_code="component_membership_closure",
                    robot_id=baseline_owner,
                    task_id=task,
                    expected=True,
                    actual=False,
                    schema_version=self._SCHEMA_VERSION,
                )
        for robot in range(self._num_robots):
            is_policy = bool(policy[robot].item())
            kind = self.proposal_kind[robot]
            task = int(proposed[robot].item())
            if not is_policy:
                if kind is not None or task != -1:
                    raise MrtaSchemaError(
                        "nonpolicy/forced row cannot become component proposal",
                        failure_code="forced_not_component_proposal",
                        robot_id=robot,
                        expected=(None, -1),
                        actual=(kind, task),
                        schema_version=self._SCHEMA_VERSION,
                    )
                continue
            if type(kind) is not ProposalKind:
                raise MrtaSchemaError(
                    "policy component row requires a ProposalKind",
                    failure_code="component_proposal_kind",
                    robot_id=robot,
                    expected=ProposalKind,
                    actual=type(kind),
                    schema_version=self._SCHEMA_VERSION,
                )
            baseline_task = int(
                tensors["baseline_assignment_a0"][robot].item()
            )
            if baseline_task < 0:
                expected_kind = (
                    ProposalKind.NOOP_IDLE
                    if task < 0
                    else ProposalKind.CLAIM
                )
            elif task < 0:
                expected_kind = None
            elif task == baseline_task:
                expected_kind = ProposalKind.CONTINUE
            else:
                expected_kind = ProposalKind.SWITCH
            if expected_kind is None or kind is not expected_kind:
                raise MrtaSchemaError(
                    "proposal kind differs from baseline/proposed task meaning",
                    failure_code="component_proposal_semantics",
                    field_name="proposal_kind",
                    robot_id=robot,
                    expected=(
                        "assigned robot must CONTINUE or SWITCH"
                        if expected_kind is None
                        else expected_kind
                    ),
                    actual=kind,
                    schema_version=self._SCHEMA_VERSION,
                )
            if kind is ProposalKind.NOOP_IDLE:
                if task != -1:
                    raise MrtaSchemaError(
                        "NOOP_IDLE component proposal has no task ID",
                        failure_code="component_proposal_semantics",
                        robot_id=robot,
                        expected=-1,
                        actual=task,
                        schema_version=self._SCHEMA_VERSION,
                    )
            else:
                if (
                    task < 0
                    or not bool(members_task[task].item())
                    or not bool(tensors["pair_legal_mask"][robot, task].item())
                ):
                    raise MrtaSchemaError(
                        "task proposal must target a legal component task",
                        failure_code="component_proposal_legality",
                        robot_id=robot,
                        task_id=task,
                        expected="member task with pair_legal=true",
                        actual=task,
                        schema_version=self._SCHEMA_VERSION,
                    )
        for robot in range(self._num_robots):
            if not bool(members_robot[robot].item()):
                continue
            has_baseline_edge = int(baseline_assignment[robot].item()) >= 0
            has_policy_participation = bool(policy[robot].item())
            if not has_baseline_edge and not has_policy_participation:
                raise MrtaSchemaError(
                    "member robot must participate in baseline or policy proposal",
                    failure_code="component_dangling_robot",
                    robot_id=robot,
                    expected="baseline task or policy proposal row",
                    actual=False,
                    schema_version=self._SCHEMA_VERSION,
                )
        for task in range(self._num_tasks):
            if not bool(members_task[task].item()):
                continue
            has_baseline_edge = int(baseline_ownership[task].item()) >= 0
            has_policy_edge = bool(
                (policy & (proposed == task)).any().item()
            )
            if not has_baseline_edge and not has_policy_edge:
                raise MrtaSchemaError(
                    "member task must participate in a baseline or proposal edge",
                    failure_code="component_dangling_task",
                    task_id=task,
                    expected="baseline owner or policy proposal",
                    actual=False,
                    schema_version=self._SCHEMA_VERSION,
                )
        nominal = tensors["nominal_cost"]
        legal = tensors["pair_legal_mask"]
        index = _first_true_index(legal & (~torch.isfinite(nominal) | (nominal < 0)))
        if index is not None:
            robot, task = index
            raise MrtaSchemaError(
                "legal component pair cost must be finite and non-negative",
                failure_code="component_cost",
                robot_id=robot,
                task_id=task,
                expected="finite and >= 0",
                actual=float(nominal[robot, task].item()),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index((~legal) & ~torch.isnan(nominal))
        if index is not None:
            robot, task = index
            raise MrtaSchemaError(
                "illegal component pair cost must be canonical NaN",
                failure_code="component_invalid_cost",
                robot_id=robot,
                task_id=task,
                expected="NaN",
                actual=float(nominal[robot, task].item()),
                schema_version=self._SCHEMA_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        scalar_values: dict[str, object] = {
            "schema_version": self.schema_version,
            "component_id": self.component_id,
            "proposal_kind": self.proposal_kind,
            "pair_abs_threshold_spec": self.pair_abs_threshold_spec,
            "pair_rel_threshold_spec": self.pair_rel_threshold_spec,
            "component_abs_threshold_spec": self.component_abs_threshold_spec,
            "component_rel_threshold_spec": self.component_rel_threshold_spec,
            "transfer_penalty_spec": self.transfer_penalty_spec,
        }
        return _mapping_with_cloned_tensors(
            self,
            field_order=_COMPONENT_REQUEST_FIELD_ORDER,
            scalar_values=scalar_values,
        )


for _name, _, _ in _COMPONENT_REQUEST_TENSOR_SPECS:
    setattr(TransferComponentRequest, _name, _tensor_property(_name))


_COMPONENT_RESULT_TENSOR_SPECS = (
    ("proposal_accepted", ("M",), torch.bool),
    ("proposal_accepted_valid", ("M",), torch.bool),
    ("effective_assignment", ("M",), torch.int64),
    ("effective_ownership", ("N",), torch.int64),
    ("owner_change_mask", ("N",), torch.bool),
    *_BATCH_GENERATION_SPECS,
)
_COMPONENT_RESULT_FIELD_ORDER = (
    "schema_version",
    "component_id",
    "accepted",
    "rejection_reason",
    "all_rejection_reasons",
    "proposal_accepted",
    "proposal_accepted_valid",
    "effective_assignment",
    "effective_ownership",
    "owner_change_mask",
    "assigned_count_before",
    "assigned_count_after",
    "local_cost_before",
    "local_cost_after",
    "transfer_count",
    "commit_generation",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
)


def _canonical_rejection_tuple(
    value: object,
    *,
    schema_version: str,
) -> tuple[ComponentRejectionReason, ...]:
    if type(value) is not tuple:
        raise MrtaSchemaError(
            "all_rejection_reasons must be an exact immutable tuple",
            failure_code="rejection_reason_tuple",
            expected="tuple[ComponentRejectionReason, ...]",
            actual=type(value),
            schema_version=schema_version,
        )
    for reason in value:
        if (
            type(reason) is not ComponentRejectionReason
            or reason is ComponentRejectionReason.NONE
        ):
            raise MrtaSchemaError(
                "all_rejection_reasons contains an invalid reason",
                failure_code="rejection_reason_tuple",
                expected="unique non-NONE canonical reasons",
                actual=reason,
                schema_version=schema_version,
            )
    order = {reason: index for index, reason in enumerate(ComponentRejectionReason)}
    expected = tuple(sorted(set(value), key=order.__getitem__))
    if value != expected:
        raise MrtaSchemaError(
            "all_rejection_reasons must be unique and in canonical enum order",
            failure_code="rejection_reason_order",
            expected=expected,
            actual=value,
            schema_version=schema_version,
        )
    return value


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TransferComponentResult(_TensorDtoMixin):
    """Validated whole-component outcome; this DTO performs no commit."""

    schema_version: str
    component_id: str
    accepted: bool
    rejection_reason: ComponentRejectionReason
    all_rejection_reasons: tuple[ComponentRejectionReason, ...]
    assigned_count_before: int
    assigned_count_after: int
    local_cost_before: float
    local_cost_after: float
    transfer_count: int
    commit_generation: int
    _request: TransferComponentRequest = field(repr=False)
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    _SCHEMA_VERSION = TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION
    _TENSOR_SPECS = _COMPONENT_RESULT_TENSOR_SPECS

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MrtaSchemaError(
            "TransferComponentResult must be created by from_mapping()",
            failure_code="factory_required",
            expected="TransferComponentResult.from_mapping",
            actual="direct constructor",
            schema_version=self._SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        request: TransferComponentRequest,
        device: torch.device,
    ) -> "TransferComponentResult":
        values = _require_mapping_keys(
            values,
            field_order=_COMPONENT_RESULT_FIELD_ORDER,
            schema_version=cls._SCHEMA_VERSION,
        )
        _require_schema_version(
            values["schema_version"],
            expected=cls._SCHEMA_VERSION,
        )
        if type(request) is not TransferComponentRequest:
            raise MrtaSchemaError(
                "component result requires canonical request binding",
                failure_code="request_type",
                expected=TransferComponentRequest,
                actual=type(request),
                schema_version=cls._SCHEMA_VERSION,
            )
        request.validate_integrity()
        explicit_device = _require_explicit_device(
            device,
            schema_version=cls._SCHEMA_VERSION,
        )
        if explicit_device != request.device:
            raise MrtaSchemaError(
                "component result device differs from request",
                failure_code="device",
                expected=request.device,
                actual=explicit_device,
                schema_version=cls._SCHEMA_VERSION,
            )
        accepted = _require_bool_scalar(
            values["accepted"],
            field_name="accepted",
            schema_version=cls._SCHEMA_VERSION,
        )
        reason = values["rejection_reason"]
        if type(reason) is not ComponentRejectionReason:
            raise MrtaSchemaError(
                "rejection_reason must use the canonical enum",
                failure_code="rejection_reason",
                expected=ComponentRejectionReason,
                actual=type(reason),
                schema_version=cls._SCHEMA_VERSION,
            )
        all_reasons = _canonical_rejection_tuple(
            values["all_rejection_reasons"],
            schema_version=cls._SCHEMA_VERSION,
        )
        if accepted:
            if reason is not ComponentRejectionReason.NONE or all_reasons:
                raise MrtaSchemaError(
                    "accepted component must have NONE and no rejection set",
                    failure_code="accepted_rejection_relation",
                    expected=(ComponentRejectionReason.NONE, ()),
                    actual=(reason, all_reasons),
                    schema_version=cls._SCHEMA_VERSION,
                )
        else:
            if (
                reason is ComponentRejectionReason.NONE
                or not all_reasons
                or reason is not all_reasons[0]
            ):
                raise MrtaSchemaError(
                    "rejected component requires canonical first non-NONE reason",
                    failure_code="accepted_rejection_relation",
                    expected="reason == canonical first(all_rejection_reasons)",
                    actual=(reason, all_reasons),
                    schema_version=cls._SCHEMA_VERSION,
                )
        component_id = _require_canonical_string(
            values["component_id"],
            field_name="component_id",
            schema_version=cls._SCHEMA_VERSION,
        )
        if component_id != request.component_id:
            raise MrtaGenerationError(
                "component result ID differs from request",
                failure_code="request_component_id",
                expected=request.component_id,
                actual=component_id,
                schema_version=cls._SCHEMA_VERSION,
            )
        counts = {
            name: _require_int64_scalar(
                values[name],
                field_name=name,
                schema_version=cls._SCHEMA_VERSION,
                nonnegative=True,
            )
            for name in (
                "assigned_count_before",
                "assigned_count_after",
                "transfer_count",
            )
        }
        if (
            counts["assigned_count_before"] > min(request.num_robots, request.num_tasks)
            or counts["assigned_count_after"] > min(request.num_robots, request.num_tasks)
        ):
            raise MrtaSchemaError(
                "assigned counts exceed component dimensions",
                failure_code="assigned_count_range",
                expected=(0, min(request.num_robots, request.num_tasks)),
                actual=(
                    counts["assigned_count_before"],
                    counts["assigned_count_after"],
                ),
                schema_version=cls._SCHEMA_VERSION,
            )
        costs = {
            name: _require_finite_float(
                values[name],
                field_name=name,
                schema_version=cls._SCHEMA_VERSION,
                nonnegative=True,
            )
            for name in ("local_cost_before", "local_cost_after")
        }
        commit_generation = _require_int64_scalar(
            values["commit_generation"],
            field_name="commit_generation",
            schema_version=cls._SCHEMA_VERSION,
            nonnegative=accepted,
            allow_minus_one=not accepted,
        )
        if (accepted and commit_generation < 0) or (
            not accepted and commit_generation != -1
        ):
            raise MrtaSchemaError(
                "commit generation must be non-negative iff component accepted",
                failure_code="commit_generation",
                expected="accepted: >=0; rejected: -1",
                actual=commit_generation,
                schema_version=cls._SCHEMA_VERSION,
            )
        snapshots = _capture_tensor_specs(
            values,
            specs=cls._TENSOR_SPECS,
            device=explicit_device,
            num_envs=1,
            num_robots=request.num_robots,
            num_tasks=request.num_tasks,
            schema_version=cls._SCHEMA_VERSION,
        )
        result_internal = {
            name: snapshot.internal(
                field_name=name,
                schema_version=cls._SCHEMA_VERSION,
            )
            for name, snapshot in snapshots.items()
        }
        request_internal = request._validated_internal_tensors()
        _validate_batch_generation(
            result_internal,
            num_envs=1,
            schema_version=cls._SCHEMA_VERSION,
        )
        for name in (
            "env_id",
            "episode_generation",
            "transition_generation",
            "assignment_tick_generation",
        ):
            if not torch.equal(result_internal[name], request_internal[name]):
                raise MrtaGenerationError(
                    "component result generation differs from request",
                    failure_code="request_generation",
                    field_name=name,
                    expected=int(request_internal[name][0].item()),
                    actual=int(result_internal[name][0].item()),
                    schema_version=cls._SCHEMA_VERSION,
                )
        instance = object.__new__(cls)
        _initialize_tensor_dto(
            instance,
            schema_version=cls._SCHEMA_VERSION,
            device=explicit_device,
            num_envs=1,
            num_robots=request.num_robots,
            num_tasks=request.num_tasks,
            tensor_snapshots=snapshots,
            metadata={
                "component_id": component_id,
                "accepted": accepted,
                "rejection_reason": reason,
                "all_rejection_reasons": all_reasons,
                **counts,
                **costs,
                "commit_generation": commit_generation,
                "_request": request,
            },
        )
        instance._validate_semantics()
        return instance

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        request_tensors = self._request._validated_internal_tensors()
        _validate_batch_generation(
            tensors,
            num_envs=1,
            schema_version=self._SCHEMA_VERSION,
        )
        policy = request_tensors["policy_proposal_present_mask"]
        member_robots = request_tensors["member_robot_mask"]
        member_tasks = request_tensors["member_task_mask"]
        if not torch.equal(tensors["proposal_accepted_valid"], policy):
            raise MrtaSchemaError(
                "proposal_accepted_valid must equal request policy rows",
                failure_code="proposal_accepted_validity",
                expected="request.policy_proposal_present_mask",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        if bool((tensors["proposal_accepted"] & ~policy).any()):
            raise MrtaSchemaError(
                "only policy rows can have proposal_accepted=true",
                failure_code="proposal_accepted_validity",
                expected="proposal_accepted <= policy mask",
                actual="forced/nonpolicy row accepted",
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(
            member_robots
            & ~policy
            & (
                tensors["effective_assignment"]
                != request_tensors["baseline_assignment_a0"]
            )
        )
        if index is not None:
            robot = index[0]
            raise MrtaSchemaError(
                "nonpolicy component member must retain baseline assignment",
                failure_code="nonpolicy_member_assignment",
                field_name="effective_assignment",
                robot_id=robot,
                expected=int(
                    request_tensors["baseline_assignment_a0"][robot].item()
                ),
                actual=int(
                    tensors["effective_assignment"][robot].item()
                ),
                schema_version=self._SCHEMA_VERSION,
            )
        accepted_proposal = tensors["proposal_accepted"] & policy
        index = _first_true_index(
            accepted_proposal
            & (
                tensors["effective_assignment"]
                != request_tensors["proposed_task_id"]
            )
        )
        if index is not None:
            robot = index[0]
            raise MrtaSchemaError(
                "accepted proposal must become that robot's effective assignment",
                failure_code="proposal_effective_mismatch",
                field_name="effective_assignment",
                robot_id=robot,
                expected=int(
                    request_tensors["proposed_task_id"][robot].item()
                ),
                actual=int(
                    tensors["effective_assignment"][robot].item()
                ),
                schema_version=self._SCHEMA_VERSION,
            )
        if self.accepted:
            unaccepted_policy = policy & ~tensors["proposal_accepted"]
            for robot in range(self._num_robots):
                if not bool(unaccepted_policy[robot].item()):
                    continue
                kind = self._request.proposal_kind[robot]
                if kind is not ProposalKind.CONTINUE:
                    raise MrtaSchemaError(
                        "accepted component cannot partially reject a "
                        "CLAIM, SWITCH, or NOOP_IDLE policy proposal",
                        failure_code="accepted_policy_partial",
                        field_name="proposal_accepted",
                        robot_id=robot,
                        expected=ProposalKind.CONTINUE,
                        actual=kind,
                        schema_version=self._SCHEMA_VERSION,
                    )
                current_task = int(
                    request_tensors["proposed_task_id"][robot].item()
                )
                effective_owner = int(
                    tensors["effective_ownership"][current_task].item()
                )
                covered = (
                    int(
                        tensors["effective_assignment"][robot].item()
                    )
                    == -1
                    and 0 <= effective_owner < self._num_robots
                    and effective_owner != robot
                    and bool(
                        tensors["proposal_accepted"][
                            effective_owner
                        ].item()
                    )
                    and int(
                        request_tensors["proposed_task_id"][
                            effective_owner
                        ].item()
                    )
                    == current_task
                )
                if not covered:
                    raise MrtaSchemaError(
                        "unaccepted CONTINUE must be covered by another "
                        "accepted proposal in the same component",
                        failure_code="continue_override_coverage",
                        field_name="proposal_accepted",
                        robot_id=robot,
                        task_id=current_task,
                        expected=(
                            "effective_assignment=-1 and different "
                            "accepted effective owner"
                        ),
                        actual=effective_owner,
                        schema_version=self._SCHEMA_VERSION,
                    )
        if not self.accepted and bool(tensors["proposal_accepted"].any()):
            raise MrtaSchemaError(
                "whole-component rejection cannot accept a member proposal",
                failure_code="whole_component_reject",
                expected="all proposal_accepted false",
                actual="true proposal acceptance",
                schema_version=self._SCHEMA_VERSION,
            )
        outside_robot = ~member_robots
        index = _first_true_index(
            outside_robot
            & (
                tensors["effective_assignment"]
                != request_tensors["baseline_assignment_a0"]
            )
        )
        if index is not None:
            robot = index[0]
            raise MrtaSchemaError(
                "robot outside component must retain baseline assignment",
                failure_code="component_boundary_assignment",
                field_name="effective_assignment",
                robot_id=robot,
                expected=int(
                    request_tensors["baseline_assignment_a0"][robot].item()
                ),
                actual=int(
                    tensors["effective_assignment"][robot].item()
                ),
                schema_version=self._SCHEMA_VERSION,
            )
        outside_task = ~member_tasks
        index = _first_true_index(
            outside_task
            & (
                tensors["effective_ownership"]
                != request_tensors["baseline_ownership_a0"]
            )
        )
        if index is not None:
            task = index[0]
            raise MrtaSchemaError(
                "task outside component must retain baseline ownership",
                failure_code="component_boundary_ownership",
                field_name="effective_ownership",
                task_id=task,
                expected=int(
                    request_tensors["baseline_ownership_a0"][task].item()
                ),
                actual=int(
                    tensors["effective_ownership"][task].item()
                ),
                schema_version=self._SCHEMA_VERSION,
            )
        index = _first_true_index(
            outside_task & tensors["owner_change_mask"]
        )
        if index is not None:
            task = index[0]
            raise MrtaSchemaError(
                "task outside component cannot report owner change",
                failure_code="component_boundary_owner_change",
                field_name="owner_change_mask",
                task_id=task,
                expected=False,
                actual=True,
                schema_version=self._SCHEMA_VERSION,
            )
        _validate_assignment_ownership_consistency(
            tensors["effective_assignment"],
            tensors["effective_ownership"],
            num_robots=self._num_robots,
            num_tasks=self._num_tasks,
            field_prefix="effective",
            schema_version=self._SCHEMA_VERSION,
        )
        expected_change = (
            tensors["effective_ownership"]
            != request_tensors["baseline_ownership_a0"]
        )
        if not torch.equal(tensors["owner_change_mask"], expected_change):
            raise MrtaSchemaError(
                "owner_change_mask differs from baseline/effective ownership",
                failure_code="owner_change_mask",
                expected="effective_ownership != baseline_ownership_a0",
                actual="tensor values differ",
                schema_version=self._SCHEMA_VERSION,
            )
        expected_assigned_before = int(
            (
                member_tasks
                & (request_tensors["baseline_ownership_a0"] >= 0)
            ).sum().item()
        )
        if self.assigned_count_before != expected_assigned_before:
            raise MrtaSchemaError(
                "assigned_count_before differs from baseline member ownership",
                failure_code="assigned_count_before",
                field_name="assigned_count_before",
                expected=expected_assigned_before,
                actual=self.assigned_count_before,
                schema_version=self._SCHEMA_VERSION,
            )
        expected_assigned_after = int(
            (
                member_tasks & (tensors["effective_ownership"] >= 0)
            ).sum().item()
        )
        if self.assigned_count_after != expected_assigned_after:
            raise MrtaSchemaError(
                "assigned_count_after differs from effective member ownership",
                failure_code="assigned_count_after",
                field_name="assigned_count_after",
                expected=expected_assigned_after,
                actual=self.assigned_count_after,
                schema_version=self._SCHEMA_VERSION,
            )
        if (
            self.accepted
            and self.assigned_count_after < self.assigned_count_before
        ):
            raise MrtaSchemaError(
                "accepted component cannot decrease assigned member tasks",
                failure_code="accepted_assigned_count_decrease",
                field_name="assigned_count_after",
                expected=f">= {self.assigned_count_before}",
                actual=self.assigned_count_after,
                schema_version=self._SCHEMA_VERSION,
            )
        expected_transfer_count = int(
            (
                member_tasks
                & (request_tensors["baseline_ownership_a0"] >= 0)
                & (tensors["effective_ownership"] >= 0)
                & tensors["owner_change_mask"]
            ).sum().item()
        )
        if self.transfer_count != expected_transfer_count:
            raise MrtaSchemaError(
                "transfer_count differs from changed existing member owners",
                failure_code="transfer_count",
                field_name="transfer_count",
                expected=expected_transfer_count,
                actual=self.transfer_count,
                schema_version=self._SCHEMA_VERSION,
            )
        if not self.accepted:
            if (
                not torch.equal(
                    tensors["effective_assignment"],
                    request_tensors["baseline_assignment_a0"],
                )
                or not torch.equal(
                    tensors["effective_ownership"],
                    request_tensors["baseline_ownership_a0"],
                )
                or bool(tensors["owner_change_mask"].any())
                or self.assigned_count_after != self.assigned_count_before
                or self.local_cost_after != self.local_cost_before
                or self.transfer_count != 0
            ):
                raise MrtaSchemaError(
                    "whole-component rejection must preserve event-updated baseline",
                    failure_code="whole_component_reject",
                    expected=(
                        "baseline effective state, unchanged counts/cost, "
                        "zero transfers"
                    ),
                    actual="rejected result claims a state change",
                    schema_version=self._SCHEMA_VERSION,
                )

    def to_mapping(self) -> Mapping[str, object]:
        return _mapping_with_cloned_tensors(
            self,
            field_order=_COMPONENT_RESULT_FIELD_ORDER,
            scalar_values={
                "schema_version": self.schema_version,
                "component_id": self.component_id,
                "accepted": self.accepted,
                "rejection_reason": self.rejection_reason,
                "all_rejection_reasons": self.all_rejection_reasons,
                "assigned_count_before": self.assigned_count_before,
                "assigned_count_after": self.assigned_count_after,
                "local_cost_before": self.local_cost_before,
                "local_cost_after": self.local_cost_after,
                "transfer_count": self.transfer_count,
                "commit_generation": self.commit_generation,
            },
        )


for _name, _, _ in _COMPONENT_RESULT_TENSOR_SPECS:
    setattr(TransferComponentResult, _name, _tensor_property(_name))


@dataclass(frozen=True, slots=True)
class ComponentRejectionRecord:
    """Immutable component-level penalty attribution; no reward is applied."""

    component_id: str
    reason: ComponentRejectionReason
    policy_caused: bool
    penalty_eligible: bool
    penalty_unit_count: int
    member_robot_ids: tuple[int, ...]
    member_task_ids: tuple[int, ...]
    env_id: int
    episode_generation: int
    transition_generation: int
    assignment_tick_generation: int

    schema_version: ClassVar[str] = COMPONENT_REJECTION_RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_canonical_string(
            self.component_id,
            field_name="component_id",
            schema_version=self.schema_version,
        )
        if (
            type(self.reason) is not ComponentRejectionReason
            or self.reason is ComponentRejectionReason.NONE
        ):
            raise MrtaSchemaError(
                "rejection record requires a canonical non-NONE reason",
                failure_code="rejection_reason",
                expected="non-NONE ComponentRejectionReason",
                actual=self.reason,
                schema_version=self.schema_version,
            )
        _require_bool_scalar(
            self.policy_caused,
            field_name="policy_caused",
            schema_version=self.schema_version,
        )
        _require_bool_scalar(
            self.penalty_eligible,
            field_name="penalty_eligible",
            schema_version=self.schema_version,
        )
        units = _require_int64_scalar(
            self.penalty_unit_count,
            field_name="penalty_unit_count",
            schema_version=self.schema_version,
            nonnegative=True,
        )
        expected_units = 1 if self.penalty_eligible else 0
        if units != expected_units or (
            self.penalty_eligible and not self.policy_caused
        ):
            raise MrtaSchemaError(
                "penalty unit must be one iff eligible and eligibility is policy-caused",
                failure_code="penalty_unit",
                expected=(expected_units, "eligible implies policy_caused"),
                actual=(units, self.policy_caused),
                schema_version=self.schema_version,
            )
        if self.reason in _NON_POLICY_REJECTION_REASONS and (
            self.policy_caused or self.penalty_eligible or units != 0
        ):
            raise MrtaSchemaError(
                "system/overflow/terminal rejection cannot be policy-penalized",
                failure_code="nonpolicy_rejection_attribution",
                expected=(False, False, 0),
                actual=(
                    self.policy_caused,
                    self.penalty_eligible,
                    units,
                ),
                schema_version=self.schema_version,
            )
        for field_name in ("member_robot_ids", "member_task_ids"):
            members = getattr(self, field_name)
            if (
                type(members) is not tuple
                or not members
                or any(type(member) is not int or member < 0 for member in members)
                or members != tuple(sorted(set(members)))
            ):
                raise MrtaSchemaError(
                    f"{field_name} must be a non-empty sorted unique int tuple",
                    failure_code="component_members",
                    field_name=field_name,
                    expected="sorted unique non-negative tuple",
                    actual=members,
                    schema_version=self.schema_version,
                )
        for name in (
            "env_id",
            "episode_generation",
            "transition_generation",
            "assignment_tick_generation",
        ):
            _require_int64_scalar(
                getattr(self, name),
                field_name=name,
                schema_version=self.schema_version,
                nonnegative=(name != "env_id"),
            )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "component_id": self.component_id,
                "reason": self.reason,
                "policy_caused": self.policy_caused,
                "penalty_eligible": self.penalty_eligible,
                "penalty_unit_count": self.penalty_unit_count,
                "member_robot_ids": self.member_robot_ids,
                "member_task_ids": self.member_task_ids,
                "env_id": self.env_id,
                "episode_generation": self.episode_generation,
                "transition_generation": self.transition_generation,
                "assignment_tick_generation": self.assignment_tick_generation,
            }
        )


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if isinstance(value, (tuple, list)):
        return tuple(_deep_readonly(item) for item in value)
    return value


def _tensor_field_descriptor(
    name: str,
    symbols: tuple[str, ...],
    dtype: torch.dtype,
) -> Mapping[str, object]:
    return {
        "name": name,
        "shape": symbols,
        "dtype": str(dtype),
    }


def _schema_descriptor(
    schema_version: str,
    field_order: tuple[str, ...],
    tensor_specs: tuple[tuple[str, tuple[str, ...], torch.dtype], ...],
) -> Mapping[str, object]:
    tensor_lookup = {
        name: (symbols, dtype) for name, symbols, dtype in tensor_specs
    }
    fields: list[Mapping[str, object]] = []
    for name in field_order:
        if name in tensor_lookup:
            symbols, dtype = tensor_lookup[name]
            fields.append(_tensor_field_descriptor(name, symbols, dtype))
        else:
            fields.append(
                {
                    "name": name,
                    "shape": "scalar_or_immutable_typed_tuple",
                    "dtype": "typed_python",
                }
            )
    return {"schema_version": schema_version, "fields": tuple(fields)}


_ACTION_CONTRACT = {
    "contract_version": ACTION_CONTRACT_VERSION,
    "num_agents": "scale_contract.M",
    "action_dimension": "scale_contract.N + 1",
    "target_action_id_domain": (
        "global_task_ids_0_through_scale_contract.N_minus_1"
    ),
    "noop_raw_id": "scale_contract.N",
    "noop_decoded_value": -1,
    "available_action_order": "target_global_task_ids_ascending_then_noop",
    "decision_valid_mask_contract_version": (
        DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION
    ),
    "proposal_mask_contract_version": PROPOSAL_SNAPSHOT_SCHEMA_VERSION,
    "cross_section_invariants": (
        "num_agents == scale_contract.M",
        "action_dimension == scale_contract.N + 1",
        "target_action_id_domain == global task IDs "
        "0..scale_contract.N-1",
        "noop_raw_id == scale_contract.N",
        "noop_decoded_value == -1",
        "available_action_order == target global task IDs followed by noop",
        "len(scale_contract.ordered_agent_names) == num_agents",
    ),
}


_LOCAL_CANDIDATE_UNRESOLVED_PARAMETERS = (
    UnresolvedParameterSpec(
        name="top_k_tasks_per_robot",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "maximum_nominal_cost_ranked_tasks_per_local_robot_before_"
            "current_task_retention"
        ),
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="local_robot_cap",
        owner_phase="phase_b",
        semantic_purpose="maximum_robots_in_merged_local_assignment_set",
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="local_task_cap",
        owner_phase="phase_b",
        semantic_purpose="maximum_tasks_in_merged_local_assignment_set",
    ).to_mapping(),
)


_COST_PATH_UNRESOLVED_PARAMETERS = (
    UnresolvedParameterSpec(
        name="alignment_time_constant",
        owner_phase="phase_b_e",
        semantic_purpose="robot_specific_expected_terminal_alignment_time",
    ).to_mapping(),
)


_COMPONENT_UNRESOLVED_PARAMETERS = (
    UnresolvedParameterSpec(
        name="pair_abs_threshold",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "strict_absolute_expected_time_improvement_for_active_preemption"
        ),
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="pair_rel_threshold",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "strict_relative_expected_time_improvement_for_active_preemption"
        ),
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="component_abs_threshold",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "strict_absolute_expected_time_improvement_for_equal_count_"
            "component_acceptance"
        ),
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="component_rel_threshold",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "strict_relative_expected_time_improvement_for_equal_count_"
            "component_acceptance"
        ),
    ).to_mapping(),
    UnresolvedParameterSpec(
        name="transfer_penalty",
        owner_phase="phase_b_e",
        semantic_purpose=(
            "expected_time_regularizer_per_owner_change_in_equal_count_"
            "component_objective"
        ),
    ).to_mapping(),
)


_LOCAL_CANDIDATE_SEMANTICS = {
    "projection_version": LOCAL_CANDIDATE_SEMANTICS_VERSION,
    "seed_sources": (
        "needs_assignment_mask",
        "trigger_eligible_finalized_LifecycleEventRecord",
        "AssignmentOpportunityRecord",
    ),
    "seed_robot_mask_equation": (
        "seed_robot_mask[e,i] = needs_assignment_mask[e,i] OR any "
        "trigger-eligible LifecycleEventRecord with robot_id == i OR any "
        "AssignmentOpportunityRecord with robot_id == i"
    ),
    "trigger_record_robot_rule": (
        "task-related lifecycle events use canonical record/payload cause "
        "robot attribution"
    ),
    "forbidden_trigger_records": ("ResolverDiagnosticRecord",),
    "candidate_prefilter_order": (
        "global_task_valid",
        "task_not_completed_or_team_infeasible",
        "failed_pair_legal",
        "nominal_path_valid",
    ),
    "candidate_eligibility_equation": (
        "global_task_valid AND task_not_completed_or_team_infeasible AND "
        "failed_pair_legal AND nominal_path_valid"
    ),
    "top_k_sort_order": (
        "nominal_cost_ascending",
        "global_task_id_ascending",
    ),
    "occupied_task_candidate_rule": (
        "occupied tasks are not filtered before Top-K"
    ),
    "current_task_retention_rule": (
        "append a still-legal event-updated current task as CONTINUE "
        "regardless of rank"
    ),
    "owner_expansion_rounds": 1,
    "owner_expansion_equation": (
        "owner_added = owners(seed Top-K occupied tasks) minus seeds"
    ),
    "second_layer_owner_recursion": False,
    "outside_set_owner_preemption_rule": (
        "candidate fact may remain but preemption mask is false"
    ),
    "overlap_identity": (
        "preliminary sets overlap when robot masks or task masks intersect"
    ),
    "overlap_merge_rule": "transitive_closure_merge",
    "post_merge_recomputation_order": (
        "top_k",
        "current_task_retention",
        "available_actions",
        "decision_valid_mask",
    ),
    "post_merge_owner_expansion": False,
    "global_robot_identity": "preserve_global_robot_ids",
    "global_task_identity": "preserve_global_task_ids",
    "local_observation_repacking": False,
    "overflow_behavior": "FAIL_CLOSED_NO_ASSIGNMENT",
    "request_result_association_key": (
        "env_id",
        "episode_generation",
        "transition_generation",
        "assignment_tick_generation",
    ),
    "unresolved_parameters": _LOCAL_CANDIDATE_UNRESOLVED_PARAMETERS,
}


_COST_PATH_SEMANTICS = {
    "projection_version": COST_PATH_SEMANTICS_VERSION,
    "cost_unit": "expected_time_seconds",
    "tensor_shapes": (
        ("navigation_cost", ("E", "M", "N")),
        ("alignment_cost", ("E", "M", "N")),
        ("nominal_cost", ("E", "M", "N")),
        ("nominal_path_valid", ("E", "M", "N")),
    ),
    "tensor_dtypes": (
        ("navigation_cost", "torch.float32"),
        ("alignment_cost", "torch.float32"),
        ("nominal_cost", "torch.float32"),
        ("nominal_path_valid", "torch.bool"),
    ),
    "cost_generation_key": (
        "env_id",
        "episode_generation",
        "transition_generation",
        "assignment_tick_generation",
    ),
    "refresh_rule": "recompute_at_each_assignment_tick",
    "snapshot_consistency_rule": (
        "single fact-updated immutable snapshot; each pair is estimated at "
        "most once; one finalized NominalPairCostResult is read-only"
    ),
    "navigation_cost_semantics": (
        "expected navigation time from current physical state to terminal "
        "alignment region"
    ),
    "alignment_cost_semantics": (
        "pair-specific expected terminal alignment time"
    ),
    "nominal_cost_equation": (
        "nominal_cost[e,i,j] = navigation_cost[e,i,j] + "
        "alignment_cost[e,i,j]"
    ),
    "current_owner_navigation_rule": (
        "NAVIGATING uses remaining expected navigation seconds; ALIGNING "
        "uses zero navigation seconds"
    ),
    "current_owner_alignment_rule": (
        "remaining expected terminal alignment seconds"
    ),
    "nonowner_cost_rule": (
        "complete navigation and pair-specific alignment from current "
        "physical state"
    ),
    "alignment_fallback_rule": (
        "alignment_time_constant[i] expected-time seconds broadcast over "
        "global task j when no pair estimator exists"
    ),
    "unresolved_parameters": _COST_PATH_UNRESOLVED_PARAMETERS,
    "path_valid_authority": "cost_path_estimator_authority",
    "valid_pair_rule": (
        "path_valid true requires navigation, alignment, and nominal costs "
        "finite and nonnegative with exact nominal sum"
    ),
    "invalid_path_encoding": (
        "path_valid false and navigation, alignment, nominal costs all "
        "canonical NaN"
    ),
    "finite_invalid_sentinel_allowed": False,
    "top_k_penalty_rule": "no_transfer_or_switch_penalty",
    "pair_gate_cost_source": "nominal_remaining_cost",
    "component_penalty_scope": (
        "transfer_penalty only in complete equal-count component Jp"
    ),
}


_COMPONENT_SEMANTICS = {
    "projection_version": COMPONENT_SEMANTICS_VERSION,
    "baseline_a0_identity": (
        "LifecycleTransitionResult.updated_ownership after completion, "
        "release, failure, availability, and TEAM_INFEASIBLE updates"
    ),
    "component_scope": "connected_transfer_component_members_only",
    "proposal_source": (
        "policy_proposal_present_mask only; forced rows are forbidden"
    ),
    "contention_order": (
        "non_preemptible_current_owner",
        "hard_and_pair_legal",
        "improvement_descending",
        "new_nominal_cost_ascending",
        "global_robot_id_ascending",
    ),
    "contention_loser_rule": (
        "CONTENTION_LOSS; no runner-up promotion after winner component failure"
    ),
    "component_closure_rule": "complete_connected_transfer_component",
    "whole_component_outcome": "all_accept_or_all_reject",
    "partial_policy_acceptance_rule": False,
    "covered_continue_override_rule": (
        "only a current-owner CONTINUE may be unaccepted and become "
        "effective_assignment=-1 when another accepted member takes its task"
    ),
    "assigned_unfinished_count_equation": (
        "assigned_count(a) = sum_j 1[member_task_mask[j] AND "
        "event-updated task j is unfinished AND owner_a[j] >= 0]"
    ),
    "assigned_count_gate": (
        "increase_allowed_after_all_legality_checks",
        "equal_requires_component_improvement",
        "decrease_rejected",
    ),
    "active_preemption_definition": (
        "active_preemption(i,j) = member_task_mask[j] AND event-updated task "
        "j is unfinished AND a0_owner[j] >= 0 AND staged_owner[j] == i AND "
        "i != a0_owner[j]"
    ),
    "pair_improvement_equations": (
        "C(a0_owner[j],j) - C(i,j) > pair_abs_threshold",
        "C(i,j) < (1 - pair_rel_threshold) * C(a0_owner[j],j)",
    ),
    "pair_gate_conjunction": (
        "both strict pair improvement equations for every active preemption"
    ),
    "baseline_cost_equation": (
        "J0 = sum_j 1[member_task_mask[j] AND event-updated task j is "
        "unfinished AND a0_owner[j] >= 0] * C(a0_owner[j],j)"
    ),
    "staged_cost_equation": (
        "Jp = sum_j 1[member_task_mask[j] AND event-updated task j is "
        "unfinished AND staged_owner[j] >= 0] * C(staged_owner[j],j) + "
        "transfer_penalty * N_owner_changes"
    ),
    "owner_change_count_equation": (
        "N_owner_changes = sum_j 1[member_task_mask[j] AND event-updated "
        "task j is unfinished AND a0_owner[j] >= 0 AND staged_owner[j] >= 0 "
        "AND staged_owner[j] != a0_owner[j]]"
    ),
    "count_increase_rule": (
        "requires hard, pair, closure, uniqueness, and atomic staging checks"
    ),
    "count_equal_improvement_equations": (
        "J0 - Jp > component_abs_threshold",
        "Jp < (1 - component_rel_threshold) * J0",
    ),
    "count_decrease_rule": (
        "reject; forced lifecycle release is already represented in a0"
    ),
    "canonical_rejection_order": tuple(
        item.name for item in ComponentRejectionReason
    ),
    "nonpolicy_rejection_reasons": (
        ComponentRejectionReason.LOCAL_SET_OVERFLOW_FAIL_CLOSED.name,
        ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION.name,
        ComponentRejectionReason.TERMINAL_TRANSITION.name,
    ),
    "policy_penalty_attribution_rule": (
        "first seven non-NONE ordinary rejection reasons are policy-caused "
        "and penalty-eligible once per rejected component"
    ),
    "penalty_unit_equation": (
        "penalty_unit_count == 1 iff penalty_eligible else 0"
    ),
    "invariant_failure_rule": (
        "generation, historical-mask, duplicate-ownership, or half-mutation "
        "failure is typed fail-fast and not a learning rejection"
    ),
    "forbidden_resolver_behaviors": (
        "matching_or_search",
        "proposal_subset_search",
        "second_candidate_generation",
        "runner_up_promotion",
        "unproposed_task_assignment",
        "non_atomic_partial_commit",
    ),
    "unresolved_parameters": _COMPONENT_UNRESOLVED_PARAMETERS,
}


_PUBLIC_DESCRIPTOR = _deep_readonly(
    {
        "contract_version": ASSIGNMENT_MRTA_CONTRACT_VERSION,
        "observable_immutability_contract_version": (
            OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION
        ),
        "unresolved_parameter_spec": {
            "schema_version": UNRESOLVED_PARAMETER_SPEC_VERSION,
            "fields": ("name", "owner_phase", "semantic_purpose"),
            "numeric_value_present": False,
        },
        "enum_order": {
            "LocalSetOverflowDisposition": tuple(
                item.name for item in LocalSetOverflowDisposition
            ),
            "ProposalKind": tuple(item.name for item in ProposalKind),
            "StoredActionRowKind": tuple(
                item.name for item in StoredActionRowKind
            ),
            "ComponentRejectionReason": tuple(
                item.name for item in ComponentRejectionReason
            ),
        },
        "schemas": {
            "nominal_pair_cost": _schema_descriptor(
                NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION,
                _NOMINAL_COST_FIELD_ORDER,
                _NOMINAL_COST_TENSOR_SPECS,
            ),
            "local_set_request": _schema_descriptor(
                LOCAL_SET_REQUEST_SCHEMA_VERSION,
                _LOCAL_SET_REQUEST_FIELD_ORDER,
                _LOCAL_SET_REQUEST_TENSOR_SPECS,
            ),
            "local_set_result": _schema_descriptor(
                LOCAL_SET_RESULT_SCHEMA_VERSION,
                _LOCAL_SET_RESULT_FIELD_ORDER,
                _LOCAL_SET_RESULT_TENSOR_SPECS,
            ),
            "top_k_candidate": _schema_descriptor(
                TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION,
                _TOP_K_FIELD_ORDER,
                _TOP_K_TENSOR_SPECS,
            ),
            "decision_valid_mask": _schema_descriptor(
                DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION,
                _DVM_FIELD_ORDER,
                _DVM_TENSOR_SPECS,
            ),
            "proposal_snapshot": _schema_descriptor(
                PROPOSAL_SNAPSHOT_SCHEMA_VERSION,
                _PROPOSAL_FIELD_ORDER,
                _PROPOSAL_TENSOR_SPECS,
            ),
            "component_request": _schema_descriptor(
                TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION,
                _COMPONENT_REQUEST_FIELD_ORDER,
                _COMPONENT_REQUEST_TENSOR_SPECS,
            ),
            "component_result": _schema_descriptor(
                TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION,
                _COMPONENT_RESULT_FIELD_ORDER,
                _COMPONENT_RESULT_TENSOR_SPECS,
            ),
            "component_rejection": {
                "schema_version": COMPONENT_REJECTION_RECORD_SCHEMA_VERSION,
                "fields": (
                    "schema_version",
                    "component_id",
                    "reason",
                    "policy_caused",
                    "penalty_eligible",
                    "penalty_unit_count",
                    "member_robot_ids",
                    "member_task_ids",
                    "env_id",
                    "episode_generation",
                    "transition_generation",
                    "assignment_tick_generation",
                ),
            },
        },
        "nominal_cost_equation": (
            "nominal_cost = navigation_cost + alignment_cost"
        ),
        "invalid_path_encoding": "path_valid=false and all cost cells NaN",
        "local_trigger_records": (
            "LifecycleEventRecord",
            "AssignmentOpportunityRecord",
        ),
        "local_trigger_forbidden": ("ResolverDiagnosticRecord",),
        "owner_expansion_rounds": 1,
        "overflow_behavior": "fail_closed_no_assignment",
        "global_task_identity": "no local task renumbering",
        "target_mask_equation": (
            "global_task_valid & failed_pair_legal & nominal_path_valid & "
            "local_topk_or_continue & ownership_preemption_legal & "
            "robot_available"
        ),
        "available_action_equation": "concat(target_action_mask, noop_action_mask)",
        "decision_valid_equation": (
            "decision_opportunity_present & robot_available & "
            "semantic_legal_action_count>=2"
        ),
        "construction_legality_context": {
            "inputs": tuple(
                _tensor_field_descriptor(name, symbols, dtype)
                for name, symbols, dtype in _DVM_CONSTRUCTION_CONTEXT_SPECS
            ),
            "persistence": "constructor_only_not_snapshot_mapping_fields",
            "equations": (
                "executing_mask & idle_or_needs_assignment_mask == false",
                "opportunity & robot_available => exactly one context",
                "current_task_id in [-1,N-1]",
                "executing opportunity => current task globally valid, "
                "local/continue retained, target true, noop false",
                "idle_or_needs_assignment => current_task_id == -1",
                "idle/needs opportunity => noop true",
                "current-task retention applies only to opportunity rows",
            ),
        },
        "four_mask_equations": (
            "policy_proposal_present_mask == decision_valid_mask",
            "storage_row_present_mask == nonterminal_mask",
            "forced_nondecision_mask == storage_row_present_mask & "
            "nonterminal_mask & ~decision_valid_mask",
            "storage_row_present_mask == policy_proposal_present_mask | "
            "forced_nondecision_mask",
            "policy_proposal_present_mask & forced_nondecision_mask == false",
        ),
        "proposal_effective_separation": (
            "ProposalSnapshot has no effective_assignment field"
        ),
        "resolver_policy_selection": (
            "policy_proposal_present_mask only; forced rows forbidden"
        ),
        "component_behavior": (
            "caller-provided whole accept/reject validation only; "
            "no graph, search, arbitration, objective, or commit"
        ),
        "penalty_unit_equation": (
            "penalty_unit_count == 1 iff penalty_eligible else 0"
        ),
        "action_contract": _ACTION_CONTRACT,
        "local_candidate_semantics": _LOCAL_CANDIDATE_SEMANTICS,
        "cost_path_semantics": _COST_PATH_SEMANTICS,
        "component_semantics": _COMPONENT_SEMANTICS,
    }
)


def get_assignment_mrta_contract_descriptor() -> Mapping[str, object]:
    """Return the deterministic, deeply read-only public A3 MRTA descriptor."""

    return _PUBLIC_DESCRIPTOR  # type: ignore[return-value]


__all__ = [
    "ACTION_CONTRACT_VERSION",
    "ASSIGNMENT_MRTA_CONTRACT_VERSION",
    "AssignmentMrtaContractError",
    "CANONICAL_ASSIGNMENT_MRTA_MODULE",
    "COMPONENT_REJECTION_RECORD_SCHEMA_VERSION",
    "COMPONENT_SEMANTICS_VERSION",
    "COST_PATH_SEMANTICS_VERSION",
    "ComponentRejectionReason",
    "ComponentRejectionRecord",
    "DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION",
    "DecisionValidMaskSnapshot",
    "LOCAL_CANDIDATE_SEMANTICS_VERSION",
    "LOCAL_SET_REQUEST_SCHEMA_VERSION",
    "LOCAL_SET_RESULT_SCHEMA_VERSION",
    "LocalSetOverflowDisposition",
    "LocalSetRequest",
    "LocalSetResult",
    "MrtaGenerationError",
    "MrtaSchemaError",
    "MrtaSnapshotMutationError",
    "NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION",
    "NominalPairCostResult",
    "OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION",
    "PROPOSAL_SNAPSHOT_SCHEMA_VERSION",
    "ProposalKind",
    "ProposalSnapshot",
    "StoredActionRowKind",
    "TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION",
    "TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION",
    "TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION",
    "TopKCandidateResult",
    "TransferComponentRequest",
    "TransferComponentResult",
    "UNRESOLVED_PARAMETER_SPEC_VERSION",
    "UnresolvedParameterSpec",
    "get_assignment_mrta_contract_descriptor",
]
