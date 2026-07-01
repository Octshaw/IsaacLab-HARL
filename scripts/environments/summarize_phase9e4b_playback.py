"""Summarize Phase 9E-4B budget-trained playback diagnostics.

This helper reads existing CSV/JSON/TensorBoard outputs only. It does not
launch Isaac Sim, run training, or modify assignment/environment behavior.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
except Exception:  # pragma: no cover - optional at runtime
    EventAccumulator = None


RUNS = [
    {
        "run": "models_with_budget",
        "checkpoint": "models",
        "playback_cooldown": "budget",
        "path": Path("results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback"),
    },
    {
        "run": "best_model_with_budget",
        "checkpoint": "best_model",
        "playback_cooldown": "budget",
        "path": Path("results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback"),
    },
    {
        "run": "models_no_cooldown",
        "checkpoint": "models",
        "playback_cooldown": "disabled",
        "path": Path("results/assignment_diagnostics/phase9e4b_budget_trained_models_no_cooldown_playback"),
    },
    {
        "run": "best_model_no_cooldown",
        "checkpoint": "best_model",
        "playback_cooldown": "disabled",
        "path": Path("results/assignment_diagnostics/phase9e4b_budget_trained_best_model_no_cooldown_playback"),
    },
]

TRAIN_RUN_DIR = Path(
    "results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/"
    "assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/"
    "seed-00001-2026-07-01-14-40-47"
)
TRAIN_CONSOLE_LOG = Path("results/assignment_diagnostics/phase9e4a_budget_m15_slack5_d5_train_100k_console.log")
SUMMARY_CSV = Path("results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.csv")
SUMMARY_JSON = Path("results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.json")


def _float(value: Any, default: float = math.nan) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _parse_list(value: Any) -> list[Any]:
    if value is None:
        return []
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _mode(values: list[int]) -> int | None:
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _derive_history_metrics(history_rows: list[dict[str, str]]) -> dict[str, Any]:
    max_streak = max((_float(row.get("same_target_streak"), 0.0) for row in history_rows), default=0.0)
    max_step = max((_int(row.get("step"), -1) for row in history_rows), default=-1)
    late_start = max(0, max_step - 100)
    robots = sorted({_int(row.get("robot_id"), -1) for row in history_rows if _int(row.get("robot_id"), -1) >= 0})
    late_targets: dict[str, int | None] = {}
    final_targets: dict[str, int | None] = {}
    max_streak_targets: dict[str, int | None] = {}
    for robot in robots:
        robot_rows = [row for row in history_rows if _int(row.get("robot_id"), -1) == robot]
        late_values = [
            _int(row.get("selected_viewpoint_id"), -1)
            for row in robot_rows
            if _int(row.get("step"), -1) >= late_start and not str(row.get("is_noop", "")).lower() == "true"
        ]
        final_candidates = [row for row in robot_rows if _int(row.get("step"), -1) == max_step]
        robot_max = max((_float(row.get("same_target_streak"), 0.0) for row in robot_rows), default=0.0)
        max_rows = [row for row in robot_rows if _float(row.get("same_target_streak"), 0.0) == robot_max]
        late_targets[f"robot_{robot}"] = _mode([value for value in late_values if value >= 0])
        final_targets[f"robot_{robot}"] = (
            _int(final_candidates[-1].get("selected_viewpoint_id"), -1) if final_candidates else None
        )
        max_streak_targets[f"robot_{robot}"] = (
            _int(max_rows[-1].get("selected_viewpoint_id"), -1) if max_rows else None
        )
    return {
        "max_same_target_streak": max_streak,
        "late_window_start_step": late_start,
        "late_repeated_targets_by_robot": late_targets,
        "final_selected_targets_by_robot": final_targets,
        "max_streak_targets_by_robot": max_streak_targets,
    }


def _summarize_run(run: dict[str, Any]) -> dict[str, Any]:
    summary_rows = _read_csv(run["path"] / "summary.csv")
    if not summary_rows:
        raise RuntimeError(f"Missing summary row in {run['path']}")
    summary = summary_rows[0]
    history = _read_csv(run["path"] / "assignment_history.csv")
    derived = _derive_history_metrics(history)
    return {
        "run": run["run"],
        "checkpoint": run["checkpoint"],
        "playback_cooldown": run["playback_cooldown"],
        "output_dir": str(run["path"]),
        "final_coverage": _float(summary.get("final_coverage_mean")),
        "coverage_auc": _float(summary.get("coverage_auc_mean")),
        "new_viewpoints": _float(summary.get("new_viewpoints_total_mean")),
        "max_same_target_streak": derived["max_same_target_streak"],
        "late_repeated_assignment_count": _float(summary.get("late_repeated_assignment_count_mean")),
        "late_repeated_targets_by_robot": derived["late_repeated_targets_by_robot"],
        "final_selected_targets_by_robot": derived["final_selected_targets_by_robot"],
        "max_streak_targets_by_robot": derived["max_streak_targets_by_robot"],
        "noop_when_available_rate": _float(summary.get("noop_when_available_rate_mean")),
        "selected_target_conflict_rate": _float(summary.get("selected_target_conflict_rate_mean")),
        "inter_robot_overlap_rate": _float(summary.get("inter_robot_overlap_rate_mean")),
        "base_motion_crossing_rate": _float(summary.get("actual_base_motion_intersection_rate_mean")),
        "duplicate_selected_target_rate": _float(summary.get("duplicate_selected_target_rate_mean")),
        "duplicate_scans": None,
        "reach_violation": None,
        "cooldown_enabled": summary.get("cooldown_enabled"),
        "cooldown_trigger_mode": summary.get("cooldown_trigger_mode"),
        "cooldown_trigger_count": _float(summary.get("cooldown_trigger_count_mean")),
        "budget_trigger_count": _float(summary.get("budget_trigger_count_mean")),
        "cooldown_suppressed_count": _float(summary.get("cooldown_suppressed_count_mean")),
        "selected_pair_active_count": _float(summary.get("cooldown_active_count_mean")),
        "budget_over_budget_selected_count": _float(summary.get("budget_over_budget_selected_count_mean")),
        "budget_triggered_pair_count": _float(summary.get("budget_triggered_pair_count_mean")),
        "budget_ratio_mean": _float(summary.get("budget_ratio_mean")),
        "budget_ratio_max": _float(summary.get("budget_ratio_max")),
    }


def _parse_training_console() -> dict[str, Any]:
    context: dict[str, Any] = {
        "console_log": str(TRAIN_CONSOLE_LOG),
        "training_completed": False,
        "final_run_dir": str(TRAIN_RUN_DIR),
        "models_exists": (TRAIN_RUN_DIR / "models").exists(),
        "best_model_exists": (TRAIN_RUN_DIR / "best_model").exists(),
    }
    if not TRAIN_CONSOLE_LOG.exists():
        context["console_log_found"] = False
        return context
    context["console_log_found"] = True
    text = TRAIN_CONSOLE_LOG.read_text(encoding="utf-8", errors="replace")
    context["training_completed"] = "Saved final HARL model" in text
    progress_matches = re.findall(r"episodes\s+(\d+)/(\d+)\s+total num timesteps\s+(\d+)/(\d+)", text)
    if progress_matches:
        episodes, episodes_total, timesteps, timesteps_total = progress_matches[-1]
        context.update(
            {
                "final_episodes": int(episodes),
                "total_episodes": int(episodes_total),
                "final_timesteps": int(timesteps),
                "target_timesteps": int(timesteps_total),
            }
        )
    for key in [
        "coverage_ratio",
        "duplicate_scans",
        "reach_violation",
        "assignment_rl.noop_count",
        "assignment_cooldown.budget_trigger_count",
        "assignment_cooldown.suppressed_action_count_mean",
        "assignment_rl_reward/final_reward_mean",
    ]:
        matches = re.findall(rf"{re.escape(key)}:\s+([-+0-9.eE]+)", text)
        if matches:
            context[f"last_{key}"] = float(matches[-1])
    reward_matches = re.findall(r"Total Reward is\s+([-+0-9.eE]+)", text)
    if reward_matches:
        context["last_Total_Reward"] = float(reward_matches[-1].rstrip("."))
    final_reward = context.get("last_assignment_rl_reward/final_reward_mean")
    total_reward = context.get("last_Total_Reward")
    if final_reward not in (None, 0.0) and total_reward is not None:
        context["total_reward_to_final_reward_ratio"] = total_reward / final_reward
    return context


def _parse_tensorboard() -> dict[str, Any]:
    event_dir = TRAIN_RUN_DIR / "logs"
    context: dict[str, Any] = {"event_dir": str(event_dir), "available": EventAccumulator is not None}
    if EventAccumulator is None or not event_dir.exists():
        return context
    accumulator = EventAccumulator(str(event_dir), size_guidance={"scalars": 0})
    accumulator.Reload()
    tags = accumulator.Tags().get("scalars", [])
    nonfinite: list[dict[str, Any]] = []
    final_values: dict[str, float] = {}
    for tag in tags:
        events = accumulator.Scalars(tag)
        if events:
            final_values[tag] = events[-1].value
        for event in events:
            if not math.isfinite(event.value):
                nonfinite.append({"tag": tag, "step": event.step, "value": event.value})
    interesting_tags = [
        tag
        for tag in final_values
        if tag
        in {
            "Total_Reward",
            "coverage_ratio",
            "assignment_rl_reward/final_reward_mean",
            "assignment_rl.noop_count",
            "assignment_cooldown.budget_trigger_count",
            "assignment_cooldown.suppressed_action_count_mean",
        }
    ]
    context.update(
        {
            "scalar_tag_count": len(tags),
            "nonfinite_scalar_count": len(nonfinite),
            "nonfinite_examples": nonfinite[:10],
            "final_interesting_scalars": {tag: final_values[tag] for tag in interesting_tags},
        }
    )
    return context


def main() -> None:
    rows = [_summarize_run(run) for run in RUNS]
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "run",
        "checkpoint",
        "playback_cooldown",
        "final_coverage",
        "coverage_auc",
        "new_viewpoints",
        "max_same_target_streak",
        "late_repeated_assignment_count",
        "late_repeated_targets_by_robot",
        "final_selected_targets_by_robot",
        "max_streak_targets_by_robot",
        "noop_when_available_rate",
        "selected_target_conflict_rate",
        "inter_robot_overlap_rate",
        "base_motion_crossing_rate",
        "duplicate_selected_target_rate",
        "duplicate_scans",
        "reach_violation",
        "cooldown_enabled",
        "cooldown_trigger_mode",
        "cooldown_trigger_count",
        "budget_trigger_count",
        "cooldown_suppressed_count",
        "selected_pair_active_count",
        "budget_over_budget_selected_count",
        "budget_triggered_pair_count",
        "budget_ratio_mean",
        "budget_ratio_max",
        "output_dir",
    ]
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in csv_fields})
    payload = {
        "playback_runs": rows,
        "training_context_console": _parse_training_console(),
        "training_context_tensorboard": _parse_tensorboard(),
        "field_notes": {
            "duplicate_scans": "not present in playback diagnostics; available in Phase 9E-4A training console only",
            "reach_violation": "not present in playback diagnostics; available in Phase 9E-4A training console only",
            "late_repeated_targets_by_robot": "mode of selected non-noop targets in the last 100 playback steps",
            "final_selected_targets_by_robot": "selected target at final playback step",
        },
    }
    SUMMARY_JSON.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(_json_safe(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
