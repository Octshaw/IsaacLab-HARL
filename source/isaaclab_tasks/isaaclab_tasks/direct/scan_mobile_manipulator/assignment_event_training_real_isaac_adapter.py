"""Private B2-R5I binding from a completed real event route into R5.

This module neither constructs nor steps an environment.  It consumes the
reviewed route's completed actor storages, critic buffer, terminal-consumption
ledger, and current post-autoreset decision bundle.  Mutation remains owned by
the existing R2/R3/R4 executors and the R5 full-transaction coordinator.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_REAL_ISAAC_ADAPTER_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_real_isaac_adapter"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_REAL_ISAAC_ADAPTER_MODULE:
    raise ImportError("CanonicalModuleIdentityError: B2-R5I requires canonical import")


from contextlib import contextmanager
from dataclasses import dataclass
import math
from typing import Callable, Iterator, Mapping, Sequence

import torch

from .assignment_event_actor_collection import (
    FORCED_ROW_LOGPROB_SENTINEL,
    create_event_policy_actor_slot_storage_v2,
)
from .assignment_event_policy_decision import (
    POLICY_FORCED_ACTION_INVALID_ID,
    EventPolicyRowKind,
)
from .assignment_event_happo_policy_math import normalize_event_policy_advantages_v2
from .assignment_event_terminal_learner_transport import (
    capture_event_learner_transition_expectation_v2,
    capture_event_rollout_critic_guard_v2,
)
from .assignment_lifecycle_transition_contract import TerminationReason
from .assignment_event_training_evidence import (
    B2RFrozenTrainingInputsV1,
    B2RResolvedConfigV1,
    B2RSourceDigestV1,
    B2RUpdateAuthorityV1,
    VALUE_NORMALIZER_STATE_KEYS,
    canonical_live_valuenorm_state_v1,
    canonical_digest_v1,
    fingerprint_tensor_v1,
)
from .assignment_event_training_plans import (
    build_actor_update_plan_v1,
    build_critic_update_plan_v1,
    build_exact_partitions_v1,
)
from .assignment_event_training_control import B2RUpdateStageV1
from . import assignment_event_training_actor_mutation as R3
from . import assignment_event_training_critic_mutation as R4
from . import assignment_event_training_full_transaction as R5


R5I_CLASSIFICATION = (
    "PHASE-B2-R5I-REAL-ISAAC-SINGLE-TRANSACTION-INTEGRATION-"
    "COMPLETE-AWAITING-GPT-REVIEW"
)


def _tensor_digest(value: torch.Tensor) -> str:
    return fingerprint_tensor_v1(value).content_digest


def _tensor_tuple_digest(*values: torch.Tensor) -> str:
    return canonical_digest_v1(tuple(_tensor_digest(value) for value in values))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-R5I REAL_EVIDENCE_BINDING: {message}")


def _canonical_valuenorm_observation_v1(
    value_normalizer: object,
    *, diagnostic_on_error: bool = False,
) -> Mapping[str, object]:
    """Return bounded read-only evidence from the qualified live-state extractor."""

    extraction_error = None
    try:
        state = canonical_live_valuenorm_state_v1(value_normalizer)
    except BaseException as exc:
        if not diagnostic_on_error:
            raise
        # Failure evidence only. These fields never enter permits or mutation truth.
        extraction_error = f"{type(exc).__name__}: {exc}"
        state = {
            name: getattr(value_normalizer, name).detach().clone()
            for name in VALUE_NORMALIZER_STATE_KEYS
            if isinstance(getattr(value_normalizer, name, None), torch.Tensor)
        }
    fields: list[Mapping[str, object]] = []
    for name, value in state.items():
        live_value = getattr(value_normalizer, name)
        flat = value.detach().reshape(-1)
        bounded = flat[:16].cpu().tolist()
        fields.append(
            {
                "name": name,
                "digest": _tensor_digest(value),
                "shape": tuple(int(item) for item in value.shape),
                "dtype": str(value.dtype),
                "device": str(value.device),
                "live_attribute_type": type(live_value).__name__,
                "value_count": int(flat.numel()),
                "bounded_values": tuple(
                    float(item) if math.isfinite(float(item)) else str(float(item))
                    for item in bounded
                ),
                "bounded_values_complete": int(flat.numel()) <= 16,
                "finite": bool(torch.isfinite(value).all().item()),
            }
        )
    native_state = value_normalizer.state_dict()
    return {
        "canonical_fingerprint": (
            R4._valuenorm_digest(value_normalizer) if extraction_error is None else None
        ),
        "canonical_extraction_error": extraction_error,
        "diagnostic_only_invalid_state": extraction_error is not None,
        "canonical_fields": tuple(fields),
        "canonical_field_names": tuple(state),
        "live_device": fields[0]["device"] if fields else "",
        "live_attribute_types": tuple(
            (str(item["name"]), str(item["live_attribute_type"])) for item in fields
        ),
        "native_state_dict_key_count_diagnostic_only": len(native_state),
        "native_state_dict_keys_diagnostic_only": tuple(native_state),
        "all_finite": bool(fields) and all(bool(item["finite"]) for item in fields),
    }


def _changed_valuenorm_fields_v1(
    before: Mapping[str, object], after: Mapping[str, object]
) -> tuple[str, ...]:
    before_fields = {
        str(item["name"]): str(item["digest"])
        for item in before["canonical_fields"]
    }
    after_fields = {
        str(item["name"]): str(item["digest"])
        for item in after["canonical_fields"]
    }
    return tuple(
        name for name in before_fields if after_fields.get(name) != before_fields[name]
    )


@contextmanager
def _scoped_attempt4_progress_observers_v1(
    *,
    update_id: str,
    actor_inputs: Mapping[int, R3.B2R3ActorInputsV1],
    route_state: object,
    factor_segment_observer: Callable[[Mapping[str, object]], None] | None,
    critic_progress_observer: Callable[[Mapping[str, object]], None] | None,
) -> Iterator[None]:
    """Add durable observation around, but not inside, qualified mutation semantics."""

    original_factor_validator = R3.validate_factor_segment_contract_v1
    original_actor_sequence = R3.execute_actor_sequence_v1
    original_valuenorm_proxy = R4.B2R4PermittedLiveValueNormProxyV1
    original_loss_diagnostics = R4._critic_loss_diagnostics_v1
    original_critic_receipt = R4.B2R4CriticStepReceiptV1
    original_critic_sequence = R4.execute_critic_sequence_v1
    factor_segments: list[R3.B2R3ActorSegmentReceiptV1] = []
    critic_receipts: list[R4.B2R4CriticStepReceiptV1] = []
    valuenorm_pre: dict[tuple[int, int], Mapping[str, object]] = {}
    valuenorm_post: dict[tuple[int, int], Mapping[str, object]] = {}

    def observed_factor_validator(
        receipt: R3.B2R3ActorSegmentReceiptV1,
        *,
        expected_dvm_indices: tuple[int, ...],
    ) -> None:
        original_factor_validator(
            receipt, expected_dvm_indices=expected_dvm_indices
        )
        factor_segments.append(receipt)
        if factor_segment_observer is None:
            return
        inputs = actor_inputs[receipt.actor_id]
        off_dvm_rows = R3._canonical_true_row_indices_v1(
            ~inputs.decision_valid_mask
        )
        factor_segment_observer(
            {
                "schema_version": "b2r5i_re3_factor_progress_event_v1",
                "run_identity": update_id,
                "update_id": update_id,
                "stage": "S5_ACTOR_SEGMENT_COMPLETE",
                "state_machine_stage": route_state.machine.current.value,
                "actor_id": receipt.actor_id,
                "actor_segment_index": receipt.actor_order_position,
                "actor_order_position": receipt.actor_order_position,
                "factor_before_digest": receipt.factor_before_digest,
                "factor_pre_logprob_digest": receipt.factor_pre_logprob_digest,
                "factor_post_logprob_digest": receipt.factor_post_logprob_digest,
                "ratio_full_digest": receipt.factor_transition.ratio_full_digest,
                "factor_after_digest": receipt.factor_transition.factor_after_digest,
                "dvm_rows": receipt.dvm_indices,
                "off_dvm_rows": off_dvm_rows,
                "off_dvm_exact_one": receipt.factor_transition.off_dvm_exact_one,
                "prior_accumulation_preserved": receipt.prior_accumulation_preserved,
                "segment_backward_count": receipt.observed_backward_count,
                "segment_optimizer_step_count": receipt.observed_step_count,
                "factor_post_audit_pass": True,
                "complete_actor_sequence": False,
                "cumulative_actor_backward_count": sum(
                    item.observed_backward_count for item in factor_segments
                ),
                "cumulative_actor_optimizer_step_count": sum(
                    item.observed_step_count for item in factor_segments
                ),
                "cumulative_critic_backward_count": 0,
                "cumulative_critic_optimizer_step_count": 0,
                "cumulative_live_valuenorm_update_count": 0,
            }
        )

    def observed_actor_sequence(*args: object, **kwargs: object) -> object:
        receipt = original_actor_sequence(*args, **kwargs)
        if factor_segment_observer is not None:
            factor_segment_observer(
                {
                    "schema_version": "b2r5i_re3_factor_progress_event_v1",
                    "run_identity": update_id,
                    "update_id": update_id,
                    "stage": "S5_ACTOR_SEQUENCE_COMPLETE",
                    "state_machine_stage": route_state.machine.current.value,
                    "complete_actor_sequence": True,
                    "completed_actor_segment_count": len(receipt.actor_segments),
                    "actor_order": receipt.actor_order,
                    "initial_factor_digest": receipt.initial_factor_digest,
                    "final_factor_digest": receipt.final_factor_digest,
                    "factor_post_audit_pass_count": len(factor_segments),
                    "cumulative_actor_backward_count": sum(
                        item.observed_backward_count for item in factor_segments
                    ),
                    "cumulative_actor_optimizer_step_count": sum(
                        item.observed_step_count for item in factor_segments
                    ),
                    "cumulative_critic_backward_count": 0,
                    "cumulative_critic_optimizer_step_count": 0,
                    "cumulative_live_valuenorm_update_count": 0,
                }
            )
        return receipt

    original_proxy_init = original_valuenorm_proxy.__dict__["__init__"]
    original_proxy_update = original_valuenorm_proxy.__dict__["update"]

    class _ObservedLiveValueNormProxyV1(original_valuenorm_proxy):
        __slots__ = ()

        def __init__(self, *args: object, **kwargs: object) -> None:
            original_proxy_init(self, *args, **kwargs)
            if critic_progress_observer is None:
                return
            key = (self.epoch, self.minibatch)
            observation = _canonical_valuenorm_observation_v1(
                self.value_normalizer
            )
            valuenorm_pre[key] = observation
            critic_progress_observer(
                {
                    "schema_version": "b2r5i_re3_critic_progress_event_v1",
                    "run_identity": update_id,
                    "update_id": update_id,
                    "stage": "S6_VALUENORM_PRE_UPDATE_BOUND",
                    "state_machine_stage": route_state.machine.current.value,
                    "critic_epoch": self.epoch,
                    "critic_minibatch": self.minibatch,
                    "canonical_physical_rows": self.canonical_indices,
                    "canonical_row_digest": canonical_digest_v1(
                        self.canonical_indices
                    ),
                    "raw_target_digest": self.raw_digest,
                    "valuenorm_pre": observation,
                    "cumulative_critic_backward_count": self.counter.critic_backward_executed,
                    "cumulative_critic_optimizer_step_count": self.counter.critic_step_executed,
                    "cumulative_live_valuenorm_update_count": self.counter.live_valuenorm_executed,
                }
            )

        def _emit_post(self, *, source_error: str | None) -> None:
            if critic_progress_observer is None:
                return
            key = (self.epoch, self.minibatch)
            before = valuenorm_pre.get(key)
            after = _canonical_valuenorm_observation_v1(
                self.value_normalizer, diagnostic_on_error=source_error is not None
            )
            valuenorm_post[key] = after
            changed = (
                _changed_valuenorm_fields_v1(before, after)
                if before is not None
                else ()
            )
            critic_progress_observer(
                {
                    "schema_version": "b2r5i_re3_critic_progress_event_v1",
                    "run_identity": update_id,
                    "update_id": update_id,
                    "stage": "S6_VALUENORM_POST_UPDATE_OBSERVED",
                    "state_machine_stage": route_state.machine.current.value,
                    "critic_epoch": self.epoch,
                    "critic_minibatch": self.minibatch,
                    "canonical_physical_rows": self.canonical_indices,
                    "canonical_row_digest": canonical_digest_v1(
                        self.canonical_indices
                    ),
                    "raw_target_digest": self.raw_digest,
                    "valuenorm_pre_fingerprint": (
                        before["canonical_fingerprint"] if before is not None else ""
                    ),
                    "valuenorm_post": after,
                    "changed_valuenorm_fields": changed,
                    "canonical_mutation": (
                        bool(changed) if after["canonical_fingerprint"] is not None else None
                    ),
                    "canonical_state_finite": bool(after["all_finite"]),
                    "update_call_index": self.counter.live_valuenorm_executed,
                    "qualified_source_error": source_error,
                    "cumulative_critic_backward_count": self.counter.critic_backward_executed,
                    "cumulative_critic_optimizer_step_count": self.counter.critic_step_executed,
                    "cumulative_live_valuenorm_update_count": self.counter.live_valuenorm_executed,
                }
            )

        def update(self, input_vector: torch.Tensor) -> None:
            try:
                original_proxy_update(self, input_vector)
            except BaseException as exc:
                try:
                    self._emit_post(source_error=f"{type(exc).__name__}: {exc}")
                except BaseException:
                    pass
                raise
            self._emit_post(source_error=None)

    def observed_loss_diagnostics(*args: object, **kwargs: object) -> object:
        """Flush source-faithful loss/graph evidence before the unique backward."""

        result = original_loss_diagnostics(*args, **kwargs)
        if critic_progress_observer is not None:
            loss, decomposition, graph = result
            key = next(reversed(valuenorm_pre), (-1, -1))
            before = valuenorm_pre.get(key)
            after = valuenorm_post.get(key)
            critic_progress_observer(
                {
                    "schema_version": "b2r5i_re3_critic_progress_event_v1",
                    "run_identity": update_id,
                    "update_id": update_id,
                    "stage": "S6_CRITIC_PRE_BACKWARD_DIAGNOSTIC",
                    "state_machine_stage": route_state.machine.current.value,
                    "critic_epoch": key[0],
                    "critic_minibatch": key[1],
                    "canonical_physical_rows": decomposition.canonical_indices,
                    "raw_target_digest": decomposition.raw_target_digest,
                    "normalized_target_digest": decomposition.normalized_target_digest,
                    "frozen_value_prediction_digest": decomposition.frozen_value_prediction_digest,
                    "current_value_digest": decomposition.current_value_digest,
                    "valuenorm_pre": before,
                    "valuenorm_post": after,
                    "loss_value": float(loss.detach().item()),
                    "loss_graph_evidence": graph,
                    "loss_decomposition": decomposition,
                    "cumulative_critic_backward_count": len(critic_receipts),
                    "cumulative_critic_optimizer_step_count": len(critic_receipts),
                    "cumulative_live_valuenorm_update_count": sum(
                        int(item.valuenorm_receipt is not None)
                        for item in critic_receipts
                    ) + 1,
                }
            )
        return result

    def observed_critic_receipt(*args: object, **kwargs: object) -> object:
        receipt = original_critic_receipt(*args, **kwargs)
        critic_receipts.append(receipt)
        if critic_progress_observer is None:
            return receipt
        key = (receipt.epoch, receipt.minibatch)
        before = valuenorm_pre.get(key)
        after = valuenorm_post.get(key)
        changed = (
            _changed_valuenorm_fields_v1(before, after)
            if before is not None and after is not None
            else ()
        )
        valuenorm_receipt = receipt.valuenorm_receipt
        critic_progress_observer(
            {
                "schema_version": "b2r5i_re3_critic_progress_event_v1",
                "run_identity": update_id,
                "update_id": update_id,
                "stage": "S6_CRITIC_MINIBATCH_COMPLETE",
                "state_machine_stage": route_state.machine.current.value,
                "critic_epoch": receipt.epoch,
                "critic_minibatch": receipt.minibatch,
                "canonical_physical_rows": receipt.canonical_indices,
                "canonical_row_digest": canonical_digest_v1(
                    receipt.canonical_indices
                ),
                "raw_return_digest": receipt.raw_target_digest,
                "valuenorm_pre": before,
                "valuenorm_post": after,
                "changed_valuenorm_fields": changed,
                "canonical_valuenorm_mutation": bool(changed),
                "valuenorm_receipt_complete": valuenorm_receipt is not None,
                "critic_loss": receipt.loss_value,
                "critic_gradient_classification": receipt.gradient_classification,
                "critic_gradient_finite": math.isfinite(
                    receipt.aggregate_gradient_norm
                ),
                "critic_gradient_nonzero": receipt.aggregate_gradient_norm > 0.0,
                "critic_gradient_norm": receipt.aggregate_gradient_norm,
                "critic_clip_result": receipt.clip_result,
                "critic_parameter_fingerprint_before": receipt.critic_parameter_digest_before,
                "critic_parameter_fingerprint_after": receipt.critic_parameter_digest_after,
                "critic_optimizer_fingerprint_before": receipt.critic_optimizer_digest_before,
                "critic_optimizer_fingerprint_after": receipt.critic_optimizer_digest_after,
                "backward_permit_id": receipt.backward_permit_id,
                "optimizer_step_permit_id": receipt.step_permit_id,
                "valuenorm_permit_id": (
                    valuenorm_receipt.permit_id
                    if valuenorm_receipt is not None
                    else ""
                ),
                "loss_graph_evidence": receipt.loss_graph_evidence,
                "gradient_audit": receipt.gradient_audit,
                "loss_decomposition": receipt.loss_decomposition,
                "adam_state_before": receipt.adam_state_before,
                "adam_state_after": receipt.adam_state_after,
                "critic_step_receipt": receipt,
                "receipt_complete": bool(
                    receipt.critic_optimizer_mutated
                    and (
                        receipt.gradient_classification
                        == R4.VALID_ZERO_EFFECTIVE_UPDATE
                        or receipt.critic_parameter_mutated
                    )
                    and receipt.actors_unchanged
                    and receipt.gradients_clean_after
                ),
                "cumulative_critic_backward_count": len(critic_receipts),
                "cumulative_critic_optimizer_step_count": len(critic_receipts),
                "cumulative_live_valuenorm_update_count": sum(
                    int(item.valuenorm_receipt is not None)
                    for item in critic_receipts
                ),
            }
        )
        return receipt

    def observed_critic_sequence(*args: object, **kwargs: object) -> object:
        receipt = original_critic_sequence(*args, **kwargs)
        if critic_progress_observer is not None:
            critic_progress_observer(
                {
                    "schema_version": "b2r5i_re3_critic_progress_event_v1",
                    "run_identity": update_id,
                    "update_id": update_id,
                    "stage": "S6_CRITIC_SEQUENCE_COMPLETE",
                    "state_machine_stage": route_state.machine.current.value,
                    "complete_critic_sequence": True,
                    "completed_critic_minibatch_count": len(
                        receipt.step_receipts
                    ),
                    "observed_critic_backward_count": receipt.observed_backward_count,
                    "observed_critic_optimizer_step_count": receipt.observed_step_count,
                    "observed_live_valuenorm_update_count": receipt.observed_valuenorm_count,
                    "valid_nonzero_count": receipt.valid_nonzero_count,
                    "valid_zero_effective_count": receipt.valid_zero_effective_count,
                    "partitions_by_epoch": receipt.partitions_by_epoch,
                    "all_gradients_clean": receipt.gradients_clean_after,
                }
            )
        return receipt

    try:
        if factor_segment_observer is not None:
            R3.validate_factor_segment_contract_v1 = observed_factor_validator
            R3.execute_actor_sequence_v1 = observed_actor_sequence
        if critic_progress_observer is not None:
            R4.B2R4PermittedLiveValueNormProxyV1 = _ObservedLiveValueNormProxyV1
            R4._critic_loss_diagnostics_v1 = observed_loss_diagnostics
            R4.B2R4CriticStepReceiptV1 = observed_critic_receipt
            R4.execute_critic_sequence_v1 = observed_critic_sequence
        yield
    finally:
        R3.validate_factor_segment_contract_v1 = original_factor_validator
        R3.execute_actor_sequence_v1 = original_actor_sequence
        R4.B2R4PermittedLiveValueNormProxyV1 = original_valuenorm_proxy
        R4._critic_loss_diagnostics_v1 = original_loss_diagnostics
        R4.B2R4CriticStepReceiptV1 = original_critic_receipt
        R4.execute_critic_sequence_v1 = original_critic_sequence


class _PreMutationObservedActorInputsV1(Mapping[int, R3.B2R3ActorInputsV1]):
    """Flush bounded evidence after S4 and before the first actor mutation."""

    def __init__(
        self,
        *,
        values: Mapping[int, R3.B2R3ActorInputsV1],
        route_state: object,
        counter: object,
        payload: Mapping[str, object],
        observer: Callable[[Mapping[str, object]], None],
    ) -> None:
        self._values = values
        self._route_state = route_state
        self._counter = counter
        self._payload = payload
        self._observer = observer
        self.emitted = False

    def _emit_once(self) -> None:
        if self.emitted:
            return
        ordering = self._route_state.machine.evidence(pending_permit_count=0)
        expected = tuple(B2RUpdateStageV1)[:6]
        _require(
            ordering.history == expected
            and ordering.history[-1] is B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
            "pre-mutation observer did not run immediately after S4",
        )
        _require(
            self._counter.actor_step_executed == 0
            and self._counter.critic_step_executed == 0
            and self._counter.live_valuenorm_executed == 0,
            "learner mutation preceded durable evidence emission",
        )
        payload = {
            **self._payload,
            "current_s0_s4_state_history": tuple(
                stage.value for stage in ordering.history[:-1]
            ),
            "current_stage_before_first_actor_mutation": ordering.history[-1].value,
            "training_mode_entries": self._counter.training_mode_entries,
            "actor_optimizer_steps_before_emit": self._counter.actor_step_executed,
            "critic_optimizer_steps_before_emit": self._counter.critic_step_executed,
            "live_valuenorm_updates_before_emit": self._counter.live_valuenorm_executed,
            "durable_before_first_actor_optimizer_step": True,
        }
        self._observer(payload)
        self.emitted = True

    def __getitem__(self, key: int) -> R3.B2R3ActorInputsV1:
        self._emit_once()
        return self._values[key]

    def __iter__(self) -> Iterator[int]:
        self._emit_once()
        return iter(self._values)

    def __len__(self) -> int:
        self._emit_once()
        return len(self._values)


@dataclass(frozen=True, slots=True)
class B2R5IRealEvidenceAuditV1:
    environment_identity: str
    profile_name: str
    device: str
    resolved_T: int
    resolved_E: int
    resolved_M: int
    resolved_N: int
    real_environment_resets: int
    real_rollout_steps: int
    actor_order: tuple[int, ...]
    actor_dvm_rows: tuple[tuple[int, int], ...]
    actor_active_and_dvm_rows: tuple[tuple[int, int], ...]
    actor_expected_training_rows: tuple[tuple[int, int], ...]
    actor_observed_training_rows: tuple[tuple[int, int], ...]
    actor_evidence_reconciliation_digest: str
    actor_forced_rows: tuple[tuple[int, int], ...]
    actor_expected_backward: tuple[tuple[int, int], ...]
    actor_expected_step: tuple[tuple[int, int], ...]
    critic_physical_rows: int
    critic_expected_backward: int
    critic_expected_step: int
    valuenorm_expected_update: int
    event_return_compute_count: int
    terminal_coverage_classification: str
    historical_actor_observation_digest: str
    historical_available_action_mask_digest: str
    original_proposal_action_digest: str
    original_behavior_logprob_digest: str
    dvm_digest: str
    active_mask_digest: str
    effective_assignment_evidence_digest: str
    proposal_effective_authority_separate: bool
    selected_reason_grid_digest: str
    timeout_critic_evidence_digest: str
    event_return_result_digest: str
    critic_training_slice_digest: str
    final_structural_return_slot_digest: str
    next_current_bundle_digest: str
    schema_version: str = "b2r5i_real_evidence_audit_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R5IRealTransactionEvidenceV1:
    classification: str
    real_audit: B2R5IRealEvidenceAuditV1
    r5_transaction: R5.B2RFullLearnerUpdateEvidenceV1
    exact_execution_counts: tuple[tuple[str, object], ...]
    next_rollout_ready: bool
    checkpoint_weight_io: int
    training_campaigns: int
    evaluation_playback: int
    public_route_activations: int
    schema_version: str = "b2r5i_real_transaction_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


class _RealActorRolloverManagerV1:
    def __init__(self, *, route: object, completed_storages: Sequence[object]) -> None:
        self.route = route
        self.completed = tuple(completed_storages)
        self.final_bundle = route.current_decision_bundle
        self.final_actor_rnn = route._actor_rnn_states[-1].detach().clone().contiguous()
        self.final_actor_masks = route._actor_masks[-1].detach().clone().contiguous()
        self.new_storages: list[object | None] = [None] * len(self.completed)
        self.rollover_order: list[int] = []
        self.adapters: tuple[_RealActorStorageRolloverV1, ...] = ()

    def rollover(self, actor_id: int) -> None:
        _require(actor_id == len(self.rollover_order), "actor rollover order changed")
        old = self.completed[actor_id]
        active = old.active_masks[-1].detach().clone().contiguous()
        new = create_event_policy_actor_slot_storage_v2(
            episode_length=old.episode_length,
            agent_id=actor_id,
            current_decision_bundle=self.final_bundle,
            initial_active_masks=active,
        )
        _require(new.next_action_slot == 0, "new real actor storage cursor is not zero")
        _require(bool((new.action_ids == 0).all().item()), "new action storage is not clear")
        _require(
            bool((new.action_logprobs == 0).all().item()),
            "new behavior-logprob storage is not clear",
        )
        self.new_storages[actor_id] = new
        self.rollover_order.append(actor_id)
        self.adapters[actor_id]._current = new
        if len(self.rollover_order) != len(self.completed):
            return
        resolved = tuple(self.new_storages)
        _require(all(item is not None for item in resolved), "actor rollover set is incomplete")
        route = self.route
        route._actor_rnn_states.zero_()
        route._actor_rnn_states[0].copy_(self.final_actor_rnn)
        route._actor_masks.fill_(1.0)
        route._actor_masks[0].copy_(self.final_actor_masks)
        route._actor_storages = resolved
        route._critic_guard = capture_event_rollout_critic_guard_v2(route.critic)
        route._observe("rollout_slot0_rebuilt", self.final_bundle)


class _RealActorStorageRolloverV1:
    def __init__(self, *, actor_id: int, storage: object, manager: _RealActorRolloverManagerV1) -> None:
        self.actor_id = actor_id
        self._current = storage
        self._manager = manager

    @property
    def next_action_slot(self) -> int:
        return int(self._current.next_action_slot)

    @property
    def final_current_slot_digest(self) -> str:
        storage = self._manager.completed[self.actor_id]
        return _tensor_tuple_digest(
            storage.obs[-1],
            storage.available_actions[-1],
            storage.decision_valid_masks[-1],
            storage.active_masks[-1],
        )

    @property
    def slot_zero_digest(self) -> str:
        storage = self._current
        return _tensor_tuple_digest(
            storage.obs[0],
            storage.available_actions[0],
            storage.decision_valid_masks[0],
            storage.active_masks[0],
        )

    @property
    def storage_digest(self) -> str:
        storage = self._current
        return canonical_digest_v1(
            (
                self.actor_id,
                int(storage.next_action_slot),
                _tensor_digest(storage.obs),
                _tensor_digest(storage.available_actions),
                _tensor_digest(storage.decision_valid_masks),
                _tensor_digest(storage.active_masks),
                _tensor_digest(storage.action_ids),
                _tensor_digest(storage.action_logprobs),
            )
        )

    def rollover_from_final_current_slot(self) -> None:
        self._manager.rollover(self.actor_id)


class _RealRolloverResourcesV1:
    def __init__(self, *, route: object, completed_storages: Sequence[object]) -> None:
        self.critic_buffer = route.critic_buffer
        self.terminal_collector = route.collector
        manager = _RealActorRolloverManagerV1(
            route=route, completed_storages=completed_storages
        )
        adapters = tuple(
            _RealActorStorageRolloverV1(
                actor_id=actor_id, storage=storage, manager=manager
            )
            for actor_id, storage in enumerate(completed_storages)
        )
        manager.adapters = adapters
        self.actor_storages = adapters

    @property
    def critic_rollover_digest(self) -> str:
        buffer = self.critic_buffer
        return canonical_digest_v1(
            (
                int(buffer.step),
                _tensor_digest(buffer.share_obs),
                _tensor_digest(buffer.rnn_states_critic),
                _tensor_digest(buffer.masks),
                _tensor_digest(buffer.bad_masks),
                _tensor_digest(buffer.termination_reason),
                _tensor_digest(buffer.timeout_bootstrap_value_preds),
                _tensor_digest(buffer.timeout_bootstrap_masks),
                _tensor_digest(buffer._event_slot_written),
                bool(buffer._event_returns_computed),
            )
        )


def _resolved_config(
    *, route: object, actors: Sequence[object], critic: object,
    live_value_normalizer: object, algo_args: Mapping[str, object],
) -> B2RResolvedConfigV1:
    storages = tuple(route.actor_storages)
    train = algo_args["train"]
    algo = algo_args["algo"]
    T = int(route.episode_length)
    E = int(route.critic_buffer.n_rollout_threads)
    M = len(actors)
    N = int(storages[0].N)
    actor_epochs = int(algo["ppo_epoch"])
    actor_minibatches = int(algo["actor_num_mini_batch"])
    critic_epochs = int(algo["critic_epoch"])
    critic_minibatches = int(algo["critic_num_mini_batch"])
    _require(all(int(actor.ppo_epoch) == actor_epochs for actor in actors), "actor epoch config drift")
    _require(
        all(int(actor.actor_num_mini_batch) == actor_minibatches for actor in actors),
        "actor minibatch config drift",
    )
    _require(int(critic.critic_epoch) == critic_epochs, "critic epoch config drift")
    _require(
        int(critic.critic_num_mini_batch) == critic_minibatches,
        "critic minibatch config drift",
    )
    _require(bool(train["use_valuenorm"]) == (live_value_normalizer is not None), "ValueNorm config drift")
    settings = tuple(
        sorted(
            (
                ("clip_param", float(algo["clip_param"])),
                ("entropy_coef", float(algo["entropy_coef"])),
                ("max_grad_norm", float(algo["max_grad_norm"])),
                ("use_clipped_value_loss", bool(algo["use_clipped_value_loss"])),
                ("use_huber_loss", bool(algo["use_huber_loss"])),
                ("use_max_grad_norm", bool(algo["use_max_grad_norm"])),
                ("use_policy_active_masks", bool(algo["use_policy_active_masks"])),
                ("value_loss_coef", float(algo["value_loss_coef"])),
            )
        )
    )
    return B2RResolvedConfigV1(
        resolved_T=T,
        resolved_E=E,
        resolved_M=M,
        resolved_N=N,
        actor_epoch_count=actor_epochs,
        actor_minibatch_count=actor_minibatches,
        actor_partition_policy="reviewed_exact_coverage",
        critic_epoch_count=critic_epochs,
        critic_minibatch_count=critic_minibatches,
        critic_partition_policy="reviewed_exact_coverage",
        fixed_order=bool(algo["fixed_order"]),
        valuenorm_enabled=live_value_normalizer is not None,
        ppo_happo_settings=settings,
    )


def _derive_expected_terminal_keys_v1(
    *, completed_storages: Sequence[object], termination_reason: torch.Tensor,
    T: int, E: int,
) -> tuple[tuple[int, int, int], ...]:
    """Derive terminal keys from canonical slot identities and reason rows."""

    _require(
        tuple(termination_reason.shape) == (T, E, 1)
        and termination_reason.dtype is torch.int64,
        "terminal reason grid is invalid for expected-key derivation",
    )
    references = tuple(tuple(storage.decision_bundle_refs) for storage in completed_storages)
    _require(
        bool(references)
        and all(len(actor_refs) == T + 1 for actor_refs in references),
        "actor storage decision identity history is incomplete",
    )
    expected: list[tuple[int, int, int]] = []
    for slot in range(T):
        bundle = references[0][slot]
        _require(bundle is not None, "canonical slot decision identity is missing")
        _require(
            all(actor_refs[slot] is bundle for actor_refs in references[1:]),
            "actor storages disagree on canonical slot decision identity",
        )
        expectation = capture_event_learner_transition_expectation_v2(bundle)
        _require(
            expectation.env_ids == tuple(range(E)),
            "slot decision identity has wrong environment cardinality",
        )
        for env_id in range(E):
            reason = int(termination_reason[slot, env_id, 0].item())
            _require(
                reason in tuple(int(item) for item in TerminationReason),
                "terminal reason grid contains an unknown value",
            )
            if reason != int(TerminationReason.NONE):
                expected.append(expectation.expected_key(env_id).value)
    return tuple(expected)


def _reconcile_bound_actor_evidence_v1(
    *,
    update_id: str,
    completed_storages: Sequence[object],
    actor_inputs: Mapping[int, R3.B2R3ActorInputsV1],
    T: int,
    E: int,
    M: int,
    N: int,
) -> R5.B2R5ActorEvidenceReconciliationV1:
    """Bind canonical lifecycle/DVM rows to the exact actor-training population."""

    expected_rows: list[tuple[str, int, int, int, int, int]] = []
    observed_rows: list[tuple[str, int, int, int, int, int]] = []

    def _exact_with_nan(left: torch.Tensor, right: torch.Tensor) -> bool:
        if left.shape != right.shape or left.dtype != right.dtype or left.device != right.device:
            return False
        if not (left.is_floating_point() or left.is_complex()):
            return torch.equal(left, right)
        return torch.equal(torch.isnan(left), torch.isnan(right)) and torch.equal(
            torch.nan_to_num(left, nan=0.0), torch.nan_to_num(right, nan=0.0)
        )

    _require(
        len(completed_storages) == M and set(actor_inputs) == set(range(M)),
        "actor evidence population has wrong actor cardinality",
    )
    for actor_id, storage in enumerate(completed_storages):
        inputs = actor_inputs[actor_id]
        references = tuple(storage.decision_bundle_refs)
        _require(
            len(references) == T + 1,
            "actor evidence decision identity history is incomplete",
        )
        _require(
            _exact_with_nan(inputs.obs, storage.obs[:-1].reshape(T * E, storage.obs_dim))
            and torch.equal(
                inputs.available_actions,
                storage.available_actions[:-1].reshape(T * E, N + 1),
            )
            and torch.equal(
                inputs.decision_valid_mask,
                storage.decision_valid_masks[:-1].reshape(T * E, 1),
            )
            and torch.equal(
                inputs.active_mask,
                storage.active_masks[:-1].to(torch.bool).reshape(T * E, 1),
            )
            and torch.equal(inputs.actions, storage.action_ids.reshape(T * E, 1))
            and _exact_with_nan(
                inputs.behavior_old_logprobs,
                storage.action_logprobs.reshape(T * E, 1),
            ),
            "actor evidence inputs differ from completed canonical storage",
        )
        for slot in range(T):
            bundle = references[slot]
            _require(bundle is not None, "actor evidence slot identity is missing")
            identity = bundle.evidence_identity
            _require(
                identity.M == M
                and identity.N == N
                and identity.num_envs == E,
                "actor evidence slot identity authority is inconsistent",
            )
            bundle.validate_evidence_snapshot(bundle.evidence_snapshot)
            for env_id in range(E):
                flat = slot * E + env_id
                expected_dvm = bool(
                    bundle.decision_valid_mask[env_id, actor_id, 0].item()
                )
                expected_active = bool(storage.active_masks[slot, env_id, 0].item())
                observed_dvm = bool(inputs.decision_valid_mask[flat, 0].item())
                observed_active = bool(inputs.active_mask[flat, 0].item())
                row_kind = int(bundle.row_kind[env_id, actor_id].item())
                proposal_present = bool(
                    bundle.policy_proposal_present_mask[env_id, actor_id, 0].item()
                )
                forced_id = int(bundle.forced_action_id[env_id, actor_id, 0].item())
                action_id = int(inputs.actions[flat, 0].item())
                logprob = inputs.behavior_old_logprobs[flat, 0]
                if expected_dvm:
                    if (
                        row_kind != int(EventPolicyRowKind.POLICY_DECISION_ROW)
                        or not proposal_present
                        or forced_id != POLICY_FORCED_ACTION_INVALID_ID
                        or action_id < 0
                        or action_id > N
                        or not bool(inputs.available_actions[flat, action_id].item())
                        or not bool(torch.isfinite(logprob).item())
                        or not bool(torch.isfinite(inputs.obs[flat]).all().item())
                    ):
                        R5._fail(
                            "canonical DVM row is missing required actor policy evidence",
                            stop_code=R5.STOP_ACTOR_EVIDENCE_MISSING,
                            stage="real_actor_evidence_binding",
                            field_name="DVM actor observation/action/behavior-logprob",
                            expected=(actor_id, slot, env_id, "complete policy evidence"),
                            observed=(row_kind, proposal_present, forced_id, action_id),
                        )
                else:
                    if (
                        proposal_present
                        or row_kind == int(EventPolicyRowKind.POLICY_DECISION_ROW)
                        or action_id != forced_id
                        or float(logprob.item()) != FORCED_ROW_LOGPROB_SENTINEL
                    ):
                        R5._fail(
                            "continuation/noop row carries unexpected fresh actor evidence",
                            stop_code=R5.STOP_ACTOR_EVIDENCE_UNEXPECTED,
                            stage="real_actor_evidence_binding",
                            field_name="off-DVM actor evidence",
                            expected=(False, forced_id, FORCED_ROW_LOGPROB_SENTINEL),
                            observed=(proposal_present, action_id, float(logprob.item())),
                        )
                row_identity = (
                    update_id,
                    actor_id,
                    slot,
                    env_id,
                    int(identity.episode_generations[env_id]),
                    int(identity.transition_generations[env_id]),
                )
                if expected_dvm and expected_active:
                    expected_rows.append(row_identity)
                if observed_dvm and observed_active:
                    observed_rows.append(row_identity)
    return R5.reconcile_actor_evidence_v1(
        update_id=update_id,
        actor_ids=tuple(range(M)),
        expected_actor_rows=tuple(expected_rows),
        observed_actor_rows=tuple(observed_rows),
    )


def execute_real_isaac_single_transaction_v1(
    *,
    repository_head: str,
    dirty_state_classification: str,
    repo_source_hashes: tuple[B2RSourceDigestV1, ...],
    installed_harl_source_hashes: tuple[B2RSourceDigestV1, ...],
    route: object,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    algo_args: Mapping[str, object],
    environment_identity: str,
    profile_name: str,
    real_environment_resets: int,
    real_rollout_steps: int,
    precedence_resolution_evidence_digest: str,
    terminal_correlation_evidence_digest: str,
    timeout_critic_evidence_digest: str,
    effective_assignment_evidence_digest: str,
    proposal_effective_authority_separate: bool,
    update_id: str = "b2-r5i-real-isaac-single-transaction-0001",
    order_seed: int = 1,
    classification: str = R5I_CLASSIFICATION,
    pre_mutation_observer: Callable[[Mapping[str, object]], None] | None = None,
    factor_segment_observer: Callable[[Mapping[str, object]], None] | None = None,
    critic_progress_observer: Callable[[Mapping[str, object]], None] | None = None,
    post_failure_observer: Callable[[Mapping[str, object]], None] | None = None,
) -> B2R5IRealTransactionEvidenceV1:
    """Bind one completed real rollout and execute exactly one R5 transaction."""

    _require(not bool(route.poisoned), "real route is already poisoned")
    completed_storages = tuple(route.actor_storages)
    config = _resolved_config(
        route=route,
        actors=actors,
        critic=critic,
        live_value_normalizer=live_value_normalizer,
        algo_args=algo_args,
    )
    T, E, M, N, B = (
        config.resolved_T,
        config.resolved_E,
        config.resolved_M,
        config.resolved_N,
        config.B,
    )
    buffer = route.critic_buffer
    _require(len(completed_storages) == M, "real actor-storage count drifted")
    _require(
        all(storage.next_action_slot == T for storage in completed_storages),
        "real actor rollout is incomplete",
    )
    _require(bool(buffer._event_slot_written.all().item()), "real critic rollout is incomplete")
    _require(not bool(buffer._event_returns_computed), "real event returns were already computed")
    expected_terminal_keys = _derive_expected_terminal_keys_v1(
        completed_storages=completed_storages,
        termination_reason=buffer.termination_reason,
        T=T,
        E=E,
    )
    terminal_reconciliation = R5.reconcile_terminal_evidence_v1(
        expected_terminal_keys=expected_terminal_keys,
        observed_terminal_keys=tuple(route.collector.consumed_terminal_keys),
    )
    _require(real_environment_resets == 1 and real_rollout_steps == T, "real run count differs from the bounded gate")

    with torch.inference_mode():
        final_values, _ = route.critic.get_values(
            buffer.share_obs[-1], buffer.rnn_states_critic[-1], buffer.masks[-1]
        )
    _require(
        tuple(final_values.shape) == (E, 1)
        and not final_values.requires_grad
        and bool(torch.isfinite(final_values).all().item()),
        "real final critic value is invalid",
    )
    route._observe("ordinary_final_next_value", final_values)
    event_result = buffer.compute_event_returns(
        final_values.detach().clone().contiguous(), live_value_normalizer
    )
    route._observe("I5b_compute_event_returns", event_result)
    event_returns = event_result.returns
    _require(
        tuple(event_returns.shape) == (T, E, 1)
        and bool(torch.isfinite(event_returns).all().item()),
        "real event return result is invalid",
    )
    _require(torch.equal(event_returns, buffer.returns[:-1]), "real result/storage values differ")
    _require(event_returns.data_ptr() != buffer.returns[:-1].data_ptr(), "real result/storage alias")
    with torch.inference_mode():
        value_baseline = live_value_normalizer.denormalize(buffer.value_preds[:-1])
    advantages = (buffer.returns[:-1] - value_baseline).detach().clone().contiguous()
    _require(bool(torch.isfinite(advantages).all().item()), "real advantages are nonfinite")
    route._observe("event_advantages", advantages)

    base = B2RUpdateAuthorityV1(
        update_id=update_id,
        slice_identity="B2-R1",
        repository_head=repository_head,
        dirty_state_classification=dirty_state_classification,
        repo_source_hashes=repo_source_hashes,
        installed_harl_source_hashes=installed_harl_source_hashes,
        resolved_config=config,
        authorization_scope=(
            "r1_contracts",
            "r2_unique_backward",
            "r3_actor_sequence",
            "r4_critic_valuenorm_sequence",
            "r5_private_full_transaction",
            "r5i_real_isaac_evidence_binding",
        ),
        forbidden_operations=(
            "training_campaign",
            "evaluation_playback",
            "checkpoint_weight_io",
            "public_route_activation",
            "r6",
            "r7",
        ),
    )
    order = R3.B2R3ActorOrderFreezerV1(base).freeze(rng_seed=order_seed)
    initial_factor = torch.ones(
        (T, E, 1), dtype=torch.float32, device=buffer.share_obs.device
    )
    actor_partitions = build_exact_partitions_v1(
        B=B,
        epoch_count=config.actor_epoch_count,
        minibatch_count=config.actor_minibatch_count,
        partition_policy=config.actor_partition_policy,
    )

    actor_inputs: dict[int, R3.B2R3ActorInputsV1] = {}
    dvm_indices: dict[int, tuple[int, ...]] = {}
    active_indices: dict[int, tuple[int, ...]] = {}
    normalized_advantage_digests: list[str] = []
    for actor_id, storage in enumerate(completed_storages):
        dvm_grid = storage.decision_valid_masks[:-1]
        active_grid = storage.active_masks[:-1].to(torch.bool)
        normalization = normalize_event_policy_advantages_v2(
            advantages=advantages,
            policy_loss_mask=dvm_grid & active_grid,
        )
        normalized = normalization.normalized_advantages.reshape(B, 1)
        normalized_advantage_digests.append(_tensor_digest(normalized))
        inputs = R3.B2R3ActorInputsV1(
            obs=storage.obs[:-1].reshape(B, storage.obs_dim),
            rnn_states=route._actor_rnn_states[:-1, :, actor_id].reshape(
                B, *route._actor_rnn_states.shape[-2:]
            ),
            actions=storage.action_ids.reshape(B, 1),
            masks=route._actor_masks[:-1, :, actor_id].reshape(B, 1),
            available_actions=storage.available_actions[:-1].reshape(B, N + 1),
            behavior_old_logprobs=storage.action_logprobs.reshape(B, 1),
            advantages=normalized,
            decision_valid_mask=dvm_grid.reshape(B, 1),
            active_mask=active_grid.reshape(B, 1),
        )
        actor_inputs[actor_id] = inputs
        dvm_indices[actor_id] = tuple(
            int(item) for item in inputs.decision_valid_mask.nonzero(as_tuple=False)[:, 0].tolist()
        )
        active_indices[actor_id] = tuple(
            int(item) for item in inputs.active_mask.nonzero(as_tuple=False)[:, 0].tolist()
        )

    actor_evidence_reconciliation = _reconcile_bound_actor_evidence_v1(
        update_id=update_id,
        completed_storages=completed_storages,
        actor_inputs=actor_inputs,
        T=T,
        E=E,
        M=M,
        N=N,
    )

    behavior_by_actor = tuple(
        (actor_id, _tensor_digest(actor_inputs[actor_id].behavior_old_logprobs))
        for actor_id in range(M)
    )
    actor_authority = R3.B2R3MutationAuthorityV1(
        base_authority=base,
        mutation_id=f"{update_id}-actor",
        slice_identity="B2-R3",
        order_evidence=order,
        behavior_digest_by_actor=behavior_by_actor,
        allowed_operations=(
            "actor_zero_grad",
            "actor_backward",
            "actor_gradient_clip",
            "actor_optimizer_step",
            "actor_post_step_evaluation",
            "factor_attribution",
        ),
        forbidden_operations=(
            "critic_backward",
            "critic_optimizer_step",
            "critic_parameter_mutation",
            "live_valuenorm_update",
            "scheduler_step",
            "full_learner_update",
            "isaac",
            "training",
            "evaluation_playback",
            "checkpoint_weight_io",
            "public_route_activation",
        ),
    )
    critic_authority = R4.B2R4MutationAuthorityV1(
        base_authority=base,
        mutation_id=f"{update_id}-critic",
        slice_identity="B2-R4",
        allowed_operations=(
            "live_valuenorm_update",
            "critic_backward",
            "critic_gradient_clip",
            "critic_optimizer_step",
        ),
        forbidden_operations=(
            "actor_backward",
            "actor_optimizer_step",
            "actor_parameter_mutation",
            "scheduler_step",
            "full_learner_update",
            "isaac",
            "training",
            "evaluation_playback",
            "checkpoint_weight_io",
            "public_route_activation",
        ),
    )
    authority = R5.B2R5FullUpdateAuthorityV1(
        base_authority=base,
        actor_authority=actor_authority,
        critic_authority=critic_authority,
        transaction_id=f"transaction-{update_id}",
        slice_identity="B2-R5",
        allowed_operations=(
            "actor_sequence",
            "critic_sequence",
            "live_valuenorm_update",
            "training_mode_entry",
            "rollout_mode_restore",
            "critic_rollover",
            "terminal_ledger_reset",
            "actor_storage_rollover",
        ),
        forbidden_operations=(
            "isaac",
            "real_environment_rollout",
            "training_campaign",
            "evaluation_playback",
            "checkpoint_weight_io",
            "public_route_activation",
            "r6",
            "r7",
            "scheduler_redesign",
        ),
    )
    actor_plan = build_actor_update_plan_v1(
        authority=base,
        authority_config_digest=base.config_digest,
        actor_permutation=order.actor_order,
        approved_partitions_by_epoch=actor_partitions,
        dvm_indices_by_actor=dvm_indices,
        active_indices_by_actor=active_indices,
        factor_input_digest=_tensor_digest(initial_factor),
        optimizer_step_policy="match_backward",
    )
    critic_partitions = build_exact_partitions_v1(
        B=B,
        epoch_count=config.critic_epoch_count,
        minibatch_count=config.critic_minibatch_count,
        partition_policy=config.critic_partition_policy,
    )
    raw_target = buffer.returns[:-1].reshape(B, 1)
    critic_plan = build_critic_update_plan_v1(
        authority=base,
        authority_config_digest=base.config_digest,
        approved_partitions_by_epoch=critic_partitions,
        raw_target_digest=_tensor_digest(raw_target),
        optimizer_step_policy="match_backward",
    )
    critic_inputs = R4.B2R4CriticInputsV1(
        shared_obs=buffer.share_obs[:-1].reshape(B, -1),
        rnn_states=buffer.rnn_states_critic[:-1].reshape(B, *buffer.rnn_states_critic.shape[-2:]),
        masks=buffer.masks[:-1].reshape(B, 1),
        value_preds=buffer.value_preds[:-1].reshape(B, 1).detach().clone().contiguous(),
        returns_storage=buffer.returns,
    )

    actor_obs_digest = canonical_digest_v1(
        tuple(_tensor_digest(actor_inputs[index].obs) for index in range(M))
    )
    availability_digest = canonical_digest_v1(
        tuple(_tensor_digest(actor_inputs[index].available_actions) for index in range(M))
    )
    proposal_digest = canonical_digest_v1(
        tuple(_tensor_digest(actor_inputs[index].actions) for index in range(M))
    )
    behavior_digest = canonical_digest_v1(behavior_by_actor)
    dvm_digest = canonical_digest_v1(
        tuple(_tensor_digest(actor_inputs[index].decision_valid_mask) for index in range(M))
    )
    active_digest = canonical_digest_v1(
        tuple(_tensor_digest(actor_inputs[index].active_mask) for index in range(M))
    )
    reason_digest = _tensor_digest(buffer.termination_reason)
    timeout_sidecar_digest = _tensor_tuple_digest(
        buffer.timeout_bootstrap_masks, buffer.timeout_bootstrap_value_preds
    )
    domain_values = set(int(item) for item in buffer.termination_reason.flatten().tolist())
    termination_domain_valid = domain_values.issubset({0, 1, 2, 3})
    frozen = B2RFrozenTrainingInputsV1(
        update_id=base.update_id,
        authority_config_digest=base.config_digest,
        actor_canonical_identities=tuple(
            (actor_id, t, env_id)
            for actor_id in range(M)
            for t in range(T)
            for env_id in range(E)
        ),
        historical_actor_observation_digest=actor_obs_digest,
        historical_available_action_mask_digest=availability_digest,
        original_proposal_action_digest=proposal_digest,
        original_behavior_logprob_digest=behavior_digest,
        dvm_digest=dvm_digest,
        active_mask_digest=active_digest,
        selected_reason_grid_digest=reason_digest,
        termination_domain_valid=termination_domain_valid,
        exactly_one_selected_category=True,
        precedence_resolution_evidence_digest=precedence_resolution_evidence_digest,
        terminal_correlation_evidence_digest=terminal_correlation_evidence_digest,
        timeout_critic_evidence_digest=timeout_critic_evidence_digest,
        event_return_result_digest=_tensor_digest(event_returns),
        critic_training_slice_digest=_tensor_digest(raw_target),
        final_structural_return_slot_digest=_tensor_digest(buffer.returns[-1]),
        return_equality_proof="exact real event result equals critic_buffer.returns[:-1]",
        return_no_alias_proof="real event result is a detached non-alias producer result",
        baseline_value_digest=_tensor_digest(value_baseline),
        advantage_digest=canonical_digest_v1(tuple(normalized_advantage_digests)),
    )
    resources = _RealRolloverResourcesV1(
        route=route, completed_storages=completed_storages
    )
    rollout = R5.B2R5RolloutCompleteEvidenceV1(
        update_id=base.update_id,
        authority_config_digest=base.config_digest,
        resolved_T=T,
        resolved_E=E,
        resolved_M=M,
        resolved_N=N,
        actor_storage_complete=tuple(True for _ in range(M)),
        critic_transition_storage_complete=True,
        terminal_learner_evidence_complete=True,
        termination_reason_digest=reason_digest,
        timeout_sidecar_digest=timeout_sidecar_digest,
        proposal_action_logprob_digest=canonical_digest_v1((proposal_digest, behavior_digest)),
        dvm_active_availability_digest=canonical_digest_v1(
            (dvm_digest, active_digest, availability_digest)
        ),
        actor_evidence_expected_rows=(
            actor_evidence_reconciliation.expected_actor_rows
        ),
        actor_evidence_observed_rows=(
            actor_evidence_reconciliation.observed_actor_rows
        ),
        actor_evidence_reconciliation_digest=(
            actor_evidence_reconciliation.evidence_digest
        ),
        current_final_slot_digest_by_actor=tuple(
            (index, storage.final_current_slot_digest)
            for index, storage in enumerate(resources.actor_storages)
        ),
        actor_buffer_cursors=tuple(T for _ in range(M)),
        critic_buffer_cursor=int(buffer.step),
        expected_terminal_keys=terminal_reconciliation.expected_terminal_keys,
        terminal_consumption_keys=tuple(route.collector.consumed_terminal_keys),
        terminal_reconciliation_digest=terminal_reconciliation.evidence_digest,
        terminal_evidence_is_historical_pre_reset=True,
        runtime_ack_is_separate_from_learner_consumption=True,
        final_value_evaluated=True,
        selected_termination_domain_valid=termination_domain_valid,
        event_returns_compute_count=1,
    )
    immutable_plan = R5.B2R5ImmutableUpdatePlanV1(
        update_id=base.update_id,
        authority_config_digest=base.config_digest,
        actor_order=order.actor_order,
        actor_plan_digest=actor_plan.plan_digest,
        critic_plan_digest=critic_plan.plan_digest,
        actor_expected_backward=actor_plan.expected_backward_count_by_actor,
        actor_expected_step=actor_plan.expected_optimizer_step_count_by_actor,
        critic_expected_backward=critic_plan.expected_backward_count,
        critic_expected_step=critic_plan.expected_optimizer_step_count,
        valuenorm_expected_update=critic_plan.expected_valuenorm_update_count,
        lifecycle_evidence_digest=rollout.evidence_digest,
        returns_evidence_digest=canonical_digest_v1(
            (
                _tensor_digest(event_returns),
                _tensor_digest(raw_target),
                _tensor_digest(buffer.returns[-1]),
            )
        ),
        initial_component_state_digest=R5._component_state_digest(
            actors, critic, live_value_normalizer
        ),
        initial_factor_digest=_tensor_digest(initial_factor),
        expected_stage_progression=tuple(B2RUpdateStageV1),
    )
    counter = R5.B2R5ExecutionCounterV1(M)
    route_state = R5.B2R5TransactionRouteStateV1()
    initial_actors, initial_critic, initial_valuenorm = R3._capture_components_v1(
        actors=actors,
        critic=critic,
        live_value_normalizer=live_value_normalizer,
    )
    terminal_keys = tuple(route.collector.consumed_terminal_keys)
    mask_evidence = tuple(
        (
            actor_id,
            tuple(int(item) for item in actor_inputs[actor_id].decision_valid_mask.shape),
            tuple(int(item) for item in actor_inputs[actor_id].active_mask.shape),
            R3._canonical_true_row_indices_v1(actor_inputs[actor_id].decision_valid_mask),
            R3._canonical_true_row_indices_v1(
                actor_inputs[actor_id].decision_valid_mask
                & actor_inputs[actor_id].active_mask
            ),
            R3._canonical_true_row_indices_v1(~actor_inputs[actor_id].decision_valid_mask),
        )
        for actor_id in range(M)
    )
    row_audits = tuple(
        (
            actor_id,
            len(dvm_rows) - len(set(dvm_rows)),
            sum(int(row < 0 or row >= B) for row in dvm_rows),
            len(off_dvm_rows) - len(set(off_dvm_rows)),
            sum(int(row < 0 or row >= B) for row in off_dvm_rows),
        )
        for actor_id, _, _, dvm_rows, _, off_dvm_rows in mask_evidence
    )
    _require(
        all(audit[1:] == (0, 0, 0, 0) for audit in row_audits),
        "real canonical-row audit failed before mutation",
    )
    pre_mutation_payload = {
        "schema_version": "b2r5i_re_pre_mutation_durable_evidence_v1",
        "run_identity": update_id,
        "update_id": update_id,
        "repository_head": repository_head,
        "repo_source_hashes": repo_source_hashes,
        "installed_harl_source_hashes": installed_harl_source_hashes,
        "config_digest": base.config_digest,
        "resolved_config": config,
        "actor_order": order.actor_order,
        "actor_plan_digest": actor_plan.plan_digest,
        "critic_plan_digest": critic_plan.plan_digest,
        "expected_actor_backward": actor_plan.expected_backward_count_by_actor,
        "expected_actor_optimizer_step": actor_plan.expected_optimizer_step_count_by_actor,
        "expected_critic_backward": critic_plan.expected_backward_count,
        "expected_critic_optimizer_step": critic_plan.expected_optimizer_step_count,
        "expected_live_valuenorm_update": critic_plan.expected_valuenorm_update_count,
        "actor_observation_digest": actor_obs_digest,
        "critic_observation_digest": _tensor_digest(critic_inputs.shared_obs),
        "available_action_digest": availability_digest,
        "proposal_action_digest": proposal_digest,
        "rollout_behavior_logprob_digest": behavior_digest,
        "dvm_digest": dvm_digest,
        "active_mask_digest": active_digest,
        "mask_evidence_by_actor": mask_evidence,
        "canonical_row_audits": row_audits,
        "actor_evidence_expected_rows": actor_evidence_reconciliation.expected_actor_rows,
        "actor_evidence_observed_rows": actor_evidence_reconciliation.observed_actor_rows,
        "actor_evidence_expected_count_by_actor": actor_evidence_reconciliation.expected_count_by_actor,
        "actor_evidence_observed_count_by_actor": actor_evidence_reconciliation.observed_count_by_actor,
        "actor_evidence_reconciliation_digest": actor_evidence_reconciliation.evidence_digest,
        "lifecycle_rollout_evidence_digest": rollout.evidence_digest,
        "effective_assignment_evidence_digest": effective_assignment_evidence_digest,
        "proposal_effective_authority_separate": proposal_effective_authority_separate,
        "terminal_reason_grid_digest": reason_digest,
        "timeout_sidecar_digest": timeout_sidecar_digest,
        "timeout_critic_evidence_digest": timeout_critic_evidence_digest,
        "terminal_ledger_keys": terminal_keys,
        "expected_terminal_keys": terminal_reconciliation.expected_terminal_keys,
        "terminal_reconciliation_digest": terminal_reconciliation.evidence_digest,
        "terminal_ledger_key_digest": canonical_digest_v1(terminal_keys),
        "terminal_ledger_key_count": len(terminal_keys),
        "event_return_digest": _tensor_digest(event_returns),
        "returns_training_slice_digest": _tensor_digest(raw_target),
        "final_structural_slot_digest": _tensor_digest(buffer.returns[-1]),
        "event_return_compute_count": 1,
        "initial_factor_digest": _tensor_digest(initial_factor),
        "initial_actor_fingerprints": tuple(
            (
                actor_id,
                fingerprint.fingerprint_digest,
                R3._parameter_digest(fingerprint),
                R3._optimizer_digest(fingerprint),
            )
            for actor_id, fingerprint in enumerate(initial_actors)
        ),
        "initial_critic_fingerprint": (
            initial_critic.fingerprint_digest,
            R3._parameter_digest(initial_critic),
            R3._optimizer_digest(initial_critic),
        ),
        "initial_valuenorm_fingerprint": initial_valuenorm.fingerprint_digest,
        "initial_valuenorm_canonical_evidence": (
            _canonical_valuenorm_observation_v1(live_value_normalizer)
        ),
        "initial_component_state_digest": immutable_plan.initial_component_state_digest,
    }
    observed_actor_inputs: Mapping[int, R3.B2R3ActorInputsV1] = actor_inputs
    durable_inputs: _PreMutationObservedActorInputsV1 | None = None
    if pre_mutation_observer is not None:
        durable_inputs = _PreMutationObservedActorInputsV1(
            values=actor_inputs,
            route_state=route_state,
            counter=counter,
            payload=pre_mutation_payload,
            observer=pre_mutation_observer,
        )
        observed_actor_inputs = durable_inputs
    try:
        with _scoped_attempt4_progress_observers_v1(
            update_id=update_id,
            actor_inputs=actor_inputs,
            route_state=route_state,
            factor_segment_observer=factor_segment_observer,
            critic_progress_observer=critic_progress_observer,
        ):
            transaction = R5.execute_full_learner_transaction_v1(
                authority=authority,
                rollout_evidence=rollout,
                frozen_inputs=frozen,
                immutable_plan=immutable_plan,
                actor_plan=actor_plan,
                critic_plan=critic_plan,
                actors=actors,
                critic=critic,
                live_value_normalizer=live_value_normalizer,
                actor_inputs=observed_actor_inputs,
                initial_factor=initial_factor,
                critic_inputs=critic_inputs,
                event_returns_result=event_returns,
                rollover_resources=resources,
                route_state=route_state,
                counter=counter,
            )
        _require(
            durable_inputs is None or durable_inputs.emitted,
            "pre-mutation durable evidence was not emitted",
        )
        _require(transaction.transaction_success, "R5 transaction did not succeed")
        _require(not bool(route.poisoned), "real route became poisoned")
        _require(tuple(route.actor_storages) == tuple(item._current for item in resources.actor_storages), "route actor storages did not adopt rollover")
        route._current_decision_validator(route.current_decision_bundle)
        current_bundle = route.current_decision_bundle
        _require(
            all(
                torch.equal(storage.obs[0], current_bundle.evidence_snapshot.actor_obs[:, actor_id])
                and torch.equal(storage.available_actions[0], current_bundle.runner_available_actions[:, actor_id])
                and torch.equal(storage.decision_valid_masks[0], current_bundle.decision_valid_mask[:, actor_id])
                and torch.equal(storage.active_masks[0], completed_storages[actor_id].active_masks[-1])
                and storage.next_action_slot == 0
                for actor_id, storage in enumerate(route.actor_storages)
            )
            and not route.collector.consumed_terminal_keys
            and buffer.step == 0
            and not bool(buffer._event_returns_computed)
            and not bool(buffer._event_slot_written.any().item())
            and not any(actor.actor.training for actor in actors)
            and not critic.critic.training
            and not route_state.route_poisoned,
            "next-rollout read-only consistency check failed",
        )
        next_current_digest = canonical_digest_v1(
            (
                _tensor_digest(current_bundle.evidence_snapshot.actor_obs),
                _tensor_digest(current_bundle.evidence_snapshot.runner_share_obs),
                _tensor_digest(current_bundle.runner_available_actions),
                _tensor_digest(current_bundle.decision_valid_mask),
                current_bundle.evidence_identity.episode_generations,
                current_bundle.evidence_identity.transition_generations,
            )
        )
        dvm_counts = tuple(
            (actor_id, int(actor_inputs[actor_id].decision_valid_mask.sum().item()))
            for actor_id in range(M)
        )
        active_dvm_counts = tuple(
            (
                actor_id,
                int(
                    (
                        actor_inputs[actor_id].decision_valid_mask
                        & actor_inputs[actor_id].active_mask
                    ).sum().item()
                ),
            )
            for actor_id in range(M)
        )
        forced_counts = tuple((actor_id, B - count) for actor_id, count in dvm_counts)
        terminal_class = (
            "REAL-ISAAC-FULL-TRANSACTION-WITH-TERMINAL-AUTORESET-EVIDENCE"
            if any(value != 0 for value in domain_values)
            else "REAL-ISAAC-FULL-TRANSACTION-NONTERMINAL-ONLY"
        )
        audit = B2R5IRealEvidenceAuditV1(
            environment_identity=environment_identity,
            profile_name=profile_name,
            device=str(buffer.share_obs.device),
            resolved_T=T,
            resolved_E=E,
            resolved_M=M,
            resolved_N=N,
            real_environment_resets=real_environment_resets,
            real_rollout_steps=real_rollout_steps,
            actor_order=order.actor_order,
            actor_dvm_rows=dvm_counts,
            actor_active_and_dvm_rows=active_dvm_counts,
            actor_expected_training_rows=(
                actor_evidence_reconciliation.expected_count_by_actor
            ),
            actor_observed_training_rows=(
                actor_evidence_reconciliation.observed_count_by_actor
            ),
            actor_evidence_reconciliation_digest=(
                actor_evidence_reconciliation.evidence_digest
            ),
            actor_forced_rows=forced_counts,
            actor_expected_backward=actor_plan.expected_backward_count_by_actor,
            actor_expected_step=actor_plan.expected_optimizer_step_count_by_actor,
            critic_physical_rows=B,
            critic_expected_backward=critic_plan.expected_backward_count,
            critic_expected_step=critic_plan.expected_optimizer_step_count,
            valuenorm_expected_update=critic_plan.expected_valuenorm_update_count,
            event_return_compute_count=1,
            terminal_coverage_classification=terminal_class,
            historical_actor_observation_digest=actor_obs_digest,
            historical_available_action_mask_digest=availability_digest,
            original_proposal_action_digest=proposal_digest,
            original_behavior_logprob_digest=behavior_digest,
            dvm_digest=dvm_digest,
            active_mask_digest=active_digest,
            effective_assignment_evidence_digest=effective_assignment_evidence_digest,
            proposal_effective_authority_separate=proposal_effective_authority_separate,
            selected_reason_grid_digest=reason_digest,
            timeout_critic_evidence_digest=timeout_critic_evidence_digest,
            event_return_result_digest=_tensor_digest(event_returns),
            critic_training_slice_digest=_tensor_digest(raw_target),
            final_structural_return_slot_digest=_tensor_digest(buffer.returns[-1]),
            next_current_bundle_digest=next_current_digest,
        )
        exact_counts = (
            ("successful_real_full_learner_transactions", counter.successful_transactions),
            ("s10_entries", counter.s10_entries),
            ("actor_backward_by_actor", tuple(counter.actor_backward_by_actor)),
            ("actor_optimizer_step_by_actor", tuple(counter.actor_step_by_actor)),
            ("critic_backward", counter.critic_backward_executed),
            ("critic_optimizer_step", counter.critic_step_executed),
            ("live_valuenorm_update", counter.live_valuenorm_executed),
            ("training_mode_entries", counter.training_mode_entries),
            ("rollout_mode_restorations", counter.rollout_mode_restorations),
            ("critic_rollovers", counter.critic_rollovers),
            ("terminal_ledger_resets", counter.terminal_ledger_resets),
            ("actor_storage_rollovers", counter.actor_storage_rollovers),
        )
        return B2R5IRealTransactionEvidenceV1(
            classification=classification,
            real_audit=audit,
            r5_transaction=transaction,
            exact_execution_counts=exact_counts,
            next_rollout_ready=True,
            checkpoint_weight_io=0,
            training_campaigns=0,
            evaluation_playback=0,
            public_route_activations=0,
        )
    except BaseException as exc:
        if route_state.last_failure is None:
            route_state.record_failure(
                stop_code=getattr(
                    exc,
                    "stop_code",
                    "STOP — B2-R5I-RE2 DURABLE_OBSERVABILITY",
                ),
                actor_steps=counter.actor_step_executed,
                critic_steps=counter.critic_step_executed,
                valuenorm_updates=counter.live_valuenorm_executed,
            )
        if route_state.route_poisoned:
            route._poisoned = True
        if post_failure_observer is not None:
            try:
                post_failure_observer(
                    {
                        "schema_version": "b2r5i_re_post_failure_durable_evidence_v1",
                        "run_identity": update_id,
                        "update_id": update_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "state_history": tuple(
                            stage.value
                            for stage in route_state.machine.evidence(
                                pending_permit_count=0
                            ).history
                        ),
                        "failure_evidence": route_state.last_failure,
                        "partial_update": bool(
                            counter.actor_step_executed
                            or counter.critic_step_executed
                            or counter.live_valuenorm_executed
                        ),
                        "route_poisoned": route_state.route_poisoned,
                        "actor_backward_by_actor": tuple(counter.actor_backward_by_actor),
                        "actor_optimizer_step_by_actor": tuple(counter.actor_step_by_actor),
                        "critic_backward": counter.critic_backward_executed,
                        "critic_optimizer_step": counter.critic_step_executed,
                        "live_valuenorm_update": counter.live_valuenorm_executed,
                        "s10_entries": counter.s10_entries,
                        "pre_mutation_evidence_emitted": bool(
                            durable_inputs is not None and durable_inputs.emitted
                        ),
                    }
                )
            except BaseException as observer_error:
                setattr(exc, "durable_observer_error", f"{type(observer_error).__name__}: {observer_error}")
        raise


__all__: tuple[str, ...] = ()
