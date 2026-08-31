"""B2-I5b event-profile GAE and return arithmetic.

This module consumes only fixed EP critic-buffer tensors.  It deliberately has
no terminal DTO, runtime, actor/DVM, critic-forward, optimizer, or runner
capability.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_GAE_RETURNS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_gae_returns"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_GAE_RETURNS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event GAE returns must execute under "
        f"its canonical module key; expected={CANONICAL_ASSIGNMENT_EVENT_GAE_RETURNS_MODULE!r}; "
        f"actual={__name__!r}"
    )


from dataclasses import dataclass, field
import math

import torch
from harl.common.valuenorm import ValueNorm

from .assignment_lifecycle_transition_contract import TerminationReason


EVENT_GAE_RETURNS_V2 = "event_gae_returns_v2"


class EventGAEReturnsError(RuntimeError):
    """Fail-closed event return validation or arithmetic error."""

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
            f"expected={expected!r}; actual={actual!r}"
        )


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    expected: object = None,
    actual: object = None,
) -> None:
    raise EventGAEReturnsError(
        message,
        failure_code=failure_code,
        stage=stage,
        expected=expected,
        actual=actual,
    )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventGAEReturnComputationV2:
    """Detached result and audit tensors for one completed fixed EP rollout."""

    schema_version: str
    returns: torch.Tensor = field(repr=False)
    advantages: torch.Tensor = field(repr=False)
    deltas: torch.Tensor = field(repr=False)
    bootstrap_values: torch.Tensor = field(repr=False)
    trace_continue_masks: torch.Tensor = field(repr=False)
    arithmetic_value_preds: torch.Tensor = field(repr=False)


def _validate_float_tensor(
    value: object,
    *,
    name: str,
    shape: tuple[int, ...],
    device: torch.device,
    require_finite: bool = True,
) -> torch.Tensor:
    if (
        type(value) is not torch.Tensor
        or tuple(value.shape) != shape
        or value.dtype is not torch.float32
        or value.device != device
        or value.requires_grad
    ):
        _fail(
            f"{name} violates the fixed float32 tensor contract",
            failure_code=f"{name}_contract",
            stage="event_gae_validate",
            expected=(shape, torch.float32, device, False),
            actual=(
                getattr(value, "shape", None),
                getattr(value, "dtype", None),
                getattr(value, "device", None),
                getattr(value, "requires_grad", None),
            ),
        )
    if require_finite and not bool(torch.isfinite(value).all().item()):
        _fail(
            f"{name} must be finite",
            failure_code=f"{name}_nonfinite",
            stage="event_gae_validate",
            expected="finite",
            actual=value,
        )
    return value


def _normalizer_snapshot(
    value_normalizer: ValueNorm,
) -> tuple[bool, tuple[tuple[str, torch.Tensor], ...]]:
    state = value_normalizer.state_dict()
    return (
        bool(value_normalizer.training),
        tuple((name, tensor.detach().clone()) for name, tensor in state.items()),
    )


def _normalizer_snapshot_equal(
    value_normalizer: ValueNorm,
    before: tuple[bool, tuple[tuple[str, torch.Tensor], ...]],
) -> bool:
    before_training, before_state = before
    after_state = value_normalizer.state_dict()
    if bool(value_normalizer.training) != before_training:
        return False
    if tuple(after_state) != tuple(name for name, _ in before_state):
        return False
    return all(
        current.shape == saved.shape
        and current.dtype == saved.dtype
        and current.device == saved.device
        and torch.equal(current.detach(), saved)
        for name, saved in before_state
        for current in (after_state[name],)
    )


def _denormalize_one_snapshot(
    *,
    native_values: torch.Tensor,
    timeout_values: torch.Tensor,
    timeout_masks: torch.Tensor,
    value_normalizer: ValueNorm | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    selected_timeout = timeout_values[timeout_masks].reshape(-1, 1)
    if selected_timeout.numel() and not bool(torch.isfinite(selected_timeout).all().item()):
        _fail(
            "TIME_LIMIT bootstrap values must be finite before return arithmetic",
            failure_code="timeout_value_nonfinite",
            stage="event_gae_validate",
            expected="finite at timeout mask",
            actual=selected_timeout,
        )

    if value_normalizer is None:
        arithmetic_timeout = torch.zeros_like(timeout_values)
        arithmetic_timeout[timeout_masks] = selected_timeout.reshape(-1)
        return native_values.detach().clone(), arithmetic_timeout

    if not isinstance(value_normalizer, ValueNorm):
        _fail(
            "event ValueNorm arithmetic requires the canonical installed ValueNorm API",
            failure_code="value_normalizer_type",
            stage="event_gae_valuenorm",
            expected=ValueNorm,
            actual=type(value_normalizer),
        )
    normalizer_device = value_normalizer.running_mean.device
    if normalizer_device != native_values.device:
        _fail(
            "ValueNorm and critic-native values must use one device",
            failure_code="value_normalizer_device",
            stage="event_gae_valuenorm",
            expected=native_values.device,
            actual=normalizer_device,
        )

    native_flat = native_values.reshape(-1, 1)
    joined = torch.cat((native_flat, selected_timeout), dim=0)
    before = _normalizer_snapshot(value_normalizer)
    with torch.inference_mode():
        arithmetic_joined = value_normalizer.denormalize(joined)
    if not _normalizer_snapshot_equal(value_normalizer, before):
        _fail(
            "ValueNorm state changed during one event return computation",
            failure_code="value_normalizer_mutated",
            stage="event_gae_valuenorm",
            expected="one stable current normalizer snapshot",
            actual="state or mode changed",
        )
    if (
        type(arithmetic_joined) is not torch.Tensor
        or tuple(arithmetic_joined.shape) != tuple(joined.shape)
        or arithmetic_joined.dtype is not torch.float32
        or arithmetic_joined.device != native_values.device
        or arithmetic_joined.requires_grad
        or not bool(torch.isfinite(arithmetic_joined).all().item())
    ):
        _fail(
            "ValueNorm denormalization returned invalid arithmetic values",
            failure_code="value_denormalize_contract",
            stage="event_gae_valuenorm",
            expected=(joined.shape, torch.float32, native_values.device, False, "finite"),
            actual=(
                getattr(arithmetic_joined, "shape", None),
                getattr(arithmetic_joined, "dtype", None),
                getattr(arithmetic_joined, "device", None),
                getattr(arithmetic_joined, "requires_grad", None),
            ),
        )

    native_count = native_flat.shape[0]
    arithmetic_values = arithmetic_joined[:native_count].reshape_as(native_values).clone()
    arithmetic_timeout = torch.zeros_like(timeout_values)
    arithmetic_timeout[timeout_masks] = arithmetic_joined[native_count:].reshape(-1)
    return arithmetic_values, arithmetic_timeout


def compute_event_gae_returns_v2(
    *,
    rewards: torch.Tensor,
    value_preds: torch.Tensor,
    next_value: torch.Tensor,
    masks: torch.Tensor,
    termination_reason: torch.Tensor,
    timeout_bootstrap_masks: torch.Tensor,
    timeout_bootstrap_value_preds: torch.Tensor,
    gamma: float,
    gae_lambda: float,
    value_normalizer: ValueNorm | None = None,
) -> EventGAEReturnComputationV2:
    """Compute event GAE with independent bootstrap and trace semantics.

    ``value_preds`` and timeout values are critic-native outputs.  When
    ValueNorm is present, one stable current normalizer denormalizes all values
    before any delta, GAE, or return arithmetic.
    """

    if type(rewards) is not torch.Tensor or rewards.ndim != 3 or rewards.shape[-1] != 1:
        _fail(
            "rewards must establish one fixed [T,E,1] rollout",
            failure_code="rewards_contract",
            stage="event_gae_validate",
            expected="[T,E,1] float32",
            actual=(getattr(rewards, "shape", None), getattr(rewards, "dtype", None)),
        )
    T, E = int(rewards.shape[0]), int(rewards.shape[1])
    if T <= 0 or E <= 0:
        _fail(
            "event GAE requires nonempty fixed T and E dimensions",
            failure_code="rollout_shape",
            stage="event_gae_validate",
            expected="T>0 and E>0",
            actual=(T, E),
        )
    device = rewards.device
    _validate_float_tensor(rewards, name="rewards", shape=(T, E, 1), device=device)
    _validate_float_tensor(
        value_preds, name="value_preds", shape=(T + 1, E, 1), device=device
    )
    _validate_float_tensor(next_value, name="next_value", shape=(E, 1), device=device)
    _validate_float_tensor(masks, name="masks", shape=(T + 1, E, 1), device=device)
    if not bool(((masks == 0.0) | (masks == 1.0)).all().item()):
        _fail(
            "EP liveness masks must be binary",
            failure_code="masks_binary",
            stage="event_gae_validate",
            expected=(0.0, 1.0),
            actual=masks,
        )

    expected_transition_shape = (T, E, 1)
    if (
        type(termination_reason) is not torch.Tensor
        or tuple(termination_reason.shape) != expected_transition_shape
        or termination_reason.dtype is not torch.int64
        or termination_reason.device != device
        or termination_reason.requires_grad
    ):
        _fail(
            "termination_reason violates the authoritative [T,E,1] contract",
            failure_code="termination_reason_contract",
            stage="event_gae_validate",
            expected=(expected_transition_shape, torch.int64, device, False),
            actual=(
                getattr(termination_reason, "shape", None),
                getattr(termination_reason, "dtype", None),
                getattr(termination_reason, "device", None),
            ),
        )
    valid_reason_values = torch.tensor(
        [int(reason) for reason in TerminationReason], dtype=torch.int64, device=device
    )
    if not bool(
        (termination_reason.unsqueeze(-1) == valid_reason_values).any(dim=-1).all().item()
    ):
        _fail(
            "termination_reason contains an unknown authoritative enum",
            failure_code="termination_reason_value",
            stage="event_gae_validate",
            expected=tuple(int(reason) for reason in TerminationReason),
            actual=termination_reason,
        )
    if (
        type(timeout_bootstrap_masks) is not torch.Tensor
        or tuple(timeout_bootstrap_masks.shape) != expected_transition_shape
        or timeout_bootstrap_masks.dtype is not torch.bool
        or timeout_bootstrap_masks.device != device
        or timeout_bootstrap_masks.requires_grad
    ):
        _fail(
            "timeout bootstrap masks violate the [T,E,1] bool contract",
            failure_code="timeout_mask_contract",
            stage="event_gae_validate",
            expected=(expected_transition_shape, torch.bool, device, False),
            actual=(
                getattr(timeout_bootstrap_masks, "shape", None),
                getattr(timeout_bootstrap_masks, "dtype", None),
                getattr(timeout_bootstrap_masks, "device", None),
            ),
        )
    _validate_float_tensor(
        timeout_bootstrap_value_preds,
        name="timeout_bootstrap_value_preds",
        shape=expected_transition_shape,
        device=device,
        require_finite=False,
    )
    expected_timeout_masks = termination_reason == int(TerminationReason.TIME_LIMIT)
    if not torch.equal(timeout_bootstrap_masks, expected_timeout_masks):
        _fail(
            "timeout mask must be exactly equivalent to authoritative TIME_LIMIT reason",
            failure_code="termination_timeout_mask_mismatch",
            stage="event_gae_validate",
            expected=expected_timeout_masks,
            actual=timeout_bootstrap_masks,
        )
    terminal_rows = termination_reason != int(TerminationReason.NONE)
    if bool((masks[1:][terminal_rows] != 0.0).any().item()):
        _fail(
            "authoritative terminal transitions require a stopped EP boundary mask",
            failure_code="terminal_liveness_mask",
            stage="event_gae_validate",
            expected=0.0,
            actual=masks[1:][terminal_rows],
        )
    for name, value in (("gamma", gamma), ("gae_lambda", gae_lambda)):
        if type(value) not in (float, int) or isinstance(value, bool) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
            _fail(
                f"{name} must be a finite probability-scale scalar",
                failure_code=f"{name}_value",
                stage="event_gae_validate",
                expected="finite scalar in [0,1]",
                actual=value,
            )

    native_values = value_preds.detach().clone()
    native_values[-1].copy_(next_value)
    arithmetic_values, arithmetic_timeout = _denormalize_one_snapshot(
        native_values=native_values,
        timeout_values=timeout_bootstrap_value_preds,
        timeout_masks=timeout_bootstrap_masks,
        value_normalizer=value_normalizer,
    )

    none_rows = termination_reason == int(TerminationReason.NONE)
    true_terminal_rows = (
        (termination_reason == int(TerminationReason.ALL_TASKS_COMPLETED))
        | (termination_reason == int(TerminationReason.NO_FEASIBLE_TASKS_REMAIN))
    )
    if not bool((none_rows | true_terminal_rows | timeout_bootstrap_masks).all().item()):
        _fail(
            "authoritative reason routing was not exhaustive",
            failure_code="termination_reason_routing",
            stage="event_gae_route",
            expected="NONE, either true terminal, or TIME_LIMIT",
            actual=termination_reason,
        )

    liveness = masks[1:]
    bootstrap_values = torch.zeros_like(rewards)
    bootstrap_values[none_rows] = (
        arithmetic_values[1:][none_rows] * liveness[none_rows]
    )
    bootstrap_values[timeout_bootstrap_masks] = arithmetic_timeout[timeout_bootstrap_masks]
    trace_continue_masks = torch.zeros_like(rewards)
    trace_continue_masks[none_rows] = liveness[none_rows]

    deltas = rewards + float(gamma) * bootstrap_values - arithmetic_values[:-1]
    advantages = torch.zeros_like(rewards)
    gae = torch.zeros((E, 1), dtype=torch.float32, device=device)
    for step in reversed(range(T)):
        gae = (
            deltas[step]
            + float(gamma)
            * float(gae_lambda)
            * trace_continue_masks[step]
            * gae
        )
        advantages[step].copy_(gae)
    returns = advantages + arithmetic_values[:-1]

    for name, value in (
        ("bootstrap_values", bootstrap_values),
        ("trace_continue_masks", trace_continue_masks),
        ("deltas", deltas),
        ("advantages", advantages),
        ("returns", returns),
    ):
        if not bool(torch.isfinite(value).all().item()):
            _fail(
                f"{name} became nonfinite during event GAE",
                failure_code=f"{name}_nonfinite",
                stage="event_gae_arithmetic",
                expected="finite",
                actual=value,
            )

    result = object.__new__(EventGAEReturnComputationV2)
    object.__setattr__(result, "schema_version", EVENT_GAE_RETURNS_V2)
    object.__setattr__(result, "returns", returns.detach().clone().contiguous())
    object.__setattr__(result, "advantages", advantages.detach().clone().contiguous())
    object.__setattr__(result, "deltas", deltas.detach().clone().contiguous())
    object.__setattr__(
        result, "bootstrap_values", bootstrap_values.detach().clone().contiguous()
    )
    object.__setattr__(
        result,
        "trace_continue_masks",
        trace_continue_masks.detach().clone().contiguous(),
    )
    object.__setattr__(
        result,
        "arithmetic_value_preds",
        arithmetic_values.detach().clone().contiguous(),
    )
    return result


__all__: tuple[str, ...] = ()
