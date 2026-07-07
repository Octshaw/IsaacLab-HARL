"""Passive assignment lifecycle transition logger.

This module reconstructs proxy lifecycle transitions from standardized
assignment proposals and pre/post assignment problem snapshots. It is a
diagnostics component only: it does not resolve conflicts, latch actions,
generate masks, command the controller, or mutate assignment proposals.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import torch


ROBOT_IDLE_PROXY = 0
ROBOT_ACTIVE_PROXY = 1
ROBOT_RELEASED_PROXY = 2
ROBOT_RESET_PROXY = 3

TASK_OPEN_PROXY = 0
TASK_CLAIMED_PROXY = 1
TASK_COMPLETED = 2

PAIR_NONE = 0
PAIR_ACTIVE_PROXY = 1
PAIR_COMPLETED = 2
PAIR_FAILED_BUDGET_PROXY = 3
PAIR_RELEASED_PROXY = 4
PAIR_TIMEOUT_PROXY = 5

NO_ACTIVE_TARGET = -1
NO_PROPOSAL_SEEN = -2

ROBOT_STATE_PROXY_NAMES = {
    ROBOT_IDLE_PROXY: "idle_proxy",
    ROBOT_ACTIVE_PROXY: "active_proxy",
    ROBOT_RELEASED_PROXY: "released_proxy",
    ROBOT_RESET_PROXY: "reset_proxy",
}

TASK_STATE_PROXY_NAMES = {
    TASK_OPEN_PROXY: "open_proxy",
    TASK_CLAIMED_PROXY: "claimed_proxy",
    TASK_COMPLETED: "completed",
}

PAIR_STATE_PROXY_NAMES = {
    PAIR_NONE: "none",
    PAIR_ACTIVE_PROXY: "active_proxy",
    PAIR_COMPLETED: "completed",
    PAIR_FAILED_BUDGET_PROXY: "failed_budget_proxy",
    PAIR_RELEASED_PROXY: "released_proxy",
    PAIR_TIMEOUT_PROXY: "timeout_proxy",
}

ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK = "lowest_path_cost_robot_id_tiebreak"


@dataclass(frozen=True)
class AssignmentLifecycleEvent:
    """Machine-readable passive lifecycle transition event."""

    event_type: str
    env_id: int
    step: int
    robot_id: int | None = None
    target_id: int | None = None
    method_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "event_type": self.event_type,
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


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return _json_safe(value.item())
        return _json_safe(value.detach().cpu().tolist())
    if isinstance(value, dict):
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


def _clone_problem_tensors(problem: Mapping[str, Any]) -> dict[str, torch.Tensor]:
    cloned: dict[str, torch.Tensor] = {}
    for key, value in problem.items():
        if isinstance(value, torch.Tensor):
            cloned[str(key)] = value.detach().clone()
    return cloned


class AssignmentLifecycleTransitionLogger:
    """Online passive lifecycle proxy logger for assignment proposals.

    The standardized proposal is a ``torch.long`` tensor with shape
    ``[num_envs, num_robots]``. Values ``0..num_tasks - 1`` are proposed
    target ids, and ``-1`` is decoded noop / no proposed target.

    The logger is method-agnostic. Optional metadata may identify the source
    method, but metadata never changes transition reconstruction.
    """

    def __init__(
        self,
        *,
        num_envs: int,
        num_robots: int,
        num_tasks: int,
        device: torch.device | str = "cpu",
        strict_proposals: bool = True,
        retain_events: bool = True,
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
        self.strict_proposals = bool(strict_proposals)
        self.retain_events = bool(retain_events)

        shape_robot = (self.num_envs, self.num_robots)
        shape_task = (self.num_envs, self.num_tasks)
        shape_pair = (self.num_envs, self.num_robots, self.num_tasks)

        self.step = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.robot_state_proxy = torch.full(shape_robot, ROBOT_IDLE_PROXY, dtype=torch.long, device=self.device)
        self.active_target_proxy = torch.full(shape_robot, NO_ACTIVE_TARGET, dtype=torch.long, device=self.device)
        self.task_owner_proxy = torch.full(shape_task, -1, dtype=torch.long, device=self.device)
        self.task_state_proxy = torch.full(shape_task, TASK_OPEN_PROXY, dtype=torch.long, device=self.device)
        self.pair_state_proxy = torch.full(shape_pair, PAIR_NONE, dtype=torch.long, device=self.device)
        self.attempt_start_step_proxy = torch.full(shape_robot, -1, dtype=torch.long, device=self.device)
        self.attempt_age_proxy = torch.zeros(shape_robot, dtype=torch.long, device=self.device)
        self.last_proposal = torch.full(shape_robot, NO_PROPOSAL_SEEN, dtype=torch.long, device=self.device)
        self._last_event_type = [["" for _ in range(self.num_robots)] for _ in range(self.num_envs)]
        self._last_transition_reason = [["" for _ in range(self.num_robots)] for _ in range(self.num_envs)]
        self._events: list[AssignmentLifecycleEvent] = []
        self._total_event_count = 0

    def reset(self, env_ids: torch.Tensor | Sequence[int] | None = None, *, emit_events: bool = True) -> dict[str, Any]:
        """Reset passive proxy state for selected environments."""
        env_index = self._normalize_env_ids(env_ids)
        self.robot_state_proxy[env_index] = ROBOT_IDLE_PROXY
        self.active_target_proxy[env_index] = NO_ACTIVE_TARGET
        self.task_owner_proxy[env_index] = -1
        self.task_state_proxy[env_index] = TASK_OPEN_PROXY
        self.pair_state_proxy[env_index] = PAIR_NONE
        self.attempt_start_step_proxy[env_index] = -1
        self.attempt_age_proxy[env_index] = 0
        self.last_proposal[env_index] = NO_PROPOSAL_SEEN
        self.step[env_index] = 0
        for env_id in env_index.detach().cpu().tolist():
            env_int = int(env_id)
            for robot_id in range(self.num_robots):
                self._last_event_type[env_int][robot_id] = "reset_proxy"
                self._last_transition_reason[env_int][robot_id] = "reset"
                if emit_events:
                    self._emit(
                        "reset_proxy",
                        env_id=env_int,
                        robot_id=robot_id,
                        details={"reset_scope": "selected_env"},
                    )
        return self.snapshot()

    def observe_pre_step(
        self,
        *,
        problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> dict[str, Any]:
        """Observe the current-step proposal and emit passive pre-step events."""
        validated = self._validate_problem(problem, name="problem")
        proposal = self._validate_assignment_proposal(assignment_proposal)
        method_name = _metadata_value(method_metadata, "method_name")

        self._sync_completed_tasks(validated["viewpoints_covered"])
        self._log_exact_claim_conflicts(validated, proposal, method_name=method_name)
        self._observe_robot_proposals(validated, proposal, method_name=method_name)
        self.last_proposal = proposal.clone()
        return self.snapshot()

    def observe_post_step(
        self,
        *,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        post_step_problem: Mapping[str, Any],
        external_diagnostics: Mapping[str, Any] | None = None,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> dict[str, Any]:
        """Observe post-step completion/failure signals and update proxy state."""
        pre = self._validate_problem(pre_step_problem, name="pre_step_problem")
        post = self._validate_problem(post_step_problem, name="post_step_problem")
        self._validate_assignment_proposal(assignment_proposal)
        method_name = _metadata_value(method_metadata, "method_name")

        self._observe_completion(pre, post, external_diagnostics=external_diagnostics, method_name=method_name)
        self._observe_budget_failures(external_diagnostics, method_name=method_name)

        active = self.active_target_proxy >= 0
        self.attempt_age_proxy = torch.where(active, self.attempt_age_proxy + 1, torch.zeros_like(self.attempt_age_proxy))
        self.step += 1
        return self.snapshot()

    def update(
        self,
        *,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        post_step_problem: Mapping[str, Any],
        external_diagnostics: Mapping[str, Any] | None = None,
        method_metadata: Mapping[str, Any] | object | None = None,
    ) -> dict[str, Any]:
        """Convenience method for one complete passive pre/post observation."""
        self.observe_pre_step(
            problem=pre_step_problem,
            assignment_proposal=assignment_proposal,
            method_metadata=method_metadata,
        )
        return self.observe_post_step(
            pre_step_problem=pre_step_problem,
            assignment_proposal=assignment_proposal,
            post_step_problem=post_step_problem,
            external_diagnostics=external_diagnostics,
            method_metadata=method_metadata,
        )

    def snapshot(self) -> dict[str, Any]:
        """Return a clone-based snapshot of current passive proxy state."""
        return {
            "step": self.step.clone(),
            "robot_state_proxy": self.robot_state_proxy.clone(),
            "active_target_proxy": self.active_target_proxy.clone(),
            "task_owner_proxy": self.task_owner_proxy.clone(),
            "task_state_proxy": self.task_state_proxy.clone(),
            "pair_state_proxy": self.pair_state_proxy.clone(),
            "attempt_start_step_proxy": self.attempt_start_step_proxy.clone(),
            "attempt_age_proxy": self.attempt_age_proxy.clone(),
            "last_proposal": self.last_proposal.clone(),
            "event_count": int(self._total_event_count),
            "last_event_type": [list(row) for row in self._last_event_type],
            "last_transition_reason": [list(row) for row in self._last_transition_reason],
            "robot_state_proxy_names": dict(ROBOT_STATE_PROXY_NAMES),
            "task_state_proxy_names": dict(TASK_STATE_PROXY_NAMES),
            "pair_state_proxy_names": dict(PAIR_STATE_PROXY_NAMES),
        }

    def pop_events(self) -> list[dict[str, Any]]:
        """Drain and return retained events as dictionaries."""
        events = [event.to_dict() for event in self._events]
        self._events.clear()
        return events

    def peek_events(self) -> list[dict[str, Any]]:
        """Return retained events without draining them."""
        return [event.to_dict() for event in self._events]

    def clone_problem_inputs(self, problem: Mapping[str, Any]) -> dict[str, torch.Tensor]:
        """Return cloned tensor inputs for external non-mutation checks."""
        return _clone_problem_tensors(problem)

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

    def _validate_problem(self, problem: Mapping[str, Any], *, name: str) -> dict[str, torch.Tensor]:
        if not isinstance(problem, Mapping):
            raise TypeError(f"{name} must be a mapping, got {type(problem).__name__}")
        required = ("available_mask", "viewpoints_covered")
        for key in required:
            if key not in problem:
                raise KeyError(f"{name} must contain {key!r}")
            if not isinstance(problem[key], torch.Tensor):
                raise TypeError(f"{name}[{key!r}] must be a torch.Tensor, got {type(problem[key]).__name__}")

        available_mask = problem["available_mask"]
        covered = problem["viewpoints_covered"]
        expected_available = (self.num_envs, self.num_robots, self.num_tasks)
        expected_covered = (self.num_envs, self.num_tasks)
        if tuple(available_mask.shape) != expected_available:
            raise ValueError(f"{name}['available_mask'] must have shape {expected_available}, got {tuple(available_mask.shape)}")
        if tuple(covered.shape) != expected_covered:
            raise ValueError(f"{name}['viewpoints_covered'] must have shape {expected_covered}, got {tuple(covered.shape)}")

        result = {
            "available_mask": available_mask.to(device=self.device, dtype=torch.bool),
            "viewpoints_covered": covered.to(device=self.device, dtype=torch.bool),
        }
        cost_matrix = problem.get("cost_matrix")
        if cost_matrix is not None:
            if not isinstance(cost_matrix, torch.Tensor):
                raise TypeError(f"{name}['cost_matrix'] must be a torch.Tensor when supplied")
            if tuple(cost_matrix.shape) != expected_available:
                raise ValueError(f"{name}['cost_matrix'] must have shape {expected_available}, got {tuple(cost_matrix.shape)}")
            result["cost_matrix"] = cost_matrix.to(device=self.device, dtype=torch.float32)
        return result

    def _validate_assignment_proposal(self, assignment_proposal: torch.Tensor) -> torch.Tensor:
        if not isinstance(assignment_proposal, torch.Tensor):
            raise TypeError(
                f"assignment_proposal must be a torch.Tensor, got {type(assignment_proposal).__name__}"
            )
        expected = (self.num_envs, self.num_robots)
        if tuple(assignment_proposal.shape) != expected:
            raise ValueError(f"assignment_proposal must have shape {expected}, got {tuple(assignment_proposal.shape)}")
        if torch.is_floating_point(assignment_proposal):
            integer = torch.isfinite(assignment_proposal) & (assignment_proposal == torch.trunc(assignment_proposal))
            if not bool(integer.all()):
                raise ValueError("assignment_proposal must contain finite integer target ids")
        proposal = assignment_proposal.to(device=self.device, dtype=torch.long).clone()
        invalid = (proposal < -1) | (proposal >= self.num_tasks)
        if bool(invalid.any()):
            invalid_rows = torch.nonzero(invalid, as_tuple=False).detach().cpu().tolist()
            if self.strict_proposals:
                raise ValueError(
                    "assignment_proposal contains ids outside [-1, num_tasks): "
                    f"{invalid_rows[:8]}"
                )
            for env_id, robot_id in invalid_rows:
                self._emit(
                    "invalid_assignment_proposal_proxy",
                    env_id=int(env_id),
                    robot_id=int(robot_id),
                    details={"proposal_value": int(proposal[env_id, robot_id].item())},
                )
        return proposal

    def _sync_completed_tasks(self, covered: torch.Tensor) -> None:
        self.task_state_proxy = torch.where(
            covered,
            torch.full_like(self.task_state_proxy, TASK_COMPLETED),
            self.task_state_proxy,
        )

    def _log_exact_claim_conflicts(
        self,
        problem: Mapping[str, torch.Tensor],
        proposal: torch.Tensor,
        *,
        method_name: str | None,
    ) -> None:
        available = problem["available_mask"]
        covered = problem["viewpoints_covered"]
        cost_matrix = problem.get("cost_matrix")

        for env_id in range(self.num_envs):
            for target_id in range(self.num_tasks):
                if bool(covered[env_id, target_id].item()):
                    continue
                claimers: list[int] = []
                for robot_id in range(self.num_robots):
                    if int(proposal[env_id, robot_id].item()) != target_id:
                        continue
                    if bool(available[env_id, robot_id, target_id].item()):
                        claimers.append(robot_id)
                if len(claimers) < 2:
                    continue
                costs: list[float | None] = []
                finite_costs: list[tuple[float, int]] = []
                fallback_reason = None
                for robot_id in claimers:
                    value: float | None = None
                    if cost_matrix is not None:
                        raw = float(cost_matrix[env_id, robot_id, target_id].item())
                        value = raw
                        if torch.isfinite(torch.tensor(raw)):
                            finite_costs.append((raw, robot_id))
                    costs.append(value)
                if len(finite_costs) == len(claimers):
                    finite_costs.sort(key=lambda item: (item[0], item[1]))
                    winner = int(finite_costs[0][1])
                else:
                    winner = int(min(claimers))
                    fallback_reason = "cost_unavailable_or_non_finite"
                losers = [int(robot_id) for robot_id in claimers if int(robot_id) != winner]
                self._emit(
                    "exact_claim_conflict_proxy",
                    env_id=env_id,
                    target_id=target_id,
                    method_name=method_name,
                    details={
                        "claiming_robot_ids": [int(robot_id) for robot_id in claimers],
                        "claiming_costs": costs,
                        "would_be_winner_robot_id": winner,
                        "would_be_loser_robot_ids": losers,
                        "arbitration_rule": ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK,
                        "fallback_reason": fallback_reason,
                        "behavior_changed": False,
                    },
                )

    def _observe_robot_proposals(
        self,
        problem: Mapping[str, torch.Tensor],
        proposal: torch.Tensor,
        *,
        method_name: str | None,
    ) -> None:
        available = problem["available_mask"]
        covered = problem["viewpoints_covered"]
        for env_id in range(self.num_envs):
            step = int(self.step[env_id].item())
            for robot_id in range(self.num_robots):
                target_id = int(proposal[env_id, robot_id].item())
                previous_target = int(self.active_target_proxy[env_id, robot_id].item())
                if target_id < 0:
                    if previous_target < 0:
                        self._emit(
                            "noop_idle_proxy",
                            env_id=env_id,
                            robot_id=robot_id,
                            method_name=method_name,
                            details={"current_behavior": "noop_sends_no_target_directed_command"},
                        )
                        self._set_robot_last(env_id, robot_id, "noop_idle_proxy", "noop_while_idle")
                    else:
                        self._emit(
                            "noop_after_active_ambiguous",
                            env_id=env_id,
                            robot_id=robot_id,
                            target_id=previous_target,
                            method_name=method_name,
                            details={
                                "previous_target_id": previous_target,
                                "current_behavior": "noop_sends_no_target_directed_command",
                                "future_contract_c_interpretation": "noop_could_mean_continue_when_executing",
                                "phase9g6b_applies_future_semantic": False,
                            },
                        )
                        self._clear_robot_active_proxy(env_id, robot_id, previous_target, reason="noop_after_active")
                        self._set_robot_last(env_id, robot_id, "noop_after_active_ambiguous", "noop_after_active")
                    continue

                target_available = bool(available[env_id, robot_id, target_id].item())
                target_covered = bool(covered[env_id, target_id].item())
                if target_covered or not target_available:
                    self._emit(
                        "unavailable_target_proposal_proxy",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=target_id,
                        method_name=method_name,
                        details={
                            "target_available": bool(target_available),
                            "target_covered": bool(target_covered),
                            "behavior_changed": False,
                        },
                    )
                    self._set_robot_last(env_id, robot_id, "unavailable_target_proposal_proxy", "target_unavailable")
                    continue

                if previous_target < 0:
                    self._start_or_claim_proxy(env_id, robot_id, target_id, start_step=step)
                    self._emit(
                        "attempt_started_proxy",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=target_id,
                        method_name=method_name,
                    )
                    self._set_robot_last(env_id, robot_id, "attempt_started_proxy", "proposal_started_proxy_attempt")
                elif previous_target == target_id:
                    self.robot_state_proxy[env_id, robot_id] = ROBOT_ACTIVE_PROXY
                    self.pair_state_proxy[env_id, robot_id, target_id] = PAIR_ACTIVE_PROXY
                    self.attempt_age_proxy[env_id, robot_id] = max(
                        0,
                        step - int(self.attempt_start_step_proxy[env_id, robot_id].item()),
                    )
                    self._emit(
                        "attempt_continued_proxy",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=target_id,
                        method_name=method_name,
                        details={"attempt_age_proxy": int(self.attempt_age_proxy[env_id, robot_id].item())},
                    )
                    self._set_robot_last(env_id, robot_id, "attempt_continued_proxy", "proposal_repeated_active_target")
                else:
                    self._emit(
                        "switch_request_proxy",
                        env_id=env_id,
                        robot_id=robot_id,
                        target_id=target_id,
                        method_name=method_name,
                        details={
                            "previous_target_id": previous_target,
                            "new_target_id": target_id,
                            "proxy_update_rule": "advance_active_target_to_new_proposal_for_reconstruction_only",
                            "behavior_changed": False,
                        },
                    )
                    self._release_pair_proxy(env_id, robot_id, previous_target, reason="switch_request_proxy")
                    self._start_or_claim_proxy(env_id, robot_id, target_id, start_step=step)
                    self._set_robot_last(env_id, robot_id, "switch_request_proxy", "switch_request_proxy")

    def _start_or_claim_proxy(self, env_id: int, robot_id: int, target_id: int, *, start_step: int) -> None:
        self.robot_state_proxy[env_id, robot_id] = ROBOT_ACTIVE_PROXY
        self.active_target_proxy[env_id, robot_id] = int(target_id)
        self.task_state_proxy[env_id, target_id] = TASK_CLAIMED_PROXY
        self.task_owner_proxy[env_id, target_id] = int(robot_id)
        self.pair_state_proxy[env_id, robot_id, target_id] = PAIR_ACTIVE_PROXY
        self.attempt_start_step_proxy[env_id, robot_id] = int(start_step)
        self.attempt_age_proxy[env_id, robot_id] = 0

    def _observe_completion(
        self,
        pre: Mapping[str, torch.Tensor],
        post: Mapping[str, torch.Tensor],
        *,
        external_diagnostics: Mapping[str, Any] | None,
        method_name: str | None,
    ) -> None:
        newly_covered = (~pre["viewpoints_covered"]) & post["viewpoints_covered"]
        completed_by = self._completed_by_robot_tensor(external_diagnostics)
        for env_id, target_id in torch.nonzero(newly_covered, as_tuple=False).detach().cpu().tolist():
            env_int = int(env_id)
            target_int = int(target_id)
            owner = int(self.task_owner_proxy[env_int, target_int].item())
            completing_robot = -1
            if completed_by is not None:
                completing_robot = int(completed_by[env_int, target_int].item())
            if owner >= 0 and completing_robot >= 0 and completing_robot != owner:
                self._emit(
                    "target_completed_by_teammate_proxy",
                    env_id=env_int,
                    robot_id=owner,
                    target_id=target_int,
                    method_name=method_name,
                    details={
                        "associated_active_robot_id": owner,
                        "completing_robot_id": completing_robot,
                        "completion_source": "external_diagnostics_completed_by_robot_ids",
                    },
                )
                self._set_robot_last(env_int, owner, "target_completed_by_teammate_proxy", "target_covered_by_teammate")
            elif owner >= 0:
                self._emit(
                    "target_completed_proxy",
                    env_id=env_int,
                    robot_id=owner,
                    target_id=target_int,
                    method_name=method_name,
                    details={"completion_source": "viewpoints_covered"},
                )
                self._set_robot_last(env_int, owner, "target_completed_proxy", "target_covered")
            else:
                self._emit(
                    "active_target_became_covered_proxy",
                    env_id=env_int,
                    target_id=target_int,
                    method_name=method_name,
                    details={
                        "completion_source": "viewpoints_covered",
                        "limitation": "no_active_proxy_owner_or_completing_robot_id_available",
                    },
                )
            self._complete_target_proxy(env_int, target_int)
        self._sync_completed_tasks(post["viewpoints_covered"])

    def _completed_by_robot_tensor(self, external_diagnostics: Mapping[str, Any] | None) -> torch.Tensor | None:
        if external_diagnostics is None:
            return None
        value = external_diagnostics.get("completed_by_robot_ids")
        if value is None:
            value = external_diagnostics.get("coverage_completed_by_robot_ids")
        if value is None:
            return None
        if not isinstance(value, torch.Tensor):
            raise TypeError("completed_by_robot_ids must be a torch.Tensor when supplied")
        expected = (self.num_envs, self.num_tasks)
        if tuple(value.shape) != expected:
            raise ValueError(f"completed_by_robot_ids must have shape {expected}, got {tuple(value.shape)}")
        return value.to(device=self.device, dtype=torch.long)

    def _complete_target_proxy(self, env_id: int, target_id: int) -> None:
        self.task_state_proxy[env_id, target_id] = TASK_COMPLETED
        self.task_owner_proxy[env_id, target_id] = -1
        active_robots = torch.nonzero(self.active_target_proxy[env_id] == int(target_id), as_tuple=False).flatten()
        for robot_tensor in active_robots.detach().cpu().tolist():
            robot_id = int(robot_tensor)
            self.robot_state_proxy[env_id, robot_id] = ROBOT_IDLE_PROXY
            self.active_target_proxy[env_id, robot_id] = NO_ACTIVE_TARGET
            self.pair_state_proxy[env_id, robot_id, target_id] = PAIR_COMPLETED
            self.attempt_start_step_proxy[env_id, robot_id] = -1
            self.attempt_age_proxy[env_id, robot_id] = 0

    def _observe_budget_failures(
        self,
        external_diagnostics: Mapping[str, Any] | None,
        *,
        method_name: str | None,
    ) -> None:
        for env_id, robot_id, target_id, reason in self._iter_budget_failure_pairs(external_diagnostics):
            active_target = int(self.active_target_proxy[env_id, robot_id].item())
            if target_id < 0:
                target_id = active_target
            if target_id < 0 or target_id >= self.num_tasks:
                continue
            self.pair_state_proxy[env_id, robot_id, target_id] = PAIR_FAILED_BUDGET_PROXY
            self._emit(
                "budget_failure_proxy",
                env_id=env_id,
                robot_id=robot_id,
                target_id=target_id,
                method_name=method_name,
                details={"failure_source": reason},
            )
            self._release_pair_proxy(env_id, robot_id, target_id, reason="budget_failure_proxy")
            self.robot_state_proxy[env_id, robot_id] = ROBOT_RELEASED_PROXY
            self._emit(
                "release_proxy",
                env_id=env_id,
                robot_id=robot_id,
                target_id=target_id,
                method_name=method_name,
                details={
                    "release_source": "budget_failure_proxy",
                    "behavior_changed": False,
                },
            )
            self._set_robot_last(env_id, robot_id, "release_proxy", "budget_failure_release_proxy")

    def _iter_budget_failure_pairs(
        self,
        external_diagnostics: Mapping[str, Any] | None,
    ) -> list[tuple[int, int, int, str]]:
        if external_diagnostics is None:
            return []
        pairs: list[tuple[int, int, int, str]] = []
        raw_pairs = external_diagnostics.get("budget_failure_pairs")
        if raw_pairs is not None:
            if not isinstance(raw_pairs, Sequence) or isinstance(raw_pairs, (str, bytes)):
                raise TypeError("budget_failure_pairs must be a sequence of mappings")
            for item in raw_pairs:
                if not isinstance(item, Mapping):
                    raise TypeError("budget_failure_pairs entries must be mappings")
                env_id = int(item.get("env_id", 0))
                robot_id = int(item["robot_id"])
                target_id = int(item.get("target_id", NO_ACTIVE_TARGET))
                reason = str(item.get("reason", "budget_trigger"))
                self._validate_pair_indices(env_id, robot_id, target_id, allow_negative_target=True)
                pairs.append((env_id, robot_id, target_id, reason))
        mask = external_diagnostics.get("budget_failure_mask")
        if mask is not None:
            if not isinstance(mask, torch.Tensor):
                raise TypeError("budget_failure_mask must be a torch.Tensor when supplied")
            expected = (self.num_envs, self.num_robots, self.num_tasks)
            if tuple(mask.shape) != expected:
                raise ValueError(f"budget_failure_mask must have shape {expected}, got {tuple(mask.shape)}")
            for env_id, robot_id, target_id in torch.nonzero(
                mask.to(device=self.device, dtype=torch.bool), as_tuple=False
            ).detach().cpu().tolist():
                pairs.append((int(env_id), int(robot_id), int(target_id), "budget_trigger"))
        return pairs

    def _validate_pair_indices(self, env_id: int, robot_id: int, target_id: int, *, allow_negative_target: bool) -> None:
        if not 0 <= env_id < self.num_envs:
            raise ValueError(f"env_id out of range: {env_id}")
        if not 0 <= robot_id < self.num_robots:
            raise ValueError(f"robot_id out of range: {robot_id}")
        if target_id < 0 and allow_negative_target:
            return
        if not 0 <= target_id < self.num_tasks:
            raise ValueError(f"target_id out of range: {target_id}")

    def _release_pair_proxy(self, env_id: int, robot_id: int, target_id: int, *, reason: str) -> None:
        if 0 <= target_id < self.num_tasks:
            self.pair_state_proxy[env_id, robot_id, target_id] = PAIR_RELEASED_PROXY
            if int(self.task_owner_proxy[env_id, target_id].item()) == robot_id:
                self.task_owner_proxy[env_id, target_id] = -1
            if int(self.task_state_proxy[env_id, target_id].item()) != TASK_COMPLETED:
                self.task_state_proxy[env_id, target_id] = TASK_OPEN_PROXY
        if int(self.active_target_proxy[env_id, robot_id].item()) == target_id:
            self.active_target_proxy[env_id, robot_id] = NO_ACTIVE_TARGET
        self.attempt_start_step_proxy[env_id, robot_id] = -1
        self.attempt_age_proxy[env_id, robot_id] = 0
        self._last_transition_reason[env_id][robot_id] = str(reason)

    def _clear_robot_active_proxy(self, env_id: int, robot_id: int, target_id: int, *, reason: str) -> None:
        if 0 <= target_id < self.num_tasks and int(self.task_owner_proxy[env_id, target_id].item()) == robot_id:
            self.task_owner_proxy[env_id, target_id] = -1
            if int(self.task_state_proxy[env_id, target_id].item()) != TASK_COMPLETED:
                self.task_state_proxy[env_id, target_id] = TASK_OPEN_PROXY
        self.robot_state_proxy[env_id, robot_id] = ROBOT_IDLE_PROXY
        self.active_target_proxy[env_id, robot_id] = NO_ACTIVE_TARGET
        self.attempt_start_step_proxy[env_id, robot_id] = -1
        self.attempt_age_proxy[env_id, robot_id] = 0
        self._last_transition_reason[env_id][robot_id] = str(reason)

    def _set_robot_last(self, env_id: int, robot_id: int, event_type: str, reason: str) -> None:
        self._last_event_type[env_id][robot_id] = str(event_type)
        self._last_transition_reason[env_id][robot_id] = str(reason)

    def _emit(
        self,
        event_type: str,
        *,
        env_id: int,
        robot_id: int | None = None,
        target_id: int | None = None,
        method_name: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        event = AssignmentLifecycleEvent(
            event_type=str(event_type),
            env_id=int(env_id),
            step=int(self.step[int(env_id)].item()),
            robot_id=None if robot_id is None else int(robot_id),
            target_id=None if target_id is None else int(target_id),
            method_name=None if method_name is None else str(method_name),
            details=dict(details or {}),
        )
        self._total_event_count += 1
        if self.retain_events:
            self._events.append(event)


__all__ = [
    "ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK",
    "AssignmentLifecycleEvent",
    "AssignmentLifecycleTransitionLogger",
    "NO_ACTIVE_TARGET",
    "NO_PROPOSAL_SEEN",
    "PAIR_ACTIVE_PROXY",
    "PAIR_COMPLETED",
    "PAIR_FAILED_BUDGET_PROXY",
    "PAIR_NONE",
    "PAIR_RELEASED_PROXY",
    "PAIR_STATE_PROXY_NAMES",
    "PAIR_TIMEOUT_PROXY",
    "ROBOT_ACTIVE_PROXY",
    "ROBOT_IDLE_PROXY",
    "ROBOT_RELEASED_PROXY",
    "ROBOT_RESET_PROXY",
    "ROBOT_STATE_PROXY_NAMES",
    "TASK_CLAIMED_PROXY",
    "TASK_COMPLETED",
    "TASK_OPEN_PROXY",
    "TASK_STATE_PROXY_NAMES",
]
