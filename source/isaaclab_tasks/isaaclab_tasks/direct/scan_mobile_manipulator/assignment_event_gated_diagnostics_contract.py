"""Pure typed diagnostics contract for event-gated assignment semantics.

The module defines CPU/Python summary payloads, availability semantics,
deterministic serialization, and a typed envelope only.  Phase A3 deliberately
does not create a logger, output sink, info key, TensorBoard metric, file, or
checkpoint.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_gated_diagnostics_contract"
)
ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_SOURCE_PURPOSE = (
    "pure typed event-gated assignment diagnostics contract"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event-gated diagnostics contract "
        "source must fail before declaring identity-bearing types; "
        f"expected module key="
        f"{CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose="
        f"{ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, InitVar
from enum import Enum
import math
from types import MappingProxyType
from typing import TypeAlias

from .assignment_event_contract import (
    AssignmentOpportunityType,
    LifecycleCausalSource,
)
from .assignment_lifecycle_transition_contract import TerminationReason
from .assignment_mrta_contract import (
    ComponentRejectionReason,
    ProposalKind,
    StoredActionRowKind,
)
from .assignment_profile_contract import AssignmentProfileName


ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION = (
    "assignment_event_gated_diagnostics_contract_v1"
)
DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION = (
    "event_gated_diagnostic_envelope_v1"
)

_NON_POLICY_REJECTION_REASONS = frozenset(
    {
        ComponentRejectionReason.LOCAL_SET_OVERFLOW_FAIL_CLOSED,
        ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION,
        ComponentRejectionReason.TERMINAL_TRANSITION,
    }
)


class DiagnosticAvailability(str, Enum):
    PRODUCED = "produced"
    DEFINED_NOT_PRODUCED = "defined_not_produced"
    NOT_APPLICABLE = "not_applicable"


class DiagnosticKind(str, Enum):
    PROFILE_ROUTE = "profile_route"
    TRANSITION_AUTHORITY = "transition_authority"
    ASSIGNMENT_TICK = "assignment_tick"
    PROPOSAL_RESOLUTION = "proposal_resolution"
    ACTOR_UPDATE = "actor_update"
    TEAM_REWARD = "team_reward"
    CHECKPOINT_SEMANTIC = "checkpoint_semantic"
    DEFAULT_OFF_IDENTITY = "default_off_identity"


class TransitionConsumeStatus(str, Enum):
    FIRST_CONSUME = "first_consume"
    DUPLICATE = "duplicate"
    STALE = "stale"
    FUTURE = "future"
    MISMATCH = "mismatch"


class DefaultOffCohort(str, Enum):
    D0_ABSENT = "d0_absent"
    D1_PRE_RESOLVED_VALID = "d1_pre_resolved_valid"
    SCENARIO_CORRECTION = "scenario_correction"


class AssignmentEventGatedDiagnosticsContractError(RuntimeError):
    """Base error with stable diagnostics schema context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        kind: object = None,
        expected: object = None,
        actual: object = None,
        schema_version: str = DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.kind = kind
        self.expected = expected
        self.actual = actual
        self.schema_version = schema_version
        super().__init__(
            f"{message}; "
            f"failure_code={failure_code!r}; "
            f"field_name={field_name!r}; "
            f"kind={_context_value(kind)!r}; "
            f"expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; "
            f"schema_version={schema_version!r}"
        )


class DiagnosticSchemaError(
    AssignmentEventGatedDiagnosticsContractError
):
    """A payload or envelope violates the exact diagnostics schema."""


class DiagnosticAvailabilityError(
    AssignmentEventGatedDiagnosticsContractError
):
    """Availability and payload presence are inconsistent."""


class DiagnosticPayloadKindMismatchError(
    AssignmentEventGatedDiagnosticsContractError
):
    """A diagnostic kind carries the wrong canonical payload type."""


def _context_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return value


def _require_exact_enum(
    value: object,
    enum_type: type[Enum],
    field_name: str,
) -> None:
    if type(value) is not enum_type:
        raise DiagnosticSchemaError(
            f"{field_name} must use its exact canonical enum class",
            failure_code="enum_type",
            field_name=field_name,
            expected=enum_type,
            actual=type(value),
        )


def _require_bool(value: object, field_name: str) -> None:
    if type(value) is not bool:
        raise DiagnosticSchemaError(
            f"{field_name} must be an exact bool",
            failure_code="bool_type",
            field_name=field_name,
            expected=bool,
            actual=type(value),
        )


def _require_int(
    value: object,
    field_name: str,
    *,
    minimum: int = 0,
) -> None:
    if type(value) is not int or value < minimum:
        raise DiagnosticSchemaError(
            f"{field_name} must be an exact int in range",
            failure_code="integer_range",
            field_name=field_name,
            expected=f"int >= {minimum}",
            actual=value,
        )


def _require_finite_float(
    value: object,
    field_name: str,
    *,
    nonnegative: bool = False,
) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise DiagnosticSchemaError(
            f"{field_name} must be an exact finite Python float",
            failure_code="finite_float",
            field_name=field_name,
            expected="finite float",
            actual=value,
        )
    if nonnegative and value < 0.0:
        raise DiagnosticSchemaError(
            f"{field_name} must be non-negative",
            failure_code="float_range",
            field_name=field_name,
            expected="finite float >= 0",
            actual=value,
        )


def _require_string(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> None:
    if type(value) is not str or (not allow_empty and not value):
        raise DiagnosticSchemaError(
            f"{field_name} must be an exact canonical string",
            failure_code="string_type",
            field_name=field_name,
            expected=(
                "exact str" if allow_empty else "non-empty exact str"
            ),
            actual=value,
        )


def _require_optional_string(
    value: object,
    field_name: str,
) -> None:
    if value is not None:
        _require_string(value, field_name)


def _require_tuple(
    value: object,
    field_name: str,
    *,
    item_type: type,
    expected_length: int | None = None,
) -> None:
    if type(value) is not tuple:
        raise DiagnosticSchemaError(
            f"{field_name} must be an immutable tuple",
            failure_code="tuple_type",
            field_name=field_name,
            expected=tuple,
            actual=type(value),
        )
    if expected_length is not None and len(value) != expected_length:
        raise DiagnosticSchemaError(
            f"{field_name} has the wrong fixed length",
            failure_code="tuple_length",
            field_name=field_name,
            expected=expected_length,
            actual=len(value),
        )
    for index, item in enumerate(value):
        if type(item) is not item_type:
            raise DiagnosticSchemaError(
                f"{field_name} contains a non-canonical item",
                failure_code="tuple_item_type",
                field_name=f"{field_name}[{index}]",
                expected=item_type,
                actual=type(item),
            )


class _DiagnosticPayloadSerialization:
    def to_mapping(self) -> Mapping[str, object]:
        return _serialize_payload(self)

    def to_canonical_items(self) -> tuple[tuple[str, object], ...]:
        return tuple(self.to_mapping().items())


@dataclass(frozen=True, slots=True)
class ProfileRouteDiagnostic(_DiagnosticPayloadSerialization):
    profile_contract_version: str
    resolved_variant: str
    runtime_route: str
    checkpoint_family: str
    runtime_readiness: str
    resolution_origin: str
    event_target_semantics_contract_version: str | None

    def __post_init__(self) -> None:
        for field_name in (
            "profile_contract_version",
            "resolved_variant",
            "runtime_route",
            "checkpoint_family",
            "runtime_readiness",
            "resolution_origin",
        ):
            _require_string(getattr(self, field_name), field_name)
        _require_optional_string(
            self.event_target_semantics_contract_version,
            "event_target_semantics_contract_version",
        )


@dataclass(frozen=True, slots=True)
class TransitionAuthorityDiagnostic(_DiagnosticPayloadSerialization):
    facts_schema_version: str
    result_schema_version: str
    facts_producer_id: str
    lifecycle_authority_id: str
    consume_token: int
    receipt_id: int
    consume_status: TransitionConsumeStatus
    generation_match: bool
    facts_producer_match: bool
    lifecycle_authority_match: bool
    pair_attribution_contract_version: str
    pair_attribution_validated: bool
    observable_immutability_contract_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "facts_schema_version",
            "result_schema_version",
            "facts_producer_id",
            "lifecycle_authority_id",
            "pair_attribution_contract_version",
            "observable_immutability_contract_version",
        ):
            _require_string(getattr(self, field_name), field_name)
        _require_int(self.consume_token, "consume_token")
        _require_int(self.receipt_id, "receipt_id")
        _require_exact_enum(
            self.consume_status,
            TransitionConsumeStatus,
            "consume_status",
        )
        for field_name in (
            "generation_match",
            "facts_producer_match",
            "lifecycle_authority_match",
            "pair_attribution_validated",
        ):
            _require_bool(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class AssignmentTickDiagnostic(_DiagnosticPayloadSerialization):
    assignment_tick_count: int
    lifecycle_event_ids: tuple[str, ...]
    lifecycle_causal_sources: tuple[LifecycleCausalSource, ...]
    assignment_opportunity_ids: tuple[str, ...]
    assignment_opportunity_types: tuple[AssignmentOpportunityType, ...]
    trigger_eligible_count: int
    resolver_diagnostic_count: int
    suppressed_resolver_diagnostic_trigger_count: int
    local_robot_count: int
    local_task_count: int
    per_robot_decision_count: tuple[int, ...]
    decision_valid_count: int
    policy_proposal_count_by_kind: tuple[int, ...]
    forced_storage_row_count: int
    accepted_component_count: int
    rejected_component_count: int
    ownership_transfer_count: int
    needs_assignment_duration: tuple[int, ...]
    idle_with_available_task_count: int
    failed_pair_count: int
    team_infeasible_task_count: int
    termination_reason: TerminationReason
    expected_robot_count: InitVar[int]

    def __post_init__(self, expected_robot_count: int) -> None:
        _require_int(expected_robot_count, "expected_robot_count", minimum=1)
        for field_name in (
            "assignment_tick_count",
            "trigger_eligible_count",
            "resolver_diagnostic_count",
            "suppressed_resolver_diagnostic_trigger_count",
            "local_robot_count",
            "local_task_count",
            "decision_valid_count",
            "forced_storage_row_count",
            "accepted_component_count",
            "rejected_component_count",
            "ownership_transfer_count",
            "idle_with_available_task_count",
            "failed_pair_count",
            "team_infeasible_task_count",
        ):
            _require_int(getattr(self, field_name), field_name)
        _require_tuple(
            self.lifecycle_event_ids,
            "lifecycle_event_ids",
            item_type=str,
        )
        _require_tuple(
            self.lifecycle_causal_sources,
            "lifecycle_causal_sources",
            item_type=LifecycleCausalSource,
        )
        _require_tuple(
            self.assignment_opportunity_ids,
            "assignment_opportunity_ids",
            item_type=str,
        )
        _require_tuple(
            self.assignment_opportunity_types,
            "assignment_opportunity_types",
            item_type=AssignmentOpportunityType,
        )
        for field_name, value in (
            ("lifecycle_event_ids", self.lifecycle_event_ids),
            (
                "assignment_opportunity_ids",
                self.assignment_opportunity_ids,
            ),
        ):
            for index, item in enumerate(value):
                _require_string(item, f"{field_name}[{index}]")
            if len(set(value)) != len(value):
                raise DiagnosticSchemaError(
                    f"{field_name} must not contain duplicate identities",
                    failure_code="duplicate_identity",
                    field_name=field_name,
                    expected="unique tuple",
                    actual=value,
                )
        if len(self.lifecycle_event_ids) != len(
            self.lifecycle_causal_sources
        ):
            raise DiagnosticSchemaError(
                "lifecycle event IDs and sources must have equal cardinality",
                failure_code="tuple_alignment",
                field_name="lifecycle_causal_sources",
                expected=len(self.lifecycle_event_ids),
                actual=len(self.lifecycle_causal_sources),
            )
        if len(self.assignment_opportunity_ids) != len(
            self.assignment_opportunity_types
        ):
            raise DiagnosticSchemaError(
                "assignment opportunity IDs and types must align",
                failure_code="tuple_alignment",
                field_name="assignment_opportunity_types",
                expected=len(self.assignment_opportunity_ids),
                actual=len(self.assignment_opportunity_types),
            )
        expected_trigger_count = (
            len(self.lifecycle_event_ids)
            + len(self.assignment_opportunity_ids)
        )
        if self.trigger_eligible_count != expected_trigger_count:
            raise DiagnosticSchemaError(
                "trigger count must equal lifecycle events plus opportunities",
                failure_code="trigger_count",
                field_name="trigger_eligible_count",
                expected=expected_trigger_count,
                actual=self.trigger_eligible_count,
            )
        if (
            self.suppressed_resolver_diagnostic_trigger_count
            > self.resolver_diagnostic_count
        ):
            raise DiagnosticSchemaError(
                "suppressed resolver trigger count exceeds diagnostics",
                failure_code="suppression_count",
                field_name="suppressed_resolver_diagnostic_trigger_count",
                expected=f"<= {self.resolver_diagnostic_count}",
                actual=self.suppressed_resolver_diagnostic_trigger_count,
            )
        _require_tuple(
            self.per_robot_decision_count,
            "per_robot_decision_count",
            item_type=int,
            expected_length=expected_robot_count,
        )
        _require_tuple(
            self.needs_assignment_duration,
            "needs_assignment_duration",
            item_type=int,
            expected_length=expected_robot_count,
        )
        for field_name, values in (
            ("per_robot_decision_count", self.per_robot_decision_count),
            ("needs_assignment_duration", self.needs_assignment_duration),
        ):
            for index, value in enumerate(values):
                _require_int(value, f"{field_name}[{index}]")
        _require_tuple(
            self.policy_proposal_count_by_kind,
            "policy_proposal_count_by_kind",
            item_type=int,
            expected_length=len(ProposalKind),
        )
        for index, value in enumerate(
            self.policy_proposal_count_by_kind
        ):
            _require_int(
                value,
                f"policy_proposal_count_by_kind[{index}]",
            )
        proposal_count = sum(self.policy_proposal_count_by_kind)
        if proposal_count != self.decision_valid_count:
            raise DiagnosticSchemaError(
                "policy proposal count must equal decision-valid count",
                failure_code="proposal_count",
                field_name="policy_proposal_count_by_kind",
                expected=self.decision_valid_count,
                actual=proposal_count,
            )
        if self.decision_valid_count > sum(
            self.per_robot_decision_count
        ):
            raise DiagnosticSchemaError(
                "decision-valid count exceeds per-robot decision total",
                failure_code="decision_count",
                field_name="decision_valid_count",
                expected=(
                    f"<= {sum(self.per_robot_decision_count)}"
                ),
                actual=self.decision_valid_count,
            )
        _require_exact_enum(
            self.termination_reason,
            TerminationReason,
            "termination_reason",
        )


@dataclass(frozen=True, slots=True)
class ProposalResolutionDiagnostic(_DiagnosticPayloadSerialization):
    robot_id: int
    storage_row_present: bool
    policy_proposal_present: bool
    forced_nondecision: bool
    decision_valid: bool
    stored_row_kind: StoredActionRowKind
    proposal_kind: ProposalKind | None
    stored_action_id: int
    proposed_task_id: int
    effective_assignment: int
    proposal_accepted: bool | None
    proposal_effective_mismatch: bool | None
    component_id: str
    component_size: int
    rejection_reason: ComponentRejectionReason
    policy_caused: bool
    penalty_eligible: bool
    ownership_transfer_count: int
    local_cost_before: float
    local_cost_after: float

    def __post_init__(self) -> None:
        _require_int(self.robot_id, "robot_id")
        for field_name in (
            "storage_row_present",
            "policy_proposal_present",
            "forced_nondecision",
            "decision_valid",
            "policy_caused",
            "penalty_eligible",
        ):
            _require_bool(getattr(self, field_name), field_name)
        _require_exact_enum(
            self.stored_row_kind,
            StoredActionRowKind,
            "stored_row_kind",
        )
        if self.proposal_kind is not None:
            _require_exact_enum(
                self.proposal_kind,
                ProposalKind,
                "proposal_kind",
            )
        for field_name, value in (
            ("stored_action_id", self.stored_action_id),
            ("proposed_task_id", self.proposed_task_id),
            ("effective_assignment", self.effective_assignment),
        ):
            _require_int(value, field_name, minimum=-1)
        if self.proposal_accepted is not None:
            _require_bool(self.proposal_accepted, "proposal_accepted")
        if self.proposal_effective_mismatch is not None:
            _require_bool(
                self.proposal_effective_mismatch,
                "proposal_effective_mismatch",
            )
        _require_string(self.component_id, "component_id", allow_empty=True)
        _require_int(self.component_size, "component_size")
        _require_exact_enum(
            self.rejection_reason,
            ComponentRejectionReason,
            "rejection_reason",
        )
        _require_int(
            self.ownership_transfer_count,
            "ownership_transfer_count",
        )
        _require_finite_float(
            self.local_cost_before,
            "local_cost_before",
            nonnegative=True,
        )
        _require_finite_float(
            self.local_cost_after,
            "local_cost_after",
            nonnegative=True,
        )

        if self.policy_proposal_present != self.decision_valid:
            raise DiagnosticSchemaError(
                "policy proposal presence must equal decision-valid",
                failure_code="four_mask",
                field_name="policy_proposal_present",
                expected=self.decision_valid,
                actual=self.policy_proposal_present,
            )
        expected_forced = (
            self.storage_row_present and not self.decision_valid
        )
        if self.forced_nondecision != expected_forced:
            raise DiagnosticSchemaError(
                "forced row must equal storage and not decision-valid",
                failure_code="four_mask",
                field_name="forced_nondecision",
                expected=expected_forced,
                actual=self.forced_nondecision,
            )
        if self.storage_row_present != (
            self.policy_proposal_present or self.forced_nondecision
        ):
            raise DiagnosticSchemaError(
                "storage presence must equal policy-or-forced",
                failure_code="four_mask",
                field_name="storage_row_present",
                expected=(
                    self.policy_proposal_present
                    or self.forced_nondecision
                ),
                actual=self.storage_row_present,
            )

        if self.policy_proposal_present:
            if self.stored_row_kind is not (
                StoredActionRowKind.POLICY_PROPOSAL
            ):
                raise DiagnosticSchemaError(
                    "policy row requires POLICY_PROPOSAL kind",
                    failure_code="stored_row_kind",
                    field_name="stored_row_kind",
                    expected=StoredActionRowKind.POLICY_PROPOSAL,
                    actual=self.stored_row_kind,
                )
            if self.proposal_kind is None:
                raise DiagnosticSchemaError(
                    "policy row requires a proposal kind",
                    failure_code="proposal_optional",
                    field_name="proposal_kind",
                    expected=ProposalKind,
                    actual=None,
                )
            if self.stored_action_id < 0:
                raise DiagnosticSchemaError(
                    "policy row requires a stored action ID",
                    failure_code="stored_action",
                    field_name="stored_action_id",
                    expected=">= 0",
                    actual=self.stored_action_id,
                )
            if (
                self.proposal_accepted is None
                or self.proposal_effective_mismatch is None
            ):
                raise DiagnosticSchemaError(
                    "policy row requires accepted and mismatch diagnostics",
                    failure_code="proposal_optional",
                    field_name="proposal_accepted",
                    expected="bool values",
                    actual=(
                        self.proposal_accepted,
                        self.proposal_effective_mismatch,
                    ),
                )
            expected_mismatch = (
                self.proposed_task_id != self.effective_assignment
            )
            if self.proposal_effective_mismatch != expected_mismatch:
                raise DiagnosticSchemaError(
                    "proposal/effective mismatch is algebraically inconsistent",
                    failure_code="proposal_mismatch",
                    field_name="proposal_effective_mismatch",
                    expected=expected_mismatch,
                    actual=self.proposal_effective_mismatch,
                )
            if self.proposal_accepted:
                if self.rejection_reason is not (
                    ComponentRejectionReason.NONE
                ):
                    raise DiagnosticSchemaError(
                        "accepted proposal cannot carry rejection reason",
                        failure_code="rejection_relation",
                        field_name="rejection_reason",
                        expected=ComponentRejectionReason.NONE,
                        actual=self.rejection_reason,
                    )
                if self.proposal_effective_mismatch:
                    raise DiagnosticSchemaError(
                        "accepted proposal cannot mismatch effective assignment",
                        failure_code="proposal_mismatch",
                        field_name="proposal_effective_mismatch",
                        expected=False,
                        actual=True,
                    )
            elif self.rejection_reason is ComponentRejectionReason.NONE:
                raise DiagnosticSchemaError(
                    "rejected proposal requires a non-NONE reason",
                    failure_code="rejection_relation",
                    field_name="rejection_reason",
                    expected="non-NONE ComponentRejectionReason",
                    actual=self.rejection_reason,
                )
        elif self.forced_nondecision:
            if self.stored_row_kind is not (
                StoredActionRowKind.FORCED_NONDECISION
            ):
                raise DiagnosticSchemaError(
                    "forced row requires FORCED_NONDECISION kind",
                    failure_code="stored_row_kind",
                    field_name="stored_row_kind",
                    expected=StoredActionRowKind.FORCED_NONDECISION,
                    actual=self.stored_row_kind,
                )
            if self.stored_action_id < 0:
                raise DiagnosticSchemaError(
                    "forced nondecision row requires a legal stored action ID",
                    failure_code="stored_action",
                    field_name="stored_action_id",
                    expected=">= 0",
                    actual=self.stored_action_id,
                )
            self._validate_nonpolicy_optional_fields()
        else:
            if self.stored_row_kind is not StoredActionRowKind.NO_ROW:
                raise DiagnosticSchemaError(
                    "terminal/no-storage row requires NO_ROW kind",
                    failure_code="stored_row_kind",
                    field_name="stored_row_kind",
                    expected=StoredActionRowKind.NO_ROW,
                    actual=self.stored_row_kind,
                )
            if self.stored_action_id != -1:
                raise DiagnosticSchemaError(
                    "terminal/no-row stored action must be -1",
                    failure_code="stored_action",
                    field_name="stored_action_id",
                    expected=-1,
                    actual=self.stored_action_id,
                )
            self._validate_nonpolicy_optional_fields()

        if self.penalty_eligible and not self.policy_caused:
            raise DiagnosticSchemaError(
                "penalty eligibility requires policy attribution",
                failure_code="penalty_attribution",
                field_name="penalty_eligible",
                expected=False,
                actual=True,
            )
        if self.penalty_eligible and (
            self.rejection_reason is ComponentRejectionReason.NONE
        ):
            raise DiagnosticSchemaError(
                "penalty eligibility requires a rejection reason",
                failure_code="penalty_attribution",
                field_name="rejection_reason",
                expected="non-NONE ComponentRejectionReason",
                actual=self.rejection_reason,
            )
        if self.rejection_reason in _NON_POLICY_REJECTION_REASONS and (
            self.policy_caused or self.penalty_eligible
        ):
            raise DiagnosticSchemaError(
                "overflow, post-snapshot, and terminal rejection diagnostics "
                "cannot carry policy or penalty attribution",
                failure_code="nonpolicy_rejection_attribution",
                field_name="rejection_reason",
                expected=(False, False),
                actual=(self.policy_caused, self.penalty_eligible),
            )
        if (
            self.rejection_reason is ComponentRejectionReason.NONE
            and (self.policy_caused or self.penalty_eligible)
        ):
            raise DiagnosticSchemaError(
                "a non-rejection diagnostic cannot carry policy or penalty "
                "attribution",
                failure_code="penalty_attribution",
                field_name="rejection_reason",
                expected=(False, False),
                actual=(self.policy_caused, self.penalty_eligible),
            )

    def _validate_nonpolicy_optional_fields(self) -> None:
        if self.proposal_kind is not None:
            raise DiagnosticSchemaError(
                "non-policy row cannot carry proposal kind",
                failure_code="proposal_optional",
                field_name="proposal_kind",
                expected=None,
                actual=self.proposal_kind,
            )
        if self.proposed_task_id != -1:
            raise DiagnosticSchemaError(
                "non-policy proposed task ID must be -1",
                failure_code="proposal_optional",
                field_name="proposed_task_id",
                expected=-1,
                actual=self.proposed_task_id,
            )
        if (
            self.proposal_accepted is not None
            or self.proposal_effective_mismatch is not None
        ):
            raise DiagnosticSchemaError(
                "non-policy row cannot fabricate resolver outcome",
                failure_code="proposal_optional",
                field_name="proposal_accepted",
                expected=(None, None),
                actual=(
                    self.proposal_accepted,
                    self.proposal_effective_mismatch,
                ),
            )
        if self.rejection_reason is not ComponentRejectionReason.NONE:
            raise DiagnosticSchemaError(
                "non-policy row cannot carry rejection reason",
                failure_code="rejection_relation",
                field_name="rejection_reason",
                expected=ComponentRejectionReason.NONE,
                actual=self.rejection_reason,
            )
        if self.policy_caused or self.penalty_eligible:
            raise DiagnosticSchemaError(
                "non-policy row cannot be policy-caused or penalty-eligible",
                failure_code="penalty_attribution",
                field_name="policy_caused",
                expected=(False, False),
                actual=(self.policy_caused, self.penalty_eligible),
            )


@dataclass(frozen=True, slots=True)
class ActorUpdateDiagnostic(_DiagnosticPayloadSerialization):
    actor_id: int
    decision_valid_sample_count: int
    skipped_actor_update_count: int
    skipped_minibatch_count: int
    singleton_advantage_fallback_count: int
    nondecision_factor_identity_violation_count: int
    reduction_denominator: int

    def __post_init__(self) -> None:
        for field_name in (
            "actor_id",
            "decision_valid_sample_count",
            "skipped_actor_update_count",
            "skipped_minibatch_count",
            "singleton_advantage_fallback_count",
            "nondecision_factor_identity_violation_count",
            "reduction_denominator",
        ):
            _require_int(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class TeamRewardDiagnostic(_DiagnosticPayloadSerialization):
    wrapper_final_reward_mean: float
    policy_rejected_component_count: int
    rejection_penalty_scale: float
    team_reward: float
    broadcast_agent_count: int
    broadcast_equal: bool

    def __post_init__(self) -> None:
        _require_finite_float(
            self.wrapper_final_reward_mean,
            "wrapper_final_reward_mean",
        )
        _require_int(
            self.policy_rejected_component_count,
            "policy_rejected_component_count",
        )
        _require_finite_float(
            self.rejection_penalty_scale,
            "rejection_penalty_scale",
            nonnegative=True,
        )
        _require_finite_float(self.team_reward, "team_reward")
        _require_int(
            self.broadcast_agent_count,
            "broadcast_agent_count",
            minimum=1,
        )
        _require_bool(self.broadcast_equal, "broadcast_equal")


@dataclass(frozen=True, slots=True)
class CheckpointSemanticDiagnostic(_DiagnosticPayloadSerialization):
    manifest_format_version: str
    manifest_kind: str
    profile_name: str
    checkpoint_family: str
    fingerprint_sha256: str
    purpose: str
    compatibility_classification: str
    runtime_readiness: str

    def __post_init__(self) -> None:
        for field_name in (
            "manifest_format_version",
            "manifest_kind",
            "profile_name",
            "checkpoint_family",
            "fingerprint_sha256",
            "purpose",
            "compatibility_classification",
            "runtime_readiness",
        ):
            _require_string(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class DefaultOffIdentityDiagnostic(_DiagnosticPayloadSerialization):
    cohort: DefaultOffCohort
    surface: str
    evidence_label: str
    expected_digest: str | None
    actual_digest: str | None
    matched: bool
    deferred_reason: str | None

    def __post_init__(self) -> None:
        _require_exact_enum(self.cohort, DefaultOffCohort, "cohort")
        _require_string(self.surface, "surface")
        _require_string(self.evidence_label, "evidence_label")
        _require_optional_string(self.expected_digest, "expected_digest")
        _require_optional_string(self.actual_digest, "actual_digest")
        _require_bool(self.matched, "matched")
        _require_optional_string(self.deferred_reason, "deferred_reason")
        if self.matched:
            if (
                self.expected_digest is None
                or self.actual_digest is None
                or self.expected_digest != self.actual_digest
            ):
                raise DiagnosticSchemaError(
                    "matched identity requires equal produced digests",
                    failure_code="digest_relation",
                    field_name="matched",
                    expected="equal non-None digests",
                    actual=(
                        self.expected_digest,
                        self.actual_digest,
                    ),
                )
            if self.deferred_reason is not None:
                raise DiagnosticSchemaError(
                    "matched identity cannot also be deferred",
                    failure_code="digest_relation",
                    field_name="deferred_reason",
                    expected=None,
                    actual=self.deferred_reason,
                )


DiagnosticPayload: TypeAlias = (
    ProfileRouteDiagnostic
    | TransitionAuthorityDiagnostic
    | AssignmentTickDiagnostic
    | ProposalResolutionDiagnostic
    | ActorUpdateDiagnostic
    | TeamRewardDiagnostic
    | CheckpointSemanticDiagnostic
    | DefaultOffIdentityDiagnostic
)


_PAYLOAD_TYPE_BY_KIND: Mapping[DiagnosticKind, type] = MappingProxyType(
    {
        DiagnosticKind.PROFILE_ROUTE: ProfileRouteDiagnostic,
        DiagnosticKind.TRANSITION_AUTHORITY: TransitionAuthorityDiagnostic,
        DiagnosticKind.ASSIGNMENT_TICK: AssignmentTickDiagnostic,
        DiagnosticKind.PROPOSAL_RESOLUTION: (
            ProposalResolutionDiagnostic
        ),
        DiagnosticKind.ACTOR_UPDATE: ActorUpdateDiagnostic,
        DiagnosticKind.TEAM_REWARD: TeamRewardDiagnostic,
        DiagnosticKind.CHECKPOINT_SEMANTIC: (
            CheckpointSemanticDiagnostic
        ),
        DiagnosticKind.DEFAULT_OFF_IDENTITY: (
            DefaultOffIdentityDiagnostic
        ),
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticEnvelope:
    schema_version: str = DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION
    kind: DiagnosticKind
    resolved_profile: AssignmentProfileName
    env_id: int
    episode_generation: int
    transition_generation: int
    assignment_tick_generation: int
    availability: DiagnosticAvailability
    payload: DiagnosticPayload | None

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not str
            or self.schema_version != DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION
        ):
            raise DiagnosticSchemaError(
                "diagnostic envelope schema version mismatch",
                failure_code="schema_version",
                field_name="schema_version",
                expected=DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION,
                actual=self.schema_version,
            )
        _require_exact_enum(self.kind, DiagnosticKind, "kind")
        _require_exact_enum(
            self.resolved_profile,
            AssignmentProfileName,
            "resolved_profile",
        )
        _require_int(self.env_id, "env_id")
        _require_int(
            self.episode_generation,
            "episode_generation",
        )
        _require_int(
            self.transition_generation,
            "transition_generation",
        )
        _require_int(
            self.assignment_tick_generation,
            "assignment_tick_generation",
            minimum=-1,
        )
        _require_exact_enum(
            self.availability,
            DiagnosticAvailability,
            "availability",
        )

        expected_payload_type = _PAYLOAD_TYPE_BY_KIND[self.kind]
        if self.availability is DiagnosticAvailability.PRODUCED:
            if type(self.payload) is not expected_payload_type:
                raise DiagnosticPayloadKindMismatchError(
                    "produced diagnostic carries the wrong payload type",
                    failure_code="payload_kind",
                    field_name="payload",
                    kind=self.kind,
                    expected=expected_payload_type,
                    actual=type(self.payload),
                )
        elif self.payload is not None:
            raise DiagnosticAvailabilityError(
                "unproduced or not-applicable diagnostic must not fabricate "
                "a payload",
                failure_code="availability_payload",
                field_name="payload",
                kind=self.kind,
                expected=None,
                actual=type(self.payload),
            )

        if (
            self.availability is DiagnosticAvailability.PRODUCED
            and self.kind
            in (
                DiagnosticKind.ASSIGNMENT_TICK,
                DiagnosticKind.PROPOSAL_RESOLUTION,
            )
            and self.assignment_tick_generation < 0
        ):
            raise DiagnosticSchemaError(
                "tick-scoped produced diagnostic requires tick generation",
                failure_code="tick_generation",
                field_name="assignment_tick_generation",
                kind=self.kind,
                expected=">= 0",
                actual=self.assignment_tick_generation,
            )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
    ) -> "DiagnosticEnvelope":
        if not isinstance(values, Mapping):
            raise DiagnosticSchemaError(
                "diagnostic envelope input must be a mapping",
                failure_code="mapping_type",
                field_name="values",
                expected=Mapping,
                actual=type(values),
            )
        expected_keys = (
            "schema_version",
            "kind",
            "resolved_profile",
            "env_id",
            "episode_generation",
            "transition_generation",
            "assignment_tick_generation",
            "availability",
            "payload",
        )
        actual_keys = tuple(values.keys())
        if (
            any(type(key) is not str for key in actual_keys)
            or set(actual_keys) != set(expected_keys)
            or len(actual_keys) != len(expected_keys)
        ):
            raise DiagnosticSchemaError(
                "diagnostic envelope mapping key set mismatch",
                failure_code="mapping_keys",
                field_name="values",
                expected=expected_keys,
                actual=actual_keys,
            )
        return cls(
            schema_version=values["schema_version"],  # type: ignore[arg-type]
            kind=values["kind"],  # type: ignore[arg-type]
            resolved_profile=values["resolved_profile"],  # type: ignore[arg-type]
            env_id=values["env_id"],  # type: ignore[arg-type]
            episode_generation=values["episode_generation"],  # type: ignore[arg-type]
            transition_generation=values["transition_generation"],  # type: ignore[arg-type]
            assignment_tick_generation=values[
                "assignment_tick_generation"
            ],  # type: ignore[arg-type]
            availability=values["availability"],  # type: ignore[arg-type]
            payload=values["payload"],  # type: ignore[arg-type]
        )

    def to_mapping(self) -> Mapping[str, object]:
        serialized_payload = (
            None if self.payload is None else self.payload.to_mapping()
        )
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "kind": self.kind.value,
                "resolved_profile": self.resolved_profile.value,
                "env_id": self.env_id,
                "episode_generation": self.episode_generation,
                "transition_generation": self.transition_generation,
                "assignment_tick_generation": (
                    self.assignment_tick_generation
                ),
                "availability": self.availability.value,
                "payload": serialized_payload,
            }
        )

    def to_canonical_items(self) -> tuple[tuple[str, object], ...]:
        return tuple(self.to_mapping().items())


def _serialize_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if type(value) is tuple:
        return tuple(_serialize_value(item) for item in value)
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise DiagnosticSchemaError(
        "diagnostic serialization encountered a non-primitive value",
        failure_code="serialization_type",
        field_name="payload",
        expected="Python primitive, enum, immutable tuple, or None",
        actual=type(value),
    )


_PAYLOAD_FIELD_ORDER: Mapping[type, tuple[str, ...]] = MappingProxyType(
    {
        ProfileRouteDiagnostic: (
            "profile_contract_version",
            "resolved_variant",
            "runtime_route",
            "checkpoint_family",
            "runtime_readiness",
            "resolution_origin",
            "event_target_semantics_contract_version",
        ),
        TransitionAuthorityDiagnostic: (
            "facts_schema_version",
            "result_schema_version",
            "facts_producer_id",
            "lifecycle_authority_id",
            "consume_token",
            "receipt_id",
            "consume_status",
            "generation_match",
            "facts_producer_match",
            "lifecycle_authority_match",
            "pair_attribution_contract_version",
            "pair_attribution_validated",
            "observable_immutability_contract_version",
        ),
        AssignmentTickDiagnostic: (
            "assignment_tick_count",
            "lifecycle_event_ids",
            "lifecycle_causal_sources",
            "assignment_opportunity_ids",
            "assignment_opportunity_types",
            "trigger_eligible_count",
            "resolver_diagnostic_count",
            "suppressed_resolver_diagnostic_trigger_count",
            "local_robot_count",
            "local_task_count",
            "per_robot_decision_count",
            "decision_valid_count",
            "policy_proposal_count_by_kind",
            "forced_storage_row_count",
            "accepted_component_count",
            "rejected_component_count",
            "ownership_transfer_count",
            "needs_assignment_duration",
            "idle_with_available_task_count",
            "failed_pair_count",
            "team_infeasible_task_count",
            "termination_reason",
        ),
        ProposalResolutionDiagnostic: (
            "robot_id",
            "storage_row_present",
            "policy_proposal_present",
            "forced_nondecision",
            "decision_valid",
            "stored_row_kind",
            "proposal_kind",
            "stored_action_id",
            "proposed_task_id",
            "effective_assignment",
            "proposal_accepted",
            "proposal_effective_mismatch",
            "component_id",
            "component_size",
            "rejection_reason",
            "policy_caused",
            "penalty_eligible",
            "ownership_transfer_count",
            "local_cost_before",
            "local_cost_after",
        ),
        ActorUpdateDiagnostic: (
            "actor_id",
            "decision_valid_sample_count",
            "skipped_actor_update_count",
            "skipped_minibatch_count",
            "singleton_advantage_fallback_count",
            "nondecision_factor_identity_violation_count",
            "reduction_denominator",
        ),
        TeamRewardDiagnostic: (
            "wrapper_final_reward_mean",
            "policy_rejected_component_count",
            "rejection_penalty_scale",
            "team_reward",
            "broadcast_agent_count",
            "broadcast_equal",
        ),
        CheckpointSemanticDiagnostic: (
            "manifest_format_version",
            "manifest_kind",
            "profile_name",
            "checkpoint_family",
            "fingerprint_sha256",
            "purpose",
            "compatibility_classification",
            "runtime_readiness",
        ),
        DefaultOffIdentityDiagnostic: (
            "cohort",
            "surface",
            "evidence_label",
            "expected_digest",
            "actual_digest",
            "matched",
            "deferred_reason",
        ),
    }
)


def _serialize_payload(value: object) -> Mapping[str, object]:
    field_order = _PAYLOAD_FIELD_ORDER.get(type(value))
    if field_order is None:
        raise DiagnosticSchemaError(
            "unknown diagnostic payload type",
            failure_code="payload_type",
            field_name="payload",
            expected=tuple(_PAYLOAD_FIELD_ORDER.keys()),
            actual=type(value),
        )
    return MappingProxyType(
        {
            field_name: _serialize_value(getattr(value, field_name))
            for field_name in field_order
        }
    )


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


_DIAGNOSTICS_PUBLIC_DESCRIPTOR = _deep_readonly(
    {
        "contract_version": (
            ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION
        ),
        "schema_version": DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION,
        "diagnostic_availability_order": tuple(
            item.value for item in DiagnosticAvailability
        ),
        "diagnostic_kind_order": tuple(
            item.value for item in DiagnosticKind
        ),
        "transition_consume_status_order": tuple(
            item.value for item in TransitionConsumeStatus
        ),
        "default_off_cohort_order": tuple(
            item.value for item in DefaultOffCohort
        ),
        "envelope_field_order": (
            "schema_version",
            "kind",
            "resolved_profile",
            "env_id",
            "episode_generation",
            "transition_generation",
            "assignment_tick_generation",
            "availability",
            "payload",
        ),
        "payload_type_by_kind": tuple(
            (
                kind.value,
                _PAYLOAD_TYPE_BY_KIND[kind].__name__,
                _PAYLOAD_FIELD_ORDER[_PAYLOAD_TYPE_BY_KIND[kind]],
            )
            for kind in DiagnosticKind
        ),
        "availability_rules": (
            "produced requires the exact canonical payload type for kind",
            "defined_not_produced requires payload None",
            "not_applicable requires payload None",
            "unproduced measurements are never represented by zero fill",
        ),
        "serialization": (
            "fixed enum order",
            "fixed field order",
            "Python primitive values and immutable tuples only",
            "deeply read-only mappings",
            "finite Python float validation",
            "no live tensor alias",
        ),
    }
)


def get_assignment_event_gated_diagnostics_descriptor(
) -> Mapping[str, object]:
    """Return the deterministic deeply read-only diagnostics descriptor."""

    return _DIAGNOSTICS_PUBLIC_DESCRIPTOR  # type: ignore[return-value]


__all__ = [
    "ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION",
    "ActorUpdateDiagnostic",
    "AssignmentEventGatedDiagnosticsContractError",
    "AssignmentTickDiagnostic",
    "CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE",
    "CheckpointSemanticDiagnostic",
    "DIAGNOSTIC_ENVELOPE_SCHEMA_VERSION",
    "DefaultOffCohort",
    "DefaultOffIdentityDiagnostic",
    "DiagnosticAvailability",
    "DiagnosticAvailabilityError",
    "DiagnosticEnvelope",
    "DiagnosticKind",
    "DiagnosticPayload",
    "DiagnosticPayloadKindMismatchError",
    "DiagnosticSchemaError",
    "ProfileRouteDiagnostic",
    "ProposalResolutionDiagnostic",
    "TeamRewardDiagnostic",
    "TransitionAuthorityDiagnostic",
    "TransitionConsumeStatus",
    "get_assignment_event_gated_diagnostics_descriptor",
]
