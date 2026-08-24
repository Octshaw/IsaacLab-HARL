"""Pure B0-1B regressions for the default-off generation clock.

The suite loads only the canonical profile, transition-contract, and pure
runtime sources through namespace-only package placeholders.  It does not run
task discovery, AppLauncher, Isaac, a wrapper, a resolver, HARL, training,
playback, diagnosis, or evaluation.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import FrozenInstanceError, replace
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import ModuleType
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_TASK_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PROFILE_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
RUNTIME_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_authority_runtime.py"

PROFILE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
)
TRANSITION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_authority_runtime"
)

DEVICE = torch.device("cpu")
INT64_MAX = torch.iinfo(torch.int64).max


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
            Path(str(getattr(existing, "__file__", ""))).resolve()
            == path.resolve(),
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
RUNTIME = _load_canonical(RUNTIME_MODULE, RUNTIME_PATH)


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


def _ids(*values: int) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=DEVICE)


def _clock(*env_ids: int) -> Any:
    event, _ = _profiles()
    return RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(*env_ids))


def _snapshot(clock: Any, *env_ids: int) -> tuple[Any, ...]:
    return clock.snapshot(_ids(*env_ids))


def _snapshot_mapping(clock: Any, *env_ids: int) -> dict[int, tuple[int, int, Any]]:
    return {
        row.env_id: (
            row.episode_generation,
            row.transition_generation,
            row.outstanding_transition_generation,
        )
        for row in _snapshot(clock, *env_ids)
    }


def _expect_error(
    exception_type: type[BaseException],
    operation: Callable[[], Any],
) -> BaseException:
    try:
        operation()
    except exception_type as exc:
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _expect_clock_error(code: str, operation: Callable[[], Any]) -> Any:
    error = _expect_error(RUNTIME.GenerationClockRuntimeError, operation)
    _assert(error.failure_code == code, f"expected {code}, got {error.failure_code}")
    return error


def _set_private_generations(
    clock: Any,
    *,
    env_id: int,
    episode: int | None = None,
    transition: int | None = None,
) -> None:
    """Reach an int64 boundary without adding a public runtime test hook."""

    with clock._lock:
        state = clock._state
        row = clock._row_by_env[env_id]
        episodes = list(state.episode_generation)
        transitions = list(state.transition_generation)
        if episode is not None:
            episodes[row] = episode
        if transition is not None:
            transitions[row] = transition
        clock._state = RUNTIME._GenerationClockState(
            episode_generation=tuple(episodes),
            transition_generation=tuple(transitions),
            outstanding=state.outstanding,
        )


def _facts_input(context: Any, *, invalid_completion_dtype: bool = False) -> Any:
    env_count, robot_count, task_count = 1, 2, 3
    completion_dtype = torch.int64 if invalid_completion_dtype else torch.bool
    return RUNTIME.ExecutionTransitionInput(
        device=DEVICE,
        env_id=_ids(context.env_id),
        episode_generation=_ids(context.episode_generation),
        transition_generation=_ids(context.transition_generation),
        physical_terminated=torch.zeros(env_count, dtype=torch.bool, device=DEVICE),
        physical_truncated=torch.zeros(env_count, dtype=torch.bool, device=DEVICE),
        time_limit_reached=torch.zeros(env_count, dtype=torch.bool, device=DEVICE),
        bad_transition=torch.zeros(env_count, dtype=torch.bool, device=DEVICE),
        completion_signals=torch.zeros(
            (env_count, robot_count, task_count),
            dtype=completion_dtype,
            device=DEVICE,
        ),
        terminal_pair_failure_signals=torch.zeros(
            (env_count, robot_count, task_count), dtype=torch.bool, device=DEVICE
        ),
        forced_release_signals=torch.zeros(
            (env_count, robot_count, task_count), dtype=torch.bool, device=DEVICE
        ),
        robot_unavailable_signals=torch.zeros(
            (env_count, robot_count), dtype=torch.bool, device=DEVICE
        ),
        robot_recovered_signals=torch.zeros(
            (env_count, robot_count), dtype=torch.bool, device=DEVICE
        ),
        coverage_before_transition=torch.zeros(
            (env_count, task_count), dtype=torch.bool, device=DEVICE
        ),
        task_state_before_transition=torch.zeros(
            (env_count, task_count), dtype=torch.int64, device=DEVICE
        ),
        robot_state_before_transition=torch.ones(
            (env_count, robot_count), dtype=torch.int64, device=DEVICE
        ),
        ownership_before_transition=torch.full(
            (env_count, task_count), -1, dtype=torch.int64, device=DEVICE
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
    return (
        root.level,
        tuple(id(handler) for handler in root.handlers),
        root.disabled,
        named,
    )


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


def test_g1_initial_state() -> dict[str, Any]:
    event, _ = _profiles()
    _expect_clock_error(
        "env_id_type",
        lambda: RUNTIME.LifecycleGenerationClock(event, env_ids=[1000]),
    )
    _expect_clock_error(
        "env_id_dtype",
        lambda: RUNTIME.LifecycleGenerationClock(
            event,
            env_ids=torch.tensor([1000.0], dtype=torch.float32),
        ),
    )
    _expect_clock_error(
        "env_id_shape",
        lambda: RUNTIME.LifecycleGenerationClock(
            event,
            env_ids=torch.tensor([[1000]], dtype=torch.int64),
        ),
    )
    _expect_clock_error(
        "env_id_unique",
        lambda: RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(1000, 1000)),
    )
    _expect_clock_error(
        "env_id_materialization",
        lambda: RUNTIME.LifecycleGenerationClock(
            event,
            env_ids=torch.empty((1,), dtype=torch.int64, device="meta"),
        ),
    )
    clock = RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(1000, 1001, 1002))
    _expect_clock_error("unknown_env", lambda: clock.snapshot(_ids(9999)))
    _expect_clock_error("env_id_unique", lambda: clock.snapshot(_ids(1000, 1000)))
    rows = _snapshot(clock, 1000, 1001, 1002)
    _assert(
        all(row.episode_generation == -1 for row in rows),
        "episode generation did not start at -1",
    )
    _assert(
        all(row.transition_generation == -1 for row in rows),
        "transition generation did not start at -1",
    )
    _assert(
        all(row.outstanding_transition_generation is None for row in rows),
        "initial clock has an outstanding candidate",
    )
    return {
        "env_ids": [row.env_id for row in rows],
        "episode_generation": -1,
        "transition_generation": -1,
        "outstanding": False,
        "env_id_gates": [
            "type",
            "dtype",
            "shape",
            "unique",
            "materialization",
            "known-domain",
        ],
    }


def test_g2_episode_advance_selected_atomic_overflow() -> dict[str, Any]:
    clock = _clock(1010, 1011, 1012)
    clock.advance_episode(_ids(1011))
    _assert(
        _snapshot_mapping(clock, 1010, 1011, 1012)
        == {1010: (-1, -1, None), 1011: (0, -1, None), 1012: (-1, -1, None)},
        "first selected-row episode advance was not exact",
    )
    clock.advance_episode(_ids(1011))
    _assert(_snapshot(clock, 1011)[0].episode_generation == 1, "0 -> 1 failed")

    boundary = _clock(1020, 1021)
    boundary.advance_episode(_ids(1020, 1021))
    _set_private_generations(boundary, env_id=1020, episode=INT64_MAX - 1)
    boundary.advance_episode(_ids(1020))
    _assert(
        _snapshot(boundary, 1020)[0].episode_generation == INT64_MAX,
        "max-1 -> max episode advance failed",
    )
    before = _snapshot(boundary, 1020, 1021)
    _expect_clock_error(
        "episode_overflow",
        lambda: boundary.advance_episode(_ids(1021, 1020)),
    )
    _assert(_snapshot(boundary, 1020, 1021) == before, "overflow partially advanced")
    return {
        "first_advance": 0,
        "later_advance": 1,
        "selected_rows_exact": True,
        "int64_overflow_atomic": True,
    }


def test_g3_candidate_generation_and_overflow() -> dict[str, Any]:
    clock = _clock(1100, 1101)
    initial = _snapshot(clock, 1100, 1101)
    _expect_clock_error(
        "episode_not_started",
        lambda: clock.request_transition_candidate(_ids(1100)),
    )
    _assert(_snapshot(clock, 1100, 1101) == initial, "failed request mutated clock")
    clock.advance_episode(_ids(1100, 1101))
    first = clock.request_transition_candidate(_ids(1100))[0]
    pending = _snapshot(clock, 1100)[0]
    _assert(first.transition_generation == 0, "first candidate is not zero")
    _assert(pending.transition_generation == -1, "request committed generation")
    clock.commit_transition(_ids(1100), (first,))
    second = clock.request_transition_candidate(_ids(1100))[0]
    _assert(second.transition_generation == 1, "next candidate is not one")

    boundary = _clock(1110, 1111)
    boundary.advance_episode(_ids(1110, 1111))
    _set_private_generations(boundary, env_id=1110, transition=INT64_MAX - 1)
    maximum = boundary.request_transition_candidate(_ids(1110))[0]
    _assert(maximum.transition_generation == INT64_MAX, "max candidate unavailable")
    boundary.commit_transition(_ids(1110), (maximum,))
    _expect_clock_error(
        "transition_overflow",
        lambda: boundary.request_transition_candidate(_ids(1110)),
    )
    before_free = _snapshot(boundary, 1111)[0]
    _expect_clock_error(
        "transition_overflow",
        lambda: boundary.request_transition_candidate(_ids(1111, 1110)),
    )
    _assert(_snapshot(boundary, 1111)[0] == before_free, "mixed request reserved free row")
    return {
        "first_candidate": first.transition_generation,
        "next_candidate": second.transition_generation,
        "request_does_not_commit": True,
        "pre_episode_rejected": True,
        "int64_overflow_atomic": True,
    }


def test_g4_explicit_multirow_commit() -> dict[str, Any]:
    clock = _clock(1200, 1201)
    selected = _ids(1201, 1200)
    clock.advance_episode(selected)
    contexts = clock.request_transition_candidate(selected)
    committed = clock.commit_transition(selected, contexts)
    _assert(
        [(row.env_id, row.transition_generation) for row in committed]
        == [(1201, 0), (1200, 0)],
        "explicit ordered multirow commit failed",
    )
    _assert(
        all(row.outstanding_transition_generation is None for row in committed),
        "commit did not clear exact active contexts",
    )
    return {
        "commit_order": [1201, 1200],
        "committed_generation": [0, 0],
        "active_contexts_cleared": True,
    }


def test_g5_invalid_commits_fail_closed() -> dict[str, Any]:
    clock = _clock(1300, 1301)
    selected = _ids(1300, 1301)
    clock.advance_episode(selected)
    contexts = clock.request_transition_candidate(selected)
    before = _snapshot(clock, 1300, 1301)
    _expect_clock_error(
        "wrong_env",
        lambda: clock.commit_transition(selected, (contexts[0], contexts[0])),
    )
    _assert(_snapshot(clock, 1300, 1301) == before, "wrong-env batch partially committed")
    clock.commit_transition(selected, contexts)

    committed_zero = _snapshot(clock, 1300, 1301)
    _expect_clock_error(
        "duplicate_commit",
        lambda: clock.commit_transition(_ids(1300), (contexts[0],)),
    )
    _assert(_snapshot(clock, 1300, 1301) == committed_zero, "duplicate mutated clock")

    next_context = clock.request_transition_candidate(_ids(1300))[0]
    clock.commit_transition(_ids(1300), (next_context,))
    after_one = _snapshot(clock, 1300, 1301)
    _expect_clock_error(
        "stale_candidate",
        lambda: clock.commit_transition(_ids(1300), (contexts[0],)),
    )
    future = replace(next_context, transition_generation=3)
    _expect_clock_error(
        "future_candidate",
        lambda: clock.commit_transition(_ids(1300), (future,)),
    )
    _assert(_snapshot(clock, 1300, 1301) == after_one, "stale/future mutated clock")

    clock.advance_episode(_ids(1300))
    episode_one = _snapshot(clock, 1300, 1301)
    _expect_clock_error(
        "wrong_episode",
        lambda: clock.commit_transition(_ids(1300), (next_context,)),
    )
    other_clock = _clock(1300)
    other_clock.advance_episode(_ids(1300))
    foreign = other_clock.request_transition_candidate(_ids(1300))[0]
    _expect_clock_error(
        "wrong_clock",
        lambda: clock.commit_transition(_ids(1300), (foreign,)),
    )
    _assert(_snapshot(clock, 1300, 1301) == episode_one, "context mismatch mutated clock")

    active = clock.request_transition_candidate(_ids(1300))[0]
    copied = replace(active)
    before_copy = _snapshot(clock, 1300, 1301)
    _expect_clock_error(
        "candidate_identity",
        lambda: clock.commit_transition(_ids(1300), (copied,)),
    )
    _assert(_snapshot(clock, 1300, 1301) == before_copy, "copied context mutated clock")
    clock.commit_transition(_ids(1300), (active,))

    atomic = _clock(1310, 1311)
    atomic.advance_episode(_ids(1310, 1311))
    atomic_contexts = atomic.request_transition_candidate(_ids(1310, 1311))
    forged_future = replace(atomic_contexts[1], transition_generation=1)
    atomic_before = _snapshot(atomic, 1310, 1311)
    _expect_clock_error(
        "future_candidate",
        lambda: atomic.commit_transition(
            _ids(1310, 1311),
            (atomic_contexts[0], forged_future),
        ),
    )
    _assert(_snapshot(atomic, 1310, 1311) == atomic_before, "batch partially committed")
    atomic.commit_transition(_ids(1310, 1311), atomic_contexts)
    return {
        "wrong_env": "rejected",
        "wrong_clock": "rejected",
        "wrong_episode": "rejected",
        "duplicate": "rejected",
        "stale": "rejected",
        "future": "rejected",
        "copied_identity": "rejected",
        "full_batch_atomic": True,
    }


def test_g6_one_outstanding_per_env() -> dict[str, Any]:
    clock = _clock(1400, 1401)
    clock.advance_episode(_ids(1400, 1401))
    first = clock.request_transition_candidate(_ids(1400))[0]
    before = _snapshot(clock, 1400, 1401)
    _expect_clock_error(
        "candidate_already_outstanding",
        lambda: clock.request_transition_candidate(_ids(1400)),
    )
    _expect_clock_error(
        "candidate_already_outstanding",
        lambda: clock.request_transition_candidate(_ids(1401, 1400)),
    )
    _assert(_snapshot(clock, 1400, 1401) == before, "mixed request reserved env 1401")
    second = clock.request_transition_candidate(_ids(1401))[0]
    _assert(first.env_id == 1400 and second.env_id == 1401, "independent request failed")
    return {
        "same_env_second_request": "rejected",
        "different_env_independent": True,
        "mixed_batch_atomic": True,
    }


def test_g7_episode_advance_blocked_by_outstanding() -> dict[str, Any]:
    clock = _clock(1500, 1501)
    clock.advance_episode(_ids(1500, 1501))
    active = clock.request_transition_candidate(_ids(1500))[0]
    before = _snapshot(clock, 1500, 1501)
    _expect_clock_error(
        "outstanding_transition",
        lambda: clock.advance_episode(_ids(1500)),
    )
    _expect_clock_error(
        "outstanding_transition",
        lambda: clock.advance_episode(_ids(1501, 1500)),
    )
    _assert(_snapshot(clock, 1500, 1501) == before, "blocked advance changed rows")
    clock.advance_episode(_ids(1501))
    _assert(
        _snapshot(clock, 1500)[0].outstanding_transition_generation
        == active.transition_generation,
        "blocked episode advance discarded candidate",
    )
    return {
        "single_blocked": True,
        "mixed_batch_atomic": True,
        "candidate_preserved": True,
        "free_env_advanced": 1,
    }


def test_g8_transition_survives_episode_advance() -> dict[str, Any]:
    clock = _clock(1600)
    clock.advance_episode(_ids(1600))
    first = clock.request_transition_candidate(_ids(1600))[0]
    clock.commit_transition(_ids(1600), (first,))
    after_first = clock.advance_episode(_ids(1600))[0]
    _assert(after_first.episode_generation == 1, "episode did not advance")
    _assert(after_first.transition_generation == 0, "transition reset across episode")
    second = clock.request_transition_candidate(_ids(1600))[0]
    clock.commit_transition(_ids(1600), (second,))
    final = _snapshot(clock, 1600)[0]
    _assert(final.transition_generation == 1, "next transition was not contiguous")
    return {
        "episode_generation": final.episode_generation,
        "transition_generation": final.transition_generation,
        "transition_survived_episode_advance": True,
    }


def test_g9_token_independence() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    clock = RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(1700))
    clock.advance_episode(_ids(1700))

    first_context = clock.request_transition_candidate(_ids(1700))[0]
    first_facts = producer.build_facts(_facts_input(first_context))
    first_token = int(first_facts.consume_once_token[0].item())
    _assert(
        int(first_facts.episode_generation[0].item())
        == first_context.episode_generation,
        "producer changed episode generation",
    )
    _assert(
        int(first_facts.transition_generation[0].item())
        == first_context.transition_generation,
        "producer changed transition generation",
    )
    clock.commit_transition(_ids(1700), (first_context,))

    second_context = clock.request_transition_candidate(_ids(1700))[0]
    _expect_error(
        RUNTIME.ExecutionFactsProducerRuntimeError,
        lambda: producer.build_facts(
            _facts_input(second_context, invalid_completion_dtype=True)
        ),
    )
    pending = _snapshot(clock, 1700)[0]
    _assert(pending.transition_generation == 0, "failed facts build committed clock")
    _assert(
        pending.outstanding_transition_generation == 1,
        "failed facts build discarded candidate",
    )
    retry_facts = producer.build_facts(_facts_input(second_context))
    retry_token = int(retry_facts.consume_once_token[0].item())
    _assert(retry_token - first_token == 2, "failed facts token was not burned")
    _assert(
        int(retry_facts.transition_generation[0].item()) == 1,
        "retry did not reuse the same transition candidate",
    )
    clock.commit_transition(_ids(1700), (second_context,))
    _assert(_snapshot(clock, 1700)[0].transition_generation == 1, "commit gap exists")
    return {
        "first_token": first_token,
        "retry_token": retry_token,
        "token_delta": retry_token - first_token,
        "transition_delta": 1,
        "same_candidate_retried": True,
        "producer_api_unchanged": True,
    }


def test_g10_non_rng_alias_and_side_effects() -> dict[str, Any]:
    event, _ = _profiles()
    declared = _ids(1800, 1801)
    python_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()
    logger_before = _logger_state()
    files_before = _file_inventory()
    cwd_before = Path.cwd()
    environment_before = dict(os.environ)
    sys_path_before = tuple(sys.path)

    clock = RUNTIME.LifecycleGenerationClock(event, env_ids=declared)
    declared[0] = -999
    _assert(_snapshot(clock, 1800)[0].env_id == 1800, "declared tensor aliased clock")
    clock.advance_episode(_ids(1800, 1801))
    snapshot_row = _snapshot(clock, 1800)[0]
    altered_snapshot = replace(snapshot_row, episode_generation=99)
    _assert(altered_snapshot.episode_generation == 99, "snapshot replacement failed")
    _assert(_snapshot(clock, 1800)[0].episode_generation == 0, "snapshot aliased clock")
    _expect_error(
        FrozenInstanceError,
        lambda: setattr(snapshot_row, "episode_generation", 12),
    )

    context = clock.request_transition_candidate(_ids(1800))[0]
    copied = replace(context)
    _expect_clock_error(
        "candidate_identity",
        lambda: clock.commit_transition(_ids(1800), (copied,)),
    )
    _assert(
        _snapshot(clock, 1800)[0].outstanding_transition_generation == 0,
        "copied context altered active candidate",
    )
    clock.commit_transition(_ids(1800), (context,))

    tamper_clock = RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(1802))
    tamper_clock.advance_episode(_ids(1802))
    tampered = tamper_clock.request_transition_candidate(_ids(1802))[0]
    before_tamper = _snapshot(tamper_clock, 1802)[0]
    object.__setattr__(tampered, "transition_generation", 7)
    _expect_clock_error(
        "future_candidate",
        lambda: tamper_clock.commit_transition(_ids(1802), (tampered,)),
    )
    _assert(
        _snapshot(tamper_clock, 1802)[0] == before_tamper,
        "tampered active context changed internal state",
    )
    object.__setattr__(tampered, "transition_generation", 0)
    tamper_clock.commit_transition(_ids(1802), (tampered,))

    _assert(random.getstate() == python_before, "Python RNG side effect")
    _assert(torch.equal(torch.random.get_rng_state(), torch_before), "Torch RNG side effect")
    _assert(_logger_state() == logger_before, "logger side effect")
    _assert(_file_inventory() == files_before, "filesystem side effect")
    _assert(Path.cwd() == cwd_before, "cwd side effect")
    _assert(dict(os.environ) == environment_before, "environment side effect")
    _assert(tuple(sys.path) == sys_path_before, "sys.path side effect")
    return {
        "python_rng_unchanged": True,
        "torch_rng_unchanged": True,
        "logger_unchanged": True,
        "filesystem_unchanged": True,
        "cwd_environment_sys_path_unchanged": True,
        "snapshot_alias_isolated": True,
        "context_copy_rejected": True,
        "active_context_tamper_rejected": True,
        "constructor_included": True,
    }


def test_g11_profile_gate_and_default_off() -> dict[str, Any]:
    event, existing = _profiles()
    calls: list[str] = []
    original_resolve = PROFILE.resolve_assignment_profile
    original_normalize = PROFILE.normalize_assignment_profile_name

    def _forbidden_resolve(*args: Any, **kwargs: Any) -> Any:
        calls.append("resolve")
        raise AssertionError("clock invoked profile resolver")

    def _forbidden_normalize(*args: Any, **kwargs: Any) -> Any:
        calls.append("normalize")
        raise AssertionError("clock invoked profile normalizer")

    PROFILE.resolve_assignment_profile = _forbidden_resolve
    PROFILE.normalize_assignment_profile_name = _forbidden_normalize
    try:
        accepted = RUNTIME.LifecycleGenerationClock(event, env_ids=_ids(1900))
        _assert(_snapshot(accepted, 1900)[0].episode_generation == -1, "event rejected")
        for index, candidate in enumerate(existing):
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda candidate=candidate, index=index: RUNTIME.LifecycleGenerationClock(
                    candidate,
                    env_ids=_ids(1910 + index),
                ),
            )
        raw_candidates = (
            PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            "event_gated_local_mrta",
            {"profile_name": "event_gated_local_mrta"},
        )
        for index, candidate in enumerate(raw_candidates):
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda candidate=candidate, index=index: RUNTIME.LifecycleGenerationClock(
                    candidate,
                    env_ids=_ids(1920 + index),
                ),
            )
    finally:
        PROFILE.resolve_assignment_profile = original_resolve
        PROFILE.normalize_assignment_profile_name = original_normalize

    _assert(calls == [], f"fallback profile path invoked: {calls}")
    readiness_error = _expect_error(
        PROFILE.PhaseAExecutionNotAuthorizedError,
        lambda: PROFILE.require_assignment_profile_runtime_ready(
            event,
            consumer="B0-1B generation-clock pure test",
            entrypoint="standalone pure test",
            current_phase="B0-1B",
            barrier="event runtime remains default-off",
        ),
    )
    _assert(type(readiness_error) is PROFILE.PhaseAExecutionNotAuthorizedError, "wrong block")
    _assert(event.runtime_readiness.value == "interface_only", "readiness opened")
    _assert(event.training_support.value == "phase_a_blocked", "training opened")
    _assert(event.playback_support.value == "blocked", "playback opened")
    return {
        "exact_event_type_accepted": True,
        "existing_profiles_rejected": len(existing),
        "raw_profiles_rejected": len(raw_candidates),
        "resolver_calls": len(calls),
        "runtime_readiness": event.runtime_readiness.value,
        "training_support": event.training_support.value,
        "playback_support": event.playback_support.value,
    }


def test_g12_no_later_capabilities_or_wiring() -> dict[str, Any]:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(RUNTIME_PATH))
    forbidden_symbols = (
        "LifecycleAuthorityRuntime",
        "LifecycleStateStore",
        "TransitionConsumeLedger",
        "LifecycleTransitionResult",
        "LifecycleEvent",
        "TerminationReason",
        "PreResetTransitionMailbox",
        "TerminalCriticSidecar",
        "updated_failed_pairs",
        "TEAM_INFEASIBLE",
    )
    for symbol in forbidden_symbols:
        _assert(symbol not in source, f"runtime module contains {symbol}")

    forbidden_methods = {
        "mutate_state",
        "finalize_result",
        "consume",
        "commit_ownership",
        "reset_episode",
        "cancel_transition",
        "rollback_transition",
        "read_handoff",
        "acknowledge",
        "build_sidecar",
    }
    methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    _assert(not (methods & forbidden_methods), "later-phase method exists")

    clock_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LifecycleGenerationClock"
    )
    clock_public = tuple(
        node.name
        for node in clock_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    _assert(
        clock_public
        == (
            "snapshot",
            "advance_episode",
            "request_transition_candidate",
            "commit_transition",
        ),
        "clock public capability surface changed",
    )
    clock_source = ast.get_source_segment(source, clock_class) or ""
    for coupling in (
        "_NEXT_TOKEN_BY_ENV",
        "_PROCESS_TOKEN_LOCK",
        "consume_once_token",
        "build_facts",
        "EnvironmentExecutionFactsProducer",
    ):
        _assert(coupling not in clock_source, f"clock coupled to producer: {coupling}")
    _assert(
        "next_transition[row] = context.transition_generation" not in clock_source,
        "commit rereads externally held context after validation",
    )

    producer_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "EnvironmentExecutionFactsProducer"
    )
    producer_public = tuple(
        node.name
        for node in producer_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    _assert(producer_public == ("build_facts",), "B0-1A producer API changed")
    _assert(
        tuple(RUNTIME.EnvironmentExecutionFactsProducer.__slots__)
        == ("_profile", "_producer_stamp"),
        "B0-1A producer stores clock state",
    )
    producer_source = ast.get_source_segment(source, producer_class) or ""
    _assert("LifecycleGenerationClock" not in producer_source, "producer owns clock")
    _assert(
        source.count("ExecutionTransitionFacts.from_mapping") == 1,
        "canonical facts factory call changed",
    )

    entry_paths = (
        SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_TASK_SOURCE / "assignment_harl_wrapper.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_TASK_SOURCE / "assignment_controller.py",
        SCAN_TASK_SOURCE / "__init__.py",
    )
    runtime_leaf = RUNTIME_MODULE.rsplit(".", 1)[-1]
    for path in entry_paths:
        entry_source = path.read_text(encoding="utf-8")
        _assert(runtime_leaf not in entry_source, f"runtime module wired in {path.name}")
        _assert("LifecycleGenerationClock" not in entry_source, f"clock wired in {path.name}")

    blocked_modules = sorted(
        name
        for name in sys.modules
        if name == "isaaclab" or name.startswith(("isaaclab.", "omni", "pxr", "harl"))
    )
    _assert(blocked_modules == [], f"heavy runtime modules imported: {blocked_modules}")
    return {
        "clock_public_methods": list(clock_public),
        "producer_public_methods": list(producer_public),
        "forbidden_symbols_absent": len(forbidden_symbols),
        "environment_wrapper_resolver_controller_wiring": "absent",
        "heavy_runtime_imports": blocked_modules,
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("G1_initial_state", test_g1_initial_state),
    ("G2_episode_advance_selected_atomic_overflow", test_g2_episode_advance_selected_atomic_overflow),
    ("G3_candidate_generation_and_overflow", test_g3_candidate_generation_and_overflow),
    ("G4_explicit_multirow_commit", test_g4_explicit_multirow_commit),
    ("G5_invalid_commits_fail_closed", test_g5_invalid_commits_fail_closed),
    ("G6_one_outstanding_per_env", test_g6_one_outstanding_per_env),
    ("G7_episode_advance_blocked_by_outstanding", test_g7_episode_advance_blocked_by_outstanding),
    ("G8_transition_survives_episode_advance", test_g8_transition_survives_episode_advance),
    ("G9_token_independence", test_g9_token_independence),
    ("G10_non_rng_alias_and_side_effects", test_g10_non_rng_alias_and_side_effects),
    ("G11_profile_gate_and_default_off", test_g11_profile_gate_and_default_off),
    ("G12_no_later_capabilities_or_wiring", test_g12_no_later_capabilities_or_wiring),
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
            "clock_ownership": "one retained instance per declared env domain",
            "initial_episode_generation": -1,
            "initial_transition_generation": -1,
            "validation_then_single_state_swap": True,
            "token_generation_independent": True,
        },
        "runtime_boundary": {
            "generation_clock": "pure_default_off_implemented",
            "facts_producer": "B0-1A_unchanged",
            "environment_hook": "absent",
            "lifecycle_mutation": "absent",
            "consume_finalization": "absent",
            "mailbox_sidecar": "absent",
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
