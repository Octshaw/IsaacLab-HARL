"""Phase 9G-4B failed-pair memory D=6 playback validation aggregator.

This script is offline CSV/JSON analysis only. It reads already-generated
playback histories and analyzer outputs, then writes the D=6 comparison table
and boundary diagnostics for the Phase 9G-4B report. It does not import or run
Isaac Lab, HARL, wrappers, rewards, controllers, or simulation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/comparison")
DEFAULT_LIFECYCLE_FILE_SUMMARY = Path(
    "results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/"
    "lifecycle_all/phase9g1_lifecycle_file_summary.csv"
)

DEFAULT_INPUTS = {
    "reference_phase9f2c_disabled": {
        "history": Path("results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv"),
        "summary": Path("results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/summary.csv"),
        "trigger_summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_comparison/reference_phase9f2c_trigger_windows/phase9f2c_trigger_window_summary.json"
        ),
        "trigger_attribution": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_comparison/reference_phase9f2c_trigger_windows/phase9f2c_trigger_window_attribution.csv"
        ),
    },
    "reference_phase9f5_redirect_guardrail": {
        "history": Path("results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv"),
        "summary": Path("results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/summary.csv"),
        "trigger_summary": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_comparison/reference_phase9f5_trigger_windows/phase9f2c_trigger_window_summary.json"
        ),
        "trigger_attribution": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_comparison/reference_phase9f5_trigger_windows/phase9f2c_trigger_window_attribution.csv"
        ),
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
        "trigger_attribution": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_default_disabled_trigger_windows/phase9f2c_trigger_window_attribution.csv"
        ),
    },
    "phase9g3_failed_pair_memory_d5": {
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
        "trigger_attribution": Path(
            "results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/"
            "phase9g3_failed_pair_memory_enabled_trigger_windows/phase9f2c_trigger_window_attribution.csv"
        ),
    },
    "phase9g4b_failed_pair_memory_d6": {
        "history": Path(
            "results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/"
            "phase9g4b_failed_pair_memory_d6/assignment_history.csv"
        ),
        "summary": Path(
            "results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/"
            "phase9g4b_failed_pair_memory_d6/summary.csv"
        ),
        "trigger_summary": Path(
            "results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/"
            "phase9g4b_d6_trigger_windows/phase9f2c_trigger_window_summary.json"
        ),
        "trigger_attribution": Path(
            "results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/"
            "phase9g4b_d6_trigger_windows/phase9f2c_trigger_window_attribution.csv"
        ),
    },
}

COMPARISON_FIELDS = [
    "label",
    "history",
    "final_coverage_ratio",
    "coverage_auc",
    "same_owner_returns",
    "same_owner_return_delay_steps",
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
    "selected_pair_active_at_return_count",
    "ttl_remaining_at_return_min",
    "ttl_remaining_at_return_max",
    "ttl_remaining_at_return_mean",
    "return_step_delta_min",
    "return_step_delta_max",
    "return_step_delta_mean",
    "returns_shifted_after_t_plus_6_count",
    "t_plus_6_original_pair_selected_count",
    "t_plus_6_memory_suppressed_count",
    "t_plus_6_selected_pair_active_count",
]

BOUNDARY_FIELDS = [
    "label",
    "trigger_step",
    "trigger_robot_id",
    "trigger_target_id",
    "boundary_step_t_plus_6",
    "boundary_selected_target_id",
    "boundary_original_pair_selected",
    "boundary_memory_suppressed_for_robot",
    "boundary_selected_pair_active",
    "boundary_selected_pair_ttl_remaining",
    "return_step_after_cooldown",
    "return_step_delta",
    "return_selected_target_id",
    "return_selected_pair_active",
    "return_selected_pair_ttl_remaining",
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


def _norm_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lower()


def _path_matches(left: str | Path, right: str | Path) -> bool:
    left_norm = _norm_path(left)
    right_norm = _norm_path(right)
    return left_norm == right_norm or left_norm.endswith(right_norm) or right_norm.endswith(left_norm)


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
    return {row.get("source_file", ""): row for row in _read_csv_rows(path)}


def _lifecycle_for(history: Path, lifecycle_rows: dict[str, dict[str, str]]) -> dict[str, str]:
    for source, row in lifecycle_rows.items():
        if _path_matches(source, history):
            return row
    return {}


def _history_index(rows: list[dict[str, str]]) -> dict[tuple[int, int, int, int], dict[str, str]]:
    indexed: dict[tuple[int, int, int, int], dict[str, str]] = {}
    for row in rows:
        indexed[(_int(row.get("episode")), _int(row.get("env_id")), _int(row.get("step")), _int(row.get("robot_id")))] = row
    return indexed


def _trigger_deltas(attribution_rows: list[dict[str, str]]) -> list[int]:
    deltas: list[int] = []
    for row in attribution_rows:
        return_step = _int(row.get("return_step_after_cooldown"), -1)
        trigger_step = _int(row.get("trigger_step"), -1)
        if return_step >= 0 and trigger_step >= 0:
            deltas.append(return_step - trigger_step)
    return deltas


def _stats(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    return (min(values), max(values), sum(values) / len(values))


def _build_boundary_rows(label: str, history_rows: list[dict[str, str]], attribution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    indexed = _history_index(history_rows)
    rows: list[dict[str, Any]] = []
    for trigger in attribution_rows:
        episode = _int(trigger.get("episode"))
        env_id = _int(trigger.get("env_id"))
        trigger_step = _int(trigger.get("trigger_step"))
        robot_id = _int(trigger.get("trigger_robot_id"))
        target_id = _int(trigger.get("trigger_target_id"))
        return_step = _int(trigger.get("return_step_after_cooldown"), -1)
        boundary_step = trigger_step + 6
        boundary = indexed.get((episode, env_id, boundary_step, robot_id), {})
        return_row = indexed.get((episode, env_id, return_step, robot_id), {})
        boundary_target = _int(boundary.get("selected_viewpoint_id"), -1)
        return_target = _int(return_row.get("selected_viewpoint_id"), -1)
        rows.append(
            {
                "label": label,
                "trigger_step": trigger_step,
                "trigger_robot_id": robot_id,
                "trigger_target_id": target_id,
                "boundary_step_t_plus_6": boundary_step,
                "boundary_selected_target_id": boundary_target,
                "boundary_original_pair_selected": boundary_target == target_id,
                "boundary_memory_suppressed_for_robot": _int(
                    boundary.get("failed_pair_memory_suppressed_count_for_robot")
                ),
                "boundary_selected_pair_active": _bool(boundary.get("failed_pair_memory_selected_pair_active")),
                "boundary_selected_pair_ttl_remaining": _int(
                    boundary.get("failed_pair_memory_selected_pair_ttl_remaining")
                ),
                "return_step_after_cooldown": return_step,
                "return_step_delta": return_step - trigger_step if return_step >= 0 else "",
                "return_selected_target_id": return_target,
                "return_selected_pair_active": _bool(return_row.get("failed_pair_memory_selected_pair_active")),
                "return_selected_pair_ttl_remaining": _int(
                    return_row.get("failed_pair_memory_selected_pair_ttl_remaining")
                ),
            }
        )
    return rows


def _build_comparison_rows(
    inputs: dict[str, dict[str, Path]], lifecycle_file_summary: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lifecycle_rows = _load_lifecycle_by_history(lifecycle_file_summary)
    comparison_rows: list[dict[str, Any]] = []
    all_boundary_rows: list[dict[str, Any]] = []

    for label, paths in inputs.items():
        history = paths["history"]
        summary = _single_csv_row(paths["summary"])
        trigger_summary = _read_json(paths["trigger_summary"]).get("attribution", {})
        lifecycle = _lifecycle_for(history, lifecycle_rows)
        history_rows = _read_csv_rows(history)
        attribution_rows = _read_csv_rows(paths["trigger_attribution"])
        row_count = max(1, len(history_rows))
        boundary_rows = _build_boundary_rows(label, history_rows, attribution_rows)
        all_boundary_rows.extend(boundary_rows)

        return_rows = [row for row in boundary_rows if row["return_step_after_cooldown"] != ""]
        return_active = [row for row in return_rows if bool(row["return_selected_pair_active"])]
        return_ttls = [float(row["return_selected_pair_ttl_remaining"]) for row in return_rows]
        ttl_min, ttl_max, ttl_mean = _stats(return_ttls)
        deltas = _trigger_deltas(attribution_rows)
        delta_min, delta_max, delta_mean = _stats([float(delta) for delta in deltas])

        comparison_rows.append(
            {
                "label": label,
                "history": str(history),
                "final_coverage_ratio": _float(summary.get("final_coverage_mean")),
                "coverage_auc": _float(summary.get("coverage_auc_mean")),
                "same_owner_returns": _int(lifecycle.get("num_same_owner_returns")),
                "same_owner_return_delay_steps": _float(lifecycle.get("median_same_owner_return_delay_steps")),
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
                "selected_pair_active_at_return_count": len(return_active),
                "ttl_remaining_at_return_min": ttl_min,
                "ttl_remaining_at_return_max": ttl_max,
                "ttl_remaining_at_return_mean": ttl_mean,
                "return_step_delta_min": delta_min,
                "return_step_delta_max": delta_max,
                "return_step_delta_mean": delta_mean,
                "returns_shifted_after_t_plus_6_count": sum(1 for delta in deltas if delta > 6),
                "t_plus_6_original_pair_selected_count": sum(
                    1 for row in boundary_rows if bool(row["boundary_original_pair_selected"])
                ),
                "t_plus_6_memory_suppressed_count": sum(
                    1 for row in boundary_rows if _float(row["boundary_memory_suppressed_for_robot"]) > 0
                ),
                "t_plus_6_selected_pair_active_count": sum(
                    1 for row in boundary_rows if bool(row["boundary_selected_pair_active"])
                ),
            }
        )

    return comparison_rows, all_boundary_rows


def _build_summary(comparison_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = {str(row["label"]): row for row in comparison_rows}
    d5 = by_label.get("phase9g3_failed_pair_memory_d5", {})
    d6 = by_label.get("phase9g4b_failed_pair_memory_d6", {})
    same_owner_delta = _float(d6.get("same_owner_returns")) - _float(d5.get("same_owner_returns"))
    suppressed = _float(d6.get("failed_pair_memory_suppressed_count")) > 0
    noop_regression = _float(d6.get("noop_action_rate")) > _float(d5.get("noop_action_rate"))
    coverage_regression = _float(d6.get("final_coverage_ratio")) < _float(d5.get("final_coverage_ratio"))

    if same_owner_delta < 0 and suppressed and not noop_regression and not coverage_regression:
        conclusion = "PASS"
    elif same_owner_delta < 0 and suppressed:
        conclusion = "PARTIAL"
    else:
        conclusion = "FAIL"

    return {
        "comparison_csv": "phase9g4b_d6_comparison_table.csv",
        "boundary_csv": "phase9g4b_d6_boundary_rows.csv",
        "conclusion": conclusion,
        "d6_suppressed_any_action": suppressed,
        "same_owner_return_delta_d6_minus_d5": same_owner_delta,
        "d6_returns_shifted_after_t_plus_6_count": _int(d6.get("returns_shifted_after_t_plus_6_count")),
        "d6_t_plus_6_memory_suppressed_count": _int(d6.get("t_plus_6_memory_suppressed_count")),
        "d6_t_plus_6_original_pair_selected_count": _int(d6.get("t_plus_6_original_pair_selected_count")),
        "coverage_regression": coverage_regression,
        "noop_regression": noop_regression,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--lifecycle_file_summary", type=Path, default=DEFAULT_LIFECYCLE_FILE_SUMMARY)
    for label, paths in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{label}_history", type=Path, default=paths["history"])
        parser.add_argument(f"--{label}_summary", type=Path, default=paths["summary"])
        parser.add_argument(f"--{label}_trigger_summary", type=Path, default=paths["trigger_summary"])
        parser.add_argument(f"--{label}_trigger_attribution", type=Path, default=paths["trigger_attribution"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs: dict[str, dict[str, Path]] = {}
    for label in DEFAULT_INPUTS:
        inputs[label] = {
            "history": getattr(args, f"{label}_history"),
            "summary": getattr(args, f"{label}_summary"),
            "trigger_summary": getattr(args, f"{label}_trigger_summary"),
            "trigger_attribution": getattr(args, f"{label}_trigger_attribution"),
        }

    comparison_rows, boundary_rows = _build_comparison_rows(inputs, args.lifecycle_file_summary)
    summary = _build_summary(comparison_rows)

    comparison_csv = args.output_dir / "phase9g4b_d6_comparison_table.csv"
    boundary_csv = args.output_dir / "phase9g4b_d6_boundary_rows.csv"
    summary_json = args.output_dir / "phase9g4b_d6_comparison_summary.json"
    _write_csv(comparison_csv, comparison_rows, COMPARISON_FIELDS)
    _write_csv(boundary_csv, boundary_rows, BOUNDARY_FIELDS)
    _write_json(summary_json, summary)

    print(f"[phase9g4b] comparison_csv={comparison_csv}")
    print(f"[phase9g4b] boundary_csv={boundary_csv}")
    print(f"[phase9g4b] summary_json={summary_json}")
    print(
        "[phase9g4b] conclusion={conclusion}, d6_suppressed_any_action={d6_suppressed_any_action}, "
        "same_owner_return_delta_d6_minus_d5={same_owner_return_delta_d6_minus_d5}, "
        "d6_returns_shifted_after_t_plus_6_count={d6_returns_shifted_after_t_plus_6_count}".format(**summary)
    )


if __name__ == "__main__":
    main()
