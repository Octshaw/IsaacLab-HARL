"""Pure lifecycle legality and immutable current decision routing for B2-I2.

The only state input is one exact B2-I1 :class:`EventPolicyEvidenceSnapshot`.
This module does not recapture P2, an OPEN window, or environment problem
evidence, and it does not sample, resolve, mutate ownership, or control robots.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_POLICY_DECISION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_policy_decision"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_POLICY_DECISION_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event policy decision source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_POLICY_DECISION_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from types import MappingProxyType

import torch

from .assignment_event_policy_evidence import (
    EVENT_POLICY_EVIDENCE_SNAPSHOT_V2,
    EventPolicyEvidenceSnapshot,
)
from .assignment_event_profile_schema_contract_v2 import EventPolicyEvidenceIdentityV2
from .assignment_lifecycle_transition_contract import (
    RobotLifecycleState,
    TaskLifecycleState,
)
from .assignment_profile_contract import AssignmentProfileName


EVENT_POLICY_DECISION_BUNDLE_V2 = "event_policy_decision_bundle_v2"
EVENT_POLICY_LEGALITY_PROJECTOR_V2 = "event_policy_lifecycle_legality_projector_v2"
EVENT_POLICY_I42_PROPOSAL_SOURCE_BINDING_V2 = (
    "event_policy_i4_2_pre_inference_proposal_source_binding_v2"
)
EVENT_POLICY_TERMINAL_NO_ROW_DESCRIPTOR_V2 = (
    "event_policy_terminal_no_row_semantic_descriptor_v2"
)
POLICY_FORCED_ACTION_INVALID_ID = -1


class EventPolicyDecisionError(RuntimeError):
    """Fail-closed B2-I2 legality, row-plan, or binding error."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.stage = stage
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"field_name={field_name!r}; expected={expected!r}; "
            f"actual={actual!r}; schema={EVENT_POLICY_DECISION_BUNDLE_V2!r}"
        )


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    field_name: str | None = None,
    expected: object = None,
    actual: object = None,
) -> None:
    raise EventPolicyDecisionError(
        message,
        failure_code=failure_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        actual=actual,
    )


def _readonly_tensor(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if type(value) in (tuple, list):
        return tuple(_deep_readonly(item) for item in value)
    return value


class EventPolicyRowKind(IntEnum):
    """Frozen semantic row classes; terminal production is not an I2 route."""

    POLICY_DECISION_ROW = 0
    FORCED_CONTINUATION_ROW = 1
    FORCED_NOOP_ROW = 2
    TERMINAL_NO_ROW = 3


_ACTIVE_OWNED_TASK_STATES = (
    int(TaskLifecycleState.CLAIMED),
    int(TaskLifecycleState.NAVIGATING),
    int(TaskLifecycleState.ALIGNING),
)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyI42ProposalSourceBindingV2:
    """Pre-inference exact binding for a future existing-I4-2 adapter capture."""

    schema_version: str
    adapter_module: str
    adapter_snapshot_type: str
    evidence_schema_version: str
    _evidence_snapshot: EventPolicyEvidenceSnapshot = field(repr=False)
    _identity: EventPolicyEvidenceIdentityV2 = field(repr=False)
    _provenance: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "proposal-source binding requires the decision-bundle factory",
            failure_code="proposal_binding_factory_required",
            stage="bundle_seal",
            expected="seal_current_event_policy_decision_bundle_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls, *, evidence_snapshot: EventPolicyEvidenceSnapshot
    ) -> "EventPolicyI42ProposalSourceBindingV2":
        instance = object.__new__(cls)
        object.__setattr__(
            instance, "schema_version", EVENT_POLICY_I42_PROPOSAL_SOURCE_BINDING_V2
        )
        object.__setattr__(
            instance,
            "adapter_module",
            "assignment_event_proposal_adapter.EventProposalAdapter",
        )
        object.__setattr__(
            instance,
            "adapter_snapshot_type",
            "assignment_event_proposal_adapter.EventProposalDecisionSnapshot",
        )
        object.__setattr__(instance, "evidence_schema_version", evidence_snapshot.schema_version)
        object.__setattr__(instance, "_evidence_snapshot", evidence_snapshot)
        object.__setattr__(instance, "_identity", evidence_snapshot.identity)
        object.__setattr__(
            instance,
            "_provenance",
            _deep_readonly(
                {
                    "phase": "pre_inference_pre_arbitration",
                    "actual_adapter_snapshot_created": False,
                    "future_adapter_inputs": {
                        "identity": "exact sealed I1 identity metadata",
                        "feasibility": "sealed I1 explicit physical feasibility",
                        "ranking_cost": "sealed I1 geometric ranking cost",
                        "available_mask": "I2 legal new-task mask for policy rows",
                    },
                    "proposal_rows": "POLICY_DECISION_ROW only",
                    "forced_rows_are_actor_proposals": False,
                    "resolver_or_b1_called": False,
                    "authority_change": False,
                }
            ),
        )
        return instance

    @property
    def evidence_snapshot(self) -> EventPolicyEvidenceSnapshot:
        return self._evidence_snapshot

    @property
    def identity(self) -> EventPolicyEvidenceIdentityV2:
        return self._identity

    @property
    def p2_publication_identity(self) -> object:
        return self._identity.p2_publication_identity

    @property
    def open_window_identity(self) -> object:
        return self._identity.open_window_identity

    @property
    def episode_generations(self) -> tuple[int, ...]:
        return self._identity.episode_generations

    @property
    def transition_generations(self) -> tuple[int, ...]:
        return self._identity.transition_generations

    @property
    def provenance(self) -> Mapping[str, object]:
        return self._provenance

    def validate_evidence_snapshot(
        self, evidence_snapshot: EventPolicyEvidenceSnapshot
    ) -> None:
        if evidence_snapshot is not self._evidence_snapshot:
            _fail(
                "proposal-source binding cannot be rebound to another I1 snapshot",
                failure_code="evidence_snapshot_identity_mismatch",
                stage="bundle_identity_validation",
                expected="same exact EventPolicyEvidenceSnapshot object",
                actual="different object",
            )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyDecisionBundle:
    """Sealed current legality and fixed-shape pre-inference routing plan."""

    schema_version: str
    profile_name: str
    legality_projector_version: str
    forced_action_invalid_id: int
    _evidence_snapshot: EventPolicyEvidenceSnapshot = field(repr=False)
    _evidence_identity: EventPolicyEvidenceIdentityV2 = field(repr=False)
    _proposal_source_binding: EventPolicyI42ProposalSourceBindingV2 = field(repr=False)
    _available_actions_bool: torch.Tensor = field(repr=False)
    _runner_available_actions: torch.Tensor = field(repr=False)
    _decision_valid_mask: torch.Tensor = field(repr=False)
    _row_kind: torch.Tensor = field(repr=False)
    _forced_action_id: torch.Tensor = field(repr=False)
    _policy_proposal_present_mask: torch.Tensor = field(repr=False)
    _policy_row_mask: torch.Tensor = field(repr=False)
    _forced_continuation_mask: torch.Tensor = field(repr=False)
    _forced_noop_mask: torch.Tensor = field(repr=False)
    _forced_row_mask: torch.Tensor = field(repr=False)
    _terminal_no_row_mask: torch.Tensor = field(repr=False)
    _storage_row_mask: torch.Tensor = field(repr=False)
    _provenance: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "decision bundle requires the canonical sealing factory",
            failure_code="decision_bundle_factory_required",
            stage="bundle_seal",
            expected="seal_current_event_policy_decision_bundle_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(cls, **values: object) -> "EventPolicyDecisionBundle":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_POLICY_DECISION_BUNDLE_V2)
        object.__setattr__(
            instance, "profile_name", AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
        )
        object.__setattr__(
            instance, "legality_projector_version", EVENT_POLICY_LEGALITY_PROJECTOR_V2
        )
        object.__setattr__(
            instance, "forced_action_invalid_id", POLICY_FORCED_ACTION_INVALID_ID
        )
        object.__setattr__(instance, "_evidence_snapshot", values["evidence_snapshot"])
        object.__setattr__(instance, "_evidence_identity", values["evidence_snapshot"].identity)
        object.__setattr__(
            instance, "_proposal_source_binding", values["proposal_source_binding"]
        )
        for name in (
            "available_actions_bool",
            "runner_available_actions",
            "decision_valid_mask",
            "row_kind",
            "forced_action_id",
            "policy_proposal_present_mask",
            "policy_row_mask",
            "forced_continuation_mask",
            "forced_noop_mask",
            "forced_row_mask",
            "terminal_no_row_mask",
            "storage_row_mask",
        ):
            object.__setattr__(instance, f"_{name}", _readonly_tensor(values[name]))
        object.__setattr__(instance, "_provenance", _deep_readonly(values["provenance"]))
        return instance

    @property
    def evidence_snapshot(self) -> EventPolicyEvidenceSnapshot:
        return self._evidence_snapshot

    @property
    def evidence_identity(self) -> EventPolicyEvidenceIdentityV2:
        return self._evidence_identity

    @property
    def proposal_source_binding(self) -> EventPolicyI42ProposalSourceBindingV2:
        return self._proposal_source_binding

    @property
    def available_actions_bool(self) -> torch.Tensor:
        return _readonly_tensor(self._available_actions_bool)

    @property
    def runner_available_actions(self) -> torch.Tensor:
        return _readonly_tensor(self._runner_available_actions)

    @property
    def decision_valid_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._decision_valid_mask)

    @property
    def row_kind(self) -> torch.Tensor:
        return _readonly_tensor(self._row_kind)

    @property
    def forced_action_id(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_action_id)

    @property
    def policy_proposal_present_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._policy_proposal_present_mask)

    @property
    def policy_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._policy_row_mask)

    @property
    def forced_continuation_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_continuation_mask)

    @property
    def forced_noop_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_noop_mask)

    @property
    def forced_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_row_mask)

    @property
    def terminal_no_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._terminal_no_row_mask)

    @property
    def storage_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._storage_row_mask)

    @property
    def provenance(self) -> Mapping[str, object]:
        return self._provenance

    def validate_evidence_snapshot(
        self, evidence_snapshot: EventPolicyEvidenceSnapshot
    ) -> None:
        if evidence_snapshot is not self._evidence_snapshot:
            _fail(
                "decision bundle cannot be rebound to another I1 snapshot",
                failure_code="evidence_snapshot_identity_mismatch",
                stage="bundle_identity_validation",
                expected="same exact EventPolicyEvidenceSnapshot object",
                actual="different object",
            )
        if evidence_snapshot.identity is not self._evidence_identity:
            _fail(
                "decision bundle identity object differs from its sealed I1 snapshot",
                failure_code="evidence_identity_mismatch",
                stage="bundle_identity_validation",
                expected="same exact EventPolicyEvidenceIdentityV2 object",
                actual="different identity object",
            )
        self._proposal_source_binding.validate_evidence_snapshot(evidence_snapshot)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyTerminalNoRowDescriptorV2:
    """Pure historical semantic descriptor; never a current I1 decision bundle."""

    schema_version: str
    E: int
    M: int
    N: int
    forced_action_invalid_id: int
    _available_actions_bool: torch.Tensor = field(repr=False)
    _decision_valid_mask: torch.Tensor = field(repr=False)
    _row_kind: torch.Tensor = field(repr=False)
    _forced_action_id: torch.Tensor = field(repr=False)
    _policy_proposal_present_mask: torch.Tensor = field(repr=False)
    _terminal_no_row_mask: torch.Tensor = field(repr=False)
    _storage_row_mask: torch.Tensor = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "terminal no-row descriptor requires its pure semantic factory",
            failure_code="terminal_descriptor_factory_required",
            stage="terminal_semantic_descriptor",
            expected="build_terminal_no_row_semantics_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(cls, *, E: int, M: int, N: int, device: torch.device) -> "EventPolicyTerminalNoRowDescriptorV2":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_POLICY_TERMINAL_NO_ROW_DESCRIPTOR_V2)
        object.__setattr__(instance, "E", E)
        object.__setattr__(instance, "M", M)
        object.__setattr__(instance, "N", N)
        object.__setattr__(instance, "forced_action_invalid_id", POLICY_FORCED_ACTION_INVALID_ID)
        object.__setattr__(instance, "_available_actions_bool", torch.zeros((E, M, N + 1), dtype=torch.bool, device=device))
        object.__setattr__(instance, "_decision_valid_mask", torch.zeros((E, M, 1), dtype=torch.bool, device=device))
        object.__setattr__(instance, "_row_kind", torch.full((E, M), int(EventPolicyRowKind.TERMINAL_NO_ROW), dtype=torch.int64, device=device))
        object.__setattr__(instance, "_forced_action_id", torch.full((E, M, 1), POLICY_FORCED_ACTION_INVALID_ID, dtype=torch.int64, device=device))
        object.__setattr__(instance, "_policy_proposal_present_mask", torch.zeros((E, M, 1), dtype=torch.bool, device=device))
        object.__setattr__(instance, "_terminal_no_row_mask", torch.ones((E, M, 1), dtype=torch.bool, device=device))
        object.__setattr__(instance, "_storage_row_mask", torch.zeros((E, M, 1), dtype=torch.bool, device=device))
        return instance

    @property
    def available_actions_bool(self) -> torch.Tensor:
        return _readonly_tensor(self._available_actions_bool)

    @property
    def decision_valid_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._decision_valid_mask)

    @property
    def row_kind(self) -> torch.Tensor:
        return _readonly_tensor(self._row_kind)

    @property
    def forced_action_id(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_action_id)

    @property
    def policy_proposal_present_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._policy_proposal_present_mask)

    @property
    def terminal_no_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._terminal_no_row_mask)

    @property
    def storage_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._storage_row_mask)


def _validate_omitted_external_seams(evidence_snapshot: EventPolicyEvidenceSnapshot) -> None:
    physical_source = evidence_snapshot.provenance.get("physical_source")
    seams = physical_source.get("external_producers") if isinstance(physical_source, Mapping) else None
    if type(seams) is not tuple or not seams:
        _fail(
            "I1 provenance does not declare the reviewed external-evidence seams",
            failure_code="external_seam_provenance_missing",
            stage="legality_projection",
            field_name="external_producers",
            expected="non-empty tuple of omitted typed seams",
            actual=type(seams),
        )
    for seam in seams:
        if (
            not isinstance(seam, Mapping)
            or seam.get("included_in_numerical_schema") is not False
            or seam.get("missing_behavior") != "explicitly omitted; no synthetic default"
        ):
            _fail(
                "an active or malformed external seam has no frozen I1 legality tensor",
                failure_code="external_legality_evidence_unavailable",
                stage="legality_projection",
                field_name="external_producers",
                expected="reviewed omitted seam; no synthetic default",
                actual=seam,
            )


def seal_current_event_policy_decision_bundle_v2(
    *, evidence_snapshot: EventPolicyEvidenceSnapshot
) -> EventPolicyDecisionBundle:
    """Project and seal current legality exclusively from one exact I1 snapshot."""

    if type(evidence_snapshot) is not EventPolicyEvidenceSnapshot:
        _fail(
            "B2-I2 requires the exact canonical B2-I1 snapshot type",
            failure_code="evidence_snapshot_type",
            stage="bundle_seal",
            expected=EventPolicyEvidenceSnapshot,
            actual=type(evidence_snapshot),
        )
    if (
        evidence_snapshot.schema_version != EVENT_POLICY_EVIDENCE_SNAPSHOT_V2
        or evidence_snapshot.profile_name != AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
    ):
        _fail(
            "B2-I2 snapshot schema/profile binding is invalid",
            failure_code="evidence_snapshot_schema",
            stage="bundle_seal",
            expected=(
                EVENT_POLICY_EVIDENCE_SNAPSHOT_V2,
                AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value,
            ),
            actual=(evidence_snapshot.schema_version, evidence_snapshot.profile_name),
        )
    _validate_omitted_external_seams(evidence_snapshot)

    identity = evidence_snapshot.identity
    E, M, N = identity.num_envs, identity.M, identity.N
    robot_state = evidence_snapshot.robot_state
    task_state = evidence_snapshot.task_state
    ownership = evidence_snapshot.ownership
    current_owned_task_id = evidence_snapshot.current_owned_task_id
    failed_pairs = evidence_snapshot.cumulative_failed_pairs
    explicit_feasibility = (
        evidence_snapshot.physical_evidence.explicit_physical_feasibility
    )
    device = robot_state.device
    contracts = (
        (task_state, (E, N), torch.int64, "task_state"),
        (ownership, (E, N), torch.int64, "ownership"),
        (current_owned_task_id, (E, M), torch.int64, "current_owned_task_id"),
        (failed_pairs, (E, M, N), torch.bool, "cumulative_failed_pairs"),
        (explicit_feasibility, (E, M, N), torch.bool, "explicit_physical_feasibility"),
    )
    if tuple(robot_state.shape) != (E, M) or robot_state.dtype is not torch.int64:
        _fail(
            "I1 robot lifecycle tensor has an invalid decision contract",
            failure_code="snapshot_tensor_contract",
            stage="legality_projection",
            field_name="robot_state",
            expected=((E, M), torch.int64),
            actual=(tuple(robot_state.shape), robot_state.dtype),
        )
    for value, shape, dtype, name in contracts:
        if tuple(value.shape) != shape or value.dtype is not dtype or value.device != device:
            _fail(
                "I1 evidence tensor has an invalid decision contract",
                failure_code="snapshot_tensor_contract",
                stage="legality_projection",
                field_name=name,
                expected=(shape, dtype, device),
                actual=(tuple(value.shape), value.dtype, value.device),
            )

    needs = robot_state == int(RobotLifecycleState.NEEDS_ASSIGNMENT)
    executing = robot_state == int(RobotLifecycleState.EXECUTING)
    waiting = robot_state == int(RobotLifecycleState.WAITING_FOR_TASK)
    unavailable = robot_state == int(RobotLifecycleState.UNAVAILABLE)
    if not bool((needs | executing | waiting | unavailable).all().item()):
        _fail(
            "I1 robot lifecycle value is outside the frozen row domain",
            failure_code="robot_state_domain",
            stage="row_classification",
            expected=tuple(int(item) for item in RobotLifecycleState),
            actual="unknown robot lifecycle value",
        )

    task_available = task_state == int(TaskLifecycleState.AVAILABLE)
    task_unowned = ownership == -1
    legal_new_targets = (
        needs.unsqueeze(-1)
        & task_available.unsqueeze(1)
        & task_unowned.unsqueeze(1)
        & ~failed_pairs
        & explicit_feasibility
    ).contiguous()
    has_legal_target = legal_new_targets.any(dim=-1)
    policy_rows = needs & has_legal_target
    forced_noop_rows = (needs & ~has_legal_target) | waiting | unavailable

    robot_ids = torch.arange(M, dtype=torch.int64, device=device).view(1, M, 1)
    owned_by_robot = ownership.unsqueeze(1) == robot_ids
    owned_count = owned_by_robot.sum(dim=-1)
    if bool((executing & (owned_count != 1)).any().item()):
        _fail(
            "EXECUTING row does not have exactly one authoritative owned task",
            failure_code="executing_ownership_cardinality",
            stage="row_classification",
            field_name="ownership",
            expected="exactly one task owned by each EXECUTING robot",
            actual="zero or multiple owned tasks",
        )
    if bool((executing & (current_owned_task_id >= N)).any().item()):
        _fail(
            "EXECUTING row has the I1 none-owned sentinel",
            failure_code="executing_owned_task_mismatch",
            stage="row_classification",
            field_name="current_owned_task_id",
            expected="global task ID in [0,N)",
            actual="none sentinel",
        )
    if bool(executing.any().item()):
        safe_owned = current_owned_task_id.clamp(0, N - 1)
        selected_owner = ownership.gather(1, safe_owned)
        selected_task_state = task_state.gather(1, safe_owned)
        row_ids = torch.arange(M, dtype=torch.int64, device=device).view(1, M).expand(E, M)
        if bool((executing & (selected_owner != row_ids)).any().item()):
            _fail(
                "EXECUTING inverse owned-task evidence disagrees with ownership",
                failure_code="executing_owned_task_mismatch",
                stage="row_classification",
                field_name="current_owned_task_id",
                expected="inverse of exact ownership",
                actual="mismatched owner",
            )
        active = torch.zeros((E, M), dtype=torch.bool, device=device)
        for state in _ACTIVE_OWNED_TASK_STATES:
            active |= selected_task_state == state
        if bool((executing & ~active).any().item()):
            _fail(
                "EXECUTING owned task is not in an active continuation state",
                failure_code="executing_task_not_active",
                stage="row_classification",
                field_name="task_state",
                expected=tuple(_ACTIVE_OWNED_TASK_STATES),
                actual="non-active task state",
            )

    available_actions = torch.zeros((E, M, N + 1), dtype=torch.bool, device=device)
    available_actions[..., :N] = legal_new_targets
    available_actions[..., N] = policy_rows | forced_noop_rows
    if bool(executing.any().item()):
        exec_env, exec_robot = executing.nonzero(as_tuple=True)
        exec_task = current_owned_task_id[exec_env, exec_robot]
        available_actions[exec_env, exec_robot, exec_task] = True

    row_kind = torch.full(
        (E, M), int(EventPolicyRowKind.FORCED_NOOP_ROW), dtype=torch.int64, device=device
    )
    row_kind[policy_rows] = int(EventPolicyRowKind.POLICY_DECISION_ROW)
    row_kind[executing] = int(EventPolicyRowKind.FORCED_CONTINUATION_ROW)
    forced_action_id = torch.full(
        (E, M, 1), POLICY_FORCED_ACTION_INVALID_ID, dtype=torch.int64, device=device
    )
    forced_action_id[..., 0][forced_noop_rows] = N
    forced_action_id[..., 0][executing] = current_owned_task_id[executing]

    policy_row_mask = policy_rows.unsqueeze(-1).contiguous()
    forced_continuation_mask = executing.unsqueeze(-1).contiguous()
    forced_noop_mask = forced_noop_rows.unsqueeze(-1).contiguous()
    forced_row_mask = (executing | forced_noop_rows).unsqueeze(-1).contiguous()
    terminal_no_row_mask = torch.zeros((E, M, 1), dtype=torch.bool, device=device)
    storage_row_mask = torch.ones((E, M, 1), dtype=torch.bool, device=device)
    decision_valid_mask = policy_row_mask.clone().contiguous()
    policy_proposal_present_mask = policy_row_mask.clone().contiguous()
    if bool((available_actions.sum(dim=-1) == 0).any().item()):
        _fail(
            "current nonterminal decision row has no routed semantic action",
            failure_code="all_zero_current_action_row",
            stage="bundle_validation",
            field_name="available_actions_bool",
            expected="at least one true action per current row",
            actual="all false row",
        )
    if not bool((policy_rows | executing | forced_noop_rows).all().item()):
        _fail(
            "current row classification is not exhaustive",
            failure_code="row_partition_incomplete",
            stage="bundle_validation",
            expected="exactly one current row class",
            actual="unclassified row",
        )

    proposal_binding = EventPolicyI42ProposalSourceBindingV2._create(
        evidence_snapshot=evidence_snapshot
    )
    provenance = {
        "bundle_schema_version": EVENT_POLICY_DECISION_BUNDLE_V2,
        "exact_input_rule": "one exact immutable EventPolicyEvidenceSnapshot",
        "p2_or_window_recapture": False,
        "physical_problem_recapture": False,
        "geometric_ranking_cost_used_for_legality": False,
        "external_legality_seams": "reviewed v2 omissions; no synthetic defaults",
        "dvm_definition": "true iff POLICY_DECISION_ROW",
        "runner_available_actions_boundary_dtype": "float32",
        "forced_action_semantics": {
            "policy": "invalid sentinel -1; no forced action",
            "continuation": "authoritative current owned global task ID",
            "noop": "raw HARL ID N; future decode maps N to -1",
        },
        "policy_proposal_present_semantics": "pre-inference eligibility only",
        "same_task_multi_robot_conflict_preserved": True,
        "actual_sample_or_logprob_present": False,
        "resolver_or_arbitration_result_present": False,
        "effective_assignment_present": False,
        "lifecycle_or_ownership_mutation": False,
        "terminal_historical_production": False,
        "learner_active_mask_semantics": False,
    }
    return EventPolicyDecisionBundle._create(
        evidence_snapshot=evidence_snapshot,
        proposal_source_binding=proposal_binding,
        available_actions_bool=available_actions,
        runner_available_actions=available_actions.to(torch.float32).contiguous(),
        decision_valid_mask=decision_valid_mask,
        row_kind=row_kind,
        forced_action_id=forced_action_id,
        policy_proposal_present_mask=policy_proposal_present_mask,
        policy_row_mask=policy_row_mask,
        forced_continuation_mask=forced_continuation_mask,
        forced_noop_mask=forced_noop_mask,
        forced_row_mask=forced_row_mask,
        terminal_no_row_mask=terminal_no_row_mask,
        storage_row_mask=storage_row_mask,
        provenance=provenance,
    )


def build_terminal_no_row_semantics_v2(
    *, E: int, M: int, N: int, device: torch.device
) -> EventPolicyTerminalNoRowDescriptorV2:
    """Build only the frozen terminal no-row semantics, without I1/history input."""

    if any(type(value) is not int or value <= 0 for value in (E, M, N)):
        _fail(
            "terminal descriptor cardinalities must be exact positive ints",
            failure_code="terminal_descriptor_cardinality",
            stage="terminal_semantic_descriptor",
            expected="positive exact E/M/N",
            actual=(E, M, N),
        )
    if type(device) is not torch.device:
        _fail(
            "terminal descriptor requires an exact torch.device",
            failure_code="terminal_descriptor_device",
            stage="terminal_semantic_descriptor",
            expected=torch.device,
            actual=type(device),
        )
    return EventPolicyTerminalNoRowDescriptorV2._create(E=E, M=M, N=N, device=device)


def get_event_policy_decision_descriptor_v2() -> Mapping[str, object]:
    """Describe implemented I2 routing without changing any readiness gate."""

    return _deep_readonly(
        {
            "bundle_schema_version": EVENT_POLICY_DECISION_BUNDLE_V2,
            "legality_projector_version": EVENT_POLICY_LEGALITY_PROJECTOR_V2,
            "profile_name": AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value,
            "row_kinds": tuple((item.name, int(item)) for item in EventPolicyRowKind),
            "canonical_available_actions_dtype": "bool",
            "runner_available_actions_dtype": "float32",
            "decision_valid_definition": "true iff POLICY_DECISION_ROW",
            "policy_forced_action_invalid_id": POLICY_FORCED_ACTION_INVALID_ID,
            "terminal_no_row_is_descriptor_only": True,
            "input": "exact EventPolicyEvidenceSnapshot object only",
            "p2_physical_window_recapture": False,
            "actor_sampling_or_logprob": False,
            "resolver_or_b1_execution": False,
            "public_runtime_integration": False,
            "readiness_change_authorized": False,
        }
    )


__all__ = (
    "CANONICAL_ASSIGNMENT_EVENT_POLICY_DECISION_MODULE",
    "EVENT_POLICY_DECISION_BUNDLE_V2",
    "EVENT_POLICY_I42_PROPOSAL_SOURCE_BINDING_V2",
    "EVENT_POLICY_LEGALITY_PROJECTOR_V2",
    "EVENT_POLICY_TERMINAL_NO_ROW_DESCRIPTOR_V2",
    "POLICY_FORCED_ACTION_INVALID_ID",
    "EventPolicyDecisionBundle",
    "EventPolicyDecisionError",
    "EventPolicyI42ProposalSourceBindingV2",
    "EventPolicyRowKind",
    "EventPolicyTerminalNoRowDescriptorV2",
    "build_terminal_no_row_semantics_v2",
    "get_event_policy_decision_descriptor_v2",
    "seal_current_event_policy_decision_bundle_v2",
)
