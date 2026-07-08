"""Pure smoke tests for resolver runtime adapter integration.

The tests use fake assignment problems, fake controller recorders, and
temporary output directories only. They do not launch Isaac Sim, run playback,
evaluate methods, train, or invoke environment physics.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import tempfile
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
    PAIR_RELEASED_BUDGET,
    REJECT_FAILED_PAIR,
    ROBOT_EXECUTING,
)
from assignment_lifecycle_resolver_runtime import (  # noqa: E402
    ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION,
    AssignmentLifecycleResolverRuntimeAdapter,
    build_resolver_budget_failure_diagnostics,
    select_assignment_lifecycle_passive_input,
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
        robot_offset = torch.arange(num_robots, dtype=torch.float32).view(1, num_robots, 1) * 0.25
        env_offset = torch.arange(num_envs, dtype=torch.float32).view(num_envs, 1, 1) * 0.05
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


def _clone_problem(problem: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in problem.items():
        if isinstance(value, torch.Tensor):
            result[key] = value.clone()
        else:
            result[key] = copy.deepcopy(value)
    return result


def _assert_problem_unchanged(before: dict[str, Any], after: dict[str, Any]) -> None:
    for key, expected in before.items():
        actual = after[key]
        if isinstance(expected, torch.Tensor):
            _assert(torch.equal(expected, actual), f"problem tensor {key!r} was mutated")
        else:
            _assert(expected == actual, f"problem field {key!r} was mutated")


def _assert_snapshot_default(snapshot: dict[str, Any]) -> None:
    _assert(int(snapshot["event_count"]) == 0, "disabled resolver emitted events")
    _assert(int(snapshot["total_steps_observed"]) == 0, "disabled adapter counted steps")
    _assert(int(snapshot["total_events"]) == 0, "disabled adapter counted events")
    _assert(torch.all(snapshot["active_target_id"] == -1).item(), "disabled adapter latched active targets")
    _assert(torch.all(snapshot["task_owner_robot_id"] == -1).item(), "disabled adapter created owners")
    _assert(torch.all(snapshot["pair_state"] == 0).item(), "disabled adapter changed pair state")


def _event_types(events: list[dict[str, Any]]) -> list[str]:
    return [str(event["event_type"]) for event in events]


def _fake_controller_recorder(assignment: torch.Tensor, records: list[torch.Tensor]) -> dict[str, torch.Tensor]:
    records.append(assignment.detach().clone())
    return {"recorded_assignment": assignment.detach().clone()}


def _run_adapter_row(
    adapter: AssignmentLifecycleResolverRuntimeAdapter,
    *,
    problem: dict[str, Any],
    proposal: torch.Tensor,
    post_problem: dict[str, Any] | None = None,
    external_diagnostics: dict[str, Any] | None = None,
    done_env_ids: torch.Tensor | None = None,
) -> tuple[Any, Any]:
    pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    post = adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem if post_problem is None else post_problem,
        external_diagnostics=external_diagnostics,
        done_env_ids=done_env_ids,
    )
    return pre, post


def _case_disabled_adapter_absolute_identity() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "disabled"
        adapter = AssignmentLifecycleResolverRuntimeAdapter(
            enabled=False,
            num_envs=1,
            num_robots=2,
            num_tasks=3,
            output_dir=output_dir,
            log_diagnostics=False,
        )
        problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
        proposal = _proposal([[3, -2]])
        before_problem = _clone_problem(problem)
        before_proposal = proposal.clone()
        before_snapshot = adapter.snapshot()
        pre, post = _run_adapter_row(adapter, problem=problem, proposal=proposal)
        after_snapshot = adapter.snapshot()
        _assert(torch.equal(pre.effective_assignment.cpu(), before_proposal), "disabled effective != proposal")
        _assert(pre.behavior_changed is False and post.behavior_changed is False, "disabled behavior_changed true")
        _assert(adapter.pop_events() == [], "disabled adapter produced events")
        _assert_snapshot_default(before_snapshot)
        _assert_snapshot_default(after_snapshot)
        _assert_problem_unchanged(before_problem, problem)
        _assert(torch.equal(proposal, before_proposal), "disabled adapter mutated proposal")
        _assert(not output_dir.exists(), "disabled logging false created output files")
    return {"case": "disabled_adapter_absolute_identity", "passed": True}


def _case_disabled_wrapper_integration_identity() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=False, num_envs=1, num_robots=2, num_tasks=4)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    proposal = _proposal([[1, -1]])
    old_records: list[torch.Tensor] = []
    new_records: list[torch.Tensor] = []
    _fake_controller_recorder(proposal, old_records)
    pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    _fake_controller_recorder(pre.effective_assignment, new_records)
    _assert(torch.equal(old_records[0], new_records[0]), "disabled wrapper fake controller input changed")
    _assert_snapshot_default(adapter.snapshot())
    return {"case": "disabled_wrapper_integration_identity", "passed": True}


def _case_disabled_comparison_integration_identity() -> dict[str, Any]:
    labels = ["random", "nearest", "greedy", "future_sota_placeholder"]
    for label in labels:
        adapter = AssignmentLifecycleResolverRuntimeAdapter(
            enabled=False,
            num_envs=1,
            num_robots=2,
            num_tasks=5,
            method_name=label,
        )
        problem = _problem(num_envs=1, num_robots=2, num_tasks=5)
        solver_proposal = _proposal([[2, 3]])
        pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=solver_proposal)
        _assert(torch.equal(pre.effective_assignment.cpu(), solver_proposal), f"{label} disabled effective changed")
        _assert_snapshot_default(adapter.snapshot())
    return {"case": "disabled_comparison_integration_identity", "methods": labels}


def _case_enabled_noop_and_switch_controller_input() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=1, num_tasks=5)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=5)
    _run_adapter_row(adapter, problem=problem, proposal=_proposal([[1]]))
    adapter.pop_events()

    noop_pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[-1]]))
    controller_records: list[torch.Tensor] = []
    _fake_controller_recorder(noop_pre.effective_assignment, controller_records)
    _assert(int(controller_records[-1][0, 0].item()) == 1, "noop-as-continue did not feed active target")
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=_proposal([[-1]]),
        effective_assignment=noop_pre.effective_assignment,
        post_step_problem=problem,
    )
    adapter.pop_events()

    switch_pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[3]]))
    _fake_controller_recorder(switch_pre.effective_assignment, controller_records)
    _assert(int(controller_records[-1][0, 0].item()) == 1, "switch rejection did not feed previous active target")
    _assert(bool(switch_pre.switch_rejected[0, 0].item()), "switch rejection flag missing")
    return {"case": "enabled_noop_and_switch_controller_input", "passed": True}


def _case_budget_release_uses_effective_target() -> dict[str, Any]:
    for proposal_value in (3, -1):
        adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=1, num_tasks=5)
        problem = _problem(num_envs=1, num_robots=1, num_tasks=5)
        _run_adapter_row(adapter, problem=problem, proposal=_proposal([[1]]))
        adapter.pop_events()
        proposal = _proposal([[proposal_value]])
        pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
        budget_mask = torch.ones(1, 1, dtype=torch.bool)
        external = build_resolver_budget_failure_diagnostics(
            effective_assignment=pre.effective_assignment,
            budget_trigger_mask=budget_mask,
        )
        adapter.observe_post_step(
            pre_step_problem=problem,
            assignment_proposal=proposal,
            effective_assignment=pre.effective_assignment,
            post_step_problem=problem,
            external_diagnostics=external,
        )
        snapshot = adapter.snapshot()
        _assert(int(snapshot["pair_state"][0, 0, 1].item()) == PAIR_RELEASED_BUDGET, "active target was not released")
        if proposal_value >= 0:
            _assert(int(snapshot["task_owner_robot_id"][0, proposal_value].item()) == -1, "proposal target was claimed")
        events = _event_types(adapter.pop_events())
        _assert("budget_failure" in events and "release_budget_failure" in events, "budget/release events missing")
    return {"case": "budget_release_uses_effective_target", "passed": True}


def _case_proposal_effective_logging_and_passive_selection() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=1, num_tasks=4)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
    _run_adapter_row(adapter, problem=problem, proposal=_proposal([[1]]))
    adapter.pop_events()
    proposal = _proposal([[-1]])
    pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    passive, passive_type = select_assignment_lifecycle_passive_input(
        resolver_enabled=True,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
    )
    _assert(passive_type == "effective_assignment_from_resolver", "resolver-on passive stream mismatch")
    _assert(int(passive[0, 0].item()) == 1, "passive stream did not use effective assignment")
    proposal_passive, proposal_type = select_assignment_lifecycle_passive_input(
        resolver_enabled=False,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
    )
    _assert(proposal_type == "standardized_assignment", "resolver-off passive stream mismatch")
    _assert(int(proposal_passive[0, 0].item()) == -1, "resolver-off passive stream did not use proposal")
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=problem,
    )
    _assert(adapter.snapshot()["proposal_effective_changed_count"] == 1, "proposal/effective change not counted")
    return {"case": "proposal_effective_logging_and_passive_selection", "passed": True}


def _case_post_event_before_reset_and_subset_reset() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=3, num_robots=1, num_tasks=5)
    problem = _problem(num_envs=3, num_robots=1, num_tasks=5)
    _run_adapter_row(adapter, problem=problem, proposal=_proposal([[1], [2], [3]]))
    adapter.pop_events()
    covered = torch.zeros(3, 5, dtype=torch.bool)
    covered[0, 1] = True
    covered[2, 3] = True
    post_problem = _problem(num_envs=3, num_robots=1, num_tasks=5, covered=covered)
    proposal = _proposal([[1], [2], [3]])
    pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        effective_assignment=pre.effective_assignment,
        post_step_problem=post_problem,
        done_env_ids=torch.tensor([0, 2], dtype=torch.long),
    )
    events = _event_types(adapter.pop_events())
    _assert(events.index("target_completed") < events.index("reset"), "reset preceded completion")
    snapshot = adapter.snapshot()
    _assert(int(snapshot["active_target_id"][0, 0].item()) == -1, "env 0 not reset")
    _assert(int(snapshot["active_target_id"][2, 0].item()) == -1, "env 2 not reset")
    _assert(int(snapshot["active_target_id"][1, 0].item()) == 2, "env 1 state was incorrectly reset")
    return {"case": "post_event_before_reset_and_subset_reset", "passed": True}


def _case_method_isolation_and_output_files() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        methods = ["nearest", "greedy", "future_sota_placeholder"]
        adapters = []
        for index, method in enumerate(methods):
            adapter = AssignmentLifecycleResolverRuntimeAdapter(
                enabled=True,
                num_envs=1,
                num_robots=1,
                num_tasks=4,
                method_name=method,
                output_dir=root / method,
                log_diagnostics=True,
            )
            problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
            _run_adapter_row(adapter, problem=problem, proposal=_proposal([[index + 1]]))
            adapters.append(adapter)
        summaries = [adapter.finalize() for adapter in adapters]
        for adapter, method, summary in zip(adapters, methods, summaries, strict=True):
            output_dir = root / method
            events_path = output_dir / "assignment_lifecycle_resolver_events.jsonl"
            summary_path = output_dir / "assignment_lifecycle_resolver_summary.json"
            rows_path = output_dir / "assignment_lifecycle_resolver_rows.csv"
            _assert(events_path.exists(), f"{method} events missing")
            _assert(summary_path.exists(), f"{method} summary missing")
            _assert(rows_path.exists(), f"{method} rows missing")
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            parsed_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            rows = list(csv.DictReader(rows_path.open("r", encoding="utf-8")))
            _assert(parsed_summary["schema_version"] == ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION, "schema mismatch")
            _assert(parsed_summary["total_events"] == len(events), "event count mismatch")
            _assert(len(rows) == 1, "row CSV count mismatch")
            _assert(summary["method_name"] == method, "summary method mismatch")
        _assert(len({str((root / method).resolve()) for method in methods}) == len(methods), "output dirs collided")
        first_active = adapters[0].snapshot()["active_target_id"].clone()
        second_active = adapters[1].snapshot()["active_target_id"].clone()
        _assert(not torch.equal(first_active, second_active), "method resolver states appear shared")
        events_once = adapters[0].pop_events()
        events_twice = adapters[0].pop_events()
        _assert(events_once and not events_twice, "event draining failed")
        summary_a = adapters[0].finalize()
        summary_b = adapters[0].finalize()
        _assert(summary_a == summary_b, "finalize not idempotent")
    return {"case": "method_isolation_and_output_files", "methods": methods}


def _case_active_infeasibility_monitoring() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=1, num_tasks=4)
    problem = _problem(num_envs=1, num_robots=1, num_tasks=4)
    _run_adapter_row(adapter, problem=problem, proposal=_proposal([[2]]))
    adapter.pop_events()
    available = problem["available_mask"].clone()
    available[0, 0, 2] = False
    infeasible_problem = _problem(num_envs=1, num_robots=1, num_tasks=4, available=available)
    pre = adapter.resolve_pre_step(problem=infeasible_problem, assignment_proposal=_proposal([[2]]))
    snapshot = adapter.snapshot()
    _assert(int(pre.effective_assignment[0, 0].item()) == 2, "infeasibility monitor changed effective assignment")
    _assert(int(snapshot["active_target_id"][0, 0].item()) == 2, "infeasibility monitor changed active target")
    _assert(snapshot["active_target_infeasible_step_count"] == 1, "infeasible step count mismatch")
    _assert(snapshot["active_target_infeasible_max_streak"] == 1, "infeasible streak mismatch")
    return {"case": "active_infeasibility_monitoring", "passed": True}


def _case_stranded_detector_start_continue_recovery() -> dict[str, Any]:
    adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=2, num_tasks=3)
    problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
    start = adapter.resolve_pre_step(problem=problem, assignment_proposal=_proposal([[1, -1]]))
    external = build_resolver_budget_failure_diagnostics(
        effective_assignment=start.effective_assignment,
        budget_trigger_mask=torch.tensor([[True, False]], dtype=torch.bool),
    )
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=_proposal([[1, -1]]),
        effective_assignment=start.effective_assignment,
        post_step_problem=problem,
        external_diagnostics=external,
    )
    adapter.pop_events()

    available = problem["available_mask"].clone()
    available[0, 1, 1] = False
    stranded_problem = _problem(num_envs=1, num_robots=2, num_tasks=3, available=available)
    adapter.resolve_pre_step(problem=stranded_problem, assignment_proposal=_proposal([[-1, -1]]))
    started_events = _event_types(adapter.pop_events())
    _assert("stranded_failed_pair_started" in started_events, "stranded start event missing")
    adapter.observe_post_step(
        pre_step_problem=stranded_problem,
        assignment_proposal=_proposal([[-1, -1]]),
        effective_assignment=_proposal([[-1, -1]]),
        post_step_problem=stranded_problem,
    )

    adapter.resolve_pre_step(problem=stranded_problem, assignment_proposal=_proposal([[-1, -1]]))
    continue_events = _event_types(adapter.pop_events())
    _assert("stranded_failed_pair_started" not in continue_events, "stranded start repeated")
    adapter.observe_post_step(
        pre_step_problem=stranded_problem,
        assignment_proposal=_proposal([[-1, -1]]),
        effective_assignment=_proposal([[-1, -1]]),
        post_step_problem=stranded_problem,
    )

    recovered_problem = _problem(num_envs=1, num_robots=2, num_tasks=3)
    adapter.resolve_pre_step(problem=recovered_problem, assignment_proposal=_proposal([[-1, -1]]))
    recovered_events = _event_types(adapter.pop_events())
    _assert("stranded_failed_pair_recovered" in recovered_events, "stranded recovery event missing")
    snapshot = adapter.snapshot()
    _assert(snapshot["stranded_failed_pair_started_count"] == 1, "stranded started count mismatch")
    _assert(snapshot["stranded_failed_pair_recovered_count"] == 1, "stranded recovered count mismatch")
    _assert(torch.all(snapshot["active_target_id"] == -1).item(), "stranded detector changed active assignment")
    return {"case": "stranded_detector_start_continue_recovery", "passed": True}


def _case_variable_shapes_and_strict_proposals() -> dict[str, Any]:
    shapes = [(1, 1, 3), (2, 3, 5), (2, 4, 8)]
    for num_envs, num_robots, num_tasks in shapes:
        adapter = AssignmentLifecycleResolverRuntimeAdapter(
            enabled=True,
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
        )
        problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
        proposal = torch.full((num_envs, num_robots), -1, dtype=torch.long)
        proposal[:, 0] = min(1, num_tasks - 1)
        pre = adapter.resolve_pre_step(problem=problem, assignment_proposal=proposal)
        _assert(tuple(pre.effective_assignment.shape) == (num_envs, num_robots), "variable shape effective mismatch")
        snapshot = adapter.snapshot()
        _assert(tuple(snapshot["active_target_id"].shape) == (num_envs, num_robots), "variable active shape mismatch")

    strict_adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=True, num_envs=1, num_robots=1, num_tasks=3)
    strict_problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    for value in (-2, 3, 4):
        try:
            strict_adapter.resolve_pre_step(problem=strict_problem, assignment_proposal=_proposal([[value]]))
        except ValueError:
            pass
        else:
            raise AssertionError(f"strict invalid proposal {value} did not raise")
    disabled_adapter = AssignmentLifecycleResolverRuntimeAdapter(enabled=False, num_envs=1, num_robots=1, num_tasks=3)
    disabled_pre = disabled_adapter.resolve_pre_step(problem=strict_problem, assignment_proposal=_proposal([[4]]))
    _assert(int(disabled_pre.effective_assignment[0, 0].item()) == 4, "disabled mode imposed enabled value semantics")
    return {"case": "variable_shapes_and_strict_proposals", "shapes": shapes}


def _case_input_non_mutation_and_default_output_compatibility() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "no_output"
        adapter = AssignmentLifecycleResolverRuntimeAdapter(
            enabled=False,
            num_envs=1,
            num_robots=1,
            num_tasks=3,
            output_dir=output_dir,
            log_diagnostics=False,
        )
        problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
        post_problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
        before_problem = _clone_problem(problem)
        before_post = _clone_problem(post_problem)
        proposal = _proposal([[1]])
        before_proposal = proposal.clone()
        external = {"budget_failure_pairs": [{"env_id": 0, "robot_id": 0, "target_id": 1}]}
        before_external = copy.deepcopy(external)
        done_ids = torch.tensor([0], dtype=torch.long)
        before_done = done_ids.clone()
        episode_ids = torch.tensor([3], dtype=torch.long)
        before_episode = episode_ids.clone()
        metadata = {"method_name": "future_sota_placeholder", "proposal_type": "standardized_assignment"}
        before_metadata = copy.deepcopy(metadata)
        pre = adapter.resolve_pre_step(
            problem=problem,
            assignment_proposal=proposal,
            episode_ids=episode_ids,
            method_metadata=metadata,
        )
        effective_before = pre.effective_assignment.clone()
        adapter.observe_post_step(
            pre_step_problem=problem,
            assignment_proposal=proposal,
            effective_assignment=pre.effective_assignment,
            post_step_problem=post_problem,
            external_diagnostics=external,
            done_env_ids=done_ids,
            episode_ids=episode_ids,
            method_metadata=metadata,
        )
        _assert_problem_unchanged(before_problem, problem)
        _assert_problem_unchanged(before_post, post_problem)
        _assert(torch.equal(proposal, before_proposal), "proposal mutated")
        _assert(torch.equal(pre.effective_assignment, effective_before), "effective assignment mutated")
        _assert(external == before_external, "external diagnostics mutated")
        _assert(torch.equal(done_ids, before_done), "done ids mutated")
        _assert(torch.equal(episode_ids, before_episode), "episode ids mutated")
        _assert(metadata == before_metadata, "metadata mutated")
        _assert(not output_dir.exists(), "default disabled/logging false created output directory")
    return {"case": "input_non_mutation_and_default_output_compatibility", "passed": True}


def run_smoke() -> dict[str, Any]:
    cases = [
        _case_disabled_adapter_absolute_identity(),
        _case_disabled_wrapper_integration_identity(),
        _case_disabled_comparison_integration_identity(),
        _case_enabled_noop_and_switch_controller_input(),
        _case_budget_release_uses_effective_target(),
        _case_proposal_effective_logging_and_passive_selection(),
        _case_post_event_before_reset_and_subset_reset(),
        _case_method_isolation_and_output_files(),
        _case_active_infeasibility_monitoring(),
        _case_stranded_detector_start_continue_recovery(),
        _case_variable_shapes_and_strict_proposals(),
        _case_input_non_mutation_and_default_output_compatibility(),
    ]
    return {
        "status": "passed",
        "num_cases": len(cases),
        "cases": cases,
        "notes": [
            "pure Python/Torch runtime adapter smoke only",
            "no Isaac Sim launch",
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
        print(f"Assignment lifecycle resolver runtime smoke passed: {result['num_cases']} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
