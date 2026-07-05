"""Phase 9F-5 redirect-guardrail playback validation.

This script is CSV-only. It validates the guardrail-enabled playback history,
summarizes guardrail activation/suppression diagnostics, and compares direct
trigger-window attribution against the Phase 9F-2C disabled reference.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_phase9f2c_trigger_windows import (  # noqa: E402
    ATTRIBUTION_FIELDS,
    REQUIRED_NEW_COLUMNS,
    _analyze_trigger_windows,
    _bool,
    _first_non_noop_after,
    _float,
    _int,
    _json_list,
    _read_csv,
    _robot_key,
    _target_id,
    _validate_history,
    _write_csv,
    _write_json,
)


DEFAULT_ENABLED_HISTORY = Path(
    "results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv"
)
DEFAULT_REFERENCE_HISTORY = Path(
    "results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv"
)
DEFAULT_OUTPUT_DIR = Path("results/assignment_diagnostics/phase9f5_redirect_guardrail_validation")

GUARDRAIL_COLUMNS = [
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

GUARDRAIL_COUNT_FIELDS = [
    "claimed_target_redirect_suppressed_count",
    "spacing_redirect_suppressed_count",
    "redirect_guardrail_overmask_non_noop_count",
]

GUARDRAIL_JSON_LIST_FIELDS = [
    "redirect_guardrail_claimed_target_robot_ids",
    "redirect_guardrail_nearby_target_robot_ids",
]

PHASE9F5_ATTRIBUTION_FIELDS = ATTRIBUTION_FIELDS + [
    "next_redirect_guardrail_active_for_robot",
    "next_redirect_guardrail_context",
    "next_claimed_target_redirect_suppressed_count",
    "next_spacing_redirect_suppressed_count",
    "next_redirect_guardrail_overmask_non_noop_count",
    "next_redirect_guardrail_only_noop_remaining",
    "next_redirect_guardrail_fail_open_reason",
    "next_redirect_guardrail_threshold",
    "next_redirect_guardrail_claimed_target_robot_ids",
    "next_redirect_guardrail_nearby_target_robot_ids",
]


def _read_columns(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or [])


def _metric_rate(count: int | float, total: int) -> float:
    if total <= 0:
        return math.nan
    return float(count) / float(total)


def _json_list_or_empty(value: Any) -> list[Any]:
    if value is None or str(value).strip() == "":
        return []
    return _json_list(value)


def _validate_enabled_history(rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    base_summary = _validate_history(rows, columns)
    column_set = set(columns)
    missing_guardrail = [name for name in GUARDRAIL_COLUMNS if name not in column_set]

    numeric_errors: list[str] = []
    nonnegative_errors: list[str] = []
    threshold_errors: list[str] = []
    json_errors: list[str] = []
    inactive_default_errors: list[str] = []

    active_rows = 0
    for row_index, row in enumerate(rows, start=2):
        active = _bool(row.get("redirect_guardrail_active_for_robot"))
        if active:
            active_rows += 1

        count_sum = 0
        for field in GUARDRAIL_COUNT_FIELDS:
            value = _float(row.get(field))
            if not math.isfinite(value):
                numeric_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
                continue
            if value < 0:
                nonnegative_errors.append(f"line {row_index}: {field}={row.get(field)!r}")
            count_sum += int(value)

        threshold = _float(row.get("redirect_guardrail_threshold"), 0.0)
        if active and (not math.isfinite(threshold) or threshold <= 0.0):
            threshold_errors.append(
                f"line {row_index}: active row has redirect_guardrail_threshold={row.get('redirect_guardrail_threshold')!r}"
            )

        list_values: dict[str, list[Any]] = {}
        for field in GUARDRAIL_JSON_LIST_FIELDS:
            try:
                list_values[field] = _json_list_or_empty(row.get(field))
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                json_errors.append(f"line {row_index}: {field}: {exc}")

        if not active:
            context = str(row.get("redirect_guardrail_context", "") or "").strip()
            fail_reason = str(row.get("redirect_guardrail_fail_open_reason", "") or "").strip()
            only_noop = _bool(row.get("redirect_guardrail_only_noop_remaining"))
            lists_nonempty = any(list_values.get(field) for field in GUARDRAIL_JSON_LIST_FIELDS)
            if count_sum != 0 or context or fail_reason or only_noop or lists_nonempty:
                inactive_default_errors.append(f"line {row_index}: inactive guardrail row has non-default diagnostics")

    guardrail_summary = {
        "guardrail_columns_exist": not missing_guardrail,
        "missing_guardrail_columns": missing_guardrail,
        "guardrail_active_row_count": active_rows,
        "guardrail_numeric_validation_passed": not numeric_errors,
        "guardrail_numeric_errors_sample": numeric_errors[:10],
        "guardrail_count_nonnegative_validation_passed": not nonnegative_errors,
        "guardrail_count_nonnegative_errors_sample": nonnegative_errors[:10],
        "guardrail_active_threshold_positive_validation_passed": not threshold_errors,
        "guardrail_active_threshold_errors_sample": threshold_errors[:10],
        "guardrail_json_list_parse_validation_passed": not json_errors,
        "guardrail_json_errors_sample": json_errors[:10],
        "guardrail_inactive_default_validation_passed": not inactive_default_errors,
        "guardrail_inactive_default_errors_sample": inactive_default_errors[:10],
        "noop_when_available_reported": "noop_when_available" in column_set,
        "available_actions_shape_logged": False,
        "available_actions_shape_validation": "not_logged",
    }
    guardrail_summary["validation_passed"] = bool(
        base_summary["validation_passed"]
        and guardrail_summary["guardrail_columns_exist"]
        and guardrail_summary["guardrail_numeric_validation_passed"]
        and guardrail_summary["guardrail_count_nonnegative_validation_passed"]
        and guardrail_summary["guardrail_active_threshold_positive_validation_passed"]
        and guardrail_summary["guardrail_json_list_parse_validation_passed"]
        and guardrail_summary["guardrail_inactive_default_validation_passed"]
        and guardrail_summary["noop_when_available_reported"]
    )
    return {**base_summary, **guardrail_summary}


def _rows_by_robot(rows: list[dict[str, str]]) -> dict[tuple[int, int, int], list[dict[str, str]]]:
    grouped: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_robot_key(row)].append(row)
    for robot_rows in grouped.values():
        robot_rows.sort(key=lambda item: _int(item.get("step")))
    return grouped


def _trigger_next_rows(rows: list[dict[str, str]]) -> list[tuple[dict[str, str], dict[str, str] | None]]:
    grouped = _rows_by_robot(rows)
    pairs: list[tuple[dict[str, str], dict[str, str] | None]] = []
    for trigger in rows:
        if not _bool(trigger.get("budget_triggered_by_budget")):
            continue
        pairs.append(
            (
                trigger,
                _first_non_noop_after(
                    grouped,
                    episode=_int(trigger.get("episode")),
                    env_id=_int(trigger.get("env_id")),
                    robot_id=_int(trigger.get("robot_id")),
                    step=_int(trigger.get("step")),
                ),
            )
        )
    return pairs


def _decorate_attribution_rows(
    rows: list[dict[str, str]],
    attribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trigger_next_by_key: dict[tuple[int, int, int, int], dict[str, str] | None] = {}
    for trigger, next_row in _trigger_next_rows(rows):
        key = (
            _int(trigger.get("episode")),
            _int(trigger.get("env_id")),
            _int(trigger.get("step")),
            _int(trigger.get("robot_id")),
        )
        trigger_next_by_key[key] = next_row

    decorated: list[dict[str, Any]] = []
    for record in attribution_rows:
        key = (
            _int(record.get("episode")),
            _int(record.get("env_id")),
            _int(record.get("trigger_step")),
            _int(record.get("trigger_robot_id")),
        )
        next_row = trigger_next_by_key.get(key)
        decorated_row = dict(record)
        if next_row is None:
            decorated_row.update(
                {
                    "next_redirect_guardrail_active_for_robot": "",
                    "next_redirect_guardrail_context": "",
                    "next_claimed_target_redirect_suppressed_count": "",
                    "next_spacing_redirect_suppressed_count": "",
                    "next_redirect_guardrail_overmask_non_noop_count": "",
                    "next_redirect_guardrail_only_noop_remaining": "",
                    "next_redirect_guardrail_fail_open_reason": "",
                    "next_redirect_guardrail_threshold": "",
                    "next_redirect_guardrail_claimed_target_robot_ids": "",
                    "next_redirect_guardrail_nearby_target_robot_ids": "",
                }
            )
        else:
            decorated_row.update(
                {
                    "next_redirect_guardrail_active_for_robot": _bool(
                        next_row.get("redirect_guardrail_active_for_robot")
                    ),
                    "next_redirect_guardrail_context": next_row.get("redirect_guardrail_context", ""),
                    "next_claimed_target_redirect_suppressed_count": _int(
                        next_row.get("claimed_target_redirect_suppressed_count")
                    ),
                    "next_spacing_redirect_suppressed_count": _int(
                        next_row.get("spacing_redirect_suppressed_count")
                    ),
                    "next_redirect_guardrail_overmask_non_noop_count": _int(
                        next_row.get("redirect_guardrail_overmask_non_noop_count")
                    ),
                    "next_redirect_guardrail_only_noop_remaining": _bool(
                        next_row.get("redirect_guardrail_only_noop_remaining")
                    ),
                    "next_redirect_guardrail_fail_open_reason": next_row.get(
                        "redirect_guardrail_fail_open_reason",
                        "",
                    ),
                    "next_redirect_guardrail_threshold": _float(next_row.get("redirect_guardrail_threshold"), 0.0),
                    "next_redirect_guardrail_claimed_target_robot_ids": next_row.get(
                        "redirect_guardrail_claimed_target_robot_ids",
                        "[]",
                    ),
                    "next_redirect_guardrail_nearby_target_robot_ids": next_row.get(
                        "redirect_guardrail_nearby_target_robot_ids",
                        "[]",
                    ),
                }
            )
        decorated.append(decorated_row)
    return decorated


def _guardrail_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    active_rows = [row for row in rows if _bool(row.get("redirect_guardrail_active_for_robot"))]
    trigger_next = _trigger_next_rows(rows)
    active_trigger_count = sum(
        1 for _, next_row in trigger_next if next_row is not None and _bool(next_row.get("redirect_guardrail_active_for_robot"))
    )
    claimed_total = sum(_int(row.get("claimed_target_redirect_suppressed_count")) for row in rows)
    spacing_total = sum(_int(row.get("spacing_redirect_suppressed_count")) for row in rows)
    overmask_total = sum(_int(row.get("redirect_guardrail_overmask_non_noop_count")) for row in rows)
    fail_open_rows = [
        row for row in rows if str(row.get("redirect_guardrail_fail_open_reason", "") or "").strip()
    ]
    only_noop_rows = [row for row in rows if _bool(row.get("redirect_guardrail_only_noop_remaining"))]
    active_rows_with_suppression = [
        row
        for row in active_rows
        if (
            _int(row.get("claimed_target_redirect_suppressed_count"))
            + _int(row.get("spacing_redirect_suppressed_count"))
        )
        > 0
    ]
    active_thresholds = [
        _float(row.get("redirect_guardrail_threshold"))
        for row in active_rows
        if math.isfinite(_float(row.get("redirect_guardrail_threshold")))
    ]
    return {
        "redirect_guardrail_active_row_count": len(active_rows),
        "guardrail_active_trigger_count": active_trigger_count,
        "claimed_target_suppression_total": claimed_total,
        "spacing_suppression_total": spacing_total,
        "fail_open_count": len(fail_open_rows),
        "fail_open_reasons": dict(Counter(row.get("redirect_guardrail_fail_open_reason", "") for row in fail_open_rows)),
        "overmask_count": overmask_total,
        "only_noop_remaining_count": len(only_noop_rows),
        "active_rows_with_suppression_count": len(active_rows_with_suppression),
        "active_threshold_min": min(active_thresholds) if active_thresholds else math.nan,
        "active_threshold_max": max(active_thresholds) if active_thresholds else math.nan,
    }


def _coverage_noop_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    step_rows: dict[tuple[int, int, int], dict[str, str]] = {}
    for row in rows:
        key = (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("step")))
        step_rows.setdefault(key, row)
    ordered_step_rows = [step_rows[key] for key in sorted(step_rows)]
    coverage_values = [
        _float(row.get("coverage_ratio_after_step"))
        for row in ordered_step_rows
        if math.isfinite(_float(row.get("coverage_ratio_after_step")))
    ]
    final_coverage = coverage_values[-1] if coverage_values else math.nan
    coverage_auc = sum(coverage_values) / len(coverage_values) if coverage_values else math.nan
    noop_action_count = sum(1 for row in rows if _target_id(row) < 0)
    noop_when_available = sum(1 for row in rows if _bool(row.get("noop_when_available")))
    row_count = len(rows)
    return {
        "final_coverage_ratio": final_coverage,
        "coverage_auc": coverage_auc,
        "noop_when_available": noop_when_available,
        "noop_action_count": noop_action_count,
        "noop_when_non_noop_available_count": noop_when_available,
        "noop_when_available_rate": _metric_rate(noop_when_available, row_count),
        "noop_action_rate": _metric_rate(noop_action_count, row_count),
    }


def _summarize_trigger_rates(summary: dict[str, Any]) -> dict[str, Any]:
    trigger_count = _int(summary.get("trigger_count"))
    metrics = {
        "budget_trigger_row_count": trigger_count,
        "trigger_pairs": summary.get("trigger_pairs", {}),
    }
    for field in [
        "next_exact_duplicate_direct_count",
        "next_nearby_selected_target_direct_count",
        "next_inter_robot_overlap_direct_count",
        "next_path_crossing_direct_count",
        "next_path_near_miss_direct_count",
        "coverage_gain_within_20_count",
        "return_to_triggered_pair_after_cooldown_count",
    ]:
        value = _int(summary.get(field))
        metrics[field] = value
        metrics[f"{field}_rate"] = _metric_rate(value, trigger_count)
    return metrics


def _comparison_rows(
    enabled_trigger: dict[str, Any],
    reference_trigger: dict[str, Any],
    enabled_coverage: dict[str, Any],
    reference_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in [
        "next_exact_duplicate_direct_count_rate",
        "next_nearby_selected_target_direct_count_rate",
        "next_inter_robot_overlap_direct_count_rate",
        "next_path_crossing_direct_count_rate",
        "next_path_near_miss_direct_count_rate",
        "coverage_gain_within_20_count_rate",
        "return_to_triggered_pair_after_cooldown_count_rate",
    ]:
        enabled = _float(enabled_trigger.get(field))
        reference = _float(reference_trigger.get(field))
        rows.append(
            {
                "metric": field,
                "enabled": enabled,
                "reference": reference,
                "delta_enabled_minus_reference": enabled - reference
                if math.isfinite(enabled) and math.isfinite(reference)
                else math.nan,
            }
        )
    for field in [
        "final_coverage_ratio",
        "coverage_auc",
        "noop_when_available_rate",
        "noop_action_rate",
    ]:
        enabled = _float(enabled_coverage.get(field))
        reference = _float(reference_coverage.get(field))
        rows.append(
            {
                "metric": field,
                "enabled": enabled,
                "reference": reference,
                "delta_enabled_minus_reference": enabled - reference
                if math.isfinite(enabled) and math.isfinite(reference)
                else math.nan,
            }
        )
    return rows


def _classify(
    *,
    schema_passed: bool,
    trigger_count: int,
    enabled_trigger: dict[str, Any],
    reference_trigger: dict[str, Any],
    enabled_coverage: dict[str, Any],
    reference_coverage: dict[str, Any],
) -> str:
    if not schema_passed or trigger_count <= 0:
        return "VALIDATION-INCOMPLETE"

    enabled_exact = _float(enabled_trigger.get("next_exact_duplicate_direct_count_rate"))
    reference_exact = _float(reference_trigger.get("next_exact_duplicate_direct_count_rate"))
    enabled_nearby = _float(enabled_trigger.get("next_nearby_selected_target_direct_count_rate"))
    reference_nearby = _float(reference_trigger.get("next_nearby_selected_target_direct_count_rate"))
    conflict_reduced = (enabled_exact + enabled_nearby) < (reference_exact + reference_nearby)

    final_coverage_delta = _float(enabled_coverage.get("final_coverage_ratio")) - _float(
        reference_coverage.get("final_coverage_ratio")
    )
    coverage_auc_delta = _float(enabled_coverage.get("coverage_auc")) - _float(reference_coverage.get("coverage_auc"))
    noop_delta = _float(enabled_coverage.get("noop_when_available_rate")) - _float(
        reference_coverage.get("noop_when_available_rate")
    )
    coverage_stable = final_coverage_delta >= -0.01 and coverage_auc_delta >= -0.01
    noop_stable = noop_delta <= 0.01

    if conflict_reduced and coverage_stable and noop_stable:
        return "GUARDRAIL-P"
    if conflict_reduced:
        return "GUARDRAIL-MIXED"
    return "GUARDRAIL-N"


def _history_bundle(path: Path, *, window_steps: int, cooldown_duration: int, require_guardrail: bool) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = _read_csv(path)
    columns = _read_columns(path)
    schema = _validate_enabled_history(rows, columns) if require_guardrail else _validate_history(rows, columns)
    attribution_rows, attribution_summary = _analyze_trigger_windows(
        rows,
        window_steps=window_steps,
        cooldown_duration=cooldown_duration,
    )
    return {
        "path": str(path),
        "rows": rows,
        "columns": columns,
        "schema": schema,
        "attribution_rows": attribution_rows,
        "attribution_summary": attribution_summary,
        "trigger_metrics": _summarize_trigger_rates(attribution_summary),
        "coverage_noop_metrics": _coverage_noop_metrics(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enabled_history", type=Path, default=DEFAULT_ENABLED_HISTORY)
    parser.add_argument("--reference_history", type=Path, default=DEFAULT_REFERENCE_HISTORY)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--window_steps", type=int, default=20)
    parser.add_argument("--cooldown_duration", type=int, default=5)
    args = parser.parse_args()

    enabled = _history_bundle(
        args.enabled_history,
        window_steps=args.window_steps,
        cooldown_duration=args.cooldown_duration,
        require_guardrail=True,
    )
    reference = _history_bundle(
        args.reference_history,
        window_steps=args.window_steps,
        cooldown_duration=args.cooldown_duration,
        require_guardrail=False,
    )
    guardrail = _guardrail_metrics(enabled["rows"])
    enabled_attribution_rows = _decorate_attribution_rows(enabled["rows"], enabled["attribution_rows"])
    comparison = _comparison_rows(
        enabled["trigger_metrics"],
        reference["trigger_metrics"],
        enabled["coverage_noop_metrics"],
        reference["coverage_noop_metrics"],
    )
    classification = _classify(
        schema_passed=bool(enabled["schema"]["validation_passed"]),
        trigger_count=_int(enabled["trigger_metrics"].get("budget_trigger_row_count")),
        enabled_trigger=enabled["trigger_metrics"],
        reference_trigger=reference["trigger_metrics"],
        enabled_coverage=enabled["coverage_noop_metrics"],
        reference_coverage=reference["coverage_noop_metrics"],
    )

    summary = {
        "enabled_history": str(args.enabled_history),
        "reference_history": str(args.reference_history),
        "window_steps": args.window_steps,
        "cooldown_duration": args.cooldown_duration,
        "enabled_schema": enabled["schema"],
        "reference_schema": reference["schema"],
        "guardrail": guardrail,
        "enabled_trigger_metrics": enabled["trigger_metrics"],
        "reference_trigger_metrics": reference["trigger_metrics"],
        "enabled_coverage_noop_metrics": enabled["coverage_noop_metrics"],
        "reference_coverage_noop_metrics": reference["coverage_noop_metrics"],
        "comparison_rows": comparison,
        "classification": classification,
        "reference_trigger_count_differs": enabled["trigger_metrics"]["budget_trigger_row_count"]
        != reference["trigger_metrics"]["budget_trigger_row_count"],
    }

    output_dir = args.output_dir
    _write_json(output_dir / "phase9f5_schema_validation_summary.json", enabled["schema"])
    _write_csv(
        output_dir / "phase9f5_trigger_window_attribution.csv",
        enabled_attribution_rows,
        PHASE9F5_ATTRIBUTION_FIELDS,
    )
    _write_csv(
        output_dir / "phase9f5_reference_comparison.csv",
        comparison,
        ["metric", "enabled", "reference", "delta_enabled_minus_reference"],
    )
    _write_json(output_dir / "phase9f5_redirect_guardrail_validation_summary.json", summary)

    print(
        json.dumps(
            {
                "enabled_history": str(args.enabled_history),
                "reference_history": str(args.reference_history),
                "rows": enabled["schema"]["row_count"],
                "columns": enabled["schema"]["column_count"],
                "validation_passed": enabled["schema"]["validation_passed"],
                "budget_trigger_row_count": enabled["trigger_metrics"]["budget_trigger_row_count"],
                "guardrail": guardrail,
                "classification": classification,
                "outputs": {
                    "schema": str(output_dir / "phase9f5_schema_validation_summary.json"),
                    "attribution_csv": str(output_dir / "phase9f5_trigger_window_attribution.csv"),
                    "comparison_csv": str(output_dir / "phase9f5_reference_comparison.csv"),
                    "summary": str(output_dir / "phase9f5_redirect_guardrail_validation_summary.json"),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
