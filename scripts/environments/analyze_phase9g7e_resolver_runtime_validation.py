# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Offline validator for Phase 9G-7E resolver runtime validation outputs.

This script parses already-generated bounded runtime outputs. It does not
launch Isaac Sim, run playback/evaluation, or modify runtime behavior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("results/assignment_diagnostics/phase9g7e_resolver_runtime_validation")
DEFAULT_BASELINE_ROOT = Path("results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation")
RESOLVER_SCHEMA_VERSION = "phase9g7d_assignment_lifecycle_resolver_runtime_v1"

CORE_FILES = ("assignment_history.csv", "per_episode.csv", "summary.csv")
ENABLED_RUNS = ("rl_enabled", "nearest_enabled", "random_enabled", "greedy_enabled")
DISABLED_IDENTITY_PAIRS = (
    ("rl_disabled", "rl_disabled"),
    ("nearest_disabled", "nearest_disabled"),
)
REQUIRED_EVENT_KEYS = {
    "schema_version",
    "method_name",
    "episode_id",
    "env_id",
    "step",
    "event_type",
    "behavior_changed",
}
REQUIRED_ROW_FIELDS = [
    "schema_version",
    "method_name",
    "episode_id",
    "env_id",
    "step",
    "assignment_proposal",
    "effective_assignment",
    "proposal_effective_changed",
    "proposal_accepted",
    "proposal_rejected_reason",
    "continued_from_active_target",
    "new_claim_started",
    "switch_requested",
    "switch_rejected",
    "claim_conflict",
    "claim_winner",
    "claim_loser",
    "active_target_before",
    "active_target_after",
    "task_owner_before",
    "task_owner_after",
    "resolver_events",
    "behavior_changed",
]

REJECT_NONE = 0
REJECT_COVERED_TARGET = 2
REJECT_OWNED_TARGET = 3
REJECT_FAILED_PAIR = 4
REJECT_CLAIM_LOST = 5
REJECT_SWITCH_DISABLED = 6
REJECT_UNAVAILABLE_TARGET = 7


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return []
    return decoded if isinstance(decoded, list) else []


def _json_bool_list(value: Any) -> list[bool]:
    return [_as_bool(item) for item in _json_list(value)]


def _json_int_list(value: Any) -> list[int]:
    return [_as_int(item, -1) for item in _json_list(value)]


def _resolver_paths(root: Path, label: str) -> tuple[Path, Path, Path]:
    if label == "rl_enabled":
        base = root / label / "resolver"
    else:
        method = label.removesuffix("_enabled")
        base = root / label / "resolver" / method
    return (
        base / "assignment_lifecycle_resolver_events.jsonl",
        base / "assignment_lifecycle_resolver_summary.json",
        base / "assignment_lifecycle_resolver_rows.csv",
    )


def _passive_paths(root: Path, label: str) -> tuple[Path, Path]:
    if label == "rl_enabled":
        base = root / label / "lifecycle"
    else:
        method = label.removesuffix("_enabled")
        base = root / label / "lifecycle" / method
    return base / "assignment_lifecycle_events.jsonl", base / "assignment_lifecycle_summary.json"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _first_row(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    return rows[0] if rows else {}


def _compare_core_files(label: str, baseline_dir: Path, current_dir: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    passed = True
    for file_name in CORE_FILES:
        baseline_path = baseline_dir / file_name
        current_path = current_dir / file_name
        exists = baseline_path.exists() and current_path.exists()
        if exists:
            baseline_hash = _sha256(baseline_path)
            current_hash = _sha256(current_path)
            same = baseline_hash == current_hash
            baseline_rows = len(_read_csv(baseline_path))
            current_rows = len(_read_csv(current_path))
        else:
            baseline_hash = ""
            current_hash = ""
            same = False
            baseline_rows = -1
            current_rows = -1
        files[file_name] = {
            "exists": exists,
            "same_sha256": same,
            "baseline_sha256": baseline_hash,
            "current_sha256": current_hash,
            "baseline_rows": baseline_rows,
            "current_rows": current_rows,
        }
        passed = passed and exists and same and baseline_rows == current_rows
    baseline_summary = _first_row(baseline_dir / "summary.csv")
    current_summary = _first_row(current_dir / "summary.csv")
    baseline_episode = _first_row(baseline_dir / "per_episode.csv")
    current_episode = _first_row(current_dir / "per_episode.csv")
    return {
        "label": label,
        "passed": passed,
        "files": files,
        "baseline_final_coverage": baseline_summary.get("final_coverage_mean")
        or baseline_summary.get("mean_final_coverage")
        or baseline_episode.get("final_coverage"),
        "current_final_coverage": current_summary.get("final_coverage_mean")
        or current_summary.get("mean_final_coverage")
        or current_episode.get("final_coverage"),
        "baseline_coverage_auc": baseline_summary.get("coverage_auc_mean")
        or baseline_summary.get("mean_coverage_auc")
        or baseline_episode.get("coverage_auc"),
        "current_coverage_auc": current_summary.get("coverage_auc_mean")
        or current_summary.get("mean_coverage_auc")
        or current_episode.get("coverage_auc"),
        "baseline_episode_length": baseline_summary.get("episode_steps_mean") or baseline_episode.get("steps"),
        "current_episode_length": current_summary.get("episode_steps_mean") or current_episode.get("steps"),
        "baseline_budget_trigger_count": baseline_summary.get("budget_trigger_count_mean", ""),
        "current_budget_trigger_count": current_summary.get("budget_trigger_count_mean", ""),
    }


def _newly_covered_count(history_path: Path) -> int:
    rows = _read_csv(history_path)
    seen: set[tuple[int, int, int, int]] = set()
    for row in rows:
        episode = _as_int(row.get("episode"), 0)
        env_id = _as_int(row.get("env_id"), 0)
        step = _as_int(row.get("step"), 0)
        for target in _json_list(row.get("newly_covered_viewpoint_ids")):
            seen.add((episode, env_id, step, _as_int(target, -1)))
    return len(seen)


def _budget_rows_from_history(history_path: Path) -> list[dict[str, int]]:
    rows = _read_csv(history_path)
    result = []
    for row in rows:
        budget = _as_bool(row.get("budget_triggered_by_budget")) or _as_bool(row.get("budget_triggered_after_step"))
        if not budget:
            continue
        step = _as_int(row.get("step"), 0)
        event_step = step - 1 if row.get("method") == "rl_checkpoint" else step
        result.append(
            {
                "env_id": _as_int(row.get("env_id"), 0),
                "event_step": event_step,
                "robot_id": _as_int(row.get("robot_id") or row.get("agent_id"), -1),
            }
        )
    return result


def _proposal_effective_explanations(rows: list[dict[str, str]]) -> dict[str, Any]:
    counts = Counter()
    unexplained: list[dict[str, Any]] = []
    changed_total = 0
    for row in rows:
        proposal = _json_int_list(row.get("assignment_proposal"))
        effective = _json_int_list(row.get("effective_assignment"))
        changed_flags = _json_bool_list(row.get("proposal_effective_changed"))
        continued = _json_bool_list(row.get("continued_from_active_target"))
        switch_rejected = _json_bool_list(row.get("switch_rejected"))
        claim_loser = _json_bool_list(row.get("claim_loser"))
        rejected = _json_int_list(row.get("proposal_rejected_reason"))
        robot_count = min(len(proposal), len(effective), len(changed_flags))
        for robot_id in range(robot_count):
            actual_changed = proposal[robot_id] != effective[robot_id]
            if bool(changed_flags[robot_id]) != actual_changed:
                counts["changed_flag_mismatch"] += 1
            if not actual_changed:
                continue
            changed_total += 1
            reason = REJECT_NONE
            if robot_id < len(rejected):
                reason = int(rejected[robot_id])
            if proposal[robot_id] < 0 and robot_id < len(continued) and continued[robot_id]:
                counts["noop_continuation"] += 1
            elif robot_id < len(switch_rejected) and switch_rejected[robot_id]:
                counts["switch_rejected"] += 1
            elif robot_id < len(claim_loser) and claim_loser[robot_id]:
                counts["claim_lost"] += 1
            elif reason == REJECT_OWNED_TARGET:
                counts["owned_target_rejected"] += 1
            elif reason == REJECT_COVERED_TARGET:
                counts["covered_target_rejected"] += 1
            elif reason == REJECT_FAILED_PAIR:
                counts["failed_pair_reclaim_rejected"] += 1
            elif reason == REJECT_CLAIM_LOST:
                counts["claim_lost"] += 1
            elif reason == REJECT_SWITCH_DISABLED:
                counts["switch_rejected"] += 1
            elif reason == REJECT_UNAVAILABLE_TARGET:
                counts["unavailable_target_rejected"] += 1
            else:
                unexplained.append(
                    {
                        "env_id": row.get("env_id"),
                        "step": row.get("step"),
                        "robot_id": robot_id,
                        "proposal": proposal[robot_id],
                        "effective": effective[robot_id],
                        "rejected_reason": reason,
                    }
                )
    return {
        "changed_total": changed_total,
        "counts_by_reason": dict(counts),
        "unexplained_count": len(unexplained),
        "unexplained_sample": unexplained[:20],
        "changed_flag_mismatch_count": int(counts.get("changed_flag_mismatch", 0)),
    }


def _ownership_invariants(rows: list[dict[str, str]], *, num_robots: int, num_tasks: int) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        active = _json_int_list(row.get("active_target_after"))
        owners = _json_int_list(row.get("task_owner_after"))
        if len(active) != num_robots:
            failures.append({"step": row.get("step"), "reason": "active_target_shape", "value": active})
        if len(owners) != num_tasks:
            failures.append({"step": row.get("step"), "reason": "task_owner_shape", "length": len(owners)})
        for robot_id, target_id in enumerate(active[:num_robots]):
            if target_id < -1 or target_id >= num_tasks:
                failures.append({"step": row.get("step"), "robot_id": robot_id, "reason": "active_target_out_of_range"})
            if target_id >= 0 and target_id < len(owners) and owners[target_id] != robot_id:
                failures.append(
                    {
                        "step": row.get("step"),
                        "robot_id": robot_id,
                        "target_id": target_id,
                        "owner": owners[target_id],
                        "reason": "active_target_owner_mismatch",
                    }
                )
        for target_id, owner in enumerate(owners[:num_tasks]):
            if owner < -1 or owner >= num_robots:
                failures.append({"step": row.get("step"), "target_id": target_id, "reason": "owner_out_of_range"})
    return {
        "passed": not failures,
        "failure_count": len(failures),
        "failure_sample": failures[:20],
    }


def _reset_order_ok(events: list[dict[str, Any]]) -> dict[str, Any]:
    problems = []
    previous_by_env: dict[int, str] = {}
    for event in events:
        env_id = _as_int(event.get("env_id"), 0)
        event_type = str(event.get("event_type", ""))
        if event_type == "reset" and _as_int(event.get("step"), 0) > 0:
            previous = previous_by_env.get(env_id)
            if previous is None:
                problems.append({"env_id": env_id, "step": event.get("step"), "reason": "reset_without_prior_event"})
        else:
            previous_by_env[env_id] = event_type
    return {"passed": not problems, "failure_count": len(problems), "failure_sample": problems[:20]}


def _passive_stream_check(root: Path, label: str, resolver_rows: list[dict[str, str]]) -> dict[str, Any]:
    events_path, summary_path = _passive_paths(root, label)
    if not events_path.exists() or not summary_path.exists():
        return {"available": False, "passed": False, "reason": "missing_passive_output"}
    events = _load_jsonl(events_path)
    transition_events = [event for event in events if event.get("event_type") != "reset_proxy"]
    proposal_types = sorted({str(event.get("proposal_type")) for event in transition_events})
    reset_proposal_types = sorted(
        {str(event.get("proposal_type")) for event in events if event.get("event_type") == "reset_proxy"}
    )
    return {
        "available": True,
        "passed": proposal_types == ["effective_assignment_from_resolver"],
        "proposal_types": proposal_types,
        "reset_proposal_types": reset_proposal_types,
        "event_count": len(events),
        "transition_event_count": len(transition_events),
        "resolver_row_count": len(resolver_rows),
    }


def _load_enabled_run(root: Path, label: str) -> dict[str, Any]:
    events_path, summary_path, rows_path = _resolver_paths(root, label)
    missing = [str(path) for path in (events_path, summary_path, rows_path) if not path.exists()]
    if missing:
        return {"label": label, "available": False, "missing": missing, "passed": False}
    events = _load_jsonl(events_path)
    summary = _read_json(summary_path)
    rows = _read_csv(rows_path)
    event_counts = Counter(str(event.get("event_type")) for event in events)
    common_event_keys_ok = all(REQUIRED_EVENT_KEYS.issubset(set(event.keys())) for event in events)
    row_fields_ok = list(rows[0].keys()) == REQUIRED_ROW_FIELDS if rows else False
    total_events_ok = _as_int(summary.get("total_events"), -1) == len(events)
    summary_event_count_ok = True
    mismatched_counts: dict[str, Any] = {}
    for event_type, count in event_counts.items():
        key = f"{event_type}_count"
        if key in summary and _as_int(summary.get(key), -1) != int(count):
            summary_event_count_ok = False
            mismatched_counts[key] = {"summary": summary.get(key), "parsed": int(count)}
    changed = _proposal_effective_explanations(rows)
    ownership = _ownership_invariants(
        rows,
        num_robots=_as_int(summary.get("num_robots"), 3),
        num_tasks=_as_int(summary.get("num_tasks"), 50),
    )
    completion_events = int(event_counts.get("target_completed", 0))
    newly_covered = _newly_covered_count(root / label / "assignment_history.csv")
    budget_events = [event for event in events if event.get("event_type") == "budget_failure"]
    release_events = [event for event in events if event.get("event_type") == "release_budget_failure"]
    budget_targets_ok = all(
        event.get("target_id") == event.get("effective_assignment_for_robot")
        for event in budget_events
        if event.get("effective_assignment_for_robot") is not None
    )
    reset_order = _reset_order_ok(events)
    passive_stream = _passive_stream_check(root, label, rows)
    monitor_events = [
        event
        for event in events
        if str(event.get("event_type")) in {"stranded_failed_pair_started", "stranded_failed_pair_recovered"}
    ]
    monitors_behavior_neutral = all(not _as_bool(event.get("behavior_changed")) for event in monitor_events)
    passed = (
        common_event_keys_ok
        and row_fields_ok
        and total_events_ok
        and summary_event_count_ok
        and changed["unexplained_count"] == 0
        and changed["changed_flag_mismatch_count"] == 0
        and ownership["passed"]
        and completion_events == newly_covered
        and len(release_events) == len(budget_events)
        and budget_targets_ok
        and reset_order["passed"]
        and passive_stream["passed"]
        and monitors_behavior_neutral
    )
    return {
        "label": label,
        "available": True,
        "passed": passed,
        "events_path": str(events_path),
        "summary_path": str(summary_path),
        "rows_path": str(rows_path),
        "schema_version": summary.get("schema_version"),
        "method_name": summary.get("method_name"),
        "num_envs": _as_int(summary.get("num_envs"), -1),
        "num_robots": _as_int(summary.get("num_robots"), -1),
        "num_tasks": _as_int(summary.get("num_tasks"), -1),
        "total_events": len(events),
        "total_events_ok": total_events_ok,
        "common_event_keys_ok": common_event_keys_ok,
        "row_fields_ok": row_fields_ok,
        "summary_event_count_ok": summary_event_count_ok,
        "mismatched_event_counts": mismatched_counts,
        "summary": summary,
        "event_counts": dict(event_counts),
        "proposal_effective": changed,
        "ownership": ownership,
        "newly_covered_count": newly_covered,
        "target_completed_event_count": completion_events,
        "completion_consistent": completion_events == newly_covered,
        "budget_failure_count": len(budget_events),
        "release_budget_failure_count": len(release_events),
        "budget_release_count_consistent": len(release_events) == len(budget_events),
        "budget_effective_target_consistent": budget_targets_ok,
        "reset_order": reset_order,
        "passive_stream": passive_stream,
        "active_target_infeasible_step_count": _as_int(summary.get("active_target_infeasible_step_count"), 0),
        "active_target_infeasible_max_streak": _as_int(summary.get("active_target_infeasible_max_streak"), 0),
        "stranded_failed_pair_started_count": _as_int(summary.get("stranded_failed_pair_started_count"), 0),
        "stranded_failed_pair_recovered_count": _as_int(summary.get("stranded_failed_pair_recovered_count"), 0),
        "stranded_failed_pair_max_streak": _as_int(summary.get("stranded_failed_pair_max_streak"), 0),
        "monitor_events_behavior_neutral": monitors_behavior_neutral,
    }


def _disabled_resolver_empty(root: Path) -> dict[str, Any]:
    results = {}
    for label in ("rl_disabled", "nearest_disabled"):
        base = root / label / "resolver"
        if base.exists():
            files = [str(path.relative_to(base)) for path in base.rglob("*") if path.is_file()]
        else:
            files = []
        results[label] = {"passed": not files, "resolver_files": files}
    return results


def _identity_rows(identity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in identity:
        row = {
            "label": item["label"],
            "passed": item["passed"],
            "baseline_final_coverage": item["baseline_final_coverage"],
            "current_final_coverage": item["current_final_coverage"],
            "baseline_coverage_auc": item["baseline_coverage_auc"],
            "current_coverage_auc": item["current_coverage_auc"],
            "baseline_episode_length": item["baseline_episode_length"],
            "current_episode_length": item["current_episode_length"],
            "baseline_budget_trigger_count": item["baseline_budget_trigger_count"],
            "current_budget_trigger_count": item["current_budget_trigger_count"],
        }
        for file_name in CORE_FILES:
            file_result = item["files"].get(file_name, {})
            key = file_name.replace(".csv", "")
            row[f"{key}_same_sha256"] = file_result.get("same_sha256")
            row[f"{key}_baseline_rows"] = file_result.get("baseline_rows")
            row[f"{key}_current_rows"] = file_result.get("current_rows")
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--baseline_root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument("--output_dir", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    baseline_root = args.baseline_root.expanduser().resolve()
    output_dir = (args.output_dir or (root / "comparison")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    identity = [
        _compare_core_files(label, baseline_root / baseline_label, root / label)
        for label, baseline_label in DISABLED_IDENTITY_PAIRS
    ]
    disabled_empty = _disabled_resolver_empty(root)
    enabled = [_load_enabled_run(root, label) for label in ENABLED_RUNS]

    identity_ok = all(item["passed"] for item in identity)
    disabled_empty_ok = all(item["passed"] for item in disabled_empty.values())
    enabled_available = all(item.get("available") for item in enabled)
    enabled_ok = enabled_available and all(item.get("passed") for item in enabled)
    schema_versions = sorted({str(item.get("schema_version")) for item in enabled if item.get("available")})
    output_paths = []
    for item in enabled:
        for key in ("events_path", "summary_path", "rows_path"):
            if item.get(key):
                output_paths.append(str(item[key]))
    output_isolation_ok = len(output_paths) == len(set(output_paths))

    classification = "PASS"
    if not identity_ok or not disabled_empty_ok or not enabled_ok or not output_isolation_ok:
        classification = "FAIL"
    if not enabled_available:
        classification = "INCONCLUSIVE"

    summary = {
        "classification": classification,
        "root": str(root),
        "baseline_root": str(baseline_root),
        "output_dir": str(output_dir),
        "identity_ok": identity_ok,
        "disabled_resolver_empty_ok": disabled_empty_ok,
        "enabled_available": enabled_available,
        "enabled_semantics_ok": enabled_ok,
        "schema_versions": schema_versions,
        "schema_version_ok": schema_versions == [RESOLVER_SCHEMA_VERSION],
        "output_isolation_ok": output_isolation_ok,
        "identity": identity,
        "disabled_resolver_empty": disabled_empty,
        "enabled_runs": enabled,
    }

    table_rows = []
    for item in enabled:
        summary_payload = item.get("summary", {}) if isinstance(item.get("summary"), dict) else {}
        episode = _first_row(root / str(item.get("label")) / "per_episode.csv")
        table_rows.append(
            {
                "run": item.get("label"),
                "resolver": "enabled",
                "final_coverage": episode.get("final_coverage", ""),
                "auc": episode.get("coverage_auc", ""),
                "episode_length": episode.get("steps", ""),
                "proposal_effective_changed": item.get("proposal_effective", {}).get("changed_total", ""),
                "noop_continue": item.get("proposal_effective", {}).get("counts_by_reason", {}).get("noop_continuation", 0),
                "switch_rejected": summary_payload.get("switch_rejected_executing_count", 0),
                "budget_release": item.get("release_budget_failure_count", 0),
                "infeasible_max_streak": item.get("active_target_infeasible_max_streak", 0),
                "stranded_max_streak": item.get("stranded_failed_pair_max_streak", 0),
                "result": "PASS" if item.get("passed") else "FAIL",
            }
        )

    _write_json(output_dir / "phase9g7e_validation_summary.json", summary)
    _write_csv(output_dir / "phase9g7e_validation_summary.csv", _identity_rows(identity), [
        "label",
        "passed",
        "baseline_final_coverage",
        "current_final_coverage",
        "baseline_coverage_auc",
        "current_coverage_auc",
        "baseline_episode_length",
        "current_episode_length",
        "baseline_budget_trigger_count",
        "current_budget_trigger_count",
        "assignment_history_same_sha256",
        "assignment_history_baseline_rows",
        "assignment_history_current_rows",
        "per_episode_same_sha256",
        "per_episode_baseline_rows",
        "per_episode_current_rows",
        "summary_same_sha256",
        "summary_baseline_rows",
        "summary_current_rows",
    ])
    _write_csv(output_dir / "phase9g7e_enabled_runtime_table.csv", table_rows, [
        "run",
        "resolver",
        "final_coverage",
        "auc",
        "episode_length",
        "proposal_effective_changed",
        "noop_continue",
        "switch_rejected",
        "budget_release",
        "infeasible_max_streak",
        "stranded_max_streak",
        "result",
    ])

    print(json.dumps({"status": classification, **summary}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
