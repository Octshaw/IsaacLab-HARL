"""Pure integration smoke for passive lifecycle diagnostics wiring.

This test exercises the shared diagnostics adapter with fake assignment
problems and standardized proposals. It does not import runtime scripts,
launch Isaac Sim, run playback/evaluation, train, or invoke controller/env
functions.
"""

from __future__ import annotations

import argparse
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

from assignment_lifecycle_diagnostics import (  # noqa: E402
    ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION,
    AssignmentLifecycleDiagnosticsAdapter,
    EVENT_SCHEMA_FIELDS,
    build_assignment_lifecycle_external_diagnostics,
    make_assignment_lifecycle_post_problem,
    normalize_assignment_lifecycle_proposal,
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
        task_ids = torch.arange(num_tasks, dtype=torch.float32).view(1, 1, num_tasks)
        robot_offsets = torch.arange(num_robots, dtype=torch.float32).view(1, num_robots, 1) * 0.25
        env_offsets = torch.arange(num_envs, dtype=torch.float32).view(num_envs, 1, 1) * 0.05
        cost_matrix = task_ids + robot_offsets + env_offsets
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


def _clone_tensors(problem: dict[str, Any]) -> dict[str, torch.Tensor]:
    return {key: value.clone() for key, value in problem.items() if isinstance(value, torch.Tensor)}


def _assert_problem_unchanged(before: dict[str, torch.Tensor], after: dict[str, Any]) -> None:
    for key, value in before.items():
        _assert(torch.equal(value, after[key]), f"problem tensor {key!r} was mutated")


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _run_adapter_sequence(
    *,
    output_dir: Path,
    method_name: str,
    proposal_type: str,
    num_envs: int = 1,
    num_robots: int = 1,
    num_tasks: int = 3,
    done_env_ids: torch.Tensor | None = None,
) -> tuple[AssignmentLifecycleDiagnosticsAdapter, list[dict[str, Any]], dict[str, Any]]:
    adapter = AssignmentLifecycleDiagnosticsAdapter(
        enabled=True,
        num_envs=num_envs,
        num_robots=num_robots,
        num_tasks=num_tasks,
        device="cpu",
        method_name=method_name,
        output_dir=output_dir,
        proposal_type=proposal_type,
    )
    problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks)
    values = torch.full((num_envs, num_robots), -1, dtype=torch.long)
    values[:, 0] = min(1, num_tasks - 1)
    episode_ids = torch.arange(num_envs, dtype=torch.long)
    adapter.observe_pre_step(problem=problem, assignment_proposal=values, episode_ids=episode_ids)
    covered = torch.zeros(num_envs, num_tasks, dtype=torch.bool)
    covered[:, min(1, num_tasks - 1)] = True
    post_problem = _problem(num_envs=num_envs, num_robots=num_robots, num_tasks=num_tasks, covered=covered)
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=values,
        post_step_problem=post_problem,
        done_env_ids=done_env_ids,
        episode_ids=episode_ids,
    )
    summary = adapter.finalize()
    events = _read_events(output_dir / "assignment_lifecycle_events.jsonl")
    return adapter, events, summary


def _case_disabled_identity(root: Path) -> dict[str, Any]:
    output_dir = root / "disabled"
    problem = _problem(num_envs=1, num_robots=1, num_tasks=3)
    before = _clone_tensors(problem)
    proposal = _proposal([[1]])
    proposal_before = proposal.clone()
    adapter = AssignmentLifecycleDiagnosticsAdapter(
        enabled=False,
        num_envs=1,
        num_robots=1,
        num_tasks=3,
        output_dir=output_dir,
        method_name="happo",
    )
    adapter.observe_pre_step(problem=problem, assignment_proposal=proposal)
    adapter.observe_post_step(pre_step_problem=problem, assignment_proposal=proposal, post_step_problem=problem)
    summary = adapter.finalize()
    _assert(adapter.logger is None, "disabled adapter constructed a logger")
    _assert(not output_dir.exists(), "disabled adapter created output directory")
    _assert_problem_unchanged(before, problem)
    _assert(torch.equal(proposal, proposal_before), "disabled adapter mutated proposal")
    _assert(summary["enabled"] is False, "disabled summary did not report disabled")
    return {"case": "disabled_identity", "passed": True}


def _case_pre_post_order_and_done_reset(root: Path) -> dict[str, Any]:
    output_dir = root / "order"
    _, events, summary = _run_adapter_sequence(
        output_dir=output_dir,
        method_name="happo",
        proposal_type="decoded_rl_assignment",
        done_env_ids=torch.tensor([0], dtype=torch.long),
    )
    event_types = [event["event_type"] for event in events]
    _assert(event_types.index("target_completed_proxy") < event_types.index("reset_proxy"), "reset preceded completion")
    _assert(summary["target_completed_proxy_count"] == 1, "completion count mismatch")
    _assert(summary["reset_proxy_count"] == 1, "reset count mismatch")
    _assert(summary["behavior_changed"] is False, "summary behavior_changed must be false")
    for event in events:
        _assert(event["behavior_changed"] is False, "event behavior_changed must be false")
    return {"case": "pre_post_order_done_reset", "events": event_types}


def _case_subset_reset(root: Path) -> dict[str, Any]:
    output_dir = root / "subset_reset"
    adapter = AssignmentLifecycleDiagnosticsAdapter(
        enabled=True,
        num_envs=3,
        num_robots=1,
        num_tasks=5,
        output_dir=output_dir,
        method_name="nearest",
        proposal_type="standardized_assignment",
    )
    problem = _problem(num_envs=3, num_robots=1, num_tasks=5)
    proposal = _proposal([[1], [2], [3]])
    episode_ids = torch.tensor([0, 10, 20], dtype=torch.long)
    adapter.observe_pre_step(problem=problem, assignment_proposal=proposal, episode_ids=episode_ids)
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        post_step_problem=problem,
        done_env_ids=torch.tensor([0, 2], dtype=torch.long),
        episode_ids=episode_ids,
    )
    snapshot = adapter.logger.snapshot()
    _assert(int(snapshot["active_target_proxy"][0, 0].item()) == -1, "env 0 was not reset")
    _assert(int(snapshot["active_target_proxy"][2, 0].item()) == -1, "env 2 was not reset")
    _assert(int(snapshot["active_target_proxy"][1, 0].item()) == 2, "env 1 active proxy was incorrectly reset")
    summary = adapter.finalize()
    _assert(summary["reset_proxy_count"] == 2, "subset reset event count mismatch")
    return {"case": "subset_reset", "passed": True}


def _case_rl_proposal_normalization() -> dict[str, Any]:
    decoded = _proposal([[0, -1]])
    normalized = normalize_assignment_lifecycle_proposal(decoded, num_envs=1, num_robots=2, num_tasks=3)
    _assert(torch.equal(decoded, normalized), "decoded RL assignment changed during normalization")
    try:
        normalize_assignment_lifecycle_proposal(_proposal([[0, 3]]), num_envs=1, num_robots=2, num_tasks=3)
    except ValueError:
        pass
    else:
        raise AssertionError("raw discrete noop id N was not rejected")
    return {"case": "rl_proposal_normalization", "passed": True}


def _case_method_schema_equivalence(root: Path) -> dict[str, Any]:
    methods = ["happo", "random", "nearest", "greedy", "future_sota_placeholder", "new_sota_method_v1"]
    reference_keys: set[str] | None = None
    reference_summary_keys: set[str] | None = None
    reference_counts: dict[str, Any] | None = None
    for method_name in methods:
        _, events, summary = _run_adapter_sequence(
            output_dir=root / f"schema_{method_name}",
            method_name=method_name,
            proposal_type="standardized_assignment",
        )
        _assert(events, f"no events for method {method_name}")
        event_keys = set(events[0].keys())
        summary_keys = set(summary.keys())
        _assert(set(EVENT_SCHEMA_FIELDS).issubset(event_keys), f"event schema missing keys for {method_name}")
        counts = {
            key: value
            for key, value in summary.items()
            if key.endswith("_count") or key in {"total_events", "total_steps_observed"}
        }
        if reference_keys is None:
            reference_keys = event_keys
            reference_summary_keys = summary_keys
            reference_counts = counts
        else:
            _assert(event_keys == reference_keys, f"event keys changed for {method_name}")
            _assert(summary_keys == reference_summary_keys, f"summary keys changed for {method_name}")
            _assert(counts == reference_counts, f"transition counts changed for metadata-only method {method_name}")
        _assert(summary["schema_version"] == ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION, "schema mismatch")
    return {"case": "method_schema_equivalence", "methods": methods, "passed": True}


def _case_event_draining_finalize(root: Path) -> dict[str, Any]:
    output_dir = root / "draining"
    adapter, events, summary = _run_adapter_sequence(
        output_dir=output_dir,
        method_name="greedy",
        proposal_type="standardized_assignment",
    )
    _assert(adapter.logger.peek_events() == [], "adapter left undrained logger events")
    summary_again = adapter.finalize()
    _assert(summary_again["total_events"] == summary["total_events"], "finalize was not idempotent")
    _assert(events == _read_events(output_dir / "assignment_lifecycle_events.jsonl"), "event output changed after finalize")
    return {"case": "event_draining_finalize", "passed": True}


def _case_input_non_mutation(root: Path) -> dict[str, Any]:
    output_dir = root / "non_mutation"
    adapter = AssignmentLifecycleDiagnosticsAdapter(
        enabled=True,
        num_envs=1,
        num_robots=2,
        num_tasks=4,
        output_dir=output_dir,
        method_name="random",
    )
    problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    post_problem = _problem(num_envs=1, num_robots=2, num_tasks=4)
    before_pre = _clone_tensors(problem)
    before_post = _clone_tensors(post_problem)
    proposal = _proposal([[1, 2]])
    proposal_before = proposal.clone()
    external = build_assignment_lifecycle_external_diagnostics(
        assignment_proposal=proposal,
        info={"assignment_cooldown": {"budget_last_triggered_by_budget": torch.zeros(1, 2, dtype=torch.float32)}},
    )
    external_before = json.dumps({key: str(value) for key, value in external.items()}, sort_keys=True)
    done_env_ids = torch.tensor([], dtype=torch.long)
    done_before = done_env_ids.clone()
    metadata = {"method_name": "random", "proposal_confidence": 0.75}
    metadata_before = dict(metadata)
    adapter.observe_pre_step(problem=problem, assignment_proposal=proposal, method_metadata=metadata)
    adapter.observe_post_step(
        pre_step_problem=problem,
        assignment_proposal=proposal,
        post_step_problem=post_problem,
        external_diagnostics=external,
        done_env_ids=done_env_ids,
        method_metadata=metadata,
    )
    adapter.finalize()
    _assert_problem_unchanged(before_pre, problem)
    _assert_problem_unchanged(before_post, post_problem)
    _assert(torch.equal(proposal, proposal_before), "proposal mutated")
    _assert(torch.equal(done_env_ids, done_before), "done env ids mutated")
    _assert(metadata == metadata_before, "method metadata mutated")
    _assert(json.dumps({key: str(value) for key, value in external.items()}, sort_keys=True) == external_before, "external diagnostics mutated")
    return {"case": "input_non_mutation", "passed": True}


def _case_exact_conflict_passive(root: Path) -> dict[str, Any]:
    output_dir = root / "conflict"
    adapter = AssignmentLifecycleDiagnosticsAdapter(
        enabled=True,
        num_envs=1,
        num_robots=2,
        num_tasks=5,
        output_dir=output_dir,
        method_name="new_sota_method_v1",
        proposal_type="standardized_assignment",
    )
    cost = torch.full((1, 2, 5), 10.0)
    cost[0, 0, 4] = 3.0
    cost[0, 1, 4] = 2.0
    problem = _problem(num_envs=1, num_robots=2, num_tasks=5, cost_matrix=cost)
    proposal = _proposal([[4, 4]])
    proposal_before = proposal.clone()
    adapter.observe_pre_step(problem=problem, assignment_proposal=proposal)
    adapter.observe_post_step(pre_step_problem=problem, assignment_proposal=proposal, post_step_problem=problem)
    summary = adapter.finalize()
    events = _read_events(output_dir / "assignment_lifecycle_events.jsonl")
    conflicts = [event for event in events if event["event_type"] == "exact_claim_conflict_proxy"]
    _assert(len(conflicts) == 1, "conflict event missing")
    _assert(conflicts[0]["would_be_winner_robot_id"] == 1, "hypothetical winner mismatch")
    _assert(conflicts[0]["would_be_loser_robot_ids"] == [0], "hypothetical losers mismatch")
    _assert(conflicts[0]["behavior_changed"] is False, "conflict event changed behavior")
    _assert(torch.equal(proposal, proposal_before), "conflict diagnostics mutated proposal")
    _assert("effective_assignment" not in adapter.snapshot(), "adapter exposed effective assignment")
    _assert(summary["exact_claim_conflict_proxy_count"] == 1, "conflict summary count mismatch")
    return {"case": "exact_conflict_passive", "passed": True}


def _case_output_file_parsing(root: Path) -> dict[str, Any]:
    output_dir = root / "parse"
    _, events, summary = _run_adapter_sequence(
        output_dir=output_dir,
        method_name="nearest",
        proposal_type="standardized_assignment",
    )
    events_path = output_dir / "assignment_lifecycle_events.jsonl"
    summary_path = output_dir / "assignment_lifecycle_summary.json"
    _assert(events_path.exists(), "event file missing")
    _assert(summary_path.exists(), "summary file missing")
    parsed_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _assert(parsed_summary == summary, "summary parse mismatch")
    _assert(len(events) == summary["total_events"], "event count parse mismatch")
    return {"case": "output_file_parsing", "passed": True}


def _case_variable_mn(root: Path) -> dict[str, Any]:
    shapes = [(1, 1, 3), (2, 3, 5), (2, 4, 8)]
    for num_envs, num_robots, num_tasks in shapes:
        adapter, _, summary = _run_adapter_sequence(
            output_dir=root / f"shape_e{num_envs}_m{num_robots}_n{num_tasks}",
            method_name="future_sota_placeholder",
            proposal_type="standardized_assignment",
            num_envs=num_envs,
            num_robots=num_robots,
            num_tasks=num_tasks,
        )
        snapshot = adapter.logger.snapshot()
        _assert(tuple(snapshot["robot_state_proxy"].shape) == (num_envs, num_robots), "robot state shape mismatch")
        _assert(tuple(snapshot["task_state_proxy"].shape) == (num_envs, num_tasks), "task state shape mismatch")
        _assert(tuple(snapshot["pair_state_proxy"].shape) == (num_envs, num_robots, num_tasks), "pair state shape mismatch")
        _assert(summary["num_envs"] == num_envs, "summary env count mismatch")
        _assert(summary["num_robots"] == num_robots, "summary robot count mismatch")
        _assert(summary["num_tasks"] == num_tasks, "summary task count mismatch")
    return {"case": "variable_mn", "shapes": shapes, "passed": True}


def run_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="phase9g6c_lifecycle_") as temp_dir:
        root = Path(temp_dir)
        results = [
            _case_disabled_identity(root),
            _case_pre_post_order_and_done_reset(root),
            _case_subset_reset(root),
            _case_rl_proposal_normalization(),
            _case_method_schema_equivalence(root),
            _case_event_draining_finalize(root),
            _case_input_non_mutation(root),
            _case_exact_conflict_passive(root),
            _case_output_file_parsing(root),
            _case_variable_mn(root),
        ]
    return {
        "status": "passed",
        "case_count": len(results),
        "results": results,
        "default_disabled_identity": True,
        "rl_diagnostics_integration": True,
        "comparison_method_diagnostics_integration": True,
        "future_sota_compatibility": True,
        "pre_post_step_alignment": True,
        "subset_reset": True,
        "unified_event_summary_schema": True,
        "variable_mn": True,
        "input_non_mutation": True,
        "behavior_preservation": True,
        "no_effective_assignment_produced": True,
        "controller_or_env_invoked": False,
        "playback_evaluation_training_invoked": False,
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
    print(f"[OK]: assignment lifecycle runtime integration smoke passed: {json.dumps(result, sort_keys=True)}")


if __name__ == "__main__":
    main()
