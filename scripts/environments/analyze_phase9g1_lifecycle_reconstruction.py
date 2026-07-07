"""Phase 9G-1 lifecycle proxy reconstruction analyzer.

This script is offline CSV analysis only. It reconstructs proxy lifecycle labels
from existing ``assignment_history.csv`` rows and does not import or mutate the
Isaac Lab environment, HARL, wrappers, rewards, controllers, or scenario YAML.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("results/assignment_diagnostics/phase9g1_lifecycle_reconstruction")

REQUIRED_BASE_COLUMNS = [
    "episode",
    "env_id",
    "step",
    "robot_id",
    "is_noop",
]

SELECTION_COLUMN_CANDIDATES = [
    "selected_viewpoint_id",
    "assigned_viewpoint_id",
]

OPTIONAL_COLUMNS = [
    "method",
    "robot_name",
    "selected_available",
    "selected_feasible",
    "selected_covered_before",
    "new_coverage_gain_after_step",
    "coverage_ratio_after_step",
    "newly_covered_viewpoint_ids",
    "same_target_streak",
    "cooldown_active_for_selected_pair",
    "cooldown_remaining_for_selected_pair",
    "cooldown_triggered_after_step",
    "cooldown_suppressed_available_count_for_robot",
    "failed_attempt_count_for_selected_pair",
    "cooldown_trigger_mode",
    "budget_attempt_steps_for_selected_pair",
    "budget_steps_for_selected_pair",
    "budget_expected_steps_for_selected_pair",
    "budget_ratio_for_selected_pair",
    "budget_triggered_after_step",
    "budget_triggered_by_budget",
    "redirect_guardrail_active_for_robot",
    "redirect_guardrail_context",
    "claimed_target_redirect_suppressed_count",
    "spacing_redirect_suppressed_count",
    "redirect_guardrail_overmask_non_noop_count",
    "redirect_guardrail_only_noop_remaining",
    "redirect_guardrail_fail_open_reason",
    "redirect_guardrail_threshold",
    "redirect_guardrail_claimed_target_robot_ids",
    "redirect_guardrail_nearby_target_robot_ids",
]

LIFECYCLE_FIELDS = [
    "lifecycle_reconstructed_state",
    "lifecycle_state_reason",
    "active_assignment_age_steps",
    "attempt_segment_id",
    "attempt_segment_step",
    "failed_pair_memory_start_step",
    "failed_pair_memory_ttl_proxy",
    "released_after_budget_trigger",
    "returned_to_failed_pair_after_release",
    "coverage_gain_before_release",
    "coverage_gain_within_20_after_release",
    "same_owner_reacquire_step",
    "teammate_reacquire_step",
    "same_owner_return_delay_steps",
    "teammate_reacquire_delay_steps",
]

ROW_PREFIX_FIELDS = [
    "source_file_index",
    "source_file",
    "source_row_index",
]

FILE_SUMMARY_FIELDS = [
    "source_file_index",
    "source_file",
    "num_rows",
    "num_envs",
    "num_robots",
    "num_attempt_segments",
    "num_completed_segments",
    "num_budget_failed_segments",
    "num_released_segments",
    "num_same_owner_returns",
    "num_teammate_reacquires",
    "median_same_owner_return_delay_steps",
    "min_same_owner_return_delay_steps",
    "max_same_owner_return_delay_steps",
    "coverage_gain_after_release_count",
    "coverage_gain_within_20_count",
    "unsupported_file_count",
    "available_columns",
    "required_columns_present",
    "required_columns_missing",
    "optional_columns_present",
    "optional_columns_missing",
    "can_reconstruct_lifecycle",
    "unsupported_reason",
    "reconstruction_level",
    "phase9g2_failed_pair_release_memory_signal",
]

AGGREGATE_SUMMARY_FIELDS = [
    "num_files",
    "num_rows",
    "num_envs",
    "num_robots",
    "num_attempt_segments",
    "num_completed_segments",
    "num_budget_failed_segments",
    "num_released_segments",
    "num_same_owner_returns",
    "num_teammate_reacquires",
    "median_same_owner_return_delay_steps",
    "min_same_owner_return_delay_steps",
    "max_same_owner_return_delay_steps",
    "coverage_gain_after_release_count",
    "coverage_gain_within_20_count",
    "unsupported_file_count",
    "phase9g2_failed_pair_release_memory_signal",
]

STATE_PRIORITY = {
    "unknown_or_insufficient_columns": 0,
    "idle_or_noop_proxy": 10,
    "assigned_proxy": 20,
    "executing_proxy": 25,
    "released_after_failure_proxy": 30,
    "teammate_reacquired_proxy": 35,
    "returned_after_release_proxy": 40,
    "failed_budget_proxy": 50,
    "completed_proxy": 60,
}


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


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


def _json_list(value: Any) -> list[Any]:
    text = str(value or "").strip()
    if not text:
        return []
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return parsed
    return []


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _format_number(value: float | int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")


def _inspect_columns(columns: list[str]) -> dict[str, Any]:
    column_set = set(columns)
    required_present = [name for name in REQUIRED_BASE_COLUMNS if name in column_set]
    required_missing = [name for name in REQUIRED_BASE_COLUMNS if name not in column_set]
    selection_column = next((name for name in SELECTION_COLUMN_CANDIDATES if name in column_set), None)
    if selection_column is None:
        required_missing.append("selected_viewpoint_id_or_assigned_viewpoint_id")
    else:
        required_present.append(selection_column)

    optional_present = [name for name in OPTIONAL_COLUMNS if name in column_set]
    optional_missing = [name for name in OPTIONAL_COLUMNS if name not in column_set]
    can_reconstruct = not required_missing
    unsupported_reason = "" if can_reconstruct else "missing required columns: " + ", ".join(required_missing)

    if not can_reconstruct:
        reconstruction_level = "unsupported"
    elif "budget_triggered_by_budget" in column_set and (
        "new_coverage_gain_after_step" in column_set or "newly_covered_viewpoint_ids" in column_set
    ):
        reconstruction_level = "budget_and_coverage_proxy"
    elif "budget_triggered_by_budget" in column_set:
        reconstruction_level = "budget_proxy_without_coverage"
    else:
        reconstruction_level = "basic_assignment_proxy"

    return {
        "available_columns": list(columns),
        "required_columns_present": required_present,
        "required_columns_missing": required_missing,
        "optional_columns_present": optional_present,
        "optional_columns_missing": optional_missing,
        "can_reconstruct_lifecycle": can_reconstruct,
        "unsupported_reason": unsupported_reason,
        "selection_column": selection_column,
        "reconstruction_level": reconstruction_level,
    }


def _sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, int]:
    return (
        _int(row.get("episode")),
        _int(row.get("env_id")),
        _int(row.get("step")),
        _int(row.get("robot_id")),
        _int(row.get("_source_row_index")),
    )


def _robot_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("robot_id")))


def _env_key(row: dict[str, Any]) -> tuple[int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")))


def _row_id(row: dict[str, Any]) -> int:
    return _int(row.get("_source_row_index"), -1)


def _target_id(row: dict[str, Any], selection_column: str | None) -> int:
    if selection_column is None:
        return -1
    if _bool(row.get("is_noop")):
        return -1
    return _int(row.get(selection_column), -1)


def _newly_covered_ids(row: dict[str, Any]) -> list[int]:
    try:
        values = _json_list(row.get("newly_covered_viewpoint_ids"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    result: list[int] = []
    for value in values:
        parsed = _int(value, -1)
        if parsed >= 0:
            result.append(parsed)
    return result


def _row_covers_target(row: dict[str, Any], target_id: int, selection_column: str | None) -> bool:
    if target_id < 0:
        return False
    if target_id in _newly_covered_ids(row):
        return True
    if _bool(row.get("new_coverage_gain_after_step")) and _target_id(row, selection_column) == target_id:
        return True
    return False


def _initial_lifecycle_fields() -> dict[str, Any]:
    return {
        "lifecycle_reconstructed_state": "unknown_or_insufficient_columns",
        "lifecycle_state_reason": "",
        "active_assignment_age_steps": "",
        "attempt_segment_id": "",
        "attempt_segment_step": "",
        "failed_pair_memory_start_step": "",
        "failed_pair_memory_ttl_proxy": "",
        "released_after_budget_trigger": False,
        "returned_to_failed_pair_after_release": False,
        "coverage_gain_before_release": False,
        "coverage_gain_within_20_after_release": False,
        "same_owner_reacquire_step": "",
        "teammate_reacquire_step": "",
        "same_owner_return_delay_steps": "",
        "teammate_reacquire_delay_steps": "",
    }


def _set_state(fields: dict[str, Any], state: str, reason: str) -> None:
    current = str(fields.get("lifecycle_reconstructed_state", "unknown_or_insufficient_columns"))
    if STATE_PRIORITY[state] >= STATE_PRIORITY.get(current, 0):
        fields["lifecycle_reconstructed_state"] = state
        fields["lifecycle_state_reason"] = reason


def _set_failure_context(
    fields: dict[str, Any],
    *,
    failure_step: int,
    row_step: int,
    ttl_proxy: int,
    release_step: int | None,
    coverage_before_release: bool,
    coverage_within_20: bool,
    same_owner_reacquire_step: int | None,
    teammate_reacquire_step: int | None,
) -> None:
    fields["failed_pair_memory_start_step"] = failure_step
    fields["failed_pair_memory_ttl_proxy"] = max(0, ttl_proxy - max(0, row_step - failure_step))
    fields["released_after_budget_trigger"] = release_step is not None and row_step >= release_step
    fields["coverage_gain_before_release"] = coverage_before_release
    fields["coverage_gain_within_20_after_release"] = coverage_within_20
    fields["same_owner_reacquire_step"] = "" if same_owner_reacquire_step is None else same_owner_reacquire_step
    fields["teammate_reacquire_step"] = "" if teammate_reacquire_step is None else teammate_reacquire_step
    if release_step is not None and same_owner_reacquire_step is not None:
        fields["same_owner_return_delay_steps"] = same_owner_reacquire_step - release_step
    if release_step is not None and teammate_reacquire_step is not None:
        fields["teammate_reacquire_delay_steps"] = teammate_reacquire_step - release_step


def _empty_file_summary(source_file: Path, source_file_index: int, inventory: dict[str, Any], num_rows: int) -> dict[str, Any]:
    summary = {
        "source_file_index": source_file_index,
        "source_file": str(source_file),
        "num_rows": num_rows,
        "num_envs": 0,
        "num_robots": 0,
        "num_attempt_segments": 0,
        "num_completed_segments": 0,
        "num_budget_failed_segments": 0,
        "num_released_segments": 0,
        "num_same_owner_returns": 0,
        "num_teammate_reacquires": 0,
        "median_same_owner_return_delay_steps": "",
        "min_same_owner_return_delay_steps": "",
        "max_same_owner_return_delay_steps": "",
        "coverage_gain_after_release_count": 0,
        "coverage_gain_within_20_count": 0,
        "unsupported_file_count": 0 if inventory["can_reconstruct_lifecycle"] else 1,
        "phase9g2_failed_pair_release_memory_signal": "unsupported",
    }
    summary.update(_inventory_for_summary(inventory))
    return summary


def _inventory_for_summary(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "available_columns": _json_text(inventory["available_columns"]),
        "required_columns_present": _json_text(inventory["required_columns_present"]),
        "required_columns_missing": _json_text(inventory["required_columns_missing"]),
        "optional_columns_present": _json_text(inventory["optional_columns_present"]),
        "optional_columns_missing": _json_text(inventory["optional_columns_missing"]),
        "can_reconstruct_lifecycle": bool(inventory["can_reconstruct_lifecycle"]),
        "unsupported_reason": str(inventory["unsupported_reason"]),
        "reconstruction_level": str(inventory["reconstruction_level"]),
    }


def _signal_from_counts(
    *,
    budget_failed_segments: int,
    same_owner_returns: int,
    teammate_reacquires: int,
    coverage_within_20: int,
) -> str:
    if budget_failed_segments <= 0:
        return "no_budget_failure_signal"
    if same_owner_returns > 0 and coverage_within_20 == 0:
        return "supports_phase9g2_failed_pair_release_memory"
    if same_owner_returns > 0:
        return "supports_phase9g2_with_coverage_caveat"
    if teammate_reacquires > 0:
        return "supports_release_ownership_diagnostics_only"
    return "budget_failures_without_reacquire_signal"


def _first_coverage_step_for_target(
    env_rows: list[dict[str, Any]],
    *,
    target_id: int,
    after_step: int,
    selection_column: str | None,
) -> int | None:
    for row in env_rows:
        step = _int(row.get("step"))
        if step <= after_step:
            continue
        if _row_covers_target(row, target_id, selection_column):
            return step
    return None


def _reconstruct_file(
    *,
    source_file: Path,
    source_file_index: int,
    rows: list[dict[str, str]],
    columns: list[str],
    failed_pair_memory_ttl_proxy: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    inventory = _inspect_columns(columns)
    annotated_rows: list[dict[str, Any]] = []
    prepared_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        prepared = dict(row)
        prepared["_source_row_index"] = index
        prepared_rows.append(prepared)
        annotated = {
            "source_file_index": source_file_index,
            "source_file": str(source_file),
            "source_row_index": index,
            **row,
            **_initial_lifecycle_fields(),
        }
        if not inventory["can_reconstruct_lifecycle"]:
            annotated["lifecycle_state_reason"] = inventory["unsupported_reason"]
        annotated_rows.append(annotated)

    row_fields_by_id = {
        int(row["source_row_index"]): row
        for row in annotated_rows
    }

    if not inventory["can_reconstruct_lifecycle"]:
        summary = _empty_file_summary(source_file, source_file_index, inventory, len(rows))
        return annotated_rows, summary, inventory

    selection_column = str(inventory["selection_column"])
    segment_id = 0
    segments: dict[int, dict[str, Any]] = {}
    budget_failure_events: list[dict[str, Any]] = []
    env_rows: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    robot_rows: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)

    for row in prepared_rows:
        env_rows[_env_key(row)].append(row)
        robot_rows[_robot_key(row)].append(row)
    for grouped in env_rows.values():
        grouped.sort(key=_sort_key)
    for grouped in robot_rows.values():
        grouped.sort(key=_sort_key)

    for key, grouped in robot_rows.items():
        current_target: int | None = None
        current_segment_id: int | None = None
        segment_step = 0
        previous_step: int | None = None

        for row in grouped:
            row_id = _row_id(row)
            fields = row_fields_by_id[row_id]
            step = _int(row.get("step"))
            target = _target_id(row, selection_column)
            is_noop = _bool(row.get("is_noop")) or target < 0

            if is_noop:
                current_target = None
                current_segment_id = None
                segment_step = 0
                previous_step = step
                _set_state(fields, "idle_or_noop_proxy", "row is noop or has no valid selected target")
                continue

            starts_new_segment = (
                current_target != target
                or current_segment_id is None
                or previous_step is None
                or step > previous_step + 1
            )
            if starts_new_segment:
                segment_id += 1
                current_segment_id = segment_id
                current_target = target
                segment_step = 1
                segments[current_segment_id] = {
                    "segment_id": current_segment_id,
                    "robot_key": key,
                    "target_id": target,
                    "start_step": step,
                    "end_step": step,
                    "completed": False,
                    "budget_failed": False,
                }
            else:
                segment_step += 1
                assert current_segment_id is not None
                segments[current_segment_id]["end_step"] = step

            fields["attempt_segment_id"] = current_segment_id
            fields["attempt_segment_step"] = segment_step
            fields["active_assignment_age_steps"] = segment_step

            if segment_step == 1:
                _set_state(fields, "assigned_proxy", "first row of contiguous non-noop robot-target segment")
            else:
                _set_state(fields, "executing_proxy", "continued contiguous non-noop robot-target segment")

            completed_now = _bool(row.get("new_coverage_gain_after_step")) or _row_covers_target(
                row, target, selection_column
            )
            covered_before = _bool(row.get("selected_covered_before"))
            budget_failed_now = _bool(row.get("budget_triggered_by_budget"))

            if covered_before:
                segments[current_segment_id]["completed"] = True
                _set_state(fields, "completed_proxy", "selected target was already covered before this row")
            if completed_now:
                segments[current_segment_id]["completed"] = True
                _set_state(fields, "completed_proxy", "selected target produced or matched coverage gain after step")
            if budget_failed_now and not completed_now and not covered_before:
                segments[current_segment_id]["budget_failed"] = True
                budget_failure_events.append(
                    {
                        "event_id": len(budget_failure_events) + 1,
                        "episode": key[0],
                        "env_id": key[1],
                        "robot_id": key[2],
                        "target_id": target,
                        "failure_step": step,
                        "segment_id": current_segment_id,
                        "release_step": None,
                        "same_owner_reacquire_step": None,
                        "teammate_reacquire_step": None,
                        "coverage_step_after_release": None,
                        "coverage_before_release": False,
                        "coverage_within_20": False,
                    }
                )
                _set_state(fields, "failed_budget_proxy", "budget_triggered_by_budget marked this pair as failed proxy")

            previous_step = step

    for event in budget_failure_events:
        event_env_key = (int(event["episode"]), int(event["env_id"]))
        event_robot_key = (int(event["episode"]), int(event["env_id"]), int(event["robot_id"]))
        target_id = int(event["target_id"])
        failure_step = int(event["failure_step"])
        same_robot_rows = [
            row
            for row in robot_rows.get(event_robot_key, [])
            if _int(row.get("step")) > failure_step
        ]

        release_step = None
        for row in same_robot_rows:
            target = _target_id(row, selection_column)
            if target != target_id:
                release_step = _int(row.get("step"))
                break
        event["release_step"] = release_step

        if release_step is not None:
            for row in same_robot_rows:
                step = _int(row.get("step"))
                if step <= release_step:
                    continue
                if _target_id(row, selection_column) == target_id:
                    event["same_owner_reacquire_step"] = step
                    break

            for row in env_rows.get(event_env_key, []):
                step = _int(row.get("step"))
                if step <= release_step or _int(row.get("robot_id")) == int(event["robot_id"]):
                    continue
                if _target_id(row, selection_column) == target_id:
                    event["teammate_reacquire_step"] = step
                    break

            coverage_step = _first_coverage_step_for_target(
                env_rows.get(event_env_key, []),
                target_id=target_id,
                after_step=release_step,
                selection_column=selection_column,
            )
            event["coverage_step_after_release"] = coverage_step
            event["coverage_within_20"] = coverage_step is not None and coverage_step - release_step <= 20

        coverage_step_before_release = None
        if release_step is not None:
            for row in env_rows.get(event_env_key, []):
                step = _int(row.get("step"))
                if failure_step < step < release_step and _row_covers_target(row, target_id, selection_column):
                    coverage_step_before_release = step
                    break
        event["coverage_before_release"] = coverage_step_before_release is not None

        same_owner_reacquire_step = event.get("same_owner_reacquire_step")
        teammate_reacquire_step = event.get("teammate_reacquire_step")

        for row in env_rows.get(event_env_key, []):
            step = _int(row.get("step"))
            if step < failure_step or step > failure_step + failed_pair_memory_ttl_proxy:
                continue
            robot_id = _int(row.get("robot_id"))
            target = _target_id(row, selection_column)
            fields = row_fields_by_id[_row_id(row)]
            related_same_robot = robot_id == int(event["robot_id"])
            related_teammate_reacquire = (
                teammate_reacquire_step is not None
                and step == int(teammate_reacquire_step)
                and robot_id != int(event["robot_id"])
                and target == target_id
            )
            if not related_same_robot and not related_teammate_reacquire:
                continue

            _set_failure_context(
                fields,
                failure_step=failure_step,
                row_step=step,
                ttl_proxy=failed_pair_memory_ttl_proxy,
                release_step=release_step,
                coverage_before_release=bool(event["coverage_before_release"]),
                coverage_within_20=bool(event["coverage_within_20"]),
                same_owner_reacquire_step=(
                    int(same_owner_reacquire_step) if same_owner_reacquire_step is not None else None
                ),
                teammate_reacquire_step=(
                    int(teammate_reacquire_step) if teammate_reacquire_step is not None else None
                ),
            )

            if (
                same_owner_reacquire_step is not None
                and related_same_robot
                and step == int(same_owner_reacquire_step)
                and target == target_id
            ):
                fields["returned_to_failed_pair_after_release"] = True
                _set_state(
                    fields,
                    "returned_after_release_proxy",
                    f"same robot returned to budget-failed target {target_id} after release proxy",
                )
            elif related_teammate_reacquire:
                _set_state(
                    fields,
                    "teammate_reacquired_proxy",
                    f"teammate reacquired budget-failed target {target_id} after release proxy",
                )
            elif release_step is not None and related_same_robot and step >= int(release_step) and target != target_id:
                _set_state(
                    fields,
                    "released_after_failure_proxy",
                    f"same robot released budget-failed target {target_id} and selected another action",
                )

    completed_segments = sum(1 for segment in segments.values() if segment["completed"])
    budget_failed_segments = sum(1 for segment in segments.values() if segment["budget_failed"])
    released_events = [event for event in budget_failure_events if event.get("release_step") is not None]
    same_owner_delays = [
        int(event["same_owner_reacquire_step"]) - int(event["release_step"])
        for event in released_events
        if event.get("same_owner_reacquire_step") is not None
    ]
    teammate_delays = [
        int(event["teammate_reacquire_step"]) - int(event["release_step"])
        for event in released_events
        if event.get("teammate_reacquire_step") is not None
    ]
    coverage_after_release_count = sum(1 for event in released_events if event.get("coverage_step_after_release") is not None)
    coverage_within_20_count = sum(1 for event in released_events if event.get("coverage_within_20"))
    env_ids = {( _int(row.get("episode")), _int(row.get("env_id")) ) for row in prepared_rows}
    robot_ids = {( _int(row.get("episode")), _int(row.get("env_id")), _int(row.get("robot_id")) ) for row in prepared_rows}

    signal = _signal_from_counts(
        budget_failed_segments=budget_failed_segments,
        same_owner_returns=len(same_owner_delays),
        teammate_reacquires=len(teammate_delays),
        coverage_within_20=coverage_within_20_count,
    )
    summary = {
        "source_file_index": source_file_index,
        "source_file": str(source_file),
        "num_rows": len(rows),
        "num_envs": len(env_ids),
        "num_robots": len(robot_ids),
        "num_attempt_segments": len(segments),
        "num_completed_segments": completed_segments,
        "num_budget_failed_segments": budget_failed_segments,
        "num_released_segments": len(released_events),
        "num_same_owner_returns": len(same_owner_delays),
        "num_teammate_reacquires": len(teammate_delays),
        "median_same_owner_return_delay_steps": (
            _format_number(float(statistics.median(same_owner_delays))) if same_owner_delays else ""
        ),
        "min_same_owner_return_delay_steps": min(same_owner_delays) if same_owner_delays else "",
        "max_same_owner_return_delay_steps": max(same_owner_delays) if same_owner_delays else "",
        "coverage_gain_after_release_count": coverage_after_release_count,
        "coverage_gain_within_20_count": coverage_within_20_count,
        "unsupported_file_count": 0,
        "phase9g2_failed_pair_release_memory_signal": signal,
    }
    summary.update(_inventory_for_summary(inventory))
    return annotated_rows, summary, inventory


def _aggregate_summary(file_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_fields = [
        "num_rows",
        "num_attempt_segments",
        "num_completed_segments",
        "num_budget_failed_segments",
        "num_released_segments",
        "num_same_owner_returns",
        "num_teammate_reacquires",
        "coverage_gain_after_release_count",
        "coverage_gain_within_20_count",
        "unsupported_file_count",
    ]
    aggregate: dict[str, Any] = {"num_files": len(file_summaries)}
    for field in numeric_fields:
        aggregate[field] = sum(_int(summary.get(field)) for summary in file_summaries)

    envs: set[tuple[int, int, int]] = set()
    robots: set[tuple[int, int, int, int]] = set()
    same_owner_delays: list[int] = []
    for summary in file_summaries:
        file_index = _int(summary.get("source_file_index"))
        env_count = _int(summary.get("num_envs"))
        robot_count = _int(summary.get("num_robots"))
        for env_offset in range(env_count):
            envs.add((file_index, env_offset, 0))
        for robot_offset in range(robot_count):
            robots.add((file_index, robot_offset, 0, 0))
        median_delay = summary.get("median_same_owner_return_delay_steps")
        min_delay = summary.get("min_same_owner_return_delay_steps")
        max_delay = summary.get("max_same_owner_return_delay_steps")
        if str(min_delay) != "" and str(max_delay) != "":
            same_owner_delays.extend([_int(min_delay), _int(max_delay)])
        elif str(median_delay) != "":
            same_owner_delays.append(_int(median_delay))

    aggregate["num_envs"] = sum(_int(summary.get("num_envs")) for summary in file_summaries)
    aggregate["num_robots"] = sum(_int(summary.get("num_robots")) for summary in file_summaries)
    if same_owner_delays:
        aggregate["median_same_owner_return_delay_steps"] = _format_number(float(statistics.median(same_owner_delays)))
        aggregate["min_same_owner_return_delay_steps"] = min(same_owner_delays)
        aggregate["max_same_owner_return_delay_steps"] = max(same_owner_delays)
    else:
        aggregate["median_same_owner_return_delay_steps"] = ""
        aggregate["min_same_owner_return_delay_steps"] = ""
        aggregate["max_same_owner_return_delay_steps"] = ""

    aggregate["phase9g2_failed_pair_release_memory_signal"] = _signal_from_counts(
        budget_failed_segments=_int(aggregate["num_budget_failed_segments"]),
        same_owner_returns=_int(aggregate["num_same_owner_returns"]),
        teammate_reacquires=_int(aggregate["num_teammate_reacquires"]),
        coverage_within_20=_int(aggregate["coverage_gain_within_20_count"]),
    )
    return aggregate


def _combined_row_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    fields: list[str] = []
    for name in ROW_PREFIX_FIELDS:
        if name not in seen:
            fields.append(name)
            seen.add(name)
    for row in rows:
        for name in row.keys():
            if name.startswith("_") or name in seen or name in LIFECYCLE_FIELDS or name in ROW_PREFIX_FIELDS:
                continue
            fields.append(name)
            seen.add(name)
    for name in LIFECYCLE_FIELDS:
        if name not in seen:
            fields.append(name)
            seen.add(name)
    return fields


def analyze_histories(
    histories: list[Path],
    *,
    output_dir: Path,
    failed_pair_memory_ttl_proxy: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    file_summaries: list[dict[str, Any]] = []
    inventories: list[dict[str, Any]] = []

    for source_file_index, history in enumerate(histories):
        rows, columns = _read_csv(history)
        reconstructed_rows, file_summary, inventory = _reconstruct_file(
            source_file=history,
            source_file_index=source_file_index,
            rows=rows,
            columns=columns,
            failed_pair_memory_ttl_proxy=failed_pair_memory_ttl_proxy,
        )
        all_rows.extend(reconstructed_rows)
        file_summaries.append(file_summary)
        inventories.append(
            {
                "source_file_index": source_file_index,
                "source_file": str(history),
                **inventory,
            }
        )

    aggregate = _aggregate_summary(file_summaries)
    row_path = output_dir / "phase9g1_lifecycle_reconstructed_rows.csv"
    file_summary_path = output_dir / "phase9g1_lifecycle_file_summary.csv"
    aggregate_summary_path = output_dir / "phase9g1_lifecycle_summary.json"
    inventory_path = output_dir / "phase9g1_lifecycle_column_inventory.json"

    _write_csv(row_path, all_rows, _combined_row_fieldnames(all_rows))
    _write_csv(file_summary_path, file_summaries, FILE_SUMMARY_FIELDS)
    _write_json(
        aggregate_summary_path,
        {
            "aggregate_summary": aggregate,
            "file_summaries": file_summaries,
            "output_files": {
                "row_level_csv": str(row_path),
                "file_summary_csv": str(file_summary_path),
                "summary_json": str(aggregate_summary_path),
                "column_inventory_json": str(inventory_path),
            },
        },
    )
    _write_json(inventory_path, {"files": inventories})

    return {
        "aggregate_summary": aggregate,
        "file_summaries": file_summaries,
        "output_files": {
            "row_level_csv": str(row_path),
            "file_summary_csv": str(file_summary_path),
            "summary_json": str(aggregate_summary_path),
            "column_inventory_json": str(inventory_path),
        },
    }


def _self_test_rows_full() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(step: int, robot_id: int, target: int, **overrides: Any) -> None:
        is_noop = target < 0
        row = {
            "method": "phase9g1_self_test",
            "episode": 0,
            "step": step,
            "env_id": 0,
            "robot_id": robot_id,
            "robot_name": f"robot_{robot_id}",
            "selected_viewpoint_id": target,
            "assigned_viewpoint_id": target,
            "is_noop": is_noop,
            "selected_available": not is_noop,
            "selected_feasible": not is_noop,
            "selected_covered_before": False,
            "new_coverage_gain_after_step": False,
            "coverage_ratio_after_step": 0.0,
            "newly_covered_viewpoint_ids": "[]",
            "same_target_streak": 1,
            "cooldown_active_for_selected_pair": False,
            "cooldown_remaining_for_selected_pair": 0,
            "cooldown_triggered_after_step": False,
            "cooldown_suppressed_available_count_for_robot": 0,
            "failed_attempt_count_for_selected_pair": 0,
            "cooldown_trigger_mode": "budget_and_streak",
            "budget_attempt_steps_for_selected_pair": 0,
            "budget_steps_for_selected_pair": 0,
            "budget_expected_steps_for_selected_pair": 0,
            "budget_ratio_for_selected_pair": 0.0,
            "budget_triggered_after_step": False,
            "budget_triggered_by_budget": False,
        }
        row.update(overrides)
        rows.append(row)

    # Successful completion.
    add(0, 0, 10, same_target_streak=1)
    add(
        1,
        0,
        10,
        same_target_streak=2,
        new_coverage_gain_after_step=True,
        newly_covered_viewpoint_ids="[10]",
        coverage_ratio_after_step=0.1,
    )
    # Noop row.
    add(2, 0, -1)
    # Covered-before row.
    add(3, 0, 10, selected_covered_before=True)

    # Budget failure, release, same-owner return.
    add(4, 1, 20, same_target_streak=1, budget_attempt_steps_for_selected_pair=1, budget_steps_for_selected_pair=3)
    add(5, 1, 20, same_target_streak=2, budget_attempt_steps_for_selected_pair=2, budget_steps_for_selected_pair=3)
    add(
        6,
        1,
        20,
        same_target_streak=3,
        cooldown_triggered_after_step=True,
        budget_triggered_after_step=True,
        budget_triggered_by_budget=True,
        budget_attempt_steps_for_selected_pair=3,
        budget_steps_for_selected_pair=3,
        budget_ratio_for_selected_pair=1.0,
    )
    add(7, 1, 21)
    add(8, 1, 21)
    add(12, 1, 20)

    # Overlapping trigger window on another robot and teammate reacquire of target 30.
    add(5, 2, 30, same_target_streak=1, budget_attempt_steps_for_selected_pair=1, budget_steps_for_selected_pair=2)
    add(
        6,
        2,
        30,
        same_target_streak=2,
        cooldown_triggered_after_step=True,
        budget_triggered_after_step=True,
        budget_triggered_by_budget=True,
        budget_attempt_steps_for_selected_pair=2,
        budget_steps_for_selected_pair=2,
        budget_ratio_for_selected_pair=1.0,
    )
    add(7, 2, 31)
    add(9, 1, 30)
    add(
        10,
        1,
        30,
        new_coverage_gain_after_step=True,
        newly_covered_viewpoint_ids="[30]",
        coverage_ratio_after_step=0.2,
    )
    return rows


def _self_test_rows_missing_optional() -> list[dict[str, Any]]:
    return [
        {
            "episode": 1,
            "step": 0,
            "env_id": 0,
            "robot_id": 0,
            "assigned_viewpoint_id": 5,
            "is_noop": False,
        },
        {
            "episode": 1,
            "step": 1,
            "env_id": 0,
            "robot_id": 0,
            "assigned_viewpoint_id": -1,
            "is_noop": True,
        },
    ]


def _write_fixture(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    _write_csv(path, rows, fieldnames)


def run_self_test(output_dir: Path, failed_pair_memory_ttl_proxy: int) -> dict[str, Any]:
    fixture_dir = output_dir / "self_test_inputs"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    full_fixture = fixture_dir / "phase9g1_full_fixture_assignment_history.csv"
    missing_optional_fixture = fixture_dir / "phase9g1_missing_optional_fixture_assignment_history.csv"
    _write_fixture(full_fixture, _self_test_rows_full())
    _write_fixture(missing_optional_fixture, _self_test_rows_missing_optional())
    result = analyze_histories(
        [full_fixture, missing_optional_fixture],
        output_dir=output_dir,
        failed_pair_memory_ttl_proxy=failed_pair_memory_ttl_proxy,
    )
    aggregate = result["aggregate_summary"]
    if _int(aggregate["num_budget_failed_segments"]) < 2:
        raise AssertionError("self-test expected at least two budget-failed segments")
    if _int(aggregate["num_same_owner_returns"]) < 1:
        raise AssertionError("self-test expected a same-owner return")
    if _int(aggregate["num_teammate_reacquires"]) < 1:
        raise AssertionError("self-test expected a teammate reacquire")
    if _int(aggregate["num_completed_segments"]) < 2:
        raise AssertionError("self-test expected completed segments")
    if _int(aggregate["unsupported_file_count"]) != 0:
        raise AssertionError("self-test fixtures should be reconstructable despite missing optional columns")
    result["self_test_inputs"] = {
        "full_fixture": str(full_fixture),
        "missing_optional_fixture": str(missing_optional_fixture),
    }
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("histories", nargs="*", type=Path, help="Existing assignment_history.csv files to analyze.")
    parser.add_argument(
        "--history",
        action="append",
        nargs="+",
        type=Path,
        default=[],
        help="Additional existing assignment_history.csv files to analyze.",
    )
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--failed_pair_memory_ttl_proxy", type=int, default=20)
    parser.add_argument("--self-test", action="store_true", help="Generate and analyze tiny fake-history fixtures.")
    return parser.parse_args()


def _flatten_histories(args: argparse.Namespace) -> list[Path]:
    histories = list(args.histories)
    for group in args.history:
        histories.extend(group)
    return histories


def _print_summary(result: dict[str, Any]) -> None:
    aggregate = result["aggregate_summary"]
    outputs = result["output_files"]
    print(
        "[phase9g1] analyzed "
        f"{aggregate['num_files']} file(s), rows={aggregate['num_rows']}, "
        f"unsupported={aggregate['unsupported_file_count']}, "
        f"budget_failed_segments={aggregate['num_budget_failed_segments']}, "
        f"released_segments={aggregate['num_released_segments']}, "
        f"same_owner_returns={aggregate['num_same_owner_returns']}, "
        f"teammate_reacquires={aggregate['num_teammate_reacquires']}, "
        f"coverage_within_20={aggregate['coverage_gain_within_20_count']}"
    )
    print(f"[phase9g1] phase9g2_signal={aggregate['phase9g2_failed_pair_release_memory_signal']}")
    print(f"[phase9g1] row_level_csv={outputs['row_level_csv']}")
    print(f"[phase9g1] file_summary_csv={outputs['file_summary_csv']}")
    print(f"[phase9g1] summary_json={outputs['summary_json']}")
    if "self_test_inputs" in result:
        print(f"[phase9g1] self_test_full_fixture={result['self_test_inputs']['full_fixture']}")
        print(
            "[phase9g1] self_test_missing_optional_fixture="
            f"{result['self_test_inputs']['missing_optional_fixture']}"
        )


def main() -> None:
    args = _parse_args()
    if args.failed_pair_memory_ttl_proxy < 1:
        raise ValueError("--failed_pair_memory_ttl_proxy must be positive")

    if args.self_test:
        result = run_self_test(args.output_dir, args.failed_pair_memory_ttl_proxy)
    else:
        histories = _flatten_histories(args)
        if not histories:
            raise SystemExit("Provide one or more assignment_history.csv files, or use --self-test.")
        missing = [str(path) for path in histories if not path.exists()]
        if missing:
            raise FileNotFoundError("Missing input history files: " + ", ".join(missing))
        result = analyze_histories(
            histories,
            output_dir=args.output_dir,
            failed_pair_memory_ttl_proxy=args.failed_pair_memory_ttl_proxy,
        )

    _print_summary(result)


if __name__ == "__main__":
    main()
