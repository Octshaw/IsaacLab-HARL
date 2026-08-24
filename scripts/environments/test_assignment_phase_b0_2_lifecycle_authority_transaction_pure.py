"""Pure B0-2 lifecycle-authority transaction regressions.

The suite loads only the canonical profile, transition, event, B0-1 runtime,
and B0-2 transaction-runtime sources through namespace-only package
placeholders.  It does not run task discovery, AppLauncher, Isaac, an
environment, a wrapper, a resolver, HARL, training, playback, or evaluation.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import FrozenInstanceError
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import sys
from threading import Event, Thread
from types import MappingProxyType, ModuleType
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_TASK_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PROFILE_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
EVENT_PATH = SCAN_TASK_SOURCE / "assignment_event_contract.py"
B01_RUNTIME_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_authority_runtime.py"
B02_RUNTIME_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_transaction_runtime.py"

PROFILE_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
TRANSITION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
EVENT_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract"
B01_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_authority_runtime"
)
B02_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transaction_runtime"
)

DEVICE = torch.device("cpu")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_namespace_packages() -> None:
    package_paths = (
        ("isaaclab_tasks", TASKS_SOURCE),
        ("isaaclab_tasks.direct", DIRECT_SOURCE),
        ("isaaclab_tasks.direct.scan_mobile_manipulator", SCAN_TASK_SOURCE),
    )
    for name, path in package_paths:
        existing = sys.modules.get(name)
        if existing is not None:
            existing_path = tuple(getattr(existing, "__path__", ()))
            _assert(str(path) in existing_path, f"unexpected package at {name}")
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_canonical(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        _assert(
            Path(str(getattr(existing, "__file__", ""))).resolve() == path.resolve(),
            f"canonical key {name} points to another source",
        )
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load canonical source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace_packages()
PROFILE = _load_canonical(PROFILE_MODULE, PROFILE_PATH)
TRANSITION = _load_canonical(TRANSITION_MODULE, TRANSITION_PATH)
EVENT = _load_canonical(EVENT_MODULE, EVENT_PATH)
B01 = _load_canonical(B01_RUNTIME_MODULE, B01_RUNTIME_PATH)
B02 = _load_canonical(B02_RUNTIME_MODULE, B02_RUNTIME_PATH)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason
EventType = EVENT.LifecycleEventType


def _profiles() -> tuple[Any, tuple[Any, ...]]:
    origin = PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    event = PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        origin,
    )
    existing = tuple(
        PROFILE.resolve_assignment_profile(name, origin)
        for name in (
            PROFILE.AssignmentProfileName.LEGACY,
            PROFILE.AssignmentProfileName.LIFECYCLE_CONTRACT_C,
            PROFILE.AssignmentProfileName.LIFECYCLE_ABLATION,
            PROFILE.AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
        )
    )
    return event, existing


def _i(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=DEVICE)


def _b(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.bool, device=DEVICE)


def _expect_error(
    exception_type: type[BaseException],
    operation: Callable[[], Any],
    *,
    code: str | None = None,
) -> BaseException:
    try:
        operation()
    except exception_type as exc:
        if code is not None:
            _assert(
                getattr(exc, "failure_code", None) == code,
                f"expected failure_code={code}, got {getattr(exc, 'failure_code', None)}",
            )
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _derive_robot_state(
    task_state: torch.Tensor,
    ownership: torch.Tensor,
    *,
    num_robots: int,
) -> torch.Tensor:
    active = (
        (task_state == int(TaskState.CLAIMED))
        | (task_state == int(TaskState.NAVIGATING))
        | (task_state == int(TaskState.ALIGNING))
    )
    robot = torch.full(
        (task_state.shape[0], num_robots),
        int(RobotState.NEEDS_ASSIGNMENT),
        dtype=torch.int64,
        device=DEVICE,
    )
    for row in range(int(task_state.shape[0])):
        for robot_id in range(num_robots):
            if bool((active[row] & (ownership[row] == robot_id)).any().item()):
                robot[row, robot_id] = int(RobotState.EXECUTING)
    return robot


def _store(
    profile: Any,
    *,
    env_ids: tuple[int, ...],
    task_state: Any,
    ownership: Any,
    robot_state: Any | None = None,
    failed: Any | None = None,
    completion_count: Any | None = None,
    termination_reason: Any | None = None,
    device: torch.device = DEVICE,
) -> Any:
    task = task_state if type(task_state) is torch.Tensor else _i(task_state)
    owner = ownership if type(ownership) is torch.Tensor else _i(ownership)
    env_count, num_tasks = tuple(task.shape)
    if robot_state is None:
        maximum = int(owner.max().item()) if bool((owner >= 0).any().item()) else 0
        num_robots = max(2, maximum + 1)
        robot = _derive_robot_state(task, owner, num_robots=num_robots)
    else:
        robot = robot_state if type(robot_state) is torch.Tensor else _i(robot_state)
        num_robots = int(robot.shape[1])
    failed_tensor = (
        torch.zeros((env_count, num_robots, num_tasks), dtype=torch.bool, device=DEVICE)
        if failed is None
        else (failed if type(failed) is torch.Tensor else _b(failed))
    )
    counts = (
        torch.zeros((env_count, num_robots), dtype=torch.int64, device=DEVICE)
        if completion_count is None
        else (
            completion_count
            if type(completion_count) is torch.Tensor
            else _i(completion_count)
        )
    )
    reasons = (
        torch.zeros(env_count, dtype=torch.int64, device=DEVICE)
        if termination_reason is None
        else (
            termination_reason
            if type(termination_reason) is torch.Tensor
            else _i(termination_reason)
        )
    )
    return B02.LifecycleStateStore(
        profile,
        device=device,
        env_id=_i(env_ids),
        task_state=task,
        robot_state=robot,
        ownership=owner,
        cumulative_failed_pairs=failed_tensor,
        completion_count=counts,
        termination_reason=reasons,
    )


def _stack(
    *,
    env_ids: tuple[int, ...],
    task_state: Any,
    ownership: Any,
    robot_state: Any | None = None,
    failed: Any | None = None,
    completion_count: Any | None = None,
    termination_reason: Any | None = None,
    control: Any | None = None,
) -> dict[str, Any]:
    profile, _ = _profiles()
    store = _store(
        profile,
        env_ids=env_ids,
        task_state=task_state,
        ownership=ownership,
        robot_state=robot_state,
        failed=failed,
        completion_count=completion_count,
        termination_reason=termination_reason,
    )
    clock = B01.LifecycleGenerationClock(profile, env_ids=_i(env_ids))
    clock.advance_episode(_i(env_ids))
    coordinator = B02.LifecycleAuthorityTransactionCoordinator(
        profile,
        state_store=store,
        generation_clock=clock,
        _test_control=control,
    )
    return {
        "profile": profile,
        "store": store,
        "clock": clock,
        "coordinator": coordinator,
        "producer": B01.EnvironmentExecutionFactsProducer(profile),
    }


def _facts(
    stack: dict[str, Any],
    snapshot: Any,
    contexts: tuple[Any, ...],
    *,
    completion: torch.Tensor | None = None,
    failure: torch.Tensor | None = None,
    release: torch.Tensor | None = None,
    unavailable: torch.Tensor | None = None,
    recovered: torch.Tensor | None = None,
    physical_terminated: torch.Tensor | None = None,
    physical_truncated: torch.Tensor | None = None,
    time_limit: torch.Tensor | None = None,
    bad_transition: torch.Tensor | None = None,
    invalid_completion_dtype: bool = False,
) -> Any:
    env_count = snapshot.num_envs
    num_robots = snapshot.num_robots
    num_tasks = snapshot.num_tasks
    zero_pairs = torch.zeros(
        (env_count, num_robots, num_tasks), dtype=torch.bool, device=DEVICE
    )
    zero_robots = torch.zeros(
        (env_count, num_robots), dtype=torch.bool, device=DEVICE
    )
    zero_env = torch.zeros(env_count, dtype=torch.bool, device=DEVICE)
    completion_value = zero_pairs if completion is None else completion
    if invalid_completion_dtype:
        completion_value = completion_value.to(dtype=torch.int64)
    time_value = zero_env if time_limit is None else time_limit
    bad_value = zero_env if bad_transition is None else bad_transition
    truncated_value = (
        (time_value | bad_value)
        if physical_truncated is None
        else physical_truncated
    )
    transition_input = B01.ExecutionTransitionInput(
        device=DEVICE,
        env_id=snapshot.env_id,
        episode_generation=_i([context.episode_generation for context in contexts]),
        transition_generation=_i(
            [context.transition_generation for context in contexts]
        ),
        physical_terminated=(
            zero_env if physical_terminated is None else physical_terminated
        ),
        physical_truncated=truncated_value,
        time_limit_reached=time_value,
        bad_transition=bad_value,
        completion_signals=completion_value,
        terminal_pair_failure_signals=(zero_pairs if failure is None else failure),
        forced_release_signals=zero_pairs if release is None else release,
        robot_unavailable_signals=(
            zero_robots if unavailable is None else unavailable
        ),
        robot_recovered_signals=zero_robots if recovered is None else recovered,
        coverage_before_transition=torch.zeros(
            (env_count, num_tasks), dtype=torch.bool, device=DEVICE
        ),
        task_state_before_transition=snapshot.task_state,
        robot_state_before_transition=snapshot.robot_state,
        ownership_before_transition=snapshot.ownership,
    )
    return stack["producer"].build_facts(transition_input)


def _pending(
    stack: dict[str, Any],
    **signals: Any,
) -> tuple[Any, tuple[Any, ...], Any]:
    snapshot = stack["coordinator"].read_published_view().lifecycle_state
    contexts = stack["clock"].request_transition_candidate(snapshot.env_id)
    return snapshot, contexts, _facts(stack, snapshot, contexts, **signals)


def _ledger_counts(coordinator: Any) -> tuple[int, int, int]:
    audit = coordinator._ledger.snapshot()
    return (
        int(audit["issued_receipt_count"]),
        int(audit["finalized_receipt_count"]),
        len(audit["consumed_tokens"]),
    )


def _event_signature(event: Any) -> tuple[Any, ...]:
    payload = event.payload.to_mapping()
    return (
        event.event_id,
        event.causal_source.value,
        event.event_type.value,
        event.env_id,
        event.episode_generation,
        event.transition_generation,
        event.ordinal,
        event.robot_id,
        event.task_id,
        event.trigger_eligible,
        event.facts_consume_token,
        event.authority_id.value,
        tuple(payload.items()),
    )


def _private_replace_store_state(
    store: Any,
    *,
    task_state: torch.Tensor | None = None,
    robot_state: torch.Tensor | None = None,
    ownership: torch.Tensor | None = None,
    failed: torch.Tensor | None = None,
    completion_count: torch.Tensor | None = None,
    termination_reason: torch.Tensor | None = None,
) -> None:
    """Install an unreachable invariant fixture without a public test hook."""

    with store._lock:
        current = store._state
        store._state = B02._LifecycleStoreState(
            version=current.version,
            task_state=current.task_state if task_state is None else task_state,
            robot_state=current.robot_state if robot_state is None else robot_state,
            ownership=current.ownership if ownership is None else ownership,
            cumulative_failed_pairs=(
                current.cumulative_failed_pairs if failed is None else failed
            ),
            completion_count=(
                current.completion_count
                if completion_count is None
                else completion_count
            ),
            termination_reason=(
                current.termination_reason
                if termination_reason is None
                else termination_reason
            ),
        )


def _logger_state() -> tuple[Any, ...]:
    root = logging.getLogger()
    named = tuple(
        sorted(
            (
                name,
                type(value).__name__,
                getattr(value, "level", None),
                tuple(id(handler) for handler in getattr(value, "handlers", ())),
                getattr(value, "propagate", None),
                getattr(value, "disabled", None),
            )
            for name, value in logging.Logger.manager.loggerDict.items()
        )
    )
    return root.level, tuple(id(h) for h in root.handlers), root.disabled, named


def _file_inventory() -> tuple[tuple[str, int], ...]:
    roots = (SCAN_TASK_SOURCE, REPO_ROOT / "scripts" / "environments")
    return tuple(
        sorted(
            (
                str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                path.stat().st_size,
            )
            for root in roots
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def test_t1_state_store_initialization_invariants() -> dict[str, Any]:
    event, _ = _profiles()
    task = _i(
        [
            [TaskState.AVAILABLE, TaskState.CLAIMED, TaskState.COMPLETED, TaskState.TEAM_INFEASIBLE],
            [TaskState.NAVIGATING, TaskState.ALIGNING, TaskState.AVAILABLE, TaskState.COMPLETED],
        ]
    )
    owner = _i([[-1, 0, -1, -1], [1, 2, -1, -1]])
    robot = _i(
        [
            [RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT, RobotState.WAITING_FOR_TASK],
            [RobotState.WAITING_FOR_TASK, RobotState.EXECUTING, RobotState.EXECUTING],
        ]
    )
    failed = torch.zeros((2, 3, 4), dtype=torch.bool, device=DEVICE)
    failed[0, :, 3] = True
    failed[0, 1, 0] = True
    failed[1, 0, 0] = True
    counts = _i([[2, 0, 1], [4, 3, 2]])
    valid = _store(
        event,
        env_ids=(100, 101),
        task_state=task,
        ownership=owner,
        robot_state=robot,
        failed=failed,
        completion_count=counts,
    )
    snapshot = valid.snapshot()
    _assert(snapshot.store_version == 0, "initial store version changed")
    _assert(torch.equal(snapshot.task_state, task), "valid task state changed")
    _assert(torch.equal(snapshot.completion_count, counts), "counts changed")

    invalid_cases: list[tuple[str, dict[str, Any]]] = []

    def case(name: str, **updates: Any) -> None:
        values = {
            "task_state": task.clone(),
            "ownership": owner.clone(),
            "robot_state": robot.clone(),
            "failed": failed.clone(),
            "completion_count": counts.clone(),
        }
        values.update(updates)
        invalid_cases.append((name, values))

    value = task.clone(); value[0, 1] = int(TaskState.AVAILABLE)
    case("available_owned", task_state=value)
    value = task.clone(); value[0, 1] = int(TaskState.COMPLETED)
    case("completed_owned", task_state=value)
    value = task.clone(); value[0, 1] = int(TaskState.TEAM_INFEASIBLE)
    failed_team_owned = failed.clone(); failed_team_owned[0, :, 1] = True
    case("team_owned", task_state=value, failed=failed_team_owned)
    value = owner.clone(); value[0, 1] = -1
    case("active_unowned", ownership=value)
    value = owner.clone(); value[1, 1] = 1
    robots = robot.clone(); robots[1, 2] = int(RobotState.NEEDS_ASSIGNMENT)
    case("robot_two_active_tasks", ownership=value, robot_state=robots)
    robots = robot.clone(); robots[1, 0] = int(RobotState.EXECUTING)
    case("executing_without_task", robot_state=robots)
    robots = robot.clone(); robots[0, 0] = int(RobotState.NEEDS_ASSIGNMENT)
    case("needs_with_owned_task", robot_state=robots)
    value = failed.clone(); value[0, 0, 1] = True
    case("active_owner_failed", failed=value)
    value = failed.clone(); value[0, :, 0] = True
    case("team_equation_missing_state", failed=value)
    value = failed.clone(); value[0, 2, 3] = False
    case("team_state_without_equation", failed=value)
    value = counts.clone(); value[0, 0] = -1
    case("negative_completion_count", completion_count=value)
    value = task.clone(); value[0, 0] = 99
    case("task_enum", task_state=value)
    value = robot.clone(); value[0, 1] = 99
    case("robot_enum", robot_state=value)

    for name, values in invalid_cases:
        _expect_error(
            B02.LifecycleStateRuntimeError,
            lambda values=values: _store(
                event,
                env_ids=(110, 111),
                **values,
            ),
        )
    _expect_error(
        B02.LifecycleStateRuntimeError,
        lambda: _store(
            event,
            env_ids=(112, 113),
            task_state=task.to(torch.int32),
            ownership=owner,
            robot_state=robot,
            failed=failed,
            completion_count=counts,
        ),
        code="dtype",
    )
    _expect_error(
        B02.LifecycleStateRuntimeError,
        lambda: _store(
            event,
            env_ids=(114, 115),
            task_state=task,
            ownership=owner[:, :3],
            robot_state=robot,
            failed=failed,
            completion_count=counts,
        ),
        code="shape",
    )
    _expect_error(
        B02.LifecycleStateRuntimeError,
        lambda: _store(
            event,
            env_ids=(116, 117),
            task_state=task,
            ownership=owner,
            robot_state=robot,
            failed=failed,
            completion_count=counts,
            device=torch.device("meta"),
        ),
        code="device",
    )
    return {
        "valid_rows": 2,
        "invalid_semantic_cases": len(invalid_cases),
        "shape_dtype_device_rejections": 3,
        "initial_version": snapshot.store_version,
    }


def test_t2_immutable_versioned_snapshot() -> dict[str, Any]:
    event, _ = _profiles()
    task_source = _i([[TaskState.CLAIMED, TaskState.AVAILABLE]])
    owner_source = _i([[0, -1]])
    store = _store(
        event,
        env_ids=(200,),
        task_state=task_source,
        ownership=owner_source,
        robot_state=_i([[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]]),
    )
    task_source[0, 0] = int(TaskState.COMPLETED)
    owner_source[0, 0] = -1
    first = store.snapshot()
    _assert(first.store_version == 0, "snapshot did not start at version zero")
    _assert(int(first.task_state[0, 0].item()) == int(TaskState.CLAIMED), "source aliased store")
    clone = first.task_state
    clone[0, 0] = int(TaskState.COMPLETED)
    _assert(int(store.snapshot().task_state[0, 0].item()) == int(TaskState.CLAIMED), "snapshot accessor aliased store")
    _expect_error(FrozenInstanceError, lambda: setattr(first, "store_version", 8))

    stack = _stack(
        env_ids=(201,),
        task_state=[[TaskState.CLAIMED, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    before = stack["coordinator"].read_published_view().lifecycle_state
    contexts = stack["clock"].request_transition_candidate(before.env_id)
    rejected_facts = _facts(
        stack,
        before,
        contexts,
        physical_truncated=_b([True]),
    )
    _expect_error(
        B02.LifecycleAuthorityRuntimeError,
        lambda: stack["coordinator"].transact(
            facts=rejected_facts,
            transition_contexts=contexts,
        ),
        code="unmappable_physical_truncation",
    )
    _assert(stack["store"]._state.version == 0, "failed transaction incremented version")
    facts = _facts(stack, before, contexts)
    published = stack["coordinator"].transact(
        facts=facts,
        transition_contexts=contexts,
    )
    _assert(published.store_version == 1, "successful swap did not increment once")
    _assert(before.store_version == 0, "retained historical snapshot changed")
    _assert(stack["store"]._state.version == 1, "live version differs")
    return {
        "source_alias_isolated": True,
        "accessor_alias_isolated": True,
        "snapshot_frozen": True,
        "failed_version_delta": 0,
        "success_version_delta": 1,
    }


def test_t3_all_32_simultaneous_cause_combinations() -> dict[str, Any]:
    valid_count = 0
    invalid_count = 0
    checked_special: set[str] = set()
    for mask in range(32):
        complete = bool(mask & 1)
        fail = bool(mask & 2)
        release = bool(mask & 4)
        unavailable = bool(mask & 8)
        recovered = bool(mask & 16)
        stack = _stack(
            env_ids=(3000 + mask,),
            task_state=[[TaskState.CLAIMED, TaskState.AVAILABLE]],
            ownership=[[0, -1]],
            robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
        )
        snapshot = stack["coordinator"].read_published_view().lifecycle_state
        contexts = stack["clock"].request_transition_candidate(snapshot.env_id)
        pair_c = torch.zeros((1, 2, 2), dtype=torch.bool, device=DEVICE)
        pair_f = pair_c.clone(); pair_r = pair_c.clone()
        robot_u = torch.zeros((1, 2), dtype=torch.bool, device=DEVICE)
        robot_rc = robot_u.clone()
        pair_c[0, 0, 0] = complete
        pair_f[0, 0, 0] = fail
        pair_r[0, 0, 0] = release
        robot_u[0, 0] = unavailable
        robot_rc[0, 0] = recovered
        valid = not (complete and fail) and not recovered
        try:
            facts = _facts(
                stack,
                snapshot,
                contexts,
                completion=pair_c,
                failure=pair_f,
                release=pair_r,
                unavailable=robot_u,
                recovered=robot_rc,
            )
            view = stack["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            )
        except (TRANSITION.AssignmentTransitionContractError, B02.LifecycleAuthorityRuntimeError):
            _assert(not valid, f"valid matrix row rejected: {mask:05b}")
            invalid_count += 1
            _assert(_ledger_counts(stack["coordinator"]) == (0, 0, 0), "invalid row consumed")
            _assert(stack["store"]._state.version == 0, "invalid row swapped")
            continue
        _assert(valid, f"invalid matrix row accepted: {mask:05b}")
        valid_count += 1
        result = view.result
        _assert(result is not None, "valid matrix row has no result")
        expected_completed = complete
        expected_released = (not complete) and (fail or release or unavailable)
        _assert(bool(result.completed_tasks[0, 0].item()) == expected_completed, "completed equation changed")
        _assert(bool(result.released_tasks[0, 0].item()) == expected_released, "released equation changed")
        _assert(bool(result.new_failed_pairs[0, 0, 0].item()) == fail, "new failure equation changed")
        expected_task = (
            TaskState.COMPLETED
            if complete
            else TaskState.AVAILABLE
            if expected_released
            else TaskState.CLAIMED
        )
        expected_owner = -1 if (complete or expected_released) else 0
        expected_robot = (
            RobotState.UNAVAILABLE
            if unavailable
            else RobotState.NEEDS_ASSIGNMENT
            if (complete or expected_released)
            else RobotState.EXECUTING
        )
        _assert(int(result.updated_task_state[0, 0].item()) == int(expected_task), "task outcome changed")
        _assert(int(result.updated_ownership[0, 0].item()) == expected_owner, "owner outcome changed")
        _assert(int(result.updated_robot_state[0, 0].item()) == int(expected_robot), "robot outcome changed")
        event_types = tuple(event.event_type for event in result.lifecycle_events)
        expected_types: list[Any] = []
        if complete:
            expected_types.append(EventType.TASK_COMPLETED)
        if expected_released:
            expected_types.append(EventType.TASK_RELEASED)
        if fail:
            expected_types.append(EventType.TERMINAL_PAIR_FAILURE_RECORDED)
        if unavailable:
            expected_types.append(EventType.ROBOT_BECAME_UNAVAILABLE)
        if expected_robot is RobotState.NEEDS_ASSIGNMENT:
            expected_types.append(EventType.ROBOT_NEEDS_ASSIGNMENT)
        _assert(event_types == tuple(expected_types), f"event set/order changed for {mask:05b}")
        label = "+".join(
            name for name, enabled in (("C", complete), ("F", fail), ("R", release), ("U", unavailable)) if enabled
        ) or "none"
        if label in {"C+R", "C+U", "C+R+U", "F+R", "F+U", "F+R+U", "R+U"}:
            checked_special.add(label)
    _assert(valid_count == 12 and invalid_count == 20, "32-row validity matrix changed")
    _assert(
        checked_special == {"C+R", "C+U", "C+R+U", "F+R", "F+U", "F+R+U", "R+U"},
        "special simultaneous rows were not covered",
    )
    return {
        "rows": 32,
        "valid": valid_count,
        "invalid": invalid_count,
        "special_rows": sorted(checked_special),
    }


def test_t4_c1_active_owner_failed_invariant() -> dict[str, Any]:
    checked: list[str] = []
    for index, phase in enumerate((TaskState.CLAIMED, TaskState.NAVIGATING, TaskState.ALIGNING)):
        stack = _stack(
            env_ids=(4000 + index,),
            task_state=[[phase, TaskState.AVAILABLE]],
            ownership=[[0, -1]],
            robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
        )
        failed = stack["coordinator"].read_published_view().lifecycle_state.cumulative_failed_pairs
        failed[0, 0, 0] = True
        _private_replace_store_state(stack["store"], failed=failed)
        invalid_snapshot = stack["store"]._snapshot_for_lifecycle(
            writer_capability=stack["coordinator"]._writer_capability,
        )
        contexts = stack["clock"].request_transition_candidate(invalid_snapshot.env_id)
        facts = _facts(stack, invalid_snapshot, contexts)
        initial_view = stack["coordinator"]._published_view
        _expect_error(
            B02.LifecycleAuthorityRuntimeError,
            lambda: stack["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            ),
            code="active_owner_failed_pair",
        )
        _assert(_ledger_counts(stack["coordinator"]) == (0, 0, 0), "C1 failure consumed")
        _assert(stack["store"]._state.version == 0, "C1 failure swapped")
        clock_row = stack["clock"].snapshot(invalid_snapshot.env_id)[0]
        _assert(clock_row.transition_generation == -1, "C1 failure committed generation")
        _assert(stack["coordinator"]._published_view is initial_view, "C1 failure published")
        _assert(not stack["coordinator"].poisoned, "prevalidation failure poisoned coordinator")
        checked.append(phase.name)
    return {
        "phases": checked,
        "other_robot_feasible": True,
        "downstream_counts": [0, 0, 0],
    }


def test_t5_completion_attribution() -> dict[str, Any]:
    rows: list[str] = []
    for index, (release, unavailable) in enumerate(((False, False), (True, False), (False, True), (True, True))):
        stack = _stack(
            env_ids=(5000 + index,),
            task_state=[[TaskState.ALIGNING, TaskState.AVAILABLE]],
            ownership=[[0, -1]],
            robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
            completion_count=[[7, 3]],
        )
        c = torch.zeros((1, 2, 2), dtype=torch.bool, device=DEVICE); c[0, 0, 0] = True
        r = torch.zeros_like(c); r[0, 0, 0] = release
        u = torch.zeros((1, 2), dtype=torch.bool, device=DEVICE); u[0, 0] = unavailable
        snapshot, contexts, facts = _pending(stack, completion=c, release=r, unavailable=u)
        view = stack["coordinator"].transact(facts=facts, transition_contexts=contexts)
        _assert(view.result is not None, "completion result missing")
        _assert(view.lifecycle_state.completion_count.tolist() == [[8, 3]], "completion credited wrong robot")
        _assert(not bool(view.result.released_tasks[0, 0].item()), "completion was also released")
        rows.append("C" + ("+R" if release else "") + ("+U" if unavailable else ""))

    stack = _stack(
        env_ids=(5010,),
        task_state=[[TaskState.CLAIMED, TaskState.NAVIGATING, TaskState.AVAILABLE]],
        ownership=[[0, 1, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.EXECUTING]],
        completion_count=[[2, 5]],
    )
    c = torch.zeros((1, 2, 3), dtype=torch.bool, device=DEVICE)
    c[0, 0, 0] = True; c[0, 1, 1] = True
    snapshot, contexts, facts = _pending(stack, completion=c)
    view = stack["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(view.lifecycle_state.completion_count.tolist() == [[3, 6]], "multi-pair attribution crossed robots")
    return {
        "simultaneous_rows": rows,
        "multi_robot_multi_task": True,
        "coverage_or_reward_reconstruction": False,
    }


def test_t6_failure_and_team_infeasible() -> dict[str, Any]:
    nonlast = _stack(
        env_ids=(6000,),
        task_state=[[TaskState.NAVIGATING, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    failure = torch.zeros((1, 2, 2), dtype=torch.bool, device=DEVICE); failure[0, 0, 0] = True
    snapshot, contexts, facts = _pending(nonlast, failure=failure)
    view = nonlast["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(bool(view.result.new_failed_pairs[0, 0, 0].item()), "new failure not recorded")
    _assert(int(view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.AVAILABLE), "nonlast failure became TEAM")

    prior = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); prior[0, 1, 0] = True
    last = _stack(
        env_ids=(6001,),
        task_state=[[TaskState.CLAIMED]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        failed=prior,
    )
    failure = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); failure[0, 0, 0] = True
    snapshot, contexts, facts = _pending(last, failure=failure)
    view = last["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(int(view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.TEAM_INFEASIBLE), "last failure did not produce TEAM")
    _assert(bool(view.result.new_team_infeasible_tasks[0, 0].item()), "TEAM edge missing")
    _assert(int(view.lifecycle_state.termination_reason[0].item()) == int(Reason.NO_FEASIBLE_TASKS_REMAIN), "TEAM terminal reason changed")

    quiet = _stack(
        env_ids=(6002,),
        task_state=[[TaskState.AVAILABLE]],
        ownership=[[-1]],
        robot_state=[[RobotState.NEEDS_ASSIGNMENT, RobotState.NEEDS_ASSIGNMENT]],
        failed=[[[True], [False]]],
    )
    snapshot, contexts, facts = _pending(quiet)
    candidate = quiet["coordinator"]._authority.derive_candidate(
        facts=facts, state_snapshot=snapshot, transition_contexts=contexts
    )
    _assert(not bool(candidate.new_team_infeasible_tasks.any().item()), "nonstructural data created TEAM")
    fact_fields = tuple(facts.to_mapping())
    forbidden = ("path", "cost", "cooldown", "budget", "stall", "retry")
    _assert(not any(word in field for field in fact_fields for word in forbidden), "resolver-like input reached authority")
    return {
        "new_structural_failure": True,
        "cumulative_last_failure": True,
        "team_equation": True,
        "resolver_like_inputs_absent": True,
    }


def test_t7_robot_projection() -> dict[str, Any]:
    completed = _stack(
        env_ids=(7000,),
        task_state=[[TaskState.ALIGNING]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    c = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); c[0, 0, 0] = True
    snapshot, contexts, facts = _pending(completed, completion=c)
    view = completed["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(view.lifecycle_state.robot_state.tolist() == [[int(RobotState.WAITING_FOR_TASK), int(RobotState.WAITING_FOR_TASK)]], "ALL_COMPLETED robot projection changed")
    _assert(view.terminated.tolist() == [True] and view.truncated.tolist() == [False], "ALL_COMPLETED flags changed")

    prior_failed = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); prior_failed[0, 1, 0] = True
    infeasible = _stack(
        env_ids=(7001,),
        task_state=[[TaskState.CLAIMED]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        failed=prior_failed,
    )
    f = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); f[0, 0, 0] = True
    snapshot, contexts, facts = _pending(infeasible, failure=f)
    view = infeasible["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(view.lifecycle_state.robot_state.tolist() == [[int(RobotState.WAITING_FOR_TASK), int(RobotState.WAITING_FOR_TASK)]], "NO_FEASIBLE robot projection changed")

    horizon = _stack(
        env_ids=(7002,),
        task_state=[[TaskState.NAVIGATING, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    snapshot, contexts, facts = _pending(
        horizon,
        time_limit=_b([True]),
        physical_truncated=_b([True]),
    )
    view = horizon["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(int(view.lifecycle_state.robot_state[0, 0].item()) == int(RobotState.EXECUTING), "TIME_LIMIT released active robot")
    _assert(view.truncated.tolist() == [True], "TIME_LIMIT truncation projection changed")

    terminal_unavailable = _stack(
        env_ids=(7003,),
        task_state=[[TaskState.CLAIMED]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
    )
    c = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); c[0, 0, 0] = True
    u = torch.zeros((1, 2), dtype=torch.bool, device=DEVICE); u[0, 0] = True
    snapshot, contexts, facts = _pending(terminal_unavailable, completion=c, unavailable=u)
    view = terminal_unavailable["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(int(view.lifecycle_state.robot_state[0, 0].item()) == int(RobotState.UNAVAILABLE), "terminal normalized unavailable robot")

    recovery = _stack(
        env_ids=(7004,),
        task_state=[[TaskState.AVAILABLE]],
        ownership=[[-1]],
        robot_state=[[RobotState.UNAVAILABLE, RobotState.NEEDS_ASSIGNMENT]],
    )
    rc = torch.zeros((1, 2), dtype=torch.bool, device=DEVICE); rc[0, 0] = True
    snapshot, contexts, facts = _pending(recovery, recovered=rc)
    view = recovery["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(int(view.lifecycle_state.robot_state[0, 0].item()) == int(RobotState.NEEDS_ASSIGNMENT), "recovered feasible robot not projected to NEEDS")

    prior_projection = _stack(
        env_ids=(7005,),
        task_state=[[TaskState.AVAILABLE]],
        ownership=[[-1]],
        robot_state=[[RobotState.WAITING_FOR_TASK, RobotState.NEEDS_ASSIGNMENT]],
        failed=[[[False], [True]]],
    )
    snapshot, contexts, facts = _pending(prior_projection)
    view = prior_projection["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(view.lifecycle_state.robot_state.tolist() == [[int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK)]], "eligibility projection retained stale prior state")
    return {
        "prior_states": [member.name for member in RobotState],
        "all_completed_waiting": True,
        "no_feasible_waiting": True,
        "time_limit_preserves_execution": True,
        "unavailable_absorbed_until_recovery": True,
    }


def test_t8_task_phase_preservation() -> dict[str, Any]:
    observations: dict[str, list[str]] = {}
    env_id = 8000
    for phase in (TaskState.CLAIMED, TaskState.NAVIGATING, TaskState.ALIGNING):
        outcomes: list[str] = []
        for edge in ("none", "completion", "release", "last_failure"):
            robots = 1 if edge == "last_failure" else 2
            robot_state = [[RobotState.EXECUTING] + ([RobotState.NEEDS_ASSIGNMENT] if robots == 2 else [])]
            stack = _stack(
                env_ids=(env_id,),
                task_state=[[phase, TaskState.AVAILABLE]],
                ownership=[[0, -1]],
                robot_state=robot_state,
            )
            c = torch.zeros((1, robots, 2), dtype=torch.bool, device=DEVICE)
            f = torch.zeros_like(c); r = torch.zeros_like(c)
            if edge == "completion":
                c[0, 0, 0] = True
            elif edge == "release":
                r[0, 0, 0] = True
            elif edge == "last_failure":
                f[0, 0, 0] = True
            snapshot, contexts, facts = _pending(stack, completion=c, failure=f, release=r)
            view = stack["coordinator"].transact(facts=facts, transition_contexts=contexts)
            actual = TaskState(int(view.lifecycle_state.task_state[0, 0].item()))
            expected = {
                "none": phase,
                "completion": TaskState.COMPLETED,
                "release": TaskState.AVAILABLE,
                "last_failure": TaskState.TEAM_INFEASIBLE,
            }[edge]
            _assert(actual is expected, f"{phase.name}/{edge} produced {actual.name}")
            outcomes.append(actual.name)
            env_id += 1
        observations[phase.name] = outcomes
    return {
        "phases": observations,
        "automatic_progression": False,
        "authoritative_edges_only": True,
    }


def test_t9_deterministic_event_ordering() -> dict[str, Any]:
    failed = torch.zeros((2, 2, 2), dtype=torch.bool, device=DEVICE)
    failed[1, 1, 0] = True
    stack = _stack(
        env_ids=(9902, 9900),
        task_state=[
            [TaskState.CLAIMED, TaskState.AVAILABLE],
            [TaskState.NAVIGATING, TaskState.ALIGNING],
        ],
        ownership=[[1, -1], [0, 1]],
        robot_state=[
            [RobotState.UNAVAILABLE, RobotState.EXECUTING],
            [RobotState.EXECUTING, RobotState.EXECUTING],
        ],
        failed=failed,
    )
    c = torch.zeros((2, 2, 2), dtype=torch.bool, device=DEVICE)
    f = torch.zeros_like(c); r = torch.zeros_like(c)
    u = torch.zeros((2, 2), dtype=torch.bool, device=DEVICE)
    rc = torch.zeros_like(u)
    c[0, 1, 0] = True
    u[0, 1] = True
    rc[0, 0] = True
    f[1, 0, 0] = True
    r[1, 1, 1] = True
    u[1, 0] = True
    snapshot, contexts, facts = _pending(
        stack,
        completion=c,
        failure=f,
        release=r,
        unavailable=u,
        recovered=rc,
    )
    first = stack["coordinator"]._authority.derive_candidate(
        facts=facts,
        state_snapshot=snapshot,
        transition_contexts=contexts,
    )
    second = stack["coordinator"]._authority.derive_candidate(
        facts=facts,
        state_snapshot=snapshot,
        transition_contexts=contexts,
    )
    signature1 = tuple(_event_signature(event) for event in first.lifecycle_events)
    signature2 = tuple(_event_signature(event) for event in second.lifecycle_events)
    _assert(signature1 == signature2, "repeat derivation changed event values")
    events = first.lifecycle_events
    ranks = {event_type: rank for rank, event_type in enumerate(EventType)}

    def expected_key(event: Any) -> tuple[int, int, int, int]:
        if event.event_type in (
            EventType.TASK_COMPLETED,
            EventType.TASK_RELEASED,
            EventType.TASK_BECAME_TEAM_INFEASIBLE,
        ):
            tie = (event.task_id, event.robot_id)
        elif event.event_type is EventType.TERMINAL_PAIR_FAILURE_RECORDED:
            tie = (event.robot_id, event.task_id)
        else:
            tie = (event.robot_id, -1)
        return event.env_id, ranks[event.event_type], tie[0], tie[1]

    _assert(tuple(expected_key(event) for event in events) == tuple(sorted(expected_key(event) for event in events)), "canonical event order changed")
    by_env: dict[int, list[Any]] = {}
    facts_tokens = {int(facts.env_id[row].item()): int(facts.consume_once_token[row].item()) for row in range(facts.num_envs)}
    for event in events:
        by_env.setdefault(event.env_id, []).append(event)
        _assert(event.event_id == (event.env_id, event.episode_generation, event.transition_generation, event.ordinal), "event_id binding changed")
        _assert(event.facts_consume_token == facts_tokens[event.env_id], "event token binding changed")
    for env_value, rows in by_env.items():
        _assert(tuple(event.ordinal for event in rows) == tuple(range(len(rows))), f"ordinals not contiguous for {env_value}")
    view = stack["coordinator"].transact(facts=facts, transition_contexts=contexts)
    _assert(tuple(_event_signature(event) for event in view.result.lifecycle_events) == signature1, "finalized events differ from candidate")
    return {
        "events": len(events),
        "env_order": sorted(by_env),
        "repeat_value_exact": True,
        "enum_rank_and_ties": True,
        "generation_token_binding": True,
    }


def test_t10_termination_reason_and_physical_mapping() -> dict[str, Any]:
    observed: dict[str, str] = {}

    def run_case(
        label: str,
        env_id: int,
        *,
        last_failure: bool = False,
        completion: bool = False,
        horizon: bool = False,
    ) -> Any:
        robots = 1 if last_failure else 2
        stack = _stack(
            env_ids=(env_id,),
            task_state=[[TaskState.CLAIMED]],
            ownership=[[0]],
            robot_state=[[RobotState.EXECUTING] + ([RobotState.WAITING_FOR_TASK] if robots == 2 else [])],
        )
        c = torch.zeros((1, robots, 1), dtype=torch.bool, device=DEVICE)
        f = torch.zeros_like(c)
        c[0, 0, 0] = completion
        f[0, 0, 0] = last_failure
        snapshot, contexts, facts = _pending(
            stack,
            completion=c,
            failure=f,
            time_limit=_b([horizon]),
            physical_truncated=_b([horizon]),
            physical_terminated=_b([completion or last_failure]),
        )
        view = stack["coordinator"].transact(facts=facts, transition_contexts=contexts)
        observed[label] = Reason(int(view.lifecycle_state.termination_reason[0].item())).name
        return view

    run_case("NONE", 10000)
    run_case("ALL_TASKS_COMPLETED", 10001, completion=True)
    run_case("NO_FEASIBLE_TASKS_REMAIN", 10002, last_failure=True)
    run_case("TIME_LIMIT", 10003, horizon=True)
    run_case("completion_at_horizon", 10004, completion=True, horizon=True)
    run_case("team_at_horizon", 10005, last_failure=True, horizon=True)
    _assert(observed["NONE"] == "NONE", "NONE reason changed")
    _assert(observed["ALL_TASKS_COMPLETED"] == "ALL_TASKS_COMPLETED", "completion reason changed")
    _assert(observed["NO_FEASIBLE_TASKS_REMAIN"] == "NO_FEASIBLE_TASKS_REMAIN", "TEAM reason changed")
    _assert(observed["TIME_LIMIT"] == "TIME_LIMIT", "time-limit reason changed")
    _assert(observed["completion_at_horizon"] == "ALL_TASKS_COMPLETED", "completion priority changed")
    _assert(observed["team_at_horizon"] == "NO_FEASIBLE_TASKS_REMAIN", "TEAM priority changed")

    invalid_specs = (
        ("physical_terminated", {"physical_terminated": _b([True])}),
        ("physical_truncated", {"physical_truncated": _b([True])}),
        ("bad_transition_only", {"bad_transition": _b([True]), "physical_truncated": _b([True])}),
    )
    invalid_codes: list[str] = []
    for index, (label, signals) in enumerate(invalid_specs):
        stack = _stack(
            env_ids=(10020 + index,),
            task_state=[[TaskState.CLAIMED]],
            ownership=[[0]],
            robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        )
        snapshot, contexts, facts = _pending(stack, **signals)
        error = _expect_error(
            B02.LifecycleAuthorityRuntimeError,
            lambda stack=stack, facts=facts, contexts=contexts: stack["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            ),
        )
        invalid_codes.append(str(error.failure_code))
        _assert(_ledger_counts(stack["coordinator"]) == (0, 0, 0), f"{label} consumed")
        _assert(stack["store"]._state.version == 0, f"{label} swapped")
    return {
        "reasons": observed,
        "invalid_preconsume_codes": invalid_codes,
        "priority": "ALL_COMPLETED>NO_FEASIBLE>TIME_LIMIT>NONE",
    }


def test_t11_ledger_result_success_path() -> dict[str, Any]:
    stack = _stack(
        env_ids=(11002, 11000),
        task_state=[
            [TaskState.ALIGNING, TaskState.AVAILABLE],
            [TaskState.CLAIMED, TaskState.AVAILABLE],
        ],
        ownership=[[0, -1], [1, -1]],
        robot_state=[
            [RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT],
            [RobotState.NEEDS_ASSIGNMENT, RobotState.EXECUTING],
        ],
        completion_count=[[3, 1], [0, 4]],
    )
    c = torch.zeros((2, 2, 2), dtype=torch.bool, device=DEVICE)
    r = torch.zeros_like(c)
    c[0, 0, 0] = True
    r[1, 1, 0] = True
    before_view = stack["coordinator"].read_published_view()
    snapshot, contexts, facts = _pending(stack, completion=c, release=r)
    before_clock = stack["clock"].snapshot(snapshot.env_id)
    _assert(_ledger_counts(stack["coordinator"]) == (0, 0, 0), "ledger not empty")
    view = stack["coordinator"].transact(
        facts=facts,
        transition_contexts=contexts,
    )
    after_clock = stack["clock"].snapshot(snapshot.env_id)
    issued, finalized, consumed = _ledger_counts(stack["coordinator"])
    _assert((issued, finalized, consumed) == (1, 1, 2), "success tail counts changed")
    _assert(before_view.store_version == 0 and view.store_version == 1, "store did not swap exactly once")
    _assert(stack["store"]._state.version == 1, "live store version differs")
    _assert(all(row.transition_generation == -1 for row in before_clock), "unexpected initial generation")
    _assert(all(row.transition_generation == 0 for row in after_clock), "clock did not commit exactly once")
    _assert(all(row.outstanding_transition_generation is None for row in after_clock), "successful contexts remain outstanding")
    result = view.result
    _assert(result is not None, "success did not publish finalized result")
    result.validate_finalized()
    comparisons = (
        (result.env_id, view.env_id, "env_id"),
        (result.episode_generation, view.episode_generation, "episode_generation"),
        (result.transition_generation, view.transition_generation, "transition_generation"),
        (result.updated_task_state, view.lifecycle_state.task_state, "task_state"),
        (result.updated_robot_state, view.lifecycle_state.robot_state, "robot_state"),
        (result.updated_ownership, view.lifecycle_state.ownership, "ownership"),
        (result.updated_failed_pairs, view.lifecycle_state.cumulative_failed_pairs, "failed_pairs"),
        (result.termination_reason, view.lifecycle_state.termination_reason, "reason"),
    )
    for observed, expected, name in comparisons:
        _assert(torch.equal(observed, expected), f"published {name} differs")
    _assert(stack["coordinator"].read_published_view() is view, "success installed another view")
    return {
        "ledger_consume_batches": issued,
        "result_finalize_batches": finalized,
        "consumed_rows": consumed,
        "store_swaps": view.store_version - before_view.store_version,
        "clock_commits_per_row": 1,
        "publication_consistent": True,
    }


def test_t12_full_batch_atomic_rejection() -> dict[str, Any]:
    stack = _stack(
        env_ids=(12000, 12001),
        task_state=[
            [TaskState.CLAIMED, TaskState.AVAILABLE],
            [TaskState.NAVIGATING, TaskState.AVAILABLE],
        ],
        ownership=[[0, -1], [1, -1]],
        robot_state=[
            [RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT],
            [RobotState.NEEDS_ASSIGNMENT, RobotState.EXECUTING],
        ],
    )
    retained = stack["coordinator"].read_published_view()
    failed = retained.lifecycle_state.cumulative_failed_pairs
    failed[1, 1, 0] = True
    _private_replace_store_state(stack["store"], failed=failed)
    invalid_snapshot = stack["store"]._snapshot_for_lifecycle(
        writer_capability=stack["coordinator"]._writer_capability,
    )
    contexts = stack["clock"].request_transition_candidate(invalid_snapshot.env_id)
    facts = _facts(stack, invalid_snapshot, contexts)
    _expect_error(
        B02.LifecycleAuthorityRuntimeError,
        lambda: stack["coordinator"].transact(
            facts=facts,
            transition_contexts=contexts,
        ),
        code="active_owner_failed_pair",
    )
    _assert(_ledger_counts(stack["coordinator"]) == (0, 0, 0), "mixed batch consumed")
    _assert(stack["store"]._state.version == 0, "mixed batch swapped")
    clock_rows = stack["clock"].snapshot(invalid_snapshot.env_id)
    _assert(all(row.transition_generation == -1 for row in clock_rows), "mixed batch committed a row")
    _assert(stack["coordinator"]._published_view is retained, "mixed batch published")
    _assert(not stack["coordinator"].poisoned, "normal batch rejection poisoned")

    producer_gate = _stack(
        env_ids=(12010, 12011),
        task_state=[
            [TaskState.CLAIMED, TaskState.AVAILABLE],
            [TaskState.CLAIMED, TaskState.AVAILABLE],
        ],
        ownership=[[0, -1], [0, -1]],
        robot_state=[
            [RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT],
            [RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT],
        ],
    )
    snapshot = producer_gate["coordinator"].read_published_view().lifecycle_state
    contexts = producer_gate["clock"].request_transition_candidate(snapshot.env_id)
    c = torch.zeros((2, 2, 2), dtype=torch.bool, device=DEVICE)
    f = torch.zeros_like(c)
    c[1, 0, 0] = True; f[1, 0, 0] = True
    _expect_error(
        TRANSITION.AssignmentTransitionContractError,
        lambda: _facts(producer_gate, snapshot, contexts, completion=c, failure=f),
    )
    _assert(_ledger_counts(producer_gate["coordinator"]) == (0, 0, 0), "producer-invalid batch consumed")
    _assert(producer_gate["store"]._state.version == 0, "producer-invalid batch swapped")
    return {
        "batch_rows": 2,
        "valid_row_partial_commit": False,
        "c1_rejected_preconsume": True,
        "c_and_f_rejected_at_frozen_facts_gate": True,
        "coordinator_poisoned": False,
    }


def test_t13_generation_token_independence() -> dict[str, Any]:
    stack = _stack(
        env_ids=(13000,),
        task_state=[[TaskState.CLAIMED, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    first_snapshot, first_contexts, first_facts = _pending(stack)
    first_token = int(first_facts.consume_once_token[0].item())
    first_view = stack["coordinator"].transact(
        facts=first_facts,
        transition_contexts=first_contexts,
    )
    _assert(int(first_view.transition_generation[0].item()) == 0, "first generation changed")

    second_snapshot = stack["coordinator"].read_published_view().lifecycle_state
    second_contexts = stack["clock"].request_transition_candidate(second_snapshot.env_id)
    _expect_error(
        B01.ExecutionFactsProducerRuntimeError,
        lambda: _facts(
            stack,
            second_snapshot,
            second_contexts,
            invalid_completion_dtype=True,
        ),
    )
    pending = stack["clock"].snapshot(second_snapshot.env_id)[0]
    _assert(pending.transition_generation == 0, "failed facts build committed clock")
    _assert(pending.outstanding_transition_generation == 1, "failed facts build discarded context")
    retry_facts = _facts(stack, second_snapshot, second_contexts)
    retry_token = int(retry_facts.consume_once_token[0].item())
    _assert(retry_token - first_token == 2, "failed facts token was not burned")
    retry_view = stack["coordinator"].transact(
        facts=retry_facts,
        transition_contexts=second_contexts,
    )
    _assert(int(retry_view.transition_generation[0].item()) == 1, "retry generation has a gap")
    _assert(retry_view.store_version == 2, "retry did not make one second state swap")
    return {
        "first_token": first_token,
        "retry_token": retry_token,
        "token_delta": retry_token - first_token,
        "committed_generation_delta": 1,
        "same_context_retried": True,
    }


def _finalize_candidate(
    factory: Any,
    facts: Any,
    receipt: Any,
    candidate: Any,
    **overrides: Any,
) -> Any:
    values = {
        "completed_tasks": candidate.completed_tasks,
        "released_tasks": candidate.released_tasks,
        "new_failed_pairs": candidate.new_failed_pairs,
        "prior_failed_pairs": candidate.prior_failed_pairs,
        "updated_failed_pairs": candidate.updated_failed_pairs,
        "new_team_infeasible_tasks": candidate.new_team_infeasible_tasks,
        "updated_task_state": candidate.updated_task_state,
        "updated_robot_state": candidate.updated_robot_state,
        "updated_ownership": candidate.updated_ownership,
        "termination_reason": candidate.termination_reason,
        "task_completed_state_encoding": int(TaskState.COMPLETED),
        "lifecycle_events": candidate.lifecycle_events,
    }
    values.update(overrides)
    return factory.finalize(facts=facts, receipt=receipt, **values)


def test_t14_receipt_retry_vs_coordinator_fail_stop() -> dict[str, Any]:
    direct = _stack(
        env_ids=(14000,),
        task_state=[[TaskState.CLAIMED, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
    )
    snapshot, contexts, facts = _pending(direct)
    authority = direct["coordinator"]._authority
    candidate = authority.derive_candidate(
        facts=facts,
        state_snapshot=snapshot,
        transition_contexts=contexts,
    )
    ledger = TRANSITION.TransitionConsumeLedger(authority_stamp=authority._authority_stamp)
    factory = TRANSITION.LifecycleTransitionResultFactory(
        ledger=ledger,
        authority_stamp=ledger.authority_stamp,
    )
    expectations = tuple(
        TRANSITION.TransitionGenerationExpectation(
            env_id=context.env_id,
            episode_generation=context.episode_generation,
            transition_generation=context.transition_generation,
        )
        for context in contexts
    )
    receipt = ledger.consume(
        facts,
        producer_stamp=authority._producer_stamp,
        expected_generations=expectations,
    )
    invalid_completed = ~candidate.completed_tasks
    _expect_error(
        TRANSITION.AssignmentTransitionContractError,
        lambda: _finalize_candidate(
            factory,
            facts,
            receipt,
            candidate,
            completed_tasks=invalid_completed,
        ),
    )
    audit = ledger.snapshot()
    _assert(audit["issued_receipt_count"] == 1, "direct receipt count changed")
    _assert(audit["finalized_receipt_count"] == 0, "failed direct finalize burned receipt")
    direct_result = _finalize_candidate(factory, facts, receipt, candidate)
    direct_result.validate_finalized()
    _assert(ledger.snapshot()["finalized_receipt_count"] == 1, "same receipt retry failed")

    reached = Event(); release = Event()
    control = B02._CoordinatorTestControl(
        after_ledger_consume_reached=reached,
        after_ledger_consume_release=release,
    )
    fail_stop = _stack(
        env_ids=(14001,),
        task_state=[[TaskState.CLAIMED, TaskState.AVAILABLE]],
        ownership=[[0, -1]],
        robot_state=[[RobotState.EXECUTING, RobotState.NEEDS_ASSIGNMENT]],
        control=control,
    )
    snapshot, contexts, facts = _pending(fail_stop)
    outcome: dict[str, Any] = {}

    def transact() -> None:
        try:
            outcome["view"] = fail_stop["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            )
        except BaseException as exc:
            outcome["error"] = exc

    worker = Thread(target=transact, name="b02-t14-writer")
    worker.start()
    try:
        _assert(reached.wait(timeout=10.0), "writer did not reach post-consume pause")
        facts._tensor_snapshots["env_id"]._tensor.add_(0)
    finally:
        release.set()
        worker.join(timeout=10.0)
    _assert(not worker.is_alive(), "post-consume writer did not terminate")
    error = outcome.get("error")
    _assert(type(error) is B02.LifecycleCoordinatorRuntimeError, "unexpected fail-stop error")
    _assert(error.failure_code == "fatal_post_receipt_failure", "post-receipt failure was not fatal")
    _assert(fail_stop["coordinator"].poisoned, "coordinator not poisoned")
    _assert(_ledger_counts(fail_stop["coordinator"]) == (1, 0, 1), "coordinator retried or finalized")
    _assert(fail_stop["store"]._state.version == 0, "finalize failure swapped store")
    clock_row = fail_stop["clock"].snapshot(_i((14001,)))[0]
    _assert(clock_row.transition_generation == -1, "finalize failure committed clock")
    _assert(clock_row.outstanding_transition_generation == 0, "coordinator canceled context")
    _expect_error(
        B02.LifecycleCoordinatorRuntimeError,
        fail_stop["coordinator"].read_published_view,
        code="coordinator_poisoned",
    )
    _expect_error(
        B02.LifecycleCoordinatorRuntimeError,
        lambda: fail_stop["coordinator"].transact(
            facts=facts,
            transition_contexts=contexts,
        ),
        code="coordinator_poisoned",
    )
    _assert(_ledger_counts(fail_stop["coordinator"]) == (1, 0, 1), "poisoned retry consumed again")
    return {
        "frozen_same_receipt_retry": True,
        "coordinator_automatic_retry": False,
        "coordinator_second_consume": False,
        "post_receipt_poisoned": True,
        "state_generation_publication_unchanged": True,
    }


def test_t15_concurrent_publication_atomicity() -> dict[str, Any]:
    after_swap = Event()
    release_swap = Event()
    read_before_lock = Event()
    control = B02._CoordinatorTestControl(
        after_state_swap_reached=after_swap,
        after_state_swap_release=release_swap,
        read_before_lock=read_before_lock,
    )
    stack = _stack(
        env_ids=(15000,),
        task_state=[[TaskState.ALIGNING]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        control=control,
    )
    old_view = stack["coordinator"].read_published_view()
    read_before_lock.clear()
    c = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); c[0, 0, 0] = True
    snapshot, contexts, facts = _pending(stack, completion=c)
    read_before_lock.clear()
    writer_outcome: dict[str, Any] = {}
    reader_outcome: dict[str, Any] = {}
    reader_done = Event()

    def writer() -> None:
        try:
            writer_outcome["view"] = stack["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            )
        except BaseException as exc:
            writer_outcome["error"] = exc

    def reader() -> None:
        try:
            reader_outcome["view"] = stack["coordinator"].read_published_view()
        except BaseException as exc:
            reader_outcome["error"] = exc
        finally:
            reader_done.set()

    writer_thread = Thread(target=writer, name="b02-t15-writer")
    reader_thread = Thread(target=reader, name="b02-t15-reader")
    writer_thread.start()
    try:
        _assert(after_swap.wait(timeout=10.0), "writer did not pause after state swap")
        _assert(stack["store"]._state.version == 1, "test did not reach post-swap state")
        clock_during = stack["clock"].snapshot(_i((15000,)))[0]
        _assert(clock_during.transition_generation == -1, "clock committed before controlled pause")
        reader_thread.start()
        _assert(read_before_lock.wait(timeout=10.0), "reader did not reach publication lock")
        _assert(not reader_done.is_set(), "reader observed an intermediate publication")
        _assert("view" not in reader_outcome and "error" not in reader_outcome, "reader escaped publication lock")
    finally:
        release_swap.set()
        writer_thread.join(timeout=10.0)
        if reader_thread.ident is not None:
            reader_thread.join(timeout=10.0)
    _assert(not writer_thread.is_alive(), "writer did not terminate")
    _assert(not reader_thread.is_alive(), "reader did not terminate")
    _assert("error" not in writer_outcome, f"writer failed: {writer_outcome.get('error')}")
    _assert("error" not in reader_outcome, f"reader failed: {reader_outcome.get('error')}")
    new_view = reader_outcome.get("view")
    _assert(new_view is writer_outcome.get("view"), "reader did not receive installed view")
    _assert(old_view.store_version == 0, "retained old state version changed")
    _assert(old_view.transition_generation.tolist() == [-1], "retained old generation changed")
    _assert(int(old_view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.ALIGNING), "retained old state changed")
    _assert(new_view.store_version == 1, "reader did not observe new state version")
    _assert(new_view.transition_generation.tolist() == [0], "reader did not observe new generation")
    _assert(int(new_view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.COMPLETED), "reader did not observe new state")
    return {
        "reader_reached_lock_while_internal_state_new_clock_old": True,
        "reader_blocked": True,
        "old_pair": [old_view.store_version, int(old_view.transition_generation[0].item())],
        "new_pair": [new_view.store_version, int(new_view.transition_generation[0].item())],
        "mixed_pair_observed": False,
        "sleep_based_race": False,
    }


def test_t16_poison_between_swap_and_clock_commit() -> dict[str, Any]:
    after_swap = Event()
    release_swap = Event()
    control = B02._CoordinatorTestControl(
        after_state_swap_reached=after_swap,
        after_state_swap_release=release_swap,
    )
    stack = _stack(
        env_ids=(16000,),
        task_state=[[TaskState.ALIGNING]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        control=control,
    )
    old_view = stack["coordinator"].read_published_view()
    c = torch.zeros((1, 2, 1), dtype=torch.bool, device=DEVICE); c[0, 0, 0] = True
    snapshot, contexts, facts = _pending(stack, completion=c)
    outcome: dict[str, Any] = {}

    def writer() -> None:
        try:
            outcome["view"] = stack["coordinator"].transact(
                facts=facts,
                transition_contexts=contexts,
            )
        except BaseException as exc:
            outcome["error"] = exc

    worker = Thread(target=writer, name="b02-t16-writer")
    worker.start()
    original_transition = contexts[0].transition_generation
    try:
        _assert(after_swap.wait(timeout=10.0), "writer did not pause after state swap")
        _assert(stack["store"]._state.version == 1, "store swap was not committed")
        object.__setattr__(contexts[0], "transition_generation", original_transition + 7)
    finally:
        release_swap.set()
        worker.join(timeout=10.0)
    _assert(not worker.is_alive(), "injected commit failure did not terminate")
    error = outcome.get("error")
    _assert(type(error) is B02.LifecycleCoordinatorRuntimeError, "wrong injected failure type")
    _assert(error.failure_code == "fatal_post_receipt_failure", "post-swap failure was not fatal")
    _assert(stack["coordinator"].poisoned, "post-swap coordinator not poisoned")
    _assert(_ledger_counts(stack["coordinator"]) == (1, 1, 1), "post-swap failure retried consume/finalize")
    _assert(stack["store"]._state.version == 1, "post-swap failure rolled state back")
    _assert(int(stack["store"]._state.task_state[0, 0].item()) == int(TaskState.COMPLETED), "committed store state rolled back")
    clock_row = stack["clock"].snapshot(_i((16000,)))[0]
    _assert(clock_row.transition_generation == -1, "injected clock failure committed generation")
    _assert(clock_row.outstanding_transition_generation == original_transition, "injected failure canceled reservation")
    _assert(stack["coordinator"]._published_view is old_view, "poison path published new view")
    _assert(old_view.store_version == 0 and old_view.transition_generation.tolist() == [-1], "historical view changed")
    _assert(int(old_view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.ALIGNING), "historical state changed")
    _expect_error(
        B02.LifecycleCoordinatorRuntimeError,
        stack["coordinator"].read_published_view,
        code="coordinator_poisoned",
    )
    _expect_error(
        B02.LifecycleCoordinatorRuntimeError,
        lambda: stack["coordinator"].transact(
            facts=facts,
            transition_contexts=contexts,
        ),
        code="coordinator_poisoned",
    )
    _assert(_ledger_counts(stack["coordinator"]) == (1, 1, 1), "poisoned transaction consumed again")
    return {
        "state_swap_retained": True,
        "clock_commit": False,
        "new_publication": False,
        "poisoned": True,
        "rollback": False,
        "cancellation": False,
        "second_consume": False,
        "historical_view_readable": True,
    }


def test_t17_capability_isolation_and_static_wiring() -> dict[str, Any]:
    source = B02_RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(B02_RUNTIME_PATH))
    coordinator_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "LifecycleAuthorityTransactionCoordinator"
    )
    coordinator_public = tuple(
        node.name
        for node in coordinator_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    _assert(
        coordinator_public == ("poisoned", "read_published_view", "transact"),
        f"coordinator public surface changed: {coordinator_public}",
    )
    transact_node = next(
        node
        for node in coordinator_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "transact"
    )
    transact_args = tuple(arg.arg for arg in (*transact_node.args.args, *transact_node.args.kwonlyargs))
    _assert(transact_args == ("self", "facts", "transition_contexts"), "transact leaks store snapshot capability")
    published_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PublishedLifecycleView"
    )
    published_public = tuple(
        node.name
        for node in published_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    _assert(
        published_public
        == (
            "lifecycle_state",
            "env_id",
            "episode_generation",
            "transition_generation",
            "terminated",
            "truncated",
            "result",
        ),
        f"published view surface changed: {published_public}",
    )
    _assert(
        tuple(B02.__all__)
        == (
            "ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_SOURCE_PURPOSE",
            "CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSACTION_RUNTIME_MODULE",
            "LifecycleAuthorityRuntime",
            "LifecycleAuthorityRuntimeError",
            "LifecycleAuthorityTransactionCoordinator",
            "LifecycleCoordinatorRuntimeError",
            "LifecycleStateRuntimeError",
            "LifecycleStateSnapshot",
            "LifecycleStateStore",
            "PublishedLifecycleView",
        ),
        "B0-2 exported contract family changed",
    )
    coordinator_source = ast.get_source_segment(source, coordinator_class) or ""
    _assert("with self._publication_lock" in coordinator_source, "publication lock missing")
    _assert("_snapshot_for_lifecycle" in coordinator_source, "writer-only snapshot path missing")
    method_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    _assert(not ({"rollback", "rollback_transition", "cancel", "cancel_transition"} & method_names), "rollback/cancellation capability added")
    store_class = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "LifecycleStateStore"
    )
    store_source = ast.get_source_segment(source, store_class) or ""
    _assert("_publication_lock" not in store_source, "StateStore reaches back into coordinator lock")

    stack = _stack(
        env_ids=(17000,),
        task_state=[[TaskState.CLAIMED]],
        ownership=[[0]],
        robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
    )
    _expect_error(
        B02.LifecycleStateRuntimeError,
        stack["store"].snapshot,
        code="snapshot_capability_confined",
    )
    _expect_error(
        B02.LifecycleStateRuntimeError,
        lambda: stack["store"]._snapshot_for_lifecycle(writer_capability=object()),
        code="writer_capability",
    )
    view = stack["coordinator"].read_published_view()
    view_state = view.lifecycle_state.task_state
    view_state[0, 0] = int(TaskState.COMPLETED)
    _assert(int(view.lifecycle_state.task_state[0, 0].item()) == int(TaskState.CLAIMED), "published view exposes writable state")

    entry_paths = (
        SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_TASK_SOURCE / "assignment_harl_wrapper.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_TASK_SOURCE / "assignment_controller.py",
        SCAN_TASK_SOURCE / "__init__.py",
    )
    runtime_leaf = B02_RUNTIME_MODULE.rsplit(".", 1)[-1]
    forbidden_wiring = (
        runtime_leaf,
        "LifecycleAuthorityTransactionCoordinator",
        "LifecycleStateStore",
        "read_published_view",
    )
    for path in entry_paths:
        entry_source = path.read_text(encoding="utf-8")
        for symbol in forbidden_wiring:
            _assert(symbol not in entry_source, f"B0-2 wired into {path.name}: {symbol}")
    blocked_modules = sorted(
        name
        for name in sys.modules
        if name == "isaaclab" or name.startswith(("isaaclab.", "omni", "pxr", "harl"))
    )
    _assert(blocked_modules == [], f"heavy runtime modules imported: {blocked_modules}")
    return {
        "coordinator_public": list(coordinator_public),
        "published_public": list(published_public),
        "raw_store_snapshot_after_claim": "rejected",
        "foreign_writer_capability": "rejected",
        "rollback_cancel_surface": "absent",
        "production_wiring": "absent",
        "heavy_runtime_imports": blocked_modules,
    }


def test_t18_profile_gate_default_off_side_effects() -> dict[str, Any]:
    event, existing = _profiles()
    python_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()
    logger_before = _logger_state()
    files_before = _file_inventory()
    cwd_before = Path.cwd()
    environment_before = dict(os.environ)
    sys_path_before = tuple(sys.path)

    calls: list[str] = []
    original_resolve = PROFILE.resolve_assignment_profile
    original_normalize = PROFILE.normalize_assignment_profile_name

    def forbidden_resolve(*args: Any, **kwargs: Any) -> Any:
        calls.append("resolve")
        raise AssertionError("B0-2 invoked profile resolver")

    def forbidden_normalize(*args: Any, **kwargs: Any) -> Any:
        calls.append("normalize")
        raise AssertionError("B0-2 invoked profile normalizer")

    PROFILE.resolve_assignment_profile = forbidden_resolve
    PROFILE.normalize_assignment_profile_name = forbidden_normalize
    try:
        accepted_store = _store(
            event,
            env_ids=(18000,),
            task_state=[[TaskState.CLAIMED]],
            ownership=[[0]],
            robot_state=[[RobotState.EXECUTING, RobotState.WAITING_FOR_TASK]],
        )
        accepted_clock = B01.LifecycleGenerationClock(event, env_ids=_i((18000,)))
        accepted_clock.advance_episode(_i((18000,)))
        accepted = B02.LifecycleAuthorityTransactionCoordinator(
            event,
            state_store=accepted_store,
            generation_clock=accepted_clock,
        )
        _assert(accepted.read_published_view().store_version == 0, "event profile rejected")
        for index, profile in enumerate(existing):
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda profile=profile: B02.LifecycleAuthorityRuntime(profile),
            )
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda profile=profile, index=index: _store(
                    profile,
                    env_ids=(18010 + index,),
                    task_state=[[TaskState.AVAILABLE]],
                    ownership=[[-1]],
                    robot_state=[[RobotState.NEEDS_ASSIGNMENT, RobotState.NEEDS_ASSIGNMENT]],
                ),
            )
        raw_profiles = (
            PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            "event_gated_local_mrta",
            {"profile_name": "event_gated_local_mrta"},
            None,
            type("ProfileLookalike", (), {"profile_name": "event_gated_local_mrta"})(),
        )
        for candidate in raw_profiles:
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda candidate=candidate: B02.LifecycleAuthorityRuntime(candidate),
            )
    finally:
        PROFILE.resolve_assignment_profile = original_resolve
        PROFILE.normalize_assignment_profile_name = original_normalize

    _assert(calls == [], f"fallback profile path invoked: {calls}")
    readiness_error = _expect_error(
        PROFILE.PhaseAExecutionNotAuthorizedError,
        lambda: PROFILE.require_assignment_profile_runtime_ready(
            event,
            consumer="B0-2 lifecycle-authority pure test",
            entrypoint="standalone pure test",
            current_phase="B0-2",
            barrier="environment wiring remains unauthorized",
        ),
    )
    _assert(type(readiness_error) is PROFILE.PhaseAExecutionNotAuthorizedError, "wrong readiness block")
    _assert(event.runtime_readiness.value == "interface_only", "runtime readiness opened")
    _assert(event.training_support.value == "phase_a_blocked", "training readiness opened")
    _assert(event.playback_support.value == "blocked", "playback readiness opened")
    _assert(random.getstate() == python_before, "Python RNG side effect")
    _assert(torch.equal(torch.random.get_rng_state(), torch_before), "Torch RNG side effect")
    _assert(_logger_state() == logger_before, "logger side effect")
    _assert(_file_inventory() == files_before, "filesystem side effect")
    _assert(Path.cwd() == cwd_before, "cwd side effect")
    _assert(dict(os.environ) == environment_before, "environment side effect")
    _assert(tuple(sys.path) == sys_path_before, "sys.path side effect")
    return {
        "event_profile_accepted": True,
        "existing_profiles_rejected": len(existing),
        "raw_profiles_rejected": len(raw_profiles),
        "resolver_calls": len(calls),
        "runtime_readiness": event.runtime_readiness.value,
        "training_support": event.training_support.value,
        "playback_support": event.playback_support.value,
        "rng_filesystem_logger_cwd_environment_sys_path_unchanged": True,
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("T1_state_store_initialization_invariants", test_t1_state_store_initialization_invariants),
    ("T2_immutable_versioned_snapshot", test_t2_immutable_versioned_snapshot),
    ("T3_all_32_simultaneous_cause_combinations", test_t3_all_32_simultaneous_cause_combinations),
    ("T4_c1_active_owner_failed_invariant", test_t4_c1_active_owner_failed_invariant),
    ("T5_completion_attribution", test_t5_completion_attribution),
    ("T6_failure_and_team_infeasible", test_t6_failure_and_team_infeasible),
    ("T7_robot_projection", test_t7_robot_projection),
    ("T8_task_phase_preservation", test_t8_task_phase_preservation),
    ("T9_deterministic_event_ordering", test_t9_deterministic_event_ordering),
    ("T10_termination_reason_and_physical_mapping", test_t10_termination_reason_and_physical_mapping),
    ("T11_ledger_result_success_path", test_t11_ledger_result_success_path),
    ("T12_full_batch_atomic_rejection", test_t12_full_batch_atomic_rejection),
    ("T13_generation_token_independence", test_t13_generation_token_independence),
    ("T14_receipt_retry_vs_coordinator_fail_stop", test_t14_receipt_retry_vs_coordinator_fail_stop),
    ("T15_concurrent_publication_atomicity", test_t15_concurrent_publication_atomicity),
    ("T16_poison_between_swap_and_clock_commit", test_t16_poison_between_swap_and_clock_commit),
    ("T17_capability_isolation_and_static_wiring", test_t17_capability_isolation_and_static_wiring),
    ("T18_profile_gate_default_off_side_effects", test_t18_profile_gate_default_off_side_effects),
)


def run_suite() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = 0
    for name, operation in TESTS:
        try:
            evidence = operation()
        except BaseException as exc:
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
        else:
            passed += 1
            results.append({"name": name, "status": "passed", "evidence": evidence})
    failed = len(TESTS) - passed
    return {
        "status": "passed" if failed == 0 else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": failed,
        "tests": results,
        "evidence": {
            "standalone_groups": "T1-T18",
            "namespace_only_canonical_loading": True,
            "device": str(DEVICE),
            "deterministic_event_synchronization": "threading.Event",
            "sleep_based_races": False,
            "observable_publication_pairs": "old/old_or_new/new",
        },
        "runtime_boundary": {
            "lifecycle_authority_transaction": "pure_default_off",
            "environment_hook": "absent",
            "wrapper_resolver_controller_harl_wiring": "absent",
            "isaac_applauncher": "not_imported",
            "training_playback_evaluation": "not_run",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    payload = run_suite()
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
