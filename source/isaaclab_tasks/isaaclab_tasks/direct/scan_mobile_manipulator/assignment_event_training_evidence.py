"""Pure/static B2-R1 authority, evidence, fingerprint, and ownership contracts.

This module is deliberately read-only with respect to learner state.  It can
inspect bounded tensors, modules, optimizers, gradients, and ValueNorm-like
state, but it has no autograd, optimizer-update, trainer, runner, lifecycle, or
public-route capability.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_EVIDENCE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_evidence"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_EVIDENCE_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R1 training evidence source must be "
        "imported under its canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_EVIDENCE_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import torch

from .assignment_value_normalizer_checkpoint import (
    VALUE_NORMALIZER_STATE_KEYS,
    ValueNormalizerCheckpointError,
    extract_value_normalizer_runtime_state,
)


B2R_TRAINING_EVIDENCE_V1 = "b2r_training_evidence_v1"
B2R_UPDATE_AUTHORITY_V1 = "b2r_update_authority_v1"
B2R_COMPONENT_FINGERPRINT_V1 = "b2r_component_fingerprint_v1"
B2R_FROZEN_TRAINING_INPUTS_V1 = "b2r_frozen_training_inputs_v1"

STOP_AUTHORITY_DRIFT = "STOP — B2-R AUTHORITY_DRIFT"
STOP_TERMINATION_PRECEDENCE = "STOP — B2-R TERMINATION_PRECEDENCE"
STOP_ACTOR_EVIDENCE_BINDING = "STOP — B2-R ACTOR_EVIDENCE_BINDING"
STOP_OWNERSHIP = "STOP — B2-R OWNERSHIP"
STOP_VALUENORM = "STOP — B2-R VALUENORM"
STOP_NONFINITE_VALUENORM_STATE = "STOP — B2-R NONFINITE_VALUENORM_STATE"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_HEAD_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class B2RContractError(RuntimeError):
    """Typed fail-closed error carrying one exact frozen STOP category."""

    def __init__(
        self,
        message: str,
        *,
        stop_code: str,
        stage: str,
        field_name: str | None = None,
        expected: object = None,
        observed: object = None,
    ) -> None:
        self.stop_code = stop_code
        self.stage = stage
        self.field_name = field_name
        self.expected = expected
        self.observed = observed
        super().__init__(
            f"{message}; stop_code={stop_code!r}; stage={stage!r}; "
            f"field_name={field_name!r}; expected={_bounded_repr(expected)}; "
            f"observed={_bounded_repr(observed)}; "
            f"schema={B2R_TRAINING_EVIDENCE_V1!r}"
        )


def _bounded_repr(value: object, *, limit: int = 320) -> str:
    if isinstance(value, torch.Tensor):
        rendered = (
            f"Tensor(shape={tuple(value.shape)!r}, dtype={str(value.dtype)!r}, "
            f"device={str(value.device)!r})"
        )
    else:
        rendered = repr(value)
    return rendered if len(rendered) <= limit else rendered[: limit - 3] + "..."


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


def _require_nonempty_string(value: object, *, field_name: str, stop_code: str) -> str:
    if type(value) is not str or not value:
        _fail(
            "field must be a non-empty exact string",
            stop_code=stop_code,
            stage="schema_validation",
            field_name=field_name,
            expected="non-empty str",
            observed=value,
        )
    return value


def _require_positive_int(value: object, *, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        _fail(
            "resolved configuration integer must be positive",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="resolved_config",
            field_name=field_name,
            expected="positive exact int",
            observed=value,
        )
    return value


def _require_sha256(value: object, *, field_name: str, stop_code: str) -> str:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        _fail(
            "field must be a lowercase SHA-256 identity",
            stop_code=stop_code,
            stage="digest_validation",
            field_name=field_name,
            expected="64 lowercase hex characters",
            observed=value,
        )
    return value


def _canonical_float(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "+inf" if value > 0.0 else "-inf"
    return value.hex()


def _tensor_bytes_digest(value: torch.Tensor) -> str:
    if value.device.type == "meta":
        _fail(
            "meta tensors have no bounded content bytes",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="canonical_tensor",
            expected="materialized tensor",
            observed=value,
        )
    detached = value.detach().to(device="cpu").contiguous()
    byte_view = detached.reshape(-1).view(torch.uint8)
    payload = byte_view.numpy().tobytes(order="C")
    return hashlib.sha256(payload).hexdigest()


def _tensor_device_classification(value: torch.Tensor) -> str:
    index = value.device.index
    return value.device.type if index is None else f"{value.device.type}:{index}"


def _tensor_finite(value: torch.Tensor) -> bool:
    if value.is_floating_point() or value.is_complex():
        return bool(torch.isfinite(value.detach()).all().item())
    return True


def _canonicalize(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        return {"__float__": _canonical_float(value)}
    if isinstance(value, Enum):
        return {
            "__enum__": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": _canonicalize(value.value),
        }
    if isinstance(value, torch.Tensor):
        return {
            "__tensor__": True,
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "device": _tensor_device_classification(value),
            "finite": _tensor_finite(value),
            "content_sha256": _tensor_bytes_digest(value),
        }
    if isinstance(value, bytes):
        return {
            "__bytes__": True,
            "length": len(value),
            "content_sha256": hashlib.sha256(value).hexdigest(),
        }
    if isinstance(value, Path):
        return {"__path__": value.as_posix()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "__dataclass__": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": [
                [field.name, _canonicalize(getattr(value, field.name))]
                for field in fields(value)
            ],
        }
    if isinstance(value, Mapping):
        items: list[list[object]] = []
        for key in value:
            if type(key) is not str:
                _fail(
                    "canonical mappings require exact string keys",
                    stop_code=STOP_AUTHORITY_DRIFT,
                    stage="canonical_serialization",
                    expected="str mapping keys",
                    observed=type(key),
                )
        for key in sorted(value):
            items.append([key, _canonicalize(value[key])])
        return {"__mapping__": items}
    if isinstance(value, tuple):
        return {"__tuple__": [_canonicalize(item) for item in value]}
    if isinstance(value, list):
        return {"__list__": [_canonicalize(item) for item in value]}
    _fail(
        "object type is not part of the bounded canonical evidence domain",
        stop_code=STOP_AUTHORITY_DRIFT,
        stage="canonical_serialization",
        expected="bounded scalar/dataclass/mapping/ordered-sequence/tensor",
        observed=type(value),
    )


def canonical_json_bytes_v1(value: object) -> bytes:
    """Serialize bounded evidence deterministically without object addresses."""

    normalized = _canonicalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_digest_v1(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes_v1(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class B2RSourceDigestV1:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.path, field_name="source.path", stop_code=STOP_AUTHORITY_DRIFT
        )
        _require_sha256(
            self.sha256,
            field_name="source.sha256",
            stop_code=STOP_AUTHORITY_DRIFT,
        )


@dataclass(frozen=True, slots=True)
class B2RResolvedConfigV1:
    resolved_T: int
    resolved_E: int
    resolved_M: int
    resolved_N: int
    actor_epoch_count: int
    actor_minibatch_count: int
    actor_partition_policy: str
    critic_epoch_count: int
    critic_minibatch_count: int
    critic_partition_policy: str
    fixed_order: bool
    valuenorm_enabled: bool
    ppo_happo_settings: tuple[tuple[str, object], ...]
    schema_version: str = "b2r_resolved_config_v1"

    def __post_init__(self) -> None:
        for name in (
            "resolved_T",
            "resolved_E",
            "resolved_M",
            "resolved_N",
            "actor_epoch_count",
            "actor_minibatch_count",
            "critic_epoch_count",
            "critic_minibatch_count",
        ):
            _require_positive_int(getattr(self, name), field_name=name)
        for name in ("actor_partition_policy", "critic_partition_policy"):
            _require_nonempty_string(
                getattr(self, name), field_name=name, stop_code=STOP_AUTHORITY_DRIFT
            )
        if type(self.fixed_order) is not bool or type(self.valuenorm_enabled) is not bool:
            _fail(
                "configuration flags must be exact booleans",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="resolved_config",
                expected="bool",
                observed=(type(self.fixed_order), type(self.valuenorm_enabled)),
            )
        if any(type(item) is not tuple or len(item) != 2 for item in self.ppo_happo_settings):
            _fail(
                "PPO/HAPPO settings must be ordered name/value pairs",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="resolved_config",
                observed=self.ppo_happo_settings,
            )
        names = tuple(item[0] for item in self.ppo_happo_settings)
        if any(type(name) is not str or not name for name in names):
            _fail(
                "PPO/HAPPO setting names must be nonempty strings",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="resolved_config",
                observed=names,
            )
        if names != tuple(sorted(names)) or len(set(names)) != len(names):
            _fail(
                "PPO/HAPPO setting names must be unique and canonical",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="resolved_config",
                expected="unique lexicographic setting names",
                observed=names,
            )
        canonical_json_bytes_v1(self.ppo_happo_settings)

    @property
    def B(self) -> int:
        return self.resolved_T * self.resolved_E

    @property
    def config_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RUpdateAuthorityV1:
    update_id: str
    slice_identity: str
    repository_head: str
    dirty_state_classification: str
    repo_source_hashes: tuple[B2RSourceDigestV1, ...]
    installed_harl_source_hashes: tuple[B2RSourceDigestV1, ...]
    resolved_config: B2RResolvedConfigV1
    authorization_scope: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    schema_version: str = B2R_UPDATE_AUTHORITY_V1

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.update_id, field_name="update_id", stop_code=STOP_AUTHORITY_DRIFT
        )
        if self.slice_identity != "B2-R1":
            _fail(
                "authority is not bound to the authorized slice",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="authority",
                field_name="slice_identity",
                expected="B2-R1",
                observed=self.slice_identity,
            )
        if type(self.repository_head) is not str or _HEAD_PATTERN.fullmatch(self.repository_head) is None:
            _fail(
                "repository HEAD must be one lowercase Git object identity",
                stop_code=STOP_AUTHORITY_DRIFT,
                stage="authority",
                field_name="repository_head",
                expected="40 lowercase hex characters",
                observed=self.repository_head,
            )
        _require_nonempty_string(
            self.dirty_state_classification,
            field_name="dirty_state_classification",
            stop_code=STOP_AUTHORITY_DRIFT,
        )
        for field_name, values in (
            ("repo_source_hashes", self.repo_source_hashes),
            ("installed_harl_source_hashes", self.installed_harl_source_hashes),
        ):
            paths = tuple(item.path for item in values)
            if not values or paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
                _fail(
                    "source identities must be nonempty, unique, and canonical",
                    stop_code=STOP_AUTHORITY_DRIFT,
                    stage="authority",
                    field_name=field_name,
                    expected="lexicographic unique source paths",
                    observed=paths,
                )
        for field_name, values in (
            ("authorization_scope", self.authorization_scope),
            ("forbidden_operations", self.forbidden_operations),
        ):
            if (
                not values
                or any(type(item) is not str or not item for item in values)
                or len(set(values)) != len(values)
            ):
                _fail(
                    "authority operation sets must be nonempty unique strings",
                    stop_code=STOP_AUTHORITY_DRIFT,
                    stage="authority",
                    field_name=field_name,
                    observed=values,
                )

    @property
    def config_digest(self) -> str:
        return self.resolved_config.config_digest

    @property
    def B(self) -> int:
        return self.resolved_config.B

    @property
    def authority_digest(self) -> str:
        return canonical_digest_v1(self)


def validate_update_authority_binding_v1(
    authority: B2RUpdateAuthorityV1,
    *,
    expected_update_id: str,
    expected_repository_head: str,
    expected_config_digest: str,
    expected_repo_source_hashes: Sequence[B2RSourceDigestV1],
    expected_installed_harl_source_hashes: Sequence[B2RSourceDigestV1],
) -> str:
    """Fail closed if any frozen update-authority identity has drifted."""

    expected = (
        expected_update_id,
        expected_repository_head,
        expected_config_digest,
        tuple(expected_repo_source_hashes),
        tuple(expected_installed_harl_source_hashes),
    )
    observed = (
        authority.update_id,
        authority.repository_head,
        authority.config_digest,
        authority.repo_source_hashes,
        authority.installed_harl_source_hashes,
    )
    if observed != expected:
        _fail(
            "frozen update authority identity drifted",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="authority_binding",
            expected=expected,
            observed=observed,
        )
    return authority.authority_digest


class B2RTerminationReasonV1(str, Enum):
    NONE = "NONE"
    ALL_TASKS_COMPLETED = "ALL_TASKS_COMPLETED"
    NO_FEASIBLE_TASKS_REMAIN = "NO_FEASIBLE_TASKS_REMAIN"
    TIME_LIMIT = "TIME_LIMIT"


_TERMINATION_PRECEDENCE = (
    B2RTerminationReasonV1.ALL_TASKS_COMPLETED,
    B2RTerminationReasonV1.NO_FEASIBLE_TASKS_REMAIN,
    B2RTerminationReasonV1.TIME_LIMIT,
    B2RTerminationReasonV1.NONE,
)


def select_authoritative_termination_reason_v1(
    *,
    all_tasks_completed: bool,
    no_feasible_tasks_remain: bool,
    time_limit: bool,
) -> B2RTerminationReasonV1:
    for name, value in (
        ("all_tasks_completed", all_tasks_completed),
        ("no_feasible_tasks_remain", no_feasible_tasks_remain),
        ("time_limit", time_limit),
    ):
        if type(value) is not bool:
            _fail(
                "termination raw conditions must be exact booleans",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="termination_precedence",
                field_name=name,
                expected="bool",
                observed=value,
            )
    if all_tasks_completed:
        return B2RTerminationReasonV1.ALL_TASKS_COMPLETED
    if no_feasible_tasks_remain:
        return B2RTerminationReasonV1.NO_FEASIBLE_TASKS_REMAIN
    if time_limit:
        return B2RTerminationReasonV1.TIME_LIMIT
    return B2RTerminationReasonV1.NONE


@dataclass(frozen=True, slots=True)
class B2RTerminationSelectionEvidenceV1:
    selected_reason: B2RTerminationReasonV1
    all_tasks_completed: bool
    no_feasible_tasks_remain: bool
    time_limit: bool
    timeout_evidence_bound_for_learner_use: bool
    evidence_identity: str
    schema_version: str = "b2r_termination_selection_evidence_v1"

    def __post_init__(self) -> None:
        if type(self.selected_reason) is not B2RTerminationReasonV1:
            _fail(
                "selected reason is outside the exact four-category domain",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="termination_precedence",
                expected=tuple(item.value for item in _TERMINATION_PRECEDENCE),
                observed=self.selected_reason,
            )
        expected = select_authoritative_termination_reason_v1(
            all_tasks_completed=self.all_tasks_completed,
            no_feasible_tasks_remain=self.no_feasible_tasks_remain,
            time_limit=self.time_limit,
        )
        if self.selected_reason is not expected:
            _fail(
                "selected reason violates environment-owned precedence",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="termination_precedence",
                expected=expected.value,
                observed=self.selected_reason.value,
            )
        if (
            self.selected_reason
            in (
                B2RTerminationReasonV1.ALL_TASKS_COMPLETED,
                B2RTerminationReasonV1.NO_FEASIBLE_TASKS_REMAIN,
            )
            and self.timeout_evidence_bound_for_learner_use
        ):
            _fail(
                "zero-bootstrap terminal cannot bind timeout evidence for learner use",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="termination_precedence",
                expected=False,
                observed=True,
            )
        if (
            self.selected_reason is B2RTerminationReasonV1.TIME_LIMIT
            and not self.timeout_evidence_bound_for_learner_use
        ):
            _fail(
                "TIME_LIMIT requires correlated historical timeout evidence",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="termination_precedence",
                expected=True,
                observed=False,
            )
        _require_nonempty_string(
            self.evidence_identity,
            field_name="termination.evidence_identity",
            stop_code=STOP_TERMINATION_PRECEDENCE,
        )

    @property
    def precedence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RFrozenTrainingInputsV1:
    update_id: str
    authority_config_digest: str
    actor_canonical_identities: tuple[tuple[int, int, int], ...]
    historical_actor_observation_digest: str
    historical_available_action_mask_digest: str
    original_proposal_action_digest: str
    original_behavior_logprob_digest: str
    dvm_digest: str
    active_mask_digest: str
    selected_reason_grid_digest: str
    termination_domain_valid: bool
    exactly_one_selected_category: bool
    precedence_resolution_evidence_digest: str
    terminal_correlation_evidence_digest: str
    timeout_critic_evidence_digest: str
    event_return_result_digest: str
    critic_training_slice_digest: str
    final_structural_return_slot_digest: str
    return_equality_proof: str
    return_no_alias_proof: str
    baseline_value_digest: str
    advantage_digest: str
    schema_version: str = B2R_FROZEN_TRAINING_INPUTS_V1

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.update_id, field_name="update_id", stop_code=STOP_ACTOR_EVIDENCE_BINDING
        )
        for name in (
            "authority_config_digest",
            "historical_actor_observation_digest",
            "historical_available_action_mask_digest",
            "original_proposal_action_digest",
            "original_behavior_logprob_digest",
            "dvm_digest",
            "active_mask_digest",
            "selected_reason_grid_digest",
            "precedence_resolution_evidence_digest",
            "terminal_correlation_evidence_digest",
            "timeout_critic_evidence_digest",
            "event_return_result_digest",
            "critic_training_slice_digest",
            "final_structural_return_slot_digest",
            "baseline_value_digest",
            "advantage_digest",
        ):
            _require_sha256(
                getattr(self, name),
                field_name=name,
                stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            )
        if (
            not self.actor_canonical_identities
            or len(set(self.actor_canonical_identities)) != len(self.actor_canonical_identities)
            or any(
                type(item) is not tuple
                or len(item) != 3
                or any(type(part) is not int or part < 0 for part in item)
                for item in self.actor_canonical_identities
            )
        ):
            _fail(
                "actor/t/env identities must be unique nonnegative triples",
                stop_code=STOP_ACTOR_EVIDENCE_BINDING,
                stage="frozen_training_inputs",
                observed=self.actor_canonical_identities,
            )
        if not self.termination_domain_valid or not self.exactly_one_selected_category:
            _fail(
                "termination evidence is not an exact selected four-category grid",
                stop_code=STOP_TERMINATION_PRECEDENCE,
                stage="frozen_training_inputs",
                expected=(True, True),
                observed=(
                    self.termination_domain_valid,
                    self.exactly_one_selected_category,
                ),
            )
        for name in ("return_equality_proof", "return_no_alias_proof"):
            _require_nonempty_string(
                getattr(self, name),
                field_name=name,
                stop_code=STOP_ACTOR_EVIDENCE_BINDING,
            )

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


@dataclass(frozen=True, slots=True)
class B2RTensorFingerprintV1:
    shape: tuple[int, ...]
    dtype: str
    device: str
    finite: bool
    content_digest: str
    requires_grad: bool | None


@dataclass(frozen=True, slots=True)
class B2RNamedTensorFingerprintV1:
    name: str
    tensor: B2RTensorFingerprintV1


@dataclass(frozen=True, slots=True)
class B2RGradientFingerprintV1:
    parameter_name: str
    present: bool
    finite: bool | None
    content_digest: str | None
    norm: float | None


@dataclass(frozen=True, slots=True)
class B2ROptimizerParamGroupFingerprintV1:
    group_index: int
    parameter_names: tuple[str, ...]
    hyperparameters: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class B2ROptimizerStateFingerprintV1:
    parameter_name: str
    state_keys: tuple[str, ...]
    state_digest: str
    step_value: str | None


@dataclass(frozen=True, slots=True)
class B2RComponentFingerprintV1:
    component_kind: str
    owner_identity: str
    parameters: tuple[B2RNamedTensorFingerprintV1, ...]
    buffers: tuple[B2RNamedTensorFingerprintV1, ...]
    module_training: bool | None
    optimizer_groups: tuple[B2ROptimizerParamGroupFingerprintV1, ...]
    optimizer_state: tuple[B2ROptimizerStateFingerprintV1, ...]
    gradients: tuple[B2RGradientFingerprintV1, ...]
    valuenorm_state: tuple[B2RNamedTensorFingerprintV1, ...]
    schema_version: str = B2R_COMPONENT_FINGERPRINT_V1

    @property
    def fingerprint_digest(self) -> str:
        return canonical_digest_v1(self)


def fingerprint_tensor_v1(
    value: torch.Tensor, *, requires_grad: bool | None = None
) -> B2RTensorFingerprintV1:
    if not isinstance(value, torch.Tensor):
        _fail(
            "fingerprint input must be a tensor",
            stop_code=STOP_AUTHORITY_DRIFT,
            stage="component_fingerprint",
            expected="torch.Tensor",
            observed=type(value),
        )
    return B2RTensorFingerprintV1(
        shape=tuple(int(item) for item in value.shape),
        dtype=str(value.dtype),
        device=_tensor_device_classification(value),
        finite=_tensor_finite(value),
        content_digest=_tensor_bytes_digest(value),
        requires_grad=requires_grad,
    )


def _named_state_fingerprints(
    state: Mapping[str, torch.Tensor],
    *,
    prefix: str,
    canonical_order: Sequence[str] | None = None,
) -> tuple[B2RNamedTensorFingerprintV1, ...]:
    records: list[B2RNamedTensorFingerprintV1] = []
    names = tuple(sorted(state)) if canonical_order is None else tuple(canonical_order)
    if set(names) != set(state) or len(names) != len(state):
        _fail(
            "state fields do not match canonical order",
            stop_code=STOP_VALUENORM,
            stage="component_fingerprint",
            expected=names,
            observed=tuple(state),
        )
    for name in names:
        value = state[name]
        if not isinstance(value, torch.Tensor):
            _fail(
                "state_dict entries must be tensors",
                stop_code=STOP_VALUENORM,
                stage="component_fingerprint",
                field_name=f"{prefix}.{name}",
                observed=type(value),
            )
        records.append(
            B2RNamedTensorFingerprintV1(
                name=f"{prefix}.{name}", tensor=fingerprint_tensor_v1(value)
            )
        )
    return tuple(records)


def canonical_live_valuenorm_state_v1(
    value_normalizer: object,
) -> Mapping[str, torch.Tensor]:
    """Read the complete installed ValueNorm live state without module registration APIs."""

    try:
        state = extract_value_normalizer_runtime_state(value_normalizer)
    except ValueNormalizerCheckpointError as exc:
        message = str(exc)
        _fail(
            "live ValueNorm canonical-state extraction failed",
            stop_code=(
                STOP_NONFINITE_VALUENORM_STATE
                if "nonfinite" in message
                else STOP_VALUENORM
            ),
            stage="component_fingerprint",
            expected=VALUE_NORMALIZER_STATE_KEYS,
            observed=message,
        )
    return state


def fingerprint_component_v1(
    *,
    component_kind: str,
    owner_identity: str,
    module: torch.nn.Module | None = None,
    optimizer: torch.optim.Optimizer | None = None,
    value_normalizer: object | None = None,
) -> B2RComponentFingerprintV1:
    """Read component state without changing parameters, optimizer, or ValueNorm."""

    _require_nonempty_string(
        component_kind, field_name="component_kind", stop_code=STOP_OWNERSHIP
    )
    _require_nonempty_string(
        owner_identity, field_name="owner_identity", stop_code=STOP_OWNERSHIP
    )
    if module is None and optimizer is not None:
        _fail(
            "optimizer fingerprint requires its intended module",
            stop_code=STOP_OWNERSHIP,
            stage="component_fingerprint",
            expected="module supplied",
            observed=None,
        )
    parameters: list[B2RNamedTensorFingerprintV1] = []
    buffers: list[B2RNamedTensorFingerprintV1] = []
    gradients: list[B2RGradientFingerprintV1] = []
    parameter_lookup: dict[int, str] = {}
    parameter_by_name: dict[str, torch.nn.Parameter] = {}
    if module is not None:
        if not isinstance(module, torch.nn.Module):
            _fail(
                "module must use the installed torch module interface",
                stop_code=STOP_OWNERSHIP,
                stage="component_fingerprint",
                observed=type(module),
            )
        for name, parameter in module.named_parameters():
            qualified = f"{owner_identity}.{name}"
            parameter_lookup[id(parameter)] = qualified
            parameter_by_name[qualified] = parameter
            parameters.append(
                B2RNamedTensorFingerprintV1(
                    name=qualified,
                    tensor=fingerprint_tensor_v1(
                        parameter, requires_grad=bool(parameter.requires_grad)
                    ),
                )
            )
            gradient = parameter.grad
            if gradient is None:
                gradients.append(
                    B2RGradientFingerprintV1(qualified, False, None, None, None)
                )
            else:
                finite = _tensor_finite(gradient)
                norm = float(torch.linalg.vector_norm(gradient.detach()).item())
                gradients.append(
                    B2RGradientFingerprintV1(
                        qualified,
                        True,
                        finite,
                        _tensor_bytes_digest(gradient),
                        norm,
                    )
                )
        for name, buffer in module.named_buffers():
            buffers.append(
                B2RNamedTensorFingerprintV1(
                    name=f"{owner_identity}.{name}", tensor=fingerprint_tensor_v1(buffer)
                )
            )

    optimizer_groups: list[B2ROptimizerParamGroupFingerprintV1] = []
    optimizer_state: list[B2ROptimizerStateFingerprintV1] = []
    if optimizer is not None:
        if not isinstance(optimizer, torch.optim.Optimizer):
            _fail(
                "optimizer must use the installed torch optimizer interface",
                stop_code=STOP_OWNERSHIP,
                stage="component_fingerprint",
                observed=type(optimizer),
            )
        for group_index, group in enumerate(optimizer.param_groups):
            names: list[str] = []
            for parameter in group["params"]:
                name = parameter_lookup.get(id(parameter))
                if name is None:
                    _fail(
                        "optimizer contains a parameter outside its intended module",
                        stop_code=STOP_OWNERSHIP,
                        stage="component_fingerprint",
                        field_name=f"optimizer_group[{group_index}]",
                        observed="unresolved parameter",
                    )
                names.append(name)
            hyperparameters = tuple(
                (
                    str(key),
                    canonical_json_bytes_v1(value).decode("utf-8"),
                )
                for key, value in sorted(group.items(), key=lambda item: str(item[0]))
                if key != "params"
            )
            optimizer_groups.append(
                B2ROptimizerParamGroupFingerprintV1(
                    group_index=group_index,
                    parameter_names=tuple(names),
                    hyperparameters=hyperparameters,
                )
            )
        for name in sorted(parameter_by_name):
            parameter = parameter_by_name[name]
            if parameter not in optimizer.state:
                continue
            state = optimizer.state[parameter]
            state_keys = tuple(sorted(str(key) for key in state))
            step = state.get("step")
            optimizer_state.append(
                B2ROptimizerStateFingerprintV1(
                    parameter_name=name,
                    state_keys=state_keys,
                    state_digest=canonical_digest_v1(
                        {str(key): state[key] for key in sorted(state, key=str)}
                    ),
                    step_value=(
                        None
                        if step is None
                        else canonical_json_bytes_v1(step).decode("utf-8")
                    ),
                )
            )

    valuenorm_state: tuple[B2RNamedTensorFingerprintV1, ...] = ()
    if value_normalizer is not None:
        state = canonical_live_valuenorm_state_v1(value_normalizer)
        valuenorm_state = _named_state_fingerprints(
            state,
            prefix=owner_identity,
            canonical_order=VALUE_NORMALIZER_STATE_KEYS,
        )

    return B2RComponentFingerprintV1(
        component_kind=component_kind,
        owner_identity=owner_identity,
        parameters=tuple(parameters),
        buffers=tuple(buffers),
        module_training=None if module is None else bool(module.training),
        optimizer_groups=tuple(optimizer_groups),
        optimizer_state=tuple(optimizer_state),
        gradients=tuple(gradients),
        valuenorm_state=valuenorm_state,
    )


@dataclass(frozen=True, slots=True)
class B2ROwnershipEvidenceV1:
    actor_parameter_names: tuple[tuple[str, tuple[str, ...]], ...]
    critic_parameter_names: tuple[str, ...]
    actor_optimizers_disjoint: bool
    critic_disjoint_from_actors: bool
    exact_ownership: bool
    schema_version: str = "b2r_ownership_evidence_v1"

    @property
    def ownership_digest(self) -> str:
        return canonical_digest_v1(self)


def _optimizer_parameters(optimizer: torch.optim.Optimizer) -> tuple[torch.nn.Parameter, ...]:
    return tuple(parameter for group in optimizer.param_groups for parameter in group["params"])


def validate_parameter_ownership_v1(
    *,
    actor_bindings: Sequence[
        tuple[str, torch.nn.Module, torch.optim.Optimizer]
    ],
    critic_binding: tuple[str, torch.nn.Module, torch.optim.Optimizer],
    shared_parameter_mode: bool,
) -> B2ROwnershipEvidenceV1:
    """Validate exact optimizer ownership using object identity only transiently."""

    if shared_parameter_mode:
        _fail(
            "shared-parameter mode is unsupported by the frozen B2-R design",
            stop_code=STOP_OWNERSHIP,
            stage="ownership",
            expected=False,
            observed=True,
        )
    if not actor_bindings:
        _fail(
            "at least one actor ownership binding is required",
            stop_code=STOP_OWNERSHIP,
            stage="ownership",
            observed=actor_bindings,
        )
    actor_names = tuple(binding[0] for binding in actor_bindings)
    if len(set(actor_names)) != len(actor_names):
        _fail(
            "actor owner identities must be unique",
            stop_code=STOP_OWNERSHIP,
            stage="ownership",
            observed=actor_names,
        )

    all_seen: dict[int, str] = {}
    actor_evidence: list[tuple[str, tuple[str, ...]]] = []
    for owner, module, optimizer in actor_bindings:
        intended = tuple(module.named_parameters())
        intended_ids = {id(parameter) for _, parameter in intended}
        actual = _optimizer_parameters(optimizer)
        actual_ids = [id(parameter) for parameter in actual]
        if len(actual_ids) != len(set(actual_ids)):
            _fail(
                "actor optimizer owns a duplicate parameter",
                stop_code=STOP_OWNERSHIP,
                stage="ownership",
                field_name=owner,
                observed="duplicate optimizer parameter",
            )
        if set(actual_ids) != intended_ids:
            missing = tuple(name for name, parameter in intended if id(parameter) not in actual_ids)
            extras = len(set(actual_ids) - intended_ids)
            _fail(
                "actor optimizer ownership is not exact",
                stop_code=STOP_OWNERSHIP,
                stage="ownership",
                field_name=owner,
                expected="exact intended actor parameter set",
                observed={"missing": missing, "unexpected_count": extras},
            )
        for name, parameter in intended:
            parameter_id = id(parameter)
            previous = all_seen.get(parameter_id)
            if previous is not None:
                _fail(
                    "actor parameter sets overlap",
                    stop_code=STOP_OWNERSHIP,
                    stage="ownership",
                    field_name=f"{owner}.{name}",
                    expected="disjoint actor parameters",
                    observed=previous,
                )
            all_seen[parameter_id] = f"{owner}.{name}"
        actor_evidence.append(
            (owner, tuple(f"{owner}.{name}" for name, _ in intended))
        )

    critic_owner, critic_module, critic_optimizer = critic_binding
    intended_critic = tuple(critic_module.named_parameters())
    intended_critic_ids = {id(parameter) for _, parameter in intended_critic}
    actual_critic = _optimizer_parameters(critic_optimizer)
    actual_critic_ids = [id(parameter) for parameter in actual_critic]
    if len(actual_critic_ids) != len(set(actual_critic_ids)):
        _fail(
            "critic optimizer owns a duplicate parameter",
            stop_code=STOP_OWNERSHIP,
            stage="ownership",
            field_name=critic_owner,
            observed="duplicate optimizer parameter",
        )
    if set(actual_critic_ids) != intended_critic_ids:
        missing = tuple(
            name for name, parameter in intended_critic if id(parameter) not in actual_critic_ids
        )
        extras = len(set(actual_critic_ids) - intended_critic_ids)
        _fail(
            "critic optimizer ownership is not exact",
            stop_code=STOP_OWNERSHIP,
            stage="ownership",
            field_name=critic_owner,
            expected="exact intended critic parameter set",
            observed={"missing": missing, "unexpected_count": extras},
        )
    for name, parameter in intended_critic:
        previous = all_seen.get(id(parameter))
        if previous is not None:
            _fail(
                "critic parameter set overlaps an actor",
                stop_code=STOP_OWNERSHIP,
                stage="ownership",
                field_name=f"{critic_owner}.{name}",
                expected="critic disjoint from actors",
                observed=previous,
            )

    return B2ROwnershipEvidenceV1(
        actor_parameter_names=tuple(actor_evidence),
        critic_parameter_names=tuple(
            f"{critic_owner}.{name}" for name, _ in intended_critic
        ),
        actor_optimizers_disjoint=True,
        critic_disjoint_from_actors=True,
        exact_ownership=True,
    )


__all__: tuple[str, ...] = ()
