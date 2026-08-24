"""Pure/static B1W-I4-1 facade, wrapper, and composition verification.

No Isaac, AppLauncher, Omni, PXr, HARL, training, playback, or evaluation code
is imported or executed.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Callable

import gymnasium
import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEVICE = torch.device("cpu")

PATHS = {
    "profile": SCAN_SOURCE / "assignment_profile_contract.py",
    "transition": SCAN_SOURCE / "assignment_lifecycle_transition_contract.py",
    "event": SCAN_SOURCE / "assignment_event_contract.py",
    "b01": SCAN_SOURCE / "assignment_lifecycle_authority_runtime.py",
    "claim": SCAN_SOURCE / "assignment_initial_claim_runtime.py",
    "b02": SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py",
    "fence": SCAN_SOURCE / "assignment_interstep_claim_window_runtime.py",
    "domain": SCAN_SOURCE / "assignment_event_profile_runtime_domain.py",
    "sync": SCAN_SOURCE / "assignment_event_profile_synchronous_runtime.py",
    "facade": SCAN_SOURCE / "assignment_event_runtime_facade.py",
    "wrapper": SCAN_SOURCE / "assignment_harl_wrapper.py",
    "package_init": SCAN_SOURCE / "__init__.py",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
    return logging.root.level, tuple(id(handler) for handler in logging.root.handlers), named


def _inventory() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    )


def _numpy_state() -> tuple[object, ...]:
    state = np.random.get_state()
    return state[0], state[1].copy(), state[2], state[3], state[4]


def _same_numpy_state(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


_IMPORT_RANDOM = random.getstate()
_IMPORT_TORCH_RANDOM = torch.random.get_rng_state().clone()
_IMPORT_NUMPY_RANDOM = _numpy_state()
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
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load(short_name: str) -> ModuleType:
    name = f"{PREFIX}.{PATHS[short_name].stem}"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, PATHS[short_name])
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PATHS[short_name]}")
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
PROFILE = _load("profile")
TRANSITION = _load("transition")
EVENT = _load("event")
B01 = _load("b01")
CLAIM = _load("claim")
B02 = _load("b02")
FENCE = _load("fence")
DOMAIN = _load("domain")
SYNC = _load("sync")
FACADE = _load("facade")
WRAPPER = _load("wrapper")
_PROFILE_REGISTRY = PROFILE.get_assignment_profile_registry()
_PROFILE_REGISTRY_REPR = repr(_PROFILE_REGISTRY)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Phase = FENCE._ClaimWindowFencePhase


def _i(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=DEVICE)


def _profile(name: Any = None) -> Any:
    actual = PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA if name is None else name
    return PROFILE.resolve_assignment_profile(
        actual,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )


def _domain(profile: Any, *, robots: int = 2, tasks: int = 3) -> Any:
    return DOMAIN._EventProfileLifecycleRuntimeDomain(
        DOMAIN._EventProfileLifecycleDomainSpec(
            profile,
            device=DEVICE,
            env_ids=_i((0,)),
            num_robots=robots,
            num_tasks=tasks,
        )
    )


def _reset_args(
    domain: Any,
    *,
    executing_task: int | None,
    robot_state: Any = None,
) -> dict[str, torch.Tensor]:
    identity = domain.identity
    tasks = torch.full(
        (1, identity.num_tasks), int(TaskState.AVAILABLE), dtype=torch.int64
    )
    robots = torch.full(
        (1, identity.num_robots),
        int(RobotState.NEEDS_ASSIGNMENT),
        dtype=torch.int64,
    )
    ownership = torch.full((1, identity.num_tasks), -1, dtype=torch.int64)
    if robot_state is not None:
        robots[0, 0] = int(robot_state)
    return {
        "selected_env_ids": _i((0,)),
        "initial_task_state": tasks,
        "initial_robot_state": robots,
        "initial_ownership": ownership,
    }


def _report(domain: Any, *, terminal: bool) -> Any:
    identity = domain.identity
    terminal_rows = torch.full((identity.num_envs,), terminal, dtype=torch.bool)
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=torch.zeros(
            (identity.num_envs, identity.num_tasks), dtype=torch.bool
        ),
        raw_new_candidate=torch.zeros(
            (identity.num_envs, identity.num_robots, identity.num_tasks),
            dtype=torch.bool,
        ),
        physical_truncated=terminal_rows,
        time_limit_reached=terminal_rows,
    )


class _EventEnvironment:
    def __init__(
        self,
        profile: Any,
        domain: Any,
        *,
        executing_task: int | None = None,
        robot_state: Any = None,
        terminal: bool = False,
    ) -> None:
        self._resolved_assignment_profile = profile
        self.domain = domain
        self.validation = domain.environment_admission_validation_port
        self.lifecycle = domain.environment_port
        self.executing_task = executing_task
        self.initial_robot_state = robot_state
        self.terminal = terminal
        self.num_envs = 1
        self.num_viewpoints = domain.identity.num_tasks
        self.device = DEVICE
        self.max_episode_length = 32
        self.possible_agents = tuple(
            f"agent_{index}" for index in range(domain.identity.num_robots)
        )
        self.agents = list(self.possible_agents)
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-np.inf, np.inf, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self.cfg = SimpleNamespace(
            assignment_lifecycle_profile=profile.profile_name.value,
        )
        self.reset_calls = 0
        self.step_calls = 0
        self.last_actions: object | None = None

    @property
    def unwrapped(self) -> "_EventEnvironment":
        return self

    def _obs(self) -> dict[str, torch.Tensor]:
        return {
            agent: torch.full((1, 4), float(index), dtype=torch.float32)
            for index, agent in enumerate(self.possible_agents)
        }

    def reset(self) -> tuple[dict[str, torch.Tensor], dict[str, object]]:
        self.reset_calls += 1
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(
            **_reset_args(
                self.domain,
                executing_task=self.executing_task,
                robot_state=self.initial_robot_state,
            )
        ) as rebuild:
            rebuild.commit_physical_reset_complete()
        return self._obs(), {"route": "event_reset"}

    def step(
        self, actions: object
    ) -> tuple[
        dict[str, torch.Tensor],
        dict[str, torch.Tensor],
        dict[str, torch.Tensor],
        dict[str, torch.Tensor],
        dict[str, object],
    ]:
        self.step_calls += 1
        self.last_actions = actions.detach().clone() if type(actions) is torch.Tensor else actions
        self.validation.validate_physical_step_entry_for_active_call()
        self.validation.validate_physical_finalization_for_active_call()
        self.lifecycle.finalize_physical_transition(_report(self.domain, terminal=self.terminal))
        if self.terminal:
            self.validation.validate_reset_entry_for_active_call()
            with self.lifecycle.episode_rebuild(
                **_reset_args(
                    self.domain,
                    executing_task=self.executing_task,
                    robot_state=self.initial_robot_state,
                )
            ) as rebuild:
                rebuild.commit_physical_reset_complete()
        terminated = {
            agent: torch.tensor([False], dtype=torch.bool) for agent in self.possible_agents
        }
        truncated = {
            agent: torch.tensor([self.terminal], dtype=torch.bool)
            for agent in self.possible_agents
        }
        rewards = {
            agent: torch.zeros((1,), dtype=torch.float32) for agent in self.possible_agents
        }
        return self._obs(), rewards, terminated, truncated, {"route": "event_step"}

    def close(self) -> None:
        return None


class _WrapperView:
    """Expose metadata while making direct wrapper reset/step calls observable."""

    def __init__(self, raw: _EventEnvironment) -> None:
        self.unwrapped = raw
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self.unwrapped, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("wrapper called raw reset directly")

    def step(self, actions: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("wrapper called raw step directly")

    def close(self) -> None:
        self.unwrapped.close()


class _LegacyEnvironment:
    def __init__(self, profile_name: str) -> None:
        self.num_envs = 1
        self.num_viewpoints = 3
        self.device = DEVICE
        self.max_episode_length = 32
        self.possible_agents = ("agent_0", "agent_1")
        self.agents = list(self.possible_agents)
        self.cfg = SimpleNamespace(
            assignment_lifecycle_profile=profile_name,
            assignment_lifecycle_resolver_enabled=profile_name == "diagnostics_hidden_state",
            assignment_lifecycle_resolver_strict_proposals=True,
            assignment_lifecycle_resolver_log_diagnostics=False,
            assignment_lifecycle_resolver_output_dir=None,
            assignment_cooldown_enabled=profile_name == "lifecycle_contract_c",
            assignment_cooldown_trigger_mode=(
                "budget" if profile_name == "lifecycle_contract_c" else "streak"
            ),
            assignment_cooldown_apply_to_action_mask=profile_name != "lifecycle_contract_c",
            assignment_cooldown_duration_steps=20,
            assignment_redirect_guardrail_enabled=False,
            assignment_failed_pair_memory_enabled=False,
            max_base_xy_step=(0.08, 0.10),
            scene=SimpleNamespace(env_spacing=1.0),
        )
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-np.inf, np.inf, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        feasible = torch.ones((1, 2, 3), dtype=torch.bool)
        self._problem = {
            "num_envs": 1,
            "num_agents": 2,
            "num_viewpoints": 3,
            "viewpoint_pos": torch.zeros((1, 3, 3), dtype=torch.float32),
            "viewpoint_quat": torch.zeros((1, 3, 4), dtype=torch.float32),
            "scanner_pos": torch.zeros((1, 2, 3), dtype=torch.float32),
            "viewpoints_covered": torch.zeros((1, 3), dtype=torch.bool),
            "available_mask": feasible.clone(),
            "feasible_mask": feasible.clone(),
            "static_geometric_feasible_mask": feasible.clone(),
            "cost_matrix": torch.zeros((1, 2, 3), dtype=torch.float32),
        }

    @property
    def unwrapped(self) -> "_LegacyEnvironment":
        return self

    def get_assignment_problem(self) -> dict[str, object]:
        return {
            key: value.detach().clone() if type(value) is torch.Tensor else value
            for key, value in self._problem.items()
        }

    def close(self) -> None:
        return None


def _compose(
    *,
    executing_task: int | None = None,
    robot_state: Any = None,
    terminal: bool = False,
    stages: list[str] | None = None,
) -> tuple[Any, Any, Any, Any]:
    profile = _profile()
    domain = _domain(profile)
    raw = _EventEnvironment(
        profile,
        domain,
        executing_task=executing_task,
        robot_state=robot_state,
        terminal=terminal,
    )
    view = _WrapperView(raw)
    observer = None if stages is None else lambda stage, detail: stages.append(stage)
    wrapper = WRAPPER._compose_event_assignment_harl_wrapper(
        env=view,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=observer,
    )
    return wrapper, raw, view, domain


def _seed_existing_claim(domain: Any, task_id: int) -> object:
    """Fixture-only B1 setup performed before the measured no-claim route."""

    envelope = domain.production_claim_port.prepare_production_initial_claim(
        selected_env_ids=_i((0,)),
        requested_task_by_robot=_i(((task_id, -1),)),
    )
    return domain.production_claim_port.commit_production_initial_claim(envelope)


def _expect(operation: Callable[[], Any], *, code: str | None = None) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure: {exc}")
        return exc
    raise AssertionError("expected failure")


def test_t1_exact_event_facade_construction() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    facade = wrapper._event_runtime_facade
    _assert(type(facade) is FACADE.EventAssignmentRuntimeFacade, "facade type")
    _assert(facade.resolved_assignment_profile is wrapper.resolved_assignment_profile, "profile identity")
    return {"facade": type(facade).__name__, "same_profile": True}


def test_t2_legacy_profile_with_facade_rejects() -> dict[str, object]:
    event_wrapper, _, _, _ = _compose()
    legacy = _profile(PROFILE.AssignmentProfileName.LEGACY)
    env = _LegacyEnvironment("legacy")
    _expect(
        lambda: WRAPPER.AssignmentHarlWrapper(
            env,
            resolved_assignment_profile=legacy,
            profile_resolution_origin=legacy.resolution_origin,
            event_runtime_facade=event_wrapper._event_runtime_facade,
        )
    )
    return {"mismatch": "rejected"}


def test_t3_event_profile_without_facade_rejects() -> dict[str, object]:
    profile = _profile()
    domain = _domain(profile)
    env = _EventEnvironment(profile, domain)
    _expect(
        lambda: WRAPPER.AssignmentHarlWrapper(
            env,
            resolved_assignment_profile=profile,
            profile_resolution_origin=profile.resolution_origin,
        )
    )
    return {"missing_facade": "rejected"}


def test_t4_foreign_domain_facade_rejects() -> dict[str, object]:
    profile = _profile()
    domain_a, domain_b = _domain(profile), _domain(profile)
    env = _EventEnvironment(profile, domain_a)
    runtime = SYNC.EventProfileSynchronousRuntimeCoordinator(
        environment=env,
        current_read_port=domain_a.current_read_port,
        production_claim_port=domain_a.production_claim_port,
        physical_step_admission_port=domain_a.physical_step_admission_port,
        standalone_reset_admission_port=domain_a.standalone_reset_admission_port,
        terminal_consumer_port=domain_a.terminal_consumer_port,
        fence_read_port=domain_a.interstep_fence_read_port,
    )
    _expect(
        lambda: FACADE._compose_event_assignment_runtime_facade(
            resolved_assignment_profile=profile,
            runtime_domain=domain_b,
            synchronous_runtime=runtime,
        ),
        code="facade_domain_identity",
    )
    return {"foreign_domain": "rejected"}


def test_t5_legacy_profiles_negative_isolation() -> dict[str, object]:
    rows = []
    for name in (
        "legacy",
        "lifecycle_contract_c",
        "lifecycle_ablation",
        "diagnostics_hidden_state",
    ):
        profile = _profile(PROFILE.AssignmentProfileName(name))
        wrapper = WRAPPER.AssignmentHarlWrapper(
            _LegacyEnvironment(name),
            resolved_assignment_profile=profile,
            profile_resolution_origin=profile.resolution_origin,
        )
        _assert(wrapper._event_runtime_facade is None, f"event facade leaked to {name}")
        _assert(wrapper._assignment_lifecycle_resolver_runtime is not None, f"legacy resolver absent for {name}")
        rows.append(name)
    return {"profiles": rows, "event_objects": 0}


def test_t6_event_wrapper_has_no_legacy_resolver() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    _assert(wrapper._assignment_lifecycle_resolver_runtime is None, "legacy resolver retained")
    _assert(wrapper.finalize_assignment_lifecycle_resolver() == {}, "event resolver finalize")
    return {"legacy_resolver": None}


def test_t7_wrapper_reset_routes_only_through_facade_o1() -> dict[str, object]:
    wrapper, raw, view, _ = _compose()
    obs, shared, mask = wrapper.reset()
    _assert(raw.reset_calls == 1 and view.direct_reset_calls == 0, "raw reset routing")
    _assert(set(obs) == set(raw.possible_agents), "raw observations not preserved")
    _assert(tuple(shared.shape) == (1, 2, 8), "provisional shared shape")
    _assert(mask is None, "I4-1 must not fabricate an event action mask")
    return {"o1_reset_calls": 1, "wrapper_direct_reset_calls": 0, "mask": None}


def test_t8_admitted_reset_canonical_and_open() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    result = wrapper._last_event_facade_reset_result
    current = domain.current_read_port.read_current()
    _assert(type(result) is FACADE.EventFacadeResetResult, "reset DTO")
    _assert(result.current_publication is current, "reset current identity")
    _assert(result.episode_generations == (0,), "episode reset generation")
    _assert(result.transition_generations == (-1,), "transition reset generation")
    _assert(domain.interstep_fence_read_port.read().phase is Phase.OPEN, "fence not open")
    return {"provenance": "canonical_episode_reset", "generation": [0, -1], "fence": "OPEN"}


def test_t9_executing_no_claim_continues_ak_task() -> dict[str, object]:
    stages: list[str] = []
    wrapper, raw, view, domain = _compose(executing_task=2, stages=stages)
    wrapper.reset()
    _seed_existing_claim(domain, 2)
    source = domain.current_read_port.read_current()
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(result.claim_artifact is None, "claim artifact fabricated")
    _assert(result.source_publication is source, "source P2 changed before facade step")
    _assert(result.admitted_publication is source, "Ak did not capture source P2")
    _assert(result.admitted_effective_assignment.tolist() == [[2, -1]], "Ak assignment")
    _assert(type(raw.last_actions) is torch.Tensor and raw.last_actions.tolist() == [[2, -1]], "control")
    _assert(raw.step_calls == 1 and view.direct_step_calls == 0, "step routing")
    _assert(stages.count("S5_DETERMINISTIC_CLAIM_COMMITTED") == 0, "B1 claim occurred")
    return {
        "facade_claim_count": 0,
        "controller_assignment": [2, -1],
        "wrapper_direct_step_calls": 0,
    }


def test_t10_needs_assignment_no_claim_stays_unowned() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    source = domain.current_read_port.read_current()
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(result.admitted_publication is source, "needs P2 not admitted")
    _assert(result.admitted_effective_assignment.tolist() == [[-1, -1]], "owner fabricated")
    _assert(bool((source.lifecycle_state.ownership == -1).all().item()), "ownership fabricated")
    return {"ownership": "none", "controller_assignment": [-1, -1]}


def test_t11_controller_source_ignores_wrapper_caches() -> dict[str, object]:
    wrapper, raw, _, domain = _compose(executing_task=2)
    wrapper.reset()
    _seed_existing_claim(domain, 2)
    wrapper.last_assignment = torch.tensor([[0, 0]], dtype=torch.int64)
    wrapper.last_assignment_proposal = torch.tensor([[1, 1]], dtype=torch.int64)
    wrapper.last_effective_assignment = torch.tensor([[0, 1]], dtype=torch.int64)
    _expect(lambda: wrapper.assignment_to_env_actions(torch.tensor([[0, 1]])))
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(result.admitted_effective_assignment.tolist() == [[2, -1]], "cache became control")
    _assert(raw.last_actions.tolist() == [[2, -1]], "proposal/cache became env action")
    return {"controller_source": "Ak-bound P2", "cache_source": False}


def test_t12_store_and_p2_unchanged_before_ak() -> dict[str, object]:
    wrapper, _, _, domain = _compose(executing_task=2)
    wrapper.reset()
    _seed_existing_claim(domain, 2)
    source = domain.current_read_port.read_current()
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(result.admitted_publication is source, "P2 identity changed before Ak")
    _assert(result.admitted_publication.store_version == source.store_version, "Store changed before Ak")
    return {"publication_identity_same": True, "store_version": source.store_version}


def test_t13_nonterminal_completion_opens_next_window() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    first = domain.interstep_fence_read_port.read().window
    wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    view = domain.interstep_fence_read_port.read()
    _assert(view.phase is Phase.OPEN and view.window is not first, "next window absent")
    _assert(not domain._coordinator.poisoned, "domain poisoned")
    return {"next_window": view.window.serial, "phase": "OPEN", "poisoned": False}


def test_t14_terminal_workflow_copied_then_atomically_acked() -> dict[str, object]:
    wrapper, _, _, domain = _compose(terminal=True)
    wrapper.reset()
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    artifacts = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    _assert(len(result.terminal_historical_payload) == 1, "terminal history absent")
    _assert(artifacts == (), "terminal slot not acknowledged")
    _assert(result.current_publication.episode_generation.tolist() == [1], "current P2")
    _assert(result.current_publication.result is None, "historical result leaked into current P2")
    _assert(not hasattr(wrapper._event_runtime_facade, "acknowledge_terminal_artifact"), "ack exposed")
    return {"historical_rows": 1, "pending_slots": 0, "raw_facade_ack": False}


def test_t15_private_exports_and_capability_surface() -> dict[str, object]:
    _assert(FACADE.__all__ == (), "facade public export")
    package_source = PATHS["package_init"].read_text(encoding="utf-8")
    _assert("assignment_event_runtime_facade" not in package_source, "package export")
    fields = tuple(FACADE.EventAssignmentRuntimeFacade.__dataclass_fields__)
    _assert(fields == ("_runtime", "_resolved_profile", "_domain_identity"), f"facade fields {fields}")
    source = PATHS["facade"].read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in {"Lock", "RLock", "Condition", "Semaphore"}
    }
    _assert(not forbidden_calls, f"facade synchronization leaked: {forbidden_calls}")
    for name in (
        "commit_claim",
        "capture_pending_terminal_artifacts",
        "acknowledge_terminal_artifact",
    ):
        _assert(not hasattr(FACADE.EventAssignmentRuntimeFacade, name), f"forbidden facade method {name}")
    for name in (
        "capture_proposal_decision",
        "resolve_proposals",
        "step_resolved_proposals",
        "resolve_and_step_proposals",
    ):
        _assert(hasattr(FACADE.EventAssignmentRuntimeFacade, name), f"missing I4-2 facade method {name}")
    return {"public_exports": 0, "retained_fields": list(fields), "new_mutex": 0}


TESTS = (
    ("I4-1-T1", test_t1_exact_event_facade_construction),
    ("I4-1-T2", test_t2_legacy_profile_with_facade_rejects),
    ("I4-1-T3", test_t3_event_profile_without_facade_rejects),
    ("I4-1-T4", test_t4_foreign_domain_facade_rejects),
    ("I4-1-T5", test_t5_legacy_profiles_negative_isolation),
    ("I4-1-T6", test_t6_event_wrapper_has_no_legacy_resolver),
    ("I4-1-T7", test_t7_wrapper_reset_routes_only_through_facade_o1),
    ("I4-1-T8", test_t8_admitted_reset_canonical_and_open),
    ("I4-1-T9", test_t9_executing_no_claim_continues_ak_task),
    ("I4-1-T10", test_t10_needs_assignment_no_claim_stays_unowned),
    ("I4-1-T11", test_t11_controller_source_ignores_wrapper_caches),
    ("I4-1-T12", test_t12_store_and_p2_unchanged_before_ak),
    ("I4-1-T13", test_t13_nonterminal_completion_opens_next_window),
    ("I4-1-T14", test_t14_terminal_workflow_copied_then_atomically_acked),
    ("I4-1-T15", test_t15_private_exports_and_capability_surface),
)


def _assert_global_side_effects() -> dict[str, object]:
    _assert(random.getstate() == _IMPORT_RANDOM, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), _IMPORT_TORCH_RANDOM), "Torch RNG changed")
    _assert(_same_numpy_state(_numpy_state(), _IMPORT_NUMPY_RANDOM), "NumPy RNG changed")
    _assert(Path.cwd() == _IMPORT_CWD, "cwd changed")
    _assert(tuple(sys.path) == _IMPORT_SYS_PATH, "sys.path changed")
    _assert(dict(os.environ) == _IMPORT_ENV, "environment changed")
    _assert(_logging_state() == _IMPORT_LOGGING, "logging changed")
    _assert(_inventory() == _IMPORT_INVENTORY, "filesystem inventory changed")
    _assert(PROFILE.get_assignment_profile_registry() is _PROFILE_REGISTRY, "registry identity")
    _assert(repr(PROFILE.get_assignment_profile_registry()) == _PROFILE_REGISTRY_REPR, "registry content")
    return {
        "python_rng": "unchanged",
        "torch_rng": "unchanged",
        "numpy_rng": "unchanged",
        "cwd": "unchanged",
        "environment": "unchanged",
        "sys_path": "unchanged",
        "logging": "unchanged",
        "filesystem": "unchanged",
        "profile_registry": "unchanged",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = []
    for test_id, operation in TESTS:
        rows.append({"test": test_id, "status": "passed", "detail": operation()})
    payload = {
        "classification": (
            "PHASE-B1W-I4-1-EVENT-FACADE-COMPOSITION-RESET-CONTINUATION-"
            "COMPLETE-AWAITING-GPT-REVIEW"
        ),
        "passed": len(rows),
        "total": len(TESTS),
        "rows": rows,
        "side_effects": _assert_global_side_effects(),
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for row in rows:
            print(f"{row['test']}: passed")
        print(f"passed {len(rows)}/{len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
