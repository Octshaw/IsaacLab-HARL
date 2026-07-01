"""Trace-level inspection for Phase 9E-3E budget-aware cooldown events.

The script reads existing playback diagnostics CSV/JSON outputs only. It does
not import Isaac Sim, run training, or modify environment behavior.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RUNS = {
    "models": Path("results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback"),
    "best_model": Path("results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback"),
}

DEFAULT_STRICT_RUNS = {
    "models": Path("results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_models_playback"),
    "best_model": Path("results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_best_model_playback"),
}

KNOWN_STUCK_PAIRS = {
    "models": {(0, 44), (1, 44), (2, 15)},
    "best_model": {(0, 39), (1, 0), (2, 15)},
}


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = math.nan) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_ids(value: Any) -> set[int]:
    if value is None:
        return set()
    text = str(value).strip()
    if not text:
        return set()
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return set()
    if not isinstance(parsed, (list, tuple, set)):
        return set()
    return {_int(item, -1) for item in parsed if _int(item, -1) >= 0}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _load_summary(run_dir: Path) -> dict[str, str]:
    rows = _read_csv(run_dir / "summary.csv")
    return rows[0] if rows else {}


def _step_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row["episode"]), _int(row["env_id"]), _int(row["step"]))


def _robot_key(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return (_int(row["episode"]), _int(row["env_id"]), _int(row["robot_id"]), _int(row["step"]))


def _selected_target(row: dict[str, Any]) -> int:
    if _bool(row.get("is_noop")):
        return -1
    return _int(row.get("selected_viewpoint_id"), -1)


def _same_step_targets(step_rows: list[dict[str, Any]], exclude_robot: int | None = None) -> list[str]:
    parts = []
    for row in sorted(step_rows, key=lambda item: _int(item["robot_id"])):
        robot_id = _int(row["robot_id"])
        if exclude_robot is not None and robot_id == exclude_robot:
            continue
        target = _selected_target(row)
        parts.append(f"r{robot_id}->{target if target >= 0 else 'noop'}")
    return parts


def _compact_sequence(rows: list[dict[str, Any]], *, limit: int = 12) -> str:
    targets = [_selected_target(row) for row in rows]
    tokens: list[str] = []
    index = 0
    while index < len(targets):
        target = targets[index]
        count = 1
        index += 1
        while index < len(targets) and targets[index] == target:
            count += 1
            index += 1
        label = "noop" if target < 0 else str(target)
        tokens.append(f"{label}x{count}")
    if len(tokens) > limit:
        return ", ".join(tokens[:limit]) + f", ... (+{len(tokens) - limit} runs)"
    return ", ".join(tokens)


def _rows_for_robot(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    checkpoint: str,
    episode: int,
    env_id: int,
    robot_id: int,
) -> list[dict[str, Any]]:
    return rows_by_robot[(episode, env_id, robot_id)]


def _first_robot_row_after(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    *,
    episode: int,
    env_id: int,
    robot_id: int,
    step: int,
    non_noop: bool = False,
) -> dict[str, Any] | None:
    for row in _rows_for_robot(rows_by_robot, "", episode, env_id, robot_id):
        if _int(row["step"]) <= step:
            continue
        if non_noop and _selected_target(row) < 0:
            continue
        return row
    return None


def _target_later_covered(rows: list[dict[str, Any]], *, step: int, target_id: int) -> bool:
    for row in rows:
        if _int(row["step"]) <= step:
            continue
        if target_id in _parse_ids(row.get("newly_covered_viewpoint_ids")):
            return True
    return False


def _coverage_at_or_after(step_rows: dict[int, list[dict[str, Any]]], *, step: int) -> float:
    eligible_steps = [item for item in step_rows if item >= step]
    if not eligible_steps:
        return math.nan
    row = step_rows[min(eligible_steps)][0]
    return _float(row.get("coverage_ratio_after_step"))


def _last_gain_step(step_rows: dict[int, list[dict[str, Any]]]) -> int:
    gain_steps = [
        step
        for step, rows in step_rows.items()
        if any(_bool(row.get("new_coverage_gain_after_step")) for row in rows)
    ]
    return max(gain_steps) if gain_steps else -1


def _segment_end_reason(robot_rows: list[dict[str, Any]], *, trigger_index: int, target_id: int) -> str:
    for row in robot_rows[trigger_index + 1 :]:
        target = _selected_target(row)
        if target_id in _parse_ids(row.get("newly_covered_viewpoint_ids")):
            return "target_covered"
        if target < 0:
            return "noop"
        if target != target_id:
            return "switched_target"
    return "episode_end"


def _event_window_rows(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    *,
    episode: int,
    env_id: int,
    robot_id: int,
    step: int,
    before: int = 10,
    after: int = 20,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _rows_for_robot(rows_by_robot, "", episode, env_id, robot_id)
    before_rows = [row for row in rows if step - before <= _int(row["step"]) < step]
    after_rows = [row for row in rows if step < _int(row["step"]) <= step + after]
    return before_rows, after_rows


def _step_duplicate_count(step_rows: list[dict[str, Any]]) -> float:
    if not step_rows:
        return 0.0
    return max(_float(row.get("duplicate_selected_target_on_step"), 0.0) for row in step_rows)


def _step_crossing_rate(step_rows: list[dict[str, Any]]) -> float:
    if not step_rows:
        return math.nan
    return sum(1.0 for row in step_rows if _bool(row.get("actual_base_motion_intersects_component"))) / float(len(step_rows))


def _mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def _format_counter(counter: Counter[Any], *, limit: int = 10) -> str:
    return "; ".join(f"{key}:{count}" for key, count in counter.most_common(limit))


def analyze_run(checkpoint: str, run_dir: Path) -> dict[str, Any]:
    rows = _read_csv(run_dir / "assignment_history.csv")
    summary = _load_summary(run_dir)
    step_rows: dict[tuple[int, int], dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        row["_checkpoint"] = checkpoint
        episode = _int(row["episode"])
        env_id = _int(row["env_id"])
        step = _int(row["step"])
        robot_id = _int(row["robot_id"])
        step_rows[(episode, env_id)][step].append(row)
        rows_by_robot[(episode, env_id, robot_id)].append(row)
    for key in rows_by_robot:
        rows_by_robot[key].sort(key=lambda item: _int(item["step"]))

    known_pairs = KNOWN_STUCK_PAIRS[checkpoint]
    events = []
    windows = []
    redirects = []
    window_step_ids: set[tuple[int, int, int]] = set()

    trigger_rows = [row for row in rows if _bool(row.get("budget_triggered_by_budget"))]
    for row in trigger_rows:
        episode = _int(row["episode"])
        env_id = _int(row["env_id"])
        step = _int(row["step"])
        robot_id = _int(row["robot_id"])
        target_id = _selected_target(row)
        robot_rows = rows_by_robot[(episode, env_id, robot_id)]
        robot_index = next(index for index, item in enumerate(robot_rows) if _int(item["step"]) == step)
        same_step = step_rows[(episode, env_id)][step]
        episode_steps = step_rows[(episode, env_id)]
        later_rows = [item for item in rows if _int(item["episode"]) == episode and _int(item["env_id"]) == env_id]
        next_row = _first_robot_row_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=step,
            non_noop=False,
        )
        next_non_noop = _first_robot_row_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=step,
            non_noop=True,
        )
        next_target = _selected_target(next_non_noop) if next_non_noop is not None else -1
        next_step_rows = (
            step_rows[(episode, env_id)][_int(next_non_noop["step"])] if next_non_noop is not None else []
        )
        next_equals_other_current = bool(
            next_non_noop is not None
            and any(
                _int(other["robot_id"]) != robot_id and _selected_target(other) == next_target
                for other in next_step_rows
            )
        )
        same_step_same_target = any(
            _int(other["robot_id"]) != robot_id and _selected_target(other) == target_id for other in same_step
        )
        target_later_covered = _target_later_covered(later_rows, step=step, target_id=target_id)
        event = {
            "checkpoint": checkpoint,
            "episode": episode,
            "env_id": env_id,
            "step": step,
            "robot_id": robot_id,
            "robot_name": row.get("robot_name", f"robot_{robot_id}"),
            "target_id": target_id,
            "is_known_late_stuck_pair": (robot_id, target_id) in known_pairs,
            "attempt_steps_for_selected_pair": _int(row.get("budget_attempt_steps_for_selected_pair")),
            "budget_steps_for_selected_pair": _int(row.get("budget_steps_for_selected_pair")),
            "budget_ratio_for_selected_pair": _float(row.get("budget_ratio_for_selected_pair")),
            "selected_path_cost": _float(row.get("selected_path_cost")),
            "cooldown_remaining_after_trigger": 5,
            "cooldown_remaining_for_selected_pair_recorded": _int(row.get("cooldown_remaining_for_selected_pair")),
            "cooldown_suppressed_count_for_robot": _int(row.get("cooldown_suppressed_available_count_for_robot")),
            "available_real_target_count": _int(row.get("available_viewpoint_count")),
            "coverage_ratio_before": _float(row.get("covered_before_count"), 0.0) / 50.0,
            "coverage_ratio_after": _float(row.get("coverage_ratio_after_step")),
            "coverage_gain_this_step": _bool(row.get("new_coverage_gain_after_step")),
            "same_target_streak": _float(row.get("same_target_streak")),
            "selected_target_conflict_trace_available": False,
            "selected_target_conflict_value": "",
            "exact_duplicate_selected_target_count": _float(row.get("duplicate_selected_target_on_step")),
            "another_robot_selected_same_target_same_step": same_step_same_target,
            "inter_robot_overlap_trace_available": False,
            "inter_robot_overlap_value": "",
            "base_motion_crossing": _bool(row.get("actual_base_motion_intersects_component")),
            "actual_base_motion_distance": _float(row.get("actual_base_motion_distance")),
            "other_robots_selected_targets_same_step": "; ".join(_same_step_targets(same_step, exclude_robot=robot_id)),
            "target_later_covered_after_trigger": target_later_covered,
            "next_selected_target_for_same_robot": next_target,
            "next_selected_step_for_same_robot": _int(next_non_noop["step"]) if next_non_noop is not None else "",
            "next_target_equals_other_robot_current_target": next_equals_other_current,
            "segment_end_reason": _segment_end_reason(robot_rows, trigger_index=robot_index, target_id=target_id),
        }
        events.append(event)

        before_rows, after_rows = _event_window_rows(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=step,
        )
        for window_step in range(step + 1, min(step + 20, max(episode_steps.keys())) + 1):
            window_step_ids.add((episode, env_id, window_step))
        coverage_at_5 = _coverage_at_or_after(episode_steps, step=step + 5)
        coverage_at_10 = _coverage_at_or_after(episode_steps, step=step + 10)
        coverage_at_20 = _coverage_at_or_after(episode_steps, step=step + 20)
        coverage_gain_20 = any(
            any(_bool(item.get("new_coverage_gain_after_step")) for item in episode_steps[window_step])
            for window_step in episode_steps
            if step < window_step <= step + 20
        )
        duplicate_values_20 = [
            _step_duplicate_count(episode_steps[window_step])
            for window_step in episode_steps
            if step < window_step <= step + 20
        ]
        crossing_values_20 = [
            _step_crossing_rate(episode_steps[window_step])
            for window_step in episode_steps
            if step < window_step <= step + 20
        ]
        returns_after_cooldown = any(
            _selected_target(item) == target_id and _int(item["step"]) > step + 5
            for item in robot_rows
        )
        switch_to_noop = any(_selected_target(item) < 0 for item in after_rows)
        switch_to_other_current = bool(
            next_non_noop is not None
            and any(
                _int(other["robot_id"]) != robot_id and _selected_target(other) == next_target
                for other in next_step_rows
            )
        )
        max_post_streak = max((_float(item.get("same_target_streak"), 0.0) for item in after_rows), default=0.0)
        windows.append(
            {
                "checkpoint": checkpoint,
                "episode": episode,
                "env_id": env_id,
                "step": step,
                "robot_id": robot_id,
                "target_id": target_id,
                "selected_sequence_10_steps_before": _compact_sequence(before_rows),
                "selected_sequence_20_steps_after": _compact_sequence(after_rows),
                "returns_to_same_target_after_cooldown_expires": returns_after_cooldown,
                "coverage_increases_within_20_steps_after_trigger": coverage_gain_20,
                "coverage_ratio_at_trigger": _float(row.get("coverage_ratio_after_step")),
                "coverage_ratio_5_steps_after": coverage_at_5,
                "coverage_ratio_10_steps_after": coverage_at_10,
                "coverage_ratio_20_steps_after": coverage_at_20,
                "duplicate_selected_target_mean_20_steps_after": _mean(duplicate_values_20),
                "crossing_rate_20_steps_after": _mean(crossing_values_20),
                "inter_robot_overlap_trace_available": False,
                "switches_to_noop_within_20_steps": switch_to_noop,
                "next_non_noop_target": next_target,
                "next_non_noop_target_already_selected_by_other_robot": switch_to_other_current,
                "next_non_noop_target_selected_covered_before": (
                    _bool(next_non_noop.get("selected_covered_before")) if next_non_noop is not None else ""
                ),
                "available_real_targets_at_trigger": _int(row.get("available_viewpoint_count")),
                "available_real_targets_next_selection": (
                    _int(next_non_noop.get("available_viewpoint_count")) if next_non_noop is not None else ""
                ),
                "max_same_target_streak_within_20_steps_after": max_post_streak,
            }
        )

        next_target_covered_20 = bool(
            next_target >= 0
            and any(
                next_target in _parse_ids(item.get("newly_covered_viewpoint_ids"))
                for item in later_rows
                if step < _int(item["step"]) <= step + 20
            )
        )
        returns_trigger_target_later = any(
            _selected_target(item) == target_id and _int(item["step"]) > step for item in robot_rows
        )
        long_streak_after_redirect = max_post_streak >= 30.0
        redirects.append(
            {
                "checkpoint": checkpoint,
                "episode": episode,
                "env_id": env_id,
                "trigger_step": step,
                "robot_id": robot_id,
                "trigger_target": target_id,
                "next_non_noop_step": _int(next_non_noop["step"]) if next_non_noop is not None else "",
                "next_non_noop_target": next_target,
                "next_target_equals_other_robot_current_target": next_equals_other_current,
                "next_target_selected_by_multiple_robots_within_20_steps": any(value > 0 for value in duplicate_values_20),
                "next_target_leads_to_coverage_within_20_steps": next_target_covered_20,
                "returns_to_triggered_target_later": returns_trigger_target_later,
                "falls_into_another_long_same_target_streak_within_20_steps": long_streak_after_redirect,
            }
        )

    conflict_rows = []
    for (episode, env_id), episode_steps in step_rows.items():
        all_steps = sorted(episode_steps)
        last_gain = _last_gain_step(episode_steps)
        within_steps = {step for ep, env, step in window_step_ids if ep == episode and env == env_id}
        outside_steps = set(all_steps) - within_steps
        def step_values(steps: set[int], fn) -> list[float]:
            return [fn(episode_steps[step]) for step in sorted(steps) if step in episode_steps]
        within_duplicate = step_values(within_steps, _step_duplicate_count)
        outside_duplicate = step_values(outside_steps, _step_duplicate_count)
        within_crossing = step_values(within_steps, _step_crossing_rate)
        outside_crossing = step_values(outside_steps, _step_crossing_rate)
        conflict_rows.append(
            {
                "checkpoint": checkpoint,
                "episode": episode,
                "env_id": env_id,
                "selected_target_conflict_rate_overall_summary": _float(
                    summary.get("selected_target_conflict_rate_mean")
                ),
                "selected_target_conflict_rate_within_20_steps_after_triggers": "",
                "selected_target_conflict_rate_outside_trigger_windows": "",
                "selected_target_conflict_trace_available": False,
                "duplicate_selected_target_rate_overall_summary": _float(
                    summary.get("duplicate_selected_target_rate_mean")
                ),
                "duplicate_selected_target_rate_within_20_steps_after_triggers": _mean(within_duplicate),
                "duplicate_selected_target_rate_outside_trigger_windows": _mean(outside_duplicate),
                "inter_robot_overlap_rate_overall_summary": _float(summary.get("inter_robot_overlap_rate_mean")),
                "inter_robot_overlap_rate_within_20_steps_after_triggers": "",
                "inter_robot_overlap_rate_outside_trigger_windows": "",
                "inter_robot_overlap_trace_available": False,
                "crossing_rate_overall_summary": _float(summary.get("actual_base_motion_intersection_rate_mean")),
                "crossing_rate_within_20_steps_after_triggers": _mean(within_crossing),
                "crossing_rate_outside_trigger_windows": _mean(outside_crossing),
                "last_coverage_gain_step": last_gain,
                "trigger_count": len([event for event in events if event["episode"] == episode and event["env_id"] == env_id]),
                "trigger_steps_before_last_gain": sum(
                    1
                    for event in events
                    if event["episode"] == episode and event["env_id"] == env_id and event["step"] <= last_gain
                ),
                "trigger_steps_after_last_gain": sum(
                    1
                    for event in events
                    if event["episode"] == episode and event["env_id"] == env_id and event["step"] > last_gain
                ),
                "triggers_followed_by_coverage_gain_within_20": sum(
                    1
                    for window in windows
                    if window["episode"] == episode
                    and window["coverage_increases_within_20_steps_after_trigger"]
                ),
            }
        )

    unique_pairs = sorted({(event["robot_id"], event["target_id"]) for event in events})
    known_trigger_count = sum(1 for event in events if event["is_known_late_stuck_pair"])
    non_known_pairs = sorted(
        {
            (event["robot_id"], event["target_id"])
            for event in events
            if not event["is_known_late_stuck_pair"]
        }
    )
    non_known_later_covered = sum(
        1
        for event in events
        if (not event["is_known_late_stuck_pair"]) and event["target_later_covered_after_trigger"]
    )
    return {
        "checkpoint": checkpoint,
        "run_dir": str(run_dir),
        "summary": summary,
        "events": events,
        "windows": windows,
        "redirects": redirects,
        "conflict_rows": conflict_rows,
        "summary_record": {
            "checkpoint": checkpoint,
            "total_budget_triggers": len(events),
            "triggers_on_known_stuck_pairs": known_trigger_count,
            "triggers_on_non_known_pairs": len(events) - known_trigger_count,
            "unique_triggered_pairs": [f"r{robot}->{target}" for robot, target in unique_pairs],
            "unique_non_known_triggered_pairs": [f"r{robot}->{target}" for robot, target in non_known_pairs],
            "fraction_triggers_on_known_stuck_pairs": known_trigger_count / float(max(1, len(events))),
            "non_known_triggers_later_covered_count": non_known_later_covered,
            "triggers_followed_by_coverage_gain_within_20": sum(
                1 for window in windows if window["coverage_increases_within_20_steps_after_trigger"]
            ),
            "triggers_before_or_at_last_gain": sum(row["trigger_steps_before_last_gain"] for row in conflict_rows),
            "triggers_after_last_gain": sum(row["trigger_steps_after_last_gain"] for row in conflict_rows),
            "redirect_next_target_distribution": _format_counter(
                Counter(item["next_non_noop_target"] for item in redirects)
            ),
            "redirect_next_target_equals_other_robot_current_count": sum(
                1 for item in redirects if item["next_target_equals_other_robot_current_target"]
            ),
            "returns_to_triggered_target_later_count": sum(
                1 for item in redirects if item["returns_to_triggered_target_later"]
            ),
            "another_long_streak_after_redirect_count": sum(
                1 for item in redirects if item["falls_into_another_long_same_target_streak_within_20_steps"]
            ),
        },
    }


def _strict_comparison(strict_dirs: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    summary_path = Path("results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.csv")
    if summary_path.exists():
        rows = _read_csv(summary_path)
        for row in rows:
            records.append(
                {
                    "variant": row.get("variant"),
                    "checkpoint": row.get("checkpoint"),
                    "final_coverage": _float(row.get("final_coverage")),
                    "coverage_auc": _float(row.get("coverage_auc")),
                    "max_same_target_streak": _float(row.get("max_same_target_streak")),
                    "cooldown_suppressed_count": _float(row.get("cooldown_suppressed_count")),
                    "budget_trigger_count": _float(row.get("budget_trigger_count")),
                    "budget_over_budget_selected_count": _float(row.get("budget_over_budget_selected_count")),
                }
            )
        return records
    for checkpoint, run_dir in strict_dirs.items():
        if not run_dir.exists():
            continue
        summary = _load_summary(run_dir)
        records.append(
            {
                "variant": "strict_budget",
                "checkpoint": checkpoint,
                "final_coverage": _float(summary.get("final_coverage_mean")),
                "coverage_auc": _float(summary.get("coverage_auc_mean")),
                "max_same_target_streak": "",
                "cooldown_suppressed_count": _float(summary.get("cooldown_suppressed_count_mean")),
                "budget_trigger_count": _float(summary.get("budget_trigger_count_mean")),
                "budget_over_budget_selected_count": _float(summary.get("budget_over_budget_selected_count_mean")),
            }
        )
    return records


def _make_notes(
    output_dir: Path,
    *,
    run_results: list[dict[str, Any]],
    strict_comparison: list[dict[str, Any]],
    classification: str,
    notes_filename: str = "phase9e3e_trace_notes.md",
) -> None:
    lines = [
        "# Phase 9E-3E Trace Notes",
        "",
        "No training was run. This inspection used existing playback CSV/JSON outputs only.",
        "",
        "Row-level selected-target conflict and inter-robot overlap are not present in assignment_history.csv. "
        "The trace analysis therefore uses exact duplicate selected targets and base-motion crossing as local proxies, "
        "while preserving overall selected-target conflict and overlap from summary.csv.",
        "",
        "## Trigger Summary",
        "",
        "| Checkpoint | Triggers | Known-Pair Triggers | Non-Known Triggers | Unique Pairs | Coverage Gain Within 20 |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for result in run_results:
        record = result["summary_record"]
        lines.append(
            "| {checkpoint} | {total_budget_triggers} | {triggers_on_known_stuck_pairs} | "
            "{triggers_on_non_known_pairs} | {pairs} | {triggers_followed_by_coverage_gain_within_20} |".format(
                checkpoint=record["checkpoint"],
                total_budget_triggers=record["total_budget_triggers"],
                triggers_on_known_stuck_pairs=record["triggers_on_known_stuck_pairs"],
                triggers_on_non_known_pairs=record["triggers_on_non_known_pairs"],
                pairs=", ".join(record["unique_triggered_pairs"]),
                triggers_followed_by_coverage_gain_within_20=record[
                    "triggers_followed_by_coverage_gain_within_20"
                ],
            )
        )
    lines.extend(["", "## Redirect Summary", ""])
    for result in run_results:
        record = result["summary_record"]
        lines.extend(
            [
                f"- {record['checkpoint']}: next target distribution {record['redirect_next_target_distribution']}",
                (
                    f"- {record['checkpoint']}: next target equals another robot current target "
                    f"{record['redirect_next_target_equals_other_robot_current_count']}/"
                    f"{record['total_budget_triggers']}"
                ),
                (
                    f"- {record['checkpoint']}: returned to triggered target later "
                    f"{record['returns_to_triggered_target_later_count']}/{record['total_budget_triggers']}"
                ),
                (
                    f"- {record['checkpoint']}: another long post-trigger streak "
                    f"{record['another_long_streak_after_redirect_count']}/{record['total_budget_triggers']}"
                ),
            ]
        )
    lines.extend(["", "## m15 vs Strict Budget", ""])
    for row in strict_comparison:
        lines.append(
            "- {variant} {checkpoint}: coverage={coverage:.4f}, auc={auc:.4f}, max_streak={streak}, "
            "suppressed={suppressed:.4f}, budget_triggers={triggers:.0f}".format(
                variant=row["variant"],
                checkpoint=row["checkpoint"],
                coverage=row["final_coverage"],
                auc=row["coverage_auc"],
                streak=row["max_same_target_streak"],
                suppressed=row["cooldown_suppressed_count"],
                triggers=row["budget_trigger_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Classification",
            "",
            classification,
            "",
            "The m15_slack5_d5 trace is plausible enough for a scoped debug training run, but the non-known triggers, "
            "post-trigger returns, and mixed spatial proxies justify caution.",
        ]
    )
    (output_dir / notes_filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection"),
    )
    parser.add_argument("--models_dir", type=Path, default=DEFAULT_RUNS["models"])
    parser.add_argument("--best_model_dir", type=Path, default=DEFAULT_RUNS["best_model"])
    parser.add_argument("--strict_models_dir", type=Path, default=DEFAULT_STRICT_RUNS["models"])
    parser.add_argument("--strict_best_model_dir", type=Path, default=DEFAULT_STRICT_RUNS["best_model"])
    parser.add_argument("--summary_filename", default="phase9e3e_budget_trigger_trace_summary.json")
    parser.add_argument("--notes_filename", default="phase9e3e_trace_notes.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dirs = {"models": args.models_dir, "best_model": args.best_model_dir}
    strict_dirs = {"models": args.strict_models_dir, "best_model": args.strict_best_model_dir}

    missing = [str(path) for path in run_dirs.values() if not (path / "assignment_history.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing assignment_history.csv in: {missing}")

    run_results = [analyze_run(checkpoint, run_dir) for checkpoint, run_dir in run_dirs.items()]
    event_rows = [event for result in run_results for event in result["events"]]
    window_rows = [window for result in run_results for window in result["windows"]]
    redirect_rows = [redirect for result in run_results for redirect in result["redirects"]]
    conflict_rows = [row for result in run_results for row in result["conflict_rows"]]
    strict_comparison = _strict_comparison(strict_dirs)

    _write_csv(
        output_dir / "budget_trigger_events.csv",
        event_rows,
        [
            "checkpoint",
            "episode",
            "env_id",
            "step",
            "robot_id",
            "robot_name",
            "target_id",
            "is_known_late_stuck_pair",
            "attempt_steps_for_selected_pair",
            "budget_steps_for_selected_pair",
            "budget_ratio_for_selected_pair",
            "selected_path_cost",
            "cooldown_remaining_after_trigger",
            "cooldown_remaining_for_selected_pair_recorded",
            "cooldown_suppressed_count_for_robot",
            "available_real_target_count",
            "coverage_ratio_before",
            "coverage_ratio_after",
            "coverage_gain_this_step",
            "same_target_streak",
            "selected_target_conflict_trace_available",
            "selected_target_conflict_value",
            "exact_duplicate_selected_target_count",
            "another_robot_selected_same_target_same_step",
            "inter_robot_overlap_trace_available",
            "inter_robot_overlap_value",
            "base_motion_crossing",
            "actual_base_motion_distance",
            "other_robots_selected_targets_same_step",
            "target_later_covered_after_trigger",
            "next_selected_target_for_same_robot",
            "next_selected_step_for_same_robot",
            "next_target_equals_other_robot_current_target",
            "segment_end_reason",
        ],
    )
    _write_csv(
        output_dir / "budget_trigger_windows.csv",
        window_rows,
        [
            "checkpoint",
            "episode",
            "env_id",
            "step",
            "robot_id",
            "target_id",
            "selected_sequence_10_steps_before",
            "selected_sequence_20_steps_after",
            "returns_to_same_target_after_cooldown_expires",
            "coverage_increases_within_20_steps_after_trigger",
            "coverage_ratio_at_trigger",
            "coverage_ratio_5_steps_after",
            "coverage_ratio_10_steps_after",
            "coverage_ratio_20_steps_after",
            "duplicate_selected_target_mean_20_steps_after",
            "crossing_rate_20_steps_after",
            "inter_robot_overlap_trace_available",
            "switches_to_noop_within_20_steps",
            "next_non_noop_target",
            "next_non_noop_target_already_selected_by_other_robot",
            "next_non_noop_target_selected_covered_before",
            "available_real_targets_at_trigger",
            "available_real_targets_next_selection",
            "max_same_target_streak_within_20_steps_after",
        ],
    )
    _write_csv(
        output_dir / "post_trigger_redirect_summary.csv",
        redirect_rows,
        [
            "checkpoint",
            "episode",
            "env_id",
            "trigger_step",
            "robot_id",
            "trigger_target",
            "next_non_noop_step",
            "next_non_noop_target",
            "next_target_equals_other_robot_current_target",
            "next_target_selected_by_multiple_robots_within_20_steps",
            "next_target_leads_to_coverage_within_20_steps",
            "returns_to_triggered_target_later",
            "falls_into_another_long_same_target_streak_within_20_steps",
        ],
    )
    _write_csv(
        output_dir / "conflict_after_trigger_summary.csv",
        conflict_rows,
        [
            "checkpoint",
            "episode",
            "env_id",
            "selected_target_conflict_rate_overall_summary",
            "selected_target_conflict_rate_within_20_steps_after_triggers",
            "selected_target_conflict_rate_outside_trigger_windows",
            "selected_target_conflict_trace_available",
            "duplicate_selected_target_rate_overall_summary",
            "duplicate_selected_target_rate_within_20_steps_after_triggers",
            "duplicate_selected_target_rate_outside_trigger_windows",
            "inter_robot_overlap_rate_overall_summary",
            "inter_robot_overlap_rate_within_20_steps_after_triggers",
            "inter_robot_overlap_rate_outside_trigger_windows",
            "inter_robot_overlap_trace_available",
            "crossing_rate_overall_summary",
            "crossing_rate_within_20_steps_after_triggers",
            "crossing_rate_outside_trigger_windows",
            "last_coverage_gain_step",
            "trigger_count",
            "trigger_steps_before_last_gain",
            "trigger_steps_after_last_gain",
            "triggers_followed_by_coverage_gain_within_20",
        ],
    )

    classification = "TRACE-PARTIAL"
    summary = {
        "classification": classification,
        "inputs": {checkpoint: str(path) for checkpoint, path in run_dirs.items()},
        "strict_comparison": strict_comparison,
        "run_summaries": [result["summary_record"] for result in run_results],
        "field_limitations": {
            "selected_target_conflict_trace": "unavailable in assignment_history.csv; overall summary.csv only",
            "inter_robot_overlap_trace": "unavailable in assignment_history.csv; overall summary.csv only",
            "duplicate_selected_target": "available and used as local exact-target conflict proxy",
            "base_motion_crossing": "available per robot row",
        },
        "outputs": {
            "budget_trigger_events_csv": str(output_dir / "budget_trigger_events.csv"),
            "budget_trigger_windows_csv": str(output_dir / "budget_trigger_windows.csv"),
            "post_trigger_redirect_summary_csv": str(output_dir / "post_trigger_redirect_summary.csv"),
            "conflict_after_trigger_summary_csv": str(output_dir / "conflict_after_trigger_summary.csv"),
            "notes_md": str(output_dir / args.notes_filename),
        },
    }
    _write_json(output_dir / args.summary_filename, summary)
    _make_notes(
        output_dir,
        run_results=run_results,
        strict_comparison=strict_comparison,
        classification=classification,
        notes_filename=args.notes_filename,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
