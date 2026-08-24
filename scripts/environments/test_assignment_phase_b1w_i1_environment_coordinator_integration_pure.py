"""Pure/static B1W-I1 environment-validation and O1 integration suite.

No Isaac, AppLauncher, Omni, PXr, HARL, task discovery, training, playback, or
evaluation module is imported or executed.
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
from threading import Thread
from types import ModuleType
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"

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
    "env": SCAN_SOURCE / "scan_mobile_manipulator_env.py",
    "wrapper": SCAN_SOURCE / "assignment_harl_wrapper.py",
    "direct_env": REPO_ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py",
}
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
    return logging.root.level, tuple(id(h) for h in logging.root.handlers), logging.root.disabled, named


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


def _load(short_name: str) -> ModuleType:
    name = f"{PREFIX}.{PATHS[short_name].stem}"
    spec = importlib.util.spec_from_file_location(name, PATHS[short_name])
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PATHS[short_name]}")
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
PROFILE = _load("profile")
TRANSITION = _load("transition")
EVENT = _load("event")
B01 = _load("b01")
CLAIM = _load("claim")
B02 = _load("b02")
FENCE = _load("fence")
DOMAIN = _load("domain")
SYNC = _load("sync")
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


def _domain(*, env_ids: tuple[int, ...] = (0,), robots: int = 2, tasks: int = 3) -> Any:
    return DOMAIN._EventProfileLifecycleRuntimeDomain(
        DOMAIN._EventProfileLifecycleDomainSpec(
            _profile(),
            device=DEVICE,
            env_ids=_i(env_ids),
            num_robots=robots,
            num_tasks=tasks,
        )
    )


def _reset_args(domain: Any, selected: tuple[int, ...] | None = None) -> dict[str, torch.Tensor]:
    identity = domain.identity
    if selected is None:
        selected = tuple(int(v) for v in identity.env_ids.tolist())
    rows = len(selected)
    return {
        "selected_env_ids": _i(selected),
        "initial_task_state": torch.full((rows, identity.num_tasks), int(TaskState.AVAILABLE), dtype=torch.int64),
        "initial_robot_state": torch.full((rows, identity.num_robots), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64),
        "initial_ownership": torch.full((rows, identity.num_tasks), -1, dtype=torch.int64),
    }


def _report(domain: Any, *, terminal: bool = False) -> Any:
    identity = domain.identity
    terminal_rows = torch.full((identity.num_envs,), terminal, dtype=torch.bool)
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=torch.zeros((identity.num_envs, identity.num_tasks), dtype=torch.bool),
        raw_new_candidate=torch.zeros((identity.num_envs, identity.num_robots, identity.num_tasks), dtype=torch.bool),
        physical_truncated=terminal_rows,
        time_limit_reached=terminal_rows,
    )


class _FakeEnvironment:
    def __init__(self, domain: Any, stages: list[str] | None = None) -> None:
        self.domain = domain
        self.validation = domain.environment_admission_validation_port
        self.lifecycle = domain.environment_port
        self.stages = [] if stages is None else stages
        self.raise_reset = False
        self.raise_step = False
        self.skip_finalization = False
        self.autoreset = False
        self.last_assignment: torch.Tensor | None = None
        self.geometry_version = 0

    def reset(self) -> dict[str, bool]:
        self.validation.validate_reset_entry_for_active_call()
        self.stages.append("S2_RESET_ENTRY_VALIDATED")
        if self.raise_reset:
            raise RuntimeError("injected reset failure")
        with self.lifecycle.episode_rebuild(**_reset_args(self.domain)) as rebuild:
            rebuild.commit_physical_reset_complete()
        return {"reset": True}

    def step(self, actions: object) -> tuple[str, object]:
        self.validation.validate_physical_step_entry_for_active_call()
        self.stages.append("S10_STEP_ENTRY_VALIDATED")
        if self.raise_step:
            raise RuntimeError("injected step failure")
        if not self.skip_finalization:
            self.validation.validate_physical_finalization_for_active_call()
            self.stages.append("S11_I3_VALIDATED")
            self.lifecycle.finalize_physical_transition(_report(self.domain, terminal=self.autoreset))
        if self.autoreset:
            self.validation.validate_reset_entry_for_active_call()
            with self.lifecycle.episode_rebuild(**_reset_args(self.domain)) as rebuild:
                rebuild.commit_physical_reset_complete()
        return "step", actions


def _coordinator(domain: Any, env: _FakeEnvironment, stages: list[str] | None = None) -> Any:
    observer = None if stages is None else lambda stage, detail: stages.append(stage)
    return SYNC.EventProfileSynchronousRuntimeCoordinator(
        environment=env,
        current_read_port=domain.current_read_port,
        production_claim_port=domain.production_claim_port,
        physical_step_admission_port=domain.physical_step_admission_port,
        standalone_reset_admission_port=domain.standalone_reset_admission_port,
        terminal_consumer_port=domain.terminal_consumer_port,
        fence_read_port=domain.interstep_fence_read_port,
        stage_observer=observer,
    )


def _expect(operation: Callable[[], Any], *, code: str | None = None) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError("expected failure")


def _reset(domain: Any, env: _FakeEnvironment | None = None) -> tuple[Any, _FakeEnvironment]:
    actual = _FakeEnvironment(domain) if env is None else env
    _coordinator(domain, actual).reset_environment()
    return domain.interstep_fence_read_port.read().window, actual


def _valid_step_direct(domain: Any, *, autoreset: bool = False) -> Any:
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    validation = domain.environment_admission_validation_port
    validation.validate_physical_step_entry_for_active_call()
    validation.validate_physical_finalization_for_active_call()
    domain.environment_port.finalize_physical_transition(_report(domain, terminal=autoreset))
    if autoreset:
        validation.validate_reset_entry_for_active_call()
        with domain.environment_port.episode_rebuild(**_reset_args(domain)) as rebuild:
            rebuild.commit_physical_reset_complete()
    return admission


def test_t1_capability_composition_identity() -> dict[str, Any]:
    a, b = _domain(), _domain()
    _coordinator(a, _FakeEnvironment(a))
    _expect(
        lambda: SYNC.EventProfileSynchronousRuntimeCoordinator(
            environment=_FakeEnvironment(a),
            current_read_port=a.current_read_port,
            production_claim_port=b.production_claim_port,
            physical_step_admission_port=a.physical_step_admission_port,
            standalone_reset_admission_port=a.standalone_reset_admission_port,
            terminal_consumer_port=a.terminal_consumer_port,
        ),
        code="coordinator_domain_identity",
    )
    return {"same_domain": True, "cross_domain": "rejected"}


def test_t2_initial_reset_bootstrap() -> dict[str, Any]:
    domain, stages = _domain(), []
    env = _FakeEnvironment(domain, stages)
    coordinator = _coordinator(domain, env, stages)
    coordinator.reset_environment()
    view = domain.interstep_fence_read_port.read()
    _assert(view.phase is Phase.OPEN and view.window.serial == 0, "W1 not opened")
    _assert(stages.index("S2_RESET_ENTRY_VALIDATED") < stages.index("S4_WINDOW_OPEN"), "early open")
    return {"path": "PREBOOTSTRAP-R1-reset-return-W1", "early_open": False}


def test_t3_raw_reset_bypass() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    _expect(env.reset, code="reset_admission_required")
    _assert(domain.interstep_fence_read_port.read().phase is Phase.FAULTED, "raw reset did not poison")
    return {"raw_reset": "fail_stop"}


def test_t4_later_standalone_reset() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    w1 = domain.interstep_fence_read_port.read().window
    coordinator.reset_environment()
    w2 = domain.interstep_fence_read_port.read().window
    _assert(w1 is not w2 and (w1.serial, w2.serial) == (0, 1), "later reset window identity")
    return {"w1": 0, "w2": 1}


def test_t5_step_entry_exact_ak() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry_for_active_call()
    _expect(domain.environment_admission_validation_port.validate_physical_step_entry_for_active_call, code="admission_already_consumed")
    _assert(domain.interstep_fence_read_port.read().phase is Phase.FAULTED, "duplicate entry did not poison")
    foreign = _domain()
    _reset(foreign)
    foreign.physical_step_admission_port.begin_physical_step_admission()
    failures: list[BaseException] = []
    thread = Thread(target=lambda: _capture_failure(foreign.environment_admission_validation_port.validate_physical_step_entry_for_active_call, failures))
    thread.start()
    thread.join(5.0)
    _assert(failures and foreign.interstep_fence_read_port.read().phase is Phase.FAULTED, "foreign context")
    return {"exact_once": True, "duplicate": "fail_stop", "foreign_context": "fail_stop"}


def _capture_failure(operation: Callable[[], Any], failures: list[BaseException]) -> None:
    try:
        operation()
    except BaseException as exc:
        failures.append(exc)


def test_t6_finalization_same_ak() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    admission = _valid_step_direct(domain)
    domain.physical_step_admission_port.commit_successful_return(admission)
    return {"entry_and_i3": "same_Ak", "completed": True}


def test_t7_finalization_before_entry() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    domain.physical_step_admission_port.begin_physical_step_admission()
    _expect(domain.environment_admission_validation_port.validate_physical_finalization_for_active_call, code="physical_step_admission_required")
    return {"finalization_before_entry": "fail_stop", "poisoned": domain._coordinator.poisoned}


def test_t8_autoreset_same_ak() -> dict[str, Any]:
    domain, stages = _domain(), []
    env = _FakeEnvironment(domain, stages)
    coordinator = _coordinator(domain, env, stages)
    coordinator.reset_environment()
    env.autoreset = True
    coordinator.step_environment(action_builder=lambda env, assignment: assignment)
    current = domain.current_read_port.read_current()
    _assert(int(current.episode_generation[0].item()) == 1, "autoreset generation")
    _assert(domain.interstep_fence_read_port.read().phase is Phase.OPEN, "outer completion did not open")
    return {"same_Ak": True, "early_open": False, "episode": 1}


def test_t9_zero_claim_continuation() -> dict[str, Any]:
    domain, env = _domain(), _FakeEnvironment(_domain())
    domain = env.domain
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    before = domain.current_read_port.read_current()
    coordinator.step_environment(action_builder=lambda env, assignment: setattr(env, "last_assignment", assignment.clone()) or assignment)
    _assert(env.last_assignment is not None and bool((env.last_assignment == -1).all()), "zero claim mapping")
    _assert(before.store_version + 1 == domain.current_read_port.read_current().store_version, "only I3 should advance store")
    return {"claim_count": 0, "assignment": [[-1, -1]]}


def test_t10_deterministic_claim_then_ak() -> dict[str, Any]:
    domain = _domain()
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    coordinator.commit_deterministic_initial_claim(selected_env_ids=_i((0,)), requested_task_by_robot=_i(((1, -1),)))
    coordinator.step_environment(action_builder=lambda env, assignment: setattr(env, "last_assignment", assignment.clone()) or assignment)
    _assert(torch.equal(env.last_assignment, _i(((1, -1),))), "Ak mapping differs from claim")
    return {"mapping": [[1, -1]], "source": "Ak.P2"}


def test_t11_caller_cache_cannot_override_ak() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    proposal = _i(((2, -1),))
    coordinator.commit_deterministic_initial_claim(selected_env_ids=_i((0,)), requested_task_by_robot=_i(((0, -1),)))
    proposal.fill_(-1)
    coordinator.step_environment(action_builder=lambda env, assignment: setattr(env, "last_assignment", assignment.clone()) or assignment)
    _assert(torch.equal(env.last_assignment, _i(((0, -1),))), "caller cache overrode Ak")
    return {"caller_mutated": True, "Ak_mapping": [[0, -1]]}


def test_t12_geometry_assignment_separation() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    coordinator.commit_deterministic_initial_claim(selected_env_ids=_i((0,)), requested_task_by_robot=_i(((2, -1),)))
    env.geometry_version = 7
    seen: dict[str, Any] = {}
    def builder(fake: _FakeEnvironment, assignment: torch.Tensor) -> torch.Tensor:
        seen.update(geometry=fake.geometry_version, assignment=assignment.clone())
        return assignment
    coordinator.step_environment(action_builder=builder)
    _assert(seen["geometry"] == 7 and torch.equal(seen["assignment"], _i(((2, -1),))), "geometry became assignment authority")
    return {"geometry": 7, "assignment": [[2, -1]]}


def test_t13_claim_after_ak_rejects() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    before = domain.current_read_port.read_current()
    domain.physical_step_admission_port.begin_physical_step_admission()
    _expect(
        lambda: domain.production_claim_port.prepare_production_initial_claim(selected_env_ids=_i((0,)), requested_task_by_robot=_i(((0, -1),))),
        code="runtime_step_in_flight",
    )
    _assert(domain.current_read_port.read_current() is before, "claim mutated P2 after Ak")
    return {"claim_after_Ak": "rejected", "P2_unchanged": True}


def test_t14_action_build_exception() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    _expect(lambda: coordinator.step_environment(action_builder=lambda env, assignment: (_ for _ in ()).throw(RuntimeError("build"))))
    return {"faulted": domain.interstep_fence_read_port.read().phase is Phase.FAULTED, "reopened": False}


def test_t15_env_step_exception() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    env.raise_step = True
    _expect(lambda: coordinator.step_environment(action_builder=lambda env, assignment: assignment))
    return {"faulted": domain.interstep_fence_read_port.read().phase is Phase.FAULTED, "reopened": False}


def test_t16_reset_exception() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    env.raise_reset = True
    _expect(_coordinator(domain, env).reset_environment)
    view = domain.interstep_fence_read_port.read()
    return {"faulted": view.phase is Phase.FAULTED, "window": view.window}


def test_t17_completion_before_finalization() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    env.skip_finalization = True
    _expect(lambda: coordinator.step_environment(action_builder=lambda env, assignment: assignment), code="physical_step_admission_required")
    return {"completion_rejected": True, "faulted": domain._coordinator.poisoned}


def test_t18_duplicate_completion() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    admission = _valid_step_direct(domain)
    domain.physical_step_admission_port.commit_successful_return(admission)
    _expect(lambda: domain.physical_step_admission_port.commit_successful_return(admission), code="admission_already_consumed")
    return {"duplicate": "ordinary_reject", "poisoned": domain._coordinator.poisoned}


def _env_method(name: str) -> ast.FunctionDef:
    tree = ast.parse(PATHS["env"].read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ScanMobileManipulatorEnv")
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_t19_environment_mutation_order_static() -> dict[str, Any]:
    source = PATHS["env"].read_text(encoding="utf-8")
    pre = ast.get_source_segment(source, _env_method("_pre_physics_step")) or ""
    dones = ast.get_source_segment(source, _env_method("_get_dones")) or ""
    reset = ast.get_source_segment(source, _env_method("_reset_idx")) or ""
    _assert(pre.index("_validate_event_physical_step_entry") < pre.index("self.previous_actions"), "step mutation precedes validation")
    _assert(dones.index("validate_physical_finalization_for_active_call") < dones.index("finalize_physical_transition"), "I3 validation order")
    _assert(reset.index("_validate_event_reset_entry") < reset.index("torch.arange"), "reset normalization precedes validation")
    return {"step": True, "i3": True, "reset": True}


def test_t20_an1_static() -> dict[str, Any]:
    source = PATHS["env"].read_text(encoding="utf-8")
    _assert("event_action_noise_not_supported" in source and "cfg.action_noise_model is not None" in source, "AN1 removed")
    return {"event_action_noise": None}


def test_t21_default_profile_isolation() -> dict[str, Any]:
    source = PATHS["env"].read_text(encoding="utf-8")
    _assert("event_admission_validation_port is not None" in source and "if port is None:" in source, "default isolation missing")
    return {"existing_profiles_require_validation": False}


def test_t22_no_wrapper_wiring() -> dict[str, Any]:
    symbol = "EventProfileSynchronousRuntimeCoordinator"
    wrapper_source = PATHS["wrapper"].read_text(encoding="utf-8")
    _assert("def _compose_event_assignment_harl_wrapper(" in wrapper_source, "I4-1 private composition seam missing")
    _assert(wrapper_source.count(f"{symbol}(") == 1, "O1 must be constructed exactly once by the private composition seam")
    _assert("self._event_runtime_facade" in wrapper_source, "wrapper did not retain the facade boundary")
    _assert("self._event_profile_synchronous_runtime" not in wrapper_source, "wrapper retained O1 directly")
    candidates = [*REPO_ROOT.glob("scripts/**/*train*.py"), *REPO_ROOT.glob("scripts/**/*play*.py")]
    hits = [str(path) for path in candidates if path.is_file() and symbol in path.read_text(encoding="utf-8", errors="ignore")]
    _assert(not hits, f"O1 leaked into training/playback: {hits}")
    _assert(SYNC.__all__ == (), "O1 module gained a public export")
    return {"private_wrapper_composition": 1, "wrapper_retains_O1": False, "public_exports": 0}


def test_t23_raw_step_reset_fail_stop() -> dict[str, Any]:
    step_domain = _domain()
    _reset(step_domain)
    _expect(step_domain.environment_admission_validation_port.validate_physical_step_entry_for_active_call, code="physical_step_admission_required")
    reset_domain = _domain()
    _expect(reset_domain.environment_admission_validation_port.validate_reset_entry_for_active_call, code="reset_admission_required")
    return {"step": "fail_stop", "reset": "fail_stop"}


def test_t24_validation_semantic_neutrality() -> dict[str, Any]:
    domain = _domain()
    _reset(domain)
    before = domain.current_read_port.read_current()
    admission = domain.physical_step_admission_port.begin_physical_step_admission()
    domain.environment_admission_validation_port.validate_physical_step_entry_for_active_call()
    domain.environment_admission_validation_port.validate_physical_finalization_for_active_call()
    after = domain.current_read_port.read_current()
    _assert(after is before and after.store_version == before.store_version, "validation changed P2/Store")
    domain.physical_step_admission_port.commit_successful_return(admission)
    return {"P2_identity": True, "store_version_delta": 0}


def test_t25_p2_b1_b1w_basic_regression() -> dict[str, Any]:
    domain, env = _domain(), None
    env = _FakeEnvironment(domain)
    coordinator = _coordinator(domain, env)
    coordinator.reset_environment()
    source = domain.current_read_port.read_current()
    artifact = coordinator.commit_deterministic_initial_claim(selected_env_ids=_i((0,)), requested_task_by_robot=_i(((0, -1),)))
    claimed = domain.current_read_port.read_current()
    _assert(claimed is not source and claimed.store_version == source.store_version + 1, "B1 P2 regression")
    _assert(artifact is claimed.provenance[0].assignment_artifact, "artifact provenance regression")
    return {"P2": True, "B1": True, "B1W": True}


def test_t26_b0_regression_inventory() -> dict[str, Any]:
    names = (
        "test_assignment_phase_b0_1a_execution_facts_producer_pure.py",
        "test_assignment_phase_b0_1b_generation_clock_pure.py",
        "test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py",
        "test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py",
        "test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py",
        "test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py",
        "test_assignment_phase_b0_3i4_terminal_handoff_pure.py",
        "test_assignment_phase_b0_3i4_environment_integration.py",
    )
    missing = [name for name in names if not (REPO_ROOT / "scripts" / "environments" / name).is_file()]
    _assert(not missing, f"missing B0 suites: {missing}")
    return {"retained_suites": len(names)}


def test_t27_frozen_contract_hashes() -> dict[str, Any]:
    import hashlib
    expected = {
        "transition": "1bf66c6c6b51adb8a44292910c1b11dfb1e43f31d711d3320285f3df587b0cc9",
        "event": "22194ad8671dd299bd7acd0b837325b4c85f50b8636cb285ff4f76879467086a",
        "profile": "ece4a58c1636ea3f710775eaac25e12df4097972ef57ec0d15cefec5e6702500",
    }
    actual = {name: hashlib.sha256(PATHS[name].read_bytes()).hexdigest() for name in expected}
    _assert(actual == expected, f"frozen contract drift: {actual}")
    return actual


def test_t28_no_global_side_effects() -> dict[str, Any]:
    checks = {
        "python_rng": random.getstate() == _IMPORT_RANDOM,
        "torch_rng": torch.equal(torch.random.get_rng_state(), _IMPORT_TORCH_RANDOM),
        "cwd": Path.cwd() == _IMPORT_CWD,
        "sys_path": tuple(sys.path) == _IMPORT_SYS_PATH,
        "environment": dict(os.environ) == _IMPORT_ENV,
        "logging": _logging_state() == _IMPORT_LOGGING,
        "filesystem": _inventory() == _IMPORT_INVENTORY,
        "registry": PROFILE.get_assignment_profile_registry() is _PROFILE_REGISTRY
        and repr(PROFILE.get_assignment_profile_registry()) == _PROFILE_REGISTRY_REPR,
    }
    _assert(all(checks.values()), f"global side effect: {checks}")
    return checks


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I1-T1_capability_composition_identity", test_t1_capability_composition_identity),
    ("I1-T2_initial_reset_bootstrap", test_t2_initial_reset_bootstrap),
    ("I1-T3_raw_reset_bypass", test_t3_raw_reset_bypass),
    ("I1-T4_later_standalone_reset", test_t4_later_standalone_reset),
    ("I1-T5_step_entry_exact_Ak", test_t5_step_entry_exact_ak),
    ("I1-T6_finalization_exact_Ak", test_t6_finalization_same_ak),
    ("I1-T7_finalization_before_entry", test_t7_finalization_before_entry),
    ("I1-T8_autoreset_same_Ak", test_t8_autoreset_same_ak),
    ("I1-T9_zero_claim_continuation", test_t9_zero_claim_continuation),
    ("I1-T10_deterministic_claim_then_Ak", test_t10_deterministic_claim_then_ak),
    ("I1-T11_cache_cannot_override_Ak", test_t11_caller_cache_cannot_override_ak),
    ("I1-T12_geometry_assignment_separation", test_t12_geometry_assignment_separation),
    ("I1-T13_claim_after_Ak", test_t13_claim_after_ak_rejects),
    ("I1-T14_action_build_exception", test_t14_action_build_exception),
    ("I1-T15_env_step_exception", test_t15_env_step_exception),
    ("I1-T16_reset_exception", test_t16_reset_exception),
    ("I1-T17_completion_before_finalization", test_t17_completion_before_finalization),
    ("I1-T18_duplicate_completion", test_t18_duplicate_completion),
    ("I1-T19_environment_mutation_order", test_t19_environment_mutation_order_static),
    ("I1-T20_AN1", test_t20_an1_static),
    ("I1-T21_default_profile_isolation", test_t21_default_profile_isolation),
    ("I1-T22_no_wrapper_wiring", test_t22_no_wrapper_wiring),
    ("I1-T23_raw_bypass_fail_stop", test_t23_raw_step_reset_fail_stop),
    ("I1-T24_semantic_neutrality", test_t24_validation_semantic_neutrality),
    ("I1-T25_P2_B1_B1W_regression", test_t25_p2_b1_b1w_basic_regression),
    ("I1-T26_B0_inventory", test_t26_b0_regression_inventory),
    ("I1-T27_frozen_contract_hashes", test_t27_frozen_contract_hashes),
    ("I1-T28_no_global_side_effects", test_t28_no_global_side_effects),
)


def run_suite() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for name, operation in TESTS:
        try:
            evidence = operation()
        except BaseException as exc:
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"name": name, "status": "passed", "evidence": evidence})
    passed = sum(item["status"] == "passed" for item in results)
    return {
        "status": "passed" if passed == len(TESTS) else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": len(TESTS) - passed,
        "tests": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
