"""Private B2-R2 real-autograd, no-step controlled gradient probes.

This module may execute a permit-bound ``Tensor.backward`` and clear gradients.
It cannot delegate an optimizer step or a live ValueNorm update.  It is not a
trainer, runner, rollout component, or public-route coordinator.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_PROBE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_gradient_probe"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_PROBE_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R2 gradient probe must be imported "
        "under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_PROBE_MODULE!r}; "
        f"actual={__name__!r}"
    )


import copy
from dataclasses import dataclass, replace
import math
from typing import Mapping, Sequence

import torch

from .assignment_event_training_control import (
    B2RMutationPermitV1,
    B2RPermitLedgerV1,
    B2RPermitOperationV1,
    B2RUpdateStageV1,
    B2RUpdateStateMachineV1,
    STOP_MODE_ORDER,
    STOP_UNAUTHORIZED_BACKWARD,
    STOP_UNAUTHORIZED_OPTIMIZER_STEP,
)
from .assignment_event_training_evidence import (
    B2RComponentFingerprintV1,
    B2RContractError,
    B2RFrozenTrainingInputsV1,
    B2RUpdateAuthorityV1,
    STOP_ACTOR_EVIDENCE_BINDING,
    STOP_AUTHORITY_DRIFT,
    STOP_NONFINITE_VALUENORM_STATE,
    STOP_OWNERSHIP,
    STOP_VALUENORM,
    canonical_live_valuenorm_state_v1,
    canonical_digest_v1,
    fingerprint_component_v1,
    fingerprint_tensor_v1,
    validate_parameter_ownership_v1,
)
from .assignment_event_training_plans import (
    B2RActorMinibatchPlanV1,
    B2RActorUpdatePlanV1,
    B2RCriticUpdatePlanV1,
    STOP_CRITIC_ROW_COVERAGE,
    STOP_FORCED_ROW_POLICY_LEAK,
)


B2R_GRADIENT_PARAMETER_EVIDENCE_V1 = "b2r_gradient_parameter_evidence_v1"
B2R_GRADIENT_AUDIT_V1 = "b2r_gradient_audit_v1"
B2R_LOSS_GRAPH_EVIDENCE_V1 = "b2r_loss_graph_evidence_v1"
B2R_PROBE_SNAPSHOT_V1 = "b2r_probe_snapshot_v1"
B2R_BACKWARD_PROBE_RECEIPT_V1 = "b2r_backward_probe_receipt_v1"
B2R2_PROBE_AUTHORITY_V1 = "b2r2_probe_authority_v1"

STOP_NONFINITE_TARGET = "STOP — B2-R NONFINITE_TARGET"
STOP_NONFINITE_LOSS = "STOP — B2-R NONFINITE_LOSS"
STOP_NONFINITE_GRADIENT = "STOP — B2-R NONFINITE_GRADIENT"
STOP_NONFINITE_PARAMETER = "STOP — B2-R NONFINITE_PARAMETER"
STOP_NONFINITE_OPTIMIZER_STATE = "STOP — B2-R NONFINITE_OPTIMIZER_STATE"
STOP_MUTATION_ATTRIBUTION = "STOP — B2-R MUTATION_ATTRIBUTION"
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_UNEXPECTED_STEP_COUNT = "STOP — B2-R UNEXPECTED_STEP_COUNT"

VALID_NONZERO_UPDATE = "VALID_NONZERO_UPDATE"
VALID_ZERO_EFFECTIVE_UPDATE = "VALID_ZERO_EFFECTIVE_UPDATE"
GRAPH_DISCONNECT_OR_UNUSED = "GRAPH_DISCONNECT_OR_UNUSED"
NONFINITE_GRADIENT_CLASS = "NONFINITE"
OWNERSHIP_OR_FOREIGN_GRADIENT_FAILURE = "OWNERSHIP_OR_FOREIGN_GRADIENT_FAILURE"


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


def _component_state_digest(fingerprint: B2RComponentFingerprintV1) -> str:
    """Digest component state while intentionally excluding ephemeral grads."""

    return canonical_digest_v1(replace(fingerprint, gradients=()))


def _tensor_indices_digest(indices: Sequence[int]) -> str:
    return canonical_digest_v1(tuple(indices))


def _module_parameters(module: torch.nn.Module) -> tuple[torch.nn.Parameter, ...]:
    return tuple(module.parameters())


def _all_parameters(
    actor_bindings: Sequence[tuple[str, torch.nn.Module, torch.optim.Optimizer]],
    critic_binding: tuple[str, torch.nn.Module, torch.optim.Optimizer],
) -> tuple[torch.nn.Parameter, ...]:
    return tuple(
        parameter
        for _, module, _ in tuple(actor_bindings) + (critic_binding,)
        for parameter in module.parameters()
    )


def _clear_gradients_v1(modules: Sequence[torch.nn.Module]) -> None:
    for module in modules:
        for parameter in module.parameters():
            parameter.grad = None


def validate_gradients_clear_v1(
    bindings: Sequence[tuple[str, torch.nn.Module]],
) -> None:
    dirty = tuple(
        f"{owner}.{name}"
        for owner, module in bindings
        for name, parameter in module.named_parameters()
        if parameter.grad is not None
    )
    if dirty:
        _fail(
            "probe requires an exact no-gradient start/restoration state",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="gradient_quiescence",
            expected="all gradients absent",
            observed=dirty[:16],
        )


def _validate_finite_component_state_v1(
    *,
    owner: str,
    module: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
) -> None:
    for name, parameter in module.named_parameters():
        if not bool(torch.isfinite(parameter.detach()).all().item()):
            _fail(
                "module parameter is nonfinite",
                stop_code=STOP_NONFINITE_PARAMETER,
                stage="pre_probe_finite_state",
                field_name=f"{owner}.{name}",
                expected="finite parameter",
                observed="nonfinite",
            )
    for parameter, state in optimizer.state.items():
        for key, value in state.items():
            if isinstance(value, torch.Tensor) and not bool(torch.isfinite(value.detach()).all().item()):
                _fail(
                    "optimizer tensor state is nonfinite",
                    stop_code=STOP_NONFINITE_OPTIMIZER_STATE,
                    stage="pre_probe_finite_state",
                    field_name=f"{owner}.optimizer.{key}",
                    expected="finite optimizer state",
                    observed="nonfinite",
                )
            if type(value) is float and not math.isfinite(value):
                _fail(
                    "optimizer scalar state is nonfinite",
                    stop_code=STOP_NONFINITE_OPTIMIZER_STATE,
                    stage="pre_probe_finite_state",
                    field_name=f"{owner}.optimizer.{key}",
                    expected="finite optimizer state",
                    observed=value,
                )


def _validate_finite_valuenorm_v1(value_normalizer: object) -> None:
    canonical_live_valuenorm_state_v1(value_normalizer)


@dataclass(frozen=True, slots=True)
class B2RGradientParameterEvidenceV1:
    parameter_name: str
    requires_grad: bool
    present: bool
    shape: tuple[int, ...] | None
    dtype: str | None
    device: str | None
    finite: bool | None
    content_digest: str | None
    norm: float | None
    nonzero: bool | None
    schema_version: str = B2R_GRADIENT_PARAMETER_EVIDENCE_V1


@dataclass(frozen=True, slots=True)
class B2RLossGraphEvidenceV1:
    current_values_requires_grad: bool
    current_values_grad_fn: str | None
    value_loss_requires_grad: bool
    value_loss_grad_fn: str | None
    frozen_value_prediction_requires_grad: bool
    normalized_target_requires_grad: bool
    d_loss_d_values_present: bool
    d_loss_d_values_shape: tuple[int, ...] | None
    d_loss_d_values_dtype: str | None
    d_loss_d_values_device: str | None
    d_loss_d_values_finite: bool | None
    d_loss_d_values_exact_zero: bool | None
    d_loss_d_values_norm: float | None
    d_loss_d_values_digest: str | None
    source_faithful_loss_evidence_digest: str
    mathematical_zero_effective_proved: bool
    zero_effective_reason: str | None
    classification: str
    schema_version: str = B2R_LOSS_GRAPH_EVIDENCE_V1

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2R2ProbeAuthorityV1:
    base_authority: B2RUpdateAuthorityV1
    probe_id: str
    slice_identity: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    expected_actor_backward_count: int
    expected_critic_backward_count: int
    expected_optimizer_step_count: int
    expected_live_valuenorm_update_count: int
    schema_version: str = B2R2_PROBE_AUTHORITY_V1

    def __post_init__(self) -> None:
        if self.slice_identity != "B2-R2" or type(self.probe_id) is not str or not self.probe_id:
            _fail(
                "probe authority is not bound to B2-R2",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r2_probe_authority",
                expected="B2-R2 and nonempty probe ID",
                observed=(self.slice_identity, self.probe_id),
            )
        if self.allowed_operations != ("backward", "gradient_inspection", "gradient_cleanup"):
            _fail(
                "R2 allowed operation set drifted",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r2_probe_authority",
                observed=self.allowed_operations,
            )
        required_forbidden = {
            "optimizer_step",
            "scheduler_step",
            "live_valuenorm_update",
            "parameter_mutation",
            "optimizer_state_mutation",
            "isaac",
            "training",
            "checkpoint_weight_io",
            "public_route_activation",
        }
        if not required_forbidden.issubset(set(self.forbidden_operations)):
            _fail(
                "R2 forbidden operation set is incomplete",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r2_probe_authority",
                expected=tuple(sorted(required_forbidden)),
                observed=self.forbidden_operations,
            )
        if (
            type(self.expected_actor_backward_count) is not int
            or self.expected_actor_backward_count < 0
            or type(self.expected_critic_backward_count) is not int
            or self.expected_critic_backward_count < 0
            or self.expected_optimizer_step_count != 0
            or self.expected_live_valuenorm_update_count != 0
        ):
            _fail(
                "R2 expected execution counts violate the no-step/no-live-ValueNorm boundary",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="r2_probe_authority",
                observed=(self.expected_actor_backward_count, self.expected_critic_backward_count, self.expected_optimizer_step_count, self.expected_live_valuenorm_update_count),
            )

    @property
    def update_id(self) -> str:
        return self.base_authority.update_id

    @property
    def config_digest(self) -> str:
        return self.base_authority.config_digest

    @property
    def resolved_config(self):
        return self.base_authority.resolved_config

    @property
    def B(self) -> int:
        return self.base_authority.B

    @property
    def authority_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RGradientAuditV1:
    owner_identity: str
    parameters: tuple[B2RGradientParameterEvidenceV1, ...]
    aggregate_norm: float
    finite: bool
    any_nonzero: bool
    all_required_gradients_present: bool
    all_present_gradients_exact_zero: bool
    classification: str
    loss_graph_evidence: B2RLossGraphEvidenceV1 | None
    foreign_gradient_names: tuple[str, ...]
    schema_version: str = B2R_GRADIENT_AUDIT_V1

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RProbeSnapshotV1:
    authority_digest: str
    frozen_inputs_digest: str
    plan_digest: str
    factor_digest: str | None
    actor_component_digests: tuple[tuple[str, str], ...]
    critic_component_digest: str
    live_valuenorm_component_digest: str
    ownership_digest: str
    schema_version: str = B2R_PROBE_SNAPSHOT_V1

    @property
    def snapshot_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RBackwardProbeReceiptV1:
    component_kind: str
    owner_identity: str
    actor_id: int | None
    epoch: int
    minibatch: int
    canonical_partition_indices: tuple[int, ...]
    dvm_evaluation_indices: tuple[int, ...]
    loss_indices: tuple[int, ...]
    behavior_old_logprob_field: str | None
    behavior_old_logprob_digest: str | None
    raw_target_digest: str | None
    permit_id: str | None
    backward_executed: int
    loss_value: float | None
    evaluation_logprob_digest: str | None
    gradient_audit: B2RGradientAuditV1 | None
    aggregate_gradient_norm: float
    projected_clipped_gradient_norm: float
    pre_snapshot_digest: str
    post_snapshot_digest: str
    parameters_unchanged: bool
    optimizers_unchanged: bool
    live_valuenorm_unchanged: bool
    foreign_gradients_absent: bool
    gradients_clean_after: bool
    factor_unchanged: bool
    synthetic_controlled_inputs: bool
    schema_version: str = B2R_BACKWARD_PROBE_RECEIPT_V1

    @property
    def receipt_digest(self) -> str:
        return canonical_digest_v1(self)


class B2RProbeExecutionCounterV1:
    """Mutable test-only execution counter; it owns no learner component."""

    __slots__ = (
        "actor_backward_executed",
        "critic_backward_executed",
        "optimizer_step_attempted",
        "optimizer_step_executed",
        "live_valuenorm_update_attempted",
        "live_valuenorm_update_executed",
    )

    def __init__(self) -> None:
        self.actor_backward_executed = 0
        self.critic_backward_executed = 0
        self.optimizer_step_attempted = 0
        self.optimizer_step_executed = 0
        self.live_valuenorm_update_attempted = 0
        self.live_valuenorm_update_executed = 0

    @property
    def total_backward_executed(self) -> int:
        return self.actor_backward_executed + self.critic_backward_executed


class B2ROptimizerStepTrapV1:
    """A rejecting seam that never delegates to the wrapped optimizer."""

    __slots__ = ("component_kind", "owner_identity", "module", "optimizer", "counter")

    def __init__(
        self,
        *,
        component_kind: str,
        owner_identity: str,
        module: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        counter: B2RProbeExecutionCounterV1,
    ) -> None:
        self.component_kind = component_kind
        self.owner_identity = owner_identity
        self.module = module
        self.optimizer = optimizer
        self.counter = counter

    def step(self) -> None:
        self.counter.optimizer_step_attempted += 1
        _fail(
            "B2-R2 optimizer-step trap rejected the attempted operation before delegation",
            stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP,
            stage="optimizer_step_trap",
            field_name=self.owner_identity,
            expected="optimizer.step executed exactly zero times",
            observed="attempt rejected",
        )


class B2RLiveValueNormTrapV1:
    """A rejecting seam that never delegates to the live ValueNorm object."""

    __slots__ = ("value_normalizer", "counter")

    def __init__(self, *, value_normalizer: object, counter: B2RProbeExecutionCounterV1) -> None:
        self.value_normalizer = value_normalizer
        self.counter = counter

    def update(self, _: torch.Tensor) -> None:
        self.counter.live_valuenorm_update_attempted += 1
        _fail(
            "B2-R2 live ValueNorm trap rejected the attempted update before delegation",
            stop_code=STOP_VALUENORM,
            stage="live_valuenorm_trap",
            expected="live ValueNorm.update executed exactly zero times",
            observed="attempt rejected",
        )


def capture_probe_snapshot_v1(
    *,
    authority: B2R2ProbeAuthorityV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    plan_digest: str,
    factor: torch.Tensor | None,
    actor_bindings: Sequence[tuple[str, torch.nn.Module, torch.optim.Optimizer]],
    critic_binding: tuple[str, torch.nn.Module, torch.optim.Optimizer],
    live_value_normalizer: object,
) -> B2RProbeSnapshotV1:
    """Capture one hard-precondition topology/state snapshot before backward."""

    ownership = validate_parameter_ownership_v1(
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        shared_parameter_mode=False,
    )
    bindings = tuple((owner, module) for owner, module, _ in actor_bindings) + (
        (critic_binding[0], critic_binding[1]),
    )
    validate_gradients_clear_v1(bindings)
    actor_digests: list[tuple[str, str]] = []
    for owner, module, optimizer in actor_bindings:
        _validate_finite_component_state_v1(owner=owner, module=module, optimizer=optimizer)
        fingerprint = fingerprint_component_v1(
            component_kind="actor",
            owner_identity=owner,
            module=module,
            optimizer=optimizer,
        )
        actor_digests.append((owner, fingerprint.fingerprint_digest))
    critic_owner, critic_module, critic_optimizer = critic_binding
    _validate_finite_component_state_v1(
        owner=critic_owner, module=critic_module, optimizer=critic_optimizer
    )
    critic_fingerprint = fingerprint_component_v1(
        component_kind="critic",
        owner_identity=critic_owner,
        module=critic_module,
        optimizer=critic_optimizer,
    )
    _validate_finite_valuenorm_v1(live_value_normalizer)
    valuenorm_fingerprint = fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=live_value_normalizer,
    )
    return B2RProbeSnapshotV1(
        authority_digest=authority.authority_digest,
        frozen_inputs_digest=frozen_inputs.evidence_digest,
        plan_digest=plan_digest,
        factor_digest=None if factor is None else fingerprint_tensor_v1(factor).content_digest,
        actor_component_digests=tuple(actor_digests),
        critic_component_digest=critic_fingerprint.fingerprint_digest,
        live_valuenorm_component_digest=valuenorm_fingerprint.fingerprint_digest,
        ownership_digest=ownership.ownership_digest,
    )


def _assert_snapshot_restored_v1(
    before: B2RProbeSnapshotV1,
    after: B2RProbeSnapshotV1,
) -> None:
    if after != before:
        _fail(
            "post-probe topology/state did not return to exact quiescence",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="post_probe_restoration",
            expected=before.snapshot_digest,
            observed=after.snapshot_digest,
        )


def _grad_fn_name_v1(tensor: torch.Tensor) -> str | None:
    grad_fn = tensor.grad_fn
    return None if grad_fn is None else type(grad_fn).__name__


def classify_loss_graph_v1(
    *,
    value_loss: torch.Tensor,
    current_values: torch.Tensor,
    frozen_value_predictions: torch.Tensor,
    normalized_targets: torch.Tensor,
    source_faithful_loss_evidence_digest: str,
    mathematical_zero_effective_proved: bool,
    zero_effective_reason: str | None,
) -> B2RLossGraphEvidenceV1:
    """Classify dLoss/dValues without mutating learner state."""

    if (
        type(value_loss) is not torch.Tensor
        or value_loss.numel() != 1
        or not bool(torch.isfinite(value_loss.detach()).all().item())
    ):
        _fail(
            "critic value loss is not one finite scalar",
            stop_code=STOP_NONFINITE_LOSS,
            stage="critic_loss_graph",
            expected="one finite scalar",
            observed=(type(value_loss), getattr(value_loss, "shape", None)),
        )
    if type(current_values) is not torch.Tensor or not current_values.requires_grad:
        _fail(
            "current critic values are detached from autograd",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="critic_loss_graph",
            expected=GRAPH_DISCONNECT_OR_UNUSED,
            observed=(type(current_values), getattr(current_values, "requires_grad", None)),
        )
    if not value_loss.requires_grad:
        _fail(
            "critic value loss is detached from autograd",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="critic_loss_graph",
            expected=GRAPH_DISCONNECT_OR_UNUSED,
            observed=False,
        )
    derivative = torch.autograd.grad(
        value_loss,
        current_values,
        retain_graph=True,
        allow_unused=True,
    )[0]
    if derivative is None:
        _fail(
            "critic loss does not use the current value tensor",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="critic_loss_graph",
            expected=GRAPH_DISCONNECT_OR_UNUSED,
            observed=None,
        )
    # autograd may return an expanded stride-zero view (for example d(sum)/dx);
    # canonical byte evidence requires a contiguous physical representation.
    detached = torch.empty(
        tuple(derivative.shape), dtype=derivative.dtype, device=derivative.device
    )
    detached.copy_(derivative.detach())
    if not bool(torch.isfinite(detached).all().item()):
        _fail(
            "dLoss/dValues is nonfinite",
            stop_code=STOP_NONFINITE_GRADIENT,
            stage="critic_loss_graph",
            expected="finite derivative",
            observed="nonfinite",
        )
    exact_zero = not bool(torch.count_nonzero(detached).item())
    norm = float(torch.linalg.vector_norm(detached).item())
    if not math.isfinite(norm):
        _fail(
            "dLoss/dValues norm is nonfinite",
            stop_code=STOP_NONFINITE_GRADIENT,
            stage="critic_loss_graph",
            expected="finite derivative norm",
            observed=norm,
        )
    if exact_zero and (
        not mathematical_zero_effective_proved or not zero_effective_reason
    ):
        _fail(
            "zero dLoss/dValues lacks source-faithful mathematical proof",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="critic_loss_graph",
            expected="explicit installed-loss zero-effective proof",
            observed=(mathematical_zero_effective_proved, zero_effective_reason),
        )
    if not exact_zero and mathematical_zero_effective_proved:
        _fail(
            "zero-effective proof contradicts a nonzero derivative",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="critic_loss_graph",
            expected="proof iff derivative is exact zero",
            observed=norm,
        )
    fingerprint = fingerprint_tensor_v1(detached)
    return B2RLossGraphEvidenceV1(
        current_values_requires_grad=True,
        current_values_grad_fn=_grad_fn_name_v1(current_values),
        value_loss_requires_grad=True,
        value_loss_grad_fn=_grad_fn_name_v1(value_loss),
        frozen_value_prediction_requires_grad=bool(
            frozen_value_predictions.requires_grad
        ),
        normalized_target_requires_grad=bool(normalized_targets.requires_grad),
        d_loss_d_values_present=True,
        d_loss_d_values_shape=fingerprint.shape,
        d_loss_d_values_dtype=fingerprint.dtype,
        d_loss_d_values_device=fingerprint.device,
        d_loss_d_values_finite=True,
        d_loss_d_values_exact_zero=exact_zero,
        d_loss_d_values_norm=norm,
        d_loss_d_values_digest=fingerprint.content_digest,
        source_faithful_loss_evidence_digest=source_faithful_loss_evidence_digest,
        mathematical_zero_effective_proved=mathematical_zero_effective_proved,
        zero_effective_reason=zero_effective_reason,
        classification=(
            VALID_ZERO_EFFECTIVE_UPDATE if exact_zero else VALID_NONZERO_UPDATE
        ),
    )


def _audit_gradients_v1(
    *,
    owner_identity: str,
    target_module: torch.nn.Module,
    foreign_bindings: Sequence[tuple[str, torch.nn.Module]],
    require_nonzero: bool,
    allow_proved_zero_effective: bool = False,
    loss_graph_evidence: B2RLossGraphEvidenceV1 | None = None,
) -> B2RGradientAuditV1:
    foreign = tuple(
        f"{owner}.{name}"
        for owner, module in foreign_bindings
        for name, parameter in module.named_parameters()
        if parameter.grad is not None
    )
    if foreign:
        _fail(
            "target backward produced a foreign-component gradient",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="post_backward_gradient_audit",
            expected="no foreign gradient",
            observed=foreign[:16],
        )
    evidence: list[B2RGradientParameterEvidenceV1] = []
    aggregate_sq = 0.0
    any_nonzero = False
    required_gradient_names: list[str] = []
    missing_required_gradient_names: list[str] = []
    for name, parameter in target_module.named_parameters():
        gradient = parameter.grad
        qualified = f"{owner_identity}.{name}"
        if parameter.requires_grad:
            required_gradient_names.append(qualified)
        if gradient is None:
            evidence.append(
                B2RGradientParameterEvidenceV1(
                    qualified,
                    bool(parameter.requires_grad),
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            if parameter.requires_grad:
                missing_required_gradient_names.append(qualified)
            continue
        finite = bool(torch.isfinite(gradient.detach()).all().item())
        if not finite:
            _fail(
                "owned gradient is nonfinite",
                stop_code=STOP_NONFINITE_GRADIENT,
                stage="post_backward_gradient_audit",
                field_name=qualified,
                expected="finite gradient",
                observed="nonfinite",
            )
        norm = float(torch.linalg.vector_norm(gradient.detach()).item())
        if not math.isfinite(norm):
            _fail(
                "owned gradient norm is nonfinite",
                stop_code=STOP_NONFINITE_GRADIENT,
                stage="post_backward_gradient_audit",
                field_name=qualified,
                expected="finite norm",
                observed=norm,
            )
        nonzero = bool(torch.count_nonzero(gradient.detach()).item())
        any_nonzero = any_nonzero or nonzero
        aggregate_sq += norm * norm
        tensor_fingerprint = fingerprint_tensor_v1(gradient.detach())
        evidence.append(
            B2RGradientParameterEvidenceV1(
                qualified,
                bool(parameter.requires_grad),
                True,
                tensor_fingerprint.shape,
                tensor_fingerprint.dtype,
                tensor_fingerprint.device,
                True,
                tensor_fingerprint.content_digest,
                norm,
                nonzero,
            )
        )
    aggregate = math.sqrt(aggregate_sq)
    if not math.isfinite(aggregate):
        _fail(
            "aggregate gradient norm is nonfinite",
            stop_code=STOP_NONFINITE_GRADIENT,
            stage="post_backward_gradient_audit",
            expected="finite aggregate norm",
            observed=aggregate,
        )
    if require_nonzero and not any_nonzero:
        _fail(
            "nondegenerate probe produced no nonzero owned gradient",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="post_backward_gradient_audit",
            expected="at least one nonzero owned gradient",
            observed=False,
        )
    all_required_present = not missing_required_gradient_names
    all_present_exact_zero = all(
        item.nonzero is False for item in evidence if item.present
    )
    if any_nonzero:
        if (
            loss_graph_evidence is not None
            and loss_graph_evidence.d_loss_d_values_exact_zero is True
        ):
            _fail(
                "owned nonzero gradients contradict exact-zero dLoss/dValues",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="post_backward_gradient_audit",
                expected=OWNERSHIP_OR_FOREIGN_GRADIENT_FAILURE,
                observed=loss_graph_evidence.evidence_digest,
            )
        classification = VALID_NONZERO_UPDATE
    else:
        proof_valid = (
            allow_proved_zero_effective
            and loss_graph_evidence is not None
            and loss_graph_evidence.classification == VALID_ZERO_EFFECTIVE_UPDATE
            and loss_graph_evidence.d_loss_d_values_present
            and loss_graph_evidence.d_loss_d_values_finite is True
            and loss_graph_evidence.d_loss_d_values_exact_zero is True
            and loss_graph_evidence.mathematical_zero_effective_proved
            and bool(loss_graph_evidence.zero_effective_reason)
            and all_required_present
            and bool(required_gradient_names)
            and all_present_exact_zero
        )
        if not proof_valid:
            _fail(
                "zero owned gradients are not a proved valid zero-effective update",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="post_backward_gradient_audit",
                expected=(
                    "connected finite exact-zero dLoss/dValues, source-faithful "
                    "branch proof, and present finite-zero owned gradients"
                ),
                observed={
                    "allow_proved_zero_effective": allow_proved_zero_effective,
                    "missing_required_gradients": tuple(
                        missing_required_gradient_names
                    ),
                    "loss_graph_classification": (
                        None
                        if loss_graph_evidence is None
                        else loss_graph_evidence.classification
                    ),
                },
            )
        classification = VALID_ZERO_EFFECTIVE_UPDATE
    return B2RGradientAuditV1(
        owner_identity=owner_identity,
        parameters=tuple(evidence),
        aggregate_norm=aggregate,
        finite=True,
        any_nonzero=any_nonzero,
        all_required_gradients_present=all_required_present,
        all_present_gradients_exact_zero=all_present_exact_zero,
        classification=classification,
        loss_graph_evidence=loss_graph_evidence,
        foreign_gradient_names=(),
    )


def _execute_backward_v1(
    *,
    loss: torch.Tensor,
    component_kind: str,
    owner_identity: str,
    target_module: torch.nn.Module,
    foreign_bindings: Sequence[tuple[str, torch.nn.Module]],
    counter: B2RProbeExecutionCounterV1,
    require_nonzero: bool,
    allow_proved_zero_effective: bool = False,
    loss_graph_evidence: B2RLossGraphEvidenceV1 | None = None,
) -> B2RGradientAuditV1:
    if type(loss) is not torch.Tensor or loss.numel() != 1 or not bool(torch.isfinite(loss.detach()).all().item()):
        _fail(
            "controlled probe loss is not one finite scalar",
            stop_code=STOP_NONFINITE_LOSS,
            stage="pre_backward_loss",
            expected="one finite scalar",
            observed=(type(loss), getattr(loss, "shape", None)),
        )
    if not loss.requires_grad:
        _fail(
            "controlled probe loss is detached from autograd",
            stop_code=STOP_MUTATION_ATTRIBUTION,
            stage="pre_backward_loss",
            expected=GRAPH_DISCONNECT_OR_UNUSED,
            observed=False,
        )
    loss.backward()
    if component_kind == "actor":
        counter.actor_backward_executed += 1
    elif component_kind == "critic":
        counter.critic_backward_executed += 1
    else:
        _fail(
            "backward component kind is not authorized in B2-R2",
            stop_code=STOP_UNAUTHORIZED_BACKWARD,
            stage="backward_dispatch",
            observed=component_kind,
        )
    return _audit_gradients_v1(
        owner_identity=owner_identity,
        target_module=target_module,
        foreign_bindings=foreign_bindings,
        require_nonzero=require_nonzero,
        allow_proved_zero_effective=allow_proved_zero_effective,
        loss_graph_evidence=loss_graph_evidence,
    )


def _require_stage_v1(
    state_machine: B2RUpdateStateMachineV1,
    expected: B2RUpdateStageV1,
) -> None:
    if state_machine.current is not expected or state_machine.poisoned:
        _fail(
            "R2 backward attempted outside its frozen state-machine stage",
            stop_code=STOP_MODE_ORDER,
            stage=state_machine.current.value,
            expected=expected.value,
            observed=(state_machine.current.value, state_machine.poisoned),
        )


def _consume_backward_permit_v1(
    *,
    ledger: B2RPermitLedgerV1 | None,
    permit: B2RMutationPermitV1 | None,
    authority: B2R2ProbeAuthorityV1,
    component_kind: str,
    owner_identity: str,
    actor_id: int | None,
    stage: B2RUpdateStageV1,
    epoch: int,
    minibatch: int,
    canonical_indices: tuple[int, ...],
    precondition_digest: str,
) -> str:
    if ledger is None or permit is None:
        _fail(
            "real backward requires one issued R1 single-use permit",
            stop_code=STOP_UNAUTHORIZED_BACKWARD,
            stage="backward_permit",
            expected="live backward-only permit",
            observed=None,
        )
    ledger.consume(
        permit_id=permit.permit_id,
        operation=B2RPermitOperationV1.BACKWARD,
        update_id=authority.update_id,
        authority_config_digest=authority.config_digest,
        component_kind=component_kind,
        owner_identity=owner_identity,
        actor_id=actor_id,
        stage=stage,
        epoch=epoch,
        minibatch=minibatch,
        canonical_index_digest=_tensor_indices_digest(canonical_indices),
        precondition_fingerprint_digest=precondition_digest,
    )
    return permit.permit_id


def _validate_actor_tensor_contract_v1(
    *,
    B: int,
    obs: torch.Tensor,
    rnn_states: torch.Tensor,
    actions: torch.Tensor,
    masks: torch.Tensor,
    available_actions: torch.Tensor,
    behavior_old_logprobs: torch.Tensor,
    advantages: torch.Tensor,
    factor: torch.Tensor,
    decision_valid_mask: torch.Tensor,
    active_mask: torch.Tensor,
    resolved_T: int,
    resolved_E: int,
) -> None:
    shapes = {
        "obs": tuple(obs.shape),
        "rnn_states": tuple(rnn_states.shape),
        "actions": tuple(actions.shape),
        "masks": tuple(masks.shape),
        "available_actions": tuple(available_actions.shape),
        "behavior_old_logprobs": tuple(behavior_old_logprobs.shape),
        "advantages": tuple(advantages.shape),
        "factor": tuple(factor.shape),
        "decision_valid_mask": tuple(decision_valid_mask.shape),
        "active_mask": tuple(active_mask.shape),
    }
    valid = (
        obs.ndim == 2 and obs.shape[0] == B
        and rnn_states.ndim == 3 and rnn_states.shape[0] == B
        and tuple(actions.shape) == (B, 1)
        and tuple(masks.shape) == (B, 1)
        and available_actions.ndim == 2 and available_actions.shape[0] == B
        and tuple(behavior_old_logprobs.shape) == (B, 1)
        and tuple(advantages.shape) == (B, 1)
        and tuple(factor.shape) == (resolved_T, resolved_E, 1)
        and tuple(decision_valid_mask.shape) == (B,)
        and tuple(active_mask.shape) == (B,)
        and decision_valid_mask.dtype is torch.bool
        and active_mask.dtype is torch.bool
    )
    if not valid:
        _fail(
            "actor probe tensor shapes do not bind the resolved canonical grid",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=f"B={B}, factor=[{resolved_T},{resolved_E},1]",
            observed=shapes,
        )


def _actor_evaluate_v1(
    *,
    actor: object,
    indices: tuple[int, ...],
    obs: torch.Tensor,
    rnn_states: torch.Tensor,
    actions: torch.Tensor,
    masks: torch.Tensor,
    available_actions: torch.Tensor,
    active_masks: torch.Tensor | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    index = torch.tensor(indices, dtype=torch.long, device=obs.device)
    result = actor.evaluate_actions(
        obs[index],
        rnn_states[index],
        actions[index],
        masks[index],
        available_actions[index],
        active_masks,
    )
    if type(result) is not tuple or len(result) != 3:
        _fail(
            "installed actor evaluate_actions contract drifted",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_real_forward",
            expected="three-item tuple",
            observed=type(result),
        )
    logprobs, entropy, _ = result
    if tuple(logprobs.shape) != (len(indices), 1) or entropy.numel() != 1:
        _fail(
            "installed actor evaluate_actions output shape drifted",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_real_forward",
            expected=((len(indices), 1), "scalar entropy"),
            observed=(tuple(logprobs.shape), tuple(entropy.shape)),
        )
    return logprobs, entropy.reshape(())


def probe_actor_backward_v1(
    *,
    authority: B2R2ProbeAuthorityV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    actor_plan: B2RActorUpdatePlanV1,
    minibatch_plan: B2RActorMinibatchPlanV1,
    actor_id: int,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    state_machine: B2RUpdateStateMachineV1,
    ledger: B2RPermitLedgerV1 | None,
    permit: B2RMutationPermitV1 | None,
    obs: torch.Tensor,
    rnn_states: torch.Tensor,
    actions: torch.Tensor,
    masks: torch.Tensor,
    available_actions: torch.Tensor,
    behavior_old_logprobs: torch.Tensor,
    behavior_old_logprob_digest: str,
    advantages: torch.Tensor,
    factor: torch.Tensor,
    decision_valid_mask: torch.Tensor,
    active_mask: torch.Tensor,
    counter: B2RProbeExecutionCounterV1,
    claimed_partition_indices: Sequence[int] | None = None,
    claimed_evaluation_indices: Sequence[int] | None = None,
    claimed_loss_indices: Sequence[int] | None = None,
    claimed_behavior_field: str = "original_rollout_behavior_logprob",
    attempt_backward_when_empty: bool = False,
    synthetic_fault_loss_term: torch.Tensor | None = None,
) -> B2RBackwardProbeReceiptV1:
    """Execute one real installed-HAPPO actor backward and restore gradients."""

    _require_stage_v1(state_machine, B2RUpdateStageV1.S5_ACTOR_SEQUENCE)
    if actor_plan.update_id != authority.update_id or actor_plan.authority_config_digest != authority.config_digest:
        _fail(
            "actor probe plan is stale relative to update authority",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="actor_probe_binding",
            expected=(authority.update_id, authority.config_digest),
            observed=(actor_plan.update_id, actor_plan.authority_config_digest),
        )
    if actor_id < 0 or actor_id >= len(actors) or minibatch_plan.actor_id != actor_id or minibatch_plan not in actor_plan.minibatches:
        _fail(
            "actor probe owner/minibatch is not in the frozen plan",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=actor_id,
            observed=minibatch_plan.actor_id,
        )
    partition = minibatch_plan.canonical_partition_indices
    evaluation = minibatch_plan.dvm_evaluation_indices
    loss_indices = minibatch_plan.active_and_dvm_loss_indices
    claimed_partition = partition if claimed_partition_indices is None else tuple(claimed_partition_indices)
    claimed_evaluation = evaluation if claimed_evaluation_indices is None else tuple(claimed_evaluation_indices)
    claimed_loss = loss_indices if claimed_loss_indices is None else tuple(claimed_loss_indices)
    if claimed_partition != partition or claimed_evaluation != evaluation:
        _fail(
            "actor probe claimed rows differ from the immutable plan",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=(partition, evaluation),
            observed=(claimed_partition, claimed_evaluation),
        )
    if claimed_loss != loss_indices:
        _fail(
            "actor probe attempted to add a forced/inactive row to loss authority",
            stop_code=STOP_FORCED_ROW_POLICY_LEAK,
            stage="actor_probe_binding",
            expected=loss_indices,
            observed=claimed_loss,
        )
    if claimed_behavior_field != actor_plan.behavior_old_logprob_field:
        _fail(
            "actor behavior-logprob field identity drifted",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=actor_plan.behavior_old_logprob_field,
            observed=claimed_behavior_field,
        )
    if (
        frozen_inputs.update_id != authority.update_id
        or frozen_inputs.authority_config_digest != authority.config_digest
        or frozen_inputs.original_behavior_logprob_digest != behavior_old_logprob_digest
    ):
        _fail(
            "actor probe is not bound to the frozen training-input authority",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=(authority.update_id, authority.config_digest, behavior_old_logprob_digest),
            observed=(frozen_inputs.update_id, frozen_inputs.authority_config_digest, frozen_inputs.original_behavior_logprob_digest),
        )
    B = authority.B
    config = authority.resolved_config
    _validate_actor_tensor_contract_v1(
        B=B,
        obs=obs,
        rnn_states=rnn_states,
        actions=actions,
        masks=masks,
        available_actions=available_actions,
        behavior_old_logprobs=behavior_old_logprobs,
        advantages=advantages,
        factor=factor,
        decision_valid_mask=decision_valid_mask,
        active_mask=active_mask,
        resolved_T=config.resolved_T,
        resolved_E=config.resolved_E,
    )
    partition_set = set(partition)
    actual_evaluation = tuple(index for index in partition if bool(decision_valid_mask[index].item()))
    actual_loss = tuple(index for index in partition if bool((decision_valid_mask[index] & active_mask[index]).item()))
    if actual_evaluation != evaluation:
        _fail(
            "actual DVM rows do not match frozen evaluation indices",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=evaluation,
            observed=actual_evaluation,
        )
    if actual_loss != loss_indices or not set(loss_indices).issubset(partition_set):
        _fail(
            "actual active-and-DVM rows do not match frozen loss indices",
            stop_code=STOP_FORCED_ROW_POLICY_LEAK,
            stage="actor_probe_binding",
            expected=loss_indices,
            observed=actual_loss,
        )
    actual_behavior_digest = fingerprint_tensor_v1(behavior_old_logprobs).content_digest
    if behavior_old_logprob_digest != actual_behavior_digest:
        _fail(
            "actor behavior-logprob evidence digest does not bind the supplied historical tensor",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=behavior_old_logprob_digest,
            observed=actual_behavior_digest,
        )
    factor_digest = fingerprint_tensor_v1(factor).content_digest
    if factor_digest != actor_plan.factor_input_digest:
        _fail(
            "actor factor input is not the frozen plan input",
            stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            stage="actor_probe_binding",
            expected=actor_plan.factor_input_digest,
            observed=factor_digest,
        )
    actor_bindings = tuple(
        (f"actor{index}", item.actor, item.actor_optimizer)
        for index, item in enumerate(actors)
    )
    critic_binding = ("critic", critic.critic, critic.critic_optimizer)
    pre = capture_probe_snapshot_v1(
        authority=authority,
        frozen_inputs=frozen_inputs,
        plan_digest=actor_plan.plan_digest,
        factor=factor,
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        live_value_normalizer=live_value_normalizer,
    )
    target = actors[actor_id]
    target_component_pre = fingerprint_component_v1(
        component_kind="actor",
        owner_identity=f"actor{actor_id}",
        module=target.actor,
        optimizer=target.actor_optimizer,
    )
    modules = tuple(item.actor for item in actors) + (critic.critic,)
    if not loss_indices:
        if attempt_backward_when_empty:
            _fail(
                "forced-only actor has no backward authority",
                stop_code=STOP_UNAUTHORIZED_BACKWARD,
                stage="actor_forced_only",
                expected="zero backward",
                observed="attempted",
            )
        post = capture_probe_snapshot_v1(
            authority=authority,
            frozen_inputs=frozen_inputs,
            plan_digest=actor_plan.plan_digest,
            factor=factor,
            actor_bindings=actor_bindings,
            critic_binding=critic_binding,
            live_value_normalizer=live_value_normalizer,
        )
        _assert_snapshot_restored_v1(pre, post)
        return B2RBackwardProbeReceiptV1(
            component_kind="actor",
            owner_identity=f"actor{actor_id}",
            actor_id=actor_id,
            epoch=minibatch_plan.epoch,
            minibatch=minibatch_plan.minibatch,
            canonical_partition_indices=partition,
            dvm_evaluation_indices=evaluation,
            loss_indices=loss_indices,
            behavior_old_logprob_field=actor_plan.behavior_old_logprob_field,
            behavior_old_logprob_digest=behavior_old_logprob_digest,
            raw_target_digest=None,
            permit_id=None,
            backward_executed=0,
            loss_value=None,
            evaluation_logprob_digest=None,
            gradient_audit=None,
            aggregate_gradient_norm=0.0,
            projected_clipped_gradient_norm=0.0,
            pre_snapshot_digest=pre.snapshot_digest,
            post_snapshot_digest=post.snapshot_digest,
            parameters_unchanged=True,
            optimizers_unchanged=True,
            live_valuenorm_unchanged=True,
            foreign_gradients_absent=True,
            gradients_clean_after=True,
            factor_unchanged=True,
            synthetic_controlled_inputs=True,
        )

    try:
        with torch.no_grad():
            evaluated_logprobs, _ = _actor_evaluate_v1(
                actor=target,
                indices=evaluation,
                obs=obs,
                rnn_states=rnn_states,
                actions=actions,
                masks=masks,
                available_actions=available_actions,
                active_masks=None,
            )
        active_ones = torch.ones((len(loss_indices), 1), dtype=torch.float32, device=obs.device)
        current_logprobs, entropy = _actor_evaluate_v1(
            actor=target,
            indices=loss_indices,
            obs=obs,
            rnn_states=rnn_states,
            actions=actions,
            masks=masks,
            available_actions=available_actions,
            active_masks=active_ones,
        )
        index = torch.tensor(loss_indices, dtype=torch.long, device=obs.device)
        old_logprobs = behavior_old_logprobs[index]
        importance = torch.prod(torch.exp(current_logprobs - old_logprobs), dim=-1, keepdim=True)
        advantage_batch = advantages[index]
        factor_batch = factor.reshape(B, 1)[index]
        surrogate_one = importance * advantage_batch
        surrogate_two = torch.clamp(
            importance,
            1.0 - float(target.clip_param),
            1.0 + float(target.clip_param),
        ) * advantage_batch
        policy_loss = -(factor_batch * torch.minimum(surrogate_one, surrogate_two)).sum() / float(len(loss_indices))
        total_loss = policy_loss - entropy * float(target.entropy_coef)
        if synthetic_fault_loss_term is not None:
            if type(synthetic_fault_loss_term) is not torch.Tensor or synthetic_fault_loss_term.numel() != 1:
                _fail(
                    "synthetic fault term must be one scalar",
                    stop_code=STOP_NONFINITE_LOSS,
                    stage="actor_fault_fixture",
                    observed=type(synthetic_fault_loss_term),
                )
            total_loss = total_loss + synthetic_fault_loss_term.reshape(())
        if not bool(torch.isfinite(total_loss.detach()).all().item()):
            _fail(
                "actor loss is nonfinite before backward",
                stop_code=STOP_NONFINITE_LOSS,
                stage="actor_real_loss",
                expected="finite scalar actor loss",
                observed=float(total_loss.detach().item()),
            )
        permit_id = _consume_backward_permit_v1(
            ledger=ledger,
            permit=permit,
            authority=authority,
            component_kind="actor",
            owner_identity=f"actor{actor_id}",
            actor_id=actor_id,
            stage=B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
            epoch=minibatch_plan.epoch,
            minibatch=minibatch_plan.minibatch,
            canonical_indices=loss_indices,
            precondition_digest=pre.snapshot_digest,
        )
        foreign = tuple(
            (f"actor{index}", item.actor)
            for index, item in enumerate(actors)
            if index != actor_id
        ) + (("critic", critic.critic),)
        audit = _execute_backward_v1(
            loss=total_loss,
            component_kind="actor",
            owner_identity=f"actor{actor_id}",
            target_module=target.actor,
            foreign_bindings=foreign,
            counter=counter,
            require_nonzero=True,
        )
        target_during = fingerprint_component_v1(
            component_kind="actor",
            owner_identity=f"actor{actor_id}",
            module=target.actor,
            optimizer=target.actor_optimizer,
        )
        if _component_state_digest(target_during) != _component_state_digest(target_component_pre):
            _fail(
                "actor parameter/optimizer state changed before cleanup",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="actor_post_backward_state",
            )
        loss_value = float(total_loss.detach().item())
        evaluation_digest = fingerprint_tensor_v1(evaluated_logprobs).content_digest
    except BaseException:
        _clear_gradients_v1(modules)
        post_failure = capture_probe_snapshot_v1(
            authority=authority,
            frozen_inputs=frozen_inputs,
            plan_digest=actor_plan.plan_digest,
            factor=factor,
            actor_bindings=actor_bindings,
            critic_binding=critic_binding,
            live_value_normalizer=live_value_normalizer,
        )
        _assert_snapshot_restored_v1(pre, post_failure)
        raise
    _clear_gradients_v1(modules)
    post = capture_probe_snapshot_v1(
        authority=authority,
        frozen_inputs=frozen_inputs,
        plan_digest=actor_plan.plan_digest,
        factor=factor,
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        live_value_normalizer=live_value_normalizer,
    )
    _assert_snapshot_restored_v1(pre, post)
    projected = min(audit.aggregate_norm, float(target.max_grad_norm))
    return B2RBackwardProbeReceiptV1(
        component_kind="actor",
        owner_identity=f"actor{actor_id}",
        actor_id=actor_id,
        epoch=minibatch_plan.epoch,
        minibatch=minibatch_plan.minibatch,
        canonical_partition_indices=partition,
        dvm_evaluation_indices=evaluation,
        loss_indices=loss_indices,
        behavior_old_logprob_field=actor_plan.behavior_old_logprob_field,
        behavior_old_logprob_digest=behavior_old_logprob_digest,
        raw_target_digest=None,
        permit_id=permit_id,
        backward_executed=1,
        loss_value=loss_value,
        evaluation_logprob_digest=evaluation_digest,
        gradient_audit=audit,
        aggregate_gradient_norm=audit.aggregate_norm,
        projected_clipped_gradient_norm=projected,
        pre_snapshot_digest=pre.snapshot_digest,
        post_snapshot_digest=post.snapshot_digest,
        parameters_unchanged=True,
        optimizers_unchanged=True,
        live_valuenorm_unchanged=True,
        foreign_gradients_absent=True,
        gradients_clean_after=True,
        factor_unchanged=True,
        synthetic_controlled_inputs=True,
    )


def probe_critic_backward_v1(
    *,
    authority: B2R2ProbeAuthorityV1,
    frozen_inputs: B2RFrozenTrainingInputsV1,
    critic_plan: B2RCriticUpdatePlanV1,
    epoch: int,
    minibatch: int,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
    state_machine: B2RUpdateStateMachineV1,
    ledger: B2RPermitLedgerV1 | None,
    permit: B2RMutationPermitV1 | None,
    shared_obs: torch.Tensor,
    rnn_states: torch.Tensor,
    masks: torch.Tensor,
    value_preds: torch.Tensor,
    critic_returns_storage: torch.Tensor,
    counter: B2RProbeExecutionCounterV1,
    claimed_target_digest: str | None = None,
    synthetic_fault_loss_term: torch.Tensor | None = None,
) -> B2RBackwardProbeReceiptV1:
    """Execute one real installed-VCritic backward using disposable ValueNorm."""

    _require_stage_v1(state_machine, B2RUpdateStageV1.S6_CRITIC_SEQUENCE)
    if critic_plan.update_id != authority.update_id or critic_plan.authority_config_digest != authority.config_digest:
        _fail(
            "critic probe plan is stale relative to update authority",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="critic_probe_binding",
            expected=(authority.update_id, authority.config_digest),
            observed=(critic_plan.update_id, critic_plan.authority_config_digest),
        )
    if epoch < 0 or epoch >= critic_plan.critic_epoch_count or minibatch < 0 or minibatch >= critic_plan.critic_minibatch_count:
        _fail(
            "critic probe epoch/minibatch is outside the immutable plan",
            stop_code=STOP_CRITIC_ROW_COVERAGE,
            stage="critic_probe_binding",
            observed=(epoch, minibatch),
        )
    B = critic_plan.B
    config = authority.resolved_config
    if tuple(critic_returns_storage.shape) != (config.resolved_T + 1, config.resolved_E, 1):
        _fail(
            "critic storage does not expose exact [T+1,E,1] returns",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="critic_probe_binding",
            expected=(config.resolved_T + 1, config.resolved_E, 1),
            observed=tuple(critic_returns_storage.shape),
        )
    raw_target = critic_returns_storage[:-1].reshape(B, 1)
    if not bool(torch.isfinite(raw_target).all().item()):
        _fail(
            "critic raw target contains a nonfinite value",
            stop_code=STOP_NONFINITE_TARGET,
            stage="critic_probe_binding",
            expected="finite returns[:-1]",
            observed="nonfinite",
        )
    target_digest = fingerprint_tensor_v1(raw_target).content_digest
    claimed = target_digest if claimed_target_digest is None else claimed_target_digest
    if claimed != critic_plan.raw_target_digest or target_digest != critic_plan.raw_target_digest:
        _fail(
            "critic target digest is not the frozen returns[:-1] identity",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="critic_probe_binding",
            expected=critic_plan.raw_target_digest,
            observed=(claimed, target_digest),
        )
    if (
        frozen_inputs.update_id != authority.update_id
        or frozen_inputs.authority_config_digest != authority.config_digest
        or frozen_inputs.critic_training_slice_digest != target_digest
    ):
        _fail(
            "critic probe is not bound to the frozen returns[:-1] input authority",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="critic_probe_binding",
            expected=(authority.update_id, authority.config_digest, target_digest),
            observed=(frozen_inputs.update_id, frozen_inputs.authority_config_digest, frozen_inputs.critic_training_slice_digest),
        )
    if shared_obs.ndim != 2 or shared_obs.shape[0] != B or tuple(rnn_states.shape[:1]) != (B,) or tuple(masks.shape) != (B, 1) or tuple(value_preds.shape) != (B, 1):
        _fail(
            "critic probe tensors do not bind the canonical physical grid",
            stop_code=STOP_CRITIC_TRAINING_SLICE,
            stage="critic_probe_binding",
            expected=f"leading B={B}",
            observed=(tuple(shared_obs.shape), tuple(rnn_states.shape), tuple(masks.shape), tuple(value_preds.shape)),
        )
    partition = critic_plan.partitions_by_epoch[epoch][minibatch]
    actor_bindings = tuple(
        (f"actor{index}", item.actor, item.actor_optimizer)
        for index, item in enumerate(actors)
    )
    critic_binding = ("critic", critic.critic, critic.critic_optimizer)
    pre = capture_probe_snapshot_v1(
        authority=authority,
        frozen_inputs=frozen_inputs,
        plan_digest=critic_plan.plan_digest,
        factor=None,
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        live_value_normalizer=live_value_normalizer,
    )
    critic_component_pre = fingerprint_component_v1(
        component_kind="critic",
        owner_identity="critic",
        module=critic.critic,
        optimizer=critic.critic_optimizer,
    )
    modules = tuple(item.actor for item in actors) + (critic.critic,)
    try:
        index = torch.tensor(partition, dtype=torch.long, device=shared_obs.device)
        values, _ = critic.get_values(shared_obs[index], rnn_states[index], masks[index])
        if not bool(torch.isfinite(values).all().item()):
            _fail(
                "critic forward output is nonfinite",
                stop_code=STOP_NONFINITE_LOSS,
                stage="critic_real_forward",
                expected="finite values",
                observed="nonfinite",
            )
        disposable_value_normalizer = copy.deepcopy(live_value_normalizer)
        disposable_before = fingerprint_component_v1(
            component_kind="disposable_valuenorm",
            owner_identity="disposable_valuenorm",
            value_normalizer=disposable_value_normalizer,
        )
        value_loss = critic.cal_value_loss(
            values,
            value_preds[index],
            raw_target[index],
            value_normalizer=disposable_value_normalizer,
        )
        disposable_after = fingerprint_component_v1(
            component_kind="disposable_valuenorm",
            owner_identity="disposable_valuenorm",
            value_normalizer=disposable_value_normalizer,
        )
        if disposable_after.fingerprint_digest == disposable_before.fingerprint_digest:
            _fail(
                "disposable ValueNorm did not exercise installed critic loss normalization",
                stop_code=STOP_VALUENORM,
                stage="critic_disposable_valuenorm",
                expected="disposable clone mutation",
                observed="unchanged",
            )
        total_loss = value_loss * float(critic.value_loss_coef)
        if synthetic_fault_loss_term is not None:
            total_loss = total_loss + synthetic_fault_loss_term.reshape(())
        if not bool(torch.isfinite(total_loss.detach()).all().item()):
            _fail(
                "critic loss is nonfinite before backward",
                stop_code=STOP_NONFINITE_LOSS,
                stage="critic_real_loss",
                expected="finite scalar critic loss",
                observed=float(total_loss.detach().item()),
            )
        permit_id = _consume_backward_permit_v1(
            ledger=ledger,
            permit=permit,
            authority=authority,
            component_kind="critic",
            owner_identity="critic",
            actor_id=None,
            stage=B2RUpdateStageV1.S6_CRITIC_SEQUENCE,
            epoch=epoch,
            minibatch=minibatch,
            canonical_indices=partition,
            precondition_digest=pre.snapshot_digest,
        )
        audit = _execute_backward_v1(
            loss=total_loss,
            component_kind="critic",
            owner_identity="critic",
            target_module=critic.critic,
            foreign_bindings=tuple((f"actor{index}", item.actor) for index, item in enumerate(actors)),
            counter=counter,
            require_nonzero=True,
        )
        critic_component_during = fingerprint_component_v1(
            component_kind="critic",
            owner_identity="critic",
            module=critic.critic,
            optimizer=critic.critic_optimizer,
        )
        if _component_state_digest(critic_component_during) != _component_state_digest(critic_component_pre):
            _fail(
                "critic parameter/optimizer state changed before cleanup",
                stop_code=STOP_MUTATION_ATTRIBUTION,
                stage="critic_post_backward_state",
            )
        loss_value = float(total_loss.detach().item())
    except BaseException:
        _clear_gradients_v1(modules)
        post_failure = capture_probe_snapshot_v1(
            authority=authority,
            frozen_inputs=frozen_inputs,
            plan_digest=critic_plan.plan_digest,
            factor=None,
            actor_bindings=actor_bindings,
            critic_binding=critic_binding,
            live_value_normalizer=live_value_normalizer,
        )
        _assert_snapshot_restored_v1(pre, post_failure)
        raise
    _clear_gradients_v1(modules)
    post = capture_probe_snapshot_v1(
        authority=authority,
        frozen_inputs=frozen_inputs,
        plan_digest=critic_plan.plan_digest,
        factor=None,
        actor_bindings=actor_bindings,
        critic_binding=critic_binding,
        live_value_normalizer=live_value_normalizer,
    )
    _assert_snapshot_restored_v1(pre, post)
    projected = min(audit.aggregate_norm, float(critic.max_grad_norm))
    return B2RBackwardProbeReceiptV1(
        component_kind="critic",
        owner_identity="critic",
        actor_id=None,
        epoch=epoch,
        minibatch=minibatch,
        canonical_partition_indices=partition,
        dvm_evaluation_indices=(),
        loss_indices=partition,
        behavior_old_logprob_field=None,
        behavior_old_logprob_digest=None,
        raw_target_digest=target_digest,
        permit_id=permit_id,
        backward_executed=1,
        loss_value=loss_value,
        evaluation_logprob_digest=None,
        gradient_audit=audit,
        aggregate_gradient_norm=audit.aggregate_norm,
        projected_clipped_gradient_norm=projected,
        pre_snapshot_digest=pre.snapshot_digest,
        post_snapshot_digest=post.snapshot_digest,
        parameters_unchanged=True,
        optimizers_unchanged=True,
        live_valuenorm_unchanged=True,
        foreign_gradients_absent=True,
        gradients_clean_after=True,
        factor_unchanged=True,
        synthetic_controlled_inputs=True,
    )


__all__: tuple[str, ...] = ()
