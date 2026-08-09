"""Pure regressions for the Phase A3x-1 event-profile schema descriptor.

The suite installs namespace packages only, imports the six lower-level
contracts and the aggregate contract by their canonical module keys, and never
imports normal Isaac Lab task discovery.  It performs no environment/runtime,
HARL, checkpoint, model, optimizer, training, playback, or evaluation work.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
MODULE_BASENAMES = (
    "assignment_profile_contract",
    "assignment_lifecycle_transition_contract",
    "assignment_event_contract",
    "assignment_mrta_contract",
    "assignment_team_reward_contract",
    "assignment_event_gated_diagnostics_contract",
    "assignment_event_profile_schema_contract",
)
MODULE_PATHS = {
    f"{PACKAGE}.{basename}": SCAN_SOURCE / f"{basename}.py"
    for basename in MODULE_BASENAMES
}
SCHEMA_KEY = f"{PACKAGE}.assignment_event_profile_schema_contract"

ROOT_KEYS = (
    "contract_version",
    "scale_contract",
    "actor_schema",
    "shared_schema",
    "unresolved_parameter_inventory",
    "decision_valid_training_contract",
    "sequential_factor_contract",
    "model_structure",
    "training_contract",
    "runtime_readiness_contract",
    "v3_section_ownership",
)
SCALE_KEYS = (
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
ACTOR_KEYS = (
    "schema_version",
    "scope",
    "robot_reference_frame",
    "global_robot_order_source",
    "global_task_order_source",
    "output_dtype",
    "flatten_order",
    "block_record_field_order",
    "block_count",
    "blocks",
    "dimension_formula",
    "reference_dimension",
    "normalization_contract",
    "generation_binding",
    "temporal_boundary",
    "ordinary_no_tick_contract",
    "terminal_row_contract",
    "excluded_fields",
)
ACTOR_BLOCK_KEYS = (
    "order",
    "name",
    "category",
    "treatment",
    "shape",
    "source_dtype",
    "serialized_dtype",
    "flatten_rule",
    "column_order",
    "semantic_source",
    "visibility",
    "normalization_rule",
)
ROBOT_PHYSICAL_COLUMNS = (
    "base_x", "base_y", "base_z", "base_yaw_sin", "base_yaw_cos",
    "scanner_x", "scanner_y", "scanner_z", "scanner_qw", "scanner_qx",
    "scanner_qy", "scanner_qz", "arm_reach", "scanner_min_range",
    "scanner_max_range", "scanner_fov_cos",
)
ROBOT_LIFECYCLE_COLUMNS = (
    "EXECUTING", "NEEDS_ASSIGNMENT", "WAITING_FOR_TASK", "UNAVAILABLE",
    "robot_available",
)
TASK_POSE_COLUMNS = (
    "task_x", "task_y", "task_z", "task_qw", "task_qx", "task_qy",
    "task_qz",
)
TASK_LIFECYCLE_COLUMNS = (
    "AVAILABLE", "CLAIMED", "NAVIGATING", "ALIGNING", "COMPLETED",
    "TEAM_INFEASIBLE",
)
TRIGGER_COLUMNS = (
    "lifecycle_event_seed", "scheduled_retry_opportunity",
    "decision_opportunity_present", "decision_valid",
    "current_task_continue_legal",
)
EXPECTED_ACTOR_BLOCKS = (
    (1, "actor_robot_identity_one_hot", "A", "EVENT_SPECIFIC", ("M",),
     "torch.bool", "torch.float32", "global_robot_id_ascending", (),
     "actor_id_against_scale_contract_ordered_agent_names", "policy_visible",
     "bool_to_float32_0_1"),
    (2, "global_robot_physical_table", "B", "REUSE_PRIMITIVE", ("M", 16),
     "torch.float32", "torch.float32",
     "global_robot_id_outer_column_order_inner", ROBOT_PHYSICAL_COLUMNS,
     "finalized_pre_policy_global_robot_physical_state", "policy_visible",
     "robot_physical_normalization_v1"),
    (3, "global_robot_lifecycle_table", "B", "EVENT_SPECIFIC", ("M", 5),
     "torch.bool", "torch.float32",
     "global_robot_id_outer_column_order_inner", ROBOT_LIFECYCLE_COLUMNS,
     "finalized_pre_policy_robot_lifecycle_state", "policy_visible",
     "bool_to_float32_0_1"),
    (4, "global_task_pose_table", "C", "REUSE_PRIMITIVE", ("N", 7),
     "torch.float32", "torch.float32",
     "global_task_id_outer_column_order_inner", TASK_POSE_COLUMNS,
     "finalized_pre_policy_global_task_pose", "policy_visible",
     "task_pose_normalization_v1"),
    (5, "global_task_lifecycle_one_hot", "C", "EVENT_SPECIFIC", ("N", 6),
     "torch.bool", "torch.float32",
     "global_task_id_outer_column_order_inner", TASK_LIFECYCLE_COLUMNS,
     "finalized_pre_policy_task_lifecycle_state", "policy_visible",
     "bool_to_float32_0_1"),
    (6, "event_updated_task_ownership_one_hot", "D", "REUSE_PRIMITIVE",
     ("N", "M+1"), "torch.bool", "torch.float32",
     "global_task_id_outer_global_robot_id_then_no_owner_inner", (),
     "finalized_pre_policy_a0_ownership", "policy_visible",
     "bool_to_float32_0_1"),
    (7, "event_updated_baseline_assignment_one_hot", "D", "REUSE_PRIMITIVE",
     ("M", "N+1"), "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_then_no_task_inner", (),
     "finalized_pre_policy_a0_assignment", "policy_visible",
     "bool_to_float32_0_1"),
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
     "torch.bool", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (),
     "tick_policy_or_ordinary_forced_or_terminal_zero_target_mask",
     "policy_visible", "bool_to_float32_0_1"),
    (12, "noop_action_mask", "F", "EVENT_SPECIFIC", ("M",),
     "torch.bool", "torch.float32", "global_robot_id_ascending", (),
     "tick_policy_or_ordinary_forced_or_terminal_zero_noop_mask",
     "policy_visible", "bool_to_float32_0_1"),
    (13, "assignment_trigger_context", "F", "EVENT_SPECIFIC", ("M", 5),
     "torch.bool", "torch.float32",
     "global_robot_id_outer_column_order_inner", TRIGGER_COLUMNS,
     "finalized_row_class_trigger_context", "policy_visible",
     "bool_to_float32_0_1"),
    (14, "per_robot_workload", "G", "REUSE_PRIMITIVE", ("M", 1),
     "torch.float32", "torch.float32",
     "global_robot_id_outer_column_order_inner", ("completed_task_fraction",),
     "authoritative_completion_attribution", "policy_visible",
     "completed_task_count_divide_N"),
    (15, "episode_context", "G", "REUSE_PRIMITIVE", (2,),
     "torch.float32", "torch.float32", "column_order",
     ("assignment_tick_present", "episode_progress_fraction"),
     "finalized_row_class_and_episode_progress", "policy_visible",
     "tick_identity_and_elapsed_steps_divide_horizon"),
)

NORMALIZATION_KEYS = (
    "normalization_contract_version",
    "position_length_denominator_source",
    "cost_denominator_source",
    "episode_progress_denominator_source",
    "quaternion_order",
    "quaternion_sign_rule",
    "invalid_cost_observation_fill",
    "model_feature_normalization_contract",
)
EXPECTED_NORMALIZATION_VALUES = (
    "event_gated_observation_normalization_v1",
    "scale_contract.scene_env_spacing",
    "scale_contract.episode_time_limit_seconds",
    "scale_contract.episode_horizon_steps",
    "wxyz",
    "unit_then_qw_nonnegative_then_first_nonzero_xyz_positive_when_qw_zero",
    0.0,
    "separate_model_layer_use_feature_normalization_identity",
)
GENERATION_KEYS = ("association_key", "required_equal_sources", "mismatch_behavior")
EXPECTED_GENERATION_VALUES = (
    ("env_id", "episode_generation", "transition_generation",
     "assignment_tick_generation"),
    ("lifecycle_transition_result",
     "local_set_result_when_assignment_tick_present",
     "nominal_pair_cost_result_when_assignment_tick_present",
     "decision_valid_mask_snapshot_when_assignment_tick_present"),
    "fail_closed_before_observation_construction",
)
ORDINARY_KEYS = (
    "row_class", "terminal", "assignment_tick_present",
    "semantic_action_count", "decision_valid", "storage_row_present",
    "policy_proposal_present", "forced_nondecision_present", "actor_sampling",
    "executing_action_rule", "nonexecuting_action_rule",
)
EXPECTED_ORDINARY_VALUES = (
    "nonterminal_forced_nondecision", False, False, 1, False, True, False,
    True, "not_called", "current_task_only_and_noop_illegal",
    "deterministic_noop_only_storage_encoding_including_unavailable",
)
TERMINAL_KEYS = (
    "row_class", "terminal", "assignment_tick_present", "target_actions",
    "noop_action", "semantic_action_count", "decision_valid",
    "forced_policy_action_id", "storage_row_present", "policy_proposal_present",
    "forced_nondecision_present", "actor_sampling", "resolver_consumption",
)
EXPECTED_TERMINAL_VALUES = (
    "terminal_no_row", True, False, "all_false", "all_false", 0, False, -1,
    False, False, False, "not_called", False,
)
ACTOR_EXCLUSIONS = (
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

SHARED_KEYS = (
    "schema_version", "construction_mode", "semantic_state_shape",
    "runner_transport_shape", "critic_input_shape", "runner_transport_mode",
    "output_dtype", "flatten_order", "block_record_field_order", "block_count",
    "blocks", "dimension_formula", "reference_dimension",
    "normalization_contract_reference", "generation_binding",
    "temporal_boundary", "ordinary_no_tick_contract_reference",
    "terminal_shared_state_contract", "excluded_fields",
)
SHARED_BLOCK_KEYS = (
    "order", "name", "shape", "source_dtype", "serialized_dtype",
    "flatten_rule", "column_order", "visibility", "semantic_source",
    "construction_rule",
)
EXPECTED_SHARED_BLOCKS = (
    (1, "global_robot_physical_table", ("M", 16), "torch.float32",
     "torch.float32", "global_robot_id_outer_column_order_inner",
     ROBOT_PHYSICAL_COLUMNS, "actor_visible",
     "finalized_pre_policy_global_robot_physical_state",
     "exact_actor_block_2_snapshot_stored_once_without_actor_identity"),
    (2, "global_robot_lifecycle_table", ("M", 5), "torch.bool",
     "torch.float32", "global_robot_id_outer_column_order_inner",
     ROBOT_LIFECYCLE_COLUMNS, "actor_visible",
     "finalized_pre_policy_robot_lifecycle_state",
     "exact_actor_block_3_snapshot_stored_once_without_actor_identity"),
    (3, "global_task_pose_table", ("N", 7), "torch.float32", "torch.float32",
     "global_task_id_outer_column_order_inner", TASK_POSE_COLUMNS,
     "actor_visible", "finalized_pre_policy_global_task_pose",
     "exact_actor_block_4_snapshot_stored_once_without_actor_identity"),
    (4, "global_task_lifecycle_one_hot", ("N", 6), "torch.bool",
     "torch.float32", "global_task_id_outer_column_order_inner",
     TASK_LIFECYCLE_COLUMNS, "actor_visible",
     "finalized_pre_policy_task_lifecycle_state",
     "exact_actor_block_5_snapshot_stored_once_without_actor_identity"),
    (5, "event_updated_task_ownership_one_hot", ("N", "M+1"), "torch.bool",
     "torch.float32",
     "global_task_id_outer_global_robot_id_then_no_owner_inner", (),
     "actor_visible", "finalized_pre_policy_a0_ownership",
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
     "torch.float32", "torch.float32",
     "global_robot_id_outer_global_task_id_inner", (), "actor_visible",
     "assignment_tick_nominal_cost_else_zero",
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
     "torch.float32", "global_robot_id_outer_column_order_inner",
     TRIGGER_COLUMNS, "actor_visible", "finalized_row_class_trigger_context",
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
TERMINAL_SHARED_KEYS = (
    "contract_version", "source_snapshot", "physical_lifecycle_a0_state",
    "termination_reason_source", "assignment_tick_present", "path_cost_blocks",
    "local_set_blocks", "semantic_action_masks", "decision_valid",
    "storage_row_present", "policy_proposal_present",
    "forced_nondecision_present", "pre_reset_sidecar_required",
    "reset_state_alias_forbidden", "critic_buffer_ordering",
)
EXPECTED_TERMINAL_SHARED_VALUES = (
    "event_gated_terminal_shared_state_v1", "finalized_pre_reset_transition",
    "finalized_pre_reset_physical_lifecycle_a0_failed_workload_progress",
    "LifecycleTransitionResult.termination_reason", False,
    "zero_value_and_false_validity", "all_false", "all_false", False, False,
    False, False, True, True, "terminal_sidecar_before_new_episode_initial_row",
)
SHARED_EXCLUSIONS = ACTOR_EXCLUSIONS + (
    "actor_identity_one_hot", "duplicated_actor_observation_concat",
)

UNRESOLVED_KEYS = (
    "contract_version", "owner_enum_order", "triple_field_order",
    "reference_record_field_order", "unresolved_parameter_order",
    "unresolved_parameter_references",
)
REFERENCE_KEYS = (
    "name", "triple_owner_module", "triple_owner_contract_version",
    "triple_descriptor_key_path", "expected_concrete_type", "unit",
    "legal_domain",
)
UNRESOLVED_NAMES = (
    "top_k_tasks_per_robot", "local_robot_cap", "local_task_cap",
    "pair_abs_threshold", "pair_rel_threshold", "component_abs_threshold",
    "component_rel_threshold", "transfer_penalty", "rejection_penalty_scale",
    "alignment_time_constant", "assignment_retry_cadence",
)
MRTA_MODULE = f"{PACKAGE}.assignment_mrta_contract"
EVENT_MODULE = f"{PACKAGE}.assignment_event_contract"
REWARD_MODULE = f"{PACKAGE}.assignment_team_reward_contract"
EXPECTED_REFERENCES = (
    ("top_k_tasks_per_robot", MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[0]", "exact_int",
     "tasks_per_robot", "1 <= value <= N"),
    ("local_robot_cap", MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[1]", "exact_int",
     "robots", "1 <= value <= M"),
    ("local_task_cap", MRTA_MODULE, "assignment_mrta_contract_v2",
     "local_candidate_semantics.unresolved_parameters[2]", "exact_int",
     "tasks", "1 <= value <= N"),
    ("pair_abs_threshold", MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[0]", "finite_float",
     "expected_time_seconds", "value >= 0"),
    ("pair_rel_threshold", MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[1]", "finite_float",
     "dimensionless_ratio", "0 <= value < 1"),
    ("component_abs_threshold", MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[2]", "finite_float",
     "expected_time_seconds", "value >= 0"),
    ("component_rel_threshold", MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[3]", "finite_float",
     "dimensionless_ratio", "0 <= value < 1"),
    ("transfer_penalty", MRTA_MODULE, "assignment_mrta_contract_v2",
     "component_semantics.unresolved_parameters[4]", "finite_float",
     "expected_time_seconds_per_owner_change", "value >= 0"),
    ("rejection_penalty_scale", REWARD_MODULE,
     "assignment_team_reward_contract_v1", "unresolved_parameter",
     "finite_float", "team_reward_units_per_rejected_component",
     "value >= 0"),
    ("alignment_time_constant", MRTA_MODULE, "assignment_mrta_contract_v2",
     "cost_path_semantics.unresolved_parameters[0]",
     "tuple_finite_float_len_M", "expected_time_seconds_per_robot_entry",
     "len(value) == M AND all entries finite and >= 0 AND tuple index i == global robot_id i"),
    ("assignment_retry_cadence", EVENT_MODULE, "assignment_event_contract_v2",
     "scheduled_assignment_opportunity_semantics.unresolved_parameter",
     "exact_int", "physical_transitions", "value >= 1"),
)
EXPECTED_DOMAIN_TRIPLES = (
    ("top_k_tasks_per_robot", "phase_b_e",
     "maximum_nominal_cost_ranked_tasks_per_local_robot_before_current_task_retention"),
    ("local_robot_cap", "phase_b",
     "maximum_robots_in_merged_local_assignment_set"),
    ("local_task_cap", "phase_b",
     "maximum_tasks_in_merged_local_assignment_set"),
    ("pair_abs_threshold", "phase_b_e",
     "strict_absolute_expected_time_improvement_for_active_preemption"),
    ("pair_rel_threshold", "phase_b_e",
     "strict_relative_expected_time_improvement_for_active_preemption"),
    ("component_abs_threshold", "phase_b_e",
     "strict_absolute_expected_time_improvement_for_equal_count_component_acceptance"),
    ("component_rel_threshold", "phase_b_e",
     "strict_relative_expected_time_improvement_for_equal_count_component_acceptance"),
    ("transfer_penalty", "phase_b_e",
     "expected_time_regularizer_per_owner_change_in_equal_count_component_objective"),
    ("rejection_penalty_scale", "phase_d_e",
     "once_per_penalty_eligible_rejected_component"),
    ("alignment_time_constant", "phase_b_e",
     "robot_specific_expected_terminal_alignment_time"),
    ("assignment_retry_cadence", "phase_b",
     "physical_step_interval_for_persistent_unassigned_retry_opportunities"),
)

MODEL_KEYS = (
    "projection_version", "projection_status", "actor_class", "critic_class",
    "action_distribution_class", "actor_input_schema_version",
    "actor_input_dimension_source", "critic_input_schema_version",
    "critic_input_dimension_source", "action_dimension_formula",
    "actor_hidden_sizes", "critic_hidden_sizes", "activation",
    "feature_normalization", "share_param",
    "number_of_actor_networks_formula", "ordered_actor_network_names_source",
    "critic_architecture", "harl_state_type", "use_recurrent_policy",
    "use_naive_recurrent_policy", "recurrent_n", "initialization_method",
    "action_gain", "serialization_mode", "save_entire_model",
    "state_dict_key_contract_version", "state_dict_inventory_binding",
)
EXPECTED_MODEL_VALUES = (
    "event_gated_model_structure_projection_v1",
    "interface_identity_only_not_runtime_verified", "HAPPO/StochasticPolicy",
    "VCritic/VNet", "Categorical", "event_gated_global_actor_observation_v1",
    "actor_schema.dimension_formula",
    "event_gated_global_centralized_observation_v1",
    "shared_schema.dimension_formula", "action_contract.action_dimension",
    (256, 256), (256, 256), "relu", True, False,
    "action_contract.num_agents", "scale_contract.ordered_agent_names",
    "centralized_v_network", "EP", False, False, 1, "orthogonal_", 0.01,
    "state_dict", False, "event_gated_state_dict_inventory_contract_v1",
    "deferred_checkpoint_ready_manifest",
)
TRAINING_KEYS = (
    "projection_version", "algorithm_identity", "rollout_return_semantics",
    "optimizer_config_identity", "ppo_config_identity",
    "decision_valid_training_contract_ref", "sequential_factor_contract_ref",
    "serialization_contract", "runtime_evidence_status",
)
ALGORITHM_KEYS = (
    "algorithm_family", "algorithm_name", "state_type", "share_param",
    "policy_sequence_mode", "use_recurrent_policy",
    "use_naive_recurrent_policy", "actor_buffer_generator",
    "installed_harl_mutable",
)
ROLLOUT_KEYS = (
    "time_axis", "episode_length_semantics", "episode_length_config_binding",
    "standard_gae", "use_gae_config_binding", "gamma_config_binding",
    "gae_lambda_config_binding", "proper_time_limits_config_binding",
    "critic_reward_source", "critic_return_sample_set",
    "decision_valid_excluded_from_gae_returns_critic",
    "valuenorm_enabled_config_binding", "valuenorm_source", "valuenorm_epsilon",
)
OPTIMIZER_KEYS = (
    "optimizer_family", "actor_learning_rate_binding",
    "critic_learning_rate_binding", "optimizer_epsilon_binding",
    "weight_decay_binding",
)
PPO_KEYS = (
    "ppo_epoch_binding", "critic_epoch_binding", "actor_minibatches_binding",
    "critic_minibatches_binding", "clip_coefficient_binding",
    "value_loss_coefficient_binding", "entropy_coefficient_binding",
    "gradient_clipping_enabled_binding", "max_gradient_norm_binding",
    "clipped_value_loss_binding", "huber_loss_binding", "huber_delta_binding",
    "action_aggregation_binding", "fixed_agent_order_binding",
    "policy_active_masks_binding",
)
SERIALIZATION_KEYS = (
    "serialization_mode", "save_entire_model", "state_dict_key_contract_version",
    "checkpoint_ready_inventory_required",
    "interface_descriptor_weight_use_authorized",
)
BINDING_KEYS = (
    "source_path", "expected_type", "legal_domain", "current_config_value",
    "semantic_status", "runtime_evidence_status",
)
EXPECTED_BINDINGS = {
    "rollout_return_semantics.episode_length_config_binding":
        ("train.episode_length", "exact_int", ">= 1 physical transitions", 1000),
    "rollout_return_semantics.use_gae_config_binding":
        ("algo.use_gae", "exact_bool", "event contract requires true", True),
    "rollout_return_semantics.gamma_config_binding":
        ("algo.gamma", "finite_float", "0 < value <= 1", 0.99),
    "rollout_return_semantics.gae_lambda_config_binding":
        ("algo.gae_lambda", "finite_float", "0 <= value <= 1", 0.95),
    "rollout_return_semantics.proper_time_limits_config_binding":
        ("train.use_proper_time_limits", "exact_bool", "boolean", True),
    "rollout_return_semantics.valuenorm_enabled_config_binding":
        ("train.use_valuenorm", "exact_bool", "boolean", True),
    "optimizer_config_identity.actor_learning_rate_binding":
        ("model.lr", "finite_float", "value > 0", 0.0005),
    "optimizer_config_identity.critic_learning_rate_binding":
        ("model.critic_lr", "finite_float", "value > 0", 0.0005),
    "optimizer_config_identity.optimizer_epsilon_binding":
        ("model.opti_eps", "finite_float", "value > 0", 0.00001),
    "optimizer_config_identity.weight_decay_binding":
        ("model.weight_decay", "finite_float", "value >= 0", 0),
    "ppo_config_identity.ppo_epoch_binding":
        ("algo.ppo_epoch", "exact_int", "value >= 1", 5),
    "ppo_config_identity.critic_epoch_binding":
        ("algo.critic_epoch", "exact_int", "value >= 1", 5),
    "ppo_config_identity.actor_minibatches_binding":
        ("algo.actor_num_mini_batch", "exact_int", "value >= 1", 2),
    "ppo_config_identity.critic_minibatches_binding":
        ("algo.critic_num_mini_batch", "exact_int", "value >= 1", 2),
    "ppo_config_identity.clip_coefficient_binding":
        ("algo.clip_param", "finite_float", "0 < value < 1", 0.2),
    "ppo_config_identity.value_loss_coefficient_binding":
        ("algo.value_loss_coef", "finite_float", "value >= 0", 1),
    "ppo_config_identity.entropy_coefficient_binding":
        ("algo.entropy_coef", "finite_float", "value >= 0", 0.01),
    "ppo_config_identity.gradient_clipping_enabled_binding":
        ("algo.use_max_grad_norm", "exact_bool", "boolean", True),
    "ppo_config_identity.max_gradient_norm_binding":
        ("algo.max_grad_norm", "finite_float", "value > 0", 10.0),
    "ppo_config_identity.clipped_value_loss_binding":
        ("algo.use_clipped_value_loss", "exact_bool", "boolean", True),
    "ppo_config_identity.huber_loss_binding":
        ("algo.use_huber_loss", "exact_bool", "boolean", True),
    "ppo_config_identity.huber_delta_binding":
        ("algo.huber_delta", "finite_float", "value > 0", 10.0),
    "ppo_config_identity.action_aggregation_binding":
        ("algo.action_aggregation", "exact_supported_string", "value == prod", "prod"),
    "ppo_config_identity.fixed_agent_order_binding":
        ("algo.fixed_order", "exact_bool", "boolean", False),
    "ppo_config_identity.policy_active_masks_binding":
        ("algo.use_policy_active_masks", "exact_bool", "boolean", True),
}
DVM_KEYS = (
    "contract_version", "buffer_mask_shape", "training_slice",
    "actor_valid_equation", "policy_loss_reduction", "entropy_reduction",
    "advantage_population", "zero_valid_actor_rule",
    "singleton_advantage_rule", "multi_sample_advantage_rule",
    "advantage_std_epsilon", "empty_minibatch_rule",
    "rejected_proposal_included", "critic_dvm_usage",
)
EXPECTED_DVM_VALUES = (
    "event_gated_decision_valid_actor_training_v1",
    ("T+1", "E", 1),
    "decision_valid_mask[:-1]_over_storage_row_present_nonterminal_rows_only_terminal_no_row_excluded",
    "actor_valid=active_mask AND decision_valid_mask",
    "masked_mean=sum(actor_valid*policy_loss)/sum(actor_valid)",
    "masked_mean=sum(actor_valid*entropy)/sum(actor_valid)",
    "per_actor_rollout_actor_valid_samples_only_ordinary_forced_nondecision_and_terminal_no_row_excluded",
    "skip_actor_forward_backward_optimizer_factor_and_logger_update",
    "use_finite_raw_advantage_without_normalization",
    "unbiased_false_mean_std;nonfinite_or_std_below_epsilon_uses_finite_raw_advantage",
    0.00001,
    "skip_minibatch_without_optimizer_step_and_normalize_logger_by_processed_updates",
    True,
    "not_used",
)
FACTOR_KEYS = (
    "contract_version", "factor_shape", "initial_value",
    "agent_update_order_source", "raw_ratio_equation",
    "effective_ratio_equation", "factor_update_equation",
    "nondecision_identity", "per_agent_dvm_rule", "zero_valid_actor_rule",
    "agent_axis_rule",
)
EXPECTED_FACTOR_VALUES = (
    "event_gated_happo_sequential_factor_v1",
    ("T", "E", 1),
    1.0,
    "algo.fixed_order_current_false_uses_runner_random_permutation_rule",
    "raw_ratio=aggregate(exp(new_action_log_probability-old_action_log_probability))",
    "effective_ratio=torch.where(decision_valid_mask,raw_ratio,torch.ones_like(raw_ratio))",
    "factor=factor*effective_ratio",
    "ordinary_forced_nondecision_effective_ratio_exactly_one",
    "each_actor_uses_its_own_decision_valid_mask_to_update_shared_factor",
    "zero_valid_actor_skips_ratio_evaluation_and_leaves_factor_unchanged",
    "shared_factor_has_no_agent_axis;terminal_no_row_has_no_factor_or_action_row",
)
RUNTIME_KEYS = (
    "projection_version", "profile_runtime_readiness_ref",
    "unresolved_parameter_inventory_projection",
    "unresolved_parameter_resolution_status", "runtime_execution_authorized",
    "checkpoint_weight_use_authorized",
)
OWNERSHIP_KEYS = (
    "contract_version", "section_order", "record_field_order", "records",
    "unique_authority_rule",
)
OWNERSHIP_RECORD_KEYS = (
    "order", "section_name", "owner_module", "owner_contract_version",
    "descriptor_key_path", "projection_mode",
)
EXPECTED_OWNERSHIP_RECORDS = (
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
    (11, "sequential_factor_contract",
     "assignment_event_profile_schema_contract",
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
    (19, "runtime_readiness_contract",
     "assignment_event_profile_schema_contract",
     "assignment_event_profile_schema_contract_v1",
     "runtime_readiness_contract", "inline_owned_mapping"),
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_types: type[BaseException] | tuple[type[BaseException], ...],
) -> BaseException:
    try:
        function()
    except exception_types as exc:
        return exc
    except Exception as exc:
        raise AssertionError(
            f"unexpected error {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError("expected an exception")


def _install_namespace() -> None:
    packages = (
        ("isaaclab_tasks", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"),
        ("isaaclab_tasks.direct", REPO_ROOT / "source" / "isaaclab_tasks" /
         "isaaclab_tasks" / "direct"),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in packages:
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_exact(key: str, path: Path) -> ModuleType:
    existing = sys.modules.get(key)
    if existing is not None:
        _assert(Path(str(existing.__file__)).resolve() == path.resolve(), key)
        return existing
    spec = importlib.util.spec_from_file_location(key, path)
    _assert(spec is not None and spec.loader is not None, f"no spec: {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(key, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace()
MODULES = {key: _load_exact(key, path) for key, path in MODULE_PATHS.items()}
PROFILE = MODULES[f"{PACKAGE}.assignment_profile_contract"]
TRANSITION = MODULES[f"{PACKAGE}.assignment_lifecycle_transition_contract"]
EVENT = MODULES[f"{PACKAGE}.assignment_event_contract"]
MRTA = MODULES[f"{PACKAGE}.assignment_mrta_contract"]
REWARD = MODULES[f"{PACKAGE}.assignment_team_reward_contract"]
DIAGNOSTICS = MODULES[f"{PACKAGE}.assignment_event_gated_diagnostics_contract"]
SCHEMA = MODULES[SCHEMA_KEY]


def _values(mapping: Mapping[str, object]) -> tuple[object, ...]:
    return tuple(mapping[key] for key in mapping)


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_plain(item) for item in value)
    return value


def _exact_equal(actual: object, expected: object) -> bool:
    """Compare frozen primitives without Python's bool/int equality alias."""

    if isinstance(actual, Mapping) and isinstance(expected, Mapping):
        return tuple(actual) == tuple(expected) and all(
            _exact_equal(actual[key], expected[key]) for key in actual
        )
    if type(actual) is not type(expected):
        return False
    if type(actual) is tuple:
        return len(actual) == len(expected) and all(  # type: ignore[arg-type]
            _exact_equal(left, right)
            for left, right in zip(actual, expected, strict=True)  # type: ignore[arg-type]
        )
    return bool(actual == expected)


def _assert_exact(actual: object, expected: object, message: str) -> None:
    _assert(_exact_equal(actual, expected), message)


def _fixture_kwargs() -> dict[str, object]:
    return {
        "M": 3,
        "N": 50,
        "ordered_agent_names": ("robot_0", "robot_1", "robot_2"),
        "ordered_task_ids": tuple(range(50)),
        "scene_env_spacing": 12.0,
        "sim_dt_seconds": 0.01,
        "control_decimation": 4,
        "physical_control_step_seconds": 0.04,
        "episode_time_limit_seconds": 40.01,
        "episode_horizon_steps": 1001,
    }


def _descriptor(**overrides: object) -> Mapping[str, object]:
    values = _fixture_kwargs()
    values.update(overrides)
    scale = SCHEMA.build_event_gated_scale_contract(**values)
    return SCHEMA.build_assignment_event_profile_schema_descriptor(
        scale_contract=scale
    )


def test_canonical_module_identity() -> None:
    _assert(SCHEMA.__name__ == SCHEMA_KEY, "aggregate canonical module key")
    public_types = (
        SCHEMA.UnresolvedParameterOwner,
        SCHEMA.AssignmentEventProfileSchemaContractError,
    )
    for public_type in public_types:
        _assert(public_type.__module__ == SCHEMA_KEY, f"type module: {public_type}")
    _assert("assignment_event_profile_schema_contract" not in sys.modules,
            "bare module alias exists")
    source = MODULE_PATHS[SCHEMA_KEY].read_text(encoding="utf-8")
    _assert("import assignment_event_profile_schema_contract" not in source,
            "bare self import exists")
    _assert('sys.modules["assignment_event_profile_schema_contract"]' not in source and
            "sys.modules['assignment_event_profile_schema_contract']" not in source,
            "bare sys.modules alias source exists")
    registry_before = _plain(PROFILE.get_assignment_profile_registry())
    _descriptor()
    _assert(_plain(PROFILE.get_assignment_profile_registry()) == registry_before,
            "aggregate mutated profile registry")

    child = f"""
import importlib.util, json, pathlib, sys
p=pathlib.Path({str(MODULE_PATHS[SCHEMA_KEY])!r})
spec=importlib.util.spec_from_file_location('assignment_event_profile_schema_contract',p)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
sys.dont_write_bytecode=True
try:
    spec.loader.exec_module(m)
except Exception as exc:
    print(json.dumps({{'type':type(exc).__name__, 'message':str(exc), 'types':[
        name for name,value in vars(m).items() if isinstance(value,type)
    ], 'public':[name for name in vars(m) if not name.startswith('__')],
    'torch':'torch' in sys.modules,
    'dependency':any(name.startswith({PACKAGE!r}+'.assignment_') for name in sys.modules)}}))
else:
    raise SystemExit('wrong-key import unexpectedly succeeded')
"""
    result = subprocess.run(
        [sys.executable, "-c", child], capture_output=True, text=True, check=False,
    )
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(payload["types"] == [], "identity types created before key guard")
    _assert(payload["type"] in ("ImportError", "RuntimeError"),
            "wrong-key did not raise identity failure")
    _assert("canonical" in payload["message"].lower() or
            SCHEMA_KEY in payload["message"], "identity failure context missing")
    forbidden_public = {
        "UnresolvedParameterOwner", "AssignmentEventProfileSchemaContractError",
        "ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION",
    }
    _assert(not forbidden_public.intersection(payload["public"]),
            "identity surface created before key guard")
    _assert(payload["torch"] is False, "torch imported before key guard")
    _assert(payload["dependency"] is False, "dependency imported before key guard")


def test_root_scale_and_dimensions() -> None:
    descriptor = _descriptor()
    _assert(tuple(descriptor) == ROOT_KEYS, "root exact order")
    _assert(descriptor["contract_version"] ==
            "assignment_event_profile_schema_contract_v1", "root version")
    getter_result = SCHEMA.get_assignment_event_profile_schema_descriptor(
        scale_contract=descriptor["scale_contract"]
    )
    _assert_exact(_plain(getter_result), _plain(descriptor),
                  "public getter must preserve caller-provided scale identity")
    scale = descriptor["scale_contract"]
    _assert(isinstance(scale, Mapping) and tuple(scale) == SCALE_KEYS,
            "scale exact order")
    _assert_exact(_values(scale), (
        "event_gated_scale_contract_v1", 3, 50,
        ("robot_0", "robot_1", "robot_2"), tuple(range(50)), 12.0, 0.01,
        4, 0.04, 40.01, 1001,
    ), "scale exact values/derived horizon")
    for name in ("num_agents", "action_dimension", "noop_raw_id",
                 "noop_decoded_value"):
        _assert(name not in scale, f"action-owned field leaked into scale: {name}")
    for M, N in ((1, 1), (2, 7), (3, 50), (5, 4)):
        _assert(SCHEMA.actor_obs_dim(M, N) ==
                6 * M * N + 30 * M + 14 * N + 2, "actor dimension")
        _assert(SCHEMA.shared_obs_dim(M, N) ==
                6 * M * N + 31 * M + 15 * N + 8, "shared dimension")
        names = tuple(f"robot_{index}" for index in range(M))
        scale_variant = SCHEMA.build_event_gated_scale_contract(
            M=M,
            N=N,
            ordered_agent_names=names,
            ordered_task_ids=tuple(range(N)),
            scene_env_spacing=2.5,
            sim_dt_seconds=0.02,
            control_decimation=5,
            physical_control_step_seconds=0.1,
            episode_time_limit_seconds=10.01,
            episode_horizon_steps=101,
        )
        variant = SCHEMA.build_assignment_event_profile_schema_descriptor(
            scale_contract=scale_variant
        )
        _assert(variant["scale_contract"]["M"] == M and
                variant["scale_contract"]["N"] == N and
                variant["scale_contract"]["ordered_agent_names"] == names,
                f"multi-scale descriptor build: {M}/{N}")
    _assert(SCHEMA.actor_obs_dim(3, 50) == 1692, "actor ref")
    _assert(SCHEMA.shared_obs_dim(3, 50) == 1751, "shared ref")

    invalid_dimension = ((True, 2), (2, False), (0, 2), (2, 0), (-1, 2),
                         (2, -1), (1.0, 2), (2, 1.0))
    for M, N in invalid_dimension:
        _expect_error(lambda M=M, N=N: SCHEMA.actor_obs_dim(M, N),
                      (TypeError, ValueError,
                       SCHEMA.AssignmentEventProfileSchemaContractError))
        _expect_error(lambda M=M, N=N: SCHEMA.shared_obs_dim(M, N),
                      (TypeError, ValueError,
                       SCHEMA.AssignmentEventProfileSchemaContractError))

    bad_cases = (
        {"M": True}, {"N": False}, {"M": 0}, {"N": 0},
        {"M": 3.0}, {"N": 50.0},
        {"ordered_agent_names": ("robot_0", "robot_0", "robot_2")},
        {"ordered_agent_names": ("robot_0", "", "robot_2")},
        {"ordered_agent_names": ("robot_0", 1, "robot_2")},
        {"ordered_agent_names": ("robot_0", "robot_1")},
        {"ordered_agent_names": ["robot_0", "robot_1", "robot_2"]},
        {"ordered_task_ids": tuple(range(49))},
        {"ordered_task_ids": tuple(range(1, 51))},
        {"ordered_task_ids": list(range(50))},
        {"scene_env_spacing": 0.0}, {"scene_env_spacing": float("inf")},
        {"scene_env_spacing": float("nan")}, {"scene_env_spacing": True},
        {"scene_env_spacing": 12},
        {"sim_dt_seconds": 0.0}, {"sim_dt_seconds": float("nan")},
        {"sim_dt_seconds": float("inf")}, {"sim_dt_seconds": True},
        {"sim_dt_seconds": 1},
        {"control_decimation": True}, {"control_decimation": 0},
        {"control_decimation": 1.0},
        {"physical_control_step_seconds": 0.0},
        {"physical_control_step_seconds": float("inf")},
        {"physical_control_step_seconds": float("nan")},
        {"physical_control_step_seconds": True},
        {"physical_control_step_seconds": 4},
        {"physical_control_step_seconds": 0.041},
        {"episode_time_limit_seconds": 0.0},
        {"episode_time_limit_seconds": float("inf")},
        {"episode_time_limit_seconds": float("nan")},
        {"episode_time_limit_seconds": True},
        {"episode_time_limit_seconds": 40},
        {"episode_horizon_steps": True}, {"episode_horizon_steps": 0},
        {"episode_horizon_steps": 1001.0}, {"episode_horizon_steps": 1000},
    )
    for overrides in bad_cases:
        _expect_error(lambda overrides=overrides: _descriptor(**overrides),
                      (TypeError, ValueError,
                       SCHEMA.AssignmentEventProfileSchemaContractError))
    valid_scale = descriptor["scale_contract"]
    missing_scale = dict(valid_scale)
    missing_scale.pop("M")
    unknown_scale = dict(valid_scale)
    unknown_scale["metadata"] = "forbidden"
    reordered_scale = dict(reversed(tuple(valid_scale.items())))
    for bad_scale in (missing_scale, unknown_scale, reordered_scale):
        _expect_error(
            lambda bad_scale=bad_scale:
                SCHEMA.build_assignment_event_profile_schema_descriptor(
                    scale_contract=bad_scale
                ),
            (TypeError, ValueError,
             SCHEMA.AssignmentEventProfileSchemaContractError),
        )


def test_actor_inventory() -> None:
    actor = _descriptor()["actor_schema"]
    _assert(isinstance(actor, Mapping) and tuple(actor) == ACTOR_KEYS,
            "actor exact key order")
    _assert(actor["schema_version"] == "event_gated_global_actor_observation_v1",
            "actor version")
    _assert(actor["scope"] == "global_fixed_width_per_actor_complete_team_state_v1",
            "actor scope")
    _assert(actor["robot_reference_frame"] ==
            "scenario_environment_local_cartesian_v1", "actor frame")
    _assert(actor["global_robot_order_source"] ==
            "scale_contract.ordered_agent_names", "robot order source")
    _assert(actor["global_task_order_source"] == "scale_contract.ordered_task_ids",
            "task order source")
    _assert(actor["output_dtype"] == "torch.float32", "actor dtype")
    _assert(actor["flatten_order"] ==
            "block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner",
            "actor flatten")
    _assert(actor["block_record_field_order"] == ACTOR_BLOCK_KEYS,
            "actor record keys")
    _assert(actor["block_count"] == 15 and len(actor["blocks"]) == 15,
            "actor block count")
    for record, expected in zip(actor["blocks"], EXPECTED_ACTOR_BLOCKS, strict=True):
        _assert(tuple(record) == ACTOR_BLOCK_KEYS, "actor record field order")
        _assert_exact(_values(record), expected,
                      f"actor block mismatch: {expected[1]}")
    _assert(actor["dimension_formula"] == "6*M*N + 30*M + 14*N + 2",
            "actor dimension formula")
    _assert(tuple(actor["reference_dimension"]) == ("M", "N", "dimension"),
            "actor reference keys")
    _assert_exact(_values(actor["reference_dimension"]), (3, 50, 1692),
                  "actor reference dimension")
    normalization = actor["normalization_contract"]
    _assert(tuple(normalization) == NORMALIZATION_KEYS,
            "actor normalization keys")
    _assert_exact(_values(normalization), EXPECTED_NORMALIZATION_VALUES,
                  "actor normalization contract")
    generation = actor["generation_binding"]
    _assert(tuple(generation) == GENERATION_KEYS, "actor generation keys")
    _assert_exact(_values(generation), EXPECTED_GENERATION_VALUES,
                  "actor generation contract")
    _assert(actor["temporal_boundary"] ==
            "fact_updated_a0_pre_policy_no_same_tick_resolver_outcome_v1",
            "actor temporal boundary")
    ordinary = actor["ordinary_no_tick_contract"]
    terminal = actor["terminal_row_contract"]
    _assert(tuple(ordinary) == ORDINARY_KEYS, "ordinary row keys")
    _assert_exact(_values(ordinary), EXPECTED_ORDINARY_VALUES, "ordinary row")
    _assert(tuple(terminal) == TERMINAL_KEYS, "terminal row keys")
    _assert_exact(_values(terminal), EXPECTED_TERMINAL_VALUES, "terminal row")
    _assert(actor["excluded_fields"] == ACTOR_EXCLUSIONS, "actor exclusions")
    serialized = json.dumps(_plain(actor), sort_keys=True)
    for forbidden in ("assignment_observation_contract_c_v1",
                      "contract_c_actor_observation", "nearest_task_slots"):
        _assert(forbidden not in serialized, f"Contract-C leak: {forbidden}")


def test_shared_inventory() -> None:
    descriptor = _descriptor()
    actor = descriptor["actor_schema"]
    shared = descriptor["shared_schema"]
    _assert(isinstance(shared, Mapping) and tuple(shared) == SHARED_KEYS,
            "shared exact key order")
    expected_scalars = {
        "schema_version": "event_gated_global_centralized_observation_v1",
        "construction_mode": "global_fixed_width_centralized_v1",
        "semantic_state_shape": ("E", "S"),
        "runner_transport_shape": ("E", "M", "S"),
        "critic_input_shape": ("B", "S"),
        "runner_transport_mode":
            "repeat_identical_semantic_shared_state_across_agent_axis_v1",
        "output_dtype": "torch.float32",
        "flatten_order":
            "block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner",
        "dimension_formula": "6*M*N + 31*M + 15*N + 8",
        "normalization_contract_reference": "actor_schema.normalization_contract",
        "temporal_boundary":
            "fact_updated_pre_policy_or_terminal_pre_reset_no_same_tick_resolver_outcome_v1",
        "ordinary_no_tick_contract_reference":
            "actor_schema.ordinary_no_tick_contract",
    }
    for key, expected in expected_scalars.items():
        _assert(shared[key] == expected, f"shared field: {key}")
    for shape_key in ("semantic_state_shape", "runner_transport_shape",
                      "critic_input_shape"):
        _assert(type(shared[shape_key]) is tuple, f"shape not tuple: {shape_key}")
    _assert(shared["block_record_field_order"] == SHARED_BLOCK_KEYS,
            "shared record keys")
    _assert(shared["block_count"] == 19 and len(shared["blocks"]) == 19,
            "shared block count")
    for record, expected in zip(shared["blocks"], EXPECTED_SHARED_BLOCKS, strict=True):
        _assert(tuple(record) == SHARED_BLOCK_KEYS, "shared record field order")
        _assert_exact(_values(record), expected,
                      f"shared block mismatch: {expected[1]}")
        _assert(type(record["shape"]) is tuple, f"shape primitive: {expected[1]}")
    _assert(tuple(shared["reference_dimension"]) ==
            ("M", "N", "semantic_dimension", "runner_agent_count"),
            "shared reference keys")
    _assert_exact(_values(shared["reference_dimension"]), (3, 50, 1751, 3),
                  "shared reference dimension")
    _assert_exact(_plain(shared["generation_binding"]),
                  _plain(actor["generation_binding"]), "generation mismatch")
    terminal_shared = shared["terminal_shared_state_contract"]
    _assert(tuple(terminal_shared) == TERMINAL_SHARED_KEYS,
            "terminal shared keys")
    _assert_exact(_values(terminal_shared), EXPECTED_TERMINAL_SHARED_VALUES,
                  "terminal shared contract")
    _assert(shared["excluded_fields"] == SHARED_EXCLUSIONS, "shared exclusions")
    serialized = json.dumps(_plain(shared), sort_keys=True)
    _assert("concat_all_actor_observations" not in serialized,
            "actor-concat semantics leaked")


def test_terminal_semantics() -> None:
    descriptor = _descriptor()
    ordinary = descriptor["actor_schema"]["ordinary_no_tick_contract"]
    terminal = descriptor["actor_schema"]["terminal_row_contract"]
    terminal_shared = descriptor["shared_schema"]["terminal_shared_state_contract"]
    _assert(ordinary["terminal"] is False and
            ordinary["semantic_action_count"] == 1, "ordinary row identity")
    _assert(ordinary["storage_row_present"] is True and
            ordinary["forced_nondecision_present"] is True and
            ordinary["policy_proposal_present"] is False and
            ordinary["decision_valid"] is False, "ordinary forced storage")
    _assert(terminal["terminal"] is True and terminal["semantic_action_count"] == 0,
            "terminal row identity")
    _assert(terminal["target_actions"] == "all_false" and
            terminal["noop_action"] == "all_false" and
            terminal["forced_policy_action_id"] == -1, "terminal mask/id")
    for key in ("storage_row_present", "policy_proposal_present",
                "forced_nondecision_present", "resolver_consumption"):
        _assert(terminal[key] is False, f"terminal must not expose {key}")
    _assert(terminal["actor_sampling"] == "not_called", "terminal actor call")
    _assert(terminal_shared["pre_reset_sidecar_required"] is True and
            terminal_shared["reset_state_alias_forbidden"] is True,
            "terminal pre-reset boundary")
    serialized = json.dumps(_plain(terminal_shared), sort_keys=True).lower()
    for forbidden in ("extra_physical_transition", "independent_critic_loss_sample",
                      "extra_actor_sample"):
        _assert(forbidden not in serialized, f"terminal extra-sample claim: {forbidden}")


def _resolve_reference(reference: Mapping[str, object]) -> Mapping[str, object]:
    module = MODULES[str(reference["triple_owner_module"])]
    getter_names = {
        MRTA_MODULE: "get_assignment_mrta_contract_descriptor",
        EVENT_MODULE: "get_assignment_event_contract_descriptor",
        REWARD_MODULE: "get_assignment_team_reward_contract_descriptor",
    }
    current: object = getattr(module, getter_names[module.__name__])()
    path = str(reference["triple_descriptor_key_path"])
    for segment in path.split("."):
        if "[" in segment:
            name, index_text = segment[:-1].split("[", 1)
            current = current[name][int(index_text)]  # type: ignore[index]
        else:
            current = current[segment]  # type: ignore[index]
    _assert(isinstance(current, Mapping), f"reference not mapping: {path}")
    return current


def test_parameter_inventory() -> None:
    descriptor = _descriptor()
    SCHEMA.validate_event_profile_domain_references()
    enum_values = tuple(member.value for member in SCHEMA.UnresolvedParameterOwner)
    expected_member_names = (
        "PHASE_B_RUNTIME", "PHASE_D_REWARD", "PHASE_E_EVALUATION",
        "PHASE_B_RUNTIME_AND_PHASE_E_EVALUATION",
        "PHASE_D_REWARD_AND_PHASE_E_EVALUATION",
    )
    _assert(tuple(SCHEMA.UnresolvedParameterOwner.__members__) ==
            expected_member_names and
            tuple(member.name for member in SCHEMA.UnresolvedParameterOwner) ==
            expected_member_names,
            "owner enum names/aliases")
    _assert(enum_values == ("phase_b", "phase_d", "phase_e", "phase_b_e",
                            "phase_d_e"), "owner enum values")
    inventory = descriptor["unresolved_parameter_inventory"]
    _assert(tuple(inventory) == UNRESOLVED_KEYS, "inventory key order")
    _assert(inventory["contract_version"] ==
            "event_gated_unresolved_parameter_inventory_v1", "inventory version")
    _assert(inventory["owner_enum_order"] == enum_values, "inventory enum order")
    _assert(inventory["triple_field_order"] ==
            ("name", "owner_phase", "semantic_purpose"), "triple field order")
    _assert(inventory["reference_record_field_order"] == REFERENCE_KEYS,
            "reference field order")
    _assert(inventory["unresolved_parameter_order"] == UNRESOLVED_NAMES,
            "unresolved order")
    references = inventory["unresolved_parameter_references"]
    _assert(len(references) == 11, "no twelfth parameter")
    for reference, expected, expected_triple in zip(
        references, EXPECTED_REFERENCES, EXPECTED_DOMAIN_TRIPLES, strict=True
    ):
        _assert(tuple(reference) == REFERENCE_KEYS, "reference key order")
        _assert_exact(_values(reference), expected,
                      f"reference mismatch: {expected[0]}")
        triple = _resolve_reference(reference)
        extracted = tuple(triple[key] for key in inventory["triple_field_order"])
        _assert(extracted == expected_triple,
                f"domain triple drift: {reference['name']}")
        SCHEMA.UnresolvedParameterOwner(extracted[1])
        if reference["triple_owner_module"] == REWARD_MODULE:
            _assert(tuple(triple) == (
                "name", "owner_phase", "semantic_purpose", "required_type",
                "numeric_value_selected"), "reward v1 shape changed")
        _assert(len(extracted) == 3, "aggregate must extract only triple")
    readiness = descriptor["runtime_readiness_contract"]
    _assert(tuple(readiness) == RUNTIME_KEYS, "runtime key order")
    _assert(readiness["projection_version"] ==
            "event_gated_runtime_readiness_projection_v1", "runtime version")
    _assert_exact(_plain(readiness["unresolved_parameter_inventory_projection"]),
                  _plain(inventory),
                  "runtime inventory is not exact inline mapping")
    _assert(readiness["unresolved_parameter_resolution_status"] ==
            "all_11_unresolved", "unresolved status")
    _assert(readiness["runtime_execution_authorized"] is False and
            readiness["checkpoint_weight_use_authorized"] is False,
            "runtime/weight authorization")
    readiness_ref = readiness["profile_runtime_readiness_ref"]
    _assert(tuple(readiness_ref) ==
            ("canonical_module", "descriptor_key_path", "expected_value"),
            "profile readiness reference keys")
    _assert_exact(_values(readiness_ref), (
        f"{PACKAGE}.assignment_profile_contract",
        "resolved_event_profile_mapping.runtime_readiness", "interface_only",
    ), "profile readiness reference")

    # Public revalidation deliberately consumes the canonical lower-level
    # getter bound by the aggregate module.  Replacing that dependency with a
    # drifted public descriptor is the narrow pure test seam for fail-closed
    # domain reference validation; it is restored before this test returns.
    original = SCHEMA.get_assignment_mrta_contract_descriptor
    original_descriptor = original()
    altered = dict(original_descriptor)
    local = dict(altered["local_candidate_semantics"])
    triples = list(local["unresolved_parameters"])
    first = dict(triples[0])
    first["owner_phase"] = "phase_b"
    triples[0] = MappingProxyType(first)
    local["unresolved_parameters"] = tuple(triples)
    altered["local_candidate_semantics"] = MappingProxyType(local)
    SCHEMA.get_assignment_mrta_contract_descriptor = lambda: MappingProxyType(altered)
    try:
        _expect_error(
            SCHEMA.validate_event_profile_domain_references,
            SCHEMA.AssignmentEventProfileSchemaContractError,
        )
    finally:
        SCHEMA.get_assignment_mrta_contract_descriptor = original


def _walk_bindings(value: object, path: str = "") -> list[tuple[str, Mapping[str, object]]]:
    results: list[tuple[str, Mapping[str, object]]] = []
    if isinstance(value, Mapping):
        if path.endswith("_binding"):
            results.append((path, value))
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            results.extend(_walk_bindings(item, child))
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            results.extend(_walk_bindings(item, f"{path}[{index}]"))
    return results


def test_model_and_training() -> None:
    descriptor = _descriptor()
    model = descriptor["model_structure"]
    _assert(tuple(model) == MODEL_KEYS, "model exact order")
    _assert_exact(_values(model), EXPECTED_MODEL_VALUES,
                  "model exact projection")
    _assert(model["actor_hidden_sizes"] == (256, 256) and
            model["critic_hidden_sizes"] == (256, 256), "actual runner sizes")
    _assert("hidden_sizes_critic" not in json.dumps(_plain(model), sort_keys=True),
            "unused hidden_sizes_critic leaked")
    _assert(model["actor_input_schema_version"] ==
            descriptor["actor_schema"]["schema_version"] and
            model["actor_input_dimension_source"] == "actor_schema.dimension_formula",
            "actor model reference")
    _assert(model["critic_input_schema_version"] ==
            descriptor["shared_schema"]["schema_version"] and
            model["critic_input_dimension_source"] == "shared_schema.dimension_formula",
            "critic model reference")
    action_contract = MRTA.get_assignment_mrta_contract_descriptor()["action_contract"]
    _assert(model["action_dimension_formula"] ==
            "action_contract.action_dimension" and
            action_contract["action_dimension"] == "scale_contract.N + 1",
            "action model reference")
    _assert(model["ordered_actor_network_names_source"] ==
            "scale_contract.ordered_agent_names", "actor-name model reference")
    resolved = PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    profile_mapping = PROFILE.resolved_assignment_profile_to_mapping(resolved)
    training_semantics = profile_mapping["event_gated_target_semantics"][
        "training_semantic_contract"
    ]
    for model_key, profile_key in (
        ("harl_state_type", "state_type"),
        ("share_param", "share_param"),
        ("use_recurrent_policy", "use_recurrent_policy"),
        ("use_naive_recurrent_policy", "use_naive_recurrent_policy"),
        ("serialization_mode", "serialization_mode"),
        ("save_entire_model", "save_entire_model"),
    ):
        _assert(model[model_key] == training_semantics[profile_key],
                f"model/profile drift: {model_key}")
    training = descriptor["training_contract"]
    _assert(tuple(training) == TRAINING_KEYS, "training exact order")
    _assert(training["projection_version"] ==
            "event_gated_training_contract_projection_v1", "training version")
    _assert(training["decision_valid_training_contract_ref"] ==
            "event_gated_decision_valid_actor_training_v1", "DVM ref")
    _assert(training["sequential_factor_contract_ref"] ==
            "event_gated_happo_sequential_factor_v1", "factor ref")
    _assert(training["runtime_evidence_status"] == "DEFERRED_RUNTIME_EVIDENCE",
            "training runtime evidence")
    algorithm = training["algorithm_identity"]
    _assert(tuple(algorithm) == ALGORITHM_KEYS, "algorithm identity order")
    _assert_exact(_values(algorithm), (
        "HAPPO", "happo", "EP", False,
        "event_gated_decision_valid_feed_forward_v1", False, False,
        "feed_forward_generator_actor", False,
    ), "algorithm identity")
    rollout = training["rollout_return_semantics"]
    _assert(tuple(rollout) == ROLLOUT_KEYS, "rollout exact order")
    for key, expected in {
        "time_axis": "fixed_physical_transitions",
        "episode_length_semantics": "transitions_per_rollout",
        "standard_gae": True,
        "critic_reward_source": "broadcast_team_reward",
        "critic_return_sample_set": "all_valid_physical_steps",
        "decision_valid_excluded_from_gae_returns_critic": True,
        "valuenorm_source": "all_valid_physical_step_returns",
        "valuenorm_epsilon": 0.00001,
    }.items():
        _assert_exact(rollout[key], expected, f"rollout literal: {key}")
    optimizer = training["optimizer_config_identity"]
    ppo = training["ppo_config_identity"]
    _assert(tuple(optimizer) == OPTIMIZER_KEYS and
            optimizer["optimizer_family"] == "Adam", "optimizer exact order")
    _assert(tuple(ppo) == PPO_KEYS, "PPO exact order")
    serialization = training["serialization_contract"]
    _assert(tuple(serialization) == SERIALIZATION_KEYS, "serialization exact order")
    bindings = _walk_bindings(training)
    _assert(tuple(path for path, _ in bindings) == tuple(EXPECTED_BINDINGS),
            "config binding order/inventory")
    for path, binding in bindings:
        _assert(tuple(binding) == BINDING_KEYS, f"binding order: {path}")
        _assert_exact(_values(binding)[:4], EXPECTED_BINDINGS[path],
                      f"binding identity: {path}")
        _assert(binding["semantic_status"] == "CONFIG_BOUND_CURRENT_IDENTITY",
                f"binding semantic status: {path}")
        _assert(binding["runtime_evidence_status"] == "DEFERRED_RUNTIME_EVIDENCE",
                f"binding evidence status: {path}")

    dvm = descriptor["decision_valid_training_contract"]
    factor = descriptor["sequential_factor_contract"]
    _assert(tuple(dvm) == DVM_KEYS, "DVM exact order")
    _assert_exact(_values(dvm), EXPECTED_DVM_VALUES,
                  "DVM exact immutable projection")
    _assert(tuple(factor) == FACTOR_KEYS, "factor exact order")
    _assert_exact(_values(factor), EXPECTED_FACTOR_VALUES,
                  "factor exact immutable projection")
    _assert_exact(_values(serialization), (
        "state_dict", False, "event_gated_state_dict_inventory_contract_v1",
        True, False,
    ), "interface-only serialization")


def _owner_descriptor(record: Mapping[str, object], aggregate: Mapping[str, object]) -> object:
    basename = str(record["owner_module"])
    _assert(basename in MODULE_BASENAMES, f"unknown owner basename: {basename}")
    if basename == "assignment_event_profile_schema_contract":
        current: object = aggregate
    elif basename == "assignment_profile_contract":
        resolved = PROFILE.resolve_assignment_profile(
            PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
        )
        current = {
            "resolved_event_profile_mapping":
                PROFILE.resolved_assignment_profile_to_mapping(resolved)
        }
    else:
        module = MODULES[f"{PACKAGE}.{basename}"]
        getters = {
            "assignment_lifecycle_transition_contract":
                "get_assignment_lifecycle_transition_schema_descriptor",
            "assignment_event_contract": "get_assignment_event_contract_descriptor",
            "assignment_mrta_contract": "get_assignment_mrta_contract_descriptor",
            "assignment_team_reward_contract":
                "get_assignment_team_reward_contract_descriptor",
            "assignment_event_gated_diagnostics_contract":
                "get_assignment_event_gated_diagnostics_descriptor",
        }
        current = getattr(module, getters[basename])()
    path = str(record["descriptor_key_path"])
    if path == "$":
        return current
    for segment in path.split("."):
        current = current[segment]  # type: ignore[index]
    return current


def test_v3_section_ownership() -> None:
    descriptor = _descriptor()
    ownership = descriptor["v3_section_ownership"]
    _assert(tuple(ownership) == OWNERSHIP_KEYS, "ownership exact order")
    _assert(ownership["contract_version"] ==
            "event_gated_v3_section_ownership_v1", "ownership version")
    _assert(ownership["record_field_order"] == OWNERSHIP_RECORD_KEYS,
            "ownership record fields")
    records = ownership["records"]
    _assert(len(records) == 19, "ownership record count")
    _assert(ownership["section_order"] == tuple(row[1] for row in
                                                EXPECTED_OWNERSHIP_RECORDS),
            "section order")
    seen_sections: set[str] = set()
    resolved = PROFILE.resolve_assignment_profile(
        PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    resolved_mapping = PROFILE.resolved_assignment_profile_to_mapping(resolved)
    for record, expected in zip(records, EXPECTED_OWNERSHIP_RECORDS, strict=True):
        _assert(tuple(record) == OWNERSHIP_RECORD_KEYS, "ownership record order")
        _assert_exact(_values(record), expected,
                      f"ownership record: {expected[1]}")
        _assert(record["projection_mode"] in
                ("inline_owned_mapping", "canonical_reference"),
                "unknown projection mode")
        canonical = f"{PACKAGE}.{record['owner_module']}"
        _assert(canonical in MODULES, f"owner does not resolve canonically: {canonical}")
        _owner_descriptor(record, descriptor)
        SCHEMA.validate_event_profile_v3_section_ownership_record(
            record,
            aggregate_descriptor=descriptor,
            resolved_event_profile_mapping=resolved_mapping,
        )
        section = str(record["section_name"])
        _assert(section not in seen_sections, f"duplicate owner: {section}")
        seen_sections.add(section)
    _assert(ownership["unique_authority_rule"] ==
            "exactly_one_owner_per_semantic_field_no_documentary_fallback",
            "unique authority rule")

    first = records[0]
    for field, invalid in (
        ("owner_module", "unknown_owner"),
        ("descriptor_key_path", "unknown.path"),
        ("projection_mode", "unknown_mode"),
    ):
        altered = dict(first)
        altered[field] = invalid
        _expect_error(
            lambda altered=altered:
                SCHEMA.validate_event_profile_v3_section_ownership_record(
                    altered,
                    aggregate_descriptor=descriptor,
                    resolved_event_profile_mapping=resolved_mapping,
                ),
            SCHEMA.AssignmentEventProfileSchemaContractError,
        )


def test_immutability_and_side_effects() -> None:
    descriptor_a = _descriptor()
    descriptor_b = _descriptor()
    _assert(isinstance(descriptor_a, Mapping), "root must be a read-only mapping")
    _assert_exact(_plain(descriptor_a), _plain(descriptor_b),
                  "nondeterministic descriptor")
    mutable_scale_source = dict(descriptor_a["scale_contract"])
    detached = SCHEMA.build_assignment_event_profile_schema_descriptor(
        scale_contract=mutable_scale_source
    )
    mutable_scale_source["M"] = 999
    mutable_scale_source["ordered_agent_names"] = ("mutated",)
    _assert(detached["scale_contract"]["M"] == 3 and
            detached["scale_contract"]["ordered_agent_names"] ==
            ("robot_0", "robot_1", "robot_2"),
            "source mutation changed built descriptor")
    mappings: list[Mapping[str, object]] = []

    def collect(value: object) -> None:
        if isinstance(value, Mapping):
            mappings.append(value)
            for nested in value.values():
                collect(nested)
        elif isinstance(value, tuple):
            for nested in value:
                collect(nested)

    collect(descriptor_a)
    _assert(mappings and all(isinstance(item, Mapping) for item in mappings),
            "nested value is not a mapping")

    def assert_primitives(value: object) -> None:
        if isinstance(value, Mapping):
            _assert(all(type(key) is str for key in value), "non-string descriptor key")
            for nested in value.values():
                assert_primitives(nested)
            return
        if type(value) is tuple:
            for nested in value:
                assert_primitives(nested)
            return
        _assert(type(value) in (str, int, float, bool),
                f"non-primitive descriptor value: {type(value).__name__}")

    assert_primitives(descriptor_a)
    for mapping in mappings:
        _expect_error(lambda mapping=mapping: mapping.__setitem__("x", 1),
                      (AttributeError, TypeError))
    text = json.dumps(_plain(descriptor_a), sort_keys=True)
    forbidden_exact = (
        "tensor._version", "storage_ptr", "data_ptr", "private_digest",
        "factory_seal", "ledger_layout", "sys.modules alias", "hostname",
        "username", "checkpoint fingerprint", "checkpoint_fingerprint",
        "timestamp",
    )
    for forbidden in forbidden_exact:
        _assert(forbidden not in text.lower(), f"private term: {forbidden}")
    _assert("C:\\\\" not in text and "E:\\\\" not in text,
            "absolute drive path leaked")

    strings: list[tuple[str, str]] = []

    def collect_strings(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                strings.append((f"{path}.<key>", str(key)))
                collect_strings(nested, f"{path}.{key}")
        elif type(value) is tuple:
            for index, nested in enumerate(value):
                collect_strings(nested, f"{path}[{index}]")
        elif type(value) is str:
            strings.append((path, value))

    collect_strings(descriptor_a, "$root")
    for path, value in strings:
        lower = value.lower()
        _assert(lower != "pid" and "timestamp" not in lower,
                f"process/time identity leak at {path}")
        _assert(not re.match(r"^[a-zA-Z]:[\\/]", value),
                f"drive path leak at {path}")
        _assert(not value.startswith(("\\\\", "/")),
                f"UNC/POSIX absolute path leak at {path}")
        if "mutation_detector" in lower or "capability" in lower:
            _assert(value == "private_mutation_detector_or_capability" and
                    ".excluded_fields[" in path,
                    f"private detector/capability leak at {path}")
        if lower == "storage":
            raise AssertionError(f"raw storage object identity leaked at {path}")

    child = f"""
import contextlib, importlib.util, io, json, logging, os, pathlib, random, sys
from types import ModuleType
root=pathlib.Path({str(REPO_ROOT)!r})
scan=pathlib.Path({str(SCAN_SOURCE)!r})
package={PACKAGE!r}
for name,path in (("isaaclab_tasks",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'),
                  ("isaaclab_tasks.direct",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'/'direct'),
                  (package,scan)):
    m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
def load(key,path):
    spec=importlib.util.spec_from_file_location(key,path); m=importlib.util.module_from_spec(spec)
    sys.modules[key]=m; previous=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True; spec.loader.exec_module(m)
    finally:
        sys.dont_write_bytecode=previous
    return m
names={MODULE_BASENAMES[:-1]!r}
loaded={{}}
for basename in names:
    loaded[basename]=load(package+'.'+basename,scan/(basename+'.py'))
registry_before=repr(loaded['assignment_profile_contract'].get_assignment_profile_registry())
aggregate_absent_before=(package+'.assignment_event_profile_schema_contract' not in sys.modules)
import torch
cwd=os.getcwd(); env=dict(os.environ); syspath=tuple(sys.path)
handlers=tuple(logging.getLogger().handlers); level=logging.getLogger().level
py=random.getstate(); trng=torch.random.get_rng_state().clone()
numpy_before='numpy' in sys.modules
modules_before=set(sys.modules)
files=tuple(sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob('*')))
out=io.StringIO(); err=io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    module=load(package+'.assignment_event_profile_schema_contract',
                scan/'assignment_event_profile_schema_contract.py')
    scale=module.build_event_gated_scale_contract(
        M=3,N=50,ordered_agent_names=('robot_0','robot_1','robot_2'),
        ordered_task_ids=tuple(range(50)),scene_env_spacing=12.0,
        sim_dt_seconds=0.01,control_decimation=4,
        physical_control_step_seconds=0.04,
        episode_time_limit_seconds=40.01,episode_horizon_steps=1001)
    module.build_assignment_event_profile_schema_descriptor(scale_contract=scale)
result={{'stdout':out.getvalue(),'stderr':err.getvalue(),'cwd':os.getcwd()==cwd,
 'env':dict(os.environ)==env,'path':tuple(sys.path)==syspath,
 'handlers':tuple(logging.getLogger().handlers)==handlers,
 'level':logging.getLogger().level==level,'py':random.getstate()==py,
 'torch':torch.equal(torch.random.get_rng_state(),trng),
 'numpy':('numpy' in sys.modules)==numpy_before,
 'dag':aggregate_absent_before,
 'registry':repr(loaded['assignment_profile_contract'].get_assignment_profile_registry())==registry_before,
 'files':tuple(sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob('*')))==files,
 'bare':'assignment_event_profile_schema_contract' not in sys.modules,
 'source_keys':[name for name,value in sys.modules.items()
    if getattr(value,'__file__',None) and
       pathlib.Path(value.__file__).resolve()==(scan/'assignment_event_profile_schema_contract.py').resolve()],
 'forbidden':not any(name.startswith(('omni','isaaclab.app','harl')) or 'checkpoint' in name
    for name in set(sys.modules)-modules_before)}}
result['source_keys']=(result['source_keys']==[package+'.assignment_event_profile_schema_contract'])
print(json.dumps(result,sort_keys=True))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [sys.executable, "-c", child], cwd=temp_dir,
            capture_output=True, text=True, check=False,
        )
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(payload["stdout"] == "" and payload["stderr"] == "", "import output")
    for key, value in payload.items():
        if key not in ("stdout", "stderr"):
            _assert(value is True, f"clean child side effect: {key}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("canonical_module_identity", test_canonical_module_identity),
    ("root_scale_and_dimensions", test_root_scale_and_dimensions),
    ("actor_inventory", test_actor_inventory),
    ("shared_inventory", test_shared_inventory),
    ("terminal_semantics", test_terminal_semantics),
    ("parameter_inventory", test_parameter_inventory),
    ("model_and_training", test_model_and_training),
    ("v3_section_ownership", test_v3_section_ownership),
    ("immutability_and_side_effects", test_immutability_and_side_effects),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append({
                "name": name,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_event_profile_schema_contract",
        "passed": passed,
        "total": len(results),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for item in results:
            suffix = "" if item["status"] == "passed" else f": {item['error']}"
            print(f"{item['status'].upper():6} {item['name']}{suffix}")
        print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
