"""Pure regressions for playback proposal/effective attribution diagnostics.

These tests use synthetic tensors only. They do not import Isaac Lab, launch an
application, load a checkpoint, run playback, evaluate, or train.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from assignment_lifecycle_resolver import (  # noqa: E402
    NO_OWNER,
    NO_TARGET,
    PAIR_ACTIVE,
    PAIR_COMPLETED,
    PAIR_NONE,
    PAIR_RELEASED_BUDGET,
    REASON_BUDGET_FAILURE,
    REASON_NONE,
    REJECT_CLAIM_LOST,
    REJECT_COVERED_TARGET,
    REJECT_FAILED_PAIR,
    REJECT_NONE,
    REJECT_OWNED_TARGET,
    REJECT_SWITCH_DISABLED,
    REJECT_UNAVAILABLE_TARGET,
)
from assignment_playback_attribution_diagnostics import (  # noqa: E402
    AttributionInvariantError,
    AssignmentPlaybackAttributionCollector,
    OUTPUT_FILENAMES,
    ROWS_FILENAME,
    SCHEMA_VERSION,
    SEGMENTS_FILENAME,
    SUMMARY_FILENAME,
    capture_assignment_playback_physical_snapshot,
    format_assignment_playback_attribution_row,
    make_assignment_playback_attribution_collector_if_enabled,
    stack_assignment_controller_actions,
    validate_assignment_playback_attribution_cli,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _physical_snapshot(
    *,
    e: int,
    m: int,
    n: int,
    covered_ids: dict[int, list[int]] | None = None,
    unavailable: list[tuple[int, int, int]] | None = None,
    base_offset: float = 0.0,
) -> Any:
    base_pos = torch.zeros(e, m, 3, dtype=torch.float32)
    scanner_pos = torch.zeros(e, m, 3, dtype=torch.float32)
    for env_id in range(e):
        for robot_id in range(m):
            base_pos[env_id, robot_id, 0] = float(env_id * 10 + robot_id + base_offset)
            scanner_pos[env_id, robot_id] = base_pos[env_id, robot_id]
    viewpoint_pos = torch.zeros(e, n, 3, dtype=torch.float32)
    for target_id in range(n):
        viewpoint_pos[:, target_id, 0] = float(target_id + 1)
    covered = torch.zeros(e, n, dtype=torch.bool)
    for env_id, ids in (covered_ids or {}).items():
        covered[env_id, ids] = True
    available = (~covered[:, None, :]).expand(e, m, n).clone()
    feasible = available.clone()
    for env_id, robot_id, target_id in unavailable or []:
        available[env_id, robot_id, target_id] = False
        feasible[env_id, robot_id, target_id] = False
    problem = {
        "base_pos": base_pos,
        "scanner_pos": scanner_pos,
        "viewpoint_pos": viewpoint_pos,
        "viewpoints_covered": covered,
        "available_mask": available,
        "feasible_mask": feasible,
    }
    return capture_assignment_playback_physical_snapshot(problem)


def _state_from_active(
    active: torch.Tensor,
    *,
    n: int,
    pair_state: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    e, m = active.shape
    owner = torch.full((e, n), NO_OWNER, dtype=torch.long)
    pair = torch.full((e, m, n), PAIR_NONE, dtype=torch.long) if pair_state is None else pair_state.clone()
    for env_id in range(e):
        for robot_id in range(m):
            target_id = int(active[env_id, robot_id].item())
            if target_id >= 0:
                owner[env_id, target_id] = robot_id
                pair[env_id, robot_id, target_id] = PAIR_ACTIVE
    return owner, pair


def _payload(
    *,
    proposal: list[list[int]],
    effective: list[list[int]],
    active_after: list[list[int]],
    n: int,
    events: list[dict[str, Any]],
    rejected: list[list[int]] | None = None,
    accepted: list[list[bool]] | None = None,
    continued: list[list[bool]] | None = None,
    started: list[list[bool]] | None = None,
    switch_requested: list[list[bool]] | None = None,
    switch_rejected: list[list[bool]] | None = None,
    conflict: list[list[bool]] | None = None,
    winner: list[list[bool]] | None = None,
    loser: list[list[bool]] | None = None,
    completed: list[list[bool]] | None = None,
    released: list[list[bool]] | None = None,
    release_reason: list[list[int]] | None = None,
    failure_reason: list[list[int]] | None = None,
    reset_env_ids: list[int] | None = None,
    pair_state: torch.Tensor | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    proposal_tensor = torch.tensor(proposal, dtype=torch.long)
    effective_tensor = torch.tensor(effective, dtype=torch.long)
    active_tensor = torch.tensor(active_after, dtype=torch.long)
    e, m = proposal_tensor.shape
    owner, pair = _state_from_active(active_tensor, n=n, pair_state=pair_state)

    def bool_tensor(value: list[list[bool]] | None) -> torch.Tensor:
        return torch.zeros(e, m, dtype=torch.bool) if value is None else torch.tensor(value, dtype=torch.bool)

    def long_tensor(value: list[list[int]] | None, default: int) -> torch.Tensor:
        return torch.full((e, m), default, dtype=torch.long) if value is None else torch.tensor(value, dtype=torch.long)

    return {
        "enabled": bool(enabled),
        "assignment_proposal": proposal_tensor,
        "effective_assignment": effective_tensor,
        "proposal_effective_changed": proposal_tensor != effective_tensor,
        "proposal_accepted": bool_tensor(accepted),
        "proposal_rejected_reason": long_tensor(rejected, REJECT_NONE),
        "continued_from_active_target": bool_tensor(continued),
        "new_claim_started": bool_tensor(started),
        "switch_requested": bool_tensor(switch_requested),
        "switch_rejected": bool_tensor(switch_rejected),
        "claim_conflict": bool_tensor(conflict),
        "claim_winner": bool_tensor(winner),
        "claim_loser": bool_tensor(loser),
        "pre_behavior_changed": bool((proposal_tensor != effective_tensor).any()),
        "post_completed": bool_tensor(completed),
        "post_released": bool_tensor(released),
        "post_release_reason": long_tensor(release_reason, REASON_NONE),
        "post_failure_reason": long_tensor(failure_reason, REASON_NONE),
        "post_reset_env_ids": list(reset_env_ids or []),
        "post_behavior_changed": bool(bool_tensor(completed).any() or bool_tensor(released).any()),
        "resolver_snapshot": {
            "active_target_id": active_tensor,
            "task_owner_robot_id": owner,
            "pair_state": pair,
        },
        "resolver_events": copy.deepcopy(events),
    }


def _collector(*, e: int, m: int, n: int, output_dir: Path | None = None) -> AssignmentPlaybackAttributionCollector:
    collector = AssignmentPlaybackAttributionCollector(
        method_name="fake_happo",
        num_envs=e,
        num_robots=m,
        num_tasks=n,
        robot_names=[f"robot_{robot_id}" for robot_id in range(m)],
        noop_raw_id=n,
        output_dir=output_dir,
        distance_dwell_thresholds=[0.25 for _ in range(m)],
    )
    collector.reset_envs(episode_ids=torch.zeros(e, dtype=torch.long))
    return collector


def _record(
    collector: AssignmentPlaybackAttributionCollector,
    payload: dict[str, Any],
    *,
    pre: Any | None = None,
    post: Any | None = None,
    post_valid: list[bool] | None = None,
    dones: list[bool] | None = None,
    controller_actions: torch.Tensor | None = None,
) -> list[dict[str, Any]]:
    e, m = payload["assignment_proposal"].shape
    n = collector.num_tasks
    raw = torch.where(
        payload["assignment_proposal"] == NO_TARGET,
        torch.full_like(payload["assignment_proposal"], n),
        payload["assignment_proposal"],
    ).unsqueeze(-1)
    pre = pre or _physical_snapshot(e=e, m=m, n=n)
    if post_valid is None:
        post_valid = [True for _ in range(e)]
    if post is None and any(post_valid):
        post = _physical_snapshot(e=e, m=m, n=n, base_offset=0.1)
    return collector.record_decision(
        raw_actions=raw,
        selected_action_probabilities=torch.full((e, m), 0.5, dtype=torch.float32),
        pre_state=pre,
        lifecycle_resolution=payload,
        controller_assignment=payload["effective_assignment"],
        controller_actions=(
            torch.zeros(e, m, 9, dtype=torch.float32) if controller_actions is None else controller_actions
        ),
        post_state=post,
        post_state_pre_reset_available=post_valid,
        dones=dones or [False for _ in range(e)],
    )


def _event(event_type: str, *, env: int = 0, robot: int | None = 0, target: int | None = None, **extra) -> dict:
    result: dict[str, Any] = {"event_type": event_type, "env_id": env, "step": 0}
    if robot is not None:
        result["robot_id"] = robot
    if target is not None:
        result["target_id"] = target
    result.update(extra)
    return result


def _case_cli_default_off_and_collisions() -> dict[str, Any]:
    calls: list[dict[str, Any]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("default-off factory must not be called")

    result = make_assignment_playback_attribution_collector_if_enabled(
        log_enabled=False,
        print_enabled=False,
        output_dir=None,
        collector_factory=factory,
        method_name="unused",
    )
    _assert(result is None and calls == [], "default-off collector factory was called")
    print_only = make_assignment_playback_attribution_collector_if_enabled(
        log_enabled=False,
        print_enabled=True,
        output_dir=None,
        method_name="fake_happo",
        num_envs=1,
        num_robots=1,
        num_tasks=3,
        robot_names=["robot_0"],
        noop_raw_id=3,
    )
    _assert(print_only is not None and print_only.output_dir is None, "print-only mode unexpectedly writes files")
    print_only.finalize()
    for kwargs in (
        {"log_enabled": True, "print_enabled": False, "output_dir": None},
        {"log_enabled": False, "print_enabled": False, "output_dir": "unused"},
    ):
        try:
            validate_assignment_playback_attribution_cli(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid CLI combination did not fail: {kwargs}")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        (output / ROWS_FILENAME).write_text("existing", encoding="utf-8")
        try:
            validate_assignment_playback_attribution_cli(
                log_enabled=True,
                print_enabled=False,
                output_dir=output,
            )
        except FileExistsError:
            pass
        else:
            raise AssertionError("existing output collision was not rejected")
    return {"case": "cli_default_off_and_collisions", "passed": True}


def _case_snapshot_and_controller_no_alias() -> dict[str, Any]:
    e, m, n = 2, 3, 5
    problem = {
        "base_pos": torch.randn(e, m, 3),
        "scanner_pos": torch.randn(e, m, 3),
        "viewpoint_pos": torch.randn(e, n, 3),
        "viewpoints_covered": torch.zeros(e, n, dtype=torch.bool),
        "available_mask": torch.ones(e, m, n, dtype=torch.bool),
        "feasible_mask": torch.ones(e, m, n, dtype=torch.bool),
    }
    original = {key: value.clone() for key, value in problem.items()}
    snapshot = capture_assignment_playback_physical_snapshot(problem)
    for value in problem.values():
        value.fill_(7)
    _assert(torch.equal(snapshot.base_pos, original["base_pos"]), "snapshot base_pos aliases source")
    _assert(torch.equal(snapshot.available_mask, original["available_mask"]), "snapshot mask aliases source")
    actions = {f"robot_{r}": torch.full((e, 9), float(r)) for r in range(m)}
    stacked = stack_assignment_controller_actions(actions, [f"robot_{r}" for r in range(m)])
    actions["robot_1"].fill_(99)
    _assert(float(stacked[0, 1, 0]) == 1.0, "stacked controller actions alias source")
    return {"case": "snapshot_and_controller_no_alias", "passed": True}


def _case_idle_noop_initial_reset_boundary() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    payload = _payload(
        proposal=[[-1]],
        effective=[[-1]],
        active_after=[[-1]],
        n=3,
        accepted=[[True]],
        events=[_event("reset"), _event("noop_idle")],
    )
    row = _record(collector, payload)[0]
    _assert(row["primary_attribution"] == "noop_idle", "initial reset polluted first attribution")
    _assert(row["reset_before_decision"] is True, "explicit reset boundary metadata missing")
    _assert(row["effective_is_noop"], "idle noop not recorded")
    summary = collector.finalize()
    robot = summary["per_robot_summaries"][0]
    _assert(robot["idle_step_count"] == 1 and robot["executing_step_count"] == 0, "idle accounting failed")
    _assert(len(summary["episode_boundary_events"]) == 1, "initial reset boundary event missing")
    return {"case": "idle_noop_initial_reset_boundary", "passed": True}


def _case_active_sequence_completion_and_segments() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=4)
    rows: list[dict[str, Any]] = []
    rows += _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=4,
            accepted=[[True]], started=[[True]], winner=[[True]],
            events=[_event("attempt_started", target=1)],
        ),
    )
    rows += _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=4,
            accepted=[[True]], continued=[[True]],
            events=[_event("attempt_continued_same_target", target=1)],
        ),
    )
    rows += _record(
        collector,
        _payload(
            proposal=[[-1]], effective=[[1]], active_after=[[1]], n=4,
            accepted=[[True]], continued=[[True]],
            events=[_event("attempt_continued_noop_contract_c", target=1)],
        ),
    )
    rows += _record(
        collector,
        _payload(
            proposal=[[2]], effective=[[1]], active_after=[[1]], n=4,
            rejected=[[REJECT_SWITCH_DISABLED]], switch_requested=[[True]], switch_rejected=[[True]],
            events=[_event("switch_rejected_executing", target=1, proposed_target_id=2)],
        ),
    )
    rows += _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=4,
            accepted=[[True]], continued=[[True]],
            events=[
                _event("active_target_infeasible_deferred", target=1),
                _event("attempt_continued_same_target", target=1),
            ],
        ),
    )
    completion_pre = _physical_snapshot(e=1, m=1, n=4)
    completion_post = _physical_snapshot(e=1, m=1, n=4, covered_ids={0: [1, 2]}, base_offset=0.2)
    pair_completed = torch.full((1, 1, 4), PAIR_NONE, dtype=torch.long)
    pair_completed[0, 0, 1] = PAIR_COMPLETED
    rows += _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[-1]], n=4,
            accepted=[[True]], continued=[[True]], completed=[[True]], pair_state=pair_completed,
            events=[
                _event("attempt_continued_same_target", target=1),
                _event("target_completed", target=1, owner_robot_id=0),
            ],
        ),
        pre=completion_pre,
        post=completion_post,
    )
    _assert(rows[2]["primary_attribution"] == "attempt_continued_noop_contract_c", "Contract C label failed")
    _assert(rows[2]["effective_assignment"] == 1, "Contract C continuation counted idle")
    _assert(rows[3]["primary_attribution"] == "switch_rejected_executing", "switch label failed")
    _assert(rows[4]["primary_attribution"] == "active_target_infeasible_deferred", "infeasible priority failed")
    completion = rows[-1]
    _assert(completion["primary_attribution"] == "target_completed", "completion priority failed")
    _assert(completion["coverage_delta_ids"] == [1, 2], "coverage delta ids failed")
    _assert(completion["assigned_target_completion_count"] == 1, "assigned completion credit failed")
    _assert(completion["incidental_coverage_ids"] == [], "incidental coverage was guessed")
    _assert(completion["unattributed_coverage_ids"] == [2], "unattributed coverage split failed")
    summary = collector.finalize()
    robot = summary["per_robot_summaries"][0]
    _assert(robot["executing_step_count"] == 6 and robot["idle_step_count"] == 0, "executing accounting failed")
    _assert(robot["noop_continue_active_count"] == 1, "noop continuation summary failed")
    _assert(robot["switch_rejected_count"] == 1, "switch summary failed")
    segments = collector.get_segments()
    _assert(len(segments) == 1, "active sequence segment count failed")
    _assert(segments[0]["duration_steps"] == 6, "segment duration failed")
    _assert(segments[0]["release_type"] == "target_completed", "segment completion release failed")
    return {"case": "active_sequence_completion_and_segments", "passed": True}


def _case_exact_conflict_projection() -> dict[str, Any]:
    collector = _collector(e=1, m=2, n=3)
    conflict_event = _event(
        "exact_claim_conflict_resolved",
        robot=None,
        target=1,
        claiming_robot_ids=[0, 1],
        winner_robot_id=0,
        loser_robot_ids=[1],
    )
    rows = _record(
        collector,
        _payload(
            proposal=[[1, 1]], effective=[[1, -1]], active_after=[[1, -1]], n=3,
            rejected=[[REJECT_NONE, REJECT_CLAIM_LOST]],
            accepted=[[True, False]], started=[[True, False]],
            conflict=[[True, True]], winner=[[True, False]], loser=[[False, True]],
            events=[
                conflict_event,
                _event("attempt_started", robot=0, target=1),
                _event("claim_lost", robot=1, target=1, owner_robot_id=0),
            ],
        ),
    )
    _assert(rows[0]["primary_attribution"] == "attempt_started", "conflict winner primary failed")
    _assert(rows[1]["primary_attribution"] == "claim_lost", "conflict loser primary failed")
    _assert(rows[0]["resolver_event_types"].count("exact_claim_conflict_resolved") == 1, "winner conflict duplicated")
    _assert(rows[1]["resolver_event_types"].count("exact_claim_conflict_resolved") == 1, "loser conflict duplicated")
    summary = collector.finalize()
    _assert(summary["per_robot_summaries"][0]["exact_conflict_win_count"] == 1, "conflict win count failed")
    _assert(summary["per_robot_summaries"][1]["exact_conflict_loss_count"] == 1, "conflict loss count failed")
    return {"case": "exact_conflict_projection", "passed": True}


def _case_owned_target_rejection() -> dict[str, Any]:
    collector = _collector(e=1, m=2, n=3)
    _record(
        collector,
        _payload(
            proposal=[[-1, 1]], effective=[[-1, 1]], active_after=[[-1, 1]], n=3,
            accepted=[[True, True]], started=[[False, True]], winner=[[False, True]],
            events=[_event("noop_idle", robot=0), _event("attempt_started", robot=1, target=1)],
        ),
    )
    rows = _record(
        collector,
        _payload(
            proposal=[[1, 1]], effective=[[-1, 1]], active_after=[[-1, 1]], n=3,
            rejected=[[REJECT_OWNED_TARGET, REJECT_NONE]], accepted=[[False, True]],
            continued=[[False, True]],
            events=[
                _event("owned_target_rejected", robot=0, target=1, owner_robot_id=1),
                _event("attempt_continued_same_target", robot=1, target=1),
            ],
        ),
    )
    rejected = rows[0]
    _assert(rejected["primary_attribution"] == "owned_target_rejected", "owned rejection label failed")
    _assert(rejected["proposal_target_owner_before"] == 1, "pre owner attribution failed")
    _assert(rejected["owner_robot_id"] == 1, "owner id projection failed")
    collector.finalize()
    return {"case": "owned_target_rejection", "passed": True}


def _case_covered_and_unavailable_rejections() -> dict[str, Any]:
    covered_collector = _collector(e=1, m=1, n=3)
    covered = _physical_snapshot(e=1, m=1, n=3, covered_ids={0: [2]})
    covered_row = _record(
        covered_collector,
        _payload(
            proposal=[[2]], effective=[[-1]], active_after=[[-1]], n=3,
            rejected=[[REJECT_COVERED_TARGET]],
            events=[_event("covered_target_rejected", target=2)],
        ),
        pre=covered,
        post=covered,
    )[0]
    _assert(covered_row["proposal_covered_before"] is True, "covered pre-state missing")
    _assert(covered_row["primary_attribution"] == "covered_target_rejected", "covered label failed")
    covered_collector.finalize()

    unavailable_collector = _collector(e=1, m=1, n=3)
    unavailable = _physical_snapshot(e=1, m=1, n=3, unavailable=[(0, 0, 1)])
    unavailable_row = _record(
        unavailable_collector,
        _payload(
            proposal=[[1]], effective=[[-1]], active_after=[[-1]], n=3,
            rejected=[[REJECT_UNAVAILABLE_TARGET]],
            events=[_event("unavailable_target_rejected", target=1)],
        ),
        pre=unavailable,
        post=unavailable,
    )[0]
    _assert(unavailable_row["proposal_available_before"] is False, "unavailable pre-state missing")
    _assert(unavailable_row["primary_attribution"] == "unavailable_target_rejected", "unavailable label failed")
    unavailable_collector.finalize()
    return {"case": "covered_and_unavailable_rejections", "passed": True}


def _case_budget_release_and_failed_pair_reclaim() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=3,
            accepted=[[True]], started=[[True]], winner=[[True]],
            events=[_event("attempt_started", target=1)],
        ),
    )
    released_pair = torch.full((1, 1, 3), PAIR_NONE, dtype=torch.long)
    released_pair[0, 0, 1] = PAIR_RELEASED_BUDGET
    release_row = _record(
        collector,
        _payload(
            proposal=[[-1]], effective=[[1]], active_after=[[-1]], n=3,
            accepted=[[True]], continued=[[True]], released=[[True]],
            release_reason=[[REASON_BUDGET_FAILURE]], failure_reason=[[REASON_BUDGET_FAILURE]],
            pair_state=released_pair,
            events=[
                _event("attempt_continued_noop_contract_c", target=1),
                _event("budget_failure", target=1),
                _event("release_budget_failure", target=1),
            ],
        ),
    )[0]
    _assert(release_row["primary_attribution"] == "release_budget_failure", "release priority failed")
    retry_row = _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[-1]], active_after=[[-1]], n=3,
            rejected=[[REJECT_FAILED_PAIR]], pair_state=released_pair,
            events=[_event("failed_pair_reclaim_rejected", target=1)],
        ),
    )[0]
    _assert(retry_row["self_pair_failed_or_released_before"] is True, "failed pair pre-state missing")
    _assert(retry_row["primary_attribution"] == "failed_pair_reclaim_rejected", "failed pair label failed")
    summary = collector.finalize()
    robot = summary["per_robot_summaries"][0]
    _assert(robot["budget_failure_count"] == 1, "budget failure count failed")
    _assert(robot["release_budget_failure_count"] == 1, "budget release count failed")
    _assert(collector.get_segments()[0]["release_type"] == "budget_failure", "budget segment release failed")
    return {"case": "budget_release_and_failed_pair_reclaim", "passed": True}


def _case_done_reset_alignment_and_null_post() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=3,
            accepted=[[True]], started=[[True]], winner=[[True]],
            events=[_event("attempt_started", target=1)],
        ),
    )
    done_row = _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[-1]], n=3,
            accepted=[[True]], continued=[[True]], completed=[[True]], reset_env_ids=[0],
            events=[
                _event("attempt_continued_same_target", target=1),
                _event("target_completed", target=1, owner_robot_id=0),
                _event("reset", target=None),
            ],
        ),
        post=None,
        post_valid=[False],
        dones=[True],
    )[0]
    _assert(done_row["primary_attribution"] == "reset", "done reset priority failed")
    _assert(done_row["target_completed_this_step"] is True, "completion flag lost under reset")
    _assert(done_row["base_motion_distance"] is None, "reset state substituted for base post-state")
    _assert(done_row["coverage_delta_ids"] is None, "reset state substituted for coverage post-state")
    _assert(done_row["post_state_pre_reset_available"] is False, "post validity flag failed")
    collector.finalize()
    _assert(collector.get_segments()[0]["release_type"] == "target_completed", "completion cause lost at reset")
    return {"case": "done_reset_alignment_and_null_post", "passed": True}


def _case_multi_env_subset_reset_and_unprojected_event() -> dict[str, Any]:
    collector = _collector(e=2, m=3, n=5)
    payload = _payload(
        proposal=[[-1, -1, -1], [-1, -1, -1]],
        effective=[[-1, -1, -1], [-1, -1, -1]],
        active_after=[[-1, -1, -1], [-1, -1, -1]],
        n=5,
        accepted=[[True, True, True], [True, True, True]],
        events=[
            *[_event("noop_idle", env=e, robot=r) for e in range(2) for r in range(3)],
            _event("stranded_failed_pair_started", env=0, robot=None, target=4),
        ],
    )
    first_rows = _record(collector, payload)
    _assert(len(first_rows) == 6, "variable E/M row count failed")
    _assert(
        "stranded_failed_pair_started" not in first_rows[0]["resolver_event_types"],
        "robot-less event was guessed onto a robot",
    )
    collector.reset_envs(env_ids=[1], episode_ids=[7])
    second_rows = _record(collector, payload)
    env0 = next(row for row in second_rows if row["env_id"] == 0 and row["robot_id"] == 0)
    env1 = next(row for row in second_rows if row["env_id"] == 1 and row["robot_id"] == 0)
    _assert((env0["episode_id"], env0["decision_step"]) == (0, 2), "non-reset env generation changed")
    _assert((env1["episode_id"], env1["decision_step"]) == (7, 1), "subset reset generation failed")
    summary = collector.finalize()
    _assert(len(summary["unprojected_environment_events"]) == 2, "unprojected event accounting failed")
    return {"case": "multi_env_subset_reset_and_unprojected_event", "passed": True}


def _case_jain_and_open_segment_finalize() -> dict[str, Any]:
    collector = _collector(e=1, m=2, n=3)
    _record(
        collector,
        _payload(
            proposal=[[1, -1]], effective=[[1, -1]], active_after=[[1, -1]], n=3,
            accepted=[[True, True]], started=[[True, False]], winner=[[True, False]],
            events=[_event("attempt_started", robot=0, target=1), _event("noop_idle", robot=1)],
        ),
    )
    summary = collector.finalize()
    segment = collector.get_segments()[0]
    _assert(segment["release_type"] == "playback_truncated", "open segment finalization failed")
    load = summary["episode_load_balance_summaries"][0]
    _assert(abs(float(load["jain_executing_steps"]) - 0.5) < 1.0e-12, "Jain executing value failed")
    _assert(load["jain_completion_count"] is None, "zero-total Jain must be null")
    _assert(load["robots_with_zero_target_starts"] == [1], "zero start robot list failed")
    return {"case": "jain_and_open_segment_finalize", "passed": True}


def _case_invariant_break() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    _record(
        collector,
        _payload(
            proposal=[[1]], effective=[[1]], active_after=[[1]], n=3,
            accepted=[[True]], started=[[True]], winner=[[True]],
            events=[_event("attempt_started", target=1)],
        ),
    )
    try:
        _record(
            collector,
            _payload(
                proposal=[[1]], effective=[[1]], active_after=[[2]], n=3,
                accepted=[[True]], continued=[[True]],
                events=[_event("attempt_continued_same_target", target=1)],
            ),
        )
    except AttributionInvariantError as exc:
        _assert("unexplained active-target change" in str(exc), "invariant error was not actionable")
    else:
        raise AssertionError("unexplained target change did not fail")
    _assert(collector.get_segments()[0]["release_type"] == "invariant_break", "invariant segment not closed")
    return {"case": "invariant_break", "passed": True}


def _case_input_nonmutation_and_copy_results() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    payload = _payload(
        proposal=[[-1]], effective=[[-1]], active_after=[[-1]], n=3,
        accepted=[[True]], events=[_event("noop_idle")],
    )
    payload_before = copy.deepcopy(payload)
    pre = _physical_snapshot(e=1, m=1, n=3)
    pre_before = pre.base_pos.clone()
    actions = torch.zeros(1, 1, 9)
    actions_before = actions.clone()
    rows = _record(collector, payload, pre=pre, controller_actions=actions)
    for key, value in payload_before.items():
        if isinstance(value, torch.Tensor):
            _assert(torch.equal(payload[key], value), f"payload tensor {key} mutated")
    _assert(torch.equal(pre.base_pos, pre_before), "physical snapshot mutated")
    _assert(torch.equal(actions, actions_before), "controller actions mutated")
    rows[0]["resolver_event_types"].append("tampered")
    _assert("tampered" not in collector.get_rows()[0]["resolver_event_types"], "returned rows alias collector state")
    collector.finalize()
    return {"case": "input_nonmutation_and_copy_results", "passed": True}


def _case_output_files_and_idempotent_finalize() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "attribution"
        collector = _collector(e=1, m=1, n=3, output_dir=output)
        _record(
            collector,
            _payload(
                proposal=[[-1]], effective=[[-1]], active_after=[[-1]], n=3,
                accepted=[[True]], events=[_event("noop_idle")],
            ),
        )
        first = collector.finalize()
        mtimes = {name: (output / name).stat().st_mtime_ns for name in OUTPUT_FILENAMES}
        second = collector.finalize()
        _assert(first == second, "finalize is not idempotent")
        _assert(mtimes == {name: (output / name).stat().st_mtime_ns for name in OUTPUT_FILENAMES}, "idempotent finalize rewrote files")
        with (output / ROWS_FILENAME).open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        with (output / SEGMENTS_FILENAME).open("r", encoding="utf-8", newline="") as file:
            segments = list(csv.DictReader(file))
        summary = json.loads((output / SUMMARY_FILENAME).read_text(encoding="utf-8"))
        _assert(len(rows) == 1 and rows[0]["schema_version"] == SCHEMA_VERSION, "rows CSV schema failed")
        _assert(segments == [], "idle output unexpectedly created a segment")
        _assert(summary["row_count"] == 1 and summary["segment_count"] == 0, "summary counts failed")
        _assert(set(path.name for path in output.iterdir()) == set(OUTPUT_FILENAMES), "unexpected output files")
    return {"case": "output_files_and_idempotent_finalize", "passed": True}


def _case_compact_format() -> dict[str, Any]:
    collector = _collector(e=1, m=1, n=3)
    row = _record(
        collector,
        _payload(
            proposal=[[-1]], effective=[[-1]], active_after=[[-1]], n=3,
            accepted=[[True]], events=[_event("noop_idle")],
        ),
    )[0]
    text = format_assignment_playback_attribution_row(row)
    _assert("proposal=-1 effective=-1" in text and "attr=noop_idle" in text, "compact row format failed")
    _assert("resolver_events" not in text, "compact output leaked full event JSON")
    collector.finalize()
    return {"case": "compact_format", "passed": True}


def _case_playback_static_architecture() -> dict[str, Any]:
    play_path = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py"
    module_path = SCAN_TASK_SOURCE / "assignment_playback_attribution_diagnostics.py"
    play_source = play_path.read_text(encoding="utf-8")
    module_source = module_path.read_text(encoding="utf-8")
    validation_call = play_source.index("ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR = validate_assignment_playback_attribution_cli(")
    launcher_call = play_source.index("app_launcher = AppLauncher(args_cli)")
    _assert(validation_call < launcher_call, "CLI validation occurs after AppLauncher")
    _assert(play_source.count("get_last_assignment_lifecycle_resolution()") == 1, "payload accessor count changed")
    _assert("if attribution_collector is not None:" in play_source, "diagnostic reads lack default-off guard")
    _assert("assignment={_tensor_list(assignment)}" in play_source, "existing aggregate console schema changed")
    _assert("pop_events(" not in module_source, "collector contains an event-drain dependency")
    _assert("assignment_playback_attribution_diagnostics" not in (
        REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py"
    ).read_text(encoding="utf-8"), "training path imports playback diagnostics")
    return {"case": "playback_static_architecture", "passed": True}


def run_smoke() -> dict[str, Any]:
    cases = [
        _case_cli_default_off_and_collisions(),
        _case_snapshot_and_controller_no_alias(),
        _case_idle_noop_initial_reset_boundary(),
        _case_active_sequence_completion_and_segments(),
        _case_exact_conflict_projection(),
        _case_owned_target_rejection(),
        _case_covered_and_unavailable_rejections(),
        _case_budget_release_and_failed_pair_reclaim(),
        _case_done_reset_alignment_and_null_post(),
        _case_multi_env_subset_reset_and_unprojected_event(),
        _case_jain_and_open_segment_finalize(),
        _case_invariant_break(),
        _case_input_nonmutation_and_copy_results(),
        _case_output_files_and_idempotent_finalize(),
        _case_compact_format(),
        _case_playback_static_architecture(),
    ]
    return {
        "status": "passed",
        "num_cases": len(cases),
        "cases": cases,
        "notes": [
            "pure fake playback attribution regression only",
            "no Isaac Lab or AppLauncher import",
            "no checkpoint, playback, evaluation, or training",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Assignment playback attribution diagnostics passed: {result['num_cases']} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
