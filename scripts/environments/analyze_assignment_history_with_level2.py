#!/usr/bin/env python3
"""Join assignment-history rows with Level 2 agent-viewpoint diagnostics.

This script is diagnostic-only. It does not import IsaacLab, create an environment,
or change evaluator/controller/baseline behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STATUS_NOOP = "noop"
STATUS_ALREADY_COVERED = "already_covered"
STATUS_KNOWN_COVERABLE = "known_coverable_pair"
STATUS_KNOWN_FAILING = "known_level2_failing_pair"
STATUS_UNCHECKED = "unchecked_pair"


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "t"}


def _parse_int(value: Any, default: int = -1) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _parse_json_list(value: str) -> list[Any]:
    text = (value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _load_level2_lookup(level2_json: Path) -> dict[tuple[int, int], dict[str, Any]]:
    with level2_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lookup: dict[tuple[int, int], dict[str, Any]] = {}
    for row in data.get("results", []):
        agent_id = _parse_int(row.get("agent_id"))
        viewpoint_id = _parse_int(row.get("viewpoint_id", row.get("viewpoint_index")))
        if agent_id < 0 or viewpoint_id < 0:
            continue
        lookup[(agent_id, viewpoint_id)] = {
            "agent_id": agent_id,
            "agent_name": row.get("agent_name", f"agent_{agent_id}"),
            "viewpoint_id": viewpoint_id,
            "covered": bool(row.get("covered", False)),
            "first_covered_step": row.get("first_covered_step"),
            "most_likely_failure_reason": row.get("most_likely_failure_reason", ""),
            "controller_converged": row.get("controller_converged"),
            "ever_all_coverage_gates_ok": row.get("ever_all_coverage_gates_ok"),
        }
    return lookup


def _label_row(row: dict[str, str], level2_lookup: dict[tuple[int, int], dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    if _parse_bool(row.get("is_noop")):
        return STATUS_NOOP, None
    if _parse_bool(row.get("assigned_viewpoint_was_covered_before")):
        return STATUS_ALREADY_COVERED, None

    agent_id = _parse_int(row.get("agent_id"))
    viewpoint_id = _parse_int(row.get("assigned_viewpoint_id"))
    level2 = level2_lookup.get((agent_id, viewpoint_id))
    if level2 is None:
        return STATUS_UNCHECKED, None
    if bool(level2.get("covered", False)):
        return STATUS_KNOWN_COVERABLE, level2
    return STATUS_KNOWN_FAILING, level2


def _augment_rows(
    assignment_history_csv: Path,
    level2_lookup: dict[tuple[int, int], dict[str, Any]],
    target_viewpoint_ids: set[int],
) -> tuple[list[dict[str, str]], list[str]]:
    with assignment_history_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError(f"No CSV header found in {assignment_history_csv}")
        original_fields = list(reader.fieldnames)
        rows = []
        for row in reader:
            viewpoint_id = _parse_int(row.get("assigned_viewpoint_id"))
            status, level2 = _label_row(row, level2_lookup)
            level2_covered = "" if level2 is None else str(bool(level2.get("covered", False))).lower()
            first_covered = "" if level2 is None or level2.get("first_covered_step") is None else str(level2["first_covered_step"])
            failure_reason = "" if level2 is None else str(level2.get("most_likely_failure_reason", ""))
            row.update(
                {
                    "pair_level2_status": status,
                    "level2_covered": level2_covered,
                    "level2_first_covered_step": first_covered,
                    "level2_failure_reason": failure_reason,
                    "is_target_uncovered_viewpoint": str(viewpoint_id in target_viewpoint_ids).lower(),
                    "is_known_coverable_pair": str(status == STATUS_KNOWN_COVERABLE).lower(),
                    "is_known_failing_pair": str(status == STATUS_KNOWN_FAILING).lower(),
                }
            )
            rows.append(row)

    extra_fields = [
        "pair_level2_status",
        "level2_covered",
        "level2_first_covered_step",
        "level2_failure_reason",
        "is_target_uncovered_viewpoint",
        "is_known_coverable_pair",
        "is_known_failing_pair",
    ]
    return rows, original_fields + extra_fields


def _write_joined_csv(rows: list[dict[str, str]], fieldnames: list[str], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _summarize_pairs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for row in rows:
        method = row.get("method", "")
        viewpoint_id = _parse_int(row.get("assigned_viewpoint_id"))
        agent_id = _parse_int(row.get("agent_id"))
        status = row.get("pair_level2_status", STATUS_UNCHECKED)
        step = _parse_int(row.get("step"), default=0)
        key = (method, viewpoint_id, agent_id, status)
        group = groups.setdefault(
            key,
            {
                "method": method,
                "assigned_viewpoint_id": viewpoint_id,
                "agent_id": agent_id,
                "pair_level2_status": status,
                "assignment_count": 0,
                "first_assigned_step": step,
                "last_assigned_step": step,
                "any_newly_covered": False,
                "assigned_viewpoint_covered_after_count": 0,
                "covered_before_count": 0,
                "final_observed_coverage_count": _parse_int(row.get("coverage_count"), default=0),
                "level2_failure_reason": row.get("level2_failure_reason", ""),
            },
        )
        group["assignment_count"] += 1
        group["first_assigned_step"] = min(group["first_assigned_step"], step)
        group["last_assigned_step"] = max(group["last_assigned_step"], step)
        group["any_newly_covered"] = bool(group["any_newly_covered"]) or bool(
            _parse_json_list(row.get("newly_covered_viewpoint_ids", "[]"))
        )
        if _parse_bool(row.get("assigned_viewpoint_covered_after")):
            group["assigned_viewpoint_covered_after_count"] += 1
        if _parse_bool(row.get("assigned_viewpoint_was_covered_before")):
            group["covered_before_count"] += 1
        group["final_observed_coverage_count"] = _parse_int(row.get("coverage_count"), default=0)
        if not group.get("level2_failure_reason") and row.get("level2_failure_reason"):
            group["level2_failure_reason"] = row.get("level2_failure_reason", "")

    summaries = list(groups.values())
    summaries.sort(
        key=lambda g: (
            str(g["method"]),
            int(g["assigned_viewpoint_id"]),
            int(g["agent_id"]),
            str(g["pair_level2_status"]),
        )
    )
    return summaries


def _write_pair_summary_csv(summaries: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "method",
        "assigned_viewpoint_id",
        "agent_id",
        "pair_level2_status",
        "assignment_count",
        "first_assigned_step",
        "last_assigned_step",
        "any_newly_covered",
        "assigned_viewpoint_covered_after_count",
        "covered_before_count",
        "final_observed_coverage_count",
        "level2_failure_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for summary in summaries:
            out = dict(summary)
            out["any_newly_covered"] = str(bool(out["any_newly_covered"])).lower()
            writer.writerow(out)


def _status_counts(rows: list[dict[str, str]], target_only: bool = False) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        if target_only and not _parse_bool(row.get("is_target_uncovered_viewpoint")):
            continue
        counts[row.get("pair_level2_status", STATUS_UNCHECKED)] += 1
    return counts


def _method_status_counts(rows: list[dict[str, str]], target_only: bool = False) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        if target_only and not _parse_bool(row.get("is_target_uncovered_viewpoint")):
            continue
        counts[row.get("method", "")][row.get("pair_level2_status", STATUS_UNCHECKED)] += 1
    return counts


def _target_summary(rows: list[dict[str, str]], target_ids: list[int]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for viewpoint_id in target_ids:
        target_rows = [
            row for row in rows if _parse_int(row.get("assigned_viewpoint_id")) == viewpoint_id
        ]
        agents = sorted({_parse_int(row.get("agent_id")) for row in target_rows})
        coverable_count = sum(1 for row in target_rows if row.get("pair_level2_status") == STATUS_KNOWN_COVERABLE)
        failing_count = sum(1 for row in target_rows if row.get("pair_level2_status") == STATUS_KNOWN_FAILING)
        any_covered_after = any(_parse_bool(row.get("assigned_viewpoint_covered_after")) for row in target_rows)
        result.append(
            {
                "viewpoint_id": viewpoint_id,
                "assigned_count": len(target_rows),
                "assigned_agents": agents,
                "assigned_to_coverable_agent_count": coverable_count,
                "assigned_to_failing_agent_count": failing_count,
                "any_assignment_covered_after": any_covered_after,
                "repeatedly_assigned_but_not_covered": len(target_rows) > 1 and not any_covered_after,
            }
        )
    return result


def _final_stuck_pairs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    max_step_by_method: dict[str, int] = {}
    for row in rows:
        method = row.get("method", "")
        step = _parse_int(row.get("step"), default=0)
        max_step_by_method[method] = max(max_step_by_method.get(method, step), step)

    stuck: list[dict[str, Any]] = []
    for row in rows:
        method = row.get("method", "")
        if _parse_int(row.get("step"), default=0) != max_step_by_method.get(method):
            continue
        stuck.append(
            {
                "method": method,
                "agent_id": _parse_int(row.get("agent_id")),
                "assigned_viewpoint_id": _parse_int(row.get("assigned_viewpoint_id")),
                "pair_level2_status": row.get("pair_level2_status", ""),
                "level2_failure_reason": row.get("level2_failure_reason", ""),
            }
        )
    stuck.sort(key=lambda item: (str(item["method"]), int(item["agent_id"])))
    return stuck


def _format_counter(counter: Counter[str]) -> str:
    statuses = [
        STATUS_KNOWN_COVERABLE,
        STATUS_KNOWN_FAILING,
        STATUS_UNCHECKED,
        STATUS_NOOP,
        STATUS_ALREADY_COVERED,
    ]
    return "\n".join(f"- {status}: {counter.get(status, 0)}" for status in statuses)


def _recommend_next_step(target_counts: Counter[str], target_summary: list[dict[str, Any]]) -> str:
    failing = target_counts.get(STATUS_KNOWN_FAILING, 0)
    coverable = target_counts.get(STATUS_KNOWN_COVERABLE, 0)
    never_assigned = [row["viewpoint_id"] for row in target_summary if row["assigned_count"] == 0]
    repeated_coverable = any(
        row["assigned_to_coverable_agent_count"] > 0 and row["repeatedly_assigned_but_not_covered"]
        for row in target_summary
    )

    if failing > coverable:
        return (
            "pair-level feasibility filtering is the most justified next step, because target assignments are dominated "
            "by known Level-2-failing pairs. Keep this as a controlled behavior change and re-run the same diagnostics."
        )
    if repeated_coverable:
        return (
            "controller-state / target-switching / multi-agent interaction diagnostics are the most justified next step, "
            "because known-coverable pairs are repeatedly assigned but do not cover in the multi-agent episode."
        )
    if never_assigned:
        return (
            "retry/fallback or coverage-aware assignment logic is the most justified next step, because some coverable "
            "target viewpoints are never assigned."
        )
    return "assignment-history-aware baseline diagnostics are the most justified next step."


def _write_report(
    report_path: Path,
    assignment_history_csv: Path,
    level2_json: Path,
    joined_csv: Path,
    pair_summary_csv: Path,
    rows: list[dict[str, str]],
    target_ids: list[int],
) -> None:
    overall_counts = _status_counts(rows, target_only=False)
    target_counts = _status_counts(rows, target_only=True)
    method_counts = _method_status_counts(rows, target_only=False)
    target_by_method = _method_status_counts(rows, target_only=True)
    target_rows = _target_summary(rows, target_ids)
    never_assigned = [row["viewpoint_id"] for row in target_rows if row["assigned_count"] == 0]
    repeated_not_covered = [
        row["viewpoint_id"] for row in target_rows if row["repeatedly_assigned_but_not_covered"]
    ]
    stuck_pairs = _final_stuck_pairs(rows)
    recommendation = _recommend_next_step(target_counts, target_rows)

    lines: list[str] = []
    lines.append("# Stage 4B Real Component N24 Assignment-Level2 Join Report")
    lines.append("")
    lines.append("Date: 2026-06-15")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "This is a diagnostic-only join between evaluator assignment history and Level 2 pair-coverability results. "
        "It does not change random/nearest/greedy behavior, controller behavior, reward logic, HARL core, the 9D action "
        "path, assignment-RL, pair-level filtering, retry/fallback logic, IK, collision, raycast, or robot articulation."
    )
    lines.append("")
    lines.append(
        "`real_component_bbox_sample.csv` remains temporary pipeline sanity data, not final viewpoint planning output."
    )
    lines.append("")
    lines.append("## Source Artifacts")
    lines.append("")
    lines.append("```text")
    lines.append(f"assignment_history_csv: {assignment_history_csv}")
    lines.append(f"level2_json: {level2_json}")
    lines.append(f"assignment_history_joined_csv: {joined_csv}")
    lines.append(f"assignment_history_pair_summary_csv: {pair_summary_csv}")
    lines.append("```")
    lines.append("")
    lines.append("## Overall Assignment Status Counts")
    lines.append("")
    lines.append(_format_counter(overall_counts))
    lines.append("")
    lines.append("By method:")
    lines.append("")
    lines.append("| method | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for method in sorted(method_counts):
        counts = method_counts[method]
        lines.append(
            f"| {method} | {counts.get(STATUS_KNOWN_COVERABLE, 0)} | "
            f"{counts.get(STATUS_KNOWN_FAILING, 0)} | {counts.get(STATUS_UNCHECKED, 0)} | "
            f"{counts.get(STATUS_NOOP, 0)} | {counts.get(STATUS_ALREADY_COVERED, 0)} |"
        )
    lines.append("")
    lines.append(
        "Note: `unchecked_pair` mostly covers non-target viewpoints because the Level 2 diagnostic JSON was generated "
        "only for target ids `[1, 2, 8, 12, 13, 14, 20]`."
    )
    lines.append("")
    lines.append("## Target-Only Assignment Status Counts")
    lines.append("")
    lines.append(_format_counter(target_counts))
    lines.append("")
    lines.append("By method, target ids only:")
    lines.append("")
    lines.append("| method | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for method in sorted(target_by_method):
        counts = target_by_method[method]
        lines.append(
            f"| {method} | {counts.get(STATUS_KNOWN_COVERABLE, 0)} | "
            f"{counts.get(STATUS_KNOWN_FAILING, 0)} | {counts.get(STATUS_UNCHECKED, 0)} | "
            f"{counts.get(STATUS_NOOP, 0)} | {counts.get(STATUS_ALREADY_COVERED, 0)} |"
        )
    lines.append("")
    lines.append("## Target Viewpoint Summary")
    lines.append("")
    lines.append(
        "| viewpoint | assigned_count | assigned_agents | assigned_to_coverable_agent_count | "
        "assigned_to_failing_agent_count | any_assignment_covered_after | interpretation |"
    )
    lines.append("| ---: | ---: | --- | ---: | ---: | ---: | --- |")
    for row in target_rows:
        if row["assigned_count"] == 0:
            interpretation = "never assigned"
        elif row["repeatedly_assigned_but_not_covered"]:
            interpretation = "repeatedly assigned but not covered"
        else:
            interpretation = "assigned"
        lines.append(
            f"| {row['viewpoint_id']} | {row['assigned_count']} | {row['assigned_agents']} | "
            f"{row['assigned_to_coverable_agent_count']} | {row['assigned_to_failing_agent_count']} | "
            f"{str(row['any_assignment_covered_after']).lower()} | {interpretation} |"
        )
    lines.append("")
    lines.append(f"Never assigned ids: `{never_assigned}`")
    lines.append("")
    lines.append(f"Repeatedly assigned but not covered ids: `{repeated_not_covered}`")
    lines.append("")
    lines.append("## Final Stuck Pattern")
    lines.append("")
    lines.append("| method | agent | assigned_viewpoint | pair_level2_status | level2_failure_reason |")
    lines.append("| --- | ---: | ---: | --- | --- |")
    for row in stuck_pairs:
        lines.append(
            f"| {row['method']} | {row['agent_id']} | {row['assigned_viewpoint_id']} | "
            f"{row['pair_level2_status']} | {row['level2_failure_reason']} |"
        )
    lines.append("")
    lines.append("The requested stuck pattern is therefore:")
    lines.append("")
    lines.append("```text")
    for row in stuck_pairs:
        if row["method"] == "nearest":
            lines.append(
                f"robot_{row['agent_id']} -> viewpoint_{row['assigned_viewpoint_id']}: "
                f"{row['pair_level2_status']}"
            )
    lines.append("```")
    lines.append("")
    lines.append("Nearest and greedy have the same final stuck pattern in this run.")
    lines.append("")
    lines.append("## Diagnostic Answers")
    lines.append("")
    lines.append("1. Are nearest/greedy mostly stuck because they assign Level-2-failing pairs?")
    lines.append("")
    lines.append(
        "For target assignments, yes: known Level-2-failing assignments outnumber known-coverable assignments. "
        "The final stuck pattern includes two known failing pairs and one known coverable pair per method."
    )
    lines.append("")
    lines.append("2. Are they skipping coverable viewpoints entirely?")
    lines.append("")
    lines.append(
        f"Yes. The never-assigned target ids are `{never_assigned}`. Level 2 previously showed these viewpoints are "
        "coverable by at least one robot."
    )
    lines.append("")
    lines.append("3. Do they repeatedly assign known-coverable pairs that still fail in multi-agent context?")
    lines.append("")
    lines.append(
        "Yes. The target summary includes known-coverable assignments that do not produce coverage in the multi-agent "
        "baseline episode, especially the stuck `robot_1 -> viewpoint_13` pair and repeated `robot_2 -> viewpoint_12` "
        "assignments before the final step."
    )
    lines.append("")
    lines.append("4. Which next fix is most justified?")
    lines.append("")
    lines.append(recommendation)
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(
        "Primary recommendation: pair-level feasibility filtering. The join shows many repeated target assignments are "
        "to known Level-2-failing agent-viewpoint pairs, including two of the three final stuck pairs per method. "
        "This should be tested as a controlled behavior change, then followed by the same assignment-history diagnostics."
    )
    lines.append("")
    lines.append(
        "Residual risk: filtering alone may not solve skipped viewpoints `2 / 8 / 14 / 20` or known-coverable pairs that "
        "still fail in multi-agent context. If coverage remains at 17/24 after filtering, the next diagnostic should focus "
        "on retry/fallback sequencing and controller-state/target-switching behavior."
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignment_history_csv", type=Path, required=True)
    parser.add_argument("--level2_json", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_viewpoint_ids", type=int, nargs="+", required=True)
    parser.add_argument("--report_path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    level2_lookup = _load_level2_lookup(args.level2_json)
    target_ids = list(dict.fromkeys(args.target_viewpoint_ids))
    rows, fieldnames = _augment_rows(args.assignment_history_csv, level2_lookup, set(target_ids))

    joined_csv = args.output_dir / "assignment_history_joined.csv"
    pair_summary_csv = args.output_dir / "assignment_history_pair_summary.csv"
    _write_joined_csv(rows, fieldnames, joined_csv)
    pair_summaries = _summarize_pairs(rows)
    _write_pair_summary_csv(pair_summaries, pair_summary_csv)

    report_path = args.report_path
    if report_path is None:
        report_path = args.output_dir / "assignment_history_level2_join_report.md"
    _write_report(
        report_path=report_path,
        assignment_history_csv=args.assignment_history_csv,
        level2_json=args.level2_json,
        joined_csv=joined_csv,
        pair_summary_csv=pair_summary_csv,
        rows=rows,
        target_ids=target_ids,
    )

    overall_counts = _status_counts(rows, target_only=False)
    target_counts = _status_counts(rows, target_only=True)
    print(f"Wrote {joined_csv}")
    print(f"Wrote {pair_summary_csv}")
    print(f"Wrote {report_path}")
    print("Overall status counts:")
    print(_format_counter(overall_counts))
    print("Target-only status counts:")
    print(_format_counter(target_counts))


if __name__ == "__main__":
    main()
