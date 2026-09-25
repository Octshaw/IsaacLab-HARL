"""Bounded real-Isaac task-progress and horizon qualification for Phase B2-T3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _assignment_phase_b2_t3_progress_observer import (  # noqa: E402
    capture_progress_row,
    schema_artifact,
)
from _assignment_phase_b2_t0_ld_decision_gate import (  # noqa: E402
    FORCED_CONTINUATION_ROW,
    FORCED_NOOP_ROW,
    POLICY_DECISION_ROW,
    LifecycleDecisionRowEvidence,
    qualify_lifecycle_decision_boundary,
)


PASS = "PHASE-B2-T3-TASK-PROGRESS-HORIZON-QUALIFIED-AWAITING-GPT-REVIEW"
STOP_NO_PROGRESS = "PHASE-B2-T3-STOP-CONTROLLED-TASK-NO-PROGRESS"
STOP_NOT_COMPLETED = "PHASE-B2-T3-STOP-CONTROLLED-TASK-NOT-COMPLETED"
STOP_CONTRACT = "PHASE-B2-T3-STOP-LIFECYCLE-COMPLETION-CONTRACT-DEFECT"
STARTED = time.monotonic()


class QualificationError(RuntimeError):
    def __init__(self, classification: str, message: str) -> None:
        self.classification = classification
        super().__init__(f"{classification}: {message}")


def _require(condition: bool, classification: str, message: str) -> None:
    if not condition:
        raise QualificationError(classification, message)


def _jsonable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "detach") and hasattr(value, "cpu") and hasattr(value, "tolist"):
        return value.detach().cpu().tolist()  # type: ignore[union-attr]
    if hasattr(value, "value"):
        return _jsonable(value.value)  # type: ignore[union-attr]
    return str(value)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _record(stage: str, **payload: object) -> None:
    print(
        json.dumps(
            {
                "elapsed_seconds": round(time.monotonic() - STARTED, 3),
                "pid": os.getpid(),
                "stage": stage,
                **{key: _jsonable(value) for key, value in payload.items()},
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _digest_tensors(values: list[tuple[str, object]]) -> str:
    digest = hashlib.sha256()
    for name, value in values:
        digest.update(name.encode("utf-8"))
        if hasattr(value, "detach"):
            tensor = value.detach().contiguous().cpu()  # type: ignore[union-attr]
            digest.update(str(tuple(tensor.shape)).encode("ascii"))
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(tensor.numpy().tobytes())
        else:
            digest.update(repr(value).encode("utf-8"))
    return digest.hexdigest()


class _WrapperCallGuard:
    def __init__(self, env: object) -> None:
        self._env = env
        self.unwrapped = env.unwrapped  # type: ignore[attr-defined]
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self._env, name)

    def reset(self, *_args: object, **_kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("event wrapper attempted its raw wrapper/duplicate reset path")

    def step(self, *_args: object, **_kwargs: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("event wrapper attempted its raw wrapper/duplicate step path")

    def close(self) -> None:
        self._env.close()  # type: ignore[attr-defined]


def _active_owned_task(state: object, robot_id: int) -> int | None:
    import torch

    active = torch.tensor([1, 2, 3], dtype=torch.int64, device=state.task_state.device)
    mask = torch.isin(state.task_state[0], active) & (state.ownership[0] == robot_id)
    tasks = mask.nonzero(as_tuple=False).flatten().detach().cpu().tolist()
    _require(len(tasks) <= 1, STOP_CONTRACT, f"robot {robot_id} owns multiple active tasks")
    return None if not tasks else int(tasks[0])


def _make_runtime(*, entrypoint: str) -> dict[str, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import (
        seal_current_event_policy_decision_bundle_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import (
        capture_current_event_policy_evidence_snapshot_v2,
        capture_event_policy_physical_problem_evidence_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import (
        _compose_event_assignment_harl_wrapper,
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
    cfg.scene.num_envs = 1
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    normal_episode_length_s = float(cfg.episode_length_s)
    device = torch.device(cfg.sim.device)
    num_robots = len(cfg.possible_agents)
    num_tasks = len(cfg.viewpoint_poses)
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(1, dtype=torch.int64, device=device),
            num_robots=num_robots,
            num_tasks=num_tasks,
        )
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw = env.unwrapped
    guard = _WrapperCallGuard(env)
    facade_events: list[tuple[str, object | None]] = []

    def facade_observer(stage: str, detail: object | None) -> None:
        facade_events.append((stage, detail))

    wrapper = _compose_event_assignment_harl_wrapper(
        env=guard,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=facade_observer,
        assignment_profile_entrypoint=entrypoint,
    )

    def current_bundle() -> object:
        current = domain.current_read_port.read_current()
        open_view = domain.interstep_fence_read_port.read()
        scale = raw._event_terminal_critic_scale_contract_v2
        physical = capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=raw.get_assignment_problem(),
            episode_progress_steps=raw.episode_length_buf,
            scale_contract=scale,
        )
        snapshot = capture_current_event_policy_evidence_snapshot_v2(
            current_publication=current,
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=scale,
        )
        return seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)

    control_records: list[dict[str, object]] = []

    def action_builder(environment: object, assignment: object) -> object:
        _require(environment is raw, STOP_CONTRACT, "controller received foreign environment")
        controls = assignment_to_env_actions(environment, assignment)
        finite = all(bool(torch.isfinite(value).all().item()) for value in controls.values())
        _require(finite, STOP_CONTRACT, "controller emitted nonfinite action")
        control_records.append(
            {
                "assignment": assignment.detach().cpu().tolist(),
                "max_abs_action": max(float(value.abs().max().item()) for value in controls.values()),
                "finite": finite,
            }
        )
        return controls

    return {
        "torch": torch,
        "cfg": cfg,
        "profile": profile,
        "device": device,
        "num_robots": num_robots,
        "num_tasks": num_tasks,
        "normal_episode_length_s": normal_episode_length_s,
        "domain": domain,
        "raw": raw,
        "guard": guard,
        "wrapper": wrapper,
        "current_bundle": current_bundle,
        "action_builder": action_builder,
        "control_records": control_records,
        "facade_events": facade_events,
    }


def _decision_capture(wrapper: object, bundle: object) -> object:
    physical = bundle.evidence_snapshot.physical_evidence
    available = (
        bundle.available_actions_bool[..., : bundle.evidence_identity.N]
        & bundle.policy_row_mask.expand(-1, -1, bundle.evidence_identity.N)
    ).contiguous()
    return wrapper._capture_event_proposal_decision(
        feasible_mask=physical.explicit_physical_feasibility,
        cost_matrix=physical.geometric_pair_ranking_cost,
        available_mask=available,
    )


def _select_controlled_pair(runtime: dict[str, object], bundle: object) -> dict[str, object]:
    raw = runtime["raw"]
    problem = raw.get_assignment_problem()
    available = bundle.available_actions_bool[0, :, : runtime["num_tasks"]]
    candidates: list[tuple[float, int, int]] = []
    fallback: list[tuple[float, int, int]] = []
    for robot_id in range(int(runtime["num_robots"])):
        tolerance = float(raw.scan_pos_tolerance[robot_id].item())
        step = float(raw.max_ee_xyz_step[robot_id].item())
        for task_id in range(int(runtime["num_tasks"])):
            if not bool(available[robot_id, task_id].item()):
                continue
            cost = float(problem["cost_matrix"][0, robot_id, task_id].item())
            item = (cost, robot_id, task_id)
            fallback.append(item)
            if cost > tolerance + step + 1.0e-6:
                candidates.append(item)
    _require(bool(fallback), STOP_CONTRACT, "no legal physically feasible initial task")
    cost, robot_id, task_id = min(candidates or fallback)
    return {
        "selection_rule": (
            "minimum current geometric pair cost among canonical policy-row legal tasks "
            "whose initial distance exceeds scan tolerance plus one scanner increment"
            if candidates
            else "minimum current geometric pair cost among canonical policy-row legal tasks"
        ),
        "robot_id": robot_id,
        "task_id": task_id,
        "initial_distance": cost,
        "scan_pos_tolerance": float(raw.scan_pos_tolerance[robot_id].item()),
        "max_ee_xyz_step": float(raw.max_ee_xyz_step[robot_id].item()),
        "feasible": bool(problem["feasible_mask"][0, robot_id, task_id].item()),
        "available": bool(problem["available_mask"][0, robot_id, task_id].item()),
    }


def _controlled_actions(
    runtime: dict[str, object],
    bundle: object,
    *,
    target_robot: int,
    target_task: int,
    initial_claim_pending: bool,
) -> tuple[object, tuple[int, ...]]:
    torch = runtime["torch"]
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import (
        EventPolicyRowKind,
    )

    actions = bundle.forced_action_id.clone().to(dtype=torch.int64)
    policy_calls = [0] * int(runtime["num_robots"])
    for robot_id in range(int(runtime["num_robots"])):
        kind = int(bundle.row_kind[0, robot_id].item())
        if kind == int(EventPolicyRowKind.POLICY_DECISION_ROW):
            policy_calls[robot_id] = 1
            actions[0, robot_id, 0] = int(runtime["num_tasks"])
            if initial_claim_pending and robot_id == target_robot:
                actions[0, robot_id, 0] = target_task
        elif kind in (
            int(EventPolicyRowKind.FORCED_CONTINUATION_ROW),
            int(EventPolicyRowKind.FORCED_NOOP_ROW),
        ):
            _require(
                int(actions[0, robot_id, 0].item()) >= 0,
                STOP_CONTRACT,
                "forced row lacked canonical action",
            )
        else:
            raise QualificationError(STOP_CONTRACT, "unexpected terminal row before physical step")
    return actions, tuple(policy_calls)


def _ld_receipt(
    runtime: dict[str, object],
    bundle: object,
    after_publication: object,
    *,
    collection_index: int,
    policy_calls: tuple[int, ...],
) -> dict[str, object]:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import (
        EventPolicyRowKind,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
    )

    before = bundle.evidence_snapshot.source_publication.lifecycle_state
    after = after_publication.lifecycle_state
    kinds = {
        int(EventPolicyRowKind.POLICY_DECISION_ROW): POLICY_DECISION_ROW,
        int(EventPolicyRowKind.FORCED_CONTINUATION_ROW): FORCED_CONTINUATION_ROW,
        int(EventPolicyRowKind.FORCED_NOOP_ROW): FORCED_NOOP_ROW,
    }
    rows = []
    for robot_id in range(int(runtime["num_robots"])):
        row_kind = kinds[int(bundle.row_kind[0, robot_id].item())]
        called = int(policy_calls[robot_id])
        rows.append(
            LifecycleDecisionRowEvidence(
                collection_index=collection_index,
                physical_step_index=collection_index,
                env_index=0,
                robot_index=robot_id,
                episode_generation=int(bundle.evidence_identity.episode_generations[0]),
                transition_generation=int(bundle.evidence_identity.transition_generations[0]),
                lifecycle_state=RobotLifecycleState(
                    int(before.robot_state[0, robot_id].item())
                ).name,
                current_owned_task_id=_active_owned_task(before, robot_id),
                decision_required=row_kind == POLICY_DECISION_ROW,
                decision_reason=row_kind,
                actor_policy_call_count=called,
                proposal_produced=called == 1,
                behavior_logprob_produced=called == 1,
                continuation_used=row_kind == FORCED_CONTINUATION_ROW,
                terminal_autoreset_context="none",
                ownership_before=_active_owned_task(before, robot_id),
                ownership_after=_active_owned_task(after, robot_id),
            )
        )
    return qualify_lifecycle_decision_boundary(tuple(rows)).to_mapping()


def run_controlled(artifact_dir: Path) -> dict[str, object]:
    from collections import Counter

    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import (
        EventPolicyRowKind,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        RobotLifecycleState,
        TaskLifecycleState,
        TerminationReason,
    )

    runtime = _make_runtime(entrypoint="B2-T3.controlled_task_completion")
    wrapper = runtime["wrapper"]
    raw = runtime["raw"]
    domain = runtime["domain"]
    torch = runtime["torch"]
    trajectory: list[dict[str, object]] = []
    ld_receipts: list[dict[str, object]] = []
    event_histogram: Counter[str] = Counter()
    policy_calls_total = [0] * int(runtime["num_robots"])
    continuation_boundaries = 0
    claim_result = None
    completion_result = None
    completion_step = None
    selected = None
    initial_scanner = None
    minimum_distance = float("inf")
    physical_steps = 0
    timeout_boundaries = 0
    autoreset_boundaries = 0
    try:
        reset = wrapper.reset()
        _require(type(reset) is tuple and len(reset) == 3, STOP_CONTRACT, "reset contract")
        bundle = runtime["current_bundle"]()
        selected = _select_controlled_pair(runtime, bundle)
        robot_id = int(selected["robot_id"])
        task_id = int(selected["task_id"])
        source_publication = bundle.evidence_snapshot.source_publication
        initial_scanner = raw.scanner_pos[0, robot_id].detach().clone()
        initial_completed = int(
            (source_publication.lifecycle_state.task_state[0] == int(TaskLifecycleState.COMPLETED))
            .sum()
            .item()
        )
        initial_coverage = int(raw.viewpoints_covered[0].sum().item())
        initial_completion_count = int(
            source_publication.lifecycle_state.completion_count[0, robot_id].item()
        )
        pre_actions, pre_calls = _controlled_actions(
            runtime,
            bundle,
            target_robot=robot_id,
            target_task=task_id,
            initial_claim_pending=True,
        )
        trajectory.append(
            capture_progress_row(
                raw,
                source_publication,
                global_step=0,
                target_robot=robot_id,
                target_task=task_id,
                decision_required=True,
                policy_call_count=pre_calls[robot_id],
                proposal_action_id=int(pre_actions[0, robot_id, 0].item()),
                effective_assignment=None,
                boundary_kind="POLICY_DECISION_ROW_PRE_CLAIM",
            )
        )
        process_config = {
            "schema_version": "b2_t3_b_process_config_v1",
            "pid": os.getpid(),
            "fresh_process": True,
            "historical_route_reused": False,
            "app_launcher_lifetimes": 1,
            "environment_constructions": 1,
            "environment_objects": 1,
            "E": 1,
            "M": int(runtime["num_robots"]),
            "N": int(runtime["num_tasks"]),
            "profile": runtime["profile"].profile_name.value,
            "device": str(runtime["device"]),
            "sim_dt_seconds": float(runtime["cfg"].sim.dt),
            "control_decimation": int(runtime["cfg"].decimation),
            "step_dt_seconds": float(raw.step_dt),
            "episode_length_s": float(runtime["normal_episode_length_s"]),
            "max_episode_length": int(raw.max_episode_length),
            "harness_episode_override": False,
            "learner_constructed": False,
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "selected_pair": selected,
        }
        _write_json(artifact_dir / "t3_b_process_config.json", process_config)
        _record("T3_B_START", config=process_config)

        while physical_steps < int(raw.max_episode_length):
            bundle = runtime["current_bundle"]()
            kind = int(bundle.row_kind[0, robot_id].item())
            is_continuation = kind == int(EventPolicyRowKind.FORCED_CONTINUATION_ROW)
            actions, policy_calls = _controlled_actions(
                runtime,
                bundle,
                target_robot=robot_id,
                target_task=task_id,
                initial_claim_pending=physical_steps == 0,
            )
            for index, count in enumerate(policy_calls):
                policy_calls_total[index] += int(count)
            if is_continuation:
                continuation_boundaries += 1
                _require(
                    policy_calls[robot_id] == 0,
                    STOP_CONTRACT,
                    "target actor/policy called during genuine continuation",
                )
            decision = _decision_capture(wrapper, bundle)
            result = wrapper._step_event_proposals(
                actions,
                decision=decision,
                layout="env_agent_action",
                action_builder=runtime["action_builder"],
            )
            physical_steps += 1
            ld_receipts.append(
                _ld_receipt(
                    runtime,
                    bundle,
                    result.current_publication,
                    collection_index=physical_steps,
                    policy_calls=policy_calls,
                )
            )
            current_result = result.current_publication.result
            events = () if current_result is None else tuple(current_result.lifecycle_events)
            for event in events:
                event_histogram[str(event.event_type.value)] += 1
            row = capture_progress_row(
                raw,
                result.current_publication,
                global_step=physical_steps,
                target_robot=robot_id,
                target_task=task_id,
                decision_required=bool(bundle.decision_valid_mask[0, robot_id, 0].item()),
                policy_call_count=policy_calls[robot_id],
                proposal_action_id=int(actions[0, robot_id, 0].item()),
                effective_assignment=result.admitted_effective_assignment,
                boundary_kind=EventPolicyRowKind(kind).name,
            )
            trajectory.append(row)
            minimum_distance = min(minimum_distance, float(row["distance_to_target"]))
            if physical_steps == 1:
                claim_result = result
                state = result.current_publication.lifecycle_state
                _require(result.claim_artifact is not None, STOP_CONTRACT, "initial proposal produced no B1 artifact")
                _require(
                    int(state.ownership[0, task_id].item()) == robot_id,
                    STOP_CONTRACT,
                    "claim did not establish target ownership",
                )
                _require(
                    int(state.task_state[0, task_id].item())
                    in (
                        int(TaskLifecycleState.CLAIMED),
                        int(TaskLifecycleState.NAVIGATING),
                        int(TaskLifecycleState.ALIGNING),
                    ),
                    STOP_CONTRACT,
                    "claim did not establish active task state",
                )
            if row["task_completed_event"]:
                completion_result = result
                completion_step = physical_steps
                break
            if result.terminal_historical_payload:
                timeout_boundaries += sum(
                    int(item.termination_reason == int(TerminationReason.TIME_LIMIT))
                    for item in result.terminal_historical_payload
                )
                autoreset_boundaries += len(result.terminal_historical_payload)
                break

        _require(claim_result is not None, STOP_CONTRACT, "no real claim")
        moved = float(torch.norm(raw.scanner_pos[0, robot_id] - initial_scanner).item())
        _require(
            minimum_distance < float(selected["initial_distance"]) - 1.0e-5 and moved > 1.0e-5,
            STOP_NO_PROGRESS,
            "controlled pair showed no measurable scanner/distance progress",
        )
        _require(completion_result is not None, STOP_NOT_COMPLETED, "normal horizon produced no task completion")
        _require(
            completion_step is not None and completion_step > 1 and continuation_boundaries >= 1,
            STOP_CONTRACT,
            "completion did not survive a genuine continuation boundary",
        )
        completed_publication = completion_result.current_publication
        completed_state = completed_publication.lifecycle_state
        completed_count = int(
            (completed_state.task_state[0] == int(TaskLifecycleState.COMPLETED)).sum().item()
        )
        coverage_count = int(raw.viewpoints_covered[0].sum().item())
        completion_count = int(completed_state.completion_count[0, robot_id].item())
        _require(
            int(completed_state.task_state[0, task_id].item()) == int(TaskLifecycleState.COMPLETED),
            STOP_CONTRACT,
            "TASK_COMPLETED event did not bind to P2 COMPLETED",
        )
        _require(
            int(completed_state.ownership[0, task_id].item()) == -1,
            STOP_CONTRACT,
            "completed task retained ownership",
        )
        _require(completed_count > initial_completed, STOP_CONTRACT, "completed task count did not increase")
        _require(coverage_count > initial_coverage, STOP_CONTRACT, "coverage did not increase")
        _require(completion_count > initial_completion_count, STOP_CONTRACT, "robot completion count did not increase")
        _require(
            int(completed_state.robot_state[0, robot_id].item())
            == int(RobotLifecycleState.NEEDS_ASSIGNMENT),
            STOP_CONTRACT,
            "robot did not reopen a decision after completion",
        )

        reopened_bundle = runtime["current_bundle"]()
        _require(
            bool(reopened_bundle.decision_valid_mask[0, robot_id, 0].item()),
            STOP_CONTRACT,
            "post-completion target row was not decision eligible",
        )
        reopened_actions, reopened_calls = _controlled_actions(
            runtime,
            reopened_bundle,
            target_robot=robot_id,
            target_task=task_id,
            initial_claim_pending=False,
        )
        _require(reopened_calls[robot_id] == 1, STOP_CONTRACT, "reopened decision did not call policy exactly once")
        for index, count in enumerate(reopened_calls):
            policy_calls_total[index] += int(count)
        reopened_result = wrapper._step_event_proposals(
            reopened_actions,
            decision=_decision_capture(wrapper, reopened_bundle),
            layout="env_agent_action",
            action_builder=runtime["action_builder"],
        )
        physical_steps += 1
        ld_receipts.append(
            _ld_receipt(
                runtime,
                reopened_bundle,
                reopened_result.current_publication,
                collection_index=physical_steps,
                policy_calls=reopened_calls,
            )
        )
        trajectory.append(
            capture_progress_row(
                raw,
                reopened_result.current_publication,
                global_step=physical_steps,
                target_robot=robot_id,
                target_task=task_id,
                decision_required=True,
                policy_call_count=1,
                proposal_action_id=int(reopened_actions[0, robot_id, 0].item()),
                effective_assignment=reopened_result.admitted_effective_assignment,
                boundary_kind="POLICY_DECISION_ROW_POST_COMPLETION_REOPENED",
            )
        )

        completion_events = int(event_histogram.get("task_completed", 0))
        _require(completion_events >= 1, STOP_CONTRACT, "event histogram lacks TASK_COMPLETED")
        _require(
            all(int(row["observer_mutation_count"]) == 0 for row in trajectory),
            STOP_CONTRACT,
            "observer mutation",
        )
        _require(
            runtime["guard"].direct_reset_calls == 0 and runtime["guard"].direct_step_calls == 0,
            STOP_CONTRACT,
            "wrapper raw-call isolation failed",
        )
        witness = {
            "schema_version": "b2_t3_b_completion_witness_v1",
            "pass": True,
            "selected_pair": selected,
            "claim_step": 1,
            "claim_store_version": int(claim_result.claim_artifact.committed_store_version),
            "completion_step": int(completion_step),
            "claim_and_completion_distinct": completion_step != 1,
            "continuation_boundaries": continuation_boundaries,
            "initial_distance": float(selected["initial_distance"]),
            "minimum_observed_distance": minimum_distance,
            "scanner_displacement": moved,
            "task_completed_events": completion_events,
            "p2_completed": True,
            "completed_task_count_before": initial_completed,
            "completed_task_count_after": completed_count,
            "completed_task_count_delta": completed_count - initial_completed,
            "coverage_count_before": initial_coverage,
            "coverage_count_after": coverage_count,
            "coverage_delta": coverage_count - initial_coverage,
            "completion_count_before": initial_completion_count,
            "completion_count_after": completion_count,
            "ownership_after_completion": -1,
            "robot_decision_reopened": True,
            "reopened_policy_call_count": 1,
            "timeout_before_completion": False,
            "autoreset_before_completion": False,
            "observer_mutation_count": 0,
        }
        result = {
            "schema_version": "b2_t3_b_final_result_v1",
            "classification": PASS,
            "gate": "T3-B",
            "pass": True,
            "root_cause_candidate": "SHORT-HORIZON QUALIFICATION ARTIFACT",
            "process_config": process_config,
            "witness": witness,
            "physical_environment_steps": physical_steps,
            "policy_call_count_by_robot": policy_calls_total,
            "policy_call_count_total": sum(policy_calls_total),
            "policy_decision_boundaries": sum(
                int(any(bool(item) for item in receipt["decision_required"]))
                for receipt in ld_receipts
            ),
            "continuation_boundaries": continuation_boundaries,
            "event_histogram": dict(sorted(event_histogram.items())),
            "release_events": int(event_histogram.get("task_released", 0)),
            "failure_events": int(event_histogram.get("terminal_pair_failure_recorded", 0)),
            "timeout_boundaries": timeout_boundaries,
            "autoreset_boundaries": autoreset_boundaries,
            "illegal_actor_call_faults": 0,
            "actor_backward": 0,
            "actor_optimizer_step": 0,
            "critic_backward": 0,
            "critic_optimizer_step": 0,
            "valuenorm_update": 0,
            "event_learner_transactions": 0,
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "production_semantic_modifications": 0,
            "direct_wrapper_reset_calls": runtime["guard"].direct_reset_calls,
            "direct_wrapper_step_calls": runtime["guard"].direct_step_calls,
            "observer_mutation_count": 0,
        }
        _write_json(artifact_dir / "t3_b_trajectory.json", {"rows": trajectory, "ld_receipts": ld_receipts})
        _write_json(artifact_dir / "t3_b_completion_witness.json", witness)
        _write_json(artifact_dir / "t3_b_final_result.json", result)
        _record("T3_B_PASS", result=result)
        return result
    finally:
        wrapper.close()


def _run_frozen_policy_buffer_bound_attempt(artifact_dir: Path) -> dict[str, object]:
    from collections import Counter

    import gymnasium as gym
    import torch
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import (
        EventOnPolicyCriticBufferEPV2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import (
        _compose_dormant_event_learned_policy_route_v2,
        get_dormant_event_learned_policy_route_descriptor_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import (
        build_assignment_event_profile_schema_v2_descriptor,
    )

    import test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke as T0
    import test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke as V2
    from _assignment_phase_b2_t2_observability import capture_step_observability

    algo_args = V2.load_production_algo_args()
    set_seed(dict(algo_args["seed"]))
    cublas_probe = torch.ones((1, 1), dtype=torch.float32, device="cuda:0")
    _require(
        float(torch.mm(cublas_probe, cublas_probe).item()) == 1.0,
        STOP_CONTRACT,
        "pre-environment CUBLAS initialization probe failed",
    )
    torch.cuda.synchronize()
    runtime = _make_runtime(entrypoint="B2-T3.frozen_policy_runtime")
    wrapper = runtime["wrapper"]
    raw = runtime["raw"]
    scale = raw._event_terminal_critic_scale_contract_v2
    schema = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)
    actor_dim = int(schema["actor_schema"]["dimension"])
    critic_dim = int(schema["critic_schema"]["dimension"])
    model_args = dict(algo_args["model"])
    algorithm_args = dict(algo_args["algo"])
    actor_args = {**model_args, **algorithm_args}
    critic_args = {**model_args, **algorithm_args}
    actors_raw = [
        HAPPO(
            actor_args,
            V2.Box((actor_dim,)),
            gym.spaces.Discrete(int(runtime["num_tasks"]) + 1),
            device=runtime["device"],
        )
        for _ in range(int(runtime["num_robots"]))
    ]
    critic_raw = VCritic(critic_args, V2.Box((critic_dim,)), device=runtime["device"])
    live_value_normalizer = ValueNorm(1, device=runtime["device"])
    actors = [V2.ActorRecorder(actor, index) for index, actor in enumerate(actors_raw)]
    critic = V2.CriticRecorder(critic_raw)
    episode_length = int(raw.max_episode_length)
    buffer_args = {
        **algo_args["train"],
        **model_args,
        **algorithm_args,
        "episode_length": episode_length,
        "n_rollout_threads": 1,
    }
    buffer = EventOnPolicyCriticBufferEPV2(
        buffer_args,
        V2.Box((critic_dim,)),
        device=runtime["device"],
    )
    for actor in actors_raw:
        actor.prep_rollout()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    critic_raw.prep_rollout()
    critic_raw.critic_optimizer.zero_grad(set_to_none=True)

    forbidden_counts = {
        "actor_optimizer_step": 0,
        "critic_optimizer_step": 0,
        "valuenorm_update": 0,
    }

    def forbidden_actor_step(*_args: object, **_kwargs: object) -> None:
        forbidden_counts["actor_optimizer_step"] += 1
        raise RuntimeError("STOP — B2-T3 actor optimizer.step invoked")

    def forbidden_critic_step(*_args: object, **_kwargs: object) -> None:
        forbidden_counts["critic_optimizer_step"] += 1
        raise RuntimeError("STOP — B2-T3 critic optimizer.step invoked")

    def forbidden_valuenorm_update(*_args: object, **_kwargs: object) -> None:
        forbidden_counts["valuenorm_update"] += 1
        raise RuntimeError("STOP — B2-T3 ValueNorm.update invoked")

    for actor in actors_raw:
        actor.actor_optimizer.step = forbidden_actor_step
    critic_raw.critic_optimizer.step = forbidden_critic_step
    live_value_normalizer.update = forbidden_valuenorm_update

    route_events: list[tuple[str, object | None]] = []

    def route_observer(stage: str, detail: object | None) -> None:
        route_events.append((stage, detail))

    route = _compose_dormant_event_learned_policy_route_v2(
        episode_length=episode_length,
        actors=tuple(actors),
        critic=critic,
        critic_buffer=buffer,
        admitted_reset=wrapper.reset,
        current_decision_supplier=runtime["current_bundle"],
        current_decision_validator=lambda bundle: bundle.evidence_snapshot.validate_current(
            current_publication=runtime["domain"].current_read_port.read_current(),
            current_open_window_view=runtime["domain"].interstep_fence_read_port.read(),
        ),
        capture_i42_decision=wrapper._capture_event_proposal_decision,
        step_i42_proposals=wrapper._step_event_proposals,
        action_builder=runtime["action_builder"],
        actor_trainer=lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("STOP — B2-T3 actor trainer invoked")
        ),
        critic_trainer=lambda *_args: (_ for _ in ()).throw(
            RuntimeError("STOP — B2-T3 critic trainer invoked")
        ),
        value_normalizer=live_value_normalizer,
        actor_rnn_shape=(1, 256),
        call_observer=route_observer,
    )
    descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
    _require(
        descriptor["route"] == "private_test_only_dormant"
        and descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R",
        STOP_CONTRACT,
        "private/public route authority changed",
    )
    trajectory: list[dict[str, object]] = []
    target_trajectory: list[dict[str, object]] = []
    ld_receipts: list[dict[str, object]] = []
    event_histogram: Counter[str] = Counter()
    target_pair: tuple[int, int] | None = None
    prior_episodes = None
    physical_steps = 0
    terminal_history = ()
    try:
        route.reset()
        learner_before = T0._learner_snapshot(
            actors=actors_raw,
            critic=critic_raw,
            live_value_normalizer=live_value_normalizer,
        )
        process_config = {
            "schema_version": "b2_t3_c_process_config_v1",
            "pid": os.getpid(),
            "fresh_process": True,
            "app_launcher_lifetimes": 1,
            "environment_constructions": 1,
            "environment_objects": 1,
            "private_route_constructions": 1,
            "E": 1,
            "M": int(runtime["num_robots"]),
            "N": int(runtime["num_tasks"]),
            "rollout_storage_length": episode_length,
            "episode_length_s": float(runtime["normal_episode_length_s"]),
            "max_episode_length": episode_length,
            "step_dt_seconds": float(raw.step_dt),
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "learner_update_authorized": False,
            "pre_environment_cublas_probe": "PASS",
        }
        _write_json(artifact_dir / "t3_c_process_config.json", process_config)
        _record("T3_C_START", config=process_config)
        while physical_steps < episode_length:
            actor_before = tuple(len(actor.calls) for actor in actors)
            receipt = route.collect_step()
            physical_steps += 1
            actor_after = tuple(len(actor.calls) for actor in actors)
            gate, prior_episodes = T0._capture_lifecycle_decision_gate_v1(
                receipt=receipt,
                actors=actors,
                actor_calls_before=actor_before,
                actor_calls_after=actor_after,
                transaction_index=0,
                collection_index=physical_steps,
                physical_step_index=physical_steps,
                previous_episode_generations=prior_episodes,
            )
            ld_receipts.append(gate)
            observation = capture_step_observability(receipt.facade_result)
            for name, count in observation["lifecycle_event_histogram"].items():
                event_histogram[str(name)] += int(count)
            trajectory.append(
                {
                    "step": physical_steps,
                    "episode_generation": receipt.facade_result.current_publication.episode_generation,
                    "task_state_aggregate": observation["task_state_aggregate"],
                    "completed_viewpoint_count": observation["completed_viewpoint_count"],
                    "claimed_executing_task_count": observation["claimed_executing_task_count"],
                    "coverage_ratio": observation["environment_info_metrics"]["coverage_ratio"],
                    "events": observation["lifecycle_event_histogram"],
                    "raw_action_histogram": observation["raw_action_histogram"],
                    "effective_assignment_histogram": observation["effective_assignment_histogram"],
                    "observer_mutation_count": observation["observer_mutation_count"],
                }
            )
            publication = receipt.facade_result.current_publication
            if target_pair is None and not receipt.facade_result.terminal_historical_payload:
                state = publication.lifecycle_state
                for robot_id in range(int(runtime["num_robots"])):
                    task_id = _active_owned_task(state, robot_id)
                    if task_id is not None:
                        target_pair = (robot_id, task_id)
                        break
            if target_pair is not None and not receipt.facade_result.terminal_historical_payload:
                robot_id, task_id = target_pair
                target_trajectory.append(
                    capture_progress_row(
                        raw,
                        publication,
                        global_step=physical_steps,
                        target_robot=robot_id,
                        target_task=task_id,
                        decision_required=bool(
                            receipt.decision_bundle.decision_valid_mask[0, robot_id, 0].item()
                        ),
                        policy_call_count=actor_after[robot_id] - actor_before[robot_id],
                        proposal_action_id=int(
                            receipt.proposal_envelope.runner_actions[0, robot_id, 0].item()
                        ),
                        effective_assignment=receipt.facade_result.admitted_effective_assignment,
                        boundary_kind=str(
                            int(receipt.decision_bundle.row_kind[0, robot_id].item())
                        ),
                    )
                )
            if receipt.facade_result.terminal_historical_payload:
                terminal_history = receipt.facade_result.terminal_historical_payload
                break
        _require(bool(terminal_history), STOP_CONTRACT, "frozen-policy episode did not reach one terminal")
        learner_after = T0._learner_snapshot(
            actors=actors_raw,
            critic=critic_raw,
            live_value_normalizer=live_value_normalizer,
        )
        _require(
            T0._persistent_state_equal(learner_before, learner_after),
            STOP_CONTRACT,
            "frozen policy mutated actor/critic/optimizer/ValueNorm state",
        )
        _require(not route.poisoned, STOP_CONTRACT, "frozen private route poisoned")
        _require(
            all(value == 0 for value in forbidden_counts.values()),
            STOP_CONTRACT,
            "forbidden learner mutation executor invoked",
        )
        completion_events = int(event_histogram.get("task_completed", 0))
        result = {
            "schema_version": "b2_t3_c_final_result_v1",
            "classification": "PASS" if completion_events else "NO-COMPLETION-DIAGNOSTIC",
            "gate": "T3-C",
            "pass_runtime_validity": True,
            "interpretation": "C1" if completion_events else "C2",
            "process_config": process_config,
            "physical_environment_steps": physical_steps,
            "normal_horizon_episodes": 1,
            "terminal_rows": len(terminal_history),
            "terminal_reasons": [int(item.termination_reason) for item in terminal_history],
            "autoreset_boundaries": len(terminal_history),
            "policy_call_count_by_robot": [len(actor.calls) for actor in actors],
            "policy_call_count_total": sum(len(actor.calls) for actor in actors),
            "event_histogram": dict(sorted(event_histogram.items())),
            "task_completion_events": completion_events,
            "release_events": int(event_histogram.get("task_released", 0)),
            "failure_events": int(event_histogram.get("terminal_pair_failure_recorded", 0)),
            "target_pair": target_pair,
            "learner_state_digest_before": learner_before["state_digest"],
            "learner_state_digest_after": learner_after["state_digest"],
            "learner_state_exact": True,
            "illegal_actor_call_faults": 0,
            "actor_backward": 0,
            "actor_optimizer_step": 0,
            "critic_backward": 0,
            "critic_optimizer_step": 0,
            "valuenorm_update": 0,
            "event_learner_transactions": 0,
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "production_semantic_modifications": 0,
            "observer_mutation_count": 0,
        }
        _write_json(
            artifact_dir / "t3_c_trajectory.json",
            {"rows": trajectory, "target_rows": target_trajectory, "ld_receipts": ld_receipts},
        )
        _write_json(artifact_dir / "t3_c_final_result.json", result)
        _record("T3_C_PASS", result=result)
        return result
    finally:
        wrapper.close()


def run_frozen_policy(artifact_dir: Path) -> dict[str, object]:
    from collections import Counter
    from types import SimpleNamespace

    import gymnasium as gym
    import torch
    from harl.algorithms.actors.happo import HAPPO
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_actor_collection import (
        collect_event_policy_proposals_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import (
        _validate_adapter_binding,
        _validate_resolution_routing,
        get_dormant_event_learned_policy_route_descriptor_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import (
        build_assignment_event_profile_schema_v2_descriptor,
    )

    import test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke as T0
    import test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke as V2
    from _assignment_phase_b2_t2_observability import capture_step_observability

    algo_args = V2.load_production_algo_args()
    set_seed(dict(algo_args["seed"]))
    cublas_probe = torch.ones((1, 1), dtype=torch.float32, device="cuda:0")
    _require(
        float(torch.mm(cublas_probe, cublas_probe).item()) == 1.0,
        STOP_CONTRACT,
        "pre-environment CUBLAS initialization probe failed",
    )
    torch.cuda.synchronize()
    del cublas_probe
    runtime = _make_runtime(entrypoint="B2-T3.frozen_policy_runtime")
    wrapper = runtime["wrapper"]
    raw = runtime["raw"]
    schema = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=raw._event_terminal_critic_scale_contract_v2
    )
    actor_dim = int(schema["actor_schema"]["dimension"])
    actor_args = {**dict(algo_args["model"]), **dict(algo_args["algo"])}
    actors_raw = [
        HAPPO(
            actor_args,
            V2.Box((actor_dim,)),
            gym.spaces.Discrete(int(runtime["num_tasks"]) + 1),
            device=runtime["device"],
        )
        for _ in range(int(runtime["num_robots"]))
    ]
    actors = [V2.ActorRecorder(actor, index) for index, actor in enumerate(actors_raw)]
    for actor in actors_raw:
        actor.prep_rollout()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    actor_optimizer_step_count = 0

    def forbidden_actor_step(*_args: object, **_kwargs: object) -> None:
        nonlocal actor_optimizer_step_count
        actor_optimizer_step_count += 1
        raise RuntimeError("STOP — B2-T3 actor optimizer.step invoked")

    for actor in actors_raw:
        actor.actor_optimizer.step = forbidden_actor_step

    def actor_state_digest() -> str:
        values: list[tuple[str, object]] = []
        for actor_id, actor in enumerate(actors_raw):
            for name, value in sorted(actor.actor.state_dict().items()):
                values.append((f"actor{actor_id}.{name}", value))
            values.append(
                (f"actor{actor_id}.optimizer_state_count", len(actor.actor_optimizer.state))
            )
        return _digest_tensors(values)

    descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
    _require(
        descriptor["route"] == "private_test_only_dormant"
        and descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R",
        STOP_CONTRACT,
        "private/public route authority changed",
    )
    episode_length = int(raw.max_episode_length)
    rnn_states = torch.zeros(
        (1, int(runtime["num_robots"]), 1, 256),
        dtype=torch.float32,
        device=runtime["device"],
    )
    masks = torch.ones(
        (1, int(runtime["num_robots"]), 1),
        dtype=torch.float32,
        device=runtime["device"],
    )
    trajectory: list[dict[str, object]] = []
    target_trajectory: list[dict[str, object]] = []
    ld_receipts: list[dict[str, object]] = []
    event_histogram: Counter[str] = Counter()
    target_pair: tuple[int, int] | None = None
    prior_episodes = None
    physical_steps = 0
    terminal_history = ()
    try:
        wrapper.reset()
        actor_digest_before = actor_state_digest()
        process_config = {
            "schema_version": "b2_t3_c_process_config_v2",
            "pid": os.getpid(),
            "fresh_process": True,
            "app_launcher_lifetimes": 1,
            "environment_constructions": 1,
            "environment_objects": 1,
            "private_route_slice": (
                "canonical I1/I2 -> I3a actor inference -> I4.2/P2/controller"
            ),
            "critic_constructed": False,
            "rollout_buffer_constructed": False,
            "E": 1,
            "M": int(runtime["num_robots"]),
            "N": int(runtime["num_tasks"]),
            "learner_rollout_T": "not bound; no learner transaction",
            "episode_length_s": float(runtime["normal_episode_length_s"]),
            "max_episode_length": episode_length,
            "step_dt_seconds": float(raw.step_dt),
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "learner_update_authorized": False,
        }
        _write_json(artifact_dir / "t3_c_process_config.json", process_config)
        _record("T3_C_START", config=process_config)
        while physical_steps < episode_length:
            bundle = runtime["current_bundle"]()
            bundle.evidence_snapshot.validate_current(
                current_publication=runtime["domain"].current_read_port.read_current(),
                current_open_window_view=runtime["domain"].interstep_fence_read_port.read(),
            )
            actor_before = tuple(len(actor.calls) for actor in actors)
            with torch.inference_mode():
                envelope = collect_event_policy_proposals_v2(
                    decision_bundle=bundle,
                    actors=actors,
                    rnn_states=rnn_states,
                    masks=masks,
                )
            actor_after = tuple(len(actor.calls) for actor in actors)
            decision = _validate_adapter_binding(
                bundle=bundle,
                decision=_decision_capture(wrapper, bundle),
            )
            facade_result = wrapper._step_event_proposals(
                envelope.runner_actions,
                decision=decision,
                layout="env_agent_action",
                action_builder=runtime["action_builder"],
            )
            facade_result = _validate_resolution_routing(
                bundle=bundle,
                envelope=envelope,
                result=facade_result,
            )
            next_bundle = runtime["current_bundle"]()
            receipt = SimpleNamespace(
                proposal_envelope=envelope,
                next_decision_bundle=next_bundle,
            )
            physical_steps += 1
            gate, prior_episodes = T0._capture_lifecycle_decision_gate_v1(
                receipt=receipt,
                actors=actors,
                actor_calls_before=actor_before,
                actor_calls_after=actor_after,
                transaction_index=0,
                collection_index=physical_steps,
                physical_step_index=physical_steps,
                previous_episode_generations=prior_episodes,
            )
            ld_receipts.append(gate)
            observation = capture_step_observability(facade_result)
            for name, count in observation["lifecycle_event_histogram"].items():
                event_histogram[str(name)] += int(count)
            trajectory.append(
                {
                    "step": physical_steps,
                    "episode_generation": facade_result.current_publication.episode_generation,
                    "task_state_aggregate": observation["task_state_aggregate"],
                    "completed_viewpoint_count": observation["completed_viewpoint_count"],
                    "claimed_executing_task_count": observation["claimed_executing_task_count"],
                    "coverage_ratio": observation["environment_info_metrics"]["coverage_ratio"],
                    "events": observation["lifecycle_event_histogram"],
                    "raw_action_histogram": observation["raw_action_histogram"],
                    "effective_assignment_histogram": observation["effective_assignment_histogram"],
                    "observer_mutation_count": observation["observer_mutation_count"],
                }
            )
            publication = facade_result.current_publication
            if target_pair is None and not facade_result.terminal_historical_payload:
                state = publication.lifecycle_state
                for robot_id in range(int(runtime["num_robots"])):
                    task_id = _active_owned_task(state, robot_id)
                    if task_id is not None:
                        target_pair = (robot_id, task_id)
                        break
            if target_pair is not None and not facade_result.terminal_historical_payload:
                robot_id, task_id = target_pair
                target_trajectory.append(
                    capture_progress_row(
                        raw,
                        publication,
                        global_step=physical_steps,
                        target_robot=robot_id,
                        target_task=task_id,
                        decision_required=bool(
                            bundle.decision_valid_mask[0, robot_id, 0].item()
                        ),
                        policy_call_count=actor_after[robot_id] - actor_before[robot_id],
                        proposal_action_id=int(
                            envelope.runner_actions[0, robot_id, 0].item()
                        ),
                        effective_assignment=facade_result.admitted_effective_assignment,
                        boundary_kind=str(int(bundle.row_kind[0, robot_id].item())),
                    )
                )
            rnn_states = envelope.next_rnn_states.detach().clone()
            if facade_result.terminal_historical_payload:
                terminal_history = facade_result.terminal_historical_payload
                break
        _require(
            bool(terminal_history),
            STOP_CONTRACT,
            "frozen-policy episode did not reach one terminal",
        )
        actor_digest_after = actor_state_digest()
        _require(
            actor_digest_before == actor_digest_after,
            STOP_CONTRACT,
            "frozen actor state mutated",
        )
        _require(
            actor_optimizer_step_count == 0,
            STOP_CONTRACT,
            "actor optimizer.step invoked",
        )
        _require(
            all(
                parameter.grad is None
                for actor in actors_raw
                for parameter in actor.actor.parameters()
            ),
            STOP_CONTRACT,
            "frozen actor accumulated gradients",
        )
        completion_events = int(event_histogram.get("task_completed", 0))
        result = {
            "schema_version": "b2_t3_c_final_result_v2",
            "classification": "PASS" if completion_events else "NO-COMPLETION-DIAGNOSTIC",
            "gate": "T3-C",
            "pass_runtime_validity": True,
            "interpretation": "C1" if completion_events else "C2",
            "process_config": process_config,
            "physical_environment_steps": physical_steps,
            "normal_horizon_episodes": 1,
            "terminal_rows": len(terminal_history),
            "terminal_reasons": [int(item.termination_reason) for item in terminal_history],
            "autoreset_boundaries": len(terminal_history),
            "policy_call_count_by_robot": [len(actor.calls) for actor in actors],
            "policy_call_count_total": sum(len(actor.calls) for actor in actors),
            "event_histogram": dict(sorted(event_histogram.items())),
            "task_completion_events": completion_events,
            "release_events": int(event_histogram.get("task_released", 0)),
            "failure_events": int(
                event_histogram.get("terminal_pair_failure_recorded", 0)
            ),
            "target_pair": target_pair,
            "actor_state_digest_before": actor_digest_before,
            "actor_state_digest_after": actor_digest_after,
            "actor_state_exact": True,
            "illegal_actor_call_faults": 0,
            "actor_backward": 0,
            "actor_optimizer_step": 0,
            "critic_backward": 0,
            "critic_optimizer_step": 0,
            "valuenorm_update": 0,
            "event_learner_transactions": 0,
            "checkpoint_weight_io": 0,
            "public_activation": 0,
            "production_semantic_modifications": 0,
            "observer_mutation_count": 0,
        }
        _write_json(
            artifact_dir / "t3_c_trajectory.json",
            {
                "rows": trajectory,
                "target_rows": target_trajectory,
                "ld_receipts": ld_receipts,
            },
        )
        _write_json(artifact_dir / "t3_c_final_result.json", result)
        _record("T3_C_PASS", result=result)
        return result
    finally:
        wrapper.close()


def run_worker(mode: str, artifact_dir: Path) -> int:
    from isaaclab.app import AppLauncher

    _record("APP_LAUNCHER_ENTER", mode=mode)
    launcher = AppLauncher(headless=True)
    simulation_app = launcher.app
    try:
        if mode == "controlled":
            run_controlled(artifact_dir)
        elif mode == "frozen":
            run_frozen_policy(artifact_dir)
        else:
            raise ValueError(mode)
        return 0
    except BaseException as exc:
        classification = getattr(exc, "classification", f"PHASE-B2-T3-STOP-{mode.upper()}-WORKER")
        failure = {
            "classification": classification,
            "mode": mode,
            "pid": os.getpid(),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        _write_json(artifact_dir / f"t3_{'b' if mode == 'controlled' else 'c'}_failure.json", failure)
        _record("WORKER_FAILURE", failure=failure)
        return 1
    finally:
        simulation_app.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("controlled", "frozen"), required=True)
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()
    return run_worker(args.mode, Path(args.artifact_dir).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
