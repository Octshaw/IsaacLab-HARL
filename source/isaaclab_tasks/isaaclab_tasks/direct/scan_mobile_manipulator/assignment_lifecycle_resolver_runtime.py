"""Runtime adapter for the shared assignment lifecycle resolver.

This adapter wires standardized assignment proposals into
``AssignmentLifecycleResolver`` and records proposal/effective diagnostics. It
does not duplicate resolver behavior logic, call policy inference, invoke
solvers, command controllers, generate masks, change observations, or own env
physics. When disabled it is an absolute pass-through.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
import json
from pathlib import Path
from typing import Any

import torch

try:
    from .assignment_lifecycle_resolver import (
        AssignmentLifecyclePostStepResult,
        AssignmentLifecyclePreStepResult,
        AssignmentLifecycleResolver,
        NO_OWNER,
        NO_TARGET,
        PAIR_FAILED_BUDGET,
        PAIR_RELEASED_BUDGET,
    )
except ImportError:  # pragma: no cover - supports direct script-style imports.
    from assignment_lifecycle_resolver import (  # type: ignore
        AssignmentLifecyclePostStepResult,
        AssignmentLifecyclePreStepResult,
        AssignmentLifecycleResolver,
        NO_OWNER,
        NO_TARGET,
        PAIR_FAILED_BUDGET,
        PAIR_RELEASED_BUDGET,
    )


ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION = "phase9g7d_assignment_lifecycle_resolver_runtime_v1"

RESOLVER_ROW_FIELDS = [
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

RESOLVER_EVENT_TYPES = [
    "attempt_started",
    "attempt_continued_same_target",
    "attempt_continued_noop_contract_c",
    "switch_rejected_executing",
    "exact_claim_conflict_resolved",
    "claim_lost",
    "owned_target_rejected",
    "covered_target_rejected",
    "failed_pair_reclaim_rejected",
    "active_target_infeasible_deferred",
    "target_completed",
    "budget_failure",
    "release_budget_failure",
    "reset",
    "stranded_failed_pair_started",
    "stranded_failed_pair_recovered",
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


def _as_env_ids(env_ids: torch.Tensor | Sequence[int] | None, *, device: torch.device) -> torch.Tensor | None:
    if env_ids is None:
        return None
    if isinstance(env_ids, torch.Tensor):
        return env_ids.to(device=device, dtype=torch.long).flatten().clone()
    return torch.tensor(list(env_ids), dtype=torch.long, device=device).flatten()


def _clone_problem_tensors(problem: Mapping[str, Any]) -> dict[str, torch.Tensor]:
    result: dict[str, torch.Tensor] = {}
    for key in ("available_mask", "feasible_mask", "viewpoints_covered", "cost_matrix"):
        value = problem.get(key)
        if isinstance(value, torch.Tensor):
            result[key] = value.detach().clone()
    return result


def _clone_tensor(value: torch.Tensor | None) -> torch.Tensor | None:
    if value is None:
        return None
    return value.detach().clone()


def _json_cell(value: Any) -> str:
    return json.dumps(_json_safe(value), sort_keys=True)


def select_assignment_lifecycle_passive_input(
    *,
    resolver_enabled: bool,
    assignment_proposal: torch.Tensor,
    effective_assignment: torch.Tensor,
) -> tuple[torch.Tensor, str]:
    """Return the assignment stream passive diagnostics should observe."""

    if resolver_enabled:
        return effective_assignment.detach().clone(), "effective_assignment_from_resolver"
    return assignment_proposal.detach().clone(), "standardized_assignment"


def build_resolver_budget_failure_diagnostics(
    *,
    effective_assignment: torch.Tensor,
    info: Mapping[str, Any] | None = None,
    budget_trigger_mask: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Build resolver budget-failure diagnostics from executed effective targets."""

    pairs: list[dict[str, Any]] = []
    mask = budget_trigger_mask
    if mask is None and isinstance(info, Mapping):
        cooldown_info = info.get("assignment_cooldown")
        if isinstance(cooldown_info, Mapping):
            candidate = cooldown_info.get("budget_last_triggered_by_budget")
            if isinstance(candidate, torch.Tensor):
                mask = candidate
    if isinstance(mask, torch.Tensor):
        bool_mask = mask.to(dtype=torch.bool)
        if tuple(bool_mask.shape) != tuple(effective_assignment.shape):
            raise ValueError(
                "budget_trigger_mask must have the same shape as effective_assignment, "
                f"got {tuple(bool_mask.shape)} and {tuple(effective_assignment.shape)}"
            )
        effective_cpu = effective_assignment.detach().cpu().to(dtype=torch.long)
        for env_id, robot_id in torch.nonzero(bool_mask, as_tuple=False).detach().cpu().tolist():
            target_id = int(effective_cpu[int(env_id), int(robot_id)].item())
            if target_id >= 0:
                pairs.append(
                    {
                        "env_id": int(env_id),
                        "robot_id": int(robot_id),
                        "target_id": target_id,
                        "reason": "budget_trigger",
                    }
                )
    return {"budget_failure_pairs": pairs} if pairs else {}


class AssignmentLifecycleResolverRuntimeAdapter:
    """Shared runtime adapter for the effective-assignment resolver."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        num_envs: int,
        num_robots: int,
        num_tasks: int,
        device: torch.device | str = "cpu",
        method_name: str = "unknown",
        output_dir: str | Path | None = None,
        log_diagnostics: bool = False,
        strict_proposals: bool = True,
    ) -> None:
        self.enabled = bool(enabled)
        self.num_envs = int(num_envs)
        self.num_robots = int(num_robots)
        self.num_tasks = int(num_tasks)
        self.device = torch.device(device)
        self.method_name = str(method_name)
        self.log_diagnostics = bool(log_diagnostics)
        self.output_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else None
        self.events_path = self.output_dir / "assignment_lifecycle_resolver_events.jsonl" if self.output_dir else None
        self.summary_path = self.output_dir / "assignment_lifecycle_resolver_summary.json" if self.output_dir else None
        self.rows_path = self.output_dir / "assignment_lifecycle_resolver_rows.csv" if self.output_dir else None
        self.resolver = AssignmentLifecycleResolver(
            num_envs=self.num_envs,
            num_robots=self.num_robots,
            num_tasks=self.num_tasks,
            device=self.device,
            enabled=self.enabled,
            strict_proposals=bool(strict_proposals),
        )
        self._finalized = False
        self._episode_ids = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._pending_pre_problem: dict[str, torch.Tensor] | None = None
        self._pending_assignment_proposal: torch.Tensor | None = None
        self._pending_effective_assignment: torch.Tensor | None = None
        self._pending_pre_result: AssignmentLifecyclePreStepResult | None = None
        self._pending_active_target_before: torch.Tensor | None = None
        self._pending_task_owner_before: torch.Tensor | None = None
        self._pending_events_by_env: list[list[dict[str, Any]]] = [[] for _ in range(self.num_envs)]
        self._event_buffer: list[dict[str, Any]] = []
        self._event_counts = {event_type: 0 for event_type in RESOLVER_EVENT_TYPES}
        self._total_events = 0
        self._total_steps_observed = 0
        self._proposal_effective_changed_count = 0
        self._behavior_changed = False
        self._active_infeasible_step_count = 0
        self._active_infeasible_streak = torch.zeros(
            self.num_envs,
            self.num_robots,
            dtype=torch.long,
            device=self.device,
        )
        self._active_infeasible_max_streak = 0
        self._active_infeasible_pairs: set[tuple[int, int, int]] = set()
        self._stranded_active = torch.zeros(self.num_envs, self.num_tasks, dtype=torch.bool, device=self.device)
        self._stranded_streak = torch.zeros(self.num_envs, self.num_tasks, dtype=torch.long, device=self.device)
        self._stranded_max_streak = 0
        self._stranded_started_count = 0
        self._stranded_recovered_count = 0

        if self.log_diagnostics:
            if self.output_dir is None:
                raise ValueError("output_dir is required when resolver diagnostics logging is enabled")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            assert self.events_path is not None and self.rows_path is not None
            self.events_path.write_text("", encoding="utf-8")
            with self.rows_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=RESOLVER_ROW_FIELDS)
                writer.writeheader()

    @property
    def behavior_changed(self) -> bool:
        return bool(self._behavior_changed)

    def resolve_pre_step(
        self,
        *,
        problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
        method_metadata: Mapping[str, Any] | None = None,
    ) -> AssignmentLifecyclePreStepResult:
        self._update_episode_ids(episode_ids)
        if not self.enabled:
            return self.resolver.resolve_pre_step(
                problem=problem,
                assignment_proposal=assignment_proposal,
                method_metadata=self._merged_metadata(method_metadata),
            )
        if self._pending_assignment_proposal is not None:
            raise RuntimeError("resolve_pre_step called before observe_post_step for the previous resolver row")
        proposal = assignment_proposal.detach().to(device=self.device, dtype=torch.long).clone()
        snapshot_before = self.resolver.snapshot()
        active_before = snapshot_before["active_target_id"].clone()
        owner_before = snapshot_before["task_owner_robot_id"].clone()
        if self.enabled:
            self._update_active_infeasibility_monitor(problem, active_before)
        pre_result = self.resolver.resolve_pre_step(
            problem=problem,
            assignment_proposal=proposal,
            method_metadata=self._merged_metadata(method_metadata),
        )
        self._pending_pre_problem = _clone_problem_tensors(problem)
        self._pending_assignment_proposal = proposal.clone()
        self._pending_effective_assignment = pre_result.effective_assignment.detach().clone()
        self._pending_pre_result = pre_result
        self._pending_active_target_before = active_before.clone()
        self._pending_task_owner_before = owner_before.clone()
        self._drain_resolver_events()
        if self.enabled:
            self._update_stranded_failed_pair_detector(problem)
        return pre_result

    def observe_post_step(
        self,
        *,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        effective_assignment: torch.Tensor,
        post_step_problem: Mapping[str, Any],
        external_diagnostics: Mapping[str, Any] | None = None,
        done_env_ids: torch.Tensor | Sequence[int] | None = None,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
        method_metadata: Mapping[str, Any] | None = None,
    ) -> AssignmentLifecyclePostStepResult:
        self._update_episode_ids(episode_ids)
        if not self.enabled:
            return self.resolver.observe_post_step(
                pre_step_problem=pre_step_problem,
                assignment_proposal=assignment_proposal,
                effective_assignment=effective_assignment,
                post_step_problem=post_step_problem,
                external_diagnostics=external_diagnostics,
                done_env_ids=done_env_ids,
                method_metadata=self._merged_metadata(method_metadata),
            )
        self._assert_pending_row(pre_step_problem, assignment_proposal, effective_assignment)
        external = dict(external_diagnostics or {})
        post_result = self.resolver.observe_post_step(
            pre_step_problem=self._pending_pre_problem or pre_step_problem,
            assignment_proposal=assignment_proposal,
            effective_assignment=effective_assignment,
            post_step_problem=post_step_problem,
            external_diagnostics=external,
            done_env_ids=done_env_ids,
            method_metadata=self._merged_metadata(method_metadata),
        )
        self._drain_resolver_events()
        self._write_pending_rows(post_result=post_result)
        self._total_steps_observed += self.num_envs
        self._clear_pending_row()
        return post_result

    def reset_envs(
        self,
        env_ids: torch.Tensor | Sequence[int] | None = None,
        *,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
        method_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._update_episode_ids(episode_ids)
        snapshot = self.resolver.reset(
            env_ids=env_ids,
            emit_events=bool(self.enabled),
            method_metadata=self._merged_metadata(method_metadata),
        )
        self._drain_resolver_events()
        ids = _as_env_ids(env_ids, device=self.device)
        if ids is None:
            ids = torch.arange(self.num_envs, dtype=torch.long, device=self.device)
        if ids.numel() > 0:
            self._active_infeasible_streak[ids] = 0
            self._stranded_active[ids] = False
            self._stranded_streak[ids] = 0
        return snapshot

    def snapshot(self) -> dict[str, Any]:
        payload = self.resolver.snapshot()
        payload.update(
            {
                "schema_version": ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION,
                "adapter_enabled": bool(self.enabled),
                "log_diagnostics": bool(self.log_diagnostics),
                "method_name": self.method_name,
                "total_steps_observed": int(self._total_steps_observed),
                "total_events": int(self._total_events),
                "proposal_effective_changed_count": int(self._proposal_effective_changed_count),
                "active_target_infeasible_step_count": int(self._active_infeasible_step_count),
                "active_target_infeasible_max_streak": int(self._active_infeasible_max_streak),
                "active_target_infeasible_robot_target_pairs": [
                    {"env_id": env_id, "robot_id": robot_id, "target_id": target_id}
                    for env_id, robot_id, target_id in sorted(self._active_infeasible_pairs)
                ],
                "stranded_failed_pair_started_count": int(self._stranded_started_count),
                "stranded_failed_pair_recovered_count": int(self._stranded_recovered_count),
                "stranded_failed_pair_max_streak": int(self._stranded_max_streak),
                "behavior_changed": bool(self._behavior_changed),
                "events_path": str(self.events_path) if self.log_diagnostics and self.events_path else None,
                "summary_path": str(self.summary_path) if self.log_diagnostics and self.summary_path else None,
                "rows_path": str(self.rows_path) if self.log_diagnostics and self.rows_path else None,
            }
        )
        return payload

    def pop_events(self) -> list[dict[str, Any]]:
        events = list(self._event_buffer)
        self._event_buffer.clear()
        return events

    def peek_events(self) -> list[dict[str, Any]]:
        return list(self._event_buffer)

    def finalize(self) -> dict[str, Any]:
        self._drain_resolver_events()
        payload = self._summary_payload()
        if self.log_diagnostics and not self._finalized:
            assert self.summary_path is not None
            self.summary_path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")
        self._finalized = True
        return payload

    def passive_lifecycle_input(self, assignment_proposal: torch.Tensor, effective_assignment: torch.Tensor) -> tuple[torch.Tensor, str]:
        return select_assignment_lifecycle_passive_input(
            resolver_enabled=self.enabled,
            assignment_proposal=assignment_proposal,
            effective_assignment=effective_assignment,
        )

    def budget_failure_diagnostics(
        self,
        *,
        effective_assignment: torch.Tensor,
        info: Mapping[str, Any] | None = None,
        budget_trigger_mask: torch.Tensor | None = None,
    ) -> dict[str, Any]:
        return build_resolver_budget_failure_diagnostics(
            effective_assignment=effective_assignment,
            info=info,
            budget_trigger_mask=budget_trigger_mask,
        )

    def _merged_metadata(self, method_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
        metadata = dict(method_metadata or {})
        metadata.setdefault("method_name", self.method_name)
        return metadata

    def _update_episode_ids(self, episode_ids: torch.Tensor | Sequence[int] | int | None) -> None:
        ids = _as_episode_ids(episode_ids, num_envs=self.num_envs, device=self.device)
        if ids is not None:
            self._episode_ids = ids

    def _assert_pending_row(
        self,
        pre_step_problem: Mapping[str, Any],
        assignment_proposal: torch.Tensor,
        effective_assignment: torch.Tensor,
    ) -> None:
        if self._pending_assignment_proposal is None or self._pending_effective_assignment is None:
            raise RuntimeError("observe_post_step called before resolve_pre_step for this resolver row")
        proposal = assignment_proposal.to(device=self.device, dtype=torch.long)
        effective = effective_assignment.to(device=self.device, dtype=torch.long)
        if not torch.equal(self._pending_assignment_proposal, proposal):
            raise RuntimeError("observe_post_step assignment_proposal does not match pending resolver proposal")
        if not torch.equal(self._pending_effective_assignment, effective):
            raise RuntimeError("observe_post_step effective_assignment does not match pending resolver output")
        if self._pending_pre_problem:
            for key, expected in self._pending_pre_problem.items():
                value = pre_step_problem.get(key)
                if not isinstance(value, torch.Tensor):
                    raise RuntimeError(f"observe_post_step pre_step_problem missing tensor {key!r}")
                if tuple(value.shape) != tuple(expected.shape):
                    raise RuntimeError(
                        f"observe_post_step pre_step_problem tensor {key!r} shape changed since resolve_pre_step"
                    )

    def _clear_pending_row(self) -> None:
        self._pending_pre_problem = None
        self._pending_assignment_proposal = None
        self._pending_effective_assignment = None
        self._pending_pre_result = None
        self._pending_active_target_before = None
        self._pending_task_owner_before = None
        self._pending_events_by_env = [[] for _ in range(self.num_envs)]

    def _drain_resolver_events(self) -> None:
        events = self.resolver.pop_events()
        for event in events:
            row = self._normalize_event(event)
            self._record_event(row)

    def _emit_adapter_event(self, event: Mapping[str, Any]) -> None:
        row = self._normalize_event(event)
        self._record_event(row)

    def _normalize_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        env_id = int(event.get("env_id", 0))
        robot_id = event.get("robot_id")
        proposal_value = None
        effective_value = None
        if (
            robot_id is not None
            and self._pending_assignment_proposal is not None
            and self._pending_effective_assignment is not None
            and 0 <= env_id < self.num_envs
            and 0 <= int(robot_id) < self.num_robots
        ):
            proposal_value = int(self._pending_assignment_proposal[env_id, int(robot_id)].item())
            effective_value = int(self._pending_effective_assignment[env_id, int(robot_id)].item())
        row = dict(event)
        row.update(
            {
                "schema_version": ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION,
                "method_name": str(event.get("method_name") or self.method_name),
                "episode_id": int(self._episode_ids[env_id].item()) if 0 <= env_id < self.num_envs else None,
                "env_id": env_id,
                "step": int(event.get("step", 0)),
                "event_type": str(event.get("event_type", "")),
                "assignment_proposal_for_robot": proposal_value,
                "effective_assignment_for_robot": effective_value,
                "behavior_changed": bool(event.get("behavior_changed", event.get("details", {}).get("behavior_changed", False))),
            }
        )
        return _json_safe(row)

    def _record_event(self, row: Mapping[str, Any]) -> None:
        safe_row = dict(_json_safe(row))
        event_type = str(safe_row.get("event_type", ""))
        self._event_counts.setdefault(event_type, 0)
        self._event_counts[event_type] += 1
        self._total_events += 1
        self._behavior_changed = self._behavior_changed or bool(safe_row.get("behavior_changed", False))
        env_id = int(safe_row.get("env_id", 0))
        if 0 <= env_id < self.num_envs:
            self._pending_events_by_env[env_id].append(safe_row)
        self._event_buffer.append(safe_row)
        if self.log_diagnostics:
            assert self.events_path is not None
            with self.events_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(safe_row, sort_keys=True) + "\n")

    def _write_pending_rows(self, *, post_result: AssignmentLifecyclePostStepResult) -> None:
        if self._pending_assignment_proposal is None or self._pending_effective_assignment is None:
            return
        if self._pending_pre_result is None:
            return
        active_after = self.resolver.snapshot()["active_target_id"]
        owner_after = self.resolver.snapshot()["task_owner_robot_id"]
        changed = self._pending_assignment_proposal != self._pending_effective_assignment
        changed_count = int(changed.to(dtype=torch.long).sum().item())
        self._proposal_effective_changed_count += changed_count
        self._behavior_changed = self._behavior_changed or bool(self._pending_pre_result.behavior_changed)
        rows = []
        for env_id in range(self.num_envs):
            row = {
                "schema_version": ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION,
                "method_name": self.method_name,
                "episode_id": int(self._episode_ids[env_id].item()),
                "env_id": env_id,
                "step": int(self.resolver.step[env_id].item()),
                "assignment_proposal": self._pending_assignment_proposal[env_id].detach().cpu().tolist(),
                "effective_assignment": self._pending_effective_assignment[env_id].detach().cpu().tolist(),
                "proposal_effective_changed": changed[env_id].detach().cpu().tolist(),
                "proposal_accepted": self._pending_pre_result.proposal_accepted[env_id].detach().cpu().tolist(),
                "proposal_rejected_reason": self._pending_pre_result.proposal_rejected_reason[env_id].detach().cpu().tolist(),
                "continued_from_active_target": self._pending_pre_result.continued_from_active_target[env_id].detach().cpu().tolist(),
                "new_claim_started": self._pending_pre_result.new_claim_started[env_id].detach().cpu().tolist(),
                "switch_requested": self._pending_pre_result.switch_requested[env_id].detach().cpu().tolist(),
                "switch_rejected": self._pending_pre_result.switch_rejected[env_id].detach().cpu().tolist(),
                "claim_conflict": self._pending_pre_result.claim_conflict[env_id].detach().cpu().tolist(),
                "claim_winner": self._pending_pre_result.claim_winner[env_id].detach().cpu().tolist(),
                "claim_loser": self._pending_pre_result.claim_loser[env_id].detach().cpu().tolist(),
                "active_target_before": (
                    self._pending_active_target_before[env_id].detach().cpu().tolist()
                    if self._pending_active_target_before is not None
                    else []
                ),
                "active_target_after": active_after[env_id].detach().cpu().tolist(),
                "task_owner_before": (
                    self._pending_task_owner_before[env_id].detach().cpu().tolist()
                    if self._pending_task_owner_before is not None
                    else []
                ),
                "task_owner_after": owner_after[env_id].detach().cpu().tolist(),
                "resolver_events": [event.get("event_type") for event in self._pending_events_by_env[env_id]],
                "behavior_changed": bool(changed[env_id].any().item() or post_result.behavior_changed),
            }
            rows.append(row)
        if self.log_diagnostics:
            assert self.rows_path is not None
            with self.rows_path.open("a", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=RESOLVER_ROW_FIELDS)
                for row in rows:
                    writer.writerow({field: _json_cell(row.get(field)) for field in RESOLVER_ROW_FIELDS})

    def _update_active_infeasibility_monitor(self, problem: Mapping[str, Any], active_target: torch.Tensor) -> None:
        available = problem.get("available_mask")
        covered = problem.get("viewpoints_covered")
        if not isinstance(available, torch.Tensor) or not isinstance(covered, torch.Tensor):
            return
        feasible = problem.get("feasible_mask")
        available_bool = available.to(device=self.device, dtype=torch.bool)
        feasible_bool = feasible.to(device=self.device, dtype=torch.bool) if isinstance(feasible, torch.Tensor) else available_bool
        covered_bool = covered.to(device=self.device, dtype=torch.bool)
        condition = torch.zeros((self.num_envs, self.num_robots), dtype=torch.bool, device=self.device)
        for env_id in range(self.num_envs):
            for robot_id in range(self.num_robots):
                target_id = int(active_target[env_id, robot_id].item())
                if target_id < 0 or target_id >= self.num_tasks:
                    continue
                if bool(covered_bool[env_id, target_id].item()):
                    continue
                if not bool((available_bool[env_id, robot_id, target_id] & feasible_bool[env_id, robot_id, target_id]).item()):
                    condition[env_id, robot_id] = True
                    self._active_infeasible_pairs.add((env_id, robot_id, target_id))
        self._active_infeasible_step_count += int(condition.to(dtype=torch.long).sum().item())
        self._active_infeasible_streak = torch.where(
            condition,
            self._active_infeasible_streak + 1,
            torch.zeros_like(self._active_infeasible_streak),
        )
        if self._active_infeasible_streak.numel() > 0:
            self._active_infeasible_max_streak = max(
                self._active_infeasible_max_streak,
                int(self._active_infeasible_streak.max().item()),
            )

    def _update_stranded_failed_pair_detector(self, problem: Mapping[str, Any]) -> None:
        snapshot = self.resolver.snapshot()
        owner = snapshot["task_owner_robot_id"].to(device=self.device)
        pair_state = snapshot["pair_state"].to(device=self.device)
        covered = problem.get("viewpoints_covered")
        available = problem.get("available_mask")
        if not isinstance(covered, torch.Tensor) or not isinstance(available, torch.Tensor):
            return
        feasible = problem.get("feasible_mask")
        covered_bool = covered.to(device=self.device, dtype=torch.bool)
        available_bool = available.to(device=self.device, dtype=torch.bool)
        feasible_bool = feasible.to(device=self.device, dtype=torch.bool) if isinstance(feasible, torch.Tensor) else available_bool
        failed = (pair_state == PAIR_FAILED_BUDGET) | (pair_state == PAIR_RELEASED_BUDGET)
        condition = torch.zeros((self.num_envs, self.num_tasks), dtype=torch.bool, device=self.device)
        for env_id in range(self.num_envs):
            for target_id in range(self.num_tasks):
                if bool(covered_bool[env_id, target_id].item()):
                    continue
                if int(owner[env_id, target_id].item()) != NO_OWNER:
                    continue
                target_failed = failed[env_id, :, target_id]
                if not bool(target_failed.any().item()):
                    continue
                target_available = available_bool[env_id, :, target_id] & feasible_bool[env_id, :, target_id]
                unblocked_available = target_available & (~target_failed)
                blocked_available = target_available & target_failed
                if bool(blocked_available.any().item()) and not bool(unblocked_available.any().item()):
                    condition[env_id, target_id] = True
        started = condition & (~self._stranded_active)
        recovered = self._stranded_active & (~condition)
        for env_id, target_id in torch.nonzero(started, as_tuple=False).detach().cpu().tolist():
            failed_robot_ids = torch.nonzero(failed[int(env_id), :, int(target_id)], as_tuple=False).flatten()
            self._stranded_started_count += 1
            self._emit_adapter_event(
                {
                    "event_type": "stranded_failed_pair_started",
                    "env_id": int(env_id),
                    "step": int(self.resolver.step[int(env_id)].item()),
                    "target_id": int(target_id),
                    "failed_robot_ids": failed_robot_ids.detach().cpu().tolist(),
                    "behavior_changed": False,
                }
            )
        for env_id, target_id in torch.nonzero(recovered, as_tuple=False).detach().cpu().tolist():
            self._stranded_recovered_count += 1
            self._emit_adapter_event(
                {
                    "event_type": "stranded_failed_pair_recovered",
                    "env_id": int(env_id),
                    "step": int(self.resolver.step[int(env_id)].item()),
                    "target_id": int(target_id),
                    "behavior_changed": False,
                }
            )
        self._stranded_active = condition
        self._stranded_streak = torch.where(condition, self._stranded_streak + 1, torch.zeros_like(self._stranded_streak))
        if self._stranded_streak.numel() > 0:
            self._stranded_max_streak = max(self._stranded_max_streak, int(self._stranded_streak.max().item()))

    def _summary_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION,
            "enabled": bool(self.enabled),
            "method_name": self.method_name,
            "num_envs": self.num_envs,
            "num_robots": self.num_robots,
            "num_tasks": self.num_tasks,
            "total_steps_observed": int(self._total_steps_observed),
            "total_events": int(self._total_events),
            "proposal_effective_changed_count": int(self._proposal_effective_changed_count),
            "stranded_failed_pair_started_count": int(self._stranded_started_count),
            "stranded_failed_pair_recovered_count": int(self._stranded_recovered_count),
            "active_target_infeasible_step_count": int(self._active_infeasible_step_count),
            "active_target_infeasible_max_streak": int(self._active_infeasible_max_streak),
            "behavior_changed": bool(self._behavior_changed),
        }
        for event_type in RESOLVER_EVENT_TYPES:
            payload[f"{event_type}_count"] = int(self._event_counts.get(event_type, 0))
        return payload


__all__ = [
    "ASSIGNMENT_LIFECYCLE_RESOLVER_RUNTIME_SCHEMA_VERSION",
    "AssignmentLifecycleResolverRuntimeAdapter",
    "RESOLVER_EVENT_TYPES",
    "RESOLVER_ROW_FIELDS",
    "build_resolver_budget_failure_diagnostics",
    "select_assignment_lifecycle_passive_input",
]
