"""Pure playback-only proposal/effective assignment attribution diagnostics."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import copy
import csv
import json
import math
from pathlib import Path
from typing import Any

import torch

try:
    from .assignment_lifecycle_resolver import (
        NO_OWNER,
        NO_TARGET,
        PAIR_FAILED_BUDGET,
        PAIR_NONE,
        PAIR_RELEASED_BUDGET,
        PROPOSAL_REJECTED_REASON_NAMES,
        REASON_BUDGET_FAILURE,
        REJECT_CLAIM_LOST,
        REJECT_COVERED_TARGET,
        REJECT_FAILED_PAIR,
        REJECT_NONE,
        REJECT_OWNED_TARGET,
        REJECT_SWITCH_DISABLED,
        REJECT_UNAVAILABLE_TARGET,
    )
except ImportError:  # pragma: no cover - direct script import fallback
    from assignment_lifecycle_resolver import (
        NO_OWNER,
        NO_TARGET,
        PAIR_FAILED_BUDGET,
        PAIR_NONE,
        PAIR_RELEASED_BUDGET,
        PROPOSAL_REJECTED_REASON_NAMES,
        REASON_BUDGET_FAILURE,
        REJECT_CLAIM_LOST,
        REJECT_COVERED_TARGET,
        REJECT_FAILED_PAIR,
        REJECT_NONE,
        REJECT_OWNED_TARGET,
        REJECT_SWITCH_DISABLED,
        REJECT_UNAVAILABLE_TARGET,
    )


SCHEMA_VERSION = "phase9g8h1_assignment_proposal_effective_attribution_v1"
ROWS_FILENAME = "assignment_proposal_effective_rows.csv"
SUMMARY_FILENAME = "assignment_proposal_effective_summary.json"
SEGMENTS_FILENAME = "assignment_target_segments.csv"
OUTPUT_FILENAMES = (ROWS_FILENAME, SUMMARY_FILENAME, SEGMENTS_FILENAME)

PRIMARY_ATTRIBUTION_PRIORITY = (
    "reset",
    "target_completed",
    "release_budget_failure",
    "budget_failure",
    "active_target_infeasible_deferred",
    "switch_rejected_executing",
    "claim_lost",
    "owned_target_rejected",
    "failed_pair_reclaim_rejected",
    "covered_target_rejected",
    "unavailable_target_rejected",
    "attempt_started",
    "attempt_continued_same_target",
    "attempt_continued_noop_contract_c",
    "noop_idle",
)

ROW_FIELDS = (
    "schema_version",
    "method_name",
    "episode_id",
    "env_id",
    "decision_step",
    "robot_id",
    "robot_name",
    "raw_action_id",
    "decoded_proposal",
    "proposal_is_noop",
    "selected_action_probability",
    "active_target_before",
    "robot_execution_state_before",
    "proposal_target_owner_before",
    "proposal_available_before",
    "proposal_feasible_before",
    "proposal_covered_before",
    "self_pair_failed_or_released_before",
    "effective_assignment",
    "effective_is_noop",
    "proposal_effective_changed",
    "controller_assignment",
    "primary_attribution",
    "resolver_event_types",
    "resolver_events",
    "proposal_rejected",
    "proposal_rejected_reason",
    "arbitration_winner_robot_id",
    "owner_robot_id",
    "active_target_after",
    "target_completed_this_step",
    "budget_failure_this_step",
    "release_budget_failure_this_step",
    "active_target_infeasible_deferred",
    "done",
    "reset",
    "controller_action_l2_norm",
    "base_motion_distance",
    "distance_to_effective_target_before",
    "distance_to_effective_target_after",
    "distance_to_effective_target",
    "distance_progress",
    "post_state_pre_reset_available",
    "coverage_ratio",
    "coverage_delta_ids",
    "coverage_delta_count",
    "assigned_target_completed",
    "assigned_target_completion_count",
    "incidental_coverage_ids",
    "incidental_coverage_count",
    "unattributed_coverage_ids",
    "unattributed_coverage_count",
    "continued_from_active_target",
    "new_claim_started",
    "switch_requested",
    "switch_rejected",
    "claim_conflict",
    "claim_winner",
    "claim_loser",
    "reset_before_decision",
    "unprojected_env_event_types",
)

SEGMENT_FIELDS = (
    "schema_version",
    "method_name",
    "episode_id",
    "env_id",
    "robot_id",
    "robot_name",
    "segment_id",
    "target_id",
    "start_step",
    "end_step",
    "duration_steps",
    "release_type",
    "minimum_distance",
    "zero_distance_dwell_steps",
    "coverage_gain_during_segment",
    "start_distance",
    "final_distance",
    "cumulative_positive_distance_progress",
    "zero_progress_steps",
    "zero_base_motion_steps",
    "active_infeasible_steps",
    "noop_continue_steps",
    "same_target_continue_steps",
    "switch_rejected_steps",
    "start_raw_action_id",
    "start_decoded_proposal",
    "assigned_target_completion_count",
    "incidental_coverage_count",
    "unattributed_coverage_count",
    "terminal_event_types",
)


class AttributionInvariantError(RuntimeError):
    """Raised when joined playback inputs violate lifecycle continuity."""


@dataclass(frozen=True)
class AssignmentPlaybackPhysicalSnapshot:
    """Copy-owned physical and task tensors for one playback boundary."""

    base_pos: torch.Tensor
    scanner_pos: torch.Tensor
    viewpoint_pos: torch.Tensor
    viewpoints_covered: torch.Tensor
    available_mask: torch.Tensor
    feasible_mask: torch.Tensor


def _clone_tensor(value: torch.Tensor, *, dtype: torch.dtype | None = None) -> torch.Tensor:
    result = value.detach().clone()
    return result.to(dtype=dtype) if dtype is not None else result


def _clone_value(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, Mapping):
        return {str(key): _clone_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_value(item) for item in value)
    return copy.deepcopy(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return _json_safe(value.item())
        return _json_safe(value.detach().cpu().tolist())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (bool, int, str)) or value is None:
        return value
    return str(value)


def capture_assignment_playback_physical_snapshot(
    problem: Mapping[str, Any],
) -> AssignmentPlaybackPhysicalSnapshot:
    """Capture the assignment tensors needed by the pure collector without aliases."""

    required = ("base_pos", "scanner_pos", "viewpoint_pos", "viewpoints_covered", "available_mask")
    missing = [key for key in required if not isinstance(problem.get(key), torch.Tensor)]
    if missing:
        raise ValueError(f"assignment playback snapshot is missing tensor fields: {missing}")
    feasible = problem.get("feasible_mask", problem["available_mask"])
    if not isinstance(feasible, torch.Tensor):
        raise TypeError("problem['feasible_mask'] must be a tensor when supplied")

    snapshot = AssignmentPlaybackPhysicalSnapshot(
        base_pos=_clone_tensor(problem["base_pos"], dtype=torch.float32),
        scanner_pos=_clone_tensor(problem["scanner_pos"], dtype=torch.float32),
        viewpoint_pos=_clone_tensor(problem["viewpoint_pos"], dtype=torch.float32),
        viewpoints_covered=_clone_tensor(problem["viewpoints_covered"], dtype=torch.bool),
        available_mask=_clone_tensor(problem["available_mask"], dtype=torch.bool),
        feasible_mask=_clone_tensor(feasible, dtype=torch.bool),
    )
    _validate_physical_snapshot(snapshot)
    return snapshot


def _copy_physical_snapshot(snapshot: AssignmentPlaybackPhysicalSnapshot) -> AssignmentPlaybackPhysicalSnapshot:
    return AssignmentPlaybackPhysicalSnapshot(
        base_pos=_clone_tensor(snapshot.base_pos, dtype=torch.float32),
        scanner_pos=_clone_tensor(snapshot.scanner_pos, dtype=torch.float32),
        viewpoint_pos=_clone_tensor(snapshot.viewpoint_pos, dtype=torch.float32),
        viewpoints_covered=_clone_tensor(snapshot.viewpoints_covered, dtype=torch.bool),
        available_mask=_clone_tensor(snapshot.available_mask, dtype=torch.bool),
        feasible_mask=_clone_tensor(snapshot.feasible_mask, dtype=torch.bool),
    )


def _validate_physical_snapshot(snapshot: AssignmentPlaybackPhysicalSnapshot) -> tuple[int, int, int]:
    if snapshot.base_pos.ndim != 3 or snapshot.base_pos.shape[-1] < 2:
        raise ValueError(f"base_pos must have shape [E,M,D>=2], got {tuple(snapshot.base_pos.shape)}")
    if snapshot.scanner_pos.ndim != 3 or snapshot.scanner_pos.shape[-1] != 3:
        raise ValueError(f"scanner_pos must have shape [E,M,3], got {tuple(snapshot.scanner_pos.shape)}")
    if snapshot.viewpoint_pos.ndim != 3 or snapshot.viewpoint_pos.shape[-1] != 3:
        raise ValueError(f"viewpoint_pos must have shape [E,N,3], got {tuple(snapshot.viewpoint_pos.shape)}")
    e, m = snapshot.base_pos.shape[:2]
    n = snapshot.viewpoint_pos.shape[1]
    expected = {
        "scanner_pos": (e, m, 3),
        "viewpoints_covered": (e, n),
        "available_mask": (e, m, n),
        "feasible_mask": (e, m, n),
    }
    for name, shape in expected.items():
        actual = tuple(getattr(snapshot, name).shape)
        if actual != shape:
            raise ValueError(f"{name} must have shape {shape}, got {actual}")
    return int(e), int(m), int(n)


def stack_assignment_controller_actions(
    controller_actions: Mapping[str, torch.Tensor],
    robot_names: Sequence[str],
) -> torch.Tensor:
    """Stack the exact wrapper-produced controller commands in stable robot order."""

    commands: list[torch.Tensor] = []
    for robot_name in robot_names:
        value = controller_actions.get(str(robot_name))
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"controller action for {robot_name!r} is missing or not a tensor")
        if value.ndim != 2:
            raise ValueError(f"controller action for {robot_name!r} must have shape [E,A], got {tuple(value.shape)}")
        commands.append(value.detach().clone().to(dtype=torch.float32))
    if not commands:
        raise ValueError("at least one controller action is required")
    return torch.stack(commands, dim=1)


def validate_assignment_playback_attribution_cli(
    *,
    log_enabled: bool,
    print_enabled: bool,
    output_dir: str | Path | None,
) -> Path | None:
    """Validate the default-off CLI contract without creating files or directories."""

    del print_enabled
    if log_enabled and output_dir is None:
        raise ValueError(
            "--log_assignment_proposal_effective requires "
            "--assignment_proposal_effective_output_dir PATH"
        )
    if output_dir is not None and not log_enabled:
        raise ValueError(
            "--assignment_proposal_effective_output_dir requires "
            "--log_assignment_proposal_effective"
        )
    if output_dir is None:
        return None
    resolved = Path(output_dir).expanduser().resolve()
    if resolved.exists() and not resolved.is_dir():
        raise NotADirectoryError(f"assignment attribution output path is not a directory: {resolved}")
    collisions = [resolved / filename for filename in OUTPUT_FILENAMES if (resolved / filename).exists()]
    if collisions:
        raise FileExistsError(f"assignment attribution output already exists: {collisions[0]}")
    return resolved


def make_assignment_playback_attribution_collector_if_enabled(
    *,
    log_enabled: bool,
    print_enabled: bool,
    output_dir: str | Path | None,
    collector_factory: Callable[..., "AssignmentPlaybackAttributionCollector"] | None = None,
    **collector_kwargs: Any,
) -> "AssignmentPlaybackAttributionCollector | None":
    """Construct the collector only when logging or compact printing is requested."""

    resolved = validate_assignment_playback_attribution_cli(
        log_enabled=log_enabled,
        print_enabled=print_enabled,
        output_dir=output_dir,
    )
    if not log_enabled and not print_enabled:
        return None
    factory = collector_factory or AssignmentPlaybackAttributionCollector
    return factory(output_dir=resolved if log_enabled else None, **collector_kwargs)


def format_assignment_playback_attribution_row(row: Mapping[str, Any]) -> str:
    """Format one compact row without exposing the full resolver event payload."""

    move = row.get("base_motion_distance")
    move_text = "null" if move is None else f"{float(move):.4f}"
    owner = row.get("owner_robot_id")
    owner_text = "" if owner is None else f" owner={int(owner)}"
    return (
        f"[STEP {int(row['decision_step']):03d}]"
        f"[env_{int(row['env_id'])}]"
        f"[{row['robot_name']}] "
        f"proposal={int(row['decoded_proposal'])} effective={int(row['effective_assignment'])} "
        f"active={int(row['active_target_before'])}->{int(row['active_target_after'])} "
        f"attr={row['primary_attribution']}{owner_text} "
        f"p={float(row['selected_action_probability']):.4f} "
        f"cmd={float(row['controller_action_l2_norm']):.4f} move={move_text}"
    )


class AssignmentPlaybackAttributionCollector:
    """Join immutable playback inputs into rows, segments, and load diagnostics."""

    def __init__(
        self,
        *,
        method_name: str,
        num_envs: int,
        num_robots: int,
        num_tasks: int,
        robot_names: Sequence[str],
        noop_raw_id: int,
        output_dir: str | Path | None = None,
        distance_dwell_thresholds: torch.Tensor | Sequence[float] | None = None,
        zero_command_epsilon: float = 1.0e-8,
        zero_motion_epsilon: float = 1.0e-8,
        zero_progress_epsilon: float = 1.0e-8,
    ) -> None:
        if num_envs <= 0 or num_robots <= 0 or num_tasks <= 0:
            raise ValueError("num_envs, num_robots, and num_tasks must be positive")
        if len(robot_names) != num_robots:
            raise ValueError(f"robot_names must contain {num_robots} entries, got {len(robot_names)}")
        if int(noop_raw_id) != int(num_tasks):
            raise ValueError(f"noop_raw_id must equal num_tasks ({num_tasks}), got {noop_raw_id}")

        self.method_name = str(method_name)
        self.num_envs = int(num_envs)
        self.num_robots = int(num_robots)
        self.num_tasks = int(num_tasks)
        self.robot_names = tuple(str(name) for name in robot_names)
        self.noop_raw_id = int(noop_raw_id)
        self.zero_command_epsilon = float(zero_command_epsilon)
        self.zero_motion_epsilon = float(zero_motion_epsilon)
        self.zero_progress_epsilon = float(zero_progress_epsilon)

        if distance_dwell_thresholds is None:
            thresholds = torch.zeros(self.num_robots, dtype=torch.float32)
        else:
            thresholds = torch.as_tensor(distance_dwell_thresholds, dtype=torch.float32).detach().clone().flatten()
        if tuple(thresholds.shape) != (self.num_robots,):
            raise ValueError(
                f"distance_dwell_thresholds must have shape [{self.num_robots}], got {tuple(thresholds.shape)}"
            )
        if bool((thresholds < 0).any()):
            raise ValueError("distance_dwell_thresholds must be nonnegative")
        self.distance_dwell_thresholds = thresholds.cpu()

        self._episode_ids = torch.zeros(self.num_envs, dtype=torch.long)
        self._decision_steps = torch.zeros(self.num_envs, dtype=torch.long)
        self._episode_initialized = torch.zeros(self.num_envs, dtype=torch.bool)
        self._boundary_pending = torch.ones(self.num_envs, dtype=torch.bool)
        self._active_target = torch.full((self.num_envs, self.num_robots), NO_TARGET, dtype=torch.long)
        self._task_owner = torch.full((self.num_envs, self.num_tasks), NO_OWNER, dtype=torch.long)
        self._pair_state = torch.full(
            (self.num_envs, self.num_robots, self.num_tasks), PAIR_NONE, dtype=torch.long
        )
        self._segment_ids = torch.zeros((self.num_envs, self.num_robots), dtype=torch.long)
        self._open_segments: dict[tuple[int, int], dict[str, Any]] = {}
        self._rows: list[dict[str, Any]] = []
        self._segments: list[dict[str, Any]] = []
        self._episode_boundary_events: list[dict[str, Any]] = []
        self._unprojected_environment_events: list[dict[str, Any]] = []
        self._invariant_failures: list[str] = []
        self._resolver_enabled_seen: set[bool] = set()
        self._finalized = False
        self._final_summary: dict[str, Any] | None = None

        self.output_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else None
        self.rows_path = self.output_dir / ROWS_FILENAME if self.output_dir is not None else None
        self.summary_path = self.output_dir / SUMMARY_FILENAME if self.output_dir is not None else None
        self.segments_path = self.output_dir / SEGMENTS_FILENAME if self.output_dir is not None else None
        if self.output_dir is not None:
            validate_assignment_playback_attribution_cli(
                log_enabled=True,
                print_enabled=False,
                output_dir=self.output_dir,
            )
            self.output_dir.mkdir(parents=True, exist_ok=True)
            assert self.rows_path is not None
            with self.rows_path.open("x", encoding="utf-8", newline="") as file:
                csv.DictWriter(file, fieldnames=ROW_FIELDS).writeheader()

    def reset_envs(
        self,
        env_ids: torch.Tensor | Sequence[int] | None = None,
        *,
        episode_ids: torch.Tensor | Sequence[int] | int | None = None,
    ) -> None:
        """Initialize or explicitly reset selected playback episode state."""

        self._ensure_recording()
        ids = self._normalize_env_ids(env_ids)
        supplied_episode_ids = self._normalize_episode_ids(episode_ids, ids)
        for offset, env_id in enumerate(ids):
            for robot_id in range(self.num_robots):
                key = (env_id, robot_id)
                if key in self._open_segments:
                    self._close_segment(
                        key,
                        end_step=max(1, int(self._decision_steps[env_id].item())),
                        release_type="reset",
                        terminal_event_types=["reset"],
                    )
            if supplied_episode_ids is not None:
                self._episode_ids[env_id] = supplied_episode_ids[offset]
            elif bool(self._episode_initialized[env_id]):
                self._episode_ids[env_id] += 1
            else:
                self._episode_ids[env_id] = 0
            self._episode_initialized[env_id] = True
            self._decision_steps[env_id] = 0
            self._active_target[env_id] = NO_TARGET
            self._task_owner[env_id] = NO_OWNER
            self._pair_state[env_id] = PAIR_NONE
            self._boundary_pending[env_id] = True

    def record_decision(
        self,
        *,
        raw_actions: torch.Tensor,
        selected_action_probabilities: torch.Tensor,
        pre_state: AssignmentPlaybackPhysicalSnapshot,
        lifecycle_resolution: Mapping[str, Any],
        controller_assignment: torch.Tensor,
        controller_actions: torch.Tensor,
        post_state: AssignmentPlaybackPhysicalSnapshot | None,
        post_state_pre_reset_available: torch.Tensor | Sequence[bool] | bool,
        dones: torch.Tensor | Sequence[bool] | bool,
    ) -> list[dict[str, Any]]:
        """Record one complete vector-environment decision atomically."""

        self._ensure_recording()
        pre = _copy_physical_snapshot(pre_state)
        post = _copy_physical_snapshot(post_state) if post_state is not None else None
        payload = _clone_value(lifecycle_resolution)
        raw = self._normalize_robot_tensor(raw_actions, name="raw_actions", dtype=torch.long)
        probabilities = self._normalize_robot_tensor(
            selected_action_probabilities, name="selected_action_probabilities", dtype=torch.float32
        )
        controller_assignment_copy = self._normalize_robot_tensor(
            controller_assignment, name="controller_assignment", dtype=torch.long
        )
        controller_actions_copy = controller_actions.detach().clone().to(dtype=torch.float32)
        if controller_actions_copy.ndim != 3 or tuple(controller_actions_copy.shape[:2]) != (
            self.num_envs,
            self.num_robots,
        ):
            raise ValueError(
                "controller_actions must have shape "
                f"[E,M,A], got {tuple(controller_actions_copy.shape)}"
            )
        done = self._normalize_env_bool(dones, name="dones")
        post_valid = self._normalize_env_bool(
            post_state_pre_reset_available,
            name="post_state_pre_reset_available",
        )
        if bool(post_valid.any()) and post is None:
            raise ValueError("post_state is required for environments marked post-state valid")

        self._validate_dimensions(pre, name="pre_state")
        if post is not None:
            self._validate_dimensions(post, name="post_state")
        self._validate_payload(payload)
        self._validate_resolver_state(self._active_target, self._task_owner, name="collector pre-state")

        proposal = payload["assignment_proposal"].to(dtype=torch.long)
        effective = payload["effective_assignment"].to(dtype=torch.long)
        changed = payload["proposal_effective_changed"].to(dtype=torch.bool)
        expected_changed = proposal != effective
        if not torch.equal(changed.cpu(), expected_changed.cpu()):
            raise AttributionInvariantError("proposal_effective_changed does not match proposal/effective equality")
        decoded_from_raw = torch.where(raw == self.noop_raw_id, torch.full_like(raw, NO_TARGET), raw)
        if not torch.equal(decoded_from_raw.cpu(), proposal.cpu()):
            raise AttributionInvariantError("raw action ids do not decode to the lifecycle assignment proposal")
        if not torch.equal(controller_assignment_copy.cpu(), effective.cpu()):
            raise AttributionInvariantError("controller assignment differs from resolver effective assignment")

        resolver_snapshot = payload["resolver_snapshot"]
        post_active = resolver_snapshot["active_target_id"].detach().clone().to(dtype=torch.long).cpu()
        post_owner = resolver_snapshot["task_owner_robot_id"].detach().clone().to(dtype=torch.long).cpu()
        post_pair = resolver_snapshot["pair_state"].detach().clone().to(dtype=torch.long).cpu()
        self._validate_resolver_state(post_active, post_owner, name="resolver post-state")
        reset_env_ids = {int(value) for value in payload.get("post_reset_env_ids", [])}
        reset_flags = torch.tensor(
            [env_id in reset_env_ids or bool(done[env_id]) for env_id in range(self.num_envs)],
            dtype=torch.bool,
        )
        self._resolver_enabled_seen.add(bool(payload.get("enabled", True)))

        projected_by_env, unprojected_by_env = self._project_events(payload.get("resolver_events", []))
        rows_by_env: list[list[dict[str, Any]]] = []
        for env_id in range(self.num_envs):
            self._decision_steps[env_id] += 1
            decision_step = int(self._decision_steps[env_id].item())
            episode_id = int(self._episode_ids[env_id].item())
            reset_before_decision = bool(self._boundary_pending[env_id])
            projected, unprojected = self._separate_initial_boundary_events(
                env_id=env_id,
                episode_id=episode_id,
                decision_step=decision_step,
                projected=projected_by_env[env_id],
                unprojected=unprojected_by_env[env_id],
            )
            unprojected_event_types = [str(event.get("event_type", "")) for event in unprojected]
            for event in unprojected:
                self._unprojected_environment_events.append(
                    {
                        "method_name": self.method_name,
                        "episode_id": episode_id,
                        "env_id": env_id,
                        "decision_step": decision_step,
                        "event": _json_safe(event),
                    }
                )

            coverage = self._coverage_context(
                env_id=env_id,
                pre=pre,
                post=post,
                post_valid=bool(post_valid[env_id]),
                projected=projected,
                payload=payload,
                effective=effective,
            )
            env_rows: list[dict[str, Any]] = []
            for robot_id in range(self.num_robots):
                row_events = projected[robot_id]
                row = self._build_row(
                    env_id=env_id,
                    robot_id=robot_id,
                    episode_id=episode_id,
                    decision_step=decision_step,
                    raw=raw,
                    probabilities=probabilities,
                    pre=pre,
                    post=post,
                    post_valid=bool(post_valid[env_id]),
                    payload=payload,
                    effective=effective,
                    proposal=proposal,
                    changed=changed,
                    controller_assignment=controller_assignment_copy,
                    controller_actions=controller_actions_copy,
                    post_active=post_active,
                    row_events=row_events,
                    coverage=coverage,
                    done=bool(done[env_id]),
                    reset=bool(reset_flags[env_id]),
                    reset_before_decision=reset_before_decision,
                    unprojected_event_types=unprojected_event_types,
                )
                env_rows.append(row)
            rows_by_env.append(env_rows)

        lifecycle_enabled = bool(payload.get("enabled", True))
        for env_rows in rows_by_env:
            for row in env_rows:
                self._validate_segment_transition(row, lifecycle_enabled=lifecycle_enabled)
        for env_rows in rows_by_env:
            for row in env_rows:
                self._update_segment(row, lifecycle_enabled=lifecycle_enabled)

        new_rows = [row for env_rows in rows_by_env for row in env_rows]
        self._rows.extend(copy.deepcopy(new_rows))
        self._write_rows(new_rows)

        self._active_target = post_active.clone()
        self._task_owner = post_owner.clone()
        self._pair_state = post_pair.clone()
        for env_id in range(self.num_envs):
            if bool(reset_flags[env_id]):
                self._episode_ids[env_id] += 1
                self._decision_steps[env_id] = 0
                self._boundary_pending[env_id] = False
        return copy.deepcopy(new_rows)

    def finalize(self) -> dict[str, Any]:
        """Close open segments and write final artifacts exactly once."""

        if self._finalized:
            return copy.deepcopy(self._final_summary or {})
        for key in sorted(self._open_segments):
            segment = self._open_segments.get(key)
            if segment is None:
                continue
            self._close_segment(
                key,
                end_step=int(segment["last_step"]),
                release_type="playback_truncated",
                terminal_event_types=[],
            )
        summary = self._build_summary()
        if self.output_dir is not None:
            assert self.segments_path is not None and self.summary_path is not None
            with self.segments_path.open("x", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=SEGMENT_FIELDS)
                writer.writeheader()
                for segment in self._segments:
                    writer.writerow({field: self._csv_cell(segment.get(field)) for field in SEGMENT_FIELDS})
            self.summary_path.write_text(
                json.dumps(_json_safe(summary), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        self._finalized = True
        self._final_summary = copy.deepcopy(summary)
        return copy.deepcopy(summary)

    def get_rows(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._rows)

    def get_segments(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._segments)

    def get_summary(self) -> dict[str, Any]:
        if self._finalized:
            return copy.deepcopy(self._final_summary or {})
        return self._build_summary(include_open_segments=True)

    def _ensure_recording(self) -> None:
        if self._finalized:
            raise RuntimeError("assignment playback attribution collector is already finalized")

    def _normalize_env_ids(self, env_ids: torch.Tensor | Sequence[int] | None) -> list[int]:
        if env_ids is None:
            ids = list(range(self.num_envs))
        elif isinstance(env_ids, torch.Tensor):
            ids = [int(value) for value in env_ids.detach().cpu().flatten().tolist()]
        else:
            ids = [int(value) for value in env_ids]
        if len(ids) != len(set(ids)) or any(value < 0 or value >= self.num_envs for value in ids):
            raise ValueError(f"invalid environment ids: {ids}")
        return ids

    def _normalize_episode_ids(
        self,
        episode_ids: torch.Tensor | Sequence[int] | int | None,
        env_ids: Sequence[int],
    ) -> list[int] | None:
        if episode_ids is None:
            return None
        if isinstance(episode_ids, int):
            return [int(episode_ids) for _ in env_ids]
        if isinstance(episode_ids, torch.Tensor):
            values = [int(value) for value in episode_ids.detach().cpu().flatten().tolist()]
        else:
            values = [int(value) for value in episode_ids]
        if len(values) == self.num_envs:
            return [values[env_id] for env_id in env_ids]
        if len(values) != len(env_ids):
            raise ValueError("episode_ids must be scalar, length E, or match env_ids")
        return values

    def _normalize_robot_tensor(self, value: torch.Tensor, *, name: str, dtype: torch.dtype) -> torch.Tensor:
        result = value.detach().clone().to(dtype=dtype)
        if result.ndim == 3 and result.shape[-1] == 1:
            result = result[..., 0]
        expected = (self.num_envs, self.num_robots)
        if tuple(result.shape) != expected:
            raise ValueError(f"{name} must have shape {expected} or {expected + (1,)}, got {tuple(result.shape)}")
        return result

    def _normalize_env_bool(self, value: torch.Tensor | Sequence[bool] | bool, *, name: str) -> torch.Tensor:
        result = torch.as_tensor(value, dtype=torch.bool).detach().clone().flatten()
        if result.numel() == 1:
            result = result.repeat(self.num_envs)
        if tuple(result.shape) != (self.num_envs,):
            raise ValueError(f"{name} must have shape [{self.num_envs}], got {tuple(result.shape)}")
        return result.cpu()

    def _validate_dimensions(self, snapshot: AssignmentPlaybackPhysicalSnapshot, *, name: str) -> None:
        actual = _validate_physical_snapshot(snapshot)
        expected = (self.num_envs, self.num_robots, self.num_tasks)
        if actual != expected:
            raise ValueError(f"{name} dimensions must be {expected}, got {actual}")

    def _validate_payload(self, payload: Mapping[str, Any]) -> None:
        robot_fields = (
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
            "post_completed",
            "post_released",
            "post_release_reason",
            "post_failure_reason",
        )
        for field in robot_fields:
            value = payload.get(field)
            if not isinstance(value, torch.Tensor):
                raise ValueError(f"lifecycle payload field {field!r} must be a tensor")
            if tuple(value.shape) != (self.num_envs, self.num_robots):
                raise ValueError(
                    f"lifecycle payload field {field!r} must have shape "
                    f"[{self.num_envs},{self.num_robots}], got {tuple(value.shape)}"
                )
        snapshot = payload.get("resolver_snapshot")
        if not isinstance(snapshot, Mapping):
            raise ValueError("lifecycle payload resolver_snapshot is missing")
        expected = {
            "active_target_id": (self.num_envs, self.num_robots),
            "task_owner_robot_id": (self.num_envs, self.num_tasks),
            "pair_state": (self.num_envs, self.num_robots, self.num_tasks),
        }
        for field, shape in expected.items():
            value = snapshot.get(field)
            if not isinstance(value, torch.Tensor) or tuple(value.shape) != shape:
                actual = None if not isinstance(value, torch.Tensor) else tuple(value.shape)
                raise ValueError(f"resolver snapshot field {field!r} must have shape {shape}, got {actual}")
        events = payload.get("resolver_events", [])
        if not isinstance(events, list) or any(not isinstance(event, Mapping) for event in events):
            raise ValueError("lifecycle payload resolver_events must be a list of mappings")

    def _validate_resolver_state(self, active: torch.Tensor, owner: torch.Tensor, *, name: str) -> None:
        if bool(((active < NO_TARGET) | (active >= self.num_tasks)).any()):
            raise AttributionInvariantError(f"{name} contains an invalid active target id")
        if bool(((owner < NO_OWNER) | (owner >= self.num_robots)).any()):
            raise AttributionInvariantError(f"{name} contains an invalid owner id")
        for env_id in range(self.num_envs):
            for robot_id in range(self.num_robots):
                target_id = int(active[env_id, robot_id].item())
                if target_id >= 0 and int(owner[env_id, target_id].item()) != robot_id:
                    raise AttributionInvariantError(
                        f"{name} active target/owner mismatch at env={env_id}, robot={robot_id}, target={target_id}"
                    )
            for target_id in range(self.num_tasks):
                robot_id = int(owner[env_id, target_id].item())
                if robot_id >= 0 and int(active[env_id, robot_id].item()) != target_id:
                    raise AttributionInvariantError(
                        f"{name} owner/active target mismatch at env={env_id}, robot={robot_id}, target={target_id}"
                    )

    def _project_events(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> tuple[list[list[list[dict[str, Any]]]], list[list[dict[str, Any]]]]:
        projected = [[[] for _ in range(self.num_robots)] for _ in range(self.num_envs)]
        unprojected = [[] for _ in range(self.num_envs)]
        for source_event in events:
            event = dict(_json_safe(source_event))
            env_id = int(event.get("env_id", -1))
            if env_id < 0 or env_id >= self.num_envs:
                continue
            robot_id = event.get("robot_id")
            if robot_id is not None and 0 <= int(robot_id) < self.num_robots:
                projected[env_id][int(robot_id)].append(event)
                continue
            claimants = event.get("claiming_robot_ids")
            if isinstance(claimants, list):
                valid_claimants: list[int] = []
                for value in claimants:
                    claimant = int(value)
                    if 0 <= claimant < self.num_robots and claimant not in valid_claimants:
                        valid_claimants.append(claimant)
                if valid_claimants:
                    for claimant in valid_claimants:
                        projected[env_id][claimant].append(copy.deepcopy(event))
                    continue
            unprojected[env_id].append(event)
        return projected, unprojected

    def _separate_initial_boundary_events(
        self,
        *,
        env_id: int,
        episode_id: int,
        decision_step: int,
        projected: list[list[dict[str, Any]]],
        unprojected: list[dict[str, Any]],
    ) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]]:
        if not bool(self._boundary_pending[env_id]):
            return projected, unprojected
        filtered = [[] for _ in range(self.num_robots)]
        for robot_id, events in enumerate(projected):
            leading = True
            for event in events:
                if leading and str(event.get("event_type", "")) == "reset":
                    self._episode_boundary_events.append(
                        {
                            "method_name": self.method_name,
                            "episode_id": episode_id,
                            "env_id": env_id,
                            "decision_step": decision_step,
                            "robot_id": robot_id,
                            "event": copy.deepcopy(event),
                        }
                    )
                    continue
                leading = False
                filtered[robot_id].append(event)
        filtered_unprojected: list[dict[str, Any]] = []
        leading = True
        for event in unprojected:
            if leading and str(event.get("event_type", "")) == "reset":
                self._episode_boundary_events.append(
                    {
                        "method_name": self.method_name,
                        "episode_id": episode_id,
                        "env_id": env_id,
                        "decision_step": decision_step,
                        "robot_id": None,
                        "event": copy.deepcopy(event),
                    }
                )
                continue
            leading = False
            filtered_unprojected.append(event)
        self._boundary_pending[env_id] = False
        return filtered, filtered_unprojected

    def _coverage_context(
        self,
        *,
        env_id: int,
        pre: AssignmentPlaybackPhysicalSnapshot,
        post: AssignmentPlaybackPhysicalSnapshot | None,
        post_valid: bool,
        projected: list[list[dict[str, Any]]],
        payload: Mapping[str, Any],
        effective: torch.Tensor,
    ) -> dict[str, Any]:
        assigned_targets: dict[int, set[int]] = {robot_id: set() for robot_id in range(self.num_robots)}
        for robot_id, events in enumerate(projected):
            for event in events:
                if str(event.get("event_type", "")) != "target_completed":
                    continue
                target_id = event.get("target_id")
                if target_id is not None and 0 <= int(target_id) < self.num_tasks:
                    assigned_targets[robot_id].add(int(target_id))
        post_completed = payload["post_completed"].to(dtype=torch.bool)
        for robot_id in range(self.num_robots):
            if bool(post_completed[env_id, robot_id]) and not assigned_targets[robot_id]:
                target_id = int(effective[env_id, robot_id].item())
                if target_id >= 0:
                    assigned_targets[robot_id].add(target_id)

        if not post_valid or post is None:
            return {
                "coverage_ratio": None,
                "coverage_delta_ids": None,
                "coverage_delta_count": None,
                "assigned_targets": assigned_targets,
                "unattributed_coverage_ids": None,
            }
        newly_covered = (~pre.viewpoints_covered[env_id]) & post.viewpoints_covered[env_id]
        coverage_delta_ids = [int(value) for value in torch.nonzero(newly_covered, as_tuple=False).flatten().cpu().tolist()]
        credited = set().union(*assigned_targets.values()) if assigned_targets else set()
        unattributed = [target_id for target_id in coverage_delta_ids if target_id not in credited]
        return {
            "coverage_ratio": float(post.viewpoints_covered[env_id].to(dtype=torch.float32).mean().cpu().item()),
            "coverage_delta_ids": coverage_delta_ids,
            "coverage_delta_count": len(coverage_delta_ids),
            "assigned_targets": assigned_targets,
            "unattributed_coverage_ids": unattributed,
        }

    def _build_row(
        self,
        *,
        env_id: int,
        robot_id: int,
        episode_id: int,
        decision_step: int,
        raw: torch.Tensor,
        probabilities: torch.Tensor,
        pre: AssignmentPlaybackPhysicalSnapshot,
        post: AssignmentPlaybackPhysicalSnapshot | None,
        post_valid: bool,
        payload: Mapping[str, Any],
        effective: torch.Tensor,
        proposal: torch.Tensor,
        changed: torch.Tensor,
        controller_assignment: torch.Tensor,
        controller_actions: torch.Tensor,
        post_active: torch.Tensor,
        row_events: list[dict[str, Any]],
        coverage: Mapping[str, Any],
        done: bool,
        reset: bool,
        reset_before_decision: bool,
        unprojected_event_types: list[str],
    ) -> dict[str, Any]:
        proposed_target = int(proposal[env_id, robot_id].item())
        effective_target = int(effective[env_id, robot_id].item())
        active_before = int(self._active_target[env_id, robot_id].item())
        active_after = int(post_active[env_id, robot_id].item())
        event_types = [str(event.get("event_type", "")) for event in row_events]
        rejected_code = int(payload["proposal_rejected_reason"][env_id, robot_id].item())
        rejected_reason = str(PROPOSAL_REJECTED_REASON_NAMES.get(rejected_code, f"unknown_{rejected_code}"))
        proposal_owner = None
        proposal_available = None
        proposal_feasible = None
        proposal_covered = None
        failed_pair = None
        if proposed_target >= 0:
            proposal_owner = int(self._task_owner[env_id, proposed_target].item())
            proposal_available = bool(pre.available_mask[env_id, robot_id, proposed_target].item())
            proposal_feasible = bool(pre.feasible_mask[env_id, robot_id, proposed_target].item())
            proposal_covered = bool(pre.viewpoints_covered[env_id, proposed_target].item())
            pair_value = int(self._pair_state[env_id, robot_id, proposed_target].item())
            failed_pair = pair_value in (PAIR_FAILED_BUDGET, PAIR_RELEASED_BUDGET)

        completed = bool(payload["post_completed"][env_id, robot_id].item()) or "target_completed" in event_types
        failure_reason = int(payload["post_failure_reason"][env_id, robot_id].item())
        released = bool(payload["post_released"][env_id, robot_id].item())
        budget_failure = "budget_failure" in event_types or failure_reason == REASON_BUDGET_FAILURE
        release_budget = "release_budget_failure" in event_types or (
            released and int(payload["post_release_reason"][env_id, robot_id].item()) == REASON_BUDGET_FAILURE
        )
        active_infeasible = "active_target_infeasible_deferred" in event_types
        assigned_targets = coverage["assigned_targets"][robot_id]
        assigned_completed = bool(assigned_targets)

        arbitration_winner = None
        owner_robot_id = None
        for event in row_events:
            if event.get("winner_robot_id") is not None:
                arbitration_winner = int(event["winner_robot_id"])
            if event.get("owner_robot_id") is not None:
                owner_robot_id = int(event["owner_robot_id"])
        if owner_robot_id is None:
            if arbitration_winner is not None:
                owner_robot_id = arbitration_winner
            elif proposal_owner is not None and proposal_owner >= 0:
                owner_robot_id = proposal_owner
            elif bool(payload["new_claim_started"][env_id, robot_id].item()):
                owner_robot_id = robot_id

        command_norm = float(torch.linalg.vector_norm(controller_actions[env_id, robot_id]).cpu().item())
        before_distance = self._distance_to_target(pre, env_id, robot_id, effective_target)
        after_distance = self._distance_to_target(post, env_id, robot_id, effective_target) if post_valid else None
        base_motion = None
        if post_valid and post is not None:
            delta = post.base_pos[env_id, robot_id, :2] - pre.base_pos[env_id, robot_id, :2]
            base_motion = float(torch.linalg.vector_norm(delta).cpu().item())
        progress = None
        if before_distance is not None and after_distance is not None:
            progress = float(before_distance - after_distance)

        if coverage["coverage_delta_ids"] is None:
            incidental_ids = None
            incidental_count = None
            unattributed_ids = None
            unattributed_count = None
        else:
            # The current environment exposes no reliable robot source for incidental coverage.
            incidental_ids = []
            incidental_count = 0
            unattributed_ids = list(coverage["unattributed_coverage_ids"])
            unattributed_count = len(unattributed_ids)

        row: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "method_name": self.method_name,
            "episode_id": episode_id,
            "env_id": env_id,
            "decision_step": decision_step,
            "robot_id": robot_id,
            "robot_name": self.robot_names[robot_id],
            "raw_action_id": int(raw[env_id, robot_id].item()),
            "decoded_proposal": proposed_target,
            "proposal_is_noop": proposed_target == NO_TARGET,
            "selected_action_probability": float(probabilities[env_id, robot_id].cpu().item()),
            "active_target_before": active_before,
            "robot_execution_state_before": "idle" if active_before == NO_TARGET else "executing",
            "proposal_target_owner_before": proposal_owner,
            "proposal_available_before": proposal_available,
            "proposal_feasible_before": proposal_feasible,
            "proposal_covered_before": proposal_covered,
            "self_pair_failed_or_released_before": failed_pair,
            "effective_assignment": effective_target,
            "effective_is_noop": effective_target == NO_TARGET,
            "proposal_effective_changed": bool(changed[env_id, robot_id].item()),
            "controller_assignment": int(controller_assignment[env_id, robot_id].item()),
            "resolver_event_types": event_types,
            "resolver_events": copy.deepcopy(row_events),
            "proposal_rejected": rejected_code != REJECT_NONE,
            "proposal_rejected_reason": rejected_reason,
            "arbitration_winner_robot_id": arbitration_winner,
            "owner_robot_id": owner_robot_id,
            "active_target_after": active_after,
            "target_completed_this_step": completed,
            "budget_failure_this_step": budget_failure,
            "release_budget_failure_this_step": release_budget,
            "active_target_infeasible_deferred": active_infeasible,
            "done": bool(done),
            "reset": bool(reset),
            "controller_action_l2_norm": command_norm,
            "base_motion_distance": base_motion,
            "distance_to_effective_target_before": before_distance,
            "distance_to_effective_target_after": after_distance,
            "distance_to_effective_target": after_distance,
            "distance_progress": progress,
            "post_state_pre_reset_available": bool(post_valid),
            "coverage_ratio": coverage["coverage_ratio"],
            "coverage_delta_ids": copy.deepcopy(coverage["coverage_delta_ids"]),
            "coverage_delta_count": coverage["coverage_delta_count"],
            "assigned_target_completed": assigned_completed,
            "assigned_target_completion_count": len(assigned_targets),
            "incidental_coverage_ids": incidental_ids,
            "incidental_coverage_count": incidental_count,
            "unattributed_coverage_ids": unattributed_ids,
            "unattributed_coverage_count": unattributed_count,
            "continued_from_active_target": bool(payload["continued_from_active_target"][env_id, robot_id].item()),
            "new_claim_started": bool(payload["new_claim_started"][env_id, robot_id].item()),
            "switch_requested": bool(payload["switch_requested"][env_id, robot_id].item()),
            "switch_rejected": bool(payload["switch_rejected"][env_id, robot_id].item()),
            "claim_conflict": bool(payload["claim_conflict"][env_id, robot_id].item()),
            "claim_winner": bool(payload["claim_winner"][env_id, robot_id].item()),
            "claim_loser": bool(payload["claim_loser"][env_id, robot_id].item()),
            "reset_before_decision": bool(reset_before_decision),
            "unprojected_env_event_types": list(unprojected_event_types),
        }
        row["primary_attribution"] = self._primary_attribution(row, rejected_code=rejected_code)
        return row

    def _primary_attribution(self, row: Mapping[str, Any], *, rejected_code: int) -> str:
        candidates = set(str(value) for value in row["resolver_event_types"])
        if bool(row["reset"]):
            candidates.add("reset")
        if bool(row["target_completed_this_step"]):
            candidates.add("target_completed")
        if bool(row["release_budget_failure_this_step"]):
            candidates.add("release_budget_failure")
        if bool(row["budget_failure_this_step"]):
            candidates.add("budget_failure")
        if bool(row["active_target_infeasible_deferred"]):
            candidates.add("active_target_infeasible_deferred")
        rejection_events = {
            REJECT_SWITCH_DISABLED: "switch_rejected_executing",
            REJECT_CLAIM_LOST: "claim_lost",
            REJECT_OWNED_TARGET: "owned_target_rejected",
            REJECT_FAILED_PAIR: "failed_pair_reclaim_rejected",
            REJECT_COVERED_TARGET: "covered_target_rejected",
            REJECT_UNAVAILABLE_TARGET: "unavailable_target_rejected",
        }
        if rejected_code in rejection_events:
            candidates.add(rejection_events[rejected_code])
        if bool(row["new_claim_started"]):
            candidates.add("attempt_started")
        if bool(row["continued_from_active_target"]):
            candidates.add(
                "attempt_continued_noop_contract_c"
                if bool(row["proposal_is_noop"])
                else "attempt_continued_same_target"
            )
        if bool(row["proposal_is_noop"]) and int(row["active_target_before"]) == NO_TARGET:
            candidates.add("noop_idle")
        for event_type in PRIMARY_ATTRIBUTION_PRIORITY:
            if event_type in candidates:
                return event_type
        return "unclassified"

    def _distance_to_target(
        self,
        snapshot: AssignmentPlaybackPhysicalSnapshot | None,
        env_id: int,
        robot_id: int,
        target_id: int,
    ) -> float | None:
        if snapshot is None or target_id < 0 or target_id >= self.num_tasks:
            return None
        delta = snapshot.scanner_pos[env_id, robot_id] - snapshot.viewpoint_pos[env_id, target_id]
        return float(torch.linalg.vector_norm(delta).cpu().item())

    def _validate_segment_transition(self, row: Mapping[str, Any], *, lifecycle_enabled: bool) -> None:
        if not lifecycle_enabled:
            return
        key = (int(row["env_id"]), int(row["robot_id"]))
        active_before = int(row["active_target_before"])
        active_after = int(row["active_target_after"])
        effective = int(row["effective_assignment"])
        started = "attempt_started" in row["resolver_event_types"]
        if started != bool(row["new_claim_started"]):
            self._invariant_break(key, row, "attempt_started event disagrees with new_claim_started")
        terminal = bool(
            row["target_completed_this_step"]
            or row["release_budget_failure_this_step"]
            or row["reset"]
        )
        segment = self._open_segments.get(key)
        if segment is not None and int(segment["target_id"]) != active_before:
            self._invariant_break(key, row, "open segment does not match active_target_before")
        if segment is None and active_before >= 0:
            self._invariant_break(key, row, "active target has no open segment")
        if active_before >= 0 and effective != active_before:
            self._invariant_break(key, row, "effective assignment does not continue the active target")
        if started and active_before != NO_TARGET:
            self._invariant_break(key, row, "attempt_started occurred while a target was already active")
        if started and effective < 0:
            self._invariant_break(key, row, "attempt_started has no effective target")
        if active_before == NO_TARGET and effective >= 0 and not started:
            self._invariant_break(key, row, "effective target appeared without attempt_started")
        if active_after != active_before:
            expected_start = started and active_before == NO_TARGET and active_after == effective
            expected_end = terminal and active_after == NO_TARGET
            if not expected_start and not expected_end:
                self._invariant_break(key, row, "unexplained active-target change")

    def _invariant_break(self, key: tuple[int, int], row: Mapping[str, Any], message: str) -> None:
        failure = (
            f"{message}: episode={row['episode_id']} env={row['env_id']} "
            f"step={row['decision_step']} robot={row['robot_id']}"
        )
        self._invariant_failures.append(failure)
        if key in self._open_segments:
            self._close_segment(
                key,
                end_step=int(row["decision_step"]),
                release_type="invariant_break",
                terminal_event_types=list(row["resolver_event_types"]),
            )
        raise AttributionInvariantError(failure)

    def _update_segment(self, row: Mapping[str, Any], *, lifecycle_enabled: bool) -> None:
        if not lifecycle_enabled:
            return
        key = (int(row["env_id"]), int(row["robot_id"]))
        started = "attempt_started" in row["resolver_event_types"]
        if started:
            self._segment_ids[key] += 1
            self._open_segments[key] = {
                "schema_version": SCHEMA_VERSION,
                "method_name": self.method_name,
                "episode_id": int(row["episode_id"]),
                "env_id": int(row["env_id"]),
                "robot_id": int(row["robot_id"]),
                "robot_name": str(row["robot_name"]),
                "segment_id": int(self._segment_ids[key].item()),
                "target_id": int(row["effective_assignment"]),
                "start_step": int(row["decision_step"]),
                "last_step": int(row["decision_step"]),
                "minimum_distance": None,
                "zero_distance_dwell_steps": 0,
                "coverage_gain_during_segment": 0,
                "start_distance": row["distance_to_effective_target_before"],
                "final_distance": row["distance_to_effective_target_after"],
                "cumulative_positive_distance_progress": 0.0,
                "zero_progress_steps": 0,
                "zero_base_motion_steps": 0,
                "active_infeasible_steps": 0,
                "noop_continue_steps": 0,
                "same_target_continue_steps": 0,
                "switch_rejected_steps": 0,
                "start_raw_action_id": int(row["raw_action_id"]),
                "start_decoded_proposal": int(row["decoded_proposal"]),
                "assigned_target_completion_count": 0,
                "incidental_coverage_count": 0,
                "unattributed_coverage_count": 0,
            }
        segment = self._open_segments.get(key)
        if segment is None:
            return
        segment["last_step"] = int(row["decision_step"])
        distances = [
            row["distance_to_effective_target_before"],
            row["distance_to_effective_target_after"],
        ]
        finite_distances = [float(value) for value in distances if value is not None and math.isfinite(float(value))]
        if finite_distances:
            current_min = min(finite_distances)
            segment["minimum_distance"] = (
                current_min
                if segment["minimum_distance"] is None
                else min(float(segment["minimum_distance"]), current_min)
            )
        if row["distance_to_effective_target_after"] is not None:
            distance_after = float(row["distance_to_effective_target_after"])
            segment["final_distance"] = distance_after
            threshold = float(self.distance_dwell_thresholds[int(row["robot_id"])].item())
            if distance_after <= threshold:
                segment["zero_distance_dwell_steps"] += 1
        if row["distance_progress"] is not None:
            progress = float(row["distance_progress"])
            segment["cumulative_positive_distance_progress"] += max(progress, 0.0)
            if abs(progress) <= self.zero_progress_epsilon:
                segment["zero_progress_steps"] += 1
        if row["base_motion_distance"] is not None and float(row["base_motion_distance"]) <= self.zero_motion_epsilon:
            segment["zero_base_motion_steps"] += 1
        if bool(row["active_target_infeasible_deferred"]):
            segment["active_infeasible_steps"] += 1
        if "attempt_continued_noop_contract_c" in row["resolver_event_types"]:
            segment["noop_continue_steps"] += 1
        if "attempt_continued_same_target" in row["resolver_event_types"]:
            segment["same_target_continue_steps"] += 1
        if "switch_rejected_executing" in row["resolver_event_types"]:
            segment["switch_rejected_steps"] += 1
        assigned_count = int(row["assigned_target_completion_count"] or 0)
        incidental_count = int(row["incidental_coverage_count"] or 0)
        unattributed_count = int(row["unattributed_coverage_count"] or 0)
        segment["assigned_target_completion_count"] += assigned_count
        segment["incidental_coverage_count"] += incidental_count
        segment["unattributed_coverage_count"] += unattributed_count
        segment["coverage_gain_during_segment"] += assigned_count + incidental_count

        release_type = None
        if bool(row["target_completed_this_step"]):
            release_type = "target_completed"
        elif bool(row["release_budget_failure_this_step"]):
            release_type = "budget_failure"
        elif bool(row["reset"]):
            release_type = "reset"
        if release_type is not None:
            self._close_segment(
                key,
                end_step=int(row["decision_step"]),
                release_type=release_type,
                terminal_event_types=list(row["resolver_event_types"]),
            )

    def _close_segment(
        self,
        key: tuple[int, int],
        *,
        end_step: int,
        release_type: str,
        terminal_event_types: Sequence[str],
    ) -> None:
        segment = self._open_segments.pop(key)
        start_step = int(segment.pop("start_step"))
        segment.pop("last_step", None)
        segment.update(
            {
                "start_step": start_step,
                "end_step": int(end_step),
                "duration_steps": int(end_step) - start_step + 1,
                "release_type": str(release_type),
                "terminal_event_types": list(terminal_event_types),
            }
        )
        self._segments.append({field: segment.get(field) for field in SEGMENT_FIELDS})

    def _write_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        if self.rows_path is None:
            return
        with self.rows_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=ROW_FIELDS)
            for row in rows:
                writer.writerow({field: self._csv_cell(row.get(field)) for field in ROW_FIELDS})

    @staticmethod
    def _csv_cell(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(_json_safe(value), separators=(",", ":"), sort_keys=True)
        return value

    def _build_summary(self, *, include_open_segments: bool = False) -> dict[str, Any]:
        segment_rows = list(self._segments)
        if include_open_segments:
            segment_rows.extend(copy.deepcopy(list(self._open_segments.values())))
        grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
        for row in self._rows:
            key = (int(row["episode_id"]), int(row["env_id"]), int(row["robot_id"]))
            grouped.setdefault(key, []).append(row)
        per_robot: list[dict[str, Any]] = []
        for key in sorted(grouped):
            episode_id, env_id, robot_id = key
            rows = grouped[key]
            event_counts: dict[str, int] = {}
            rejection_counts: dict[str, int] = {}
            for row in rows:
                for event_type in row["resolver_event_types"]:
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
                if row["proposal_rejected"]:
                    reason = str(row["proposal_rejected_reason"])
                    rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
            starts = {
                int(row["effective_assignment"])
                for row in rows
                if "attempt_started" in row["resolver_event_types"] and int(row["effective_assignment"]) >= 0
            }
            completed_targets: set[int] = set()
            for row in rows:
                for event in row["resolver_events"]:
                    if event.get("event_type") == "target_completed" and event.get("target_id") is not None:
                        completed_targets.add(int(event["target_id"]))
            total = len(rows)
            idle = sum(int(row["effective_assignment"] < 0) for row in rows)
            executing = total - idle
            proposal_noop = sum(int(row["proposal_is_noop"]) for row in rows)
            proposal_target = total - proposal_noop
            if idle + executing != total or proposal_noop + proposal_target != total:
                raise AttributionInvariantError("per-robot decision accounting identity failed")
            summary = {
                "method_name": self.method_name,
                "episode_id": episode_id,
                "env_id": env_id,
                "robot_id": robot_id,
                "robot_name": self.robot_names[robot_id],
                "total_decision_steps": total,
                "proposal_noop_count": proposal_noop,
                "proposal_target_count": proposal_target,
                "effective_idle_noop_count": idle,
                "effective_target_count": executing,
                "proposal_effective_changed_count": sum(int(row["proposal_effective_changed"]) for row in rows),
                "proposal_rejected_count": sum(int(row["proposal_rejected"]) for row in rows),
                "noop_idle_count": event_counts.get("noop_idle", 0),
                "noop_continue_active_count": event_counts.get("attempt_continued_noop_contract_c", 0),
                "attempt_started_count": event_counts.get("attempt_started", 0),
                "same_target_continue_count": event_counts.get("attempt_continued_same_target", 0),
                "switch_rejected_count": event_counts.get("switch_rejected_executing", 0),
                "exact_conflict_win_count": sum(int(row["claim_conflict"] and row["claim_winner"]) for row in rows),
                "exact_conflict_loss_count": sum(int(row["claim_conflict"] and row["claim_loser"]) for row in rows),
                "owned_target_rejected_count": event_counts.get("owned_target_rejected", 0),
                "covered_target_rejected_count": event_counts.get("covered_target_rejected", 0),
                "failed_pair_reclaim_rejected_count": event_counts.get("failed_pair_reclaim_rejected", 0),
                "unavailable_target_rejected_count": event_counts.get("unavailable_target_rejected", 0),
                "active_target_infeasible_deferred_count": sum(
                    int(row["active_target_infeasible_deferred"]) for row in rows
                ),
                "target_completed_count": sum(int(row["target_completed_this_step"]) for row in rows),
                "budget_failure_count": sum(int(row["budget_failure_this_step"]) for row in rows),
                "release_budget_failure_count": sum(
                    int(row["release_budget_failure_this_step"]) for row in rows
                ),
                "idle_step_count": idle,
                "executing_step_count": executing,
                "idle_fraction": float(idle / total) if total else None,
                "executing_fraction": float(executing / total) if total else None,
                "unique_targets_started": sorted(starts),
                "unique_targets_completed": sorted(completed_targets),
                "assigned_target_completion_count": sum(
                    int(row["assigned_target_completion_count"] or 0) for row in rows
                ),
                "coverage_delta_count": sum(int(row["coverage_delta_count"] or 0) for row in rows),
                "incidental_coverage_count": sum(int(row["incidental_coverage_count"] or 0) for row in rows),
                "unattributed_coverage_count": sum(
                    int(row["unattributed_coverage_count"] or 0) for row in rows
                ),
                "zero_controller_command_count": sum(
                    int(float(row["controller_action_l2_norm"]) <= self.zero_command_epsilon) for row in rows
                ),
                "zero_base_motion_step_count": sum(
                    int(
                        row["base_motion_distance"] is not None
                        and float(row["base_motion_distance"]) <= self.zero_motion_epsilon
                    )
                    for row in rows
                ),
                "zero_progress_step_count": sum(
                    int(
                        row["distance_progress"] is not None
                        and abs(float(row["distance_progress"])) <= self.zero_progress_epsilon
                    )
                    for row in rows
                ),
                "active_target_segment_count": sum(
                    int(segment.get("episode_id") == episode_id)
                    * int(segment.get("env_id") == env_id)
                    * int(segment.get("robot_id") == robot_id)
                    for segment in segment_rows
                ),
                "resolver_event_counts": event_counts,
                "proposal_rejection_reason_counts": rejection_counts,
            }
            per_robot.append(summary)

        load_summaries: list[dict[str, Any]] = []
        episode_env_keys = sorted({(item["episode_id"], item["env_id"]) for item in per_robot})
        for episode_id, env_id in episode_env_keys:
            by_robot = {
                int(item["robot_id"]): item
                for item in per_robot
                if item["episode_id"] == episode_id and item["env_id"] == env_id
            }
            if len(by_robot) != self.num_robots:
                raise AttributionInvariantError("episode load summary is missing a robot row")
            executing = [int(by_robot[r]["executing_step_count"]) for r in range(self.num_robots)]
            idle = [int(by_robot[r]["idle_step_count"]) for r in range(self.num_robots)]
            starts = [int(by_robot[r]["attempt_started_count"]) for r in range(self.num_robots)]
            completions = [int(by_robot[r]["target_completed_count"]) for r in range(self.num_robots)]
            releases = [int(by_robot[r]["release_budget_failure_count"]) for r in range(self.num_robots)]
            assigned = [int(by_robot[r]["assigned_target_completion_count"]) for r in range(self.num_robots)]
            coverage = [int(by_robot[r]["coverage_delta_count"]) for r in range(self.num_robots)]
            load_summaries.append(
                {
                    "method_name": self.method_name,
                    "episode_id": episode_id,
                    "env_id": env_id,
                    "executing_steps": executing,
                    "idle_steps": idle,
                    "target_starts": starts,
                    "target_completions": completions,
                    "budget_releases": releases,
                    "assigned_target_completions": assigned,
                    "coverage_delta_counts": coverage,
                    "executing_step_range": max(executing) - min(executing),
                    "completion_count_range": max(completions) - min(completions),
                    "executing_fraction_of_team_total_by_robot": self._fractions(executing),
                    "completion_fraction_of_team_total_by_robot": self._fractions(completions),
                    "robots_with_zero_target_starts": [r for r, value in enumerate(starts) if value == 0],
                    "robots_with_zero_completions": [r for r, value in enumerate(completions) if value == 0],
                    "jain_executing_steps": self._jain(executing),
                    "jain_completion_count": self._jain(completions),
                    "classification": "playback_diagnostics_only",
                    "not_reward_or_optimizer_objective": True,
                    "not_automatic_pass_fail": True,
                }
            )

        valid_rows = sum(int(row["post_state_pre_reset_available"]) for row in self._rows)
        return {
            "schema_version": SCHEMA_VERSION,
            "method_name": self.method_name,
            "num_envs": self.num_envs,
            "num_robots": self.num_robots,
            "num_tasks": self.num_tasks,
            "robot_names": list(self.robot_names),
            "raw_noop_id": self.noop_raw_id,
            "decoded_noop": NO_TARGET,
            "resolver_enabled_values_seen": sorted(self._resolver_enabled_seen),
            "per_robot_summaries": per_robot,
            "episode_load_balance_summaries": load_summaries,
            "episode_boundary_events": copy.deepcopy(self._episode_boundary_events),
            "unprojected_environment_events": copy.deepcopy(self._unprojected_environment_events),
            "validity_counters": {
                "post_state_pre_reset_available_rows": valid_rows,
                "post_state_pre_reset_unavailable_rows": len(self._rows) - valid_rows,
                "coverage_null_rows": sum(int(row["coverage_delta_ids"] is None) for row in self._rows),
                "base_motion_null_rows": sum(int(row["base_motion_distance"] is None) for row in self._rows),
            },
            "artifact_paths": {
                "rows_csv": str(self.rows_path) if self.rows_path is not None else None,
                "summary_json": str(self.summary_path) if self.summary_path is not None else None,
                "segments_csv": str(self.segments_path) if self.segments_path is not None else None,
            },
            "row_count": len(self._rows),
            "segment_count": len(segment_rows),
            "invariant_failures": list(self._invariant_failures),
            "coverage_attribution_note": (
                "incidental coverage remains unattributed because the current environment does not expose a reliable "
                "per-robot source; no nearest-distance guessing is used"
            ),
        }

    @staticmethod
    def _fractions(values: Sequence[int]) -> list[float | None]:
        total = sum(values)
        if total == 0:
            return [None for _ in values]
        return [float(value / total) for value in values]

    @staticmethod
    def _jain(values: Sequence[int]) -> float | None:
        total = float(sum(values))
        denominator = float(len(values) * sum(value * value for value in values))
        if total == 0.0 or denominator == 0.0:
            return None
        return float((total * total) / denominator)


__all__ = [
    "AttributionInvariantError",
    "AssignmentPlaybackAttributionCollector",
    "AssignmentPlaybackPhysicalSnapshot",
    "OUTPUT_FILENAMES",
    "PRIMARY_ATTRIBUTION_PRIORITY",
    "ROWS_FILENAME",
    "ROW_FIELDS",
    "SCHEMA_VERSION",
    "SEGMENTS_FILENAME",
    "SEGMENT_FIELDS",
    "SUMMARY_FILENAME",
    "capture_assignment_playback_physical_snapshot",
    "format_assignment_playback_attribution_row",
    "make_assignment_playback_attribution_collector_if_enabled",
    "stack_assignment_controller_actions",
    "validate_assignment_playback_attribution_cli",
]
