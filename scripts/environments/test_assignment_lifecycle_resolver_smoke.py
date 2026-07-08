"""Pure smoke tests for the shared assignment lifecycle resolver prototype.

These tests use fake assignment problem dictionaries and decoded assignment
proposals only. They do not launch Isaac Sim, run playback/evaluation, train,
or integrate the resolver into runtime paths.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from assignment_lifecycle_resolver import (  # noqa: E402
    NO_TARGET,
    PAIR_ACTIVE,
    PAIR_COMPLETED,
    PAIR_NONE,
    PAIR_RELEASED_BUDGET,
    REASON_BUDGET_FAILURE,
    REJECT_CLAIM_LOST,
    REJECT_COVERED_TARGET,
    REJECT_FAILED_PAIR,
    REJECT_OWNED_TARGET,
    REJECT_SWITCH_DISABLED,
    ROBOT_EXECUTING,
    ROBOT_IDLE,
    AssignmentLifecycleResolver,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _proposal(values: list[list[int]]) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.long)


def _problem(
    *,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    covered: torch.Tensor | None = None,
    available: torch.Tensor | None = None,
    feasible: torch.Tensor | None = None,
    cost_matrix: torch.Tensor | None = None,
) -> dict[str, Any]:
    if covered is None:
        covered = torch.zeros(num_envs, num_tasks, dtype=torch.bool)
    else:
        covered = covered.clone().to(dtype=torch.bool)
    if available is None:
        available = torch.ones(num_envs, num_robots, num_tasks, dtype=torch.bool)
    else:
        available = available.clone().to(dtype=torch.bool)
    if feasible is None:
        feasible = torch.ones(num_envs, num_robots, num_tasks, dtype=torch.bool)
    else:
        feasible = feasible.clone().to(dtype=torch.bool)
    available = available & (~covered[:, None, :])
    feasible = feasible & (~covered[:, None, :])
    if cost_matrix is None:
        target_base = torch.arange(num_tasks, dtype=torch.float32).view(1, 1, num_tasks)
        robot_offset = torch.arange(num_robots, dtype=torch.float32).view(1, num_robots, 1) * 0.1
        env_offset = torch.arange(num_envs, dtype=torch.float32).view(num_envs, 1, 1) * 0.01
        cost_matrix = target_base + robot_offset + env_offset
    else:
        cost_matrix = cost_matrix.clone().to(dtype=torch.float32)
    return {
        "num_envs": int(num_envs),
        "num_agents": int(num_robots),
        "num_viewpoints": int(num_tasks),
        "available_mask": available,
        "feasible_mask": feasible,
        "viewpoints_covered": covered,
        "cost_matrix": cost_matrix,
    }


def _event_types(events: list[dict[str, Any]]) -> list[str]:
    return [str(event["event_type"]) for event in events]


def _assert_events_include(events: list[dict[str, Any]], expected: list[str]) -> None:
    got = _event_types(events)
    for event_type in expected:
        _assert(event_type in got, f"missing event {event_type}; got {got}")


def _clone_problem(problem: dict[str, Any]) -> dict[str, Any]:
    cloned: dict[str, Any] = {}
    for key, value in problem.items():
        if isinstance(value, torch.Tensor):
            cloned[key] = value.clone()
        else:
            cloned[key] = copy.deepcopy(value)
    return cloned


def _assert_problem_unchanged(before: dict[str, Any], after: dict[str, Any]) -> None:
    for key, expected in before.items():
        actual = after[key]
        if isinstance(expected, torch.Tensor):
            _assert(torch.equal(expected, actual), f"problem tensor {key!r} was mutated")
        else:
            _assert(expected == actual, f"problem field {key!r} was mutated")


def _assert_snapshot_same(before: dict[str, Any], after: dict[str, Any], *, ignore_event_count: bool = False) -> None:
    for key, expected in before.items():
        if ignore_event_count and key == "event_count":
            continue
        actual = after[key]
        if isinstance(expected, torch.Tensor):
            _assert(torch.equal(expected, actual), f"snapshot tensor {key!r} changed")
        elif isinstance(expected, dict):
            _assert(expected == actual, f"snapshot mapping {key!r} changed")
        else:
            _assert(expected == actual, f"snapshot field {key!r} changed")


def _start_target(
    resolver: AssignmentLifecycleResolver,
    *,
    target_id: int,
    num_envs: int = 1,
    num_robots: int = 1,
    num_tasks: int = 5,
    robot_id: int = 0,
) -> tuple[dict[str, Any], torch.Tensor]:
    problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
    proposal = torch.full((num_envs, num_robots), NO_TARGET, dtype=torch.long)
    proposal[:, robot_id] = target_id
    result = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    _assert(int(result.effective_assignment[0, robot_id].item()) == target_id, "target start failed")
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=result.effective_assignment,
        post_step_problem=problem,
    )
    resolver.pop_events()
    return problem, proposal


def _case_disabled_absolute_identity() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=3, enabled=False)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
    proposal = _proposal([[4, -2]])
    before_snapshot = resolver.snapshot()
    before_problem = _clone_problem(problem)
    before_proposal = proposal.clone()
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    post = resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem,
        external_diagnostics={"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 1}]},
    )
    after_snapshot = resolver.snapshot()
    _assert(torch.equal(pre.effective_assignment.cpu(), before_proposal), "disabled effective assignment changed proposal")
    _assert(pre.behavior_changed is False, "disabled pre-step reported behavior change")
    _assert(post.behavior_changed is False, "disabled post-step reported behavior change")
    _assert(resolver.pop_events() == [], "disabled resolver emitted events")
    _assert_snapshot_same(before_snapshot, after_snapshot)
    _assert_problem_unchanged(before_problem, problem)
    _assert(torch.equal(proposal, before_proposal), "disabled resolver mutated proposal")
    return {"case": "disabled_absolute_identity", "passed": True}


def _case_idle_target_claim() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[2]]))
    events = resolver.pop_events()
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 2, "idle claim effective target mismatch")
    _assert(bool(pre.new_claim_started[0, 0].item()), "new claim flag missing")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == 2, "active target not latched")
    _assert(int(snapshot["task_owner_robot_id"][0, 2].item()) == 0, "owner not created")
    _assert(int(snapshot["robot_execution_state"][0, 0].item()) == ROBOT_EXECUTING, "robot not executing")
    _assert(int(snapshot["pair_state"][0, 0, 2].item()) == PAIR_ACTIVE, "pair not active")
    _assert_events_include(events, ["attempt_started"])
    return {"case": "idle_target_claim", "passed": True}


def _case_idle_noop() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=3, enabled=True)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[-1]]))
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == NO_TARGET, "idle noop effective mismatch")
    _assert(int(snapshot["robot_execution_state"][0, 0].item()) == ROBOT_IDLE, "idle noop changed state")
    _assert_events_include(resolver.pop_events(), ["noop_idle"])
    return {"case": "idle_noop", "passed": True}


def _case_same_target_continuation() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
    problem, _ = _start_target(resolver, target_id=1, num_tasks=4)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[1]]))
    _assert(int(pre.effective_assignment[0, 0].item()) == 1, "same-target continuation effective mismatch")
    _assert(bool(pre.continued_from_active_target[0, 0].item()), "continuation flag missing")
    _assert(pre.behavior_changed is False, "same-target continuation should not change proposal")
    _assert_events_include(resolver.pop_events(), ["attempt_continued_same_target"])
    return {"case": "same_target_continuation", "passed": True}


def _case_noop_as_continue() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
    problem, _ = _start_target(resolver, target_id=1, num_tasks=4)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[-1]]))
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 1, "noop did not continue active target")
    _assert(pre.behavior_changed is True, "noop-as-continue must report behavior_changed")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == 1, "noop released active target")
    _assert_events_include(resolver.pop_events(), ["attempt_continued_noop_contract_c"])
    return {"case": "noop_as_continue", "passed": True}


def _case_switch_rejected() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=5, enabled=True)
    problem, _ = _start_target(resolver, target_id=1, num_tasks=5)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[3]]))
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 1, "switch changed effective assignment")
    _assert(bool(pre.switch_rejected[0, 0].item()), "switch rejection flag missing")
    _assert(int(pre.proposal_rejected_reason[0, 0].item()) == REJECT_SWITCH_DISABLED, "switch reason mismatch")
    _assert(int(snapshot["task_owner_robot_id"][0, 1].item()) == 0, "old target owner lost")
    _assert(int(snapshot["task_owner_robot_id"][0, 3].item()) == -1, "new target was claimed")
    _assert_events_include(resolver.pop_events(), ["switch_rejected_executing"])
    return {"case": "switch_rejected", "passed": True}


def _case_completion_release() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
    problem, proposal = _start_target(resolver, target_id=2, num_tasks=4)
    covered = torch.zeros(1, 4, dtype=torch.bool)
    covered[0, 2] = True
    post_problem = _problem(num_envs=1, num_robots=1, num_tasks=4, covered=covered)
    post = resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=proposal,
        post_step_problem=post_problem,
    )
    snapshot = resolver.snapshot()
    _assert(bool(post.completed[0, 0].item()), "completion result missing")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == NO_TARGET, "completion did not clear active")
    _assert(int(snapshot["task_owner_robot_id"][0, 2].item()) == -1, "completion did not clear owner")
    _assert(int(snapshot["robot_execution_state"][0, 0].item()) == ROBOT_IDLE, "completion did not idle robot")
    _assert(int(snapshot["pair_state"][0, 0, 2].item()) == PAIR_COMPLETED, "completion pair state mismatch")
    _assert_events_include(resolver.pop_events(), ["target_completed"])
    return {"case": "completion_release", "passed": True}


def _case_budget_failure_release_and_reclaim() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=4, enabled=True)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    proposal = _proposal([[2, -1]])
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    resolver.pop_events()
    post = resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem,
        external_diagnostics={"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 2, "reason": "budget_trigger"}]},
    )
    events = resolver.pop_events()
    snapshot = resolver.snapshot()
    _assert(bool(post.released[0, 0].item()), "budget release result missing")
    _assert(int(post.release_reason[0, 0].item()) == REASON_BUDGET_FAILURE, "release reason mismatch")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == NO_TARGET, "budget release active not cleared")
    _assert(int(snapshot["task_owner_robot_id"][0, 2].item()) == -1, "budget release owner not cleared")
    _assert(int(snapshot["pair_state"][0, 0, 2].item()) == PAIR_RELEASED_BUDGET, "pair not released-budget")
    _assert_events_include(events, ["budget_failure", "release_budget_failure"])

    retry = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[2, -1]]))
    retry_events = resolver.pop_events()
    _assert(int(retry.effective_assignment[0, 0].item()) == NO_TARGET, "failed pair reclaim was not rejected")
    _assert(int(retry.proposal_rejected_reason[0, 0].item()) == REJECT_FAILED_PAIR, "failed pair reject reason mismatch")
    _assert_events_include(retry_events, ["failed_pair_reclaim_rejected"])

    teammate = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[-1, 2]]))
    teammate_snapshot = resolver.snapshot()
    _assert(int(teammate.effective_assignment[0, 1].item()) == 2, "teammate could not claim released target")
    _assert(int(teammate_snapshot["task_owner_robot_id"][0, 2].item()) == 1, "teammate owner missing")
    return {"case": "budget_failure_release_failed_pair_and_teammate_claim", "passed": True}


def _case_failed_pair_cleared_on_completion() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=3, enabled=True)
    problem, proposal = _start_target(resolver, target_id=1, num_tasks=3)
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=proposal,
        post_step_problem=problem,
        external_diagnostics={"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 1}]},
    )
    covered = torch.zeros(1, 3, dtype=torch.bool)
    covered[0, 1] = True
    post_problem = _problem(num_envs=1, num_robots=1, num_tasks=3, covered=covered)
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=_proposal([[-1]]),
        effective_assignment=_proposal([[-1]]),
        post_step_problem=post_problem,
    )
    snapshot = resolver.snapshot()
    _assert(int(snapshot["pair_state"][0, 0, 1].item()) == PAIR_COMPLETED, "completion did not clear failed/released pair")
    return {"case": "failed_pair_cleared_on_completion", "passed": True}


def _case_failed_pair_cleared_on_reset() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=2, num_robots=1, num_tasks=3, enabled=True)
    problem = _problem(num_envs=2, num_robots=1, num_tasks=3)
    proposal = _proposal([[1], [2]])
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem,
        external_diagnostics={"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 1}]},
    )
    resolver.reset(env_ids=[0])
    snapshot = resolver.snapshot()
    _assert(int(snapshot["pair_state"][0, 0, 1].item()) == PAIR_NONE, "subset reset did not clear failed pair")
    _assert(int(snapshot["active_target_id"][1, 0].item()) == 2, "subset reset affected other env")
    resolver.reset()
    snapshot = resolver.snapshot()
    _assert(int(snapshot["active_target_id"][1, 0].item()) == NO_TARGET, "full reset did not clear other env")
    _assert(int(snapshot["pair_state"][1, 0, 2].item()) == PAIR_NONE, "full reset did not clear pair")
    return {"case": "failed_pair_cleared_on_reset", "passed": True}


def _case_exact_conflict_arbitration() -> dict[str, Any]:
    cost = torch.full((1, 2, 5), 10.0)
    cost[0, 0, 4] = 3.0
    cost[0, 1, 4] = 2.0
    problem = _problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=cost)
    proposal = _proposal([[4, 4]])
    proposal_before = proposal.clone()
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=5, enabled=True)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    events = resolver.pop_events()
    _assert(torch.equal(proposal, proposal_before), "conflict arbitration mutated proposal")
    _assert(int(pre.effective_assignment[0, 1].item()) == 4, "lowest-cost robot did not win")
    _assert(int(pre.effective_assignment[0, 0].item()) == NO_TARGET, "loser effective assignment mismatch")
    _assert(bool(pre.claim_conflict[0, 0].item()) and bool(pre.claim_conflict[0, 1].item()), "claim conflict flags missing")
    _assert(int(pre.proposal_rejected_reason[0, 0].item()) == REJECT_CLAIM_LOST, "claim lost reason mismatch")
    conflicts = [event for event in events if event["event_type"] == "exact_claim_conflict_resolved"]
    _assert(conflicts and conflicts[0]["winner_robot_id"] == 1, "conflict winner event mismatch")
    _assert_events_include(events, ["claim_lost"])

    tie_cost = torch.full((1, 2, 5), 10.0)
    tie_cost[0, 0, 4] = 2.0
    tie_cost[0, 1, 4] = 2.0
    tie_resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=5, enabled=True)
    tie_pre = tie_resolver.resolve_pre_step(
        problem=_problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=tie_cost),
        assignment_proposal=proposal,
    )
    _assert(int(tie_pre.effective_assignment[0, 0].item()) == 4, "robot-id tie-break failed")

    bad_cost = torch.full((1, 2, 5), float("nan"))
    bad_resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=5, enabled=True)
    bad_pre = bad_resolver.resolve_pre_step(
        problem=_problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=bad_cost),
        assignment_proposal=proposal,
    )
    _assert(int(bad_pre.effective_assignment[0, 0].item()) == 4, "non-finite fallback did not use lower robot id")
    return {"case": "exact_conflict_arbitration", "passed": True}


def _case_active_owner_priority() -> dict[str, Any]:
    cost = torch.full((1, 2, 4), 10.0)
    cost[0, 1, 1] = 0.0
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=4, enabled=True)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4, cost_matrix=cost)
    resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[1, -1]]))
    resolver.pop_events()
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[-1, 1]]))
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 1, "owner did not continue via noop")
    _assert(int(pre.effective_assignment[0, 1].item()) == NO_TARGET, "teammate stole owned target")
    _assert(int(pre.proposal_rejected_reason[0, 1].item()) == REJECT_OWNED_TARGET, "owned target reason mismatch")
    _assert(int(snapshot["task_owner_robot_id"][0, 1].item()) == 0, "existing owner was not preserved")
    _assert_events_include(resolver.pop_events(), ["owned_target_rejected"])
    return {"case": "active_owner_priority", "passed": True}


def _case_covered_target_rejected() -> dict[str, Any]:
    covered = torch.zeros(1, 3, dtype=torch.bool)
    covered[0, 2] = True
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3, covered=covered)
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=3, enabled=True)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[2]]))
    _assert(int(pre.effective_assignment[0, 0].item()) == NO_TARGET, "covered target was accepted")
    _assert(int(pre.proposal_rejected_reason[0, 0].item()) == REJECT_COVERED_TARGET, "covered reject reason mismatch")
    _assert_events_include(resolver.pop_events(), ["covered_target_rejected"])
    return {"case": "covered_target_rejected", "passed": True}


def _case_active_target_infeasible_deferred() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
    problem, _ = _start_target(resolver, target_id=2, num_tasks=4)
    available = problem["available_mask"].clone()
    available[0, 0, 2] = False
    infeasible = _problem(num_envs=1, num_robots=1, num_tasks=4, available=available)
    pre = resolver.resolve_pre_step(problem=infeasible, assignment_proposal=_proposal([[2]]))
    snapshot = resolver.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 2, "infeasible active target was released")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == 2, "infeasible active owner cleared")
    _assert_events_include(resolver.pop_events(), ["active_target_infeasible_deferred"])
    return {"case": "active_target_infeasible_deferred", "passed": True}


def _case_invalid_proposals() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=3, enabled=True, strict_proposals=True)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    for values in ([[[-2]], [[3]], [[4]]]):
        try:
            resolver.resolve_pre_step(problem=problem, assignment_proposal=torch.tensor(values, dtype=torch.long).view(1, 1))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid proposal {values} did not raise")
    try:
        resolver.resolve_pre_step(problem=problem, assignment_proposal=torch.zeros(1, 2, dtype=torch.long))
    except ValueError:
        pass
    else:
        raise AssertionError("wrong proposal shape did not raise")
    return {"case": "invalid_proposals", "passed": True}


def _case_subset_reset() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=2, num_robots=1, num_tasks=4, enabled=True)
    problem = _problem(num_envs=2, num_robots=1, num_tasks=4)
    resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[1], [2]]))
    resolver.reset(env_ids=torch.tensor([0], dtype=torch.long))
    snapshot = resolver.snapshot()
    _assert(int(snapshot["active_target_id"][0, 0].item()) == NO_TARGET, "env 0 not reset")
    _assert(int(snapshot["active_target_id"][1, 0].item()) == 2, "env 1 incorrectly reset")
    return {"case": "subset_reset", "passed": True}


def _case_variable_shapes() -> dict[str, Any]:
    results = []
    for num_envs, num_robots, num_tasks in [(1, 1, 3), (2, 3, 5), (2, 4, 8)]:
        resolver = AssignmentLifecycleResolver(
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
            enabled=True,
        )
        problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
        proposal = torch.full((num_envs, num_robots), -1, dtype=torch.long)
        proposal[:, 0] = min(1, num_tasks - 1)
        pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
        snapshot = resolver.snapshot()
        _assert(tuple(pre.effective_assignment.shape) == (num_envs, num_robots), "effective shape mismatch")
        _assert(tuple(snapshot["active_target_id"].shape) == (num_envs, num_robots), "active shape mismatch")
        _assert(tuple(snapshot["task_owner_robot_id"].shape) == (num_envs, num_tasks), "owner shape mismatch")
        _assert(tuple(snapshot["pair_state"].shape) == (num_envs, num_robots, num_tasks), "pair shape mismatch")
        results.append({"E": num_envs, "M": num_robots, "N": num_tasks})
    return {"case": "variable_shapes", "shapes": results}


def _case_method_agnostic_behavior() -> dict[str, Any]:
    methods = ["happo", "random", "nearest", "greedy", "future_sota_placeholder"]
    signatures = []
    for method_name in methods:
        resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=1, num_tasks=4, enabled=True)
        problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
        pre = resolver.resolve_pre_step(
            problem=problem,
            assignment_proposal=_proposal([[2]]),
            method_metadata={"method_name": method_name},
        )
        events = resolver.pop_events()
        signatures.append(
            {
                "effective": pre.effective_assignment.detach().cpu().tolist(),
                "active": resolver.snapshot()["active_target_id"].detach().cpu().tolist(),
                "events": _event_types(events),
            }
        )
    first = signatures[0]
    for signature in signatures[1:]:
        _assert(signature == first, "method metadata changed resolver behavior")
    return {"case": "method_agnostic_behavior", "methods": methods}


def _case_input_non_mutation() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=4, enabled=True)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    problem_before = _clone_problem(problem)
    proposal = _proposal([[2, 2]])
    proposal_before = proposal.clone()
    diagnostics = {"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 2, "reason": "budget_trigger"}]}
    diagnostics_before = copy.deepcopy(diagnostics)
    done_env_ids = torch.tensor([0], dtype=torch.long)
    done_before = done_env_ids.clone()
    metadata = {"method_name": "new_sota_method_v1", "proposal_score": [0.4, 0.5]}
    metadata_before = copy.deepcopy(metadata)
    pre = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal, method_metadata=metadata)
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem,
        external_diagnostics=diagnostics,
        done_env_ids=done_env_ids,
        method_metadata=metadata,
    )
    _assert_problem_unchanged(problem_before, problem)
    _assert(torch.equal(proposal, proposal_before), "proposal mutated")
    _assert(diagnostics == diagnostics_before, "external diagnostics mutated")
    _assert(torch.equal(done_env_ids, done_before), "done env ids mutated")
    _assert(metadata == metadata_before, "method metadata mutated")
    return {"case": "input_non_mutation", "passed": True}


def _case_episode_persistent_failed_pair_limitation() -> dict[str, Any]:
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=2, num_tasks=3, enabled=True)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
    start = resolver.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[1, -1]]))
    resolver.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=_proposal([[1, -1]]),
        effective_assignment=start.effective_assignment,
        post_step_problem=problem,
        external_diagnostics={"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 1}]},
    )
    unavailable_to_teammate = problem["available_mask"].clone()
    unavailable_to_teammate[0, 1, 1] = False
    stranded_problem = _problem(num_envs=1, num_robots=2, num_tasks=3, available=unavailable_to_teammate)
    retry = resolver.resolve_pre_step(problem=stranded_problem, assignment_proposal=_proposal([[1, -1]]))
    snapshot = resolver.snapshot()
    _assert(int(retry.effective_assignment[0, 0].item()) == NO_TARGET, "failed robot retry was not rejected")
    _assert(int(snapshot["task_owner_robot_id"][0, 1].item()) == -1, "stranded target unexpectedly owned")
    return {"case": "episode_persistent_failed_pair_limitation", "stranded_task_risk_observed": True}


def run_smoke() -> dict[str, Any]:
    cases = [
        _case_disabled_absolute_identity(),
        _case_idle_target_claim(),
        _case_idle_noop(),
        _case_same_target_continuation(),
        _case_noop_as_continue(),
        _case_switch_rejected(),
        _case_completion_release(),
        _case_budget_failure_release_and_reclaim(),
        _case_failed_pair_cleared_on_completion(),
        _case_failed_pair_cleared_on_reset(),
        _case_exact_conflict_arbitration(),
        _case_active_owner_priority(),
        _case_covered_target_rejected(),
        _case_active_target_infeasible_deferred(),
        _case_invalid_proposals(),
        _case_subset_reset(),
        _case_variable_shapes(),
        _case_method_agnostic_behavior(),
        _case_input_non_mutation(),
        _case_episode_persistent_failed_pair_limitation(),
    ]
    return {
        "status": "passed",
        "num_cases": len(cases),
        "cases": cases,
        "notes": [
            "pure fake-sequence resolver smoke only",
            "no runtime integration",
            "no playback, evaluation, or training",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Assignment lifecycle resolver smoke passed: {result['num_cases']} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
