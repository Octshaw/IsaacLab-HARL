"""Phase 9F-1 post-budget-redirect conflict diagnostics.

This script reads existing playback diagnostics only. It does not import Isaac
Sim, run training, run playback, or modify environment behavior.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RUNS = {
    "phase9e4b_models_budget": Path(
        "results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback"
    ),
    "phase9e4b_best_model_budget": Path(
        "results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback"
    ),
}

DEFAULT_COMPARISON_RUNS = {
    "phase9e3d_models_budget": Path(
        "results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback"
    ),
    "phase9e3d_best_model_budget": Path(
        "results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback"
    ),
}

DEFAULT_SCENARIO = Path(
    "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/"
    "algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml"
)

DEFAULT_OUTPUT_DIR = Path(
    "results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics"
)

SCHEMA_REQUIREMENTS = [
    {
        "question": "selected target per robot per step",
        "required": ["episode", "env_id", "step", "robot_id", "selected_viewpoint_id", "is_noop"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Directly stored per robot row.",
    },
    {
        "question": "budget trigger step",
        "required": ["budget_triggered_by_budget", "step"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Direct budget-trigger boolean is stored per robot row.",
    },
    {
        "question": "triggered robot-target pair",
        "required": ["budget_triggered_by_budget", "robot_id", "selected_viewpoint_id"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Trigger row identifies robot and selected target.",
    },
    {
        "question": "next selected target after trigger",
        "required": ["episode", "env_id", "step", "robot_id", "selected_viewpoint_id", "is_noop"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Inferred by scanning later rows for the same robot.",
    },
    {
        "question": "whether next target is already selected by another robot",
        "required": ["episode", "env_id", "step", "robot_id", "selected_viewpoint_id", "is_noop"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Inferred from other robot rows at the next-selection step.",
    },
    {
        "question": "target positions or viewpoint positions",
        "required": ["target_x", "target_y", "selected_viewpoint_id"],
        "status_when_present": "PARTIAL",
        "critical_for_attribution": True,
        "notes": "Selected target positions are stored; full unselected viewpoint table is not in assignment_history.",
    },
    {
        "question": "robot base positions",
        "required": ["robot_base_x", "robot_base_y"],
        "status_when_present": "PARTIAL",
        "critical_for_attribution": False,
        "notes": "Stored base positions are the pre-step positions captured by the playback script.",
    },
    {
        "question": "post-step robot base positions for future histories",
        "required": ["robot_base_post_x", "robot_base_post_y"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": False,
        "notes": "Phase 9F-2A future-history fields; absent in older playback histories.",
    },
    {
        "question": "duplicate selected target proxy",
        "required": ["duplicate_selected_target_on_step"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Direct exact duplicate proxy is stored per row.",
    },
    {
        "question": "base motion crossing proxy",
        "required": ["actual_base_motion_intersects_component", "actual_base_motion_distance"],
        "status_when_present": "PARTIAL",
        "critical_for_attribution": False,
        "notes": "Stored proxy is component/obstacle intersection, not true inter-robot path crossing.",
    },
    {
        "question": "coverage gain after redirect",
        "required": ["new_coverage_gain_after_step", "coverage_ratio_after_step", "newly_covered_viewpoint_ids"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Global gain and newly covered target ids are available after each step.",
    },
    {
        "question": "return to triggered pair after cooldown",
        "required": ["episode", "env_id", "step", "robot_id", "selected_viewpoint_id"],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": True,
        "notes": "Inferred by scanning later rows after the configured cooldown duration.",
    },
    {
        "question": "row-level selected-target conflict",
        "required": ["target_x", "target_y", "selected_viewpoint_id"],
        "status_when_present": "PARTIAL",
        "critical_for_attribution": True,
        "notes": "Not stored directly, but reconstructable as a target-distance proxy using the scenario threshold.",
    },
    {
        "question": "direct row-level selected-target conflict fields for future histories",
        "required": [
            "selected_target_conflict_pair_count",
            "selected_target_conflict_pairs",
            "selected_target_min_distance_to_other_selected",
            "selected_target_conflict_threshold",
        ],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": False,
        "notes": "Phase 9F-2A future-history fields; old histories remain reconstructable from target coordinates.",
    },
    {
        "question": "row-level inter-robot overlap",
        "required": [
            "inter_robot_overlap_pair_count",
            "inter_robot_overlap_pairs",
            "inter_robot_min_base_distance",
            "inter_robot_overlap_threshold",
        ],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": False,
        "notes": "Phase 9F-2A future-history fields; older histories only have aggregate summary.csv overlap.",
    },
    {
        "question": "row-level inter-robot path crossing or near-miss proxy",
        "required": [
            "inter_robot_path_crossing_pair_count",
            "inter_robot_path_crossing_pairs",
            "inter_robot_path_near_miss_pair_count",
            "inter_robot_path_near_miss_pairs",
            "inter_robot_path_near_miss_threshold",
        ],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": False,
        "notes": "Phase 9F-2A future-history observed pre/post base segment proxy.",
    },
    {
        "question": "same-step claim and nearby-claim snapshot",
        "required": [
            "same_step_claimed_target_count",
            "same_step_claimed_target_robot_ids",
            "same_step_nearby_claimed_target_count",
            "same_step_nearby_claimed_target_robot_ids",
        ],
        "status_when_present": "SUFFICIENT",
        "critical_for_attribution": False,
        "notes": "Phase 9F-2A future-history ownership snapshot fields.",
    },
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


def _parse_ids(value: Any) -> set[int]:
    text = str(value or "").strip()
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


def _read_csv_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        return next(reader, [])


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _read_summary(run_dir: Path) -> dict[str, str]:
    path = run_dir / "summary.csv"
    if not path.exists():
        return {}
    rows = _read_csv(path)
    return rows[0] if rows else {}


def _target_id(row: dict[str, Any]) -> int:
    if _bool(row.get("is_noop")):
        return -1
    return _int(row.get("selected_viewpoint_id"), -1)


def _row_step(row: dict[str, Any]) -> int:
    return _int(row.get("step"))


def _row_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _row_step(row))


def _robot_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("robot_id")))


def _target_xy(row: dict[str, Any]) -> tuple[float, float] | None:
    x = _float(row.get("target_x"))
    y = _float(row.get("target_y"))
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return x, y


def _distance(row_a: dict[str, Any], row_b: dict[str, Any]) -> float:
    pos_a = _target_xy(row_a)
    pos_b = _target_xy(row_b)
    if pos_a is None or pos_b is None:
        return math.nan
    return math.hypot(pos_a[0] - pos_b[0], pos_a[1] - pos_b[1])


def _step_metrics(step_rows: list[dict[str, Any]], *, threshold: float) -> dict[str, Any]:
    selected = [row for row in step_rows if _target_id(row) >= 0]
    target_counts = Counter(_target_id(row) for row in selected)
    exact_duplicate_robot_count = sum(max(0, count - 1) for count in target_counts.values())
    exact_duplicate_pair_count = sum(count * (count - 1) // 2 for count in target_counts.values())
    selected_target_conflict_pair_count = 0
    nearby_distinct_pair_count = 0
    min_target_distance = math.nan
    min_clearance = math.nan
    nearest_pair = ""
    for index, row_a in enumerate(selected):
        for row_b in selected[index + 1 :]:
            distance = _distance(row_a, row_b)
            if not math.isfinite(distance):
                continue
            if not math.isfinite(min_target_distance) or distance < min_target_distance:
                min_target_distance = distance
                min_clearance = distance - threshold
                nearest_pair = (
                    f"r{_int(row_a.get('robot_id'))}->{_target_id(row_a)};"
                    f"r{_int(row_b.get('robot_id'))}->{_target_id(row_b)}"
                )
            if distance < threshold:
                selected_target_conflict_pair_count += 1
                if _target_id(row_a) != _target_id(row_b):
                    nearby_distinct_pair_count += 1
    component_crossing_count = sum(1 for row in selected if _bool(row.get("actual_base_motion_intersects_component")))
    return {
        "selected_count": len(selected),
        "exact_duplicate_robot_count": exact_duplicate_robot_count,
        "exact_duplicate_pair_count": exact_duplicate_pair_count,
        "selected_target_conflict_pair_count": selected_target_conflict_pair_count,
        "nearby_distinct_pair_count": nearby_distinct_pair_count,
        "min_target_distance": min_target_distance,
        "min_clearance": min_clearance,
        "nearest_pair": nearest_pair,
        "component_crossing_count": component_crossing_count,
        "component_crossing_rate": component_crossing_count / len(step_rows) if step_rows else math.nan,
    }


def _mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def _rate(count: int, total: int) -> float:
    return count / float(total) if total else math.nan


def _format_counter(counter: Counter[Any], *, limit: int = 8) -> str:
    return "; ".join(f"{key}:{count}" for key, count in counter.most_common(limit))


def _first_non_noop_after(
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]],
    *,
    episode: int,
    env_id: int,
    robot_id: int,
    step: int,
) -> dict[str, Any] | None:
    for row in rows_by_robot[(episode, env_id, robot_id)]:
        if _row_step(row) > step and _target_id(row) >= 0:
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
        if _row_step(row) <= step + cooldown_duration:
            continue
        if _target_id(row) == target_id:
            return row
    return None


def _coverage_ratio_at_or_after(step_rows: dict[int, list[dict[str, Any]]], step: int) -> float:
    steps = [candidate for candidate in step_rows if candidate >= step]
    if not steps:
        return math.nan
    return _float(step_rows[min(steps)][0].get("coverage_ratio_after_step"))


def _gain_between(step_rows: dict[int, list[dict[str, Any]]], *, start: int, end: int) -> bool:
    for step, rows in step_rows.items():
        if start < step <= end and any(_bool(row.get("new_coverage_gain_after_step")) for row in rows):
            return True
    return False


def _target_covered_between(step_rows: dict[int, list[dict[str, Any]]], *, start: int, end: int, target_id: int) -> bool:
    if target_id < 0:
        return False
    for step, rows in step_rows.items():
        if start < step <= end and any(target_id in _parse_ids(row.get("newly_covered_viewpoint_ids")) for row in rows):
            return True
    return False


def _last_gain_step(step_rows: dict[int, list[dict[str, Any]]]) -> int:
    gain_steps = [
        step
        for step, rows in step_rows.items()
        if any(_bool(row.get("new_coverage_gain_after_step")) for row in rows)
    ]
    return max(gain_steps) if gain_steps else -1


def _window_step_set(
    trigger_rows: list[dict[str, Any]],
    *,
    max_step_by_episode: dict[tuple[int, int], int],
    window_steps: int,
) -> set[tuple[int, int, int]]:
    selected_steps: set[tuple[int, int, int]] = set()
    for row in trigger_rows:
        episode, env_id, step = _row_key(row)
        max_step = max_step_by_episode[(episode, env_id)]
        for window_step in range(step + 1, min(max_step, step + window_steps) + 1):
            selected_steps.add((episode, env_id, window_step))
    return selected_steps


def _period_rates(
    all_step_metrics: dict[tuple[int, int, int], dict[str, Any]],
    selected_keys: set[tuple[int, int, int]],
) -> dict[str, float]:
    metrics = [all_step_metrics[key] for key in sorted(selected_keys) if key in all_step_metrics]
    if not metrics:
        return {
            "step_count": 0,
            "selected_target_conflict_pair_rate": math.nan,
            "exact_duplicate_robot_rate": math.nan,
            "nearby_distinct_pair_rate": math.nan,
            "component_crossing_rate": math.nan,
        }
    return {
        "step_count": len(metrics),
        "selected_target_conflict_pair_rate": _mean(
            [_float(item.get("selected_target_conflict_pair_count")) for item in metrics]
        ),
        "exact_duplicate_robot_rate": _mean([_float(item.get("exact_duplicate_robot_count")) for item in metrics]),
        "nearby_distinct_pair_rate": _mean([_float(item.get("nearby_distinct_pair_count")) for item in metrics]),
        "component_crossing_rate": _mean([_float(item.get("component_crossing_rate")) for item in metrics]),
    }


def _parse_scenario_threshold(scenario_path: Path) -> dict[str, float | str]:
    defaults = {
        "target_conflict_radius": 0.35,
        "target_conflict_safety_margin": 0.15,
        "selected_target_conflict_threshold": 0.85,
        "source": "defaults",
    }
    if not scenario_path.exists():
        return defaults
    text = scenario_path.read_text(encoding="utf-8")
    radius_match = re.search(r"^\s*target_conflict_radius:\s*([-+0-9.eE]+)\s*$", text, re.MULTILINE)
    margin_match = re.search(r"^\s*target_conflict_safety_margin:\s*([-+0-9.eE]+)\s*$", text, re.MULTILINE)
    radius = float(radius_match.group(1)) if radius_match else float(defaults["target_conflict_radius"])
    margin = float(margin_match.group(1)) if margin_match else float(defaults["target_conflict_safety_margin"])
    return {
        "target_conflict_radius": radius,
        "target_conflict_safety_margin": margin,
        "selected_target_conflict_threshold": (2.0 * radius) + margin,
        "source": str(scenario_path),
    }


def _schema_inventory_rows(run_dirs: dict[str, Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    critical_statuses: list[str] = []
    all_statuses: list[str] = []
    for run_label, run_dir in run_dirs.items():
        history_path = run_dir / "assignment_history.csv"
        exists = history_path.exists()
        columns = _read_csv_header(history_path) if exists else []
        row_count = len(_read_csv(history_path)) if exists else 0
        column_set = set(columns)
        for requirement in SCHEMA_REQUIREMENTS:
            missing = [name for name in requirement["required"] if name not in column_set]
            if not exists:
                status = "MISSING_FILE"
            elif missing:
                status = "INSUFFICIENT"
            else:
                status = str(requirement["status_when_present"])
            if run_label in DEFAULT_RUNS:
                all_statuses.append(status)
                if bool(requirement.get("critical_for_attribution")):
                    critical_statuses.append(status)
            rows.append(
                {
                    "run_label": run_label,
                    "assignment_history_csv": str(history_path),
                    "file_exists": exists,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "question": requirement["question"],
                    "status": status,
                    "critical_for_attribution": bool(requirement.get("critical_for_attribution")),
                    "required_or_proxy_columns": ";".join(requirement["required"]),
                    "missing_columns": ";".join(missing),
                    "notes": requirement["notes"],
                }
            )
    primary_missing_file = any(status == "MISSING_FILE" for status in critical_statuses)
    primary_critical_insufficient = any(status == "INSUFFICIENT" for status in critical_statuses)
    primary_any_insufficient = any(status == "INSUFFICIENT" for status in all_statuses)
    primary_partial = any(status == "PARTIAL" for status in all_statuses)
    if primary_missing_file or primary_critical_insufficient:
        sufficiency = "DIAG-INCOMPLETE"
    elif primary_partial or primary_any_insufficient:
        sufficiency = "DIAG-PARTIAL"
    else:
        sufficiency = "DIAG-SUFFICIENT"
    return rows, {
        "schema_sufficiency": sufficiency,
        "primary_missing_file": primary_missing_file,
        "primary_has_critical_insufficient_fields": primary_critical_insufficient,
        "primary_has_noncritical_insufficient_fields": primary_any_insufficient and not primary_critical_insufficient,
        "primary_has_partial_proxy_fields": primary_partial,
    }


def _analyze_run(
    run_label: str,
    run_dir: Path,
    *,
    threshold: float,
    window_steps: int,
    cooldown_duration: int,
) -> dict[str, Any]:
    rows = _read_csv(run_dir / "assignment_history.csv")
    summary = _read_summary(run_dir)
    rows_by_step: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    rows_by_robot: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    step_rows_by_episode: dict[tuple[int, int], dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        row["_run_label"] = run_label
        rows_by_step[_row_key(row)].append(row)
        rows_by_robot[_robot_key(row)].append(row)
        episode, env_id, step = _row_key(row)
        step_rows_by_episode[(episode, env_id)][step].append(row)
    for key in rows_by_robot:
        rows_by_robot[key].sort(key=_row_step)

    step_metrics = {
        key: _step_metrics(step_rows, threshold=threshold) for key, step_rows in rows_by_step.items()
    }
    max_step_by_episode = {
        key: max(steps.keys()) for key, steps in step_rows_by_episode.items() if steps
    }
    trigger_rows = [row for row in rows if _bool(row.get("budget_triggered_by_budget"))]
    window_keys = _window_step_set(
        trigger_rows,
        max_step_by_episode=max_step_by_episode,
        window_steps=window_steps,
    )
    all_keys = set(step_metrics)
    outside_keys = all_keys - window_keys
    within_rates = _period_rates(step_metrics, window_keys)
    outside_rates = _period_rates(step_metrics, outside_keys)
    all_rates = _period_rates(step_metrics, all_keys)

    window_rows: list[dict[str, Any]] = []
    next_target_rows: list[dict[str, Any]] = []
    for trigger in trigger_rows:
        episode, env_id, trigger_step = _row_key(trigger)
        robot_id = _int(trigger.get("robot_id"))
        trigger_target = _target_id(trigger)
        episode_steps = step_rows_by_episode[(episode, env_id)]
        next_row = _first_non_noop_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=trigger_step,
        )
        next_step = _row_step(next_row) if next_row is not None else -1
        next_target = _target_id(next_row) if next_row is not None else -1
        next_rows = rows_by_step.get((episode, env_id, next_step), [])
        other_next_rows = [row for row in next_rows if _int(row.get("robot_id")) != robot_id]
        exact_claimed_by = [
            _int(row.get("robot_id")) for row in other_next_rows if _target_id(row) == next_target and next_target >= 0
        ]
        nearest_other_robot = ""
        nearest_other_target = ""
        nearest_distance = math.nan
        nearby_robots: list[str] = []
        for other in other_next_rows:
            other_target = _target_id(other)
            if next_row is None or other_target < 0:
                continue
            distance = _distance(next_row, other)
            if not math.isfinite(distance):
                continue
            if not math.isfinite(nearest_distance) or distance < nearest_distance:
                nearest_distance = distance
                nearest_other_robot = str(_int(other.get("robot_id")))
                nearest_other_target = str(other_target)
            if other_target != next_target and distance < threshold:
                nearby_robots.append(f"r{_int(other.get('robot_id'))}->{other_target}@{distance:.3f}")
        next_metrics = step_metrics.get(
            (episode, env_id, next_step),
            {
                "selected_target_conflict_pair_count": math.nan,
                "exact_duplicate_robot_count": math.nan,
                "nearby_distinct_pair_count": math.nan,
                "component_crossing_rate": math.nan,
                "min_target_distance": math.nan,
                "min_clearance": math.nan,
            },
        )
        window_step_keys = [
            (episode, env_id, step)
            for step in range(trigger_step + 1, min(max_step_by_episode[(episode, env_id)], trigger_step + window_steps) + 1)
        ]
        window_metrics = [step_metrics[key] for key in window_step_keys if key in step_metrics]
        window_triggered_robot_rows = [
            row
            for row in rows_by_robot[(episode, env_id, robot_id)]
            if trigger_step < _row_step(row) <= trigger_step + window_steps
        ]
        exact_duplicate_steps = sum(1 for item in window_metrics if _int(item.get("exact_duplicate_robot_count")) > 0)
        nearby_conflict_steps = sum(1 for item in window_metrics if _int(item.get("nearby_distinct_pair_count")) > 0)
        selected_conflict_steps = sum(
            1 for item in window_metrics if _int(item.get("selected_target_conflict_pair_count")) > 0
        )
        crossing_steps = sum(1 for item in window_metrics if _float(item.get("component_crossing_rate")) > 0.0)
        triggered_robot_crossing_rows = sum(
            1 for row in window_triggered_robot_rows if _bool(row.get("actual_base_motion_intersects_component"))
        )
        coverage_at_trigger = _float(trigger.get("coverage_ratio_after_step"))
        coverage_at_20 = _coverage_ratio_at_or_after(episode_steps, trigger_step + window_steps)
        return_row = _first_return_after(
            rows_by_robot,
            episode=episode,
            env_id=env_id,
            robot_id=robot_id,
            step=trigger_step,
            target_id=trigger_target,
            cooldown_duration=cooldown_duration,
        )
        last_gain = _last_gain_step(episode_steps)
        max_same_target_streak_20 = max(
            (_float(row.get("same_target_streak"), 0.0) for row in window_triggered_robot_rows),
            default=0.0,
        )
        record = {
            "run_label": run_label,
            "checkpoint_kind": summary.get("checkpoint_kind", run_label),
            "episode": episode,
            "env_id": env_id,
            "trigger_step": trigger_step,
            "trigger_robot_id": robot_id,
            "trigger_target_id": trigger_target,
            "trigger_pair": f"r{robot_id}->{trigger_target}",
            "trigger_after_last_coverage_gain": trigger_step > last_gain,
            "attempt_steps_for_selected_pair": _int(trigger.get("budget_attempt_steps_for_selected_pair")),
            "budget_steps_for_selected_pair": _int(trigger.get("budget_steps_for_selected_pair")),
            "same_target_streak_at_trigger": _float(trigger.get("same_target_streak")),
            "coverage_ratio_at_trigger": coverage_at_trigger,
            "next_non_noop_step": "" if next_row is None else next_step,
            "next_non_noop_target_id": "" if next_row is None else next_target,
            "next_target_selected_available": "" if next_row is None else _bool(next_row.get("selected_available")),
            "next_target_selected_feasible": "" if next_row is None else _bool(next_row.get("selected_feasible")),
            "next_target_selected_covered_before": "" if next_row is None else _bool(next_row.get("selected_covered_before")),
            "next_target_exact_claimed_by_other_robot": bool(exact_claimed_by),
            "next_target_claimed_by_robot_ids": ";".join(str(item) for item in exact_claimed_by),
            "next_target_nearby_distinct_other_target_count": len(nearby_robots),
            "next_target_nearby_distinct_other_targets": ";".join(nearby_robots),
            "nearest_other_robot_at_next_step": nearest_other_robot,
            "nearest_other_target_at_next_step": nearest_other_target,
            "nearest_other_target_distance_at_next_step": _format_float(nearest_distance),
            "next_step_selected_target_conflict_pair_count": next_metrics["selected_target_conflict_pair_count"],
            "next_step_exact_duplicate_robot_count": next_metrics["exact_duplicate_robot_count"],
            "next_step_nearby_distinct_pair_count": next_metrics["nearby_distinct_pair_count"],
            "next_step_min_target_distance": _format_float(next_metrics["min_target_distance"]),
            "next_step_min_clearance": _format_float(next_metrics["min_clearance"]),
            "coverage_gain_within_20_steps": _gain_between(episode_steps, start=trigger_step, end=trigger_step + window_steps),
            "coverage_delta_within_20_steps": _format_float(coverage_at_20 - coverage_at_trigger),
            "next_target_covered_within_20_steps": _target_covered_between(
                episode_steps,
                start=trigger_step,
                end=trigger_step + window_steps,
                target_id=next_target,
            ),
            "trigger_target_covered_within_20_steps": _target_covered_between(
                episode_steps,
                start=trigger_step,
                end=trigger_step + window_steps,
                target_id=trigger_target,
            ),
            "selected_target_conflict_step_count_20": selected_conflict_steps,
            "exact_duplicate_step_count_20": exact_duplicate_steps,
            "nearby_distinct_conflict_step_count_20": nearby_conflict_steps,
            "component_crossing_step_count_20": crossing_steps,
            "triggered_robot_component_crossing_row_count_20": triggered_robot_crossing_rows,
            "selected_target_conflict_pair_rate_20": _format_float(
                _mean([_float(item.get("selected_target_conflict_pair_count")) for item in window_metrics])
            ),
            "exact_duplicate_robot_rate_20": _format_float(
                _mean([_float(item.get("exact_duplicate_robot_count")) for item in window_metrics])
            ),
            "nearby_distinct_pair_rate_20": _format_float(
                _mean([_float(item.get("nearby_distinct_pair_count")) for item in window_metrics])
            ),
            "component_crossing_rate_20": _format_float(
                _mean([_float(item.get("component_crossing_rate")) for item in window_metrics])
            ),
            "returns_to_triggered_pair_after_cooldown": return_row is not None,
            "return_step_after_cooldown": "" if return_row is None else _row_step(return_row),
            "max_same_target_streak_within_20_steps": max_same_target_streak_20,
        }
        window_rows.append(record)
        next_target_rows.append(record)

    trigger_count = len(window_rows)
    exact_next_count = sum(1 for row in window_rows if row["next_target_exact_claimed_by_other_robot"])
    nearby_next_count = sum(1 for row in window_rows if _int(row["next_target_nearby_distinct_other_target_count"]) > 0)
    coverage_gain_count = sum(1 for row in window_rows if row["coverage_gain_within_20_steps"])
    next_target_covered_count = sum(1 for row in window_rows if row["next_target_covered_within_20_steps"])
    return_count = sum(1 for row in window_rows if row["returns_to_triggered_pair_after_cooldown"])
    triggers_after_last_gain = sum(1 for row in window_rows if row["trigger_after_last_coverage_gain"])
    trigger_pair_counter = Counter(row["trigger_pair"] for row in window_rows)
    next_target_counter = Counter(str(row["next_non_noop_target_id"]) for row in window_rows)
    exact_by_robot = Counter(str(row["trigger_robot_id"]) for row in window_rows if row["next_target_exact_claimed_by_other_robot"])
    nearby_by_robot = Counter(
        str(row["trigger_robot_id"])
        for row in window_rows
        if _int(row["next_target_nearby_distinct_other_target_count"]) > 0
    )
    return_by_pair = Counter(row["trigger_pair"] for row in window_rows if row["returns_to_triggered_pair_after_cooldown"])

    exact_duplicate_ratio = _rate(exact_next_count, trigger_count)
    nearby_ratio = _rate(nearby_next_count, trigger_count)
    return_ratio = _rate(return_count, trigger_count)
    coverage_gain_ratio = _rate(coverage_gain_count, trigger_count)
    within_conflict = within_rates["selected_target_conflict_pair_rate"]
    outside_conflict = outside_rates["selected_target_conflict_pair_rate"]
    within_crossing = within_rates["component_crossing_rate"]
    outside_crossing = outside_rates["component_crossing_rate"]

    cause_flags = []
    if math.isfinite(exact_duplicate_ratio) and exact_duplicate_ratio >= 0.25:
        cause_flags.append("A")
    if math.isfinite(nearby_ratio) and nearby_ratio >= 0.25:
        cause_flags.append("B")
    if (
        math.isfinite(within_crossing)
        and within_crossing >= 0.10
        and (not math.isfinite(outside_crossing) or within_crossing >= outside_crossing * 1.25)
    ):
        cause_flags.append("C")
    if (
        math.isfinite(outside_conflict)
        and outside_conflict > 0.25
        and (
            not math.isfinite(within_conflict)
            or outside_conflict >= within_conflict * 0.40
            or math.isclose(outside_conflict, within_conflict, rel_tol=0.20)
        )
    ):
        cause_flags.append("D")
    if "A" not in cause_flags and "B" not in cause_flags and "C" not in cause_flags and "D" not in cause_flags:
        cause_flags.append("E")

    summary_record = {
        "run_label": run_label,
        "checkpoint_kind": summary.get("checkpoint_kind", run_label),
        "total_budget_triggers": trigger_count,
        "trigger_pair_distribution": _format_counter(trigger_pair_counter),
        "next_target_distribution": _format_counter(next_target_counter),
        "exact_duplicate_next_target_claim_count": exact_next_count,
        "exact_duplicate_next_target_claim_rate": exact_duplicate_ratio,
        "nearby_distinct_next_target_conflict_count": nearby_next_count,
        "nearby_distinct_next_target_conflict_rate": nearby_ratio,
        "coverage_gain_within_20_count": coverage_gain_count,
        "coverage_gain_within_20_rate": coverage_gain_ratio,
        "next_target_covered_within_20_count": next_target_covered_count,
        "next_target_covered_within_20_rate": _rate(next_target_covered_count, trigger_count),
        "returns_to_triggered_pair_after_cooldown_count": return_count,
        "returns_to_triggered_pair_after_cooldown_rate": return_ratio,
        "triggers_after_last_coverage_gain_count": triggers_after_last_gain,
        "triggers_after_last_coverage_gain_rate": _rate(triggers_after_last_gain, trigger_count),
        "selected_target_conflict_pair_rate_overall_reconstructed": all_rates["selected_target_conflict_pair_rate"],
        "selected_target_conflict_pair_rate_within_20_steps_after_triggers": within_conflict,
        "selected_target_conflict_pair_rate_outside_trigger_windows": outside_conflict,
        "exact_duplicate_robot_rate_overall_reconstructed": all_rates["exact_duplicate_robot_rate"],
        "exact_duplicate_robot_rate_within_20_steps_after_triggers": within_rates["exact_duplicate_robot_rate"],
        "exact_duplicate_robot_rate_outside_trigger_windows": outside_rates["exact_duplicate_robot_rate"],
        "nearby_distinct_pair_rate_overall_reconstructed": all_rates["nearby_distinct_pair_rate"],
        "nearby_distinct_pair_rate_within_20_steps_after_triggers": within_rates["nearby_distinct_pair_rate"],
        "nearby_distinct_pair_rate_outside_trigger_windows": outside_rates["nearby_distinct_pair_rate"],
        "component_crossing_rate_overall_reconstructed": all_rates["component_crossing_rate"],
        "component_crossing_rate_within_20_steps_after_triggers": within_crossing,
        "component_crossing_rate_outside_trigger_windows": outside_crossing,
        "summary_selected_target_conflict_rate": _float(summary.get("selected_target_conflict_rate_mean")),
        "summary_inter_robot_overlap_rate": _float(summary.get("inter_robot_overlap_rate_mean")),
        "summary_component_crossing_rate": _float(summary.get("actual_base_motion_intersection_rate_mean")),
        "summary_duplicate_selected_target_rate": _float(summary.get("duplicate_selected_target_rate_mean")),
        "dominant_trigger_pair": trigger_pair_counter.most_common(1)[0][0] if trigger_pair_counter else "",
        "dominant_next_target": next_target_counter.most_common(1)[0][0] if next_target_counter else "",
        "exact_duplicate_dominant_robot": exact_by_robot.most_common(1)[0][0] if exact_by_robot else "",
        "nearby_conflict_dominant_robot": nearby_by_robot.most_common(1)[0][0] if nearby_by_robot else "",
        "return_dominant_pair": return_by_pair.most_common(1)[0][0] if return_by_pair else "",
        "cause_categories": "+".join(cause_flags),
    }
    return {
        "run_label": run_label,
        "run_dir": str(run_dir),
        "summary": summary_record,
        "window_rows": window_rows,
    }


def _next_target_summary_rows(window_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in window_rows:
        grouped[(row["run_label"], str(row["next_non_noop_target_id"]))].append(row)
    output: list[dict[str, Any]] = []
    for (run_label, next_target), rows in sorted(grouped.items()):
        count = len(rows)
        robots = Counter(str(row["trigger_robot_id"]) for row in rows)
        trigger_pairs = Counter(row["trigger_pair"] for row in rows)
        output.append(
            {
                "run_label": run_label,
                "next_non_noop_target_id": next_target,
                "count": count,
                "trigger_robot_distribution": _format_counter(robots),
                "trigger_pair_distribution": _format_counter(trigger_pairs),
                "exact_claimed_by_other_robot_count": sum(
                    1 for row in rows if row["next_target_exact_claimed_by_other_robot"]
                ),
                "exact_claimed_by_other_robot_rate": _format_float(
                    _rate(sum(1 for row in rows if row["next_target_exact_claimed_by_other_robot"]), count)
                ),
                "nearby_distinct_conflict_count": sum(
                    1 for row in rows if _int(row["next_target_nearby_distinct_other_target_count"]) > 0
                ),
                "nearby_distinct_conflict_rate": _format_float(
                    _rate(
                        sum(1 for row in rows if _int(row["next_target_nearby_distinct_other_target_count"]) > 0),
                        count,
                    )
                ),
                "coverage_gain_within_20_count": sum(1 for row in rows if row["coverage_gain_within_20_steps"]),
                "next_target_covered_within_20_count": sum(
                    1 for row in rows if row["next_target_covered_within_20_steps"]
                ),
                "return_to_triggered_pair_after_cooldown_count": sum(
                    1 for row in rows if row["returns_to_triggered_pair_after_cooldown"]
                ),
            }
        )
    return output


def _flatten_attribution_rows(run_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in run_summaries:
        row = dict(item)
        for key, value in list(row.items()):
            if isinstance(value, float):
                row[key] = _format_float(value)
        rows.append(row)
    return rows


def _phase_classification(schema_status: dict[str, Any], run_summaries: list[dict[str, Any]]) -> str:
    if schema_status["schema_sufficiency"] == "DIAG-INCOMPLETE":
        return "DIAG-I"
    if any("E" in str(row.get("cause_categories", "")) for row in run_summaries):
        return "DIAG-I"
    exact_or_nearby = any(
        category in str(row.get("cause_categories", ""))
        for row in run_summaries
        for category in ["A", "B", "C", "D"]
    )
    if not exact_or_nearby:
        return "DIAG-N"
    return "DIAG-P" if schema_status["schema_sufficiency"] == "DIAG-PARTIAL" else "DIAG-S"


def _make_notes(
    output_dir: Path,
    *,
    schema_status: dict[str, Any],
    run_summaries: list[dict[str, Any]],
    classification: str,
    threshold_info: dict[str, Any],
) -> None:
    lines = [
        "# Phase 9F-1 Conflict Diagnostics Notes",
        "",
        "No training was run. No playback was run. This diagnostic reads existing playback CSV/JSON outputs only.",
        "",
        f"Schema sufficiency: {schema_status['schema_sufficiency']}.",
        (
            "Selected-target spatial conflict is reconstructed from selected target coordinates using "
            f"threshold {threshold_info['selected_target_conflict_threshold']:.3f} m. "
            "Row-level inter-robot overlap is not present, so overlap attribution remains aggregate-only."
        ),
        "",
        "## Attribution Summary",
        "",
        "| Run | Triggers | Exact next claim | Nearby next conflict | Coverage gain within 20 | Return after cooldown | Causes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in run_summaries:
        lines.append(
            "| {run} | {triggers} | {exact}/{triggers} | {nearby}/{triggers} | {gain}/{triggers} | "
            "{returns}/{triggers} | {causes} |".format(
                run=row["run_label"],
                triggers=row["total_budget_triggers"],
                exact=row["exact_duplicate_next_target_claim_count"],
                nearby=row["nearby_distinct_next_target_conflict_count"],
                gain=row["coverage_gain_within_20_count"],
                returns=row["returns_to_triggered_pair_after_cooldown_count"],
                causes=row["cause_categories"],
            )
        )
    lines.extend(
        [
            "",
            "## Cause Labels",
            "",
            "- A: exact duplicate redirect conflict.",
            "- B: nearby-target spatial conflict.",
            "- C: component/base-motion crossing proxy is elevated in post-trigger windows.",
            "- D: persistent policy preference; conflict also remains outside trigger windows.",
            "- E: insufficient trace fields.",
            "",
            "## Mechanism Recommendation Table",
            "",
            "| Diagnosis | Possible next mechanism |",
            "|---|---|",
            "| Exact duplicate conflict | target reservation / claimed-target mask |",
            "| Nearby target conflict | target proximity exclusion or spacing-aware redirect |",
            "| Path crossing conflict | path-crossing-aware redirect diagnostics |",
            "| Persistent policy preference | policy/reward/lifecycle issue; do not solve with another local mask only |",
            "| Repeated return to triggered pair | active-task lifecycle or explicit failed-target state |",
            "| Insufficient fields | add diagnostics before mechanism changes |",
            "",
            "## Classification",
            "",
            classification,
            "",
        ]
    )
    (output_dir / "phase9f1_conflict_diagnostics_notes.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scenario_config", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--window_steps", type=int, default=20)
    parser.add_argument("--cooldown_duration", type=int, default=5)
    parser.add_argument("--models_dir", type=Path, default=DEFAULT_RUNS["phase9e4b_models_budget"])
    parser.add_argument("--best_model_dir", type=Path, default=DEFAULT_RUNS["phase9e4b_best_model_budget"])
    parser.add_argument("--comparison_models_dir", type=Path, default=DEFAULT_COMPARISON_RUNS["phase9e3d_models_budget"])
    parser.add_argument(
        "--comparison_best_model_dir",
        type=Path,
        default=DEFAULT_COMPARISON_RUNS["phase9e3d_best_model_budget"],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    primary_runs = {
        "phase9e4b_models_budget": args.models_dir,
        "phase9e4b_best_model_budget": args.best_model_dir,
    }
    comparison_runs = {
        "phase9e3d_models_budget": args.comparison_models_dir,
        "phase9e3d_best_model_budget": args.comparison_best_model_dir,
    }
    available_runs = {
        label: path
        for label, path in {**primary_runs, **comparison_runs}.items()
        if (path / "assignment_history.csv").exists()
    }
    missing_primary = [
        str(path / "assignment_history.csv")
        for path in primary_runs.values()
        if not (path / "assignment_history.csv").exists()
    ]
    if missing_primary:
        raise FileNotFoundError(f"Missing primary assignment_history.csv files: {missing_primary}")

    threshold_info = _parse_scenario_threshold(args.scenario_config)
    threshold = float(threshold_info["selected_target_conflict_threshold"])
    schema_rows, schema_status = _schema_inventory_rows(available_runs)
    run_results = [
        _analyze_run(
            label,
            path,
            threshold=threshold,
            window_steps=args.window_steps,
            cooldown_duration=args.cooldown_duration,
        )
        for label, path in primary_runs.items()
    ]
    window_rows = [row for result in run_results for row in result["window_rows"]]
    next_target_rows = _next_target_summary_rows(window_rows)
    run_summaries = [result["summary"] for result in run_results]
    classification = _phase_classification(schema_status, run_summaries)

    _write_csv(
        output_dir / "assignment_history_schema_inventory.csv",
        schema_rows,
        [
            "run_label",
            "assignment_history_csv",
            "file_exists",
            "row_count",
            "column_count",
            "question",
            "status",
            "critical_for_attribution",
            "required_or_proxy_columns",
            "missing_columns",
            "notes",
        ],
    )
    _write_csv(
        output_dir / "post_trigger_conflict_windows.csv",
        window_rows,
        [
            "run_label",
            "checkpoint_kind",
            "episode",
            "env_id",
            "trigger_step",
            "trigger_robot_id",
            "trigger_target_id",
            "trigger_pair",
            "trigger_after_last_coverage_gain",
            "attempt_steps_for_selected_pair",
            "budget_steps_for_selected_pair",
            "same_target_streak_at_trigger",
            "coverage_ratio_at_trigger",
            "next_non_noop_step",
            "next_non_noop_target_id",
            "next_target_selected_available",
            "next_target_selected_feasible",
            "next_target_selected_covered_before",
            "next_target_exact_claimed_by_other_robot",
            "next_target_claimed_by_robot_ids",
            "next_target_nearby_distinct_other_target_count",
            "next_target_nearby_distinct_other_targets",
            "nearest_other_robot_at_next_step",
            "nearest_other_target_at_next_step",
            "nearest_other_target_distance_at_next_step",
            "next_step_selected_target_conflict_pair_count",
            "next_step_exact_duplicate_robot_count",
            "next_step_nearby_distinct_pair_count",
            "next_step_min_target_distance",
            "next_step_min_clearance",
            "coverage_gain_within_20_steps",
            "coverage_delta_within_20_steps",
            "next_target_covered_within_20_steps",
            "trigger_target_covered_within_20_steps",
            "selected_target_conflict_step_count_20",
            "exact_duplicate_step_count_20",
            "nearby_distinct_conflict_step_count_20",
            "component_crossing_step_count_20",
            "triggered_robot_component_crossing_row_count_20",
            "selected_target_conflict_pair_rate_20",
            "exact_duplicate_robot_rate_20",
            "nearby_distinct_pair_rate_20",
            "component_crossing_rate_20",
            "returns_to_triggered_pair_after_cooldown",
            "return_step_after_cooldown",
            "max_same_target_streak_within_20_steps",
        ],
    )
    _write_csv(
        output_dir / "post_trigger_next_target_summary.csv",
        next_target_rows,
        [
            "run_label",
            "next_non_noop_target_id",
            "count",
            "trigger_robot_distribution",
            "trigger_pair_distribution",
            "exact_claimed_by_other_robot_count",
            "exact_claimed_by_other_robot_rate",
            "nearby_distinct_conflict_count",
            "nearby_distinct_conflict_rate",
            "coverage_gain_within_20_count",
            "next_target_covered_within_20_count",
            "return_to_triggered_pair_after_cooldown_count",
        ],
    )
    _write_csv(
        output_dir / "conflict_cause_attribution_summary.csv",
        _flatten_attribution_rows(run_summaries),
        [
            "run_label",
            "checkpoint_kind",
            "total_budget_triggers",
            "trigger_pair_distribution",
            "next_target_distribution",
            "exact_duplicate_next_target_claim_count",
            "exact_duplicate_next_target_claim_rate",
            "nearby_distinct_next_target_conflict_count",
            "nearby_distinct_next_target_conflict_rate",
            "coverage_gain_within_20_count",
            "coverage_gain_within_20_rate",
            "next_target_covered_within_20_count",
            "next_target_covered_within_20_rate",
            "returns_to_triggered_pair_after_cooldown_count",
            "returns_to_triggered_pair_after_cooldown_rate",
            "triggers_after_last_coverage_gain_count",
            "triggers_after_last_coverage_gain_rate",
            "selected_target_conflict_pair_rate_overall_reconstructed",
            "selected_target_conflict_pair_rate_within_20_steps_after_triggers",
            "selected_target_conflict_pair_rate_outside_trigger_windows",
            "exact_duplicate_robot_rate_overall_reconstructed",
            "exact_duplicate_robot_rate_within_20_steps_after_triggers",
            "exact_duplicate_robot_rate_outside_trigger_windows",
            "nearby_distinct_pair_rate_overall_reconstructed",
            "nearby_distinct_pair_rate_within_20_steps_after_triggers",
            "nearby_distinct_pair_rate_outside_trigger_windows",
            "component_crossing_rate_overall_reconstructed",
            "component_crossing_rate_within_20_steps_after_triggers",
            "component_crossing_rate_outside_trigger_windows",
            "summary_selected_target_conflict_rate",
            "summary_inter_robot_overlap_rate",
            "summary_component_crossing_rate",
            "summary_duplicate_selected_target_rate",
            "dominant_trigger_pair",
            "dominant_next_target",
            "exact_duplicate_dominant_robot",
            "nearby_conflict_dominant_robot",
            "return_dominant_pair",
            "cause_categories",
        ],
    )

    summary_json = {
        "classification": classification,
        "schema_status": schema_status,
        "threshold_info": threshold_info,
        "window_steps": args.window_steps,
        "cooldown_duration": args.cooldown_duration,
        "inputs": {label: str(path) for label, path in primary_runs.items()},
        "optional_comparison_inputs_present": {
            label: (path / "assignment_history.csv").exists() for label, path in comparison_runs.items()
        },
        "run_summaries": run_summaries,
        "field_limitations": {
            "row_level_selected_target_conflict": (
                "not stored directly; reconstructed from selected target positions and scenario threshold"
            ),
            "row_level_inter_robot_overlap": (
                "not present in assignment_history.csv; only aggregate summary.csv overlap rates are available"
            ),
            "base_motion_crossing_proxy": (
                "actual_base_motion_intersects_component is a component/obstacle intersection proxy, "
                "not true inter-robot path crossing"
            ),
            "robot_base_positions": "history stores pre-step base positions from playback diagnostics",
        },
        "mechanism_recommendations": [
            {
                "diagnosis": "exact duplicate conflict",
                "possible_next_mechanism": "target reservation / claimed-target mask",
            },
            {
                "diagnosis": "nearby target conflict",
                "possible_next_mechanism": "target proximity exclusion or spacing-aware redirect",
            },
            {
                "diagnosis": "path crossing conflict",
                "possible_next_mechanism": "path-crossing-aware redirect diagnostics",
            },
            {
                "diagnosis": "persistent policy preference",
                "possible_next_mechanism": "policy/reward/lifecycle issue; do not solve with another local mask only",
            },
            {
                "diagnosis": "repeated return to triggered pair",
                "possible_next_mechanism": "active-task lifecycle or explicit failed-target state",
            },
            {
                "diagnosis": "insufficient fields",
                "possible_next_mechanism": "add diagnostics before mechanism changes",
            },
        ],
        "outputs": {
            "assignment_history_schema_inventory_csv": str(output_dir / "assignment_history_schema_inventory.csv"),
            "post_trigger_conflict_windows_csv": str(output_dir / "post_trigger_conflict_windows.csv"),
            "post_trigger_next_target_summary_csv": str(output_dir / "post_trigger_next_target_summary.csv"),
            "conflict_cause_attribution_summary_csv": str(output_dir / "conflict_cause_attribution_summary.csv"),
            "notes_md": str(output_dir / "phase9f1_conflict_diagnostics_notes.md"),
        },
    }
    _write_json(output_dir / "phase9f1_conflict_diagnostics_summary.json", summary_json)
    _make_notes(
        output_dir,
        schema_status=schema_status,
        run_summaries=run_summaries,
        classification=classification,
        threshold_info=threshold_info,
    )
    print(json.dumps(summary_json, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
