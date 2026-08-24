"""Pure/default-off Phase-B1 initial-claim transaction regressions.

The runner installs namespace-only package placeholders and loads only frozen
contracts plus pure B0/B1 runtime modules.  It never imports Isaac, AppLauncher,
Omni, PXr, HARL, task discovery, training, playback, or evaluation entrypoints.
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
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"

PROFILE_PATH = SCAN_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = SCAN_SOURCE / "assignment_lifecycle_transition_contract.py"
EVENT_PATH = SCAN_SOURCE / "assignment_event_contract.py"
B01_PATH = SCAN_SOURCE / "assignment_lifecycle_authority_runtime.py"
CLAIM_PATH = SCAN_SOURCE / "assignment_initial_claim_runtime.py"
B02_PATH = SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py"
DOMAIN_PATH = SCAN_SOURCE / "assignment_event_profile_runtime_domain.py"

PROFILE_MODULE = f"{PREFIX}.assignment_profile_contract"
TRANSITION_MODULE = f"{PREFIX}.assignment_lifecycle_transition_contract"
EVENT_MODULE = f"{PREFIX}.assignment_event_contract"
B01_MODULE = f"{PREFIX}.assignment_lifecycle_authority_runtime"
CLAIM_MODULE = f"{PREFIX}.assignment_initial_claim_runtime"
B02_MODULE = f"{PREFIX}.assignment_lifecycle_transaction_runtime"
DOMAIN_MODULE = f"{PREFIX}.assignment_event_profile_runtime_domain"
DEVICE = torch.device("cpu")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _inventory() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    )


_IMPORT_RANDOM = random.getstate()
_IMPORT_TORCH_RANDOM = torch.random.get_rng_state().clone()
_IMPORT_CWD = Path.cwd()
_IMPORT_SYS_PATH = tuple(sys.path)
_IMPORT_ENV = dict(os.environ)
_IMPORT_LOGGING = (logging.root.level, tuple(logging.root.handlers))
_IMPORT_INVENTORY = _inventory()


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
CLAIM = _load(CLAIM_MODULE, CLAIM_PATH)
B02 = _load(B02_MODULE, B02_PATH)
DOMAIN = _load(DOMAIN_MODULE, DOMAIN_PATH)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason
ProvenanceKind = CLAIM._CurrentPublicationProvenanceKind
SourceKind = CLAIM._InitialClaimSourceKind


def _i(values: Any, *, device: torch.device = DEVICE) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=device)


def _b(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.bool, device=DEVICE)


def _profile() -> Any:
    return PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )


def _domain(
    *,
    env_ids: tuple[int, ...] = (71000,),
    num_robots: int = 2,
    num_tasks: int = 3,
    claim_control: Any | None = None,
) -> Any:
    spec = DOMAIN._EventProfileLifecycleDomainSpec(
        _profile(),
        device=DEVICE,
        env_ids=_i(env_ids),
        num_robots=num_robots,
        num_tasks=num_tasks,
    )
    return DOMAIN._EventProfileLifecycleRuntimeDomain(
        spec,
        _initial_claim_test_control=claim_control,
    )


def _reset(domain: Any, selected: tuple[int, ...] | None = None) -> Any:
    identity = domain.identity
    selected = tuple(identity.env_ids.tolist()) if selected is None else selected
    rows = len(selected)
    with domain.environment_port.episode_rebuild(
        selected_env_ids=_i(selected),
        initial_task_state=torch.full(
            (rows, identity.num_tasks), int(TaskState.AVAILABLE), dtype=torch.int64
        ),
        initial_robot_state=torch.full(
            (rows, identity.num_robots), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64
        ),
        initial_ownership=torch.full((rows, identity.num_tasks), -1, dtype=torch.int64),
    ) as rebuild:
        return rebuild.commit_physical_reset_complete()


def _report(
    domain: Any,
    *,
    candidate: torch.Tensor | None = None,
    timeout: torch.Tensor | None = None,
) -> Any:
    identity = domain.identity
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=torch.zeros(
            (identity.num_envs, identity.num_tasks), dtype=torch.bool
        ),
        raw_new_candidate=(
            torch.zeros(
                (identity.num_envs, identity.num_robots, identity.num_tasks),
                dtype=torch.bool,
            )
            if candidate is None
            else candidate
        ),
        physical_truncated=(
            torch.zeros(identity.num_envs, dtype=torch.bool)
            if timeout is None
            else timeout
        ),
        time_limit_reached=(
            torch.zeros(identity.num_envs, dtype=torch.bool)
            if timeout is None
            else timeout
        ),
    )


def _transition(domain: Any) -> Any:
    return domain.environment_port.finalize_physical_transition(_report(domain))


def _prepare(domain: Any, selected: tuple[int, ...], rows: Any) -> Any:
    return domain.initial_claim_port.prepare_initial_claim(
        selected_env_ids=_i(selected),
        requested_task_by_robot=_i(rows),
    )


def _claim(domain: Any, selected: tuple[int, ...], rows: Any) -> Any:
    return domain.initial_claim_port.commit_initial_claim(
        _prepare(domain, selected, rows)
    )


def _expect(
    operation: Callable[[], Any],
    *,
    code: str | None = None,
    exception: type[BaseException] = Exception,
) -> BaseException:
    try:
        operation()
    except exception as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError(f"expected {exception.__name__}")


def _state_signature(current: Any) -> tuple[torch.Tensor, ...]:
    state = current.lifecycle_state
    return (
        state.task_state,
        state.robot_state,
        state.ownership,
        state.cumulative_failed_pairs,
        state.completion_count,
        state.termination_reason,
        current.episode_generation,
        current.transition_generation,
    )


def _same_tensors(left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]) -> bool:
    return all(torch.equal(a, b) for a, b in zip(left, right, strict=True))


def test_b1_t1_canonical_reset_source_success() -> dict[str, Any]:
    domain = _domain(env_ids=(71100,))
    reset = _reset(domain)
    before = reset.store_version
    artifact = _claim(domain, (71100,), ((0, -1),))
    current = domain.current_read_port.read_current()
    _assert(tuple(reset.episode_generation.tolist()) == (0,), "episode bootstrap")
    _assert(tuple(reset.transition_generation.tolist()) == (-1,), "fake transition")
    _assert(reset.result is None and current.result is None, "fake lifecycle result")
    _assert(current.store_version == before + 1, "version delta")
    _assert(current.provenance[0].kind is ProvenanceKind.ASSIGNMENT_COMMIT, "claim provenance")
    _assert(artifact.source_publication is reset, "source publication identity")
    return {"episode": 0, "transition": -1, "version_delta": 1, "fake_result": False}


def test_b1_t2_lifecycle_transition_source_success() -> dict[str, Any]:
    domain = _domain(env_ids=(71200,))
    _reset(domain)
    outcome = _transition(domain)
    source = domain.current_read_port.read_current()
    result = outcome.result
    request = _prepare(domain, (71200,), ((1, -1),))
    artifact = domain.initial_claim_port.commit_initial_claim(request)
    current = domain.current_read_port.read_current()
    _assert(request._baseline.source_kinds == (SourceKind.FINALIZED_LIFECYCLE_TRANSITION,), "source kind")
    _assert(artifact.root_provenance[0].lifecycle_result is result, "root result")
    _assert(source.result is result and current.result is None, "result boundary")
    _assert(outcome.result.updated_ownership[0, 0].item() == -1, "result rewritten")
    return {"root_result_exact": True, "post_assignment_result": None}


def test_b1_t3_post_assignment_second_claim() -> dict[str, Any]:
    domain = _domain(env_ids=(71300,), num_robots=2, num_tasks=3)
    _reset(domain)
    first = _claim(domain, (71300,), ((0, -1),))
    first_current = domain.current_read_port.read_current()
    request = _prepare(domain, (71300,), ((-1, 1),))
    second = domain.initial_claim_port.commit_initial_claim(request)
    current = domain.current_read_port.read_current()
    _assert(request._baseline.source_kinds == (SourceKind.POST_ASSIGNMENT,), "post source")
    _assert(second.immediate_predecessor_provenance[0].assignment_artifact is first, "immediate predecessor")
    _assert(second.root_provenance[0] is first.root_provenance[0], "root changed")
    _assert(current.store_version == first_current.store_version + 1, "second version")
    _assert(torch.equal(current.transition_generation, first_current.transition_generation), "transition changed")
    return {"source": "POST_ASSIGNMENT", "root_exact": True, "successes": 2}


def test_b1_t4_c2_multi_robot_batch() -> dict[str, Any]:
    domain = _domain(env_ids=(71400,), num_robots=3, num_tasks=6)
    reset = _reset(domain)
    artifact = _claim(domain, (71400,), ((0, 2, 5),))
    current = domain.current_read_port.read_current()
    _assert(current.store_version == reset.store_version + 1, "C2 version count")
    _assert(tuple(current.lifecycle_state.ownership[0].tolist()) == (0, -1, 1, -1, -1, 2), "C2 ownership")
    _assert(torch.equal(artifact.requested_task_by_robot, artifact.effective_task_by_robot), "requested/effective values")
    _assert(artifact._requested_task_by_robot.data_ptr() != artifact._effective_task_by_robot.data_ptr(), "requested/effective alias")
    return {"claims": 3, "version_delta": 1, "atomic": True}


def test_b1_t5_nonassignable_robot_rejection() -> dict[str, Any]:
    states = (RobotState.UNAVAILABLE, RobotState.EXECUTING, RobotState.WAITING_FOR_TASK)
    for offset, state in enumerate(states):
        domain = _domain(env_ids=(71500 + offset,), num_robots=1, num_tasks=1)
        _reset(domain)
        request = _prepare(domain, (71500 + offset,), ((0,),))
        request._baseline._robot_state[0, 0] = int(state)
        _expect(
            lambda request=request, domain=domain: domain._coordinator._claim_deriver.derive_candidate(request),
            code="robot_not_assignable",
            exception=CLAIM.InitialClaimRuntimeError,
        )
        _assert(domain.current_read_port.read_current().store_version == 1, "pure rejection mutated Store")
    return {"states": [state.name for state in states], "mutations": 0}


def test_b1_t6_illegal_task_rejection() -> dict[str, Any]:
    states = (
        TaskState.CLAIMED,
        TaskState.NAVIGATING,
        TaskState.ALIGNING,
        TaskState.COMPLETED,
        TaskState.TEAM_INFEASIBLE,
    )
    for offset, state in enumerate(states):
        domain = _domain(env_ids=(71600 + offset,), num_robots=2, num_tasks=1)
        _reset(domain)
        request = _prepare(domain, (71600 + offset,), ((0, -1),))
        request._baseline._task_state[0, 0] = int(state)
        request._baseline._ownership[0, 0] = (
            1 if state in (TaskState.CLAIMED, TaskState.NAVIGATING, TaskState.ALIGNING) else -1
        )
        _expect(
            lambda request=request, domain=domain: domain._coordinator._claim_deriver.derive_candidate(request),
            code="task_not_available",
            exception=CLAIM.InitialClaimRuntimeError,
        )
    return {"illegal_states": [state.name for state in states], "all_rejected": True}


def test_b1_t7_failed_pair_rejection() -> dict[str, Any]:
    domain = _domain(env_ids=(71700,), num_robots=1, num_tasks=1)
    _reset(domain)
    request = _prepare(domain, (71700,), ((0,),))
    request._baseline._cumulative_failed_pairs[0, 0, 0] = True
    _expect(
        lambda: domain._coordinator._claim_deriver.derive_candidate(request),
        code="failed_pair",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    return {"failed_pair": [0, 0], "mutation": False}


def test_b1_t8_structural_conflict_rejection() -> dict[str, Any]:
    domain = _domain(env_ids=(71800, 71801), num_robots=2, num_tasks=2)
    _reset(domain)
    before = domain.current_read_port.read_current()
    cases = (
        lambda: _prepare(domain, (71800, 71800), ((0, -1), (1, -1))),
        lambda: _prepare(domain, (71800,), ((0, 0),)),
        lambda: _prepare(domain, (71800,), ((-2, -1),)),
        lambda: _prepare(domain, (71800,), ((2, -1),)),
        lambda: domain.initial_claim_port.prepare_initial_claim(
            selected_env_ids=torch.tensor([71800], dtype=torch.int32),
            requested_task_by_robot=_i(((0, -1),)),
        ),
        lambda: domain.initial_claim_port.prepare_initial_claim(
            selected_env_ids=_i((71800,)),
            requested_task_by_robot=_i((0, -1)),
        ),
        lambda: domain.initial_claim_port.prepare_initial_claim(
            selected_env_ids=_i((71800,), device=torch.device("meta")),
            requested_task_by_robot=_i(((0, -1),)),
        ),
    )
    for operation in cases:
        _expect(operation)
    _assert(domain.current_read_port.read_current() is before, "structural failure published")
    return {"cases": len(cases), "batch_mutation": False}


def test_b1_t9_g2_terminal_row_block() -> dict[str, Any]:
    domain = _domain(env_ids=(71900, 71901), num_robots=2, num_tasks=2)
    _reset(domain)
    timeout = _b((True, False))
    terminal = domain.environment_port.finalize_physical_transition(
        _report(domain, timeout=timeout)
    )
    key = terminal.terminal_keys[0]
    _reset(domain, (71900,))
    blocked_request = _prepare(domain, (71900,), ((0, -1),))
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(blocked_request),
        code="terminal_slot_occupied",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    domain.terminal_consumer_port.acknowledge_terminal(key)
    retried = domain.initial_claim_port.commit_initial_claim(blocked_request)

    other_domain = _domain(env_ids=(71910, 71911), num_robots=2, num_tasks=2)
    _reset(other_domain)
    other_terminal = other_domain.environment_port.finalize_physical_transition(
        _report(other_domain, timeout=_b((True, False)))
    )
    _reset(other_domain, (71910,))
    other = _claim(other_domain, (71911,), ((0, -1),))
    _expect(other_domain.environment_port.assert_physical_step_allowed, code="terminal_ack_required", exception=B02.LifecycleCoordinatorRuntimeError)
    _assert(retried.token == 0 and other.token == 0 and not domain._coordinator.poisoned, "G2 retry")
    _assert(other_terminal.terminal_keys[0] is not None, "unselected terminal fixture")
    return {"selected_blocked": True, "unselected_ignored": True, "retry_after_ack": True, "r3_global": True}


def test_b1_t10_stale_source_rejection() -> dict[str, Any]:
    domain = _domain(env_ids=(72000,), num_robots=2, num_tasks=2)
    _reset(domain)
    first = _prepare(domain, (72000,), ((0, -1),))
    stale = _prepare(domain, (72000,), ((-1, 1),))
    domain.initial_claim_port.commit_initial_claim(first)
    before = domain.current_read_port.read_current()
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(stale),
        code="stale_source",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain.current_read_port.read_current() is before, "stale request mutated")
    old_after_reset = _prepare(domain, (72000,), ((-1, 1),))
    _reset(domain)
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(old_after_reset),
        code="stale_source",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    return {"publication_store_state_generation_provenance": "stale", "rebase": False}


def test_b1_t11_request_effective_no_alias() -> dict[str, Any]:
    domain = _domain(env_ids=(72100,), num_robots=2, num_tasks=2)
    _reset(domain)
    selected = _i((72100,))
    requested = _i(((0, -1),))
    request = domain.initial_claim_port.prepare_initial_claim(
        selected_env_ids=selected,
        requested_task_by_robot=requested,
    )
    selected.fill_(0)
    requested.fill_(1)
    artifact = domain.initial_claim_port.commit_initial_claim(request)
    request_copy = request.requested_task_by_robot
    effective_copy = artifact.effective_task_by_robot
    request_copy.fill_(1)
    effective_copy.fill_(1)
    _assert(tuple(request.requested_task_by_robot[0].tolist()) == (0, -1), "request alias")
    _assert(tuple(artifact.effective_task_by_robot[0].tolist()) == (0, -1), "effective alias")
    _expect(lambda: setattr(request, "token", 9), exception=(FrozenInstanceError, AttributeError, TypeError))
    return {"request_effective_separate": True, "caller_alias": False, "immutable": True}


def test_b1_t12_assignment_owned_only_fields() -> dict[str, Any]:
    domain = _domain(env_ids=(72200, 72201), num_robots=2, num_tasks=3)
    before = _reset(domain)
    before_sig = _state_signature(before)
    artifact = _claim(domain, (72200,), ((0, -1),))
    after = domain.current_read_port.read_current()
    after_sig = _state_signature(after)
    _assert(torch.equal(before_sig[3], after_sig[3]), "failed pairs changed")
    _assert(torch.equal(before_sig[4], after_sig[4]), "completion count changed")
    _assert(torch.equal(before_sig[5], after_sig[5]), "reason changed")
    _assert(torch.equal(before_sig[6], after_sig[6]) and torch.equal(before_sig[7], after_sig[7]), "generation changed")
    for index in (0, 1, 2):
        _assert(torch.equal(before_sig[index][1], after_sig[index][1]), "unselected row changed")
    _assert(artifact.committed_store_version == artifact.source_store_version + 1, "version")
    return {"allowed": ["task_state", "robot_state", "ownership", "store_version", "P2"], "lifecycle_fields_bit_exact": True}


def test_b1_t13_historical_result_immutable() -> dict[str, Any]:
    domain = _domain(env_ids=(72300,))
    _reset(domain)
    outcome = _transition(domain)
    result = outcome.result
    tensors = tuple(
        value.detach().clone()
        for value in (
            result.updated_task_state,
            result.updated_robot_state,
            result.updated_ownership,
            result.updated_failed_pairs,
            result.facts_consume_token,
            result.authority_receipt_id,
        )
    )
    events = result.lifecycle_events
    _claim(domain, (72300,), ((0, -1),))
    current = domain.current_read_port.read_current()
    observed = (
        result.updated_task_state,
        result.updated_robot_state,
        result.updated_ownership,
        result.updated_failed_pairs,
        result.facts_consume_token,
        result.authority_receipt_id,
    )
    _assert(all(torch.equal(a, b) for a, b in zip(tensors, observed, strict=True)), "historical result tensors changed")
    _assert(result.lifecycle_events == events and current.result is None, "historical events/result changed")
    return {"result_identity": id(result), "tensors_exact": True, "events_exact": True}


def test_b1_t14_reader_atomicity() -> dict[str, Any]:
    after_swap, release = Event(), Event()
    control = B02._InitialClaimTestControl(
        after_state_swap_reached=after_swap,
        after_state_swap_release=release,
    )
    domain = _domain(env_ids=(72400,), claim_control=control)
    old = _reset(domain)
    request = _prepare(domain, (72400,), ((0, -1),))
    outcomes: dict[str, Any] = {}
    errors: list[BaseException] = []
    reader_started = Event()

    def writer() -> None:
        try:
            outcomes["artifact"] = domain.initial_claim_port.commit_initial_claim(request)
        except BaseException as exc:
            errors.append(exc)

    def reader() -> None:
        reader_started.set()
        try:
            outcomes["current"] = domain.current_read_port.read_current()
        except BaseException as exc:
            errors.append(exc)

    wt, rt = Thread(target=writer), Thread(target=reader)
    wt.start()
    _assert(after_swap.wait(10.0), "writer did not reach post-swap interlock")
    rt.start()
    _assert(reader_started.wait(10.0), "reader did not start")
    _assert("current" not in outcomes, "reader observed mixed tail")
    release.set()
    wt.join(10.0)
    rt.join(10.0)
    _assert(not errors and not wt.is_alive() and not rt.is_alive(), f"thread failure {errors}")
    new = outcomes["current"]
    _assert(new is domain.current_read_port.read_current(), "reader did not receive current P2")
    _assert(new.store_version == old.store_version + 1, "reader version")
    return {"old_old_or_new_new": True, "reader_blocked": True, "sleep": False}


def test_b1_t15_post_swap_failure_poison() -> dict[str, Any]:
    control = B02._InitialClaimTestControl(fail_after_state_swap=True)
    domain = _domain(env_ids=(72500,), claim_control=control)
    old = _reset(domain)
    request = _prepare(domain, (72500,), ((0, -1),))
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(request),
        code="fatal_post_claim_swap_failure",
        exception=B02.LifecycleCoordinatorRuntimeError,
    )
    _assert(domain._coordinator.poisoned, "coordinator not poisoned")
    _assert(domain._state_store._state.version == old.store_version + 1, "Store rolled back")
    _assert(domain._coordinator._published_view is old, "substitute P2 installed")
    _assert(request.token in domain._coordinator._active_claim_contexts, "request marker changed")
    _expect(domain.current_read_port.read_current, code="coordinator_poisoned", exception=B02.LifecycleCoordinatorRuntimeError)
    return {"poison": True, "rollback": False, "retry": False, "publication": "old"}


def test_b1_t16_duplicate_consume_replay() -> dict[str, Any]:
    domain = _domain(env_ids=(72600,))
    _reset(domain)
    request = _prepare(domain, (72600,), ((0, -1),))
    domain.initial_claim_port.commit_initial_claim(request)
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(request),
        code="request_consumed",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain._coordinator._consumed_claim_token_intervals == ((request.token, request.token),), "consumed compaction")
    return {"token": request.token, "replay": "rejected", "registry": "interval_compacted"}


def test_b1_t17_default_off_no_production_wiring() -> dict[str, Any]:
    production_files = (
        SCAN_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_SOURCE / "assignment_harl_wrapper.py",
        SCAN_SOURCE / "assignment_lifecycle_resolver.py",
        REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py",
    )
    forbidden = ("InitialClaim", "initial_claim", "ASSIGNMENT_COMMIT", "claim_window")
    hits: list[str] = []
    for path in production_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for symbol in forbidden:
            if symbol in text:
                hits.append(f"{path}:{symbol}")
    origin = PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    rejected = 0
    for name in (
        PROFILE.AssignmentProfileName.LEGACY,
        PROFILE.AssignmentProfileName.LIFECYCLE_CONTRACT_C,
        PROFILE.AssignmentProfileName.LIFECYCLE_ABLATION,
        PROFILE.AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
    ):
        profile = PROFILE.resolve_assignment_profile(name, origin)
        try:
            DOMAIN._EventProfileLifecycleDomainSpec(
                profile,
                device=DEVICE,
                env_ids=_i((1,)),
                num_robots=1,
                num_tasks=1,
            )
        except PROFILE.AssignmentProfileRouteError:
            rejected += 1
    _assert(not hits and rejected == 4, f"production/default isolation {hits}, {rejected}")
    _assert(tuple(CLAIM.__all__) == () and tuple(DOMAIN.__all__) == (), "public export")
    _assert("initial_claim_port" not in inspect.getsource(DOMAIN._EventProfileLifecycleEnvironmentPort), "environment capability leak")
    return {"production_hits": [], "existing_profiles_rejected": 4, "public_exports": 0, "claim_window": False}


def test_b1_t18_frozen_contract_and_side_effect_audit() -> dict[str, Any]:
    expected = {
        "assignment_lifecycle_transition_contract.py": "1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9",
        "assignment_event_contract.py": "22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A",
        "assignment_profile_contract.py": "ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500",
        "assignment_event_profile_schema_contract.py": "04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF",
    }
    from hashlib import sha256

    actual = {name: sha256((SCAN_SOURCE / name).read_bytes()).hexdigest().upper() for name in expected}
    _assert(actual == expected, f"frozen hash drift {actual}")
    _assert(random.getstate() == _IMPORT_RANDOM, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), _IMPORT_TORCH_RANDOM), "Torch RNG changed")
    _assert(Path.cwd() == _IMPORT_CWD and tuple(sys.path) == _IMPORT_SYS_PATH, "cwd/sys.path changed")
    _assert(dict(os.environ) == _IMPORT_ENV, "environment changed")
    _assert((logging.root.level, tuple(logging.root.handlers)) == _IMPORT_LOGGING, "logging changed")
    _assert(_inventory() == _IMPORT_INVENTORY, "filesystem inventory changed")
    heavy = sorted(
        name
        for name in sys.modules
        if name == "isaaclab"
        or name.startswith(("isaaclab.", "omni", "pxr", "harl"))
    )
    _assert(not heavy, f"heavy modules imported {heavy}")
    return {"frozen_hashes": 4, "global_side_effects": "none", "heavy_modules": []}


def test_b1_t19_noop_and_mixed_batch_atomicity() -> dict[str, Any]:
    domain = _domain(env_ids=(72900, 72901), num_robots=2, num_tasks=2)
    _reset(domain)
    _expect(lambda: _prepare(domain, (), ()), code="empty_request", exception=CLAIM.InitialClaimRuntimeError)
    _expect(lambda: _prepare(domain, (72900,), ((-1, -1),)), code="empty_selected_row", exception=CLAIM.InitialClaimRuntimeError)
    request = _prepare(domain, (72900, 72901), ((0, -1), (0, -1)))
    request._baseline._cumulative_failed_pairs[1, 0, 0] = True
    before = domain.current_read_port.read_current()
    _expect(
        lambda: domain.initial_claim_port.commit_initial_claim(request),
        code="stale_source",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain.current_read_port.read_current() is before, "mixed batch partially committed")
    valid = _prepare(domain, (72900, 72901), ((0, -1), (0, -1)))
    valid._baseline._cumulative_failed_pairs[1, 0, 0] = True
    _expect(
        lambda: domain._coordinator._claim_deriver.derive_candidate(valid),
        code="failed_pair",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain._state_store._state.version == before.store_version, "mixed batch Store version")
    return {"empty_rejected": True, "empty_row_rejected": True, "mixed_atomic": True}


def test_b1_t20_concurrency_and_partial_provenance() -> dict[str, Any]:
    reached, release = Event(), Event()
    control = B02._InitialClaimTestControl(
        before_state_swap_reached=reached,
        before_state_swap_release=release,
    )
    domain = _domain(env_ids=(73000,), num_robots=2, num_tasks=2, claim_control=control)
    _reset(domain)
    first = _prepare(domain, (73000,), ((0, -1),))
    second = _prepare(domain, (73000,), ((-1, 1),))
    outcomes: list[Any] = []
    errors: list[BaseException] = []
    second_started = Event()

    def commit_first() -> None:
        try:
            outcomes.append(domain.initial_claim_port.commit_initial_claim(first))
        except BaseException as exc:
            errors.append(exc)

    def commit_second() -> None:
        second_started.set()
        try:
            outcomes.append(domain.initial_claim_port.commit_initial_claim(second))
        except BaseException as exc:
            errors.append(exc)

    a, b = Thread(target=commit_first), Thread(target=commit_second)
    a.start()
    _assert(reached.wait(10.0), "first claim interlock")
    b.start()
    _assert(second_started.wait(10.0) and len(outcomes) == 0, "claim lock did not serialize")
    release.set()
    a.join(10.0)
    b.join(10.0)
    _assert(len(outcomes) == 1 and len(errors) == 1 and getattr(errors[0], "failure_code", None) == "stale_source", f"claim race {outcomes}, {errors}")

    reset_reached, reset_release = Event(), Event()
    reset_control = B02._InitialClaimTestControl(
        before_state_swap_reached=reset_reached,
        before_state_swap_release=reset_release,
    )
    reset_domain = _domain(env_ids=(73010,), claim_control=reset_control)
    _reset(reset_domain)
    request = _prepare(reset_domain, (73010,), ((0, -1),))
    sequence: list[str] = []
    reset_started = Event()

    def claim_writer() -> None:
        reset_domain.initial_claim_port.commit_initial_claim(request)
        sequence.append("claim")

    def reset_writer() -> None:
        reset_started.set()
        _reset(reset_domain)
        sequence.append("reset")

    c, d = Thread(target=claim_writer), Thread(target=reset_writer)
    c.start()
    _assert(reset_reached.wait(10.0), "claim/reset interlock")
    d.start()
    _assert(reset_started.wait(10.0) and not sequence, "reset bypassed operation lock")
    reset_release.set()
    c.join(10.0)
    d.join(10.0)
    _assert(sequence == ["claim", "reset"], f"claim/reset order {sequence}")

    final_reached, final_release = Event(), Event()
    final_control = B02._InitialClaimTestControl(
        before_state_swap_reached=final_reached,
        before_state_swap_release=final_release,
    )
    final_domain = _domain(env_ids=(73020,), claim_control=final_control)
    _reset(final_domain)
    final_request = _prepare(final_domain, (73020,), ((0, -1),))
    final_sequence: list[str] = []
    finalize_started = Event()

    def claim_then() -> None:
        final_domain.initial_claim_port.commit_initial_claim(final_request)
        final_sequence.append("claim")

    def finalize_then() -> None:
        finalize_started.set()
        final_domain.environment_port.finalize_physical_transition(_report(final_domain))
        final_sequence.append("finalize")

    e, f = Thread(target=claim_then), Thread(target=finalize_then)
    e.start()
    _assert(final_reached.wait(10.0), "claim/finalize interlock")
    f.start()
    _assert(finalize_started.wait(10.0) and not final_sequence, "finalize bypassed operation lock")
    final_release.set()
    e.join(10.0)
    f.join(10.0)
    _assert(final_sequence == ["claim", "finalize"], f"claim/finalize order {final_sequence}")
    return {"assignment_assignment": "one_success_one_stale", "assignment_reset": sequence, "assignment_finalize": final_sequence, "sleep": False}


def test_b1_t21_p2_producer_migration_and_partial_rows() -> dict[str, Any]:
    domain = _domain(env_ids=(73100, 73101, 73102), num_robots=2, num_tasks=2)
    pre = domain.current_read_port.read_current()
    _assert(all(p.kind is ProvenanceKind.PREBOOTSTRAP for p in pre.provenance), "prebootstrap P2")
    reset = _reset(domain)
    _assert(all(p.kind is ProvenanceKind.CANONICAL_EPISODE_RESET for p in reset.provenance), "reset P2")
    _transition(domain)
    lifecycle = domain.current_read_port.read_current()
    _assert(all(p.kind is ProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION for p in lifecycle.provenance), "lifecycle P2")
    row1_lifecycle = lifecycle.provenance[1]
    row2_lifecycle = lifecycle.provenance[2]
    partial_reset = _reset(domain, (73100,))
    _assert(partial_reset.provenance[0].kind is ProvenanceKind.CANONICAL_EPISODE_RESET, "partial reset selected")
    _assert(partial_reset.provenance[1] is row1_lifecycle and partial_reset.provenance[2] is row2_lifecycle, "partial reset unselected")
    row0_reset = partial_reset.provenance[0]
    _claim(domain, (73101,), ((0, -1),))
    assignment = domain.current_read_port.read_current()
    _assert(assignment.provenance[0] is row0_reset, "partial claim reset row")
    _assert(assignment.provenance[1].kind is ProvenanceKind.ASSIGNMENT_COMMIT, "assignment P2")
    _assert(assignment.provenance[2] is row2_lifecycle, "partial claim lifecycle row")
    _assert(type(assignment) is CLAIM._EventRuntimeCurrentPublication, "current authority type")
    return {"producers": [kind.name for kind in ProvenanceKind], "mixed_rows": ["reset", "assignment", "lifecycle"], "second_pointer": False}


def test_b1_t22_assignment_then_lifecycle_transition() -> dict[str, Any]:
    domain = _domain(env_ids=(73200,), num_robots=2, num_tasks=2)
    _reset(domain)
    artifact = _claim(domain, (73200,), ((0, -1),))
    assignment_current = domain.current_read_port.read_current()
    candidate = torch.zeros((1, 2, 2), dtype=torch.bool)
    candidate[0, 0, 0] = True
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, candidate=candidate)
    )
    current = domain.current_read_port.read_current()
    _assert(bool(outcome.result.completed_tasks[0, 0].item()), "new owner completion missing")
    _assert(int(outcome.result.updated_ownership[0, 0].item()) == -1, "completion did not release")
    _assert(current.provenance[0].kind is ProvenanceKind.FINALIZED_LIFECYCLE_TRANSITION, "lifecycle did not replace provenance")
    _assert(assignment_current.provenance[0].assignment_artifact is artifact, "assignment history lost")
    return {"owner_qualified_completion": 0, "lifecycle_replaced_current": True, "artifact_historical": True}


def test_b1_t23_assignment_then_reset() -> dict[str, Any]:
    domain = _domain(env_ids=(73300, 73301), num_robots=2, num_tasks=2)
    _reset(domain)
    artifact = _claim(domain, (73300,), ((0, -1),))
    assigned = domain.current_read_port.read_current()
    old_transition = assigned.transition_generation.clone()
    reset = _reset(domain, (73300,))
    _assert(reset.provenance[0].kind is ProvenanceKind.CANONICAL_EPISODE_RESET, "reset provenance")
    _assert(reset.provenance[1] is assigned.provenance[1], "unselected provenance")
    _assert(torch.equal(reset.transition_generation, old_transition), "reset changed transition")
    _assert(assigned.provenance[0].assignment_artifact is artifact, "historical artifact changed")
    return {"selected_reset": True, "unselected_exact": True, "transition_unchanged": True, "artifact_historical": True}


TESTS = (
    ("B1-T1_canonical_reset_source_success", test_b1_t1_canonical_reset_source_success),
    ("B1-T2_lifecycle_transition_source_success", test_b1_t2_lifecycle_transition_source_success),
    ("B1-T3_post_assignment_second_claim", test_b1_t3_post_assignment_second_claim),
    ("B1-T4_c2_multi_robot_batch", test_b1_t4_c2_multi_robot_batch),
    ("B1-T5_nonassignable_robot_rejection", test_b1_t5_nonassignable_robot_rejection),
    ("B1-T6_illegal_task_rejection", test_b1_t6_illegal_task_rejection),
    ("B1-T7_failed_pair_rejection", test_b1_t7_failed_pair_rejection),
    ("B1-T8_structural_conflict_rejection", test_b1_t8_structural_conflict_rejection),
    ("B1-T9_g2_terminal_row_block", test_b1_t9_g2_terminal_row_block),
    ("B1-T10_stale_source_rejection", test_b1_t10_stale_source_rejection),
    ("B1-T11_request_effective_no_alias", test_b1_t11_request_effective_no_alias),
    ("B1-T12_assignment_owned_only_fields", test_b1_t12_assignment_owned_only_fields),
    ("B1-T13_historical_result_immutable", test_b1_t13_historical_result_immutable),
    ("B1-T14_reader_atomicity", test_b1_t14_reader_atomicity),
    ("B1-T15_post_swap_failure_poison", test_b1_t15_post_swap_failure_poison),
    ("B1-T16_duplicate_consume_replay", test_b1_t16_duplicate_consume_replay),
    ("B1-T17_default_off_no_production_wiring", test_b1_t17_default_off_no_production_wiring),
    ("B1-T18_frozen_contract_and_side_effect_audit", test_b1_t18_frozen_contract_and_side_effect_audit),
    ("B1-T19_noop_and_mixed_batch_atomicity", test_b1_t19_noop_and_mixed_batch_atomicity),
    ("B1-T20_concurrency_and_partial_provenance", test_b1_t20_concurrency_and_partial_provenance),
    ("B1-T21_p2_producer_migration", test_b1_t21_p2_producer_migration_and_partial_rows),
    ("B1-T22_assignment_then_lifecycle", test_b1_t22_assignment_then_lifecycle_transition),
    ("B1-T23_assignment_then_reset", test_b1_t23_assignment_then_reset),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    for name, test in TESTS:
        try:
            evidence = test()
            results.append({"name": name, "status": "passed", "evidence": evidence})
        except BaseException as exc:
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
    passed = sum(result["status"] == "passed" for result in results)
    payload = {
        "status": "passed" if passed == len(results) else "failed",
        "num_tests": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "tests": results,
        "evidence": {
            "groups": "B1-T1..B1-T23",
            "publication": "one P2 current authority",
            "claim": "pure dormant default-off",
            "synchronization": "threading.Event",
        },
        "runtime_boundary": {
            "production_assignment_wiring": "absent",
            "inter_step_claim_window": "deferred",
            "isaac_applauncher": "not_imported",
            "training_playback_evaluation": "not_run",
        },
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Phase B1 pure initial-claim: {passed}/{len(results)} passed")
        for result in results:
            print(f"[{result['status']}] {result['name']}")
            if result["status"] == "failed":
                print(f"  {result['error_type']}: {result['error']}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
