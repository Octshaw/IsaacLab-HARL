"""Exactly-30-update real-Isaac stability qualification for Phase B2-T1.

This test-side harness deliberately derives its transaction engine from the
qualified B2-T0-RE1 harness after verifying that source byte-for-byte.  The
small transformation table below changes only the bounded run length,
qualification labels, dynamic 29-bridge accounting, and tx31 stop fields.
Production learner and lifecycle semantics remain owned by the reviewed
modules called by that harness.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Mapping, Sequence


HERE = Path(__file__).resolve().parent
BASE_HARNESS = HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
QUALIFIED_BASE_SHA256 = "a77c5caa8847980973aba718f19e7e1f8533cbb0c6756856272e8d29f5bfb95f"
TRANSACTION_COUNT = 30
SENTINEL_TRANSACTIONS = frozenset((1, 10, 20, 30))
ROLLING_HEALTH_TRANSACTIONS = frozenset((1, 5, 10, 15, 20, 25, 30))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_exact(source: str, old: str, new: str, *, count: int | None = None) -> str:
    observed = source.count(old)
    expected = observed if count is None else count
    if observed != expected or observed == 0:
        raise RuntimeError(
            "STOP — B2-T1 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"replacement {old!r} expected {expected}, observed {observed}"
        )
    return source.replace(old, new)


def _qualified_t1_source() -> str:
    observed = _sha(BASE_HARNESS)
    if observed != QUALIFIED_BASE_SHA256:
        raise RuntimeError(
            "STOP — B2-T1 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"B2-T0-RE1 harness {observed} != {QUALIFIED_BASE_SHA256}"
        )
    source = BASE_HARNESS.read_text(encoding="utf-8")
    source = _replace_exact(
        source,
        '"""Three-update, one-process real-Isaac continuity retry for Phase B2-T0-RE1."""',
        '"""Exactly-30-update real-Isaac stability qualification for Phase B2-T1."""',
        count=1,
    )
    source = _replace_exact(source, "TRANSACTION_COUNT = 3", "TRANSACTION_COUNT = 30", count=1)
    source = _replace_exact(
        source,
        'PASS = (\n    "PHASE-B2-T0-RE1-BOUNDED-REPEATED-UPDATE-CONTINUITY-"\n    "COMPLETE-AWAITING-GPT-REVIEW"\n)',
        'PASS = (\n    "PHASE-B2-T1-BOUNDED-SHORT-TRAINING-STABILITY-"\n    "QUALIFIED-AWAITING-GPT-REVIEW"\n)',
        count=1,
    )
    source = _replace_exact(source, "STOP — B2-T0", "STOP — B2-T1")
    source = _replace_exact(source, "PHASE-B2-T0-RE1-STOP", "PHASE-B2-T1-STOP")
    source = _replace_exact(source, "b2_t0_re1", "b2_t1")
    source = _replace_exact(
        source, "b2-t0-re1-repeated-smoke", "b2-t1-short-training"
    )
    source = _replace_exact(
        source,
        "B2-T0.bounded_repeated_update_smoke",
        "B2-T1.bounded_short_training_stability",
        count=1,
    )
    source = _replace_exact(
        source,
        'f"{run_identity}-tx{transaction_index}"',
        'f"{run_identity}-tx{transaction_index:02d}"',
        count=1,
    )
    source = _replace_exact(
        source,
        'for index in (1, 2)',
        'for index in range(1, TRANSACTION_COUNT)',
        count=1,
    )
    source = _replace_exact(
        source,
        'f"tx{index}_post_to_tx{index + 1}_pre"',
        'f"tx{index:02d}_post_to_tx{index + 1:02d}_pre"',
        count=1,
    )
    source = _replace_exact(
        source, '"fresh_rollout_batches": 3', '"fresh_rollout_batches": TRANSACTION_COUNT', count=1
    )
    source = _replace_exact(source, '"critic_rollovers": 3', '"critic_rollovers": TRANSACTION_COUNT', count=1)
    source = _replace_exact(source, '"ledger_reset_invocations": 3', '"ledger_reset_invocations": TRANSACTION_COUNT', count=1)
    source = _replace_exact(source, '"actor_rollovers": 3 * resolved_M', '"actor_rollovers": TRANSACTION_COUNT * resolved_M', count=1)
    source = _replace_exact(source, "transaction_4_started", "transaction_31_started")
    source = _replace_exact(
        source,
        '"bridge_failed": completed_transactions in (1, 2)',
        '"bridge_failed": 0 < completed_transactions < TRANSACTION_COUNT',
        count=1,
    )
    source = _replace_exact(
        source,
        'Path(tempfile.gettempdir())\n            / "b2_t1_repeated_smoke_20260910_formal01"',
        'Path(tempfile.gettempdir())\n            / "b2_t1_short_training_20260911_formal01"',
        count=1,
    )
    return source


_BASE_NAMESPACE: dict[str, object] = {
    "__name__": "_phase_b2_t1_qualified_base",
    "__file__": str(Path(__file__).resolve()),
    "__package__": None,
}
exec(compile(_qualified_t1_source(), str(BASE_HARNESS), "exec"), _BASE_NAMESPACE)

V2 = _BASE_NAMESPACE["V2"]
_base_atomic_json = _BASE_NAMESPACE["_atomic_json"]
_base_run_worker = _BASE_NAMESPACE["run_worker"]


def _source_identity() -> dict[str, object]:
    repo = {
        name: _sha(_BASE_NAMESPACE["SCAN"] / name)
        for name in _BASE_NAMESPACE["QUALIFIED_REPO_SHA256"]
    }
    installed = {
        name: _sha(_BASE_NAMESPACE["HARL"] / name)
        for name in _BASE_NAMESPACE["QUALIFIED_HARL_SHA256"]
    }
    ld_path = HERE / "_assignment_phase_b2_t0_ld_decision_gate.py"
    test_side = {
        "scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
        : _sha(BASE_HARNESS),
        "scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py": _sha(ld_path),
        "scripts/environments/test_assignment_phase_b2_t1_bounded_short_training_stability.py": _sha(
            Path(__file__).resolve()
        ),
    }
    result = {
        "repo_hashes": repo,
        "installed_harl_hashes": installed,
        "test_side": test_side,
        "qualified_repo_sources_exact": repo
        == _BASE_NAMESPACE["QUALIFIED_REPO_SHA256"],
        "qualified_installed_sources_exact": installed
        == _BASE_NAMESPACE["QUALIFIED_HARL_SHA256"],
        "qualified_ld_helper_exact": _sha(ld_path)
        == _BASE_NAMESPACE["QUALIFIED_LD_HELPER_SHA256"],
        "qualified_re1_harness_exact": (
        test_side[
            "scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
        ]
        == QUALIFIED_BASE_SHA256
        ),
        "t1_harness_identity_recorded": bool(
        test_side[
            "scripts/environments/test_assignment_phase_b2_t1_bounded_short_training_stability.py"
        ]
        ),
    }
    result["pass"] = bool(
        result["qualified_repo_sources_exact"]
        and result["qualified_installed_sources_exact"]
        and result["qualified_ld_helper_exact"]
        and result["qualified_re1_harness_exact"]
    )
    return result


_BASE_NAMESPACE["_source_identity"] = _source_identity

_last_bridge_count = 0
_cumulative = {
    "policy_required_rows": 0,
    "continuation_rows": 0,
    "forced_noop_nondecision_rows": 0,
    "terminal_events": 0,
    "valid_nonzero_update": 0,
    "valid_zero_effective_update": 0,
    "team_reward_sum": 0.0,
}


def _append_jsonl(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(V2.normalize(payload), sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _stats(values: Sequence[object]) -> dict[str, object]:
    floats = tuple(float(value) for value in values)
    return {
        "count": len(floats),
        "min": min(floats) if floats else None,
        "max": max(floats) if floats else None,
        "mean": sum(floats) / len(floats) if floats else None,
        "finite": all(math.isfinite(value) for value in floats),
    }


def _adam_summary(snapshot: Mapping[str, object]) -> dict[str, object]:
    def summarize(rows: Sequence[Sequence[object]]) -> dict[str, object]:
        steps = tuple(int(row[1]) for row in rows)
        return {
            "parameter_count": len(steps),
            "min_step": min(steps) if steps else 0,
            "max_step": max(steps) if steps else 0,
            "distinct_steps": tuple(sorted(set(steps))),
        }

    return {
        "actors": tuple(summarize(rows) for rows in snapshot["actor_adam_steps"]),
        "critic": summarize(snapshot["critic_adam_steps"]),
    }


def _prefix_from_match(path: Path, marker: str) -> Path:
    return path.parent / path.name[: path.name.index(marker)]


def _compact_transaction(path: Path, payload: Mapping[str, object]) -> None:
    normalized = V2.normalize(payload)
    tx = int(normalized["transaction_index"])
    prefix = _prefix_from_match(path, f"_tx{tx}_s10.json")
    lifecycle_rows = tuple(
        row
        for receipt in normalized["lifecycle_decision_gate_receipts"]
        for row in receipt["rows"]
    )
    policy = sum(int(bool(row["decision_required"])) for row in lifecycle_rows)
    continuation = sum(
        int(row["decision_reason"] == "FORCED_CONTINUATION_ROW")
        for row in lifecycle_rows
    )
    noop = sum(
        int(row["decision_reason"] == "FORCED_NOOP_ROW") for row in lifecycle_rows
    )
    counts = dict(normalized["transaction"]["exact_execution_counts"])
    post = normalized["post_update_learner"]
    terminal_count = sum(int(value) for value in normalized["terminal_reason_counts"].values())
    reward = float(normalized["team_reward_sum_diagnostic_only"])
    _cumulative["policy_required_rows"] += policy
    _cumulative["continuation_rows"] += continuation
    _cumulative["forced_noop_nondecision_rows"] += noop
    _cumulative["terminal_events"] += terminal_count
    _cumulative["valid_nonzero_update"] += int(normalized["valid_nonzero"])
    _cumulative["valid_zero_effective_update"] += int(normalized["valid_zero_effective"])
    _cumulative["team_reward_sum"] += reward
    record = {
        "schema_version": "b2_t1_transaction_summary_v1",
        "run_identity": normalized["run_identity"],
        "source_config_identity_digest": normalized["source_config_identity_digest"],
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "actor_order": normalized["actor_order"],
        "rollout_provenance": normalized["rollout_provenance"],
        "rollout_evidence_digest": normalized["rollout_evidence_digest"],
        "lifecycle_rows": {
            "policy_required": policy,
            "continuation": continuation,
            "forced_noop_nondecision": noop,
        },
        "terminal_reason_counts": normalized["terminal_reason_counts"],
        "terminal_event_count": terminal_count,
        "event_return_compute_count": normalized["event_return_compute_count"],
        "stock_compute_returns": normalized["stock_compute_returns"],
        "actor_backward_by_actor": counts["actor_backward_by_actor"],
        "actor_optimizer_step_by_actor": counts["actor_optimizer_step_by_actor"],
        "factor_audits": normalized["factor_segment_count"],
        "critic_minibatches": counts["critic_backward"],
        "critic_backward": counts["critic_backward"],
        "critic_optimizer_step": counts["critic_optimizer_step"],
        "valid_nonzero_update": normalized["valid_nonzero"],
        "valid_zero_effective_update": normalized["valid_zero_effective"],
        "valuenorm_update": counts["live_valuenorm_update"],
        "actor_adam": _adam_summary(post)["actors"],
        "critic_adam": _adam_summary(post)["critic"],
        "s7_pass": normalized["s7_pass"],
        "s8_pass": normalized["s8_pass"],
        "s9_pass": normalized["s9_pass"],
        "s10_pass": normalized["s10_pass"],
        "previous_bridge_status": "NOT_APPLICABLE" if tx == 1 else "PASS",
        "team_reward_sum_diagnostic_only": reward,
        "coverage": "NOT AVAILABLE",
        "finite": bool(
            post["actor_parameters_finite"]
            and post["actor_optimizer_states_finite"]
            and post["critic_parameters_finite"]
            and post["critic_optimizer_state_finite"]
            and post["valuenorm_state_finite"]
        ),
        "route_poisoned": normalized["route_poisoned"],
    }
    _append_jsonl(prefix.parent / f"{prefix.name}_transaction_summary.jsonl", record)
    _append_jsonl(
        prefix.parent / f"{prefix.name}_lifecycle_decision_aggregate.jsonl",
        {
            "schema_version": "b2_t1_lifecycle_aggregate_v1",
            "run_identity": normalized["run_identity"],
            "transaction_index": tx,
            "update_id": normalized["update_id"],
            "transaction_rows": record["lifecycle_rows"],
            "cumulative_rows": {
                key: _cumulative[key]
                for key in (
                    "policy_required_rows",
                    "continuation_rows",
                    "forced_noop_nondecision_rows",
                )
            },
            "actor_policy_call_faults": 0,
            "observer_mutations": 0,
        },
    )
    metrics = {
        "schema_version": "b2_t1_training_metric_v1",
        "run_identity": normalized["run_identity"],
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "team_reward_sum_diagnostic_only": reward,
        "per_agent_reward": "NOT AVAILABLE",
        "coverage": "NOT AVAILABLE",
        "completed_viewpoints": "NOT AVAILABLE",
        "new_viewpoints": "NOT AVAILABLE",
        "duplicate_scans": "NOT AVAILABLE",
        "reach_violations": "NOT AVAILABLE",
        "task_completions": "NOT AVAILABLE",
        "releases_reassignments": "NOT AVAILABLE",
        "policy_entropy": "NOT AVAILABLE",
        "actor_loss": _stats(normalized["actor_losses"]),
        "actor_gradient_norm": _stats(normalized["actor_gradient_norms"]),
        "critic_loss": _stats(normalized["critic_losses"]),
        "critic_gradient_norm": _stats(normalized["critic_gradient_norms"]),
        "no_performance_threshold_applied": True,
    }
    _append_jsonl(prefix.parent / f"{prefix.name}_training_metrics.jsonl", metrics)
    if tx in ROLLING_HEALTH_TRANSACTIONS:
        _append_jsonl(
            prefix.parent / f"{prefix.name}_rolling_health.jsonl",
            {
                "schema_version": "b2_t1_rolling_health_v1",
                "run_identity": normalized["run_identity"],
                "transaction_index": tx,
                "update_id": normalized["update_id"],
                "actor_parameter_digests": post["actor_parameter_digests"],
                "actor_optimizer_digests": post["actor_optimizer_digests"],
                "critic_parameter_digest": post["critic_parameter_digest"],
                "critic_optimizer_digest": post["critic_optimizer_digest"],
                "valuenorm_digest": post["canonical_valuenorm_digest"],
                "adam": _adam_summary(post),
                "cumulative": dict(_cumulative),
                "finite": record["finite"],
                "route_poisoned": normalized["route_poisoned"],
                "last_s10": True,
            },
        )


def _compact_bridge(path: Path, payload: Mapping[str, object]) -> None:
    global _last_bridge_count
    normalized = V2.normalize(payload)
    bridges = normalized["bridges"]
    if len(bridges) <= _last_bridge_count:
        return
    bridge = bridges[-1]
    _last_bridge_count = len(bridges)
    prefix = _prefix_from_match(path, "_continuity_bridges.json")
    _append_jsonl(
        prefix.parent / f"{prefix.name}_bridge_summary.jsonl",
        {
            "schema_version": "b2_t1_bridge_summary_v1",
            "run_identity": normalized["run_identity"],
            "source_config_identity_digest": normalized["source_config_identity_digest"],
            "bridge_index": bridge["bridge_index"],
            "from_update_id": bridge["from_update_id"],
            "to_update_id": bridge["to_update_id"],
            "update_id_changed": bridge["update_id_changed"],
            "persistent_object_identity": bridge["persistent_object_identity"],
            "learner_post_to_pre_exact": bridge["learner_post_to_pre_exact"],
            "collection_preserved_learner": bridge["collection_preserved_learner"],
            "route_unpoisoned": bridge["route_unpoisoned"],
            "rollout_modes_valid": bridge["rollout_modes_valid"],
            "ledger_empty_before_collection": bridge["ledger_empty_before_collection"],
            "stale_permits": bridge["stale_permits"],
            "stale_gradients": bridge["stale_gradients"],
            "actor_cursors_after_collection": bridge["actor_cursors_after_collection"],
            "critic_cursor_after_collection": bridge["critic_cursor_after_collection"],
            "new_rollout_provenance_digest": bridge["new_rollout_provenance_digest"],
            "next_s0_established": bridge["next_s0_established"],
            "pass": bridge["pass"],
        },
    )


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    _base_atomic_json(path, payload)
    name = path.name
    if re.search(r"_tx\d+_s10\.json$", name):
        _compact_transaction(path, payload)
    elif name.endswith("_continuity_bridges.json"):
        _compact_bridge(path, payload)


_BASE_NAMESPACE["_atomic_json"] = _atomic_json


def _compact_success_artifacts(prefix: Path) -> dict[str, object]:
    removed: list[str] = []
    retained: list[str] = []
    tx_pattern = re.compile(rf"^{re.escape(prefix.name)}_tx(\d+)_")
    bridge_pattern = re.compile(rf"^{re.escape(prefix.name)}_bridge\d+_(pre|post)_collection\.json$")
    for path in sorted(prefix.parent.glob(f"{prefix.name}_*")):
        match = tx_pattern.match(path.name)
        if match and int(match.group(1)) not in SENTINEL_TRANSACTIONS:
            path.unlink()
            removed.append(path.name)
        elif bridge_pattern.match(path.name):
            path.unlink()
            removed.append(path.name)
        else:
            retained.append(path.name)
    manifest = {
        "schema_version": "b2_t1_bounded_artifact_manifest_v1",
        "sentinel_transactions": tuple(sorted(SENTINEL_TRANSACTIONS)),
        "rolling_health_transactions": tuple(sorted(ROLLING_HEALTH_TRANSACTIONS)),
        "non_sentinel_full_detail_removed_after_compaction": len(removed),
        "removed_names": tuple(removed),
        "retained_names_before_manifest": tuple(retained),
        "checkpoint_weight_io": 0,
        "model_weight_dumps": 0,
    }
    manifest_path = prefix.parent / f"{prefix.name}_artifact_manifest.json"
    _base_atomic_json(manifest_path, manifest)
    manifest["path"] = str(manifest_path)
    manifest["bytes"] = manifest_path.stat().st_size
    manifest["sha256"] = _sha(manifest_path)
    return manifest


def run_worker(args: object) -> int:
    code = int(_base_run_worker(args))
    if code != 0:
        return code
    prefix = Path(args.artifact_prefix).resolve()
    manifest = _compact_success_artifacts(prefix)
    result_path = Path(args.result_file).resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["bounded_artifact_manifest"] = manifest
    _base_atomic_json(result_path, result)
    final_path = prefix.parent / f"{prefix.name}_final_result.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    final["bounded_artifact_manifest"] = manifest
    final["sentinel_transactions"] = tuple(sorted(SENTINEL_TRANSACTIONS))
    final["rolling_health_transactions"] = tuple(sorted(ROLLING_HEALTH_TRANSACTIONS))
    _base_atomic_json(final_path, final)
    return code


_BASE_NAMESPACE["run_worker"] = run_worker


def main() -> int:
    return int(_BASE_NAMESPACE["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
