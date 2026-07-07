"""Pure smoke tests for the passive assignment lifecycle transition logger.

The tests use fake assignment problem dictionaries and decoded assignment
proposals only. They do not launch Isaac Sim, run playback, train, change
assignments, or exercise controller/environment behavior.
"""

from __future__ import annotations

import argparse
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

from assignment_lifecycle import (  # noqa: E402
    ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK,
    AssignmentLifecycleTransitionLogger,
    NO_ACTIVE_TARGET,
    PAIR_NONE,
    ROBOT_IDLE_PROXY,
    TASK_COMPLETED,
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
    available = available & (~covered[:, None, :])
    if cost_matrix is None:
        base = torch.arange(num_tasks, dtype=torch.float32).view(1, 1, num_tasks)
        robot_offset = torch.arange(num_robots, dtype=torch.float32).view(1, num_robots, 1) * 0.1
        env_offset = torch.arange(num_envs, dtype=torch.float32).view(num_envs, 1, 1) * 0.01
        cost_matrix = base + robot_offset + env_offset
    else:
        cost_matrix = cost_matrix.clone().to(dtype=torch.float32)
    return {
        "num_envs": int(num_envs),
        "num_agents": int(num_robots),
        "num_viewpoints": int(num_tasks),
        "available_mask": available,
        "viewpoints_covered": covered,
        "cost_matrix": cost_matrix,
    }


def _event_types(events: list[dict[str, Any]]) -> list[str]:
    return [str(event["event_type"]) for event in events]


def _problem_tensor_clone(problem: dict[str, Any]) -> dict[str, torch.Tensor]:
    return {key: value.clone() for key, value in problem.items() if isinstance(value, torch.Tensor)}


def _assert_problem_unchanged(before: dict[str, torch.Tensor], after: dict[str, Any]) -> None:
    for key, expected in before.items():
        actual = after[key]
        _assert(torch.equal(actual, expected), f"problem tensor {key!r} was mutated")


def _assert_events_include(events: list[dict[str, Any]], expected: list[str]) -> None:
    event_types = _event_types(events)
    for event_type in expected:
        _assert(event_type in event_types, f"missing event {event_type}; got {event_types}")


def _run_sequence_a_normal_attempt() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=3)
    problem0 = _problem(num_envs=1, num_robots=1, num_tasks=3)
    proposal = _proposal([[2]])
    logger.update(pre_step_problem=problem0, assignment_proposal=proposal, post_step_problem=problem0)
    logger.update(pre_step_problem=problem0, assignment_proposal=proposal, post_step_problem=problem0)
    covered = torch.zeros(1, 3, dtype=torch.bool)
    covered[0, 2] = True
    problem_done = _problem(num_envs=1, num_robots=1, num_tasks=3, covered=covered)
    logger.update(pre_step_problem=problem0, assignment_proposal=proposal, post_step_problem=problem_done)
    events = logger.pop_events()
    _assert_events_include(events, ["attempt_started_proxy", "attempt_continued_proxy", "target_completed_proxy"])
    snapshot = logger.snapshot()
    _assert(int(snapshot["active_target_proxy"][0, 0].item()) == NO_ACTIVE_TARGET, "completed target was not cleared")
    _assert(int(snapshot["task_state_proxy"][0, 2].item()) == TASK_COMPLETED, "completed task state missing")
    return {"sequence": "normal_attempt", "events": _event_types(events)}


def _run_sequence_b_noop_idle() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=3)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    noop = _proposal([[-1]])
    logger.update(pre_step_problem=problem, assignment_proposal=noop, post_step_problem=problem)
    logger.update(pre_step_problem=problem, assignment_proposal=noop, post_step_problem=problem)
    events = logger.pop_events()
    _assert(_event_types(events).count("noop_idle_proxy") == 2, "noop idle events missing")
    _assert(int(logger.snapshot()["active_target_proxy"][0, 0].item()) == NO_ACTIVE_TARGET, "noop created active target")
    return {"sequence": "noop_idle", "events": _event_types(events)}


def _run_sequence_c_noop_after_active() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=3)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[1]]), post_step_problem=problem)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[-1]]), post_step_problem=problem)
    events = logger.pop_events()
    _assert_events_include(events, ["attempt_started_proxy", "noop_after_active_ambiguous"])
    _assert("attempt_continued_proxy" not in _event_types(events)[-1:], "noop was mislabeled as continuation")
    _assert(int(logger.snapshot()["active_target_proxy"][0, 0].item()) == NO_ACTIVE_TARGET, "noop ambiguity retained active target")
    return {"sequence": "noop_after_active", "events": _event_types(events)}


def _run_sequence_d_switch_request() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=5)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=5)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[1]]), post_step_problem=problem)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[3]]), post_step_problem=problem)
    events = logger.pop_events()
    _assert_events_include(events, ["attempt_started_proxy", "switch_request_proxy"])
    switch_events = [event for event in events if event["event_type"] == "switch_request_proxy"]
    _assert(switch_events[0]["previous_target_id"] == 1, "switch previous target mismatch")
    _assert(switch_events[0]["new_target_id"] == 3, "switch new target mismatch")
    _assert(int(logger.snapshot()["active_target_proxy"][0, 0].item()) == 3, "proxy did not advance to switched target")
    return {"sequence": "switch_request", "events": _event_types(events)}


def _run_sequence_e_budget_failure_release() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=4)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
    before = _problem_tensor_clone(problem)
    proposal = _proposal([[2]])
    proposal_before = proposal.clone()
    logger.update(pre_step_problem=problem, assignment_proposal=proposal, post_step_problem=problem)
    logger.update(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        post_step_problem=problem,
        external_diagnostics={
            "budget_failure_pairs": [
                {"env_id": 0, "robot_id": 0, "target_id": 2, "reason": "budget_trigger"}
            ]
        },
    )
    _assert_problem_unchanged(before, problem)
    _assert(torch.equal(proposal, proposal_before), "assignment proposal was mutated")
    events = logger.pop_events()
    _assert_events_include(events, ["budget_failure_proxy", "release_proxy"])
    snapshot = logger.snapshot()
    _assert(int(snapshot["active_target_proxy"][0, 0].item()) == NO_ACTIVE_TARGET, "budget release did not clear active")
    return {"sequence": "budget_failure_release", "events": _event_types(events), "input_not_mutated": True}


def _run_sequence_f_exact_conflict() -> dict[str, Any]:
    cost = torch.full((1, 2, 5), 10.0)
    cost[0, 0, 4] = 3.0
    cost[0, 1, 4] = 2.0
    problem = _problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=cost)
    proposal = _proposal([[4, 4]])
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=5)
    proposal_before = proposal.clone()
    logger.observe_pre_step(problem=problem, assignment_proposal=proposal, method_metadata={"method_name": "nearest"})
    _assert(torch.equal(proposal, proposal_before), "conflict diagnostics mutated proposal")
    events = logger.pop_events()
    conflicts = [event for event in events if event["event_type"] == "exact_claim_conflict_proxy"]
    _assert(len(conflicts) == 1, f"expected one conflict event, got {len(conflicts)}")
    _assert(conflicts[0]["would_be_winner_robot_id"] == 1, "lowest-cost conflict winner mismatch")
    _assert(conflicts[0]["would_be_loser_robot_ids"] == [0], "conflict loser mismatch")
    _assert(conflicts[0]["arbitration_rule"] == ARBITRATION_RULE_LOWEST_COST_ROBOT_ID_TIEBREAK, "rule mismatch")

    tie_cost = torch.full((1, 2, 5), 10.0)
    tie_cost[0, 0, 4] = 2.0
    tie_cost[0, 1, 4] = 2.0
    tie_problem = _problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=tie_cost)
    tie_logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=5)
    tie_logger.observe_pre_step(problem=tie_problem, assignment_proposal=proposal)
    tie_conflict = [event for event in tie_logger.pop_events() if event["event_type"] == "exact_claim_conflict_proxy"][0]
    _assert(tie_conflict["would_be_winner_robot_id"] == 0, "robot-id tie-breaker mismatch")

    no_cost_problem = _problem(num_envs=1, num_robots=2, num_tasks=5)
    no_cost_problem.pop("cost_matrix")
    no_cost_logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=5)
    no_cost_logger.observe_pre_step(problem=no_cost_problem, assignment_proposal=proposal)
    no_cost_conflict = [
        event for event in no_cost_logger.pop_events() if event["event_type"] == "exact_claim_conflict_proxy"
    ][0]
    _assert(no_cost_conflict["would_be_winner_robot_id"] == 0, "cost-unavailable fallback winner mismatch")
    _assert(no_cost_conflict["fallback_reason"] == "cost_unavailable_or_non_finite", "fallback reason mismatch")
    return {
        "sequence": "exact_conflict",
        "lowest_cost_winner": 1,
        "tie_winner": 0,
        "fallback_winner": 0,
        "proposal_not_mutated": True,
    }


def _run_sequence_g_teammate_completion() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=3)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[1, -1]]), post_step_problem=problem)
    covered = torch.zeros(1, 3, dtype=torch.bool)
    covered[0, 1] = True
    post = _problem(num_envs=1, num_robots=2, num_tasks=3, covered=covered)
    completed_by = torch.full((1, 3), -1, dtype=torch.long)
    completed_by[0, 1] = 1
    logger.update(
        pre_step_problem=problem,
        assignment_proposal=_proposal([[1, -1]]),
        post_step_problem=post,
        external_diagnostics={"completed_by_robot_ids": completed_by},
    )
    events = logger.pop_events()
    teammate_events = [event for event in events if event["event_type"] == "target_completed_by_teammate_proxy"]
    _assert(len(teammate_events) == 1, "teammate completion event missing")
    _assert(teammate_events[0]["completing_robot_id"] == 1, "teammate completion robot mismatch")
    return {"sequence": "teammate_completion", "events": _event_types(events)}


def _run_sequence_h_reset() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=2, num_robots=2, num_tasks=4)
    problem = _problem(num_envs=2, num_robots=2, num_tasks=4)
    logger.update(pre_step_problem=problem, assignment_proposal=_proposal([[1, -1], [2, -1]]), post_step_problem=problem)
    logger.pop_events()
    logger.reset(env_ids=torch.tensor([0], dtype=torch.long))
    snapshot = logger.snapshot()
    _assert(torch.all(snapshot["active_target_proxy"][0] == NO_ACTIVE_TARGET), "subset reset missed env 0")
    _assert(int(snapshot["active_target_proxy"][1, 0].item()) == 2, "subset reset cleared wrong env")
    _assert(torch.all(snapshot["pair_state_proxy"][0] == PAIR_NONE), "subset reset did not clear pair proxy")
    logger.reset()
    snapshot = logger.snapshot()
    _assert(torch.all(snapshot["active_target_proxy"] == NO_ACTIVE_TARGET), "full reset missed active targets")
    _assert(torch.all(snapshot["robot_state_proxy"] == ROBOT_IDLE_PROXY), "full reset missed robot states")
    events = logger.pop_events()
    _assert("reset_proxy" in _event_types(events), "reset event missing")
    return {"sequence": "reset", "subset_reset": True, "full_reset": True}


def _run_sequence_i_method_agnostic_equivalence() -> dict[str, Any]:
    method_names = ["happo", "random", "nearest", "greedy", "future_sota_placeholder"]
    reference_event_types: list[str] | None = None
    reference_snapshot: dict[str, torch.Tensor] | None = None
    for method_name in method_names:
        logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=4)
        problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
        logger.update(
            pre_step_problem=problem,
            assignment_proposal=_proposal([[1, -1]]),
            post_step_problem=problem,
            method_metadata={"method_name": method_name, "proposal_type": "one_target_per_robot"},
        )
        logger.update(
            pre_step_problem=problem,
            assignment_proposal=_proposal([[1, 2]]),
            post_step_problem=problem,
            method_metadata={"method_name": method_name, "proposal_confidence": 0.5},
        )
        event_types = _event_types(logger.pop_events())
        snapshot = logger.snapshot()
        comparable_snapshot = {
            key: value
            for key, value in snapshot.items()
            if isinstance(value, torch.Tensor)
        }
        if reference_event_types is None:
            reference_event_types = event_types
            reference_snapshot = comparable_snapshot
        else:
            _assert(event_types == reference_event_types, f"method {method_name} changed event types")
            assert reference_snapshot is not None
            for key, expected in reference_snapshot.items():
                _assert(torch.equal(comparable_snapshot[key], expected), f"method {method_name} changed {key}")
    return {"sequence": "method_agnostic_equivalence", "methods": method_names, "passed": True}


def _run_variable_shape_and_invalid_tests() -> dict[str, Any]:
    shapes = [(1, 1, 3), (2, 3, 5), (2, 4, 8)]
    shape_results = []
    for num_envs, num_robots, num_tasks in shapes:
        logger = AssignmentLifecycleTransitionLogger(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
        problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
        values = torch.full((num_envs, num_robots), -1, dtype=torch.long)
        values[:, 0] = min(1, num_tasks - 1)
        logger.update(pre_step_problem=problem, assignment_proposal=values, post_step_problem=problem)
        snapshot = logger.snapshot()
        _assert(tuple(snapshot["robot_state_proxy"].shape) == (num_envs, num_robots), "robot state shape mismatch")
        _assert(tuple(snapshot["task_state_proxy"].shape) == (num_envs, num_tasks), "task state shape mismatch")
        _assert(tuple(snapshot["pair_state_proxy"].shape) == (num_envs, num_robots, num_tasks), "pair state shape mismatch")
        shape_results.append([num_envs, num_robots, num_tasks])

    covered = torch.zeros(1, 3, dtype=torch.bool)
    covered[0, 1] = True
    covered_problem = _problem(num_envs=1, num_robots=1, num_tasks=3, covered=covered)
    covered_logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=3)
    covered_logger.update(
        pre_step_problem=covered_problem,
        assignment_proposal=_proposal([[1]]),
        post_step_problem=covered_problem,
    )
    covered_events = _event_types(covered_logger.pop_events())
    _assert("unavailable_target_proposal_proxy" in covered_events, "covered target diagnostic missing")
    _assert(
        int(covered_logger.snapshot()["active_target_proxy"][0, 0].item()) == NO_ACTIVE_TARGET,
        "covered proposal created active proxy",
    )

    invalid_logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=1, num_tasks=3)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    for bad in (-2, 3):
        try:
            invalid_logger.observe_pre_step(problem=problem, assignment_proposal=_proposal([[bad]]))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid proposal {bad} did not raise")

    return {
        "sequence": "variable_shape_invalid",
        "shapes": shape_results,
        "covered_target_diagnostic": True,
        "invalid_proposals_raise": True,
    }


def _run_sequence_j_no_mutation() -> dict[str, Any]:
    logger = AssignmentLifecycleTransitionLogger(num_envs=1, num_robots=2, num_tasks=4)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    post_problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    external = {
        "budget_failure_pairs": [
            {"env_id": 0, "robot_id": 0, "target_id": 1, "reason": "budget_trigger"}
        ]
    }
    before_pre = _problem_tensor_clone(problem)
    before_post = _problem_tensor_clone(post_problem)
    proposal = _proposal([[1, 2]])
    proposal_before = proposal.clone()
    external_before = json.dumps(external, sort_keys=True)
    logger.update(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        post_step_problem=post_problem,
        external_diagnostics=external,
    )
    _assert_problem_unchanged(before_pre, problem)
    _assert_problem_unchanged(before_post, post_problem)
    _assert(torch.equal(proposal, proposal_before), "proposal mutated")
    _assert(json.dumps(external, sort_keys=True) == external_before, "external diagnostics mutated")
    return {"sequence": "no_mutation", "problem_not_mutated": True, "proposal_not_mutated": True}


def run_smoke() -> dict[str, Any]:
    results = [
        _run_sequence_a_normal_attempt(),
        _run_sequence_b_noop_idle(),
        _run_sequence_c_noop_after_active(),
        _run_sequence_d_switch_request(),
        _run_sequence_e_budget_failure_release(),
        _run_sequence_f_exact_conflict(),
        _run_sequence_g_teammate_completion(),
        _run_sequence_h_reset(),
        _run_sequence_i_method_agnostic_equivalence(),
        _run_variable_shape_and_invalid_tests(),
        _run_sequence_j_no_mutation(),
    ]
    return {
        "status": "passed",
        "sequence_count": len(results),
        "results": results,
        "behavior_changed": False,
        "assignments_modified": False,
        "masks_modified": False,
        "observations_modified": False,
        "controller_or_env_invoked": False,
        "training_or_playback_invoked": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result_file", type=str, default=None, help="Optional JSON result path.")
    args = parser.parse_args()
    result = run_smoke()
    if args.result_file:
        path = Path(args.result_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[OK]: assignment lifecycle transition logger smoke passed: {json.dumps(result, sort_keys=True)}")


if __name__ == "__main__":
    main()
