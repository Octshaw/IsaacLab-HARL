"""Pure Phase-A V3 assignment checkpoint interface descriptor contract.

The contract in this module fingerprints public interface semantics only.  It
does not inspect, save, or load checkpoint weights; construct a model; import
HARL; or authorize runtime execution.  All semantic section content is
projected from the frozen public A1--A3x descriptors.
"""

from __future__ import annotations


if __name__ != (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_contract_v3"
):
    raise ImportError(
        "CanonicalModuleIdentityError: assignment checkpoint contract V3 "
        "must be imported by its canonical package key before declaring "
        "identity-bearing types or importing dependencies; expected="
        "'isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_checkpoint_contract_v3'; actual="
        f"{__name__!r}"
    )


from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from enum import Enum
import hashlib
import json
import math
import re

from .assignment_event_contract import (
    ASSIGNMENT_EVENT_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE,
    get_assignment_event_contract_descriptor,
)
from .assignment_event_gated_diagnostics_contract import (
    ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE,
    get_assignment_event_gated_diagnostics_descriptor,
)
from .assignment_event_profile_schema_contract import (
    ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_MODULE,
    AssignmentEventProfileSchemaContractError,
    actor_obs_dim,
    build_assignment_event_profile_schema_descriptor,
    get_assignment_event_profile_schema_descriptor,
    shared_obs_dim,
    validate_event_profile_v3_section_ownership_record,
)
from .assignment_lifecycle_transition_contract import (
    ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE,
    get_assignment_lifecycle_transition_schema_descriptor,
)
from .assignment_mrta_contract import (
    ASSIGNMENT_MRTA_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_MRTA_MODULE,
    get_assignment_mrta_contract_descriptor,
)
from .assignment_profile_contract import (
    ASSIGNMENT_PROFILE_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_PROFILE_MODULE,
    AssignmentProfileName,
    AssignmentProfileResolutionOrigin,
    resolve_assignment_profile,
    resolved_assignment_profile_to_mapping,
)
from .assignment_team_reward_contract import (
    ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION,
    CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE,
    get_assignment_team_reward_contract_descriptor,
)


CANONICAL_ASSIGNMENT_CHECKPOINT_CONTRACT_V3_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_contract_v3"
)
MANIFEST_FORMAT_VERSION = "assignment_checkpoint_contract_v3"
ASSIGNMENT_CHECKPOINT_MANIFEST_FORMAT_VERSION_V3 = MANIFEST_FORMAT_VERSION

SEMANTIC_SECTION_NAMES = (
    "identity",
    "scale",
    "actor_schema",
    "shared_schema",
    "action_contract",
    "transition_contract",
    "event_tick_contract",
    "local_candidate_contract",
    "cost_path_contract",
    "decision_valid_training_contract",
    "sequential_factor_contract",
    "component_contract",
    "reward_contract",
    "failure_termination_contract",
    "diagnostics_contract",
    "policy_sequence_contract",
    "model_structure",
    "training_contract",
    "runtime_readiness_contract",
)
TOP_LEVEL_KEY_ORDER = (
    "manifest_format_version",
    "manifest_kind",
    *SEMANTIC_SECTION_NAMES,
)

_OWNERSHIP_RECORD_KEYS = (
    "order",
    "section_name",
    "owner_module",
    "owner_contract_version",
    "descriptor_key_path",
    "projection_mode",
)
_ALLOWED_PROJECTION_MODES = (
    "inline_owned_mapping",
    "canonical_reference",
)
_INDEXED_PATH_SEGMENT = re.compile(r"^([a-z][a-z0-9_]*)\[([0-9]+)\]$")


class AssignmentCheckpointV3ContractError(ValueError):
    """Base error for the pure V3 interface contract."""


class UnsupportedCheckpointManifestVersionError(AssignmentCheckpointV3ContractError):
    """Raised when a present manifest does not declare the exact V3 version."""


class UnsupportedCheckpointManifestKindError(AssignmentCheckpointV3ContractError):
    """Raised for an unknown V3 artifact kind."""


class CheckpointManifestSchemaError(AssignmentCheckpointV3ContractError):
    """Raised when a V3 mapping differs from its frozen public schema."""


class CheckpointManifestPurposeError(AssignmentCheckpointV3ContractError):
    """Raised when Phase A is asked to perform a non-audit operation."""


class CheckpointReadyManifestNotAuthorizedError(AssignmentCheckpointV3ContractError):
    """Raised because Phase A cannot construct or parse checkpoint-ready V3."""

    def __init__(
        self,
        *,
        parameter_status: str,
        missing_runtime_evidence_categories: tuple[str, ...],
        state_dict_inventory_status: str,
    ) -> None:
        self.requested_kind = (
            AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST
        )
        self.runtime_readiness = "interface_only"
        self.parameter_status = parameter_status
        self.missing_runtime_evidence_categories = (
            missing_runtime_evidence_categories
        )
        self.state_dict_inventory_status = state_dict_inventory_status
        super().__init__(
            "checkpoint-ready V3 construction/parsing is not authorized in "
            "Phase A; requested_kind=checkpoint_ready_manifest; "
            "runtime_readiness=interface_only; "
            f"parameter_status={parameter_status}; "
            "missing runtime evidence categories="
            f"{missing_runtime_evidence_categories!r}; "
            f"state-dict inventory status={state_dict_inventory_status}; "
            "checkpoint_weight_use_authorized=false"
        )


class UnresolvedCheckpointParameterError(AssignmentCheckpointV3ContractError):
    """Reserved typed boundary for later checkpoint-ready parameter resolution."""


class CheckpointRuntimeReadinessError(AssignmentCheckpointV3ContractError):
    """Reserved typed boundary for later verified runtime evidence."""


class CheckpointManifestFamilyMismatchError(AssignmentCheckpointV3ContractError):
    """Raised when V2 and V3 semantic families are compared as compatible."""


class CheckpointManifestInputError(AssignmentCheckpointV3ContractError):
    """Raised when a manifest facade input is not a present mapping."""


class AssignmentCheckpointManifestKind(str, Enum):
    INTERFACE_SEMANTIC_DESCRIPTOR = "interface_semantic_descriptor"
    CHECKPOINT_READY_MANIFEST = "checkpoint_ready_manifest"


class AssignmentCheckpointV3Purpose(str, Enum):
    INTERFACE_AUDIT = "interface_audit"


class _FrozenSemanticMapping(Mapping[str, object]):
    """Insertion-order-preserving immutable mapping for validated semantics."""

    __slots__ = ("_items",)

    def __init__(self, value: Mapping[str, object]) -> None:
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise CheckpointManifestSchemaError(
                    "semantic descriptor mapping keys must be exact strings"
                )
            items.append((key, _deep_freeze(item)))
        object.__setattr__(self, "_items", tuple(items))

    def __getitem__(self, key: str) -> object:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")


def _deep_freeze(value: object) -> object:
    if isinstance(value, _FrozenSemanticMapping):
        return value
    if isinstance(value, Mapping):
        return _FrozenSemanticMapping(value)
    if type(value) in (tuple, list):
        return tuple(_deep_freeze(item) for item in value)  # type: ignore[arg-type]
    if type(value) is float:
        if not math.isfinite(value):
            raise CheckpointManifestSchemaError(
                "V3 semantic descriptor floats must be finite"
            )
        return value
    if type(value) in (str, int, bool):
        return value
    raise CheckpointManifestSchemaError(
        "V3 semantic descriptors accept only mappings, ordered sequences, "
        "and exact JSON primitive values; actual="
        f"{type(value).__name__}"
    )


def _to_plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_to_plain(item) for item in value]
    return value


def _to_authority_plain(value: object) -> object:
    """Return public-descriptor container form (tuples remain semantic tuples)."""

    if isinstance(value, Mapping):
        return {
            key: _to_authority_plain(item) for key, item in value.items()
        }
    if type(value) is tuple:
        return tuple(_to_authority_plain(item) for item in value)
    return value


def _exact_semantic_equal(left: object, right: object) -> bool:
    """Type-aware equality with JSON list/semantic tuple normalization only."""

    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return False
        return all(_exact_semantic_equal(left[key], right[key]) for key in left)
    if type(left) in (tuple, list) and type(right) in (tuple, list):
        if len(left) != len(right):  # type: ignore[arg-type]
            return False
        return all(
            _exact_semantic_equal(a, b)
            for a, b in zip(left, right, strict=True)  # type: ignore[arg-type]
        )
    if type(left) is not type(right):
        return False
    return bool(left == right)


def _require_mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CheckpointManifestSchemaError(f"{field} must be a mapping")
    if any(type(key) is not str for key in value):
        raise CheckpointManifestSchemaError(
            f"{field} mapping keys must be exact strings"
        )
    return value  # type: ignore[return-value]


def _require_exact_key_set(
    value: Mapping[str, object], *, expected: tuple[str, ...], field: str
) -> None:
    actual = set(value)
    required = set(expected)
    if actual != required:
        missing = tuple(key for key in expected if key not in actual)
        unexpected = tuple(repr(key) for key in value if key not in required)
        raise CheckpointManifestSchemaError(
            f"{field} keys mismatch; missing={missing!r}; "
            f"unexpected={unexpected!r}"
        )


class _CheckpointV3Section:
    """Shared mechanics; every semantic authority remains a named dataclass field."""

    __slots__ = ()

    def __post_init__(self) -> None:
        for field in fields(self):
            object.__setattr__(self, field.name, _deep_freeze(getattr(self, field.name)))

    @classmethod
    def _from_mapping(cls, value: Mapping[str, object]) -> _CheckpointV3Section:
        mapping = _require_mapping(value, field=cls.__name__)
        names = tuple(field.name for field in fields(cls))
        _require_exact_key_set(mapping, expected=names, field=cls.__name__)
        return cls(**{name: mapping[name] for name in names})  # type: ignore[call-arg]

    def to_mapping(self) -> dict[str, object]:
        return {
            field.name: _to_plain(getattr(self, field.name)) for field in fields(self)
        }

    def _to_authority_mapping(self) -> dict[str, object]:
        return {
            field.name: _to_authority_plain(getattr(self, field.name))
            for field in fields(self)
        }


@dataclass(frozen=True, slots=True)
class CheckpointV3IdentitySection(_CheckpointV3Section):
    profile: str
    profile_contract_version: str
    checkpoint_family: str
    runtime_route: str
    runtime_readiness: str
    event_target_semantics_contract: str
    training_semantics: str


@dataclass(frozen=True, slots=True)
class CheckpointV3ScaleSection(_CheckpointV3Section):
    contract_version: str
    M: int
    N: int
    ordered_agent_names: tuple[str, ...]
    ordered_task_ids: tuple[int, ...]
    scene_env_spacing: float
    sim_dt_seconds: float
    control_decimation: int
    physical_control_step_seconds: float
    episode_time_limit_seconds: float
    episode_horizon_steps: int


@dataclass(frozen=True, slots=True)
class CheckpointV3ActorSchemaSection(_CheckpointV3Section):
    schema_version: str
    scope: str
    robot_reference_frame: str
    global_robot_order_source: str
    global_task_order_source: str
    output_dtype: str
    flatten_order: str
    block_record_field_order: tuple[str, ...]
    block_count: int
    blocks: tuple[Mapping[str, object], ...]
    dimension_formula: str
    reference_dimension: Mapping[str, object]
    normalization_contract: Mapping[str, object]
    generation_binding: Mapping[str, object]
    temporal_boundary: str
    ordinary_no_tick_contract: Mapping[str, object]
    terminal_row_contract: Mapping[str, object]
    excluded_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointV3SharedSchemaSection(_CheckpointV3Section):
    schema_version: str
    construction_mode: str
    semantic_state_shape: tuple[object, ...]
    runner_transport_shape: tuple[object, ...]
    critic_input_shape: tuple[object, ...]
    runner_transport_mode: str
    output_dtype: str
    flatten_order: str
    block_record_field_order: tuple[str, ...]
    block_count: int
    blocks: tuple[Mapping[str, object], ...]
    dimension_formula: str
    reference_dimension: Mapping[str, object]
    normalization_contract_reference: str
    generation_binding: Mapping[str, object]
    temporal_boundary: str
    ordinary_no_tick_contract_reference: str
    terminal_shared_state_contract: Mapping[str, object]
    excluded_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointV3ActionContractSection(_CheckpointV3Section):
    contract_version: str
    num_agents: str
    action_dimension: str
    target_action_id_domain: str
    noop_raw_id: str
    noop_decoded_value: int
    available_action_order: str
    decision_valid_mask_contract_version: str
    proposal_mask_contract_version: str
    cross_section_invariants: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckpointV3TransitionContractSection(_CheckpointV3Section):
    contract_version: str
    facts: Mapping[str, object]
    result: Mapping[str, object]
    pair_attribution_contract_version: str
    observable_immutability_contract_version: str
    observable_immutability_guarantees: tuple[str, ...]
    failure_termination_semantics: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CheckpointV3EventTickContractSection(_CheckpointV3Section):
    contract_version: str
    record_systems: tuple[Mapping[str, object], ...]
    payload_field_order: Mapping[str, object]
    placement_rules: Mapping[str, object]
    record_system_separation: tuple[str, ...]
    scheduled_assignment_opportunity_semantics: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CheckpointV3LocalCandidateContractSection(_CheckpointV3Section):
    projection_version: str
    seed_sources: tuple[str, ...]
    seed_robot_mask_equation: str
    trigger_record_robot_rule: str
    forbidden_trigger_records: tuple[str, ...]
    candidate_prefilter_order: tuple[str, ...]
    candidate_eligibility_equation: str
    top_k_sort_order: tuple[str, ...]
    occupied_task_candidate_rule: str
    current_task_retention_rule: str
    owner_expansion_rounds: int
    owner_expansion_equation: str
    second_layer_owner_recursion: bool
    outside_set_owner_preemption_rule: str
    overlap_identity: str
    overlap_merge_rule: str
    post_merge_recomputation_order: tuple[str, ...]
    post_merge_owner_expansion: str
    global_robot_identity: str
    global_task_identity: str
    local_observation_repacking: bool
    overflow_behavior: str
    request_result_association_key: tuple[str, ...]
    unresolved_parameters: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class CheckpointV3CostPathContractSection(_CheckpointV3Section):
    projection_version: str
    cost_unit: str
    tensor_shapes: Mapping[str, object]
    tensor_dtypes: Mapping[str, object]
    cost_generation_key: tuple[str, ...]
    refresh_rule: str
    snapshot_consistency_rule: str
    navigation_cost_semantics: str
    alignment_cost_semantics: str
    nominal_cost_equation: str
    current_owner_navigation_rule: str
    current_owner_alignment_rule: str
    nonowner_cost_rule: str
    alignment_fallback_rule: str
    unresolved_parameters: tuple[Mapping[str, object], ...]
    path_valid_authority: str
    valid_pair_rule: str
    invalid_path_encoding: str
    finite_invalid_sentinel_allowed: bool
    top_k_penalty_rule: str
    pair_gate_cost_source: str
    component_penalty_scope: str


@dataclass(frozen=True, slots=True)
class CheckpointV3DecisionValidTrainingContractSection(_CheckpointV3Section):
    contract_version: str
    buffer_mask_shape: tuple[object, ...]
    training_slice: str
    actor_valid_equation: str
    policy_loss_reduction: str
    entropy_reduction: str
    advantage_population: str
    zero_valid_actor_rule: str
    singleton_advantage_rule: str
    multi_sample_advantage_rule: str
    advantage_std_epsilon: float
    empty_minibatch_rule: str
    rejected_proposal_included: bool
    critic_dvm_usage: str


@dataclass(frozen=True, slots=True)
class CheckpointV3SequentialFactorContractSection(_CheckpointV3Section):
    contract_version: str
    factor_shape: tuple[object, ...]
    initial_value: float
    agent_update_order_source: str
    raw_ratio_equation: str
    effective_ratio_equation: str
    factor_update_equation: str
    nondecision_identity: str
    per_agent_dvm_rule: str
    zero_valid_actor_rule: str
    agent_axis_rule: str


@dataclass(frozen=True, slots=True)
class CheckpointV3ComponentContractSection(_CheckpointV3Section):
    projection_version: str
    baseline_a0_identity: Mapping[str, object]
    component_scope: str
    proposal_source: str
    contention_order: tuple[str, ...]
    contention_loser_rule: str
    component_closure_rule: str
    whole_component_outcome: str
    partial_policy_acceptance_rule: str
    covered_continue_override_rule: str
    assigned_unfinished_count_equation: str
    assigned_count_gate: str
    active_preemption_definition: str
    pair_improvement_equations: Mapping[str, object]
    pair_gate_conjunction: str
    baseline_cost_equation: str
    staged_cost_equation: str
    owner_change_count_equation: str
    count_increase_rule: str
    count_equal_improvement_equations: Mapping[str, object]
    count_decrease_rule: str
    canonical_rejection_order: tuple[str, ...]
    nonpolicy_rejection_reasons: tuple[str, ...]
    policy_penalty_attribution_rule: str
    penalty_unit_equation: str
    invariant_failure_rule: str
    forbidden_resolver_behaviors: tuple[str, ...]
    unresolved_parameters: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class CheckpointV3RewardContractSection(_CheckpointV3Section):
    contract_version: str
    schema_version: str
    spec_field_order: tuple[str, ...]
    semantic_values: Mapping[str, object]
    base_env_reward_contract: Mapping[str, object]
    wrapper_shaping_contract: Mapping[str, object]
    unresolved_parameter: Mapping[str, object]
    operation_order: tuple[str, ...]
    formula: str
    oracle_inputs: Mapping[str, object]
    oracle_outputs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CheckpointV3FailureTerminationContractSection(_CheckpointV3Section):
    projection_version: str
    task_state_enum_order: tuple[str, ...]
    robot_state_enum_order: tuple[str, ...]
    transient_event_exclusion: tuple[str, ...]
    termination_reason_order: tuple[str, ...]
    failed_pair_source: str
    new_failed_pairs_equation: str
    updated_failed_pairs_equation: str
    failed_pair_episode_reset_rule: str
    team_infeasible_equation: str
    new_team_infeasible_equation: str
    path_invalid_non_equivalence: str
    terminal_task_ownership_release_rule: str
    event_updated_baseline_order: tuple[str, ...]
    termination_priority: tuple[str, ...]
    physical_terminal_mapping_boundary: str
    bad_transition_boundary: str
    unmappable_physical_terminal_rule: str
    terminal_assignment_rule: str
    episode_generation_rule: str
    transition_generation_rule: str
    assignment_tick_generation_rule: str


@dataclass(frozen=True, slots=True)
class CheckpointV3DiagnosticsContractSection(_CheckpointV3Section):
    contract_version: str
    schema_version: str
    diagnostic_availability_order: tuple[str, ...]
    diagnostic_kind_order: tuple[str, ...]
    transition_consume_status_order: tuple[str, ...]
    default_off_cohort_order: tuple[str, ...]
    envelope_field_order: tuple[str, ...]
    payload_type_by_kind: Mapping[str, object]
    availability_rules: Mapping[str, object]
    serialization: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CheckpointV3PolicySequenceContractSection(_CheckpointV3Section):
    contract_version: str
    actor_schema_version: str
    shared_schema_version: str
    shared_construction_mode: str
    mask_contract_version: str
    budget_release_contract: str
    policy_sequence_route: str
    training_semantic_contract: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CheckpointV3ModelStructureSection(_CheckpointV3Section):
    projection_version: str
    projection_status: str
    actor_class: str
    critic_class: str
    action_distribution_class: str
    actor_input_schema_version: str
    actor_input_dimension_source: str
    critic_input_schema_version: str
    critic_input_dimension_source: str
    action_dimension_formula: str
    actor_hidden_sizes: tuple[int, ...]
    critic_hidden_sizes: tuple[int, ...]
    activation: str
    feature_normalization: bool
    share_param: bool
    number_of_actor_networks_formula: str
    ordered_actor_network_names_source: str
    critic_architecture: str
    harl_state_type: str
    use_recurrent_policy: bool
    use_naive_recurrent_policy: bool
    recurrent_n: int
    initialization_method: str
    action_gain: float
    serialization_mode: str
    save_entire_model: bool
    state_dict_key_contract_version: str
    state_dict_inventory_binding: str


@dataclass(frozen=True, slots=True)
class CheckpointV3TrainingContractSection(_CheckpointV3Section):
    projection_version: str
    algorithm_identity: Mapping[str, object]
    rollout_return_semantics: Mapping[str, object]
    optimizer_config_identity: Mapping[str, object]
    ppo_config_identity: Mapping[str, object]
    decision_valid_training_contract_ref: str
    sequential_factor_contract_ref: str
    serialization_contract: Mapping[str, object]
    runtime_evidence_status: str


@dataclass(frozen=True, slots=True)
class CheckpointV3RuntimeReadinessSection(_CheckpointV3Section):
    projection_version: str
    profile_runtime_readiness_ref: Mapping[str, object]
    unresolved_parameter_inventory_projection: Mapping[str, object]
    unresolved_parameter_resolution_status: str
    runtime_execution_authorized: bool
    checkpoint_weight_use_authorized: bool


_SECTION_CLASS_BY_NAME = {
    "identity": CheckpointV3IdentitySection,
    "scale": CheckpointV3ScaleSection,
    "actor_schema": CheckpointV3ActorSchemaSection,
    "shared_schema": CheckpointV3SharedSchemaSection,
    "action_contract": CheckpointV3ActionContractSection,
    "transition_contract": CheckpointV3TransitionContractSection,
    "event_tick_contract": CheckpointV3EventTickContractSection,
    "local_candidate_contract": CheckpointV3LocalCandidateContractSection,
    "cost_path_contract": CheckpointV3CostPathContractSection,
    "decision_valid_training_contract": (
        CheckpointV3DecisionValidTrainingContractSection
    ),
    "sequential_factor_contract": CheckpointV3SequentialFactorContractSection,
    "component_contract": CheckpointV3ComponentContractSection,
    "reward_contract": CheckpointV3RewardContractSection,
    "failure_termination_contract": CheckpointV3FailureTerminationContractSection,
    "diagnostics_contract": CheckpointV3DiagnosticsContractSection,
    "policy_sequence_contract": CheckpointV3PolicySequenceContractSection,
    "model_structure": CheckpointV3ModelStructureSection,
    "training_contract": CheckpointV3TrainingContractSection,
    "runtime_readiness_contract": CheckpointV3RuntimeReadinessSection,
}


def _resolved_event_profile_mapping() -> Mapping[str, object]:
    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    mapping = resolved_assignment_profile_to_mapping(profile)
    return _require_mapping(mapping, field="resolved_event_profile_mapping")


def _project_identity_section(
    resolved_profile: Mapping[str, object],
) -> Mapping[str, object]:
    """Project the exact seven A4a identity discriminants from A1 authority."""

    target = _require_mapping(
        resolved_profile.get("event_gated_target_semantics"),
        field="resolved_event_profile_mapping.event_gated_target_semantics",
    )
    training = _require_mapping(
        target.get("training_semantic_contract"),
        field=(
            "resolved_event_profile_mapping.event_gated_target_semantics."
            "training_semantic_contract"
        ),
    )
    return _FrozenSemanticMapping(
        {
            "profile": resolved_profile.get("profile_name"),
            "profile_contract_version": resolved_profile.get(
                "profile_contract_version"
            ),
            "checkpoint_family": resolved_profile.get("checkpoint_family"),
            "runtime_route": resolved_profile.get("runtime_route"),
            "runtime_readiness": resolved_profile.get("runtime_readiness"),
            "event_target_semantics_contract": target.get("contract_version"),
            "training_semantics": training.get("contract_version"),
        }
    )


def _resolve_descriptor_path(root: object, path: str) -> object:
    if path == "$":
        return root
    current = root
    for segment in path.split("."):
        indexed = _INDEXED_PATH_SEGMENT.fullmatch(segment)
        if indexed is not None:
            mapping = _require_mapping(current, field=f"path before {segment!r}")
            name, raw_index = indexed.groups()
            if name not in mapping:
                raise CheckpointManifestSchemaError(
                    f"ownership path missing key {name!r}: {path!r}"
                )
            sequence = mapping[name]
            if type(sequence) not in (tuple, list):
                raise CheckpointManifestSchemaError(
                    f"ownership indexed path is not an ordered sequence: {path!r}"
                )
            index = int(raw_index)
            if index >= len(sequence):
                raise CheckpointManifestSchemaError(
                    f"ownership path index out of range: {path!r}"
                )
            current = sequence[index]
        else:
            mapping = _require_mapping(current, field=f"path before {segment!r}")
            if segment not in mapping:
                raise CheckpointManifestSchemaError(
                    f"ownership path missing segment {segment!r}: {path!r}"
                )
            current = mapping[segment]
    return current


def _authority_section_mappings(
    scale_contract: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    """Resolve all 19 mappings through the frozen ownership inventory."""

    try:
        aggregate = get_assignment_event_profile_schema_descriptor(
            scale_contract=scale_contract
        )
        canonical_aggregate = build_assignment_event_profile_schema_descriptor(
            scale_contract=scale_contract
        )
        if not _exact_semantic_equal(aggregate, canonical_aggregate):
            raise CheckpointManifestSchemaError(
                "event-profile getter content differs from its canonical public builder"
            )
        aggregate = _require_mapping(
            aggregate, field="assignment event-profile descriptor"
        )
        if aggregate.get("contract_version") != (
            ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION
        ):
            raise CheckpointManifestSchemaError(
                "event-profile aggregate contract version drift"
            )

        resolved_profile = _resolved_event_profile_mapping()
        transition = get_assignment_lifecycle_transition_schema_descriptor()
        event = get_assignment_event_contract_descriptor()
        mrta = get_assignment_mrta_contract_descriptor()
        reward = get_assignment_team_reward_contract_descriptor()
        diagnostics = get_assignment_event_gated_diagnostics_descriptor()

        roots: dict[str, Mapping[str, object]] = {
            "assignment_profile_contract": _FrozenSemanticMapping(
                {"resolved_event_profile_mapping": resolved_profile}
            ),
            "assignment_event_profile_schema_contract": aggregate,
            "assignment_lifecycle_transition_contract": transition,
            "assignment_event_contract": event,
            "assignment_mrta_contract": mrta,
            "assignment_team_reward_contract": reward,
            "assignment_event_gated_diagnostics_contract": diagnostics,
        }
        module_keys = {
            "assignment_profile_contract": CANONICAL_ASSIGNMENT_PROFILE_MODULE,
            "assignment_event_profile_schema_contract": (
                CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_MODULE
            ),
            "assignment_lifecycle_transition_contract": (
                CANONICAL_ASSIGNMENT_LIFECYCLE_TRANSITION_MODULE
            ),
            "assignment_event_contract": CANONICAL_ASSIGNMENT_EVENT_CONTRACT_MODULE,
            "assignment_mrta_contract": CANONICAL_ASSIGNMENT_MRTA_MODULE,
            "assignment_team_reward_contract": (
                CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE
            ),
            "assignment_event_gated_diagnostics_contract": (
                CANONICAL_ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_MODULE
            ),
        }
        versions = {
            "assignment_profile_contract": ASSIGNMENT_PROFILE_CONTRACT_VERSION,
            "assignment_event_profile_schema_contract": (
                ASSIGNMENT_EVENT_PROFILE_SCHEMA_CONTRACT_VERSION
            ),
            "assignment_lifecycle_transition_contract": (
                ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION
            ),
            "assignment_event_contract": ASSIGNMENT_EVENT_CONTRACT_VERSION,
            "assignment_mrta_contract": ASSIGNMENT_MRTA_CONTRACT_VERSION,
            "assignment_team_reward_contract": (
                ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION
            ),
            "assignment_event_gated_diagnostics_contract": (
                ASSIGNMENT_EVENT_GATED_DIAGNOSTICS_CONTRACT_VERSION
            ),
        }
        getter_modules = {
            "assignment_profile_contract": (
                resolved_assignment_profile_to_mapping.__module__
            ),
            "assignment_event_profile_schema_contract": (
                get_assignment_event_profile_schema_descriptor.__module__
            ),
            "assignment_lifecycle_transition_contract": (
                get_assignment_lifecycle_transition_schema_descriptor.__module__
            ),
            "assignment_event_contract": (
                get_assignment_event_contract_descriptor.__module__
            ),
            "assignment_mrta_contract": (
                get_assignment_mrta_contract_descriptor.__module__
            ),
            "assignment_team_reward_contract": (
                get_assignment_team_reward_contract_descriptor.__module__
            ),
            "assignment_event_gated_diagnostics_contract": (
                get_assignment_event_gated_diagnostics_descriptor.__module__
            ),
        }
        for basename, module_key in module_keys.items():
            expected_key = (
                "isaaclab_tasks.direct.scan_mobile_manipulator." + basename
            )
            if module_key != expected_key or getter_modules[basename] != expected_key:
                raise CheckpointManifestSchemaError(
                    f"noncanonical owner module identity for {basename!r}"
                )

        ownership = _require_mapping(
            aggregate.get("v3_section_ownership"),
            field="v3_section_ownership",
        )
        records = ownership.get("records")
        if type(records) is not tuple or len(records) != 19:
            raise CheckpointManifestSchemaError(
                "V3 ownership must contain exactly 19 ordered records"
            )
        if tuple(ownership.get("section_order", ())) != SEMANTIC_SECTION_NAMES:
            raise CheckpointManifestSchemaError("V3 ownership section order drift")

        sections: dict[str, Mapping[str, object]] = {}
        for order, raw_record in enumerate(records, 1):
            record = _require_mapping(
                raw_record, field=f"v3_section_ownership.records[{order - 1}]"
            )
            _require_exact_key_set(
                record,
                expected=_OWNERSHIP_RECORD_KEYS,
                field=f"v3_section_ownership.records[{order - 1}]",
            )
            if record["order"] != order:
                raise CheckpointManifestSchemaError(
                    "V3 ownership record order must be exact 1..19"
                )
            section_name = record["section_name"]
            if section_name != SEMANTIC_SECTION_NAMES[order - 1]:
                raise CheckpointManifestSchemaError(
                    "V3 ownership record section order/name drift"
                )
            owner = record["owner_module"]
            if type(owner) is not str or owner not in roots:
                raise CheckpointManifestSchemaError(
                    f"V3 ownership uses an unknown canonical owner {owner!r}"
                )
            if record["owner_contract_version"] != versions[owner]:
                raise CheckpointManifestSchemaError(
                    f"V3 ownership version drift for section {section_name!r}"
                )
            if record["projection_mode"] not in _ALLOWED_PROJECTION_MODES:
                raise CheckpointManifestSchemaError(
                    f"V3 ownership projection mode drift for {section_name!r}"
                )
            path = record["descriptor_key_path"]
            if type(path) is not str:
                raise CheckpointManifestSchemaError(
                    "V3 ownership descriptor key path must be an exact string"
                )
            validate_event_profile_v3_section_ownership_record(
                record,
                aggregate_descriptor=aggregate,
                resolved_event_profile_mapping=resolved_profile,
            )
            resolved = _resolve_descriptor_path(roots[owner], path)
            resolved_mapping = _require_mapping(
                resolved, field=f"resolved V3 section {section_name}"
            )
            sections[section_name] = (
                _project_identity_section(resolved_mapping)
                if section_name == "identity"
                else resolved_mapping
            )

        if tuple(sections) != SEMANTIC_SECTION_NAMES:
            raise CheckpointManifestSchemaError(
                "V3 ownership did not resolve the exact 19 section inventory"
            )
        return sections
    except AssignmentCheckpointV3ContractError:
        raise
    except AssignmentEventProfileSchemaContractError as exc:
        raise CheckpointManifestSchemaError(
            f"event-profile schema authority rejected V3 assembly: {exc}"
        ) from exc
    except Exception as exc:
        raise CheckpointManifestSchemaError(
            f"public descriptor authority rejected V3 assembly: {exc}"
        ) from exc


def _typed_sections_from_authority(
    scale_contract: Mapping[str, object],
) -> dict[str, _CheckpointV3Section]:
    mappings = _authority_section_mappings(scale_contract)
    return {
        name: _SECTION_CLASS_BY_NAME[name]._from_mapping(mappings[name])
        for name in SEMANTIC_SECTION_NAMES
    }


@dataclass(frozen=True, slots=True)
class AssignmentCheckpointContractManifestV3:
    manifest_format_version: str
    manifest_kind: AssignmentCheckpointManifestKind
    identity: CheckpointV3IdentitySection
    scale: CheckpointV3ScaleSection
    actor_schema: CheckpointV3ActorSchemaSection
    shared_schema: CheckpointV3SharedSchemaSection
    action_contract: CheckpointV3ActionContractSection
    transition_contract: CheckpointV3TransitionContractSection
    event_tick_contract: CheckpointV3EventTickContractSection
    local_candidate_contract: CheckpointV3LocalCandidateContractSection
    cost_path_contract: CheckpointV3CostPathContractSection
    decision_valid_training_contract: CheckpointV3DecisionValidTrainingContractSection
    sequential_factor_contract: CheckpointV3SequentialFactorContractSection
    component_contract: CheckpointV3ComponentContractSection
    reward_contract: CheckpointV3RewardContractSection
    failure_termination_contract: CheckpointV3FailureTerminationContractSection
    diagnostics_contract: CheckpointV3DiagnosticsContractSection
    policy_sequence_contract: CheckpointV3PolicySequenceContractSection
    model_structure: CheckpointV3ModelStructureSection
    training_contract: CheckpointV3TrainingContractSection
    runtime_readiness_contract: CheckpointV3RuntimeReadinessSection

    def __post_init__(self) -> None:
        if type(self.manifest_format_version) is not str or (
            self.manifest_format_version != MANIFEST_FORMAT_VERSION
        ):
            raise UnsupportedCheckpointManifestVersionError(
                "unsupported V3 manifest_format_version: "
                f"{self.manifest_format_version!r}"
            )
        if type(self.manifest_kind) is not AssignmentCheckpointManifestKind:
            raise UnsupportedCheckpointManifestKindError(
                "manifest_kind must be AssignmentCheckpointManifestKind"
            )
        if self.manifest_kind is (
            AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST
        ):
            _raise_ready_not_authorized(
                parameter_status="not_inspected_declared_ready_manifest",
                missing_runtime_evidence_categories=(
                    "runtime_evidence_not_inspected_phase_a_kind_rejection",
                ),
                state_dict_inventory_status="deferred",
            )
        for name in SEMANTIC_SECTION_NAMES:
            expected_class = _SECTION_CLASS_BY_NAME[name]
            if type(getattr(self, name)) is not expected_class:
                raise CheckpointManifestSchemaError(
                    f"{name} must be {expected_class.__name__}"
                )

        canonical_sections = _typed_sections_from_authority(
            self.scale._to_authority_mapping()
        )
        for name in SEMANTIC_SECTION_NAMES:
            actual = getattr(self, name).to_mapping()
            expected = canonical_sections[name].to_mapping()
            if not _exact_semantic_equal(actual, expected):
                raise CheckpointManifestSchemaError(
                    f"{name} differs from its frozen public descriptor projection"
                )
            object.__setattr__(self, name, canonical_sections[name])
        self._validate_cross_section_invariants()

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> AssignmentCheckpointContractManifestV3:
        if not isinstance(mapping, Mapping):
            raise CheckpointManifestInputError(
                "V3 manifest input must be an already available mapping"
            )
        if "manifest_format_version" not in mapping:
            raise UnsupportedCheckpointManifestVersionError(
                "present manifest mapping is missing manifest_format_version"
            )
        raw_version = mapping["manifest_format_version"]
        if type(raw_version) is not str or raw_version != MANIFEST_FORMAT_VERSION:
            raise UnsupportedCheckpointManifestVersionError(
                "unsupported manifest_format_version: "
                f"{raw_version!r}"
            )
        if "manifest_kind" not in mapping:
            raise CheckpointManifestSchemaError("V3 manifest is missing manifest_kind")
        raw_kind = mapping["manifest_kind"]
        if type(raw_kind) is not str:
            raise UnsupportedCheckpointManifestKindError(
                "V3 manifest_kind must be an exact string; actual_type="
                f"{type(raw_kind).__name__}"
            )
        try:
            kind = AssignmentCheckpointManifestKind(raw_kind)
        except (TypeError, ValueError) as exc:
            raise UnsupportedCheckpointManifestKindError(
                f"unsupported V3 manifest_kind: {raw_kind!r}"
            ) from exc
        if kind is AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST:
            _raise_ready_not_authorized(
                parameter_status="not_inspected_declared_ready_manifest",
                missing_runtime_evidence_categories=(
                    "runtime_evidence_not_inspected_phase_a_kind_rejection",
                ),
                state_dict_inventory_status="deferred",
            )

        typed_mapping = _require_mapping(mapping, field="V3 manifest")
        _require_exact_key_set(
            typed_mapping, expected=TOP_LEVEL_KEY_ORDER, field="V3 manifest"
        )
        scale_input = _require_mapping(
            typed_mapping["scale"], field="V3 manifest.scale"
        )
        scale_candidate = CheckpointV3ScaleSection._from_mapping(scale_input)
        canonical_sections = _typed_sections_from_authority(
            scale_candidate._to_authority_mapping()
        )
        for name in SEMANTIC_SECTION_NAMES:
            incoming = _require_mapping(
                typed_mapping[name], field=f"V3 manifest.{name}"
            )
            canonical = canonical_sections[name].to_mapping()
            if not _exact_semantic_equal(incoming, canonical):
                raise CheckpointManifestSchemaError(
                    f"V3 manifest.{name} differs from its frozen public "
                    "descriptor projection"
                )
        return cls(
            manifest_format_version=MANIFEST_FORMAT_VERSION,
            manifest_kind=kind,
            **canonical_sections,
        )  # type: ignore[arg-type]

    def to_mapping(self) -> dict[str, object]:
        return {
            "manifest_format_version": self.manifest_format_version,
            "manifest_kind": self.manifest_kind.value,
            **{
                name: getattr(self, name).to_mapping()
                for name in SEMANTIC_SECTION_NAMES
            },
        }

    def _validate_cross_section_invariants(self) -> None:
        identity = self.identity
        scale = self.scale
        actor = self.actor_schema
        shared = self.shared_schema
        action = self.action_contract
        readiness = self.runtime_readiness_contract

        exact_identity = {
            "profile": "event_gated_local_mrta",
            "profile_contract_version": "assignment_resolved_profile_v1",
            "checkpoint_family": MANIFEST_FORMAT_VERSION,
            "runtime_route": "event_gated_phase_a_interface_only_v1",
            "runtime_readiness": "interface_only",
            "event_target_semantics_contract": (
                "event_gated_target_semantics_v1"
            ),
            "training_semantics": "event_gated_happo_ep_feed_forward_v1",
        }
        for key, expected in exact_identity.items():
            if getattr(identity, key) != expected:
                raise CheckpointManifestSchemaError(
                    f"identity.{key} must equal {expected!r}"
                )
        forbidden_identity = {
            "event_gate_enabled",
            "resolver_enabled",
            "lifecycle_observation_enabled",
            "lifecycle_mask_enabled",
        }
        if forbidden_identity.intersection(self.identity.to_mapping()):
            raise CheckpointManifestSchemaError(
                "legacy runtime booleans are forbidden from V3 identity"
            )

        if scale.ordered_task_ids != tuple(range(scale.N)):
            raise CheckpointManifestSchemaError(
                "scale ordered_task_ids must be exact global IDs 0..N-1"
            )
        if len(scale.ordered_agent_names) != scale.M:
            raise CheckpointManifestSchemaError(
                "scale ordered_agent_names length must equal M"
            )
        if (
            action.num_agents != "scale_contract.M"
            or action.action_dimension != "scale_contract.N + 1"
        ):
            raise CheckpointManifestSchemaError(
                "action num_agents/action_dimension formula bindings must "
                "reference scale M/N+1"
            )
        if (
            action.noop_raw_id != "scale_contract.N"
            or action.noop_decoded_value != -1
        ):
            raise CheckpointManifestSchemaError("global noop encoding drift")

        actor_reference = actor.reference_dimension
        shared_reference = shared.reference_dimension
        if (
            actor_reference["M"] != scale.M
            or actor_reference["N"] != scale.N
            or actor_reference["dimension"] != actor_obs_dim(scale.M, scale.N)
        ):
            raise CheckpointManifestSchemaError(
                "actor reference dimension must match scale M/N and formula"
            )
        if (
            shared_reference["M"] != scale.M
            or shared_reference["N"] != scale.N
            or shared_reference["semantic_dimension"]
            != shared_obs_dim(scale.M, scale.N)
            or shared_reference["runner_agent_count"] != scale.M
        ):
            raise CheckpointManifestSchemaError(
                "shared reference dimension must match scale M/N and formula"
            )
        if (
            shared.semantic_state_shape != ("E", "S")
            or shared.runner_transport_shape != ("E", "M", "S")
            or shared.critic_input_shape != ("B", "S")
        ):
            raise CheckpointManifestSchemaError("shared transport semantics drift")

        inventory = _require_mapping(
            readiness.unresolved_parameter_inventory_projection,
            field="runtime_readiness_contract.unresolved_parameter_inventory_projection",
        )
        unresolved_order = inventory["unresolved_parameter_order"]
        references = inventory["unresolved_parameter_references"]
        if (
            type(unresolved_order) is not tuple
            or len(unresolved_order) != 11
            or len(set(unresolved_order)) != 11
            or type(references) is not tuple
            or len(references) != 11
        ):
            raise CheckpointManifestSchemaError(
                "runtime readiness must carry exactly 11 ordered unresolved parameters"
            )
        if (
            readiness.unresolved_parameter_resolution_status != "all_11_unresolved"
            or readiness.runtime_execution_authorized is not False
            or readiness.checkpoint_weight_use_authorized is not False
        ):
            raise CheckpointManifestSchemaError(
                "Phase-A V3 runtime readiness must remain interface-only and "
                "weight-use unauthorized"
            )


def build_interface_semantic_descriptor_v3(
    *, scale_contract: Mapping[str, object]
) -> AssignmentCheckpointContractManifestV3:
    """Build the exact interface-only V3 manifest from caller-resolved scale."""

    sections = _typed_sections_from_authority(scale_contract)
    return AssignmentCheckpointContractManifestV3(
        manifest_format_version=MANIFEST_FORMAT_VERSION,
        manifest_kind=(
            AssignmentCheckpointManifestKind.INTERFACE_SEMANTIC_DESCRIPTOR
        ),
        **sections,
    )  # type: ignore[arg-type]


def parse_assignment_checkpoint_manifest_v3(
    mapping: Mapping[str, object],
) -> AssignmentCheckpointContractManifestV3:
    """Strictly parse one present interface-descriptor V3 mapping."""

    return AssignmentCheckpointContractManifestV3.from_mapping(mapping)


def _raise_ready_not_authorized(
    *,
    parameter_status: str,
    missing_runtime_evidence_categories: tuple[str, ...],
    state_dict_inventory_status: str,
) -> None:
    raise CheckpointReadyManifestNotAuthorizedError(
        parameter_status=parameter_status,
        missing_runtime_evidence_categories=missing_runtime_evidence_categories,
        state_dict_inventory_status=state_dict_inventory_status,
    )


def build_checkpoint_ready_v3(
    *,
    scale_contract: Mapping[str, object],
    resolved_parameters: Mapping[str, object] | None = None,
    runtime_evidence: Mapping[str, object] | None = None,
    state_dict_inventory: object | None = None,
) -> AssignmentCheckpointContractManifestV3:
    """Always fail closed: checkpoint-ready construction is not Phase-A work."""

    sections = _typed_sections_from_authority(scale_contract)
    readiness = sections["runtime_readiness_contract"]
    if not isinstance(readiness, CheckpointV3RuntimeReadinessSection):
        raise CheckpointManifestSchemaError("runtime readiness section type drift")
    inventory = _require_mapping(
        readiness.unresolved_parameter_inventory_projection,
        field="unresolved parameter inventory",
    )
    names = tuple(inventory["unresolved_parameter_order"])  # type: ignore[arg-type]
    if resolved_parameters is None:
        parameter_status = "all_11_unresolved"
    elif not isinstance(resolved_parameters, Mapping):
        raise CheckpointManifestInputError(
            "resolved_parameters must be a mapping when supplied"
        )
    else:
        present = tuple(name for name in names if name in resolved_parameters)
        extras = tuple(key for key in resolved_parameters if key not in set(names))
        if len(present) == 11 and not extras:
            parameter_status = (
                "all_11_caller_values_present_but_unverified_and_not_authorized"
            )
        else:
            parameter_status = (
                f"partial_{len(present)}_of_11_caller_values_present;"
                f"unexpected_keys={extras!r}"
            )
    evidence_status = (
        "runtime_execution_evidence",
        "event_gated_assignment_runtime_evidence",
        "training_integration_evidence",
        "checkpoint_weight_use_evidence",
    )
    if runtime_evidence is not None:
        if not isinstance(runtime_evidence, Mapping):
            raise CheckpointManifestInputError(
                "runtime_evidence must be a mapping when supplied"
            )
        evidence_status = (
            "caller_runtime_evidence_present_but_not_phase_a_verified",
        )
    inventory_status = (
        "deferred"
        if state_dict_inventory is None
        else "caller_inventory_present_but_phase_a_state_dict_inventory_deferred"
    )
    _raise_ready_not_authorized(
        parameter_status=parameter_status,
        missing_runtime_evidence_categories=evidence_status,
        state_dict_inventory_status=inventory_status,
    )


def canonical_assignment_checkpoint_manifest_v3_bytes(
    manifest: AssignmentCheckpointContractManifestV3 | Mapping[str, object],
) -> bytes:
    """Return canonical UTF-8 JSON bytes for an interface-only V3 manifest."""

    candidate = (
        manifest.to_mapping()
        if isinstance(manifest, AssignmentCheckpointContractManifestV3)
        else manifest
    )
    validated = AssignmentCheckpointContractManifestV3.from_mapping(candidate)
    text = json.dumps(
        validated.to_mapping(),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return text.encode("utf-8")


def compute_assignment_checkpoint_manifest_v3_sha256(
    manifest: AssignmentCheckpointContractManifestV3 | Mapping[str, object],
) -> str:
    """Return lowercase SHA-256 of canonical V3 interface semantic bytes."""

    return hashlib.sha256(
        canonical_assignment_checkpoint_manifest_v3_bytes(manifest)
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class AssignmentCheckpointV3SemanticDecision:
    schema_valid: bool
    interface_semantics_valid: bool
    runtime_ready: bool
    weight_use_authorized: bool
    family_match: bool
    semantic_fingerprint_match: bool
    classification: str
    requested_purpose: AssignmentCheckpointV3Purpose
    reason: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_valid": self.schema_valid,
            "interface_semantics_valid": self.interface_semantics_valid,
            "runtime_ready": self.runtime_ready,
            "weight_use_authorized": self.weight_use_authorized,
            "family_match": self.family_match,
            "semantic_fingerprint_match": self.semantic_fingerprint_match,
            "classification": self.classification,
            "requested_purpose": self.requested_purpose.value,
            "reason": self.reason,
        }


def _coerce_v3_manifest(
    value: AssignmentCheckpointContractManifestV3 | Mapping[str, object],
    *,
    field: str,
) -> AssignmentCheckpointContractManifestV3:
    candidate = (
        value.to_mapping()
        if isinstance(value, AssignmentCheckpointContractManifestV3)
        else value
    )
    if not isinstance(candidate, Mapping):
        raise CheckpointManifestInputError(f"{field} must be a V3 object or mapping")
    version = candidate.get("manifest_format_version")
    if version != MANIFEST_FORMAT_VERSION:
        raise CheckpointManifestFamilyMismatchError(
            f"{field} semantic family is {version!r}, not "
            f"{MANIFEST_FORMAT_VERSION!r}; equal tensor shapes do not make "
            "V2 and V3 compatible"
        )
    return AssignmentCheckpointContractManifestV3.from_mapping(candidate)


def evaluate_assignment_checkpoint_manifest_v3_semantics(
    checkpoint_manifest: (
        AssignmentCheckpointContractManifestV3 | Mapping[str, object]
    ),
    *,
    current_manifest: (
        AssignmentCheckpointContractManifestV3 | Mapping[str, object] | None
    ) = None,
    purpose: AssignmentCheckpointV3Purpose = (
        AssignmentCheckpointV3Purpose.INTERFACE_AUDIT
    ),
) -> AssignmentCheckpointV3SemanticDecision:
    """Audit V3 interface semantics without claiming runtime/weight readiness."""

    if purpose is not AssignmentCheckpointV3Purpose.INTERFACE_AUDIT:
        raise CheckpointManifestPurposeError(
            "V3 interface descriptors allow only AssignmentCheckpointV3Purpose."
            "INTERFACE_AUDIT in Phase A"
        )
    checkpoint = _coerce_v3_manifest(
        checkpoint_manifest, field="checkpoint_manifest"
    )
    current = (
        checkpoint
        if current_manifest is None
        else _coerce_v3_manifest(current_manifest, field="current_manifest")
    )
    fingerprints_match = (
        compute_assignment_checkpoint_manifest_v3_sha256(checkpoint)
        == compute_assignment_checkpoint_manifest_v3_sha256(current)
    )
    return AssignmentCheckpointV3SemanticDecision(
        schema_valid=True,
        interface_semantics_valid=fingerprints_match,
        runtime_ready=False,
        weight_use_authorized=False,
        family_match=True,
        semantic_fingerprint_match=fingerprints_match,
        classification=(
            "interface_audit_valid_not_runtime_ready"
            if fingerprints_match
            else "interface_semantic_mismatch"
        ),
        requested_purpose=purpose,
        reason=(
            "V3 interface semantics are schema-valid and equal; runtime and "
            "checkpoint weight use remain unauthorized"
            if fingerprints_match
            else "V3 interface semantic fingerprints differ; runtime and "
            "checkpoint weight use remain unauthorized"
        ),
    )


__all__ = [
    "ASSIGNMENT_CHECKPOINT_MANIFEST_FORMAT_VERSION_V3",
    "AssignmentCheckpointContractManifestV3",
    "AssignmentCheckpointManifestKind",
    "AssignmentCheckpointV3ContractError",
    "AssignmentCheckpointV3Purpose",
    "AssignmentCheckpointV3SemanticDecision",
    "CANONICAL_ASSIGNMENT_CHECKPOINT_CONTRACT_V3_MODULE",
    "CheckpointManifestFamilyMismatchError",
    "CheckpointManifestInputError",
    "CheckpointManifestPurposeError",
    "CheckpointManifestSchemaError",
    "CheckpointReadyManifestNotAuthorizedError",
    "CheckpointRuntimeReadinessError",
    "CheckpointV3ActionContractSection",
    "CheckpointV3ActorSchemaSection",
    "CheckpointV3ComponentContractSection",
    "CheckpointV3CostPathContractSection",
    "CheckpointV3DecisionValidTrainingContractSection",
    "CheckpointV3DiagnosticsContractSection",
    "CheckpointV3EventTickContractSection",
    "CheckpointV3FailureTerminationContractSection",
    "CheckpointV3IdentitySection",
    "CheckpointV3LocalCandidateContractSection",
    "CheckpointV3ModelStructureSection",
    "CheckpointV3PolicySequenceContractSection",
    "CheckpointV3RewardContractSection",
    "CheckpointV3RuntimeReadinessSection",
    "CheckpointV3ScaleSection",
    "CheckpointV3SequentialFactorContractSection",
    "CheckpointV3SharedSchemaSection",
    "CheckpointV3TrainingContractSection",
    "CheckpointV3TransitionContractSection",
    "MANIFEST_FORMAT_VERSION",
    "SEMANTIC_SECTION_NAMES",
    "TOP_LEVEL_KEY_ORDER",
    "UnresolvedCheckpointParameterError",
    "UnsupportedCheckpointManifestKindError",
    "UnsupportedCheckpointManifestVersionError",
    "build_checkpoint_ready_v3",
    "build_interface_semantic_descriptor_v3",
    "canonical_assignment_checkpoint_manifest_v3_bytes",
    "compute_assignment_checkpoint_manifest_v3_sha256",
    "evaluate_assignment_checkpoint_manifest_v3_semantics",
    "parse_assignment_checkpoint_manifest_v3",
]
