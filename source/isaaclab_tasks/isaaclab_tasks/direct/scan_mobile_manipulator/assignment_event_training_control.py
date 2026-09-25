"""Pure B2-R1 mutation-permit, receipt, failure, and ordering contracts.

The controller objects in this module mutate only their own synthetic ledger or
state-machine bookkeeping.  They are not connected to tensors, modules,
optimizers, ValueNorm, runners, or lifecycle runtime objects.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_CONTROL_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_control"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_CONTROL_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R1 training control source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_CONTROL_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass
from enum import Enum, IntEnum
import re
from typing import Sequence

from .assignment_event_training_evidence import (
    B2RContractError,
    STOP_AUTHORITY_DRIFT,
    STOP_VALUENORM,
    canonical_digest_v1,
)


B2R_MUTATION_PERMIT_V1 = "b2r_mutation_permit_v1"
B2R_STEP_RECEIPT_V1 = "b2r_step_receipt_v1"
B2R_FAILURE_EVIDENCE_V1 = "b2r_failure_evidence_v1"
B2R_ORDERING_EVIDENCE_V1 = "b2r_ordering_evidence_v1"

STOP_UNAUTHORIZED_BACKWARD = "STOP — B2-R UNAUTHORIZED_BACKWARD"
STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_UNEXPECTED_STEP_COUNT = "STOP — B2-R UNEXPECTED_STEP_COUNT"
STOP_MUTATION_ATTRIBUTION = "STOP — B2-R MUTATION_ATTRIBUTION"
STOP_MODE_ORDER = "STOP — B2-R MODE_ORDER"
STOP_ROLLOVER_ORDER = "STOP — B2-R ROLLOVER_ORDER"
STOP_CHECKPOINT_BOUNDARY = "STOP — B2-R CHECKPOINT_BOUNDARY"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _fail(
    message: str,
    *,
    stop_code: str,
    stage: str,
    field_name: str | None = None,
    expected: object = None,
    observed: object = None,
) -> None:
    raise B2RContractError(
        message,
        stop_code=stop_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        observed=observed,
    )


class B2RPermitOperationV1(str, Enum):
    BACKWARD = "backward"
    VALUENORM_UPDATE = "valuenorm_update"
    OPTIMIZER_STEP = "optimizer_step"


class B2RUpdateStageV1(str, Enum):
    S0_ROLLOUT_COMPLETE = "S0_ROLLOUT_COMPLETE"
    S1_FINAL_VALUE_EVALUATED = "S1_FINAL_VALUE_EVALUATED"
    S2_EVENT_RETURNS_FROZEN = "S2_EVENT_RETURNS_FROZEN"
    S3_UPDATE_PLAN_FROZEN = "S3_UPDATE_PLAN_FROZEN"
    S4_TRAINING_MODE_ENTERED = "S4_TRAINING_MODE_ENTERED"
    S5_ACTOR_SEQUENCE = "S5_ACTOR_SEQUENCE"
    S6_CRITIC_SEQUENCE = "S6_CRITIC_SEQUENCE"
    S7_POST_UPDATE_AUDIT = "S7_POST_UPDATE_AUDIT"
    S8_ROLLOUT_MODE_RESTORED = "S8_ROLLOUT_MODE_RESTORED"
    S9_ROLLOVER_COMPLETE = "S9_ROLLOVER_COMPLETE"
    S10_QUIESCENT = "S10_QUIESCENT"


class _B2RStageOrdinalV1(IntEnum):
    S0_ROLLOUT_COMPLETE = 0
    S1_FINAL_VALUE_EVALUATED = 1
    S2_EVENT_RETURNS_FROZEN = 2
    S3_UPDATE_PLAN_FROZEN = 3
    S4_TRAINING_MODE_ENTERED = 4
    S5_ACTOR_SEQUENCE = 5
    S6_CRITIC_SEQUENCE = 6
    S7_POST_UPDATE_AUDIT = 7
    S8_ROLLOUT_MODE_RESTORED = 8
    S9_ROLLOVER_COMPLETE = 9
    S10_QUIESCENT = 10


_STAGE_ORDINAL = {
    stage: _B2RStageOrdinalV1[stage.name] for stage in B2RUpdateStageV1
}


def _operation_stop_code(operation: B2RPermitOperationV1) -> str:
    if operation is B2RPermitOperationV1.BACKWARD:
        return STOP_UNAUTHORIZED_BACKWARD
    if operation is B2RPermitOperationV1.OPTIMIZER_STEP:
        return STOP_UNAUTHORIZED_OPTIMIZER_STEP
    return STOP_VALUENORM


@dataclass(frozen=True, slots=True)
class B2RMutationPermitV1:
    permit_id: str
    update_id: str
    authority_config_digest: str
    component_kind: str
    owner_identity: str
    actor_id: int | None
    stage: B2RUpdateStageV1
    epoch: int
    minibatch: int
    canonical_index_digest: str
    allowed_operations: tuple[B2RPermitOperationV1, ...]
    expected_call_count: int
    precondition_fingerprint_digest: str
    issuance_sequence: int
    schema_version: str = B2R_MUTATION_PERMIT_V1

    def __post_init__(self) -> None:
        strings = (
            self.permit_id,
            self.update_id,
            self.authority_config_digest,
            self.component_kind,
            self.owner_identity,
            self.canonical_index_digest,
            self.precondition_fingerprint_digest,
        )
        if any(type(value) is not str or not value for value in strings):
            _fail(
                "permit string identities must be nonempty",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_schema",
                observed=strings,
            )
        for field_name, value in (
            ("authority_config_digest", self.authority_config_digest),
            ("canonical_index_digest", self.canonical_index_digest),
            ("precondition_fingerprint_digest", self.precondition_fingerprint_digest),
        ):
            if _SHA256_PATTERN.fullmatch(value) is None:
                _fail(
                    "permit digest binding is malformed",
                    stop_code=STOP_AUTHORITY_DRIFT,
                    stage="permit_schema",
                    field_name=field_name,
                    observed=value,
                )
        if type(self.stage) is not B2RUpdateStageV1:
            _fail(
                "permit stage must use the frozen state enum",
                stop_code=STOP_MODE_ORDER,
                stage="permit_schema",
                observed=self.stage,
            )
        if (
            type(self.epoch) is not int
            or self.epoch < 0
            or type(self.minibatch) is not int
            or self.minibatch < 0
            or type(self.issuance_sequence) is not int
            or self.issuance_sequence < 0
        ):
            _fail(
                "permit ordinal fields must be nonnegative exact integers",
                stop_code=STOP_MODE_ORDER,
                stage="permit_schema",
                observed=(self.epoch, self.minibatch, self.issuance_sequence),
            )
        if self.actor_id is not None and (type(self.actor_id) is not int or self.actor_id < 0):
            _fail(
                "permit actor identity must be absent or nonnegative",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="permit_schema",
                observed=self.actor_id,
            )
        if (
            not self.allowed_operations
            or any(type(item) is not B2RPermitOperationV1 for item in self.allowed_operations)
            or len(set(self.allowed_operations)) != len(self.allowed_operations)
        ):
            _fail(
                "permit allowed-operation set is invalid",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_schema",
                observed=self.allowed_operations,
            )
        if self.expected_call_count != 1:
            _fail(
                "B2-R mutation permits are single-use",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="permit_schema",
                expected=1,
                observed=self.expected_call_count,
            )

    @property
    def permit_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RPermitConsumptionV1:
    permit_id: str
    operation: B2RPermitOperationV1
    issuance_sequence: int
    consumed_count: int
    schema_version: str = "b2r_permit_consumption_v1"


class B2RPermitLedgerV1:
    """Test-only single-use ledger with no callable learner operation."""

    __slots__ = (
        "_permits",
        "_consumed",
        "_expired",
        "_next_sequence",
        "_poisoned",
        "_update_id",
        "_config_digest",
    )

    def __init__(self, permits: Sequence[B2RMutationPermitV1]) -> None:
        permit_tuple = tuple(permits)
        if not permit_tuple:
            _fail(
                "permit ledger requires at least one immutable permit",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_ledger",
                observed=permit_tuple,
            )
        identifiers = tuple(item.permit_id for item in permit_tuple)
        sequences = tuple(item.issuance_sequence for item in permit_tuple)
        update_ids = {item.update_id for item in permit_tuple}
        config_digests = {item.authority_config_digest for item in permit_tuple}
        if len(set(identifiers)) != len(identifiers) or sequences != tuple(range(len(permit_tuple))):
            _fail(
                "permit ledger identities/sequences are not canonical",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_ledger",
                expected="unique IDs and contiguous sequence from zero",
                observed=(identifiers, sequences),
            )
        if len(update_ids) != 1 or len(config_digests) != 1:
            _fail(
                "permit ledger mixes update or configuration authority",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_ledger",
                observed=(update_ids, config_digests),
            )
        self._permits = {item.permit_id: item for item in permit_tuple}
        self._consumed = {item.permit_id: 0 for item in permit_tuple}
        self._expired: set[str] = set()
        self._next_sequence = 0
        self._poisoned = False
        self._update_id = next(iter(update_ids))
        self._config_digest = next(iter(config_digests))

    @property
    def pending_count(self) -> int:
        return sum(count == 0 for count in self._consumed.values())

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    def expire(self, permit_id: str) -> None:
        if permit_id not in self._permits:
            _fail(
                "cannot expire an unknown permit",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_ledger",
                observed=permit_id,
            )
        self._expired.add(permit_id)

    def poison(self) -> None:
        self._poisoned = True

    def consume(
        self,
        *,
        permit_id: str,
        operation: B2RPermitOperationV1,
        update_id: str,
        authority_config_digest: str,
        component_kind: str,
        owner_identity: str,
        actor_id: int | None,
        stage: B2RUpdateStageV1,
        epoch: int,
        minibatch: int,
        canonical_index_digest: str,
        precondition_fingerprint_digest: str,
    ) -> B2RPermitConsumptionV1:
        permit = self._permits.get(permit_id)
        if permit is None:
            _fail(
                "mutation attempted without an issued permit",
                stop_code=_operation_stop_code(operation),
                stage="permit_consume",
                observed=permit_id,
            )
        if self._poisoned:
            _fail(
                "poisoned update cannot consume another permit",
                stop_code=_operation_stop_code(operation),
                stage="permit_consume",
                expected="live unpoisoned ledger",
                observed="poisoned",
            )
        if update_id != self._update_id or authority_config_digest != self._config_digest:
            _fail(
                "permit consumption authority drifted",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="permit_consume",
                expected=(self._update_id, self._config_digest),
                observed=(update_id, authority_config_digest),
            )
        if type(operation) is not B2RPermitOperationV1 or operation not in permit.allowed_operations:
            stop_code = (
                STOP_AUTHORITY_DRIFT
                if type(operation) is not B2RPermitOperationV1
                else _operation_stop_code(operation)
            )
            _fail(
                "permit does not authorize the requested operation",
                stop_code=stop_code,
                stage="permit_consume",
                expected=permit.allowed_operations,
                observed=operation,
            )
        if permit_id in self._expired or self._consumed[permit_id] >= permit.expected_call_count:
            _fail(
                "permit is expired or already consumed",
                stop_code=_operation_stop_code(operation),
                stage="permit_consume",
                expected="one live unconsumed permit",
                observed={
                    "expired": permit_id in self._expired,
                    "consumed": self._consumed[permit_id],
                },
            )
        if permit.issuance_sequence != self._next_sequence:
            _fail(
                "permit consumed out of issuance order",
                stop_code=STOP_MODE_ORDER,
                stage="permit_consume",
                expected=self._next_sequence,
                observed=permit.issuance_sequence,
            )
        binding_expected = (
            permit.component_kind,
            permit.owner_identity,
            permit.actor_id,
            permit.stage,
            permit.epoch,
            permit.minibatch,
            permit.canonical_index_digest,
            permit.precondition_fingerprint_digest,
        )
        binding_observed = (
            component_kind,
            owner_identity,
            actor_id,
            stage,
            epoch,
            minibatch,
            canonical_index_digest,
            precondition_fingerprint_digest,
        )
        if stage is not permit.stage:
            stop_code = STOP_MODE_ORDER
        else:
            stop_code = _operation_stop_code(operation)
        if binding_observed != binding_expected:
            _fail(
                "permit consumption binding does not match issuance",
                stop_code=stop_code,
                stage="permit_consume",
                expected=binding_expected,
                observed=binding_observed,
            )
        self._consumed[permit_id] += 1
        self._next_sequence += 1
        return B2RPermitConsumptionV1(
            permit_id=permit_id,
            operation=operation,
            issuance_sequence=permit.issuance_sequence,
            consumed_count=self._consumed[permit_id],
        )


@dataclass(frozen=True, slots=True)
class B2RMutationExpectationV1:
    component_kind: str
    owner_identity: str
    condition_identity: str
    expected_backward_count: int
    expected_optimizer_step_count: int
    expected_valuenorm_update_count: int
    parameter_mutation_classification: str
    optimizer_mutation_classification: str
    valuenorm_mutation_classification: str
    forced_or_no_policy_rows_excluded: bool
    schema_version: str = "b2r_mutation_expectation_v1"

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value < 0
            for value in (
                self.expected_backward_count,
                self.expected_optimizer_step_count,
                self.expected_valuenorm_update_count,
            )
        ):
            _fail(
                "mutation expectation counts must be nonnegative exact integers",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="mutation_expectation",
                observed=(self.expected_backward_count, self.expected_optimizer_step_count, self.expected_valuenorm_update_count),
            )
        if type(self.forced_or_no_policy_rows_excluded) is not bool or not self.forced_or_no_policy_rows_excluded:
            _fail(
                "actor mutation expectations must exclude forced/no-policy rows",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="mutation_expectation",
                expected=True,
                observed=self.forced_or_no_policy_rows_excluded,
            )
        for value in (
            self.component_kind,
            self.owner_identity,
            self.condition_identity,
            self.parameter_mutation_classification,
            self.optimizer_mutation_classification,
            self.valuenorm_mutation_classification,
        ):
            if type(value) is not str or not value:
                _fail(
                    "mutation expectation identities/classifications must be nonempty",
                    stop_code=STOP_MUTATION_ATTRIBUTION,
                    stage="mutation_expectation",
                    observed=value,
                )


@dataclass(frozen=True, slots=True)
class B2RStepReceiptV1:
    consumed_permit_id: str
    stage: B2RUpdateStageV1
    owner_identity: str
    actor_id: int | None
    epoch: int
    minibatch: int
    canonical_row_digest: str
    pre_loss_fingerprint: str
    loss_summary: str
    gradient_fingerprint: str
    clip_summary: str
    pre_parameter_fingerprint: str
    post_parameter_fingerprint: str
    optimizer_fingerprint: str
    valuenorm_fingerprint: str
    mutation_classification: str
    no_foreign_mutation: bool
    stage_transition_result: str
    synthetic_fixture: bool
    schema_version: str = B2R_STEP_RECEIPT_V1

    def __post_init__(self) -> None:
        if not self.synthetic_fixture:
            _fail(
                "B2-R1 may create only synthetic receipt fixtures",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="step_receipt",
                expected=True,
                observed=False,
            )

    @property
    def receipt_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RFailureEvidenceV1:
    stop_code: str
    stage: str
    owner_identity: str | None
    component_kind: str | None
    actor_id: int | None
    epoch: int | None
    minibatch: int | None
    canonical_index_identity: str | None
    parameter_identity: str | None
    expected_summary: str
    observed_summary: str
    last_completed_receipt: str | None
    irreversible_mutation_occurred: bool
    partial_update: bool
    route_poisoned: bool
    restoration_classification: str
    quarantine_classification: str
    rollover_allowed: bool
    checkpoint_allowed: bool
    next_rollout_allowed: bool
    public_use_allowed: bool
    prohibited_next_actions: tuple[str, ...]
    schema_version: str = B2R_FAILURE_EVIDENCE_V1

    def __post_init__(self) -> None:
        if type(self.stop_code) is not str or not self.stop_code.startswith("STOP — B2-R "):
            _fail(
                "failure evidence requires one exact B2-R STOP category",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="failure_evidence",
                observed=self.stop_code,
            )
        if self.partial_update != self.irreversible_mutation_occurred:
            _fail(
                "partial-update evidence must match irreversible mutation",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="failure_evidence",
                expected=self.irreversible_mutation_occurred,
                observed=self.partial_update,
            )
        if self.partial_update and (
            not self.route_poisoned
            or self.rollover_allowed
            or self.checkpoint_allowed
            or self.next_rollout_allowed
            or self.public_use_allowed
        ):
            _fail(
                "future post-mutation failure must poison and prohibit continuation",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="failure_evidence",
                expected="poisoned and all continuation flags false",
                observed=(
                    self.route_poisoned,
                    self.rollover_allowed,
                    self.checkpoint_allowed,
                    self.next_rollout_allowed,
                    self.public_use_allowed,
                ),
            )
        if not self.partial_update and self.irreversible_mutation_occurred:
            _fail(
                "pure failure fixture cannot claim irreversible mutation",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="failure_evidence",
            )

    @property
    def failure_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2ROrderingEvidenceV1:
    history: tuple[B2RUpdateStageV1, ...]
    poisoned: bool
    pending_permit_count: int
    checkpoint_eligible: bool
    schema_version: str = B2R_ORDERING_EVIDENCE_V1

    @property
    def ordering_digest(self) -> str:
        return canonical_digest_v1(self)


class B2RUpdateStateMachineV1:
    """Pure exact S0--S10 transition validator."""

    __slots__ = ("_current", "_history", "_poisoned")

    def __init__(self) -> None:
        self._current = B2RUpdateStageV1.S0_ROLLOUT_COMPLETE
        self._history = [self._current]
        self._poisoned = False

    @property
    def current(self) -> B2RUpdateStageV1:
        return self._current

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    def poison(self) -> None:
        self._poisoned = True

    def transition(self, next_stage: B2RUpdateStageV1) -> None:
        if self._poisoned:
            _fail(
                "poisoned update cannot transition or continue",
                stop_code=STOP_MODE_ORDER,
                stage=self._current.value,
                expected="no continuation",
                observed=next_stage,
            )
        if type(next_stage) is not B2RUpdateStageV1:
            _fail(
                "next state must use the frozen S0-S10 enum",
                stop_code=STOP_MODE_ORDER,
                stage=self._current.value,
                observed=next_stage,
            )
        current_ordinal = int(_STAGE_ORDINAL[self._current])
        next_ordinal = int(_STAGE_ORDINAL[next_stage])
        expected_ordinal = current_ordinal + 1
        if next_ordinal != expected_ordinal:
            stop_code = (
                STOP_ROLLOVER_ORDER
                if next_stage is B2RUpdateStageV1.S9_ROLLOVER_COMPLETE
                or self._current is B2RUpdateStageV1.S9_ROLLOVER_COMPLETE
                else STOP_MODE_ORDER
            )
            _fail(
                "state-machine transition skipped or reversed a frozen stage",
                stop_code=stop_code,
                stage=self._current.value,
                expected=(
                    None
                    if expected_ordinal > int(_B2RStageOrdinalV1.S10_QUIESCENT)
                    else B2RUpdateStageV1(
                        _B2RStageOrdinalV1(expected_ordinal).name
                    ).value
                ),
                observed=next_stage.value,
            )
        self._current = next_stage
        self._history.append(next_stage)

    def evidence(self, *, pending_permit_count: int) -> B2ROrderingEvidenceV1:
        eligible = (
            self._current is B2RUpdateStageV1.S10_QUIESCENT
            and not self._poisoned
            and pending_permit_count == 0
        )
        return B2ROrderingEvidenceV1(
            history=tuple(self._history),
            poisoned=self._poisoned,
            pending_permit_count=pending_permit_count,
            checkpoint_eligible=eligible,
        )

    def require_checkpoint_eligible(self, *, pending_permit_count: int) -> None:
        evidence = self.evidence(pending_permit_count=pending_permit_count)
        if not evidence.checkpoint_eligible:
            _fail(
                "checkpoint eligibility requires unpoisoned S10 with no pending permit",
                stop_code=STOP_CHECKPOINT_BOUNDARY,
                stage=self._current.value,
                expected="S10, unpoisoned, pending_permit_count=0",
                observed=(self._current, self._poisoned, pending_permit_count),
            )


__all__: tuple[str, ...] = ()
