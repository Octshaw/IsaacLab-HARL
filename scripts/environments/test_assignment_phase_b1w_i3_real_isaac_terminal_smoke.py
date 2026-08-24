"""Bounded real-Isaac B1W-I3 terminal capture/ack/recovery smoke.

The public process is a supervisor. It launches exactly one worker, streams
flushed stage evidence, enforces a finite timeout, and recovers a temporary
pre-shutdown result artifact. This is evidence-only, never a production entry.
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
_EXPECTED_STAGES = ("T0", "T1", "T2", "T3", "T4", "T5", "T6", "T6B", "T7", "T8", "T9")
_STAGES_REACHED: list[str] = []
_STAGE_EVIDENCE: dict[str, dict[str, object]] = {}
_WORKER_RESULT_PREFIX = "__B1W_I3_WORKER_RESULT__"


class SmokeEvidenceError(RuntimeError):
    def __init__(self, message: str, *, classification: str, failure_code: str) -> None:
        self.classification = classification
        self.failure_code = failure_code
        super().__init__(f"{message}; classification={classification!r}; failure_code={failure_code!r}")


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


def _record(stage: str, message: str, **evidence: object) -> None:
    payload = {
        "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
        "message": message,
        "pid": os.getpid(),
        "stage": stage,
    }
    payload.update({key: _jsonable(value) for key, value in evidence.items()})
    print(json.dumps(payload, sort_keys=True, default=str), flush=True)


def _stage(stage: str, message: str, **evidence: object) -> None:
    expected = _EXPECTED_STAGES[len(_STAGES_REACHED)] if len(_STAGES_REACHED) < len(_EXPECTED_STAGES) else None
    if stage != expected:
        raise SmokeEvidenceError(
            "terminal smoke stage order diverged",
            classification="PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP",
            failure_code="stage_order",
        )
    payload = {key: _jsonable(value) for key, value in evidence.items()}
    _STAGES_REACHED.append(stage)
    _STAGE_EVIDENCE[stage] = payload
    _record(stage, message, **payload)


def _diagnostic(stage: str, message: str, **evidence: object) -> None:
    _record(stage, message, **evidence)


def _require(
    condition: bool,
    message: str,
    *,
    classification: str = "PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP",
    failure_code: str = "evidence_mismatch",
) -> None:
    if not condition:
        raise SmokeEvidenceError(message, classification=classification, failure_code=failure_code)


def _values(value: object) -> list[object]:
    return value.detach().cpu().tolist()  # type: ignore[union-attr]


def _publication(publication: object) -> dict[str, object]:
    state = publication.lifecycle_state  # type: ignore[attr-defined]
    return {
        "episode_generation": _values(publication.episode_generation),  # type: ignore[attr-defined]
        "ownership": _values(state.ownership),
        "publication_serial": publication.publication_identity.serial,  # type: ignore[attr-defined]
        "result_present": publication.result is not None,  # type: ignore[attr-defined]
        "robot_state": _values(state.robot_state),
        "store_version": publication.store_version,  # type: ignore[attr-defined]
        "task_state": _values(state.task_state),
        "terminated": _values(publication.terminated),  # type: ignore[attr-defined]
        "termination_reason": _values(state.termination_reason),
        "transition_generation": _values(publication.transition_generation),  # type: ignore[attr-defined]
        "truncated": _values(publication.truncated),  # type: ignore[attr-defined]
    }


def _done_vectors(returned: object) -> tuple[list[bool], list[bool]]:
    _require(type(returned) is tuple and len(returned) == 5, "real step did not return five values")
    terminated_by_agent, truncated_by_agent = returned[2], returned[3]  # type: ignore[index]
    _require(type(terminated_by_agent) is dict and type(truncated_by_agent) is dict, "done outputs are not dictionaries")
    terminated = [[bool(item) for item in _values(value)] for value in terminated_by_agent.values()]
    truncated = [[bool(item) for item in _values(value)] for value in truncated_by_agent.values()]
    _require(all(vector == terminated[0] for vector in terminated[1:]), "agent terminated vectors differ")
    _require(all(vector == truncated[0] for vector in truncated[1:]), "agent truncated vectors differ")
    return terminated[0], truncated[0]


def _raw_snapshot(raw_env: object, torch: Any) -> dict[str, object]:
    return {
        "common_step_counter": int(raw_env.common_step_counter),
        "current_actions": {key: value.detach().clone() for key, value in raw_env.actions.items()},
        "dwell_counter": raw_env.dwell_counter.detach().clone(),
        "episode_length": raw_env.episode_length_buf.detach().clone(),
        "previous_actions": {key: value.detach().clone() for key, value in raw_env.previous_actions.items()},
        "viewpoints_covered": raw_env.viewpoints_covered.detach().clone(),
    }


def _same_raw_snapshot(left: dict[str, object], right: dict[str, object], torch: Any) -> bool:
    if left["common_step_counter"] != right["common_step_counter"]:
        return False
    for name in ("dwell_counter", "episode_length", "viewpoints_covered"):
        if not torch.equal(left[name], right[name]):
            return False
    for name in ("current_actions", "previous_actions"):
        left_map, right_map = left[name], right[name]
        if set(left_map) != set(right_map):
            return False
        if any(not torch.equal(left_map[key], right_map[key]) for key in left_map):
            return False
    return True


def _select_fixture_claim(current: object, raw_env: object, torch: Any) -> tuple[object, object, list[dict[str, object]]]:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
        TaskLifecycleState,
    )

    state = current.lifecycle_state
    problem = raw_env.get_assignment_problem()
    selected: list[int] = []
    requested: list[list[int]] = []
    evidence: list[dict[str, object]] = []
    num_envs, num_tasks = state.task_state.shape
    num_robots = int(state.robot_state.shape[1])
    for row in range(num_envs):
        chosen: tuple[int, int, float] | None = None
        for robot_id in range(num_robots):
            if int(state.robot_state[row, robot_id]) != int(RobotLifecycleState.NEEDS_ASSIGNMENT):
                continue
            candidates: list[tuple[float, int]] = []
            for task_id in range(num_tasks):
                legal = (
                    int(state.task_state[row, task_id]) == int(TaskLifecycleState.AVAILABLE)
                    and int(state.ownership[row, task_id]) == -1
                    and not bool(state.cumulative_failed_pairs[row, robot_id, task_id])
                    and bool(problem["available_mask"][row, robot_id, task_id])
                )
                if legal:
                    candidates.append((float(problem["cost_matrix"][row, robot_id, task_id]), task_id))
            if candidates:
                distance, task_id = max(candidates, key=lambda item: (item[0], -item[1]))
                chosen = (robot_id, task_id, distance)
                break
        if chosen is None:
            continue
        robot_id, task_id, distance = chosen
        row_request = [-1] * num_robots
        row_request[robot_id] = task_id
        selected.append(int(current.env_id[row]))
        requested.append(row_request)
        evidence.append({
            "distance": distance,
            "env_id": int(current.env_id[row]),
            "robot_id": robot_id,
            "selection_rule": "TEST FIXTURE ONLY: lowest legal robot, farthest feasible legal task",
            "task_id": task_id,
        })
    _require(
        bool(selected),
        "real reset state has no legal deterministic claim fixture",
        classification="PHASE-B1W-I3-STOP-TERMINAL-FIXTURE-GAP",
        failure_code="legal_claim_gap",
    )
    device = state.task_state.device
    return (
        torch.tensor(selected, dtype=torch.int64, device=device),
        torch.tensor(requested, dtype=torch.int64, device=device),
        evidence,
    )


def _action_builder(raw_env: object, torch: Any, assignment_to_env_actions: Any):
    def build(environment: object, assignment: object) -> object:
        _require(environment is raw_env, "O1 received a foreign environment")
        actions = assignment_to_env_actions(environment, assignment)
        _require(type(actions) is dict and set(actions) == set(raw_env.cfg.possible_agents), "action mapping mismatch")
        for action in actions.values():
            _require(bool(torch.isfinite(action).all()), "action contains NaN or Inf")
        return actions

    return build


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
        TerminationReason,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
        AssignmentProfileName,
        AssignmentProfileResolutionOrigin,
        resolve_assignment_profile,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import assignment_to_env_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = num_envs
    physical_step_seconds = float(cfg.sim.dt) * int(cfg.decimation)
    cfg.episode_length_s = physical_step_seconds * 4
    device = torch.device(cfg.sim.device)
    num_robots, num_tasks = len(cfg.possible_agents), len(cfg.viewpoint_poses)
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(num_envs, dtype=torch.int64, device=device),
            num_robots=num_robots,
            num_tasks=num_tasks,
        )
    )
    _diagnostic(
        "FIXTURE",
        "configured existing episode-length mechanism",
        episode_length_s=cfg.episode_length_s,
        physical_step_seconds=physical_step_seconds,
        rule="TEST FIXTURE ONLY: four configured physical-step periods; no production config file changed",
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw_env = env.unwrapped
    context: dict[str, object] = {"admissions": [], "returns": [], "observer_error": None}

    def observer(stage_name: str, detail: object | None) -> None:
        try:
            if stage_name == "S8_AK_ACTIVE":
                context["admissions"].append(detail)  # type: ignore[union-attr]
            elif stage_name == "S12_ENV_STEP_RETURNED":
                fence = domain.interstep_fence_read_port.read()
                context["returns"].append({  # type: ignore[union-attr]
                    "admission": fence.active_step,
                    "autoreset_latch": bool(domain._interstep_fence._internal_autoreset_entry_validated),
                    "entry_latch": bool(domain._interstep_fence._step_entry_validated),
                    "finalization_latch": bool(domain._interstep_fence._step_finalization_validated),
                    "publication": domain.current_read_port.read_current(),
                    "returned": detail,
                })
        except BaseException as exc:
            context["observer_error"] = exc
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

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
    action_builder = _action_builder(raw_env, torch, assignment_to_env_actions)
    physical_steps = 0
    try:
        reset_return = coordinator.reset_environment()
        _require(type(reset_return) is tuple and len(reset_return) == 2, "real reset did not return two values")
        reset_view = domain.current_read_port.read_current()
        selected, requested, claim_evidence = _select_fixture_claim(reset_view, raw_env, torch)
        coordinator.commit_deterministic_initial_claim(
            selected_env_ids=selected,
            requested_task_by_robot=requested,
        )

        terminal_return: object | None = None
        terminal_return_index = -1
        for index in range(8):
            returned = coordinator.step_environment(action_builder=action_builder)
            physical_steps += 1
            _require(context["observer_error"] is None, f"observer failed: {context['observer_error']}")
            terminated, truncated = _done_vectors(returned)
            any_done = any(terminated) or any(truncated)
            if any_done:
                _require(all(truncated) and not any(terminated), "fixture terminal is not an all-row time limit", classification="PHASE-B1W-I3-STOP-TERMINAL-FIXTURE-GAP", failure_code="terminal_kind")
                terminal_return = returned
                terminal_return_index = index
                break
            _require(coordinator.capture_pending_terminal_artifacts() == (), "nonterminal step created a slot")
        _require(terminal_return is not None, "bounded fixture did not produce a terminal", classification="PHASE-B1W-I3-STOP-TERMINAL-FIXTURE-GAP", failure_code="no_terminal")
        _require(physical_steps <= 32, "physical-step bound exceeded", classification="PHASE-B1W-I3-STOP-TERMINAL-FIXTURE-GAP", failure_code="step_bound")

        terminal_admission = context["admissions"][-1]  # type: ignore[index]
        terminal_observation = context["returns"][-1]  # type: ignore[index]
        fence_after_return = domain.interstep_fence_read_port.read()
        current_reset = domain.current_read_port.read_current()
        artifacts = coordinator.capture_pending_terminal_artifacts()
        _require(len(artifacts) == num_envs, "one exact slot per terminal row was not captured", classification="PHASE-B1W-I3-STOP-TERMINAL-SLOT-SURVIVAL-GAP", failure_code="slot_count")
        keys = [artifact.key for artifact in artifacts]
        _require([key.env_id for key in keys] == list(range(num_envs)), "captured slots are not env-id ordered")
        _require(fence_after_return.phase is _ClaimWindowFencePhase.OPEN and fence_after_return.active_step is None, "terminal Ak did not complete to OPEN")
        _require(terminal_observation["admission"] is terminal_admission, "autoreset/return lost exact Ak identity")
        _require(terminal_observation["entry_latch"] and terminal_observation["finalization_latch"], "terminal Ak validation latches missing")
        _require(terminal_observation["autoreset_latch"], "autoreset did not validate under the terminal Ak", classification="PHASE-B1W-I3-STOP-REAL-AUTORESET-AK-GAP", failure_code="autoreset_latch")
        _require(terminal_observation["publication"] is current_reset, "post-autoreset P2 changed before external return")
        _require(current_reset.result is None, "current P2 is not the reset publication")
        artifact_evidence: list[dict[str, object]] = []
        for artifact in artifacts:
            key = artifact.key
            _require(artifact.termination_reason == int(TerminationReason.TIME_LIMIT), "terminal artifact reason is not TIME_LIMIT")
            _require(artifact.truncated and not artifact.terminated, "terminal artifact done projection mismatch")
            _require(artifact.published_view.result is artifact.result, "artifact lost exact terminal result identity")
            _require(key.episode_generation + 1 == int(current_reset.episode_generation[key.env_id]), "terminal/reset episode separation mismatch")
            _require(key.transition_generation == int(current_reset.transition_generation[key.env_id]), "autoreset changed transition generation")
            artifact_evidence.append({
                "authority_receipt_id": artifact.authority_receipt_id,
                "episode_generation": key.episode_generation,
                "env_id": key.env_id,
                "facts_consume_token": artifact.facts_consume_token,
                "termination_reason": artifact.termination_reason,
                "transition_generation": key.transition_generation,
                "truncated": artifact.truncated,
            })

        _stage("T0", "TERMINAL_STEP_ADMITTED", admission_serial=terminal_admission.identity.serial, physical_step_index=terminal_return_index)
        _stage("T1", "TERMINAL_LIFECYCLE_FINALIZED", artifacts=artifact_evidence)
        _stage("T2", "TERMINAL_SLOTS_INSTALLED", slot_count=len(artifacts), env_id_order=[key.env_id for key in keys])
        _stage("T3", "AUTORESET_UNDER_SAME_AK", admission_serial=terminal_admission.identity.serial, current_reset=_publication(current_reset))
        _stage("T4", "TERMINAL_ENV_STEP_RETURNED", terminated=_done_vectors(terminal_return)[0], truncated=_done_vectors(terminal_return)[1])
        _stage("T5", "TERMINAL_AK_COMPLETED_WINDOW_OPEN_WITH_SLOTS", window_serial=fence_after_return.window.serial, slot_count=len(artifacts))
        _stage("T6", "EXACT_STORED_ARTIFACTS_CAPTURED", artifacts=artifact_evidence, repeat_identity=all(a is b for a, b in zip(artifacts, coordinator.capture_pending_terminal_artifacts(), strict=True)))

        before_publication = current_reset
        before_window = fence_after_return.window
        before_raw = _raw_snapshot(raw_env, torch)
        before_slots = coordinator.capture_pending_terminal_artifacts()
        try:
            coordinator.step_environment(action_builder=action_builder)
        except BaseException as exc:
            _require(getattr(exc, "failure_code", None) == "terminal_ack_required", "pre-ack O1 attempt did not reject through R3", classification="PHASE-B1W-I3-STOP-PREACK-R3-GAP", failure_code="r3_code")
        else:
            raise SmokeEvidenceError("pre-ack O1 attempt unexpectedly passed", classification="PHASE-B1W-I3-STOP-PREACK-R3-GAP", failure_code="r3_missing")
        _require(domain.current_read_port.read_current() is before_publication, "pre-ack R3 changed P2", classification="PHASE-B1W-I3-STOP-PREACK-R3-GAP", failure_code="p2_mutation")
        fence_after_reject = domain.interstep_fence_read_port.read()
        _require(fence_after_reject.phase is _ClaimWindowFencePhase.OPEN and fence_after_reject.window is before_window and not domain._coordinator.poisoned, "pre-ack R3 changed window or poison", classification="PHASE-B1W-I3-STOP-PREACK-R3-GAP", failure_code="fence_mutation")
        _require(_same_raw_snapshot(before_raw, _raw_snapshot(raw_env, torch), torch), "pre-ack R3 changed environment/physical buffers", classification="PHASE-B1W-I3-STOP-PREACK-R3-GAP", failure_code="environment_mutation")
        _require(all(a is b for a, b in zip(before_slots, coordinator.capture_pending_terminal_artifacts(), strict=True)), "pre-ack R3 changed slots")
        _stage("T6B", "DELIBERATE_PREACK_R3_REJECTED_NEUTRALLY", failure_code="terminal_ack_required", poisoned=False)

        ack_before_publication = domain.current_read_port.read_current()
        ack_before_window = domain.interstep_fence_read_port.read().window
        acknowledged = [coordinator.acknowledge_terminal_artifact(artifact.key) for artifact in artifacts]
        _require(all(left is right for left, right in zip(acknowledged, artifacts, strict=True)), "ack returned reconstructed artifacts")
        _require(coordinator.capture_pending_terminal_artifacts() == (), "exact ack did not remove every designated row")
        _require(domain.current_read_port.read_current() is ack_before_publication and domain.interstep_fence_read_port.read().window is ack_before_window, "ack changed P2/window", classification="PHASE-B1W-I3-STOP-ACK-NEUTRALITY-GAP", failure_code="ack_authority_mutation")
        _stage("T7", "EXACT_KEYS_ACKNOWLEDGED_NEUTRALLY", acknowledged=[[key.env_id, key.episode_generation, key.transition_generation] for key in keys])

        postack_before = domain.interstep_fence_read_port.read().window
        next_return = coordinator.step_environment(action_builder=action_builder)
        physical_steps += 1
        _require(physical_steps <= 32, "physical-step bound exceeded after recovery")
        next_admission = context["admissions"][-1]  # type: ignore[index]
        _require(next_admission is not terminal_admission and next_admission.source_window is postack_before, "post-ack R3 did not admit the next exact Ak", classification="PHASE-B1W-I3-STOP-POSTACK-RECOVERY-GAP", failure_code="next_admission")
        _stage("T8", "POSTACK_R3_PASSED", source_window_serial=postack_before.serial, admission_serial=next_admission.identity.serial)
        next_terminated, next_truncated = _done_vectors(next_return)
        _require(not any(next_terminated) and not any(next_truncated), "post-ack step is not nonterminal", classification="PHASE-B1W-I3-STOP-POSTACK-RECOVERY-GAP", failure_code="postack_terminal")
        final_fence = domain.interstep_fence_read_port.read()
        final_publication = domain.current_read_port.read_current()
        _require(final_fence.phase is _ClaimWindowFencePhase.OPEN and final_fence.window is not postack_before and final_fence.active_step is None, "post-ack step stranded Ak", classification="PHASE-B1W-I3-STOP-POSTACK-RECOVERY-GAP", failure_code="stranded_ak")
        _require(coordinator.capture_pending_terminal_artifacts() == () and not domain._coordinator.poisoned, "post-ack recovery created slot or poison")
        _stage("T9", "NEXT_NONTERMINAL_REAL_STEP_COMPLETED_TO_OPEN", admission_serial=next_admission.identity.serial, final_window_serial=final_fence.window.serial, publication=_publication(final_publication))

        return {
            "app_launcher_initialized": True,
            "artifact_evidence": artifact_evidence,
            "capture_repeat_identity": True,
            "claim_fixture": claim_evidence,
            "device": str(device),
            "domain_count": 1,
            "environment_type": type(raw_env).__name__,
            "episode_length_fixture_steps": raw_env.max_episode_length,
            "final_publication": _publication(final_publication),
            "num_envs": num_envs,
            "num_robots": num_robots,
            "num_tasks": num_tasks,
            "o1_count": 1,
            "physical_steps": physical_steps,
            "poisoned": False,
            "postack_nonterminal": True,
            "preack_r3_neutral": True,
            "reset_publication": _publication(reset_view),
            "stages_reached": list(_STAGES_REACHED),
            "terminal_current_reset_separation": True,
            "terminal_slots_after_ack": 0,
        }
    finally:
        env.close()


def _failure_classification(exc: BaseException) -> str:
    explicit = getattr(exc, "classification", None)
    if isinstance(explicit, str):
        return explicit
    code = str(getattr(exc, "failure_code", ""))
    if "terminal_capture" in code:
        return "PHASE-B1W-I3-STOP-TERMINAL-DISCOVERY-AUTHORITY-GAP"
    if "terminal_ack" in code:
        return "PHASE-B1W-I3-STOP-ACK-NEUTRALITY-GAP"
    return "PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP"


def _write_result(path: str | None, result: dict[str, object]) -> None:
    if path is not None:
        Path(path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8")


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
        _diagnostic("L1_PASS", "AppLauncher initialized", headless=True)
        evidence = _run_real_smoke(num_envs=args.num_envs)
        result = {
            "classification": "PHASE-B1W-I3-REAL-TERMINAL-CAPTURE-ACK-AND-RECOVERY-PASS-AWAITING-GPT-REVIEW",
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
                    "classification": "PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP",
                    "error": f"shutdown {type(close_exc).__name__}: {close_exc}",
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
    with tempfile.TemporaryDirectory(prefix="b1w_i3_smoke_") as temp_dir:
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
                worker_result = json.loads(line[len(_WORKER_RESULT_PREFIX):])
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
                worker_result = json.loads(line[len(_WORKER_RESULT_PREFIX):])
            else:
                print(line, end="", flush=True)
        if os.path.isfile(result_path):
            worker_result = json.loads(Path(result_path).read_text(encoding="utf-8"))
        if timed_out:
            result: dict[str, object] = {
                "child_exit_code": child_exit_code,
                "classification": "PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP",
                "error": "bounded worker timeout",
                "status": "failed",
                "timeout": True,
            }
        elif worker_result is None:
            result = {
                "child_exit_code": child_exit_code,
                "classification": "PHASE-B1W-I3-STOP-REAL-TERMINAL-LIFECYCLE-GAP",
                "error": "worker exited without result artifact",
                "status": "failed",
            }
        else:
            result = dict(worker_result)
            result["child_exit_code"] = child_exit_code
            result["shutdown_observed"] = child_exit_code == 0
            result["timeout"] = False
            result["worker_process_alive_after_wait"] = process.poll() is None
            if child_exit_code != 0:
                result["status"] = "failed"
        _diagnostic("SUPERVISOR_EXIT", "worker tree exited", child_exit_code=child_exit_code, child_pid=process.pid, timed_out=timed_out)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(result, indent=2, sort_keys=True), flush=True)
        return 0 if result.get("status") == "passed" and child_exit_code == 0 else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=240)
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
