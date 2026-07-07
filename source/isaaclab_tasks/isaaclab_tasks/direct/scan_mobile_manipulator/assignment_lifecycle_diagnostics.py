"""Shared passive lifecycle diagnostics adapter.

This module wires standardized assignment proposals into the passive lifecycle
transition logger. It is diagnostics-only: it never returns effective
assignments, changes masks, latches targets, or invokes controller/env logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
from pathlib import Path
from typing import Any

import torch

try:
    from .assignment_lifecycle import AssignmentLifecycleTransitionLogger
except ImportError:  # pragma: no cover - supports direct script-style imports.
    from assignment_lifecycle import AssignmentLifecycleTransitionLogger


ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION = "phase9g6c_assignment_lifecycle_diagnostics_v1"

EVENT_SCHEMA_FIELDS = [
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

COUNTED_EVENT_TYPES = [
    "attempt_started_proxy",
    "attempt_continued_proxy",
    "noop_idle_proxy",
    "noop_after_active_ambiguous",
    "switch_request_proxy",
    "target_completed_proxy",
    "target_completed_by_teammate_proxy",
    "active_target_became_covered_proxy",
    "budget_failure_proxy",
    "release_proxy",
    "exact_claim_conflict_proxy",
    "unavailable_target_proposal_proxy",
    "invalid_assignment_proposal_proxy",
    "reset_proxy",
]


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return _json_safe(value.item())
        return _json_safe(value.detach().cpu().tolist())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def _metadata_get(method_metadata: Mapping[str, Any] | object | None, key: str, default: Any = None) -> Any:
    if method_metadata is None:
        return default
    if isinstance(method_metadata, Mapping):
        return method_metadata.get(key, default)
    return getattr(method_metadata, key, default)


def _as_env_ids(env_ids: torch.Tensor | Sequence[int] | None, *, device: torch.device) -> torch.Tensor | None:
    if env_ids is None:
        return None
    if isinstance(env_ids, torch.Tensor):
        return env_ids.to(device=device, dtype=torch.long).flatten().clone()
    return torch.tensor(list(env_ids), dtype=torch.long, device=device).flatten()


def _as_episode_ids(
    episode_ids: torch.Tensor | Sequence[int] | int | None,
    *,
    num_envs: int,
    device: torch.device,
) -> torch.Tensor | None:
    if episode_ids is None:
        return None
    if isinstance(episode_ids, torch.Tensor):
        tensor = episode_ids.to(device=device, dtype=torch.long).flatten().clone()
    elif isinstance(episode_ids, int):
        tensor = torch.full((num_envs,), int(episode_ids), dtype=torch.long, device=device)
    else:
        tensor = torch.tensor(list(episode_ids), dtype=torch.long, device=device).flatten()
    if tuple(tensor.shape) != (num_envs,):
        raise ValueError(f"episode_ids must have shape [{num_envs}], got {tuple(tensor.shape)}")
    return tensor


def normalize_assignment_lifecycle_proposal(
    assignment_proposal: torch.Tensor,
    *,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
) -> torch.Tensor:
    """Validate and clone a standardized lifecycle proposal.

    The proposal must already use decoded lifecycle convention: target ids
    ``0..N-1`` or ``-1`` for noop. Raw discrete noop id ``N`` is rejected.
    """

    if not isinstance(assignment_proposal, torch.Tensor):
        raise TypeError(
            f"assignment_proposal must be a torch.Tensor, got {type(assignment_proposal).__name__}"
        )
    expected_shape = (int(num_envs), int(num_robots))
    if tuple(assignment_proposal.shape) != expected_shape:
        raise ValueError(f"assignment_proposal must have shape {expected_shape}, got {tuple(assignment_proposal.shape)}")
    if torch.is_floating_point(assignment_proposal):
        integer = torch.isfinite(assignment_proposal) & (assignment_proposal == torch.trunc(assignment_proposal))
        if not bool(integer.all()):
            raise ValueError("assignment_proposal must contain finite integer ids")
    proposal = assignment_proposal.to(dtype=torch.long).clone()
    invalid = (proposal < -1) | (proposal >= int(num_tasks))
    if bool(invalid.any()):
        raise ValueError(
            "assignment_proposal must use decoded ids in [-1, num_tasks); "
            "raw discrete noop id N must be decoded to -1 before lifecycle diagnostics"
        )
    return proposal


def make_assignment_lifecycle_post_problem(
    post_step_problem: Mapping[str, Any],
    *,
    covered_after: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Return a shallow post-step problem copy with optional pre-reset coverage.

    Some runtime paths capture terminal coverage before the env reset. The
    lifecycle logger only needs post-step ``viewpoints_covered`` for completion
    events, so this helper preserves that signal without mutating the source
    problem.
    """

    result = dict(post_step_problem)
    if covered_after is not None:
        result["viewpoints_covered"] = covered_after.clone()
    return result


def build_assignment_lifecycle_external_diagnostics(
    *,
    assignment_proposal: torch.Tensor,
    info: Mapping[str, Any] | None = None,
    completed_by_robot_ids: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Normalize existing diagnostics into logger-supported external signals.

    This function does not create new failure criteria. It only translates
    already-supplied budget trigger diagnostics into ``budget_failure_pairs``.
    """

    diagnostics: dict[str, Any] = {}
    if completed_by_robot_ids is not None:
        diagnostics["completed_by_robot_ids"] = completed_by_robot_ids.clone()
    if info is None:
        return diagnostics

    memory_info = info.get("assignment_failed_pair_memory") if isinstance(info, Mapping) else None
    pairs: list[dict[str, Any]] = []
    if isinstance(memory_info, Mapping):
        robot_ids_by_env = memory_info.get("last_trigger_robot_ids")
        target_ids_by_env = memory_info.get("last_trigger_target_ids")
        reasons_by_env = memory_info.get("last_trigger_reason")
        if isinstance(robot_ids_by_env, Sequence) and isinstance(target_ids_by_env, Sequence):
            for env_id, robot_ids in enumerate(robot_ids_by_env):
                if not isinstance(robot_ids, Sequence) or isinstance(robot_ids, (str, bytes)):
                    continue
                target_ids = target_ids_by_env[env_id] if env_id < len(target_ids_by_env) else []
                reasons = reasons_by_env[env_id] if isinstance(reasons_by_env, Sequence) and env_id < len(reasons_by_env) else []
                for index, robot_id in enumerate(robot_ids):
                    if index >= len(target_ids):
                        continue
                    reason = reasons[index] if isinstance(reasons, Sequence) and index < len(reasons) else "budget_trigger"
                    pairs.append(
                        {
                            "env_id": int(env_id),
                            "robot_id": int(robot_id),
                            "target_id": int(target_ids[index]),
                            "reason": str(reason),
                        }
                    )

    if not pairs and isinstance(info, Mapping):
        cooldown_info = info.get("assignment_cooldown")
        if isinstance(cooldown_info, Mapping):
            budget_mask = cooldown_info.get("budget_last_triggered_by_budget")
            if isinstance(budget_mask, torch.Tensor):
                mask = budget_mask.to(dtype=torch.bool)
                for env_id, robot_id in torch.nonzero(mask, as_tuple=False).detach().cpu().tolist():
                    target_id = int(assignment_proposal[int(env_id), int(robot_id)].item())
                    if target_id >= 0:
                        pairs.append(
                            {
                                "env_id": int(env_id),
                                "robot_id": int(robot_id),
                                "target_id": target_id,
                                "reason": "budget_trigger",
                            }
                        )
    if pairs:
        diagnostics["budget_failure_pairs"] = pairs
    return diagnostics


class AssignmentLifecycleDiagnosticsAdapter:
    """Default-off adapter from runtime rows to lifecycle JSONL/summary diagnostics."""

    def __init__(
        self,
        *,
        enabled: bool,
        num_envs: int,
        num_robots: int,
        num_tasks: int,
        device: torch.device | str = "cpu",
        method_name: str = "unknown",
        output_dir: str | Path | None = None,
        proposal_type: str | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.num_envs = int(num_envs)
        self.num_robots = int(num_robots)
        self.num_tasks = int(num_tasks)
        self.device = torch.device(device)
        self.method_name = str(method_name)
        self.default_proposal_type = proposal_type
        self.output_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else None
        self.events_path = self.output_dir / "assignment_lifecycle_events.jsonl" if self.output_dir is not None else None
        self.summary_path = self.output_dir / "assignment_lifecycle_summary.json" if self.output_dir is not None else None
        self.logger: AssignmentLifecycleTransitionLogger | None = None
        self._finalized = False
        self._pending_pre_problem_tensors: dict[str, torch.Tensor] | None = None
        self._pending_assignment_proposal: torch.Tensor | None = None
        self._episode_ids = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._event_counts = {event_type: 0 for event_type in COUNTED_EVENT_TYPES}
        self._total_events = 0
        self._total_steps_observed = 0
        self._hypothetical_conflict_loser_count = 0
        self._attempt_age_min: float | None = None
        self._attempt_age_max: float | None = None
        self._attempt_age_sum = 0.0
        self._attempt_age_count = 0

        if self.enabled:
            if self.output_dir is None:
                raise ValueError("output_dir is required when lifecycle diagnostics are enabled")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.events_path.write_text("", encoding="utf-8")
            self.logger = AssignmentLifecycleTransitionLogger(
                num_envs=self.num_envs,
                num_robots=self.num_robots,
                num_tasks=self.num_tasks,
                device=self.device,
                retain_events=True,
            )

    @property
    def behavior_changed(self) -> bool:
        return False

    def observe_pre_step(
        self,
        *,
        problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
        method_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return self.snapshot()
        assert self.logger is not None
        self._update_episode_ids(episode_ids)
        proposal = normalize_assignment_lifecycle_proposal(
            assignment_proposal,
            num_envs=self.num_envs,
            num_robots=self.num_robots,
            num_tasks=self.num_tasks,
        ).to(device=self.device)
        self._pending_assignment_proposal = proposal.clone()
        self._pending_pre_problem_tensors = self._clone_core_problem_tensors(problem)
        self.logger.observe_pre_step(
            problem=problem,
            assignment_proposal=proposal,
            method_metadata=self._merged_metadata(method_metadata),
        )
        self._drain_events()
        return self.snapshot()

    def observe_post_step(
        self,
        *,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        post_step_problem: Mapping[str, Any],
        external_diagnostics: Mapping[str, Any] | None = None,
        completed_by_robot_ids: torch.Tensor | None = None,
        done_env_ids: torch.Tensor | Sequence[int] | None = None,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
        method_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return self.snapshot()
        assert self.logger is not None
        self._update_episode_ids(episode_ids)
        proposal = normalize_assignment_lifecycle_proposal(
            assignment_proposal,
            num_envs=self.num_envs,
            num_robots=self.num_robots,
            num_tasks=self.num_tasks,
        ).to(device=self.device)
        self._assert_pending_step(pre_step_problem, proposal)
        assert self._pending_pre_problem_tensors is not None
        external = dict(external_diagnostics or {})
        if completed_by_robot_ids is not None:
            external["completed_by_robot_ids"] = completed_by_robot_ids.clone()
        self.logger.observe_post_step(
            pre_step_problem=self._pending_pre_problem_tensors,
            assignment_proposal=proposal,
            post_step_problem=post_step_problem,
            external_diagnostics=external,
            method_metadata=self._merged_metadata(method_metadata),
        )
        self._total_steps_observed += self.num_envs
        self._update_attempt_age_summary()
        self._drain_events()
        self._pending_pre_problem_tensors = None
        self._pending_assignment_proposal = None

        env_ids = _as_env_ids(done_env_ids, device=self.device)
        if env_ids is not None and env_ids.numel() > 0:
            self.reset_envs(env_ids, episode_ids=episode_ids)
        return self.snapshot()

    def reset_envs(
        self,
        env_ids: torch.Tensor | Sequence[int] | None = None,
        *,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return self.snapshot()
        assert self.logger is not None
        self._update_episode_ids(episode_ids)
        self.logger.reset(env_ids=env_ids, emit_events=True)
        self._drain_events()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "schema_version": ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION,
            "method_name": self.method_name,
            "num_envs": self.num_envs,
            "num_robots": self.num_robots,
            "num_tasks": self.num_tasks,
            "behavior_changed": False,
            "logger_constructed": self.logger is not None,
            "events_path": str(self.events_path) if self.events_path is not None and self.enabled else None,
            "summary_path": str(self.summary_path) if self.summary_path is not None and self.enabled else None,
            "total_steps_observed": int(self._total_steps_observed),
            "total_events": int(self._total_events),
        }

    def finalize(self) -> dict[str, Any]:
        if not self.enabled:
            self._finalized = True
            return self._summary_payload()
        if not self._finalized:
            self._drain_events()
            payload = self._summary_payload()
            assert self.summary_path is not None
            self.summary_path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
            self._finalized = True
            return payload
        return self._summary_payload()

    def _merged_metadata(self, method_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
        metadata = dict(method_metadata or {})
        metadata.setdefault("method_name", self.method_name)
        if self.default_proposal_type is not None:
            metadata.setdefault("proposal_type", self.default_proposal_type)
        return metadata

    def _update_episode_ids(self, episode_ids: torch.Tensor | Sequence[int] | int | None) -> None:
        ids = _as_episode_ids(episode_ids, num_envs=self.num_envs, device=self.device)
        if ids is not None:
            self._episode_ids = ids

    def _clone_core_problem_tensors(self, problem: Mapping[str, Any]) -> dict[str, torch.Tensor]:
        clones: dict[str, torch.Tensor] = {}
        for key in ("available_mask", "viewpoints_covered", "cost_matrix"):
            value = problem.get(key)
            if isinstance(value, torch.Tensor):
                clones[key] = value.detach().clone()
        return clones

    def _assert_pending_step(self, pre_step_problem: Mapping[str, Any], assignment_proposal: torch.Tensor) -> None:
        if self._pending_assignment_proposal is None or self._pending_pre_problem_tensors is None:
            raise RuntimeError("observe_post_step called before observe_pre_step for this lifecycle row")
        if not torch.equal(self._pending_assignment_proposal.to(device=self.device), assignment_proposal.to(device=self.device)):
            raise RuntimeError("observe_post_step assignment_proposal does not match pending pre-step proposal")
        for key, expected in self._pending_pre_problem_tensors.items():
            value = pre_step_problem.get(key)
            if not isinstance(value, torch.Tensor):
                raise RuntimeError(f"observe_post_step pre_step_problem missing tensor {key!r}")
            if tuple(value.shape) != tuple(expected.shape):
                raise RuntimeError(
                    f"observe_post_step pre_step_problem tensor {key!r} shape changed since observe_pre_step"
                )

    def _drain_events(self) -> None:
        if not self.enabled or self.logger is None:
            return
        events = self.logger.pop_events()
        if not events:
            return
        assert self.events_path is not None
        with self.events_path.open("a", encoding="utf-8") as file:
            for event in events:
                row = self._normalize_event_row(event)
                self._update_summary_for_event(row)
                file.write(json.dumps(row, sort_keys=True) + "\n")

    def _normalize_event_row(self, event: Mapping[str, Any]) -> dict[str, Any]:
        env_id = int(event.get("env_id", 0))
        method_name = event.get("method_name") or self.method_name
        row = {field: None for field in EVENT_SCHEMA_FIELDS}
        row.update(
            {
                "schema_version": ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION,
                "method_name": str(method_name),
                "proposal_type": event.get("proposal_type", self.default_proposal_type),
                "episode_id": int(self._episode_ids[env_id].item()) if 0 <= env_id < self.num_envs else None,
                "env_id": env_id,
                "step": int(event.get("step", 0)),
                "event_type": str(event.get("event_type", "")),
                "robot_id": event.get("robot_id"),
                "target_id": event.get("target_id"),
                "previous_target_id": event.get("previous_target_id"),
                "new_target_id": event.get("new_target_id"),
                "attempt_age_proxy": event.get("attempt_age_proxy"),
                "failure_reason": event.get("failure_reason", event.get("failure_source")),
                "release_reason": event.get("release_reason", event.get("release_source")),
                "claiming_robot_ids": event.get("claiming_robot_ids", []),
                "claiming_costs": event.get("claiming_costs", []),
                "would_be_winner_robot_id": event.get("would_be_winner_robot_id"),
                "would_be_loser_robot_ids": event.get("would_be_loser_robot_ids", []),
                "arbitration_rule": event.get("arbitration_rule"),
                "fallback_reason": event.get("fallback_reason"),
                "behavior_changed": False,
            }
        )
        return _json_safe(row)

    def _update_summary_for_event(self, row: Mapping[str, Any]) -> None:
        event_type = str(row.get("event_type", ""))
        if event_type in self._event_counts:
            self._event_counts[event_type] += 1
        self._total_events += 1
        if event_type == "exact_claim_conflict_proxy":
            losers = row.get("would_be_loser_robot_ids") or []
            if isinstance(losers, Sequence) and not isinstance(losers, (str, bytes)):
                self._hypothetical_conflict_loser_count += len(losers)

    def _update_attempt_age_summary(self) -> None:
        if self.logger is None:
            return
        snapshot = self.logger.snapshot()
        ages = snapshot["attempt_age_proxy"].detach().to(device="cpu", dtype=torch.float32).flatten()
        if ages.numel() == 0:
            return
        min_age = float(ages.min().item())
        max_age = float(ages.max().item())
        sum_age = float(ages.sum().item())
        self._attempt_age_min = min_age if self._attempt_age_min is None else min(self._attempt_age_min, min_age)
        self._attempt_age_max = max_age if self._attempt_age_max is None else max(self._attempt_age_max, max_age)
        self._attempt_age_sum += sum_age
        self._attempt_age_count += int(ages.numel())

    def _summary_payload(self) -> dict[str, Any]:
        mean_age = (
            self._attempt_age_sum / float(self._attempt_age_count)
            if self._attempt_age_count > 0
            else 0.0
        )
        payload: dict[str, Any] = {
            "schema_version": ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION,
            "enabled": self.enabled,
            "method_name": self.method_name,
            "num_envs": self.num_envs,
            "num_robots": self.num_robots,
            "num_tasks": self.num_tasks,
            "total_steps_observed": int(self._total_steps_observed),
            "total_events": int(self._total_events),
            "hypothetical_conflict_loser_count": int(self._hypothetical_conflict_loser_count),
            "attempt_age_proxy_min": float(self._attempt_age_min) if self._attempt_age_min is not None else 0.0,
            "attempt_age_proxy_mean": float(mean_age),
            "attempt_age_proxy_max": float(self._attempt_age_max) if self._attempt_age_max is not None else 0.0,
            "behavior_changed": False,
            "events_path": str(self.events_path) if self.events_path is not None and self.enabled else None,
            "summary_path": str(self.summary_path) if self.summary_path is not None and self.enabled else None,
        }
        for event_type in COUNTED_EVENT_TYPES:
            payload[f"{event_type}_count"] = int(self._event_counts[event_type])
        return payload


__all__ = [
    "ASSIGNMENT_LIFECYCLE_DIAGNOSTICS_SCHEMA_VERSION",
    "AssignmentLifecycleDiagnosticsAdapter",
    "EVENT_SCHEMA_FIELDS",
    "build_assignment_lifecycle_external_diagnostics",
    "make_assignment_lifecycle_post_problem",
    "normalize_assignment_lifecycle_proposal",
]
