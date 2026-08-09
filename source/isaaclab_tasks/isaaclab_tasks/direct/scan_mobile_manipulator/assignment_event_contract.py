"""Pure typed records for event-gated assignment boundaries.

Phase A3 defines three deliberately disjoint record systems:

* finalized pre-policy lifecycle events;
* scheduled assignment opportunities; and
* post-resolver diagnostics.

This module validates immutable records and container placement only.  It does
not produce lifecycle facts, schedule retries, construct local sets, invoke a
resolver, mutate ownership, or create a diagnostic sink.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_contract"
)
ASSIGNMENT_EVENT_CONTRACT_SOURCE_PURPOSE = (
    "pure typed assignment event, opportunity, and resolver diagnostic contract"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment event contract source must "
        "fail before declaring identity-bearing types; "
        f"expected module key={CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose={ASSIGNMENT_EVENT_CONTRACT_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from .assignment_lifecycle_transition_contract import LifecycleAuthorityId


ASSIGNMENT_EVENT_CONTRACT_VERSION = "assignment_event_contract_v2"
LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION = "lifecycle_event_record_v1"
ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION = (
    "assignment_opportunity_record_v1"
)
RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION = "resolver_diagnostic_record_v1"
SCHEDULED_ASSIGNMENT_OPPORTUNITY_SEMANTICS_VERSION = (
    "event_gated_scheduled_assignment_opportunity_semantics_v1"
)

_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


class LifecycleEventType(str, Enum):
    """Exact finalized pre-policy lifecycle-event order."""

    TASK_COMPLETED = "task_completed"
    TASK_RELEASED = "task_released"
    TERMINAL_PAIR_FAILURE_RECORDED = "terminal_pair_failure_recorded"
    TASK_BECAME_TEAM_INFEASIBLE = "task_became_team_infeasible"
    ROBOT_BECAME_UNAVAILABLE = "robot_became_unavailable"
    ROBOT_RECOVERED = "robot_recovered"
    ROBOT_NEEDS_ASSIGNMENT = "robot_needs_assignment"


class LifecycleCausalSource(str, Enum):
    """Source category for lifecycle-authority derivation."""

    EXECUTION_FACTS = "execution_facts"
    LIFECYCLE_DERIVATION = "lifecycle_derivation"


class AssignmentOpportunityType(str, Enum):
    """Exact scheduled-opportunity vocabulary."""

    ASSIGNMENT_RETRY_DUE = "assignment_retry_due"


class AssignmentOpportunityProducerId(str, Enum):
    """Identity of the future retry scheduler."""

    RETRY_SCHEDULER_V1 = "retry_scheduler_v1"


class ResolverDiagnosticType(str, Enum):
    """Exact post-resolver diagnostic vocabulary."""

    COMPONENT_ACCEPTED = "component_accepted"
    COMPONENT_REJECTED = "component_rejected"
    OWNERSHIP_TRANSFER_COMMITTED = "ownership_transfer_committed"


class ResolverDiagnosticProducerId(str, Enum):
    """Identity of the future resolver diagnostic producer."""

    RESOLVER_DIAGNOSTIC_PRODUCER_V1 = (
        "resolver_diagnostic_producer_v1"
    )


class AssignmentEventContractError(RuntimeError):
    """Base typed error for record schema and placement failures."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
        record_system: str | None = None,
        schema_version: str = ASSIGNMENT_EVENT_CONTRACT_VERSION,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        self.record_system = record_system
        self.schema_version = schema_version
        super().__init__(
            f"{message}; "
            f"failure_code={failure_code!r}; "
            f"field_name={field_name!r}; "
            f"expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; "
            f"record_system={record_system!r}; "
            f"schema_version={schema_version!r}"
        )


class EventSchemaError(AssignmentEventContractError):
    """A typed record or payload violates its exact schema."""


class EventPlacementError(AssignmentEventContractError):
    """A canonical record was inserted into the wrong container."""


class EventGenerationError(AssignmentEventContractError):
    """A record ID or generation binding is invalid."""


class EventAuthorityMismatchError(AssignmentEventContractError):
    """A lifecycle event carries the wrong canonical authority."""


def _context_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return value


def _require_exact_string(
    value: object,
    *,
    field_name: str,
    schema_version: str,
    expected: str | None = None,
) -> str:
    if type(value) is not str:
        raise EventSchemaError(
            f"{field_name} must be an exact Python string",
            failure_code="string_type",
            field_name=field_name,
            expected="str",
            actual=type(value),
            schema_version=schema_version,
        )
    if expected is not None:
        if value != expected:
            raise EventSchemaError(
                f"{field_name} differs from the exact schema value",
                failure_code="schema_version",
                field_name=field_name,
                expected=expected,
                actual=value,
                schema_version=schema_version,
            )
    elif not value or value.strip() != value:
        raise EventSchemaError(
            f"{field_name} must be a non-empty canonical string",
            failure_code="string_value",
            field_name=field_name,
            expected="non-empty string without surrounding whitespace",
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_int64(
    value: object,
    *,
    field_name: str,
    schema_version: str,
    minimum: int = _INT64_MIN,
) -> int:
    if type(value) is not int:
        raise EventSchemaError(
            f"{field_name} must be an exact Python int",
            failure_code="integer_type",
            field_name=field_name,
            expected="signed int64",
            actual=type(value),
            schema_version=schema_version,
        )
    if value < minimum or value > _INT64_MAX:
        raise EventSchemaError(
            f"{field_name} is outside its signed int64 domain",
            failure_code="integer_range",
            field_name=field_name,
            expected=(minimum, _INT64_MAX),
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_exact_bool(
    value: object,
    *,
    field_name: str,
    expected: bool | None,
    schema_version: str,
) -> bool:
    if type(value) is not bool or (
        expected is not None and value is not expected
    ):
        raise EventSchemaError(
            f"{field_name} has the wrong exact boolean value",
            failure_code="boolean_value",
            field_name=field_name,
            expected=("bool" if expected is None else expected),
            actual=value,
            schema_version=schema_version,
        )
    return value


def _require_exact_id_tuple(
    value: object,
    *,
    field_name: str,
    length: int,
    schema_version: str,
    minimums: tuple[int, ...],
) -> tuple[int, ...]:
    if type(value) is not tuple or len(value) != length:
        raise EventGenerationError(
            f"{field_name} must be an exact immutable tuple",
            failure_code="record_id",
            field_name=field_name,
            expected=f"tuple[{length}]",
            actual=value,
            schema_version=schema_version,
        )
    checked = tuple(
        _require_int64(
            item,
            field_name=f"{field_name}[{index}]",
            schema_version=schema_version,
            minimum=minimums[index],
        )
        for index, item in enumerate(value)
    )
    return checked


def _require_global_id_tuple(
    value: object,
    *,
    field_name: str,
    schema_version: str,
    allow_empty: bool,
) -> tuple[int, ...]:
    if type(value) is not tuple:
        raise EventSchemaError(
            f"{field_name} must be an exact immutable tuple",
            failure_code="id_tuple_type",
            field_name=field_name,
            expected="tuple[int, ...]",
            actual=type(value),
            schema_version=schema_version,
        )
    if not allow_empty and not value:
        raise EventSchemaError(
            f"{field_name} must contain at least one global ID",
            failure_code="id_tuple_empty",
            field_name=field_name,
            expected="non-empty tuple",
            actual=value,
            schema_version=schema_version,
        )
    checked = tuple(
        _require_int64(
            item,
            field_name=f"{field_name}[{index}]",
            schema_version=schema_version,
            minimum=0,
        )
        for index, item in enumerate(value)
    )
    if tuple(sorted(checked)) != checked or len(set(checked)) != len(checked):
        raise EventSchemaError(
            f"{field_name} must contain unique IDs in canonical order",
            failure_code="id_tuple_order",
            field_name=field_name,
            expected="strictly increasing unique IDs",
            actual=checked,
            schema_version=schema_version,
        )
    return checked


def _payload_mapping(
    fields: tuple[tuple[str, object], ...],
) -> Mapping[str, object]:
    return MappingProxyType(dict(fields))


@dataclass(frozen=True, slots=True)
class TaskLifecycleEventPayload:
    """Typed task-state lifecycle payload."""

    task_id: int
    previous_task_state: int
    updated_task_state: int
    cause_robot_id: int

    def __post_init__(self) -> None:
        for field_name, minimum in (
            ("task_id", 0),
            ("previous_task_state", _INT64_MIN),
            ("updated_task_state", _INT64_MIN),
            ("cause_robot_id", -1),
        ):
            _require_int64(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                minimum=minimum,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("task_id", self.task_id),
                ("previous_task_state", self.previous_task_state),
                ("updated_task_state", self.updated_task_state),
                ("cause_robot_id", self.cause_robot_id),
            )
        )


@dataclass(frozen=True, slots=True)
class RobotLifecycleEventPayload:
    """Typed robot-state lifecycle payload."""

    robot_id: int
    previous_robot_state: int
    updated_robot_state: int

    def __post_init__(self) -> None:
        for field_name, minimum in (
            ("robot_id", 0),
            ("previous_robot_state", _INT64_MIN),
            ("updated_robot_state", _INT64_MIN),
        ):
            _require_int64(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                minimum=minimum,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("robot_id", self.robot_id),
                ("previous_robot_state", self.previous_robot_state),
                ("updated_robot_state", self.updated_robot_state),
            )
        )


@dataclass(frozen=True, slots=True)
class PairFailureEventPayload:
    """Typed robot-task structural-failure payload."""

    robot_id: int
    task_id: int
    newly_recorded: bool

    def __post_init__(self) -> None:
        _require_int64(
            self.robot_id,
            field_name="robot_id",
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            minimum=0,
        )
        _require_int64(
            self.task_id,
            field_name="task_id",
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            minimum=0,
        )
        _require_exact_bool(
            self.newly_recorded,
            field_name="newly_recorded",
            expected=None,
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("robot_id", self.robot_id),
                ("task_id", self.task_id),
                ("newly_recorded", self.newly_recorded),
            )
        )


_TASK_EVENT_TYPES = frozenset(
    {
        LifecycleEventType.TASK_COMPLETED,
        LifecycleEventType.TASK_RELEASED,
        LifecycleEventType.TASK_BECAME_TEAM_INFEASIBLE,
    }
)
_ROBOT_EVENT_TYPES = frozenset(
    {
        LifecycleEventType.ROBOT_BECAME_UNAVAILABLE,
        LifecycleEventType.ROBOT_RECOVERED,
        LifecycleEventType.ROBOT_NEEDS_ASSIGNMENT,
    }
)


@dataclass(frozen=True, slots=True)
class LifecycleEventRecord:
    """One finalized lifecycle-authority event."""

    schema_version: str
    event_id: tuple[int, int, int, int]
    causal_source: LifecycleCausalSource
    event_type: LifecycleEventType
    env_id: int
    episode_generation: int
    transition_generation: int
    ordinal: int
    robot_id: int
    task_id: int
    trigger_eligible: bool
    facts_consume_token: int
    authority_id: LifecycleAuthorityId
    payload: (
        TaskLifecycleEventPayload
        | RobotLifecycleEventPayload
        | PairFailureEventPayload
    )

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _require_exact_string(
            self.schema_version,
            field_name="schema_version",
            expected=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )
        if type(self.causal_source) is not LifecycleCausalSource:
            raise EventSchemaError(
                "causal_source must use the canonical lifecycle source enum",
                failure_code="enum_type",
                field_name="causal_source",
                expected=LifecycleCausalSource,
                actual=type(self.causal_source),
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )
        if type(self.event_type) is not LifecycleEventType:
            raise EventSchemaError(
                "event_type must use the canonical lifecycle event enum",
                failure_code="enum_type",
                field_name="event_type",
                expected=LifecycleEventType,
                actual=type(self.event_type),
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )
        for field_name, minimum in (
            ("env_id", _INT64_MIN),
            ("episode_generation", 0),
            ("transition_generation", 0),
            ("ordinal", 0),
            ("robot_id", -1),
            ("task_id", -1),
            ("facts_consume_token", 0),
        ):
            _require_int64(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                minimum=minimum,
            )
        expected_event_id = (
            self.env_id,
            self.episode_generation,
            self.transition_generation,
            self.ordinal,
        )
        actual_event_id = _require_exact_id_tuple(
            self.event_id,
            field_name="event_id",
            length=4,
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            minimums=(_INT64_MIN, 0, 0, 0),
        )
        if actual_event_id != expected_event_id:
            raise EventGenerationError(
                "event_id differs from the event generation fields",
                failure_code="record_id_binding",
                field_name="event_id",
                expected=expected_event_id,
                actual=actual_event_id,
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )
        _require_exact_bool(
            self.trigger_eligible,
            field_name="trigger_eligible",
            expected=True,
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )
        if (
            type(self.authority_id) is not LifecycleAuthorityId
            or self.authority_id
            is not LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
        ):
            raise EventAuthorityMismatchError(
                "lifecycle event carries the wrong authority identity",
                failure_code="authority_id",
                field_name="authority_id",
                expected=LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
                actual=self.authority_id,
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )
        if self.event_type in _TASK_EVENT_TYPES:
            if type(self.payload) is not TaskLifecycleEventPayload:
                self._raise_payload_type(TaskLifecycleEventPayload)
            if (
                self.task_id != self.payload.task_id
                or self.robot_id != self.payload.cause_robot_id
            ):
                self._raise_payload_id_binding(
                    expected=(
                        self.payload.cause_robot_id,
                        self.payload.task_id,
                    )
                )
        elif self.event_type in _ROBOT_EVENT_TYPES:
            if type(self.payload) is not RobotLifecycleEventPayload:
                self._raise_payload_type(RobotLifecycleEventPayload)
            if self.robot_id != self.payload.robot_id or self.task_id != -1:
                self._raise_payload_id_binding(
                    expected=(self.payload.robot_id, -1)
                )
        elif (
            self.event_type
            is LifecycleEventType.TERMINAL_PAIR_FAILURE_RECORDED
        ):
            if type(self.payload) is not PairFailureEventPayload:
                self._raise_payload_type(PairFailureEventPayload)
            if (
                self.robot_id != self.payload.robot_id
                or self.task_id != self.payload.task_id
            ):
                self._raise_payload_id_binding(
                    expected=(self.payload.robot_id, self.payload.task_id)
                )
            if self.payload.newly_recorded is not True:
                raise EventSchemaError(
                    "terminal pair failure event requires a newly recorded pair",
                    failure_code="pair_failure_not_new",
                    field_name="payload.newly_recorded",
                    expected=True,
                    actual=self.payload.newly_recorded,
                    record_system="lifecycle_event",
                    schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                )
        else:
            raise EventSchemaError(
                "event_type is outside the frozen lifecycle event domain",
                failure_code="enum_value",
                field_name="event_type",
                expected=tuple(LifecycleEventType),
                actual=self.event_type,
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )

    def _raise_payload_type(self, expected: type[object]) -> None:
        raise EventSchemaError(
            "lifecycle event payload type does not match event_type",
            failure_code="payload_type",
            field_name="payload",
            expected=expected,
            actual=type(self.payload),
            record_system="lifecycle_event",
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )

    def _raise_payload_id_binding(
        self,
        *,
        expected: tuple[int, int],
    ) -> None:
        raise EventSchemaError(
            "lifecycle event global IDs differ from its typed payload",
            failure_code="payload_id_binding",
            field_name="robot_id/task_id",
            expected=expected,
            actual=(self.robot_id, self.task_id),
            record_system="lifecycle_event",
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )

    def to_mapping(self) -> Mapping[str, object]:
        self.validate()
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "event_id": self.event_id,
                "causal_source": self.causal_source.value,
                "event_type": self.event_type.value,
                "env_id": self.env_id,
                "episode_generation": self.episode_generation,
                "transition_generation": self.transition_generation,
                "ordinal": self.ordinal,
                "robot_id": self.robot_id,
                "task_id": self.task_id,
                "trigger_eligible": self.trigger_eligible,
                "facts_consume_token": self.facts_consume_token,
                "authority_id": self.authority_id.value,
                "payload": self.payload.to_mapping(),
            }
        )


@dataclass(frozen=True, slots=True)
class AssignmentOpportunityRecord:
    """One independently scheduled retry opportunity."""

    schema_version: str
    opportunity_id: tuple[int, int, int, int, int]
    opportunity_type: AssignmentOpportunityType
    producer_id: AssignmentOpportunityProducerId
    env_id: int
    episode_generation: int
    transition_generation: int
    assignment_tick_generation: int
    ordinal: int
    robot_id: int
    retry_generation: int
    trigger_eligible: bool

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _require_exact_string(
            self.schema_version,
            field_name="schema_version",
            expected=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
        )
        if (
            type(self.opportunity_type) is not AssignmentOpportunityType
            or self.opportunity_type
            is not AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE
        ):
            raise EventSchemaError(
                "opportunity_type differs from the frozen retry type",
                failure_code="enum_type",
                field_name="opportunity_type",
                expected=AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE,
                actual=self.opportunity_type,
                record_system="assignment_opportunity",
                schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            )
        if (
            type(self.producer_id) is not AssignmentOpportunityProducerId
            or self.producer_id
            is not AssignmentOpportunityProducerId.RETRY_SCHEDULER_V1
        ):
            raise EventAuthorityMismatchError(
                "assignment opportunity carries the wrong producer identity",
                failure_code="producer_id",
                field_name="producer_id",
                expected=AssignmentOpportunityProducerId.RETRY_SCHEDULER_V1,
                actual=self.producer_id,
                record_system="assignment_opportunity",
                schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            )
        for field_name, minimum in (
            ("env_id", _INT64_MIN),
            ("episode_generation", 0),
            ("transition_generation", 0),
            ("assignment_tick_generation", 0),
            ("ordinal", 0),
            ("robot_id", 0),
            ("retry_generation", 0),
        ):
            _require_int64(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
                minimum=minimum,
            )
        expected_id = (
            self.env_id,
            self.episode_generation,
            self.transition_generation,
            self.assignment_tick_generation,
            self.ordinal,
        )
        actual_id = _require_exact_id_tuple(
            self.opportunity_id,
            field_name="opportunity_id",
            length=5,
            schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            minimums=(_INT64_MIN, 0, 0, 0, 0),
        )
        if actual_id != expected_id:
            raise EventGenerationError(
                "opportunity_id differs from its generation fields",
                failure_code="record_id_binding",
                field_name="opportunity_id",
                expected=expected_id,
                actual=actual_id,
                record_system="assignment_opportunity",
                schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            )
        _require_exact_bool(
            self.trigger_eligible,
            field_name="trigger_eligible",
            expected=True,
            schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
        )

    def to_mapping(self) -> Mapping[str, object]:
        self.validate()
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "opportunity_id": self.opportunity_id,
                "opportunity_type": self.opportunity_type.value,
                "producer_id": self.producer_id.value,
                "env_id": self.env_id,
                "episode_generation": self.episode_generation,
                "transition_generation": self.transition_generation,
                "assignment_tick_generation": (
                    self.assignment_tick_generation
                ),
                "ordinal": self.ordinal,
                "robot_id": self.robot_id,
                "retry_generation": self.retry_generation,
                "trigger_eligible": self.trigger_eligible,
            }
        )


@dataclass(frozen=True, slots=True)
class ResolverComponentAcceptedPayload:
    """Typed payload for a whole-component acceptance diagnostic."""

    member_robot_ids: tuple[int, ...]
    member_task_ids: tuple[int, ...]
    transfer_count: int

    def __post_init__(self) -> None:
        _require_global_id_tuple(
            self.member_robot_ids,
            field_name="member_robot_ids",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            allow_empty=False,
        )
        _require_global_id_tuple(
            self.member_task_ids,
            field_name="member_task_ids",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            allow_empty=False,
        )
        _require_int64(
            self.transfer_count,
            field_name="transfer_count",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            minimum=0,
        )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("member_robot_ids", self.member_robot_ids),
                ("member_task_ids", self.member_task_ids),
                ("transfer_count", self.transfer_count),
            )
        )


@dataclass(frozen=True, slots=True)
class ResolverComponentRejectedPayload:
    """Typed payload for a whole-component rejection diagnostic."""

    rejection_reason: str
    policy_caused: bool
    penalty_eligible: bool
    member_robot_ids: tuple[int, ...]
    member_task_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        _require_exact_string(
            self.rejection_reason,
            field_name="rejection_reason",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        _require_exact_bool(
            self.policy_caused,
            field_name="policy_caused",
            expected=None,
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        _require_exact_bool(
            self.penalty_eligible,
            field_name="penalty_eligible",
            expected=None,
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        if self.penalty_eligible and not self.policy_caused:
            raise EventSchemaError(
                "penalty-eligible resolver rejection must be policy-caused",
                failure_code="rejection_attribution",
                field_name="penalty_eligible",
                expected="penalty_eligible implies policy_caused",
                actual=(self.policy_caused, self.penalty_eligible),
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )
        _require_global_id_tuple(
            self.member_robot_ids,
            field_name="member_robot_ids",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            allow_empty=False,
        )
        _require_global_id_tuple(
            self.member_task_ids,
            field_name="member_task_ids",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            allow_empty=False,
        )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("rejection_reason", self.rejection_reason),
                ("policy_caused", self.policy_caused),
                ("penalty_eligible", self.penalty_eligible),
                ("member_robot_ids", self.member_robot_ids),
                ("member_task_ids", self.member_task_ids),
            )
        )


@dataclass(frozen=True, slots=True)
class OwnershipTransferCommittedPayload:
    """Typed payload for an atomic ownership-transfer commit diagnostic."""

    task_ids: tuple[int, ...]
    previous_owner_ids: tuple[int, ...]
    updated_owner_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        tasks = _require_global_id_tuple(
            self.task_ids,
            field_name="task_ids",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            allow_empty=False,
        )
        for field_name, value in (
            ("previous_owner_ids", self.previous_owner_ids),
            ("updated_owner_ids", self.updated_owner_ids),
        ):
            if type(value) is not tuple or len(value) != len(tasks):
                raise EventSchemaError(
                    f"{field_name} must align one-to-one with task_ids",
                    failure_code="ownership_tuple_shape",
                    field_name=field_name,
                    expected=f"tuple length {len(tasks)}",
                    actual=value,
                    schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
                )
            for index, owner in enumerate(value):
                _require_int64(
                    owner,
                    field_name=f"{field_name}[{index}]",
                    schema_version=(
                        RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION
                    ),
                    minimum=-1,
                )
        if any(
            previous == updated
            for previous, updated in zip(
                self.previous_owner_ids,
                self.updated_owner_ids,
                strict=True,
            )
        ):
            raise EventSchemaError(
                "ownership-transfer payload contains an unchanged owner",
                failure_code="ownership_transfer_identity",
                expected="previous owner != updated owner for every task",
                actual=(
                    self.previous_owner_ids,
                    self.updated_owner_ids,
                ),
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        return _payload_mapping(
            (
                ("task_ids", self.task_ids),
                ("previous_owner_ids", self.previous_owner_ids),
                ("updated_owner_ids", self.updated_owner_ids),
            )
        )


_RESOLVER_PAYLOAD_TYPES: Mapping[
    ResolverDiagnosticType,
    type[
        ResolverComponentAcceptedPayload
        | ResolverComponentRejectedPayload
        | OwnershipTransferCommittedPayload
    ],
] = MappingProxyType(
    {
        ResolverDiagnosticType.COMPONENT_ACCEPTED: (
            ResolverComponentAcceptedPayload
        ),
        ResolverDiagnosticType.COMPONENT_REJECTED: (
            ResolverComponentRejectedPayload
        ),
        ResolverDiagnosticType.OWNERSHIP_TRANSFER_COMMITTED: (
            OwnershipTransferCommittedPayload
        ),
    }
)


@dataclass(frozen=True, slots=True)
class ResolverDiagnosticRecord:
    """One non-triggering post-resolver diagnostic record."""

    schema_version: str
    diagnostic_id: tuple[int, int, int, int, int]
    diagnostic_type: ResolverDiagnosticType
    producer_id: ResolverDiagnosticProducerId
    env_id: int
    episode_generation: int
    transition_generation: int
    assignment_tick_generation: int
    ordinal: int
    component_id: str
    trigger_eligible: bool
    payload: (
        ResolverComponentAcceptedPayload
        | ResolverComponentRejectedPayload
        | OwnershipTransferCommittedPayload
    )

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _require_exact_string(
            self.schema_version,
            field_name="schema_version",
            expected=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        if type(self.diagnostic_type) is not ResolverDiagnosticType:
            raise EventSchemaError(
                "diagnostic_type must use the canonical resolver enum",
                failure_code="enum_type",
                field_name="diagnostic_type",
                expected=ResolverDiagnosticType,
                actual=type(self.diagnostic_type),
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )
        if (
            type(self.producer_id) is not ResolverDiagnosticProducerId
            or self.producer_id
            is not ResolverDiagnosticProducerId.RESOLVER_DIAGNOSTIC_PRODUCER_V1
        ):
            raise EventAuthorityMismatchError(
                "resolver diagnostic carries the wrong producer identity",
                failure_code="producer_id",
                field_name="producer_id",
                expected=(
                    ResolverDiagnosticProducerId
                    .RESOLVER_DIAGNOSTIC_PRODUCER_V1
                ),
                actual=self.producer_id,
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )
        for field_name, minimum in (
            ("env_id", _INT64_MIN),
            ("episode_generation", 0),
            ("transition_generation", 0),
            ("assignment_tick_generation", 0),
            ("ordinal", 0),
        ):
            _require_int64(
                getattr(self, field_name),
                field_name=field_name,
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
                minimum=minimum,
            )
        _require_exact_string(
            self.component_id,
            field_name="component_id",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        expected_id = (
            self.env_id,
            self.episode_generation,
            self.transition_generation,
            self.assignment_tick_generation,
            self.ordinal,
        )
        actual_id = _require_exact_id_tuple(
            self.diagnostic_id,
            field_name="diagnostic_id",
            length=5,
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            minimums=(_INT64_MIN, 0, 0, 0, 0),
        )
        if actual_id != expected_id:
            raise EventGenerationError(
                "diagnostic_id differs from its generation fields",
                failure_code="record_id_binding",
                field_name="diagnostic_id",
                expected=expected_id,
                actual=actual_id,
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )
        _require_exact_bool(
            self.trigger_eligible,
            field_name="trigger_eligible",
            expected=False,
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
        expected_payload = _RESOLVER_PAYLOAD_TYPES[self.diagnostic_type]
        if type(self.payload) is not expected_payload:
            raise EventSchemaError(
                "resolver diagnostic payload type does not match diagnostic_type",
                failure_code="payload_type",
                field_name="payload",
                expected=expected_payload,
                actual=type(self.payload),
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )

    def to_mapping(self) -> Mapping[str, object]:
        self.validate()
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "diagnostic_id": self.diagnostic_id,
                "diagnostic_type": self.diagnostic_type.value,
                "producer_id": self.producer_id.value,
                "env_id": self.env_id,
                "episode_generation": self.episode_generation,
                "transition_generation": self.transition_generation,
                "assignment_tick_generation": (
                    self.assignment_tick_generation
                ),
                "ordinal": self.ordinal,
                "component_id": self.component_id,
                "trigger_eligible": self.trigger_eligible,
                "payload": self.payload.to_mapping(),
            }
        )


def _validate_order(
    records: tuple[object, ...],
    *,
    key_name: str,
    key_function: object,
    record_system: str,
    schema_version: str,
) -> None:
    keys = tuple(key_function(record) for record in records)  # type: ignore[operator]
    if len(set(keys)) != len(keys):
        raise EventGenerationError(
            f"{record_system} contains a duplicate ordinal/generation ID",
            failure_code="duplicate_ordinal",
            field_name=key_name,
            expected="unique canonical record IDs",
            actual=keys,
            record_system=record_system,
            schema_version=schema_version,
        )
    if keys != tuple(sorted(keys)):
        raise EventGenerationError(
            f"{record_system} is not in deterministic canonical order",
            failure_code="record_order",
            field_name=key_name,
            expected=tuple(sorted(keys)),
            actual=keys,
            record_system=record_system,
            schema_version=schema_version,
        )


def validate_lifecycle_event_records(
    records: tuple[object, ...],
) -> tuple[LifecycleEventRecord, ...]:
    """Validate a canonical immutable lifecycle-event container."""

    if type(records) is not tuple:
        raise EventPlacementError(
            "lifecycle event container must be an exact immutable tuple",
            failure_code="container_type",
            expected="tuple[LifecycleEventRecord, ...]",
            actual=type(records),
            record_system="lifecycle_event",
            schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        )
    for record in records:
        if type(record) is not LifecycleEventRecord:
            raise EventPlacementError(
                "lifecycle event container contains another record system",
                failure_code="record_placement",
                expected=LifecycleEventRecord,
                actual=type(record),
                record_system="lifecycle_event",
                schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            )
        record.validate()
    _validate_order(
        records,
        key_name="event_id",
        key_function=lambda record: record.event_id,
        record_system="lifecycle_event",
        schema_version=LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
    )
    return records  # type: ignore[return-value]


def validate_assignment_opportunity_records(
    records: tuple[object, ...],
) -> tuple[AssignmentOpportunityRecord, ...]:
    """Validate a canonical immutable retry-opportunity container."""

    if type(records) is not tuple:
        raise EventPlacementError(
            "opportunity container must be an exact immutable tuple",
            failure_code="container_type",
            expected="tuple[AssignmentOpportunityRecord, ...]",
            actual=type(records),
            record_system="assignment_opportunity",
            schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
        )
    for record in records:
        if type(record) is not AssignmentOpportunityRecord:
            raise EventPlacementError(
                "opportunity container contains another record system",
                failure_code="record_placement",
                expected=AssignmentOpportunityRecord,
                actual=type(record),
                record_system="assignment_opportunity",
                schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
            )
        record.validate()
    _validate_order(
        records,
        key_name="opportunity_id",
        key_function=lambda record: record.opportunity_id,
        record_system="assignment_opportunity",
        schema_version=ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
    )
    return records  # type: ignore[return-value]


def validate_resolver_diagnostic_records(
    records: tuple[object, ...],
) -> tuple[ResolverDiagnosticRecord, ...]:
    """Validate the non-triggering resolver diagnostic stream."""

    if type(records) is not tuple:
        raise EventPlacementError(
            "resolver diagnostic stream must be an exact immutable tuple",
            failure_code="container_type",
            expected="tuple[ResolverDiagnosticRecord, ...]",
            actual=type(records),
            record_system="resolver_diagnostic",
            schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        )
    for record in records:
        if type(record) is not ResolverDiagnosticRecord:
            raise EventPlacementError(
                "resolver diagnostic stream contains another record system",
                failure_code="record_placement",
                expected=ResolverDiagnosticRecord,
                actual=type(record),
                record_system="resolver_diagnostic",
                schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
            )
        record.validate()
    _validate_order(
        records,
        key_name="diagnostic_id",
        key_function=lambda record: record.diagnostic_id,
        record_system="resolver_diagnostic",
        schema_version=RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
    )
    return records  # type: ignore[return-value]


def validate_local_trigger_sources(
    records: tuple[object, ...],
) -> tuple[LifecycleEventRecord | AssignmentOpportunityRecord, ...]:
    """Allow lifecycle events and opportunities, and reject diagnostics."""

    if type(records) is not tuple:
        raise EventPlacementError(
            "local trigger input must be an exact immutable tuple",
            failure_code="container_type",
            expected=(
                "tuple[LifecycleEventRecord | "
                "AssignmentOpportunityRecord, ...]"
            ),
            actual=type(records),
            record_system="local_trigger",
            schema_version=ASSIGNMENT_EVENT_CONTRACT_VERSION,
        )
    lifecycle: list[LifecycleEventRecord] = []
    opportunities: list[AssignmentOpportunityRecord] = []
    for record in records:
        if type(record) is LifecycleEventRecord:
            record.validate()
            lifecycle.append(record)
        elif type(record) is AssignmentOpportunityRecord:
            record.validate()
            opportunities.append(record)
        else:
            raise EventPlacementError(
                "local trigger input accepts only finalized lifecycle events "
                "and scheduled assignment opportunities",
                failure_code="record_placement",
                expected=(
                    LifecycleEventRecord,
                    AssignmentOpportunityRecord,
                ),
                actual=type(record),
                record_system="local_trigger",
                schema_version=ASSIGNMENT_EVENT_CONTRACT_VERSION,
            )
    validate_lifecycle_event_records(tuple(lifecycle))
    validate_assignment_opportunity_records(tuple(opportunities))
    return records  # type: ignore[return-value]


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


_SCHEDULED_ASSIGNMENT_OPPORTUNITY_SEMANTICS = {
    "projection_version": (
        SCHEDULED_ASSIGNMENT_OPPORTUNITY_SEMANTICS_VERSION
    ),
    "unresolved_parameter": {
        "name": "assignment_retry_cadence",
        "owner_phase": "phase_b",
        "semantic_purpose": (
            "physical_step_interval_for_persistent_unassigned_"
            "retry_opportunities"
        ),
    },
    "counter_source": "finalized_physical_transition_generation_delta",
    "unit": "physical_transitions",
    "persistent_unassigned_equation": (
        "current_assignment[e,i]==NO_TASK AND "
        "robot_state[e,i] IN {NEEDS_ASSIGNMENT,WAITING_FOR_TASK} AND "
        "robot_available[e,i] AND NOT terminal[e]"
    ),
    "anchor_initialization_rule": (
        "on_first_persistent_unassigned_entry_set_anchor_to_"
        "finalized_transition_generation"
    ),
    "anchor_refresh_rule": (
        "after_any_assignment_tick_containing_robot_if_still_"
        "persistent_unassigned_refresh_anchor_to_finalized_"
        "transition_generation"
    ),
    "due_equation": (
        "same_episode_as_anchor AND persistent_unassigned[e,i] AND "
        "transition_generation[e]-retry_anchor_transition_generation[e,i]"
        ">=assignment_retry_cadence"
    ),
    "retry_generation_rule": (
        "episode_local_per_(env_id,episode_generation,robot_id);"
        "first_emitted_retry=0;increment_only_after_emitted_retry;"
        "early_lifecycle_tick_does_not_increment"
    ),
    "lifecycle_early_trigger_rule": (
        "independent_lifecycle_event_may_trigger_before_cadence_and_"
        "refresh_anchor_without_emitting_retry_record"
    ),
    "unavailable_terminal_suppression": (
        "assigned_or_unavailable_or_terminal_or_episode_reset_"
        "invalidates_retry_anchor"
    ),
    "output_record_schema": (
        "AssignmentOpportunityRecord",
        ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
        AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE.value,
        AssignmentOpportunityProducerId.RETRY_SCHEDULER_V1.value,
    ),
}


_PUBLIC_EVENT_DESCRIPTOR = _deep_readonly(
    {
        "contract_version": ASSIGNMENT_EVENT_CONTRACT_VERSION,
        "record_systems": (
            {
                "name": "finalized_lifecycle_events",
                "schema_version": LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
                "enum_order": tuple(member.value for member in LifecycleEventType),
                "causal_source_order": tuple(
                    member.value for member in LifecycleCausalSource
                ),
                "field_order": (
                    "schema_version",
                    "event_id",
                    "causal_source",
                    "event_type",
                    "env_id",
                    "episode_generation",
                    "transition_generation",
                    "ordinal",
                    "robot_id",
                    "task_id",
                    "trigger_eligible",
                    "facts_consume_token",
                    "authority_id",
                    "payload",
                ),
                "trigger_eligible": True,
                "authority_id": (
                    LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1.value
                ),
            },
            {
                "name": "scheduled_assignment_opportunities",
                "schema_version": (
                    ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION
                ),
                "enum_order": tuple(
                    member.value for member in AssignmentOpportunityType
                ),
                "producer_order": tuple(
                    member.value
                    for member in AssignmentOpportunityProducerId
                ),
                "field_order": (
                    "schema_version",
                    "opportunity_id",
                    "opportunity_type",
                    "producer_id",
                    "env_id",
                    "episode_generation",
                    "transition_generation",
                    "assignment_tick_generation",
                    "ordinal",
                    "robot_id",
                    "retry_generation",
                    "trigger_eligible",
                ),
                "trigger_eligible": True,
            },
            {
                "name": "post_resolver_diagnostics",
                "schema_version": RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
                "enum_order": tuple(
                    member.value for member in ResolverDiagnosticType
                ),
                "producer_order": tuple(
                    member.value for member in ResolverDiagnosticProducerId
                ),
                "field_order": (
                    "schema_version",
                    "diagnostic_id",
                    "diagnostic_type",
                    "producer_id",
                    "env_id",
                    "episode_generation",
                    "transition_generation",
                    "assignment_tick_generation",
                    "ordinal",
                    "component_id",
                    "trigger_eligible",
                    "payload",
                ),
                "trigger_eligible": False,
            },
        ),
        "payload_field_order": {
            "TaskLifecycleEventPayload": (
                "task_id",
                "previous_task_state",
                "updated_task_state",
                "cause_robot_id",
            ),
            "RobotLifecycleEventPayload": (
                "robot_id",
                "previous_robot_state",
                "updated_robot_state",
            ),
            "PairFailureEventPayload": (
                "robot_id",
                "task_id",
                "newly_recorded",
            ),
            "ResolverComponentAcceptedPayload": (
                "member_robot_ids",
                "member_task_ids",
                "transfer_count",
            ),
            "ResolverComponentRejectedPayload": (
                "rejection_reason",
                "policy_caused",
                "penalty_eligible",
                "member_robot_ids",
                "member_task_ids",
            ),
            "OwnershipTransferCommittedPayload": (
                "task_ids",
                "previous_owner_ids",
                "updated_owner_ids",
            ),
        },
        "placement_rules": (
            (
                "LifecycleTransitionResult.lifecycle_events",
                "LifecycleEventRecord",
            ),
            (
                "retry_scheduler_output",
                "AssignmentOpportunityRecord",
            ),
            (
                "local_trigger_input",
                "LifecycleEventRecord | AssignmentOpportunityRecord",
            ),
            (
                "resolver_diagnostic_stream",
                "ResolverDiagnosticRecord",
            ),
        ),
        "record_system_separation": (
            "lifecycle events are lifecycle-authority finalized",
            "retry opportunities are scheduler produced",
            "resolver diagnostics never trigger assignment",
        ),
        "scheduled_assignment_opportunity_semantics": (
            _SCHEDULED_ASSIGNMENT_OPPORTUNITY_SEMANTICS
        ),
    }
)


def get_assignment_event_contract_descriptor() -> Mapping[str, object]:
    """Return the deterministic deeply read-only public A3 event descriptor."""

    return _PUBLIC_EVENT_DESCRIPTOR  # type: ignore[return-value]


__all__ = [
    "ASSIGNMENT_EVENT_CONTRACT_VERSION",
    "ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION",
    "AssignmentEventContractError",
    "AssignmentOpportunityProducerId",
    "AssignmentOpportunityRecord",
    "AssignmentOpportunityType",
    "CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE",
    "EventAuthorityMismatchError",
    "EventGenerationError",
    "EventPlacementError",
    "EventSchemaError",
    "LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION",
    "LifecycleCausalSource",
    "LifecycleEventRecord",
    "LifecycleEventType",
    "OwnershipTransferCommittedPayload",
    "PairFailureEventPayload",
    "RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION",
    "SCHEDULED_ASSIGNMENT_OPPORTUNITY_SEMANTICS_VERSION",
    "ResolverComponentAcceptedPayload",
    "ResolverComponentRejectedPayload",
    "ResolverDiagnosticProducerId",
    "ResolverDiagnosticRecord",
    "ResolverDiagnosticType",
    "RobotLifecycleEventPayload",
    "TaskLifecycleEventPayload",
    "get_assignment_event_contract_descriptor",
    "validate_assignment_opportunity_records",
    "validate_lifecycle_event_records",
    "validate_local_trigger_sources",
    "validate_resolver_diagnostic_records",
]
