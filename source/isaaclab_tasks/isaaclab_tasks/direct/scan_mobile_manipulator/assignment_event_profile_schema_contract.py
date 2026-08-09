"""Pure descriptor contract for the event-gated assignment profile.

This module freezes immutable interface/schema identity only.  It does not
construct observations, schedule retries, run a resolver, build a model, touch
HARL, or perform checkpoint I/O.
"""

from __future__ import annotations


if __name__ != (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract"
):
    raise ImportError(
        "CanonicalModuleIdentityError: assignment event-profile schema "
        "contract source must fail before declaring identity-bearing types "
        "or importing dependencies; expected module key="
        "'isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_event_profile_schema_contract'; actual module key="
        f"{__name__!r}"
    )


from collections.abc import Mapping
from enum import Enum
import math
import re
from types import MappingProxyType

from .assignment_event_contract import (
    ASSIGNMENT_EVENT_CONTRACT_VERSION,
    get_assignment_event_contract_descriptor,
)
from .assignment_event_gated_diagnostics_contract import (
    ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION,
    get_assignment_event_gated_diagnostics_descriptor,
)
from .assignment_lifecycle_transition_contract import (
    ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION,
    get_assignment_lifecycle_transition_schema_descriptor,
)
from .assignment_mrta_contract import (
    ASSIGNMENT_MRTA_CONTRACT_VERSION,
    get_assignment_mrta_contract_descriptor,
)
from .assignment_profile_contract import (
    ASSIGNMENT_PROFILE_CONTRACT_VERSION,
    AssignmentProfileName,
    AssignmentProfileResolutionOrigin,
    resolve_assignment_profile,
    resolved_assignment_profile_to_mapping,
)
from .assignment_team_reward_contract import (
    ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION,
    get_assignment_team_reward_contract_descriptor,
)


CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract"
)
ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION = (
    "assignment_event_profile_schema_contract_v1"
)
EVENT_GATED_SCALE_CONTRACT_VERSION = "event_gated_scale_contract_v1"
EVENT_GATED_UNRESOLVED_PARAMETER_INVENTORY_VERSION = (
    "event_gated_unresolved_parameter_inventory_v1"
)
EVENT_GATED_DECISION_VALID_TRAINING_CONTRACT_VERSION = (
    "event_gated_decision_valid_actor_training_v1"
)
EVENT_GATED_SEQUENTIAL_FACTOR_CONTRACT_VERSION = (
    "event_gated_happo_sequential_factor_v1"
)
EVENT_GATED_MODEL_STRUCTURE_PROJECTION_VERSION = (
    "event_gated_model_structure_projection_v1"
)
EVENT_GATED_TRAINING_CONTRACT_PROJECTION_VERSION = (
    "event_gated_training_contract_projection_v1"
)
EVENT_GATED_RUNTIME_READINESS_PROJECTION_VERSION = (
    "event_gated_runtime_readiness_projection_v1"
)
EVENT_GATED_V3_SECTION_OWNERSHIP_VERSION = (
    "event_gated_v3_section_ownership_v1"
)


class AssignmentEventProfileSchemaContractError(RuntimeError):
    """Stable fail-closed error for malformed or drifting schema identity."""


class UnresolvedParameterOwner(str, Enum):
    """Only legal serialized owner vocabulary for unresolved method values."""

    PHASE_B_RUNTIME = "phase_b"
    PHASE_D_REWARD = "phase_d"
    PHASE_E_EVALUATION = "phase_e"
    PHASE_B_RUNTIME_AND_PHASE_E_EVALUATION = "phase_b_e"
    PHASE_D_REWARD_AND_PHASE_E_EVALUATION = "phase_d_e"


_SCALE_KEYS = (
    "contract_version",
    "M",
    "N",
    "ordered_agent_names",
    "ordered_task_ids",
    "scene_env_spacing",
    "sim_dt_seconds",
    "control_decimation",
    "physical_control_step_seconds",
    "episode_time_limit_seconds",
    "episode_horizon_steps",
)


def _fail(message: str) -> None:
    raise AssignmentEventProfileSchemaContractError(message)


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("descriptor mappings require exact string keys")
            result[key] = _deep_readonly(item)
        return MappingProxyType(result)
    if type(value) in (tuple, list):
        return tuple(_deep_readonly(item) for item in value)
    if type(value) in (str, int, float, bool):
        return value
    _fail(
        "descriptor values must be immutable Python primitives; "
        f"actual={type(value).__name__}"
    )


def _require_positive_dimension(value: object, *, name: str) -> int:
    if type(value) is not int or value <= 0:
        _fail(f"{name} must be an exact positive int; actual={value!r}")
    return value


def _require_positive_finite_float(value: object, *, name: str) -> float:
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        _fail(f"{name} must be an exact finite float > 0; actual={value!r}")
    return value


def actor_obs_dim(M: int, N: int) -> int:
    """Return ``6*M*N + 30*M + 14*N + 2`` for exact positive ints."""

    M = _require_positive_dimension(M, name="M")
    N = _require_positive_dimension(N, name="N")
    return 6 * M * N + 30 * M + 14 * N + 2


def shared_obs_dim(M: int, N: int) -> int:
    """Return ``6*M*N + 31*M + 15*N + 8`` for exact positive ints."""

    M = _require_positive_dimension(M, name="M")
    N = _require_positive_dimension(N, name="N")
    return 6 * M * N + 31 * M + 15 * N + 8


def build_event_gated_scale_contract(
    *,
    M: int,
    N: int,
    ordered_agent_names: tuple[str, ...],
    ordered_task_ids: tuple[int, ...],
    scene_env_spacing: float,
    sim_dt_seconds: float,
    control_decimation: int,
    physical_control_step_seconds: float,
    episode_time_limit_seconds: float,
    episode_horizon_steps: int,
) -> Mapping[str, object]:
    """Validate caller-resolved pure scale values and return an immutable map."""

    M = _require_positive_dimension(M, name="M")
    N = _require_positive_dimension(N, name="N")
    if type(ordered_agent_names) is not tuple:
        _fail("ordered_agent_names must be an exact tuple")
    if len(ordered_agent_names) != M:
        _fail("ordered_agent_names length must equal M")
    if any(type(name) is not str or not name for name in ordered_agent_names):
        _fail("ordered_agent_names entries must be nonempty exact strings")
    if len(set(ordered_agent_names)) != M:
        _fail("ordered_agent_names must be unique")
    if type(ordered_task_ids) is not tuple or ordered_task_ids != tuple(range(N)):
        _fail("ordered_task_ids must be the exact tuple(range(N))")
    scene_env_spacing = _require_positive_finite_float(
        scene_env_spacing, name="scene_env_spacing"
    )
    sim_dt_seconds = _require_positive_finite_float(
        sim_dt_seconds, name="sim_dt_seconds"
    )
    if type(control_decimation) is not int or control_decimation < 1:
        _fail("control_decimation must be an exact int >= 1")
    physical_control_step_seconds = _require_positive_finite_float(
        physical_control_step_seconds,
        name="physical_control_step_seconds",
    )
    expected_physical_step = sim_dt_seconds * control_decimation
    if physical_control_step_seconds != expected_physical_step:
        _fail(
            "physical_control_step_seconds must exactly equal "
            "sim_dt_seconds * control_decimation"
        )
    episode_time_limit_seconds = _require_positive_finite_float(
        episode_time_limit_seconds,
        name="episode_time_limit_seconds",
    )
    if type(episode_horizon_steps) is not int or episode_horizon_steps < 1:
        _fail("episode_horizon_steps must be an exact int >= 1")
    expected_horizon = math.ceil(
        episode_time_limit_seconds / physical_control_step_seconds
    )
    if episode_horizon_steps != expected_horizon:
        _fail(
            "episode_horizon_steps must exactly equal ceil(time_limit / "
            "physical_control_step)"
        )
    return _deep_readonly(
        {
            "contract_version": EVENT_GATED_SCALE_CONTRACT_VERSION,
            "M": M,
            "N": N,
            "ordered_agent_names": ordered_agent_names,
            "ordered_task_ids": ordered_task_ids,
            "scene_env_spacing": scene_env_spacing,
            "sim_dt_seconds": sim_dt_seconds,
            "control_decimation": control_decimation,
            "physical_control_step_seconds": physical_control_step_seconds,
            "episode_time_limit_seconds": episode_time_limit_seconds,
            "episode_horizon_steps": episode_horizon_steps,
        }
    )  # type: ignore[return-value]


def _validated_scale_copy(scale_contract: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(scale_contract, Mapping):
        _fail("scale_contract must be a mapping")
    if tuple(scale_contract) != _SCALE_KEYS:
        _fail(
            "scale_contract has missing, unknown, or reordered keys; "
            f"expected={_SCALE_KEYS!r}; actual={tuple(scale_contract)!r}"
        )
    if scale_contract["contract_version"] != EVENT_GATED_SCALE_CONTRACT_VERSION:
        _fail("scale_contract contract_version drift")
    return build_event_gated_scale_contract(
        M=scale_contract["M"],  # type: ignore[arg-type]
        N=scale_contract["N"],  # type: ignore[arg-type]
        ordered_agent_names=scale_contract["ordered_agent_names"],  # type: ignore[arg-type]
        ordered_task_ids=scale_contract["ordered_task_ids"],  # type: ignore[arg-type]
        scene_env_spacing=scale_contract["scene_env_spacing"],  # type: ignore[arg-type]
        sim_dt_seconds=scale_contract["sim_dt_seconds"],  # type: ignore[arg-type]
        control_decimation=scale_contract["control_decimation"],  # type: ignore[arg-type]
        physical_control_step_seconds=scale_contract[
            "physical_control_step_seconds"
        ],  # type: ignore[arg-type]
        episode_time_limit_seconds=scale_contract[
            "episode_time_limit_seconds"
        ],  # type: ignore[arg-type]
        episode_horizon_steps=scale_contract["episode_horizon_steps"],  # type: ignore[arg-type]
    )


_ROBOT_PHYSICAL_COLUMNS = (
    "base_x", "base_y", "base_z", "base_yaw_sin", "base_yaw_cos",
    "scanner_x", "scanner_y", "scanner_z", "scanner_qw", "scanner_qx",
    "scanner_qy", "scanner_qz", "arm_reach", "scanner_min_range",
    "scanner_max_range", "scanner_fov_cos",
)
_ROBOT_LIFECYCLE_COLUMNS = (
    "EXECUTING", "NEEDS_ASSIGNMENT", "WAITING_FOR_TASK", "UNAVAILABLE",
    "robot_available",
)
_TASK_POSE_COLUMNS = (
    "task_x", "task_y", "task_z", "task_qw", "task_qx", "task_qy",
    "task_qz",
)
_TASK_LIFECYCLE_COLUMNS = (
    "AVAILABLE", "CLAIMED", "NAVIGATING", "ALIGNING", "COMPLETED",
    "TEAM_INFEASIBLE",
)
_TRIGGER_COLUMNS = (
    "lifecycle_event_seed", "scheduled_retry_opportunity",
    "decision_opportunity_present", "decision_valid",
    "current_task_continue_legal",
)
_ACTOR_BLOCK_RECORD_FIELD_ORDER = (
    "order", "name", "category", "treatment", "shape", "source_dtype",
    "serialized_dtype", "flatten_rule", "column_order", "semantic_source",
    "visibility", "normalization_rule",
)
_ACTOR_BLOCK_ROWS = (
    (1, "actor_robot_identity_one_hot", "A", "EVENT_SPECIFIC", ("M",),
     "torch.bool", "torch.float32", "global_robot_id_ascending", (),
     "actor_id_against_scale_contract_ordered_agent_names", "policy_visible",
     "bool_to_float32_0_1"),
    (2, "global_robot_physical_table", "B", "REUSE_PRIMITIVE", ("M", 16),
     "torch.float32", "torch.float32",
     "global_robot_id_outer_column_order_inner", _ROBOT_PHYSICAL_COLUMNS,
     "finalized_pre_policy_global_robot_physical_state", "policy_visible",
     "robot_physical_normalization_v1"),
    (3, "global_robot_lifecycle_table", "B", "EVENT_SPECIFIC", ("M", 5),
     "torch.bool", "torch.float32", "global_robot_id_outer_column_order_inner",
     _ROBOT_LIFECYCLE_COLUMNS, "finalized_pre_policy_robot_lifecycle_state",
     "policy_visible", "bool_to_float32_0_1"),
    (4, "global_task_pose_table", "C", "REUSE_PRIMITIVE", ("N", 7),
     "torch.float32", "torch.float32", "global_task_id_outer_column_order_inner",
     _TASK_POSE_COLUMNS, "finalized_pre_policy_global_task_pose",
     "policy_visible", "task_pose_normalization_v1"),
    (5, "global_task_lifecycle_one_hot", "C", "EVENT_SPECIFIC", ("N", 6),
     "torch.bool", "torch.float32", "global_task_id_outer_column_order_inner",
     _TASK_LIFECYCLE_COLUMNS, "finalized_pre_policy_task_lifecycle_state",
     "policy_visible", "bool_to_float32_0_1"),
    (6, "event_updated_task_ownership_one_hot", "D", "REUSE_PRIMITIVE",
     ("N", "M+1"), "torch.bool", "torch.float32",
     "global_task_id_outer_global_robot_id_then_no_owner_inner", (),
     "finalized_pre_policy_a0_ownership", "policy_visible", "bool_to_float32_0_1"),
    (7, "event_updated_baseline_assignment_one_hot", "D", "REUSE_PRIMITIVE",
     ("M", "N+1"), "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_then_no_task_inner", (),
     "finalized_pre_policy_a0_assignment", "policy_visible", "bool_to_float32_0_1"),
    (8, "episode_permanent_failed_pair_mask", "E", "EVENT_SPECIFIC",
     ("M", "N"), "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (),
     "episode_cumulative_updated_failed_pairs", "policy_visible",
     "bool_to_float32_0_1"),
    (9, "assignment_tick_nominal_path_valid_mask", "E", "EVENT_SPECIFIC",
     ("M", "N"), "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (),
     "assignment_tick_cost_path_valid_else_false", "policy_visible",
     "bool_to_float32_0_1"),
    (10, "assignment_tick_normalized_nominal_remaining_cost", "E",
     "EVENT_SPECIFIC", ("M", "N"), "torch.float32", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (),
     "assignment_tick_nominal_cost_else_zero", "policy_visible",
     "valid_cost_divide_episode_time_limit_else_zero"),
    (11, "target_action_mask", "F", "EVENT_SPECIFIC", ("M", "N"),
     "torch.bool", "torch.float32", "global_robot_id_outer_global_task_id_inner",
     (), "tick_policy_or_ordinary_forced_or_terminal_zero_target_mask",
     "policy_visible", "bool_to_float32_0_1"),
    (12, "noop_action_mask", "F", "EVENT_SPECIFIC", ("M",), "torch.bool",
     "torch.float32", "global_robot_id_ascending", (),
     "tick_policy_or_ordinary_forced_or_terminal_zero_noop_mask",
     "policy_visible", "bool_to_float32_0_1"),
    (13, "assignment_trigger_context", "F", "EVENT_SPECIFIC", ("M", 5),
     "torch.bool", "torch.float32", "global_robot_id_outer_column_order_inner",
     _TRIGGER_COLUMNS, "finalized_row_class_trigger_context", "policy_visible",
     "bool_to_float32_0_1"),
    (14, "per_robot_workload", "G", "REUSE_PRIMITIVE", ("M", 1),
     "torch.float32", "torch.float32", "global_robot_id_outer_column_order_inner",
     ("completed_task_fraction",), "authoritative_completion_attribution",
     "policy_visible", "completed_task_count_divide_N"),
    (15, "episode_context", "G", "REUSE_PRIMITIVE", (2,), "torch.float32",
     "torch.float32", "column_order",
     ("assignment_tick_present", "episode_progress_fraction"),
     "finalized_row_class_and_episode_progress", "policy_visible",
     "tick_identity_and_elapsed_steps_divide_horizon"),
)


def _records(field_order: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> tuple[Mapping[str, object], ...]:
    if any(len(row) != len(field_order) for row in rows):
        _fail("frozen descriptor record width mismatch")
    return tuple(dict(zip(field_order, row, strict=True)) for row in rows)


_NORMALIZATION_CONTRACT = {
    "normalization_contract_version": "event_gated_observation_normalization_v1",
    "position_length_denominator_source": "scale_contract.scene_env_spacing",
    "cost_denominator_source": "scale_contract.episode_time_limit_seconds",
    "episode_progress_denominator_source": "scale_contract.episode_horizon_steps",
    "quaternion_order": "wxyz",
    "quaternion_sign_rule": (
        "unit_then_qw_nonnegative_then_first_nonzero_xyz_positive_when_qw_zero"
    ),
    "invalid_cost_observation_fill": 0.0,
    "model_feature_normalization_contract": (
        "separate_model_layer_use_feature_normalization_identity"
    ),
}
_GENERATION_BINDING = {
    "association_key": (
        "env_id", "episode_generation", "transition_generation",
        "assignment_tick_generation",
    ),
    "required_equal_sources": (
        "lifecycle_transition_result",
        "local_set_result_when_assignment_tick_present",
        "nominal_pair_cost_result_when_assignment_tick_present",
        "decision_valid_mask_snapshot_when_assignment_tick_present",
    ),
    "mismatch_behavior": "fail_closed_before_observation_construction",
}
_ORDINARY_NO_TICK_CONTRACT = {
    "row_class": "nonterminal_forced_nondecision",
    "terminal": False,
    "assignment_tick_present": False,
    "semantic_action_count": 1,
    "decision_valid": False,
    "storage_row_present": True,
    "policy_proposal_present": False,
    "forced_nondecision_present": True,
    "actor_sampling": "not_called",
    "executing_action_rule": "current_task_only_and_noop_illegal",
    "nonexecuting_action_rule": (
        "deterministic_noop_only_storage_encoding_including_unavailable"
    ),
}
_TERMINAL_ROW_CONTRACT = {
    "row_class": "terminal_no_row",
    "terminal": True,
    "assignment_tick_present": False,
    "target_actions": "all_false",
    "noop_action": "all_false",
    "semantic_action_count": 0,
    "decision_valid": False,
    "forced_policy_action_id": -1,
    "storage_row_present": False,
    "policy_proposal_present": False,
    "forced_nondecision_present": False,
    "actor_sampling": "not_called",
    "resolver_consumption": False,
}
_ACTOR_EXCLUSIONS = (
    "nearest_or_local_task_repacking",
    "local_robot_or_task_renumbering",
    "previous_low_level_action",
    "attempt_count_or_age",
    "same_target_or_repeated_assignment_history",
    "contract_c_budget_state",
    "private_mutation_detector_or_capability",
    "raw_record_ids_or_generation_counters",
    "raw_event_payload",
    "policy_proposal",
    "proposal_log_probability",
    "proposal_acceptance_or_rejection",
    "same_tick_resolver_result",
    "same_tick_effective_assignment",
    "future_execution_facts",
)
_ACTOR_SCHEMA = {
    "schema_version": "event_gated_global_actor_observation_v1",
    "scope": "global_fixed_width_per_actor_complete_team_state_v1",
    "robot_reference_frame": "scenario_environment_local_cartesian_v1",
    "global_robot_order_source": "scale_contract.ordered_agent_names",
    "global_task_order_source": "scale_contract.ordered_task_ids",
    "output_dtype": "torch.float32",
    "flatten_order": (
        "block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner"
    ),
    "block_record_field_order": _ACTOR_BLOCK_RECORD_FIELD_ORDER,
    "block_count": 15,
    "blocks": _records(_ACTOR_BLOCK_RECORD_FIELD_ORDER, _ACTOR_BLOCK_ROWS),
    "dimension_formula": "6*M*N + 30*M + 14*N + 2",
    "reference_dimension": {"M": 3, "N": 50, "dimension": 1692},
    "normalization_contract": _NORMALIZATION_CONTRACT,
    "generation_binding": _GENERATION_BINDING,
    "temporal_boundary": (
        "fact_updated_a0_pre_policy_no_same_tick_resolver_outcome_v1"
    ),
    "ordinary_no_tick_contract": _ORDINARY_NO_TICK_CONTRACT,
    "terminal_row_contract": _TERMINAL_ROW_CONTRACT,
    "excluded_fields": _ACTOR_EXCLUSIONS,
}


_SHARED_BLOCK_RECORD_FIELD_ORDER = (
    "order", "name", "shape", "source_dtype", "serialized_dtype",
    "flatten_rule", "column_order", "visibility", "semantic_source",
    "construction_rule",
)
_SHARED_BLOCK_ROWS = (
    (1, "global_robot_physical_table", ("M", 16), "torch.float32",
     "torch.float32", "global_robot_id_outer_column_order_inner",
     _ROBOT_PHYSICAL_COLUMNS, "actor_visible",
     "finalized_pre_policy_global_robot_physical_state",
     "exact_actor_block_2_snapshot_stored_once_without_actor_identity"),
    (2, "global_robot_lifecycle_table", ("M", 5), "torch.bool",
     "torch.float32", "global_robot_id_outer_column_order_inner",
     _ROBOT_LIFECYCLE_COLUMNS, "actor_visible",
     "finalized_pre_policy_robot_lifecycle_state",
     "exact_actor_block_3_snapshot_stored_once_without_actor_identity"),
    (3, "global_task_pose_table", ("N", 7), "torch.float32", "torch.float32",
     "global_task_id_outer_column_order_inner", _TASK_POSE_COLUMNS,
     "actor_visible", "finalized_pre_policy_global_task_pose",
     "exact_actor_block_4_snapshot_stored_once_without_actor_identity"),
    (4, "global_task_lifecycle_one_hot", ("N", 6), "torch.bool",
     "torch.float32", "global_task_id_outer_column_order_inner",
     _TASK_LIFECYCLE_COLUMNS, "actor_visible",
     "finalized_pre_policy_task_lifecycle_state",
     "exact_actor_block_5_snapshot_stored_once_without_actor_identity"),
    (5, "event_updated_task_ownership_one_hot", ("N", "M+1"), "torch.bool",
     "torch.float32", "global_task_id_outer_global_robot_id_then_no_owner_inner",
     (), "actor_visible", "finalized_pre_policy_a0_ownership",
     "exact_actor_block_6_snapshot_stored_once_without_actor_identity"),
    (6, "event_updated_baseline_assignment_one_hot", ("M", "N+1"),
     "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_then_no_task_inner", (),
     "actor_visible", "finalized_pre_policy_a0_assignment",
     "exact_actor_block_7_snapshot_stored_once_without_actor_identity"),
    (7, "episode_permanent_failed_pair_mask", ("M", "N"), "torch.bool",
     "torch.float32", "global_robot_id_outer_global_task_id_inner", (),
     "actor_visible", "episode_cumulative_updated_failed_pairs",
     "exact_actor_block_8_snapshot_stored_once_without_actor_identity"),
    (8, "assignment_tick_nominal_path_valid_mask", ("M", "N"), "torch.bool",
     "torch.float32", "global_robot_id_outer_global_task_id_inner", (),
     "actor_visible", "assignment_tick_cost_path_valid_else_false",
     "exact_actor_block_9_snapshot_stored_once_without_actor_identity"),
    (9, "assignment_tick_normalized_nominal_remaining_cost", ("M", "N"),
     "torch.float32", "torch.float32", "global_robot_id_outer_global_task_id_inner",
     (), "actor_visible", "assignment_tick_nominal_cost_else_zero",
     "exact_actor_block_10_snapshot_stored_once_without_actor_identity"),
    (10, "target_action_mask", ("M", "N"), "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (), "actor_visible",
     "tick_policy_or_ordinary_forced_or_terminal_zero_target_mask",
     "exact_actor_block_11_snapshot_stored_once_without_actor_identity"),
    (11, "noop_action_mask", ("M",), "torch.bool", "torch.float32",
     "global_robot_id_ascending", (), "actor_visible",
     "tick_policy_or_ordinary_forced_or_terminal_zero_noop_mask",
     "exact_actor_block_12_snapshot_stored_once_without_actor_identity"),
    (12, "assignment_trigger_context", ("M", 5), "torch.bool",
     "torch.float32", "global_robot_id_outer_column_order_inner", _TRIGGER_COLUMNS,
     "actor_visible", "finalized_row_class_trigger_context",
     "exact_actor_block_13_snapshot_stored_once_without_actor_identity"),
    (13, "per_robot_workload", ("M", 1), "torch.float32", "torch.float32",
     "global_robot_id_outer_column_order_inner", ("completed_task_fraction",),
     "actor_visible", "authoritative_completion_attribution",
     "exact_actor_block_14_snapshot_stored_once_without_actor_identity"),
    (14, "episode_context", (2,), "torch.float32", "torch.float32",
     "column_order", ("assignment_tick_present", "episode_progress_fraction"),
     "actor_visible", "finalized_row_class_and_episode_progress",
     "exact_actor_block_15_snapshot_stored_once_without_actor_identity"),
    (15, "local_robot_mask", ("M",), "torch.bool", "torch.float32",
     "global_robot_id_ascending", (), "critic_only",
     "final_merged_local_set_robot_membership", "tick_result_else_all_false"),
    (16, "local_task_mask", ("N",), "torch.bool", "torch.float32",
     "global_task_id_ascending", (), "critic_only",
     "final_merged_local_set_task_membership", "tick_result_else_all_false"),
    (17, "owner_added_robot_mask", ("M",), "torch.bool", "torch.float32",
     "global_robot_id_ascending", (), "critic_only",
     "one_round_owner_expansion_attribution", "tick_result_else_all_false"),
    (18, "local_set_flags", (2,), "torch.bool", "torch.float32",
     "column_order", ("overlap_merged", "overflowed"), "critic_only",
     "final_merged_local_set_flags", "tick_result_else_all_false"),
    (19, "termination_reason_one_hot", (4,), "torch.bool", "torch.float32",
     "column_order",
     ("NONE", "ALL_TASKS_COMPLETED", "NO_FEASIBLE_TASKS_REMAIN", "TIME_LIMIT"),
     "critic_only", "pre_reset_finalized_lifecycle_transition_result",
     "exact_one_hot_for_same_transition"),
)
_TERMINAL_SHARED_STATE_CONTRACT = {
    "contract_version": "event_gated_terminal_shared_state_v1",
    "source_snapshot": "finalized_pre_reset_transition",
    "physical_lifecycle_a0_state": (
        "finalized_pre_reset_physical_lifecycle_a0_failed_workload_progress"
    ),
    "termination_reason_source": "LifecycleTransitionResult.termination_reason",
    "assignment_tick_present": False,
    "path_cost_blocks": "zero_value_and_false_validity",
    "local_set_blocks": "all_false",
    "semantic_action_masks": "all_false",
    "decision_valid": False,
    "storage_row_present": False,
    "policy_proposal_present": False,
    "forced_nondecision_present": False,
    "pre_reset_sidecar_required": True,
    "reset_state_alias_forbidden": True,
    "critic_buffer_ordering": "terminal_sidecar_before_new_episode_initial_row",
}
_SHARED_SCHEMA = {
    "schema_version": "event_gated_global_centralized_observation_v1",
    "construction_mode": "global_fixed_width_centralized_v1",
    "semantic_state_shape": ("E", "S"),
    "runner_transport_shape": ("E", "M", "S"),
    "critic_input_shape": ("B", "S"),
    "runner_transport_mode": (
        "repeat_identical_semantic_shared_state_across_agent_axis_v1"
    ),
    "output_dtype": "torch.float32",
    "flatten_order": (
        "block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner"
    ),
    "block_record_field_order": _SHARED_BLOCK_RECORD_FIELD_ORDER,
    "block_count": 19,
    "blocks": _records(_SHARED_BLOCK_RECORD_FIELD_ORDER, _SHARED_BLOCK_ROWS),
    "dimension_formula": "6*M*N + 31*M + 15*N + 8",
    "reference_dimension": {
        "M": 3, "N": 50, "semantic_dimension": 1751,
        "runner_agent_count": 3,
    },
    "normalization_contract_reference": "actor_schema.normalization_contract",
    "generation_binding": _GENERATION_BINDING,
    "temporal_boundary": (
        "fact_updated_pre_policy_or_terminal_pre_reset_no_same_tick_"
        "resolver_outcome_v1"
    ),
    "ordinary_no_tick_contract_reference": (
        "actor_schema.ordinary_no_tick_contract"
    ),
    "terminal_shared_state_contract": _TERMINAL_SHARED_STATE_CONTRACT,
    "excluded_fields": _ACTOR_EXCLUSIONS + (
        "actor_identity_one_hot", "duplicated_actor_observation_concat",
    ),
}


_TRIPLE_FIELD_ORDER = ("name", "owner_phase", "semantic_purpose")
_REFERENCE_RECORD_FIELD_ORDER = (
    "name", "triple_owner_module", "triple_owner_contract_version",
    "triple_descriptor_key_path", "expected_concrete_type", "unit",
    "legal_domain",
)
_MRTA_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract"
)
_EVENT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract"
)
_REWARD_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract"
)
_UNRESOLVED_PARAMETER_SPECS = (
    ("top_k_tasks_per_robot", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[0]", "exact_int",
     "tasks_per_robot", "1 <= value <= N", "phase_b_e",
     "maximum_nominal_cost_ranked_tasks_per_local_robot_before_current_task_retention"),
    ("local_robot_cap", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[1]", "exact_int",
     "robots", "1 <= value <= M", "phase_b",
     "maximum_robots_in_merged_local_assignment_set"),
    ("local_task_cap", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[2]", "exact_int",
     "tasks", "1 <= value <= N", "phase_b",
     "maximum_tasks_in_merged_local_assignment_set"),
    ("pair_abs_threshold", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[0]", "finite_float",
     "expected_time_seconds", "value >= 0", "phase_b_e",
     "strict_absolute_expected_time_improvement_for_active_preemption"),
    ("pair_rel_threshold", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[1]", "finite_float",
     "dimensionless_ratio", "0 <= value < 1", "phase_b_e",
     "strict_relative_expected_time_improvement_for_active_preemption"),
    ("component_abs_threshold", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[2]", "finite_float",
     "expected_time_seconds", "value >= 0", "phase_b_e",
     "strict_absolute_expected_time_improvement_for_equal_count_component_acceptance"),
    ("component_rel_threshold", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[3]", "finite_float",
     "dimensionless_ratio", "0 <= value < 1", "phase_b_e",
     "strict_relative_expected_time_improvement_for_equal_count_component_acceptance"),
    ("transfer_penalty", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[4]", "finite_float",
     "expected_time_seconds_per_owner_change", "value >= 0", "phase_b_e",
     "expected_time_regularizer_per_owner_change_in_equal_count_component_objective"),
    ("rejection_penalty_scale", _REWARD_MODULE,
     "assignment_team_reward_contract_v1", "unresolved_parameter", "finite_float",
     "team_reward_units_per_rejected_component", "value >= 0", "phase_d_e",
     "once_per_penalty_eligible_rejected_component"),
    ("alignment_time_constant", _MRTA_MODULE, "assignment_mrta_contract_v2",
     "cost_path_semantics.unresolved_parameters[0]", "tuple_finite_float_len_M",
     "expected_time_seconds_per_robot_entry",
     "len(value) == M AND all entries finite and >= 0 AND tuple index i == global robot_id i",
     "phase_b_e", "robot_specific_expected_terminal_alignment_time"),
    ("assignment_retry_cadence", _EVENT_MODULE, "assignment_event_contract_v2",
     "scheduled_assignment_opportunity_semantics.unresolved_parameter", "exact_int",
     "physical_transitions", "value >= 1", "phase_b",
     "physical_step_interval_for_persistent_unassigned_retry_opportunities"),
)
_INDEXED_SEGMENT = re.compile(r"^([a-z][a-z0-9_]*)\[([0-9]+)\]$")


def _resolve_key_path(root: object, path: str) -> object:
    current = root
    for segment in path.split("."):
        match = _INDEXED_SEGMENT.fullmatch(segment)
        if match is not None:
            if not isinstance(current, Mapping):
                _fail(f"key path enters non-mapping before {segment!r}")
            name, raw_index = match.groups()
            if name not in current:
                _fail(f"missing descriptor key {name!r} in path {path!r}")
            sequence = current[name]
            if type(sequence) is not tuple:
                _fail(f"indexed descriptor value is not tuple in path {path!r}")
            index = int(raw_index)
            if index >= len(sequence):
                _fail(f"descriptor index out of range in path {path!r}")
            current = sequence[index]
        else:
            if not isinstance(current, Mapping) or segment not in current:
                _fail(f"missing descriptor key segment {segment!r} in path {path!r}")
            current = current[segment]
    return current


def _domain_descriptor(module_name: str) -> Mapping[str, object]:
    if module_name == _MRTA_MODULE:
        descriptor = get_assignment_mrta_contract_descriptor()
    elif module_name == _EVENT_MODULE:
        descriptor = get_assignment_event_contract_descriptor()
    elif module_name == _REWARD_MODULE:
        descriptor = get_assignment_team_reward_contract_descriptor()
    else:
        _fail(f"unknown canonical unresolved-parameter owner module {module_name!r}")
    if not isinstance(descriptor, Mapping):
        _fail("domain descriptor getter returned a non-mapping")
    return descriptor


def _build_unresolved_parameter_inventory() -> Mapping[str, object]:
    references: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for spec in _UNRESOLVED_PARAMETER_SPECS:
        (
            name, module_name, version, path, concrete_type, unit, legal_domain,
            expected_owner, expected_purpose,
        ) = spec
        if name in seen:
            _fail(f"duplicate unresolved parameter {name!r}")
        seen.add(name)
        descriptor = _domain_descriptor(module_name)
        if descriptor.get("contract_version") != version:
            _fail(f"domain contract-version drift for {name!r}")
        triple = _resolve_key_path(descriptor, path)
        if not isinstance(triple, Mapping):
            _fail(f"domain triple path is not a mapping for {name!r}")
        keys = tuple(triple)
        if module_name == _REWARD_MODULE:
            expected_keys = _TRIPLE_FIELD_ORDER + (
                "required_type", "numeric_value_selected",
            )
        else:
            expected_keys = _TRIPLE_FIELD_ORDER
        if keys != expected_keys:
            _fail(f"domain triple field-order drift for {name!r}")
        actual_triple = tuple(triple[key] for key in _TRIPLE_FIELD_ORDER)
        expected_triple = (name, expected_owner, expected_purpose)
        if actual_triple != expected_triple:
            _fail(
                f"domain unresolved-parameter triple drift for {name!r}; "
                f"expected={expected_triple!r}; actual={actual_triple!r}"
            )
        try:
            UnresolvedParameterOwner(expected_owner)
        except ValueError as exc:
            raise AssignmentEventProfileSchemaContractError(
                f"unknown unresolved-parameter owner {expected_owner!r}"
            ) from exc
        references.append(
            dict(
                zip(
                    _REFERENCE_RECORD_FIELD_ORDER,
                    (name, module_name, version, path, concrete_type, unit, legal_domain),
                    strict=True,
                )
            )
        )
    expected_order = tuple(spec[0] for spec in _UNRESOLVED_PARAMETER_SPECS)
    if len(seen) != 11 or len(expected_order) != 11:
        _fail("unresolved parameter inventory must contain exactly 11 unique items")
    return _deep_readonly(
        {
            "contract_version": EVENT_GATED_UNRESOLVED_PARAMETER_INVENTORY_VERSION,
            "owner_enum_order": tuple(owner.value for owner in UnresolvedParameterOwner),
            "triple_field_order": _TRIPLE_FIELD_ORDER,
            "reference_record_field_order": _REFERENCE_RECORD_FIELD_ORDER,
            "unresolved_parameter_order": expected_order,
            "unresolved_parameter_references": tuple(references),
        }
    )  # type: ignore[return-value]


_DECISION_VALID_TRAINING_CONTRACT = {
    "contract_version": EVENT_GATED_DECISION_VALID_TRAINING_CONTRACT_VERSION,
    "buffer_mask_shape": ("T+1", "E", 1),
    "training_slice": (
        "decision_valid_mask[:-1]_over_storage_row_present_nonterminal_rows_"
        "only_terminal_no_row_excluded"
    ),
    "actor_valid_equation": "actor_valid=active_mask AND decision_valid_mask",
    "policy_loss_reduction": (
        "masked_mean=sum(actor_valid*policy_loss)/sum(actor_valid)"
    ),
    "entropy_reduction": (
        "masked_mean=sum(actor_valid*entropy)/sum(actor_valid)"
    ),
    "advantage_population": (
        "per_actor_rollout_actor_valid_samples_only_ordinary_forced_"
        "nondecision_and_terminal_no_row_excluded"
    ),
    "zero_valid_actor_rule": (
        "skip_actor_forward_backward_optimizer_factor_and_logger_update"
    ),
    "singleton_advantage_rule": (
        "use_finite_raw_advantage_without_normalization"
    ),
    "multi_sample_advantage_rule": (
        "unbiased_false_mean_std;nonfinite_or_std_below_epsilon_uses_finite_"
        "raw_advantage"
    ),
    "advantage_std_epsilon": 0.00001,
    "empty_minibatch_rule": (
        "skip_minibatch_without_optimizer_step_and_normalize_logger_by_"
        "processed_updates"
    ),
    "rejected_proposal_included": True,
    "critic_dvm_usage": "not_used",
}
_SEQUENTIAL_FACTOR_CONTRACT = {
    "contract_version": EVENT_GATED_SEQUENTIAL_FACTOR_CONTRACT_VERSION,
    "factor_shape": ("T", "E", 1),
    "initial_value": 1.0,
    "agent_update_order_source": (
        "algo.fixed_order_current_false_uses_runner_random_permutation_rule"
    ),
    "raw_ratio_equation": (
        "raw_ratio=aggregate(exp(new_action_log_probability-"
        "old_action_log_probability))"
    ),
    "effective_ratio_equation": (
        "effective_ratio=torch.where(decision_valid_mask,raw_ratio,"
        "torch.ones_like(raw_ratio))"
    ),
    "factor_update_equation": "factor=factor*effective_ratio",
    "nondecision_identity": (
        "ordinary_forced_nondecision_effective_ratio_exactly_one"
    ),
    "per_agent_dvm_rule": (
        "each_actor_uses_its_own_decision_valid_mask_to_update_shared_factor"
    ),
    "zero_valid_actor_rule": (
        "zero_valid_actor_skips_ratio_evaluation_and_leaves_factor_unchanged"
    ),
    "agent_axis_rule": (
        "shared_factor_has_no_agent_axis;terminal_no_row_has_no_factor_or_"
        "action_row"
    ),
}
_MODEL_STRUCTURE = {
    "projection_version": EVENT_GATED_MODEL_STRUCTURE_PROJECTION_VERSION,
    "projection_status": "interface_identity_only_not_runtime_verified",
    "actor_class": "HAPPO/StochasticPolicy",
    "critic_class": "VCritic/VNet",
    "action_distribution_class": "Categorical",
    "actor_input_schema_version": "event_gated_global_actor_observation_v1",
    "actor_input_dimension_source": "actor_schema.dimension_formula",
    "critic_input_schema_version": "event_gated_global_centralized_observation_v1",
    "critic_input_dimension_source": "shared_schema.dimension_formula",
    "action_dimension_formula": "action_contract.action_dimension",
    "actor_hidden_sizes": (256, 256),
    "critic_hidden_sizes": (256, 256),
    "activation": "relu",
    "feature_normalization": True,
    "share_param": False,
    "number_of_actor_networks_formula": "action_contract.num_agents",
    "ordered_actor_network_names_source": "scale_contract.ordered_agent_names",
    "critic_architecture": "centralized_v_network",
    "harl_state_type": "EP",
    "use_recurrent_policy": False,
    "use_naive_recurrent_policy": False,
    "recurrent_n": 1,
    "initialization_method": "orthogonal_",
    "action_gain": 0.01,
    "serialization_mode": "state_dict",
    "save_entire_model": False,
    "state_dict_key_contract_version": "event_gated_state_dict_inventory_contract_v1",
    "state_dict_inventory_binding": "deferred_checkpoint_ready_manifest",
}


def _config_binding(
    source_path: str,
    expected_type: str,
    legal_domain: str,
    current_config_value: object,
) -> Mapping[str, object]:
    return {
        "source_path": source_path,
        "expected_type": expected_type,
        "legal_domain": legal_domain,
        "current_config_value": current_config_value,
        "semantic_status": "CONFIG_BOUND_CURRENT_IDENTITY",
        "runtime_evidence_status": "DEFERRED_RUNTIME_EVIDENCE",
    }


def _resolved_event_profile_mapping() -> Mapping[str, object]:
    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    mapping = resolved_assignment_profile_to_mapping(profile)
    if not isinstance(mapping, Mapping):
        _fail("resolved event profile serializer returned a non-mapping")
    if mapping.get("profile_contract_version") != ASSIGNMENT_PROFILE_CONTRACT_VERSION:
        _fail("resolved event profile contract-version drift")
    return mapping


def _build_training_contract() -> Mapping[str, object]:
    resolved = _resolved_event_profile_mapping()
    semantics = _resolve_key_path(resolved, "event_gated_target_semantics")
    training_identity = _resolve_key_path(
        resolved, "event_gated_target_semantics.training_semantic_contract"
    )
    if not isinstance(semantics, Mapping) or not isinstance(training_identity, Mapping):
        _fail("resolved event profile semantic references are malformed")
    expected_profile_values = {
        "algorithm_name": "happo",
        "state_type": "EP",
        "share_param": False,
        "use_recurrent_policy": False,
        "use_naive_recurrent_policy": False,
        "actor_buffer_generator": "feed_forward_generator_actor",
        "serialization_mode": "state_dict",
        "save_entire_model": False,
        "installed_harl_mutable": False,
    }
    for key, expected in expected_profile_values.items():
        if training_identity.get(key) != expected:
            _fail(f"resolved event profile training identity drift at {key!r}")
    if semantics.get("policy_sequence_route") != (
        "event_gated_decision_valid_feed_forward_v1"
    ):
        _fail("resolved event profile policy-sequence identity drift")
    algorithm = {
        "algorithm_family": "HAPPO",
        "algorithm_name": training_identity["algorithm_name"],
        "state_type": training_identity["state_type"],
        "share_param": training_identity["share_param"],
        "policy_sequence_mode": semantics["policy_sequence_route"],
        "use_recurrent_policy": training_identity["use_recurrent_policy"],
        "use_naive_recurrent_policy": training_identity[
            "use_naive_recurrent_policy"
        ],
        "actor_buffer_generator": training_identity["actor_buffer_generator"],
        "installed_harl_mutable": training_identity["installed_harl_mutable"],
    }
    rollout = {
        "time_axis": "fixed_physical_transitions",
        "episode_length_semantics": "transitions_per_rollout",
        "episode_length_config_binding": _config_binding(
            "train.episode_length", "exact_int",
            ">= 1 physical transitions", 1000
        ),
        "standard_gae": True,
        "use_gae_config_binding": _config_binding(
            "algo.use_gae", "exact_bool", "event contract requires true", True
        ),
        "gamma_config_binding": _config_binding(
            "algo.gamma", "finite_float", "0 < value <= 1", 0.99
        ),
        "gae_lambda_config_binding": _config_binding(
            "algo.gae_lambda", "finite_float", "0 <= value <= 1", 0.95
        ),
        "proper_time_limits_config_binding": _config_binding(
            "train.use_proper_time_limits", "exact_bool", "boolean", True
        ),
        "critic_reward_source": "broadcast_team_reward",
        "critic_return_sample_set": "all_valid_physical_steps",
        "decision_valid_excluded_from_gae_returns_critic": True,
        "valuenorm_enabled_config_binding": _config_binding(
            "train.use_valuenorm", "exact_bool", "boolean", True
        ),
        "valuenorm_source": "all_valid_physical_step_returns",
        "valuenorm_epsilon": 0.00001,
    }
    optimizer = {
        "optimizer_family": "Adam",
        "actor_learning_rate_binding": _config_binding(
            "model.lr", "finite_float", "value > 0", 0.0005
        ),
        "critic_learning_rate_binding": _config_binding(
            "model.critic_lr", "finite_float", "value > 0", 0.0005
        ),
        "optimizer_epsilon_binding": _config_binding(
            "model.opti_eps", "finite_float", "value > 0", 0.00001
        ),
        "weight_decay_binding": _config_binding(
            "model.weight_decay", "finite_float", "value >= 0", 0
        ),
    }
    ppo = {
        "ppo_epoch_binding": _config_binding(
            "algo.ppo_epoch", "exact_int", "value >= 1", 5
        ),
        "critic_epoch_binding": _config_binding(
            "algo.critic_epoch", "exact_int", "value >= 1", 5
        ),
        "actor_minibatches_binding": _config_binding(
            "algo.actor_num_mini_batch", "exact_int", "value >= 1", 2
        ),
        "critic_minibatches_binding": _config_binding(
            "algo.critic_num_mini_batch", "exact_int", "value >= 1", 2
        ),
        "clip_coefficient_binding": _config_binding(
            "algo.clip_param", "finite_float", "0 < value < 1", 0.2
        ),
        "value_loss_coefficient_binding": _config_binding(
            "algo.value_loss_coef", "finite_float", "value >= 0", 1
        ),
        "entropy_coefficient_binding": _config_binding(
            "algo.entropy_coef", "finite_float", "value >= 0", 0.01
        ),
        "gradient_clipping_enabled_binding": _config_binding(
            "algo.use_max_grad_norm", "exact_bool", "boolean", True
        ),
        "max_gradient_norm_binding": _config_binding(
            "algo.max_grad_norm", "finite_float", "value > 0", 10.0
        ),
        "clipped_value_loss_binding": _config_binding(
            "algo.use_clipped_value_loss", "exact_bool", "boolean", True
        ),
        "huber_loss_binding": _config_binding(
            "algo.use_huber_loss", "exact_bool", "boolean", True
        ),
        "huber_delta_binding": _config_binding(
            "algo.huber_delta", "finite_float", "value > 0", 10.0
        ),
        "action_aggregation_binding": _config_binding(
            "algo.action_aggregation", "exact_supported_string", "value == prod", "prod"
        ),
        "fixed_agent_order_binding": _config_binding(
            "algo.fixed_order", "exact_bool", "boolean", False
        ),
        "policy_active_masks_binding": _config_binding(
            "algo.use_policy_active_masks", "exact_bool", "boolean", True
        ),
    }
    serialization = {
        "serialization_mode": training_identity["serialization_mode"],
        "save_entire_model": training_identity["save_entire_model"],
        "state_dict_key_contract_version": (
            "event_gated_state_dict_inventory_contract_v1"
        ),
        "checkpoint_ready_inventory_required": True,
        "interface_descriptor_weight_use_authorized": False,
    }
    return _deep_readonly(
        {
            "projection_version": EVENT_GATED_TRAINING_CONTRACT_PROJECTION_VERSION,
            "algorithm_identity": algorithm,
            "rollout_return_semantics": rollout,
            "optimizer_config_identity": optimizer,
            "ppo_config_identity": ppo,
            "decision_valid_training_contract_ref": (
                EVENT_GATED_DECISION_VALID_TRAINING_CONTRACT_VERSION
            ),
            "sequential_factor_contract_ref": (
                EVENT_GATED_SEQUENTIAL_FACTOR_CONTRACT_VERSION
            ),
            "serialization_contract": serialization,
            "runtime_evidence_status": "DEFERRED_RUNTIME_EVIDENCE",
        }
    )  # type: ignore[return-value]


_V3_SECTION_OWNERSHIP_RECORD_FIELD_ORDER = (
    "order", "section_name", "owner_module", "owner_contract_version",
    "descriptor_key_path", "projection_mode",
)
_V3_SECTION_OWNERSHIP_ROWS = (
    (1, "identity", "assignment_profile_contract", "assignment_resolved_profile_v1",
     "resolved_event_profile_mapping", "canonical_reference"),
    (2, "scale", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "scale_contract",
     "inline_owned_mapping"),
    (3, "actor_schema", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "actor_schema",
     "inline_owned_mapping"),
    (4, "shared_schema", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "shared_schema",
     "inline_owned_mapping"),
    (5, "action_contract", "assignment_mrta_contract",
     "assignment_mrta_contract_v2", "action_contract", "canonical_reference"),
    (6, "transition_contract", "assignment_lifecycle_transition_contract",
     "assignment_lifecycle_transition_contract_v2", "$", "canonical_reference"),
    (7, "event_tick_contract", "assignment_event_contract",
     "assignment_event_contract_v2", "$", "canonical_reference"),
    (8, "local_candidate_contract", "assignment_mrta_contract",
     "assignment_mrta_contract_v2", "local_candidate_semantics",
     "canonical_reference"),
    (9, "cost_path_contract", "assignment_mrta_contract",
     "assignment_mrta_contract_v2", "cost_path_semantics", "canonical_reference"),
    (10, "decision_valid_training_contract",
     "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1",
     "decision_valid_training_contract", "inline_owned_mapping"),
    (11, "sequential_factor_contract", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "sequential_factor_contract",
     "inline_owned_mapping"),
    (12, "component_contract", "assignment_mrta_contract",
     "assignment_mrta_contract_v2", "component_semantics", "canonical_reference"),
    (13, "reward_contract", "assignment_team_reward_contract",
     "assignment_team_reward_contract_v1", "$", "canonical_reference"),
    (14, "failure_termination_contract",
     "assignment_lifecycle_transition_contract",
     "assignment_lifecycle_transition_contract_v2",
     "failure_termination_semantics", "canonical_reference"),
    (15, "diagnostics_contract", "assignment_event_gated_diagnostics_contract",
     "assignment_event_gated_diagnostics_contract_v1", "$", "canonical_reference"),
    (16, "policy_sequence_contract", "assignment_profile_contract",
     "assignment_resolved_profile_v1",
     "resolved_event_profile_mapping.event_gated_target_semantics",
     "canonical_reference"),
    (17, "model_structure", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "model_structure",
     "inline_owned_mapping"),
    (18, "training_contract", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "training_contract",
     "inline_owned_mapping"),
    (19, "runtime_readiness_contract", "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1", "runtime_readiness_contract",
     "inline_owned_mapping"),
)
_V3_SECTION_OWNERSHIP_RECORDS = _records(
    _V3_SECTION_OWNERSHIP_RECORD_FIELD_ORDER,
    _V3_SECTION_OWNERSHIP_ROWS,
)


def _owner_roots(aggregate: Mapping[str, object]) -> Mapping[str, object]:
    resolved_profile_root = {
        "resolved_event_profile_mapping": _resolved_event_profile_mapping()
    }
    return {
        "assignment_profile_contract": resolved_profile_root,
        "assignment_event_profile_schema_contract": aggregate,
        "assignment_lifecycle_transition_contract": (
            get_assignment_lifecycle_transition_schema_descriptor()
        ),
        "assignment_event_contract": get_assignment_event_contract_descriptor(),
        "assignment_mrta_contract": get_assignment_mrta_contract_descriptor(),
        "assignment_team_reward_contract": (
            get_assignment_team_reward_contract_descriptor()
        ),
        "assignment_event_gated_diagnostics_contract": (
            get_assignment_event_gated_diagnostics_descriptor()
        ),
    }


def _validate_and_build_ownership(
    aggregate: Mapping[str, object],
) -> Mapping[str, object]:
    expected_sections = tuple(row[1] for row in _V3_SECTION_OWNERSHIP_ROWS)
    if type(_V3_SECTION_OWNERSHIP_RECORDS) is not tuple or len(
        _V3_SECTION_OWNERSHIP_RECORDS
    ) != 19:
        _fail("V3 ownership must contain exactly 19 records")
    roots = _owner_roots(aggregate)
    seen: set[str] = set()
    ordered_sections: list[str] = []
    validated: list[Mapping[str, object]] = []
    for expected_order, record in enumerate(_V3_SECTION_OWNERSHIP_RECORDS, 1):
        if not isinstance(record, Mapping):
            _fail("V3 ownership record must be a mapping")
        if tuple(record) != _V3_SECTION_OWNERSHIP_RECORD_FIELD_ORDER:
            _fail("V3 ownership record has missing, unknown, or reordered fields")
        if record["order"] != expected_order:
            _fail("V3 ownership record order must be exact 1..19")
        section = record["section_name"]
        if type(section) is not str or section in seen:
            _fail("V3 ownership section must be a unique exact string")
        seen.add(section)
        ordered_sections.append(section)
        basename = record["owner_module"]
        if type(basename) is not str or basename not in roots:
            _fail(f"unknown canonical V3 owner basename {basename!r}")
        mode = record["projection_mode"]
        if mode not in ("inline_owned_mapping", "canonical_reference"):
            _fail(f"unknown V3 ownership projection mode {mode!r}")
        path = record["descriptor_key_path"]
        if type(path) is not str:
            _fail("V3 ownership descriptor key path must be an exact string")
        root = roots[basename]
        if path == "$":
            resolved_value = root
        else:
            resolved_value = _resolve_key_path(root, path)
        if resolved_value is None:
            _fail(f"V3 ownership path resolves to no value for {section!r}")
        expected_version = record["owner_contract_version"]
        if basename == "assignment_profile_contract":
            profile_map = roots[basename]["resolved_event_profile_mapping"]  # type: ignore[index]
            actual_version = profile_map["profile_contract_version"]  # type: ignore[index]
        else:
            actual_version = root["contract_version"]  # type: ignore[index]
        if actual_version != expected_version:
            _fail(f"V3 ownership owner-contract version drift for {section!r}")
        validated.append(dict(record))
    if tuple(ordered_sections) != expected_sections:
        _fail("V3 ownership section order drift")
    return _deep_readonly(
        {
            "contract_version": EVENT_GATED_V3_SECTION_OWNERSHIP_VERSION,
            "section_order": expected_sections,
            "record_field_order": _V3_SECTION_OWNERSHIP_RECORD_FIELD_ORDER,
            "records": tuple(validated),
            "unique_authority_rule": (
                "exactly_one_owner_per_semantic_field_no_documentary_fallback"
            ),
        }
    )  # type: ignore[return-value]


def validate_event_profile_domain_references() -> None:
    """Re-run the exact eleven canonical domain version/path/triple checks."""

    _build_unresolved_parameter_inventory()


def validate_event_profile_v3_section_ownership_record(
    record: Mapping[str, object],
    *,
    aggregate_descriptor: Mapping[str, object],
    resolved_event_profile_mapping: Mapping[str, object] | None = None,
) -> None:
    """Validate one exact frozen ownership record without bare imports."""

    if not isinstance(record, Mapping) or tuple(
        record
    ) != _V3_SECTION_OWNERSHIP_RECORD_FIELD_ORDER:
        _fail("V3 ownership record has missing, unknown, or reordered fields")
    order = record["order"]
    if type(order) is not int or not 1 <= order <= len(_V3_SECTION_OWNERSHIP_ROWS):
        _fail("V3 ownership record order must be an exact int in 1..19")
    actual = tuple(record[key] for key in record)
    if actual != _V3_SECTION_OWNERSHIP_ROWS[order - 1]:
        _fail("V3 ownership record differs from the exact frozen inventory")
    basename = record["owner_module"]
    if type(basename) is not str:
        _fail("V3 owner module basename must be an exact string")
    mode = record["projection_mode"]
    if mode not in ("inline_owned_mapping", "canonical_reference"):
        _fail(f"unknown V3 ownership projection mode {mode!r}")
    resolved_profile = (
        _resolved_event_profile_mapping()
        if resolved_event_profile_mapping is None
        else resolved_event_profile_mapping
    )
    roots = {
        "assignment_profile_contract": {
            "resolved_event_profile_mapping": resolved_profile
        },
        "assignment_event_profile_schema_contract": aggregate_descriptor,
        "assignment_lifecycle_transition_contract": (
            get_assignment_lifecycle_transition_schema_descriptor()
        ),
        "assignment_event_contract": get_assignment_event_contract_descriptor(),
        "assignment_mrta_contract": get_assignment_mrta_contract_descriptor(),
        "assignment_team_reward_contract": (
            get_assignment_team_reward_contract_descriptor()
        ),
        "assignment_event_gated_diagnostics_contract": (
            get_assignment_event_gated_diagnostics_descriptor()
        ),
    }
    if basename not in roots:
        _fail(f"unknown canonical V3 owner basename {basename!r}")
    root = roots[basename]
    path = record["descriptor_key_path"]
    if type(path) is not str:
        _fail("V3 ownership descriptor key path must be an exact string")
    if path != "$":
        _resolve_key_path(root, path)
    if basename == "assignment_profile_contract":
        actual_version = resolved_profile.get("profile_contract_version")
    else:
        actual_version = root.get("contract_version")
    if actual_version != record["owner_contract_version"]:
        _fail(f"V3 ownership owner-contract version drift for order {order}")


def build_assignment_event_profile_schema_descriptor(
    *, scale_contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Build the exact aggregate from caller-resolved pure scale values.

    Every build revalidates lower-level public descriptor versions, paths, and
    domain-owned unresolved-parameter triples.  No runtime/config source is
    read by this function.
    """

    scale = _validated_scale_copy(scale_contract)
    inventory = _build_unresolved_parameter_inventory()
    training = _build_training_contract()
    readiness = {
        "projection_version": EVENT_GATED_RUNTIME_READINESS_PROJECTION_VERSION,
        "profile_runtime_readiness_ref": {
            "canonical_module": (
                "isaaclab_tasks.direct.scan_mobile_manipulator."
                "assignment_profile_contract"
            ),
            "descriptor_key_path": (
                "resolved_event_profile_mapping.runtime_readiness"
            ),
            "expected_value": "interface_only",
        },
        "unresolved_parameter_inventory_projection": inventory,
        "unresolved_parameter_resolution_status": "all_11_unresolved",
        "runtime_execution_authorized": False,
        "checkpoint_weight_use_authorized": False,
    }
    resolved_profile = _resolved_event_profile_mapping()
    if resolved_profile.get("runtime_readiness") != "interface_only":
        _fail("profile runtime-readiness reference drift")
    mutable_root: dict[str, object] = {
        "contract_version": ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION,
        "scale_contract": scale,
        "actor_schema": _ACTOR_SCHEMA,
        "shared_schema": _SHARED_SCHEMA,
        "unresolved_parameter_inventory": inventory,
        "decision_valid_training_contract": _DECISION_VALID_TRAINING_CONTRACT,
        "sequential_factor_contract": _SEQUENTIAL_FACTOR_CONTRACT,
        "model_structure": _MODEL_STRUCTURE,
        "training_contract": training,
        "runtime_readiness_contract": readiness,
    }
    ownership = _validate_and_build_ownership(mutable_root)
    mutable_root["v3_section_ownership"] = ownership
    result = _deep_readonly(mutable_root)
    expected_root_order = (
        "contract_version", "scale_contract", "actor_schema", "shared_schema",
        "unresolved_parameter_inventory", "decision_valid_training_contract",
        "sequential_factor_contract", "model_structure", "training_contract",
        "runtime_readiness_contract", "v3_section_ownership",
    )
    if tuple(result) != expected_root_order:  # type: ignore[arg-type]
        _fail("event-profile aggregate root key order drift")
    return result  # type: ignore[return-value]


def get_assignment_event_profile_schema_descriptor(
    *, scale_contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Return a freshly validated descriptor for caller-resolved pure scale.

    This getter intentionally has no scenario-derived default: A3x-1 is a pure
    descriptor slice and only accepts scale values explicitly resolved by its
    caller.
    """

    return build_assignment_event_profile_schema_descriptor(
        scale_contract=scale_contract
    )


__all__ = [
    "ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION",
    "AssignmentEventProfileSchemaContractError",
    "CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_MODULE",
    "EVENT_GATED_DECISION_VALID_TRAINING_CONTRACT_VERSION",
    "EVENT_GATED_MODEL_STRUCTURE_PROJECTION_VERSION",
    "EVENT_GATED_RUNTIME_READINESS_PROJECTION_VERSION",
    "EVENT_GATED_SCALE_CONTRACT_VERSION",
    "EVENT_GATED_SEQUENTIAL_FACTOR_CONTRACT_VERSION",
    "EVENT_GATED_TRAINING_CONTRACT_PROJECTION_VERSION",
    "EVENT_GATED_UNRESOLVED_PARAMETER_INVENTORY_VERSION",
    "EVENT_GATED_V3_SECTION_OWNERSHIP_VERSION",
    "UnresolvedParameterOwner",
    "actor_obs_dim",
    "build_assignment_event_profile_schema_descriptor",
    "build_event_gated_scale_contract",
    "get_assignment_event_profile_schema_descriptor",
    "shared_obs_dim",
    "validate_event_profile_domain_references",
    "validate_event_profile_v3_section_ownership_record",
]
