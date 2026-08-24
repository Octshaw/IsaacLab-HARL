"""Pure B0-3I1 episode-rebuild transaction regressions.

Loads only canonical contract and B0 runtime sources through namespace-only
package placeholders.  It never starts Isaac, task discovery, an environment,
HARL, training, playback, or evaluation.
"""

from __future__ import annotations

import argparse
from dataclasses import FrozenInstanceError
import importlib.util
import inspect
import json
import logging
import os
from pathlib import Path
import random
import sys
from threading import Event, Thread
from types import ModuleType
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_TASK_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PROFILE_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
EVENT_PATH = SCAN_TASK_SOURCE / "assignment_event_contract.py"
B01_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_authority_runtime.py"
B02_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_transaction_runtime.py"

PROFILE_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
TRANSITION_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract"
EVENT_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract"
B01_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_authority_runtime"
B02_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transaction_runtime"
DEVICE = torch.device("cpu")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_namespace_packages() -> None:
    for name, path in (
        ("isaaclab_tasks", TASKS_SOURCE),
        ("isaaclab_tasks.direct", DIRECT_SOURCE),
        ("isaaclab_tasks.direct.scan_mobile_manipulator", SCAN_TASK_SOURCE),
    ):
        existing = sys.modules.get(name)
        if existing is not None:
            _assert(str(path) in tuple(getattr(existing, "__path__", ())), f"unexpected package {name}")
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    prior = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = prior
    return module


_install_namespace_packages()
PROFILE = _load(PROFILE_MODULE, PROFILE_PATH)
TRANSITION = _load(TRANSITION_MODULE, TRANSITION_PATH)
EVENT = _load(EVENT_MODULE, EVENT_PATH)
B01 = _load(B01_MODULE, B01_PATH)
B02 = _load(B02_MODULE, B02_PATH)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason


def _i(values: Any, *, device: torch.device = DEVICE) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=device)


def _b(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.bool, device=DEVICE)


def _event_profile() -> Any:
    return PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )


def _existing_profiles() -> tuple[Any, ...]:
    origin = PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    return tuple(
        PROFILE.resolve_assignment_profile(name, origin)
        for name in (
            PROFILE.AssignmentProfileName.LEGACY,
            PROFILE.AssignmentProfileName.LIFECYCLE_CONTRACT_C,
            PROFILE.AssignmentProfileName.LIFECYCLE_ABLATION,
            PROFILE.AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
        )
    )


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
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _set_clock(clock: Any, episodes: tuple[int, ...], transitions: tuple[int, ...]) -> None:
    _assert(len(episodes) == len(transitions) == len(clock._env_ids), "clock fixture shape")
    with clock._lock:
        clock._state = B01._GenerationClockState(
            episode_generation=episodes,
            transition_generation=transitions,
            outstanding=tuple(None for _ in episodes),
        )


def _stack(
    *,
    env_ids: tuple[int, ...],
    task_state: Any,
    robot_state: Any,
    ownership: Any,
    failed: Any | None = None,
    counts: Any | None = None,
    reasons: Any | None = None,
    episodes: tuple[int, ...] | None = None,
    transitions: tuple[int, ...] | None = None,
    coordinator_control: Any | None = None,
) -> dict[str, Any]:
    profile = _event_profile()
    task = _i(task_state)
    robot = _i(robot_state)
    owner = _i(ownership)
    env_count, num_tasks = task.shape
    num_robots = robot.shape[1]
    failed_tensor = (
        torch.zeros((env_count, num_robots, num_tasks), dtype=torch.bool)
        if failed is None
        else _b(failed)
    )
    count_tensor = torch.zeros((env_count, num_robots), dtype=torch.int64) if counts is None else _i(counts)
    reason_tensor = torch.zeros(env_count, dtype=torch.int64) if reasons is None else _i(reasons)
    store = B02.LifecycleStateStore(
        profile,
        device=DEVICE,
        env_id=_i(env_ids),
        task_state=task,
        robot_state=robot,
        ownership=owner,
        cumulative_failed_pairs=failed_tensor,
        completion_count=count_tensor,
        termination_reason=reason_tensor,
    )
    clock = B01.LifecycleGenerationClock(profile, env_ids=_i(env_ids))
    _set_clock(
        clock,
        tuple(-1 for _ in env_ids) if episodes is None else episodes,
        tuple(-1 for _ in env_ids) if transitions is None else transitions,
    )
    coordinator = B02.LifecycleAuthorityTransactionCoordinator(
        profile,
        state_store=store,
        generation_clock=clock,
        _test_control=coordinator_control,
    )
    return {"profile": profile, "store": store, "clock": clock, "coordinator": coordinator}


def _inputs(stack: dict[str, Any], selected: tuple[int, ...]) -> Any:
    state = stack["coordinator"].read_published_view().lifecycle_state
    rows = len(selected)
    return B02._EpisodeRebuildInputs(
        stack["profile"],
        device=DEVICE,
        selected_env_ids=_i(selected),
        initial_task_state=torch.full(
            (rows, state.num_tasks), int(TaskState.AVAILABLE), dtype=torch.int64
        ),
        initial_robot_state=torch.full(
            (rows, state.num_robots), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64
        ),
        initial_ownership=torch.full((rows, state.num_tasks), -1, dtype=torch.int64),
    )


def _reset(
    stack: dict[str, Any],
    selected: tuple[int, ...],
    *,
    control: Any | None = None,
) -> Any:
    with stack["coordinator"]._episode_rebuild(
        _inputs(stack, selected), _test_control=control
    ) as rebuild:
        return rebuild.commit_physical_reset_complete()


def _view_signature(view: Any) -> tuple[Any, ...]:
    state = view.lifecycle_state
    return (
        view.store_version,
        state.task_state,
        state.robot_state,
        state.ownership,
        state.cumulative_failed_pairs,
        state.completion_count,
        state.termination_reason,
        view.episode_generation,
        view.transition_generation,
        view.result,
    )


def _same_view(left: Any, right: Any) -> bool:
    a = _view_signature(left)
    b = _view_signature(right)
    return a[0] == b[0] and all(torch.equal(x, y) for x, y in zip(a[1:9], b[1:9])) and a[9] is b[9]


def _assert_reset_view(view: Any, *, episodes: tuple[int, ...], transitions: tuple[int, ...]) -> None:
    state = view.lifecycle_state
    _assert(bool((state.task_state == int(TaskState.AVAILABLE)).all()), "task reset")
    _assert(bool((state.robot_state == int(RobotState.NEEDS_ASSIGNMENT)).all()), "robot reset")
    _assert(bool((state.ownership == -1).all()), "ownership reset")
    _assert(not bool(state.cumulative_failed_pairs.any()), "failed pairs not cleared")
    _assert(not bool(state.completion_count.any()), "completion count not cleared")
    _assert(bool((state.termination_reason == int(Reason.NONE)).all()), "reason not NONE")
    _assert(tuple(view.episode_generation.tolist()) == episodes, "episode vector")
    _assert(tuple(view.transition_generation.tolist()) == transitions, "transition vector")
    _assert(view.result is None, "reset fabricated result")
    _assert(not bool(view.terminated.any()) and not bool(view.truncated.any()), "reset done flags")


def test_i1_t1_canonical_initial_bootstrap() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31000, 31001),
        task_state=[[0, 0], [0, 0]],
        robot_state=[[1, 1], [1, 1]],
        ownership=[[-1, -1], [-1, -1]],
    )
    before = stack["coordinator"].read_published_view()
    task_source = _i([[0, 0], [0, 0]])
    alias_probe = B02._EpisodeRebuildInputs(
        stack["profile"],
        device=DEVICE,
        selected_env_ids=_i((31000, 31001)),
        initial_task_state=task_source,
        initial_robot_state=_i([[1, 1], [1, 1]]),
        initial_ownership=_i([[-1, -1], [-1, -1]]),
    )
    task_source.fill_(int(TaskState.COMPLETED))
    _assert(bool((alias_probe.initial_task_state == int(TaskState.AVAILABLE)).all()), "reset input retained ingress alias")
    accessor = alias_probe.initial_task_state
    accessor.fill_(int(TaskState.COMPLETED))
    _assert(bool((alias_probe.initial_task_state == int(TaskState.AVAILABLE)).all()), "reset input accessor leaked alias")
    _expect_error(FrozenInstanceError, lambda: setattr(alias_probe, "_device", torch.device("meta")))
    view = _reset(stack, (31000, 31001))
    _assert_reset_view(view, episodes=(0, 0), transitions=(-1, -1))
    _assert(view.store_version == before.store_version + 1, "version did not increment once")
    return {"episode": [0, 0], "transition": [-1, -1], "version_delta": 1, "result": None, "input_alias_isolated": True}


def test_i1_t2_ordinary_later_rebuild() -> dict[str, Any]:
    failed = [[[False, True], [False, True]]]
    stack = _stack(
        env_ids=(31100,),
        task_state=[[4, 5]],
        robot_state=[[2, 2]],
        ownership=[[-1, -1]],
        failed=failed,
        counts=[[3, 2]],
        reasons=[2],
        episodes=(5,),
        transitions=(9,),
    )
    view = _reset(stack, (31100,))
    _assert_reset_view(view, episodes=(6,), transitions=(9,))
    return {"episode_before": 5, "episode_after": 6, "transition_preserved": 9}


def test_i1_t3_episode_sensitive_state_clearing() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31200,),
        task_state=[[4, 5]],
        robot_state=[[2, 2]],
        ownership=[[-1, -1]],
        failed=[[[True, True], [False, True]]],
        counts=[[7, 4]],
        reasons=[2],
        episodes=(2,),
        transitions=(4,),
    )
    view = _reset(stack, (31200,))
    _assert_reset_view(view, episodes=(3,), transitions=(4,))
    return {"failed_cleared": True, "counts_cleared": True, "reason_none": True}


def test_i1_t4_partial_reset() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31300, 31301, 31302),
        task_state=[[1, 0], [4, 4], [0, 0]],
        robot_state=[[0, 1], [2, 2], [1, 1]],
        ownership=[[0, -1], [-1, -1], [-1, -1]],
        counts=[[1, 0], [2, 3], [0, 0]],
        reasons=[0, 1, 0],
        episodes=(3, 7, 11),
        transitions=(2, 6, 10),
    )
    before = stack["coordinator"].read_published_view()
    view = _reset(stack, (31301,))
    _assert(view.store_version == before.store_version + 1, "partial reset version")
    _assert(tuple(view.episode_generation.tolist()) == (3, 8, 11), "partial episode")
    _assert(tuple(view.transition_generation.tolist()) == (2, 6, 10), "partial transition")
    for name in ("task_state", "robot_state", "ownership", "cumulative_failed_pairs", "completion_count", "termination_reason"):
        old = getattr(before.lifecycle_state, name)
        new = getattr(view.lifecycle_state, name)
        _assert(torch.equal(old[[0, 2]], new[[0, 2]]), f"unselected {name} changed")
    _assert(bool((view.lifecycle_state.task_state[1] == 0).all()), "selected task not reset")
    return {"selected": [31301], "unselected_bit_exact": True, "version_delta": 1}


def test_i1_t5_no_outstanding_transition() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31400, 31401),
        task_state=[[0], [0]],
        robot_state=[[1, 1], [1, 1]],
        ownership=[[-1], [-1]],
        episodes=(0, 0),
        transitions=(-1, -1),
    )
    context = stack["clock"].request_transition_candidate(_i((31400,)))[0]
    before = stack["coordinator"].read_published_view()
    _expect_error(
        B02.LifecycleEpisodeRebuildRuntimeError,
        lambda: stack["coordinator"]._episode_rebuild(_inputs(stack, (31400,))).__enter__(),
        code="outstanding_transition",
    )
    after = stack["coordinator"].read_published_view()
    _assert(_same_view(before, after), "outstanding rejection changed publication")
    row = stack["clock"].snapshot(_i((31400,)))[0]
    _assert(row.outstanding_transition_generation == context.transition_generation, "candidate cancelled")
    _assert(not stack["coordinator"].poisoned, "pre-signal rejection poisoned")
    return {"rejected_pre_signal": True, "candidate_retained": True, "poisoned": False}


def test_i1_t6_invalid_reset_inputs() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31500, 31501),
        task_state=[[0], [0]],
        robot_state=[[1, 1], [1, 1]],
        ownership=[[-1], [-1]],
    )
    profile = stack["profile"]
    make = lambda ids, task, robot, owner, device=DEVICE: B02._EpisodeRebuildInputs(
        profile,
        device=device,
        selected_env_ids=ids,
        initial_task_state=task,
        initial_robot_state=robot,
        initial_ownership=owner,
    )
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: make(_i((31500, 31500)), _i([[0], [0]]), _i([[1, 1], [1, 1]]), _i([[-1], [-1]])))
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: make(torch.tensor([31500], dtype=torch.int32), _i([[0]]), _i([[1, 1]]), _i([[-1]])))
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: make(_i(()), torch.empty((0, 1), dtype=torch.int64), torch.empty((0, 2), dtype=torch.int64), torch.empty((0, 1), dtype=torch.int64)))
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: make(_i((31500,)), _i([0]), _i([[1, 1]]), _i([[-1]])))
    foreign = make(_i((99999,)), _i([[0]]), _i([[1, 1]]), _i([[-1]]))
    _expect_error(Exception, lambda: stack["coordinator"]._episode_rebuild(foreign).__enter__())
    for invalid in (
        make(_i((31500,)), _i([[int(TaskState.COMPLETED)]]), _i([[1, 1]]), _i([[-1]])),
        make(_i((31500,)), _i([[0]]), _i([[int(RobotState.WAITING_FOR_TASK), 1]]), _i([[-1]])),
        make(_i((31500,)), _i([[0]]), _i([[1, 1]]), _i([[0]])),
    ):
        _expect_error(
            B02.LifecycleEpisodeRebuildRuntimeError,
            lambda invalid=invalid: stack["coordinator"]._episode_rebuild(invalid).__enter__(),
        )
    wrong_device = _inputs(stack, (31500,))
    object.__setattr__(wrong_device, "_device", torch.device("meta"))
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: stack["coordinator"]._episode_rebuild(wrong_device).__enter__(), code="device")
    for existing in _existing_profiles():
        _expect_error(PROFILE.AssignmentProfileRouteError, lambda existing=existing: B02._EpisodeRebuildInputs(existing, device=DEVICE, selected_env_ids=_i((31500,)), initial_task_state=_i([[0]]), initial_robot_state=_i([[1, 1]]), initial_ownership=_i([[-1]])))
    _assert(not stack["coordinator"].poisoned, "invalid inputs poisoned")
    return {"duplicate_foreign_dtype_device_shape_empty_rejected": True, "canonical_reset_value_rejections": 3, "existing_profiles_rejected": 4}


def test_i1_t7_abort_before_physical_completion() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31600,),
        task_state=[[4]],
        robot_state=[[2, 2]],
        ownership=[[-1]],
        counts=[[2, 0]],
        reasons=[1],
        episodes=(2,),
        transitions=(5,),
    )
    before = stack["coordinator"].read_published_view()
    with stack["coordinator"]._episode_rebuild(_inputs(stack, (31600,))):
        pass
    after = stack["coordinator"].read_published_view()
    _assert(_same_view(before, after), "pre-completion abort mutated publication")
    rows = stack["clock"].snapshot(_i((31600,)))
    _assert((rows[0].episode_generation, rows[0].transition_generation) == (2, 5), "abort changed clock")
    _assert(not stack["coordinator"].poisoned, "abort poisoned")
    return {"state_clock_publication_unchanged": True, "poisoned": False}


def test_i1_t8_exact_success_count_order() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31700,), task_state=[[0]], robot_state=[[1, 1]], ownership=[[-1]]
    )
    stages: list[str] = []
    control = B02._EpisodeRebuildTestControl(stage_log=stages)
    ledger_before = stack["coordinator"]._ledger.snapshot()
    _reset(stack, (31700,), control=control)
    ledger_after = stack["coordinator"]._ledger.snapshot()
    _assert(stages == ["state_swap", "advance_episode", "publication"], f"wrong stages {stages}")
    _assert(stages.count("state_swap") == stages.count("advance_episode") == stages.count("publication") == 1, "wrong success counts")
    _assert(ledger_before == ledger_after, "episode rebuild touched consume ledger")
    return {"counts": {name: stages.count(name) for name in stages}, "order": stages, "ledger_untouched": True}


def test_i1_t9_clock_failure_after_state_swap() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31800,), task_state=[[4]], robot_state=[[2, 2]], ownership=[[-1]], reasons=[1], episodes=(1,), transitions=(3,)
    )
    old = stack["coordinator"].read_published_view()
    control = B02._EpisodeRebuildTestControl(fail_clock_advance=True)
    _expect_error(
        B02.LifecycleEpisodeRebuildRuntimeError,
        lambda: _reset(stack, (31800,), control=control),
        code="fatal_post_physical_reset_failure",
    )
    _assert(stack["coordinator"].poisoned, "clock failure did not poison")
    _assert(stack["store"]._state.version == old.store_version + 1, "state swap rolled back")
    row = stack["clock"].snapshot(_i((31800,)))[0]
    _assert((row.episode_generation, row.transition_generation) == (1, 3), "clock unexpectedly changed")
    _assert(stack["coordinator"]._published_view is old, "failed reset published")
    _expect_error(B02.LifecycleCoordinatorRuntimeError, stack["coordinator"].read_published_view, code="coordinator_poisoned")
    _expect_error(B02.LifecycleCoordinatorRuntimeError, lambda: stack["coordinator"].transact(facts=None, transition_contexts=()), code="coordinator_poisoned")
    _expect_error(B02.LifecycleCoordinatorRuntimeError, lambda: stack["coordinator"]._episode_rebuild(_inputs_from_old(stack, old, (31800,))).__enter__(), code="coordinator_poisoned")
    return {"state_swap_retained": True, "clock_unchanged": True, "publication_absent": True, "poisoned": True}


def _inputs_from_old(stack: dict[str, Any], view: Any, selected: tuple[int, ...]) -> Any:
    rows = len(selected)
    state = view.lifecycle_state
    return B02._EpisodeRebuildInputs(
        stack["profile"], device=DEVICE, selected_env_ids=_i(selected),
        initial_task_state=torch.full((rows, state.num_tasks), 0, dtype=torch.int64),
        initial_robot_state=torch.full((rows, state.num_robots), 1, dtype=torch.int64),
        initial_ownership=torch.full((rows, state.num_tasks), -1, dtype=torch.int64),
    )


def test_i1_t10_publication_failure_after_episode_advance() -> dict[str, Any]:
    stack = _stack(
        env_ids=(31900,), task_state=[[4]], robot_state=[[2, 2]], ownership=[[-1]], reasons=[1], episodes=(4,), transitions=(8,)
    )
    old = stack["coordinator"].read_published_view()
    control = B02._EpisodeRebuildTestControl(fail_publication=True)
    _expect_error(B02.LifecycleEpisodeRebuildRuntimeError, lambda: _reset(stack, (31900,), control=control), code="fatal_post_physical_reset_failure")
    row = stack["clock"].snapshot(_i((31900,)))[0]
    _assert((row.episode_generation, row.transition_generation) == (5, 8), "clock advance missing")
    _assert(stack["store"]._state.version == old.store_version + 1, "state swap missing")
    _assert(stack["coordinator"]._published_view is old, "publication failure installed view")
    _assert(stack["coordinator"].poisoned, "publication failure did not poison")
    _expect_error(B02.LifecycleCoordinatorRuntimeError, stack["coordinator"].read_published_view, code="coordinator_poisoned")
    return {"state_and_clock_retained": True, "publication_absent": True, "poisoned": True, "rollback": False}


def test_i1_t11_publication_atomicity() -> dict[str, Any]:
    swap_reached, swap_release, reader_before = Event(), Event(), Event()
    coordinator_control = B02._CoordinatorTestControl(read_before_lock=reader_before)
    stack = _stack(
        env_ids=(32000,), task_state=[[4]], robot_state=[[2, 2]], ownership=[[-1]], reasons=[1], episodes=(3,), transitions=(6,), coordinator_control=coordinator_control
    )
    old = stack["coordinator"].read_published_view()
    reader_before.clear()
    reset_control = B02._EpisodeRebuildTestControl(
        after_state_swap_reached=swap_reached,
        after_state_swap_release=swap_release,
    )
    worker_result: list[Any] = []
    reader_result: list[Any] = []
    worker_error: list[BaseException] = []
    reader_error: list[BaseException] = []

    def worker() -> None:
        try:
            worker_result.append(_reset(stack, (32000,), control=reset_control))
        except BaseException as exc:
            worker_error.append(exc)

    def reader() -> None:
        try:
            reader_result.append(stack["coordinator"].read_published_view())
        except BaseException as exc:
            reader_error.append(exc)

    worker_thread = Thread(target=worker)
    reader_thread = Thread(target=reader)
    try:
        worker_thread.start()
        _assert(swap_reached.wait(10.0), "worker did not reach post-swap pause")
        reader_thread.start()
        _assert(reader_before.wait(10.0), "reader did not reach publication lock")
        _assert(reader_result == [] and reader_error == [], "reader observed intermediate state")
        swap_release.set()
        worker_thread.join(10.0)
        reader_thread.join(10.0)
    finally:
        swap_release.set()
        worker_thread.join(10.0)
        reader_thread.join(10.0)
    _assert(not worker_thread.is_alive() and not reader_thread.is_alive(), "thread watchdog")
    _assert(worker_error == [] and reader_error == [], f"thread errors {worker_error} {reader_error}")
    _assert(len(worker_result) == len(reader_result) == 1, "missing result")
    new = reader_result[0]
    _assert(_same_view(new, worker_result[0]), "reader did not get new/new")
    _assert(tuple(old.episode_generation.tolist()) == (3,) and tuple(new.episode_generation.tolist()) == (4,), "old/new episode")
    _assert(tuple(old.transition_generation.tolist()) == tuple(new.transition_generation.tolist()) == (6,), "transition tore")
    return {"reader_blocked": True, "old_pair": [0, 3, 6], "new_pair": [1, 4, 6], "sleep_based_race": False}


def _logger_state() -> tuple[Any, ...]:
    root = logging.getLogger()
    return (root.level, tuple(root.handlers), tuple(root.filters), root.disabled)


def _file_inventory() -> tuple[str, ...]:
    return tuple(sorted(str(path.relative_to(REPO_ROOT)) for path in REPO_ROOT.rglob("*") if path.is_file()))


def test_i1_t12_default_off_profile_isolation() -> dict[str, Any]:
    python_rng = random.getstate()
    torch_rng = torch.random.get_rng_state().clone()
    logger_state = _logger_state()
    files = _file_inventory()
    cwd = Path.cwd()
    environment = dict(os.environ)
    sys_path = tuple(sys.path)
    event = _event_profile()
    raw = (
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        "event_gated_local_mrta",
        {"profile_name": "event_gated_local_mrta"},
        type("Lookalike", (), {"profile_name": "event_gated_local_mrta"})(),
    )
    for candidate in (*_existing_profiles(), *raw):
        _expect_error(
            PROFILE.AssignmentProfileRouteError,
            lambda candidate=candidate: B02._EpisodeRebuildInputs(
                candidate, device=DEVICE, selected_env_ids=_i((32100,)),
                initial_task_state=_i([[0]]), initial_robot_state=_i([[1, 1]]), initial_ownership=_i([[-1]])
            ),
        )
    _expect_error(
        PROFILE.PhaseAExecutionNotAuthorizedError,
        lambda: PROFILE.require_assignment_profile_runtime_ready(
            event,
            consumer="B0-3I1 pure episode-rebuild test",
            entrypoint="standalone pure test",
            current_phase="B0-3I1",
            barrier="environment integration remains unauthorized",
        ),
    )
    _assert(tuple(B02.__all__) == (
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
    ), "B0-2 public exports changed")
    coordinator_public = tuple(
        name
        for name, member in inspect.getmembers(
            B02.LifecycleAuthorityTransactionCoordinator,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    )
    context_public = tuple(
        name
        for name, member in inspect.getmembers(
            B02._EpisodeRebuildContext,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    )
    _assert(coordinator_public == ("read_published_view", "transact"), f"coordinator method surface changed {coordinator_public}")
    _assert(context_public == ("commit_physical_reset_complete",), f"reset context leaks capability {context_public}")
    _assert("_EpisodeRebuildInputs" not in B02.__all__ and "_EpisodeRebuildContext" not in B02.__all__, "private reset protocol exported")
    for path in (
        SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_TASK_SOURCE / "assignment_harl_wrapper.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_TASK_SOURCE / "assignment_controller.py",
        SCAN_TASK_SOURCE / "__init__.py",
    ):
        source = path.read_text(encoding="utf-8")
        _assert("_EpisodeRebuildInputs" not in source and "_episode_rebuild" not in source, f"production wiring in {path.name}")
    blocked = sorted(name for name in sys.modules if name == "isaaclab" or name.startswith(("isaaclab.", "omni", "pxr", "harl")))
    _assert(blocked == [], f"heavy modules imported {blocked}")
    _assert(random.getstate() == python_rng, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), torch_rng), "Torch RNG changed")
    _assert(_logger_state() == logger_state, "logger changed")
    _assert(_file_inventory() == files, "filesystem changed")
    _assert(Path.cwd() == cwd and dict(os.environ) == environment and tuple(sys.path) == sys_path, "process state changed")
    return {"existing_profiles_rejected": 4, "raw_profiles_rejected": len(raw), "runtime_readiness": event.runtime_readiness.value, "production_wiring": "absent", "side_effects": "none", "reset_context_public": list(context_public), "b0_2_public_unchanged": True}


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I1-T1_canonical_initial_bootstrap", test_i1_t1_canonical_initial_bootstrap),
    ("I1-T2_ordinary_later_rebuild", test_i1_t2_ordinary_later_rebuild),
    ("I1-T3_episode_sensitive_state_clearing", test_i1_t3_episode_sensitive_state_clearing),
    ("I1-T4_partial_reset", test_i1_t4_partial_reset),
    ("I1-T5_no_outstanding_transition", test_i1_t5_no_outstanding_transition),
    ("I1-T6_invalid_reset_inputs", test_i1_t6_invalid_reset_inputs),
    ("I1-T7_abort_before_physical_completion", test_i1_t7_abort_before_physical_completion),
    ("I1-T8_exact_success_count_order", test_i1_t8_exact_success_count_order),
    ("I1-T9_clock_failure_after_state_swap", test_i1_t9_clock_failure_after_state_swap),
    ("I1-T10_publication_failure_after_episode_advance", test_i1_t10_publication_failure_after_episode_advance),
    ("I1-T11_publication_atomicity", test_i1_t11_publication_atomicity),
    ("I1-T12_default_off_profile_isolation", test_i1_t12_default_off_profile_isolation),
)


def run_suite() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = 0
    for name, operation in TESTS:
        try:
            evidence = operation()
        except BaseException as exc:
            results.append({"name": name, "status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
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
        "evidence": {"groups": "I1-T1..I1-T12", "publication_synchronization": "threading.Event", "sleep_based_races": False, "device": str(DEVICE)},
        "runtime_boundary": {"episode_rebuild": "pure_default_off", "environment_wiring": "absent", "isaac_applauncher": "not_imported", "training_playback_evaluation": "not_run"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = run_suite()
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
