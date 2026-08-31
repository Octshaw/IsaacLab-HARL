"""Decision-valid HAPPO actor math for the lifecycle event profile.

The implementation is deliberately repo-local.  It consumes completed B2-I3a
actor slot storage, evaluates only original policy proposals, and preserves the
full canonical ``(t, env)`` factor index space.  It has no lifecycle, runtime,
critic, GAE, proposal-execution, or public-runner capability.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_HAPPO_POLICY_MATH_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_happo_policy_math"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_HAPPO_POLICY_MATH_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event HAPPO policy math source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_HAPPO_POLICY_MATH_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from types import MappingProxyType

import torch

from .assignment_event_actor_collection import EventPolicyActorSlotStorageV2
from .assignment_profile_contract import AssignmentProfileName


EVENT_POLICY_HAPPO_POLICY_MATH_V2 = "event_policy_happo_policy_math_v2"
EVENT_POLICY_HAPPO_ACTOR_UPDATE_V2 = "event_policy_happo_actor_update_v2"
EVENT_POLICY_HAPPO_SEQUENCE_UPDATE_V2 = "event_policy_happo_sequence_update_v2"
_RESULT_FACTORY_CAPABILITY = object()
_ADVANTAGE_EPSILON = 1.0e-5


class EventPolicyHAPPOMathError(RuntimeError):
    """Fail-closed event-profile actor-math contract error."""

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
            f"actual={actual!r}; schema={EVENT_POLICY_HAPPO_POLICY_MATH_V2!r}"
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
    raise EventPolicyHAPPOMathError(
        message,
        failure_code=failure_code,
        stage=stage,
        field_name=field_name,
        expected=expected,
        actual=actual,
    )


def _readonly_tensor(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


def _readonly_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    copied: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            copied[str(key)] = _readonly_mapping(item)
        elif isinstance(item, torch.Tensor):
            copied[str(key)] = _readonly_tensor(item)
        elif isinstance(item, list):
            copied[str(key)] = tuple(item)
        else:
            copied[str(key)] = item
    return MappingProxyType(copied)


def _tensor_contract(
    value: object,
    *,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    device: torch.device,
    field_name: str,
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
            "tensor violates exact shape/dtype/device contract",
            failure_code="happo_tensor_contract",
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
            "tensor contains a nonfinite value",
            failure_code="nonfinite_happo_tensor",
            stage=stage,
            field_name=field_name,
            expected="all finite",
            actual=value,
        )
    return value


def _canonical_indices(mask: torch.Tensor) -> torch.Tensor:
    """Return row-major k=t*E+e indices for a [T,E,1] bool mask."""

    return mask[..., 0].reshape(-1).nonzero(as_tuple=False).flatten().to(torch.int64)


def _index_tuple(indices: torch.Tensor) -> tuple[int, ...]:
    return tuple(int(item) for item in indices.detach().cpu().tolist())


@dataclass(frozen=True)
class EventPolicyAdvantageNormalizationV2:
    """Finite actor-valid advantage projection and its exact fallback rule."""

    schema_version: str
    valid_count: int
    rule: str
    mean: float | None
    std: float | None
    _normalized_advantages: torch.Tensor
    _factory_capability: object

    def __post_init__(self) -> None:
        if self._factory_capability is not _RESULT_FACTORY_CAPABILITY:
            _fail(
                "advantage normalization records require the canonical factory",
                failure_code="happo_result_factory_required",
                stage="advantage_normalization",
                expected="normalize_event_policy_advantages_v2",
                actual="direct constructor",
            )

    @property
    def normalized_advantages(self) -> torch.Tensor:
        return _readonly_tensor(self._normalized_advantages)


@dataclass(frozen=True)
class EventPolicyHAPPOMinibatchRecordV2:
    """Canonical-index record for one planned feed-forward minibatch."""

    epoch: int
    minibatch: int
    planned_canonical_indices: tuple[int, ...]
    policy_loss_canonical_indices: tuple[int, ...]
    processed: bool


@dataclass(frozen=True)
class EventPolicyHAPPOActorUpdateResultV2:
    """Immutable per-actor update and full-grid sequential-factor evidence."""

    schema_version: str
    agent_id: int
    actor_storage: EventPolicyActorSlotStorageV2
    canonical_evaluation_indices: tuple[int, ...]
    canonical_policy_loss_indices: tuple[int, ...]
    optimizer_steps: int
    processed_minibatches: int
    planned_minibatches: int
    factor_evaluation_performed: bool
    normalization_rule: str
    minibatch_records: tuple[EventPolicyHAPPOMinibatchRecordV2, ...]
    _factor_before: torch.Tensor
    _ratio_full: torch.Tensor
    _factor_after: torch.Tensor
    _pre_update_logprobs: torch.Tensor
    _post_update_logprobs: torch.Tensor
    _train_info: Mapping[str, object]
    _factory_capability: object

    def __post_init__(self) -> None:
        if self._factory_capability is not _RESULT_FACTORY_CAPABILITY:
            _fail(
                "actor update results require the canonical factory",
                failure_code="happo_result_factory_required",
                stage="actor_result",
                expected="train_event_policy_happo_actor_v2",
                actual="direct constructor",
            )

    @property
    def factor_before(self) -> torch.Tensor:
        return _readonly_tensor(self._factor_before)

    @property
    def ratio_full(self) -> torch.Tensor:
        return _readonly_tensor(self._ratio_full)

    @property
    def factor_after(self) -> torch.Tensor:
        return _readonly_tensor(self._factor_after)

    @property
    def pre_update_logprobs(self) -> torch.Tensor:
        return _readonly_tensor(self._pre_update_logprobs)

    @property
    def post_update_logprobs(self) -> torch.Tensor:
        return _readonly_tensor(self._post_update_logprobs)

    @property
    def train_info(self) -> Mapping[str, object]:
        return _readonly_mapping(self._train_info)

    def validate_actor_storage(self, candidate: object) -> None:
        if candidate is not self.actor_storage:
            _fail(
                "actor update result cannot be rebound to replacement storage",
                failure_code="actor_storage_identity_mismatch",
                stage="actor_result_validate",
                expected=id(self.actor_storage),
                actual=id(candidate),
            )


@dataclass(frozen=True)
class EventPolicyHAPPOSequenceUpdateResultV2:
    """Immutable sequential actor order and accumulated full-grid factor."""

    schema_version: str
    agent_order: tuple[int, ...]
    actor_results: tuple[EventPolicyHAPPOActorUpdateResultV2, ...]
    _initial_factor: torch.Tensor
    _final_factor: torch.Tensor
    _factory_capability: object

    def __post_init__(self) -> None:
        if self._factory_capability is not _RESULT_FACTORY_CAPABILITY:
            _fail(
                "sequence results require the canonical factory",
                failure_code="happo_result_factory_required",
                stage="sequence_result",
                expected="train_event_policy_happo_sequence_v2",
                actual="direct constructor",
            )

    @property
    def initial_factor(self) -> torch.Tensor:
        return _readonly_tensor(self._initial_factor)

    @property
    def final_factor(self) -> torch.Tensor:
        return _readonly_tensor(self._final_factor)


@dataclass(frozen=True)
class _ActorRolloutView:
    T: int
    E: int
    O: int
    R: int
    H: int
    device: torch.device
    obs: torch.Tensor
    available_actions: torch.Tensor
    decision_valid_masks: torch.Tensor
    active_masks: torch.Tensor
    actions: torch.Tensor
    old_action_logprobs: torch.Tensor
    rnn_states: torch.Tensor
    masks: torch.Tensor
    advantages: torch.Tensor
    factor_before: torch.Tensor
    evaluation_indices: torch.Tensor
    policy_loss_indices: torch.Tensor


def normalize_event_policy_advantages_v2(
    *,
    advantages: torch.Tensor,
    policy_loss_mask: torch.Tensor,
) -> EventPolicyAdvantageNormalizationV2:
    """Normalize only active-and-DVM advantages with finite small-N guards."""

    if type(advantages) is not torch.Tensor or advantages.ndim != 3 or advantages.shape[-1] != 1:
        _fail(
            "advantages must use exact [T,E,1] layout",
            failure_code="advantage_contract",
            stage="advantage_normalization",
            field_name="advantages",
            expected="float32[T,E,1]",
            actual=(type(advantages), getattr(advantages, "shape", None)),
        )
    _tensor_contract(
        policy_loss_mask,
        shape=tuple(advantages.shape),
        dtype=torch.bool,
        device=advantages.device,
        field_name="policy_loss_mask",
        stage="advantage_normalization",
    )
    if advantages.dtype is not torch.float32:
        _fail(
            "advantages must remain float32",
            failure_code="advantage_contract",
            stage="advantage_normalization",
            field_name="advantages",
            expected=torch.float32,
            actual=advantages.dtype,
        )
    indices = _canonical_indices(policy_loss_mask)
    output = torch.zeros_like(advantages)
    count = int(indices.numel())
    if count == 0:
        return EventPolicyAdvantageNormalizationV2(
            schema_version=EVENT_POLICY_HAPPO_POLICY_MATH_V2,
            valid_count=0,
            rule="zero_valid_skip",
            mean=None,
            std=None,
            _normalized_advantages=output,
            _factory_capability=_RESULT_FACTORY_CAPABILITY,
        )
    flat = advantages.reshape(-1, 1)
    valid = flat[indices]
    if not bool(torch.isfinite(valid).all().item()):
        _fail(
            "actor-valid advantages contain nonfinite values",
            failure_code="nonfinite_actor_advantage",
            stage="advantage_normalization",
            field_name="advantages[active&DVM]",
            expected="all finite",
            actual=valid,
        )
    mean_value: float | None = None
    std_value: float | None = None
    normalized = valid
    rule = "singleton_raw_finite" if count == 1 else "raw_finite_fallback"
    if count > 1:
        mean = valid.mean()
        std = valid.std(unbiased=True)
        mean_value = float(mean.detach().item()) if bool(torch.isfinite(mean).item()) else None
        std_value = float(std.detach().item()) if bool(torch.isfinite(std).item()) else None
        if bool(torch.isfinite(mean).item()) and bool(torch.isfinite(std).item()) and float(std.item()) > 0.0:
            candidate = (valid - mean) / (std + _ADVANTAGE_EPSILON)
            if bool(torch.isfinite(candidate).all().item()):
                normalized = candidate
                rule = "stock_unbiased_std_plus_1e-5"
            else:
                rule = "nonfinite_normalization_raw_finite_fallback"
        elif bool(torch.isfinite(std).item()) and float(std.item()) == 0.0:
            rule = "zero_variance_raw_finite"
        else:
            rule = "nonfinite_stats_raw_finite_fallback"
    output_flat = output.reshape(-1, 1)
    output_flat[indices] = normalized
    if not bool(torch.isfinite(output_flat[indices]).all().item()):
        _fail(
            "advantage normalization failed to produce finite actor values",
            failure_code="nonfinite_normalized_advantage",
            stage="advantage_normalization",
            expected="finite actor-valid advantages",
            actual=output_flat[indices],
        )
    return EventPolicyAdvantageNormalizationV2(
        schema_version=EVENT_POLICY_HAPPO_POLICY_MATH_V2,
        valid_count=count,
        rule=rule,
        mean=mean_value,
        std=std_value,
        _normalized_advantages=output,
        _factory_capability=_RESULT_FACTORY_CAPABILITY,
    )


def _validate_actor(actor: object) -> None:
    stage = "actor_contract"
    required = (
        "actor",
        "actor_optimizer",
        "evaluate_actions",
        "ppo_epoch",
        "actor_num_mini_batch",
        "clip_param",
        "entropy_coef",
        "use_max_grad_norm",
        "max_grad_norm",
        "use_policy_active_masks",
        "use_recurrent_policy",
        "use_naive_recurrent_policy",
        "action_aggregation",
    )
    missing = tuple(name for name in required if not hasattr(actor, name))
    if missing:
        _fail(
            "actor lacks the installed HAPPO component contract",
            failure_code="happo_actor_contract",
            stage=stage,
            expected=required,
            actual=missing,
        )
    if not callable(actor.evaluate_actions) or not isinstance(actor.actor, torch.nn.Module):
        _fail(
            "actor evaluation/model boundary is invalid",
            failure_code="happo_actor_contract",
            stage=stage,
            expected="callable evaluate_actions and torch.nn.Module actor",
            actual=type(actor),
        )
    if bool(actor.use_recurrent_policy) or bool(actor.use_naive_recurrent_policy):
        _fail(
            "B2-I3b is frozen to feed-forward HAPPO",
            failure_code="recurrent_policy_forbidden",
            stage=stage,
            expected="both recurrent flags false",
            actual=(actor.use_recurrent_policy, actor.use_naive_recurrent_policy),
        )
    if actor.action_aggregation != "prod":
        _fail(
            "B2-I3b requires the frozen HAPPO action aggregation",
            failure_code="action_aggregation_contract",
            stage=stage,
            expected="prod",
            actual=actor.action_aggregation,
        )
    if not bool(actor.use_policy_active_masks):
        _fail(
            "event HAPPO requires the frozen policy-active-mask configuration",
            failure_code="active_mask_configuration",
            stage=stage,
            expected=True,
            actual=actor.use_policy_active_masks,
        )
    if type(actor.ppo_epoch) is not int or actor.ppo_epoch <= 0:
        _fail(
            "ppo_epoch must be a positive int",
            failure_code="happo_actor_contract",
            stage=stage,
            field_name="ppo_epoch",
            expected="positive int",
            actual=actor.ppo_epoch,
        )
    if type(actor.actor_num_mini_batch) is not int or actor.actor_num_mini_batch <= 0:
        _fail(
            "actor_num_mini_batch must be a positive int",
            failure_code="happo_actor_contract",
            stage=stage,
            field_name="actor_num_mini_batch",
            expected="positive int",
            actual=actor.actor_num_mini_batch,
        )
    for name in ("clip_param", "entropy_coef", "max_grad_norm"):
        value = float(getattr(actor, name))
        if not math.isfinite(value) or value < 0.0:
            _fail(
                "HAPPO scalar configuration must be finite and nonnegative",
                failure_code="happo_actor_contract",
                stage=stage,
                field_name=name,
                expected="finite nonnegative scalar",
                actual=value,
            )


def _build_rollout_view(
    *,
    actor_storage: EventPolicyActorSlotStorageV2,
    rnn_states: torch.Tensor,
    masks: torch.Tensor,
    advantages: torch.Tensor,
    factor_before: torch.Tensor,
) -> _ActorRolloutView:
    if type(actor_storage) is not EventPolicyActorSlotStorageV2:
        _fail(
            "I3b requires exact completed I3a actor slot storage",
            failure_code="actor_storage_contract",
            stage="rollout_view",
            expected=EventPolicyActorSlotStorageV2,
            actual=type(actor_storage),
        )
    T, E, O = actor_storage.episode_length, actor_storage.E, actor_storage.obs_dim
    device = actor_storage.device
    if actor_storage.next_action_slot != T:
        _fail(
            "actor slot storage rollout is incomplete",
            failure_code="actor_storage_incomplete",
            stage="rollout_view",
            expected=T,
            actual=actor_storage.next_action_slot,
        )
    obs = _tensor_contract(
        actor_storage.obs,
        shape=(T + 1, E, O),
        dtype=torch.float32,
        device=device,
        field_name="storage.obs",
        stage="rollout_view",
        finite=True,
    )
    available = _tensor_contract(
        actor_storage.available_actions,
        shape=(T + 1, E, actor_storage.N + 1),
        dtype=torch.float32,
        device=device,
        field_name="storage.available_actions",
        stage="rollout_view",
        finite=True,
    )
    dvm = _tensor_contract(
        actor_storage.decision_valid_masks,
        shape=(T + 1, E, 1),
        dtype=torch.bool,
        device=device,
        field_name="storage.decision_valid_masks",
        stage="rollout_view",
    )
    active = _tensor_contract(
        actor_storage.active_masks,
        shape=(T + 1, E, 1),
        dtype=torch.float32,
        device=device,
        field_name="storage.active_masks",
        stage="rollout_view",
        finite=True,
    )
    if not bool(((active == 0.0) | (active == 1.0)).all().item()):
        _fail(
            "HARL active masks must remain binary and separate from DVM",
            failure_code="active_mask_contract",
            stage="rollout_view",
            expected="values in {0,1}",
            actual=active,
        )
    actions = _tensor_contract(
        actor_storage.action_ids,
        shape=(T, E, 1),
        dtype=torch.int64,
        device=device,
        field_name="storage.action_ids",
        stage="rollout_view",
    )
    old_logprobs = _tensor_contract(
        actor_storage.action_logprobs,
        shape=(T, E, 1),
        dtype=torch.float32,
        device=device,
        field_name="storage.action_logprobs",
        stage="rollout_view",
    )
    if type(rnn_states) is not torch.Tensor or rnn_states.ndim != 4:
        _fail(
            "feed-forward HARL placeholders require [T+1,E,R,H] RNN layout",
            failure_code="happo_tensor_contract",
            stage="rollout_view",
            field_name="rnn_states",
            expected="float32[T+1,E,R,H]",
            actual=(type(rnn_states), getattr(rnn_states, "shape", None)),
        )
    R, H = int(rnn_states.shape[2]), int(rnn_states.shape[3])
    rnn = _tensor_contract(
        rnn_states,
        shape=(T + 1, E, R, H),
        dtype=torch.float32,
        device=device,
        field_name="rnn_states",
        stage="rollout_view",
        finite=True,
    )
    sequence_masks = _tensor_contract(
        masks,
        shape=(T + 1, E, 1),
        dtype=torch.float32,
        device=device,
        field_name="masks",
        stage="rollout_view",
        finite=True,
    )
    advantage_tensor = _tensor_contract(
        advantages,
        shape=(T, E, 1),
        dtype=torch.float32,
        device=device,
        field_name="advantages",
        stage="rollout_view",
    )
    factor = _tensor_contract(
        factor_before,
        shape=(T, E, 1),
        dtype=torch.float32,
        device=device,
        field_name="factor_before",
        stage="rollout_view",
        finite=True,
    )
    dvm_t = dvm[:-1]
    loss_mask = dvm_t & active[:-1].to(torch.bool)
    evaluation_indices = _canonical_indices(dvm_t)
    loss_indices = _canonical_indices(loss_mask)
    if int(evaluation_indices.numel()) > 0:
        flat_actions = actions.reshape(-1, 1)
        selected = available[:-1].reshape(-1, actor_storage.N + 1)[evaluation_indices].gather(
            1, flat_actions[evaluation_indices]
        )
        if not bool(selected.to(torch.bool).all().item()):
            _fail(
                "stored original action is illegal under its historical mask",
                failure_code="historical_action_mask_mismatch",
                stage="rollout_view",
                expected="available_actions[t, original_action] == true",
                actual=flat_actions[evaluation_indices],
            )
        if not bool(torch.isfinite(old_logprobs.reshape(-1, 1)[evaluation_indices]).all().item()):
            _fail(
                "stored policy behavior logprob is nonfinite",
                failure_code="nonfinite_behavior_logprob",
                stage="rollout_view",
                expected="finite on DVM rows",
                actual=old_logprobs.reshape(-1, 1)[evaluation_indices],
            )
    return _ActorRolloutView(
        T=T,
        E=E,
        O=O,
        R=R,
        H=H,
        device=device,
        obs=obs,
        available_actions=available,
        decision_valid_masks=dvm,
        active_masks=active,
        actions=actions,
        old_action_logprobs=old_logprobs,
        rnn_states=rnn,
        masks=sequence_masks,
        advantages=advantage_tensor,
        factor_before=factor,
        evaluation_indices=evaluation_indices,
        policy_loss_indices=loss_indices,
    )


def _validate_permutations(
    *,
    full_count: int,
    ppo_epoch: int,
    permutations: Sequence[torch.Tensor] | None,
    device: torch.device,
) -> tuple[torch.Tensor, ...]:
    if permutations is None:
        return tuple(torch.randperm(full_count, device=device) for _ in range(ppo_epoch))
    if type(permutations) not in (tuple, list) or len(permutations) != ppo_epoch:
        _fail(
            "minibatch permutations require one full canonical permutation per epoch",
            failure_code="minibatch_permutation_contract",
            stage="minibatch_plan",
            expected=f"tuple/list length {ppo_epoch}",
            actual=(type(permutations), len(permutations) if isinstance(permutations, Sequence) else None),
        )
    expected = torch.arange(full_count, dtype=torch.int64, device=device)
    validated = []
    for epoch, permutation in enumerate(permutations):
        _tensor_contract(
            permutation,
            shape=(full_count,),
            dtype=torch.int64,
            device=device,
            field_name=f"minibatch_permutations[{epoch}]",
            stage="minibatch_plan",
        )
        if not torch.equal(permutation.sort().values, expected):
            _fail(
                "minibatch order is not an exact permutation of canonical Omega",
                failure_code="minibatch_permutation_contract",
                stage="minibatch_plan",
                field_name=f"minibatch_permutations[{epoch}]",
                expected=_index_tuple(expected),
                actual=_index_tuple(permutation),
            )
        validated.append(permutation.clone().contiguous())
    return tuple(validated)


def _evaluate(
    *,
    actor: object,
    view: _ActorRolloutView,
    indices: torch.Tensor,
    active_masks: torch.Tensor | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    K = int(indices.numel())
    obs = view.obs[:-1].reshape(-1, view.O)[indices]
    rnn = view.rnn_states[:-1].reshape(-1, view.R, view.H)[indices]
    actions = view.actions.reshape(-1, 1)[indices]
    masks = view.masks[:-1].reshape(-1, 1)[indices]
    available = view.available_actions[:-1].reshape(-1, view.available_actions.shape[-1])[indices]
    result = actor.evaluate_actions(obs, rnn, actions, masks, available, active_masks)
    if type(result) is not tuple or len(result) != 3:
        _fail(
            "evaluate_actions must return the installed three-item tuple",
            failure_code="evaluate_actions_contract",
            stage="actor_evaluate",
            expected="(logprobs, entropy, distribution)",
            actual=type(result),
        )
    logprobs, entropy, _ = result
    _tensor_contract(
        logprobs,
        shape=(K, 1),
        dtype=torch.float32,
        device=view.device,
        field_name="evaluate_actions.logprobs",
        stage="actor_evaluate",
        finite=True,
    )
    if type(entropy) is not torch.Tensor or entropy.numel() != 1 or entropy.device != view.device or not bool(torch.isfinite(entropy).all().item()):
        _fail(
            "evaluate_actions entropy must be one finite device scalar",
            failure_code="evaluate_actions_contract",
            stage="actor_evaluate",
            field_name="entropy",
            expected=("one finite value", view.device),
            actual=(type(entropy), getattr(entropy, "shape", None), getattr(entropy, "device", None)),
        )
    return logprobs, entropy.reshape(())


def _grad_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            value = float(parameter.grad.detach().norm().item())
            total += value * value
    return math.sqrt(total)


def train_event_policy_happo_actor_v2(
    *,
    actor: object,
    actor_storage: EventPolicyActorSlotStorageV2,
    rnn_states: torch.Tensor,
    masks: torch.Tensor,
    advantages: torch.Tensor,
    factor_before: torch.Tensor,
    minibatch_permutations: Sequence[torch.Tensor] | None = None,
) -> EventPolicyHAPPOActorUpdateResultV2:
    """Run bounded feed-forward HAPPO math on actor-valid canonical rows only."""

    _validate_actor(actor)
    view = _build_rollout_view(
        actor_storage=actor_storage,
        rnn_states=rnn_states,
        masks=masks,
        advantages=advantages,
        factor_before=factor_before,
    )
    full_count = view.T * view.E
    if actor.actor_num_mini_batch > full_count or full_count % actor.actor_num_mini_batch != 0:
        _fail(
            "feed-forward full rollout must partition without dropping canonical indices",
            failure_code="minibatch_partition_contract",
            stage="minibatch_plan",
            expected=f"{full_count} divisible by {actor.actor_num_mini_batch}",
            actual=(full_count, actor.actor_num_mini_batch),
        )
    permutations = _validate_permutations(
        full_count=full_count,
        ppo_epoch=actor.ppo_epoch,
        permutations=minibatch_permutations,
        device=view.device,
    )
    normalization = normalize_event_policy_advantages_v2(
        advantages=view.advantages,
        policy_loss_mask=view.decision_valid_masks[:-1] & view.active_masks[:-1].to(torch.bool),
    )
    factor_before_copy = view.factor_before.detach().clone().contiguous()
    ratio_full = torch.ones_like(factor_before_copy)
    empty_logprobs = torch.empty((0, 1), dtype=torch.float32, device=view.device)
    evaluation_tuple = _index_tuple(view.evaluation_indices)
    loss_tuple = _index_tuple(view.policy_loss_indices)
    planned_minibatches = actor.ppo_epoch * actor.actor_num_mini_batch
    if int(view.policy_loss_indices.numel()) == 0:
        return EventPolicyHAPPOActorUpdateResultV2(
            schema_version=EVENT_POLICY_HAPPO_ACTOR_UPDATE_V2,
            agent_id=actor_storage.agent_id,
            actor_storage=actor_storage,
            canonical_evaluation_indices=evaluation_tuple,
            canonical_policy_loss_indices=loss_tuple,
            optimizer_steps=0,
            processed_minibatches=0,
            planned_minibatches=planned_minibatches,
            factor_evaluation_performed=False,
            normalization_rule=normalization.rule,
            minibatch_records=tuple(),
            _factor_before=factor_before_copy,
            _ratio_full=ratio_full,
            _factor_after=factor_before_copy.clone(),
            _pre_update_logprobs=empty_logprobs,
            _post_update_logprobs=empty_logprobs,
            _train_info=MappingProxyType(
                {
                    "policy_loss": 0.0,
                    "dist_entropy": 0.0,
                    "actor_grad_norm": 0.0,
                    "ratio": 0.0,
                    "processed_updates": 0,
                    "planned_minibatches": planned_minibatches,
                    "evaluation_count": len(evaluation_tuple),
                    "policy_loss_count": 0,
                    "zero_valid_actor_skip": True,
                    "active_masks_replaced_by_dvm": False,
                }
            ),
            _factory_capability=_RESULT_FACTORY_CAPABILITY,
        )

    with torch.inference_mode():
        pre_logprobs, _ = _evaluate(
            actor=actor,
            view=view,
            indices=view.evaluation_indices,
            active_masks=None,
        )
        pre_logprobs = pre_logprobs.detach().clone().contiguous()

    normalized_flat = normalization.normalized_advantages.reshape(-1, 1)
    factor_flat = factor_before_copy.reshape(-1, 1)
    old_logprob_flat = view.old_action_logprobs.reshape(-1, 1)
    actor_valid_flat = (
        view.decision_valid_masks[:-1] & view.active_masks[:-1].to(torch.bool)
    )[..., 0].reshape(-1)
    mini_batch_size = full_count // actor.actor_num_mini_batch
    records: list[EventPolicyHAPPOMinibatchRecordV2] = []
    sums = {"policy_loss": 0.0, "dist_entropy": 0.0, "actor_grad_norm": 0.0, "ratio": 0.0}
    processed = 0
    parameters = tuple(actor.actor.parameters())
    for epoch, permutation in enumerate(permutations):
        for minibatch in range(actor.actor_num_mini_batch):
            planned = permutation[minibatch * mini_batch_size : (minibatch + 1) * mini_batch_size]
            selected = planned[actor_valid_flat[planned]]
            if int(selected.numel()) == 0:
                records.append(
                    EventPolicyHAPPOMinibatchRecordV2(
                        epoch=epoch,
                        minibatch=minibatch,
                        planned_canonical_indices=_index_tuple(planned),
                        policy_loss_canonical_indices=tuple(),
                        processed=False,
                    )
                )
                continue
            active_ones = torch.ones((int(selected.numel()), 1), dtype=torch.float32, device=view.device)
            current_logprobs, entropy = _evaluate(
                actor=actor,
                view=view,
                indices=selected,
                active_masks=active_ones,
            )
            old_logprobs = old_logprob_flat[selected]
            importance = torch.prod(
                torch.exp(current_logprobs - old_logprobs), dim=-1, keepdim=True
            )
            advantage_batch = normalized_flat[selected]
            factor_batch = factor_flat[selected]
            surrogate_one = importance * advantage_batch
            surrogate_two = torch.clamp(
                importance,
                1.0 - float(actor.clip_param),
                1.0 + float(actor.clip_param),
            ) * advantage_batch
            policy_loss = -(
                factor_batch * torch.minimum(surrogate_one, surrogate_two)
            ).sum() / float(selected.numel())
            total_loss = policy_loss - entropy * float(actor.entropy_coef)
            if not bool(torch.isfinite(total_loss).item()):
                _fail(
                    "actor loss became nonfinite before backward",
                    failure_code="nonfinite_actor_loss",
                    stage="actor_update",
                    expected="finite policy loss and entropy",
                    actual=(policy_loss, entropy),
                )
            actor.actor_optimizer.zero_grad()
            total_loss.backward()
            if any(
                parameter.grad is not None and not bool(torch.isfinite(parameter.grad).all().item())
                for parameter in parameters
            ):
                _fail(
                    "actor gradients became nonfinite",
                    failure_code="nonfinite_actor_gradient",
                    stage="actor_update",
                    expected="all finite gradients",
                    actual="nonfinite gradient",
                )
            if bool(actor.use_max_grad_norm):
                grad_norm_value = torch.nn.utils.clip_grad_norm_(
                    parameters, float(actor.max_grad_norm)
                )
                grad_norm = float(grad_norm_value.detach().item())
            else:
                grad_norm = _grad_norm(parameters)
            if not math.isfinite(grad_norm):
                _fail(
                    "actor gradient norm is nonfinite",
                    failure_code="nonfinite_actor_gradient",
                    stage="actor_update",
                    field_name="actor_grad_norm",
                    expected="finite",
                    actual=grad_norm,
                )
            actor.actor_optimizer.step()
            if any(not bool(torch.isfinite(parameter).all().item()) for parameter in parameters):
                _fail(
                    "actor parameters became nonfinite after optimizer step",
                    failure_code="nonfinite_actor_parameter",
                    stage="actor_update",
                    expected="all finite actor parameters",
                    actual="nonfinite parameter",
                )
            processed += 1
            sums["policy_loss"] += float(policy_loss.detach().item())
            sums["dist_entropy"] += float(entropy.detach().item())
            sums["actor_grad_norm"] += grad_norm
            sums["ratio"] += float(importance.detach().mean().item())
            records.append(
                EventPolicyHAPPOMinibatchRecordV2(
                    epoch=epoch,
                    minibatch=minibatch,
                    planned_canonical_indices=_index_tuple(planned),
                    policy_loss_canonical_indices=_index_tuple(selected),
                    processed=True,
                )
            )
    if processed == 0:
        _fail(
            "nonempty actor-valid population produced no optimizer minibatch",
            failure_code="empty_processed_update_set",
            stage="actor_update",
            expected="at least one processed minibatch",
            actual=0,
        )

    with torch.inference_mode():
        post_logprobs, _ = _evaluate(
            actor=actor,
            view=view,
            indices=view.evaluation_indices,
            active_masks=None,
        )
        post_logprobs = post_logprobs.detach().clone().contiguous()
        raw_ratio = torch.prod(
            torch.exp(post_logprobs - pre_logprobs), dim=-1, keepdim=True
        )
    if not bool(torch.isfinite(raw_ratio).all().item()):
        _fail(
            "pre/post HAPPO factor ratio is nonfinite",
            failure_code="nonfinite_factor_ratio",
            stage="factor_scatter",
            expected="finite positive ratios",
            actual=raw_ratio,
        )
    ratio_flat = ratio_full.reshape(-1, 1)
    ratio_flat[view.evaluation_indices] = raw_ratio
    factor_after = factor_before_copy * ratio_full
    if not bool(torch.isfinite(factor_after).all().item()):
        _fail(
            "full-grid sequential factor became nonfinite",
            failure_code="nonfinite_full_factor",
            stage="factor_scatter",
            expected="finite [T,E,1] factor",
            actual=factor_after,
        )
    train_info = {
        key: value / processed for key, value in sums.items()
    }
    train_info.update(
        {
            "processed_updates": processed,
            "planned_minibatches": planned_minibatches,
            "evaluation_count": len(evaluation_tuple),
            "policy_loss_count": len(loss_tuple),
            "zero_valid_actor_skip": False,
            "active_masks_replaced_by_dvm": False,
            "forced_rows_evaluated": False,
            "normalization_rule": normalization.rule,
        }
    )
    return EventPolicyHAPPOActorUpdateResultV2(
        schema_version=EVENT_POLICY_HAPPO_ACTOR_UPDATE_V2,
        agent_id=actor_storage.agent_id,
        actor_storage=actor_storage,
        canonical_evaluation_indices=evaluation_tuple,
        canonical_policy_loss_indices=loss_tuple,
        optimizer_steps=processed,
        processed_minibatches=processed,
        planned_minibatches=planned_minibatches,
        factor_evaluation_performed=True,
        normalization_rule=normalization.rule,
        minibatch_records=tuple(records),
        _factor_before=factor_before_copy,
        _ratio_full=ratio_full,
        _factor_after=factor_after,
        _pre_update_logprobs=pre_logprobs,
        _post_update_logprobs=post_logprobs,
        _train_info=MappingProxyType(train_info),
        _factory_capability=_RESULT_FACTORY_CAPABILITY,
    )


def train_event_policy_happo_sequence_v2(
    *,
    actors: Sequence[object],
    actor_storages: Sequence[EventPolicyActorSlotStorageV2],
    rnn_states_by_agent: Sequence[torch.Tensor],
    masks_by_agent: Sequence[torch.Tensor],
    advantages: torch.Tensor,
    initial_factor: torch.Tensor,
    agent_order: Sequence[int],
    minibatch_permutations_by_agent: Mapping[int, Sequence[torch.Tensor]] | None = None,
) -> EventPolicyHAPPOSequenceUpdateResultV2:
    """Update actors sequentially while retaining one full canonical factor."""

    if type(actors) not in (tuple, list) or type(actor_storages) not in (tuple, list):
        _fail(
            "sequence update requires fixed ordered actor and storage sequences",
            failure_code="happo_sequence_contract",
            stage="sequence_validate",
            expected="tuple/list actors and storages",
            actual=(type(actors), type(actor_storages)),
        )
    M = len(actors)
    if M == 0 or len(actor_storages) != M or len(rnn_states_by_agent) != M or len(masks_by_agent) != M:
        _fail(
            "sequence domains disagree on fixed agent cardinality",
            failure_code="happo_sequence_contract",
            stage="sequence_validate",
            expected=(M, M, M, M),
            actual=(M, len(actor_storages), len(rnn_states_by_agent), len(masks_by_agent)),
        )
    order = tuple(agent_order)
    if len(order) != M or tuple(sorted(order)) != tuple(range(M)):
        _fail(
            "agent order must be an exact permutation of fixed actor IDs",
            failure_code="happo_sequence_contract",
            stage="sequence_validate",
            field_name="agent_order",
            expected=tuple(range(M)),
            actual=order,
        )
    if any(type(storage) is not EventPolicyActorSlotStorageV2 or storage.agent_id != index for index, storage in enumerate(actor_storages)):
        _fail(
            "actor storages are not in canonical agent-ID order",
            failure_code="happo_sequence_contract",
            stage="sequence_validate",
            expected="storage[i].agent_id == i",
            actual=tuple(getattr(storage, "agent_id", None) for storage in actor_storages),
        )
    current_factor = initial_factor.detach().clone().contiguous()
    initial_copy = current_factor.clone()
    results = []
    for agent_id in order:
        permutations = None
        if minibatch_permutations_by_agent is not None:
            permutations = minibatch_permutations_by_agent.get(agent_id)
        result = train_event_policy_happo_actor_v2(
            actor=actors[agent_id],
            actor_storage=actor_storages[agent_id],
            rnn_states=rnn_states_by_agent[agent_id],
            masks=masks_by_agent[agent_id],
            advantages=advantages.clone(),
            factor_before=current_factor,
            minibatch_permutations=permutations,
        )
        current_factor = result.factor_after
        results.append(result)
    return EventPolicyHAPPOSequenceUpdateResultV2(
        schema_version=EVENT_POLICY_HAPPO_SEQUENCE_UPDATE_V2,
        agent_order=order,
        actor_results=tuple(results),
        _initial_factor=initial_copy,
        _final_factor=current_factor,
        _factory_capability=_RESULT_FACTORY_CAPABILITY,
    )


def get_event_policy_happo_math_descriptor_v2() -> Mapping[str, object]:
    """Describe I3b math without opening a runner or readiness gate."""

    return _readonly_mapping(
        {
            "schema_version": EVENT_POLICY_HAPPO_POLICY_MATH_V2,
            "profile_name": AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value,
            "policy_evaluation_population": "decision_valid_masks[:-1]",
            "policy_loss_population": "active_masks[:-1] AND decision_valid_masks[:-1]",
            "canonical_index": "k=t*E+env in full [T,E,1] Omega",
            "forced_ratio_source": "ones initialization; never fake logprob evaluation",
            "original_action_source": "I3a actor_storage.action_ids on DVM rows",
            "historical_mask_source": "I3a actor_storage.available_actions[:-1]",
            "stock_happo_retained": (
                "actor network/distribution/evaluate_actions/optimizer/clip/entropy coefficient/"
                "max-grad-norm/feed-forward full-grid minibatch permutation"
            ),
            "event_specialization": (
                "DVM subset evaluation; active&DVM loss; finite normalization; empty skip; "
                "canonical full-grid factor scatter"
            ),
            "installed_harl_modified": False,
            "critic_gae_or_terminal_math": False,
            "proposal_execution_or_runtime_step": False,
            "public_runner_integration": False,
            "readiness_change_authorized": False,
        }
    )


__all__ = (
    "CANONICAL_ASSIGNMENT_EVENT_HAPPO_POLICY_MATH_MODULE",
    "EVENT_POLICY_HAPPO_ACTOR_UPDATE_V2",
    "EVENT_POLICY_HAPPO_POLICY_MATH_V2",
    "EVENT_POLICY_HAPPO_SEQUENCE_UPDATE_V2",
    "EventPolicyAdvantageNormalizationV2",
    "EventPolicyHAPPOActorUpdateResultV2",
    "EventPolicyHAPPOMathError",
    "EventPolicyHAPPOMinibatchRecordV2",
    "EventPolicyHAPPOSequenceUpdateResultV2",
    "get_event_policy_happo_math_descriptor_v2",
    "normalize_event_policy_advantages_v2",
    "train_event_policy_happo_actor_v2",
    "train_event_policy_happo_sequence_v2",
)
