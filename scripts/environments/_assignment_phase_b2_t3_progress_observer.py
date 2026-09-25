"""Read-only task-progress observer for Phase B2-T3.

The observer projects already-authoritative environment and P2 state.  It does
not advance the environment, derive lifecycle authority, or mutate RNG/state.
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from typing import Any

import torch


SCHEMA_VERSION = "b2_t3_progress_observability_v1"

PROGRESS_SCHEMA = (
    {"signal": "robot pose", "status": "AVAILABLE", "source": "assignment problem base_pos/base_yaw"},
    {"signal": "task/viewpoint pose", "status": "AVAILABLE", "source": "assignment problem viewpoint_pos/viewpoint_quat"},
    {"signal": "scanner pose", "status": "AVAILABLE", "source": "assignment problem scanner_pos/scanner_quat"},
    {"signal": "current owned task", "status": "AVAILABLE", "source": "canonical P2 ownership"},
    {"signal": "robot lifecycle state", "status": "AVAILABLE", "source": "canonical P2 robot_state"},
    {"signal": "task lifecycle state", "status": "AVAILABLE", "source": "canonical P2 task_state"},
    {"signal": "path/distance cost", "status": "AVAILABLE", "source": "assignment problem cost_matrix"},
    {"signal": "current distance-to-target", "status": "AVAILABLE", "source": "selected cost_matrix cell"},
    {"signal": "arrival flag", "status": "NOT AVAILABLE", "source": "no named production signal"},
    {"signal": "controller command", "status": "AVAILABLE", "source": "admitted effective assignment and emitted continuous action"},
    {"signal": "alignment state", "status": "NOT AVAILABLE", "source": "no named production state"},
    {"signal": "scan/completion predicate", "status": "AVAILABLE", "source": "read-only _compute_scan_candidate"},
    {"signal": "elapsed execution steps", "status": "AVAILABLE-DERIVED", "source": "observer boundary count, not lifecycle authority"},
    {"signal": "no-progress counter", "status": "NOT AVAILABLE", "source": "no production counter"},
    {"signal": "release/failure reason", "status": "AVAILABLE", "source": "canonical lifecycle events and termination reason"},
    {"signal": "coverage", "status": "AVAILABLE", "source": "environment viewpoints_covered"},
    {"signal": "completion count", "status": "AVAILABLE", "source": "canonical P2 completion_count"},
)


def _tensor_digest(value: torch.Tensor) -> str:
    captured = value.detach().contiguous().cpu()
    digest = hashlib.sha256()
    digest.update(str(tuple(captured.shape)).encode("ascii"))
    digest.update(str(captured.dtype).encode("ascii"))
    digest.update(captured.numpy().tobytes())
    return digest.hexdigest()


def _event_name(event: object) -> str:
    return str(getattr(getattr(event, "event_type", None), "value", "UNKNOWN"))


def _projection(raw_env: object, publication: object) -> str:
    state = publication.lifecycle_state  # type: ignore[attr-defined]
    tensors = (
        raw_env.base_pos,  # type: ignore[attr-defined]
        raw_env.base_yaw,  # type: ignore[attr-defined]
        raw_env.scanner_pos,  # type: ignore[attr-defined]
        raw_env.scanner_quat,  # type: ignore[attr-defined]
        raw_env.viewpoints_covered,  # type: ignore[attr-defined]
        raw_env.dwell_counter,  # type: ignore[attr-defined]
        raw_env.episode_length_buf,  # type: ignore[attr-defined]
        state.task_state,
        state.robot_state,
        state.ownership,
        state.cumulative_failed_pairs,
        state.completion_count,
        publication.episode_generation,  # type: ignore[attr-defined]
        publication.transition_generation,  # type: ignore[attr-defined]
    )
    result = publication.result  # type: ignore[attr-defined]
    payload = {
        "common_step_counter": int(raw_env.common_step_counter),  # type: ignore[attr-defined]
        "store_version": int(publication.store_version),  # type: ignore[attr-defined]
        "tensors": tuple(_tensor_digest(value) for value in tensors),
        "events": () if result is None else tuple(_event_name(event) for event in result.lifecycle_events),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def capture_progress_row(
    raw_env: object,
    publication: object,
    *,
    global_step: int,
    target_robot: int,
    target_task: int,
    decision_required: bool,
    policy_call_count: int,
    proposal_action_id: int | None,
    effective_assignment: torch.Tensor | None,
    boundary_kind: str,
) -> dict[str, object]:
    """Capture one target-pair row and prove the projection/RNG stayed exact."""

    cpu_rng_before = torch.random.get_rng_state().clone()
    cuda_rng_before = torch.cuda.get_rng_state().clone() if torch.cuda.is_available() else None
    source_before = _projection(raw_env, publication)
    problem = raw_env.get_assignment_problem()  # type: ignore[attr-defined]
    state = publication.lifecycle_state  # type: ignore[attr-defined]
    candidate = raw_env._compute_scan_candidate()  # type: ignore[attr-defined]
    result = publication.result  # type: ignore[attr-defined]
    events = () if result is None else tuple(result.lifecycle_events)
    event_rows = tuple(
        {
            "event": _event_name(event),
            "env_id": int(event.env_id),
            "robot_id": int(event.robot_id),
            "task_id": int(event.task_id),
        }
        for event in events
    )
    task_completed = any(
        row["event"] == "task_completed"
        and row["robot_id"] == target_robot
        and row["task_id"] == target_task
        for row in event_rows
    )
    row = {
        "schema_version": SCHEMA_VERSION,
        "global_physical_step": int(global_step),
        "episode_generation": int(publication.episode_generation[0].item()),  # type: ignore[attr-defined]
        "transition_generation": int(publication.transition_generation[0].item()),  # type: ignore[attr-defined]
        "robot_id": int(target_robot),
        "task_id": int(target_task),
        "robot_state": int(state.robot_state[0, target_robot].item()),
        "task_state": int(state.task_state[0, target_task].item()),
        "owner": int(state.ownership[0, target_task].item()),
        "decision_required": bool(decision_required),
        "policy_call_count": int(policy_call_count),
        "boundary_kind": str(boundary_kind),
        "proposal_action_id": None if proposal_action_id is None else int(proposal_action_id),
        "effective_assignment": None
        if effective_assignment is None
        else int(effective_assignment[0, target_robot].item()),
        "distance_to_target": float(problem["cost_matrix"][0, target_robot, target_task].item()),
        "base_position": tuple(float(item) for item in problem["base_pos"][0, target_robot].detach().cpu().tolist()),
        "scanner_position": tuple(float(item) for item in problem["scanner_pos"][0, target_robot].detach().cpu().tolist()),
        "target_position": tuple(float(item) for item in problem["viewpoint_pos"][0, target_task].detach().cpu().tolist()),
        "scan_candidate": bool(candidate[0, target_robot, target_task].item()),
        "dwell_count": int(raw_env.dwell_counter[0, target_robot, target_task].item()),  # type: ignore[attr-defined]
        "events": event_rows,
        "task_completed_event": bool(task_completed),
        "completed_task_count": int((state.task_state[0] == 4).sum().item()),
        "robot_completion_count": int(state.completion_count[0, target_robot].item()),
        "covered_viewpoint_count": int(raw_env.viewpoints_covered[0].sum().item()),  # type: ignore[attr-defined]
        "coverage_ratio": float(raw_env.viewpoints_covered[0].float().mean().item()),  # type: ignore[attr-defined]
        "episode_progress_steps": int(raw_env.episode_length_buf[0].item()),  # type: ignore[attr-defined]
        "terminal_reason": int(state.termination_reason[0].item()),
    }
    source_after = _projection(raw_env, publication)
    cpu_rng_after = torch.random.get_rng_state()
    cuda_rng_after = torch.cuda.get_rng_state() if torch.cuda.is_available() else None
    mutation = int(
        source_before != source_after
        or not torch.equal(cpu_rng_before, cpu_rng_after)
        or (
            cuda_rng_before is not None
            and (cuda_rng_after is None or not torch.equal(cuda_rng_before, cuda_rng_after))
        )
    )
    if mutation:
        raise RuntimeError("STOP — B2-T3 PROGRESS OBSERVER MUTATED AUTHORITATIVE STATE OR RNG")
    row["source_digest_before"] = source_before
    row["source_digest_after"] = source_after
    row["observer_mutation_count"] = 0
    return row


def schema_artifact() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "signals": PROGRESS_SCHEMA,
        "observer_authority": "read_only_authoritative_projection",
        "second_source_of_truth": False,
        "environment_steps_added": 0,
        "policy_calls_added": 0,
        "observer_mutation_count": 0,
        "production_semantic_modifications": 0,
    }


def run_pure_qualification() -> dict[str, object]:
    class FakeEnv:
        def __init__(self) -> None:
            self.base_pos = torch.zeros((1, 1, 3))
            self.base_yaw = torch.zeros((1, 1))
            self.scanner_pos = torch.tensor([[[0.0, 0.0, 0.0]]])
            self.scanner_quat = torch.tensor([[[1.0, 0.0, 0.0, 0.0]]])
            self.viewpoint_pos = torch.tensor([[[0.3, 0.0, 0.0]]])
            self.viewpoints_covered = torch.zeros((1, 1), dtype=torch.bool)
            self.dwell_counter = torch.zeros((1, 1, 1), dtype=torch.int64)
            self.episode_length_buf = torch.tensor([7], dtype=torch.int64)
            self.common_step_counter = 7

        def get_assignment_problem(self) -> dict[str, torch.Tensor]:
            cost = torch.norm(self.scanner_pos[:, :, None, :] - self.viewpoint_pos[:, None, 0, :], dim=-1)
            return {
                "base_pos": self.base_pos,
                "scanner_pos": self.scanner_pos,
                "viewpoint_pos": self.viewpoint_pos,
                "cost_matrix": cost,
            }

        def _compute_scan_candidate(self) -> torch.Tensor:
            return torch.zeros((1, 1, 1), dtype=torch.bool)

    state = SimpleNamespace(
        task_state=torch.tensor([[1]], dtype=torch.int64),
        robot_state=torch.tensor([[0]], dtype=torch.int64),
        ownership=torch.tensor([[0]], dtype=torch.int64),
        cumulative_failed_pairs=torch.zeros((1, 1, 1), dtype=torch.bool),
        completion_count=torch.zeros((1, 1), dtype=torch.int64),
        termination_reason=torch.zeros((1,), dtype=torch.int64),
    )
    publication = SimpleNamespace(
        lifecycle_state=state,
        episode_generation=torch.tensor([0], dtype=torch.int64),
        transition_generation=torch.tensor([7], dtype=torch.int64),
        store_version=8,
        result=SimpleNamespace(lifecycle_events=()),
    )
    env = FakeEnv()
    kwargs = dict(
        global_step=7,
        target_robot=0,
        target_task=0,
        decision_required=False,
        policy_call_count=0,
        proposal_action_id=None,
        effective_assignment=torch.tensor([[0]], dtype=torch.int64),
        boundary_kind="FORCED_CONTINUATION_ROW",
    )
    before = _projection(env, publication)
    first = capture_progress_row(env, publication, **kwargs)
    second = capture_progress_row(env, publication, **kwargs)
    after = _projection(env, publication)
    assertions = {
        "repeat_exact": first == second,
        "source_exact": before == after,
        "observer_mutation_zero": first["observer_mutation_count"] == 0,
        "distance_exact": abs(float(first["distance_to_target"]) - 0.3) < 1.0e-6,
        "schema_complete": len(PROGRESS_SCHEMA) == 17,
    }
    return {
        "schema_version": "b2_t3_progress_observer_pure_qualification_v1",
        "pass": all(assertions.values()),
        "assertions": assertions,
        "observer_mutation_count": 0,
        "sample": first,
    }


if __name__ == "__main__":
    print(json.dumps(run_pure_qualification(), indent=2, sort_keys=True))
