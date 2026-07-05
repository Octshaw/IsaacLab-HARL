"""Phase 9F-2C row-level trigger-window validation.

This script is CSV-only. It validates the Phase 9F-2A playback history fields
and attributes post-budget-trigger conflicts using direct row-level diagnostics
when they are present.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_HISTORY = Path(
    "results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation"
)

REQUIRED_NEW_COLUMNS = [
    "robot_base_post_x",
    "robot_base_post_y",
    "selected_target_conflict_pair_count",
    "selected_target_conflict_pairs",
    "selected_target_min_distance_to_other_selected",
    "selected_target_conflict_threshold",
    "same_step_claimed_target_count",
    "same_step_claimed_target_robot_ids",
    "same_step_nearby_claimed_target_count",
    "same_step_nearby_claimed_target_robot_ids",
    "inter_robot_overlap_pair_count",
    "inter_robot_overlap_pairs",
    "inter_robot_min_base_distance",
    "inter_robot_overlap_threshold",
    "inter_robot_path_crossing_pair_count",
    "inter_robot_path_crossing_pairs",
    "inter_robot_path_near_miss_pair_count",
    "inter_robot_path_near_miss_pairs",
    "inter_robot_path_near_miss_threshold",
]

CORE_COLUMNS = [
    "episode",
    "env_id",
    "step",
    "robot_id",
    "selected_viewpoint_id",
    "is_noop",
    "robot_base_x",
    "robot_base_y",
    "target_x",
    "target_y",
    "new_coverage_gain_after_step",
    "coverage_ratio_after_step",
    "newly_covered_viewpoint_ids",
    "budget_triggered_by_budget",
]

COUNT_FIELDS = [
    "selected_target_conflict_pair_count",
    "same_step_claimed_target_count",
    "same_step_nearby_claimed_target_count",
    "inter_robot_overlap_pair_count",
    "inter_robot_path_crossing_pair_count",
    "inter_robot_path_near_miss_pair_count",
]

THRESHOLD_FIELDS = [
    "selected_target_conflict_threshold",
    "inter_robot_overlap_threshold",
    "inter_robot_path_near_miss_threshold",
]

JSON_LIST_FIELDS = [
    "selected_target_conflict_pairs",
    "same_step_claimed_target_robot_ids",
    "same_step_nearby_claimed_target_robot_ids",
    "inter_robot_overlap_pairs",
    "inter_robot_path_crossing_pairs",
    "inter_robot_path_near_miss_pairs",
    "newly_covered_viewpoint_ids",
]

STEP_LEVEL_REPEATED_FIELDS = [
    "selected_target_conflict_pair_count",
    "selected_target_conflict_pairs",
    "selected_target_conflict_threshold",
    "inter_robot_overlap_pair_count",
    "inter_robot_overlap_pairs",
    "inter_robot_overlap_threshold",
    "inter_robot_path_crossing_pair_count",
    "inter_robot_path_crossing_pairs",
    "inter_robot_path_near_miss_pair_count",
    "inter_robot_path_near_miss_pairs",
    "inter_robot_path_near_miss_threshold",
]

ATTRIBUTION_FIELDS = [
    "episode",
    "env_id",
    "trigger_step",
    "trigger_robot_id",
    "trigger_target_id",
    "trigger_pair",
    "trigger_same_step_claimed_target_count",
    "trigger_same_step_claimed_target_robot_ids",
    "trigger_same_step_nearby_claimed_target_count",
    "trigger_same_step_nearby_claimed_target_robot_ids",
    "trigger_selected_target_min_distance",
    "trigger_inter_robot_overlap_pair_count",
    "trigger_inter_robot_min_base_distance",
    "trigger_inter_robot_path_crossing_pair_count",
    "trigger_inter_robot_path_near_miss_pair_count",
    "next_non_noop_step",
    "next_non_noop_target_id",
    "next_direct_exact_duplicate_count",
    "next_direct_claimed_robot_ids",
    "next_reconstructed_exact_duplicate_count",
    "next_reconstructed_claimed_robot_ids",
    "next_exact_direct_reconstructed_agree",
    "next_direct_nearby_count",
    "next_direct_nearby_robot_ids",
    "next_reconstructed_nearby_count",
    "next_reconstructed_nearby_robot_ids",
    "next_nearby_direct_reconstructed_agree",
    "next_selected_target_min_distance",
    "next_reconstructed_nearest_other_target_distance",
    "next_step_direct_selected_target_conflict_pair_count",
    "next_step_reconstructed_selected_target_conflict_pair_count",
    "next_pair_count_direct_reconstructed_agree",
    "next_step_inter_robot_overlap_pair_count",
    "next_step_inter_robot_min_base_distance",
    "next_step_inter_robot_path_crossing_pair_count",
    "next_step_inter_robot_path_near_miss_pair_count",
    "direct_exact_duplicate_step_count_20",
    "direct_nearby_selected_target_step_count_20",
    "direct_inter_robot_overlap_step_count_20",
    "direct_path_crossing_step_count_20",
    "direct_path_near_miss_step_count_20",
    "coverage_gain_within_20_steps",
    "coverage_delta_within_available_window",
    "returns_to_triggered_pair_after_cooldown",
    "return_step_after_cooldown",
]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = math.nan) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_float(value: float, digits: int = 6) -> str:
    if not math.isfinite(value):
        return ""
    return f"{value:.{digits}f}"


def _target_id(row: dict[str, Any]) -> int:
    if _bool(row.get("is_noop")):
        return -1
    return _int(row.get("selected_viewpoint_id"), -1)


def _row_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("step")))


def _robot_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("robot_id")))


def _json_list(value: Any) -> list[Any]:
    text = str(value or "").strip()
    if not text:
        return []
    parsed = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError(f"expected JSON list, got {type(parsed).__name__}")
    return parsed


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


def _target_xy(row: dict[str, Any]) -> tuple[float, float] | None:
    x = _float(row.get("target_x"))
    y = _float(row.get("target_y"))
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return x, y


def _target_distance(row_a: dict[str, Any], row_b: dict[str, Any]) -> float:
    pos_a = _target_xy(row_a)
    pos_b = _target_xy(row_b)
    if pos_a is None or pos_b is None:
        return math.nan
    return math.hypot(pos_a[0] - pos_b[0], pos_a[1] - pos_b[1])


def _reconstructed_step_target_metrics(
    step_rows: list[dict[str, Any]],
    *,
    threshold: float,
) -> dict[str, Any]:
    selected = [row for row in step_rows if _target_id(row) >= 0]
    target_counts = Counter(_target_id(row) for row in selected)
    exact_duplicate_pair_count = sum(count * (count - 1) // 2 for count in target_counts.values())
    conflict_pair_count = 0
    nearby_distinct_pair_count = 0
    min_distance = math.nan
    for index, row_a in enumerate(selected):
        for row_b in selected[index + 1 :]:
            distance = _target_distance(row_a, row_b)
            if not math.isfinite(distance):
                continue
            min_distance = distance if not math.isfinite(min_distance) else min(min_distance, distance)
            if distance < threshold:
                conflict_pair_count += 1
                if _target_id(row_a) != _target_id(row_b):
                    nearby_distinct_pair_count += 1
    return {
        "exact_duplicate_pair_count": exact_duplicate_pair_count,
        "selected_target_conflict_pair_count": conflict_pair_count,
        "nearby_distinct_pair_count": nearby_distinct_pair_count,
        "min_target_distance": min_distance,
    }


def _first_non_noop_after(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    *,
    episode: int,
    env_id: int,
    robot_id: int,
    step: int,
) -> dict[str, Any] | None:
    for row in rows_by_robot[(episode, env_id, robot_id)]:
        if _int(row.get("step")) > step and _target_id(row) >= 0:
            return row
    return None


def _first_return_after(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    *,
    episode: int,
    env_id: int,
    robot_id: int,
    step: int,
    target_id: int,
    cooldown_duration: int,
) -> dict[str, Any] | None:
    for row in rows_by_robot[(episode, env_id, robot_id)]:
        if _int(row.get("step")) <= step + cooldown_duration:
            continue
        if _target_id(row) == target_id:
            return row
    return None


def _coverage_gain_between(
    step_rows: dict[int, list[dict[str, Any]]],
    *,
    start: int,
    end: int,
) -> bool:
    return any(
        any(_bool(row.get("new_coverage_gain_after_step")) for row in rows)
        for step, rows in step_rows.items()
        if start < step <= end
    )


def _coverage_delta_available(
    step_rows: dict[int, list[dict[str, Any]]],
    *,
    start_step: int,
    end_step: int,
    start_ratio: float,
) -> float:
    available_steps = [step for step in step_rows if start_step < step <= end_step]
    if not available_steps or not math.isfinite(start_ratio):
        return math.nan
    end_ratio = _float(step_rows[max(available_steps)][0].get("coverage_ratio_after_step"))
    if not math.isfinite(end_ratio):
        return math.nan
    return end_ratio - start_ratio


def _step_has_direct_exact(rows: list[dict[str, Any]]) -> bool:
    return any(_int(row.get("same_step_claimed_target_count")) > 0 for row in rows)


def _step_has_direct_nearby(rows: list[dict[str, Any]]) -> bool:
    return any(_int(row.get("same_step_nearby_claimed_target_count")) > 0 for row in rows)


def _step_level_count(rows: list[dict[str, Any]], field: str) -> int:
    return _int(rows[0].get(field)) if rows else 0


def _validate_history(rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    column_set = set(columns)
    required = CORE_COLUMNS + REQUIRED_NEW_COLUMNS
    missing_columns = [name for name in required if name not in column_set]

    numeric_errors: list[str] = []
    nonnegative_errors: list[str] = []
    positive_threshold_errors: list[str] = []
    json_errors: list[str] = []

    for row_index, row in enumerate(rows, start=2):
        for field in ["robot_base_post_x", "robot_base_post_y"]:
            value = _float(row.get(field))
            if not math.isfinite(value):
                numeric_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
        for field in COUNT_FIELDS:
            value = _float(row.get(field))
            if not math.isfinite(value):
                numeric_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
            elif value < 0:
                nonnegative_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
        for field in THRESHOLD_FIELDS:
            value = _float(row.get(field))
            if not math.isfinite(value):
                numeric_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
            elif value <= 0:
                positive_threshold_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
        for field in JSON_LIST_FIELDS:
            try:
                _json_list(row.get(field))
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                json_errors.append(f"line {row_index}: {field}: {exc}")

    rows_by_step: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_step[_row_key(row)].append(row)

    consistency_errors: list[str] = []
    for key, step_rows in sorted(rows_by_step.items()):
        for field in STEP_LEVEL_REPEATED_FIELDS:
            values = {row.get(field, "") for row in step_rows}
            if len(values) > 1:
                consistency_errors.append(f"{key}: {field} has {len(values)} values")

    budget_trigger_count = sum(1 for row in rows if _bool(row.get("budget_triggered_by_budget")))
    return {
        "history_exists": True,
        "row_count": len(rows),
        "column_count": len(columns),
        "required_new_columns_exist": not [name for name in REQUIRED_NEW_COLUMNS if name not in column_set],
        "missing_required_columns": missing_columns,
        "pre_step_base_columns_exist": {"robot_base_x", "robot_base_y"}.issubset(column_set),
        "budget_triggered_by_budget_exists": "budget_triggered_by_budget" in column_set,
        "budget_trigger_row_count": budget_trigger_count,
        "numeric_validation_passed": not numeric_errors,
        "numeric_errors_sample": numeric_errors[:10],
        "count_nonnegative_validation_passed": not nonnegative_errors,
        "count_nonnegative_errors_sample": nonnegative_errors[:10],
        "threshold_positive_validation_passed": not positive_threshold_errors,
        "threshold_positive_errors_sample": positive_threshold_errors[:10],
        "json_list_parse_validation_passed": not json_errors,
        "json_errors_sample": json_errors[:10],
        "step_level_repeated_consistency_passed": not consistency_errors,
        "step_level_repeated_consistency_errors_sample": consistency_errors[:10],
        "validation_passed": not (
            missing_columns
            or numeric_errors
            or nonnegative_errors
            or positive_threshold_errors
            or json_errors
            or consistency_errors
        ),
    }


def _analyze_trigger_windows(
    rows: list[dict[str, str]],
    *,
    window_steps: int,
    cooldown_duration: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows_by_step: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    step_rows_by_episode: dict[tuple[int, int], dict[int, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        rows_by_step[_row_key(row)].append(row)
        rows_by_robot[_robot_key(row)].append(row)
        episode, env_id, step = _row_key(row)
        step_rows_by_episode[(episode, env_id)][step].append(row)
    for key in rows_by_robot:
        rows_by_robot[key].sort(key=lambda item: _int(item.get("step")))

    trigger_rows = [row for row in rows if _bool(row.get("budget_triggered_by_budget"))]
    records: list[dict[str, Any]] = []

    for trigger in trigger_rows:
        episode, env_id, trigger_step = _row_key(trigger)
        robot_id = _int(trigger.get("robot_id"))
        trigger_target = _target_id(trigger)
        episode_steps = step_rows_by_episode[(episode, env_id)]
        max_step = max(episode_steps) if episode_steps else trigger_step
        window_end = min(max_step, trigger_step + window_steps)
        trigger_key = (episode, env_id, trigger_step)
        trigger_rows_for_step = rows_by_step[trigger_key]

        next_row = _first_non_noop_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=trigger_step,
        )
        next_step = _int(next_row.get("step"), -1) if next_row is not None else -1
        next_target = _target_id(next_row) if next_row is not None else -1
        next_rows = rows_by_step.get((episode, env_id, next_step), [])
        threshold = _float(
            (next_row or trigger).get("selected_target_conflict_threshold"),
            0.85,
        )

        other_next_rows = [
            row for row in next_rows if _int(row.get("robot_id"), -1) != robot_id and _target_id(row) >= 0
        ]
        reconstructed_claimed = [
            _int(row.get("robot_id")) for row in other_next_rows if _target_id(row) == next_target and next_target >= 0
        ]
        reconstructed_nearby: list[int] = []
        nearest_distance = math.nan
        if next_row is not None:
            for other in other_next_rows:
                distance = _target_distance(next_row, other)
                if not math.isfinite(distance):
                    continue
                nearest_distance = distance if not math.isfinite(nearest_distance) else min(nearest_distance, distance)
                if _target_id(other) != next_target and distance < threshold:
                    reconstructed_nearby.append(_int(other.get("robot_id")))

        reconstructed_step_metrics = _reconstructed_step_target_metrics(next_rows, threshold=threshold)
        direct_next_pair_count = _int((next_row or {}).get("selected_target_conflict_pair_count"), -1)
        reconstructed_pair_count = _int(reconstructed_step_metrics["selected_target_conflict_pair_count"], -1)
        direct_next_exact_count = _int((next_row or {}).get("same_step_claimed_target_count"), -1)
        direct_next_nearby_count = _int((next_row or {}).get("same_step_nearby_claimed_target_count"), -1)

        window_step_rows = [
            episode_steps[step] for step in range(trigger_step + 1, window_end + 1) if step in episode_steps
        ]
        return_row = _first_return_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=trigger_step,
            target_id=trigger_target,
            cooldown_duration=cooldown_duration,
        )
        coverage_at_trigger = _float(trigger.get("coverage_ratio_after_step"))

        records.append(
            {
                "episode": episode,
                "env_id": env_id,
                "trigger_step": trigger_step,
                "trigger_robot_id": robot_id,
                "trigger_target_id": trigger_target,
                "trigger_pair": f"r{robot_id}->{trigger_target}",
                "trigger_same_step_claimed_target_count": _int(trigger.get("same_step_claimed_target_count")),
                "trigger_same_step_claimed_target_robot_ids": trigger.get("same_step_claimed_target_robot_ids", "[]"),
                "trigger_same_step_nearby_claimed_target_count": _int(
                    trigger.get("same_step_nearby_claimed_target_count")
                ),
                "trigger_same_step_nearby_claimed_target_robot_ids": trigger.get(
                    "same_step_nearby_claimed_target_robot_ids", "[]"
                ),
                "trigger_selected_target_min_distance": _format_float(
                    _float(trigger.get("selected_target_min_distance_to_other_selected"))
                ),
                "trigger_inter_robot_overlap_pair_count": _int(trigger.get("inter_robot_overlap_pair_count")),
                "trigger_inter_robot_min_base_distance": _format_float(_float(trigger.get("inter_robot_min_base_distance"))),
                "trigger_inter_robot_path_crossing_pair_count": _int(trigger.get("inter_robot_path_crossing_pair_count")),
                "trigger_inter_robot_path_near_miss_pair_count": _int(
                    trigger.get("inter_robot_path_near_miss_pair_count")
                ),
                "next_non_noop_step": "" if next_row is None else next_step,
                "next_non_noop_target_id": "" if next_row is None else next_target,
                "next_direct_exact_duplicate_count": "" if next_row is None else direct_next_exact_count,
                "next_direct_claimed_robot_ids": "" if next_row is None else next_row.get("same_step_claimed_target_robot_ids", "[]"),
                "next_reconstructed_exact_duplicate_count": len(reconstructed_claimed),
                "next_reconstructed_claimed_robot_ids": json.dumps(reconstructed_claimed),
                "next_exact_direct_reconstructed_agree": (
                    "" if next_row is None else (direct_next_exact_count == len(reconstructed_claimed))
                ),
                "next_direct_nearby_count": "" if next_row is None else direct_next_nearby_count,
                "next_direct_nearby_robot_ids": "" if next_row is None else next_row.get(
                    "same_step_nearby_claimed_target_robot_ids", "[]"
                ),
                "next_reconstructed_nearby_count": len(reconstructed_nearby),
                "next_reconstructed_nearby_robot_ids": json.dumps(reconstructed_nearby),
                "next_nearby_direct_reconstructed_agree": (
                    "" if next_row is None else (direct_next_nearby_count == len(reconstructed_nearby))
                ),
                "next_selected_target_min_distance": "" if next_row is None else _format_float(
                    _float(next_row.get("selected_target_min_distance_to_other_selected"))
                ),
                "next_reconstructed_nearest_other_target_distance": _format_float(nearest_distance),
                "next_step_direct_selected_target_conflict_pair_count": "" if next_row is None else direct_next_pair_count,
                "next_step_reconstructed_selected_target_conflict_pair_count": reconstructed_pair_count,
                "next_pair_count_direct_reconstructed_agree": (
                    "" if next_row is None else (direct_next_pair_count == reconstructed_pair_count)
                ),
                "next_step_inter_robot_overlap_pair_count": "" if next_row is None else _int(
                    next_row.get("inter_robot_overlap_pair_count")
                ),
                "next_step_inter_robot_min_base_distance": "" if next_row is None else _format_float(
                    _float(next_row.get("inter_robot_min_base_distance"))
                ),
                "next_step_inter_robot_path_crossing_pair_count": "" if next_row is None else _int(
                    next_row.get("inter_robot_path_crossing_pair_count")
                ),
                "next_step_inter_robot_path_near_miss_pair_count": "" if next_row is None else _int(
                    next_row.get("inter_robot_path_near_miss_pair_count")
                ),
                "direct_exact_duplicate_step_count_20": sum(_step_has_direct_exact(step_rows) for step_rows in window_step_rows),
                "direct_nearby_selected_target_step_count_20": sum(
                    _step_has_direct_nearby(step_rows) for step_rows in window_step_rows
                ),
                "direct_inter_robot_overlap_step_count_20": sum(
                    _step_level_count(step_rows, "inter_robot_overlap_pair_count") > 0 for step_rows in window_step_rows
                ),
                "direct_path_crossing_step_count_20": sum(
                    _step_level_count(step_rows, "inter_robot_path_crossing_pair_count") > 0 for step_rows in window_step_rows
                ),
                "direct_path_near_miss_step_count_20": sum(
                    _step_level_count(step_rows, "inter_robot_path_near_miss_pair_count") > 0
                    for step_rows in window_step_rows
                ),
                "coverage_gain_within_20_steps": _coverage_gain_between(
                    episode_steps, start=trigger_step, end=trigger_step + window_steps
                ),
                "coverage_delta_within_available_window": _format_float(
                    _coverage_delta_available(
                        episode_steps,
                        start_step=trigger_step,
                        end_step=trigger_step + window_steps,
                        start_ratio=coverage_at_trigger,
                    )
                ),
                "returns_to_triggered_pair_after_cooldown": return_row is not None,
                "return_step_after_cooldown": "" if return_row is None else _int(return_row.get("step")),
            }
        )

    summary = {
        "trigger_count": len(records),
        "window_steps": window_steps,
        "cooldown_duration": cooldown_duration,
        "trigger_pairs": dict(Counter(row["trigger_pair"] for row in records)),
        "next_exact_duplicate_direct_count": sum(
            1 for row in records if _int(row["next_direct_exact_duplicate_count"], -1) > 0
        ),
        "next_nearby_selected_target_direct_count": sum(
            1 for row in records if _int(row["next_direct_nearby_count"], -1) > 0
        ),
        "next_inter_robot_overlap_direct_count": sum(
            1 for row in records if _int(row["next_step_inter_robot_overlap_pair_count"], -1) > 0
        ),
        "next_path_crossing_direct_count": sum(
            1 for row in records if _int(row["next_step_inter_robot_path_crossing_pair_count"], -1) > 0
        ),
        "next_path_near_miss_direct_count": sum(
            1 for row in records if _int(row["next_step_inter_robot_path_near_miss_pair_count"], -1) > 0
        ),
        "coverage_gain_within_20_count": sum(_bool(row["coverage_gain_within_20_steps"]) for row in records),
        "return_to_triggered_pair_after_cooldown_count": sum(
            _bool(row["returns_to_triggered_pair_after_cooldown"]) for row in records
        ),
        "exact_direct_reconstructed_mismatch_count": sum(
            1 for row in records if row["next_exact_direct_reconstructed_agree"] is False
        ),
        "nearby_direct_reconstructed_mismatch_count": sum(
            1 for row in records if row["next_nearby_direct_reconstructed_agree"] is False
        ),
        "selected_target_pair_count_direct_reconstructed_mismatch_count": sum(
            1 for row in records if row["next_pair_count_direct_reconstructed_agree"] is False
        ),
        "direct_exact_duplicate_step_count_20_total": sum(_int(row["direct_exact_duplicate_step_count_20"]) for row in records),
        "direct_nearby_selected_target_step_count_20_total": sum(
            _int(row["direct_nearby_selected_target_step_count_20"]) for row in records
        ),
        "direct_inter_robot_overlap_step_count_20_total": sum(
            _int(row["direct_inter_robot_overlap_step_count_20"]) for row in records
        ),
        "direct_path_crossing_step_count_20_total": sum(_int(row["direct_path_crossing_step_count_20"]) for row in records),
        "direct_path_near_miss_step_count_20_total": sum(
            _int(row["direct_path_near_miss_step_count_20"]) for row in records
        ),
    }
    return records, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--window_steps", type=int, default=20)
    parser.add_argument("--cooldown_duration", type=int, default=5)
    args = parser.parse_args()

    if not args.history.exists():
        raise FileNotFoundError(args.history)
    rows = _read_csv(args.history)
    columns = list(rows[0].keys()) if rows else []
    schema_summary = _validate_history(rows, columns)
    attribution_rows, attribution_summary = _analyze_trigger_windows(
        rows,
        window_steps=args.window_steps,
        cooldown_duration=args.cooldown_duration,
    )
    output_dir = args.output_dir
    _write_json(output_dir / "phase9f2c_schema_validation_summary.json", schema_summary)
    _write_csv(output_dir / "phase9f2c_trigger_window_attribution.csv", attribution_rows, ATTRIBUTION_FIELDS)
    _write_json(
        output_dir / "phase9f2c_trigger_window_summary.json",
        {
            "history": str(args.history),
            "schema": schema_summary,
            "attribution": attribution_summary,
        },
    )
    print(
        json.dumps(
            {
                "history": str(args.history),
                "rows": schema_summary["row_count"],
                "columns": schema_summary["column_count"],
                "validation_passed": schema_summary["validation_passed"],
                "budget_trigger_row_count": schema_summary["budget_trigger_row_count"],
                "trigger_attribution_rows": len(attribution_rows),
                "outputs": {
                    "schema": str(output_dir / "phase9f2c_schema_validation_summary.json"),
                    "attribution_csv": str(output_dir / "phase9f2c_trigger_window_attribution.csv"),
                    "summary": str(output_dir / "phase9f2c_trigger_window_summary.json"),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
