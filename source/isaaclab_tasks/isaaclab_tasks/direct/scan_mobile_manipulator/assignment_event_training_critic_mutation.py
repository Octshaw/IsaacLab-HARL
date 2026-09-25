"""Private B2-R4 critic/ValueNorm controlled mutation seam.

The seam proves source-faithful live ValueNorm ordering and critic-only Adam
mutation against an immutable R1 plan.  It is not a runner, trainer, rollout
component, public coordinator, or full learner update.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_CRITIC_MUTATION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_critic_mutation"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_CRITIC_MUTATION_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R4 critic mutation requires its "
        "canonical module key"
    )


from dataclasses import dataclass, replace
import math
from typing import Mapping, Sequence

import torch
from harl.utils.models_tools import huber_loss, mse_loss

from .assignment_event_training_actor_mutation import (
    _optimizer_digest,
    _optimizer_step_vector,
    _parameter_digest,
    _state_digest,
)
from .assignment_event_training_control import B2RPermitOperationV1
from .assignment_event_training_evidence import (
    B2RComponentFingerprintV1,
    B2RContractError,
    B2RFrozenTrainingInputsV1,
    B2RUpdateAuthorityV1,
    STOP_ACTOR_EVIDENCE_BINDING,
    STOP_AUTHORITY_DRIFT,
    STOP_VALUENORM,
    canonical_live_valuenorm_state_v1,
    canonical_digest_v1,
    fingerprint_component_v1,
    fingerprint_tensor_v1,
    validate_parameter_ownership_v1,
)
from .assignment_event_training_gradient_probe import (
    B2RGradientAuditV1,
    B2RLossGraphEvidenceV1,
    B2RProbeExecutionCounterV1,
    VALID_NONZERO_UPDATE,
    VALID_ZERO_EFFECTIVE_UPDATE,
    STOP_CRITIC_TRAINING_SLICE,
    STOP_MUTATION_ATTRIBUTION,
    STOP_NONFINITE_GRADIENT,
    STOP_NONFINITE_LOSS,
    STOP_NONFINITE_OPTIMIZER_STATE,
    STOP_NONFINITE_PARAMETER,
    STOP_NONFINITE_TARGET,
    STOP_NONFINITE_VALUENORM_STATE,
    STOP_UNEXPECTED_STEP_COUNT,
    _clear_gradients_v1,
    _execute_backward_v1,
    _validate_finite_component_state_v1,
    _validate_finite_valuenorm_v1,
    classify_loss_graph_v1,
    validate_gradients_clear_v1,
)
from .assignment_event_training_plans import (
    B2RCriticUpdatePlanV1,
    STOP_CRITIC_ROW_COVERAGE,
)


STOP_UNAUTHORIZED_BACKWARD = "STOP — B2-R UNAUTHORIZED_BACKWARD"
STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_MODE_ORDER = "STOP — B2-R MODE_ORDER"


def _fail(
    message: str,
    *,
    stop_code: str,
    stage: str,
    field_name: str | None = None,
    expected: object = None,
    observed: object = None,
) -> None:
    raise B2RContractError(
        message,
        stop_code=stop_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        observed=observed,
    )


def _indices_digest(indices: Sequence[int]) -> str:
    return canonical_digest_v1(tuple(indices))


def _valuenorm_digest(value_normalizer: object) -> str:
    return fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=value_normalizer,
    ).fingerprint_digest


def _actor_bindings(actors: Sequence[object]):
    return tuple(
        (f"actor{index}", actor.actor, actor.actor_optimizer)
        for index, actor in enumerate(actors)
    )


def _capture_all_v1(
    *, actors: Sequence[object], critic: object, live_value_normalizer: object
) -> tuple[tuple[B2RComponentFingerprintV1, ...], B2RComponentFingerprintV1, B2RComponentFingerprintV1]:
    actor_bindings = _actor_bindings(actors)
    critic_binding = ("critic", critic.critic, critic.critic_optimizer)
    validate_parameter_ownership_v1(
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        shared_parameter_mode=False,
    )
    bindings = tuple((owner, module) for owner, module, _ in actor_bindings) + (
        ("critic", critic.critic),
    )
    validate_gradients_clear_v1(bindings)
    actor_fingerprints: list[B2RComponentFingerprintV1] = []
    for owner, module, optimizer in actor_bindings:
        _validate_finite_component_state_v1(
            owner=owner, module=module, optimizer=optimizer
        )
        actor_fingerprints.append(
            fingerprint_component_v1(
                component_kind="actor",
                owner_identity=owner,
                module=module,
                optimizer=optimizer,
            )
        )
    _validate_finite_component_state_v1(
        owner="critic", module=critic.critic, optimizer=critic.critic_optimizer
    )
    critic_fingerprint = fingerprint_component_v1(
        component_kind="critic",
        owner_identity="critic",
        module=critic.critic,
        optimizer=critic.critic_optimizer,
    )
    _validate_finite_valuenorm_v1(live_value_normalizer)
    valuenorm_fingerprint = fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=live_value_normalizer,
    )
    return tuple(actor_fingerprints), critic_fingerprint, valuenorm_fingerprint


@dataclass(frozen=True, slots=True)
class B2R4MutationAuthorityV1:
    base_authority: B2RUpdateAuthorityV1
    mutation_id: str
    slice_identity: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    schema_version: str = "b2r4_mutation_authority_v1"

    def __post_init__(self) -> None:
        required_allowed = {
            "live_valuenorm_update",
            "critic_backward",
            "critic_gradient_clip",
            "critic_optimizer_step",
        }
        required_forbidden = {
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
        }
        if (
            self.slice_identity != "B2-R4"
            or not self.mutation_id
            or not required_allowed.issubset(set(self.allowed_operations))
            or not required_forbidden.issubset(set(self.forbidden_operations))
        ):
            _fail(
                "R4 authority boundary is incomplete",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r4_authority",
            )

    @property
    def update_id(self) -> str:
        return self.base_authority.update_id

    @property
    def config_digest(self) -> str:
        return self.base_authority.config_digest

    @property
    def authority_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R4CriticInputsV1:
    shared_obs: torch.Tensor
    rnn_states: torch.Tensor
    masks: torch.Tensor
    value_preds: torch.Tensor
    returns_storage: torch.Tensor


@dataclass(frozen=True, slots=True)
class B2R4MutationPermitV1:
    permit_id: str
    update_id: str
    authority_config_digest: str
    component_kind: str
    epoch: int
    minibatch: int
    canonical_index_digest: str
    raw_target_digest: str
    operation: B2RPermitOperationV1
    expected_critic_parameter_fingerprint: str
    expected_critic_optimizer_fingerprint: str
    expected_valuenorm_fingerprint: str
    target_classification: str
    schema_version: str = "b2r4_mutation_permit_v1"


class B2R4PermitLedgerV1:
    __slots__ = ("_consumed",)

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def consume(
        self,
        permit: B2R4MutationPermitV1 | None,
        *,
        authority: B2R4MutationAuthorityV1,
        route_state: "B2R4RouteStateV1",
        component_kind: str,
        epoch: int,
        minibatch: int,
        canonical_indices: tuple[int, ...],
        raw_target_digest: str,
        operation: B2RPermitOperationV1,
        critic_parameter_fingerprint: str,
        critic_optimizer_fingerprint: str,
        valuenorm_fingerprint: str,
    ) -> None:
        stop = {
            B2RPermitOperationV1.VALUENORM_UPDATE: STOP_VALUENORM,
            B2RPermitOperationV1.BACKWARD: STOP_UNAUTHORIZED_BACKWARD,
            B2RPermitOperationV1.OPTIMIZER_STEP: STOP_UNAUTHORIZED_OPTIMIZER_STEP,
        }[operation]
        if route_state.route_poisoned:
            _fail(
                "poisoned R4 route rejected a later mutation",
                stop_code=stop,
                stage="r4_permit",
                observed="poisoned",
            )
        if permit is None:
            _fail(
                "R4 mutation attempted without a permit",
                stop_code=stop,
                stage="r4_permit",
                observed=None,
            )
        if permit.permit_id in self._consumed:
            _fail(
                "R4 single-use permit was consumed twice",
                stop_code=stop,
                stage="r4_permit",
                observed=permit.permit_id,
            )
        expected = (
            authority.update_id,
            authority.config_digest,
            component_kind,
            epoch,
            minibatch,
            _indices_digest(canonical_indices),
            raw_target_digest,
            operation,
            critic_parameter_fingerprint,
            critic_optimizer_fingerprint,
            valuenorm_fingerprint,
            "raw_returns_minus_final",
        )
        observed = (
            permit.update_id,
            permit.authority_config_digest,
            permit.component_kind,
            permit.epoch,
            permit.minibatch,
            permit.canonical_index_digest,
            permit.raw_target_digest,
            permit.operation,
            permit.expected_critic_parameter_fingerprint,
            permit.expected_critic_optimizer_fingerprint,
            permit.expected_valuenorm_fingerprint,
            permit.target_classification,
        )
        if observed != expected or not canonical_indices:
            _fail(
                "R4 permit does not bind the exact raw critic minibatch state",
                stop_code=stop,
                stage="r4_permit",
                expected=expected,
                observed=observed,
            )
        self._consumed.add(permit.permit_id)


@dataclass(frozen=True, slots=True)
class B2R4FailureEvidenceV1:
    stop_code: str
    partial_update: bool
    route_poisoned: bool
    rollover_allowed: bool
    checkpoint_allowed: bool
    next_rollout_allowed: bool
    public_use_allowed: bool
    live_valuenorm_updates_before_failure: int
    critic_steps_before_failure: int
    schema_version: str = "b2r4_failure_evidence_v1"


class B2R4RouteStateV1:
    __slots__ = ("partial_update", "route_poisoned", "last_failure")

    def __init__(self) -> None:
        self.partial_update = False
        self.route_poisoned = False
        self.last_failure: B2R4FailureEvidenceV1 | None = None

    def record_failure(
        self, *, stop_code: str, valuenorm_updates: int, critic_steps: int
    ) -> None:
        partial = valuenorm_updates > 0 or critic_steps > 0
        self.partial_update = partial
        self.route_poisoned = partial
        self.last_failure = B2R4FailureEvidenceV1(
            stop_code=stop_code,
            partial_update=partial,
            route_poisoned=partial,
            rollover_allowed=not partial,
            checkpoint_allowed=False,
            next_rollout_allowed=not partial,
            public_use_allowed=False,
            live_valuenorm_updates_before_failure=valuenorm_updates,
            critic_steps_before_failure=critic_steps,
        )


class B2R4ExecutionCounterV1:
    __slots__ = (
        "critic_backward_executed",
        "critic_valid_nonzero_executed",
        "critic_valid_zero_effective_executed",
        "critic_step_attempted",
        "critic_step_executed",
        "live_valuenorm_attempted",
        "live_valuenorm_executed",
        "actor_step_attempted",
        "actor_step_executed",
        "actor_backward_executed",
        "scheduler_step_executed",
    )

    def __init__(self) -> None:
        self.critic_backward_executed = 0
        self.critic_valid_nonzero_executed = 0
        self.critic_valid_zero_effective_executed = 0
        self.critic_step_attempted = 0
        self.critic_step_executed = 0
        self.live_valuenorm_attempted = 0
        self.live_valuenorm_executed = 0
        self.actor_step_attempted = 0
        self.actor_step_executed = 0
        self.actor_backward_executed = 0
        self.scheduler_step_executed = 0


class B2R4ActorStepTrapV1:
    __slots__ = ("counter",)

    def __init__(self, counter: B2R4ExecutionCounterV1) -> None:
        self.counter = counter

    def step(self) -> None:
        self.counter.actor_step_attempted += 1
        _fail(
            "actor optimizer step is forbidden in R4",
            stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP,
            stage="r4_actor_step_trap",
        )


@dataclass(frozen=True, slots=True)
class B2R4ValueNormReceiptV1:
    permit_id: str
    epoch: int
    minibatch: int
    canonical_indices: tuple[int, ...]
    raw_target_digest: str
    pre_fingerprint: str
    post_fingerprint: str
    running_mean_digest: str
    running_mean_sq_digest: str
    debiasing_term_digest: str
    running_mean_values: tuple[float, ...]
    running_mean_sq_values: tuple[float, ...]
    debiasing_term_values: tuple[float, ...]
    update_call_index: int
    normalize_call_count: int
    normalize_same_object: bool
    normalize_same_digest: bool
    state_mutated: bool
    finite: bool
    schema_version: str = "b2r4_valuenorm_receipt_v1"


class B2R4PermittedLiveValueNormProxyV1:
    """Single-minibatch proxy around one real live ValueNorm object."""

    __slots__ = (
        "value_normalizer",
        "authority",
        "route_state",
        "ledger",
        "permit",
        "epoch",
        "minibatch",
        "canonical_indices",
        "raw_target",
        "raw_digest",
        "critic_parameter_fingerprint",
        "critic_optimizer_fingerprint",
        "counter",
        "pre_fingerprint",
        "post_fingerprint",
        "normalize_count",
        "same_object",
        "same_digest",
        "updated",
    )

    def __init__(
        self,
        *,
        value_normalizer: object,
        authority: B2R4MutationAuthorityV1,
        route_state: B2R4RouteStateV1,
        ledger: B2R4PermitLedgerV1,
        permit: B2R4MutationPermitV1 | None,
        epoch: int,
        minibatch: int,
        canonical_indices: tuple[int, ...],
        raw_target: torch.Tensor,
        critic_parameter_fingerprint: str,
        critic_optimizer_fingerprint: str,
        counter: B2R4ExecutionCounterV1,
    ) -> None:
        self.value_normalizer = value_normalizer
        self.authority = authority
        self.route_state = route_state
        self.ledger = ledger
        self.permit = permit
        self.epoch = epoch
        self.minibatch = minibatch
        self.canonical_indices = canonical_indices
        self.raw_target = raw_target
        self.raw_digest = fingerprint_tensor_v1(raw_target).content_digest
        self.critic_parameter_fingerprint = critic_parameter_fingerprint
        self.critic_optimizer_fingerprint = critic_optimizer_fingerprint
        self.counter = counter
        self.pre_fingerprint = _valuenorm_digest(value_normalizer)
        self.post_fingerprint: str | None = None
        self.normalize_count = 0
        self.same_object = True
        self.same_digest = True
        self.updated = False

    def update(self, input_vector: torch.Tensor) -> None:
        self.counter.live_valuenorm_attempted += 1
        supplied_digest = fingerprint_tensor_v1(input_vector).content_digest
        if input_vector is not self.raw_target or supplied_digest != self.raw_digest:
            _fail(
                "live ValueNorm update did not receive the exact raw target object",
                stop_code=STOP_VALUENORM,
                stage="r4_valuenorm_update",
            )
        self.ledger.consume(
            self.permit,
            authority=self.authority,
            route_state=self.route_state,
            component_kind="live_valuenorm",
            epoch=self.epoch,
            minibatch=self.minibatch,
            canonical_indices=self.canonical_indices,
            raw_target_digest=self.raw_digest,
            operation=B2RPermitOperationV1.VALUENORM_UPDATE,
            critic_parameter_fingerprint=self.critic_parameter_fingerprint,
            critic_optimizer_fingerprint=self.critic_optimizer_fingerprint,
            valuenorm_fingerprint=self.pre_fingerprint,
        )
        self.value_normalizer.update(input_vector)
        self.counter.live_valuenorm_executed += 1
        self.updated = True
        _validate_finite_valuenorm_v1(self.value_normalizer)
        self.post_fingerprint = _valuenorm_digest(self.value_normalizer)
        if self.post_fingerprint == self.pre_fingerprint:
            _fail(
                "nondegenerate live ValueNorm update produced no state mutation",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="r4_valuenorm_update",
            )

    def normalize(self, input_vector: torch.Tensor) -> torch.Tensor:
        if not self.updated:
            _fail(
                "normalization attempted before live ValueNorm update",
                stop_code=STOP_MODE_ORDER,
                stage="r4_valuenorm_normalize",
            )
        supplied_digest = fingerprint_tensor_v1(input_vector).content_digest
        self.normalize_count += 1
        self.same_object = self.same_object and input_vector is self.raw_target
        self.same_digest = self.same_digest and supplied_digest == self.raw_digest
        if not self.same_object or not self.same_digest:
            _fail(
                "normalization source differs from the updated raw batch",
                stop_code=STOP_VALUENORM,
                stage="r4_valuenorm_normalize",
            )
        result = self.value_normalizer.normalize(input_vector)
        if not bool(torch.isfinite(result).all().item()):
            _fail(
                "normalized critic target is nonfinite",
                stop_code=STOP_NONFINITE_VALUENORM_STATE,
                stage="r4_valuenorm_normalize",
            )
        return result

    def receipt(self) -> B2R4ValueNormReceiptV1:
        if not self.updated or self.post_fingerprint is None or self.normalize_count != 2:
            _fail(
                "ValueNorm update/normalize order is incomplete",
                stop_code=STOP_VALUENORM,
                stage="r4_valuenorm_receipt",
                expected="one update then two same-raw normalize calls",
                observed=(self.updated, self.normalize_count),
            )
        state = canonical_live_valuenorm_state_v1(self.value_normalizer)
        mean = state["running_mean"].detach().reshape(-1)
        mean_sq = state["running_mean_sq"].detach().reshape(-1)
        debias = state["debiasing_term"].detach().reshape(-1)
        return B2R4ValueNormReceiptV1(
            permit_id=self.permit.permit_id if self.permit is not None else "",
            epoch=self.epoch,
            minibatch=self.minibatch,
            canonical_indices=self.canonical_indices,
            raw_target_digest=self.raw_digest,
            pre_fingerprint=self.pre_fingerprint,
            post_fingerprint=self.post_fingerprint,
            running_mean_digest=fingerprint_tensor_v1(mean).content_digest,
            running_mean_sq_digest=fingerprint_tensor_v1(mean_sq).content_digest,
            debiasing_term_digest=fingerprint_tensor_v1(debias).content_digest,
            running_mean_values=tuple(float(item) for item in mean.cpu().tolist()),
            running_mean_sq_values=tuple(float(item) for item in mean_sq.cpu().tolist()),
            debiasing_term_values=tuple(float(item) for item in debias.cpu().tolist()),
            update_call_index=self.counter.live_valuenorm_executed,
            normalize_call_count=self.normalize_count,
            normalize_same_object=self.same_object,
            normalize_same_digest=self.same_digest,
            state_mutated=True,
            finite=True,
        )


@dataclass(frozen=True, slots=True)
class B2R4CriticLossSampleEvidenceV1:
    canonical_index: int
    raw_return: float
    normalized_return: float
    frozen_value_prediction: float
    current_value_prediction: float
    current_minus_frozen: float
    clipped_current_value_prediction: float
    unclipped_value_error: float
    clipped_value_error: float
    unclipped_branch_loss: float
    clipped_branch_loss: float
    selected_branch: str
    d_loss_d_current_value: float
    zero_derivative_reason: str | None
    schema_version: str = "b2r4_critic_loss_sample_evidence_v1"


@dataclass(frozen=True, slots=True)
class B2R4CriticLossDecompositionV1:
    canonical_indices: tuple[int, ...]
    raw_target_digest: str
    normalized_target_digest: str
    frozen_value_prediction_digest: str
    current_value_digest: str
    clip_param: float
    huber_delta: float
    value_loss_coef: float
    use_clipped_value_loss: bool
    use_huber_loss: bool
    loss_value: float
    source_math_digest: str
    sample_count: int
    bounded_samples_complete: bool
    samples: tuple[B2R4CriticLossSampleEvidenceV1, ...]
    mathematical_zero_effective_proved: bool
    zero_effective_reason: str | None
    schema_version: str = "b2r4_critic_loss_decomposition_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R4AdamParameterStateEvidenceV1:
    parameter_name: str
    state_present: bool
    step: float
    exp_avg_digest: str | None
    exp_avg_norm: float | None
    exp_avg_sq_digest: str | None
    exp_avg_sq_norm: float | None
    schema_version: str = "b2r4_adam_parameter_state_evidence_v1"


def _adam_state_evidence_v1(critic: object) -> tuple[B2R4AdamParameterStateEvidenceV1, ...]:
    result: list[B2R4AdamParameterStateEvidenceV1] = []
    optimizer = critic.critic_optimizer
    for name, parameter in critic.critic.named_parameters():
        state = optimizer.state.get(parameter, {})
        step = state.get("step", 0.0)
        if isinstance(step, torch.Tensor):
            step = float(step.detach().cpu().item())
        exp_avg = state.get("exp_avg")
        exp_avg_sq = state.get("exp_avg_sq")
        result.append(
            B2R4AdamParameterStateEvidenceV1(
                parameter_name=f"critic.{name}",
                state_present=bool(state),
                step=float(step),
                exp_avg_digest=(
                    None
                    if not isinstance(exp_avg, torch.Tensor)
                    else fingerprint_tensor_v1(exp_avg.detach()).content_digest
                ),
                exp_avg_norm=(
                    None
                    if not isinstance(exp_avg, torch.Tensor)
                    else float(torch.linalg.vector_norm(exp_avg.detach()).item())
                ),
                exp_avg_sq_digest=(
                    None
                    if not isinstance(exp_avg_sq, torch.Tensor)
                    else fingerprint_tensor_v1(exp_avg_sq.detach()).content_digest
                ),
                exp_avg_sq_norm=(
                    None
                    if not isinstance(exp_avg_sq, torch.Tensor)
                    else float(torch.linalg.vector_norm(exp_avg_sq.detach()).item())
                ),
            )
        )
    return tuple(result)


@dataclass(frozen=True, slots=True)
class B2R4CriticStepReceiptV1:
    epoch: int
    minibatch: int
    canonical_indices: tuple[int, ...]
    raw_target_digest: str
    normalized_target_digest: str
    final_slot_digest: str
    valuenorm_receipt: B2R4ValueNormReceiptV1 | None
    backward_permit_id: str
    step_permit_id: str
    loss_value: float
    aggregate_gradient_norm: float
    clip_result: float
    critic_parameter_digest_before: str
    critic_parameter_digest_after: str
    critic_optimizer_digest_before: str
    critic_optimizer_digest_after: str
    optimizer_step_vector_before: tuple[tuple[int, float], ...]
    optimizer_step_vector_after: tuple[tuple[int, float], ...]
    critic_parameter_mutated: bool
    critic_optimizer_mutated: bool
    valuenorm_mutated: bool
    actors_unchanged: bool
    gradients_clean_after: bool
    gradient_classification: str = VALID_NONZERO_UPDATE
    gradient_audit: B2RGradientAuditV1 | None = None
    loss_graph_evidence: B2RLossGraphEvidenceV1 | None = None
    loss_decomposition: B2R4CriticLossDecompositionV1 | None = None
    adam_state_before: tuple[B2R4AdamParameterStateEvidenceV1, ...] = ()
    adam_state_after: tuple[B2R4AdamParameterStateEvidenceV1, ...] = ()
    schema_version: str = "b2r4_critic_step_receipt_v1"


@dataclass(frozen=True, slots=True)
class B2R4CriticSequenceReceiptV1:
    plan_digest: str
    target_digest: str
    final_slot_digest: str
    partitions_by_epoch: tuple[tuple[tuple[int, ...], ...], ...]
    per_epoch_backward_count: tuple[int, ...]
    per_epoch_step_count: tuple[int, ...]
    per_epoch_valuenorm_count: tuple[int, ...]
    observed_backward_count: int
    observed_step_count: int
    observed_valuenorm_count: int
    actor_components_unchanged: bool
    actor_optimizers_unchanged: bool
    gradients_clean_after: bool
    valuenorm_enabled: bool
    remainder_safe: bool
    step_receipts: tuple[B2R4CriticStepReceiptV1, ...]
    valid_nonzero_count: int = 0
    valid_zero_effective_count: int = 0
    schema_version: str = "b2r4_critic_sequence_receipt_v1"


def _make_permit_v1(
    *,
    authority: B2R4MutationAuthorityV1,
    component_kind: str,
    epoch: int,
    minibatch: int,
    indices: tuple[int, ...],
    raw_digest: str,
    operation: B2RPermitOperationV1,
    critic_parameter_digest: str,
    critic_optimizer_digest: str,
    valuenorm_digest: str,
) -> B2R4MutationPermitV1:
    return B2R4MutationPermitV1(
        permit_id=f"{authority.mutation_id}:{epoch}:{minibatch}:{operation.value}",
        update_id=authority.update_id,
        authority_config_digest=authority.config_digest,
        component_kind=component_kind,
        epoch=epoch,
        minibatch=minibatch,
        canonical_index_digest=_indices_digest(indices),
        raw_target_digest=raw_digest,
        operation=operation,
        expected_critic_parameter_fingerprint=critic_parameter_digest,
        expected_critic_optimizer_fingerprint=critic_optimizer_digest,
        expected_valuenorm_fingerprint=valuenorm_digest,
        target_classification="raw_returns_minus_final",
    )


def _critic_value_loss_terms_v1(
    *, critic: object, values: torch.Tensor, value_preds: torch.Tensor,
    normalized_one: torch.Tensor, normalized_two: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    clipped = value_preds + (values - value_preds).clamp(
        -critic.clip_param, critic.clip_param
    )
    error_clipped = normalized_one - clipped
    error_original = normalized_two - values
    if critic.use_huber_loss:
        loss_clipped = huber_loss(error_clipped, critic.huber_delta)
        loss_original = huber_loss(error_original, critic.huber_delta)
    else:
        loss_clipped = mse_loss(error_clipped)
        loss_original = mse_loss(error_original)
    loss = (
        torch.max(loss_original, loss_clipped)
        if critic.use_clipped_value_loss
        else loss_original
    )
    return (
        loss.mean() * float(critic.value_loss_coef),
        clipped,
        error_original,
        error_clipped,
        loss_original,
        loss_clipped,
    )


def _critic_value_loss_v1(
    *, critic: object, values: torch.Tensor, value_preds: torch.Tensor,
    normalized_one: torch.Tensor, normalized_two: torch.Tensor
) -> torch.Tensor:
    return _critic_value_loss_terms_v1(
        critic=critic,
        values=values,
        value_preds=value_preds,
        normalized_one=normalized_one,
        normalized_two=normalized_two,
    )[0]


def _critic_loss_diagnostics_v1(
    *,
    critic: object,
    canonical_indices: tuple[int, ...],
    raw_batch: torch.Tensor,
    values: torch.Tensor,
    value_preds: torch.Tensor,
    normalized_one: torch.Tensor,
    normalized_two: torch.Tensor,
) -> tuple[torch.Tensor, B2R4CriticLossDecompositionV1, B2RLossGraphEvidenceV1]:
    """Run installed-source-faithful loss math and classify graph evidence."""

    (
        loss,
        clipped,
        error_original,
        error_clipped,
        loss_original,
        loss_clipped,
    ) = _critic_value_loss_terms_v1(
        critic=critic,
        values=values,
        value_preds=value_preds,
        normalized_one=normalized_one,
        normalized_two=normalized_two,
    )
    detached_values = values.detach().reshape(-1)
    detached_preds = value_preds.detach().reshape(-1)
    detached_raw = raw_batch.detach().reshape(-1)
    detached_normalized = normalized_one.detach().reshape(-1)
    detached_clipped = clipped.detach().reshape(-1)
    detached_error_original = error_original.detach().reshape(-1)
    detached_error_clipped = error_clipped.detach().reshape(-1)
    detached_loss_original = loss_original.detach().reshape(-1)
    detached_loss_clipped = loss_clipped.detach().reshape(-1)
    if not (
        len(canonical_indices)
        == detached_values.numel()
        == detached_preds.numel()
        == detached_raw.numel()
        == detached_normalized.numel()
    ):
        _fail(
            "critic loss decomposition does not bind one value per physical row",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="r4_loss_decomposition",
            expected=len(canonical_indices),
            observed=(
                detached_values.numel(),
                detached_preds.numel(),
                detached_raw.numel(),
                detached_normalized.numel(),
            ),
        )
    selected_branches: list[str] = []
    zero_reasons: list[str | None] = []
    for position in range(len(canonical_indices)):
        original_value = float(detached_loss_original[position].item())
        clipped_value = float(detached_loss_clipped[position].item())
        if not critic.use_clipped_value_loss:
            selected = "unclipped"
        elif original_value > clipped_value:
            selected = "unclipped"
        elif clipped_value > original_value:
            selected = "clipped"
        else:
            selected = "tie"
        selected_branches.append(selected)
        original_error = float(detached_error_original[position].item())
        clipped_error = float(detached_error_clipped[position].item())
        delta = float(
            (detached_values[position] - detached_preds[position]).item()
        )
        reason: str | None = None
        if selected == "unclipped" and original_error == 0.0:
            reason = "EXACT_TARGET"
        elif selected == "tie" and original_error == 0.0 and clipped_error == 0.0:
            reason = "EXACT_TARGET"
        elif (
            selected == "clipped"
            and abs(delta) > float(critic.clip_param)
            and clipped_value > original_value
        ):
            reason = "CLIPPED_VALUE_PLATEAU"
        zero_reasons.append(reason)
    source_math_digest = canonical_digest_v1(
        (
            tuple(canonical_indices),
            fingerprint_tensor_v1(raw_batch).content_digest,
            fingerprint_tensor_v1(normalized_one).content_digest,
            fingerprint_tensor_v1(value_preds).content_digest,
            fingerprint_tensor_v1(values).content_digest,
            float(critic.clip_param),
            float(critic.huber_delta),
            float(critic.value_loss_coef),
            bool(critic.use_clipped_value_loss),
            bool(critic.use_huber_loss),
            tuple(selected_branches),
            tuple(zero_reasons),
        )
    )
    candidate_zero_proof = bool(zero_reasons) and all(
        reason is not None for reason in zero_reasons
    )
    combined_reason: str | None = None
    if candidate_zero_proof:
        distinct = tuple(dict.fromkeys(reason for reason in zero_reasons if reason))
        combined_reason = "+".join(distinct)
    graph = classify_loss_graph_v1(
        value_loss=loss,
        current_values=values,
        frozen_value_predictions=value_preds,
        normalized_targets=normalized_one,
        source_faithful_loss_evidence_digest=source_math_digest,
        mathematical_zero_effective_proved=candidate_zero_proof,
        zero_effective_reason=combined_reason,
    )
    derivative = torch.autograd.grad(
        loss,
        values,
        retain_graph=True,
        allow_unused=False,
    )[0].detach().reshape(-1)
    bounded_count = min(len(canonical_indices), 32)
    samples = tuple(
        B2R4CriticLossSampleEvidenceV1(
            canonical_index=canonical_indices[position],
            raw_return=float(detached_raw[position].item()),
            normalized_return=float(detached_normalized[position].item()),
            frozen_value_prediction=float(detached_preds[position].item()),
            current_value_prediction=float(detached_values[position].item()),
            current_minus_frozen=float(
                (detached_values[position] - detached_preds[position]).item()
            ),
            clipped_current_value_prediction=float(
                detached_clipped[position].item()
            ),
            unclipped_value_error=float(detached_error_original[position].item()),
            clipped_value_error=float(detached_error_clipped[position].item()),
            unclipped_branch_loss=float(detached_loss_original[position].item()),
            clipped_branch_loss=float(detached_loss_clipped[position].item()),
            selected_branch=selected_branches[position],
            d_loss_d_current_value=float(derivative[position].item()),
            zero_derivative_reason=zero_reasons[position],
        )
        for position in range(bounded_count)
    )
    decomposition = B2R4CriticLossDecompositionV1(
        canonical_indices=canonical_indices,
        raw_target_digest=fingerprint_tensor_v1(raw_batch).content_digest,
        normalized_target_digest=fingerprint_tensor_v1(normalized_one).content_digest,
        frozen_value_prediction_digest=fingerprint_tensor_v1(value_preds).content_digest,
        current_value_digest=fingerprint_tensor_v1(values).content_digest,
        clip_param=float(critic.clip_param),
        huber_delta=float(critic.huber_delta),
        value_loss_coef=float(critic.value_loss_coef),
        use_clipped_value_loss=bool(critic.use_clipped_value_loss),
        use_huber_loss=bool(critic.use_huber_loss),
        loss_value=float(loss.detach().item()),
        source_math_digest=source_math_digest,
        sample_count=len(canonical_indices),
        bounded_samples_complete=len(canonical_indices) <= bounded_count,
        samples=samples,
        mathematical_zero_effective_proved=(
            graph.classification == VALID_ZERO_EFFECTIVE_UPDATE
        ),
        zero_effective_reason=graph.zero_effective_reason,
    )
    return loss, decomposition, graph


def validate_pre_backward_loss_v1(
    *, raw_finite: bool, normalized_finite: bool, prediction_finite: bool,
    loss_finite: bool
) -> None:
    if not raw_finite:
        _fail("raw critic target is nonfinite", stop_code=STOP_NONFINITE_TARGET, stage="r4_loss_gate")
    if not normalized_finite:
        _fail("normalized target is nonfinite", stop_code=STOP_NONFINITE_VALUENORM_STATE, stage="r4_loss_gate")
    if not prediction_finite or not loss_finite:
        _fail("critic prediction/loss is nonfinite", stop_code=STOP_NONFINITE_LOSS, stage="r4_loss_gate")


def validate_same_raw_normalization_v1(
    *, update_digest: str, normalize_digest: str, same_object: bool
) -> None:
    if update_digest != normalize_digest or not same_object:
        _fail(
            "normalization does not use the exact updated raw batch",
            stop_code=STOP_VALUENORM,
            stage="r4_normalization_identity",
        )


def validate_valuenorm_state_claim_v1(*, finite: bool, mutated: bool) -> None:
    if not finite:
        _fail("live ValueNorm state is nonfinite", stop_code=STOP_NONFINITE_VALUENORM_STATE, stage="r4_valuenorm_audit")
    if not mutated:
        _fail("expected live ValueNorm mutation is absent", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_valuenorm_audit")


def validate_gradient_clip_claim_v1(
    *, owned_finite: bool, aggregate_norm: float, clip_result: float,
    foreign_gradient_names: tuple[str, ...]
) -> None:
    if not owned_finite or not math.isfinite(aggregate_norm) or not math.isfinite(clip_result):
        _fail("critic gradient/clip evidence is nonfinite", stop_code=STOP_NONFINITE_GRADIENT, stage="r4_gradient_audit")
    if foreign_gradient_names:
        _fail("critic backward produced actor gradient", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_gradient_audit", observed=foreign_gradient_names)


def validate_post_step_state_claim_v1(
    *, parameter_finite: bool, optimizer_finite: bool,
    parameter_mutated: bool, optimizer_mutated: bool,
    gradient_classification: str = VALID_NONZERO_UPDATE,
) -> None:
    if not parameter_finite:
        _fail("critic parameter is nonfinite", stop_code=STOP_NONFINITE_PARAMETER, stage="r4_post_step_claim")
    if not optimizer_finite:
        _fail("critic optimizer state is nonfinite", stop_code=STOP_NONFINITE_OPTIMIZER_STATE, stage="r4_post_step_claim")
    if gradient_classification not in {
        VALID_NONZERO_UPDATE,
        VALID_ZERO_EFFECTIVE_UPDATE,
    }:
        _fail(
            "critic gradient classification is not step-authorizing",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="r4_post_step_claim",
            observed=gradient_classification,
        )
    if not optimizer_mutated or (
        gradient_classification == VALID_NONZERO_UPDATE and not parameter_mutated
    ):
        _fail(
            "critic mutation attribution is incomplete for its gradient class",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="r4_post_step_claim",
            expected=gradient_classification,
            observed=(parameter_mutated, optimizer_mutated),
        )


def validate_count_claim_v1(
    *, expected: tuple[int, int, int], observed: tuple[int, int, int]
) -> None:
    if expected != observed:
        _fail(
            "critic backward/step/ValueNorm counts differ from plan",
            stop_code=STOP_UNEXPECTED_STEP_COUNT,
            stage="r4_count_audit",
            expected=expected,
            observed=observed,
        )


def validate_actor_freeze_claim_v1(
    *, expected: Mapping[str, str], observed: Mapping[str, str]
) -> None:
    if dict(expected) != dict(observed):
        _fail(
            "actor or actor optimizer changed during critic mutation",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="r4_actor_freeze",
            expected=dict(expected),
            observed=dict(observed),
        )


def _execute_critic_optimizer_step_v1(
    *, critic: object, counter: B2R4ExecutionCounterV1
) -> None:
    counter.critic_step_attempted += 1
    critic.critic_optimizer.step()
    counter.critic_step_executed += 1


def execute_critic_sequence_v1(
    *,
    authority: B2R4MutationAuthorityV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    critic_plan: B2RCriticUpdatePlanV1,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    inputs: B2R4CriticInputsV1,
    route_state: B2R4RouteStateV1,
    counter: B2R4ExecutionCounterV1,
    synthetic_fault: str | None = None,
) -> B2R4CriticSequenceReceiptV1:
    """Execute one plan-bound critic-only sequence and exact post audits."""

    start_backward = counter.critic_backward_executed
    start_steps = counter.critic_step_executed
    start_vn = counter.live_valuenorm_executed
    start_valid_nonzero = counter.critic_valid_nonzero_executed
    start_valid_zero = counter.critic_valid_zero_effective_executed
    modules = tuple(actor.actor for actor in actors) + (critic.critic,)
    try:
        if (
            critic_plan.update_id != authority.update_id
            or critic_plan.authority_config_digest != authority.config_digest
            or critic_plan.optimizer_step_policy != "match_backward"
        ):
            _fail(
                "critic plan authority drifted",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r4_sequence_start",
            )
        config = authority.base_authority.resolved_config
        expected_shape = (config.resolved_T + 1, config.resolved_E, 1)
        if tuple(inputs.returns_storage.shape) != expected_shape:
            _fail(
                "critic returns storage is not exact [T+1,E,1]",
                stop_code=STOP_CRITIC_TRAINING_SLICE,
                stage="r4_target_binding",
                expected=expected_shape,
                observed=tuple(inputs.returns_storage.shape),
            )
        raw_target = inputs.returns_storage[:-1].reshape(critic_plan.B, 1)
        final_slot = inputs.returns_storage[-1]
        if not bool(torch.isfinite(raw_target).all().item()):
            _fail("raw returns[:-1] is nonfinite", stop_code=STOP_NONFINITE_TARGET, stage="r4_target_binding")
        target_digest = fingerprint_tensor_v1(raw_target).content_digest
        final_slot_digest = fingerprint_tensor_v1(final_slot).content_digest
        if (
            target_digest != critic_plan.raw_target_digest
            or frozen_inputs.critic_training_slice_digest != target_digest
            or frozen_inputs.update_id != authority.update_id
            or frozen_inputs.authority_config_digest != authority.config_digest
        ):
            _fail(
                "critic target is not the frozen returns[:-1] identity",
                stop_code=STOP_CRITIC_TRAINING_SLICE,
                stage="r4_target_binding",
            )
        if (
            inputs.shared_obs.ndim != 2
            or inputs.shared_obs.shape[0] != critic_plan.B
            or inputs.rnn_states.shape[0] != critic_plan.B
            or tuple(inputs.masks.shape) != (critic_plan.B, 1)
            or tuple(inputs.value_preds.shape) != (critic_plan.B, 1)
        ):
            _fail("critic input grid does not bind B", stop_code=STOP_CRITIC_TRAINING_SLICE, stage="r4_target_binding")
        initial_actors, initial_critic, initial_vn = _capture_all_v1(
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
        )
        expected_actor_state = {
            f"actor{index}": _state_digest(fingerprint)
            for index, fingerprint in enumerate(initial_actors)
        }
        ledger = B2R4PermitLedgerV1()
        r2_counter = B2RProbeExecutionCounterV1()
        receipts: list[B2R4CriticStepReceiptV1] = []
        epoch_backward = [0] * critic_plan.critic_epoch_count
        epoch_steps = [0] * critic_plan.critic_epoch_count
        epoch_vn = [0] * critic_plan.critic_epoch_count
        for epoch, partitions in enumerate(critic_plan.partitions_by_epoch):
            observed_rows = tuple(row for partition in partitions for row in partition)
            if len(observed_rows) != critic_plan.B or set(observed_rows) != set(range(critic_plan.B)):
                _fail("critic epoch lacks exact-once row coverage", stop_code=STOP_CRITIC_ROW_COVERAGE, stage="r4_row_coverage", observed=observed_rows)
            for minibatch, partition in enumerate(partitions):
                if any(row < 0 or row >= critic_plan.B for row in partition):
                    _fail("critic partition selects structural/out-of-range row", stop_code=STOP_CRITIC_ROW_COVERAGE, stage="r4_row_coverage")
                pre_actors, pre_critic, pre_vn = _capture_all_v1(
                    actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
                )
                index = torch.tensor(partition, dtype=torch.long, device=raw_target.device)
                raw_batch = raw_target[index]
                raw_digest = fingerprint_tensor_v1(raw_batch).content_digest
                pre_parameter = _parameter_digest(pre_critic)
                pre_optimizer = _optimizer_digest(pre_critic)
                pre_vn_digest = pre_vn.fingerprint_digest
                valuenorm_receipt: B2R4ValueNormReceiptV1 | None = None
                if critic_plan.valuenorm_enabled:
                    vn_permit = _make_permit_v1(
                        authority=authority,
                        component_kind="live_valuenorm",
                        epoch=epoch,
                        minibatch=minibatch,
                        indices=partition,
                        raw_digest=raw_digest,
                        operation=B2RPermitOperationV1.VALUENORM_UPDATE,
                        critic_parameter_digest=pre_parameter,
                        critic_optimizer_digest=pre_optimizer,
                        valuenorm_digest=pre_vn_digest,
                    )
                    proxy = B2R4PermittedLiveValueNormProxyV1(
                        value_normalizer=live_value_normalizer,
                        authority=authority,
                        route_state=route_state,
                        ledger=ledger,
                        permit=vn_permit,
                        epoch=epoch,
                        minibatch=minibatch,
                        canonical_indices=partition,
                        raw_target=raw_batch,
                        critic_parameter_fingerprint=pre_parameter,
                        critic_optimizer_fingerprint=pre_optimizer,
                        counter=counter,
                    )
                    proxy.update(raw_batch)
                    normalized_one = proxy.normalize(raw_batch)
                    normalized_two = proxy.normalize(raw_batch)
                    valuenorm_receipt = proxy.receipt()
                    epoch_vn[epoch] += 1
                    post_vn_digest = valuenorm_receipt.post_fingerprint
                    if synthetic_fault == "post_valuenorm":
                        _fail("controlled failure after live ValueNorm mutation", stop_code=STOP_VALUENORM, stage="r4_post_valuenorm_fault")
                else:
                    normalized_one = raw_batch
                    normalized_two = raw_batch
                    post_vn_digest = pre_vn_digest
                values, _ = critic.get_values(
                    inputs.shared_obs[index], inputs.rnn_states[index], inputs.masks[index]
                )
                loss, loss_decomposition, loss_graph = _critic_loss_diagnostics_v1(
                    critic=critic,
                    canonical_indices=partition,
                    raw_batch=raw_batch,
                    values=values,
                    value_preds=inputs.value_preds[index],
                    normalized_one=normalized_one,
                    normalized_two=normalized_two,
                )
                validate_pre_backward_loss_v1(
                    raw_finite=bool(torch.isfinite(raw_batch).all().item()),
                    normalized_finite=bool(torch.isfinite(normalized_one).all().item() and torch.isfinite(normalized_two).all().item()),
                    prediction_finite=bool(torch.isfinite(values).all().item()),
                    loss_finite=bool(torch.isfinite(loss.detach()).all().item()),
                )
                backward_permit = _make_permit_v1(
                    authority=authority,
                    component_kind="critic",
                    epoch=epoch,
                    minibatch=minibatch,
                    indices=partition,
                    raw_digest=raw_digest,
                    operation=B2RPermitOperationV1.BACKWARD,
                    critic_parameter_digest=pre_parameter,
                    critic_optimizer_digest=pre_optimizer,
                    valuenorm_digest=post_vn_digest,
                )
                ledger.consume(
                    backward_permit,
                    authority=authority,
                    route_state=route_state,
                    component_kind="critic",
                    epoch=epoch,
                    minibatch=minibatch,
                    canonical_indices=partition,
                    raw_target_digest=raw_digest,
                    operation=B2RPermitOperationV1.BACKWARD,
                    critic_parameter_fingerprint=pre_parameter,
                    critic_optimizer_fingerprint=pre_optimizer,
                    valuenorm_fingerprint=post_vn_digest,
                )
                critic.critic_optimizer.zero_grad(set_to_none=True)
                audit = _execute_backward_v1(
                    loss=loss,
                    component_kind="critic",
                    owner_identity="critic",
                    target_module=critic.critic,
                    foreign_bindings=tuple((f"actor{index}", actor.actor) for index, actor in enumerate(actors)),
                    counter=r2_counter,
                    require_nonzero=False,
                    allow_proved_zero_effective=True,
                    loss_graph_evidence=loss_graph,
                )
                counter.critic_backward_executed += 1
                if audit.classification == VALID_NONZERO_UPDATE:
                    counter.critic_valid_nonzero_executed += 1
                elif audit.classification == VALID_ZERO_EFFECTIVE_UPDATE:
                    counter.critic_valid_zero_effective_executed += 1
                else:
                    _fail(
                        "critic backward returned an unauthorized gradient class",
                        stop_code=STOP_MUTATION_ATTRIBUTION,
                        stage="r4_gradient_classification",
                        observed=audit.classification,
                    )
                epoch_backward[epoch] += 1
                if critic.use_max_grad_norm:
                    clip_value = torch.nn.utils.clip_grad_norm_(
                        critic.critic.parameters(), critic.max_grad_norm
                    )
                    clip_result = float(clip_value.detach().item() if isinstance(clip_value, torch.Tensor) else clip_value)
                else:
                    clip_result = audit.aggregate_norm
                if not math.isfinite(clip_result):
                    _fail("critic clip result is nonfinite", stop_code=STOP_NONFINITE_GRADIENT, stage="r4_pre_step")
                during = fingerprint_component_v1(
                    component_kind="critic", owner_identity="critic",
                    module=critic.critic, optimizer=critic.critic_optimizer,
                )
                if _parameter_digest(during) != pre_parameter or _optimizer_digest(during) != pre_optimizer:
                    _fail("critic/optimizer mutated before step", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_pre_step")
                step_permit = _make_permit_v1(
                    authority=authority,
                    component_kind="critic",
                    epoch=epoch,
                    minibatch=minibatch,
                    indices=partition,
                    raw_digest=raw_digest,
                    operation=B2RPermitOperationV1.OPTIMIZER_STEP,
                    critic_parameter_digest=pre_parameter,
                    critic_optimizer_digest=pre_optimizer,
                    valuenorm_digest=post_vn_digest,
                )
                ledger.consume(
                    step_permit,
                    authority=authority,
                    route_state=route_state,
                    component_kind="critic",
                    epoch=epoch,
                    minibatch=minibatch,
                    canonical_indices=partition,
                    raw_target_digest=raw_digest,
                    operation=B2RPermitOperationV1.OPTIMIZER_STEP,
                    critic_parameter_fingerprint=pre_parameter,
                    critic_optimizer_fingerprint=pre_optimizer,
                    valuenorm_fingerprint=post_vn_digest,
                )
                step_before = _optimizer_step_vector(critic.critic_optimizer)
                adam_state_before = _adam_state_evidence_v1(critic)
                _execute_critic_optimizer_step_v1(critic=critic, counter=counter)
                epoch_steps[epoch] += 1
                _validate_finite_component_state_v1(
                    owner="critic", module=critic.critic, optimizer=critic.critic_optimizer
                )
                post_critic = fingerprint_component_v1(
                    component_kind="critic", owner_identity="critic",
                    module=critic.critic, optimizer=critic.critic_optimizer,
                )
                post_actors = tuple(
                    fingerprint_component_v1(
                        component_kind="actor", owner_identity=f"actor{actor_id}",
                        module=actor.actor, optimizer=actor.actor_optimizer,
                    )
                    for actor_id, actor in enumerate(actors)
                )
                post_vn = fingerprint_component_v1(
                    component_kind="live_valuenorm", owner_identity="live_valuenorm",
                    value_normalizer=live_value_normalizer,
                )
                observed_actor_state = {
                    f"actor{actor_id}": _state_digest(fingerprint)
                    for actor_id, fingerprint in enumerate(post_actors)
                }
                expected_pre_actor_state = {
                    f"actor{actor_id}": _state_digest(fingerprint)
                    for actor_id, fingerprint in enumerate(pre_actors)
                }
                validate_actor_freeze_claim_v1(expected=expected_pre_actor_state, observed=observed_actor_state)
                parameter_mutated = _parameter_digest(post_critic) != pre_parameter
                optimizer_mutated = _optimizer_digest(post_critic) != pre_optimizer
                step_after = _optimizer_step_vector(critic.critic_optimizer)
                adam_state_after = _adam_state_evidence_v1(critic)
                increments = len(step_before) == len(step_after) and all(
                    after == before + 1.0
                    for (_, before), (_, after) in zip(step_before, step_after)
                )
                if (
                    not optimizer_mutated
                    or not increments
                    or (
                        audit.classification == VALID_NONZERO_UPDATE
                        and not parameter_mutated
                    )
                ):
                    _fail(
                        "critic/Adam mutation is not attributable to the classified step",
                        stop_code=STOP_MUTATION_ATTRIBUTION,
                        stage="r4_post_step",
                        expected=(audit.classification, True, True),
                        observed=(parameter_mutated, optimizer_mutated, increments),
                    )
                if post_vn.fingerprint_digest != post_vn_digest:
                    _fail("live ValueNorm changed outside its permitted update", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_post_step")
                if synthetic_fault == "post_step":
                    _fail("controlled failure after critic optimizer step", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_post_step_fault")
                _clear_gradients_v1(modules)
                validate_gradients_clear_v1(tuple((f"actor{index}", actor.actor) for index, actor in enumerate(actors)) + (("critic", critic.critic),))
                receipts.append(
                    B2R4CriticStepReceiptV1(
                        epoch=epoch,
                        minibatch=minibatch,
                        canonical_indices=partition,
                        raw_target_digest=raw_digest,
                        normalized_target_digest=fingerprint_tensor_v1(normalized_one).content_digest,
                        final_slot_digest=final_slot_digest,
                        valuenorm_receipt=valuenorm_receipt,
                        backward_permit_id=backward_permit.permit_id,
                        step_permit_id=step_permit.permit_id,
                        loss_value=float(loss.detach().item()),
                        aggregate_gradient_norm=audit.aggregate_norm,
                        clip_result=clip_result,
                        critic_parameter_digest_before=pre_parameter,
                        critic_parameter_digest_after=_parameter_digest(post_critic),
                        critic_optimizer_digest_before=pre_optimizer,
                        critic_optimizer_digest_after=_optimizer_digest(post_critic),
                        optimizer_step_vector_before=step_before,
                        optimizer_step_vector_after=step_after,
                        critic_parameter_mutated=parameter_mutated,
                        critic_optimizer_mutated=True,
                        valuenorm_mutated=valuenorm_receipt is not None,
                        actors_unchanged=True,
                        gradients_clean_after=True,
                        gradient_classification=audit.classification,
                        gradient_audit=audit,
                        loss_graph_evidence=loss_graph,
                        loss_decomposition=loss_decomposition,
                        adam_state_before=adam_state_before,
                        adam_state_after=adam_state_after,
                    )
                )
        observed = (
            counter.critic_backward_executed - start_backward,
            counter.critic_step_executed - start_steps,
            counter.live_valuenorm_executed - start_vn,
        )
        expected = (
            critic_plan.expected_backward_count,
            critic_plan.expected_optimizer_step_count,
            critic_plan.expected_valuenorm_update_count,
        )
        validate_count_claim_v1(expected=expected, observed=observed)
        final_actors, _, final_vn = _capture_all_v1(
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
        )
        validate_actor_freeze_claim_v1(
            expected=expected_actor_state,
            observed={f"actor{index}": _state_digest(fingerprint) for index, fingerprint in enumerate(final_actors)},
        )
        if not critic_plan.valuenorm_enabled and final_vn.fingerprint_digest != initial_vn.fingerprint_digest:
            _fail("disabled ValueNorm changed", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r4_sequence_end")
        remainder_safe = any(
            len({len(partition) for partition in epoch_partitions}) > 1
            for epoch_partitions in critic_plan.partitions_by_epoch
        )
        return B2R4CriticSequenceReceiptV1(
            plan_digest=critic_plan.plan_digest,
            target_digest=target_digest,
            final_slot_digest=final_slot_digest,
            partitions_by_epoch=critic_plan.partitions_by_epoch,
            per_epoch_backward_count=tuple(epoch_backward),
            per_epoch_step_count=tuple(epoch_steps),
            per_epoch_valuenorm_count=tuple(epoch_vn),
            observed_backward_count=observed[0],
            observed_step_count=observed[1],
            observed_valuenorm_count=observed[2],
            actor_components_unchanged=True,
            actor_optimizers_unchanged=True,
            gradients_clean_after=True,
            valuenorm_enabled=critic_plan.valuenorm_enabled,
            remainder_safe=remainder_safe,
            step_receipts=tuple(receipts),
            valid_nonzero_count=(
                counter.critic_valid_nonzero_executed - start_valid_nonzero
            ),
            valid_zero_effective_count=(
                counter.critic_valid_zero_effective_executed - start_valid_zero
            ),
        )
    except B2RContractError as exc:
        _clear_gradients_v1(modules)
        route_state.record_failure(
            stop_code=exc.stop_code,
            valuenorm_updates=counter.live_valuenorm_executed - start_vn,
            critic_steps=counter.critic_step_executed - start_steps,
        )
        raise


__all__: tuple[str, ...] = ()
