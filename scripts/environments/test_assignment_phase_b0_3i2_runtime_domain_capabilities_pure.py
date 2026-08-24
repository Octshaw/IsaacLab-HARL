"""Pure B0-3I2 dormant runtime-domain and capability-port regressions."""

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


def _spec(
    *,
    env_ids: tuple[int, ...] = (41000, 41001),
    num_robots: int = 2,
    num_tasks: int = 3,
) -> Any:
    return DOMAIN._EventProfileLifecycleDomainSpec(
        _event_profile(),
        device=DEVICE,
        env_ids=_i(env_ids),
        num_robots=num_robots,
        num_tasks=num_tasks,
    )


def _domain(**kwargs: Any) -> Any:
    return DOMAIN._EventProfileLifecycleRuntimeDomain(_spec(**kwargs))


def _canonical_reset_args(domain: Any, selected: tuple[int, ...]) -> dict[str, torch.Tensor]:
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
        "initial_ownership": torch.full(
            (rows, identity.num_tasks), -1, dtype=torch.int64
        ),
    }


def _rebuild(domain: Any, selected: tuple[int, ...]) -> Any:
    with domain.environment_port.episode_rebuild(
        **_canonical_reset_args(domain, selected)
    ) as rebuild:
        return rebuild.commit_physical_reset_complete()


def _state_tensors(view: Any) -> tuple[torch.Tensor, ...]:
    state = view.lifecycle_state
    return (
        state.task_state,
        state.robot_state,
        state.ownership,
        state.cumulative_failed_pairs,
        state.completion_count,
        state.termination_reason,
    )


def _same_view(left: Any, right: Any) -> bool:
    return (
        left.store_version == right.store_version
        and all(torch.equal(a, b) for a, b in zip(_state_tensors(left), _state_tensors(right), strict=True))
        and torch.equal(left.episode_generation, right.episode_generation)
        and torch.equal(left.transition_generation, right.transition_generation)
        and left.result is right.result
    )


def test_i2_t1_canonical_domain_construction() -> dict[str, Any]:
    profile = _event_profile()
    source_ids = _i((41100, 41101, 41102))
    spec = DOMAIN._EventProfileLifecycleDomainSpec(
        profile,
        device=DEVICE,
        env_ids=source_ids,
        num_robots=3,
        num_tasks=5,
    )
    source_ids.fill_(999)
    domain = DOMAIN._EventProfileLifecycleRuntimeDomain(spec)
    object.__setattr__(spec, "num_tasks", 99)
    identity = domain.identity
    view = domain.current_read_port.read_current()
    _assert(identity.profile is profile, "profile identity changed")
    _assert(identity.device == DEVICE and identity.num_envs == 3, "device/E mismatch")
    _assert(identity.num_robots == 3 and identity.num_tasks == 5, "M/N mismatch")
    _assert(tuple(identity.env_ids.tolist()) == (41100, 41101, 41102), "env alias leaked")
    accessor = identity.env_ids
    accessor.fill_(0)
    _assert(tuple(identity.env_ids.tolist()) == (41100, 41101, 41102), "identity accessor alias leaked")
    object.__setattr__(identity, "num_tasks", 77)
    _assert(domain.identity.num_tasks == 5, "issued identity record retargeted domain")
    _assert(tuple(view.episode_generation.tolist()) == (-1, -1, -1), "constructor bootstrapped episode")
    _assert(tuple(view.transition_generation.tolist()) == (-1, -1, -1), "constructor requested transition")
    _assert(view.store_version == 0 and view.result is None, "prebootstrap publication")
    _assert(not bool(view.terminated.any()) and not bool(view.truncated.any()), "prebootstrap done")
    for env_id in (41100, 41101, 41102):
        _assert(env_id not in B01._NEXT_TOKEN_BY_ENV, "constructor allocated facts token")
    ledger = domain._coordinator._ledger.snapshot()
    _assert(
        int(ledger["issued_receipt_count"]) == 0
        and ledger["consumed_tokens"] == ()
        and ledger["generation_tokens"] == (),
        "constructor consumed ledger",
    )
    return {"profile_exact": True, "domain": [3, 3, 5], "episode": -1, "transition": -1, "tokens": 0}


def test_i2_t2_exact_profile_domain_rejection() -> dict[str, Any]:
    def build(profile: Any, **kwargs: Any) -> Any:
        return DOMAIN._EventProfileLifecycleDomainSpec(
            profile,
            device=kwargs.pop("device", DEVICE),
            env_ids=kwargs.pop("env_ids", _i((41200,))),
            num_robots=kwargs.pop("num_robots", 2),
            num_tasks=kwargs.pop("num_tasks", 3),
        )

    raw = (
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        "event_gated_local_mrta",
        {"profile_name": "event_gated_local_mrta"},
        None,
        type("Lookalike", (), {"profile_name": "event_gated_local_mrta"})(),
    )
    for candidate in (*_existing_profiles(), *raw):
        _expect_error(PROFILE.AssignmentProfileRouteError, lambda candidate=candidate: build(candidate))
    event = _event_profile()
    invalid_specs = (
        lambda: build(event, env_ids=_i((41200, 41200))),
        lambda: build(event, env_ids=_i((-1,))),
        lambda: build(event, env_ids=_i(())),
        lambda: build(event, env_ids=_i((41200,), dtype=torch.int32)),
        lambda: build(event, env_ids=_i([[41200]])),
        lambda: build(event, device=torch.device("meta"), env_ids=_i((41200,))),
        lambda: build(event, num_robots=0),
        lambda: build(event, num_tasks=-1),
        lambda: build(event, num_robots=True),
    )
    for operation in invalid_specs:
        _expect_error(DOMAIN._EventProfileLifecycleDomainRuntimeError, operation)
    _expect_error(DOMAIN._EventProfileLifecycleDomainRuntimeError, lambda: DOMAIN._EventProfileLifecycleRuntimeDomain(object()), code="spec_type")
    return {"existing_profiles_rejected": 4, "raw_rejected": len(raw), "domain_failures": len(invalid_specs) + 1}


def test_i2_t3_retained_lifetime_across_rebuild() -> dict[str, Any]:
    domain = _domain(env_ids=(41300,), num_robots=2, num_tasks=2)
    observed: list[tuple[int, int, int]] = []
    for expected_episode in (0, 1, 2):
        view = _rebuild(domain, (41300,))
        observed.append((view.store_version, int(view.episode_generation[0]), int(view.transition_generation[0])))
        _assert(observed[-1] == (expected_episode + 1, expected_episode, -1), "lifetime continuity")
    _assert(domain.environment_port is domain.environment_port, "environment port reconstructed")
    _assert(domain.current_read_port is domain.current_read_port, "read port reconstructed")
    return {"observable_sequence": observed, "transition_preserved": -1, "same_ports": True}


def test_i2_t4_environment_port_delegation() -> dict[str, Any]:
    port_domain = _domain(env_ids=(41400,), num_robots=2, num_tasks=2)
    direct_domain = _domain(env_ids=(41400,), num_robots=2, num_tasks=2)
    port_view = _rebuild(port_domain, (41400,))
    direct_inputs = B02._EpisodeRebuildInputs(
        direct_domain.identity.profile,
        device=DEVICE,
        **_canonical_reset_args(direct_domain, (41400,)),
    )
    with direct_domain._coordinator._episode_rebuild(direct_inputs) as direct_rebuild:
        direct_view = direct_rebuild.commit_physical_reset_complete()
    _assert(_same_view(port_view, direct_view), "port changed I1 semantics")
    _assert(port_view.store_version == 1 and port_view.result is None, "delegated view")
    return {"direct_i1_oracle_equal": True, "version_delta": 1, "episode": 0, "transition": -1}


def test_i2_t5_partial_rebuild_through_port() -> dict[str, Any]:
    domain = _domain(env_ids=(41500, 41501, 41502), num_robots=2, num_tasks=2)
    first = _rebuild(domain, (41500, 41501, 41502))
    second = _rebuild(domain, (41501,))
    _assert(second.store_version == first.store_version + 1, "partial version")
    _assert(tuple(second.episode_generation.tolist()) == (0, 1, 0), "partial episode")
    _assert(tuple(second.transition_generation.tolist()) == (-1, -1, -1), "transition changed")
    for before, after in zip(_state_tensors(first), _state_tensors(second), strict=True):
        _assert(torch.equal(before[[0, 2]], after[[0, 2]]), "unselected lifecycle row changed")
    return {"selected": [41501], "unselected_bit_exact": True, "global_version_delta": 1}


def test_i2_t6_current_read_capability() -> dict[str, Any]:
    domain = _domain(env_ids=(41600,), num_robots=2, num_tasks=2)
    view = _rebuild(domain, (41600,))
    read = domain.current_read_port.read_current()
    _assert(read is view, "read port did not reuse coordinator publication")
    episode_copy = read.episode_generation
    task_copy = read.lifecycle_state.task_state
    episode_copy.fill_(99)
    task_copy.fill_(int(TaskState.COMPLETED))
    reread = domain.current_read_port.read_current()
    _assert(tuple(reread.episode_generation.tolist()) == (0,), "generation alias leaked")
    _assert(bool((reread.lifecycle_state.task_state == int(TaskState.AVAILABLE)).all()), "state alias leaked")
    _expect_error(FrozenInstanceError, lambda: setattr(domain.current_read_port, "_domain", object()))
    return {"coordinator_publication_reused": True, "generation_no_alias": True, "state_no_alias": True, "port_frozen": True}


def _supported_surface(cls: type[Any]) -> tuple[str, ...]:
    methods = tuple(
        name
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    )
    properties = tuple(
        name for name, member in vars(cls).items() if isinstance(member, property)
    )
    return tuple(sorted((*methods, *properties)))


def test_i2_t7_capability_surface_isolation() -> dict[str, Any]:
    env_surface = _supported_surface(DOMAIN._EventProfileLifecycleEnvironmentPort)
    read_surface = _supported_surface(DOMAIN._EventProfileLifecycleCurrentReadPort)
    claim_surface = _supported_surface(DOMAIN._EventProfileInitialClaimPort)
    context_surface = _supported_surface(DOMAIN._EnvironmentEpisodeRebuildContext)
    domain_surface = _supported_surface(DOMAIN._EventProfileLifecycleRuntimeDomain)
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
    _assert(read_surface == ("domain_identity", "read_current"), f"read surface {read_surface}")
    _assert(context_surface == ("commit_physical_reset_complete",), f"context surface {context_surface}")
    _assert(claim_surface == ("commit_initial_claim", "prepare_initial_claim"), f"claim surface {claim_surface}")
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
    forbidden = (
        "clock", "store", "ledger", "authority", "coordinator", "producer",
        "receipt", "writer_capability", "get_clock", "get_store", "components",
        "debug_components", "advance_episode", "commit_transition",
        "request_transition_candidate", "install_publication",
    )
    for surface in (env_surface, read_surface, claim_surface, context_surface, domain_surface):
        _assert(not set(surface).intersection(forbidden), f"capability leaked {surface}")
    _assert(tuple(DOMAIN.__all__) == (), "private domain module exported symbols")
    return {"environment": list(env_surface), "read": list(read_surface), "claim": list(claim_surface), "context": list(context_surface), "domain": list(domain_surface), "raw_authority_leak": False}


def test_i2_t8_terminal_extension_is_capability_separated() -> dict[str, Any]:
    env_surface = _supported_surface(DOMAIN._EventProfileLifecycleEnvironmentPort)
    observer_surface = _supported_surface(DOMAIN._EventProfileTerminalObserverPort)
    consumer_surface = _supported_surface(DOMAIN._EventProfileTerminalConsumerPort)
    _assert("read_terminal" not in env_surface and "acknowledge_terminal" not in env_surface, "environment gained terminal read/ack")
    _assert(observer_surface == ("read_terminal",), f"observer surface {observer_surface}")
    _assert(
        consumer_surface
        == (
            "acknowledge_terminal",
            "acknowledge_terminal_batch",
            "capture_pending_terminal_artifacts",
            "domain_identity",
            "read_terminal",
        ),
        f"consumer surface {consumer_surface}",
    )
    return {"environment_read_ack": False, "observer": list(observer_surface), "consumer": list(consumer_surface)}


def test_i2_t9_no_raw_transition_capability() -> dict[str, Any]:
    env_surface = _supported_surface(DOMAIN._EventProfileLifecycleEnvironmentPort)
    source = inspect.getsource(DOMAIN._EventProfileLifecycleEnvironmentPort)
    forbidden = (
        "reserve_transition_context", "build_facts", "raw_scan",
        "owner_qualified_completion", "get_prestate", "read_clock",
        "commit_generation", "transition_contexts",
    )
    for symbol in forbidden:
        _assert(
            symbol not in source and symbol not in env_surface,
            f"raw transition capability leaked: {symbol}",
        )
    return {
        "environment_surface": list(env_surface),
        "staged_finalize_only": True,
        "forbidden_symbols": len(forbidden),
    }


def test_i2_t10_poison_propagation() -> dict[str, Any]:
    domain = _domain(env_ids=(42000,), num_robots=2, num_tasks=1)
    direct_inputs = B02._EpisodeRebuildInputs(
        domain.identity.profile,
        device=DEVICE,
        **_canonical_reset_args(domain, (42000,)),
    )
    control = B02._EpisodeRebuildTestControl(fail_clock_advance=True)
    try:
        with domain._coordinator._episode_rebuild(direct_inputs, _test_control=control) as rebuild:
            rebuild.commit_physical_reset_complete()
    except B02.LifecycleEpisodeRebuildRuntimeError:
        pass
    else:
        raise AssertionError("expected controlled I1 poison")
    _expect_error(B02.LifecycleCoordinatorRuntimeError, domain.current_read_port.read_current, code="coordinator_poisoned")
    context = domain.environment_port.episode_rebuild(**_canonical_reset_args(domain, (42000,)))
    _expect_error(B02.LifecycleCoordinatorRuntimeError, context.__enter__, code="coordinator_poisoned")
    _assert(domain._coordinator.poisoned, "coordinator poison absent")
    return {"single_poison_authority": "coordinator", "read_rejected": True, "rebuild_rejected": True}


def test_i2_t11_no_authority_use_during_rebuild() -> dict[str, Any]:
    domain = _domain(env_ids=(42100, 42101), num_robots=2, num_tasks=2)
    ledger_before = dict(domain._coordinator._ledger.snapshot())
    token_before = {env: B01._NEXT_TOKEN_BY_ENV.get(env) for env in (42100, 42101)}
    view_before = domain.current_read_port.read_current()
    view = _rebuild(domain, (42100, 42101))
    ledger_after = dict(domain._coordinator._ledger.snapshot())
    token_after = {env: B01._NEXT_TOKEN_BY_ENV.get(env) for env in (42100, 42101)}
    _assert(ledger_before == ledger_after, "rebuild used ledger")
    _assert(token_before == token_after, "rebuild allocated facts token")
    _assert(view.result is None, "rebuild fabricated result")
    _assert(torch.equal(view.transition_generation, view_before.transition_generation), "transition advanced")
    return {"ledger_unchanged": True, "facts_tokens_unchanged": True, "result": None, "transition_unchanged": True}


def _logger_state() -> tuple[Any, ...]:
    root = logging.getLogger()
    return (root.level, tuple(root.handlers), tuple(root.filters), root.disabled)


def _file_inventory() -> tuple[str, ...]:
    return tuple(sorted(str(path.relative_to(REPO_ROOT)) for path in REPO_ROOT.rglob("*") if path.is_file()))


def test_i2_t12_default_off_global_side_effects() -> dict[str, Any]:
    python_rng = random.getstate()
    torch_rng = torch.random.get_rng_state().clone()
    logger_state = _logger_state()
    files = _file_inventory()
    cwd = Path.cwd()
    environment = dict(os.environ)
    sys_path = tuple(sys.path)
    domain = _domain(env_ids=(42200,), num_robots=2, num_tasks=2)
    _rebuild(domain, (42200,))
    _assert(domain.current_read_port.read_current().result is None, "default-off read")
    event = domain.identity.profile
    _expect_error(
        PROFILE.PhaseAExecutionNotAuthorizedError,
        lambda: PROFILE.require_assignment_profile_runtime_ready(
            event,
            consumer="B0-3I2 dormant domain test",
            entrypoint="standalone pure test",
            current_phase="B0-3I2",
            barrier="production composition remains unauthorized",
        ),
    )
    entry_paths = (
        SCAN_SOURCE / "scan_mobile_manipulator_env.py",
        SCAN_SOURCE / "assignment_harl_wrapper.py",
        SCAN_SOURCE / "assignment_lifecycle_resolver_runtime.py",
        SCAN_SOURCE / "assignment_controller.py",
        SCAN_SOURCE / "__init__.py",
    )
    hits = []
    for path in entry_paths:
        source = path.read_text(encoding="utf-8")
        if "assignment_event_profile_runtime_domain" in source or "_EventProfileLifecycleRuntimeDomain" in source:
            hits.append(path.name)
    _assert(
        hits == ["scan_mobile_manipulator_env.py", "assignment_harl_wrapper.py"],
        f"unexpected I4 wiring {hits}",
    )
    wrapper_source = (SCAN_SOURCE / "assignment_harl_wrapper.py").read_text(encoding="utf-8")
    _assert(
        "def _compose_event_assignment_harl_wrapper(" in wrapper_source,
        "authorized I4-1 private composition seam missing",
    )
    _assert(
        "_compose_event_assignment_harl_wrapper" not in (SCAN_SOURCE / "__init__.py").read_text(encoding="utf-8"),
        "I4-1 composition seam became a public package export",
    )
    blocked = sorted(name for name in sys.modules if name == "isaaclab" or name.startswith(("isaaclab.", "omni", "pxr", "harl")))
    _assert(blocked == [], f"heavy modules imported {blocked}")
    _assert(random.getstate() == python_rng, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), torch_rng), "Torch RNG changed")
    _assert(_logger_state() == logger_state, "logger changed")
    _assert(_file_inventory() == files, "filesystem changed")
    _assert(Path.cwd() == cwd and dict(os.environ) == environment and tuple(sys.path) == sys_path, "process globals changed")
    return {
        "production_wiring": "event environment plus private I4-1 wrapper composition",
        "runtime_readiness": event.runtime_readiness.value,
        "heavy_modules": blocked,
        "global_side_effects": "none",
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I2-T1_canonical_domain_construction", test_i2_t1_canonical_domain_construction),
    ("I2-T2_exact_profile_domain_rejection", test_i2_t2_exact_profile_domain_rejection),
    ("I2-T3_retained_lifetime_across_rebuild", test_i2_t3_retained_lifetime_across_rebuild),
    ("I2-T4_environment_port_delegation", test_i2_t4_environment_port_delegation),
    ("I2-T5_partial_rebuild_through_port", test_i2_t5_partial_rebuild_through_port),
    ("I2-T6_current_read_capability", test_i2_t6_current_read_capability),
    ("I2-T7_capability_surface_isolation", test_i2_t7_capability_surface_isolation),
    ("I2-T8_terminal_extension_is_capability_separated", test_i2_t8_terminal_extension_is_capability_separated),
    ("I2-T9_no_raw_transition_capability", test_i2_t9_no_raw_transition_capability),
    ("I2-T10_poison_propagation", test_i2_t10_poison_propagation),
    ("I2-T11_no_authority_use_during_rebuild", test_i2_t11_no_authority_use_during_rebuild),
    ("I2-T12_default_off_global_side_effects", test_i2_t12_default_off_global_side_effects),
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
        "evidence": {"groups": "I2-T1..I2-T12", "domain": "pure_dormant_retained", "ports": ["episode_rebuild", "finalize_physical_transition", "read_current"]},
        "runtime_boundary": {"production_wiring": "event environment only", "I3": "narrow_staged_adapter", "I4": "terminal_environment_integration", "isaac_applauncher": "not_imported", "training_playback_evaluation": "not_run"},
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
