"""Budget-aware diagnostics for repeated assignment targets.

This script reads playback ``assignment_history.csv`` files and classifies
contiguous same robot-target segments using a simple execution-budget proxy:

    expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)

The analysis is diagnostic-only. It does not import Isaac Sim, modify
environment behavior, or change cooldown/reward logic.
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


DEFAULT_MAX_BASE_XY_STEP_BY_ROBOT = {
    "robot_0": 0.08,
    "robot_1": 0.10,
    "robot_2": 0.06,
}


def _parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except Exception:
        return default


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _max(values: list[float]) -> float:
    return max(values) if values else 0.0


def _parse_id_list(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    ids: list[int] = []
    for item in parsed:
        try:
            ids.append(int(item))
        except Exception:
            continue
    return ids


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _resolve_history_arg(arg: str) -> tuple[str, Path]:
    if "=" not in arg:
        raise ValueError(f"history argument must be LABEL=PATH, got {arg!r}")
    label, raw_path = arg.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"history label must be non-empty for {arg!r}")
    path = Path(raw_path)
    if path.is_dir():
        path = path / "assignment_history.csv"
    if not path.exists():
        raise FileNotFoundError(f"assignment history not found: {path}")
    return label, path


def _expected_steps(cost: float, robot_name: str, max_step_by_robot: dict[str, float]) -> int:
    max_step = float(max_step_by_robot.get(robot_name, 0.08))
    if max_step <= 0.0:
        max_step = 0.08
    if cost <= 0.0:
        return 1
    return max(1, int(math.ceil(cost / max_step)))


def _segment_key(row: dict[str, str]) -> tuple[int, int, int]:
    return (
        _parse_int(row.get("episode")),
        _parse_int(row.get("env_id")),
        _parse_int(row.get("robot_id")),
    )


def _new_segment(label: str, row: dict[str, str]) -> dict[str, Any]:
    target_id = _parse_int(row.get("selected_viewpoint_id"), default=-1)
    return {
        "source_label": label,
        "episode": _parse_int(row.get("episode")),
        "env_id": _parse_int(row.get("env_id")),
        "robot_id": _parse_int(row.get("robot_id")),
        "robot_name": row.get("robot_name") or f"robot_{_parse_int(row.get('robot_id'))}",
        "target_id": target_id,
        "start_step": _parse_int(row.get("step")),
        "end_step": _parse_int(row.get("step")),
        "rows": [row],
    }


def _finalize_segment(
    segment: dict[str, Any],
    *,
    max_step_by_robot: dict[str, float],
    budget_multiplier: float,
    fixed_slack_steps: int,
    trigger_thresholds: list[int],
) -> dict[str, Any]:
    rows = segment["rows"]
    target_id = int(segment["target_id"])
    costs = [_parse_float(row.get("selected_path_cost")) for row in rows]
    finite_costs = [cost for cost in costs if math.isfinite(cost)]
    cost_first = finite_costs[0] if finite_costs else 0.0
    cost_mean = _mean(finite_costs)
    expected_first = _expected_steps(cost_first, str(segment["robot_name"]), max_step_by_robot)
    expected_mean = _expected_steps(cost_mean, str(segment["robot_name"]), max_step_by_robot)
    budget_steps = int(math.ceil(expected_first * budget_multiplier + fixed_slack_steps))
    budget_steps = max(1, budget_steps)
    length = len(rows)
    selected_completion_steps: list[int] = []
    any_coverage_gain_steps: list[int] = []
    for row in rows:
        step = _parse_int(row.get("step"))
        newly_covered = _parse_id_list(row.get("newly_covered_viewpoint_ids"))
        if target_id in newly_covered:
            selected_completion_steps.append(step)
        if _parse_bool(row.get("new_coverage_gain_after_step")) or newly_covered:
            any_coverage_gain_steps.append(step)

    selected_completed = bool(selected_completion_steps)
    any_coverage_gain = bool(any_coverage_gain_steps)
    first_completion_offset = (
        selected_completion_steps[0] - int(segment["start_step"]) + 1 if selected_completion_steps else 0
    )
    over_budget = length > budget_steps
    completed_within_budget = selected_completed and first_completion_offset <= budget_steps
    completed_after_budget = selected_completed and first_completion_offset > budget_steps
    over_budget_no_completion = over_budget and not selected_completed
    within_budget_persistence = length >= 2 and length <= budget_steps

    threshold_fields: dict[str, Any] = {}
    for threshold in trigger_thresholds:
        prefix = f"threshold_{threshold}"
        would_trigger = length >= threshold
        trigger_within_budget = would_trigger and threshold <= budget_steps
        trigger_after_budget = would_trigger and threshold > budget_steps
        threshold_fields[f"{prefix}_would_trigger"] = bool(would_trigger)
        threshold_fields[f"{prefix}_trigger_within_budget"] = bool(trigger_within_budget)
        threshold_fields[f"{prefix}_trigger_after_budget"] = bool(trigger_after_budget)

    cooldown_trigger_count = sum(1 for row in rows if _parse_bool(row.get("cooldown_triggered_after_step")))
    cooldown_active_count = sum(1 for row in rows if _parse_bool(row.get("cooldown_active_for_selected_pair")))
    suppressed_values = [
        _parse_float(row.get("cooldown_suppressed_available_count_for_robot"))
        for row in rows
        if row.get("cooldown_suppressed_available_count_for_robot") not in (None, "")
    ]
    same_target_streak_max = _max([_parse_float(row.get("same_target_streak")) for row in rows])
    available_counts = [
        _parse_float(row.get("available_viewpoint_count")) for row in rows if row.get("available_viewpoint_count") not in (None, "")
    ]

    result = {
        "source_label": segment["source_label"],
        "episode": segment["episode"],
        "env_id": segment["env_id"],
        "robot_id": segment["robot_id"],
        "robot_name": segment["robot_name"],
        "target_id": target_id,
        "start_step": segment["start_step"],
        "end_step": segment["end_step"],
        "segment_length": length,
        "selected_path_cost_first": cost_first,
        "selected_path_cost_mean": cost_mean,
        "expected_steps_first": expected_first,
        "expected_steps_mean": expected_mean,
        "budget_multiplier": budget_multiplier,
        "fixed_slack_steps": fixed_slack_steps,
        "budget_steps": budget_steps,
        "budget_ratio": float(length / budget_steps) if budget_steps else 0.0,
        "selected_target_completed": selected_completed,
        "any_coverage_gain": any_coverage_gain,
        "first_selected_completion_offset": first_completion_offset,
        "over_budget": over_budget,
        "over_budget_no_completion": over_budget_no_completion,
        "within_budget_persistence": within_budget_persistence,
        "completed_within_budget": completed_within_budget,
        "completed_after_budget": completed_after_budget,
        "selected_available_all": all(_parse_bool(row.get("selected_available")) for row in rows),
        "selected_feasible_all": all(_parse_bool(row.get("selected_feasible")) for row in rows),
        "selected_covered_before_any": any(_parse_bool(row.get("selected_covered_before")) for row in rows),
        "same_target_streak_max": same_target_streak_max,
        "cooldown_trigger_count": cooldown_trigger_count,
        "cooldown_active_for_selected_pair_count": cooldown_active_count,
        "suppressed_available_count_mean": _mean(suppressed_values),
        "available_viewpoint_count_mean": _mean(available_counts),
        "start_coverage_ratio": _parse_float(rows[0].get("coverage_ratio_after_step")),
        "end_coverage_ratio": _parse_float(rows[-1].get("coverage_ratio_after_step")),
    }
    result.update(threshold_fields)
    return result


def analyze_history(
    label: str,
    path: Path,
    *,
    max_step_by_robot: dict[str, float],
    budget_multiplier: float,
    fixed_slack_steps: int,
    trigger_thresholds: list[int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _read_csv(path)
    rows.sort(key=lambda row: (_segment_key(row), _parse_int(row.get("step"))))
    segments: list[dict[str, Any]] = []
    active_by_key: dict[tuple[int, int, int], dict[str, Any]] = {}

    def close(key: tuple[int, int, int]) -> None:
        segment = active_by_key.pop(key, None)
        if segment is not None:
            segments.append(
                _finalize_segment(
                    segment,
                    max_step_by_robot=max_step_by_robot,
                    budget_multiplier=budget_multiplier,
                    fixed_slack_steps=fixed_slack_steps,
                    trigger_thresholds=trigger_thresholds,
                )
            )

    for row in rows:
        key = _segment_key(row)
        is_noop = _parse_bool(row.get("is_noop")) or _parse_int(row.get("selected_viewpoint_id"), -1) < 0
        if is_noop:
            close(key)
            continue
        target_id = _parse_int(row.get("selected_viewpoint_id"), -1)
        current = active_by_key.get(key)
        if current is None or int(current["target_id"]) != target_id:
            close(key)
            active_by_key[key] = _new_segment(label, row)
        else:
            current["rows"].append(row)
            current["end_step"] = _parse_int(row.get("step"))
    for key in list(active_by_key):
        close(key)

    total_segments = len(segments)
    long_segments = [seg for seg in segments if int(seg["segment_length"]) >= 10]
    over_budget_no_completion = [seg for seg in segments if seg["over_budget_no_completion"]]
    completed_within_budget = [seg for seg in segments if seg["completed_within_budget"]]
    completed_after_budget = [seg for seg in segments if seg["completed_after_budget"]]
    within_budget_persistence = [seg for seg in segments if seg["within_budget_persistence"]]
    threshold_summary: dict[str, Any] = {}
    for threshold in trigger_thresholds:
        trigger_key = f"threshold_{threshold}_would_trigger"
        within_key = f"threshold_{threshold}_trigger_within_budget"
        after_key = f"threshold_{threshold}_trigger_after_budget"
        triggered = [seg for seg in segments if seg[trigger_key]]
        within = [seg for seg in segments if seg[within_key]]
        after = [seg for seg in segments if seg[after_key]]
        threshold_summary[f"threshold_{threshold}_triggered_segments"] = len(triggered)
        threshold_summary[f"threshold_{threshold}_triggered_within_budget"] = len(within)
        threshold_summary[f"threshold_{threshold}_triggered_after_budget"] = len(after)
        threshold_summary[f"threshold_{threshold}_within_budget_fraction"] = (
            float(len(within) / len(triggered)) if triggered else 0.0
        )

    top_over_budget = sorted(
        over_budget_no_completion,
        key=lambda seg: (float(seg["budget_ratio"]), int(seg["segment_length"])),
        reverse=True,
    )[:10]
    pair_counter = Counter(
        f"{seg['robot_name']}->{seg['target_id']}" for seg in over_budget_no_completion
    )
    summary = {
        "source_label": label,
        "assignment_history_csv": str(path),
        "history_rows": len(rows),
        "total_segments": total_segments,
        "long_segments_ge_10": len(long_segments),
        "within_budget_persistence_segments": len(within_budget_persistence),
        "completed_within_budget_segments": len(completed_within_budget),
        "completed_after_budget_segments": len(completed_after_budget),
        "over_budget_no_completion_segments": len(over_budget_no_completion),
        "over_budget_no_completion_fraction": (
            float(len(over_budget_no_completion) / total_segments) if total_segments else 0.0
        ),
        "max_segment_length": max((int(seg["segment_length"]) for seg in segments), default=0),
        "max_budget_ratio": max((float(seg["budget_ratio"]) for seg in segments), default=0.0),
        "mean_budget_ratio": _mean([float(seg["budget_ratio"]) for seg in segments]),
        "mean_expected_steps_first": _mean([float(seg["expected_steps_first"]) for seg in segments]),
        "mean_segment_length": _mean([float(seg["segment_length"]) for seg in segments]),
        "top_over_budget_pairs": [{"pair": pair, "count": count} for pair, count in pair_counter.most_common(10)],
        "top_over_budget_segments": [
            {
                "robot_name": seg["robot_name"],
                "target_id": seg["target_id"],
                "episode": seg["episode"],
                "start_step": seg["start_step"],
                "end_step": seg["end_step"],
                "segment_length": seg["segment_length"],
                "budget_steps": seg["budget_steps"],
                "budget_ratio": seg["budget_ratio"],
                "selected_path_cost_first": seg["selected_path_cost_first"],
            }
            for seg in top_over_budget
        ],
    }
    summary.update(threshold_summary)
    return segments, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        action="append",
        required=True,
        help="History input as LABEL=PATH. PATH may be assignment_history.csv or a playback output directory.",
    )
    parser.add_argument("--output_dir", type=Path, required=True, help="Directory for summary and segment CSV outputs.")
    parser.add_argument("--budget_multiplier", type=float, default=1.5, help="Multiplier applied to expected steps.")
    parser.add_argument("--fixed_slack_steps", type=int, default=5, help="Fixed slack added after the multiplier.")
    parser.add_argument(
        "--trigger_thresholds",
        type=int,
        nargs="+",
        default=[10, 30, 50],
        help="Streak thresholds to test for within-budget trigger diagnostics.",
    )
    args = parser.parse_args()

    max_step_by_robot = dict(DEFAULT_MAX_BASE_XY_STEP_BY_ROBOT)
    all_segments: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for history_arg in args.history:
        label, path = _resolve_history_arg(history_arg)
        segments, summary = analyze_history(
            label,
            path,
            max_step_by_robot=max_step_by_robot,
            budget_multiplier=float(args.budget_multiplier),
            fixed_slack_steps=int(args.fixed_slack_steps),
            trigger_thresholds=list(args.trigger_thresholds),
        )
        all_segments.extend(segments)
        summaries.append(summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    segment_fields = [
        "source_label",
        "episode",
        "env_id",
        "robot_id",
        "robot_name",
        "target_id",
        "start_step",
        "end_step",
        "segment_length",
        "selected_path_cost_first",
        "selected_path_cost_mean",
        "expected_steps_first",
        "expected_steps_mean",
        "budget_multiplier",
        "fixed_slack_steps",
        "budget_steps",
        "budget_ratio",
        "selected_target_completed",
        "any_coverage_gain",
        "first_selected_completion_offset",
        "over_budget",
        "over_budget_no_completion",
        "within_budget_persistence",
        "completed_within_budget",
        "completed_after_budget",
        "selected_available_all",
        "selected_feasible_all",
        "selected_covered_before_any",
        "same_target_streak_max",
        "cooldown_trigger_count",
        "cooldown_active_for_selected_pair_count",
        "suppressed_available_count_mean",
        "available_viewpoint_count_mean",
        "start_coverage_ratio",
        "end_coverage_ratio",
    ]
    for threshold in args.trigger_thresholds:
        segment_fields.extend(
            [
                f"threshold_{threshold}_would_trigger",
                f"threshold_{threshold}_trigger_within_budget",
                f"threshold_{threshold}_trigger_after_budget",
            ]
        )
    summary_fields = [
        "source_label",
        "assignment_history_csv",
        "history_rows",
        "total_segments",
        "long_segments_ge_10",
        "within_budget_persistence_segments",
        "completed_within_budget_segments",
        "completed_after_budget_segments",
        "over_budget_no_completion_segments",
        "over_budget_no_completion_fraction",
        "max_segment_length",
        "max_budget_ratio",
        "mean_budget_ratio",
        "mean_expected_steps_first",
        "mean_segment_length",
    ]
    for threshold in args.trigger_thresholds:
        summary_fields.extend(
            [
                f"threshold_{threshold}_triggered_segments",
                f"threshold_{threshold}_triggered_within_budget",
                f"threshold_{threshold}_triggered_after_budget",
                f"threshold_{threshold}_within_budget_fraction",
            ]
        )
    json_ready = {
        "budget_model": {
            "description": "expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot); budget_steps = ceil(expected_steps * budget_multiplier + fixed_slack_steps)",
            "max_base_xy_step_by_robot": max_step_by_robot,
            "budget_multiplier": args.budget_multiplier,
            "fixed_slack_steps": args.fixed_slack_steps,
            "trigger_thresholds": args.trigger_thresholds,
            "limitations": [
                "selected_path_cost is scanner-to-viewpoint distance, not measured execution distance",
                "actual_base_motion_distance in playback history is an obstacle footprint distance diagnostic, not traveled distance",
                "segments are contiguous same robot-target selections",
            ],
        },
        "summaries": summaries,
    }
    _write_csv(args.output_dir / "budget_aware_segment_summary.csv", all_segments, segment_fields)
    _write_csv(args.output_dir / "budget_aware_source_summary.csv", summaries, summary_fields)
    (args.output_dir / "budget_aware_summary.json").write_text(json.dumps(json_ready, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(args.output_dir), "sources": len(summaries), "segments": len(all_segments)}, indent=2))


if __name__ == "__main__":
    main()
