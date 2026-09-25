"""Pure B2-R1 actor, critic, and full-index factor planning contracts."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_PLANS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_plans"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_PLANS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R1 training plan source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_PLANS_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re

import torch

from .assignment_event_training_evidence import (
    B2RContractError,
    B2RResolvedConfigV1,
    B2RUpdateAuthorityV1,
    STOP_AUTHORITY_DRIFT,
    canonical_digest_v1,
    fingerprint_tensor_v1,
)


B2R_ACTOR_UPDATE_PLAN_V1 = "b2r_actor_update_plan_v1"
B2R_CRITIC_UPDATE_PLAN_V1 = "b2r_critic_update_plan_v1"
B2R_FACTOR_TRANSITION_EVIDENCE_V1 = "b2r_factor_transition_evidence_v1"

STOP_AGENT_ORDER = "STOP — B2-R AGENT_ORDER"
STOP_FACTOR = "STOP — B2-R FACTOR"
STOP_FORCED_ROW_POLICY_LEAK = "STOP — B2-R FORCED_ROW_POLICY_LEAK"
STOP_CRITIC_ROW_COVERAGE = "STOP — B2-R CRITIC_ROW_COVERAGE"
STOP_UNEXPECTED_STEP_COUNT = "STOP — B2-R UNEXPECTED_STEP_COUNT"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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


def canonical_index_v1(*, t: int, env_id: int, resolved_E: int) -> int:
    if (
        type(t) is not int
        or type(env_id) is not int
        or type(resolved_E) is not int
        or t < 0
        or env_id < 0
        or resolved_E <= 0
        or env_id >= resolved_E
    ):
        _fail(
            "canonical index inputs violate k=t*resolved_E+env_id",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="canonical_index",
            expected="nonnegative t and env_id in [0,resolved_E)",
            observed=(t, env_id, resolved_E),
        )
    return t * resolved_E + env_id


def _validate_index_tuple(
    values: Sequence[int],
    *,
    B: int,
    field_name: str,
    stop_code: str,
) -> tuple[int, ...]:
    result = tuple(values)
    if any(type(item) is not int or item < 0 or item >= B for item in result):
        _fail(
            "canonical index is outside the resolved [0,B) domain",
            stop_code=stop_code,
            stage="plan_indices",
            field_name=field_name,
            expected=f"integer indices in [0,{B})",
            observed=result,
        )
    if len(result) != len(set(result)):
        _fail(
            "canonical index sequence contains a duplicate",
            stop_code=stop_code,
            stage="plan_indices",
            field_name=field_name,
            expected="unique canonical indices",
            observed=result,
        )
    return result


def _validate_epoch_partitions(
    partitions_by_epoch: Sequence[Sequence[Sequence[int]]],
    *,
    epoch_count: int,
    minibatch_count: int,
    B: int,
    stop_code: str,
    require_full_coverage: bool,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    epochs = tuple(tuple(tuple(batch) for batch in epoch) for epoch in partitions_by_epoch)
    if len(epochs) != epoch_count:
        _fail(
            "approved partition epoch count does not match resolved config",
            stop_code=stop_code,
            stage="plan_partitions",
            expected=epoch_count,
            observed=len(epochs),
        )
    validated: list[tuple[tuple[int, ...], ...]] = []
    for epoch_index, epoch in enumerate(epochs):
        if len(epoch) != minibatch_count:
            _fail(
                "approved minibatch count does not match resolved config",
                stop_code=stop_code,
                stage="plan_partitions",
                field_name=f"epoch[{epoch_index}]",
                expected=minibatch_count,
                observed=len(epoch),
            )
        checked_batches: list[tuple[int, ...]] = []
        flat: list[int] = []
        for batch_index, batch in enumerate(epoch):
            if not batch:
                _fail(
                    "approved canonical partition cannot be zero-sized",
                    stop_code=stop_code,
                    stage="plan_partitions",
                    field_name=f"epoch[{epoch_index}].minibatch[{batch_index}]",
                    expected="nonempty partition",
                    observed=batch,
                )
            checked = _validate_index_tuple(
                batch,
                B=B,
                field_name=f"epoch[{epoch_index}].minibatch[{batch_index}]",
                stop_code=stop_code,
            )
            checked_batches.append(checked)
            flat.extend(checked)
        if len(flat) != len(set(flat)):
            _fail(
                "canonical row appears in more than one approved minibatch",
                stop_code=stop_code,
                stage="plan_partitions",
                field_name=f"epoch[{epoch_index}]",
                expected="at most once per epoch",
                observed=tuple(flat),
            )
        if require_full_coverage and set(flat) != set(range(B)):
            missing = tuple(sorted(set(range(B)) - set(flat)))
            extras = tuple(sorted(set(flat) - set(range(B))))
            _fail(
                "approved epoch partition is not exact full canonical coverage",
                stop_code=stop_code,
                stage="plan_partitions",
                field_name=f"epoch[{epoch_index}]",
                expected=f"every k in [0,{B}) exactly once",
                observed={"missing": missing[:16], "unexpected": extras[:16]},
            )
        validated.append(tuple(checked_batches))
    return tuple(validated)


def build_exact_partitions_v1(
    *,
    B: int,
    epoch_count: int,
    minibatch_count: int,
    partition_policy: str,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Build deterministic canonical partitions without floor-remainder loss."""

    if any(type(value) is not int or value <= 0 for value in (B, epoch_count, minibatch_count)):
        _fail(
            "partition dimensions must be positive exact integers",
            stop_code=STOP_CRITIC_ROW_COVERAGE,
            stage="partition_builder",
            expected="positive B/epoch/minibatch counts",
            observed=(B, epoch_count, minibatch_count),
        )
    if minibatch_count > B:
        _fail(
            "minibatch count would create a zero-sized partition",
            stop_code=STOP_CRITIC_ROW_COVERAGE,
            stage="partition_builder",
            expected=f"minibatch_count <= {B}",
            observed=minibatch_count,
        )
    if partition_policy == "exact_divisible":
        if B % minibatch_count != 0:
            _fail(
                "exact-divisible partition would omit a stock-style remainder",
                stop_code=STOP_CRITIC_ROW_COVERAGE,
                stage="partition_builder",
                expected="B divisible by minibatch_count",
                observed=(B, minibatch_count, B % minibatch_count),
            )
        sizes = (B // minibatch_count,) * minibatch_count
    elif partition_policy == "reviewed_exact_coverage":
        base, remainder = divmod(B, minibatch_count)
        sizes = tuple(base + (1 if index < remainder else 0) for index in range(minibatch_count))
    else:
        _fail(
            "partition policy is not an approved exact-coverage policy",
            stop_code=STOP_CRITIC_ROW_COVERAGE,
            stage="partition_builder",
            expected=("exact_divisible", "reviewed_exact_coverage"),
            observed=partition_policy,
        )
    batches: list[tuple[int, ...]] = []
    cursor = 0
    for size in sizes:
        batches.append(tuple(range(cursor, cursor + size)))
        cursor += size
    epoch = tuple(batches)
    return tuple(epoch for _ in range(epoch_count))


@dataclass(frozen=True, slots=True)
class B2RActorMinibatchPlanV1:
    actor_id: int
    epoch: int
    minibatch: int
    canonical_partition_indices: tuple[int, ...]
    dvm_evaluation_indices: tuple[int, ...]
    active_and_dvm_loss_indices: tuple[int, ...]
    empty_loss: bool

    def __post_init__(self) -> None:
        for field_name, values in (
            ("canonical_partition_indices", self.canonical_partition_indices),
            ("dvm_evaluation_indices", self.dvm_evaluation_indices),
            ("active_and_dvm_loss_indices", self.active_and_dvm_loss_indices),
        ):
            if (
                any(type(item) is not int or item < 0 for item in values)
                or len(values) != len(set(values))
            ):
                _fail(
                    "actor minibatch indices must be unique nonnegative canonical rows",
                    stop_code=STOP_FORCED_ROW_POLICY_LEAK,
                    stage="actor_plan_schema",
                    field_name=field_name,
                    observed=values,
                )
        partition = set(self.canonical_partition_indices)
        evaluation = set(self.dvm_evaluation_indices)
        loss = set(self.active_and_dvm_loss_indices)
        if not evaluation.issubset(partition) or not loss.issubset(evaluation):
            _fail(
                "actor selected rows are not bound to partition/DVM authority",
                stop_code=STOP_FORCED_ROW_POLICY_LEAK,
                stage="actor_plan_schema",
                expected="loss subset of DVM evaluation subset of partition",
                observed={
                    "partition": self.canonical_partition_indices,
                    "evaluation": self.dvm_evaluation_indices,
                    "loss": self.active_and_dvm_loss_indices,
                },
            )
        if self.empty_loss is not (len(self.active_and_dvm_loss_indices) == 0):
            _fail(
                "actor minibatch empty/nonempty classification is inconsistent",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="actor_plan_schema",
                expected=len(self.active_and_dvm_loss_indices) == 0,
                observed=self.empty_loss,
            )


@dataclass(frozen=True, slots=True)
class B2RActorUpdatePlanV1:
    update_id: str
    authority_config_digest: str
    resolved_T: int
    resolved_E: int
    resolved_M: int
    actor_epoch_count: int
    actor_minibatch_count: int
    actor_permutation: tuple[int, ...]
    minibatches: tuple[B2RActorMinibatchPlanV1, ...]
    behavior_old_logprob_field: str
    factor_pre_logprob_field: str
    factor_post_logprob_field: str
    expected_backward_count_by_actor: tuple[tuple[int, int], ...]
    expected_optimizer_step_count_by_actor: tuple[tuple[int, int], ...]
    factor_input_digest: str
    optimizer_step_policy: str
    schema_version: str = B2R_ACTOR_UPDATE_PLAN_V1

    def __post_init__(self) -> None:
        if type(self.update_id) is not str or not self.update_id or _SHA256_PATTERN.fullmatch(self.authority_config_digest) is None:
            _fail(
                "actor plan update/config authority identity is malformed",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="actor_plan_schema",
                observed=(self.update_id, self.authority_config_digest),
            )
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.resolved_T,
                self.resolved_E,
                self.resolved_M,
                self.actor_epoch_count,
                self.actor_minibatch_count,
            )
        ):
            _fail(
                "actor plan resolved dimensions/counts must be positive",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="actor_plan_schema",
                observed=(self.resolved_T, self.resolved_E, self.resolved_M, self.actor_epoch_count, self.actor_minibatch_count),
            )
        B = self.resolved_T * self.resolved_E
        expected_actors = tuple(range(self.resolved_M))
        if self.actor_permutation != tuple(dict.fromkeys(self.actor_permutation)) or set(self.actor_permutation) != set(expected_actors):
            _fail(
                "actor plan schema does not contain one exact actor permutation",
                stop_code=STOP_AGENT_ORDER,
                stage="actor_plan_schema",
                expected=expected_actors,
                observed=self.actor_permutation,
            )
        expected_keys = {
            (actor_id, epoch, minibatch)
            for actor_id in expected_actors
            for epoch in range(self.actor_epoch_count)
            for minibatch in range(self.actor_minibatch_count)
        }
        expected_order = tuple(
            (actor_id, epoch, minibatch)
            for actor_id in self.actor_permutation
            for epoch in range(self.actor_epoch_count)
            for minibatch in range(self.actor_minibatch_count)
        )
        observed_order = tuple(
            (item.actor_id, item.epoch, item.minibatch) for item in self.minibatches
        )
        if set(observed_order) != expected_keys or observed_order != expected_order:
            _fail(
                "actor plan schema is missing, duplicating, or reordering a planned minibatch",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="actor_plan_schema",
                expected=expected_order,
                observed=observed_order,
            )
        backward = {actor_id: 0 for actor_id in expected_actors}
        for item in self.minibatches:
            _validate_index_tuple(
                item.canonical_partition_indices,
                B=B,
                field_name="actor_plan.partition",
                stop_code=STOP_AGENT_ORDER,
            )
            if not item.empty_loss:
                backward[item.actor_id] += 1
        for actor_id in expected_actors:
            for epoch in range(self.actor_epoch_count):
                rows = tuple(
                    row
                    for item in self.minibatches
                    if item.actor_id == actor_id and item.epoch == epoch
                    for row in item.canonical_partition_indices
                )
                if len(rows) != B or set(rows) != set(range(B)):
                    _fail(
                        "actor plan does not cover every canonical partition row exactly once per actor/epoch",
                        stop_code=STOP_AGENT_ORDER,
                        stage="actor_plan_schema",
                        expected=f"every k in [0,{B}) exactly once",
                        observed=(actor_id, epoch, rows),
                    )
        expected_backward = tuple(sorted(backward.items()))
        expected_steps = tuple(
            (actor_id, count if self.optimizer_step_policy == "match_backward" else 0)
            for actor_id, count in expected_backward
        )
        if self.optimizer_step_policy not in ("match_backward", "disabled"):
            _fail(
                "actor optimizer policy is not frozen",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="actor_plan_schema",
                observed=self.optimizer_step_policy,
            )
        if self.expected_backward_count_by_actor != expected_backward or self.expected_optimizer_step_count_by_actor != expected_steps:
            _fail(
                "actor expected mutation counts do not match the immutable plan",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="actor_plan_schema",
                expected=(expected_backward, expected_steps),
                observed=(self.expected_backward_count_by_actor, self.expected_optimizer_step_count_by_actor),
            )
        if (
            self.behavior_old_logprob_field != "original_rollout_behavior_logprob"
            or self.factor_pre_logprob_field != "factor_pre_logprob"
            or self.factor_post_logprob_field != "factor_post_logprob"
        ):
            _fail(
                "actor plan behavior/factor evidence fields drifted",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="actor_plan_schema",
                observed=(self.behavior_old_logprob_field, self.factor_pre_logprob_field, self.factor_post_logprob_field),
            )
        if _SHA256_PATTERN.fullmatch(self.factor_input_digest) is None:
            _fail(
                "actor factor input digest is malformed",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="actor_plan_schema",
                observed=self.factor_input_digest,
            )

    @property
    def plan_digest(self) -> str:
        return canonical_digest_v1(self)


def build_actor_update_plan_v1(
    *,
    authority: B2RUpdateAuthorityV1,
    authority_config_digest: str,
    actor_permutation: Sequence[int],
    approved_partitions_by_epoch: Sequence[Sequence[Sequence[int]]],
    dvm_indices_by_actor: Mapping[int, Sequence[int]],
    active_indices_by_actor: Mapping[int, Sequence[int]],
    factor_input_digest: str,
    optimizer_step_policy: str = "match_backward",
) -> B2RActorUpdatePlanV1:
    config = authority.resolved_config
    if authority_config_digest != authority.config_digest:
        _fail(
            "actor plan is bound to a stale/wrong configuration",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="actor_plan",
            expected=authority.config_digest,
            observed=authority_config_digest,
        )
    permutation = tuple(actor_permutation)
    expected_actors = tuple(range(config.resolved_M))
    if len(permutation) != config.resolved_M or set(permutation) != set(expected_actors):
        _fail(
            "actor order must be one exact permutation of all resolved actors",
            stop_code=STOP_AGENT_ORDER,
            stage="actor_plan",
            expected=expected_actors,
            observed=permutation,
        )
    if set(dvm_indices_by_actor) != set(expected_actors) or set(active_indices_by_actor) != set(expected_actors):
        _fail(
            "actor mask bindings are missing or contain an unexpected actor",
            stop_code=STOP_AGENT_ORDER,
            stage="actor_plan",
            expected=expected_actors,
            observed=(tuple(dvm_indices_by_actor), tuple(active_indices_by_actor)),
        )
    if optimizer_step_policy not in ("match_backward", "disabled"):
        _fail(
            "actor optimizer step policy is not representable",
            stop_code=STOP_UNEXPECTED_STEP_COUNT,
            stage="actor_plan",
            expected=("match_backward", "disabled"),
            observed=optimizer_step_policy,
        )
    partitions = _validate_epoch_partitions(
        approved_partitions_by_epoch,
        epoch_count=config.actor_epoch_count,
        minibatch_count=config.actor_minibatch_count,
        B=config.B,
        stop_code=STOP_AGENT_ORDER,
        require_full_coverage=True,
    )
    dvm: dict[int, set[int]] = {}
    active: dict[int, set[int]] = {}
    for actor_id in expected_actors:
        dvm_tuple = _validate_index_tuple(
            dvm_indices_by_actor[actor_id],
            B=config.B,
            field_name=f"actor[{actor_id}].dvm",
            stop_code=STOP_FORCED_ROW_POLICY_LEAK,
        )
        active_tuple = _validate_index_tuple(
            active_indices_by_actor[actor_id],
            B=config.B,
            field_name=f"actor[{actor_id}].active",
            stop_code=STOP_FORCED_ROW_POLICY_LEAK,
        )
        dvm[actor_id] = set(dvm_tuple)
        active[actor_id] = set(active_tuple)

    minibatches: list[B2RActorMinibatchPlanV1] = []
    backward_counts = {actor_id: 0 for actor_id in expected_actors}
    for actor_id in permutation:
        for epoch_index, epoch in enumerate(partitions):
            for batch_index, partition in enumerate(epoch):
                evaluation = tuple(index for index in partition if index in dvm[actor_id])
                loss = tuple(
                    index
                    for index in partition
                    if index in dvm[actor_id] and index in active[actor_id]
                )
                if loss:
                    backward_counts[actor_id] += 1
                minibatches.append(
                    B2RActorMinibatchPlanV1(
                        actor_id=actor_id,
                        epoch=epoch_index,
                        minibatch=batch_index,
                        canonical_partition_indices=partition,
                        dvm_evaluation_indices=evaluation,
                        active_and_dvm_loss_indices=loss,
                        empty_loss=not loss,
                    )
                )
    step_counts = {
        actor_id: (
            backward_counts[actor_id]
            if optimizer_step_policy == "match_backward"
            else 0
        )
        for actor_id in expected_actors
    }
    return B2RActorUpdatePlanV1(
        update_id=authority.update_id,
        authority_config_digest=authority_config_digest,
        resolved_T=config.resolved_T,
        resolved_E=config.resolved_E,
        resolved_M=config.resolved_M,
        actor_epoch_count=config.actor_epoch_count,
        actor_minibatch_count=config.actor_minibatch_count,
        actor_permutation=permutation,
        minibatches=tuple(minibatches),
        behavior_old_logprob_field="original_rollout_behavior_logprob",
        factor_pre_logprob_field="factor_pre_logprob",
        factor_post_logprob_field="factor_post_logprob",
        expected_backward_count_by_actor=tuple(sorted(backward_counts.items())),
        expected_optimizer_step_count_by_actor=tuple(sorted(step_counts.items())),
        factor_input_digest=factor_input_digest,
        optimizer_step_policy=optimizer_step_policy,
    )


@dataclass(frozen=True, slots=True)
class B2RFactorTransitionEvidenceV1:
    actor_id: int
    shape: tuple[int, int, int]
    scatter_indices: tuple[int, ...]
    factor_before_digest: str
    ratio_full_digest: str
    factor_after_digest: str
    finite: bool
    strictly_positive: bool
    off_dvm_exact_one: bool
    recurrence_exact: bool
    skipped_actor: bool
    schema_version: str = B2R_FACTOR_TRANSITION_EVIDENCE_V1

    def __post_init__(self) -> None:
        if len(self.scatter_indices) != len(set(self.scatter_indices)):
            _fail(
                "factor evidence contains duplicate scatter indices",
                stop_code=STOP_FACTOR,
                stage="factor_evidence_schema",
                observed=self.scatter_indices,
            )
        if not all((self.finite, self.strictly_positive, self.off_dvm_exact_one, self.recurrence_exact)):
            _fail(
                "factor evidence cannot certify a failed recurrence",
                stop_code=STOP_FACTOR,
                stage="factor_evidence_schema",
                expected=(True, True, True, True),
                observed=(self.finite, self.strictly_positive, self.off_dvm_exact_one, self.recurrence_exact),
            )
        for value in (self.factor_before_digest, self.ratio_full_digest, self.factor_after_digest):
            if _SHA256_PATTERN.fullmatch(value) is None:
                _fail(
                    "factor evidence digest is malformed",
                    stop_code=STOP_FACTOR,
                    stage="factor_evidence_schema",
                    observed=value,
                )

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class B2RFactorTransitionResultV1:
    evidence: B2RFactorTransitionEvidenceV1
    _factor_after: torch.Tensor

    @classmethod
    def _create(
        cls,
        *,
        evidence: B2RFactorTransitionEvidenceV1,
        factor_after: torch.Tensor,
    ) -> "B2RFactorTransitionResultV1":
        result = object.__new__(cls)
        object.__setattr__(result, "evidence", evidence)
        object.__setattr__(result, "_factor_after", factor_after.detach().clone().contiguous())
        return result

    @property
    def factor_after(self) -> torch.Tensor:
        return self._factor_after.detach().clone().contiguous()


def compute_full_index_factor_transition_v1(
    *,
    actor_id: int,
    factor_before: torch.Tensor,
    decision_valid_mask: torch.Tensor,
    factor_pre_logprob: torch.Tensor,
    factor_post_logprob: torch.Tensor,
    scatter_indices: Sequence[int] | None = None,
    skipped_actor: bool = False,
) -> B2RFactorTransitionResultV1:
    tensors = (factor_before, decision_valid_mask, factor_pre_logprob, factor_post_logprob)
    if any(type(value) is not torch.Tensor for value in tensors):
        _fail(
            "factor transition requires exact tensors",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            observed=tuple(type(value) for value in tensors),
        )
    shape = tuple(factor_before.shape)
    if len(shape) != 3 or shape[-1] != 1 or any(tuple(value.shape) != shape for value in tensors):
        _fail(
            "factor transition requires one full canonical [T,E,1] shape",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected="same [T,E,1] shape",
            observed=tuple(tuple(value.shape) for value in tensors),
        )
    if decision_valid_mask.dtype is not torch.bool:
        _fail(
            "decision-valid factor mask must be boolean",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected=torch.bool,
            observed=decision_valid_mask.dtype,
        )
    if (
        not factor_before.is_floating_point()
        or factor_pre_logprob.dtype is not factor_before.dtype
        or factor_post_logprob.dtype is not factor_before.dtype
        or any(value.device != factor_before.device for value in tensors)
    ):
        _fail(
            "factor/logprob dtype-device binding is inconsistent",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected=(factor_before.dtype, factor_before.device),
            observed=tuple((value.dtype, value.device) for value in tensors),
        )
    for name, value in (
        ("factor_before", factor_before),
        ("factor_pre_logprob", factor_pre_logprob),
        ("factor_post_logprob", factor_post_logprob),
    ):
        if not bool(torch.isfinite(value).all().item()):
            _fail(
                "factor transition input contains a nonfinite value",
                stop_code=STOP_FACTOR,
                stage="factor_plan",
                field_name=name,
                expected="finite",
                observed=value,
            )
    if not bool((factor_before > 0).all().item()):
        _fail(
            "factor input must be strictly positive",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected="factor_before > 0",
            observed=factor_before,
        )
    canonical_scatter = tuple(
        int(item)
        for item in decision_valid_mask[..., 0]
        .reshape(-1)
        .nonzero(as_tuple=False)
        .flatten()
        .tolist()
    )
    supplied_scatter = canonical_scatter if scatter_indices is None else tuple(scatter_indices)
    if len(supplied_scatter) != len(set(supplied_scatter)) or supplied_scatter != canonical_scatter:
        _fail(
            "factor scatter is duplicated, compacted, or not canonical DVM order",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected=canonical_scatter,
            observed=supplied_scatter,
        )

    ratio_full = torch.ones_like(factor_before)
    if skipped_actor:
        factor_after = factor_before.detach().clone().contiguous()
    else:
        ratio_values = torch.exp(
            factor_post_logprob[decision_valid_mask]
            - factor_pre_logprob[decision_valid_mask]
        )
        if not bool(torch.isfinite(ratio_values).all().item()) or not bool((ratio_values > 0).all().item()):
            _fail(
                "DVM factor ratio must be finite and strictly positive",
                stop_code=STOP_FACTOR,
                stage="factor_plan",
                expected="finite ratio > 0",
                observed=ratio_values,
            )
        ratio_full[decision_valid_mask] = ratio_values
        factor_after = factor_before * ratio_full
    off_dvm_exact_one = torch.equal(
        ratio_full[~decision_valid_mask], torch.ones_like(ratio_full[~decision_valid_mask])
    )
    recurrence = torch.equal(factor_after, factor_before * ratio_full)
    finite = bool(torch.isfinite(factor_after).all().item())
    positive = bool((factor_after > 0).all().item())
    if not off_dvm_exact_one or not recurrence or not finite or not positive:
        _fail(
            "full-index factor recurrence violated its exact contract",
            stop_code=STOP_FACTOR,
            stage="factor_plan",
            expected="finite positive exact recurrence and off-DVM one",
            observed=(off_dvm_exact_one, recurrence, finite, positive),
        )
    evidence = B2RFactorTransitionEvidenceV1(
        actor_id=actor_id,
        shape=(int(shape[0]), int(shape[1]), int(shape[2])),
        scatter_indices=supplied_scatter,
        factor_before_digest=fingerprint_tensor_v1(factor_before).content_digest,
        ratio_full_digest=fingerprint_tensor_v1(ratio_full).content_digest,
        factor_after_digest=fingerprint_tensor_v1(factor_after).content_digest,
        finite=finite,
        strictly_positive=positive,
        off_dvm_exact_one=off_dvm_exact_one,
        recurrence_exact=recurrence,
        skipped_actor=skipped_actor,
    )
    return B2RFactorTransitionResultV1._create(
        evidence=evidence, factor_after=factor_after
    )


@dataclass(frozen=True, slots=True)
class B2RCriticUpdatePlanV1:
    update_id: str
    authority_config_digest: str
    resolved_T: int
    resolved_E: int
    resolved_M: int
    resolved_N: int
    B: int
    critic_epoch_count: int
    critic_minibatch_count: int
    partitions_by_epoch: tuple[tuple[tuple[int, ...], ...], ...]
    raw_target_digest: str
    expected_backward_count: int
    expected_optimizer_step_count: int
    expected_valuenorm_update_count: int
    valuenorm_enabled: bool
    optimizer_step_policy: str
    schema_version: str = B2R_CRITIC_UPDATE_PLAN_V1

    def __post_init__(self) -> None:
        if type(self.update_id) is not str or not self.update_id or _SHA256_PATTERN.fullmatch(self.authority_config_digest) is None:
            _fail(
                "critic plan update/config authority identity is malformed",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="critic_plan_schema",
                observed=(self.update_id, self.authority_config_digest),
            )
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.resolved_T,
                self.resolved_E,
                self.resolved_M,
                self.resolved_N,
                self.B,
                self.critic_epoch_count,
                self.critic_minibatch_count,
            )
        ) or type(self.valuenorm_enabled) is not bool:
            _fail(
                "critic plan resolved dimensions/counts/flags are malformed",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="critic_plan_schema",
                observed=(self.resolved_T, self.resolved_E, self.resolved_M, self.resolved_N, self.B, self.critic_epoch_count, self.critic_minibatch_count, self.valuenorm_enabled),
            )
        if self.B != self.resolved_T * self.resolved_E:
            _fail(
                "critic plan B does not match resolved T*E",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="critic_plan_schema",
                expected=self.resolved_T * self.resolved_E,
                observed=self.B,
            )
        partitions = _validate_epoch_partitions(
            self.partitions_by_epoch,
            epoch_count=self.critic_epoch_count,
            minibatch_count=self.critic_minibatch_count,
            B=self.B,
            stop_code=STOP_CRITIC_ROW_COVERAGE,
            require_full_coverage=True,
        )
        expected_backward = sum(len(epoch) for epoch in partitions)
        if self.optimizer_step_policy not in ("match_backward", "disabled"):
            _fail(
                "critic optimizer policy is not frozen",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="critic_plan_schema",
                observed=self.optimizer_step_policy,
            )
        expected_step = expected_backward if self.optimizer_step_policy == "match_backward" else 0
        expected_vn = expected_step if self.valuenorm_enabled else 0
        if (
            self.expected_backward_count != expected_backward
            or self.expected_optimizer_step_count != expected_step
            or self.expected_valuenorm_update_count != expected_vn
        ):
            _fail(
                "critic expected mutation counts do not match exact coverage",
                stop_code=STOP_UNEXPECTED_STEP_COUNT,
                stage="critic_plan_schema",
                expected=(expected_backward, expected_step, expected_vn),
                observed=(self.expected_backward_count, self.expected_optimizer_step_count, self.expected_valuenorm_update_count),
            )
        if _SHA256_PATTERN.fullmatch(self.raw_target_digest) is None:
            _fail(
                "critic raw-target digest is malformed",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="critic_plan_schema",
                observed=self.raw_target_digest,
            )

    @property
    def plan_digest(self) -> str:
        return canonical_digest_v1(self)


def build_critic_update_plan_v1(
    *,
    authority: B2RUpdateAuthorityV1,
    authority_config_digest: str,
    approved_partitions_by_epoch: Sequence[Sequence[Sequence[int]]],
    raw_target_digest: str,
    optimizer_step_policy: str = "match_backward",
) -> B2RCriticUpdatePlanV1:
    config: B2RResolvedConfigV1 = authority.resolved_config
    if authority_config_digest != authority.config_digest:
        _fail(
            "critic plan is bound to a stale/wrong configuration",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="critic_plan",
            expected=authority.config_digest,
            observed=authority_config_digest,
        )
    if optimizer_step_policy not in ("match_backward", "disabled"):
        _fail(
            "critic optimizer step policy is not representable",
            stop_code=STOP_UNEXPECTED_STEP_COUNT,
            stage="critic_plan",
            expected=("match_backward", "disabled"),
            observed=optimizer_step_policy,
        )
    partitions = _validate_epoch_partitions(
        approved_partitions_by_epoch,
        epoch_count=config.critic_epoch_count,
        minibatch_count=config.critic_minibatch_count,
        B=config.B,
        stop_code=STOP_CRITIC_ROW_COVERAGE,
        require_full_coverage=True,
    )
    backward_count = sum(len(epoch) for epoch in partitions)
    optimizer_count = backward_count if optimizer_step_policy == "match_backward" else 0
    valuenorm_count = optimizer_count if config.valuenorm_enabled else 0
    return B2RCriticUpdatePlanV1(
        update_id=authority.update_id,
        authority_config_digest=authority_config_digest,
        resolved_T=config.resolved_T,
        resolved_E=config.resolved_E,
        resolved_M=config.resolved_M,
        resolved_N=config.resolved_N,
        B=config.B,
        critic_epoch_count=config.critic_epoch_count,
        critic_minibatch_count=config.critic_minibatch_count,
        partitions_by_epoch=partitions,
        raw_target_digest=raw_target_digest,
        expected_backward_count=backward_count,
        expected_optimizer_step_count=optimizer_count,
        expected_valuenorm_update_count=valuenorm_count,
        valuenorm_enabled=config.valuenorm_enabled,
        optimizer_step_policy=optimizer_step_policy,
    )


__all__: tuple[str, ...] = ()
