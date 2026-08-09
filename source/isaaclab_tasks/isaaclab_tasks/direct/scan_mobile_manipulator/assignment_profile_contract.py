"""Pure assignment-profile registry and resolved identity contracts.

This module deliberately has no Isaac Lab, HARL, torch, scenario, runner, or
checkpoint dependency.  Phase A1a defines identity only; it does not enable an
event-gated runtime route.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_PROFILE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
)
ASSIGNMENT_PROFILE_SOURCE_PURPOSE = (
    "pure assignment profile registry and resolved identity contract"
)

if __name__ != CANONICAL_ASSIGNMENT_PROFILE_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment profile contract source must "
        "fail before declaring identity-bearing types; "
        f"expected module key={CANONICAL_ASSIGNMENT_PROFILE_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose={ASSIGNMENT_PROFILE_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TypeAlias


ASSIGNMENT_PROFILE_CONTRACT_VERSION = "assignment_resolved_profile_v1"
EVENT_GATED_TARGET_SEMANTICS_VERSION = "event_gated_target_semantics_v1"
LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON = (
    "assignment_lifecycle_profile='lifecycle_ablation' is an explicit "
    "observation/mask ablation profile and is not enabled for normal training."
)


class AssignmentProfileName(str, Enum):
    """Canonical assignment profile selector vocabulary."""

    LEGACY = "legacy"
    LIFECYCLE_ABLATION = "lifecycle_ablation"
    LIFECYCLE_CONTRACT_C = "lifecycle_contract_c"
    DIAGNOSTICS_HIDDEN_STATE = "diagnostics_hidden_state"
    EVENT_GATED_LOCAL_MRTA = "event_gated_local_mrta"


class AssignmentRuntimeRoute(str, Enum):
    """Resolved route identity; the four existing values name current paths."""

    EXISTING_LEGACY_ASSIGNMENT_HARL = "existing_legacy_assignment_harl_v1"
    EXISTING_LIFECYCLE_ABLATION_ASSIGNMENT_HARL = (
        "existing_lifecycle_ablation_assignment_harl_v1"
    )
    EXISTING_LIFECYCLE_CONTRACT_C_ASSIGNMENT_HARL = (
        "existing_lifecycle_contract_c_assignment_harl_v1"
    )
    EXISTING_DIAGNOSTICS_HIDDEN_STATE_ASSIGNMENT_HARL = (
        "existing_diagnostics_hidden_state_assignment_harl_v1"
    )
    EVENT_GATED_PHASE_A_INTERFACE_ONLY = "event_gated_phase_a_interface_only_v1"


class AssignmentCheckpointFamily(str, Enum):
    """Checkpoint compatibility identity, not a save/load implementation.

    The explicit-ablation value is a named v2 evaluation compatibility target.
    It is not a new manifest format or a native ablation save family.
    """

    ASSIGNMENT_CHECKPOINT_CONTRACT_V2 = "assignment_checkpoint_contract_v2"
    ASSIGNMENT_CHECKPOINT_CONTRACT_V2_EXPLICIT_ABLATION_EVALUATION = (
        "assignment_checkpoint_contract_v2_explicit_ablation_evaluation"
    )
    NONE = "none"
    ASSIGNMENT_CHECKPOINT_CONTRACT_V3 = "assignment_checkpoint_contract_v3"


class AssignmentProfileSupport(str, Enum):
    """Training and playback support vocabulary.

    The two fields intentionally share one vocabulary.  Resolved-profile
    validation enforces disjoint training and playback subsets.
    """

    ALLOWED = "allowed"
    EXISTING_BLOCKED = "existing_blocked"
    PHASE_A_BLOCKED = "phase_a_blocked"
    NORMAL = "normal"
    EXPLICIT_ABLATION = "explicit_ablation"
    DIAGNOSTICS = "diagnostics"
    BLOCKED = "blocked"


class AssignmentRuntimeReadiness(str, Enum):
    """Whether the selected route already has a production runtime."""

    EXISTING_READY = "existing_ready"
    INTERFACE_ONLY = "interface_only"


class AssignmentProfileResolutionOrigin(str, Enum):
    """Explicit authority that requested profile resolution."""

    FORMAL_ENTRYPOINT = "formal_entrypoint"
    DIRECT_WRAPPER_FALLBACK = "direct_wrapper_fallback"


class AssignmentProfileContractError(RuntimeError):
    """Base error carrying stable assignment-profile contract context."""

    def __init__(
        self,
        message: str,
        *,
        profile: object = None,
        expected: object = None,
        actual: object = None,
        contract_version: str = ASSIGNMENT_PROFILE_CONTRACT_VERSION,
        resolution_origin: object = None,
    ) -> None:
        self.profile = profile
        self.expected = expected
        self.actual = actual
        self.contract_version = contract_version
        self.resolution_origin = resolution_origin
        super().__init__(
            f"{message}; "
            f"profile={_context_value(profile)!r}; "
            f"expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; "
            f"contract_version={contract_version!r}; "
            f"resolution_origin={_context_value(resolution_origin)!r}"
        )


class ProfileResolutionError(AssignmentProfileContractError):
    """Base error for selector or origin resolution failures."""


class UnknownAssignmentProfileError(ProfileResolutionError):
    """A non-empty selector is not one of the five canonical profiles."""


class InvalidAssignmentProfileError(ProfileResolutionError):
    """A profile contract value has the wrong type or is empty/inconsistent."""


class AssignmentProfileRegistryError(AssignmentProfileContractError):
    """The exhaustive immutable registry is incomplete or inconsistent."""


class AssignmentProfileRouteError(AssignmentProfileContractError):
    """A resolved subtype was routed to an incompatible consumer."""


class ResolvedProfileMismatchError(AssignmentProfileContractError):
    """A caller's raw declaration, resolved identity, or origin disagrees."""


class PhaseAExecutionNotAuthorizedError(AssignmentProfileRouteError):
    """The interface-only event profile reached a Phase A runtime barrier."""


class CanonicalModuleIdentityError(AssignmentProfileContractError):
    """Canonical module/type identity validation failed after canonical import."""


def _context_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return value


def _require_nonempty_string(
    value: object,
    *,
    field: str,
    profile: object = None,
    resolution_origin: object = None,
) -> None:
    if type(value) is not str or not value:
        raise InvalidAssignmentProfileError(
            f"{field} must be a non-empty exact string",
            profile=profile,
            expected="non-empty str",
            actual=value,
            resolution_origin=resolution_origin,
        )


def _require_optional_string(
    value: object,
    *,
    field: str,
    profile: object = None,
    resolution_origin: object = None,
) -> None:
    if value is not None:
        _require_nonempty_string(
            value,
            field=field,
            profile=profile,
            resolution_origin=resolution_origin,
        )


def _require_optional_bool(
    value: object,
    *,
    field: str,
    profile: object = None,
    resolution_origin: object = None,
) -> None:
    if value is not None and type(value) is not bool:
        raise InvalidAssignmentProfileError(
            f"{field} must be bool or None",
            profile=profile,
            expected="bool | None",
            actual=value,
            resolution_origin=resolution_origin,
        )


@dataclass(frozen=True, slots=True)
class TrainingSemanticContract:
    """Immutable policy/training identity for one resolved profile."""

    contract_version: str
    algorithm_name: str | None
    state_type: str | None
    share_param: bool | None
    use_recurrent_policy: bool | None
    use_naive_recurrent_policy: bool | None
    actor_buffer_generator: str | None
    serialization_mode: str | None
    save_entire_model: bool | None
    installed_harl_mutable: bool

    def __post_init__(self) -> None:
        _require_nonempty_string(self.contract_version, field="training.contract_version")
        for field, value in (
            ("training.algorithm_name", self.algorithm_name),
            ("training.state_type", self.state_type),
            ("training.actor_buffer_generator", self.actor_buffer_generator),
            ("training.serialization_mode", self.serialization_mode),
        ):
            _require_optional_string(value, field=field)
        for field, value in (
            ("training.share_param", self.share_param),
            ("training.use_recurrent_policy", self.use_recurrent_policy),
            (
                "training.use_naive_recurrent_policy",
                self.use_naive_recurrent_policy,
            ),
            ("training.save_entire_model", self.save_entire_model),
        ):
            _require_optional_bool(value, field=field)
        if type(self.installed_harl_mutable) is not bool:
            raise InvalidAssignmentProfileError(
                "training.installed_harl_mutable must be bool",
                expected="bool",
                actual=self.installed_harl_mutable,
            )


@dataclass(frozen=True, slots=True)
class EventGatedTargetSemantics:
    """Interface-only target identity for the future event-gated route."""

    contract_version: str
    actor_schema_version: str
    shared_schema_version: str
    shared_construction_mode: str
    mask_contract_version: str
    budget_release_contract: str
    policy_sequence_route: str
    training_semantic_contract: TrainingSemanticContract

    def __post_init__(self) -> None:
        for field, value in (
            ("event.contract_version", self.contract_version),
            ("event.actor_schema_version", self.actor_schema_version),
            ("event.shared_schema_version", self.shared_schema_version),
            ("event.shared_construction_mode", self.shared_construction_mode),
            ("event.mask_contract_version", self.mask_contract_version),
            ("event.budget_release_contract", self.budget_release_contract),
            ("event.policy_sequence_route", self.policy_sequence_route),
        ):
            _require_nonempty_string(value, field=field)
        if type(self.training_semantic_contract) is not TrainingSemanticContract:
            raise InvalidAssignmentProfileError(
                "event training semantic contract has noncanonical type identity",
                expected=TrainingSemanticContract,
                actual=type(self.training_semantic_contract),
            )


_TRAINING_SUPPORT_VALUES = frozenset(
    {
        AssignmentProfileSupport.ALLOWED,
        AssignmentProfileSupport.EXISTING_BLOCKED,
        AssignmentProfileSupport.PHASE_A_BLOCKED,
    }
)
_PLAYBACK_SUPPORT_VALUES = frozenset(
    {
        AssignmentProfileSupport.NORMAL,
        AssignmentProfileSupport.EXPLICIT_ABLATION,
        AssignmentProfileSupport.DIAGNOSTICS,
        AssignmentProfileSupport.BLOCKED,
    }
)


def _validate_common_resolved_fields(
    *,
    profile_contract_version: object,
    profile_name: object,
    resolution_origin: object,
    runtime_route: object,
    checkpoint_family: object,
    training_support: object,
    playback_support: object,
    runtime_readiness: object,
) -> None:
    if (
        type(profile_contract_version) is not str
        or profile_contract_version != ASSIGNMENT_PROFILE_CONTRACT_VERSION
    ):
        raise InvalidAssignmentProfileError(
            "resolved profile contract version mismatch",
            profile=profile_name,
            expected=ASSIGNMENT_PROFILE_CONTRACT_VERSION,
            actual=profile_contract_version,
            resolution_origin=resolution_origin,
        )
    for field, value, expected_type in (
        ("profile_name", profile_name, AssignmentProfileName),
        ("resolution_origin", resolution_origin, AssignmentProfileResolutionOrigin),
        ("runtime_route", runtime_route, AssignmentRuntimeRoute),
        ("checkpoint_family", checkpoint_family, AssignmentCheckpointFamily),
        ("training_support", training_support, AssignmentProfileSupport),
        ("playback_support", playback_support, AssignmentProfileSupport),
        ("runtime_readiness", runtime_readiness, AssignmentRuntimeReadiness),
    ):
        if type(value) is not expected_type:
            raise InvalidAssignmentProfileError(
                f"resolved {field} has noncanonical enum identity",
                profile=profile_name,
                expected=expected_type,
                actual=type(value),
                resolution_origin=resolution_origin,
            )
    if training_support not in _TRAINING_SUPPORT_VALUES:
        raise InvalidAssignmentProfileError(
            "training_support uses a playback-only support value",
            profile=profile_name,
            expected=tuple(value.value for value in _TRAINING_SUPPORT_VALUES),
            actual=training_support,
            resolution_origin=resolution_origin,
        )
    if playback_support not in _PLAYBACK_SUPPORT_VALUES:
        raise InvalidAssignmentProfileError(
            "playback_support uses a training-only support value",
            profile=profile_name,
            expected=tuple(value.value for value in _PLAYBACK_SUPPORT_VALUES),
            actual=playback_support,
            resolution_origin=resolution_origin,
        )


@dataclass(frozen=True, slots=True)
class ResolvedExistingAssignmentProfile:
    """Resolved identity for one of the four current runtime profiles."""

    profile_contract_version: str
    profile_name: AssignmentProfileName
    resolution_origin: AssignmentProfileResolutionOrigin
    runtime_route: AssignmentRuntimeRoute
    checkpoint_family: AssignmentCheckpointFamily
    training_support: AssignmentProfileSupport
    playback_support: AssignmentProfileSupport
    runtime_readiness: AssignmentRuntimeReadiness
    resolver_enabled: bool
    lifecycle_observation_enabled: bool
    lifecycle_mask_enabled: bool
    actor_schema_version: str
    shared_schema_version: str
    shared_construction_mode: str
    mask_contract_version: str
    budget_release_contract: str
    legacy_guardrail_profile: str
    policy_sequence_route: str
    training_semantic_contract: TrainingSemanticContract

    def __post_init__(self) -> None:
        _validate_common_resolved_fields(
            profile_contract_version=self.profile_contract_version,
            profile_name=self.profile_name,
            resolution_origin=self.resolution_origin,
            runtime_route=self.runtime_route,
            checkpoint_family=self.checkpoint_family,
            training_support=self.training_support,
            playback_support=self.playback_support,
            runtime_readiness=self.runtime_readiness,
        )
        if self.profile_name is AssignmentProfileName.EVENT_GATED_LOCAL_MRTA:
            raise InvalidAssignmentProfileError(
                "event-gated profile cannot use the existing-profile subtype",
                profile=self.profile_name,
                expected=ResolvedEventGatedAssignmentProfile,
                actual=ResolvedExistingAssignmentProfile,
                resolution_origin=self.resolution_origin,
            )
        for field, value in (
            ("resolver_enabled", self.resolver_enabled),
            ("lifecycle_observation_enabled", self.lifecycle_observation_enabled),
            ("lifecycle_mask_enabled", self.lifecycle_mask_enabled),
        ):
            if type(value) is not bool:
                raise InvalidAssignmentProfileError(
                    f"{field} must be bool",
                    profile=self.profile_name,
                    expected="bool",
                    actual=value,
                    resolution_origin=self.resolution_origin,
                )
        for field, value in (
            ("actor_schema_version", self.actor_schema_version),
            ("shared_schema_version", self.shared_schema_version),
            ("shared_construction_mode", self.shared_construction_mode),
            ("mask_contract_version", self.mask_contract_version),
            ("budget_release_contract", self.budget_release_contract),
            ("legacy_guardrail_profile", self.legacy_guardrail_profile),
            ("policy_sequence_route", self.policy_sequence_route),
        ):
            _require_nonempty_string(
                value,
                field=field,
                profile=self.profile_name,
                resolution_origin=self.resolution_origin,
            )
        if type(self.training_semantic_contract) is not TrainingSemanticContract:
            raise InvalidAssignmentProfileError(
                "existing training semantic contract has noncanonical type identity",
                profile=self.profile_name,
                expected=TrainingSemanticContract,
                actual=type(self.training_semantic_contract),
                resolution_origin=self.resolution_origin,
            )
        definition = _PROFILE_DEFINITIONS.get(self.profile_name)
        if type(definition) is not _ExistingProfileDefinition:
            raise AssignmentProfileRouteError(
                "existing-profile subtype has no existing registry definition",
                profile=self.profile_name,
                expected="existing profile definition",
                actual=type(definition),
                resolution_origin=self.resolution_origin,
            )
        if _existing_resolved_identity_tuple(self) != _existing_definition_identity_tuple(
            definition
        ):
            raise InvalidAssignmentProfileError(
                "existing resolved identity differs from the exhaustive registry",
                profile=self.profile_name,
                expected=_existing_definition_identity_tuple(definition),
                actual=_existing_resolved_identity_tuple(self),
                resolution_origin=self.resolution_origin,
            )

    def to_legacy_wrapper_mapping(self) -> dict[str, object]:
        """Reproduce the current wrapper mapping exactly, including key order."""

        result: dict[str, object] = {
            "profile_name": self.profile_name.value,
            "actor_schema_version": self.actor_schema_version,
            "shared_schema_version": self.shared_schema_version,
            "shared_construction_mode": self.shared_construction_mode,
            "mask_contract_version": self.mask_contract_version,
            "budget_release_contract": self.budget_release_contract,
            "legacy_guardrail_profile": self.legacy_guardrail_profile,
            "resolver_enabled": self.resolver_enabled,
            "lifecycle_observation_enabled": self.lifecycle_observation_enabled,
            "lifecycle_mask_enabled": self.lifecycle_mask_enabled,
            "training_allowed": self.training_support
            is AssignmentProfileSupport.ALLOWED,
        }
        if self.profile_name is AssignmentProfileName.LIFECYCLE_ABLATION:
            result["training_blocked_reason"] = (
                LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON
            )
        return result


@dataclass(frozen=True, slots=True)
class ResolvedEventGatedAssignmentProfile:
    """Resolved interface-only identity for the future event-gated route."""

    profile_contract_version: str
    profile_name: AssignmentProfileName
    resolution_origin: AssignmentProfileResolutionOrigin
    runtime_route: AssignmentRuntimeRoute
    checkpoint_family: AssignmentCheckpointFamily
    training_support: AssignmentProfileSupport
    playback_support: AssignmentProfileSupport
    runtime_readiness: AssignmentRuntimeReadiness
    event_gated_target_semantics: EventGatedTargetSemantics

    def __post_init__(self) -> None:
        _validate_common_resolved_fields(
            profile_contract_version=self.profile_contract_version,
            profile_name=self.profile_name,
            resolution_origin=self.resolution_origin,
            runtime_route=self.runtime_route,
            checkpoint_family=self.checkpoint_family,
            training_support=self.training_support,
            playback_support=self.playback_support,
            runtime_readiness=self.runtime_readiness,
        )
        if self.profile_name is not AssignmentProfileName.EVENT_GATED_LOCAL_MRTA:
            raise InvalidAssignmentProfileError(
                "existing profile cannot use the event-gated subtype",
                profile=self.profile_name,
                expected=AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
                actual=self.profile_name,
                resolution_origin=self.resolution_origin,
            )
        if type(self.event_gated_target_semantics) is not EventGatedTargetSemantics:
            raise InvalidAssignmentProfileError(
                "event-gated target semantics has noncanonical type identity",
                profile=self.profile_name,
                expected=EventGatedTargetSemantics,
                actual=type(self.event_gated_target_semantics),
                resolution_origin=self.resolution_origin,
            )
        definition = _PROFILE_DEFINITIONS.get(self.profile_name)
        if type(definition) is not _EventProfileDefinition:
            raise AssignmentProfileRouteError(
                "event-gated subtype has no event registry definition",
                profile=self.profile_name,
                expected="event profile definition",
                actual=type(definition),
                resolution_origin=self.resolution_origin,
            )
        if _event_resolved_identity_tuple(self) != _event_definition_identity_tuple(
            definition
        ):
            raise InvalidAssignmentProfileError(
                "event-gated resolved identity differs from the exhaustive registry",
                profile=self.profile_name,
                expected=_event_definition_identity_tuple(definition),
                actual=_event_resolved_identity_tuple(self),
                resolution_origin=self.resolution_origin,
            )


ResolvedAssignmentProfile: TypeAlias = (
    ResolvedExistingAssignmentProfile | ResolvedEventGatedAssignmentProfile
)


@dataclass(frozen=True, slots=True)
class _ExistingProfileDefinition:
    profile_name: AssignmentProfileName
    runtime_route: AssignmentRuntimeRoute
    checkpoint_family: AssignmentCheckpointFamily
    training_support: AssignmentProfileSupport
    playback_support: AssignmentProfileSupport
    runtime_readiness: AssignmentRuntimeReadiness
    resolver_enabled: bool
    lifecycle_observation_enabled: bool
    lifecycle_mask_enabled: bool
    actor_schema_version: str
    shared_schema_version: str
    shared_construction_mode: str
    mask_contract_version: str
    budget_release_contract: str
    legacy_guardrail_profile: str
    policy_sequence_route: str
    training_semantic_contract: TrainingSemanticContract


@dataclass(frozen=True, slots=True)
class _EventProfileDefinition:
    profile_name: AssignmentProfileName
    runtime_route: AssignmentRuntimeRoute
    checkpoint_family: AssignmentCheckpointFamily
    training_support: AssignmentProfileSupport
    playback_support: AssignmentProfileSupport
    runtime_readiness: AssignmentRuntimeReadiness
    event_gated_target_semantics: EventGatedTargetSemantics


_LEGACY_TRAINING_SEMANTICS = TrainingSemanticContract(
    contract_version="legacy_existing_policy_sequence_v1",
    algorithm_name=None,
    state_type=None,
    share_param=None,
    use_recurrent_policy=None,
    use_naive_recurrent_policy=None,
    actor_buffer_generator="resolved_by_legacy_harl_config",
    serialization_mode=None,
    save_entire_model=None,
    installed_harl_mutable=False,
)
_LIFECYCLE_ABLATION_TRAINING_SEMANTICS = TrainingSemanticContract(
    contract_version="lifecycle_ablation_no_training_v1",
    algorithm_name=None,
    state_type=None,
    share_param=None,
    use_recurrent_policy=None,
    use_naive_recurrent_policy=None,
    actor_buffer_generator=None,
    serialization_mode=None,
    save_entire_model=None,
    installed_harl_mutable=False,
)
_LIFECYCLE_CONTRACT_C_TRAINING_SEMANTICS = TrainingSemanticContract(
    contract_version="lifecycle_feed_forward_v1",
    algorithm_name="happo",
    state_type="EP",
    share_param=False,
    use_recurrent_policy=False,
    use_naive_recurrent_policy=False,
    actor_buffer_generator="feed_forward_generator_actor",
    serialization_mode="state_dict",
    save_entire_model=False,
    installed_harl_mutable=False,
)
_DIAGNOSTICS_TRAINING_SEMANTICS = TrainingSemanticContract(
    contract_version="diagnostics_only_no_training_v1",
    algorithm_name=None,
    state_type=None,
    share_param=None,
    use_recurrent_policy=None,
    use_naive_recurrent_policy=None,
    actor_buffer_generator=None,
    serialization_mode=None,
    save_entire_model=None,
    installed_harl_mutable=False,
)
_EVENT_GATED_TRAINING_SEMANTICS = TrainingSemanticContract(
    contract_version="event_gated_happo_ep_feed_forward_v1",
    algorithm_name="happo",
    state_type="EP",
    share_param=False,
    use_recurrent_policy=False,
    use_naive_recurrent_policy=False,
    actor_buffer_generator="feed_forward_generator_actor",
    serialization_mode="state_dict",
    save_entire_model=False,
    installed_harl_mutable=False,
)
_EVENT_GATED_TARGET_SEMANTICS = EventGatedTargetSemantics(
    contract_version=EVENT_GATED_TARGET_SEMANTICS_VERSION,
    actor_schema_version="event_gated_global_actor_observation_v1",
    shared_schema_version="event_gated_global_centralized_observation_v1",
    shared_construction_mode="global_fixed_width_centralized_v1",
    mask_contract_version="event_gated_global_id_local_mask_v1",
    budget_release_contract="authoritative_lifecycle_release_v1",
    policy_sequence_route="event_gated_decision_valid_feed_forward_v1",
    training_semantic_contract=_EVENT_GATED_TRAINING_SEMANTICS,
)


_PROFILE_DEFINITION_ITEMS = (
    (
        AssignmentProfileName.LEGACY,
        _ExistingProfileDefinition(
            profile_name=AssignmentProfileName.LEGACY,
            runtime_route=AssignmentRuntimeRoute.EXISTING_LEGACY_ASSIGNMENT_HARL,
            checkpoint_family=(
                AssignmentCheckpointFamily.ASSIGNMENT_CHECKPOINT_CONTRACT_V2
            ),
            training_support=AssignmentProfileSupport.ALLOWED,
            playback_support=AssignmentProfileSupport.NORMAL,
            runtime_readiness=AssignmentRuntimeReadiness.EXISTING_READY,
            resolver_enabled=False,
            lifecycle_observation_enabled=False,
            lifecycle_mask_enabled=False,
            actor_schema_version="legacy_v1",
            shared_schema_version="legacy_v1_shared_actor_concat",
            shared_construction_mode="actor_concat",
            mask_contract_version="legacy_mask_v1",
            budget_release_contract="disabled",
            legacy_guardrail_profile="legacy_guardrails_v1",
            policy_sequence_route="legacy_existing_policy_sequence_v1",
            training_semantic_contract=_LEGACY_TRAINING_SEMANTICS,
        ),
    ),
    (
        AssignmentProfileName.LIFECYCLE_ABLATION,
        _ExistingProfileDefinition(
            profile_name=AssignmentProfileName.LIFECYCLE_ABLATION,
            runtime_route=(
                AssignmentRuntimeRoute.EXISTING_LIFECYCLE_ABLATION_ASSIGNMENT_HARL
            ),
            checkpoint_family=(
                AssignmentCheckpointFamily
                .ASSIGNMENT_CHECKPOINT_CONTRACT_V2_EXPLICIT_ABLATION_EVALUATION
            ),
            training_support=AssignmentProfileSupport.EXISTING_BLOCKED,
            playback_support=AssignmentProfileSupport.EXPLICIT_ABLATION,
            runtime_readiness=AssignmentRuntimeReadiness.EXISTING_READY,
            resolver_enabled=False,
            lifecycle_observation_enabled=True,
            lifecycle_mask_enabled=False,
            actor_schema_version="lifecycle_v1_actor_3n",
            shared_schema_version="lifecycle_v1_shared_option_a_budget2m",
            shared_construction_mode="actor_concat_plus_critic_budget_2m",
            mask_contract_version="lifecycle_ablation_physical_mask_v1",
            budget_release_contract="disabled",
            legacy_guardrail_profile="lifecycle_no_legacy_guardrails_v1",
            policy_sequence_route="lifecycle_ablation_no_training_v1",
            training_semantic_contract=(
                _LIFECYCLE_ABLATION_TRAINING_SEMANTICS
            ),
        ),
    ),
    (
        AssignmentProfileName.LIFECYCLE_CONTRACT_C,
        _ExistingProfileDefinition(
            profile_name=AssignmentProfileName.LIFECYCLE_CONTRACT_C,
            runtime_route=(
                AssignmentRuntimeRoute.EXISTING_LIFECYCLE_CONTRACT_C_ASSIGNMENT_HARL
            ),
            checkpoint_family=(
                AssignmentCheckpointFamily.ASSIGNMENT_CHECKPOINT_CONTRACT_V2
            ),
            training_support=AssignmentProfileSupport.ALLOWED,
            playback_support=AssignmentProfileSupport.NORMAL,
            runtime_readiness=AssignmentRuntimeReadiness.EXISTING_READY,
            resolver_enabled=True,
            lifecycle_observation_enabled=True,
            lifecycle_mask_enabled=True,
            actor_schema_version="lifecycle_v1_actor_3n",
            shared_schema_version="lifecycle_v1_shared_option_a_budget2m",
            shared_construction_mode="actor_concat_plus_critic_budget_2m",
            mask_contract_version="lifecycle_contract_c_mask_v1",
            budget_release_contract="budget_release_v1",
            legacy_guardrail_profile="lifecycle_no_legacy_guardrails_v1",
            policy_sequence_route="lifecycle_feed_forward_v1",
            training_semantic_contract=(
                _LIFECYCLE_CONTRACT_C_TRAINING_SEMANTICS
            ),
        ),
    ),
    (
        AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
        _ExistingProfileDefinition(
            profile_name=AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
            runtime_route=(
                AssignmentRuntimeRoute
                .EXISTING_DIAGNOSTICS_HIDDEN_STATE_ASSIGNMENT_HARL
            ),
            checkpoint_family=AssignmentCheckpointFamily.NONE,
            training_support=AssignmentProfileSupport.EXISTING_BLOCKED,
            playback_support=AssignmentProfileSupport.DIAGNOSTICS,
            runtime_readiness=AssignmentRuntimeReadiness.EXISTING_READY,
            resolver_enabled=True,
            lifecycle_observation_enabled=False,
            lifecycle_mask_enabled=False,
            actor_schema_version="legacy_v1",
            shared_schema_version="legacy_v1_shared_actor_concat",
            shared_construction_mode="actor_concat",
            mask_contract_version="diagnostics_mask_v1",
            budget_release_contract="diagnostics_only",
            legacy_guardrail_profile="diagnostics_guardrails_v1",
            policy_sequence_route="diagnostics_only_no_training_v1",
            training_semantic_contract=_DIAGNOSTICS_TRAINING_SEMANTICS,
        ),
    ),
    (
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        _EventProfileDefinition(
            profile_name=AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            runtime_route=(
                AssignmentRuntimeRoute.EVENT_GATED_PHASE_A_INTERFACE_ONLY
            ),
            checkpoint_family=(
                AssignmentCheckpointFamily.ASSIGNMENT_CHECKPOINT_CONTRACT_V3
            ),
            training_support=AssignmentProfileSupport.PHASE_A_BLOCKED,
            playback_support=AssignmentProfileSupport.BLOCKED,
            runtime_readiness=AssignmentRuntimeReadiness.INTERFACE_ONLY,
            event_gated_target_semantics=_EVENT_GATED_TARGET_SEMANTICS,
        ),
    ),
)
_PROFILE_DEFINITIONS = MappingProxyType(dict(_PROFILE_DEFINITION_ITEMS))


def _existing_definition_identity_tuple(
    definition: _ExistingProfileDefinition,
) -> tuple[object, ...]:
    return (
        ASSIGNMENT_PROFILE_CONTRACT_VERSION,
        definition.profile_name,
        definition.runtime_route,
        definition.checkpoint_family,
        definition.training_support,
        definition.playback_support,
        definition.runtime_readiness,
        definition.resolver_enabled,
        definition.lifecycle_observation_enabled,
        definition.lifecycle_mask_enabled,
        definition.actor_schema_version,
        definition.shared_schema_version,
        definition.shared_construction_mode,
        definition.mask_contract_version,
        definition.budget_release_contract,
        definition.legacy_guardrail_profile,
        definition.policy_sequence_route,
        definition.training_semantic_contract,
    )


def _existing_resolved_identity_tuple(
    resolved: ResolvedExistingAssignmentProfile,
) -> tuple[object, ...]:
    return (
        resolved.profile_contract_version,
        resolved.profile_name,
        resolved.runtime_route,
        resolved.checkpoint_family,
        resolved.training_support,
        resolved.playback_support,
        resolved.runtime_readiness,
        resolved.resolver_enabled,
        resolved.lifecycle_observation_enabled,
        resolved.lifecycle_mask_enabled,
        resolved.actor_schema_version,
        resolved.shared_schema_version,
        resolved.shared_construction_mode,
        resolved.mask_contract_version,
        resolved.budget_release_contract,
        resolved.legacy_guardrail_profile,
        resolved.policy_sequence_route,
        resolved.training_semantic_contract,
    )


def _event_definition_identity_tuple(
    definition: _EventProfileDefinition,
) -> tuple[object, ...]:
    return (
        ASSIGNMENT_PROFILE_CONTRACT_VERSION,
        definition.profile_name,
        definition.runtime_route,
        definition.checkpoint_family,
        definition.training_support,
        definition.playback_support,
        definition.runtime_readiness,
        definition.event_gated_target_semantics,
    )


def _event_resolved_identity_tuple(
    resolved: ResolvedEventGatedAssignmentProfile,
) -> tuple[object, ...]:
    return (
        resolved.profile_contract_version,
        resolved.profile_name,
        resolved.runtime_route,
        resolved.checkpoint_family,
        resolved.training_support,
        resolved.playback_support,
        resolved.runtime_readiness,
        resolved.event_gated_target_semantics,
    )


def _training_semantics_to_mapping(
    contract: TrainingSemanticContract,
) -> dict[str, object]:
    return {
        "contract_version": contract.contract_version,
        "algorithm_name": contract.algorithm_name,
        "state_type": contract.state_type,
        "share_param": contract.share_param,
        "use_recurrent_policy": contract.use_recurrent_policy,
        "use_naive_recurrent_policy": contract.use_naive_recurrent_policy,
        "actor_buffer_generator": contract.actor_buffer_generator,
        "serialization_mode": contract.serialization_mode,
        "save_entire_model": contract.save_entire_model,
        "installed_harl_mutable": contract.installed_harl_mutable,
    }


def _event_semantics_to_mapping(
    semantics: EventGatedTargetSemantics,
) -> dict[str, object]:
    return {
        "contract_version": semantics.contract_version,
        "actor_schema_version": semantics.actor_schema_version,
        "shared_schema_version": semantics.shared_schema_version,
        "shared_construction_mode": semantics.shared_construction_mode,
        "mask_contract_version": semantics.mask_contract_version,
        "budget_release_contract": semantics.budget_release_contract,
        "policy_sequence_route": semantics.policy_sequence_route,
        "training_semantic_contract": _training_semantics_to_mapping(
            semantics.training_semantic_contract
        ),
    }


def _definition_to_mapping(
    definition: _ExistingProfileDefinition | _EventProfileDefinition,
) -> dict[str, object]:
    result: dict[str, object] = {
        "profile_contract_version": ASSIGNMENT_PROFILE_CONTRACT_VERSION,
        "profile_name": definition.profile_name.value,
        "runtime_route": definition.runtime_route.value,
        "checkpoint_family": definition.checkpoint_family.value,
        "training_support": definition.training_support.value,
        "playback_support": definition.playback_support.value,
        "runtime_readiness": definition.runtime_readiness.value,
    }
    if type(definition) is _ExistingProfileDefinition:
        result.update(
            {
                "resolver_enabled": definition.resolver_enabled,
                "lifecycle_observation_enabled": (
                    definition.lifecycle_observation_enabled
                ),
                "lifecycle_mask_enabled": definition.lifecycle_mask_enabled,
                "actor_schema_version": definition.actor_schema_version,
                "shared_schema_version": definition.shared_schema_version,
                "shared_construction_mode": definition.shared_construction_mode,
                "mask_contract_version": definition.mask_contract_version,
                "budget_release_contract": definition.budget_release_contract,
                "legacy_guardrail_profile": definition.legacy_guardrail_profile,
                "policy_sequence_route": definition.policy_sequence_route,
                "training_semantic_contract": _training_semantics_to_mapping(
                    definition.training_semantic_contract
                ),
            }
        )
        return result
    if type(definition) is _EventProfileDefinition:
        result["event_gated_target_semantics"] = _event_semantics_to_mapping(
            definition.event_gated_target_semantics
        )
        return result
    raise AssignmentProfileRegistryError(
        "registry contains an unsupported definition subtype",
        expected=(_ExistingProfileDefinition, _EventProfileDefinition),
        actual=type(definition),
    )


def _deep_read_only(value: object) -> object:
    if type(value) is dict:
        return MappingProxyType(
            {key: _deep_read_only(item) for key, item in value.items()}
        )
    if type(value) is tuple:
        return tuple(_deep_read_only(item) for item in value)
    return value


_PUBLIC_PROFILE_REGISTRY = MappingProxyType(
    {
        profile_name: _deep_read_only(_definition_to_mapping(definition))
        for profile_name, definition in _PROFILE_DEFINITION_ITEMS
    }
)


def normalize_assignment_profile_name(
    profile: AssignmentProfileName | str,
) -> AssignmentProfileName:
    """Return one exact canonical profile; never lower, alias, or default."""

    if type(profile) is AssignmentProfileName:
        return profile
    if type(profile) is not str:
        raise InvalidAssignmentProfileError(
            "assignment profile must be the canonical enum or an exact string",
            profile=profile,
            expected=(AssignmentProfileName, str),
            actual=type(profile),
        )
    candidate = profile.strip()
    if not candidate:
        raise InvalidAssignmentProfileError(
            "assignment profile must not be empty",
            profile=profile,
            expected=tuple(item.value for item in AssignmentProfileName),
            actual=candidate,
        )
    try:
        return AssignmentProfileName(candidate)
    except ValueError as exc:
        raise UnknownAssignmentProfileError(
            "unknown assignment profile; aliases and case folding are forbidden",
            profile=candidate,
            expected=tuple(item.value for item in AssignmentProfileName),
            actual=candidate,
        ) from exc


def _validate_resolution_origin(
    resolution_origin: AssignmentProfileResolutionOrigin,
    *,
    profile: AssignmentProfileName,
) -> AssignmentProfileResolutionOrigin:
    if type(resolution_origin) is not AssignmentProfileResolutionOrigin:
        raise InvalidAssignmentProfileError(
            "resolution origin must use the canonical enum identity",
            profile=profile,
            expected=AssignmentProfileResolutionOrigin,
            actual=type(resolution_origin),
            resolution_origin=resolution_origin,
        )
    return resolution_origin


def resolve_assignment_profile(
    profile: AssignmentProfileName | str,
    resolution_origin: AssignmentProfileResolutionOrigin,
) -> ResolvedAssignmentProfile:
    """Materialize a fresh immutable resolved identity from the pure registry."""

    profile_name = normalize_assignment_profile_name(profile)
    origin = _validate_resolution_origin(resolution_origin, profile=profile_name)
    definition = _PROFILE_DEFINITIONS.get(profile_name)
    if type(definition) is _ExistingProfileDefinition:
        return ResolvedExistingAssignmentProfile(
            profile_contract_version=ASSIGNMENT_PROFILE_CONTRACT_VERSION,
            profile_name=definition.profile_name,
            resolution_origin=origin,
            runtime_route=definition.runtime_route,
            checkpoint_family=definition.checkpoint_family,
            training_support=definition.training_support,
            playback_support=definition.playback_support,
            runtime_readiness=definition.runtime_readiness,
            resolver_enabled=definition.resolver_enabled,
            lifecycle_observation_enabled=definition.lifecycle_observation_enabled,
            lifecycle_mask_enabled=definition.lifecycle_mask_enabled,
            actor_schema_version=definition.actor_schema_version,
            shared_schema_version=definition.shared_schema_version,
            shared_construction_mode=definition.shared_construction_mode,
            mask_contract_version=definition.mask_contract_version,
            budget_release_contract=definition.budget_release_contract,
            legacy_guardrail_profile=definition.legacy_guardrail_profile,
            policy_sequence_route=definition.policy_sequence_route,
            training_semantic_contract=definition.training_semantic_contract,
        )
    if type(definition) is _EventProfileDefinition:
        return ResolvedEventGatedAssignmentProfile(
            profile_contract_version=ASSIGNMENT_PROFILE_CONTRACT_VERSION,
            profile_name=definition.profile_name,
            resolution_origin=origin,
            runtime_route=definition.runtime_route,
            checkpoint_family=definition.checkpoint_family,
            training_support=definition.training_support,
            playback_support=definition.playback_support,
            runtime_readiness=definition.runtime_readiness,
            event_gated_target_semantics=definition.event_gated_target_semantics,
        )
    raise AssignmentProfileRegistryError(
        "canonical profile has no registered definition",
        profile=profile_name,
        expected=tuple(item.value for item in AssignmentProfileName),
        actual=type(definition),
        resolution_origin=origin,
    )


def get_assignment_profile_registry(
) -> Mapping[AssignmentProfileName, Mapping[str, object]]:
    """Return the deeply read-only origin-independent definition registry.

    ``resolution_origin`` is intentionally absent from this view because it is
    supplied by the caller to :func:`resolve_assignment_profile`.
    """

    return _PUBLIC_PROFILE_REGISTRY


def validate_existing_assignment_profile(
    profile: ResolvedAssignmentProfile,
) -> ResolvedExistingAssignmentProfile:
    """Require the strict existing subtype before any legacy boolean consumer."""

    if type(profile) is not ResolvedExistingAssignmentProfile:
        raise AssignmentProfileRouteError(
            "legacy wrapper mapping accepts only the canonical existing subtype",
            profile=getattr(profile, "profile_name", None),
            expected=ResolvedExistingAssignmentProfile,
            actual=type(profile),
            resolution_origin=getattr(profile, "resolution_origin", None),
        )
    return profile


def resolve_or_validate_assignment_profile_authority(
    *,
    raw_profile: AssignmentProfileName | str | None,
    raw_profile_present: bool,
    resolved_assignment_profile: ResolvedAssignmentProfile | None,
    expected_origin: AssignmentProfileResolutionOrigin,
    allow_direct_fallback: bool,
    consumer: str,
    entrypoint: str,
) -> ResolvedAssignmentProfile:
    """Resolve only an explicit direct fallback, otherwise validate by identity.

    Formal entrypoints own the sole final resolution and pass that same object
    through every consumer.  A direct/fake wrapper surface may opt into the
    narrow fallback by setting ``allow_direct_fallback=True`` and using the
    canonical ``DIRECT_WRAPPER_FALLBACK`` origin.
    """

    _require_nonempty_string(consumer, field="authority.consumer")
    _require_nonempty_string(entrypoint, field="authority.entrypoint")
    if type(raw_profile_present) is not bool:
        raise ResolvedProfileMismatchError(
            "raw_profile_present must be an exact bool",
            profile=raw_profile,
            expected="bool",
            actual=type(raw_profile_present),
            resolution_origin=expected_origin,
        )
    if type(allow_direct_fallback) is not bool:
        raise ResolvedProfileMismatchError(
            "allow_direct_fallback must be an exact bool",
            profile=raw_profile,
            expected="bool",
            actual=type(allow_direct_fallback),
            resolution_origin=expected_origin,
        )
    if type(expected_origin) is not AssignmentProfileResolutionOrigin:
        raise ResolvedProfileMismatchError(
            "caller authority uses a noncanonical resolution-origin identity",
            profile=raw_profile,
            expected=AssignmentProfileResolutionOrigin,
            actual=type(expected_origin),
            resolution_origin=expected_origin,
        )
    if allow_direct_fallback and (
        expected_origin
        is not AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK
    ):
        raise ResolvedProfileMismatchError(
            "formal authority cannot enable the direct-wrapper fallback",
            profile=raw_profile,
            expected=AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK,
            actual=expected_origin,
            resolution_origin=expected_origin,
        )

    raw_profile_name = (
        normalize_assignment_profile_name(raw_profile)
        if raw_profile_present
        else AssignmentProfileName.LEGACY
    )
    if resolved_assignment_profile is None:
        if not allow_direct_fallback:
            raise ResolvedProfileMismatchError(
                "formal caller omitted the required resolved assignment profile; "
                f"consumer={consumer!r}; entrypoint={entrypoint!r}",
                profile=raw_profile_name,
                expected=expected_origin,
                actual="missing resolved assignment profile and origin",
                resolution_origin=expected_origin,
            )
        resolved_assignment_profile = resolve_assignment_profile(
            raw_profile_name,
            AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK,
        )
    elif type(resolved_assignment_profile) not in (
        ResolvedExistingAssignmentProfile,
        ResolvedEventGatedAssignmentProfile,
    ):
        raise ResolvedProfileMismatchError(
            "resolved assignment profile has a noncanonical class/module identity; "
            f"consumer={consumer!r}; entrypoint={entrypoint!r}",
            profile=getattr(resolved_assignment_profile, "profile_name", raw_profile_name),
            expected=(
                ResolvedExistingAssignmentProfile,
                ResolvedEventGatedAssignmentProfile,
            ),
            actual=type(resolved_assignment_profile),
            resolution_origin=getattr(
                resolved_assignment_profile,
                "resolution_origin",
                None,
            ),
        )

    if resolved_assignment_profile.resolution_origin is not expected_origin:
        raise ResolvedProfileMismatchError(
            "resolved assignment profile origin differs from caller authority; "
            f"consumer={consumer!r}; entrypoint={entrypoint!r}",
            profile=resolved_assignment_profile.profile_name,
            expected=expected_origin,
            actual=resolved_assignment_profile.resolution_origin,
            resolution_origin=resolved_assignment_profile.resolution_origin,
        )
    if resolved_assignment_profile.profile_name is not raw_profile_name:
        raise ResolvedProfileMismatchError(
            "raw assignment profile differs from the resolved identity; "
            f"consumer={consumer!r}; entrypoint={entrypoint!r}",
            profile=raw_profile_name,
            expected=raw_profile_name,
            actual=resolved_assignment_profile.profile_name,
            resolution_origin=resolved_assignment_profile.resolution_origin,
        )
    return resolved_assignment_profile


def require_assignment_profile_runtime_ready(
    profile: ResolvedAssignmentProfile,
    *,
    consumer: str,
    entrypoint: str,
    current_phase: str = "Phase A1c",
    barrier: str,
) -> ResolvedExistingAssignmentProfile:
    """Return an existing profile or fail before an event runtime consumer."""

    _require_nonempty_string(consumer, field="readiness.consumer")
    _require_nonempty_string(entrypoint, field="readiness.entrypoint")
    _require_nonempty_string(current_phase, field="readiness.current_phase")
    _require_nonempty_string(barrier, field="readiness.barrier")
    if type(profile) is ResolvedExistingAssignmentProfile:
        return profile
    if type(profile) is ResolvedEventGatedAssignmentProfile:
        raise PhaseAExecutionNotAuthorizedError(
            "event-gated assignment runtime is not authorized; "
            f"runtime_route={profile.runtime_route.value!r}; "
            f"runtime_readiness={profile.runtime_readiness.value!r}; "
            f"current_phase={current_phase!r}; "
            f"blocked_consumer={consumer!r}; "
            f"entrypoint={entrypoint!r}; barrier={barrier!r}",
            profile=profile.profile_name,
            expected="existing-ready assignment profile",
            actual=profile.runtime_readiness,
            resolution_origin=profile.resolution_origin,
        )
    raise AssignmentProfileRouteError(
        "runtime readiness requires a canonical resolved-profile subtype; "
        f"consumer={consumer!r}; entrypoint={entrypoint!r}; barrier={barrier!r}",
        profile=getattr(profile, "profile_name", None),
        expected=(
            ResolvedExistingAssignmentProfile,
            ResolvedEventGatedAssignmentProfile,
        ),
        actual=type(profile),
        resolution_origin=getattr(profile, "resolution_origin", None),
    )


def resolved_assignment_profile_to_mapping(
    profile: ResolvedAssignmentProfile,
) -> dict[str, object]:
    """Serialize one resolved identity to a deterministic primitive mapping."""

    if type(profile) not in (
        ResolvedExistingAssignmentProfile,
        ResolvedEventGatedAssignmentProfile,
    ):
        raise AssignmentProfileRouteError(
            "resolved profile serialization requires a canonical resolved subtype",
            profile=getattr(profile, "profile_name", None),
            expected=(
                ResolvedExistingAssignmentProfile,
                ResolvedEventGatedAssignmentProfile,
            ),
            actual=type(profile),
            resolution_origin=getattr(profile, "resolution_origin", None),
        )
    result: dict[str, object] = {
        "profile_contract_version": profile.profile_contract_version,
        "profile_name": profile.profile_name.value,
        "resolution_origin": profile.resolution_origin.value,
        "runtime_route": profile.runtime_route.value,
        "checkpoint_family": profile.checkpoint_family.value,
        "training_support": profile.training_support.value,
        "playback_support": profile.playback_support.value,
        "runtime_readiness": profile.runtime_readiness.value,
    }
    if type(profile) is ResolvedExistingAssignmentProfile:
        result.update(
            {
                "resolver_enabled": profile.resolver_enabled,
                "lifecycle_observation_enabled": (
                    profile.lifecycle_observation_enabled
                ),
                "lifecycle_mask_enabled": profile.lifecycle_mask_enabled,
                "actor_schema_version": profile.actor_schema_version,
                "shared_schema_version": profile.shared_schema_version,
                "shared_construction_mode": profile.shared_construction_mode,
                "mask_contract_version": profile.mask_contract_version,
                "budget_release_contract": profile.budget_release_contract,
                "legacy_guardrail_profile": profile.legacy_guardrail_profile,
                "policy_sequence_route": profile.policy_sequence_route,
                "training_semantic_contract": _training_semantics_to_mapping(
                    profile.training_semantic_contract
                ),
            }
        )
        return result
    result["event_gated_target_semantics"] = _event_semantics_to_mapping(
        profile.event_gated_target_semantics
    )
    return result


def validate_canonical_module_identity() -> None:
    """Validate canonical identity after the pre-declaration guard has passed."""

    if __name__ != CANONICAL_ASSIGNMENT_PROFILE_MODULE:
        raise CanonicalModuleIdentityError(
            "assignment profile module key changed after canonical import",
            expected=CANONICAL_ASSIGNMENT_PROFILE_MODULE,
            actual=__name__,
        )
    identity_types = (
        AssignmentProfileName,
        AssignmentRuntimeRoute,
        AssignmentCheckpointFamily,
        AssignmentProfileSupport,
        AssignmentRuntimeReadiness,
        AssignmentProfileResolutionOrigin,
        TrainingSemanticContract,
        EventGatedTargetSemantics,
        ResolvedExistingAssignmentProfile,
        ResolvedEventGatedAssignmentProfile,
        AssignmentProfileContractError,
        ProfileResolutionError,
        UnknownAssignmentProfileError,
        InvalidAssignmentProfileError,
        AssignmentProfileRegistryError,
        AssignmentProfileRouteError,
        ResolvedProfileMismatchError,
        PhaseAExecutionNotAuthorizedError,
        CanonicalModuleIdentityError,
    )
    invalid = tuple(
        identity_type.__qualname__
        for identity_type in identity_types
        if identity_type.__module__ != CANONICAL_ASSIGNMENT_PROFILE_MODULE
    )
    if invalid:
        raise CanonicalModuleIdentityError(
            "public identity-bearing types have noncanonical __module__ values",
            expected=CANONICAL_ASSIGNMENT_PROFILE_MODULE,
            actual=invalid,
        )


def validate_assignment_profile_registry() -> None:
    """Fail closed unless the five-profile registry is exact and exhaustive."""

    validate_canonical_module_identity()
    expected_names = tuple(AssignmentProfileName)
    actual_names = tuple(_PROFILE_DEFINITIONS)
    if actual_names != expected_names:
        raise AssignmentProfileRegistryError(
            "profile registry keys/order differ from canonical enum order",
            expected=expected_names,
            actual=actual_names,
        )
    if len(_PROFILE_DEFINITION_ITEMS) != len(set(actual_names)):
        raise AssignmentProfileRegistryError(
            "profile registry contains duplicate profile keys",
            expected=len(expected_names),
            actual=len(set(actual_names)),
        )
    if tuple(_PUBLIC_PROFILE_REGISTRY) != expected_names:
        raise AssignmentProfileRegistryError(
            "public immutable registry keys/order differ from definitions",
            expected=expected_names,
            actual=tuple(_PUBLIC_PROFILE_REGISTRY),
        )
    for profile_name, definition in _PROFILE_DEFINITION_ITEMS:
        if definition.profile_name is not profile_name:
            raise AssignmentProfileRegistryError(
                "profile definition discriminant differs from its registry key",
                profile=profile_name,
                expected=profile_name,
                actual=definition.profile_name,
            )
        public_mapping = _PUBLIC_PROFILE_REGISTRY[profile_name]
        if dict(public_mapping) != _definition_to_mapping(definition):
            raise AssignmentProfileRegistryError(
                "public registry mapping differs from its immutable definition",
                profile=profile_name,
                expected=_definition_to_mapping(definition),
                actual=dict(public_mapping),
            )
        for origin in AssignmentProfileResolutionOrigin:
            first = resolve_assignment_profile(profile_name, origin)
            second = resolve_assignment_profile(profile_name, origin)
            if first != second or first is second:
                raise AssignmentProfileRegistryError(
                    "profile resolution must return equal independent values",
                    profile=profile_name,
                    expected="value-equal independent frozen objects",
                    actual=(first == second, first is second),
                    resolution_origin=origin,
                )
            if profile_name is AssignmentProfileName.EVENT_GATED_LOCAL_MRTA:
                if type(first) is not ResolvedEventGatedAssignmentProfile:
                    raise AssignmentProfileRegistryError(
                        "event profile resolved to the wrong subtype",
                        profile=profile_name,
                        expected=ResolvedEventGatedAssignmentProfile,
                        actual=type(first),
                        resolution_origin=origin,
                    )
            elif type(first) is not ResolvedExistingAssignmentProfile:
                raise AssignmentProfileRegistryError(
                    "existing profile resolved to the wrong subtype",
                    profile=profile_name,
                    expected=ResolvedExistingAssignmentProfile,
                    actual=type(first),
                    resolution_origin=origin,
                )
            serialized = resolved_assignment_profile_to_mapping(first)
            expected_serialized = dict(_definition_to_mapping(definition))
            expected_serialized["resolution_origin"] = origin.value
            ordered_expected = {
                "profile_contract_version": expected_serialized.pop(
                    "profile_contract_version"
                ),
                "profile_name": expected_serialized.pop("profile_name"),
                "resolution_origin": expected_serialized.pop("resolution_origin"),
                **expected_serialized,
            }
            if serialized != ordered_expected:
                raise AssignmentProfileRegistryError(
                    "resolved canonical mapping differs from registry definition",
                    profile=profile_name,
                    expected=ordered_expected,
                    actual=serialized,
                    resolution_origin=origin,
                )


__all__ = [
    "ASSIGNMENT_PROFILE_CONTRACT_VERSION",
    "ASSIGNMENT_PROFILE_SOURCE_PURPOSE",
    "CANONICAL_ASSIGNMENT_PROFILE_MODULE",
    "EVENT_GATED_TARGET_SEMANTICS_VERSION",
    "LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON",
    "AssignmentCheckpointFamily",
    "AssignmentProfileContractError",
    "AssignmentProfileName",
    "AssignmentProfileRegistryError",
    "AssignmentProfileResolutionOrigin",
    "AssignmentProfileRouteError",
    "AssignmentProfileSupport",
    "AssignmentRuntimeReadiness",
    "AssignmentRuntimeRoute",
    "CanonicalModuleIdentityError",
    "EventGatedTargetSemantics",
    "InvalidAssignmentProfileError",
    "PhaseAExecutionNotAuthorizedError",
    "ProfileResolutionError",
    "ResolvedProfileMismatchError",
    "ResolvedAssignmentProfile",
    "ResolvedEventGatedAssignmentProfile",
    "ResolvedExistingAssignmentProfile",
    "TrainingSemanticContract",
    "UnknownAssignmentProfileError",
    "get_assignment_profile_registry",
    "normalize_assignment_profile_name",
    "require_assignment_profile_runtime_ready",
    "resolve_assignment_profile",
    "resolve_or_validate_assignment_profile_authority",
    "resolved_assignment_profile_to_mapping",
    "validate_assignment_profile_registry",
    "validate_canonical_module_identity",
    "validate_existing_assignment_profile",
]


validate_assignment_profile_registry()
