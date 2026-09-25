"""Exactly-300-update real-Isaac observability/stability qualification for B2-T2."""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


HERE = Path(__file__).resolve().parent
T1_HARNESS = HERE / "test_assignment_phase_b2_t1_bounded_short_training_stability.py"
OBSERVER_HELPER = HERE / "_assignment_phase_b2_t2_observability.py"
QUALIFIED_T1_SHA256 = "8c08bffdbabcedaafb4371a78ce16535900b4ac6e27cd012e9a8008281ab0932"
TRANSACTION_COUNT = 300
SENTINEL_TRANSACTIONS = frozenset((1, 30, 100, 200, 300))
ROLLING_HEALTH_TRANSACTIONS = frozenset((1, 10, 25, 50, 75, 100, 150, 200, 250, 300))
WINDOWS = ((1, 50), (51, 100), (101, 150), (151, 200), (201, 250), (251, 300))
PASS = "PHASE-B2-T2-MEDIUM-LENGTH-TRAINING-OBSERVABILITY-STABILITY-QUALIFIED-AWAITING-GPT-REVIEW"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_exact(source: str, old: str, new: str, *, count: int | None = None) -> str:
    observed = source.count(old)
    expected = observed if count is None else count
    if observed != expected or observed == 0:
        raise RuntimeError(
            "STOP — B2-T2 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"replacement {old!r} expected {expected}, observed {observed}"
        )
    return source.replace(old, new)


def _load_qualified_t1_module():
    observed = _sha(T1_HARNESS)
    if observed != QUALIFIED_T1_SHA256:
        raise RuntimeError(
            "STOP — B2-T2 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"B2-T1 harness {observed} != {QUALIFIED_T1_SHA256}"
        )
    spec = importlib.util.spec_from_file_location("_phase_b2_t1_qualified_source", T1_HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP — B2-T2 T1-HARNESS-LOAD")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _qualified_t2_source() -> str:
    t1 = _load_qualified_t1_module()
    source = t1._qualified_t1_source()
    source = _replace_exact(
        source,
        '"""Exactly-30-update real-Isaac stability qualification for Phase B2-T1."""',
        '"""Exactly-300-update real-Isaac observability/stability qualification for Phase B2-T2."""',
        count=1,
    )
    source = _replace_exact(source, "TRANSACTION_COUNT = 30", "TRANSACTION_COUNT = 300", count=1)
    source = _replace_exact(
        source,
        'PASS = (\n    "PHASE-B2-T1-BOUNDED-SHORT-TRAINING-STABILITY-"\n    "QUALIFIED-AWAITING-GPT-REVIEW"\n)',
        f'PASS = "{PASS}"',
        count=1,
    )
    source = _replace_exact(source, "STOP — B2-T1", "STOP — B2-T2")
    source = _replace_exact(source, "PHASE-B2-T1-STOP", "PHASE-B2-T2-STOP")
    source = _replace_exact(source, "b2_t1", "b2_t2")
    source = _replace_exact(
        source,
        "b2_t2_short_training_20260911_formal01",
        "b2_t2_medium_training_20260911_formal01",
        count=1,
    )
    source = _replace_exact(source, "b2-t1-short-training", "b2-t2-medium-training")
    source = _replace_exact(
        source,
        "B2-T1.bounded_short_training_stability",
        "B2-T2.medium_length_training_observability_stability",
        count=1,
    )
    source = _replace_exact(
        source,
        'f"{run_identity}-tx{transaction_index:02d}"',
        'f"{run_identity}-tx{transaction_index:03d}"',
        count=1,
    )
    source = _replace_exact(
        source,
        'f"tx{index:02d}_post_to_tx{index + 1:02d}_pre"',
        'f"tx{index:03d}_post_to_tx{index + 1:03d}_pre"',
        count=1,
    )
    source = _replace_exact(source, "transaction_31_started", "transaction_301_started")
    source = _replace_exact(
        source,
        'parser.add_argument("--timeout-seconds", type=int, default=900)',
        'parser.add_argument("--timeout-seconds", type=int, default=10800)',
        count=1,
    )
    observer_old = '''    def route_observer(stage: str, detail: object | None) -> None:
        route_events.append((stage, detail))
'''
    observer_new = '''    from _assignment_phase_b2_t2_observability import capture_step_observability

    observability_steps: list[dict[str, object]] = []

    def route_observer(stage: str, detail: object | None) -> None:
        route_events.append((stage, detail))
        if stage != "runtime_proposal_effective_step":
            return
        cpu_rng_before = torch.random.get_rng_state().clone()
        cuda_rng_before = tuple(item.clone() for item in torch.cuda.get_rng_state_all())
        runtime_before = (
            int(buffer.step),
            tuple(storage.next_action_slot for storage in route.actor_storages),
            tuple(sorted(route.collector.consumed_terminal_keys)),
            bool(route.poisoned),
        )
        observation = capture_step_observability(detail)
        runtime_after = (
            int(buffer.step),
            tuple(storage.next_action_slot for storage in route.actor_storages),
            tuple(sorted(route.collector.consumed_terminal_keys)),
            bool(route.poisoned),
        )
        cuda_rng_after = tuple(item.clone() for item in torch.cuda.get_rng_state_all())
        rng_unchanged = bool(
            torch.equal(cpu_rng_before, torch.random.get_rng_state())
            and len(cuda_rng_before) == len(cuda_rng_after)
            and all(torch.equal(left, right) for left, right in zip(cuda_rng_before, cuda_rng_after))
        )
        _require(runtime_before == runtime_after, "OBSERVER_RUNTIME_MUTATION")
        _require(rng_unchanged, "OBSERVER_RNG_MUTATION")
        observation["runtime_state_before"] = runtime_before
        observation["runtime_state_after"] = runtime_after
        observation["rng_unchanged"] = True
        observation["observer_runtime_nonmutation"] = True
        observability_steps.append(observation)
'''
    source = _replace_exact(source, observer_old, observer_new, count=1)
    source = _replace_exact(
        source,
        '            "team_reward_sum_diagnostic_only": reward_total,',
        '            "team_reward_sum_diagnostic_only": reward_total,\n'
        '            "observability_steps": tuple(observability_steps[-resolved_T:]),',
        count=1,
    )
    source = _replace_exact(
        source,
        '                "worker": worker,',
        '''                "worker": {
                    "status": worker.get("status"),
                    "classification": worker.get("classification"),
                    "process_id": worker.get("process_id"),
                    "real_runtime_counts": worker.get("real_runtime_counts"),
                    "exact_execution_counts": worker.get("exact_execution_counts"),
                    "final_result_path": str(_artifact_path(Path(args.artifact_prefix).resolve(), "final_result")),
                },''',
        count=1,
    )
    return source


_INNER: dict[str, object] = {
    "__name__": "_phase_b2_t2_qualified_base",
    "__file__": str(Path(__file__).resolve()),
    "__package__": None,
}
exec(compile(_qualified_t2_source(), str(T1_HARNESS), "exec"), _INNER)

V2 = _INNER["V2"]
_base_atomic_json = _INNER["_atomic_json"]
_base_run_worker = _INNER["run_worker"]


def _source_identity() -> dict[str, object]:
    repo = {name: _sha(_INNER["SCAN"] / name) for name in _INNER["QUALIFIED_REPO_SHA256"]}
    installed = {name: _sha(_INNER["HARL"] / name) for name in _INNER["QUALIFIED_HARL_SHA256"]}
    test_side = {
        "scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py": _sha(HERE / "_assignment_phase_b2_t0_ld_decision_gate.py"),
        "scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py": _sha(HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"),
        "scripts/environments/test_assignment_phase_b2_t1_bounded_short_training_stability.py": _sha(T1_HARNESS),
        "scripts/environments/_assignment_phase_b2_t2_observability.py": _sha(OBSERVER_HELPER),
        "scripts/environments/test_assignment_phase_b2_t2_medium_length_training_observability_stability.py": _sha(Path(__file__).resolve()),
    }
    result = {
        "repo_hashes": repo,
        "installed_harl_hashes": installed,
        "test_side": test_side,
        "qualified_repo_sources_exact": repo == _INNER["QUALIFIED_REPO_SHA256"],
        "qualified_installed_sources_exact": installed == _INNER["QUALIFIED_HARL_SHA256"],
        "qualified_ld_helper_exact": test_side["scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py"] == _INNER["QUALIFIED_LD_HELPER_SHA256"],
        "qualified_t1_harness_exact": test_side["scripts/environments/test_assignment_phase_b2_t1_bounded_short_training_stability.py"] == QUALIFIED_T1_SHA256,
        "t2_observer_identity_recorded": bool(test_side["scripts/environments/_assignment_phase_b2_t2_observability.py"]),
        "t2_harness_identity_recorded": bool(test_side["scripts/environments/test_assignment_phase_b2_t2_medium_length_training_observability_stability.py"]),
    }
    result["pass"] = bool(
        result["qualified_repo_sources_exact"]
        and result["qualified_installed_sources_exact"]
        and result["qualified_ld_helper_exact"]
        and result["qualified_t1_harness_exact"]
    )
    return result


_INNER["_source_identity"] = _source_identity

_last_bridge_count = 0
_cumulative: dict[str, object] = {
    "policy_required_rows": 0,
    "continuation_rows": 0,
    "forced_noop_nondecision_rows": 0,
    "terminal_events": 0,
    "valid_nonzero_update": 0,
    "valid_zero_effective_update": 0,
    "team_reward_sum": 0.0,
    "task_completion_events": 0,
    "release_events": 0,
    "failure_events": 0,
    "new_failed_pairs": 0,
    "observer_mutations": 0,
}
_cumulative_raw_actions: Counter[str] = Counter()
_cumulative_effective_actions: Counter[str] = Counter()


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
        "sum": sum(floats),
        "finite": all(math.isfinite(value) for value in floats),
    }


def _adam_summary(snapshot: Mapping[str, object]) -> dict[str, object]:
    def summarize(rows: Sequence[Sequence[object]]) -> dict[str, object]:
        steps = tuple(int(row[1]) for row in rows)
        return {"parameter_count": len(steps), "min_step": min(steps) if steps else 0, "max_step": max(steps) if steps else 0, "distinct_steps": tuple(sorted(set(steps)))}

    return {"actors": tuple(summarize(rows) for rows in snapshot["actor_adam_steps"]), "critic": summarize(snapshot["critic_adam_steps"])}


def _prefix_from_match(path: Path, marker: str) -> Path:
    return path.parent / path.name[: path.name.index(marker)]


def _merge_histograms(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, int]:
    total: Counter[str] = Counter()
    for row in rows:
        total.update({str(key): int(value) for key, value in row[field].items()})
    return dict(sorted(total.items(), key=lambda item: int(item[0])))


def _compact_transaction(path: Path, payload: Mapping[str, object]) -> None:
    normalized = V2.normalize(payload)
    tx = int(normalized["transaction_index"])
    prefix = _prefix_from_match(path, f"_tx{tx}_s10.json")
    observations = tuple(normalized["observability_steps"])
    physical_range = normalized["rollout_provenance"]["collection_physical_step_range"]
    if len(observations) != int(physical_range[1] - physical_range[0] + 1):
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-STEP-COUNT")
    if any(
        int(item["observer_mutation_count"]) != 0
        or not bool(item["observer_runtime_nonmutation"])
        or not bool(item["rng_unchanged"])
        for item in observations
    ):
        raise RuntimeError("STOP — B2-T2 OBSERVER-NONMUTATION")
    lifecycle_rows = tuple(row for receipt in normalized["lifecycle_decision_gate_receipts"] for row in receipt["rows"])
    policy = sum(int(bool(row["decision_required"])) for row in lifecycle_rows)
    continuation = sum(int(row["decision_reason"] == "FORCED_CONTINUATION_ROW") for row in lifecycle_rows)
    noop = sum(int(row["decision_reason"] == "FORCED_NOOP_ROW") for row in lifecycle_rows)
    counts = dict(normalized["transaction"]["exact_execution_counts"])
    post = normalized["post_update_learner"]
    terminal_count = sum(int(value) for value in normalized["terminal_reason_counts"].values())
    reward = float(normalized["team_reward_sum_diagnostic_only"])
    completion_events = sum(int(item["task_completion_events"]) for item in observations)
    release_events = sum(int(item["release_events"]) for item in observations)
    failure_events = sum(int(item["failure_events"]) for item in observations)
    new_failed_pairs = sum(int(item["new_failed_pair_count"]) for item in observations)
    for key, value in (
        ("policy_required_rows", policy),
        ("continuation_rows", continuation),
        ("forced_noop_nondecision_rows", noop),
        ("terminal_events", terminal_count),
        ("valid_nonzero_update", int(normalized["valid_nonzero"])),
        ("valid_zero_effective_update", int(normalized["valid_zero_effective"])),
        ("task_completion_events", completion_events),
        ("release_events", release_events),
        ("failure_events", failure_events),
        ("new_failed_pairs", new_failed_pairs),
    ):
        _cumulative[key] = int(_cumulative[key]) + value
    _cumulative["team_reward_sum"] = float(_cumulative["team_reward_sum"]) + reward
    raw_hist = _merge_histograms(observations, "raw_action_histogram")
    effective_hist = _merge_histograms(observations, "effective_assignment_histogram")
    _cumulative_raw_actions.update(raw_hist)
    _cumulative_effective_actions.update(effective_hist)
    finite = bool(
        post["actor_parameters_finite"]
        and post["actor_optimizer_states_finite"]
        and post["critic_parameters_finite"]
        and post["critic_optimizer_state_finite"]
        and post["valuenorm_state_finite"]
    )
    record = {
        "schema_version": "b2_t2_transaction_summary_v1",
        "run_identity": normalized["run_identity"],
        "source_config_identity_digest": normalized["source_config_identity_digest"],
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "actor_order": normalized["actor_order"],
        "rollout_provenance": normalized["rollout_provenance"],
        "rollout_evidence_digest": normalized["rollout_evidence_digest"],
        "lifecycle_rows": {"policy_required": policy, "continuation": continuation, "forced_noop_nondecision": noop},
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
        "observer_mutations": 0,
        "finite": finite,
        "route_poisoned": normalized["route_poisoned"],
    }
    _append_jsonl(prefix.parent / f"{prefix.name}_transaction_summary.jsonl", record)
    _append_jsonl(
        prefix.parent / f"{prefix.name}_lifecycle_decision_aggregate.jsonl",
        {
            "schema_version": "b2_t2_lifecycle_aggregate_v1",
            "run_identity": normalized["run_identity"],
            "transaction_index": tx,
            "update_id": normalized["update_id"],
            "transaction_rows": record["lifecycle_rows"],
            "cumulative_rows": {key: _cumulative[key] for key in ("policy_required_rows", "continuation_rows", "forced_noop_nondecision_rows")},
            "actor_policy_call_faults": 0,
            "observer_mutations": 0,
        },
    )
    per_agent = {}
    for name in observations[0]["reward_by_agent"]:
        values = [float(item["reward_by_agent"][name]["sum"]) for item in observations]
        per_agent[name] = _stats(values)
    coverage_values = [float(item["environment_info_metrics"]["coverage_ratio"]) for item in observations]
    duplicate_values = [float(item["environment_info_metrics"]["duplicate_scans"]) for item in observations]
    reach_values = [float(item["environment_info_metrics"]["reach_violation"]) for item in observations]
    metric = {
        "schema_version": "b2_t2_training_metric_v1",
        "run_identity": normalized["run_identity"],
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "team_reward_sum_diagnostic_only": reward,
        "per_agent_reward": per_agent,
        "coverage_ratio": {**_stats(coverage_values), "final": coverage_values[-1]},
        "duplicate_scans": _stats(duplicate_values),
        "reach_violations": _stats(reach_values),
        "policy_entropy": "NOT AVAILABLE",
        "actor_loss": _stats(normalized["actor_losses"]),
        "actor_gradient_norm": _stats(normalized["actor_gradient_norms"]),
        "critic_loss": _stats(normalized["critic_losses"]),
        "critic_gradient_norm": _stats(normalized["critic_gradient_norms"]),
        "critic_classes": {"VALID_NONZERO_UPDATE": int(normalized["valid_nonzero"]), "VALID_ZERO_EFFECTIVE_UPDATE": int(normalized["valid_zero_effective"])},
        "raw_action_histogram": raw_hist,
        "effective_assignment_histogram": effective_hist,
        "no_performance_threshold_applied": True,
    }
    _append_jsonl(prefix.parent / f"{prefix.name}_training_metrics.jsonl", metric)
    task = {
        "schema_version": "b2_t2_task_progress_metric_v1",
        "run_identity": normalized["run_identity"],
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "step_count": len(observations),
        "instantaneous_steps": observations,
        "per_update_delta": {
            "task_completion_events": completion_events,
            "release_events": release_events,
            "failure_events": failure_events,
            "new_failed_pairs": new_failed_pairs,
            "reassignment_events": "NOT AVAILABLE",
        },
        "cumulative": {key: _cumulative[key] for key in ("task_completion_events", "release_events", "failure_events", "new_failed_pairs")},
        "final_step": {
            "completed_viewpoint_count": observations[-1]["completed_viewpoint_count"],
            "coverage_ratio": coverage_values[-1],
            "available_task_count": observations[-1]["available_task_count"],
            "claimed_executing_task_count": observations[-1]["claimed_executing_task_count"],
            "team_infeasible_task_count": observations[-1]["team_infeasible_task_count"],
        },
        "observer_mutation_count": 0,
    }
    _append_jsonl(prefix.parent / f"{prefix.name}_task_progress_metrics.jsonl", task)
    if tx in ROLLING_HEALTH_TRANSACTIONS:
        _append_jsonl(
            prefix.parent / f"{prefix.name}_rolling_health.jsonl",
            {
                "schema_version": "b2_t2_rolling_health_v1",
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
                "cumulative_raw_action_histogram": dict(sorted(_cumulative_raw_actions.items(), key=lambda item: int(item[0]))),
                "cumulative_effective_assignment_histogram": dict(sorted(_cumulative_effective_actions.items(), key=lambda item: int(item[0]))),
                "latest_metrics": metric,
                "latest_task_progress": task["final_step"],
                "finite": finite,
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
            "schema_version": "b2_t2_bridge_summary_v1",
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
    if re.search(r"_tx\d+_s10\.json$", path.name):
        _compact_transaction(path, payload)
    elif path.name.endswith("_continuity_bridges.json"):
        _compact_bridge(path, payload)


_INNER["_atomic_json"] = _atomic_json


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _combine_stats(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, object]:
    stats = [row[field] for row in rows]
    count = sum(int(item["count"]) for item in stats)
    total = sum(float(item["sum"]) for item in stats)
    return {
        "count": count,
        "min": min(float(item["min"]) for item in stats) if count else None,
        "max": max(float(item["max"]) for item in stats) if count else None,
        "mean": total / count if count else None,
        "finite": all(bool(item["finite"]) for item in stats),
    }


def _windowed_diagnostics(prefix: Path) -> tuple[dict[str, object], ...]:
    metrics = _read_jsonl(prefix.parent / f"{prefix.name}_training_metrics.jsonl")
    tasks = _read_jsonl(prefix.parent / f"{prefix.name}_task_progress_metrics.jsonl")
    lifecycle = _read_jsonl(prefix.parent / f"{prefix.name}_lifecycle_decision_aggregate.jsonl")
    output = []
    for start, end in WINDOWS:
        mrows = metrics[start - 1 : end]
        trows = tasks[start - 1 : end]
        lrows = lifecycle[start - 1 : end]
        reward_values = [float(row["team_reward_sum_diagnostic_only"]) for row in mrows]
        coverage_values = [float(row["coverage_ratio"]["final"]) for row in mrows]
        output.append(
            {
                "window": f"tx{start:03d}-{end:03d}",
                "team_reward": _stats(reward_values),
                "coverage_final_per_update": {**_stats(coverage_values), "window_final": coverage_values[-1]},
                "task_completion_events": sum(int(row["per_update_delta"]["task_completion_events"]) for row in trows),
                "release_events": sum(int(row["per_update_delta"]["release_events"]) for row in trows),
                "failure_events": sum(int(row["per_update_delta"]["failure_events"]) for row in trows),
                "new_failed_pairs": sum(int(row["per_update_delta"]["new_failed_pairs"]) for row in trows),
                "actor_loss": _combine_stats(mrows, "actor_loss"),
                "critic_loss": _combine_stats(mrows, "critic_loss"),
                "actor_gradient_norm": _combine_stats(mrows, "actor_gradient_norm"),
                "critic_gradient_norm": _combine_stats(mrows, "critic_gradient_norm"),
                "policy_entropy": "NOT AVAILABLE",
                "lifecycle_rows": {
                    key: sum(int(row["transaction_rows"][key]) for row in lrows)
                    for key in ("policy_required", "continuation", "forced_noop_nondecision")
                },
                "critic_classes": {
                    key: sum(int(row["critic_classes"][key]) for row in mrows)
                    for key in ("VALID_NONZERO_UPDATE", "VALID_ZERO_EFFECTIVE_UPDATE")
                },
                "raw_action_histogram": _merge_histograms(mrows, "raw_action_histogram"),
                "descriptive_only": True,
            }
        )
    return tuple(output)


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
        "schema_version": "b2_t2_bounded_artifact_manifest_v1",
        "sentinel_transactions": tuple(sorted(SENTINEL_TRANSACTIONS)),
        "rolling_health_transactions": tuple(sorted(ROLLING_HEALTH_TRANSACTIONS)),
        "window_definitions": WINDOWS,
        "non_sentinel_full_detail_removed_after_success": len(removed),
        "removed_names": tuple(removed),
        "retained_names_before_manifest": tuple(retained),
        "checkpoint_weight_io": 0,
        "model_weight_dumps": 0,
    }
    path = prefix.parent / f"{prefix.name}_artifact_manifest.json"
    _base_atomic_json(path, manifest)
    return {**manifest, "path": str(path), "bytes": path.stat().st_size, "sha256": _sha(path)}


def _compact_large_final(result: dict[str, object]) -> dict[str, object]:
    compacted = dict(result)
    removed = {}
    for key in ("transactions", "bridges", "lifecycle_decision_gate_receipts", "continuity_table"):
        value = compacted.pop(key, None)
        if value is not None:
            removed[key] = {"count": len(value), "canonical_digest": _INNER["_json_digest"](value)}
    compacted["post_success_large_fields_compacted"] = removed
    return compacted


def _postprocess_success(prefix: Path, *, result_path: Path | None = None) -> dict[str, object]:
    from _assignment_phase_b2_t2_observability import run_pure_qualification, schema_artifact

    prefix = prefix.resolve()
    final_path = prefix.parent / f"{prefix.name}_final_result.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    existing_manifest = prefix.parent / f"{prefix.name}_artifact_manifest.json"
    if (
        existing_manifest.exists()
        and final.get("post_success_large_fields_compacted")
        and final.get("training_observability")
    ):
        return {
            "status": "already_postprocessed",
            "classification": final.get("classification"),
            "artifact_manifest": str(existing_manifest),
        }
    counts = final.get("exact_execution_counts", {})
    _INNER["_require"](final.get("status") == "passed", "POSTPROCESS_FORMAL_STATUS")
    _INNER["_require"](final.get("classification") == PASS, "POSTPROCESS_CLASSIFICATION")
    _INNER["_require"](counts.get("successful_full_transactions") == 300, "POSTPROCESS_TX_COUNT")
    _INNER["_require"](counts.get("s10_to_next_s0_bridges") == 299, "POSTPROCESS_BRIDGE_COUNT")
    _INNER["_require"](not final.get("transaction_301_started"), "POSTPROCESS_TX301")
    observer_qualification = run_pure_qualification()
    if not observer_qualification["pass"]:
        raise RuntimeError("STOP — B2-T2 OBSERVER-PURE-QUALIFICATION")
    schema_path = prefix.parent / f"{prefix.name}_observability_schema_source.json"
    schema_payload = {
        **schema_artifact(),
        "pure_qualification": observer_qualification,
    }
    _base_atomic_json(schema_path, schema_payload)
    manifest = _compact_success_artifacts(prefix)
    windows = _windowed_diagnostics(prefix)
    tx_rows = _read_jsonl(prefix.parent / f"{prefix.name}_transaction_summary.jsonl")
    metric_rows = _read_jsonl(prefix.parent / f"{prefix.name}_training_metrics.jsonl")
    task_rows = _read_jsonl(prefix.parent / f"{prefix.name}_task_progress_metrics.jsonl")
    rolling_rows = _read_jsonl(prefix.parent / f"{prefix.name}_rolling_health.jsonl")
    bridge_rows = _read_jsonl(prefix.parent / f"{prefix.name}_bridge_summary.jsonl")
    aggregate = {
        "observability_schema": {"path": str(schema_path), "bytes": schema_path.stat().st_size, "sha256": _sha(schema_path)},
        "observer_mutation_count": sum(int(row["observer_mutations"]) for row in tx_rows),
        "windowed_diagnostics": windows,
        "raw_action_histogram": _merge_histograms(metric_rows, "raw_action_histogram"),
        "effective_assignment_histogram": _merge_histograms(metric_rows, "effective_assignment_histogram"),
        "task_completion_events": sum(int(row["per_update_delta"]["task_completion_events"]) for row in task_rows),
        "release_events": sum(int(row["per_update_delta"]["release_events"]) for row in task_rows),
        "failure_events": sum(int(row["per_update_delta"]["failure_events"]) for row in task_rows),
        "new_failed_pairs": sum(int(row["per_update_delta"]["new_failed_pairs"]) for row in task_rows),
        "reassignment_events": "NOT AVAILABLE",
        "policy_entropy": "NOT AVAILABLE",
        "ledger_counts": {
            "transactions": len(tx_rows),
            "bridges": len(bridge_rows),
            "lifecycle": len(_read_jsonl(prefix.parent / f"{prefix.name}_lifecycle_decision_aggregate.jsonl")),
            "training_metrics": len(metric_rows),
            "task_progress": len(task_rows),
            "rolling_health": len(rolling_rows),
        },
    }
    final = _compact_large_final(final)
    final.update(
        {
            "classification": PASS,
            "bounded_artifact_manifest": manifest,
            "sentinel_transactions": tuple(sorted(SENTINEL_TRANSACTIONS)),
            "rolling_health_transactions": tuple(sorted(ROLLING_HEALTH_TRANSACTIONS)),
            "training_observability": aggregate,
            "production_semantic_modifications": 0,
            "transaction_301_started": False,
        }
    )
    _base_atomic_json(final_path, final)
    if result_path is not None and result_path.exists():
        worker = _compact_large_final(json.loads(result_path.read_text(encoding="utf-8")))
        worker.update(
            {
                "classification": PASS,
                "bounded_artifact_manifest": manifest,
                "sentinel_transactions": tuple(sorted(SENTINEL_TRANSACTIONS)),
                "rolling_health_transactions": tuple(sorted(ROLLING_HEALTH_TRANSACTIONS)),
                "training_observability": aggregate,
                "production_semantic_modifications": 0,
                "transaction_301_started": False,
                "final_result": {"path": str(final_path), "bytes": final_path.stat().st_size, "sha256": _sha(final_path)},
            }
        )
        _base_atomic_json(result_path, worker)
    return {
        "status": "postprocessed",
        "classification": PASS,
        "artifact_manifest": manifest,
        "training_observability": aggregate,
        "final_result": {"path": str(final_path), "bytes": final_path.stat().st_size, "sha256": _sha(final_path)},
    }


def run_worker(args: object) -> int:
    code = int(_base_run_worker(args))
    if code != 0:
        return code
    _postprocess_success(
        Path(args.artifact_prefix),
        result_path=Path(args.result_file).resolve(),
    )
    return 0


_INNER["run_worker"] = run_worker


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--postprocess-existing-success":
        result = _postprocess_success(Path(sys.argv[2]))
        print(json.dumps(V2.normalize(result), indent=2, sort_keys=True))
        return 0
    return int(_INNER["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
