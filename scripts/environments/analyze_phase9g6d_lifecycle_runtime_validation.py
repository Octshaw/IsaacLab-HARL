# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Offline validator for Phase 9G-6D passive lifecycle runtime diagnostics.

This script parses already-generated runtime outputs. It does not launch Isaac
Sim, does not run playback or evaluation, and does not change behavior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation")
SCHEMA_VERSION = "phase9g6c_assignment_lifecycle_diagnostics_v1"

EVENT_FIELDS = [
    "schema_version",
    "method_name",
    "proposal_type",
    "episode_id",
    "env_id",
    "step",
    "event_type",
    "robot_id",
    "target_id",
    "previous_target_id",
    "new_target_id",
    "attempt_age_proxy",
    "failure_reason",
    "release_reason",
    "claiming_robot_ids",
    "claiming_costs",
    "would_be_winner_robot_id",
    "would_be_loser_robot_ids",
    "arbitration_rule",
    "fallback_reason",
    "behavior_changed",
]

SUMMARY_FIELDS = [
    "schema_version",
    "enabled",
    "method_name",
    "num_envs",
    "num_robots",
    "num_tasks",
    "total_steps_observed",
    "total_events",
    "attempt_started_proxy_count",
    "attempt_continued_proxy_count",
    "noop_idle_proxy_count",
    "noop_after_active_ambiguous_count",
    "switch_request_proxy_count",
    "target_completed_proxy_count",
    "target_completed_by_teammate_proxy_count",
    "active_target_became_covered_proxy_count",
    "budget_failure_proxy_count",
    "release_proxy_count",
    "exact_claim_conflict_proxy_count",
    "unavailable_target_proposal_proxy_count",
    "invalid_assignment_proposal_proxy_count",
    "hypothetical_conflict_loser_count",
    "reset_proxy_count",
    "attempt_age_proxy_min",
    "attempt_age_proxy_mean",
    "attempt_age_proxy_max",
    "behavior_changed",
    "events_path",
    "summary_path",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _safe_json_list(value: str | None) -> list[Any]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _first_row(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    return rows[0] if rows else {}


def _compare_file_hash(left: Path, right: Path) -> tuple[bool, str, str]:
    left_hash = _sha256(left)
    right_hash = _sha256(right)
    return left_hash == right_hash, left_hash, right_hash


def _identity_compare(name: str, disabled_dir: Path, enabled_dir: Path) -> dict[str, Any]:
    files = ["assignment_history.csv", "per_episode.csv", "summary.csv"]
    file_results: dict[str, Any] = {}
    passed = True
    for file_name in files:
        disabled_path = disabled_dir / file_name
        enabled_path = enabled_dir / file_name
        exists = disabled_path.exists() and enabled_path.exists()
        if exists:
            same, disabled_hash, enabled_hash = _compare_file_hash(disabled_path, enabled_path)
            disabled_rows = len(_read_csv(disabled_path))
            enabled_rows = len(_read_csv(enabled_path))
        else:
            same = False
            disabled_hash = ""
            enabled_hash = ""
            disabled_rows = -1
            enabled_rows = -1
        file_results[file_name] = {
            "exists": exists,
            "same_sha256": same,
            "disabled_sha256": disabled_hash,
            "enabled_sha256": enabled_hash,
            "disabled_rows": disabled_rows,
            "enabled_rows": enabled_rows,
        }
        passed = passed and exists and same and disabled_rows == enabled_rows

    disabled_summary = _first_row(disabled_dir / "summary.csv")
    enabled_summary = _first_row(enabled_dir / "summary.csv")
    disabled_episode = _first_row(disabled_dir / "per_episode.csv")
    enabled_episode = _first_row(enabled_dir / "per_episode.csv")
    return {
        "comparison": name,
        "passed": passed,
        "files": file_results,
        "disabled_final_coverage": disabled_summary.get("final_coverage_mean")
        or disabled_summary.get("mean_final_coverage")
        or disabled_episode.get("final_coverage"),
        "enabled_final_coverage": enabled_summary.get("final_coverage_mean")
        or enabled_summary.get("mean_final_coverage")
        or enabled_episode.get("final_coverage"),
        "disabled_coverage_auc": disabled_summary.get("coverage_auc_mean")
        or disabled_summary.get("mean_coverage_auc")
        or disabled_episode.get("coverage_auc"),
        "enabled_coverage_auc": enabled_summary.get("coverage_auc_mean")
        or enabled_summary.get("mean_coverage_auc")
        or enabled_episode.get("coverage_auc"),
        "disabled_episode_length": disabled_summary.get("episode_steps_mean") or disabled_episode.get("episode_length"),
        "enabled_episode_length": enabled_summary.get("episode_steps_mean") or enabled_episode.get("episode_length"),
        "disabled_noop_rate": disabled_summary.get("noop_when_available_rate_mean")
        or disabled_summary.get("mean_noop_rate")
        or disabled_episode.get("noop_rate"),
        "enabled_noop_rate": enabled_summary.get("noop_when_available_rate_mean")
        or enabled_summary.get("mean_noop_rate")
        or enabled_episode.get("noop_rate"),
        "disabled_budget_trigger_count": disabled_summary.get("budget_trigger_count_mean", ""),
        "enabled_budget_trigger_count": enabled_summary.get("budget_trigger_count_mean", ""),
    }


def _load_lifecycle_output(label: str, method: str, events_path: Path, summary_path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                events.append(json.loads(text))
    summary = _read_json(summary_path)
    event_field_sets = {tuple(sorted(event.keys())) for event in events}
    behavior_changed_events = [event for event in events if bool(event.get("behavior_changed"))]
    invalid_events = [event for event in events if event.get("event_type") == "invalid_assignment_proposal_proxy"]
    event_counts = Counter(str(event.get("event_type")) for event in events)
    exact_conflict_events = [event for event in events if event.get("event_type") == "exact_claim_conflict_proxy"]
    reset_events = [event for event in events if event.get("event_type") == "reset_proxy"]
    non_initial_reset_order_ok = True
    reset_order_notes: list[str] = []
    seen_non_reset_by_env_step: set[tuple[int, int]] = set()
    for event in events:
        env_step = (_as_int(event.get("env_id"), -1), _as_int(event.get("step"), -1))
        if event.get("event_type") == "reset_proxy":
            # Initial reset events at step 0 can legitimately precede proposals.
            if _as_int(event.get("step"), -1) == 0 and not seen_non_reset_by_env_step:
                continue
            if env_step not in seen_non_reset_by_env_step:
                non_initial_reset_order_ok = False
                reset_order_notes.append(
                    f"reset_proxy before same-step post event env={env_step[0]} step={env_step[1]}"
                )
        else:
            seen_non_reset_by_env_step.add(env_step)
    return {
        "label": label,
        "method": method,
        "events_path": str(events_path),
        "summary_path": str(summary_path),
        "events": events,
        "summary": summary,
        "event_count": len(events),
        "event_counts": dict(event_counts),
        "event_field_sets": event_field_sets,
        "behavior_changed_event_count": len(behavior_changed_events),
        "behavior_changed_summary": bool(summary.get("behavior_changed")),
        "invalid_assignment_proposal_proxy_count": len(invalid_events),
        "summary_total_events": _as_int(summary.get("total_events"), -1),
        "schema_version": summary.get("schema_version"),
        "summary_key_set": tuple(sorted(summary.keys())),
        "method_name": summary.get("method_name"),
        "num_envs": _as_int(summary.get("num_envs"), -1),
        "num_robots": _as_int(summary.get("num_robots"), -1),
        "num_tasks": _as_int(summary.get("num_tasks"), -1),
        "exact_conflict_count": len(exact_conflict_events),
        "exact_conflict_passive": all(not bool(event.get("behavior_changed")) for event in exact_conflict_events),
        "reset_proxy_count": len(reset_events),
        "non_initial_reset_order_ok": non_initial_reset_order_ok,
        "reset_order_notes": reset_order_notes,
    }


def _newly_covered_count(history_path: Path) -> int:
    rows = _read_csv(history_path)
    seen: set[tuple[int, int, int, int]] = set()
    for row in rows:
        episode = _as_int(row.get("episode"), 0)
        env_id = _as_int(row.get("env_id"), 0)
        step = _as_int(row.get("step"), 0)
        for target in _safe_json_list(row.get("newly_covered_viewpoint_ids")):
            seen.add((episode, env_id, step, _as_int(target, -1)))
    return len(seen)


def _budget_pairs_from_history(history_path: Path) -> set[tuple[int, int, int, int]]:
    rows = _read_csv(history_path)
    pairs: set[tuple[int, int, int, int]] = set()
    for row in rows:
        budget = _as_bool(row.get("budget_triggered_by_budget")) or _as_bool(row.get("budget_triggered_after_step"))
        if not budget:
            continue
        step = _as_int(row.get("step"), 0)
        # RL playback rows are 1-based in assignment_history; lifecycle events
        # use logger step starting at 0.
        lifecycle_step = step - 1 if row.get("method") == "rl_checkpoint" else step
        robot = _as_int(row.get("robot_id") or row.get("agent_id"), -1)
        target = _as_int(row.get("assigned_viewpoint_id") or row.get("selected_viewpoint_id"), -1)
        env_id = _as_int(row.get("env_id"), 0)
        pairs.add((env_id, lifecycle_step, robot, target))
    return pairs


def _budget_pairs_from_events(events: list[dict[str, Any]]) -> set[tuple[int, int, int, int]]:
    pairs: set[tuple[int, int, int, int]] = set()
    for event in events:
        if event.get("event_type") != "budget_failure_proxy":
            continue
        pairs.add(
            (
                _as_int(event.get("env_id"), 0),
                _as_int(event.get("step"), 0),
                _as_int(event.get("robot_id"), -1),
                _as_int(event.get("target_id"), -1),
            )
        )
    return pairs


def _runtime_consistency(run: dict[str, Any], history_path: Path) -> dict[str, Any]:
    summary = run["summary"]
    events = run["events"]
    completed_event_count = (
        _as_int(summary.get("target_completed_proxy_count"), 0)
        + _as_int(summary.get("target_completed_by_teammate_proxy_count"), 0)
        + _as_int(summary.get("active_target_became_covered_proxy_count"), 0)
    )
    newly_covered = _newly_covered_count(history_path)
    budget_history = _budget_pairs_from_history(history_path)
    budget_events = _budget_pairs_from_events(events)
    release_events = [event for event in events if event.get("event_type") == "release_proxy"]
    return {
        "label": run["label"],
        "method": run["method"],
        "newly_covered_count": newly_covered,
        "completed_lifecycle_event_count": completed_event_count,
        "completion_consistent": newly_covered == completed_event_count,
        "budget_history_count": len(budget_history),
        "budget_lifecycle_event_count": len(budget_events),
        "budget_pair_identity_consistent": budget_history == budget_events,
        "release_proxy_count": len(release_events),
        "release_matches_budget_count": len(release_events) == len(budget_events),
        "reset_order_ok": bool(run["non_initial_reset_order_ok"]),
        "exact_conflict_count": run["exact_conflict_count"],
        "exact_conflict_passive": bool(run["exact_conflict_passive"]),
        "invalid_assignment_proposal_proxy_count": run["invalid_assignment_proposal_proxy_count"],
        "unavailable_target_proposal_proxy_count": _as_int(summary.get("unavailable_target_proposal_proxy_count"), 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output_dir", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    output_dir = (args.output_dir or (root / "comparison")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    identity = [
        _identity_compare("rl_enabled_vs_disabled", root / "rl_disabled", root / "rl_enabled"),
        _identity_compare("nearest_enabled_vs_disabled", root / "nearest_disabled", root / "nearest_enabled"),
    ]

    lifecycle_specs = [
        (
            "rl_enabled",
            "rl_checkpoint",
            root / "rl_enabled" / "lifecycle" / "assignment_lifecycle_events.jsonl",
            root / "rl_enabled" / "lifecycle" / "assignment_lifecycle_summary.json",
            root / "rl_enabled" / "assignment_history.csv",
        ),
        (
            "nearest_enabled",
            "nearest",
            root / "nearest_enabled" / "lifecycle" / "nearest" / "assignment_lifecycle_events.jsonl",
            root / "nearest_enabled" / "lifecycle" / "nearest" / "assignment_lifecycle_summary.json",
            root / "nearest_enabled" / "assignment_history.csv",
        ),
        (
            "random_enabled",
            "random",
            root / "random_enabled" / "lifecycle" / "random" / "assignment_lifecycle_events.jsonl",
            root / "random_enabled" / "lifecycle" / "random" / "assignment_lifecycle_summary.json",
            root / "random_enabled" / "assignment_history.csv",
        ),
        (
            "greedy_enabled",
            "greedy",
            root / "greedy_enabled" / "lifecycle" / "greedy" / "assignment_lifecycle_events.jsonl",
            root / "greedy_enabled" / "lifecycle" / "greedy" / "assignment_lifecycle_summary.json",
            root / "greedy_enabled" / "assignment_history.csv",
        ),
    ]

    lifecycle_runs = []
    missing_outputs = []
    for label, method, events_path, summary_path, _history_path in lifecycle_specs:
        if not events_path.exists() or not summary_path.exists():
            missing_outputs.append({"label": label, "events_path": str(events_path), "summary_path": str(summary_path)})
            continue
        lifecycle_runs.append(_load_lifecycle_output(label, method, events_path, summary_path))

    schema_versions = {run["schema_version"] for run in lifecycle_runs}
    event_field_sets = {field_set for run in lifecycle_runs for field_set in run["event_field_sets"]}
    summary_key_sets = {run["summary_key_set"] for run in lifecycle_runs}
    lifecycle_paths = [run["events_path"] for run in lifecycle_runs] + [run["summary_path"] for run in lifecycle_runs]
    output_isolation_ok = len(lifecycle_paths) == len(set(lifecycle_paths))
    expected_event_fields = tuple(sorted(EVENT_FIELDS))
    expected_summary_fields = tuple(sorted(SUMMARY_FIELDS))
    schema_ok = (
        not missing_outputs
        and schema_versions == {SCHEMA_VERSION}
        and len(event_field_sets) == 1
        and expected_event_fields == next(iter(event_field_sets), ())
        and len(summary_key_sets) == 1
        and expected_summary_fields == next(iter(summary_key_sets), ())
    )
    lifecycle_files_ok = all(
        run["event_count"] == run["summary_total_events"]
        and run["behavior_changed_event_count"] == 0
        and not run["behavior_changed_summary"]
        and run["invalid_assignment_proposal_proxy_count"] == 0
        and run["method_name"] == run["method"]
        and run["num_envs"] == 1
        and run["num_robots"] == 3
        and run["num_tasks"] == 50
        for run in lifecycle_runs
    )

    consistency = []
    run_by_label = {run["label"]: run for run in lifecycle_runs}
    for label, _method, _events_path, _summary_path, history_path in lifecycle_specs:
        if label in run_by_label and history_path.exists():
            consistency.append(_runtime_consistency(run_by_label[label], history_path))

    identity_ok = all(row["passed"] for row in identity)
    consistency_ok = all(
        row["completion_consistent"]
        and row["budget_pair_identity_consistent"]
        and row["release_matches_budget_count"]
        and row["reset_order_ok"]
        and row["exact_conflict_passive"]
        and row["invalid_assignment_proposal_proxy_count"] == 0
        for row in consistency
    )
    pass_all = identity_ok and schema_ok and lifecycle_files_ok and output_isolation_ok and consistency_ok

    identity_rows = []
    for row in identity:
        assignment = row["files"].get("assignment_history.csv", {})
        per_episode = row["files"].get("per_episode.csv", {})
        summary = row["files"].get("summary.csv", {})
        identity_rows.append(
            {
                "comparison": row["comparison"],
                "passed": row["passed"],
                "assignment_history_same_sha256": assignment.get("same_sha256"),
                "assignment_history_rows_disabled": assignment.get("disabled_rows"),
                "assignment_history_rows_enabled": assignment.get("enabled_rows"),
                "per_episode_same_sha256": per_episode.get("same_sha256"),
                "summary_same_sha256": summary.get("same_sha256"),
                "disabled_final_coverage": row["disabled_final_coverage"],
                "enabled_final_coverage": row["enabled_final_coverage"],
                "disabled_coverage_auc": row["disabled_coverage_auc"],
                "enabled_coverage_auc": row["enabled_coverage_auc"],
                "disabled_episode_length": row["disabled_episode_length"],
                "enabled_episode_length": row["enabled_episode_length"],
                "disabled_noop_rate": row["disabled_noop_rate"],
                "enabled_noop_rate": row["enabled_noop_rate"],
                "disabled_budget_trigger_count": row["disabled_budget_trigger_count"],
                "enabled_budget_trigger_count": row["enabled_budget_trigger_count"],
            }
        )

    lifecycle_table = []
    for run in lifecycle_runs:
        summary = run["summary"]
        lifecycle_table.append(
            {
                "label": run["label"],
                "method_name": run["method_name"],
                "schema_version": run["schema_version"],
                "events": run["event_count"],
                "total_steps_observed": summary.get("total_steps_observed"),
                "attempt_started": summary.get("attempt_started_proxy_count"),
                "attempt_continued": summary.get("attempt_continued_proxy_count"),
                "switch_request": summary.get("switch_request_proxy_count"),
                "target_completed": summary.get("target_completed_proxy_count"),
                "active_target_became_covered": summary.get("active_target_became_covered_proxy_count"),
                "budget_failure": summary.get("budget_failure_proxy_count"),
                "release": summary.get("release_proxy_count"),
                "exact_conflict": summary.get("exact_claim_conflict_proxy_count"),
                "reset": summary.get("reset_proxy_count"),
                "invalid_proposal": summary.get("invalid_assignment_proposal_proxy_count"),
                "behavior_changed": summary.get("behavior_changed"),
            }
        )

    _write_csv(
        output_dir / "phase9g6d_identity_comparison.csv",
        identity_rows,
        list(identity_rows[0].keys()) if identity_rows else [],
    )
    _write_json(
        output_dir / "phase9g6d_runtime_schema_summary.json",
        {
            "schema_ok": schema_ok,
            "schema_versions": sorted(str(value) for value in schema_versions),
            "event_field_set_count": len(event_field_sets),
            "summary_key_set_count": len(summary_key_sets),
            "missing_outputs": missing_outputs,
            "output_isolation_ok": output_isolation_ok,
            "lifecycle_table": lifecycle_table,
        },
    )
    _write_json(
        output_dir / "phase9g6d_event_consistency.json",
        {
            "consistency_ok": consistency_ok,
            "runs": consistency,
        },
    )
    validation_summary = {
        "root": str(root),
        "output_dir": str(output_dir),
        "identity_ok": identity_ok,
        "schema_ok": schema_ok,
        "lifecycle_files_ok": lifecycle_files_ok,
        "output_isolation_ok": output_isolation_ok,
        "consistency_ok": consistency_ok,
        "behavior_changed_ok": all(
            run["behavior_changed_event_count"] == 0 and not run["behavior_changed_summary"] for run in lifecycle_runs
        ),
        "invalid_proposal_ok": all(run["invalid_assignment_proposal_proxy_count"] == 0 for run in lifecycle_runs),
        "conclusion": "PASS" if pass_all else "FAIL",
        "identity": identity,
        "lifecycle_outputs": [
            {
                key: value
                for key, value in run.items()
                if key not in {"events", "summary", "event_field_sets", "summary_key_set"}
            }
            for run in lifecycle_runs
        ],
    }
    _write_json(output_dir / "phase9g6d_validation_summary.json", validation_summary)
    print(json.dumps({"status": validation_summary["conclusion"], **validation_summary}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
