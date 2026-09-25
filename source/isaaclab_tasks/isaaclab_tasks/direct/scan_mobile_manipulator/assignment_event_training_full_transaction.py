"""Private B2-R5 full learner-update transaction coordinator.

This module composes the reviewed R1--R4 authorities.  It is deliberately
production-unreferenced and does not own another backward, optimizer-step, or
live-ValueNorm executor.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_FULL_TRANSACTION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_full_transaction"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_FULL_TRANSACTION_MODULE:
    raise ImportError("CanonicalModuleIdentityError: B2-R5 requires canonical import")


from dataclasses import dataclass
from typing import Mapping, Sequence

import torch

from .assignment_event_training_evidence import (
    B2RContractError,
    B2RFrozenTrainingInputsV1,
    B2RUpdateAuthorityV1,
    STOP_AUTHORITY_DRIFT,
    canonical_digest_v1,
    fingerprint_tensor_v1,
)
from .assignment_event_training_plans import (
    B2RActorUpdatePlanV1,
    B2RCriticUpdatePlanV1,
    STOP_AGENT_ORDER,
    STOP_CRITIC_ROW_COVERAGE,
    STOP_UNEXPECTED_STEP_COUNT,
)
from .assignment_event_training_control import (
    B2ROrderingEvidenceV1,
    B2RUpdateStageV1,
    B2RUpdateStateMachineV1,
    STOP_CHECKPOINT_BOUNDARY,
    STOP_MODE_ORDER,
    STOP_MUTATION_ATTRIBUTION,
    STOP_ROLLOVER_ORDER,
)
from .assignment_event_training_gradient_probe import validate_gradients_clear_v1
from . import assignment_event_training_actor_mutation as R3
from . import assignment_event_training_critic_mutation as R4


STOP_ROLLOUT_INCOMPLETE = "STOP — B2-R ROLLOUT_INCOMPLETE"
STOP_TERMINAL_EVIDENCE_MISSING = "STOP — B2-R TERMINAL_EVIDENCE_MISSING"
STOP_TERMINAL_EVIDENCE_UNEXPECTED = "STOP — B2-R TERMINAL_EVIDENCE_UNEXPECTED"
STOP_TERMINAL_EVIDENCE_DUPLICATE = "STOP — B2-R TERMINAL_EVIDENCE_DUPLICATE"
STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH = (
    "STOP — B2-R TERMINAL_EVIDENCE_IDENTITY_MISMATCH"
)
STOP_TERMINAL_GENERATION_MISMATCH = "STOP — B2-R TERMINAL_GENERATION_MISMATCH"
STOP_ACTOR_EVIDENCE_MISSING = "STOP — B2-R ACTOR_EVIDENCE_MISSING"
STOP_ACTOR_EVIDENCE_UNEXPECTED = "STOP — B2-R ACTOR_EVIDENCE_UNEXPECTED"
STOP_ACTOR_EVIDENCE_DUPLICATE = "STOP — B2-R ACTOR_EVIDENCE_DUPLICATE"
STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH = (
    "STOP — B2-R ACTOR_EVIDENCE_IDENTITY_MISMATCH"
)
STOP_ACTOR_EVIDENCE_UPDATE_ID_MISMATCH = (
    "STOP — B2-R ACTOR_EVIDENCE_UPDATE_ID_MISMATCH"
)
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_VALUENORM = "STOP — B2-R VALUENORM"
STOP_PUBLIC_ROUTE_OPEN = "STOP — B2-R PUBLIC_ROUTE_OPEN"

_EXPECTED_STAGES = tuple(B2RUpdateStageV1)


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


def _module_modes(actors: Sequence[object], critic: object) -> tuple[tuple[bool, ...], bool]:
    return tuple(bool(actor.actor.training) for actor in actors), bool(critic.critic.training)


def _parameter_optimizer_digests(
    actors: Sequence[object], critic: object, live_value_normalizer: object
) -> tuple[tuple[tuple[str, str], ...], tuple[str, str], str]:
    actor_values = tuple(
        (R3._parameter_digest(R3.fingerprint_component_v1(
            component_kind="actor", owner_identity=f"actor{index}",
            module=actor.actor, optimizer=actor.actor_optimizer,
        )), R3._optimizer_digest(R3.fingerprint_component_v1(
            component_kind="actor", owner_identity=f"actor{index}",
            module=actor.actor, optimizer=actor.actor_optimizer,
        )))
        for index, actor in enumerate(actors)
    )
    critic_fp = R3.fingerprint_component_v1(
        component_kind="critic", owner_identity="critic",
        module=critic.critic, optimizer=critic.critic_optimizer,
    )
    return (
        actor_values,
        (R3._parameter_digest(critic_fp), R3._optimizer_digest(critic_fp)),
        R4._valuenorm_digest(live_value_normalizer),
    )


def _component_state_digest(
    actors: Sequence[object], critic: object, live_value_normalizer: object
) -> str:
    return canonical_digest_v1(
        _parameter_optimizer_digests(actors, critic, live_value_normalizer)
    )


def _validate_all_gradients_clear(actors: Sequence[object], critic: object) -> None:
    validate_gradients_clear_v1(
        tuple((f"actor{index}", actor.actor) for index, actor in enumerate(actors))
        + (("critic", critic.critic),)
    )


@dataclass(frozen=True, slots=True)
class B2R5FullUpdateAuthorityV1:
    base_authority: B2RUpdateAuthorityV1
    actor_authority: R3.B2R3MutationAuthorityV1
    critic_authority: R4.B2R4MutationAuthorityV1
    transaction_id: str
    slice_identity: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    schema_version: str = "b2r5_full_update_authority_v1"

    def __post_init__(self) -> None:
        required_allowed = {
            "actor_sequence", "critic_sequence", "live_valuenorm_update",
            "training_mode_entry", "rollout_mode_restore", "critic_rollover",
            "terminal_ledger_reset", "actor_storage_rollover",
        }
        required_forbidden = {
            "isaac", "real_environment_rollout", "training_campaign",
            "evaluation_playback", "checkpoint_weight_io",
            "public_route_activation", "r6", "r7", "scheduler_redesign",
        }
        base_digest = self.base_authority.authority_digest
        if (
            self.slice_identity != "B2-R5"
            or not self.transaction_id
            or self.actor_authority.base_authority.authority_digest != base_digest
            or self.critic_authority.base_authority.authority_digest != base_digest
            or not required_allowed.issubset(set(self.allowed_operations))
            or not required_forbidden.issubset(set(self.forbidden_operations))
        ):
            _fail("R5 authority composition drifted", stop_code=STOP_AUTHORITY_DRIFT, stage="r5_authority")

    @property
    def update_id(self) -> str:
        return self.base_authority.update_id

    @property
    def config_digest(self) -> str:
        return self.base_authority.config_digest

    @property
    def authority_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5RolloutCompleteEvidenceV1:
    update_id: str
    authority_config_digest: str
    resolved_T: int
    resolved_E: int
    resolved_M: int
    resolved_N: int
    actor_storage_complete: tuple[bool, ...]
    critic_transition_storage_complete: bool
    terminal_learner_evidence_complete: bool
    termination_reason_digest: str
    timeout_sidecar_digest: str
    proposal_action_logprob_digest: str
    dvm_active_availability_digest: str
    actor_evidence_expected_rows: tuple[tuple[str, int, int, int, int, int], ...]
    actor_evidence_observed_rows: tuple[tuple[str, int, int, int, int, int], ...]
    actor_evidence_reconciliation_digest: str
    current_final_slot_digest_by_actor: tuple[tuple[int, str], ...]
    actor_buffer_cursors: tuple[int, ...]
    critic_buffer_cursor: int
    expected_terminal_keys: tuple[tuple[int, int, int], ...]
    terminal_consumption_keys: tuple[tuple[int, int, int], ...]
    terminal_reconciliation_digest: str
    terminal_evidence_is_historical_pre_reset: bool
    runtime_ack_is_separate_from_learner_consumption: bool
    final_value_evaluated: bool
    selected_termination_domain_valid: bool
    event_returns_compute_count: int
    schema_version: str = "b2r5_rollout_complete_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5TerminalEvidenceReconciliationV1:
    expected_terminal_keys: tuple[tuple[int, int, int], ...]
    observed_terminal_keys: tuple[tuple[int, int, int], ...]
    expected_count: int
    observed_count: int
    unique_expected_count: int
    unique_observed_count: int
    missing_terminal_keys: tuple[tuple[int, int, int], ...]
    unexpected_terminal_keys: tuple[tuple[int, int, int], ...]
    duplicate_observed_keys: tuple[tuple[int, int, int], ...]
    exact_match: bool
    schema_version: str = "b2r5_terminal_evidence_reconciliation_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5ActorEvidenceReconciliationV1:
    update_id: str
    actor_ids: tuple[int, ...]
    expected_actor_rows: tuple[tuple[str, int, int, int, int, int], ...]
    observed_actor_rows: tuple[tuple[str, int, int, int, int, int], ...]
    expected_count_by_actor: tuple[tuple[int, int], ...]
    observed_count_by_actor: tuple[tuple[int, int], ...]
    missing_actor_rows: tuple[tuple[str, int, int, int, int, int], ...]
    unexpected_actor_rows: tuple[tuple[str, int, int, int, int, int], ...]
    duplicate_observed_rows: tuple[tuple[str, int, int, int, int, int], ...]
    exact_match: bool
    schema_version: str = "b2r5_actor_evidence_reconciliation_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


def _canonical_actor_evidence_rows_v1(
    value: object,
    *,
    field_name: str,
    update_id: str,
    actor_ids: tuple[int, ...],
) -> tuple[tuple[str, int, int, int, int, int], ...]:
    if type(value) is not tuple:
        _fail(
            "actor evidence rows require one immutable tuple",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            field_name=field_name,
            expected="tuple[(update_id, actor_id, slot, env_id, episode_generation, transition_generation)]",
            observed=type(value),
        )
    rows = tuple(value)
    if any(
        type(row) is not tuple
        or len(row) != 6
        or type(row[0]) is not str
        or not row[0]
        or any(type(item) is not int or item < 0 for item in row[1:5])
        or type(row[5]) is not int
        or row[5] < -1
        for row in rows
    ):
        _fail(
            "actor evidence row identity is malformed",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            field_name=field_name,
            expected="exact actor row identity tuples with transition generation >= -1",
            observed=rows,
        )
    wrong_updates = tuple(row for row in rows if row[0] != update_id)
    if wrong_updates:
        _fail(
            "actor evidence belongs to a stale or wrong update",
            stop_code=STOP_ACTOR_EVIDENCE_UPDATE_ID_MISMATCH,
            stage="actor_evidence_reconciliation",
            field_name=field_name,
            expected=update_id,
            observed=wrong_updates,
        )
    wrong_actors = tuple(row for row in rows if row[1] not in actor_ids)
    if wrong_actors:
        _fail(
            "actor evidence row references an actor outside the resolved authority",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            field_name=field_name,
            expected=actor_ids,
            observed=wrong_actors,
        )
    return rows


def _duplicate_actor_evidence_rows_v1(
    rows: tuple[tuple[str, int, int, int, int, int], ...]
) -> tuple[tuple[str, int, int, int, int, int], ...]:
    seen: set[tuple[str, int, int, int, int, int]] = set()
    duplicates: list[tuple[str, int, int, int, int, int]] = []
    for row in rows:
        if row in seen and row not in duplicates:
            duplicates.append(row)
        seen.add(row)
    return tuple(duplicates)


def reconcile_actor_evidence_v1(
    *,
    update_id: str,
    actor_ids: tuple[int, ...],
    expected_actor_rows: tuple[tuple[str, int, int, int, int, int], ...],
    observed_actor_rows: tuple[tuple[str, int, int, int, int, int], ...],
) -> B2R5ActorEvidenceReconciliationV1:
    """Require an exact canonical active-and-DVM actor-evidence population."""

    if type(update_id) is not str or not update_id or type(actor_ids) is not tuple:
        _fail(
            "actor evidence reconciliation authority is malformed",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            expected="nonempty update ID and exact actor-ID tuple",
            observed=(update_id, actor_ids),
        )
    if (
        any(type(actor_id) is not int or actor_id < 0 for actor_id in actor_ids)
        or len(actor_ids) != len(set(actor_ids))
    ):
        _fail(
            "actor evidence reconciliation actor authority is invalid",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            expected="unique nonnegative actor IDs",
            observed=actor_ids,
        )
    expected = _canonical_actor_evidence_rows_v1(
        expected_actor_rows,
        field_name="expected_actor_rows",
        update_id=update_id,
        actor_ids=actor_ids,
    )
    observed = _canonical_actor_evidence_rows_v1(
        observed_actor_rows,
        field_name="observed_actor_rows",
        update_id=update_id,
        actor_ids=actor_ids,
    )
    duplicate_expected = _duplicate_actor_evidence_rows_v1(expected)
    if duplicate_expected:
        _fail(
            "canonical expected actor evidence contains duplicate rows",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            field_name="expected_actor_rows",
            observed=duplicate_expected,
        )
    duplicates = _duplicate_actor_evidence_rows_v1(observed)
    if duplicates:
        _fail(
            "observed actor evidence contains duplicate rows",
            stop_code=STOP_ACTOR_EVIDENCE_DUPLICATE,
            stage="actor_evidence_reconciliation",
            field_name="observed_actor_rows",
            observed=duplicates,
        )
    expected_set = set(expected)
    observed_set = set(observed)
    missing = tuple(sorted(expected_set - observed_set))
    unexpected = tuple(sorted(observed_set - expected_set))
    if missing and unexpected:
        _fail(
            "actor evidence counts may match but canonical row identities differ",
            stop_code=STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            stage="actor_evidence_reconciliation",
            expected=missing,
            observed=unexpected,
        )
    if missing:
        _fail(
            "canonical actor evidence rows are missing",
            stop_code=STOP_ACTOR_EVIDENCE_MISSING,
            stage="actor_evidence_reconciliation",
            expected=missing,
            observed=observed,
        )
    if unexpected:
        _fail(
            "unexpected actor evidence rows were supplied",
            stop_code=STOP_ACTOR_EVIDENCE_UNEXPECTED,
            stage="actor_evidence_reconciliation",
            expected=expected,
            observed=unexpected,
        )
    expected_counts = tuple(
        (actor_id, sum(int(row[1] == actor_id) for row in expected))
        for actor_id in actor_ids
    )
    observed_counts = tuple(
        (actor_id, sum(int(row[1] == actor_id) for row in observed))
        for actor_id in actor_ids
    )
    return B2R5ActorEvidenceReconciliationV1(
        update_id=update_id,
        actor_ids=actor_ids,
        expected_actor_rows=expected,
        observed_actor_rows=observed,
        expected_count_by_actor=expected_counts,
        observed_count_by_actor=observed_counts,
        missing_actor_rows=(),
        unexpected_actor_rows=(),
        duplicate_observed_rows=(),
        exact_match=True,
    )


def _canonical_terminal_keys_v1(
    value: object, *, field_name: str
) -> tuple[tuple[int, int, int], ...]:
    if type(value) is not tuple:
        _fail(
            "terminal evidence keys require one immutable tuple",
            stop_code=STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH,
            stage="terminal_evidence_reconciliation",
            field_name=field_name,
            expected="tuple[(env_id, episode_generation, transition_generation)]",
            observed=type(value),
        )
    keys = tuple(value)
    if any(
        type(key) is not tuple
        or len(key) != 3
        or any(type(item) is not int or item < 0 for item in key)
        for key in keys
    ):
        _fail(
            "terminal evidence key identity is malformed",
            stop_code=STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH,
            stage="terminal_evidence_reconciliation",
            field_name=field_name,
            expected="nonnegative exact (env, episode, transition) tuples",
            observed=keys,
        )
    return keys


def _duplicate_terminal_keys_v1(
    keys: tuple[tuple[int, int, int], ...]
) -> tuple[tuple[int, int, int], ...]:
    seen: set[tuple[int, int, int]] = set()
    duplicates: list[tuple[int, int, int]] = []
    for key in keys:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return tuple(sorted(duplicates))


def reconcile_terminal_evidence_v1(
    *,
    expected_terminal_keys: tuple[tuple[int, int, int], ...],
    observed_terminal_keys: tuple[tuple[int, int, int], ...],
) -> B2R5TerminalEvidenceReconciliationV1:
    """Require an exact terminal-key match while accepting valid empty/empty."""

    expected = _canonical_terminal_keys_v1(
        expected_terminal_keys, field_name="expected_terminal_keys"
    )
    observed = _canonical_terminal_keys_v1(
        observed_terminal_keys, field_name="observed_terminal_keys"
    )
    expected_duplicates = _duplicate_terminal_keys_v1(expected)
    observed_duplicates = _duplicate_terminal_keys_v1(observed)
    if expected_duplicates:
        _fail(
            "authoritative terminal rows produced duplicate identities",
            stop_code=STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH,
            stage="terminal_evidence_reconciliation",
            field_name="expected_terminal_keys",
            expected="unique authoritative terminal identities",
            observed=expected_duplicates,
        )
    if observed_duplicates:
        _fail(
            "observed terminal evidence contains duplicate identities",
            stop_code=STOP_TERMINAL_EVIDENCE_DUPLICATE,
            stage="terminal_evidence_reconciliation",
            field_name="observed_terminal_keys",
            expected="unique consumed terminal identities",
            observed=observed_duplicates,
        )
    expected_set = set(expected)
    observed_set = set(observed)
    missing = tuple(sorted(expected_set - observed_set))
    unexpected = tuple(sorted(observed_set - expected_set))
    if missing and unexpected:
        missing_envs = tuple(sorted(key[0] for key in missing))
        unexpected_envs = tuple(sorted(key[0] for key in unexpected))
        generation_only = (
            len(missing) == len(unexpected)
            and missing_envs == unexpected_envs
        )
        _fail(
            "terminal evidence generation differs from authoritative rows"
            if generation_only
            else "terminal evidence identities do not match authoritative rows",
            stop_code=(
                STOP_TERMINAL_GENERATION_MISMATCH
                if generation_only
                else STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH
            ),
            stage="terminal_evidence_reconciliation",
            expected=tuple(sorted(expected)),
            observed=tuple(sorted(observed)),
        )
    if missing:
        _fail(
            "required terminal historical evidence is missing",
            stop_code=STOP_TERMINAL_EVIDENCE_MISSING,
            stage="terminal_evidence_reconciliation",
            expected=missing,
            observed=tuple(sorted(observed)),
        )
    if unexpected:
        _fail(
            "terminal evidence exists for no authoritative terminal row",
            stop_code=STOP_TERMINAL_EVIDENCE_UNEXPECTED,
            stage="terminal_evidence_reconciliation",
            expected=tuple(sorted(expected)),
            observed=unexpected,
        )
    canonical_expected = tuple(sorted(expected))
    canonical_observed = tuple(sorted(observed))
    return B2R5TerminalEvidenceReconciliationV1(
        expected_terminal_keys=canonical_expected,
        observed_terminal_keys=canonical_observed,
        expected_count=len(expected),
        observed_count=len(observed),
        unique_expected_count=len(expected_set),
        unique_observed_count=len(observed_set),
        missing_terminal_keys=(),
        unexpected_terminal_keys=(),
        duplicate_observed_keys=(),
        exact_match=True,
    )


@dataclass(frozen=True, slots=True)
class B2R5ImmutableUpdatePlanV1:
    update_id: str
    authority_config_digest: str
    actor_order: tuple[int, ...]
    actor_plan_digest: str
    critic_plan_digest: str
    actor_expected_backward: tuple[tuple[int, int], ...]
    actor_expected_step: tuple[tuple[int, int], ...]
    critic_expected_backward: int
    critic_expected_step: int
    valuenorm_expected_update: int
    lifecycle_evidence_digest: str
    returns_evidence_digest: str
    initial_component_state_digest: str
    initial_factor_digest: str
    expected_stage_progression: tuple[B2RUpdateStageV1, ...]
    schema_version: str = "b2r5_immutable_update_plan_v1"

    def __post_init__(self) -> None:
        if self.expected_stage_progression != _EXPECTED_STAGES:
            _fail("R5 plan does not freeze S0-S10", stop_code=STOP_MODE_ORDER, stage="r5_plan")

    @property
    def plan_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5ModeReceiptV1:
    operation: str
    actor_modes_before: tuple[bool, ...]
    actor_modes_after: tuple[bool, ...]
    critic_mode_before: bool
    critic_mode_after: bool
    gradients_clean: bool
    schema_version: str = "b2r5_mode_receipt_v1"


@dataclass(frozen=True, slots=True)
class B2R5RolloverEvidenceV1:
    operation_order: tuple[str, ...]
    critic_rollover_count: int
    terminal_ledger_reset_count: int
    actor_storage_rollover_count: int
    critic_pre_digest: str
    critic_post_digest: str
    terminal_keys_before: tuple[tuple[int, int, int], ...]
    terminal_keys_after: tuple[tuple[int, int, int], ...]
    actor_pre_digests: tuple[str, ...]
    actor_post_digests: tuple[str, ...]
    final_current_slot_reused: tuple[bool, ...]
    schema_version: str = "b2r5_rollover_evidence_v1"


@dataclass(frozen=True, slots=True)
class B2RFullUpdateQuiescenceEvidenceV1:
    update_id: str
    gradients_clean: bool
    pending_backward_permits: int
    pending_optimizer_permits: int
    pending_valuenorm_permits: int
    unconsumed_terminal_keys: int
    incomplete_actor_receipts: int
    incomplete_critic_receipts: int
    route_poisoned: bool
    actor_modes_rollout: bool
    critic_mode_rollout: bool
    critic_cursor_reset: bool
    actor_cursors_reset: bool
    event_returns_compute_once_reset: bool
    next_rollout_guards_established: bool
    checkpoint_boundary_eligible_by_state_machine: bool
    schema_version: str = "b2r_full_update_quiescence_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5FailureEvidenceV1:
    stop_code: str
    failed_stage: B2RUpdateStageV1
    partial_update: bool
    route_poisoned: bool
    actor_steps_before_failure: int
    critic_steps_before_failure: int
    valuenorm_updates_before_failure: int
    rollover_allowed: bool
    ledger_reset_allowed: bool
    checkpoint_allowed: bool
    next_rollout_allowed: bool
    public_use_allowed: bool
    s10_reached: bool
    schema_version: str = "b2r5_failure_evidence_v1"


class B2R5TransactionRouteStateV1:
    __slots__ = ("machine", "route_poisoned", "last_failure")

    def __init__(self) -> None:
        self.machine = B2RUpdateStateMachineV1()
        self.route_poisoned = False
        self.last_failure: B2R5FailureEvidenceV1 | None = None

    def record_failure(
        self,
        *,
        stop_code: str,
        actor_steps: int,
        critic_steps: int,
        valuenorm_updates: int,
    ) -> None:
        partial = actor_steps > 0 or critic_steps > 0 or valuenorm_updates > 0
        if partial:
            self.machine.poison()
            self.route_poisoned = True
        self.last_failure = B2R5FailureEvidenceV1(
            stop_code=stop_code,
            failed_stage=self.machine.current,
            partial_update=partial,
            route_poisoned=self.route_poisoned,
            actor_steps_before_failure=actor_steps,
            critic_steps_before_failure=critic_steps,
            valuenorm_updates_before_failure=valuenorm_updates,
            rollover_allowed=False,
            ledger_reset_allowed=False,
            checkpoint_allowed=False,
            next_rollout_allowed=not partial,
            public_use_allowed=False,
            s10_reached=False,
        )


class B2R5ExecutionCounterV1:
    __slots__ = (
        "actor_backward_by_actor", "actor_step_by_actor",
        "critic_backward_executed", "critic_step_executed",
        "live_valuenorm_executed", "training_mode_entries",
        "rollout_mode_restorations", "critic_rollovers",
        "terminal_ledger_resets", "actor_storage_rollovers",
        "s10_entries", "successful_transactions",
    )

    def __init__(self, resolved_M: int) -> None:
        self.actor_backward_by_actor = [0] * resolved_M
        self.actor_step_by_actor = [0] * resolved_M
        self.critic_backward_executed = 0
        self.critic_step_executed = 0
        self.live_valuenorm_executed = 0
        self.training_mode_entries = 0
        self.rollout_mode_restorations = 0
        self.critic_rollovers = 0
        self.terminal_ledger_resets = 0
        self.actor_storage_rollovers = 0
        self.s10_entries = 0
        self.successful_transactions = 0

    @property
    def actor_backward_executed(self) -> int:
        return sum(self.actor_backward_by_actor)

    @property
    def actor_step_executed(self) -> int:
        return sum(self.actor_step_by_actor)


class B2R5RolloverOrderV1:
    __slots__ = ("critic_done", "ledger_done", "actor_done")

    def __init__(self) -> None:
        self.critic_done = False
        self.ledger_done = False
        self.actor_done = 0

    def record_critic_rollover(self) -> None:
        if self.critic_done or self.ledger_done or self.actor_done:
            _fail("critic rollover is out of order", stop_code=STOP_ROLLOVER_ORDER, stage="r5_rollover")
        self.critic_done = True

    def record_terminal_reset(self) -> None:
        if not self.critic_done or self.ledger_done or self.actor_done:
            _fail("terminal ledger reset requires critic rollover", stop_code=STOP_ROLLOVER_ORDER, stage="r5_rollover")
        self.ledger_done = True

    def record_actor_rollover(self) -> None:
        if not self.critic_done or not self.ledger_done:
            _fail("actor rollover requires terminal reset", stop_code=STOP_ROLLOVER_ORDER, stage="r5_rollover")
        self.actor_done += 1

    def require_complete(self, expected_actors: int) -> None:
        if not self.critic_done or not self.ledger_done or self.actor_done != expected_actors:
            _fail("rollover sequence is incomplete", stop_code=STOP_ROLLOVER_ORDER, stage="r5_rollover", expected=(True, True, expected_actors), observed=(self.critic_done, self.ledger_done, self.actor_done))


@dataclass(frozen=True, slots=True)
class B2RFullLearnerUpdateEvidenceV1:
    authority_digest: str
    immutable_plan_digest: str
    rollout_complete_digest: str
    actor_sequence_receipt: R3.B2R3SequenceReceiptV1
    critic_sequence_receipt: R4.B2R4CriticSequenceReceiptV1
    mode_entry_receipt: B2R5ModeReceiptV1
    mode_restore_receipt: B2R5ModeReceiptV1
    rollover_evidence: B2R5RolloverEvidenceV1
    quiescence_evidence: B2RFullUpdateQuiescenceEvidenceV1
    ordering_evidence: B2ROrderingEvidenceV1
    actor_parameter_mutation_by_actor: tuple[tuple[int, bool], ...]
    critic_parameter_mutated: bool
    live_valuenorm_mutated: bool
    frozen_inputs_unchanged: bool
    transaction_success: bool
    retained_nonclaims: tuple[str, ...]
    schema_version: str = "b2r_full_learner_update_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


def validate_rollout_complete_v1(
    *,
    authority: B2R5FullUpdateAuthorityV1,
    rollout: B2R5RolloutCompleteEvidenceV1,
    rollover_resources: object,
) -> None:
    config = authority.base_authority.resolved_config
    actor_storages = tuple(rollover_resources.actor_storages)
    buffer = rollover_resources.critic_buffer
    keys = tuple(rollover_resources.terminal_collector.consumed_terminal_keys)
    terminal_reconciliation = reconcile_terminal_evidence_v1(
        expected_terminal_keys=rollout.expected_terminal_keys,
        observed_terminal_keys=keys,
    )
    actor_reconciliation = reconcile_actor_evidence_v1(
        update_id=rollout.update_id,
        actor_ids=tuple(range(config.resolved_M)),
        expected_actor_rows=rollout.actor_evidence_expected_rows,
        observed_actor_rows=rollout.actor_evidence_observed_rows,
    )
    actual_final = tuple((index, storage.final_current_slot_digest) for index, storage in enumerate(actor_storages))
    if (
        rollout.update_id != authority.update_id
        or rollout.authority_config_digest != authority.config_digest
        or (rollout.resolved_T, rollout.resolved_E, rollout.resolved_M, rollout.resolved_N)
        != (config.resolved_T, config.resolved_E, config.resolved_M, config.resolved_N)
        or len(actor_storages) != config.resolved_M
        or rollout.actor_storage_complete != tuple(True for _ in actor_storages)
        or tuple(storage.next_action_slot for storage in actor_storages) != tuple(config.resolved_T for _ in actor_storages)
        or not bool(buffer._event_slot_written.all().item())
        or not bool(buffer._event_returns_computed)
        or rollout.actor_buffer_cursors != tuple(config.resolved_T for _ in actor_storages)
        or rollout.critic_buffer_cursor != buffer.step
        or rollout.terminal_consumption_keys != keys
        or rollout.terminal_reconciliation_digest
        != terminal_reconciliation.evidence_digest
        or rollout.actor_evidence_reconciliation_digest
        != actor_reconciliation.evidence_digest
        or rollout.current_final_slot_digest_by_actor != actual_final
        or not all((rollout.critic_transition_storage_complete, rollout.terminal_learner_evidence_complete,
                    rollout.terminal_evidence_is_historical_pre_reset,
                    rollout.runtime_ack_is_separate_from_learner_consumption,
                    rollout.final_value_evaluated, rollout.selected_termination_domain_valid))
        or rollout.event_returns_compute_count != 1
    ):
        _fail("controlled rollout evidence is incomplete", stop_code=STOP_ROLLOUT_INCOMPLETE, stage="S0_ROLLOUT_COMPLETE")


def validate_immutable_plan_v1(
    *,
    authority: B2R5FullUpdateAuthorityV1,
    plan: B2R5ImmutableUpdatePlanV1,
    actor_plan: B2RActorUpdatePlanV1,
    critic_plan: B2RCriticUpdatePlanV1,
    initial_factor: torch.Tensor,
    current_component_digest: str,
) -> None:
    if (
        plan.update_id != authority.update_id
        or plan.authority_config_digest != authority.config_digest
        or plan.actor_order != authority.actor_authority.order_evidence.actor_order
        or plan.actor_plan_digest != actor_plan.plan_digest
        or plan.critic_plan_digest != critic_plan.plan_digest
        or plan.actor_expected_backward != actor_plan.expected_backward_count_by_actor
        or plan.actor_expected_step != actor_plan.expected_optimizer_step_count_by_actor
        or plan.critic_expected_backward != critic_plan.expected_backward_count
        or plan.critic_expected_step != critic_plan.expected_optimizer_step_count
        or plan.valuenorm_expected_update != critic_plan.expected_valuenorm_update_count
        or plan.initial_factor_digest != fingerprint_tensor_v1(initial_factor).content_digest
        or plan.initial_component_state_digest != current_component_digest
    ):
        _fail("immutable full update plan drifted", stop_code=STOP_AUTHORITY_DRIFT, stage="S3_UPDATE_PLAN_FROZEN")


def validate_post_update_audit_v1(
    *,
    plan: B2R5ImmutableUpdatePlanV1,
    actor_receipt: R3.B2R3SequenceReceiptV1,
    critic_receipt: R4.B2R4CriticSequenceReceiptV1,
    initial_states: tuple[tuple[tuple[str, str], ...], tuple[str, str], str],
    final_states: tuple[tuple[tuple[str, str], ...], tuple[str, str], str],
    frozen_digest_before: str,
    frozen_digest_after: str,
    terminal_keys_before: tuple[tuple[int, int, int], ...],
    terminal_keys_after: tuple[tuple[int, int, int], ...],
    actors: Sequence[object],
    critic: object,
) -> tuple[tuple[int, bool], ...]:
    expected_actor = dict(plan.actor_expected_step)
    observed_actor = {item.actor_id: item.observed_step_count for item in actor_receipt.actor_segments}
    observed_backward = tuple(
        sorted((item.actor_id, item.observed_backward_count) for item in actor_receipt.actor_segments)
    )
    observed_steps = tuple(
        sorted((item.actor_id, item.observed_step_count) for item in actor_receipt.actor_segments)
    )
    mutation = tuple(
        (actor_id, final_states[0][actor_id] != initial_states[0][actor_id])
        for actor_id in range(len(initial_states[0]))
    )
    expected_mutation = tuple((actor_id, count > 0) for actor_id, count in sorted(expected_actor.items()))
    if (
        observed_actor != expected_actor
        or observed_backward != plan.actor_expected_backward
        or observed_steps != plan.actor_expected_step
        or critic_receipt.observed_backward_count != plan.critic_expected_backward
        or critic_receipt.observed_step_count != plan.critic_expected_step
        or critic_receipt.observed_valuenorm_count != plan.valuenorm_expected_update
        or mutation != expected_mutation
        or final_states[1] == initial_states[1]
        or (plan.valuenorm_expected_update > 0 and final_states[2] == initial_states[2])
        or frozen_digest_before != frozen_digest_after
        or terminal_keys_before != terminal_keys_after
    ):
        _fail("full post-update audit failed", stop_code=STOP_MUTATION_ATTRIBUTION, stage="S7_POST_UPDATE_AUDIT")
    _validate_all_gradients_clear(actors, critic)
    return mutation


def validate_quiescence_claim_v1(evidence: B2RFullUpdateQuiescenceEvidenceV1) -> None:
    if not (
        evidence.gradients_clean
        and evidence.pending_backward_permits == 0
        and evidence.pending_optimizer_permits == 0
        and evidence.pending_valuenorm_permits == 0
        and evidence.unconsumed_terminal_keys == 0
        and evidence.incomplete_actor_receipts == 0
        and evidence.incomplete_critic_receipts == 0
        and not evidence.route_poisoned
        and evidence.actor_modes_rollout
        and evidence.critic_mode_rollout
        and evidence.critic_cursor_reset
        and evidence.actor_cursors_reset
        and evidence.event_returns_compute_once_reset
        and evidence.next_rollout_guards_established
        and evidence.checkpoint_boundary_eligible_by_state_machine
    ):
        _fail("S10 quiescence claim is incomplete", stop_code=STOP_CHECKPOINT_BOUNDARY, stage="S10_QUIESCENT")


def _enter_training_mode_v1(actors: Sequence[object], critic: object) -> B2R5ModeReceiptV1:
    before_actor, before_critic = _module_modes(actors, critic)
    for actor in actors:
        actor.actor.train()
    critic.critic.train()
    after_actor, after_critic = _module_modes(actors, critic)
    if not all(after_actor) or not after_critic:
        _fail("training mode entry failed", stop_code=STOP_MODE_ORDER, stage="S4_TRAINING_MODE_ENTERED")
    _validate_all_gradients_clear(actors, critic)
    return B2R5ModeReceiptV1("enter_training", before_actor, after_actor, before_critic, after_critic, True)


def _restore_rollout_mode_v1(actors: Sequence[object], critic: object) -> B2R5ModeReceiptV1:
    before_actor, before_critic = _module_modes(actors, critic)
    for actor in actors:
        actor.actor.eval()
    critic.critic.eval()
    after_actor, after_critic = _module_modes(actors, critic)
    if any(after_actor) or after_critic:
        _fail("rollout mode restoration failed", stop_code=STOP_MODE_ORDER, stage="S8_ROLLOUT_MODE_RESTORED")
    _validate_all_gradients_clear(actors, critic)
    return B2R5ModeReceiptV1("restore_rollout", before_actor, after_actor, before_critic, after_critic, True)


def _execute_actor_segment_v1(
    *, authority: B2R5FullUpdateAuthorityV1, frozen_inputs: B2RFrozenTrainingInputsV1,
    actor_plan: B2RActorUpdatePlanV1, actors: Sequence[object], critic: object,
    live_value_normalizer: object, actor_inputs: Mapping[int, R3.B2R3ActorInputsV1],
    initial_factor: torch.Tensor, counter: B2R5ExecutionCounterV1,
    synthetic_fault_actor: int | None,
) -> R3.B2R3SequenceReceiptV1:
    local = R3.B2R3ExecutionCounterV1(len(actors))
    try:
        return R3.execute_actor_sequence_v1(
            authority=authority.actor_authority, frozen_inputs=frozen_inputs,
            actor_plan=actor_plan, actors=actors, critic=critic,
            live_value_normalizer=live_value_normalizer, actor_inputs=actor_inputs,
            initial_factor=initial_factor, route_state=R3.B2R3RouteStateV1(),
            counter=local, synthetic_post_step_fault_actor=synthetic_fault_actor,
        )
    finally:
        for index in range(len(actors)):
            counter.actor_backward_by_actor[index] += local.actor_backward_by_actor[index]
            counter.actor_step_by_actor[index] += local.actor_step_by_actor[index]


def _execute_critic_segment_v1(
    *, authority: B2R5FullUpdateAuthorityV1, frozen_inputs: B2RFrozenTrainingInputsV1,
    critic_plan: B2RCriticUpdatePlanV1, actors: Sequence[object], critic: object,
    live_value_normalizer: object, critic_inputs: R4.B2R4CriticInputsV1,
    counter: B2R5ExecutionCounterV1, synthetic_fault: str | None,
) -> R4.B2R4CriticSequenceReceiptV1:
    local = R4.B2R4ExecutionCounterV1()
    try:
        return R4.execute_critic_sequence_v1(
            authority=authority.critic_authority, frozen_inputs=frozen_inputs,
            critic_plan=critic_plan, actors=actors, critic=critic,
            live_value_normalizer=live_value_normalizer, inputs=critic_inputs,
            route_state=R4.B2R4RouteStateV1(), counter=local,
            synthetic_fault=synthetic_fault,
        )
    finally:
        counter.critic_backward_executed += local.critic_backward_executed
        counter.critic_step_executed += local.critic_step_executed
        counter.live_valuenorm_executed += local.live_valuenorm_executed


def execute_full_learner_transaction_v1(
    *,
    authority: B2R5FullUpdateAuthorityV1,
    rollout_evidence: B2R5RolloutCompleteEvidenceV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    immutable_plan: B2R5ImmutableUpdatePlanV1,
    actor_plan: B2RActorUpdatePlanV1,
    critic_plan: B2RCriticUpdatePlanV1,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    actor_inputs: Mapping[int, R3.B2R3ActorInputsV1],
    initial_factor: torch.Tensor,
    critic_inputs: R4.B2R4CriticInputsV1,
    event_returns_result: torch.Tensor,
    rollover_resources: object,
    route_state: B2R5TransactionRouteStateV1,
    counter: B2R5ExecutionCounterV1,
    synthetic_fault: str | None = None,
) -> B2RFullLearnerUpdateEvidenceV1:
    """Execute one complete private CPU R5 transaction through S10."""

    start_actor = counter.actor_step_executed
    start_critic = counter.critic_step_executed
    start_vn = counter.live_valuenorm_executed
    frozen_before = canonical_digest_v1(frozen_inputs)
    initial_states = _parameter_optimizer_digests(actors, critic, live_value_normalizer)
    initial_component_digest = _component_state_digest(actors, critic, live_value_normalizer)
    terminal_keys_before = tuple(rollover_resources.terminal_collector.consumed_terminal_keys)
    try:
        if route_state.machine.current is not B2RUpdateStageV1.S0_ROLLOUT_COMPLETE or route_state.route_poisoned:
            _fail("transaction did not start at fresh S0", stop_code=STOP_MODE_ORDER, stage="S0_ROLLOUT_COMPLETE")
        if synthetic_fault == "pre_mutation":
            _fail("controlled pre-mutation rejection", stop_code=STOP_ROLLOUT_INCOMPLETE, stage="S0_ROLLOUT_COMPLETE")
        validate_rollout_complete_v1(authority=authority, rollout=rollout_evidence, rollover_resources=rollover_resources)

        route_state.machine.transition(B2RUpdateStageV1.S1_FINAL_VALUE_EVALUATED)
        if not rollout_evidence.final_value_evaluated or not rollout_evidence.terminal_evidence_is_historical_pre_reset:
            _fail("final/terminal evidence is invalid", stop_code=STOP_ROLLOUT_INCOMPLETE, stage="S1_FINAL_VALUE_EVALUATED")

        route_state.machine.transition(B2RUpdateStageV1.S2_EVENT_RETURNS_FROZEN)
        target = critic_inputs.returns_storage[:-1]
        if (
            event_returns_result.data_ptr() == target.data_ptr()
            or not torch.equal(event_returns_result, target)
            or not bool(torch.isfinite(target).all().item())
            or fingerprint_tensor_v1(target.reshape(-1, 1)).content_digest != critic_plan.raw_target_digest
        ):
            _fail("frozen event return identity failed", stop_code=STOP_CRITIC_TRAINING_SLICE, stage="S2_EVENT_RETURNS_FROZEN")

        route_state.machine.transition(B2RUpdateStageV1.S3_UPDATE_PLAN_FROZEN)
        validate_immutable_plan_v1(
            authority=authority, plan=immutable_plan, actor_plan=actor_plan,
            critic_plan=critic_plan, initial_factor=initial_factor,
            current_component_digest=initial_component_digest,
        )

        route_state.machine.transition(B2RUpdateStageV1.S4_TRAINING_MODE_ENTERED)
        mode_entry = _enter_training_mode_v1(actors, critic)
        counter.training_mode_entries += 1

        route_state.machine.transition(B2RUpdateStageV1.S5_ACTOR_SEQUENCE)
        actor_receipt = _execute_actor_segment_v1(
            authority=authority, frozen_inputs=frozen_inputs, actor_plan=actor_plan,
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer,
            actor_inputs=actor_inputs, initial_factor=initial_factor, counter=counter,
            synthetic_fault_actor=0 if synthetic_fault == "actor_post_step" else None,
        )

        route_state.machine.transition(B2RUpdateStageV1.S6_CRITIC_SEQUENCE)
        critic_fault = synthetic_fault if synthetic_fault in ("post_valuenorm", "post_step") else None
        critic_receipt = _execute_critic_segment_v1(
            authority=authority, frozen_inputs=frozen_inputs, critic_plan=critic_plan,
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer,
            critic_inputs=critic_inputs, counter=counter, synthetic_fault=critic_fault,
        )

        route_state.machine.transition(B2RUpdateStageV1.S7_POST_UPDATE_AUDIT)
        final_states = _parameter_optimizer_digests(actors, critic, live_value_normalizer)
        actor_mutation = validate_post_update_audit_v1(
            plan=immutable_plan, actor_receipt=actor_receipt, critic_receipt=critic_receipt,
            initial_states=initial_states, final_states=final_states,
            frozen_digest_before=frozen_before, frozen_digest_after=canonical_digest_v1(frozen_inputs),
            terminal_keys_before=terminal_keys_before,
            terminal_keys_after=tuple(rollover_resources.terminal_collector.consumed_terminal_keys),
            actors=actors, critic=critic,
        )
        if synthetic_fault == "post_update_audit":
            _fail("controlled S7 audit corruption", stop_code=STOP_MUTATION_ATTRIBUTION, stage="S7_POST_UPDATE_AUDIT")

        route_state.machine.transition(B2RUpdateStageV1.S8_ROLLOUT_MODE_RESTORED)
        mode_restore = _restore_rollout_mode_v1(actors, critic)
        counter.rollout_mode_restorations += 1

        buffer = rollover_resources.critic_buffer
        collector = rollover_resources.terminal_collector
        storages = tuple(rollover_resources.actor_storages)
        critic_pre = rollover_resources.critic_rollover_digest
        actor_pre = tuple(storage.storage_digest for storage in storages)
        final_slot_digests = tuple(storage.final_current_slot_digest for storage in storages)
        rollover_order = B2R5RolloverOrderV1()
        operation_order: list[str] = []
        buffer.after_update()
        rollover_order.record_critic_rollover()
        operation_order.append("critic_buffer.after_update")
        counter.critic_rollovers += 1
        collector.reset_consumption_ledger_after_buffer_update()
        rollover_order.record_terminal_reset()
        operation_order.append("terminal_ledger.reset")
        counter.terminal_ledger_resets += 1
        for storage in storages:
            storage.rollover_from_final_current_slot()
            rollover_order.record_actor_rollover()
            operation_order.append(f"actor_storage[{storage.actor_id}].rollover")
            counter.actor_storage_rollovers += 1
        rollover_order.require_complete(len(storages))
        route_state.machine.transition(B2RUpdateStageV1.S9_ROLLOVER_COMPLETE)
        actor_post = tuple(storage.storage_digest for storage in storages)
        final_reused = tuple(
            storage.slot_zero_digest == final_slot_digests[index]
            for index, storage in enumerate(storages)
        )
        rollover = B2R5RolloverEvidenceV1(
            operation_order=tuple(operation_order), critic_rollover_count=1,
            terminal_ledger_reset_count=1, actor_storage_rollover_count=len(storages),
            critic_pre_digest=critic_pre,
            critic_post_digest=rollover_resources.critic_rollover_digest,
            terminal_keys_before=terminal_keys_before,
            terminal_keys_after=tuple(collector.consumed_terminal_keys),
            actor_pre_digests=actor_pre, actor_post_digests=actor_post,
            final_current_slot_reused=final_reused,
        )

        route_state.machine.transition(B2RUpdateStageV1.S10_QUIESCENT)
        _validate_all_gradients_clear(actors, critic)
        actor_modes, critic_mode = _module_modes(actors, critic)
        ordering = route_state.machine.evidence(pending_permit_count=0)
        quiescence = B2RFullUpdateQuiescenceEvidenceV1(
            update_id=authority.update_id, gradients_clean=True,
            pending_backward_permits=0, pending_optimizer_permits=0,
            pending_valuenorm_permits=0,
            unconsumed_terminal_keys=len(collector.consumed_terminal_keys),
            incomplete_actor_receipts=0, incomplete_critic_receipts=0,
            route_poisoned=route_state.route_poisoned,
            actor_modes_rollout=not any(actor_modes), critic_mode_rollout=not critic_mode,
            critic_cursor_reset=(buffer.step == 0 and not bool(buffer._event_slot_written.any().item())),
            actor_cursors_reset=all(storage.next_action_slot == 0 for storage in storages),
            event_returns_compute_once_reset=not bool(buffer._event_returns_computed),
            next_rollout_guards_established=all(final_reused),
            checkpoint_boundary_eligible_by_state_machine=ordering.checkpoint_eligible,
        )
        validate_quiescence_claim_v1(quiescence)
        counter.s10_entries += 1
        counter.successful_transactions += 1
        return B2RFullLearnerUpdateEvidenceV1(
            authority_digest=authority.authority_digest,
            immutable_plan_digest=immutable_plan.plan_digest,
            rollout_complete_digest=rollout_evidence.evidence_digest,
            actor_sequence_receipt=actor_receipt,
            critic_sequence_receipt=critic_receipt,
            mode_entry_receipt=mode_entry, mode_restore_receipt=mode_restore,
            rollover_evidence=rollover, quiescence_evidence=quiescence,
            ordering_evidence=ordering,
            actor_parameter_mutation_by_actor=actor_mutation,
            critic_parameter_mutated=final_states[1] != initial_states[1],
            live_valuenorm_mutated=final_states[2] != initial_states[2],
            frozen_inputs_unchanged=True, transaction_success=True,
            retained_nonclaims=(
                "real_isaac_full_learner_integration_not_established",
                "training_update_readiness_not_yet_established",
                "checkpoint_weight_io_not_authorized",
                "public_learned_policy_route_dormant_blocked",
            ),
        )
    except B2RContractError as exc:
        route_state.record_failure(
            stop_code=exc.stop_code,
            actor_steps=counter.actor_step_executed - start_actor,
            critic_steps=counter.critic_step_executed - start_critic,
            valuenorm_updates=counter.live_valuenorm_executed - start_vn,
        )
        raise


__all__: tuple[str, ...] = ()
