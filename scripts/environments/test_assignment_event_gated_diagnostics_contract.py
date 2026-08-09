"""Pure regressions for the Phase A3/A5 diagnostics semantic contract."""

from __future__ import annotations

import argparse
import ast
from dataclasses import fields, is_dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Mapping, get_args


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
    "assignment_profile_contract": (
        TASK_SOURCE / "assignment_profile_contract.py"
    ),
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
    "assignment_event_gated_diagnostics_contract": (
        TASK_SOURCE / "assignment_event_gated_diagnostics_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_team_reward_contract": (
        TASK_SOURCE / "assignment_team_reward_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract": (
        TASK_SOURCE / "assignment_event_profile_schema_contract.py"
    ),
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_contract_v3": (
        TASK_SOURCE / "assignment_checkpoint_contract_v3.py"
    ),
}
CANONICAL_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_gated_diagnostics_contract"
)
TEAM_REWARD_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_team_reward_contract"
)
EVENT_PROFILE_SCHEMA_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_profile_schema_contract"
)
CHECKPOINT_V3_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_checkpoint_contract_v3"
)
CHILD_MODULE_KEYS = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_profile_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_mrta_contract",
    CANONICAL_MODULE,
    TEAM_REWARD_MODULE,
)

EXPECTED_ENVELOPE_FIELD_ORDER = (
    "schema_version",
    "kind",
    "resolved_profile",
    "env_id",
    "episode_generation",
    "transition_generation",
    "assignment_tick_generation",
    "availability",
    "payload",
)
EXPECTED_ENVELOPE_SCHEMA_VERSION = "event_gated_diagnostic_envelope_v1"
EXPECTED_V3_DIAGNOSTICS_FIELD_ORDER = (
    "contract_version",
    "schema_version",
    "diagnostic_availability_order",
    "diagnostic_kind_order",
    "transition_consume_status_order",
    "default_off_cohort_order",
    "envelope_field_order",
    "payload_type_by_kind",
    "availability_rules",
    "serialization",
)
EXPECTED_V3_INTERFACE_BYTE_LENGTH = 67794
EXPECTED_V3_INTERFACE_SHA256 = (
    "03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a"
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
PROFILE = MODULES[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract"
]
TRANSITION = MODULES[
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
]
EVENT = MODULES[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract"
]
MRTA = MODULES[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract"
]
TEAM_REWARD = MODULES[TEAM_REWARD_MODULE]
EVENT_PROFILE_SCHEMA = MODULES[EVENT_PROFILE_SCHEMA_MODULE]
CHECKPOINT_V3 = MODULES[CHECKPOINT_V3_MODULE]


def _profile_payload() -> Any:
    return MODULE.ProfileRouteDiagnostic(
        profile_contract_version="assignment_resolved_profile_v1",
        resolved_variant="event_gated",
        runtime_route="event_gated_phase_a_interface_only_v1",
        checkpoint_family="assignment_checkpoint_contract_v3",
        runtime_readiness="interface_only",
        resolution_origin="formal_entrypoint",
        event_target_semantics_contract_version=(
            "event_gated_target_semantics_v1"
        ),
    )


def _authority_payload() -> Any:
    return MODULE.TransitionAuthorityDiagnostic(
        facts_schema_version="execution_transition_facts_v1",
        result_schema_version="lifecycle_transition_result_v1",
        facts_producer_id="env_execution_facts_producer_v1",
        lifecycle_authority_id="lifecycle_authority_v1",
        consume_token=7,
        receipt_id=8,
        consume_status=MODULE.TransitionConsumeStatus.FIRST_CONSUME,
        generation_match=True,
        facts_producer_match=True,
        lifecycle_authority_match=True,
        pair_attribution_contract_version=(
            "pair_attributed_execution_signals_v1"
        ),
        pair_attribution_validated=True,
        observable_immutability_contract_version=(
            "assignment_tensor_alias_isolation_v1"
        ),
    )


def _tick_payload() -> Any:
    return MODULE.AssignmentTickDiagnostic(
        assignment_tick_count=1,
        lifecycle_event_ids=("0:3:4:0",),
        lifecycle_causal_sources=(
            EVENT.LifecycleCausalSource.EXECUTION_FACTS,
        ),
        assignment_opportunity_ids=("0:3:4:5:0",),
        assignment_opportunity_types=(
            EVENT.AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE,
        ),
        trigger_eligible_count=2,
        resolver_diagnostic_count=1,
        suppressed_resolver_diagnostic_trigger_count=1,
        local_robot_count=2,
        local_task_count=3,
        per_robot_decision_count=(1, 0),
        decision_valid_count=1,
        policy_proposal_count_by_kind=(1, 0, 0, 0),
        forced_storage_row_count=1,
        accepted_component_count=1,
        rejected_component_count=0,
        ownership_transfer_count=1,
        needs_assignment_duration=(2, 0),
        idle_with_available_task_count=0,
        failed_pair_count=1,
        team_infeasible_task_count=0,
        termination_reason=TRANSITION.TerminationReason.NONE,
        expected_robot_count=2,
    )


def _proposal_payload(
    row: str = "policy_accepted",
) -> Any:
    common = {
        "robot_id": 0,
        "component_id": "",
        "component_size": 0,
        "ownership_transfer_count": 0,
        "local_cost_before": 2.0,
        "local_cost_after": 2.0,
    }
    if row == "policy_accepted":
        return MODULE.ProposalResolutionDiagnostic(
            **common,
            storage_row_present=True,
            policy_proposal_present=True,
            forced_nondecision=False,
            decision_valid=True,
            stored_row_kind=MRTA.StoredActionRowKind.POLICY_PROPOSAL,
            proposal_kind=MRTA.ProposalKind.CLAIM,
            stored_action_id=1,
            proposed_task_id=1,
            effective_assignment=1,
            proposal_accepted=True,
            proposal_effective_mismatch=False,
            rejection_reason=MRTA.ComponentRejectionReason.NONE,
            policy_caused=False,
            penalty_eligible=False,
        )
    if row == "policy_rejected":
        return MODULE.ProposalResolutionDiagnostic(
            **common,
            storage_row_present=True,
            policy_proposal_present=True,
            forced_nondecision=False,
            decision_valid=True,
            stored_row_kind=MRTA.StoredActionRowKind.POLICY_PROPOSAL,
            proposal_kind=MRTA.ProposalKind.SWITCH,
            stored_action_id=2,
            proposed_task_id=2,
            effective_assignment=0,
            proposal_accepted=False,
            proposal_effective_mismatch=True,
            rejection_reason=(
                MRTA.ComponentRejectionReason.CONTENTION_LOSS
            ),
            policy_caused=True,
            penalty_eligible=True,
        )
    if row == "policy_noop":
        return MODULE.ProposalResolutionDiagnostic(
            **common,
            storage_row_present=True,
            policy_proposal_present=True,
            forced_nondecision=False,
            decision_valid=True,
            stored_row_kind=MRTA.StoredActionRowKind.POLICY_PROPOSAL,
            proposal_kind=MRTA.ProposalKind.NOOP_IDLE,
            stored_action_id=50,
            proposed_task_id=-1,
            effective_assignment=-1,
            proposal_accepted=True,
            proposal_effective_mismatch=False,
            rejection_reason=MRTA.ComponentRejectionReason.NONE,
            policy_caused=False,
            penalty_eligible=False,
        )
    if row == "forced":
        return MODULE.ProposalResolutionDiagnostic(
            **common,
            storage_row_present=True,
            policy_proposal_present=False,
            forced_nondecision=True,
            decision_valid=False,
            stored_row_kind=MRTA.StoredActionRowKind.FORCED_NONDECISION,
            proposal_kind=None,
            stored_action_id=0,
            proposed_task_id=-1,
            effective_assignment=0,
            proposal_accepted=None,
            proposal_effective_mismatch=None,
            rejection_reason=MRTA.ComponentRejectionReason.NONE,
            policy_caused=False,
            penalty_eligible=False,
        )
    if row == "no_row":
        return MODULE.ProposalResolutionDiagnostic(
            **common,
            storage_row_present=False,
            policy_proposal_present=False,
            forced_nondecision=False,
            decision_valid=False,
            stored_row_kind=MRTA.StoredActionRowKind.NO_ROW,
            proposal_kind=None,
            stored_action_id=-1,
            proposed_task_id=-1,
            effective_assignment=-1,
            proposal_accepted=None,
            proposal_effective_mismatch=None,
            rejection_reason=MRTA.ComponentRejectionReason.NONE,
            policy_caused=False,
            penalty_eligible=False,
        )
    raise AssertionError(f"unknown row fixture: {row}")


def _actor_payload() -> Any:
    return MODULE.ActorUpdateDiagnostic(
        actor_id=0,
        decision_valid_sample_count=3,
        skipped_actor_update_count=0,
        skipped_minibatch_count=1,
        singleton_advantage_fallback_count=0,
        nondecision_factor_identity_violation_count=0,
        reduction_denominator=3,
    )


def _reward_payload() -> Any:
    return MODULE.TeamRewardDiagnostic(
        wrapper_final_reward_mean=2.0,
        policy_rejected_component_count=1,
        rejection_penalty_scale=0.25,
        team_reward=1.75,
        broadcast_agent_count=2,
        broadcast_equal=True,
    )


def _checkpoint_payload() -> Any:
    return MODULE.CheckpointSemanticDiagnostic(
        manifest_format_version="assignment_checkpoint_contract_v3",
        manifest_kind="interface_semantic_descriptor",
        profile_name="event_gated_local_mrta",
        checkpoint_family="assignment_checkpoint_contract_v3",
        fingerprint_sha256="a" * 64,
        purpose="phase_a_interface",
        compatibility_classification="runtime_not_ready",
        runtime_readiness="interface_only",
    )


def _default_off_payload() -> Any:
    return MODULE.DefaultOffIdentityDiagnostic(
        cohort=MODULE.DefaultOffCohort.D0_ABSENT,
        surface="resolved_profile",
        evidence_label="pure_identity",
        expected_digest="a" * 64,
        actual_digest="a" * 64,
        matched=True,
        deferred_reason=None,
    )


PAYLOADS = {
    MODULE.DiagnosticKind.PROFILE_ROUTE: _profile_payload,
    MODULE.DiagnosticKind.TRANSITION_AUTHORITY: _authority_payload,
    MODULE.DiagnosticKind.ASSIGNMENT_TICK: _tick_payload,
    MODULE.DiagnosticKind.PROPOSAL_RESOLUTION: _proposal_payload,
    MODULE.DiagnosticKind.ACTOR_UPDATE: _actor_payload,
    MODULE.DiagnosticKind.TEAM_REWARD: _reward_payload,
    MODULE.DiagnosticKind.CHECKPOINT_SEMANTIC: _checkpoint_payload,
    MODULE.DiagnosticKind.DEFAULT_OFF_IDENTITY: _default_off_payload,
}

# Literal Phase A plan section 15.2 authority.  Do not derive this inventory
# from the production descriptor or dataclass fields: a matching drift in both
# implementation and descriptor must still fail this independent regression.
AUTHORITATIVE_PAYLOAD_FIELD_ORDER = {
    MODULE.DiagnosticKind.PROFILE_ROUTE: (
        "profile_contract_version",
        "resolved_variant",
        "runtime_route",
        "checkpoint_family",
        "runtime_readiness",
        "resolution_origin",
        "event_target_semantics_contract_version",
    ),
    MODULE.DiagnosticKind.TRANSITION_AUTHORITY: (
        "facts_schema_version",
        "result_schema_version",
        "facts_producer_id",
        "lifecycle_authority_id",
        "consume_token",
        "receipt_id",
        "consume_status",
        "generation_match",
        "facts_producer_match",
        "lifecycle_authority_match",
        "pair_attribution_contract_version",
        "pair_attribution_validated",
        "observable_immutability_contract_version",
    ),
    MODULE.DiagnosticKind.ASSIGNMENT_TICK: (
        "assignment_tick_count",
        "lifecycle_event_ids",
        "lifecycle_causal_sources",
        "assignment_opportunity_ids",
        "assignment_opportunity_types",
        "trigger_eligible_count",
        "resolver_diagnostic_count",
        "suppressed_resolver_diagnostic_trigger_count",
        "local_robot_count",
        "local_task_count",
        "per_robot_decision_count",
        "decision_valid_count",
        "policy_proposal_count_by_kind",
        "forced_storage_row_count",
        "accepted_component_count",
        "rejected_component_count",
        "ownership_transfer_count",
        "needs_assignment_duration",
        "idle_with_available_task_count",
        "failed_pair_count",
        "team_infeasible_task_count",
        "termination_reason",
    ),
    MODULE.DiagnosticKind.PROPOSAL_RESOLUTION: (
        "robot_id",
        "storage_row_present",
        "policy_proposal_present",
        "forced_nondecision",
        "decision_valid",
        "stored_row_kind",
        "proposal_kind",
        "stored_action_id",
        "proposed_task_id",
        "effective_assignment",
        "proposal_accepted",
        "proposal_effective_mismatch",
        "component_id",
        "component_size",
        "rejection_reason",
        "policy_caused",
        "penalty_eligible",
        "ownership_transfer_count",
        "local_cost_before",
        "local_cost_after",
    ),
    MODULE.DiagnosticKind.ACTOR_UPDATE: (
        "actor_id",
        "decision_valid_sample_count",
        "skipped_actor_update_count",
        "skipped_minibatch_count",
        "singleton_advantage_fallback_count",
        "nondecision_factor_identity_violation_count",
        "reduction_denominator",
    ),
    MODULE.DiagnosticKind.TEAM_REWARD: (
        "wrapper_final_reward_mean",
        "policy_rejected_component_count",
        "rejection_penalty_scale",
        "team_reward",
        "broadcast_agent_count",
        "broadcast_equal",
    ),
    MODULE.DiagnosticKind.CHECKPOINT_SEMANTIC: (
        "manifest_format_version",
        "manifest_kind",
        "profile_name",
        "checkpoint_family",
        "fingerprint_sha256",
        "purpose",
        "compatibility_classification",
        "runtime_readiness",
    ),
    MODULE.DiagnosticKind.DEFAULT_OFF_IDENTITY: (
        "cohort",
        "surface",
        "evidence_label",
        "expected_digest",
        "actual_digest",
        "matched",
        "deferred_reason",
    ),
}

AUTHORITATIVE_PAYLOAD_CLASS_NAMES = (
    "ProfileRouteDiagnostic",
    "TransitionAuthorityDiagnostic",
    "AssignmentTickDiagnostic",
    "ProposalResolutionDiagnostic",
    "ActorUpdateDiagnostic",
    "TeamRewardDiagnostic",
    "CheckpointSemanticDiagnostic",
    "DefaultOffIdentityDiagnostic",
)
PHASE_A_STATIC_EVIDENCE_KINDS = (
    MODULE.DiagnosticKind.PROFILE_ROUTE,
    MODULE.DiagnosticKind.CHECKPOINT_SEMANTIC,
    MODULE.DiagnosticKind.DEFAULT_OFF_IDENTITY,
)
PHASE_A_DEFINED_NOT_PRODUCED_KINDS = (
    MODULE.DiagnosticKind.TRANSITION_AUTHORITY,
    MODULE.DiagnosticKind.ASSIGNMENT_TICK,
    MODULE.DiagnosticKind.PROPOSAL_RESOLUTION,
    MODULE.DiagnosticKind.ACTOR_UPDATE,
    MODULE.DiagnosticKind.TEAM_REWARD,
)


def _fabricated_unproduced_payload(kind: Any) -> Any:
    if kind is MODULE.DiagnosticKind.TRANSITION_AUTHORITY:
        return MODULE.TransitionAuthorityDiagnostic(
            facts_schema_version="fabricated_facts_v1",
            result_schema_version="fabricated_result_v1",
            facts_producer_id="fabricated_producer",
            lifecycle_authority_id="fabricated_authority",
            consume_token=0,
            receipt_id=0,
            consume_status=MODULE.TransitionConsumeStatus.FIRST_CONSUME,
            generation_match=False,
            facts_producer_match=False,
            lifecycle_authority_match=False,
            pair_attribution_contract_version="fabricated_pair_v1",
            pair_attribution_validated=False,
            observable_immutability_contract_version="fabricated_alias_v1",
        )
    if kind is MODULE.DiagnosticKind.ASSIGNMENT_TICK:
        return MODULE.AssignmentTickDiagnostic(
            assignment_tick_count=0,
            lifecycle_event_ids=(),
            lifecycle_causal_sources=(),
            assignment_opportunity_ids=(),
            assignment_opportunity_types=(),
            trigger_eligible_count=0,
            resolver_diagnostic_count=0,
            suppressed_resolver_diagnostic_trigger_count=0,
            local_robot_count=0,
            local_task_count=0,
            per_robot_decision_count=(0, 0),
            decision_valid_count=0,
            policy_proposal_count_by_kind=(0, 0, 0, 0),
            forced_storage_row_count=0,
            accepted_component_count=0,
            rejected_component_count=0,
            ownership_transfer_count=0,
            needs_assignment_duration=(0, 0),
            idle_with_available_task_count=0,
            failed_pair_count=0,
            team_infeasible_task_count=0,
            termination_reason=TRANSITION.TerminationReason.NONE,
            expected_robot_count=2,
        )
    if kind is MODULE.DiagnosticKind.PROPOSAL_RESOLUTION:
        return MODULE.ProposalResolutionDiagnostic(
            robot_id=0,
            storage_row_present=False,
            policy_proposal_present=False,
            forced_nondecision=False,
            decision_valid=False,
            stored_row_kind=MRTA.StoredActionRowKind.NO_ROW,
            proposal_kind=None,
            stored_action_id=-1,
            proposed_task_id=-1,
            effective_assignment=-1,
            proposal_accepted=None,
            proposal_effective_mismatch=None,
            component_id="",
            component_size=0,
            rejection_reason=MRTA.ComponentRejectionReason.NONE,
            policy_caused=False,
            penalty_eligible=False,
            ownership_transfer_count=0,
            local_cost_before=0.0,
            local_cost_after=0.0,
        )
    if kind is MODULE.DiagnosticKind.ACTOR_UPDATE:
        return MODULE.ActorUpdateDiagnostic(
            actor_id=0,
            decision_valid_sample_count=0,
            skipped_actor_update_count=0,
            skipped_minibatch_count=0,
            singleton_advantage_fallback_count=0,
            nondecision_factor_identity_violation_count=0,
            reduction_denominator=0,
        )
    if kind is MODULE.DiagnosticKind.TEAM_REWARD:
        return MODULE.TeamRewardDiagnostic(
            wrapper_final_reward_mean=0.0,
            policy_rejected_component_count=0,
            rejection_penalty_scale=0.0,
            team_reward=0.0,
            broadcast_agent_count=1,
            broadcast_equal=False,
        )
    raise AssertionError(f"no fabricated unproduced fixture for {kind!r}")


def _expect_python_error(
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


def _payload_constructor_kwargs(payload: Any) -> dict[str, Any]:
    result = {
        field_name: getattr(payload, field_name)
        for field_name in payload.to_mapping()
    }
    if type(payload) is MODULE.AssignmentTickDiagnostic:
        result["expected_robot_count"] = len(
            payload.per_robot_decision_count
        )
    return result


def _semantic_content(value: object) -> object:
    if isinstance(value, Mapping):
        return (
            "mapping",
            tuple(
                (str(key), _semantic_content(item))
                for key, item in value.items()
            ),
        )
    if type(value) is tuple:
        return ("tuple", tuple(_semantic_content(item) for item in value))
    if type(value) is list:
        return ("list", tuple(_semantic_content(item) for item in value))
    return (type(value).__qualname__, value)


def _recursive_mapping_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value) + tuple(
            key
            for item in value.values()
            for key in _recursive_mapping_keys(item)
        )
    if type(value) in (tuple, list):
        return tuple(
            key for item in value for key in _recursive_mapping_keys(item)
        )
    return ()


def _envelope(kind: Any, payload: Any) -> Any:
    tick = (
        5
        if kind
        in (
            MODULE.DiagnosticKind.ASSIGNMENT_TICK,
            MODULE.DiagnosticKind.PROPOSAL_RESOLUTION,
        )
        else -1
    )
    return MODULE.DiagnosticEnvelope(
        kind=kind,
        resolved_profile=PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        env_id=0,
        episode_generation=3,
        transition_generation=4,
        assignment_tick_generation=tick,
        availability=MODULE.DiagnosticAvailability.PRODUCED,
        payload=payload,
    )


def _assert_primitive_immutable(value: object) -> None:
    if isinstance(value, Mapping):
        _assert(
            isinstance(value, MappingProxyType),
            "serialized mapping is not read-only",
        )
        for key, item in value.items():
            _assert(type(key) is str, "serialized mapping key is not str")
            _assert_primitive_immutable(item)
        return
    if type(value) is tuple:
        for item in value:
            _assert_primitive_immutable(item)
        return
    _assert(
        value is None or type(value) in (str, int, float, bool),
        f"non-primitive serialization value: {type(value)}",
    )


def test_canonical_identity_and_enum_orders() -> dict[str, Any]:
    _assert(MODULE.__name__ == CANONICAL_MODULE, "module key changed")
    _assert(
        MODULE.DiagnosticEnvelope.__module__ == CANONICAL_MODULE,
        "envelope identity changed",
    )
    _assert(
        MODULE.AssignmentProfileName is PROFILE.AssignmentProfileName,
        "profile enum was duplicated",
    )
    _assert(
        MODULE.TerminationReason is TRANSITION.TerminationReason,
        "termination enum was duplicated",
    )
    _assert(
        MODULE.LifecycleCausalSource is EVENT.LifecycleCausalSource,
        "event causal source was duplicated",
    )
    _assert(
        MODULE.ProposalKind is MRTA.ProposalKind,
        "proposal enum was duplicated",
    )
    expected = {
        "DiagnosticAvailability": (
            ("PRODUCED", "produced"),
            ("DEFINED_NOT_PRODUCED", "defined_not_produced"),
            ("NOT_APPLICABLE", "not_applicable"),
        ),
        "DiagnosticKind": (
            ("PROFILE_ROUTE", "profile_route"),
            ("TRANSITION_AUTHORITY", "transition_authority"),
            ("ASSIGNMENT_TICK", "assignment_tick"),
            ("PROPOSAL_RESOLUTION", "proposal_resolution"),
            ("ACTOR_UPDATE", "actor_update"),
            ("TEAM_REWARD", "team_reward"),
            ("CHECKPOINT_SEMANTIC", "checkpoint_semantic"),
            ("DEFAULT_OFF_IDENTITY", "default_off_identity"),
        ),
        "TransitionConsumeStatus": (
            ("FIRST_CONSUME", "first_consume"),
            ("DUPLICATE", "duplicate"),
            ("STALE", "stale"),
            ("FUTURE", "future"),
            ("MISMATCH", "mismatch"),
        ),
        "DefaultOffCohort": (
            ("D0_ABSENT", "d0_absent"),
            ("D1_PRE_RESOLVED_VALID", "d1_pre_resolved_valid"),
            ("SCENARIO_CORRECTION", "scenario_correction"),
        ),
    }
    for name, identities in expected.items():
        actual = tuple(
            (item.name, item.value) for item in getattr(MODULE, name)
        )
        _assert(actual == identities, f"{name} identity/order changed")

    spec = importlib.util.spec_from_file_location(
        "assignment_event_gated_diagnostics_contract",
        MODULE_PATHS[CANONICAL_MODULE],
    )
    _assert(spec is not None and spec.loader is not None, "missing bare spec")
    bare = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bare)
    except ImportError as exc:
        _assert("CanonicalModuleIdentityError" in str(exc), "wrong guard error")
    else:
        raise AssertionError("bare import did not fail")
    return {
        "availability_count": 3,
        "kind_count": 8,
        "consume_status_count": 5,
        "default_off_cohort_count": 3,
    }


def test_all_payloads_and_deterministic_serialization() -> dict[str, Any]:
    payload_field_counts: dict[str, int] = {}
    _assert(
        tuple(field.name for field in fields(MODULE.DiagnosticEnvelope))
        == EXPECTED_ENVELOPE_FIELD_ORDER,
        "DiagnosticEnvelope dataclass field order changed",
    )
    expected_union_types = tuple(
        getattr(MODULE, name) for name in AUTHORITATIVE_PAYLOAD_CLASS_NAMES
    )
    _assert(
        get_args(MODULE.DiagnosticPayload) == expected_union_types,
        "DiagnosticPayload is not the exact eight-class typed union",
    )
    for kind, factory in PAYLOADS.items():
        payload = factory()
        _assert(is_dataclass(payload), f"{kind.value} is not dataclass")
        first = payload.to_mapping()
        second = payload.to_mapping()
        _assert(
            tuple(field.name for field in fields(payload))
            == AUTHORITATIVE_PAYLOAD_FIELD_ORDER[kind],
            f"{kind.value} dataclass field order drifted",
        )
        _assert(
            tuple(first) == AUTHORITATIVE_PAYLOAD_FIELD_ORDER[kind],
            f"{kind.value} field order drifted from Phase A plan section 15.2",
        )
        _assert(tuple(first.items()) == tuple(second.items()), "nondeterminism")
        _assert_primitive_immutable(first)
        envelope = _envelope(kind, payload)
        serialized = envelope.to_mapping()
        _assert_primitive_immutable(serialized)
        _assert(serialized["kind"] == kind.value, "kind serialization changed")
        _assert(
            tuple(serialized) == EXPECTED_ENVELOPE_FIELD_ORDER,
            "envelope field order changed",
        )
        _assert(
            serialized["schema_version"]
            == EXPECTED_ENVELOPE_SCHEMA_VERSION,
            "envelope schema version changed",
        )
        payload_field_counts[kind.value] = len(first)
        try:
            payload.to_mapping()[next(iter(first))] = "changed"
        except TypeError:
            pass
        else:
            raise AssertionError("payload serialization is writable")
    return {
        "payload_field_counts": payload_field_counts,
        "authoritative_literal_orders_pinned": len(
            AUTHORITATIVE_PAYLOAD_FIELD_ORDER
        ),
        "exact_typed_union_size": len(expected_union_types),
        "universal_payload_bag": False,
    }


def test_exact_typed_mapping_and_payload_constructor_rejection(
) -> dict[str, Any]:
    envelope = _envelope(
        MODULE.DiagnosticKind.PROFILE_ROUTE,
        _profile_payload(),
    )
    typed_mapping = {
        "schema_version": envelope.schema_version,
        "kind": envelope.kind,
        "resolved_profile": envelope.resolved_profile,
        "env_id": envelope.env_id,
        "episode_generation": envelope.episode_generation,
        "transition_generation": envelope.transition_generation,
        "assignment_tick_generation": envelope.assignment_tick_generation,
        "availability": envelope.availability,
        "payload": envelope.payload,
    }
    rebuilt = MODULE.DiagnosticEnvelope.from_mapping(typed_mapping)
    _assert(
        rebuilt.to_canonical_items() == envelope.to_canonical_items(),
        "typed envelope reconstruction changed primitive serialization",
    )
    _assert(
        tuple(rebuilt.to_mapping()) == EXPECTED_ENVELOPE_FIELD_ORDER,
        "typed envelope reconstruction changed field order",
    )

    missing = dict(typed_mapping)
    missing.pop("payload")
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(missing),
        MODULE.DiagnosticSchemaError,
        "mapping_keys",
    )
    unknown = dict(typed_mapping)
    unknown["unknown"] = 1
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(unknown),
        MODULE.DiagnosticSchemaError,
        "mapping_keys",
    )
    wrong_enum = dict(typed_mapping)
    wrong_enum["kind"] = "profile_route"
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(wrong_enum),
        MODULE.DiagnosticSchemaError,
        "enum_type",
    )
    wrong_value_type = dict(typed_mapping)
    wrong_value_type["env_id"] = True
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(wrong_value_type),
        MODULE.DiagnosticSchemaError,
        "integer_range",
    )
    wrong_schema = dict(typed_mapping)
    wrong_schema["schema_version"] = "event_gated_diagnostic_envelope_v2"
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(wrong_schema),
        MODULE.DiagnosticSchemaError,
        "schema_version",
    )
    wrong_payload = dict(typed_mapping)
    wrong_payload["payload"] = _checkpoint_payload()
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(wrong_payload),
        MODULE.DiagnosticPayloadKindMismatchError,
        "payload_kind",
    )

    wrong_payload_fields = {
        MODULE.DiagnosticKind.PROFILE_ROUTE: (
            "profile_contract_version",
            1,
            "string_type",
        ),
        MODULE.DiagnosticKind.TRANSITION_AUTHORITY: (
            "consume_token",
            True,
            "integer_range",
        ),
        MODULE.DiagnosticKind.ASSIGNMENT_TICK: (
            "assignment_tick_count",
            True,
            "integer_range",
        ),
        MODULE.DiagnosticKind.PROPOSAL_RESOLUTION: (
            "robot_id",
            True,
            "integer_range",
        ),
        MODULE.DiagnosticKind.ACTOR_UPDATE: (
            "actor_id",
            True,
            "integer_range",
        ),
        MODULE.DiagnosticKind.TEAM_REWARD: (
            "wrapper_final_reward_mean",
            1,
            "finite_float",
        ),
        MODULE.DiagnosticKind.CHECKPOINT_SEMANTIC: (
            "manifest_format_version",
            1,
            "string_type",
        ),
        MODULE.DiagnosticKind.DEFAULT_OFF_IDENTITY: (
            "cohort",
            "d0_absent",
            "enum_type",
        ),
    }
    for kind, factory in PAYLOADS.items():
        payload = factory()
        payload_type = type(payload)
        valid_kwargs = _payload_constructor_kwargs(payload)
        reconstructed_payload = payload_type(**valid_kwargs)
        _assert(
            reconstructed_payload.to_canonical_items()
            == payload.to_canonical_items(),
            f"{kind.value} valid constructor mapping did not reconstruct",
        )

        missing_kwargs = dict(valid_kwargs)
        missing_kwargs.pop(AUTHORITATIVE_PAYLOAD_FIELD_ORDER[kind][0])
        _expect_python_error(
            lambda payload_type=payload_type, missing_kwargs=missing_kwargs: (
                payload_type(**missing_kwargs)
            ),
            TypeError,
        )

        unknown_kwargs = dict(valid_kwargs)
        unknown_kwargs["unknown_field"] = "forbidden"
        _expect_python_error(
            lambda payload_type=payload_type, unknown_kwargs=unknown_kwargs: (
                payload_type(**unknown_kwargs)
            ),
            TypeError,
        )

        field_name, wrong_value, failure_code = wrong_payload_fields[kind]
        wrong_kwargs = dict(valid_kwargs)
        wrong_kwargs[field_name] = wrong_value
        _expect_error(
            lambda payload_type=payload_type, wrong_kwargs=wrong_kwargs: (
                payload_type(**wrong_kwargs)
            ),
            MODULE.DiagnosticSchemaError,
            failure_code,
        )

    return {
        "typed_mapping_reconstruction": True,
        "primitive_serialized_self_parse_claimed": False,
        "envelope_missing_unknown_wrong_type_rejected": True,
        "payload_classes_with_missing_unknown_wrong_type_rejected": 8,
    }


def test_availability_and_payload_kind_rules() -> dict[str, Any]:
    common = {
        "resolved_profile": (
            PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA
        ),
        "env_id": 0,
        "episode_generation": 1,
        "transition_generation": 2,
        "assignment_tick_generation": -1,
    }
    defined = MODULE.DiagnosticEnvelope(
        kind=MODULE.DiagnosticKind.CHECKPOINT_SEMANTIC,
        availability=MODULE.DiagnosticAvailability.DEFINED_NOT_PRODUCED,
        payload=None,
        **common,
    )
    _assert(defined.payload is None, "defined-not-produced fabricated payload")
    not_applicable = MODULE.DiagnosticEnvelope(
        kind=MODULE.DiagnosticKind.ACTOR_UPDATE,
        availability=MODULE.DiagnosticAvailability.NOT_APPLICABLE,
        payload=None,
        **common,
    )
    _assert(not_applicable.payload is None, "N/A fabricated payload")
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope(
            kind=MODULE.DiagnosticKind.TEAM_REWARD,
            availability=MODULE.DiagnosticAvailability.DEFINED_NOT_PRODUCED,
            payload=_reward_payload(),
            **common,
        ),
        MODULE.DiagnosticAvailabilityError,
        "availability_payload",
    )
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope(
            kind=MODULE.DiagnosticKind.TEAM_REWARD,
            availability=MODULE.DiagnosticAvailability.PRODUCED,
            payload=_actor_payload(),
            **common,
        ),
        MODULE.DiagnosticPayloadKindMismatchError,
        "payload_kind",
    )
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope(
            kind=MODULE.DiagnosticKind.ASSIGNMENT_TICK,
            availability=MODULE.DiagnosticAvailability.PRODUCED,
            payload=_tick_payload(),
            **common,
        ),
        MODULE.DiagnosticSchemaError,
        "tick_generation",
    )
    return {
        "defined_not_produced_payload": None,
        "not_applicable_payload": None,
        "zero_fill_fake_measurement": False,
    }


def test_phase_a_availability_authority_matrix() -> dict[str, Any]:
    common = {
        "resolved_profile": (
            PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA
        ),
        "env_id": 0,
        "episode_generation": 1,
        "transition_generation": 2,
        "assignment_tick_generation": -1,
    }

    for kind in PHASE_A_DEFINED_NOT_PRODUCED_KINDS:
        fabricated_payload = _fabricated_unproduced_payload(kind)
        absent = MODULE.DiagnosticEnvelope(
            kind=kind,
            availability=(
                MODULE.DiagnosticAvailability.DEFINED_NOT_PRODUCED
            ),
            payload=None,
            **common,
        )
        _assert(absent.payload is None, f"{kind.value} fabricated payload")
        _expect_error(
            lambda kind=kind, fabricated_payload=fabricated_payload: (
                MODULE.DiagnosticEnvelope(
                    kind=kind,
                    availability=(
                        MODULE.DiagnosticAvailability.DEFINED_NOT_PRODUCED
                    ),
                    payload=fabricated_payload,
                    **common,
                )
            ),
            MODULE.DiagnosticAvailabilityError,
            "availability_payload",
        )

        not_applicable = MODULE.DiagnosticEnvelope(
            kind=kind,
            availability=MODULE.DiagnosticAvailability.NOT_APPLICABLE,
            payload=None,
            **common,
        )
        _assert(
            not_applicable.payload is None,
            f"{kind.value} N/A fabricated payload",
        )
        _expect_error(
            lambda kind=kind, fabricated_payload=fabricated_payload: (
                MODULE.DiagnosticEnvelope(
                    kind=kind,
                    availability=(
                        MODULE.DiagnosticAvailability.NOT_APPLICABLE
                    ),
                    payload=fabricated_payload,
                    **common,
                )
            ),
            MODULE.DiagnosticAvailabilityError,
            "availability_payload",
        )

    for kind in PHASE_A_STATIC_EVIDENCE_KINDS:
        produced = _envelope(kind, PAYLOADS[kind]())
        _assert(
            produced.availability
            is MODULE.DiagnosticAvailability.PRODUCED,
            f"{kind.value} static evidence did not construct",
        )
        _expect_error(
            lambda kind=kind: MODULE.DiagnosticEnvelope(
                kind=kind,
                availability=MODULE.DiagnosticAvailability.PRODUCED,
                payload=None,
                **common,
            ),
            MODULE.DiagnosticPayloadKindMismatchError,
            "payload_kind",
        )
        _expect_error(
            lambda kind=kind: MODULE.DiagnosticEnvelope(
                kind=kind,
                availability=MODULE.DiagnosticAvailability.PRODUCED,
                payload=_reward_payload(),
                **common,
            ),
            MODULE.DiagnosticPayloadKindMismatchError,
            "payload_kind",
        )

    _assert(
        set(PHASE_A_STATIC_EVIDENCE_KINDS).isdisjoint(
            PHASE_A_DEFINED_NOT_PRODUCED_KINDS
        ),
        "Phase-A availability fixture sets overlap",
    )
    _assert(
        set(PHASE_A_STATIC_EVIDENCE_KINDS)
        | set(PHASE_A_DEFINED_NOT_PRODUCED_KINDS)
        == set(MODULE.DiagnosticKind),
        "Phase-A availability fixtures do not cover all kinds",
    )
    return {
        "authoritative_static_semantic_evidence_kinds": tuple(
            item.value for item in PHASE_A_STATIC_EVIDENCE_KINDS
        ),
        "authoritative_later_runtime_producer_kinds": tuple(
            item.value for item in PHASE_A_DEFINED_NOT_PRODUCED_KINDS
        ),
        "production_descriptor_enforces_phase_mapping": False,
        "runtime_producer_claimed": False,
        "fabricated_dnp_or_na_payload_rejected": 10,
        "zero_or_fake_empty_fixture_kinds": 5,
        "static_produced_exact_payload_positive_cases": 3,
    }


def test_assignment_tick_fixed_robot_and_count_relations() -> dict[str, Any]:
    valid = _tick_payload()
    _assert(
        len(valid.per_robot_decision_count) == 2,
        "fixed M length changed",
    )
    kwargs = {
        field_name: getattr(valid, field_name)
        for field_name in valid.to_mapping()
    }
    kwargs["expected_robot_count"] = 3
    _expect_error(
        lambda: MODULE.AssignmentTickDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "tuple_length",
    )
    kwargs = {
        field_name: getattr(valid, field_name)
        for field_name in valid.to_mapping()
    }
    kwargs["needs_assignment_duration"] = (2,)
    kwargs["expected_robot_count"] = 2
    _expect_error(
        lambda: MODULE.AssignmentTickDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "tuple_length",
    )
    kwargs = {
        field_name: getattr(valid, field_name)
        for field_name in valid.to_mapping()
    }
    kwargs["trigger_eligible_count"] = 1
    kwargs["expected_robot_count"] = 2
    _expect_error(
        lambda: MODULE.AssignmentTickDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "trigger_count",
    )
    kwargs = {
        field_name: getattr(valid, field_name)
        for field_name in valid.to_mapping()
    }
    kwargs["policy_proposal_count_by_kind"] = (0, 0, 0, 0)
    kwargs["expected_robot_count"] = 2
    _expect_error(
        lambda: MODULE.AssignmentTickDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "proposal_count",
    )
    kwargs = {
        field_name: getattr(valid, field_name)
        for field_name in valid.to_mapping()
    }
    kwargs["suppressed_resolver_diagnostic_trigger_count"] = 2
    kwargs["expected_robot_count"] = 2
    _expect_error(
        lambda: MODULE.AssignmentTickDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "suppression_count",
    )
    return {
        "expected_robot_count": 2,
        "trigger_count": valid.trigger_eligible_count,
        "proposal_count": sum(valid.policy_proposal_count_by_kind),
        "resolver_trigger_suppressed": 1,
        "fixed_m_tuple_length_checks": 2,
    }


def test_proposal_optional_and_four_mask_rows() -> dict[str, Any]:
    rows = {
        name: _proposal_payload(name)
        for name in (
            "policy_accepted",
            "policy_rejected",
            "policy_noop",
            "forced",
            "no_row",
        )
    }
    _assert(
        rows["policy_rejected"].proposal_accepted is False,
        "rejection absent",
    )
    _assert(
        rows["forced"].proposal_accepted is None,
        "forced row fabricated acceptance",
    )
    _assert(
        rows["no_row"].proposal_effective_mismatch is None,
        "terminal row fabricated mismatch",
    )
    _assert(
        rows["policy_rejected"].policy_proposal_present
        and rows["policy_rejected"].decision_valid,
        "rejected real proposal lost policy-proposal identity",
    )
    _assert(
        rows["policy_noop"].proposal_kind is MRTA.ProposalKind.NOOP_IDLE
        and rows["policy_noop"].policy_proposal_present
        and rows["policy_noop"].decision_valid,
        "NOOP_IDLE was not accepted as a real policy proposal",
    )
    kwargs = {
        field_name: getattr(rows["forced"], field_name)
        for field_name in rows["forced"].to_mapping()
    }
    kwargs["proposal_accepted"] = False
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "proposal_optional",
    )
    kwargs = {
        field_name: getattr(rows["forced"], field_name)
        for field_name in rows["forced"].to_mapping()
    }
    kwargs["policy_proposal_present"] = True
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "four_mask",
    )
    kwargs = {
        field_name: getattr(rows["no_row"], field_name)
        for field_name in rows["no_row"].to_mapping()
    }
    kwargs["proposal_effective_mismatch"] = False
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "proposal_optional",
    )
    kwargs = {
        field_name: getattr(rows["forced"], field_name)
        for field_name in rows["forced"].to_mapping()
    }
    kwargs["policy_caused"] = True
    kwargs["penalty_eligible"] = True
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "penalty_attribution",
    )
    kwargs = {
        field_name: getattr(rows["policy_accepted"], field_name)
        for field_name in rows["policy_accepted"].to_mapping()
    }
    kwargs["forced_nondecision"] = True
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "four_mask",
    )
    kwargs = {
        field_name: getattr(rows["forced"], field_name)
        for field_name in rows["forced"].to_mapping()
    }
    kwargs["stored_action_id"] = -1
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "stored_action",
    )
    kwargs = {
        field_name: getattr(rows["policy_rejected"], field_name)
        for field_name in rows["policy_rejected"].to_mapping()
    }
    kwargs["penalty_eligible"] = True
    kwargs["policy_caused"] = False
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "penalty_attribution",
    )
    for reason in (
        MRTA.ComponentRejectionReason.LOCAL_SET_OVERFLOW_FAIL_CLOSED,
        MRTA.ComponentRejectionReason.POST_SNAPSHOT_SYSTEM_INVALIDATION,
        MRTA.ComponentRejectionReason.TERMINAL_TRANSITION,
    ):
        kwargs = {
            field_name: getattr(rows["policy_rejected"], field_name)
            for field_name in rows["policy_rejected"].to_mapping()
        }
        kwargs["rejection_reason"] = reason
        kwargs["policy_caused"] = True
        kwargs["penalty_eligible"] = True
        _expect_error(
            lambda kwargs=kwargs: MODULE.ProposalResolutionDiagnostic(**kwargs),
            MODULE.DiagnosticSchemaError,
            "nonpolicy_rejection_attribution",
        )
    kwargs = {
        field_name: getattr(rows["policy_accepted"], field_name)
        for field_name in rows["policy_accepted"].to_mapping()
    }
    kwargs["policy_caused"] = True
    _expect_error(
        lambda: MODULE.ProposalResolutionDiagnostic(**kwargs),
        MODULE.DiagnosticSchemaError,
        "penalty_attribution",
    )
    return {
        "policy_rows_have_optional_results": True,
        "forced_and_terminal_results_none": True,
        "four_mask_rows_validated": 4,
        "nonpolicy_rejection_attribution_rejected": 3,
        "noop_idle_real_policy_proposal": True,
        "forced_policy_claim_rejected": True,
        "no_row_mismatch_fabrication_rejected": True,
        "nonpolicy_penalty_claim_rejected": True,
    }


def test_finite_float_and_identity_relations() -> dict[str, Any]:
    numeric_cases = (
        (_proposal_payload("policy_accepted"), "local_cost_before"),
        (_proposal_payload("policy_accepted"), "local_cost_after"),
        (_reward_payload(), "wrapper_final_reward_mean"),
        (_reward_payload(), "rejection_penalty_scale"),
        (_reward_payload(), "team_reward"),
    )
    for payload, field_name in numeric_cases:
        for invalid in (float("nan"), float("inf"), float("-inf")):
            kwargs = _payload_constructor_kwargs(payload)
            kwargs[field_name] = invalid
            payload_type = type(payload)
            _expect_error(
                lambda payload_type=payload_type, kwargs=kwargs: (
                    payload_type(**kwargs)
                ),
                MODULE.DiagnosticSchemaError,
                "finite_float",
            )
    _expect_error(
        lambda: MODULE.DefaultOffIdentityDiagnostic(
            cohort=MODULE.DefaultOffCohort.D0_ABSENT,
            surface="surface",
            evidence_label="evidence",
            expected_digest="a",
            actual_digest="b",
            matched=True,
            deferred_reason=None,
        ),
        MODULE.DiagnosticSchemaError,
        "digest_relation",
    )
    try:
        MODULE.ProfileRouteDiagnostic(
            profile_contract_version="v",
            resolved_variant="event_gated",
            runtime_route="route",
            checkpoint_family="family",
            runtime_readiness="ready",
            resolution_origin="origin",
            event_target_semantics_contract_version=None,
            unknown_field="forbidden",
        )
    except TypeError:
        pass
    else:
        raise AssertionError("unknown payload field was accepted")
    return {
        "finite_float_required": True,
        "finite_float_field_count": len(numeric_cases),
        "nan_posinf_neginf_rejections": len(numeric_cases) * 3,
        "matched_digest_relation": True,
        "unknown_field_rejected": True,
    }


def test_mapping_parser_descriptor_and_private_boundary() -> dict[str, Any]:
    envelope = _envelope(
        MODULE.DiagnosticKind.PROFILE_ROUTE,
        _profile_payload(),
    )
    typed_mapping = {
        "schema_version": envelope.schema_version,
        "kind": envelope.kind,
        "resolved_profile": envelope.resolved_profile,
        "env_id": envelope.env_id,
        "episode_generation": envelope.episode_generation,
        "transition_generation": envelope.transition_generation,
        "assignment_tick_generation": envelope.assignment_tick_generation,
        "availability": envelope.availability,
        "payload": envelope.payload,
    }
    rebuilt = MODULE.DiagnosticEnvelope.from_mapping(typed_mapping)
    _assert(
        rebuilt.to_canonical_items() == envelope.to_canonical_items(),
        "typed mapping rebuild changed serialization",
    )
    unknown = dict(typed_mapping)
    unknown["unknown"] = 1
    _expect_error(
        lambda: MODULE.DiagnosticEnvelope.from_mapping(unknown),
        MODULE.DiagnosticSchemaError,
        "mapping_keys",
    )
    descriptor = MODULE.get_assignment_event_gated_diagnostics_descriptor()
    _assert(isinstance(descriptor, MappingProxyType), "descriptor mutable")
    _assert(
        descriptor["diagnostic_kind_order"]
        == tuple(item.value for item in MODULE.DiagnosticKind),
        "descriptor enum order changed",
    )
    _assert(
        "runtime_sink" not in descriptor,
        "descriptor contains runtime sink implementation",
    )
    rendered = repr(descriptor).lower()
    for private_text in (
        "storage identity",
        "detector",
        "private capability",
        "logger path",
    ):
        _assert(
            private_text not in rendered,
            f"descriptor leaked private/runtime detail: {private_text}",
        )
    _assert(
        "_version" not in _recursive_mapping_keys(descriptor),
        "descriptor leaked tensor mutation-version key",
    )
    _assert(
        ("a" * 64) not in rendered,
        "descriptor leaked a concrete checkpoint fingerprint",
    )
    try:
        descriptor["schema_version"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("descriptor root is writable")
    return {
        "typed_mapping_reconstruction_to_primitive_serialization": True,
        "primitive_serialization_self_parser_claimed": False,
        "descriptor_deep_readonly": True,
        "private_fields_absent": True,
    }


def test_v3_diagnostics_projection_and_frozen_golden() -> dict[str, Any]:
    descriptor = MODULE.get_assignment_event_gated_diagnostics_descriptor()
    scale_contract = EVENT_PROFILE_SCHEMA.build_event_gated_scale_contract(
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
    manifest = CHECKPOINT_V3.build_interface_semantic_descriptor_v3(
        scale_contract=scale_contract
    )
    section = manifest.diagnostics_contract
    section_field_order = tuple(field.name for field in fields(section))
    _assert(
        section_field_order == EXPECTED_V3_DIAGNOSTICS_FIELD_ORDER,
        "V3 diagnostics section field order changed",
    )
    typed_section_projection = {
        field_name: getattr(section, field_name)
        for field_name in section_field_order
    }
    _assert(
        _semantic_content(typed_section_projection)
        == _semantic_content(descriptor),
        "V3 typed diagnostics section differs from canonical descriptor",
    )
    _assert(
        typed_section_projection["contract_version"]
        == "assignment_event_gated_diagnostics_contract_v1",
        "V3 diagnostics contract version changed",
    )
    _assert(
        typed_section_projection["diagnostic_kind_order"]
        == tuple(item.value for item in MODULE.DiagnosticKind),
        "V3 diagnostics kind order changed",
    )
    expected_payload_mapping = tuple(
        (
            kind.value,
            class_name,
            AUTHORITATIVE_PAYLOAD_FIELD_ORDER[kind],
        )
        for kind, class_name in zip(
            MODULE.DiagnosticKind,
            AUTHORITATIVE_PAYLOAD_CLASS_NAMES,
            strict=True,
        )
    )
    _assert(
        typed_section_projection["payload_type_by_kind"]
        == expected_payload_mapping,
        "V3 diagnostics payload mapping changed",
    )
    _assert(
        typed_section_projection["availability_rules"]
        == (
            "produced requires the exact canonical payload type for kind",
            "defined_not_produced requires payload None",
            "not_applicable requires payload None",
            "unproduced measurements are never represented by zero fill",
        ),
        "V3 diagnostics availability rules changed",
    )
    hidden_keys = {
        "logger_path",
        "sink_config",
        "file_format",
        "runtime_evidence_ids",
        "tensorboard_key",
    }
    _assert(
        hidden_keys.isdisjoint(
            _recursive_mapping_keys(typed_section_projection)
        ),
        "V3 diagnostics section gained an A5 runtime/sink field",
    )

    canonical_bytes = (
        CHECKPOINT_V3.canonical_assignment_checkpoint_manifest_v3_bytes(
            manifest
        )
    )
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    _assert(
        len(canonical_bytes) == EXPECTED_V3_INTERFACE_BYTE_LENGTH,
        "frozen V3 canonical byte length drifted",
    )
    _assert(
        digest == EXPECTED_V3_INTERFACE_SHA256,
        "frozen V3 interface SHA-256 drifted",
    )
    return {
        "typed_section_equals_canonical_descriptor": True,
        "v3_diagnostics_field_count": len(section_field_order),
        "hidden_a5_runtime_fields": [],
        "canonical_byte_length": len(canonical_bytes),
        "interface_sha256": digest,
    }


def _ast_dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _flatten_union_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _flatten_union_names(node.left) + _flatten_union_names(
            node.right
        )
    name = _ast_dotted_name(node)
    return (name,) if name else ()


def test_static_no_sink_no_info_and_typed_union_boundary() -> dict[str, Any]:
    paths = (
        MODULE_PATHS[CANONICAL_MODULE],
        MODULE_PATHS[TEAM_REWARD_MODULE],
    )
    forbidden_import_prefixes = (
        "omni",
        "isaacsim",
        "isaaclab.app",
        "gym",
        "harl",
    )
    forbidden_exact_calls = {
        "open",
        "gym.make",
        "torch.save",
        "torch.load",
        "json.dump",
        "csv.writer",
        "logging.getLogger",
        "logging.basicConfig",
        "os.mkdir",
        "os.makedirs",
    }
    forbidden_terminal_calls = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "SummaryWriter",
        "FileHandler",
        "addHandler",
        "backward",
        "load_state_dict",
    }
    runtime_module_fragments = (
        "assignment_harl_wrapper",
        "scan_mobile_manipulator_env",
        "runner",
        "trainer",
    )
    info_roots = {"info", "infos", "extras", "episode_info"}
    checked_calls = 0
    info_writes: list[str] = []

    diagnostics_tree: ast.Module | None = None
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if path == MODULE_PATHS[CANONICAL_MODULE]:
            diagnostics_tree = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported = ((node.module or ""),)
            else:
                imported = ()
            for imported_name in imported:
                lowered_import = imported_name.lower()
                _assert(
                    not any(
                        lowered_import == prefix
                        or lowered_import.startswith(prefix + ".")
                        for prefix in forbidden_import_prefixes
                    ),
                    f"forbidden runtime import in {path.name}: "
                    f"{imported_name}",
                )
                _assert(
                    not any(
                        fragment in lowered_import
                        for fragment in runtime_module_fragments
                    ),
                    f"runtime wiring import in {path.name}: {imported_name}",
                )

            if isinstance(node, ast.Call):
                checked_calls += 1
                call_name = _ast_dotted_name(node.func)
                terminal = call_name.rsplit(".", 1)[-1]
                lowered_call = call_name.lower()
                _assert(
                    call_name not in forbidden_exact_calls
                    and terminal not in forbidden_terminal_calls
                    and not lowered_call.startswith("wandb.")
                    and "optimizer" not in lowered_call
                    and not (
                        terminal == "commit" and "resolver" in lowered_call
                    )
                    and not (
                        terminal == "step"
                        and bool(
                            {"env", "environment"}
                            & set(lowered_call.split("."))
                        )
                    ),
                    f"forbidden behavior call in {path.name}: {call_name}",
                )
                if terminal in {"update", "setdefault", "append"}:
                    receiver = call_name.rsplit(".", 1)[0]
                    if receiver.rsplit(".", 1)[-1] in info_roots:
                        info_writes.append(call_name)

            if isinstance(node, ast.Subscript) and isinstance(
                node.ctx, ast.Store
            ):
                receiver = _ast_dotted_name(node.value)
                if receiver.rsplit(".", 1)[-1] in info_roots:
                    info_writes.append(receiver)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = (
                    node.targets
                    if isinstance(node, ast.Assign)
                    else (node.target,)
                )
                for target in targets:
                    target_name = _ast_dotted_name(target)
                    if target_name.rsplit(".", 1)[-1] in info_roots:
                        info_writes.append(target_name)

            if isinstance(node, (ast.Name, ast.Attribute)):
                _assert(
                    _ast_dotted_name(node).rsplit(".", 1)[-1]
                    != "AppLauncher",
                    f"AppLauncher reference in {path.name}",
                )

    _assert(diagnostics_tree is not None, "diagnostics AST was not loaded")
    union_nodes = [
        node
        for node in diagnostics_tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "DiagnosticPayload"
    ]
    _assert(len(union_nodes) == 1, "DiagnosticPayload alias count changed")
    union_names = _flatten_union_names(union_nodes[0].value)
    _assert(
        union_names == AUTHORITATIVE_PAYLOAD_CLASS_NAMES,
        "DiagnosticPayload AST is not the exact typed union",
    )
    _assert(
        not ({"Any", "dict", "Mapping"} & set(union_names)),
        "DiagnosticPayload gained a universal payload bag",
    )
    _assert(not info_writes, f"runtime info wiring found: {info_writes}")
    return {
        "production_sources_ast_checked": tuple(path.name for path in paths),
        "call_nodes_checked": checked_calls,
        "forbidden_behavior_calls": [],
        "runtime_info_writes": [],
        "typed_union_names": union_names,
        "runtime_sink_or_producer_implemented": False,
    }


def _child_source() -> str:
    return r'''
import contextlib
import dataclasses
import hashlib
import importlib.util
import io
import json
import logging
import os
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
import random
import sys
from types import ModuleType
import torch

def stable_content(value):
    if isinstance(value, Mapping):
        return tuple(
            (stable_content(key), stable_content(item))
            for key, item in value.items()
        )
    if isinstance(value, Enum):
        return (
            "enum",
            type(value).__module__,
            type(value).__qualname__,
            value.name,
            value.value,
        )
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return (
            "dataclass",
            type(value).__module__,
            type(value).__qualname__,
            tuple(
                (field.name, stable_content(getattr(value, field.name)))
                for field in dataclasses.fields(value)
            ),
        )
    if type(value) in (tuple, list):
        return tuple(stable_content(item) for item in value)
    if value is None or type(value) in (str, int, float, bool):
        return value
    return ("repr", repr(value))

def class_content(value):
    members = ()
    if issubclass(value, Enum):
        members = tuple(
            (item.name, item.value, id(item))
            for item in value
        )
    return (
        value.__module__,
        value.__qualname__,
        repr(value),
        members,
    )

def logger_content():
    return tuple(sorted(
        (
            name,
            logger.level,
            logger.propagate,
            logger.disabled,
            tuple(id(handler) for handler in logger.handlers),
        )
        for name, logger in logging.Logger.manager.loggerDict.items()
        if isinstance(logger, logging.Logger)
    ))

paths = [Path(item).resolve() for item in sys.argv[1:]]
names = [
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract",
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_gated_diagnostics_contract",
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
root_logger_level = logging.getLogger().level
named_logger_content = logger_content()
files = tuple(sorted(str(item.relative_to(Path.cwd())) for item in Path.cwd().rglob("*")))
hashes = tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths)
stdout = io.StringIO()
stderr = io.StringIO()
loaded = {}
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    # Establish canonical A1/A2 authority first, then snapshot it before any
    # A3 event/MRTA/diagnostics module is imported.
    for name, path in zip(names[:2], paths[:2]):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    profile = loaded[names[0]]
    transition = loaded[names[1]]
    registry_before = profile.get_assignment_profile_registry()
    registry_before_id = id(registry_before)
    registry_before_repr = repr(registry_before)
    registry_before_content = stable_content(registry_before)
    profile_class_before = profile.AssignmentProfileName
    profile_class_before_id = id(profile_class_before)
    profile_class_before_content = class_content(profile_class_before)
    authority_class_before = transition.LifecycleAuthorityId
    authority_class_before_id = id(authority_class_before)
    authority_class_before_content = class_content(authority_class_before)
    facts_class_before = transition.ExecutionTransitionFacts
    facts_class_before_id = id(facts_class_before)
    facts_class_before_content = class_content(facts_class_before)

    for name, path in zip(names[2:], paths[2:]):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    diag = loaded[names[4]]
    envelope = diag.DiagnosticEnvelope(
        kind=diag.DiagnosticKind.CHECKPOINT_SEMANTIC,
        resolved_profile=profile.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        env_id=0,
        episode_generation=0,
        transition_generation=0,
        assignment_tick_generation=-1,
        availability=diag.DiagnosticAvailability.DEFINED_NOT_PRODUCED,
        payload=None,
    )
    serialized = tuple(envelope.to_mapping())
    diagnostics_descriptor = diag.get_assignment_event_gated_diagnostics_descriptor()
    reward = loaded[names[5]]
    reward_descriptor = reward.get_assignment_team_reward_contract_descriptor()
    reward_contract = reward.TeamRewardContractSpec(
        rejection_penalty_scale=loaded[names[3]].UnresolvedParameterSpec(
            name="rejection_penalty_scale",
            owner_phase="phase_d_e",
            semantic_purpose="once_per_penalty_eligible_rejected_component",
        )
    )
    reward_result = reward.compute_team_reward_oracle(
        contract=reward_contract,
        wrapper_final_reward=torch.tensor(
            [[[1.0], [3.0]]], dtype=torch.float32
        ),
        policy_rejected_component_count=torch.tensor([1], dtype=torch.int64),
        rejection_penalty_scale=0.25,
    )
    reward_oracle_exact = (
        torch.equal(
            reward_result.base_team_reward,
            torch.tensor([[2.0]], dtype=torch.float32),
        )
        and torch.equal(
            reward_result.team_reward,
            torch.tensor([[1.75]], dtype=torch.float32),
        )
        and torch.equal(
            reward_result.learner_reward,
            torch.tensor([[[1.75], [1.75]]], dtype=torch.float32),
        )
    )

    origin = profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    legacy = profile.resolve_assignment_profile(
        profile.AssignmentProfileName.LEGACY, origin
    )
    contract_c = profile.resolve_assignment_profile(
        profile.AssignmentProfileName.LIFECYCLE_CONTRACT_C, origin
    )
    legacy_ready = (
        profile.require_assignment_profile_runtime_ready(
            legacy,
            consumer="phase_a5_pure_test",
            entrypoint="clean_child",
            barrier="old_route_no_sink_evidence",
        )
        is legacy
    )
    contract_c_ready = (
        profile.require_assignment_profile_runtime_ready(
            contract_c,
            consumer="phase_a5_pure_test",
            entrypoint="clean_child",
            barrier="old_route_no_sink_evidence",
        )
        is contract_c
    )
    event_profile = profile.resolve_assignment_profile(
        profile.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, origin
    )
    try:
        profile.require_assignment_profile_runtime_ready(
            event_profile,
            consumer="phase_a5_pure_test",
            entrypoint="clean_child",
            barrier="event_profile_must_remain_interface_only",
        )
    except profile.PhaseAExecutionNotAuthorizedError:
        event_runtime_blocked = True
    else:
        event_runtime_blocked = False
    registry_after = profile.get_assignment_profile_registry()
    profile_registry_identity_unchanged = (
        registry_after is registry_before
        and id(registry_after) == registry_before_id
    )
    profile_registry_repr_unchanged = (
        repr(registry_after) == registry_before_repr
    )
    profile_registry_content_unchanged = (
        stable_content(registry_after) == registry_before_content
    )
    profile_class_identity_unchanged = (
        profile.AssignmentProfileName is profile_class_before
        and id(profile.AssignmentProfileName) == profile_class_before_id
    )
    profile_class_content_unchanged = (
        class_content(profile.AssignmentProfileName)
        == profile_class_before_content
    )
    authority_class_identity_unchanged = (
        transition.LifecycleAuthorityId is authority_class_before
        and id(transition.LifecycleAuthorityId) == authority_class_before_id
    )
    authority_class_content_unchanged = (
        class_content(transition.LifecycleAuthorityId)
        == authority_class_before_content
    )
    facts_class_identity_unchanged = (
        transition.ExecutionTransitionFacts is facts_class_before
        and id(transition.ExecutionTransitionFacts) == facts_class_before_id
    )
    facts_class_content_unchanged = (
        class_content(transition.ExecutionTransitionFacts)
        == facts_class_before_content
    )

blocked = [
    name for name in sys.modules
    if name.startswith(("omni", "harl", "isaaclab.app"))
    or "assignment_harl_wrapper" in name
    or "assignment_checkpoint_" in name
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
    "loggers": tuple(sorted(logging.Logger.manager.loggerDict)) == loggers,
    "handlers": tuple(id(item) for item in logging.getLogger().handlers) == handlers,
    "root_logger_level": logging.getLogger().level == root_logger_level,
    "named_logger_content": logger_content() == named_logger_content,
    "files": files_after == files,
    "sources": tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths) == hashes,
    "stdout": stdout.getvalue(),
    "stderr": stderr.getvalue(),
    "blocked": blocked,
    "serialized": serialized,
    "profile_registry_identity_unchanged": profile_registry_identity_unchanged,
    "profile_registry_repr_unchanged": profile_registry_repr_unchanged,
    "profile_registry_content_unchanged": profile_registry_content_unchanged,
    "profile_class_identity_unchanged": profile_class_identity_unchanged,
    "profile_class_content_unchanged": profile_class_content_unchanged,
    "authority_class_identity_unchanged": authority_class_identity_unchanged,
    "authority_class_content_unchanged": authority_class_content_unchanged,
    "facts_class_identity_unchanged": facts_class_identity_unchanged,
    "facts_class_content_unchanged": facts_class_content_unchanged,
    "diagnostics_descriptor_built": bool(diagnostics_descriptor),
    "reward_descriptor_built": bool(reward_descriptor),
    "reward_oracle_exact": reward_oracle_exact,
    "legacy_ready_without_sink": legacy_ready,
    "contract_c_ready_without_sink": contract_c_ready,
    "event_runtime_blocked": event_runtime_blocked,
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
                *[
                    str(MODULE_PATHS[key])
                    for key in CHILD_MODULE_KEYS
                ],
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
        "root_logger_level",
        "named_logger_content",
        "files",
        "sources",
        "profile_registry_identity_unchanged",
        "profile_registry_repr_unchanged",
        "profile_registry_content_unchanged",
        "profile_class_identity_unchanged",
        "profile_class_content_unchanged",
        "authority_class_identity_unchanged",
        "authority_class_content_unchanged",
        "facts_class_identity_unchanged",
        "facts_class_content_unchanged",
        "diagnostics_descriptor_built",
        "reward_descriptor_built",
        "reward_oracle_exact",
        "legacy_ready_without_sink",
        "contract_c_ready_without_sink",
        "event_runtime_blocked",
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
        "logger_or_sink_created": False,
        "root_and_full_named_logger_state_unchanged": True,
        "legacy_and_contract_c_pure_routes_resolved": True,
        "event_profile_runtime_blocked": True,
        "reward_oracle_and_descriptors_exercised": True,
        "a1_registry_identity_and_content_unchanged": True,
        "a1_profile_class_identity_and_content_unchanged": True,
        "a2_authority_and_facts_class_identity_and_content_unchanged": True,
    }


TESTS = (
    test_canonical_identity_and_enum_orders,
    test_all_payloads_and_deterministic_serialization,
    test_exact_typed_mapping_and_payload_constructor_rejection,
    test_availability_and_payload_kind_rules,
    test_phase_a_availability_authority_matrix,
    test_assignment_tick_fixed_robot_and_count_relations,
    test_proposal_optional_and_four_mask_rows,
    test_finite_float_and_identity_relations,
    test_mapping_parser_descriptor_and_private_boundary,
    test_v3_diagnostics_projection_and_frozen_golden,
    test_static_no_sink_no_info_and_typed_union_boundary,
    test_clean_child_side_effect_boundary,
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
        "tests": results,
        "evidence": evidence,
        "runtime_boundary": (
            "pure/static Phase A5 closeout evidence only; typed diagnostics, "
            "authority-pinned phase availability fixtures, pure descriptors, "
            "and V3 interface canonicalization without a runtime producer, "
            "logger/file sink, checkpoint tensor I/O, AppLauncher, Isaac, "
            "training, playback, diagnosis, or evaluation"
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
