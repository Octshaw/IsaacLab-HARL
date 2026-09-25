"""Read-only metric extraction for the Phase B2-T2 qualification harness.

The observer accepts only already-produced immutable facade receipts and the
environment result carried by those receipts.  It never calls the policy,
steps the environment, or writes lifecycle/learner state.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from types import SimpleNamespace
from typing import Mapping, Sequence

import torch


OBSERVABILITY_SCHEMA_VERSION = "b2_t2_observability_schema_v1"


OBSERVABILITY_SCHEMA: tuple[dict[str, object], ...] = (
    {"metric": "team reward", "status": "AVAILABLE — authoritative direct", "source": "facade environment_result reward mapping / HARL step reward tensor", "definition": "sum of all E x M reward scalars in one physical transition", "aggregation": "per-step sum; per-update and window min/max/mean/sum", "future": "yes"},
    {"metric": "per-agent reward", "status": "AVAILABLE — authoritative direct", "source": "facade environment_result reward mapping keyed by configured agent", "definition": "reward tensor for each configured agent over E environments", "aggregation": "per-step per-agent sum/min/max/mean; per-update and window summaries", "future": "yes"},
    {"metric": "completed task/viewpoint count", "status": "AVAILABLE — read-only derived", "source": "canonical P2 LifecycleStateSnapshot.task_state; terminal rows use copied updated_task_state", "definition": "count(task_state == TaskLifecycleState.COMPLETED)", "aggregation": "instantaneous per environment and aggregate; terminal rows are pre-reset", "future": "yes"},
    {"metric": "coverage ratio", "status": "AVAILABLE — authoritative direct", "source": "environment info['log']['coverage_ratio']", "definition": "viewpoints_covered.float().mean() over E x N at reward time", "aggregation": "per-step scalar; per-update/window mean/min/max/final", "future": "yes"},
    {"metric": "currently claimed/executing task count", "status": "AVAILABLE — read-only derived", "source": "canonical P2 task_state", "definition": "count of CLAIMED, NAVIGATING, or ALIGNING task states", "aggregation": "instantaneous per environment and aggregate", "future": "yes"},
    {"metric": "available task count", "status": "AVAILABLE — read-only derived", "source": "canonical P2 task_state", "definition": "count(task_state == AVAILABLE)", "aggregation": "instantaneous per environment and aggregate", "future": "yes"},
    {"metric": "task completion events", "status": "AVAILABLE — authoritative direct", "source": "canonical LifecycleEventType.TASK_COMPLETED records", "definition": "exact finalized TASK_COMPLETED event count", "aggregation": "per-step delta; per-update/window/run cumulative", "future": "yes"},
    {"metric": "release events", "status": "AVAILABLE — authoritative direct", "source": "canonical LifecycleEventType.TASK_RELEASED records", "definition": "exact finalized TASK_RELEASED event count", "aggregation": "per-step delta; per-update/window/run cumulative", "future": "yes"},
    {"metric": "reassignment events", "status": "NOT AVAILABLE — no existing authoritative basis", "source": "none", "definition": "owner change is not treated as exact reassignment", "aggregation": "NOT AVAILABLE", "future": "no"},
    {"metric": "failure events / failed-pair events", "status": "AVAILABLE — authoritative direct", "source": "TERMINAL_PAIR_FAILURE_RECORDED lifecycle events and terminal new_failed_pairs", "definition": "exact finalized failure-event count; terminal new-pair count retained separately", "aggregation": "per-step delta; per-update/window/run cumulative", "future": "yes"},
    {"metric": "policy-required row count", "status": "AVAILABLE — read-only derived", "source": "unchanged LD decision-gate receipts", "definition": "count(decision_required == true)", "aggregation": "per-update and cumulative", "future": "yes"},
    {"metric": "continuation row count", "status": "AVAILABLE — read-only derived", "source": "unchanged LD decision-gate receipts", "definition": "count(decision_reason == FORCED_CONTINUATION_ROW)", "aggregation": "per-update and cumulative", "future": "yes"},
    {"metric": "forced-noop/nondecision row count", "status": "AVAILABLE — read-only derived", "source": "unchanged LD decision-gate receipts", "definition": "count(decision_reason == FORCED_NOOP_ROW)", "aggregation": "per-update and cumulative", "future": "yes"},
    {"metric": "terminal reason counts", "status": "AVAILABLE — authoritative direct", "source": "immutable terminal historical rows / termination reason grid", "definition": "count by canonical TerminationReason", "aggregation": "per-update and cumulative", "future": "yes"},
    {"metric": "duplicate scan metric", "status": "AVAILABLE — diagnostic only", "source": "environment info['log']['duplicate_scans']", "definition": "mean last_duplicate_scans at reward time", "aggregation": "per-step; per-update/window descriptive summary", "future": "yes, diagnostic"},
    {"metric": "reach-violation metric", "status": "AVAILABLE — diagnostic only", "source": "environment info['log']['reach_violation']", "definition": "mean last_reach_violation at reward time", "aggregation": "per-step; per-update/window descriptive summary", "future": "yes, diagnostic"},
    {"metric": "actor loss", "status": "AVAILABLE — diagnostic only", "source": "reviewed actor step receipts", "definition": "source-returned loss_value for each planned actor step", "aggregation": "per-update/window min/max/mean", "future": "yes, diagnostic"},
    {"metric": "critic loss", "status": "AVAILABLE — diagnostic only", "source": "reviewed critic minibatch receipts", "definition": "source-returned critic_loss for each planned critic step", "aggregation": "per-update/window min/max/mean", "future": "yes, diagnostic"},
    {"metric": "actor gradient norm", "status": "AVAILABLE — diagnostic only", "source": "reviewed actor step receipts", "definition": "aggregate_gradient_norm before the authorized step", "aggregation": "per-update/window min/max/mean", "future": "yes, diagnostic"},
    {"metric": "critic gradient norm", "status": "AVAILABLE — diagnostic only", "source": "reviewed critic minibatch receipts", "definition": "aggregate_gradient_norm before the authorized step", "aggregation": "per-update/window min/max/mean", "future": "yes, diagnostic"},
    {"metric": "policy entropy", "status": "NOT AVAILABLE — no existing authoritative basis", "source": "not exposed by reviewed actor mutation receipts", "definition": "no second actor evaluation or RNG-perturbing forward is permitted", "aggregation": "NOT AVAILABLE", "future": "no"},
    {"metric": "valid-nonzero critic count", "status": "AVAILABLE — authoritative direct", "source": "unchanged CG classification receipts", "definition": "count(VALID_NONZERO_UPDATE)", "aggregation": "per-update/window/run", "future": "yes"},
    {"metric": "valid-zero-effective critic count", "status": "AVAILABLE — authoritative direct", "source": "unchanged CG classification receipts", "definition": "count(VALID_ZERO_EFFECTIVE_UPDATE)", "aggregation": "per-update/window/run", "future": "yes"},
    {"metric": "actor action/proposal distribution", "status": "AVAILABLE — diagnostic only", "source": "immutable EventProposalResolution.raw_action_ids and admitted_effective_assignment", "definition": "histograms of sampled action IDs and admitted effective task IDs; noop remains distinct", "aggregation": "per-step/update/window/run histograms", "future": "yes, diagnostic"},
)


def _tensor_digest(value: torch.Tensor) -> str:
    captured = value.detach().contiguous().cpu()
    digest = hashlib.sha256()
    digest.update(str(tuple(captured.shape)).encode("ascii"))
    digest.update(str(captured.dtype).encode("ascii"))
    digest.update(captured.numpy().tobytes())
    return digest.hexdigest()


def _finite_float(value: object, *, field: str) -> float:
    if type(value) is torch.Tensor:
        if value.numel() != 1:
            raise RuntimeError(f"STOP — B2-T2 OBSERVABILITY-{field}-SHAPE")
        result = float(value.detach().cpu().item())
    else:
        result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"STOP — B2-T2 OBSERVABILITY-{field}-NONFINITE")
    return result


def _tensor_stats(value: torch.Tensor, *, field: str) -> dict[str, object]:
    if type(value) is not torch.Tensor or value.numel() == 0:
        raise RuntimeError(f"STOP — B2-T2 OBSERVABILITY-{field}-TENSOR")
    captured = value.detach().to(dtype=torch.float64).cpu().reshape(-1)
    if not bool(torch.isfinite(captured).all().item()):
        raise RuntimeError(f"STOP — B2-T2 OBSERVABILITY-{field}-NONFINITE")
    return {
        "count": int(captured.numel()),
        "sum": float(captured.sum().item()),
        "min": float(captured.min().item()),
        "max": float(captured.max().item()),
        "mean": float(captured.mean().item()),
    }


def _histogram(values: torch.Tensor) -> dict[str, int]:
    flat = values.detach().to(dtype=torch.int64).cpu().reshape(-1).tolist()
    return {str(key): int(value) for key, value in sorted(Counter(int(item) for item in flat).items())}


def _event_name(event: object) -> str:
    value = getattr(getattr(event, "event_type", None), "value", None)
    if type(value) is not str:
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-LIFECYCLE-EVENT-TYPE")
    return value


def _source_projection(result: object) -> dict[str, object]:
    raw = result.environment_result
    if type(raw) is not tuple or len(raw) != 5 or not isinstance(raw[1], Mapping):
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-ENVIRONMENT-RESULT-CONTRACT")
    reward_digests = {
        str(name): _tensor_digest(value) for name, value in sorted(raw[1].items())
    }
    info = raw[4]
    log = info.get("log", {}) if isinstance(info, Mapping) else {}
    info_values = {
        name: _finite_float(log[name], field=name.upper())
        for name in ("coverage_ratio", "new_viewpoints", "duplicate_scans", "reach_violation", "mean_reward")
        if name in log
    }
    state = result.current_publication.lifecycle_state
    terminal = []
    for row in result.terminal_historical_payload:
        terminal.append(
            {
                "env_id": int(row.env_id),
                "task_state": _tensor_digest(row.updated_task_state),
                "ownership": _tensor_digest(row.updated_ownership),
                "completion_count": _tensor_digest(row.completion_count),
                "coverage": _tensor_digest(row.coverage_after_transition),
                "completed": _tensor_digest(row.completed_tasks),
                "released": _tensor_digest(row.released_tasks),
                "new_failed": _tensor_digest(row.new_failed_pairs),
                "events": tuple(_event_name(event) for event in row.lifecycle_events),
            }
        )
    return {
        "reward_digests": reward_digests,
        "info_values": info_values,
        "raw_action_ids": _tensor_digest(result.resolution.raw_action_ids),
        "effective_assignment": _tensor_digest(result.admitted_effective_assignment),
        "current_task_state": _tensor_digest(state.task_state),
        "current_robot_state": _tensor_digest(state.robot_state),
        "current_ownership": _tensor_digest(state.ownership),
        "current_failed_pairs": _tensor_digest(state.cumulative_failed_pairs),
        "current_completion_count": _tensor_digest(state.completion_count),
        "terminal": terminal,
    }


def _projection_digest(result: object) -> str:
    encoded = json.dumps(_source_projection(result), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _state_counts(task_state: torch.Tensor, codes: Mapping[str, int]) -> dict[str, int]:
    if task_state.ndim != 1:
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-TASK-STATE-SHAPE")
    return {
        name.lower(): int((task_state == int(code)).sum().item())
        for name, code in codes.items()
    }


def capture_step_observability(
    result: object,
    *,
    task_state_codes: Mapping[str, int] | None = None,
) -> dict[str, object]:
    """Capture one read-only step row and prove the receipt was unchanged."""

    if task_state_codes is None:
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
            TaskLifecycleState,
        )

        task_state_codes = {
            member.name: int(member) for member in TaskLifecycleState
        }

    source_before = _projection_digest(result)
    raw = result.environment_result
    reward_by_agent = {
        str(name): _tensor_stats(value, field=f"REWARD-{name}")
        for name, value in sorted(raw[1].items())
    }
    team_reward_sum = sum(float(item["sum"]) for item in reward_by_agent.values())
    info = raw[4]
    log = info.get("log", {}) if isinstance(info, Mapping) else {}
    info_metrics = {
        name: _finite_float(log[name], field=name.upper())
        for name in ("coverage_ratio", "new_viewpoints", "duplicate_scans", "reach_violation", "mean_reward")
        if name in log
    }
    required_info = {"coverage_ratio", "new_viewpoints", "duplicate_scans", "reach_violation"}
    if not required_info.issubset(info_metrics):
        raise RuntimeError(
            "STOP — B2-T2 OBSERVABILITY-REQUIRED-INFO-MISSING: "
            f"{sorted(required_info - set(info_metrics))}"
        )
    if not 0.0 <= info_metrics["coverage_ratio"] <= 1.0:
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-COVERAGE-RANGE")

    codes = dict(task_state_codes)
    if tuple(codes) != (
        "AVAILABLE",
        "CLAIMED",
        "NAVIGATING",
        "ALIGNING",
        "COMPLETED",
        "TEAM_INFEASIBLE",
    ):
        raise RuntimeError("STOP — B2-T2 OBSERVABILITY-TASK-STATE-DOMAIN")
    current = result.current_publication.lifecycle_state
    current_env_ids = current.env_id.detach().cpu().tolist()
    current_task_state = current.task_state.detach().cpu()
    current_ownership = current.ownership.detach().cpu()
    current_completion = current.completion_count.detach().cpu()
    terminal_by_env = {int(row.env_id): row for row in result.terminal_historical_payload}
    state_rows: list[dict[str, object]] = []
    completed_signal_count = 0
    released_signal_count = 0
    new_failed_pair_count = 0
    terminal_events: list[object] = []
    for env_index, env_id_value in enumerate(current_env_ids):
        env_id = int(env_id_value)
        terminal_row = terminal_by_env.get(env_id)
        if terminal_row is None:
            state_tensor = current_task_state[env_index]
            ownership = current_ownership[env_index]
            completion = current_completion[env_index]
            coverage_count = int((state_tensor == codes["COMPLETED"]).sum().item())
            basis = "current_episode_post_transition"
        else:
            state_tensor = terminal_row.updated_task_state.detach().cpu()
            ownership = terminal_row.updated_ownership.detach().cpu()
            completion = terminal_row.completion_count.detach().cpu()
            coverage_count = int(terminal_row.coverage_after_transition.detach().cpu().to(torch.int64).sum().item())
            completed_signal_count += int(terminal_row.completed_tasks.detach().cpu().to(torch.int64).sum().item())
            released_signal_count += int(terminal_row.released_tasks.detach().cpu().to(torch.int64).sum().item())
            new_failed_pair_count += int(terminal_row.new_failed_pairs.detach().cpu().to(torch.int64).sum().item())
            terminal_events.extend(terminal_row.lifecycle_events)
            basis = "terminal_pre_reset_historical"
        counts = _state_counts(state_tensor, codes)
        state_rows.append(
            {
                "env_id": env_id,
                "basis": basis,
                "task_state_counts": counts,
                "owned_robot_count": int((ownership >= 0).sum().item()),
                "completion_count_by_robot": tuple(int(item) for item in completion.reshape(-1).tolist()),
                "covered_viewpoint_count": coverage_count,
            }
        )

    current_result = result.current_publication.result
    nonterminal_events = [] if current_result is None else [
        event for event in current_result.lifecycle_events
        if int(event.env_id) not in terminal_by_env
    ]
    events = tuple(nonterminal_events) + tuple(terminal_events)
    event_histogram = dict(sorted(Counter(_event_name(event) for event in events).items()))
    completion_events = int(event_histogram.get("task_completed", 0))
    release_events = int(event_histogram.get("task_released", 0))
    failure_events = int(event_histogram.get("terminal_pair_failure_recorded", 0))
    aggregate_states = {
        key: sum(int(row["task_state_counts"][key]) for row in state_rows)
        for key in (name.lower() for name in codes)
    }
    claimed_executing = sum(
        aggregate_states[name] for name in ("claimed", "navigating", "aligning")
    )
    raw_action_ids = result.resolution.raw_action_ids
    effective = result.admitted_effective_assignment
    source_after = _projection_digest(result)
    observer_mutations = int(source_before != source_after)
    if observer_mutations:
        raise RuntimeError("STOP — B2-T2 OBSERVER-MUTATED-AUTHORITATIVE-SOURCE")
    return {
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "team_reward_sum": team_reward_sum,
        "reward_by_agent": reward_by_agent,
        "environment_info_metrics": info_metrics,
        "task_state_rows": tuple(state_rows),
        "task_state_aggregate": aggregate_states,
        "completed_viewpoint_count": aggregate_states["completed"],
        "claimed_executing_task_count": claimed_executing,
        "available_task_count": aggregate_states["available"],
        "team_infeasible_task_count": aggregate_states["team_infeasible"],
        "task_completion_events": completion_events,
        "release_events": release_events,
        "failure_events": failure_events,
        "reassignment_events": "NOT AVAILABLE",
        "completed_signal_count": completed_signal_count,
        "released_signal_count": released_signal_count,
        "new_failed_pair_count": new_failed_pair_count,
        "lifecycle_event_histogram": event_histogram,
        "raw_action_histogram": _histogram(raw_action_ids),
        "effective_assignment_histogram": _histogram(effective),
        "raw_action_shape": tuple(int(item) for item in raw_action_ids.shape),
        "effective_assignment_shape": tuple(int(item) for item in effective.shape),
        "source_digest_before": source_before,
        "source_digest_after": source_after,
        "observer_mutation_count": 0,
    }


def schema_artifact() -> dict[str, object]:
    return {
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "metrics": OBSERVABILITY_SCHEMA,
        "observer_authority": "read_only_receipt_projection",
        "second_source_of_truth": False,
        "policy_forward_calls_added": 0,
        "environment_steps_added": 0,
        "production_semantic_modifications": 0,
    }


def run_pure_qualification() -> dict[str, object]:
    """Exercise shape/range/source extraction with detached synthetic receipts."""

    test_codes = {
        "AVAILABLE": 0,
        "CLAIMED": 1,
        "NAVIGATING": 2,
        "ALIGNING": 3,
        "COMPLETED": 4,
        "TEAM_INFEASIBLE": 5,
    }

    class Event:
        def __init__(self, env_id: int, value: str) -> None:
            self.env_id = env_id
            self.event_type = SimpleNamespace(value=value)

    current_state = SimpleNamespace(
        env_id=torch.tensor([0, 1], dtype=torch.int64),
        task_state=torch.tensor(
            [
                [test_codes["AVAILABLE"]] * 3,
                [test_codes["AVAILABLE"], test_codes["NAVIGATING"], test_codes["COMPLETED"]],
            ],
            dtype=torch.int64,
        ),
        robot_state=torch.zeros((2, 2), dtype=torch.int64),
        ownership=torch.tensor([[-1, -1], [1, -1]], dtype=torch.int64),
        cumulative_failed_pairs=torch.zeros((2, 2, 3), dtype=torch.bool),
        completion_count=torch.tensor([[0, 0], [0, 1]], dtype=torch.int64),
    )
    terminal = SimpleNamespace(
        env_id=0,
        updated_task_state=torch.tensor(
            [test_codes["COMPLETED"], test_codes["AVAILABLE"], test_codes["TEAM_INFEASIBLE"]],
            dtype=torch.int64,
        ),
        updated_ownership=torch.tensor([-1, -1], dtype=torch.int64),
        completion_count=torch.tensor([1, 0], dtype=torch.int64),
        coverage_after_transition=torch.tensor([True, False, False]),
        completed_tasks=torch.tensor([True, False, False]),
        released_tasks=torch.tensor([False, False, False]),
        new_failed_pairs=torch.zeros((2, 3), dtype=torch.bool),
        lifecycle_events=(Event(0, "task_completed"),),
    )
    result = SimpleNamespace(
        environment_result=(
            {},
            {"robot_0": torch.tensor([1.0, 2.0]), "robot_1": torch.tensor([3.0, 4.0])},
            {},
            {},
            {"log": {"coverage_ratio": torch.tensor(1.0 / 3.0), "new_viewpoints": torch.tensor(0.5), "duplicate_scans": torch.tensor(0.0), "reach_violation": torch.tensor(0.25), "mean_reward": torch.tensor(2.5)}},
        ),
        resolution=SimpleNamespace(raw_action_ids=torch.tensor([[0, 3], [1, 2]], dtype=torch.int64)),
        admitted_effective_assignment=torch.tensor([[0, -1], [1, 2]], dtype=torch.int64),
        current_publication=SimpleNamespace(
            lifecycle_state=current_state,
            result=SimpleNamespace(lifecycle_events=(Event(1, "task_completed"),)),
        ),
        terminal_historical_payload=(terminal,),
    )
    cpu_rng_before = torch.random.get_rng_state().clone()
    first = capture_step_observability(result, task_state_codes=test_codes)
    second = capture_step_observability(result, task_state_codes=test_codes)
    cpu_rng_after = torch.random.get_rng_state().clone()
    assertions = {
        "repeat_exact": first == second,
        "rng_unchanged": torch.equal(cpu_rng_before, cpu_rng_after),
        "observer_mutations_zero": first["observer_mutation_count"] == 0,
        "team_reward_sum": first["team_reward_sum"] == 10.0,
        "completed_viewpoints": first["completed_viewpoint_count"] == 2,
        "coverage_range": 0.0 <= first["environment_info_metrics"]["coverage_ratio"] <= 1.0,
        "completion_events": first["task_completion_events"] == 2,
        "action_count": sum(first["raw_action_histogram"].values()) == 4,
        "schema_complete": len(OBSERVABILITY_SCHEMA) == 24,
    }
    return {
        "schema_version": "b2_t2_observer_pure_qualification_v1",
        "pass": all(assertions.values()),
        "assertions": assertions,
        "observer_mutation_count": 0,
        "metric_count": len(OBSERVABILITY_SCHEMA),
        "sample": first,
    }


if __name__ == "__main__":
    print(json.dumps(run_pure_qualification(), indent=2, sort_keys=True))
