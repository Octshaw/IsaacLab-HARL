"""Fake-env TTL boundary checks for failed-pair/release memory.

This script exercises wrapper-local Phase 9G failed-pair memory with the
existing fake assignment env. It does not launch Isaac simulation, playback, or
training, and it does not modify wrapper behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch

from test_assignment_failed_pair_memory_smoke import _assert, _make_wrapper


TRIGGER_STEP = 100
ROBOT_ID = 0
TARGET_ID = 2
TRACE_DURATIONS = (5, 6, 7, 10)


def _activate_memory(wrapper, *, duration_steps: int, trigger_step: int = TRIGGER_STEP) -> None:
    wrapper._assignment_step[:] = int(trigger_step)
    budget_trigger = torch.zeros(wrapper.num_envs, wrapper.num_agents, dtype=torch.bool)
    budget_trigger[0, ROBOT_ID] = True
    assignment = torch.full((wrapper.num_envs, wrapper.num_agents), -1, dtype=torch.long)
    assignment[0, ROBOT_ID] = TARGET_ID
    wrapper._activate_assignment_failed_pair_memory_for_budget_triggers(
        budget_trigger=budget_trigger,
        assignment=assignment,
    )
    _assert(
        int(wrapper._assignment_failed_pair_memory_remaining[0, ROBOT_ID, TARGET_ID].item()) == duration_steps,
        "manual budget-trigger activation did not set configured duration",
    )
    _assert(
        int(wrapper._assignment_failed_pair_memory_trigger_step[0, ROBOT_ID, TARGET_ID].item()) == trigger_step,
        "manual budget-trigger activation did not record trigger step",
    )


def _problem_with_pair_available(wrapper, *, available: bool = True) -> dict[str, Any]:
    problem = wrapper.unwrapped.get_assignment_problem()
    problem["available_mask"] = problem["available_mask"].clone()
    problem["available_mask"][0, ROBOT_ID, TARGET_ID] = bool(available)
    return problem


def _assignment_selecting_memorized_pair(wrapper) -> torch.Tensor:
    assignment = torch.full((wrapper.num_envs, wrapper.num_agents), -1, dtype=torch.long)
    assignment[0, ROBOT_ID] = TARGET_ID
    return assignment


def _assignment_noop(wrapper) -> torch.Tensor:
    return torch.full((wrapper.num_envs, wrapper.num_agents), -1, dtype=torch.long)


def _selected_available_mask(wrapper, assignment: torch.Tensor, available_actions: torch.Tensor) -> torch.Tensor:
    return wrapper._selected_available_mask(assignment, available_actions)


def _decision_trace_row(wrapper, *, logical_step: int, pair_available: bool = True) -> dict[str, Any]:
    problem = _problem_with_pair_available(wrapper, available=pair_available)
    assignment = _assignment_selecting_memorized_pair(wrapper)
    memory_before = int(wrapper._assignment_failed_pair_memory_remaining[0, ROBOT_ID, TARGET_ID].item())
    available_before = bool(problem["available_mask"][0, ROBOT_ID, TARGET_ID].item())
    available_actions = wrapper._build_available_actions(problem=problem)
    available_after = bool(available_actions[0, ROBOT_ID, TARGET_ID].item())
    noop_available = bool(available_actions[0, ROBOT_ID, -1].item())
    suppressed_count = int(wrapper._last_failed_pair_memory_suppressed_count[0, ROBOT_ID].item())
    fail_open_count = int(wrapper._last_failed_pair_memory_fail_open_count[0, ROBOT_ID].item())
    only_noop_remaining = bool(wrapper._last_failed_pair_memory_only_noop_remaining[0, ROBOT_ID].item())
    selected_available = _selected_available_mask(wrapper, assignment, available_actions)
    wrapper._update_assignment_diagnostics(
        assignment=assignment,
        pre_step_problem=problem,
        post_step_problem=problem,
        selected_available_mask=selected_available,
    )
    selected_pair_active = bool(wrapper._last_failed_pair_memory_selected_pair_active[0, ROBOT_ID].item())
    selected_pair_ttl = int(wrapper._last_failed_pair_memory_selected_pair_ttl_remaining[0, ROBOT_ID].item())
    memory_after = int(wrapper._assignment_failed_pair_memory_remaining[0, ROBOT_ID, TARGET_ID].item())

    _assert(int(wrapper._assignment_step[0].item()) == logical_step, "logical assignment step drifted")
    if memory_before > 0 and pair_available:
        _assert(not available_after, "active memory did not suppress available memorized pair")
        _assert(suppressed_count == 1, "active memory did not record one suppression")
        _assert(selected_pair_active, "selected_pair_active was false for active selected memorized pair")
        _assert(selected_pair_ttl == memory_before, "selected_pair_ttl did not match pre-decrement memory")
    if memory_before <= 0:
        _assert(available_after == available_before, "expired memory still changed available mask")
        _assert(suppressed_count == 0, "expired memory recorded suppression")
        _assert(not selected_pair_active, "expired memory reported selected pair active")
    _assert(memory_after == max(0, memory_before - 1), "memory did not decrement once after action diagnostics")
    _assert(noop_available, "noop was not preserved")

    return {
        "duration_steps": int(wrapper.assignment_failed_pair_memory_config["duration_steps"]),
        "trigger_step": TRIGGER_STEP,
        "build_available_actions_step": int(logical_step),
        "offset_from_trigger": int(logical_step - TRIGGER_STEP),
        "memory_remaining_before_decrement": memory_before,
        "memory_remaining_after_decrement": memory_after,
        "selected_pair_active": selected_pair_active,
        "selected_pair_ttl_remaining": selected_pair_ttl,
        "suppressed_count": suppressed_count,
        "fail_open_count": fail_open_count,
        "only_noop_remaining": only_noop_remaining,
        "noop_available": noop_available,
        "available_before_memory_for_pair": available_before,
        "available_after_memory_for_pair": available_after,
    }


def _trace_duration(duration_steps: int) -> list[dict[str, Any]]:
    wrapper = _make_wrapper(
        memory_enabled=True,
        memory_duration_steps=duration_steps,
        num_envs=1,
        num_agents=2,
        num_viewpoints=4,
    )
    _activate_memory(wrapper, duration_steps=duration_steps)
    rows: list[dict[str, Any]] = []
    for offset in range(1, duration_steps + 3):
        rows.append(_decision_trace_row(wrapper, logical_step=TRIGGER_STEP + offset))

    active_offsets = [row["offset_from_trigger"] for row in rows if row["selected_pair_active"]]
    suppressed_offsets = [row["offset_from_trigger"] for row in rows if row["suppressed_count"] > 0]
    expected = list(range(1, duration_steps + 1))
    _assert(active_offsets == expected, f"active offsets for D={duration_steps} were {active_offsets}, expected {expected}")
    _assert(
        suppressed_offsets == expected,
        f"suppressed offsets for D={duration_steps} were {suppressed_offsets}, expected {expected}",
    )
    return rows


def _covers_offset(rows: list[dict[str, Any]], offset: int) -> bool:
    for row in rows:
        if row["offset_from_trigger"] == offset:
            return bool(row["selected_pair_active"]) and int(row["suppressed_count"]) > 0
    return False


def _check_unavailable_pair_suppression() -> dict[str, Any]:
    wrapper = _make_wrapper(memory_enabled=True, memory_duration_steps=5, num_envs=1, num_agents=2, num_viewpoints=4)
    _activate_memory(wrapper, duration_steps=5)
    problem = _problem_with_pair_available(wrapper, available=False)
    mask = wrapper._build_available_actions(problem=problem)
    suppressed_count = int(wrapper._last_failed_pair_memory_suppressed_count[0, ROBOT_ID].item())
    _assert(not bool(mask[0, ROBOT_ID, TARGET_ID].item()), "unavailable memorized pair became available")
    _assert(suppressed_count == 0, "unavailable memorized pair should not count as suppressed")
    return {
        "available_before_memory_for_pair": False,
        "available_after_memory_for_pair": bool(mask[0, ROBOT_ID, TARGET_ID].item()),
        "suppressed_count": suppressed_count,
    }


def _check_fail_open_and_noop() -> dict[str, Any]:
    wrapper = _make_wrapper(memory_enabled=True, memory_duration_steps=5, num_envs=1, num_agents=2, num_viewpoints=4)
    _activate_memory(wrapper, duration_steps=5)
    problem = _problem_with_pair_available(wrapper, available=True)
    problem["available_mask"][0, ROBOT_ID, :] = False
    problem["available_mask"][0, ROBOT_ID, TARGET_ID] = True
    mask = wrapper._build_available_actions(problem=problem)
    fail_open_count = int(wrapper._last_failed_pair_memory_fail_open_count[0, ROBOT_ID].item())
    suppressed_count = int(wrapper._last_failed_pair_memory_suppressed_count[0, ROBOT_ID].item())
    _assert(bool(mask[0, ROBOT_ID, TARGET_ID].item()), "fail-open did not preserve the only target option")
    _assert(bool(mask[0, ROBOT_ID, -1].item()), "noop was not preserved under fail-open")
    _assert(fail_open_count == 1, "fail-open diagnostic was not recorded")
    _assert(suppressed_count == 0, "fail-open should not count as actual suppression")
    return {
        "target_available_after_fail_open": bool(mask[0, ROBOT_ID, TARGET_ID].item()),
        "noop_available": bool(mask[0, ROBOT_ID, -1].item()),
        "fail_open_count": fail_open_count,
        "suppressed_count": suppressed_count,
    }


def _check_coverage_clear() -> dict[str, Any]:
    wrapper = _make_wrapper(memory_enabled=True, memory_duration_steps=5, num_envs=1, num_agents=2, num_viewpoints=4)
    _activate_memory(wrapper, duration_steps=5)
    pre_problem = _problem_with_pair_available(wrapper, available=True)
    post_problem = _problem_with_pair_available(wrapper, available=True)
    post_problem["viewpoints_covered"] = post_problem["viewpoints_covered"].clone()
    post_problem["viewpoints_covered"][0, TARGET_ID] = True
    assignment = _assignment_noop(wrapper)
    selected_available = torch.ones(wrapper.num_envs, wrapper.num_agents, dtype=torch.bool)
    wrapper._update_assignment_diagnostics(
        assignment=assignment,
        pre_step_problem=pre_problem,
        post_step_problem=post_problem,
        selected_available_mask=selected_available,
    )
    remaining = int(wrapper._assignment_failed_pair_memory_remaining[0, ROBOT_ID, TARGET_ID].item())
    _assert(remaining == 0, "coverage did not clear failed-pair memory")
    return {"remaining_after_coverage_clear": remaining}


def _check_reset_clear() -> dict[str, Any]:
    wrapper = _make_wrapper(memory_enabled=True, memory_duration_steps=5, num_envs=1, num_agents=2, num_viewpoints=4)
    _activate_memory(wrapper, duration_steps=5)
    problem = _problem_with_pair_available(wrapper, available=True)
    wrapper._reset_assignment_diagnostics(problem=problem)
    remaining = int(wrapper._assignment_failed_pair_memory_remaining.sum().item())
    trigger_steps = int((wrapper._assignment_failed_pair_memory_trigger_step >= 0).sum().item())
    _assert(remaining == 0, "reset did not clear failed-pair memory")
    _assert(trigger_steps == 0, "reset did not clear failed-pair trigger steps")
    return {"remaining_after_reset": remaining, "nonnegative_trigger_steps_after_reset": trigger_steps}


def run_ttl_boundary_smoke() -> dict[str, Any]:
    traces = {str(duration): _trace_duration(duration) for duration in TRACE_DURATIONS}
    coverage_summary = {
        str(duration): {
            "active_offsets": [
                row["offset_from_trigger"]
                for row in traces[str(duration)]
                if row["selected_pair_active"] and row["suppressed_count"] > 0
            ],
            "covers_T_plus_4": _covers_offset(traces[str(duration)], 4),
            "covers_T_plus_5": _covers_offset(traces[str(duration)], 5),
            "covers_T_plus_6": _covers_offset(traces[str(duration)], 6),
        }
        for duration in TRACE_DURATIONS
    }

    _assert(coverage_summary["5"]["covers_T_plus_4"], "D=5 did not cover T+4")
    _assert(coverage_summary["5"]["covers_T_plus_5"], "D=5 did not cover T+5")
    _assert(not coverage_summary["5"]["covers_T_plus_6"], "D=5 unexpectedly covered T+6")
    _assert(coverage_summary["6"]["covers_T_plus_5"], "D=6 did not cover T+5")
    _assert(coverage_summary["6"]["covers_T_plus_6"], "D=6 did not cover T+6")
    _assert(coverage_summary["7"]["covers_T_plus_6"], "D=7 did not cover T+6")
    _assert(coverage_summary["10"]["covers_T_plus_6"], "D=10 did not cover T+6")

    return {
        "status": "passed",
        "trigger_step": TRIGGER_STEP,
        "robot_id": ROBOT_ID,
        "target_id": TARGET_ID,
        "semantics": "active for subsequent decision/build_available_actions offsets 1..D, inactive at offset D+1",
        "coverage_summary": coverage_summary,
        "trace": traces,
        "unavailable_pair": _check_unavailable_pair_suppression(),
        "fail_open": _check_fail_open_and_noop(),
        "coverage_clear": _check_coverage_clear(),
        "reset_clear": _check_reset_clear(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result_file", type=Path, default=None, help="Optional JSON trace output path.")
    args = parser.parse_args()
    result = run_ttl_boundary_smoke()
    if args.result_file is not None:
        args.result_file.parent.mkdir(parents=True, exist_ok=True)
        args.result_file.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    compact = {
        "status": result["status"],
        "semantics": result["semantics"],
        "coverage_summary": result["coverage_summary"],
    }
    print(f"[OK]: assignment failed-pair memory TTL boundary smoke passed: {json.dumps(compact, sort_keys=True)}")


if __name__ == "__main__":
    main()
