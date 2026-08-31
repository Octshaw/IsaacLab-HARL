"""Pure no-clock schema contracts for event-profile policy evidence.

This module defines immutable version-two identity and numerical-layout
descriptors only.  It does not project observations, compute legality, classify
rows, route proposals, or enable an event-profile runtime.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract_v2"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment event-profile schema v2 "
        "must be imported under its canonical module key before declaring "
        "identity-bearing types; expected="
        f"{CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from types import MappingProxyType

from .assignment_profile_contract import (
    ASSIGNMENT_PROFILE_CONTRACT_VERSION,
    AssignmentProfileName,
    AssignmentProfileResolutionOrigin,
    resolve_assignment_profile,
    resolved_assignment_profile_to_mapping,
)


ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION = (
    "assignment_event_profile_schema_contract_v2"
)
EVENT_POLICY_EVIDENCE_IDENTITY_V2_CONTRACT_VERSION = (
    "event_policy_evidence_identity_v2"
)
EVENT_POLICY_SCALE_V2_CONTRACT_VERSION = "event_policy_scale_contract_v2"
EVENT_POLICY_ACTOR_SCHEMA_V2 = "event_policy_actor_observation_schema_v2"
EVENT_POLICY_CRITIC_SCHEMA_V2 = "event_policy_critic_observation_schema_v2"
EVENT_POLICY_ROUTING_SLOTS_V2 = "event_policy_routing_slots_v2"

HISTORICAL_V1_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract"
)
HISTORICAL_V1_CONTRACT_VERSION = "assignment_event_profile_schema_contract_v1"


class AssignmentEventProfileSchemaV2ContractError(RuntimeError):
    """Fail-closed error with stable v2 contract context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.stage = stage
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"expected={expected!r}; actual={actual!r}; "
            f"contract_version={ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION!r}"
        )


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    expected: object = None,
    actual: object = None,
) -> None:
    raise AssignmentEventProfileSchemaV2ContractError(
        message,
        failure_code=failure_code,
        stage=stage,
        expected=expected,
        actual=actual,
    )


def _deep_readonly(value: object) -> object:
    if type(value) is dict:
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if type(value) in (list, tuple):
        return tuple(_deep_readonly(item) for item in value)
    return value


def _require_positive_int(value: object, *, field: str) -> int:
    if type(value) is not int or value <= 0:
        _fail(
            f"{field} must be an exact positive int",
            failure_code="invalid_fixed_cardinality",
            stage="schema_validation",
            expected="positive int",
            actual=value,
        )
    return value


def _require_finite_positive_float(value: object, *, field: str) -> float:
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        _fail(
            f"{field} must be an exact finite positive float",
            failure_code="invalid_scale_value",
            stage="scale_validation",
            expected="finite positive float",
            actual=value,
        )
    return value


def _require_generation_tuple(
    value: object,
    *,
    field: str,
    expected_length: int,
    minimum: int,
) -> tuple[int, ...]:
    if type(value) is not tuple or len(value) != expected_length:
        _fail(
            f"{field} must be an exact tuple with one entry per environment",
            failure_code=f"invalid_{field}",
            stage="identity_validation",
            expected=f"tuple[int] length {expected_length}",
            actual=type(value).__name__ if type(value) is not tuple else len(value),
        )
    if any(type(item) is not int or item < minimum for item in value):
        _fail(
            f"{field} contains an invalid generation value",
            failure_code=f"invalid_{field}",
            stage="identity_validation",
            expected=f"exact ints >= {minimum}",
            actual=value,
        )
    return value


def _require_opaque_identity(value: object, *, field: str) -> object:
    if value is None or type(value) in (bool, int, float, complex, str, bytes):
        _fail(
            f"{field} must be an opaque reference object, not a serialized value",
            failure_code=f"invalid_{field}",
            stage="identity_capture",
            expected="non-primitive opaque object",
            actual=type(value).__name__,
        )
    return value


@dataclass(frozen=True, slots=True, init=False)
class EventPolicyEvidenceIdentityV2:
    """Opaque runtime binding metadata; never a numerical model feature."""

    schema_version: str
    profile_name: str
    M: int
    N: int
    episode_generations: tuple[int, ...]
    transition_generations: tuple[int, ...]
    _p2_publication_identity: object
    _open_window_identity: object

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "direct construction is forbidden; use the canonical capture factory",
            failure_code="direct_identity_construction_forbidden",
            stage="identity_capture",
            expected="capture_event_policy_evidence_identity_v2",
            actual="direct constructor",
        )

    @classmethod
    def _capture(
        cls,
        *,
        p2_publication_identity: object,
        episode_generations: tuple[int, ...],
        transition_generations: tuple[int, ...],
        open_window_identity: object,
        M: int,
        N: int,
    ) -> "EventPolicyEvidenceIdentityV2":
        publication = _require_opaque_identity(
            p2_publication_identity, field="p2_publication_identity"
        )
        window = _require_opaque_identity(
            open_window_identity, field="open_window_identity"
        )
        fixed_M = _require_positive_int(M, field="M")
        fixed_N = _require_positive_int(N, field="N")
        if type(episode_generations) is not tuple:
            env_count = -1
        else:
            env_count = len(episode_generations)
        if env_count <= 0:
            _fail(
                "identity must cover at least one environment",
                failure_code="invalid_environment_count",
                stage="identity_capture",
                expected="positive tuple length",
                actual=env_count,
            )
        episodes = _require_generation_tuple(
            episode_generations,
            field="episode_generations",
            expected_length=env_count,
            minimum=0,
        )
        transitions = _require_generation_tuple(
            transition_generations,
            field="transition_generations",
            expected_length=env_count,
            minimum=-1,
        )
        instance = object.__new__(cls)
        object.__setattr__(
            instance, "schema_version", EVENT_POLICY_EVIDENCE_IDENTITY_V2_CONTRACT_VERSION
        )
        object.__setattr__(
            instance, "profile_name", AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
        )
        object.__setattr__(instance, "M", fixed_M)
        object.__setattr__(instance, "N", fixed_N)
        object.__setattr__(instance, "episode_generations", episodes)
        object.__setattr__(instance, "transition_generations", transitions)
        object.__setattr__(instance, "_p2_publication_identity", publication)
        object.__setattr__(instance, "_open_window_identity", window)
        return instance

    @property
    def p2_publication_identity(self) -> object:
        """Return the opaque reference without serializing or encoding it."""

        return self._p2_publication_identity

    @property
    def open_window_identity(self) -> object:
        """Return the exact opaque OPEN reference, not a counter or timestamp."""

        return self._open_window_identity

    @property
    def num_envs(self) -> int:
        return len(self.episode_generations)

    def validate_current(
        self,
        *,
        p2_publication_identity: object,
        episode_generations: tuple[int, ...],
        transition_generations: tuple[int, ...],
        open_window_identity: object,
        M: int,
        N: int,
    ) -> None:
        """Reject stale or recreated identity components without mutation."""

        if p2_publication_identity is not self._p2_publication_identity:
            _fail(
                "policy evidence belongs to a different P2 publication",
                failure_code="p2_publication_identity_mismatch",
                stage="stale_evidence_validation",
                expected="same opaque P2 publication object",
                actual=type(p2_publication_identity).__name__,
            )
        episodes = _require_generation_tuple(
            episode_generations,
            field="episode_generations",
            expected_length=self.num_envs,
            minimum=0,
        )
        if episodes != self.episode_generations:
            _fail(
                "policy evidence episode generations are stale",
                failure_code="episode_generation_mismatch",
                stage="stale_evidence_validation",
                expected=self.episode_generations,
                actual=episodes,
            )
        transitions = _require_generation_tuple(
            transition_generations,
            field="transition_generations",
            expected_length=self.num_envs,
            minimum=-1,
        )
        if transitions != self.transition_generations:
            _fail(
                "policy evidence transition generations are stale",
                failure_code="transition_generation_mismatch",
                stage="stale_evidence_validation",
                expected=self.transition_generations,
                actual=transitions,
            )
        if open_window_identity is not self._open_window_identity:
            _fail(
                "policy evidence belongs to a different OPEN window",
                failure_code="open_window_identity_mismatch",
                stage="stale_evidence_validation",
                expected="same opaque OPEN window object",
                actual=type(open_window_identity).__name__,
            )
        if M != self.M or N != self.N or type(M) is not int or type(N) is not int:
            _fail(
                "policy evidence fixed-cardinality identity is inconsistent",
                failure_code="fixed_cardinality_mismatch",
                stage="stale_evidence_validation",
                expected=(self.M, self.N),
                actual=(M, N),
            )


def capture_event_policy_evidence_identity_v2(
    *,
    p2_publication_identity: object,
    episode_generations: tuple[int, ...],
    transition_generations: tuple[int, ...],
    open_window_identity: object,
    M: int,
    N: int,
) -> EventPolicyEvidenceIdentityV2:
    """Capture exact current references and generation tuples as metadata."""

    return EventPolicyEvidenceIdentityV2._capture(
        p2_publication_identity=p2_publication_identity,
        episode_generations=episode_generations,
        transition_generations=transition_generations,
        open_window_identity=open_window_identity,
        M=M,
        N=N,
    )


def validate_event_policy_evidence_identity_v2_current(
    identity: EventPolicyEvidenceIdentityV2,
    *,
    p2_publication_identity: object,
    episode_generations: tuple[int, ...],
    transition_generations: tuple[int, ...],
    open_window_identity: object,
    M: int,
    N: int,
) -> None:
    """Canonical fail-closed validator for a captured v2 identity."""

    if type(identity) is not EventPolicyEvidenceIdentityV2:
        _fail(
            "identity must use the canonical v2 class",
            failure_code="noncanonical_identity_type",
            stage="stale_evidence_validation",
            expected=EventPolicyEvidenceIdentityV2,
            actual=type(identity),
        )
    identity.validate_current(
        p2_publication_identity=p2_publication_identity,
        episode_generations=episode_generations,
        transition_generations=transition_generations,
        open_window_identity=open_window_identity,
        M=M,
        N=N,
    )


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


def build_event_policy_scale_contract_v2(
    *,
    M: int,
    N: int,
    ordered_agent_names: tuple[str, ...],
    ordered_task_ids: tuple[int, ...],
    scene_env_spacing: float,
    sim_dt_seconds: float,
    control_decimation: int,
    episode_time_limit_seconds: float,
) -> Mapping[str, object]:
    """Build immutable fixed-cardinality scale identity for the v2 manifest."""

    fixed_M = _require_positive_int(M, field="M")
    fixed_N = _require_positive_int(N, field="N")
    if (
        type(ordered_agent_names) is not tuple
        or len(ordered_agent_names) != fixed_M
        or any(type(item) is not str or not item for item in ordered_agent_names)
        or len(set(ordered_agent_names)) != fixed_M
    ):
        _fail(
            "ordered_agent_names must be a unique exact tuple of length M",
            failure_code="invalid_agent_order",
            stage="scale_validation",
            expected=f"unique tuple[str] length {fixed_M}",
            actual=ordered_agent_names,
        )
    if (
        type(ordered_task_ids) is not tuple
        or ordered_task_ids != tuple(range(fixed_N))
    ):
        _fail(
            "ordered_task_ids must equal the canonical fixed task order",
            failure_code="invalid_task_order",
            stage="scale_validation",
            expected=tuple(range(fixed_N)),
            actual=ordered_task_ids,
        )
    spacing = _require_finite_positive_float(scene_env_spacing, field="scene_env_spacing")
    sim_dt = _require_finite_positive_float(sim_dt_seconds, field="sim_dt_seconds")
    decimation = _require_positive_int(control_decimation, field="control_decimation")
    time_limit = _require_finite_positive_float(
        episode_time_limit_seconds, field="episode_time_limit_seconds"
    )
    control_step = sim_dt * decimation
    horizon_ratio = time_limit / control_step
    horizon = round(horizon_ratio)
    if not math.isclose(horizon_ratio, horizon, rel_tol=0.0, abs_tol=1.0e-9):
        _fail(
            "episode horizon must be an integral number of physical control steps",
            failure_code="nonintegral_episode_horizon",
            stage="scale_validation",
            expected="integral episode_time_limit / control_step",
            actual=horizon_ratio,
        )
    return _deep_readonly(
        {
            "contract_version": EVENT_POLICY_SCALE_V2_CONTRACT_VERSION,
            "M": fixed_M,
            "N": fixed_N,
            "ordered_agent_names": ordered_agent_names,
            "ordered_task_ids": ordered_task_ids,
            "scene_env_spacing": spacing,
            "sim_dt_seconds": sim_dt,
            "control_decimation": decimation,
            "physical_control_step_seconds": control_step,
            "episode_time_limit_seconds": time_limit,
            "episode_horizon_steps": horizon,
        }
    )


def _validated_scale_copy(scale_contract: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(scale_contract, Mapping) or tuple(scale_contract.keys()) != _SCALE_KEYS:
        _fail(
            "scale contract keys or order do not match the canonical v2 schema",
            failure_code="invalid_scale_contract_keys",
            stage="schema_validation",
            expected=_SCALE_KEYS,
            actual=tuple(scale_contract.keys()) if isinstance(scale_contract, Mapping) else type(scale_contract),
        )
    return build_event_policy_scale_contract_v2(
        M=scale_contract["M"],
        N=scale_contract["N"],
        ordered_agent_names=scale_contract["ordered_agent_names"],
        ordered_task_ids=scale_contract["ordered_task_ids"],
        scene_env_spacing=scale_contract["scene_env_spacing"],
        sim_dt_seconds=scale_contract["sim_dt_seconds"],
        control_decimation=scale_contract["control_decimation"],
        episode_time_limit_seconds=scale_contract["episode_time_limit_seconds"],
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
    "task_x", "task_y", "task_z", "task_qw", "task_qx", "task_qy", "task_qz",
)
_TASK_LIFECYCLE_COLUMNS = (
    "AVAILABLE", "CLAIMED", "NAVIGATING", "ALIGNING", "COMPLETED", "TEAM_INFEASIBLE",
)

_ACTOR_BLOCK_ROWS = (
    ("actor_robot_identity_one_hot", ("M",), "selected robot identity", "one_hot", ()),
    (
        "global_robot_physical_state",
        ("M", 16),
        "finalized current ordered robot physical snapshot",
        "physical bounds and scene spacing",
        _ROBOT_PHYSICAL_COLUMNS,
    ),
    (
        "global_robot_lifecycle_state",
        ("M", 5),
        "authoritative current P2 robot lifecycle state",
        "one_hot",
        _ROBOT_LIFECYCLE_COLUMNS,
    ),
    ("task_pose", ("N", 7), "ordered task pose", "scene-relative normalized pose", _TASK_POSE_COLUMNS),
    (
        "task_lifecycle_state",
        ("N", 6),
        "authoritative current P2 task lifecycle state",
        "one_hot",
        _TASK_LIFECYCLE_COLUMNS,
    ),
    (
        "task_ownership",
        ("N", "M+1"),
        "authoritative current P2 task owner including unowned",
        "one_hot",
        (),
    ),
    (
        "current_robot_owned_task",
        ("M", "N+1"),
        "authoritative current P2 robot task including none",
        "one_hot",
        (),
    ),
    (
        "failed_pair_state",
        ("M", "N"),
        "authoritative current P2 failed robot-task pairs",
        "binary",
        (),
    ),
    (
        "explicit_physical_feasibility",
        ("M", "N"),
        "environment physical feasibility predicate",
        "binary",
        (),
    ),
    (
        "geometric_pair_ranking_cost",
        ("M", "N"),
        "scanner-to-viewpoint Euclidean distance; ranking only, never feasibility",
        "finite distance divided by scene_env_spacing",
        (),
    ),
    ("robot_workload", ("M", 1), "P2 completion attribution count per robot", "divide by N", ("completed_task_fraction",)),
    (
        "episode_physical_progress_fraction",
        (1,),
        "elapsed physical episode time divided by configured time limit",
        "clamp to [0,1]",
        ("episode_physical_progress_fraction",),
    ),
)


def _block_descriptors(rows: Sequence[tuple[object, ...]]) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _deep_readonly(
            {
                "order": order,
                "name": row[0],
                "shape": row[1],
                "source_dtype": "semantic source contract",
                "serialized_dtype": "float32",
                "semantic_source": row[2],
                "normalization_rule": row[3],
                "column_order": row[4],
                "model_input": True,
            }
        )
        for order, row in enumerate(rows, start=1)
    )


_ACTOR_BLOCKS = _block_descriptors(_ACTOR_BLOCK_ROWS)
_CRITIC_BLOCKS = _block_descriptors(_ACTOR_BLOCK_ROWS[1:])


def _resolve_axis(axis: object, *, M: int, N: int) -> int:
    if type(axis) is int and axis > 0:
        return axis
    values = {"M": M, "N": N, "M+1": M + 1, "N+1": N + 1}
    if type(axis) is str and axis in values:
        return values[axis]
    _fail(
        "schema block contains an unsupported shape axis",
        failure_code="invalid_manifest_shape_axis",
        stage="dimension_derivation",
        expected=tuple(values),
        actual=axis,
    )


def _dimension_from_blocks(
    blocks: Sequence[Mapping[str, object]], *, M: int, N: int
) -> int:
    fixed_M = _require_positive_int(M, field="M")
    fixed_N = _require_positive_int(N, field="N")
    total = 0
    for expected_order, block in enumerate(blocks, start=1):
        if block.get("order") != expected_order or block.get("model_input") is not True:
            _fail(
                "numerical block manifest is malformed",
                failure_code="invalid_numerical_block_manifest",
                stage="dimension_derivation",
                expected=(expected_order, True),
                actual=(block.get("order"), block.get("model_input")),
            )
        product = 1
        shape = block.get("shape")
        if type(shape) is not tuple or not shape:
            _fail(
                "numerical block shape must be a non-empty exact tuple",
                failure_code="invalid_manifest_shape",
                stage="dimension_derivation",
                expected="non-empty tuple",
                actual=shape,
            )
        for axis in shape:
            product *= _resolve_axis(axis, M=fixed_M, N=fixed_N)
        total += product
    return total


def event_policy_actor_observation_dimension_v2(*, M: int, N: int) -> int:
    """Derive O_v2 exclusively by summing semantic actor manifest blocks."""

    return _dimension_from_blocks(_ACTOR_BLOCKS, M=M, N=N)


def event_policy_critic_observation_dimension_v2(*, M: int, N: int) -> int:
    """Derive centralized critic width from semantic critic manifest blocks."""

    return _dimension_from_blocks(_CRITIC_BLOCKS, M=M, N=N)


_IDENTITY_METADATA_FIELDS = (
    "p2_publication_identity",
    "episode_generations",
    "transition_generations",
    "open_window_identity",
)

_ROUTING_SLOT_ROWS = (
    ("row_kind", ("M",), "B2-I2", "categorical routing metadata"),
    ("forced_action_id", ("M",), "B2-I2", "deterministic routing metadata"),
    ("policy_sampled", ("M",), "B2-I2", "training-row routing metadata"),
    ("decision_valid_mask", ("M",), "B2-I2", "buffer participation metadata"),
    ("available_actions", ("M", "N+1"), "B2-I2", "policy sampling legality"),
)


def _profile_binding() -> Mapping[str, object]:
    resolved = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    mapping = resolved_assignment_profile_to_mapping(resolved)
    return _deep_readonly(
        {
            "profile_contract_version": ASSIGNMENT_PROFILE_CONTRACT_VERSION,
            "profile_name": mapping["profile_name"],
            "runtime_route": mapping["runtime_route"],
            "runtime_readiness": mapping["runtime_readiness"],
            "resolution_origin": mapping["resolution_origin"],
            "readiness_change_authorized": False,
        }
    )


def build_assignment_event_profile_schema_v2_descriptor(
    *, scale_contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Build the immutable no-clock v2 schema descriptor."""

    scale = _validated_scale_copy(scale_contract)
    M = scale["M"]
    N = scale["N"]
    routing_slots = tuple(
        _deep_readonly(
            {
                "order": order,
                "name": row[0],
                "shape": row[1],
                "future_implementation_owner": row[2],
                "semantic_role": row[3],
                "implemented_in_b2_i0": False,
                "numerical_model_feature": False,
            }
        )
        for order, row in enumerate(_ROUTING_SLOT_ROWS, start=1)
    )
    return _deep_readonly(
        {
            "contract_version": ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION,
            "historical_v1_reference": {
                "module": HISTORICAL_V1_MODULE,
                "contract_version": HISTORICAL_V1_CONTRACT_VERSION,
                "preservation_rule": "preserve byte and semantic identity; no in-place reinterpretation",
            },
            "profile_binding": _profile_binding(),
            "scale_contract": dict(scale),
            "identity_schema": {
                "contract_version": EVENT_POLICY_EVIDENCE_IDENTITY_V2_CONTRACT_VERSION,
                "metadata_fields": _IDENTITY_METADATA_FIELDS,
                "p2_comparison": "exact opaque object identity",
                "open_window_comparison": "exact opaque object identity",
                "generation_comparison": "exact tuple equality",
                "clock_semantics": "none",
                "numeric_encoding": "forbidden in all model feature forms",
                "mismatch_behavior": "fail closed as stale evidence",
                "mutation_or_rebinding": "forbidden",
            },
            "actor_schema": {
                "schema_version": EVENT_POLICY_ACTOR_SCHEMA_V2,
                "fixed_cardinality": True,
                "flatten_order": "block order then row major",
                "blocks": _ACTOR_BLOCKS,
                "dimension_derivation": "sum product of resolved manifest block shapes",
                "dimension_formula_audit": "5*M*N + 24*M + 14*N + 1",
                "dimension": event_policy_actor_observation_dimension_v2(M=M, N=N),
                "identity_metadata_fields_excluded": _IDENTITY_METADATA_FIELDS,
                "routing_fields_excluded": tuple(row[0] for row in _ROUTING_SLOT_ROWS),
                "projector_implemented": False,
            },
            "critic_schema": {
                "schema_version": EVENT_POLICY_CRITIC_SCHEMA_V2,
                "fixed_cardinality": True,
                "construction": "central semantic state; not actor concatenation",
                "blocks": _CRITIC_BLOCKS,
                "dimension_derivation": "sum product of resolved manifest block shapes",
                "dimension_formula_audit": "5*M*N + 23*M + 14*N + 1",
                "dimension": event_policy_critic_observation_dimension_v2(M=M, N=N),
                "identity_metadata_fields_excluded": _IDENTITY_METADATA_FIELDS,
                "routing_fields_excluded": tuple(row[0] for row in _ROUTING_SLOT_ROWS),
                "termination_reason_is_transition_metadata": True,
                "projector_implemented": False,
            },
            "future_routing_slots": {
                "schema_version": EVENT_POLICY_ROUTING_SLOTS_V2,
                "slots": routing_slots,
                "legality_computation_implemented": False,
                "row_classification_implemented": False,
                "forced_action_generation_implemented": False,
                "proposal_routing_implemented": False,
            },
            "external_evidence_seams": (
                {
                    "name": "validated_path_feasibility",
                    "included_in_numerical_schema": False,
                    "missing_behavior": "explicitly omitted; no synthetic default",
                },
                {
                    "name": "validated_path_or_nominal_pair_cost",
                    "included_in_numerical_schema": False,
                    "missing_behavior": "explicitly omitted; no synthetic default",
                },
                {
                    "name": "local_candidate_selection",
                    "included_in_numerical_schema": False,
                    "missing_behavior": "explicitly omitted; no synthetic default",
                },
                {
                    "name": "assignment_retry_opportunity",
                    "included_in_numerical_schema": False,
                    "missing_behavior": "explicitly omitted; no synthetic default",
                },
            ),
            "compatibility_contract": {
                "historical_actor_dimension_reference_M3_N12": 476,
                "historical_shared_dimension_reference_M3_N12": 497,
                "dimension_equality_required": False,
                "reserved_compatibility_slot_present": False,
                "learned_event_profile_checkpoint_exists": False,
            },
            "scope_barriers": {
                "actor_projector": "B2-I1 not authorized",
                "critic_projector": "B2-I1 not authorized",
                "dvm_and_row_semantics": "B2-I2 not authorized",
                "runtime_integration": False,
                "learner_integration": False,
                "variable_cardinality": False,
            },
        }
    )


__all__ = (
    "ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION",
    "AssignmentEventProfileSchemaV2ContractError",
    "CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_MODULE",
    "EVENT_POLICY_ACTOR_SCHEMA_V2",
    "EVENT_POLICY_CRITIC_SCHEMA_V2",
    "EVENT_POLICY_EVIDENCE_IDENTITY_V2_CONTRACT_VERSION",
    "EVENT_POLICY_ROUTING_SLOTS_V2",
    "EVENT_POLICY_SCALE_V2_CONTRACT_VERSION",
    "EventPolicyEvidenceIdentityV2",
    "build_assignment_event_profile_schema_v2_descriptor",
    "build_event_policy_scale_contract_v2",
    "capture_event_policy_evidence_identity_v2",
    "event_policy_actor_observation_dimension_v2",
    "event_policy_critic_observation_dimension_v2",
    "validate_event_policy_evidence_identity_v2_current",
)
