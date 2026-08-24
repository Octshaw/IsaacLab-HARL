"""Bounded real-Isaac B1W-I2 admitted reset/claim/nonterminal-step smoke.

The public invocation is a supervisor.  It launches exactly one worker,
streams every flushed diagnostic line, enforces a finite timeout, and recovers
the worker's pre-shutdown JSON artifact if SimulationApp.close() exits Python.
This file is evidence-only and is not a production runtime entry point.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any


_STARTED_AT = time.monotonic()
_EXPECTED_STAGES = tuple(f"S{index}" for index in range(15))
_STAGES_REACHED: list[str] = []
_STAGE_EVIDENCE: dict[str, dict[str, object]] = {}
_WORKER_RESULT_PREFIX = "__B1W_I2_WORKER_RESULT__"


class SmokeEvidenceError(RuntimeError):
    """Typed smoke-only failure carrying the required phase classification."""

    def __init__(self, message: str, *, classification: str, failure_code: str) -> None:
        self.classification = classification
        self.failure_code = failure_code
        super().__init__(
            f"{message}; classification={classification!r}; failure_code={failure_code!r}"
        )


def _jsonable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "detach") and hasattr(value, "cpu") and hasattr(value, "tolist"):
        return value.detach().cpu().tolist()  # type: ignore[union-attr]
    if hasattr(value, "value"):
        return _jsonable(value.value)  # type: ignore[union-attr]
    return str(value)


def _print_record(stage: str, message: str, **evidence: object) -> None:
    payload = {
        "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
        "message": message,
        "pid": os.getpid(),
        "stage": stage,
    }
    payload.update({key: _jsonable(value) for key, value in evidence.items()})
    print(json.dumps(payload, sort_keys=True, default=str), flush=True)


def _diagnostic(stage: str, message: str, **evidence: object) -> None:
    _print_record(stage, message, **evidence)


def _stage(stage: str, message: str, **evidence: object) -> None:
    expected = _EXPECTED_STAGES[len(_STAGES_REACHED)] if len(_STAGES_REACHED) < 15 else None
    if stage != expected:
        raise SmokeEvidenceError(
            "runtime stage order diverged from S0-S14",
            classification="PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP",
            failure_code="stage_order",
        )
    payload = {key: _jsonable(value) for key, value in evidence.items()}
    _STAGES_REACHED.append(stage)
    _STAGE_EVIDENCE[stage] = payload
    _print_record(stage, message, **payload)


def _require(
    condition: bool,
    message: str,
    *,
    classification: str = "PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP",
    failure_code: str = "evidence_mismatch",
) -> None:
    if not condition:
        raise SmokeEvidenceError(
            message,
            classification=classification,
            failure_code=failure_code,
        )


def _tensor_values(value: object) -> list[object]:
    return value.detach().cpu().tolist()  # type: ignore[union-attr]


def _profile_label(profile: object) -> str:
    value = getattr(profile, "profile_name", None)
    return str(getattr(value, "value", value))


def _publication_evidence(publication: object) -> dict[str, object]:
    state = publication.lifecycle_state  # type: ignore[attr-defined]
    return {
        "episode_generation": _tensor_values(publication.episode_generation),  # type: ignore[attr-defined]
        "provenance": [item.kind.value for item in publication.provenance],  # type: ignore[attr-defined]
        "publication_serial": publication.publication_identity.serial,  # type: ignore[attr-defined]
        "robot_state": _tensor_values(state.robot_state),
        "store_version": publication.store_version,  # type: ignore[attr-defined]
        "task_state": _tensor_values(state.task_state),
        "terminated": _tensor_values(publication.terminated),  # type: ignore[attr-defined]
        "termination_reason": _tensor_values(state.termination_reason),
        "transition_generation": _tensor_values(publication.transition_generation),  # type: ignore[attr-defined]
        "truncated": _tensor_values(publication.truncated),  # type: ignore[attr-defined]
        "ownership": _tensor_values(state.ownership),
    }


def _assert_generations(
    publication: object,
    *,
    episode: int,
    transition: int,
    result_present: bool,
) -> None:
    _require(
        all(value == episode for value in _tensor_values(publication.episode_generation)),  # type: ignore[attr-defined]
        "unexpected episode generation",
        failure_code="episode_generation",
    )
    _require(
        all(value == transition for value in _tensor_values(publication.transition_generation)),  # type: ignore[attr-defined]
        "unexpected transition generation",
        failure_code="transition_generation",
    )
    _require(
        (publication.result is not None) is result_present,  # type: ignore[attr-defined]
        "unexpected lifecycle result presence",
        failure_code="result_presence",
    )


def _assert_all_nonterminal(returned: object) -> tuple[list[bool], list[bool]]:
    _require(type(returned) is tuple and len(returned) == 5, "DirectMARLEnv step did not return five values")
    terminated_by_agent = returned[2]  # type: ignore[index]
    truncated_by_agent = returned[3]  # type: ignore[index]
    _require(type(terminated_by_agent) is dict, "terminated result is not an exact dict")
    _require(type(truncated_by_agent) is dict, "truncated result is not an exact dict")
    terminated_vectors = [_tensor_values(value) for value in terminated_by_agent.values()]
    truncated_vectors = [_tensor_values(value) for value in truncated_by_agent.values()]
    _require(
        all(not any(bool(item) for item in vector) for vector in terminated_vectors)
        and all(not any(bool(item) for item in vector) for vector in truncated_vectors),
        "primary physical step was terminal or truncated",
        classification="PHASE-B1W-I2-STOP-NONTERMINAL-FIXTURE-GAP",
        failure_code="nonterminal_fixture_invalid",
    )
    return (
        [bool(value) for value in next(iter(terminated_vectors), [])],
        [bool(value) for value in next(iter(truncated_vectors), [])],
    )


def _artifact_snapshot(artifact: object) -> dict[str, object]:
    return {
        "committed_store_version": artifact.committed_store_version,  # type: ignore[attr-defined]
        "effective_task_by_robot": _tensor_values(artifact.effective_task_by_robot),  # type: ignore[attr-defined]
        "episode_generation": _tensor_values(artifact.episode_generation),  # type: ignore[attr-defined]
        "post_state": {key: _tensor_values(value) for key, value in artifact.post_state.items()},  # type: ignore[attr-defined]
        "pre_state": {key: _tensor_values(value) for key, value in artifact.pre_state.items()},  # type: ignore[attr-defined]
        "requested_task_by_robot": _tensor_values(artifact.requested_task_by_robot),  # type: ignore[attr-defined]
        "selected_env_ids": _tensor_values(artifact.selected_env_ids),  # type: ignore[attr-defined]
        "source_store_version": artifact.source_store_version,  # type: ignore[attr-defined]
        "token": artifact.token,  # type: ignore[attr-defined]
        "transition_generation": _tensor_values(artifact.transition_generation),  # type: ignore[attr-defined]
    }


def _select_fixture_claims(
    *,
    current: object,
    raw_env: object,
    torch: Any,
) -> tuple[object, object, list[dict[str, object]]]:
    """Choose farthest feasible legal pairs as TEST-FIXTURE SELECTION ONLY."""

    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
        TaskLifecycleState,
    )

    state = current.lifecycle_state
    problem = raw_env.get_assignment_problem()
    selected_env_ids: list[int] = []
    requested_rows: list[list[int]] = []
    pairs: list[dict[str, object]] = []
    num_envs = int(state.task_state.shape[0])
    num_robots = int(state.robot_state.shape[1])
    num_tasks = int(state.task_state.shape[1])
    for row in range(num_envs):
        chosen: tuple[int, int, float] | None = None
        for robot_id in range(num_robots):
            if int(state.robot_state[row, robot_id].item()) != int(
                RobotLifecycleState.NEEDS_ASSIGNMENT
            ):
                continue
            if bool((state.ownership[row] == robot_id).any().item()):
                continue
            candidates: list[tuple[float, int]] = []
            for task_id in range(num_tasks):
                legal = (
                    int(state.task_state[row, task_id].item())
                    == int(TaskLifecycleState.AVAILABLE)
                    and int(state.ownership[row, task_id].item()) == -1
                    and not bool(state.cumulative_failed_pairs[row, robot_id, task_id].item())
                    and bool(problem["available_mask"][row, robot_id, task_id].item())
                )
                if legal:
                    candidates.append((float(problem["cost_matrix"][row, robot_id, task_id].item()), task_id))
            if candidates:
                distance, task_id = max(candidates, key=lambda item: (item[0], -item[1]))
                chosen = (robot_id, task_id, distance)
                break
        if chosen is None:
            continue
        robot_id, task_id, distance = chosen
        request = [-1] * num_robots
        request[robot_id] = task_id
        selected_env_ids.append(int(current.env_id[row].item()))
        requested_rows.append(request)
        pairs.append(
            {
                "distance": distance,
                "env_id": int(current.env_id[row].item()),
                "robot_id": robot_id,
                "selection_rule": "TEST-FIXTURE ONLY: lowest legal robot, farthest feasible legal task",
                "task_id": task_id,
            }
        )
    _require(
        bool(selected_env_ids),
        "no legal deterministic claim pair exists in the real reset state",
        classification="PHASE-B1W-I2-STOP-SMOKE-FIXTURE-LEGAL-CLAIM-GAP",
        failure_code="legal_claim_gap",
    )
    device = state.task_state.device
    return (
        torch.tensor(selected_env_ids, dtype=torch.int64, device=device),
        torch.tensor(requested_rows, dtype=torch.int64, device=device),
        pairs,
    )


def _expected_controller_assignment(publication: object, torch: Any) -> object:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        TaskLifecycleState,
    )

    state = publication.lifecycle_state
    num_envs, num_tasks = state.task_state.shape
    num_robots = int(state.robot_state.shape[1])
    assignment = torch.full(
        (num_envs, num_robots),
        -1,
        dtype=torch.int64,
        device=state.task_state.device,
    )
    active_values = {
        int(TaskLifecycleState.CLAIMED),
        int(TaskLifecycleState.NAVIGATING),
        int(TaskLifecycleState.ALIGNING),
    }
    for env_row in range(num_envs):
        for task_id in range(num_tasks):
            if int(state.task_state[env_row, task_id].item()) in active_values:
                robot_id = int(state.ownership[env_row, task_id].item())
                _require(robot_id >= 0, "active task lacks ownership", failure_code="control_source")
                _require(
                    int(assignment[env_row, robot_id].item()) == -1,
                    "one robot owns multiple active tasks",
                    classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP",
                    failure_code="control_multi_owner",
                )
                assignment[env_row, robot_id] = task_id
    return assignment


def _run_real_smoke(*, num_envs: int) -> dict[str, object]:
    _diagnostic("L2", "before real environment imports")
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_synchronous_runtime import (
        EventProfileSynchronousRuntimeCoordinator,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_interstep_claim_window_runtime import (
        _ClaimWindowFencePhase,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
        TaskLifecycleState,
        TerminationReason,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
        AssignmentProfileName,
        AssignmentProfileResolutionOrigin,
        resolve_assignment_profile,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import (
        assignment_to_env_actions,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import (
        ScanMobileManipulatorEnvCfg,
    )

    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = num_envs
    device = torch.device(cfg.sim.device)
    num_robots = len(cfg.possible_agents)
    num_tasks = len(cfg.viewpoint_poses)
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(num_envs, dtype=torch.int64, device=device),
            num_robots=num_robots,
            num_tasks=num_tasks,
        )
    )
    prebootstrap = domain.current_read_port.read_current()
    fence0 = domain.interstep_fence_read_port.read()
    _require(fence0.phase is _ClaimWindowFencePhase.PREBOOTSTRAP_CLOSED, "initial fence is not closed")
    _require(fence0.window is None and fence0.active_step is None and fence0.active_reset is None, "initial fence carries an identity")
    _assert_generations(prebootstrap, episode=-1, transition=-1, result_present=False)
    _require(
        all(item.kind.value == "prebootstrap" for item in prebootstrap.provenance),
        "initial P2 provenance is not PREBOOTSTRAP",
    )

    _diagnostic("L3", "before exact event environment construction", num_envs=num_envs)
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw_env = env.unwrapped
    context: dict[str, object] = {
        "domain": domain,
        "fence_phase": _ClaimWindowFencePhase,
        "observer_error": None,
        "observer_traceback": None,
        "torch": torch,
    }

    def observer(stage_name: str, detail: object | None) -> None:
        if context["observer_error"] is not None:
            return
        try:
            fence = domain.interstep_fence_read_port.read()
            if stage_name == "S0_COORDINATOR_READY":
                return
            if stage_name == "S1_RESET_ADMISSION_BEGUN":
                _require(fence.phase is _ClaimWindowFencePhase.RESET_IN_FLIGHT, "R1 did not enter RESET_IN_FLIGHT")
                _require(fence.active_reset is detail and fence.window is None, "R1 is not the exact active reset")
                context["reset_admission"] = detail
                _stage(
                    "S1",
                    "RESET_ADMISSION_BEGIN",
                    admission_serial=detail.identity.serial,  # type: ignore[union-attr]
                    fence_phase=fence.phase.value,
                    open_window=False,
                )
            elif stage_name == "S3_ENV_RESET_RETURNED":
                _require(fence.active_reset is context.get("reset_admission"), "reset returned under a foreign R1")
                _require(domain._interstep_fence._reset_entry_validated, "real reset did not consume the R1 entry latch")
                _stage("S2", "RESET_ENTRY_VALIDATED", mode="VERIFIED_POST_RETURN")
                _stage("S3", "ENV_RESET_RETURNED", tuple_length=len(detail))  # type: ignore[arg-type]
            elif stage_name == "S4_WINDOW_OPEN":
                _require(fence.phase is _ClaimWindowFencePhase.OPEN and fence.window is detail, "R1 completion did not open exact W1")
                reset_view = domain.current_read_port.read_current()
                _assert_generations(reset_view, episode=0, transition=-1, result_present=False)
                _require(all(item.kind.value == "canonical_episode_reset" for item in reset_view.provenance), "reset P2 provenance is not canonical")
                _require(all(int(value) == int(TerminationReason.NONE) for value in reset_view.lifecycle_state.termination_reason.tolist()), "reset termination reason is not NONE")
                context["w1"] = detail
                context["reset_view"] = reset_view
                _stage("S4", "WINDOW_W1_OPEN", window_serial=detail.serial, publication=_publication_evidence(reset_view))  # type: ignore[union-attr]
            elif stage_name == "S5_DETERMINISTIC_CLAIM_COMMITTED":
                _require(fence.phase is _ClaimWindowFencePhase.OPEN and fence.window is context.get("w1"), "claim changed W1 identity")
                context["artifact"] = detail
                _stage(
                    "S5",
                    "DETERMINISTIC_CLAIM_COMMITTED",
                    claim_pairs=context["claim_pairs"],
                    committed_store_version=detail.committed_store_version,  # type: ignore[union-attr]
                    source_store_version=detail.source_store_version,  # type: ignore[union-attr]
                    window_serial=fence.window.serial,  # type: ignore[union-attr]
                )
            elif stage_name == "S6_FINAL_P2_SEEN" and "S6" not in _STAGES_REACHED:
                post_claim = domain.current_read_port.read_current()
                _require(post_claim is detail, "S6 did not expose the authoritative current P2")
                selected = {pair["env_id"] for pair in context["claim_pairs"]}  # type: ignore[union-attr]
                for row, env_value in enumerate(_tensor_values(post_claim.env_id)):
                    if env_value in selected:
                        _require(post_claim.provenance[row].kind.value == "assignment_commit", "selected row lacks assignment provenance")
                context["post_claim"] = post_claim
                context["expected_assignment"] = _expected_controller_assignment(post_claim, torch)
                _stage("S6", "POST_CLAIM_P2_VERIFIED", publication=_publication_evidence(post_claim), window_serial=fence.window.serial)  # type: ignore[union-attr]
            elif stage_name == "S7_STEP_ADMISSION_REQUESTED":
                _require(fence.phase is _ClaimWindowFencePhase.OPEN and fence.window is context.get("w1"), "primary R3 did not begin from W1")
                _stage("S7", "STEP_ADMISSION_BEGIN", primary_r3="PASS", window_serial=fence.window.serial)  # type: ignore[union-attr]
            elif stage_name == "S8_AK_ACTIVE":
                post_claim = context["post_claim"]
                _require(fence.phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT and fence.active_step is detail, "Ak is not exact active step")
                _require(detail.source_window is context.get("w1"), "Ak did not close W1")  # type: ignore[union-attr]
                _require(detail.admitted_publication is post_claim, "Ak did not bind post-claim P2")  # type: ignore[union-attr]
                _require(detail.admitted_store_version == post_claim.store_version, "Ak Store version mismatch")  # type: ignore[union-attr,attr-defined]
                context["admission"] = detail
                _stage(
                    "S8",
                    "AK_ACTIVE",
                    admission_serial=detail.identity.serial,  # type: ignore[union-attr]
                    admitted_publication_serial=detail.admitted_publication_identity.serial,  # type: ignore[union-attr]
                    admitted_store_version=detail.admitted_store_version,  # type: ignore[union-attr]
                    source_window_serial=detail.source_window.serial,  # type: ignore[union-attr]
                )
            elif stage_name == "S9_CONTROL_ACTION_BUILT":
                assignment = context.get("action_assignment")
                expected = context.get("expected_assignment")
                _require(torch.equal(detail, assignment) and torch.equal(detail, expected), "O1 control assignment differs from Ak ownership", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="control_source_mismatch")
                _stage("S9", "AK_BOUND_CONTROL_BUILT", assignment=_tensor_values(detail), action=context["action_evidence"])  # type: ignore[arg-type]
            elif stage_name == "S12_ENV_STEP_RETURNED":
                _require(domain._interstep_fence._step_entry_validated, "real event hook did not consume exact Ak entry latch", classification="PHASE-B1W-I2-STOP-REAL-AK-ENTRY-GAP", failure_code="ak_entry_latch")
                _require(domain._interstep_fence._step_finalization_validated, "real I3 did not consume exact Ak finalization latch", classification="PHASE-B1W-I2-STOP-REAL-I3-ADMISSION-GAP", failure_code="i3_latch")
                terminated, truncated = _assert_all_nonterminal(detail)
                final_view = domain.current_read_port.read_current()
                _assert_generations(final_view, episode=0, transition=0, result_present=True)
                _require(all(item.kind.value == "finalized_lifecycle_transition" for item in final_view.provenance), "final P2 provenance is not lifecycle finalization")
                _require(not any(_tensor_values(final_view.terminated)) and not any(_tensor_values(final_view.truncated)), "final P2 is terminal")
                _require(all(int(value) == int(TerminationReason.NONE) for value in final_view.lifecycle_state.termination_reason.tolist()), "final termination reason is not NONE")
                result = final_view.result
                context["step_return"] = detail
                context["terminated"] = terminated
                context["truncated"] = truncated
                context["final_view"] = final_view
                context["lifecycle_events"] = [type(event).__name__ for event in result.lifecycle_events]
                context["completed_tasks"] = _tensor_values(result.completed_tasks)
                _stage("S10", "ENV_AK_ENTRY_VALIDATED", mode="VERIFIED_POST_RETURN")
                _stage("S11", "I3_SAME_AK_VALIDATED", mode="VERIFIED_POST_RETURN", completed_tasks=context["completed_tasks"], lifecycle_event_types=context["lifecycle_events"])
                _stage("S12", "ENV_STEP_RETURNED", tuple_length=len(detail), terminated=terminated, truncated=truncated)
            elif stage_name == "S13_AK_COMPLETED":
                _require(detail is context.get("admission"), "O1 completed a foreign Ak")
                _require(fence.phase is _ClaimWindowFencePhase.OPEN, "Ak completion did not reopen the fence")
                context["w2"] = fence.window
                _stage("S13", "AK_SUCCESS_COMPLETED", admission_serial=detail.identity.serial)  # type: ignore[union-attr]
            elif stage_name == "S14_WINDOW_OPEN":
                _require(detail is context.get("w2") and detail is not context.get("w1"), "W2 identity is not new")
                _stage("S14", "WINDOW_W2_OPEN", window_serial=detail.serial)  # type: ignore[union-attr]
            elif stage_name.startswith("F_"):
                _diagnostic(stage_name, "O1 failure observation", error=f"{type(detail).__name__}: {detail}")
        except BaseException as exc:
            context["observer_error"] = exc
            context["observer_traceback"] = traceback.format_exc()
            _diagnostic("OBSERVER_FAILURE", "stage observer validation failed", error=f"{type(exc).__name__}: {exc}", observed_stage=stage_name)

    coordinator = EventProfileSynchronousRuntimeCoordinator(
        environment=raw_env,
        current_read_port=domain.current_read_port,
        production_claim_port=domain.production_claim_port,
        physical_step_admission_port=domain.physical_step_admission_port,
        standalone_reset_admission_port=domain.standalone_reset_admission_port,
        terminal_consumer_port=domain.terminal_consumer_port,
        fence_read_port=domain.interstep_fence_read_port,
        stage_observer=observer,
    )
    _require(raw_env._event_lifecycle_environment_port is domain.environment_port, "environment retained a foreign lifecycle port")
    _require(raw_env._event_admission_validation_port is domain.environment_admission_validation_port, "environment retained a foreign validation port")
    _stage(
        "S0",
        "COMPOSITION_READY",
        device=str(device),
        domain_identity=id(domain.current_read_port.domain_identity),
        fence_identity=id(domain._interstep_fence),
        fence_phase=fence0.phase.value,
        num_envs=num_envs,
        num_robots=num_robots,
        num_tasks=num_tasks,
        o1_identity=id(coordinator),
        prebootstrap=_publication_evidence(prebootstrap),
        profile=_profile_label(profile),
    )

    try:
        reset_return = coordinator.reset_environment()
        if context["observer_error"] is not None:
            print(str(context["observer_traceback"]), file=sys.stderr, flush=True)
            raise context["observer_error"]  # type: ignore[misc]
        _require(_STAGES_REACHED == list(_EXPECTED_STAGES[:5]), "reset did not reach S4")
        _require(type(reset_return) is tuple and len(reset_return) == 2, "real reset did not return observation/extras")

        reset_view = context["reset_view"]
        domain.environment_port.assert_physical_step_allowed()
        selected_env_ids, requested, claim_pairs = _select_fixture_claims(
            current=reset_view,
            raw_env=raw_env,
            torch=torch,
        )
        context["claim_pairs"] = claim_pairs
        w1_before_claim = domain.interstep_fence_read_port.read().window
        artifact = coordinator.commit_deterministic_initial_claim(
            selected_env_ids=selected_env_ids,
            requested_task_by_robot=requested,
        )
        if context["observer_error"] is not None:
            print(str(context["observer_traceback"]), file=sys.stderr, flush=True)
            raise context["observer_error"]  # type: ignore[misc]
        _require(_STAGES_REACHED == list(_EXPECTED_STAGES[:7]), "claim did not reach S6")
        post_claim = context["post_claim"]
        _require(artifact.committed_store_version == reset_view.store_version + 1, "claim did not advance Store exactly once")  # type: ignore[union-attr]
        _require(post_claim.store_version == artifact.committed_store_version, "post-claim P2 Store version mismatch")  # type: ignore[union-attr]
        _require(domain.interstep_fence_read_port.read().window is w1_before_claim is context["w1"], "claim replaced W1")
        historical_snapshot = _artifact_snapshot(artifact)

        domain.environment_port.assert_physical_step_allowed()

        def action_builder(environment: object, assignment: object) -> object:
            _require(environment is raw_env, "O1 action builder received a foreign environment")
            expected = context["expected_assignment"]
            _require(torch.equal(assignment, expected), "action builder source differs from Ak P2", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="action_builder_source")
            actions = assignment_to_env_actions(environment, assignment)
            _require(type(actions) is dict and set(actions) == set(raw_env.cfg.possible_agents), "controller action mapping keys mismatch", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="action_keys")
            action_evidence: dict[str, object] = {}
            for agent, action in actions.items():
                _require(tuple(action.shape) == (num_envs, raw_env.cfg.action_spaces[agent]), "controller action shape mismatch", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="action_shape")
                _require(action.device == device, "controller action device mismatch", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="action_device")
                _require(bool(torch.isfinite(action).all().item()), "controller action contains NaN or Inf", classification="PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP", failure_code="action_finite")
                action_evidence[agent] = {"device": str(action.device), "finite": True, "shape": list(action.shape)}
            context["action_assignment"] = assignment.detach().clone().contiguous()
            context["action_evidence"] = action_evidence
            return actions

        returned = coordinator.step_environment(action_builder=action_builder)
        if context["observer_error"] is not None:
            print(str(context["observer_traceback"]), file=sys.stderr, flush=True)
            raise context["observer_error"]  # type: ignore[misc]
        _require(_STAGES_REACHED == list(_EXPECTED_STAGES), "real step did not reach S14")
        _require(returned is context["step_return"], "O1 changed the external step return")
        domain.environment_port.assert_physical_step_allowed()
        final_fence = domain.interstep_fence_read_port.read()
        _require(final_fence.phase is _ClaimWindowFencePhase.OPEN and final_fence.window is context["w2"], "final fence is not OPEN W2")
        _require(not domain._coordinator.poisoned and final_fence.phase is not _ClaimWindowFencePhase.FAULTED, "runtime poisoned during successful smoke")
        _require(_artifact_snapshot(artifact) == historical_snapshot, "historical assignment artifact mutated after I3")
        final_view = context["final_view"]
        return {
            "action": context["action_evidence"],
            "ak_assignment": _tensor_values(context["action_assignment"]),
            "app_launcher_initialized": True,
            "claim_artifact_immutable": True,
            "claim_pairs": claim_pairs,
            "device": str(device),
            "domain_count": 1,
            "domain_identity": id(domain.current_read_port.domain_identity),
            "environment_type": type(raw_env).__name__,
            "final_publication": _publication_evidence(final_view),
            "lifecycle_event_types": context["lifecycle_events"],
            "completed_tasks": context["completed_tasks"],
            "num_envs": num_envs,
            "num_robots": num_robots,
            "num_tasks": num_tasks,
            "o1_count": 1,
            "poisoned": False,
            "post_claim_publication": _publication_evidence(post_claim),
            "profile": _profile_label(profile),
            "reset_publication": _publication_evidence(reset_view),
            "stages_reached": list(_STAGES_REACHED),
            "terminal_slot_occupancy": "none (fresh-domain plus R3 guard passed before and after step)",
            "terminated": context["terminated"],
            "truncated": context["truncated"],
            "w1_serial": context["w1"].serial,  # type: ignore[union-attr]
            "w2_serial": context["w2"].serial,  # type: ignore[union-attr]
        }
    finally:
        env.close()


def _failure_classification(exc: BaseException) -> str:
    explicit = getattr(exc, "classification", None)
    if isinstance(explicit, str):
        return explicit
    stage = getattr(exc, "stage", "")
    if "reset" in str(stage) or _STAGES_REACHED == ["S0", "S1"]:
        return "PHASE-B1W-I2-STOP-REAL-RESET-ADMISSION-GAP"
    if "control" in str(stage) or (_STAGES_REACHED and _STAGES_REACHED[-1] == "S8"):
        return "PHASE-B1W-I2-STOP-REAL-CONTROL-SOURCE-GAP"
    if "physical_step_entry" in str(stage):
        return "PHASE-B1W-I2-STOP-REAL-AK-ENTRY-GAP"
    if "finalization" in str(stage) or "i3" in str(stage).lower():
        return "PHASE-B1W-I2-STOP-REAL-I3-ADMISSION-GAP"
    return "PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP"


def _write_result(path: str | None, result: dict[str, object]) -> None:
    if path is None:
        return
    target = Path(path)
    target.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _run_worker(args: argparse.Namespace) -> int:
    _diagnostic("L0", "smoke worker entered", python=sys.executable)
    simulation_app = None
    result: dict[str, object]
    exit_code = 1
    try:
        _diagnostic("L1", "before AppLauncher construction", headless=True)
        from isaaclab.app import AppLauncher

        launcher = AppLauncher(headless=True)
        simulation_app = launcher.app
        _diagnostic("L1_PASS", "AppLauncher initialized successfully", headless=True)
        evidence = _run_real_smoke(num_envs=args.num_envs)
        result = {
            "classification": "PHASE-B1W-I2-FOCUSED-REAL-ISAAC-NONTERMINAL-SMOKE-PASS-AWAITING-GPT-REVIEW",
            "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
            "evidence": evidence,
            "last_stage": _STAGES_REACHED[-1] if _STAGES_REACHED else None,
            "pid": os.getpid(),
            "stage_evidence": _STAGE_EVIDENCE,
            "status": "passed",
        }
        exit_code = 0
    except BaseException as exc:
        trace = traceback.format_exc()
        print(trace, file=sys.stderr, flush=True)
        result = {
            "classification": _failure_classification(exc),
            "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "failure_code": getattr(exc, "failure_code", None),
            "last_stage": _STAGES_REACHED[-1] if _STAGES_REACHED else None,
            "pid": os.getpid(),
            "stage_evidence": _STAGE_EVIDENCE,
            "stages_reached": list(_STAGES_REACHED),
            "status": "failed",
            "traceback": trace,
        }
    finally:
        _write_result(args.result_file, result)
        print(_WORKER_RESULT_PREFIX + json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)
        _diagnostic("L4", "before SimulationApp shutdown")
        if simulation_app is not None:
            try:
                simulation_app.close()
            except BaseException as close_exc:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                result = {
                    "classification": "PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP",
                    "error": f"shutdown {type(close_exc).__name__}: {close_exc}",
                    "last_stage": _STAGES_REACHED[-1] if _STAGES_REACHED else None,
                    "status": "failed",
                }
                _write_result(args.result_file, result)
                exit_code = 1
    return exit_code


def _reader(pipe: Any, lines: queue.Queue[str | None]) -> None:
    try:
        for line in pipe:
            lines.put(line)
    finally:
        lines.put(None)


def _terminate_worker_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    elif process.poll() is None:
        process.kill()


def _run_supervisor(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="b1w_i2_smoke_") as temp_dir:
        result_path = os.path.join(temp_dir, "result.json")
        command = [
            sys.executable,
            "-u",
            os.path.abspath(__file__),
            "--num-envs",
            str(args.num_envs),
            "--result-file",
            result_path,
            "--worker",
        ]
        _diagnostic("SUPERVISOR", "launching exactly one bounded worker", command=command, timeout_seconds=args.timeout_seconds)
        process = subprocess.Popen(
            command,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        lines: queue.Queue[str | None] = queue.Queue()
        reader = threading.Thread(target=_reader, args=(process.stdout, lines), daemon=True)
        reader.start()
        deadline = time.monotonic() + args.timeout_seconds
        worker_result: dict[str, object] | None = None
        reader_done = False
        timed_out = False
        while not reader_done or process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0 and process.poll() is None:
                timed_out = True
                _diagnostic("SUPERVISOR_TIMEOUT", "worker exceeded finite timeout", child_pid=process.pid)
                _terminate_worker_tree(process)
                break
            try:
                line = lines.get(timeout=min(0.25, max(0.01, remaining)))
            except queue.Empty:
                continue
            if line is None:
                reader_done = True
            elif line.startswith(_WORKER_RESULT_PREFIX):
                worker_result = json.loads(line[len(_WORKER_RESULT_PREFIX) :])
            else:
                print(line, end="", flush=True)
        try:
            child_exit_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_worker_tree(process)
            child_exit_code = process.wait(timeout=15)
        reader.join(timeout=5)
        while True:
            try:
                line = lines.get_nowait()
            except queue.Empty:
                break
            if line is None:
                continue
            if line.startswith(_WORKER_RESULT_PREFIX):
                worker_result = json.loads(line[len(_WORKER_RESULT_PREFIX) :])
            else:
                print(line, end="", flush=True)
        if os.path.isfile(result_path):
            worker_result = json.loads(Path(result_path).read_text(encoding="utf-8"))
        if timed_out:
            result: dict[str, object] = {
                "child_exit_code": child_exit_code,
                "classification": "PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP",
                "error": "bounded worker timeout",
                "last_stage": None if worker_result is None else worker_result.get("last_stage"),
                "status": "failed",
                "timeout": True,
            }
        elif worker_result is None:
            result = {
                "child_exit_code": child_exit_code,
                "classification": "PHASE-B1W-I2-STOP-REAL-RUNTIME-INTEGRATION-GAP",
                "error": "worker exited without a result artifact",
                "status": "failed",
            }
        else:
            result = dict(worker_result)
            result["child_exit_code"] = child_exit_code
            result["shutdown_observed"] = child_exit_code == 0
            result["timeout"] = False
            if child_exit_code != 0:
                result["status"] = "failed"
                result["shutdown_error"] = f"worker exit code {child_exit_code}"
        _diagnostic("SUPERVISOR_EXIT", "worker tree exited", child_exit_code=child_exit_code, child_pid=process.pid, timed_out=timed_out)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(result, indent=2, sort_keys=True), flush=True)
        return 0 if result.get("status") == "passed" and child_exit_code == 0 else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--result-file", help=argparse.SUPPRESS)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.num_envs <= 0:
        parser.error("--num-envs must be positive")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.worker and not args.result_file:
        parser.error("worker requires --result-file")
    return args


def main() -> int:
    args = _parse_args()
    return _run_worker(args) if args.worker else _run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
