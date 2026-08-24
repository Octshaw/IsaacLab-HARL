"""Pure B0-1A regressions for the default-off execution-facts producer.

The suite loads only the canonical profile, transition-contract, and producer
sources through namespace-only package placeholders.  It does not execute the
task package initializer, AppLauncher, Isaac, a wrapper, a resolver, HARL,
checkpoint I/O, training, playback, diagnosis, or evaluation.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import fields, replace
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_TASK_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PROFILE_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"
TRANSITION_PATH = (
    SCAN_TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
)
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

E = 2
M = 3
N = 5
DEVICE = torch.device("cpu")

FACTS_FIELDS = (
    "schema_version",
    "producer_contract_version",
    "producer_id",
    "env_id",
    "episode_generation",
    "transition_generation",
    "physical_terminated",
    "physical_truncated",
    "time_limit_reached",
    "bad_transition",
    "completion_signals",
    "terminal_pair_failure_signals",
    "forced_release_signals",
    "robot_unavailable_signals",
    "robot_recovered_signals",
    "coverage_before_reset",
    "task_state_before_transition",
    "robot_state_before_transition",
    "ownership_before_transition",
    "consume_once_token",
)

TENSOR_SPECS = {
    "env_id": ((E,), torch.int64),
    "episode_generation": ((E,), torch.int64),
    "transition_generation": ((E,), torch.int64),
    "physical_terminated": ((E,), torch.bool),
    "physical_truncated": ((E,), torch.bool),
    "time_limit_reached": ((E,), torch.bool),
    "bad_transition": ((E,), torch.bool),
    "completion_signals": ((E, M, N), torch.bool),
    "terminal_pair_failure_signals": ((E, M, N), torch.bool),
    "forced_release_signals": ((E, M, N), torch.bool),
    "robot_unavailable_signals": ((E, M), torch.bool),
    "robot_recovered_signals": ((E, M), torch.bool),
    "coverage_before_reset": ((E, N), torch.bool),
    "task_state_before_transition": ((E, N), torch.int64),
    "robot_state_before_transition": ((E, M), torch.int64),
    "ownership_before_transition": ((E, N), torch.int64),
    "consume_once_token": ((E,), torch.int64),
}


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


def _transition_input() -> Any:
    completion = torch.zeros((E, M, N), dtype=torch.bool, device=DEVICE)
    failure = torch.zeros((E, M, N), dtype=torch.bool, device=DEVICE)
    release = torch.zeros((E, M, N), dtype=torch.bool, device=DEVICE)

    completion[0, 0, 0] = True
    completion[1, 1, 2] = True
    failure[0, 1, 1] = True
    failure[1, 2, 3] = True
    release[0, 2, 2] = True
    release[1, 0, 1] = True

    return RUNTIME.ExecutionTransitionInput(
        device=DEVICE,
        env_id=torch.tensor([10, 20], dtype=torch.int64, device=DEVICE),
        episode_generation=torch.tensor(
            [3, 8], dtype=torch.int64, device=DEVICE
        ),
        transition_generation=torch.tensor(
            [12, 21], dtype=torch.int64, device=DEVICE
        ),
        physical_terminated=torch.tensor(
            [False, True], dtype=torch.bool, device=DEVICE
        ),
        physical_truncated=torch.tensor(
            [True, False], dtype=torch.bool, device=DEVICE
        ),
        time_limit_reached=torch.tensor(
            [True, False], dtype=torch.bool, device=DEVICE
        ),
        bad_transition=torch.tensor(
            [False, False], dtype=torch.bool, device=DEVICE
        ),
        completion_signals=completion,
        terminal_pair_failure_signals=failure,
        forced_release_signals=release,
        robot_unavailable_signals=torch.tensor(
            [[False, False, True], [False, False, False]],
            dtype=torch.bool,
            device=DEVICE,
        ),
        robot_recovered_signals=torch.tensor(
            [[False, False, False], [True, False, False]],
            dtype=torch.bool,
            device=DEVICE,
        ),
        coverage_before_transition=torch.tensor(
            [
                [False, True, False, False, True],
                [True, False, False, False, False],
            ],
            dtype=torch.bool,
            device=DEVICE,
        ),
        task_state_before_transition=torch.tensor(
            [[1, 2, 3, 0, 4], [2, 1, 3, 0, 0]],
            dtype=torch.int64,
            device=DEVICE,
        ),
        robot_state_before_transition=torch.tensor(
            [[0, 1, 2], [3, 0, 1]], dtype=torch.int64, device=DEVICE
        ),
        ownership_before_transition=torch.tensor(
            [[0, 1, 2, -1, 0], [2, 0, 1, 2, -1]],
            dtype=torch.int64,
            device=DEVICE,
        ),
    )


def _expected_mapping(transition_input: Any, tokens: torch.Tensor) -> dict[str, Any]:
    return {
        "schema_version": TRANSITION.EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        "producer_contract_version": (
            TRANSITION.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
        ),
        "producer_id": (
            TRANSITION.ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1
        ),
        "env_id": transition_input.env_id,
        "episode_generation": transition_input.episode_generation,
        "transition_generation": transition_input.transition_generation,
        "physical_terminated": transition_input.physical_terminated,
        "physical_truncated": transition_input.physical_truncated,
        "time_limit_reached": transition_input.time_limit_reached,
        "bad_transition": transition_input.bad_transition,
        "completion_signals": transition_input.completion_signals,
        "terminal_pair_failure_signals": (
            transition_input.terminal_pair_failure_signals
        ),
        "forced_release_signals": transition_input.forced_release_signals,
        "robot_unavailable_signals": transition_input.robot_unavailable_signals,
        "robot_recovered_signals": transition_input.robot_recovered_signals,
        "coverage_before_reset": (
            transition_input.coverage_before_transition
            | transition_input.completion_signals.any(dim=1)
        ),
        "task_state_before_transition": (
            transition_input.task_state_before_transition
        ),
        "robot_state_before_transition": (
            transition_input.robot_state_before_transition
        ),
        "ownership_before_transition": (
            transition_input.ownership_before_transition
        ),
        "consume_once_token": tokens,
    }


def _expect_error(exception_type: type[BaseException], operation: Callable[[], Any]) -> BaseException:
    try:
        operation()
    except exception_type as exc:
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _select_rows(transition_input: Any, indices: tuple[int, ...]) -> Any:
    index = torch.tensor(indices, dtype=torch.int64, device=DEVICE)
    values: dict[str, Any] = {"device": transition_input.device}
    for descriptor in fields(transition_input):
        if descriptor.name == "device":
            continue
        values[descriptor.name] = getattr(transition_input, descriptor.name).index_select(
            0, index
        )
    return RUNTIME.ExecutionTransitionInput(**values)


def _tensor_inputs(transition_input: Any) -> dict[str, torch.Tensor]:
    return {
        descriptor.name: getattr(transition_input, descriptor.name)
        for descriptor in fields(transition_input)
        if descriptor.name != "device"
    }


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


def test_t1_exact_event_profile_gate() -> dict[str, Any]:
    event, existing = _profiles()
    calls: list[tuple[str, tuple[Any, ...]]] = []
    original_resolve = PROFILE.resolve_assignment_profile
    original_normalize = PROFILE.normalize_assignment_profile_name

    def _forbidden_resolve(*args: Any, **kwargs: Any) -> Any:
        calls.append(("resolve", args))
        raise AssertionError("producer invoked the canonical profile resolver")

    def _forbidden_normalize(*args: Any, **kwargs: Any) -> Any:
        calls.append(("normalize", args))
        raise AssertionError("producer normalized a raw profile selector")

    PROFILE.resolve_assignment_profile = _forbidden_resolve
    PROFILE.normalize_assignment_profile_name = _forbidden_normalize
    try:
        producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
        _assert(
            object.__getattribute__(producer, "_profile") is event,
            "producer did not retain the exact canonical event object",
        )
        for candidate in existing:
            error = _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda candidate=candidate: (
                    RUNTIME.EnvironmentExecutionFactsProducer(candidate)
                ),
            )
            _assert(error.profile is candidate.profile_name, "wrong rejected profile")
            _assert(
                error.expected is PROFILE.ResolvedEventGatedAssignmentProfile,
                "wrong expected profile subtype",
            )
            _assert(
                error.actual is PROFILE.ResolvedExistingAssignmentProfile,
                "existing subtype was not rejected exactly",
            )
        for raw in ("event_gated_local_mrta", None, {"profile_name": "event_gated_local_mrta"}):
            _expect_error(
                PROFILE.AssignmentProfileRouteError,
                lambda raw=raw: RUNTIME.EnvironmentExecutionFactsProducer(raw),
            )
    finally:
        PROFILE.resolve_assignment_profile = original_resolve
        PROFILE.normalize_assignment_profile_name = original_normalize

    _assert(calls == [], f"producer used a second profile resolver: {calls}")
    return {
        "event_exact_type": type(event).__name__,
        "existing_rejected": len(existing),
        "raw_fallbacks_rejected": 3,
        "resolver_calls": len(calls),
    }


def test_t2_exact_full_batch_facts_construction() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    transition_input = _transition_input()
    facts = producer.build_facts(transition_input)
    facts_token = facts.consume_once_token
    expected = _expected_mapping(
        transition_input,
        facts_token,
    )
    mapping = facts.to_mapping()

    _assert(type(facts) is TRANSITION.ExecutionTransitionFacts, "wrong facts type")
    _assert(tuple(mapping) == FACTS_FIELDS, "frozen facts field order changed")
    _assert(mapping["schema_version"] == expected["schema_version"], "schema")
    _assert(
        mapping["producer_contract_version"]
        == expected["producer_contract_version"],
        "producer contract version",
    )
    _assert(mapping["producer_id"] is expected["producer_id"], "producer ID")
    _assert(facts.device == DEVICE, "facts device changed")
    _assert((facts.num_envs, facts.num_robots, facts.num_tasks) == (E, M, N), "dims")

    for name, (shape, dtype) in TENSOR_SPECS.items():
        actual = mapping[name]
        _assert(type(actual) is torch.Tensor, f"{name} is not exact Tensor")
        _assert(tuple(actual.shape) == shape, f"{name} shape")
        _assert(actual.dtype is dtype, f"{name} dtype")
        _assert(actual.device == DEVICE, f"{name} device")
        _assert(actual.is_contiguous(), f"{name} not contiguous")
        _assert(not actual.requires_grad, f"{name} requires grad")
        _assert(torch.equal(actual, expected[name]), f"{name} content")
    _assert(bool(torch.all(facts_token >= 0).item()), "tokens are negative")

    nonzero_fields = sum(
        int(torch.count_nonzero(mapping[name]).item()) > 0
        for name in TENSOR_SPECS
        if name != "consume_once_token"
    )
    _assert(nonzero_fields >= 12, "fixture is not sufficiently nonzero")
    return {
        "shape": [E, M, N],
        "fields": len(mapping),
        "nonzero_tensor_fields": nonzero_fields,
        "producer_id": facts.producer_id.value,
    }


def test_t3_alias_isolation() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    transition_input = _transition_input()
    facts = producer.build_facts(transition_input)
    before = {name: value.clone() for name, value in facts.to_mapping().items() if type(value) is torch.Tensor}

    for tensor in _tensor_inputs(transition_input).values():
        if tensor.dtype is torch.bool:
            tensor.logical_not_()
        else:
            tensor.add_(97)

    after = facts.to_mapping()
    for name, expected in before.items():
        _assert(torch.equal(after[name], expected), f"input alias changed {name}")

    accessor_alias = facts.completion_signals
    accessor_alias.logical_not_()
    _assert(
        torch.equal(facts.completion_signals, before["completion_signals"]),
        "public accessor leaked writable storage",
    )
    mapping_alias = facts.to_mapping()["ownership_before_transition"]
    mapping_alias.add_(1)
    _assert(
        torch.equal(
            facts.ownership_before_transition,
            before["ownership_before_transition"],
        ),
        "to_mapping leaked writable storage",
    )
    return {"isolated_tensor_fields": len(before), "accessor_clone": True}


def test_t4_pair_attribution_preservation() -> dict[str, Any]:
    event, _ = _profiles()
    facts = RUNTIME.EnvironmentExecutionFactsProducer(event).build_facts(
        _transition_input()
    )
    expected_coordinates = {
        "completion_signals": ((0, 0, 0), (1, 1, 2)),
        "terminal_pair_failure_signals": ((0, 1, 1), (1, 2, 3)),
        "forced_release_signals": ((0, 2, 2), (1, 0, 1)),
    }
    for name, expected in expected_coordinates.items():
        actual = tuple(
            tuple(int(value) for value in row)
            for row in torch.nonzero(getattr(facts, name), as_tuple=False).tolist()
        )
        _assert(actual == expected, f"{name} pair attribution changed")
        _assert(tuple(getattr(facts, name).shape) == (E, M, N), f"{name} reduced")
    return {
        name: [list(item) for item in coordinates]
        for name, coordinates in expected_coordinates.items()
    }


def test_t5_external_generations_preserved() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    transition_input = replace(
        _transition_input(),
        episode_generation=torch.tensor([101, 4], dtype=torch.int64),
        transition_generation=torch.tensor([1001, 77], dtype=torch.int64),
    )
    facts = producer.build_facts(transition_input)
    _assert(
        torch.equal(facts.episode_generation, transition_input.episode_generation),
        "producer changed episode generations",
    )
    _assert(
        torch.equal(
            facts.transition_generation,
            transition_input.transition_generation,
        ),
        "producer changed transition generations",
    )
    return {
        "episode_generation": facts.episode_generation.tolist(),
        "transition_generation": facts.transition_generation.tolist(),
    }


def test_t6_token_monotonic_non_rng() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    transition_input = _transition_input()
    python_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()

    first = producer.build_facts(transition_input).consume_once_token
    env_10_only = producer.build_facts(
        _select_rows(transition_input, (0,))
    ).consume_once_token
    reconstructed_producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    reversed_batch = reconstructed_producer.build_facts(
        _select_rows(transition_input, (1, 0))
    ).consume_once_token

    first_values = first.tolist()
    _assert(
        env_10_only.tolist() == [first_values[0] + 1],
        "env 10 did not increment",
    )
    _assert(
        reversed_batch.tolist() == [first_values[1] + 1, first_values[0] + 2],
        "tokens reset across producer reconstruction or depend on row order",
    )
    _assert(random.getstate() == python_before, "Python RNG changed")
    _assert(
        torch.equal(torch.random.get_rng_state(), torch_before),
        "Torch RNG changed",
    )
    return {
        "env_10_sequence": [
            first_values[0],
            first_values[0] + 1,
            first_values[0] + 2,
        ],
        "env_20_sequence": [first_values[1], first_values[1] + 1],
        "survives_producer_reconstruction": True,
        "python_rng_unchanged": True,
        "torch_rng_unchanged": True,
    }


def test_t7_failed_construction_no_external_mutation() -> dict[str, Any]:
    event, _ = _profiles()
    producer = RUNTIME.EnvironmentExecutionFactsProducer(event)
    transition_input = _transition_input()
    first = producer.build_facts(transition_input).consume_once_token
    invalid = replace(
        transition_input,
        completion_signals=transition_input.completion_signals.to(torch.int64),
    )
    input_before = {
        name: tensor.clone() for name, tensor in _tensor_inputs(invalid).items()
    }
    logger_before = _logger_state()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        files_before = tuple(temporary_path.iterdir())
        _expect_error(
            RUNTIME.ExecutionFactsProducerRuntimeError,
            lambda: producer.build_facts(invalid),
        )
        files_after = tuple(temporary_path.iterdir())
    _assert(files_after == files_before, "failed construction wrote a file")
    _assert(_logger_state() == logger_before, "failed construction changed logging")
    for name, expected in input_before.items():
        _assert(torch.equal(_tensor_inputs(invalid)[name], expected), f"mutated {name}")

    after_failure = producer.build_facts(transition_input).consume_once_token
    _assert(
        after_failure.tolist()
        == [int(value) + 2 for value in first.tolist()],
        "failed construction token was reused instead of burned",
    )
    _assert(
        tuple(RUNTIME.EnvironmentExecutionFactsProducer.__slots__)
        == ("_profile", "_producer_stamp"),
        "producer stores unauthorized runtime state",
    )
    return {
        "tokens_before_failure": first.tolist(),
        "tokens_after_failure": after_failure.tolist(),
        "failed_token_burned": True,
        "external_tensors_unchanged": True,
    }


def test_t8_no_derived_lifecycle_result() -> dict[str, Any]:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(RUNTIME_PATH))
    forbidden_symbols = (
        "LifecycleTransitionResult",
        "TransitionConsumeLedger",
        "LifecycleEvent",
        "TerminationReason",
        "updated_failed_pairs",
        "TEAM_INFEASIBLE",
    )
    for symbol in forbidden_symbols:
        _assert(symbol not in source, f"runtime module contains {symbol}")

    forbidden_capabilities = {
        "mutate_state",
        "finalize_result",
        "consume",
        "commit_ownership",
        "reset_episode",
        "read_handoff",
        "acknowledge",
        "build_sidecar",
    }
    methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    _assert(not (methods & forbidden_capabilities), "unauthorized capability exists")

    producer_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "EnvironmentExecutionFactsProducer"
    )
    public_methods = tuple(
        node.name
        for node in producer_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    )
    _assert(public_methods == ("build_facts",), "producer public API expanded")

    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    _assert(not (set(forbidden_symbols) & imported_names), "forbidden import")
    _assert(
        source.count("ExecutionTransitionFacts.from_mapping") == 1,
        "canonical facts factory call is absent or duplicated",
    )
    for path in (
        SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_TASK_SOURCE / "assignment_harl_wrapper.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver.py",
        SCAN_TASK_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_TASK_SOURCE / "__init__.py",
    ):
        entry_source = path.read_text(encoding="utf-8")
        _assert(RUNTIME_MODULE.rsplit(".", 1)[-1] not in entry_source, f"wired in {path.name}")
        _assert("EnvironmentExecutionFactsProducer" not in entry_source, f"producer wired in {path.name}")
    return {
        "public_methods": list(public_methods),
        "forbidden_symbols_absent": len(forbidden_symbols),
        "environment_hook_absent": True,
    }


def test_t9_existing_profile_rejection_side_effects() -> dict[str, Any]:
    event, existing = _profiles()
    registry = PROFILE.get_assignment_profile_registry()
    registry_identity_before = (
        id(registry),
        tuple((id(key), id(value), repr(value)) for key, value in registry.items()),
    )
    python_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()
    logger_before = _logger_state()
    files_before = _file_inventory()
    cwd_before = Path.cwd()
    environment_before = dict(os.environ)
    sys_path_before = tuple(sys.path)

    for candidate in existing:
        _expect_error(
            PROFILE.AssignmentProfileRouteError,
            lambda candidate=candidate: RUNTIME.EnvironmentExecutionFactsProducer(
                candidate
            ),
        )

    registry_after = PROFILE.get_assignment_profile_registry()
    registry_identity_after = (
        id(registry_after),
        tuple(
            (id(key), id(value), repr(value))
            for key, value in registry_after.items()
        ),
    )
    _assert(random.getstate() == python_before, "Python RNG side effect")
    _assert(torch.equal(torch.random.get_rng_state(), torch_before), "Torch RNG side effect")
    _assert(_logger_state() == logger_before, "logger side effect")
    _assert(_file_inventory() == files_before, "filesystem side effect")
    _assert(Path.cwd() == cwd_before, "cwd side effect")
    _assert(dict(os.environ) == environment_before, "environment side effect")
    _assert(tuple(sys.path) == sys_path_before, "sys.path side effect")
    _assert(
        registry_identity_after == registry_identity_before,
        "profile registry identity changed",
    )
    _assert(event.runtime_readiness.value == "interface_only", "event readiness opened")
    _assert(event.training_support.value == "phase_a_blocked", "training opened")
    _assert(event.playback_support.value == "blocked", "playback opened")
    _assert(
        event.runtime_route.value == "event_gated_phase_a_interface_only_v1",
        "event route identity changed",
    )
    blocked_modules = sorted(
        name
        for name in sys.modules
        if name == "isaaclab"
        or name.startswith(("isaaclab.", "omni", "pxr", "harl"))
    )
    _assert(blocked_modules == [], f"runtime modules imported: {blocked_modules}")
    return {
        "existing_profiles_rejected": len(existing),
        "registry_identity_unchanged": True,
        "runtime_readiness": event.runtime_readiness.value,
        "training_support": event.training_support.value,
        "playback_support": event.playback_support.value,
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("T1_exact_event_profile_gate", test_t1_exact_event_profile_gate),
    ("T2_exact_full_batch_facts_construction", test_t2_exact_full_batch_facts_construction),
    ("T3_alias_isolation", test_t3_alias_isolation),
    ("T4_pair_attribution_preservation", test_t4_pair_attribution_preservation),
    ("T5_external_generations_preserved", test_t5_external_generations_preserved),
    ("T6_token_monotonic_non_rng", test_t6_token_monotonic_non_rng),
    ("T7_failed_construction_no_external_mutation", test_t7_failed_construction_no_external_mutation),
    ("T8_no_derived_lifecycle_result", test_t8_no_derived_lifecycle_result),
    ("T9_existing_profile_rejection_side_effects", test_t9_existing_profile_rejection_side_effects),
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
            results.append(
                {"name": name, "status": "passed", "evidence": evidence}
            )
    failed = len(TESTS) - passed
    return {
        "status": "passed" if failed == 0 else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": failed,
        "tests": results,
        "runtime_boundary": {
            "facts_producer": "pure_default_off_implemented",
            "environment_hook": "absent",
            "state_mutation": "absent",
            "consume_ledger": "absent",
            "result_finalization": "absent",
            "mailbox_sidecar": "absent",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"{result['status'].upper()} {result['passed']}/"
            f"{result['num_tests']} B0-1A pure groups"
        )
        for item in result["tests"]:
            print(f"{item['status'].upper()} {item['name']}")
            if item["status"] == "failed":
                print(f"  {item['error_type']}: {item['error']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
