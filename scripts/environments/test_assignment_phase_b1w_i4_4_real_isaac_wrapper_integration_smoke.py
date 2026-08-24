"""Bounded real-Isaac B1W-I4-4 private wrapper integration smoke.

The public process supervises exactly one headless worker with a finite timeout.
This is verification-only: it uses the private WR-C proof seams and never
activates the public learned-policy event route or a HARL runner.
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
_WORKER_RESULT_PREFIX = "__B1W_I4_4_WORKER_RESULT__"
_PASS = (
    "PHASE-B1W-I4-4-FOCUSED-REAL-ISAAC-WRAPPER-INTEGRATION-"
    "VERIFICATION-PASS-AWAITING-GPT-REVIEW"
)
_STAGES: list[dict[str, object]] = []


class SmokeEvidenceError(RuntimeError):
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


def _record(stage: str, message: str, **evidence: object) -> None:
    payload = {
        "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
        "message": message,
        "pid": os.getpid(),
        "stage": stage,
        **{key: _jsonable(value) for key, value in evidence.items()},
    }
    print(json.dumps(payload, sort_keys=True, default=str), flush=True)


def _stage(stage: str, message: str, **evidence: object) -> None:
    payload = {"stage": stage, **{key: _jsonable(value) for key, value in evidence.items()}}
    _STAGES.append(payload)
    _record(stage, message, **evidence)


def _require(
    condition: bool,
    message: str,
    *,
    classification: str = "PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP",
    failure_code: str = "evidence_mismatch",
) -> None:
    if not condition:
        raise SmokeEvidenceError(
            message,
            classification=classification,
            failure_code=failure_code,
        )


def _values(value: object) -> list[object]:
    return value.detach().cpu().tolist()  # type: ignore[union-attr]


def _publication(publication: object) -> dict[str, object]:
    state = publication.lifecycle_state  # type: ignore[attr-defined]
    return {
        "episode_generation": _values(publication.episode_generation),  # type: ignore[attr-defined]
        "ownership": _values(state.ownership),
        "provenance": [item.kind.value for item in publication.provenance],  # type: ignore[attr-defined]
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
    _require(
        type(returned) is tuple and len(returned) == 5,
        "real DirectMARLEnv step did not return five values",
        classification="PHASE-B1W-I4-4-STOP-REAL-TERMINAL-HANDOFF-GAP",
        failure_code="environment_result",
    )
    terminated_by_agent, truncated_by_agent = returned[2], returned[3]  # type: ignore[index]
    _require(
        type(terminated_by_agent) is dict and type(truncated_by_agent) is dict,
        "real done outputs are not dictionaries",
        classification="PHASE-B1W-I4-4-STOP-REAL-TERMINAL-HANDOFF-GAP",
        failure_code="done_mapping",
    )
    terminated = [[bool(item) for item in _values(value)] for value in terminated_by_agent.values()]
    truncated = [[bool(item) for item in _values(value)] for value in truncated_by_agent.values()]
    _require(bool(terminated) and bool(truncated), "real done mappings are empty")
    _require(all(row == terminated[0] for row in terminated[1:]), "terminated rows differ by agent")
    _require(all(row == truncated[0] for row in truncated[1:]), "truncated rows differ by agent")
    return terminated[0], truncated[0]


def _expected_assignment(publication: object, torch: Any) -> object:
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
    active = {
        int(TaskLifecycleState.CLAIMED),
        int(TaskLifecycleState.NAVIGATING),
        int(TaskLifecycleState.ALIGNING),
    }
    for row in range(num_envs):
        for task_id in range(num_tasks):
            if int(state.task_state[row, task_id].item()) not in active:
                continue
            robot_id = int(state.ownership[row, task_id].item())
            _require(robot_id >= 0, "active task lacks owner", failure_code="active_owner")
            _require(
                int(assignment[row, robot_id].item()) == -1,
                "one robot owns multiple active tasks",
                failure_code="multiple_active_tasks",
            )
            assignment[row, robot_id] = task_id
    return assignment


class _WrapperCallGuard:
    """Delegate metadata but make wrapper-direct raw calls observable."""

    def __init__(self, env: object) -> None:
        self._env = env
        self.unwrapped = env.unwrapped  # type: ignore[attr-defined]
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self._env, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("exact-event wrapper called its raw wrapper reset path")

    def step(self, *args: object, **kwargs: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("exact-event wrapper called its raw wrapper step path")

    def close(self) -> None:
        self._env.close()  # type: ignore[attr-defined]


def _select_real_proposals(
    *, current: object, problem: dict[str, object], noop_id: int, torch: Any
) -> tuple[object, list[dict[str, object]]]:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
        TaskLifecycleState,
    )

    state = current.lifecycle_state
    feasible = problem["feasible_mask"]
    available = problem["available_mask"]
    costs = problem["cost_matrix"]
    num_envs, num_robots, num_tasks = feasible.shape
    actions = torch.full(
        (num_envs, num_robots, 1),
        noop_id,
        dtype=torch.int64,
        device=state.task_state.device,
    )
    selected: list[dict[str, object]] = []
    for row in range(num_envs):
        chosen: tuple[float, int, int] | None = None
        for robot_id in range(num_robots):
            if int(state.robot_state[row, robot_id].item()) != int(
                RobotLifecycleState.NEEDS_ASSIGNMENT
            ):
                continue
            candidates: list[tuple[float, int, int]] = []
            for task_id in range(num_tasks):
                legal = (
                    int(state.task_state[row, task_id].item())
                    == int(TaskLifecycleState.AVAILABLE)
                    and int(state.ownership[row, task_id].item()) == -1
                    and not bool(state.cumulative_failed_pairs[row, robot_id, task_id].item())
                    and bool(feasible[row, robot_id, task_id].item())
                    and bool(available[row, robot_id, task_id].item())
                )
                if legal:
                    candidates.append(
                        (float(costs[row, robot_id, task_id].item()), robot_id, task_id)
                    )
            if candidates:
                chosen = max(candidates, key=lambda item: (item[0], -item[2]))
                break
        _require(
            chosen is not None,
            "bounded reset snapshot has no real feasible legal claim candidate",
            classification="PHASE-B1W-I4-4-STOP-NO-REAL-FEASIBLE-CLAIM-FIXTURE",
            failure_code="real_feasible_fixture",
        )
        cost, robot_id, task_id = chosen
        actions[row, robot_id, 0] = task_id
        selected.append(
            {
                "cost": cost,
                "env_id": int(current.env_id[row].item()),
                "feasible": bool(feasible[row, robot_id, task_id].item()),
                "robot_id": robot_id,
                "selection_rule": "TEST FIXTURE ONLY: lowest legal robot, farthest real feasible task",
                "task_id": task_id,
            }
        )
    return actions, selected


def _run_real_smoke(*, num_envs: int) -> dict[str, object]:
    _record("L2", "before real environment imports")
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import (
        _compose_event_assignment_harl_wrapper,
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
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    physical_step_seconds = float(cfg.sim.dt) * int(cfg.decimation)
    cfg.episode_length_s = physical_step_seconds * 5
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
    _stage(
        "S0",
        "PREFLIGHT_READY",
        device=str(device),
        num_envs=num_envs,
        num_robots=num_robots,
        num_tasks=num_tasks,
        profile=profile.profile_name.value,
    )

    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw_env = env.unwrapped
    guard = _WrapperCallGuard(env)
    context: dict[str, object] = {
        "admissions": [],
        "controls": [],
        "final_p2": [],
        "returns": [],
        "terminal_pre_ack": None,
        "observer_error": None,
    }

    def observer(stage_name: str, detail: object | None) -> None:
        try:
            if stage_name == "S8_AK_ACTIVE":
                context["admissions"].append(detail)  # type: ignore[union-attr]
            elif stage_name == "S6_FINAL_P2_SEEN":
                context["final_p2"].append(detail)  # type: ignore[union-attr]
            elif stage_name == "S9_CONTROL_ACTION_BUILT":
                context["controls"].append(detail.detach().clone())  # type: ignore[union-attr]
            elif stage_name == "S12_ENV_STEP_RETURNED":
                context["returns"].append(detail)  # type: ignore[union-attr]
            elif stage_name == "S14_WINDOW_OPEN":
                slots = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
                if slots:
                    current = domain.current_read_port.read_current()
                    fence = domain.interstep_fence_read_port.read()
                    context["terminal_pre_ack"] = {
                        "current": current,
                        "episode": current.episode_generation.detach().clone(),
                        "transition": current.transition_generation.detach().clone(),
                        "store_version": current.store_version,
                        "window": fence.window,
                        "phase": fence.phase,
                        "poisoned": domain._coordinator.poisoned,
                        "slots": slots,
                    }
        except BaseException as exc:
            context["observer_error"] = exc
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

    wrapper = _compose_event_assignment_harl_wrapper(
        env=guard,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=observer,
        assignment_profile_entrypoint="B1W-I4-4.real_smoke",
    )
    action_records: list[dict[str, object]] = []

    def action_builder(environment: object, assignment: object) -> object:
        _require(environment is raw_env, "O1 received a foreign real environment")
        actions = assignment_to_env_actions(environment, assignment)
        finite = all(bool(torch.isfinite(value).all().item()) for value in actions.values())
        devices = sorted({str(value.device) for value in actions.values()})
        _require(finite, "real continuous action contains NaN or Inf")
        _require(devices == [str(device)], "real continuous action device mismatch", classification="PHASE-B1W-I4-4-STOP-DEVICE-IDENTITY-GAP", failure_code="action_device")
        action_records.append(
            {
                "assignment": assignment.detach().clone(),
                "continuous_action_devices": devices,
                "continuous_action_finite": finite,
            }
        )
        return actions

    physical_steps = 0
    try:
        _stage("S1", "REAL_ENV_AND_WR_C_COMPOSED", environment_type=type(raw_env).__name__)
        reset_result = wrapper.reset()
        _require(type(reset_result) is tuple and len(reset_result) == 3, "wrapper reset arity")
        reset_p2 = domain.current_read_port.read_current()
        reset_fence = domain.interstep_fence_read_port.read()
        _require(str(reset_p2.env_id.device) == str(device), "P2 device mismatch", classification="PHASE-B1W-I4-4-STOP-DEVICE-IDENTITY-GAP", failure_code="p2_device")
        _require(_values(reset_p2.episode_generation) == [0] * num_envs, "reset episode generation", classification="PHASE-B1W-I4-4-STOP-REAL-RESET-INTEGRATION-GAP", failure_code="reset_episode")
        _require(_values(reset_p2.transition_generation) == [-1] * num_envs, "reset transition generation", classification="PHASE-B1W-I4-4-STOP-REAL-RESET-INTEGRATION-GAP", failure_code="reset_transition")
        _require(reset_p2.result is None, "reset P2 retained result", classification="PHASE-B1W-I4-4-STOP-REAL-RESET-INTEGRATION-GAP", failure_code="reset_result")
        _require(all(item.kind.value == "canonical_episode_reset" for item in reset_p2.provenance), "reset provenance", classification="PHASE-B1W-I4-4-STOP-REAL-RESET-INTEGRATION-GAP", failure_code="reset_provenance")
        _require(bool((reset_p2.lifecycle_state.ownership == -1).all().item()), "reset ownership is noncanonical")
        _require(reset_fence.phase is _ClaimWindowFencePhase.OPEN and reset_fence.active_step is None, "reset did not open W1")
        _require(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "reset terminal slots")
        _require(not domain._coordinator.poisoned, "reset poisoned domain")
        _require(wrapper._assignment_lifecycle_resolver_runtime is None, "legacy resolver constructed")
        _stage("S2", "ADMITTED_RESET_RETURNED", reset_publication=_publication(reset_p2))
        _stage("S3", "CANONICAL_RESET_P2_AND_OPEN_W1_VERIFIED", window_serial=reset_fence.window.serial)

        dummy = torch.full(
            (num_envs, num_robots, 1),
            wrapper.noop_action_id,
            dtype=torch.int64,
            device=device,
        )
        common_before = int(raw_env.common_step_counter)
        try:
            wrapper.step(dummy)
        except RuntimeError as exc:
            _require("not runtime-ready" in str(exc), "public event step wrong failure")
        else:
            raise SmokeEvidenceError(
                "public exact-event learned-policy step unexpectedly opened",
                classification="PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP",
                failure_code="public_step_open",
            )
        _require(int(raw_env.common_step_counter) == common_before, "blocked public step mutated real env")

        problem = raw_env.get_assignment_problem()
        source_p2 = domain.current_read_port.read_current()
        source_window = domain.interstep_fence_read_port.read().window
        proposals, selected = _select_real_proposals(
            current=source_p2,
            problem=problem,
            noop_id=wrapper.noop_action_id,
            torch=torch,
        )
        feasible_snapshot = problem["feasible_mask"].detach().clone()
        cost_snapshot = problem["cost_matrix"].detach().clone()
        available_snapshot = problem["available_mask"].detach().clone()
        shape_evidence = {
            "ownership": list(source_p2.lifecycle_state.ownership.shape),
            "failed_pair": list(source_p2.lifecycle_state.cumulative_failed_pairs.shape),
            "feasible_mask": list(feasible_snapshot.shape),
            "cost_matrix": list(cost_snapshot.shape),
        }
        _require(
            shape_evidence
            == {
                "ownership": [num_envs, num_tasks],
                "failed_pair": [num_envs, num_robots, num_tasks],
                "feasible_mask": [num_envs, num_robots, num_tasks],
                "cost_matrix": [num_envs, num_robots, num_tasks],
            },
            f"real proposal/P2 shapes do not preserve E/M/N: {shape_evidence}",
            failure_code="shape_identity",
        )
        _require(str(feasible_snapshot.device) == str(device) and str(cost_snapshot.device) == str(device), "proposal snapshot device", classification="PHASE-B1W-I4-4-STOP-DEVICE-IDENTITY-GAP", failure_code="proposal_device")
        decision = wrapper._capture_event_proposal_decision(
            feasible_mask=feasible_snapshot,
            cost_matrix=cost_snapshot,
            available_mask=available_snapshot,
        )
        _stage(
            "S4",
            "REAL_PROPOSAL_SNAPSHOT_CAPTURED",
            source_publication_serial=source_p2.publication_identity.serial,
            source_episode=_values(source_p2.episode_generation),
            source_transition=_values(source_p2.transition_generation),
            source_window_serial=source_window.serial,
            selected=selected,
            feasible_shape=list(feasible_snapshot.shape),
            cost_shape=list(cost_snapshot.shape),
            ownership_shape=shape_evidence["ownership"],
            failed_pair_shape=shape_evidence["failed_pair"],
        )
        proposal_result = wrapper._step_event_proposals(
            proposals,
            decision=decision,
            action_builder=action_builder,
        )
        physical_steps += 1
        _require(context["observer_error"] is None, f"stage observer failed: {context['observer_error']}")
        proposal_done = _done_vectors(proposal_result.environment_result)
        _require(not any(proposal_done[0]) and not any(proposal_done[1]), "proposal fixture terminated early", classification="PHASE-B1W-I4-4-STOP-REAL-PROPOSAL-B1-GAP", failure_code="proposal_terminal")
        _require(proposal_result.claim_artifact is not None, "real proposal produced no B1 artifact", classification="PHASE-B1W-I4-4-STOP-REAL-PROPOSAL-B1-GAP", failure_code="claim_artifact")
        _require(proposal_result.post_claim_publication.store_version == source_p2.store_version + 1, "B1 Store delta is not exactly one", classification="PHASE-B1W-I4-4-STOP-REAL-PROPOSAL-B1-GAP", failure_code="b1_store_delta")
        _require(proposal_result.admitted_publication is proposal_result.post_claim_publication, "Ak did not capture final P2")
        expected = _expected_assignment(proposal_result.admitted_publication, torch)
        _require(torch.equal(expected, proposal_result.admitted_effective_assignment), "proposal Ak assignment differs from final P2")
        _require(torch.equal(action_records[-1]["assignment"], expected), "real proposal controller source differs from Ak")
        committed = [[item.value for item in row] for row in proposal_result.committed_interpretations]
        for item in selected:
            row = int(item["env_id"])
            robot_id = int(item["robot_id"])
            _require(committed[row][robot_id] == "new_claim_committed", "real feasible proposal was not committed", classification="PHASE-B1W-I4-4-STOP-REAL-PROPOSAL-B1-GAP", failure_code="proposal_interpretation")
        _stage("S5", "REAL_M1_B1_COMMITTED_ONCE", artifact_store_version=proposal_result.claim_artifact.committed_store_version, selected=selected)
        _stage("S6", "FINAL_P2_ADMITTED_TO_AK_AND_REAL_STEP_COMPLETED", admitted_assignment=expected, controller_assignment_shape=list(expected.shape), post_step_publication=_publication(proposal_result.current_publication))

        continuation_source = domain.current_read_port.read_current()
        continuation_expected = _expected_assignment(continuation_source, torch)
        _require(bool((continuation_expected >= 0).any().item()), "real claim did not persist for continuation", classification="PHASE-B1W-I4-4-STOP-REAL-PROPOSAL-B1-GAP", failure_code="continuation_fixture")
        continuation_window = domain.interstep_fence_read_port.read().window
        continuation_result = wrapper._step_event_without_new_claim(action_builder=action_builder)
        physical_steps += 1
        continuation_done = _done_vectors(continuation_result.environment_result)
        _require(not any(continuation_done[0]) and not any(continuation_done[1]), "continuation fixture terminated early")
        _require(continuation_result.claim_artifact is None, "continuation created a B1 artifact")
        _require(continuation_result.source_publication is continuation_source and continuation_result.admitted_publication is continuation_source, "continuation changed P2 before Ak")
        _require(torch.equal(continuation_result.admitted_effective_assignment, continuation_expected), "continuation Ak assignment")
        _require(torch.equal(action_records[-1]["assignment"], continuation_expected), "continuation controller source")
        _require(domain.interstep_fence_read_port.read().window is not continuation_window, "continuation did not open next window")
        _stage("S7", "REAL_NO_NEW_CLAIM_CONTINUATION_COMPLETED", assignment=continuation_expected)

        terminal_result = None
        while physical_steps < 32:
            result = wrapper._step_event_without_new_claim(action_builder=action_builder)
            physical_steps += 1
            if result.terminal_historical_payload:
                terminal_result = result
                break
            done = _done_vectors(result.environment_result)
            _require(not any(done[0]) and not any(done[1]), "terminal return lacked historical payload", classification="PHASE-B1W-I4-4-STOP-REAL-TERMINAL-HANDOFF-GAP", failure_code="terminal_payload_missing")
        _require(terminal_result is not None, "bounded drive produced no real terminal", classification="PHASE-B1W-I4-4-STOP-REAL-TERMINAL-HANDOFF-GAP", failure_code="no_terminal")
        _require(context["observer_error"] is None, f"terminal observer failed: {context['observer_error']}")
        pre_ack = context["terminal_pre_ack"]
        _require(type(pre_ack) is dict, "no pre-ACK real terminal snapshot", classification="PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP", failure_code="pre_ack_snapshot")
        slots = pre_ack["slots"]
        history = terminal_result.terminal_historical_payload
        _require(len(slots) == num_envs and len(history) == num_envs, "real terminal batch cardinality")
        keys = [(item.key.env_id, item.key.episode_generation, item.key.transition_generation) for item in slots]
        historical_keys = [(item.env_id, item.episode_generation, item.transition_generation) for item in history]
        _require(keys == sorted(keys) and historical_keys == keys, "real history/capture exact keys")
        terminal_done = _done_vectors(terminal_result.environment_result)
        _require(all(terminal_done[1]) and not any(terminal_done[0]), "real terminal is not all-row time limit")
        for row, historical in enumerate(history):
            _require(historical.termination_reason == int(TerminationReason.TIME_LIMIT), "historical reason")
            _require(historical.truncated and not historical.terminated, "historical done flags")
            _require(historical.optional_sidecar is None, "historical critic sidecar synthesized")
            _require(historical.episode_generation + 1 == int(terminal_result.current_publication.episode_generation[row].item()), "historical/current episode split")
            _require(historical.transition_generation == int(terminal_result.current_publication.transition_generation[row].item()), "historical/current transition split")
            _require(str(historical.coverage_after_transition.device) == str(device), "historical tensor device")
        _stage("S8", "BOUNDED_DRIVE_REACHED_REAL_TERMINAL", physical_steps=physical_steps, keys=keys)
        _stage("S9", "REAL_TERMINAL_SLOTS_OBSERVED_BEFORE_FACADE_ACK", slot_count=len(slots))
        _stage("S10", "SAME_AK_AUTORESET_AND_OPEN_WNEXT_OBSERVED", current_publication=_publication(terminal_result.current_publication), window_serial=pre_ack["window"].serial)
        _stage("S11", "WRAPPER_HISTORICAL_COPY_RETURNED", historical_keys=historical_keys, optional_sidecar=None)

        after_ack = domain.current_read_port.read_current()
        after_fence = domain.interstep_fence_read_port.read()
        _require(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "facade batch ACK left slots", classification="PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP", failure_code="slots_after_ack")
        _require(after_ack is pre_ack["current"] and after_ack.store_version == pre_ack["store_version"], "ACK changed P2/Store", classification="PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP", failure_code="ack_p2")
        _require(torch.equal(after_ack.episode_generation, pre_ack["episode"]) and torch.equal(after_ack.transition_generation, pre_ack["transition"]), "ACK changed generations", classification="PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP", failure_code="ack_generations")
        _require(after_fence.phase is pre_ack["phase"] and after_fence.window is pre_ack["window"] and domain._coordinator.poisoned is pre_ack["poisoned"], "ACK changed window/poison", classification="PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP", failure_code="ack_window")
        _require(context["returns"][-1] is terminal_result.environment_result, "facade did not preserve raw terminal return identity")
        _stage("S12", "ATOMIC_BATCH_EXACT_ACK_COMPLETED_NEUTRALLY", slots_before=len(slots), slots_after=0, window_serial=after_fence.window.serial)
        _stage("S13", "HISTORICAL_AND_CURRENT_LIFETIMES_SEPARATED", historical_episode=[item.episode_generation for item in history], current_episode=_values(after_ack.episode_generation), raw_episode_length=_values(raw_env.episode_length_buf))

        recovery_window = after_fence.window
        recovery_result = wrapper._step_event_without_new_claim(action_builder=action_builder)
        physical_steps += 1
        recovery_done = _done_vectors(recovery_result.environment_result)
        _require(not any(recovery_done[0]) and not any(recovery_done[1]), "post-ACK recovery terminal", classification="PHASE-B1W-I4-4-STOP-REAL-POST-ACK-RECOVERY-GAP", failure_code="recovery_terminal")
        final_fence = domain.interstep_fence_read_port.read()
        _require(recovery_result.terminal_historical_payload == (), "terminal history accumulated")
        _require(final_fence.phase is _ClaimWindowFencePhase.OPEN and final_fence.window is not recovery_window and final_fence.active_step is None, "post-ACK recovery stranded Ak", classification="PHASE-B1W-I4-4-STOP-REAL-POST-ACK-RECOVERY-GAP", failure_code="recovery_window")
        _require(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == () and not domain._coordinator.poisoned, "post-ACK recovery slot/poison")
        _stage("S14", "REAL_POST_ACK_RECOVERY_STEP_COMPLETED", final_window_serial=final_fence.window.serial, final_publication=_publication(recovery_result.current_publication))
        _require(guard.direct_reset_calls == 0 and guard.direct_step_calls == 0, "wrapper used raw wrapper calls")
        _stage("S15", "WRAPPER_RAW_CALL_ISOLATION_VERIFIED", direct_reset_calls=0, direct_step_calls=0)
        _stage("S16", "PUBLIC_EVENT_STEP_AND_READINESS_REMAIN_BLOCKED", public_event_step="blocked", action_mask=None)
        _stage("S17", "FINAL_OPEN_NO_SLOT_NO_POISON", window_serial=final_fence.window.serial)

        return {
            "action_records": action_records,
            "app_launcher_initialized": True,
            "b1_store_delta": 1,
            "device": str(device),
            "direct_wrapper_reset_calls": guard.direct_reset_calls,
            "direct_wrapper_step_calls": guard.direct_step_calls,
            "environment_type": type(raw_env).__name__,
            "exact_event_profile": profile.profile_name.value,
            "final_publication": _publication(recovery_result.current_publication),
            "final_window_serial": final_fence.window.serial,
            "legacy_resolver": None,
            "num_envs": num_envs,
            "num_robots": num_robots,
            "num_tasks": num_tasks,
            "optional_sidecar": None,
            "physical_steps": physical_steps,
            "poisoned": False,
            "proposal_selected": selected,
            "public_event_step": "blocked",
            "reset_publication": _publication(reset_p2),
            "runtime_readiness": "blocked",
            "shape_evidence": {**shape_evidence, "controller_assignment": [num_envs, num_robots]},
            "stages": list(_STAGES),
            "terminal_historical_keys": historical_keys,
            "terminal_slots_after_ack": 0,
            "terminal_slots_before_ack": len(slots),
            "wrapper_count": 1,
        }
    finally:
        wrapper.close()


def _failure_classification(exc: BaseException) -> str:
    explicit = getattr(exc, "classification", None)
    if isinstance(explicit, str):
        return explicit
    code = str(getattr(exc, "failure_code", ""))
    if "device" in code:
        return "PHASE-B1W-I4-4-STOP-DEVICE-IDENTITY-GAP"
    if "ack" in code:
        return "PHASE-B1W-I4-4-STOP-REAL-ATOMIC-ACK-GAP"
    if "terminal" in code:
        return "PHASE-B1W-I4-4-STOP-REAL-TERMINAL-HANDOFF-GAP"
    return "PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP"


def _write_result(path: str | None, result: dict[str, object]) -> None:
    if path is not None:
        Path(path).write_text(
            json.dumps(_jsonable(result), sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )


def _run_worker(args: argparse.Namespace) -> int:
    _record("L0", "smoke worker entered", python=sys.executable)
    simulation_app = None
    result: dict[str, object]
    exit_code = 1
    try:
        _record("L1", "before AppLauncher construction", headless=True)
        from isaaclab.app import AppLauncher

        launcher = AppLauncher(headless=True)
        simulation_app = launcher.app
        _record("L1_PASS", "AppLauncher initialized", headless=True)
        evidence = _run_real_smoke(num_envs=args.num_envs)
        _stage("S18", "CLEAN_ENV_CLOSE_REQUESTED")
        result = {
            "classification": _PASS,
            "elapsed_seconds": round(time.monotonic() - _STARTED_AT, 3),
            "evidence": evidence,
            "pid": os.getpid(),
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
            "pid": os.getpid(),
            "stages": list(_STAGES),
            "status": "failed",
            "traceback": trace,
        }
    finally:
        _write_result(args.result_file, result)
        print(
            _WORKER_RESULT_PREFIX
            + json.dumps(_jsonable(result), sort_keys=True, separators=(",", ":")),
            flush=True,
        )
        _record("L4", "before SimulationApp shutdown")
        if simulation_app is not None:
            try:
                simulation_app.close()
            except BaseException as close_exc:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                result = {
                    "classification": "PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP",
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
    with tempfile.TemporaryDirectory(prefix="b1w_i4_4_smoke_") as temp_dir:
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
        _record(
            "SUPERVISOR",
            "launching exactly one bounded worker",
            command=command,
            timeout_seconds=args.timeout_seconds,
        )
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
                _record("SUPERVISOR_TIMEOUT", "worker exceeded timeout", child_pid=process.pid)
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
                "classification": "PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP",
                "error": "bounded worker timeout",
                "status": "failed",
                "timeout": True,
            }
        elif worker_result is None:
            result = {
                "child_exit_code": child_exit_code,
                "classification": "PHASE-B1W-I4-4-STOP-REAL-P2-AK-CONTROL-GAP",
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
        _record(
            "SUPERVISOR_EXIT",
            "worker tree exited",
            child_exit_code=child_exit_code,
            child_pid=process.pid,
            timed_out=timed_out,
        )
        print(
            json.dumps(result, sort_keys=True, separators=(",", ":"))
            if args.json
            else json.dumps(result, indent=2, sort_keys=True),
            flush=True,
        )
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
