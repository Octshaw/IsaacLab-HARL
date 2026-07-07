"""Phase 9G-3 failed-pair memory playback validation aggregator.

This script is offline CSV/JSON analysis only. It reads already-generated
playback histories plus Phase 9F/9G analyzer outputs and writes a compact
comparison table for the Phase 9G-3 report. It does not import or run Isaac Lab,
HARL, wrappers, rewards, controllers, or simulation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison")

DEFAULT_INPUTS = {
    "reference_phase9f2c_disabled": {
        "history": Path("results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv"),
        "summary": Path("results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/summary.csv"),
        "trigger_summary": DEFAULT_OUTPUT_DIR
        / "reference_phase9f2c_trigger_windows"
        / "phase9f2c_trigger_window_summary.json",
    },
    "reference_phase9f5_redirect_guardrail": {
        "history": Path("results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv"),
        "summary": Path("results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/summary.csv"),
        "trigger_summary": DEFAULT_OUTPUT_DIR
        / "reference_phase9f5_trigger_windows"
        / "phase9f2c_trigger_window_summary.json",
    },
    "phase9g3_default_disabled": {
        "history": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_default_disabled/assignment_history.csv"
        ),
        "summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/summary.csv"
        ),
        "trigger_summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_default_disabled_trigger_windows/phase9f2c_trigger_window_summary.json"
        ),
    },
    "phase9g3_failed_pair_memory_enabled": {
        "history": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_failed_pair_memory_enabled/assignment_history.csv"
        ),
        "summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_failed_pair_memory_enabled/summary.csv"
        ),
        "trigger_summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_failed_pair_memory_enabled_trigger_windows/phase9f2c_trigger_window_summary.json"
        ),
    },
}

DEFAULT_LIFECYCLE_FILE_SUMMARY = DEFAULT_OUTPUT_DIR / "lifecycle_all" / "phase9g1_lifecycle_file_summary.csv"
DEFAULT_ENABLED_TRIGGER_ATTRIBUTION = Path(
    "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
    "phase9g3_failed_pair_memory_enabled_trigger_windows/phase9f2c_trigger_window_attribution.csv"
)

COMPARISON_FIELDS = [
    "label",
    "history",
    "final_coverage_ratio",
    "coverage_auc",
    "same_owner_returns",
    "median_same_owner_return_delay_steps",
    "min_same_owner_return_delay_steps",
    "max_same_owner_return_delay_steps",
    "teammate_reacquires",
    "coverage_gain_after_release_count",
    "coverage_gain_within_20_count",
    "noop_action_rate",
    "noop_when_available_rate",
    "next_exact_duplicate_direct_count",
    "next_nearby_selected_target_direct_count",
    "next_inter_robot_overlap_direct_count",
    "next_path_crossing_direct_count",
    "next_path_near_miss_direct_count",
    "return_to_triggered_pair_after_cooldown_count",
    "failed_pair_memory_enabled",
    "failed_pair_memory_trigger_count",
    "failed_pair_memory_active_pair_step_total",
    "failed_pair_memory_active_step_count",
    "failed_pair_memory_suppressed_count",
    "failed_pair_memory_fail_open_count",
    "failed_pair_memory_only_noop_remaining_count",
    "failed_pair_memory_selected_pair_active_count",
    "failed_pair_memory_selected_pair_ttl_mean",
    "failed_pair_memory_selected_pair_ttl_max",
]

TTL_FIELDS = [
    "trigger_step",
    "trigger_robot_id",
    "trigger_target_id",
    "return_step_after_cooldown",
    "trigger_to_return_step_delta",
    "return_row_found",
    "selected_pair_active_at_return",
    "ttl_remaining_at_return",
    "active_count_at_return_step",
    "last_active_memory_step_before_return",
    "active_memory_steps_between_trigger_and_return",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _single_csv_row(path: Path) -> dict[str, str]:
    rows = _read_csv_rows(path)
    return rows[0] if rows else {}


def _norm_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lower()


def _path_matches(left: str | Path, right: str | Path) -> bool:
    left_norm = _norm_path(left)
    right_norm = _norm_path(right)
    return left_norm == right_norm or left_norm.endswith(right_norm) or right_norm.endswith(left_norm)


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result):
        return default
    return result


def _int(value: Any, default: int = 0) -> int:
    return int(round(_float(value, float(default))))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _step_key(row: dict[str, str]) -> tuple[int, int, int]:
    return (_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("step")))


def _sum_step_max(rows: list[dict[str, str]], field: str) -> float:
    per_step: dict[tuple[int, int, int], float] = defaultdict(float)
    for row in rows:
        if field not in row:
            continue
        key = _step_key(row)
        per_step[key] = max(per_step[key], _float(row.get(field)))
    return sum(per_step.values())


def _count_step_positive(rows: list[dict[str, str]], field: str) -> int:
    per_step: dict[tuple[int, int, int], float] = defaultdict(float)
    for row in rows:
        if field not in row:
            continue
        key = _step_key(row)
        per_step[key] = max(per_step[key], _float(row.get(field)))
    return sum(1 for value in per_step.values() if value > 0)


def _sum_bool_rows(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if _bool(row.get(field)))


def _load_lifecycle_by_history(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv_rows(path)
    return {row.get("source_file", ""): row for row in rows}


def _lifecycle_for(history: Path, lifecycle_rows: dict[str, dict[str, str]]) -> dict[str, str]:
    for source, row in lifecycle_rows.items():
        if _path_matches(source, history):
            return row
    return {}


def _build_comparison_rows(
    inputs: dict[str, dict[str, Path]], lifecycle_file_summary: Path
) -> list[dict[str, Any]]:
    lifecycle_rows = _load_lifecycle_by_history(lifecycle_file_summary)
    comparison_rows: list[dict[str, Any]] = []

    for label, paths in inputs.items():
        history = paths["history"]
        summary = _single_csv_row(paths["summary"])
        trigger_summary = _read_json(paths["trigger_summary"]).get("attribution", {})
        lifecycle = _lifecycle_for(history, lifecycle_rows)
        history_rows = _read_csv_rows(history)
        row_count = max(1, len(history_rows))

        selected_pair_ttls = [
            _float(row.get("failed_pair_memory_selected_pair_ttl_remaining"))
            for row in history_rows
            if _bool(row.get("failed_pair_memory_selected_pair_active"))
        ]
        ttl_mean = sum(selected_pair_ttls) / len(selected_pair_ttls) if selected_pair_ttls else 0.0
        ttl_max = max(selected_pair_ttls) if selected_pair_ttls else 0.0

        comparison_rows.append(
            {
                "label": label,
                "history": str(history),
                "final_coverage_ratio": _float(summary.get("final_coverage_mean")),
                "coverage_auc": _float(summary.get("coverage_auc_mean")),
                "same_owner_returns": _int(lifecycle.get("num_same_owner_returns")),
                "median_same_owner_return_delay_steps": _float(
                    lifecycle.get("median_same_owner_return_delay_steps")
                ),
                "min_same_owner_return_delay_steps": _int(lifecycle.get("min_same_owner_return_delay_steps")),
                "max_same_owner_return_delay_steps": _int(lifecycle.get("max_same_owner_return_delay_steps")),
                "teammate_reacquires": _int(lifecycle.get("num_teammate_reacquires")),
                "coverage_gain_after_release_count": _int(lifecycle.get("coverage_gain_after_release_count")),
                "coverage_gain_within_20_count": _int(lifecycle.get("coverage_gain_within_20_count")),
                "noop_action_rate": _sum_bool_rows(history_rows, "is_noop") / row_count,
                "noop_when_available_rate": _float(summary.get("noop_when_available_rate_mean")),
                "next_exact_duplicate_direct_count": _int(trigger_summary.get("next_exact_duplicate_direct_count")),
                "next_nearby_selected_target_direct_count": _int(
                    trigger_summary.get("next_nearby_selected_target_direct_count")
                ),
                "next_inter_robot_overlap_direct_count": _int(
                    trigger_summary.get("next_inter_robot_overlap_direct_count")
                ),
                "next_path_crossing_direct_count": _int(trigger_summary.get("next_path_crossing_direct_count")),
                "next_path_near_miss_direct_count": _int(trigger_summary.get("next_path_near_miss_direct_count")),
                "return_to_triggered_pair_after_cooldown_count": _int(
                    trigger_summary.get("return_to_triggered_pair_after_cooldown_count")
                ),
                "failed_pair_memory_enabled": _bool(summary.get("failed_pair_memory_enabled"))
                or any(_bool(row.get("assignment_failed_pair_memory_enabled")) for row in history_rows),
                "failed_pair_memory_trigger_count": _sum_step_max(history_rows, "failed_pair_memory_trigger_count"),
                "failed_pair_memory_active_pair_step_total": _sum_step_max(
                    history_rows, "failed_pair_memory_active_count"
                ),
                "failed_pair_memory_active_step_count": _count_step_positive(
                    history_rows, "failed_pair_memory_active_count"
                ),
                "failed_pair_memory_suppressed_count": _sum_step_max(
                    history_rows, "failed_pair_memory_suppressed_count"
                ),
                "failed_pair_memory_fail_open_count": _sum_step_max(
                    history_rows, "failed_pair_memory_fail_open_count"
                ),
                "failed_pair_memory_only_noop_remaining_count": _sum_step_max(
                    history_rows, "failed_pair_memory_only_noop_remaining_count"
                ),
                "failed_pair_memory_selected_pair_active_count": _sum_bool_rows(
                    history_rows, "failed_pair_memory_selected_pair_active"
                ),
                "failed_pair_memory_selected_pair_ttl_mean": ttl_mean,
                "failed_pair_memory_selected_pair_ttl_max": ttl_max,
            }
        )

    return comparison_rows


def _index_history_rows(rows: list[dict[str, str]]) -> dict[tuple[int, int, int, int], dict[str, str]]:
    indexed: dict[tuple[int, int, int, int], dict[str, str]] = {}
    for row in rows:
        key = (
            _int(row.get("episode")),
            _int(row.get("env_id")),
            _int(row.get("step")),
            _int(row.get("robot_id")),
        )
        indexed[key] = row
    return indexed


def _active_steps_by_step(rows: list[dict[str, str]]) -> dict[tuple[int, int, int], float]:
    active_by_step: dict[tuple[int, int, int], float] = defaultdict(float)
    for row in rows:
        active_by_step[_step_key(row)] = max(active_by_step[_step_key(row)], _float(row.get("failed_pair_memory_active_count")))
    return active_by_step


def _build_ttl_boundary_rows(enabled_history: Path, enabled_trigger_attribution: Path) -> list[dict[str, Any]]:
    history_rows = _read_csv_rows(enabled_history)
    attribution_rows = _read_csv_rows(enabled_trigger_attribution)
    indexed_history = _index_history_rows(history_rows)
    active_by_step = _active_steps_by_step(history_rows)
    ttl_rows: list[dict[str, Any]] = []

    for row in attribution_rows:
        episode = _int(row.get("episode"))
        env_id = _int(row.get("env_id"))
        trigger_step = _int(row.get("trigger_step"))
        robot_id = _int(row.get("trigger_robot_id"))
        target_id = _int(row.get("trigger_target_id"))
        return_step = _int(row.get("return_step_after_cooldown"), -1)
        return_row = indexed_history.get((episode, env_id, return_step, robot_id), {})

        active_steps = [
            step
            for step in range(trigger_step, return_step + 1)
            if active_by_step.get((episode, env_id, step), 0.0) > 0
        ]

        ttl_rows.append(
            {
                "trigger_step": trigger_step,
                "trigger_robot_id": robot_id,
                "trigger_target_id": target_id,
                "return_step_after_cooldown": return_step,
                "trigger_to_return_step_delta": return_step - trigger_step if return_step >= 0 else "",
                "return_row_found": bool(return_row),
                "selected_pair_active_at_return": _bool(return_row.get("failed_pair_memory_selected_pair_active")),
                "ttl_remaining_at_return": _int(return_row.get("failed_pair_memory_selected_pair_ttl_remaining")),
                "active_count_at_return_step": active_by_step.get((episode, env_id, return_step), 0.0),
                "last_active_memory_step_before_return": max(active_steps) if active_steps else "",
                "active_memory_steps_between_trigger_and_return": len(active_steps),
            }
        )

    return ttl_rows


def _build_summary(comparison_rows: list[dict[str, Any]], ttl_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = {str(row["label"]): row for row in comparison_rows}
    default_row = by_label.get("phase9g3_default_disabled", {})
    enabled_row = by_label.get("phase9g3_failed_pair_memory_enabled", {})
    same_owner_delta = _float(enabled_row.get("same_owner_returns")) - _float(default_row.get("same_owner_returns"))
    memory_triggered = _float(enabled_row.get("failed_pair_memory_trigger_count")) > 0
    memory_suppressed = _float(enabled_row.get("failed_pair_memory_suppressed_count")) > 0
    return_active_count = sum(1 for row in ttl_rows if _bool(row.get("selected_pair_active_at_return")))

    if same_owner_delta < 0 and _float(enabled_row.get("noop_action_rate")) <= _float(default_row.get("noop_action_rate")):
        conclusion = "PASS"
    elif same_owner_delta < 0:
        conclusion = "PARTIAL"
    else:
        conclusion = "FAIL"

    return {
        "comparison_csv": "phase9g3_comparison_table.csv",
        "ttl_boundary_csv": "phase9g3_ttl_boundary_rows.csv",
        "conclusion": conclusion,
        "memory_triggered": memory_triggered,
        "memory_suppressed_any_action": memory_suppressed,
        "same_owner_return_delta_enabled_minus_default": same_owner_delta,
        "return_rows_with_selected_pair_active_memory": return_active_count,
        "ttl_return_row_count": len(ttl_rows),
        "ttl_selected_pair_active_at_all_returns": bool(ttl_rows) and return_active_count == len(ttl_rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--lifecycle_file_summary", type=Path, default=DEFAULT_LIFECYCLE_FILE_SUMMARY)
    parser.add_argument("--enabled_trigger_attribution", type=Path, default=DEFAULT_ENABLED_TRIGGER_ATTRIBUTION)
    for label, paths in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{label}_history", type=Path, default=paths["history"])
        parser.add_argument(f"--{label}_summary", type=Path, default=paths["summary"])
        parser.add_argument(f"--{label}_trigger_summary", type=Path, default=paths["trigger_summary"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs: dict[str, dict[str, Path]] = {}
    for label in DEFAULT_INPUTS:
        inputs[label] = {
            "history": getattr(args, f"{label}_history"),
            "summary": getattr(args, f"{label}_summary"),
            "trigger_summary": getattr(args, f"{label}_trigger_summary"),
        }

    comparison_rows = _build_comparison_rows(inputs, args.lifecycle_file_summary)
    enabled_history = inputs["phase9g3_failed_pair_memory_enabled"]["history"]
    ttl_rows = _build_ttl_boundary_rows(enabled_history, args.enabled_trigger_attribution)
    summary = _build_summary(comparison_rows, ttl_rows)

    comparison_csv = args.output_dir / "phase9g3_comparison_table.csv"
    ttl_csv = args.output_dir / "phase9g3_ttl_boundary_rows.csv"
    summary_json = args.output_dir / "phase9g3_comparison_summary.json"
    _write_csv(comparison_csv, comparison_rows, COMPARISON_FIELDS)
    _write_csv(ttl_csv, ttl_rows, TTL_FIELDS)
    _write_json(summary_json, summary)

    print(f"[phase9g3] comparison_csv={comparison_csv}")
    print(f"[phase9g3] ttl_boundary_csv={ttl_csv}")
    print(f"[phase9g3] summary_json={summary_json}")
    print(
        "[phase9g3] conclusion={conclusion}, memory_triggered={memory_triggered}, "
        "memory_suppressed_any_action={memory_suppressed_any_action}, "
        "same_owner_return_delta_enabled_minus_default={same_owner_return_delta_enabled_minus_default}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
