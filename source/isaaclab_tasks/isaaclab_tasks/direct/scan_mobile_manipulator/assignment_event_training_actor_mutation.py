"""Private B2-R3 controlled actor mutation and factor-attribution seam.

This module is deliberately not a trainer or coordinator.  It mutates only a
permit-bound installed HAPPO actor/Adam pair inside a controlled CPU harness,
keeps critic and live ValueNorm frozen, and emits bounded exact evidence.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_ACTOR_MUTATION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_actor_mutation"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_ACTOR_MUTATION_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R3 actor mutation must be imported "
        "under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_ACTOR_MUTATION_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, replace
import math
from typing import Mapping, Sequence

import torch

from .assignment_event_training_control import B2RPermitOperationV1
from .assignment_event_training_evidence import (
    B2RComponentFingerprintV1,
    B2RContractError,
    B2RFrozenTrainingInputsV1,
    B2RUpdateAuthorityV1,
    STOP_ACTOR_EVIDENCE_BINDING,
    STOP_AUTHORITY_DRIFT,
    STOP_OWNERSHIP,
    STOP_VALUENORM,
    canonical_digest_v1,
    fingerprint_component_v1,
    fingerprint_tensor_v1,
    validate_parameter_ownership_v1,
)
from .assignment_event_training_gradient_probe import (
    B2RProbeExecutionCounterV1,
    STOP_MUTATION_ATTRIBUTION,
    STOP_NONFINITE_GRADIENT,
    STOP_NONFINITE_LOSS,
    STOP_NONFINITE_OPTIMIZER_STATE,
    STOP_NONFINITE_PARAMETER,
    _actor_evaluate_v1,
    _clear_gradients_v1,
    _execute_backward_v1,
    _validate_finite_component_state_v1,
    _validate_finite_valuenorm_v1,
    validate_gradients_clear_v1,
)
from .assignment_event_training_plans import (
    B2RActorMinibatchPlanV1,
    B2RActorUpdatePlanV1,
    B2RFactorTransitionEvidenceV1,
    STOP_AGENT_ORDER,
    STOP_FACTOR,
    STOP_FORCED_ROW_POLICY_LEAK,
    STOP_UNEXPECTED_STEP_COUNT,
    compute_full_index_factor_transition_v1,
)


STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_NONFINITE_VALUENORM_STATE = "STOP — B2-R NONFINITE_VALUENORM_STATE"


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


def _parameter_digest(fingerprint: B2RComponentFingerprintV1) -> str:
    return canonical_digest_v1((fingerprint.parameters, fingerprint.buffers))


def _optimizer_digest(fingerprint: B2RComponentFingerprintV1) -> str:
    return canonical_digest_v1(
        (fingerprint.optimizer_groups, fingerprint.optimizer_state)
    )


def _state_digest(fingerprint: B2RComponentFingerprintV1) -> str:
    return canonical_digest_v1(replace(fingerprint, gradients=()))


def _optimizer_step_vector(optimizer: torch.optim.Optimizer) -> tuple[tuple[int, float], ...]:
    result: list[tuple[int, float]] = []
    position = 0
    for group in optimizer.param_groups:
        for parameter in group["params"]:
            state = optimizer.state.get(parameter, {})
            step = state.get("step", 0.0)
            if isinstance(step, torch.Tensor):
                step = float(step.detach().cpu().item())
            result.append((position, float(step)))
            position += 1
    return tuple(result)


@dataclass(frozen=True, slots=True)
class B2R3ActorOrderEvidenceV1:
    update_id: str
    resolved_M: int
    fixed_order: bool
    rng_algorithm: str
    rng_seed: int
    rng_state_before_digest: str
    rng_state_after_digest: str
    actor_order: tuple[int, ...]
    generation_count: int
    schema_version: str = "b2r3_actor_order_evidence_v1"

    def __post_init__(self) -> None:
        expected = tuple(range(self.resolved_M))
        if (
            self.fixed_order
            or self.rng_algorithm != "torch.Generator.cpu.randperm"
            or self.generation_count != 1
            or len(self.actor_order) != self.resolved_M
            or set(self.actor_order) != set(expected)
            or len(set(self.actor_order)) != self.resolved_M
        ):
            _fail(
                "R3 actor order is not one RNG-proven permutation",
                stop_code=STOP_AGENT_ORDER,
                stage="r3_actor_order",
                expected=expected,
                observed=self.actor_order,
            )

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


class B2R3ActorOrderFreezerV1:
    """Generate exactly one actor order for one update identity."""

    __slots__ = ("_authority", "_generated")

    def __init__(self, authority: B2RUpdateAuthorityV1) -> None:
        self._authority = authority
        self._generated = False

    def freeze(self, *, rng_seed: int) -> B2R3ActorOrderEvidenceV1:
        if self._generated:
            _fail(
                "a second actor permutation was requested for one update",
                stop_code=STOP_AGENT_ORDER,
                stage="r3_actor_order",
                expected="one generation",
                observed="second generation",
            )
        if self._authority.resolved_config.fixed_order or type(rng_seed) is not int:
            _fail(
                "R3 controlled fixture requires recorded RNG order provenance",
                stop_code=STOP_AGENT_ORDER,
                stage="r3_actor_order",
                observed=(self._authority.resolved_config.fixed_order, rng_seed),
            )
        generator = torch.Generator(device="cpu")
        generator.manual_seed(rng_seed)
        before = fingerprint_tensor_v1(generator.get_state()).content_digest
        order = tuple(
            int(item)
            for item in torch.randperm(
                self._authority.resolved_config.resolved_M, generator=generator
            ).tolist()
        )
        after = fingerprint_tensor_v1(generator.get_state()).content_digest
        self._generated = True
        return B2R3ActorOrderEvidenceV1(
            update_id=self._authority.update_id,
            resolved_M=self._authority.resolved_config.resolved_M,
            fixed_order=False,
            rng_algorithm="torch.Generator.cpu.randperm",
            rng_seed=rng_seed,
            rng_state_before_digest=before,
            rng_state_after_digest=after,
            actor_order=order,
            generation_count=1,
        )


@dataclass(frozen=True, slots=True)
class B2R3MutationAuthorityV1:
    base_authority: B2RUpdateAuthorityV1
    mutation_id: str
    slice_identity: str
    order_evidence: B2R3ActorOrderEvidenceV1
    behavior_digest_by_actor: tuple[tuple[int, str], ...]
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    schema_version: str = "b2r3_mutation_authority_v1"

    def __post_init__(self) -> None:
        expected_actors = tuple(range(self.base_authority.resolved_config.resolved_M))
        if (
            self.slice_identity != "B2-R3"
            or not self.mutation_id
            or self.order_evidence.update_id != self.base_authority.update_id
            or tuple(actor for actor, _ in self.behavior_digest_by_actor)
            != expected_actors
        ):
            _fail(
                "R3 authority/order/behavior binding drifted",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r3_authority",
                observed=(self.slice_identity, self.mutation_id),
            )
        required_allowed = {
            "actor_zero_grad",
            "actor_backward",
            "actor_gradient_clip",
            "actor_optimizer_step",
            "actor_post_step_evaluation",
            "factor_attribution",
        }
        required_forbidden = {
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
        }
        if not required_allowed.issubset(set(self.allowed_operations)) or not required_forbidden.issubset(
            set(self.forbidden_operations)
        ):
            _fail(
                "R3 allowed/forbidden operation boundary is incomplete",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r3_authority",
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
class B2R3ActorInputsV1:
    obs: torch.Tensor
    rnn_states: torch.Tensor
    actions: torch.Tensor
    masks: torch.Tensor
    available_actions: torch.Tensor
    behavior_old_logprobs: torch.Tensor
    advantages: torch.Tensor
    decision_valid_mask: torch.Tensor
    active_mask: torch.Tensor


@dataclass(frozen=True, slots=True)
class B2R3MutationPermitV1:
    permit_id: str
    update_id: str
    authority_config_digest: str
    actor_id: int
    actor_order_position: int
    epoch: int
    minibatch: int
    canonical_index_digest: str
    operation: B2RPermitOperationV1
    expected_module_fingerprint: str
    expected_optimizer_fingerprint: str
    empty_minibatch: bool
    schema_version: str = "b2r3_mutation_permit_v1"


class B2R3PermitLedgerV1:
    __slots__ = ("_consumed",)

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def consume(
        self,
        permit: B2R3MutationPermitV1 | None,
        *,
        authority: B2R3MutationAuthorityV1,
        route_state: "B2R3RouteStateV1",
        operation: B2RPermitOperationV1,
        actor_id: int,
        actor_order_position: int,
        epoch: int,
        minibatch: int,
        canonical_indices: tuple[int, ...],
        module_fingerprint: str,
        optimizer_fingerprint: str,
    ) -> None:
        if route_state.route_poisoned:
            _fail(
                "poisoned route rejected a later mutation permit",
                stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP,
                stage="r3_permit",
                expected="unpoisoned route",
                observed="poisoned",
            )
        stop = (
            STOP_UNAUTHORIZED_OPTIMIZER_STEP
            if operation is B2RPermitOperationV1.OPTIMIZER_STEP
            else "STOP — B2-R UNAUTHORIZED_BACKWARD"
        )
        if permit is None:
            _fail(
                "mutation attempted without a permit",
                stop_code=stop,
                stage="r3_permit",
                observed=None,
            )
        if permit.permit_id in self._consumed:
            _fail(
                "single-use mutation permit was consumed twice",
                stop_code=stop,
                stage="r3_permit",
                observed=permit.permit_id,
            )
        expected = (
            authority.update_id,
            authority.config_digest,
            actor_id,
            actor_order_position,
            epoch,
            minibatch,
            _indices_digest(canonical_indices),
            operation,
            module_fingerprint,
            optimizer_fingerprint,
            False,
        )
        observed = (
            permit.update_id,
            permit.authority_config_digest,
            permit.actor_id,
            permit.actor_order_position,
            permit.epoch,
            permit.minibatch,
            permit.canonical_index_digest,
            permit.operation,
            permit.expected_module_fingerprint,
            permit.expected_optimizer_fingerprint,
            permit.empty_minibatch,
        )
        if observed != expected or not canonical_indices:
            _fail(
                "mutation permit does not bind the exact actor minibatch state",
                stop_code=stop,
                stage="r3_permit",
                expected=expected,
                observed=observed,
            )
        self._consumed.add(permit.permit_id)


@dataclass(frozen=True, slots=True)
class B2R3FailureEvidenceV1:
    stop_code: str
    partial_update: bool
    route_poisoned: bool
    rollover_allowed: bool
    checkpoint_allowed: bool
    next_rollout_allowed: bool
    public_use_allowed: bool
    actor_step_count_before_failure: int
    schema_version: str = "b2r3_failure_evidence_v1"


class B2R3RouteStateV1:
    __slots__ = ("partial_update", "route_poisoned", "last_failure")

    def __init__(self) -> None:
        self.partial_update = False
        self.route_poisoned = False
        self.last_failure: B2R3FailureEvidenceV1 | None = None

    def record_failure(self, *, stop_code: str, executed_steps: int) -> None:
        partial = executed_steps > 0
        self.partial_update = partial
        self.route_poisoned = partial
        self.last_failure = B2R3FailureEvidenceV1(
            stop_code=stop_code,
            partial_update=partial,
            route_poisoned=partial,
            rollover_allowed=False if partial else True,
            checkpoint_allowed=False,
            next_rollout_allowed=False if partial else True,
            public_use_allowed=False,
            actor_step_count_before_failure=executed_steps,
        )


class B2R3ExecutionCounterV1:
    __slots__ = (
        "actor_backward_by_actor",
        "actor_step_by_actor",
        "actor_step_attempted",
        "unauthorized_actor_step_attempted",
        "critic_backward_executed",
        "critic_step_attempted",
        "critic_step_executed",
        "live_valuenorm_attempted",
        "live_valuenorm_executed",
        "scheduler_step_executed",
    )

    def __init__(self, resolved_M: int) -> None:
        self.actor_backward_by_actor = [0] * resolved_M
        self.actor_step_by_actor = [0] * resolved_M
        self.actor_step_attempted = 0
        self.unauthorized_actor_step_attempted = 0
        self.critic_backward_executed = 0
        self.critic_step_attempted = 0
        self.critic_step_executed = 0
        self.live_valuenorm_attempted = 0
        self.live_valuenorm_executed = 0
        self.scheduler_step_executed = 0

    @property
    def actor_backward_executed(self) -> int:
        return sum(self.actor_backward_by_actor)

    @property
    def actor_step_executed(self) -> int:
        return sum(self.actor_step_by_actor)


class B2R3CriticStepTrapV1:
    __slots__ = ("counter",)

    def __init__(self, counter: B2R3ExecutionCounterV1) -> None:
        self.counter = counter

    def step(self) -> None:
        self.counter.critic_step_attempted += 1
        _fail(
            "R3 critic optimizer step is forbidden",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="r3_critic_step_trap",
        )


class B2R3LiveValueNormTrapV1:
    __slots__ = ("counter",)

    def __init__(self, counter: B2R3ExecutionCounterV1) -> None:
        self.counter = counter

    def update(self, _: torch.Tensor) -> None:
        self.counter.live_valuenorm_attempted += 1
        _fail(
            "R3 live ValueNorm update is forbidden",
            stop_code=STOP_VALUENORM,
            stage="r3_live_valuenorm_trap",
        )


@dataclass(frozen=True, slots=True)
class B2R3StepReceiptV1:
    actor_id: int
    actor_order_position: int
    epoch: int
    minibatch: int
    loss_indices: tuple[int, ...]
    backward_permit_id: str
    step_permit_id: str
    loss_value: float
    aggregate_gradient_norm: float
    clip_result: float
    parameter_digest_before: str
    parameter_digest_after: str
    optimizer_digest_before: str
    optimizer_digest_after: str
    optimizer_step_vector_before: tuple[tuple[int, float], ...]
    optimizer_step_vector_after: tuple[tuple[int, float], ...]
    target_parameter_mutated: bool
    target_optimizer_mutated: bool
    foreign_components_unchanged: bool
    gradients_clean_after: bool
    factor_used_digest: str
    schema_version: str = "b2r3_step_receipt_v1"


@dataclass(frozen=True, slots=True)
class B2R3ActorSegmentReceiptV1:
    actor_id: int
    actor_order_position: int
    skipped: bool
    expected_backward_count: int
    expected_step_count: int
    observed_backward_count: int
    observed_step_count: int
    factor_pre_evaluation_count: int
    factor_post_evaluation_count: int
    factor_update_count: int
    behavior_old_logprob_field: str
    factor_pre_logprob_field: str
    factor_post_logprob_field: str
    factor_pre_logprob_digest: str | None
    factor_post_logprob_digest: str | None
    dvm_indices: tuple[int, ...]
    factor_before_digest: str
    loss_factor_digests: tuple[str, ...]
    prior_accumulation_witness_indices: tuple[int, ...]
    prior_accumulation_preserved: bool
    factor_transition: B2RFactorTransitionEvidenceV1
    step_receipts: tuple[B2R3StepReceiptV1, ...]
    schema_version: str = "b2r3_actor_segment_receipt_v1"


@dataclass(frozen=True, slots=True)
class B2R3SequenceReceiptV1:
    actor_order: tuple[int, ...]
    order_evidence_digest: str
    actor_segments: tuple[B2R3ActorSegmentReceiptV1, ...]
    initial_factor_digest: str
    final_factor_digest: str
    critic_unchanged: bool
    critic_optimizer_unchanged: bool
    live_valuenorm_unchanged: bool
    gradients_clean_after: bool
    schema_version: str = "b2r3_sequence_receipt_v1"


def _capture_components_v1(
    *, actors: Sequence[object], critic: object, live_value_normalizer: object
) -> tuple[tuple[B2RComponentFingerprintV1, ...], B2RComponentFingerprintV1, B2RComponentFingerprintV1]:
    actor_bindings = tuple(
        (f"actor{index}", actor.actor, actor.actor_optimizer)
        for index, actor in enumerate(actors)
    )
    critic_binding = ("critic", critic.critic, critic.critic_optimizer)
    validate_parameter_ownership_v1(
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        shared_parameter_mode=False,
    )
    validate_gradients_clear_v1(
        tuple((owner, module) for owner, module, _ in actor_bindings)
        + (("critic", critic.critic),)
    )
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


def _canonical_true_row_indices_v1(mask: torch.Tensor) -> tuple[int, ...]:
    """Return canonical row indices for either [B] or [B,1] masks."""

    if mask.ndim not in (1, 2) or (mask.ndim == 2 and mask.shape[1] != 1):
        _fail(
            "row mask is not canonical [B] or [B,1]",
            stop_code=STOP_FACTOR,
            stage="r3_row_index_binding",
            expected="[B] or [B,1]",
            observed=tuple(mask.shape),
        )
    return tuple(
        int(item)
        for item in mask.reshape(-1).nonzero(as_tuple=False).flatten().tolist()
    )


def _evaluate_factor_logprob_v1(
    *, actor: object, inputs: B2R3ActorInputsV1, shape: tuple[int, int, int]
) -> tuple[torch.Tensor, tuple[int, ...]]:
    indices = _canonical_true_row_indices_v1(inputs.decision_valid_mask)
    full = torch.zeros(shape, dtype=inputs.obs.dtype, device=inputs.obs.device)
    if indices:
        with torch.no_grad():
            values, _ = _actor_evaluate_v1(
                actor=actor,
                indices=indices,
                obs=inputs.obs,
                rnn_states=inputs.rnn_states,
                actions=inputs.actions,
                masks=inputs.masks,
                available_actions=inputs.available_actions,
                active_masks=None,
            )
        full.reshape(-1, 1)[
            torch.tensor(indices, dtype=torch.long, device=inputs.obs.device)
        ] = values
    return full, indices


def _actor_loss_v1(
    *,
    actor: object,
    inputs: B2R3ActorInputsV1,
    loss_indices: tuple[int, ...],
    factor_before: torch.Tensor,
) -> torch.Tensor:
    active = torch.ones(
        (len(loss_indices), 1), dtype=torch.float32, device=inputs.obs.device
    )
    current_logprobs, entropy = _actor_evaluate_v1(
        actor=actor,
        indices=loss_indices,
        obs=inputs.obs,
        rnn_states=inputs.rnn_states,
        actions=inputs.actions,
        masks=inputs.masks,
        available_actions=inputs.available_actions,
        active_masks=active,
    )
    index = torch.tensor(loss_indices, dtype=torch.long, device=inputs.obs.device)
    old = inputs.behavior_old_logprobs[index]
    importance = torch.prod(torch.exp(current_logprobs - old), dim=-1, keepdim=True)
    advantage = inputs.advantages[index]
    factor_batch = factor_before.reshape(-1, 1)[index]
    surrogate_one = importance * advantage
    surrogate_two = torch.clamp(
        importance, 1.0 - float(actor.clip_param), 1.0 + float(actor.clip_param)
    ) * advantage
    policy_loss = -(
        factor_batch * torch.minimum(surrogate_one, surrogate_two)
    ).sum() / float(len(loss_indices))
    return policy_loss - entropy * float(actor.entropy_coef)


def validate_pre_step_gate_v1(
    *,
    loss_finite: bool,
    owned_gradients_finite: bool,
    aggregate_gradient_norm: float,
    clip_result: float,
    foreign_gradient_names: tuple[str, ...],
) -> None:
    if not loss_finite:
        _fail("actor loss is nonfinite", stop_code=STOP_NONFINITE_LOSS, stage="r3_pre_step")
    if not owned_gradients_finite or not math.isfinite(aggregate_gradient_norm):
        _fail("actor gradients are nonfinite", stop_code=STOP_NONFINITE_GRADIENT, stage="r3_pre_step")
    if not math.isfinite(clip_result):
        _fail("actor clipping result is nonfinite", stop_code=STOP_NONFINITE_GRADIENT, stage="r3_pre_step")
    if foreign_gradient_names:
        _fail("foreign gradient exists before actor step", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r3_pre_step", observed=foreign_gradient_names)


def validate_foreign_state_claim_v1(
    *, expected: Mapping[str, str], observed: Mapping[str, str]
) -> None:
    if dict(expected) != dict(observed):
        _fail(
            "foreign component changed during target actor mutation",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="r3_post_step_foreign_audit",
            expected=dict(expected),
            observed=dict(observed),
        )


def validate_factor_segment_contract_v1(
    receipt: B2R3ActorSegmentReceiptV1,
    *,
    expected_dvm_indices: tuple[int, ...],
) -> None:
    if receipt.dvm_indices != expected_dvm_indices:
        _fail("factor post rows differ from the frozen DVM rows", stop_code=STOP_FACTOR, stage="r3_factor_segment")
    if receipt.skipped:
        if receipt.factor_update_count != 1 or receipt.factor_before_digest != receipt.factor_transition.factor_after_digest or not receipt.prior_accumulation_preserved:
            _fail("skipped actor reset or changed accumulated factor", stop_code=STOP_FACTOR, stage="r3_factor_segment")
        return
    if (
        receipt.behavior_old_logprob_field != "original_rollout_behavior_logprob"
        or receipt.factor_pre_logprob_field != "factor_pre_logprob"
        or receipt.factor_post_logprob_field != "factor_post_logprob"
        or len({receipt.behavior_old_logprob_field, receipt.factor_pre_logprob_field, receipt.factor_post_logprob_field}) != 3
        or
        receipt.factor_pre_evaluation_count != 1
        or receipt.factor_post_evaluation_count != 1
        or receipt.factor_update_count != 1
        or receipt.factor_pre_logprob_digest is None
        or receipt.factor_post_logprob_digest is None
        or any(value != receipt.factor_before_digest for value in receipt.loss_factor_digests)
        or not receipt.prior_accumulation_preserved
    ):
        _fail(
            "factor pre/post identity or temporal direction drifted",
            stop_code=STOP_FACTOR,
            stage="r3_factor_segment",
        )


def _make_permit_v1(
    *,
    authority: B2R3MutationAuthorityV1,
    actor_id: int,
    actor_order_position: int,
    minibatch: B2RActorMinibatchPlanV1,
    operation: B2RPermitOperationV1,
    module_fingerprint: str,
    optimizer_fingerprint: str,
) -> B2R3MutationPermitV1:
    return B2R3MutationPermitV1(
        permit_id=f"{authority.mutation_id}:{actor_id}:{minibatch.epoch}:{minibatch.minibatch}:{operation.value}",
        update_id=authority.update_id,
        authority_config_digest=authority.config_digest,
        actor_id=actor_id,
        actor_order_position=actor_order_position,
        epoch=minibatch.epoch,
        minibatch=minibatch.minibatch,
        canonical_index_digest=_indices_digest(minibatch.active_and_dvm_loss_indices),
        operation=operation,
        expected_module_fingerprint=module_fingerprint,
        expected_optimizer_fingerprint=optimizer_fingerprint,
        empty_minibatch=minibatch.empty_loss,
    )


def consume_actor_step_permit_v1(
    *,
    ledger: B2R3PermitLedgerV1,
    permit: B2R3MutationPermitV1 | None,
    authority: B2R3MutationAuthorityV1,
    route_state: B2R3RouteStateV1,
    actor_id: int,
    actor_order_position: int,
    epoch: int,
    minibatch: int,
    canonical_indices: tuple[int, ...],
    module_fingerprint: str,
    optimizer_fingerprint: str,
    counter: B2R3ExecutionCounterV1,
) -> None:
    counter.actor_step_attempted += 1
    try:
        ledger.consume(
            permit,
            authority=authority,
            route_state=route_state,
            operation=B2RPermitOperationV1.OPTIMIZER_STEP,
            actor_id=actor_id,
            actor_order_position=actor_order_position,
            epoch=epoch,
            minibatch=minibatch,
            canonical_indices=canonical_indices,
            module_fingerprint=module_fingerprint,
            optimizer_fingerprint=optimizer_fingerprint,
        )
    except B2RContractError:
        counter.unauthorized_actor_step_attempted += 1
        raise


def _execute_actor_optimizer_step_v1(
    *, target: object, actor_id: int, counter: B2R3ExecutionCounterV1
) -> None:
    target.actor_optimizer.step()
    counter.actor_step_by_actor[actor_id] += 1


def execute_actor_sequence_v1(
    *,
    authority: B2R3MutationAuthorityV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    actor_plan: B2RActorUpdatePlanV1,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    actor_inputs: Mapping[int, B2R3ActorInputsV1],
    initial_factor: torch.Tensor,
    route_state: B2R3RouteStateV1,
    counter: B2R3ExecutionCounterV1,
    claimed_actor_order: Sequence[int] | None = None,
    synthetic_post_step_fault_actor: int | None = None,
) -> B2R3SequenceReceiptV1:
    """Run one controlled sequential actor-only update under frozen evidence."""

    start_steps = counter.actor_step_executed
    modules = tuple(actor.actor for actor in actors) + (critic.critic,)
    try:
        order = authority.order_evidence.actor_order
        claimed = order if claimed_actor_order is None else tuple(claimed_actor_order)
        if (
            claimed != order
            or actor_plan.actor_permutation != order
            or actor_plan.update_id != authority.update_id
            or actor_plan.authority_config_digest != authority.config_digest
            or actor_plan.optimizer_step_policy != "match_backward"
        ):
            _fail(
                "actor sequence order/plan authority changed after freeze",
                stop_code=STOP_AGENT_ORDER,
                stage="r3_sequence_start",
                expected=order,
                observed=(claimed, actor_plan.actor_permutation),
            )
        if set(actor_inputs) != set(order) or len(actors) != len(order):
            _fail("actor inputs are missing or duplicated", stop_code=STOP_AGENT_ORDER, stage="r3_sequence_start")
        combined_behavior = canonical_digest_v1(
            tuple(
                (actor_id, fingerprint_tensor_v1(actor_inputs[actor_id].behavior_old_logprobs).content_digest)
                for actor_id in range(len(actors))
            )
        )
        if (
            frozen_inputs.update_id != authority.update_id
            or frozen_inputs.authority_config_digest != authority.config_digest
            or frozen_inputs.original_behavior_logprob_digest != combined_behavior
            or tuple(authority.behavior_digest_by_actor)
            != tuple(
                (actor_id, fingerprint_tensor_v1(actor_inputs[actor_id].behavior_old_logprobs).content_digest)
                for actor_id in range(len(actors))
            )
        ):
            _fail("actor behavior evidence is not frozen", stop_code=STOP_ACTOR_EVIDENCE_BINDING, stage="r3_sequence_start")
        factor = initial_factor.detach().clone().contiguous()
        initial_factor_digest = fingerprint_tensor_v1(factor).content_digest
        if initial_factor_digest != actor_plan.factor_input_digest:
            _fail("initial factor does not bind the actor plan", stop_code=STOP_FACTOR, stage="r3_sequence_start")
        initial_actors, initial_critic, initial_vn = _capture_components_v1(
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
        )
        expected_backward = dict(actor_plan.expected_backward_count_by_actor)
        expected_steps = dict(actor_plan.expected_optimizer_step_count_by_actor)
        segments: list[B2R3ActorSegmentReceiptV1] = []
        ledger = B2R3PermitLedgerV1()
        r2_counter = B2RProbeExecutionCounterV1()
        for position, actor_id in enumerate(order):
            target = actors[actor_id]
            inputs = actor_inputs[actor_id]
            segment_batches = tuple(
                item for item in actor_plan.minibatches if item.actor_id == actor_id
            )
            segment_factor = factor.detach().clone().contiguous()
            factor_before_digest = fingerprint_tensor_v1(segment_factor).content_digest
            observed_backward = 0
            observed_steps = 0
            step_receipts: list[B2R3StepReceiptV1] = []
            loss_factor_digests: list[str] = []
            if expected_steps[actor_id] == 0:
                transition = compute_full_index_factor_transition_v1(
                    actor_id=actor_id,
                    factor_before=segment_factor,
                    decision_valid_mask=inputs.decision_valid_mask.reshape(factor.shape),
                    factor_pre_logprob=torch.zeros_like(factor),
                    factor_post_logprob=torch.zeros_like(factor),
                    skipped_actor=True,
                )
                skipped_after = transition.factor_after.reshape(-1, 1)
                skipped_before = segment_factor.reshape(-1, 1)
                witnesses = tuple(
                    int(index)
                    for index in range(skipped_before.shape[0])
                    if not torch.equal(skipped_before[index], torch.ones_like(skipped_before[index]))
                )
                preserved = all(torch.equal(skipped_after[index], skipped_before[index]) for index in witnesses)
                segment = B2R3ActorSegmentReceiptV1(
                    actor_id, position, True, expected_backward[actor_id], expected_steps[actor_id],
                    0, 0, 0, 0, 1,
                    actor_plan.behavior_old_logprob_field, actor_plan.factor_pre_logprob_field, actor_plan.factor_post_logprob_field,
                    None, None, (), factor_before_digest, (),
                    witnesses, preserved, transition.evidence, (),
                )
                validate_factor_segment_contract_v1(segment, expected_dvm_indices=())
                segments.append(segment)
                factor = transition.factor_after
                continue
            factor_pre, dvm_indices = _evaluate_factor_logprob_v1(
                actor=target, inputs=inputs, shape=tuple(factor.shape)
            )
            for minibatch in segment_batches:
                if minibatch.empty_loss:
                    continue
                actual_loss = tuple(
                    index
                    for index in minibatch.canonical_partition_indices
                    if bool(inputs.decision_valid_mask[index].item())
                    and bool(inputs.active_mask[index].item())
                )
                if actual_loss != minibatch.active_and_dvm_loss_indices:
                    _fail("actor loss rows drifted from active-and-DVM plan", stop_code=STOP_FORCED_ROW_POLICY_LEAK, stage="r3_actor_segment")
                pre_actors, pre_critic, pre_vn = _capture_components_v1(
                    actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
                )
                pre_target = pre_actors[actor_id]
                target.actor_optimizer.zero_grad(set_to_none=True)
                loss = _actor_loss_v1(
                    actor=target,
                    inputs=inputs,
                    loss_indices=actual_loss,
                    factor_before=segment_factor,
                )
                if not bool(torch.isfinite(loss.detach()).all().item()):
                    _fail("actor loss is nonfinite", stop_code=STOP_NONFINITE_LOSS, stage="r3_actor_loss")
                backward_permit = _make_permit_v1(
                    authority=authority,
                    actor_id=actor_id,
                    actor_order_position=position,
                    minibatch=minibatch,
                    operation=B2RPermitOperationV1.BACKWARD,
                    module_fingerprint=_parameter_digest(pre_target),
                    optimizer_fingerprint=_optimizer_digest(pre_target),
                )
                ledger.consume(
                    backward_permit,
                    authority=authority,
                    route_state=route_state,
                    operation=B2RPermitOperationV1.BACKWARD,
                    actor_id=actor_id,
                    actor_order_position=position,
                    epoch=minibatch.epoch,
                    minibatch=minibatch.minibatch,
                    canonical_indices=actual_loss,
                    module_fingerprint=_parameter_digest(pre_target),
                    optimizer_fingerprint=_optimizer_digest(pre_target),
                )
                foreign = tuple(
                    (f"actor{index}", item.actor)
                    for index, item in enumerate(actors)
                    if index != actor_id
                ) + (("critic", critic.critic),)
                audit = _execute_backward_v1(
                    loss=loss,
                    component_kind="actor",
                    owner_identity=f"actor{actor_id}",
                    target_module=target.actor,
                    foreign_bindings=foreign,
                    counter=r2_counter,
                    require_nonzero=True,
                )
                counter.actor_backward_by_actor[actor_id] += 1
                observed_backward += 1
                if target.use_max_grad_norm:
                    clip_value = torch.nn.utils.clip_grad_norm_(
                        target.actor.parameters(), target.max_grad_norm
                    )
                    clip_result = float(clip_value.detach().item() if isinstance(clip_value, torch.Tensor) else clip_value)
                else:
                    clip_result = audit.aggregate_norm
                validate_pre_step_gate_v1(
                    loss_finite=True,
                    owned_gradients_finite=audit.finite,
                    aggregate_gradient_norm=audit.aggregate_norm,
                    clip_result=clip_result,
                    foreign_gradient_names=audit.foreign_gradient_names,
                )
                during = fingerprint_component_v1(
                    component_kind="actor",
                    owner_identity=f"actor{actor_id}",
                    module=target.actor,
                    optimizer=target.actor_optimizer,
                )
                if _parameter_digest(during) != _parameter_digest(pre_target) or _optimizer_digest(during) != _optimizer_digest(pre_target):
                    _fail("actor/optimizer mutated before authorized step", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r3_pre_step")
                step_permit = _make_permit_v1(
                    authority=authority,
                    actor_id=actor_id,
                    actor_order_position=position,
                    minibatch=minibatch,
                    operation=B2RPermitOperationV1.OPTIMIZER_STEP,
                    module_fingerprint=_parameter_digest(during),
                    optimizer_fingerprint=_optimizer_digest(during),
                )
                consume_actor_step_permit_v1(
                    ledger=ledger,
                    permit=step_permit,
                    authority=authority,
                    route_state=route_state,
                    actor_id=actor_id,
                    actor_order_position=position,
                    epoch=minibatch.epoch,
                    minibatch=minibatch.minibatch,
                    canonical_indices=actual_loss,
                    module_fingerprint=_parameter_digest(during),
                    optimizer_fingerprint=_optimizer_digest(during),
                    counter=counter,
                )
                step_vector_before = _optimizer_step_vector(target.actor_optimizer)
                _execute_actor_optimizer_step_v1(
                    target=target, actor_id=actor_id, counter=counter
                )
                observed_steps += 1
                _validate_finite_component_state_v1(
                    owner=f"actor{actor_id}",
                    module=target.actor,
                    optimizer=target.actor_optimizer,
                )
                post_actors = tuple(
                    fingerprint_component_v1(
                        component_kind="actor",
                        owner_identity=f"actor{index}",
                        module=item.actor,
                        optimizer=item.actor_optimizer,
                    )
                    for index, item in enumerate(actors)
                )
                post_critic = fingerprint_component_v1(
                    component_kind="critic", owner_identity="critic",
                    module=critic.critic, optimizer=critic.critic_optimizer,
                )
                post_vn = fingerprint_component_v1(
                    component_kind="live_valuenorm", owner_identity="live_valuenorm",
                    value_normalizer=live_value_normalizer,
                )
                post_target = post_actors[actor_id]
                parameter_mutated = _parameter_digest(post_target) != _parameter_digest(pre_target)
                optimizer_mutated = _optimizer_digest(post_target) != _optimizer_digest(pre_target)
                step_vector_after = _optimizer_step_vector(target.actor_optimizer)
                increments_valid = all(after == before + 1.0 for (_, before), (_, after) in zip(step_vector_before, step_vector_after))
                foreign_expected = {
                    **{f"actor{index}": _state_digest(pre_actors[index]) for index in range(len(actors)) if index != actor_id},
                    "critic": _state_digest(pre_critic),
                    "live_valuenorm": _state_digest(pre_vn),
                }
                foreign_observed = {
                    **{f"actor{index}": _state_digest(post_actors[index]) for index in range(len(actors)) if index != actor_id},
                    "critic": _state_digest(post_critic),
                    "live_valuenorm": _state_digest(post_vn),
                }
                validate_foreign_state_claim_v1(expected=foreign_expected, observed=foreign_observed)
                if not parameter_mutated or not optimizer_mutated or not increments_valid:
                    _fail("target actor/Adam mutation is not attributable to exactly one step", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r3_post_step", observed=(parameter_mutated, optimizer_mutated, step_vector_before, step_vector_after))
                _clear_gradients_v1(modules)
                validate_gradients_clear_v1(tuple((f"actor{index}", item.actor) for index, item in enumerate(actors)) + (("critic", critic.critic),))
                loss_factor_digest = fingerprint_tensor_v1(segment_factor).content_digest
                loss_factor_digests.append(loss_factor_digest)
                step_receipts.append(
                    B2R3StepReceiptV1(
                        actor_id, position, minibatch.epoch, minibatch.minibatch, actual_loss,
                        backward_permit.permit_id, step_permit.permit_id,
                        float(loss.detach().item()), audit.aggregate_norm, clip_result,
                        _parameter_digest(pre_target), _parameter_digest(post_target),
                        _optimizer_digest(pre_target), _optimizer_digest(post_target),
                        step_vector_before, step_vector_after, True, True, True, True,
                        loss_factor_digest,
                    )
                )
                if synthetic_post_step_fault_actor == actor_id:
                    _fail("controlled fault after legitimate actor step and before factor completion", stop_code=STOP_FACTOR, stage="r3_post_step_fault")
            if observed_backward != expected_backward[actor_id] or observed_steps != expected_steps[actor_id]:
                _fail("actor observed counts differ from frozen plan", stop_code=STOP_UNEXPECTED_STEP_COUNT, stage="r3_actor_segment", expected=(expected_backward[actor_id], expected_steps[actor_id]), observed=(observed_backward, observed_steps))
            factor_post, post_indices = _evaluate_factor_logprob_v1(
                actor=target, inputs=inputs, shape=tuple(factor.shape)
            )
            if post_indices != dvm_indices:
                _fail("factor post evaluation rows differ from factor pre rows", stop_code=STOP_FACTOR, stage="r3_factor_post")
            transition = compute_full_index_factor_transition_v1(
                actor_id=actor_id,
                factor_before=segment_factor,
                decision_valid_mask=inputs.decision_valid_mask.reshape(factor.shape),
                factor_pre_logprob=factor_pre,
                factor_post_logprob=factor_post,
            )
            flat_before = segment_factor.reshape(-1, 1)
            flat_after = transition.factor_after.reshape(-1, 1)
            off_dvm = ~inputs.decision_valid_mask
            witnesses = tuple(
                index
                for index in _canonical_true_row_indices_v1(off_dvm)
                if not torch.equal(flat_before[index], torch.ones_like(flat_before[index]))
            )
            preserved = all(torch.equal(flat_after[index], flat_before[index]) for index in witnesses)
            segment = B2R3ActorSegmentReceiptV1(
                actor_id, position, False, expected_backward[actor_id], expected_steps[actor_id],
                observed_backward, observed_steps, 1, 1, 1,
                actor_plan.behavior_old_logprob_field, actor_plan.factor_pre_logprob_field, actor_plan.factor_post_logprob_field,
                fingerprint_tensor_v1(factor_pre).content_digest,
                fingerprint_tensor_v1(factor_post).content_digest,
                dvm_indices, factor_before_digest, tuple(loss_factor_digests),
                witnesses, preserved, transition.evidence, tuple(step_receipts),
            )
            validate_factor_segment_contract_v1(segment, expected_dvm_indices=dvm_indices)
            segments.append(segment)
            factor = transition.factor_after
        final_actors, final_critic, final_vn = _capture_components_v1(
            actors=actors, critic=critic, live_value_normalizer=live_value_normalizer
        )
        if _state_digest(final_critic) != _state_digest(initial_critic) or _state_digest(final_vn) != _state_digest(initial_vn):
            _fail("critic or live ValueNorm changed during actor-only sequence", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r3_sequence_end")
        for actor_id in range(len(actors)):
            expected = expected_steps[actor_id]
            changed = _state_digest(final_actors[actor_id]) != _state_digest(initial_actors[actor_id])
            if changed is not (expected > 0):
                _fail("actor final mutation classification differs from plan", stop_code=STOP_MUTATION_ATTRIBUTION, stage="r3_sequence_end", observed=(actor_id, changed, expected))
        validate_gradients_clear_v1(tuple((f"actor{index}", item.actor) for index, item in enumerate(actors)) + (("critic", critic.critic),))
        return B2R3SequenceReceiptV1(
            actor_order=order,
            order_evidence_digest=authority.order_evidence.evidence_digest,
            actor_segments=tuple(segments),
            initial_factor_digest=initial_factor_digest,
            final_factor_digest=fingerprint_tensor_v1(factor).content_digest,
            critic_unchanged=True,
            critic_optimizer_unchanged=True,
            live_valuenorm_unchanged=True,
            gradients_clean_after=True,
        )
    except B2RContractError as exc:
        _clear_gradients_v1(modules)
        route_state.record_failure(
            stop_code=exc.stop_code,
            executed_steps=counter.actor_step_executed - start_steps,
        )
        raise


__all__: tuple[str, ...] = ()
