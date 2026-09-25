"""Pure, read-only lifecycle decision-gating observer for Phase B2-T0-LD.

The observer does not derive lifecycle state.  It validates evidence copied
from the already-authoritative I1/I2 decision bundle and the I3a actor-call
record at one collection boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


STOP_POLICY_CALL_DURING_CONTINUATION = (
    "STOP — B2-T0 POLICY_CALL_DURING_CONTINUATION"
)
STOP_POLICY_CALL_DURING_NONDECISION = (
    "STOP — B2-T0 POLICY_CALL_DURING_NONDECISION"
)
STOP_MISSING_REQUIRED_POLICY_CALL = (
    "STOP — B2-T0 MISSING_REQUIRED_POLICY_CALL"
)
STOP_DUPLICATE_POLICY_CALL = "STOP — B2-T0 DUPLICATE_POLICY_CALL"
STOP_DECISION_EVIDENCE_MISMATCH = "STOP — B2-T0 DECISION_EVIDENCE_MISMATCH"

POLICY_DECISION_ROW = "POLICY_DECISION_ROW"
FORCED_CONTINUATION_ROW = "FORCED_CONTINUATION_ROW"
FORCED_NOOP_ROW = "FORCED_NOOP_ROW"
_ROW_KINDS = frozenset(
    (POLICY_DECISION_ROW, FORCED_CONTINUATION_ROW, FORCED_NOOP_ROW)
)


class LifecycleDecisionGateError(RuntimeError):
    """Precise fail-closed decision-gating qualification error."""

    def __init__(self, stop_code: str, row: "LifecycleDecisionRowEvidence") -> None:
        self.stop_code = stop_code
        self.row = row
        super().__init__(
            f"{stop_code}: env={row.env_index}, robot={row.robot_index}, "
            f"collection={row.collection_index}, physical_step={row.physical_step_index}"
        )


@dataclass(frozen=True, slots=True)
class LifecycleDecisionRowEvidence:
    """Small immutable row copied from existing I1/I2/I3a evidence."""

    collection_index: int
    physical_step_index: int
    env_index: int
    robot_index: int
    episode_generation: int
    transition_generation: int
    lifecycle_state: str
    current_owned_task_id: int | None
    decision_required: bool
    decision_reason: str
    actor_policy_call_count: int
    proposal_produced: bool
    behavior_logprob_produced: bool
    continuation_used: bool
    terminal_autoreset_context: str
    ownership_before: int | None
    ownership_after: int | None

    @property
    def decision_identity(self) -> tuple[int, int, int, int, int]:
        return (
            self.episode_generation,
            self.transition_generation,
            self.collection_index,
            self.env_index,
            self.robot_index,
        )


@dataclass(frozen=True, slots=True)
class LifecycleDecisionGateReceipt:
    """Immutable PASS receipt for exactly one collection boundary."""

    collection_index: int
    physical_step_index: int
    decision_identities: tuple[tuple[int, int, int, int, int], ...]
    policy_call_counts: tuple[int, ...]
    decision_required: tuple[bool, ...]
    rows: tuple[LifecycleDecisionRowEvidence, ...]
    observer_mutations: int = 0
    classification: str = "PASS"

    def to_mapping(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "collection_index": self.collection_index,
            "physical_step_index": self.physical_step_index,
            "decision_identities": self.decision_identities,
            "policy_call_counts": self.policy_call_counts,
            "decision_required": self.decision_required,
            "observer_mutations": self.observer_mutations,
            "rows": tuple(asdict(row) for row in self.rows),
        }


def qualify_lifecycle_decision_boundary(
    rows: tuple[LifecycleDecisionRowEvidence, ...],
) -> LifecycleDecisionGateReceipt:
    """Validate DVM-derived eligibility against actual per-row call evidence."""

    if type(rows) is not tuple or not rows:
        raise TypeError("rows must be one non-empty exact tuple")
    first = rows[0]
    identities: set[tuple[int, int, int, int, int]] = set()
    for row in rows:
        if type(row) is not LifecycleDecisionRowEvidence:
            raise TypeError("every row must be exact LifecycleDecisionRowEvidence")
        if (
            row.collection_index != first.collection_index
            or row.physical_step_index != first.physical_step_index
            or row.decision_reason not in _ROW_KINDS
            or type(row.actor_policy_call_count) is not int
            or row.actor_policy_call_count < 0
            or row.decision_identity in identities
        ):
            raise LifecycleDecisionGateError(STOP_DECISION_EVIDENCE_MISMATCH, row)
        identities.add(row.decision_identity)

        source_requires = row.decision_reason == POLICY_DECISION_ROW
        source_continues = row.decision_reason == FORCED_CONTINUATION_ROW
        if (
            row.decision_required is not source_requires
            or row.continuation_used is not source_continues
        ):
            raise LifecycleDecisionGateError(STOP_DECISION_EVIDENCE_MISMATCH, row)

        if row.decision_required:
            if row.actor_policy_call_count == 0:
                raise LifecycleDecisionGateError(
                    STOP_MISSING_REQUIRED_POLICY_CALL, row
                )
            if row.actor_policy_call_count > 1:
                raise LifecycleDecisionGateError(STOP_DUPLICATE_POLICY_CALL, row)
        elif row.actor_policy_call_count:
            raise LifecycleDecisionGateError(
                STOP_POLICY_CALL_DURING_CONTINUATION
                if row.continuation_used
                else STOP_POLICY_CALL_DURING_NONDECISION,
                row,
            )

        called_once = row.actor_policy_call_count == 1
        if (
            row.proposal_produced is not called_once
            or row.behavior_logprob_produced is not called_once
        ):
            raise LifecycleDecisionGateError(STOP_DECISION_EVIDENCE_MISMATCH, row)

    return LifecycleDecisionGateReceipt(
        collection_index=first.collection_index,
        physical_step_index=first.physical_step_index,
        decision_identities=tuple(row.decision_identity for row in rows),
        policy_call_counts=tuple(row.actor_policy_call_count for row in rows),
        decision_required=tuple(row.decision_required for row in rows),
        rows=rows,
    )


__all__ = (
    "FORCED_CONTINUATION_ROW",
    "FORCED_NOOP_ROW",
    "POLICY_DECISION_ROW",
    "STOP_DECISION_EVIDENCE_MISMATCH",
    "STOP_DUPLICATE_POLICY_CALL",
    "STOP_MISSING_REQUIRED_POLICY_CALL",
    "STOP_POLICY_CALL_DURING_CONTINUATION",
    "STOP_POLICY_CALL_DURING_NONDECISION",
    "LifecycleDecisionGateError",
    "LifecycleDecisionGateReceipt",
    "LifecycleDecisionRowEvidence",
    "qualify_lifecycle_decision_boundary",
)
