"""Pure/static Phase A1c resolved-profile production-wiring regressions.

This suite never imports a formal entrypoint, AppLauncher, Isaac Lab, HARL,
torch, checkpoint code, or the assignment wrapper/training runtime.  It loads
the pure identity and scenario modules with bounded file-based harnesses, then
uses AST/source evidence for production ordering and same-object propagation.
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
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
CONTRACT_PATH = TASK_SOURCE / "assignment_profile_contract.py"
SCENARIO_PATH = TASK_SOURCE / "scenario_config.py"
WRAPPER_PATH = TASK_SOURCE / "assignment_harl_wrapper.py"
TRAINING_CONTRACT_PATH = TASK_SOURCE / "assignment_lifecycle_training_contract.py"
TRAINING_PATH = TASK_SOURCE / "assignment_harl_training.py"
ENTRYPOINT_PATHS = {
    "train": REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py",
    "play": REPO_ROOT
    / "scripts"
    / "reinforcement_learning"
    / "harl"
    / "play_assignment.py",
    "rl_diagnostics": REPO_ROOT
    / "scripts"
    / "environments"
    / "evaluate_assignment_rl_playback_diagnostics.py",
    "methods": REPO_ROOT
    / "scripts"
    / "environments"
    / "evaluate_assignment_methods.py",
    "controller_diagnosis": REPO_ROOT
    / "scripts"
    / "environments"
    / "diagnose_assignment_controller_feasibility.py",
}
CANONICAL_CONTRACT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
)
FORMAL_ENTRYPOINTS = tuple(ENTRYPOINT_PATHS)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_type: type[BaseException] | tuple[type[BaseException], ...],
    *expected_text: str,
) -> BaseException:
    try:
        function()
    except exception_type as exc:
        rendered = str(exc)
        for text in expected_text:
            _assert(text in rendered, f"expected {text!r} in {rendered!r}")
        return exc
    except Exception as exc:
        raise AssertionError(
            f"expected {exception_type!r}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exception_type!r}")


def _load_contract() -> ModuleType:
    existing = sys.modules.get(CANONICAL_CONTRACT_MODULE)
    if existing is not None:
        _assert(
            Path(str(existing.__file__)).resolve() == CONTRACT_PATH.resolve(),
            "canonical contract key points to another source",
        )
        return existing
    spec = importlib.util.spec_from_file_location(
        CANONICAL_CONTRACT_MODULE,
        CONTRACT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not build canonical profile-contract spec")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[CANONICAL_CONTRACT_MODULE] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(CANONICAL_CONTRACT_MODULE, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


def _load_scenario() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "phase_a1c_scenario_config_harness",
        SCENARIO_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not build scenario-config spec")
    module = importlib.util.module_from_spec(spec)
    inserted = False
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        if str(TASK_SOURCE) not in sys.path:
            sys.path.insert(0, str(TASK_SOURCE))
            inserted = True
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(str(TASK_SOURCE))
        sys.dont_write_bytecode = previous
    return module


CONTRACT = _load_contract()
SCENARIO = _load_scenario()


def _load_training_contract() -> ModuleType:
    module_name = (
        "isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_lifecycle_training_contract"
    )
    package_paths = (
        ("isaaclab_tasks", TASK_SOURCE.parents[2]),
        ("isaaclab_tasks.direct", TASK_SOURCE.parent),
        ("isaaclab_tasks.direct.scan_mobile_manipulator", TASK_SOURCE),
    )
    for package_name, package_path in package_paths:
        if package_name in sys.modules:
            continue
        package = ModuleType(package_name)
        package.__path__ = [str(package_path)]  # type: ignore[attr-defined]
        package.__package__ = package_name
        sys.modules[package_name] = package
    spec = importlib.util.spec_from_file_location(
        module_name,
        TRAINING_CONTRACT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not build lifecycle-training-contract spec")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[module_name] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


TRAINING_CONTRACT = _load_training_contract()


def _origin(name: str):
    return CONTRACT.AssignmentProfileResolutionOrigin(name)


def _resolve(name: str, origin: str = "formal_entrypoint"):
    return CONTRACT.resolve_assignment_profile(name, _origin(origin))


def _authority(
    raw: str | None,
    resolved,
    *,
    origin: str,
    present: bool = True,
    allow_direct: bool = False,
    consumer: str = "test-consumer",
):
    return CONTRACT.resolve_or_validate_assignment_profile_authority(
        raw_profile=raw,
        raw_profile_present=present,
        resolved_assignment_profile=resolved,
        expected_origin=_origin(origin),
        allow_direct_fallback=allow_direct,
        consumer=consumer,
        entrypoint="test-entrypoint",
    )


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _call_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and _call_name(child) == name
    ]


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    _assert(len(matches) == 1, f"expected one function {name!r}, got {len(matches)}")
    return matches[0]


def _class_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    _assert(len(classes) == 1, f"class {class_name!r} is ambiguous")
    methods = [
        node
        for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    ]
    _assert(len(methods) == 1, f"{class_name}.{method_name} is ambiguous")
    return methods[0]


def _first_call_line(node: ast.AST, name: str) -> int:
    matches = _calls(node, name)
    _assert(matches, f"missing call {name!r}")
    return min(call.lineno for call in matches)


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _attribute_chain(node: ast.AST | None) -> tuple[str, ...]:
    result: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        result.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        result.append(current.id)
    return tuple(reversed(result))


def test_authority_and_mismatch_matrix() -> dict[str, Any]:
    formal = "formal_entrypoint"
    direct = "direct_wrapper_fallback"
    legacy = _resolve("legacy", formal)
    contract_c = _resolve("lifecycle_contract_c", formal)
    event = _resolve("event_gated_local_mrta", formal)

    _assert(_authority("legacy", legacy, origin=formal) is legacy, "legacy copy/rebuild")
    _assert(
        _authority("lifecycle_contract_c", contract_c, origin=formal) is contract_c,
        "Contract C copy/rebuild",
    )
    _assert(
        _authority(None, legacy, origin=formal, present=False) is legacy,
        "missing raw must explicitly mean current legacy default",
    )
    _expect_error(
        lambda: _authority("legacy", None, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "missing resolved assignment profile",
        "formal_entrypoint",
        "test-entrypoint",
        "assignment_resolved_profile_v1",
    )
    _expect_error(
        lambda: _authority("legacy", contract_c, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "raw assignment profile differs",
    )
    _expect_error(
        lambda: _authority("event_gated_local_mrta", legacy, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "raw assignment profile differs",
    )
    _expect_error(
        lambda: _authority("legacy", event, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "raw assignment profile differs",
    )
    direct_legacy = _resolve("legacy", direct)
    _expect_error(
        lambda: _authority("legacy", direct_legacy, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "origin differs",
    )
    _expect_error(
        lambda: _authority("legacy", legacy, origin=direct, allow_direct=True),
        CONTRACT.ResolvedProfileMismatchError,
        "origin differs",
    )
    foreign = SimpleNamespace(
        profile_name=legacy.profile_name,
        resolution_origin=legacy.resolution_origin,
    )
    _expect_error(
        lambda: _authority("legacy", foreign, origin=formal),
        CONTRACT.ResolvedProfileMismatchError,
        "noncanonical class/module identity",
    )
    _expect_error(
        lambda: CONTRACT.require_assignment_profile_runtime_ready(
            event,
            consumer="event-consumer",
            entrypoint="event-entrypoint",
            barrier="pre-runtime",
        ),
        CONTRACT.PhaseAExecutionNotAuthorizedError,
        "event_gated_local_mrta",
        "event_gated_phase_a_interface_only_v1",
        "interface_only",
        "Phase A1c",
        "event-consumer",
        "pre-runtime",
    )
    return {
        "matching_existing": 2,
        "missing_raw_legacy": "pass",
        "formal_missing": "typed-fail",
        "raw_object_mismatches": 3,
        "origin_mismatches": 2,
        "foreign_class": "typed-fail",
        "matching_event": "readiness-fail",
    }


def test_direct_fallback_exactly_once() -> dict[str, Any]:
    original = CONTRACT.resolve_assignment_profile
    calls: list[tuple[Any, Any]] = []

    def spy(profile, origin):
        calls.append((profile, origin))
        return original(profile, origin)

    CONTRACT.resolve_assignment_profile = spy
    try:
        direct_legacy = _authority(
            "legacy",
            None,
            origin="direct_wrapper_fallback",
            allow_direct=True,
            consumer="direct-wrapper",
        )
        _assert(len(calls) == 1, f"direct fallback resolve count={len(calls)}")
        _assert(
            direct_legacy.resolution_origin
            is CONTRACT.AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK,
            "direct fallback origin changed",
        )
        same = _authority(
            "legacy",
            direct_legacy,
            origin="direct_wrapper_fallback",
            allow_direct=True,
            consumer="wrapper-after-factory",
        )
        _assert(same is direct_legacy, "factory-to-wrapper object was reconstructed")
        _assert(len(calls) == 1, "supplied direct identity resolved again")

        before = len(calls)
        _expect_error(
            lambda: _authority("legacy", None, origin="formal_entrypoint"),
            CONTRACT.ResolvedProfileMismatchError,
            "missing resolved assignment profile",
        )
        _assert(len(calls) == before, "formal missing identity used fallback")

        direct_event = _authority(
            "event_gated_local_mrta",
            None,
            origin="direct_wrapper_fallback",
            allow_direct=True,
            consumer="direct-wrapper",
        )
        _assert(len(calls) == before + 1, "direct event did not resolve exactly once")
        _expect_error(
            lambda: CONTRACT.require_assignment_profile_runtime_ready(
                direct_event,
                consumer="direct-wrapper",
                entrypoint="direct-test",
                barrier="before wrapper branches",
            ),
            CONTRACT.PhaseAExecutionNotAuthorizedError,
            "event_gated_local_mrta",
        )
    finally:
        CONTRACT.resolve_assignment_profile = original
    return {
        "existing_resolve_count": 1,
        "factory_wrapper_total_resolve_count": 1,
        "formal_missing_resolve_count": 0,
        "event_direct_resolve_count": 1,
        "event_direct_runtime": "blocked",
    }


def _contract_c_cfg(raw_resolver: object = "ABSENT") -> SimpleNamespace:
    values: dict[str, Any] = {
        "assignment_lifecycle_profile": "lifecycle_contract_c",
        "assignment_cooldown_enabled": True,
        "assignment_cooldown_trigger_mode": "budget",
        "assignment_cooldown_duration_steps": 5,
        "assignment_cooldown_apply_to_action_mask": False,
        "assignment_redirect_guardrail_enabled": False,
        "assignment_failed_pair_memory_enabled": False,
    }
    if raw_resolver != "ABSENT":
        values["assignment_lifecycle_resolver_enabled"] = raw_resolver
    return SimpleNamespace(**values)


def test_primitive_preflight_finalize_and_contract_c() -> dict[str, Any]:
    preflight = SCENARIO.preflight_assignment_lifecycle_profile_runtime_primitive
    _assert(
        preflight(
            "legacy",
            raw_profile_present=True,
            hydra_overrides=[],
            entrypoint="preflight-test",
        )
        == "legacy",
        "existing preflight changed",
    )
    _expect_error(
        lambda: preflight(
            "event_gated_local_mrta",
            raw_profile_present=True,
            hydra_overrides=[],
            entrypoint="preflight-test",
        ),
        RuntimeError,
        "ASSIGNMENT_EVENT_PROFILE_PRELAUNCH_BLOCKED",
        "AppLauncher_constructed=False",
    )
    _expect_error(
        lambda: preflight(
            None,
            raw_profile_present=False,
            hydra_overrides=[
                "env.assignment_lifecycle_profile=event_gated_local_mrta"
            ],
            entrypoint="hydra-test",
        ),
        RuntimeError,
        "ASSIGNMENT_EVENT_PROFILE_PRELAUNCH_BLOCKED",
        "hydra-test",
    )
    _expect_error(
        lambda: preflight(
            "legacy",
            raw_profile_present=True,
            hydra_overrides=[
                "env.assignment_lifecycle_profile=lifecycle_contract_c"
            ],
            entrypoint="conflict-test",
        ),
        ValueError,
        "ASSIGNMENT_RUNTIME_PROFILE_CONFLICT",
    )

    finalize = SCENARIO.finalize_assignment_lifecycle_profile_runtime_primitive
    legacy_cfg = SimpleNamespace(assignment_lifecycle_resolver_enabled=False)
    _assert(
        finalize(
            legacy_cfg,
            declaration_settings=None,
            entrypoint="finalize-test",
        )
        == "legacy",
        "absent profile did not preserve legacy default",
    )

    resolver_results: dict[str, bool] = {}
    for label, raw in (("absent", "ABSENT"), ("false", False), ("true", True)):
        cfg = _contract_c_cfg(raw)
        profile = finalize(
            cfg,
            declaration_settings=None,
            entrypoint=f"contract-c-{label}",
        )
        _assert(profile == "lifecycle_contract_c", "Contract C finalization changed")
        resolved = _resolve(profile)
        resolver_results[label] = bool(
            resolved.to_legacy_wrapper_mapping()["resolver_enabled"]
        )
    _assert(
        resolver_results == {"absent": True, "false": True, "true": True},
        f"Contract C raw/effective resolver drift: {resolver_results}",
    )
    return {
        "visible_event": "prelaunch-blocked",
        "raw_hydra_event": "prelaunch-blocked",
        "source_conflict": "blocked",
        "absent_default": "legacy",
        "contract_c_effective_resolver": resolver_results,
    }


def test_same_object_authority_chain() -> dict[str, Any]:
    entrypoint_object = _resolve("lifecycle_contract_c")
    runner_object = _authority(
        "lifecycle_contract_c",
        entrypoint_object,
        origin="formal_entrypoint",
        consumer="runner",
    )
    facade_object = _authority(
        "lifecycle_contract_c",
        runner_object,
        origin="formal_entrypoint",
        consumer="env-facade",
    )
    wrapper_object = _authority(
        "lifecycle_contract_c",
        facade_object,
        origin="formal_entrypoint",
        consumer="wrapper",
    )
    _assert(
        entrypoint_object is runner_object is facade_object is wrapper_object,
        "pure authority chain lost object identity",
    )
    _assert(
        type(wrapper_object) is CONTRACT.ResolvedExistingAssignmentProfile,
        "same-object chain lost canonical class identity",
    )
    _assert(
        type(wrapper_object).__module__ == CANONICAL_CONTRACT_MODULE,
        "same-object chain lost canonical module identity",
    )
    return {
        "entrypoint_is_runner_is_facade_is_wrapper": True,
        "origin": wrapper_object.resolution_origin.value,
        "canonical_module": type(wrapper_object).__module__,
        "evidence_boundary": "pure helper chain plus production AST; no Isaac runtime",
    }


def test_training_contract_resolved_identity_routes() -> dict[str, Any]:
    expected_modes = {
        "legacy": "existing_legacy_behavior",
        "lifecycle_ablation": "not_training_enabled",
        "lifecycle_contract_c": "feed_forward",
        "diagnostics_hidden_state": "diagnostics_only",
    }
    modes: dict[str, str] = {}
    for profile_name, expected_mode in expected_modes.items():
        resolved = _resolve(profile_name)
        contract = TRAINING_CONTRACT.policy_sequence_contract_for_profile(resolved)
        modes[profile_name] = str(contract["policy_sequence_mode"])
        _assert(modes[profile_name] == expected_mode, f"{profile_name} mode drift")

    algo_args = {
        "model": {
            "use_recurrent_policy": False,
            "use_naive_recurrent_policy": False,
        },
        "algo": {"share_param": False},
        "train": {"save_entire_model": False},
    }
    env_args = {"algorithm": "happo", "state_type": "EP"}
    contract_c = TRAINING_CONTRACT.validate_assignment_lifecycle_policy_sequence(
        resolved_assignment_profile=_resolve("lifecycle_contract_c"),
        algo_args=algo_args,
        env_args=env_args,
    )
    _assert(
        contract_c["supported_actor_buffer_generator"]
        == "feed_forward_generator_actor",
        "Contract C feed-forward route drift",
    )
    _expect_error(
        lambda: TRAINING_CONTRACT.validate_assignment_lifecycle_policy_sequence(
            resolved_assignment_profile=_resolve("lifecycle_ablation"),
            algo_args=algo_args,
            env_args=env_args,
        ),
        RuntimeError,
        "not enabled for normal training",
    )
    _expect_error(
        lambda: TRAINING_CONTRACT.validate_assignment_lifecycle_policy_sequence(
            resolved_assignment_profile=_resolve("diagnostics_hidden_state"),
            algo_args=algo_args,
            env_args=env_args,
        ),
        RuntimeError,
        "not training-ready",
    )
    _expect_error(
        lambda: TRAINING_CONTRACT.validate_assignment_lifecycle_policy_sequence(
            resolved_assignment_profile=_resolve("event_gated_local_mrta"),
            algo_args=algo_args,
            env_args=env_args,
        ),
        CONTRACT.PhaseAExecutionNotAuthorizedError,
        "event-gated assignment runtime is not authorized",
    )
    return {
        "existing_policy_modes": modes,
        "contract_c_training": "HAPPO/EP/nonshared/feed-forward/state-dict pass",
        "ablation_training": "blocked",
        "diagnostics_training": "blocked",
        "event_training": "Phase-A typed blocked",
    }


def test_entrypoint_ordering_and_formal_resolution_inventory() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    side_effect_calls = {
        "train": "register_assignment_harl_runner",
        "play": "make_assignment_harl_env",
        "rl_diagnostics": "make_assignment_harl_env",
        "methods": "_set_global_seeds",
        "controller_diagnosis": "make_assignment_harl_env",
    }
    for label, path in ENTRYPOINT_PATHS.items():
        source = _source(path)
        tree = _tree(path)
        preflight_index = source.index(
            "preflight_assignment_lifecycle_profile_runtime_primitive("
        )
        launcher_index = source.index("app_launcher = AppLauncher(")
        _assert(
            preflight_index < launcher_index,
            f"{label} primitive preflight occurs after AppLauncher construction",
        )
        bootstrap_index = source.index("import isaaclab_tasks")
        canonical_import_index = source.index(
            "assignment_profile_contract import"
        )
        _assert(
            launcher_index < bootstrap_index < canonical_import_index,
            f"{label} canonical import crossed the bootstrap boundary",
        )
        _assert(
            "assignment_profile_contract import"
            not in source[:launcher_index],
            f"{label} imports canonical contract prelaunch",
        )

        resolve_calls = _calls(tree, "resolve_assignment_profile")
        _assert(
            len(resolve_calls) == 1,
            f"{label} formal final resolve count={len(resolve_calls)}",
        )
        main = _function(tree, "main")
        finalize_line = _first_call_line(
            main,
            "finalize_assignment_lifecycle_profile_runtime_primitive",
        )
        resolve_line = _first_call_line(main, "resolve_assignment_profile")
        readiness_line = _first_call_line(
            main,
            "require_assignment_profile_runtime_ready",
        )
        side_effect_line = _first_call_line(main, side_effect_calls[label])
        _assert(
            finalize_line < resolve_line < readiness_line < side_effect_line,
            f"{label} post-compose authority/readiness ordering changed",
        )
        resolution_call = resolve_calls[0]
        _assert(
            any(
                _attribute_chain(argument)
                == (
                    "AssignmentProfileResolutionOrigin",
                    "FORMAL_ENTRYPOINT",
                )
                for argument in resolution_call.args
            ),
            f"{label} final resolution does not use FORMAL_ENTRYPOINT",
        )
        evidence[label] = {
            "formal_resolve_count": 1,
            "preflight_before_app_launcher": True,
            "canonical_import_post_bootstrap": True,
            "finalize_resolve_guard_before_side_effect": True,
        }
    return evidence


def test_core_barriers_and_same_object_ast() -> dict[str, Any]:
    wrapper_tree = _tree(WRAPPER_PATH)
    wrapper_init = _class_method(wrapper_tree, "AssignmentHarlWrapper", "__init__")
    _assert(
        _first_call_line(
            wrapper_init,
            "resolve_or_validate_assignment_profile_authority",
        )
        < _first_call_line(wrapper_init, "_initial_agents"),
        "wrapper authority is after wrapper branch/state initialization",
    )
    wrapper_factory = _function(wrapper_tree, "make_assignment_harl_env")
    _assert(
        _first_call_line(
            wrapper_factory,
            "resolve_or_validate_assignment_profile_authority",
        )
        < _first_call_line(wrapper_factory, "make"),
        "wrapper factory authority is after gymnasium.make",
    )
    factory_wrapper_calls = _calls(wrapper_factory, "AssignmentHarlWrapper")
    _assert(len(factory_wrapper_calls) == 1, "factory wrapper call is ambiguous")
    _assert(
        _attribute_chain(
            _keyword(factory_wrapper_calls[0], "resolved_assignment_profile")
        )
        == ("authoritative_profile",),
        "factory does not pass its exact authority object to wrapper",
    )

    training_tree = _tree(TRAINING_PATH)
    facade_init = _class_method(training_tree, "AssignmentIsaacLabEnv", "__init__")
    _assert(
        _first_call_line(
            facade_init,
            "resolve_or_validate_assignment_profile_authority",
        )
        < _first_call_line(facade_init, "make"),
        "env facade authority is after gym.make",
    )
    facade_wrapper_calls = _calls(facade_init, "AssignmentHarlWrapper")
    _assert(len(facade_wrapper_calls) == 1, "facade wrapper call is ambiguous")
    _assert(
        _attribute_chain(
            _keyword(facade_wrapper_calls[0], "resolved_assignment_profile")
        )
        == ("self", "resolved_assignment_profile"),
        "env facade does not pass its exact object to wrapper",
    )
    runner_init = _class_method(
        training_tree,
        "AssignmentOnPolicyHARunner",
        "__init__",
    )
    _assert(
        _first_call_line(
            runner_init,
            "resolve_or_validate_assignment_profile_authority",
        )
        < _first_call_line(runner_init, "set_seed"),
        "runner authority is after RNG initialization",
    )
    train_env_calls = _calls(runner_init, "make_assignment_train_env")
    _assert(len(train_env_calls) == 1, "runner train-env call is ambiguous")
    _assert(
        _attribute_chain(
            _keyword(train_env_calls[0], "resolved_assignment_profile")
        )
        == ("self", "resolved_assignment_profile"),
        "runner does not pass its exact object to env facade",
    )

    train_main = _function(_tree(ENTRYPOINT_PATHS["train"]), "main")
    dynamic_runner_calls = [
        call
        for call in ast.walk(train_main)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Subscript)
    ]
    formal_runner_calls = [
        call
        for call in dynamic_runner_calls
        if _keyword(call, "resolved_assignment_profile") is not None
    ]
    _assert(len(formal_runner_calls) == 1, "formal dynamic runner call is ambiguous")
    _assert(
        _attribute_chain(
            _keyword(formal_runner_calls[0], "resolved_assignment_profile")
        )
        == ("resolved_assignment_profile",),
        "entrypoint does not pass its exact local identity to runner",
    )
    return {
        "wrapper_guard_before_branches": True,
        "factory_guard_before_gym": True,
        "facade_guard_before_gym": True,
        "runner_guard_before_rng_output_env_actor_checkpoint": True,
        "entrypoint_runner_facade_wrapper_parameter_chain": True,
    }


def test_import_boundary_training_contract_and_serialization_ast() -> dict[str, Any]:
    consumer_paths = (WRAPPER_PATH, TRAINING_CONTRACT_PATH, TRAINING_PATH)
    for path in consumer_paths:
        source = _source(path)
        _assert(
            "from assignment_profile_contract import" not in source,
            f"{path.name} contains forbidden bare contract fallback",
        )
        _assert(
            "sys.modules" not in source,
            f"{path.name} contains a module alias/cache mutation",
        )
    training_contract_source = _source(TRAINING_CONTRACT_PATH)
    _assert(
        "_profile_name_from_config" not in training_contract_source,
        "training contract still owns raw-string profile authority",
    )
    _assert(
        "assignment_lifecycle_profile_from_env_args"
        not in training_contract_source,
        "training contract still rereads env_args profile",
    )
    _assert(
        "ResolvedEventGatedAssignmentProfile"
        not in training_contract_source
        or "require_assignment_profile_runtime_ready"
        in training_contract_source,
        "event training route lacks explicit typed readiness dispatch",
    )

    train_source = _source(ENTRYPOINT_PATHS["train"])
    forbidden_serialization_patterns = (
        'env_args["resolved_assignment_profile"]',
        "env_args['resolved_assignment_profile']",
        'args["resolved_assignment_profile"]',
        "args['resolved_assignment_profile']",
        "env_cfg.resolved_assignment_profile",
        "setattr(env_cfg, \"resolved_assignment_profile\"",
    )
    for pattern in forbidden_serialization_patterns:
        _assert(pattern not in train_source, f"resolved object serialized via {pattern}")
    _assert(
        "resolved_assignment_profile=resolved_assignment_profile"
        in train_source,
        "train does not use an explicit process-local constructor parameter",
    )
    _assert(
        "render.use_render=False" in _source(TRAINING_PATH),
        "assignment render bypass is not fail-closed",
    )
    return {
        "canonical_relative_or_absolute_key_only": True,
        "bare_contract_fallback": False,
        "training_contract_raw_string_authority": False,
        "resolved_object_in_config_or_serialization": False,
        "assignment_render_bypass": "fail-closed before side effects",
    }


def test_formal_wrapper_call_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "formal_entrypoint_resolvers": {},
        "formal_wrapper_factories": {},
        "production_internal_wrapper_calls": [],
        "direct_fake_wrapper_call_count": 0,
    }
    for label, path in ENTRYPOINT_PATHS.items():
        tree = _tree(path)
        inventory["formal_entrypoint_resolvers"][label] = len(
            _calls(tree, "resolve_assignment_profile")
        )
        factory_calls = _calls(tree, "make_assignment_harl_env")
        if factory_calls:
            for call in factory_calls:
                origin = _attribute_chain(
                    _keyword(call, "profile_resolution_origin")
                )
                _assert(
                    origin
                    == (
                        "AssignmentProfileResolutionOrigin",
                        "FORMAL_ENTRYPOINT",
                    ),
                    f"{label} factory call can silently use direct fallback",
                )
            inventory["formal_wrapper_factories"][label] = len(factory_calls)
    _assert(
        inventory["formal_entrypoint_resolvers"]
        == {label: 1 for label in FORMAL_ENTRYPOINTS},
        "formal resolver inventory changed",
    )
    _assert(
        inventory["formal_wrapper_factories"]
        == {
            "play": 1,
            "rl_diagnostics": 1,
            "methods": 1,
            "controller_diagnosis": 1,
        },
        "formal wrapper-factory inventory changed",
    )

    for path, enclosing in (
        (WRAPPER_PATH, "make_assignment_harl_env"),
        (TRAINING_PATH, "AssignmentIsaacLabEnv.__init__"),
    ):
        count = len(_calls(_tree(path), "AssignmentHarlWrapper"))
        _assert(count == 1, f"{path.name} internal wrapper call count={count}")
        inventory["production_internal_wrapper_calls"].append(
            {"file": path.name, "enclosing": enclosing, "count": count}
        )

    direct_test_files = (
        "test_assignment_cooldown_mask_smoke.py",
        "test_assignment_failed_pair_memory_smoke.py",
        "test_assignment_lifecycle_controlled_training_gate.py",
        "test_assignment_lifecycle_feed_forward_guard.py",
        "test_assignment_lifecycle_observation_integration.py",
        "test_assignment_lifecycle_mask_and_harl_replay.py",
    )
    direct_count = 0
    for filename in direct_test_files:
        path = REPO_ROOT / "scripts" / "environments" / filename
        direct_count += len(_calls(_tree(path), "AssignmentHarlWrapper"))
    _assert(direct_count == 11, f"direct/fake wrapper inventory={direct_count}")
    inventory["direct_fake_wrapper_call_count"] = direct_count
    inventory["dynamic_runner_authority"] = (
        "train.py RUNNER_REGISTRY call with explicit resolved keyword"
    )
    return inventory


def test_helper_side_effect_boundary() -> dict[str, Any]:
    random_before = random.getstate()
    cwd_before = Path.cwd()
    environment_before = dict(os.environ)
    sys_path_before = tuple(sys.path)
    root_handlers_before = tuple(logging.getLogger().handlers)
    with tempfile.TemporaryDirectory(prefix="phase_a1c_profile_wiring_") as temp:
        temp_path = Path(temp)
        files_before = tuple(temp_path.iterdir())
        profile = _resolve("legacy")
        _assert(
            _authority("legacy", profile, origin="formal_entrypoint") is profile,
            "side-effect probe changed identity",
        )
        SCENARIO.preflight_assignment_lifecycle_profile_runtime_primitive(
            "legacy",
            raw_profile_present=True,
            hydra_overrides=[],
            entrypoint="side-effect-test",
        )
        files_after = tuple(temp_path.iterdir())
    checks = {
        "random_unchanged": random.getstate() == random_before,
        "cwd_unchanged": Path.cwd() == cwd_before,
        "environment_unchanged": dict(os.environ) == environment_before,
        "sys_path_unchanged": tuple(sys.path) == sys_path_before,
        "logger_unchanged": tuple(logging.getLogger().handlers)
        == root_handlers_before,
        "files_unchanged": files_before == files_after == (),
    }
    _assert(all(checks.values()), f"pure helper side effect: {checks}")
    forbidden = (
        "isaaclab",
        "isaacsim",
        "omni",
        "harl",
        "torch",
    )
    loaded_forbidden = sorted(
        name
        for name in sys.modules
        if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
    )
    _assert(not loaded_forbidden, f"forbidden modules loaded: {loaded_forbidden[:5]}")
    checks["forbidden_runtime_modules_absent"] = True
    return checks


TESTS = (
    test_authority_and_mismatch_matrix,
    test_direct_fallback_exactly_once,
    test_primitive_preflight_finalize_and_contract_c,
    test_same_object_authority_chain,
    test_training_contract_resolved_identity_routes,
    test_entrypoint_ordering_and_formal_resolution_inventory,
    test_core_barriers_and_same_object_ast,
    test_import_boundary_training_contract_and_serialization_ast,
    test_formal_wrapper_call_inventory,
    test_helper_side_effect_boundary,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {}
    failures = 0
    for test in TESTS:
        try:
            evidence[test.__name__] = test()
            results.append({"name": test.__name__, "status": "passed"})
        except Exception as exc:
            failures += 1
            results.append(
                {
                    "name": test.__name__,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    payload = {
        "status": "passed" if failures == 0 else "failed",
        "num_tests": len(TESTS),
        "passed": len(TESTS) - failures,
        "failed": failures,
        "tests": results,
        "evidence": evidence,
        "runtime_boundary": (
            "pure/static A1c wiring evidence only; no AppLauncher, Isaac "
            "environment, HARL, actor, checkpoint I/O, training, playback, or evaluation"
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result['status'].upper()}: {result['name']}")
            if "error" in result:
                print(f"  {result['error']}")
        print(
            f"{payload['status'].upper()}: "
            f"{payload['passed']}/{payload['num_tests']} tests passed"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
