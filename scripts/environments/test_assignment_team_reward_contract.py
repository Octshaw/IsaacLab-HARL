"""Pure A5 closeout regressions for the A3-frozen team-reward contract."""

from __future__ import annotations

import argparse
import ast
import contextlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
import hashlib
import importlib.util
import io
import json
import logging
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Mapping

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
MODULE_PATHS = {
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract": (
        TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_contract": (
        TASK_SOURCE / "assignment_event_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_mrta_contract": (
        TASK_SOURCE / "assignment_mrta_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_team_reward_contract": (
        TASK_SOURCE / "assignment_team_reward_contract.py"
    ),
}
CANONICAL_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_team_reward_contract"
)
BARE_MODULE = "assignment_team_reward_contract"
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
PROFILE_MODULE = f"{PACKAGE}.assignment_profile_contract"
DIAGNOSTICS_MODULE = (
    f"{PACKAGE}.assignment_event_gated_diagnostics_contract"
)
EVENT_PROFILE_MODULE = (
    f"{PACKAGE}.assignment_event_profile_schema_contract"
)
CHECKPOINT_V3_MODULE = f"{PACKAGE}.assignment_checkpoint_contract_v3"
PHASE_A5_MODULE_PATHS = {
    PROFILE_MODULE: TASK_SOURCE / "assignment_profile_contract.py",
    DIAGNOSTICS_MODULE: (
        TASK_SOURCE / "assignment_event_gated_diagnostics_contract.py"
    ),
    EVENT_PROFILE_MODULE: (
        TASK_SOURCE / "assignment_event_profile_schema_contract.py"
    ),
    CHECKPOINT_V3_MODULE: (
        TASK_SOURCE / "assignment_checkpoint_contract_v3.py"
    ),
}
OLD_ROUTE_CHILD_MODULE_PATHS = {
    PROFILE_MODULE: TASK_SOURCE / "assignment_profile_contract.py",
    **MODULE_PATHS,
}
RUNTIME_REWARD_SOURCE_PATHS = {
    "environment": TASK_SOURCE / "scan_mobile_manipulator_env.py",
    "wrapper": TASK_SOURCE / "assignment_harl_wrapper.py",
    "training": TASK_SOURCE / "assignment_harl_training.py",
}
V3_INTERFACE_CANONICAL_BYTE_LENGTH = 67794
V3_INTERFACE_SHA256 = (
    "03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a"
)
A3_BASELINE_TEST_GROUP_COUNT = 6
A5_ADDED_TEST_GROUP_COUNT = 6
UNRESOLVED_PARAMETER_ORDER = (
    "top_k_tasks_per_robot",
    "local_robot_cap",
    "local_task_cap",
    "pair_abs_threshold",
    "pair_rel_threshold",
    "component_abs_threshold",
    "component_rel_threshold",
    "transfer_penalty",
    "rejection_penalty_scale",
    "alignment_time_constant",
    "assignment_retry_cadence",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_type: type[BaseException],
    failure_code: str,
) -> BaseException:
    try:
        function()
    except exception_type as exc:
        _assert(
            getattr(exc, "failure_code", None) == failure_code,
            f"wrong failure code: {exc}",
        )
        return exc
    except Exception as exc:
        raise AssertionError(
            f"expected {exception_type.__name__}, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _expect_plain_error(
    function: Callable[[], Any],
    exception_type: type[BaseException],
) -> BaseException:
    try:
        function()
    except exception_type as exc:
        return exc
    except Exception as exc:
        raise AssertionError(
            f"expected {exception_type.__name__}, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _install_namespace_packages() -> None:
    namespaces = (
        ("isaaclab_tasks", TASK_SOURCE.parents[2]),
        ("isaaclab_tasks.direct", TASK_SOURCE.parent),
        (
            "isaaclab_tasks.direct.scan_mobile_manipulator",
            TASK_SOURCE,
        ),
    )
    for name, path in namespaces:
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_canonical_modules() -> dict[str, ModuleType]:
    _install_namespace_packages()
    loaded: dict[str, ModuleType] = {}
    for name, path in MODULE_PATHS.items():
        existing = sys.modules.get(name)
        if existing is not None:
            loaded[name] = existing
            continue
        spec = importlib.util.spec_from_file_location(name, path)
        _assert(spec is not None and spec.loader is not None, f"no spec: {name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(name, None)
            raise
        loaded[name] = module
    return loaded


MODULES = _load_canonical_modules()
MODULE = MODULES[CANONICAL_MODULE]
MRTA = MODULES[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract"
]
_PHASE_A5_MODULE_CACHE: dict[str, ModuleType] | None = None


def _phase_a5_modules() -> dict[str, ModuleType]:
    global _PHASE_A5_MODULE_CACHE
    if _PHASE_A5_MODULE_CACHE is not None:
        return _PHASE_A5_MODULE_CACHE
    _install_namespace_packages()
    loaded: dict[str, ModuleType] = {}
    for name, path in PHASE_A5_MODULE_PATHS.items():
        existing = sys.modules.get(name)
        if existing is not None:
            _assert(
                Path(str(existing.__file__)).resolve() == path.resolve(),
                f"canonical module source mismatch: {name}",
            )
            loaded[name] = existing
            continue
        spec = importlib.util.spec_from_file_location(name, path)
        _assert(spec is not None and spec.loader is not None, f"no spec: {name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(name, None)
            raise
        finally:
            sys.dont_write_bytecode = previous
        loaded[name] = module
    _PHASE_A5_MODULE_CACHE = loaded
    return loaded


def _v3_scale_contract() -> Mapping[str, object]:
    aggregate = _phase_a5_modules()[EVENT_PROFILE_MODULE]
    return aggregate.build_event_gated_scale_contract(
        M=3,
        N=50,
        ordered_agent_names=("robot_0", "robot_1", "robot_2"),
        ordered_task_ids=tuple(range(50)),
        scene_env_spacing=12.0,
        sim_dt_seconds=0.01,
        control_decimation=4,
        physical_control_step_seconds=0.04,
        episode_time_limit_seconds=40.01,
        episode_horizon_steps=1001,
    )


def _semantic_snapshot(value: object) -> object:
    if isinstance(value, Mapping):
        return tuple(
            (key, _semantic_snapshot(item)) for key, item in value.items()
        )
    if type(value) in (tuple, list):
        return tuple(_semantic_snapshot(item) for item in value)  # type: ignore[arg-type]
    return value


def _contract() -> Any:
    unresolved = MRTA.UnresolvedParameterSpec(
        name="rejection_penalty_scale",
        owner_phase="phase_d_e",
        semantic_purpose=(
            "once_per_penalty_eligible_rejected_component"
        ),
    )
    return MODULE.TeamRewardContractSpec(
        rejection_penalty_scale=unresolved
    )


def test_canonical_identity_and_exact_spec() -> dict[str, Any]:
    _assert(MODULE.__name__ == CANONICAL_MODULE, "canonical name changed")
    _assert(
        MODULE.TeamRewardContractSpec.__module__ == CANONICAL_MODULE,
        "spec class has wrong module identity",
    )
    _assert(
        MODULE.UnresolvedParameterSpec is MRTA.UnresolvedParameterSpec,
        "reward contract duplicated unresolved parameter identity",
    )
    bare_spec = importlib.util.spec_from_file_location(
        BARE_MODULE,
        MODULE_PATHS[CANONICAL_MODULE],
    )
    _assert(
        bare_spec is not None and bare_spec.loader is not None,
        "missing bare-key module spec",
    )
    bare_module = importlib.util.module_from_spec(bare_spec)
    try:
        bare_spec.loader.exec_module(bare_module)
    except ImportError as exc:
        _assert(
            "CanonicalModuleIdentityError" in str(exc),
            "bare-key guard returned the wrong error",
        )
    else:
        raise AssertionError("bare-key reward import did not fail")
    spec = _contract()
    _assert(is_dataclass(spec), "spec is not a dataclass")
    mapping = spec.to_mapping()
    expected_keys = (
        "schema_version",
        "wrapper_reward_source",
        "base_reducer",
        "penalty_order",
        "penalty_unit",
        "broadcast_mode",
        "critic_reward_source",
        "valuenorm_source",
        "raw_per_agent_usage",
        "rejection_penalty_scale",
        "base_env_reward_contract",
        "wrapper_shaping_contract",
    )
    _assert(
        tuple(field.name for field in fields(MODULE.TeamRewardContractSpec))
        == expected_keys,
        "spec dataclass field order changed",
    )
    _assert(tuple(mapping) == expected_keys, "spec field order changed")
    expected_values = {
        "schema_version": "event_gated_team_reward_contract_v1",
        "wrapper_reward_source": "AssignmentHarlWrapper.final_reward",
        "base_reducer": "mean_over_robot_axis",
        "penalty_order": "after_mean_before_broadcast",
        "penalty_unit": (
            "once_per_penalty_eligible_rejected_component"
        ),
        "broadcast_mode": "identical_all_agents",
        "critic_reward_source": "broadcast_team_reward",
        "valuenorm_source": "all_physical_step_critic_returns",
        "raw_per_agent_usage": "diagnostics_only",
    }
    for key, value in expected_values.items():
        _assert(mapping[key] == value, f"wrong semantic: {key}")
    _assert(
        tuple(mapping["rejection_penalty_scale"])
        == ("name", "owner_phase", "semantic_purpose"),
        "unresolved parameter mapping changed",
    )
    _assert(
        mapping["rejection_penalty_scale"]
        == {
            "name": "rejection_penalty_scale",
            "owner_phase": "phase_d_e",
            "semantic_purpose": (
                "once_per_penalty_eligible_rejected_component"
            ),
        },
        "unresolved parameter triple changed",
    )
    _assert(
        "value" not in mapping["rejection_penalty_scale"],
        "A3 selected a numeric penalty value",
    )
    _assert(
        mapping["base_env_reward_contract"]
        == (
            "global_coverage_reward_scale",
            "own_coverage_reward_scale",
            "duplicate_scan_penalty_scale",
            "reach_violation_penalty_scale",
            "action_rate_penalty_scale",
            "time_penalty",
        ),
        "base environment identity changed",
    )
    _assert(
        mapping["wrapper_shaping_contract"]
        == (
            "repeated_assignment_penalty_scale",
            "repeated_assignment_grace_steps",
            "no_progress_penalty_scale",
            "no_progress_grace_steps",
            "no_progress_penalty_cap",
            "selected_path_cost_penalty_scale",
        ),
        "wrapper shaping identity changed",
    )
    try:
        spec.schema_version = "changed"
    except (FrozenInstanceError, AttributeError, TypeError):
        pass
    else:
        raise AssertionError("frozen spec allowed rebinding")
    try:
        mapping["schema_version"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("spec mapping is mutable")

    wrong_name = MRTA.UnresolvedParameterSpec(
        name="some_scale",
        owner_phase="phase_d_e",
        semantic_purpose="wrong",
    )
    _expect_error(
        lambda: MODULE.TeamRewardContractSpec(
            rejection_penalty_scale=wrong_name
        ),
        MODULE.TeamRewardSchemaError,
        "unresolved_parameter",
    )
    wrong_purpose = MRTA.UnresolvedParameterSpec(
        name="rejection_penalty_scale",
        owner_phase="phase_d_e",
        semantic_purpose="different_semantics",
    )
    _expect_error(
        lambda: MODULE.TeamRewardContractSpec(
            rejection_penalty_scale=wrong_purpose
        ),
        MODULE.TeamRewardSchemaError,
        "unresolved_parameter",
    )
    wrong_owner = MRTA.UnresolvedParameterSpec(
        name="rejection_penalty_scale",
        owner_phase="phase_d",
        semantic_purpose=(
            "once_per_penalty_eligible_rejected_component"
        ),
    )
    _expect_error(
        lambda: MODULE.TeamRewardContractSpec(
            rejection_penalty_scale=wrong_owner
        ),
        MODULE.TeamRewardSchemaError,
        "unresolved_parameter",
    )
    _expect_error(
        lambda: MODULE.TeamRewardContractSpec(
            rejection_penalty_scale=spec.rejection_penalty_scale,
            base_env_reward_contract=list(
                mapping["base_env_reward_contract"]
            ),
        ),
        MODULE.TeamRewardSchemaError,
        "ordered_identity",
    )
    _expect_plain_error(
        lambda: MODULE.TeamRewardContractSpec(),
        TypeError,
    )
    _expect_plain_error(
        lambda: MODULE.TeamRewardContractSpec(
            rejection_penalty_scale=spec.rejection_penalty_scale,
            unexpected_extension=True,
        ),
        TypeError,
    )
    descriptor = MODULE.get_assignment_team_reward_contract_descriptor()
    expected_descriptor_keys = (
        "contract_version",
        "schema_version",
        "spec_field_order",
        "semantic_values",
        "base_env_reward_contract",
        "wrapper_shaping_contract",
        "unresolved_parameter",
        "operation_order",
        "formula",
        "oracle_inputs",
        "oracle_outputs",
    )
    _assert(
        tuple(descriptor) == expected_descriptor_keys,
        "reward descriptor root order changed",
    )
    _assert(
        descriptor["spec_field_order"] == expected_keys,
        "descriptor/spec field-order identity diverged",
    )
    _assert(
        tuple(descriptor["semantic_values"])
        == (
            "wrapper_reward_source",
            "base_reducer",
            "penalty_order",
            "penalty_unit",
            "broadcast_mode",
            "critic_reward_source",
            "valuenorm_source",
            "raw_per_agent_usage",
        ),
        "semantic value order changed",
    )
    return {
        "schema": mapping["schema_version"],
        "field_count": len(mapping),
        "numeric_parameter_selected": False,
        "missing_extra_list_inputs_rejected": True,
        "descriptor_field_count": len(descriptor),
    }


def test_oracle_operation_order_and_broadcast() -> dict[str, Any]:
    rewards = torch.tensor(
        [
            [[1.0], [3.0], [5.0]],
            [[2.0], [4.0], [6.0]],
        ],
        dtype=torch.float32,
    )
    rejected_components = torch.tensor([2, 1], dtype=torch.int64)
    result = MODULE.compute_team_reward_oracle(
        contract=_contract(),
        wrapper_final_reward=rewards,
        policy_rejected_component_count=rejected_components,
        rejection_penalty_scale=0.5,
    )
    expected_base = torch.tensor([[3.0], [4.0]], dtype=torch.float32)
    expected_team = torch.tensor([[2.0], [3.5]], dtype=torch.float32)
    expected_learner = torch.tensor(
        [
            [[2.0], [2.0], [2.0]],
            [[3.5], [3.5], [3.5]],
        ],
        dtype=torch.float32,
    )
    _assert(
        torch.equal(result.base_team_reward, expected_base),
        "mean over robot axis changed",
    )
    _assert(
        torch.equal(result.team_reward, expected_team),
        "component-once penalty/order changed",
    )
    _assert(
        torch.equal(result.learner_reward, expected_learner),
        "identical agent broadcast changed",
    )
    _assert(
        torch.equal(
            result.learner_reward[:, :1],
            result.learner_reward[:, 1:2],
        ),
        "learner rewards are not identical",
    )
    for agent_id in range(result.learner_reward.shape[1]):
        _assert(
            torch.equal(
                result.learner_reward[:, agent_id, :],
                result.team_reward,
            ),
            f"agent {agent_id} reward is not the exact team reward",
        )
    alias_result = MODULE.evaluate_team_reward_oracle(
        contract=_contract(),
        wrapper_final_reward=rewards,
        policy_rejected_component_count=rejected_components,
        rejection_penalty_scale=0.5,
    )
    _assert(
        torch.equal(alias_result.team_reward, expected_team),
        "evaluate alias differs",
    )
    return {
        "base": expected_base.tolist(),
        "team": expected_team.tolist(),
        "component_penalty_units": rejected_components.tolist(),
        "broadcast_equal": True,
        "broadcast_agent_count": result.learner_reward.shape[1],
        "synthetic_penalty_scale_test_data_only": 0.5,
    }


def test_oracle_input_failure_matrix() -> dict[str, Any]:
    contract = _contract()
    rewards = torch.ones((2, 3, 1), dtype=torch.float32)
    counts = torch.tensor([0, 1], dtype=torch.int64)
    cases = (
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards.squeeze(-1),
                policy_rejected_component_count=counts,
                rejection_penalty_scale=0.1,
            ),
            "shape",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards.to(torch.float64),
                policy_rejected_component_count=counts,
                rejection_penalty_scale=0.1,
            ),
            "dtype",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=torch.full(
                    (2, 3, 1),
                    float("nan"),
                    dtype=torch.float32,
                ),
                policy_rejected_component_count=counts,
                rejection_penalty_scale=0.1,
            ),
            "finite",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=counts.view(2, 1),
                rejection_penalty_scale=0.1,
            ),
            "shape",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=counts.to(torch.int32),
                rejection_penalty_scale=0.1,
            ),
            "dtype",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=torch.tensor(
                    [0, -1], dtype=torch.int64
                ),
                rejection_penalty_scale=0.1,
            ),
            "range",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=counts,
                rejection_penalty_scale=float("nan"),
            ),
            "numeric_range",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=counts,
                rejection_penalty_scale=-0.1,
            ),
            "numeric_range",
        ),
        (
            lambda: MODULE.compute_team_reward_oracle(
                contract=contract,
                wrapper_final_reward=rewards,
                policy_rejected_component_count=counts,
                rejection_penalty_scale=True,
            ),
            "numeric_type",
        ),
    )
    for function, code in cases:
        _expect_error(
            function,
            MODULE.TeamRewardOracleError,
            code,
        )
    return {"invalid_cases": len(cases)}


def test_result_validation_alias_isolation_and_mutation() -> dict[str, Any]:
    rewards = torch.tensor([[[1.0], [3.0]]], dtype=torch.float32)
    counts = torch.tensor([1], dtype=torch.int64)
    result = MODULE.compute_team_reward_oracle(
        contract=_contract(),
        wrapper_final_reward=rewards,
        policy_rejected_component_count=counts,
        rejection_penalty_scale=0.25,
    )
    expected = result.team_reward
    rewards.fill_(99.0)
    counts.fill_(99)
    _assert(
        torch.equal(result.team_reward, expected),
        "source mutation reached oracle result",
    )
    clone = result.learner_reward
    clone.fill_(-7.0)
    _assert(
        not torch.equal(result.learner_reward, clone),
        "accessor exposed writable alias",
    )
    _expect_error(
        lambda: MODULE.TeamRewardOracleResult(
            base_team_reward=torch.zeros((1,), dtype=torch.float32),
            team_reward=torch.zeros((1, 1), dtype=torch.float32),
            learner_reward=torch.zeros((1, 2, 1), dtype=torch.float32),
        ),
        MODULE.TeamRewardOracleError,
        "shape",
    )
    _expect_error(
        lambda: MODULE.TeamRewardOracleResult(
            base_team_reward=torch.zeros((1, 1), dtype=torch.float32),
            team_reward=torch.ones((1, 1), dtype=torch.float32),
            learner_reward=torch.zeros((1, 2, 1), dtype=torch.float32),
        ),
        MODULE.TeamRewardOracleError,
        "broadcast",
    )
    result._team_reward._value.add_(1.0)
    _expect_error(
        lambda: result.team_reward,
        MODULE.TeamRewardOracleError,
        "snapshot_mutation",
    )
    return {
        "source_alias_isolated": True,
        "accessor_alias_isolated": True,
        "direct_result_validation": True,
        "supported_mutation_detected": True,
    }


def test_descriptor_deep_readonly_and_privacy() -> dict[str, Any]:
    first = MODULE.get_assignment_team_reward_contract_descriptor()
    second = MODULE.get_assignment_team_reward_contract_descriptor()
    _assert(first is second, "descriptor identity is not stable")
    _assert(isinstance(first, MappingProxyType), "descriptor is mutable")
    _assert(
        first["schema_version"] == "event_gated_team_reward_contract_v1",
        "descriptor schema changed",
    )
    _assert(
        first["unresolved_parameter"]["numeric_value_selected"] is False,
        "descriptor claims a numeric selection",
    )
    _assert(
        "rejection_penalty_scale"
        not in str(first["base_env_reward_contract"]),
        "new penalty leaked into base reducer identity",
    )
    rendered = repr(first).lower()
    for private_text in (
        "storage",
        "detector",
        "capability",
        "checkpoint fingerprint",
    ):
        _assert(
            private_text not in rendered,
            f"descriptor leaked private field: {private_text}",
        )
    def descriptor_keys(value: object) -> tuple[str, ...]:
        if isinstance(value, Mapping):
            return tuple(value.keys()) + tuple(
                key
                for item in value.values()
                for key in descriptor_keys(item)
            )
        if type(value) is tuple:
            return tuple(
                key for item in value for key in descriptor_keys(item)
            )
        return ()
    _assert(
        "_version" not in descriptor_keys(first),
        "descriptor leaked tensor mutation-version key",
    )
    try:
        first["schema_version"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("descriptor root is writable")
    try:
        first["semantic_values"]["base_reducer"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("descriptor nested mapping is writable")
    return {
        "deep_readonly": True,
        "private_fields_absent": True,
        "numeric_parameter_selected": False,
    }


def test_alternative_reward_order_and_unit_non_equivalence() -> dict[str, Any]:
    rewards = torch.tensor(
        [
            [[1.0], [3.0], [5.0]],
            [[2.0], [4.0], [6.0]],
        ],
        dtype=torch.float32,
    )
    component_counts = torch.tensor([2, 1], dtype=torch.int64)
    scale = 0.5
    canonical = MODULE.compute_team_reward_oracle(
        contract=_contract(),
        wrapper_final_reward=rewards,
        policy_rejected_component_count=component_counts,
        rejection_penalty_scale=scale,
    )

    per_robot_penalty_units = torch.tensor(
        [
            [[1.0], [1.0], [1.0]],
            [[1.0], [1.0], [0.0]],
        ],
        dtype=torch.float32,
    )
    wrong_penalty_before_mean = (
        rewards - scale * per_robot_penalty_units
    ).mean(dim=1)
    _assert(
        not torch.equal(wrong_penalty_before_mean, canonical.team_reward),
        "per-robot penalty before mean unexpectedly matched canonical order",
    )

    base_broadcast = canonical.base_team_reward.view(2, 1, 1).expand_as(
        rewards
    )
    wrong_broadcast_then_per_agent_penalty = (
        base_broadcast - scale * per_robot_penalty_units
    )
    _assert(
        not torch.equal(
            wrong_broadcast_then_per_agent_penalty[:, 0, :],
            wrong_broadcast_then_per_agent_penalty[:, 2, :],
        ),
        "per-agent penalty after broadcast did not expose unequal rewards",
    )
    _assert(
        not torch.equal(
            wrong_broadcast_then_per_agent_penalty,
            canonical.learner_reward,
        ),
        "broadcast-before-per-agent-penalty matched canonical learner reward",
    )

    wrong_unit_counts = {
        "proposal": torch.tensor([3.0, 2.0], dtype=torch.float32),
        "robot": torch.tensor([3.0, 3.0], dtype=torch.float32),
        "task": torch.tensor([4.0, 2.0], dtype=torch.float32),
        "transfer": torch.tensor([1.0, 2.0], dtype=torch.float32),
    }
    for unit_name, counts in wrong_unit_counts.items():
        alternative = canonical.base_team_reward - scale * counts.view(2, 1)
        _assert(
            not torch.equal(alternative, canonical.team_reward),
            f"once-per-{unit_name} fixture matched component-once semantics",
        )
    return {
        "canonical_order": "mean_then_component_penalty_then_broadcast",
        "alternative_order_non_equivalent": True,
        "alternative_units_non_equivalent": tuple(wrong_unit_counts),
        "synthetic_scale_test_data_only": scale,
    }


def _component_rejection_record(
    *,
    component_id: str,
    reason: Any,
    policy_caused: bool,
    penalty_eligible: bool,
    penalty_unit_count: int,
    member_robot_ids: tuple[int, ...] = (0,),
    member_task_ids: tuple[int, ...] = (0,),
) -> Any:
    return MRTA.ComponentRejectionRecord(
        component_id=component_id,
        reason=reason,
        policy_caused=policy_caused,
        penalty_eligible=penalty_eligible,
        penalty_unit_count=penalty_unit_count,
        member_robot_ids=member_robot_ids,
        member_task_ids=member_task_ids,
        env_id=0,
        episode_generation=1,
        transition_generation=2,
        assignment_tick_generation=3,
    )


def test_component_rejection_record_penalty_units() -> dict[str, Any]:
    eligible_records = (
        _component_rejection_record(
            component_id="contention_component_large",
            reason=MRTA.ComponentRejectionReason.CONTENTION_LOSS,
            policy_caused=True,
            penalty_eligible=True,
            penalty_unit_count=1,
            member_robot_ids=(0, 1, 2),
            member_task_ids=(4, 5),
        ),
        _component_rejection_record(
            component_id="contention_component_single",
            reason=MRTA.ComponentRejectionReason.CONTENTION_LOSS,
            policy_caused=True,
            penalty_eligible=True,
            penalty_unit_count=1,
            member_robot_ids=(3,),
            member_task_ids=(6,),
        ),
    )
    _assert(
        tuple(record.penalty_unit_count for record in eligible_records)
        == (1, 1),
        "eligible component penalty was scaled by member cardinality",
    )
    _assert(
        sum(record.penalty_unit_count for record in eligible_records) == 2,
        "two eligible component records did not produce exactly two units",
    )
    expected_mapping_order = (
        "schema_version",
        "component_id",
        "reason",
        "policy_caused",
        "penalty_eligible",
        "penalty_unit_count",
        "member_robot_ids",
        "member_task_ids",
        "env_id",
        "episode_generation",
        "transition_generation",
        "assignment_tick_generation",
    )
    _assert(
        tuple(eligible_records[0].to_mapping()) == expected_mapping_order,
        "component rejection mapping order changed",
    )

    nonpolicy_units: dict[str, int] = {}
    for reason in (
        MRTA.ComponentRejectionReason.LOCAL_SET_OVERFLOW_FAIL_CLOSED,
        MRTA.ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION,
        MRTA.ComponentRejectionReason.TERMINAL_TRANSITION,
    ):
        record = _component_rejection_record(
            component_id=f"nonpolicy_{reason.value}",
            reason=reason,
            policy_caused=False,
            penalty_eligible=False,
            penalty_unit_count=0,
        )
        nonpolicy_units[reason.value] = record.penalty_unit_count
    _assert(
        tuple(nonpolicy_units.values()) == (0, 0, 0),
        "non-policy component rejection received a penalty unit",
    )

    _expect_error(
        lambda: _component_rejection_record(
            component_id="eligible_wrong_units",
            reason=MRTA.ComponentRejectionReason.CONTENTION_LOSS,
            policy_caused=True,
            penalty_eligible=True,
            penalty_unit_count=2,
        ),
        MRTA.MrtaSchemaError,
        "penalty_unit",
    )
    _expect_error(
        lambda: _component_rejection_record(
            component_id="ineligible_wrong_units",
            reason=MRTA.ComponentRejectionReason.CONTENTION_LOSS,
            policy_caused=True,
            penalty_eligible=False,
            penalty_unit_count=1,
        ),
        MRTA.MrtaSchemaError,
        "penalty_unit",
    )
    _expect_error(
        lambda: _component_rejection_record(
            component_id="system_wrong_attribution",
            reason=(
                MRTA.ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION
            ),
            policy_caused=True,
            penalty_eligible=True,
            penalty_unit_count=1,
        ),
        MRTA.MrtaSchemaError,
        "nonpolicy_rejection_attribution",
    )
    return {
        "eligible_component_units": (1, 1),
        "eligible_component_total": 2,
        "nonpolicy_reason_units": nonpolicy_units,
        "invalid_unit_attribution_rejected": True,
    }


def test_v3_reward_projection_and_interface_golden() -> dict[str, Any]:
    v3 = _phase_a5_modules()[CHECKPOINT_V3_MODULE]
    manifest = v3.build_interface_semantic_descriptor_v3(
        scale_contract=_v3_scale_contract()
    )
    reward_section = manifest.reward_contract
    descriptor = MODULE.get_assignment_team_reward_contract_descriptor()
    descriptor_order = tuple(descriptor)
    _assert(
        tuple(field.name for field in fields(type(reward_section)))
        == descriptor_order,
        "typed V3 reward field order differs from reward authority",
    )
    typed_projection = {
        field.name: getattr(reward_section, field.name)
        for field in fields(type(reward_section))
    }
    _assert(
        _semantic_snapshot(typed_projection)
        == _semantic_snapshot(descriptor),
        "typed V3 reward projection differs from tuple-preserving authority",
    )
    json_projection = manifest.to_mapping()["reward_contract"]
    _assert(
        tuple(json_projection) == descriptor_order,
        "JSON-facing V3 reward key order differs from reward authority",
    )
    _assert(
        _semantic_snapshot(json_projection)
        == _semantic_snapshot(descriptor),
        "JSON list normalization changed V3 reward semantics",
    )

    canonical = v3.canonical_assignment_checkpoint_manifest_v3_bytes(manifest)
    fingerprint = hashlib.sha256(canonical).hexdigest()
    _assert(
        len(canonical) == V3_INTERFACE_CANONICAL_BYTE_LENGTH,
        "frozen V3 canonical byte length drifted",
    )
    _assert(
        fingerprint == V3_INTERFACE_SHA256,
        "frozen V3 interface fingerprint drifted",
    )
    decision = v3.evaluate_assignment_checkpoint_manifest_v3_semantics(
        manifest,
        current_manifest=manifest,
        purpose=v3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
    )
    _assert(decision.schema_valid, "V3 interface schema audit failed")
    _assert(
        decision.interface_semantics_valid,
        "V3 interface semantic audit failed",
    )
    _assert(not decision.runtime_ready, "V3 interface became runtime-ready")
    _assert(
        not decision.weight_use_authorized,
        "V3 interface authorized checkpoint weights",
    )
    return {
        "reward_projection_equal": True,
        "canonical_bytes": len(canonical),
        "sha256": fingerprint,
        "runtime_ready": decision.runtime_ready,
        "weight_use_authorized": decision.weight_use_authorized,
    }


def test_checkpoint_ready_rejection_penalty_remains_unresolved() -> dict[str, Any]:
    v3 = _phase_a5_modules()[CHECKPOINT_V3_MODULE]
    scale_contract = _v3_scale_contract()
    manifest = v3.build_interface_semantic_descriptor_v3(
        scale_contract=scale_contract
    )
    readiness = manifest.to_mapping()["runtime_readiness_contract"]
    inventory = readiness["unresolved_parameter_inventory_projection"]
    _assert(
        tuple(inventory["unresolved_parameter_order"])
        == UNRESOLVED_PARAMETER_ORDER,
        "V3 unresolved parameter order changed",
    )
    references = inventory["unresolved_parameter_references"]
    _assert(len(references) == 11, "V3 unresolved inventory is not exactly 11")
    reward_reference = references[8]
    expected_reference = {
        "name": "rejection_penalty_scale",
        "triple_owner_module": (
            "isaaclab_tasks.direct.scan_mobile_manipulator."
            "assignment_team_reward_contract"
        ),
        "triple_owner_contract_version": (
            "assignment_team_reward_contract_v1"
        ),
        "triple_descriptor_key_path": "unresolved_parameter",
        "expected_concrete_type": "finite_float",
        "unit": "team_reward_units_per_rejected_component",
        "legal_domain": "value >= 0",
    }
    _assert(
        tuple(reward_reference) == tuple(expected_reference),
        "reward unresolved-reference field order changed",
    )
    _assert(
        reward_reference == expected_reference,
        "V3 unresolved reference #9 changed",
    )
    _assert(
        readiness["unresolved_parameter_resolution_status"]
        == "all_11_unresolved",
        "V3 readiness no longer reports all 11 unresolved",
    )
    _assert(
        readiness["runtime_execution_authorized"] is False,
        "V3 interface authorized runtime execution",
    )
    _assert(
        readiness["checkpoint_weight_use_authorized"] is False,
        "V3 interface authorized checkpoint weight use",
    )

    no_values = _expect_plain_error(
        lambda: v3.build_checkpoint_ready_v3(
            scale_contract=scale_contract
        ),
        v3.CheckpointReadyManifestNotAuthorizedError,
    )
    _assert(
        no_values.parameter_status == "all_11_unresolved",
        "checkpoint-ready no-value status changed",
    )
    synthetic_only = _expect_plain_error(
        lambda: v3.build_checkpoint_ready_v3(
            scale_contract=scale_contract,
            resolved_parameters={"rejection_penalty_scale": 0.5},
        ),
        v3.CheckpointReadyManifestNotAuthorizedError,
    )
    _assert(
        synthetic_only.parameter_status.startswith("partial_1_of_11"),
        "test-only penalty value was not kept partial/unverified",
    )
    caller_values = {name: 0.5 for name in UNRESOLVED_PARAMETER_ORDER}
    all_caller_values = _expect_plain_error(
        lambda: v3.build_checkpoint_ready_v3(
            scale_contract=scale_contract,
            resolved_parameters=caller_values,
        ),
        v3.CheckpointReadyManifestNotAuthorizedError,
    )
    _assert(
        all_caller_values.parameter_status
        == "all_11_caller_values_present_but_unverified_and_not_authorized",
        "caller values unexpectedly made V3 checkpoint-ready",
    )
    _assert(
        all_caller_values.runtime_readiness == "interface_only",
        "ready-builder rejection lost interface-only readiness",
    )
    return {
        "reward_reference_index": 9,
        "reward_reference": expected_reference,
        "readiness": "all_11_unresolved",
        "synthetic_scale_test_data_only": 0.5,
        "checkpoint_ready_blocked": True,
        "checkpoint_weight_use_authorized": False,
    }


def _qualified_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _root_identifier(node: ast.AST) -> str:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else ""


def _qualified_components(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (*_qualified_components(node.value), node.attr)
    if isinstance(node, ast.Subscript):
        return _qualified_components(node.value)
    return ()


def _literal_subscript_key(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Subscript):
        return None
    return (
        node.slice.value
        if isinstance(node.slice, ast.Constant)
        and type(node.slice.value) is str
        else None
    )


def test_static_reward_identity_and_runtime_non_wiring() -> dict[str, Any]:
    reward_path = MODULE_PATHS[CANONICAL_MODULE]
    reward_tree = ast.parse(reward_path.read_text(encoding="utf-8"))
    import_targets: set[str] = set()
    call_targets: set[str] = set()
    for node in ast.walk(reward_tree):
        if isinstance(node, ast.Import):
            import_targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            import_targets.add(node.module or "")
        elif isinstance(node, ast.Call):
            call_targets.add(_qualified_call_name(node.func))
    forbidden_import_prefixes = (
        "omni",
        "isaacsim",
        "isaaclab.app",
        "harl",
        "gym",
        "wandb",
    )
    _assert(
        not any(
            target.startswith(forbidden_import_prefixes)
            for target in import_targets
        ),
        "pure reward contract imports a forbidden runtime dependency",
    )
    forbidden_calls = {
        "AppLauncher",
        "open",
        "io.open",
        "os.open",
        "Path.open",
        "Path.write_text",
        "Path.write_bytes",
        "json.dump",
        "csv.writer",
        "SummaryWriter",
        "wandb.init",
        "wandb.log",
        "torch.save",
        "torch.load",
        "torch.jit.load",
        "load_state_dict",
        "gym.make",
        "optimizer.step",
        "backward",
        "environment.step",
    }
    forbidden_call_terminals = {
        "open",
        "write_text",
        "write_bytes",
        "dump",
        "writer",
        "save",
        "load",
        "load_state_dict",
        "backward",
        "step",
        "commit",
    }
    _assert(
        forbidden_calls.isdisjoint(call_targets),
        "pure reward contract contains a forbidden runtime/I/O call",
    )
    _assert(
        not {
            target
            for target in call_targets
            if target.rsplit(".", 1)[-1] in forbidden_call_terminals
        },
        "pure reward contract contains a receiver-qualified forbidden call",
    )

    runtime_trees = {
        name: ast.parse(path.read_text(encoding="utf-8"))
        for name, path in RUNTIME_REWARD_SOURCE_PATHS.items()
    }
    prohibited_runtime_literals = {
        "event_gated_team_reward_contract_v1",
        "rejection_penalty_scale",
        "policy_rejected_component_count",
        "once_per_penalty_eligible_rejected_component",
        "broadcast_team_reward",
    }
    phase_a_diagnostic_sink_keys = {
        "assignment_tick",
        "proposal_resolution",
        "team_reward",
        "actor_update",
    }
    sink_root_names = {
        "info",
        "infos",
        "extras",
        "episode_info",
        "episode_infos",
        "train_info",
        "writer",
        "summary_writer",
        "tensorboard",
        "logger",
    }
    sink_methods = {
        "update",
        "setdefault",
        "add_scalar",
        "add_scalars",
        "log",
        "write",
    }
    scoped_sink_writes: list[tuple[str, str]] = []
    for name, tree in runtime_trees.items():
        imports: set[str] = set()
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                imports.add(module_name)
                imports.update(
                    f"{module_name}.{alias.name}" if module_name else alias.name
                    for alias in node.names
                )
        _assert(
            not any(
                target.endswith(
                    (
                        "assignment_team_reward_contract",
                        "assignment_event_gated_diagnostics_contract",
                    )
                )
                for target in imports
            ),
            f"{name} imported a Phase-A reward/diagnostics contract",
        )
        _assert(
            prohibited_runtime_literals.isdisjoint(literals),
            f"{name} contains new event-team-reward contract wiring",
        )
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    tuple(node.targets)
                    if isinstance(node, ast.Assign)
                    else (node.target,)
                )
                value = getattr(node, "value", None)
                for target in targets:
                    target_components = set(_qualified_components(target))
                    key = _literal_subscript_key(target)
                    if (
                        target_components.intersection(sink_root_names)
                        and key in phase_a_diagnostic_sink_keys
                    ):
                        scoped_sink_writes.append((name, key))
                    if (
                        isinstance(target, ast.Name)
                        and target.id in sink_root_names
                        and isinstance(value, ast.Dict)
                    ):
                        for dict_key in value.keys:
                            if (
                                isinstance(dict_key, ast.Constant)
                                and dict_key.value in phase_a_diagnostic_sink_keys
                            ):
                                scoped_sink_writes.append(
                                    (name, str(dict_key.value))
                                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in sink_methods
                and set(_qualified_components(node.func.value)).intersection(
                    sink_root_names
                )
            ):
                for argument in (*node.args, *(item.value for item in node.keywords)):
                    for child in ast.walk(argument):
                        if (
                            isinstance(child, ast.Constant)
                            and child.value in phase_a_diagnostic_sink_keys
                        ):
                            scoped_sink_writes.append(
                                (name, str(child.value))
                            )
    _assert(
        scoped_sink_writes == [],
        "runtime source wires Phase-A diagnostic keys into info/extras/TB sinks",
    )

    expected_env_order = (
        "global_coverage_reward_scale",
        "own_coverage_reward_scale",
        "duplicate_scan_penalty_scale",
        "reach_violation_penalty_scale",
        "action_rate_penalty_scale",
        "time_penalty",
    )
    env_tree = runtime_trees["environment"]
    env_assignment_lines: dict[str, int] = {}
    for node in ast.walk(env_tree):
        targets: tuple[ast.expr, ...] = ()
        if isinstance(node, ast.Assign):
            targets = tuple(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
        for target in targets:
            if isinstance(target, ast.Name) and target.id in expected_env_order:
                env_assignment_lines.setdefault(target.id, node.lineno)
    _assert(
        tuple(sorted(env_assignment_lines, key=env_assignment_lines.get))
        == expected_env_order,
        "environment reward-scale declaration order changed",
    )
    _assert(
        MODULE.BASE_ENV_REWARD_SCALE_IDENTITY == expected_env_order,
        "reward descriptor/environment scale identity diverged",
    )

    expected_wrapper_order = (
        "repeated_assignment_penalty_scale",
        "repeated_assignment_grace_steps",
        "no_progress_penalty_scale",
        "no_progress_grace_steps",
        "no_progress_penalty_cap",
        "selected_path_cost_penalty_scale",
    )
    wrapper_tree = runtime_trees["wrapper"]
    matching_dict_orders: list[tuple[str, ...]] = []
    final_reward_source_found = False
    for node in ast.walk(wrapper_tree):
        if isinstance(node, ast.Dict):
            keys = tuple(
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            )
            if set(expected_wrapper_order).issubset(keys):
                matching_dict_orders.append(keys)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "final_reward"
            for target in node.targets
        ):
            value = node.value
            final_reward_source_found = (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Add)
                and isinstance(value.left, ast.Name)
                and value.left.id == "base_reward_tensor"
                and isinstance(value.right, ast.Name)
                and value.right.id == "total_adjustment"
            )
    _assert(
        matching_dict_orders == [expected_wrapper_order],
        "wrapper shaping config identity/order changed",
    )
    _assert(
        MODULE.WRAPPER_SHAPING_CONFIG_IDENTITY == expected_wrapper_order,
        "reward descriptor/wrapper shaping identity diverged",
    )
    _assert(
        final_reward_source_found,
        "AssignmentHarlWrapper.final_reward source expression changed",
    )
    return {
        "reward_contract_forbidden_imports": False,
        "reward_contract_forbidden_calls": False,
        "runtime_reward_or_diagnostics_contract_imports": False,
        "phase_a_info_extras_tensorboard_sink_writes": False,
        "environment_reward_order": expected_env_order,
        "wrapper_shaping_order": expected_wrapper_order,
        "wrapper_final_reward_source": "base_reward_tensor + total_adjustment",
    }


def _child_source() -> str:
    return r'''
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import ModuleType
import torch

paths = [Path(item).resolve() for item in sys.argv[1:]]
names = [
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract",
]
task_source = paths[-1].parent
for name, path in (
    ("isaaclab_tasks", task_source.parents[2]),
    ("isaaclab_tasks.direct", task_source.parent),
    ("isaaclab_tasks.direct.scan_mobile_manipulator", task_source),
):
    module = ModuleType(name)
    module.__package__ = name
    module.__path__ = [str(path)]
    sys.modules[name] = module

python_rng = random.getstate()
torch_rng = torch.random.get_rng_state().clone()
numpy_before = "numpy" in sys.modules
environment = dict(os.environ)
cwd = os.getcwd()
sys_path = tuple(sys.path)
loggers = tuple(sorted(logging.Logger.manager.loggerDict))
handlers = tuple(id(item) for item in logging.getLogger().handlers)
files = tuple(sorted(str(item.relative_to(Path.cwd())) for item in Path.cwd().rglob("*")))
source_hashes = tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)
stdout = io.StringIO()
stderr = io.StringIO()
loaded = {}
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    for name, path in zip(names, paths):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    mrta = loaded[names[2]]
    reward = loaded[names[3]]
    contract = reward.TeamRewardContractSpec(
        rejection_penalty_scale=mrta.UnresolvedParameterSpec(
            name="rejection_penalty_scale",
            owner_phase="phase_d_e",
            semantic_purpose="once_per_penalty_eligible_rejected_component",
        )
    )
    result = reward.compute_team_reward_oracle(
        contract=contract,
        wrapper_final_reward=torch.tensor([[[1.0], [3.0]]], dtype=torch.float32),
        policy_rejected_component_count=torch.tensor([1], dtype=torch.int64),
        rejection_penalty_scale=0.25,
    )

blocked = [
    name for name in sys.modules
    if name.startswith(("omni", "harl", "isaaclab.app"))
    or "assignment_harl_wrapper" in name
    or "assignment_checkpoint" in name
]
profile_contract_absent = not any(
    "assignment_profile_contract" in name
    for name in sys.modules
)
files_after = tuple(sorted(str(item.relative_to(Path.cwd())) for item in Path.cwd().rglob("*")))
print(json.dumps({
    "random": random.getstate() == python_rng,
    "torch": torch.equal(torch.random.get_rng_state(), torch_rng),
    "numpy_before": numpy_before,
    "numpy_after": "numpy" in sys.modules,
    "environment": dict(os.environ) == environment,
    "cwd": os.getcwd() == cwd,
    "sys_path": tuple(sys.path) == sys_path,
    "loggers": tuple(sorted(logging.Logger.manager.loggerDict)) == loggers,
    "handlers": tuple(id(item) for item in logging.getLogger().handlers) == handlers,
    "files": files_after == files,
    "sources": tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths) == source_hashes,
    "stdout": stdout.getvalue(),
    "stderr": stderr.getvalue(),
    "blocked": blocked,
    "profile_contract_absent": profile_contract_absent,
    "result": result.team_reward.tolist(),
}, sort_keys=True))
'''


def test_clean_child_side_effect_boundary() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                _child_source(),
                *[str(path) for path in MODULE_PATHS.values()],
            ],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"child failed: {completed.stdout!r} {completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(len(lines) == 1, "child emitted non-JSON stdout")
    evidence = json.loads(lines[0])
    for key in (
        "random",
        "torch",
        "environment",
        "cwd",
        "sys_path",
        "loggers",
        "handlers",
        "files",
        "sources",
        "profile_contract_absent",
    ):
        _assert(evidence[key], f"side-effect evidence failed: {key}")
    if not evidence["numpy_before"]:
        _assert(not evidence["numpy_after"], "module imported NumPy")
    _assert(evidence["blocked"] == [], "forbidden runtime import")
    _assert(not evidence["stdout"], "module wrote stdout")
    _assert(not evidence["stderr"], "module wrote stderr")
    return {
        "rng_unchanged": True,
        "cwd_env_path_logger_unchanged": True,
        "files_unchanged": True,
        "forbidden_runtime_imports": [],
        "a1_profile_contract_absent": True,
    }


def _old_route_child_source() -> str:
    return r'''
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import ModuleType
import torch

paths = [Path(item).resolve() for item in sys.argv[1:]]
names = [
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract",
]
task_source = paths[0].parent
for name, path in (
    ("isaaclab_tasks", task_source.parents[2]),
    ("isaaclab_tasks.direct", task_source.parent),
    ("isaaclab_tasks.direct.scan_mobile_manipulator", task_source),
):
    module = ModuleType(name)
    module.__package__ = name
    module.__path__ = [str(path)]
    sys.modules[name] = module

def logger_state():
    root = logging.getLogger()
    manager_items = tuple(sorted(logging.Logger.manager.loggerDict.items()))
    named = tuple(
        (
            name,
            logger.level,
            logger.propagate,
            logger.disabled,
            tuple(id(handler) for handler in logger.handlers),
        )
        for name, logger in manager_items
        if isinstance(logger, logging.Logger)
    )
    registry = tuple((name, type(value).__name__) for name, value in manager_items)
    return (
        root.level,
        root.propagate,
        root.disabled,
        tuple(id(handler) for handler in root.handlers),
        named,
        registry,
    )

python_rng = random.getstate()
torch_rng = torch.random.get_rng_state().clone()
numpy_before = "numpy" in sys.modules
environment = dict(os.environ)
cwd = os.getcwd()
sys_path = tuple(sys.path)
logger_before = logger_state()
files = tuple(sorted(str(item.relative_to(Path.cwd())) for item in Path.cwd().rglob("*")))
source_hashes = tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)
stdout = io.StringIO()
stderr = io.StringIO()
loaded = {}
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    for name, path in zip(names, paths):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    profile = loaded[names[0]]
    mrta = loaded[names[3]]
    reward = loaded[names[4]]
    resolved = {}
    for profile_name in (
        profile.AssignmentProfileName.LEGACY,
        profile.AssignmentProfileName.LIFECYCLE_CONTRACT_C,
    ):
        identity = profile.resolve_assignment_profile(
            profile_name,
            profile.AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK,
        )
        mapping = profile.resolved_assignment_profile_to_mapping(identity)
        if "event_gated_target_semantics" in mapping:
            raise AssertionError("old profile gained event-gated target semantics")
        resolved[profile_name.value] = mapping["runtime_route"]
    contract = reward.TeamRewardContractSpec(
        rejection_penalty_scale=mrta.UnresolvedParameterSpec(
            name="rejection_penalty_scale",
            owner_phase="phase_d_e",
            semantic_purpose="once_per_penalty_eligible_rejected_component",
        )
    )
    descriptor = reward.get_assignment_team_reward_contract_descriptor()
    result = reward.compute_team_reward_oracle(
        contract=contract,
        wrapper_final_reward=torch.tensor([[[1.0], [3.0]]], dtype=torch.float32),
        policy_rejected_component_count=torch.tensor([1], dtype=torch.int64),
        rejection_penalty_scale=0.25,
    )

blocked = [
    name for name in sys.modules
    if name.startswith(("omni", "harl", "isaaclab.app"))
    or "scan_mobile_manipulator_env" in name
    or "assignment_harl_wrapper" in name
    or "assignment_harl_training" in name
    or "assignment_lifecycle_resolver" in name
    or "assignment_event_profile_schema_contract" in name
    or "assignment_event_gated_diagnostics_contract" in name
    or "assignment_checkpoint" in name
]
files_after = tuple(sorted(str(item.relative_to(Path.cwd())) for item in Path.cwd().rglob("*")))
print(json.dumps({
    "random": random.getstate() == python_rng,
    "torch": torch.equal(torch.random.get_rng_state(), torch_rng),
    "numpy_before": numpy_before,
    "numpy_after": "numpy" in sys.modules,
    "environment": dict(os.environ) == environment,
    "cwd": os.getcwd() == cwd,
    "sys_path": tuple(sys.path) == sys_path,
    "logger_state": logger_state() == logger_before,
    "files": files_after == files,
    "sources": tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths) == source_hashes,
    "stdout": stdout.getvalue(),
    "stderr": stderr.getvalue(),
    "blocked": blocked,
    "routes": resolved,
    "reward_contract_version": descriptor["contract_version"],
    "result": result.team_reward.tolist(),
}, sort_keys=True))
'''


def test_old_profile_resolution_clean_child_no_side_effects() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                _old_route_child_source(),
                *[
                    str(path)
                    for path in OLD_ROUTE_CHILD_MODULE_PATHS.values()
                ],
            ],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"old-route child failed: {completed.stdout!r} {completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(len(lines) == 1, "old-route child emitted non-JSON stdout")
    evidence = json.loads(lines[0])
    for key in (
        "random",
        "torch",
        "environment",
        "cwd",
        "sys_path",
        "logger_state",
        "files",
        "sources",
    ):
        _assert(evidence[key], f"old-route side-effect evidence failed: {key}")
    if not evidence["numpy_before"]:
        _assert(not evidence["numpy_after"], "old-route child imported NumPy")
    _assert(evidence["blocked"] == [], "old route imported runtime/sink module")
    _assert(not evidence["stdout"], "old-route operation wrote stdout")
    _assert(not evidence["stderr"], "old-route operation wrote stderr")
    expected_routes = {
        "legacy": "existing_legacy_assignment_harl_v1",
        "lifecycle_contract_c": (
            "existing_lifecycle_contract_c_assignment_harl_v1"
        ),
    }
    _assert(evidence["routes"] == expected_routes, "old-route identity changed")
    _assert(
        evidence["reward_contract_version"]
        == "assignment_team_reward_contract_v1",
        "clean child observed reward contract version drift",
    )
    return {
        "resolved_routes": expected_routes,
        "rng_unchanged": True,
        "logger_state_unchanged": True,
        "files_unchanged": True,
        "runtime_or_sink_imports": [],
    }


TESTS = (
    test_canonical_identity_and_exact_spec,
    test_oracle_operation_order_and_broadcast,
    test_oracle_input_failure_matrix,
    test_result_validation_alias_isolation_and_mutation,
    test_descriptor_deep_readonly_and_privacy,
    test_clean_child_side_effect_boundary,
    test_alternative_reward_order_and_unit_non_equivalence,
    test_component_rejection_record_penalty_units,
    test_v3_reward_projection_and_interface_golden,
    test_checkpoint_ready_rejection_penalty_remains_unresolved,
    test_static_reward_identity_and_runtime_non_wiring,
    test_old_profile_resolution_clean_child_no_side_effects,
)

_assert(
    len(TESTS)
    == A3_BASELINE_TEST_GROUP_COUNT + A5_ADDED_TEST_GROUP_COUNT,
    "reward test group accounting changed",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, str]] = []
    evidence: dict[str, Any] = {}
    for test in TESTS:
        try:
            evidence[test.__name__] = test()
        except Exception as exc:
            results.append(
                {
                    "name": test.__name__,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"name": test.__name__, "status": "passed"})
    failed = [item for item in results if item["status"] == "failed"]
    payload = {
        "status": "failed" if failed else "passed",
        "num_tests": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "previous_groups": A3_BASELINE_TEST_GROUP_COUNT,
        "new_groups": A5_ADDED_TEST_GROUP_COUNT,
        "final_groups": len(TESTS),
        "tests": results,
        "evidence": evidence,
        "runtime_boundary": (
            "pure/schema Phase A3-frozen and Phase A5 closeout evidence only; "
            "no wrapper reward change, critic/ValueNorm route, logger, "
            "checkpoint tensor I/O, AppLauncher, Isaac, training, playback, "
            "diagnosis, or evaluation"
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            suffix = (
                f": {item['error']}" if item["status"] == "failed" else ""
            )
            print(f"{item['status'].upper()} {item['name']}{suffix}")
        print(
            f"{'FAIL' if failed else 'PASS'} "
            f"{payload['passed']}/{payload['num_tests']} tests"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
