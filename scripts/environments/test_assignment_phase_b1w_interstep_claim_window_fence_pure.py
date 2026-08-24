"""Pure B1W inter-step claim-window fence and dormant W2 regressions.

The runner loads only canonical namespace modules.  It imports no Isaac,
AppLauncher, Omni, PXr, HARL, task discovery, training, playback, or evaluation
entrypoint.
"""

from __future__ import annotations

import argparse
import ast
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
FENCE_PATH = SCAN_SOURCE / "assignment_interstep_claim_window_runtime.py"
DOMAIN_PATH = SCAN_SOURCE / "assignment_event_profile_runtime_domain.py"
ENV_PATH = SCAN_SOURCE / "scan_mobile_manipulator_env.py"
WRAPPER_PATH = SCAN_SOURCE / "assignment_harl_wrapper.py"

PROFILE_MODULE = f"{PREFIX}.assignment_profile_contract"
TRANSITION_MODULE = f"{PREFIX}.assignment_lifecycle_transition_contract"
EVENT_MODULE = f"{PREFIX}.assignment_event_contract"
B01_MODULE = f"{PREFIX}.assignment_lifecycle_authority_runtime"
CLAIM_MODULE = f"{PREFIX}.assignment_initial_claim_runtime"
B02_MODULE = f"{PREFIX}.assignment_lifecycle_transaction_runtime"
FENCE_MODULE = f"{PREFIX}.assignment_interstep_claim_window_runtime"
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


def _logging_state() -> tuple[object, ...]:
    named = tuple(
        sorted(
            (
                name,
                logger.level,
                tuple(id(handler) for handler in logger.handlers),
                logger.disabled,
                logger.propagate,
            )
            for name, logger in logging.root.manager.loggerDict.items()
            if isinstance(logger, logging.Logger)
        )
    )
    return (
        logging.root.level,
        tuple(id(handler) for handler in logging.root.handlers),
        logging.root.disabled,
        named,
    )


_IMPORT_RANDOM = random.getstate()
_IMPORT_TORCH_RANDOM = torch.random.get_rng_state().clone()
_IMPORT_CWD = Path.cwd()
_IMPORT_SYS_PATH = tuple(sys.path)
_IMPORT_ENV = dict(os.environ)
_IMPORT_LOGGING = _logging_state()
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
FENCE = _load(FENCE_MODULE, FENCE_PATH)
DOMAIN = _load(DOMAIN_MODULE, DOMAIN_PATH)
_PROFILE_REGISTRY = PROFILE.get_assignment_profile_registry()
_PROFILE_REGISTRY_REPR = repr(_PROFILE_REGISTRY)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Phase = FENCE._ClaimWindowFencePhase


def _i(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=DEVICE)


def _b(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.bool, device=DEVICE)


def _profile() -> Any:
    return PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )


def _domain(
    *,
    env_ids: tuple[int, ...] = (81000,),
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


def _reset_args(domain: Any, selected: tuple[int, ...]) -> dict[str, torch.Tensor]:
    identity = domain.identity
    rows = len(selected)
    return {
        "selected_env_ids": _i(selected),
        "initial_task_state": torch.full(
            (rows, identity.num_tasks), int(TaskState.AVAILABLE), dtype=torch.int64
        ),
        "initial_robot_state": torch.full(
            (rows, identity.num_robots), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64
        ),
        "initial_ownership": torch.full((rows, identity.num_tasks), -1, dtype=torch.int64),
    }


def _rebuild(domain: Any, selected: tuple[int, ...] | None = None) -> Any:
    if selected is None:
        selected = tuple(int(value) for value in domain.identity.env_ids.tolist())
    with domain.environment_port.episode_rebuild(**_reset_args(domain, selected)) as rebuild:
        return rebuild.commit_physical_reset_complete()


def _admitted_reset(domain: Any, selected: tuple[int, ...] | None = None) -> tuple[Any, Any, Any]:
    admission = domain.standalone_reset_admission_port.begin_full_reset_admission()
    domain.environment_admission_validation_port.validate_reset_entry(admission)
    publication = _rebuild(domain, selected)
    window = domain.standalone_reset_admission_port.commit_successful_return(admission)
    return publication, window, admission


def _report(domain: Any, *, timeout: torch.Tensor | None = None) -> Any:
    identity = domain.identity
    false_env = torch.zeros(identity.num_envs, dtype=torch.bool)
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=torch.zeros(
            (identity.num_envs, identity.num_tasks), dtype=torch.bool
        ),
        raw_new_candidate=torch.zeros(
            (identity.num_envs, identity.num_robots, identity.num_tasks), dtype=torch.bool
        ),
        physical_truncated=false_env if timeout is None else timeout,
        time_limit_reached=false_env if timeout is None else timeout,
    )


def _prepare(domain: Any, selected: tuple[int, ...], rows: Any) -> Any:
    return domain.production_claim_port.prepare_production_initial_claim(
        selected_env_ids=_i(selected),
        requested_task_by_robot=_i(rows),
    )


def _claim(domain: Any, selected: tuple[int, ...], rows: Any) -> Any:
    return domain.production_claim_port.commit_production_initial_claim(
        _prepare(domain, selected, rows)
    )


def _expect(
    operation: Callable[[], Any],
    *,
    code: str | None = None,
    exception: type[BaseException] | tuple[type[BaseException], ...] = Exception,
) -> BaseException:
    try:
        operation()
    except exception as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError("expected typed failure")


def _semantic_signature(publication: Any) -> tuple[Any, ...]:
    view = publication.lifecycle_view
    state = view.lifecycle_state
    return (
        id(publication),
        id(publication.publication_identity),
        state.store_version,
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


def _same_semantics(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool:
    return (
        left[:3] == right[:3]
        and all(torch.equal(a, b) for a, b in zip(left[3:11], right[3:11], strict=True))
        and left[11] is right[11]
    )


def _complete_empty_step(domain: Any) -> tuple[Any, Any]:
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry(admission)
    domain.environment_admission_validation_port.validate_physical_finalization(admission)
    window = domain.physical_step_admission_port.commit_successful_return(admission)
    return admission, window


def _terminal_open_window(
    domain: Any,
    *,
    terminal_mask: tuple[bool, ...],
) -> tuple[Any, Any, Any]:
    _admitted_reset(domain)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry(admission)
    domain.environment_admission_validation_port.validate_physical_finalization(admission)
    outcome = domain.environment_port.finalize_physical_transition(
        _report(domain, timeout=_b(terminal_mask))
    )
    selected = tuple(
        int(env_id)
        for env_id, terminal in zip(domain.identity.env_ids.tolist(), terminal_mask, strict=True)
        if terminal
    )
    if selected:
        domain.environment_admission_validation_port.validate_reset_entry_for_active_call()
        _rebuild(domain, selected)
    window = domain.physical_step_admission_port.commit_successful_return(admission)
    return outcome, window, admission


def test_w_t1_prebootstrap_closed() -> dict[str, Any]:
    domain = _domain(env_ids=(81100,))
    view = domain.interstep_fence_read_port.read()
    _assert(view.phase is Phase.PREBOOTSTRAP_CLOSED and view.window is None, "prebootstrap fence")
    _expect(
        lambda: _prepare(domain, (81100,), ((0, -1),)),
        code="claim_window_not_open",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _expect(
        domain.physical_step_admission_port.begin_physical_step_admission,
        code="physical_step_admission_required",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    reset = domain.standalone_reset_admission_port.begin_full_reset_admission()
    _assert(domain.interstep_fence_read_port.read().active_reset is reset, "initial reset not admitted")
    return {"phase": "PREBOOTSTRAP_CLOSED", "only_reset": True}


def test_w_t2_first_reset_opens_first_window() -> dict[str, Any]:
    domain = _domain(env_ids=(81200,))
    admission = domain.standalone_reset_admission_port.begin_full_reset_admission()
    _assert(domain.interstep_fence_read_port.read().phase is Phase.RESET_IN_FLIGHT, "reset phase")
    domain.environment_admission_validation_port.validate_reset_entry(admission)
    publication = _rebuild(domain)
    mid = domain.interstep_fence_read_port.read()
    _assert(mid.phase is Phase.RESET_IN_FLIGHT and mid.window is None, "I1 opened early")
    window = domain.standalone_reset_admission_port.commit_successful_return(admission)
    final = domain.interstep_fence_read_port.read()
    _assert(final.phase is Phase.OPEN and final.window is window and window.serial == 0, "first window")
    _assert(publication.episode_generation.tolist() == [0], "I1 semantics")
    return {"window": window.serial, "open_after_return": True}


def test_w_t3_multiple_claims_same_window() -> dict[str, Any]:
    domain = _domain(env_ids=(81300,), num_robots=2, num_tasks=3)
    reset, window, _ = _admitted_reset(domain)
    first = _claim(domain, (81300,), ((0, -1),))
    after_first = domain.current_read_port.read_current()
    _assert(domain.interstep_fence_read_port.read().window is window, "claim replaced W")
    second = _claim(domain, (81300,), ((-1, 1),))
    after_second = domain.current_read_port.read_current()
    _assert(domain.interstep_fence_read_port.read().window is window, "second claim replaced W")
    _assert(after_first.store_version == reset.store_version + 1, "first version")
    _assert(after_second.store_version == reset.store_version + 2, "second version")
    return {"window": window.serial, "claim_tokens": [first.token, second.token]}


def test_w_t4_step_close_atomic() -> dict[str, Any]:
    domain = _domain(env_ids=(81400,))
    publication, window, _ = _admitted_reset(domain)
    before = _semantic_signature(publication)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    view = domain.interstep_fence_read_port.read()
    after = _semantic_signature(domain.current_read_port.read_current())
    _assert(view.phase is Phase.STEP_IN_FLIGHT and view.active_step is admission, "step phase")
    _assert(admission.source_window is window, "source window")
    _assert(admission.admitted_publication is publication, "admitted P2")
    _assert(_same_semantics(before, after), "step close changed semantics")
    return {"window": window.serial, "admission": admission.identity.serial, "atomic": True}


def test_w_t5_claim_after_close() -> dict[str, Any]:
    domain = _domain(env_ids=(81500,))
    _admitted_reset(domain)
    envelope = _prepare(domain, (81500,), ((0, -1),))
    before = domain.current_read_port.read_current()
    domain.physical_step_admission_port.begin_physical_step_admission()
    _expect(
        lambda: _prepare(domain, (81500,), ((0, -1),)),
        code="runtime_step_in_flight",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="stale_claim_window",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _assert(envelope.request.token in domain._coordinator._active_claim_contexts, "request consumed")
    _assert(domain.current_read_port.read_current() is before, "claim after close mutated")
    return {"prepare": "runtime_step_in_flight", "commit": "stale_claim_window"}


def test_w_t6_w1_envelope_invalid_in_w2() -> dict[str, Any]:
    domain = _domain(env_ids=(81600,))
    publication, w1, _ = _admitted_reset(domain)
    envelope = _prepare(domain, (81600,), ((0, -1),))
    _, w2 = _complete_empty_step(domain)
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="stale_claim_window",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _assert(w2 is not w1 and domain.current_read_port.read_current() is publication, "W2/P2")
    _assert(envelope.request.token in domain._coordinator._active_claim_contexts, "old request consumed")
    return {"w1": w1.serial, "w2": w2.serial, "rebind": False}


def test_w_t7_claim_vs_step_race() -> dict[str, Any]:
    reached, release = Event(), Event()
    control = B02._InitialClaimTestControl(
        before_state_swap_reached=reached,
        before_state_swap_release=release,
    )
    domain = _domain(env_ids=(81700,), claim_control=control)
    _admitted_reset(domain)
    envelope = _prepare(domain, (81700,), ((0, -1),))
    order: list[str] = []
    errors: list[BaseException] = []
    step_started = Event()
    outputs: dict[str, Any] = {}

    def claim_first() -> None:
        try:
            outputs["artifact"] = domain.production_claim_port.commit_production_initial_claim(envelope)
            order.append("claim")
        except BaseException as exc:
            errors.append(exc)

    def step_second() -> None:
        step_started.set()
        try:
            outputs["admission"] = domain.physical_step_admission_port.begin_physical_step_admission()
            order.append("step")
        except BaseException as exc:
            errors.append(exc)

    a, b = Thread(target=claim_first), Thread(target=step_second)
    a.start()
    _assert(reached.wait(10.0), "claim interlock")
    b.start()
    _assert(step_started.wait(10.0) and not order, "step bypassed claim lock")
    release.set()
    a.join(10.0)
    b.join(10.0)
    _assert(not errors and order == ["claim", "step"], f"claim-first race {errors} {order}")
    _assert(outputs["admission"].admitted_store_version == outputs["artifact"].committed_store_version, "Ak baseline")

    other = _domain(env_ids=(81710,))
    _admitted_reset(other)
    old = _prepare(other, (81710,), ((0, -1),))
    other.physical_step_admission_port.begin_physical_step_admission()
    failure: list[BaseException] = []

    def claim_after_step() -> None:
        try:
            other.production_claim_port.commit_production_initial_claim(old)
        except BaseException as exc:
            failure.append(exc)

    thread = Thread(target=claim_after_step)
    thread.start()
    thread.join(10.0)
    _assert(len(failure) == 1 and getattr(failure[0], "failure_code", None) == "stale_claim_window", "step-first race")
    return {"claim_first": order, "step_first": "stale_claim_window", "sleep": False}


def test_w_t8_success_opens_one_window() -> dict[str, Any]:
    domain = _domain(env_ids=(81800,))
    _, w1, _ = _admitted_reset(domain)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry(admission)
    domain.environment_admission_validation_port.validate_physical_finalization(admission)
    w2 = domain.physical_step_admission_port.commit_successful_return(admission)
    _expect(
        lambda: domain.physical_step_admission_port.commit_successful_return(admission),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    view = domain.interstep_fence_read_port.read()
    _assert(view.window is w2 and view.next_window_serial == 2, "duplicate allocated W3")
    return {"w1": w1.serial, "w2": w2.serial, "duplicate": "rejected"}


def test_w_t9_autoreset_no_early_open() -> dict[str, Any]:
    domain = _domain(env_ids=(81900,))
    _admitted_reset(domain)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry(admission)
    domain.environment_admission_validation_port.validate_physical_finalization(admission)
    outcome = domain.environment_port.finalize_physical_transition(_report(domain, timeout=_b((True,))))
    key = outcome.terminal_keys[0]
    domain.environment_admission_validation_port.validate_reset_entry_for_active_call()
    _rebuild(domain)
    mid = domain.interstep_fence_read_port.read()
    _assert(mid.phase is Phase.STEP_IN_FLIGHT and mid.window is None, "autoreset opened early")
    window = domain.physical_step_admission_port.commit_successful_return(admission)
    _assert(domain.interstep_fence_read_port.read().window is window and key is not None, "outer return")
    return {"terminal": True, "autoreset_open": False, "window": window.serial}


def test_w_t10_standalone_reset() -> dict[str, Any]:
    domain = _domain(env_ids=(82000,))
    _, w1, _ = _admitted_reset(domain)
    _claim(domain, (82000,), ((0, -1),))
    admission = domain.standalone_reset_admission_port.begin_full_reset_admission()
    _assert(admission.source_window is w1, "reset source window")
    domain.environment_admission_validation_port.validate_reset_entry(admission)
    publication = _rebuild(domain)
    _assert(domain.interstep_fence_read_port.read().phase is Phase.RESET_IN_FLIGHT, "I1 opened reset")
    w2 = domain.standalone_reset_admission_port.commit_successful_return(admission)
    _assert(publication.provenance[0].kind is CLAIM._CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET, "reset provenance")
    return {"w1": w1.serial, "w2": w2.serial, "reset_provenance": True}


def test_w_t11_reset_vs_claim_race() -> dict[str, Any]:
    reached, release = Event(), Event()
    control = B02._InitialClaimTestControl(
        before_state_swap_reached=reached,
        before_state_swap_release=release,
    )
    domain = _domain(env_ids=(82100,), claim_control=control)
    _admitted_reset(domain)
    envelope = _prepare(domain, (82100,), ((0, -1),))
    order: list[str] = []

    def claim_first() -> None:
        domain.production_claim_port.commit_production_initial_claim(envelope)
        order.append("claim")

    def reset_second() -> None:
        domain.standalone_reset_admission_port.begin_full_reset_admission()
        order.append("reset")

    a, b = Thread(target=claim_first), Thread(target=reset_second)
    a.start()
    _assert(reached.wait(10.0), "reset race claim interlock")
    b.start()
    _assert(not order, "reset bypassed claim lock")
    release.set()
    a.join(10.0)
    b.join(10.0)
    _assert(order == ["claim", "reset"], f"claim/reset order {order}")

    other = _domain(env_ids=(82110,))
    _admitted_reset(other)
    old = _prepare(other, (82110,), ((0, -1),))
    other.standalone_reset_admission_port.begin_full_reset_admission()
    _expect(
        lambda: other.production_claim_port.commit_production_initial_claim(old),
        code="stale_claim_window",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _expect(
        lambda: _prepare(other, (82110,), ((0, -1),)),
        code="claim_window_not_open",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    return {"claim_first": order, "reset_first": "claim_rejected", "sleep": False}


def test_w_t12_g2_selected_terminal_row() -> dict[str, Any]:
    domain = _domain(env_ids=(82200, 82201), num_robots=2, num_tasks=2)
    outcome, window, _ = _terminal_open_window(domain, terminal_mask=(True, False))
    envelope = _prepare(domain, (82200,), ((0, -1),))
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="terminal_slot_occupied",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain.interstep_fence_read_port.read().window is window, "G2 changed W")
    _assert(envelope.request.token in domain._coordinator._active_claim_contexts, "G2 consumed")
    return {"terminal_key": outcome.terminal_keys[0].env_id, "window": window.serial}


def test_w_t13_unselected_terminal_row() -> dict[str, Any]:
    domain = _domain(env_ids=(82300, 82301), num_robots=2, num_tasks=2)
    _, window, _ = _terminal_open_window(domain, terminal_mask=(True, False))
    artifact = _claim(domain, (82301,), ((0, -1),))
    _assert(domain.interstep_fence_read_port.read().window is window, "unselected G2 changed W")
    return {"claim_env": 82301, "token": artifact.token, "window": window.serial}


def test_w_t14_r3_rejection_keeps_window() -> dict[str, Any]:
    domain = _domain(env_ids=(82400, 82401))
    _, window, _ = _terminal_open_window(domain, terminal_mask=(True, False))
    before = domain.interstep_fence_read_port.read()
    publication = domain.current_read_port.read_current()
    _expect(
        domain.physical_step_admission_port.begin_physical_step_admission,
        code="terminal_ack_required",
        exception=B02.LifecycleCoordinatorRuntimeError,
    )
    after = domain.interstep_fence_read_port.read()
    _assert(after.phase is Phase.OPEN and after.window is window, "R3 closed W")
    _assert(after.next_admission_serial == before.next_admission_serial, "R3 allocated admission")
    _assert(after.next_window_serial == before.next_window_serial, "R3 allocated window")
    _assert(domain.current_read_port.read_current() is publication, "R3 published")
    return {"window_exact": True, "allocation": False, "poison": False}


def test_w_t15_ack_no_window_change() -> dict[str, Any]:
    domain = _domain(env_ids=(82500, 82501))
    outcome, window, _ = _terminal_open_window(domain, terminal_mask=(True, False))
    key = outcome.terminal_keys[0]
    before = domain.current_read_port.read_current()
    before_view = domain.interstep_fence_read_port.read()
    domain.terminal_consumer_port.acknowledge_terminal(key)
    after_view = domain.interstep_fence_read_port.read()
    _assert(after_view.window is window and before_view.window is window, "ack window")
    _assert(after_view.next_window_serial == before_view.next_window_serial, "ack serial")
    _assert(domain.current_read_port.read_current() is before, "ack P2")
    return {"window": window.serial, "P2_exact": True, "Store_exact": True}


def test_w_t16_ack_retry_same_window() -> dict[str, Any]:
    domain = _domain(env_ids=(82600, 82601), num_robots=2, num_tasks=2)
    outcome, window, _ = _terminal_open_window(domain, terminal_mask=(True, False))
    envelope = _prepare(domain, (82600,), ((0, -1),))
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="terminal_slot_occupied",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    source = domain.current_read_port.read_current()
    domain.terminal_consumer_port.acknowledge_terminal(outcome.terminal_keys[0])
    artifact = domain.production_claim_port.commit_production_initial_claim(envelope)
    _assert(artifact.source_publication is source and domain.interstep_fence_read_port.read().window is window, "ack retry")
    return {"retry": True, "same_window": window.serial, "token": artifact.token}


def test_w_t17_step_failure_no_reopen() -> dict[str, Any]:
    domain = _domain(env_ids=(82700,))
    _admitted_reset(domain)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.physical_step_admission_port.report_abnormal_failure(admission, ValueError("step failed"))
    view = domain.interstep_fence_read_port.read()
    _assert(domain._coordinator.poisoned and view.phase is Phase.FAULTED, "step poison")
    _assert(view.window is None and view.next_window_serial == 1, "step reopened")
    return {"poison": True, "derived_faulted": True, "reopen": False}


def test_w_t18_reset_failure_no_reopen() -> dict[str, Any]:
    domain = _domain(env_ids=(82800,))
    admission = domain.standalone_reset_admission_port.begin_full_reset_admission()
    domain.standalone_reset_admission_port.report_abnormal_failure(admission, ValueError("reset failed"))
    view = domain.interstep_fence_read_port.read()
    _assert(domain._coordinator.poisoned and view.phase is Phase.FAULTED, "reset poison")
    _assert(view.window is None and view.next_window_serial == 0, "reset reopened")
    return {"poison": True, "derived_faulted": True, "reopen": False}


def test_w_t19_admission_identity_exactness() -> dict[str, Any]:
    domain = _domain(env_ids=(82900,))
    foreign_domain = _domain(env_ids=(82901,))
    _admitted_reset(domain)
    _admitted_reset(foreign_domain)
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    foreign = foreign_domain.physical_step_admission_port.begin_physical_step_admission()
    _expect(
        lambda: domain.environment_admission_validation_port.validate_physical_step_entry(foreign),
        code="physical_step_admission_required",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    errors: list[BaseException] = []

    def foreign_thread_entry() -> None:
        try:
            domain.environment_admission_validation_port.validate_physical_step_entry(admission)
        except BaseException as exc:
            errors.append(exc)

    thread = Thread(target=foreign_thread_entry)
    thread.start()
    thread.join(10.0)
    _assert(len(errors) == 1 and getattr(errors[0], "failure_code", None) == "physical_step_admission_required", "thread binding")
    domain.environment_admission_validation_port.validate_physical_step_entry(admission)
    _expect(
        lambda: domain.environment_admission_validation_port.validate_physical_step_entry(admission),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    domain.environment_admission_validation_port.validate_physical_finalization(admission)
    _expect(
        lambda: domain.environment_admission_validation_port.validate_physical_finalization(admission),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    domain.physical_step_admission_port.commit_successful_return(admission)
    _expect(
        lambda: domain.physical_step_admission_port.commit_successful_return(admission),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )

    reset_domain = _domain(env_ids=(82910,))
    reset = reset_domain.standalone_reset_admission_port.begin_full_reset_admission()
    reset_domain.environment_admission_validation_port.validate_reset_entry(reset)
    _expect(
        lambda: reset_domain.environment_admission_validation_port.validate_reset_entry(reset),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _rebuild(reset_domain)
    reset_domain.standalone_reset_admission_port.commit_successful_return(reset)
    _expect(
        lambda: reset_domain.standalone_reset_admission_port.commit_successful_return(reset),
        code="admission_already_consumed",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    return {"foreign": True, "thread_local": True, "single_use": True}


def test_w_t20_fence_semantic_neutrality() -> dict[str, Any]:
    domain = _domain(env_ids=(83000,))
    admission = domain.standalone_reset_admission_port.begin_full_reset_admission()
    domain.environment_admission_validation_port.validate_reset_entry(admission)
    publication = _rebuild(domain)
    before_open = _semantic_signature(publication)
    domain.standalone_reset_admission_port.commit_successful_return(admission)
    after_open = _semantic_signature(domain.current_read_port.read_current())
    step = domain.physical_step_admission_port.begin_physical_step_admission()
    after_close = _semantic_signature(domain.current_read_port.read_current())
    domain.environment_admission_validation_port.validate_physical_step_entry(step)
    domain.environment_admission_validation_port.validate_physical_finalization(step)
    domain.physical_step_admission_port.commit_successful_return(step)
    after_step_open = _semantic_signature(domain.current_read_port.read_current())
    reset = domain.standalone_reset_admission_port.begin_full_reset_admission()
    domain.environment_admission_validation_port.validate_reset_entry(reset)
    after_reset_close = _semantic_signature(domain.current_read_port.read_current())
    domain.standalone_reset_admission_port.commit_successful_return(reset)
    after_reset_open = _semantic_signature(domain.current_read_port.read_current())
    signatures = (after_open, after_close, after_step_open, after_reset_close, after_reset_open)
    _assert(all(_same_semantics(before_open, item) for item in signatures), "fence changed semantic state")
    return {"Store_P2_generations_result": "exact", "transitions": 5}


def test_w_t21_p2_identity_neutrality() -> dict[str, Any]:
    domain = _domain(env_ids=(83100,))
    publication, _, _ = _admitted_reset(domain)
    _complete_empty_step(domain)
    reset = domain.standalone_reset_admission_port.begin_full_reset_admission()
    domain.environment_admission_validation_port.validate_reset_entry(reset)
    domain.standalone_reset_admission_port.commit_successful_return(reset)
    current = domain.current_read_port.read_current()
    _assert(current is publication and current.publication_identity is publication.publication_identity, "fence created P2")
    return {"P2_object_exact": True, "publication_identity_exact": True}


def test_w_t22_capability_isolation() -> dict[str, Any]:
    fence_source = inspect.getsource(FENCE)
    domain_source = inspect.getsource(DOMAIN)
    environment_port_source = inspect.getsource(DOMAIN._EventProfileLifecycleEnvironmentPort)
    validation_source = inspect.getsource(DOMAIN._EventProfileEnvironmentAdmissionValidationPort)
    for forbidden in ("open_window", "close_window", "set_phase", "force_open", "set_window"):
        _assert(forbidden not in domain_source and forbidden not in fence_source, f"raw writer {forbidden}")
    _assert("Lock(" not in fence_source and "RLock" not in fence_source, "independent fence mutex")
    for forbidden in ("begin_physical_step_admission", "begin_full_reset_admission", "prepare_production_initial_claim"):
        _assert(forbidden not in environment_port_source, f"environment port leak: {forbidden}")
    _assert("begin_" not in validation_source and "commit_" not in validation_source, "validation writer leak")
    _assert(FENCE.__all__ == (), "B1W public export")
    _expect(
        lambda: setattr(_admitted_reset(_domain(env_ids=(83110,)))[1], "serial", 99),
        exception=(FrozenInstanceError, AttributeError, TypeError),
    )
    return {"raw_writer": False, "second_mutex": False, "public_export": False}


def test_w_t23_b1_default_off_and_no_wiring() -> dict[str, Any]:
    domain = _domain(env_ids=(83200,))
    publication = _rebuild(domain)
    request = domain.initial_claim_port.prepare_initial_claim(
        selected_env_ids=_i((83200,)),
        requested_task_by_robot=_i(((0, -1),)),
    )
    artifact = domain.initial_claim_port.commit_initial_claim(request)
    _assert(artifact.source_publication is publication, "pure B1 changed")
    env_source = ENV_PATH.read_text(encoding="utf-8")
    wrapper_source = WRAPPER_PATH.read_text(encoding="utf-8")
    wrapper_tree = ast.parse(wrapper_source)
    helpers = [
        node
        for node in wrapper_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_compose_event_assignment_harl_wrapper"
    ]
    _assert(len(helpers) == 1, "I4-1 private wrapper composition seam missing")
    helper_source = ast.get_source_segment(wrapper_source, helpers[0]) or ""
    for symbol in (
        "RuntimeClaimAdmissionEnvelope",
        "production_claim_port",
        "physical_step_admission_port",
        "standalone_reset_admission_port",
    ):
        _assert(symbol not in env_source, f"environment production wiring {symbol}")
        if symbol != "RuntimeClaimAdmissionEnvelope":
            _assert(symbol in helper_source, f"I4-1 composition omitted {symbol}")
    _assert("event_admission_validation_port" in env_source, "B1W-I1 environment validation missing")
    _assert("event_admission_validation_port" not in wrapper_source, "wrapper validation wiring added")
    facade_source = (WRAPPER_PATH.parent / "assignment_event_runtime_facade.py").read_text(encoding="utf-8")
    _assert("commit_deterministic_initial_claim(" not in facade_source, "I4-1 facade gained B1 claim mapping")
    return {
        "pure_B1": True,
        "environment_validation_wiring": True,
        "private_I4_1_composition": True,
        "facade_B1_mapping": False,
    }


def test_w_t24_p2_stale_priority_same_window() -> dict[str, Any]:
    domain = _domain(env_ids=(83300,), num_robots=2, num_tasks=2)
    _admitted_reset(domain)
    first = _prepare(domain, (83300,), ((0, -1),))
    stale = _prepare(domain, (83300,), ((-1, 1),))
    window = domain.interstep_fence_read_port.read().window
    domain.production_claim_port.commit_production_initial_claim(first)
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(stale),
        code="stale_source",
        exception=CLAIM.InitialClaimRuntimeError,
    )
    _assert(domain.interstep_fence_read_port.read().window is window, "window changed")
    return {"failure": "stale_source", "stale_window": False}


def test_w_t25_old_window_priority_without_p2_change() -> dict[str, Any]:
    domain = _domain(env_ids=(83400,))
    publication, _, _ = _admitted_reset(domain)
    envelope = _prepare(domain, (83400,), ((0, -1),))
    _complete_empty_step(domain)
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="stale_claim_window",
        exception=FENCE.InterStepClaimWindowRuntimeError,
    )
    _assert(domain.current_read_port.read_current() is publication, "P2 changed")
    return {"failure": "stale_claim_window", "P2_exact": True}


def test_w_t26_faulted_derived_from_existing_poison() -> dict[str, Any]:
    control = B02._InitialClaimTestControl(fail_after_state_swap=True)
    domain = _domain(env_ids=(83500,), claim_control=control)
    _admitted_reset(domain)
    envelope = _prepare(domain, (83500,), ((0, -1),))
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="fatal_post_claim_swap_failure",
        exception=B02.LifecycleCoordinatorRuntimeError,
    )
    _assert(domain._coordinator.poisoned, "existing coordinator not poisoned")
    view = domain.interstep_fence_read_port.read()
    _assert(view.phase is Phase.FAULTED and view.window is None, "FAULTED not derived")
    _assert("_faulted" not in FENCE._InterStepClaimWindowFence.__slots__, "second fault truth")
    return {"poison_owner": "existing_coordinator", "fence_fault_field": False}


TESTS = (
    ("W-T1_prebootstrap_closed", test_w_t1_prebootstrap_closed),
    ("W-T2_first_reset_opens_window", test_w_t2_first_reset_opens_first_window),
    ("W-T3_multiple_claims_same_window", test_w_t3_multiple_claims_same_window),
    ("W-T4_step_close_atomic", test_w_t4_step_close_atomic),
    ("W-T5_claim_after_close", test_w_t5_claim_after_close),
    ("W-T6_w1_envelope_invalid_w2", test_w_t6_w1_envelope_invalid_in_w2),
    ("W-T7_claim_vs_step_race", test_w_t7_claim_vs_step_race),
    ("W-T8_success_opens_one_window", test_w_t8_success_opens_one_window),
    ("W-T9_autoreset_no_early_open", test_w_t9_autoreset_no_early_open),
    ("W-T10_standalone_reset", test_w_t10_standalone_reset),
    ("W-T11_reset_vs_claim_race", test_w_t11_reset_vs_claim_race),
    ("W-T12_g2_selected_terminal", test_w_t12_g2_selected_terminal_row),
    ("W-T13_unselected_terminal", test_w_t13_unselected_terminal_row),
    ("W-T14_r3_rejection", test_w_t14_r3_rejection_keeps_window),
    ("W-T15_ack_no_window", test_w_t15_ack_no_window_change),
    ("W-T16_ack_retry", test_w_t16_ack_retry_same_window),
    ("W-T17_step_failure", test_w_t17_step_failure_no_reopen),
    ("W-T18_reset_failure", test_w_t18_reset_failure_no_reopen),
    ("W-T19_admission_identity", test_w_t19_admission_identity_exactness),
    ("W-T20_semantic_neutrality", test_w_t20_fence_semantic_neutrality),
    ("W-T21_p2_identity_neutrality", test_w_t21_p2_identity_neutrality),
    ("W-T22_capability_isolation", test_w_t22_capability_isolation),
    ("W-T23_b1_default_off_no_wiring", test_w_t23_b1_default_off_and_no_wiring),
    ("W-T24_p2_stale_priority", test_w_t24_p2_stale_priority_same_window),
    ("W-T25_old_window_priority", test_w_t25_old_window_priority_without_p2_change),
    ("W-T26_faulted_derived", test_w_t26_faulted_derived_from_existing_poison),
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
    side_effects = {
        "random": random.getstate() == _IMPORT_RANDOM,
        "torch_random": torch.equal(torch.random.get_rng_state(), _IMPORT_TORCH_RANDOM),
        "cwd": Path.cwd() == _IMPORT_CWD,
        "sys_path": tuple(sys.path) == _IMPORT_SYS_PATH,
        "environment": dict(os.environ) == _IMPORT_ENV,
        "logging": _logging_state() == _IMPORT_LOGGING,
        "filesystem": _inventory() == _IMPORT_INVENTORY,
        "registry_identity": PROFILE.get_assignment_profile_registry() is _PROFILE_REGISTRY,
        "registry_content": repr(PROFILE.get_assignment_profile_registry()) == _PROFILE_REGISTRY_REPR,
    }
    if not all(side_effects.values()):
        results.append({"name": "global_side_effect_audit", "status": "failed", "evidence": side_effects})
    payload = {
        "status": "passed" if passed == len(TESTS) and all(side_effects.values()) else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": len(TESTS) - passed,
        "tests": results,
        "side_effects": side_effects,
        "evidence": {
            "groups": "W-T1..W-T26",
            "fence": "global vector-domain S4/O1/W2/F1 pure default-off",
            "synchronization": "threading.Event",
            "assignment_tick": "not_used",
        },
        "runtime_boundary": {
            "production_environment_wiring": "absent",
            "wrapper_harl_wiring": "private_i4_1_facade_composition_only",
            "isaac_applauncher": "not_imported",
            "training_playback_evaluation": "not_run",
        },
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Phase B1W pure claim-window fence: {passed}/{len(TESTS)} passed")
        for result in results:
            print(f"[{result['status']}] {result['name']}")
            if result["status"] == "failed":
                print(f"  {result.get('error_type', 'AssertionError')}: {result.get('error', result.get('evidence'))}")
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
