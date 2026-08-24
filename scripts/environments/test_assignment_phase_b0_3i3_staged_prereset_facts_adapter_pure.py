"""Pure B0-3I3 staged pre-reset reporter/facts-adapter regressions."""

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
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"

PROFILE_PATH = SCAN_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = SCAN_SOURCE / "assignment_lifecycle_transition_contract.py"
EVENT_PATH = SCAN_SOURCE / "assignment_event_contract.py"
B01_PATH = SCAN_SOURCE / "assignment_lifecycle_authority_runtime.py"
B02_PATH = SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py"
DOMAIN_PATH = SCAN_SOURCE / "assignment_event_profile_runtime_domain.py"

PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
PROFILE_MODULE = f"{PREFIX}.assignment_profile_contract"
TRANSITION_MODULE = f"{PREFIX}.assignment_lifecycle_transition_contract"
EVENT_MODULE = f"{PREFIX}.assignment_event_contract"
B01_MODULE = f"{PREFIX}.assignment_lifecycle_authority_runtime"
B02_MODULE = f"{PREFIX}.assignment_lifecycle_transaction_runtime"
DOMAIN_MODULE = f"{PREFIX}.assignment_event_profile_runtime_domain"
DEVICE = torch.device("cpu")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_namespace_packages() -> None:
    for name, path in (
        ("isaaclab_tasks", TASKS_SOURCE),
        ("isaaclab_tasks.direct", DIRECT_SOURCE),
        (PREFIX, SCAN_SOURCE),
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
DOMAIN = _load(DOMAIN_MODULE, DOMAIN_PATH)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason


def _i(values: Any, *, dtype: torch.dtype = torch.int64) -> torch.Tensor:
    return torch.tensor(values, dtype=dtype, device=DEVICE)


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
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code {exc}")
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _domain(
    *,
    env_ids: tuple[int, ...],
    num_robots: int = 2,
    num_tasks: int = 2,
    control: Any = None,
) -> Any:
    spec = DOMAIN._EventProfileLifecycleDomainSpec(
        _event_profile(),
        device=DEVICE,
        env_ids=_i(env_ids),
        num_robots=num_robots,
        num_tasks=num_tasks,
    )
    return DOMAIN._EventProfileLifecycleRuntimeDomain(spec, _test_control=control)


def _reset(domain: Any) -> Any:
    identity = domain.identity
    env_ids = identity.env_ids
    with domain.environment_port.episode_rebuild(
        selected_env_ids=env_ids,
        initial_task_state=torch.full(
            (identity.num_envs, identity.num_tasks),
            int(TaskState.AVAILABLE),
            dtype=torch.int64,
        ),
        initial_robot_state=torch.full(
            (identity.num_envs, identity.num_robots),
            int(RobotState.NEEDS_ASSIGNMENT),
            dtype=torch.int64,
        ),
        initial_ownership=torch.full(
            (identity.num_envs, identity.num_tasks), -1, dtype=torch.int64
        ),
    ) as rebuild:
        return rebuild.commit_physical_reset_complete()


def _report(
    domain: Any,
    *,
    coverage: torch.Tensor | None = None,
    candidate: torch.Tensor | None = None,
    timeout: torch.Tensor | None = None,
) -> Any:
    identity = domain.identity
    coverage = (
        torch.zeros((identity.num_envs, identity.num_tasks), dtype=torch.bool)
        if coverage is None
        else coverage
    )
    candidate = (
        torch.zeros(
            (identity.num_envs, identity.num_robots, identity.num_tasks),
            dtype=torch.bool,
        )
        if candidate is None
        else candidate
    )
    timeout = (
        torch.zeros((identity.num_envs,), dtype=torch.bool)
        if timeout is None
        else timeout
    )
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=coverage,
        raw_new_candidate=candidate,
        physical_truncated=timeout,
        time_limit_reached=timeout,
    )


def _install_state(
    domain: Any,
    *,
    task_state: torch.Tensor,
    robot_state: torch.Tensor,
    ownership: torch.Tensor,
) -> None:
    """Install a coherent pure-test prestate without adding a runtime setter."""

    coordinator = domain._coordinator
    store = domain._state_store
    with coordinator._publication_lock:
        with store._lock:
            prior = store._state
            replacement = B02._LifecycleStoreState(
                version=prior.version + 1,
                task_state=task_state.detach().clone().contiguous(),
                robot_state=robot_state.detach().clone().contiguous(),
                ownership=ownership.detach().clone().contiguous(),
                cumulative_failed_pairs=prior.cumulative_failed_pairs,
                completion_count=prior.completion_count,
                termination_reason=torch.full_like(
                    prior.termination_reason, int(Reason.NONE)
                ),
            )
            store._state = replacement
            snapshot = B02.LifecycleStateSnapshot._create(
                store_identity=store._store_identity,
                device=store._device,
                env_id=store._env_id,
                state=replacement,
            )
        rows = domain._clock.snapshot(store._env_id)
        episode = _i(tuple(row.episode_generation for row in rows))
        transition = _i(tuple(row.transition_generation for row in rows))
        coordinator._published_view = B02.PublishedLifecycleView._create(
            state_snapshot=snapshot,
            episode_generation=episode,
            transition_generation=transition,
            result=None,
        )


def _active_owner_state(domain: Any, *, task: int = 0, owner: int = 0) -> None:
    identity = domain.identity
    task_state = torch.full(
        (identity.num_envs, identity.num_tasks),
        int(TaskState.AVAILABLE),
        dtype=torch.int64,
    )
    ownership = torch.full(
        (identity.num_envs, identity.num_tasks), -1, dtype=torch.int64
    )
    robot_state = torch.full(
        (identity.num_envs, identity.num_robots),
        int(RobotState.NEEDS_ASSIGNMENT),
        dtype=torch.int64,
    )
    task_state[:, task] = int(TaskState.CLAIMED)
    ownership[:, task] = owner
    robot_state[:, owner] = int(RobotState.EXECUTING)
    _install_state(
        domain,
        task_state=task_state,
        robot_state=robot_state,
        ownership=ownership,
    )


def _ledger_counts(domain: Any) -> tuple[int, int, int]:
    snapshot = domain._ledger.snapshot()
    return (
        len(snapshot["consumed_tokens"]),
        int(snapshot["issued_receipt_count"]),
        int(snapshot["finalized_receipt_count"]),
    )


def _public_surface(cls: type[Any]) -> tuple[str, ...]:
    methods = tuple(
        name
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    )
    properties = tuple(
        name for name, member in vars(cls).items() if isinstance(member, property)
    )
    return tuple(sorted((*methods, *properties)))


def test_i3_t1_staged_report_validation() -> dict[str, Any]:
    domain = _domain(env_ids=(51000, 51001), num_robots=2, num_tasks=3)
    valid = _report(domain)
    _assert(valid.num_envs == 2 and valid.num_robots == 2 and valid.num_tasks == 3, "report dimensions")
    source = valid.raw_new_candidate
    source.fill_(True)
    _assert(not bool(valid.raw_new_candidate.any()), "report accessor alias")
    noncontiguous = torch.zeros((2, 2, 6), dtype=torch.bool)[:, :, ::2]
    accepted = _report(domain, candidate=noncontiguous)
    _assert(accepted.raw_new_candidate.is_contiguous(), "noncontiguous ingress not captured")
    failures = 0
    invalid_builders = (
        lambda: DOMAIN._StagedPreResetPhysicalReport(
            device=DEVICE,
            coverage_before_transition=torch.zeros((2, 3), dtype=torch.int64),
            raw_new_candidate=torch.zeros((2, 2, 3), dtype=torch.bool),
            physical_truncated=torch.zeros(2, dtype=torch.bool),
            time_limit_reached=torch.zeros(2, dtype=torch.bool),
        ),
        lambda: DOMAIN._StagedPreResetPhysicalReport(
            device=DEVICE,
            coverage_before_transition=torch.zeros((2, 2), dtype=torch.bool),
            raw_new_candidate=torch.zeros((2, 2, 3), dtype=torch.bool),
            physical_truncated=torch.zeros(2, dtype=torch.bool),
            time_limit_reached=torch.zeros(2, dtype=torch.bool),
        ),
        lambda: DOMAIN._StagedPreResetPhysicalReport(
            device=DEVICE,
            coverage_before_transition=torch.zeros((2, 3), dtype=torch.bool),
            raw_new_candidate=torch.zeros((2, 3), dtype=torch.bool),
            physical_truncated=torch.zeros(2, dtype=torch.bool),
            time_limit_reached=torch.zeros(2, dtype=torch.bool),
        ),
        lambda: DOMAIN._StagedPreResetPhysicalReport(
            device=DEVICE,
            coverage_before_transition=torch.zeros((2, 3), dtype=torch.bool),
            raw_new_candidate=torch.zeros((2, 2, 3), dtype=torch.bool),
            physical_truncated=_i((1, 0), dtype=torch.bool),
            time_limit_reached=torch.zeros(2, dtype=torch.bool),
        ),
    )
    for operation in invalid_builders:
        _expect_error(DOMAIN._EventProfileLifecycleDomainRuntimeError, operation)
        failures += 1
    wrong_domain = _domain(env_ids=(51010,), num_robots=2, num_tasks=2)
    _reset(wrong_domain)
    _expect_error(
        DOMAIN._EventProfileLifecycleDomainRuntimeError,
        lambda: wrong_domain.environment_port.finalize_physical_transition(valid),
        code="report_domain",
    )
    return {"valid_shape": [2, 2, 3], "validation_failures": failures + 1, "bad_transition_input": "absent"}


def test_i3_t2_no_event_all_e_transition() -> dict[str, Any]:
    domain = _domain(env_ids=(51100, 51101), num_robots=2, num_tasks=2)
    before = _reset(domain)
    outcome = domain.environment_port.finalize_physical_transition(_report(domain))
    after = outcome.published_view
    _assert(after.store_version == before.store_version + 1, "store version")
    _assert(tuple(after.transition_generation.tolist()) == (0, 0), "all-E generation")
    _assert(outcome.result.lifecycle_events == (), "unexpected events")
    _assert(not bool(outcome.coverage_after_transition.any()), "coverage changed")
    _assert(_ledger_counts(domain) == (2, 1, 1), "ledger counts")
    return {"all_rows": 2, "transition_generation": [0, 0], "events": 0}


def test_i3_t3_passive_non_owner_counterexample() -> dict[str, Any]:
    domain = _domain(env_ids=(51200,), num_robots=2, num_tasks=1)
    _reset(domain)
    _active_owner_state(domain, owner=0)
    candidate = torch.zeros((1, 2, 1), dtype=torch.bool)
    candidate[0, 1, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    _assert(not bool(outcome.completion_signals.any()), "passive candidate completed")
    _assert(not bool(outcome.canonical_task_completion.any()), "task completion")
    _assert(not bool(outcome.coverage_after_transition.any()), "passive coverage")
    _assert(int(outcome.result.termination_reason[0]) == int(Reason.NONE), "passive terminal")
    _assert(outcome.result.lifecycle_events == (), "passive event")
    return {"passive_raw": True, "canonical_completion": False, "terminated": False}


def test_i3_t4_exact_owner_completion() -> dict[str, Any]:
    domain = _domain(env_ids=(51300,), num_robots=2, num_tasks=2)
    _reset(domain)
    _active_owner_state(domain, owner=0)
    candidate = torch.zeros((1, 2, 2), dtype=torch.bool)
    candidate[0, 0, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    _assert(bool(outcome.completion_signals[0, 0, 0]), "owner missing")
    _assert(int(outcome.result.updated_task_state[0, 0]) == int(TaskState.COMPLETED), "task not completed")
    _assert(int(outcome.published_view.lifecycle_state.completion_count[0, 0]) == 1, "owner count")
    _assert(bool(outcome.coverage_after_transition[0, 0]), "coverage missing")
    event_types = tuple(event.event_type for event in outcome.result.lifecycle_events)
    _assert(event_types[0] is EVENT.LifecycleEventType.TASK_COMPLETED, "completion event")
    return {"owner": 0, "completion_count": 1, "event": "task_completed"}


def test_i3_t5_owner_completes_last_task() -> dict[str, Any]:
    domain = _domain(env_ids=(51400,), num_robots=2, num_tasks=1)
    _reset(domain)
    _active_owner_state(domain, owner=0)
    candidate = torch.zeros((1, 2, 1), dtype=torch.bool)
    candidate[0, 0, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    _assert(int(outcome.result.termination_reason[0]) == int(Reason.ALL_TASKS_COMPLETED), "reason")
    _assert(bool(outcome.terminated[0]) and not bool(outcome.truncated[0]), "Gym projection")
    _assert(bool(outcome.coverage_after_transition.all()), "coverage")
    return {"physical_terminated": True, "reason": "ALL_TASKS_COMPLETED", "terminated": True}


def test_i3_t6_mixed_owner_nonowner_candidates() -> dict[str, Any]:
    domain = _domain(env_ids=(51500,), num_robots=3, num_tasks=2)
    _reset(domain)
    _active_owner_state(domain, owner=1)
    candidate = torch.zeros((1, 3, 2), dtype=torch.bool)
    candidate[0, :, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    _assert(int(outcome.completion_signals.sum()) == 1, "duplicate completion")
    _assert(bool(outcome.completion_signals[0, 1, 0]), "wrong owner")
    counts = outcome.published_view.lifecycle_state.completion_count[0]
    _assert(tuple(counts.tolist()) == (0, 1, 0), "nonowner credit")
    return {"raw_candidates": 3, "canonical_completers": 1, "credited_owner": 1}


def test_i3_t7_structural_reporters_remain_deferred() -> dict[str, Any]:
    report_signature = inspect.signature(DOMAIN._StagedPreResetPhysicalReport)
    port_signature = inspect.signature(
        DOMAIN._EventProfileLifecycleEnvironmentPort.finalize_physical_transition
    )
    forbidden = (
        "terminal_pair_failure_signals",
        "forced_release_signals",
        "robot_unavailable_signals",
        "robot_recovered_signals",
    )
    combined = f"{report_signature} {port_signature}"
    _assert(not any(name in combined for name in forbidden), "deferred reporter exposed")
    return {"physical_team_regression": "B0-2", "deferred_reporters": list(forbidden)}


def test_i3_t8_timeout_and_priority() -> dict[str, Any]:
    timeout_domain = _domain(env_ids=(51600,), num_robots=2, num_tasks=1)
    _reset(timeout_domain)
    timeout = _i((1,), dtype=torch.bool)
    timeout_outcome = timeout_domain.environment_port.finalize_physical_transition(
        _report(timeout_domain, timeout=timeout)
    )
    _assert(int(timeout_outcome.result.termination_reason[0]) == int(Reason.TIME_LIMIT), "timeout reason")
    _assert(not bool(timeout_outcome.terminated[0]) and bool(timeout_outcome.truncated[0]), "timeout projection")

    complete_domain = _domain(env_ids=(51610,), num_robots=2, num_tasks=1)
    _reset(complete_domain)
    _active_owner_state(complete_domain, owner=0)
    candidate = torch.zeros((1, 2, 1), dtype=torch.bool)
    candidate[0, 0, 0] = True
    complete = complete_domain.environment_port.finalize_physical_transition(
        _report(complete_domain, candidate=candidate, timeout=timeout)
    )
    _assert(int(complete.result.termination_reason[0]) == int(Reason.ALL_TASKS_COMPLETED), "terminal priority")
    _assert(bool(complete.terminated[0]) and not bool(complete.truncated[0]), "priority projection")
    return {"timeout": "TIME_LIMIT", "simultaneous_completion": "ALL_TASKS_COMPLETED"}


def test_i3_t9_canonical_coverage_outcome() -> dict[str, Any]:
    domain = _domain(env_ids=(51700,), num_robots=2, num_tasks=2)
    _reset(domain)
    _active_owner_state(domain, task=1, owner=0)
    coverage = _i(((1, 0),), dtype=torch.bool)
    candidate = torch.zeros((1, 2, 2), dtype=torch.bool)
    candidate[0, 1, 1] = True
    passive = domain.environment_port.finalize_physical_transition(
        _report(domain, coverage=coverage, candidate=candidate)
    )
    _assert(tuple(passive.coverage_after_transition[0].tolist()) == (True, False), "raw candidate changed coverage")
    _assert(torch.equal(passive.coverage_after_transition, coverage | passive.result.completed_tasks), "coverage equation")
    return {"coverage_equation": "coverage0 OR result.completed_tasks", "passive_ignored": True}


def test_i3_t10_success_counts() -> dict[str, Any]:
    domain = _domain(env_ids=(51800, 51801), num_robots=2, num_tasks=2)
    before = _reset(domain)
    ledger0 = _ledger_counts(domain)
    token0 = tuple(B01._NEXT_TOKEN_BY_ENV.get(env, 0) for env in (51800, 51801))
    outcome = domain.environment_port.finalize_physical_transition(_report(domain))
    token1 = tuple(B01._NEXT_TOKEN_BY_ENV[env] for env in (51800, 51801))
    _assert(_ledger_counts(domain) == (ledger0[0] + 2, ledger0[1] + 1, ledger0[2] + 1), "ledger/finalize count")
    _assert(outcome.published_view.store_version == before.store_version + 1, "swap count")
    _assert(tuple(outcome.published_view.transition_generation.tolist()) == (0, 0), "clock count")
    _assert(token1 == tuple(value + 1 for value in token0), "producer count")
    _assert(domain._pending_transition is None, "outstanding pending not cleared")
    return {"producer": 1, "consume": 1, "finalize": 1, "swap": 1, "clock": 1, "publication": 1}


def test_i3_t11_receipt_free_failure_retry() -> dict[str, Any]:
    control = DOMAIN._PhysicalTransitionAdapterTestControl()
    domain = _domain(env_ids=(51900,), num_robots=2, num_tasks=2, control=control)
    _reset(domain)
    first = domain.environment_port.finalize_physical_transition(_report(domain))
    first_token = int(first.result.facts_consume_token[0])
    first_generation = int(first.result.transition_generation[0])
    report = _report(domain)
    control.fail_next_facts_build = True
    before = domain.current_read_port.read_current()
    _expect_error(Exception, lambda: domain.environment_port.finalize_physical_transition(report))
    pending = domain._pending_transition
    _assert(pending is not None and pending.report is report, "pending report/context lost")
    row = domain._clock.snapshot(domain.identity.env_ids)[0]
    _assert(row.transition_generation == first_generation, "generation committed on failure")
    _assert(row.outstanding_transition_generation == first_generation + 1, "context not outstanding")
    _assert(domain.current_read_port.read_current() is before, "publication changed")
    _expect_error(
        DOMAIN._EventProfileLifecycleDomainRuntimeError,
        lambda: domain.environment_port.finalize_physical_transition(_report(domain)),
        code="pending_report_identity",
    )
    retry = domain.environment_port.finalize_physical_transition(report)
    retry_token = int(retry.result.facts_consume_token[0])
    retry_generation = int(retry.result.transition_generation[0])
    _assert(retry_token - first_token == 2, "burned token gap missing")
    _assert(retry_generation - first_generation == 1, "generation gap created")
    _assert(domain._pending_transition is None, "pending not cleared after retry")
    return {"token_delta": 2, "transition_delta": 1, "same_report": True, "automatic_retry": False}


def test_i3_t12_stale_prestate_rejection() -> dict[str, Any]:
    reached, release = Event(), Event()
    control = DOMAIN._PhysicalTransitionAdapterTestControl(
        after_prestate_reached=reached,
        after_prestate_release=release,
    )
    domain = _domain(env_ids=(52000,), num_robots=2, num_tasks=2, control=control)
    _reset(domain)
    report = _report(domain)
    outcome: dict[str, Any] = {}

    def worker() -> None:
        try:
            domain.environment_port.finalize_physical_transition(report)
        except BaseException as exc:
            outcome["error"] = exc

    thread = Thread(target=worker, name="b03i3-stale-prestate")
    try:
        thread.start()
        _assert(reached.wait(timeout=10.0), "prestate interlock not reached")
        store = domain._state_store
        with store._lock:
            state = store._state
            store._state = B02._LifecycleStoreState(
                version=state.version + 1,
                task_state=state.task_state,
                robot_state=state.robot_state,
                ownership=state.ownership,
                cumulative_failed_pairs=state.cumulative_failed_pairs,
                completion_count=state.completion_count,
                termination_reason=state.termination_reason,
            )
    finally:
        release.set()
        thread.join(timeout=10.0)
    _assert(not thread.is_alive(), "stale worker did not join")
    error = outcome.get("error")
    _assert(type(error) is DOMAIN._EventProfileLifecycleDomainRuntimeError, f"wrong stale error {error}")
    _assert(error.failure_code == "stale_bound_prestate", "wrong stale failure code")
    _assert(_ledger_counts(domain) == (0, 0, 0), "stale prestate consumed")
    row = domain._clock.snapshot(domain.identity.env_ids)[0]
    _assert(row.transition_generation == -1 and row.outstanding_transition_generation == 0, "stale context changed")
    return {"rejected_before_consume": True, "outstanding_preserved": True}


def test_i3_t13_immutable_outcome() -> dict[str, Any]:
    domain = _domain(env_ids=(52100,), num_robots=2, num_tasks=2)
    _reset(domain)
    outcome = domain.environment_port.finalize_physical_transition(_report(domain))
    copies = (
        outcome.completion_signals,
        outcome.canonical_task_completion,
        outcome.coverage_before_transition,
        outcome.coverage_after_transition,
        outcome.terminated,
        outcome.truncated,
        outcome.published_view.transition_generation,
    )
    for value in copies:
        value.fill_(True if value.dtype is torch.bool else 999)
    fresh = domain.current_read_port.read_current()
    _assert(tuple(fresh.transition_generation.tolist()) == (0,), "generation alias")
    _assert(not bool(outcome.coverage_after_transition.any()), "outcome alias")
    _expect_error(FrozenInstanceError, lambda: setattr(outcome, "_result", None))
    next_outcome = domain.environment_port.finalize_physical_transition(_report(domain))
    _assert(int(next_outcome.result.transition_generation[0]) == 1, "next transition affected")
    return {"tensor_aliases": 0, "frozen": True, "next_transition": 1}


def test_i3_t14_terminal_handoff_extension_preserves_i3_outcome() -> dict[str, Any]:
    domain = _domain(env_ids=(52200,), num_robots=2, num_tasks=1)
    _reset(domain)
    _active_owner_state(domain, owner=0)
    candidate = torch.zeros((1, 2, 1), dtype=torch.bool)
    candidate[0, 0, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    _assert(bool(outcome.terminated[0]), "terminal outcome missing")
    key = outcome.terminal_keys[0]
    artifact = domain.terminal_observer_port().read_terminal(key)
    _assert(artifact.result is outcome.result, "I4 handoff changed I3 result identity")
    _assert(artifact.coverage_after_transition.equal(outcome.coverage_after_transition[0]), "coverage binding")
    return {"terminal_result": True, "persistent_terminal_slot": True, "i3_outcome_preserved": True}


def test_i3_t15_capability_isolation() -> dict[str, Any]:
    env_surface = _public_surface(DOMAIN._EventProfileLifecycleEnvironmentPort)
    domain_surface = _public_surface(DOMAIN._EventProfileLifecycleRuntimeDomain)
    outcome_surface = _public_surface(DOMAIN._EnvironmentPhysicalTransitionOutcome)
    _assert(
        env_surface
        == (
            "assert_physical_step_allowed",
            "domain_identity",
            "episode_rebuild",
            "finalize_physical_transition",
            "report_post_authority_bookkeeping_failure",
        ),
        f"environment surface {env_surface}",
    )
    _assert(
        domain_surface
        == (
            "current_read_port",
            "environment_admission_validation_port",
            "environment_port",
            "identity",
            "initial_claim_port",
            "interstep_fence_read_port",
            "physical_step_admission_port",
            "production_claim_port",
            "standalone_reset_admission_port",
            "terminal_consumer_port",
            "terminal_observer_port",
        ),
        f"domain surface {domain_surface}",
    )
    forbidden = {
        "producer", "clock", "store", "coordinator", "authority", "ledger",
        "reserve_context", "build_facts", "get_prestate", "commit_generation",
        "receipt", "transition_contexts",
    }
    _assert(not forbidden.intersection(env_surface + domain_surface + outcome_surface), "raw capability leak")
    _assert(tuple(DOMAIN.__all__) == (), "module exports")
    return {"environment": list(env_surface), "domain": list(domain_surface), "raw_capability_leak": False}


def test_i3_t16_default_off_no_production_wiring() -> dict[str, Any]:
    before_random = random.getstate()
    before_torch = torch.random.get_rng_state().clone()
    before_cwd = Path.cwd()
    before_env = dict(os.environ)
    before_path = tuple(sys.path)
    before_loggers = tuple(sorted(logging.Logger.manager.loggerDict))
    for index, profile in enumerate(_existing_profiles()):
        spec_operation = lambda profile=profile, index=index: DOMAIN._EventProfileLifecycleDomainSpec(
            profile,
            device=DEVICE,
            env_ids=_i((52300 + index,)),
            num_robots=2,
            num_tasks=2,
        )
        _expect_error(PROFILE.AssignmentProfileRouteError, spec_operation)
    profile = _event_profile()
    _expect_error(
        PROFILE.PhaseAExecutionNotAuthorizedError,
        lambda: PROFILE.require_assignment_profile_runtime_ready(
            profile,
            consumer="B0-3I3 staged adapter pure test",
            entrypoint="standalone pure test",
            current_phase="B0-3I3",
            barrier="production composition remains unauthorized",
        ),
    )
    targets = (
        SCAN_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_SOURCE / "assignment_harl_wrapper.py",
        SCAN_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_SOURCE / "assignment_controller.py",
        SCAN_SOURCE / "__init__.py",
    )
    hits = []
    for path in targets:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if "assignment_event_profile_runtime_domain" in text or "_StagedPreResetPhysicalReport" in text:
            hits.append(str(path))
    expected_hits = [
        str(SCAN_SOURCE / "scan_mobile_manipulator_env.py"),
        str(SCAN_SOURCE / "assignment_harl_wrapper.py"),
    ]
    _assert(hits == expected_hits, f"unexpected I4 production wiring {hits}")
    heavy = tuple(
        name for name in sys.modules
        if name.startswith(("isaaclab.", "omni.", "pxr", "harl"))
    )
    _assert(not heavy, f"heavy imports {heavy}")
    _assert(random.getstate() == before_random, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), before_torch), "Torch RNG changed")
    _assert(Path.cwd() == before_cwd and dict(os.environ) == before_env, "process state changed")
    _assert(tuple(sys.path) == before_path, "sys.path changed")
    _assert(tuple(sorted(logging.Logger.manager.loggerDict)) == before_loggers, "logger changed")
    return {
        "existing_profiles_rejected": 4,
        "production_wiring": "event environment plus private I4 wrapper composition",
        "readiness": "blocked",
        "heavy_modules": [],
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I3-T1_staged_report_validation", test_i3_t1_staged_report_validation),
    ("I3-T2_no_event_all_e_transition", test_i3_t2_no_event_all_e_transition),
    ("I3-T3_passive_non_owner_counterexample", test_i3_t3_passive_non_owner_counterexample),
    ("I3-T4_exact_owner_completion", test_i3_t4_exact_owner_completion),
    ("I3-T5_owner_completes_last_task", test_i3_t5_owner_completes_last_task),
    ("I3-T6_mixed_owner_nonowner_candidates", test_i3_t6_mixed_owner_nonowner_candidates),
    ("I3-T7_structural_reporters_remain_deferred", test_i3_t7_structural_reporters_remain_deferred),
    ("I3-T8_timeout_and_priority", test_i3_t8_timeout_and_priority),
    ("I3-T9_canonical_coverage_outcome", test_i3_t9_canonical_coverage_outcome),
    ("I3-T10_transaction_success_counts", test_i3_t10_success_counts),
    ("I3-T11_receipt_free_failure_retry", test_i3_t11_receipt_free_failure_retry),
    ("I3-T12_stale_prestate_rejection", test_i3_t12_stale_prestate_rejection),
    ("I3-T13_immutable_outcome", test_i3_t13_immutable_outcome),
    ("I3-T14_terminal_handoff_extension_preserves_i3_outcome", test_i3_t14_terminal_handoff_extension_preserves_i3_outcome),
    ("I3-T15_capability_isolation", test_i3_t15_capability_isolation),
    ("I3-T16_default_off_no_production_wiring", test_i3_t16_default_off_no_production_wiring),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    failed = 0
    for name, test in TESTS:
        try:
            evidence = test()
            results.append({"name": name, "status": "passed", "evidence": evidence})
        except BaseException as exc:
            failed += 1
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    payload = {
        "status": "passed" if failed == 0 else "failed",
        "num_tests": len(TESTS),
        "passed": len(TESTS) - failed,
        "failed": failed,
        "tests": results,
        "evidence": {
            "groups": "I3-T1..I3-T16",
            "adapter": "staged raw report -> retained producer -> B0-2 transaction",
            "bad_transition": "canonical false",
        },
        "runtime_boundary": {
            "I4": "terminal_environment_integration",
            "production_wiring": "event environment only",
            "isaac_applauncher": "not_imported",
            "training_playback_evaluation": "not_run",
        },
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for result in results:
            print(f"{result['status']}: {result['name']}")
        print(f"{payload['status']}: {payload['passed']}/{payload['num_tests']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
