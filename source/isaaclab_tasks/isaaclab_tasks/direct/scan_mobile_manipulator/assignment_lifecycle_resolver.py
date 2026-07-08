"""Shared effective-assignment lifecycle resolver prototype.

This module implements a standalone, disabled-by-default prototype for
Contract C assignment semantics. It is not integrated into runtime paths in
Phase 9G-7B. When disabled, it is an absolute pass-through: proposals are
cloned into effective assignments and no lifecycle state is interpreted or
updated.

When enabled, the resolver owns behavior-driving prototype state and produces
effective assignments from standardized decoded proposals. It does not command
controllers, mutate assignment problems, generate masks, modify observations,
or know about raw HARL action encodings.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import torch


NO_TARGET = -1
NO_OWNER = -1
NO_ATTEMPT = -1
NO_REASON = -1

ROBOT_IDLE = 0
ROBOT_EXECUTING = 1

PAIR_NONE = 0
PAIR_ACTIVE = 1
PAIR_COMPLETED = 2
PAIR_FAILED_BUDGET = 3
PAIR_RELEASED_BUDGET = 4

REASON_NONE = -1
REASON_BUDGET_FAILURE = 1
REASON_COMPLETION = 2
REASON_RESET = 3

REJECT_NONE = 0
REJECT_INVALID_PROPOSAL = 1
REJECT_COVERED_TARGET = 2
REJECT_OWNED_TARGET = 3
REJECT_FAILED_PAIR = 4
REJECT_CLAIM_LOST = 5
REJECT_SWITCH_DISABLED = 6
REJECT_UNAVAILABLE_TARGET = 7

ROBOT_EXECUTION_STATE_NAMES = {
    ROBOT_IDLE: "idle",
    ROBOT_EXECUTING: "executing",
}

PAIR_STATE_NAMES = {
    PAIR_NONE: "none",
    PAIR_ACTIVE: "active",
    PAIR_COMPLETED: "completed",
    PAIR_FAILED_BUDGET: "failed_budget",
    PAIR_RELEASED_BUDGET: "released_budget",
}

REASON_NAMES = {
    REASON_NONE: "none",
    REASON_BUDGET_FAILURE: "budget_failure",
    REASON_COMPLETION: "completion",
    REASON_RESET: "reset",
}

PROPOSAL_REJECTED_REASON_NAMES = {
    REJECT_NONE: "none",
    REJECT_INVALID_PROPOSAL: "invalid_proposal",
    REJECT_COVERED_TARGET: "covered_target",
    REJECT_OWNED_TARGET: "owned_target",
    REJECT_FAILED_PAIR: "failed_pair",
    REJECT_CLAIM_LOST: "claim_lost",
    REJECT_SWITCH_DISABLED: "switch_disabled",
    REJECT_UNAVAILABLE_TARGET: "unavailable_target",
}

ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK = "lowest_path_cost_robot_id_tiebreak"
ARBITRATION_FALLBACK_ROBOT_ID = "robot_id_fallback_nonfinite_or_unavailable_cost"


@dataclass(frozen=True)
class AssignmentLifecycleResolverEvent:
    """Machine-readable resolver event."""

    event_type: str
    env_id: int
    step: int
    robot_id: int | None = None
    target_id: int | None = None
    method_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "event_type": str(self.event_type),
            "env_id": int(self.env_id),
            "step": int(self.step),
        }
        if self.robot_id is not None:
            data["robot_id"] = int(self.robot_id)
        if self.target_id is not None:
            data["target_id"] = int(self.target_id)
        if self.method_name is not None:
            data["method_name"] = str(self.method_name)
        data.update(_json_safe(self.details))
        return data


@dataclass(frozen=True)
class AssignmentLifecyclePreStepResult:
    """Deterministic pre-step resolver output."""

    effective_assignment: torch.Tensor
    proposal_accepted: torch.Tensor
    proposal_rejected_reason: torch.Tensor
    continued_from_active_target: torch.Tensor
    new_claim_started: torch.Tensor
    claim_conflict: torch.Tensor
    claim_winner: torch.Tensor
    claim_loser: torch.Tensor
    switch_requested: torch.Tensor
    switch_rejected: torch.Tensor
    behavior_changed: bool


@dataclass(frozen=True)
class AssignmentLifecyclePostStepResult:
    """Deterministic post-step resolver diagnostics."""

    completed: torch.Tensor
    released: torch.Tensor
    release_reason: torch.Tensor
    failure_reason: torch.Tensor
    reset_env_ids: list[int]
    behavior_changed: bool


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return _json_safe(value.item())
        return _json_safe(value.detach().cpu().tolist())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def _metadata_value(method_metadata: Mapping[str, Any] | object | None, key: str) -> Any:
    if method_metadata is None:
        return None
    if isinstance(method_metadata, Mapping):
        return method_metadata.get(key)
    return getattr(method_metadata, key, None)


class AssignmentLifecycleResolver:
    """Shared method-agnostic effective-assignment resolver prototype.

    Proposals must use decoded assignment convention: target ids ``0..N-1`` or
    ``-1`` for noop / no new target proposal. The resolver intentionally does
    not know about raw policy noop ids.
    """

    def __init__(
        self,
        *,
        num_envs: int,
        num_robots: int,
        num_tasks: int,
        device: torch.device | str = "cpu",
        enabled: bool = False,
        strict_proposals: bool = True,
    ) -> None:
        if num_envs <= 0:
            raise ValueError(f"num_envs must be positive, got {num_envs}")
        if num_robots <= 0:
            raise ValueError(f"num_robots must be positive, got {num_robots}")
        if num_tasks < 0:
            raise ValueError(f"num_tasks must be non-negative, got {num_tasks}")
        self.num_envs = int(num_envs)
        self.num_robots = int(num_robots)
        self.num_tasks = int(num_tasks)
        self.device = torch.device(device)
        self.enabled = bool(enabled)
        self.strict_proposals = bool(strict_proposals)

        shape_robot = (self.num_envs, self.num_robots)
        shape_task = (self.num_envs, self.num_tasks)
        shape_pair = (self.num_envs, self.num_robots, self.num_tasks)

        self.step = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.active_target_id = torch.full(shape_robot, NO_TARGET, dtype=torch.long, device=self.device)
        self.robot_execution_state = torch.full(shape_robot, ROBOT_IDLE, dtype=torch.long, device=self.device)
        self.task_owner_robot_id = torch.full(shape_task, NO_OWNER, dtype=torch.long, device=self.device)
        self.attempt_start_step = torch.full(shape_robot, NO_ATTEMPT, dtype=torch.long, device=self.device)
        self.attempt_age = torch.zeros(shape_robot, dtype=torch.long, device=self.device)
        self.pair_state = torch.full(shape_pair, PAIR_NONE, dtype=torch.long, device=self.device)
        self.last_release_reason = torch.full(shape_robot, REASON_NONE, dtype=torch.long, device=self.device)
        self.last_failure_reason = torch.full(shape_robot, REASON_NONE, dtype=torch.long, device=self.device)
        self._events: list[AssignmentLifecycleResolverEvent] = []
        self._total_event_count = 0

    def resolve_pre_step(
        self,
        *,
        problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> AssignmentLifecyclePreStepResult:
        """Resolve one current-step proposal into an effective assignment."""

        if not self.enabled:
            proposal = self._clone_proposal_shape_only(assignment_proposal)
            return self._make_pre_result(effective_assignment=proposal, proposal_accepted=torch.ones_like(proposal, dtype=torch.bool))

        validated = self._validate_problem(problem, name="problem")
        proposal = self._validate_assignment_proposal(assignment_proposal)
        method_name = _metadata_value(method_metadata, "method_name")

        shape_robot = (self.num_envs, self.num_robots)
        effective = torch.full(shape_robot, NO_TARGET, dtype=torch.long, device=self.device)
        accepted = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        rejected_reason = torch.full(shape_robot, REJECT_NONE, dtype=torch.long, device=self.device)
        continued = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        new_claim_started = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        claim_conflict = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        claim_winner = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        claim_loser = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        switch_requested = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        switch_rejected = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)

        for env_id in range(self.num_envs):
            pending_claims: dict[int, list[int]] = {}
            for robot_id in range(self.num_robots):
                active_target = int(self.active_target_id[env_id, robot_id].item())
                proposed_target = int(proposal[env_id, robot_id].item())
                if active_target >= 0:
                    self._resolve_executing_robot(
                        env_id=env_id,
                        robot_id=robot_id,
                        active_target=active_target,
                        proposed_target=proposed_target,
                        problem=validated,
                        effective=effective,
                        accepted=accepted,
                        rejected_reason=rejected_reason,
                        continued=continued,
                        switch_requested=switch_requested,
                        switch_rejected=switch_rejected,
                        method_name=method_name,
                    )
                    continue

                if proposed_target == NO_TARGET:
                    effective[env_id, robot_id] = NO_TARGET
                    accepted[env_id, robot_id] = True
                    self._emit(
                        "noop_idle",
                        env_id=env_id,
                        robot_id=robot_id,
                        details={
                            "proposed_target_id": NO_TARGET,
                            "effective_target_id": NO_TARGET,
                            "behavior_changed": False,
                        },
                        method_name=method_name,
                    )
                    continue

                if self._is_target_covered(validated, env_id, proposed_target):
                    rejected_reason[env_id, robot_id] = REJECT_COVERED_TARGET
                    self._emit_rejection(
                        "covered_target_rejected",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=proposed_target,
                        proposed_target_id=proposed_target,
                        effective_target_id=NO_TARGET,
                        reason="covered_target",
                        behavior_changed=True,
                        method_name=method_name,
                    )
                    continue

                owner = int(self.task_owner_robot_id[env_id, proposed_target].item())
                if owner != NO_OWNER and owner != robot_id:
                    rejected_reason[env_id, robot_id] = REJECT_OWNED_TARGET
                    self._emit_rejection(
                        "owned_target_rejected",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=proposed_target,
                        proposed_target_id=proposed_target,
                        effective_target_id=NO_TARGET,
                        owner_robot_id=owner,
                        reason="owned_target",
                        behavior_changed=True,
                        method_name=method_name,
                    )
                    continue

                if int(self.pair_state[env_id, robot_id, proposed_target].item()) in (
                    PAIR_FAILED_BUDGET,
                    PAIR_RELEASED_BUDGET,
                ):
                    rejected_reason[env_id, robot_id] = REJECT_FAILED_PAIR
                    self._emit_rejection(
                        "failed_pair_reclaim_rejected",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=proposed_target,
                        proposed_target_id=proposed_target,
                        effective_target_id=NO_TARGET,
                        reason="episode_persistent_failed_pair",
                        behavior_changed=True,
                        method_name=method_name,
                    )
                    continue

                if not self._is_target_available(validated, env_id, robot_id, proposed_target):
                    rejected_reason[env_id, robot_id] = REJECT_UNAVAILABLE_TARGET
                    self._emit_rejection(
                        "unavailable_target_rejected",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=proposed_target,
                        proposed_target_id=proposed_target,
                        effective_target_id=NO_TARGET,
                        reason="unavailable_target",
                        behavior_changed=True,
                        method_name=method_name,
                    )
                    continue

                pending_claims.setdefault(proposed_target, []).append(robot_id)

            for target_id, robot_ids in pending_claims.items():
                winner_id, fallback_reason = self._choose_claim_winner(
                    validated,
                    env_id=env_id,
                    target_id=target_id,
                    robot_ids=robot_ids,
                )
                if len(robot_ids) > 1:
                    loser_ids = [robot_id for robot_id in robot_ids if robot_id != winner_id]
                    for robot_id in robot_ids:
                        claim_conflict[env_id, robot_id] = True
                    self._emit(
                        "exact_claim_conflict_resolved",
                        env_id=env_id,
                        target_id=target_id,
                        details={
                            "claiming_robot_ids": list(robot_ids),
                            "claiming_costs": self._claiming_costs(validated, env_id, target_id, robot_ids),
                            "winner_robot_id": winner_id,
                            "loser_robot_ids": loser_ids,
                            "arbitration_rule": ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK,
                            "fallback_reason": fallback_reason,
                            "behavior_changed": bool(loser_ids),
                        },
                        method_name=method_name,
                    )

                self._start_claim(
                    env_id=env_id,
                    robot_id=winner_id,
                    target_id=target_id,
                    effective=effective,
                    accepted=accepted,
                    new_claim_started=new_claim_started,
                    claim_winner=claim_winner,
                    method_name=method_name,
                )
                for loser_id in robot_ids:
                    if loser_id == winner_id:
                        continue
                    claim_loser[env_id, loser_id] = True
                    rejected_reason[env_id, loser_id] = REJECT_CLAIM_LOST
                    self._emit_rejection(
                        "claim_lost",
                        env_id=env_id,
                        robot_id=loser_id,
                        target_id=target_id,
                        proposed_target_id=target_id,
                        effective_target_id=NO_TARGET,
                        owner_robot_id=winner_id,
                        reason="simultaneous_claim_lost",
                        behavior_changed=True,
                        method_name=method_name,
                    )

        behavior_changed = not bool(torch.equal(effective, proposal))
        return AssignmentLifecyclePreStepResult(
            effective_assignment=effective.clone(),
            proposal_accepted=accepted.clone(),
            proposal_rejected_reason=rejected_reason.clone(),
            continued_from_active_target=continued.clone(),
            new_claim_started=new_claim_started.clone(),
            claim_conflict=claim_conflict.clone(),
            claim_winner=claim_winner.clone(),
            claim_loser=claim_loser.clone(),
            switch_requested=switch_requested.clone(),
            switch_rejected=switch_rejected.clone(),
            behavior_changed=behavior_changed,
        )

    def observe_post_step(
        self,
        *,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        effective_assignment: torch.Tensor,
        post_step_problem: Mapping[str, Any],
        external_diagnostics: Mapping[str, Any] | None = None,
        done_env_ids: torch.Tensor | Sequence[int] | None = None,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> AssignmentLifecyclePostStepResult:
        """Observe completion, budget failure/release, and reset signals."""

        if not self.enabled:
            self._clone_proposal_shape_only(assignment_proposal)
            self._clone_proposal_shape_only(effective_assignment)
            return AssignmentLifecyclePostStepResult(
                completed=torch.zeros((self.num_envs, self.num_robots), dtype=torch.bool, device=self.device),
                released=torch.zeros((self.num_envs, self.num_robots), dtype=torch.bool, device=self.device),
                release_reason=torch.full((self.num_envs, self.num_robots), REASON_NONE, dtype=torch.long, device=self.device),
                failure_reason=torch.full((self.num_envs, self.num_robots), REASON_NONE, dtype=torch.long, device=self.device),
                reset_env_ids=self._normalize_done_env_ids(done_env_ids).detach().cpu().tolist(),
                behavior_changed=False,
            )

        pre = self._validate_problem(pre_step_problem, name="pre_step_problem")
        post = self._validate_problem(post_step_problem, name="post_step_problem")
        self._validate_assignment_proposal(assignment_proposal)
        effective = self._validate_assignment_proposal(effective_assignment)
        method_name = _metadata_value(method_metadata, "method_name")

        completed = torch.zeros((self.num_envs, self.num_robots), dtype=torch.bool, device=self.device)
        released = torch.zeros_like(completed)
        release_reason = torch.full_like(self.last_release_reason, REASON_NONE)
        failure_reason = torch.full_like(self.last_failure_reason, REASON_NONE)

        newly_covered = (~pre["viewpoints_covered"]) & post["viewpoints_covered"]
        for env_id, target_id in torch.nonzero(newly_covered, as_tuple=False).detach().cpu().tolist():
            self._complete_target(
                env_id=int(env_id),
                target_id=int(target_id),
                completed=completed,
                method_name=method_name,
            )

        for failure in self._budget_failure_pairs(external_diagnostics, effective):
            env_id = int(failure["env_id"])
            robot_id = int(failure["robot_id"])
            target_id = int(failure["target_id"])
            if env_id < 0 or env_id >= self.num_envs or robot_id < 0 or robot_id >= self.num_robots:
                continue
            if target_id < 0:
                target_id = int(self.active_target_id[env_id, robot_id].item())
            if target_id < 0 or target_id >= self.num_tasks:
                continue
            self._apply_budget_failure_release(
                env_id=env_id,
                robot_id=robot_id,
                target_id=target_id,
                reason=str(failure.get("reason", "budget_trigger")),
                released=released,
                release_reason=release_reason,
                failure_reason=failure_reason,
                method_name=method_name,
            )

        self.step += 1
        reset_ids = self._normalize_done_env_ids(done_env_ids).detach().cpu().tolist()
        if reset_ids:
            self.reset(env_ids=reset_ids, emit_events=True, method_metadata=method_metadata)

        state_changed = bool(completed.any().item() or released.any().item() or reset_ids)
        return AssignmentLifecyclePostStepResult(
            completed=completed.clone(),
            released=released.clone(),
            release_reason=release_reason.clone(),
            failure_reason=failure_reason.clone(),
            reset_env_ids=[int(env_id) for env_id in reset_ids],
            behavior_changed=state_changed,
        )

    def reset(
        self,
        env_ids: torch.Tensor | Sequence[int] | None = None,
        *,
        emit_events: bool = True,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> dict[str, Any]:
        """Reset resolver state for all or selected environments."""

        env_index = self._normalize_env_ids(env_ids)
        self.active_target_id[env_index] = NO_TARGET
        self.robot_execution_state[env_index] = ROBOT_IDLE
        self.task_owner_robot_id[env_index] = NO_OWNER
        self.attempt_start_step[env_index] = NO_ATTEMPT
        self.attempt_age[env_index] = 0
        self.pair_state[env_index] = PAIR_NONE
        self.last_release_reason[env_index] = REASON_NONE
        self.last_failure_reason[env_index] = REASON_NONE
        self.step[env_index] = 0
        if self.enabled and emit_events:
            method_name = _metadata_value(method_metadata, "method_name")
            for env_id in env_index.detach().cpu().tolist():
                for robot_id in range(self.num_robots):
                    self._emit(
                        "reset",
                        env_id=int(env_id),
                        robot_id=robot_id,
                        details={
                            "reason": "reset",
                            "behavior_changed": False,
                        },
                        method_name=method_name,
                    )
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        """Return clone-based resolver state snapshot."""

        return {
            "enabled": bool(self.enabled),
            "step": self.step.clone(),
            "active_target_id": self.active_target_id.clone(),
            "robot_execution_state": self.robot_execution_state.clone(),
            "task_owner_robot_id": self.task_owner_robot_id.clone(),
            "attempt_start_step": self.attempt_start_step.clone(),
            "attempt_age": self.attempt_age.clone(),
            "pair_state": self.pair_state.clone(),
            "last_release_reason": self.last_release_reason.clone(),
            "last_failure_reason": self.last_failure_reason.clone(),
            "event_count": int(self._total_event_count),
            "robot_execution_state_names": dict(ROBOT_EXECUTION_STATE_NAMES),
            "pair_state_names": dict(PAIR_STATE_NAMES),
            "reason_names": dict(REASON_NAMES),
            "proposal_rejected_reason_names": dict(PROPOSAL_REJECTED_REASON_NAMES),
        }

    def pop_events(self) -> list[dict[str, Any]]:
        """Drain retained events."""

        events = [event.to_dict() for event in self._events]
        self._events.clear()
        return events

    def peek_events(self) -> list[dict[str, Any]]:
        """Return retained events without draining."""

        return [event.to_dict() for event in self._events]

    def _make_pre_result(
        self,
        *,
        effective_assignment: torch.Tensor,
        proposal_accepted: torch.Tensor | None = None,
    ) -> AssignmentLifecyclePreStepResult:
        shape_robot = (self.num_envs, self.num_robots)
        if proposal_accepted is None:
            proposal_accepted = torch.zeros(shape_robot, dtype=torch.bool, device=self.device)
        return AssignmentLifecyclePreStepResult(
            effective_assignment=effective_assignment.clone(),
            proposal_accepted=proposal_accepted.clone(),
            proposal_rejected_reason=torch.full(shape_robot, REJECT_NONE, dtype=torch.long, device=self.device),
            continued_from_active_target=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            new_claim_started=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            claim_conflict=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            claim_winner=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            claim_loser=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            switch_requested=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            switch_rejected=torch.zeros(shape_robot, dtype=torch.bool, device=self.device),
            behavior_changed=False,
        )

    def _normalize_env_ids(self, env_ids: torch.Tensor | Sequence[int] | None) -> torch.Tensor:
        if env_ids is None:
            return torch.arange(self.num_envs, dtype=torch.long, device=self.device)
        if isinstance(env_ids, torch.Tensor):
            ids = env_ids.to(device=self.device, dtype=torch.long).flatten()
        else:
            ids = torch.tensor(list(env_ids), dtype=torch.long, device=self.device).flatten()
        if ids.numel() == 0:
            return ids
        if bool(((ids < 0) | (ids >= self.num_envs)).any()):
            raise ValueError(f"env_ids must be in [0, {self.num_envs})")
        return ids

    def _normalize_done_env_ids(self, env_ids: torch.Tensor | Sequence[int] | None) -> torch.Tensor:
        if env_ids is None:
            return torch.empty(0, dtype=torch.long, device=self.device)
        return self._normalize_env_ids(env_ids)

    def _clone_proposal_shape_only(self, assignment_proposal: torch.Tensor) -> torch.Tensor:
        if not isinstance(assignment_proposal, torch.Tensor):
            raise TypeError(f"assignment_proposal must be a torch.Tensor, got {type(assignment_proposal).__name__}")
        expected = (self.num_envs, self.num_robots)
        if tuple(assignment_proposal.shape) != expected:
            raise ValueError(f"assignment_proposal must have shape {expected}, got {tuple(assignment_proposal.shape)}")
        return assignment_proposal.to(device=self.device, dtype=torch.long).clone()

    def _validate_assignment_proposal(self, assignment_proposal: torch.Tensor) -> torch.Tensor:
        proposal = self._clone_proposal_shape_only(assignment_proposal)
        if torch.is_floating_point(assignment_proposal):
            integer = torch.isfinite(assignment_proposal) & (assignment_proposal == torch.trunc(assignment_proposal))
            if not bool(integer.all()):
                raise ValueError("assignment_proposal must contain finite integer target ids")
        invalid = (proposal < NO_TARGET) | (proposal >= self.num_tasks)
        if bool(invalid.any()) and self.strict_proposals:
            invalid_rows = torch.nonzero(invalid, as_tuple=False).detach().cpu().tolist()
            raise ValueError(
                "assignment_proposal contains ids outside [-1, num_tasks): "
                f"{invalid_rows[:8]}"
            )
        return proposal

    def _validate_problem(self, problem: Mapping[str, Any], *, name: str) -> dict[str, torch.Tensor]:
        if not isinstance(problem, Mapping):
            raise TypeError(f"{name} must be a mapping, got {type(problem).__name__}")
        required = ("available_mask", "viewpoints_covered")
        for key in required:
            if key not in problem:
                raise KeyError(f"{name} must contain {key!r}")
            if not isinstance(problem[key], torch.Tensor):
                raise TypeError(f"{name}[{key!r}] must be a torch.Tensor, got {type(problem[key]).__name__}")
        expected_available = (self.num_envs, self.num_robots, self.num_tasks)
        expected_covered = (self.num_envs, self.num_tasks)
        available_mask = problem["available_mask"]
        covered = problem["viewpoints_covered"]
        if tuple(available_mask.shape) != expected_available:
            raise ValueError(f"{name}['available_mask'] must have shape {expected_available}, got {tuple(available_mask.shape)}")
        if tuple(covered.shape) != expected_covered:
            raise ValueError(f"{name}['viewpoints_covered'] must have shape {expected_covered}, got {tuple(covered.shape)}")
        result: dict[str, torch.Tensor] = {
            "available_mask": available_mask.to(device=self.device, dtype=torch.bool),
            "viewpoints_covered": covered.to(device=self.device, dtype=torch.bool),
        }
        feasible_mask = problem.get("feasible_mask")
        if feasible_mask is not None:
            if not isinstance(feasible_mask, torch.Tensor):
                raise TypeError(f"{name}['feasible_mask'] must be a torch.Tensor when supplied")
            if tuple(feasible_mask.shape) != expected_available:
                raise ValueError(f"{name}['feasible_mask'] must have shape {expected_available}, got {tuple(feasible_mask.shape)}")
            result["feasible_mask"] = feasible_mask.to(device=self.device, dtype=torch.bool)
        cost_matrix = problem.get("cost_matrix")
        if cost_matrix is not None:
            if not isinstance(cost_matrix, torch.Tensor):
                raise TypeError(f"{name}['cost_matrix'] must be a torch.Tensor when supplied")
            if tuple(cost_matrix.shape) != expected_available:
                raise ValueError(f"{name}['cost_matrix'] must have shape {expected_available}, got {tuple(cost_matrix.shape)}")
            result["cost_matrix"] = cost_matrix.to(device=self.device, dtype=torch.float32)
        return result

    def _is_target_covered(self, problem: Mapping[str, torch.Tensor], env_id: int, target_id: int) -> bool:
        return bool(problem["viewpoints_covered"][env_id, target_id].item())

    def _is_target_available(self, problem: Mapping[str, torch.Tensor], env_id: int, robot_id: int, target_id: int) -> bool:
        available = bool(problem["available_mask"][env_id, robot_id, target_id].item())
        if "feasible_mask" in problem:
            available = available and bool(problem["feasible_mask"][env_id, robot_id, target_id].item())
        return available

    def _resolve_executing_robot(
        self,
        *,
        env_id: int,
        robot_id: int,
        active_target: int,
        proposed_target: int,
        problem: Mapping[str, torch.Tensor],
        effective: torch.Tensor,
        accepted: torch.Tensor,
        rejected_reason: torch.Tensor,
        continued: torch.Tensor,
        switch_requested: torch.Tensor,
        switch_rejected: torch.Tensor,
        method_name: str | None,
    ) -> None:
        effective[env_id, robot_id] = active_target
        if not self._is_target_available(problem, env_id, robot_id, active_target) and not self._is_target_covered(
            problem,
            env_id,
            active_target,
        ):
            self._emit(
                "active_target_infeasible_deferred",
                env_id=env_id,
                robot_id=robot_id,
                target_id=active_target,
                details={
                    "proposed_target_id": proposed_target,
                    "effective_target_id": active_target,
                    "owner_robot_id": int(self.task_owner_robot_id[env_id, active_target].item()),
                    "reason": "active_target_infeasible_deferred",
                    "behavior_changed": proposed_target != active_target,
                },
                method_name=method_name,
            )
        if proposed_target == active_target:
            accepted[env_id, robot_id] = True
            continued[env_id, robot_id] = True
            self._update_attempt_age(env_id, robot_id)
            self._emit(
                "attempt_continued_same_target",
                env_id=env_id,
                robot_id=robot_id,
                target_id=active_target,
                details={
                    "proposed_target_id": proposed_target,
                    "effective_target_id": active_target,
                    "attempt_age": int(self.attempt_age[env_id, robot_id].item()),
                    "behavior_changed": False,
                },
                method_name=method_name,
            )
        elif proposed_target == NO_TARGET:
            accepted[env_id, robot_id] = True
            continued[env_id, robot_id] = True
            self._update_attempt_age(env_id, robot_id)
            self._emit(
                "attempt_continued_noop_contract_c",
                env_id=env_id,
                robot_id=robot_id,
                target_id=active_target,
                details={
                    "proposed_target_id": NO_TARGET,
                    "effective_target_id": active_target,
                    "attempt_age": int(self.attempt_age[env_id, robot_id].item()),
                    "reason": "noop_continue_contract_c",
                    "behavior_changed": True,
                },
                method_name=method_name,
            )
        else:
            switch_requested[env_id, robot_id] = True
            switch_rejected[env_id, robot_id] = True
            rejected_reason[env_id, robot_id] = REJECT_SWITCH_DISABLED
            self._update_attempt_age(env_id, robot_id)
            self._emit(
                "switch_rejected_executing",
                env_id=env_id,
                robot_id=robot_id,
                target_id=active_target,
                details={
                    "previous_target_id": active_target,
                    "proposed_target_id": proposed_target,
                    "effective_target_id": active_target,
                    "reason": "switching_disabled_while_executing",
                    "behavior_changed": True,
                },
                method_name=method_name,
            )

    def _start_claim(
        self,
        *,
        env_id: int,
        robot_id: int,
        target_id: int,
        effective: torch.Tensor,
        accepted: torch.Tensor,
        new_claim_started: torch.Tensor,
        claim_winner: torch.Tensor,
        method_name: str | None,
    ) -> None:
        effective[env_id, robot_id] = target_id
        accepted[env_id, robot_id] = True
        new_claim_started[env_id, robot_id] = True
        claim_winner[env_id, robot_id] = True
        self.active_target_id[env_id, robot_id] = target_id
        self.robot_execution_state[env_id, robot_id] = ROBOT_EXECUTING
        self.task_owner_robot_id[env_id, target_id] = robot_id
        self.attempt_start_step[env_id, robot_id] = self.step[env_id]
        self.attempt_age[env_id, robot_id] = 0
        self.pair_state[env_id, robot_id, target_id] = PAIR_ACTIVE
        self._emit(
            "attempt_started",
            env_id=env_id,
            robot_id=robot_id,
            target_id=target_id,
            details={
                "proposed_target_id": target_id,
                "effective_target_id": target_id,
                "owner_robot_id": robot_id,
                "attempt_age": 0,
                "behavior_changed": False,
            },
            method_name=method_name,
        )

    def _update_attempt_age(self, env_id: int, robot_id: int) -> None:
        start = int(self.attempt_start_step[env_id, robot_id].item())
        if start >= 0:
            self.attempt_age[env_id, robot_id] = torch.clamp(self.step[env_id] - start, min=0)

    def _choose_claim_winner(
        self,
        problem: Mapping[str, torch.Tensor],
        *,
        env_id: int,
        target_id: int,
        robot_ids: Sequence[int],
    ) -> tuple[int, str | None]:
        if "cost_matrix" not in problem:
            return int(min(robot_ids)), ARBITRATION_FALLBACK_ROBOT_ID
        finite: list[tuple[float, int]] = []
        for robot_id in robot_ids:
            value = float(problem["cost_matrix"][env_id, robot_id, target_id].item())
            if torch.isfinite(torch.tensor(value)).item():
                finite.append((value, int(robot_id)))
        if not finite:
            return int(min(robot_ids)), ARBITRATION_FALLBACK_ROBOT_ID
        finite.sort(key=lambda item: (item[0], item[1]))
        return int(finite[0][1]), None

    def _claiming_costs(
        self,
        problem: Mapping[str, torch.Tensor],
        env_id: int,
        target_id: int,
        robot_ids: Sequence[int],
    ) -> list[float | None]:
        if "cost_matrix" not in problem:
            return [None for _ in robot_ids]
        costs: list[float | None] = []
        for robot_id in robot_ids:
            value = float(problem["cost_matrix"][env_id, robot_id, target_id].item())
            costs.append(value if torch.isfinite(torch.tensor(value)).item() else None)
        return costs

    def _complete_target(
        self,
        *,
        env_id: int,
        target_id: int,
        completed: torch.Tensor,
        method_name: str | None,
    ) -> None:
        owner = int(self.task_owner_robot_id[env_id, target_id].item())
        active_robots = torch.nonzero(self.active_target_id[env_id] == target_id, as_tuple=False).flatten()
        if owner >= 0 and owner not in [int(robot_id.item()) for robot_id in active_robots]:
            active_robots = torch.cat([active_robots, torch.tensor([owner], dtype=torch.long, device=self.device)])
        if active_robots.numel() == 0:
            self._emit(
                "target_completed",
                env_id=env_id,
                target_id=target_id,
                details={
                    "owner_robot_id": owner if owner >= 0 else None,
                    "reason": "viewpoints_covered",
                    "behavior_changed": True,
                },
                method_name=method_name,
            )
        for robot_tensor in active_robots:
            robot_id = int(robot_tensor.item())
            completed[env_id, robot_id] = True
            self._emit(
                "target_completed",
                env_id=env_id,
                robot_id=robot_id,
                target_id=target_id,
                details={
                    "owner_robot_id": owner if owner >= 0 else robot_id,
                    "reason": "viewpoints_covered",
                    "behavior_changed": True,
                },
                method_name=method_name,
            )
            self._clear_robot_attempt(env_id, robot_id)
        self.task_owner_robot_id[env_id, target_id] = NO_OWNER
        self.pair_state[env_id, :, target_id] = PAIR_COMPLETED

    def _apply_budget_failure_release(
        self,
        *,
        env_id: int,
        robot_id: int,
        target_id: int,
        reason: str,
        released: torch.Tensor,
        release_reason: torch.Tensor,
        failure_reason: torch.Tensor,
        method_name: str | None,
    ) -> None:
        self._emit(
            "budget_failure",
            env_id=env_id,
            robot_id=robot_id,
            target_id=target_id,
            details={
                "reason": reason,
                "failure_reason": "budget_failure",
                "behavior_changed": True,
            },
            method_name=method_name,
        )
        self.pair_state[env_id, robot_id, target_id] = PAIR_FAILED_BUDGET
        self.last_failure_reason[env_id, robot_id] = REASON_BUDGET_FAILURE
        failure_reason[env_id, robot_id] = REASON_BUDGET_FAILURE
        released[env_id, robot_id] = True
        release_reason[env_id, robot_id] = REASON_BUDGET_FAILURE
        self.last_release_reason[env_id, robot_id] = REASON_BUDGET_FAILURE
        if int(self.active_target_id[env_id, robot_id].item()) == target_id:
            self._clear_robot_attempt(env_id, robot_id)
        if int(self.task_owner_robot_id[env_id, target_id].item()) == robot_id:
            self.task_owner_robot_id[env_id, target_id] = NO_OWNER
        self.pair_state[env_id, robot_id, target_id] = PAIR_RELEASED_BUDGET
        self._emit(
            "release_budget_failure",
            env_id=env_id,
            robot_id=robot_id,
            target_id=target_id,
            details={
                "release_reason": "budget_failure",
                "failure_reason": "budget_failure",
                "behavior_changed": True,
            },
            method_name=method_name,
        )

    def _clear_robot_attempt(self, env_id: int, robot_id: int) -> None:
        self.active_target_id[env_id, robot_id] = NO_TARGET
        self.robot_execution_state[env_id, robot_id] = ROBOT_IDLE
        self.attempt_start_step[env_id, robot_id] = NO_ATTEMPT
        self.attempt_age[env_id, robot_id] = 0

    def _budget_failure_pairs(
        self,
        external_diagnostics: Mapping[str, Any] | None,
        effective_assignment: torch.Tensor,
    ) -> list[dict[str, Any]]:
        if external_diagnostics is None:
            return []
        pairs = external_diagnostics.get("budget_failure_pairs") if isinstance(external_diagnostics, Mapping) else None
        normalized: list[dict[str, Any]] = []
        if isinstance(pairs, Sequence) and not isinstance(pairs, (str, bytes)):
            for item in pairs:
                if not isinstance(item, Mapping):
                    continue
                normalized.append(
                    {
                        "env_id": int(item.get("env_id", 0)),
                        "robot_id": int(item.get("robot_id", -1)),
                        "target_id": int(item.get("target_id", -1)),
                        "reason": str(item.get("reason", "budget_trigger")),
                    }
                )
        mask = external_diagnostics.get("budget_failure_mask") if isinstance(external_diagnostics, Mapping) else None
        if isinstance(mask, torch.Tensor):
            bool_mask = mask.to(device=self.device, dtype=torch.bool)
            if tuple(bool_mask.shape) == (self.num_envs, self.num_robots):
                for env_id, robot_id in torch.nonzero(bool_mask, as_tuple=False).detach().cpu().tolist():
                    normalized.append(
                        {
                            "env_id": int(env_id),
                            "robot_id": int(robot_id),
                            "target_id": int(effective_assignment[int(env_id), int(robot_id)].item()),
                            "reason": "budget_trigger",
                        }
                    )
            elif tuple(bool_mask.shape) == (self.num_envs, self.num_robots, self.num_tasks):
                for env_id, robot_id, target_id in torch.nonzero(bool_mask, as_tuple=False).detach().cpu().tolist():
                    normalized.append(
                        {
                            "env_id": int(env_id),
                            "robot_id": int(robot_id),
                            "target_id": int(target_id),
                            "reason": "budget_trigger",
                        }
                    )
        return normalized

    def _emit_rejection(
        self,
        event_type: str,
        *,
        env_id: int,
        robot_id: int,
        target_id: int,
        proposed_target_id: int,
        effective_target_id: int,
        reason: str,
        behavior_changed: bool,
        method_name: str | None,
        owner_robot_id: int | None = None,
    ) -> None:
        self._emit(
            event_type,
            env_id=env_id,
            robot_id=robot_id,
            target_id=target_id,
            details={
                "proposed_target_id": proposed_target_id,
                "effective_target_id": effective_target_id,
                "owner_robot_id": owner_robot_id,
                "reason": reason,
                "behavior_changed": bool(behavior_changed),
            },
            method_name=method_name,
        )

    def _emit(
        self,
        event_type: str,
        *,
        env_id: int,
        step: int | None = None,
        robot_id: int | None = None,
        target_id: int | None = None,
        details: Mapping[str, Any] | None = None,
        method_name: str | None = None,
    ) -> None:
        if not self.enabled:
            return
        event_step = int(self.step[env_id].item()) if step is None else int(step)
        self._events.append(
            AssignmentLifecycleResolverEvent(
                event_type=str(event_type),
                env_id=int(env_id),
                step=event_step,
                robot_id=None if robot_id is None else int(robot_id),
                target_id=None if target_id is None else int(target_id),
                method_name=method_name,
                details=dict(details or {}),
            )
        )
        self._total_event_count += 1


__all__ = [
    "ARBITRATION_FALLBACK_ROBOT_ID",
    "ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK",
    "AssignmentLifecyclePostStepResult",
    "AssignmentLifecyclePreStepResult",
    "AssignmentLifecycleResolver",
    "AssignmentLifecycleResolverEvent",
    "NO_ATTEMPT",
    "NO_OWNER",
    "NO_REASON",
    "NO_TARGET",
    "PAIR_ACTIVE",
    "PAIR_COMPLETED",
    "PAIR_FAILED_BUDGET",
    "PAIR_NONE",
    "PAIR_RELEASED_BUDGET",
    "PAIR_STATE_NAMES",
    "PROPOSAL_REJECTED_REASON_NAMES",
    "REASON_BUDGET_FAILURE",
    "REASON_COMPLETION",
    "REASON_NAMES",
    "REASON_NONE",
    "REASON_RESET",
    "REJECT_CLAIM_LOST",
    "REJECT_COVERED_TARGET",
    "REJECT_FAILED_PAIR",
    "REJECT_INVALID_PROPOSAL",
    "REJECT_NONE",
    "REJECT_OWNED_TARGET",
    "REJECT_SWITCH_DISABLED",
    "REJECT_UNAVAILABLE_TARGET",
    "ROBOT_EXECUTING",
    "ROBOT_EXECUTION_STATE_NAMES",
    "ROBOT_IDLE",
]
