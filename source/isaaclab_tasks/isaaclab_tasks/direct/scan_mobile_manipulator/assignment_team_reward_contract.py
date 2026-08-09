"""Pure event-gated team-reward semantic contract.

Phase A3 freezes only the reward source, reduction order, component-level
penalty unit, broadcast semantics, and an unresolved parameter identity.  It
does not select the rejection-penalty value and is not imported by the
environment, wrapper, runner, critic, or ValueNorm runtime paths.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_team_reward_contract"
)
ASSIGNMENT_TEAM_REWARD_SOURCE_PURPOSE = (
    "pure event-gated assignment team-reward semantic contract"
)

if __name__ != CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: assignment team reward contract source "
        "must fail before declaring identity-bearing types or importing torch; "
        f"expected module key={CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE!r}; "
        f"actual module key={__name__!r}; "
        f"source purpose={ASSIGNMENT_TEAM_REWARD_SOURCE_PURPOSE!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType

import torch

from .assignment_mrta_contract import UnresolvedParameterSpec


ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION = (
    "assignment_team_reward_contract_v1"
)
TEAM_REWARD_CONTRACT_SCHEMA_VERSION = (
    "event_gated_team_reward_contract_v1"
)
TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION = (
    "event_gated_team_reward_oracle_result_v1"
)

WRAPPER_REWARD_SOURCE = "AssignmentHarlWrapper.final_reward"
BASE_REDUCER = "mean_over_robot_axis"
PENALTY_ORDER = "after_mean_before_broadcast"
PENALTY_UNIT = "once_per_penalty_eligible_rejected_component"
BROADCAST_MODE = "identical_all_agents"
CRITIC_REWARD_SOURCE = "broadcast_team_reward"
VALUENORM_SOURCE = "all_physical_step_critic_returns"
RAW_PER_AGENT_USAGE = "diagnostics_only"
REJECTION_PENALTY_PARAMETER_NAME = "rejection_penalty_scale"
REJECTION_PENALTY_OWNER_PHASE = "phase_d_e"
REJECTION_PENALTY_SEMANTIC_PURPOSE = (
    "once_per_penalty_eligible_rejected_component"
)

# These tuples freeze current *ordered field identities*, not scenario values.
# A scenario can resolve different numeric values later without A3 importing or
# reading runtime config.
BASE_ENV_REWARD_SCALE_IDENTITY = (
    "global_coverage_reward_scale",
    "own_coverage_reward_scale",
    "duplicate_scan_penalty_scale",
    "reach_violation_penalty_scale",
    "action_rate_penalty_scale",
    "time_penalty",
)
WRAPPER_SHAPING_CONFIG_IDENTITY = (
    "repeated_assignment_penalty_scale",
    "repeated_assignment_grace_steps",
    "no_progress_penalty_scale",
    "no_progress_grace_steps",
    "no_progress_penalty_cap",
    "selected_path_cost_penalty_scale",
)


class AssignmentTeamRewardContractError(RuntimeError):
    """Base error carrying stable pure reward-contract context."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        field_name: str | None = None,
        expected: object = None,
        actual: object = None,
        schema_version: str = TEAM_REWARD_CONTRACT_SCHEMA_VERSION,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.field_name = field_name
        self.expected = expected
        self.actual = actual
        self.schema_version = schema_version
        super().__init__(
            f"{message}; "
            f"failure_code={failure_code!r}; "
            f"field_name={field_name!r}; "
            f"expected={_context_value(expected)!r}; "
            f"actual={_context_value(actual)!r}; "
            f"schema_version={schema_version!r}"
        )


class TeamRewardSchemaError(AssignmentTeamRewardContractError):
    """The frozen semantic configuration is invalid."""


class TeamRewardOracleError(AssignmentTeamRewardContractError):
    """Synthetic tensors violate the pure reward-oracle boundary."""


def _context_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, torch.dtype):
        return str(value)
    if isinstance(value, torch.device):
        return str(value)
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return value


def _require_exact_string(
    value: object,
    *,
    expected: str,
    field_name: str,
) -> None:
    if type(value) is not str or value != expected:
        raise TeamRewardSchemaError(
            f"{field_name} does not match the frozen team-reward semantic",
            failure_code="semantic_identity",
            field_name=field_name,
            expected=expected,
            actual=value,
        )


def _require_exact_identity_tuple(
    value: object,
    *,
    expected: tuple[str, ...],
    field_name: str,
) -> None:
    if type(value) is not tuple or value != expected:
        raise TeamRewardSchemaError(
            f"{field_name} does not match the ordered current identity",
            failure_code="ordered_identity",
            field_name=field_name,
            expected=expected,
            actual=value,
        )
    if any(type(item) is not str or not item for item in value):
        raise TeamRewardSchemaError(
            f"{field_name} contains a non-canonical item",
            failure_code="ordered_identity",
            field_name=field_name,
            expected="tuple of non-empty exact strings",
            actual=value,
        )


def _validate_unresolved_penalty_spec(value: object) -> None:
    if type(value) is not UnresolvedParameterSpec:
        raise TeamRewardSchemaError(
            "rejection_penalty_scale must remain the canonical unresolved "
            "parameter spec in Phase A3",
            failure_code="unresolved_parameter",
            field_name="rejection_penalty_scale",
            expected=UnresolvedParameterSpec,
            actual=type(value),
        )
    expected_identity = (
        REJECTION_PENALTY_PARAMETER_NAME,
        REJECTION_PENALTY_OWNER_PHASE,
        REJECTION_PENALTY_SEMANTIC_PURPOSE,
    )
    actual_identity = (
        value.name,
        value.owner_phase,
        value.semantic_purpose,
    )
    if actual_identity != expected_identity:
        raise TeamRewardSchemaError(
            "unresolved parameter has the wrong semantic identity",
            failure_code="unresolved_parameter",
            field_name="rejection_penalty_scale",
            expected=expected_identity,
            actual=actual_identity,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamRewardContractSpec:
    """Frozen semantic configuration; it intentionally has no numeric value."""

    schema_version: str = TEAM_REWARD_CONTRACT_SCHEMA_VERSION
    wrapper_reward_source: str = WRAPPER_REWARD_SOURCE
    base_reducer: str = BASE_REDUCER
    penalty_order: str = PENALTY_ORDER
    penalty_unit: str = PENALTY_UNIT
    broadcast_mode: str = BROADCAST_MODE
    critic_reward_source: str = CRITIC_REWARD_SOURCE
    valuenorm_source: str = VALUENORM_SOURCE
    raw_per_agent_usage: str = RAW_PER_AGENT_USAGE
    rejection_penalty_scale: UnresolvedParameterSpec
    base_env_reward_contract: tuple[str, ...] = (
        BASE_ENV_REWARD_SCALE_IDENTITY
    )
    wrapper_shaping_contract: tuple[str, ...] = (
        WRAPPER_SHAPING_CONFIG_IDENTITY
    )

    def __post_init__(self) -> None:
        _require_exact_string(
            self.schema_version,
            expected=TEAM_REWARD_CONTRACT_SCHEMA_VERSION,
            field_name="schema_version",
        )
        fixed_strings = (
            ("wrapper_reward_source", WRAPPER_REWARD_SOURCE),
            ("base_reducer", BASE_REDUCER),
            ("penalty_order", PENALTY_ORDER),
            ("penalty_unit", PENALTY_UNIT),
            ("broadcast_mode", BROADCAST_MODE),
            ("critic_reward_source", CRITIC_REWARD_SOURCE),
            ("valuenorm_source", VALUENORM_SOURCE),
            ("raw_per_agent_usage", RAW_PER_AGENT_USAGE),
        )
        for field_name, expected in fixed_strings:
            _require_exact_string(
                getattr(self, field_name),
                expected=expected,
                field_name=field_name,
            )
        _validate_unresolved_penalty_spec(self.rejection_penalty_scale)
        _require_exact_identity_tuple(
            self.base_env_reward_contract,
            expected=BASE_ENV_REWARD_SCALE_IDENTITY,
            field_name="base_env_reward_contract",
        )
        _require_exact_identity_tuple(
            self.wrapper_shaping_contract,
            expected=WRAPPER_SHAPING_CONFIG_IDENTITY,
            field_name="wrapper_shaping_contract",
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return deterministic immutable primitives in exact field order."""

        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "wrapper_reward_source": self.wrapper_reward_source,
                "base_reducer": self.base_reducer,
                "penalty_order": self.penalty_order,
                "penalty_unit": self.penalty_unit,
                "broadcast_mode": self.broadcast_mode,
                "critic_reward_source": self.critic_reward_source,
                "valuenorm_source": self.valuenorm_source,
                "raw_per_agent_usage": self.raw_per_agent_usage,
                "rejection_penalty_scale": MappingProxyType(
                    {
                        "name": self.rejection_penalty_scale.name,
                        "owner_phase": self.rejection_penalty_scale.owner_phase,
                        "semantic_purpose": (
                            self.rejection_penalty_scale.semantic_purpose
                        ),
                    }
                ),
                "base_env_reward_contract": (
                    self.base_env_reward_contract
                ),
                "wrapper_shaping_contract": (
                    self.wrapper_shaping_contract
                ),
            }
        )


@dataclass(frozen=True, slots=True)
class _ProtectedOracleTensor:
    _value: torch.Tensor
    _mutation_marker: int

    @classmethod
    def capture(cls, value: torch.Tensor) -> "_ProtectedOracleTensor":
        with torch.inference_mode(False):
            cloned = value.detach().clone().contiguous()
        return cls(cloned, int(cloned._version))

    def validate(self, field_name: str) -> None:
        try:
            actual_marker = int(self._value._version)
        except RuntimeError as exc:
            raise TeamRewardOracleError(
                "protected oracle tensor cannot be validated",
                failure_code="snapshot_mutation",
                field_name=field_name,
                expected="supported tensor integrity",
                actual="integrity unavailable",
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            ) from exc
        if actual_marker != self._mutation_marker:
            raise TeamRewardOracleError(
                "supported-path mutation of oracle output was detected",
                failure_code="snapshot_mutation",
                field_name=field_name,
                expected="protected tensor integrity unchanged",
                actual="supported-path mutation detected",
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )

    def read(self, field_name: str) -> torch.Tensor:
        self.validate(field_name)
        return self._value.detach().clone().contiguous()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class TeamRewardOracleResult:
    """Alias-isolated result of the synthetic, caller-parameterized oracle."""

    _base_team_reward: _ProtectedOracleTensor
    _team_reward: _ProtectedOracleTensor
    _learner_reward: _ProtectedOracleTensor

    def __init__(
        self,
        *,
        base_team_reward: torch.Tensor,
        team_reward: torch.Tensor,
        learner_reward: torch.Tensor,
    ) -> None:
        tensors = {
            "base_team_reward": base_team_reward,
            "team_reward": team_reward,
            "learner_reward": learner_reward,
        }
        for field_name, value in tensors.items():
            if type(value) is not torch.Tensor:
                raise TeamRewardOracleError(
                    "oracle result fields must be exact torch.Tensor values",
                    failure_code="tensor_type",
                    field_name=field_name,
                    expected=torch.Tensor,
                    actual=type(value),
                    schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
                )
            if value.dtype is not torch.float32:
                raise TeamRewardOracleError(
                    "oracle result fields must use exact float32",
                    failure_code="dtype",
                    field_name=field_name,
                    expected=torch.float32,
                    actual=value.dtype,
                    schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
                )
            if value.requires_grad:
                raise TeamRewardOracleError(
                    "oracle result fields cannot require gradients",
                    failure_code="requires_grad",
                    field_name=field_name,
                    expected=False,
                    actual=True,
                    schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
                )
            if not bool(torch.isfinite(value).all()):
                raise TeamRewardOracleError(
                    "oracle result fields must be finite",
                    failure_code="finite",
                    field_name=field_name,
                    expected="all finite",
                    actual="contains non-finite value",
                    schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
                )
        if (
            base_team_reward.ndim != 2
            or base_team_reward.shape[0] <= 0
            or base_team_reward.shape[1] != 1
        ):
            raise TeamRewardOracleError(
                "base_team_reward must have shape [E,1]",
                failure_code="shape",
                field_name="base_team_reward",
                expected="[E,1], E>0",
                actual=tuple(base_team_reward.shape),
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )
        env_count = int(base_team_reward.shape[0])
        if tuple(team_reward.shape) != (env_count, 1):
            raise TeamRewardOracleError(
                "team_reward must have shape [E,1]",
                failure_code="shape",
                field_name="team_reward",
                expected=(env_count, 1),
                actual=tuple(team_reward.shape),
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )
        if (
            learner_reward.ndim != 3
            or learner_reward.shape[0] != env_count
            or learner_reward.shape[1] <= 0
            or learner_reward.shape[2] != 1
        ):
            raise TeamRewardOracleError(
                "learner_reward must have shape [E,M,1]",
                failure_code="shape",
                field_name="learner_reward",
                expected="[E,M,1], M>0",
                actual=tuple(learner_reward.shape),
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )
        devices = {value.device for value in tensors.values()}
        if len(devices) != 1:
            raise TeamRewardOracleError(
                "oracle result tensors must share one device",
                failure_code="device",
                field_name="oracle_result",
                expected=base_team_reward.device,
                actual=tuple(str(device) for device in devices),
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )
        expected_broadcast = team_reward.view(env_count, 1, 1).expand_as(
            learner_reward
        )
        if not torch.equal(learner_reward, expected_broadcast):
            raise TeamRewardOracleError(
                "learner_reward must be an identical all-agent broadcast",
                failure_code="broadcast",
                field_name="learner_reward",
                expected="team_reward broadcast over M",
                actual="non-identical learner rows",
                schema_version=TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION,
            )
        object.__setattr__(
            self,
            "_base_team_reward",
            _ProtectedOracleTensor.capture(base_team_reward),
        )
        object.__setattr__(
            self,
            "_team_reward",
            _ProtectedOracleTensor.capture(team_reward),
        )
        object.__setattr__(
            self,
            "_learner_reward",
            _ProtectedOracleTensor.capture(learner_reward),
        )

    @property
    def schema_version(self) -> str:
        return TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION

    @property
    def base_team_reward(self) -> torch.Tensor:
        return self._base_team_reward.read("base_team_reward")

    @property
    def team_reward(self) -> torch.Tensor:
        return self._team_reward.read("team_reward")

    @property
    def learner_reward(self) -> torch.Tensor:
        return self._learner_reward.read("learner_reward")

    def validate_snapshot(self) -> None:
        self._base_team_reward.validate("base_team_reward")
        self._team_reward.validate("team_reward")
        self._learner_reward.validate("learner_reward")

    def to_mapping(self) -> Mapping[str, object]:
        self.validate_snapshot()
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "base_team_reward": self.base_team_reward,
                "team_reward": self.team_reward,
                "learner_reward": self.learner_reward,
            }
        )


def _validate_reward_tensor(value: object) -> tuple[int, int, torch.device]:
    if type(value) is not torch.Tensor:
        raise TeamRewardOracleError(
            "wrapper_final_reward must be an exact torch.Tensor",
            failure_code="tensor_type",
            field_name="wrapper_final_reward",
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.dtype is not torch.float32:
        raise TeamRewardOracleError(
            "wrapper_final_reward must use exact float32",
            failure_code="dtype",
            field_name="wrapper_final_reward",
            expected=torch.float32,
            actual=value.dtype,
        )
    if value.ndim != 3 or value.shape[0] <= 0 or value.shape[1] <= 0:
        raise TeamRewardOracleError(
            "wrapper_final_reward must have shape [E,M,1] with E,M > 0",
            failure_code="shape",
            field_name="wrapper_final_reward",
            expected="[E,M,1], E>0, M>0",
            actual=tuple(value.shape),
        )
    if value.shape[2] != 1:
        raise TeamRewardOracleError(
            "wrapper_final_reward trailing dimension must be one",
            failure_code="shape",
            field_name="wrapper_final_reward",
            expected="[E,M,1]",
            actual=tuple(value.shape),
        )
    if value.requires_grad:
        raise TeamRewardOracleError(
            "the pure oracle does not accept autograd tensors",
            failure_code="requires_grad",
            field_name="wrapper_final_reward",
            expected=False,
            actual=True,
        )
    if not bool(torch.isfinite(value).all()):
        raise TeamRewardOracleError(
            "wrapper_final_reward must be finite",
            failure_code="finite",
            field_name="wrapper_final_reward",
            expected="all finite",
            actual="contains non-finite value",
        )
    return int(value.shape[0]), int(value.shape[1]), value.device


def _validate_component_count(
    value: object,
    *,
    env_count: int,
    device: torch.device,
) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise TeamRewardOracleError(
            "policy_rejected_component_count must be an exact torch.Tensor",
            failure_code="tensor_type",
            field_name="policy_rejected_component_count",
            expected=torch.Tensor,
            actual=type(value),
        )
    if value.dtype is not torch.int64:
        raise TeamRewardOracleError(
            "policy_rejected_component_count must use exact int64",
            failure_code="dtype",
            field_name="policy_rejected_component_count",
            expected=torch.int64,
            actual=value.dtype,
        )
    if tuple(value.shape) != (env_count,):
        raise TeamRewardOracleError(
            "policy_rejected_component_count must have shape [E]",
            failure_code="shape",
            field_name="policy_rejected_component_count",
            expected=(env_count,),
            actual=tuple(value.shape),
        )
    if value.device != device:
        raise TeamRewardOracleError(
            "reward and component count tensors must share one device",
            failure_code="device",
            field_name="policy_rejected_component_count",
            expected=device,
            actual=value.device,
        )
    if value.requires_grad:
        raise TeamRewardOracleError(
            "component count cannot require gradients",
            failure_code="requires_grad",
            field_name="policy_rejected_component_count",
            expected=False,
            actual=True,
        )
    if bool((value < 0).any()):
        raise TeamRewardOracleError(
            "policy_rejected_component_count must be non-negative",
            failure_code="range",
            field_name="policy_rejected_component_count",
            expected=">= 0",
            actual=value.detach().cpu().tolist(),
        )
    return value


def _validate_synthetic_penalty_scale(value: object) -> float:
    if type(value) not in (int, float):
        raise TeamRewardOracleError(
            "synthetic rejection_penalty_scale must be an exact number",
            failure_code="numeric_type",
            field_name="rejection_penalty_scale",
            expected="finite non-negative int or float supplied by test caller",
            actual=value,
        )
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise TeamRewardOracleError(
            "synthetic rejection_penalty_scale must be finite and non-negative",
            failure_code="numeric_range",
            field_name="rejection_penalty_scale",
            expected="finite value >= 0",
            actual=value,
        )
    return result


def compute_team_reward_oracle(
    *,
    contract: TeamRewardContractSpec,
    wrapper_final_reward: torch.Tensor,
    policy_rejected_component_count: torch.Tensor,
    rejection_penalty_scale: float,
) -> TeamRewardOracleResult:
    """Apply mean -> component-once penalty -> identical broadcast.

    ``rejection_penalty_scale`` is supplied by a synthetic test caller.  Its
    presence here does not resolve the Phase D/E parameter in ``contract``.
    """

    if type(contract) is not TeamRewardContractSpec:
        raise TeamRewardSchemaError(
            "oracle requires the exact canonical team-reward contract",
            failure_code="contract_type",
            field_name="contract",
            expected=TeamRewardContractSpec,
            actual=type(contract),
        )
    contract.__post_init__()
    env_count, agent_count, device = _validate_reward_tensor(
        wrapper_final_reward
    )
    component_count = _validate_component_count(
        policy_rejected_component_count,
        env_count=env_count,
        device=device,
    )
    scale = _validate_synthetic_penalty_scale(rejection_penalty_scale)

    base_team_reward = wrapper_final_reward.mean(dim=1)
    penalty = component_count.to(dtype=torch.float32).view(env_count, 1)
    team_reward = base_team_reward - scale * penalty
    learner_reward = team_reward.view(env_count, 1, 1).expand(
        env_count,
        agent_count,
        1,
    )
    return TeamRewardOracleResult(
        base_team_reward=base_team_reward,
        team_reward=team_reward,
        learner_reward=learner_reward,
    )


def evaluate_team_reward_oracle(
    *,
    contract: TeamRewardContractSpec,
    wrapper_final_reward: torch.Tensor,
    policy_rejected_component_count: torch.Tensor,
    rejection_penalty_scale: float,
) -> TeamRewardOracleResult:
    """Spelled-out alias for callers that treat the function as an oracle."""

    return compute_team_reward_oracle(
        contract=contract,
        wrapper_final_reward=wrapper_final_reward,
        policy_rejected_component_count=policy_rejected_component_count,
        rejection_penalty_scale=rejection_penalty_scale,
    )


def _deep_readonly(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _deep_readonly(item) for key, item in value.items()}
        )
    if isinstance(value, tuple):
        return tuple(_deep_readonly(item) for item in value)
    if isinstance(value, list):
        return tuple(_deep_readonly(item) for item in value)
    return value


_TEAM_REWARD_PUBLIC_DESCRIPTOR = _deep_readonly(
    {
        "contract_version": ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION,
        "schema_version": TEAM_REWARD_CONTRACT_SCHEMA_VERSION,
        "spec_field_order": (
            "schema_version",
            "wrapper_reward_source",
            "base_reducer",
            "penalty_order",
            "penalty_unit",
            "broadcast_mode",
            "critic_reward_source",
            "valuenorm_source",
            "raw_per_agent_usage",
            "rejection_penalty_scale",
            "base_env_reward_contract",
            "wrapper_shaping_contract",
        ),
        "semantic_values": {
            "wrapper_reward_source": WRAPPER_REWARD_SOURCE,
            "base_reducer": BASE_REDUCER,
            "penalty_order": PENALTY_ORDER,
            "penalty_unit": PENALTY_UNIT,
            "broadcast_mode": BROADCAST_MODE,
            "critic_reward_source": CRITIC_REWARD_SOURCE,
            "valuenorm_source": VALUENORM_SOURCE,
            "raw_per_agent_usage": RAW_PER_AGENT_USAGE,
        },
        "base_env_reward_contract": BASE_ENV_REWARD_SCALE_IDENTITY,
        "wrapper_shaping_contract": WRAPPER_SHAPING_CONFIG_IDENTITY,
        "unresolved_parameter": {
            "name": REJECTION_PENALTY_PARAMETER_NAME,
            "owner_phase": REJECTION_PENALTY_OWNER_PHASE,
            "semantic_purpose": (
                REJECTION_PENALTY_SEMANTIC_PURPOSE
            ),
            "required_type": "UnresolvedParameterSpec",
            "numeric_value_selected": False,
        },
        "operation_order": (
            "mean wrapper_final_reward over robot axis",
            "subtract one penalty unit per penalty-eligible rejected component",
            "broadcast identical team reward to every agent",
        ),
        "formula": (
            "base_team_reward[e] = mean_i(wrapper_final_reward[e,i])",
            "team_reward[e] = base_team_reward[e] - "
            "rejection_penalty_scale * "
            "policy_rejected_component_count[e]",
            "learner_reward[e,i] = team_reward[e]",
        ),
        "oracle_inputs": (
            {
                "name": "wrapper_final_reward",
                "shape": ("E", "M", "1"),
                "dtype": "torch.float32",
            },
            {
                "name": "policy_rejected_component_count",
                "shape": ("E",),
                "dtype": "torch.int64",
            },
            {
                "name": "rejection_penalty_scale",
                "shape": "scalar",
                "dtype": "caller-supplied finite non-negative synthetic number",
            },
        ),
        "oracle_outputs": (
            {
                "name": "base_team_reward",
                "shape": ("E", "1"),
                "dtype": "torch.float32",
            },
            {
                "name": "team_reward",
                "shape": ("E", "1"),
                "dtype": "torch.float32",
            },
            {
                "name": "learner_reward",
                "shape": ("E", "M", "1"),
                "dtype": "torch.float32",
            },
        ),
    }
)


def get_assignment_team_reward_contract_descriptor() -> Mapping[str, object]:
    """Return the deterministic deeply read-only A3 reward descriptor."""

    return _TEAM_REWARD_PUBLIC_DESCRIPTOR  # type: ignore[return-value]


__all__ = [
    "ASSIGNMENT_TEAM_REWARD_CONTRACT_VERSION",
    "AssignmentTeamRewardContractError",
    "BASE_ENV_REWARD_SCALE_IDENTITY",
    "BASE_REDUCER",
    "BROADCAST_MODE",
    "CANONICAL_ASSIGNMENT_TEAM_REWARD_MODULE",
    "CRITIC_REWARD_SOURCE",
    "PENALTY_ORDER",
    "PENALTY_UNIT",
    "RAW_PER_AGENT_USAGE",
    "REJECTION_PENALTY_OWNER_PHASE",
    "REJECTION_PENALTY_PARAMETER_NAME",
    "REJECTION_PENALTY_SEMANTIC_PURPOSE",
    "TEAM_REWARD_CONTRACT_SCHEMA_VERSION",
    "TEAM_REWARD_ORACLE_RESULT_SCHEMA_VERSION",
    "TeamRewardContractSpec",
    "TeamRewardOracleError",
    "TeamRewardOracleResult",
    "TeamRewardSchemaError",
    "VALUENORM_SOURCE",
    "WRAPPER_REWARD_SOURCE",
    "WRAPPER_SHAPING_CONFIG_IDENTITY",
    "compute_team_reward_oracle",
    "evaluate_team_reward_oracle",
    "get_assignment_team_reward_contract_descriptor",
]
