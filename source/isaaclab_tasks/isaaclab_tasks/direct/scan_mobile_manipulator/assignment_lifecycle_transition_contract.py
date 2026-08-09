"""Pure transition-facts, lifecycle-authority, and consume-once contracts.

Phase A2 defines process-local schemas and authority identity only.  It does
not install an environment hook, place the runtime lifecycle authority, derive
TEAM_INFEASIBLE, invoke a resolver, or connect to training/checkpoint paths.

Tensor immutability is deliberately stated as an observable supported-path
contract: construction isolates input aliases, public accessors return clones,
and normal in-place corruption of private backing tensors is detected before
supported reads/consume/finalize operations.  This is not a cryptographic or
adversarial-reflection guarantee.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
ASSIGNMENT_LIFECYCLE_TRANSITION_SOURCE_PURPOSE = (
    "pure assignment lifecycle transition facts and authority contract"
)

if __name__ != CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment lifecycle transition "
        "contract source must fail before declaring identity-bearing types or "
        "importing torch; "
        f"expected module key="
        f"{CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose={ASSIGNMENT_LIFECYCLE_TRANSITION_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from types import MappingProxyType
from typing import TYPE_CHECKING
import torch

if TYPE_CHECKING:
    from .assignment_event_contract import LifecycleEventRecord


ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION = (
    "assignment_lifecycle_transition_contract_v2"
)
EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION = "execution_transition_facts_v1"
LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION = "lifecycle_transition_result_v1"
TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION = "transition_consume_receipt_v1"
EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION = (
    "execution_facts_producer_contract_v1"
)
LIFECYCLE_AUTHORITY_CONTRACT_VERSION = "unique_lifecycle_authority_v1"
PAIR_ATTRIBUTION_CONTRACT_VERSION = "pair_attributed_execution_signals_v1"
OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION = (
    "assignment_tensor_alias_isolation_v1"
)
FAILURE_TERMINATION_SEMANTICS_VERSION = (
    "event_gated_failure_termination_semantics_v1"
)

_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1
_RESULT_FACTORY_CAPABILITY = object()


class ExecutionFactsProducerId(str, Enum):
    """Identity of the execution layer that is allowed to produce raw facts."""

    ENV_EXECUTION_FACTS_PRODUCER_V1 = "env_execution_facts_producer_v1"


class LifecycleAuthorityId(str, Enum):
    """Identity of the sole lifecycle finalization authority."""

    LIFECYCLE_AUTHORITY_V1 = "lifecycle_authority_v1"


class TaskLifecycleState(IntEnum):
    """Unique public task-lifecycle state encoding for the event profile."""

    AVAILABLE = 0
    CLAIMED = 1
    NAVIGATING = 2
    ALIGNING = 3
    COMPLETED = 4
    TEAM_INFEASIBLE = 5


class RobotLifecycleState(IntEnum):
    """Unique public robot-lifecycle state encoding for the event profile."""

    EXECUTING = 0
    NEEDS_ASSIGNMENT = 1
    WAITING_FOR_TASK = 2
    UNAVAILABLE = 3


class TerminationReason(IntEnum):
    """Frozen lifecycle termination encoding."""

    NONE = 0
    ALL_TASKS_COMPLETED = 1
    NO_FEASIBLE_TASKS_REMAIN = 2
    TIME_LIMIT = 3


class AssignmentTransitionContractError(RuntimeError):
    """Base error with stable transition-contract context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        env_id: object = None,
        expected_episode_generation: object = None,
        actual_episode_generation: object = None,
        expected_transition_generation: object = None,
        actual_transition_generation: object = None,
        expected_token: object = None,
        actual_token: object = None,
        expected_producer: object = None,
        actual_producer: object = None,
        expected_authority: object = None,
        actual_authority: object = None,
        expected: object = None,
        actual: object = None,
        schema_version: str = ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.env_id = env_id
        self.expected_episode_generation = expected_episode_generation
        self.actual_episode_generation = actual_episode_generation
        self.expected_transition_generation = expected_transition_generation
        self.actual_transition_generation = actual_transition_generation
        self.expected_token = expected_token
        self.actual_token = actual_token
        self.expected_producer = expected_producer
        self.actual_producer = actual_producer
        self.expected_authority = expected_authority
        self.actual_authority = actual_authority
        self.expected = expected
        self.actual = actual
        self.schema_version = schema_version
        super().__init__(
            f"{message}; "
            f"failure_code={failure_code!r}; "
            f"field_name={field_name!r}; "
            f"env_id={_context_value(env_id)!r}; "
            f"expected_episode_generation="
            f"{_context_value(expected_episode_generation)!r}; "
            f"actual_episode_generation="
            f"{_context_value(actual_episode_generation)!r}; "
            f"expected_transition_generation="
            f"{_context_value(expected_transition_generation)!r}; "
            f"actual_transition_generation="
            f"{_context_value(actual_transition_generation)!r}; "
            f"expected_token={_context_value(expected_token)!r}; "
            f"actual_token={_context_value(actual_token)!r}; "
            f"expected_producer={_context_value(expected_producer)!r}; "
            f"actual_producer={_context_value(actual_producer)!r}; "
            f"expected_authority={_context_value(expected_authority)!r}; "
            f"actual_authority={_context_value(actual_authority)!r}; "
            f"expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; "
            f"schema_version={schema_version!r}"
        )


class TransitionSchemaError(AssignmentTransitionContractError):
    """Facts or result fields violate their exact schema."""


class TransitionGenerationError(AssignmentTransitionContractError):
    """Environment, episode, or transition generation does not match."""


class DuplicateTransitionConsumeError(AssignmentTransitionContractError):
    """The same facts or receipt has already been consumed/finalized."""


class TransitionTokenMismatchError(AssignmentTransitionContractError):
    """A generation is bound to a different facts token."""


class ExecutionFactsProducerMismatchError(AssignmentTransitionContractError):
    """The producer stamp or facts producer identity is invalid."""


class LifecycleAuthorityMismatchError(AssignmentTransitionContractError):
    """The lifecycle authority or receipt issuance authority is invalid."""


class FinalizedSnapshotMutationError(AssignmentTransitionContractError):
    """A supported path detected mutation of protected tensor backing."""


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


def _require_exact_string(
    value: object,
    *,
    expected: str,
    field_name: str,
    schema_version: str,
) -> None:
    if type(value) is not str or value != expected:
        raise TransitionSchemaError(
            f"{field_name} does not match the exact transition schema",
            failure_code="schema_version",
            field_name=field_name,
            expected=expected,
            actual=value,
            schema_version=schema_version,
        )


def _require_int64_scalar(
    value: object,
    *,
    field_name: str,
    error_type: type[AssignmentTransitionContractError],
    failure_code: str,
    nonnegative: bool,
    schema_version: str,
) -> int:
    if type(value) is not int:
        raise error_type(
            f"{field_name} must be an exact Python int",
            failure_code=failure_code,
            field_name=field_name,
            expected="int64 scalar",
            actual=type(value),
            schema_version=schema_version,
        )
    if value < _INT64_MIN or value > _INT64_MAX:
        raise error_type(
            f"{field_name} is outside signed int64 range",
            failure_code=failure_code,
            field_name=field_name,
            expected=(_INT64_MIN, _INT64_MAX),
            actual=value,
            schema_version=schema_version,
        )
    if nonnegative and value < 0:
        raise error_type(
            f"{field_name} must be non-negative",
            failure_code=failure_code,
            field_name=field_name,
            expected=">= 0",
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_explicit_device(
    device: object,
    *,
    schema_version: str,
) -> torch.device:
    if type(device) is not torch.device:
        raise TransitionSchemaError(
            "transition tensor construction requires an explicit torch.device",
            failure_code="device",
            field_name="device",
            expected="torch.device",
            actual=type(device),
            schema_version=schema_version,
        )
    return device


@dataclass(frozen=True, slots=True)
class ExecutionFactsProducerStamp:
    """Exact stamp carried by the future environment facts producer."""

    producer_id: ExecutionFactsProducerId
    producer_contract_version: str

    def __post_init__(self) -> None:
        if (
            type(self.producer_id) is not ExecutionFactsProducerId
            or self.producer_id
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
        ):
            raise ExecutionFactsProducerMismatchError(
                "execution facts producer stamp has the wrong producer identity",
                failure_code="producer_stamp",
                expected_producer=(
                    ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
                ),
                actual_producer=self.producer_id,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if (
            type(self.producer_contract_version) is not str
            or self.producer_contract_version
            != EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
        ):
            raise ExecutionFactsProducerMismatchError(
                "execution facts producer stamp has the wrong contract version",
                failure_code="producer_contract_version",
                expected=EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
                actual=self.producer_contract_version,
                expected_producer=self.producer_id,
                actual_producer=self.producer_id,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )


@dataclass(frozen=True, slots=True)
class LifecycleAuthorityStamp:
    """Exact stamp carried by the sole lifecycle authority."""

    authority_id: LifecycleAuthorityId
    authority_contract_version: str

    def __post_init__(self) -> None:
        if (
            type(self.authority_id) is not LifecycleAuthorityId
            or self.authority_id is not LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
        ):
            raise LifecycleAuthorityMismatchError(
                "lifecycle authority stamp has the wrong authority identity",
                failure_code="authority_stamp",
                expected_authority=LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
                actual_authority=self.authority_id,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if (
            type(self.authority_contract_version) is not str
            or self.authority_contract_version
            != LIFECYCLE_AUTHORITY_CONTRACT_VERSION
        ):
            raise LifecycleAuthorityMismatchError(
                "lifecycle authority stamp has the wrong contract version",
                failure_code="authority_contract_version",
                expected=LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
                actual=self.authority_contract_version,
                expected_authority=self.authority_id,
                actual_authority=self.authority_id,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )


@dataclass(frozen=True, slots=True, eq=False)
class _ProtectedTensor:
    """Private clone plus replaceable supported-path integrity metadata."""

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
            raise TransitionSchemaError(
                f"{field_name} must be an exact torch.Tensor",
                failure_code="tensor_type",
                field_name=field_name,
                expected="torch.Tensor",
                actual=type(value),
                schema_version=schema_version,
            )
        if value.dtype is not expected_dtype:
            raise TransitionSchemaError(
                f"{field_name} has the wrong dtype; implicit cast is forbidden",
                failure_code="dtype",
                field_name=field_name,
                expected=expected_dtype,
                actual=value.dtype,
                schema_version=schema_version,
            )
        if value.device != expected_device:
            raise TransitionSchemaError(
                f"{field_name} is on the wrong device; implicit move is forbidden",
                failure_code="device",
                field_name=field_name,
                expected=expected_device,
                actual=value.device,
                schema_version=schema_version,
            )
        if tuple(value.shape) != expected_shape:
            raise TransitionSchemaError(
                f"{field_name} has the wrong shape",
                failure_code="shape",
                field_name=field_name,
                expected=expected_shape,
                actual=tuple(value.shape),
                schema_version=schema_version,
            )
        if value.requires_grad:
            raise TransitionSchemaError(
                f"{field_name} must not require gradients",
                failure_code="requires_grad",
                field_name=field_name,
                expected=False,
                actual=True,
                schema_version=schema_version,
            )
        # An inference-mode clone remains an inference tensor and has no
        # observable version counter.  Preserve value/device/dtype while
        # keeping the protected copy usable by the supported integrity check.
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
            raise FinalizedSnapshotMutationError(
                "protected transition tensor changed after construction",
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


_FACTS_TENSOR_FIELD_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("physical_terminated", ("E",), torch.bool),
    ("physical_truncated", ("E",), torch.bool),
    ("time_limit_reached", ("E",), torch.bool),
    ("bad_transition", ("E",), torch.bool),
    ("completion_signals", ("E", "M", "N"), torch.bool),
    ("terminal_pair_failure_signals", ("E", "M", "N"), torch.bool),
    ("forced_release_signals", ("E", "M", "N"), torch.bool),
    ("robot_unavailable_signals", ("E", "M"), torch.bool),
    ("robot_recovered_signals", ("E", "M"), torch.bool),
    ("coverage_before_reset", ("E", "N"), torch.bool),
    ("task_state_before_transition", ("E", "N"), torch.int64),
    ("robot_state_before_transition", ("E", "M"), torch.int64),
    ("ownership_before_transition", ("E", "N"), torch.int64),
    ("consume_once_token", ("E",), torch.int64),
)

_FACTS_PUBLIC_FIELD_ORDER: tuple[str, ...] = (
    "schema_version",
    "producer_contract_version",
    "producer_id",
    *tuple(name for name, _, _ in _FACTS_TENSOR_FIELD_SPECS),
)

_FACTS_DERIVED_FORBIDDEN_FIELDS = frozenset(
    {
        "TEAM_INFEASIBLE",
        "termination_reason",
        "updated_task_state",
        "updated_robot_state",
        "updated_ownership",
        "completed_tasks",
        "released_tasks",
        "new_failed_pairs",
        "updated_failed_pairs",
        "new_team_infeasible_tasks",
        "lifecycle_events",
        "authority_receipt_id",
    }
)


def _shape_from_symbols(
    symbols: tuple[str, ...],
    *,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
) -> tuple[int, ...]:
    values = {"E": num_envs, "M": num_robots, "N": num_tasks}
    return tuple(values[symbol] for symbol in symbols)


def _first_true_index(mask: torch.Tensor) -> tuple[int, ...] | None:
    indices = torch.nonzero(mask, as_tuple=False)
    if indices.numel() == 0:
        return None
    return tuple(int(value.item()) for value in indices[0])


@dataclass(frozen=True, slots=True, init=False, eq=False)
class ExecutionTransitionFacts:
    """Alias-isolated raw execution facts produced before lifecycle derivation."""

    schema_version: str
    producer_contract_version: str
    producer_id: ExecutionFactsProducerId
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TransitionSchemaError(
            "ExecutionTransitionFacts must be created by from_mapping()",
            failure_code="factory_required",
            expected="ExecutionTransitionFacts.from_mapping",
            actual="direct constructor",
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        producer_stamp: ExecutionFactsProducerStamp,
        device: torch.device,
    ) -> "ExecutionTransitionFacts":
        if not isinstance(values, Mapping):
            raise TransitionSchemaError(
                "execution facts input must be a mapping",
                failure_code="mapping_type",
                expected="Mapping[str, object]",
                actual=type(values),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        non_string_keys = tuple(
            sorted(
                (key for key in values if type(key) is not str),
                key=repr,
            )
        )
        if non_string_keys:
            raise TransitionSchemaError(
                "raw execution facts field names must be exact strings",
                failure_code="unexpected_fields",
                expected="exact str field names",
                actual={"non_string_keys": non_string_keys},
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        actual_keys = set(values)
        expected_keys = set(_FACTS_PUBLIC_FIELD_ORDER)
        unexpected = tuple(sorted(actual_keys - expected_keys, key=repr))
        missing = tuple(
            name for name in _FACTS_PUBLIC_FIELD_ORDER if name not in actual_keys
        )
        if unexpected:
            derived = tuple(
                name for name in unexpected if name in _FACTS_DERIVED_FORBIDDEN_FIELDS
            )
            raise TransitionSchemaError(
                "raw execution facts contain unexpected or derived fields",
                failure_code="unexpected_fields",
                expected=_FACTS_PUBLIC_FIELD_ORDER,
                actual={
                    "unexpected": unexpected,
                    "derived_forbidden": derived,
                },
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if missing:
            raise TransitionSchemaError(
                "raw execution facts are missing required fields",
                failure_code="missing_fields",
                expected=_FACTS_PUBLIC_FIELD_ORDER,
                actual={"missing": missing},
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if type(producer_stamp) is not ExecutionFactsProducerStamp:
            raise ExecutionFactsProducerMismatchError(
                "facts construction requires the canonical producer stamp type",
                failure_code="producer_stamp",
                expected_producer=ExecutionFactsProducerStamp,
                actual_producer=type(producer_stamp),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        _require_exact_string(
            values["schema_version"],
            expected=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            field_name="schema_version",
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )
        if (
            type(values["producer_contract_version"]) is not str
            or values["producer_contract_version"]
            != producer_stamp.producer_contract_version
            or values["producer_contract_version"]
            != EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
        ):
            raise ExecutionFactsProducerMismatchError(
                "facts producer contract version differs from the producer stamp",
                failure_code="producer_contract_version",
                expected=EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
                actual=values["producer_contract_version"],
                expected_producer=producer_stamp.producer_id,
                actual_producer=values.get("producer_id"),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if (
            type(values["producer_id"]) is not ExecutionFactsProducerId
            or values["producer_id"] is not producer_stamp.producer_id
            or values["producer_id"]
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
        ):
            raise ExecutionFactsProducerMismatchError(
                "facts producer identity differs from the producer stamp",
                failure_code="producer_id",
                expected_producer=producer_stamp.producer_id,
                actual_producer=values["producer_id"],
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        explicit_device = _require_explicit_device(
            device,
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )
        env_id_value = values["env_id"]
        if type(env_id_value) is not torch.Tensor:
            raise TransitionSchemaError(
                "env_id must be an exact torch.Tensor",
                failure_code="tensor_type",
                field_name="env_id",
                expected="torch.Tensor",
                actual=type(env_id_value),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if env_id_value.ndim != 1:
            raise TransitionSchemaError(
                "env_id must have rank one",
                failure_code="shape",
                field_name="env_id",
                expected="[E]",
                actual=tuple(env_id_value.shape),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        num_envs = int(env_id_value.shape[0])
        completion_value = values["completion_signals"]
        if type(completion_value) is not torch.Tensor:
            raise TransitionSchemaError(
                "completion_signals must be an exact torch.Tensor",
                failure_code="tensor_type",
                field_name="completion_signals",
                expected="torch.Tensor",
                actual=type(completion_value),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if completion_value.ndim != 3:
            raise TransitionSchemaError(
                "completion_signals must have rank three",
                failure_code="shape",
                field_name="completion_signals",
                expected="[E,M,N]",
                actual=tuple(completion_value.shape),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        completion_shape = tuple(completion_value.shape)
        if completion_shape[0] != num_envs:
            raise TransitionSchemaError(
                "completion_signals batch differs from env_id",
                failure_code="shape",
                field_name="completion_signals",
                expected=(num_envs, "M", "N"),
                actual=completion_shape,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        num_robots = int(completion_shape[1])
        num_tasks = int(completion_shape[2])
        if num_envs <= 0 or num_robots <= 0 or num_tasks <= 0:
            raise TransitionSchemaError(
                "execution facts require E > 0, M > 0, and N > 0",
                failure_code="dimensions",
                expected="E>0,M>0,N>0",
                actual=(num_envs, num_robots, num_tasks),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        protected: dict[str, _ProtectedTensor] = {}
        for name, symbols, dtype in _FACTS_TENSOR_FIELD_SPECS:
            protected[name] = _ProtectedTensor.capture(
                values[name],
                field_name=name,
                expected_shape=_shape_from_symbols(
                    symbols,
                    num_envs=num_envs,
                    num_robots=num_robots,
                    num_tasks=num_tasks,
                ),
                expected_dtype=dtype,
                expected_device=explicit_device,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "schema_version",
            EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )
        object.__setattr__(
            instance,
            "producer_contract_version",
            EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
        )
        object.__setattr__(instance, "producer_id", producer_stamp.producer_id)
        object.__setattr__(instance, "_device", explicit_device)
        object.__setattr__(instance, "_num_envs", num_envs)
        object.__setattr__(instance, "_num_robots", num_robots)
        object.__setattr__(instance, "_num_tasks", num_tasks)
        object.__setattr__(
            instance,
            "_tensor_snapshots",
            MappingProxyType(dict(protected)),
        )
        instance._validate_semantics()
        return instance

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

    def _require_initialized(self) -> None:
        for name in (
            "schema_version",
            "producer_contract_version",
            "producer_id",
            "_device",
            "_num_envs",
            "_num_robots",
            "_num_tasks",
            "_tensor_snapshots",
        ):
            if not hasattr(self, name):
                raise FinalizedSnapshotMutationError(
                    "execution facts object is not initialized by from_mapping",
                    failure_code="uninitialized_snapshot",
                    field_name=name,
                    expected="factory initialized field",
                    actual="missing",
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )

    def validate_integrity(self) -> None:
        self._require_initialized()
        if (
            self.schema_version != EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION
            or self.producer_contract_version
            != EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
            or type(self.producer_id) is not ExecutionFactsProducerId
            or self.producer_id
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
        ):
            raise FinalizedSnapshotMutationError(
                "execution facts metadata changed after construction",
                failure_code="snapshot_metadata",
                expected=(
                    EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                    EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
                    ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1,
                ),
                actual=(
                    self.schema_version,
                    self.producer_contract_version,
                    self.producer_id,
                ),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if type(self._tensor_snapshots) is not MappingProxyType:
            raise FinalizedSnapshotMutationError(
                "execution facts tensor index changed after construction",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected="private read-only mapping",
                actual=type(self._tensor_snapshots),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if tuple(self._tensor_snapshots) != tuple(
            name for name, _, _ in _FACTS_TENSOR_FIELD_SPECS
        ):
            raise FinalizedSnapshotMutationError(
                "execution facts tensor field order changed after construction",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected=tuple(
                    name for name, _, _ in _FACTS_TENSOR_FIELD_SPECS
                ),
                actual=tuple(self._tensor_snapshots),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        for name, snapshot in self._tensor_snapshots.items():
            if type(snapshot) is not _ProtectedTensor:
                raise FinalizedSnapshotMutationError(
                    "execution facts private tensor wrapper changed",
                    failure_code="snapshot_metadata",
                    field_name=name,
                    expected=_ProtectedTensor,
                    actual=type(snapshot),
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            snapshot.validate(
                field_name=name,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )

    def _validated_internal_tensors(self) -> dict[str, torch.Tensor]:
        self.validate_integrity()
        return {
            name: snapshot.internal(
                field_name=name,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
            for name, snapshot in self._tensor_snapshots.items()
        }

    def _validate_semantics(self) -> None:
        tensors = self._validated_internal_tensors()
        env_id = tensors["env_id"]
        if int(torch.unique(env_id).numel()) != self._num_envs:
            raise TransitionSchemaError(
                "env_id rows must be unique",
                failure_code="env_id_unique",
                expected=f"{self._num_envs} unique env IDs",
                actual=tuple(int(value.item()) for value in env_id),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        for name in (
            "episode_generation",
            "transition_generation",
            "consume_once_token",
        ):
            invalid = tensors[name] < 0
            index = _first_true_index(invalid)
            if index is not None:
                row = index[0]
                raise TransitionSchemaError(
                    f"{name} must be non-negative",
                    failure_code="nonnegative",
                    field_name=name,
                    env_id=int(env_id[row].item()),
                    expected=">= 0",
                    actual=int(tensors[name][row].item()),
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
        ownership = tensors["ownership_before_transition"]
        invalid_ownership = (ownership < -1) | (ownership >= self._num_robots)
        index = _first_true_index(invalid_ownership)
        if index is not None:
            row, task = index
            raise TransitionSchemaError(
                "ownership_before_transition is outside -1..M-1",
                failure_code="ownership_range",
                field_name="ownership_before_transition",
                env_id=int(env_id[row].item()),
                expected=(-1, self._num_robots - 1),
                actual={
                    "task": task,
                    "owner": int(ownership[row, task].item()),
                },
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        truncation_required = (
            tensors["time_limit_reached"] | tensors["bad_transition"]
        ) & ~tensors["physical_truncated"]
        index = _first_true_index(truncation_required)
        if index is not None:
            row = index[0]
            raise TransitionSchemaError(
                "time-limit/bad-transition facts require physical_truncated",
                failure_code="truncation_relation",
                field_name="physical_truncated",
                env_id=int(env_id[row].item()),
                expected=True,
                actual=False,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        completion = tensors["completion_signals"]
        completion_cardinality = completion.sum(dim=1) > 1
        index = _first_true_index(completion_cardinality)
        if index is not None:
            row, task = index
            raise TransitionSchemaError(
                "more than one robot completed the same task in one transition",
                failure_code="completion_cardinality",
                field_name="completion_signals",
                env_id=int(env_id[row].item()),
                expected="robot cardinality <= 1",
                actual={
                    "task": task,
                    "robot_count": int(
                        completion[row, :, task].sum().item()
                    ),
                },
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        pair_conflict = completion & tensors["terminal_pair_failure_signals"]
        index = _first_true_index(pair_conflict)
        if index is not None:
            row, robot, task = index
            raise TransitionSchemaError(
                "one pair cannot complete and terminal-fail simultaneously",
                failure_code="pair_signal_conflict",
                env_id=int(env_id[row].item()),
                expected="completion XOR terminal failure",
                actual={"robot": robot, "task": task},
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        robot_ids = torch.arange(
            self._num_robots,
            dtype=torch.int64,
            device=self._device,
        ).view(1, self._num_robots, 1)
        owner_match = ownership.unsqueeze(1) == robot_ids
        owner_rules = (
            ("completion_signals", "completion_owner"),
            ("forced_release_signals", "release_owner"),
            ("terminal_pair_failure_signals", "failure_owner"),
        )
        for field_name, failure_code in owner_rules:
            invalid = tensors[field_name] & ~owner_match
            index = _first_true_index(invalid)
            if index is not None:
                row, robot, task = index
                raise TransitionSchemaError(
                    f"{field_name} must match pre-transition ownership",
                    failure_code=failure_code,
                    field_name=field_name,
                    env_id=int(env_id[row].item()),
                    expected={
                        "robot": robot,
                        "owner": robot,
                        "task": task,
                    },
                    actual={
                        "robot": robot,
                        "owner": int(ownership[row, task].item()),
                        "task": task,
                    },
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
        availability_conflict = (
            tensors["robot_unavailable_signals"]
            & tensors["robot_recovered_signals"]
        )
        index = _first_true_index(availability_conflict)
        if index is not None:
            row, robot = index
            raise TransitionSchemaError(
                "one robot cannot become unavailable and recover simultaneously",
                failure_code="availability_edge_conflict",
                env_id=int(env_id[row].item()),
                expected="unavailable XOR recovered",
                actual={"robot": robot},
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )

    def _clone_tensor(self, name: str) -> torch.Tensor:
        self.validate_integrity()
        return self._tensor_snapshots[name].clone(
            field_name=name,
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )

    def to_mapping(self) -> Mapping[str, object]:
        self.validate_integrity()
        values: dict[str, object] = {
            "schema_version": self.schema_version,
            "producer_contract_version": self.producer_contract_version,
            "producer_id": self.producer_id,
        }
        for name, _, _ in _FACTS_TENSOR_FIELD_SPECS:
            values[name] = self._clone_tensor(name)
        return MappingProxyType(values)


def _facts_tensor_property(name: str) -> property:
    return property(lambda self: self._clone_tensor(name))


for _facts_field_name, _, _ in _FACTS_TENSOR_FIELD_SPECS:
    setattr(
        ExecutionTransitionFacts,
        _facts_field_name,
        _facts_tensor_property(_facts_field_name),
    )


@dataclass(frozen=True, slots=True)
class TransitionConsumeToken:
    """Hashable scalar ledger key; torch tensors are never used as keys."""

    producer_id: ExecutionFactsProducerId
    env_id: int
    episode_generation: int
    transition_generation: int
    consume_once_token: int

    def __post_init__(self) -> None:
        if (
            type(self.producer_id) is not ExecutionFactsProducerId
            or self.producer_id
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
        ):
            raise ExecutionFactsProducerMismatchError(
                "transition token carries the wrong producer identity",
                failure_code="producer_id",
                expected_producer=(
                    ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
                ),
                actual_producer=self.producer_id,
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
        _require_int64_scalar(
            self.env_id,
            field_name="env_id",
            error_type=TransitionTokenMismatchError,
            failure_code="token_env_id",
            nonnegative=False,
            schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
        )
        for field_name in (
            "episode_generation",
            "transition_generation",
            "consume_once_token",
        ):
            _require_int64_scalar(
                getattr(self, field_name),
                field_name=field_name,
                error_type=TransitionTokenMismatchError,
                failure_code="token_value",
                nonnegative=True,
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )


@dataclass(frozen=True, slots=True)
class TransitionGenerationExpectation:
    """Explicit per-env generation expected by the consuming authority."""

    env_id: int
    episode_generation: int
    transition_generation: int

    def __post_init__(self) -> None:
        _require_int64_scalar(
            self.env_id,
            field_name="env_id",
            error_type=TransitionGenerationError,
            failure_code="env_id",
            nonnegative=False,
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )
        _require_int64_scalar(
            self.episode_generation,
            field_name="episode_generation",
            error_type=TransitionGenerationError,
            failure_code="episode",
            nonnegative=True,
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )
        _require_int64_scalar(
            self.transition_generation,
            field_name="transition_generation",
            error_type=TransitionGenerationError,
            failure_code="transition",
            nonnegative=True,
            schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        )


_RECEIPT_TENSOR_FIELD_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("facts_consume_token", ("E",), torch.int64),
    ("authority_receipt_id", ("E",), torch.int64),
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TransitionConsumeReceipt:
    """Immutable ledger-issued receipt batch bound to producer and authority."""

    schema_version: str
    producer_contract_version: str
    facts_producer_id: ExecutionFactsProducerId
    authority_contract_version: str
    authority_id: LifecycleAuthorityId
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)
    _receipt_tokens: tuple[TransitionConsumeToken, ...] = field(repr=False)
    _ledger_capability: object = field(repr=False)
    _issuance_capability: object = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise LifecycleAuthorityMismatchError(
            "TransitionConsumeReceipt can only be issued by a ledger",
            failure_code="ledger_receipt_required",
            expected="TransitionConsumeLedger.consume",
            actual="direct constructor",
            schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
        )

    @classmethod
    def _create(
        cls,
        *,
        producer_stamp: ExecutionFactsProducerStamp,
        authority_stamp: LifecycleAuthorityStamp,
        device: torch.device,
        tensors: Mapping[str, torch.Tensor],
        receipt_tokens: tuple[TransitionConsumeToken, ...],
        ledger_capability: object,
        issuance_capability: object,
    ) -> "TransitionConsumeReceipt":
        num_envs = len(receipt_tokens)
        protected: dict[str, _ProtectedTensor] = {}
        for name, symbols, dtype in _RECEIPT_TENSOR_FIELD_SPECS:
            protected[name] = _ProtectedTensor.capture(
                tensors[name],
                field_name=name,
                expected_shape=_shape_from_symbols(
                    symbols,
                    num_envs=num_envs,
                    num_robots=1,
                    num_tasks=1,
                ),
                expected_dtype=dtype,
                expected_device=device,
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "schema_version",
            TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
        )
        object.__setattr__(
            instance,
            "producer_contract_version",
            producer_stamp.producer_contract_version,
        )
        object.__setattr__(
            instance,
            "facts_producer_id",
            producer_stamp.producer_id,
        )
        object.__setattr__(
            instance,
            "authority_contract_version",
            authority_stamp.authority_contract_version,
        )
        object.__setattr__(instance, "authority_id", authority_stamp.authority_id)
        object.__setattr__(instance, "_device", device)
        object.__setattr__(instance, "_num_envs", num_envs)
        object.__setattr__(
            instance,
            "_tensor_snapshots",
            MappingProxyType(dict(protected)),
        )
        object.__setattr__(instance, "_receipt_tokens", receipt_tokens)
        object.__setattr__(instance, "_ledger_capability", ledger_capability)
        object.__setattr__(instance, "_issuance_capability", issuance_capability)
        instance.validate_integrity()
        return instance

    def _require_initialized(self) -> None:
        for name in (
            "schema_version",
            "producer_contract_version",
            "facts_producer_id",
            "authority_contract_version",
            "authority_id",
            "_device",
            "_num_envs",
            "_tensor_snapshots",
            "_receipt_tokens",
            "_ledger_capability",
            "_issuance_capability",
        ):
            if not hasattr(self, name):
                raise LifecycleAuthorityMismatchError(
                    "receipt is not ledger-issued",
                    failure_code="receipt_uninitialized",
                    field_name=name,
                    expected="ledger-issued receipt",
                    actual="missing field",
                    schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
                )

    def validate_integrity(self) -> None:
        self._require_initialized()
        if (
            self.schema_version != TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION
            or self.producer_contract_version
            != EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
            or type(self.facts_producer_id) is not ExecutionFactsProducerId
            or self.facts_producer_id
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
            or self.authority_contract_version
            != LIFECYCLE_AUTHORITY_CONTRACT_VERSION
            or type(self.authority_id) is not LifecycleAuthorityId
            or self.authority_id is not LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
        ):
            raise FinalizedSnapshotMutationError(
                "receipt metadata changed after issuance",
                failure_code="snapshot_metadata",
                expected=(
                    TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
                    EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
                    ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1,
                    LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
                    LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
                ),
                actual=(
                    self.schema_version,
                    self.producer_contract_version,
                    self.facts_producer_id,
                    self.authority_contract_version,
                    self.authority_id,
                ),
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
        if type(self._tensor_snapshots) is not MappingProxyType:
            raise FinalizedSnapshotMutationError(
                "receipt tensor index changed after issuance",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected="private read-only mapping",
                actual=type(self._tensor_snapshots),
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
        for name, snapshot in self._tensor_snapshots.items():
            if type(snapshot) is not _ProtectedTensor:
                raise FinalizedSnapshotMutationError(
                    "receipt private tensor wrapper changed",
                    failure_code="snapshot_metadata",
                    field_name=name,
                    expected=_ProtectedTensor,
                    actual=type(snapshot),
                    schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
                )
            snapshot.validate(
                field_name=name,
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )

    @property
    def device(self) -> torch.device:
        self.validate_integrity()
        return self._device

    @property
    def num_envs(self) -> int:
        self.validate_integrity()
        return self._num_envs

    def _clone_tensor(self, name: str) -> torch.Tensor:
        self.validate_integrity()
        return self._tensor_snapshots[name].clone(
            field_name=name,
            schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
        )

    def _validated_internal_tensors(self) -> dict[str, torch.Tensor]:
        self.validate_integrity()
        return {
            name: snapshot.internal(
                field_name=name,
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
            for name, snapshot in self._tensor_snapshots.items()
        }

    def to_mapping(self) -> Mapping[str, object]:
        self.validate_integrity()
        values: dict[str, object] = {
            "schema_version": self.schema_version,
            "producer_contract_version": self.producer_contract_version,
            "facts_producer_id": self.facts_producer_id,
            "authority_contract_version": self.authority_contract_version,
            "authority_id": self.authority_id,
        }
        for name, _, _ in _RECEIPT_TENSOR_FIELD_SPECS:
            values[name] = self._clone_tensor(name)
        return MappingProxyType(values)


def _receipt_tensor_property(name: str) -> property:
    return property(lambda self: self._clone_tensor(name))


for _receipt_field_name, _, _ in _RECEIPT_TENSOR_FIELD_SPECS:
    setattr(
        TransitionConsumeReceipt,
        _receipt_field_name,
        _receipt_tensor_property(_receipt_field_name),
    )


@dataclass(frozen=True, slots=True)
class _LedgerState:
    consumed_tokens: frozenset[TransitionConsumeToken]
    generation_tokens: Mapping[tuple[ExecutionFactsProducerId, int, int, int], int]
    last_consumed: Mapping[int, tuple[int, int]]
    receipt_counters: Mapping[int, int]
    issued_capabilities: frozenset[object]
    finalized_capabilities: frozenset[object]


def _empty_ledger_state() -> _LedgerState:
    return _LedgerState(
        consumed_tokens=frozenset(),
        generation_tokens=MappingProxyType({}),
        last_consumed=MappingProxyType({}),
        receipt_counters=MappingProxyType({}),
        issued_capabilities=frozenset(),
        finalized_capabilities=frozenset(),
    )


class TransitionConsumeLedger:
    """Pure logical batch-atomic consume ledger owned by one authority.

    The copy-on-write state swap provides logical atomicity for this API.  It
    does not claim multi-thread transactional or cryptographic guarantees.
    """

    __slots__ = (
        "_authority_stamp",
        "_ledger_capability",
        "_state",
    )

    def __init__(self, *, authority_stamp: LifecycleAuthorityStamp) -> None:
        if type(authority_stamp) is not LifecycleAuthorityStamp:
            raise LifecycleAuthorityMismatchError(
                "ledger requires the canonical lifecycle authority stamp",
                failure_code="authority_stamp",
                expected_authority=LifecycleAuthorityStamp,
                actual_authority=type(authority_stamp),
                schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
            )
        self._authority_stamp = authority_stamp
        self._ledger_capability = object()
        self._state = _empty_ledger_state()

    @property
    def authority_stamp(self) -> LifecycleAuthorityStamp:
        return self._authority_stamp

    def snapshot(self) -> Mapping[str, object]:
        """Return a deterministic immutable primitive audit snapshot."""

        state = self._state
        consumed = tuple(
            sorted(
                (
                    token.producer_id.value,
                    token.env_id,
                    token.episode_generation,
                    token.transition_generation,
                    token.consume_once_token,
                )
                for token in state.consumed_tokens
            )
        )
        generation_tokens = tuple(
            sorted(
                (
                    key[0].value,
                    key[1],
                    key[2],
                    key[3],
                    value,
                )
                for key, value in state.generation_tokens.items()
            )
        )
        return MappingProxyType(
            {
                "consumed_tokens": consumed,
                "generation_tokens": generation_tokens,
                "last_consumed": tuple(sorted(state.last_consumed.items())),
                "receipt_counters": tuple(sorted(state.receipt_counters.items())),
                "issued_receipt_count": len(state.issued_capabilities),
                "finalized_receipt_count": len(state.finalized_capabilities),
            }
        )

    def consume(
        self,
        facts: ExecutionTransitionFacts,
        *,
        producer_stamp: ExecutionFactsProducerStamp,
        expected_generations: tuple[TransitionGenerationExpectation, ...],
    ) -> TransitionConsumeReceipt:
        if type(facts) is not ExecutionTransitionFacts:
            raise TransitionSchemaError(
                "ledger consume requires canonical ExecutionTransitionFacts",
                failure_code="facts_type",
                expected=ExecutionTransitionFacts,
                actual=type(facts),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        facts.validate_integrity()
        facts._validate_semantics()
        if type(producer_stamp) is not ExecutionFactsProducerStamp:
            raise ExecutionFactsProducerMismatchError(
                "ledger consume requires the canonical producer stamp",
                failure_code="producer_stamp",
                expected_producer=ExecutionFactsProducerStamp,
                actual_producer=type(producer_stamp),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if (
            facts.producer_id is not producer_stamp.producer_id
            or facts.producer_contract_version
            != producer_stamp.producer_contract_version
        ):
            raise ExecutionFactsProducerMismatchError(
                "facts producer differs from consume producer stamp",
                failure_code="producer_id",
                expected_producer=producer_stamp.producer_id,
                actual_producer=facts.producer_id,
                expected=producer_stamp.producer_contract_version,
                actual=facts.producer_contract_version,
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        if type(expected_generations) is not tuple:
            raise TransitionGenerationError(
                "expected_generations must be an exact immutable tuple",
                failure_code="expectation_type",
                expected="tuple[TransitionGenerationExpectation, ...]",
                actual=type(expected_generations),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        expectations: dict[int, TransitionGenerationExpectation] = {}
        for expectation in expected_generations:
            if type(expectation) is not TransitionGenerationExpectation:
                raise TransitionGenerationError(
                    "expected_generations contains a noncanonical entry",
                    failure_code="expectation_type",
                    expected=TransitionGenerationExpectation,
                    actual=type(expectation),
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            if expectation.env_id in expectations:
                raise TransitionGenerationError(
                    "expected_generations contains duplicate env_id",
                    failure_code="env_id",
                    env_id=expectation.env_id,
                    expected="unique expectation env_id",
                    actual="duplicate",
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            expectations[expectation.env_id] = expectation
        tensors = facts._validated_internal_tensors()
        fact_rows: list[tuple[int, int, int, int]] = []
        for row in range(facts.num_envs):
            fact_rows.append(
                (
                    int(tensors["env_id"][row].item()),
                    int(tensors["episode_generation"][row].item()),
                    int(tensors["transition_generation"][row].item()),
                    int(tensors["consume_once_token"][row].item()),
                )
            )
        fact_env_ids = {row[0] for row in fact_rows}
        expected_env_ids = set(expectations)
        if fact_env_ids != expected_env_ids:
            raise TransitionGenerationError(
                "facts env_id set differs from generation expectations",
                failure_code="env_id",
                expected=tuple(sorted(expected_env_ids)),
                actual=tuple(sorted(fact_env_ids)),
                schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
            )
        state = self._state
        prepared_tokens: list[TransitionConsumeToken] = []
        for env_id, episode, transition, token_value in fact_rows:
            expectation = expectations[env_id]
            if episode != expectation.episode_generation:
                raise TransitionGenerationError(
                    "facts episode generation differs from expectation",
                    failure_code="episode",
                    env_id=env_id,
                    expected_episode_generation=expectation.episode_generation,
                    actual_episode_generation=episode,
                    expected_transition_generation=(
                        expectation.transition_generation
                    ),
                    actual_transition_generation=transition,
                    actual_token=token_value,
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            generation_key = (
                producer_stamp.producer_id,
                env_id,
                episode,
                transition,
            )
            if generation_key in state.generation_tokens:
                consumed_token = state.generation_tokens[generation_key]
                if consumed_token == token_value:
                    raise DuplicateTransitionConsumeError(
                        "execution facts generation/token was already consumed",
                        failure_code="duplicate",
                        env_id=env_id,
                        expected_episode_generation=episode,
                        actual_episode_generation=episode,
                        expected_transition_generation=transition,
                        actual_transition_generation=transition,
                        expected_token=consumed_token,
                        actual_token=token_value,
                        expected_producer=producer_stamp.producer_id,
                        actual_producer=facts.producer_id,
                        schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                    )
                raise TransitionTokenMismatchError(
                    "an already consumed generation is bound to another token",
                    failure_code="generation_token",
                    env_id=env_id,
                    expected_episode_generation=episode,
                    actual_episode_generation=episode,
                    expected_transition_generation=transition,
                    actual_transition_generation=transition,
                    expected_token=consumed_token,
                    actual_token=token_value,
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            if transition < expectation.transition_generation:
                raise TransitionGenerationError(
                    "facts transition generation is stale",
                    failure_code="stale",
                    env_id=env_id,
                    expected_episode_generation=expectation.episode_generation,
                    actual_episode_generation=episode,
                    expected_transition_generation=(
                        expectation.transition_generation
                    ),
                    actual_transition_generation=transition,
                    actual_token=token_value,
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            if transition > expectation.transition_generation:
                raise TransitionGenerationError(
                    "facts transition generation is in the future",
                    failure_code="future",
                    env_id=env_id,
                    expected_episode_generation=expectation.episode_generation,
                    actual_episode_generation=episode,
                    expected_transition_generation=(
                        expectation.transition_generation
                    ),
                    actual_transition_generation=transition,
                    actual_token=token_value,
                    schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                )
            last = state.last_consumed.get(env_id)
            if last is not None:
                last_episode, last_transition = last
                if episode < last_episode or transition <= last_transition:
                    raise TransitionGenerationError(
                        "facts generation violates per-env monotonic history",
                        failure_code="stale",
                        env_id=env_id,
                        expected_episode_generation=max(
                            expectation.episode_generation,
                            last_episode,
                        ),
                        actual_episode_generation=episode,
                        expected_transition_generation=last_transition + 1,
                        actual_transition_generation=transition,
                        actual_token=token_value,
                        schema_version=EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
                    )
            prepared_tokens.append(
                TransitionConsumeToken(
                    producer_id=producer_stamp.producer_id,
                    env_id=env_id,
                    episode_generation=episode,
                    transition_generation=transition,
                    consume_once_token=token_value,
                )
            )
        receipt_ids: list[int] = []
        new_counters = dict(state.receipt_counters)
        for token in prepared_tokens:
            candidate = int(new_counters.get(token.env_id, 0)) + 1
            if candidate == token.consume_once_token:
                candidate += 1
            if candidate > _INT64_MAX:
                raise TransitionTokenMismatchError(
                    "authority receipt ID exhausted signed int64 range",
                    failure_code="receipt_id_overflow",
                    env_id=token.env_id,
                    expected=f"<= {_INT64_MAX}",
                    actual=candidate,
                    actual_token=token.consume_once_token,
                    schema_version=TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION,
                )
            new_counters[token.env_id] = candidate
            receipt_ids.append(candidate)
        receipt_id_tensor = torch.tensor(
            receipt_ids,
            dtype=torch.int64,
            device=facts.device,
        )
        issuance_capability = object()
        receipt = TransitionConsumeReceipt._create(
            producer_stamp=producer_stamp,
            authority_stamp=self._authority_stamp,
            device=facts.device,
            tensors={
                "env_id": tensors["env_id"],
                "episode_generation": tensors["episode_generation"],
                "transition_generation": tensors["transition_generation"],
                "facts_consume_token": tensors["consume_once_token"],
                "authority_receipt_id": receipt_id_tensor,
            },
            receipt_tokens=tuple(prepared_tokens),
            ledger_capability=self._ledger_capability,
            issuance_capability=issuance_capability,
        )
        new_consumed = set(state.consumed_tokens)
        new_generation_tokens = dict(state.generation_tokens)
        new_last = dict(state.last_consumed)
        for token in prepared_tokens:
            new_consumed.add(token)
            generation_key = (
                token.producer_id,
                token.env_id,
                token.episode_generation,
                token.transition_generation,
            )
            new_generation_tokens[generation_key] = token.consume_once_token
            new_last[token.env_id] = (
                token.episode_generation,
                token.transition_generation,
            )
        self._state = _LedgerState(
            consumed_tokens=frozenset(new_consumed),
            generation_tokens=MappingProxyType(new_generation_tokens),
            last_consumed=MappingProxyType(new_last),
            receipt_counters=MappingProxyType(new_counters),
            issued_capabilities=(
                state.issued_capabilities | frozenset({issuance_capability})
            ),
            finalized_capabilities=state.finalized_capabilities,
        )
        return receipt

    def _validate_issued_receipt(
        self,
        receipt: object,
        *,
        require_unfinalized: bool,
    ) -> TransitionConsumeReceipt:
        if type(receipt) is not TransitionConsumeReceipt:
            raise LifecycleAuthorityMismatchError(
                "result finalization requires a canonical ledger receipt",
                failure_code="receipt_type",
                expected_authority=TransitionConsumeReceipt,
                actual_authority=type(receipt),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        receipt.validate_integrity()
        if receipt._ledger_capability is not self._ledger_capability:
            raise LifecycleAuthorityMismatchError(
                "receipt was issued by another ledger",
                failure_code="receipt_issuer",
                expected_authority="factory-bound ledger",
                actual_authority="different ledger capability",
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if receipt._issuance_capability not in self._state.issued_capabilities:
            raise LifecycleAuthorityMismatchError(
                "receipt issuance is not registered by this ledger",
                failure_code="receipt_issuer",
                expected_authority="registered ledger issuance",
                actual_authority="unknown issuance",
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if (
            receipt.authority_id is not self._authority_stamp.authority_id
            or receipt.authority_contract_version
            != self._authority_stamp.authority_contract_version
        ):
            raise LifecycleAuthorityMismatchError(
                "receipt authority differs from the ledger authority",
                failure_code="receipt_authority",
                expected_authority=self._authority_stamp.authority_id,
                actual_authority=receipt.authority_id,
                expected=self._authority_stamp.authority_contract_version,
                actual=receipt.authority_contract_version,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if (
            require_unfinalized
            and receipt._issuance_capability
            in self._state.finalized_capabilities
        ):
            raise DuplicateTransitionConsumeError(
                "receipt has already finalized a lifecycle result",
                failure_code="duplicate_finalization",
                expected_authority=self._authority_stamp.authority_id,
                actual_authority=receipt.authority_id,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        return receipt

    def _claim_finalization(self, receipt: TransitionConsumeReceipt) -> None:
        validated = self._validate_issued_receipt(
            receipt,
            require_unfinalized=True,
        )
        state = self._state
        self._state = _LedgerState(
            consumed_tokens=state.consumed_tokens,
            generation_tokens=state.generation_tokens,
            last_consumed=state.last_consumed,
            receipt_counters=state.receipt_counters,
            issued_capabilities=state.issued_capabilities,
            finalized_capabilities=(
                state.finalized_capabilities
                | frozenset({validated._issuance_capability})
            ),
        )


_RESULT_TENSOR_FIELD_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("completed_tasks", ("E", "N"), torch.bool),
    ("released_tasks", ("E", "N"), torch.bool),
    ("new_failed_pairs", ("E", "M", "N"), torch.bool),
    ("updated_failed_pairs", ("E", "M", "N"), torch.bool),
    ("new_team_infeasible_tasks", ("E", "N"), torch.bool),
    ("updated_task_state", ("E", "N"), torch.int64),
    ("updated_robot_state", ("E", "M"), torch.int64),
    ("updated_ownership", ("E", "N"), torch.int64),
    ("termination_reason", ("E",), torch.int64),
    ("facts_consume_token", ("E",), torch.int64),
    ("authority_receipt_id", ("E",), torch.int64),
)

_RESULT_PUBLIC_FIELD_ORDER: tuple[str, ...] = (
    "schema_version",
    "authority_contract_version",
    "facts_producer_id",
    "authority_id",
    *tuple(name for name, _, _ in _RESULT_TENSOR_FIELD_SPECS[:12]),
    "lifecycle_events",
    *tuple(name for name, _, _ in _RESULT_TENSOR_FIELD_SPECS[12:]),
)


@dataclass(frozen=True, slots=True)
class _FinalizationSeal:
    factory_capability: object = field(repr=False)
    ledger_capability: object = field(repr=False)
    issuance_capability: object = field(repr=False)
    authority_id: LifecycleAuthorityId
    authority_contract_version: str

    def __post_init__(self) -> None:
        if (
            self.factory_capability is not _RESULT_FACTORY_CAPABILITY
            or self.ledger_capability is None
            or self.issuance_capability is None
            or self.authority_id
            is not LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
            or self.authority_contract_version
            != LIFECYCLE_AUTHORITY_CONTRACT_VERSION
        ):
            raise LifecycleAuthorityMismatchError(
                "lifecycle result finalization seal lacks factory authority",
                failure_code="finalization_seal",
                expected_authority=LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
                actual_authority=self.authority_id,
                expected=LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
                actual=self.authority_contract_version,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )


def _validate_result_lifecycle_events(
    lifecycle_events: object,
    *,
    authority_id: LifecycleAuthorityId,
    env_id: torch.Tensor,
    episode_generation: torch.Tensor,
    transition_generation: torch.Tensor,
    facts_consume_token: torch.Tensor,
) -> tuple[LifecycleEventRecord, ...]:
    """Late-bind A3 event types without creating a transition/event cycle."""

    if type(lifecycle_events) is not tuple:
        raise TransitionSchemaError(
            "lifecycle_events must be an exact immutable tuple",
            failure_code="lifecycle_events_type",
            field_name="lifecycle_events",
            expected="tuple[LifecycleEventRecord, ...]",
            actual=type(lifecycle_events),
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
    if not lifecycle_events:
        return ()

    # Import is intentionally late: assignment_event_contract imports the
    # canonical authority enum from this module, while this module has no
    # top-level event-contract dependency.
    from .assignment_event_contract import (
        AssignmentEventContractError,
        validate_lifecycle_event_records,
    )

    try:
        validated = validate_lifecycle_event_records(lifecycle_events)
    except AssignmentEventContractError as exc:
        raise TransitionSchemaError(
            "lifecycle_events contains an invalid or misplaced record",
            failure_code="lifecycle_events_invalid",
            field_name="lifecycle_events",
            expected="canonical finalized LifecycleEventRecord tuple",
            actual={
                "event_failure_code": exc.failure_code,
                "record_system": exc.record_system,
            },
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        ) from exc

    env_rows = {
        int(env_id[row].item()): row for row in range(int(env_id.shape[0]))
    }
    order_keys: list[tuple[int, int]] = []
    for event in validated:
        row = env_rows.get(event.env_id)
        if row is None:
            raise TransitionGenerationError(
                "lifecycle event env_id is absent from the result batch",
                failure_code="lifecycle_event_env",
                field_name="lifecycle_events.env_id",
                env_id=event.env_id,
                expected=tuple(sorted(env_rows)),
                actual=event.env_id,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        expected_episode = int(episode_generation[row].item())
        expected_transition = int(transition_generation[row].item())
        expected_token = int(facts_consume_token[row].item())
        if event.episode_generation != expected_episode:
            raise TransitionGenerationError(
                "lifecycle event episode generation differs from its result row",
                failure_code="lifecycle_event_episode",
                field_name="lifecycle_events.episode_generation",
                env_id=event.env_id,
                expected_episode_generation=expected_episode,
                actual_episode_generation=event.episode_generation,
                expected_transition_generation=expected_transition,
                actual_transition_generation=event.transition_generation,
                expected_token=expected_token,
                actual_token=event.facts_consume_token,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if event.transition_generation != expected_transition:
            raise TransitionGenerationError(
                "lifecycle event transition generation differs from its result row",
                failure_code="lifecycle_event_transition",
                field_name="lifecycle_events.transition_generation",
                env_id=event.env_id,
                expected_episode_generation=expected_episode,
                actual_episode_generation=event.episode_generation,
                expected_transition_generation=expected_transition,
                actual_transition_generation=event.transition_generation,
                expected_token=expected_token,
                actual_token=event.facts_consume_token,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if event.facts_consume_token != expected_token:
            raise TransitionTokenMismatchError(
                "lifecycle event facts token differs from its result row",
                failure_code="lifecycle_event_token",
                field_name="lifecycle_events.facts_consume_token",
                env_id=event.env_id,
                expected_episode_generation=expected_episode,
                actual_episode_generation=event.episode_generation,
                expected_transition_generation=expected_transition,
                actual_transition_generation=event.transition_generation,
                expected_token=expected_token,
                actual_token=event.facts_consume_token,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if event.authority_id is not authority_id:
            raise LifecycleAuthorityMismatchError(
                "lifecycle event authority differs from result authority",
                failure_code="lifecycle_event_authority",
                field_name="lifecycle_events.authority_id",
                env_id=event.env_id,
                expected_authority=authority_id,
                actual_authority=event.authority_id,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        order_keys.append((event.env_id, event.ordinal))
    if tuple(order_keys) != tuple(sorted(order_keys)):
        raise TransitionGenerationError(
            "result lifecycle events are not ordered by (env_id, ordinal)",
            failure_code="lifecycle_event_order",
            field_name="lifecycle_events",
            expected=tuple(sorted(order_keys)),
            actual=tuple(order_keys),
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
    return validated


@dataclass(frozen=True, slots=True, init=False, eq=False)
class LifecycleTransitionResult:
    """Factory-finalized immutable lifecycle result for one facts batch."""

    schema_version: str
    authority_contract_version: str
    facts_producer_id: ExecutionFactsProducerId
    authority_id: LifecycleAuthorityId
    lifecycle_events: tuple[LifecycleEventRecord, ...]
    _device: torch.device = field(repr=False)
    _num_envs: int = field(repr=False)
    _num_robots: int = field(repr=False)
    _num_tasks: int = field(repr=False)
    _tensor_snapshots: Mapping[str, _ProtectedTensor] = field(repr=False)
    _finalization_seal: _FinalizationSeal = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise LifecycleAuthorityMismatchError(
            "LifecycleTransitionResult requires authority factory finalization",
            failure_code="factory_required",
            expected="LifecycleTransitionResultFactory.finalize",
            actual="direct constructor",
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )

    @classmethod
    def _create_finalized(
        cls,
        *,
        facts: ExecutionTransitionFacts,
        receipt: TransitionConsumeReceipt,
        authority_stamp: LifecycleAuthorityStamp,
        tensors: Mapping[str, torch.Tensor],
        lifecycle_events: tuple[LifecycleEventRecord, ...],
        finalization_seal: _FinalizationSeal,
    ) -> "LifecycleTransitionResult":
        protected: dict[str, _ProtectedTensor] = {}
        for name, symbols, dtype in _RESULT_TENSOR_FIELD_SPECS:
            protected[name] = _ProtectedTensor.capture(
                tensors[name],
                field_name=name,
                expected_shape=_shape_from_symbols(
                    symbols,
                    num_envs=facts.num_envs,
                    num_robots=facts.num_robots,
                    num_tasks=facts.num_tasks,
                ),
                expected_dtype=dtype,
                expected_device=facts.device,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "schema_version",
            LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        object.__setattr__(
            instance,
            "authority_contract_version",
            authority_stamp.authority_contract_version,
        )
        object.__setattr__(
            instance,
            "facts_producer_id",
            receipt.facts_producer_id,
        )
        object.__setattr__(instance, "authority_id", authority_stamp.authority_id)
        object.__setattr__(instance, "lifecycle_events", lifecycle_events)
        object.__setattr__(instance, "_device", facts.device)
        object.__setattr__(instance, "_num_envs", facts.num_envs)
        object.__setattr__(instance, "_num_robots", facts.num_robots)
        object.__setattr__(instance, "_num_tasks", facts.num_tasks)
        object.__setattr__(
            instance,
            "_tensor_snapshots",
            MappingProxyType(dict(protected)),
        )
        object.__setattr__(instance, "_finalization_seal", finalization_seal)
        instance.validate_finalized()
        return instance

    def _require_initialized(self) -> None:
        for name in (
            "schema_version",
            "authority_contract_version",
            "facts_producer_id",
            "authority_id",
            "lifecycle_events",
            "_device",
            "_num_envs",
            "_num_robots",
            "_num_tasks",
            "_tensor_snapshots",
            "_finalization_seal",
        ):
            if not hasattr(self, name):
                raise LifecycleAuthorityMismatchError(
                    "lifecycle result is not factory-finalized",
                    failure_code="result_uninitialized",
                    field_name=name,
                    expected="factory-finalized result",
                    actual="missing field",
                    schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
                )

    def validate_integrity(self) -> None:
        self._require_initialized()
        if (
            self.schema_version != LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION
            or self.authority_contract_version
            != LIFECYCLE_AUTHORITY_CONTRACT_VERSION
            or type(self.facts_producer_id) is not ExecutionFactsProducerId
            or self.facts_producer_id
            is not ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
            or type(self.authority_id) is not LifecycleAuthorityId
            or self.authority_id is not LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
            or type(self.lifecycle_events) is not tuple
        ):
            raise FinalizedSnapshotMutationError(
                "lifecycle result metadata changed after finalization",
                failure_code="snapshot_metadata",
                expected=(
                    LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
                    LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
                    ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1,
                    LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
                    "tuple[LifecycleEventRecord, ...]",
                ),
                actual=(
                    self.schema_version,
                    self.authority_contract_version,
                    self.facts_producer_id,
                    self.authority_id,
                    self.lifecycle_events,
                ),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if type(self._tensor_snapshots) is not MappingProxyType:
            raise FinalizedSnapshotMutationError(
                "lifecycle result tensor index changed after finalization",
                failure_code="snapshot_metadata",
                field_name="tensor_fields",
                expected="private read-only mapping",
                actual=type(self._tensor_snapshots),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        for name, snapshot in self._tensor_snapshots.items():
            if type(snapshot) is not _ProtectedTensor:
                raise FinalizedSnapshotMutationError(
                    "lifecycle result private tensor wrapper changed",
                    failure_code="snapshot_metadata",
                    field_name=name,
                    expected=_ProtectedTensor,
                    actual=type(snapshot),
                    schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
                )
            snapshot.validate(
                field_name=name,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        event_binding_tensors = {
            name: self._tensor_snapshots[name].internal(
                field_name=name,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
            for name in (
                "env_id",
                "episode_generation",
                "transition_generation",
                "facts_consume_token",
            )
        }
        _validate_result_lifecycle_events(
            self.lifecycle_events,
            authority_id=self.authority_id,
            env_id=event_binding_tensors["env_id"],
            episode_generation=event_binding_tensors["episode_generation"],
            transition_generation=event_binding_tensors[
                "transition_generation"
            ],
            facts_consume_token=event_binding_tensors["facts_consume_token"],
        )

    def validate_finalized(self) -> None:
        self.validate_integrity()
        seal = self._finalization_seal
        if (
            type(seal) is not _FinalizationSeal
            or seal.factory_capability is not _RESULT_FACTORY_CAPABILITY
            or seal.ledger_capability is None
            or seal.issuance_capability is None
            or seal.authority_id is not self.authority_id
            or seal.authority_contract_version
            != self.authority_contract_version
        ):
            raise LifecycleAuthorityMismatchError(
                "lifecycle result has no valid authority finalization seal",
                failure_code="finalization_seal",
                expected_authority=self.authority_id,
                actual_authority=getattr(seal, "authority_id", None),
                expected=self.authority_contract_version,
                actual=getattr(seal, "authority_contract_version", None),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )

    @property
    def device(self) -> torch.device:
        self.validate_finalized()
        return self._device

    @property
    def num_envs(self) -> int:
        self.validate_finalized()
        return self._num_envs

    @property
    def num_robots(self) -> int:
        self.validate_finalized()
        return self._num_robots

    @property
    def num_tasks(self) -> int:
        self.validate_finalized()
        return self._num_tasks

    def _clone_tensor(self, name: str) -> torch.Tensor:
        self.validate_finalized()
        return self._tensor_snapshots[name].clone(
            field_name=name,
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )

    def to_mapping(self) -> Mapping[str, object]:
        self.validate_finalized()
        values: dict[str, object] = {
            "schema_version": self.schema_version,
            "authority_contract_version": self.authority_contract_version,
            "facts_producer_id": self.facts_producer_id,
            "authority_id": self.authority_id,
        }
        for name, _, _ in _RESULT_TENSOR_FIELD_SPECS[:12]:
            values[name] = self._clone_tensor(name)
        values["lifecycle_events"] = self.lifecycle_events
        for name, _, _ in _RESULT_TENSOR_FIELD_SPECS[12:]:
            values[name] = self._clone_tensor(name)
        return MappingProxyType(values)


def _result_tensor_property(name: str) -> property:
    return property(lambda self: self._clone_tensor(name))


for _result_field_name, _, _ in _RESULT_TENSOR_FIELD_SPECS:
    setattr(
        LifecycleTransitionResult,
        _result_field_name,
        _result_tensor_property(_result_field_name),
    )


def _capture_result_input(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    facts: ExecutionTransitionFacts,
) -> _ProtectedTensor:
    return _ProtectedTensor.capture(
        value,
        field_name=field_name,
        expected_shape=shape,
        expected_dtype=dtype,
        expected_device=facts.device,
        schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
    )


def _require_equal_tensor(
    left: torch.Tensor,
    right: torch.Tensor,
    *,
    error_type: type[AssignmentTransitionContractError],
    failure_code: str,
    field_name: str,
    context_kind: str,
    source_env_ids: torch.Tensor,
    schema_version: str,
) -> None:
    if not torch.equal(left, right):
        index = _first_true_index(left != right)
        if index is None:
            raise TransitionSchemaError(
                "unequal transition tensors have no observable mismatch",
                failure_code="internal_mismatch_context",
                field_name=field_name,
                expected="at least one unequal scalar",
                actual="no unequal scalar",
                schema_version=schema_version,
            )
        row = index[0]
        expected_value = int(right[row].item())
        actual_value = int(left[row].item())
        env_id = int(source_env_ids[row].item())
        context: dict[str, object] = {}
        if context_kind == "episode":
            context["expected_episode_generation"] = expected_value
            context["actual_episode_generation"] = actual_value
        elif context_kind == "transition":
            context["expected_transition_generation"] = expected_value
            context["actual_transition_generation"] = actual_value
        elif context_kind == "token":
            context["expected_token"] = expected_value
            context["actual_token"] = actual_value
        elif context_kind != "env_id":
            raise TransitionSchemaError(
                "unsupported transition mismatch context",
                failure_code="internal_mismatch_context",
                field_name=field_name,
                env_id=env_id,
                expected=("env_id", "episode", "transition", "token"),
                actual=context_kind,
                schema_version=schema_version,
            )
        raise error_type(
            f"{field_name} differs from its authoritative source",
            failure_code=failure_code,
            field_name=field_name,
            env_id=env_id,
            expected=expected_value,
            actual=actual_value,
            schema_version=schema_version,
            **context,
        )


class LifecycleTransitionResultFactory:
    """Only public authority path that can produce a validated result."""

    __slots__ = ("_ledger", "_authority_stamp")

    def __init__(
        self,
        *,
        ledger: TransitionConsumeLedger,
        authority_stamp: LifecycleAuthorityStamp,
    ) -> None:
        if type(ledger) is not TransitionConsumeLedger:
            raise LifecycleAuthorityMismatchError(
                "result factory requires a canonical transition ledger",
                failure_code="ledger_type",
                expected_authority=TransitionConsumeLedger,
                actual_authority=type(ledger),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if type(authority_stamp) is not LifecycleAuthorityStamp:
            raise LifecycleAuthorityMismatchError(
                "result factory requires the canonical lifecycle authority stamp",
                failure_code="authority_stamp",
                expected_authority=LifecycleAuthorityStamp,
                actual_authority=type(authority_stamp),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if authority_stamp != ledger.authority_stamp:
            raise LifecycleAuthorityMismatchError(
                "result factory authority differs from ledger authority",
                failure_code="authority_stamp",
                expected_authority=ledger.authority_stamp.authority_id,
                actual_authority=authority_stamp.authority_id,
                expected=ledger.authority_stamp.authority_contract_version,
                actual=authority_stamp.authority_contract_version,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        self._ledger = ledger
        self._authority_stamp = authority_stamp

    def finalize(
        self,
        *,
        facts: ExecutionTransitionFacts,
        receipt: TransitionConsumeReceipt | None,
        completed_tasks: torch.Tensor,
        released_tasks: torch.Tensor,
        new_failed_pairs: torch.Tensor,
        prior_failed_pairs: torch.Tensor,
        updated_failed_pairs: torch.Tensor,
        new_team_infeasible_tasks: torch.Tensor,
        updated_task_state: torch.Tensor,
        updated_robot_state: torch.Tensor,
        updated_ownership: torch.Tensor,
        termination_reason: torch.Tensor,
        task_completed_state_encoding: int,
        lifecycle_events: tuple[LifecycleEventRecord, ...] = (),
    ) -> LifecycleTransitionResult:
        if type(facts) is not ExecutionTransitionFacts:
            raise TransitionSchemaError(
                "result factory requires canonical ExecutionTransitionFacts",
                failure_code="facts_type",
                expected=ExecutionTransitionFacts,
                actual=type(facts),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        facts.validate_integrity()
        facts._validate_semantics()
        validated_receipt = self._ledger._validate_issued_receipt(
            receipt,
            require_unfinalized=True,
        )
        if (
            validated_receipt.authority_id
            is not self._authority_stamp.authority_id
            or validated_receipt.authority_contract_version
            != self._authority_stamp.authority_contract_version
        ):
            raise LifecycleAuthorityMismatchError(
                "receipt authority differs from factory authority",
                failure_code="receipt_authority",
                expected_authority=self._authority_stamp.authority_id,
                actual_authority=validated_receipt.authority_id,
                expected=self._authority_stamp.authority_contract_version,
                actual=validated_receipt.authority_contract_version,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        if (
            validated_receipt.facts_producer_id is not facts.producer_id
            or validated_receipt.producer_contract_version
            != facts.producer_contract_version
        ):
            raise ExecutionFactsProducerMismatchError(
                "receipt producer differs from source facts producer",
                failure_code="receipt_producer",
                expected_producer=facts.producer_id,
                actual_producer=validated_receipt.facts_producer_id,
                expected=facts.producer_contract_version,
                actual=validated_receipt.producer_contract_version,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        facts_tensors = facts._validated_internal_tensors()
        receipt_tensors = validated_receipt._validated_internal_tensors()
        _require_equal_tensor(
            receipt_tensors["env_id"],
            facts_tensors["env_id"],
            error_type=TransitionGenerationError,
            failure_code="env_id",
            field_name="receipt.env_id",
            context_kind="env_id",
            source_env_ids=facts_tensors["env_id"],
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        _require_equal_tensor(
            receipt_tensors["episode_generation"],
            facts_tensors["episode_generation"],
            error_type=TransitionGenerationError,
            failure_code="episode",
            field_name="receipt.episode_generation",
            context_kind="episode",
            source_env_ids=facts_tensors["env_id"],
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        _require_equal_tensor(
            receipt_tensors["transition_generation"],
            facts_tensors["transition_generation"],
            error_type=TransitionGenerationError,
            failure_code="transition",
            field_name="receipt.transition_generation",
            context_kind="transition",
            source_env_ids=facts_tensors["env_id"],
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        _require_equal_tensor(
            receipt_tensors["facts_consume_token"],
            facts_tensors["consume_once_token"],
            error_type=TransitionTokenMismatchError,
            failure_code="result_token",
            field_name="receipt.facts_consume_token",
            context_kind="token",
            source_env_ids=facts_tensors["env_id"],
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        validated_lifecycle_events = _validate_result_lifecycle_events(
            lifecycle_events,
            authority_id=self._authority_stamp.authority_id,
            env_id=facts_tensors["env_id"],
            episode_generation=facts_tensors["episode_generation"],
            transition_generation=facts_tensors["transition_generation"],
            facts_consume_token=facts_tensors["consume_once_token"],
        )
        completed_encoding = _require_int64_scalar(
            task_completed_state_encoding,
            field_name="task_completed_state_encoding",
            error_type=TransitionSchemaError,
            failure_code="completed_state_encoding",
            nonnegative=False,
            schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
        )
        dimensions = {
            "E": facts.num_envs,
            "M": facts.num_robots,
            "N": facts.num_tasks,
        }
        input_specs: tuple[
            tuple[str, object, tuple[str, ...], torch.dtype], ...
        ] = (
            ("completed_tasks", completed_tasks, ("E", "N"), torch.bool),
            ("released_tasks", released_tasks, ("E", "N"), torch.bool),
            (
                "new_failed_pairs",
                new_failed_pairs,
                ("E", "M", "N"),
                torch.bool,
            ),
            (
                "prior_failed_pairs",
                prior_failed_pairs,
                ("E", "M", "N"),
                torch.bool,
            ),
            (
                "updated_failed_pairs",
                updated_failed_pairs,
                ("E", "M", "N"),
                torch.bool,
            ),
            (
                "new_team_infeasible_tasks",
                new_team_infeasible_tasks,
                ("E", "N"),
                torch.bool,
            ),
            (
                "updated_task_state",
                updated_task_state,
                ("E", "N"),
                torch.int64,
            ),
            (
                "updated_robot_state",
                updated_robot_state,
                ("E", "M"),
                torch.int64,
            ),
            (
                "updated_ownership",
                updated_ownership,
                ("E", "N"),
                torch.int64,
            ),
            (
                "termination_reason",
                termination_reason,
                ("E",),
                torch.int64,
            ),
        )
        protected_inputs: dict[str, _ProtectedTensor] = {}
        for name, value, symbols, dtype in input_specs:
            protected_inputs[name] = _capture_result_input(
                value,
                field_name=name,
                shape=tuple(dimensions[symbol] for symbol in symbols),
                dtype=dtype,
                facts=facts,
            )
        derived = {
            name: snapshot.internal(
                field_name=name,
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
            for name, snapshot in protected_inputs.items()
        }
        expected_completed = facts_tensors["completion_signals"].any(dim=1)
        if not torch.equal(derived["completed_tasks"], expected_completed):
            raise TransitionSchemaError(
                "completed_tasks must equal completion_signals.any(dim=1)",
                failure_code="completed_derivation",
                field_name="completed_tasks",
                expected="completion_signals.any(dim=1)",
                actual="tensor values differ",
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        completed = derived["completed_tasks"]
        completed_owned = completed & (derived["updated_ownership"] != -1)
        index = _first_true_index(completed_owned)
        if index is not None:
            row, task = index
            raise TransitionSchemaError(
                "completed task must have ownership -1",
                failure_code="completed_task_ownership",
                field_name="updated_ownership",
                env_id=int(facts_tensors["env_id"][row].item()),
                expected=-1,
                actual={
                    "task": task,
                    "owner": int(
                        derived["updated_ownership"][row, task].item()
                    ),
                },
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        completed_state_invalid = completed & (
            derived["updated_task_state"] != completed_encoding
        )
        index = _first_true_index(completed_state_invalid)
        if index is not None:
            row, task = index
            raise TransitionSchemaError(
                "completed task state differs from caller canonical encoding",
                failure_code="completed_task_state",
                field_name="updated_task_state",
                env_id=int(facts_tensors["env_id"][row].item()),
                expected=completed_encoding,
                actual={
                    "task": task,
                    "state": int(
                        derived["updated_task_state"][row, task].item()
                    ),
                },
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        failed_pair_conflict = (
            derived["new_failed_pairs"] & derived["prior_failed_pairs"]
        )
        index = _first_true_index(failed_pair_conflict)
        if index is not None:
            row, robot, task = index
            raise TransitionSchemaError(
                "new_failed_pairs cannot repeat a prior failed pair",
                failure_code="new_failed_pair_conflict",
                field_name="new_failed_pairs",
                env_id=int(facts_tensors["env_id"][row].item()),
                expected="new & prior == false",
                actual={"robot": robot, "task": task},
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        expected_updated_failed = (
            derived["prior_failed_pairs"] | derived["new_failed_pairs"]
        )
        if not torch.equal(
            derived["updated_failed_pairs"],
            expected_updated_failed,
        ):
            raise TransitionSchemaError(
                "updated_failed_pairs must equal prior | new",
                failure_code="updated_failed_pairs_consistency",
                field_name="updated_failed_pairs",
                expected="prior_failed_pairs | new_failed_pairs",
                actual="tensor values differ",
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        invalid_ownership = (derived["updated_ownership"] < -1) | (
            derived["updated_ownership"] >= facts.num_robots
        )
        index = _first_true_index(invalid_ownership)
        if index is not None:
            row, task = index
            raise TransitionSchemaError(
                "updated_ownership is outside -1..M-1",
                failure_code="ownership_range",
                field_name="updated_ownership",
                env_id=int(facts_tensors["env_id"][row].item()),
                expected=(-1, facts.num_robots - 1),
                actual={
                    "task": task,
                    "owner": int(
                        derived["updated_ownership"][row, task].item()
                    ),
                },
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        valid_reasons = tuple(int(reason) for reason in TerminationReason)
        invalid_reason = torch.ones_like(
            derived["termination_reason"],
            dtype=torch.bool,
        )
        for reason in valid_reasons:
            invalid_reason &= derived["termination_reason"] != reason
        index = _first_true_index(invalid_reason)
        if index is not None:
            row = index[0]
            raise TransitionSchemaError(
                "termination_reason is outside the frozen enum domain",
                failure_code="termination_reason",
                field_name="termination_reason",
                env_id=int(facts_tensors["env_id"][row].item()),
                expected=valid_reasons,
                actual=int(derived["termination_reason"][row].item()),
                schema_version=LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
            )
        result_tensors: dict[str, torch.Tensor] = {
            "env_id": facts_tensors["env_id"],
            "episode_generation": facts_tensors["episode_generation"],
            "transition_generation": facts_tensors["transition_generation"],
            "completed_tasks": derived["completed_tasks"],
            "released_tasks": derived["released_tasks"],
            "new_failed_pairs": derived["new_failed_pairs"],
            "updated_failed_pairs": derived["updated_failed_pairs"],
            "new_team_infeasible_tasks": derived[
                "new_team_infeasible_tasks"
            ],
            "updated_task_state": derived["updated_task_state"],
            "updated_robot_state": derived["updated_robot_state"],
            "updated_ownership": derived["updated_ownership"],
            "termination_reason": derived["termination_reason"],
            "facts_consume_token": facts_tensors["consume_once_token"],
            "authority_receipt_id": receipt_tensors[
                "authority_receipt_id"
            ],
        }
        seal = _FinalizationSeal(
            factory_capability=_RESULT_FACTORY_CAPABILITY,
            ledger_capability=self._ledger._ledger_capability,
            issuance_capability=validated_receipt._issuance_capability,
            authority_id=self._authority_stamp.authority_id,
            authority_contract_version=(
                self._authority_stamp.authority_contract_version
            ),
        )
        result = LifecycleTransitionResult._create_finalized(
            facts=facts,
            receipt=validated_receipt,
            authority_stamp=self._authority_stamp,
            tensors=result_tensors,
            lifecycle_events=validated_lifecycle_events,
            finalization_seal=seal,
        )
        self._ledger._claim_finalization(validated_receipt)
        return result


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if isinstance(value, tuple):
        return tuple(_deep_readonly(item) for item in value)
    if isinstance(value, list):
        return tuple(_deep_readonly(item) for item in value)
    return value


def _field_descriptor(
    name: str,
    shape: tuple[str, ...] | str,
    dtype: str,
) -> Mapping[str, object]:
    return {
        "name": name,
        "shape": shape,
        "dtype": dtype,
    }


_FACTS_SCHEMA_DESCRIPTOR = {
    "schema_version": EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
    "producer_contract_version": EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
    "producer_id": (
        ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1.value
    ),
    "fields": (
        _field_descriptor("schema_version", "scalar", "str"),
        _field_descriptor("producer_contract_version", "scalar", "str"),
        _field_descriptor(
            "producer_id",
            "scalar",
            "ExecutionFactsProducerId",
        ),
        *tuple(
            _field_descriptor(name, symbols, str(dtype))
            for name, symbols, dtype in _FACTS_TENSOR_FIELD_SPECS
        ),
    ),
}

_RESULT_SCHEMA_DESCRIPTOR = {
    "schema_version": LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
    "authority_contract_version": LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
    "facts_producer_id": (
        ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1.value
    ),
    "authority_id": LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1.value,
    "fields": (
        _field_descriptor("schema_version", "scalar", "str"),
        _field_descriptor("authority_contract_version", "scalar", "str"),
        _field_descriptor(
            "facts_producer_id",
            "scalar",
            "ExecutionFactsProducerId",
        ),
        _field_descriptor("authority_id", "scalar", "LifecycleAuthorityId"),
        *tuple(
            _field_descriptor(name, symbols, str(dtype))
            for name, symbols, dtype in _RESULT_TENSOR_FIELD_SPECS[:12]
        ),
        _field_descriptor(
            "lifecycle_events",
            "tuple",
            "LifecycleEventRecord",
        ),
        *tuple(
            _field_descriptor(name, symbols, str(dtype))
            for name, symbols, dtype in _RESULT_TENSOR_FIELD_SPECS[12:]
        ),
    ),
}

_FAILURE_TERMINATION_SEMANTICS = {
    "projection_version": FAILURE_TERMINATION_SEMANTICS_VERSION,
    "task_state_enum_order": tuple(
        (member.name, int(member)) for member in TaskLifecycleState
    ),
    "robot_state_enum_order": tuple(
        (member.name, int(member)) for member in RobotLifecycleState
    ),
    "transient_event_exclusion": (
        "ROBOT_RECOVERED_is_a_transient_lifecycle_event_not_a_"
        "RobotLifecycleState"
    ),
    "termination_reason_order": tuple(
        (member.name, int(member)) for member in TerminationReason
    ),
    "failed_pair_source": (
        "ExecutionTransitionFacts.terminal_pair_failure_signals_and_"
        "episode_cumulative_prior_failed_pairs"
    ),
    "new_failed_pairs_equation": (
        "new_failed_pairs=terminal_pair_failure_signals AND NOT "
        "prior_failed_pairs"
    ),
    "updated_failed_pairs_equation": (
        "updated_failed_pairs=prior_failed_pairs OR new_failed_pairs"
    ),
    "failed_pair_episode_reset_rule": (
        "updated_failed_pairs_is_episode_cumulative_and_clears_only_on_"
        "episode_reset"
    ),
    "team_infeasible_equation": (
        "TEAM_INFEASIBLE[j]=event_updated_task_state[j]!=COMPLETED AND "
        "all_i(updated_failed_pairs[i,j])"
    ),
    "new_team_infeasible_equation": (
        "new_team_infeasible_tasks[j]=NOT prior_team_infeasible[j] AND "
        "event_updated_task_state[j]!=COMPLETED AND "
        "all_i(updated_failed_pairs[i,j])"
    ),
    "path_invalid_non_equivalence": (
        "all_nominal_paths_invalid_does_not_imply_TEAM_INFEASIBLE"
    ),
    "terminal_task_ownership_release_rule": (
        "COMPLETED_or_TEAM_INFEASIBLE_task_ownership_is_NO_OWNER_"
        "before_a0"
    ),
    "event_updated_baseline_order": (
        "finalize_execution_and_lifecycle_facts",
        "write_completion_release_failed_pair_and_robot_availability",
        "derive_TEAM_INFEASIBLE_after_updated_failed_pairs",
        "release_terminal_task_ownership",
        "finalize_updated_task_robot_and_ownership_state_as_a0",
        "derive_termination_before_assignment",
    ),
    "termination_priority": (
        TerminationReason.ALL_TASKS_COMPLETED.name,
        TerminationReason.NO_FEASIBLE_TASKS_REMAIN.name,
        TerminationReason.TIME_LIMIT.name,
        TerminationReason.NONE.name,
    ),
    "physical_terminal_mapping_boundary": (
        "all_tasks_completed=>ALL_TASKS_COMPLETED",
        "all_tasks_completed_or_team_infeasible=>"
        "NO_FEASIBLE_TASKS_REMAIN",
        "time_limit_reached=>TIME_LIMIT",
    ),
    "bad_transition_boundary": (
        "bad_transition_is_a_bootstrap_transport_fact_not_a_"
        "TerminationReason"
    ),
    "unmappable_physical_terminal_rule": (
        "physical_terminated_or_truncated_with_final_reason_NONE_or_"
        "unsupported_non_time_limit_boundary=>typed_fail_closed_with_"
        "DVM_zero_no_proposal_no_commit"
    ),
    "terminal_assignment_rule": (
        "target_noop_available_action_masks_all_false",
        "semantic_legal_action_count=0",
        "forced_policy_action_id=-1",
        "no_actor_sampling_action_log_probability_proposal_"
        "forced_nondecision_resolver_or_component_row",
        "finalized_pre_reset_critic_shared_sidecar_only",
    ),
    "episode_generation_rule": (
        "increment_once_per_episode_reset_and_rebuild_all_episode_"
        "lifecycle_MRTA_retry_and_termination_state"
    ),
    "transition_generation_rule": (
        "per_env_process_lifetime_monotonic_increment_once_per_"
        "finalized_physical_transition_and_never_reset_on_episode_reset"
    ),
    "assignment_tick_generation_rule": (
        "per_env_process_lifetime_monotonic_increment_once_per_"
        "canonical_merged_assignment_tick;overlapping_same_transition_"
        "triggers_share_one_increment;no_tick_no_increment"
    ),
}


_PUBLIC_SCHEMA_DESCRIPTOR = _deep_readonly(
    {
        "contract_version": ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION,
        "facts": _FACTS_SCHEMA_DESCRIPTOR,
        "result": _RESULT_SCHEMA_DESCRIPTOR,
        "pair_attribution_contract_version": (
            PAIR_ATTRIBUTION_CONTRACT_VERSION
        ),
        "observable_immutability_contract_version": (
            OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION
        ),
        "observable_immutability_guarantees": (
            "frozen metadata",
            "no public writable tensor alias",
            "supported-path mutation detection",
        ),
        "failure_termination_semantics": _FAILURE_TERMINATION_SEMANTICS,
    }
)


def get_assignment_lifecycle_transition_schema_descriptor(
) -> Mapping[str, object]:
    """Return the deeply read-only, deterministic public A2 descriptor."""

    return _PUBLIC_SCHEMA_DESCRIPTOR  # type: ignore[return-value]


__all__ = [
    "ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION",
    "AssignmentTransitionContractError",
    "CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE",
    "DuplicateTransitionConsumeError",
    "EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION",
    "EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION",
    "ExecutionFactsProducerId",
    "ExecutionFactsProducerMismatchError",
    "ExecutionFactsProducerStamp",
    "ExecutionTransitionFacts",
    "FAILURE_TERMINATION_SEMANTICS_VERSION",
    "FinalizedSnapshotMutationError",
    "LIFECYCLE_AUTHORITY_CONTRACT_VERSION",
    "LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION",
    "LifecycleAuthorityId",
    "LifecycleAuthorityMismatchError",
    "LifecycleAuthorityStamp",
    "LifecycleTransitionResult",
    "LifecycleTransitionResultFactory",
    "OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION",
    "PAIR_ATTRIBUTION_CONTRACT_VERSION",
    "RobotLifecycleState",
    "TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION",
    "TaskLifecycleState",
    "TerminationReason",
    "TransitionConsumeLedger",
    "TransitionConsumeReceipt",
    "TransitionConsumeToken",
    "TransitionGenerationError",
    "TransitionGenerationExpectation",
    "TransitionSchemaError",
    "TransitionTokenMismatchError",
    "get_assignment_lifecycle_transition_schema_descriptor",
]
