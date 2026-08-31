"""DVM-subset actor collection and slot-aligned proposal storage for B2-I3a.

This module consumes one exact B2-I2 decision bundle and per-agent actor
collection state.  It never reads lifecycle/environment/window authority,
never evaluates forced rows, and never resolves or executes a proposal.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_ACTOR_COLLECTION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_actor_collection"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_ACTOR_COLLECTION_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event actor collection source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_ACTOR_COLLECTION_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

import torch

from .assignment_event_policy_decision import (
    EVENT_POLICY_DECISION_BUNDLE_V2,
    POLICY_FORCED_ACTION_INVALID_ID,
    EventPolicyDecisionBundle,
    EventPolicyRowKind,
)
from .assignment_event_profile_schema_contract_v2 import EventPolicyEvidenceIdentityV2
from .assignment_profile_contract import AssignmentProfileName


EVENT_POLICY_PROPOSAL_ENVELOPE_V2 = "event_policy_proposal_envelope_v2"
EVENT_POLICY_SUBSET_COLLECTOR_V2 = "event_policy_dvm_subset_actor_collector_v2"
EVENT_POLICY_ACTOR_SLOT_STORAGE_V2 = "event_policy_actor_slot_storage_v2"
FORCED_ROW_LOGPROB_SENTINEL = 0.0


class EventPolicyActorCollectionError(RuntimeError):
    """Fail-closed subset collection, scatter, envelope, or slot error."""

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
            f"actual={actual!r}; schema={EVENT_POLICY_PROPOSAL_ENVELOPE_V2!r}"
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
    raise EventPolicyActorCollectionError(
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


def _tensor_contract(
    value: object,
    *,
    field_name: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    stage: str,
    finite: bool = False,
) -> torch.Tensor:
    if (
        type(value) is not torch.Tensor
        or tuple(value.shape) != shape
        or value.dtype is not dtype
        or value.device != device
    ):
        _fail(
            "tensor violates the exact event actor collection contract",
            failure_code="collection_tensor_contract",
            stage=stage,
            field_name=field_name,
            expected=(shape, dtype, device),
            actual=(
                type(value),
                getattr(value, "shape", None),
                getattr(value, "dtype", None),
                getattr(value, "device", None),
            ),
        )
    if finite and not bool(torch.isfinite(value).all().item()):
        _fail(
            "collection tensor must be finite",
            failure_code="nonfinite_collection_tensor",
            stage=stage,
            field_name=field_name,
            expected="all finite",
            actual="contains NaN or infinity",
        )
    return _readonly_tensor(value)


@dataclass(frozen=True, slots=True)
class EventPolicyActorCallRecordV2:
    """Immutable proof of one per-agent compact call decision."""

    agent_id: int
    valid_env_indices: tuple[int, ...]
    actor_called: bool
    actor_batch_size: int


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventPolicyProposalEnvelope:
    """Sealed original proposals/logprobs plus fixed forced routing storage."""

    schema_version: str
    profile_name: str
    collector_version: str
    forced_row_logprob_sentinel: float
    _decision_bundle: EventPolicyDecisionBundle = field(repr=False)
    _evidence_identity: EventPolicyEvidenceIdentityV2 = field(repr=False)
    _action_ids: torch.Tensor = field(repr=False)
    _runner_actions: torch.Tensor = field(repr=False)
    _action_logprobs: torch.Tensor = field(repr=False)
    _original_policy_proposal_ids: torch.Tensor = field(repr=False)
    _policy_proposal_present_mask: torch.Tensor = field(repr=False)
    _decision_valid_mask: torch.Tensor = field(repr=False)
    _row_kind: torch.Tensor = field(repr=False)
    _forced_action_id: torch.Tensor = field(repr=False)
    _sampled_policy_row_mask: torch.Tensor = field(repr=False)
    _forced_row_mask: torch.Tensor = field(repr=False)
    _next_rnn_states: torch.Tensor = field(repr=False)
    _actor_call_records: tuple[EventPolicyActorCallRecordV2, ...]
    _provenance: Mapping[str, object] = field(repr=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "proposal envelope requires the canonical subset collector",
            failure_code="proposal_envelope_factory_required",
            stage="envelope_seal",
            expected="collect_event_policy_proposals_v2",
            actual="direct constructor",
        )

    @classmethod
    def _create(cls, **values: object) -> "EventPolicyProposalEnvelope":
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_POLICY_PROPOSAL_ENVELOPE_V2)
        object.__setattr__(
            instance, "profile_name", AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
        )
        object.__setattr__(instance, "collector_version", EVENT_POLICY_SUBSET_COLLECTOR_V2)
        object.__setattr__(
            instance, "forced_row_logprob_sentinel", FORCED_ROW_LOGPROB_SENTINEL
        )
        object.__setattr__(instance, "_decision_bundle", values["decision_bundle"])
        object.__setattr__(
            instance, "_evidence_identity", values["decision_bundle"].evidence_identity
        )
        for name in (
            "action_ids",
            "runner_actions",
            "action_logprobs",
            "original_policy_proposal_ids",
            "policy_proposal_present_mask",
            "decision_valid_mask",
            "row_kind",
            "forced_action_id",
            "sampled_policy_row_mask",
            "forced_row_mask",
            "next_rnn_states",
        ):
            object.__setattr__(instance, f"_{name}", _readonly_tensor(values[name]))
        object.__setattr__(instance, "_actor_call_records", values["actor_call_records"])
        object.__setattr__(instance, "_provenance", _deep_readonly(values["provenance"]))
        return instance

    @property
    def decision_bundle(self) -> EventPolicyDecisionBundle:
        return self._decision_bundle

    @property
    def evidence_identity(self) -> EventPolicyEvidenceIdentityV2:
        return self._evidence_identity

    @property
    def action_ids(self) -> torch.Tensor:
        return _readonly_tensor(self._action_ids)

    @property
    def runner_actions(self) -> torch.Tensor:
        return _readonly_tensor(self._runner_actions)

    @property
    def action_logprobs(self) -> torch.Tensor:
        return _readonly_tensor(self._action_logprobs)

    @property
    def original_policy_proposal_ids(self) -> torch.Tensor:
        return _readonly_tensor(self._original_policy_proposal_ids)

    @property
    def policy_proposal_present_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._policy_proposal_present_mask)

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
    def sampled_policy_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._sampled_policy_row_mask)

    @property
    def forced_row_mask(self) -> torch.Tensor:
        return _readonly_tensor(self._forced_row_mask)

    @property
    def next_rnn_states(self) -> torch.Tensor:
        return _readonly_tensor(self._next_rnn_states)

    @property
    def actor_call_records(self) -> tuple[EventPolicyActorCallRecordV2, ...]:
        return self._actor_call_records

    @property
    def historical_actor_obs(self) -> torch.Tensor:
        return self._decision_bundle.evidence_snapshot.actor_obs

    @property
    def historical_available_actions(self) -> torch.Tensor:
        return self._decision_bundle.runner_available_actions

    @property
    def provenance(self) -> Mapping[str, object]:
        return self._provenance

    def validate_decision_bundle(self, decision_bundle: EventPolicyDecisionBundle) -> None:
        if decision_bundle is not self._decision_bundle:
            _fail(
                "proposal envelope cannot be rebound to another decision bundle",
                failure_code="decision_bundle_identity_mismatch",
                stage="envelope_identity_validation",
                expected="same exact EventPolicyDecisionBundle object",
                actual="different object",
            )
        if decision_bundle.evidence_identity is not self._evidence_identity:
            _fail(
                "proposal envelope identity chain differs from its decision bundle",
                failure_code="evidence_identity_mismatch",
                stage="envelope_identity_validation",
                expected="same exact EventPolicyEvidenceIdentityV2 object",
                actual="different identity object",
            )
        decision_bundle.validate_evidence_snapshot(decision_bundle.evidence_snapshot)


def _validate_decision_routing(
    decision_bundle: EventPolicyDecisionBundle,
) -> tuple[torch.Tensor, ...]:
    if type(decision_bundle) is not EventPolicyDecisionBundle:
        _fail(
            "collector requires the exact canonical B2-I2 bundle type",
            failure_code="decision_bundle_type",
            stage="collection_validate",
            expected=EventPolicyDecisionBundle,
            actual=type(decision_bundle),
        )
    if (
        decision_bundle.schema_version != EVENT_POLICY_DECISION_BUNDLE_V2
        or decision_bundle.profile_name
        != AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
    ):
        _fail(
            "decision bundle schema/profile binding is invalid",
            failure_code="decision_bundle_schema",
            stage="collection_validate",
            expected=(
                EVENT_POLICY_DECISION_BUNDLE_V2,
                AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value,
            ),
            actual=(decision_bundle.schema_version, decision_bundle.profile_name),
        )
    decision_bundle.validate_evidence_snapshot(decision_bundle.evidence_snapshot)
    identity = decision_bundle.evidence_identity
    E, M, N = identity.num_envs, identity.M, identity.N
    available = decision_bundle.available_actions_bool
    dvm = decision_bundle.decision_valid_mask
    row_kind = decision_bundle.row_kind
    forced_id = decision_bundle.forced_action_id
    proposal_present = decision_bundle.policy_proposal_present_mask
    forced_rows = decision_bundle.forced_row_mask
    device = available.device
    contracts = (
        (available, (E, M, N + 1), torch.bool, "available_actions_bool"),
        (dvm, (E, M, 1), torch.bool, "decision_valid_mask"),
        (row_kind, (E, M), torch.int64, "row_kind"),
        (forced_id, (E, M, 1), torch.int64, "forced_action_id"),
        (proposal_present, (E, M, 1), torch.bool, "policy_proposal_present_mask"),
        (forced_rows, (E, M, 1), torch.bool, "forced_row_mask"),
    )
    for value, shape, dtype, name in contracts:
        if tuple(value.shape) != shape or value.dtype is not dtype or value.device != device:
            _fail(
                "I2 routing tensor violates the collector contract",
                failure_code="decision_routing_contract",
                stage="collection_validate",
                field_name=name,
                expected=(shape, dtype, device),
                actual=(tuple(value.shape), value.dtype, value.device),
            )
    policy_kind = row_kind == int(EventPolicyRowKind.POLICY_DECISION_ROW)
    continuation_kind = row_kind == int(EventPolicyRowKind.FORCED_CONTINUATION_ROW)
    noop_kind = row_kind == int(EventPolicyRowKind.FORCED_NOOP_ROW)
    terminal_kind = row_kind == int(EventPolicyRowKind.TERMINAL_NO_ROW)
    if bool(terminal_kind.any().item()):
        _fail(
            "current actor collection cannot accept terminal no-row semantics",
            failure_code="terminal_row_collection_forbidden",
            stage="collection_validate",
            expected="current I2 rows only",
            actual="TERMINAL_NO_ROW",
        )
    if (
        not torch.equal(dvm[..., 0], policy_kind)
        or not torch.equal(proposal_present, dvm)
        or not torch.equal(forced_rows[..., 0], continuation_kind | noop_kind)
    ):
        _fail(
            "DVM/proposal/forced masks disagree with I2 row kinds",
            failure_code="decision_routing_inconsistent",
            stage="collection_validate",
            expected="DVM and proposal iff POLICY; forced iff continuation/noop",
            actual="inconsistent routing masks",
        )
    policy_available = available[policy_kind]
    if policy_available.numel() and (
        not bool(policy_available[:, N].all().item())
        or bool((policy_available[:, :N].sum(dim=-1) < 1).any().item())
        or bool((forced_id[..., 0][policy_kind] != POLICY_FORCED_ACTION_INVALID_ID).any().item())
    ):
        _fail(
            "policy rows violate historical available/forced-ID semantics",
            failure_code="policy_row_routing_invalid",
            stage="collection_validate",
            expected="legal task plus noop and forced ID -1",
            actual="invalid policy routing",
        )
    if bool(continuation_kind.any().item()):
        ids = forced_id[..., 0][continuation_kind]
        rows = available[continuation_kind]
        selected = rows.gather(1, ids.unsqueeze(-1)).squeeze(-1)
        if (
            bool(((ids < 0) | (ids >= N)).any().item())
            or not bool(selected.all().item())
            or bool((rows.sum(dim=-1) != 1).any().item())
            or bool(rows[:, N].any().item())
        ):
            _fail(
                "continuation rows violate the frozen forced routing plan",
                failure_code="continuation_routing_invalid",
                stage="collection_validate",
                expected="one owned task action and noop false",
                actual="invalid continuation routing",
            )
    if bool(noop_kind.any().item()):
        ids = forced_id[..., 0][noop_kind]
        rows = available[noop_kind]
        if (
            bool((ids != N).any().item())
            or not bool(rows[:, N].all().item())
            or bool((rows.sum(dim=-1) != 1).any().item())
        ):
            _fail(
                "forced-noop rows violate the frozen routing plan",
                failure_code="forced_noop_routing_invalid",
                stage="collection_validate",
                expected="noop-only action ID N",
                actual="invalid forced-noop routing",
            )
    return available, dvm, row_kind, forced_id, proposal_present, forced_rows


def _validate_actor_result(
    *,
    result: object,
    agent_id: int,
    env_indices: torch.Tensor,
    available_subset: torch.Tensor,
    rnn_shape: tuple[int, int],
    device: torch.device,
    N: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    K = int(env_indices.numel())
    if type(result) is not tuple or len(result) != 3:
        _fail(
            "actor get_actions must return an exact three-tensor tuple",
            failure_code="actor_result_contract",
            stage="actor_subset_result",
            field_name=f"actor[{agent_id}]",
            expected="(actions, action_log_probs, rnn_states)",
            actual=type(result),
        )
    actions, logprobs, next_rnn = result
    if type(actions) is not torch.Tensor or tuple(actions.shape) != (K, 1) or actions.device != device:
        _fail(
            "actor actions violate subset shape/device",
            failure_code="actor_action_contract",
            stage="actor_subset_result",
            field_name=f"actor[{agent_id}].actions",
            expected=((K, 1), device),
            actual=(type(actions), getattr(actions, "shape", None), getattr(actions, "device", None)),
        )
    if actions.dtype is torch.bool or (
        not actions.dtype.is_floating_point
        and actions.dtype not in (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
    ):
        _fail(
            "actor discrete actions use an invalid dtype",
            failure_code="actor_action_dtype",
            stage="actor_subset_result",
            field_name=f"actor[{agent_id}].actions",
            expected="integer dtype or integral floating dtype",
            actual=actions.dtype,
        )
    if actions.dtype.is_floating_point:
        if not bool(torch.isfinite(actions).all().item()) or not torch.equal(actions, actions.round()):
            _fail(
                "actor returned a nonfinite or nonintegral discrete action",
                failure_code="actor_action_not_integral",
                stage="actor_subset_result",
                field_name=f"actor[{agent_id}].actions",
                expected="finite integral values",
                actual=actions,
            )
    action_ids = actions.to(torch.int64).contiguous()
    if bool(((action_ids < 0) | (action_ids > N)).any().item()):
        _fail(
            "actor returned an out-of-range discrete action",
            failure_code="actor_action_out_of_range",
            stage="actor_subset_result",
            field_name=f"actor[{agent_id}].actions",
            expected=f"IDs in [0,{N}]",
            actual=action_ids,
        )
    if not bool(available_subset.gather(1, action_ids).all().item()):
        _fail(
            "actor sampled an action masked out by historical available actions",
            failure_code="actor_sampled_masked_action",
            stage="actor_subset_result",
            field_name=f"actor[{agent_id}].actions",
            expected="historical available_actions[action] == true",
            actual=action_ids,
        )
    logprobs = _tensor_contract(
        logprobs,
        field_name=f"actor[{agent_id}].action_logprobs",
        shape=(K, 1),
        dtype=torch.float32,
        device=device,
        stage="actor_subset_result",
        finite=True,
    )
    next_rnn = _tensor_contract(
        next_rnn,
        field_name=f"actor[{agent_id}].rnn_states",
        shape=(K, *rnn_shape),
        dtype=torch.float32,
        device=device,
        stage="actor_subset_result",
        finite=True,
    )
    return action_ids, logprobs, next_rnn


def collect_event_policy_proposals_v2(
    *,
    decision_bundle: EventPolicyDecisionBundle,
    actors: Sequence[object],
    rnn_states: torch.Tensor,
    masks: torch.Tensor,
) -> EventPolicyProposalEnvelope:
    """Call each actor only on its DVM subset and scatter exact fixed tensors."""

    available, dvm, row_kind, forced_id, proposal_present, forced_rows = (
        _validate_decision_routing(decision_bundle)
    )
    identity = decision_bundle.evidence_identity
    E, M, N = identity.num_envs, identity.M, identity.N
    actor_obs = decision_bundle.evidence_snapshot.actor_obs
    device = actor_obs.device
    if type(actors) not in (tuple, list) or len(actors) != M:
        _fail(
            "collector requires one ordered actor per fixed agent",
            failure_code="actor_sequence_contract",
            stage="collection_validate",
            expected=f"tuple/list length {M}",
            actual=(type(actors), len(actors) if isinstance(actors, Sequence) else None),
        )
    if len({id(actor) for actor in actors}) != M:
        _fail(
            "B2-I3a is frozen to share_param=false distinct per-agent actors",
            failure_code="shared_actor_forbidden",
            stage="collection_validate",
            expected="distinct actor object per agent",
            actual="duplicate actor object identity",
        )
    for agent_id, actor in enumerate(actors):
        if not callable(getattr(actor, "get_actions", None)):
            _fail(
                "actor does not expose the installed HARL get_actions API",
                failure_code="actor_api_missing",
                stage="collection_validate",
                field_name=f"actor[{agent_id}]",
                expected="callable get_actions",
                actual=type(actor),
            )
    if type(rnn_states) is not torch.Tensor or rnn_states.ndim != 4:
        _fail(
            "collector RNN placeholder must have shape [E,M,R,H]",
            failure_code="collection_tensor_contract",
            stage="collection_validate",
            field_name="rnn_states",
            expected="float32[E,M,R,H]",
            actual=(type(rnn_states), getattr(rnn_states, "shape", None)),
        )
    R, H = int(rnn_states.shape[2]), int(rnn_states.shape[3])
    rnn_states = _tensor_contract(
        rnn_states,
        field_name="rnn_states",
        shape=(E, M, R, H),
        dtype=torch.float32,
        device=device,
        stage="collection_validate",
        finite=True,
    )
    masks = _tensor_contract(
        masks,
        field_name="masks",
        shape=(E, M, 1),
        dtype=torch.float32,
        device=device,
        stage="collection_validate",
        finite=True,
    )
    if tuple(actor_obs.shape[:2]) != (E, M) or actor_obs.dtype is not torch.float32:
        _fail(
            "I1 actor observations violate the collection contract",
            failure_code="actor_observation_contract",
            stage="collection_validate",
            expected=f"float32[{E},{M},O]",
            actual=(tuple(actor_obs.shape), actor_obs.dtype),
        )

    action_ids = forced_id.clone().contiguous()
    action_logprobs = torch.full(
        (E, M, 1),
        FORCED_ROW_LOGPROB_SENTINEL,
        dtype=torch.float32,
        device=device,
    )
    original_proposals = torch.full(
        (E, M, 1),
        POLICY_FORCED_ACTION_INVALID_ID,
        dtype=torch.int64,
        device=device,
    )
    next_rnn_states = rnn_states.clone().contiguous()
    call_records = []
    with torch.inference_mode():
        for agent_id, actor in enumerate(actors):
            env_indices = dvm[:, agent_id, 0].nonzero(as_tuple=False).flatten()
            valid_tuple = tuple(int(item) for item in env_indices.detach().cpu().tolist())
            K = len(valid_tuple)
            if K == 0:
                call_records.append(
                    EventPolicyActorCallRecordV2(
                        agent_id=agent_id,
                        valid_env_indices=valid_tuple,
                        actor_called=False,
                        actor_batch_size=0,
                    )
                )
                continue
            available_subset = available[env_indices, agent_id].to(torch.float32).contiguous()
            if tuple(available_subset.shape) != (K, N + 1) or bool(
                (available_subset.sum(dim=-1) < 2).any().item()
            ):
                _fail(
                    "policy actor subset lacks a legal task plus noop",
                    failure_code="actor_subset_available_actions",
                    stage="actor_subset_gather",
                    field_name=f"actor[{agent_id}].available_actions",
                    expected=(K, N + 1, "at least two true entries"),
                    actual=(tuple(available_subset.shape), available_subset.sum(dim=-1)),
                )
            result = actor.get_actions(
                actor_obs[env_indices, agent_id].contiguous(),
                rnn_states[env_indices, agent_id].contiguous(),
                masks[env_indices, agent_id].contiguous(),
                available_subset,
                deterministic=False,
            )
            sampled_ids, sampled_logprobs, sampled_rnn = _validate_actor_result(
                result=result,
                agent_id=agent_id,
                env_indices=env_indices,
                available_subset=available_subset.to(torch.bool),
                rnn_shape=(R, H),
                device=device,
                N=N,
            )
            action_ids[env_indices, agent_id] = sampled_ids
            original_proposals[env_indices, agent_id] = sampled_ids
            action_logprobs[env_indices, agent_id] = sampled_logprobs
            next_rnn_states[env_indices, agent_id] = sampled_rnn
            call_records.append(
                EventPolicyActorCallRecordV2(
                    agent_id=agent_id,
                    valid_env_indices=valid_tuple,
                    actor_called=True,
                    actor_batch_size=K,
                )
            )
    if bool(((action_ids < 0) | (action_ids > N)).any().item()):
        _fail(
            "fixed action scatter left an invalid routing ID",
            failure_code="fixed_action_scatter_incomplete",
            stage="fixed_scatter_validate",
            expected=f"all IDs in [0,{N}]",
            actual=action_ids,
        )
    if not torch.equal(original_proposals >= 0, proposal_present):
        _fail(
            "original proposal ledger disagrees with the I2 proposal mask",
            failure_code="proposal_ledger_inconsistent",
            stage="fixed_scatter_validate",
            expected="proposal ID present iff policy proposal mask",
            actual="inconsistent proposal ledger",
        )
    if not bool(
        (action_logprobs[forced_rows] == FORCED_ROW_LOGPROB_SENTINEL).all().item()
    ):
        _fail(
            "forced-row logprob storage differs from the canonical sentinel",
            failure_code="forced_logprob_sentinel_mismatch",
            stage="fixed_scatter_validate",
            expected=FORCED_ROW_LOGPROB_SENTINEL,
            actual=action_logprobs[forced_rows],
        )
    provenance = {
        "envelope_schema_version": EVENT_POLICY_PROPOSAL_ENVELOPE_V2,
        "collector_version": EVENT_POLICY_SUBSET_COLLECTOR_V2,
        "exact_decision_bundle_binding": True,
        "actor_call_rule": "only decision_valid_mask true rows; zero-valid actor skipped",
        "per_agent_share_param": False,
        "gather_scatter_index": "canonical env index within each fixed agent",
        "deterministic_actor_mode": False,
        "original_action_and_behavior_logprob_preserved": True,
        "historical_obs_and_available_actions_source": "exact bound decision bundle",
        "forced_logprob_sentinel": FORCED_ROW_LOGPROB_SENTINEL,
        "forced_logprob_is_behavior_evidence": False,
        "active_masks_replaced_by_dvm": False,
        "lifecycle_environment_or_window_recapture": False,
        "resolver_i4_2_m1_b1_controller_or_env_step": False,
        "policy_update_or_factor_math": False,
    }
    return EventPolicyProposalEnvelope._create(
        decision_bundle=decision_bundle,
        action_ids=action_ids,
        runner_actions=action_ids.to(torch.float32).contiguous(),
        action_logprobs=action_logprobs,
        original_policy_proposal_ids=original_proposals,
        policy_proposal_present_mask=proposal_present,
        decision_valid_mask=dvm,
        row_kind=row_kind,
        forced_action_id=forced_id,
        sampled_policy_row_mask=dvm,
        forced_row_mask=forced_rows,
        next_rnn_states=next_rnn_states,
        actor_call_records=tuple(call_records),
        provenance=provenance,
    )


class EventPolicyActorSlotStorageV2:
    """Per-actor bounded I3a storage; no loss, GAE, factor, or optimizer math."""

    __slots__ = (
        "schema_version",
        "episode_length",
        "agent_id",
        "E",
        "M",
        "N",
        "obs_dim",
        "device",
        "_obs",
        "_available_actions",
        "_decision_valid_masks",
        "_active_masks",
        "_action_ids",
        "_action_logprobs",
        "_decision_bundle_refs",
        "_next_action_slot",
    )

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        _fail(
            "actor slot storage requires the canonical slot-zero factory",
            failure_code="slot_storage_factory_required",
            stage="slot_zero",
            expected="create_event_policy_actor_slot_storage_v2",
            actual="direct constructor",
        )

    @property
    def obs(self) -> torch.Tensor:
        return _readonly_tensor(self._obs)

    @property
    def available_actions(self) -> torch.Tensor:
        return _readonly_tensor(self._available_actions)

    @property
    def decision_valid_masks(self) -> torch.Tensor:
        return _readonly_tensor(self._decision_valid_masks)

    @property
    def active_masks(self) -> torch.Tensor:
        return _readonly_tensor(self._active_masks)

    @property
    def action_ids(self) -> torch.Tensor:
        return _readonly_tensor(self._action_ids)

    @property
    def runner_actions(self) -> torch.Tensor:
        return self._action_ids.to(torch.float32).contiguous()

    @property
    def action_logprobs(self) -> torch.Tensor:
        return _readonly_tensor(self._action_logprobs)

    @property
    def next_action_slot(self) -> int:
        return self._next_action_slot

    @property
    def decision_bundle_refs(self) -> tuple[EventPolicyDecisionBundle | None, ...]:
        return tuple(self._decision_bundle_refs)

    def insert_transition(
        self,
        *,
        slot: int,
        proposal_envelope: EventPolicyProposalEnvelope,
        next_decision_bundle: EventPolicyDecisionBundle,
        next_active_masks: torch.Tensor,
    ) -> None:
        if type(slot) is not int or slot != self._next_action_slot or slot >= self.episode_length:
            _fail(
                "actor storage insertion is not at the next canonical action slot",
                failure_code="slot_alignment",
                stage="slot_insert",
                field_name="slot",
                expected=self._next_action_slot,
                actual=slot,
            )
        if type(proposal_envelope) is not EventPolicyProposalEnvelope:
            _fail(
                "slot insertion requires the exact proposal envelope type",
                failure_code="proposal_envelope_type",
                stage="slot_insert",
                expected=EventPolicyProposalEnvelope,
                actual=type(proposal_envelope),
            )
        current_bundle = self._decision_bundle_refs[slot]
        proposal_envelope.validate_decision_bundle(current_bundle)
        _validate_decision_routing(next_decision_bundle)
        next_identity = next_decision_bundle.evidence_identity
        if (
            next_identity.M != self.M
            or next_identity.N != self.N
            or next_identity.num_envs != self.E
            or next_decision_bundle.evidence_snapshot.actor_obs.shape[-1] != self.obs_dim
        ):
            _fail(
                "next bundle differs from the fixed actor storage domain",
                failure_code="slot_domain_mismatch",
                stage="slot_insert",
                expected=(self.E, self.M, self.N, self.obs_dim),
                actual=(
                    next_identity.num_envs,
                    next_identity.M,
                    next_identity.N,
                    next_decision_bundle.evidence_snapshot.actor_obs.shape[-1],
                ),
            )
        next_active = _tensor_contract(
            next_active_masks,
            field_name="next_active_masks",
            shape=(self.E, 1),
            dtype=torch.float32,
            device=self.device,
            stage="slot_insert",
            finite=True,
        )
        current_obs = current_bundle.evidence_snapshot.actor_obs[:, self.agent_id]
        current_available = current_bundle.runner_available_actions[:, self.agent_id]
        current_dvm = current_bundle.decision_valid_mask[:, self.agent_id]
        if (
            not torch.equal(self._obs[slot], current_obs)
            or not torch.equal(self._available_actions[slot], current_available)
            or not torch.equal(self._decision_valid_masks[slot], current_dvm)
        ):
            _fail(
                "slot-t historical observation/mask/DVM binding was overwritten",
                failure_code="historical_slot_binding_mismatch",
                stage="slot_insert",
                expected="exact current decision-bundle slot",
                actual="stored slot differs",
            )
        self._action_ids[slot] = proposal_envelope.action_ids[:, self.agent_id]
        self._action_logprobs[slot] = proposal_envelope.action_logprobs[:, self.agent_id]
        next_slot = slot + 1
        self._obs[next_slot] = next_decision_bundle.evidence_snapshot.actor_obs[:, self.agent_id]
        self._available_actions[next_slot] = next_decision_bundle.runner_available_actions[:, self.agent_id]
        self._decision_valid_masks[next_slot] = next_decision_bundle.decision_valid_mask[:, self.agent_id]
        self._active_masks[next_slot] = next_active
        self._decision_bundle_refs[next_slot] = next_decision_bundle
        self._next_action_slot = next_slot


def create_event_policy_actor_slot_storage_v2(
    *,
    episode_length: int,
    agent_id: int,
    current_decision_bundle: EventPolicyDecisionBundle,
    initial_active_masks: torch.Tensor,
) -> EventPolicyActorSlotStorageV2:
    """Initialize obs/mask/DVM at slot 0 without shifting the first action."""

    _validate_decision_routing(current_decision_bundle)
    identity = current_decision_bundle.evidence_identity
    E, M, N = identity.num_envs, identity.M, identity.N
    if type(episode_length) is not int or episode_length <= 0:
        _fail(
            "episode length must be an exact positive int",
            failure_code="slot_storage_cardinality",
            stage="slot_zero",
            field_name="episode_length",
            expected="positive int",
            actual=episode_length,
        )
    if type(agent_id) is not int or not 0 <= agent_id < M:
        _fail(
            "actor storage agent ID is outside fixed order",
            failure_code="slot_storage_agent",
            stage="slot_zero",
            field_name="agent_id",
            expected=f"ID in [0,{M})",
            actual=agent_id,
        )
    actor_obs = current_decision_bundle.evidence_snapshot.actor_obs
    available = current_decision_bundle.runner_available_actions
    dvm = current_decision_bundle.decision_valid_mask
    device = actor_obs.device
    active = _tensor_contract(
        initial_active_masks,
        field_name="initial_active_masks",
        shape=(E, 1),
        dtype=torch.float32,
        device=device,
        stage="slot_zero",
        finite=True,
    )
    instance = object.__new__(EventPolicyActorSlotStorageV2)
    instance.schema_version = EVENT_POLICY_ACTOR_SLOT_STORAGE_V2
    instance.episode_length = episode_length
    instance.agent_id = agent_id
    instance.E = E
    instance.M = M
    instance.N = N
    instance.obs_dim = int(actor_obs.shape[-1])
    instance.device = device
    instance._obs = torch.zeros(
        (episode_length + 1, E, instance.obs_dim), dtype=torch.float32, device=device
    )
    instance._available_actions = torch.zeros(
        (episode_length + 1, E, N + 1), dtype=torch.float32, device=device
    )
    instance._decision_valid_masks = torch.zeros(
        (episode_length + 1, E, 1), dtype=torch.bool, device=device
    )
    instance._active_masks = torch.zeros(
        (episode_length + 1, E, 1), dtype=torch.float32, device=device
    )
    instance._action_ids = torch.zeros(
        (episode_length, E, 1), dtype=torch.int64, device=device
    )
    instance._action_logprobs = torch.zeros(
        (episode_length, E, 1), dtype=torch.float32, device=device
    )
    instance._decision_bundle_refs = [None] * (episode_length + 1)
    instance._next_action_slot = 0
    instance._obs[0] = actor_obs[:, agent_id]
    instance._available_actions[0] = available[:, agent_id]
    instance._decision_valid_masks[0] = dvm[:, agent_id]
    instance._active_masks[0] = active
    instance._decision_bundle_refs[0] = current_decision_bundle
    return instance


def get_event_policy_actor_collection_descriptor_v2() -> Mapping[str, object]:
    """Describe implemented I3a collection without enabling later readiness."""

    return _deep_readonly(
        {
            "proposal_envelope_schema_version": EVENT_POLICY_PROPOSAL_ENVELOPE_V2,
            "collector_version": EVENT_POLICY_SUBSET_COLLECTOR_V2,
            "slot_storage_version": EVENT_POLICY_ACTOR_SLOT_STORAGE_V2,
            "profile_name": AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value,
            "actor_call_population": "decision_valid_mask true rows only",
            "zero_valid_actor_call": "skip",
            "fixed_action_shape": "[E,M,1]",
            "fixed_logprob_shape": "[E,M,1]",
            "forced_logprob_sentinel": FORCED_ROW_LOGPROB_SENTINEL,
            "forced_logprob_is_policy_evidence": False,
            "decision_valid_storage_shape": "[T+1,E,1] per actor",
            "action_slot_uses": "decision_valid_masks[:-1] at the same t",
            "active_masks_are_separate": True,
            "policy_update_or_happo_factor_math": False,
            "terminal_or_learner_transport": False,
            "public_runtime_integration": False,
            "readiness_change_authorized": False,
        }
    )


__all__ = (
    "CANONICAL_ASSIGNMENT_EVENT_ACTOR_COLLECTION_MODULE",
    "EVENT_POLICY_ACTOR_SLOT_STORAGE_V2",
    "EVENT_POLICY_PROPOSAL_ENVELOPE_V2",
    "EVENT_POLICY_SUBSET_COLLECTOR_V2",
    "FORCED_ROW_LOGPROB_SENTINEL",
    "EventPolicyActorCallRecordV2",
    "EventPolicyActorCollectionError",
    "EventPolicyActorSlotStorageV2",
    "EventPolicyProposalEnvelope",
    "collect_event_policy_proposals_v2",
    "create_event_policy_actor_slot_storage_v2",
    "get_event_policy_actor_collection_descriptor_v2",
)
