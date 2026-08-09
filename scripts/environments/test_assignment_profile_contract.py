"""Pure/static regressions for the Phase A1a/A1b assignment profile contract.

This suite deliberately avoids a normal ``isaaclab_tasks`` package import.
That package performs task discovery and the scan task package imports its
environment.  The contract is instead loaded once under its sole canonical
module key by a bounded namespace harness.

The suite does not import Isaac Lab, AppLauncher, HARL, NumPy, or torch; create
an Isaac environment; read or write a checkpoint; run training, playback, or
evaluation; or modify a production consumer.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from enum import Enum
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable, Mapping, get_args


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
CONTRACT_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"
SCENARIO_CONFIG_PATH = SCAN_TASK_SOURCE / "scenario_config.py"
WRAPPER_PATH = SCAN_TASK_SOURCE / "assignment_harl_wrapper.py"
OBSERVATION_PATH = SCAN_TASK_SOURCE / "assignment_lifecycle_observation.py"
HISTORICAL_IDENTITY_TEST_PATH = (
    REPO_ROOT / "scripts" / "environments" / "test_assignment_initial_condition_contract.py"
)

CANONICAL_MODULE = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
BARE_MODULE = "assignment_profile_contract"
PROFILE_CONTRACT_VERSION = "assignment_resolved_profile_v1"

PROFILE_VALUES = (
    "legacy",
    "lifecycle_ablation",
    "lifecycle_contract_c",
    "diagnostics_hidden_state",
    "event_gated_local_mrta",
)
EXISTING_PROFILE_VALUES = PROFILE_VALUES[:4]
ORIGIN_VALUES = ("formal_entrypoint", "direct_wrapper_fallback")
RUNTIME_ROUTE_VALUES = (
    "existing_legacy_assignment_harl_v1",
    "existing_lifecycle_ablation_assignment_harl_v1",
    "existing_lifecycle_contract_c_assignment_harl_v1",
    "existing_diagnostics_hidden_state_assignment_harl_v1",
    "event_gated_phase_a_interface_only_v1",
)
CHECKPOINT_FAMILY_VALUES = (
    "assignment_checkpoint_contract_v2",
    "assignment_checkpoint_contract_v2_explicit_ablation_evaluation",
    "none",
    "assignment_checkpoint_contract_v3",
)
SUPPORT_VALUES = {
    "allowed",
    "existing_blocked",
    "phase_a_blocked",
    "normal",
    "explicit_ablation",
    "diagnostics",
    "blocked",
}
READINESS_VALUES = ("existing_ready", "interface_only")

SHARED_RESOLVED_FIELDS = (
    "profile_contract_version",
    "profile_name",
    "resolution_origin",
    "runtime_route",
    "checkpoint_family",
    "training_support",
    "playback_support",
    "runtime_readiness",
)
EXISTING_ONLY_FIELDS = (
    "resolver_enabled",
    "lifecycle_observation_enabled",
    "lifecycle_mask_enabled",
    "actor_schema_version",
    "shared_schema_version",
    "shared_construction_mode",
    "mask_contract_version",
    "budget_release_contract",
    "legacy_guardrail_profile",
    "policy_sequence_route",
    "training_semantic_contract",
)
EVENT_ONLY_FIELDS = ("event_gated_target_semantics",)

PUBLIC_ENUM_NAMES = (
    "AssignmentProfileName",
    "AssignmentRuntimeRoute",
    "AssignmentCheckpointFamily",
    "AssignmentProfileSupport",
    "AssignmentRuntimeReadiness",
    "AssignmentProfileResolutionOrigin",
)
PUBLIC_DATACLASS_NAMES = (
    "TrainingSemanticContract",
    "EventGatedTargetSemantics",
    "ResolvedExistingAssignmentProfile",
    "ResolvedEventGatedAssignmentProfile",
)
PUBLIC_EXCEPTION_NAMES = (
    "AssignmentProfileContractError",
    "ProfileResolutionError",
    "UnknownAssignmentProfileError",
    "InvalidAssignmentProfileError",
    "AssignmentProfileRegistryError",
    "AssignmentProfileRouteError",
    "CanonicalModuleIdentityError",
)
PUBLIC_IDENTITY_TYPE_NAMES = PUBLIC_ENUM_NAMES + PUBLIC_DATACLASS_NAMES + PUBLIC_EXCEPTION_NAMES

EXPECTED_POLICY_SEQUENCE_ROUTES = {
    "legacy": "legacy_existing_policy_sequence_v1",
    "lifecycle_ablation": "lifecycle_ablation_no_training_v1",
    "lifecycle_contract_c": "lifecycle_feed_forward_v1",
    "diagnostics_hidden_state": "diagnostics_only_no_training_v1",
}

EXPECTED_EXISTING_TRAINING_SEMANTICS = {
    "legacy": {
        "contract_version": "legacy_existing_policy_sequence_v1",
        "algorithm_name": None,
        "state_type": None,
        "share_param": None,
        "use_recurrent_policy": None,
        "use_naive_recurrent_policy": None,
        "actor_buffer_generator": "resolved_by_legacy_harl_config",
        "serialization_mode": None,
        "save_entire_model": None,
        "installed_harl_mutable": False,
    },
    "lifecycle_ablation": {
        "contract_version": "lifecycle_ablation_no_training_v1",
        "algorithm_name": None,
        "state_type": None,
        "share_param": None,
        "use_recurrent_policy": None,
        "use_naive_recurrent_policy": None,
        "actor_buffer_generator": None,
        "serialization_mode": None,
        "save_entire_model": None,
        "installed_harl_mutable": False,
    },
    "lifecycle_contract_c": {
        "contract_version": "lifecycle_feed_forward_v1",
        "algorithm_name": "happo",
        "state_type": "EP",
        "share_param": False,
        "use_recurrent_policy": False,
        "use_naive_recurrent_policy": False,
        "actor_buffer_generator": "feed_forward_generator_actor",
        "serialization_mode": "state_dict",
        "save_entire_model": False,
        "installed_harl_mutable": False,
    },
    "diagnostics_hidden_state": {
        "contract_version": "diagnostics_only_no_training_v1",
        "algorithm_name": None,
        "state_type": None,
        "share_param": None,
        "use_recurrent_policy": None,
        "use_naive_recurrent_policy": None,
        "actor_buffer_generator": None,
        "serialization_mode": None,
        "save_entire_model": None,
        "installed_harl_mutable": False,
    },
}

EXPECTED_LEGACY_WRAPPER_MAPPINGS: dict[str, tuple[tuple[str, object], ...]] = {
    "legacy": (
        ("profile_name", "legacy"),
        ("actor_schema_version", "legacy_v1"),
        ("shared_schema_version", "legacy_v1_shared_actor_concat"),
        ("shared_construction_mode", "actor_concat"),
        ("mask_contract_version", "legacy_mask_v1"),
        ("budget_release_contract", "disabled"),
        ("legacy_guardrail_profile", "legacy_guardrails_v1"),
        ("resolver_enabled", False),
        ("lifecycle_observation_enabled", False),
        ("lifecycle_mask_enabled", False),
        ("training_allowed", True),
    ),
    "lifecycle_ablation": (
        ("profile_name", "lifecycle_ablation"),
        ("actor_schema_version", "lifecycle_v1_actor_3n"),
        ("shared_schema_version", "lifecycle_v1_shared_option_a_budget2m"),
        ("shared_construction_mode", "actor_concat_plus_critic_budget_2m"),
        ("mask_contract_version", "lifecycle_ablation_physical_mask_v1"),
        ("budget_release_contract", "disabled"),
        ("legacy_guardrail_profile", "lifecycle_no_legacy_guardrails_v1"),
        ("resolver_enabled", False),
        ("lifecycle_observation_enabled", True),
        ("lifecycle_mask_enabled", False),
        ("training_allowed", False),
        (
            "training_blocked_reason",
            "assignment_lifecycle_profile='lifecycle_ablation' is an explicit "
            "observation/mask ablation profile and is not enabled for normal training.",
        ),
    ),
    "lifecycle_contract_c": (
        ("profile_name", "lifecycle_contract_c"),
        ("actor_schema_version", "lifecycle_v1_actor_3n"),
        ("shared_schema_version", "lifecycle_v1_shared_option_a_budget2m"),
        ("shared_construction_mode", "actor_concat_plus_critic_budget_2m"),
        ("mask_contract_version", "lifecycle_contract_c_mask_v1"),
        ("budget_release_contract", "budget_release_v1"),
        ("legacy_guardrail_profile", "lifecycle_no_legacy_guardrails_v1"),
        ("resolver_enabled", True),
        ("lifecycle_observation_enabled", True),
        ("lifecycle_mask_enabled", True),
        ("training_allowed", True),
    ),
    "diagnostics_hidden_state": (
        ("profile_name", "diagnostics_hidden_state"),
        ("actor_schema_version", "legacy_v1"),
        ("shared_schema_version", "legacy_v1_shared_actor_concat"),
        ("shared_construction_mode", "actor_concat"),
        ("mask_contract_version", "diagnostics_mask_v1"),
        ("budget_release_contract", "diagnostics_only"),
        ("legacy_guardrail_profile", "diagnostics_guardrails_v1"),
        ("resolver_enabled", True),
        ("lifecycle_observation_enabled", False),
        ("lifecycle_mask_enabled", False),
        ("training_allowed", False),
    ),
}

PROFILE_MATRIX = {
    "legacy": {
        "runtime_route": "existing_legacy_assignment_harl_v1",
        "checkpoint_family": "assignment_checkpoint_contract_v2",
        "training_support": "allowed",
        "playback_support": "normal",
        "runtime_readiness": "existing_ready",
    },
    "lifecycle_ablation": {
        "runtime_route": "existing_lifecycle_ablation_assignment_harl_v1",
        "checkpoint_family": "assignment_checkpoint_contract_v2_explicit_ablation_evaluation",
        "training_support": "existing_blocked",
        "playback_support": "explicit_ablation",
        "runtime_readiness": "existing_ready",
    },
    "lifecycle_contract_c": {
        "runtime_route": "existing_lifecycle_contract_c_assignment_harl_v1",
        "checkpoint_family": "assignment_checkpoint_contract_v2",
        "training_support": "allowed",
        "playback_support": "normal",
        "runtime_readiness": "existing_ready",
    },
    "diagnostics_hidden_state": {
        "runtime_route": "existing_diagnostics_hidden_state_assignment_harl_v1",
        "checkpoint_family": "none",
        "training_support": "existing_blocked",
        "playback_support": "diagnostics",
        "runtime_readiness": "existing_ready",
    },
    "event_gated_local_mrta": {
        "runtime_route": "event_gated_phase_a_interface_only_v1",
        "checkpoint_family": "assignment_checkpoint_contract_v3",
        "training_support": "phase_a_blocked",
        "playback_support": "blocked",
        "runtime_readiness": "interface_only",
    },
}

EVENT_SERIALIZED_MAPPING_FORMAL = {
    "profile_contract_version": "assignment_resolved_profile_v1",
    "profile_name": "event_gated_local_mrta",
    "resolution_origin": "formal_entrypoint",
    "runtime_route": "event_gated_phase_a_interface_only_v1",
    "checkpoint_family": "assignment_checkpoint_contract_v3",
    "training_support": "phase_a_blocked",
    "playback_support": "blocked",
    "runtime_readiness": "interface_only",
    "event_gated_target_semantics": {
        "contract_version": "event_gated_target_semantics_v1",
        "actor_schema_version": "event_gated_global_actor_observation_v1",
        "shared_schema_version": "event_gated_global_centralized_observation_v1",
        "shared_construction_mode": "global_fixed_width_centralized_v1",
        "mask_contract_version": "event_gated_global_id_local_mask_v1",
        "budget_release_contract": "authoritative_lifecycle_release_v1",
        "policy_sequence_route": "event_gated_decision_valid_feed_forward_v1",
        "training_semantic_contract": {
            "contract_version": "event_gated_happo_ep_feed_forward_v1",
            "algorithm_name": "happo",
            "state_type": "EP",
            "share_param": False,
            "use_recurrent_policy": False,
            "use_naive_recurrent_policy": False,
            "actor_buffer_generator": "feed_forward_generator_actor",
            "serialization_mode": "state_dict",
            "save_entire_model": False,
            "installed_harl_mutable": False,
        },
    },
}

FORBIDDEN_EVENT_KEYS = {
    "event_gate_enabled",
    "resolver_enabled",
    "lifecycle_observation_enabled",
    "lifecycle_mask_enabled",
    "to_legacy_wrapper_mapping",
}

IDENTITY_EVIDENCE: dict[str, Any] = {}
SIDE_EFFECT_EVIDENCE: dict[str, Any] = {}
STATIC_MAPPING_EVIDENCE: dict[str, Any] = {}
SCENARIO_EVIDENCE: dict[str, Any] = {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(
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


def _load_contract_module() -> ModuleType:
    if not CONTRACT_PATH.is_file():
        raise RuntimeError(f"Phase A1a contract source is absent: {CONTRACT_PATH}")
    existing = sys.modules.get(CANONICAL_MODULE)
    if existing is not None:
        existing_path = Path(str(getattr(existing, "__file__", ""))).resolve()
        _assert(existing_path == CONTRACT_PATH.resolve(), "canonical key points to another source")
        return existing
    spec = importlib.util.spec_from_file_location(CANONICAL_MODULE, CONTRACT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not create canonical module spec for {CONTRACT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[CANONICAL_MODULE] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(CANONICAL_MODULE, None)
        raise
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


CONTRACT = _load_contract_module()


def _load_scenario_config_module() -> ModuleType:
    if not SCENARIO_CONFIG_PATH.is_file():
        raise RuntimeError(f"Phase A1b scenario source is absent: {SCENARIO_CONFIG_PATH}")
    spec = importlib.util.spec_from_file_location(
        "phase_a1b_scenario_config_harness",
        SCENARIO_CONFIG_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not create scenario module spec for {SCENARIO_CONFIG_PATH}")
    module = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    path_inserted = False
    try:
        sys.dont_write_bytecode = True
        if str(SCAN_TASK_SOURCE) not in sys.path:
            sys.path.insert(0, str(SCAN_TASK_SOURCE))
            path_inserted = True
        spec.loader.exec_module(module)
    finally:
        if path_inserted:
            sys.path.remove(str(SCAN_TASK_SOURCE))
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


SCENARIO_CONFIG = _load_scenario_config_module()


def _enum_values(enum_type: type[Enum]) -> tuple[str, ...]:
    return tuple(str(member.value) for member in enum_type)


def _enum_member_for_value(enum_type: type[Enum], value: str) -> Enum:
    matches = [member for member in enum_type if member.value == value]
    _assert(len(matches) == 1, f"{enum_type.__name__} must contain exactly one {value!r}")
    return matches[0]


def _serialized_value(value: object) -> object:
    return value.value if isinstance(value, Enum) else value


def _origin(value: str = "formal_entrypoint") -> Enum:
    return _enum_member_for_value(CONTRACT.AssignmentProfileResolutionOrigin, value)


def _resolve(profile: str | Enum, origin: str = "formal_entrypoint") -> object:
    return CONTRACT.resolve_assignment_profile(profile, _origin(origin))


def _assert_mapping_rejects_mutation(mapping: Mapping[object, object], label: str) -> None:
    try:
        mapping["__a1a_mutation_probe__"] = "forbidden"  # type: ignore[index]
    except (TypeError, AttributeError):
        return
    raise AssertionError(f"{label} is mutable")


def _assert_deeply_immutable(value: object, label: str) -> None:
    if isinstance(value, Mapping):
        _assert_mapping_rejects_mutation(value, label)
        for key, nested in value.items():
            _assert_deeply_immutable(nested, f"{label}[{key!r}]")
        return
    if isinstance(value, tuple):
        for index, nested in enumerate(value):
            _assert_deeply_immutable(nested, f"{label}[{index}]")
        return
    _assert(not isinstance(value, (dict, list, set)), f"{label} contains mutable {type(value).__name__}")


def _assert_primitive_mapping(value: object, label: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _assert(isinstance(key, str), f"{label} has non-string key {key!r}")
            _assert_primitive_mapping(nested, f"{label}.{key}")
        return
    if isinstance(value, (tuple, list)):
        for index, nested in enumerate(value):
            _assert_primitive_mapping(nested, f"{label}[{index}]")
        return
    _assert(
        value is None or isinstance(value, (str, bool, int, float)),
        f"{label} contains non-primitive {type(value).__name__}",
    )


def test_profile_vocabulary_and_normalization() -> None:
    profile_enum = CONTRACT.AssignmentProfileName
    _assert(_enum_values(profile_enum) == PROFILE_VALUES, "canonical profile vocabulary/order changed")
    _assert(
        _enum_values(CONTRACT.AssignmentRuntimeRoute) == RUNTIME_ROUTE_VALUES,
        "runtime-route vocabulary/order changed",
    )
    _assert(
        _enum_values(CONTRACT.AssignmentCheckpointFamily) == CHECKPOINT_FAMILY_VALUES,
        "checkpoint-family vocabulary/order changed",
    )
    _assert(
        set(_enum_values(CONTRACT.AssignmentProfileSupport)) == SUPPORT_VALUES,
        "profile-support vocabulary changed",
    )
    _assert(
        _enum_values(CONTRACT.AssignmentRuntimeReadiness) == READINESS_VALUES,
        "runtime-readiness vocabulary/order changed",
    )
    _assert(
        _enum_values(CONTRACT.AssignmentProfileResolutionOrigin) == ORIGIN_VALUES,
        "resolution-origin vocabulary/order changed",
    )

    for value in PROFILE_VALUES:
        member = _enum_member_for_value(profile_enum, value)
        _assert(CONTRACT.normalize_assignment_profile_name(member) is member, f"enum identity lost for {value}")
        _assert(
            CONTRACT.normalize_assignment_profile_name(f" \t{value}\n") is member,
            f"whitespace canonicalization failed for {value}",
        )

    _expect_raises(
        lambda: CONTRACT.normalize_assignment_profile_name(""),
        CONTRACT.InvalidAssignmentProfileError,
        "actual",
    )
    _expect_raises(
        lambda: CONTRACT.normalize_assignment_profile_name("   "),
        CONTRACT.InvalidAssignmentProfileError,
        "actual",
    )
    _expect_raises(
        lambda: CONTRACT.normalize_assignment_profile_name(None),
        CONTRACT.InvalidAssignmentProfileError,
        "actual",
    )
    for invalid in ("LEGACY", "Legacy", "contract_c", "event_gated", "unknown"):
        _expect_raises(
            lambda invalid=invalid: CONTRACT.normalize_assignment_profile_name(invalid),
            CONTRACT.UnknownAssignmentProfileError,
            invalid,
            "expected",
        )


def test_exception_hierarchy_and_context() -> None:
    base = CONTRACT.AssignmentProfileContractError
    resolution = CONTRACT.ProfileResolutionError
    _assert(issubclass(resolution, base), "ProfileResolutionError hierarchy changed")
    _assert(
        issubclass(CONTRACT.UnknownAssignmentProfileError, resolution),
        "UnknownAssignmentProfileError hierarchy changed",
    )
    _assert(
        issubclass(CONTRACT.InvalidAssignmentProfileError, resolution),
        "InvalidAssignmentProfileError hierarchy changed",
    )
    for name in (
        "AssignmentProfileRegistryError",
        "AssignmentProfileRouteError",
        "CanonicalModuleIdentityError",
    ):
        _assert(issubclass(getattr(CONTRACT, name), base), f"{name} hierarchy changed")

    event_profile = _resolve("event_gated_local_mrta")
    route_error = _expect_raises(
        lambda: CONTRACT.validate_existing_assignment_profile(event_profile),
        CONTRACT.AssignmentProfileRouteError,
        "event_gated_local_mrta",
        PROFILE_CONTRACT_VERSION,
        "formal_entrypoint",
    )
    _assert("expected" in str(route_error) and "actual" in str(route_error), "route error lacks context")


def test_registry_exhaustiveness_immutability_and_resolution() -> None:
    registry = CONTRACT.get_assignment_profile_registry()
    _assert(isinstance(registry, Mapping), "registry is not a mapping")
    _assert(tuple(registry) == tuple(CONTRACT.AssignmentProfileName), "registry order/key identity changed")
    _assert(len(registry) == 5, "registry must contain exactly five profiles")
    _assert_mapping_rejects_mutation(registry, "registry")
    _assert_deeply_immutable(registry, "registry")
    CONTRACT.validate_assignment_profile_registry()

    for profile_name, definition in registry.items():
        _assert(isinstance(definition, Mapping), f"{profile_name.value} definition is not a mapping")
        _assert(
            "resolution_origin" not in definition,
            f"{profile_name.value} registry definition incorrectly freezes a call-specific origin",
        )

    existing_type = CONTRACT.ResolvedExistingAssignmentProfile
    event_type = CONTRACT.ResolvedEventGatedAssignmentProfile
    for origin_value in ORIGIN_VALUES:
        for profile_value in PROFILE_VALUES:
            first = _resolve(profile_value, origin_value)
            second = _resolve(profile_value, origin_value)
            _assert(first == second, f"{profile_value}/{origin_value} resolution is nondeterministic")
            _assert(first is not second, f"{profile_value}/{origin_value} did not materialize a fresh value object")
            _assert(first.profile_contract_version == PROFILE_CONTRACT_VERSION, "contract version changed")
            _assert(first.profile_name.value == profile_value, "resolved profile discriminant changed")
            _assert(first.resolution_origin.value == origin_value, "resolution origin changed")
            expected_type = event_type if profile_value == "event_gated_local_mrta" else existing_type
            _assert(type(first) is expected_type, f"{profile_value} resolved to the wrong exact subtype")
            _assert(not hasattr(first, "__dict__"), f"{profile_value} dataclass does not use slots")
            _expect_raises(
                lambda first=first: setattr(first, "profile_contract_version", "mutated"),
                (FrozenInstanceError, AttributeError),
            )
            matrix = PROFILE_MATRIX[profile_value]
            for field_name, expected in matrix.items():
                actual = _serialized_value(getattr(first, field_name))
                _assert(actual == expected, f"{profile_value}.{field_name}: {actual!r} != {expected!r}")

    _expect_raises(
        lambda: CONTRACT.resolve_assignment_profile("not_a_profile", _origin()),
        CONTRACT.UnknownAssignmentProfileError,
        "not_a_profile",
    )
    _expect_raises(
        lambda: CONTRACT.resolve_assignment_profile("legacy", "formal_entrypoint"),
        CONTRACT.InvalidAssignmentProfileError,
        "resolution",
        "actual",
    )


def test_discriminated_union_and_existing_route_guard() -> None:
    union_args = get_args(CONTRACT.ResolvedAssignmentProfile)
    _assert(
        union_args
        == (
            CONTRACT.ResolvedExistingAssignmentProfile,
            CONTRACT.ResolvedEventGatedAssignmentProfile,
        ),
        "ResolvedAssignmentProfile union changed",
    )
    _assert(
        tuple(field.name for field in fields(CONTRACT.ResolvedExistingAssignmentProfile))
        == SHARED_RESOLVED_FIELDS + EXISTING_ONLY_FIELDS,
        "existing resolved-profile field family changed",
    )
    _assert(
        tuple(field.name for field in fields(CONTRACT.ResolvedEventGatedAssignmentProfile))
        == SHARED_RESOLVED_FIELDS + EVENT_ONLY_FIELDS,
        "event resolved-profile field family changed",
    )

    for profile_value in EXISTING_PROFILE_VALUES:
        resolved = _resolve(profile_value)
        _assert(
            CONTRACT.validate_existing_assignment_profile(resolved) is resolved,
            f"{profile_value} existing-route validator rebuilt the identity",
        )
        for field_name in EXISTING_ONLY_FIELDS:
            _assert(hasattr(resolved, field_name), f"{profile_value} lacks {field_name}")

    event_profile = _resolve("event_gated_local_mrta")
    _assert(
        isinstance(event_profile, CONTRACT.ResolvedEventGatedAssignmentProfile),
        "event profile strict isinstance failed",
    )
    _assert(
        not isinstance(event_profile, CONTRACT.ResolvedExistingAssignmentProfile),
        "event profile entered the existing subtype",
    )
    for name in FORBIDDEN_EVENT_KEYS:
        _assert(not hasattr(event_profile, name), f"event subtype exposes forbidden {name}")
        _assert(not hasattr(type(event_profile), name), f"event subtype class exposes forbidden {name}")
    _expect_raises(
        lambda: CONTRACT.validate_existing_assignment_profile(event_profile),
        CONTRACT.AssignmentProfileRouteError,
        "event_gated_local_mrta",
    )

    legacy = _resolve("legacy")
    _expect_raises(
        lambda: replace(
            legacy,
            profile_name=_enum_member_for_value(
                CONTRACT.AssignmentProfileName, "event_gated_local_mrta"
            ),
        ),
        CONTRACT.InvalidAssignmentProfileError,
        "expected",
        "actual",
    )
    _expect_raises(
        lambda: replace(
            event_profile,
            profile_name=_enum_member_for_value(CONTRACT.AssignmentProfileName, "legacy"),
        ),
        CONTRACT.InvalidAssignmentProfileError,
        "expected",
        "actual",
    )


def _static_eval(node: ast.AST, constants: Mapping[str, object]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in constants:
            raise KeyError(node.id)
        return constants[node.id]
    if isinstance(node, ast.Tuple):
        return tuple(_static_eval(item, constants) for item in node.elts)
    if isinstance(node, ast.List):
        return [_static_eval(item, constants) for item in node.elts]
    if isinstance(node, ast.Set):
        return {_static_eval(item, constants) for item in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _static_eval(key, constants): _static_eval(value, constants)
            for key, value in zip(node.keys, node.values, strict=True)
            if key is not None
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_static_eval(node.operand, constants)  # type: ignore[operator]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_eval(node.left, constants) + _static_eval(node.right, constants)  # type: ignore[operator]
    raise TypeError(f"unsupported static expression: {ast.dump(node, include_attributes=False)}")


def _collect_static_constants(tree: ast.Module, initial: Mapping[str, object] | None = None) -> dict[str, object]:
    constants = dict(initial or {})
    pending: list[tuple[str, ast.AST]] = []
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name):
            pending.append((target.id, statement.value))
    while pending:
        unresolved: list[tuple[str, ast.AST]] = []
        progress = False
        for name, expression in pending:
            try:
                constants[name] = _static_eval(expression, constants)
            except (KeyError, TypeError):
                unresolved.append((name, expression))
            else:
                progress = True
        if not progress:
            break
        pending = unresolved
    return constants


def _profile_comparison_value(test: ast.AST) -> str | None:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    if not isinstance(test.ops[0], ast.Eq):
        return None
    if not isinstance(test.left, ast.Name) or test.left.id != "profile":
        return None
    comparator = test.comparators[0]
    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
        return comparator.value
    return None


def _return_dict_from_statements(statements: list[ast.stmt]) -> ast.Dict:
    direct = [
        statement.value
        for statement in statements
        if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Dict)
    ]
    _assert(len(direct) == 1, "profile branch does not have exactly one direct dict return")
    return direct[0]


def _extract_current_wrapper_mappings() -> dict[str, tuple[tuple[str, object], ...]]:
    wrapper_tree = ast.parse(WRAPPER_PATH.read_text(encoding="utf-8"), filename=str(WRAPPER_PATH))
    wrapper_classes = [
        node
        for node in wrapper_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "AssignmentHarlWrapper"
    ]
    _assert(len(wrapper_classes) == 1, "AssignmentHarlWrapper definition is ambiguous")
    methods = [
        node
        for node in wrapper_classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_assignment_lifecycle_profile_config"
    ]
    _assert(len(methods) == 1, "wrapper profile-config method is ambiguous")
    method = methods[0]
    mapping_calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "to_legacy_wrapper_mapping"
    ]
    _assert(
        len(mapping_calls) == 1,
        "wrapper must consume exactly one canonical to_legacy_wrapper_mapping() result",
    )
    _assert(
        not any(isinstance(node, ast.Dict) for node in ast.walk(method)),
        "wrapper must not duplicate the canonical existing-profile mapping",
    )
    enum_branches = {
        node.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "AssignmentProfileName"
    }
    _assert(
        enum_branches
        == {
            "LEGACY",
            "LIFECYCLE_ABLATION",
            "LIFECYCLE_CONTRACT_C",
            "DIAGNOSTICS_HIDDEN_STATE",
        },
        "wrapper existing-profile enum dispatch is not exact/exhaustive",
    )
    return {
        profile_value: tuple(
            _resolve(profile_value).to_legacy_wrapper_mapping().items()
        )
        for profile_value in EXISTING_PROFILE_VALUES
    }


def test_existing_wrapper_mapping_static_golden() -> None:
    source_mappings = _extract_current_wrapper_mappings()
    _assert(
        source_mappings == EXPECTED_LEGACY_WRAPPER_MAPPINGS,
        "static wrapper mappings differ from the A1a golden fixture",
    )
    for profile_value in EXISTING_PROFILE_VALUES:
        resolved = _resolve(profile_value)
        mapping = resolved.to_legacy_wrapper_mapping()
        _assert(isinstance(mapping, Mapping), f"{profile_value} legacy mapping is not a mapping")
        _assert(
            tuple(mapping.items()) == source_mappings[profile_value],
            f"{profile_value} mapping differs by key/value/order from current wrapper",
        )
        _assert(
            resolved.policy_sequence_route == EXPECTED_POLICY_SEQUENCE_ROUTES[profile_value],
            f"{profile_value} policy sequence route changed",
        )
        try:
            mapping["profile_name"] = "corrupt"  # type: ignore[index]
        except (TypeError, AttributeError):
            pass
        _assert(
            tuple(resolved.to_legacy_wrapper_mapping().items()) == source_mappings[profile_value],
            f"{profile_value} mapping exposes mutable global state",
        )

    STATIC_MAPPING_EVIDENCE.update(
        evidence_kind="static_ast_canonical_mapping_consumer",
        source=str(WRAPPER_PATH.relative_to(REPO_ROOT)),
        profiles=list(EXISTING_PROFILE_VALUES),
        exact_key_value_order=True,
        wrapper_imported=False,
    )


def test_existing_training_semantics_and_corruption_guards() -> None:
    for profile_value in EXISTING_PROFILE_VALUES:
        resolved = _resolve(profile_value)
        serialized = CONTRACT.resolved_assignment_profile_to_mapping(resolved)
        _assert(
            serialized["training_semantic_contract"]
            == EXPECTED_EXISTING_TRAINING_SEMANTICS[profile_value],
            f"{profile_value} training semantic identity changed",
        )

    legacy = _resolve("legacy")

    class ContractVersionImpostor(str):
        pass

    corruptions = (
        {
            "profile_contract_version": ContractVersionImpostor(
                PROFILE_CONTRACT_VERSION
            )
        },
        {
            "runtime_route": _enum_member_for_value(
                CONTRACT.AssignmentRuntimeRoute,
                "event_gated_phase_a_interface_only_v1",
            )
        },
        {
            "checkpoint_family": _enum_member_for_value(
                CONTRACT.AssignmentCheckpointFamily,
                "none",
            )
        },
        {
            "training_support": _enum_member_for_value(
                CONTRACT.AssignmentProfileSupport,
                "normal",
            )
        },
        {
            "playback_support": _enum_member_for_value(
                CONTRACT.AssignmentProfileSupport,
                "allowed",
            )
        },
        {
            "runtime_readiness": _enum_member_for_value(
                CONTRACT.AssignmentRuntimeReadiness,
                "interface_only",
            )
        },
        {
            "training_semantic_contract": replace(
                legacy.training_semantic_contract,
                actor_buffer_generator="corrupt_generator",
            )
        },
    )
    for changes in corruptions:
        _expect_raises(
            lambda changes=changes: replace(legacy, **changes),
            CONTRACT.InvalidAssignmentProfileError,
            "expected",
            "actual",
        )


def test_event_interface_only_semantic_identity_and_serialization() -> None:
    event_profile = _resolve("event_gated_local_mrta")
    target = event_profile.event_gated_target_semantics
    training = target.training_semantic_contract
    expected_target_fields = (
        "contract_version",
        "actor_schema_version",
        "shared_schema_version",
        "shared_construction_mode",
        "mask_contract_version",
        "budget_release_contract",
        "policy_sequence_route",
        "training_semantic_contract",
    )
    expected_training_fields = (
        "contract_version",
        "algorithm_name",
        "state_type",
        "share_param",
        "use_recurrent_policy",
        "use_naive_recurrent_policy",
        "actor_buffer_generator",
        "serialization_mode",
        "save_entire_model",
        "installed_harl_mutable",
    )
    _assert(tuple(field.name for field in fields(type(target))) == expected_target_fields, "event target fields changed")
    _assert(
        tuple(field.name for field in fields(type(training))) == expected_training_fields,
        "training semantic fields changed",
    )
    for instance, label in ((target, "event target"), (training, "training semantic")):
        _assert(is_dataclass(instance), f"{label} is not a dataclass")
        _assert(not hasattr(instance, "__dict__"), f"{label} is not slots-based")
        first_field = fields(type(instance))[0].name
        _expect_raises(
            lambda instance=instance, first_field=first_field: setattr(instance, first_field, "mutated"),
            (FrozenInstanceError, AttributeError),
        )

    serialized = CONTRACT.resolved_assignment_profile_to_mapping(event_profile)
    _assert(isinstance(serialized, dict), "resolved mapping helper must return a primitive dict")
    _assert_primitive_mapping(serialized, "event mapping")
    _assert(serialized == EVENT_SERIALIZED_MAPPING_FORMAL, "event semantic mapping changed")
    _assert(
        tuple(serialized) == tuple(EVENT_SERIALIZED_MAPPING_FORMAL),
        "event semantic top-level mapping order changed",
    )
    _assert(
        tuple(serialized["event_gated_target_semantics"])
        == tuple(EVENT_SERIALIZED_MAPPING_FORMAL["event_gated_target_semantics"]),
        "event target mapping order changed",
    )
    serialized_keys = set(serialized)
    serialized_keys.update(serialized["event_gated_target_semantics"])
    _assert(
        not (serialized_keys & FORBIDDEN_EVENT_KEYS),
        f"event mapping exposes old runtime keys: {sorted(serialized_keys & FORBIDDEN_EVENT_KEYS)}",
    )
    serialized["profile_name"] = "corrupt"
    _assert(
        CONTRACT.resolved_assignment_profile_to_mapping(event_profile) == EVENT_SERIALIZED_MAPPING_FORMAL,
        "serialization output aliases global/resolved state",
    )


def _contains_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(candidate, ast.Name) and candidate.id == name for candidate in ast.walk(node))


def _is_sys_modules_attribute(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
        and node.attr == "modules"
    )


def _sys_modules_store_slices(tree: ast.AST) -> list[ast.AST]:
    result: list[ast.AST] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Subscript)
                and _is_sys_modules_attribute(target.value)
            ):
                result.append(target.slice)
    return result


def _canonical_child_source() -> str:
    return r'''
import ast
import contextlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import sys
from typing import get_args

canonical_name = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
bare_name = "assignment_profile_contract"
module_path = Path(sys.argv[1]).resolve()
cwd_path = Path.cwd().resolve()
module_parent = module_path.parent

def directory_snapshot(root):
    entries = []
    for path in root.rglob("*"):
        stat = path.stat()
        entries.append(
            (
                str(path.relative_to(root)),
                path.is_dir(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return tuple(sorted(entries))

def source_module_keys():
    keys = []
    for key, candidate in tuple(sys.modules.items()):
        candidate_path = getattr(candidate, "__file__", None)
        if not isinstance(candidate_path, str):
            continue
        try:
            same_source = Path(candidate_path).resolve() == module_path
        except (OSError, RuntimeError):
            same_source = False
        if same_source:
            keys.append(key)
    return tuple(sorted(keys))

random_before = random.getstate()
environment_before = dict(os.environ)
cwd_before = os.getcwd()
sys_path_before = tuple(sys.path)
logger_names_before = tuple(sorted(logging.Logger.manager.loggerDict))
root_handlers_before = tuple(id(handler) for handler in logging.getLogger().handlers)
files_before = (
    directory_snapshot(cwd_path),
    directory_snapshot(module_parent),
)
captured_stdout = io.StringIO()
captured_stderr = io.StringIO()

with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
    spec = importlib.util.spec_from_file_location(canonical_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create canonical module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[canonical_name] = module
    spec.loader.exec_module(module)

    profile_enum = module.AssignmentProfileName
    origin_enum = module.AssignmentProfileResolutionOrigin
    formal_origin = next(member for member in origin_enum if member.value == "formal_entrypoint")
    for profile_member in profile_enum:
        module.normalize_assignment_profile_name(profile_member)
        module.normalize_assignment_profile_name(f" {profile_member.value} ")
        resolved = module.resolve_assignment_profile(profile_member, formal_origin)
        module.resolved_assignment_profile_to_mapping(resolved)
    module.get_assignment_profile_registry()
    module.validate_assignment_profile_registry()

    consumer_module = sys.modules[canonical_name]
    event_member = next(member for member in profile_enum if member.value == "event_gated_local_mrta")
    event_profile = module.resolve_assignment_profile(event_member, formal_origin)
    producer_class = module.ResolvedEventGatedAssignmentProfile
    consumer_class = consumer_module.ResolvedEventGatedAssignmentProfile
    producer_enum = module.AssignmentProfileName
    consumer_enum = consumer_module.AssignmentProfileName
    producer_exception = module.AssignmentProfileRouteError
    consumer_exception = consumer_module.AssignmentProfileRouteError

    bad_spec = importlib.util.spec_from_file_location(bare_name, module_path)
    if bad_spec is None or bad_spec.loader is None:
        raise RuntimeError("could not create wrong-key module spec")
    bad_module = importlib.util.module_from_spec(bad_spec)
    try:
        bad_spec.loader.exec_module(bad_module)
    except (ImportError, RuntimeError) as exc:
        wrong_key_error_type = type(exc).__name__
        wrong_key_error = str(exc)
    else:
        raise AssertionError("wrong-key source execution did not fail")

public_type_names = (
    "AssignmentProfileName",
    "AssignmentRuntimeRoute",
    "AssignmentCheckpointFamily",
    "AssignmentProfileSupport",
    "AssignmentRuntimeReadiness",
    "AssignmentProfileResolutionOrigin",
    "TrainingSemanticContract",
    "EventGatedTargetSemantics",
    "ResolvedExistingAssignmentProfile",
    "ResolvedEventGatedAssignmentProfile",
    "AssignmentProfileContractError",
    "ProfileResolutionError",
    "UnknownAssignmentProfileError",
    "InvalidAssignmentProfileError",
    "AssignmentProfileRegistryError",
    "AssignmentProfileRouteError",
    "CanonicalModuleIdentityError",
)
public_type_modules = {
    name: getattr(module, name).__module__
    for name in public_type_names
}
blocked_prefixes = ("isaaclab", "omni", "pxr", "harl", "torch", "numpy")
blocked_modules = sorted(
    name
    for name in sys.modules
    if name != canonical_name
    and (name.startswith(blocked_prefixes) or "assignment_checkpoint" in name)
)
evidence = {
    "module_name": module.__name__,
    "module_key_present": canonical_name in sys.modules,
    "source_module_keys": source_module_keys(),
    "bare_key_present": bare_name in sys.modules,
    "public_type_modules": public_type_modules,
    "producer_class_is_consumer_class": producer_class is consumer_class,
    "producer_enum_is_consumer_enum": producer_enum is consumer_enum,
    "producer_exception_is_consumer_exception": producer_exception is consumer_exception,
    "strict_isinstance": isinstance(event_profile, consumer_class),
    "union_args_exact": get_args(module.ResolvedAssignmentProfile)
        == (module.ResolvedExistingAssignmentProfile, module.ResolvedEventGatedAssignmentProfile),
    "wrong_key_blocked": True,
    "wrong_key_error_type": wrong_key_error_type,
    "wrong_key_error": wrong_key_error,
    "wrong_key_public_types_created": sorted(set(public_type_names) & set(bad_module.__dict__)),
    "random_unchanged": random.getstate() == random_before,
    "environment_unchanged": dict(os.environ) == environment_before,
    "cwd_unchanged": os.getcwd() == cwd_before,
    "sys_path_unchanged": tuple(sys.path) == sys_path_before,
    "logger_names_unchanged": tuple(sorted(logging.Logger.manager.loggerDict)) == logger_names_before,
    "root_handlers_unchanged": tuple(id(handler) for handler in logging.getLogger().handlers)
        == root_handlers_before,
    "files_unchanged": (
        directory_snapshot(cwd_path),
        directory_snapshot(module_parent),
    ) == files_before,
    "blocked_modules": blocked_modules,
    "captured_stdout": captured_stdout.getvalue(),
    "captured_stderr": captured_stderr.getvalue(),
}
print(json.dumps(evidence, sort_keys=True))
'''


def test_canonical_module_identity_clean_child_and_side_effects() -> None:
    child_source = _canonical_child_source()
    child_tree = ast.parse(child_source, filename="<assignment-profile-contract-child>")
    child_stores = _sys_modules_store_slices(child_tree)
    _assert(len(child_stores) == 1, "child harness must register exactly one module key")
    _assert(
        isinstance(child_stores[0], ast.Name) and child_stores[0].id == "canonical_name",
        "child harness registration is not the canonical key",
    )
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", child_source, str(CONTRACT_PATH.resolve())],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"canonical child failed: stdout={completed.stdout!r}, stderr={completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(lines, "canonical child emitted no JSON evidence")
    evidence = json.loads(lines[-1])
    _assert(evidence["module_name"] == CANONICAL_MODULE, "canonical module __name__ changed")
    _assert(evidence["module_key_present"], "canonical module key is absent")
    _assert(evidence["source_module_keys"] == [CANONICAL_MODULE], "target source has multiple module keys")
    _assert(not evidence["bare_key_present"], "bare module key was registered")
    _assert(
        set(evidence["public_type_modules"].values()) == {CANONICAL_MODULE},
        "public identity-bearing types have noncanonical __module__",
    )
    for key in (
        "producer_class_is_consumer_class",
        "producer_enum_is_consumer_enum",
        "producer_exception_is_consumer_exception",
        "strict_isinstance",
        "union_args_exact",
        "wrong_key_blocked",
        "random_unchanged",
        "environment_unchanged",
        "cwd_unchanged",
        "sys_path_unchanged",
        "logger_names_unchanged",
        "root_handlers_unchanged",
        "files_unchanged",
    ):
        _assert(evidence[key], f"child evidence failed: {key}")
    _assert(
        evidence["wrong_key_error_type"] in {"ImportError", "RuntimeError"},
        "pre-declaration guard did not use a built-in import/runtime error",
    )
    for required_text in (CANONICAL_MODULE, BARE_MODULE, "purpose"):
        _assert(required_text in evidence["wrong_key_error"], f"guard error lacks {required_text!r}")
    _assert(
        evidence["wrong_key_public_types_created"] == [],
        "wrong-key execution created a second identity-bearing type family",
    )
    _assert(evidence["blocked_modules"] == [], f"pure child imported forbidden modules: {evidence['blocked_modules']}")
    _assert(not evidence["captured_stdout"], "contract import/resolve wrote stdout")
    _assert(not evidence["captured_stderr"], "contract import/resolve wrote stderr")
    IDENTITY_EVIDENCE.update(
        canonical_module=evidence["module_name"],
        sole_source_key=evidence["source_module_keys"],
        producer_class_is_consumer_class=evidence["producer_class_is_consumer_class"],
        producer_enum_is_consumer_enum=evidence["producer_enum_is_consumer_enum"],
        producer_exception_is_consumer_exception=evidence["producer_exception_is_consumer_exception"],
        strict_isinstance=evidence["strict_isinstance"],
        wrong_key_blocked_before_types=not evidence["wrong_key_public_types_created"],
    )
    SIDE_EFFECT_EVIDENCE.update(
        random_unchanged=evidence["random_unchanged"],
        environment_unchanged=evidence["environment_unchanged"],
        cwd_unchanged=evidence["cwd_unchanged"],
        sys_path_unchanged=evidence["sys_path_unchanged"],
        logger_unchanged=evidence["logger_names_unchanged"] and evidence["root_handlers_unchanged"],
        files_unchanged=evidence["files_unchanged"],
        forbidden_modules_absent=not evidence["blocked_modules"],
    )


def test_contract_source_ast_import_guard_and_no_alias() -> None:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONTRACT_PATH))
    class_defs = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    _assert(class_defs, "contract source has no public type declarations")
    first_class_line = min(node.lineno for node in class_defs)
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and _contains_name(node.test, "__name__")
        and any(isinstance(candidate, ast.Raise) for candidate in ast.walk(node))
    ]
    _assert(len(guards) == 1, "canonical __name__ guard is absent or ambiguous")
    _assert(guards[0].lineno < first_class_line, "canonical guard occurs after a type declaration")
    _assert(CANONICAL_MODULE in source, "canonical module key literal is absent")

    target_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            target_imports.extend(alias for alias in node.names if alias.name == BARE_MODULE)
        elif isinstance(node, ast.ImportFrom) and node.module == BARE_MODULE:
            target_imports.append(node)
    _assert(not target_imports, "contract source imports itself through the bare key")
    _assert(
        not any(_is_sys_modules_attribute(node) for node in ast.walk(tree)),
        "contract source accesses sys.modules instead of enforcing a canonical key",
    )

    forbidden_import_roots = {
        "isaaclab",
        "isaaclab_tasks",
        "omni",
        "pxr",
        "harl",
        "torch",
        "numpy",
        "random",
        "logging",
        "os",
        "pathlib",
        "shutil",
        "tempfile",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    _assert(
        not (imported_roots & forbidden_import_roots),
        f"contract imports forbidden roots: {sorted(imported_roots & forbidden_import_roots)}",
    )
    _assert(
        not any(
            isinstance(node, ast.Try)
            and any(
                handler.type is None
                or (isinstance(handler.type, ast.Name) and handler.type.id == "ImportError")
                for handler in node.handlers
            )
            and any(isinstance(candidate, (ast.Import, ast.ImportFrom)) for candidate in ast.walk(node))
            for node in ast.walk(tree)
        ),
        "contract source contains a relative-to-bare import fallback",
    )
    forbidden_calls = {
        "open",
        "chdir",
        "putenv",
        "unsetenv",
        "seed",
        "getLogger",
        "basicConfig",
        "write_text",
        "write_bytes",
        "touch",
        "mkdir",
        "unlink",
        "rmdir",
        "rename",
        "replace",
        "remove",
        "makedirs",
        "removedirs",
        "copy",
        "copy2",
        "copyfile",
        "move",
        "rmtree",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    _assert(
        not ((called_names | called_attributes) & forbidden_calls),
        f"contract calls a forbidden side-effect API: {sorted((called_names | called_attributes) & forbidden_calls)}",
    )

    test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    test_stores = _sys_modules_store_slices(test_tree)
    _assert(len(test_stores) == 1, "test harness registers more than one module key")
    _assert(
        isinstance(test_stores[0], ast.Name) and test_stores[0].id == "CANONICAL_MODULE",
        "test harness registration is not canonical",
    )


def test_public_type_identity_in_current_canonical_harness() -> None:
    _assert(CONTRACT.__name__ == CANONICAL_MODULE, "current harness module name is noncanonical")
    _assert(sys.modules.get(CANONICAL_MODULE) is CONTRACT, "canonical cache does not hold the loaded module")
    _assert(BARE_MODULE not in sys.modules, "bare contract module key is active")
    for name in PUBLIC_ENUM_NAMES:
        value = getattr(CONTRACT, name)
        _assert(issubclass(value, Enum), f"{name} is not an enum")
        _assert(value.__module__ == CANONICAL_MODULE, f"{name} has noncanonical __module__")
    for name in PUBLIC_DATACLASS_NAMES:
        value = getattr(CONTRACT, name)
        _assert(is_dataclass(value), f"{name} is not a dataclass")
        _assert(value.__module__ == CANONICAL_MODULE, f"{name} has noncanonical __module__")
    for name in PUBLIC_EXCEPTION_NAMES:
        value = getattr(CONTRACT, name)
        _assert(issubclass(value, BaseException), f"{name} is not an exception")
        _assert(value.__module__ == CANONICAL_MODULE, f"{name} has noncanonical __module__")


def test_scenario_vocabulary_normalization_and_primitive_ast_boundary() -> None:
    class StringSubclass(str):
        pass

    vocabulary = SCENARIO_CONFIG.SUPPORTED_ASSIGNMENT_LIFECYCLE_PROFILES
    _assert(type(vocabulary) is tuple, "scenario profile vocabulary must be an exact tuple")
    _assert(vocabulary == PROFILE_VALUES, "scenario profile vocabulary/order differs from the A1a golden")
    _assert(
        vocabulary == _enum_values(CONTRACT.AssignmentProfileName),
        "scenario primitive vocabulary/order differs from the A1a enum",
    )
    _assert(len(vocabulary) == len(set(vocabulary)), "scenario profile vocabulary contains duplicates")
    try:
        vocabulary[0] = "mutation_probe"
    except TypeError:
        pass
    else:
        raise AssertionError("scenario profile vocabulary is mutable")

    for value in PROFILE_VALUES:
        normalized = SCENARIO_CONFIG.normalize_assignment_lifecycle_profile_primitive(
            f"  {value}  ",
            source="test.source",
        )
        _assert(type(normalized) is str and normalized == value, f"scenario normalization failed for {value}")

    for raw_value in (
        "",
        "   ",
        "Legacy",
        "LIFECYCLE_CONTRACT_C",
        "contract_c",
        "event-gated-local-mrta",
        None,
        1,
        True,
        _enum_member_for_value(CONTRACT.AssignmentProfileName, "legacy"),
        StringSubclass("legacy"),
    ):
        normalized = raw_value.strip() if type(raw_value) is str else None
        _expect_raises(
            lambda raw_value=raw_value: SCENARIO_CONFIG.normalize_assignment_lifecycle_profile_primitive(
                raw_value,
                source="test.invalid_source",
            ),
            ValueError,
            SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_INVALID_ERROR,
            "test.invalid_source",
            f"raw={raw_value!r}",
            f"normalized={normalized!r}",
            f"allowed={PROFILE_VALUES!r}",
        )

    source = SCENARIO_CONFIG_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SCENARIO_CONFIG_PATH))
    forbidden_contract_names = {
        "assignment_profile_contract",
        "AssignmentProfileName",
        "ResolvedAssignmentProfile",
        "ResolvedExistingAssignmentProfile",
        "ResolvedEventGatedAssignmentProfile",
    }
    _assert(
        not {name for name in forbidden_contract_names if name in source},
        "scenario source references an A1a contract/type name",
    )
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    _assert(
        not any("assignment_profile_contract" in name for name in imported_modules),
        "scenario source imports assignment_profile_contract",
    )
    identity_class_defs: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {
            base.id
            for base in node.bases
            if isinstance(base, ast.Name)
        } | {
            base.attr
            for base in node.bases
            if isinstance(base, ast.Attribute)
        }
        decorator_names = {
            decorator.id
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Name)
        } | {
            decorator.attr
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Attribute)
        }
        if base_names & {"Enum", "Exception", "BaseException", "ValueError", "RuntimeError"}:
            identity_class_defs.append(node.name)
        if decorator_names & {"dataclass"}:
            identity_class_defs.append(node.name)
    _assert(
        not identity_class_defs,
        f"scenario source declares enum/dataclass/custom exception identities: {identity_class_defs}",
    )
    _assert(
        not any(_is_sys_modules_attribute(node) for node in ast.walk(tree)),
        "scenario source accesses sys.modules",
    )
    referenced_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    _assert(
        not (forbidden_contract_names & referenced_names),
        f"scenario AST references contract types: {sorted(forbidden_contract_names & referenced_names)}",
    )
    _assert(
        not any(
            isinstance(node, ast.Try)
            and any(
                handler.type is None
                or (isinstance(handler.type, ast.Name) and handler.type.id == "ImportError")
                for handler in node.handlers
            )
            and any(
                isinstance(candidate, (ast.Import, ast.ImportFrom))
                and (
                    (
                        isinstance(candidate, ast.Import)
                        and any("assignment_profile_contract" in alias.name for alias in candidate.names)
                    )
                    or (
                        isinstance(candidate, ast.ImportFrom)
                        and "assignment_profile_contract" in str(candidate.module)
                    )
                )
                for candidate in ast.walk(node)
            )
            for node in ast.walk(tree)
        ),
        "scenario source contains a relative-to-bare assignment profile contract fallback",
    )

    complete_vocabulary_literals: list[ast.AST] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            continue
        string_values = [
            element.value
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
        if len(string_values) == len(node.elts) == len(PROFILE_VALUES) and set(string_values) == set(PROFILE_VALUES):
            complete_vocabulary_literals.append(node)
    _assert(
        len(complete_vocabulary_literals) == 1 and isinstance(complete_vocabulary_literals[0], ast.Tuple),
        "scenario source must contain exactly one five-profile tuple definition",
    )

    function_nodes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    normalizer = function_nodes["normalize_assignment_lifecycle_profile_primitive"]
    _assert(
        any(
            isinstance(node, ast.Name)
            and node.id == "SUPPORTED_ASSIGNMENT_LIFECYCLE_PROFILES"
            for node in ast.walk(normalizer)
        ),
        "scenario normalizer does not consume the single profile tuple",
    )
    for function_name in (
        "resolve_assignment_lifecycle_profile_declaration",
        "validate_assignment_lifecycle_profile_prerequisites",
        "_validate_assignment_lifecycle_args",
    ):
        _assert(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "normalize_assignment_lifecycle_profile_primitive"
                for node in ast.walk(function_nodes[function_name])
            ),
            f"{function_name} bypasses the shared primitive normalizer",
        )
    _assert(
        any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "resolve_assignment_lifecycle_profile_declaration"
            for node in ast.walk(function_nodes["_validate_assignment_lifecycle_metadata"])
        ),
        "scenario metadata validation bypasses declaration conflict/normalization authority",
    )

    SCENARIO_EVIDENCE.update(
        primitive_vocabulary=vocabulary,
        a1a_order_equal=True,
        primitive_only_ast=True,
        single_vocabulary_tuple=True,
    )


def test_scenario_declaration_resolution_matrix_and_provenance() -> None:
    resolve = SCENARIO_CONFIG.resolve_assignment_lifecycle_profile_declaration
    top_source = SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_TOP_LEVEL_SOURCE
    nested_source = SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_NESTED_SOURCE
    provenance_values = SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PROVENANCE_VALUES
    _assert(type(provenance_values) is tuple, "scenario provenance vocabulary must be an exact tuple")
    _assert(
        provenance_values == ("ABSENT", "TOP_LEVEL", "NESTED", "TOP_LEVEL_AND_NESTED"),
        f"scenario provenance vocabulary/order changed: {provenance_values!r}",
    )
    _assert(len(provenance_values) == len(set(provenance_values)), "scenario provenance values contain duplicates")

    absent = resolve({})
    _assert(absent == (None, "ABSENT", ()), f"absent declaration changed: {absent!r}")
    top_only = resolve({"assignment_lifecycle_profile": " lifecycle_ablation "})
    _assert(
        top_only
        == (
            "lifecycle_ablation",
            "TOP_LEVEL",
            ((top_source, " lifecycle_ablation ", "lifecycle_ablation"),),
        ),
        f"top-only resolution changed: {top_only!r}",
    )
    nested_only = resolve({"assignment_lifecycle": {"profile": "event_gated_local_mrta"}})
    _assert(
        nested_only
        == (
            "event_gated_local_mrta",
            "NESTED",
            ((nested_source, "event_gated_local_mrta", "event_gated_local_mrta"),),
        ),
        f"nested-only resolution changed: {nested_only!r}",
    )
    both_same_config = {
        "assignment_lifecycle_profile": " lifecycle_contract_c",
        "assignment_lifecycle": {"profile": "lifecycle_contract_c "},
    }
    both_same_before = json.dumps(both_same_config, sort_keys=True)
    both_same = resolve(both_same_config)
    _assert(
        both_same
        == (
            "lifecycle_contract_c",
            "TOP_LEVEL_AND_NESTED",
            (
                (top_source, " lifecycle_contract_c", "lifecycle_contract_c"),
                (nested_source, "lifecycle_contract_c ", "lifecycle_contract_c"),
            ),
        ),
        f"equal dual declaration changed: {both_same!r}",
    )
    _assert(resolve(both_same_config) == both_same, "dual-source resolution is nondeterministic")
    _assert(
        json.dumps(both_same_config, sort_keys=True) == both_same_before,
        "valid dual-source resolution mutated config",
    )
    for result in (absent, top_only, nested_only, both_same):
        _assert_primitive_mapping(result, "scenario declaration result")

    conflict_config = {
        "assignment_lifecycle_profile": " legacy ",
        "assignment_lifecycle": {"profile": "lifecycle_ablation"},
    }
    conflict_before = json.dumps(conflict_config, sort_keys=True)
    _expect_raises(
        lambda: resolve(conflict_config),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_CONFLICT_ERROR,
        top_source,
        "top_level_raw=' legacy '",
        "top_level_canonical='legacy'",
        nested_source,
        "nested_raw='lifecycle_ablation'",
        "nested_canonical='lifecycle_ablation'",
    )
    _assert(json.dumps(conflict_config, sort_keys=True) == conflict_before, "conflict resolution mutated config")

    invalid_cases = (
        ({"assignment_lifecycle_profile": "unknown"}, top_source),
        ({"assignment_lifecycle": {"profile": "unknown"}}, nested_source),
        (
            {
                "assignment_lifecycle_profile": "unknown",
                "assignment_lifecycle": {"profile": "legacy"},
            },
            top_source,
        ),
        (
            {
                "assignment_lifecycle_profile": "legacy",
                "assignment_lifecycle": {"profile": "unknown"},
            },
            nested_source,
        ),
        (
            {
                "assignment_lifecycle_profile": "",
                "assignment_lifecycle": {"profile": "legacy"},
            },
            top_source,
        ),
        ({"assignment_lifecycle": {"profile": "   "}}, nested_source),
        (
            {
                "assignment_lifecycle_profile": "legacy",
                "assignment_lifecycle": {"profile": " "},
            },
            nested_source,
        ),
        ({"assignment_lifecycle_profile": "Legacy"}, top_source),
        ({"assignment_lifecycle": {"profile": "contract_c"}}, nested_source),
        ({"assignment_lifecycle_profile": None}, top_source),
        ({"assignment_lifecycle": {"profile": None}}, nested_source),
        ({"assignment_lifecycle_profile": 3}, top_source),
        ({"assignment_lifecycle": {"profile": False}}, nested_source),
    )
    for invalid_config, expected_source in invalid_cases:
        before = repr(invalid_config)
        _expect_raises(
            lambda invalid_config=invalid_config: resolve(invalid_config),
            ValueError,
            SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_INVALID_ERROR,
            expected_source,
            "raw=",
            "normalized=",
            f"allowed={PROFILE_VALUES!r}",
        )
        _assert(repr(invalid_config) == before, f"invalid resolution mutated {invalid_config!r}")

    SCENARIO_EVIDENCE.update(
        source_resolution_matrix="passed",
        provenance_values=SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PROVENANCE_VALUES,
        conflicts_fail_fast=True,
    )


class _FakeScenarioEnvCfg:
    assignment_lifecycle_profile = "legacy"

    def __init__(self) -> None:
        self.existing_marker = "unchanged"


def test_scenario_conditional_env_apply_and_failure_atomicity() -> None:
    apply_config = SCENARIO_CONFIG.apply_scenario_config_to_env_cfg
    defaults_from_config = SCENARIO_CONFIG.smoke_defaults_from_config

    absent_env = _FakeScenarioEnvCfg()
    absent_before = json.dumps(vars(absent_env), sort_keys=True)
    returned = apply_config(absent_env, {})
    _assert(returned is absent_env, "absent apply did not return the same env cfg")
    _assert(json.dumps(vars(absent_env), sort_keys=True) == absent_before, "absent apply changed primitive state")
    _assert(
        "assignment_lifecycle_profile" not in vars(absent_env),
        "absent apply injected an assignment_lifecycle_profile instance field",
    )
    _assert(absent_env.assignment_lifecycle_profile == "legacy", "absent apply changed the class default")
    absent_namespace_env = _FakeScenarioEnvCfg()
    absent_namespace_before = dict(vars(absent_namespace_env))
    apply_config(absent_namespace_env, argparse.Namespace())
    _assert(vars(absent_namespace_env) == absent_namespace_before, "absent Namespace apply changed env cfg")
    _assert(
        "assignment_lifecycle_profile" not in vars(absent_namespace_env),
        "absent Namespace apply injected a profile instance field",
    )

    nonempty_absent_config = {
        "scenario_name": "existing_scenario_without_profile",
        "assignment_cooldown": {"enabled": False},
        "assignment_redirect_guardrail": {"enabled": False},
    }
    nonempty_absent_defaults = defaults_from_config(nonempty_absent_config)
    _assert(
        nonempty_absent_defaults
        == {
            "scenario_name": "existing_scenario_without_profile",
            "assignment_cooldown_enabled": False,
            "assignment_redirect_guardrail_enabled": False,
        },
        f"nonempty profile-absent defaults changed: {nonempty_absent_defaults!r}",
    )
    nonempty_absent_env = _FakeScenarioEnvCfg()
    apply_config(nonempty_absent_env, argparse.Namespace(**nonempty_absent_defaults))
    _assert(
        vars(nonempty_absent_env)
        == {
            "existing_marker": "unchanged",
            "scenario_name": "existing_scenario_without_profile",
            "assignment_cooldown_enabled": False,
            "assignment_redirect_guardrail_enabled": False,
        },
        f"nonempty profile-absent apply changed unrelated state: {vars(nonempty_absent_env)!r}",
    )
    _assert(
        "assignment_lifecycle_profile" not in vars(nonempty_absent_env),
        "nonempty profile-absent scenario injected a profile instance field",
    )

    existing_defaults = defaults_from_config(
        {"assignment_lifecycle_profile": " lifecycle_ablation "}
    )
    _assert(
        existing_defaults["assignment_lifecycle_profile"] == "lifecycle_ablation",
        "existing profile default was not canonicalized",
    )
    existing_env = _FakeScenarioEnvCfg()
    apply_config(existing_env, argparse.Namespace(**existing_defaults))
    _assert(
        type(vars(existing_env)["assignment_lifecycle_profile"]) is str,
        "env cfg received a non-primitive profile value",
    )
    _assert(
        existing_env.assignment_lifecycle_profile == "lifecycle_ablation",
        "explicit existing profile was not applied",
    )
    _assert(
        vars(existing_env)
        == {
            "existing_marker": "unchanged",
            "assignment_lifecycle_profile": "lifecycle_ablation",
        },
        f"existing profile apply leaked fields: {vars(existing_env)!r}",
    )

    stripped_namespace_env = _FakeScenarioEnvCfg()
    apply_config(
        stripped_namespace_env,
        argparse.Namespace(assignment_lifecycle_profile=" legacy "),
    )
    _assert(
        vars(stripped_namespace_env)
        == {
            "existing_marker": "unchanged",
            "assignment_lifecycle_profile": "legacy",
        },
        "explicit Namespace profile was not canonicalized/applied exactly",
    )

    event_defaults = defaults_from_config(
        {"assignment_lifecycle": {"profile": " event_gated_local_mrta "}}
    )
    event_env = _FakeScenarioEnvCfg()
    apply_config(event_env, event_defaults)
    first_event_state = json.dumps(vars(event_env), sort_keys=True)
    apply_config(event_env, event_defaults)
    _assert(json.dumps(vars(event_env), sort_keys=True) == first_event_state, "repeated event apply is nondeterministic")
    _assert(
        type(event_env.assignment_lifecycle_profile) is str
        and event_env.assignment_lifecycle_profile == "event_gated_local_mrta",
        "event profile was not applied as an exact built-in string",
    )
    _assert(
        vars(event_env)
        == {
            "existing_marker": "unchanged",
            "assignment_lifecycle_profile": "event_gated_local_mrta",
        },
        f"event apply leaked identity/provenance fields: {vars(event_env)!r}",
    )
    _assert_primitive_mapping(vars(event_env), "event env primitive state")

    conflict_env = _FakeScenarioEnvCfg()
    conflict_before = json.dumps(vars(conflict_env), sort_keys=True)
    _expect_raises(
        lambda: defaults_from_config(
            {
                "assignment_lifecycle_profile": "legacy",
                "assignment_lifecycle": {"profile": "lifecycle_ablation"},
            }
        ),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_CONFLICT_ERROR,
    )
    _assert(json.dumps(vars(conflict_env), sort_keys=True) == conflict_before, "conflict path mutated env cfg")

    invalid_env = _FakeScenarioEnvCfg()
    invalid_before = json.dumps(vars(invalid_env), sort_keys=True)
    _expect_raises(
        lambda: apply_config(
            invalid_env,
            {
                "scenario_name": "must_not_apply",
                "assignment_lifecycle_profile": "Legacy",
            },
        ),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_INVALID_ERROR,
    )
    _assert(json.dumps(vars(invalid_env), sort_keys=True) == invalid_before, "invalid profile partially mutated env cfg")

    prerequisite_env = _FakeScenarioEnvCfg()
    prerequisite_before = json.dumps(vars(prerequisite_env), sort_keys=True)
    _expect_raises(
        lambda: apply_config(
            prerequisite_env,
            {
                "scenario_name": "must_not_apply",
                "assignment_lifecycle_profile": "legacy",
                "assignment_lifecycle_resolver_enabled": True,
            },
        ),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PREREQUISITE_ERROR,
        "assignment_lifecycle_resolver_enabled",
    )
    _assert(
        json.dumps(vars(prerequisite_env), sort_keys=True) == prerequisite_before,
        "prerequisite failure partially mutated env cfg",
    )

    SCENARIO_EVIDENCE.update(
        absent_instance_field_injected=False,
        absent_primitive_state_exact=True,
        explicit_existing_applied=True,
        explicit_event_applied=True,
        apply_failure_atomic=True,
    )


def test_scenario_existing_profile_prerequisite_matrix_and_no_mutation() -> None:
    validate = SCENARIO_CONFIG.validate_assignment_lifecycle_profile_prerequisites

    valid_settings = {
        "legacy": {
            "assignment_lifecycle_resolver_enabled": False,
        },
        "lifecycle_ablation": {
            "assignment_lifecycle_resolver_enabled": False,
            "assignment_cooldown_enabled": False,
            "assignment_redirect_guardrail_enabled": False,
            "assignment_failed_pair_memory_enabled": False,
        },
        "lifecycle_contract_c": {
            "assignment_lifecycle_resolver_enabled": False,
            "assignment_cooldown_enabled": True,
            "assignment_cooldown_trigger_mode": "budget",
            "assignment_cooldown_duration_steps": 20,
            "assignment_cooldown_apply_to_action_mask": False,
            "assignment_redirect_guardrail_enabled": False,
            "assignment_failed_pair_memory_enabled": False,
        },
        "diagnostics_hidden_state": {
            "assignment_lifecycle_resolver_enabled": True,
        },
    }
    for profile, settings in valid_settings.items():
        before = json.dumps(settings, sort_keys=True)
        validate(profile, settings, source=f"test.{profile}")
        _assert(json.dumps(settings, sort_keys=True) == before, f"{profile} preflight mutated mapping")
        namespace = argparse.Namespace(**settings)
        namespace_before = dict(vars(namespace))
        validate(profile, namespace, source=f"test.namespace.{profile}")
        _assert(vars(namespace) == namespace_before, f"{profile} preflight mutated namespace")

    SCENARIO_CONFIG.validate_smoke_args(
        argparse.Namespace(
            assignment_lifecycle_profile="legacy",
            assignment_lifecycle_resolver_enabled=False,
        ),
        repo_root=REPO_ROOT,
    )
    _expect_raises(
        lambda: SCENARIO_CONFIG.validate_smoke_args(
            argparse.Namespace(
                assignment_lifecycle_profile="legacy",
                assignment_lifecycle_resolver_enabled=True,
            ),
            repo_root=REPO_ROOT,
        ),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PREREQUISITE_ERROR,
        "assignment_lifecycle_resolver_enabled",
    )

    validate(
        "lifecycle_contract_c",
        {
            **valid_settings["lifecycle_contract_c"],
            "assignment_lifecycle_resolver_enabled": True,
            "assignment_cooldown_trigger_mode": "budget_and_streak",
        },
        source="test.contract_c.alternate",
    )
    contract_without_raw_resolver = dict(valid_settings["lifecycle_contract_c"])
    contract_without_raw_resolver.pop("assignment_lifecycle_resolver_enabled")
    validate(
        "lifecycle_contract_c",
        contract_without_raw_resolver,
        source="test.contract_c.profile_derived_resolver",
    )

    broken_cases = (
        (
            "legacy",
            {**valid_settings["legacy"], "assignment_lifecycle_resolver_enabled": True},
            "assignment_lifecycle_resolver_enabled",
        ),
        (
            "lifecycle_ablation",
            {**valid_settings["lifecycle_ablation"], "assignment_lifecycle_resolver_enabled": True},
            "assignment_lifecycle_resolver_enabled",
        ),
        (
            "lifecycle_ablation",
            {**valid_settings["lifecycle_ablation"], "assignment_cooldown_enabled": True},
            "assignment_cooldown_enabled",
        ),
        (
            "lifecycle_ablation",
            {**valid_settings["lifecycle_ablation"], "assignment_redirect_guardrail_enabled": True},
            "assignment_redirect_guardrail_enabled",
        ),
        (
            "lifecycle_ablation",
            {**valid_settings["lifecycle_ablation"], "assignment_failed_pair_memory_enabled": True},
            "assignment_failed_pair_memory_enabled",
        ),
        (
            "lifecycle_contract_c",
            {**valid_settings["lifecycle_contract_c"], "assignment_cooldown_enabled": False},
            "assignment_cooldown_enabled",
        ),
        (
            "lifecycle_contract_c",
            {**valid_settings["lifecycle_contract_c"], "assignment_cooldown_trigger_mode": "streak"},
            "assignment_cooldown_trigger_mode",
        ),
        (
            "lifecycle_contract_c",
            {**valid_settings["lifecycle_contract_c"], "assignment_cooldown_duration_steps": 0},
            "assignment_cooldown_duration_steps",
        ),
        (
            "lifecycle_contract_c",
            {**valid_settings["lifecycle_contract_c"], "assignment_cooldown_apply_to_action_mask": True},
            "assignment_cooldown_apply_to_action_mask",
        ),
        (
            "lifecycle_contract_c",
            {
                **valid_settings["lifecycle_contract_c"],
                "assignment_redirect_guardrail_enabled": True,
                "assignment_redirect_guardrail_window_steps": 1,
            },
            "assignment_redirect_guardrail_enabled",
        ),
        (
            "lifecycle_contract_c",
            {
                **valid_settings["lifecycle_contract_c"],
                "assignment_failed_pair_memory_enabled": True,
                "assignment_failed_pair_memory_duration_steps": 1,
            },
            "assignment_failed_pair_memory_enabled",
        ),
        (
            "diagnostics_hidden_state",
            {"assignment_lifecycle_resolver_enabled": False},
            "assignment_lifecycle_resolver_enabled",
        ),
        (
            "diagnostics_hidden_state",
            {},
            "assignment_lifecycle_resolver_enabled",
        ),
    )
    for profile, settings, expected_field in broken_cases:
        before = json.dumps(settings, sort_keys=True)
        _expect_raises(
            lambda profile=profile, settings=settings: validate(
                profile,
                settings,
                source=f"test.broken.{profile}",
            ),
            ValueError,
            SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PREREQUISITE_ERROR,
            f"profile={profile!r}",
            expected_field,
            "expected=",
            "actual=",
        )
        _assert(json.dumps(settings, sort_keys=True) == before, f"failed {profile} preflight mutated settings")

    failing_namespace = argparse.Namespace(
        assignment_lifecycle_resolver_enabled=False,
    )
    failing_namespace_before = dict(vars(failing_namespace))
    _expect_raises(
        lambda: validate(
            "diagnostics_hidden_state",
            failing_namespace,
            source="test.broken_namespace.diagnostics_hidden_state",
        ),
        ValueError,
        SCENARIO_CONFIG.ASSIGNMENT_LIFECYCLE_PROFILE_PREREQUISITE_ERROR,
        "assignment_lifecycle_resolver_enabled",
    )
    _assert(vars(failing_namespace) == failing_namespace_before, "failed preflight mutated Namespace")

    event_non_contract_settings = {
        "assignment_lifecycle_resolver_enabled": False,
        "assignment_cooldown_enabled": False,
        "assignment_cooldown_trigger_mode": "streak",
        "assignment_cooldown_duration_steps": 0,
        "assignment_cooldown_apply_to_action_mask": True,
        "assignment_redirect_guardrail_enabled": True,
        "assignment_redirect_guardrail_window_steps": 1,
        "assignment_failed_pair_memory_enabled": True,
        "assignment_failed_pair_memory_duration_steps": 1,
    }
    event_before = json.dumps(event_non_contract_settings, sort_keys=True)
    validate(
        "event_gated_local_mrta",
        event_non_contract_settings,
        source="test.event.interface_only",
    )
    _assert(
        json.dumps(event_non_contract_settings, sort_keys=True) == event_before,
        "event declaration preflight mutated settings",
    )

    for profile, expected_support in (
        ("lifecycle_ablation", "existing_blocked"),
        ("diagnostics_hidden_state", "existing_blocked"),
        ("event_gated_local_mrta", "phase_a_blocked"),
    ):
        resolved = _resolve(profile)
        _assert(
            _serialized_value(resolved.training_support) == expected_support,
            f"{profile} training support was promoted",
        )

    SCENARIO_EVIDENCE.update(
        prerequisite_matrix="passed",
        prerequisite_input_mutation=False,
        contract_c_resolver_authority="profile_derived_effective_true",
        event_contract_c_prerequisites_reused=False,
    )


def _scenario_clean_child_source() -> str:
    return r'''
import contextlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import sys

module_path = Path(sys.argv[1]).resolve()
module_parent = module_path.parent
source_path = str(Path(sys.argv[2]).resolve())
cwd_path = Path.cwd().resolve()

def directory_snapshot(root):
    entries = []
    for path in root.rglob("*"):
        stat = path.stat()
        entries.append(
            (
                str(path.relative_to(root)),
                path.is_dir(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return tuple(sorted(entries))

class FakeEnvCfg:
    assignment_lifecycle_profile = "legacy"

    def __init__(self):
        self.existing_marker = "unchanged"

random_before = random.getstate()
environment_before = dict(os.environ)
cwd_before = os.getcwd()
sys_path_before = tuple(sys.path)
logger_names_before = tuple(sorted(logging.Logger.manager.loggerDict))
root_handlers_before = tuple(id(handler) for handler in logging.getLogger().handlers)
files_before = (
    directory_snapshot(cwd_path),
    directory_snapshot(module_parent),
)
env_cfg = FakeEnvCfg()
env_before = json.dumps(vars(env_cfg), sort_keys=True, separators=(",", ":"))
captured_stdout = io.StringIO()
captured_stderr = io.StringIO()

with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
    spec = importlib.util.spec_from_file_location("phase_a1b_clean_scenario_harness", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create scenario module spec")
    module = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sys.path.insert(0, source_path)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(source_path)
        sys.dont_write_bytecode = previous_dont_write_bytecode

    declaration = module.resolve_assignment_lifecycle_profile_declaration({})
    defaults = module.smoke_defaults_from_config({})
    module.apply_scenario_config_to_env_cfg(env_cfg, defaults)

blocked_prefixes = ("isaaclab", "omni", "pxr", "harl", "torch", "numpy")
blocked_modules = sorted(
    name
    for name in sys.modules
    if name.startswith(blocked_prefixes)
    or "assignment_checkpoint" in name
    or "assignment_profile_contract" in name
)
evidence = {
    "declaration": declaration,
    "defaults": defaults,
    "env_unchanged": json.dumps(vars(env_cfg), sort_keys=True, separators=(",", ":")) == env_before,
    "profile_instance_field_absent": "assignment_lifecycle_profile" not in vars(env_cfg),
    "class_default_legacy": env_cfg.assignment_lifecycle_profile == "legacy",
    "random_unchanged": random.getstate() == random_before,
    "environment_unchanged": dict(os.environ) == environment_before,
    "cwd_unchanged": os.getcwd() == cwd_before,
    "sys_path_unchanged": tuple(sys.path) == sys_path_before,
    "logger_names_unchanged": tuple(sorted(logging.Logger.manager.loggerDict)) == logger_names_before,
    "root_handlers_unchanged": tuple(id(handler) for handler in logging.getLogger().handlers)
        == root_handlers_before,
    "files_unchanged": (
        directory_snapshot(cwd_path),
        directory_snapshot(module_parent),
    ) == files_before,
    "blocked_modules": blocked_modules,
    "captured_stdout": captured_stdout.getvalue(),
    "captured_stderr": captured_stderr.getvalue(),
}
print(json.dumps(evidence, sort_keys=True))
'''


def test_scenario_absent_default_clean_child_side_effect_boundary() -> None:
    child_source = _scenario_clean_child_source()
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                child_source,
                str(SCENARIO_CONFIG_PATH.resolve()),
                str(SCAN_TASK_SOURCE.resolve()),
            ],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"scenario clean child failed: stdout={completed.stdout!r}, stderr={completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(lines, "scenario clean child emitted no JSON evidence")
    evidence = json.loads(lines[-1])
    _assert(evidence["declaration"] == [None, "ABSENT", []], "clean-child absent declaration changed")
    _assert(evidence["defaults"] == {}, "clean-child absent defaults changed")
    for key in (
        "env_unchanged",
        "profile_instance_field_absent",
        "class_default_legacy",
        "random_unchanged",
        "environment_unchanged",
        "cwd_unchanged",
        "sys_path_unchanged",
        "logger_names_unchanged",
        "root_handlers_unchanged",
        "files_unchanged",
    ):
        _assert(evidence[key], f"scenario clean-child evidence failed: {key}")
    _assert(not evidence["blocked_modules"], f"scenario imported forbidden modules: {evidence['blocked_modules']}")
    _assert(not evidence["captured_stdout"], "scenario import/default-off path wrote stdout")
    _assert(not evidence["captured_stderr"], "scenario import/default-off path wrote stderr")
    SCENARIO_EVIDENCE.update(
        clean_child_default_off_exact=True,
        clean_child_files_unchanged=evidence["files_unchanged"],
        clean_child_rng_unchanged=evidence["random_unchanged"],
        clean_child_forbidden_modules_absent=not evidence["blocked_modules"],
    )


def test_historical_module_identity_regression_has_pure_boundary() -> None:
    tree = ast.parse(
        HISTORICAL_IDENTITY_TEST_PATH.read_text(encoding="utf-8"),
        filename=str(HISTORICAL_IDENTITY_TEST_PATH),
    )
    forbidden_roots = {"isaaclab", "omni", "pxr", "harl", "torch", "numpy"}
    imported_roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    _assert(
        not (imported_roots & forbidden_roots),
        f"historical identity regression imports forbidden runtime packages: "
        f"{sorted(imported_roots & forbidden_roots)}",
    )
    docstring = ast.get_docstring(tree) or ""
    _assert("does not import Isaac Lab" in docstring, "historical regression pure-boundary declaration changed")
    _assert("load a checkpoint" in docstring, "historical regression checkpoint boundary declaration changed")


A1A_TESTS = (
    test_profile_vocabulary_and_normalization,
    test_exception_hierarchy_and_context,
    test_registry_exhaustiveness_immutability_and_resolution,
    test_discriminated_union_and_existing_route_guard,
    test_existing_wrapper_mapping_static_golden,
    test_existing_training_semantics_and_corruption_guards,
    test_event_interface_only_semantic_identity_and_serialization,
    test_canonical_module_identity_clean_child_and_side_effects,
    test_contract_source_ast_import_guard_and_no_alias,
    test_public_type_identity_in_current_canonical_harness,
    test_historical_module_identity_regression_has_pure_boundary,
)

A1B_TESTS = (
    test_scenario_vocabulary_normalization_and_primitive_ast_boundary,
    test_scenario_declaration_resolution_matrix_and_provenance,
    test_scenario_conditional_env_apply_and_failure_atomicity,
    test_scenario_existing_profile_prerequisite_matrix_and_no_mutation,
    test_scenario_absent_default_clean_child_side_effect_boundary,
)

TESTS = A1A_TESTS + A1B_TESTS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, str]] = []
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone pure regression runner.
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    failed = [result for result in results if result["status"] == "failed"]
    a1a_names = {test.__name__ for test in A1A_TESTS}
    a1b_names = {test.__name__ for test in A1B_TESTS}
    a1a_results = [result for result in results if result["name"] in a1a_names]
    a1b_results = [result for result in results if result["name"] in a1b_names]
    output = {
        "status": "failed" if failed else "passed",
        "num_tests": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "tests": results,
        "a1a": {
            "num_tests": len(a1a_results),
            "passed": sum(result["status"] == "passed" for result in a1a_results),
            "failed": sum(result["status"] == "failed" for result in a1a_results),
        },
        "a1b": {
            "num_tests": len(a1b_results),
            "passed": sum(result["status"] == "passed" for result in a1b_results),
            "failed": sum(result["status"] == "failed" for result in a1b_results),
        },
        "module_identity_evidence": IDENTITY_EVIDENCE,
        "side_effect_evidence": SIDE_EFFECT_EVIDENCE,
        "existing_mapping_evidence": STATIC_MAPPING_EVIDENCE,
        "scenario_evidence": SCENARIO_EVIDENCE,
        "runtime_boundary": (
            "pure/static A1a identity and A1b primitive-scenario evidence only; "
            "no formal-entrypoint-to-wrapper wiring claim; no Isaac Lab, AppLauncher, "
            "HARL, checkpoint I/O, training, playback, or evaluation"
        ),
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for result in results:
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{result['status'].upper()} {result['name']}{suffix}")
        if IDENTITY_EVIDENCE:
            print(f"canonical module: {IDENTITY_EVIDENCE['canonical_module']}")
            print(f"sole source key: {IDENTITY_EVIDENCE['sole_source_key']}")
            print(
                "ProducerClass is ConsumerClass: "
                f"{IDENTITY_EVIDENCE['producer_class_is_consumer_class']}"
            )
            print(f"strict isinstance: {IDENTITY_EVIDENCE['strict_isinstance']}")
        print(f"{'FAIL' if failed else 'PASS'} {output['passed']}/{output['num_tests']} tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
